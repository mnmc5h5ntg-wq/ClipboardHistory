# -*- coding: utf-8 -*-
"""帧级状态自证：录制态那一圈必须**在写出的 PNG 里**量得到（R147 / BACKLOG 177 收尾）。

为什么要有这支工具（不是"再截一次图看看"）：R145 给设置窗口加了录制态夹具
`settings-shortcuts-recording`，帧名声称"录制中"，而它当时的自证只有两条：
① 夹具闭包里 `XCTAssert(window.firstResponder === button)`，② 本轮一次性脚本量过一次高色度像素。
①记的是**视图树里第一响应者是谁**，不是**画面上有没有那一圈** —— 闭包里的断言不拦快门（U-493），
一次说谎的帧今天照样能落盘并被基线钉成契约。这支工具把那句话搬到产物上：
读**已经写出的 PNG**，判"录制态比静置态多出来的那圈描边存在、四边连续、且没外溢到别的行"。

口径（与 R121–R123 那颗列级尺同一族）：
  · 色度轴：`max(r,g,b) − min(r,g,b) > chroma_min` 算一个高色度像素（强调蓝在亮暗两档都高色度，
    而灰底、文字、材质都低色度 ⇒ 与"亮度"无关，暗档黑字不会伪装成墨）；
  · 两帧**逐像素差**的包围盒 = "录制态改了哪一块"，四边连续 = 那一圈是环而不是一团；
  · 地板全部由**实测值留出余量**推出来（本机 2 个样本：亮 Δ443、暗 Δ441 ⇒ 地板 300），
    不是拍脑袋，也不是把某一次读数当门限（U-486 那一族）。

输出是**格子**不是散文：每格一个 `大写标记=值`，红了要说清是哪一格、判的是哪句话。
`--allow-missing` 之类的沉默出口不存在：读不到帧 ⇒ `FRAME_STATE_NOT_RUN=<原因>` 且退出码 1，
因为"没量到"与"量了没问题"在账上必须长得不一样。
"""
import argparse
import io
import json
import sys

from PIL import Image

CHROMA_MIN = 60
# 地板全部由**这把尺自己**的读数推出来（U-486：不许拿别的脚本、别的机器、别的口径的读数当门限）。
# 本机 `frame_recording_proof.py /tmp/shots_r145` 实测：
#   亮 1569 → 3341（多 1772）、暗 1593 → 3357（多 1764）；两样本跨度 0.5% ⇒ 地板取 ~51%（900），
#   这样"整圈没画"（多出来 ≈ 0）必红，而"画了但被挤掉一半"也红。
DELTA_FLOOR = 900
# 挖掉两个角之后重测真帧：上 726 / 下 726 / 左 102 / 右 102（两档一样）。
# 地板第一版写 80，被自己的守卫格拦下（`testFloorsAreBelowTheRealRingButAboveZero` 要地板离最小读数留 ≥3 倍）；
# 而更早的一版整带都数 ⇒ 把上边整条擦掉仍读 80（左右竖边的顶端落进了那一带），`testMissingOneEdgeIsNamed` 当场抓住。
# 取 40 = 最小读数 102 的 39%："缺一条边"读到 0，照样拦得住。
EDGE_FLOOR = 40
# 包围盒实测 宽 256 × 高 48（2x 步进像素）⇒ 上限给 ~33% 余量，超出就是外溢到别的行。
BBOX_MAX_WIDTH = 340
BBOX_MAX_HEIGHT = 90


def _chroma_mask(image, chroma_min=CHROMA_MIN):
    """返回 (宽, 高, [True/False per pixel])。灰度与低色度都是 False。"""
    rgb = image.convert("RGB")
    width, height = rgb.size
    pixels = rgb.getdata()
    mask = []
    for red, green, blue in pixels:
        mask.append((max(red, green, blue) - min(red, green, blue)) > chroma_min)
    return width, height, mask


def _chroma_count(image, chroma_min=CHROMA_MIN):
    return sum(1 for hit in _chroma_mask(image, chroma_min)[2] if hit)


def _diff_bbox(a, b):
    """两帧逐像素不同的包围盒；完全相同返回 None。"""
    ia, ib = a.convert("RGB"), b.convert("RGB")
    if ia.size != ib.size:
        return "SIZE_MISMATCH"
    width, height = ia.size
    pa, pb = ia.getdata(), ib.getdata()
    min_x, min_y, max_x, max_y = width, height, -1, -1
    for index in range(len(pa)):
        if pa[index] != pb[index]:
            x = index % width
            y = index // width
            if x < min_x:
                min_x = x
            if x > max_x:
                max_x = x
            if y < min_y:
                min_y = y
            if y > max_y:
                max_y = y
    if max_x < 0:
        return None
    return (min_x, min_y, max_x, max_y)


def _edge_runs(image, bbox, band=8, chroma_min=CHROMA_MIN):
    """包围盒四条边各 `band` 像素带内的高色度像素数 ⇒ "那一圈是连续的环"的证据。"""
    left, top, right, bottom = bbox
    width, height, mask = _chroma_mask(image, chroma_min)
    counts = {"上": 0, "下": 0, "左": 0, "右": 0}
    # 每条边各数自己那一段，**并挖掉两个角**（角属于相邻的两条边）。
    # 第一版整幅带都数 ⇒ 把上边整条擦掉，左右两条竖边的顶端仍然落在"上"这一带里，
    # 合成样本读到 80 就过了地板（我的 `testMissingOneEdgeIsNamed` 当场抓住这件事）。
    for y in range(max(0, top), min(height, bottom + 1)):
        for x in range(max(0, left), min(width, right + 1)):
            if not mask[y * width + x]:
                continue
            # 带就是**那条边自己**（贴边 `band` 个像素），只是把两个角让给相邻的边。
            # 我第一版把带写到了 `top+band .. top+2*band`（边**外面**那一圈），于是四边全读 0 ——
            # 真帧当场红成"四条边都缺"，这是尺坏掉的样子，不是产品坏掉的样子。
            if top <= y <= top + band and left + band <= x <= right - band:
                counts["上"] += 1
            if bottom - band <= y <= bottom and left + band <= x <= right - band:
                counts["下"] += 1
            if left <= x <= left + band and top + band <= y <= bottom - band:
                counts["左"] += 1
            if right - band <= x <= right and top + band <= y <= bottom - band:
                counts["右"] += 1
    return counts


def measure(idle_path, recording_path, chroma_min=CHROMA_MIN):
    """一份读数（不是判定）。判定在 `judge()`，这样正对照能喂合成的两帧。"""
    with Image.open(io.open(idle_path, "rb")) as idle, \
         Image.open(io.open(recording_path, "rb")) as recording:
        bbox = _diff_bbox(idle, recording)
        idle_chroma = _chroma_count(idle, chroma_min)
        rec_chroma = _chroma_count(recording, chroma_min)
        edges = _edge_runs(recording, bbox, chroma_min=chroma_min) if isinstance(bbox, tuple) else None
    return {"bbox": bbox,
            "idle_chroma": idle_chroma,
            "recording_chroma": rec_chroma,
            "delta": rec_chroma - idle_chroma,
            "edges": edges}


def judge(reading, label="pair"):
    """返回 (行列表, 是否成立)。每一格都只判一件事，且都能被打红。"""
    lines = []
    ok = True
    bbox = reading.get("bbox")
    if bbox is None:
        lines.append("FRAME_STATE_NO_DIFF=%s 两帧逐字节看不出差别 ⇒ 这一对里"
                     "『录制态』没有画面证据（不许读成『差别很细微』）" % label)
        return lines, False
    if bbox == "SIZE_MISMATCH":
        lines.append("FRAME_STATE_SIZE_MISMATCH=%s 两帧尺寸不同 ⇒ 比的是两张不同的屏，这一对不成立" % label)
        return lines, False
    left, top, right, bottom = bbox
    width, height = right - left + 1, bottom - top + 1
    lines.append("FRAME_STATE_PAIR=%s 包围盒 x %d..%d、y %d..%d（宽 %d × 高 %d）"
                 % (label, left, right, top, bottom, width, height))
    lines.append("FRAME_STATE_CHROMA=%s 静置=%d 录制=%d 多出来=%d"
                 % (label, reading["idle_chroma"], reading["recording_chroma"], reading["delta"]))
    edges = reading.get("edges") or {}
    lines.append("FRAME_STATE_EDGES=%s %s"
                 % (label, " ".join("%s%d" % (name, edges.get(name, -1)) for name in ("上", "下", "左", "右"))))

    if reading["delta"] < DELTA_FLOOR:
        lines.append("FRAME_STATE_DELTA_BELOW_FLOOR=%d（本机两样本 1772 / 1764，地板 %d）⇒ 录制态比静置态多出的高色度太少，"
                     "那一圈可能根本没画进产物" % (reading["delta"], DELTA_FLOOR))
        ok = False
    for name in ("上", "下", "左", "右"):
        count = edges.get(name, -1)
        if count < EDGE_FLOOR:
            lines.append("FRAME_STATE_EDGE_MISSING=%s=%d（地板 %d）⇒ 环断了一条边，这不是描边"
                         % (name, count, EDGE_FLOOR))
            ok = False
    if width > BBOX_MAX_WIDTH or height > BBOX_MAX_HEIGHT:
        lines.append("FRAME_STATE_BBOX_OVERFLOW 宽 %d（上限 %d）高 %d（上限 %d）⇒ 改动外溢到别的行/别的控件，"
                     "『不喧宾夺主』这条不成立" % (width, BBOX_MAX_WIDTH, height, BBOX_MAX_HEIGHT))
        ok = False
    if ok:
        lines.append("FRAME_STATE_PROVES_RECORDING=%s" % label)
    return lines, ok


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("frames_dir", help="装着 settings-shortcuts*.png 的目录")
    parser.add_argument("--basename", default="settings-shortcuts",
                        help="静置帧名前缀（默认 settings-shortcuts）")
    parser.add_argument("--recording", default="settings-shortcuts-recording",
                        help="录制态帧名前缀（默认 settings-shortcuts-recording）")
    parser.add_argument("--json", dest="json_out", default=None, help="把读数写成一份 JSON")
    args = parser.parse_args(argv)

    import os
    pairs = []
    for shade in ("light", "dark"):
        idle = os.path.join(args.frames_dir, "%s-720x540-%s.png" % (args.basename, shade))
        recording = os.path.join(args.frames_dir, "%s-720x540-%s.png" % (args.recording, shade))
        missing = [path for path in (idle, recording) if not os.path.exists(path)]
        if missing:
            print("FRAME_STATE_NOT_RUN=%s 读不到帧：%s ⇒ 这一格**没量过**，不是"
                  "『量了没问题』" % (shade, ",".join(missing)))
            return 1
        pairs.append((shade, idle, recording))

    readings, all_ok = {}, True
    for shade, idle, recording in pairs:
        reading = measure(idle, recording)
        readings[shade] = reading
        lines, ok = judge(reading, shade)
        for line in lines:
            print(line)
        all_ok = all_ok and ok
    if args.json_out:
        with io.open(args.json_out, "w", encoding="utf-8") as handle:
            handle.write(json.dumps(readings, ensure_ascii=False, sort_keys=True))
    print("FRAME_STATE_RESULT=%s pairs=%d" % ("ok" if all_ok else "red", len(pairs)))
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())

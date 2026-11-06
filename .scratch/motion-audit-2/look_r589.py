# -*- coding: utf-8 -*-
"""R589 / 视觉腿：对名册里那 8 组的 **light 档四张**（R588 已看过 dark）逐张看整帧 + 差量包围盒。

尺走 659 认过的形状：两张 RGBA 相减之后**必须先 `convert("L")` 再 `getbbox()`**
（RGBA 差值图上 `getbbox()` 恒报 None ⇒ 尺"拒绝出声"不等于没有差量），
差量颗数按 >8/255 计，且每一趟都配**同尺寸正对照**（同一张帧自己跟自己比 ⇒ 必须 0 颗，
另一把用两张已知不同的帧 ⇒ 必须非零），否则「看不见」这句话没有资格被写出来（R579）。
"""
import hashlib
import io
import os
import sys
from PIL import Image, ImageChops

SHOTS = os.environ.get("CLIPBOARD_HISTORY_UI_SHOTS") or "/tmp/r589/frames"
ROSTER = "/Users/wangziyi/Codex_Project0/docs/frame_identical_pairs.json"
THRESH = 8


def sha(path):
    return hashlib.sha256(io.open(path, "rb").read()).hexdigest()


def pixels(d):
    return sum(1 for v in d.getdata() if v > THRESH) if d.mode == "L" else 0


def measure(a_path, b_path):
    """返回 (包围盒, 差量颗数, 整幅尺寸) —— 三格都要，缺一条就不许说「看不出差别」。"""
    ia, ib = Image.open(a_path), Image.open(b_path)
    if ia.size != ib.size:
        return None, None, (ia.size, ib.size)
    diff = ImageChops.difference(ia.convert("RGB"), ib.convert("RGB")).convert("L")
    return diff.getbbox(), pixels(diff), ia.size


def main():
    import json
    rows = json.load(io.open(ROSTER, encoding="utf-8"))["rows"]
    print("LOOK_SHOTS=%s png=%d" % (SHOTS, len([f for f in os.listdir(SHOTS) if f.endswith(".png")])))
    for r in rows:
        names = r["members"]
        if not all(os.path.exists(os.path.join(SHOTS, n)) for n in names):
            print("LOOK_MISSING %s ⇒ 这一组本轮没有帧，不判" % (" + ".join(names),))
            continue
        digs = [sha(os.path.join(SHOTS, n)) for n in names]
        same = len(set(digs)) == 1
        bbox, cnt, size = measure(os.path.join(SHOTS, names[0]), os.path.join(SHOTS, names[1]))
        # 正对照一：同一张帧自己跟自己比 ⇒ 必须 0 颗（证明这把尺在"同图"上确实出 0）
        self_bbox, self_cnt, _ = measure(os.path.join(SHOTS, names[0]), os.path.join(SHOTS, names[0]))
        # 正对照二：拿一张**同尺寸**而内容不同的帧比 ⇒ 必须非 0（证明这把尺不是恒 0）。
        # 尺寸必须对齐：R579 那一课说"采错带子"就会把结论下错，而这里若拿 720x140 去比 1500x1120，
        # `measure` 直接返回 (None, None) —— 那既不是"无差量"也不是"有差量"，是尺没对上对象。
        other = None
        base_size = Image.open(os.path.join(SHOTS, names[0])).size
        base_tier = names[0].rsplit(u"-", 1)[-1]        # `-dark.png` / `-light.png`：对照要同一档
        for cand in sorted(os.listdir(SHOTS)):
            if not cand.endswith(u".png") or cand in names or not cand.endswith(base_tier):
                continue
            if Image.open(os.path.join(SHOTS, cand)).size != base_size:
                continue
            if sha(os.path.join(SHOTS, cand)) != digs[0]:
                other = cand
                break
        o_bbox, o_cnt, _ = (measure(os.path.join(SHOTS, names[0]), os.path.join(SHOTS, other))
                           if other else (None, None, None))
        print("LOOK 组=%s ｜ 逐字节同一=%s ｜ 尺寸=%s ｜ 差量包围盒=%s ｜ 差量颗数=%s"
              % (" + ".join(n.replace("-420x300", "").replace("-750x560", "")
                            .replace("-720x520", "").replace("-300x74", "") for n in names),
                 ("是" if same else "否"), size, bbox, cnt))
        print(u"     正对照：自比=%d 颗（该 0）；与 %s 比=%s 颗（该非 0）；名册该行说该相同=%s"
              % (self_cnt, (other or "（同尺寸同色档里没找到第三张 ⇒ 这一组的非零对照缺席，尺没被证明会出声）"),
                 o_cnt, r[u"should_be_identical"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())

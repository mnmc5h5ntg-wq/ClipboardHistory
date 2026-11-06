# -*- coding: utf-8 -*-
"""R594 靶 1：把「655 那句跨会话一次性差」与「名册 observed 那对哈希读的不是它声称的那个对象」
**分开的那组数**。两种成因的修法相反，而红本身不含成因信息（R556/R579 那一课）⇒ 这一支只落读数、不选边。

四组读数：
① 恒等式：本轮变帧总数 = 已登记 + 未登记（只报"拦路 17"不够 —— 17 是拦路的，不是变帧的；
   拦路 = 未登记 + 出处不符，那一行由 `frame_baseline.py check` 自己报，这一支不重复数）。
② 名册本机行逐行：行内旧值（observed.frame_sha / baseline_sha）↔ 本轮新值 ↔ 这台机器上历次**同倍率**
   会话里那张帧的字节哈希。行内旧值在任何一趟会话里都逐字找不到 ⇒ 它的"出处"不是这台机器看到的对象（甲）；
   在早几趟里逐字命中、本轮对不上 ⇒ 漂移真的会再动（乙）。
③ 每张变帧的"值史"（run-length）+ 本轮那个值**第一次出现于哪一趟** ⇒ 把"什么时候再动的"钉成读数。
④ 像素一侧：字节差再分成"画面真的变了"与"只有编码变了"（R585：RGBA 差值图上 getbbox() 恒 None，
   包围盒不许单独当证人 ⇒ 这里用逐字节/逐像素计数，不用包围盒）。

倍率是这道题的前提不是脚注：1x 与 2x 的同名帧不是同一个对象（R555 那一课）⇒ 跨会话对照只在**同倍率**
会话之间做，不同倍率的目录一律排除并点名。

只读：不改名册、不 restamp、不 update、不写基线。口径一律复用 frame_baseline 自己的函数。
"""
from __future__ import annotations

import datetime
import glob
import io
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, "scripts"))
import frame_baseline as fb  # noqa: E402  —— 复用被测系统自己的口径，不另建一份哈希算法

TODAY = sys.argv[1] if len(sys.argv) > 1 else "/tmp/r593v1"
LAST_N = int(sys.argv[2]) if len(sys.argv) > 2 else 14
SCAN_ROOTS = sorted(glob.glob(os.path.join("/tmp", "r5*")))


def session_dirs():
    """每个含 ≥300 张 PNG 的会话目录，带倍率与时间戳（目录名带轮次 ⇒ 可复查）。"""
    out = []
    for root in SCAN_ROOTS:
        if not os.path.isdir(root):
            continue
        for d in [root] + sorted(p for p in glob.glob(os.path.join(root, "*")) if os.path.isdir(p)):
            if len(glob.glob(os.path.join(d, "*.png"))) >= 300:
                try:
                    info = fb.capture_scale(d)
                    scale = info.get("scale")
                except Exception as exc:
                    scale = u"读不出(%s)" % type(exc).__name__
                out.append((os.path.getmtime(d), d, scale))
                break
    out.sort()
    return out


def run_length(seq):
    out = []
    for item in seq:
        if out and out[-1][0] == item:
            out[-1][1] += 1
        else:
            out.append([item, 1])
    return out


def main():
    base_path, against = fb.resolve_baseline_path(REPO, "working")
    baseline = fb.load_baseline(base_path)
    current = fb.collect(TODAY)
    machine = fb.machine_key(os.environ)
    rows = fb.load_drift_registry(fb.drift_registry_path(REPO))
    ours = [r for r in rows if r.get("machine") == machine]
    by_name = {r["frame"]: r for r in ours}
    digest = fb.baseline_digest(baseline)

    changed = sorted(n for n, h in current.items() if baseline.get(n) != h)
    added = sorted(n for n in current if n not in baseline)
    reg_hits = [n for n in changed if n in by_name]
    unreg = [n for n in changed if n not in by_name]

    sess = session_dirs()
    scales = sorted({s for _, _, s in sess})
    print(u"DRIFT_IDENTITY 本轮目录=%s 倍率=%s 基准=%s(%s) png=%d 会话目录=%d 倍率取值=%s"
          % (TODAY, json.dumps(fb.capture_scale(TODAY).get("scale"), ensure_ascii=False),
             os.path.relpath(base_path, REPO), against, len(current), len(sess), u",".join(scales)), flush=True)
    print(u"DRIFT_IDENTITY 变帧=%d 已登记=%d 未登记=%d 新帧=%d 恒等式=%s"
          % (len(changed), len(reg_hits), len(unreg), len(added),
             u"成立" if len(changed) == len(reg_hits) + len(unreg) else u"不成立"), flush=True)

    # 同倍率的最近 N 趟（今天的目录一定排在最后）：跨会话对照只在同倍率之间做
    today_scale = fb.capture_scale(TODAY).get("scale")
    hist = [(m, d) for m, d, s in sess if s == today_scale][-LAST_N:]
    tables = []
    for m, d in hist:
        tables.append((datetime.datetime.fromtimestamp(m).strftime("%m-%d %H:%M"), d, fb.collect(d)))
    print(u"DRIFT_HISTORY 同倍率会话取=%d 趟（%s … %s）"
          % (len(tables), tables[0][0] if tables else u"无", tables[-1][0] if tables else u"无"), flush=True)

    print(u"DRIFT_REGISTERED 本机=%s 行=%d 本轮清单 digest=%s" % (machine, len(ours), digest[:12]), flush=True)
    for r in ours:
        name = r["frame"]
        obs = r.get("observed") or {}
        want = (obs.get("frame_sha") or u"")
        bwant = (obs.get("baseline_sha") or u"")
        hits = [t[0] for t in tables if t[2].get(name) == want]
        print(u"  行 %s 登记轮=%s 行内帧值=%s 本轮=%s 相等=%d 行内基线值=%s 与本轮清单同=%d "
              u"旧值在同倍率会话里逐字命中=%d/%d 命中趟=%s"
              % (name, r.get("registered_by_round", u"?"), want[:12], (current.get(name) or u"缺")[:12],
                 1 if want == current.get(name) else 0, bwant[:12], 1 if bwant == digest else 0,
                 len(hits), len(tables), u",".join(hits[-4:]) if hits else u"无一次相同"), flush=True)

    alpha = {}
    print(u"DRIFT_VALUE_HISTORY 每张变帧的字节值史（字母=同一个 12 位哈希；* 点名册行内旧值；"
          u"⇒ 甲=旧值任何一趟都不在，乙=旧值在早几趟在、本轮换了字母）", flush=True)
    for name in changed:
        seq = []
        for stamp, d, tab in tables:
            v = tab.get(name, u"")
            key = v[:12]
            if key not in alpha:
                alpha[key] = chr(ord('A') + len(alpha)) if len(alpha) < 26 else u"Z%d" % len(alpha)
            mark = u"*" if by_name.get(name) and (by_name[name].get("observed") or {}).get("frame_sha", u"")[:12] == key else u""
            seq.append(alpha[key] + mark)
        cur_key = alpha[(current.get(name) or u"")[:12]]
        first = next((tables[i][0] for i in range(len(tables)) if seq[i].rstrip(u"*") == cur_key), u"?")
        print(u"  %s 本轮值=%s 第一次出现于=%s 登记=%s"
              % (u" ".join(run_repr(run_length(seq))), cur_key, first,
                 u"已登记" if name in by_name else u"未登记"), flush=True)

    try:
        from PIL import Image
    except ImportError:
        print(u"DRIFT_PIXEL=absent 没有 PIL ⇒ 像素那一侧没读数，只有字节读数", flush=True)
        return 0
    prev_tab = tables[-2][1] if len(tables) >= 2 else None
    print(u"DRIFT_PIXEL 对照=%s vs %s（字节差再分：画面真的变 / 只有编码变）"
          % (os.path.basename(prev_tab or u"无"), os.path.basename(TODAY)), flush=True)
    n_same, n_diff, n_none = 0, 0, 0
    for name in changed:
        pa = os.path.join(prev_tab or u"", name)
        pb = os.path.join(TODAY, name)
        if not (os.path.exists(pa) and os.path.exists(pb)):
            print(u"  像素 %s 一侧没文件 ⇒ 这一张不判" % name, flush=True)
            n_none += 1
            continue
        ia = Image.open(pa).convert("RGBA")
        ib = Image.open(pb).convert("RGBA")
        if ia.size != ib.size:
            print(u"  像素 %s 尺寸不同 %s vs %s" % (name, ia.size, ib.size), flush=True)
            n_diff += 1
            continue
        sa, sb = ia.tobytes(), ib.tobytes()
        diff = sum(1 for x, y in zip(sa, sb) if x != y)
        over8 = sum(1 for i in range(0, len(sa), 4)
                    if abs(sa[i] - sb[i]) > 8 or abs(sa[i + 1] - sb[i + 1]) > 8 or abs(sa[i + 2] - sb[i + 2]) > 8)
        if diff == 0:
            print(u"  像素 %s 字节不同但像素逐位相同=1 ⇒ 差在编码不在画面" % name, flush=True)
            n_same += 1
        else:
            print(u"  像素 %s 不同字节=%d 超8档像素=%d ⇒ 画面%s"
                  % (name, diff, over8, u"真的变了" if over8 else u"只在 8 档以内动"), flush=True)
            n_diff += 1
    print(u"DRIFT_PIXEL_SUM 对象=%d 像素未变=%d 像素已变=%d 没文件=%d"
          % (len(changed), n_same, n_diff, n_none), flush=True)
    return 0


def run_repr(rl):
    out = []
    for val, cnt in rl:
        out.append(u"%s×%d" % (val, cnt) if cnt > 1 else val)
    return out


if __name__ == "__main__":
    sys.exit(main())

# -*- coding: utf-8 -*-
"""R594 落盘之后的派生格：streak 两格 + §1。

规矩（R569 那一族第 13 次）：派生格**只在本轮那一小节内**找，锚不到就当场报错，绝不回头改历史；
取数时刻由函数名字钉住（`post_land`），不写在纪律上。
"""
from __future__ import annotations

import io
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TMP = "/tmp/r594"


def sh(args):
    proc = subprocess.Popen(args, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            universal_newlines=True)
    out, _ = proc.communicate(timeout=900)
    return out or u""


def main():
    reading = sh([sys.executable, "scripts/product_streak.py"])
    line = [l.strip() for l in reading.splitlines() if l.startswith(u"PRODUCT_STREAK ledger_round")][0]
    streak_n = int(re.search(r"streak=(\d+)", line).group(1))
    landed_r = max(int(x) for x in re.findall(r"(?m)^## R(\d+) 状态",
                                              io.open(os.path.join(ROOT, "AGENT_STATE.md"),
                                                      encoding=u"utf-8").read()))

    st_path = os.path.join(ROOT, "AGENT_STATE.md")
    st = io.open(st_path, encoding=u"utf-8").read()
    head_at = re.search(u"(?m)^## R%d 状态（" % landed_r, st)
    if not head_at:
        raise SystemExit(u"ANCHOR-MISS：读不到本轮（R%d）那一节" % landed_r)
    nxt = re.search(u"(?m)^## R\\d+ 状态（", st[head_at.end():])
    section = st[head_at.start(): head_at.end() + (nxt.start() if nxt else len(st))]
    if re.search(u"连续零改动[ \\t]*\\*\\*[0-9]+\\**[ \\t]*轮", section):
        print(u"STATE streak 格已在盘上 ⇒ 幂等重放，不写")
    else:
        anchor = u"⑦ **基线与名单**：本轮动过的文件 "
        if section.count(anchor) != 1:
            raise SystemExit(u"ANCHOR-MISS STATE ⑦：锚点命中 %d 次 ⇒ 不敢猜切点" % section.count(anchor))
        cell = (u"⑦ **基线与名单**：产品文件 4 个（`MainWindowCollapsePolicy.swift`、"
                u"`MainWindowCollapseController.swift`、`WindowConfigurator.swift`、`ContentView.swift`），"
                u"连续零改动 **%d** 轮（唯一取数口 "
                u"`python3 scripts/product_streak.py`，**台账落盘之后**现读 `%s`；as-of 口径 ⇒ 读作"
                u"「本轮之前最后一次产品改动在 %d 轮前」；本轮又是产品轮 ⇒ 下一轮那一格的分界换成本笔、"
                u"读 1 —— 用户要的『回到 0』在这一把尺上到不了 0（`streak_at` 用严格小于，"
                u"本轮自己那一笔不记进自己那一格），**复位值就是 1**〔streak-cell-end〕）。"
                u"本轮动过的其余文件 "
                % (streak_n, line, streak_n))
        off = head_at.start() + section.index(anchor)
        st = st[:off] + cell + st[off + len(anchor):]
        io.open(st_path, u"w", encoding=u"utf-8", newline=u"\n").write(st)
        print(u"STATE ⑥ streak 格已写（streak=%d）" % streak_n)

    fin_path = os.path.join(ROOT, "AGENT_FINAL_REPORT.md")
    fin = io.open(fin_path, encoding=u"utf-8").read()
    m2 = re.search(u"产品面连续零改动轮数 = \\*\\*（落盘之后现读）\\*\\*（R%d 台账落盘之后现读" % landed_r, fin)
    if not m2:
        m2 = re.search(u"产品面连续零改动轮数 = \\*\\*(-?\\d+)\\*\\*（R%d 台账落盘之后现读" % landed_r, fin)
    if not m2:
        raise SystemExit(u"ANCHOR-MISS FINAL：本轮那一格现读不到")
    end = fin.index(u"上一格原文留着：", m2.start())
    cell = (u"产品面连续零改动轮数 = **%d**（R%d 台账落盘之后现读 `python3 scripts/product_streak.py` ⇒ `%s`；"
            u"as-of 口径 ⇒ 读作「本轮之前最后一次产品改动在 %d 轮前」；本笔是产品轮 ⇒ 下一轮的分界换成本笔、读 1"
            u"（这把尺的复位值是 1，不是 0：`streak_at` 用严格小于）。"
            % (streak_n, landed_r, line, streak_n))
    fin = fin[:m2.start()] + cell + fin[end:]
    io.open(fin_path, u"w", encoding=u"utf-8", newline=u"\n").write(fin)
    print(u"FINAL streak 格已写（streak=%d）" % streak_n)

    # §1 的 U 上界与「仍开」那一行的指针 —— 这两格也是派生格，从前每轮靠人记得改（R580 那一族：
    # 派生格只补了一本 ⇒ 电池红在 `test_the_headline_cells_agree_with_the_live_ledgers`）。
    # 现在由这一趟一起算：U 上界 = UI 里最大的 U 号，指针 = 刚落盘那一轮的 R 号。
    ui_max = max(int(x) for x in re.findall(r"U-(\d+)",
                                            io.open(os.path.join(ROOT, "AGENT_UI_AUDIT.md"),
                                                    encoding=u"utf-8").read()))
    fin2 = io.open(fin_path, encoding=u"utf-8").read()
    # 锚点必须把**旧的那张贴纸一起吃掉**：只匹配 `U-31 … U-<数>` 的话，替换留在贴纸前面，
    # 于是每轮攒一张 ——「（R594 现读…）（R593 现读…）」这正是 R303 记过的那一族，本轮由
    # `test_the_u_cell_carries_exactly_one_derivation_note` 抓到（电池那一格，不是我看到的）。
    m3 = re.search(u"U-31 … U-(\\d+)(?:（R\\d+ 现读抬到最新一节）)*", fin2)
    if not m3:
        raise SystemExit(u"ANCHOR-MISS FINAL：§1 的 U 上界那一格现读不到")
    canonical = u"U-31 … U-%d（R%d 现读抬到最新一节）" % (ui_max, landed_r)
    if m3.group(0) != canonical:
        fin2 = fin2[:m3.start()] + canonical + fin2[m3.end():]
        print(u"FINAL U 上界写成规范形（旧贴纸一并抹掉）：%s" % canonical)
    m4 = re.search(u"完整名单以 `AGENT_STATE.md` 的 R(\\d+) 节 ② 为准", fin2)
    if not m4:
        raise SystemExit(u"ANCHOR-MISS FINAL：「仍开」那一行的指针现读不到")
    if int(m4.group(1)) != landed_r:
        fin2 = (fin2[:m4.start()] + u"完整名单以 `AGENT_STATE.md` 的 R%d 节 ② 为准" % landed_r
                + fin2[m4.end():])
        print(u"FINAL「仍开」指针改到 R%d" % landed_r)
    io.open(fin_path, u"w", encoding=u"utf-8", newline=u"\n").write(fin2)

    for cand in (os.path.join(ROOT, "scripts", "refresh_report_section1.py"),
                 os.path.join(ROOT, ".scratch", "motion-audit-2", "refresh_report_section1.py")):
        if os.path.exists(cand):
            out = sh([sys.executable, cand])
            print(u"§1 刷新（仪器=%s）:\n%s" % (cand, out.strip()[:400]))
            break
    else:
        raise SystemExit(u"post-land：两处候选路径都找不到 §1 仪器 ⇒ 不许静默跳过（R592 ⑨·8 那一课）")
    io.open(os.path.join(TMP, "streak.txt"), u"w", encoding=u"utf-8").write(line + u"\n")
    return 0


if __name__ == u"__main__":
    sys.exit(main())

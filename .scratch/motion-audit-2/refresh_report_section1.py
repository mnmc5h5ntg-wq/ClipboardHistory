#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把报告 §1「阶段二多少轮」那一格刷成 `curve_from_ledger.py` 的现读数。

范围**只有 §1**，标题那一行故意不动 —— 理由由既有守卫自己签：
`scripts/tests/test_final_report_headline.py` 里 `FINAL_REPORT_HEADLINE_AHEAD` 那一条
拿标题的 `R9–R<NNN>` 与 ITERATION 的 **Round** 尾轮比大小（`claimed > live['last_round']` 就红），
⇒ 那个数一直是 **Round 口径**，只是标签写着 R。上一轮我按 R=Round+3 把它改成 R293，
于是它红 —— 错的是我改的单位，不是那道门。改标签文字会让它的正则解析不出（另一条红），
所以标签与单位不一致这件事留在 344/345 里显式记账，不在这一支里顺手改。

§1 里那四个数全部推导，一个都不手抄：
· `**N 轮**` 与 `PHASE2 n=N` ← 仪器 `PHASE2 n=`
· `R9–R<NNN>` 与 `Round <NNN>` ← 仪器 `rounds=9..N`（同一口径：Round）
"""
import io
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REPORT = os.path.join(ROOT, "AGENT_FINAL_REPORT.md")
CURVE = os.path.join(ROOT, ".scratch", "motion-audit-2", "curve_from_ledger.py")

CELL = re.compile(u"^(\\| 阶段二 \\*\\*)(\\d+)( 轮\\*\\*审计（R9–R)(\\d+)"
                  u"(；以 `curve_from_ledger\\.py` 的 `PHASE2 n=)(\\d+)"
                  u"(` 为准，最新一节是 `AGENT_VISUAL_ITERATION\\.md` 的 Round )(\\d+)", re.M)


def die(m):
    sys.stderr.write("REFRESH_SECTION1 REFUSED: " + m + "\n")
    raise SystemExit(1)


def rd(p):
    with io.open(p, encoding="utf-8") as h:
        return h.read()


def wr(p, t):
    with io.open(p, "w", encoding="utf-8") as h:
        h.write(t)


def instrument():
    env = dict(os.environ)
    env["PYTHONUTF8"] = "1"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    pipe = subprocess.Popen(["python3", CURVE], cwd=ROOT, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, env=env)
    txt = pipe.communicate()[0].decode("utf-8", "replace")
    if pipe.returncode != 0:
        die(u"曲线尺不是绿的（rc=" + str(pipe.returncode) + u"）")
    hit = re.findall(u"^PHASE2 n=(\\d+) rounds=(\\d+)\\.\\.(\\d+)", txt, re.M)
    if not hit:
        die(u"曲线尺没打出 PHASE2 n=… rounds=… ⇒ 没有可推的数")
    return hit[-1]


def refresh(report_text, inst, write=True):
    """返回 (新文本, 改了没有)。inst = (n, lo, hi)。"""
    n, lo, hi = inst
    m = CELL.search(report_text)
    if not m:
        die(u"§1 那一格的锚点解不出来 ⇒ 先打印原文再钉锚点，别硬改")
    if (m.group(2), m.group(4), m.group(6), m.group(8)) == (n, hi, n, hi):
        return report_text, False
    out = (report_text[:m.start()] + m.group(1) + n + m.group(3) + hi + m.group(5)
           + n + m.group(7) + hi + report_text[m.end():])
    if write:
        wr(REPORT, out)
    return out, True


def main():
    dry = u"--check" in sys.argv
    inst = instrument()
    out, changed = refresh(rd(REPORT), inst, write=not dry)
    if dry:
        print(u"REFRESH_SECTION1 CHECK " + (u"停旧数：§1" if changed else u"§1 已与仪器一致"))
        return 1 if changed else 0
    print(u"REFRESH_SECTION1 OK 改=" + (u"§1" if changed else u"无（已是现读数）")
          + u" n=" + inst[0] + u" 尾轮=" + inst[2] + u" 标题=未动（Round 口径，由既有守卫签）")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
# R258：刷 FINAL_REPORT 的三张格。数字一律现读，不手抄。
#   用法一（提交代码半之前）：report_cells_r258.py headline
#   用法二（提交代码半之后，带那笔的短 sha）：report_cells_r258.py sources <sha>
import re
import sys
import os

ROOT = "/Users/wangziyi/Codex_Project0"
UI = os.path.join(ROOT, "AGENT_UI_AUDIT.md")
ITER = os.path.join(ROOT, "AGENT_VISUAL_ITERATION.md")
REP = os.path.join(ROOT, "AGENT_FINAL_REPORT.md")


def die(m):
    sys.stderr.write("REPORT_CELLS REFUSED: " + m + "\n")
    raise SystemExit(2)


def rd(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def wr(p, t):
    with open(p, "w", encoding="utf-8") as f:
        f.write(t)


def sub_once(text, pat, new, label):
    hits = re.findall(pat, text)
    if len(hits) != 1:
        die(label + " 的锚点命中 " + str(len(hits)) + " 次（要求恰好 1 次）")
    return re.sub(pat, new, text, count=1)


mode = sys.argv[1] if len(sys.argv) > 1 else "headline"
ui = rd(UI)
ids = [int(x) for x in re.findall(r"- \*\*U-(\d+)", ui)]
if not ids:
    die("UI_AUDIT 里一个 U 定义都没有")
mx, cnt = max(ids), len(ids)
it = rd(ITER)
rounds = [int(x) for x in re.findall(r"^## Round (\d+) ·", it, re.M)]
if not rounds:
    die("ITERATION 读不到轮次号")
last_round = max(rounds)
t = rd(REP)

if mode == "headline":
    t = sub_once(t, r"R9–R\d+，\d+ 轮自评", "R9–R" + str(last_round) + "，" + str(last_round) + " 轮自评",
                 "标题轮次格")
    # 刷新者那一格由 UI_AUDIT **最大轮次**那一节的 R 标签派生 —— 上一版把 "R258" 写死在替换文本里，
    # 于是 R262 之后每次刷新都会说"这是 R258 现读的数"（假出处）。
    # 也不许取"文件里第一个匹配"：R256 那节是**补记**，插在降序块之上（现读第 366 行），
    # 按文本顺序取会拿到 R256（R262 撞过一次，正对照就是它）。
    sections = re.findall(r"^## 第 (\d+) 轮（(R\d+) / ", ui, re.M)
    if not sections:
        die("UI_AUDIT 读不到任何一节的 R 标签 ⇒ 出处那一格不许手抄")
    tag = max(sections, key=lambda s: int(s[0]))[1]
    t = sub_once(t, r"U-31 … U-\d+（R\d+：[^；]*；\d+ 条定义行是 R\d+ 现读的数",
                 "U-31 … U-" + str(mx) + "（" + tag + "：现读刷新到最新一节之后；" + str(cnt)
                 + " 条定义行是 " + tag + " 现读的数", "U 上界格")
    wr(REP, t)
    print("REPORT_CELLS headline last_round=" + str(last_round) + " maxU=" + str(mx) + " defs=" + str(cnt))
elif mode == "sources":
    sha = sys.argv[2] if len(sys.argv) > 2 else ""
    if not re.fullmatch(r"[0-9a-f]{7,40}", sha):
        die("sources 模式要一个真实的短 sha（只能来自 git rev-parse，不许编）")
    # 锚点按**行首标签**认（不按上一版的正文认）：R270 撞过一次 —— 旧锚点要求句尾出现
    # 「上一笔动源码是 R253」，而那格早在 R263 就被改写 ⇒ 命中 0 次。守卫用的也是这个标签，
    # 所以尺与闸门读同一个对象（D-247）。
    pat = r"\| 最后一次动到 `Sources/` 的轮次 \|.*\n"
    new = ("| 最后一次动到 `Sources/` 的轮次 | **R270**（commit `" + sha + "`）—— 1 文件，"
           "**动的是常量的可见性，不是画面**：`DailyCopyLedger.visibilityGrace` 从 private let 升成 "
           "internal static let，判据的观察窗口不再抄值而是读它（D-256；新尺 ledger_timing_scan 9 格 + 刀 M830；"
           "行为不变由同一格改前改后两份读数与帧基线 changed=0 签）。上一笔是 R263（收藏星字形墨那一抬）。\n")
    t = sub_once(t, pat, new.replace("\\", "\\\\"), "Sources 格")
    wr(REP, t)
    print("REPORT_CELLS sources sha=" + sha + " maxU=" + str(mx))
else:
    die("未知模式 " + mode)

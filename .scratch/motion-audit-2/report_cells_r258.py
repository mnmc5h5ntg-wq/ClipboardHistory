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
    pat = r"\| 最后一次动到 `Sources/` 的轮次 \|.*?上一笔动源码是 R253"
    new = ("| 最后一次动到 `Sources/` 的轮次 | **R258**（commit `" + sha + "`）—— 1 文件，**动的是取证面不是画面**："
           "`EnvironmentValues.pressedForCapture` 让按下那一档第一次可拍、可量、可被刀红回来"
           "（台阶读数 U-836、两把刀各钉一条轴 D-244、看图 U-838；产品侧写这颗键=0 有守卫）。"
           "上一笔是 R256（`c7d8385`：亮档 pressed 抬量 0.015→0.03，那一笔的代价账记在 D-242/D-243 与第 255 轮）。"
           "上一笔动源码是 R253")
    t = sub_once(t, pat, new.replace("\\", "\\\\"), "Sources 格")
    wr(REP, t)
    print("REPORT_CELLS sources sha=" + sha + " maxU=" + str(mx))
else:
    die("未知模式 " + mode)

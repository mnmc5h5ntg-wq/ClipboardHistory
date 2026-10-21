#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R279 补记：把 R277 / R278 两笔「只落了一本账」的轮次补成三本齐（第 276、277 轮 / Round 274、275）。

为什么由本脚本做：R279 的账落盘之后，`test_round_batch_consistency` 与 `test_curve_gaps` 同时点名
R277/R278 缺于三本账、曲线断档 GAPS=[274,275]。这两笔当时确实只动了 BACKLOG（回退记账与机制更正），
但**曲线不认申报通道** —— 少一轮就把均值算错（R197 那笔的先例：当时也是靠 patch_r197_backfill.py 补的）。
所以这里补的是真正文，不是桩标题。

分数按实记低：两笔都是 0 判据、0 产品、0 新位点看图。
"""
import io
import os
import re
import subprocess
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DATE = "2026-10-21"


def die(m):
    sys.stderr.write("BACKFILL_R277_R278 REFUSED: " + m + "\n")
    raise SystemExit(2)


def rd(p):
    with io.open(p, encoding="utf-8", errors="replace") as h:
        return h.read()


def sh(cmd):
    env = dict(os.environ)
    env["PYTHONUTF8"] = "1"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    pr = subprocess.run(cmd, cwd=ROOT, env=env, capture_output=True, text=True)
    return (pr.stdout or "") + (pr.stderr or ""), pr.returncode


def files_of(sha):
    out, rc = sh(["git", "show", "--name-only", "--format=", sha])
    if rc != 0:
        die("读不到 " + sha + " 的改动文件：" + out[-160:])
    return [l.strip() for l in out.splitlines() if l.strip()]


# 正文里的"动了哪些文件"必须由 git 现读，不许照抄提交信息（R273 那条：台账里的数字要能复查）
F277 = files_of("759b0df") + files_of("268287d")
F278 = files_of("bfb8acf") + files_of("41e5ce0")
for tag, fs in (("R277", F277), ("R278", F278)):
    if any(f.startswith("ClipboardHistory/") for f in fs):
        die(tag + " 现读动了 ClipboardHistory/ ⇒ 本轮正文那句「0 判据 0 产品」是假话，先改文案")
N277 = len(set(os.path.basename(f) for f in F277))
N278 = len(set(os.path.basename(f) for f in F278))


def table(scores):
    names = ["真实视觉审查", "判据有效性", "假绿防御", "产品面推进", "台账一致性", "交付诚实性", "可复核性"]
    rows = "\n".join("| %s | %d/15 |" % (n, s) for n, s in zip(names, scores))
    return rows, sum(scores)


S277 = [5, 8, 12, 0, 12, 15, 11]
S278 = [5, 9, 13, 0, 12, 15, 12]
R277_ROWS, SUM277 = table(S277)
R278_ROWS, SUM278 = table(S278)

UI277 = """## 第 276 轮（R277 / 第 276 轮 / Round 274 · %s）：331 两次尝试都回退了 —— 回退的原因各留下一组读数，spike 不进判据（U-927…U-929 / 产品 0 文件）【R279 补记】

本轮次对照：与 R276（自评 79，门只扫直接 import）相比，本轮没有落地任何判据，做的是"把一条走不通的路证伪并写清下一步形状"。
本节由 R279 补落（当时只动了 AGENT_BACKLOG.md 的追记二/追记三）；正文里的文件数由 `git show --name-only 759b0df 268287d` 现读（%d 个文件，全在台账与 .scratch）。

- **U-927：静态扫源码预测谁会 skip —— 两种错法都有读数** —— 第一版按"def test_x … skipTest(" 跨行匹配，把后面格子的 skip 记到前面格子头上：现读 15 条 findings 里 4 条 STALE 是尺自己造的。改成只认语句级 `self.skipTest(` 之后认出 8 处，而名册说本机该跳的 4 格里只认出 2 格 —— 因为 skip 的形状至少三种（装饰器 `@unittest.skipUnless(...)`、语句级但理由讲数据形状、以及藏在 helper 里）。结论：这条路对"谁会 skip"没有足够分辨力 ⇒ 整支回退。
- **U-928：观测式（把电池跑成子进程）第一版坏在归属，正对照当场抓住** —— 防递归与"排除观察者恰好 1 格"两条都工作（现读 排除观察者=1 通过），但内层只认出 2 格、名册说 4 格 ⇒ 两格被误报成 NOT_SKIPPING_ANYMORE。根因：`unittest -v` 把格子 docstring 打在第一行、把 `... skipped '理由'` 落在另一行，那两行行首不是 `test_x (模块.类)`，按 marker 切拿不到 id。我自己写的正对照格把这条 bug 抓了出来（它多认出一条 `mod.SomeTests)` 这种 docstring 拼出来的垃圾 id）。
- **U-929：下一版的形状因此是确定的，且回退笔也要留实物** —— 按"表头行 + 结果行"配对归属，并加一条恒等式闸门：解析出的 id 数必须等于内层汇总行 `OK (skipped=N)` 的 N 减去观察者那一格，不相等就红（少认一格正是这次的红法）。spike 留在 `.scratch/spikes/skip_roster_spike.py`（它现在还会 `KeyError: None`，正是"理由认不出通道"那一类没处理干净的实物），仓库净变化 0 个判据文件；脚本电池回到 Ran 521 / OK (skipped=4)。

眼睛腿：NOT-RUN —— 本轮没有新位点可看，也没有重捕帧。读数腿：RUN —— 上面三格里的 15/4、8/4/2、排除观察者=1 都是脚本自己打印的现读值。产品腿：0 文件。

""" % (DATE, N277)

UI278 = """## 第 277 轮（R278 / 第 277 轮 / Round 275 · %s）：一笔好消息 + 一次公开更正 —— runner 第一次给 D-260/D-262 这条链签字，而我上一笔把脚本回显当成了执行输出（U-930…U-932 / 产品 0 文件）【R279 补记】

本轮次对照：与 R277（自评 %d，两版 331 都回退）相比，本轮拿到的是"修仪器"那条链的 runner 验收，代价是自曝一笔假指控。
本节由 R279 补落（当时动了 AGENT_STATE.md 与 AGENT_BACKLOG.md 两本）；文件数由 `git show --name-only bfb8acf 41e5ce0` 现读（%d 个文件，全在台账）。

- **U-930：D-260 / D-262 这条链第一次被 runner 签字** —— `99f3284 → 39591885399 = completed / success`，STEP[9]「Release script tests」现读 `Ran 521 tests / OK (skipped=1)`；同一跑里 `mutate_r271` 的镜像对账格不再红 ⇒ "R51 归根 + exec 命名空间补 `__file__`"两处都生效，且不是靠放宽。
- **U-931：公开更正 —— 「硬门在 runner 上等于不存在」是假的，成因是我读错了日志** —— 上一笔我按步骤名过滤，同一步里既看到 `FRAME_BASELINE_SKIPPED=runner-capture-unavailable` 又看到 `CHANGED=170` 却 exit 0。真相：`--log` 的回显段含 GitHub 打印的脚本正文，按 `##[endgroup]` 之后切执行段再数，SKIPPED 出现 0 次，那条 `count<60` 的整步放行今天根本没走过。教训写进 D-263：**按步骤名过滤日志 ≠ 拿到执行输出**。
- **U-932：更正之后剩下的那半句仍是真问题，而且比原话更窄** —— `frame_baseline.py` 的 `check` 模式按设计只在 missing 时返回 1（源码注释：只要求一帧不许少，多帧与变帧交给人判断），所以 CHANGED=170 → exit 0 正是该步名字（fixture-set gate）声明的行为。留下的是：runner 那次捕获与本机整体不同（COMPARED=170 CHANGED=170 MISSING=0 ADDED=0），而"改界面没在同一笔 update 基线"在任何一侧都没有闸门 ⇒ 333 收窄成"给 changed 开一条按机器键的具名出口 + 两把刀"，本笔只改台账、判据零改动。

眼睛腿：NOT-RUN —— 本轮没有新看位点（读数全在 CI 文本通道）。读数腿：RUN —— run 39591885399 的 STEP[9] 结论行、执行段里 SKIPPED 计数 0、CHANGED=170/COMPARED=170。产品腿：0 文件。

""" % (DATE, SUM277, N278)

IT274 = """## Round 274 · 331 两次尝试都回退：静态预测没有分辨力、观测式坏在归属，正对照当场抓住自己的尺（R277 / 第 276 轮）/ 产品 0 文件【R279 补记】

本轮次对照：与 R276（自评 79）相比，本轮 0 判据落地，产出是"这条路为什么走不通"的两组读数与下一版的确定形状。
看图腿：NOT-RUN —— 没有新位点、没有重捕帧。
读数腿：RUN —— 第一版 15 条 findings 里 4 条 STALE；第二版认出 8 处而名册只说 4 格、只覆盖其中 2 格；观测式内层认出 2 格、排除观察者=1 通过。
七维度自评：
%s
各维理由：真实视觉审查 %d —— 没看图；判据有效性 %d —— 没有新判据落地，只有被证伪的两版；假绿防御 %d —— 正对照格把归属 bug 抓了出来，且两版都整支回退而不是留下半套；产品面推进 %d —— 0 文件；台账一致性 %d —— 当时只落 BACKLOG 追记（本节由 R279 补落，缺口写进正文而不是掩盖）；交付诚实性 %d —— 回退原因、spike 现在还会长 `KeyError: None` 都记在账上；可复核性 %d —— spike 留在 `.scratch/spikes/`，两笔提交的仓库净变化可查。合计 **%d**/105。

""" % (R277_ROWS, S277[0], S277[1], S277[2], S277[3], S277[4], S277[5], S277[6], SUM277)

IT275 = """## Round 275 · runner 第一次给 D-260/D-262 这条链签字，而我上一笔把脚本回显当成了执行输出（R278 / 第 277 轮）/ 产品 0 文件【R279 补记】

本轮次对照：与 R277（自评 %d，两版回退）相比，本轮拿到验收也交出一次假指控 —— 两件事都留在同一节里。
看图腿：NOT-RUN —— 本轮读数全在 CI 文本通道。
读数腿：RUN —— run 39591885399 STEP[9] `Ran 521 / OK (skipped=1)`；执行段里 `FRAME_BASELINE_SKIPPED` 计数 0；`COMPARED=170 CHANGED=170 MISSING=0 ADDED=0`。
七维度自评：
%s
各维理由：真实视觉审查 %d —— 没看图；判据有效性 %d —— 没有新判据，但把 333 从"门失效"收窄成"changed 没有闸门 + 需要按机器具名出口"；假绿防御 %d —— 自己上一笔的假指控被同一轮用 `##[endgroup]` 切片证伪，并升成 D-263；产品面推进 %d —— 0 文件；台账一致性 %d —— 当时只动两本账（本节由 R279 补落）；交付诚实性 %d —— 更正写在提交信息与 BACKLOG 追记里，没有偷偷改写；可复核性 %d —— run 号、步骤号、计数命令都在账上可重跑。合计 **%d**/105。

""" % (SUM277, R278_ROWS, S278[0], S278[1], S278[2], S278[3], S278[4], S278[5], S278[6], SUM278)

CG277 = """### 回退记账（R277 / 第 276 轮 / Round 274 · 331 两次尝试）【R279 补记】

静态扫源码预测"谁会 skip"没有足够分辨力（跨行匹配把后面的 skip 记到前面格子头上，现读 15 findings/4 STALE；改成语句级只认 8 处而名册说 4 格、只覆盖 2 格，skip 形状至少三种）；观测式（把电池跑成子进程）防递归与排除观察者都工作（排除观察者=1 通过），但归属仍坏 —— `unittest -v` 把 docstring 与 `... skipped` 打在两行，按 marker 切拿不到 id，内层只认出 2 格 ⇒ 两格误报 NOT_SKIPPING_ANYMORE，我自己写的正对照格当场抓出这条 bug。两版都不进仓库判据（净变化 0），spike 留 `.scratch/spikes/skip_roster_spike.py`。下一版形状确定：表头行 + 结果行配对归属 + 恒等式闸门（解析 id 数 == 内层 `OK (skipped=N)` − 观察者那一格）。电池 Ran 521 OK (skipped=4)。

"""

CG278 = """### 交账与更正（R278 / 第 277 轮 / Round 275 · runner 签字 + 撤回一句假指控）【R279 补记】

好消息：`99f3284 → 39591885399` completed/success，STEP[9] 现读 `Ran 521 tests / OK (skipped=1)` ⇒ D-260（写死本机根）与 D-262（可达闭包）这条链第一次拿到 runner 验收，且不是靠放宽。坏消息：上一笔那句"硬门在 runner 上等于不存在"是我把 GitHub 回显的脚本正文当成执行输出 —— 按 `##[endgroup]` 之后切执行段再数，`FRAME_BASELINE_SKIPPED` 出现 0 次，`count<60` 那条整步放行今天没走过；`check` 按设计只在 missing 时返回 1，所以 CHANGED=170 → exit 0 正是该步声明的行为。撤回归因，但真问题剩半句且更窄：runner 那次捕获与本机整体不同（COMPARED=170 CHANGED=170），而"改界面没在同一笔 update 基线"两侧都没有闸门 ⇒ 333 收窄成"changed 的按机器具名出口 + 两把刀"（本机半由 R279 落地）。教训升成 D-263：按步骤名过滤日志 ≠ 拿到执行输出。

"""


def must_preserve(old, new, name):
    cn = Counter(new.splitlines())
    lost = [l for l, c in Counter(old.splitlines()).items() if cn[l] < c]
    if lost:
        die(name + " 弄丢 " + str(len(lost)) + " 行：" + " | ".join(lost[:2])[:140])


ui_p = os.path.join(ROOT, "AGENT_UI_AUDIT.md")
ui = rd(ui_p)
for tag in ("（R277 /", "（R278 /"):
    if tag in ui:
        die("UI_AUDIT 已有 " + tag + " 那一节 ⇒ 本脚本不幂等，先还原再重跑")
anchor = "## 第 275 轮"
if ui.count(anchor) != 1:
    die("UI_AUDIT 锚点命中 %d 次（要恰好 1）" % ui.count(anchor))
ui_new = ui.replace(anchor, UI277 + UI278 + anchor, 1)
must_preserve(ui, ui_new, "AGENT_UI_AUDIT.md")

it_p = os.path.join(ROOT, "AGENT_VISUAL_ITERATION.md")
it = rd(it_p)
if re.search(r"^## Round 274 · ", it, re.M) or re.search(r"^## Round 275 · ", it, re.M):
    die("ITERATION 已有 Round 274/275 ⇒ 不幂等")
it_new = it.rstrip("\n") + "\n\n" + IT274 + IT275
if not it_new.startswith(it.rstrip("\n")):
    die("升序那本不是纯追加")

cg_p = os.path.join(ROOT, "CHANGELOG.md")
cg = rd(cg_p)
if "（R277 /" in cg or "（R278 /" in cg:
    die("CHANGELOG 已有 R277/R278 标题行 ⇒ 不幂等")
mark = "### Fixed（R279 / 第 278 轮 / Round 276"
if cg.count(mark) != 1:
    die("CHANGELOG 里找不到 R279 那一节（R279 的账还没落？）")
cg_new = cg.replace(mark, CG277 + CG278 + mark, 1)
must_preserve(cg, cg_new, "CHANGELOG.md")

for p, t in ((ui_p, ui_new), (it_p, it_new), (cg_p, cg_new)):
    with io.open(p, "w", encoding="utf-8") as h:
        h.write(t)

out, rc = sh([sys.executable, os.path.join(HERE, "report_cells_r258.py"), "headline"])
if rc != 0:
    die("FINAL_REPORT 刷新失败：" + out[-300:])

g, rc = sh([sys.executable, "scripts/ledger_round_numbers.py"]) if os.path.exists(
    os.path.join(ROOT, "scripts", "ledger_round_numbers.py")) else ("(无编号仪器)", 0)
b, rc2 = sh([sys.executable, "-m", "unittest", "discover", "-s", "scripts/tests"])
ran = re.findall(r"^Ran (\d+) tests", b, re.M)
if rc2 != 0 or not re.search(r"^OK", b, re.M):
    die("补记之后电池不绿（写盘已发生，请按下面的失败清单修，别回退正文）：\n" + "\n".join(
        l for l in b.splitlines() if l.startswith(("FAIL:", "ERROR:")) or "AssertionError" in l)[:1800])
print("BACKFILL_R277_R278 OK batt=Ran " + (ran[-1] if ran else "?") + " ui_files=" + str(N277 + N278) +
      " 现读文件数 R277=" + str(N277) + " R278=" + str(N278) + " 自评 " + str(SUM277) + "/" + str(SUM278) +
      " U=927..932")

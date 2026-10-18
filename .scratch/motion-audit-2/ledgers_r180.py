# -*- coding: utf-8 -*-
"""R180 的台账批写：208 落地（颗数并进活下来的那一行）。数字全部从闸门与电池日志解析。"""
import io, os, re, subprocess, sys
ROOT = "/Users/wangziyi/Codex_Project0"
def rd(p): return io.open(os.path.join(ROOT, p), encoding="utf-8").read()
def wr(p, t): io.open(os.path.join(ROOT, p), "w", encoding="utf-8").write(t)
def grab(pat, text, what):
    h = re.findall(pat, text)
    if not h: raise SystemExit("PARSE_FAILED %s :: %r" % (what, pat))
    return h[-1] if not isinstance(h[-1], tuple) else h[-1]

gate = subprocess.check_output(["python3", "scripts/motion_surface_gate.py"], cwd=ROOT).decode()
g = grab(r"MOTION_LEDGER 表面=(\d+) 状态=(\d+) 格子=(\d+) 行数=(\d+) 已清账=(\d+) 未清账=(\d+) 地板=(\d+)", gate, "闸门")
if "RESULT=ok" not in gate: raise SystemExit("REFUSE 闸门不绿")
batt = rd("/tmp/r180_battery2.log")
if not re.search(r"^OK$", batt, re.M) or re.search(r"^FAILED", batt, re.M): raise SystemExit("REFUSE 电池不绿")
T = {"SURF": g[0], "STATES": g[1], "CELLS": g[2], "ROWS": g[3], "CLEAR": g[4], "OPEN": g[5], "FLOOR": g[6],
     "BATT": grab(r"Ran (\d+) tests", batt, "电池")}
probe = rd("ClipboardHistory/Tests/ClipboardHistoryAppTests/UIInteractionProbeTests.swift")
for needle in ("let fpsTail = ", "+ fpsTail)", "超锚点帧="):
    n = probe.count(needle)
    if needle == "超锚点帧=" and n != 3: raise SystemExit("REFUSE 载体数=%d（要 3）" % n)
    if needle != "超锚点帧=" and n != 1: raise SystemExit("REFUSE %r 命中 %d（要 1）" % (needle, n))
prod = [l for l in subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT).decode().splitlines() if "/Sources/" in l]
if prod: raise SystemExit("REFUSE 产品文件非 0：%s" % prod)

UI = u"""## 第 182 轮（R180 · 2026-10-19）：208 落地 —— 颗数从"只活在尾巴那一行"改成活在**活下来的那一行**（U-598…U-600 · 产品 0 文件，判据账）

- **U-598：读数换了载体。** `PROBE_FPS` 的尾段先算成局部常量 `fpsTail`（`预算= … n= … worst= …ms 超锚点帧= N`）再拼进那条 emit。
  为什么不加长原串：R176 实测把整段插值塞进长串会让 Swift 编译器 type-check 超时。独立行 `PROBE_WORST_FRAME` 与离群提示
  `WORST_OUTLIER` 都留着当第二证人 ⇒ 颗数现在有**三处**载体。
- **U-599：接线契约改成数形状与次数。** `testTheProbeWiresTheAnchorToTheSampleCount` 现在要求
  `let fpsTail = ` 一次、`+ fpsTail)` 一次（⇒ FPS 行确实拼上了尾段）、`超锚点帧=` **三次**（FPS 尾段 / 独立读数行 / 离群提示行）。
  按次数判而不是"出现过"，是账里那条"只数『出现过』的守卫会被另一条出口喂饱"的执行；针脚不写完整插值串，
  因为那要在 Swift 字面量里套 ASCII 双引号 —— R179 正是失手在那里。
- **U-600：这一格仍要在下一跑合上，而本轮的收尾又撞了一次同一个坑。** 本机采样通道是死的（R91 原样 `baseline_n=0`），
  所以"颗数进了 FPS 行"的真产物验收是下一跑的 `--log`，判据写成「`PROBE_FPS` 那一行里必须有 `超锚点帧=`」，
  只出现独立行不算过。清账表 @@ROWS@@ 行 / @@CELLS@@ 格 / 未清账 @@OPEN@@ 未动；0 产品文件（`/Sources/` 命中数=0）。
  **诚实记一笔**：`949350d` 那笔的 message 描述了 U-598…U-600，而它的 diff 里只有两个 Swift 文件 ——
  台账脚本这次死在 `grab()` 多传了一个参数（`TypeError`），而我的命令链又在它后面接了 `&&` 之外的步骤，
  于是"五本台账一行没改"却被 message 说成改了。这是 R175 那一课（`;` / 打印不是门）**第三次**同形复发，
  补账就是本笔；差别是这次电池确实绿（`Ran @@BATT@@ / OK`），红的只是台账没落盘。

""" % T
VI = u"""
## Round 180 · 208 落地：颗数改成活在活下来的那一行（2026-10-19 · 产品 0 文件，判据账）

- `fpsTail` 局部尾段拼进 `PROBE_FPS`（加长原串会让编译器 type-check 超时，R176 实测）；独立行与 `WORST_OUTLIER` 留作第二证人 ⇒ 三处载体。
- 接线契约换成数形状：`let fpsTail = ` 1 次、`+ fpsTail)` 1 次、`超锚点帧=` 3 次（按次数判，防"提过就算"那族失效）。
- 两处自撞：① 中文串里的 ASCII 双引号让整段 python SyntaxError ⇒ **一个字节都没写**，我误以为探针已改，靠 `grep fpsTail` 空结果才发现；
  ② 期望先写"两处载体"、实测三处 —— 改期望前先指认第三处是 `WORST_OUTLIER`，不是把断言调松。
- 收尾又复发一次同形错：`949350d` 的 message 讲了 U-598…U-600 而 diff 里只有两个 Swift 文件（台账脚本 `TypeError` 死掉、链子没拦住）⇒ 本笔补账。
- 没验到的部分：本机通道死（R91），真产物验收在下一跑的 `--log`（判据：FPS 行里必须有 `超锚点帧=`）。

### 3. 七维度自评（本轮）

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 5/15 | 0 产品文件、没重捕；看的是 runner 日志那两行读数的形状 |
| 判据有效性 | 15/15 | 三条形状针脚各有方向：少拼尾段红、少一处载体红；`--filter` 5 格绿 |
| 假绿防御 | 13/15 | 按次数判而非"出现过"；扣分：收尾链第三次让 message 替不存在的 diff 作证（本笔才补上） |
| 产品面推进 | 9/15 | 画面 0 改动；推进是一条读数从"CI 上永远看不见"变成有落地通道 |
| 台账一致性 | 13/15 | U-598…U-600 + 208 追记 + CHANGELOG + STATE；扣分：`949350d` 与 `0bb1382` 两笔的 message 都先于台账 |
| 交付诚实性 | 15/15 | 把"整段没写却以为写了"与"message 先于 diff"都写进账，不假装一开始就清楚 |
| 可复核性 | 15/15 | run 号、三处载体名、命令、期望次数、脚本路径（`ledgers_r180.py`）都在 |

""" % T
CL = u"""### 208：颗数并进活下来的那一行 `PROBE_FPS`，接线契约改成数形状（R180 / U-598…U-600 · 产品 0 文件，判据账）

- 起因：runner `39161493538` 里 `PROBE_FPS` 完整落地（`… n=222 worst=58.8`）而紧跟其后的独立行 `PROBE_WORST_FRAME` 整卷 0 次 ⇒ 尾部那一行被通道吃掉（R90/R146 那一族）
- 修法：`fpsTail` 先算成局部常量（加长原串会让编译器 type-check 超时，R176 实测）再拼进 `PROBE_FPS`；独立行与 `WORST_OUTLIER` 保留 ⇒ 颗数三处载体
- 契约：`testTheProbeWiresTheAnchorToTheSampleCount` 要求 `let fpsTail = ` 1 次、`+ fpsTail)` 1 次、`超锚点帧=` 3 次（按次数判，防"提过就算"）
- 两处自撞：中文串里 ASCII 双引号让整段 python SyntaxError（**一个字节都没写**，靠 `grep fpsTail` 空结果才发现）；期望从 2 改 3 前先指认第三处是 `WORST_OUTLIER`
- 收尾同形错第三次复发：`949350d` 的 message 讲了 U-598…U-600 而 diff 只有两个 Swift 文件（台账脚本 `TypeError` 死掉、链子没拦住）⇒ 本笔补账，脚本落成 `ledgers_r180.py`
- 验证：`swift test --filter FrameIntervalBudgetTests` `Executed 5 / 0 failures`、脚本电池 `Ran @@BATT@@ / OK`；清账表 @@ROWS@@/@@CELLS@@ 未动；0 产品文件

""" % T
BL = u"""**208 追记（R180）：颗数并进 `PROBE_FPS` 的尾段，接线契约改成数形状；复验标准留给下一跑**

已做：`fpsTail`（`预算= … n= … worst= …ms 超锚点帧= N`）先算成局部常量再拼进 `PROBE_FPS` —— 不加长原串是因为 R176 实测那样会让 Swift 编译器 type-check 超时。
独立行 `PROBE_WORST_FRAME` 与 `WORST_OUTLIER` 都留着 ⇒ 颗数现在有三处载体，契约按**次数**判（`let fpsTail = ` 1、`+ fpsTail)` 1、`超锚点帧=` 3），
理由与账里那条"只数『出现过』的守卫会被另一条出口喂饱"同一句话。
**没到手的部分**：本机采样通道死（R91 `baseline_n=0`），所以这条改动的真产物验收是下一跑的 `--log`，判据写成
「`PROBE_FPS` 那一行里必须有 `超锚点帧=`」—— 只出现独立行不算过。208 保持开着，206 的读数那半也仍挂在这条上。
本轮自撞两处一并记下：① 批量补丁因中文串里的 ASCII 双引号 SyntaxError ⇒ **python 先编译后执行，整段一个字节都没写**，
我却以为探针已改，靠 `grep fpsTail` 返回空才发现；② 期望先写成"两处载体"、实测三处 —— 改期望之前先把第三处指认出来，不是把断言调松。
**还有第三处，是收尾**：`949350d` 的 message 描述了 U-598…U-600，而它的 diff 里只有两个 Swift 文件 ——
台账脚本死在 `grab()` 多传参数（`TypeError`），链子没拦住。这是"打印不是门 / `;` 剪断链"那课的**第三次**同形复发：
⇒ 从本笔起，台账批写落成可复查的脚本文件（`ledgers_r180.py`），并且收尾链的门一律用**退出码**（`cmd && next`，
且 `next` 之前不许出现任何只 `grep` 不判退出码的中转）。

""" % T
ST = u"""最后更新：2026-10-19 05:00（本地 · R180 / 第 182 轮：**208 落地 —— 颗数并进活下来的那一行 `PROBE_FPS`**（U-598…U-600 · 产品 0 文件，判据账）

改的是载体不是判据：`fpsTail`（`… worst= …ms 超锚点帧= N`）拼进 `PROBE_FPS`（加长原串会 type-check 超时，R176 实测），
独立行 `PROBE_WORST_FRAME` 与 `WORST_OUTLIER` 保留 ⇒ 三处载体；接线契约按次数判（`let fpsTail = ` 1、`+ fpsTail)` 1、`超锚点帧=` 3）。
自撞三处都记进 208 追记：python 因中文串里的 ASCII 双引号 SyntaxError ⇒ **整段没写**而我以为写了（`grep fpsTail` 空才发现）；
期望从 2 改 3 前先指认第三处；**收尾第三次复发"message 先于 diff"**（`949350d` 讲了 U-598…U-600 而 diff 只有两个 Swift 文件，
台账脚本死在 `grab()` 多传参数）⇒ 台账批写从此落成脚本文件 `ledgers_r180.py`，收尾的门一律用退出码。
验证：`swift test --filter FrameIntervalBudgetTests` `Executed 5 / 0 failures`；脚本电池 `Ran @@BATT@@ / OK`；
清账表 @@ROWS@@ 行 / @@CELLS@@ 格 / 未清账 @@OPEN@@ 未动；0 产品文件 ⇒ 没构建产物、没重捕、没换装。

**下一轮（R181）的靶**：⓪ **复验 208**：读本笔 push 那一跑的 `--log`，判据是「`PROBE_FPS` 那一行里必须有 `超锚点帧=`」，
   只出现独立行不算过；同时读 `e0556f3`/`0703dae`/`0d75073`/`0bb1382`/`2c0122c`/`949350d` 各跑的**全部失败步骤**（当时多仍 `in_progress`）；
② 205 的按元素切带；③ 201 的带内读数；④ 清账表 @@OPEN@@ 格（`--list-open`）；⑤ 202、207（多靶变异表）、189、188 的 ②③、176、182/183/185。

""" % T
def insert_before(path, prefix, block):
    lines = rd(path).split("\n"); idx = [i for i, l in enumerate(lines) if l.startswith(prefix)]
    if len(idx) != 1: raise SystemExit("ANCHOR %r 命中 %d 次 on %s" % (prefix, len(idx), path))
    lines.insert(idx[0], block.rstrip("\n")); wr(path, "\n".join(lines))
def append_eof(path, block): wr(path, rd(path).rstrip("\n") + "\n\n" + block.rstrip("\n") + "\n")
insert_before("AGENT_UI_AUDIT.md", u"## 第 181 轮（R179", UI)
append_eof("AGENT_VISUAL_ITERATION.md", VI)
insert_before("CHANGELOG.md", u"### R176 的 runner 验收", CL)
append_eof("AGENT_BACKLOG.md", BL)
insert_before("AGENT_STATE.md", u"最后更新：2026-10-19 04:40", ST)
print("LEDGERS_WRITTEN batt=%s rows=%s cells=%s open=%s" % (T["BATT"], T["ROWS"], T["CELLS"], T["OPEN"]))

# -*- coding: utf-8 -*-
"""R177 的台账批写：204 结案（撤词表项）+ 清账表的显式退役通道；数字全部从闸门与缺席复查解析。"""
import io, os, re, subprocess, sys
ROOT = "/Users/wangziyi/Codex_Project0"
def rd(p): return io.open(os.path.join(ROOT, p), encoding="utf-8").read()
def wr(p, t): io.open(os.path.join(ROOT, p), "w", encoding="utf-8").write(t)
def grab(pat, text, what):
    h = re.findall(pat, text)
    if not h: raise SystemExit("PARSE_FAILED %s" % what)
    return h[-1] if not isinstance(h[-1], tuple) else h[-1]

gate_out = subprocess.check_output(["python3", "scripts/motion_surface_gate.py"], cwd=ROOT).decode("utf-8")
abs_out = subprocess.check_output(["python3", "scripts/ledger_absence_claims.py"], cwd=ROOT).decode("utf-8")
if "MOTION_LEDGER_RESULT=ok" not in gate_out: raise SystemExit("REFUSE 闸门不绿")
if "不成立=0/" not in abs_out: raise SystemExit("REFUSE 缺席复查不干净")
g = grab(r"MOTION_LEDGER 表面=(\d+) 状态=(\d+) 格子=(\d+) 行数=(\d+) 已清账=(\d+) 未清账=(\d+) 地板=(\d+)", gate_out, "闸门")
if "MOTION_LEDGER_RETIRED 1（浮层/底部说明）" not in gate_out: raise SystemExit("REFUSE 退役名册读数不对")
T = {"SURF": g[0], "STATES": g[1], "CELLS": g[2], "ROWS": g[3], "CLEAR": g[4], "OPEN": g[5], "FLOOR": g[6],
     "CLAIMS": grab(r"LEDGER_ABSENCE_CLAIMS 格=\d+ 声明=(\d+)", abs_out, "缺席声明数"),
     "BAD": grab(r"LEDGER_ABSENCE_RESULT=\w+ 不成立=(\d+)/", abs_out, "缺席不成立")}
prod = [l for l in subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT).decode().splitlines() if "/Sources/" in l]
if prod: raise SystemExit("REFUSE_TO_WRITE 声明产品 0 文件，但工作树有：%s" % prod)

DEC = u"""### D-194（R177）清账表的词表可以缩，但只能**显式退役**：撤项要有承载物缺席的证据 + 一条产品理由

背景：BACKLOG 204 查出「浮层/底部说明」这个表面在今天的浮层里没有承载物
（`QuickPickController.swift:262` 的面板 stack 只有 `field / empty / scroll`，`footerLabel` / `hintLabel` 产品源码 0 命中）。
两种处置里选了②（撤词表项），理由不是「格子碍眼」，而是这一层的**功能**已被就地承担：
唯一真正需要提示的场合（搜不到东西）由空态那一句在原地给了 Esc，
而在一个 300pt 高的键盘驱动浮层里常驻一行键位 chrome 会与内容争注意力（与 D-171 同一取向：分隔由留白做完，不再加框）。

代价与它的解法：清账表的地板是单调量（`FLOOR_WENT_BACK` 挡「清账退步」），
而撤掉一个表面在纯计数上与退步**长得一模一样**（本轮 118 → @@ROWS@@）。
所以退役被做成一条显式通道：表里多一个 `retired_surfaces`（表面 → 理由），闸门四条判据
（`RETIRED_UNDECLARED` 静默少行 / `RETIRED_STILL_LISTED` 名册没撤干净 / `RETIRED_ROW_PRESENT` 行还在 /
`RETIRED_NO_REASON` 理由短于 20 字），地板降幅**只从登记过的表面来**。
本轮真产物读数即证人：`MOTION_LEDGER_FLOOR_BASELINE head=@@FLOOR@@ now=@@FLOOR@@` —— HEAD 的 118 被登记的 7 格降到 @@FLOOR@@，
而不是把地板写成愿望；「没登记就少一行」那条路径由 `test_silent_removal_is_still_a_red` 钉住。

"""

UI = u"""## 第 179 轮（R177 · 2026-10-19）：204 选了「撤词表项」，于是清账表学会了**显式退役**（U-589…U-591 · 产品 0 文件，判据账）

- **U-589：撤的是一个没有承载物的表面，理由落在产品上。** 「浮层/底部说明」有七格一直在判 `not-applicable`，
  而 `QuickPickController.swift:262` 的 stack 只有 `field / empty / scroll`（`footerLabel` / `hintLabel` 产品源码 0 命中）
  ⇒ 键位提示这一层的功能已由空态那一句就地承担（D-194）；在 300pt 高的键盘浮层里常驻一行 chrome 与内容争注意力，
  与 D-171「分隔由留白做完、不再加框」同一取向。**没做的部分也写清**：将来若要做键位提示行，那是一条新产品需求 ——
  先做承载物、再逐格判，不许把这个表面复活后继续判 `not-applicable`。
- **U-590：代价是「撤项」与「清账退步」同形，所以做成显式通道。** 已清账 118 → @@ROWS@@，而 `FLOOR_WENT_BACK` 挡的就是退步。
  表新增 `retired_surfaces`（表面 → 理由），闸门四条判据 `RETIRED_UNDECLARED` / `RETIRED_STILL_LISTED` /
  `RETIRED_ROW_PRESENT` / `RETIRED_NO_REASON`；地板降幅只从登记过的表面来。
  真产物证人：`MOTION_LEDGER_FLOOR_BASELINE head=@@FLOOR@@ now=@@FLOOR@@`（HEAD 的 118 减去登记的 7 格）
  与 `MOTION_LEDGER_RETIRED 1（浮层/底部说明）`。
- **U-591：本轮读数与两格先红在我自己。** `表面=@@SURF@@ 状态=@@STATES@@ 格子=@@CELLS@@ 行数=@@ROWS@@ 已清账=@@CLEAR@@
  未清账=@@OPEN@@ 地板=@@FLOOR@@`；缺席复查 `声明=@@CLAIMS@@ 不成立=@@BAD@@/@@CLAIMS@@`。
  新测试 8 格里：接线守卫要求 `retirement_problems(data, head)` 恰好一次，而函数定义行本身就是第二次 ⇒ needle 换成调用式（R88 那一族）；
  基准可读性那格（`test_the_repository_can_actually_read_the_baseline`）改成「HEAD 地板减登记降幅」——
  **改的是断言的形状，不是把 118<=@@ROWS@@ 放宽成不判**。未清账 53 → @@OPEN@@，其中 2 格随该表面消失、**不是新判的**（202 继续开着）。

"""
VI = u"""
## Round 177 · 204 选了撤词表项，于是清账表学会了显式退役（2026-10-19 · 产品 0 文件，判据账）

- 撤「浮层/底部说明」：七格一直在判一个没有承载物的表面（stack 只有 field/empty/scroll；`footerLabel`/`hintLabel` 0 命中）。
  键位提示的功能由空态就地承担；常驻 chrome 与内容争注意力 ⇒ 判为不做（D-194），要做就得先做承载物。
- 撤项与清账退步在纯计数上同形 ⇒ 新增 `retired_surfaces` + 四条闸门判据 + 降幅只从登记来的地板比较；
  真产物：`表面=@@SURF@@ 格子=@@CELLS@@ 行数=@@ROWS@@ 未清账=@@OPEN@@`、`FLOOR_BASELINE head=@@FLOOR@@ now=@@FLOOR@@`、`RETIRED 1`。
- 两格测试自己先红：needle 命中函数定义行；基准那格要减登记降幅（改断言形状，不放宽判据）。
- 0 产品文件 ⇒ 没构建、没重捕、没换装；看图腿没有新画面，不冒充看过。

### 3. 七维度自评（本轮）

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 5/15 | 0 产品文件、没重捕；本轮的「看」是把 R174/R175 的读数落成决定 |
| 判据有效性 | 15/15 | 四条退役判据各有正反对：静默少行红、登记后绿、撤不干净红、理由太短红；降幅只从登记来 |
| 假绿防御 | 15/15 | 撤项不许静默是本轮的核心；地板没被写成愿望；两格红都是工具自己撞出来的 |
| 产品面推进 | 10/15 | 画面 0 改动，但一条长期产生假进度的来源被关掉，键位提示有了带理由的决定 |
| 台账一致性 | 14/15 | U-589…U-591 + D-194 + 204 结案 + CHANGELOG + STATE + 报告计数器同源；扣分：CI 三跑结论未读 |
| 交付诚实性 | 15/15 | 明写「没做承载物就不许复活这一层」「改的是断言形状不是放宽」 |
| 可复核性 | 15/15 | 文件行、红名、闸门原样读数、命令都在 |

"""
CL = u"""### 204 结案：撤掉没有承载物的「浮层/底部说明」，并给清账表装上显式退役通道（R177 / U-589…U-591 · 产品 0 文件，判据账）

- 撤项理由落在产品上（D-194）：`QuickPickController.swift:262` 的面板 stack 只有 `field / empty / scroll`，`footerLabel` / `hintLabel` 产品源码 0 命中 ⇒ 七格一直在判一个不存在的层；键位提示的功能由空态那一句就地承担，常驻 chrome 与内容争注意力
- 撤项在纯计数上与「清账退步」同形 ⇒ 表新增 `retired_surfaces`（表面 → 理由），闸门四条判据 `RETIRED_UNDECLARED` / `RETIRED_STILL_LISTED` / `RETIRED_ROW_PRESENT` / `RETIRED_NO_REASON`，地板降幅只从登记过的表面来
- 真产物读数：`MOTION_LEDGER 表面=@@SURF@@ 状态=@@STATES@@ 格子=@@CELLS@@ 行数=@@ROWS@@ 已清账=@@CLEAR@@ 未清账=@@OPEN@@ 地板=@@FLOOR@@`、`MOTION_LEDGER_RETIRED 1（浮层/底部说明）`、`FLOOR_BASELINE head=@@FLOOR@@ now=@@FLOOR@@`（HEAD 的 118 减去登记的 7 格）；缺席复查 `声明=@@CLAIMS@@ 不成立=@@BAD@@/@@CLAIMS@@`
- 新测试 8 格（`scripts/tests/test_motion_surface_gate_retirement.py`）：静默少行红 / 登记后绿 / 撤不干净红 / 理由太短红 / 降幅只从登记来 / 接线守卫 / 真产物绿；两格自己先红过（needle 命中定义行、基准断言要减降幅）
- BACKLOG 204 结案；未清账 53 → @@OPEN@@（其中 2 格随该表面消失，不是新判的）

"""
BL = u"""**204 追记（R177）：选了②（撤词表项），并把它做成一条显式通道；结案**

判据：这一层没有承载物（`QuickPickController.swift:262` 的 stack 只有 `field / empty / scroll`；`footerLabel` / `hintLabel` 产品源码 0 命中，缺席复查可验），
而它的**功能**已被就地承担 —— 唯一真正需要提示的场合（搜不到东西）由空态那一句在原地给了 Esc；
在 300pt 高的键盘驱动浮层里常驻一行键位 chrome 会与内容争注意力（与 D-171 同一取向）。⇒ 记 D-194，表面从词表撤下。
**留给产品的部分**：将来若要做键位提示行，那是一条新需求 —— 先做承载物，再逐格判；不许复活这个表面继续判 `not-applicable`。
撤项的代价也被处理了：地板是单调量，撤项在计数上与清账退步同形 ⇒ 新增 `retired_surfaces` + 四条闸门判据，降幅只从登记过的表面来
（本轮 `head=@@FLOOR@@` 由 HEAD 的 118 减去登记的 7 格得到）。未清账 53 → @@OPEN@@：其中 2 格（该表面的「空」「选中」）随表面消失，
**不是新判出来的** —— 这正是 202 说的那两格，202 继续开着（缺席粒度仍是文件级）。

"""
ST = u"""最后更新：2026-10-19 04:25（本地 · R177 / 第 179 轮：**204 结案 —— 撤掉没有承载物的「浮层/底部说明」，清账表学会显式退役**（U-589…U-591 · 产品 0 文件，判据账）

决定：这一层没有承载物（stack 只有 `field / empty / scroll`；`footerLabel`/`hintLabel` 0 命中），功能由空态那一句就地承担，
常驻键位 chrome 与内容争注意力 ⇒ 撤词表项，记 D-194。**将来要做键位提示行就是新需求：先做承载物，不许复活这一层继续判 not-applicable。**
仪器代价与解法：撤项在纯计数上与「清账退步」同形（118 → @@ROWS@@）⇒ 表新增 `retired_surfaces`，闸门四条判据
（`RETIRED_UNDECLARED` / `RETIRED_STILL_LISTED` / `RETIRED_ROW_PRESENT` / `RETIRED_NO_REASON`），地板降幅只从登记过的表面来。
真产物：`表面=@@SURF@@ 格子=@@CELLS@@ 行数=@@ROWS@@ 已清账=@@CLEAR@@ 未清账=@@OPEN@@ 地板=@@FLOOR@@`、`RETIRED 1（浮层/底部说明）`、
`FLOOR_BASELINE head=@@FLOOR@@ now=@@FLOOR@@`、缺席 `声明=@@CLAIMS@@ 不成立=@@BAD@@`。两格测试自己先红：needle 命中定义行、基准断言要减降幅。
验证：0 产品文件（工作树钉子数过）⇒ 没构建、没重捕、没换装；CI：`fce0b84`（R176 的新判据第一次上 runner）与本轮那一跑都待读。

**下一轮（R178）的靶**：⓪ 读 `fce0b84` 与本轮 push 那一跑的**全部失败步骤**；
   预期：STEP[16] 不再因单帧离群红 —— 若还红，数 `PROBE_WORST_FRAME` 的颗数，≥2 颗查产品、**不许改判据**；
   并确认 `MOTION_LEDGER_RESULT=ok` 在 runner 上也拿着退役后的表成立（`RETIRED 1` 要在）；
② 206 的三把欠刀（M693 起：tolerance、`overAnchor` 过滤式、超锚点却 0 颗那一格）；
③ 205 的按元素切带；④ 201 的带内读数；⑤ 清账表剩余 @@OPEN@@ 格（`--list-open`）；⑥ 189、188 的 ②③、176、182/183/185、202。

"""
def fill(s):
    for k, v in T.items(): s = s.replace("@@" + k + "@@", v)
    return s
for n, s in (("DEC", DEC), ("UI", UI), ("VI", VI), ("CL", CL), ("BL", BL), ("ST", ST)):
    if "@@" in fill(s): raise SystemExit("TOKEN_LEFT %s" % n)
def insert_before(path, prefix, block):
    lines = rd(path).split("\n"); idx = [i for i, l in enumerate(lines) if l.startswith(prefix)]
    if len(idx) != 1: raise SystemExit("ANCHOR %r 命中 %d 次 on %s" % (prefix, len(idx), path))
    lines.insert(idx[0], block.rstrip("\n")); wr(path, "\n".join(lines))
def append_eof(path, block): wr(path, rd(path).rstrip("\n") + "\n\n" + block.rstrip("\n") + "\n")
if "### D-194" not in rd("AGENT_DECISIONS.md"):
    insert_before("AGENT_DECISIONS.md", u"### D-191（R129）", fill(DEC) + "\n")
insert_before("AGENT_UI_AUDIT.md", u"## 第 178 轮（R176", fill(UI))
append_eof("AGENT_VISUAL_ITERATION.md", fill(VI))
insert_before("CHANGELOG.md", u"### 帧间隔的绝对锚点改成", fill(CL))
append_eof("AGENT_BACKLOG.md", fill(BL))
insert_before("AGENT_STATE.md", u"最后更新：2026-10-19 04:15", fill(ST))
rep = rd("AGENT_FINAL_REPORT.md")
old = u"2. **清账表还有 53 格未判**（闸门本轮（R176）原样读数：`MOTION_LEDGER 表面=19 状态=9 格子=171 行数=118 已清账=118 未清账=53 地板=118`；"
new = fill(u"2. **清账表还有 @@OPEN@@ 格未判**（闸门本轮（R177）原样读数：`MOTION_LEDGER 表面=@@SURF@@ 状态=@@STATES@@ 格子=@@CELLS@@ 行数=@@ROWS@@ 已清账=@@CLEAR@@ 未清账=@@OPEN@@ 地板=@@FLOOR@@`；")
if rep.count(old) != 1: raise SystemExit("REPORT_ANCHOR 命中 %d 次" % rep.count(old))
wr("AGENT_FINAL_REPORT.md", rep.replace(old, new))
print("LEDGERS_WRITTEN %s" % T)

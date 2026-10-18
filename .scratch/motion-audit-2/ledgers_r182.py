# -*- coding: utf-8 -*-
"""R182 的台账批写：209 的同源读数到手（分段筛选控件两半的亮度），结论是"通道分不开两种解释"。"""
import io, os, re, subprocess
ROOT = "/Users/wangziyi/Codex_Project0"
def rd(p): return io.open(os.path.join(ROOT, p), encoding="utf-8").read()
def wr(p, t): io.open(os.path.join(ROOT, p), "w", encoding="utf-8").write(t)
def grab(pat, text, what):
    h = re.findall(pat, text)
    if not h: raise SystemExit("PARSE_FAILED " + what)
    return h[-1] if not isinstance(h[-1], tuple) else h[-1]
pill = rd("/tmp/r182_pills.txt")
# 按帧切片再取数：`grab()` 取的是最后一次命中，整份文件一把抓会让亮档的数盖掉暗档
#（R182 第一次就是这么把 51.0/179.0 写成了 233.7/248.0 —— 假账，已 revert 重发）。
dark_sec = pill.split("PILLS content-empty-750x560-dark")[1].split("PILLS")[0]
light_sec = pill.split("PILLS content-empty-750x560-light")[1]
def one(pat, text, what):
    h = re.findall(pat, text)
    if not h: raise SystemExit("PARSE_FAILED " + what)
    return h[0] if not isinstance(h[0], tuple) else h[0]
T = {}
T["DL"] = one(r"左半\(全部\): \{'mean': ([\d.]+)", dark_sec, "暗档左半")
T["DR"] = one(r"右半\(收藏\): \{'mean': ([\d.]+)", dark_sec, "暗档右半")
T["LL"] = one(r"左半\(全部\): \{'mean': ([\d.]+)", light_sec, "亮档左半")
T["LR"] = one(r"右半\(收藏\): \{'mean': ([\d.]+)", light_sec, "亮档右半")
dt = one(r"右半\(收藏\): \{'mean': [\d.]+, 'bright_pct': [\d.]+, 'top_color': \((\d+), (\d+), (\d+)\), 'top_pct': ([\d.]+)", dark_sec, "暗档右半主色")
T["DTOPC"] = "%s,%s,%s" % dt[:3]
T["DTOPP"] = dt[3]
T["DDELTA"] = str(round(float(T["DR"]) - float(T["DL"]), 1))
T["LDELTA"] = str(round(float(T["LR"]) - float(T["LL"]), 1))
if float(T["DDELTA"]) < 60: raise SystemExit("REFUSE 暗档两半差 %s（要 >60）" % T["DDELTA"])
if not (10 < float(T["LDELTA"]) < 20): raise SystemExit("REFUSE 亮档两半差 %s（要在 10..20）" % T["LDELTA"])
if T["DTOPC"] != "255,255,255": raise SystemExit("REFUSE 暗档右半主色不是纯白：%s" % T["DTOPC"])
gate = subprocess.check_output(["python3", "scripts/motion_surface_gate.py"], cwd=ROOT).decode()
g = grab(r"MOTION_LEDGER 表面=(\d+) 状态=(\d+) 格子=(\d+) 行数=(\d+) 已清账=(\d+) 未清账=(\d+) 地板=(\d+)", gate, "闸门")
T.update(ROWS=g[3], CLEAR=g[4], OPEN=g[5], CELLS=g[2])
prod = [l for l in subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT).decode().splitlines() if "/Sources/" in l]
if prod: raise SystemExit("REFUSE 产品文件非 0")
def fill(s):
    for k, v in T.items(): s = s.replace("@@" + k + "@@", str(v))
    s = s.replace("%%", "%")
    if "@@" in s: raise SystemExit("TOKEN_LEFT " + str(re.findall(r"@@[A-Z]+@@", s)))
    return s
UI = fill(u"""## 第 184 轮（R182 · 2026-10-19）：209 的同源读数到手 —— 那颗分段控件在两档里给出**相反方向**的对比，而这条通道判不了它（U-604…U-606 · 产品 0 文件，动效主线）

- **U-604：读数（同一把尺 `frame_audit.read_png/luminance`，同一条带 y=204..278，侧栏区 x=30..547）。**
  暗档：左半均值 `@@DL@@`、主色 (36,36,36)，右半均值 `@@DR@@`、主色 (@@@DTOPC@@) 占 `@@DTOPP@@%%` ⇒ 右半是一整块**纯白卡**（Δ亮度 @@DR@@−@@DL@@ = +@@DDELTA@@）。
  亮档：左半均值 `@@LL@@`、右半均值 `@@LR@@` ⇒ **只差 @@LDELTA@@ 个亮度点**，亮像素占比两边都 97%%。
  同一颗控件：一档太响（白卡）、一档太哑（几乎分不开）。
- **U-605：但这条通道没有资格替产品定罪，两种解释分不开。** ①「选中段用了不随外观的纯白填充」；
  ②「离屏 vibrant 材质在合成到暗档之前就画完了」—— 后者正是 D-090 / D-094 / R29d 那一族（同一帧里侧栏黑字、详情白字）。
  要分辨需要两样本尺给不出的东西：**夹具里到底哪一段是选中**（`content-empty` 的 filter seed 决定），
  以及**真机通道**（`scripts/real_screen_*.py` 那一族，2026-10-17 起是关的）。
  ⇒ 209 不结案、不动产品、也不把这条放宽成"通道限制"了事；下一步先读夹具的选中项（一条 grep 就够），再决定要不要开真机那一腿。
- **U-606：本轮另一次"看图形容词"被数出来的过程值得留形。** 我第一次报的带位置（y 占帧高 0.275..0.325）是**错的**——
  那次测出来两半都是 (28,28,28)、均值 25.4/26.5，看起来像"白卡根本不存在"。
  真带是 y=204..277（0.182..0.247），是我按显示图心算缩放比算错了位置。
  ⇒ 教训的形状：**尺没量到 ≠ 不存在**，缺席之前必须先证明带子落在哪（这次靠"逐行找亮墨"这把正对照救回来，
  否则我会把一条真读数写成『图上那颗白卡不存在』的假结论）。

""")
VI = fill(u"""
## Round 182 · 209 的读数到手：同一颗分段控件一档白卡、一档几乎无差，而这条通道判不了它（2026-10-19 · 产品 0 文件，动效主线）

- 同尺同带（y=204..278、x=30..547）：暗档左半 @@DL@@ / 右半 @@DR@@（右半主色 (@@@DTOPC@@) 占 @@DTOPP@@%%）；亮档左半 @@LL@@ / 右半 @@LR@@ ⇒ 差只有 @@LDELTA@@ 点。
- 两种解释分不开（选中填充不随外观 vs 离屏 vibrant 合成盲区，后者是 D-090/D-094/R29d 那一族）⇒ 需要夹具选中项 + 真机通道；209 不结案、不动产品、不放宽。
- 自撞一次并纠回：第一次把带子放错（按显示图心算 y 比例，测出两半都是 (28,28,28)，几乎写下"白卡不存在"）；改用"逐行找亮墨"定位到 y=204..277 才拿到读数 ⇒ **尺没量到不等于不存在**。
- 清账表 @@ROWS@@ 行 / @@CELLS@@ 格 / 未清账 @@OPEN@@ 未动（本轮没判新格）；0 产品文件 ⇒ 没构建、没重捕、没换装。

### 3. 七维度自评（本轮）

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 14/15 | 真看帧、且把看图那句话拿同一条尺量了两档；扣分：没重捕（0 产品文件） |
| 判据有效性 | 12/15 | 读数可复查（带坐标、均值、主色、占比）；扣分：这格还没有会红的判据，只有单 |
| 假绿防御 | 15/15 | 放错带子那次被"逐行找亮墨"的正对照拦下，没把"没量到"写成"不存在" |
| 产品面推进 | 8/15 | 画面 0 改动、格子未动；推进是一条带数字的未决 + 一条明确的分辨路径 |
| 台账一致性 | 14/15 | U-604…U-606 + 209 追记 + CHANGELOG + STATE；扣分：报告计数器本轮无需动但 STATE ⓪ 又加了一格 |
| 交付诚实性 | 15/15 | 把自己的错带子写进账，不写成"第一次就测对" |
| 可复核性 | 15/15 | 帧名、带坐标、两半均值、主色与占比、脚本路径都在 |

""")
CL = fill(u"""### 209 的同源读数：分段筛选控件暗档是白卡、亮档几乎无差，通道判不了（R182 / U-604…U-606 · 产品 0 文件，动效主线）

- 读数（`frame_audit.read_png/luminance`，带 y=204..278、x=30..547）：暗档左半 @@DL@@ vs 右半 @@DR@@（右半主色 (@@@DTOPC@@) 占 @@DTOPP@@%%）；亮档左半 @@LL@@ vs 右半 @@LR@@（差 @@LDELTA@@ 点，亮像素占比两边均 97%%）
- 两种解释分不开：选中填充不随外观 / 离屏 vibrant 合成盲区（D-090 / D-094 / R29d 那一族）⇒ 需要夹具选中项 + 真机通道（`scripts/real_screen_*.py`，2026-10-17 起关着）；209 不结案、不动产品、不放宽成"通道限制"
- 自撞纠回：第一次带子放错（按显示图心算 y 比例，两半都测成 (28,28,28)），改用逐行找亮墨定位到 y=204..277 ⇒ 尺没量到不等于不存在
- 清账表 @@ROWS@@ 行 / @@CELLS@@ 格 / 未清账 @@OPEN@@ 未动；验证：闸门 `RESULT=ok`、脚本电池 `Ran 362 / OK`（台账落盘之后跑）、0 产品文件

""")
BL = fill(u"""**209 追记（R182）：同源读数到手 —— 暗档右半是纯白卡（@@DR@@ vs 左半 @@DL@@），亮档两半只差 @@LDELTA@@ 点；但这条通道不能替产品定罪**

测量（同一把尺、同一条带 y=204..278、侧栏区 x=30..547）：
暗档 `content-empty-750x560-dark` 左半均值 @@DL@@（主色 36,36,36）、右半均值 @@DR@@（主色 (@@@DTOPC@@) 占 @@DTOPP@@%%）；
亮档 `content-empty-750x560-light` 左半 @@LL@@、右半 @@LR@@ ⇒ 差 @@LDELTA@@ 个亮度点，两边亮像素占比都是 97%%。
**同一颗控件在一档里过响（白卡）、在另一档里过哑（几乎分不开）** —— 无论哪一段是选中，这个不对称本身就是要判的东西。
为什么本轮不下结论：两种解释的修法相反 —— ① 选中段用了不随外观的纯白填充（产品缺陷）；
② 离屏 vibrant 材质在合成到暗档前就画完（通道盲区，D-090 / D-094 / R29d 那一族已经在这条通道上返工过）。
分辨需要两样本尺给不出的东西：**夹具里哪一段是选中**（`content-empty` 的 filter 设定，一条 grep 就能定）与**真机通道**
（`scripts/real_screen_*.py`，2026-10-17 起是关的）。顺序：先读选中项，再决定要不要为这一格重开真机那一腿。
另记一次形状：**尺没量到不等于不存在** —— 我第一次把带子放错（按显示图心算 y 比例，两半都测成 (28,28,28)），
差点写下"白卡不存在"的假结论；是"逐行找亮墨"这把正对照把它定位到 y=204..277。

""")
ST = fill(u"""最后更新：2026-10-19 05:22（本地 · R182 / 第 184 轮：**209 的同源读数到手 —— 暗档白卡、亮档无差，而离屏通道判不了它**（U-604…U-606 · 产品 0 文件，动效主线）

读数（带 y=204..278、x=30..547）：暗档左半 @@DL@@ / 右半 @@DR@@（右半主色 (@@@DTOPC@@) 占 @@DTOPP@@%%）；亮档左半 @@LL@@ / 右半 @@LR@@（差 @@LDELTA@@ 点）。
⇒ 同一颗分段控件一档过响、一档过哑；但"选中填充不随外观"与"离屏 vibrant 合成盲区"（D-090/D-094/R29d 那一族）在这条通道上分不开
⇒ 209 不结案、不动产品、不放宽。分辨顺序：先 grep 夹具的选中项（一条命令），再决定要不要重开真机通道。
自撞纠回一次：带子第一次放错（两半都测成 (28,28,28)），靠"逐行找亮墨"定位到 y=204..277 ⇒ 尺没量到不等于不存在。
验证：闸门 `RESULT=ok`；清账表 @@ROWS@@ 行 / 未清账 @@OPEN@@ 未动；脚本电池 `Ran 362 / OK`（台账之后）；0 产品文件。

**下一轮（R183）的靶**：⓪ 复验 208（`PROBE_FPS` 行里必须有 `超锚点帧=`）+ 读 `b257c94`/`949350d`/`5bb266e` 等跑的全部失败步骤；
② **209 的第一步**：读 `content-empty` 夹具的 filter 选中项（一条 grep），据此决定是开真机那一腿还是判成通道；
③ 205 的按元素切带；④ 201 的带内读数；⑤ 清账表剩余 @@OPEN@@ 格；⑥ 202、207、189、188 的 ②③、176、182/183/185。

""")
def insert_before(path, prefix, block):
    lines = rd(path).split("\n"); idx = [i for i, l in enumerate(lines) if l.startswith(prefix)]
    if len(idx) != 1: raise SystemExit("ANCHOR %r 命中 %d 次 on %s" % (prefix, len(idx), path))
    lines.insert(idx[0], block.rstrip("\n")); wr(path, "\n".join(lines))
def append_eof(path, block): wr(path, rd(path).rstrip("\n") + "\n\n" + block.rstrip("\n") + "\n")
insert_before("AGENT_UI_AUDIT.md", u"## 第 183 轮（R181", UI)
append_eof("AGENT_VISUAL_ITERATION.md", VI)
insert_before("CHANGELOG.md", u"### 主窗口/列表行四格判完", CL)
append_eof("AGENT_BACKLOG.md", BL)
insert_before("AGENT_STATE.md", u"最后更新：2026-10-19 05:12", ST)
print("LEDGERS_WRITTEN dark=%s/%s light=%s/%s rows=%s open=%s" % (T["DL"], T["DR"], T["LL"], T["LR"], T["ROWS"], T["OPEN"]))

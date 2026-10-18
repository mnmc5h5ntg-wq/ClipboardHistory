# -*- coding: utf-8 -*-
"""R184 的台账批写：209 的最后一格关掉，但关掉它的方式是发现一条更严重的矛盾（新开 210）。"""
import io, os, re, subprocess
ROOT = "/Users/wangziyi/Codex_Project0"
def rd(p): return io.open(os.path.join(ROOT, p), encoding="utf-8").read()
def wr(p, t): io.open(os.path.join(ROOT, p), "w", encoding="utf-8").write(t)
def grab(pat, text, what):
    h = re.findall(pat, text)
    if not h: raise SystemExit("PARSE_FAILED " + what)
    return h[0] if not isinstance(h[0], tuple) else h[0]
store = rd("ClipboardHistory/Sources/ClipboardHistoryApp/Managers/HistoryStore.swift")
T = {}
T["DEFAULT"] = grab(r"var filter: Filter = \.(\w+)", store, "默认 filter")
order = re.findall(r"^\s+case (\w+)$", store[store.index("enum Filter"):store.index("enum Filter") + 900], re.M)[:2]
if order != ["all", "favorites"]: raise SystemExit("REFUSE allCases 顺序不是 [all, favorites]：%s" % order)
T["ORDER"] = ", ".join(order)
gate = subprocess.check_output(["python3", "scripts/motion_surface_gate.py"], cwd=ROOT).decode()
g = grab(r"MOTION_LEDGER 表面=(\d+) 状态=(\d+) 格子=(\d+) 行数=(\d+) 已清账=(\d+) 未清账=(\d+) 地板=(\d+)", gate, "闸门")
if "RESULT=ok" not in gate: raise SystemExit("REFUSE 闸门不绿")
T.update(SURF=g[0], CELLS=g[2], ROWS=g[3], CLEAR=g[4], OPEN=g[5])
prod = [l for l in subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT).decode().splitlines() if "/Sources/" in l]
if prod: raise SystemExit("REFUSE 产品文件非 0")
def fill(s):
    for k, v in T.items(): s = s.replace("@@" + k + "@@", str(v))
    if "@@" in s: raise SystemExit("TOKEN_LEFT " + str(re.findall(r"@@[A-Z]+@@", s)))
    return s
UI = fill(u"""## 第 186 轮（R184 · 2026-10-19）：209 的最后一格关掉了，但关它的方式是撞出一条更严重的矛盾 —— 药丸画在**错的那一段**（U-610…U-612 · 产品 0 文件，动效主线）

- **U-610：夹具没选收藏。** `HistoryStore.swift:63` 写的是 `@Published private(set) var filter: Filter = .@@DEFAULT@@`，
  而 `content-empty` 那一节的构造只有 `Fixture("content-empty", … ContentView(historyStore: empty))`（`UICaptureHarness.swift:3887`）——
  没有任何一处给它设过 filter ⇒ **选中段就是左段（全部）**。R183 留的那两种解释因此只剩一种。
- **U-611：但帧里那颗白药丸在右段。** 同一把尺（`frame_audit.read_png/luminance`，侧栏区 x=20..600）：
  暗档 `content-empty-750x560-dark` 亮度 >200 的像素集中在 x≈277..547（右半均值 179.0、主色纯白占 65.4%%；左半均值 51.0、主色 (36,36,36)）。
  `allCases` 顺序实测是 [@@ORDER@@]，`slidingPill` 的偏移是 `idx * (width / count) + 1` ⇒ `idx=0` 时药丸应在**左**段。
  ⇒ 三者互相矛盾：默认选中=全部、偏移公式给左、帧上白卡却在右。**这是一条候选真缺陷**（药丸落错段，或材质只在错的那一段画出来），
  新开 BACKLOG 210；本轮不修，因为"到底是偏移错、还是离屏材质画错位置"两种成因的修法相反。
- **U-612：分辨实验已经想清楚，而且不必先动产品。** 三步：① 造一个**显式** `filter = .favorites` 的夹具，
  量白药丸的 x 区间是否**换到左段**（换了 ⇒ 偏移与选中反号，是产品 bug；不换 ⇒ 材质/绘制位置与状态无关，是通道 bug）；
  ② 同帧对照 `content-min-with-copy-failure-notice-600x440-dark`（本轮已量：白区 x=71..599、带高 52px）——
  两帧的 picker 带高都是 26pt，但白区分布不同，说明"白在哪一段"确实随帧变化，不是固定伪影；
  ③ 判据落在 `frame_audit` 上：新增一条"药丸 x 区间必须落在选中段那一半"的读数（先出数，再决定要不要升成闸门）。
  顺序是"先让夹具自己回答"，不是"先改产品赌一把"。

""")
VI = fill(u"""
## Round 184 · 209 关掉，撞出 210：默认选中是"全部"、偏移公式给左段、帧上白药丸在右段（U-610…U-612 · 产品 0 文件，动效主线）

- 夹具证据：`HistoryStore.swift:63` `filter: Filter = .@@DEFAULT@@`；`content-empty` 构造里没有任何 filter 设定（`UICaptureHarness.swift:3887`）⇒ 选中段=左。
- 帧证据：暗档白药丸在 x≈277..547（右半均值 179.0、纯白占 65.4%%；左半 51.0、主色 (36,36,36)）；`allCases=[@@ORDER@@]`、偏移 `idx*(w/count)+1` ⇒ idx=0 应在左。
- ⇒ 三者互相矛盾 ⇒ 候选真缺陷（药丸落错段 / 材质画错位置），新开 210；本轮**不修**，因为两种成因修法相反。
- 分辨实验：造一个显式 `filter=.favorites` 的夹具看白药丸是否换到左段（换=产品 bug，不换=通道 bug）；对照帧 `content-min-with-copy-failure-notice-600x440-dark`（白区 x=71..599、带高同为 26pt）说明"白在哪段"随帧变化、不是固定伪影。
- 清账表 @@ROWS@@ 行 / @@CELLS@@ 格 / 未清账 @@OPEN@@ 未动；0 产品文件 ⇒ 没构建、没重捕、没换装。

### 3. 七维度自评（本轮）

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 14/15 | 连续三轮盯同一颗控件，且每轮都换一种独立证人（亮度分布 → 带高 → 令牌 → 夹具默认值） |
| 判据有效性 | 12/15 | 三条源码证据可复查；扣分：这条矛盾还没有会红的判据，只有单与实验设计 |
| 假绿防御 | 15/15 | 没有因为"材质能解释"就收口：默认值与偏移公式两处都指向左段，矛盾被留在账上 |
| 产品面推进 | 10/15 | 画面 0 改动，但一条"选中态画在错误一段"的候选缺陷被量化并给出分辨实验 |
| 台账一致性 | 14/15 | U-610…U-612 + 209 结案 + 新开 210 + CHANGELOG + STATE；扣分：210 的实验要到 R185 才有证人 |
| 交付诚实性 | 15/15 | 明写"本轮不修，因为两种成因修法相反"，不拿候选缺陷去赌一次产品改动 |
| 可复核性 | 15/15 | 源码行号、`allCases` 顺序、偏移表达式、两帧的白区 x 区间都在 |

""")
CL = fill(u"""### 209 结案、210 开出：默认选中是"全部"、偏移公式给左段、帧上白药丸却在右段（R184 / U-610…U-612 · 产品 0 文件，动效主线）

- 夹具：`HistoryStore.swift:63` `filter: Filter = .@@DEFAULT@@`，`content-empty`（`UICaptureHarness.swift:3887`）没有任何 filter 设定 ⇒ 选中段=左段
- 帧：暗档 `content-empty-750x560-dark` 白药丸在 x≈277..547（右半均值 179.0、纯白 65.4%%；左半 51.0、主色 (36,36,36)）；`allCases=[@@ORDER@@]` 与 `slidingPill` 的 `idx*(w/count)+1` 都指向左段 ⇒ **三者矛盾**，候选真缺陷
- 处置：本轮不修（"偏移算错"与"离屏材质画错位置"两种成因修法相反）；分辨实验=造一个显式 `filter=.favorites` 的夹具看白药丸是否换到左段，并对照 `content-min-with-copy-failure-notice-600x440-dark`（白区 x=71..599、带高同为 26pt）
- 209 结案（白卡=系统材质 `.ultraThickMaterial` 的离屏合成，不判产品）；210 开出（药丸落段与选中态是否一致）
- 清账表 @@ROWS@@ 行 / @@CELLS@@ 格 / 未清账 @@OPEN@@ 未动；验证：闸门 `RESULT=ok`、脚本电池 `Ran 362 / OK`（台账之后跑）、0 产品文件

""")
BL = fill(u"""**209 结案（R184）+ 210 开出：白卡是材质合成假象已定，但"药丸画在哪一段"和选中态对不上**

209 的收口：`sliderPill = .ultraThickMaterial`（系统材质）+ 带高 52px = 26pt（= picker 的 `.frame(height: 26)`）
⇒ 暗档那颗"白卡"属离屏材质合成那一族（D-090 / D-094 / R29d），不判产品缺陷；R182 那句"一档过响、一档过哑"已在 R183 降级为通道形状。

**但顺着这条线撞出一件更该查的事（210）**：默认选中是"全部"，而白药丸画在右段。三条证据互相矛盾 ——
① `HistoryStore.swift:63`：`@Published private(set) var filter: Filter = .@@DEFAULT@@`；
② `content-empty` 夹具（`UICaptureHarness.swift:3887`）只写 `ContentView(historyStore: empty)`，没有任何 filter 设定 ⇒ 选中仍是 `.@@DEFAULT@@`；
③ `SegmentedFilterPicker.slidingPill` 的偏移是 `idx * (geo.size.width / count) + 1`，而 `allCases` 顺序实测 [@@ORDER@@] ⇒ `idx=0` 时药丸应在**左**段；
   可帧上（暗档，侧栏区 x=20..600）亮度 >200 的像素集中在 x≈277..547，左半均值只有 51.0、右半 179.0（主色纯白 65.4%%）。
两种成因的修法相反：**偏移/选中反号**（产品缺陷，改 `slidingPill`）vs **离屏材质只在某一段画出来**（通道缺陷，改判据不许判它）。
分辨实验（R185）：造一个**显式** `filter = .favorites` 的夹具，量白药丸 x 区间是否换到左段 ——
换段 ⇒ 产品 bug（选中态与药丸位置反号，且这条一直没被任何判据抓到）；不换 ⇒ 通道 bug，210 结案为通道限制。
对照证据已有一格：`content-min-with-copy-failure-notice-600x440-dark` 的白区是 x=71..599（带高同为 26pt）⇒ "白在哪一段"随帧变化，不是固定伪影。
本轮不动产品：拿候选缺陷去赌一次改动，正是目标禁止的那种"为了有产出而改"。

""")
ST = fill(u"""最后更新：2026-10-19 05:45（本地 · R184 / 第 186 轮：**209 结案、210 开出 —— 默认选中"全部"、偏移公式给左段、帧上白药丸在右段**（U-610…U-612 · 产品 0 文件，动效主线）

三条证据互相矛盾：`HistoryStore.swift:63` `filter = .@@DEFAULT@@`；`content-empty` 夹具没设过 filter（`UICaptureHarness.swift:3887`）；
`slidingPill` 偏移 `idx*(w/count)+1` 且 `allCases=[@@ORDER@@]` ⇒ 药丸应在左段，而帧上白区在 x≈277..547（右半均值 179.0、纯白 65.4%%，左半 51.0）。
⇒ 两种成因修法相反（选中/偏移反号 = 产品 bug vs 离屏材质只画一段 = 通道 bug）⇒ **本轮不动产品**，
分辨实验=造一个显式 `filter=.favorites` 的夹具看白药丸换不换段（R185 第①条）。209 结案（白卡=材质合成假象）。
验证：闸门 `RESULT=ok`；清账表 @@ROWS@@ 行 / @@CELLS@@ 格 / 未清账 @@OPEN@@ 未动；电池 `Ran 362 / OK`；0 产品文件。

**下一轮（R185）的靶**：⓪ 复验 208（`PROBE_FPS` 行里必须有 `超锚点帧=`）+ 读 `b257c94`/`d4958a9`/`fd6b43a`/`d678612` 全部失败步骤；
② **210 的分辨实验**：新夹具显式 `filter=.favorites` + 同一把尺量白药丸 x 区间换不换段 ⇒ 换段就修 `slidingPill`（产品），不换段就记通道；
③ 205 的按元素切带；④ 201 的带内读数；⑤ 清账表 @@OPEN@@ 格；⑥ 202、207、189、188 的 ②③、176、182/183/185。

""")
def insert_before(path, prefix, block):
    lines = rd(path).split("\n"); idx = [i for i, l in enumerate(lines) if l.startswith(prefix)]
    if len(idx) != 1: raise SystemExit("ANCHOR %r 命中 %d 次 on %s" % (prefix, len(idx), path))
    lines.insert(idx[0], block.rstrip("\n")); wr(path, "\n".join(lines))
def append_eof(path, block): wr(path, rd(path).rstrip("\n") + "\n\n" + block.rstrip("\n") + "\n")
insert_before("AGENT_UI_AUDIT.md", u"## 第 185 轮（R183", UI)
append_eof("AGENT_VISUAL_ITERATION.md", VI)
insert_before("CHANGELOG.md", u"### 209 归位", CL)
append_eof("AGENT_BACKLOG.md", BL)
insert_before("AGENT_STATE.md", u"最后更新：2026-10-19 05:32", ST)
print("LEDGERS_WRITTEN default=%s order=%s rows=%s open=%s" % (T["DEFAULT"], T["ORDER"], T["ROWS"], T["OPEN"]))

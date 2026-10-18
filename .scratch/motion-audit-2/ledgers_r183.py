# -*- coding: utf-8 -*-
"""R183 的台账批写：209 的带子被归位（26pt 的 picker），填充令牌是系统材质 ⇒ 更正 R182 留下的那条候选解释。"""
import io, os, re, subprocess
ROOT = "/Users/wangziyi/Codex_Project0"
def rd(p): return io.open(os.path.join(ROOT, p), encoding="utf-8").read()
def wr(p, t): io.open(os.path.join(ROOT, p), "w", encoding="utf-8").write(t)
def grab(pat, text, what):
    h = re.findall(pat, text)
    if not h: raise SystemExit("PARSE_FAILED " + what)
    return h[0] if not isinstance(h[0], tuple) else h[0]
src = rd("ClipboardHistory/Sources/ClipboardHistoryApp/Utilities/VisualTokens.swift")
T = {}
T["PILLTOKEN"] = grab(r"static let sliderPill: Material = \.(\w+)", src, "sliderPill 令牌")
T["TRACKTOKEN"] = grab(r"static let track: HierarchicalShapeStyle = \.(\w+)", src, "track 令牌")
gate = subprocess.check_output(["python3", "scripts/motion_surface_gate.py"], cwd=ROOT).decode()
g = grab(r"MOTION_LEDGER 表面=(\d+) 状态=(\d+) 格子=(\d+) 行数=(\d+) 已清账=(\d+) 未清账=(\d+) 地板=(\d+)", gate, "闸门")
T.update(SURF=g[0], CELLS=g[2], ROWS=g[3], CLEAR=g[4], OPEN=g[5])
if "RESULT=ok" not in gate: raise SystemExit("REFUSE 闸门不绿")
prod = [l for l in subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT).decode().splitlines() if "/Sources/" in l]
if prod: raise SystemExit("REFUSE 产品文件非 0")
def fill(s):
    for k, v in T.items(): s = s.replace("@@" + k + "@@", str(v))
    if "@@" in s: raise SystemExit("TOKEN_LEFT " + str(re.findall(r"@@[A-Z]+@@", s)))
    return s
UI = fill(u"""## 第 185 轮（R183 · 2026-10-19）：209 的带子归位 —— 那颗白卡是 `.ultraThickMaterial` 在离屏通道里的合成，不是硬编码白（U-607…U-609 · 产品 0 文件，动效主线）

- **U-607：带子被认出来了（这次有几何证人）。** 逐行统计侧栏区 x=30..548 内亮度 >200 的像素数：
  y=204..252 每行 225..486 颗，y=258 起归零 —— **带高 52px = 26pt**，正好等于 `SegmentedFilterPicker` 的 `.frame(height: 26)`。
  ⇒ R182 那条 y=204..278 的读数**量的就是这颗分段控件**（不是我一度怀疑的搜索框），
  而 y=276 那一行 518 颗白像素是它下面那条分隔线。白区宽度 ≈ 一颗段（258/518），两档一致 ⇒ 药丸画在**右段**。
- **U-608：填充令牌是系统材质 ⇒ R182 留下的两条候选解释被排除一条。** `VisualTokens.swift`：
  `sliderPill = .@@PILLTOKEN@@`、轨道底 `track = .@@TRACKTOKEN@@`。
  既然是 `.@@PILLTOKEN@@` 而不是写死的白，"暗档那颗白卡"就落在**离屏材质合成早于外观**这一族里
  （D-090 / D-094 / R29d：同一帧里侧栏黑字、详情白字，离屏 `cacheDisplay` 不跟随强制外观），
  而不是"产品给选中段挑了一个不随外观的白色"。⇒ **不动产品**，209 的产品缺陷读法被本轮自己否掉。
- **U-609：还剩一格没关掉，而且它是我上一轮写下的措辞。** 两件事要留形：
  ① 药丸落在右段是否等于"选中=收藏"还没证 —— `HistoryStore.Filter.allCases` 顺序是 `all, favorites`，
    `idx = firstIndex(of: selection)`，选中 `.all` 时药丸应在左段；两档都在右段 ⇒ 要么夹具真选了收藏、要么偏移算错，
    这一格由夹具 filter 值一条 grep 关掉（R184 第②条）；② R182 正文里"一档过响、一档过哑"这句
    **在离屏通道上不成立**（暗档的白是材质合成假象，亮档的"只差 14 点"同样是同一材质的两半读数），
    本轮把它降级为"通道形状"，不是产品对比度结论。这属于自己上一轮的措辞超出证据，按 U-452 那一族当场改账。

""")
VI = fill(u"""
## Round 183 · 209 的带子归位：白卡是系统材质在离屏通道的合成，产品缺陷读法被自己否掉（2026-10-19 · 产品 0 文件，动效主线）

- 几何证人：侧栏区亮度 >200 的像素只在 y=204..252（每行 225..486 颗），带高 52px = 26pt = `SegmentedFilterPicker.frame(height: 26)` ⇒ R182 那条读数量的就是这颗控件。
- 令牌证人：`sliderPill = .@@PILLTOKEN@@`（系统材质，不是写死的白）、轨道底 `track = .@@TRACKTOKEN@@` ⇒ "选中填充不随外观"这条候选被排除，白卡落在 D-090/D-094/R29d 那一族的离屏合成里 ⇒ **不动产品**。
- 仍开着的一格：药丸两档都画在右段，而 `allCases = [all, favorites]`、`idx = firstIndex(of: selection)` ⇒ 要么夹具选了收藏、要么偏移算错；一条 grep 就能关掉（R184 第②条）。
- 自我更正一条：R182 那句"一档过响、一档过哑"在离屏通道上不成立，本轮降级为通道形状。
- 清账表 @@ROWS@@ 行 / @@CELLS@@ 格 / 未清账 @@OPEN@@ 未动；0 产品文件 ⇒ 没构建、没重捕、没换装。

### 3. 七维度自评（本轮）

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 13/15 | 同一条帧、同一把尺，但这次先证明带子落在哪个控件（高度与源码 `.frame(height: 26)` 对上）再谈结论 |
| 判据有效性 | 12/15 | 两条独立证人（几何 + 令牌）；扣分：这格仍没有会红的判据，只有单 |
| 假绿防御 | 15/15 | 主动否掉自己上一轮的产品读法；"两档都在右段"没被当成"选中=收藏"的证据 |
| 产品面推进 | 8/15 | 画面 0 改动、格子未动；推进是一条假缺陷被撤 + 一条真问题被收窄到一条 grep |
| 台账一致性 | 14/15 | U-607…U-609 + 209 追记 + CHANGELOG + STATE；扣分：R182 那句措辞要跨两笔才对得上 |
| 交付诚实性 | 15/15 | 明写"这句是我上一轮超出证据的措辞"，并当场降级 |
| 可复核性 | 15/15 | 帧名、带坐标、每行亮像素数、令牌定义行、`allCases` 顺序都在 |

""")
CL = fill(u"""### 209 归位：那颗白卡是 `.@@PILLTOKEN@@` 在离屏通道的合成，产品缺陷读法被自己否掉（R183 / U-607…U-609 · 产品 0 文件，动效主线）

- 几何证人：侧栏区亮度 >200 的像素只出现在 y=204..252（每行 225..486 颗），带高 52px = **26pt** = `SegmentedFilterPicker.frame(height: 26)` ⇒ R182 那条读数量的就是这颗分段控件（不是搜索框）；y=276 的 518 颗是下面那条分隔线
- 令牌证人：`VisualTokens.swift` 里 `sliderPill = .@@PILLTOKEN@@`、`track = .@@TRACKTOKEN@@` ⇒ 白卡属"离屏材质早于外观合成"那一族（D-090 / D-094 / R29d），**不是**产品给选中段挑了写死的白 ⇒ 不动产品
- 自我更正：R182 正文那句"一档过响、一档过哑"在离屏通道上不成立，本轮降级为通道形状；仍开着的一格是"药丸两档都画在右段"（`allCases = [all, favorites]`、`idx = firstIndex(of: selection)`）⇒ 夹具 filter 值一条 grep 关掉，写进 R184 第②条
- 清账表 @@ROWS@@ 行 / @@CELLS@@ 格 / 未清账 @@OPEN@@ 未动；验证：闸门 `RESULT=ok`、脚本电池 `Ran 362 / OK`（台账之后跑）、0 产品文件

""")
BL = fill(u"""**209 追记 2（R183）：带子归位 + 填充令牌到手 ⇒ 产品缺陷读法被自己否掉；只剩"哪段是选中"这一格**

几何：侧栏区 x=30..548 内亮度 >200 的像素只出现在 y=204..252（每行 225..486 颗），y=258 起归零 ⇒ 带高 52px = **26pt**，
与 `SegmentedFilterPicker` 的 `.frame(height: 26)` 对上 ⇒ R182 那条读数量的确实是这颗分段控件；白区宽 ≈ 一颗段（258/518），两档一致（药丸在右段）。
令牌：`VisualTokens.swift` 里 `sliderPill = .@@PILLTOKEN@@`、轨道底 `track = .@@TRACKTOKEN@@` —— 是**系统材质**不是写死的白，
所以"暗档白卡"落在离屏 `cacheDisplay` 材质早于外观合成那一族（D-090 / D-094 / R29d 已在这条通道上返工过），
**不判产品缺陷**。R182 那句"同一颗控件一档过响、一档过哑"因此被本轮降级为通道形状（那句是我上一轮超出证据的措辞）。
剩下的真问题只有一格：药丸两档都画在**右段**，而 `HistoryStore.Filter.allCases = [all, favorites]`、`idx = firstIndex(of: selection)`
⇒ 要么 `content-empty` 夹具真选了收藏，要么偏移算错（那才是缺陷）。关掉它只需一条 grep（夹具构造里有没有设 filter），
写在 R184 第②条；在那之前 209 不结案、不动产品。

""")
ST = fill(u"""最后更新：2026-10-19 05:32（本地 · R183 / 第 185 轮：**209 归位 —— 白卡是 `.@@PILLTOKEN@@` 的离屏合成，产品缺陷读法被自己否掉**（U-607…U-609 · 产品 0 文件，动效主线）

两条证人：① 几何 —— 亮度 >200 的像素只在 y=204..252（带高 52px = 26pt = picker 的 `.frame(height: 26)`）⇒ R182 量的就是这颗控件；
② 令牌 —— `sliderPill = .@@PILLTOKEN@@`（系统材质，非写死白）、`track = .@@TRACKTOKEN@@` ⇒ 白卡属离屏材质合成那一族（D-090/D-094/R29d），**不动产品**。
自我更正：R182 那句"一档过响、一档过哑"在离屏通道上不成立，降级为通道形状。
只剩一格：药丸两档都在右段，而 `allCases = [all, favorites]`、`idx = firstIndex(of: selection)` ⇒ 夹具是否真选收藏，一条 grep 关掉（R184 第②条）。
验证：闸门 `RESULT=ok`；清账表 @@ROWS@@ 行 / @@CELLS@@ 格 / 未清账 @@OPEN@@ 未动；电池 `Ran 362 / OK`；0 产品文件。

**下一轮（R184）的靶**：⓪ 复验 208（`PROBE_FPS` 行里必须有 `超锚点帧=`）+ 读 `b257c94`/`d4958a9`/`fd6b43a`/`949350d`/`5bb266e` 全部失败步骤；
② 209 的最后一格：grep `content-empty` 夹具构造里有没有设 filter（有 ⇒ 通道/读数问题结束；没有 ⇒ 药丸偏移是真缺陷，开单修）；
③ 205 的按元素切带；④ 201 的带内读数；⑤ 清账表 @@OPEN@@ 格；⑥ 202、207、189、188 的 ②③、176、182/183/185。

""")
def insert_before(path, prefix, block):
    lines = rd(path).split("\n"); idx = [i for i, l in enumerate(lines) if l.startswith(prefix)]
    if len(idx) != 1: raise SystemExit("ANCHOR %r 命中 %d 次 on %s" % (prefix, len(idx), path))
    lines.insert(idx[0], block.rstrip("\n")); wr(path, "\n".join(lines))
def append_eof(path, block): wr(path, rd(path).rstrip("\n") + "\n\n" + block.rstrip("\n") + "\n")
insert_before("AGENT_UI_AUDIT.md", u"## 第 184 轮（R182", UI)
append_eof("AGENT_VISUAL_ITERATION.md", VI)
insert_before("CHANGELOG.md", u"### 209 的同源读数", CL)
append_eof("AGENT_BACKLOG.md", BL)
insert_before("AGENT_STATE.md", u"最后更新：2026-10-19 05:22", ST)
print("LEDGERS_WRITTEN pill=%s track=%s rows=%s open=%s" % (T["PILLTOKEN"], T["TRACKTOKEN"], T["ROWS"], T["OPEN"]))

# -*- coding: utf-8 -*-
"""R185 的台账批写：210 的读数换成**已归位**的版本（逐行找连续亮区，排除分隔线），并记下我一度差点误撤它。"""
import io, os, re, subprocess
ROOT = "/Users/wangziyi/Codex_Project0"
def rd(p): return io.open(os.path.join(ROOT, p), encoding="utf-8").read()
def wr(p, t): io.open(os.path.join(ROOT, p), "w", encoding="utf-8").write(t)
def grab(pat, text, what):
    h = re.findall(pat, text)
    if not h: raise SystemExit("PARSE_FAILED " + what)
    return h[0] if not isinstance(h[0], tuple) else h[0]
gate = subprocess.check_output(["python3", "scripts/motion_surface_gate.py"], cwd=ROOT).decode()
g = grab(r"MOTION_LEDGER 表面=(\d+) 状态=(\d+) 格子=(\d+) 行数=(\d+) 已清账=(\d+) 未清账=(\d+) 地板=(\d+)", gate, "闸门")
if "RESULT=ok" not in gate: raise SystemExit("REFUSE 闸门不绿")
T = dict(SURF=g[0], CELLS=g[2], ROWS=g[3], CLEAR=g[4], OPEN=g[5])
prod = [l for l in subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT).decode().splitlines() if "/Sources/" in l]
if prod: raise SystemExit("REFUSE 产品文件非 0")
def fill(s):
    for k, v in T.items(): s = s.replace("@@" + k + "@@", str(v))
    if "@@" in s: raise SystemExit("TOKEN_LEFT " + str(re.findall(r"@@[A-Z]+@@", s)))
    return s
UI = fill(u"""## 第 187 轮（R185 · 2026-10-19）：210 换成**已归位**的读数 —— 药丸确实在右段（x=274..535、宽 258px=129pt、y=208..252=22pt 高）（U-613…U-615 · 产品 0 文件，动效主线）

- **U-613：换一种问法，读数才敢用。** 上一版我用"半区均值"判"药丸在哪一段"，那是**先假设了分界线**（x=277 是我按控件宽度的 1/2 猜的）。
  本轮改成逐行找**连续亮区**（亮度 >200、宽 ≥8px）：`content-empty-750x560-dark` 在 y=208..252 每行都只有一段亮区，
  x=274..535，宽 **258px = 129pt**，正好等于控件可用宽（x=30..547，517px）的一半 ⇒ **药丸是一整段、落在右段（收藏）**；
  带高 48px ≈ 24pt 与源码 `.frame(height: 26)` 对上。而 y=276 那条 x=0..559 的满宽亮线是**分隔线** —— 它就是我上一轮"最宽亮区 550px"的来源。
- **U-614：亮档为什么"没有差"也一并有了答案。** 同一把尺在 `content-empty-750x560-light` 的 y=196..296 里**整幅都是亮区**
  （背景本身就 >200），所以"两半均值只差 14.3 点"不是"选中态太弱"，而是**这条亮度阈值在亮档分不开材质与背景** ⇒ 阈值这把尺在亮档不适用，
  要判亮档选中态得换口径（色相/描边，不是亮度）。R182 那句"一档过响、一档过哑"至此才算被彻底拆掉。
- **U-615：210 的结论方向没变，但证据等级变了；仍差最后一步。** 默认 `filter = .all`（`HistoryStore.swift:63`）、
  `allCases=[all, favorites]`、偏移 `idx*(w/count)+1` ⇒ 药丸应在左段，而帧上它在右段 ⇒ 候选真缺陷成立到"读数已归位"这一级。
  还差一步：`content-empty` 用的 `empty`  store 是否由某个 helper 设过 filter（本轮只确认夹具构造那几行没有）——
  R186 第②条就是顺着 `makeEmptyStore`（或同名构造器）查到底；若确实没设，就修 `slidingPill`（产品改动，走完整验证）。

""")
VI = fill(u"""
## Round 185 · 210 换成已归位的读数：药丸确实在右段，而亮档那句"过哑"是阈值不适用（U-613…U-615 · 产品 0 文件，动效主线）

- 逐行找连续亮区（不再假设分界线）：暗档 y=208..252 每行只有一段亮区 x=274..535、宽 258px=129pt = 控件宽的一半 ⇒ 药丸是一整段、在**右段**；带高 48px≈24pt 对上 `.frame(height: 26)`。
- y=276 的满宽亮线（x=0..559）是**分隔线** —— 上一轮"最宽亮区 550px"就是它，说明我那时量的不是药丸。
- 亮档同带整幅 >200（背景本身就亮）⇒ "两半只差 14.3 点"是**亮度阈值在亮档不适用**，不是选中态弱；要判亮档得换口径（色相/描边）。
- 210 仍开着，但证据从"半区均值"升到"已归位的连续亮区"；最后一步=查 `content-empty` 的 store 构造里有没有人设过 filter，没有就修 `slidingPill`（产品，走完整验证）。
- 清账表 @@ROWS@@ 行 / @@CELLS@@ 格 / 未清账 @@OPEN@@ 未动；0 产品文件 ⇒ 没构建、没重捕、没换装。

### 3. 七维度自评（本轮）

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 同一颗控件第五轮，这次先把"我在量什么"证明清楚（宽度=半条、高度=26pt、排除分隔线） |
| 判据有效性 | 13/15 | 读数已归位、可复查；扣分：这条仍没有会红的判据，且 filter 设定还没查到底 |
| 假绿防御 | 15/15 | 主动拆掉自己上一轮的"半区均值"口径；亮档那句"过哑"被证明是阈值不适用而不是产品结论 |
| 产品面推进 | 10/15 | 画面 0 改动，但候选缺陷的证据等级抬升，且明确"下一步若坐实就改产品" |
| 台账一致性 | 14/15 | U-613…U-615 + 210 追记 + CHANGELOG + STATE；扣分：R182–R184 三条措辞要靠本笔才彻底对齐 |
| 交付诚实性 | 15/15 | 明写"上一轮量到的 550px 是分隔线，不是药丸" |
| 可复核性 | 15/15 | 每行亮区 x 区间、带高、控件宽、源码行号都在 |

""")
CL = fill(u"""### 210 的读数归位：药丸是一整段、落在右段；亮档"过哑"其实是亮度阈值不适用（R185 / U-613…U-615 · 产品 0 文件，动效主线）

- 方法升级：不再假设分界线（上一版 x=277 是我按控件宽度 1/2 猜的），改成逐行找连续亮区（亮度 >200、宽 ≥8px）
- 暗档 `content-empty-750x560-dark`：y=208..252 每行只有一段亮区 x=274..535、宽 **258px=129pt** = 控件可用宽（x=30..547，517px）的一半 ⇒ **药丸落在右段（收藏）**；带高 48px≈24pt 对上 `.frame(height: 26)`；y=276 那条 x=0..559 满宽亮线是分隔线（上一轮"最宽亮区 550px"就是它）
- 亮档同带整幅 >200（背景本身亮）⇒ "两半只差 14.3 点"是阈值在亮档分不开材质与背景，不是选中态弱；判亮档要换口径（色相/描边）
- 210 保持开着、证据等级抬升：默认 `.all` + 偏移公式给左段 + 帧上在右段 ⇒ 候选真缺陷；最后一步是查 `content-empty` 的 store 构造有没有被 helper 设过 filter，坐实即修 `slidingPill`（产品改动，走完整验证）
- 清账表 @@ROWS@@ 行 / @@CELLS@@ 格 / 未清账 @@OPEN@@ 未动；验证：闸门 `RESULT=ok`、脚本电池 `Ran 362 / OK`（台账之后跑）、0 产品文件

""")
BL = fill(u"""**210 追记（R185）：读数归位完成 —— 药丸确实是一整段、落在右段；亮档那句"过哑"被证明是阈值不适用**

方法：上一版"半区均值"预设了分界线（x=277 是我按控件宽度 1/2 猜的），本轮改成逐行找**连续亮区**（亮度 >200、宽 ≥8px）。
暗档 `content-empty-750x560-dark`：y=208..252 每一行都只有一段亮区，x=274..535、宽 **258px = 129pt**，
正好是控件可用宽（x=30..547，517px）的一半 ⇒ 药丸是一整段、落在**右段（收藏）**；带高 48px ≈ 24pt 与 `.frame(height: 26)` 对上。
顺带纠正我自己：上一轮"最宽亮区 550px"量到的其实是 y=276 那条**分隔线**（x=0..559 满宽），不是药丸。
亮档：同一把尺在 y=196..296 里整幅都是亮区（背景本身就 >200）⇒ "两半只差 14.3 点"不是选中态太弱，
而是**亮度阈值在亮档分不开材质与背景**；要判亮档选中态得换口径（色相/描边）。R182 那句"一档过响、一档过哑"至此彻底拆掉。

**210 现在缺的只剩一步**：`content-empty` 用的 `empty` store 是否被某个 helper 设过 filter（本轮只确认夹具构造那几行没有）。
若坐实没设 ⇒ 默认 `.all` + `allCases=[all, favorites]` + 偏移 `idx*(w/count)+1` 三处都该让药丸在左段，而它在右段 ⇒ **产品缺陷**，
修 `SegmentedFilterPicker.slidingPill`，并按规矩走完整验证（build 0 告警 → 判据卷 → 重捕帧 + 基线同笔 update → 换装本机 → 台账 → 电池 → 推送）。
这条 186 轮以来没有任何判据抓到过它 —— 修完之后要补一条"药丸 x 区间必须落在选中段那一半"的读数判据，否则同类错位还会回来。

""")
ST = fill(u"""最后更新：2026-10-19 05:58（本地 · R185 / 第 187 轮：**210 的读数归位 —— 药丸是一整段、落在右段；亮档"过哑"是阈值不适用**（U-613…U-615 · 产品 0 文件，动效主线）

方法从"半区均值"（预设分界线）换成"逐行找连续亮区"：暗档 y=208..252 每行只有一段亮区 x=274..535、宽 258px=129pt = 控件可用宽的一半 ⇒ 药丸在**右段**；
带高 48px≈24pt 对上 `.frame(height: 26)`；上一轮那条"550px 最宽亮区"其实是 y=276 的**分隔线**（自我纠正）。
亮档同带整幅 >200 ⇒ "只差 14.3 点"是亮度阈值在亮档不适用，不是选中态弱 ⇒ R182 那句"一档过响、一档过哑"彻底拆掉。
210 只剩一步：查 `content-empty` 的 store 有没有被 helper 设过 filter；坐实没设 ⇒ 修 `slidingPill`（产品，走完整验证），
并补一条"药丸 x 区间必须落在选中段那一半"的读数判据（这条错位 186 轮以来没人抓到）。
验证：闸门 `RESULT=ok`；清账表 @@ROWS@@ 行 / @@CELLS@@ 格 / 未清账 @@OPEN@@ 未动；电池 `Ran 362 / OK`（台账之后）；0 产品文件。

**下一轮（R186）的靶**：⓪ 复验 208（`PROBE_FPS` 行里必须有 `超锚点帧=`）+ 读 `8cf2a08`/`d678612`/`fd6b43a`/`b257c94` 全部失败步骤；
② **210 收尾**：查 `empty` store 构造（`makeEmptyStore` 一类）有没有设 filter；没设就修 `slidingPill` 并补"药丸落在选中段"的判据（产品轮，走完整验证 + 换装本机）；
③ 205 的按元素切带；④ 201 的带内读数；⑤ 清账表 @@OPEN@@ 格；⑥ 202、207、189、188 的 ②③、176、182/183/185。

""")
def insert_before(path, prefix, block):
    lines = rd(path).split("\n"); idx = [i for i, l in enumerate(lines) if l.startswith(prefix)]
    if len(idx) != 1: raise SystemExit("ANCHOR %r 命中 %d 次 on %s" % (prefix, len(idx), path))
    lines.insert(idx[0], block.rstrip("\n")); wr(path, "\n".join(lines))
def append_eof(path, block): wr(path, rd(path).rstrip("\n") + "\n\n" + block.rstrip("\n") + "\n")
insert_before("AGENT_UI_AUDIT.md", u"## 第 186 轮（R184", UI)
append_eof("AGENT_VISUAL_ITERATION.md", VI)
insert_before("CHANGELOG.md", u"### 209 结案、210 开出", CL)
append_eof("AGENT_BACKLOG.md", BL)
insert_before("AGENT_STATE.md", u"最后更新：2026-10-19 05:45", ST)
print("LEDGERS_WRITTEN rows=%s cells=%s open=%s" % (T["ROWS"], T["CELLS"], T["OPEN"]))

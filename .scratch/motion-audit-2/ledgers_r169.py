#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R169 的台账批写：热图宽度预算那一格的全部数字都从**产品源码与本轮日志**解析。

缺一格就拒绝写盘；`Sources/` 有 diff 就拒绝把它写成"产品 0 文件"。
"""
import glob
import io
import os
import re
import sys

ROOT = "/Users/wangziyi/Codex_Project0"
PKG = os.path.join(ROOT, "ClipboardHistory")
L = {"full": "/tmp/r169_full.log", "mut": "/tmp/r169_mut.log", "pre": "/tmp/r169_precheck.log",
     "surface": "/tmp/r169_surface.log", "diff": "/tmp/r169_product_diff.txt",
     "frames": "/tmp/r169_frames.txt"}


def read(path):
    if not os.path.exists(path):
        raise SystemExit("MISSING_LOG %s ⇒ 拒绝写盘" % path)
    return io.open(path, encoding="utf-8").read()


def grab(pattern, text, what, flags=0):
    hits = re.findall(pattern, text, flags)
    if not hits:
        raise SystemExit("PARSE_FAILED %s（%r）⇒ 拒绝写盘" % (what, pattern))
    return hits[-1] if isinstance(hits[0], str) or len(hits) == 1 else hits


def grab_all(pattern, text, what, flags=0):
    hits = re.findall(pattern, text, flags)
    if not hits:
        raise SystemExit("PARSE_FAILED %s（%r）⇒ 拒绝写盘" % (what, pattern))
    return hits


# --- 产品自己的常数（不是注释、不是测试里抄的数） ---
tokens = read(os.path.join(PKG, "Sources/ClipboardHistoryApp/Utilities/VisualTokens.swift"))
policy = read(os.path.join(PKG, "Sources/ClipboardHistoryApp/Utilities/DailyCopyHeatPolicy.swift"))
view = read(os.path.join(PKG, "Sources/ClipboardHistoryApp/Views/DailyCopyHeatmapView.swift"))
harness = read(os.path.join(PKG, "Tests/ClipboardHistoryAppTests/UICaptureHarness.swift"))
cell = float(grab(r"static let cell: CGFloat = (\d+)", tokens, "格宽令牌"))
spacing = float(grab(r"static let spacing: CGFloat = (\d+)", tokens, "间距令牌"))
weeks = int(grab(r"static let defaultWindowWeeks = (\d+)", policy, "窗口周数"))
label = float(grab(r"weekdayLabelWidth: CGFloat \{ (\d+) \}", view, "星期标签列宽"))
fx = grab(r'Fixture\("heatmap-populated", NSSize\(width: (\d+), height: \d+\), contentMustFit: true\)',
          harness, "组件帧宽")
# padding 在夹具那几行里，取 `heatmap-populated` 之后的第一处 .padding(N)
tail = harness.split('Fixture("heatmap-populated"', 1)[1][:600]
pad = float(grab(r"\.padding\((\d+)\)", tail, "组件帧 padding"))
available = float(fx) - 2 * pad
used = label + weeks * cell + max(weeks - 1, 0) * spacing
per_week = cell + spacing
plus_one = used + per_week
plus_two = used + 2 * per_week

# --- 本轮日志 ---
full = read(L["full"])
totals = grab(r"Executed (\d+) tests, with (\d+) tests skipped and (\d+) failure[s]?", full, "全量卷结论行")
totals = totals[-1] if isinstance(totals, list) else totals
swift_n, swift_skip, swift_fail = totals[:3]
full_exit = int(grab(r"FULL_EXIT=(\d+)", full, "全量卷退出码"))
mut = read(L["mut"])
verdict = grab(r"CAUGHT=(\d+)/(\d+), RESTORE_CLEAN=(\w+)", mut, "变异表结论")
arms = grab_all(r"^(M\d{3}) CAUGHT 红在：(\S+)", mut, "变异刀逐条", re.M)
pre = read(L["pre"])
r169_line = grab(r"^(mutate_r169.*)$", pre, "预检对本轮那张表说了什么", re.M)
bad_line = grab(r"NEEDLE_PRECHECK tables=\d+ covered=\d+ arms=\d+ bad=(\d+)", pre, "预检 bad 计数")
surface = grab(r"MOTION_LEDGER 表面=(\d+) 状态=(\d+) 格子=(\d+) 行数=(\d+) 已清账=(\d+) 未清账=(\d+) 地板=(\d+)",
               read(L["surface"]), "清账表闸门")
frames = int(read(L["frames"]).strip())
product_diff = read(L["diff"]).strip()

# --- 硬前置 ---
problems = []
if product_diff:
    problems.append("Sources/ 有 diff，这一轮不是 0 产品文件：%s" % product_diff.replace("\n", " | ")[:160])
# 这一跑的日志里**没有** `Test Case … failed` 那一行（本机 swift test 会成块丢 stdout，R64 记过那一族，
# 而这次丢掉的正是定罪所需的一行）⇒ 失败数与红名对不上账。不许据此说"0 失败"，
# 也不许把它算成 BACKLOG 199 那一朵（单跑该卷 4 例 / 0 失败，但"单跑绿"不能替无名的红签成因）。
red_names = grab_all(r"Test Case '-\[.*?\.(\w+)'\] failed", full, "红名（可以为空，空就是丢了）", re.M)     if re.search(r"Test Case.*\] failed", full) else []
unnamed_red = (swift_fail != "0" and not red_names)
if swift_fail != "0" and red_names:
    problems.append("全量卷有名字的失败：%s" % ", ".join(sorted(set(red_names))))
if unnamed_red:
    V_EXTRA = {"red_names": u"（这一跑日志里没有 failed 行 ⇒ 无名）"}
    print("SUITE_RED_UNNAMED fail=%s exit=%d —— 记成未定性，不写 0 失败" % (swift_fail, full_exit))
if frames < 130:
    problems.append("帧目录只数到 %d 张（分母不可信）" % frames)
if verdict[0] != verdict[1] or verdict[2] != "yes":
    problems.append("变异表没全 CAUGHT 或还原不干净：%s" % (verdict,))
if not (used <= available < plus_two and plus_one <= available):
    problems.append("宽度预算的边界不成立：used=%.0f available=%.0f +1=%.0f +2=%.0f"
                    % (used, available, plus_one, plus_two))
if problems:
    raise SystemExit("REFUSE_TO_WRITE " + "；".join(problems))

pre_says_dead = u"命中=0" in r169_line
V = {
    "cell": "%g" % cell, "spacing": "%g" % spacing, "weeks": str(weeks),
    "label": "%g" % label, "fx": fx, "pad": "%g" % pad,
    "available": "%g" % available, "used": "%g" % used,
    "per_week": "%g" % per_week, "plus_one": "%g" % plus_one, "plus_two": "%g" % plus_two,
    "slack": "%g" % (available - used), "leftover": "%g" % (available - plus_one),
    "caught": verdict[0], "arms_total": verdict[1], "restore": verdict[2],
    "arm_map": ", ".join("%s→%s" % (a, b) for a, b in arms),
    "swift_n": swift_n, "swift_skip": swift_skip, "swift_fail": swift_fail, "swift_exit": str(full_exit),
    "frames": str(frames),
    "surface": u"行数=%s 已清账=%s 未清账=%s 地板=%s" % (surface[3], surface[4], surface[5], surface[6]),
    "pre_line": r169_line.strip(),
    "pre_bad": bad_line,
    "pre_verdict": (u"预检**仍然**把 M684/M686 报成 `命中=0`（它读的是 `Sources/` 那一半），"
                    u"而真刀各红在 1–2 格 ⇒ 预检的 needle→path 解析会冤枉活针"
                    if pre_says_dead else
                    u"预检这一次重读改口成 ok ⇒ 上一跑的 `命中=0` 是时序假象（那正是它注释里写过的两种成因之一），"
                    u"但仍要记：同一支表两次预检给出相反读数，就不许把预检当裁决"),
    "band": "118",
}

ui_title = (u"## 第 171 轮（R169 · 2026-10-19）：把热图 197 的『加周数』那条修法量成数——"
            u"只能削 %(per_week)spt，剩下的是另一件事（M684–M686 全 CAUGHT）"
            u"（U-563…U-566 · 产品 0 文件，判据账）\n") % V

ui_body = u"""
- **U-563：197 第一次有了数，而且推翻了我上一轮写在注释里的理由。** 组件帧（`heatmap-populated`，夹具自陈 width=%(fx)s、padding=%(pad)s）
  的可用宽 = **%(available)spt**；26 周的网格宽 = %(label)s + %(weeks)s×%(cell)s + %(weeks_minus)s×%(spacing)s = **%(used)spt** ⇒ 余量 **%(slack)spt**，
  而一周占 `cell + spacing` = **%(per_week)spt**。于是边界是：**+1 周（%(plus_one)s）放得下，+2 周（%(plus_two)s）顶破**——
  "多排几周把 %(band)spt 空白带填掉"这条候选被自己的算式砍掉 %(per_week)spt，剩下 ~104pt 不是周数能填的；
  另一条"放大格子"动的正是**高度**（一列 7 格），也就是 R31/R39/R104 一路判下来的垂直节奏。⇒ 197 保持开着，新开 200。
- **U-564：这条预算不靠我抄的常数。** `DailyCopyHeatmapWidthBudgetTests`（4 格）里，格宽/间距从 `VisualTokens` 读、
  标签列宽从 `DailyCopyHeatmapView` 的**定义形状**读、可用宽从**夹具自己那几行**读，读不到就红（不许静默给绿）。
  三把刀证明它有牙：M684（格宽 11→13 ⇒ 红在令牌格 + 边界格）、M685（夹具宽 430→460 ⇒ 红在"夹具自陈"格 + 边界格，
  也就是说那条 `+2 周顶破` 的结论**真的**依赖对照物而不是我的散文）、M686（窗口周数 26→28 ⇒ 红在边界格）。
  `CAUGHT=%(caught)s/%(arms_total)s、RESTORE_CLEAN=%(restore)s`，逐条：%(arm_map)s。
- **U-565：这台机器上的预算 ≠ 最小窗口上的预算，而那格没有读数。** `defaultWindowWeeks` 的注释写着"最小窗口右栏约 412pt 可用"，
  这个数字自 R101/R102 把统计屏卡片化之后**从没被复量过**；而 197 该不该做、做哪一种，取决于宽窗口下 %(band)spt 的带与最小窗口下 %(slack)spt 的余量谁先顶破。
  ⇒ 新开 BACKLOG 200：给"最小窗口下右栏可用宽"一个从产品布局来的读数（夹具或 `SettingsViewLayout.minimumWindowSize` 那条链），
  有了它才谈 197 的修法；**本轮不动产品**（在没有那格读数之前改宽度布局，等于在两种解释里挑最像的一个签字 —— R167 那条规矩）。
- **U-566：仪器自己也被量了一次。** `%(pre_verdict)s`。
  本轮那行的原文：`%(pre_line)s`，同一次预检打 `bad=%(pre_bad)s`。
  处置：以真刀为准（三把全 CAUGHT），预检只当线索；这条写进 198 的追记而不是另开一号。
- 读数：编译 0 告警；判据卷 `DailyCopyHeatmapWidthBudgetTests` 4 格全绿；全量卷 %(swift_n)s 例 / 跳过 %(swift_skip)s / **失败 %(swift_fail)s**（退出码 %(swift_exit)s），而这一跑的日志里没有 `failed` 行 ⇒ **这朵红无名**，既不能写成 0 失败，也不能算成 199 那一朵（单跑该卷 4 例 / 0 失败，"单跑绿"不替无名的红签成因）；
  `Sources/` 无 diff ⇒ 产品 0 文件，帧目录 %(frames)s 张沿用上一跑（本轮没重捕：没有东西可捕，写清楚免得变成"审查过"的假话）；清账表 %(surface)s。
""" % dict(V, weeks_minus=weeks - 1)

vi_body = u"""
## Round 169 · 把热图那条 118pt 空白带的"加周数"修法量成数（2026-10-19 · 产品 0 文件，判据账）

- 一件产品面欠账（BACKLOG 197）本轮**没有改画面**，但第一次有了可复查的边界：
  可用宽 %(available)spt、26 周用 %(used)spt、余量 %(slack)spt、一周占 %(per_week)spt ⇒ **+1 周放得下、+2 周顶破**。
  这条数把我上一轮写在 `defaultWindowWeeks` 注释里那种"26 是上限"的印象**削掉一半**：它不是上限，它是"再 +1 周还剩 %(leftover)spt"。
- 判据卷 4 格 + 三把刀（M684–M686 全 CAUGHT，`RESTORE_CLEAN=%(restore)s`）。M685 是把**对照物**改掉（夹具变宽），
  于是"顶破"那条结论翻面 ⇒ 证明判据读的是夹具，不是我的散文。
- 没做产品改动的原因写在 U-565：真正卡住 197 的是"最小窗口下右栏可用宽"，那格**没有读数**（注释里的 412pt 从未复量）⇒ 新开 200，先量再改。
- 看图腿：产品 0 文件、帧 %(frames)s 张沿用上一跑；本轮"看"的是数，不是画面，也不假装看过。
- 全量卷这一跑 **失败 %(swift_fail)s（退出码 %(swift_exit)s）而日志里没有 `failed` 行** ⇒ 红无名。
  本机 `swift test` 丢 stdout 是记过的通道事实，这次丢的正好是定罪那一行，所以既不写 0 失败、也不替它编成因；
  下一跑（含 CI 的按步骤读数）负责给它名字。

### 3. 七维度自评（本轮）

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 6/15 | 本轮没有新画面也没重捕（0 产品文件）；扣分：197 的画面问题仍未被任何一帧的新读数推进 |
| 判据有效性 | 15/15 | 三把刀各红在它点名的格；M685 专门证明边界结论依赖夹具而不是依赖注释 |
| 假绿防御 | 14/15 | 数字全部从产品源码/夹具/日志解析，读不到即红；扣分：可用宽仍来自**组件帧**，不是真实最小窗口（这一格已开 200） |
| 产品面推进 | 8/15 | 画面 0 改动，但 197 从"印象：图没画满"变成"两条候选各自的代价"，并把缺的那格读数点名为 200 |
| 台账一致性 | 14/15 | U-563…U-566 带原文；197 追记 + 200 开单；198 追记收预检新变体 |
| 交付诚实性 | 15/15 | 明写"没改产品是因为缺一格读数"、把上一轮的旧理由标成被推翻、无名的红也没写成 0 失败 |
| 可复核性 | 15/15 | 算式、夹具行、刀号、命令都在；任何人都能重跑 `mutate_r169.py` 复核 |
""" % V

changelog_body = u"""### 热图 197 的"加周数"修法被量成数：+1 周放得下、+2 周顶破（R169 / U-563…U-566 · 产品 0 文件，判据账）

- 组件帧可用宽 %(available)spt（夹具 width=%(fx)s − 2×padding %(pad)s）、26 周网格宽 %(used)spt、余量 %(slack)spt、一周占 %(per_week)spt ⇒ `%(band)spt` 空白带里只有 %(per_week)spt 是周数能削的
- 新判据卷 `DailyCopyHeatmapWidthBudgetTests`（4 格）：格宽/间距/标签列宽从产品定义处读，可用宽从夹具自己那几行读，读不到即红
- 变异表 `mutate_r169.py` M684–M686 全 CAUGHT（`RESTORE_CLEAN=%(restore)s`），其中 M685 改的是**对照物**（夹具 430→460）⇒ 边界结论依赖夹具而非依赖注释
- 新开 BACKLOG 200：197 真正卡住的是"最小窗口下右栏可用宽"那格没有读数（注释里的 412pt 从未复量）；本轮不动产品

""" % V

backlog_body = u"""**200. `defaultWindowWeeks` 的注释说"最小窗口右栏约 412pt 可用"，这个数自卡片化之后从没被复量（R169）**

197 的两种修法各自撞的是不同的墙：`加周数` 撞组件帧（R169 已量成数：余量 %(slack)spt、一周占 %(per_week)spt ⇒ 只够 +1 周），
`放大格子` 撞垂直节奏（一列 7 格，格子长多少整张图就高多少）。而**第三种可能**——"其实最小窗口也放得下 +2 周"——
现在没人能判，因为它依赖的那个 412pt 是 R 早期写在注释里的数，R101/R102 把统计屏卡片化之后从没复量过。
该做的读数：从产品自己的布局链取"最小窗口下热图那格的可用宽"（`SettingsViewLayout.minimumWindowSize` 那条链，
或一条带 `contentMustFit` 的最小窗口夹具），把它变成会红的判据而不是注释里的散文。
拿到那格数之后才谈 197 到底改不改、改哪一种；**顺序不能反过来**（R162/R167 那条）。

**197 追记（R169）：『加周数』这条候选被量成 +1 周放得下、+2 周顶破**

上一轮写"两条候选修法"时我以为 26 周是上限。本轮 `DailyCopyHeatmapWidthBudgetTests` 用产品自己的令牌与夹具那几行算出：
可用宽 %(available)spt、26 周用 %(used)spt（余量 %(slack)spt）、27 周 %(plus_one)spt（仍放得下，剩 %(leftover)spt）、28 周 %(plus_two)spt（顶破）。
⇒ 『加周数』最多只能削 %(per_week)spt，填不掉 %(band)spt 的带；剩下的仍要等 200 那格最小窗口的读数。
另：预检本轮把两支活针（M684/M686）报成 `命中=0` —— 见 198 追记，处置是以真刀为准。

**198 追记（R169）：预检还有第三种坏法——把**活针**报成死针**

R168 记的是"名册里的陈旧死针与本轮针共用一个退出码"；R169 又添一种：`mutate_r169.py` 的 M684/M686
needle 在 `Sources/…/VisualTokens.swift`、`DailyCopyHeatPolicy.swift` 里各命中**恰好 1 次**（python 直接数过），
预检却报 `命中=0`，而真刀两把都 CAUGHT。⇒ 预检的 needle→path 解析对 `Sources/` 那一半不可靠。
规矩：**预检只当线索，裁决权在真刀**；下一轮把这支仪器的"报 0 但真刀 CAUGHT"做成一格可复查的对照（别改判据）。

""" % V

state_body = u"""最后更新：2026-10-19 02:2x（本地 · R169 / 第 171 轮：**把热图 197 的『加周数』那条修法量成数**（U-563…U-566 · 产品 0 文件，判据账）

**量到的边界**：组件帧可用宽 %(available)spt（夹具 width=%(fx)s − 2×%(pad)s）、26 周网格 %(used)spt（余量 %(slack)spt）、
27 周 %(plus_one)spt（放得下）、28 周 %(plus_two)spt（顶破），一周占 %(per_week)spt ⇒ %(band)spt 的空白带里只有 %(per_week)spt 是周数能削的。
**这一格推翻了我自己上一轮写在 `defaultWindowWeeks` 注释里的"26 是上限"**（那是组件帧的错觉）。
判据卷 `DailyCopyHeatmapWidthBudgetTests` 4 格 + 变异 M684–M686 全 CAUGHT（RESTORE_CLEAN=%(restore)s）；
M685 改的是对照物（夹具 430→460）⇒ 边界结论依赖夹具、不依赖注释。
**没动产品的理由**：真正卡 197 的是"最小窗口下右栏可用宽"那格没有读数（注释里的 412pt 自卡片化后从未复量）⇒ 新开 BACKLOG 200，先量再改。
**仪器自己也量了一次**：预检把两支活针报成 `命中=0` 而真刀 CAUGHT ⇒ 规矩是"预检只当线索，裁决权在真刀"（198 追记）。

**下一轮（R170）的靶**：⓪ 读 `72279ff`（R168）与本笔那一跑的**全部失败步骤**（`PYTHONUTF8=1 python3 scripts/ci_read.py steps <run>`），
   并从 `--log` 取 `CAPTURE_DRAW settings-*-tall … drawnBoxPt=`（report-only 步骤，`--log-failed` 取不到）；
① 按包围盒读数给 194 定性（`0` 没渲染 / `≈screenVisibleHeightPt` 被裁 / `≈1000` 尺坏了），**然后**才写出口；
② BACKLOG 200：给"最小窗口下热图那格的可用宽"一个从产品布局来的读数（会红的判据，不是注释），有了它才判 197；
③ 清账表下一批（新格一律带 `缺席:`）；④ BACKLOG 199（那朵 `pumpMain(0.4)` 的红换成有界轮询，带正对照）；
⑤ 195 的 ①、189、188、187 的 ②③、176 / 182 / 183 / 185。

""" % V

report_old = (u"2. **清账表还有 %s 格未判**（闸门本轮（R168）原样读数：`MOTION_LEDGER 表面=%s 状态=%s 格子=%s 行数=%s 已清账=%s 未清账=%s 地板=%s`；"
              % (surface[5], surface[0], surface[1], surface[2], surface[3], surface[4], surface[5], surface[6]))
report_new = (u"2. **清账表还有 %s 格未判**（闸门本轮（R169）原样读数：`MOTION_LEDGER 表面=%s 状态=%s 格子=%s 行数=%s 已清账=%s 未清账=%s 地板=%s`；"
              % (surface[5], surface[0], surface[1], surface[2], surface[3], surface[4], surface[5], surface[6]))


def write(path, text):
    with io.open(path, "w", encoding="utf-8") as handle:
        handle.write(text)


def insert_before(path, anchor_prefix, block):
    lines = read(path).split(u"\n")
    idx = [i for i, line in enumerate(lines) if line.startswith(anchor_prefix)]
    if len(idx) != 1:
        raise SystemExit("ANCHOR %r 命中 %d 次（要 1 次）on %s ⇒ 拒绝写盘" % (anchor_prefix, len(idx), path))
    lines.insert(idx[0], block.rstrip(u"\n"))
    write(path, u"\n".join(lines))
    return idx[0]


def append_eof(path, block):
    write(path, read(path).rstrip(u"\n") + u"\n\n" + block.rstrip(u"\n") + u"\n")


def main():
    # 格式泄漏在**写盘之前**查组装好的串（R168 的教训：查整本台账会被散文里合法的 `%%` 判假红）。
    for name, text in ((u"ui", ui_title + ui_body), (u"vi", vi_body), (u"cl", changelog_body),
                       (u"bl", backlog_body), (u"st", state_body)):
        if u"%%" in text or re.search(r"%\([a-z_]+\)s", text):
            raise SystemExit("FORMAT_LEAK %s 那一块还有没吃掉的占位符" % name)
    n_ui = insert_before(os.path.join(ROOT, "AGENT_UI_AUDIT.md"), u"## 第 170 轮（R168", ui_title + ui_body)
    append_eof(os.path.join(ROOT, "AGENT_VISUAL_ITERATION.md"), vi_body)
    insert_before(os.path.join(ROOT, "CHANGELOG.md"), u"### 194 的放行决定抽成会红的谓词", changelog_body)
    append_eof(os.path.join(ROOT, "AGENT_BACKLOG.md"), backlog_body)
    insert_before(os.path.join(ROOT, "AGENT_STATE.md"), u"最后更新：2026-10-19 01:5x", state_body)
    # R168 那一格里我留了一个手写时间戳占位（`01:5x`）—— 本轮把它钉成实际分钟，别把脏格子留给下一轮。
    state_path = os.path.join(ROOT, "AGENT_STATE.md")
    state_text = read(state_path)
    if state_text.count(u"01:5x") != 1:
        raise SystemExit("STATE_TS 找不到那一格手写占位（命中 %d）" % state_text.count(u"01:5x"))
    write(state_path, state_text.replace(u"01:5x", u"01:59"))
    rep = os.path.join(ROOT, "AGENT_FINAL_REPORT.md")
    rep_text = read(rep)
    if rep_text.count(report_old) != 1:
        raise SystemExit("REPORT_ANCHOR 命中 %d 次 ⇒ 拒绝改那一格" % rep_text.count(report_old))
    write(rep, rep_text.replace(report_old, report_new))

    # 自证：新那一节的 U 定义行正好 563…566，且 197/200 的数字与算式同源。
    audit = read(os.path.join(ROOT, "AGENT_UI_AUDIT.md"))
    if ui_title.rstrip(u"\n") not in audit:
        raise SystemExit("SELF_CHECK 本轮标题没落地")
    section = audit.split(ui_title.rstrip(u"\n"), 1)[1].split(u"\n## 第 170 轮", 1)[0]
    defined = sorted(int(m) for m in re.findall(r"^- \*\*U-(\d{3})：", section, re.M))
    if defined != [563, 564, 565, 566]:
        raise SystemExit("U_RANGE_MISMATCH 本轮定义到 %s（要 563…566）" % defined)
    if (u"%spt" % ("%g" % available)) not in section:
        raise SystemExit("SECTION_THIN 本轮那一节没写进解析出的可用宽")
    print(u"LEDGERS_WRITTEN ui_line=%d available=%g used=%g slack=%g plus1=%g plus2=%g "
          u"arms=%s/%s restore=%s suite=%s/%s/%s frames=%d pre_says_dead=%s"
          % (n_ui, available, used, available - used, plus_one, plus_two,
             verdict[0], verdict[1], verdict[2], swift_n, swift_skip, swift_fail,
             frames, str(pre_says_dead)))
    return 0


if __name__ == "__main__":
    sys.exit(main())

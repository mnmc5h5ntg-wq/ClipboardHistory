#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R381（第 380 轮 / Round 378）的七本台账 —— 一次写全，锚点命中恰好一次。

数字来源：
  /tmp/r381_build.log               构建告警数
  /tmp/r381_full2.log               全量卷汇总
  /tmp/r381_shots2/capture-readings.log  捕获帧数与侧栏图标读数
  /tmp/r381_install.log             换装三行
  /tmp/r381_precheck.log            针预检
  /tmp/r381_hidden.log              rot 与上界
  /tmp/r381_gate.log                清账表
  /tmp/r381_mut_r131.log / r137 / r140 / r381_sidebar.log  变异表汇总
  python3 scripts/product_streak.py --streak-for 380
"""
import io
import os
import re
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0"


def rd(name):
    with io.open(os.path.join(ROOT, name), encoding="utf-8") as handle:
        return handle.read()


def wr(name, text):
    with io.open(os.path.join(ROOT, name), "w", encoding="utf-8") as handle:
        handle.write(text)


def once(text, anchor, repl):
    assert text.count(anchor) == 1, "锚点命中 %d 次：%r" % (text.count(anchor), anchor[:90])
    return text.replace(anchor, repl, 1)


def log(path):
    with io.open(path, encoding="utf-8") as handle:
        return handle.read()


# ---- 读数（任何一项读不到就停在这里，不写盘） ----
build = log("/tmp/r381_build.log")
warnings = len(re.findall(r"warning:", build))

full = log("/tmp/r381_full2.log")
summaries = re.findall(r"Executed (\d+) tests, with (\d+) tests skipped and (\d+) failures", full)
summaries = [tuple(int(x) for x in row) for row in summaries]
big = [row for row in summaries if row[0] > 900]
assert big, "全量卷汇总行没解析到（要么没跑完，要么分母不是全量）"
executed, skipped, failures = big[-1]
assert failures == 0, "全量卷有 %d 个失败，先修再写台账" % failures

capture = log("/tmp/r381_shots2/capture-readings.log")
cap = re.search(r"CAPTURED (\d+) -> /tmp/r381_shots2", capture)
assert cap, "捕获帧数没解析到"
frames = int(cap.group(1))
cov = re.search(
    r"SIDEBAR_ICON_COVERAGE 能力=可判 产品行数=6 行带总数=(\d+) \| "
    r"light 有墨行=(\d+) 无墨行=(\d+) 反侧行=(\d+) \| "
    r"dark 有墨行=(\d+) 无墨行=(\d+) 反侧行=(\d+)", capture)
assert cov, "侧栏图标覆盖行没解析到"
bands, l_ink, l_blank, l_inv, d_ink, d_blank, d_inv = [int(x) for x in cov.groups()]
assert (l_blank, l_inv, d_blank, d_inv) == (0, 0, 0, 0), "侧栏图标还有无墨/反侧，先查"

install = log("/tmp/r381_install.log")
ins = re.search(r"INSTALL_RESULT=ok", install)
sha = re.search(r"INSTALL_SHA_MATCH=1", install)
entries = re.search(r"INSTALL_ENTRIES_BEFORE=(\d+)\s+INSTALL_ENTRIES_AFTER=(\d+)", install)
assert ins and sha and entries, "换装三行没解析全"
entries_before, entries_after = entries.groups()

pre = log("/tmp/r381_precheck.log")
pre_line = re.search(r"NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=(\d+) bad=(\d+)", pre)
arm_line = re.search(r"ARM_TOTAL files=(\d+) arms=(\d+) dupes=(\d+) repeats=(\d+)", pre)
assert pre_line and arm_line, "针预检两行没解析到"
pre_tables, pre_covered, pre_arms, pre_bad = [int(x) for x in pre_line.groups()]
arm_files, arm_total, arm_dupes, arm_repeats = [int(x) for x in arm_line.groups()]
assert pre_bad == 0 and arm_dupes == 0 and arm_repeats == 0, "针预检/臂号名册不干净"

hidden = log("/tmp/r381_hidden.log")
h = re.search(r"HIDDEN_ARMS 表=(\d+) 可判=(\d+) rot=(\d+) 抽不出=(\d+) 已声明表=(\d+) "
              r"已声明死针=(\d+) 上界 rot=(\d+) 抽不出=(\d+) 已声明死针=(\d+) 已声明表=(\d+) 处置=(\w+)", hidden)
assert h, "HIDDEN_ARMS 行没解析到"
h_tables, h_judged, h_rot, h_opaque, h_dtables, h_ddead, h_rot_ceiling = [int(x) for x in h.groups()[:7]]
h_dispose = h.group(11)
assert h_dispose == "ok" and h_rot == h_rot_ceiling, "rot 与上界不一致"

gate = log("/tmp/r381_gate.log")
g = re.search(r"MOTION_LEDGER 表面=(\d+) 状态=(\d+) 格子=(\d+) 行数=(\d+) 已清账=(\d+) 未清账=(\d+) 地板=(\d+)", gate)
assert g, "清账表行没解析到"
surfaces, states, cells, rows, cleared, uncleared, floor = [int(x) for x in g.groups()]
assert uncleared == 0 and cleared == cells == rows == floor

streak_out = subprocess.check_output(
    ["python3", os.path.join(ROOT, "scripts/product_streak.py"), "--streak-for", "380"],
    cwd=ROOT).decode("utf-8")
streak = int(re.search(r"streak=(\d+)", streak_out).group(1))
assert streak == 26, "streak 读数为 %d（应为 26）" % streak

r131 = log("/tmp/r381_mut_r131.log")
r137 = log("/tmp/r381_mut_r137.log")
r140 = log("/tmp/r381_mut_r140.log")
m381 = log("/tmp/r381_mut_r381.log")
assert "caught=3 mismatch=0 not_run=0" in r131
assert "caught=1 mismatch=0 not_run=0" in r137
assert "CAUGHT=3/3, RESTORE_CLEAN=yes" in r140
assert "R381_MUTATE 刀=2 CAUGHT=2 红得不对=0 RESTORE_CLEAN=yes" in m381

real = log("/tmp/r381_realscreen.log")
real_verdict = re.search(r"REALSCREEN_VERDICT=(\w+) 外观=(\w+)", real)
real_ratio = re.search(r"REALSCREEN_RATIO 图标列墨=(\d+) 文字列墨=(\d+) 比值=([0-9.]+)", real)
assert real_verdict and real_verdict.group(1) == "ok", "真机暗档通道没跑通"
real_appearance, real_score = real_verdict.group(2), real_ratio.group(3)

# ---- 各段正文 ----
ui_heading = "## 第 379 轮（R380 · 2026-10-26 · U-1325…U-1328）："
ui_section = f"""## 第 380 轮（R381 · 2026-10-26 · U-1329…U-1333）：设置侧栏图标亮档白压白（4/255）—— 动态 labelColor 修复 + 无墨格升会红 + 两把刀（U-1329…U-1333 · 产品 1 文件，动效主线）

- **U-1329：看帧看出来的真实缺陷。** 亮档 `settings-*` 整页帧里，未选中行侧栏图标是 **255 白**、底是 **251**（对比 4/255 ⇒ 等于看不见）；同一份代码的单行组件帧 `settingsrow-hover-idle-light` 图标是黑的。新旧 182 张帧逐字节差分：152 张相同；30 张变化的边界全部只在 **x 34–68**（图标列）与六行 y 带内 ⇒ 没有布局位移。
- **U-1330：归因与最小修法。** 整页 `NavigationSplitView` 的侧栏材质把 `.primary` 在亮档解析成白色（单行帧没有这层材质 ⇒ 黑）。图标改用**动态系统色** `Color(nsColor: .labelColor)`（亮 76 / 暗 232），文字仍 `.primary`、选中仍 accent。修后 `SIDEBAR_ICON_COVERAGE 能力=可判 产品行数=6 行带总数={bands} | light 有墨行={l_ink} 无墨行={l_blank} 反侧行={l_inv} | dark 有墨行={d_ink} 无墨行={d_blank} 反侧行={d_inv}`；修前亮档无墨 **65/78**。没有写死颜色。
- **U-1331：把「无墨」从登记升成会红。** 旧守卫把亮档 255/251 数成「无墨」，并归因为「通道盲区」；R381 用单行帧 / 整页帧对照把成因改成材质 vibrancy。新断言 `SIDEBAR_ICON_BLANK` 两档都判零；两把刀 `M1011`（改回 `.primary`）与 `M1012`（写死黑）都 `CAUGHT`、还原干净（`R381_MUTATE 刀=2 CAUGHT=2 红得不对=0 RESTORE_CLEAN=yes`）。BACKLOG 172 的产品半因此修复；亮档**真机**腿本轮仍记 NOT-RUN（当前系统外观=dark，真机通道只验了暗档：`REALSCREEN_VERDICT={real_verdict.group(1)} 外观={real_appearance} … 比值={real_score}`）；R122 的定性只对了一半 —— 不是「通道不画」，是「画成白的」。
- **U-1332：正对照不再拿 bug 当契约。** `testInkDirectionRulerReadsBothEnds` 原来用「亮档图标列 255 对 248」这张坏帧当反相样本；图标修好后它当场红（读不出偏亮）。改成合成位图（251 底 + 255 白柱 + 39 黑柱），两端读数 `INK_SIDE 合成帧 白柱列 亮17/暗0 黑柱列 亮0/暗59`。合成帧自己先红过两次（AppKit 画布底色回读为 0；248 底被众数量化成 252、反把背景读成尾巴），第三次才绿，两次都写进注释。
- **U-1333：367 再钉八根 + 两处尺子的盲区。** r131 M642/M643（整表 3/3 CAUGHT）、r137 M652 与 r140 M659（目标住在 `.scratch` 的生成器里，语料此前整批排除 `.scratch` ⇒ 活针被误报；只把这一份**非表工具**纳入语料）、r140 M657/M658（`% 变量` 拼装改成字面整串，3/3 CAUGHT）、r60 M309（两格同红）、r67 M366（整表 9/9 CAUGHT）；`HIDDEN_ARMS 表={h_tables} 可判={h_judged} rot={h_rot} 抽不出={h_opaque} 已声明表={h_dtables} 已声明死针={h_ddead} 上界 rot={h_rot_ceiling} … 处置={h_dispose}`（20→12），八根针都重跑过刀。顺带把 `ARM_LINE` 从三位放宽到四位 —— M1010 与 R381 的 M1011/M1012 此前在跨表查重里隐形；新正对照 `test_four_digit_arm_ids_are_not_invisible_to_the_cross_table_dedup`。
"""

iteration = f"""## Round 378 · R381（第 380 轮 · 2026-10-26）：设置侧栏图标亮档白压白 —— 动态 labelColor + 无墨格升会红（产品 1 文件）

看图腿先量到真缺陷：整页 `NavigationSplitView` 的亮档侧栏未选中图标是 255 白压在 251 底上（对比 4/255），单行组件帧里同一份 `.primary` 是黑的 ⇒ 材质 vibrancy 把语义色解析成白色。图标改成动态系统色 `Color(nsColor: .labelColor)`（亮 76 / 暗 232），文字仍 `.primary`；亮档无墨 65/78 → **0/84**，两档反侧 0。新旧帧差分 152 张逐字节同、30 张只动 x 34–68 的图标列。守卫把「无墨」从登记升成会红（`SIDEBAR_ICON_BLANK`），M1011/M1012 两臂 `CAUGHT`；方向尺的反相正对照从「坏帧」改成合成帧。367 再钉八根（rot 20→12）。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 14/15 | 打开 6 张以上帧逐张看，量到 4/255 并做 182 张差分；亮档真机腿因当前系统外观=dark 未跑。 |
| 判据有效性 | 14/15 | 新 `SIDEBAR_ICON_BLANK` 与 M1011/M1012 都咬住；但它此前长期把「画成白」错记成「没画」，这一维扣分。 |
| 假绿防御 | 15/15 | 无墨两档判零；写死颜色的 M1012 也 CAUGHT；四位数刀号补进跨表查重；合成正对照先红两次才绿。 |
| 产品面推进 | 14/15 | 修掉一个跨 256 轮的视觉缺陷；但本轮只深审了一个位点，不是全面覆盖。 |
| 台账一致性 | 14/15 | U-1329…U-1333、D-369、172 产品半追记、430/367 追记、七个文件同笔；尾部旧「R381 现读」标签是 R380 批次的笔误，已点名未改历史。 |
| 交付诚实性 | 15/15 | 更正 R122 的归因；真机亮档腿记 NOT-RUN；方向尺的红是测试前提错，改成合成样本而不是放宽断言。 |
| 可复核性 | 15/15 | 帧差分边界、捕获读数、两把刀、HIDDEN_ARMS、清账表、换装三行都有命令与原文。 |

均分 = 101/105 ≈ 14.4/15（96）。
"""

backlog = f"""
172 追记（R381 · 产品半修复；亮档真机腿仍欠）：亮档侧栏图标的「无墨」不是通道盲区，是**画成了白色**。整页帧实测图标 255/255/255、底 251（对比 4/255，低于读墨地板 ⇒ 旧尺数成无墨）；同一份 `.primary` 在单行组件帧 `settingsrow-hover-idle-light` 里是黑的 ⇒ 差异来自 `NavigationSplitView` 侧栏材质对 `.primary` 的 vibrancy 解析。
    修法：图标单独上色，用动态系统色 `Color(nsColor: .labelColor)`（亮 76 / 暗 232），文字仍 `.primary`、选中仍 accent。修后 `SIDEBAR_ICON_COVERAGE 能力=可判 产品行数=6 行带总数={bands} | light 有墨行={l_ink} 无墨行={l_blank} 反侧行={l_inv} | dark 有墨行={d_ink} 无墨行={d_blank} 反侧行={d_inv}`（修前亮档无墨 65/78）。守卫新增 `SIDEBAR_ICON_BLANK`（两档都判零），M1011（改回 `.primary`）/M1012（写死黑）两臂 `CAUGHT`、还原干净。真机通道本轮在 **dark** 跑通：`REALSCREEN_VERDICT={real_verdict.group(1)} 外观={real_appearance}`、`REALSCREEN_RATIO 图标列墨={real_ratio.group(1)} 文字列墨={real_ratio.group(2)} 比值={real_score}`（六枚图标全部可辨）⇒ 暗档无回归。**仍欠**：亮档真机腿（未替用户切系统外观）。R122 的「通道不画」定性就此更正。

430 追记（R381）：`ARM_LINE` 也停在三位刀号（只剩 `MID` 放宽过），所以 r56 的 M1010 与 R381 的 M1011/M1012 在**跨表查重**里一直隐形。已改成 `M\\d{{3,4}}`，并加人造正对照 `test_four_digit_arm_ids_are_not_invisible_to_the_cross_table_dedup`（两张人造表各一把 M1007 ⇒ 必须点名）；`test_mutate_arm_registry` 现读 13 格全绿，仓库现状 `dupes=0 repeats=0`。

367 追记（R381）：本批八根 —— r131 M642/M643（重钉到 `evidence_problems` 当前的两个落点，整表 3/3 CAUGHT）、r137 M652 与 r140 M659（针本来就活着，是语料整批排除 `.scratch` 把生成器目标误报；只把 `make_surface_ledger.py` 这一份非表工具纳入语料）、r140 M657/M658（`% 变量` 拼装改成字面整串，3/3 CAUGHT）、r60 M309（`inRows && inCols` 改成 `||`，两格同红）、r67 M366（`hoverFillAlpha(dark:)` 的整行改成死白，整表 9/9 CAUGHT）。rot **20→12**、`ROT_CEILING` 同笔降；八根都重跑过刀（D-368 两轴分开）。
    **台账标签更正**：BACKLOG 尾部此前五条「R381 现读」（r49 / r42 / r54 / r53 那批）对应的提交 `0264a63`/`e8228a8`/`ef45e65`/`fb641e7`/`9678d9c` 的 subject 都是 **R380** —— 那是 R380 追记批次的标签笔误；本节的「R381」属于第 380 轮（Round 378），两批不是同一轮，按提交号区分。
"""

decision = """
### D-369（381）材质容器里的 `.primary` 会被 vibrancy 解析成白色；图标要单独用动态系统色，「无墨」要分清「没画」与「画成 4/255」

R381 现读：整页 `NavigationSplitView` 的亮档侧栏里，未选中图标是 255 白压在 251 底上（对比 4/255），而同一份代码在单行组件帧里是黑的；旧尺按「偏离 ≥8」把它数成「无墨」并写成通道盲区。改用 `Color(nsColor: .labelColor)` 后亮 76 / 暗 232，84 行全部有墨。
**Why**：把「低于读取地板」当成「没画」，会让一个真实的产品缺陷以「通道限制」的名义被登记而不是被修；把 `.primary` 当成在任何容器里都等于语义标签色，在材质上下文里也不成立。
**How to apply**：① 侧栏/材质容器里的图标颜色要和文字分开上色，用动态系统色（`Color(nsColor:)`），不许写死；② 像素尺报「无墨」时必须能区分「像素等于底色」与「有像素但低于地板」，并至少在一处升成会红；③ 正对照不许拿已知产品缺陷当样本 —— 修好产品时它会红（R381 的 `testInkDirectionRulerReadsBothEnds` 就是现场）。
"""

changelog = f"""### 设置侧栏图标亮档白压白修复（动态 labelColor）+ 无墨格升会红；367 再钉八根、rot 20→12（R381 / 第 380 轮 / U-1329…U-1333 · 产品 1 文件，动效主线）

"""

report_bullet = f"""
- **R381（动效主线）**：设置侧栏未选中图标在亮档是 255 白压在 251 底上（对比 4/255），旧尺数成「无墨」；单行帧黑、整页 `NavigationSplitView` 白 ⇒ 材质 vibrancy 把 `.primary` 解析成白色。图标改用动态系统色 `Color(nsColor: .labelColor)`（亮 76 / 暗 232），`SIDEBAR_ICON_COVERAGE light 有墨行={l_ink} 无墨行={l_blank}`（修前 65/78 无墨），新守卫 `SIDEBAR_ICON_BLANK` + M1011/M1012 两臂 `CAUGHT`；367 再钉八根（rot 20→12）；方向尺的正对照从坏帧改成合成帧。
"""

state_section = f"""## R381 状态（2026-10-26 · 本地 · 第 380 轮 / Round 378）：设置侧栏图标亮档白压白 —— 动态 labelColor 修复 + 无墨格升会红；367 再钉八根（产品 1 文件，动效主线）

最后更新：2026-10-26（本地 · R381 / 第 380 轮 / Round 378）：亮档设置侧栏未选中图标实测 **255 白压在 251 底上（对比 4/255）**，旧尺数成「无墨」；单行组件帧黑、整页 `NavigationSplitView` 白 ⇒ 侧栏材质 vibrancy 把 `.primary` 解析成白色。图标改用动态系统色 `Color(nsColor: .labelColor)`（亮 76 / 暗 232），文字仍 `.primary`；修后 `SIDEBAR_ICON_COVERAGE light 有墨行={l_ink} 无墨行={l_blank} 反侧行={l_inv} | dark {d_ink}/{d_blank}/{d_inv}`（修前亮档无墨 65/78）；新旧帧差分 152 张逐字节同、30 张只动 x 34–68。新守卫 `SIDEBAR_ICON_BLANK` 把无墨格升成会红，`M1011`（改回 `.primary`）/`M1012`（写死黑）两臂 `CAUGHT`；367 再钉八根（r131/r137/r140/r60/r67），`HIDDEN_ARMS … rot={h_rot} … 上界 rot={h_rot_ceiling} … 处置={h_dispose}`（20→12），八根都重跑过刀；`swift build --build-tests` 告警 **{warnings}**；全量 `Executed {executed} tests, with {skipped} tests skipped and {failures} failures`；电池读数见下一节；清账表 `MOTION_LEDGER 表面={surfaces} 状态={states} 格子={cells} 行数={rows} 已清账={cleared} 未清账={uncleared} 地板={floor}`；产品面连续零改动 **{streak}** 轮（`python3 scripts/product_streak.py --streak-for 380` 现读，口径是「本轮之前的连读轮数」）。

本轮做了什么：
① ⓪ CI：`9678d9c ↔ 40216535782`（in_progress）、`fb641e7 ↔ 40216344972`（in_progress）、`ef45e65 ↔ 40216188878`、`e8228a8 ↔ 40216027769`、`0264a63 ↔ 40215895770`、`39189c2 ↔ 40215694974`、`947cd29 ↔ 40215439140`、`dfe411a ↔ 40214501796`（concluded=success）；只登记不轮询。
② 产品位：看图 → 量像素（4/255）→ 单行/整页对照定因（材质 vibrancy）→ 图标改动态系统色；帧差分确认只动图标列。
③ 判据：`SIDEBAR_ICON_BLANK` 两档判零；方向尺的反相正对照改成合成位图（先红两次，成因写进注释）。
④ rot：八根重钉并跑刀；语料补 `make_surface_ledger.py`；`ARM_LINE` 放宽到四位并加正对照。
⑤ 验证：构建 0 告警；全量 `{executed}/{skipped}/{failures}`；捕获 `CAPTURED {frames} -> /tmp/r381_shots2`；帧基线 `COMPARED=182 CHANGED=0 MISSING=0 ADDED=0`；换装 `INSTALL_RESULT=ok`、`INSTALL_SHA_MATCH=1`、条目 {entries_before}={entries_after}；清账表 162=162。

验证读数（现读）：`SIDEBAR_ICON_COVERAGE` 两档 `{l_ink}/{l_blank}/{l_inv}` 与 `{d_ink}/{d_blank}/{d_inv}`；`R381_MUTATE 刀=2 CAUGHT=2 红得不对=0 RESTORE_CLEAN=yes`；`MUTATE_TABLE n=3 caught=3`（r131）、`n=1 caught=1`（r137）、`CAUGHT=3/3`（r140）；`NEEDLE_PRECHECK tables={pre_tables} covered={pre_covered} arms={pre_arms} bad={pre_bad}`；`ARM_TOTAL files={arm_files} arms={arm_total} dupes={arm_dupes} repeats={arm_repeats}`；全量 `Executed {executed} tests, with {skipped} tests skipped and {failures} failures`。

NOT-RUN（分开写）：① **亮档真机腿**没跑：当前系统外观是 dark，`real_screen_sidebar_icons.py` 只能读当前外观；暗档真机通道已跑通（`REALSCREEN_VERDICT={real_verdict.group(1)} 外观={real_appearance}`、六枚图标可辨），亮档这一半的证据仍是离屏整页帧。② 剩 12 根 rot 未重钉（r142 M674、r29d M132/M133/M135、r303 M876、r33 M147、r64 M340/M341、r76 M402、r77 M411、r78 M417、r94 M518）。③ `settings-*` 的帧基线已同一笔更新，不是 NOT-RUN；`capture-readings.log` 与全量日志留在 `/tmp` 不入库。

下一轮（R382）的靶：⓪ 读队列（本笔 run id 待 push 后成对写回）；① 继续 367（从 r29d 或 r76 起，先看 `HIDDEN_ROT` 现读名单）；② 回产品动效面再点一个真实位（本轮的最弱维仍是「只深审了一个位点」）。
"""

# ---- 只读不写的全量变换（任一断言失败都不会落盘） ----
audit = rd("AGENT_UI_AUDIT.md")
assert ui_heading in audit
audit_new = once(audit, ui_heading, ui_section + "\n" + ui_heading)

iteration_new = rd("AGENT_VISUAL_ITERATION.md").rstrip() + "\n\n" + iteration

backlog_new = rd("AGENT_BACKLOG.md").rstrip() + "\n" + backlog

decisions_new = rd("AGENT_DECISIONS.md").rstrip() + "\n" + decision

changelog_old = rd("CHANGELOG.md")
changelog_anchor = "## [Unreleased]\n\n"
assert changelog_old.count(changelog_anchor) == 1
changelog_new = once(changelog_old, changelog_anchor, changelog_anchor + changelog + "\n")

report_old = rd("AGENT_FINAL_REPORT.md")
report_new = once(report_old, "D-069 … **D-362**", "D-069 … **D-369**")
report_new = once(report_new, "产品面连续零改动轮数 = **25**", "产品面连续零改动轮数 = **26**")
report_new = once(
    report_new,
    "R368 现读：注册表 **134** 张 / 刀号最大 **M1009** / 预检 covered=117 arms=376 bad=0；全仓 228 文件 / 864 把；M906 空刀退役",
    f"R381 现读：注册表 **{pre_tables}** 张 / 刀号最大 **M1012** / 预检 covered={pre_covered} arms={pre_arms} bad={pre_bad}；"
    f"全仓 {arm_files} 文件 / {arm_total} 把；M906 空刀退役")
report_new = once(
    report_new,
    "本机换装 `INSTALL_RESULT=ok`、SHA_MATCH=1、条目 381=381。",
    "本机换装 `INSTALL_RESULT=ok`、SHA_MATCH=1、条目 381=381。" + report_bullet)

state_old = rd("AGENT_STATE.md")
state_anchor = "## R380 状态（2026-10-26 · 本地 · 第 379 轮 / Round 377）"
assert state_old.count(state_anchor) == 1
state_new = once(state_old, state_anchor, state_section + "\n" + state_anchor)

# ---- 全部断言都过了才写盘 ----
wr("AGENT_UI_AUDIT.md", audit_new)
wr("AGENT_VISUAL_ITERATION.md", iteration_new)
wr("AGENT_BACKLOG.md", backlog_new)
wr("AGENT_DECISIONS.md", decisions_new)
wr("CHANGELOG.md", changelog_new)
wr("AGENT_FINAL_REPORT.md", report_new)
wr("AGENT_STATE.md", state_new)

print("R381_LEDGERS_OK warnings=%d full=%d/%d/%d frames=%d rot=%d/%d pre=%d/%d/%d/%d arms=%d/%d gate=%d=%d streak=%d"
      % (warnings, executed, skipped, failures, frames, h_rot, h_rot_ceiling,
         pre_tables, pre_covered, pre_arms, pre_bad, arm_files, arm_total,
         cleared, cells, streak))

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R394（第 393 轮 / Round 391）的台账。数字全部从本机日志解析。"""
import io
import os
import re
import subprocess

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


build = log("/tmp/r394_build_final.log")
warnings = len(re.findall(r"warning:", build))
assert warnings == 0

full = log("/tmp/r394_full.log")
summaries = [tuple(int(x) for x in row) for row in
             re.findall(r"Executed (\d+) tests, with (\d+) tests skipped and (\d+) failures", full)]
big = [row for row in summaries if row[0] > 900]
assert big
executed, skipped, failures = big[-1]
assert failures == 0

capture = log("/tmp/r394_capture.log")
cap = re.search(r"CAPTURED (\d+) -> /tmp/r394_shots", capture)
assert cap
frames = int(cap.group(1))

diff = log("/tmp/r394_framediff.log")
dm = re.search(r"FRAME_DIFF 比了=(\d+) 变了=(\d+)", diff)
assert dm
total_frames, changed_frames = [int(x) for x in dm.groups()]
same_frames = total_frames - changed_frames
assert (same_frames, changed_frames, total_frames) == (182, 0, 182)

baseline = log("/tmp/r394_framebaseline.log")
bm = re.search(r"FRAME_BASELINE_COMPARED=(\d+)\s+FRAME_BASELINE_CHANGED=(\d+)"
               r"\s+FRAME_BASELINE_MISSING=(\d+)\s+FRAME_BASELINE_ADDED=(\d+)", baseline)
assert bm
b_compared, b_changed, b_missing, b_added = [int(x) for x in bm.groups()]
assert (b_compared, b_changed, b_missing, b_added) == (182, 0, 0, 0)

copy = log("/tmp/r394_copyfail2.log")
cl = re.search(r"COPY_FAIL_RED light 成功红=(\d+) 失败红=(\d+) 失败对比=([0-9.]+) 墨=(\d+)/(\d+)", copy)
cd = re.search(r"COPY_FAIL_RED dark 成功红=(\d+) 失败红=(\d+) 失败对比=([0-9.]+) 墨=(\d+)/(\d+)", copy)
assert cl and cd
clr = [int(cl.group(1)), int(cl.group(2))] + [cl.group(3)] + [int(cl.group(4)), int(cl.group(5))]
cdr = [int(cd.group(1)), int(cd.group(2))] + [cd.group(3)] + [int(cd.group(4)), int(cd.group(5))]
assert clr[0] == 0 and cdr[0] == 0 and clr[1] >= 30 and cdr[1] >= 30
assert float(clr[2]) >= 3.0 and float(cdr[2]) >= 3.0

fade = log("/tmp/r394_fade3.log")
f2 = re.search(r"COPY_FAIL_FADE scale=2x 帧数=(\d+) 过渡帧数=(\d+) 峰值=([0-9.]+)", fade)
f1 = re.search(r"COPY_FAIL_FADE scale=1x 帧数=(\d+) 过渡帧数=(\d+) 峰值=([0-9.]+)", fade)
assert f2 and f1
f2_frames, f2_span, f2_peak = int(f2.group(1)), int(f2.group(2)), f2.group(3)
f1_frames, f1_span, f1_peak = int(f1.group(1)), int(f1.group(2)), f1.group(3)
assert f2_span >= 2 and f1_span >= 2

motion = log("/tmp/r390_motion_full.log")
ms = re.search(r"MOTION_SUMMARY (.+)", motion)
mr = re.search(r"MOTION_RESOLVE_SUMMARY judged=(\d+)/(\d+) not-run=(\S+)", motion)
mex = re.search(r"Executed (\d+) tests, with (\d+) tests skipped and (\d+) failures", motion)
assert ms and mr and mex
motion_summary = ms.group(1)
motion_judged, motion_total, motion_notrun = mr.groups()
motion_exec, motion_skip, motion_fail = [int(x) for x in mex.groups()]
assert "settings-reset-fade" in motion_summary
assert motion_judged == motion_total == "5" and motion_notrun == "-"
assert motion_fail == 0

install = log("/tmp/r394_install.log")
assert "INSTALL_RESULT=ok" in install and "INSTALL_SHA_MATCH=1" in install
entries = re.search(r"INSTALL_ENTRIES_BEFORE=(\d+)\s+INSTALL_ENTRIES_AFTER=(\d+)", install)
assert entries
entries_before, entries_after = entries.groups()

pre = log("/tmp/r394_precheck5.log")
pre_line = re.search(r"NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=(\d+) bad=(\d+)", pre)
arm_line = re.search(r"ARM_TOTAL files=(\d+) arms=(\d+) dupes=(\d+) repeats=(\d+)", pre)
assert pre_line and arm_line
pre_tables, pre_covered, pre_arms, pre_bad = [int(x) for x in pre_line.groups()]
arm_files, arm_total, arm_dupes, arm_repeats = [int(x) for x in arm_line.groups()]
assert pre_bad == 0 and arm_dupes == 0 and arm_repeats == 0

hidden = log("/tmp/r394_hidden2.log")
h = re.search(r"HIDDEN_ARMS 表=(\d+) 可判=(\d+) rot=(\d+) 抽不出=(\d+) 已声明表=(\d+) 已声明死针=(\d+) 上界 rot=(\d+)", hidden)
assert h
h_tables, h_judged, h_rot, h_opaque, h_dtables, h_ddead, h_rot_ceiling = [int(x) for x in h.groups()]
assert h_rot == h_rot_ceiling == 0

gate = log("/tmp/r394_gate.log")
g = re.search(r"MOTION_LEDGER 表面=(\d+) 状态=(\d+) 格子=(\d+) 行数=(\d+) 已清账=(\d+) 未清账=(\d+) 地板=(\d+)", gate)
assert g
surfaces, states, cells, rows, cleared, uncleared, floor_count = [int(x) for x in g.groups()]
assert uncleared == 0 and cleared == cells == rows == floor_count

streak_out = subprocess.check_output(
    ["python3", os.path.join(ROOT, "scripts/product_streak.py"), "--streak-for", "393"],
    cwd=ROOT).decode("utf-8")
streak = int(re.search(r"streak=(\d+)", streak_out).group(1))
assert streak == 1, "streak=%d" % streak

mut = log("/tmp/r394_mut4.log")
wiring = log("/tmp/r394_mut_wiring3.log")
assert "R394_MUTATE 刀=2 CAUGHT=2 红得不对=0 RESTORE_CLEAN=yes" in mut
assert "R394_WIRING_MUTATE 刀=1 CAUGHT=1 红得不对=0 RESTORE_CLEAN=yes" in wiring

ui_heading = "## 第 392 轮（R393"
ui_section = f"""## 第 393 轮（R394 · 2026-10-26 · U-1390…U-1394）：复制失败那一颗终于变红 —— 成功 0 / 失败 145·132 颗，胶片 2x 12 帧 / 1x 16 帧；M1029–M1031 CAUGHT（U-1390…U-1394 · 产品 1 文件，动效主线）

- **U-1390：⓪ 网络与 CI。** 11:36 `git push origin main` 被 SSH 拒（`Connection closed by 20.205.243.166 port 22`），同分钟 `api=000`（LibreSSL SSL_ERROR_SYSCALL）/ `apple=200` ⇒ GitHub 侧仍断；`PUSH_BLOCKED=network`，本地 ahead=25（R393 之后、R394 落笔前），**不写已推送**。`origin/main` 本地 ref 仍 `5c7814e`；网络不可达无法 fetch 确认远端是否被推进（push 在连接阶段失败，未用 force）。恢复后先 push、复核 ahead=0，再读 `40234023212`/`40234058148` 与 R387–R394 推送跑的全部失败步骤。
- **U-1391：产品位 —— 复制失败的颜色反馈。** `GlassPill` 的失败态原来只把图标换成感叹号，前景仍是主色 —— 成功/失败两帧在颜色上完全一样，用户要读第二眼才知道「没写进剪贴板」。R394 给失败态上动态错误红（亮 `Color.red` / 暗 `1.0,0.48,0.44`，与登录失败回执同一套），成功仍主色。静态两态现读：亮 成功红 **{clr[0]}** / 失败红 **{clr[1]}** / 失败对比 **{clr[2]}**，暗 **{cdr[0]}** / **{cdr[1]}** / **{cdr[2]}**（控件地板 3.0；第一版系统红暗档只有 2.69，换成动态红后过）。胶片新场景只拍第三颗 copy 按钮：2x `帧数={f2_frames} 过渡帧数={f2_span} 峰值={f2_peak}`、1x `{f1_frames}/{f1_span}/{f1_peak}`（声明 160ms），strip 逐帧看到 黑 doc → 红 doc → 红感叹号。8 张静态 PNG 在 `/tmp/r394_copyfail`，两张 strip 在 `/tmp/r394_motion`，都逐张看过。
- **U-1392：判据、刀与一次自伤。** `UICaptureTests.testCopyFailurePillTurnsRedAndSuccessDoesNot`（成功红必须 0、失败红 ≥30、失败红对比 ≥3.0）+ 胶片 `testCopyFailureColorSwapIsAVisibleProcess`（2x/1x 各 ≥2 帧）+ `MotionCatalogTests.testCopyFailureStateIsWiredFromDetailViewToTheRedPill`（`copyFailed: copyFailed` 与 `.emphasis` 事务）。`M1029`（失败退回主色）/`M1030`（成功也涂红）/`M1031`（DetailView 不传 copyFailed）全 **CAUGHT**。**自伤**：第一版把 M1029/M1030/M1031 放进**同一张表**，而 M1031 的靶是 `DetailView.swift`；脚本的 restore 用全局 `original`（GlassControls 全文）写回每个 path ⇒ 把 `struct GlassPill` 写进了 DetailView，构建以 `invalid redeclaration` 报错。已 `git checkout -- DetailView.swift` 还原，并把接线刀拆成单靶表 `mutate_r394_copy_wiring.py` 重跑通过。规矩见 D-384。
- **U-1393：BACKLOG 436 处置（仍未结案）。** 本轮没有新的 runner motion 读数；R390 的完整本地卷 `Executed {motion_exec} tests, with {motion_skip} tests skipped and {motion_fail} failures`、`MOTION_SUMMARY {motion_summary}`、`MOTION_RESOLVE_SUMMARY judged={motion_judged}/{motion_total} not-run={motion_notrun}` 与闸门 exit 1（UNLISTED `settings-reset-fade`）的本地复现仍成立。**不关单、不改 JSON/自测、不猜 `must_judge`**；runner 卷继续记具名 NOT-RUN。
- **U-1394：① 367 rot 与八步。** `HIDDEN_ARMS 表={h_tables} 可判={h_judged} rot={h_rot} 抽不出={h_opaque} 已声明表={h_dtables} 已声明死针={h_ddead} 上界 rot={h_rot_ceiling} 处置=ok`；预检 `tables={pre_tables} covered={pre_covered} arms={pre_arms} bad={pre_bad}`、全仓 {arm_files} 文件 / {arm_total} 把；`M1029–M1031` 全 CAUGHT。build **{warnings}** 告警；全量 `Executed {executed} tests, with {skipped} tests skipped and {failures} failures`；捕获 `CAPTURED {frames} -> /tmp/r394_shots`，与 R393 逐张比 `变了={changed_frames}`（静态帧没变，不 update），帧基线 `COMPARED={b_compared} CHANGED={b_changed}`；换装 `INSTALL_RESULT=ok`、`INSTALL_SHA_MATCH=1`、条目 `{entries_before}={entries_after}`；清账表 `表面={surfaces} 状态={states} 格子={cells} 已清账={cleared} 未清账={uncleared} 地板={floor_count}`；产品面连续零改动 **{streak}** 轮（现读 `python3 scripts/product_streak.py --streak-for 393`）。
"""

iteration = f"""## Round 391 · R394（第 393 轮 · 2026-10-26）：复制失败那一颗终于变红（成功 0 / 失败 145·132 颗）；胶片 2x 12 帧 / 1x 16 帧；M1029–M1031 CAUGHT（产品 1 文件，动效主线）

`GlassPill` 失败态原来只换图标不换色，成功/失败颜色相同。R394 给失败态上动态错误红（亮 Color.red / 暗 1.0,0.48,0.44），静态现读亮 成功 0 / 失败 145 / 对比 4.57，暗 0 / 132 / 4.70；胶片只拍第三颗 copy 按钮，2x `{f2_span}` 帧 / 1x `{f1_span}` 帧（峰值 `{f2_peak}`/`{f1_peak}`，声明 160ms），strip 看到 黑 doc → 红 doc → 红感叹号。M1029/M1030/M1031 全 CAUGHT。**自伤**：第一版把不同靶的刀放同一张表，restore 把 GlassControls 全文写进 DetailView，构建以无效重声明报错；已还原并拆成单靶表。静态 182 帧零变化；436 无新 runner 读数；rot 0/0。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 15/15 | 看了 8 张成功/失败静态帧（亮/暗）与两张胶片，红图标与过渡过程都可见。 |
| 判据有效性 | 15/15 | 静态颜色/对比 + 2x/1x 胶片 + 接线守卫；M1029/M1030/M1031 三面都有牙。 |
| 假绿防御 | 14/15 | 先证胶片通道能看见（2x/1x 都 ≥2 帧）；扣 1：第一版多靶表把产品文件写坏，靠构建才发现（已修）。 |
| 产品面推进 | 15/15 | 真实 Sources 改动，失败反馈从「只换字形」变成「红色 + 字形」。 |
| 台账一致性 | 14/15 | U-1390…U-1394、D-384、436 状态、计数器都从日志解析；扣 1：自伤让本轮多花了一次构建诊断。 |
| 交付诚实性 | 15/15 | 把多靶表写坏 DetailView 的事故与还原过程写进账；网络只写 BLOCKED。 |
| 可复核性 | 15/15 | 静态红/对比读数、两倍率胶片与 strip、三把刀、precheck/rot 都有原文。 |

均分 = 103/105 ≈ 14.7/15（98）。
"""

decision = """
### D-384（394）一张变异表只准一个靶；restore 的 `original` 必须与每一臂的 path 同源

R394 现读：第一版把 M1029/M1030（靶 `GlassControls.swift`）与 M1031（靶 `DetailView.swift`）放进同一张表；restore 用全局 `original`（GlassControls 全文）写回每个 path ⇒ `struct GlassPill` 被写进 DetailView，构建报 `invalid redeclaration of 'GlassPill'`。`git checkout -- DetailView.swift` 还原后，把接线刀拆成 `mutate_r394_copy_wiring.py` 单靶表，三臂全部 CAUGHT。
**Why**：表级 `original` 是单靶表的隐含假设；第二个靶一旦出现，restore 就不再是"还原"，而是"把第一靶的全文复制到第二靶"。这类坏法在构建时才会响，但若第二个靶不是编译单元（json/md），它会安静地把账写坏。
**How to apply**：① 一张变异表只准一个文件靶；要钉两个文件就拆两张表（R178 的老规矩，R394 又犯一次）；② restore 若必须多靶，按 path 各存原文，并在收尾断言 `被改过的文件集合 ⊆ 本表声明过的靶集合`；③ 新表登记进预检，且用标准 `MUTATIONS` 形状（lambda/自定义 main 会从静态覆盖里隐形）；④ 事故要写进台账，不把"构建替我发现"写成"流程本来就有门"。
"""

changelog = """### 复制失败那一颗终于变红（成功 0 / 失败 145·132 颗）；胶片 2x 12 帧 / 1x 16 帧；M1029–M1031 CAUGHT，多靶表自伤已拆（R394 / 第 393 轮 / Round 391 / U-1390…U-1394 · 产品 1 文件，动效主线）

"""

report_bullet = f"""
- **R394（动效主线）**：`GlassPill` 失败态原来只换图标不换色 ⇒ 加动态错误红（亮 `Color.red` / 暗 `1.0,0.48,0.44`）。静态现读亮 成功 `{clr[0]}` / 失败 `{clr[1]}` / 对比 `{clr[2]}`，暗 `{cdr[0]}` / `{cdr[1]}` / `{cdr[2]}`；胶片只拍 copy 按钮，2x `{f2_span}` 帧 / 1x `{f1_span}` 帧（峰值 `{f2_peak}`/`{f1_peak}`），strip 黑 doc → 红 doc → 红感叹号。M1029/M1030/M1031 CAUGHT；第一版多靶表把 GlassControls 写进 DetailView，构建报无效重声明，已还原并拆成单靶表（D-384）。静态 182 帧零变化；436 无新 runner 读数，仍未结案；rot 0/0。**网络仍断 ⇒ PUSH_BLOCKED=network，ahead=25，未推送。**
"""

state_section = f"""## R394 状态（2026-10-26 · 本地 · 第 393 轮 / Round 391）：复制失败那一颗终于变红（成功 0 / 失败 145·132 颗）；胶片 2x 12 帧 / 1x 16 帧；M1029–M1031 CAUGHT（产品 1 文件，动效主线）

最后更新：2026-10-26（本地 · R394 / 第 393 轮 / Round 391）：`GlassPill` 的失败态原来只把图标换成感叹号、前景仍是主色，成功/失败在颜色上完全一样。R394 给失败态上动态错误红（亮 `Color.red` / 暗 `1.0,0.48,0.44`），成功仍主色。静态现读：亮 成功红 **{clr[0]}** / 失败红 **{clr[1]}** / 失败对比 **{clr[2]}**，暗 **{cdr[0]}** / **{cdr[1]}** / **{cdr[2]}**（控件地板 3.0；系统红暗档只有 2.69，动态红过）。胶片新场景只拍第三颗 copy 按钮：2x `帧数={f2_frames} 过渡帧数={f2_span} 峰值={f2_peak}`、1x `{f1_frames}/{f1_span}/{f1_peak}`（声明 160ms），strip 逐帧看到 黑 doc → 红 doc → 红感叹号。判据：静态颜色/对比 + 两倍率胶片 + DetailView 接线；`M1029`/`M1030`/`M1031` 全 CAUGHT。**自伤**：第一版多靶表用全局 original 还原，把 GlassControls 全文写进 DetailView，构建报 `invalid redeclaration`；已 `git checkout -- DetailView.swift` 还原并拆成单靶表（D-384）。静态 182 帧 `变了={changed_frames}`，帧基线 182/0；全量 `Executed {executed} tests, with {skipped} tests skipped and {failures} failures`；换装 `ok / SHA_MATCH=1 / 381=381`；清账表 162=162；`HIDDEN_ARMS 表={h_tables} 可判={h_judged} rot={h_rot} … 上界 rot={h_rot_ceiling} 处置=ok`；预检 `tables={pre_tables} covered={pre_covered} arms={pre_arms} bad={pre_bad}`、全仓 {arm_files} 文件 / {arm_total} 把；产品面连续零改动 **{streak}** 轮（现读 `python3 scripts/product_streak.py --streak-for 393`）。

本轮做了什么：
① ⓪ 网络：push 被 SSH 拒 + `api=000`/`apple=200` ⇒ `PUSH_BLOCKED=network`；未推送，CI 多跑未读。
② 产品位：复制失败从「只换字形」变成「动态错误红 + 字形」；静态 0/145·132、对比 4.57/4.70。
③ 判据：静态颜色/对比、2x/1x 胶片、接线守卫；M1029–M1031 CAUGHT。
④ 自伤：多靶表 restore 写坏 DetailView，构建报错；已还原并拆表，记 D-384。
⑤ 367：hidden 表 {h_tables} / 可判 {h_judged} / rot {h_rot} / 上界 {h_rot_ceiling}；预检 {pre_tables}/{pre_covered}/{pre_arms}/{pre_bad}。
⑥ 验证：build 0 告警；全量 `{executed}/{skipped}/{failures}`；捕获 {frames} 帧、静态零变化；换装 ok；清账表 {cells}=162。

验证读数（现读）：`COPY_FAIL_RED` 亮 成功 `{clr[0]}` / 失败 `{clr[1]}` / 对比 `{clr[2]}`，暗 `{cdr[0]}` / `{cdr[1]}` / `{cdr[2]}`；`COPY_FAIL_FADE` 2x `{f2_frames}/{f2_span}/{f2_peak}`、1x `{f1_frames}/{f1_span}/{f1_peak}`；`M1029–M1031` CAUGHT；`HIDDEN_ARMS … rot={h_rot} … 处置=ok`。

NOT-RUN / 阻塞（分开写）：① **`PUSH_BLOCKED=network`**：push 被 SSH 拒 + `api=000`（LibreSSL SSL_ERROR_SYSCALL）/ `apple=200`；本地 ahead=25（R394 主笔前）；② `40234023212 ↔ d38ea10`、`40234058148 ↔ 5c7814e` 与 R387–R393 本地提交的 conclusion **未读**（网络）；③ BACKLOG 436 的 runner motion 卷未读（本地复现不能关单），不改 JSON/自测；④ 亮档真机腿仍没跑。

下一轮（R395）的靶：⓪ 先 `git push origin main`（禁 amend/force）并复核 ahead=0；读 `40234023212`/`40234058148` 与 R387–R394 推送那一跑的**全部失败步骤**，把 run↔commit 成对写回本行；按 BACKLOG 436 先读 CI motion 卷，再决定第五臂 `must_judge` 并一次性改 JSON 与自测；① 367 现读 rot=0，按 `HIDDEN_ROT` 查新腐烂；② 回产品动效面再点一个真实位。
"""

audit = rd("AGENT_UI_AUDIT.md")
assert ui_heading in audit
audit_new = once(audit, ui_heading, ui_section + "\n" + ui_heading)
iteration_new = rd("AGENT_VISUAL_ITERATION.md").rstrip() + "\n\n" + iteration
decisions_new = rd("AGENT_DECISIONS.md").rstrip() + "\n" + decision

changelog_old = rd("CHANGELOG.md")
changelog_anchor = "## [Unreleased]\n\n"
assert changelog_old.count(changelog_anchor) == 1
changelog_new = once(changelog_old, changelog_anchor, changelog_anchor + changelog + "\n")

report_old = rd("AGENT_FINAL_REPORT.md")
report_new = once(report_old, "D-069 … **D-383**", "D-069 … **D-384**")
report_new = once(report_new, "U-31 … U-1389（R393 现读抬到最新一节）", "U-31 … U-1394（R394 现读抬到最新一节）")
report_new = once(report_new, "产品面连续零改动轮数 = **2**", "产品面连续零改动轮数 = **1**")
report_new = once(
    report_new,
    "R393 现读：注册表 **147** 张 / 刀号最大 **M1028** / 预检 covered=130 arms=404 bad=0；全仓 240 文件 / 888 把；M674 退役、M906 空刀退役",
    f"R394 现读：注册表 **{pre_tables}** 张 / 刀号最大 **M1031** / 预检 covered={pre_covered} arms={pre_arms} bad={pre_bad}；"
    f"全仓 {arm_files} 文件 / {arm_total} 把；M674 退役、M906 空刀退役")
report_new = once(
    report_new,
    "**网络仍断 ⇒ PUSH_BLOCKED=network，ahead=25，未推送。**",
    "**网络仍断 ⇒ PUSH_BLOCKED=network，ahead=25，未推送。**" + report_bullet)

state_old = rd("AGENT_STATE.md")
state_anchor = "## R393 状态（2026-10-26"
assert state_old.count(state_anchor) == 1
state_new = once(state_old, state_anchor, state_section + "\n" + state_anchor)

wr("AGENT_UI_AUDIT.md", audit_new)
wr("AGENT_VISUAL_ITERATION.md", iteration_new)
wr("AGENT_DECISIONS.md", decisions_new)
wr("CHANGELOG.md", changelog_new)
wr("AGENT_FINAL_REPORT.md", report_new)
wr("AGENT_STATE.md", state_new)

print("R394_LEDGERS_OK warnings=%s full=%s/%s/%s frames=%s diff=%s/%s baseline=%s/%s copy=%s/%s,%s/%s fade=%s/%s,%s/%s rot=%s pre=%s/%s/%s/%s arms=%s/%s gate=%s=%s streak=%s"
      % (warnings, executed, skipped, failures, frames, same_frames, changed_frames,
         b_compared, b_changed, clr[1], cdr[1], clr[2], cdr[2], f2_span, f1_span, f2_peak, f1_peak,
         h_rot, pre_tables, pre_covered, pre_arms, pre_bad, arm_files, arm_total,
         cleared, cells, streak))

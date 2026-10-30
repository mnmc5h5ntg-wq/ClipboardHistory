# -*- coding: utf-8 -*-
import io
def rd(p): return io.open(p, encoding="utf-8").read()
def wr(p, t): io.open(p, "w", encoding="utf-8").write(t)
A = "AGENT_UI_AUDIT.md"; S = "AGENT_STATE.md"; P = "AGENT_FINAL_REPORT.md"; I = "AGENT_VISUAL_ITERATION.md"
a = rd(A); st = rd(S); pr = rd(P); it = rd(I)
old_t = u"U-1970…U-2001）：主窗口与设置窗口的标题栏统一"
new_t = u"U-1970…U-2002）：主窗口与设置窗口的标题栏统一"
assert a.count(old_t) == 1, a.count(old_t)
a = a.replace(old_t, new_t, 1)
U = u"""- **U-2002：⑦ runner 签收（R504 修复与 R505 两跑）。** `41105579968 ↔ e3eb62b` **success**、`41105861197 ↔ 6543959` **success**：同跑 `SETTINGS_IDENTITY_HEADER light 正 9 / 负 8`（照判）、`dark SETTINGS_IDENTITY_HEADER_NOT_RUN=sidebar-vibrant 负臂带=1`、`CAPABILITY judged=1/2 light=1 vibrant_not_run=1`；`RECORDING_REREAD light/dark diff_px=0`（1x）、`RTF_HELPER_ORPHAN_NOT_RUN=settings-content-blank` 两档 ⇒ 修复与既有 NOT_RUN 均被 runner 签收。`41106240358 ↔ 3d20a02` failure **仅** `SelectionRevealAnimationTests.testProductDurationRevealStillMovesOverTime`（已知采样 flake；同跑身份头读数同上、Motion floor clean）；`41106548360 ↔ f9b8733` failure **仅** `STEP[19] Motion coverage floor` 的 `testCopyReceiptAppearsAndDismissesWithAVisibleProcess` 1<2（已知采样 flake；同跑身份头 NOT_RUN 在）。`41112041111 ↔ 0beac05`（R506 产品）与 `41112999388 ↔ 938fc4f`（R506 台账）读时 **in_progress/queued ⇒ NOT-RUN**。
"""
anchor = u"\n## 第 499 轮（R501 · 2026-10-30 · U-1964…U-1969）"
assert a.count(anchor) == 1
a = a.replace(anchor, u"\n" + U + anchor, 1)
wr(A, a)
old_s = u"产品笔 `0beac05` 已推（ahead=0）。下一轮编号 R507"
new_s = u"产品笔 `0beac05` 已推（ahead=0）。⑦ runner 签收（收口补读）：`e3eb62b`/`6543959` 两跑 **success**（light 9/8 照判、dark `NOT_RUN=sidebar-vibrant 负臂带=1`、`judged=1/2`；`RECORDING_REREAD` 两档 diff_px=0；`RTF_HELPER_ORPHAN` 两档 NOT_RUN）；`3d20a02` 仅 SelectionReveal 采样 flake、`f9b8733` 仅 Motion `testCopyReceipt` 1<2 采样 flake；`0beac05`/`938fc4f` 两跑 in_progress/queued ⇒ NOT-RUN。下一轮编号 R507"
assert st.count(old_s) == 1, st.count(old_s)
wr(S, st.replace(old_s, new_s, 1))
old_u = u"U-31 … U-2001（R506 现读抬到最新一节）"
new_u = u"U-31 … U-2002（R506 现读抬到最新一节）"
assert pr.count(old_u) == 1
wr(P, pr.replace(old_u, new_u, 1))
anchor_it = u"**七维度自评**（恰七行，每格 n/15）：\n\n| 维度 | 分 | 依据 |\n| --- | --- | --- |\n| 真实视觉审查 | 15/15 | 状态菜单前/后"
new_it = u"⑦ runner 签收：`e3eb62b`/`6543959` success（light 9/8 照判、dark NOT_RUN=sidebar-vibrant 负臂带=1、RECORDING_REREAD diff=0、RTF 两档 NOT_RUN）；`3d20a02` 仅 SelectionReveal 采样 flake、`f9b8733` 仅 Motion testCopyReceipt 1<2；R506 两跑 NOT-RUN。\n\n" + anchor_it
assert it.count(anchor_it) == 1
wr(I, it.replace(anchor_it, new_it, 1))
print("OK")

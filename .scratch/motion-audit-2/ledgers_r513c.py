# -*- coding: utf-8 -*-
import io
def rd(p): return io.open(p, encoding="utf-8").read()
def wr(p, t): io.open(p, "w", encoding="utf-8").write(t)
A = "AGENT_UI_AUDIT.md"; S = "AGENT_STATE.md"; P = "AGENT_FINAL_REPORT.md"; I = "AGENT_VISUAL_ITERATION.md"
a = rd(A); st = rd(S); pr = rd(P); it = rd(I)
old_t = u"U-1970…U-2049）：主窗口与设置窗口的标题栏统一"
new_t = u"U-1970…U-2050）：主窗口与设置窗口的标题栏统一"
assert a.count(old_t) == 1, a.count(old_t)
a = a.replace(old_t, new_t, 1)
U = u"""- **U-2050：⑦ 收口补读与新跑登记。** `41160962238 ↔ 8c425f6`（产品笔）读时 **in_progress ⇒ NOT-RUN**；`41161522135 ↔ b29c616`（台账笔）**queued ⇒ NOT-RUN**；`41156774387 ↔ 7ff22a0` 读时 in_progress ⇒ NOT-RUN，收口时已 completed=**failure**（全部失败步骤未读，交 R514 ⓪）；`41156931203 ↔ 874d579` **success**、`41157084122 ↔ 764ea4b` **success**（R512 台账/签收笔不回归）。电池首跑 2 红的夹具样词（`disabled` 被本笔产品合法写进该文件）已重锚为 `Effect` 并复跑 **683/OK skipped=5**。
"""
anchor = u"\n## 第 499 轮（R501 · 2026-10-30 · U-1964…U-1969）"
assert a.count(anchor) == 1
a = a.replace(anchor, u"\n" + U + anchor, 1)
wr(A, a)
old_s = u"产品笔 `8c425f6` 已推（ahead=0）。下一轮编号 R514"
new_s = u"产品笔 `8c425f6` 已推（ahead=0）。⑦ 收口补读：`41160962238 ↔ 8c425f6` 读时 **in_progress ⇒ NOT-RUN**；`41161522135 ↔ b29c616`（台账笔）**queued ⇒ NOT-RUN**；`41156774387 ↔ 7ff22a0` 读时 in_progress ⇒ NOT-RUN，收口时已 completed=**failure**（全部失败步骤未读）；`41156931203 ↔ 874d579` **success**、`41157084122 ↔ 764ea4b` **success**。下一轮编号 R514"
assert st.count(old_s) == 1, st.count(old_s)
st = st.replace(old_s, new_s, 1)
old_n = u"读 `8c425f6` 自身跑与 `7ff22a0`/`874d579`/`764ea4b` 跑全部失败步骤"
new_n = u"读 `41160962238 ↔ 8c425f6`、`41161522135 ↔ b29c616`、`41156774387 ↔ 7ff22a0` 三跑全部失败步骤（`41156774387` 收口时 failure、步骤未读）"
assert st.count(old_n) == 1, st.count(old_n)
st = st.replace(old_n, new_n, 1)
wr(S, st)
old_u = u"U-31 … U-2049（R513 现读抬到最新一节）"
new_u = u"U-31 … U-2050（R513 现读抬到最新一节）"
assert pr.count(old_u) == 1
wr(P, pr.replace(old_u, new_u, 1))
anchor_it = u"**七维度自评**（恰七行，每格 n/15）：\n\n| 维度 | 分 | 依据 |\n| --- | --- | --- |\n| 真实视觉审查 | 15/15 | 普通/固定两臂"
new_it = u"⑦ 收口补读：`41160962238 ↔ 8c425f6` in_progress ⇒ NOT-RUN、`41161522135 ↔ b29c616` queued ⇒ NOT-RUN；`41156774387 ↔ 7ff22a0` 收口时 failure 但失败步骤未读（交 R514 ⓪）；`41156931203 ↔ 874d579`/`41157084122 ↔ 764ea4b` success。电池首跑 2 红的夹具样词重锚后复跑 683/OK skipped=5。\n\n" + anchor_it
assert it.count(anchor_it) == 1, it.count(anchor_it)
wr(I, it.replace(anchor_it, new_it, 1))
print("OK")

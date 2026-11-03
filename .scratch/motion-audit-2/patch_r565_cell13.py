#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R565 补段 ⑬：占位符那 1 处的选择与理由、三处「未收口」对齐、640 的代价、D-565 ④ 仍欠。

（另把 R566 读单 (i) 那一格写成"第一格·写死"，并禁止拿 `frame_baseline.py update` 当收尾。）
"""
import io

P = 'AGENT_STATE.md'
CELL = '''⑬ **补段的三格补账（占位符那 1 处选了「改散文」；三处「未收口」对齐；D-565 ④ 那一尺仍然欠着）**：ⓐ 占位符：既往口径是 0，本段现读 1 ⇒ 取**出路 (i) 改账的散文**（U-2447 里那句判法原本写作"等号后面紧跟一个反引号包住的格式槽位"，那个形状本身就是被描述的对象，不是漏替换的模板），**不给尺加例外** —— 出路 (ii)（临时放一个真没替换的占位符去证明那把尺抓得住、再具名"无刀、靠活门"）本轮没做，理由：改完散文这一格就不需要新刀，而"我有没有验证过这把尺抓得住真漏替换"这件事**仍然没被验证过**，它记在下面第 ⓔ 格一起欠着。改完复跑逐节现读：**本轮各节 percent 后接字母 = 0**（STATE 三节 / UI_AUDIT 第 564 轮 / ITERATION Round 562 / CHANGELOG 两条 R565 条目 / DECISIONS D-565 / FINAL_REPORT 两笔 / BACKLOG 639+640）。ⓑ 为什么选 (i)：把散文换个写法就能让"0"这个数说回它原本的意思（"没有漏替换"）；给尺开一个"允许形状引用"的口子，下一轮真漏替换时就藏在合法引用里 —— 那是把门的对象改宽，不是把数改对。ⓒ **640 的代价写死**：基线不更新 ⇒ 下一次产品改动**暂时没有像素证人**，这是明知故取的；R566 第一格已钉（重拍现读，同批 138 ⇒ 先分辨再决定动不动；拍到 0 ⇒ 那条"渲染状态漂移"具名结案）。ⓓ **三处「未收口」对齐**：本顶节这一格、`### R565 补记` ⑨/⑫、项目记忆索引 R565 那一行，三处同组证据 —— `git rev-list --count origin/main..HEAD` 现读 = 6（写这一格时；本笔自己那一笔会再 +1 ⇒ 不回头改这里的数）、远端 main = `c567879`、`github.com` 探测 = `000`（curl 退出码 28）而 `api.github.com` = `200` ⇒ `PUSH_BLOCKED=dns-github-unresolvable`。若这三处里任何一处日后自己写成「已收口」，按**第五处同轮互斥**登记成自伤并当场改齐。ⓔ **仍然欠着的两格**（具名，不装作已做）：D-565 ④ 那条"同一轮里跨节对账"的尺本轮**没落** —— 监工给的第 ⑤ 格；以及上面 ⓐ 说的"占位符尺的正对照"。两条都需要新守卫 + 各自的刀才能算推进，而这一半已经跑了三次 swift 卷（判据卷两卷 + 全量一卷），再塞一条只写完一半的守卫会造出一个**没有刀证人的门** ⇒ 宁可挂着。

'''

t = io.open(P, encoding='utf-8').read()
anchor = '## R565 ⓪ 开工（2026-11-03'
assert t.count(anchor) == 1, t.count(anchor)
assert '⑬ **补段的三格补账' not in t
t = t.replace(anchor, CELL + anchor, 1)

old_g = '  (i) **640 的帧漂移**：现读 `FRAME_BASELINE_COMPARED=356 CHANGED=138 not-updated`'
assert t.count(old_g) == 1, t.count(old_g)
t = t.replace(old_g, '  (i) **640 的帧漂移（R566 第一格，写死）**：现读 `FRAME_BASELINE_COMPARED=356 CHANGED=138 not-updated`', 1)

old_i = '若拍到 0，就把那条"渲染状态漂移"具名结案。'
assert t.count(old_i) == 1, t.count(old_i)
t = t.replace(old_i, '若拍到 0，就把那条"渲染状态漂移"具名结案。代价已经写在账里：基线不更新 ⇒ 下一次产品改动**暂时没有像素证人**，这是明知故取的，**不许拿 `frame_baseline.py update` 当收尾**。', 1)

io.open(P, 'w', encoding='utf-8').write(t)
print('CELL13_AND_640_COST_OK')

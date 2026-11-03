#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R565 ⑭：push 实际落地了 —— 把「未收口」按时序改齐（不是互斥，是两条时间不同的真数）。"""
import io

P = 'AGENT_STATE.md'
CELL = '''⑭ **本批已推齐（`github.com` 解析恢复之后的一次 push 成功）**：`git push` 输出 `6a3542b..e391ddb main -> main` ⇒ `HEAD=origin/main=e391ddb`、`git rev-list --count refs/remotes/origin/main..HEAD` = **0**。成对号现读：`41689665625 ↔ e391ddb`，取号时 **in_progress（conclusion 空串）⇒ 这一跑的读数属「复核未到」**，不许读成绿也不许读成红（它要回答的是：STEP[9] 有没有因补正笔转绿、`HINT_CONTRAST` 在 runner 走哪条、卫生守卫第一次进 CI 的结果）。
- **⑨/⑬/⑪ⓓ 里写的「未收口 / ahead=6 / PUSH_BLOCKED」不是错账，是写它那一刻的现读**（当时 `dscacheutil github.com` 为空、curl=000，三次尝试都失败）。本格只补一条时序：**DNS 恢复后一次 push 就落地了**，所以 R565 的**推送这一格已闭合**；仍未闭合的是那一跑的读数与 639/640 的归用户定向。这一条不构成"自写已收口解除闸门"（九十四/九十六）—— 闸门由用户/监工解，我只报数。
- **电池两次红的成因是并发争用，不是判据红**（照实记，算自伤不算缺陷）：`/tmp/r565-补-battery4.log`、`-battery5.log` 各 808s / 807s，红在 `test_install_local` 两条 `subprocess.TimeoutExpired(180)` + `test_skip_roster` 的借红（634 的观察者按设计拒绝给结论）；单独重跑那两条 **1.405s OK**，`test_launch_smoke + test_install_local` 合跑 **6.2s OK**，而最终**独占一卷**干净重跑 ⇒ `Ran 719 tests in 155.469s / OK (skipped=5)`、退出码 0（`/tmp/r565-补-battery6.log`，就是记账的这一笔）。**成因是我在电池在跑的时候同时起了别的东西**（预检/诊断/另一卷电池），把这些沙箱装机的时间挤过 180s —— 老规矩"预检与 swift 卷并行必撞锁"本轮以另一种形式又收了一次学费：**python 电池也怕并发**，因为它自己会 spawn 带超时的子进程。
- 换装仍然是 `SKIP_INSTALL=no-product-change`；帧基线仍然是 `FRAME_BASELINE_DRIFT=138/356 not-updated`（640）；`HINT_CONTRAST` 的 runner 红仍然原样留着，等 639 的定向。

'''

t = io.open(P, encoding='utf-8').read()
anchor = '## R565 ⓪ 开工（2026-11-03'
assert t.count(anchor) == 1, t.count(anchor)
assert '⑭ **本批已推齐' not in t
io.open(P, 'w', encoding='utf-8').write(t.replace(anchor, CELL + anchor, 1))
print('CELL14_ADDED')

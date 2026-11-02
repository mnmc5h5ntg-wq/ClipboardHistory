# -*- coding: utf-8 -*-
import io

P = 'AGENT_STATE.md'
s = io.open(P, encoding='utf-8').read()

anchor = u'## R555 状态（2026-11-02 · 第 554 轮 / Round 552 · 产品 3 文件 + 判据 2 文件 + 四把刀）'
assert s.count(anchor) == 1, s.count(anchor)

body = u"""## R556 ⓪ 开工（2026-11-02 · 第 555 轮 / Round 553 · CI 读单 + 基线全现读）

> 本节是**开工节**，不是轮次节（标题刻意不写「状态」两字 —— `product_streak.py` 按第一个 `## Rnnn 状态（` 认当前轮，本轮的 streak 格要到收口那笔才存在）。

**前置实读**：`git log --oneline -3` = `de58ab0` / `78e7ab5` / `c44649b`；已跟踪改动 **0**；`git rev-list --count origin/main..HEAD` = **0**（HEAD=origin=`de58ab0`）。

**① CI 读单（只登记、不轮询；in_progress/queued 一律 NOT-RUN，不算成功；已 concluded 的不重取）**
- `41439930389 ↔ 78e7ab5`（R555 台账笔）状态 **in_progress** ⇒ **NOT-RUN**。这一跑是「STEP[9] 修好之后到底绿没绿」的那一格读数 —— **现在还没读到**，所以 R555 那句"已按 616 的退场条件修尺"**只有本机 M1439 CAUGHT 作证，runner 侧仍挂未读**，不许在本轮写成「STEP[9] 已绿」。
- `41440039381 ↔ de58ab0`（R555 补记笔）状态 **in_progress** ⇒ **NOT-RUN**（同 workflow 前面还有 1 跑，队列在排队）。
- `41431129208 ↔ 5a943e7`（R555 刀表笔）concluded=failure，R555 收口前已逐条读过：失败步骤 = **STEP[9] Release script tests** + **STEP[18] On-screen probe coverage floor**（STEP[10]–[14] 是 STEP[9] 失败的下游 skipped）；**STEP[15]/[17] 绿由该步自己的结论行作证 = `CAPTURE_GATE_RESULT=ok 红=0`**。本轮不重取。
- **新读 `41391601922 ↔ 57974ec`（R554 补记笔，此前从未进过任何读单）**：concluded=**failure**，全部失败步骤 = **STEP[15] Swift tests (executed-count gate)** + **STEP[17] Capture gate (unregistered reds must be zero)**（两朵，无 [18]/[19]）。红名现读（emit 通道 `ASSERTION_RED` 行=4 去重后=2）：`UICaptureTests/testQuickPickFavoriteStarIsAtLeastEightPointsTall` light **7.0pt** / dark **6.0pt**，且失败文案是**旧措辞**「还是 9pt 小星，1x 上只剩几粒」⇒ 这一跑在 R555 的口径改动之前，与 `2c4b1ef`/`abc21c6`/`52f114c`/`75468be`/`570042c` 五跑逐字同形。
- **红名单对照（七跑）**：`2c4b1ef`、`abc21c6`、`52f114c`、`75468be`、`570042c`、`57974ec` 六跑都带同一朵收藏星红；只有 `5a943e7`（R555 代码笔）那一朵没了 —— 这就是 569 的签收形状：**不是"少判了一格"，而是判据换了口径且该步自己打了 `红=0`**。本轮起 569 不重开，只保留「1x dark 整行=6 恰在界上、余量 0」那一格监控。
- 这批日志的步骤名仍可解析（`steps` 打出真名），但**读数一律走判据自己 emit 的串**，不按步骤名过滤 —— 上一轮实测过 `UNKNOWN STEP` 会让按步骤名过滤恒 0 行。

**② 基线（本轮全部现读，不抄上一轮）**：帧 **354**（`docs/frame_baseline.json` 的 `count` 现读）；清账 **162/63/0**（`格=162 声明=63 不成立=0/63`）；streak **1**（`python3 scripts/product_streak.py --streak-for 555` 现读，last=`6b70474`/554）—— **与发令里的账面参考值差在口径**：账面抄的是 as-of 554 = 3，本轮现读 as-of 555 = 1，因为 R555 落了产品 3 文件（`6b70474`）之后连读零改动重新起算，这一格是"本轮之前"的时点量；HIDDEN **表=426 可判=1183 rot=0 抽不出=6 已声明表=6 已声明死针=0 处置=ok**（账面 425，差 **1** = R555 收口时把 M1439 那支表登记进名册后的新数，现读为准）；预检 **tables=339 covered=295 arms=757 bad=0**、`ARM_TOTAL files=432 arms=1244 dupes=0 repeats=0`；电池 **695/5**（开场即复跑，`Ran 695 tests … OK (skipped=5)`）；安装 **433=433** 且 `INSTALL_SIGNATURE=local`（R555 现读，PID 39654）；全量 **1396/55/0（756.9s）** 是 R555 的现读，本轮产品一旦动就重跑，不沿用。

**③ 禁碰清单（现读逐字抄自 `AGENT_STATE.md` 的 R555 节 ⑤，共 9 面）**：R546 登录失败图标、R547 默认行锁、R548 250pt 批量标题、R549 无序列表符号、R550 浮层提示键名、R551 收藏星尺寸、R552 折叠过渡、R553 固定码签身份链、R555 收藏星判据的倍率口径。本轮九面一律不动。

**④ 本轮靶（照发令，硬要求至少一次真产品或真判据推进，不许空账）**
- **(a) 632 剩下的那一半 —— 本轮实读把根因换了位置（R553 那格的边界读漏了一处）**。R553 写的是"采集路径（`ClipboardIntake`）只记 URL，不读文件"，那句话对 `ClipboardIntake` 成立，但**条目一进 `HistoryStore` 就有人去开那个文件**：`HistoryStore.add(...)` 第 700 行 `attachFileThumbnailIfNeeded(for: entry)` ⇒ `FileThumbnailPolicy.thumbnail(for: url)` ⇒ `CGImageSourceCreateWithURL` **在采集这一刻打开受保护目录里的图片**；更狠的是 `ApplicationShell:78` 每次启动跑 `attachMissingFileThumbnails()`，把**历史里每一条没有缩略图的图片文件**再开一遍 —— 而读失败（没授权）时条目仍是 `thumbnail == nil` ⇒ 下次启动**又全部重来** ⇒ "已批准无数次还在弹"的重复形状与这一格对得上。第三条：同一次渲染里文本被开两次（`MediaLoader.readTextPreview` 与 `DetailView.preferredTextHeight`）。
  **并且这件事现在是被判据钉住的**：`FileThumbnailTests/testStartupBackfillIsWired` 用源码 grep 断言 `ApplicationShell` 里有 `attachMissingFileThumbnails()`、`HistoryStore` 里有 `attachFileThumbnailIfNeeded(for: entry)` ⇒ 静态断言把 eager 读钉成了契约（memory 里"静态断言把 bug 钉成契约"那一族）。本轮要动的是**这一对**：产品改成"行真正显示才补图"（`requestThumbnail(for:)` 由行视图 `.task` 触发，采集与启动都不开盘），同一笔把那条 grep 判据的契约翻过来，并配新的计数器判据（采集 `count(for: url)=0` + 行显示 `=1` 作正对照）。**先量旧值再改**；上不了的那一格写具名出口续单，不许静默放回。
- 其余：622/624/627/629 继续；628/625/626/569/616 不重开；**633 仍等用户人工回执**（用户本轮未回 ⇒ 不许拿签名链 / DR 文本 / 离屏帧顶替「弹窗已修好」）；4.5 地板、150 上限、120ms 阈值、Motion ≥2 帧地板、**2x 的 8.0pt 跨度地板与 1x 的 6.0pt 整行地板**均不动；刀号 **M1440** 起。

"""

s = s.replace(anchor, body + anchor, 1)
io.open(P, 'w', encoding='utf-8').write(s)
print('R556 ⓪ written')

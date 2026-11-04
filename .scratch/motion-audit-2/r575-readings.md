# R575 读数（第 574 轮 / Round 572 · 2026-11-04 · 靶 = 折叠规格 §3 第②段收尾 / BACKLOG 654）

## ⓪ 两跑现读（不轮询）

| 对 | 现读 | 处置 |
| --- | --- | --- |
| `41828227003 ↔ d544998`（R574 判据笔） | `status=in_progress / conclusion 空` | **未读**。它才含 653 的三态与 `ROUND_HEADINGS` 那把新尺 |
| `41829014269 ↔ f3e1bf4`（R574 补记笔） | `status=in_progress / conclusion 空` | **未读**。不许替上一行签（R565 那一族） |

⇒ 本轮推进不建立在任何"等来的数"上；两对号带进 R576 的 ⓪，另加本笔自己那一跑。

## ② 推进本体：D12 八条 × 通道 × 到数（本机 2x，通道串 `D12_CHANNEL_MAP`）

| 条 | 通道 | 前置由谁满足 | 需真机 | 通道现读 | 对象现读 | 声明 | 实测 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 角度单调 | 产品内角度驱动 | 不适用 | 0 | 无 | 无 | 今天无证人 | 今天无证人 |
| 投影宽度按余弦律 | 逐帧像素 | 夹具快门cacheDisplay | 0 | 有 | 无 | 今天无证人 | 今天无证人 |
| 模糊半径从铰链到自由边递增 | 逐帧像素 | 夹具快门cacheDisplay | 0 | 有 | 无 | 今天无证人 | 今天无证人 |
| 亮度随角度单调下降 | 逐帧像素 | 夹具快门cacheDisplay | 0 | 有 | 无 | 今天无证人 | 今天无证人 |
| 边框锐度不变 | 逐帧像素 | 夹具快门cacheDisplay | 0 | 有 | 无 | 今天无证人 | 今天无证人 |
| 透明区alpha归零 | 离屏alpha图层 | 夹具快门cacheDisplay | 0 | 有 | 无 | 今天无证人 | 今天无证人 |
| 框架只在透明之后缩一次 | 窗口几何读数 | 不适用 | 0 | 有 | 无 | 今天无证人 | 今天无证人 |
| 屏上帧间隔不超标 | 真机60fps录屏 | 不适用 | 1 | 无 | 无 | 只能真机 | 只能真机 |

汇总逐字：`D12_CHANNEL_MAP_SUMMARY 条=8 runner可判=0 只能真机=1 今天无证人=7 角度驱动文件数=0 折叠路径文件数=2 折叠期改alpha文件数=0 真机键=关 离屏alpha通道采样=20160 不透明=2068 全透明=17180 产物采样=105000 产物全透明=0 窗口宽=750.0`

三条结论（各带证人）：
1. **0 条今天能在 runner 上判** —— 八条里七条 `今天无证人`、一条 `只能真机`。⇒ D12 那句"逐帧硬判据 + 用户手感签字，两边都过才算完成"今天**只剩手感那一半**（代价写进 654，取舍归用户）。
2. **通道与对象是两件事**：`逐帧像素`（`产物采样=105000`）、`离屏alpha图层`（`采样=20160 不透明=2068 全透明=17180` —— 这条通道确实分得出透明）、`窗口几何读数`（`窗口宽=750.0`）三条通道今天都**到数**；缺的全是**对象**（角度/模糊驱动文件数 0、折叠期改 alpha 文件数 0）。⇒ 这一格与 653 是两件事：653 说"帧产物那一侧没有 alpha 可用"，本表说"树那一侧通道能用但没有那块透明区"。
3. **`屏上帧间隔不超标` 只能真机**：`真机键=关` 且 CI 上那一档永远关 ⇒ 与 §4 阴影那一族 `REALSCREEN_SHADOW_NOT_RUN=env-off` 同形（先例已在账，不是本轮新造的出口）。

## ③ 本轮第一个真读数：我的探针读错了对象（两朵真红抓出来的）

- 第一版谓词：`文件里出现 "Collapse" || "foldProgress"` **且** `出现 "alphaValue" || "isOpaque"` ⇒ 命中 **1** 个文件 = `ClipboardHistory/Sources/ClipboardHistoryApp/Managers/AppDelegate.swift`，命中的两行分别是 `let mainWindowCollapse: MainWindowCollapseController`（第 24 行）与 `window.isOpaque = false`（第 67 行，D4a 那条**永久**底衬决定）⇒ 与"折叠期间改 alpha"无关。
- 后果（逐字）：`条=透明区alpha归零 … 对象现读=有 声明=今天无证人 实测=runner可判` 与 `条=框架只在透明之后缩一次 …` 两朵 `XCTAssertEqual` 红。
- 修法（**不是**改声明、**不是**放宽断言）：拆成两个独立现读 `countFoldPathWriters()`（`foldProgress` / `setCollapsed(` / `isTransitioning`）= **2** 与 `countFoldAlphaWriters()`（前者 ∩ alpha 写入）= **0**，并加 `foldPathFiles >= 1` 的反面证人（否则"交集为 0"分不清"确实没对象"与"扫描扫不到任何东西"）。
- 同族扫描的另一条证人：`countProductFiles` 在目录读不到时返回 **-1**，调用处断言 `>= 0` ⇒ "扫不到"不许冒充"没有对象"（R565 那一族在源码扫描侧的形状）。

## ④ 刀（M1509–M1512 全 CAUGHT、RESTORE_CLEAN=yes）

| 刀 | 打在哪 | 读数怎么变 | 红在哪一格 |
| --- | --- | --- | --- |
| M1509 | 表里删掉「屏上帧间隔不超标」那一行 | `rows.count` 8→7 | `XCTAssertEqual(rows.count, 8)` |
| M1510 | 那一行的 `declared: .realScreenOnly` → `.judgeableOnRunner` | 声明与实测不符 | 逐条 `XCTAssertEqual(measured, row.declared)` |
| M1511 | 分类函数里 `if !channelReads { … }` 那一支整行删掉 | 那条落到 `今天无证人` | 同上（dispatch ② 要的那句本体） |
| M1512 | `return folds && alpha` → `return alpha` | 交集 0→1 ⇒ ⑥⑦ 两条实测翻成 `runner可判` | 同上（钉本轮自己犯的错） |

撤掉的一把探测刀（不登记不占号）：把 `artifactAlpha(of:step:)` 的 step 从 4 改成 400 ⇒ `产物采样` 变小但 `samples > 0` 仍成立、没有任何断言读那个绝对数 ⇒ 空刀。下一轮从 **M1513** 起。

## ⑤ 上一轮那把新尺在门里的证据（④ 要求的那一步）

- `python3 scripts/ci_channel_hygiene.py` ⇒ `CI_CHANNEL_HYGIENE ci脚本=14 电池脚本=74 电池引用=24 合计=100 绝对根=0 真人路径=0 通道空格=0 RESULT=ok`（R574 落盘前是 `电池脚本=73` ⇒ 新那份 `scripts/tests/test_ledger_round_headings.py` 已被计入）。
- `.github/workflows/ci.yml` 的 `Release script tests` 那一步走 `python3 -m unittest discover -s scripts/tests` ⇒ 新尺**自动进 runner STEP[9]**，不需要另登记名册（与 R566 那种"新增具名 skip 必须登记"不同类：那一族登记的是 skip，不是脚本）。
- 本轮重跑该尺：5 格 OK + 现读 `ROUND_HEADINGS 本=7 标题=1833 逐字重复=0 RESULT=ok`。

## ⑥ 验证链现读（顺序没换，逐条抄自己那一行）

- 门：`ROUND_WARNING_GATE warnings=0 incremental=0 cold=0 target=build-tests`。
- 判据卷（两户合跑 `--filter "UICaptureTests|TransparencyForensicsTests"`）：`Executed 245 tests, with 8 tests skipped and 0 failures in 710.658 (710.681) seconds`。
- 重捕那一遍（`CLIPBOARD_HISTORY_UI_SHOTS=/tmp/r575/frames`，只 `--filter UICaptureTests`）：`Executed 229 tests, with 4 tests skipped and 0 failures in 741.676 (741.697) seconds` ⇒ skipped 8/4 之差是**两户合跑与单户跑的口径差**，只记现读、不动门、不猜成因。
- 帧：`FRAME_BASELINE_AGAINST=working / COMPARED=356 / CHANGED=0 / MISSING=0 / ADDED=0` ⇒ **不跑 update**（新判据只往临时目录写一张帧，不进基线名单）。
- 全量卷：`Executed 1436 tests, with 60 tests skipped and 0 failures in 630.414 (630.501) seconds`（1436 = 上一轮 1435 + 新格；skipped 60 同值，只记现读）。
- 三支预检（串行）：`NEEDLE_PRECHECK tables=383 covered=304 arms=794 bad=0`、`ARM_TOTAL files=476 arms=1281 dupes=0 repeats=0`、`HIDDEN_ARMS 表=470 可判=1220 rot=0 抽不出=6 已声明表=6 已声明死针=0 处置=ok`、`CI_CHANNEL_HYGIENE ci脚本=14 电池脚本=74 电池引用=24 合计=100 绝对根=0 真人路径=0 通道空格=0 ⇒ RESULT=ok`。
- 换装：产品 0 文件 ⇒ `SKIP_INSTALL=no-product-change`；`security find-identity -v -p codesigning` 现读 `1 valid identities found`。
- 派生格（台账落盘之后现读）：`PRODUCT_STREAK ledger_round=574 streak=7 sections=550 as_of=last=8f679f9 last_round=567 newest=8f679f9 newest_round=567 date=2026-11-04 标签补自台账=9(fb2cea0,117f45d,7ebda4c,cd9d0cb,2eb1bee,8cbe238,0c97820,b09d646,bf6b921)`；`SOURCES_CELL 账上=R568/8f679f9 git=R568/8f679f9 一致=是`；`LEDGER_ABSENCE_RESULT=ok 不成立=0/63`（格=162 声明=63）。
- 电池（台账与派生格之后）：`Ran 725 tests in 91.094s — OK (skipped=5)`（第一趟，台账与派生格全部落盘之后）。这一行的数**不回填**进 STATE ⑧ / U-2531 / FINAL_REPORT 那三格。
- 台账形状自查（本轮的写账证人义务）：七本逐本 `git diff --stat` 验过纯插入（UI_AUDIT/ITERATION/BACKLOG/DECISIONS/CHANGELOG 各一本只增不删；STATE 那一行删除是"最后更新"抬轮次；FINAL_REPORT 六行是计数器与 streak 格）；`LEDGER_TOKENS books=7 stray=0`。

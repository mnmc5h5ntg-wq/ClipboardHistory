# R576 读数台账（工作笔记，随本轮台账笔提交；所有串都由落盘文件派生，不是手打的）

## ⓪ CI（`scripts/ci_read.py` + `gh run view --log`，日志落盘在 `/tmp/r576/ci-*.log`，失败步骤清单在 `/tmp/r576/ci_steps.txt`）

| run | commit | 结论 | 全部失败步骤（逐字） |
| --- | --- | --- | --- |
| `41843233864` | `d7ac364`（R575 主笔） | `completed / failure` | `STEP[15] Swift tests (executed-count gate)`、`STEP[17] Capture gate (unregistered reds must be zero)`、`STEP[19] Motion coverage floor`（**`STEP[18]` 绿**） |
| `41845985973` | `3bafac2`（R575 补记笔） | `completed / failure` | 上面三朵 + `STEP[18] On-screen probe coverage floor` |
| `41829014269` | `f3e1bf4`（R574 补记笔 = 归因对照那一跑） | `completed / failure` | `STEP[15]`、`STEP[17]`、`STEP[19]` |
| `41828227003` | `d544998`（R574 主笔） | `completed / failure` | `STEP[15]`、`STEP[17]`、`STEP[18]`、`STEP[19]` |

- 日志字节数：`3,050,413` / `2,968,147` / `3,118,341` ⇒ "不在失败列表里"这次可以当读数用。
- 步骤名这把尺这次**不灵**：`field2` 直方图 `16561/16561`（`41843233864`）全是 `UNKNOWN STEP` ⇒ 正文一律按 emit 通道串取。
- 映射表判据的 runner 证人（两跑逐字相同）：
  `D12_CHANNEL_MAP_SUMMARY 条=8 runner可判=0 只能真机=1 今天无证人=7 角度驱动文件数=0 折叠路径文件数=2 折叠期改alpha文件数=0 真机键=关 离屏alpha通道采样=20160 不透明=2547 全透明=16733 产物采样=26320 产物全透明=0 窗口宽=750.0`
  8 条 `D12_CHANNEL_MAP` 逐行 `声明=实测`（`今天无证人` ×7 + `只能真机` ×1）。
- `executed=` 先读（两跑逐字相同）：判据卷 `Executed 229 tests, with 34 tests skipped and 14 failures`；全量 `Executed 1436 tests, with 89 tests skipped and 14 failures`；动效卷 `Executed 79 tests, with 33 tests skipped and 0 failures`；`Executed 28/8 skipped/4 failures`（在屏探针卷里那一小卷）；**在屏探针主卷 `ui suite exit: 137 executed: 0 skipped: ? 已下结论的用例: 8`（补记笔 `7`）** ⇒ `executed=0` = 被看门狗收掉，不是"没红"。
- 捕获闸门：`CAPTURE_GATE_CASES passed=195 skipped=33 failed=1 有名字的红=1 类未知名单=0 NOT_RUN=183`（两跑同）。动效闸门 `MOTION_GATE_CASES passed=47 skipped=46 failed=0 有名字的红=0 类未知名单=0 NOT_RUN=181`。
- 动效地板：`MOTION_FLOOR_SUITE_RED=3`（`41843233864`）/ `=2`（`41845985973`），新增那条 `MOTION_FLOOR_BAD_REASON empty-state 的理由是 witness-snaps-here，而登记过的是 无 ⇒ 同一臂换了一种坏法 = 新缺陷`。
- 在屏探针地板：`PROBE_COVERAGE_SUMMARY 源码用例=14 登记=14`、`PROBE_DOMAIN 问了 44 条、判成 20 条`、`PROBE_DOMAIN_NOT_RUN 放行 22 条`（两跑同）⇒ `STEP[18]` 的翻面正文**没读到** ⇒ `STEP18_FLIP_CAUSE_NOT_READ=log-step-names-degraded`。
- 电池：`Ran 725 tests in 114.503s` / `python cases: 725`（`41843233864`），`Ran 725 tests in 115.147s`（`41845985973`），`STEP[9]` 两跑都不在失败列表 ⇒ `ROUND_HEADINGS` 那把尺（含活账那一格）由 runner 签绿。⚠ 同日志里 `ROUND_HEADINGS 本=1 标题=0 逐字重复=0` + `ROUND_HEADINGS_EMPTY=1 …` 是**合成语料那一格**的 stdout，不是活账读数。
- 红名单（`error: -[Class test]` 去重）：`41829014269` 7 朵；`41843233864` 8 朵（多 `MotionFilmstripTests.testMarkdownModeLabelChangeIsAVisibleProcess`）；`41845985973` 7 朵 ⇒ 那一朵是**一跑现样本红**。7 朵同名清单：`MotionFilmstripTests.testDetailEmptyToContentCrossfadeIsMeasuredOrDeclaredBlind`、`MotionFilmstripTests.testEmptyStateStillFadesWhenMotionIsReduced`、`UICaptureTests.testActionableInkStaysAboveTheLegibilityFloor`、`UICaptureTests.testCaptionTextStaysOnTheSecondaryTier`、`UICaptureTests.testDetailAreaHasASingleLeftAxis`、`UICaptureTests.testDetailStatusBarShowsTheRealSourceAppIconOnlyWhenAttributed`、`UICaptureTests.testQuickPickKeyboardHintClearsTheContrastFloor`。

## ② 本轮新判据（本机 2x，`/tmp/r576/criteria.log`，`exit=0`）

`LAYER_TREE_COLD 树=主窗 倍率=2.00x 实测=层树建了没画进料 登记=层树建了没画进料 判=与登记一致`
`LAYER_TREE_COLD 树=浮层 倍率=2.00x 实测=层树建了没画进料 登记=层树建了没画进料 判=与登记一致`
`LAYER_TREE_COLD_MECH 解释=①无窗口服务 判=被否_同台上乙或浮层甲建得出树`
`LAYER_TREE_COLD_MECH 解释=②置层要等上屏 判=未排干`
`LAYER_TREE_COLD_MECH 解释=③夹具顺序 判=被否_同进程第二次渲染与第一次逐字同`
`LAYER_TREE_COLD_SUMMARY 倍率=2.00x 主窗甲=层树建了没画进料 主窗甲第二次=层树建了没画进料 主窗乙=层树建了没画进料 主窗丙=层树没建 浮层甲=层树建了没画进料 夹具那步之后未画比例=0.3586`

同趟顺带重读的两条既有通道（**与 R575 的差**记在这里）：
`FRAME_CHANNEL_MECHANISM 树=主窗 … 类=B 子层冷=1 contents冷=0 通道未画比例=0.3586 产物采样=105000 产物不透明=105000 产物全透明=0 产物有alpha平面=1 前置判=夹具快门那步_contentView.cacheDisplay 产物判=产物铺平alpha`
`FRAME_CHANNEL_MECHANISM 树=浮层 … 类=C 子层冷=6 contents冷=0 通道未画比例=0.8521 产物采样=31500 …`
`D12_CHANNEL_MAP_SUMMARY 条=8 runner可判=0 只能真机=1 今天无证人=7 … 离屏alpha通道采样=20160 不透明=2068 全透明=17261 产物采样=105000 产物全透明=0 窗口宽=750.0`
⇒ **一条漂移**：同一份码、同一台机器，`全透明` 由 R575 的 `17180` 变成 `17261`（+81/20160 ≈ 0.4%），`不透明=2068` 未变 ⇒ 那条通道的 alpha 三分数**不是逐轮恒定量**；映射表只用它判 `>0`（"通道到不到数"），没拿它当精确尺 ⇒ 本轮结论不受影响，但若将来有人在那个数上放地板就会漂。这一格**开进 653/654 的相邻事实**，不改登记表、不动任何地板。

## ③ 一次性探针（`R576ProbeTests.swift`，跑完当场删除、不入库）

`R576PROBE_ANGLE 切换次数=3 发布档数=3 之前=0 序列=1.00,0.00,1.00 中间档=0 缺的对象=过渡期间的角度/进度序列（今天只有 0 与 1 两档）`
`R576PROBE_WIDTH 展开宽=848.0 折叠宽=424.0 投影宽度表达式文件数=0 缺的对象=投影宽度这个量本身（今天只有窗口宽，没有按角度投影出来的宽）`
`R576PROBE_RUNNER runner镜像=macos-15 属于D6的14+那一档 着色器文件数=0 角度序列判据=数值不依赖像素⇒runner可判 投影宽度判据=要着色器先落地⇒落地后runner仍可判（14+）`

## ⑥ 禁碰证人（本轮碰的是捕获夹具那份测试文件）

`TRANSPARENCY_STATE isOpaque=0 窗口底色alpha=0.000 底衬=1 采样=39342 带内最小alpha=255 半透明样本=0/39342 洞范围=无`（与 R575 逐字同）
`TRANSPARENCY_HITTEST 探针=3 空区命中=底衬0/容器3/内容0 底衬自身 hitTest=让位 ⇒ 容器仍吃命中 ⇒ 窗口级穿透需要 contentShape/ignoresMouseEvents（第③段）`（逐字不动）
`TRANSPARENCY_MATERIAL 不透明 均值=0.9339 字墨=8253 品红漏出=0 || 非不透明 均值=0.9339 字墨=8253 品红漏出=0 || 均值差=0.0000 字墨比=1.000`（**本轮真机键那一档单独跑了一次**：`CLIPBOARD_HISTORY_UI_REALSCREEN=1 swift test --filter …/testGoingNonOpaqueDoesNotWashOutTheSidebarMaterial`，`Executed 1 test, with 0 failures`，两张贴图量完即删、不入仓）
反面臂同跑给出 `TRANSPARENCY_MATERIAL_NEG 撤掉底衬 均值=0.6914 字墨=56747 品红漏出=318 均值移动=0.2425 || 放回底衬 均值=0.9339 品红漏出=0` ⇒ 这条尺看得见变化，不是恒真。
⇒ **禁碰数不抬（仍 14 面）**；`registeredOffscreenVerdict(scale:)` 一字未动。

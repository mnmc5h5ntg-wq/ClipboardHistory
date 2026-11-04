# R568 读数笔记（自存，随台账笔提交）

## ⓪ 两跑（都在盘上：`/tmp/r568-ci-A.log` = 41733244129↔ce1904d、`/tmp/r568-ci-B.log` = 41733778713↔60a805e、`/tmp/r568-ci-base.log` = 41711240581↔fdbf0c0）
- 两跑逐字同一朵三朵失败步骤：STEP[15] / STEP[17] / STEP[19]；步骤名可解析（22 个真名、0 个 UNKNOWN STEP）。
- STEP[9] `SKIP_ROSTER … 内层Ran=720 内层skip汇总=4 解析=3 名单外=无 名册未跳=无` = success（连续第四次）。
- STEP[15]：`Executed 1411 tests, with 86 tests skipped and 4 failures`（base 是 `1406 … 1 failure`）。四朵红 = 两栏那格 2 条断言 + HINT_CONTRAST + 像素缝。
  - `FOLD_GEOMETRY_COLUMNS 侧栏=424.00 详情(算)=423.00 分隔条=1.00 分栏宽=848.00 缝中心=424.50`
  - `FOLD_GEOMETRY_ITEMS 列数=2 每列=[canCollapse=0 min=423.5 max=423.5 ; canCollapse=0 min=-1.0 max=-1.0]`
  - `FOLD_GEOMETRY_DRAG_PROBE 拖到300之后 侧栏=424.00`
  - `FOLD_GEOMETRY_ASPECT 展开 ratio=1.413333 可拖=true / 折叠 0.706667`（无 `ASPECT_LOCK_NOT_RUN`；`Target Platform: arm64e-apple-macos14.0`、Swift 6.1.2、`Target: arm64-apple-macosx15.0`）
  - `FOLD_GEOMETRY_REANCHOR 展开 layout=848x590 frame高=642.0 三口径=848/{848, 642}/{848, 642}`、`折叠 layout=424x614 高差=0.0`
  - `FOLD_SEAM_PIXEL light/dark 帧=848x600 倍率=1.00x 缝列=-1.0pt 跳变=0.0 左墨=-1 右墨=0 期望=424.0pt 地板=8pt`
- STEP[17]：`CAPTURE_GATE_RESULT=fail 有 2 个用例红了` = testQuickPickKeyboardHintClearsTheContrastFloor + testTheSeamInTheRenderedFrameSitsAtHalfTheContentWidth。
- STEP[11] success：`FRAME_BASELINE_AGAINST=working COMPARED=356 CHANGED=356 MISSING=0 ADDED=0`（CHANGED=356 是跨机通道，不许读成帧变了）。STEP[13] report-only 对 v1.4.8：`MISSING=6`（glass-pill-120x200 / search-field-320x96 / weights-520x560 各 2）+ `ADDED=294`；`docs/frame_baseline.json` 现读这 6 个名字各 0 次、`main-collapsed-424x600` 2 次。
- 639：`HINT_CONTRAST light 底=236 字芯=(118,118,118) 对比=3.84:1 字芯像素=40 偏差像素=696 地板=4.5 倍率=1.0x`、`dark 底=50 字芯=(163,163,163) 5.08:1 … 712` ⇒ 第五次同值。
- 643 第九数：`MOTION_BAND_SAVING 带中位=8.54ms 整窗中位=10.73ms 省=1.26× 线=1.0×`。
- STEP[19]：base `judged=5/5 not-run=- … empty-state=3 红的用例=- MOTION_FLOOR_REDS=0`；本环两跑 `judged=4/5 executed=79 not-run=empty-state … empty-state=1 红的用例=testDetailEmptyToContentCrossfadeIsMeasuredOrDeclaredBlind,testEmptyStateStillFadesWhenMotionIsReduced 汇总行报红=2` + `MOTION_FLOOR_BAD_REASON empty-state 的理由是 witness-snaps-here，而登记过的是 无` + `MOTION_FLOOR_SUITE_NOT_SEEN=2`（testNativeRowMove… / testRowAnimationSurvives…，与红的两条不同名）。
  - 分岔三条：`MOTION_GRAB empty-state 帧数=30 视图=380×548pt`（两棵树逐字相同）；`MOTION_REDUCE_SOURCES setting=true voiceOver=false catalog=true override=nil`（两棵树逐字相同）；`抓帧中位 6.2ms→2.1ms`、`事件内P75 38ms→21ms`、曲线 `0.089 0.000 0.000 0.148 0.021 0.017 …` → `0.322 0.000 …`。
  - 两跑之间值自己漂：A `21ms（1 帧，P75=21ms）` vs B `10ms（1 帧，P75=10ms）`。
  - `scripts/motion_floor_expectations.json` 现读：`arms["empty-state"] = {must_judge: true, stale_if_judged: false, allowed_not_run_reasons: []}`；`suite_reds` 只有两条（testNativeRowMove… / testRowAnimationSurvives…，均 machine=github-runner、recurrence=sampled、points_to 354）。

## ② 本轮现读（`/tmp/r568/readings*`、`/tmp/r568/transparency-*.log`）
- 产品今天（有底衬）：`TRANSPARENCY_MATERIAL 不透明 均值=0.9339 字墨=8253 品红漏出=0 || 非不透明 均值=0.9339 字墨=8253 品红漏出=0 || 均值差=0.0000 字墨比=1.000`
- 负臂（藏底衬，同一次跑）：`TRANSPARENCY_MATERIAL_NEG 撤掉底衬 均值=0.6637 字墨=11582 品红漏出=319 均值移动=0.2702 || 放回底衬 均值=0.9339 品红漏出=0`
- 独立两臂实验（临时改产品、已还原）：`TRANSPARENCY_STATE … 底衬=0 … 带内最小alpha=0 半透明样本=18290/41475 洞范围=x[853..1672] y[118..1238] 位图=1696x1264 首个=(x853,y118) a=25 rgb=(0,0,0)`
- 产品状态（有底衬）：`TRANSPARENCY_STATE isOpaque=0 窗口底色alpha=0.000 底衬=1 采样=39342 带内最小alpha=255 半透明样本=0/39342 洞范围=无`
- 通道：离屏 `hasAlpha=1 黑半区=(r0,g0,b0,a255) 透明半区=(r0,g0,b0,a255) 分得出=0`；真机 `透明半区=(r234,g51,b247,a255) 分得出=1`
- 阴影：正对照 `左带暗=0.0649 右带暗=0.0649 外扩=40pt 倍率=2.00x`；半片 `左带暗=0.0631 右带暗=0.0017 判=套形状`
- 命中：`TRANSPARENCY_HITTEST 探针=3 空区命中=底衬0/容器3/内容0 底衬自身 hitTest=让位`
- 本机两栏（2x）：`侧栏=423.50 详情(算)=423.50 缝中心=424.00 倍率=2.0x 半格可落=1 列差界=0.010 缝心界=0.010`
- 本机像素缝：`judged=2`（0 失败），缝列 424.5pt、跳变 54.0/17.0、左墨 125434/129950、右墨 2105/2304

## 验证链
- build：`ROUND_WARNING_GATE warnings=0 incremental=0 cold=0 target=build-tests`
- 判据卷：`Executed 224 tests, with 4 tests skipped and 0 failures in 786.259s`（`/tmp/r568/capture.log`）
- 帧：`COMPARED=356 CHANGED=0 MISSING=0 ADDED=0` ⇒ **不 update**（`/tmp/r568/compare.log`）
- 看图：3 张整帧（main-collapsed-424x600 light/dark、content-with-history-750x560-light）
- 刀：M1480–M1485 全 CAUGHT、RESTORE_CLEAN=yes（`/var/folders/…/b4php6nb3.output`）
- 全量 / 预检 / 换装 / 电池：待跑（`/tmp/r568/full.log`、`needles.log`、`armtotal.log`、`hidden.log`、`install.log`、`/tmp/r568-battery.log`）

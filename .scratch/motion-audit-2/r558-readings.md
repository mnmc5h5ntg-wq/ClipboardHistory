# R558 现读台账（工作笔记，不是第七本账；收口时抄进 ledgers_r558.py 的 NUM 与正文）

## 已到手（不要重做）

- 树：HEAD=origin=`2f85c5d`（⓪ 笔已推），ahead=0；本轮未提交改动 = `MotionFilmstripTests.swift`、`scripts/tests/test_skip_roster.py`、`.scratch/motion-audit-2/mutate_needle_precheck.py` + 4 把新刀脚本 + 探针脚本 + 台账/补记脚本。
- `swift build --build-tests`：告警 **0**（`/tmp/r558-build3.log`，改完 meanDistance 写法之后）。
- 629 新尺最终现读（`/tmp/r558-films/motion-readings.log`，收口前重捕那一次）：
  `MOTION_MARKDOWN_MODE_FADE scale=1x 帧数=27 过渡帧数=5 相邻差帧数=4 首末连续差=0.0031 峰值=0.0145 声明=200ms 窗口=329ms 每格=12.6ms`
  `相邻帧差=[0.0000,0.0145,0.0097,0.0048,0.0048,0.0000,…]`
  `离前=[0.0000,0.0011,0.0018,0.0020,0.0024,0.0026,0.0028,0.0029,0.0030,0.0030,0.0030,0.0030]`（单调升）
  `离后=[0.0031,0.0023,0.0016,0.0011,0.0008,0.0005,0.0003,0.0002,0.0001,0.0001,0.0000,0.0000]`（单调降）
  `唯一变化区=行 25…34 列 69…89（10×21px，帧 160×60）`
- 真实看图（重捕之后，`/tmp/r558-films/markdown-mode-label-1x-strip.png`，放大 `/tmp/r558-label-film-rows01.png`）：第 0–1 格「原文」→ 第 2–3 格两幅字半透明叠在一起（ghost 看得见）→ 第 4 格起「渲染」落定；逐格暗墨 `13,13,9,7,12,13,15,17`。
  ⚠ `/tmp/motion-films/`（默认目录）里那张同名 strip 是 **M1446 变异时**的产物（27 格逐格相同、暗墨恒 13）⇒ 不是证人，本轮已拒用。
- 合成真值表四臂（`testSandwichCountJudgesInterpolationNotSamplingPhase`，`Executed 1 test, with 0 failures`）：台阶保持四帧 = 新 **4** / 旧 **2**；粗相位 = 旧 **1** / 新 **0**；密采斜坡 = 新 **3**；只离前态 1/255 = 新 **1**。
- 负向臂 M1446（title 钉成常量）：`过渡帧数=0 相邻差帧数=0 首末连续差=0.0000 峰值=0.0000` ⇒ 两条断言各红一次（`根本没拍到任何交换` + `只读到 0 个中间帧`）。
- 四把刀（最终树上，`/tmp/r558-knife-*.log`）：M1446 CAUGHT / M1447 CAUGHT / M1448 CAUGHT / M1449 CAUGHT，全 `RESTORE_CLEAN=yes`，全 `预检: PASSED`。
- 634 现读两格：
  - 正常路径（`/tmp/r558-634-a.log`）：`Ran 4 tests … OK`，观察者行 `SKIP_ROSTER 键=local:MacBook-Air.local 类=local 内层Ran=696 内层skip汇总=6 解析=5 名单外=无 名册未跳=无`。
  - inner-red 路径端到端（注入一个临时失败测试再删掉，`/tmp/r558-634-b.log`）：观察者仍 **红**（`Ran 4 tests … FAILED (failures=1)`），正文 = `内层那一卷自己是红的 ⇒ … 汇总行「FAILED (failures=1, 跳过了=6)」；内层红名=test_r558_inject_probe_for_inner_red_path（键=local:MacBook-Air.local 类=local）` ⇒ 带内层汇总行 + 内层红名 + 机器身份；注入文件已删除（`REMOVED=yes`）。
  - no-summary 路径：由真值表用三份 canned 文本钉（`Ran`+`OK` / `Ran`+`FAILED` / 只有半截），**没有** live 演示（要让内层真的连汇总行都不产出得杀进程 ⇒ 本轮不演，照实写"真值表级"）。
- 本轮自造的红（已修，取证跑 `/tmp/r558-full.log`）：新尺 `meanDistance` 被既有 `testEveryTwoStateRulerReadsBothAxes`（AXIS_GUARD）点成「两态尺只读亮度」⇒ 扫到 6 / 名册 5 ⇒ 全量 1 红。修法 = 改**写法**（`max(rgb, alpha)` → `rgb > alpha ? rgb : alpha`，计算等价），**没加豁免、没放门**；复跑 AXIS_GUARD `Executed 1 test, with 0 failures`。
- 一次性探针（不入库）：`probe_r558_what_the_film_measures.py` 四臂（摘 `.id(title)` / 摘 `.transition(.opacity)` / 摘 `.animation(value:)` / 三条全摘）读数与未变异**逐字相同**（只有 `窗口`/`每格` 抖 321–330ms / 12.4–12.7ms）⇒ 胶片不为那三行接线签字 ⇒ 新开 **635**。

## 待读（截断的链要重跑，旧日志一律不算）

- 判据卷 `UICaptureTests`（`CLIPBOARD_HISTORY_UI_SHOTS=/tmp/r558-frames2`）：跑到出汇总行为止 → 填 `CAPTURE`。
- 帧基线对账 `python3 scripts/frame_baseline.py compare /tmp/r558-frames2 --against working` → 填 `FRAMES`（`docs/frame_baseline.json` 未动 ⇒ 只有 CHANGED=0 才允许不 update）。
- 全量 `swift test`（有界 grep）→ 填 `FULL`。
- 预检三读：`mutate_needle_precheck`（⚠ 它会真跑 swift，**不能**与别的 swift 任务并行 —— 刚才撞锁读到 `预检 swift 失败：NOT_RUN_TIMEOUT`）、`ARM_TOTAL`、`HIDDEN_ARMS`（现读 `表=436 可判=1183 rot=0 抽不出=6 已声明表=6 处置=ok` ✓ 这条是干净的）。
- 换装 `--label R558` → 填 `INSTALL`。
- 电池（台账+补记之后）→ 填 `BATTERY`；清账 → `ABSENCE`；streak → `--streak-for 557`。


## 第 0 步已做（防切断）
- 本地提交 `b8949f5`「R558 A：629 换判据对象（两端夹逼连续距离）与 634 拆三态读数落地（第 557 轮 / Round 555 · 产品 0 文件 + 判据 1 文件 + 观察者 1 文件 + 四把刀）」= 8 文件 652 插入，**未 push**（ahead=1）。含 4 把刀脚本 + 一次性探针 `probe_r558_what_the_film_measures.py`（探针本轮**入库**，所以它是可重跑的证人 —— 台账要按这条写，不写"不入库"）。

## 收口前补读的 CI（`ci_read.py queue` + `steps` + `gh run view --json jobs` + `readings`）
- `41465486002 ↔ 5d05578`（R557 台账笔）**success**；`41467173705 ↔ 61285b6`（R557 补记笔）**success**；`41469418563 ↔ 2f85c5d`（本轮 ⓪ 笔）**success** ⇒ sources 格一致 ⇒ STEP[9] 绿 ⇒ **634 的借红因果被 runner 签死**。
- `41464892684 ↔ ce4da8f`（R557 刀表笔）**failure**，只有 STEP[9]（10–14 skipped）⇒ 与"分批 push 造注定红"预测一致。
- `41467585182 ↔ ff15906`（R557 补记第二笔）**failure**：STEP[9] **绿**，红在 STEP[18] + STEP[19]。
  - STEP[18]：`PROBE_COVERAGE_SUMMARY 源码用例=14 登记=14 runner可跑=8 runner不可跑=6 本次下结论=7 闭合通道=接 本次跑过=8 红=1`；`FAILED testFrameIntervalsUnderStateChanges：最差帧 225.3ms 超过锚点 120ms，且超锚点的帧有 3 颗（容差 1 颗）` ⇒ **622 第十三值 225.3ms/3 颗**。
  - STEP[19]：`MOTION_FLOOR_SUITE_RED=1 … 未登记的红用例：testMarkdownModeLabelChang…`、`MOTION_FLOOR_REDS=1`、`judged=4/5 executed=77 not-run=notice-banner`、`MOTION_FLOOR_NOT_SEEN=2`。
  - 旧口径第四值（同跑 report-only 步正文）：`MOTION_MARKDOWN_MODE_FADE scale=1x 帧数=27 过渡帧数=1 峰值=0.0193 声明=200ms 窗口=756ms 每格=29.1ms 相邻帧差=[0×8,0.0193,0,0]` ⇒ **runner 上 629 那朵红仍在**；⚠ 这一行推不出新口径会读几（新尺要连续距离）⇒ 新口径在 runner 上 **NOT-RUN**，R559 头一格。

## 长链状态（本轮第二次因串链被切，改成分步）
- 判据卷 `UICaptureTests`（SHOTS=/tmp/r558-frames2）：**217/4 skipped/0 失败（781.0s）** ✓
- 帧对账 `--against working`：**354 CHANGED=0 MISSING=0 ADDED=0** ✓（`docs/frame_baseline.json` mtime 未动 ⇒ 真 0，不需要 update）
- 全量：正在跑（撞锁的重复 capture 进程 80273/85908 已终止，日志 `/tmp/r558-full2.log`）
- 预检三读：**必须串行**（与 swift 卷并行会假报 `预检 swift 失败：NOT_RUN_TIMEOUT`）；HIDDEN 那条已干净读到 `表=436 可判=1183 rot=0 抽不出=6 已声明表=6 处置=ok`
- 换装 / 台账 / sources 格 / 电池 / 一次性 push：待做

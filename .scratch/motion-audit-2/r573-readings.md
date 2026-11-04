# R573 读数笔记（第 572 轮 / Round 570 · 2026-11-04 · 靶 = 折叠规格 §3 第②段 / 651 + ③ 选路）

## ① 身份与门（现读）

- UI_AUDIT 最新标题 = `## 第 571 轮（R572` ⇒ 本轮 **R573 = 第 572 轮 / Round 570**。
- 刀高水位现读 **M1501**（`mutate_r572` 表尾）⇒ 本轮从 **M1502** 起，落三把 M1502–M1504。
- `ROUND_WARNING_GATE warnings=0 incremental=0 cold=0 target=build-tests`。
- `git status --short ClipboardHistory/Sources` **空** ⇒ 产品 0 文件；`find-identity -v -p codesigning` 仍 `1 valid identities found`（与 633 的人工回执是两件事）。
- dispatch 引的行号（`:150/:149`）按现读算漂移：R572 的「下一轮（R573）的靶」那一格现读在 **`AGENT_STATE.md:146`**（⑦ 那一行里），五行内容照抄开工。

## ② ⓪ 两跑到数（都是到数的，没有"复核未到"）

### `41783402475 ↔ 2232069`（R571 那一笔）= `completed / failure`

全部失败步骤（逐条原样）：

```
RUN=41783402475 conclusion=failure
  JOB build-and-test ⇒ failure
    STEP[15] Swift tests (executed-count gate) ⇒ failure
    STEP[17] Capture gate (unregistered reds must be zero) ⇒ failure
    STEP[19] Motion coverage floor ⇒ failure
```

- 卷的数：全量 `Executed 1430 tests, with 89 tests skipped and 18 failures`；判据卷那一遍 `227/34/14`；`Executed 28 tests, with 8 skipped and 4 failures`（R571 那一格的 4 条断言）；`Executed 79 tests … 0 failures`（动效卷有真读数）；`Executed 14 tests, with 13 skipped and 0 failures`；`Executed 12 tests, with 3 skipped and 4 failures`。
- 红的用例名（去重 6 个）：四支 `detail-*` + `testQuickPickKeyboardHintClearsTheContrastFloor`（639）+ **`TransparencyForensicsTests testTheAlphaLayerChannelSeparatesTrueBlackFromTransparentAtBothScales`（R571 那一格）**。
- **新通道在 runner 1x 那一行到手（逐字）**：
  `TRANSPARENCY_CHANNEL 通道=离屏-alpha图层 位图=400x240 倍率=2.00x 黑半区=(r0,g0,b0,a0) 透明半区=(r0,g0,b0,a0) 分得出=0`
  `TRANSPARENCY_CHANNEL 通道=离屏-alpha图层 位图=200x120 倍率=1.00x 黑半区=(r0,g0,b0,a0) 透明半区=(r0,g0,b0,a0) 分得出=0`
  ⇒ **两档都读到整幅 a=0，连黑半区也是** ⇒ 形状不是"分不出真黑与透明"，而是**什么都没画** ⇒ 落在 651 三个出口的**第一个（画不出）**。本机同一格两档都 `分得出=1`。
- 旧通道那一行照旧、登记未被改动：`TRANSPARENCY_CHANNEL 通道=离屏 位图=200x120 倍率=1.00x hasAlpha=1 黑半区=(r0,g0,b0,a255) 透明半区=(r0,g0,b0,a0) 分得出=1 实测=保留 alpha 登记=保留 alpha`。
- **恒等式判法在 runner 上绿（逐字）**：
  `CHROME_PUBLISH_TRACE 路=产品主窗 容器高=28.0 按钮高=16.0 公式应发=24.0 序列=24.0 最小=24.0`
  `CHROME_PUBLISH_TRACE 路=手搭真窗 哨兵=10.0 发布次数=2 序列=34.0 最小=34.0 容器高=38.0 按钮高=16.0 公式应发=34.0`
  ⇒ 两行都是 `序列 == 公式应发` ⇒ **R571 换的判法在那台机器上成立**；而**我上轮反推的 `按钮高=13` 是错的，实测是 16**（自我更正，见 ⑥）。
- `CAPTURE_FOREIGN_WINDOW` 没有一行（通道在这棵树上存在）⇒ (甲) 维持被否；`CAPTURE_CHROME_INSET` 2 行（`值=35.000 判=与兜底一致` / `值=24.000 差额=-11.000 上一次=首拍`）⇒ 第三次逐字重现同一形状。
- `MOTION_FLOOR_FACTS judged=4/5 executed=79 … 红的用例=crossfade 那格 + empty-state 那格`、`MOTION_FLOOR_SUITE_RED=2`、`MOTION_FLOOR_SUITE_NOT_SEEN=2`、`MOTION_FLOOR_BAD_REASON empty-state 的理由是 witness-snaps-here，而登记过的是 无 ⇒ 同一臂换了一种坏法 = 新缺陷`。

### `41795721331 ↔ 79f7116`（R572 那一笔）= `completed / failure`

全部失败步骤（**四朵，比上一跑多一朵，且那一朵是我带的**）：

```
RUN=41795721331 conclusion=failure
  JOB build-and-test ⇒ failure
    STEP[9] Release script tests ⇒ failure
    STEP[10] Info.plist gate ⇒ skipped
    STEP[11] Frame baseline vs working manifest (fixture-set gate) ⇒ skipped
    STEP[12] Surface left-axis ruler (BACKLOG 234, wired in R210; venv interpreter in R218) ⇒ skipped
    STEP[13] Frame baseline vs previous release (change report, report-only) ⇒ skipped
    STEP[14] Runtime launch smoke (report-only) ⇒ skipped
    STEP[15] Swift tests (executed-count gate) ⇒ failure
    STEP[17] Capture gate (unregistered reds must be zero) ⇒ failure
    STEP[19] Motion coverage floor ⇒ failure
```

- **R572 那三格到数且绿**（红的用例名里去重 6 个与上一跑**同一集合**，没有新增）：
  `TRANSPARENCY_PRODUCT_ALPHA 树=浮层 通道=成对 前置=走过 位图=420x300 采样=5040 旧三分=605/4029/406 新三分=605/4029/406 逐点异类=0 旧有墨=615 新有墨=615`
  `TRANSPARENCY_PRODUCT_ALPHA 树=浮层 通道=离屏-alpha图层 位图=840x600 栅格选择=2.00x 采样=20160 不透明=2573 全透明=16214 半透明=1373 有墨=2632 分得出=1`
  `TRANSPARENCY_PRODUCT_ALPHA 树=浮层 通道=离屏-alpha图层 位图=420x300 栅格选择=1.00x 采样=5040 不透明=605 全透明=4029 半透明=406 有墨=615 分得出=1`
  `TRANSPARENCY_PRODUCT_ALPHA 树=主窗 通道=成对 前置=走过 位图=420x300 采样=5040 旧三分=5040/0/0 新三分=5040/0/0 逐点异类=0`
  `TRANSPARENCY_PRODUCT_ALPHA 树=主窗 判=无透明对象 采样=5040 全透明=0 不透明=5040 有墨=5040 逐点异类=0`
  `PRODUCT_MAIN_TREE_TRANSPARENT_OBJECT_NOT_JUDGED=backing-covers-whole-tree ⇒ 第③段有真透明区之后这一格必须重开`
  `TRANSPARENCY_PRODUCT_ALPHA 树=浮层 前置=缺席 位图=840x600 采样=20160 不透明=720 全透明=17806 有墨=786`
  ⇒ **`逐点异类=0` 在 1x 那台上成立**；650 的"产品树也保 alpha"由 runner 签到了。
- **STEP[9] 那一朵是我上一笔带来的**（归因：`41783402475` 那跑 STEP[9] 不在失败名单里 ⇒ 改动前绿、改动后红 ⇒ 可署名本轮回归）：
  `FAIL: test_recent_rounds_do_not_contradict_themselves (test_round_claim_consistency.RoundClaimConsistency)`
  `AssertionError: Lists differ: [] != [('79f7116', 'K_WITHOUT_ROUND_IDENTITY', '带着「产品 0 文件」却没有可解析的轮次身份｜R572：650 验完 —— …')]`
  内层汇总 `FAILED (failures=1, 跳过了=4)`、外层 `FAILED (failures=2, skipped=3)` ⇒ 第二朵是 `test_the_roster_matches_what_this_machine_actually_skips` **借报**（R558/634 那一族，它自己写对了：「内层那一卷自己是红的 ⇒ 这一格没有可对账的对象，红在内层不在这里」）。
  成因：尺 `SUBJECT = ^R(\d{2,4})(?: (.+?))?（.*?产品 (\d+) 文件` 只认 **ASCII 空格**当分隔符，而我那笔写的是 `R572：`（全角冒号紧跟轮次号）⇒ 合法写法被读成"带 K 却没有身份"。⇒ 本轮**修尺**（见 ⑤），不登记豁免。

## ③ 本轮靶 = 651 的机制读数（一次性探针，不入库；对象全是产品自己的树）

| 类 | 臂 / 状态 | 读数（逐字） | 判 |
| --- | --- | --- | --- |
| A AppKit 自绘单视图 | 冷态 / `view.display()` / `cacheDisplay` / `layer.display()` / `window.display()` | 五臂**逐字相同** `子层=1 contents=1 不透明=1920/1920 分得出=1` | 这一类**不需要前置** |
| B `NSHostingView` 的 SwiftUI 层（R571 那一格的对象） | 同上五臂（本机） | 五臂**逐字相同** `子层=1 contents=0 不透明=1920 分得出=1` | 本机也不需要前置 —— **但 runner 同一格读到整幅 a=0** ⇒ 这一类"需不需要前置"依机器而定 |
| C 产品浮层容器树 | 甲 只根 `wantsLayer` | `子层=-1 不透明=0 全透明=20160 有墨=0 分得出=0` | 层树没建出来 ⇒ 画不出 |
| C | 乙 递归 `wantsLayer` + layout，不 display | `子层=6 不透明=176 全透明=18444 半透明=1540 有墨=190` | 层树建出来了，内容只画了一部分 |
| C | 丙 再走一遍 `cacheDisplay` | `子层=6 不透明=2096 全透明=16745 半透明=1319 有墨=2117` | **把内容画进 contents 的是 display 通路** |
| D `CAMetalLayer` | 产品源码里引用 `CAMetalLayer`/`MTKView` 的文件数 | 现读 **0** | 今天不存在 ⇒ 具名 `METAL_LAYER_NOT_RUN=no-shader-yet`，**不编读数** |

- runner 侧的同一件事（来自 ② 的 `41795721331`）：C 类走过前置 ⇒ `逐点异类=0`；B 类没走前置 ⇒ 整幅 a=0 ⇒ **前置在两台机器上都不是可省的，只是缺席的后果落在不同类上**。
- M1502 落刀时的额外一条：先 `cacheDisplay` 再走"只根 wantsLayer"那一臂 ⇒ 甲读到 `不透明=176 子层=6` ⇒ **display 通路自己会把层树建起来**（乙/甲 合流），这就是"递归 wantsLayer 单独一把刀是空刀"的原因。

## ④ ③ 选路：**（乙）把前置找回来**

- 依据：同一台 runner、同一次跑，走过前置的树画得出（`旧三分=605/4029/406 新三分=605/4029/406`）、没走前置的夹具画不出（整幅 a=0）⇒ 机制支持"补前置"，不支持"这台机器上这条通道永远不能用"。
- 落地：`captureTwoHalvesViaAlphaLayer` 在判据取图之前走一遍旧通道 `cacheDisplay`，并**保留一条冷态对照读数** `OFFSCREEN_ALPHA_LAYER_COLD 位图=400x240 倍率=2.00x 采样=3840 不透明=1920 全透明=1920 有墨=0 分得出=1`（本机；不判，只留作两台的对照）。
- **本机读数不变这件事照实写**：`OFFSCREEN_ALPHA_PREREQ_LOCAL_NOOP=本机冷态已能画 ⇒ 这一步的有效性由 runner 那一签收，不由本机`。
- 没选（甲）的理由：（甲）只说"那条通道在那台机器上不能用"，而 651 问的是"这个前置由谁满足"；且（甲）要新增机器类具名 skip 并登记进 CI 的门与电池名册（R566 那一族），把一条本可以修好的判据永久变成不判。
- **651 不结案**：类 B 为什么在那台机器上冷态画不出（window server 会话缺席？backing store 未分配？）本轮没量到那一层。

## ⑤ 第二件推进：修尺 `SUBJECT`（STEP[9] 那朵我带来的红）

- `.scratch/motion-audit-2/review_round_claims.py`：分隔符从只认 ASCII 空格放宽成 `[ ：]`（R555 的先例：修尺 + 正对照 + 刀，不攒豁免）。
- `scripts/tests/test_round_claim_consistency.py`：合成行加第 6 行 `ffff666 R904：冒号紧跟轮次号的一笔（第 903 轮 / Round 900 · 产品 0 文件，判据账）`，`scanned` 从 5 改成 6，并断言 `904` 被认出、半名与 K 读对（`[('ffff666','冒号紧跟轮次号的一笔',0)]`）。
- 现读自证：`git log HEAD~4..HEAD` 用新尺 ⇒ `rounds=['572'] unparsed=[]` ⇒ `79f7116` 不再被报成"带 K 却没有身份"。
- 旧豁免 `fb2cea0`（`Round 336: …` 那种没有 `Rnnn` 前缀的旧形状）**保留**：新尺仍然读不出它 ⇒ 没被这次放宽顺手清掉，登记仍然必要。
- 刀 **M1504** 把尺退回只认空格 ⇒ 合成正对照那一格红（CAUGHT、RESTORE_CLEAN=yes）。

## ⑥ 刀（M1502–M1504 全 CAUGHT、RESTORE_CLEAN=yes）

| 刀 | 打在 | 坏法 | 落刀后的读数 |
| --- | --- | --- | --- |
| M1502 | 尺（机制格） | 甲臂之前先 `cacheDisplay` 一遍 | 甲 `不透明=176`（与乙同）⇒ `甲.不透明 == 0` 红 |
| M1503 | 尺（机制格） | 摘掉丙臂的 display 前置 | 丙 `不透明=176` == 乙 ⇒ 严格链 `丙 > 乙` 红 |
| M1504 | 尺（提交身份） | `SUBJECT` 退回只认 ASCII 空格 | `'904' not found in by_round` ⇒ 正对照红，同时真账里 `79f7116` 又变成 unparsed |

**两把撤掉的空刀（不登记、不占号，反面事实进账）**：
- 把乙臂的 `forceLayer(view)` 摘掉 ⇒ 乙读到 0（与甲同），而 `乙 >= 甲` 与 `丙 > 乙` **两条都仍成立** ⇒ 这条链对"递归 wantsLayer"那一步不敏感（丙臂自己会把它建起来，M1502 的读数就是同一件事的正证）。
- 把 R571 那一格新加的前置摘掉 ⇒ **本机**读数逐字不变（本机冷态就能画）⇒ 这一把在本机是空刀，它的证人只能是 runner 那一跑。

下一轮从 **M1505** 起（现读本轮最高 M1504）。

## ⑦ 自我更正一笔（账上明写）

R571 我在账里写「runner 那台按它自己的实测会是 `容器高=28.0 按钮高=13.0 公式应发=24.0`（按钮高 13 是从 `序列=24.0` 反推的一档，本轮没有直接读到按钮高 ⇒ 具名未读到）」—— 现读推翻：**那一跑直接读到 `按钮高=16.0`**，13 是我反推错的。恒等式本身在两行上都成立（`序列 == 公式应发`：24/24 与 34/34），所以那一格的判法没坏，坏的是我反推出来的那个数。⇒ 这是 R571「把本机常量当普适下界」同一族的**第二次**：凡"反推"都不许当读数写进账，只能具名未读到（本轮已把这条写进 D-573）。

## ⑧ 禁碰与地板

- 产品 0 文件 ⇒ `SKIP_INSTALL=no-product-change`；禁碰 **14 面一字不增不减 ⇒ 不抬数**。
- 证人同笔：`git status --short ClipboardHistory/Sources` 空；`TRANSPARENCY_STATE isOpaque=0 窗口底色alpha=0.000 底衬=1 采样=39342 带内最小alpha=255 半透明样本=0/39342 洞范围=无` 与 `TRANSPARENCY_HITTEST 探针=3 空区命中=底衬0/容器3/内容0 底衬自身 hitTest=让位` **逐字未变**；帧 `CHANGED=0`（现读待抄）。
- 第三条证人 `均值差=0.0000 品红漏出=0` 属真机键那一档（`testGoingNonOpaqueDoesNotWashOutTheSidebarMaterial` 本轮仍是 skip，与 `testRealScreenChannelSeparatesOpaqueBlackFromTransparent`、`testTheWindowShadowFollowsTheVisibleShapeNotTheFrame` 同族）⇒ **本轮没有新读数**，具名未读到，不拿历史数冒充。
- 地板一条没动：4.5 / 150 / 120ms 与容差 1 / Motion ≥2 / 2x 8.0pt / 1x 6.0pt / `probeInkFraction=3%` / `.contentFade 0.20` / 声明时长 / 像素格 `容差 1.5` 与 `跳变地板 8`；离屏 alpha 那张登记表 `registeredOffscreenVerdict(scale:)` 一字未动（本轮也没有把任何登记值改 0↔1）；全量 skipped 只记现读。
- 仍红照实入账、不登记成不判：四支 `detail-*`、639、Motion 两朵，以及 **R571 那一格在 runner 上的真红**（本轮用（乙）去修它，修没修好要由含这一笔的那一跑说）。

## ⑨ 一处当场改掉的字面（通道值里的裸空格）

探针那三臂的标签原本写成 `甲 只根wantsLayer`（**值里带 ASCII 空格**）。落进判据时改成 `甲_只根wantsLayer`：
一行读数按空格切成「键=值」，值里带空格会让解析它的尺拿到一段没有 `=` 的 token（R565 的 `element #1 has length 1`
同一族），而 `scripts/ci_channel_hygiene.py` 第③格正是拦这个的。⇒ 上面 ③ 表里凡带空格的臂名都是**探针原文**，
判据里落的是**下划线版**。

## ⑩ 验证链现读（顺序没换，逐条抄自己那一行）

- 门：`ROUND_WARNING_GATE warnings=0 incremental=0 cold=0 target=build-tests`。
- 判据卷（`--filter UICaptureTests`，不带帧变量）：`Executed 227 tests, with 5 tests skipped and 0 failures @659.714s`；重捕那一遍：`227 tests, 4 skipped, 0 failures @837.596s` ⇒ skipped 在同一棵树上 5/4 之间漂（`testCaptureKeyViews` 那一格），**只记现读、不动门、不猜成因**。
- 帧：`FRAME_BASELINE_COMPARED=356 CHANGED=0 MISSING=0 ADDED=0` ⇒ **不跑 `frame_baseline.py update`**（帧真没变）。
- 透明卷整类（含本轮新格）：`Executed 16 tests, with 3 tests skipped and 0 failures @1.418s`；三朵 skip 全是真机键那一档（`testRealScreenChannelSeparatesOpaqueBlackFromTransparent` / `testTheWindowShadowFollowsTheVisibleShapeNotTheFrame` / `testGoingNonOpaqueDoesNotWashOutTheSidebarMaterial`）⇒ 与 ⑧ 第三条证人缺席同源。
- 刀：M1502 / M1503 / M1504 三把 **CAUGHT、RESTORE_CLEAN=yes**（标签改成无空格之后重跑过一遍，预检都先 PASSED）。
- 通道卫生：`CI_CHANNEL_HYGIENE ci脚本=14 电池脚本=73 电池引用=24 合计=99 绝对根=0 真人路径=0 通道空格=0` ⇒ `RESULT=ok`。
- 全量卷（本机，串行、不与别的 swift 卷叠加）：`Executed 1434 tests, with 60 tests skipped and 0 failures in 747.143 (747.231) seconds` ⇒ skipped **60** 只记现读。
- 三支预检（按 R558 的教训**串行**跑，避免 swift 构建锁撞成假 `NOT_RUN_TIMEOUT`）：
  `NEEDLE_PRECHECK tables=381 covered=302 arms=786 bad=0`；
  `HIDDEN_ARMS 表=468 可判=1212 rot=0 抽不出=6 已声明表=6 已声明死针=0 上界 rot=0 抽不出=6 处置=ok`；
  `CI_CHANNEL_HYGIENE … RESULT=ok`（同一分钟逐条读，见上一条）。
- 电池（台账落盘之后）：`Ran 720 / OK (skipped=5)` 共两趟 —— 第八趟 `@96.467s`（`battery8.log`，台账重复段截回之后）、第九趟 `@95.125s`（`battery9.log`，含 ⑨ 第六处自伤与 U-2512 那两处补账文字）。第二趟的数不回填进 STATE ⑧ 那一格（回填一次就要多签一次），最终那一棵由 runner 的 `STEP[9] Release script tests` 签。

## ⑪ 台账写坏与修复（不是新推进，是自我更正）

- 写手给 `AGENT_UI_AUDIT.md` 补 U-2512 那一行时，替换串是「`\n` + 那一行 + 从 anchor 起的全部内容」⇒ anchor 之后的整段被抄了两遍：文件 **15812 → 31281 行**，`git diff --stat` 打出 `15469 ++++`。
- 现读的三朵电池红（`battery7.log`）：`test_ui_audit_ids_are_unique`（**2256 个 U 号各定义两次**）、`test_mismatches_equal_the_named_roster`（`[103] != [81, 103]`；截掉重复之后同一格回落到在册的 `[103]` ⇒ 多出来的 `81` 确实是重复段造成的，具体是哪一节配错了 U 号区间我没有逐行复算）、第三朵 `test_the_roster_matches_what_this_machine_actually_skips` 是**借报**（它自己写对了：「红在内层不在这里」）。
- 修法：截回前 **15834** 行（= HEAD 的 15812 + R573 那一节 22 行），再用 `git diff --stat` / `grep -c "^-"` 验回**纯插入 +22、零删除**；`wc -l` 现读 15834。产品与判据一字未动 —— 这一族的形状是"记账的手写坏了账本"，不是尺红。
- 先前我在 STATE ⑧ 把第七趟写成"三格还没重新渲染、没有一朵是代码红"—— **那句是错的**，已按现读纠正（错在把"我读到的措辞问题"当成"红的原因"，而没有先逐条读那三朵红的 traceback）。

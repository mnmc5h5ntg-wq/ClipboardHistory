# R572 读数笔记（第 571 轮 / Round 569 · 2026-11-04 · 靶 = 折叠规格 §3 第②段 / 650）

## ① 身份与门（现读）

- UI_AUDIT 最新标题 = `## 第 570 轮（R571` ⇒ 本轮 **R572 = 第 571 轮 / Round 569**。
- 刀高水位现读 **M1498**（`mutate_r571` 表尾）⇒ 本轮从 **M1499** 起；本轮三把 M1499–M1501。
- `ROUND_WARNING_GATE warnings=0 incremental=0 cold=0 target=build-tests`。
- 产品面：本轮 `git status --short ClipboardHistory/Sources` **空** ⇒ 产品 0 文件。
- 点名账内冲突：dispatch 写「账上 `:150`」，现读那一格在 **`AGENT_STATE.md:149`**（`:150` 是「若用户给了 646 的口径」那条）。同一句内容 ⇒ 处置照 dispatch：那一格对 `41774543942` **不成立**，因为新通道 `captureTwoHalvesViaAlphaLayer` 只存在于 `2232069` 那棵树，而 `41774543942` 跑的是 `ecf8686` ⇒ **具名 `OFFSCREEN_ALPHA_LAYER_CHANNEL_ABSENT_IN_TREE=ecf8686`**，不读成绿、不读成红、也不拿本机 1x 那条读数顶替 runner 那一档（新通道没有跨机登记表）。

## ② ⓪ 两跑到数（只读、不改结论）

### `41774543942 ↔ ecf8686`（R570 补记笔）= `completed / failure`

全部失败步骤（逐条原样，不截断）：

```
RUN=41774543942 conclusion=failure
  JOB build-and-test ⇒ failure
    STEP[15] Swift tests (executed-count gate) ⇒ failure
    STEP[17] Capture gate (unregistered reds must be zero) ⇒ failure
    STEP[19] Motion coverage floor ⇒ failure
```

- 卷的数：**`Executed 1429 tests, with 89 tests skipped and 15 failures`**（全量卷）；判据卷那一遍 `Executed 227 tests, with 34 tests skipped and 14 failures`；`CAPTURE_GATE_RESULT=fail 有 1 个用例红了`；`ASSERTION_RED 行=19 去重后=16`。
- 红的用例名（去重后 6 个）：四支 `detail-*`（`testCaptionTextStaysOnTheSecondaryTier` / `testDetailAreaHasASingleLeftAxis` / `testActionableInkStaysAboveTheLegibilityFloor` / `testDetailStatusBarShowsTheRealSourceAppIconOnlyWhenAttributed`）+ `testQuickPickKeyboardHintClearsTheContrastFloor`（639）+ **`WindowChromeLayoutTests/testTheProductMainWindowPathPublishesACredibleInset`（我上一轮那一朵）**。
- `CHROME_PUBLISH_TRACE` 在这棵树上 **2 行**，逐字：
  `CHROME_PUBLISH_TRACE 路=产品主窗 容器高=28.0 序列=24.0 最小=24.0 可信下界=28.0`
  `CHROME_PUBLISH_TRACE 哨兵=10.0 发布次数=2 序列=34.0 最小=34.0 可信下界=28.0`
  ⇒ 这一格只能回答**旧判法**的那两行；R571 换的恒等式判法（`按钮高=` / `公式应发=` 两个字段）**不在这棵树上** ⇒ dispatch 第②格问的「`容器高=28.0 按钮高=13.0 公式应发=24.0` 这套恒等式在那台机器上成立吗」在这跑**没有直接读数**：能读到的是 `容器高=28.0 序列=24.0`，`按钮高`/`公式应发` 是 R571 那一笔才打的字段 ⇒ 具名 `IDENTITY_FIELDS_ABSENT_IN_TREE=ecf8686`。13 仍然只是从 24 反推的一档（不是读数）。
- `TRANSPARENCY_CHANNEL` **1 行**，而且只有旧通道那一条：
  `TRANSPARENCY_CHANNEL 通道=离屏 位图=200x120 倍率=1.00x hasAlpha=1 黑半区=(r0,g0,b0,a255) 透明半区=(r0,g0,b0,a0) 分得出=1 实测=保留 alpha 登记=保留 alpha`
  ⇒ 旧通道在 runner 1x 的登记值仍被它自己那一跑签着（`保留 alpha`）；新通道 `通道=离屏-alpha图层` 在这棵树上**一行都没有 = 通道不在那棵树上**（见 ①）。
- `CAPTURE_FOREIGN_WINDOW` **没有一行**，而这条通道**在这棵树上存在**（R569 的 `3535cad` 加的）⇒ 这是"通道在而没打"那一档 ⇒ **(甲)「捕获期间屏上有真实 app 内容窗」维持被否**。
- `CAPTURE_CHROME_INSET` **2 行**（与 R571 读到的同一形状，逐字重复）：
  `… settings-about light 兜底=35.000 值=35.000 判=与兜底一致 上一次=首拍`
  `… settings-about light 兜底=35.000 值=24.000 判=漂出兜底 差额=-11.000 上一次=首拍 ⇒ 这张帧量的不是产品默认几何，要去找漏还原的那一格`
- `MOTION_FLOOR_FACTS judged=4/5 executed=79 not-run=empty-state …红的用例=testDetailEmptyToContentCrossfadeIsMeasuredOrDeclaredBlind,…` ⇒ `executed=79`（有真读数，不是 `executed=0`）；另有 `MOTION_FLOOR_SUITE_RED=2`、`MOTION_FLOOR_SUITE_NOT_SEEN=2`、`MOTION_FLOOR_LOOP_NOT_JUDGED` ×2、`MOTION_FLOOR_BAD_REASON empty-state 的理由是 witness-snaps-here，而登记过的是 无 ⇒ 同一臂换了一种坏法 = 新缺陷`。
- `SKIP_ROSTER 键=github-runner 类=github-runner 内层Ran=720 内层skip汇总=4 解析=3 名单外=无 名册未跳=无`（第八次绿）。
- `FRAME_BASELINE_*` 73 行（对拍旧发布的那一步，形状与前几轮同）；`ON_SCREEN_PROBE` / `WARNING_COUNT` 通道没有行 ⇒ 那两步不打印这两个串（不是红）。

### `41783402475 ↔ 2232069`（R571 那一笔）= 现读 `in_progress`、`conclusion` 空

⇒ **复核未到**。新通道在 runner 1x 上那一档、以及 R571 换掉的恒等式判法在那台机器上绿不绿，**只能由这一跑作证**。不轮询、不读成绿、也不读成红。

## ③ 本轮真实推进 = 650（第②段还欠两件中、不需用户定向的那一件）

靶：那条两档一致的离屏通道（R571 建的 `captureTwoHalvesViaAlphaLayer`）对**产品真实视图树**算什么。两棵产品树分开判（合成夹具不再签字）。

### 一次性探针（四支，跑完即删，读数留在这里；同 R558 那一族的"不入库探针 ⇒ 结论只进账、不冒充判据"）

| 探针臂 | 读数（逐字） | 判 |
| --- | --- | --- |
| 主窗树 冷态（只给根 `wantsLayer`） | `子层=-1 … a0=504000 有墨=0`（2x） | 层树没建出来 ⇒ `layer.render` 画不出 |
| 主窗树 `container.displayIfNeeded` / `host.displayIfNeeded` / `window.displayIfNeeded` / `container.display` / `host.display` / 两人各 display | 六臂全部 `子层=-1 … 有墨=0` | **单次 display 都不够** ⇒ 排除"少一个 API 就叫醒了"这条路 |
| 主窗树 先走旧通道（`cacheDisplay`）再 render | `第1遍 不透明=20160/20160 透明=0` | 前置＝**必须真的画一遍**，之后新通道画得出、整幅不透明 |
| 浮层树 冷态 | `子层=-1 … a0=… 有墨=0` / 递归 `wantsLayer`+`display` 后 `不透明=176/20160` | 半醒：只画了 176 颗 |
| 浮层树 先走旧通道再 render | `不透明=2096/20160 透明=17185`（与旧通道**逐字同数**） | 前置之后两通道同一张图 |
| 行序探针（把旧通道当参照，两种假设各数一次异类） | `采样=20160 翻y异类=5002 不翻异类=0 翻y加翻x=5431 只翻x=1565` | **内存第 0 行就是顶行** ⇒ 我第一版的 `pixelsHigh-1-topY` 是自己造出来的差 |

### 落地的三格（`TransparencyForensicsTests`）与本机读数

- `testTheAlphaLayerChannelDrawsProductTreesWhereTheOldChannelDrawsThem`（同树同栅格逐点同类）
  `TRANSPARENCY_PRODUCT_ALPHA 树=主窗 通道=成对 前置=走过 位图=840x600 采样=20160 旧三分=20160/0/0 新三分=20160/0/0 逐点异类=0 旧有墨=16685 新有墨=20160`
  `TRANSPARENCY_PRODUCT_ALPHA 树=浮层 通道=成对 前置=走过 位图=840x600 采样=20160 旧三分=2096/16745/1319 新三分=2096/16745/1319 逐点异类=0 旧有墨=2117 新有墨=2117`
  `TRANSPARENCY_PRODUCT_ALPHA_DRIFT` 两行都是 `不透明差=0 全透明差=0 半透明差=0 逐点异类=0`
  ⇒ 两条通道对同一棵产品树**给同一张图** ⇒ 新通道对产品树保 alpha，且不是"少画"。
- `testTheAlphaLayerChannelKeepsRealTransparencyOfTheProductOverlayTree`（对象=产品树，不是夹具；含两种栅格各判一次"分得出"）
- `testTheProductMainTreeStillGivesTheAlphaChannelNoTransparentObject`（主窗今天**无透明对象**）
  `TRANSPARENCY_PRODUCT_ALPHA 树=主窗 判=无透明对象 采样=20160 全透明=0 不透明=20160 有墨=20160 逐点异类=0`
  `PRODUCT_MAIN_TREE_TRANSPARENT_OBJECT_NOT_JUDGED=backing-covers-whole-tree ⇒ 第③段有真透明区之后这一格必须重开`
- 前置缺席那一臂**只打点不判**（把仪器现状钉成契约是 R465 那一族）：
  `TRANSPARENCY_PRODUCT_ALPHA 树=主窗 前置=缺席 采样=20160 不透明=0 全透明=20160 有墨=0 ⇒ 这一臂的 a=0 不能当「alpha 归零」用`
  `TRANSPARENCY_PRODUCT_ALPHA 树=浮层 前置=缺席 采样=20160 不透明=178 全透明=18445 有墨=194 ⇒ 这一臂的 a=0 不能当「alpha 归零」用`

### 一条对 §4 原文的收窄（不是推翻，是限定对象）

旧通道"分不出真黑与透明"**不是通道的恒常性质，而是依对象而定**：同一个 2x、同一台机器 ——
对两半已知的自绘 `HalfBlackView` 读 `分得出=0`（读数逐字未变、登记表一字未动），
对 QuickPick 浮层那棵产品树读 `a0=16745`（看得见透明）。
⇒ §4 第三条那句"离屏帧判不了 alpha 归零"收窄为"对**自绘 NSView 那类对象**判不了"；改文档在先，原文留着。

## ④ 刀（M1499–M1501，三把全 CAUGHT、RESTORE_CLEAN=yes）

| 刀 | 打在 | 坏法 | 落刀后的读数 |
| --- | --- | --- | --- |
| M1499 | 尺（新通道唯一的缓冲） | `render` 前铺一层不透明黑（撤掉「不预先铺底」） | 浮层 `新三分=20160/0/0` vs 旧 `2096/16745/1319` ⇒ `逐点异类=18064` ⇒ 两格红（主窗那一侧不动 ⇒ 只动了一对量的一边） |
| M1500 | 尺（读法） | 内存行序当回底朝上（`topY` 再翻一次） | 浮层 `不透明差=142 … 逐点异类=5434` ⇒ 逐点同类那格红（**本轮真实自伤的形状**，第一版就是这么写的） |
| M1501 | 尺（前置） | 摘掉「先走一遍旧通道」 | 主窗 `旧三分=0/20160/0 新三分=0/20160/0` ⇒「找不到不透明探针」红；浮层 `逐点异类=1716` 红 |

下一轮从 **M1502** 起（现读本轮最高 M1501）。

## ⑤ 禁碰与地板

- 产品 0 文件 ⇒ `SKIP_INSTALL=no-product-change`（不打扰用户在跑的那扇窗）。
- 禁碰 **14 面一字不增不减** ⇒ 不抬数。证人（同笔给）：`git status --short ClipboardHistory/Sources` 空；本轮重捕帧 `CHANGED=0`（待现读）；`TRANSPARENCY_STATE` / `TRANSPARENCY_HITTEST` 读数逐字未变（待现读）。
- 地板一条没动：4.5 / 150 / 120ms 与容差 1 / Motion ≥2 / 2x 8.0pt / 1x 6.0pt / `probeInkFraction=3%` / `.contentFade 0.20` / 声明时长 / 像素格 `容差 1.5` 与 `跳变地板 8`。
- 离屏 alpha 那张登记表 `registeredOffscreenVerdict(scale:)` **一字未放宽**（仍只收 2x/1x，其余 `OFFSCREEN_ALPHA_NOT_RUN=unregistered-scale`）；本轮**没有**把任何登记值从 0 改成 1 或反之。
- 全量 skipped 只记现读：本机判据卷本轮 `227/5/0`（上一轮 227/4/0，多出来的是 `testCaptureKeyViews`），runner 那一跑 `1429/89/15` 是历史数 —— 两个都不是期望值。

## ⑥ 外部前提（只登记）

`security find-identity -v -p codesigning` 仍给 `1 valid identities found`（本轮未换装 ⇒ `INSTALL_SIGNATURE` 没有新读数，具名未读到）。633 仍等用户人工回执，不据此判结案。

## ⑦ 两支追加探针（也不入库，跑完即删）

- **探针 5（顺序摆错的那次，反面事实）**：把新通道放在旧通道**之前**跑 ⇒ 读到 `采样=20160 RGB逐字同=18171 alpha同=18231 四通道全同=18171`，分带是 `带1 异类=748（旧不透明=747 新不透明=4）| 带2 异类=1181（旧 1201 / 新 24）`，逐点探针 `旧通道 rgba=(220,220,220,255) / 新通道 rgba=(0,0,0,0)`。
  ⇒ 缺前置时新通道**少画的是选中行那层灰底**（肉眼可见：两张 /tmp 里的 PNG 一张有灰底、一张没有），而我把这个数一度当成"两通道只有 90% 相同"⇒ **顺序就是口径**，先旧后新才是判据里那个顺序。两张 PNG 与探针文件都已删除（帧与日志不留用户内容，夹具文本也不留）。
- **探针 6（按判据顺序重测）**：`浮层 顺序=先旧后新 采样=20160 alpha异类=0 alpha字节同=20160 四字节全同=20098 单通道最大差=11`
  ⇒ **alpha 那一通道两条路逐字节相同**；RGB 有 62 颗采样（0.3%）落在抗锯齿边缘带、最大差 11/255 ⇒ 第③段按 alpha 判「归零是否彻底」就够，不许拿四字节全等当门槛。

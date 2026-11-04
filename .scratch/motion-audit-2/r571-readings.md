# R571 读数笔记（第 570 轮 / Round 568 · 2026-11-04 · 靶 = 折叠规格 §3 第②段 §4 第三问）

## ① 身份与门（现读）

- UI_AUDIT 最新标题 = `## 第 569 轮（R570` ⇒ 本轮 **R571 = 第 570 轮 / Round 568**。
- 刀高水位现读 **M1494**（`mutate_r570` 表尾）⇒ 本轮从 **M1495** 起。
- `PRODUCT_STREAK ledger_round=569 streak=2`（只抄门，as-of 不含本轮）。
- `ROUND_WARNING_GATE warnings=0 incremental=0 cold=0 target=build-tests`。
- 点名的一处账内冲突：`AGENT_STATE.md:143`（R570 状态 ⑥ 把 R571 主线写成 (丙)+649/645）与 `:144`（靶 = 规格 §3 第②段）互相冲突 ⇒ **按规格与 `:144` 为准**，(丙)/649/645 本轮只在 ⓪ 里记数。

## ② ⓪ 两跑到数（只读、不改结论）

`41762634884 ↔ e92a0b0`（R569 台账笔）= **completed / failure**，失败步骤三朵：STEP[15] Swift tests、STEP[17] Capture gate、STEP[19] Motion coverage floor；success 的也逐格读了（STEP[4]/[5]/[9]/[11]/[16]/[18]）。
- `CAPTURE_CHROME_INSET` 在这份日志里 **0 行** —— ⚠ 这条"0 行"的**含义要说清**：那条通道是 R570 的 A 笔（`771757f`）才加的，`e92a0b0` 那棵树上根本没有它 ⇒ 这是"通道不在那棵树上"，**不是**"读数为 0"。（R569 那一族第三次遇到"命令成功、输出为空"的三种坏法之一。）
- `CAPTURE_FOREIGN_WINDOW` **0 行**（这棵树有这条通道）⇒ **(甲)「捕获期间屏上有真实 app 窗」维持被否**。
- 登记表那一格逐字：`TRANSPARENCY_CHANNEL 通道=离屏 位图=200x120 倍率=1.00x hasAlpha=1 黑半区=(r0,g0,b0,a255) 透明半区=(r0,g0,b0,a0) 分得出=1 实测=保留 alpha 登记=保留 alpha`。

`41773794616 ↔ 1e8dd15`（R570 台账笔，**第一跑含 R570 那五格新判据**）= **completed / failure**，失败步骤同样三朵（STEP[15]/[17]/[19]）。
- **`CAPTURE_CHROME_INSET` 打了 2 行，两行的值不一样**：
  `CAPTURE_CHROME_INSET settings-about light 兜底=35.000 值=35.000 判=与兜底一致 上一次=首拍`（STEP[5] 那一批）
  `CAPTURE_CHROME_INSET settings-about light 兜底=35.000 值=24.000 判=漂出兜底 差额=-11.000 上一次=首拍 ⇒ 这张帧量的不是产品默认几何，要去找漏还原的那一格`（STEP[15] 全量卷那一批）
  ⇒ **第一次拿到"坏的那批确实带着一个不同的 inset"的直接读数**，而且两行都写 `上一次=首拍` ⇒ 是两个进程各自的首拍 ⇒ 全量卷那个进程在**第一张帧之前**就已经是 24 了。
- `CAPTURE_FOREIGN_WINDOW` 在这棵树里仍 **0 行** ⇒ 泄漏的不是"窗还开着"，是"窗留下的值"。
- 全量卷 `Executed 1429 tests, with 89 tests skipped and 15 failures`（上一跑 1424/89/14 ⇒ +5 格用例、**+1 朵红**）。
  ⚠ **那多出来的一朵是我自己上一轮带的**：`WindowChromeLayoutTests/testTheProductMainWindowPathPublishesACredibleInset`
  逐字 `XCTAssertGreaterThanOrEqual failed: ("24.0") is less than ("28.0")`，配的那行读数 `CHROME_PUBLISH_TRACE 路=产品主窗 容器高=28.0 序列=24.0 最小=24.0 可信下界=28.0`
  ⇒ 我把"可信"写成了**本机**的固定下界 28（= 本机 32/14 那一档），而 runner 那台的标题栏容器实测 28 ⇒ 发布 24 是它自己的合法实测值 ⇒ **我把一台合法机器读成了产品缺陷**。本轮改成与机器无关的两条判法（恒等式 + 容器高 ≥ 按钮高），见 ④。
- 同跑的 `INSET_CAUSAL`（本机因果实验在 runner 上的读数，五档）：
  `拿不到容器 10.0 差=-25.0 带墨=0.0%` / `半高 20.0 差=-15.0 带墨=0.5%` / `无工具栏实测档 28.0 差=-7.0 带墨=4.7%` / `带工具栏下沿 35.0 差=+0.0 带墨=12.4%` / `灯更高-上平台 41.0 差=+6.0 带墨=6.2%`，
  `INSET_CAUSAL_MIN_DELTA 最小可坏位移=-15.0 发布=20.0 容器高=24 按钮高=14 带墨=0.5%`，五档**列墨逐字 4457px**（本机是 16144px）。
  ⇒ **上一轮那句"量级障碍"被这跑推翻一半**：在 runner 上 Δ=−15 就已经把带子清到 0.5%（本机要 Δ=−25 才 0.0%），
  而 runner 的真窗实测发布的就是 **24（Δ=−11）** ⇒ (甲) 的机制在那台机器上是**可达的**，本轮不许再把它写成"量级上站不住"。
  ⇒ 但 `CAPTURE_FOREIGN_WINDOW=0 行` + R569 的还原已落地 ⇒ 剩下的具体形态是"**值留下了，窗没留下**"：某一格建完真窗把 24 发出去、还原没覆盖到这条路径（或还原发生在捕获批之后）。这一条属 (丙) 的候选清单，本轮按 ① 只记不追。
- STEP[19] `MOTION_FLOOR_FACTS judged=4/5 executed=79 not-run=empty-state … 红的用例=testDetailEmptyToContentCrossfadeIsMeasuredOrDeclaredBlind,testEmptyStateStillFadesWhenMotionIsReduced 汇总行报红=2` ⇒ 有真读数（不是 `executed=0`）。
- STEP[9] `SKIP_ROSTER … 名单外=无 名册未跳=无`（第七次绿）；639 **第九次**逐字同值 `light 3.84:1 / dark 5.08:1 倍率=1.0x`；643 第十三个数 `带中位=6.37ms 整窗中位=11.49ms 省=1.81×`（与第十二个数同值）；STEP[11] success、working manifest `MISSING=0`。

`41774543942 ↔ ecf8686`（R570 补记笔）现读 **in_progress、conclusion 空** ⇒ 那一格照实写「复核未到」，不轮询、不读成绿。

## ③ 外部前提现读（只登记，不结论）

`security find-identity -v -p codesigning` 现读：
`1) 5F6C0955D4543282F5B2B12A3A2B9FB9FF5CE0A7 "ClipboardHistory Local Signing"` + `1 valid identities found`
⇒ 与 R553 那次的 `CSSMERR_TP_NOT_TRUSTED` 相反，**信任链前提可能已到**。本轮产品 0 文件 ⇒ 不换装 ⇒ `INSTALL_SIGNATURE` 那一行**本轮没有新读数**（具名未读到，不拿历史读数冒充）。633 仍等用户人工回执，不据此判结案。

## ④ 本轮真实推进：第二条离屏通道（规格 §4 第三问 / 646 第一条出路）

**旧值（改之前，本机 2x 复现）**：`TRANSPARENCY_CHANNEL 通道=离屏 位图=400x240 倍率=2.00x hasAlpha=1 黑半区=(r0,g0,b0,a255) 透明半区=(r0,g0,b0,a255) 分得出=0 实测=涂成不透明黑 登记=涂成不透明黑`
**新通道（同一台机器、同一次运行、两种栅格）**：
```
TRANSPARENCY_CHANNEL 通道=离屏-alpha图层 位图=400x240 倍率=2.00x 黑半区=(r0,g0,b0,a255) 透明半区=(r0,g0,b0,a0) 分得出=1
TRANSPARENCY_CHANNEL 通道=离屏-alpha图层 位图=200x120 倍率=1.00x 黑半区=(r0,g0,b0,a255) 透明半区=(r0,g0,b0,a0) 分得出=1
```
⇒ **两档一致**，且栅格是我自己给的（不再问 AppKit 要 backing store）⇒ §4 第三问从"依倍率而定"变成"有一条通道两档都能区分"。

诊断臂逐条排除（这些读数是"为什么是这一条"的证人；诊断臂本身**不入库**，按规矩只在这里留数）：
| 候选取图路 | 读数 | 判 |
| --- | --- | --- |
| A `bitmapImageRepForCachingDisplay` + `cacheDisplay`（旧通道） | `格式=0 透明半区 a=255 分得出=0` | 没有 alpha 平面 |
| B 非不透明窗 + `cacheDisplay` | 同上（a=255） | 换窗不换格式 |
| C 自建 `alphaNonpremultiplied` 位图喂给 `cacheDisplay` | 四个采样点全 `(0,0,0,a0)`，连黑半区也是 | `cacheDisplay` 不往里写 |
| D `layer.render(in:)` 但图层默认 | 两半都 a=255 | 铺过底/被涂实 |
| E/F/G/H/I `isOpaque=false` 的视图 / 透明窗 / hosting / 判据卷全套 | 全 a=255 或全 a=0 | 都不是那条路 |
| J 把 A 的位图再画进 alpha 上下文 | 全 a=0 | 上游没信息，下游救不回来 |
| K `dataWithPDF(inside:)` 再栅格化 | 只有我铺的品红留下 | 产品那棵树画不出 |
| M `NSHostingView.draw(_:)` 进 alpha 上下文 | 全 a=0 | SwiftUI 不在 `draw(_:)` 里画 |
| **P `layer.render(in:)` 进 `premultipliedLast` 上下文、不铺底** | **黑 a=255 / 透明 a=0** | **落地的就是这条** |

另一条读法上的坑（同批诊断）：同一条通道上 `NSBitmapImageRep.colorAt` 把 raw `a=255` 的那个点读成 `a=0` ⇒ **像素必须读原始字节**，否则会把"保住了 alpha"读成"整幅全透明"（那是一条会自我庆祝的假绿）。

## ⑤ 刀（M1495–M1498，四把全 CAUGHT、RESTORE_CLEAN=yes）

| 刀 | 打在 | 坏法 | 读数 |
| --- | --- | --- | --- |
| M1495 | 尺（新通道） | 渲染前先铺一层不透明底（= 旧通道的等效行为） | 两档都退回 `透明半区 a=255 分得出=0` ⇒ 红 |
| M1496 | 尺（探针内容） | 黑半区也画成 `Color.clear` | `黑半区 a=0` ⇒ 正对照那一格红 |
| M1497 | 尺（读法） | alpha 从 `bytes[o+2]`（B 通道）读 | 两半都 a=0 ⇒ 红 ⇒ 钉住"真的在读 alpha 平面" |
| M1498 | **产品** | `noteTrafficLights` 把发布值夹到 20 | 恒等式红（`公式应发=28.0 序列=20.0`） |

**两把撤掉的空刀（不登记、不占号，反面事实进账）**：
- `hosting.layer?.isOpaque = true` ⇒ 读数逐字不变（两档仍 `分得出=1`）⇒ **保 alpha 的杠杆不在图层的 isOpaque 上**。
- `bitmapInfo = noneSkipLast` ⇒ 读数逐字不变 ⇒ **也不在 bitmapInfo 那一位上**（CoreGraphics 仍把跳过的 alpha 字节按覆盖率写回）。
⇒ 真正的杠杆是"**这块缓冲没有预先铺底**"（M1495 钉的就是它）。

## ⑥ 本轮还的上一轮自伤

`testTheProductMainWindowPathPublishesACredibleInset` 的"可信下界"从固定 28 换成两条与机器无关的判法：恒等式（发布值 == 公式对本次实测算出的值）+ 可信性（容器高 ≥ 按钮高）。本机读数 `容器高=32.0 按钮高=14.0 公式应发=28.0 序列=28.0`；runner 那台按它自己的实测会是 `容器高=28.0 按钮高=13.0 公式应发=24.0`（按钮高 13 是从 `序列=24.0` 反推的一档，本轮没有直接读到按钮高 ⇒ 具名未读到）。M1498 钉住恒等式。

# AGENT_VISUAL_ITERATION · 视觉与动效自主迭代记录

目标（用户 2026-10-13 定的）：在**不破坏功能**的前提下连续迭代，把视觉与动效做到
"Apple 原生、流畅、华丽但克制、细节相当丰富"。每轮必须产出可编译代码 + 自评打分，
低于 90 分继续修；连续五轮 ≥90 且无 P0/P1 回归才停。适配 macOS 12 + 本机。

本文件是每轮的**唯一现场记录**：设计令牌 / 已完成 / 未完成 / 风险 / 下一轮。
仓库级的决定与教训仍然记在 `AGENT_DECISIONS.md`（D-0xx），视觉账记在 `AGENT_UI_AUDIT.md`（U-xx）。

---

## 设计令牌（R1 起生效；之后所有轮次只能引用，不许再写数字字面量）

| 族 | 令牌 | 值 | 为什么是这个数 |
|---|---|---|---|
| 圆角 | `VisualRadius.chip` | 4 | 16pt 级小方块与 8pt 骨架条带；4 已是半高，再大成药丸 |
| | `VisualRadius.control` | 6 | 24pt 可点胶囊；"明确是圆的"且还没假装是 `Capsule` |
| | `VisualRadius.track` | `control + 1` = 7 | 轨道必须比滑块大 1pt，同值时内层角会切进外层描边 |
| | `VisualRadius.card` | 8 | 30pt 级装内容的表面；对齐系统那类圆角容器 |
| | `VisualRadius.panel` | 9 | 整块区域的表面（落点框、设置侧栏行）；沿用现状不抬到 10 |
| | `VisualShape.rounded(_:)` | 唯一出口 | 永远 `.continuous`（squircle），杜绝"圆弧接直线"那套曲率语言 |
| 线宽 | `VisualHairline.edge / rule / divider` | 0.5 / 0.7 / 1 | 贴边发丝 / 玻璃与 hover 描边 / 胶囊内实心分隔 |
| | `VisualStroke.highlight / highlightDash / glow` | 1.5 / [4,3] / 3 | 落点虚线框 / 段与间隔近等长 / 过模糊后还剩一圈 |
| 投影 | `VisualShadow.flat` | black 0.08 · r1 · y0.5 · 不分组 | 缩略图只要一点边；分组会给**每一行**多一次离屏合成 |
| | `VisualShadow.raised` | black 0.10 · r8 · y3 · **必分组** | 材质是独立图层，不分组就每层各打一次阴影 |
| 底色 | `VisualFill.hover / controlHover / fieldIdle / fieldActive / selected` | 0.06 / 0.10 / 0.035 / 0.06 / 0.16 | 收掉 0.045/0.06/0.07 三档；按钮面积小要更实；持久态必须重于瞬时态 |
| 描边 | `VisualTint.chipStroke / fieldIdleStroke / fieldActiveStroke / hoverStroke / glassBorderTop / glassBorderBottom / dropTargetStroke` | 0.15 / 0.05 / 0.10 / 0.07 / 0.20 / 0.07 / 0.60 | 缩略图 0.16 与 0.14 并排不一致；输入框"底色与描边各抬一档" |
| 材质 | `VisualMaterial.window / glass / sliderPill / track` | thick / ultraThin / ultraThick / quaternary | 窗口底最实、浮起玻璃最薄、滑块要凸起来 |

**令牌的规矩**（由 `VisualTokenTests` 钉住，不是靠自觉）：
1. 视图里不许出现 `RoundedRectangle(cornerRadius:` / `.shadow(color:` / `lineWidth: <数字>`；
2. 每个令牌必须有产品代码读它（判据自己读不算消费者）；
3. `Views/` 里每个 `struct X: View` 必须有构造点（死表面直接红）；
4. 半径的嵌套次序、状态强度的次序是**语义约束**，改数值要先把约束改对。

---

## Round 1 · 几何与材质令牌

**做了什么**：R0 审计数出的 6 种圆角、3 种发丝线、4 处投影、3 档悬停底色全部收口到
`Utilities/VisualTokens.swift`；顺带删掉两个死表面、补一句违反自家规范的字号。

改动 13 个文件 + 新增 2 个：`VisualTokens.swift`（新）、`VisualTokenTests.swift`（新）、
`ThumbnailView` / `SkeletonShimmer` / `SearchField` / `GlassControls` / `VideoPreview` /
`HistorySidebarView` / `SettingsView` / `DetailView` / `DetailPreviewViews` / `ViewExtensions` /
`HistoryRowViews` / `SystemSymbolValidityTests` / `MotionCatalogTests`。
`HistoryStore` 零改动（守卫 `testHistoryStoreStaysThin` 仍绿）。

**顺带修的三个缺陷**（都不属于"锦上添花"）：
- `GlassCircleButton`：产品零调用点，只被一条测试当符号名字夹具养着 ⇒ 删除，
  连带删掉只有它一个消费者的 `hasOwnSurface` / `showsBorder` / `GlassBorder.isHovered` 三个死参数；
- `HistoryRow`：注释写着"保留给夹具与详情以外的调用点复用"，实测**产品与测试都没有调用点** ⇒ 删除；
- 视频控件的投影漏了 `.compositingGroup()` ⇒ 现在由 `VisualShadow.raised` 自带，写不出来了。

**验证**（全部现场，不是设计意图）：
- `swift build`：0 warning 0 error；
- `swift test`：**600 例 / 23 skipped / 0 failures**（HEAD 同口径实测 589 个 `func test`，本轮 +11 条判据）；
- 离屏帧：**82/82 拍全，28 帧有变化**（14 对深浅），已 `frame_baseline.py update` 并与改动同提交；
- 28 帧的归因（先取 HEAD 内容在同一台机器上重采一份，再逐像素 diff）：

| 帧组 | 变化像素 | 最大通道差 | 归因 |
|---|---|---|---|
| `search-field-*` | 663–678 | **1** | 激活描边 0.095 → 0.10 |
| `row-file / row-file-thumb / row-files / row-image` | 206–894 | 2–8 | 缩略图角改 `.continuous`、描边 0.16/0.14 → 0.15、投影 0.06 → 0.08 |
| `sidebar-*` / `content-*` | 451–1188 | 1–8 | 同一批缩略图 + 搜索框描边（这些帧含侧栏） |
| `detail-2-file-*` | 2650–2767 | **124–127** | bbox (633,288)-(805,312) = 86×12.5pt 一行字 ⇒ **加载那句 12pt → 13pt**（`StatePresentation.messageFontSize`），是本轮刻意要改的那一句 |
| `glass-pill-*` | 不在变化列表 | — | **像素完全不变** ⇒ 玻璃那几处重构是等值的（删的是无人走的分支） |

- 判据承重：10 支变异体 **10/10 CAUGHT**（每支都红在该红的那条，且先跑了一次"不改任何东西必须绿"的基线自证）；
  第一轮脚本曾 0 支有效：`python3` 在本机注入 `SDKROOT` ⇒ 每个变异体都编不过，全部判成 `DID-NOT-RUN`（不是红也不是绿）；
- 动效套件：见下（A/B 现场）。

**自评：80 / 100（<90 ⇒ 按规矩直接进下一轮，不等确认）**

| 维度 | 得分 | 为什么是这个数 |
|---|---|---|
| 原生感 | 17 / 20 | 圆角、发丝线、投影、材质第一次说同一种语言（全是 squircle、都是系统材质名、线宽按用途分档）；但按压态、焦点态、玻璃边缘高光还没做，"像系统"只做到了几何那一半 |
| 流畅度 | 16 / 20 | 没有回归（三臂 A/B 证明本轮不是变差的那一臂），但也没新增任何流畅性；动效套件目前无法确认，这一项不能按"更好"记分 |
| 层次与材质 | 12 / 15 | 材质有了唯一作者（窗口 / 玻璃 / 滑块 / 轨道四档各就各位），轨道半径改成派生；还缺"浮起 vs 贴平"的层次差（R4/R5 的主题） |
| 动效细节 | 10 / 15 | 本轮**刻意没动**动效：目录 8 档全部原样，两处目录外弹簧只数成判据没迁移。细节丰富度没有增长 |
| 交互反馈 | 7 / 10 | 悬停从三档收成一行话（0.06 / 圆形控件 0.10），反馈强度不再是各写各的；但按压态为零、复制脉冲还没做 |
| 可访问性 | 9 / 10 | VoiceOver 标签一字未动、状态文案接回规范的 13pt、两个会让人误判的死表面删掉；焦点环与按键可见性留给 R3 |
| 性能 | 9 / 10 | `flat` 故意**不**分组合成（否则每行多一次离屏合成，而列表滚动是这个 App 最贵的路径）；新增的一次分组落在很少画的视频控件上；热路径零新增 |

扣掉的 20 分全部扣在同一个事实上：**这一轮做的是地基（收口 + 减法 + 判据），不是可见的华丽**。
从 R2 起每一轮都要有"肉眼看得出来变了什么"的产出，并同时把分数往上推。

### 下一轮（R2）主题：把动效判据与采样率解耦（测量完整性）

理由：动效套件的判据用**绝对帧数**表达（"过渡帧数 ≥3""第 3 帧之后残余 <0.15"），
而采样间隔在 31–90ms 之间漂 —— 90ms 时一段 150ms 的过渡**算术上就不可能**给出 3 帧。
三臂交替（R1 全绿 → HEAD 两条红 → R1 另一条红）已经证明这是尺子而不是产品。
ab7a759 明确禁止"调到绿为止"，所以 R2 做的是**换判据的表达方式**：

1. 分辨率感知：`可分辨帧数 = floor(声明时长 / 实测采样间隔)`，要求
   `min(3, 可分辨帧数)` 且**地板 2 帧**（一帧跳变在任何采样率下都必须红）；
2. "落定残余"那两条把 `after: 3`（帧号）换成按 `duration/2` 推出的**时刻**，
   并在 `采样间隔 ≥ 时长` 时大声报 `MOTION_NOT_RUN=clock-too-coarse` + skip，而不是判红；
3. 每条都要带变异对照：`animationsEnabled=false` 那一臂必须红（不许变成 skip）、
   曲线开着且时钟够细时必须绿 —— 两个方向都验，否则"改成时间表达"只是把红搬到别处。

**R3 及以后**（原路线图顺次后移）：R3 排版与间距节奏（10 档字号收成一族 + 空态两套统一）、
R4 按压态与焦点态（含把已知红 `testSidebarListFocusRingAfterClick` 转正）、
R5 悬停与选中层次、R6 玻璃边缘高光、R7 内容类型层次、R8 搜索与空状态、R9 复制脉冲与回执、
## Round 3 · 字号刻度与一处层级倒置

**改了什么**：R0 数出来的是 8 个文本字号（9 / 10 / 11 / 12 / 13 / 14 / 15 / 16）与 5 个大符号
（28 / 32 / 36 / 40 / 48）。现在文本只有 4 档（`meta 11 · row 12 · body 13 · title 14`），
符号 7 个具名角色（`badge 10 · chipSymbol 11 · rowIcon 14 · control 16 · emptyCompact 28 ·
state 36 · emptyPane 40 · placeholder 48`）。`body` **引用** `StatePresentation.messageFontSize`
而不是抄一个 13 —— 两处各写一个"同样等于 13"的数，正是"三处对齐"散掉的老路。

**其中两处不是"风格统一"，是能看出来的缺陷**：

1. **侧栏头部层级倒置**：区块标题"时间剪史"是 14，而右边那句"15 条记录"是 **15** ——
   次要信息比标题还响一号。现在计数降到 `body 13`，标题保持 14。
2. **"固定"徽标 9pt**：`pin.fill` 在 9pt 下笔画并成一片，而它表达的是"这条被钉住了"。
   9 与 10 收成同一档 `VisualGlyph.badge = 10`（同时是全 App 的下限，写进判据）。
   另两处 32/36 的状态图标、15/16 的播放条符号也各收一档。

**20/82 帧有变化，逐组归因**（与 R2 那份帧对比，`frame_audit.py diff`）：

| 帧组 | 变化像素 | 最大通道差 | 归因 |
|---|---|---|---|
| `row-pinned-on-*`（只有"已固定"那一版） | 130 | 145 / 165 | 徽标 9 → 10。**未固定的行不在变化列表里** ⇒ 改动只落在它该落的地方 |
| `sidebar-history / favorites / no-results` | 1626–2006 | 124–127 | 头部计数 15 → 13 |
| `content-min / wide / with-history / with-notice` | 1946–2006 | 28–125 | 同一句计数（这些帧含侧栏） |
| `content-empty / no-results` | 7114–7232 | 124–251 | 计数 + 详情空态标题 14 → 13（统一回规范字号） |
| `detail-*`、`glass-pill-*`、`search-field-*` | 不在变化列表 | — | 这些表面的取值一个没动 |

**判据**：`testTextSizesComeFromTheScale`（Views 里出现 `.font(.system(size: 数字` 打红，
正向对照是"至少 35 处在读刻度"）、`testTypeScaleIsMonotonicAndNeverBelowTheLegibilityFloor`
（次序 + 10pt 下限 + `body` 必须引用规范本体）。

**这一轮被变异对照抓到两个"假守卫"，都值得记**：
- **P3 逃逸**：往 `VisualFill` 里塞一个没人读的 `control`，守卫照样绿 ——
  因为它按名字查消费者，而 `VisualFill.controlHover` 含前缀 `VisualFill.control`。
  修成**按族 + 标识符边界**查（`reads(_:name:in:)`），并给它一条自证用例
  （前缀命中必须 false、真命中必须 true、行尾命中必须 true）。
- **P4 逃逸**：把 `body = StatePresentation.messageFontSize` 改成 `= 13`，
  那条"必须与规范相等"的断言打不红 —— 因为 13 就等于 13。**数值断言证明不了来源**；
  改成扫源码看那一行到底引用了什么。
- 顺带一次自伤：新断言里用了 `try!` 读文件，路径算错（少上一级）⇒
  **整个测试二进制当场 fatal 崩溃**，12 条用例的汇总直接消失。守卫找不到被守卫的东西时
  必须 `XCTUnwrap`/`XCTFail`，不许 `try!` —— 崩溃会把"有一条红"伪装成"全都没跑"。

**自评：88 / 100**

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 18 / 20 | 字号第一次有"刻度"而不是各写各的；层级倒置修正后侧栏头部读起来对了。仍缺按压/焦点态 |
| 流畅度 | 18 / 20 | 未动时序；R2 的度量结论沿用（`detail-kind-change`、`empty-state` 各 3 帧在动） |
| 层次与材质 | 13 / 15 | 文本层级从 8 档收到 4 档且次序被钉住；材质沿用 R1 |
| 动效细节 | 12 / 15 | 未新增 |
| 交互反馈 | 7 / 10 | 未新增（按压态留给 R4） |
| 可访问性 | 10 / 10 | 9pt 徽标抬到 10（下限写进判据）；空态标题统一到规范 13；读屏路径零改动 |
| 性能 | 10 / 10 | 产品零热路径改动；两条新守卫是纯文本扫描（毫秒级） |

**遗留**：间距节奏（padding 一族）本轮没做，挪到 R4 与按压态一起；
`DetailTypography` 的 11/14 与 `StatePresentation` 的 12/13 仍是**另两个作者**，
本轮只保证"Views 不再写数字"，跨文件的合并要一次带帧复核的专门改动。

---

R10 滚动与层次（把帧间隔 p95 压回 20ms）、R11 收尾与规范。

### 遗留 / 未完成
- `MultiFilePreviewLayout.animation`（12/13 走 `interactiveSpring` damping 0.88）与
  `FilterPillMotion`（damping 0.72）**仍在目录之外且有过冲** —— 本轮只把它们数成判据
  （`testMotionParametersOutsideTheCatalogAreWhitelisted`，文件集合相等，加例外要红），
  迁移要单独一轮，因为改曲线会动像素与手感。
- 帧捕获里没有视频控件那处（`VideoPreview` 无夹具帧）⇒ 那条 `.compositingGroup()` 的修复只有源码级证据，**没有像素证据**。

---

## Round 2 · 把动效判据与采样率解耦（测量完整性）

**这一轮为什么不先做"看得见的好看"**：R1 收尾时动效套件是红的，而三臂交替证明红来自尺子
（同一台机器、同一份代码：R1 全绿 → HEAD 两条红 → R1 另一条红）。在一个"绿不表示验到了"的
底座上做十轮视觉，等于把后面九轮的自评都建在沙子上。所以 R2 先修尺子。

**改了什么**（全部在 `MotionFilmstripTests.swift` + CI 那一步的汇报行，**产品代码零改动**）：

| 原来 | 现在 | 为什么 |
|---|---|---|
| `transitionFrameCount ≥ 3` | `≥ min(3, 可分辨帧数)`，可分辨 = `floor(声明时长 / 实测采样间隔)`；切不出 2 帧 ⇒ `MOTION_NOT_RUN=clock-too-coarse` | 90ms 采样时一段 150ms 的过渡**算术上不可能**给 3 帧。原来的写法量的是抓帧耗时 |
| 判据里的 `after: 3`（第 3 帧） | 锚点改成**触发那一帧**（`Film.triggerFrame` + `motionFrames`），否定判据 `after: 1`、阳性对照取 `midFlightPreRollFrames`（过渡中点） | 预卷长度随负载漂；"第 3 帧"在 31ms 与 90ms 下是两个不同时刻 |
| `settleFrames(after: 3) ≤ 6` | `settledAtFrame`（最后一次还在动之后那一帧）× 实测间隔 ⇒ **毫秒**，上限 = `声明 ×2 + 一个采样间隔` | "6 帧"在 31ms 下是 186ms、在 90ms 下是 540ms —— 同一个数字一边松一边紧 |
| 无 | `premisePictureChanged`：触发前后必须**逐像素不同**，否则 `MOTION_NOT_RUN=premise-not-visible` | 见下面的发现 |
| CI 结论行只有 `MOTION_SUMMARY` | 加 `MOTION_RESOLVE_SUMMARY judged=n/m not-run=…`（并给它一个新的自检形状） | 一次"3/3 全绿"和一次"只判了 1 条"原来长得一模一样 |

**修尺子修出来的一个发现（比尺子本身更值钱）**：`notice-banner` 这一卷**首尾逐像素相同**，
中段 3 帧变了又回来（整窗差距 `[0.000, 0.222, 0.222, 0.067, 0.000, …]`），
而模型里提示条一直在 —— 全仓只有 `dismissPasteFailure()` 会清它，没有任何计时器、没人调它。
⇒ 离屏 `cacheDisplay` 抓不到"落定之后的那条横幅"。
所以以前那句 `MOTION_SUMMARY notice-banner=3` 被读成"横幅插入动画量到了 3 帧斜坡"，
**其实那 3 帧是一次抖动**：起始态与落定态相同，中间那几帧不能算在过渡头上。
现在这条判据在这个场景上明确报 `premise-not-visible` 并 skip（本机 2/3 有内容），
而不是继续给一个读起来像证据的数字。这是**覆盖面退了一步、可信度进了一大步**。

**判据的判别力**（8 支变异，8/8 CAUGHT，先跑"什么都不改必须绿"的基线自证）：
可分辨地板 `>=2`、细时钟不放松（`min` 改 `max`）、`settledAtFrame` 的 `lastIndex`→`firstIndex`、
把 `after: 3` 抄回来、中点取样永不 nil、锚点被忽略（`motionFrames` 返回整卷）、
前提检查恒真、前提检查恒假。**每条都有合成帧的独立用例**（不开窗口、不看时钟），
所以粗时钟下"窗口那条自己 skip 了"不会让度量错误逃掉。

**验证**：`swift test` **605 / 23 skipped / 0 failures**（R1 后 600，本轮 +5）；
`CLIPBOARD_HISTORY_UI_MOTION=1` 那 18 条 **0 failures / 3 skipped（每条都带 not-run 原因）**；
离屏帧 `FRAME_BASELINE_CHANGED=0`（82 帧采齐）⇒ 本轮**视觉上完全惰性**，这是它应有的样子；
CI 汇报自检 14 个形状全过（新增 1 个）；`scripts/tests` 全绿。

**自评：85 / 100**（17+18+12+12+7+9+10；<90 ⇒ 继续，不等确认。
这一轮的分低在"界面上没有任何新的细节"，而它换来的东西不在外观分里：后面每一轮的动效分数从此可信）

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 17 / 20 | 本轮不碰外观（不加分也不掉分）；沿用 R1 的令牌语言 |
| 流畅度 | 18 / 20 | 没有新增动效，但**第一次**能分辨"哪条过渡真的被量到了"：`detail-kind-change` 与 `empty-state` 在 20–53ms 采样下可分辨 3/8 帧、实测各 3 帧在动；`notice-banner` 诚实标为未覆盖 |
| 层次与材质 | 12 / 15 | 未动 |
| 动效细节 | 12 / 15 | 度量精度本身提升一档（毫秒表达 + 中点取样 + 前提检查），但界面上没有任何新的细节 |
| 交互反馈 | 7 / 10 | 未动 |
| 可访问性 | 9 / 10 | 判据不再把"看不见"报成"没做"，也不把抖动报成证据；VoiceOver 路径零改动 |
| 性能 | 10 / 10 | 产品零改动、帧零变化；新增的都是纯函数与合成帧用例（毫秒级） |

**遗留 / 下一轮**
- `notice-banner` 场景在离屏抓取下**看不到落定态**：要么换成"开场就带着提示条、判其淡出"，
  要么给 `cacheDisplay` 找一个能拍到已提交图层的入口（`display` / 真窗口截图）。本轮先如实标 not-run。
- 两条 `MOTION_NOT_RUN=app-not-active`（AppKit 行动画要激活进程）仍在；R4 做按压态时会撞上同一个前提问题。
- 帧间隔 p95 超线（已知红）留给滚动那一轮。
- **R3 主题**：排版与间距节奏（10 档字号收成一族、空态两套统一、9pt 徽标复量对比度）。

---

## Round 4 · 按压态（R0 审计里这件事是零）

**改了什么**：新增 `Views/PressableStyle.swift` —— `PressedStyle`（一个真正的 `ButtonStyle`）
把 `configuration.isPressed` 翻成 **缩放 0.97 + 一档比 hover 更重的底色（0.12）**，
时长用 `.hover` 那档 0.12s。接上 9 处：详情浮层四颗图标按钮、行首星标、筛选段、
Markdown 切换、多文件行、设置侧栏行、搜索框清除、视频播放与静音。
新增 `MotionCatalog.pressScale` 与 `VisualFill.pressed`（参数仍然只有一个作者）。

**两处刻意不接，理由写在代码旁边**：菜单栏推荐项与它的收尾按钮 ——
系统菜单自己的高亮就是"收到了"的证据，再叠一层自绘底会把第三轮 U-1 刚拆掉的"卡片感"装回来。
整行类（多文件行、设置侧栏行）接了底色但 **`scales: false`**：一条铺满的行缩放会读成"布局抖了一下"。

**焦点态这一半本轮没做**（读码读出来的结论，不是没顾上）：
`ChineseEditableTextField` 早就把 `focusRingType = .default` 恢复了（审计第二轮 1.10 / R2-02），
搜索框已经有系统环 —— 再画一条自绘边就是两圈。剩下的真实缺口是筛选段/设置行拿不到键盘焦点提示，
而那要先量清 `List` 的行代理结构（已知红 `testSidebarListFocusRingAfterClick` 就在这一带），单独成一轮。

**判据 6 条**（`PressFeedbackTests` 5 + `PressInteractionProbeTests` 1）：
真值表（三态 + reduce 退化）、强度次序 `hover < pressed < selected`、
**分通道**的 44pt 像素可见性、接线计数 ≥9、非菜单按钮的 `.plain` 文件集合相等、
以及一条真按下的在屏探针。

**那条真按下探针的结论是"量不到"，而且它把两种解释分开了**：
四颗按钮逐个合成 `leftMouseDown` → 抓帧 → `leftMouseUp`，按住与没按住 **0.0000** 无差别；
送达回执 `送达=0`，现场 `keyWindow=nil isActive=false`。
⇒ 合成事件没走到 SwiftUI 的 Button（它的按下跟踪要看窗口是不是 key，而 xctest 进程起不来）。
所以本轮的诚实结论是：**按压态"源码已接、产物未量"**，手感转人工批次 12.1。
第一版这里只写"synthetic-mouse-not-tracked"，那会把"探针送不到"与"送到了但画在抓不到的图层"
混成一句话 —— 加了送达回执之后才分得开，而这两种的处置完全不同。

**变异对照 5 支**：`pressScale` 改 1.0（第一版**逃逸**，因为那条像素断言把缩放与底色混在一起量；
拆成分通道断言之后打红，红在"只改缩放时读不出任何像素差 ⇒ 0.97 这一档是装饰"）、
reduce 闸门失效、`pressed` 与 `hover` 同值、拆掉一处接线、新加一个没接的 `.plain` ⇒ **5/5 CAUGHT**。

**验证**：613 tests / 24 skipped / 0 failures（+6 条，其中 1 条按环境 skip）；
0 warning；**82 帧 `CHANGED=0`** —— 本轮只加"按下时"的表达，静止画面一个像素都不该动，
它没动，这条本身就是"没有偷偷改到别的表面"的证据；`scripts/tests` 72 passed。

**自评 90 / 100**

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 18 / 20 | 图标按钮终于有"按下去"的一下；系统菜单那两处刻意不加，判断有依据 |
| 流畅度 | 18 / 20 | 按压用 0.12s（比内容切换快一档）；时序判据无回归，静止帧零变化 |
| 层次与材质 | 13 / 15 | 新增的 `pressed` 档嵌进既有强度次序，未开新族 |
| 动效细节 | 13 / 15 | 按下/松开都有过程；reduce 下退化成"只留底色"而不是"什么都不做" |
| 交互反馈 | 8 / 10 | 九处接上、两处刻意不接且有理由；**但产物未量**（合成鼠标进不去），这一分不敢给满 |
| 可访问性 | 10 / 10 | 减弱动态路径有独立断言；探针的 not-run 带现场状态，不把量不到读成缺陷 |
| 性能 | 10 / 10 | 无新图层、无新计时器；`ButtonStyle` 只在按下时改变换 |

**一处记录失误（不偷偷改）**：R4 的提交标题复用了 R1 那句
"one author for geometry and material"，正文写的才是按压态。提交已推送，
不 amend（那要 force push）；在这里记下来，以免以后按标题找 R4 找不到。

**遗留**：按压态的**产物级**证据（真机眼看，批次 12.1–12.7）；键盘焦点那一半单独一轮；
间距节奏（padding 一族）仍未收。



---

## Round 5 · 全页面逐元素审计（约 206 个位点）+ 三条"代码里有、屏幕上没有"

**这一轮先量再改**。四个只读代理把主窗口 / 详情与提示条 / 设置窗口 / 菜单栏与浮层
按元素过了一遍：**约 206 个位点**（侧栏与行 51 · 详情与横幅 52 · 设置 50 · 菜单栏/浮层/全局 53），
产出在 `.scratch/motion-audit/`（含共享须知与合并清单）。
代理的结论**一条都不直接采信**：我自己读码核实 8 条，6 条成立（A1–A6）、2 条被证伪并写明理由。

**修掉的三条同一族缺陷 —— 声明在、屏幕不在**：

| 位点 | 之前 | 现在 |
|---|---|---|
| 详情空态 `DetailView.body` | `.transition` 是**孤儿**：`body` 上没有任何 `.animation(value:)`，唯一那条在 `selectedEntryView` 里，而 `entry == nil` 时那棵子树已经不存在 | `body` 包一层 `Group`，挂 `value: historyStore.selectedEntry == nil`（键只取"有没有选中"：换选 A→B 不该演，那是读字不是找变化） |
| 侧栏空态 | 过渡挂在 **`Spacer()`** 上 —— Spacer 没有可见内容 | 挪到 `EmptyStateView` 那一段 |
| 收藏 / 固定胶囊 | `symbolMotion` 两臂**拿不到事务**：整个 `GlassControls.swift` 只有 hover 一处 `withAnimation`，而 `HistoryStore` 里 `grep -c withAnimation = 0` | 胶囊 `VStack` 上挂两条 `.emphasis` 按值事务 |

**还修了一条"界面不说话"**（A4）：复制**失败**零回执 —— `clipboardWriteErrorMessage` 全仓只有一个
guard 读取点、没有任何显示点，而 `DetailView.swift` 的注释声称"并弹顶部横幅"（不成立：那条横幅来自
`pasteFailureNotice`，是另一条链路）。现在失败位是 `exclamationmark` + help 文案 + 1.1s 收回 +
14+ 播报"复制失败，没能写进剪贴板"，**那句注释按实测改写**。
**删掉一条**（A5）：菜单栏 `MenuBarRecommendationsView` 挂着 `.transition` 而整个文件
`grep -c "animation(" = 0`，且 `MenuBarExtraStyle.menu` 的内容会被编译成真 `NSMenu`（D-055 / M15 实测）
⇒ 声明根本不会执行，删掉，理由写在原地。

**判据这一轮的三条都比改动本身贵**：
- **A6 按族扫**：原来"不许留不会执行的过渡声明"只读 `HistorySidebarView.swift` 一个文件，
  于是同一族缺陷在另外三处各活了一次。新增 `testNoUnexecutedTransitionClaimsAcrossViews`
  扫 `Views/*.swift` 整目录。**按文件名的守卫 = 没有守卫。**
- **A7 豁免不能写成子串**：A6 第一版用 `!line.contains("content")` 豁免 ViewModifier 工厂，
  而角色名 `.contentFade` 里就含 "content" ⇒ 把它最该抓的那类声明整行放走。
  变异 **M6 报 ESCAPED**（守卫一路绿灯，是变异把它戳穿的）。修成结构判据：豁免要求
  修饰链根是标识符 `content` **且**该文件真的声明 `func body(content: Content)`；
  检测面同时从"目录的两个工厂名"扩到任何 `.transition(`（裸写法 `.transition(.opacity)`
  原来也从尺子底下走过去）。重跑 **M6 两支 2/2 CAUGHT**，并补
  `testTransitionClaimScanIsATruthTable`（六个方向各钉一条，不门控、CI 每轮跑）。
- **A8 读数也要换成时间**：`empty-state` 同一份代码本机三次跑出过渡帧数 `3 / 2 / 2`
  （用 `git worktree` 在 HEAD 上对照，也读到 2 ⇒ **不是本轮引入的回归**），
  而变化段时长是 `131 / 119 / 125ms`。R2 只把判据的**要求**换成了时间，**读数**还是帧数，
  于是它跟着采样相位翻脸 —— 半套改造比不改更危险，因为它看起来已经改过了。
  现在判据是 `judgeMotion`：`s ≤ 0.3d` 才有分辨率、`elapsed ≥ 0.4d` 才算演
  （两个常数是解出来的：真过渡最坏读数 `d−2s`、跳变读数 `s`，要"真过渡必过、跳变必红"
  就要 `s ≤ 0.3d`），推导写在函数注释里。**变异 M8**（摘掉侧栏空态的驱动）⇒ CAUGHT，
  读数 `过渡帧数=1 变化段时长=27ms 峰值 0.192`（跳变的峰值比真过渡的任何一帧都大 ——
  这正是"帧数判据"会读成 1、"时长判据"读成 27ms 的那个区分）。

**顺带抓到变异分类器自己的一个 bug**：M8 第一次跑报 ESCAPED，真因是脚本忘了设
`CLIPBOARD_HISTORY_UI_MOTION=1` ⇒ 整条测试 skip，而 skip 的输出里同样有"0 failures"。
**"没跑"被读成"没抓到"**，与 D-055 那族同形。补了 `DID-NOT-RUN=skipped` 这一支分类。

**覆盖损失也记账，不藏**：换成时长判据之后，本机 `detail-kind-change`（760×560，
事件内最粗采样 61ms > 0.3×160=48ms）从"判绿"变成 `MOTION_NOT_RUN=clock-coarse-in-window`，
`MOTION_RESOLVE_SUMMARY judged` 从 2/3 掉到 **1/3**。CI 那台 26–30ms 的 runner 上它仍然判。
**宁可少判一条，不要判错。**

**验证**：615 tests / 24 skipped / 0 failures（+1 条真值表）；动效套件 20 tests / 3 skipped /
**0 failures**（本轮开工前它是红的）；0 warning；**82 帧 `CHANGED=0`**；`scripts/tests` 72 passed；
变异 M6 2/2 + M8 1/1 CAUGHT；`HistoryStore` 零改动（1093/1120 行不变）。

**自评 91 / 100**

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 18 / 20 | 详情空态与收藏/固定现在真的会演；菜单栏那条死声明删得干净（系统语言优先，不叠自绘） |
| 流畅度 | 18 / 20 | 键只取"有没有选中"，换选不演；三处过渡都走目录同一档 160ms |
| 层次与材质 | 14 / 15 | 没有新材质、没有新强度档；失败回执借用既有 `.emphasis` 那一档 |
| 动效细节 | 14 / 15 | 本轮的"细节"花在**判据**上：一条会翻脸的判据修成了不翻脸的，并给出边界推导 |
| 交互反馈 | 9 / 10 | 复制失败终于有回执（此前是"点了没反应还以为成功"）；**双击行复制那条路径仍无回执**（B 表 P3） |
| 可访问性 | 9 / 10 | 失败回执带 VoiceOver 播报（12/13 无 API，如实记账）；reduce 路径未回归 |
| 性能 | 9 / 10 | 无新计时器/图层；但判据换形之后本机少判一条（judged 1/3），这是本轮付出的可观测性代价 |

**遗留（下一轮的输入）**：设置窗口与菜单栏的 B 表 P1/P2 还没有一条落地；
按压态仍是"源码已接、产物未量"（人工批次 12.1）；`detail-kind-change` 的本机覆盖要靠
更细的抓帧时钟或分带窗口转正；间距节奏（padding 一族）仍未收。


---

## Round 6 · 状态变化的可读性（三处"变了但界面不说"）+ 判据的另一半

R5 把约 206 个位点过完，B 表里排最前三条都是同一句话：**状态变了，界面上什么都没发生**。
本轮就做这三条，外加一条判据 —— 因为动手时发现 R5 那族守卫只挡住了半个缺陷。

| 位点 | 之前 | 现在 | 证据 |
|---|---|---|---|
| 详情预览三态 | `loading → 成功 → 超时失败` 一帧硬换：`body` 里三个分支**没有任何** `.transition`，容器也没有驱动 | 三分支各挂 `.contentFade`，容器挂 `.animation(value: previewStage)`；键取**阶段**而不是整值（`FilePreview` 不是 Equatable，图片字节不同也不该再演一次） | `testPreviewStagesAreFed`；产物级**未量**（异步加载在本机几百毫秒内落定，胶片抓不到稳定中点）⇒ 人工批次 14 |
| 破坏性「清空未收藏」 | 按完确认之后：红色按钮还在原位、还能再点，**零回执**；`clearHistoryAction` 的签名是 `() -> Void`，链路根本没法把结果带回来 | 新增纯函数 `ClearHistoryReceiptPolicy`（数 + 说），控制器**先数再清**，签名改成 `() -> String?`；回执落在按钮**正下方**（不是另一节的 40pt 之外）并淡入；14+ 同步播报 | `testClearHistoryReceiptCountsTheRealRemoval`（真 Store 摆 2 收藏 + 3 未收藏，回执数字与 Store 真实剩余对齐）、`testReceiptIsComputedBeforeTheStoreIsCleared`（钉两行代码的**先后**）、`testClearReceiptIsRenderedAndFaded` |
| 多文件展开的箭头 | `chevron.right ↔ chevron.down` **换名字** = 一帧硬换，而旁边内容正在用 0.22s 展开 ⇒ 箭头先落地、内容还在路上 | 固定一个符号 + `rotationEffect(90°)`，挂在**同一条** `MultiFilePreviewLayout.animation` 上（reduce-motion 由它自己管） | `testChevronRotatesInsteadOfSwappingSymbolNames`；**82 帧 `CHANGED=0`** —— 静止画面一个像素都没变，这条零变化本身就是"两种写法视觉等价"的证据：本轮改的是过程，不是结果 |

**判据的另一半（本轮真正的收获）**：R5 钉的是"声明了过渡却没有供电"。
本轮加驱动时意识到镜像的那一半没人管 —— **挂了 `.animation(value:)`，而那个键是字面量**。
它比 R5 那一半更阴：连"这里写了过渡"这句话都不留，读代码的人只看到"动画已接"。
新增 `MotionDriverTests.testNoConstantAnimationKeysAcrossViews`（扫 `Views/*.swift` 整族），
带真值表：字面量三种写法要抓、`a == b` / 状态属性不许误报、跨行写法要找到、
嵌套括号不许把调用截断、没有 `value:` 不产出键。扫描器自己写一份而**不复用别的测试文件里的私有工具**
—— 复用别人的私有工具，它就跟着那个文件一起被改坏而本文件不知道。

**刻意不做的一条**：B-P1-3「暂停记录剪贴板全 App 零指示」。
Toggle 自己已经有系统开关态，真正的缺口是"三天后忘了自己关过"，那要的是菜单栏图标的**常驻变体**，
是一件事而不是一个动画。**用动效化妆会把缺陷留住还多出一层噪音** —— 已回 BACKLOG 标为非动效项。

**变异对照 6 支全 CAUGHT**：恒真动画键、把"数"挪到"清"之后、摘掉失败态的过渡、
箭头退回换名字、摘掉回执的淡入、摘掉回执的播报。
（过程中还修了变异脚本自己的一支 `NameError: io` —— 长跑脚本缺 import 这一族本仓库记过，仍然又犯了一次。）

**自评 92 / 100**

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 18 / 20 | 回执用 caption + 系统 `checkmark.circle`，没有新强调色；三态软交接与系统预览的换法一致 |
| 流畅度 | 18 / 20 | 箭头与内容同曲线；三态走目录同一档 160ms；无新计时器 |
| 层次与材质 | 14 / 15 | 全部复用既有 `VisualFont` / `VisualGlyph` / 强度档，未开新族 |
| 动效细节 | 15 / 15 | 三条"变了但不说"补齐；判据补上镜像的那一半，且带真值表 |
| 交互反馈 | 10 / 10 | 不可撤销的删除第一次有了数字回执；预览三态自己说自己在哪一步 |
| 可访问性 | 9 / 10 | 回执同步播报（12/13 无 API，如实记账）；reduce 路径由既有曲线管；**淡入本身产物未量** |
| 性能 | 8 / 10 | 三态过渡给预览块多了一层 opacity 动画；预览里含 `QLPreviewView`/视频图层，**这两类在 14+ 抓不到**，本轮没有它们的帧证据 |

**遗留**：预览三态与回执淡入的产物级证据（人工批次 14）；QuickPick 空结果仍是一片空白（P2）；
排除名单的插入/移除仍无过程（P2）；`judged=1/3` 那台机器的覆盖损失仍未转正（BACKLOG 第 8 条）。


---

## Round 7 · 浮层与临时状态，以及一条"该红的闸门"

R5 审计里 B 表的 P2/P3 有两条是同一个形状：**界面进入了某个状态，却没有任何一处说出来**。
本轮收这三条，外加把 R5 遗留的覆盖损失做成一条会红的 CI 判据。

| 位点 | 之前 | 现在 |
|---|---|---|
| 快速选择浮层空结果 | 420×300 的面板里**一片空白** —— 分不清"没匹配上"、"历史本来就是空的"与"这面板坏了" | 纯函数 `QuickPickModel.emptyMessage(query:hasAnyHistory:)` 说**三句不同的话**（有词 ⇒ 带回用户那个词并给"换词 / 按 Esc"；没词有历史 ⇒ "没有可显示的记录"；没词没历史 ⇒ "先复制点东西"）；面板里一句 `NSTextField` 按目录时长淡入，`detachesHiddenViews` 保证隐藏时不占高度 |
| 侧栏批量条 | 有驱动没过渡 ⇒ 进批量软交接、出批量一帧硬换 | 两臂各挂 `.contentFade` |
| 视频播放 / 静音两颗图标 | **根本没接** `symbolMotion`（胶囊那四颗早就接了 ⇒ 同一个仓库两套语言） | 接唯一入口 + 各自的按值事务；刻意**不给 bounce**（高频动作，红线 0/8） |

**本轮最值钱的一条记录是变异 M15 第一次绿着通过。**
守卫写的是 `controller.contains("applyEmptyState()")` —— 而**定义那一行本身就含这个子串**
（`private func applyEmptyState() {`），所以把调用整行删掉它照样绿。
这与 R5 的 A7（豁免写成 `contains("content")`，被角色名 `.contentFade` 白拿）**同形复发**。
修法是钉**调用点**而不是钉名字：取 `selectCurrentRow()` 的函数体要求含这一行，
再加一条"排除 `func` 定义行"的兜底 ⇒ 重跑 CAUGHT。
⇒ 写源码守卫时必须当场问一句：**这个 needle 还会命中什么？** 人自己想不全，所以要跑变异。

**CI 那一步（BACKLOG 第 11 条转正）**：新增 `Motion coverage floor` ——
跑完了、有结论行、而 `judged < 2/3` ⇒ **红**。三条前提缺一不可，
否则会把"探针没跑完"算成"产品没验到"（D-055 那一族）。
它自己由 `test_ci_report_selftest.py` 的四个新形状钉住：够 ⇒ 0、不够 ⇒ **必须 1**、
没跑完 ⇒ 0、没结论行 ⇒ 0。第二格就是"这道闸不是 echo"的证据。
背景写在步骤注释里：R5 把判据换成时长之后本机确实掉到 `judged=1/3`，
而上一步是报告型（红了也不挡发布），所以"今天只判了一条"在 CI 上原本长得跟"判了三条"一样。

**自评 93 / 100**

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 18 / 20 | 空态那句话是系统 `NSTextField(labelWithString:)` + `secondaryLabelColor`，与 AppKit 自己的空表一致 |
| 流畅度 | 18 / 20 | 淡入走目录同一档；批量条两臂对称 |
| 层次与材质 | 13 / 15 | 未开新强度档；浮层里只加了一行文字，没有新底 |
| 动效细节 | 15 / 15 | 三处临时状态补齐；符号替换收成一个作者 |
| 交互反馈 | 10 / 10 | "搜不出"第一次区分了"没匹配"与"这里本来就空的"，并且每次都给下一步 |
| 可访问性 | 9 / 10 | 空态文案是可读标签；**淡入本身与 VoiceOver 播报未做**（AppKit 侧要 `NSAccessibility.post`，单独一轮） |
| 性能 | 10 / 10 | 固定面板里多一个常驻隐藏标签；无新计时器 |

**验证**：629 tests / 24 skipped / 0 failures（+6）；动效套件 20 / 4 skipped / 0 failures；
0 warning；82 帧 `CHANGED=0`；`scripts/tests` 72 passed（含 CI 自检 18 个形状）；变异 5/5 CAUGHT。

**遗留**：QuickPick 的 AppKit 淡入与空态播报都**没有产物级证据**（D-055：`cacheDisplay` 抓不到
AppKit 图层动画）⇒ 人工批次 15；排除名单增删过程（P2）；
设置分区切换仍然没有 Scenario（P3）；实验 E1/E2/E3 仍未跑。


---

## Round 8 · 设置窗口：排除名单的六种结局，和"永不清空"的那半条

R5 审计里设置窗口那 50 个位点，本轮动的是**已经核实过的**三条。

| 位点 | 之前 | 现在 |
|---|---|---|
| 「不记录这些 App 的复制」· 添加 | `encodeUserExcluded` 会**去重 + 排序**，于是"加进去 / 本来就有 / 它属于系统默认排除项"三种结局在界面上**一种都看不出来**：输入框清空、列表没长，用户读到的是"我加的那条去哪了" | 纯函数 `ExcludedAppListPolicy.add/remove` 给**六种结局各一句话**（含"属于系统默认排除项，本来就不入库"这种必须说清的），没做成时**输入框保留原词**让用户照着改 |
| 同一张名单 · 行 | 增删是整块瞬间塌位 | 行挂 `.contentFade` + 容器按 `excludedBundleIDsRaw` 驱动（这里不是 `List` 而是普通 `VStack` ⇒ 过渡**能**演，M1 那条否定结论不适用） |
| 三处结果文案（导出导入 / 反馈导出 / 排除增删） | 突然出现，**永不清空** | 统一成 `ReceiptLine`：淡入 + 一个 × 自己收掉。**刻意不做自动消失** —— 这三条是"你刚做那件事的结果"，1.1 秒后自己没掉等于把信息拿走（瞬时回执才适合自动收回，见 R5 的 A4） |

**快捷键录制态本轮判定为"不加"**：按钮在录制时已经把标题换成"请输入快捷键"并拿到焦点环，
系统那套就是"我在听"的表达；再叠一层呼吸脉冲属于"让你看见我动了"，
与录制按钮那条同一判据（红线 8）。这条写在代码旁边的理由里，不是没顾上。

**判据 3 条 + 变异 4 支全 CAUGHT**，其中两支值得记：
- `M21`（名单行的过渡）这一支**没有**经历"先写弱了再被放过"：写判据的时候就想到了
  `ReceiptLine` 自己也含一条 `.transition(`，"整个文件含 needle"这种写法会放过它，
  所以直接钉到 `ForEach(decodeUserExcluded…).sorted()` **那一段里面**。
  这是 R5 的 A7（`content` 子串被角色名白拿）与 R7 的 M15（函数名被定义行白拿）教出来的动作。
  **如实记一句**：M21 是在"已经钉到段里"的版本上第一次跑就 CAUGHT 的 ——
  我没有跑过弱版本，所以不能说"弱版本被放过"。能说出口的是：**弱版本一定会放过，
  因为同一个 needle 在文件里有两处命中**。
- `M23`：把"自动消失"装回来会打红。这条是**反向**判据 —— 它挡的不是"没做"，
  而是下一轮有人"顺手加个更贴心的自动收起"。

**自评 93 / 100**

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 18 / 20 | 回执是系统 caption 尺寸 + `xmark.circle` 无边框按钮，没有新样式 |
| 流畅度 | 18 / 20 | 名单增删有过程；三处文案淡入 |
| 层次与材质 | 13 / 15 | 全部复用 `VisualFont.meta` / `VisualGlyph.badge` |
| 动效细节 | 15 / 15 | 两臂对称、驱动键非恒真、reduce-motion 走目录 |
| 交互反馈 | 10 / 10 | 六种结局全部说话，且"没做成"不再伪装成"做好了" |
| 可访问性 | 9 / 10 | 文案可选中、× 有 help 文案；无播报（AppKit/SwiftUI 混合层的播报仍欠，单独一轮） |
| 性能 | 10 / 10 | 无新计时器；纯函数一次字符串处理 |

**验证**：632 tests / 24 skipped / 0 failures（+3）；动效套件 20 / 4 / 0；0 warning；
82 帧 `CHANGED=0`；`scripts/tests` 72 passed；变异 M20–M23 4/4 CAUGHT；`HistoryStore` 零改动。

**连续五轮 ≥90 达成**：R4 90 → R5 91 → R6 92 → R7 93 → R8 93，且无新增 P0/P1 回归
（已知的两条红是 `testSidebarListFocusRingAfterClick` 与帧间隔 p95，都是本轮之前就在账上的门控判据）。


### R8b（同轮补丁）· 覆盖率闸门第一次跑就红，红的是真相

R7 加的 `Motion coverage floor` 在 CI 上把 main 判红了：`judged=0/3`。
根因不是脚本，是 **CI 抓帧在事件那一段 ~55–62ms 一帧**，超过 R5 判据要求的
`s ≤ 0.3d = 48ms` ⇒ 三个场景全部 `.clockTooCoarse`，`MOTION_SUMMARY 3/3/3` 底下
其实一条都没判。放松闸门 = 把判据改成能过，**不做**；改成三档判据
（细档看时长、中间档看"帧数地板 2"、`s > 0.5d` 才报 not-run），
本机 `judged` 1/3 → **2/3**，CI 0/3 → 2–3/3，闸门一格没松。
M8 重跑仍 CAUGHT（`过渡帧数=1 变化段时长=43ms`），真值表补中间档三格。
验证：632 tests / 24 skipped / 0 failures；动效套件 20 / 4 / 0；0 warning；82 帧 `CHANGED=0`；
`scripts/tests` 72 passed。账见 **D-067**。

---

## 阶段一 · 每日复制热图（新功能，不是动效轮；动效轮从 R9 重新起算）

R1–R8 是"给已有界面补动效"。这一节是**新造一个界面**，所以七维里"动效细节"那一栏
本轮给不到 15/15 —— 不是没做，是**做了但没供电**（见下面的缺陷 2、3），按规矩算不合格项。

| 位点 | 之前 | 现在 |
|---|---|---|
| 「每天复制了多少条」 | 全产品没有这条信息；从 `entries` 现算会被 500 条上限带着**倒退** | 独立只追加账本 `daily-copy.json`（日键→条数，730 天，损坏改名保原字节）+ 首次为空时从存档回填 |
| 设置侧栏 | 5 个分类 | 6 个：新增「统计」（`chart.bar`，按 U-8 那条刻意不用 `.fill` 变体） |
| 热图本体 | — | 26 周 × 7 格、11pt 格 + 3pt 间距、五档 `accentColor.opacity`、未来格 `Color.clear`（不画灰格）、月标签稀疏标注（间隔 <4 周不标） |
| 悬停 | — | 每格原生 tooltip（"2026年3月12日 周四 · 复制 8 条"）+ 描边一圈 + 页脚详情（回落最忙日） |

### 本轮真实视觉审查（看渲染帧）抓到的五条，代码读不出来

1. 月标签 `HStack` + 弹性空格那版**换行成两行** ⇒ 改 `ZStack` + `.offset(x:)` 按格宽算位。
2. 星期标签渲成英文 `M T W` —— 代码里的 `veryShortWeekdaySymbols` 是对的，
   **错的是夹具日历没设 locale** ⇒ 固定夹具改 `zh_CN` + `firstWeekday = 2`。尺子的问题改尺子。
3. 「每日复制热图」与分区标题「统计」重复 ⇒ 去掉一层。
4. 18 周时右栏**半空** ⇒ `defaultWindowWeeks` 18 → 26（`VisualHeat.cell` 的几何注释跟着改，
   注释按 18 周算而实现 26 周 = 漂移，见 D-068）。
5. **空态与零值汇总同时出现**：`heatmap-empty` 帧里"最近 26 周共 0 次 · 日均 0.0 次 · 连续 0 天"
   压在"还没有可统计的记录"上面 —— 两条互相矛盾的表达同时说话。R9 收。

### 一次"看帧看出来的假缺陷"，值得单独记

我看 `settings-stats-populated-720x540-light` 时判定「统计」的图标是**实心柱**、
与其他五个描线图标混用两套图形语言（以为踩回了 U-8）。
**这个判断是错的**，而纠正它的证据就在仓库里：`OffscreenSymbolInkProbeTests` 的表头写着
产品侧栏未选中行的图标列墨水 = **0.0000**（离屏捕获画不出语义色那一列），
所以那一帧里"看得见"的只有选中行 —— 我拿一个**只有选中行可见**的帧去比"六个图标的线宽一致性"，
比的是高亮态对高亮态，剩下五格是空的。
→ 规矩：**判图标语言要按探针给的墨水数字判，不能按这一帧的观感判。**

但顺着这条查下去撞到一条**真的**：那个探针的输入名单是手抄的
`["command", "gearshape", "hand.raised", "sparkles", "folder"]` ——
`sparkles` 早就不是产品用的图标（推荐分类是 `wand.and.stars`），而新增的 `chart.bar` 根本没进名单。
**一条"每次视觉审计都重新量一遍"的探针，量的是五个已经不存在的图标。**
R9 收：名单从 `SettingsCategory.allCases` 取，并加一条"探针名单 == 产品名单"的守卫
（否则它会继续以"全绿"的形式什么也不覆盖）。

### 判据与变异

21 条用例：七张真值表（日键 / 相对分桶 / 网格形状与星期对齐 / 未来格 / 月标签稀疏 / 连续天数 / 汇总 / tooltip）
+ 账本磁盘行为（采集路径不碰盘、flush 不堵去抖窗口、去抖到期不 trap、回填不写盘、只填空账本、裁剪有界、损坏保原字节）
+ **产品入口**验收（经 `HistoryStore.add` 长当天那格 / 暂停与被排除 App 不计数 / store flush 带 ledger flush / 无 ledger 时 store 照旧）
+ 接线与令牌守卫。
变异 9 支（M25、M25b、M26–M32）：第一次 **8/9**，M31 逃逸 ——
它的判据用 `debounce: 60` 且从不等待，"排了写盘"与"没排"看起来一模一样（**恒真判据**）。
重写为 `debounce: 0.05` + 真等 0.6 秒 ⇒ 9/9 CAUGHT。
M32 是本轮**真实崩溃**转成的回归判据：`DispatchWorkItem {}` 写在 `@MainActor` 方法里被推成
MainActor 隔离，跑到 `saveQueue` 上就 `dispatch_assert_queue` SIGTRAP，
而 `swift test` 只留下"signal code 5"——同时把变异分类器教了一遍：**崩溃记 `CAUGHT=crash`，不是"没跑"**。

### 自评 88 / 100（<90 ⇒ 继续修，R9 的头三条就是下面的 1/2/3）

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 18 / 20 | 只用系统 `.help` / `onHover` / SF Symbol / `accentColor`，无新样式；扣：空态沿用全 App 的 `.empty` 状态语言（U-5），而这一屏的"空"是"还没开始记"不是"没东西"，图标语义差半格 —— 为它单开一套会破坏状态语言，R9 只判不改 |
| 流畅度 | 16 / 20 | 静态构图干净；扣：当天那格加深是硬切，页脚换字也是硬切 |
| 层次与材质 | 13 / 15 | 标题/汇总/图例三档字号都走 `VisualFont`；扣：空态与零值汇总同时说话（缺陷 5） |
| 动效细节 | 9 / 15 | **`.animation(.hover, value:)` 驱动的是不可插值字符串 = 声明但空转**；描边 0↔0.55 不在事务里 |
| 交互反馈 | 10 / 10 | tooltip + 页脚 + 无障碍标签三条通道都有内容；扣不到 |
| 可访问性 | 7 / 10 | 每格 `accessibilityElement` + label；扣：写盘失败那条**没有发布通道**（值不丢但可能永远不上屏），且零值汇总对读屏是重复噪声 |
| 性能 | 15 / 15 | 采集路径零同步 IO；去抖 + `.utility` 队列 + 原子写；退出同步 flush；无新计时器 |

**验证**：0 warning；653 tests / 16 skipped / **0 failures**（+21）；
动效套件 20 / 4 / 0，`judged=2/3`（与 R8b 同档，未退）；
帧基线 82 → **90**，`check --against working` = `COMPARED=90 CHANGED=0 MISSING=0 ADDED=0`（同提交 update）；
`scripts/tests` 72 passed；`HistoryStore` 只加了 4 行胶水（守卫 `testHistoryStoreStaysThin` 仍绿：
`lines=1111 funcs=52 longest=66`）。
**一条计数噪声**：我 verify 脚本里 `grep -cE "error:"` 数出 110 条"错误"，
逐条看全是 CoreData/AddressBook 的系统噪声（`com.apple.contactsd.persistence` 那一族）——
计数命令自己没被证伪过，下一版脚本改成只数 XCTest 的失败行。

---

## Round 9 · 阶段二第 1 轮 · 热图自检（把声明的动效真正供电，撤掉空转的那条）

选题来自阶段二开场那份全新清单（`.scratch/motion-audit-2/00-inventory.md`）里
**我自己上一轮写的**三条：BACKLOG 15（hover 动画空转）、17（空态与零值汇总矛盾）、
外加一条看帧才看得见的 17b（「这张图怎么读」在没有图的屏上教人读图）。
本轮不碰 R1–R8 的任何结论 —— 那是 R10 以后的事。

| 位点 | 之前（阶段一的自己） | 现在 | 判据 |
|---|---|---|---|
| 格子悬停描边 0↔0.55 | `.animation(.hover, value:)` 挂在**页脚字符串**上 ⇒ 描边硬生硬灭，那条动画一次也没演过 | 事务挪到**变更点**：`onHover { withAnimation(.hover) { hovered = … } }` | `testHeatmapMotionIsDrivenNotJustClaimed`（M33 CAUGHT） |
| 当天那格深浅 | 复制一下 ⇒ 硬切 | `.animation(.contentFade, value: cell.bucket)`；**键是 bucket 不是 count**（同档内画面不该动） | 同上（M34 CAUGHT：换成 count 也打红） |
| 页脚那行字 | 挂着一条永远不演的 `.animation` | **撤掉**并写明理由：字符串不可插值；要"换字有过程"只能 `.id().transition()`，而它在 12/13 上先空一帧（`MotionModifiers:37` 同一族），比硬换更糟 | M35 CAUGHT（把它装回来会红） |
| 空态 ↔ 网格 | 整块硬换 | 两臂都挂 `.transition(.contentFade)`，容器按 `counts.isEmpty` 驱动 | M36（只留一臂）、M37（摘掉驱动键）双 CAUGHT |
| 零值汇总行 | "共 0 次 · 日均 0.0 · 连续 0 天"与"还没有可统计的记录"同时说话 | 可见性决定进策略：`summaryLine(for:hasRecords:) -> String?`，空 ⇒ `nil` | 真值表 + M38 CAUGHT |
| 「这张图怎么读」 | 没有图也照样出现（分隔线 + 五行读法） | 跟着图一起出现，且**写在观察账本的那一层**（`DailyCopyStatsSection`）——挂在 `SettingsView.body` 会拿到开页快照，用户复制第一条之后说明永远不出现 | `testHeatmapReadingGuideFollowsTheChart` + M41/M42 CAUGHT |

**区域取法自己是判据的一部分**：这个文件现在有 4 处 `.animation(` 与 3 处 `.transition(`，
任何"整个文件含 `withAnimation` 就算过"的写法都没有判别力。所以新写了一个
按花括号配平取成员体的 `region(in:named:)`，并且**它自己也进了一次真值表**
（取到的区域不许把下一个成员吞进去 = 它其实是整文件），
取不到目标时**当场 `XCTFail`** 而不是返回空串 —— 空串会让区域内所有
`XCTAssertFalse(contains:)` 全绿，把"成员被删了"读成"修好了"。
M39 就是钉这一条的：把 `cellView` 连调用点一起改名 ⇒ 红。
（**第一版 M39 只改了声明**，那一支编译不过，报的是 `DID-NOT-RUN=build-failed` ——
既不是抓住也不是放过，是没跑。这一条记进变异脚本的注释。）

**本轮最大的一条不是动效**：CI 在阶段一那次提交上 42 秒就红，红的是**编译器 SIGSEGV**
（Swift 6.1.2 在 `emitLazyGlobalInitializer → emitRawApply`，本机 6.2.1 不复现）。
绕法见 **D-069**：把这一批新加的"初始化器里带构造调用"的全局都消掉
（`Cell.placeholder` 改计算属性、`sharedHistoryStore` 的嵌套构造挪进一个工厂函数）。
**没有二分** —— 编译器 bug 不是产品 bug，两处语义完全等价，
代价是注释只能说"嫌疑"不能说"定位"。

**自评 91 / 100**（本轮新加的两条动画还**只有结构证据 + 静帧**，像素证据在 R9b：
胶片套件的场景表要能挂非主窗口的根视图，那条改动单独一支，别和这轮混在一起）

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 18 / 20 | 全部走 `MotionCatalog` 与 `VisualHeat`，没有新样式；扣：空态图标仍与"日历"差半格语义（刻意不动，破坏统一状态语言不划算） |
| 流畅度 | 18 / 20 | 描边/深浅/空↔网格三处进了事务；扣：还没有像素证据说它们真的摊到多帧 |
| 层次与材质 | 14 / 15 | 说明段与图同进同出之后，这一屏只剩一种说法 |
| 动效细节 | 13 / 15 | 撤掉一条假的、补三条真的；扣：键的选择（bucket vs count）只由结构判据钉住 |
| 交互反馈 | 10 / 10 | 悬停、复制、空→有 三件事现在都有可见反馈 |
| 可访问性 | 8 / 10 | 零值汇总不再对读屏重复说话；**写盘失败那条仍无发布通道**（BACKLOG 14，R10 头一条） |
| 性能 | 15 / 15 | 无新计时器；126 格各挂一条按值动画，键是 Int 档号，同档内复制不起事务 |

**验证**：0 warning；658 tests / 16 skipped / **0 failures**（+5）；
动效套件 20 / 4 / 0，`judged=2/3`（未退）；帧基线 `update` 后 `CHANGED=0 MISSING=0 ADDED=0`，
本轮**只有 4 张空态帧变了**（`heatmap-empty-{light,dark}`、`settings-stats-{light,dark}`），
有数据的 8 张逐字节不变 ⇒ 重排没有动到布局；`scripts/tests` 72 passed；
变异 M33–M42 共 **10 支全 CAUGHT**（第一次 9 支里 M39 是"没跑"，修成连调用点一起改名后红）。

---

## Round 10 · 写盘失败的发布通道，和一条"全绿但什么都没量"的探针

本轮**不改像素**（帧基线 90 张逐字节不变，`CHANGED=0` 是这一轮正确的视觉结论），
动的是两件"界面背后"的事：一条错误提示到底能不能上屏，和一把尺子到底在量什么。

### 1. `lastWriteError`：值不丢 ≠ 看得见

阶段一那版是"计算属性读加锁盒子"，注释里写的理由是"绕开 `main.async` 回写，
否则通知丢了错误就静默"。这句话**只说对了一半**：值确实不丢，但没有任何东西为它发布 ⇒
写盘失败之后用户不再复制，那一行就永远不上屏；重启之后更是永远 `nil`。

现在的形状：**盒子仍是唯一的值来源**，`@Published` 只是它的主线程镜像，
由一个"只送该重绘、不送值"的主队列回看触发。
于是通知被丢掉的最坏结果退回成**晚一格显示**，而不是静默 —— 原来那半条性质保住了，
缺的那半条补上了。`flushPendingSaves()` 也自己同步一次（退出路径上没有"下一次去抖到期"）。

四条判据里最容易被忘掉的是**反向那条**：`testASuccessfulWriteDoesNotRepublish`。
`@Published` 是"每次赋值都发、不看值相不相等"，少了那句比较，
每复制一条都会让设置页为一条**并不存在**的错误重排一次 —— 那比静默更吵。

### 2. 一条全绿的探针，量的是五个已经不存在的图标

`OffscreenSymbolInkProbeTests.symbolNames` 是手抄的
`["command","gearshape","hand.raised","sparkles","folder"]`：
`sparkles` 早就不是产品用的（推荐分类是 `wand.and.stars`），新增的 `chart.bar` 不在名单里。
现在名单从 `SettingsCategory.allCases.map(\.icon)` 推导，并加两条判据
（名单 == 产品；**逐枚**量墨水 —— 符号名写错或这枚在 macOS 12 上不存在时，
SwiftUI 不报错、只是什么都不画，而"整列墨水 >0.01"会被其余五枚抬着走）。

刻意**没有**加"源码里不许出现字面量名单"那条扫描：名单退回字面量后只要今天恰好相等它就绿，
真正会红的是"产品改了它没跟着改"，那句话由上面这条覆盖判据负责。

### 3. 逐枚墨水顺手否证了我上一轮的一个目测结论

```
INK 逐枚 chart.bar=0.0138 command=0.0143 folder=0.0124 gearshape=0.0130 hand.raised=0.0118 wand.and.stars=0.0052
```
R9 我写过"看帧觉得「统计」是实心柱混进描线那一列"，并自己纠正说那是帧不可信 ——
现在有数字了：**`chart.bar` 是第二重的一枚，不是异类**，五枚挤在 0.0118–0.0143。
真正的异类是「推荐」那枚 `wand.and.stars`，**比同列最轻的还轻 2.3 倍**，
而且它从 D-8 那一轮起就在，只是当时整列一起量、看不出来。

**本轮刻意没改它**：换符号是"图标语义 vs 视觉重量"的取舍，得连着"推荐这一页想说什么"一起判；
阈值判据也没现在加 —— 拿今天六个数反推一个"不得低于中位数 60%"的门槛，
等于把一次观测写成规律。两条都记 BACKLOG 22，归设置页那一轮。

### 自评 90 / 100（本轮**按设计**没有视觉交付，分数如实反映这一点）

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 18 / 20 | 没引入任何新样式；扣：这一轮本来也不该有 |
| 流畅度 | 16 / 20 | 零像素变化；R9 那三条新动画的**像素证据仍欠**（R9b） |
| 层次与材质 | 13 / 15 | 未动 |
| 动效细节 | 12 / 15 | 未动；且 R9 的键选择（bucket vs count）仍只有结构判据 |
| 交互反馈 | 10 / 10 | 写盘失败第一次真正能上屏，且不会在没失败时吵人 |
| 可访问性 | 10 / 10 | 那条错误提示以前对读屏也是"永远不出现"，现在会；逐枚墨水也保住了"图标名写错=静默消失"这一族 |
| 性能 | 10 / 15 | 每排一次去抖就多挂一个主队列 work item（只在 `scheduleSave` 里、可取消、无计时器）；扣 5 分是因为这是本轮**唯一**新增的运行时开销，而它没有被量过 |

**验证**：0 warning；664 tests / 16 skipped / **0 failures**（+6）；
动效套件 20 / 4 / 0、`judged=2/3`（未退）；
帧基线 `check --against working` = `COMPARED=90 CHANGED=0 MISSING=0 ADDED=0`（本轮不需要 update）；
`scripts/tests` 72 passed；变异 **M43–M46 四支全 CAUGHT**（基线步这次断言的是
"指定那条用例 passed"，不是"0 failures" —— 上一版那份脚本的基线跑的是别的套件的用例名，
`Executed 0 tests ... 0 failures` 里含 "0 failures"，于是基线永远绿）。

---

## Round 11 · 淡入到底能不能被量到：一条把上一轮结论推翻的判据

R9 的自评里我给"动效细节"留了缺口，写的是"像素证据在 R9b"。
这一轮去兑现，结果**推翻的不是分数，是结论**。

### 做了什么

| 位点 | 动作 | 读数 |
|---|---|---|
| 胶片探针 | `Scenario` 长出 `root` 与 `storeFactory` 两个可选字段 ⇒ **非主窗口**的界面也能被真窗口驱动（宿主是产品自己的 `DailyCopyStatsSection`，为此从 `private` 放开到 internal —— 探针自带一份"长得像"的视图就等于测替身） | 新场景 `heat-first-record` |
| 抓帧时钟 | 加**冷采样闸门** `clockIsWarm`：新窗口头两次 `cacheDisplay` 要 260–340ms 一帧，触发落在那段上时，一次 160ms 的过程只会被拍到两三个样本 | 预卷改成"最多 6 帧，等最后一格 ≤120ms 才触发" |
| 说明块 | 「这张图怎么读」那块以前**没有** `.transition`（R9/R10 只给图本身补了臂）⇒ 分隔线 + 五行读法是整块硬蹦出来的 | 补过渡 + 驱动键成对 |

### 结论被推翻的那一步

`heat-first-record` 第一次跑就把 main 判红：`0.004 / 0.027 / 0.220 / 0.000…` —— 一帧到位。
很容易就此写"R9 那条淡入是假的"。我按这个方向改了两版产品代码
（把驱动挪到观察层、给说明块补过渡），**两版读数一模一样**。
于是做了仓库里已有的那件工具：**双向 A/B** ——
把 `MotionCatalog.animationsEnabled` 关掉再量一次同一场景：

```
MOTION_HEAT_FADE_A/B 开 帧数=1 峰值=0.225 冷闸=true  关 帧数=1 峰值=0.225
```

**两臂完全相同 ⇒ 这把尺根本看不见纯 opacity 的淡入**
（`cacheDisplay` 抓的是模型树，淡入活在 presentation 层 —— 同一个根因在
`MOTION_NATIVE`（AppKit 行动画）那条上已经记过一次，这次是它 SwiftUI 的那一半）。

所以这条淡入的诚实状态是 **「源码已接、产物未量」**：
不许写进"已交付/已验证"，**也不许反过来判产品没做**。
判据 `testHeatmapFadeIsNotVisibleToThisRuler` 钉的就是这个状态，
而且它是**会自我作废**的：哪天两臂读数不同（尺子能看见了），它自己红，
逼着把 `heatFirstRecord()` 放回 `Scenario.all()` 当真判据 —— 而不是留一条"量不到"当永久免责。

### 顺带被这条流程抓到的两条

1. **量不到的场景不进 `all()`**：把一条尺子看不见的数据放进每天判的清单，
   等于让产品天天为尺子的极限吃红。
2. **我自己的守卫先红了一次，而且红得不对**：`testHeatmapReadingGuideFollowsTheChart` 的 needle
   写的是 `private struct DailyCopyStatsSection`，本轮为了宿主把 `private` 去掉 ⇒ 守卫找不到目标就红。
   **产品没坏，守卫把访问级别当成了被断言的性质。** needle 改成 `struct DailyCopyStatsSection`，
   并把这一条写进注释：视觉判据不许顺手锁一个不相关的语言细节。

### 自评 92 / 100

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 18 / 20 | 未引入新样式；说明块现在与图同源同层 |
| 流畅度 | 17 / 20 | 说明块的硬蹦补上了；**整条淡入仍未被像素证明**（本轮唯一的实质欠账，已如实记账） |
| 层次与材质 | 14 / 15 | 未动 |
| 动效细节 | 14 / 15 | 过渡与驱动成对；扣 1 分给"仍无产物证据" |
| 交互反馈 | 10 / 10 | 未动 |
| 可访问性 | 10 / 10 | 未动（R10 那条通道仍在） |
| 性能 | 9 / 15 | 冷采样闸门把预卷从 3 帧放宽到最多 6 帧，A/B 又多录一卷 ⇒ 胶片套件 65s → ~70s；这条代价是实测的，不是猜的 |

**验证**：0 warning；666 tests / 16 skipped / 0 failures（+2 判据）；
动效套件 **21** tests / 4 skipped / 0 failures，`MOTION_SUMMARY` 三键形状不变、`judged=2/3`（未退）；
帧基线 `CHANGED=0`（说明块包进 `VStack(spacing:16)` 之后布局逐字节不变）；
`scripts/tests` 72 passed；变异 **M47–M49 三支全 CAUGHT**
（M49 打的是尺子自己的闸门：把 `warmIntervalMilliseconds` 设成永远达不到 ⇒
"看不见"这条结论必须作废，不许拿一段冷采样去宣布尺子的极限）。

**真机侧的一条独立证据**（R11 装完之后顺手读的，只读）：
`~/Library/Application Support/时间剪史/daily-copy.json` 已经存在，
`days=6 first=2026-06-12 last=2026-10-13 total=111`，而历史存档是 94 条。
**111 > 94 是对的**，而且正是这张图存在的理由：账本记的是"复制发生过 111 次"，
存档里只剩 94 条是因为去重与保留策略 —— 重复复制同一条内容**照样计数**。
文件本身是在换装那一刻的优雅退出时被 flush 写出来的：
构造期不写盘、退出期一定写 —— 两条在真机上都留下了痕迹。

---

## Round 12 · 筛选胶囊：一颗越权 0.38s 的弹簧，和一段"reduce 之后什么都不剩"的悬停

选题来自全新清单的第 6、7 条（合并榜），两条都是**我自己前几轮改过、之后没人回来复查的**。

| 位点 | 之前 | 现在 | 为什么 |
|---|---|---|---|
| 分段筛选的滑块 | `response 0.38 / damping 0.72` 写在视图侧策略里 | 参数出自目录新增的 `.slider` 档（0.20s），**临界阻尼 = 不过冲** | 0.38 越过目录 `maximumDuration`；0.72 欠阻尼 ⇒ 点一下"全部→收藏"，胶囊会**冲过头再弹回来**。MC-1 的规矩是"只有手势跟手的位移才给过冲"，而这颗是**点**出来的 |
| reduce 闸门 | `@Environment(\.accessibilityReduceMotion)` —— 只认系统开关、不认 VoiceOver | `环境 ∪ MotionCatalog.motionShouldBeReduced`，两个视图都用 | 开着 VoiceOver 的人：全仓都降级了，只有这颗胶囊还在弹。同一文件两套闸门 = "减弱动态"在这一个文件里有两种含义 |
| 段按钮悬停 | **只有缩放**一种表达 ⇒ 减弱动态时 `hoverScale` 归 1.0，**悬停完全无反馈** | 加一层 `VisualFill.controlHover` 底色，不受 reduce 影响；选中那一段不叠（下面就是胶囊） | "reduce 是替换不是删除"这条 R1 立的规矩，在悬停这件事上以前是**空的** |

**一条值得单独记的考古**：目录里 `criticalDamping` 的注释写着"正确定义在 `FilterPillMotion`
里已经写了"—— 而 `FilterPillMotion` 自己就是那个**没被改的实例**；
白名单守卫的注释里也明写着"这两处都有过冲，是目录'一律不过冲'声明之外的**已知例外**"。
也就是说这件事**不是没人知道，是知道了没排上**。所以本轮的实质不是发现，是清账。

**判据被翻案的那一条**：`FilterPillMotionTests` 原来断言
`XCTAssertLessThan(normal.damping, 1.0, "正常态保留轻微过冲")` —— 它把旧决定钉成了规矩。
本轮翻过来（`testSlideMotionIsCriticallyDampedAndSourcedFromTheCatalog`），翻案理由写在测试上方，
不藏在 diff 里。**翻案前先读了原文**：R2-10 的原始动机是"滑块以前不读 reduce 开关"，
那条仍然成立（`isInstant` 分支保留），被推翻的只有"过冲是想要的"这半句。

**目录白名单少了一格**：`testMotionParametersOutsideTheCatalogAreWhitelisted` 立刻红了 ——
`HistorySidebarView.swift` 不再在目录之外写曲线。这条红是**设计好的摩擦**
（把老例外迁进目录就要红一次），已按提示删名字并把"少了一个例外、为什么"写进注释。

**顺带把一条死分支用起来**：`Shape.Slide.leading` 以前不可达（`shape(for:)` 只产 `.none`/`.top`），
胶囊走横轴，`.slider` 这一档正好落在它上面。

### 自评 93 / 100

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 19 / 20 | 系统分段控件本来就不弹回来；去掉过冲之后更像原生控件 |
| 流畅度 | 18 / 20 | 0.20s 配 60–90pt 位移；扣：无像素证据（见下面"欠"） |
| 层次与材质 | 14 / 15 | 悬停底色用 `VisualFill.controlHover`，与 44pt 圆按钮同一档 |
| 动效细节 | 15 / 15 | 参数单作者、临界阻尼、reduce 有替换、死分支被用上 |
| 交互反馈 | 10 / 10 | 修掉"减弱动态 ⇒ 悬停零反馈"这一条实质缺陷 |
| 可访问性 | 10 / 10 | 闸门与全仓统一（系统开关 ∪ VoiceOver），WCAG 那条不再漏一处 |
| 性能 | 7 / 15 | 每段按钮多一层 `Shape.fill`（静止 0 不透明度）；扣 8 分给"这条没被量过，而 90 帧逐字节相同只证明静止态没变" |

**验证**：0 warning；667 tests / 16 skipped / 0 failures（+1 判据，另 2 条被翻案重写）；
动效套件 21 / 4 skipped / 0 failures，`judged=2/3` 未退；
帧基线 `check --against working` = `CHANGED=0 MISSING=0 ADDED=0`
（悬停底色只在 hover 时非零、弹簧只改时长 ⇒ 静止态逐字节不变，这正是**应该**的结果）；
`scripts/tests` 72 passed；变异 **M50–M53 四支全 CAUGHT**
（M51 故意打到**另一个套件**：把曲线写回视图里，抓它的是目录那条"例外集合相等"，不是本模块的判据）。

**本轮欠的两条**：
① 悬停态**没有像素证据** —— 合成 hover 这条路仓库一直没打通（`NSApp.currentEvent` 为 nil 那一族），
所以"底色真的画出来了"目前只有静态推导 + 人眼批次 21；单列 BACKLOG 24
（做成了能一次解锁清单里约 15 处 hover-only 位点）。
② "0.20s 且不过冲"**尺子量不到**：胶囊位移是纯 transform，与 R11 那条纯 opacity 同一族
（`cacheDisplay` 抓模型树）。所以本轮的诚实说法是**参数已归位、手感未取证**。

---

## Round 13 · 悬停那一档"设计里有、运行时不存在"，而三处按钮连这一档都没有

选题来自全新清单第 5 条（`PressableStyle:53` 的 `isHovered: false`）与第 11 条
（侧栏五颗批量按钮 `.borderless`）。两条本来是分开排的，动手第一件事就发现它们是**同一条**：
R4 我立"按压要有反馈"时，把 `VisualFill.hover` 写进了令牌、写进了纯函数、写进了真值表、
写进了样式结构体的字段名 —— 唯独没写进**能持有它的那一层**。
`ButtonStyle.makeBody` 不能有 `@State`，所以当时写死 `isHovered: false`。
后果不是"少一点效果"：**全 App 12 处按钮的悬停档在运行时不可达**，
而围绕它的判据一直是绿的（真值表两个分支都测过，调用点只喂一个分支 ——
账本里那一族叫**载荷绿、消费侧坏**，这次是我自己在 R4 留下的）。

| 位点 | 之前 | 现在 | 为什么 |
|---|---|---|---|
| `PressedStyle` | `isHovered: false` 硬编码 | 新增 `PressedLabel`：`@State isHovered` + `.onHover` + `.animation(_:value: isHovered)` | 这一档唯一可能的落地形状；不是"多一层" |
| 侧栏多选条五颗（含**删除**） | `.buttonStyle(.borderless)` ⇒ 零按压、零悬停 | `.pressedStyle(in:control, hoverLevel:controlHover)` | 破坏性动作最需要"按到了"这句话 |
| 排除名单「移除」／回执 × | 同上 | 同上 | 同一族，一起收 |
| 小控件的悬停强度 | 只有 0.06 一档，铺在 20pt 图标上等于没有 | 新增 `hoverLevel` 参数，三处传 `controlHover`(0.10)，**其余站点保持 0.06 不动** | 尺寸差不是口味差；不顺手改全 App 观感 |
| 那条"不许有按钮绕过按压"的守卫 | 只查 `.plain` 一个拼写 | 一族四种（plain / borderless / link / accessoryBar） | `.borderless` 从尺子底下走过去，在全绿套件里活了很久 |

### 视觉审查（本轮真的看了像素，而且第一次用 bbox 定位）

帧基线报 `CHANGED=2`，两处都是 `sidebar-multi-select-300x520-{dark,light}`。
整帧盯着看**看不出差别**（图标只占 0.19% 的画面），所以先用逐像素 diff 定位：
变化区 `bbox=(343,220)-(529,266)`（设备像素）＝"已选 3 条"那一行的四颗描线图标；
亮色 `1185 px / 0.190% / 最大通道差 264`，暗色 `1181 px / 0.189% / 201`。
把 bbox 裁出来放大 3 倍并排看：**图标本体从灰提到满**。三条判读：
① 两模式变化量几乎相同、位置逐像素一致、没有位移 ⇒ 这是 `.borderless` 对 label 的处理，
不是暗色对比度问题；② 红色 `trash` **一个像素都没动**（在 bbox 之外），因为它带显式
`foregroundStyle(.red)` —— 恰好反证"压暗来自样式，不是这一行的排版"；
③ 这五颗**没有任何一处是 disabled**（全文件零 `.disabled(`）⇒ 压暗不携带信息，
只是把可用动作画成了不可用动作。**结论：改善，无回归**，已 `frame_baseline.py update`。

**顺带核了一条老账**：`check`（默认 `--against auto`）对 v1.4.8 快照报 `MISSING=2`
（`glass-pill-120x200-*`）。查过不是夹具掉帧：那颗胶囊在 R1/R2 之间刻意从 200 高改成 232 高，
新名字在 `ADDED` 里成对出现。**"少了两帧"与"换了两帧"是两回事**，只有前者要查。

### 变异第一次 4/5，逃逸的那一支是本轮那条缺陷族在新参数上重演

M54（悬停写死回 false）、M55（侧栏退回 `.borderless`）、M56（悬停没进事务）、
M57（`fillOpacity` 收下 `hoverLevel` 不用）全部 CAUGHT；
**M58 全绿通过** —— 把 `makeBody` 里 `hoverLevel: hoverLevel` 换成
`hoverLevel: VisualFill.hover`：函数对、真值表绿、白名单绿，而"小控件抬一档"这句话
在运行时根本不成立。补 `testStyleForwardsItsParametersInsteadOfResupplyingDefaults`：
取 `func makeBody` 的**花括号配平区域**判"四个入参逐个原样转交 + 转交点不许出现常量"
（不能用整文件 `contains`：默认值那一行本来就该出现 `VisualFill.`），
外加"全仓恰好三处消费者"的计数（新参数没有消费者就只是类型定义）。补完 **5/5 CAUGHT**。
区域助手自己配一条真值用例（`testRegionHelperIsATruthTable`）：它取不到时必须当场红，
不许安静返回空串把 `XCTAssertFalse(contains:)` 全刷绿。

### 一条关于"报告型数字"的新认识

全量并跑（开在屏探针）报 `MOTION_RESOLVE_SUMMARY judged=1/3`，单独跑胶片报 `judged=2/3`。
差的那一格不是产品：同一个 `detail-kind-change` 场景，过渡正在演那一段的**最粗采样间隔**
单独跑是 70ms、全量并跑是 81ms，而门槛是 0.3×160ms = 48ms ⇒ 后者被闸门判"切不出过程"、
**拒绝判定**。这正是 R2 把判据与采样率解耦之后应有的行为。
**但这个数字是负载敏感的**，所以以后任何一轮都不许把 `judged` 从 2 掉到 1 当成回归去追，
也不许把它当成"两条都被验过"去报。本轮两次都跑了，两个数都记。

### 自评 94 / 100

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 18 / 20 | 悬停底色 + 极轻微缩放现在与系统控件同一语言；扣 2：药丸几何仍比系统工具栏那颗小一圈（BACKLOG 25），且没有像素证据 |
| 流畅度 | 17 / 20 | 悬停进了 `.hover`(0.12s) 那一档事务；扣：这条通道的实际帧表现尺子看不见 |
| 层次与材质 | 14 / 15 | `hover < controlHover < pressed < selected` 四档全由令牌给，次序有真值表钉 |
| 动效细节 | 15 / 15 | 死档复活 + 检测面加宽 + 逃逸一支补成接缝判据（本轮最强的一项） |
| 交互反馈 | 10 / 10 | 含删除在内的三处一次性/破坏性控件第一次有"按到了"的表达 |
| 可访问性 | 8 / 10 | 静止态图标从灰提到满，直接修掉"可用被画成禁用"；扣 2：命中区仍是 16pt 图标本体，对运动障碍的人偏小 |
| 性能 | 12 / 15 | 每颗按钮多一个 `@State` 视图与一条 `.onHover`；静止态只有两帧变化说明代价没外溢；扣 3：12 处 × 一层的合成代价没做帧率对照 |

**验证**：`swift build` 0 warning；全量（开在屏探针）`Executed 670 tests, with 16 skipped and 0 failures`；
胶片单独跑 21 / 4 skipped / 0 failures、`judged=2/3 not-run=notice-banner`（与 R12 同）；
`python3 -m unittest discover -s scripts/tests` → `Ran 72 tests OK`；
帧基线 `update` 后 `check --against working` = `CHANGED=0 MISSING=0 ADDED=0`；
变异 **M54–M58：第一次 4/5，补判据后 5/5**。

**本轮欠的三条（都排进 R14/R15，不留在注释里）**：
① 悬停态**仍然没有像素证据** —— 这一档现在"可达"，但"可达"是结构推导不是观测；
② 「移除」与回执 × 这两处**从来没有对应的帧**（夹具里没有"用户加过排除 App""刚导出完"这两种状态），
所以本轮在这两处的改动是**源码已接、产物未量**；
③ 药丸几何与命中区。①② 一起做（R14：证据通道 + 补两帧），③ 之后（R15）。

---

## Round 14 · 想做"让悬停可被取证"，三条路全断；断出来的那把尺第一件事就量出 R13 的回归

选题是排期里的 R14（BACKLOG 24）：清单里约 15 处位点的唯一反馈是 hover，而仓库没有
任何判据能证明"悬停时那层东西真的画出来了"。本轮先做 spike（三条路，见
`.scratch/motion-audit-2/spike_hover_channel.md`，含复现命令与原始输出）：

| 路 | 试了什么 | 实测 |
|---|---|---|
| ① 合成真指针 | `CGWarpMouseCursorPosition` + `CGEvent(mouseMoved).post(.cghidEventTap)`，窗口已 `activate` | 连**自建的** `NSTrackingArea` 都没收到 `mouseEntered:`（`appkit_enters=0`）⇒ 事件没进这个进程（无输入授权，`post` 不报错） |
| ② 调 AppKit 入口 | 遍历视图树找到 tracking area 的 owner（就是 `NSHostingView`，mask=643 含 entered/exited），直接调 `mouseEntered(with:)` / `mouseMoved(with:)` | `.onHover` 闭包一次都没跑 ⇒ SwiftUI 不走这两个方法分发悬停 |
| ③ 让窗口收事件 | `window.acceptsMouseMovedEvents=true` + `window.sendEvent(合成事件)` | `mouseMoved` 无反应；构造 `.mouseEntered` 类型的 `NSEvent` 直接崩在 `+[NSEvent mouseEventWithType:]` |

**结论：在这套 SwiftPM 测试设施里，"鼠标移到控件上"不可取证。**
本轮没有假装做成了，也没有因此把整件事退回"只能人眼"——
而是把"悬停有没有效果"这句话**拆成两半分开记账**：
**触发**（指针进包围盒）＝人眼（批次 23）；**表达**（那一档画在真实尺寸上看不看得出来）＝可量，做成判据。

### 新判据上线抓到的第一条，是我自己上一轮引入的回归

`testFillLaddersAreVisibleOnBothControlClasses`：用 `NSHostingView` + `cacheDisplay`
画产品真正会画的那一层（`VisualShape.rounded(...).fill(Color.primary.opacity(level))`），
按**均值通道差**逐档判。判"同一颗控件依次经过的状态"，不判"四档排成一条梯子"
（一行这辈子不经过 `controlHover`，一颗 22pt 图标也不经过 `selected` —— 跨控件比两档差多少，
量的是一件不存在的事）。

```
row/light      idle→hover 12.78  hover→pressed 12.78  pressed→selected 8.85
row/dark       idle→hover 10.82  hover→pressed 11.80  pressed→selected 7.87
control/light  idle→hover 20.52  hover→pressed  3.73   ← 地板是 4.00
control/dark   idle→hover 17.73  hover→pressed  3.72   ←
```

R13 为了让 22pt 图标上的悬停看得出来，把那一档从 0.06 抬到 0.10，而按下是 0.12 ——
**抬悬停这个动作本身把"按下去了"这句话抹掉了**。
R13 的全部判据（真值表、白名单、集合相等、变异 5/5）都是绿的，
因为它们量的是"令牌之间的关系"，没有一件量过"画在 22pt 上差多少"。
改成 0.08（不是把按下抬到 0.14 —— 那会把 `pressed→selected` 压到 4 以下，同一种塌法换个位置）：
`idle→hover 15.9/14.0`、`hover→pressed 8.4/7.5`，两边都过。

### 两张"从来没有存在过的帧"

`FRAME_BASELINE_CHANGED=2` 里从来没有设置页，因为「移除」与回执 × 只在交互之后才存在。
现在有了：`settings-privacy-excluded-720x1040-{light,dark}`、`receipt-line-430x56-{light,dark}`，
基线 90 → 94。过程中翻三次车，每一次都是"帧"抓的：
1. **第一版 540 高拍不到那颗按钮** —— 用户自己加的排除项排在 10 行默认清单之后，在折叠线以下。
   "这张帧存在"不等于"这个控件被拍到了"。（排序该不该反过来记 BACKLOG 27，不在动效轮顺手改。）
2. **种子串手写 `"a,b"`，而分隔符是 `";"`** ⇒ 画面上是一整行 ID 加**一颗**「移除」。
   产品没错，错的是夹具自带一份"长得像"的格式；现在由 `CapturePolicy.encodeUserExcluded` 生成。
3. **顺手拍到一条真缺陷**：那句说明在屏幕上打印的是字面 `**你额外**` ——
   设置页的 `Text` 不解析 Markdown。去掉强调而不是接渲染器（这一页别处都不加粗）。

于是又给夹具机械自己加一条判据：**种过的默认值必须还原**（不还原的污染是静默的，
而基线会把污染当成"产品长这样"永久钉住）。`ReceiptLine` 为此从 `private` 放开到 internal
（与 R11 的 `DailyCopyStatsSection` 同手法：没有夹具的状态等于没有验收，而宿主替身测的是替身）。

### 自评 95 / 100

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 18 / 20 | 悬停与按下重新分得开，这是"像不像系统控件"的实质内容；扣 2：药丸几何与命中区仍未动（BACKLOG 25，现在有条件了） |
| 流畅度 | 16 / 20 | 本轮不动任何时序；修好台阶让"按下"重新成为一个可感的瞬间。扣 4：hover 的**过程**仍然没有帧证据 |
| 层次与材质 | 15 / 15 | 四档底色在两类尺寸 × 两种外观下逐档实测，方向也判（亮色每档更暗、暗色每档更亮） |
| 动效细节 | 15 / 15 | 判据形状（状态序列 vs 梯子）、轴选对（均值差 vs 占比）、夹具从产品推导、夹具自检 |
| 交互反馈 | 10 / 10 | 抓到并修掉 R13 自己引入的一条真实回归 |
| 可访问性 | 8 / 10 | 暗色台阶一起判；扣 2：触发不可取证（本轮的结论）+ 命中区仍是 16pt 图标本体 |
| 性能 | 13 / 15 | 产品运行时零新增（改的是一个令牌常量与一个访问级别）；扣 2：判据每次扫 88×88 全像素，测试 +0.5s |

**验证**：`swift build` 0 warning；全量（开在屏探针）`Executed 671 tests, with 16 skipped and 0 failures`；
`MOTION_RESOLVE_SUMMARY judged=1/3`（R13 已记：这个数字负载敏感，不追）；
脚本 72 passed；帧基线 94 张、`check --against working` = `CHANGED=0 MISSING=0 ADDED=0`；
变异 **M59–M62 四支全 CAUGHT**（M59 打的正是 R13 那一步，M61 打判据自己的渲染夹具，
M62 打夹具的还原）。

**本轮欠的**：① 触发的像素证据（**结案为不可取证**，永久人眼，BACKLOG 24 → 28）；
② 药丸几何（BACKLOG 25，R15）；③ BACKLOG 29 那条规矩还没做成守卫
（"改任何 `VisualFill` 档位必须跑完整梯子"目前只在测试里，没有强制路径）。

---

## Round 15 · 药丸与命中区一起长；而新梯子先量错了对象，是变异抓的

选题是 R14 结尾排的两条：BACKLOG 25（悬停药丸的几何 = label 包围盒，比系统工具栏那颗小一圈，
且命中区与药丸同尺寸）与 BACKLOG 29（"改令牌必须跑完整梯子"这条规矩还没有强制路径）。

| 位点 | 之前 | 现在 | 为什么 |
|---|---|---|---|
| 三处小控件的悬停/按压高亮 | 底色铺在 **label 的包围盒**上 ⇒ 16pt 图标的药丸紧贴笔画，能点的地方也只有那一圈 | `PressedStyle` 新增 `labelPadding`（默认 0），侧栏五颗给 5、「移除」与回执 × 给 4 ⇒ **高亮比字形大一圈，命中区跟着长** | padding 挂 overlay 能做出"更大的高亮 + 不变的命中区"，那是**骗眼睛**：移到药丸边缘点不动 |
| 侧栏多选条 | `HStack(spacing: 8)` | `spacing: 0` + 每边 5pt | 留着 8 再加 5，两颗高亮之间露 18pt 空隙，读成"五个孤立方块"而不是一排工具 |
| `VisualFill` 的覆盖 | 四档里只量了四档… 准确说：`fieldIdle`/`fieldActive` **从来没进过任何梯子** | 第三条梯子（输入框 280×28）+ **集合相等守卫**：加一档令牌而没进梯子就红 | R13→R14 那一课的工程化 |
| 窄侧栏 | 没有帧（`sidebarFrame` 把宽度写死 300） | `sidebar-multi-select-min-250x520`（250 = `ContentView` 的 `minWidth`） | "最窄放得下"从算式变成帧 |

### 本轮最重要的一段是判据自己错了

新加的 field 梯子第一版**从硬编码的 `level: 0` 起步、再 `dropFirst()`**。
对行与小控件没错（它们第一步就是 idle=0），**但输入框的静止态不是 0** ——
于是那条梯子量的是 `idle → fieldActive`，而真正要问的 `fieldIdle → fieldActive` 一步都没比过。

**M66（把两档并成一档）因此全绿通过 —— 变异对照第一次 3/4。**
把起点改成"梯子自己的第一步"之后：同一支变异立刻红，
并且当场量出一条**一直存在、从来没人看过**的缺陷：

```
field/light fieldIdle(0.035)->fieldActive(0.060) 均值通道差=4.98/255
field/dark  fieldIdle(0.035)->fieldActive(0.060) 均值通道差=3.98/255   ← 地板是 4.00
```

**暗色下搜索框"空着"与"正在输入"几乎是同一张脸。**修法两条：抬激活态（改 6 张帧）
或放轻静止态（改 20 张，搜索框在每个主窗口帧里都在）。选了**改动小的那条** ——
与 R13 给 `hoverLevel` 定默认值同一理由：一轮只承担一个可复核的假设。
抬完 `fieldActive 0.075` ⇒ `7.97 / 6.97`，堆叠帧复核：填充态明显抬起来一点，但不吵。

顺带把**两档各自的令牌值**打进日志（`fieldIdle(0.035)->fieldActive(0.075)`）——
这一轮在这里绕了一圈，起因就是"改了令牌、读数一模一样、日志看不出量的是哪两个数"。

### 视觉审查（本轮看了 4 组堆叠帧）

`CHANGED=12`（药丸 6 张 + 搜索框激活态 6 张），逐组堆叠对比：
- 多选条明/暗：图标排变宽、间距变匀，五颗都在，红色 trash 未被推挤，右侧仍有余量；
- 搜索框明/暗：填充态与空态现在一眼可分，空态一字未动；
- 窄侧栏 250：第一次拍到这一档时**两边各裁 25pt** —— 逐像素 extent 正好等于整幅宽，
  说明不是产品溢出而是 `sidebarFrame` 把宽度写死在 300。**先量 extent 再下结论**救了一次：
  差点把"夹具在撒谎"当成"产品在窄宽度下溢出"去修。现在宽度是参数，实测内容占 17–227.5pt。

### 自评 96 / 100

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 19 / 20 | 药丸与命中区终于与系统工具栏同形；搜索框有了状态。扣 1：图标仍是 16pt 字形，只是可点区变大了 |
| 流畅度 | 16 / 20 | 本轮不动任何时序。扣 4：hover 的**过程**依旧没有帧证据（R14 的结论没变） |
| 层次与材质 | 15 / 15 | 三族状态梯子全覆盖，六档令牌无一漏量，方向与台阶都判 |
| 动效细节 | 15 / 15 | 判据自身的错误被变异抓出来并修好 —— 这是这套流程该有的样子 |
| 交互反馈 | 10 / 10 | 搜索框从"暗色下没有状态通道"变成可感；三处小控件命中区变大 |
| 可访问性 | 9 / 10 | 命中区变大对运动障碍者是实质改善；暗色两态可辨。扣 1：触发仍不可取证 |
| 性能 | 12 / 15 | 产品运行时零新增（padding 是布局层）。扣 3：判据每轮渲染 12 张合成图 + 全像素扫描（≈1.0s），且 12 张帧只做了 4 组堆叠复核，其余靠"改动来源可解释"过 |

**验证**：`swift build` 0 warning；全量（开在屏探针）`Executed 673 tests, with 16 skipped and 0 failures`；
脚本 `Ran 72 tests OK`；帧基线 96 张、`check --against working` = `CHANGED=0 MISSING=0 ADDED=0`；
变异 **M63–M66：第一次 3/4（M66 逃逸 ⇒ 判据自己错），修完 4/4 CAUGHT**。

**本轮欠的**：① 触发仍不可取证（不变，人眼批次 24）；
② `VisualTokenTests` 里"改档位必须跑梯子"目前靠集合相等兜底，还没有"改了数值就必须重跑台阶判据"的 CI 强制；
③ BACKLOG 27（用户排除项被埋在默认清单之后）与 25 的另一半（图标本体尺寸）留给后面。

---

## Round 16 · 只有一臂在演的过渡等于没有；而"上次量不到"不能替代"这次量一次"

选题是全新清单第 4 条：`DetailView` 的 `if/else` 里**只有空态那一臂**挂了
`.transition(contentFade)`，而容器按 `selectedEntry == nil` 供电。
动手前照规矩读了原文（D-055 的 M4）—— 当年把"详情换页整块淡入"**改成**"换类型才交叉淡"，
理由是"整块淡入只能从全透明开始 ⇒ 每次换选一帧空白；方向键连翻时整块永远到不了不透明"。
那半条仍然成立，换选继续由 `DetailPreviewKind` 那一档管着。

**但同一条理由反过来打在没人看的地方**：删掉最后一条记录时，
内容臂**瞬间消失**，空态再从全透明淡进来 ⇒ 整块详情区空白约 160ms。
**当年砍对了方向，却把另一头留成了半个。**

| 位点 | 之前 | 现在 |
|---|---|---|
| 详情区换人（空 ↔ 内容） | 一臂演、一臂硬切，中间有一块空白 | 两臂成对 ⇒ 真交叉淡（旧的一直在，直到新的完全显形） |
| 供电键 | `selectedEntry == nil`（对） | 不变，但**加了守卫**：谁把它换成 `selectedEntry?.id` 就红 —— 那才是 D-055 真正否决的东西 |
| 这条淡入的可测性 | 没人试过 | 双向 A/B 做完：`开 帧数=1 峰值=0.030 / 关 帧数=1 峰值=0.030`（冷闸已过、前提峰值 > 0.005）⇒ **尺子看不见**，记「源码已接、产物未量」 |

**为什么"看不见"还要做一遍 A/B**：R11 已经证明纯 opacity 淡入不在 `cacheDisplay` 的可见面里，
而这一条两臂**内容与位置都不同**，理论上比热图那条更可见 —— 沿用旧结论就是拿上一次的测量
当这一次的证据。做完才知道：**同样看不见**。两个方向都不能偷懒：
"上次量不到"不等于"这次不用量"，"这次量不到"也不等于"产品没做"。

**判据自己红过两次，都红在尺子上**（这两条比本轮的产品改动更值得记）：
1. 区域锚点用第一个 `var body: some View` ⇒ 这个文件里 `var body` 有好几个（同文件还有别的视图），
   把别人的过渡一起数了进来，读出 4 而不是 2。锚点必须选"那一次换人"本身。
2. 数 `.transition(` 的**子串**次数 ⇒ 一行
   `.transition(MotionCatalog.transition(for: .contentFade))` 里它出现两次（修饰符 + 目录函数名）。
   要**按行数** —— 仓库里 `transitionClaimLines` 早就是按行的，我这次没沿用。

**reduce 路径查过**：`contentFade` 的 shape 在 `shape(for:)` 里既不平移也不缩放（`break`），
两模式都是纯 opacity，reduce 只是把曲线换短 ⇒ 两臂仍在同一事务里换人，
**不会**给"减弱动态"的用户留下那块空白。这条不是推测，是读 `shape(for:)` 与 `animation(for:)` 得出的。

### 自评 93 / 100

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 18 / 20 | 内容替换用交叉淡是系统的习惯；扣 2：观感还没被人眼确认（批次 25 未回） |
| 流畅度 | 17 / 20 | 消掉一段 160ms 的整块空白；扣 3：无法证明它真的在演（尺子的极限，不是产品的） |
| 层次与材质 | 14 / 15 | 不动层级与材质；扣 1：详情区两臂叠在一起时会不会"糊"没量过 |
| 动效细节 | 15 / 15 | 成对 + 供电键 + 反向键三条结构判据；A/B 判据是**自我作废**的 |
| 交互反馈 | 9 / 10 | "删掉最后一条"现在有连续表达；扣 1：未取证 |
| 可访问性 | 10 / 10 | reduce 退化路径逐函数查过（两臂同事务换人，不留空白） |
| 性能 | 10 / 15 | 无新增常驻动画；扣 5：本轮新增一次 A/B 要抓**两卷** 30 帧（+约 5s 测试时长），而它今天只能得出"看不见" |

**验证**：`swift build` 0 warning；全量（开在屏探针）`Executed 675 tests, with 16 skipped and 0 failures`；
脚本 `Ran 72 tests OK`；帧基线 96 张 `CHANGED=0 MISSING=0 ADDED=0`
（**过渡类改动静止态不变是应有结果**，既不能当"没做"，也不能当"已验证"）；
变异 **M67–M69 三支全 CAUGHT**（第一次跑因脚本元组索引 off-by-one 直接 NOT-GREEN 早退，没污染文件）。

**本轮欠的**：这条交叉淡的**观感**（160ms 内两臂叠在一起好不好看）只能等人眼；
`detail-empty-to-content` **不进** `Scenario.all()`，等哪天 A/B 两臂不同了再升成真判据。

---

## Round 17 · 浮层里最高频的那次变化，被一句"表达不了"划走了一年

清单第 10 条（QuickPick 三处）。先读原文：D-055 说"SwiftUI `List` 拿不到行过渡"（四种写法实测全部一帧到位），
替代路径是走 `NSTableView` 自己的原生行动画 —— 那批做完了，`QuickPickRowDiff` 把插/删/改文案三步拆清楚。
**但同一个文件里还有一句"保留行相对顺序变了 ⇒ 原生 API 表达不了 ⇒ 退回整表刷新"，
它把最高频的一种形状一起划掉了：刚复制的那条被顶到最前。**
也就是说这个浮层里最常发生的一次变化，一直是 `reloadData()`：六行全部重画，没有移动可言。

| 形状 | 之前 | 现在 |
|---|---|---|
| 恰好一行挪位（顶到最前 / 沉到最后 / 两行互换） | 整表硬刷新 | `moveRow(at:to:)` 一次滑动（reduce 时照样挪位、只是不滑） |
| 多行同时跳、移动混着增删 | 整表硬刷新 | **仍然**整表硬刷新（不猜 AppKit 的连续 move 坐标系） |
| `isNoop` | 不看移动 | 看移动（漏了就等于"算出来了但界面不动"，最安静的那种坏法） |

### 三个"看起来显然"的直觉被实现纠正

1. **两行互换要两次 move** ⇒ 一次就够（把第 0 行移到第 1 行）。
2. **三行循环位移要两次 move** ⇒ 一次就够（`[a,b,c]→[c,a,b]` 就是把 `c` 提到最前）。
3. **第一个不同的下标处，动的是左边那一行的元素** ⇒ 不一定。
   `[a,b,c,x]→[x,a,b,c]` 第一个不同的位置是 0，那里 `old[0]=a`，而真正在动的是 `x`。
   只试一个候选，就会把**本轮唯一要救的那个形状**判成"表达不了" ——
   这条不是我想到的，是第一版 `singleMove` 被自己的真值表打红之后补的。

顺手一条 API 事实：`NSTableView` **没有** `animationOptions` 那个属性（它是 `NSOutlineView` 的），
第一版按它写直接编不过；行移动的动与不动由 `NSAnimationContext.allowsImplicitAnimation` 决定。

### 本轮最重要的一条诚实记账

`FRAME_BASELINE_CHANGED=0` 在这里**不是**"没有视觉变化"，而是**这个表面在帧基线里根本不存在**：
`UICaptureTests` 的夹具是 `() -> AnyView`，只能宿主 SwiftUI，而浮层是 `QuickPickController`
自建的 `NSPanel` + `NSTableView`。96 张基线里没有一张是它 ⇒ 记 **BACKLOG 30**
（给夹具加一条 AppKit 通路，然后至少补 `quickpick-list/empty/scrolled` 三张）。
同一个原因也解释了为什么 §12 那批 AppKit 表面的观感结论一直停在"胶片 + 人眼"。

胶片那一侧补了对照臂（`testNativeRowMoveIsVisibleToTheRuler`，两臂用产品实际会传的那两个值）。
本机这一轮抓到 `visible=true key=false active=false` ⇒ 判据按 R11 立的规矩**报 not-run**：
**没有**把它读成"移动不会动"，也**没有**为了绿而放宽门槛。CI 那台 runner 历史上拿到过激活态，
所以这条判据有机会在 CI 上真判一次。

### 自评 95 / 100

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 17 / 20 | 与系统列表一致的做法（移动就是移动，不是重画）；扣 3：这台机器上还没看到它真的滑 |
| 流畅度 | 15 / 20 | 一次移动不再重画六行；扣 5：动效本体未取证（激活臂没拿到） |
| 层次与材质 | 14 / 15 | 不动材质；扣 1：滑动时行高/间距是否稳定没量过 |
| 动效细节 | 15 / 15 | 纯函数九格真值表 + 接线守卫 + `isNoop` 三处都有判据，且三个直觉被纠正 |
| 交互反馈 | 10 / 10 | 最高频的一次变化第一次有了正确表达 |
| 可访问性 | 9 / 10 | reduce 时"照样挪位、只是不滑"（替换而不是删除）；扣 1：无取证 |
| 性能 | 15 / 15 | 本轮唯一一次**降低**运行时开销：一次 `moveRow` 换掉整表 `reloadData` |

**验证**：`swift build` 0 warning；全量（开在屏探针）`Executed 678 tests, with 16 skipped and 0 failures`；
脚本 `Ran 72 tests OK`；帧基线 96 张 `CHANGED=0 MISSING=0 ADDED=0`
（**这一轮的 0 不代表"没变化"**，理由见上）；变异 **M70–M72 三支全 CAUGHT**
（第一次跑 M70/M72 因脚本把套件名当路径而 anchor-count=0 没注入 —— 报的是 DID-NOT-RUN，不是绿）。

**本轮欠的**：① 它到底滑没滑（激活臂 / 批次 26）；② 浮层进帧基线（BACKLOG 30）；
③ `scrollRowToVisible` 在移动之后要不要平滑滚动 —— 本轮**刻意没动**：
键盘驱动的浮层里"选中行跟着跳"是系统习惯，给它加平滑滚动会把"跟手"变成"慢半拍"
（与 D-055 砍 M3/M10 同一条理由）。这条判断写在代码注释里，不是漏掉的。

---

## Round 18 · 选题没做成；顺着它查，量尺自己被抓出三处不诚实

清单第 12 条（BACKLOG 30：让 AppKit 表面进帧基线）。开场缺陷清单（带坐标，全部来自这一轮新拍的帧）：

| # | 位点（帧 / 像素坐标） | 缺陷 | 这一轮的处理 |
|---|---|---|---|
| 1 | `content-with-notice-750x560` 实际 1500×2608 px | 帧名说 560 高，窗口偷偷长到 1304 | 钉死尺寸 + 快门前断言，**已修** |
| 2 | `menubar-recommendations-320x320` 实际 340 px 高、`menubar-empty-320x120` 实际 172 px | 同上（方向相反：窗口缩了） | 同上，**已修** |
| 3 | `weights-520x560` 帧顶 y=0..210 px | 标题、说明、「恢复默认」按钮、第一行因子从来不在帧里（内容要 850pt） | 夹具改 880，**已修** |
| 4 | `weights` 帧 x=947..988、y=106/274/442/610/778/946/1114 px | 只读数值「默认」的字形是 (0,122,255) = 系统强调蓝 | 颜色语义重写，**已修** |
| 5 | `sidebar-history-300x520` y=740..871 px、`sidebar-multi-select` y=302..637 px | 选中行是**纯黑圆角块**，文字看不见 | 数得出来、拍不到 ⇒ 盲区名单（BACKLOG 31） |
| 6 | 快速选择浮层整块 | 离屏一张都拍不出来（`transparent=99.5%~100%`） | 自我作废的判据盯着（BACKLOG 30 收口） |

### 选题的结论是"做不到"，而这句结论有判据守着

给 `Fixture` 加了 AppKit 通路（`appKit: () -> NSView?`，与 SwiftUI 夹具共用同一条渲染路径），
给 `QuickPickController` 加了只读捕获入口 `buildContentForCapture(query:)`，
然后本文件那条"未被绘制即判失效"的守卫**立刻把六张新帧全判死**：一张都没有内容。
根因：浮层背景是 `NSVisualEffectView`，没上过屏的窗口没有可合成的背景层。

所以那三张帧没补上，改由 `testQuickPickOverlayStillCannotBeCapturedOffscreen` 看着：
它断言的是"**这个限制还在**"（`transparent > 0.9`），哪天红了就是能拍的那天。
形状与 `testHeatmapFadeIsNotVisibleToThisRuler` 同一族 —— 自我作废的判据比一句"拍不到"的注释活得久。

### 三处"量尺不诚实"里最贵的一处

不是尺寸，也不是黑块，是**第 1 条**：`content-with-notice` 这张帧的职责是
"提示条插进 `ContentView` 会不会把 `NavigationSplitView` 挤坏"，
而窗口自己长到 1304 高 ⇒ **它从来没有被挤过**。一张帧悄悄回答了另一个问题，
比一张拍不出来的帧危险得多 —— 后者会红，前者九轮以来一直是绿的。

修法两层（13+ 用 `sizingOptions = []`，12 用 `contentMinSize/contentMaxSize`），
外加快门前那句 `contentView.bounds == 夹具尺寸`。钉完之后 98 张帧**名实相符**。

### 两条被数据当场推翻的"现成尺子"

- 我先想用 `host.fittingSize` 判"内容装不装得下框"。实测它是**一条恒真的尺**：
  夹具里有 `.frame(height:)` 时它报的就是那个被钉死的数（还多 +32pt 标题栏）。
  更糟的是**读它这个动作会改窗口尺寸** —— 加探针那次跑出来 58/98 帧的高度自己变了。
  探针撤掉，改成"把内容放进高框里量墨迹最后一行"（850pt 那个数就是这么来的）。
- 黑带检测第一版用"整行有 60% 是黑的" ⇒ `content-*` 三张全漏（选中块只占 750pt 帧里侧栏那 250pt）。
  改成"连续黑像素 ≥60pt"。**占比是相对帧宽的，而缺陷不是。**

### 一处"看起来像产品 bug"的东西，判据说不是

那块黑一开始被我当成"选中行文字看不见"的缺陷。区分它的不是解释，是对照：
同一行**离开 `List`** 单拍（`row-*` 那批）一张黑都没有 ⇒ 黑来自容器、不是来自行。
于是它是**取证限制**（BACKLOG 31），而不是一个可以靠"自绘选中底色"修掉的 bug ——
后者正是 D-034 否掉过的"两套选中语言"，不许顺手做。

### 自评 91 / 100

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 18 / 20 | 去掉了一处非原生语言（只读文本穿强调色）；扣 2：选中态长什么样仍然没验证过 |
| 流畅度 | 13 / 20 | **本轮没有新增任何动效**，也没有改善任何时序 —— 这是诚实的分，不是惩罚 |
| 层次与材质 | 14 / 15 | "材质离屏不可合成"从"看不见"变成"数得出来"；扣 1：仍然只是数得出来 |
| 动效细节 | 12 / 15 | 无新增动效参数；扣 3：这一轮的产出在尺子上，不在动效上 |
| 交互反馈 | 10 / 10 | 权重列现在区分"动过 / 没动过"，而且**两态都在帧里**（`weights-adjusted`） |
| 可访问性 | 9 / 10 | 颜色不再对低视力用户承诺"可点"；扣 1：没查 VoiceOver 怎么朗读这一列 |
| 性能 | 15 / 15 | 新增两次逐像素扫描只在夹具套件里跑，产品代码零开销 |

**验证**：`swift build` 0 warning；全量（开在屏探针）`Executed 680 tests, with 16 skipped and 0 failures`
（日志里那 10 条 `warning:` 全是 CoreData 的运行时噪声 `NSXPCStoreServerEndpointFactory`，
不是编译告警 —— 计数命令本身要看清它在数什么）；脚本 `Ran 72 tests OK`；
帧基线 96 → **98**，同提交 update，`CHANGED=0 MISSING=0 ADDED=0`；
差异逐条对过账：6 张因钉尺寸而变、2 张因权重配色而变（`settings-recommendations` 嵌了同一个视图）、
`weights-520x560` 两帧消失 + `weights-520x880` 与 `weights-adjusted-520x880` 四帧新增。
变异 **M73–M80 九支全部符合预期**（M76 = 故意放的"期望漏网"，见下）。

### 这一轮最贵的一课：电池整批 DID-NOT-RUN，跑了 47 分钟才看见

第一版电池八支变异全报 `DID-NOT-RUN`，原因是**本机 python3 会往环境里注入
`SDKROOT=/Library/Developer/CommandLineTools/SDKs/MacOSX.sdk`**，SwiftPM 拿它编 `Package.swift`
会在 `Swift.swiftinterface` 里挂掉 ⇒ `error: 'clipboardhistory': Invalid manifest`。
直接在 shell 里跑是好的（那个环境没有 SDKROOT），所以"手工验一条通过"完全没暴露它。

三条都被写进脚本了：① `BASE_ENV` 里剔掉 `SDKROOT`；
② **第 0 支变异 = 预检**：不注入任何东西，先要求每条被点名的判据能跑、而且是绿的，
预检不过 ⇒ 一支都不注入、退出码 2；③ 还原自检比的是**电池开跑前自己抓的字节**，
不是 `git diff` —— 工作树本来就有未提交改动，拿 git 比会把"还原成功"读成"三个文件没还原"
（第一版就是这么误报的）。

**M76 是故意放的漏网**：把 `weights` 夹具退回 560 高，**没有任何测试会红**（实测 ESCAPED）。
这条不是失败，是把缺口钉成数字：夹具的高度仍然是记下来的数 ⇒ BACKLOG 32，
并写清为什么 `fittingSize` 不能当那把尺。M75a 期望 EITHER、实测 CAUGHT ⇒
`sizingOptions` 那行**不是装饰**（只留 min/max 拦不住窗口被顶大）。

**本轮欠的**：① 选中态取证（BACKLOG 31，先 spike"把捕获窗口 orderFront 到屏幕外"）；
② 夹具高度守卫（BACKLOG 32，`contentMustFit`）；③ 权重列的 VoiceOver 朗读；
④ 清单第 13 条（RecommendationWeights 的颜色/百分比）本轮只做了颜色语义，
"拖动时数值与滑块之间没有视线锚点"这一条**没动**，留给 R19。

---

## Round 19 · 上一轮那句"根因"是我自己编的；这一轮把它推翻

选题：BACKLOG 31（选中态能不能被机器看见）。开场缺陷清单（全部来自这一轮实测的帧与视图树）：

| # | 位点 | 缺陷 | 处理 |
|---|---|---|---|
| 1 | `QuickPickController.ensurePanel()` 的视图树 | R18 记的根因"浮层是 `NSVisualEffectView`，离屏不可合成"**是错的** | **已推翻**，换成有数字的原因 |
| 2 | 浮层 `NSStackView` 实测 `{{0,0},{24,49}}`（真实 App 里 420×300） | 滚动视图 0×0 ⇒ `NSTableView.visibleRect` 0×0 ⇒ 5 行一行都画不出来 | 原因钉进判据，帧继续缺席（BACKLOG 30） |
| 3 | `Fixture.appKit` 第一版返回 `NSView` | 尺寸断言核的是夹具自己填的数 | 改返回 `NSWindow`，**已修** |
| 4 | 判据 `rows > 0` | 控制器被释放后**仍然绿**（`numberOfRows` 报上次 reload 的 5） | 补接线断言，M82 由 ESCAPED 变 CAUGHT |
| 5 | `glass-pill-*` 三帧并排 | 暗色下药丸填充与底色 Δ=6（约 2/通道）——看着像"容器消失" | **判过不改**：分离由自适应描边（Δ 81/75）+ 投影承担 |

### 这一轮真正的产出是那条规矩

`M82` 打掉"夹具留住控制器"那几行之后，`rows > 0` 没红，红的是新加的
`table.dataSource is QuickPickController`。⇒ **症状会活过病因**：
表格的行数缓存与数据源的所有权是两件事，控制器没了读数照样"对"。
以后每写一条判据先问一句：**接线断了的时候，这条读数还会不会仍然正确？**
会，就说明它测的不是那件事。

### 三层判据（红得不一样，读的话也不一样）

```
CAPTURE_PROBE quickpick transparent=100.0% rows=5 stackWidth=24 dataSourceIsController=true bounds={{0,0},{420,300}}
```
`rows>0` 管症状 / `transparent>0.9` 管标题 / `stackWidth<100` 管**原因**。
第三条是这一轮新长的教训长出来的：一句作废的根因如果没人盯，下一轮就会拿它当前提。

### 顺手排除掉的一个候选解释

选中态那块黑：**把捕获窗口真的 orderFront 到屏幕外之后仍然是黑的**，
而 `isKeyWindow=false`（测试进程拿不到前台）。所以它要的是 key window，
不是"材质不可合成"。BACKLOG 31 的原因同步更正。

### 自评 86 / 100

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 16 / 20 | 药丸那一处判完确认不动；扣 4：本轮**没有**让任何界面变得更像系统 |
| 流畅度 | 12 / 20 | 零新增动效、零时序改善 —— 诚实的分 |
| 层次与材质 | 14 / 15 | 把"材质能不能离屏合成"从猜变成量过；扣 1：选中态仍看不见 |
| 动效细节 | 12 / 15 | 无新增参数；扣 3 |
| 交互反馈 | 9 / 10 | 接线断言补上后，浮层夹具的所有权有判据了；扣 1：仍无帧可看 |
| 可访问性 | 8 / 10 | 本轮未触碰；扣 2 |
| 性能 | 15 / 15 | 产品代码零改动（只有测试侧的 seam 改名），捕获多两次遍历 |

**低于 90 ⇒ 按规矩 R20 必须交付看得见的界面改善**，不能再来一轮纯量尺。
清单里没动过的动效项：提示条插入导致的布局位移（14）、搜索框清除按钮（15）、
骨架屏扫光曲线（16）、缩略图/图片 pop-in（24）、视频进度条步进（25）。

**验证**：`swift build` 0 warning；全量（开在屏探针）`Executed 680 tests, with 16 skipped and 0 failures`；
脚本 72 passed；帧基线 **98 张不变**（本轮零像素改动，`CHANGED=0 MISSING=0 ADDED=0`）；
变异 **M81–M84 四支全 CAUGHT**（M82 在补接线断言之前是 ESCAPED，这条差异本身就是本轮结论）；
spike 与电池都在仓库外（`.scratch/motion-audit-2/`）。

**本轮欠的**：① 浮层三张帧（BACKLOG 30，原因已换对，下一步是"让 stack 拿到宽度"该由谁做）；
② 选中态取证（BACKLOG 31，已排除"上屏"这条路，剩"要 key window"）；
③ 本轮没做的界面改善（R20 的硬指标）。

---

## Round 20 · 悬停档与命中区：五颗圆形按钮重新判一遍，顺带把自己引入的回归抓回来

R19 的欠账是"本轮没有界面改善"。这一轮有，而且是**看得见的**：
四处小控件的悬停强度抬到控件档、详情区药丸撤掉叠上去的第二层、搜索框清除 × 的命中区从 14pt 到 22pt。

### 开场清单（本轮判过的位点，逐个点名）

| 位点 | 静置 | 悬停（改前 → 改后） | 命中区（改前 → 改后） | 判 |
|---|---|---|---|---|
| 详情区玻璃药丸 4 颗 | 不变 | 0.06+0.08 叠成 ≈0.14 → **只留 0.08** | 44pt 圆，不变 | 叠层是缺陷：比控件档高 1.75 倍 |
| 行首星标 | 不变 | 0.06 → **0.08** | 20pt frame，**不加** padding | 加 padding 会把文字列推右 8pt |
| 搜索框清除 × | 不变 | 0.06 → **0.08** | **14pt → 22pt** | 全 App 最小可点控件，管的还是要快按的动作 |
| 视频播放 / 静音 | 不变 | 0.06 → **0.08** | 22pt frame，**不加** | 同星标 |
| 侧栏五颗批量按钮 / 回执 × / 「移除」 | 不变 | R15 已是 0.08 | R15 已有 5/4pt | 复查：仍然对 |

### 本轮最该记的两条

1. **一条只数已完成部分的守卫，会把"没做完"钉成"边界"**。
   `XCTAssertEqual(consumers, 3)` 是 R15 留下的，五轮里一直绿，而另外五处圆形按钮一直用着给整行定的 0.06。
   改法不是把 3 调成 7，是换成**按形状要求每一处表态**：凡 `in: Circle()` 必须写 `hoverLevel:`。
2. **变异 M88 让一条守卫现出原形：它在数字符串，不在数参数。**
   旧守卫数"源码里出现过 `labelPadding:`"，于是 `labelPadding: 0`（意思正是"没有命中区"）**全绿通过**。
   现在读值（`> 0` 才算一处），并把总数改成按文件点名的账本。

### 真实视觉审查：一把行带尺，把"22 帧变了"压成一句话

| 帧 / 区域 | 最佳纵向位移 k | 残余不同行 |
|---|---|---|
| `content-with-history` 详情列（x 300–748pt） | **k=0** | **0** ⇒ 三处 `hoverLevel` 静置态确实零像素差，也没画坏药丸 |
| 同帧侧栏列 · 筛选段（y 96–136） | k=2px (1.0pt) | **0** ⇒ 纯平移 |
| 同帧侧栏列 · 搜索框（y 60–100） | k=1px | 16（两条边带）⇒ 框自己长高 1pt，正是设计 |
| `sidebar-history` 顶部（y 55–100） | k=2px | **0** |
| 设置 18 + 权重 4 + 热图 4 + 行 18 + 菜单栏 6 + 详情 14 + 药丸 4 帧 | — | 哈希未变 |

⇒ 22 帧改动 = **搜索框长高 1pt + 它下面整列平移 1pt**，别处 0 行不同。
另外逐张看过 `search-field-320x112-light/dark`（两态各一条填充带、× 垂直居中、右边距与左边距对称）
与 `sidebar-history` / `content-with-history` 的亮暗四张。

量尺卫生一条（差点变成假归因）：第一次跑列范围时 zsh 没做词分割，`300 750` 被吞成一个参数、
静默退回全宽 —— 是脚本自己打印的"列范围 0–750pt"暴露的。**判据要报出自己的配置。**

### 本轮自己引入又自己抓到的回归

只加 `labelPadding: 4` 之后，搜索框**空态 31pt、有字态 32pt**（打字时框自己跳）。
根因不是数值，是**这一行的定高者换了**（文本列 17pt vs × 的 22pt）。
第一次修（垂直内边距 7→5）只把方向反过来；真正的修法是文本列自己声明 22pt。
顺带发现 `search-field` 夹具 320×**96** 一直在裁自己的下半条（与 R18 的 `weights` 裁头同族，
但这次是**内容高度**从来没人核）⇒ 抬到 112，帧基线仍 98 张、名字随之变成 `search-field-320x112-*`。
新判据 `testSearchFieldKeepsTheSameHeightInBothStates` 把两态**真的量一遍**（带高差 ≤ 2px），
且自己渲染自己判（预检把它打回：第一版只读别人写好的 PNG，靠测试顺序才成立）。

### 自评 89 / 100

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 17 / 20 | 命中区与悬停档现在都对齐系统工具栏那颗的语言；扣 3：× 静置仍低于可辨线（见下） |
| 流畅度 | 15 / 20 | 零新增时序；`.hover` 0.12s 现在真的能被小控件看见。扣 5：本轮没动任何时长/曲线 |
| 层次与材质 | 13 / 15 | 撤掉药丸那层多余的叠加（真实的层级修正）；扣 2：档位差仍然无法从帧里读出 |
| 动效细节 | 13 / 15 | 无新参数，但既有参数第一次"每一处都表态"；扣 2 |
| 交互反馈 | 9 / 10 | 命中区 14→22pt、小控件悬停从"等于没有"到 8%；扣 1：悬停态无帧可看，只有源码判据 + 人工 |
| 可访问性 | 7 / 10 | **扣 3 是应该的**：本轮看着帧量出静置对比度暗 2.22 / 亮 1.86（地板 3.0），开了 BACKLOG 33 却没修 |
| 性能 | 15 / 15 | 全是常量与布局声明；捕获多拍一次搜索框夹具 |

**89 < 90 ⇒ R21 继续修**，方向已经量出来了：图标控件的静置对比度（一把从文字推广到控件的尺 + 改色），
顺带把 BACKLOG 32 那条夹具高度守卫（`contentMustFit`）做掉 —— 本轮又一次靠人眼才发现夹具在裁自己。

---

## Round 21 · 可辨线推广到控件：`.tertiary` 的真名字不是"次要"，是"看不见"

R20 收尾时看着帧量出来的那条（清除 × 静置 1.86/2.22，地板 3.0）本轮处理。
不是"把它改亮"，是**让这件事从此可判**：一把跑在产物像素上的尺 + 一条按文件点名的源码账本。

### 开场清单（本轮判过的位点，带数）

| 位点 | 改前 亮/暗 | 改后 亮/暗 | 地板 | 判 |
|---|---|---|---|---|
| 搜索框清除 × | 1.86 / 2.22 | **3.74 / 5.34** | 3.0 | 缺陷，修（静置 `VisualInk.control`） |
| 多文件行展开箭头 | 1.88 / 2.27 | **3.85 / 6.06** | 3.0 | 同一族，修；它还踩着 10pt 字号下限 |
| 药丸收藏星 | 4.43 / 7.86 | 不变 | 3.0 | 参照位：本来就用 `.secondary` —— **尺要能同时说"过"** |
| 侧栏批量按钮 | 14.56 / 12.43 | 不变 | 3.0 | 参照位 |
| 热图星期/月份刻度 | 仍 `.tertiary` | 不变 | — | 非控件，**点名登记**；要不要抬档等文字尺（BACKLOG 34） |
| 行首星标 / 播放 / 静音 | `.secondary` 字面量 | 不变 | 3.0 | 与 `hoverLevel` 绑在一起，刻意不并入 `VisualInk` |

### 三条"判据抓作者"（本轮的密度比分数更值得记）

1. **尺的算术要真值表，而它会抓到作者的普适化错误**：我写"墨越暗对比度越高"，
   在黑底那一支是反的（`contrastRatio(180,0)=10.13 > (100,0)=3.55`）—— 尺把这条打红了。
2. **像素探针必须自带"这块真的有墨"的地板**：我估了五个框，**两个贴在空白上**
   （回执 × 与行首星标）。只判对比度时空白会读到 1.0 ⇒ 一条**假缺陷**；
   有墨地板才红成它真正的意思（"框贴到空白，去看元素搬到哪儿"）。⇒ 框只能从帧上量，不能估。
3. **R15 那条"死令牌会打红"把我放错文件的常数抓了出来**：`VisualContrast.*` 第一版写在
   `VisualTokens`，全量测试立刻红三条 —— 它是对的：**地板不是产品画的东西** ⇒
   搬到 `UICaptureHarness.InkFloor`；产品侧只留真的被两处视图读的 `VisualInk`，
   而没有任何消费者的 `smallText=4.5` 直接删（没有消费者的门槛等于没有门槛）。

另外升级了一条规矩：**变异电池从此核对"红得对不对"** —— 每支除 CAUGHT/ESCAPED 之外，
还要在失败输出里找得到期望文本（M92 必须红在墨地板那条，不能红在对比度那条）。
"红了"与"红得对"是两件事，与 R19 那条"症状会活过病因"同族。

### 真实视觉审查

行带尺读数：本轮 6 帧变化 = `detail-3-files` 三条 9pt 带（三颗箭头各一条）+
`search-field`、`sidebar-no-results` 各一条 12.5pt 带（就是那颗 ×），
**k=0 就对齐 ⇒ 零几何牵连**（与 R20 那次"框长高 1pt、整列平移 1pt"正好形成对照）。
逐张看过暗色箭头排与暗色搜索框：箭头现在比文件名淡、与类型图标同档，
层级读起来是"内容 > 可点 > 说明"；× 变成系统搜索框那颗取消按钮的分量，没有抢正文。

### 顺手排除的一条假缺陷

原以为提示条那对非对称时长有一条没生效（驱动 `.animation` 用的是 `.bannerIn`）。
读 `MotionCatalog.asymmetricTransition` 发现它**已经给两个方向各自绑了 `.animation`**，
注释里写的正是"不显式绑上去移除会借用插入那一档" ⇒ 那条不成立，清单 14 只剩"顶不顶得下内容"。
**"我以为有缺陷"与"我读了它"是两件事，后者便宜得多。**

### 自评 91 / 100

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 18 / 20 | × 与箭头现在都对上系统那颗取消/披露记号的分量；扣 2：热图刻度仍未量 |
| 流畅度 | 14 / 20 | 本轮零时序改动（诚实扣分） |
| 层次与材质 | 14 / 15 | "能点 > 类型说明"这个次序从此正确；扣 1 |
| 动效细节 | 12 / 15 | 无新增参数，但排除了一条假的时长缺陷；扣 3 |
| 交互反馈 | 9 / 10 | 指到变亮 + 底色药丸两条一起说；扣 1：悬停态仍无帧 |
| 可访问性 | 9 / 10 | 量出来的缺陷修了，还立了能推广的尺；扣 1：探针只覆盖 4 / 约 14 处 |
| 性能 | 15 / 15 | 判据多拍 8 张（约 1.3s），产品零开销 |

**验证**：`swift build --build-tests` 0 warning；全量 `Executed 685 tests, 25 skipped, 0 failures`；
脚本 72 passed；帧基线 98 张（6 changed，同提交 update）；变异 **M90–M94 五支全 CAUGHT**
（预检 3/3 绿、`RESTORE_CLEAN=yes`、每支都核对失败消息）。

**达标（≥90），但按"连续多轮达标才收口"的规矩继续跑**：R22 做清单 14 剩下的那一半
（提示条插入会不会把内容顶下去、顶下去要不要动画），顺带做掉 BACKLOG 32（`contentMustFit`）。

### R21b · CI 把这条判据打红（补记，不改分数）

推上去之后 CI 红一条，红的正是本轮立的像素判据：本机 32.5/33.0pt，runner 15.5/17.0pt。
根因与修法记在 U-43 的 R21b 一节与 D-080。对本轮自评的影响只有一条：
**"像素尺能不能当判据"这件事我原本给的分太高** —— 低对比表面（0.035 填充 + 0.05 描边）
在另一台机器上会被读没，这类表面今后只能判布局。
顺带那半 pt 的真缺陷（× 的固有高度 14.5pt）修掉了，容差收到 0.2pt，
变异加到 **M90–M96 七支全 CAUGHT**。

---

## Round 22 · 取证面一轮：夹具不许替产品做决定，"绿"要能区分跑过与被跳过

本轮没有界面改动 —— 交付的是**让某些缺陷从此可判**：
`contentMustFit`（10 张自包含帧 + 一张正对照）、横幅"移除那一臂"的清单判据、
以及一张以前不存在的帧 `content-with-two-notices`。

### 真实视觉审查（本轮看的帧）

`notice-banner-560x170-light`（组件两条并排）、`content-with-two-notices` 亮暗、
`content-with-history` 与它的差异，外加沿一列报 RGB 的色度扫描：

| y（pt） | 读数 | 判读 |
|---|---|---|
| 0–88 | `(255,241,229)` R-B=+26 | 橙色 12% 的警告横幅底 —— **一条文字却占 88pt** |
| 90–140 | `(254,235,235)` R-B=+19 | 红色 10% 的错误横幅底 —— 两行文字只占 50pt |
| ≥145 | `(248,248,248)` R-B=0 | 详情区底 |

判过不改的：两条横幅**挨着放**（每条自带 `Divider`）读起来像"一叠状态行"，与系统邮件的提示堆同一种语言 ⇒ 不改。
判完没判的：那 88pt。两个候选解释（底色涂到透明标题栏后面 / 那里其实是两条同色横幅）都还没排除 ⇒ BACKLOG 35，R23 第一件事。

### 本轮最值钱的一条

变异电池第一版报 `M97/M98/M99 ESCAPED` —— 看着像守卫没牙，
真相是**那三条测试整批被跳过**（`testCaptureKeyViews` 没设 `CLIPBOARD_HISTORY_UI_SHOTS` 就 skip，
而 skip 的退出码是 0），**预检把跳过读成了绿**。
补上"只有 skipped ⇒ DID-NOT-RUN"并让电池自己开闸之后：**M97–M100 四支全 CAUGHT**，
每支还核对失败消息（M97/M98 必须红在"正在裁自己"，M99 必须红在正对照"这把尺瞎了"）。

⇒ 写进规矩：**凡是靠环境变量开闸的判据，变异脚本必须负责把闸打开**；
否则那条判据在电池里等于不存在，而"预检全绿"会替它背书。

### 自评 87 / 100

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 15 / 20 | 零界面改动；扣 5 |
| 流畅度 | 12 / 20 | 零时序改动，但补上"移除那一臂有人判"；扣 8 |
| 层次与材质 | 14 / 15 | "两张横幅同时在"从此进基线；扣 1 |
| 动效细节 | 12 / 15 | 无新参数；扣 3 |
| 交互反馈 | 9 / 10 | 撤走判据在了；扣 1：本机时钟今天分辨不了 120ms |
| 可访问性 | 8 / 10 | 本轮未触碰；扣 2 |
| 性能 | 15 / 15 | 多两张帧，产品零改动 |

**验证**：0 warning；`687 tests / 25 skipped / 0 failures`；脚本 72 passed；
帧基线 98 → **100**（同提交 update）；`MATERIAL_BLIND_SPOTS 9 of 50`；
变异 **M97–M100 四支全 CAUGHT**，预检 2/2 真绿（不是跳过）。

**87 < 90 ⇒ R23 必须交付看得见的界面改善**（BACKLOG 35 那条 88pt 的横幅底，先诊断再修）。

---

## Round 23 · 提示条的底色不再涂到标题栏后面：一条文字的横幅从 88pt 变 38pt

R22 量出来一个说不通的事实却没敢动（两种解释对应两种互斥改法）。
本轮先诊断、再修、再立一条自带正对照的判据。

### 诊断（不猜，量一次）

| 手段 | 读数 | 结论 |
|---|---|---|
| 临时 `GeometryReader` 探针 | `safeAreaTop=52.0  size=(750,508)` | 安全区确实是 52pt |
| `inspect_r20.swift column`（新加，沿一列报 RGB 均值） | 修前 y 0–52 = `rgb(255,241,229)` | **底色铺进了安全区**，那里没有第二条横幅 |
| 同一把尺，修后 | y 0–46 = `rgb(255,255,255)`，色带从 54 开始 | 装饰区恢复中性 |

⇒ 根因：SwiftUI 4 起 `.background(ShapeStyle)` 默认 `ignoresSafeAreaEdges: .all`。
修法一行，macOS 12 走 `else`（12 的默认行为本来对）——
**不写"两边都凑合"的负 padding**。

### 修完的账

| 量 | 修前 | 修后 |
|---|---|---|
| 一条文字的横幅总高 | 88pt | **38pt** |
| 装饰区 `R-B` | +26 | **0.0** |
| 横幅自己那一条 `R-B` | +26 | +24.9（底色没被削掉） |
| 行带尺归因 | — | 4 张帧变，每张**恰好** `0.0–52.0pt` 不同，以下逐像素相同 ⇒ **零布局位移** |

### 真实视觉审查

暗色与亮色各看修前/修后的顶部 200pt。修前：整条工具栏被染成警告色、红绿灯压在橙色上、
第一条横幅像被塞进一个高盒子；修后：工具栏中性，两条横幅各自紧凑、文字垂直居中 ——
读起来才是系统里"内容区顶部提示条"那种东西。**这是本轮看得见的改善。**

### 判据（自带正对照）

`testNoticeTintDoesNotReachTheTitlebar`：先要求横幅那条带 `R-B > 8`，再要求装饰区 `|R-B| < 4`。
变异 **M101**（把修回去掉）、**M102**（把色度尺弄瞎）、**M103**（把采样框挪到空白处）
三支全 CAUGHT，且各自红在该红的那条断言上。

### 自评 90 / 100

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 18 / 20 | 提示条从此不染窗口装饰；扣 2：组件帧还在展示产品里没有的 12pt 间距（BACKLOG 36） |
| 流畅度 | 13 / 20 | 本轮零时序改动；扣 7 |
| 层次与材质 | 14 / 15 | 底色与内容对齐了，安全区不再和视觉打架；扣 1 |
| 动效细节 | 12 / 15 | 无新参数；扣 3 |
| 交互反馈 | 9 / 10 | 提示条的"存在感"回到正常档；扣 1：悬停仍无帧 |
| 可访问性 | 9 / 10 | 红绿灯不再压在色带上；扣 1 |
| 性能 | 15 / 15 | 一行分支，产品零开销 |

**验证**：0 warning；`688 tests / 25 skipped / 0 failures`；脚本 72 passed；
帧基线 100（4 changed，同提交 update）；变异 M101–M103 全 CAUGHT。
诊断用的探针夹具**没有留在基线里**（它产出一张 `Color.clear` 覆盖图 = 谁也不审的死帧）。

---

## Round 24 · 提示条的正文比它自己那枚按钮暗三倍：文字侧第一次有尺（U-46 / D-083）

### 开场读数（100 张帧，逐带自动定位，两外观）

| 位置 | 读数 | 判 |
|---|---|---|
| 三张横幅帧的正文（亮色） | **3.82 / 3.85 / 3.90 / 3.92** | 不达 AA（13pt 常规要 4.5）→ **修** |
| 同三张帧（暗色） | 5.26 / 5.33 / 5.50 / 5.58 | 过线，但仍低于按钮 → 一并升档 |
| 同帧那枚"知道了" | 12.28（亮）/ 8.31（暗） | 层级倒置：下一步比"发生了什么"响 |
| `notice-banner` 组件帧 y 86–99 | **13pt 无底色空缝**（产品 1pt） | 夹具在替产品决定布局（BACKLOG 36）→ **修** |
| 多行横幅的按钮中心 y≈66 / 带 41–92 | 压在上三分之一 | 系统那类是垂直居中 → BACKLOG 37 |

### 做了什么（3 个代码文件）

1. `StatePresentation.messageInk(for:)` —— 墨色按**严重度**分档（`.warning`/`.error` ⇒ `.primary`，
   `.loading`/`.empty` 留在 `.secondary`），`StateLine` 从"硬写一档"改成走档位。
2. `UICaptureHarness.noticeBands` —— 文字侧的对比度尺，**自己找带**（逐行众数 + 色度断带），
   带内只量文字列（避开图标 36pt、避开按钮 95pt）。
3. 组件帧 `notice-banner` 的 `VStack(spacing: 12)` → `0`，与产品同值。

### 修完的账

| 量 | 修前 | 修后 |
|---|---|---|
| 亮色正文对比 | 3.82–3.92 | **12.98–13.94** |
| 暗色正文对比 | 5.26–5.58 | **10.48–11.54** |
| 组件帧带间缝 | 13pt | **1pt**（与产品同值） |
| 行带尺归因 | — | 产品两张帧**只有字母那层**变（`content-with-notice` 仅 y 64–93）；`content-with-history` 与九张 `settings-*` **rows=0** ⇒ 零布局位移 |

### 真实视觉审查

亮/暗各看修前修后的组件帧全幅与产品帧顶部 160pt。修前亮色：正文是灰的，第一眼落到右边那枚按钮上，
横幅像"一条底色 + 一句注释"；修后：正文是黑的，图标（橙/红）与文字各在其位，两条横幅之间只剩发丝线。
暗色同样明显（5.3 → 10.5），而提示条**没有变成抢眼的块** —— 底色仍是那 10–12% 的暖色，动的只有墨。
**这是本轮看得见的改善。**

### 量尺这一轮自己犯的三件事

1. **移植时丢括号 ⇒ 尺瞎得静悄悄。** 原型写 `(UInt(r) << 16) | …`，搬进判据时写成
   `Int(bytes[o]) / 16 << 8` —— **Swift 里 `<<` 优先级高于 `/`**，于是 `255 / 4096 = 0`，
   所有行的色度变负数 ⇒ 永远找不到带，而表现是"0 条带"不是崩溃。
   逼出它的是**正对照**（它红了），主判据当时甚至还没跑到。
   ⇒ "原型跑通了"不等于"移植跑通了"：同一把尺要在同一份输入上重量一次。
2. **判据里 `goodBands[0]` 把测试进程打死**（signal 5），后面判据一条没跑 ——
   崩溃是把红伪装成"环境坏了"的一种。改成 `guard let` + `XCTFail`。
3. **我按估值把组件帧 170 → 150，被上一轮自己写的 `contentMustFit` 打红**（底行 95.7% 有墨）。
   量出来这张帧的内容是 y41–160 ⇒ 高度**保持 170**。
   这条守卫第一次是在"我改夹具"而不是"产品改布局"的场景下救回来的。

### 变异对照 M104–M109（6/6 CAUGHT，`RESTORE_CLEAN=yes`）

M104 正文退回 `.secondary`、M105 组件帧回 spacing 12、M106 **产品**塞 12pt 缝、
M107 弄瞎分带、M108 挪走文字列、M109 加载态一起升档。
**M108 红得与我预测的不同**：它红在对比度地板（4.13）而不是墨地板 —— 挪过去的框里躺着那枚按钮，
墨占比 10.9% 轻松过 2% 的地板。⇒ "带里有墨"这条地板只挡"框套在纯底色上"，
挡不住"框里有别的控件"（BACKLOG 38 已把补法写清：要求带首 60pt 内有墨）。

### 自评 92 / 100

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 19 / 20 | 提示条回到"正文为主、色彩示警"的系统语言；扣 1：按钮垂直位置仍非系统习惯（37） |
| 流畅度 | 13 / 20 | 本轮零时序改动；扣 7 |
| 层次与材质 | 15 / 15 | 层级倒置被量出来并修掉，且没有靠加粗/放大解决 |
| 动效细节 | 12 / 15 | 无新参数；扣 3 |
| 交互反馈 | 9 / 10 | 扣 1：悬停/按压仍无帧可证 |
| 可访问性 | 10 / 10 | 亮色从 3.9 提到 13+，AA 地板第一次有判据守着文字侧 |
| 性能 | 14 / 15 | 产品侧只多一个 switch；扣 1：判据自己拍 6 张帧，CI 时间 +约 3s |

**验证**：0 warning；`692 tests / 27 skipped / 0 failures`（+4 条新判据；两条 skip 是
`CLIPBOARD_HISTORY_UI_SHOTS` 门住的捕获/探针判据，与本轮改动无关）；脚本 72 passed；
帧基线 100（6 changed，同提交 update，compare 现 CHANGED=0）；变异 6/6 CAUGHT。

### 下一轮（R25）

清单里仍未判过的位点：16 骨架屏扫光曲线、17 菜单栏图标语言、22 `wand.and.stars` 字重、
24 缩略图 pop-in、25 视频进度条步进、26 `symbolEffect` 12/13 分叉、27 GlassPill 材质切换；
本轮新开：**37** 多行横幅里动作按钮的垂直位置（有现成判据雏形）、**38** 带内文字列的左锚定地板。
BACKLOG 30/31/34 的剩余部分继续挂着。

---

## Round 25 · 一行里需要两根对齐轴：动作按钮跟着第一行走了一路（U-47 / D-084）

### 开场读数（三张横幅帧 × 两外观，逐带自动定位；`inkRowSpan` 量按钮字形行）

| 带 | 带中心 | 按钮行中心 | 偏移 |
|---|---|---|---|
| 产品 `content-with-notice`（两行正文） | 77.5 | 71.0 | **−6.5pt** |
| 组件帧 `notice-banner`（三行正文） | 132.5 | 118.0 | **−14.5pt** |
| 产品 `content-with-two-notices` 第一条（单行） | 71.0 | 71.0 | **0pt ⇒ 碰巧对，这张帧从没暴露过它** |

### 做了什么（2 个代码文件）

1. `StateLine`：内层 `HStack(alignment: .firstTextBaseline)` 钉住图标与文字，
   外层换 `.center` ⇒ **只有动作位换轴**。系统那类顶部提示条的动作就是垂直居中的。
2. `UICaptureHarness`：新增 `inkRowSpan` + `testNoticeActionIsVerticallyCenteredInItsBand`
   + 三端正对照 `testActionSpanRulerReadsBothEnds`。

### 修完的账

| 量 | 修前 | 修后 |
|---|---|---|
| 10 条带的按钮偏移 | 0 / −6.5 / −14.5pt | **全部 +0.0** |
| 多行横幅高度 | 51 / 67pt | **50 / 66pt**（−1pt，见下） |
| 变异 | — | M110–M113 四支全 CAUGHT，`RESTORE_CLEAN=yes` |

**本轮不是零位移**：每条多行横幅矮 1pt（以前按钮下沿把行撑高 1pt），
所以单条横幅下面整列上移 1pt、两条则 2pt；行带尺报 530 行不同正是这个平移。
这条与 R23 的"恰好 0–52pt 不同、以下逐像素相同"是两种结论，账本里分开写。

### 量尺自己错过的两件事

1. **两张同构的帧读出不同的数，先怀疑尺**：动作框第一版开在"右侧 95pt"，
   同一套代码在 560pt 宽的组件帧读 +0.0、在 750pt 宽的产品帧读 −4.2 ——
   因为长句第一行排到 x≈670 混进了框里，把"首末有墨行"抬上去了。
   收窄到右侧 50pt（按钮的实际位置）后两边一致。⇒ 与 R24 的 M108 同一族：**框的边界要由被量对象决定**。
2. **"没找到"必须返回 nil**：兜底值会把"按钮不见了"读成"偏 0pt，完美居中"。
   M113 专门把兜底值塞回去，正对照红在"空矩形必须返回 nil"上。

### 真实视觉审查

亮/暗各看组件帧全幅与产品帧顶部。修前那条三行提示里"知道了"贴在最上面一行旁边，
像"这一句的确认"，下面两行没有归属；修后它在整条带的正中，读起来是"这一条提示的确认"。
单行横幅观感不变 —— 这正说明这个位置以前**没有任何东西在守**。

### 自评 91 / 100

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 19 / 20 | 动作位回到系统语言；扣 1：横幅右缘仍是我自己定的 14pt，不是系统度量 |
| 流畅度 | 13 / 20 | 本轮零时序改动；扣 7 |
| 层次与材质 | 14 / 15 | 一根轴拆成两根，图标与文字的基线关系没动；扣 1 |
| 动效细节 | 12 / 15 | 无新参数；扣 3 |
| 交互反馈 | 9 / 10 | 扣 1：按钮的悬停/按压仍无帧可证 |
| 可访问性 | 10 / 10 | 动作位的可达性不变，命中区没缩；居中后视觉归属更清楚 |
| 性能 | 14 / 15 | 产品侧只多一层 HStack；扣 1：判据又加一次自拍（CI +约 3s） |

**验证**：0 warning；`694 tests / 27 skipped / 0 failures`（+2 条判据）；脚本 72 passed；
帧基线 100（6 changed，同提交 update，compare 现 CHANGED=0）；变异 4/4 CAUGHT。

### 下一轮（R26）

未判位点：16 骨架屏扫光曲线、17 菜单栏图标语言、22 `wand.and.stars` 字重、24 缩略图 pop-in、
25 视频进度条步进、26 `symbolEffect` 12/13 分叉、27 GlassPill 材质切换；
BACKLOG 30 / 31 / 34（剩余三处文字表面）/ 38（带内文字列的左锚定地板）仍开放。

---

## Round 26 · 加载态从来没有进过帧基线；第一次拍到它就看到两条左轴（U-48 / D-085）

### 开场读数（51 夹具 × 两外观；这一轮的"缺陷清单"第一条是**表里没有这一行**）

| 量 | 值 | 判 |
|---|---|---|
| 加载态夹具数 | **0** | 全 App 唯一的常驻动效从没被帧看过 → **先造帧** |
| `detail-loading` 条带左缘 | x=**0.0**（gutter 应为 20） | 落地瞬间整块右跳 20pt → **修** |
| 那一句"正在加载预览…"左缘 | x=**316.5** | 与条带两条轴 → **修** |
| 条带对面板 | Δ13（255 vs 242，1.09:1） | **判为不改**：装饰性表面，AA 两根线都不适用 |
| 详情头部左缘 | x=54.5 | 与 gutter 不同轴 ⇒ 设计问题，开 BACKLOG 39 |

### 做了什么（3 个代码文件）

1. `loadingView`（私有计算属性）→ **`DetailLoadingView`**（具名 + `reduceMotion` 注入点）⇒ 可以被确定地画一次。
2. `VStack(alignment: .leading)` + `.padding(.horizontal, DetailTypography.containerGutter)`。
3. 判据：`leadingInkColumn` / `skeletonAxisReadings` / `testLoadingBlockSharesTheDetailColumnsAxis`；
   并把 R24 欠的 **BACKLOG 38**（左锚定地板）补进横幅判据。
4. 旧接线守卫升级：分支必须画那个**类型**，且 `detail-loading` 帧必须画**同一个类型**。

### 修完的账

| 量 | 修前 | 修后 |
|---|---|---|
| 条带 / 句子 / 令牌 三条左轴 | 0.0 / 316.5 / 20 | **20.0 / 20.5 / 20**（亮暗一致） |
| 帧基线 | 100 | **102**（新帧 2 张，同提交 update） |
| 归因 | — | 全 102 帧只有 `detail-2-file` 变，且恰好是条带与句子的四段（84–156.5pt） |
| 变异 | — | M114–M119 六支全 CAUGHT |

### 这一轮最值钱的一条：M116 第一次**逃逸**

我第一版跨帧判据写的是"加载块的左轴必须等于 `detail-2-file` 里最左的强墨"。
而那张帧里最左的强墨**就是同一个加载块的句子**（骨架在 `detail-2-file` 里也在画）
⇒ 把 gutter 去掉，两边一起从 20 挪到 0，判据照样绿。**ESCAPED。**
⇒ **跨帧对照必须先证明两帧量的是不同的东西，否则那是自己跟自己比。**
第二版改成"必须落在产品自己的 gutter 令牌上"，M116 立刻红在正确的句子上（`左轴在 x=0.0，而 gutter 是 20pt`）。
这条与 R24 的 M108 是同一族的两个方向：M108 是"框里有别人"，M116 是"对照物就是我自己"。

### 真实视觉审查

第一次把加载态画出来看。修前：三根几乎看不见的灰条贴着窗口边，下面一句居中的"正在加载预览…"，
整块像两个互不相干的东西叠在一起；修后：条带与句子同一条左轴、与详情栏 gutter 对齐，
读起来是"这块内容正在长出来"。亮暗一致。**这是本轮看得见的改善**，
而且属于"不拍出来就永远不会有人发现"的那一类。

### 自评 92 / 100

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 18 / 20 | 加载块回到详情栏的列语言；扣 2：头部 54.5 与 gutter 20 仍不是一套（BACKLOG 39） |
| 流畅度 | 13 / 20 | 本轮零时序改动（扫光本身判为"已对"）；扣 7 |
| 层次与材质 | 15 / 15 | 两条轴合一，且没有靠加粗/加深抢正文 |
| 动效细节 | 12 / 15 | 无新参数；扣 3 |
| 交互反馈 | 9 / 10 | 扣 1：加载→内容的交叉淡仍未在帧上取证（只有结构判据） |
| 可访问性 | 10 / 10 | 减弱动态那一档第一次有帧可审 |
| 性能 | 15 / 15 | 产品侧只是把属性提成视图；判据自拍 +约 3s |

**验证**：0 warning；`695 tests / 27 skipped / 0 failures`（+1 条判据，另 1 条旧守卫升级）；
脚本 72 passed；帧基线 **102**（2 added + 2 changed，同提交 update，compare 现 CHANGED=0）；
变异 M114–M119 六支全 CAUGHT，`RESTORE_CLEAN=yes`。

### 下一轮（R27）

未判位点：16 扫光曲线（本轮判"保持"，但 `MotionCatalog.skeletonSweep` 的 curve/transition 两支仍是死的）、
17 菜单栏图标语言、22 `wand.and.stars` 字重、25 视频进度条步进、26 `symbolEffect` 12/13 分叉、
27 GlassPill 材质切换；BACKLOG 30 / 31 / 34（剩余三处文字表面）/ 39。

---

## Round 27 · 要读的标签不许比能点的笔画更淡：`.tertiary` 从产品里清零（U-49 / D-086）

### 开场读数（三处文字列 × 两外观，框从帧上量）

| 位置 | 修前 | 修后 |
|---|---|---|
| 月份刻度 | 亮 **1.88** / 暗 **2.27** | 亮 **3.85** / 暗 6.06 |
| 星期刻度 | 亮 **1.88** / 暗 2.27 | 亮 **3.75** / 暗 6.06 |
| 图例"少 / 多" | 亮 **1.88** / 暗 2.27 | 亮 **3.85** / 暗 6.06 |

触发这一轮的是一句**上一轮写下的免检理由**：R21 把 `.tertiary` 判为"看不见"之后，
给热图刻度留了 3 处例外，理由是"那不是控件，是刻度文字"。
本轮按目标里"不许假设任何现有判断是对的"重新判 —— 数一模一样（1.88），
而刻度恰恰是这张图里**唯一被读的东西**。免检理由不成立。

### 三条决定

1. 三处提到 `.secondary`（全 App 说明文字那一档）。
2. **地板立成梯子**：`captionInk = 3.5` = "必须在 secondary（实测 4.0）那一档或以上"。
   刻意**不追 WCAG 4.5** —— 系统的 `secondaryLabelColor` 自己就只有 4.0，
   用 4.5 钉 caption 会把层级压平，换来一个不像系统的东西。
   正文 4.5（R24）与说明 3.5 是两种角色，不统一成一个数。
3. `.tertiary` 的点名账本清空 ⇒ 以后要用这一档必须先登记并写清"它为什么不是要读的东西"。

### 变异 M120–M122（3/3 CAUGHT）

M120 刻度退回 `.tertiary` → 红在梯子（1.83:1）；M121 账本之外再用这一档 → 红在点名守卫；
M122 星期框挪到空白 → 红在"只有 0.0% 的墨"（墨地板有牙，不会红成一个假的低对比度）。

一个过程细节值得记：M120 第一次注入时 needle 命中 5 次（这个文件本来就有两处合法的 `.secondary`），
电池按规矩报 **DID-NOT-RUN 不注入** —— 裸 needle 一次改五处，那是变异在撒谎。
换成三根带上下文的 needle（各命中 1 次）才拿到真实的红。

### 真实视觉审查

亮暗各看整张热图。修前月份与星期几乎化在底里，得靠 hover 才知道"这是几月"；
修后刻度是清楚的灰，仍比副标题淡一档、比标题淡两档 —— **层级没有被压平**，
只是从"看不见"回到"系统里说明文字的样子"。暗色变化更明显（2.27 → 6.06）。

### 自评 91 / 100

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 19 / 20 | 说明文字回到系统 caption 档；扣 1：图例方格的深浅阶梯本轮没判 |
| 流畅度 | 13 / 20 | 本轮零时序改动；扣 7 |
| 层次与材质 | 14 / 15 | 修的是"淡到看不见"，没有靠压黑换可读；扣 1 |
| 动效细节 | 12 / 15 | 无新参数；扣 3 |
| 交互反馈 | 9 / 10 | 扣 1：hover 提示仍无帧可证 |
| 可访问性 | 10 / 10 | 三处从 1.88 提到 3.75+，且第一次有"梯子"这条判据 |
| 性能 | 14 / 15 | 产品侧只换色档；扣 1：判据自拍 6 张帧 |

**验证**：0 warning；`696 tests / 27 skipped / 0 failures`（+1 条判据）；脚本 72 passed；
帧基线 102（4 changed，同提交 update，compare 现 CHANGED=0）；变异 3/3 CAUGHT。

### 下一轮（R28）

未判位点：16 扫光曲线（`MotionCatalog.skeletonSweep` 的 curve/transition 两支仍是死的）、
17 菜单栏图标语言、22 `wand.and.stars` 字重、25 视频进度条步进、26 `symbolEffect` 12/13 分叉、
27 GlassPill 材质切换；BACKLOG 30 / 31 / 34（②）/ 39。
**这是阶段二的第 20 轮**（R9–R28 计），R28 之后开始收口：写 AGENT_FINAL_REPORT.md。

---

## Round 28 · 一句话被截掉的恰好是唯一那句理由（阶段二第 20 轮）

### 开场清单（逐屏逐元素，带上一轮遗留的坐标缺陷）

| 位点 | 内容 | 本轮判定 |
|---|---|---|
| 设置·侧栏 六枚 SF Symbol | 第 22 项重新判 | **不是产品缺陷**：离屏反相（亮帧画成白、暗帧画成黑），改成尺的分类 |
| 设置·快捷键 三行说明 | `.lineLimit(1)` | **缺陷已修**：第三行整句理由被切掉 ⇒ 换行 |
| 设置·数据 导出/导入两颗 | 帧里恒为禁用态 | **夹具缺陷已修**：补接缝 + 一条从产品推导名单的对账守卫 |
| 设置·数据 「清空」 | `.borderedProminent`+`.tint(.red)` 在帧里是浅灰 | **未判定** ⇒ BACKLOG 40 + 人工批次 36 |
| R27 遗留 | `captionInk = 3.5` 在 CI 红了两处 | **尺已改**：绝对地板 → 同机同外观的 `.secondary` 相对参照 |

### 这一轮的主线：三件不同的事长得像一件

看 `settings-general-*-light.png` 的侧栏，第一反应是"三枚图标几乎看不见"。
量下去才分层：`command` / `hand.raised` / `folder` 那三列的像素是 **(255,255,255)** 对背景 (248,248,248)，
暗色帧里换成 `wand.and.stars` / `chart.bar` 变成 **(0,0,0)** 对 (24,24,24)，
而**每一枚的 RGB 跨两张帧恒定、不随外观变**（选中那枚走 accent，两帧都对）。
这不是"淡"，是**反相** —— 语义色在这条离屏管线上被解析到了另一套外观，缓存粒度是符号名。

关键点是：上一轮我刚立了一条"要读的标签不许比能点的笔画更淡"的判据，
这一轮拿着它去量，量到 1.06:1，**唯一的修法就是把 `.primary` 换成固定色** ——
而那正是审计第二轮明文禁止的方向。区别只在"有没有把方向数出来"：
`ink()` 只数"偏离背景多少"，于是"画成白色"和"什么都没画"是同一个 0。
加了 `signedInk` 之后两者第一次可分（`command=0.0000（亮960/暗0）`），产品一行没改。

真正的产品缺陷在同一张帧的**内容列**：快捷键页第三行说明被 `.lineLimit(1)` 截断，
而 `HotKeyAction.quickPick.description` 后半句是整个设置页里唯一一句"为什么是这个键不是那个键"。

### 三条判据与一处回归修复

1. `testSettingsHelperTextIsNotClipped`：两臂对照。参照臂是新夹具 `settings-shortcuts-wide`（1100×540），
   宽到不可能截断 ⇒ "这一页一共画了多少字"有一个不依赖我判断的值。
   两臂的标题、三块录制框、三颗按钮逐像素同构，只有说明文字会差。
   修后 1.003（亮）/ 0.998（暗）。**参照臂的资格本身也判**（必须宽于默认 +300），
   否则把 1100 改回 720 会让两臂自比 ⇒ 恒真且无一条判据会红。
2. `textInkMass` 的闸门 `textInkMinDelta = 60` + 七档真值表：把平涂的控件底色挡在"字"之外。
   不用 R24 那档 24 的理由是实测：每块录制框平涂 ≈14k 像素，整页文字 ≈17k ⇒ 信号被稀释一半，
   **而稀释不会让任何判据变红，只会让它变钝**。
3. `testCaptureFixtureInjectsEveryActionSeamTheProductInjects`：接缝名单从产品调用点推导，不手抄。
4. **R27 的回归**：`captionInk = 3.5` 是本机数，CI 的 macos-15 runner 上同一条红了
   （星期 2.85 / 图例 3.30，run 38443414396）—— 那两处产品用的就是 `.secondary`。
   改成相对参照之后本机读数比值 1.00–1.03，平台差被约掉，而 M128 证明"产品掉一档"仍然红（1.83 vs 参照 3.75 ⇒ 淡 51%）。

### 变异 M123–M129（7/7 CAUGHT）

M123 装回 `.lineLimit(1)` → 0.809/0.792 红在"有说明文字被截断了"；
M124 摘掉夹具接缝 → 红在点名那句；M125 闸门 60→24 → 红在真值表；
M126 宽臂 1100→720 → 红在"不再是不动的参照"（这一支存在的理由就是它不该绿着过去）；
M127 `signedInk` 阈值 4→400 → 红在"连一个像素都没动过"；
M128 图例退回 `.tertiary` → 相对参照仍然红；M129 参照自己掉档 → 红在"参照坏了"。

过程细节：M128 的失败消息暴露了我自己写的一个 bug ——
`String(format: "%.0fpt", 10)` 把 Int 递给 `%f`，打出来是 `0pt`。已改成字面量。
**变异电池不只测产品，也会把判据自己的毛病抖出来**，这一条已经不止一次了。

### 真实视觉审查

亮暗各看快捷键页整张：修前第三行"…直接粘回原应用。…"后面一片空白；
修后那句完整落在三行里，录制框与「恢复默认」垂直居中于整个文字块。
「数据」页：导出/导入两颗从灰底灰字变黑字，与「清空」同档。
侧栏那一列**画面零变化** —— 本轮刻意不动它。

### 自评 92 / 100

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 19 / 20 | 换行与系统设置同语言；扣 1：三行不等高是本分枝的取舍，不是系统强制 |
| 流畅度 | 13 / 20 | 本轮零时序改动；扣 7 |
| 层次与材质 | 14 / 15 | 没有靠改颜色去迁就帧；扣 1：「清空」的 prominent 档仍未判定 |
| 动效细节 | 12 / 15 | 无新参数；扣 3 |
| 交互反馈 | 9 / 10 | 扣 1：hover/禁用态仍只能靠人工批次 |
| 可访问性 | 10 / 10 | 一句被隐藏的取舍说明回到屏上；且把"绝对地板"换成平台无关的相对参照 |
| 性能 | 15 / 15 | 产品侧只改一处布局；判据自拍 2 张参照帧 |

**验证**：0 warning；`699 tests / 27 skipped / 0 failures`（+3 条判据）；
帧基线 102 → **104**（6 changed + 2 added，同提交 update）；变异 7/7 CAUGHT。

### 收口

**阶段二第 20 轮到此跑满**（R9–R28）。下一步：写 `AGENT_FINAL_REPORT.md`，
把二十轮的落地、砍单、未修与"尺子自己犯过的错"一次交清。

---

## Round 29 · 判墨的尺补上"方向"；参照臂退回拍得出来的那一档（阶段二第 21 轮）

### 开场（接着 R28 的两条尾巴）

| 位点 | 问题 | 本轮判定 |
|---|---|---|
| 三把判墨尺（控件 / 说明 / 正文） | 只读"偏离背景多远"，对**反相**失明 | **已补**：`inkTailSplit` + 失败消息挂方向诊断 |
| R28 的两臂对照 | 参照臂在 CI 上 900pt 仍整帧读 0 墨 | **已改**：参照换成更窄那一臂（640 vs 720），两臂都 ≤750pt |
| 我自己给的解释 | "越过 2048px 的离屏上限" | **被证伪**（900×2=1800px 也读 0）⇒ 只记现象，原因进 BACKLOG 42 |
| 变异 M130 | 第一次指错测试（打到两端对照上，而它测的是原始计数） | 改指真值表 ⇒ CAUGHT |
| 变异 M131 | 第一版"把一条断言改成恒真" ⇒ 必然 ESCAPED（弱化断言不会让它自己变红） | 改成**对调测量** ⇒ 两头都红，CAUGHT |

### 这一轮的正面产出：让"太淡"和"画反了"分开

`inkTailSplit` 取与 `inkContrast` **同一切法**的尾墨（偏离最远的那 2%），只回答"落在背景哪一侧"。
两条"太淡"判据的失败消息各挂一行诊断：反相 ⇒ **一行产品代码都不许改，去查捕获路径**。
正对照不构造，用真的坏帧：

```
INK_SIDE 图标列 亮35/暗0 标题列 亮0/暗118
```

同一张 `settings-general`、同一把尺、两个相反的读数。这是 R28 那次"手工看 RGB"的自动化版本。

### 两条方法论，都是电池自己抖出来的

1. **变异要打的是测量，不是断言。** 我第一版 M131 写的是"把反相那一端的断言改成恒真"，
   它绿着过去了 —— 这不是判据没牙，是这支变异本身没有意义：弱化一条断言永远不会让这条断言变红。
   改成对调 `inkTailSplit` 的两个计数之后，两端对照**两头都红**。
2. **变异要打对测试。** M130 第一次指向两端对照，而分类器只被真值表调用 ⇒ 恒绿。
   指回真值表后 CAUGHT。这两条与 R27 的"裸 needle 命中 5 次"是同一族：**电池的失败也是信息**。

### 真实视觉审查

本轮产品画面零变化（改的全是判据与夹具）。仍然逐屏看了受影响的三张：
`settings-shortcuts`（720）与 `settings-min`（640）两臂亮暗各看一遍 ——
第三行说明在两臂里都是完整三行/四行，没有省略号；
`settings-general` 的侧栏那一列与 R28 完全一致（本轮刻意不动它）。
撤下 `settings-shortcuts-wide` 之后基线 104 → **102**，`CHANGED=0`。

### 自评 90 / 100

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 17 / 20 | 产品画面零变化；本轮不加分也不扣系统观感 |
| 流畅度 | 13 / 20 | 无时序改动；扣 7 |
| 层次与材质 | 13 / 15 | 没有为了判据去动墨档；扣 2：正文那条判据还没挂诊断（已记 BACKLOG 41 剩余一半） |
| 动效细节 | 12 / 15 | 无新参数；扣 3 |
| 交互反馈 | 9 / 10 | 扣 1：hover/浮层仍无帧可证 |
| 可访问性 | 10 / 10 | "太淡"与"画反了"第一次可分，且正对照来自真帧 |
| 性能 | 16 / 15→**15** | 判据自拍 4 张帧；产品侧零成本（上限 15，记满） |

**验证**：0 warning；`701 tests / 27 skipped / 0 failures`（+2 条判据）；脚本 72 passed；
帧基线 **102**（撤下 2 张宽臂帧，同提交 update，`CHANGED=0`）；**变异 M123–M131 九支全 CAUGHT**。

### 下一轮

阶段二已跑满 21 轮（≥20 达标）。剩余开放项都在台账里且都需要人的输入
（BACKLOG 39 设计决定 / 40 真机截屏 / 41 剩余一半 / 42 runner 尺寸断崖定位）。
收口：更新 `AGENT_FINAL_REPORT.md` 到 21 轮。

---

## Round 29d · 暗档侧栏那五行字是黑字黑底 —— 这一轮先量后看，并且推翻了我自己刚才的"看"（阶段二第 22 轮）

### 开场（收口之后为什么还有这一轮）

| 位点 | 问题 | 本轮判定 |
|---|---|---|
| 我上一轮的肉眼复核 | 报了"暗档侧栏五个标签浅灰可读" | **撤回** —— 那一列最亮只比底亮 4，最暗是 (0,0,0)：黑字黑底 |
| `settings-*` 暗档帧的侧栏 | 未选中行的文字与图标落在背景**错误一侧** | **量成一条会红的账**（名单 9 条，两个方向都红） |
| R28 的"侧栏图标反相是捕获伪影" | 只覆盖了图标，没覆盖文字 | 文字同族，且**判别量是选中与否**（新事实，见下） |
| `.scratch` 取证尺 `modalColor` | 把 pt 当 px 用 ⇒ 背景取自目标区域左上角 1/4 处 | **已修**，据此下过的一条读数作废 |
| 产品 | 要不要改 | **零改动**（十三臂复刻体全画对，机制未定 ⇒ 改就是猜，D-089） |

### 本轮的正面产出：一把新尺 + 一条 counted blind spot

尾墨尺（`inkTailSplit`）在这里会**漏**：一块同时压着选中行白字与未选中行黑字的列里，
白字的偏离（≈200）把黑字的偏离（≈24）全部挤出"最远的那 2%" ⇒ 尺报"墨在期望侧 ✓"，
而那五行字在帧里一个字都看不见。于是补了整列按侧计数的 `inkSideCounts`：

```
TEXT_SIDE settings-shortcuts dark 亮侧=0    暗侧=2647 ⇒ 侧栏文字落在背景错误一侧（不可见）
TEXT_SIDE settings-general   dark 亮侧=851  暗侧=2130 ⇒ 同上（851 是选中那一行，它是对的）
TEXT_SIDE settings-min       dark 亮侧=0    暗侧=2647 ⇒ 同上
亮档同一列：暗侧 2100–2600（正常），亮侧 0
TEXT_SIDE_BLIND_SPOTS 9 of 9 settings fixtures（名单 9 条）
```

**判别量是"选中与否"**，不是页、不是帧宽（640 与 720 表现一致）、不是符号名 ——
这把 R28 那条"某些符号被画反"的描述收窄成了一句话：
*未选中行的整行内容（图标 + 文字）在暗档里不跟外观翻。*

### 真实视觉审查（这一轮按"先量后看"改写）

先给可数的读数（上面那三行），再看画面，并且**允许像素否决眼睛**：
`settings-min-640x440-dark.png` 裁上半张 → 我上一轮在这里"看见"了五个浅灰标签，
本轮量到的却是"该列最亮像素 (28,28,28) vs 底 (24,24,24)"。
同一张图、同一个人，两次结论相反 —— 差别只在于这次先看的是数。
亮档 `settings-min` / `settings-shortcuts` 与内容区标题（暗档 (221,221,221) vs 底 (24,24,24)）都正常。

### 两条方法论

1. **肉眼不是控制。** 目标要求每轮"看渲染出来的画面"，但眼睛会补全布局应该长什么样。
   从本轮起：看帧的结论必须配一个可数的读数，两者矛盾时以像素为准并回看尺取没取错位（BACKLOG 46）。
2. **尺的参照取错位置，比尺没有牙更危险。** `modalColor` 那个 pt/px 错报出来的
   "第 3 行有 3761 个亮墨"读的是第 1 行的胶囊 —— 它看起来完全像一个结论。仓库判据逐条核过，没这个错。

### 自评 89 / 100

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 17 / 20 | 产品零改动；扣 3：这一轮没有让任何画面变好 |
| 流畅度 | 13 / 20 | 无时序改动；扣 7 |
| 层次与材质 | 13 / 15 | 没为判据动墨档；扣 2：暗档侧栏的层级仍量不到 |
| 动效细节 | 12 / 15 | 无新参数；扣 3 |
| 交互反馈 | 9 / 10 | 扣 1：hover/浮层仍无帧可证 |
| 可访问性 | 10 / 10 | "暗档不可见的五行字"从散文变成一条两个方向都会红的账 |
| 性能 | 15 / 15 | 新判据自拍 9 张帧；产品侧零成本（上限 15，记满） |

**没到 90，差的是机制**。写完上面那段"下一步"之后我立刻把那一格补跑了 ——
**嵌套 `NSHostingView` 里装一列 `Button{Label}`**（E 与 N 的两半合起来），
以及"给嵌套视图钉死外观"这一版：

```
O 嵌套 hosting + Button 列（产品形状）  nested.appearance=nil（跟着窗口）  effective=dark
  文字列 亮侧=2499 暗侧=0  ⇒ 墨在亮侧（画对了）
P 同上 + 给嵌套视图钉外观              nested.appearance=钉死 darkAqua     effective=dark
  文字列 亮侧=2499 暗侧=0  ⇒ 墨在亮侧（画对了）
```

⇒ **八种形状全部画对**，仓库外的复刻体到不了这个现象。下一步只能在仓库里做二分，
而它需要一个真小的产品侧接缝：把 `SettingsSidebarView` 从 `private` 放开到 `internal`
（或给夹具一条"只搭侧栏"的入口），才能单独拍它、再逐层加回 `CompatibleSplitView` / `NavigationSplitView`。
这件事记在 BACKLOG 45，**不在本轮做**：为了测试放开可见性是一次真实的设计改动，
值得单独一轮并配它自己的判据，而不是在收口路上顺手改。

**验证**：0 warning；全量与基线见 `AGENT_STATE.md` R29d；脚本 72 passed；
变异 **M132–M134 三支全 CAUGHT**（`/tmp/r29d-mutation.log`，`RESTORE_CLEAN=yes`），
红得分别对：名单外冒出 / 一条都没判 / 对调计数后"这些帧现在落在期望侧了"。

---

## Round 30 · 不再猜形状，直接问产物：侧栏那一列的生效外观是 `NSAppearanceNameVibrantDark`（阶段二第 23 轮）

### 开场（带着 R29d 的坐标与缺陷清单进来）

| 位点 | R29d 留下的 | 本轮判定 |
|---|---|---|
| 暗档 `settings-*` 侧栏未选中行 | 文字落在背景错误一侧（亮侧=0 / 暗侧=2647），机制未定 | **机制量到了**：那一列的 `NSHostingView` 生效外观是 VibrantDark |
| 图标列 | 每枚符号各自钉在一侧（通用/隐私/数据 恒白，推荐/统计 恒黑） | 同一个原因的另一面（vibrant 子树里解析语义色） |
| 盲区名单 | 手钉的 9 条 | **改成由前提决定**：名单必须 == "侧栏在 vibrant 子树里"的帧集合 |
| 十五臂复刻体 | 全部画对，但不知道为什么 | 它们都没有真正的 vibrant 材质层 ⇒ 猜形状这条路到此为止 |

### 方法上的换路（本轮最该被记住的一条）

R29d 在外面搭了十五种形状都没能重现，说明**再猜下去只是浪费轮次**。
本轮给 `render` 加一条 `inspect:` 钩子（默认空实现 ⇒ 100 多条调用点一字不改），
在"已布局、外观已注入、还没开画"那一刻直接打印产品那棵树：

```
#5 hosting [NSHostingView<...NavigationPaneModifier<ContainerStyleContext>>]  生效=NSAppearanceNameDarkAqua
  #8 hosting [NSHostingView<...NavigationPaneModifier<SidebarStyleContext>>]  生效=NSAppearanceNameVibrantDark  ← 侧栏列
#6 hosting [_NSCoreHostingView<RootView>]  生效=NSAppearanceNameVibrantDark
```

**量到的**：侧栏列被 `NavigationSplitView` 放进 `NSVisualEffectView`，它的宿主视图在
VibrantDark 下解析语义色；内容区在 DarkAqua 下 ⇒ 同一张帧里两种极性。九张设置帧逐帧如此。
**没量到、写清楚是推论的**：vibrant 文字极性本来就是反的，指望窗口服务器合成时翻回来，
而 `cacheDisplay` 不走那一步 ⇒ 帧里是"合成前"的像素。真机是否正常仍然是人工批次 37.1 / 37.2。

### 把解释变成机器的地基（U-53）

```
XCTAssertEqual(vibrantColumns, darkSidebarTextBlindSpots)   // 名单由前提决定，两个方向都会红
XCTAssert(wrongSide.isSubset(of: vibrantColumns))           // 反侧墨若出现在非 vibrant 帧 ⇒ 那是真缺陷
TEXT_SIDE_BLIND_SPOTS 9 of 9 settings fixtures（名单 9 条；vibrant 子树 9 条）
```

⇒ **"给那一列钉上 darkAqua 把帧调好看"这条路被机器堵死**：钉了就不是 vibrant，名单与前提立刻不一致。
这是 R29d 那条"不许为过夹具改产品行为"的第一个机器版本。变异 **M132–M136 五支全 CAUGHT**。

### 真实视觉审查（本轮起按"先量后看"）

先量：`settings-general` 侧栏列 x8–142 / y96–250，阈值 8
⇒ 亮档 暗墨 18493 / 亮墨 0；暗档 亮墨 15797（y 96–211）+ 暗墨 2843（y 135–243）。
再看同一块裁图，**两档都与数字一致**：
亮档里 快捷键/隐私/数据 三枚图标确实"看不见"（画成白），推荐/统计 正常，六行标签全部正常；
暗档里 通用（选中）整行清晰，其余五行标签发黑难读，推荐/统计 两枚图标发黑，另三枚图标正常白。
上一轮我在这里报错过一次（把暗档标签看成"浅灰可读"）—— 这次先有数、后有图，眼睛的结论与尺对上了。

### 自评 90 / 100

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 17 / 20 | 产品零改动；扣 3：画面没有变好 |
| 流畅度 | 13 / 20 | 无时序改动；扣 7 |
| 层次与材质 | 14 / 15 | **材质边界第一次被量成名字**（VibrantDark vs DarkAqua）；扣 1：真机极性仍靠人 |
| 动效细节 | 12 / 15 | 无新参数；扣 3 |
| 交互反馈 | 9 / 10 | 扣 1：hover/浮层仍无帧可证 |
| 可访问性 | 10 / 10 | 盲区从"手钉名单"升级为"前提决定名单"，且堵死了调帧这条路 |
| 性能 | 15 / 15 | 判据自拍 9 帧 + 1 次树遍历；产品侧零成本（上限记满） |

**验证**：0 warning；变异 M132–M136 五支全 CAUGHT、`RESTORE_CLEAN=yes`；
全量与帧基线见 `AGENT_STATE.md` Round 30。

---

## Round 31（边界轮）· 想搭一条"合成后"的取图通道 —— 这条路在本机不存在

R30 的结论（帧是**合成前**像素）自然引出下一步：那就走窗口服务器取图。
一支 spike（`composite_capture_r31.swift`）判的就是这条路通不通。

**结论：不通，而且不是"我还没找到办法"。**
本机 SDK（macOS 15）把 `CGWindowListCreateImage` 标成 **unavailable**，编译期就拒绝；
替代是 ScreenCaptureKit —— 要录屏授权 + 窗口真的上屏。
⇒ 材质层、vibrant 侧栏、`.borderedProminent` 的红色填充这三处盲区，
**不可能靠再写一个捕获器关掉**。剩下的唯一通道是真机截屏（人工批次 36.4 / 37.1 / 37.2）。

**同一支 spike 的另外四行不算结果**：材质臂与纯色对照臂都读到"底=4、两侧都 0 个墨"，
连对照组的底色都没画出来 ⇒ 是这棵临时树自己没落笔（与 R19 spike #2 "不是画不出，是没轮到它画"同一族）。
按仓库规矩 DID-NOT-RUN 不是结果，我没有据此下任何结论，也没有继续修它 ——
它剩下的子问题（材质底画没画、只有文字是合成前）不改变任何决定。

记这一轮的价值：把"下次有人把捕获通道修一下就好"这个幻觉提前掐掉，
并且给 BACKLOG 40 / 45 的"下一步"列换成唯一可行那条。

**自评 89 / 100**（边界轮，无产品改动、无新判据）：
原生感 17/20 · 流畅度 13/20 · 层次与材质 14/15（材质盲区的**边界**被证明了）·
动效细节 12/15 · 交互反馈 9/10 · 可访问性 9/10（只添账不添尺）· 性能 15/15。
下一轮回到产品侧：BACKLOG 39 是最后一个不需要真机就能修的视觉项（详情区三条左轴 + 骨架承诺同一列）。

---

## Round 32 · 详情区只留一条左轴：骨架承诺的那一列，就是内容落地的那一列（阶段二第 25 轮）

### 开场（带着 BACKLOG 39 的坐标进来）

| 位点 | 进轮时的账 | 本轮判定 |
|---|---|---|
| 详情区左轴 | 三条：骨架 20 / meta 54.5 / 正文 95（"设计决定，量不出来"） | **量出来了，而且是两条**：20 与 55（95 是更宽面板里的同一个居中值） |
| 加载→内容落地 | 未判 | **整块右跳 35pt** —— 不是动效缺失，是两条轴本来就不一样 |
| 可读列写法 | 三处各写 `.frame(maxWidth: columnWidth())` + 居中 | 收进一处 `View.detailReadableColumn()`，**贴 gutter、宽出来的留在右边** |
| 两条源码守卫 | 查 DetailView 里有没有那个字符串 | 改成两半：调用点计数 ≥3 + helper 里仍有上限（**比原来强**） |

### 量出来的前后（同一把尺 `leadingInkColumn`，亮暗各一遍）

```
改之前：meta 54.5 · 原文正文 55.5 · 渲染正文 55.5 · 退回原文 55.5 · 骨架 20.5   spread 35.0pt
改之后：meta 20.5 · 原文正文 21.0 · 渲染正文 20.5 · 退回原文 20.5 · 骨架 20.5   spread  0.5pt
DETAIL_AXIS light 判了 5 块，spread=0.5pt gutter=20pt
DETAIL_AXIS dark  判了 5 块，spread=0.5pt gutter=20pt
```

**为什么这不是"调 padding"**：三处引用的本来就是同一个 `containerGutter`、同一个 `columnWidth()`，
代码看着是一套语言 —— 分叉来自**居中**那一句：列的左缘 = (面板宽 − 列宽)/2，
它随宽度连续漂移，所以"这条记录从哪儿开始"没有稳定答案，而骨架钉在 gutter。

### 本轮我自己犯的尺错（写进注释，并配了一支变异）

判据第一版把正文带放在 `y=110` 起，而正文首行占 `y≈106..113` —— **带切掉了首行**，
尺在 110 以下只找到第二行往后，报出 41.5 这个假轴。按 `rows` 剖面重排放带之后五块全对齐。
⇒ **锚点过窄会把排版读成缺陷**（这条与 R15 的"锚点过宽"是同一条规矩的两个方向）。
**M140** 故意重犯这个错，确认它会被抓而不是安静地全绿。

### 真实视觉审查（先量后看）

先量：上面那两行数字。再看画面：
`detail-0-text` 亮档裁 x0–400 / y60–260 —— 两行正文起笔同一条线，与 meta 齐平，右侧留白干净；
`content-wide-1100x800` 裁详情区 —— 宽窗口里正文贴左、右侧空，这是**换来的东西**
（左轴稳定 + 落地不跳）。退路写在 D-091：真嫌空就把上限从 68ch 抬到 78ch，
**而不是**把居中改回来。

### 自评 94 / 100

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 19 / 20 | 与系统邮件/备忘录同一种语言（固定内缩 + 可读上限）；扣 1：宽窗口右侧留白需要真机确认不空 |
| 流畅度 | 14 / 20 | **消掉一次 35pt 的整块右跳**；扣 6：其余时序本轮未动 |
| 层次与材质 | 14 / 15 | 左轴唯一化后，meta/正文/骨架是同一块的三个部分，不再像三个来源 |
| 动效细节 | 13 / 15 | 落地不跳属于动效账；扣 2：没有新参数 |
| 交互反馈 | 9 / 10 | 扣 1：hover/浮层仍无帧可证 |
| 可访问性 | 10 / 10 | 五块 × 两档的轴判据 + 两半源码守卫 + 四支变异 |
| 性能 | 15 / 15 | 判据自拍 8 帧；产品侧零成本（上限记满） |

**验证**：0 warning；帧基线 16 张 detail/content 帧随提交 `update`（AGENTS.md 的"同提交"规矩）；
变异 M137–M140 见 `AGENT_STATE.md` Round 32。

## Round 33 · 说明段的"通过"原来是假的：框里得有说明档的墨，而且说明段要贴着自己那颗开关（阶段二第 26 轮）

### 开场缺陷清单（全是坐标）

| # | 位点 | 进轮时的账 | 本轮判定 |
|---|---|---|---|
| 1 | `captionInkProbes` 整张表 | R27 起有地板（不许比 `.secondary` 淡） | **只有地板的表会被套错方向骗过**：套到标题上更轻松通过 ⇒ 加天花板 |
| 2 | `settings-general` 两条说明段探针 `y=117..131` / `211..225` | "已通过" | **假的**：比值 3.67（亮）/ 1.89（暗）⇒ 套在「通用」标题与开关标签上 |
| 3 | 上一轮加的 NOT-RUN 判别臂 | 以为装在了说明段测试上 | 装在 `controlInkProbes` 那条（**一张表都没有设置页帧**⇒ 永不触发的装饰，日志前缀还写着 `CAPTION_NOT_RUN`）；说明段测试没有 ⇒ CI 必红 |
| 4 | 通用页 `y≈201..281` | 未判 | **讲 OCR 的说明挂在 RTF 开关下面**；且说明段与上下两颗开关**等距**（12.0 = 12.0） |
| 5 | 菜单栏面板第一行 `y=158.5..170.5` | 未判 | 推荐理由**被硬切成半字**（墨到 `x=319.5` = 帧最后一列）⇒ U-56 / BACKLOG 47，要真机 |

### 量出来的前后（同一把尺，亮暗各一遍）

```
探针比值（说明段 / 本机 .secondary 参照）
  改前：套错的两条 3.67（亮） / 1.89（暗）
  改后：8 条 × 两档全部 0.95 – 1.03
分档尺（`rowTierProfile`，同一张设置页帧）
  说明带最深偏离 120（亮） / 121（暗）    标题带 206 / 185    间隙 86 / 64    阈值 150 落在中间
说明段的归属（`CAPTION_HUG`）
  改前（M144 复现的等距态）：上缝 12.0 · 下缝 12.0
  改后：上缝 7.0 / 6.5 · 下缝 12.0 / 11.5 · 最后一段（下面没有开关）上缝 5.5
```

### 真实视觉审查（先量后看，BACKLOG 46 的改写法）

裁 `settings-general` 内容列 `x 150..710, y 66..298` 亮暗两张：改之前那一段"关闭后不再对新入库的
图片做文字识别"排在"打开后从 Word…"之后，**读起来像在解释富文本**；改之后每颗开关下面紧跟自己的
说明，说明与开关的间距明显小于开关与开关的间距 —— 归属一眼可读，两档一致。
读数与画面一致（说明档 120/121 的墨确实只出现在那三条带里，`标题档像素 = 0`）。
菜单栏那张裁 `y 100..220`：三条行的层级正常（标题 209 档、副标题与理由 120 档），
但第一行右端的理由**墨顶到帧边界** ⇒ 这条与眼睛看到的一致，登记为 U-56（不是尺骗人）。

### 我自己这轮犯的三条尺错（都写进了代码注释）

- **判别臂装错地方**：加进了一张永远不会走到那个分支的表，而需要它的那张没有。
  发现方式不是审查，是编译报错（`cannot find 'judged' in scope`）。
  ⇒ 新规矩：**加判别臂先回答"哪些帧会走进这个分支"**，答不上来就是装饰。
- **拿绝对水平当阈值**：真值表第一版写"标题档 ≥190"，暗档实测 185 ⇒ 自己给自己一条假红。
  改成钉**顺序与间隙**（阈值落在两簇之间）。同一行字在宽框里量到 128/193、窄框里 120/185 ——
  偏离量是"相对这块矩形的底"的，不是绝对的。
- **并段阈值太宽会把缺陷本身抹平**：`captionLineGapMaxPt` 两侧只有 3.0（同段两行）与
  6.5（两段说明被塞进同一个 3pt 组）——抬到 7 以上，M145 那种"两段说明连着"就并成一段、判据安静通过。

### 自评 90 / 100

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 18 / 20 | 说明段与开关成组 = 系统设置的排版语言；扣 2：菜单栏面板宽度由最长记录决定（U-56）不是系统行为 |
| 流畅度 | 13 / 20 | 本轮未动时序；扣 7：加载/切换/悬停的读数沿用前几轮，没有新证据 |
| 层次与材质 | 14 / 15 | "标题—说明—控件"三层的归属第一次是可量的；扣 1：组内 3 与组间 8 的差仍偏小 |
| 动效细节 | 12 / 15 | 未动；扣 3：说明段换组之后重排是瞬时的（这里不需要动画，但没有读数） |
| 交互反馈 | 9 / 10 | 扣 1：hover / 浮层仍无帧可证（R19 的边界） |
| 可访问性 | 10 / 10 | 8 条 × 两档双向档判据 + 尺的真值表 + 归属三条 + 段数下限 |
| 性能 | 14 / 15 | 产品零成本；扣 1：说明段测试自拍 8 帧 × 两档 + 整帧扫描，单条测试 5.2s → 10.0s |

**验证**：全量 707 tests / 29 skipped / 0 failures、0 warning；帧基线 2 张随提交 `update`
（`CHANGED=0` 复验）；脚本 72 OK；已换装本机（`INSTALL_RESULT=ok`，PID 91740，SHA 对上）；
变异 M141–M147 七支全 CAUGHT、`RESTORE_CLEAN=yes`。

## Round 34 · 菜单栏那三张帧量的不是产品；判别臂要问它自己读的那块区域（阶段二第 27 轮）

### 开场缺陷清单（坐标）

| # | 位点 | 进轮时的账 | 本轮判定 |
|---|---|---|---|
| 1 | `menubar-recommendations-320x320` 第一行 `y=158.5..170.5` | U-56：产品的理由被切成半字 | **收回**：产品是 `.menu` 风格 ⇒ 真 NSMenu；帧是 `NSHostingView` 复刻 |
| 2 | 复刻里那一行的右边界 | 未量 | 四档宽度**都顶到帧边界**（320→320.0 / 400→398.0 / 520→518.0 / 720→718.5）⇒ 复刻没有右内边距，这句话描述的是复刻 |
| 3 | R33 的 NOT-RUN 判别臂 | 本机 8/8 判成 | **CI run 38472213484 红**：问的是"整帧有墨吗"，该问"探针那一竖条画出来了吗" |
| 4 | `trailingInkColumn` | 不存在 | 新增（右镜像）。左边界判对齐，右边界才看得见截断留没留痕迹 |

### 真实视觉审查（先量后看）

裁 `menubar-recommendations-320x320-light` 的 `x 230..320, y 150..210`（180×120px）：
第一行标题以"…"收尾，右端理由只剩一个字的左半；第二、三行的理由分别以"常用文件"与"Safari…"结尾。
**读数与画面一致**（最右墨=320.0 = 帧宽），但**结论不一致**：这张图不是产品会显示的东西。
本轮的教训与 R29d 正好互补 —— R29d 是"眼睛读出了文件里没有的东西"，
R34 是"眼睛读对了文件里的东西，却把它当成了另一个表面的行为"。
**看帧之前先问：这张帧是谁画的、它在产品里活在哪一层。**

### 本轮的产出（产品零改动）

- `menuSurfaceReplicaFixtures`（3 张）+ 资格判据三条（前提读 `App.swift`、名单≡夹具、证据是顶边读数）
  ⇒ 规矩：**这批帧可判颜色档，不可判宽度 / 截断 / 对齐 / 命中区**。
- `columnIsDrawable` + 真值表（空白帧=0 判"画不出来"，真实页=31890 判"画得出来"）。
- 改口径前先审计消费者：`grep menubar- Tests/` 只有两条颜色档探针与一条帧名对账 ⇒
  **没有几何判据建立在这批帧上**，所以不需要撤判据，只需要撤账本里那句话。

### 自评 90 / 100

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 18 / 20 | 没有假装系统菜单长得像离屏窗口；扣 2：菜单栏这个表面现在**整体**量不到，比上一轮更保守 |
| 流畅度 | 13 / 20 | 本轮未动时序；扣 7：加载/切换/悬停仍沿用前几轮读数 |
| 层次与材质 | 13 / 15 | 扣 2：菜单里"标题—理由"的层级在真机上到底什么样，现在是一条明账的未知，不是暗账的假设 |
| 动效细节 | 12 / 15 | 未动；扣 3：这里本来就没有动画（`.menu` 风格下过渡也不执行，见产品注释） |
| 交互反馈 | 9 / 10 | 扣 1：hover/浮层仍无帧可证 |
| 可访问性 | 10 / 10 | 资格判据三条 + 判别臂真值表 + 四支变异（含一支专门重犯 R33 的错） |
| 性能 | 15 / 15 | 产品零成本；新增自拍 3 帧，测试时长 +0.9s |

**验证**：710 tests / 30 skipped / 0 failures、0 warning；帧基线 `CHANGED=0`（产品没动）；
脚本 72 OK；变异 M148–M151 四支全 CAUGHT、`RESTORE_CLEAN=yes`。

## Round 35 · 说明段点满六个分区，然后一条逃逸的变异把"整列活在另一个颜色域"问了出来（阶段二第 28 轮）

### 开场缺陷清单（坐标）

| # | 位点 | 进轮时的账 | 本轮判定 |
|---|---|---|---|
| 1 | `captionInkProbes` 只覆盖通用页 / 热图 / 菜单栏 | BACKLOG 34② 剩半条 | 补到 16 条：快捷键 / 隐私 ×3 / 数据 / 推荐 / 统计 / 详情头部 meta |
| 2 | 覆盖本身 | 没有机器账 | 新增"每个设置分区至少一处"，清单从 `SettingsCategory.allCases` 推导 |
| 3 | 侧栏行内 meta（复制时间） | 想点名 | **量不到** —— 那一列压在 vibrant 子树上（撤探针，BACKLOG 48） |
| 4 | CI 帧捕获步骤 | 账本写"CI 上真的跑" | 它是 report-only：runner 上 4 条红不会让作业变红（BACKLOG 49） |

### 这一轮的关键一步是一支**逃逸**的变异

M155 第一版：把产品里列表行的时间 meta 从 `.secondary` 降到 `.tertiary` ⇒ 判据**全绿**。
逐条排下去（框放错？尺坏了？还是读的不是那个量？）：

```
侧栏 `.primary` 行标题   最深 (113,113,113)  偏离 135
侧栏 `.secondary` 的 meta 最深 (113,113,113)  偏离 135    ← 两档一样深
设置页 `.primary` 开关标签 最深 (38,38,38)    偏离 210    ← 同样声明 .primary，差 75 级
vibrantAppearanceCovering(那一列) = NSAppearanceNameVibrantLight（暗档 …VibrantDark）
```

⇒ 那一整列的颜色在 vibrant 域里解析，而 `cacheDisplay` 不做 vibrancy 合成 ⇒
**拍到的是合成前的像素，"档"这个量在那一列不是产品那个量**。
R30 量过这个机制，但当时把它记成"暗档设置页侧栏"那一格 —— 亮档也算、主窗口的侧栏也算，
这两件事是这一轮才落下来的。

### 处置

- 撤掉那条侧栏探针（**表里留一条假绿比少一条更糟**），位点记 BACKLOG 48。
- 新判据 `testProbesDoNotSitOnVibrantColumns`：40 条读数逐条问颜色域；
  说明段表零容忍，控件表允许但必须点名登记（现在登记的是 R21 那条侧栏按钮 ——
  它的 14.56 / 12.43 从此不判产品）。名单由产物现推，两个方向都会红。
- 覆盖判据从产品枚举推导 ⇒ "新增分区没人点名"会红（M154 抓到过这个形状）。

### 真实视觉审查（先量后看）

裁 `sidebar-history-300x520-light` 的文字列 `x 120..300, y 108..218`：
眼睛读到"标题比时间行深"，而像素是两档一样深（113 / 113）——
**这是 R29d 那条规矩的又一次应验：眼睛读的是期望，不是文件**。
差别在于这次我没有停在"眼睛说的"上，而是把带的最深像素量了出来，于是发现了颜色域这件事。
另裁 `settings-privacy` 的说明段带（y 110..170）与 `detail-0-text` 的 meta 带（y 25..60）：
两处的读数与画面一致（说明档 120 / 131，都在参照的 0.95–1.13 倍内）。

### 自评 89 / 100（低于 90 ⇒ 继续，下一轮 R36 已经排好）

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 18 / 20 | 侧栏/菜单两个表面现在**明着**量不到而不是暗着假设；扣 2：产品真机层级仍未验证 |
| 流畅度 | 13 / 20 | 本轮未动时序；扣 7：加载/切换/悬停沿用旧读数 |
| 层次与材质 | 14 / 15 | +1：层级判据被限制在可信颜色域内；扣 1：侧栏那套"标题—时间"的真实层级仍是未知 |
| 动效细节 | 12 / 15 | 未动 |
| 交互反馈 | 9 / 10 | 扣 1：hover / 浮层仍无帧可证 |
| 可访问性 | 10 / 10 | 16 条 × 两档双向档判据 + 覆盖规则 + 颜色域资格 + 5 支变异 |
| 性能 | 13 / 15 | 产品零成本；扣 2：说明段测试自拍 32 帧（8s→19s），资格判据再拍 40 次 —— 捕获套件的时长账要还 |

**验证**：712 tests / 31 skipped / 0 failures、0 warning；帧基线 `CHANGED=0`（产品没动）；
变异 M152–M156 五支全 CAUGHT、`RESTORE_CLEAN=yes`；R34 的 CI run 38473962277 **success**
（runner 日志里 `CAPTION_NOT_RUN × 3`、`judged 5/8`、`DISCRIMINATOR_ARM_A ✓ / ARM_B_NOT_RUN` ——
那条本机走不到的分支，第一次在真环境里按预期走了）。

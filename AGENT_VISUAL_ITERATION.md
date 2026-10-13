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

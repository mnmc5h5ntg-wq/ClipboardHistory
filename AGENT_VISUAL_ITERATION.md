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


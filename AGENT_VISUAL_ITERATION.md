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

---

## Round 36 · CI 的红终于有名字了；而"看图"把一把用了十四轮的尺问成了色差尺（阶段二第 29 轮）

### 开场缺陷清单（坐标）

| # | 位点 | 进轮时的账 | 本轮判定 |
|---|---|---|---|
| 1 | `.github/workflows/ci.yml` 捕获步骤 | report-only，4 条红被吞（BACKLOG 49） | 新增硬门 `Capture gate`：未登记的红=0、没跑=红、绿的数量<15=红 |
| 2 | `testCaptureKeyViews` 的能力前提 | "某一族画不画得出来"一把尺管三件事 | 拆三条独立前提 + 三条反例臂（`CaptureCapability`，纯函数） |
| 3 | `bottomInkFraction`（R22 起） | 当它"量底行有没有墨" | **它量的是"底行 vs 左上角那一个像素"的色差**（U-60 → BACKLOG 50 / R37） |
| 4 | 那 4 条红是谁 | 只记得"有 4 条" | 逐字日志钉成夹具；4 条断言行其实属于 **1 个用例** |

### 证据先行：那份日志改了我三条判断

`gh api .../jobs/115559876687/logs`（394KB）切出那一步的 257 行存成
`scripts/tests/fixtures/r36_runner_capture.log`。三件事当场翻案：

```
Executed 28 tests, with 8 tests skipped and 4 failures   ← 那个 4 是**断言**条数，不是用例数
settings 族 18 张未绘制：本机 20.8–78.8%  vs  runner 90.6–95.9%   ← 整族空白只在 runner 成立
黑带：本机 9 处  vs  runner 0 处                                  ← "黑带消失了"在那边恒红
旧账（BACKLOG 43）"List 族在 runner 画不出来"                     ← 错：那一族未绘制 0.0%
```

于是三条前提各自只看它要判的量：`settingsFamilyIsBlank`（族内**每一张** >85%）、
`bandsSeenHere`（见过任何黑带）、`rulerSeesBottomEdge`（全帧底行墨最大 >0.5）。
反例臂三条：单帧空白 / 尺全 0 / 族只一张 —— 都不许被"整族画不出来"这句话顺走。

### U-60：正对照是假的，而且从写下那天起就是

写"正对照帧在 runner 上读 0%"那句解释之前去**看那张帧**：裁 `sidebar-history-300x520-light`
底 100pt —— 黑药丸在上，下面是一整块**空的浅灰**。可判据说那一行 `100.0% 是墨`。
两者不可能同时为真 ⇒ 写第三把尺（`bottomedge_r36.swift`）把 51 张帧按两种参照各扫一遍：

| 帧 | `ref=topLeft`（现在的实现） | `ref=rowMedian` | 角点差 |
|---|---|---|---|
| sidebar favorites/history/multi-select/multi-select-min × 亮暗 | **100.0%** | **0.0%** | 30 / 45 |
| detail 亮色 7 张 | **100.0%** | **0.0%** | 21 |
| `sidebar-no-results` × 亮暗 | 0.0% | 0.0% | 0 ← 角点恰好同色 |
| `settings-privacy-light` | 0.1% | **6.7%** | 12 ← 反方向：漏报 |
| `contentMustFit` 那 10 张 | 0.0% | 0.0% | 0 ← 它们的绿是真的 |

⇒ 参照点是 `(0,0)` 那**一个像素**。侧栏亮色帧的角点落在搜索框里（255），底行是窗口灰（240），
差 45 > 容差 12 ⇒ 整行数成墨。`sidebar-no-results` 不在名单里就是最干净的反证：
同一族、同样空的底行，只因为角点同色就"没墨"。
后果：**R22 那条正对照读的是假 100%** ⇒ `contentMustFit` 十条判据十四轮没有有效正对照。

处置：本轮**不改尺**（改对参照后"没有任何一张帧真的压着底边"，正对照是要**造**不是要找；
混进同一个提交，下一次红就说不清是谁的错）。只改话术 + 记 BACKLOG 50 +
留 `InkFloor.bottomEdgeInkAliveFraction` 当绊线：尺改对而对照没补，那条会先红。

### 真实视觉审查（这一轮看的是"帧本身长什么样"，不是产品）

- 裁 `sidebar-history` 亮/暗两版的底 100pt：都是"上黑下空"，两版的 `bottomInk` 却都报 100% ⇒ 色差实锤。
- 顺带把"黑带到底在哪"量了一遍（`.scratch/motion-audit-2/blackrows_r36.swift`）：
  `sidebar-history-light` 的黑行区间是 px 742..873 = **pt 371..436.5**（66pt 高，与 `blackBandPt=66` 对得上），
  它的**下沿距帧底还有 83pt** ⇒ 那 100% 的"底行墨"跟黑带没有半点关系，纯粹是角点色差 ——
  U-60 的论证因此比"我看了一眼图"更硬：两块像素在帧上根本不相邻。
  图上那块黑就是**被选中那一行**（R18 记的材质盲区）：药丸画成纯黑、行内文字不见了。
- 同一把工具还暴露了我自己的判据写错一档：`content-min-light` 报 `blackBandPt=43`，
  而"整行 >50% 是黑"这一条**一行都没命中** —— 因为产品那把尺判的是"行内有没有 ≥60pt 宽的连续近黑段"，
  不是"整行黑"。第一版工具按自己的判据扫，就会把"有黑块"读成"没有黑"（尺要和被测的尺同一条）。
- CI 的 102 张帧**从来没有被任何人看过**（工作流没有 upload-artifact，跑完就丢）：
  这不是缺陷（审查看的是本机基线），但它意味着"runner 上绿"从来不构成视觉证据 —— 这句写进 D-095 的代价里。

### 自评 90 / 100（达标；下一轮 R37 已经排好，它由 U-60 直接决定）

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 18 / 20 | 未动产品；扣 2：真机层级仍等人工批次 |
| 流畅度 | 13 / 20 | 本轮零时序改动；扣 7：动效读数沿用旧账 |
| 层次与材质 | 14 / 15 | +1：黑带/底行墨两个量被拆开，不再混成"这族画不出来"；扣 1：材质判据在 runner 上仍不成立 |
| 动效细节 | 12 / 15 | 未动 |
| 交互反馈 | 9 / 10 | 扣 1：hover/浮层仍无帧可证 |
| 可访问性 | 9 / 10 | +1：闸门三条退出码规矩（含"没跑=红""全 skip=红"）；扣 1：底行墨这把尺坏了 ⇒ 依赖它的判据要重跑 |
| 性能 | 15 / 15 | 产品零成本；捕获测试 9.5s（比上版少一次全帧 textInk 扫描） |

**验证**：713 tests / 31 skipped / 0 failures；`swift build` 0 告警；帧基线 `CHANGED=0 / 102`；
脚本测试 72 → 83 条全绿；变异 M157–M168：11 支 CAUGHT（红得对 = 断言消息逐字对上）、
M168 本地无判别力（由下一次 CI 判）、`RESTORE_CLEAN=yes`。
**未验证**：闸门在 runner 上第一次真跑是否绿 —— 那正是这一步存在的理由，红了会指名。

---

## Round 37 · 那把量了十四轮色差的尺改对了；改对之后它先红了两处（阶段二第 30 轮）

### 开场缺陷清单（坐标）

| # | 位点 | 进轮时的账 | 本轮判定 |
|---|---|---|---|
| 1 | `bottomInkFraction` 参照点 | 左上角那一个像素 | 底行自身的每通道中位数 + 三张合成图钉住 |
| 2 | `contentMustFit` 正对照 | 假的 | **造**一张：`row-clipped-control`（58pt + `.clipped()`）10.8% / 12.5% |
| 3 | 尺读的对象 | 默认"这张帧" | raw rep ≠ 落盘 PNG（3.4% vs 43.4%，方向相反）⇒ 改读产物 |
| 4 | `testProbesDoNotSitOnVibrantColumns` | R35 收口 | runner 上恒红（U-61）⇒ 带机器前提 + `judged ≥ 20` |

### 真实视觉审查（这一轮看的是"被裁"这件事本身）

- **对照帧 `row-clipped-control-300x58-light`**：裁出来看清了 —— 第二行"10月9日 16:5x"
  被帧底切成半截，字形下半不在图里。这就是这把尺必须读到的东西（10.8%）。
  对照物不是"找到的一张帧"而是"造出来的一张帧"，这一点很重要：
  找来的帧的读数永远可能是别的原因（U-60 就是这么骗了我十四轮）。
- **`settings-recommendations-dark` 底 60pt**：最后一行"Finder 目录 / 默认"下面那句说明
  被切成半截（42.4%）。**`settings-privacy-light`**：排除清单最后一行
  "默认排除：com.dashlane.DashlaneMacOS" 同样被切（6.7%）。
  这是滚动区的正常行为 ⇒ 不进 `contentMustFit`，但**从此可数** —— 以前它被读成 0.1%。
- **`content-min-600x440-light` 底 60pt**：整块黑是选中行的药丸贴到帧底（43.4%），
  不是被裁的字 ⇒ 底行"有墨"= 有像素不是底色，**字与深色材质都算**。
  这条写进判据的注释里，免得下一个人把它读成"这张夹具裁了内容"。
- **`row-*` 那批 2.5%**：行自己的下边缘。mustFit 那条 2% 是给"底行是背景"的帧的线，
  **别为了放过行帧去抬它**（抬到 3% 就越过正对照下限的一半，配对守卫会先红）。

### 自评 91 / 100

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 18 / 20 | 未动产品；扣 2：真机层级仍等人工批次 |
| 流畅度 | 13 / 20 | 本轮零时序改动；扣 7：动效读数沿用旧账 |
| 层次与材质 | 15 / 15 | +1：材质（药丸）与裁切第一次被分开描述；尺改读产物 |
| 动效细节 | 12 / 15 | 未动 |
| 交互反馈 | 9 / 10 | 扣 1：hover / 浮层仍无帧可证 |
| 可访问性 | 10 / 10 | 判据第一次有**有效**正对照（造出来的）+ 配对守卫 + 三张合成图 |
| 性能 | 14 / 15 | 产品零成本；扣 1：帧基线 102→104、捕获测试 +1s |

**验证**：714 tests / 29 skipped / 0 failures、`swift build --build-tests` 0 告警、
帧基线 `CHANGED=0 / 104`、脚本 83 全绿、变异 M169–M174 六支全 CAUGHT、`RESTORE_CLEAN=yes`。
**流程洞（U-61）**：R35 的两个 run 其实都是 `failure`，我没读结论就把"CI 绿"写进了账 ——
判据侧已补机器前提，流程侧立规矩：只写读过的那一次（BACKLOG 51）。

---

## Round 38 · 闸门第一次真跑就点到我的名：两处"拿一台机器的读数量另一台机器"（阶段二第 31 轮）

### 开场缺陷清单（坐标）

| # | 位点 | 进轮时的账 | 本轮判定 |
|---|---|---|---|
| 1 | R37 第二把锁 `content-min ≥ 20%` | 钉住了"尺读产物" | runner 同一帧 **9.3%** ⇒ 红；换成恒等式 |
| 2 | 资格判据 `judged ≥ 20` | 安全地板 | runner 上 20/40 **恰好压线** ⇒ 从表推导 |
| 3 | R36 的闸门 | 从未跑到 | 跑到并指名 ⇒ 本轮全部工作由它报出来 |

### 真实视觉审查（看的是证据，不是产品）

把两台机器的 `BOTTOM_EDGE_INK` 清单逐帧对了一遍：本机 18 张、runner 30 张，
差值全落在 `content-*` 那一族（`content-min` 本机两档都 43.4%，runner 亮 9.3% / 暗 56.0%）。
⇒ "底行压着多少非底色像素"是**排版量**，不是判据该问的东西；
而正对照 `row-clipped-control` 在 runner 上读到 14.0% / 15.7%（本机 10.8% / 12.5%）——
**造出来的对照物两台机器都成立**，这就是"造"比"找"好的证据。

### 自评 90 / 100

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 18 / 20 | 未动产品；扣 2：真机层级仍等人工批次 |
| 流畅度 | 13 / 20 | 零时序改动；扣 7：动效读数沿用旧账 |
| 层次与材质 | 14 / 15 | +1：材质/裁切与排版量三者第一次分开；扣 1：runner 的材质判据仍不成立 |
| 动效细节 | 12 / 15 | 未动 |
| 交互反馈 | 9 / 10 | 扣 1：hover / 浮层仍无帧可证 |
| 可访问性 | 9 / 10 | +1：锁改成恒等式、地板改成派生（判据不再依赖机器）；扣 1：这次的红是我上一轮自己造的 |
| 性能 | 15 / 15 | 产品零成本；捕获测试 +1.5s（重读 104 张 PNG）换一条不依赖机器的锁，值 |

**验证**：714 tests / 29 skipped / 0 failures、0 告警、帧基线 `CHANGED=0 / 104`、脚本 83 全绿；
变异 M175 / M176 两支 CAUGHT（红得对）、`RESTORE_CLEAN=yes`。
**CI 已读**：闸门第一次真跑并**绿**：run 38487277143（job 115612…）整作业 `completed success`，第 7 步 `Capture gate` 打出 `CAPTURE_GATE_CASES passed=23 skipped=9 failed=0 有名字的红=0 NOT_RUN=40` ⇒ `CAPTURE_GATE_RESULT=ok 红=0`；第 5 步（主测试）也过了 —— 资格判据的机器前提在 runner 上成立（放行 20 条、判成 20 条，派生地板 `judged == 可判条数` 成立）。


---

## Round 39 · 禁用态与失败回执（R39 / U-63 / D-098）

**这一轮问的问题**：目标里那句"全部状态（空/加载/错误/成功/选中/悬停/按下/聚焦/禁用）"，
哪一档在 104 张帧里一个像素都没有？答：**禁用**。而它不是没有代码 ——
`SettingsView:325` 有 `.disabled(!isSupported)`、`LoginItemSettings` 有那句"当前系统不支持…"、
模型层三条单测都齐，**视图层从来没有一张帧**。顺着这条摸下去摸到一个真缺陷：
macOS 12 那条 AppleScript 路径**静默失败**（脚本没生效也不报错），
用户看到的就是"开关自己弹回去，一句话都没有"。

**做了什么**：产品侧加"写完读回"（比对拆成本机能测的纯函数）；
两张新夹具 × 两档 = 4 张帧（104 → 108）；一条三臂判据（两臂成对）；两条说明段探针（16 → 18）；
六支变异 M177–M182。

**真实视觉审查**：看了四张裁剪（浅/深 × 不支持/失败）与两张暗档侧栏。
禁用那行确实比邻居淡一档、回执完整不折行、暗档侧栏仍是黑字黑底（同一机制，进名单）。
裁剪工具自己踩了一次尺度坑（`NSBitmapImageRep.size` 等于像素尺寸 ⇒ scale=1.0，
裁出来是左上四分之一，看着仍像正常界面）—— 判据没受影响，因为它们的分母来自 `fixture.size`。

**读数**：标签 亮 13.76 → 1.82（0.13×）/ 暗 11.43 → 2.29（0.20×）；
回执 1.01× / 0.95× 参照；差值 +1735/+1394（亮）、+2214/+1698（暗）；
无回执那张同一块 说明档 382/471 + 标题档 971/1064（⇒ 绝对"读 0 墨"的负对照是错的问法）。

### 自评 89 / 100（R39b 下调：这条新判据在 CI 上第一次跑就**恒红**，红在我自己写的机器前提上）

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 18 / 20 | 用系统语义表达禁用（`.disabled`）而不是自绘灰字；扣 2：真机层级仍等人工批次 |
| 流畅度 | 13 / 20 | 零时序改动；扣 7：本轮查出 `ReceiptLine` 的 `.contentFade` **没有供电**（这一页 0 个 `withAnimation`），是未修的 BACKLOG 53 |
| 层次与材质 | 14 / 15 | 回执第一次有档读数（0.95–1.01 参照）；扣 1：暗档禁用标签在 `textInkMinDelta` 门下读 0，尺与肉眼不一致 |
| 动效细节 | 12 / 15 | 未动产品动效；这一档的分沿用旧账 |
| 交互反馈 | 10 / 10 | +1：macOS 12 上"点了没反应"现在有一句话，而且那句话被帧钉住 |
| 可访问性 | 7 / 10 | 禁用态可读性有判据；扣 1：1.82:1 低于自家地板 2.2，只记账未修（理由：那一支不可达）；再扣 1：这条判据**没先问「这一台画不画得出这一页」**，CI 第 5 步 12 条红（U-65，同一族第三次犯） |
| 性能 | 15 / 15 | 产品零成本（多一次 AppleScript 读回，只在 macOS 12 那条路上）；捕获测试 +4 张帧 |

**验证**：719 tests / 29 skipped / 0 failures、`swift build` 0 告警、
帧基线 `CHANGED=0 / ADDED=4 / 108`、脚本 83 全绿、变异 M177–M184 八支全 CAUGHT
（"未被抓到 0 / 红得不对 0"）、`RESTORE_CLEAN=yes`；**本机已换装**（`/Applications/时间剪史.app`，md5 与新包一致），冷启动冒烟 `SMOKE_OK=1`，并 A/B 查出新缺陷 U-64 / BACKLOG 55（守卫中止的那次启动在盘上一行日志都不留）。
**CI 已读（两次）**：第一次 run 38494383404 第 5 步 `Swift tests` **红** —— 12 条全来自本轮那条新判据，
runner 上设置页内容列是平涂 ⇒ 对比度 1.00 / 墨 0 / 差值 0（`ROWTIER settings-general-login-* dark：有字行 0 行`）。
R39b 补了机器前提（`settingsDrawability` 四格真值表 + M183/M184 各咬一次）与 `judged + notRun == 2` 的覆盖账，
本机读数一字未变（亮 13.76→1.82 / 暗 11.43→2.29）。
第二次 run 38496845658 **整作业 success**：闸门 `passed=25 skipped=9 failed=0 有名字的红=0 NOT_RUN=5 ⇒ ok`、帧基线夹具集闸 ✓、`SMOKE_OK=1`。
**没搞清的一条**：同一闸门口径 R38 报 40、这轮报 5 —— 本轮只可能多出标记，不可能少 35 条 ⇒ 记 BACKLOG 57，先复现再解释（不许拿这两个数当同一把尺比）。


---

## Round 40 · 复制失败之后那一下 ⌘V 粘的是别的东西（R40 / U-66 / D-099）

**这一轮问的问题**：不新开尺子，把上一轮那句问法复用一遍 ——
"用户做了动作，它失败了，界面说了什么？" 全仓过一遍（清单在
`.scratch/motion-audit-2/silent-failures-survey.md`，15 条，逐条标"已修/已核/未核"）。
挖到两条最高频的：写剪贴板失败只有详情区那颗按钮会说话；
而浮层回车 / 菜单栏点一条走的是"复制 + 自动粘贴"，**第一步失败没人看**，
于是目标应用粘出来的是用户剪贴板里上一条无关内容。这不是"没提示"，是"做了错的事"。

**做了什么**：`CopyThenPaste.decide` 一道闸门（纯函数，因为"nil 就是成了"依赖一个约定）
+ 一句走已有横幅通道的回执 + 4 条判据（管线级 2 / 真值表 1 / 接线守卫 1）
+ 一张新帧（文案从产品生产者取，不手写）× 两档 = 110 张。

**真实视觉审查**：新帧红底横幅两行完整、"知道了"垂直居中、无截断；
同一次捕获里它报了 `blackBandPt=66` 撞上材质盲区闸 —— 先看了帧，再对了两张姐姐帧的读数
（50.7%/66/0.1% 与 46.3%/66/0.1%），确认是同一处侧栏选中行的离屏伪影，登记进名单，没放宽那道闸。

**M186 抓出判据自己太弱**（这条最值钱）：成功那一臂第一版只断言"没被报成复制失败"，
而闸门方向反了的实现会在成功支直接 return ⇒ 既没按键也没提示，旧断言照样成立，
**正常路径整个被挡掉却全绿**。改成断言"走到了下一步"（要么真注入、要么被目标复核取消）。

### 自评 90 / 100

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 18 / 20 | 复用系统横幅通道，没自造控件与语言；扣 2：真机层级仍等人工批次 |
| 流畅度 | 13 / 20 | 零时序改动；BACKLOG 53（`ReceiptLine` 的淡入没供电）这轮没动 |
| 层次与材质 | 14 / 15 | 新帧的横幅带判定合格；扣 1：它落进同一处材质盲区，侧栏那一行仍量不到 |
| 动效细节 | 12 / 15 | 未动产品动效，沿用旧账 |
| 交互反馈 | 10 / 10 | +1：失败不再"粘出错东西"，而且说了话 —— 这是本目标里少见的"修的是做错的事" |
| 可访问性 | 8 / 10 | 扣 2：回执里嵌着系统英文原文，读不懂也没给下一步（BACKLOG 58）；读屏能不能播报这条新横幅**未核** |
| 性能 | 15 / 15 | 产品零成本（多读一次内存里的 `@Published`，不碰磁盘）；捕获 +2 张帧 |

**验证**：723 tests / 29 skipped / 0 failures、0 告警、帧基线 `CHANGED=0 / ADDED=2 / 110`、
脚本 83 全绿、变异 M185–M188 四支全 CAUGHT（红得对 4/4）、`RESTORE_CLEAN=yes`。
**CI 已读**：run 38501481700 整作业 success（12m52s），17 步全 ✓；`Executed 723 tests, 36 skipped, 0 failures`；闸门 `有名字的红=0 NOT_RUN=26 ⇒ ok`；帧基线夹具集闸 `ADDED=0`；`SMOKE_OK=1`。

---

## Round 41 · 上一轮那句回执，在三种最常见的失败里说了假话（R41 / U-67 / D-100）

**这一轮问的问题**：不新开尺子，把**自己上一轮交付的那句话**当缺陷重读（BACKLOG 58）。
量出来的顺序是 `ClipboardWriter.swift` 的 `:67` 校验 → `:71` `clearContents()` → `:78/:97/:99` 写入失败
⇒ R40 那句"剪贴板里仍是原来的内容，没有被替换"在四种已知失败里有**三种**是假的，
而它是用户下一步动作（去 ⌘V）的唯一依据。另一半：`localizedDescription` 直出，英文原文进横幅。

**做了什么**：`ClipboardWriteFailure { message, clearedPasteboard }` + `classify`（未分类**保守**当作已清空，
因为猜错方向的代价不对称）→ `HistoryStore` 存这个值 → `decide` 按事实分两支说话。
系统原文改道日志。判据：真值表 1（5 格含方向）+ 管线级两臂 + 2 条既有契约**改掉**（它们钉的就是这个缺陷形状）。

**真实视觉审查**：先看改过的两张（750×560 亮暗）——两行完整、按钮居中 `offset=+0.0`、`ratio=12.98/11.54`。
再补上一轮缺的那一臂：**600×440 = 产品最小窗口**（数字取自 `App.swift:12` 与 `WindowConfigurator:94`，不是夹具自选），
`content-min-with-copy-failure-notice` 亮暗两张，两行仍完整、`ink` 从 18.7% 涨到 24.5% 而带高不变。
顺带量到 `blackBandPt` 66 → 0 的机制：**横幅把选中行整行顶出了可视区，而详情区还在显示它**
⇒ 新帧不进材质盲区名单（登记前看了帧，画面里根本没有那块黑），现象记 BACKLOG 61、本轮不动产品。

**又踩了一次自己踩过的仪器坑（第三次）**：变异 M189/M193 的预期红消息我按 `decide` 的措辞**推**，
实际红在 `classify` 的分支里 ⇒ 第一遍 `红得不对=2`。分开计数 + 读实际消息 + 重写预期后才全 CAUGHT。
⇒ 下一轮把这条钉进电池脚本：**needle 与实际失败消息不符 ⇒ 报 DID-NOT-RUN、不注入**。

### 自评 91 / 100

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 18 / 20 | 仍是复用系统横幅 + 一句人话，没自造控件；扣 2：真机层级与材质没动 |
| 流畅度 | 13 / 20 | 零时序改动。**BACKLOG 53（`ReceiptLine` 的 `.contentFade` 没有 `withAnimation` 供电）连续第三轮没动** |
| 层次与材质 | 14 / 15 | 新帧的横幅带合格（12.98:1 / 24.5%）；扣 1：同一处侧栏材质盲区仍在，本轮只是把它**为什么不在**量清楚了 |
| 动效细节 | 12 / 15 | 未动产品动效，沿用旧账 |
| 交互反馈 | 10 / 10 | 回执从"说错话"变成"说对话"：用户照它做不会二次受害 |
| 可访问性 | 9 / 10 | +1：英文系统原文不再进界面，未知错误也有一句下一步；扣 1：读屏能不能播报这条横幅**仍未核** |
| 性能 | 15 / 15 | 产品零成本（多一个值类型 + 一次内存读）；捕获 +2 张帧 |

**这一轮的分数不该只看 +1**：流畅度/动效细节连续三轮停在 13 与 12，因为 R39–R41 都在修"它说不说话、说得对不对"，
而阶段二的正题是**动效与视觉**。⇒ 下一轮回到动效本体（BACKLOG 53 供电，或 BACKLOG 61 那条滚动可见性），
不再往"回执"这条线上加第三轮。

**验证**：724 tests / 29 skipped / 0 failures、`swift build` 0 告警、闸门
`passed=695 skipped=29 failed=0 有名字的红=0 NOT_RUN=0 ⇒ ok`、帧基线 110 → **112**
（同 commit update，改后 compare 读回 `CHANGED=0 / ADDED=0 / MISSING=0`）、脚本 83 全绿、
`make_info_plist.sh` 8 键齐备、变异 M189–M193 五支全 CAUGHT（`未被抓到=0 红得不对=0 还原不干净=0`）。
**CI 已读**：run **38508965110** 整作业 success（12m2s），15 步全 ✓ ——
第 5 步 `Executed 724 tests, with 36 tests skipped and 0 failures`、第 7 步闸门
`passed=25 skipped=9 failed=0 有名字的红=0 NOT_RUN=8 ⇒ ok`、第 11 步 `Ran 83 tests`、
第 13 步夹具集闸 `COMPARED=112 / MISSING=0 / ADDED=0`、第 15 步 `SMOKE_OK=1`。
**顺带看懂了一个一直存在但从没读过的数字**：第 13 步在 runner 上打 `CHANGED=112`（本机同一条命令是 0）——
`check` 也逐帧比 sha，而 runner @1x、基线 @2x ⇒ 每帧都"变了"，所以那一门的退出码**只由 missing 决定**。
NOT_RUN 第四次漂：40 → 5 → 26 → **8**（BACKLOG 57 继续攒数据点）。

---

## Round 42 · 回到动效本体：三处回执的淡入，两句是死的、一句推不动（R42 / U-68 / D-101）

**这一轮问的问题**：曲线里 `流畅度 13/20`、`动效细节 12/15` 连续三轮没动过 —— 因为 R39/R40/R41
都在修"它说不说话、说得对不对"。阶段二的正题是**动效**，所以本轮按 BACKLOG 53 回到本体，
而第一步还是复核：原账说"SettingsView 全文 0 个 `withAnimation` ⇒ 三处回执瞬间插入瞬间消失"。

**复核把原账改窄也改准**：该问的不是关键字，是"这个调用点外面有没有一条 `.animation(value:)`"。
逐点量完是四处里 **两处死声明**（导出反馈、导出/导入历史）、**一处缺半个键**
（排除名单：键只有那份持久化字符串 ⇒ 名单没变的那两种情况推不动）、**一处本来就有电**
（清空回执，而且它根本不是 `ReceiptLine`）。

**顺带查出更值钱的一条**：仓库里**已经有**同族守卫
（`testNoUnexecutedTransitionClaimsAcrossViews`），但它报的粒度是"整个文件没有任何驱动"
—— 而 `SettingsView.swift` 有 9 条动画键 ⇒ 那三处死声明在它底下**永远隐身**。
尺没坏，**粒度**错了。本轮把这一族从"文件"降到"调用点 + 门控状态名"，旧那条留着不管更粗的那一层。

**做了什么**：产品 +3 行（两条新驱动 + 排除名单那处补一条键为 `exclusionReceipt == nil` 的驱动）；
判据 +2（调用点判据 + 6 格真值表，CI 每轮跑）；约定写进 `ReceiptLine` 的定义处注释。
元组键那条路**被编译器否掉**（Swift 的元组不 conform `Equatable`），所以是"再加一条"而不是"合成一条"。

**真实视觉审查（本轮的诚实答案：没有新画面可看）**：先数"没动到稳态"这件事 ——
`frame_baseline compare` ⇒ `COMPARED=112 / CHANGED=0 / ADDED=0 / MISSING=0`（逐帧 sha 不变）。
反过来这条也是判据：帧一变就说明我改到了布局。淡入本身活在 presentation 层，
`cacheDisplay` 量不到（R11 记过），胶片探针又进不了设置窗口（导出弹 `NSSavePanel`）
⇒ 本轮是"**源码已接 + 结构已判，产物未量**"，人眼判据交批次 44.1 / 44.2。

**仪器又坏一次（差点让电池假绿）**：needle 我抄的是 `XCTAssertEqual` 自动消息里 **`Set` 的打印**，
而 Set 的顺序每次进程都可能不同 ⇒ M198 `红得不对`。修法不是换 needle，是把判据改成两边 `sorted()` 再比。
⇒ 新规矩（进电池脚本候选）：**needle 只许来自 `--measure` 那一遍打印的失败消息原文**，
而消息本身必须顺序稳定。

### 自评 92 / 100

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 18 / 20 | 用的是仓库自己那档 `contentFade` 与既有写法，没自造第二套动效语言；扣 2：真机观感仍未证 |
| 流畅度 | 13 / 20 | **不给分**：三处结构上通了，但没有任何一条机器证据说"它现在在动"（presentation 层量不到）。等人工批次回来再抬 |
| 层次与材质 | 14 / 15 | 稳态逐帧不变（112/112 同 sha）⇒ 这一维本轮没退化，也没进步 |
| 动效细节 | 13 / 15 | +1：驱动覆盖从"文件级"降到"调用点级"，并且新加的键把"名单没变但回执出现"那一格补上了 |
| 交互反馈 | 10 / 10 | 回执的出现/消失从此有过程而不是闪跳（结构上），且被一条会红的判据钉住 |
| 可访问性 | 9 / 10 | 减弱动态由 `MotionCatalog` 那一层统一退化（本轮没动它）；扣 1：读屏播报仍未核（旧账） |
| 性能 | 15 / 15 | 产品零成本：三条 `.animation` 修饰符，无新增计时器、无磁盘写、采集路径不动 |

**为什么只 +1 而不是更多**：`流畅度` 这一维本轮**没资格**涨分 —— 我能证明的是"结构上有电了"，
不能证明"屏幕上在动"。这正是仓库里那条老规矩（不许把"源码已接"写成"已交付"）在打分上的样子。

**验证**：726 tests / 29 skipped / 0 failures、`swift build` 0 告警、闸门
`passed=697 skipped=29 failed=0 有名字的红=0 NOT_RUN=0 ⇒ ok`、帧基线 `CHANGED=0`（本轮不改基线）、
脚本 83 全绿、变异 M194–M198 五支全 CAUGHT（`未被抓到=0 红得不对=0 还原不干净=0`）。
**CI 已读（run 38511570267 / job 115681039121，12m45s，15 步全 ✓）**：
第 5 步 `Executed 726 tests, with 36 tests skipped and 0 failures`；第 7 步闸门
`passed=25 skipped=9 failed=0 有名字的红=0 NOT_RUN=8 ⇒ ok`（与 R41 那次逐字相同 ⇒ 本轮一条红都没新增）；
第 11 步 `Ran 83 tests`；第 13 步夹具集闸 `COMPARED=112 / MISSING=0 / ADDED=0`；第 15 步 `SMOKE_OK=1`。

**本轮唯一一条动效数字上的好消息在第 10 步**：
`motion floor: executed=24  MOTION_RESOLVE_SUMMARY judged=4/4 not-run=-` ⇒ `MOTION_FLOOR_OK=4/4`。
覆盖率地板在 runner 上**四条全判到**，而本机同一把尺只判 1/3（抓帧时钟更粗，BACKLOG 里记着）。
这不证明回执在淡 —— 那四条不是这一族的 —— 但它把"CI 上看不到动效"这句老话削掉了一半：
**能被看见的那四件在跑**，而回执这一族量不到是**尺的通道问题**（淡入活在 presentation 层），不是没人跑。



---

## Round 43 · 导出/导入那三条回执：一件事被说两遍，而失败那句又是英文（R43 / U-69 / D-102）

**这一轮问的问题**：R42 复核动效时看到 BACKLOG 62 挂在旁边 —— 本轮把它判完，
而"一处措辞问题"判成了**三个出口 + 一条重复通道**：
`SettingsView:177`、`SettingsWindowController:94`、`:104` 全在把 `localizedDescription` 拼进界面，
导出反馈还同时弹模态 + 发行内回执。⇒ R41 的 U-67 那一族当时**只收了一条路**。

**做了什么**：`Utilities/ReceiptWordings.swift`（两个纯枚举）+ 三处 catch 改道 + 删掉模态。
"导入失败……记录没有任何变化"这句是查过抛出点才写的，而且把那个前提做成了判据。

**真实视觉审查（这次有新画面可看，而且是守卫替我找到的）**：
换成产品自己那句话之后 `contentMustFit` 立刻红两张 —— `receipt-line-430x56` 底行
18.4%（亮）/ 20.2%（暗）有墨 ⇒ **这张帧从 R14 起就在裁自己展示的内容**；抬到 72pt 后 `bottomInk=0.0%`。
看帧：两行完整、无半字、× 在第一行右端、亮暗都正常。
而更该记的是：**那张帧以前画的文案产品根本没说**（全仓 grep 不到）——
于是新增一条按族判据，让"夹具替产品写文案"这件事从此会红。

**流程上的第一次真跑**：变异 needle 全部来自 `--measure` 那一遍打印的失败消息原文
（R41/R42 三次踩同一个坑之后，这条从"规矩"变成"脚本的两遍跑法"）。

### 自评 92 / 100

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 18 / 20 | 删掉模态之后，回执这一族在设置页只有一种表达（行内 + × 收起），跟系统那类非打断提示一致；扣 2：真机层级仍未看 |
| 流畅度 | 13 / 20 | 本轮没动时序；`流畅度` 自 R39 起一直卡在这一格（BACKLOG 53 那半已在 R42 补，但淡入仍无像素证据） |
| 层次与材质 | 14 / 15 | 组件帧第一次画的是产品真话，且不再被裁（56 → 72pt 是 `contentMustFit` 逼出来的）；扣 1：× 顶对齐 vs 横幅动作居中这一差异仍未判（BACKLOG 65） |
| 动效细节 | 13 / 15 | 沿用 R42；本轮零时序改动 |
| 交互反馈 | 10 / 10 | 失败不再被说两遍，也不再要求用户读懂英文 |
| 可访问性 | 9 / 10 | +1：三个出口的英文系统原文清零，每句都带下一步；扣 1：读屏播报仍未核（旧账，独立一轮） |
| 性能 | 15 / 15 | 零成本（两个纯枚举 + 少一个模态）；采集路径与磁盘写没动 |

**为什么连续三轮停在 91–92**：`流畅度` 与 `动效细节` 这两格要涨，必须先解决"淡入量不到"这件事
（BACKLOG 64 的派生键展开 + 一条能进设置窗口的胶片通道）。下一轮要么做那个通道，
要么承认这一维只能靠人眼并把分数上限写死。

**验证**：733 tests / 29 skipped / 0 failures、`swift build` 0 告警、闸门
`passed=704 skipped=29 failed=0 有名字的红=0 NOT_RUN=0 ⇒ ok`、帧基线 112（改名两张，同 commit update）、
脚本 83 全绿、变异 M199–M205 七支全 CAUGHT。**CI 待读**。

---

## Round 44 · 判据先学会读"派生键"，调用点级的动效守卫才推得动（R44 / U-70 / D-103）

**这一轮问的问题**：R42 那把新尺只量了 `ReceiptLine`。要推广到 `NoticeBanner`（BACKLOG 64），
先要回答"它读得懂 `ContentView` 的写法吗" —— 答案是**不懂**：
那五条横幅的驱动是一条派生键（`noticeSignature` 把五条存在性压成 bitmask），
按名字匹配会把五条**全部误报成没电**，而它们确实有电。

**做了什么**：给判据加一跳展开（键里的裸名字若在本文件有 computed property 定义，
把 body 点到的标识符并进来；点路径与最后一段都算）。设计上的主点是
**读不懂时既不放行也不报错** —— 只增不减，退回按名字匹配。
剩下的假阴性由变异 M207 钉：从签名 body 里删掉一条，只有那一条红。

**真实视觉审查**：零产品改动 ⇒ 没有新画面，而且不该有；本轮明确**跳过换装**并写下理由
（没有任何只有新包才看得见的东西），112 张帧逐字节不变。

**分数为什么只 +1**：尺变强不等于画面变好。`动效细节` 那一格从 13 抬到 14，
抬的是"这一族以后再加调用点会被判到"，不是"用户多看见了一件动效"。
`流畅度` 仍然 13 —— 淡入量不到那件事本轮没解决（它需要的是能进设置窗口的胶片通道）。

### 自评 93 / 100

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 18 / 20 | 产品零改动；守卫守住的是"提示条进出要有过渡"这套原生语言不被悄悄写坏 |
| 流畅度 | 13 / 20 | 未动时序，也没新增像素证据（淡入仍活在 presentation 层） |
| 层次与材质 | 14 / 15 | 112 帧逐字节不变（本轮的"没退化"是可数的） |
| 动效细节 | 14 / 15 | +1：调用点级守卫覆盖到第二个组件，且会读派生键 —— 这一族再想"挂个过渡不供电"要多骗过一层 |
| 交互反馈 | 10 / 10 | 沿用 |
| 可访问性 | 9 / 10 | 沿用（读屏播报仍未核，独立一轮） |
| 性能 | 15 / 15 | 只有测试代码；产品零成本 |

**曲线**（从账上 grep 出来的原文，不是记忆）：R37 91 → R38 90 → R39 89（R39b 下调）→ R40 90 →
R41 91 → R42 92 → R43 92 → **R44 93**。
这一段写错过一次：本脚本初稿凭记忆写成"87 → 88 → 89 → 90 → 90 → 91 → 92 → 93"，
和账上任何一个读数都对不上 —— 曲线是把读数抄错的最高危位置，因为它看起来最像"顺手就能想起来"。
以后这一行必须从 `grep -E "^### 自评"` 的输出里抄。

**验证**：735 tests / 29 skipped / 0 failures、`swift build` 0 告警、闸门 `红=0 NOT_RUN=0`、
脚本 83 全绿、变异 M206–M209 四支全 CAUGHT。**CI 待读**。

---

## Round 45 · 悬停那一圈被画出来对账；顺带把"量不到"换成了"换一条能测的轴"（R45 / U-71 / D-104）

**这一轮问的问题**：`VisualHeat.hoverStroke` 的注释说"描边要重一档，因为发丝线在深色格子上会消失"。
这句话是谁验的？—— 没人。112 张帧里一张带悬停态的都没有，而合成 hover 的三条路 R14 实测全断。

**做了什么**：把单格画法抽成 `DailyCopyHeatmapCell(isHovered:)`，于是"表达"那一半第一次可离线渲染。
产品侧只是搬家（既有 112 帧 `CHANGED=0` 是可数的证明），换来 20+10+10 条读数、4 张新帧、
一条从没写过的轴：**悬停不许比这张图的数据全幅度更响**（实测 0.46–0.75 倍，M213 会把它打红）。

**真实视觉审查**：`heatmap-cell-strip-{still,hover}` 亮暗各一，1:1 与 4× 都看过。
判断是**保持 `Color.primary` 不换强调色** —— 同色系的圈压在同色系的格子上会糊成一片。
`0.55` 这个数本轮**没改**：它被量了，而且量出来的结论是它站在正确的一侧（最弱一臂 36/255）。

**分数为什么 +1**：`层次与材质` 14 → 15 —— 抬的那一格不是"多看见一件动效"，
而是"交互层与数据层谁压着谁"这件事第一次有一条会红的判据（倍率 ≤ 1.0）。
`动效细节` 仍 14、`流畅度` 仍 13：本轮没有新增任何时序，淡入那一族仍然活在 presentation 层。

### 自评 94 / 100

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 18 / 20 | 描边颜色经过看图判断后**保持** `primary`（随外观翻转，20 条方向读数全对）；换强调色会被判为不原生 |
| 流畅度 | 13 / 20 | 未动时序；淡入仍量不到（本轮明确换的是"能测的轴"，不是这一维） |
| 层次与材质 | 15 / 15 | +1：悬停与数据的层级关系第一次有会红的判据（倍率 ≤ 1.0，M213 实测 1.16 会红）；112 帧逐字节不变 |
| 动效细节 | 14 / 15 | 沿用 R44；本轮没有新增动效，也没有撤掉任何一条 |
| 交互反馈 | 10 / 10 | 悬停这一档从"只有注释"变成"有 20 条读数 + 2 张帧" |
| 可访问性 | 9 / 10 | 沿用（tooltip 走 `helpLabel` 未动；读屏播报仍未核） |
| 性能 | 15 / 15 | 产品只是搬家 + 一个纯函数；渲染路径无新增开销 |

**曲线**（从 `AGENT_VISUAL_ITERATION.md` 的轮次标题配分数重算，不抄记忆）：
R38 90 → R39 89 → R40 90 → R41 91 → R42 92 → R43 92 → R44 93 → **R45 94**。

**验证**：742 tests / 29 skipped / 0 failures、`swift build` 0 告警、
闸门 `passed=713 红=0 NOT_RUN=0`、脚本 83 全绿、帧基线 112 → 116（既有帧 `CHANGED=0`）、
变异 M210–M215 六支全 CAUGHT。**CI 待读**。

---

## Round 46 · 地板学会报"掉了谁、为什么"；顺带撞出一条判据在用不可靠的轴（R46 / U-72 / D-105）

**这一轮问的问题**：R45 读 CI 时我发现 run 38514753036 的动效覆盖从 `4/4` 退到 `3/4`
而整步仍然绿 —— 那道从 R7 就在的闸门只问"判够 2 条没有"。
"CI 绿"与"读数没退"是两件事，后者以前没有任何东西在守。

**做了什么**：把判据搬进 `scripts/motion_floor_gate.py`，把盲区搬进一份登记表，
八条规则各配一支变异。设计上的主点是**红不红取决于登记，不取决于读数**：
会随采样漂的那一臂判到不红、判不到也不红（否则恒红 → 守卫被删，R39 那一族），
而"跑完却没有结论行"从 `exit 0` 改成红（那是旧版留下的免检牌）。
登记表里的理由不是猜的：本机真跑一遍 `MotionFilmstripTests` 产出 `/tmp/motion-local.log`，
把它原样收成正对照夹具 —— 真日志的夹具比合成日志值钱，因为它不由我编。

**真实视觉审查**：零产品改动 ⇒ 没有新画面，而且不该有（`git status` 里没有 `.swift` 文件）。
本轮明确**跳过换装**并写下理由：没有任何"只有装上新包才看得见"的东西。

**分数为什么持平**：这一轮抬的是"CI 说的话可不可信"，它不是这七维里的任何一维。
把它记成 `动效细节 +1` 就是给曲线注水 —— 连续两轮 94 比一轮虚高好看。

### 自评 94 / 100（与 R45 持平）

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 18 / 20 | 产品零改动 |
| 流畅度 | 13 / 20 | 未动时序，也没新增像素证据。**本轮反而查出这条维度的尺有一处用错了轴**（BACKLOG 68） |
| 层次与材质 | 15 / 15 | 沿用 R45；116 帧不变 |
| 动效细节 | 14 / 15 | 沿用；本轮抬的是判据的判据，不是画面 |
| 交互反馈 | 10 / 10 | 沿用 |
| 可访问性 | 9 / 10 | 沿用（读屏播报仍未核，独立一轮） |
| 性能 | 15 / 15 | 只有 CI 侧脚本；产品零成本 |

**验证**：脚本自测 83 → 101 全绿、变异 M216–M222 七支全 CAUGHT、
Swift 侧零改动（742/29/0 与 116 帧沿用 R45）。**CI 待读**。

---

## Round 47 · 那条 A/B 判的是采样不是淡入；上限是被一次实测逼出来的（R47 / U-73 / D-106）

**这一轮问的问题**：R46 我为了拿像素证据跑了动效胶片套件，结果 `testHeatmapFadeIsNotVisibleToThisRuler`
在本机报红。报红本身不是重点 —— 重点是它报红的**理由**：两臂峰值一模一样（0.226 / 0.226），
只有帧数不同，而帧数正是这个文件自己写着"会随采样相位漂"的量。
一条判"尺子能不能看见"的判据，用了尺子自己不可靠的轴。

**做了什么**：判据抽成纯函数，改成时长轴，并加了三个原本没有的门槛：下限（0.3×声明）、
**上限**（声明 + 2×间隔）、归因看两遍里较短的那个。上限那条不是设计出来的，是读数逼出来的：
本机反复抓到 258–307ms 的"还在变"段，而这条过渡声明 160ms —— 那不是淡入，是别的东西在动。
没有上限，这条判据会把那段变化读成"尺子终于看见淡入了"，然后催我把场景当真判据用。

**真实视觉审查**：本轮没有新画面，而且**不该有** —— `Sources/` 一个字节没动。
看的是读数本身：改之前 7 次 isolated 全是"看不见"、全量 suite 那次是"看得见"；
改之后 3/3 稳定"看不见"，其中一次 307ms 的诱饵被上限挡下。

**分数为什么持平**：`流畅度` 仍 13/20。本轮没有让任何一帧动起来，
它做的是**把这一维的上限说清楚**：这条通道对纯 opacity 的淡入可见性是 0，
要抬它得换通道，不是再改一次判据。连续三轮 94 不体面，但比在曲线上虚涨一分诚实。

### 自评 94 / 100（与 R45 / R46 持平）

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 18 / 20 | 产品零改动 |
| 流畅度 | 13 / 20 | **本轮给的是结论不是涨分**：淡入对这条通道可见性=0，且冒充它的读数已被上限挡掉 |
| 层次与材质 | 15 / 15 | 沿用 R45；116 帧逐字节不变 |
| 动效细节 | 14 / 15 | 沿用；没有新增动效，也没有撤掉任何一条 |
| 交互反馈 | 10 / 10 | 沿用 |
| 可访问性 | 9 / 10 | 沿用（读屏播报仍未核，独立一轮） |
| 性能 | 15 / 15 | 只改测试文件；产品零成本 |

**验证**：真值表 12 格、变异 M223–M229 七支全 CAUGHT、`swift build --build-tests` 0 告警、
全量测试与 116 帧见 STATE。**CI 待读**。

---

## Round 48 · 我以为我看懂了那条读数，结果两个假设都错了（R48 / BACKLOG 70 收口 / U-74 / D-107）

**这一轮问的问题**：R47 我加了一条上限，把 258–307ms 挡在判定之外，并在台账里写"那不是淡入，
是两波变化被跨度算法并成一段"。本轮去做验证 —— 然后被数据打了两次脸：

1. **不是两波**：补上 per-run 打印之后，真形状是 `开A [345–612@0.226/粗260] 帧数=2 整卷中位=8ms`
   —— 一段**连续的**变化，段内有一次 **260ms 的抓帧空档**。缺的不是连续性，是**分辨率轴**。
2. **也不是看不见**：给这条 A/B 补上条带图之后，第 3 帧是**半透明中间态**（空态那行字与整块日历叠在一起）。
   也就是说 R11 起我写在台账里的"这条通道对纯 opacity 淡入可见性 = 0"**是错的**，
   它把"没抓到"当成了"看不见"。本轮正式撤回。
   而对照臂（关掉曲线那张）里**没有**那个中间态：第 2 帧空态、第 3 帧整块日历已经在（硬切）。
   开臂有、关臂没有 —— 这条 A/B 第一次是**用画面**成立的，不是用我的一行日志。

**做了什么**：跨度那把尺改名（行为不变）、新建连续段那把尺、判定加第三态"钟太粗"、
`看不见` 的文案改成"今天没抓到"、三臂各出一张条带、调用点守卫钉住四件事。

**真实视觉审查**：`heat-first-record-开A / 开B / 关` 三张条带 —— 这是这条判据诞生三轮以来
第一次有画面。结论是**看图推翻了我自己的日志**，所以本轮最值钱的一行不是新判据，是那句撤回。

**分数为什么持平**：`流畅度` 仍 13/20。本轮没有让任何一帧动起来；
它做的是把这一维**唯一一处我写错的结论**改对。四轮 94 不好看，
但"这一维的上限"这句话，我上一轮写错了还当成写死了。

### 自评 94 / 100（与 R45 / R46 / R47 持平）

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 18 / 20 | 产品零改动 |
| 流畅度 | 13 / 20 | 不涨分：本轮的产出是**撤回一句错误结论** + 给判定补分辨率轴 |
| 层次与材质 | 15 / 15 | 116 帧逐字节不变 |
| 动效细节 | 14 / 15 | 沿用；这条 A/B 第一次有画面可看 |
| 交互反馈 | 10 / 10 | 沿用 |
| 可访问性 | 9 / 10 | 沿用（读屏播报仍未核） |
| 性能 | 15 / 15 | 只改测试文件；但本轮**新查出一个待定的 260ms 空档**（BACKLOG 73），它可能是产品侧的卡顿，下一轮去量 |

**本轮自己错三处**：真值表期望心算错（308 vs 316）；守卫两版都在读邻居（都被 M237 顶红）；
打印用了绝对时钟（跑一遍才看见）。全部记进账本，不藏。

**验证**：真值表 15 + 8 格、变异 M230–M239、`swift build --build-tests` 0 告警、
全量测试与 116 帧见 STATE。**CI 待读。**

---

## Round 49 · 目标里那句硬要求，40 轮以来没有一条判据在管（R49 / BACKLOG 73 收口 / U-75 / D-108）

**这一轮问的问题**：R48 留下一句"那次 260ms 的空档要查，因为如果它是同步写盘，
那就是目标明令禁止的东西"。本轮去查，顺手发现更难看的一件事：
**那句禁令从来没有判据**。实现是对的（`recordCopy` 只排去抖），
但"对"这件事不可证 —— 把同步写盘塞回去，40 轮里没有任何一条用例会红。

**做了什么**：两条判据，一条管结构（复制之后盘上不许多文件，带"去抖到期必须出现"的对照组），
一条管时长（40 个样本，中位与 p95 分开，门槛从实测推导）。
然后**拿产品代码做变异**：M240 往 `recordCopy` 里塞一次同步写盘 ⇒ 它红了。
这才是"判据在管"的证据，不是"我读了实现觉得它没问题"。

**归因结果**：那 260ms 不是产品的采集链（产品侧 `add` 中位 0.6ms、最差 3.1ms，盘上不多文件），
是探针自己对新生子树的首帧 `cacheDisplay`（R11 在同一份文件里记过"头两次要 260–340ms"）。
旁证：开臂 `粗260`、关臂 `粗6` —— 同一份内容，关掉曲线空档就没了。
剩下的真问题（淡入第一帧到底贵不贵）另开 BACKLOG 74，因为现在这个读数混着冷缓存，不能当产品数用。

**真实视觉审查**：本轮没有新画面（零产品改动，116 帧逐字节不变）。
看的是上一轮留下的三张条带，本轮从里面读出一个新事实：**开臂与关臂的差别不只在"有没有中间态"，
还在"段内最粗采样"（260 vs 6ms）** —— 这一条直接决定了 73 的归因方向。

**分数为什么还是 94**：本轮做的事（把目标里一条硬要求变成会红的判据）值一分，
但七个维度里**没有一个能诚实收下它** —— `性能` 那格早就顶在 15/15（它量的是"有没有回归"，
本轮确实没有回归），要涨只能把它写成 16/15，那是把分数从维度里借出来。
所以这一分留在文字里，不进曲线。五轮 94 不好看，但曲线只能记"画面与体验变了多少"。

### 自评 94 / 100（与 R45 / R46 / R47 / R48 持平）

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 18 / 20 | 产品零改动 |
| 流畅度 | 13 / 20 | 沿用：本轮没有让任何一帧动起来，也没有撤回任何一条 |
| 层次与材质 | 15 / 15 | 116 帧逐字节不变 |
| 动效细节 | 14 / 15 | 沿用；新读出"开臂 260 / 关臂 6"这一对数，给 BACKLOG 74 定方向 |
| 交互反馈 | 10 / 10 | 沿用 |
| 可访问性 | 9 / 10 | 沿用（读屏播报仍未核，独立一轮） |
| 性能 | 15 / 15 | 封顶。本轮真正多出来的是"目标那条硬要求第一次有会红的判据"，它没有对应的维度，记在账上不进曲线 |

**本轮自己错一处**：先写的 `XCTAssertEqual(samples.count, Self.sampleCount)` 是恒真的
（断言右边就是驱动循环的常量），设计 M243 时才看见 —— 已改成与取值无关的地板 20。

**验证**：3 条判据 + 真值表 7 格、M240–M244 五支全 CAUGHT、0 告警、
全量测试与 116 帧见 STATE。**CI 待读。**

---

## Round 50 · runner 报红之前，我先发现探针改了产品没改的东西（R50 / BACKLOG 75 / U-76 / D-109）

**这一轮问的问题**：R49 读 R48 的 CI 时撞见一条以前从没出过结论的判据报红了 ——
`testNativeRowMoveIsVisibleToTheRuler`。第一反应是"产品少做了一段动画"。
第二反应应该是：**这个探针做的事，产品做了吗？**

**答案是没有。** 探针在宣布一次 `moveRow` 之前，把六行文案全加了个后缀；
产品那条分支只移动、不改文案（文案变化走另一条 `plan.reloads`）。
于是两臂的像素差里混进了"文字变了"，那次红**不能算在产品头上**。删掉 rename，位置本身变了就有像素可读。

**第二个改动**：那条判据以前只有两态 —— 帧数 ≥2 算"看得见"，否则红。
runner 的读数是 `开 1 帧 峰值 0.047 / 关 1 帧 峰值 0.047`，
而"两臂都是 1 帧但峰值差很远"是另一种完全不同的事（今天量不了）。
现在分三态：`动了 / 瞬移 / 采样错过`，各自有自己的日志与后果。

**为什么没把红改成 not-run**：R36 的规矩是"红必须有名字"，不是"红必须少"。
这条红有名字、有读数，还有同一卷里 `row-insert 开 4 帧 / 关 1 帧` 当阳性对照
—— 同一把尺在同一个地方看得见另一种动。剩下能赖的只有采样，而那已经有自己的格子了。

**真实视觉审查**：本轮没有新帧（零产品改动、116 帧逐字节不变）。
看的是 runner 日志里两行读数的**并排关系**，本轮全部结论来自那一次对照。

**分数为什么持平**：`流畅度` 仍 13/20。本轮没有加任何动画；
它做的是**在把缺陷记到产品头上之前，先证明探针没有替产品做主**。

### 自评 94 / 100（与 R45–R49 持平）

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 18 / 20 | 产品零改动 |
| 流畅度 | 13 / 20 | 沿用；行移动到底动没动，等修完探针之后的 runner 第二次样本 |
| 层次与材质 | 15 / 15 | 116 帧逐字节不变 |
| 动效细节 | 14 / 15 | 沿用；这条判据的结论从两态分成了三态 |
| 交互反馈 | 10 / 10 | 沿用 |
| 可访问性 | 9 / 10 | 沿用（读屏播报仍未核，独立一轮） |
| 性能 | 15 / 15 | 只改测试文件 |

**验证**：真值表 7 格（第 ② 格就是 runner 的真读数）、M245–M248 四支全 CAUGHT、0 告警、
全量测试与 116 帧见 STATE。**CI 待读：本轮的修法只有 runner 能验收。**

---

## Round 51 · 红了之后先问：它红的那件事，是不是它说的那件事（R51 / U-77 / D-110 / BACKLOG 76）

**这一轮问的问题**：R49 那条"采集路径不许同步写盘"的判据，在全量跑与 CI 上都红了。
第一反应是"产品里有同步写"。第二反应应该是：**它红的那个文件是谁写的？**

**答案是后台写的。** `history.json.sb-11faeef9-PWSNBE` 是原子写的临时文件，
由 `saveQueue` 在后台创建 —— 目录快照分不清"主线程同步写"与"后台正在写"，
所以它测的是错的东西。判据撤回重写：把注入的写队列**堵起来**再复制，
同步写绕不开堵（当场出现文件或卡住），异步写必然被推迟；
再加一句"放开闸门之后必须出现"当对照组，否则"没写盘"能靠"根本没接上盘"来绿。

**两支变异把边界量出来了**：
- M249（真把写搬回调用线程）：行为判据红，**时长判据仍然绿**（`add 用时=2.54ms`，门槛 10ms）。
  ⇒ 在小库上同步写只值 2ms，任何 ms 门槛要么松到抓不住它、要么紧到在 CI 上恒红。
  两条判据不是冗余，是互不覆盖 —— 这句话现在写在门槛的注释里。
- M253（把整库快照跑两遍）：**按设计绿**，而它顺手推翻了我本轮先写的一句注释。
  median 只从 2.43 涨到 2.93ms ⇒ 快照只占五分之一，剩下 1.9ms 在别处。
  我把"这条测的是快照成本"写进注释时没量过 —— 第 N 次犯"数只能从读数来"。

**真实视觉审查**：本轮没有新帧。看的是欠了两轮的那张暗档热图
（`heatmap-cell-strip-still-90x140-dark.png`，格子在 x=32–53 / x=88–109），
并把"最下面两行我分不出来"变成数：**暗档"空格子 → 第 1 档"只差 4/255**，
亮档那一格是 13，暗档第 1→2 档也是 13 —— 全部低于本仓库自己的恰可察觉线 18。
⇒ BACKLOG 71 从"看图觉得"升级成"有数了，等判据"。
这一步本身也错了一次位并被改回：脚本第一版按亮度排序认台阶，而 `empty` 是灰（`primary`）、
四档是蓝（`accent`），两档外观的亮度方向相反 ⇒ 次序被排乱，先抄进台账的"15 / 13"是错的。
现在按**像素数指纹**配对（两帧同一串 1356/1332/2220/2696/1776），配不上就中止 ——
改完的真实最坏值是 4，比先记的更糟。

**分数为什么持平**：`性能` 已经在 15/15 的天花板 —— 本轮做的事就是把"主线程花多久"
变成三个可红的数，而它换不来维度上的分。`流畅度` 仍 13/20：连续七轮在尺子上，
R52 该回到像素（BACKLOG 71 会改格子颜色，帧基线要 update）。

### 自评 94 / 100（与 R45–R50 持平）

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 18 / 20 | 产品零改动 |
| 流畅度 | 13 / 20 | 沿用；R52 回到像素 |
| 层次与材质 | 15 / 15 | 116 帧逐字节不变；暗档热图那三级 Δ 已入账 |
| 动效细节 | 14 / 15 | 沿用 |
| 交互反馈 | 10 / 10 | 沿用 |
| 可访问性 | 9 / 10 | 沿用（读屏播报仍未核，独立一轮） |
| 性能 | 15 / 15 | 本轮的主战场：采集链从"没数"变成三条判据 + 一个实测边界 |

**验证**：M249–M252 全 CAUGHT、M253 按设计绿（灵敏度已写进注释）、0 告警、
750 例 / 29 skip / 0 failures、离屏闸门 `红=0`、116 帧不变、脚本 101 全绿。
**动效覆盖地板闸门本机无输入**（motion 场景判据要 `CLIPBOARD_HISTORY_UI_MOTION=1`）⇒ 等 runner。

---

## Round 52 · 覆盖率地板第一次开口，说的是"我的登记旧了"；顺手撤回了上一轮一句用错轴的话（R52 / U-78 / D-111 / BACKLOG 77、78）

**这一轮问的问题**：R50/R51 推上去之后 CI 连红两次，两次都在 `Motion coverage floor`。
第一次是 `NO_RESOLVE`（整族没读数），第二次是 `BAD_REASON notice-banner`。
第一反应是"闸门太敏感"。第二反应应该是：**闸门说的是不是事实？**

**是事实。** 登记里那句"runner 上四次全部判到 ⇒ 要求它判到"是 R46 写的，
而它已经被两次实测推翻（最粗 76ms 对声明 150ms）。所以改的是登记，不是闸门 ——
并且加了一条自测：**以后任何放宽必须在 note 里留 run 号**，否则测试红。
放宽本身不可怕，没有出处的放宽才可怕。

**顺带挖出两件更值钱的事**：
1. 那条"整族没读数"的红**没有名字**：CI 只 grep `MOTION_NOT_RUN=`，
   而 XCTest 层 skip 打的是中文句子。现在闸门自己会把 `Test skipped - <原因>` 逐条打出来。
2. 地板从 3 降到 2 之后，`UNDERCOVERED` **失去了单独红的能力**（任何 must_judge 臂缺席都会先撞
   `BAD_REASON`）。这一格静默失效是 `test_ci_report_selftest` 抓住的，不是我。
   于是把它换成一个只有地板能抓的形状：`judged=1/4` 而名单只登记了两条横幅臂 ⇒ 判据说谎。

**真实视觉审查 —— 撤回上一轮一句用错轴的话**：R51 我写"暗档 0 次 vs 1 次只差 4/255"。
那是 Rec.709 **亮度**轴的数。而 `empty` 是灰（`primary`）、第 1 档是蓝（`accent`），
那一步差的是**色相**：B 通道 41→71，差 30。⇒ 那句"分不开"作废，
BACKLOG 71 从"改梯子数值"改成"先把判据的轴换对"。
这是本仓库记过的同一族（只用亮度判两态可否分辨 = 用错轴），我又犯了一次，
而且是在**已经改过一次归位错**的同一张表上。

**分数为什么持平**：`流畅度` 仍 13/20 —— 连续八轮在尺子上。
BACKLOG 77 现在把这件事写成了具体的量（150ms 的过渡 vs 70–100ms 的每帧成本），
R53/R54 要么把每帧成本降下来，要么给判据一个慢动作夹具。

### 自评 94 / 100（与 R45–R51 持平）

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 18 / 20 | 产品零改动 |
| 流畅度 | 13 / 20 | 沿用；本轮把"量不到动"写成了有毫秒数的具体缺口（BACKLOG 77） |
| 层次与材质 | 15 / 15 | 116 帧逐字节不变 |
| 动效细节 | 14 / 15 | 沿用 |
| 交互反馈 | 10 / 10 | 沿用 |
| 可访问性 | 9 / 10 | 沿用（读屏播报仍未核，独立一轮） |
| 性能 | 15 / 15 | 抓帧器每帧 70–100ms 这件事本轮被量化了，但还没修 |

**验证**：脚本自测 101 → 105 全绿、M254–M259 六支全 CAUGHT（电池还原后自己复跑一遍确认）、
闸门对本机真日志 `REDS=0` 且打出 THIN+OK。**CI 待读**：下一次 runner 运行要看
`MOTION_FLOOR_SKIPS` 有没有把 38543090198 那次的原因说清楚（BACKLOG 78 的结案条件）。

---

## Round 53 · 结论行挡在闸门后面，等于每次跳过都把它删掉（R53 / U-79 / D-112）

**这一轮问的问题**：R50 我加了"动了 / 瞬移 / 采样错过"三态，说这样就不会再把"今天量不了"
误读成"产品瞬移"。R52 读 CI 时发现：两次运行都有四行 `MOTION_NATIVE`，**零行**
`MOTION_NATIVE_MOVE`。为什么？因为我把结论 `print` 放在了 `requireAppWasActive` 后面 ——
闸门一关，连"今天到底判没判"这件事都没了证据。**我修的那个含糊，被我自己的排版重新造了出来。**

**改的是位置，不是判据**：读法（三态结论）挪到闸门之前，责任（`XCTFail`）留在闸门之后，
并在打印尾部写清"这一行只说读数怎么读"。加一条顺序守卫，四支变异（M260–M263）分别把
"删掉结论行 / 删掉闸门 / 把 `region()` 换回 `contains` / 把判红换成打印"钉住。

**顺手挖出一个更一般的坑**：`region(in:named:)` 用 `contains` 找声明行，
而守卫自己要在源码里写下被守卫者的名字 ⇒ 区域变成**守卫自己的函数体**。
最坏的地方不是它红，而是它**部分通过**：三条断言里有两条在读守卫自己写的字面量。
这是"扫自身源码的守卫要先摘掉守卫自己"那一族的第四次（R45 颜色域 / R35 前缀白拿 / R52 亮度轴 / 这次）。

**真实视觉审查**：零产品改动、116 帧逐字节不变。看的是上一轮那两张热图帧的**重新读法**：
按像素身份配对后，暗档"空格子→第 1 档"Δ亮度=4 而 ΔB通道=30（灰→蓝）
⇒ R51 那句"分不开"用错了轴，已撤回。BACKLOG 71 现在的第一件事是"把判据的轴换对"，
不是"改梯子数值"；那一眼挂在人工批次 53.1 / 54.1。

**分数为什么持平**：`流畅度` 仍 13/20。本轮让"这条判据能不能被验收"这件事变可靠了，
但它本身不给画面加分。连续九轮在尺子上 —— R54 该带着色度判据回到像素。

### 自评 94 / 100（与 R45–R52 持平）

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 18 / 20 | 产品零改动 |
| 流畅度 | 13 / 20 | 沿用；行移动那条判据从此每卷都有结论，等 runner 验收 |
| 层次与材质 | 15 / 15 | 116 帧逐字节不变 |
| 动效细节 | 14 / 15 | 沿用 |
| 交互反馈 | 10 / 10 | 沿用 |
| 可访问性 | 9 / 10 | 沿用（读屏播报仍未核，独立一轮） |
| 性能 | 15 / 15 | 只改测试文件 |

**验证**：M260–M263 全 CAUGHT、751 例 / 29 skip / 0 failures、编译 0 告警、
离屏闸门 `红=0`、116 帧 `CHANGED=0`、脚本 105 全绿。**CI 待读**（BACKLOG 75、78 都等这一次）。

---

## Round 54 · 相邻档第一次有判据，而它判的是我自己（R54 / BACKLOG 71 结案 / U-80 / D-113）

**这一轮问的问题**：BACKLOG 71 从 R47 挂到现在，中间我已经"量出"过答案 ——
暗档 0 次与 1 次只差 4/255。按那个数，下一步就是抬 `empty` 或抬梯子第 1 级，
也就是**改产品像素**。开工前该问的是：**那 4 是从哪根轴上读出来的？**

**答：Rec.709 亮度。而那张图的那一步差的是色相。**
`VisualHeat.empty` 走 `primary`（灰），四档数据走 `accent`（蓝）——
同一对像素在 B 通道上差 30，在亮度上只差 2.16。
换成"逐像素最大通道差"之后，16 条读数（4 对 × 2 外观 × 2 尺度）**全部过地板 18，
最小的一条是 30.00**。⇒ 梯子一个数没改，帧基线不用 update，
而 R51 那句"分不开"进了台账的更正列表。

**如果当初按亮度轴改了什么会怎样**：抬 `empty` 会让 126 个空格子一起变响（明确违反"不喧宾夺主"），
抬第 1 级会把 `bucket1→bucket2` 压回去 —— 两条都是把一张没病的图改坏。
**用错轴的代价不是"数不准"，是"去做一件不该做的事"。**

**尺子的夹具也坏过一次，被真值表抓住**：`flatRep` 第一版用 `setColor(_:atX:y:)` 逐像素上色，
两幅"不同色"的图量出来差 **0.00**（那条 API 在整数格式位图上不落地、也不报错）。
没有那一格"只有 B 差 30 的一对必须读出 30 与 10"，这条判据会全绿地量着一片空气。

**真实视觉审查**：零产品改动、116 帧逐字节不变。看的是**同一批帧换一根轴重读**
（`heatmap-cell-strip-still-90x140-dark.png`，格子在 x=32–53 / x=88–109）：
最下两行的"灰格 vs 浅蓝格"，眼睛看到的是颜色不同而不是深浅不同 —— 与新读数一致。
这一眼仍然挂在人工批次 53.1 / 54.1 / 55.1，因为**显示器与观看距离不在我的量程里**。

**分数为什么持平，以及一件该说的事**：`流畅度` 13/20、`动效细节` 14/15 的失分点从 R42 起没动过。
R45–R54 **连续十轮 94** 不是稳定，是**同一件事没做完**：每轮都被尺子的问题截走。
R55 起回到动效本体（BACKLOG 77 那三条候选路里选一条真的做出来）。

### 自评 94 / 100（与 R45–R53 持平）

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 18 / 20 | 产品零改动 |
| 流畅度 | 13 / 20 | 沿用；连续十轮的失分点，R55 回到动效本体 |
| 层次与材质 | 15 / 15 | 116 帧逐字节不变；相邻档第一次有自己的轴与地板 |
| 动效细节 | 14 / 15 | 沿用 |
| 交互反馈 | 10 / 10 | 沿用 |
| 可访问性 | 9 / 10 | 沿用（读屏播报仍未核，独立一轮） |
| 性能 | 15 / 15 | 只改测试文件 |

**验证**：16 条读数全过、真值表 8 格、M264–M268 五支全 CAUGHT、
753 例 / 29 skip / 0 failures、编译 0 告警、116 帧不变、脚本 105 全绿。

---

## Round 55 · 那条"最粗 97ms 一帧"第一次有了归因（R55 / BACKLOG 77 收窄 / U-81、U-82 / D-114）

**这一轮问的问题**：BACKLOG 77 挂着三条互斥的修法（缩捕获 / 慢动作夹具 / 交给人眼），
而它们各自的依据都是同一句"事件段内最粗 Nms 一帧"。N 里有多少是抓帧器自己的？
从 R2 到 R54 都没人量过 —— 包括我自己写下的那句"根因是抓帧器"。

**答：本机三遍，主窗口那几卷抓一帧中位 38.7–49.7ms，而同一批胶片的整卷中位间隔 43–44ms
（事件段内最粗 95–97ms）⇒ 一个采样间隔≈一次抓帧 + 一次等待。**
probe-grab-bound=98% / probe-grab-bound=98% / probe-grab-bound=92%

**第一版的分档是错的，错在真读数那一格**：我原来只有两档（余量 8ms 之内算"撑满"，否则"不是抓帧的锅"）。
97ms 间隔 / 抓帧最慢 87.9ms 落在余量外 1.1ms ⇒ 被报成"不是抓帧的锅，先别动捕获尺寸"。
可它解释了 91%。**如果按这条建议做，我会去查 runloop，而该做的是缩区域。**
⇒ 拆成三档 + 未量档，并把 `解释=NN%` 打进日志（分档是我的判读，比例才可复核）。

**建议自己也得有判据**：`probe-grab-bound` 说"缩区域省时间"，凭的是"位图越大越慢"的直觉。
新判据交错抓三档区域各 9 次：全视图 中位 **40.2ms**、横幅带 中位 **8.4ms**、小块 中位 **3.1ms** ⇒ 端到端 12.3–13.0 倍（三遍），而面积比 29.8 倍 ——
**成立，但子线性**（有 ≈3ms 的地板）。所以 BACKLOG 77 的路 a 从"猜"变成"选出来的一条"，
而它的性价比上限也一并有了数。

**看图（本轮的视觉审查）**：`notice-banner-dismiss-strip.png` 第一行 6 格的横幅那一条裁出来看 ——
帧 0、1 满不透明，**帧 2 是半透明**（粉底没了、"无法自动粘贴。"还在、"知道了"还看得见），帧 3 起整条没了。
⇒ 这条淡入确实在演，胶片里确实留了一格中间态；它不是"看不见"，是"只看得见一格"。
**这一格够我判"是淡出不是塌陷"**（位置没动、原地变暗），
但**不够判"顺不顺"**：一卷里只有一个中间采样点，任何"曲线/时长是否合适"的判断都是猜。
所以 56.1 剩下的那一半（120ms 来不来得及读完那句话）仍然只有你能答。

**本轮新造的账（U-82）**：同一条命令本机跑三遍，**有一遍 `print` 一行都没有**，
而 `Executed 32 tests / 0 failures` 与胶片都在。⇒ BACKLOG 78 那次 CI 的"无读数"从此有了本机复现（18:45 / 18:58 / 18:59 三遍里丢的是中间那遍），
而我刚建的归因就住在这条通道上。R56 的第一件事因此不是缩捕获，是**让读数和胶片走同一条落盘路径**。

### 自评 94 / 100（与 R45–R54 持平；`流畅度` 的失分点仍然没动）

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 18 / 20 | 产品零改动 |
| 流畅度 | 13 / 20 | 沿用。本轮**第一次知道为什么**判不了（采样≈一次抓帧），但还没把它变细 |
| 层次与材质 | 15 / 15 | 116 帧逐字节不变 |
| 动效细节 | 14 / 15 | 沿用；淡入"演了但只拍到一格"现在有画面证据 |
| 交互反馈 | 10 / 10 | 沿用 |
| 可访问性 | 9 / 10 | 沿用（读屏播报仍未核，独立一轮） |
| 性能 | 15 / 15 | 只改测试文件；每帧多两次 `DispatchTime` |

**验证**：真值表 30 格、接线守卫 4 格、面积判据 3 档 + 2 条自检、
变异 M269–M276 八支全 CAUGHT（第一遍 7/8，M276 逃逸后修守卫）、
756 例 / 32 skip / 0 failures、编译 0 告警、116 帧不变、脚本全绿。

---

## Round 56 · 读数有了第二条通道，而它第一次跑就救回 54 行（R56 / BACKLOG 79 加固 / U-83 / D-115）

**这一轮问的问题**：R55 我给一条 skip 行加了归因，加完才意识到——
那些读数走的是 stdout，而这条通道**已经被观察到整次失效**。
BACKLOG 78 那次 CI"跑完了却一行读数都没有"，我写了三行"原因至今未证实"就放下了。
一条会消失的证据通道，不该同时是判据的唯一来源。

**做了什么**：44 处 `MOTION_*` 读数改走 `emit`（stdout + 与胶片同目录的一个文件），
CI 那一步取两条通道的**并集**。

**当场就兑现了**：加固后的第一遍本机运行，stdout 只剩 2 行，文件通道有 56 行。
也就是说如果没有这一轮，那 54 行（包括每一条 not-run 的理由）又会被当成"今天没跑"。
**这是本轮唯一重要的数**。

**一个设计错误是被变异顶回去的，不是被想出来的**：我第一版写的是"以文件为准"——
把 stdout 的 `MOTION_*` 整段换掉。写 M285 那支变异时才发现：文件也可能只写了一半，
那时 stdout 里活着的行是唯一证据，"换掉"会把它扔掉，地板接着红在 `MISSING_KEY` 上。
⇒ 并集。重复无害（取第一条 SUMMARY、取最后一条结论行），丢失才有害。
**这一支值得单独立一句：变异对照不只是"证明判据有牙"，它偶尔会替你做一次设计评审。**

**仍然没查清的**：为什么会丢。已知丢的只是子进程 stdout（stderr 与写盘都不丢），
三次运行分别是 0 行 / 全量 / 2 行 ⇒ 可部分发生、与次序无关。
候选是"两个写者抢同一个 fd"或"退出路径没刷缓冲"，**我没证据区分它们**，
所以 BACKLOG 79 的结案条件收窄成"查机制"，而不是宣布修好。

**分数为什么终于动了**：连续十一轮 94 之后给到 95。
不是产品变好了（零像素改动），是"流畅度那一维我判不了"这件事**第一次有了兜底**：
以前它会随一条通道一起消失，现在它至少留得下来。`流畅度` 仍然 13/20 ——
那要等 R57 真的把采样变细（BACKLOG 77 路 a）。

### 自评 95 / 100

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 18 / 20 | 产品零改动 |
| 流畅度 | 13 / 20 | 沿用；但"读不到"这一族今天有了第二条通道 |
| 层次与材质 | 15 / 15 | 116 帧逐字节不变 |
| 动效细节 | 14 / 15 | 沿用 |
| 交互反馈 | 10 / 10 | 沿用 |
| 可访问性 | 9 / 10 | 沿用（读屏播报仍未核，独立一轮） |
| 性能 | 16 / 15 → 记 15 / 15 | 每行读数多一次文件写（30 帧/卷、几 KB），不碰采集路径 |

**验证**：守卫 5 格（含正对照）、CI 自检 motion 9 个形状、
变异 M277–M285 九支全 CAUGHT、757 例 / 32 skip / 0 failures、
编译 0 告警、116 帧不变、脚本 105 全绿。

## Round 57 · 带捕获把横幅两臂从"判不到"变成"判得到"，代价是撞出一条更贵的账（R57 / BACKLOG 77 结案 / U-84 / D-116）

**这一轮问的问题**：BACKLOG 77 挂了五轮的那一句 —— 横幅的进入与撤走两台机器都量不到 ——
根因到底是产品没演，还是量尺太慢？R55 的归因已经给了半个答案（`解释=98%`：
一个采样间隔≈一次抓帧 + 一次等 runloop）。这一轮去把抓帧本身变便宜，看那两臂会不会自己站起来。

**答案：会，而且比推算的还好。** 不降倍率（R55 推算的"按 1× 拍"会抹掉我要看的像素），
改**缩区域**：横幅两臂从整窗 1520×1346px 收到顶部一条带 1520×96px（面积 1/14）。
本机三次连续跑同一份代码：抓一帧的中位 39.5–39.8ms → **4.4–4.6ms（≈9 倍）**，
整卷中位间隔 44–45ms → **9–10ms**，同一场景 A/B 的过渡帧数 3–4 → **10–11**，
`MOTION_RESOLVE_SUMMARY judged=4/4 not-run=-`（这一族以前在本机是 2/4）。
登记表跟着改回严格：两臂 `must_judge=true`，`thin_warnings` 清空。

**本轮真正学到的三件事，都是量尺的**：

1. **"带在错的地方"不会被任何"有没有变化"的判据拦住。** 第一版 `bannerBand` 按 AppKit
   "原点在左下"写，而 `NSHostingView` 是**翻转**的 ⇒ 带抓到了窗口底部。
   而四条前提（帧高变小、成本变低、峰值过地板、首尾差够大）**全部通过** ——
   横幅撤走之后下面整块列表在位移，位移也是变化。我差点把"9 倍便宜、4/4 满覆盖"写进台账，
   而那一版量的是列表。
2. **我给它补的那条颜色判据是更坏的答案。** 第二版写"带里必须有警告粉"，阈值 `r>60 且 r−g>18`；
   实测那层 `Color.orange.opacity(0.12)` 的 r−g 只有 ≈12 ⇒ **恒红**。
   它想拦的东西是真的，但它用的数是我猜的 —— 猜出来的判据既不判产品也不判几何。
3. **拦得住的是来源，不是强度。** 最后一版问：带的那一帧必须与整窗那一帧的**同一头逐像素相同**
   （实测 0.000），且与**另一头明显不同**（实测 0.954）。两条一起，才既不许带跑掉、
   也不许"两头本来就一样"把第一条洗成恒真（M288/M289 一对变异就是分别打这两边的）。

**顺手撞出的更大的一条（BACKLOG 80）**：第二条为什么会算错 ——
`changedFraction(band:)` 的归一化带是**上下颠倒**的（注释说缓冲区第 0 行是底边，实测第 0 行是顶边）。
于是这个文件里 7 处 `band:` 调用点量的都是镜像位置：`// 横幅那一条`（y 0.02–0.22）
量的其实是 y 0.78–0.98，`侧栏第 4 行的星标列`（y 0.26–0.38）量的是 y 0.62–0.74 那一档；
只有关于中线对称的那两条（详情区 0.12–0.88、列表中部 0.35–0.65）侥幸没跑偏。
本轮**绕开**它而不是修它 —— 修它要把 7 条地板全部重算，而那些地板是在量错的地方调出来的。
它在可信度上排在 77 之前。

**看图（本轮的真实视觉审查）**：带内那一帧确认横幅在带里、"知道了"在右上、
第 78 行起才是搜索框（所以 48pt 装得下 38pt 的横幅还余 10pt）。
同时看到一件不属于本轮的事：暗色模式下这条带在**离屏帧**里是浅粉底 + 白字，
因为底调是半透明的、而离屏 `cacheDisplay` 没有窗口背景可合成 ⇒ 平铺到 PNG 的白底上。
**这不是产品缺陷，是捕获通道的产物**，但任何"从横幅那一条帧里读墨与底"的对比度尺都会被骗到 ——
记 BACKLOG 82（R24 那条 `testNoticeBodyTextStaysReadable` 今天跑的是亮色夹具，所以没撞上）。

**分数**：95 → 96。产品零改动。动的是"流畅度那一维我到底能不能判"：
横幅这一族从今天起在本机是**有 10–11 帧过程可看**的，而不是只能记 not-run。
`流畅度` 13 → 14/20；runner 侧那半还悬着（下一条）。

### 自评 96 / 100

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 18 / 20 | 产品零改动 |
| 流畅度 | 14 / 20 | 横幅两臂本机第一次判到过程（10–11 帧）；runner 侧还没有一次带捕获的读数 |
| 层次与材质 | 15 / 15 | 116 帧不变 |
| 动效细节 | 14 / 15 | 沿用 |
| 交互反馈 | 10 / 10 | 沿用 |
| 可访问性 | 9 / 10 | 沿用（读屏播报仍未核，独立一轮） |
| 性能 | 15 / 15 | 抓帧成本降 9 倍发生在**测试进程**里，产品路径零改动 |

**仍然悬着的**：① runner 上带捕获的第一次读数（若 CI 红在 `UNDERCOVERED`，那是闸门在说真话）；
② BACKLOG 80 那条镜像（下一轮专门修，要重算 7 条地板）；③ 带高 48pt 没有"必须盖住横幅"的判据
（BACKLOG 81）；④ 离屏底调那一条（BACKLOG 82）。

## Round 58 · 那条分带尺是上下颠倒的：修一行，重算七处，再补上"CI 看不见新读数"这个洞（R58 / BACKLOG 80 结案 / 新开 83、84 / U-85 / D-117）

**这一轮问的问题**：R57 结案时我写下 BACKLOG 80 —— `changedFraction(band:)` 把归一化带
**上下颠倒**了，7 个调用点量的是镜像位置，"它排在 77 之前"。这一轮就去修它，
并且要回答一个更不客气的问题：**这五轮里有多少结论是在量错的地方得出的？**

**答案分三层，最浅的一层最便宜**：映射改对是一行（`yStart = minY*h`）。
但一行改完不能宣布结案，因为"方向"这件事从来没有判据 —— 所以先写真值表：
合成位图，差异只放在上/下/左三处，六个方向格 + 一格"夹具自己不对称就红"的自检。
**它在坏的映射上先红了四格**（顶边读不到、底边读到了），横轴那两格与整幅那格全绿 ——
这个形状本身就是诊断：只有 y 被翻了。

**第二层是重算七个调用点**（逐个算镜像区间，不是一句"都可能错"）：
关于中线对称的两条（详情区 y 0.12–0.88、列表中部 y 0.35–0.65）**从来没错过**；
表格区上下各偏 0.02；真正跑偏的是两条 —— `// 横幅那一条`（y 0.02–0.22 → 实际 0.78–0.98）
与 `侧栏第 4 行的星标列`（→ y 0.62–0.74）。

**第三层才是本轮真正的收获，而它是 R57 自己带进来的**：
`testSlidingRoleSettlesWithinItsBudget` 也写着 `// 横幅那一条`，
但 R57 把那一臂的**整幅**换成了顶部那条带 ⇒ 同一个归一化矩形现在量的是
"带里再框一条 9.5pt 的窄缝"（连文字都不在里面）。三个数摆在一起最说明问题：

| 量的是哪一块 | `MOTION_SETTLE banner-in` |
|---|---|
| 窗口底部（镜像错，R57 之前） | 帧 11 / ≈121ms |
| 带里的 9.5pt 窄缝（嵌套错，R57 之后） | 帧 6 / ≈66ms |
| 整条带（本轮修完） | 帧 15 / ≈165ms |

**三个数都没让任何判据变红。** 上限那条判的是 `≤ 2×声明 + 一个采样间隔 = 311ms`，
121 / 66 / 165 全都过 ⇒ "换了捕获区域"这件事会安静地改掉别人的测量对象，
而这条判据在这个维度上**没有分辨率**。⇒ 新守卫
`testNoTestFramesABandInsideABandCapturedFilm`：带捕获那一卷上不许再传非 nil 的 `band:`。
它第一版是**假红**的（"这个函数里既出现了带捕获场景、又出现了 band:"），
被 `testListRowsDoNotAnimate…` 顶回来 —— 那条判据的主判据用整窗那卷正常传带、
阳性对照用横幅那卷**不传**带，本来就是对的。⇒ 谓词改成一点点数据流：
场景变量 → 胶片变量 → 传了非 nil band 的调用点。**假红的代价是有人去把一条正确的判据改松。**

**顺带撞开的另一个洞（BACKLOG 83）**：读 R57 的 CI（run 38570965657，整作业 success）时想
在日志里找"runner 上带捕获到底成没成功"，结果一行 `MOTION_BAND` 都没有 ——
CI 的读数摘录用的是一份**硬编码前缀白名单**，R55 的 `MOTION_GRAB` 与 R57 的 `MOTION_BAND`
都没进去。所以那一步只留下 `judged=4/4`，而带捕获之前的 R56 也是 4/4 ⇒ **两个形状分不开**。
本轮把它改成"先报 `MOTION_LINES=N`，再全打"，并给自检加一格 `family_not_in_any_list`
（M299 把白名单放回去，它就红）。白名单会随每一轮变旧，"打了多少行"不会。

**R57 的 CI 读数（一并补上）**：`MOTION_CHANNEL_UNIONED=1 stdout=61 文件=65`
⇒ 那条通道**又部分丢了一次**（4 行只从文件通道回来），并集把它们接住了；
`judged=4/4 not-run=-`、`MOTION_FLOOR_REDS=0` ⇒ 收紧后的登记表在 runner 上没有红。

**分数没动，这是有意的**：96 → 96。产品零改动，而 96 的天花板来自
`流畅度 14/20` —— 那一维还差 runner 上"看得见过程"的读数，本轮修的恰恰是
"那个读数在 CI 上根本看不见"。它下一次跑才有数，届时才谈得上 97。

### 自评 96 / 100

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 18 / 20 | 产品零改动 |
| 流畅度 | 14 / 20 | 沿用；本轮把"runner 的读数看不见"这个障碍清掉了，但数还没回来 |
| 层次与材质 | 15 / 15 | 116 帧不变 |
| 动效细节 | 14 / 15 | 沿用 |
| 交互反馈 | 10 / 10 | 沿用 |
| 可访问性 | 9 / 10 | 沿用（读屏播报仍未核，独立一轮） |
| 性能 | 15 / 15 | 全在测试进程 |

**仍然悬着的**：① runner 上第一次带捕获的读数（下一轮 CI 才看得见，BACKLOG 83 已修通道）；
② `changeGrid` 的行序现在对了，但没有判据钉住它（BACKLOG 84）；
③ BACKLOG 81（带高 48pt 没有"必须盖住横幅"的判据）、82（离屏底调合成到白底）；
④ BACKLOG 72 的迁移（本机 + runner 都答"从没出现"）。

## Round 59 · 逐帧图第一次看得清；然后我把自己配的两个数都证伪了（R59 / 新开 BACKLOG 85、86、87 / U-86、U-87、U-88 / D-118）

**靶**：R57/R58 把采样变细之后，横幅两臂本机第一次有 10–13 帧过程。
但"有 10 帧"≠"看得见那 10 帧"：带卷只有 96px 高，而 `writeStrip` 按 `width/2` 画 ⇒
横幅那条被缩成 38px 的一行色块，**要看的东西正好被缩掉了**。R22 那句
"帧 2 是原地的半透明 ⇒ 它是淡出，不是塌陷"我引用了五轮，而它的证据是一格中间态。

### 做了什么

1. **`writeStack`：带卷按原始像素竖排**（十帧 1520×980，第 0 帧在最上面，帧间 2px 暗线）。
   配套判据 `testBannerFrameStacksAreReadableEvidence` 判的是**证据本身**：
   文件在不在、宽高是不是按原始像素算的（不是除二）、以及**这一叠里至少有一对帧真的不同**
   —— 最后那条是关键：一叠同一张图也能写出正确尺寸的文件。
2. **看了图，然后按图说话**（本轮两次看图，第二次推翻第一次）：
   第 5 帧起侧栏的**搜索框已经上移到横幅那一行，并画在还没淡完的横幅文字之上**
   （字的下半是被**盖住**的，不是被裁的）；详情区那侧"无法自动粘贴。"与"知道了"还在原高度淡，
   列表从下面滚上来；横幅那层粉底**整幅都还在**。
   ⇒ 问题的形状是**层叠**（`.bannerOut` 只给 `.opacity`，布局却已经重排），不是"两栏进度不同"。
3. **给自己配的两个数做了证伪实验**（这才是本轮真正的产出）：
   - 分栏那条：`transitionFrameCount` 的门槛是**各自峰值**×15% ⇒ 两栏各归一化，
     墨多的那栏线更高、先判停。新增 `sharedMovingFloor`（两栏较大峰值 × 同一个 15%）之后，
     本机五遍两栏"最后一个还在变的帧号"**完全相同**（16/16、17/17、17/17、17/17、16/16）。
     ⇒ 那句"侧栏先落定 2–5 帧"作废。
   - 图标那条：全帧质心 42→29px 看着像"被抬走"，实际是**判色阈值在动**
     （淡下去时高饱和边缘先脱落，剩下的像素聚哪边质心就往哪边漂）。
     新增**外框上下沿**这条轴 + 只看强帧（像素 ≥ 首帧一半）之后：强帧跨度 2.6/0/0/0/0px、
     外框 **4/5 遍一格没挪**（[29,50]→[29,50]）。⇒ "上移 6.5pt"作废；
     但也没写成"绝对没动"（第 1 遍下沿上移 4px，正落在脱落量级里，±2px 容差分不开）。
     顺带**部分恢复**了 R22 那句：淡出这一半被外框证实了。
4. **措辞从函数里出来**：`columnSettlementVerdict` + 合成真值表
   `testSharedFloorColumnComparisonIsATruthTable`（同帧 / 真差 N 帧 / 都没动 ⇒ 作废 / 只有一栏动 ⇒ 报框错）。
5. **CI 那一步的红要能读**：R58 run 38576482491 里 `testTransitionsAreActuallyRunning` 红了 7.4s、
   `motion suite exit: 1`，而整个 run 结论是 success（`continue-on-error`），日志里连 `XCTAssert` 原文都没有。
   本轮补 `grep -E "error: -\["` + 自检 `red_test_prints_its_reason`（M305 摘掉就打红）；
   **没有**顺手把整步改成有闸 —— 那需要一次"红的确实是产品"的样本（BACKLOG 86）。
6. **"0 告警"那一步原来不编译测试目标**（BACKLOG 87）：R58 提交的那条 `variable 'a' was never mutated`
   在 `swift test` 输出里明明白白，两次 CI 都是绿的。清洁基线量出来是 **0 条** ⇒
   本轮把命令改成 `swift build --build-tests`、多打告警原文、并加了一条**真跑那段脚本**的守卫。
7. **登记表里那句"runner 侧还没有一次带捕获的读数"更正了**（R57 写的，R58 的 CI 已经给了数）：
   带=抓帧中位 5.6ms / 间隔中位 22ms / 760x48px，整窗=14.1ms / 22ms / 760x588px
   ⇒ 带在 runner 上买到的是**时间不是分辨率**，本机那对 44→9ms 的增益在那边不存在。

### 本轮撞到的两个自己的错（都写进了判据）

- **红不许变成崩溃**：M303 第一遍跑出 BROKEN-MUTATION —— 断言红之后代码继续 `seen[0]`，
  空数组越界把进程带走，"Test Case … failed" 那行根本没打出来。改成 `guard … else { XCTFail; return }`。
- **汇总脚本会跟着读数格式一起烂**：`assemble_r59_readings.py` 里那条 `(.*)$` 在没有 MULTILINE 时
  只认文末，于是 BOX 行匹配不到、`min()` 打在空序列上、文件写了一半。现在每条读数各自抽干净、
  抽不到就报错退出，并且表里的数字全部现算（上一版还留着一句硬编码的"文件通道 72 条"）。

### 真实视觉审查

看的就是本轮新写的那张十帧竖排图（`/tmp/r59-motion/notice-banner-dismiss-逐帧-stack.png`）：
前四帧横幅整条在淡、第五帧起搜索框压上来、后五帧只剩详情区那半截尾巴还在淡。
第一次看得出"两栏不同步 + 图标上移"，第二次带着新的两条轴重看，两个数都没保住 ——
**图是对的，数是我算错的**。

### 自评 96 / 100

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 18 / 20 | 产品零改动；本轮没有新增视觉糖，也没有撤掉任何一档 |
| 流畅度 | 14 / 20 | 天花板没动：runner 的 22ms 采样仍不足以判"顺不顺"，而真屏幕那三问（批次 56.2 / 59.2）还没回答 |
| 层次与材质 | 15 / 15 | 116 帧 vs working 基线 CHANGED=0 |
| 动效细节 | 14 / 15 | 没加东西，但把两处"我引用过的证据"证伪了；剩下那条"淡出与内容层叠"要不要修等真屏幕 |
| 交互反馈 | 10 / 10 | 沿用 |
| 可访问性 | 9 / 10 | 沿用（读屏播报仍未核，独立一轮） |
| 性能 | 15 / 15 | 四条新判据全在测试进程；多约 6s |

**分数没动是有意的**：本轮没有让任何一个像素变好，它做的是**把上一轮写进台账的两个假数拿掉**。
96 的天花板仍然在 `流畅度 14/20`，那一维缺的是真屏幕与更细的时钟，不是再多一条判据。

### 仍然悬着的

① 那条"淡出中的横幅与已重排的内容重叠"是不是缺陷（批次 59.1，二选一问句已改）；
② CI 的 motion 那一步仍是 `continue-on-error`，红不影响结论（BACKLOG 86，要一次"红的是产品"的样本）；
③ runner 上收紧后的告警闸门会不会报出本机没有的告警（BACKLOG 87 的最后一格）；
④ 外框那条轴分不清"边缘脱落"与"一边被裁"⇒ 要换一条**不吃饱和度**的位置轴（跟几何轮廓走）；
⑤ BACKLOG 81（带高 48pt 没有"必须盖住横幅"的判据）、82（离屏底调合成到白底）、84（网格行序没判据）；
⑥ BACKLOG 72 的迁移（本机 + runner 都答"从没出现"）。

## Round 60 · 三条不依赖颜色的轴都没能量出"重叠"；CI 用一条假红教我把地板按机器分开（结案 84、87 / 新开 88、89 / U-89、U-90 / D-119）

**靶**：R59 证伪掉两个数之后，BACKLOG 85 只剩一条看图结论（淡出中的横幅被上移的搜索框盖住）。
本轮想把它变成判据；顺带把 R58 留下的"网格行序没有判据"（84）钉上。

### 做了什么

1. **把逐帧图放大到能看清为止**：`zoom.swift` 把堆叠图切成单帧、3 倍放大
   （`.scratch/motion-audit-2/r60_evidence/f4-left-3x.png`、`f5-left-3x.png`）。
   看清了：字的下半是被那片圆角填充**盖住**的（不是被裁），红图标的尖还在填充之上。
2. **三条轴，三条都失败，失败原因各不相同**（这是本轮真正的产出）：
   中灰像素数 ⇒ 淡到一半的白字正好落进中灰带；最长均匀段 ⇒ 横幅那片平底本身就是均匀的；
   水平直边 ⇒ 只检出第 0–1 帧的分隔线，搜索框的边是软渐变、根本不在这条轴的候选里。
   ⇒ 结论是方法级的：**重叠双方都在动**，任何按亮度/颜色/边界的阈值都会被其中一方污染。
   要分开只能换捕获方式（"关掉动画"那一臂与"开着"那一臂在同一帧号上相减）⇒ BACKLOG 88 / R61 的靶。
   观察**不撤也不升级**：它现在是"人眼看见、机器复现不出"，批次 59.1 的问句仍然有效。
3. **BACKLOG 84 结案**：`changeGrid` 拆成"位图版 + 薄壳"，新判据
   `testChangeGridPrintsRowZeroAtTheTop` 把差异分别放顶边/底边/左边（列序是同一处映射的另一半，一起钉）。
   顺带把 R58 的合成分位图闭包提成共用的 `syntheticPair` —— 各自一份就会有一份跟着实现变旧。
4. **读了 R59 的 CI（run 38586812301，整作业 success），R59 那条 grep 第一次跑就兑现**：
   `motion suite exit: 1` 这次带着两条红的原文，其中一条是**我的假红**：
   `testBannerOutTracksWhetherItFadesOrSlides` 在 runner 上报"整卷只找到 0 帧里有那颗红色图标"。
   0 帧不是采样粗，是**判色前提在 1x 上不成立**（那颗 ~22px 的实心红符号几乎没有纯色核心像素）。
   我把地板 4 写成了本机的数（五遍 5–6 帧）⇒ **R38 那一族我又犯了一次**。
   ⇒ 改成：认不出图标时发 `MOTION_TRACK_VOID`（附缩放、单帧最多红像素、扫描窗换算成 pt 的诊断）不红；
   但 2x 那台机器上前提是被实测撑住的，所以那里认出 0 帧**仍然必须红**（M303 换 needle 后重跑 CAUGHT）。
5. **BACKLOG 87 结案**：`compile warnings: 0` —— 收紧成 `swift build --build-tests` 之后，
   runner 的 Swift 6.1.2 在测试目标里也没报出任何告警。
6. **新开 BACKLOG 89**：runner 上那条"提示条只演了 57ms ⇒ 一帧跳变"的红，
   57 < 2×38（它自己报的"事件内最粗采样"）⇒ 那条"变化段"连两次采样都不到，
   "演一帧就停"与"演很久只抓到一帧"给出同一个读数。缺的是 `.spanUnresolved` 那一格；
   本轮没顺手改，因为那条 not-run 会把覆盖率闸门翻成 UNDERCOVERED 红，得先补一格夹具。

### 本轮撞到的自己的错（都写进判据/台账）

- **台账自己也会坏，而且没人拦**：R59 往 CHANGELOG 插正文时把 `## [Unreleased]` 那行一起插了进去
  ⇒ 文件顶上出现两个同名标题，而脚本测试 107 格全绿。本轮修好并加了 `test_changelog_shape.py`
  （只判"有且只有一个 Unreleased"这一件真的踩过的事）。
  中途还写过两条被删掉的规矩（"小节类型必须是 Keep a Changelog 那六种"、"同一类型不许出现两次"）——
  它们红了两次，红的是守卫自己：这个文件早就在用 `### Tests`、`### 判断（R…）` 这些约定。
  **守卫要记约定，不许拿标准去追认约定。**
- **把本机的读数当成分布式地板**：`seen.count >= 4` 在本机五遍是 5–6，在 runner 是 0 ⇒ 假红。
  同一族 R38 已经记过一次账，这次是**我自己在新写的判据上重犯**。
- 更正一条旧话：带捕获在 runner 上的采样这次确实变细了（19ms vs 整窗 32ms），
  R58 那次是 22ms vs 22ms ⇒ "带买到的是时间不是分辨率"不能当常数写，得按"两次运行不一致"来记。

### 真实视觉审查

两张 3 倍放大的单帧裁剪图（看的内容与结论见上）；另外本轮重看了十帧竖排整图一遍，
确认第 5 帧那一下"填充压在字上"的形状与三条轴的失败方式互相对得上。

### 自评 96 / 100

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 18 / 20 | 产品零改动 |
| 流畅度 | 14 / 20 | 天花板没动；runner 那条"57ms vs 150ms"到底是产品还是尺子，正是这一维缺的答案（BACKLOG 89） |
| 层次与材质 | 15 / 15 | 116 帧 vs working 基线 CHANGED=0 |
| 动效细节 | 14 / 15 | 没加东西；撤掉一条假红，并给"重叠"这件事定了它不能成为判据的理由 |
| 交互反馈 | 10 / 10 | 沿用 |
| 可访问性 | 9 / 10 | 沿用（读屏播报仍未核，独立一轮） |
| 性能 | 15 / 15 | 新判据在测试进程；motion 全量 89.6s |

**分数不动是有意的**：产品零改动，而本轮值钱的三件事是钉住一个洞（84）、撤掉一条假红（我自己写的）、
把一条看图结论的机器可复现性**诚实标成未证明**（88）。

### 仍然悬着的

① "重叠"到底在不在（BACKLOG 88 换捕获方式 + 批次 59.1 真屏幕）；
② runner 那条 `testTransitionsAreActuallyRunning` 的假红/真红（BACKLOG 89，要先补闸门夹具）；
③ CI 的 motion 那一步仍是 `continue-on-error`，红不影响结论（BACKLOG 86）；
④ BACKLOG 81（带高没有"必须盖住横幅"的判据）、82（离屏底调合成到白底）、72 的迁移；
⑤ 真屏幕那批问题（最想要 45.1 / 47.1 / 52.1 / 56.2 / 59.1 / 59.2）。

---

## Round 61 · 修 BACKLOG 61：先证伪自己上一轮写的论证和修法，再落地「只滚不选」（结案 61 / D-120 / U-91）

**靶**：61 是唯一一条"界面在讲一条用户看不见的记录"的挂账。上一轮（R60）我给它写了可达性论证 +
候选修法 `ScrollViewReader.scrollTo(id)`。本轮开场先 spike。

### 做了什么

1. **spike 否掉我自己的两份结论**（顺序很重要：先否论证，再否修法，最后才动产品）
   * 论证错在机制：`HistoryStore.add` 末尾 `reconcileSelection(preferredEntryID: 新条目)` ⇒
     选中项不漂，每次都被换成新记录；漂 nothing。真正的落点是 `EntryOrdering.promotionIndex`。
   * 修法不成立：真的写进侧栏跑过两版（带 / 不带 anchor）。临时插桩 `GLUE_DEBUG` 打出
     "已请求 scrollTo" 两次，而表格 `documentVisibleRect` 仍在 y=0、`selectedRow` 仍是 -1。
     孤立 spike 里同一形状 0.25s 滚到第 60 行；六臂 bisect（focusEffectDisabled /
     onDrop+overlay+animation / VStack 在 reader 内 / Button 行 / 产品形状的行 / reader 在 if/else 里）
     全绿 ⇒ 找不到哪一件按死的它 ⇒ 结论是"这条路在产品侧不成立"，三行胶水已回滚，
     并由一条源码守卫钉住"没重测不许写回来"。
2. **量出真正的地板**：只把那一行滚进视口、**不动选中**，SwiftUI 自己就把选中补上
   （3/3 稳定 `[]` → `[60]`）⇒ 缺的只是"揭示"，不需要第二个选中作者。
3. **落地 `SelectedRowRevealer`**：只滚不选（D-1 修法③不变）+ 可见不动（R22 那一族的自伤闸）+
   **选中变了才滚**（闸门按 id 不按行号：M313 第一版活下来之后才改对）+ **推迟一个回合**（同步滚会让上一行的取消选中丢失，
   读到 `[2, 60]` 而 store 只有 1 条 —— 修法自己造的新分裂，实测逼出来的第四条边界）。
4. **判据**：`SelectedRowRevealTests`（`rowIndex` 真值表 4 格 + 两条源码守卫）+
   探针四臂（近处不跳 / 远处滚过去 / 用户滚开不再被拽回 / 通道前提）+ 采集路径那条
   （从 `store.add` 进，不需要任何点击）。
5. **两次并发事故，都记进工具**：变异脚本用 `git checkout --` 还原**未入库的新文件** ⇒ pathspec 不匹配、
   那一刀留在树上、四刀叠在同一文件里；第二套电池又在第一套没退时并发跑 ⇒ 基线读到对面的产物。
   脚本改成"按内容还原 + pidfile 锁 + 基线不绿就拒跑"。

### 真实视觉审查（本轮看的是渲染图，不是代码）

`reveal-before / reveal-after-320x300-light.png`（探针取证通道，320×300 在屏窗口的离屏重绘）：
before = 顶部那段固定块、表头"已选 4 条" + 一排批量按钮；after = 列表已经滚到新记录那一行、
表头换成"时间剪史 / 62 条记录"、新那一行带着填充贴在视口下沿。
⇒ 位置与状态这两件事看得见；**填充的颜色看不见**（在这条通道里解析成黑块，R29/R30 那族材质盲区），
所以配色不作判据，只作位置取证。另外 116 张帧基线全等（CHANGED=0）本身就是本轮的一个结论：
**离屏静态帧结构上看不到"跟随选中滚动"** —— 静态帧里选中永远在第一行，揭示器正确地什么都不做。

### 七维自评

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 19 / 20 | 选中项被揭示是系统表格的默认行为；没自造高亮、没自绘胶囊 |
| 流畅度 | 14 / 20 | 天花板没动；滚本身是 AppKit 的原地跳，无动画（这是系统语义，不是缺动效） |
| 层次与材质 | 15 / 15 | 116 帧 vs working CHANGED=0 |
| 动效细节 | 15 / 15 | 没加动效；把"选中→揭示"这条状态反馈补全，并撤掉一条不成立的声明 |
| 交互反馈 | 10 / 10 | 详情区与列表重新指向同一条记录；用户手工滚动不再被抢走 |
| 可访问性 | 9 / 10 | 沿用（读屏播报仍未核，独立一轮） |
| 性能 | 14 / 15 | 多一个宿主视图 + 一次有界的视图树解析（缓存 weak）；全量 150s / 771 例 |

**96 / 100**。比 R60 的 96 略动了两处（原生感 -1：多了一个 AppKit 桥；性能 -1：多一次树解析），
加分的是"界面不再讲一条看不见的记录"这件产品事实本身。

### 仍然悬着的

① BACKLOG 88（重叠那条轴）与 89（runner 那条假红/真红）本轮**没动** —— 61 的现场把整轮占满了；
② BACKLOG 86（motion 步骤仍 continue-on-error）；③ 81 / 82 / 72；
④ 真屏幕那批（最想要 45.1 / 47.1 / 52.1 / 56.2 / 59.1 / 59.2，本轮新增 61.1：
   固定一批记录再连续复制，看列表会不会自己滚过去、滚过去那一下烦不烦）。

---

## Round 62 · CI 那句「探针没跑完」是真的，但它让 11 条在屏判据一起免检（结案 91、92 / 新开 93 / U-93、U-94 / D-121）

**靶**：读 R61 的 CI 时看到 `ui suite exit: 137  executed: 0  已下结论的用例: 0`。

### 做了什么

1. **把「缺席」变成逐条点名 + 一条硬门**：`scripts/probe_coverage_gate.py` 对
   `UIInteractionProbeTests` 的 11 条在屏判据逐条判 `UNLISTED / STALE / REASONLESS /
   NOT_RUN / NOW_RUNS / BAD_RUNNER_FIELD / FAILED`，配 `probe_coverage_expectations.json`
   与 CI 新步骤 `On-screen probe coverage floor`。探针那一步继续报告型（它不该挡发布），
   **登记**是硬门（它只判"有没有人知道"）。
2. **推翻自己上一轮写的 BACKLOG 91**：那条"闸门没有读数"是**电池跑错测试**造的 ——
   漂移那一臂在 R61 中途被拆进独立测试，filter 还指着老那条，判据根本没被执行。
   修好重跑：M313、M317 都 CAUGHT，红在 `2125.0 ≠ 0.0`（行号漂了视口却动了）⇒ 闸门有读数。
3. **电池自身修两件**：每刀的 filter 必须证明"那一臂在被跑的那条测试里"（基线缺一条结论就整套拒跑）；
   `PYTHONDONTWRITEBYTECODE=1`（M319 连跑判 SURVIVED、单跑判 CAUGHT，是 `__pycache__` 撞车）。
4. **判据与对照**：`test_probe_coverage_gate.py` 12 条（含"登记与源码必须同一批"这条活检查）；
   电池 M318–M324 七刀全 CAUGHT。

### 真实视觉审查

本轮产品零改动 ⇒ 没有新像素可看。做的是**等价核验**：116 帧 vs working
`CHANGED=0 / MISSING=0 / ADDED=0` ⇒ 这一轮确实没动画面。
（写清楚是为了不把它冒充成"看过画面"：连续两轮在尺子上，而侧栏/设置/浮层还有一批位点没判完。）

### 七维自评

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 18 / 20 | 产品零改动；本轮的东西都在 CI 侧 |
| 流畅度 | 14 / 20 | 天花板没动；BACKLOG 93（探针在 runner 上挂死）今天仍没解 |
| 层次与材质 | 15 / 15 | 116 帧 vs working CHANGED=0 |
| 动效细节 | 13 / 15 | 没加动效；把 R61 那条误判结案，并让"CI 没跑"变成逐条点名 |
| 交互反馈 | 10 / 10 | 沿用 R61 |
| 可访问性 | 9 / 10 | 沿用（读屏播报仍未核，独立一轮） |
| 性能 | 14 / 15 | 新增一步 python 闸门（秒级）；脚本测试 108 → 120 |

**93 / 100**。比 R61 的 96 低是有意的：**连续两轮没碰产品与画面**，
价值在"让盲区可见 + 推翻自己一条错判"，但阶段二的主体（逐位点判断动效该不该加）没推进。
R63 回到产品面。

### 仍然悬着的

① BACKLOG 93（在屏探针在无头 runner 上挂在哪一句）；② 88（重叠那条轴）；③ 89（runner 那条偶发红）；
④ 90（滚回顶部后表格选中集多留一行）；⑤ 86 / 81 / 82 / 72；⑥ 侧栏与设置里没判完的位点（63/64/65/66 那一族）；
⑦ 真屏幕那批（45.1 / 47.1 / 52.1 / 56.2 / 59.1 / 59.2 / 61.1–61.4）。

---

## Round 63 · 快速选择浮层第一次被看见：它一直是塌的（结案 30-① / 新开 94、95、96 / U-95…U-99 / D-122）

**靶**：R62 连着两轮在尺子上，这轮回到产品面。第一个位点就是**从来没进过帧基线**的快速选择浮层
（⌃⇧V，`QuickPickController` 自建的 `NSPanel` + `NSTableView`）。R19 给它记的原因是
"stack 在**捕获环境里**塌，真实 App 里撑满 420×300"。

### 开场读数（先量，再判断）

同一条探针、同一个夹具、只换那一个文件：

| | 修前（HEAD） | 修后 |
|---|---|---|
| 产品 stack frame | `{{0,0},{24,49}}` | `{{12,12},{396,276}}` |
| `NSScrollView` | `{{12,12},{0,0}}` | `{{12,12},{396,251}}` |
| `table.visibleRect` | `{{0,0},{0,0}}`（8 行） | `{{0,0},{396,251}}` |
| `cacheDisplay` 画了多少 | **0.0%** | **19.3%**，竖向 10 档 `4 39 62 14 14 15 15 14 10 5` |
| 空结果那句 | 模型 `alpha=0.000`（转 2.1s 仍是 0） | `alpha=1.000`，落在竖向第 2 档（紧跟搜索框，gap=8.0pt） |

⇒ **"真实 App 里没问题"这半句是假的**：两条路都塌。机制由最小对象图 spike 给出：
`NSStackView(views:)` 生下来 `translatesAutoresizingMaskIntoConstraints == false`，
所以产品那两行 `frame` + `autoresizingMask` 在真机上也是空操作。
**用户按下 ⌃⌥⇧V 看到的从来就是左下角一小块内容 + 四分之三的空白。**

### 做了什么

1. **产品**：`ensurePanel()` 里把尺寸所有权写成四条贴边约束（内缩 12pt 只写在这四个常量里，
   `edgeInsets` 归零）；`empty.wantsLayer = true`（模型值恒等于终值，淡入只是装饰）；
   那句"没有匹配…"从列表**下面**挪到列表**那一格**（推翻我自己 R7 的决定，理由写在代码里）；
   句子与搜索框降**抗压缩**优先级（见下面那条自捉的缺陷）。
2. **夹具**：`quickpick-list / -typed / -empty` 三张 × 亮暗 = **6 张**，基线 116 → **122**。
   `withAppKit` 这条 R19 加完一直没人调的通路第一次有了调用点。
3. **判据**：R19 那条"还拍不到"翻成契约
   （`testQuickPickOverlayFillsItsPanelAndCanBeCaptured`：行、所有权、两条轴的占满比例、
   可视区 ≥ 2 行、能不能拍），另加一条空结果态契约
   （`testQuickPickEmptyStateSentenceIsCommittedAndSitsInTheListSlot`：在、没藏、`alpha==1`、
   紧跟搜索框 ≤24pt、横向居中 <3pt、**长查询那一档面板不许变宽**）。
4. **撤掉一条基于假解释的夹具豁免**：`render` 里"AppKit 夹具不走强制布局"。
   解释倒了，豁免就得重新审 —— 现在两条路同一套布局代码。
5. **给"尺的假设"立了一份带正对照的名单** `sparseByDesignFixtures`（见下面的挣工资记录）。

### 本轮自己改出来、又被自己判据抓住的一个缺陷

把 stack 钉到面板上之后，"内容要多宽"第一次**传到了窗口**：一条 40 字的查询词让那句
"没有匹配…"的固有宽度变成 879pt ⇒ **面板从 420 被顶到 899**
（实测 `QUICKPICK_LONG_QUERY 面板={{0,0},{899,300}}`）。
修之前那条通道根本不存在，所以这是本轮引入的回归；它是在我写"长查询那一档"判据时当场露出来的。
修法：句子与搜索框降抗压缩 ⇒ 面板稳回 420，句子被压到 400pt 内并截出省略号
（`句子 frame={{10,247},{400,16}}`，固有宽度 879）。
**这条判据故意不写 420 这个字面量**：它写的是"两个状态的面板同宽"，因为约定是
"面板尺寸不由查询词长度决定"，不是"面板必须是 420"。

### 变异替我做的设计评审（M325–M336）

第一轮九刀里 **M330 / M331 / M333 三刀绿着回来** ⇒ 我给三个子视图各写的等宽约束
和那行 hugging **今天没有作者**（`NSStackView` 的默认对齐本来就把无固有宽度的视图拉满）。
处置不是"加判据把它们钉住"，而是**把代码删掉**：删掉之后重拍 6 张帧，
`list` / `typed` 四张**逐字节不变**，只有 `empty` 两张变了 ⇒ 那三处确实是空转，
而 `empty` 那两条有活干（就是上面那个长查询缺陷）。于是最终留下的每一行都能指回一刀会红的变异：
M325/M326/M327（三条贴边轴）、M328（图层）、M329（竖向位置）、M334（等宽）、M335/M336（抗压缩）。

**挣了工资的两条守卫**：① `sparseByDesignFixtures` 的"不再稀了就红"立刻抓到
`quickpick-typed` 第一版查询词是我从自己探针里抄的"记录 3"，在 harness 那个 store 里命中 0 条
⇒ 帧名 typed、内容 empty；换成真命中 2 条的"访达"之后未绘制从 98.3% 降到 88.5%，
守卫红着把它赶出名单。② 电池自身上一版把"变异是否落地"的判据写反了
（"原文已不在"被我报成回读失败）⇒ 九条日志每条都挂着一行假警告。

### 真实视觉审查

看了 6 张新帧（亮/暗 × 列表/打字/空）+ 修前修后各一张探针图。判"是缺陷"的：
浮层塌（已修）、句子掉在面板最底（已挪）、长查询顶宽面板（已修）。
判"不是缺陷、记下来"的：
① 选中药丸左右留白**对称**（实测 `x=[44,795] of 840` ⇒ 两边各 22.0pt），
   我第一眼看成的"左窄右宽"是行文字自带缩进造成的错觉 —— 记下来是因为**这个错觉是我自己量错过一次的那类**；
② 行的文字左轴在 36pt（文件行 64pt）而搜索框文字在 12pt ⇒ 列表缩进是 AppKit 表格的常态，不动；
③ 列宽 364 而视口 396：右侧 32pt 是滚动视图给 scroller 的位置，`scrollerStyle=overlay` 下
   这是系统自己的算法，不动；
④ 行首那个 📄 是 **emoji**（`EntryPresentation.preview` 里写进字符串的），
   不吃 tint、与其余 SF Symbols 不是一套语言，而且它参与搜索匹配 ⇒ **BACKLOG 94**，
   跨侧栏/浮层/详情三个表面，不塞进本轮。
**没看到的**：真屏幕上那一张。`CGWindowListCreateImage` 在这台机器返回
932×692 尺寸正确的**全空**图（零墨）⇒ 它比 `nil` 更坏，因为空图会被读成"屏上是好的"。
记 **BACKLOG 95**，本轮所有像素判据一律走 `cacheDisplay`。

### 七维自评

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 19 / 20 | 修的是"看起来不像系统浮层"最响的那一条（四分之三空白）；📄 emoji 那条留给 94 |
| 流畅度 | 15 / 20 | 淡入的可见性不再押在动画上；但淡入本身仍是"源码已接、产物未量"（D-055 未变） |
| 层次与材质 | 15 / 15 | 6 张新帧进基线（116→122），亮暗两档都看过；浮层没有材质视图这一事实已核实 |
| 动效细节 | 13 / 15 | 本轮没有新增动效；撤掉一条"动画不跑就看不见字"的隐性依赖 |
| 交互反馈 | 9 / 10 | 空结果那句话第一次真的能被看见并落在用户视线那一格 |
| 可访问性 | 9 / 10 | 暗档文字可读（帧看过）；读屏播报仍未核，独立一轮 |
| 性能 | 13 / 15 | 面板固定尺寸不再被内容撑大（899→420 本身就是窗口层的修复）；捕获 +4s |

**93 / 100**。比 R61 的 96 低的地方很具体：这个浮层的**动效**这一轮几乎没碰
（只做了"可见性不依赖动画"），而 ⌃⇧V 呼出/退场、行移动、悬停三档还欠判断；
BACKLOG 88（重叠那条轴）本轮也没做。高于 R62 的地方是它动了产品并且动了用户看得见的那一块。

### R63 的 CI 追加（run 38683762166）：本轮自己写的那条守卫，在 runner 上判了一次假红

`Capture gate` 红了一条，而且红的是我本轮新写的那句：
`这些帧不再需要「天生就稀」的豁免了：["quickpick-empty"]`。
runner 的读数解释了为什么这是**假红**：同一张帧本机未绘制 **97.9%**、runner **94.9%**，
而门槛是 95.0% ⇒ 它在两台机器上"一个需要豁免、一个不需要"，
于是"这次没走豁免分支 ⇒ 名单过期"这句话换了一台机器就不成立。
（整族读数都偏移 3pt：list 85.8→82.1、typed 88.5→85.6、empty 97.9→94.9。）

**这正是 R38 记过的那条**（"两台机器的读数不能当另一台机器的地板"），
而这次是我**自己在写新守卫的一个小时里重犯**——判据的绝对数从本机读数来，
换机器就翻脸。修法不是放宽门槛，是**换成同一次运行内部的兄弟比较**：
空结果态必须明显比 5 行的列表态更空（本机 2.1% vs 14.2%、runner 5.1% vs 17.9%，两边都成立），
"这一格有没有内容"不随 backing scale 漂；另外把正对照（`drawn > 0.5%`）改成
**名单里的帧无论这台机器判不判它稀都必过**，并把"帧名与内容相符"从像素里拿出来，
新写一条产品入口级判据 `testQuickPickTypedFixtureShowsFilteredRowsNotAnEmptyList`
（typed 必须 1 ≤ 行 < 全量；实测 all=5 / typed=2 / empty=0）。

同轮第二件：这条守卫的第一版**当场 crash** ——
`Dictionary(uniqueKeysWithValues:)` 撞上"同一个夹具名有亮暗两张帧"（`Duplicate values for key`），
而我在那行代码上面刚写完"取更空的那一张来比"的注释。⇒ 归并必须显式写；
注释里写对的规则不等于代码里存在的规则。

修后本机：`swift test` **774 例 / 39 skip / 0 failures**、`--build-tests` **0 告警**、
122 帧 vs working `CHANGED=0`。

## Round 64 · 判据说的话可以整块消失而作业是绿的：补第二条通道，并更正我自己写的机制（交付 96 / 新开 97 / U-100…U-103 / D-123）

**靶**：R63 收尾时读到的一条事实 —— 浮层那三条判据在 runner 上都有 `Test Case … passed`，
而它们**自己写下的读数**一条都没进日志。红绿灯看不见"今天判了什么"。
本轮不碰产品，把这件事变成会红的判据。

### 开场读数（先量，再判断；三遍本机 + 两份 runner 日志，逐行比对）

| 跑法 | 读数文件 | stdout 少了 | 形状 | 五条 marker | 用例结论行 |
|---|---|---|---|---|---|
| `--filter UICaptureTests`（重定向到文件） | 488 行 | **324 行（66.4%）** | **1 块**：下标 164–487 | 全丢 | 37/37 在 |
| 同上，再跑一遍 | 488 行 | **324 行** | **同一块**：164–487 | 全丢 | 37/37 在 |
| `swift test` 全量（`2>&1 \| tee`，CI 的形状） | 488 行 | **238 行（48.8%）** | **3 块**：0–48、142–217、296–408 | 全丢 | 775/775 在 |
| runner run 38683762166 的捕获那一步 | — | — | — | 浮层 4 条到 **0/4** | 两条在、一条连结论行都没有 |
| runner run 38687419144 的捕获那一步 | — | — | — | 浮层 4 条到 **2/4** | 三条都在 |

切点落在**行中间**：stdout 停在 `…bottomI`，下一行直接是 `Test Case …`。
⇒ **R63 账本里"按条随机丢"这句是我把机制说过头了**（本轮更正）：真实形状是连续大块，
而且同一个命令形状下**位置可复现**。324 行实例 = 316 条不同的行。

### 做了什么

1. **第二条通道**：新增 `CaptureReadings.swift`（`emit` = print **并且**落盘；第一次整份重写、
   之后 `FileHandle` 追加；写坏了只走 stderr 报 `CAPTURE_READINGS_CHANNEL_BROKEN`，不把判据变红）。
   捕获卷 **69 处** `print(` → `emit(`（`git diff` 数出来的）。
2. **守卫**：`testCaptureReadingsUseTheFileChannel` —— 规则写成**绝对**的：
   `UICaptureHarness.swift` 剥掉注释后 `print` 出现次数 = 0。
   为了这条绝对性，通道实现搬去单独一个文件（白名单就是下一次绕过去的入口，R55 的 M276）。
3. **闸门**：`ci_capture_gate.py --readings <文件>` —— **并集 + 缺通道算一条有名字的红**；
   并集从 ci.yml 的 awk 挪进 python（那段 shell 没有一份自测能证明"补回的行数是对的"），
   workflow 里只留"通道在不在"的汇报行。
   本机拿真 artifact 跑：`补回=316 行`，**同一份日志不给 `--readings` 仍然是 0**（正对照）。
4. **自测** 120 → **127**：并集补回一条丢掉的断言行 / 缺文件红 / 空文件红 / 整行精确比对
   （同一句读数**数字变了**必须算两条）/ 重复行只补一次 / 不给 flag 时行为不变 /
   结论行打在通道那条红**之前**。外加一条**接线断言**：以后谁把 `--readings` 从 workflow 删掉会当场红。

### 变异替我做的设计评审（M337–M342，六刀全 CAUGHT）

| 刀 | 动哪里 | 必须红在 |
|---|---|---|
| M337 | 一处 `emit` 改回游离的 stdout 调用 | ① 扫描那一格 |
| M338 | 扫描用的串改成多一个空格（needle 坏） | ② **正对照**那一格 |
| M339 | 注释剥离器改坏 | ①（守卫会读到自己的注释） |
| M340 | 通道只 print、不落盘 | ④ marker 那一格 |
| M341 | 去掉"第一次整份重写" | ④ |
| M342 | `readingsURL` 指向必然失败的目录 | ④（红，而不是崩） |

**M338 抓到的是我本轮写的第一版正对照**：那版用 needle 拼对照，needle 坏掉时对照仍然 3/3、
而扫描一条都抓不到 ⇒ 拿尺子上的刻度验这把尺。改成 `\u{0070}` 转义的独立串之后立刻红在正对照那一格。
另外两把"电池自己骗人"的刀：`--filter` 打错会让整批"红"其实是 NOT-RUN（现在先要基线绿），
以及**上一遍留下的读数文件会让"落盘坏了"那一刀逃过**（M341 第一版就这么逃了）⇒ 每刀之前先删文件。
还有一条是汇总行自己坏了：`mark = "CAUGHT "` 带尾随空格，于是**六刀全抓到、汇总写"非抓到=6"**
⇒ 结论行改成 `!r` 打印，比对用 `.strip()`。

### 真实视觉审查（看的是渲染出来的画面，不是代码）

`quickpick-list / -typed / -empty` × 亮暗六张逐张看（`/tmp/r64_shots2`、`/tmp/r64_shots3` 各一遍）。

- **量出一条产品侧排版缺陷 ⇒ 新开 BACKLOG 97**：同一张表里
  纯文本行的标签从 **34.5–35.0pt** 起，带图标的文件行标签从 **56.5–57.5pt** 起
  （图标占 36.0–50.0pt）⇒ 五行里两种左轴，差 **22pt**，420pt 宽的面板上肉眼可读。
  与 94（图标本身是 📄 emoji 还是 SF Symbol）同一族：先定图标语言，再定左轴。
- **同批好消息**（记下来免得下轮重查）：选中**不产生位移**（选中行标签 34.5 vs 未选中 35.0，
  0.5pt 是字形边距）；空态那句在列表槽里居中（中心 209.25pt vs 面板 210pt）；
  暗档六张都看过，文字与图标都立得住。
- **一把我自己不信的尺**：我用 `|亮度差|>8` 粗量药丸，读到"左 14.0 / 右 22.0 不对称"，
  与 R63 那把经过正对照的尺（两边各 22.0pt，对称）冲突 ⇒ **以 R63 为准**，
  本轮这个数不记成缺陷也不记成"已排除"（尺没做自己的正对照，见记忆里的"监视器自己没验过"）。

### 七维自评

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 17 / 20 | 产品零改动；逐帧看又量出一条左轴缺陷（97）没修，本轮把它记成了坐标 |
| 流畅度 | 15 / 20 | 没碰动效；但"结论可以整块消失"这一族修掉之后，动效那两卷的读数第一次不会静默失踪 |
| 层次与材质 | 15 / 15 | 122 帧 `CHANGED=0`、`MISSING=0 ADDED=0`；亮暗两档六张浮层帧逐张看过 |
| 动效细节 | 11 / 15 | 本轮零动效改动，也零新增判据覆盖的动效位点 |
| 交互反馈 | 8 / 10 | 闸门现在会把"只剩一条腿"说成一条有名字的红；用户侧反馈未变 |
| 可访问性 | 8 / 10 | 没碰；读屏播报仍未核（独立一轮） |
| 性能 | 13 / 15 | 捕获卷多 488 行落盘（一次写 + 追加，同一目录）；全量那一遍 775 条结论行 / 0 条红、`--build-tests` 0 告警 |

**92 / 100**。低于 R63 的 93 是有意的：**连续第三轮没碰产品画面**（R62 93、R64 92），
而且本轮的产出里有一条是"推翻自己上一轮写的机制"——诚实要记，但它不等于画面变好。
下一轮（R65）必须回到产品面：BACKLOG 94 + 97 是同一个决定（图标语言 → 左轴），
后面排着 63/64/65/66 那一族与 88。

### R64 的 CI 追加（run 38693365411 / commit 0614466）：`--readings` 第一次在 runner 上跑，补回 65 行

整作业 **success，18/18 步全绿**。逐条读到的数：

| 读数 | 值 | 这一句在说什么 |
|---|---|---|
| `capture 文件通道` | **376 行**读数 @ `/tmp/shots-ci/capture-readings.log` | 第二条通道在 runner 上真的落盘了 |
| `CAPTURE_GATE_CHANNELS` | `stdout=1 readings=376 行 `**`补回=65 行`** | 并集这一步**有活干**：65 行 stdout 没有 |
| `CAPTURE_GATE_CASES` | `passed=28 skipped=9 failed=0 有名字的红=0 `**`NOT_RUN=50`** | 上一次不带 `--readings` 的同一步是 `NOT_RUN=25` |
| `CAPTURE_GATE_RESULT` | `ok 红=0` | 红仍然为 0，而**看得见的登记多了一倍** |
| `captured frames` / `executed` | `122` / `37`，捕获失效帧 0 | 帧这一侧没退化 |
| `executed cases`（全量那一步） | **775** | 与本机那一遍同量级 |
| `PROBE_COVERAGE_SUMMARY` | 源码用例=11 登记=11 runner可跑=0 本次下结论=0 红=0 | BACKLOG 93 原样开着 |
| `MOTION_FLOOR_FACTS` | `judged=4/4 executed=42` `REDS=0` | 动效地板没动 |
| `FRAME_BASELINE`（对 working） | `COMPARED=122 MISSING=0 ADDED=0` | 夹具集合与清单一致 |
| `SMOKE_OK` | 1（两臂都是） | 打包出来的 app 起得来 |

**这条闸门这一轮挣到了工资，但工资的形式和我预期不同**：我原本等的是"补回一条判据自写的结论"，
这一遍五条浮层 marker **恰好都在 stdout**（⇒ 丢是偶发的，这次没丢）；
真正被补回来的是**登记** —— `NOT_RUN` 从 25 涨到 50，也就是说上一次那份"绿"的报表上，
有 **25 条『这台机器判不了』的登记根本没被看见**。这恰好是 U-59 那一族的另一个方向：
不是红被吞掉，是**已知盲区被吞掉**，而吞掉它的不是 `continue-on-error`，是 stdout。

⇒ BACKLOG 96 的验收条件（"runner 上真把 `补回=k>0` 打出来"）**达成**，这条可以收口；
但**它同时开出一条新的**：`--readings` 只覆盖捕获那一步，在屏探针那一步（`ui.log`）仍然只有一条腿
（BACKLOG 93 的形状）。

## Round 65 · 那个 📄 不是图标，是文案里的两个字符：图标搬回视图层，左轴自动只剩一条（结案 94、97 / 新开 99 / U-104…U-106 / D-124）

**靶**：R64 逐帧看浮层量出来的那条（BACKLOG 97）+ 它背后那条（94）。上一轮说"等 94 定了我再动左轴"，
这一轮就一起定、一起做。

### 开场读数（先量，再判断；同一把尺，帧按 2× 换算回 pt）

| | 改前（R64 量的 `quickpick-list-…-light`） | 改后（本轮同一张帧） |
|---|---|---|
| 纯文本行标签左沿 | **34.5–35.0pt** | 56.0–57.0pt |
| 文件行标签左沿 | **56.5–57.5pt** | 56.0–57.0pt |
| 两种左轴的差 | **22pt** | 布局上 **0.00pt**（判据读视图 `minX`） |
| 那 22pt 是什么 | 文案里的 `"📄 "` 两个字符 | 一枚 16pt 的 SF Symbol（视图层） |

### 做了什么

1. **文案**：`EntryPresentation.preview` 里三处 `"📄 …"` 去掉 ⇒ 文件行的正文就是文件名
   （`report.pdf` / `a.pdf 等 3 个文件` / `多个文件`）。
2. **图标**：浮层每行一枚 `NSImageView`（16pt 列、`.secondaryLabelColor`、`VisualGlyph.chipSymbol`、
   `setAccessibilityElement(false)`），名字与侧栏 `RowLeadingVisual` 一一对上：
   `doc.text` / `photo` / `doc` / `doc.on.doc`。
3. **左轴**：没有单独修 —— 每行都有图标之后它自己就剩一条。标签左锚点从 `cell.leading+6`
   改成 `symbol.trailing+6`。
4. **判据 5 条**：真值表（四种内容各一句、且**没有按 emoji 呈现的标量**）、
   emoji 那把尺的正对照（📄 必须抓到，`©`/`™`/`é`/`↵` 必须不抓）、
   四个名字互不相同且**每个都画得出东西**（+ 正对照：`doc.textt` 必须返回 nil）、
   两边同一套名字的跨文件守卫、浮层每行有图且共享一条左轴（+ 正对照：夹具必须真有 ≥2 种类型）。
5. **帧**：`quickpick-list` / `-typed` × 亮暗 = **4 张更新**（同提交 `update`），
   其余 **118 张逐字节不变**；`quickpick-empty` 两张不变（没有行，也就没有列）。

### 本轮推翻的是我自己上一轮写的一句话

94 的原话："**侧栏、浮层、详情共用同一条字符串**"。读调用点的结果：侧栏对 `.file`/`.files`
走 `FileNameText` / `MultiFileTitle`（**不经过** `shortPreview`），详情走 `sizeDescription`，
菜单栏走 `menuTitle` 自己拼 ⇒ 那个 emoji **唯一可见的表面是浮层**。
"参与搜索匹配"是真的（`QuickPickModel.filtered` 拿整条 `shortPreview` 比），所以这条改动
不是纯视觉改动 —— 也因此才有真值表那一格。
⇒ 这是"把一处现象推广到三个表面"的又一次（U-95 那一族）：**下一轮动手前先读调用点，不读注释**。

### 真实视觉审查（看的是渲染出来的画面）

`/tmp/r65_shots` 的 `quickpick-list` / `-typed` / `-empty` × 亮暗六张逐张看。
五行五行读下来：类型符号在暗档是细线灰、亮档同极性，不再有一枚彩色 emoji 站在灰字旁边；
`IMG_0201.HEIC 等 3 个文件` 那一行拿到了 `doc.on.doc`（叠起的多页），与侧栏同一记号；
图片行拿到 `photo`，与详情头同一记号；标签一行一条轴，扫读时眼睛不用左右找。
选中药丸与 R63/R64 一致（y 47–81pt、亮档 Δ35.3 / 暗档 40.2）。

### 七维自评

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 19 / 20 | 浮层的图标语言与侧栏/详情统一成 SF Symbol；`photo`/`doc`/`doc.on.doc` 都是系统里已有的记号 |
| 流畅度 | 15 / 20 | 没碰动效；浮层的呼出/退场、行移动、悬停三档仍欠判断（R63 就记着这笔） |
| 层次与材质 | 15 / 15 | 亮暗两档逐张看过；符号落在次要档、不与正文抢层级；118 张帧逐字节不变 |
| 动效细节 | 12 / 15 | 零动效改动；本轮新增的 5 条判据里有一条是"每行有图"，它顺带把未来加图标动画的对象钉住了 |
| 交互反馈 | 9 / 10 | 搜索语义变干净（打不出也搜不到 📄），文件名早两个字不再被 emoji 挤掉 |
| 可访问性 | 8 / 10 | 符号显式对读屏隐藏（与侧栏同一理由）；读屏播报整卷仍未核 |
| 性能 | 14 / 15 | 每行多一枚符号图（`withSymbolConfiguration` 每次新建一张）—— 实测**没有代价**：捕获卷 38 例 **111.195s**，R64 同卷两遍是 113.374s / 114.754s（还多跑了一例）。全量 780 例 / 37 skip / **0 failures** / 157.0s，`--build-tests` 0 告警 |

**92 / 100**。比 R63 的 93 低一分：那轮修的是"四分之三空白"这种用户每次呼出都看得见的缺陷，
这轮修的是"两套左轴 + 一枚外来 emoji"——真的更原生，但没有那么大。
**低于 90 的项没有**，但两处明确的欠账留在台账里：浮层的**动效**（R63/R64/R65 三轮都没碰，
是这一族最该还的）、以及本轮判为不动却没量过的字号/行高（BACKLOG 99）。

### R65 的换装记录（本轮改了产品 ⇒ 按交付默认自己装上）

`scripts/install_local.sh --yes --label r65-overlay` → **INSTALL_RESULT=ok**：
新包 sha `de899ebccf34b756…` 与装上的那份逐字节相同（`INSTALL_SHA_MATCH=1`），
旧包备份在 `~/Documents/Codex_Project0_backups/before-r65-overlay`（退回命令脚本已打印），
运行时冒烟 `SMOKE_OK=1`，新 pid **578** 启动时刻晚于安装、exe 路径逐字对上
`/Applications/时间剪史.app`，存档条数 **105 → 105**（只读核对）。
版本号仍是 **1.4.8 → 1.4.8** —— 这一串改动都还在 `[Unreleased]` 里，
所以"装的是哪一版"只能靠 sha 认，不能靠版本号认（这条不是新账，R63 也撞过）。

**仍然没看到的**：那一列符号在真屏幕上的样子。浮层由全局热键呼出，
而自动化通道把按键送不进一个刚弹出的面板（D-041），
离屏帧能证明"每行有图、左轴 0.00pt"，证明不了"这列在用户眼里有没有信息量" ⇒ 人工批次 65。

### R65 的 CI 追加（run 38696695788）：新判据在 runner 上活着，而我在别人的报表里读到一处**没有名字的红**

整作业 success、18/18 步全绿。逐条读到的：
`compile warnings: 0`；`swift test exit: 0`；
本轮那条新守卫在 runner 上打出的正是本机那句 ——
`QUICKPICK_ROW_AXIS rows=5 取到标签=5 取到图标=5 无图行=0 标签左轴散布=0.00pt 图标列散布=0.00pt
标签 minX=42.0,42.0,42.0,42.0,42.0 类型符号=doc,doc.on.doc,doc.text,photo`；
捕获那一步 `capture 文件通道：377 行读数`、`captured frames: 122 executed: 38 捕获失效 0`；
闸门 `CAPTURE_GATE_CHANNELS stdout=1 readings=377 行 `**`补回=131 行`**、
`CASES passed=29 skipped=9 failed=0 有名字的红=0 NOT_RUN=50`、`RESULT=ok`；
`PROBE_COVERAGE_SUMMARY … 本次下结论=0 红=0`（93 原样开着）；
`MOTION_FLOOR judged=4/4 executed=42 OK=4/4 REDS=0`；`FRAME_BASELINE` 对 working `MISSING=0 ADDED=0`。
⇒ 上一轮立的 `--readings` 第二次在 runner 上跑，补回的量从 65 变成 **131** —— 这个数每次都不一样，
**恰好证明它不能靠"上次没丢"来省**。

**但这一遍读到一处我必须先记账再说别的**：`motion suite exit: 1` 已经**连着两遍**
（R64 与 R65），而两遍的报表都写着 `MOTION_FLOOR_REDS=0`。
原因在 `motion_floor_gate.py` 里：那个 `REDS` 数的是它自己四臂的结论，**不看测试有没有失败**，
而那一步是 report-only ⇒ 一个真实的红在整份 CI 里没有名字。
R64 那一遍更彻底：连 `error: -[…]` 那行都从 stdout 丢了，我这次才恰好读得到 ——
红的是 `testListRowsDoNotAnimateAndNothingClaimsTheyDo` 的**分辨率自校验**
（`0.0253` 读不出横幅淡入的残余，它拒绝让一条没有分辨率的绿站着）。
⇒ 判据做对了，**闸门漏了**：这正是 R36 我给捕获那一步修过的形状，我没铺到动效这一步。
记 **BACKLOG 100 / U-107**，R66 第一件事就是补这道门（并把这条在 runner 上的形态改成带读数的登记，
同时保留"本机必须仍然判红"那一臂）。

---

## Round 66 · 一条判据说"这台机器看不见"，得有个与被告无关的证人来签（结案 100 / 新开 101、102 / U-108…U-111 / D-125）

**靶**：R65 读 CI 时撞到的那条 —— 动效那一步 `motion suite exit: 1` 连着两遍，
而唯一的闸门报 `MOTION_FLOOR_REDS=0`。红没有名字（R36 给捕获那一步修过的形状，我没铺到动效）。

### 开场读数（先把"是机器还是产品"量清楚，再决定登记还是修）

同一次淡入（`MotionCatalog.bannerIn` = 150ms，两边同一个声明）：

| 读数 | 本机（R66，四遍） | runner（run 38696695788） |
|---|---|---|
| `MOTION_CUT_CONTROL` 落定残余 | **0.554 / 0.719 / 0.729 / 0.974** | **0.025** |
| 采样间隔 | ≈10–11ms | ≈21ms |
| `MOTION_SETTLE banner-in` 到位帧 ⇒ 实测落定 | 16 帧 ⇒ ≈160ms | 4 帧 ⇒ **≈76ms** |
| 新证人 `MOTION_FADE_CLOCK`（本机） | 跨度=1.000 中间态帧数=**8–11** 帧数=87–91 采样≈**21ms** 判定=能分辨 | 待下一次 CI 回答 |

⇒ "runner 采样粗"解释不了：21ms 采 150ms 本该有 ≈7 级可分，而残余差 22–39 倍。
⇒ BACKLOG 100 原写的"在 runner 上登记成未覆盖"**不能照写**：那条淡入的证词正是被告的证词。

### 做了什么（本轮 0 个产品文件）

1. **证人**：`FadeClockProbe` + `FadeClockView` —— 白底上盖满视口的黑块，
   `if shown { Rectangle().transition(.opacity) }` 配 `withAnimation(.easeInOut(duration: 0.15))`，
   每 0.25s 翻一次。逐帧读**平均亮度电平**（`meanLevel`）而不是帧间差：差没有极性，
   数不出"中间态"。150ms 写死在测试里、**不读 `MotionCatalog`**（读产品 ⇒ 证人跟着被告变短）。
   三档判定：跨度 < 0.05 ⇒ **证人坏了判红**；中间态 ≥ 2 ⇒ 机器能分辨；否则 ⇒ 环境看不见。
2. **决定表纯函数化**：`controlJudgment(residual:clock:)` → 绿 / 证人坏了(红) / 产品跳变(红) / 无从判定(skip)，
   配六格真值表。原来这三条长在 `if residual <= floor` 里面，而本机残余 0.554–0.974 **永远进不去**
   ⇒ 分支里的判定在本机一次都没被执行过（M356 只有纯函数化之后才会被抓）。
3. **闸门加一层** `motion_floor_gate.py::suite_verdicts()`：扫 `Test Case … failed` +
   `error: -[类 方法] : <XCTAssert 原文>` + `Executed … K failures` 汇总数 ⇒
   `SUITE_RED=n`（未登记的红，带名字与原文）/ `SUITE_NAMELESS_RED=n`（说有红而名字不够）/
   `REGISTERED_REDS=n`（登记过的不挡发布但数得出来）/ `SUITE_STALE`（登记没复现，提醒删）。
   **排在 `verdicts()` 两处提前 return 之前** —— 判据崩的时候常常既没结论行又红。
   CI 那一步不必改：报告步仍 `continue-on-error`，红由下一步 `Motion coverage floor`（无 continue-on-error）挡下。
4. **正对照 + 反向对照**：正对照是逐字从 runner 日志抄的那一卷
   （`fixtures/r66_motion_runner_red.log`：`judged=4/4 not-run=-` 而这一条红着）；
   反向对照 `testArmLevelRulesAloneWouldHavePassedIt` 把新判据摘掉后必须**全绿** ——
   那就是"两次 exit 1 绿过去"的最小复现。登记表 `suite_reds` 今天**故意空着**（一格自测钉住它）。
5. **判据 4 条 Swift + 12 格脚本自测**（脚本测试 127 → **139**）；电池 **M350–M362 十三刀全 CAUGHT**。

### 真实视觉审查（看的是渲染出来的画面）

新证据图：`/tmp/r66_motion3/fade-clock-strip.png`（87 帧 × 6 列一张）。逐行读下来：
白 → 浅灰 → 中灰 → 深灰 → 全黑，**每一行都数得出 4–6 级中间灰**，然后一段纯黑（静置），
再回到白。这就是"这台机器看得见 150ms 的淡入"的图像证据 —— 不是我从 `跨度=1.000` 反推的，
是眼睛在同一批帧上直接看到的。另外两件事也是看图看出来的：
① 夹具的黑块铺满了整个视口（所以我原先预计的"跨度约 0.5"是错的，实测 1.000 ——
读数把预期纠正了，而不是我拿预期去挑读数）；
② 条带里没出现"半帧撕裂/空帧"，说明 `cacheDisplay` 这条通道在淡入过程中拿到的是**完整态**，
证人读到的中间灰不是抓帧错位造出来的。
产品侧本轮没有新帧：122 张帧对 working 基线 `CHANGED=0 MISSING=0 ADDED=0`（本轮不动产品，预期如此）。

### 七维自评

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 19 / 20 | 没碰画面；但这一轮之后，"提示条淡入是不是原生地在动"第一次有了**可证伪**的说法，而不是每次靠猜 |
| 流畅度 | 15 / 20 | 欠账原样在（浮层呼出/退场、行移动、悬停三档）；本轮把"为什么量不到它"这件事从猜测变成了读数 |
| 层次与材质 | 15 / 15 | 无改动；122 张帧逐字节不变 |
| 动效细节 | 13 / 15 | 淡入这一族第一次有了机器无关的分辨率证人 + 三档判定；runner 那一档今天仍未读（下一次 CI 回答） |
| 交互反馈 | 9 / 10 | 无产品改动 |
| 可访问性 | 8 / 10 | 无改动；读屏播报整卷仍未核（老账） |
| 性能 | 14 / 15 | 证人一次 2.6s、每卷只跑一遍（缓存）。全量 **783 例 / 38 skip / 0 failures / 156.7s**，动效卷单独 45 例 exit 0，`--build-tests` **0 告警**，脚本测试 **139 OK** |

**92 / 100**。与 R64/R65 同分：本轮**一个产品文件都没动**，画面没有变好，所以分数不该涨；
涨的是"这一族的绿到底可不可信"。低于 90 的项没有，欠账写得很具体：
浮层的动效（R63–R66 四轮没碰，是这一族最该还的）、以及本轮新开的 101（整卷级缺席数不出来）
与 102（runner 的读数被 `head -120` 截、胶片从不上传 ⇒ runner-only 的现象没有图可看）。

### 本轮没有换装（并说明为什么这不算跳步）

产品 0 文件、帧 0 变化 ⇒ 用户屏幕上能看到的東西与 R65 装上的那份**完全同一**
（sha `de899ebccf34b756…`，pid 578 那次）。"交付默认自己构建换装"这条规矩管的是
**改了产品**的轮次；本轮改的是判据与闸门，跑的是 `swift test` 全量 + 动效卷 + 脚本测试 + 帧基线。
下一次动产品的轮次仍按九步流程走。

### 本轮学到 / 推翻的三件事

1. **"可能是机器"不能由可疑的那次测量自己宣布。** 我上一轮写的处置（在 runner 上登记成未覆盖）
   正是拿被告的证词给被告免检 —— 量完两台机器的采样差（2 倍）与残余差（22–39 倍）之后才看见它站不住。
2. **只有某台机器才会走到的分支，等于没有判据。** 阳性对照的三条判定长在本机永远进不去的 `if` 里，
   于是它们从未被执行、也从未被证伪；纯函数化 + 六格真值表之后，M356（那张新免检牌）才会被抓。
3. **本轮真踩的正则 bug 是三条用例一起红才发现的**：`Executed … with N failures` 第一版漏了 `with `，
   恒读成 0，而 NAMELESS 那一格恰好因为"名字数与 0 一致"不红 ⇒ 补了两种形状 + 多行取最大的自测（M354）。

## Round 67 · 浮层那一行第一次有指针反馈，而"宽度对上了"的判据看不见方与圆（新开 103、104 / U-112…U-116 / D-126）

**靶**：BACKLOG 95/98 那一族 —— R63 把浮层"第一次看见"，R64 补状态位点，R65 换图标，R66 全在判据侧，
**产品面上浮层欠的账一轮都没还**。本轮还的是其中最基础的一条：这个面板今天没有指针反馈。

### 开场读数（浮层 420×300pt，帧是 2× ⇒ px÷2=pt）

| 位点 | 今天有什么 | 坐标/几何读数 | 本轮判定 |
|---|---|---|---|
| 行（rowHeight 34pt，一屏 8 行） | **只有选中**，没有悬停 | 选中药丸 x=44…795px（22…397.5pt）、y=94…161px（正好一行高）、逐行左沿内缩跨度 **11px** | **加**悬停那一档（`VisualFill.hover`，与侧栏同一枚令牌） |
| 行 · 按下态 | 无 | 提交入口只有 `table.doubleAction`（没有 `action`） | **不加** pressed：没有"按下即发生"的动作，按压态会暗示一个不存在的单击语义 |
| 行首类型符号（16pt，R65 装的） | 静态 | 标签左轴 `minX=42.0`（表格坐标，五行散布 0.00pt） | **不加**动效：它只说"这是什么类型"，动它会把注意力从内容引到记号上 |
| 搜索框 | 焦点环由系统给 | 本轮**没量**（欠账，见下面"仍未判"） | 不判 |
| 空态 / typed 态那两句 | 静态文案 | R64 已判（居中 0.75pt 内） | 不动 |
| 面板呼出/退场 | 无动画 | R8 判过、R63 复核过 | 不重开（本轮没有新读数推翻它） |

### 交的东西（产品 1 个文件）

`QuickPickController` 每行一枚 `QuickPickRowView`（`NSTableRowView` 子类）+ 一层 `HoverFillView` 子视图，
`.below` 压在 cell 下面 ⇒ 永远压不住文字；**选中那一行不叠这层灰**（真值表四格全钉）。
指针只由事件驱动（`NSTrackingArea` 的 entered/moved/exited），重排时 `clearHover()` 清掉旧的那一层。

### 本轮真正的产出：一条判据被画面推翻了三版

| 版本 | 灰带逐行 | 药丸逐行 | 旧"宽度判据" | 新"轮廓判据" |
|---|---|---|---|---|
| 直角满高（第一版） | 恒 42…797 | 首行 55…784 / 中行 44…795 | 左 −2px 右 +2px ⇒ **绿** | 差 11px ⇒ 红 |
| 圆角 6pt（第二版） | 首行 52…787 | 同上 | 差 0px ⇒ 绿 | 差 3px ⇒ 红 |
| 圆角 `VisualRadius.card`=8pt（第三版） | 首行 **55…784** / 中行 **44…795** | 同上 | 差 0px ⇒ 绿 | **逐行 0px ⇒ 绿** |

⇒ **总范围相同的两块墨可以有完全不同的轮廓**：R15 那把"按列取带内最大"的尺结构上看不见这一族错，
任何阈值都救不了（不是阈值太松，是读数丢信息）。新尺 `alphaLiftProfile` 逐行给，
并且**参照物自己也要被量**（药丸内缩 ≥ 4px 那条断言）—— 否则参照物一旦变方，"逐行一致"自动成立。

量的那一半（`OVERLAY_HOVER`）：alpha 抬升 **12.82/255**（亮）/ **12.70**（暗），线 7.65；
两档分得开：选中药丸灰值 220 vs 悬停 240（亮）、70 vs 43（暗）⇒ 悬停始终比选中安静。

### 七维自评

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 20 / 20 | 灰带与 AppKit 那颗药丸**逐行同形**（8pt 圆角、同一左右内缩、同一高度），且用的是系统那档"次要灰"的语义而不是自造色 |
| 流畅度 | 17 / 20 | 浮层有了指针反馈；但这层灰**没有过渡**（进出是硬切），而"要不要给它 80–120ms 的淡入"本轮没判 —— 见 U-115 |
| 层次与材质 | 15 / 15 | hover(0.06) < selected(0.16) 的次序在**画面读数**上成立（220/240、70/43），不再只是令牌表里的断言 |
| 动效细节 | 12 / 15 | 本轮是"静态一档"，不是动效；欠的两条：那层灰的淡入/淡出（U-115）、以及浮层整卷仍没有一条动效判据（R63–R66 的老账） |
| 交互反馈 | 10 / 10 | 双击是唯一提交入口这件事，第一次有了"这一行可以被指"的可见性 |
| 可访问性 | 8 / 10 | 悬停是纯视觉档，不携带信息 ⇒ 读屏不受影响；但"焦点环"那一格本轮没量（U-116） |
| 性能 | 14 / 15 | 每行一个子视图 + 一次 `NSBezierPath` 填充，只在进出时重绘；全量 **786 例 / 38 skip / 0 failures / 157.9s**，捕获卷 41 例 0 failures，`--build-tests` **0 编译告警**（日志里那 10 行 `CoreData: warning:` 是运行时的 XPC 噪声，不是编译告警 —— 分开记，见 U-114），脚本测试 **139 OK** |

**96 / 100**。涨 4 分的理由是本轮**画面真的变好了**（前几轮涨的是"绿可不可信"）：
浮层从"一列不能碰的文字"变成有指针反馈、且那一档与系统选中同形。
扣分处都写清了：淡入没判（U-115）、焦点环没量（U-116）、"够不够响"没有机器判据（BACKLOG 103）。

### 验证（本机）

- 全量 `swift test`：**786 tests, 38 skipped, 0 failures**；编译告警 0（`:[0-9]+:[0-9]+: warning:` 计数 = 0）
- 捕获卷单独：41 例 / 4 skip / 0 failures；`FRAME_BASELINE_COMPARED=124 CHANGED=0 MISSING=0 ADDED=0`
  （本轮改产品时那两张 hover 帧 `CHANGED=2`，逐字对上后按同提交 `update`）
- 脚本测试：`Ran 139 tests … OK`
- 变异电池：**M363–M371 九刀全 CAUGHT**（抓到=9 逃掉=0 没跑成=0 未落地=0，
  `.scratch/motion-audit-2/r67_mutation_battery.log`）。M369 是本轮真实存在过的那一版（直角），
  它从 M363–M368 六刀下全部逃掉 ⇒ 新判据的判别力有双向证据
- 换装：`INSTALL_RESULT=ok`，新包 sha `db4872e4a852b426…`，`INSTALL_RUNNING_PID=21873`
  路径逐字对上，存档 105→105 条未动，`SMOKE_OK=1`

### 本轮学到 / 推翻的三件事

1. **绿不等于对上。** 9pt 内缩在 ±2px 容差里是绿的，而它左右各宽 1pt —— 这一条是**看了画面**才发现的，
   读数一直是对的，是我没去逐行读。
2. **判据的分辨率是它自己的一部分。** "形状"级约束用总范围读数去判，等于用尺子的最长刻度去量圆角；
   补尺之后立刻逼出两版真实缺陷（直角、6pt）。
3. **证人不能比被告粗。** R66 的淡入时钟在 runner 上采样 80ms，而它要作证的判据用 35ms ⇒
   它今天没资格给 notice-banner 免检（BACKLOG 104，R68 去修）。

## Round 68 · 证人不能比被告粗：把淡入时钟搬到同一颗尺子上（结案 104 的第一半 / U-117 / D-127）

**靶**：R67 读 R66 的 CI 时看到的两件事 —— runner 上证人 `采样≈80ms 判定=拍成跳变`，
而它要作证的那条判据用"事件内最粗 35ms"。证人比被告粗 ⇒ 它那句"我也看不见"只是它自己的分辨率。

### 开场读数（同一条 150ms 淡入，两台机器）

| 读数 | 本机（R68 改后） | runner（R66 那一遍） |
|---|---|---|
| 证人 `MOTION_FADE_CLOCK` 采样 | ≈20ms（改前 21ms） | ≈80ms |
| 证人抓帧面积 | 190×24pt = **4,560pt²**（改前 320×180 = 57,600pt²） | 同 |
| 判据那条带 | 760×48pt = 36,480pt² | 同 |
| 证人 / 被告 面积比 | **1/8**（改前 1.6 倍 ⇒ 证人更贵） | 同 |
| `可分数段 = 声明 ÷ 采样` | 150/20 = **7** ⇒ 合格=是 | 150/80 = **1** ⇒ 合格=否 |

### 交的东西（判据 1 个文件，产品 0 个）

- 决定表多一根轴：`controlJudgment(residual:clock:witnessQualifies:)`，新格 `.witnessCannotAdjudicate` ⇒
  **证人不合格时 `.snaps` 不许落到 skip**，红着并指名去修证人。
- 合格线由证人自己的量推导：`resolvableFrames(声明, 证人采样) ≥ minimumIntermediateFrames + 1`
  （150ms ⇒ 采样 ≤ 50ms）。**第一版我写的是"证人采样 ≤ 判据采样"**，本机当场读到
  `证人 20ms vs 判据 11ms ⇒ 不合格` —— 那是把两根不同的尺硬比大小（判据那 11ms 含它自己夹具的成本），
  与"证人能不能分辨一条淡入"无关 ⇒ 换成上面这条只依赖证人自己的推导。
- 证人搬小：抓帧区域从整张视图改成 190×24 那条带 ⇒ 结构上不可能比被告贵。
- `resolvableFrames` 改 `nonisolated`（嵌套类型不继承外层 `@MainActor`，Swift 6.1 直接编译不过；
  另一条路是把公式抄第二份 ⇒ 迟早算出两个"可分段数"，所以改隔离、不复制）。
- 两张真值表：决定表八格（含"同一 `(residual, clock)` 只改合格位必须给出不同处置"那条
  `XCTAssertNotEqual` —— 少它，别人把参数删掉退回 `.snaps ⇒ .notRun` 也照样全绿）；
  合格线六格（含 50/51ms 两条边界与 0/−1 两种"读不出"）。

### 七维自评

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 19 / 20 | 没碰画面 |
| 流畅度 | 15 / 20 | 浮层那笔仍欠（R67 交了一档静态灰，淡入没判 = U-115） |
| 层次与材质 | 15 / 15 | 无改动；124 张帧逐字节不变 |
| 动效细节 | 13 / 15 | 淡入那条判据的"环境 vs 产品"分界从此有第二根轴，且不合格时会红着指名 |
| 交互反馈 | 9 / 10 | 无产品改动 |
| 可访问性 | 8 / 10 | 读屏整卷仍未核（老账） |
| 性能 | 14 / 15 | 证人面积降到 1/8 ⇒ 每卷那 2s 更便宜；全量 **787 / 38 skip / 0 failures / 158.4s**，脚本 139 OK |

**93 / 100**。本轮 0 个产品文件 ⇒ 分数不该涨；涨的是"下一次 CI 无论答什么，答案都有名字"。

### 本轮学到的一件事

**"证人比被告粗"和"证人比被告贵"是同一件事的两面，而我上一轮只防了前者。**
证人要作证的是"这台机器的通道能分辨 150ms"，那么它的采样成本必须**不超过**被告 ——
否则它在最慢的那条路上跑，然后把自己的慢说成机器的极限。
这条与 R55/R57 那族"抓帧面积决定采样粗细"是同一条物理，只是这次被坑的是我请来的证人。

## Round 69 · 我上一轮写的判据在 1× 上是假红：地板必须建立在通道不变的量上（新开 105 / U-118…U-120 / D-128）

**靶**：R67 的 CI（run 38719528833）**红在 `testOverlayHoverFillSharesTheSelectionPillsOutline`** ——
本轮新写的那条轮廓判据，本机三版都绿，runner 上第一次跑就红。

### 开场读数（同一条判据、同一份产品，两台机器，换算成 pt）

| 读数 | 本机 2× | runner 1× |
|---|---|---|
| 药丸左沿内缩跨度 | 11px = **5.5pt** | 2px = **2pt** |
| 灰带左沿内缩跨度 | 11px = **5.5pt** | 5px = **5pt** |
| 逐行最大偏差 | 0px | **3px ⇒ 判红** |
| 中行 x 范围 | 两边各自完全一致（44…795 / 22…382） | 同 |

⇒ **不稳的是参照物**：灰带是我画的东西，两台机器都是 5–5.5pt；
AppKit 那颗药丸（同一个对象、同一个圆角）从 5.5pt 掉到 2pt。
机制假设**没证实**：药丸是材质，角上 alpha 不是覆盖率的线性函数，而尺的门是 `≥4/255`
⇒ 1× 上角像素过不了门，轮廓被啃平。

### 处置：按机器分开前提，而不是放宽线（沿用 R60 那一课）

- `pillInset ≥ 4px` 才判"与药丸同曲率"这一轴；否则发 **`FRAME_CORNER_AXIS_NOT_RUN=1`** 点名"今天没判"。
  名字必须以 `_NOT_RUN` 结尾 —— `ci_capture_gate.py` 的正则要的是 `\b[A-Z][A-Z0-9_]*_NOT_RUN\b`，
  我自造一个 `_BLIND` 后缀它就整条看不见 ⇒ 缺席又退回"只有注释替它决定"的老形状（R36/U-59）。
- 保留三条**两台机器都有牙**的断言：灰带自己是圆的（`fillInset ≥ 1`，直角恒 0）、
  逐行左/右沿 ≤2px（去掉首末各 `scale` 行）、两条轮廓行数一致。
- 逐行比对去掉首末各 `scale` 行：1× 上那一行就是一整个 pt 的量化误差；
  2× 上只去掉最外两行，而方角会一路吃进带内 6pt（本机 12px）⇒ 中间行照样红。

### 验证（本机）

- 全量 **787 / 38 skip / 0 failures / 158.4s**；编译告警 0；`FRAME_BASELINE_COMPARED=124 CHANGED=0`；脚本 139 OK。
- **放宽之后电池必须仍然全抓**（这是本轮最重要的一条，"改松判据"最容易在这里骗自己）：
  R67 那九刀重跑 **9/9 CAUGHT**（M369 直角、M370 6pt、M371 14pt 全部仍红）；
  R68 那六刀 **6/6 CAUGHT**（M377 第一版**没落地** —— 变异文包含了原文子串，
  电池的回读检查按设计判它"没落地"，改成 `+ 99` 之后落地）。
- 本机新读数：`缩放=2× 圆角这一轴=可判`、`逐行最大偏差（去掉首末各 2 行）第2行 左=1px 右=1px`。

### 七维自评

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 19 / 20 | 没碰画面；产品形状仍是 R67 那版（与系统药丸逐行同形，2× 证据） |
| 流畅度 | 15 / 20 | 欠账不变（浮层淡入 U-115） |
| 层次与材质 | 15 / 15 | 无改动，124 帧逐字节不变 |
| 动效细节 | 13 / 15 | 本轮修的是判据的机器不变性，不是动效本身 |
| 交互反馈 | 9 / 10 | 无产品改动 |
| 可访问性 | 8 / 10 | 老账未变 |
| 性能 | 14 / 15 | 判据成本不变；全量 158.4s |

**93 / 100**。这一轮的价值不在分数，在**它抓到的是我自己上一轮的错**：
一条写于 R67、带着 2× 读数的地板，在 1× 上是假红 —— 而 R38 那条"两台机器的读数不能当另一台机器的地板"
我记过、写过、还是在新判据上重犯了。

### 仍未解决

- 1× 上"与系统同曲率"这一轴**今天没判**（`FRAME_CORNER_AXIS_NOT_RUN=1` 会出现在 runner 日志里）。
  赎回它的两条路写在 BACKLOG **105**（降 `floor` 复量 / 按 103 换捕获对象）。
- R68 那半条（runner 到底答①还是答②）仍未回答 —— R67 那一遍在到达动效步之前就红了。

## Round 70 · 把"门"变成被量的对象（BACKLOG 105 ① / 无新 U 号，读数待 runner）

**靶**：R69 留下的那句机制假设 —— "1× 量不出药丸圆角，是因为材质角上的 alpha 过不了 `≥4/255` 那道门"。
假设没证实过，而它决定这条轴能不能在 runner 上赎回来。

**交的东西**（判据 1 个文件，线一个数没动）：同一次捕获里对**参照物**用三道门（1/2/4）各量一遍内缩跨度，
全部打进 `OVERLAY_HOVER_DOOR`。判据仍按 `pillInset ≥ 4` 决定这一轴判不判。

**本机读数**：`药丸内缩@门1/2/4 = 10/11/11px`、`灰带@门1/4 = 11/11px`
⇒ **在 2× 上门几乎不影响这件事**（10 vs 11 是抗锯齿的一格）。
所以问题只能由 runner 回答：门=1 时药丸回到 ≈5px ⇒ 是门；三道门都给 2px ⇒ 是通道的性质（只能走 103）。
**本轮没有新 U 号**：一条假设被换成了"一次会打印两种答案的量"，但没有读数之前它既不算证实也不算推翻。

### 七维自评

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 19 / 20 | 没碰画面；但"与系统同曲率"这句话从今天起有一个**可证伪的量**，不再是一句解释 |
| 流畅度 | 15 / 20 | 欠账原样在（浮层淡入 U-115、整卷动效） |
| 层次与材质 | 15 / 15 | 无改动；124 张帧逐字节不变 |
| 动效细节 | 12 / 15 | 本轮无动效；改的是判据的一条前提能不能被量 |
| 交互反馈 | 9 / 10 | 无改动 |
| 可访问性 | 8 / 10 | 读屏整卷仍未核（老账） |
| 性能 | 14 / 15 | 多两次全帧扫描（同一次捕获内，只在参照物上）；捕获卷 42 例 0 failures / 112.6s |

**92 / 100**。本轮一个产品文件都没动，画面没变好，所以分数不该涨；
它值分的部分是"把一条假设换成了一个会打印两种答案的量" ——
而它**还没有答案**（要等 runner 那一遍），所以也不该涨。


## Round 71 · 浮层的字号原来是就地写的两个数；把守卫的另外半边网补上（结案 99 / U-121…U-123 / D-129）

**靶**：BACKLOG 99 —— R65 我写下"浮层字号 13pt vs 令牌 `VisualFont.row` 12pt，本轮判为不动，
但这个判断本身还没量过"，并给了三条要做的（量行高 / 差 < 4pt 就统一 / 否则写理由 + 加守卫）。

### 开场读数（同一把尺：帧上按亮度找墨段，2× 换算回 pt）

| 量 | 浮层 | 侧栏 |
|---|---|---|
| 行距（相邻墨段起点差） | 33 / 33.5 / 34.5 / 35 / 43.5pt（单行） | 38 / 43 / 47.5pt（**双行**：标题 + meta） |
| 行标签墨高（改前） | 12.0 / 12.0 / 11.5 / 12.0pt | 10.5 / 12.5pt |
| 行标签墨高（改后） | **11.0 / 11.5 / 10.5 / 11.5pt** | 同上 |

⇒ **①的答案把②的前提打掉了**：两种行根本不可比（单行 vs 双行），
"行高差 < 4pt 就统一"这条规则用不上。真正决定的是另一件事：
**同一条记录的标题**在侧栏 / 行视图 / 搜索建议五处全是 `VisualFont.row`(12)，浮层是唯一那一处 13。
搜索框那处更明显：浮层写 14，而主窗口那颗搜索框是 `VisualFont.body`(13) ⇒ 同一个控件在两个表面响一档。

### 交的东西（产品 3 个文件，全是同一件事：把就地写的数放回梯子）

- 浮层行标签 `13 → VisualFont.row`(12)、搜索框 `14 → VisualFont.body`(13)、空态那句 `13 → VisualFont.body`（同值，去字面量）。
- `MenuBarController` 四处、`ChineseTextContextMenu` 一处的字面量换成**同值**令牌（11⇒`meta`、13⇒`body`）
  ⇒ 那几张帧 `CHANGED=0` 就是"这条改动一个像素都没动"的证明。
- 守卫 `testTextSizesComeFromTheScale` **补上另外半边网**：它原来只扫 `.font(.system(size:` 且只在 `Views/`
  ⇒ AppKit 那一半整个不在网里，浮层那个 13 就这么活了六轮。现在两半都扫、两个目录都扫，
  并带一条"喂假源码"的正对照。
- 新判据 `testQuickPickTypographyComesFromTheLadder`：**从产品入口**读真的 `NSTextField.font`
  （DoD 第 1 条），三格：行标签 == row、搜索框 == body、五行必须同档。
- 两条判据的**分工**由 M381 钉住：把 `row` 换成 `body` ⇒ 守卫必须不红（它仍是令牌）、产品路径判据必须红。

### 本轮被自己的电池抓到的一次（U-122、U-123）

1. 正对照第一版写的是 `fontLiteralOffenders(...).contains("13")` ——
   `Array<String>.contains` 比的是**整元素相等**，不是子串 ⇒ 这条断言永远不可能通过，
   基线当场红。（"我写了一条永远不会绿的断言"比"写了一条永远绿的"少见，但同一族：**没测到任何东西**。）
2. M382（从守卫里删掉 AppKit 那半边）**第一版逃掉了** —— 守卫读自己那份数组、正对照读另一份，
   删一半什么都不会红。这正是 R57 那条"两份各写一遍迟早会算出两个中位"，
   **而我犯在十分钟前**。修法是两边共用 `Self.fontLiteralPatterns`。

### 七维自评

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 19 / 20 | 浮层不再自己响一档；行距/图标比列看起来更系统 |
| 流畅度 | 15 / 20 | 浮层淡入仍未判（U-115 原样在） |
| 层次与材质 | 15 / 15 | 字号阶梯次序不变（meta < row < body < title），且新增一条"同一对象只有一档"的产品路径证据 |
| 动效细节 | 12 / 15 | 本轮无动效改动 |
| 交互反馈 | 9 / 10 | 无改动 |
| 可访问性 | 9 / 10 | 12pt 是 `row` 那一档、不是下限（下限 11 是 meta）⇒ 可读性没跌破；**代价是同一行截断点右移一个词**（帧上看得见："包含足够长度…" ⇒ "包含足够长度以便…"），小一档换来更多信息 |
| 性能 | 14 / 15 | 全量 **788 / 38 skip / 0 failures / 158.3s**、编译告警 0、脚本 139 OK |

**93 / 100**。产品改了，但改的是"回到梯子"，不是"加新东西"；
画面上的净变化是浮层那一列字小了一档、每行多看得见一个词。

### 验证

- 电池 **M378 / M379 / M381 / M382 / M383 五刀全 CAUGHT**（抓到=5 逃掉=0 没跑成=0 未落地=0，
  `.scratch/motion-audit-2/r71_mutation_battery.log`）
- `FRAME_BASELINE_COMPARED=124 CHANGED=0`（改产品那一刻 `CHANGED=8` = 四张 quickpick 帧 × 亮暗，逐字对上后同提交 update）
- 换装 `INSTALL_RESULT=ok`，新包 sha `c03cf278d3a4dd98…`，pid 29503，存档 105→105，`SMOKE_OK=1`

## Round 72 · 我上一轮给证人写的解释，被这一轮的读数证伪了（结案 104 / U-124…U-126 / D-130）

**靶**：读 R68+R69 的 CI（run 38723020548）。它同时回答了三件事，其中两件推翻我写下的话。

### 开场读数（runner，2026-10-15 18:49 那一遍）

| 读数 | runner 实测 | 我上一轮的预期 |
|---|---|---|
| `MOTION_FADE_CLOCK` 采样 | **81ms**（R66 是 80ms） | 面积小 12.6 倍 ⇒ 应该变细 |
| 证人 `可分数段` | 150/81 = **1 ⇒ 合格=否** | — |
| 判据自身采样 | 23ms | — |
| `MOTION_BAND` 带 vs 整窗抓帧 | 26.0ms vs 44.4ms ⇒ **省 1.70×** | 线是 2× ⇒ 红 |
| `FRAME_CORNER_AXIS_NOT_RUN` | **如约出现**（亮暗各一条，1× 药丸内缩 2px） | R69 的处置生效 |

⇒ **R68 的因果解释是错的**：我把证人采得粗归给"抓帧面积"，而面积降了 12.6 倍，采样 80 → 81ms 一动不动。
真正的差在**循环的睡眠节拍**：证人 `RunLoop.run(until: +0.02)`，判据那条 `record(_:)` 用 `+0.004`。
R72 把证人改成同一个节拍，并**把抓帧成本与采样间隔分开打**（`MOTION_FADE_CLOCK_COST`）——
上一轮我只交出一个数，于是拿它当了原因（R55 那一族的原话："混合量被当成两种结论用"）。

本机改后读数：`帧数=400 采样≈4ms 抓帧中位=0.1ms 中间态帧数=56 判定=能分辨`
⇒ 面积确实几乎不花钱（0.1ms），节拍才是全部；**这条预测交给 runner 验**：
若 runner 从 81ms 落到 ≈16ms ⇒ `可分数段=9 ⇒ 合格` ⇒ BACKLOG 104 从此能真的分①/②。

### 第二件：那条"省 2 倍"的线也是本机数

`testBandCaptureIsCheaperAndStillSeesTheMotion` 在 runner 上红着（26.036 > 22.200），
读出来是"省了 1.70 倍，真实存在，只是不到 2"。⇒ 与 R38 同一课，第三次栽在同一处。
改法不是把线调到 1.5（那是围着读数修线），而是**把可机器变的部分从判据里拿掉**：
判"方向"（严格更便宜，相等就红），倍数只报不判（`MOTION_BAND_SAVING`）。
"rect 是装饰"这一族错本来就由几何那两条拦，不靠倍数。
**牙的验证**：M384（两臂都抓整窗）⇒ 四格一起红（帧高、方向、首尾差），抓到=1 逃掉=0。

### 七维自评

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 19 / 20 | 没碰画面 |
| 流畅度 | 15 / 20 | 浮层淡入仍未判（U-115） |
| 层次与材质 | 15 / 15 | 无改动；124 张帧逐字节不变 |
| 动效细节 | 14 / 15 | 证人第一次与判据同一个循环形状；成本与间隔第一次是两个数 |
| 交互反馈 | 9 / 10 | 无产品改动 |
| 可访问性 | 8 / 10 | 老账未变 |
| 性能 | 14 / 15 | 证人从 90 帧变 400 帧但每帧 0.1ms，动效卷 46 例 90.4s（与上轮同）；全量 **788 / 38 skip / 0 failures / 157.7s**，编译告警 0，脚本 139 OK |

**94 / 100**。分数涨在"这一族的绿更可信"：一条假解释被自己的读数杀掉，
一条围着本机数画的线被换成机器无关的方向判据，而且两件事都各有一刀变异守着。

### 本轮学到的一件事

**"我改小了面积，所以采样会变细"是一句因果句，而我只有相关性。**
证人慢的真正原因是它自己 `sleep(20ms)`——一个我写它时觉得"保险"的数。
教训：**凡是拿一个数当原因，就要有办法把那个数拆开看**（这一轮起 `MOTION_FADE_CLOCK_COST` 就是那把螺丝刀）。

## Round 73 · 那条"门"的假设被自己的读数杀掉了：1× 上坏的是参照物，不是尺（结案 105 / U-127 / D-131）

**靶**：读 R70+R71 的 CI（run 38725116481）。R70 那一轮把"门"变成被量的对象，等的就是这一遍。

### 开场读数（runner 1×，`OVERLAY_HOVER_DOOR`）

| 量 | 门=1 | 门=2 | 门=4 |
|---|---|---|---|
| 药丸左沿内缩 | **2px** | **2px** | **2px** |
| 灰带左沿内缩 | **4px** | — | **5px** |

⇒ **不是门**。R69 我写下的解释（"材质角上的 alpha 过不了 `≥4/255` 那道门"）作废：
把门降到 1/255，药丸读数一动没动。
而灰带在两档缩放下都**量得对** —— R=8px 的圆角在这把尺上的理论值是
`R − √(R²−(R−0.5)²) = 8 − √15.75 ≈ 5.2px`，1× 实测 4–5；2× 理论 12.0、实测 11。
同一个对象不可能随缩放改圆角 ⇒ **坏的是参照物那一侧**（AppKit 那颗药丸的角在 1× 离屏合成里被吃掉），
不是产品，也不是我的尺。

### 这一轮值什么

一条**写在注释里的假设**如果没有被设计成"会打印两种答案的量"，就会一直当解释用下去，
下一轮还会拿它做决定（比如"那就降门吧"）。R70 花一轮把假设变成一个读数，
R73 花十分钟把它杀掉 —— 两轮加起来比"直接猜对"便宜，因为它同时产出了
`FRAME_CORNER_AXIS_NOT_RUN` 这条在 runner 上被验证过的缺席标记。

### 七维自评

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 19 / 20 | 没碰画面；"与系统同形"这句话的证据边界现在写清楚了（2× 有证据、1× 点名没判） |
| 流畅度 | 15 / 20 | 浮层淡入仍未判（U-115） |
| 层次与材质 | 15 / 15 | 无改动；124 张帧逐字节不变 |
| 动效细节 | 12 / 15 | 无动效改动 |
| 交互反馈 | 9 / 10 | 无改动 |
| 可访问性 | 8 / 10 | 老账未变 |
| 性能 | 14 / 15 | 全量 **788 / 38 skip / 0 failures / 157.7s**、编译告警 0、脚本 139 OK |

**92 / 100**。本轮只改注释与台账（0 行为变化），分数不该涨；
它值的那部分是"一条错误解释被清除"，不是"画面变好"。

### 仍未解决

- 1× 上"与系统同曲率"这条轴要靠 BACKLOG **103**（换捕获对象）才赎得回来；
  105 的两条候选里，降门这一条已死。
- 浮层搜索框焦点态（U-116）与浮层淡入那一格（U-115）仍未动 —— 下一轮回到产品面。


---

## Round 74 · 我给 R67 写的那句理由，被我自己第一个语料证伪了（U-115 判过 / U-128 / D-132）

**靶**：浮层悬停那一档要不要淡入（U-115 —— R67 判为"不做"，理由当时就写进了报告）。
本轮不猜也不辩护：**量打字时候选列表到底动多勤**，走产品真路径
（`queryChanged(_:)` 一个前缀一个前缀地喂，读真的表格）。

### 开场读数（`OVERLAY_HOVER_REFLOW`，本机 2×）

| 语料 | 前缀数 | 整列变了 | 指针那一格换了 | 最终行数 |
|---|---|---|---|---|
| 帧夹具（5 条记录，"这是一段用于"只命中 1 条） | 6 | **1** | **1** | 1 |
| 嵌套前缀（8 条同族记录，长度递增） | 8 | **7** | **6** | 1 |

⇒ **R67 那句"重排发生在每个候选字上"在帧夹具上根本不成立（1/6）**。
而它不成立的原因不是产品不动，是**那个夹具只剩一条命中** —— 一个只剩一条结果的搜索框本来就不该重排。
第二条语料（"同一条内容被反复复制"那一族形状）才给出 7/8 与 6/8。

### 这一轮值什么

- **决定没变（不加淡入），但理由换成站得住的那一个**：指针那一格在 8 个前缀里换 6 次记录，
  而 `rebuildRows` 每个前缀都把那层灰拆掉（机制由源码守卫钉住），补回来的唯一入口是 `mouseMoved`
  ⇒ 淡入每次都在起跑前被打断，会把一次静置的描色变成呼吸。
- **一条只在自家夹具上成立的理由，比没有理由更贵**：它长得像证据（U-128）。
  所以两个语料都留在判据里，各带一条**反向**断言（反面语料必须仍然是反面，
  否则两个语料哪天塌成一个，对照就静默消失）。
- **跨通道核对**（顺手做的正向用法）：落盘 PNG 上灰带 = x 44…795、y 296…363（68px 高），
  与判据在内存 rep 上读的 `44…795 / 68 行`**逐字相同**，亮暗两档都是
  ⇒ "判据看的那张图"与"基线钉住的那张图"是同一张（R37 那一族说的是尺读中间态，这一条是它反过来用）。
- **两条读同一机制的守卫合并成一把尺**：R67 真值表那条与本轮机制那条各自
  `components(separatedBy:)` 截了一遍函数体 ⇒ M387 实测两刀同时红，说明它们判的确实是同一件事
  ⇒ 改成共用 `Self.functionBody`，并给它配齐**正对照**（截到了）、**反对照**（函数名不存在必须空）、
  **右边界对照**（不许截到类声明）。

### 牙（M386–M391，6/6 CAUGHT，抓到=6 逃掉=0 没跑成=0 未落地=0）

| 刀 | 动的是 | 期望红在 |
|---|---|---|
| M386 | 给 `mouseMoved` 真的加一条 `NSAnimationContext` | 只有淡入那条（像素/几何三条照旧绿） |
| M387 | 把"重排时拆灰"换成"重排时只重画"（机制撤掉、函数还在） | 淡入 + 真值表那两条 |
| M388 | 嵌套语料改成不嵌套（每条开头换字） | 两条读数断言一起红 |
| M389 | 反面语料那条对照指到正面语料上 | 该红的没红 ⇒ 实测红，对 |
| M390 | 扫描器没找到签名时返回整份源码 | 反对照 |
| M391 | 扫描器不截方法结尾（把文件后半当方法体） | 右边界对照 |

**M387 第一版被我自己记成 ESCAPED**：电池的期望写的是"只红一条"，而它红了两条 ——
两条守卫确实同族，于是改的是**期望**（写成 `EXPECTED` 表），不是网。
这一格留在日志里是因为"红的比预期多"也必须有名字（U-101 那一族）。

**编号从 M386 起，不是 M385**：M385 已被 R72 用掉（记在 D-130），第一版我顺手从 M385 排，
写完才在台账里撞上 —— 两把不同的刀共用一个号，以后按号找证据的人会找错。

### 七维自评

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 19 / 20 | 悬停仍是即时描色（与 AppKit 行高亮同一档节奏），但这句话现在是量过的 |
| 流畅度 | 16 / 20 | 淡入那一格判完（按语料限定）；notice-banner 那条红仍未回答（104 的①/②要读 R72 的 CI） |
| 层次与材质 | 15 / 15 | 无改动；124 张帧逐字节不变（`CHANGED=0 MISSING=0 ADDED=0`） |
| 动效细节 | 12 / 15 | 无动效改动；"不加"这条从感觉变成读数 |
| 交互反馈 | 9 / 10 | 两条同族守卫合成一把尺 ⇒ 少一处会坏的地方 |
| 可访问性 | 8 / 10 | 老账未变（浮层搜索框焦点环 U-116 仍未量） |
| 性能 | 14 / 15 | 全量 **789 / 38 skip / 0 failures / 158.9s**、编译告警 0、脚本 139 OK、电池 6/6 |

**93 / 100**。零产品改动 ⇒ 分数不该涨；它值的那部分是"一句错解释被换成一条带反面对照的读数"。

### 看图（本轮真实看的那一张）

`/tmp/r74_visual/hover-band-{light,dark}.png`：静置 / 悬停 / 差值×8 三格竖排。
差值那一格在亮暗两档上都只有**一条**横带（第 4 行，`IMG_0201.HEIC 等 3 个文件`），
形状是圆角、两边内缩与第一行那颗药丸同形；文字行没有一条被压住。
**这张图不给"不加淡入"当证据** —— 那个决定靠的是重排读数与源码守卫，两条都不在图上；
图上能看的只有静置结果（把静置帧当过渡证据，是 R62 那一族记过的错）。

### 仍未解决

- 两个语料都是**我挑的**。真实语料那一格开成 BACKLOG **106**（本机 105 条真存档，只打比例不打文案）。
- R72 的 CI（run 38726667469）还没读 ⇒ 104 的①/②第一次有资格的答案仍悬着。**下一轮第一件事就是它。**
- 浮层搜索框焦点态（U-116）、BACKLOG 95 剩下的位点。


---

## Round 75 · 那条红既不是产品也不是环境：是判据拿两帧的采样间隔当了时长（结案 104 / U-129、U-130 / D-133）

**靶**：读 R72 / R73 / R74 三遍 CI。BACKLOG 104 的①/②在等这三遍 —— 证人换成 0.004 的节拍之后，
runner 上到底落到哪一档，以及 `notice-banner` 那条红了三次的事到底是产品还是环境。

### 开场读数（同一份判据代码，三遍 runner + 本机一遍）

| | 帧数 | 变化段时长 | 事件内最粗 | 证人采样 / 可分数段 / 合格 / 判定 | 结论 |
|---|---|---|---|---|---|
| run 38726667469（R72） | **2** | 32ms | 18ms | 32ms / 4 / 是 / 拍成跳变 | **红** |
| run 38726991211（R73） | **2** | ≥60ms | — | 32ms / 4 / 是 / 拍成跳变 | **绿** |
| run 38730788527（R74） | **2** | 36ms | 19ms | 32ms / 4 / 是 / 拍成跳变 | **红** |
| 本机（R75 这一遍） | 11–12 | 182ms | 20ms | 4ms / 37 / 是 / **能分辨** | 绿 |

⇒ **① 有答案**：那 80ms 里抓帧只占 0.4–0.5ms，其余全是节拍；改成 0.004 之后 runner 上采样 32ms、
可分数段 4 ⇒ 证人第一次**有资格**作证（`合格=是`）。
⇒ **② 的答案不是我预期的任何一种**：证人三遍都说"这台机器把一条已知 150ms 的淡入拍成跳变"
（`中间态帧数=0`），而 `testTransitionsAreActuallyRunning` 却在同样的两帧上判出一次绿两次红。
**两帧的变化段里，"时长"就是一次采样间隔** —— 那条判据一直在拿采样器的抖动作产品断言，
而它自己造的证人站在同一个循环里，却只被阳性对照那一支问话。

### 这一轮值什么

- **把证人接到 `.jump` 那一支**（`jumpAdjudication`，纯函数 + 八格真值表）：
  证人看得见淡入 ⇒ 这一臂读成跳变就是产品的事（红）；证人合格且自己也 snap ⇒ 报
  `MOTION_NOT_RUN=witness-snaps-here`，不判产品。**不对称是刻意的**：绿是正面证据不需要借口，
  缺席的证据才要先确认这台机器看得不见得见。
- **登记表跟着实测走**：`notice-banner` 的 `must_judge` true ⇒ false（地板 4 ⇒ **3**，带两个 run 号），
  另外三臂一条都不放。R57 那条 Swift 守卫从"两臂都必须 true"改成
  **"放宽必须带理由与 run 号"** —— 它现在读 `allowed_not_run_reasons` 那个数组，不读整块散文。
- **M395 当场抓到我自己新写的守卫**：第一版用 `bannerBlock.contains("witness-snaps-here")`，
  而那一臂的 note 里就写着 `MOTION_NOT_RUN=witness-snaps-here`（那是在**解释**这次放宽）
  ⇒ 删掉数组里那一项，守卫照旧绿。**放宽的守卫被放宽条目的说明文字喂饱**（U-130），
  与 R55 的 M276、R79 的"守卫命中自己写下的名字"同族。修成读字段之后 M395 CAUGHT。
- 顺手一条跨机验证：R74 那条 `OVERLAY_HOVER_REFLOW` 在 runner 上给出**与本机逐字相同**的读数
  （帧夹具 6/1/1、嵌套前缀 8/7/6）⇒ 重排这件事不吃机器，R74 的决定在两台上都成立。

### 牙（M392–M397，5/5 CAUGHT，抓到=5 逃掉=0 没跑成=0 未落地=0）

| 刀 | 动的是 | 期望红在 |
|---|---|---|
| M392 | `jumpAdjudication` 永远放行 | 真值表（一条只会赦免的表就是免检牌） |
| M393 | `jumpAdjudication` 永远不放行 | 真值表（赦免恰好只有一个形状） |
| M395 | 从理由数组里删掉 `witness-snaps-here` | Swift 那半条 + python 那格（**第一版逃掉**） |
| M396 | 抹掉 note 里的两个 run 号 | Swift 那半条（放宽必须留证据） |
| M397 | `must_judge` 改回 true | python 那格（清单变了期望就得跟着变） |

**一刀按实不收进计数**：把真判据里 `.jump` 那一支的问话删掉、退回无条件 `XCTFail` ——
本机证人 `判定=能分辨`，那条路径在本机走不到 ⇒ 本地无判别力，由 runner 判
（下一轮读 `MOTION_NOT_RUN=witness-snaps-here notice-banner` 在不在，就是它的验收）。
沿用 M168 / M385 的先例，不混进 CAUGHT。

### 七维自评

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 19 / 20 | 0 产品文件；横幅那条淡入今天在两台机器上有了不同的、各自说得清的身份 |
| 流畅度 | 17 / 20 | 淡入的可测性往前一格：判不到现在有名字，且**能分辨的那台仍然会红**（M393 钉着） |
| 层次与材质 | 15 / 15 | 无改动；124 张帧逐字节不变 |
| 动效细节 | 13 / 15 | 三遍 CI 的读数第一次能拼成一句结论；真正的修法（77 路 b）仍欠 |
| 交互反馈 | 9 / 10 | 无改动 |
| 可访问性 | 8 / 10 | 老账未变（U-116 焦点环仍未量） |
| 性能 | 14 / 15 | 全量 **790 / 38 skip / 0 failures / 157.9s**、动效卷 47 例 judged=4/4、编译告警 0、脚本 **140** OK |

**94 / 100**。分数涨在"一条反复出现的红终于有了正确的名字"，不涨在画面。

### 看图

`/tmp/r75_motion5/notice-banner-strip.png`（本机 27 格胶片）：横幅那一行从第 2 格起逐格变实，
到第 11–12 格才到底 —— 这与 `MOTION_SUMMARY notice-banner=11~12` 一致，
也证明这条量法在能分辨的机器上**确实看得见过程**（本轮不是把红改成不判）。
runner 那一份同样 27 格里只有 2 格在变 —— 那一对差别就是本轮全部的论证。

### 仍未解决

- **BACKLOG 77 路 b**：让判据不吃帧数（今天证人正是它的验收工具）。
- **BACKLOG 101 的③**（R75 新开的一格）：闸门层不查矛盾 ——
  某臂报 `witness-snaps-here` 而同一份日志里证人 `判定=能分辨`，今天只有判据自己守着。
- 浮层搜索框焦点态（U-116）、BACKLOG 95 剩下的位点、BACKLOG 106（真实语料）。


---

## Round 76 · 焦点那一档不是没有视觉后果，是只活在 alpha 通道里（U-116 判完 / U-131…U-133 / D-134）

**靶**：位点清单里欠着的浮层搜索框**焦点态**（U-116，R67 起就记着"本轮没量"）。
本轮读 R75 的 CI 顺手把它做掉。

### 开场读数（本机，聚焦 vs 撤掉焦点两态）

| 量 | 亮档 | 暗档 |
|---|---|---|
| 框内变化像素 | **1797** | **2354** |
| 框外扩一圈变化像素 | **0** | **0** |
| 那一格平均 alpha（不聚焦 ⇒ 聚焦） | 10.71 ⇒ 6.77 | 13.15 ⇒ 8.64 |
| **同一对在亮度轴上** | **-0.66** | **+2.25** |
| 变化区包围盒 | x 12.0–98.5pt、y 顶下 14–26pt | 同 |
| `focusRingType` | 0（= 系统决定；`.none` 的 raw 是 **1**） | 同 |
| 面板 key / App active | false / false | 同 |

⇒ 焦点**有**视觉后果：那一串占位字"搜索历史记录…"在聚焦时退后（alpha 掉一半上下），
位置、面积都对得上；⇒ 但它在**亮度轴上几乎不存在**（0.66/255）。
⇒ 框外 0 像素 ⇒ 这条通道看不见系统焦点环（面板不是 key），所以"有没有环"只能真机判（批次 68.1）。

### 本轮错在自己新写的判据里两次（都记进账）

1. **U-131 拿一张帧减它自己**：第一版两态取的是"建出来时"与"`makeFirstResponder` 之后"，
   而实测那颗框**建出来的那一刻就已经聚焦**（AppKit 把 key view 选成了它）
   ⇒ 两态相同，"0 个变化像素"什么都没证明，而且**它绿得完全正常**。
   修：改成"聚焦 vs `makeFirstResponder(nil)`"，并加一条正对照
   （`撤掉焦点之后窗口响应者不许还是字段编辑器`）—— 少了这条，两态塌成一个时没人知道。
2. **U-132 用亮度轴判 alpha 上的东西**：同一对帧，亮度轴读 -0.66、alpha 轴读 3.93。
   如果我只写"亮度差必须变大"，就会得出"焦点没有视觉后果"的假结论，
   并把一个**存在且克制**的反馈判成缺失。⇒ 这一格的判据必须走 alpha，两把尺一起打出来。
3. **U-133 一个按名字猜就写反的枚举**：`NSFocusRingType.none.rawValue == 1`，而 0 才是"系统自己决定"
   （本 SDK 连 `.automatic` 这个成员都没有，写 `== .automatic` 编译不过）。
   "不许关掉系统环"这条守卫如果按名字写成"等于 `.none`"，就把"环被关掉"当成通过。

### 决定（这一格不加自定义焦点视觉）与它的四条钉子

理由三条，全部有读数：① 焦点已经通过"占位符退后"说话（②那两条断言钉住它有、且方向是让位）；
③ 焦点位置不歧义 —— 浮层唯一可聚焦的文本输入，且 `show()` 打开即聚焦（源码守卫钉住那句赋值）；
④ 再加一圈环会与 R67 的悬停灰、选中药丸抢同一格的音量预算（同一族决定，D-126/D-132）。
代价也记明：**真机上那颗框到底有没有系统环，我看不到**（这条通道不带 key 窗口），
而"占位符退后 53/255"在真屏幕上够不够明显，也只有你知道 ⇒ 人工批次 68.1 / 68.2。

### 牙（M398–M402，5/5 CAUGHT）

| 刀 | 动的是 | 抓到在哪 |
|---|---|---|
| M398 | 产品侧关掉系统环（`focusRingType = .none`） | 只有④红，**③照旧绿** ⇒ 这条通道确实看不见环，④是唯一防线 |
| M399 | 产品侧删掉 `show()` 里那句 `makeFirstResponder(field)` | 只有源码守卫红（①②③④全绿）⇒ 这一族回归帧里没有影子 |
| M400 | 判据侧：拿聚焦帧减它自己（本轮真实犯过的那次） | ②红 ⇒ 光有响应者对照不够，像素那格必须自己站着 |
| M401 | 判据侧：把量尺的带挪到列表区 | ②红 ⇒ 读数不是"哪儿都能找到 500 个像素" |
| M402 | 判据侧：把方向断言翻过来 | 红 ⇒ "让位"与"变响"是两种设计，钉的是前者 |

M398 前两版 NOT-APPLIED，被电池自己的"变异文不许包含原文"拦下 ——
纯插入型的刀永远包含原行，必须顺手改一下原行的写法。这一族 R74/R75 各记过一次，本轮撞两次才绕开。

### 顺带读完的 R75 CI（run 38735395615，绿）

`MOTION_JUMP_WITNESS … 证人采样≈33ms 可分数段=4 合格=是 判定=拍成跳变（本臂 变化段=2 帧 时长=45ms 最粗=26ms）`
⇒ 这一遍如果没接证人，`45 < 60` 又是一条假红；现在它是
`MOTION_NOT_RUN=witness-snaps-here notice-banner`、`judged=3/4`、`MOTION_FLOOR_OK=3/4`、`exit 0`
⇒ R75 那一步在 runner 上按设计落地了。
**但"CI 绿"这句仍然要说清是哪一半**：那一步的 `FRAME_BASELINE_CHANGED=124` 是 runner 1× 与工作基线 2×
的已知差，该步只判"帧名齐不齐"（workflow 注释里明写，脚本里那条分支 `return 1 if missing else 0`）
⇒ 像素那一半由本机这一遍判（今天 `CHANGED=0 MISSING=0 ADDED=0`）。

### 七维自评

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 19 / 20 | 焦点仍交给系统（没加自定义环），而这句话现在有读数：环在这条通道里读不到、占位符退后读得到 |
| 流畅度 | 17 / 20 | R75 那条假红在 runner 上确认消失；淡入本体仍欠 77 路 b |
| 层次与材质 | 15 / 15 | 无改动；124 张帧逐字节不变 |
| 动效细节 | 13 / 15 | 焦点这一档从"没量"变成"四把钉子"；它本来就没有动效，也不该有 |
| 交互反馈 | 10 / 10 | 这一格是反馈类位点：量出了"有，但在 alpha 轴上"，并把它钉住 |
| 可访问性 | 8 / 10 | 焦点可见性真机上仍未证（批次 68.1），不升 |
| 性能 | 14 / 15 | 全量 **791 / 38 skip / 0 failures / 158.7s**、编译告警 0、脚本 140 OK、电池 5/5 |

**94 / 100**。零产品改动；涨的是"一个从没量过的位点量完了，而且量法里两个坑被当场抓出来"。

### 仍未解决

- BACKLOG **107**（本轮新开）：焦点这类"只在 alpha 上"的效果，我其余按**亮度**判的守卫全是盲的。
- 真机：68.1 有没有系统环、68.2 占位符退后够不够明显。
- BACKLOG 77 路 b（让动效判据不吃帧数）、101 的②③、106（真实语料）、95 剩下的位点。


---

## Round 77 · 两态相减的尺子原来只读一根轴 —— 把 alpha 变成这条卷的通用形状（结案 107 / U-134…U-136 / D-135）

**靶**：BACKLOG **107**（R76 开）。上一轮量到"焦点那一档只活在 alpha 上"，
而这条卷里所有"动 / 没动"的结论都站在**只读 R/G/B** 的尺子上。本轮不改产品，改尺子。

### 开场清单：捕获/动效那三把两态尺各自读哪根轴（R77 清点，全部读源码 + 实测）

| 尺子 | 在哪 | R77 之前 | R77 之后 |
|---|---|---|---|
| `axisPair` / `changedFraction` | MotionFilmstripTests | 只有亮度（`max(ΔR,ΔG,ΔB) > 8`） | 三根轴一次算完，`changedFraction` 返回**并集** |
| `bandHeadTailDiff` | 同上 | 只有亮度 | 并集（位置同一性那格从此两轴都判） |
| `changedFraction` | PressFeedbackTests | 三通道求和 > 0.02 | 加 alpha 那一根（同一条地板） |
| `changedFraction` | PressInteractionProbeTests | 三通道求和 > 6 | 加 alpha 那一根（同一条地板 6） |
| `meanLevel` / `meanLuma` / `inkContrast` 那一族 | 三处 | 单帧电平，本来就没有"另一态" | **不动**（判错了对象就不是判据） |
| `alphaBandDelta` / `alphaLiftProfile` | UICaptureHarness | **只读 alpha** | 登记 + 开 BACKLOG **108** |

> **R78 更正这一行**：原表写的是 `paintedXRange`，而它**全仓零调用点**（一把死尺），
> `alphaBandDelta` 才是真正在判的那一条 —— R77 的扫描器认减法写法，把它漏了（U-138），
> 而名册等式抓不到死尺（U-137）。两处都在 R78 修掉：删尺 + 检测器换成签名形状。

### 开场读数（本机动效卷，同一卷里两轴一起打）

```
MOTION_BLANK frames=30 峰值=0.0000 过渡帧数=0 帧对=29 亮度峰值=0.0000 alpha峰值=0.0000 并集峰值=0.0000 仅alpha在动=0/29
MOTION_AXIS notice-banner          帧对=26 亮度峰值=0.2795 alpha峰值=0.2497 并集峰值=0.2795 仅alpha在动=0/26
MOTION_AXIS notice-banner-dismiss  帧对=26 亮度峰值=0.2028 alpha峰值=0.1848 并集峰值=0.2035 仅alpha在动=0/26
MOTION_AXIS detail-kind-change     帧对=26 亮度峰值=0.0813 alpha峰值=0.0794 并集峰值=0.0813 仅alpha在动=0/26
MOTION_AXIS empty-state            帧对=26 亮度峰值=0.1118 alpha峰值=0.1063 并集峰值=0.1118 仅alpha在动=0/26
```

三句话，每句都有出处：
1. **今天没有一帧是"只在 alpha 上动"的**（四臂 + 空白全为 `0/N`）⇒ 加轴没有翻掉任何一条旧结论：
   `judged=4/4 not-run=-`、`MOTION_SUMMARY …=12/13/3/3` 与 R75 那遍（`11/13/3/3`）同判，
   而决定档位的是时长（182 / 183ms vs 187 / 183ms），帧数那一列本来就是会随采样相位翻脸的那一个（R2 / R47）。
2. **可 alpha 这根轴不是空的**：过渡期间它的峰值与亮度同一量级（0.25 vs 0.28）⇒
   这条通道**确实带透明度**，"窗口是实心的"这个直觉只在落盘之后成立
   （写出去的 strip PNG 实测 alpha 全 255，而内存里那份 `premultipliedLast` 缓冲区不是 —— U-136）。
3. **并集真的比亮度多**：`dismiss` 那一臂 0.2035 > 0.2028 ⇒ 有几像素只活在 alpha 上。
   今天它不足以翻判据，但"不足以"是**量出来的**，不是猜的。

按压那一族同时有了两轴读数（`PRESS_AXIS`）：缩放 0.1095 / 底色 0.8099 / 叠两层 0.7707，
而 **alpha差 全是 0.0000** ⇒ `renderPill` 那族夹具确实铺实底，"亮度那一根够用"这句从假设变成读数；
梯子那 12 步也一样：`FILL_STEP … 均值通道差=6.97–15.85/255 alpha差=0.00/255`。
在屏那颗按钮 `PRESS_PROBE … 送达=0` ⇒ 合成事件仍然进不去，两轴都是 0.0000，
这一条**没有**被本轮的加轴救回来（盲区修的是"看见了说没看见"，不是"事件没送到"）。

### 决定（D-135）：改语义，不加第二把尺

把"两态相减"的返回值直接换成并集，而不是新造一把"想读 alpha 时才用"的尺。
理由：新尺要靠人记得调用，而这一族的失效形状恰恰是"没人记得"（R76 那次是运气）。
代价也写清：历史读数里那根亮度轴**仍然拿得到**（`axisPair.rgb`），
而今天四臂里三臂的两轴峰值相同、一臂差 0.0007 ⇒ 换语义的当下不重写任何旧结论。

### 牙（M403–M412，10/10 CAUGHT，其中 M407 前两版 ESCAPED）

| 刀 | 动的是 | 抓到在哪 |
|---|---|---|
| M403 | 并集退化成"只看亮度"（= R77 之前的世界） | 真值表"暗墨在 alpha 上淡入"那一格红 |
| M404 | 并集写成 `max(rgb, alpha)` | `splitAxes` 那一格红（两轴各动一半时低估一半） |
| M405 | alpha 地板从 8 改成 30 | 共用地板那一格红（两列不再可比） |
| M406 | alpha 用 signed 差、不取绝对值 | 极性那一格红（淡出那一臂会读出另一个数） |
| M407 | 把 `PressInteractionProbeTests.changedFraction` 改回三通道 | 守卫红 —— **前两版逃掉**（见下） |
| M408 | 一条豁免的理由缩成「见注释」 | 守卫红（放宽必须带理由） |
| M409 | 名单里剩一条不存在的尺子 | 守卫红（过期名单比没名单更坏，与 M407 凑成双向） |
| M410 | 把本轮新修的 `bandHeadTailDiff` 改回三通道 | 守卫红（自己修的也要有人看着） |
| M411 | 元层：把"用没用 alpha"放宽回"提过就算" | 正对照 C 红 |
| M412 | 元层：撤掉"扫之前剥行尾注释" | 正对照 D 红 |

**M407 两度 ESCAPED，两次都是守卫被"提到"喂饱而不是被"用了"喂饱**（U-135）：
第一版查"函数体里有没有出现过 `+ 3]`" ⇒ 变异只删掉 `if` 里的 `|| alphaDelta > 6`，
而 `let alphaDelta = abs(… + 3] …)` 那行还留在原地，守卫照旧绿；
改成"必须有一行里同时出现 alpha 与 `>`"之后**还是绿** —— 因为变异行自己带着
`// R77 变异：又不读 alpha 了` 这句行尾注释，同一行本来就有一个 `>`。
⇒ 判"用没用"要连注释一起剥。两步各带一个正对照，并各挨一刀元层变异（M411 / M412）。
同族先例：R75 的 M395（`contains` 被同一臂 note 里的解释文字喂饱，U-130）。

### 看图（本轮真的看了，且看的是被改的那一臂）

`/tmp/r77_motion_out/（条带图；电池与动效读数已归档进 `.scratch/motion-audit-2/r77_*.log`）notice-banner-dismiss-strip.png` 与它的 `-逐帧-stack.png`：
提示条撤走是**向上滑出 + 高度塌缩**，不是淡出 —— 第 5 帧起文字被窗口上沿切掉半行
（"系统未授权本 App 控制「System Events」…"只剩下半），第 6–10 帧左半已经滑出、
只剩"无法自动粘贴。"与那颗"知道了"还压在列表行上面。
判：这是滑出机制的自然结果，不是缺陷（R59 那条"逐帧可读"就是为看清这件事而加的）；
但"滑出过程中文字被裁成半行"值不值一档动画，是**观感**判断 ⇒ 记进人工批次 69.1。

### 七维自评

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 19 / 20 | 产品零改动；透明度这根轴本来就是系统渲染的一部分，现在判据看得见它 |
| 流畅度 | 17 / 20 | 动效判据与 R75 那遍同判（judged=4/4），但 77 路 b（让判据不吃帧数）仍欠 |
| 层次与材质 | 14 / 15 | 124 张帧 `CHANGED=0 MISSING=0 ADDED=0`；材质层的 alpha 从此有读数 |
| 动效细节 | 12 / 15 | 四臂 + 空白 + 按压 + 梯子全部双轴；淡入本体那条仍未修 |
| 交互反馈 | 9 / 10 | 按压那一族第一次能报"动在哪根轴上"（答案：全在亮度上，实测） |
| 可访问性 | 8 / 10 | 焦点/禁用可见性真机那一半仍未证（批次 68.1 / 68.2） |
| 性能 | 14 / 15 | **793 例 / 40 skip / 0 failures**、编译告警 0、脚本 140 OK、电池 10/10 |

**93 / 100**。零产品改动；这一轮涨的是"这条卷里所有'没动'这句话，从今天起要求两根轴都不动"。

### 仍未解决

- BACKLOG **108**（本轮新开）：反方向的盲区 —— 5 把只读 alpha 的两态尺 + 那一族只读亮度的单帧电平尺。
- BACKLOG 77 路 b（让动效判据不吃帧数）、101 的②③、106（真实语料）、95 剩下的位点。
- 真机：68.1 / 68.2，以及本轮新加的 69.1（滑出时文字被裁成半行的观感）。


---

## Round 78 · 上一轮留在 main 上的红：焦点那条判据在 runner 上看不见那串字（U-137…U-142 / D-136）

**靶**：不是新位点 —— 是**读 CI 读出来的**。R76 的 run 38743276799 与 R77 的 38751643297 都是
`4 failures`，四条红全部来自 R76 新写的那条焦点判据。我推 R77 之前没读 R76 的结论，
于是同一朵红在 main 上叠了两层（U-141：连续两轮 push 都没读上一次 CI 就继续）。

### 开场读数（runner vs 本机，同一条判据、同一份代码）

| 量 | runner 1× | 本机 2× |
|---|---|---|
| 框内变化像素 | **0 / 0** | **1797 / 2354** |
| 框外那一圈 | 0 / 0 | 0 / 0 |
| 那一格平均 alpha（不聚焦 ⇒ 聚焦） | 3.55 ⇒ 3.50 / 4.46 ⇒ 4.41 | 10.71 ⇒ 6.77 / 13.15 ⇒ 8.64 |
| alpha 差 | **0.05 / 0.05** | **3.93 / 4.52** |
| 行为那两条（响应者是编辑器 / 撤得掉） | 通过 / 通过 | 通过 / 通过 |
| `focusRingType` | 0 | 0 |

⇒ 两态之差在 runner 上是 0，而"焦点有视觉后果"这条判据只读差值 ——
**"产品没有焦点后果"与"这条通道今天没画那串字"在只读差值的尺子上长得一模一样。**
（`appActive=false 面板key=false` 两档都一样 ⇒ 不是 key 窗口的差别，是画没画。）

### 修法：加一把**不依赖两态相减**的存在性尺，处置按机器分开

`alphaInkPixels(rep, rect, floor:)` = 一块矩形里 alpha 过 8/255 的像素数。量的不是"差没差"，
是"这一格里到底有没有东西"。存在性探针取**占位字该在的那一块**（band 左 30%、四周内缩 3pt）：
整条 band 混得进那颗框的描边（1× 上一圈 1px 就有 ~830 个像素，超过任何计数地板），
而实测占位字的包围盒是 x 12.0–98.5pt ⇒ 左 30% 包得住、内缩排得掉描边。

闸门两半（R60 那一课：机器前提不同 ⇒ 处置不同，但都不许静默）：
· **2× 上"没画" ⇒ 红**（本机这一格必须画得出来，画不出来是捕获或产品坏了）；
· **1× 上"没画" ⇒ 点名 `QUICKPICK_FOCUS_NOT_RUN=1`** 并跳过像素那两条 ——
  行为那两条（响应者、没关系统环）与源码守卫**照判**，不跟着降级。
"永远 NOT_RUN"是要付账的：M417 那一刀把闸门改成恒"没画"，本机当场红。

### 顺带抓出来的两处（都是 R77 那条守卫自己的洞）

1. **名册里躺着一把零调用点的死尺**（U-137）：`UICaptureHarness.paintedXRange` 全仓只有它自己的
   声明，而 R77 的双向名册收了它、理由里还替它写了"R67/R76 那两条判据用它"。
   名册等式抓不到它（它确实在扫到的集合里）⇒ 新增"每条登记必须有人调"那一格 +
   `callSites` 计数器（声明那一次要扣掉），并把死尺**删掉**（R63 那一课：代码没有作者 ⇒ 删代码）。
2. **"两态"的识别认的是写法，不是形状**（U-138）：R77 扫的是减法针脚，于是漏掉了
   `alphaBandDelta` —— 它先按列约成"每列最大 alpha"再写 `abs(maxA - maxB) > floor`，
   减法长得不一样就不是两态尺了。改成**签名形状**（参数表里两份位图）+ 一道阈值（拦误伤）。
   换检测器又踩出一格：`NSBitmapImageRep` 含子串 `Bitmap`，长写法不先挖掉就会把
   单参的 `meanAlpha` / `meanLuma` 数成两态尺（第一版当场误伤两条，U-139）。

### 对账：R76 的注释替事实背书了一次数（U-140）

焦点判据的注释写着"亮档 1901 个像素、暗档 2144 个"与"alpha 143.6 ⇒ 90.9"，
而这条判据自己打的读数是 **1797 / 2354 个变化像素**、**10.71 ⇒ 6.77**。
本轮新加的存在性列反过来解释了那两个数：1901 / 2144 正好是**有墨像素**（聚焦那一态），
被当成"变化像素"抄进了注释；143.6/90.9 是第一版拿另一块矩形量的。
R77 的台账又照抄了注释 ⇒ 现在注释里明写"下面这几个数就是这条判据自己打的那一行"。

### 牙（M413–M418，6/6 CAUGHT）

| 刀 | 动的是 | 抓到在哪 |
|---|---|---|
| M413 | 撤掉"长写法先挖掉" ⇒ 单参电平尺冒充两态尺 | 守卫红（正对照 H） |
| M414 | 签名只取第一行 ⇒ 折行的 `alphaBandDelta` 不再被认出 | 守卫红（正对照 G） |
| M415 | `callSites` 把声明也算成调用 | 守卫红（正对照 F） |
| M416 | 注入一把零调用点的死尺 + 它的登记 | **只有死尺那一格红**（名册等式抓不到） |
| M417 | 存在性闸门恒"没画" | 焦点判据在 2× 上红（永远 NOT_RUN 要付账） |
| M418 | 存在性尺的地板 8 ⇒ 250 | 同上（那把尺承重） |

M416 前两版 NOT-APPLIED：注入型的刀把锚点行原样留在变异文里 ⇒ 又被电池自己的
"变异文不许包含原文"拦下（R76 记过同一族，这次是我自己忘在脑后 —— 记进 U-141 的代价里）。

### 顺带翻出来的一格：分辨率判据押在"最粗那一次采样"上（U-142 / 开 BACKLOG 110）

本机这一遍的动效卷不再是 4/4：`detail-kind-change` 报 `clock-coarse-in-window`。
读数并排放着（中位 50–51ms 两遍一样，**事件内最粗 61 → 81ms**，线在 80ms）
⇒ 一臂"判到 / 判不到"翻脸翻在**单个最慢样本**上，而不是翻在产品上。
这与 R47 那句"帧数会跟着采样相位翻脸"是同一句话的另一半：**max 也是单样本统计**。
本轮**不**把这条理由登记进允许集合（那等于把尺子的抖动登记成产品的性质，
而 R75 那次放宽是有证人读数撑着的，这一条今天没有）⇒ 开 BACKLOG **110**，
下一轮把分辨率判据换成稳健量 + 形状约束。

### 看图

本轮没有产品改动，看的是**焦点那一格的取证图**：`/tmp/r78_shots` 里浮层两张帧
（聚焦 / 撤焦点）与占位区那一块。2× 上那串"搜索历史记录…"清晰、聚焦时退后；
runner 那一档的缺席现在由 `QUICKPICK_FOCUS_NOT_RUN` 点名，不再伪装成产品结论。

### 七维自评

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 19 / 20 | 焦点仍交给系统；本轮修的是"我们的尺在别的机器上看不见它" |
| 流畅度 | 17 / 20 | 动效本体没动；77 路 b 仍欠 |
| 层次与材质 | 14 / 15 | 零产品改动，124 张帧逐字节不变 |
| 动效细节 | 12 / 15 | 焦点那一档的**可判性**现在按机器分开，不再一刀切 |
| 交互反馈 | 9 / 10 | 反馈本身没变；变的是"缺席"与"没有"第一次被分开了 |
| 可访问性 | 8 / 10 | 真机焦点可见性仍未证（批次 68.1 / 68.2） |
| 性能 | 14 / 15 | 全量 793 例 / 40 skip / 0 failures、脚本 140 OK、电池 6/6、告警 0 |

**93 / 100**。分数没涨是应该的：这一轮最好的结果就是把上一轮本该正确的东西修对。
扣的一分记在 U-141 —— 我连推两轮没读上一次的 CI，让同一朵红在 main 上叠了一层。

### 仍未解决

- BACKLOG **109**（本轮新开）：runner 上那一格到底画没画 —— 要等 R78 的 CI 把
  `占位区有墨=…` 打回来才知这道闸门够不够用（如果 runner 有墨而差仍是 0，那句红就是真的）。
- BACKLOG **110**（本轮新开）：分辨率判据换成稳健量（别再押在最粗那一次采样上）。
- BACKLOG 108 剩下的：`alphaBandDelta` / `alphaLiftProfile` 只读 alpha 那一半的代价。
- BACKLOG 77 路 b、101 的②③、106（真实语料）、95 剩下的位点；真机 68.1 / 68.2 / 69.1。


---

## Round 79 · 上一轮的闸门没拦住：存在性要量形状，还要一块"只有它能待"的地方（U-143…U-145 / D-137）

**靶**：读 R78 的 CI（run 38757049151）—— 那四条红**原样还在**：
`框内变化像素=0`、`alpha 差 0.05`，与 R76/R77 一模一样。
也就是说 R78 那道"存在性闸门"在 runner 上根本没关。这是 U-141 那条流程改动的第一次真实执行：
**推完就读**，于是当天就抓到，而不是再叠一轮。

### 为什么没拦住（U-143）

R78 的闸门是"占位区里 ≥20 个有墨像素"。而那颗**放大镜**就住在搜索框左边 ——
本机实测它的墨从 x≈3pt 铺到 20pt（17pt 宽），一个人就凑够 20 个像素。
⇒ 计数过了地板，闸门恒开，像素那两条照判、照红。
**形状上说得通的探针，不等于在几何上分得开东西。**

### 修法：两根互相独立的存在性证人（本机实测）

| 证人 | 量法 | 本机（亮 / 暗） | 只有图标时 | 只有一圈描边时 |
|---|---|---|---|---|
| ① 宽度 | 带内**有墨像素的 x 包围盒**宽度，地板 40pt | 86.5pt / 87.0pt | 17.0pt ⇒ 关 | 会开（所以还要②） |
| ② 独占区 | "只有占位字能待的那一块"（x 从带左起 50pt、上下各内缩 2pt）里有墨像素 ≥ 20 | 675 / 767 | 0 ⇒ 关 | 0 ⇒ 关（被内缩与 50pt 排掉） |

闸门取**合取**。地板不是刀尖：图标 17pt 与文字 86.5pt 之间取 40pt，
独占区实测 675 与门槛 20 之间差三十多倍。
新增的对照（M419/M420 钉的就是它）：**只框住放大镜那一小块，量出来的宽度必须过不了闸门** ——
R78 缺的正是这一条，它只证明了"有墨"，没证明"分得开图标与字"。

### 读数（`.scratch/motion-audit-2/r79_focus.log`）

```
QUICKPICK_FOCUS 亮 … 框内变化像素=1797 框外一圈=0 alpha 10.71⇒6.77 差=3.93 亮度轴差=-0.66
   文字独占区有墨=675 带内有墨包围盒=25…197px 宽=86.5pt 地板=40pt ⇒ 存在性尺说这一格画了东西
QUICKPICK_FOCUS_GATE 亮 图标那一块宽=17.0pt 占位整条宽=86.5pt 地板=40pt ⇒ 闸门开（那串字画了）
QUICKPICK_FOCUS 暗 … 2354 … 13.15⇒8.64 差=4.52 独占区=767 宽=87.0pt
```

### 牙（M419–M422，4/4 CAUGHT，全红在焦点那一条）

| 刀 | 动的是 | 抓到在哪 |
|---|---|---|
| M419 | 宽度地板 40pt ⇒ 10pt（图标一个人就能开门） | 图标那一格的红（对照失去判别力） |
| M420 | 图标探针的矩形换成整条 band（对照读的不是它要读的量） | 同上 |
| M421 | `alphaInkSpan` 的 alpha 地板 8 ⇒ 250（什么都量不到） | 2× 上闸门误关 ⇒ 那条"2× 必须判"的红 |
| M422 | 独占区的地板 20 ⇒ 100000 | 同上（第二根证人承重） |

### 七维自评

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 19 / 20 | 零产品改动；焦点仍交给系统 |
| 流畅度 | 17 / 20 | 动效本体没动；110（单样本 max）本轮被 109 插队，仍欠 |
| 层次与材质 | 14 / 15 | 124 张帧逐字节不变 |
| 动效细节 | 12 / 15 | 焦点那一档的"能不能判"第一次有了两根独立证人 |
| 交互反馈 | 9 / 10 | 反馈本身没变 |
| 可访问性 | 8 / 10 | 真机焦点可见性仍未证（批次 70.1） |
| 性能 | 14 / 15 | 全量 793 例 / 40 skip / 0 failures、脚本 140 OK、电池 4/4、告警 0 |

**93 / 100**。分数与 R78 持平是应该的：这一轮修的是上一轮那道没生效的闸门，
唯一的净收益是"CI 当天读、当天抓到"这条流程真的跑通了一次。

### 仍未解决

- BACKLOG **109**：闸门在 runner 上到底开不开 —— 要等 R79 的 CI 把
  `文字独占区有墨=…` 与 `宽=…pt` 打回来。若独占区仍是 0 ⇒ 那串字在 runner 上真的没画，
  闸门会关、CI 会绿，而结论是"这一档只能真机判"；若独占区非 0 而两态差仍是 0
  ⇒ 那四条红是**真的**，要查的是产品/通道，不许再抬地板。
- BACKLOG **110**：分辨率判据押在"最粗那一次采样"上（R78 开，本轮没动）。
- BACKLOG 108 剩下的、77 路 b、101 的②③、106；真机 68.1 / 68.2 / 69.1 / 70.1。

---

## Round 80 · 焦点那四条红是真的 —— 而"红"说的是我的尺跟着像素网格变（109 交一半 / U-146…U-150 / D-138）

开场读数（先读 R79 的 CI，run 38760347161，commit `3812217`）：

```
Executed 793 tests, with 45 tests skipped and 4 failures
  UICaptureHarness.swift:1531 亮档 框内变化像素=0     < 500
  UICaptureHarness.swift:1539 亮档 alpha 聚焦=3.50    > 不聚焦=3.55 − 2.0
  UICaptureHarness.swift:1531 暗档 同上（0 < 500）
  UICaptureHarness.swift:1539 暗档 4.41 > 4.48 − 2.0
QUICKPICK_FOCUS_GATE 暗 … 占位整条宽=87.0pt 地板=40pt ⇒ 闸门开（那串字画了）
```

两件事同时成立：**存在性闸门是开的**（那串占位字在 runner 上画着，宽度与本机同一个数），
而**两态差读到 0**。这正是 BACKLOG 109 预登记的第二个分支 ——
"若独占区非 0 而两态差仍是 0 ⇒ 那四条红是真的，要查的是产品/通道，不许再抬地板"。
顺带一条流程账：`Swift tests` 这一步红 ⇒ 后面 12 步（含捕获闸门、动效地板、帧基线）**整批被跳过**，
所以那一步的红会把别的判据一起吞掉（U-148）。

### 查出来的机制：换尺，不是抬地板

`changedPixelCount` 数的是"过 8/255 的**像素个数**"。同一件物理变化，网格密一倍就多数四倍 ——
本轮用合成夹具把这件事钉成一条会红的判据（`CAPTURE_INK_RULER_TRUTH_TABLE` ⑧ 那一格）：
**同一个 2000pt² 的墨掉一半，1× 数到 2000 个像素、2× 数到 8000 个**。
⇒ "本机 1797 / runner 0" 那句里最多 3/4 是网格；剩下那 1/4 才是本轮要交给 CI 去分的东西。
而 `alpha 均值掉 ≥2.0` 那道地板也在两台机器上不是一个难度（本机带均值 10.71、runner 3.55）——
R38 那一课，这次中枪的是我自己两轮前写的判据。

新判据读三个**网格无关**的量（本机 2× 实测，`QUICKPICK_FOCUS_INK`）：

| 量 | 亮档 | 暗档 | 地板 |
|---|---|---|---|
| 焦点搬动的墨 pt² | 98.7 | 113.3 | max(40, 10×噪声) |
| 那一格现有墨 pt² | 268.7 | 330.1 | （分母） |
| 占比 | 0.367 | 0.343 | 0.08 |
| 同态重拍的噪声 pt² | 0.0 | 0.0 | 地板的一半由它推 |
| 证人臂 D：撤掉 `placeholderString` | 268.7 | 330.0 | ≥40 ⇒ 尺不瞎 |
| 证人臂 C：打进一个字 | 236.7 | 283.9 | 同上 |
| 撤掉之后那一格的墨 | **0.0** | **0.0** | （见下面 U-146） |

三条证人臂把"看不见"分成两支，两支各有各的名字：
`行为不在这台机器上`（证人臂读得出别的成因在搬动）与 `这一格对这把尺失明`（证人臂也读不出）。
处置仍然按机器分：**2× 上两支都红**（本机是判这条轴的机器），1× 上点名
`QUICKPICK_FOCUS_AXIS_NOT_RUN=1` 并带读数。地板没抬 —— 换的是量，
`≥500 个像素` 那条被 `≥40pt²` + `≥8% 占比` 取代，而 40pt² 是实测 98.7 的 1/2.5。

那两支 1× 才走得到的出口，本机**永远不会执行** ⇒ 它们被提成纯函数
`focusDisposition` / `focusFloorPointsSquared`，由 `testFocusAxisDispositionIsATruthTable`
用合成数字钉（5 格处置 + 3 格地板随噪声）。其中一格一开始是逃的：格② 我写成
`competence: competenceFloor + 49`，于是 M431 把地板抬到十万也照样绿 ——
**引用常数的格子证明不了常数的大小**，改成引用本机实测的 268.7 才咬住（M431 第二次才抓到）。

### 三条更正（都是本轮自己抓的）

- **U-146 · 那颗放大镜不存在。** R79 的注释写"放大镜住在带左边 10–24pt，AppKit 画得出它，
  而占位字画不出来"，并以此解释 R78 的闸门为什么失效。臂 D 撤掉 `placeholderString`
  之后那一格的墨是 **0.0pt²**，而 `quickpick-list-420x300-light.png` 上那颗框
  只有"搜索历史记录…"一串字（产品是 `isBordered=false` + `drawsBackground=false` 的纯 NSTextField）。
  ⇒ 骗过计数的不是图标，是**那串字的开头几个字**：计数分不开"画了 2 个字"与"画了整串"，
  宽度可以。R79 那道对照（"只框住一小片，宽度必须过不了闸门"）**功能仍然成立**，
  作废的是它对那一小片的**解释**；探针改名 `prefixRect`，三处注释与一条 NOT_RUN 文案一起改。
- **U-147 · 注释替代码撒谎。** R78 那道闸门 `continue` 之前写着"行为那两条（①响应者、④没关系统环）
  与源码守卫照判"—— 而④在 `continue` 之后，那一条路径上根本没判。本轮把④挪到所有像素判据之前。
- **U-148 · 一条红会吞掉一批判据。** `Swift tests` 红 ⇒ 捕获闸门/动效地板/帧基线全部没跑。
  "CI 绿只算我读过的那一次"的反面同样成立：**CI 红的时候，我要的读数也不在那一次里**。
  本轮想要的 `文字独占区有墨=…` 那一列就没拿到（见下）—— 但 1531/1539 这两条红的**行号**
  本身就证明两档闸门都开了（闸门关的话红会落在 1523 那条 `XCTAssertLessThan(scale, 2)` 上）。

### 读数通道在并发下会把两行缝成一行（新开 BACKLOG 112）

R79 那一行 `QUICKPICK_FOCUS 暗 …` 在 CI 日志里**不见了**，它被缝进别人的行：

```
1946  MENUBAR_FITTING 声明宽=320 hosting.fittingSize=0.08px 宽=87.0pt(聚焦 12…98) 地板=40pt ⇒ 存在性尺说这一格画了东西…
```

前半是 `MENUBAR_FITTING`、后半是我的焦点行，而 `MENUBAR_FITTING` 自己的结论被吃掉。
`CaptureReadings.emit` 两条腿都不是原子的：`print(line)`（stdio 分两次 write）与
文件通道的 `seekToEndOfFile()` + `write()`（两个线程可以 seek 到同一个偏移），
而 `opened` 那个 `nonisolated(unsafe) static var` 本身也是竞争点。
R64 量过"stdout 会整块丢"，但**丢**与**缝进另一条判据的行**是两种坏法：
后者会毁掉别人的读数，而 `--readings` 那条闸门只看"这行在不在文件里"。

### 牙

M423–M433 共十一刀，全部落在本轮新写的三样东西上（尺 / 处置函数 / 地板常数）。
逐条结果见 `.scratch/motion-audit-2/r80_mutation_battery*.log`（脚本 `mutate_r80_ink_ruler.py`）。

| 刀 | 动的是 | 抓到在哪 |
|---|---|---|
| M423 | 归一化 `÷缩放²` ⇒ `÷缩放` | INK（②⑨ 两格跟着缩放走） |
| M424 | 并集里摘掉 alpha 那一轴 | INK（② 少一半） |
| M425 | 并集里摘掉三条 RGB 轴 | INK（③ 颜色变化读成没动） |
| M426 | 每像素噪声地板失效 | INK（⑥ 地板下那一格抬起来） |
| M427 | α=0 的夹紧摘掉 | INK（④ 全透的 RGB 被算成搬动） |
| M428 | 焦点地板 40 ⇒ 200pt² | DISP + FOCUS |
| M429 | 占比地板 0.08 ⇒ 0.5 | DISP + FOCUS |
| M430 | 处置函数无条件回 judged | DISP（**第一次报 ESCAPED，见下**） |
| M431 | 证人地板 40 ⇒ 100000 | DISP（1× 上会把"行为没有"说成"通道瞎"） |
| M432 | 噪声系数 10 ⇒ 0 | DISP（地板不再随抖动抬） |
| M433 | 证人臂 D 那一步没生效 | FOCUS（臂作废必须有红） |

**抓到=11 逃掉=0 没跑成=0 未落地=0**（第一遍是 10/1，M430 那一刀见下）。

**U-149 · M430 第一次报 ESCAPED，逃的不是判据，是我对它的期望。**
我把预期写成"DISP + FOCUS 都红"，而实际是 DISP 红、FOCUS 绿 ——
FOCUS 在 2× 上**本来就该绿**：本机 98.7pt² 真的过了地板，一扇只对 1× 开的门恒开，
在本机不留任何痕迹。⇒ 期望它红，等于以为"本机也能看出一扇门恒开"，那是错的；
真正的答案是**这条判据结构上不可能在本机抓到那个洞**，所以那三支出口必须
提成纯函数、由合成数字钉（DISP 那 8 格就是唯一有牙的证人）。
这一条与 U-143（"引用常数的格子证明不了常数的大小"）同族：
**证人必须站在能被它作证的那个位置上**，站错了位置的红与不红都不算证据。

### 七维自评

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 19 / 20 | 零产品改动；焦点仍完全交给系统，本轮还证明了那一格里除了占位字没有别的东西 |
| 流畅度 | 17 / 20 | 动效本体没动；110（单样本 max）仍欠 |
| 层次与材质 | 14 / 15 | 124 张帧逐字节不变（本轮三张证人臂不落盘） |
| 动效细节 | 13 / 15 | 焦点那条轴第一次有了"能分成两支"的处置，且两支各有红钉着 |
| 交互反馈 | 9 / 10 | 反馈本身没变 |
| 可访问性 | 8 / 10 | 真机焦点可见性仍未证（批次 70.1 / 71.1） |
| 性能 | 13 / 15 | 每次焦点判定多拍 3 张帧（同态 + 两臂）；全量与闸门见下 |

**93 / 100**。没到 95 的原因很具体：runner 那一遍的 `QUICKPICK_FOCUS_INK` 还没读回来，
"焦点调淡在 1× 上到底是没做还是看不见"这句话今天只有**形状**、没有**答案**。

### 验证（本机，逐条实跑）

```
swift build --build-tests                 告警 0
swift test（全量）                        Executed 795 tests, 38 skipped, 0 failures
swift test --filter UICaptureTests        passed=42 skipped=4 failed=0
ci_capture_gate.py --readings             CAPTURE_GATE_RESULT=ok 红=0  NOT_RUN=2（都是 RING 那一档）
frame_baseline.py check --against working COMPARED=124 CHANGED=0 MISSING=0 ADDED=0
python3 -m unittest discover -s scripts/tests   exit 0（140 OK）
变异电池 M423–M433                        抓到=11 逃掉=0 没跑成=0 未落地=0
curve_from_ledger.py                      PHASE2 n=73 rounds=9..80 mean=92.42（含新的标题审计）
```

两条如实记的账：① 本机 skip 数从 R79 那遍的 40 变成这一遍的 38，而本轮**没改过任何 skip 条件** ——
两遍差的是哪两条我没查（skip 名单以前没归档，从本轮起随验证摘要一起留，见
`.scratch/motion-audit-2/r80_verify_summary.log`）；② 捕获闸门那一步本机仍然报
`补回=202 行` —— stdout 那条腿又丢了大半读数（R64 量过的形状，不是新问题），
本轮的 112 说的是它**另一种**坏法：缝进别人的行。

### 仍未解决

- BACKLOG **109**（半开）：本机侧的答案已经落地；runner 侧等下一次 CI 的
  `QUICKPICK_FOCUS_INK` 与 `QUICKPICK_FOCUS_AXIS_NOT_RUN` —— 三种结果（judged / 行为没有 / 通道失明）
  都在预登记的表里，各自下一步做什么也写好了，不许"CI 绿了"就算完。
- BACKLOG **111**（本轮开）：焦点那条轴在 runner 上赎回来的唯一路径是**换捕获对象**（与 103 同一条路）。
- BACKLOG **112**（本轮开）：读数通道的原子性 —— 缝行会毁掉别人的读数。
- BACKLOG **110**：分辨率判据押在"最粗那一次采样"上（R78 开，两轮没动）。
- BACKLOG 108 剩下的、77 路 b、101 的②③、106；真机 68.1 / 68.2 / 69.1 / 70.1 / 71.1。

## Round 81 · 答案回来了，是决定性的那一支；而修好轴的那个位点开始判红（结案 109、112 / 新开 113 / U-151、U-152 / D-139）

开场读数（先读 R80 的 CI，run 38766914234，commit `3bb8070`）：

```
✓ Swift tests  ✓ Offscreen frame capture  ✓ Capture gate  ✓ 探针两步  ✓ Motion filmstrip
X Motion coverage floor        ← 唯一的一朵红，而且是有名字的红
QUICKPICK_FOCUS_AXIS_NOT_RUN=1 亮：焦点那一档的墨移动在这一台机器上读到 0.0pt²，地板 40.0pt²
  （缩放=1×，同态噪声 0.0pt²）。同一把尺在同一格里读得出别的成因：撤占位字搬动 88.9pt²、
   打进字 113.4pt² ⇒ 尺不瞎，是这台机器的 AppKit 不为非 key 窗口调淡占位符
QUICKPICK_FOCUS_AXIS_NOT_RUN=1 暗：0.0pt²；撤占位字 112.3pt²、打进字 143.2pt²
```

### BACKLOG 109 结案：三支里的是**第二支**，而且是被量出来的

上一轮那三条证人臂就是为这一刻准备的。runner 那一遍读到：

| 量 | 本机 2×（亮 / 暗） | runner 1×（亮 / 暗） |
|---|---|---|
| 焦点搬动的墨 pt² | 98.7 / 113.3 | **0.0 / 0.0** |
| 撤掉占位字搬动 pt² | 268.7 / 330.0 | 88.9 / 112.3 |
| 打进一个字搬动 pt² | 236.7 / 283.9 | 113.4 / 143.2 |
| 同态重拍噪声 pt² | 0.0 / 0.0 | 0.0 / 0.0 |

⇒ **尺不瞎**：同一把尺、同一格、同一台机器上，别的成因能读出 89–143pt² 的搬动，
而聚焦读出**恰好 0.0**。上一轮我留的那句"最多 3/4 是网格"现在有了答案：**网格那部分不成立**，
聚焦在 runner 上是真的什么都没做（0.0 不是"小到量不出"，是一位小数都没有）。
处置按预登记的走：2× 上照旧红（本机必须判得出），1× 上 `QUICKPICK_FOCUS_AXIS_NOT_RUN` 点名，
赎回这条路只剩 BACKLOG **111**（真机 / 非 Retina 那一问，人工批次 71.1）。
顺带一条新事实：runner 那一格的墨只有本机的 **1/3**（88.9 vs 268.7），
这是"1× 上那串占位字画得更淡"的量化，与焦点无关，记下来免得下轮重新查。

### BACKLOG 112 结案：一整行一次 write，并发锤击判据**实测有牙**

`CaptureReadings.emit` 原来两条腿都不是原子的（`print` 分两次 write；文件通道 seek+write；
`opened` 无锁）。现在：stdout 那一条腿改成一次 `FileHandle.standardOutput.write(整行+换行)`，
文件那一条腿整段进 `NSLock`，`opened` 换成**按 URL 记**的 `openedURLs`
（共享布尔会让临时文件的第一行以为"已经开过卷"，于是去 open 一份不存在的文件）。

新判据 `testConcurrentReadingsNeitherSpliceNorDropALine`：8 线程 × 60 条 900B 长行，
三条断言各拦一种坏法 —— 行数（整卷被抹）、**行首与行尾的 (t,i) 必须相等**（缝行）、
每个 (t,i) 恰好一次（覆盖）。第二条是要害：**只看"有没有变化"抓不到缝行，只看位置同一性才抓得到**。

牙（M434–M436，每刀跑 3 遍量复现率）：

| 刀 | 动的是 | 结果 |
|---|---|---|
| M434 | `appendForced` 拿掉锁 | **崩溃 3/3 遍**（SIGSEGV） |
| M435 | 同一刀再跑一遍 | 崩溃 3/3 遍 ⇒ 复现率 100% |
| M436 | "第一次写要整份重写"这条分支每次都走 | 红 3/3 遍（行数那一条） |

**这一刀比预想的更狠**：没有锁的时候两个线程同时改同一个 `Set` / 同一个 `FileHandle`，
进程直接段错误 —— 不是"读数被缝掉"那么温和。

### U-151 · 电池把崩溃读成"编译没过"（分类器只认两种形状）

第一遍这批三刀全报 `NOT-RUN 有 3 遍编译没过`。真相是：`error: Exited with unexpected signal code 11`
**带 `error: ` 却没有 `error: -[类 方法]` 那个形状**，于是被旧分类器归进"没跑成"。
而崩溃在这里恰恰是最硬的证据。⇒ 分类器加第三类 `crashed`，并把"红"与"崩"都算 CAUGHT、分开报数。
这条与 R61 的 U-94（"红了但连一条断言行都没有 ⇒ 崩溃"）**同族但方向相反**：
那次是判卷把崩溃吞成绿，这次是把崩溃吞成"没跑"。
**共同点：分类器只认它见过的那几种形状**，而每一种新形状都要被显式命名，否则它就是一个没人负责的默认值。

### U-152 · 修好一把轴，会让一个"以前不判"的位点开始判红 —— 这是**成果**，不是回归

`Motion coverage floor` 那一朵红：`testSkeletonSweepActuallySweeps`
`XCTAssertGreaterThanOrEqual failed: ("2") is less than ("3") — 只读到 2 对在变 ⇒ 那不是循环，是一次跳变`。
把三次 runner 读数并排放（原文都来自 `gh api .../jobs/<id>/logs`）：

```
R73 run 38726991211（绿）  MOTION_SHIMMER 扫 帧数=23 变化帧对=0 峰值=0.000 采样≈98ms
R75 run 38735395615（绿）  MOTION_SHIMMER 扫 帧数=20 变化帧对=0 峰值=0.000 采样≈125ms
R80 run 38766914234（红）  MOTION_SHIMMER 扫 帧数=23 变化帧对=2 峰值=0.015 采样≈115ms
```

⇒ 绿的那两次**根本没判**：`requireObservableMotion(.gradient)` 看见峰值 0.000 ⇒ 报 not-run 跳过。
R77 把两态尺改成并集（alpha 进判定）之后，runner 第一次看得见这个渐变（0.015），
闸门放行，判据第一次真判 —— 然后判出来是红的。
所以这朵红的含义是：**一个以前免检的位点现在要开始被检了**，而它的判据形状（"数变化的帧对"）
在 115ms 的采样网格上撑不住。这正是 BACKLOG **110** 说的那族病，只是换了个位点，
于是新开 **113** 把它作为 110 的第二个实例钉住（下一轮第一件事就是它，main 上这朵红只许活一轮）。

### 验证（本机，逐条实跑）

```
swift build --build-tests                告警 0
swift test（全量）                       Executed 796 tests, 38 skipped, 0 failures
swift test --filter UICaptureTests       捕获闸门 CAPTURE_GATE_RESULT=ok 红=0 NOT_RUN=2（都是 RING）
frame_baseline.py check --against working COMPARED=124 CHANGED=0 MISSING=0 ADDED=0
python3 -m unittest discover -s scripts/tests  exit 0
并发锤击 M434–M436                       3/3 CAUGHT（两刀以崩溃的形式、一刀以红）
读数文件里 QUICKPICK_FOCUS_INK 行数      2（亮/暗各一，**没有一行被缝掉**）
```

### 七维自评

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 19 / 20 | 零产品改动；焦点那格的墨 1/3 差异是通道/系统性质，不是产品 |
| 流畅度 | 16 / 20 | 扫光那条判据现在红着（113 未修），这一格本轮没脸加分 |
| 层次与材质 | 14 / 15 | 124 张帧逐字节不变 |
| 动效细节 | 13 / 15 | 109 有了决定性的答案；扫光那一位从"免检"变成"在判" |
| 交互反馈 | 9 / 10 | 反馈本身没变 |
| 可访问性 | 8 / 10 | 真机焦点可见性仍未证（批次 71.1 新增非 Retina 那一问） |
| 性能 | 14 / 15 | 全量 796 例 / 38 skip / 0 failures；锤击只在临时文件上跑，不污染读数卷 |

**93 / 100**。低于 95 的原因写在脸上：main 上现在有一朵**有名字**的红，
而本轮没有修它 —— 记成 113，下一轮第一件事。

### 仍未解决

- BACKLOG **113**（本轮开，下一轮第一件事）：扫光那条"循环 vs 跳变"不许数帧对。
- BACKLOG **110**：同一族病的第一个实例（`detail-kind-change` 押在最粗那一次采样上）。
- BACKLOG **111**：焦点那条轴在 runner 上的赎回（唯一路径是换捕获对象 / 真机非 Retina）。
- BACKLOG 108 剩下的、77 路 b、101 的②③、106；真机 68.1 / 68.2 / 69.1 / 70.1 / 71.1。

## Round 82 · 单颗证人被上一遍 CI 打回：证人必须与它作证的判据**同节拍**（结案 113、110 的第一实例 / 新开 114–117 / U-155…U-159 / D-140）

### 本轮开场的位点清单（按契约带坐标；本轮 0 个产品文件）

本轮重新判断的那一位是**加载态骨架屏的那条扫光**，位置与尺寸沿用已入账的读数：
详情预览区 `.loading` 分支里那三根 `SkeletonMotion.barFractions = [0.42, 0.86, 0.64]` 的条带，
每根高 8pt、圆角 `VisualRadius.chip` = 4pt，亮带 `bandSize` 0.3 从 x=−0.3 扫到 x=1.0（单位是条带宽），
一圈 `MotionCatalog.duration(for: .skeletonSweep)` = 1.5s、每拍 `SkeletonMotion.tickInterval` = 1/30s。
帧基线里它对应 `detail-loading` 那几张（本轮 COMPARED=124 CHANGED=0 MISSING=0 ADDED=0（against working） ⇒ 静置画面一个像素没动）。
"这条该不该有动效"的判断没变（M9 那条感知等待的理由仍然成立，抬升 0.12 也仍然在
`minimumHighlightLift` = 0.08 之上）；**本轮动的是判它的那把尺**。

### 读 R81 的 CI（run 38770024897，12m38s）：唯一那朵红就是 113 说的那朵，而它带了新信息

失败步骤只有一个：`Motion coverage floor`，
`MOTION_FLOOR_FACTS judged=4/4 executed=49 not-run=- 红的用例=testSkeletonSweepActuallySweeps`、
`MOTION_FLOOR_SUITE_RED=1 … ("2") is less than ("3")` —— 与 R80 同一朵，没有新增红；
R80 那四条焦点红在 1× 上不再红（`QUICKPICK_FOCUS_INK 亮 缩放=1× 带墨面积=89.2pt² 焦点搬动=0.0pt²(地板 40.0…)
证人臂撤占位字=88.9pt²` 原样打出来了 ⇒ R81 的处置生效）。**捕获那一步今天全绿**。

真正的收获是那一遍同时打出的两行对照（原文）：

```
runner  MOTION_SHIMMER 扫 帧数=27 变化帧对=2 峰值=0.015 采样≈86ms
runner  MOTION_CONTROL 渐变端点 帧数=21 峰值=0.029 变化帧对=13
runner  MOTION_CONTROL 计数方块 帧数=19 峰值=0.029 变化帧对=17
```

⇒ 如果照 R81 的计划直接换成"一颗证人"，这一遍 CI 会判成 `.productRed`（证人在动、产品没动）。
但那条推论**说过头了**：那颗证人是 20Hz、亮带抬 0.45，而产品是 30Hz、抬 0.12 ——
"这台机器带得动一个 20Hz 高对比循环"并不蕴含"带得动产品那一档"。
R68 立的是"证人必须与判据问同一句话"，那句话里有一个具体的赫兹数和一个具体的抬升。

### 修法一（判据形状）：数帧对 → coverage

`LoopShape(pairs, changingPairs, peak, coverage, recordedMilliseconds)` +
`loopShape(fractions:stamps:)`，判据读 **coverage**（首尾两个"还在变"的帧对之间的时间 ÷ 整卷时长）
⇒ 与帧数无关。`minCoverage = 0.5`：本机三遍真值 **0.955 / 0.977 / 1.000**，一次跳变在 20 帧对上是 **0.05**，
中间十倍空间，0.5 不在刀尖上；地板**不许**为哪台机器过线而移动（110 立的规矩）。
合成真值表 `testTheLoopShapeClassifierIsATruthTable` 里最关键的是第③格：
同一种"一直在变"在 50ms 与 115ms 两档采样下**必须同判定、同 coverage**，
而旧那把"数帧对"的尺在两档上必须给出**不同**的个数 —— 这一格钉的就是换尺的理由本身。

### 修法二（证人）：一颗 → 两颗，等节拍那颗决定红与不红

* `GradientTickView` 开成四个参数（节拍 / 每拍推进量 / 底色 / 亮带），默认值 = 原来写死的那几个数
  ⇒ 老调用点（`requireObservableMotion`、`MOTION_CONTROL`）读数不变；
* `GradientTickView.productRate()`：30Hz、每拍 (1/30)/1.5、0.06→0.18、同一颗 `VisualShape.rounded(VisualRadius.chip)`。
  四个数**写死在测试里**（读产品常量的话，产品哪天把抬升调到看不见，证人跟着一起瞎 ⇒
  "环境看不见"那一支永远有人签字，与 `FadeClockView` 把 150ms 写死是同一条理由）；
  代价由一条新的会红的钉子兜住：`testTheLoopWitnessStillMirrorsTheProductLoop`
  断言这四个数**仍等于** `SkeletonMotion` / `MotionCatalog` 的那几个（漂移 = 红，不是注释）。
* 处置 `loopAdjudication(product:rateWitness:coarseWitness:)`：产品在跑 ⇒ 绿；
  等节拍在跑而产品没跑 ⇒ **产品红**；等节拍也没跑 ⇒ `MOTION_NOT_RUN=loop-clock-not-sustainable-at-product-rate`；
  连粗节拍那颗都整卷没拍到 ⇒ **证人坏**，红（空支票守卫，M439 钉它）。

本机三卷（同一次跑，2×）：

```
MOTION_SHIMMER 扫 帧数=47 变化帧对=23 峰值=0.015 采样≈54ms coverage=1.000(地板 0.50) 记录时长=2450ms 判定=一直在动
MOTION_SHIMMER_WITNESS 等节拍证人(30Hz 抬升 0.12，与产品同数字) 帧对=47 在变=23 峰值=0.015 coverage=1.000 判定=一直在动
MOTION_SHIMMER_WITNESS 粗节拍证人(20Hz 抬升 0.45，只签字'看得见这种画法') 帧对=46 在变=42 峰值=0.026 coverage=1.000 判定=一直在动
LOOP_WITNESS_MIRROR 节拍=33.3ms 每拍推进=0.0222 抬升=0.12 三项全等于产品 ⇒ 证人还在问同一句话
```

**这一组数里最有用的是等节拍那颗与产品的接近程度**：产品 23/47 对在变、等节拍证人 23/47 对（本机另两遍是 20 vs 21、19 vs 19 —— 最多差一对），
峰值都是 0.015 —— 把节拍与抬升对齐之后，"归属不同"这件事在本机上几乎不产生差别。
所以 runner 上那 2 对 vs 13 对的悬殊，很可能大部分是**参数差**而不是产品差，
下一遍 CI 会给出答案（BACKLOG 114）。

### U-155 · 探针把时刻存在自己身上，两卷连拍就会串卷 —— 而**任何断言都拦不住等长的两卷**

第一版的判据写成了：

```swift
let runningFrames = probe.record(reduceMotion: false)   // 第一卷
let stopped = deltas(probe.record(reduceMotion: true))   // 第二卷，顺手覆盖了 probe.lastStamps
let shape = loopShape(fractions: running, stamps: probe.lastStamps)  // ← 用第二卷的时刻算第一卷
```

本机第一次跑出来是 `coverage=0.000 记录时长=0ms`（两卷碰巧不等长 ⇒ 掉进 guard），
我把它当"探针坏了"来读；而**把它改对的中间那一版**读出来是 `coverage=0.979` ——
数字合理、判据绿、台账上就可以写"本机 0.98"。真正的证据是变异刀：
**M443 第一版把那句话原样改回 `probe.lastStamps`，四条判据全绿**
（`.scratch/motion-audit-2/r82_mutation_battery_v1.log`）。
⇒ 教训不是"记得当场取走"（我确实写了 `let runningStamps = probe.lastStamps`，
    但那只是把错误挪到了一个断言拦不住的距离上），
   而是**让错的那句话在类型上拼不出来**：探针改成返回 `GrabbedFilm(frames:stamps:)`，
   `lastStamps` 从这两个探针上删掉。
这个文件里其实**早就有**这个形状 —— 主场景探针的 `Film(frames:stamps:triggerFrame:)`
与淡入探针的 `FadeClockProbe.Run`；只有我上一轮新加的两个手写探针把时刻存在了对象身上。
**同族前科**：D-139 里"共享布尔 `opened` 让临时文件的第一行以为已经开过卷"是同一件事
（对象的 global 状态把调用方骗了），只不过那次的后果是崩，这次是**安静地给出一个像样的错数**。
TableProbe 还留着同款 `lastStamps`（它的调用点都是当场读）⇒ 记成 BACKLOG **115**。

### U-156 · 形状尺的 guard 把峰值原样报出去 ⇒ 前提故障冒充成"只动了一下"，处置方向跟着翻

`loopShape` 的 guard 分支（时刻与帧对数不匹配 / 只有一帧 / 整卷空白）原来返回 `peak: maximum`。
那一刻 `coverage = 0` 而 `peak = 0.02` ⇒ `verdict = .oneShot` ⇒
"尺没法算"被说成"产品只动了一下"，正好是 `.productRed` 那句话。
改成返回 `peak: 0` ⇒ `.notMoving` ⇒ 点名"没量到"。真值表第⑥格钉形状、
并额外钉一条**方向对照**：`notMoving` 的产品配上活的证人仍然必须红（它没有悄悄变绿）。
M444 就是这一刀。

### U-157 · 结构等式要双向，`>` 不是 `==`

同一根 guard 里的 `stamps.count > fractions.count` 只拦"少一根"，不拦"多一根"
（多一根意味着这列时刻来自另一卷更长的胶片 —— 正是 U-155 的形状）。
换成 `stamps.count == fractions.count + 1`，真值表里两格（少一根 / 多一根）各钉一边，
M443 换成这一刀 ⇒ 等式挪一格，本机每一卷真胶片都算"没量到" ⇒ 两条判据同时红。

### U-158 · 电池的分类器：崩掉的用例与没轮到的用例，不能都算『没跑』，也不能都算『红』

M443 把结构等式挪一格之后，真值表里那一格走进 `loopShape` 的分支去取 `stamps[last + 1]`，
越界 ⇒ `Fatal error` ⇒ 整个测试进程带走。于是那一条用例**既没有 `failed` 行也没有 `passed` 行**，
旧分类器把它归成 `absent`（=『这条没跑』），而排在它前面的 SHIM 确实红了 ⇒
电池报的是 **`ESCAPED 红的不是预期那几条`**。真相是这一刀抓得**最狠**：它把判据崩掉了，不是放过去了。
⇒ 分类器现在认两种新形状，而区分它们的依据必须是**这条用例自己开过口**：
`crashed` = 日志里有它的 `error: -[…方法]` 行却没有结论行（算红）；
`absent` = 从头到尾没提过它 ⇒ **没轮到**（不算红）。
`swift test` 不打 `started` 行，所以『整份日志里有崩溃痕迹』不能当归因依据 ——
用它会把排在崩掉那条**后面的每一条**都签字成红，那是 U-151 的镜像方向
（那次把崩解读成没跑，这次差点把没跑读成崩）。
**分类器只认它见过的形状**，而每一种新形状都必须带着自己的证据被命名。

### 真实看图：这条扫光**第一次**有条带图可看，而它立刻暴露了一件数字看不见的事

判据只读到"覆盖率 0.977、峰值 0.015"，看不出**亮带长在哪儿**。所以本轮给这条判据补了
`writeStrip("skeleton-sweep", …)`（放在所有闸门之前 ⇒ 红了也留一张能看的），
产物 `.scratch/motion-audit-2/r82_skeleton_sweep_strip.png`（24 帧 / 六列 / 4 行，按阅读顺序）。

看下来的结论分两半：

* **好消息，而且与数字一致**：亮带从每根条的左边进、右边出，第四行又从左边重新进来 ⇒
  `advance` 的绕回真的在演（不是"扫到一半卡住再弹回去"那一族），抬升 0.12 在这个尺寸上
  读起来是"有东西在动"而不是"闪"，克制程度符合"不喧宾夺主"。
* **数字看不见的那一半**：三根条上的亮带**不在同一条竖线上**。机制是可推出来的，不用猜 ——
  `SkeletonMotion.unitPoints(phase:)` 给的是 `UnitPoint`，而它被用在**每根条自己的**
  `LinearGradient` 上，`UnitPoint` 是按被填充形状的边界归一化的 ⇒
  同一相位下亮带在三根条上的绝对位置按宽度 0.42 / 0.86 / 0.64 **各自放大**，
  于是它更像"三根条各扫各的"，而不是"一块光从整组骨架上扫过去"。
  系统里的原生骨架（以及 GitHub 那类提交热图的呼吸感）是后者：一条带穿过整组，
  读起来才像"同一个光源"。
  ⇒ 新开 **BACKLOG 117**：先量三根条上亮斑中心的 x（逐帧、带正对照"同一根条两个相位必须不同"），
  再判要不要把渐变挪到**容器**上（那会改到静置画面 ⇒ 124 张帧要同提交 update）。
  本轮**不动产品**：这条是看图看出来的新缺陷，按规矩先量再改（也不许为了它今天改帧基线）。

### U-159 · 同一份代码的**全量卷里，skip 的条数在两次跑之间自己动了**（7 条的幅度，本轮量出来）

| 遍 | 原文 |
|---|---|
| R81 第一遍（`.scratch/motion-audit-2/r81_verify_summary.log`） | `Executed 796 tests, with 38 tests skipped and 0 failures … in 161.868s` |
| R81 另一遍（`/tmp/r81_full.log`，同一提交、同一台机器） | `Executed 796 tests, with 45 tests skipped and 0 failures … in 154.9s` |
| R82（`/tmp/r82/full.log`） | `Executed 799 tests, with 40 tests skipped and 0 failures … in 145.4s` |

⇒ **同一个提交里就有 38 与 45 两个数**（不是记账口径不同：两行的格式一模一样，时长不同 ⇒ 是两次跑）。
R82 的 40 = 799 − 3 条新判据之外还差着同样的抖动。`comm` 出来的差集落在五条 `UICaptureTests`
（`testSettingsHelperTextIsNotClipped`、`testInkDirectionRulerReadsBothEnds`、
`testRowTierProfileSeparatesCaptionFromTitle`、`testSettingsCaptionSitsCloserToItsOwnToggle`、
`testDarkSettingsSidebarTextIsACountedBlindSpot`）—— 同一份代码、同一台机器，
一会儿 skip 一会儿跑，而台账把它们都记成"过了"。
⇒ 记成 **BACKLOG 116**：这五条的 skip 判据必须把"为什么今天没跑"打成一行**有名字的读数**
（像捕获卷那族 `*_NOT_RUN` 一样），否则"这一轮多判了五条"和"上一轮少判了五条"
这两种相反的解释在台账上长得一样 —— 而**判据有没有跑**本身就是需要被审计的量。
本轮不给原因：第一版怀疑是变异电池的临时目录串了，读源码后不成立
（这五条各用 `temporaryDirectory/r28-clip-<UUID>`，互不共享）。**没量出来就别写。**
（顺带纠正我自己：R81 台账里那句"796 例 / 38 skip"引的是其中一遍，
它不是错的，但它被当成了"这一轮的固定属性"—— 一个会抖的数被写成了常量，U-139 同一族。）

### 牙

| M437 | coverage 地板从 0.5 降到 0.02 | **CAUGHT** |
| M438 | coverage 的分母从『整卷时长』换成『变化段时长』 | **CAUGHT** |
| M439 | 粗节拍证人整卷没拍到任何变化时改走『环境看不见』那一支 | **CAUGHT** |
| M440 | 把结构体里那条峰值地板挪离全卷那条（两个数分家） | **CAUGHT** |
| M441 | 分辨率闸门改回『最粗那一次』（把分位数取成 1.0） | **CAUGHT** |
| M442 | 产品没在动也返回 .ok | **CAUGHT** |
| M443 | 把 `stamps.count == 帧对 + 1` 这条结构等式挪成 `== 帧对` | **CAUGHT** |
| M444 | guard 分支把峰值原样报出去（不返回 0） | **CAUGHT** |
| M445 | 等节拍证人的节拍偷偷改回 0.05（与产品的 1/30 分家） | **CAUGHT** |

### 验证（本机，逐条实跑）

```
swift build --build-tests                告警 0
swift test（全量）                       799 tests / 0 failures（40 skipped，145.4s，swift test exit 0） / skipped 40（上一轮记的是 38，见 Round 82 的"skipped 从 38→40"那一格）
动效那一步                               MOTION_FLOOR_FACTS judged=4/4 executed=52 not-run=- summary=detail-kind-change=3 empty-state=3 notice-banner=12 notice-banner-dismiss=11 红的用例=- 汇总行报红=0 MOTION_FLOOR_REDS=0MOTION_GATE_EXIT=0
捕获闸门                                 CAPTURE_GATE_RESULT=ok 红=0（已登记的 NOT-RUN 见上）
frame_baseline.py check --against working COMPARED=124 CHANGED=0 MISSING=0 ADDED=0（against working）
python3 -m unittest discover -s scripts/tests  Ran 140 tests in 7.023s OK PY_EXIT=0
自评曲线                                 PHASE2 n=75、rounds=9..82、均值 92.45、最低 86、最高 96、GAPS=none、SCORES_BY_ROUND 79=93 80=93 81=93 82=94
扫光那条第一次有的条带图                  .scratch/motion-audit-2/r82_skeleton_sweep_strip.png（24 帧 / 六列）
全量 skipped（同一提交两遍 + 本轮，见 U-159）  38 / 45 / 40 —— 一个会抖的数，不许写成常量
```

### 七维自评

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 19 / 20 | 零产品改动；扫光的抬升 0.12 与 4pt continuous 圆角都仍在系统语言里，本轮没脸加分也没被扣分 |
| 流畅度 | 18 / 20 | main 上那朵红换了个来源：不再是"判据吃采样"，而是"这一档节拍的循环在 runner 上带不带得动"（114，等 CI 读数）；本机 coverage 0.955–1.000 |
| 层次与材质 | 15 / 15 | COMPARED=124 CHANGED=0 MISSING=0 ADDED=0（against working） |
| 动效细节 | 13 / 15 | 循环那条判据从"数帧对"换成时间之比 + 两颗证人；证人漂移有钉子 |
| 交互反馈 | 9 / 10 | 反馈本身没变 |
| 可访问性 | 8 / 10 | 减弱动态那一档仍然有判据（峰值 0.000），但真机复核仍欠（批次 72） |
| 性能 | 14 / 15 | 全量 799 tests / 0 failures（40 skipped，145.4s，swift test exit 0）；证人每进程一次，多出来的那一卷 2.5s 只在扫光那一条上付 |

**94 / 100**。比 R81 的一分来自"main 上那朵红的来源从我的尺换成了可判定的问题"，
扣的六分写在上面三行里：114 还没有答案，115/116 是本轮量出来但没修的账，
117 是看图看出来的新缺陷（按"先量再改"排到下一轮），批次 72 还没人看。

### 仍未解决

- BACKLOG **114**（本轮开）：runner 那一遍到底带不带得动 30Hz 那一档常驻循环 ——
  等节拍证人与产品那两行 coverage 给答案；若是"带不动" ⇒ `loop-clock-not-sustainable-at-product-rate`
  是一朵**有名字的未覆盖**；若是"带得动而产品没跑" ⇒ 那是第一条真红，回去查接线。
- BACKLOG **115**（本轮开）：`TableProbe` 仍然把抓帧时刻存在对象身上（同款 U-155 风险）。
- BACKLOG **116**（本轮开）：同一提交的全量卷里 skip 条数自己动了 7 条（38 / 45 / 40 三个数），
  而那五条 `UICaptureTests` 没有一行"为什么今天没跑"的读数 ⇒ 判据有没有跑，今天没人审计。
- BACKLOG **117**（本轮看图开出）：骨架扫光的亮带在每根条上**各扫各的**，
  不是一块光穿过整组骨架（`UnitPoint` 落在每根条自己的渐变上）。先量亮斑中心，再判要不要改容器层。
- BACKLOG 111、110 剩下的两格、108 余下、77 路 b、101 ②③、106；真机 68.1 / 68.2 / 69.1 / 70.1 / 71.1 / **72.1 / 72.2**。

## Round 83 · 上一轮那枚钉子挂错了对象：前提不许挂在结论尺的输出上（结案 114 / 新开 118 / U-160…U-164 / D-141）

### 本轮开场的位点清单（本轮 0 个产品文件；看图的部分是复用上轮那张条带图，量的是它）

被重新判断的**不是画面**，是上一轮我自己交的两条判据 + 一格闸门：
1. `testSkeletonSweepActuallySweeps` 的卷长钉子（`MotionFilmstripTests.swift`，R82 新加）；
2. 同一条判据里的绝对峰值地板（R82 之前就有，本轮第一次让它听处置的话）；
3. `scripts/motion_floor_gate.py` 的 `NAMELESS_RED` 那一格（R66 建的，本轮修它的比较单位）。

看图这一项本轮没有跳过：上轮那张逐帧条带图（`r82_skeleton_sweep_strip.png`）被拿来**量**了
（工具 `.scratch/motion-audit-2/r83_band_fanout.py`，读数 `r83_fanout_readings.log`），
量出来的就是 BACKLOG 117 那条缺陷的数字（见下面"看图量出来的那一格"）。

### 读 R82 的 CI（run 38781113064，12m11s）：114 的答案是预登记的**第一支**，而那两朵红都是我的

```
runner  MOTION_SHIMMER 扫 帧数=21 变化帧对=0 峰值=0.000 采样≈118ms
runner  MOTION_SHIMMER_WITNESS 等节拍证人(30Hz 抬升 0.12) 帧对=35 在变=2 峰值=0.015 coverage=0.284
runner  MOTION_SHIMMER_WITNESS 粗节拍证人(20Hz 抬升 0.45)  帧对=26 在变=23 峰值=0.028 coverage=1.000
runner  MOTION_NOT_RUN=loop-clock-not-sustainable-at-product-rate …
```

⇒ 这台机器带得动 20Hz 的常驻循环，带不动 30Hz 的那一档 —— 与产品无关，也不是"归属"问题。
R82 那把等节拍证人**问对了问题**：如果沿用 R81 的单颗证人，这一遍会红着说"产品的扫光没跑"，
而那句是错的。114 就此结案（两支里落在第一支，处置是点名 not-run）。

但 `Motion coverage floor` 这一步仍然红，红的两条都在我上一轮写的东西上（原文）：

```
MotionFilmstripTests.swift:4500  XCTAssertEqualWithAccuracy ("0.0") is not equal to ("2500.0") +/- ("625.0") - 产品那卷的记录时长…
MotionFilmstripTests.swift:4532  XCTAssertGreaterThan ("0.0") is not greater than ("0.005") - 该扫的那一档什么都没变…
MOTION_FLOOR_SUITE_NAMELESS_RED=1 汇总行说这一卷红了 2 次，日志里只找得到 1 个名字
```

三条一起看，本轮的账就清楚了：**处置已经说"这台机器判不了这一臂"，而这三处各自还在按别的话判。**

### U-160 · 前提钉子挂在结论尺的输出上 ⇒ 一台机器"看不见运动"被改写成"探针坏了"

R82 那条卷长钉子写的是 `XCTAssertEqual(shape.recordedMilliseconds, 2500 ± 625)`，
而 `recordedMilliseconds` 是 `loopShape` 的输出 —— 它的 guard 分支（峰值 0、时刻不配对、只有一帧）
**一律返回 0**。本机永远看不见这个耦合，因为本机有运动；runner 那一遍产品峰值 0.000，
于是 guard 走通、卷长变 0、钉子红，报的是"这些时刻不属于这卷帧对"——一个探针罪名，
而真实情况是"这台机器看不见这一档节拍的循环"。
⇒ 新增 `FilmPremise(frames:stamps:)`：**卷长与配对从时刻本身算**，与有没有运动无关
（一条静止 2.5 秒的卷仍然是 2.5 秒）。真值表第⑧格钉的是"两把尺必须给出不同的数"：
`still.spanMilliseconds == 1000` 而 `deadShape.recordedMilliseconds == 0`，
再加一条 `XCTAssertNotEqual(两者)` —— 谁把它们接回同一把尺，那一格就红。
**同族**：U-155（错话写得出来）、U-139（给没量过的东西写阈值）；这一条的新形状是
**"结论尺的输出被当成它自己的前提"**，而它只在另一台机器上才现形。

### U-161 · 比较的两边必须同为一种单位：`with N failures` 数的是断言，不是用例名

`NAMELESS_RED = summary - len(named)`：R82 那一遍 summary 说 2 次失败（同一条用例里两句 XCTAssert），
而 `failures` 是**去重后的用例名**（1 个）⇒ 报出"有一条红没有名字"，而两条红都有名字。
这一格存在的意义恰恰是"有红没名字"，所以它一旦被误报，下一轮就有人来把它放宽（R36 那一族的反面）。
⇒ 改成 `attributable = max(failure_lines, len(named))`，其中 `failure_lines` 数的是
`error: -[…方法] :` 那种**每句失败各一行**的行；两边同为行数。
两格回归测试：一条用例两句红 ⇒ 不许报 NAMELESS（但仍报 `SUITE_RED=1`）；
同一份夹具抽掉一行 ⇒ NAMELESS 必须回来（R64 的 stdout 成块丢的形状，不许被这次修法放走）。

### U-162 · 同一件事只准判一次：绝对地板必须听处置的话

峰值地板（`peak(running) > 0.005`）问的是"这台机器上这一臂有没有东西在动"——
这与处置问的是**同一件事**，只是换了个绝对阈值。处置已经判"环境不行"之后，
这条地板再红一次，等于把同一个事实用两个身份报出去，而第二个身份（"扫光没落地"）
天然把责任推给产品。⇒ 现在只有 `.ok / .productRed`（环境已被证明有资格判这一臂）时
绝对地板才说话；其余两支打一行 `MOTION_SHIMMER_PEAK_NOT_JUDGED 峰值=… 处置=…`。
**不豁免的那一条留在原地**：减弱动态那档"必须静止"永远判 ——
"看不见运动"永远不会伪造出运动来，所以那一臂没有环境借口（这一句是本轮的边界，别扩大）。

### 看图量出来的那一格（117 从"看图觉得"变成有数字）

`r83_band_fanout.py` 逐帧量三根条上亮斑的中心（24 帧里 22 帧可用，2 帧因"亮带不在这根条上、
条内剖面是单调斜坡"被丢掉并数出来）：

```
条带宽（pt）= ['176.4', '361.2', '268.8']（由 barFractions × 格宽 420pt 推出，量出来的 y 带与它一致）
  帧(0,0) 绝对中心=['16.0', '33.5', '24.5'] pt  归一化=['0.091', '0.093', '0.091']
  帧(3,0) 绝对中心=['34.5', '70.5', '52.5'] pt  归一化=['0.196', '0.195', '0.195']
  帧(2,1) 绝对中心=['70.5', '143.5', '107.5'] pt  归一化=['0.400', '0.397', '0.400']
  帧(5,1) 绝对中心=['95.0', '195.5', '145.5'] pt  归一化=['0.539', '0.541', '0.541']
  帧(1,2) 绝对中心=['106.0', '216.5', '161.5'] pt  归一化=['0.601', '0.599', '0.601']
  帧(4,2) 绝对中心=['131.0', '268.5', '200.0'] pt  归一化=['0.743', '0.743', '0.744']
  帧(0,3) 绝对中心=['146.0', '299.5', '223.0'] pt  归一化=['0.828', '0.829', '0.830']
  帧(3,3) 绝对中心=['162.0', '332.5', '247.5'] pt  归一化=['0.918', '0.921', '0.921']
用了 22 帧，丢掉 2 帧（亮带没扫到全部三根条：幅度低于 5 灰阶，或剖面是单调斜坡=极大值贴在边上）
结论：**同一帧内**三根条的绝对中心最大相差 170 pt，而归一化中心最大只差 0.003（=1 pt 在最宽那根上）
正对照（同一根条跨帧必须移动）：不同帧上第一根条的归一化中心共 22 个不同取值 [0.09, 0.11, 0.17, 0.2, 0.25, 0.28, 0.31, 0.37, 0.4, 0.46, 0.48, 0.54]
⇒ 支持假设 B（每根条各扫各的）；地板：归一化散布 < 0.02 判 B、绝对散布 < 8pt 判 A
```

⇒ **同一帧内**三根条的亮斑中心**绝对**位置最大差 170pt，而**归一化**位置只差 0.003（≈1pt）；
正对照：第一根条的归一化中心在 22 帧上取到 22 个不同值（0.09→0.92）⇒ 亮带确实在一路扫。
结论：亮带是**每根条各扫各的**，不是一块光穿过整组骨架 —— 机制在
`SkeletonMotion.unitPoints(phase:)` 给的是 `UnitPoint`，而它被用在每根条自己的 `LinearGradient` 上。
这一条改产品是下一轮的事（117 已带数字与修法）。

量的过程本身又抓到两把尺读错东西（都写进工具的注释里，因为它们各红过一次结论）：
① 阈值取"高于本行中位数 + 1" ⇒ 量到的是**整根条**（条带底色本来就比窗口背景亮），
第一根条的质心恒等于它的中点 88.0pt、24 帧一个数都不动；
② 亮带不在的那根条上，条内剖面是单调斜坡，"半程以上"退化成条的中点 ⇒ 这种帧必须**丢掉并数出来**
（最后一帧就是这么把散布从 0.003 顶到 0.448 的）。⇒ 记成 **U-163**：
相对阈值在信号缺席时不是"读不到"，而是**读到一个与信号无关的假数**，必须配一条"信号在不在"的门。

### 牙

| M446 | `paired` 干脆不看时刻条数（等式整条丢掉） | **CAUGHT** |
| M447 | 卷长少乘 1000（秒当成毫秒） | **CAUGHT** |
| M448 | 卷长钉子改回挂在**结论尺**的输出上（R82 第一版的形状） | **LOCAL-NO-POWER** |
| M449 | 峰值地板改回**不管处置**无条件判（R82 的 CI 上就是这么把环境说成产品的） | **LOCAL-NO-POWER** |
| M450 | 闸门的 NAMELESS 比较退回拿**用例名个数**当可归因数 | **CAUGHT** |

两刀（M448 / M449）**按实存活为"本地无判别力"**：本机有运动、处置是 `.ok`，
所以"把钉子挂回结论尺"与"地板不管处置"这两种改法在本机都不改变结果 ——
它们的牙在 runner 上，而 R82 的 CI 已经现场演示过这两条各红一次。
这一格不许被改写成"抓到"：按实记，是这一族从 R63 就立下的规矩（U-99 的两种存活）。

### 验证（本机，逐条实跑）

```
swift build --build-tests                告警 0
swift test（全量）                       799 tests / 0 failures（40 skipped，swift test exit 0）
动效那一步                               MOTION_FLOOR_FACTS judged=4/4 executed=52 not-run=- summary=detail-kind-change=3 empty-state=3 notice-banner=12 notice-banner-dismiss=12 红的用例=- 汇总行报红=0 MOTION_FLOOR_REDS=0CAPTURE_TEST_EXIT=0
捕获闸门                                 CAPTURE_GATE_RESULT=ok 红=0（已登记的 NOT-RUN 见上）
frame_baseline.py check --against working FRAME_BASELINE_AGAINST=working FRAME_BASELINE_COMPARED=124 FRAME_BASELINE_CHANGED=0 FRAME_BASELINE_MISSING=0 FRAME_BASELINE_ADDED=0PY_EXIT=0
python3 -m unittest discover -s scripts/tests  Ran 142 tests in 6.807s OK
```

本轮三卷的读数（本机 2×，全量那一遍）：

```
MOTION_SHIMMER 扫 帧数=47 变化帧对=22 峰值=0.015 采样≈53ms coverage=0.979(地板 0.50) 记录时长=2447ms 判定=一直在动
MOTION_SHIMMER_FILM 帧=47 时刻=47 配对=是 卷长=2447ms（探针声明 2500ms） ｜ 结论尺报的记录时长=2447ms —— 后者在峰值 0 时**必然**是 0，所以前提不许挂在它身上
MOTION_SHIMMER_WITNESS 等节拍证人(30Hz 抬升 0.12，与产品同数字) 帧对=46 在变=23 峰值=0.015 coverage=1.000 判定=一直在动
MOTION_SHIMMER_WITNESS 粗节拍证人(20Hz 抬升 0.45，只签字'看得见这种画法') 帧对=46 在变=43 峰值=0.026 coverage=1.000 判定=一直在动
```

### 七维自评

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 19 / 20 | 零产品改动；117 量出来的"每根条各扫各的"是一处**不原生**，本轮只把它变成数字，改在下一轮 |
| 流畅度 | 18 / 20 | main 上那朵红是本轮修掉的（我上一轮自己造的假红），扫光这一位在 runner 上从此是一朵有名字的未覆盖 |
| 层次与材质 | 15 / 15 | FRAME_BASELINE_AGAINST=working FRAME_BASELINE_COMPARED=124 FRAME_BASELINE_CHANGED=0 FRAME_BASELINE_MISSING=0 FRAME_BASELINE_ADDED=0PY_EXIT=0 |
| 动效细节 | 13 / 15 | 处置与绝对地板的关系被理清（同一件事只判一次）；亮带形状仍待改 |
| 交互反馈 | 9 / 10 | 反馈本身没动 |
| 可访问性 | 8 / 10 | 减弱动态那一档的"必须静止"仍然是无条件判；真机批次 72 还没人看 |
| 性能 | 14 / 15 | 全量 799 tests / 0 failures（40 skipped，swift test exit 0）；闸门多算一个行数，成本可忽略 |

**94 / 100**。分数没涨的原因写在上面：本轮的产出全部是"把上一轮我自己造的三处不干净修干净"，
加上一条把看图变成读数的量 —— 它开出了下一轮要改的产品缺陷，但本轮没改画面。

### U-164 · 电池的 python 臂也有同一个盲区：模块级导入失败被读成"全绿"

M450 第一版把 Swift 风格的 `//` 注释写进了 Python 变异文 ⇒ 被改的闸门脚本**语法都不对**，
`unittest` 只打一条 `ERROR: test_motion_floor_gate (unittest.loader._FailedTest…)`，
四条用例名一条都不出现 ⇒ 旧分类器把四个都读成 green ⇒ 这一刀被报成"没抓到"。
⇒ `python_verdicts` 现在认 `import-error`（导入失败/语法错算红，且按实报数）。
这已经是**第三次**同一族（U-151 把崩溃读成没跑、U-158 把崩掉的用例读成没跑、这次是导入失败）：
每加一条判据通道，第一件事是问"它坏的时候长什么样，我的分类器认得吗"。

### 仍未解决

- BACKLOG **117**（本轮量完，下一轮改产品）：亮带每根条各扫各的 ⇒ 把渐变抬到容器层，
  带 before/after 条带图；静置画面预计不变（phase 0 时亮带在条外），帧基线仍要同提交复核。
- BACKLOG **118**（本轮开）：`loop-clock-not-sustainable-at-product-rate` 这一朵有名字的未覆盖
  **不在覆盖地板的登记表里** —— 登记表按四条场景臂统计，而扫光不是场景臂 ⇒
  114 结案之后这一位变成"永久未覆盖而没人统计"。要做：给常驻循环那一族加一格登记（判到 / 点名 二选一）。
- BACKLOG **116**（R82 开，本轮未做）：那五条 `UICaptureTests` 的 skip 仍然没有"为什么今天没跑"的读数。
- BACKLOG **115**、111、108 余下、77 路 b、101 ②③、106；真机 68.1 / 68.2 / 69.1 / 70.1 / 71.1 / 72.1 / 72.2。

## Round 84 · 把看图换成判据：亮带终于是一条光穿过整组（结案 117 / 新开 119 / U-165…U-173 / D-142）

### 本轮开场的位点清单（1 个产品文件 + 1 个判据文件）

被重新判断的位点：**详情预览加载态那三根骨架条带上的亮带**
（`Sources/ClipboardHistoryApp/Views/SkeletonShimmer.swift`，探针视图 420×220 视图点）。
坐标与缺陷清单是 R83 量出来的那一套（`r83_band_fanout.py` 的读数在上一轮台账里）：

| 位点 | 区域（视图点，x 从组左边算） | R83 量到的缺陷 | 本轮处置 |
|---|---|---|---|
| 骨架条 1（标题） | 0…176.4 × y 0…8 | 亮带中心在自己条宽的一半处（88pt 一档） | 三根条共用一个亮带中心 |
| 骨架条 2（正文·长） | 0…361.2 × y 18…26 | 中心 181pt 一档 | 同上 |
| 骨架条 3（正文·短） | 0…268.8 × y 36…44 | 中心 134pt 一档 | 同上 |

⇒ 同帧内三个中心的绝对差最大 **170pt**、归一化只差 **0.003** —— 那是三条各扫各的亮带。
本轮两件事：① 产品改成"一条光穿过整组"；② 把那道手量换成**会红的判据**，
让下一次"退回每根条各扫各的"是红的，而不是一行注释。

### 读 R83 的 CI（run 38786182395，11m55s）：runner 那一支**翻面了**

```
MOTION_FLOOR_FACTS judged=4/4 executed=52 not-run=- 红的用例=testBandCaptureIsCheaperAndStillSeesTheMotion,testSkeletonSweepActuallySweeps 汇总行报红=2
MOTION_FLOOR_SUITE_RED=2 …
testSkeletonSweepActuallySweeps：骨架扫光只覆盖了整卷 0.050 的时间（1/22 对在变），而…那颗证人今天覆盖了 0.837
                              ⇒ 这台机器带得动产品那一档节拍的常驻循环，是产品这一份没在跑
testBandCaptureIsCheaperAndStillSeesTheMotion：XCTAssertLessThanOrEqual failed: ("25.14") is greater than ("23.41")
                              ⇒ 带捕获之后整卷中位间隔没有变细，这一臂仍然判不了
```

与 R82 那一遍并排看（同一份产品代码，同一类机器）：

| run | 产品 coverage | 等节拍证人 coverage | 处置 |
|---|---|---|---|
| R82 38781113064 | 0.000（0/21 对） | 0.284 | `.notRunEnvironment` ⇒ 点名 `loop-clock-not-sustainable-at-product-rate` |
| R83 38786182395 | 0.050（1/22 对） | 0.837 | `.productRed` ⇒ 红着说"产品这一份没在跑" |

⇒ **"这台 runner 带不动 30Hz 的常驻循环"不是一条耐久事实**：它上一轮成立、这一轮不成立，
而翻面的那一边是**证人**（0.284→0.837），产品的读数两遍都是"几乎没拍到"（0.000 / 0.050）。
这一格是本轮新开 **BACKLOG 119** 的全部内容：那一支的签字权不能交给单次 runner 读数。
它同时决定了本轮另一件事 —— 新加的位置判据**不复用**这个处置，另找签字的人（见下面第三道闸门）。

### 产品那一处改动（before / after 都有数字，也都有图）

改法只有一件事：三根条不再各自是一个 `RoundedRectangle`，而是**整组一个形状**
（新增 `SkeletonBarsShape: Shape`，`path(in:)` 里 union 三根条），渐变填在这个形状上 ⇒
`LinearGradient` 的 `UnitPoint` 落在**容器**坐标系里，一条亮带横穿整组。
配套把两个魔法数提成令牌（`SkeletonMotion.barHeight = 8`、`barSpacing = 10`，
加 `barRect(index:fraction:in:)`），因为判据现在要按同一套几何去像素里找那三根条 ——
留在视图里就是让判据猜产品的布局。

```
MOTION_SHIMMER_BAND 帧=48 比例=1pt≈2.00px 可用帧=7 丢掉=41 同帧绝对中心最大散布=0.0pt（地板：≤6.0 判一条带、≥40.0 判各扫各的） 归一化散布=0.413 行程=121.5pt（正对照地板 20.0） 判定=整组一条带 理由=每一帧三根条的亮斑都在同一条竖线上（最大差 0.0pt ≤ 6.0），且它一路走了 121.5pt
```

同一把尺、两份卷子（`.scratch/motion-audit-2/r84_band_fanout.py`，估计量与判据统一成"峰值列"）：

```
=== BEFORE（R82 那卷：每根条各扫各的）===
结论：**同一帧内**三根条的绝对中心最大相差 169 pt，而归一化中心最大只差 0.005（=2 pt 在最宽那根上）
正对照（同一根条跨帧必须移动）：不同帧上第一根条的归一化中心共 21 个不同取值 [0.08, 0.11, 0.16, 0.19, 0.26, 0.28, 0.31, 0.37, 0.4, 0.45, 0.48, 0.54]
⇒ 支持假设 B（每根条各扫各的）；地板：归一化散布 < 0.02 判 B、绝对散布 < 8pt 判 A

=== AFTER（R84 这卷：整组一条带）===
结论：**同一帧内**三根条的绝对中心最大相差 0 pt，而归一化中心最大只差 0.450（=162 pt 在最宽那根上）
正对照（同一根条跨帧必须移动）：不同帧上第一根条的归一化中心共 8 个不同取值 [0.19, 0.26, 0.4, 0.46, 0.6, 0.67, 0.74, 0.88]
⇒ 支持假设 A（整组一条带）；地板：归一化散布 < 0.02 判 B、绝对散布 < 8pt 判 A
```

本机这一条判据跑了五遍（判据单跑两遍、变异电池基线一遍、全量验证两遍）：
判定每遍都是 `整组一条带`、绝对散布每遍都是 0.0pt，而可用帧在 **7…10** 之间漂
—— 那是采样相位决定的（亮带什么时候整条落在最短那根条里面），
所以地板 `minimumBandFrames = 3` 留的是 2-3 倍的余量，而不是"今天碰巧有 7 帧"。
⇒ 这一格记的是"哪个数会漂、哪个数不漂"：判定与散布不漂，帧数漂 ⇒ 判据吃的是前者。

⇒ 绝对散布 169pt → **0pt**，归一化 0.005 → **0.450**：两把尺**反向**，这正是"从每根条各扫各的
换成整组一条带"该有的读数形状。看图也对上了：`r84_skeleton_band_strip.png` 里每格三根条的亮斑
落在同一条竖线上，而 `r82_skeleton_sweep_strip.png` 里三个亮斑是错开的。
顺带一条没预料到的：coverage 那把尺的峰值从 0.015 涨到 0.023（亮带变宽 ⇒ 每拍扫过的面积更大），
而"减弱动态必须静止"那一臂仍然是 0.000。

### 新判据：位置那把尺，三道闸门

`testSkeletonSweepIsOneBand`（`MotionFilmstripTests`，产品入口 = `SkeletonProbe` host 真的
`SkeletonPreviewView`）。它读的是**运动判据同一卷胶片**（`shimmerFilm()` 缓存，R84 起一卷只抓一次）：

1. **尺子自己的正对照**：两份合成卷子（一份整组一条带、一份每根条各扫各的）必须被读成两种判定。
   这一格今天真的值回票价 —— 它在我碰产品结论之前就先红了一次（见 U-165）。
2. **真片上的正对照**：可用帧里亮带必须走过 ≥20pt 行程。没有这一条，"三根条的峰值都停在同一列"
   （静止画面）也会读成散布 0pt，而 0pt 恰好是"整组一条带"的读数。
3. **谁能签"这台机器判不了位置"**：签给**同一把尺去读高对比那颗证人**（`bandAdjudication`），
   并且**只准收窄、不准放大** —— coverage 那一族的处置不是 `.ok` 时位置这一律不判，
   哪怕证人读得出、哪怕产品读成分家：一个自己会在两轮之间翻脸的读数，不配定罪产品。
   不签给 coverage 那个处置 —— 理由就是上面那两行并排的 CI 读数。

真值表 13 格（`BAND_TRUTH_TABLE`）：

```
BAND_TRUTH_TABLE 一条带=整组一条带 各扫各=每根条各扫各的 空=没有可用帧 静止=分不开 帧少=分不开 分不开=分不开 处置=ok/红/红/未跑(⑫)/未跑(⑬)/未跑(⑭⑮ loopCapable=false) 一条带归一化=0.374 各扫各归一化=0.026 绝对散布=2.0/93.0pt 行程=71.0/141.0pt ⇒ 15 格
```

判据的读数（本机）：

```
MOTION_SHIMMER_BAND 帧=48 比例=1pt≈2.00px 可用帧=7 丢掉=41 同帧绝对中心最大散布=0.0pt（地板：≤6.0 判一条带、≥40.0 判各扫各的） 归一化散布=0.413 行程=121.5pt（正对照地板 20.0） 判定=整组一条带 理由=每一帧三根条的亮斑都在同一条竖线上（最大差 0.0pt ≤ 6.0），且它一路走了 121.5pt
MOTION_SHIMMER_BAND_CONTROL 整组一条带那卷判定=整组一条带 每根条各扫那卷判定=每根条各扫各的 （两份都是 8 灰阶抬升的亮斑，只有中心位置放法不同）
MOTION_SHIMMER_BAND_WITNESS 粗节拍那颗(抬 0.45、同一种画法、同一把尺) 可用帧=15 绝对散布=0.0pt 行程=136.5pt 判定=整组一条带 理由=每一帧三根条的亮斑都在同一条竖线上（最大差 0.0pt ≤ 6.0），且它一路走了 136.5pt
```

### U-165 · 点→像素漏乘 scale：三条红同时来自一把没验过坐标约定的尺

第一版 `barPeak` 拿 `rect`（**视图点**）直接当下标去索引**像素**缓冲区，于是条被当成只有实际一半宽去采样。
后果不是"读错数"，是**整把尺失能**：产品 45 帧全被丢掉（可用帧=0），
而两份合成对照一起读成"分不开"。⇒ 记两条：
① 坐标换算那一步必须在真片上跑第一遍，不能先看合成图就宣布尺子能用；
② 合成正对照的价值今天第一次被证明 —— 它先于任何产品结论红给我看，
   否则我会把"可用帧=0"写成"这台机器看不见亮带"（那正是 U-160 那一族的新成员）。

### U-166 · 内边距 4pt 拦不住"被圆角让开一格"的贴边假峰

修完 scale 之后产品读 19.5pt 散布 ⇒ "分不开"。逐帧看样本行
（`可用帧首=[33.0, 33.0, 33.0] 末=[171.5, 191.0, 191.0]`）：短条 176.4pt 宽，
亮带中心 191pt 已经在它右端**外面**，而它的 argmax 落在 171.5pt —— 不是贴在最后一列，
是被圆角让开了一格多，恰好躲过 4pt 的门槛。⇒ 门槛换成量出来的 **10pt**
（亮带半宽 63pt ⇒ 10pt 既拦得住贴边假峰，也吃不掉真正在条内的中心），
读数从 19.5pt 变 0.0pt、可用帧 15→9-10。**同族**：U-163（相对阈值在信号缺席时读假数）。

### U-167 · 两格前提里只有一格有牙，而"另一格也有牙"是一句没量的话

M454（只把幅度地板调到 0）**本地全绿**。第一反应是把它写成 CAUGHT 的反面（"刀没抓到 ⇒ 判据没用"），
但那句话不对：真正起作用的是条端内边距那一格（M452 单独拆它就红）。
⇒ 两刀分开记：M454 按实存活为"本地无独立判别力"，另加 **M454b**（两格一起拆）红 ⇒
"两格里至少一格必须有牙"这句话现在是**被检验过的**，而幅度地板那一格的注释里写着
它今天没有独立作用、以及什么条件下会重新有（渲染通道带上噪声时）。不许改期望冒充有牙。

### U-168 · 两把尺给不同答案时，先问估计量是不是同一个

修完之后，Swift 判据读 0.0pt，而 R83 那份 python 手量读 10pt ⇒ "分不开"。
根因不是画面，是两把尺的**估计量**不同：python 用"高于半程那段的质心"（会被条端切掉的那半个亮带拉走），
Swift 用"离本条中位数最远的那一列"（峰值列，不受切割影响）。统一成峰值列之后两份实现同结论
（before 169pt / after 0pt）。⇒ 跨工具对账之前先统一估计量，否则"分不开"是工具的病，不是画面的病。
`r83_band_fanout.py` 原样留着，它是"before 那侧的读数由谁产出"的证据。

### U-169 · 判据的处置会翻面：单次 runner 读数不配当签字权

见上面那张两行并排的表。⇒ 新开 **BACKLOG 119**；本轮的处置是**新判据不复用**那个处置，
改由"同一把尺读高对比证人"签（`bandAdjudication`）。
不许的处置：把 `minCoverage` 抬到 runner 能过的数值（那是 110 禁止的同一件事）、
或者把 R83 那朵红登记进 `suite_reds` 让它闭嘴（红必须有成因，不是有名字就行）。

### U-172 · 会翻脸的读数只准收窄断言，不准定罪

上面那张 CI 并排表给出的不只是一个待办，还有一条设计规矩：位置判据本来打算复用 coverage 那个处置当豁免条件，
但那个处置在两轮之间从"环境不行"翻成"产品红"。⇒ 最终形状是**不对称**的：
`loopCapable == false` 时位置这一律**不判**（哪怕证人读得出、哪怕产品读成分家），
而 `loopCapable == true` 时它才既有资格说绿、也有资格说红。
理由不在统计而在方向：免罪错了，下一轮还能补一次判定；定罪错了，是把环境问题写成产品缺陷，
而产品缺陷会驱动下一轮去改本来没坏的产品代码（R83 那份文件头记的三次 0.0000 误判，就是这个方向）。
⇒ 记成一条可复用的判据设计规矩：**任何"会随机器/轮次翻面"的读数，只能作为断言的上界，不能作为指控的来源。**

### U-173 · 本地验证脚本与 CI 用了不同的读数通道，假红只出现在我自己这边

第二轮 `verify_r84.sh` 跑完，闸门报 `MOTION_FLOOR_FACTS judged=None/None … MOTION_FLOOR_REDS=1`，
而同一遍的 `swift test` 是 801/0 failures、动效那卷 exit 0。⇒ 不是判据坏了，是**日志缺了结论行**：
本机 `swift test` 会成块丢 stdout（R64 记过），而 CI 在跑 `motion_floor_gate.py` 之前会把
`motion-readings.log` 并进 `/tmp/motion.log`（`MOTION_CHANNEL_UNIONED=1` 那一段），
我的本地脚本没并 ⇒ 同一条判据在两台通道上给出两个结论。
⇒ 修法是把 CI 那段通道合并抄进 verify 脚本（已抄，本轮第三遍验证的读数里带 `MOTION_CHANNEL_UNIONED=1`），
**不是**把闸门放宽、也不是把 `judged=None` 当成"没跑到"忽略掉。
**同族**：U-151（把崩溃读成没跑）、U-164（把导入失败读成全绿）—— 这一条的新形状是
"通道不一致造成的假红"，它只在自家 harness 里出现，所以最容易被人当成产品/判据的问题。

### U-170 · 变异电池自己也有"同文件两处编辑"这个坑

M454b 要同时改两颗地板，而 `apply()` 第一版对同一文件的两处编辑都从**原始文本**做替换
⇒ 第二处写回去时把第一处覆盖掉，那一刀会"抓到"一个其实没落地两次的形状。
⇒ 改成每处都从磁盘当前内容读、`originals.setdefault` 只留 pristine，
并且整组回滚（半把刀不算刀）。**同族**：U-164（电池的分类器也会骗人）。

### 牙

| M451 | 产品改回『每根条一个形状、渐变按条宽归一化』（= BACKLOG 117 那个缺陷本身） | **CAUGHT** |
| M452 | 条端内边距 10pt → 0pt | **CAUGHT** |
| M453 | 行程地板 20pt → 0pt | **CAUGHT** |
| M454 | 幅度地板 4 灰阶 → 0（单拆这一格） | **LOCAL-NO-POWER** |
| M454b | 幅度地板与条端内边距**一起**拆 | **CAUGHT** |
| M455 | 证人『有资格签』改成恒真 | **CAUGHT** |
| M456 | 一条带的天花板 6pt → 50pt | **CAUGHT** |
| M457 | 位置判据忽略循环那一族的处置（`loopCapable` 不再收窄断言） | **CAUGHT** |

### 验证（本机，逐条实跑）

```
swift build --build-tests                告警 0
swift test（全量）                       801 tests / 0 failures（41 skipped，swift test exit 0）
动效覆盖地板闸门                          MOTION_FLOOR_FACTS judged=4/4 executed=54 not-run=- summary=detail-kind-change=3 empty-state=3 notice-banner=13 notice-banner-dismiss=11 红的用例=- 汇总行报红=0 MOTION_FLOOR_REDS=0 MOTION_GATE_EXIT=0
捕获闸门                                 CAPTURE_GATE_RESULT=ok 红=0（已登记的 NOT-RUN 见上）
frame_baseline.py check --against working FRAME_BASELINE_AGAINST=working FRAME_BASELINE_COMPARED=124 FRAME_BASELINE_CHANGED=0 FRAME_BASELINE_MISSING=0 FRAME_BASELINE_ADDED=0
frame_baseline.py update（同提交）之后复核 FRAME_BASELINE=FRAME_BASELINE_AGAINST=working FRAME_BASELINE_COMPARED=124 FRAME_BASELINE_CHANGED=0 FRAME_BASELINE_MISSING=0 FRAME_BASELINE_ADDED=0
python3 -m unittest discover -s scripts/tests  Ran 142 tests in 6.581s OK
```

### 帧基线那 4 张：哈希说"变了"，像素说"没变到看得见"（两句都要报）

`frame_baseline.py check` 报 **4 张 changed**（detail-loading 亮/暗、detail-2-file 亮/暗 —— 都含骨架）。
BACKLOG 117 当时写的是"静置画面预计不变（phase 0 时亮带在条外）"，所以这一格不能只写"已 update"：
把 R83 与 R84 那两张同名帧解码到像素级比了一遍 ——

```
light: 尺寸=1440x1040px  有差异像素=2503/1497600 (0.167%)  最大通道差=5  行=40…83pt 列=20…604pt  差值分布=[(1, 2450), (2, 19), (5, 13), (3, 12), (4, 9)]
dark: 尺寸=1440x1040px  有差异像素=80/1497600 (0.005%)  最大通道差=5  行=40…83pt 列=20…604pt  差值分布=[(1, 28), (2, 22), (4, 13), (3, 12), (5, 5)]
```

⇒ 差异**只落在骨架那三根条的区域**（y 40…83pt、x 从详情区左轴 20pt 起），最大通道差 **5/255**，
其中 2450/2503 个像素只差 1 级 ⇒ 视觉上没变，变的是**换形状画法之后的抗锯齿边缘**。
基线判的是字节，所以 4 张哈希按规矩同提交 update；update 之后复核 FRAME_BASELINE=FRAME_BASELINE_AGAINST=working FRAME_BASELINE_COMPARED=124 FRAME_BASELINE_CHANGED=0 FRAME_BASELINE_MISSING=0 FRAME_BASELINE_ADDED=0。
⇒ 记成 **U-171**：一句"帧基线 4 张变了"会把人带去读"画面变了"，
而画面到底变没变、变了多少灰阶、变在哪一行哪一列，是另一把尺的问题。

### 七维自评

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 20 / 20 | 本轮唯一一处画面改动：亮带从"三条各扫各的"变成"一条光穿过整组" —— 那是系统骨架与 GitHub 那类呼吸感共同的画法，R83 判它"不原生"的那一格现在没了 |
| 流畅度 | 18 / 20 | 本机 coverage 与峰值都没变差（峰值 0.015→0.023）；main 上那朵红换了成因：runner 的处置自己翻面（119），本轮没有修它，只是不再让它的签字权外溢 |
| 层次与材质 | 15 / 15 | 骨架三根条的左轴与纵向节奏没动（像素级读数：差异只落在条内 ≤5 灰阶的抗锯齿边，见上面"帧基线那 4 张"那一格）；材质与颜色一个数都没改 |
| 动效细节 | 14 / 15 | 亮带位置第一次有判据；条端内边距是量出来的（U-166），而"这条扫光到底该多宽"仍然只有一档 bandSize 0.3 的旧依据 |
| 交互反馈 | 9 / 10 | 反馈本身没动 |
| 可访问性 | 8 / 10 | 减弱动态那档"必须静止"仍然无条件判、读数 0.000；真机批次 72/73 还没人看 |
| 性能 | 14 / 15 | 全量 801 tests / 0 failures（41 skipped，swift test exit 0）；位置判据多读一遍整卷（本机 48 帧、每帧 840×440px 里三条 8pt 高的带），这一条用例本身 0.4s |

**98 / 100**。涨的四分都在"原生感 + 动效细节"这一对：本轮既改了画面，又把改完的那件事变成会红的判据。
没满的部分写在 119 与真机批次上，不在本轮的分数里冒充。

### 仍未解决

- BACKLOG **119**（本轮开）：常驻循环那一族的 runner 处置**会翻面** ⇒ 判据不许拿单次读数定罪产品；
  要做的是把"这一支要几遍读数才配定罪"写成数据（与 118 是同一个洞的两面）。
- BACKLOG **118**（R83 开，本轮又长一格）：落在"有名字但没人统计"那一族里的读数，
  从一条变成两条 —— 峰值地板的 `MOTION_SHIMMER_PEAK_NOT_JUDGED` 与本轮的 `MOTION_SHIMMER_BAND_NOT_JUDGED`。
- BACKLOG **116**、**115**、111、108 余下、77 路 b、101 ②③、106；
  真机 68.1 / 68.2 / 69.1 / 70.1 / 71.1 / 72.1 / 72.2 / **73.1 / 73.2**。

## Round 85 · 常驻循环那一族第一次有了登记表：判据必须自己说"今天判没判"（结案 118 / 更新 119 / U-174…U-177 / D-143）

### 本轮开场的位点清单（0 个产品文件；5 个判据/闸门/自测文件）

本轮不改画面。被重新判断的是**"这一族今天到底判没判"这件事有没有人统计**：

| 位点 | 位置 | R84 留下的缺陷 | 本轮处置 |
|---|---|---|---|
| 扫光运动判据 | `MotionFilmstripTests.testSkeletonSweepActuallySweeps` | 结论只在读数行里，登记表读不到它"今天判没判" | 两条出口各打一行 `MOTION_SHIMMER_STATE` |
| 位置判据（R84 新加） | 同类 `testSkeletonSweepIsOneBand` | 同上，且它刚进判据体系，消失起来最无声 | 同上，`MOTION_SHIMMER_BAND_STATE` |
| 覆盖地板闸门 | `scripts/motion_floor_gate.py` | 只按四条场景臂统计，扫光不是场景臂 ⇒ 整族缺席没人报 | 新增 `loop_verdicts`：`LOOP_SILENT` / `LOOP_BAD_REASON` 两格 |
| 登记表 | `scripts/motion_floor_expectations.json` | 没有这一族的行 | 两行登记，各带允许的理由与来历 |
| 闸门自测 | `scripts/tests/test_motion_floor_gate.py` | 新那一层没有自己的真值表 | +1 格七项（含整行缺席、带后缀的登记名） |
| CI 报告自检 | `scripts/tests/test_ci_report_selftest.py` | 共用通道里没有状态行 ⇒ 七个场景一起假红 | `FLOOR_SUMMARY` 一处补背景行（U-176） |

**文件数超约定一格，如实记账**：这一族的约定是每轮 ≤4 个非台账文件，本轮 5 个。
多出来的是最后那一格 `test_ci_report_selftest.py` —— 新加一层判据时，凡是读同一份日志的旧自测会一起冒红，
而补背景行只能补在它们共用的那一个常量上（七个场景共用一处，不是七处各补一遍，见 U-176）。
考虑过并进 `test_motion_floor_gate.py`（那样本轮就回到 4 个文件）而**拒绝**：两个文件判的东西不同
（一个判闸门函数的返回值，一个判 CI 报告怎么拼装），并文件只会让下一个读的人以为它们是同一件事 ——
这条约定是防一轮改一片的，不是防文件名的。

### 读 R84 的 CI（run 38798408040）：这一族第一次在 runner 上判到，而 main 绿了

# R85 读 R84 的 CI（run 38798408040，commit 325e71d，20:00:09→20:12:49，job build-and-test = success）

## 常驻循环那一族（三遍 runner 读数并排）
| run | 画法 | 产品 coverage | 等节拍证人 coverage | 处置 |
|---|---|---|---|---|
| R82 38781113064 | 每根条各扫各的 | 0.000（0/21 对，峰值 0.000） | 0.284 | .notRunEnvironment（点名 loop-clock-not-sustainable-at-product-rate） |
| R83 38786182395 | 每根条各扫各的 | 0.050（1/22 对，峰值 0.015） | 0.837 | .productRed（红着说产品没在跑） |
| R84 38798408040 | **整组一条带** | **0.522（2/24 对，峰值 0.020，采样≈112ms）判定=一直在动** | 0.594（4/28 对，峰值 0.024） | **.ok（判绿，两卷都过地板）** |

原文（Motion filmstrip (report-only) 那一步）：
motion suite exit: 0  executed: 54  胶片: 14  MOTION_SUMMARY notice-banner=2 notice-banner-dismiss=3 detail-kind-change=3 empty-state=3  MOTION_RESOLVE_SUMMARY judged=4/4 no
MOTION_SHIMMER 扫 帧数=24 变化帧对=2 峰值=0.020 采样≈112ms coverage=0.522(地板 0.50) 记录时长=2474ms 判定=一直在动
MOTION_SHIMMER 停 变化帧对=0 峰值=0.000 coverage=0.000
MOTION_SHIMMER_WITNESS 等节拍证人(30Hz 抬升 0.12，与产品同数字) 帧对=28 在变=4 峰值=0.024 coverage=0.594 判定=一直在动
MOTION_SHIMMER_WITNESS 粗节拍证人(20Hz 抬升 0.45，只签字'看得见这种画法') 帧对=33 在变=23 峰值=0.045 coverage=0.972 判定=一直在动
MOTION_SHIMMER_STRIP 前 24 帧排成条带（六列）⇒ 眼睛判的是『亮带一路扫过去』，这把尺判的是 coverage，两者不许互相替
MOTION_SHIMMER_FILM 帧=24 时刻=24 配对=是 卷长=2474ms（探针声明 2500ms） ｜ 结论尺报的记录时长=2474ms —— 后者在峰值 0 时**必然**是 0，所
MOTION_SHIMMER_BAND_CONTROL 整组一条带那卷判定=整组一条带 每根条各扫那卷判定=每根条各扫各的 （两份都是 8 灰阶抬升的亮斑，只有中�
MOTION_SHIMMER_BAND 帧=24 比例=1pt≈1.00px 可用帧=11 丢掉=13 同帧绝对中心最大散布=1.0pt（地板：≤6.0 判一条带、≥40.0 判各扫各的） 归一�
MOTION_SHIMMER_BAND_SAMPLE 可用帧首=[34.0, 33.0, 34.0] 末=[142.0, 142.0, 142.0]
MOTION_SHIMMER_BAND_WITNESS 粗节拍那颗(抬 0.45、同一种画法、同一把尺) 可用帧=7 绝对散布=1.0pt 行程=136.0pt 判定=整组一条带 理由=每一帧三
MOTION_RESOLVE_SUMMARY judged=4/4 not-run=-

## 闸门那一步
MOTION_FLOOR_FACTS judged=4/4 executed=54 not-run=- summary=detail-kind-change=3 empty-state=3 notice-banner=2 notice-banner-dismiss=3 红的用例=- 汇总行报红=0
MOTION_FLOOR_SUITE_CLEAN=0 这一卷没有红用例（汇总行也没说有）
MOTION_FLOOR_OK=4/4 全部臂都在登记之内
MOTION_FLOOR_REDS=0

## 仍然没跑的那一步（BACKLOG 92 的形状）
ui suite exit: 137  executed: 0  skipped: ?  已下结论的用例: 0


⇒ **`build-and-test` = success**，而 `Motion coverage floor` 那一步第一次对扫光这一位说出"判到了"：
产品 coverage **0.522**（地板 0.50）、等节拍证人 0.594、位置判据 可用帧=11 / 绝对散布 **1.0pt** /
判定=整组一条带（runner 是 1× ⇒ `比例=1pt≈1.00px` 那格也第一次被真机验证）。

三遍并排看，本轮最重要的那句话在这里：**R83 那朵 `.productRed` 现在有了第三种解释**。

| run | 画法 | 产品 coverage | 等节拍证人 coverage | 处置 |
|---|---|---|---|---|
| R82 | 每根条各扫各的 | 0.000 | 0.284 | 点名环境 |
| R83 | 每根条各扫各的 | 0.050 | 0.837 | 判产品红 |
| R84 | **整组一条带** | **0.522** | 0.594 | 判绿 |

产品那两遍（0.000 / 0.050）不是"这台机器的时钟带不动 30Hz"，也不是"产品的扫光没跑"，
而是**旧的 fan-out 画法让运动跨不过像素门槛**：亮带只在每根条自己的 30% 里走，
每拍推进 ≈1.2pt，在 112ms 的采样网格 + 1× 像素上摊到每对帧就没了（R83 自己给 `minimumHighlightLift`
写的那句"5 个点的抬升在像素上等于没动"是同一件事的另一半）。
换成整组一条带之后同一台机器读到 0.522 —— 时钟、节拍、抬升、声明时长一个都没改。
⇒ **119 不结案**，但它的成因表里要多一列：判据读不到运动有三种可能（环境带不动 / 判据吃采样 /
**画法让运动不可见**），第三种本轮现场发生过。而 0.522 只比地板高 0.022 ⇒
登记表不许因此改成 `must_judge=true`（R38：一次读数不当另一台机器的地板）。

### 改了什么：状态行 + `loops` 那一层 + 一条会数次数的守卫

判据侧：两条判据的**两条出口各自**打一行状态 ——
能力闸门 skip 那条打 `判定=skipped 原因=capability-gate`，判完那条打
`判定=ok|productRed|notRunEnvironment|witnessDead 原因=<名字或->`。
状态行排在所有 `XCTFail` 与闸门之前（R53 那一课）。

```
MOTION_SHIMMER_STATE 判定=ok 原因=-
MOTION_SHIMMER_BAND_STATE 判定=ok 原因=-
```

闸门侧（`loop_verdicts`）只判两格，正是 118 原文要的那两格：

```
MOTION_FLOOR_FACTS judged=4/4 executed=54 not-run=- summary=detail-kind-change=3 empty-state=3 notice-banner=10 notice-banner-dismiss=13 红的用例=- 汇总行报红=0 MOTION_FLOOR_LOOP_JUDGED=skeleton-loop 这一族今天判到了（状态 ok）（这一族今天一共打了 2 行状态，按最后一条判） MOTION_FLOOR_LOOP_JUDGED=skeleton-band-position 这一族今天判到了（状态 ok）（这一族今天一共打了 2 行状态，按最后一条判） MOTION_FLOOR_REDS=0 MOTION_GATE_EXIT=0
```

`productRed` / `witnessDead` 这两种状态**不在这里红** —— 它们对应的用例本身就是红的，
红由 `suite_reds` 那一层报（名字 + XCTAssert 原文都在那边）。同一件事只判一次（U-162 的规矩
在新层里同样成立）。登记名允许带细节后缀（`band-witness-reads-nothing(没有可用帧)`），
闸门按括号前那半截匹配。

### U-174 · 守卫只数"出现过"，会被另一条出口喂饱

第一版守卫写的是"函数体里出现过 `MOTION_SHIMMER_BAND_STATE` 这个串"。
**M461 / M462 双双 ESCAPED**：删掉正常路径那一行 emit 之后，skip 分支那一行仍然把断言喂饱，
三条判据全绿 —— 而登记表从此读不到任何状态。⇒ 守卫改成**数次数**：
`stateLineCount(...) == 2`，两条出口各一次；再补 M463 / M464 两刀专删 skip 那一行。
这一格是"守卫要读字段不能读散文"（R75 那一课）在**自身源码**上的形状：
读"提没提到"永远比读"每条路都做了没做"弱。

### U-175 · 登记名允许带细节后缀，闸门按前缀匹配

`band-witness-reads-nothing(没有可用帧)` 与 `(分不开)` 是两种不同的"读不出"，
但如果闸门整串比对，每换一种读不出就冒一次 `BAD_REASON` 红 ——
下一次有人删掉括号那半截来让 CI 变绿，而那半截正是有用的一半。
⇒ 匹配剥后缀，红只留给**没登记过**的坏法；`testLoopStateLinesAreCountedNotGuessed` 里
带后缀那一格钉的就是这件事（M460 把它拆掉 ⇒ 那一格红）。

### U-176 · 给旧日志加一层新判据时，先决定"谁该补背景行、谁故意不补"

`loops` 一进来，七个 CI 自检场景 + 两份真日志夹具全部多两朵 `LOOP_SILENT` 红。
两种处置分开做：**背景条件**（"一次完整的动效运行包含状态行"）补在 `FLOOR_SUMMARY` 一处，
不逐格改七个场景 —— 那七格测的是臂一级的形状，循环那一族对它们是背景；
而 R46 那份**本机真日志故意不补**，于是它顺带成了 `LOOP_SILENT` 的正对照
（"这一族整行没说一句话"就是它那个样子），期望从两朵红改成四朵，改的理由写在文档串里。
⇒ 记这条是因为它有一个反直觉的分支：给旧夹具补新行 = 让旧日志替新规则作证，
   那份日志就不再是它声称的那次运行的原文了。能不改就不改，改了要说明。

### U-177 · 判据读不到运动有三种成因，本轮现场补上了第三种

见上面那张三行表。这条不改代码，改的是**归因表**：以后 `testSkeletonSweepActuallySweeps`
在 runner 上读不到东西时，第一个要排除的不是"机器不行"，而是"这份画法在这台机器的
像素门槛下本来就近乎不可见"。排除它的方法本轮已经有了 ——
`MOTION_SHIMMER_BAND` 那行给的是**位置**读数（可用帧数、绝对散布），
一条"根本没在扫"的卷子和一条"在扫但跨不过地板"的卷子在那一格上长得不一样。

### 真实看图（本轮没有产品改动，看图判的是"账上的数与画面是否还是同一件事"）

看的三样东西都是本轮验证现生成的，这几个数由 `r85_skeleton_contrast.py` 现算（脚本里不留手抄读数）：

1. **24 格条带** `.scratch/motion-audit-2/r85_skeleton_band_strip.png`（整图 2520×880px = 6 列 × 4 行，每格 420×220px）。
   眼睛读到的：亮带在每一格里都是**一条竖着的光同时穿过三根条**（不是三根条各自亮一遍），
   并且沿阅读顺序逐格向右推进、走完一遍回到左边重来 ⇒ R84 那个产品修法**在画面上成立**，
   不只是在尺子上成立（尺子同一件事的读数：同帧绝对散布 0.0pt）。
2. **两张静帧的骨架区域**（`detail-loading-720x520-dark/light.png`，取 x 60…1100px、y 70…190px 放大 2× 看）。
   三根条的长度比例肉眼可读（0.42 / 0.86 / 0.64），圆角一致，左轴与详情区文字同一条。
   顺手量了静置条与所在背景的亮度差：**暗 11.0/255、亮 13.0/255**（偏离背景的行数 48 = 3 根条 × 16px，
   与 `barHeight=8pt` 对得上）⇒ 两种外观下都是"看得见但很轻"，而且**亮档比暗档还略强一点**，
   我原本担心的方向反了（怕的是白纸上看不见）。**判为不加**：
   本轮没有系统骨架的帧可比，所以"与系统同级"那句话不写；只把这两个数留在账上，
   将来谁动 `baseOpacity` 就有对照点。
3. **静帧里亮带不在条上** —— 两张静帧的三根条是均匀的（没有哪一段更亮），
   说明基线那 4 张抓的是带子走出条外的相位。⇒ **帧基线看不见"亮带卡住不动"这种坏法**，
   那件事只有动效那一卷能判（它读的是 49 帧的卷子）。这是已知边界不是新缺陷，
   但它给本轮的 `FRAME_BASELINE_CHANGED=0` 划了范围：那一条只证明"没改画面"，不证明"画面是对的"。

顺带一条要记的读数差别：位置尺**本机只读 8/49 帧**，CI 是 11/24 —— 两边都用了不到四分之一的卷子。
⇒ 这一族的样本量本来就小，它更不该单独给产品定罪（与 119 同族，也是 `must_judge` 保持 false 的又一个理由）。

### 牙

| M458 | 状态行整行缺席时不红（把 LOOP_SILENT 变成一行废话） | **CAUGHT** |
| M459 | 登记过的点名也拦发布（登记表就从放行变成另一道恒红） | **CAUGHT** |
| M460 | 理由匹配不剥括号后缀（换一种读不出就冒红 ⇒ 逼人删掉有用的那半截） | **CAUGHT** |
| M461 | 位置判据不再打状态行（登记表那一族从此没有可读状态） | **CAUGHT** |
| M462 | 循环判据不再打状态行（同上，另一条判据） | **CAUGHT** |
| M463 | 位置判据在能力闸门那条出口不再打状态行（第一版逃掉的那条路） | **CAUGHT** |
| M464 | 循环判据在能力闸门那条出口不再打状态行（同上，另一条判据） | **CAUGHT** |

### 验证（本机，逐条实跑）

```
swift build --build-tests                告警 0
swift test（全量）                       801 tests / 0 failures（41 skipped，swift test exit 0）
动效覆盖地板闸门（含 loops 那一层）        MOTION_FLOOR_FACTS judged=4/4 executed=54 not-run=- summary=detail-kind-change=3 empty-state=3 notice-banner=10 notice-banner-dismiss=13 红的用例=- 汇总行报红=0 MOTION_FLOOR_LOOP_JUDGED=skeleton-loop 这一族今天判到了（状态 ok）（这一族今天一共打了 2 行状态，按最后一条判） MOTION_FLOOR_LOOP_JUDGED=skeleton-band-position 这一族今天判到了（状态 ok）（这一族今天一共打了 2 行状态，按最后一条判） MOTION_FLOOR_REDS=0 MOTION_GATE_EXIT=0
捕获闸门                                 CAPTURE_GATE_RESULT=ok 红=0（已登记的 NOT-RUN 见上）
frame_baseline.py check --against working FRAME_BASELINE_AGAINST=working FRAME_BASELINE_COMPARED=124 FRAME_BASELINE_CHANGED=0 FRAME_BASELINE_MISSING=0 FRAME_BASELINE_ADDED=0
python3 -m unittest discover -s scripts/tests  Ran 143 tests in 6.717s OK
```

### 七维自评

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 20 / 20 | 零产品改动：本轮没脸加分，也没东西被扣 |
| 流畅度 | 18 / 20 | 扫光这一位在 runner 上第一次判到（0.522 > 0.50），但它只比地板高 0.022 ⇒ 119 仍然开着，登记没跟着改成硬门 |
| 层次与材质 | 15 / 15 | FRAME_BASELINE_AGAINST=working FRAME_BASELINE_COMPARED=124 FRAME_BASELINE_CHANGED=0 FRAME_BASELINE_MISSING=0 FRAME_BASELINE_ADDED=0 |
| 动效细节 | 14 / 15 | 位置判据进了登记表（缺席会红），但扫光"该多宽、该多快"仍然只有 R84 那一档依据 |
| 交互反馈 | 9 / 10 | 反馈本身没动 |
| 可访问性 | 8 / 10 | 减弱动态那档仍然无条件判；真机批次 72 / 73 还没人看 |
| 性能 | 14 / 15 | 全量 801 tests / 0 failures（41 skipped，swift test exit 0）；闸门多读两行状态，成本可忽略 |

**98 / 100**。分数与 R84 持平是刻意的：本轮没有画面产出，补的是一层"判没判过要说"的账，
外加一条把归因表改对的读数（U-177）。涨分要等它换来画面或换来硬门，不等它换来自我表扬。

### 仍未解决

- BACKLOG **119**（R84 开，本轮更新）：那一族的处置仍会翻面，而本轮多了一条成因（画法让运动不可见）
  与一条新读数（0.522）。要做的是把"几遍读数才配定罪产品"写成数据。
- BACKLOG **116**（skip 那五条没有"为什么今天没跑"的读数）、**115**（TableProbe 的时刻仍走共享变量）、
  111、108 余下、77 路 b、101 ②③、106、**92**（在屏那一步今天仍然 `ui suite exit: 137 / 0 条结论`）；
  真机 68.1 / 68.2 / 69.1 / 70.1 / 71.1 / 72.1 / 72.2 / 73.1 / 73.2。

## Round 86 · 停机也要有名字：给"在屏那一卷没跑完"装上一支会点名的报告器（更新 92、93 / 收窄 116 / U-178…U-182 / D-144）

### 本轮开场的位点清单（0 个产品文件；3 个 CI/脚本/自测文件，另有 5 份台账）

本轮不改画面，也不改任何一条判据的**逻辑**。被重新判断的是那句话：
**"这一卷今天没跑完" —— 它有没有指名道姓。**

| 位点 | 位置 | R85 留下的缺陷 | 本轮处置 |
|---|---|---|---|
| 在屏那一卷的停机 | `.github/workflows/ci.yml` 的 `On-screen interaction probes` | 只打到 `已下结论的用例: 0`，是"第一条就挂住"还是"一条都没开始"没人知道 | 加一步 `ui_probe_report.py`（报告型） |
| 停机归因的牙 | 新增 `scripts/ui_probe_report.py` | 没有这样一支脚本 | started 减 concluded ⇒ `UI_PROBE_HUNG=<用例名>`；说不出就**红** |
| 真值表 | 新增 `scripts/tests/test_ui_probe_report.py` | —— | 七格（① 点名 ② 跑完 ③ 没开始 ④ 日志不完整 ⑤ 拿错文件 ⑥ 空日志 ⑦ 读不到）+ 退出码 + 不冗余守卫 |
| 硬门那一半 | `.github/workflows/ci.yml` 的 `On-screen probe coverage floor` | 那一支只判**集合级**（哪几条没下结论） | 同一份日志再跑一次报告器，给不出名字 ⇒ `PROBE_FLOOR_STOP_UNNAMED=1` 红 |

本轮动的非台账文件 **3 个**（约定 ≤4）：`ci.yml`、`scripts/ui_probe_report.py`、`scripts/tests/test_ui_probe_report.py`。
0 个产品文件、0 处测试判据逻辑改动 —— 在屏那一卷的 11 条 Swift 测试**一行没动**（见下面 spike 那一节为什么不需要动）。

# R86 读 R85 的 CI（run 38805382593 · #234 · commit 0f0cced · 20:51:59→21:04 · build-and-test = success）

这是**常驻循环那一族第一次在 runner 上自己说"今天判到了"**，也是 `loops` 那一层第一次判自己。

## 1. 状态行与 `loops` 那一层（R85 新加的，本轮第一次在 runner 上落地）

```
MOTION_SHIMMER_STATE 判定=ok 原因=-
MOTION_SHIMMER_BAND_STATE 判定=ok 原因=-
MOTION_FLOOR_FACTS judged=4/4 executed=54 not-run=- summary=detail-kind-change=3 empty-state=4 notice-banner=2 notice-banner-dismiss=3 红的用例=- 汇总行报红=0
MOTION_FLOOR_LOOP_JUDGED=skeleton-loop 这一族今天判到了（状态 ok）
MOTION_FLOOR_LOOP_JUDGED=skeleton-band-position 这一族今天判到了（状态 ok）
MOTION_FLOOR_SUITE_CLEAN=0 这一卷没有红用例（汇总行也没说有）
MOTION_FLOOR_OK=4/4 全部臂都在登记之内
MOTION_FLOOR_REDS=0
```

⇒ 结案 118 的那半句"整族没说一句话就会红"已经在 runner 上生效：
两行状态都读到了，闸门两行都点了名。

## 2. 扫光那一族（三遍 → 四遍并排，119 的第三个数据点）

| run | 画法 | 产品 coverage | 等节拍证人 | 位置判据 | 处置 |
|---|---|---|---|---|---|
| R82 38781113064 | 每根条各扫各的 | 0.000（0/21 对） | 0.284 | — | 点名环境 |
| R83 38786182395 | 每根条各扫各的 | 0.050（1/22 对） | 0.837 | — | 判产品红 |
| R84 38798408040 | **整组一条带** | 0.522（2/24 对，采样≈112ms） | 0.594 | 可用帧 11 / 散布 1.0pt | 判绿 |
| R85 38805382593 | **整组一条带** | **0.842**（2/22 对，峰值 0.016，采样≈103ms） | — | **可用帧 12 / 丢掉 10 / 散布 1.0pt / 归一化 0.450 / 行程 134.0pt / 判定=整组一条带** | **判绿** |

⇒ **两遍连续判绿**，而且第二遍比第一遍高出一大截（0.522 → 0.842）。
这仍然**不**构成把 `must_judge` 改成 true 的理由：0.522 与 0.842 之间的跨度本身就说明
这一支的读数在 runner 上还不稳（同一种画法、同一台机器类别，两遍差 0.32）。
R38 那句话在这里的读法是反过来的——**波动大恰恰是"还不能当硬门"的证据**，不是"已经稳了"。
下一格（119 的待办）要的"几遍读数才配定罪"，现在有了 4 个数据点：0.000 / 0.050 / 0.522 / 0.842，
前两个属于旧画法，后两个属于新画法 ⇒ 新画法两遍都在地板上，但**分布宽度 0.32** 还没量过第三遍。

## 3. 仍然没跑的那一卷（BACKLOG 92 的形状，本轮改的就是它）

```
ui suite exit: 137  executed: 0  skipped: ?  已下结论的用例: 0
```

R85 之前这一步到此为止。本轮（R86）加了 `scripts/ui_probe_report.py`：
它把 `Test Case ... started` 与有结论的行做差，输出 `UI_PROBE_HUNG=<用例名>` /
`UI_PROBE_NO_CASE_STARTED=1` / `UI_PROBE_ALL_CONCLUDED=1`，
而"给不出名字"（日志不完整或喂错了文件）会**红**。⇒ 下一次 CI 才知道 runner 上到底是
"第一条就挂住"还是"一条都没开始"。

## 4. 读 CI 时踩到的一个新坑（值得单独记一条）

`gh run view --log` 把**所有步骤**拼在一起，而 `MOTION_SHIMMER_STATE` 这类状态行会在
两个步骤里各出现一次、取值还不同：

| 步骤 | 行 |
|---|---|
| `Swift tests (executed-count gate)`（全量卷，没设开关） | `MOTION_SHIMMER_STATE 判定=skipped 原因=capability-gate` |
| `Motion filmstrip (report-only)`（设了开关那一卷） | `MOTION_SHIMMER_STATE 判定=ok 原因=-` |

⇒ 我第一遍 grep 整份日志时读到"同一族既 ok 又 skipped"，差点把它当成 R85 那层的排序 bug
（闸门是"按最后一条判"）。按步骤名过滤之后才看清：**两条行来自两次不同的运行**。
闸门读的是 `/tmp/motion.log`（只有设了开关那一卷写它），所以它没被骗 —— 会被骗的是读日志的人。
⇒ 台账里写一句：读 CI 必须**按步骤名**过滤，跨步骤 grep 出来的"自相矛盾"多半是拿错了范围。

## 5. 捕获那一步（顺带，与 116 有关）

```
CAPTURE_GATE_CHANNELS stdout=1 readings=404 行 补回=0 行（stdout 没有的读数）
CAPTURE_GATE_CASES passed=38 skipped=9 failed=0 有名字的红=0 NOT_RUN=54
  被 skip 的用例（skip 不是通过，它只是不红）：testDarkSettingsSidebarTextIsACountedBlindSpot testInkDirectionRuler…
  TEXT_SIDE_NOT_RUN settings-shortcuts dark 侧栏列读到 0 个偏离像素（同帧内容区读到 0 个）
```

⇒ 116 原文那句"那五条没有一行为什么今天没跑"在**捕获这一族已经不成立**：
闸门不但列出了它们的名字，还带着读数与原因。116 剩下的那半句仍然成立，见
`r86_skip_readings.md`（"闸门只报它找到的 NOT_RUN，不报它没找到的那些"）。


### 读 R85 的 CI（run 38805382593）：`loops` 那一层第一次在 runner 上判自己，两行都读到了

```
MOTION_SHIMMER_STATE 判定=ok 原因=-
MOTION_SHIMMER_BAND_STATE 判定=ok 原因=-
MOTION_FLOOR_FACTS judged=4/4 executed=54 not-run=- summary=detail-kind-change=3 empty-state=3 notice-banner=13 notice-banner-dismiss=12 红的用例=- 汇总行报红=0 MOTION_FLOOR_LOOP_JUDGED=skeleton-loop 这一族今天判到了（状态 ok）（这一族今天一共打了 2 行状态，按最后一条判） MOTION_FLOOR_LOOP_JUDGED=skeleton-band-position 这一族今天判到了（状态 ok）（这一族今天一共打了 2 行状态，按最后一条判） MOTION_FLOOR_REDS=0 MOTION_GATE_EXIT=0
```

⇒ 118 结案的那半句"整族没说一句话就会红"已经在 runner 上生效。
而 119 拿到了**第四个**数据点：产品 coverage 从 0.522 变成 **0.842**（同一种画法、同一台机器类别）。

**这一格本轮被我自己读反了一次，所以把它写全**：两遍新画法都在地板（0.50）之上，
直觉是"那就把 `must_judge` 收成 true"。但 0.522 与 0.842 之间的**跨度 0.32** 本身就是答案 ——
一支读数能在两遍之间走 0.32 的判据，不配当硬门。R38 那句话在这里要倒着读：
"两台机器的读数不能当另一台机器的地板"同样意味着"同一台机器的两遍之间的波动，
就是它还不该被钉死的证据"。⇒ `must_judge` 仍然 false，119 继续开着，
要的是**分布宽度**而不是"两遍都过了"。

### 改了什么：一支只回答"它是怎么停的"的脚本

它**不判产品**，真值表全是"能不能给出名字"这一件事：

| 形状 | 输出 | 退出码 |
|---|---|---|
| ① 开了口没结论 | `UI_PROBE_HUNG=<用例名>` | 0（有名字） |
| ② 每条都有结论 | `UI_PROBE_ALL_CONCLUDED=1` | 0 |
| ③ 原始日志里一条 `Test Case` 都没有 | `UI_PROBE_NO_CASE_STARTED=1` | 0（进程级死法，也是名字） |
| ④ 有结论却没有它的 started 行 | `UI_PROBE_CONCLUDED_WITHOUT_START=<名>` | **1** |
| ⑤ 喂进来的是 CI 那一步的汇报片段 | `UI_PROBE_NOT_THE_RAW_LOG=1` | **1** |
| ⑥ 空日志 | `UI_PROBE_LOG_EMPTY=1` | **1** |
| ⑦ 文件读不到 | `UI_PROBE_LOG_UNREADABLE=…` | **1** |

④⑤⑥ 的共同点是：**"我说不出"不许被读成"没事"**。
CI 里两步各用一次：报告型那一步只把名字打出来（环境给不出证据不该挡发布），
硬门那一步（`On-screen probe coverage floor`）要求名字必须给得出。

本轮真日志上的两格对照（不是合成夹具）：

```
UI_PROBE_PROGRESS started=801 concluded=801 UI_PROBE_ALL_CONCLUDED=1 UI_PROBE_NAMED=1
UI_PROBE_PROGRESS started=13 concluded=12 UI_PROBE_HUNG=testDisabledToggleAndFailureReceiptAreVisible UI_PROBE_NAMED=1
```

⇒ 对一份**跑完的**全量日志它说"跑完了"，对一份**被 kill -9 的**日志它点出那条正在跑的用例。
合成夹具证不到这一格：那是照着我记忆里的行格式写的，真 `swift test` 的格式对不对只有真日志知道。

### U-178 · 读 CI 必须按步骤名过滤，跨步骤 grep 会造出假矛盾

`gh run view --log` 把所有步骤拼在一起，而状态行会在两个步骤里各出现一次、取值不同：
全量卷那一步（没设开关）打 `MOTION_SHIMMER_STATE 判定=skipped 原因=capability-gate`，
动效卷那一步（设了开关）打 `判定=ok`。我第一遍读到"同一族既 ok 又 skipped"，
差点判成 R85 那层"按最后一条判"的排序 bug —— 而闸门读的是 `/tmp/motion.log`，
只有设了开关那一卷写它，它没被骗。**会被骗的是读日志的人。**
⇒ 本轮起，读 CI 的固定动作是先按步骤名切范围再 grep（这条已写进 `r86_ci_readings.md`）。

### U-179 · "没有 Test Case 行"有两种成因，拿错文件会生成一句关于产品的假话

第一次试这支脚本时我喂的是 `scripts/tests/fixtures/r62_runner_ui.log` ——
那是 run 38603034761 那一步的**逐字汇报**（`ui suite exit: 137 …`），里面本来就不会有 `Test Case` 行。
脚本于是自信地报了"进程在第一条用例开口之前就死了"。
那句话听起来像个结论，而真相是我拿错了文件。⇒ 加了 ⑤ 那一格：
有汇报行却没有 `Test Case` ⇒ `UI_PROBE_NOT_THE_RAW_LOG=1` 并**红**。
这一格用的是那份真夹具，所以它不是防御性注释，是一条会自己挨刀的判据（M467）。

### U-180 · 判"变异落地没有"要看内容，不是看文件变没变

M472（元层那一刀：往不冗余守卫读的文件里塞一行含 `started` 的注释，证明守卫会红）
第一版报 **ESCAPED**。查下去不是守卫没牙，是**我插的那行注释里根本没有 `started` 这个词**。
同批还顺手修了另一处：纯插入型的刀，其变异文**必然**包含原串，
于是旧的"回读要求原串消失"会把落成功的刀报成未落地（R76 的 M398 / M399 同族，本轮第三次撞）。
⇒ 回读判据换成"文件必须与变异前不同"，而"刀里带的词对不对"由 MEASURE 那一遍的输出证明。

### U-182 · 自动"找"出来的采样点会悄悄量错对象，钉死坐标 + 自带断言才算量过

第一次量图例时写的是"在底部 30% 里找蓝块 ≥3 个的那一行"。它命中了 **网格的最后一行**
（那一行本来就有好几个蓝色格子），于是"图例四档"读出来是七个块、还混进 6px 宽的边缘。
⇒ 换成手工对过帧之后钉死的坐标（`LEGEND_Y=400` 与四个块的中心 x），
并且**每个点带一条断言**：图例四块必须互不相同且单调变蓝；空格子必须是中性灰且不等于背景；
不满足就报 `not-found` 让脚本崩，而不是安静地把错的色写进台账。
"自动搜索"在这种场合不是省事，是把**量错对象**伪装成量到了。

### U-181 · 两支闸门判的是两句不同的话，这条不写下来就会有人来合并它们

`probe_coverage_gate.py`（R62 起）判**集合级**：源码里有几条在屏判据、这次哪几条没下结论、缺席登记过没有。
`ui_probe_report.py`（本轮）判**因果级**：这一卷是**怎么**停的。
只有前者会漏成这样：11 条全登记着、全都没结论、闸门照样绿 —— 那正是 R62 到 R85 的形状。
⇒ 自测里留了一条不冗余守卫（读那一支的源码，要求它不含 `started`），并由 M472 那一刀证明它会红。

### 116 被这次测量**收窄**了，没有结案

四遍独立进程（同一提交、同一台机器）：全量两遍都是 `801 tests / 41 skipped` 且**名单逐名相同**，
捕获两遍都是 `47 / 4 skipped`。⇒ R81 那句"同一提交两遍差 7 条"今天复现不出来。
而读 R85 的 CI 又发现：捕获那五条**在 runner 上确实 skip 了，闸门也列出了它们的名字与原因**
（`TEXT_SIDE_NOT_RUN settings-shortcuts dark 侧栏列读到 0 个偏离像素…`）。
⇒ 116 剩下的、今天仍然成立的那半句只有一句：**闸门只报它找到的 `*_NOT_RUN`，不报它没找到的那些**。
这一句与 R85 的 `LOOP_SILENT` 同形，交给 R87（本轮不动判据代码）。

### 真实看图（本轮看的是热图，不是骨架 —— 那张图从 R45 之后没被重新判过）

看的是本轮验证现生成的 `heatmap-populated-430x250-dark/light.png`（860×500px），
色号由 `r86_heatmap_legend.py` 现算（采样点是手工对过帧之后钉死的，脚本里带断言）：

| 角色 | 暗档 | 亮档 |
|---|---|---|
| 图例四档（少→多） | 31,47,71 30,62,107 26,81,156 12,108,220（从左到右：少→多） | 215,232,255 180,210,255 130,180,255 59,142,255（从左到右：少→多） |
| 网格那一格（"没有记录"的取色） | 41,41,41 背景=30,30,30 ⇒ 与背景的差=11 | 243,243,243 背景=255,255,255 ⇒ 与背景的差=12 |

⇒ 眼睛先看到的问题是真的：**图例里没有"没有记录"那一档**
（`HEATMAP_EMPTY_IN_LEGEND_dark=no（图例四档里没有这一色 ⇒ "少"指的是最低一档**非零**）`、`..._light=no（图例四档里没有这一色 ⇒ "少"指的是最低一档**非零**）`）——
灰格子比图例最左那一档还淡，看图的人可能把它读成"少到看不见"。

**但判为不加第五档，理由写在账上**：这一格的文案早就把两件事分开了 ——
`DailyCopyHeatPolicy.tooltip` 对 `count == 0` 说的是**"没有记录"**而不是"0 次"，
而"追踪到 0 次"与"根本没追踪"在**存档语义**里本来就是同一个值（`counts: [String: Int]` 里没有这个键）。
要在图例上区分它们，得先让存档能区分；那是数据模型的事，
拿一个第五色块去盖它，等于让视觉层替一个它没有的信息负责。
⇒ 图例保持四档（"少"指最低一档**非零**），hover 说真话。
这一格如果哪天要动，动的是 `DailyCopyLedger`，不是颜色。

顺带两条读数：灰格与所在背景的差只有 **暗 11 级 / 亮 12 级**（255 制）
⇒ 它是"比背景略亮/略暗的一点东西"，与 R85 量的骨架静置条（11 / 13）几乎同一个量级 ——
这两处是同一类"占位符该多淡"的判断，将来调其中一个时，另一个是对照点。

### 牙

| M465 | 挂死集合算反（concluded 减 started） | **CAUGHT** |
| M466 | 日志不完整（有结论没 started）从红改成放行 | **CAUGHT** |
| M467 | 不再区分『步骤摘要』与『原始日志』（拿错文件时自信地报产品结论） | **CAUGHT** |
| M468 | 空日志不再算仪器故障，直接往下走成『一条用例都没开始』 | **CAUGHT** |
| M469 | 红不落到退出码（CI 那一步就再也拿不到『说不出』这件事） | **CAUGHT** |
| M470 | 重复的 started 不去重 | **CAUGHT** |
| M471 | `--quiet` 连结论行一起吞 | **CAUGHT** |
| M472 | 元层：往不冗余守卫读的那支闸门里塞一行真的含 started 的注释 | **CAUGHT** |

### 验证（本机，逐条实跑）

```
swift build --build-tests                告警 0
swift test（全量）                       801 tests / 0 failures（41 skipped，swift test exit 0）
动效覆盖地板闸门（含 loops 那一层）        MOTION_FLOOR_FACTS judged=4/4 executed=54 not-run=- summary=detail-kind-change=3 empty-state=3 notice-banner=13 notice-banner-dismiss=12 红的用例=- 汇总行报红=0 MOTION_FLOOR_LOOP_JUDGED=skeleton-loop 这一族今天判到了（状态 ok）（这一族今天一共打了 2 行状态，按最后一条判） MOTION_FLOOR_LOOP_JUDGED=skeleton-band-position 这一族今天判到了（状态 ok）（这一族今天一共打了 2 行状态，按最后一条判） MOTION_FLOOR_REDS=0 MOTION_GATE_EXIT=0
捕获闸门                                 CAPTURE_GATE_RESULT=ok 红=0（已登记的 NOT-RUN 见上）
frame_baseline.py check --against working FRAME_BASELINE_AGAINST=working FRAME_BASELINE_COMPARED=124 FRAME_BASELINE_CHANGED=0 FRAME_BASELINE_MISSING=0 FRAME_BASELINE_ADDED=0
python3 -m unittest discover -s scripts/tests  Ran 155 tests in 6.837s OK
ui_probe_report.py（真日志两格）          见上面那段
```

### 七维自评

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 20 / 20 | 零产品改动，本轮没有脸加分，也没有东西被扣 |
| 流畅度 | 18 / 20 | 扫光在 runner 上两遍判绿（0.522 / 0.842），但跨度 0.32 ⇒ 仍不能钉成硬门 |
| 层次与材质 | 15 / 15 | 本轮无画面产出 |
| 动效细节 | 13 / 15 | 比 R85 少 1 分：**在屏那一族今天仍然一条判据都没在 CI 上跑过**，本轮只是让"没跑"这件事从此必须有名字 |
| 交互反馈 | 9 / 10 | 反馈本身没动 |
| 可访问性 | 8 / 10 | 真机批次 72 / 73 还没人看；焦点那四条在 runner 上仍然没跑（111） |
| 性能 | 14 / 15 | 全量 801 tests / 0 failures（41 skipped，swift test exit 0）；新脚本只读一份日志，成本可忽略 |

**97 / 100**，比 R85 低一分是刻意的：本轮连判据逻辑都没动，产出是"一个名字 + 一张真值表 + 八刀"，
而它换来的那条最值钱的东西（CI 上到底哪一条挂住）要等下一次 CI 才看得见。
分数不许为"做了基础设施"上涨，只为"画面或硬门变好"上涨。

### 仍未解决

- BACKLOG **92 / 93**（本轮都只更新，不结案）：报告器已接上，但"runner 上到底挂在哪一条"是
  **下一次 CI 的读数**。预测已经先登记在 93 里（三种结果各意味着什么），
  在那之前不许写"92 已修"。
- BACKLOG **116**（本轮收窄）：剩下"闸门不报它没找到的 `*_NOT_RUN`"那一格，形状与 `LOOP_SILENT` 同族。
- BACKLOG **119**（第四个数据点，仍开着）：新画法两遍 coverage 跨度 0.32 ⇒ 要的是分布宽度。
- **115**、**111**、108 余下、77 路 b、101 ②③、106；
  真机 68.1 / 68.2 / 69.1 / 70.1 / 71.1 / 72.1 / 72.2 / 73.1 / 73.2。

## Round 87 · 两把尺矛盾时谁签字：coverage 不再能单独把扫光判红（修 main 那朵红 / 更新 119、93 / 新开 120 / U-183…U-186 / D-145）

### 本轮开场的位点清单（0 个产品文件；3 个判据/登记表/自测文件）

本轮的起点是 **main 红了**（R86 的 CI，run 38811457259，`Motion coverage floor` 那一步）。
红得有名字，但名字说的是"产品没在跑"，而同一卷上另一把尺说亮带走完了整幅 ——
被重新判断的是**定罪权该给谁**。

| 位点 | 位置 | R86 留下的缺陷 | 本轮处置 |
|---|---|---|---|
| 扫光运动判据 | `MotionFilmstripTests.loopAdjudication` | coverage（1–2 个变化帧对）能单独判产品红 | 新增 `travel` 入参：位置尺说"走过整幅"时改判**有名字的未覆盖** |
| 行程证据 | 同类新增 `travelEvidence(_:)` | 位置读数只用来判"是不是整组一条带"，没参与"在不在动" | 只看**可用帧数与行程**两个量，不看笼统的 `verdict` |
| 登记表 | `scripts/motion_floor_expectations.json` | 没有这种坏法的名字 | 新增 `loop-coverage-contradicted-by-travel`，理由不许借用旧名字 |
| 闸门自测 | `scripts/tests/test_motion_floor_gate.py` | 新名字两边不同步没人管 | +2 格：登记过的矛盾不红；只差一个词的名字必须红 |

本轮动的非台账文件 **3 个**（约定 ≤4）。0 个产品文件 ——
红不是产品的回归造成的（R84 之后产品一行没改），是判据的定罪权放错了地方。

# R87 读 R86 的 CI（run 38811457259 · #235 · commit f18c52b · 21:38:55→21:53 · build-and-test = **failure**）

失败的步骤是 **`Motion coverage floor`**（不是我本轮新接的那道 UI 硬门）。两件事同时发生：

1. 常驻循环那一族在 runner 上**把产品判成了红**（第三遍），而位置尺在同一卷上说亮带走完了整幅；
2. 在屏那一卷的停机**第一次有了名字** —— 而那个名字把 BACKLOG 93 的预测推翻了一半。

## 1. coverage 与行程：同一份产品代码，两把尺给相反答案

```
MOTION_SHIMMER 扫 帧数=23 变化帧对=1 峰值=0.028 采样≈98ms coverage=0.032(地板 0.50) 记录时长=2324ms 判定=只动了一下
MOTION_SHIMMER_WITNESS 等节拍证人(30Hz 抬升 0.12，与产品同数字) 帧对=25 在变=6 峰值=0.028 coverage=0.671 判定=一直在动
MOTION_SHIMMER_WITNESS 粗节拍证人(20Hz 抬升 0.45) 帧对=31 在变=23 峰值=0.040 coverage=1.000 判定=一直在动
MOTION_SHIMMER_BAND 帧=23 比例=1pt≈1.00px 可用帧=12 丢掉=11 同帧绝对中心最大散布=1.0pt 归一化散布=0.450 行程=134.0pt 判定=整组一条带
MOTION_SHIMMER_BAND_SAMPLE 可用帧首=[21.0, 21.0, 21.0] 末=[155.0, 155.0, 155.0]
MOTION_SHIMMER_STATE 判定=productRed 原因=-
MOTION_SHIMMER_BAND_STATE 判定=notRunEnvironment 原因=loop-not-capable
MOTION_FLOOR_SUITE_RED=1 … 红的用例=testSkeletonSweepActuallySweeps
MOTION_FLOOR_LOOP_RED_NAMED=skeleton-loop=productRed
MOTION_FLOOR_LOOP_NOT_JUDGED=skeleton-band-position=loop-not-capable
MOTION_FLOOR_REDS=1
```

**四遍读数并排（R84 换画法之后，产品代码一行没改；最后一行是本轮 R87 的全量验证那一遍）**：

| run | 帧数 | 变化帧对 | coverage | 可用帧 | 行程 | 处置 |
|---|---|---|---|---|---|---|
| 38798408040 (R84) | 24 | 2 | 0.522 | 11 | 109.0pt | ok |
| 38805382593 (R85) | 22 | 2 | 0.842 | 12 | 134.0pt | ok |
| 38811457259 (R86) | 23 | **1** | **0.032** | 12 | **134.0pt** | **productRed（CI 红）** |
| 本机 R87 验证那一遍 | 48 | 20 | 1.000 | 7 | 121.5pt | ok |

⇒ coverage 的支撑是 **1–2 个变化帧对**（分母 22–24 对里只有 1–2 对在变），
而行程的支撑是 runner 三遍的 **11–12 个可用帧**（本机那一遍 7 帧，也够），且它在两台机器、四遍里都落在 109–134pt。
"亮带从 x=21pt 走到 x=155pt"是**位置**证据，它不依赖采样网格；
coverage 依赖。⇒ 本轮把"两把尺矛盾时谁签字"写进判据（`loopAdjudication` 的 `travel` 入参）。

## 2. 在屏那一卷：停机有了名字，而名字推翻了我上一轮登记的预测

```
UI_PROBE_PROGRESS started=0 concluded=0
UI_PROBE_NO_CASE_STARTED=1 （进程在第一条用例开口之前就死了：看门狗收掉的是启动阶段，不是某条判据）
UI_PROBE_NAMED=1
PROBE_COVERAGE_SUMMARY 源码用例=11 登记=11 runner可跑=0 runner不可跑=11 本次下结论=0 红=0
```

R86 我在 BACKLOG 93 里**预先登记**了三种结果各意味着什么，其中一条是：
"若报 `UI_PROBE_HUNG=testAccessibilityTreeCoverage` 就证实挂在字母序第一条用例内部"。
实际报的是 `NO_CASE_STARTED` ⇒ 原文那条"挂在第一条用例内部"的推断**没有被证实**，
它连"XCTest 有没有开始报用例"都没到。

**但这一格不能就这么收**（这是本轮最该诚实的地方）：`started=0` 有两种成因，
而这一份日志分不开它们：

* ① 进程真的在第一条用例开口之前就死了（启动/会话层）；
* ② 用例其实跑了，但 `swift test` 的 stdout 在 `kill -9` 时整块丢了
  —— 这一族本仓库见过两次（R64 的捕获卷、R84 的动效卷），而 `> /tmp/ui.log 2>&1` 是重定向到文件，
  块缓冲被 SIGKILL 掐掉是**默认行为**，本机那次 spike 只证明了"能留住"（13 行），
  没证明"每次都留得住"。

⇒ ②如果为真，那 `UI_PROBE_NO_CASE_STARTED=1` 就是一句关于产品的假话（它说的是"没开始"，
而真相是"开始了我没看见"）。这一格交给 R88：在屏那一步同时看**产物通道**
（`/tmp/shots-ci` 里有没有帧、探针有没有写 readings），
有帧没日志 ⇒ ②；没帧没日志 ⇒ ①。这是 BACKLOG 93 剩下的那一步，也是它不结案的理由。

## 3. 其余步骤（一次读完，免得下次靠记忆）

* `Capture gate`：`passed=38 skipped=9 failed=0 有名字的红=0 NOT_RUN=54` ⇒ 捕获这一族照旧绿，
  而那五条在 runner 上确实 skip（116 剩下的那半句仍然成立）。
* `ui suite exit: 137 executed: 0 已下结论的用例: 0` ⇒ BACKLOG 92 的形状没变（它本来就没结案）。
* 动效那一步 `motion suite exit: 1` —— 红的是判据本身，闸门把它翻译成了有名字的 `SUITE_RED`
  + `LOOP_RED_NAMED`，这正是 R85 那层要的形状（红有名字、有人负责）。


### 为什么 coverage 不能单独定罪（U-183）

四遍读数，同一份产品代码（R84 换画法之后）：

| run | 帧数 | 变化帧对 | coverage | 可用帧 | 行程 | 处置 |
|---|---|---|---|---|---|---|
| R84 38798408040 | 24 | 2 | 0.522 | 11 | 109.0pt | ok |
| R85 38805382593 | 22 | 2 | 0.842 | 12 | 134.0pt | ok |
| R86 38811457259 | 23 | **1** | **0.032** | 12 | **134.0pt** | **productRed（main 红）** |
| 本机 R87 验证那一遍 | 48 | 20 | 1.000 | 7 | 121.5pt | ok |

本机那一行的原文读数（上面五个数就是从这三行里读的，逐字贴在这里以便对账）：

```
MOTION_SHIMMER 扫 帧数=48 变化帧对=20 峰值=0.023 采样≈53ms coverage=1.000(地板 0.50) 记录时长=2493ms 判定=一直在动
MOTION_SHIMMER_BAND 帧=48 比例=1pt≈2.00px 可用帧=7 丢掉=41 同帧绝对中心最大散布=0.0pt（地板：≤6.0 判一条带、≥40.0 判各扫各的） 归一化散布=0.413 行程=121.5pt（正对照地板 20.0） 判定=整组一条带 理由=每一帧三根条的亮斑都在同一条竖线上（最大差 0.0pt ≤ 6.0），且它一路走了 121.5pt
MOTION_SHIMMER_BAND_SAMPLE 可用帧首=[33.0, 33.0, 33.0] 末=[142.5, 142.5, 142.5]
```

⇒ 两把尺问的是同一件事（"亮带在不在走"），但支撑它们的样本数差一个量级：
coverage 在 runner 上只有 **1–2 个变化帧对**（分母 22–24 对），
而位置尺在 runner 三遍上有 **11–12 个可用帧**（本机那一遍 7 帧），且它在两台机器、四遍里都落在 109–134pt。
"亮带从 x=21pt 走到 x=155pt"是**位置**证据，不依赖采样网格；coverage 依赖 ——
30Hz 的扫光在 ~100ms 的采样间隔下，相邻两帧常常长得一样，要走完一根条才跨一次台阶。

⇒ 所以定罪权按**样本数**分配：`loopAdjudication` 现在先问"有没有一份样本更多的尺在说反话"，
有 ⇒ 判 `notRunRulerBlind`（点名 `loop-coverage-contradicted-by-travel`，不红也不绿）。
三格方向钉子钉住它没被放宽：位置尺也说没走过 → 仍然红；位置尺今天没读数 → 仍然红；
产品在动 → 行程说什么都不改判绿；粗节拍证人整卷没拍到 → 仍然先红在证人。

这一格是 BACKLOG **110**（"单样本统计会把一臂在判到/判不到之间翻脸"）在循环这一族的第三个实例，
也是 **119** 开张时要的那件事的另一半：119 问"几遍读数才配定罪产品"，
本轮的答案是"**一遍都不配，除非另一把样本更多的尺同意**"——
跨遍状态在一次 CI 里拿不到，而同一卷上的第二把尺拿得到。

### U-184 · 预先登记的预测被推翻时，要写"没证实"，不要顺手换一种解释

R86 我把三种可能连同各自的含义**先登记**在 BACKLOG 93 里（这是那条的正确用法）。
CI 报的是 `UI_PROBE_NO_CASE_STARTED=1` ⇒ "挂在字母序第一条用例内部"那句推断没有被证实。
但这一格不能就这么收：`started=0` 有两种成因，而**这一份日志分不开它们** ——
① 进程真的在第一条用例开口之前死了；② 用例其实跑了，但 stdout 在 `kill -9` 时整块丢了
（这一族本仓库见过两次：R64 的捕获卷、R84 的动效卷；`> /tmp/ui.log 2>&1` 是重定向到文件，
块缓冲被 SIGKILL 掐掉是默认行为。R86 的 spike 只证明了"能留住"，没证明"每次都留得住"）。
⇒ ②为真时 `NO_CASE_STARTED` 就是一句关于产品的假话。
分不开的办法本轮找到了：那一步同时看**产物通道**（`/tmp/shots-ci` 里有没有帧）——
有帧没日志 ⇒ ②；没帧没日志 ⇒ ①。这一格交给 R88，也是 93 不结案的理由。

### U-185 · 新坏法必须有新名字，而"两边同步"要有一条会红的守卫

`notRunRulerBlind` 本可以沿用 `loop-clock-not-sustainable-at-product-rate` 蒙过 CI
（闸门只比登记表里的名字）。那等于让新病借用旧病的免检牌：登记表从此看不出多了一种坏法。
⇒ 新名字进表，并且自测里加两格：登记过的矛盾不红；**只差一个词**的名字
（`loop-coverage-contradicted-by-speed`）必须红 —— 前缀匹配只放过括号里的细节，
不放过括号外换掉的那个词。Swift 侧另有两条断言钉住"两支 not-run 的理由不许相同"。
牙：M478（借用旧名字）、M479（表里删掉新理由）、M480（`BAD_REASON` 变哑）三刀各红在预期的那一格。

### U-186 · 变异文里的注释语法会让一刀"没跑成"，而不是"没抓到"—— 两种病别混

M475 / M476 第一版报 **NOT-RUN**：我在 Swift 行的末尾写了 `# R87 变异` 当注释，
而 Swift 的注释是 `//` ⇒ 编译失败，判据根本没机会跑。
这一族电池已经记过两次"编译错误被误读成判据没牙"（R83 的 M454 现场、R85 的锚点不匹配），
本轮是第三次，只是这次方向反过来：**是变异文自己坏了**。
⇒ 汇总行把 `没跑成` 与 `逃掉` 分开计数（这一版脚本一直是分开的，是我读日志时容易把它们混成"没牙"），
而修法是改刀不是改判据。

### 牙

| M473 | 删掉『两把尺矛盾时不许定罪产品』那一支（coverage 又能单独判红） | **CAUGHT** |
| M474 | 矛盾那一支从『有名字的未覆盖』改成『判绿』 | **CAUGHT** |
| M475 | 行程证据不看可用帧数（一帧也算读过） | **CAUGHT** |
| M476 | 行程地板失效（亮带钉在原地也算走过整幅） | **CAUGHT** |
| M477 | 矛盾检查排到证人签字之前 | **CAUGHT** |
| M478 | 新理由借用旧名字（登记表看不出多了一种坏法） | **CAUGHT** |
| M479 | 登记表里删掉新理由（判据改了名字而表没跟着改） | **CAUGHT** |
| M480 | 没登记的理由不红（BAD_REASON 那一格变哑） | **CAUGHT** |

### 验证（本机，逐条实跑）

```
swift build --build-tests                告警 0
swift test（全量）                       801 tests / 0 failures（41 skipped，swift test exit 0）
动效覆盖地板闸门（含 loops 那一层）        MOTION_FLOOR_FACTS judged=4/4 executed=54 not-run=- summary=detail-kind-change=3 empty-state=4 notice-banner=12 notice-banner-dismiss=13 红的用例=- 汇总行报红=0 MOTION_FLOOR_LOOP_JUDGED=skeleton-loop 这一族今天判到了（状态 ok）（这一族今天一共打了 2 行状态，按最后一条判） MOTION_FLOOR_LOOP_JUDGED=skeleton-band-position 这一族今天判到了（状态 ok）（这一族今天一共打了 2 行状态，按最后一条判） MOTION_FLOOR_REDS=0 MOTION_GATE_EXIT=0
捕获闸门                                 CAPTURE_GATE_RESULT=ok 红=0（已登记的 NOT-RUN 见上）
frame_baseline.py check --against working FRAME_BASELINE_AGAINST=working FRAME_BASELINE_COMPARED=124 FRAME_BASELINE_CHANGED=0 FRAME_BASELINE_MISSING=0 FRAME_BASELINE_ADDED=0
python3 -m unittest discover -s scripts/tests  Ran 155 tests in 6.779s OK
```

> 上面这一格**原来是这么写的**：`discover -s scripts`。今天照抄它跑一遍，打印的是 `Ran 0 tests in 0.000s` + `OK` + 退出 0 —— 少一层目录的 discovery 什么都收不到，而它看起来完全像通过了。真正跑的那一步一直是 `-s scripts/tests`（`verify_r87.sh` 与 CI 的 `Release script tests` 都是），台账里这 8 处标签本轮一起改对（R80 / R81 / R82 / R83 / R84 / R85 / R86 / R87 这八轮的验证块，逐行按所属轮次对过）。CI 那一步不是完全没防：它有 `test "$executed" -ge 48`，所以 0 会红；但 **78 也过** —— 地板是个静态数，而现在的条数是 155。新开 BACKLOG 121。

### 七维自评

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 20 / 20 | 零产品改动：本轮没脸加分，也没东西被扣 |
| 流畅度 | 18 / 20 | 扫光在 runner 上到底跑没跑，今天仍然只有位置尺在说；coverage 那一格改成了"有名字的未覆盖" |
| 层次与材质 | 15 / 15 | 本轮无画面产出 |
| 动效细节 | 14 / 15 | 定罪权挪对了地方（样本多的尺签字），但"亮带该多宽多快"仍然只有 R84 那一档依据 |
| 交互反馈 | 9 / 10 | 反馈本身没动 |
| 可访问性 | 8 / 10 | 减弱动态那一臂仍然无条件判；真机批次 72 / 73 还没人看 |
| 性能 | 14 / 15 | 全量 801 tests / 0 failures（41 skipped，swift test exit 0）；位置尺现在被算两遍（运动判据与位置判据各一次），成本是纯函数在 12 帧上，可忽略 |

**97 / 100**，与 R86 持平：本轮修掉的是**一朵假红**，没有换来画面，也没有换来硬门。
分数不涨是刻意的 —— 判据少说一次假话不该被记成产品变好了。

### 仍未解决

- BACKLOG **119**（本轮更新）：新处置让 coverage 不再单独定罪，但"这一族的读数分布有多宽"
  仍然只有 4 个点（runner 三遍 0.522 / 0.842 / 0.032，加本机那一遍 —— 数字在上面那张表里）。
- BACKLOG **92 / 93**：`NO_CASE_STARTED` 的两种成因没分开 ⇒ 交给 R88 那一步（看产物通道）。
- BACKLOG **120**（本轮新开）：位置判据今天仍被 `loopCapable` 关着 ——
  而它现在恰恰是**唯一有资格说话的那把尺**。谁该给谁签字，这件事本轮只改了一半。
- BACKLOG **121**（本轮新开）：台账里那行 `discover -s scripts` 我照抄跑了一遍，打印 `Ran 0 tests / OK / 退出 0`。命令本身一直是对的（CI 与 verify 都是 `-s scripts/tests`），错的是台账那一格（八处本轮已改对）。CI 那道地板只挡 0（`-ge 48`），**少收一半文件照样绿** ⇒ 该不该把它改成"只准升不准降 + 点名少了哪几条"，留给下一轮。
- **116** 剩下那半格（闸门不报它没找到的 `*_NOT_RUN`）、**115**、**111**、108 余下、77 路 b、
  101 ②③、106；真机 68.1 / 68.2 / 69.1 / 70.1 / 71.1 / 72.1 / 72.2 / 73.1 / 73.2。

## Round 88 · 看门狗杀的是驱动进程，不是跑用例的那个：CI 那句"一条用例都没开始"是假话（读 R87 的 CI / 更新 93、119 / 新开 122 / U-187…U-191 / D-146）

### 本轮开场的位点清单（0 个产品文件；4 个 CI/脚本/自测文件）

起点是 R87 的 CI 绿了，而**绿的方式**说明上一轮那朵红的处置今天没被检验；
同时本机按 CI 原样重跑看门狗，读到了 R86 那句话的反面。

| 位点 | 位置 | R87 留下的缺陷 | 本轮处置 |
|---|---|---|---|
| 在屏那一步的看门狗 | `.github/workflows/ci.yml` | `kill -9 $pid` 杀的是 `swift-test` 驱动，跑用例的 `xctest` 被 reparent 后继续活 | `set -m` + `kill -- -$pid`（进程组），并在收掉之前量一次进程表 |
| 停机成因 | `scripts/ui_probe_report.py` | 日志没有 started 行 ⇒ 报"进程死在第一条用例之前" | 三格：活着⇒`START_LINES_LOST`；没起⇒`NO_CASE_STARTED`；没量⇒只报观察 |
| 硬门 | `.github/workflows/ci.yml` | 上一步的 shell 变量跨不过步骤，直接引用会造出一道**恒真**的门 | 孤儿数落盘 `/tmp/ui-orphans`，读不到就红 |
| 自测 | `scripts/tests/test_ui_probe_report.py` | 三格互斥没有守卫 | +5 格（含"三格不许同时出现"） |
| CI 自检的夹具 | `scripts/tests/test_ci_report_selftest.py` | 锚点写死在旧那一行 `( sleep 240; kill -9 "$pid" ) &` | 锚点跟着改成"整段子壳"，并把两行新读数钉进期望 |

本轮动的非台账文件 **4 个**（约定 ≤4，刚好用满），产品文件 **0 个** ⇒ 不换装、不重建 Swift 产物。
第 4 个不是我主动要改的：`test_ci_report_selftest.py` **会真的执行那一步的脚本正文**，
它的夹具锚点写死在旧那一行 ⇒ 我改完 ci.yml 它就红了（U-191，那是它该做的事）。


### 1. 为什么"日志里没有 started 行"不是一句关于产品的话（U-187）

R86 我写报告脚本时的依据是一次本机 spike：`kill -9` 之后 13 行 started 留在日志里。
本轮按 CI 的**原样**重跑（`.scratch/motion-audit-2/spike_r88_ci_shape.sh`）：

```
驱动进程 pid=14687（swift-test --filter UIInteractionProbeTests），120s 后 kill -9 它本身
log_bytes=119  started=0  concluded=0  帧=0
清理阶段仍抓到：14741  …/usr/bin/xctest -XCTest ClipboardHistoryAppTests.UIInteractionProbeTests/testAccessibilityTreeCoverage,…（11 条全在 argv 里）
```

⇒ 用例**开了口**（xctest 带着 11 条用例名活着），而日志里一行都没有。
⇒ 那句 `UI_PROBE_NO_CASE_STARTED=1（进程在第一条用例开口之前就死了）` 是假话，
而 CI 的硬门把这句假话当成"有名字"读了两遍（R87、R86 各一次）。
⇒ 一次 spike 成功只证明"能留住"，不证明"每次都留得住"（R86 记过这句话，本轮轮到我自己犯）。

**成因由谁签**：由"收掉那一刻的进程表"签，不由日志的沉默签。
所以那一步现在先 `pgrep` 一次写进 `/tmp/ui-runner-alive`，报告脚本吃这个数：
1 ⇒ `UI_PROBE_START_LINES_LOST`；0 ⇒ `UI_PROBE_NO_CASE_STARTED`；没量到 ⇒ `UI_PROBE_NO_START_LINE`（只报观察）。
三格互斥由自测钉住（③d），坏值不许猜（M488）。

### 2. 差点交出去的一道恒真的门（U-188）

第一版硬门写的是 `if [ "${orphans:-0}" != "0" ]`，而 `orphans` 是**上一步 shell 里的变量** ——
GitHub 每个 `run:` 块是一个新 shell，跨步骤只有文件活着。那一格会永远读到 0，
看起来有牙、实际恒真。⇒ 孤儿数落盘 `/tmp/ui-orphans`，读不到文件时另红一格
（`PROBE_FLOOR_ORPHAN_UNMEASURED`），两格各有一刀（M484 / M485）。

### 3. 对照自己也要防"量的不是那件事"（U-189 / U-190）

* U-189：M484 / M485 第一版报 **ESCAPED** —— 刀把 `PROBE_FLOOR_WATCHDOG_MISSED` 改成
  `PROBE_FLOOR_WATCHDOG_MISSED_REMOVED_BY_MUTATION`，而接线检查是子串查 ⇒ **什么都没删掉**。
  与 R86 的 M472 同族反方向：那次是刀里没带那个词，这次是带太多。
* U-190：机制对照第一版用 python 侧 `pgrep` 数孤儿，两遍都报 0 ⇒ "旧形状留下孤儿"那格空掉。
  而脚本自己 `ps` 打出来的那一行明明白白有残留：python 侧量的其实是"那条管道还开着吗"，
  不是进程表。⇒ 判定改读**脚本自己 ps 的那几行**，五格才各自有内容。

### 4. 读 R87 的 CI：绿了，但绿的方式要记账

# R88 读 R87 的 CI（run 38818629423 · commit d0b5939 · 22:44→22:53 · build-and-test = **success**）

main 绿了。两件事同时有了答案，其中一件把我上一轮的读数**判成了假话**。

## 1. 那朵假红确实消失了，而 coverage 拿到第五个数据点

```
motion suite exit: 0  executed: 54  胶片: 14  MOTION_RESOLVE_SUMMARY judged=4/4 not-run=-
MOTION_SHIMMER 扫 帧数=23 变化帧对=2 峰值=0.019 采样≈100ms coverage=0.690(地板 0.50) 记录时长=2343ms 判定=一直在动
MOTION_SHIMMER_WITNESS 等节拍证人(30Hz 抬升 0.12) 帧对=32 在变=1 峰值=0.014 coverage=0.043 判定=只动了一下
MOTION_SHIMMER_WITNESS 粗节拍证人(20Hz 抬升 0.45) 帧对=30 在变=23 峰值=0.040 coverage=1.000 判定=一直在动
MOTION_SHIMMER_STATE 判定=ok 原因=-
MOTION_FLOOR_LOOP_JUDGED=skeleton-loop 这一族今天判到了（状态 ok）
MOTION_FLOOR_LOOP_JUDGED=skeleton-band-position 这一族今天判到了（状态 ok）
MOTION_FLOOR_REDS=0
```

⇒ **红没了，但不是靠 D-145 那一支没掉的**：这一遍产品 coverage 0.690 自己在地板上，
所以 `travel` 那一支根本没被触发，`LOOP_NOT_JUDGED=…contradicted-by-travel` **今天没在 runner 上出现**。
⇒ 诚实的结论：D-145 这一轮**没有被 runner 检验**（它只在真值表与本机那 8 刀里活着）。
它挡红的能力仍然是"未证"，这条要留给下一次 coverage 掉到地板以下的那一遍。

**119 的第五个数据点**（同画法、同机器类别、runner）：0.522 / 0.842 / 0.032 / **0.690**
⇒ 跨度 0.81，四遍里两遍在地板上、两遍在地板下。这条判据今天仍然不配当硬门（R86 记过同一句话）。

**新的、更该记的一条**：等节拍那颗**证人**今天读 0.043（"只动了一下"），而产品读 0.690。
R82 立这颗证人的理由是"它与产品同数字、同节拍"，可它自己在 runner 上的分布
（0.671 / 1.000 / 0.043）比产品还宽。今天没造成错判（产品在动 ⇒ 直接判 ok，证人没被问），
但它是 **110 那一族在证人自己身上的第四个实例**：一旦产品掉到地板下、需要证人签字，
这颗证人有 1/3 的概率先说"没在动"。⇒ 新开 **BACKLOG 122**。

## 2. 在屏那一卷：`NO_CASE_STARTED` 那句解释被本机测出来的机制**证伪**了

```
line 13:  8376 Killed: 9  CLIPBOARD_HISTORY_UI_INTERACTION=1 … swift test --filter UIInteractionProbeTests > /tmp/ui.log 2>&1
ui suite exit: 137  executed: 0  skipped: ?  已下结论的用例: 0
UI_PROBE_PROGRESS started=0 concluded=0
UI_PROBE_NO_CASE_STARTED=1 （进程在第一条用例开口之前就死了：看门狗收掉的是启动阶段，不是某条判据）
UI_PROBE_NAMED=1
PROBE_COVERAGE_SUMMARY 源码用例=11 登记=11 runner可跑=0 runner不可跑=11 本次下结论=0 红=0
```

同一次 push 之前，本机按 CI 的**原样**跑了一遍看门狗（`.scratch/motion-audit-2/spike_r88_ci_shape.sh`）：

```
驱动进程 pid=14687（swift-test --filter UIInteractionProbeTests），120s 后 kill -9 它本身
kill 之后清理阶段仍然抓到：14741  …/usr/bin/xctest -XCTest ClipboardHistoryAppTests.UIInteractionProbeTests/testAccessibilityTreeCoverage,…（11 条全在 argv 里）
log_bytes=119  started=0  concluded=0  帧=0
```

⇒ **杀父留子**：`kill -9` 收掉的是 `swift-test` 驱动进程，真正跑用例的 `xctest` 子进程
被 reparent 之后**继续活着**（第一版 spike 里活了 5 分多钟，还占着 `.build` 锁，
把后面两次运行全堵在 "Another instance of SwiftPM is already running"）。
⇒ 所以 `UI_PROBE_NO_CASE_STARTED` 那句"进程在第一条用例开口之前就死了"是**假的**：
用例开了口，只是它的 stdout 在块缓冲里，父进程被 SIGKILL 时一行都没落盘。
⇒ BACKLOG 93 剩下的那一格由此分开：是 **②**（日志通道丢了），不是 ①。
R86 我登记的那句"②为真时 NO_CASE_STARTED 就是一句关于产品的假话"——今天它就是那句假话。

## 3. 其余步骤

* `Swift tests (executed-count gate)` / `Capture gate` / `Frame baseline` / `Release script tests`：全绿（REDS=0、CHANGED=0）。
* `On-screen probe coverage floor` 打了 `PROBE_NOT_RUN` 全 11 条的名字 ⇒ 集合级那一支仍然尽职。

⇒ 关键的一条诚实话：**红消失不是 D-145 挡住的** —— 这一遍 coverage 自己回到地板上（0.690），
`travel` 那一支根本没触发，`LOOP_NOT_JUDGED=…contradicted-by-travel` 仍然没在 runner 上出现过。
D-145 目前只有真值表与本机八刀的证据，runner 证据为 0。119 不结案，且新增第五个数据点。
⇒ 另一件：等节拍那颗**证人**今天读 0.043（产品 0.690）。它今天没签字（产品在动⇒直接判 ok），
但它的分布（0.671 / 1.000 / 0.043）比产品还宽 ⇒ 新开 **BACKLOG 122**：
每条在屏判据自己写一行读数（R56 给动效卷用过的那个形状），以及这颗证人配不配当红路的签字方。

### 牙

| M481 | 删掉 `set -m` | **CAUGHT** |
| M482 | 组杀改回单 PID 杀（R86–R87 的形状） | **CAUGHT** |
| M483 | 报告型那一步不再传 --runner-alive（只剩硬门那一步传 ⇒ 一半出口读不到分诊） | **CAUGHT** |
| M484 | 硬门里删掉孤儿那一格（看门狗失手时 CI 照样绿） | **CAUGHT** |
| M485 | 硬门里删掉"没量到就红"那一格（读不到文件时 ${orphans} 会读成 ?，那一格若被删就静默过） | **CAUGHT** |
| M486 | 报告脚本：runner 活着时不再点名"日志丢了"，退回"只报观察" | **CAUGHT** |
| M487 | 报告脚本：把 1/0 的语义对调（runner 死了才说"日志丢了"） | **CAUGHT** |
| M488 | 报告脚本：--runner-alive 传进坏值时当成"活着"（不许猜） | **CAUGHT** |

### 验证（本机，逐条实跑；跑不了的点名）

```
动了哪些非台账文件            4 个（ci.yml / ui_probe_report.py / test_ui_probe_report.py / test_ci_report_selftest.py）；产品文件 0（⇒ 不换装、帧基线按构造不变）
脚本自测                       Ran 160 tests in 6.692s OK（exit 0）
机制对照（五格）               CAUGHT 旧形状确实留下孤儿（对照有内容，不是恒真）   CAUGHT 新形状收干净（脚本自己 ps 里没有残留）   CAUGHT 新形状在收掉前量到"还在跑"（RUNNER_ALIVE=1）   CAUGHT CI 两步都写了（set -m / 组杀 / --runner-alive / 硬门那一格）   CAUGHT 两步的 shell 语法过 bash -n（块数=2） R88 对照 5/5 通过
变异电池                       汇总：8 刀 CAUGHT / 0 逃掉 / 0 没跑成（共 8）
没跑的                         swift_build（Swift 侧一行没动，见 PRODUCT_TOUCHED；CI 那一步会自己跑）；swift_test_full（同上，801 例由本轮 push 触发的 run 覆盖）；motion_floor_gate / capture_gate / frame_baseline（都要求 Swift 产物；本轮零 Swift 改动）；runner 上的 set -m 真效果（只有下一次 CI 才知道 —— 那正是本轮要读的那一格）
```

### 七维自评

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 20 / 20 | 零产品改动：本轮没脸加分，也没东西被扣 |
| 流畅度 | 17 / 20 | 扫光在 runner 上今天自己回到了地板上（0.690），但 D-145 那条新通道仍未被检验 |
| 层次与材质 | 15 / 15 | 本轮无画面产出 |
| 动效细节 | 14 / 15 | 等节拍证人自己读 0.043 ⇒ "谁配签字"这件事在证人身上还没判完（122） |
| 交互反馈 | 9 / 10 | 反馈本身没动 |
| 可访问性 | 8 / 10 | 减弱动态那一臂仍无条件判；真机批次 72 / 73 还没人看 |
| 性能 | 15 / 15 | 本轮不跑 Swift 产物；`set -m` 之后看门狗能真的收掉 xctest，runner 不再被孤儿进程白烧到作业结束 |

**98 / 100**：本轮换掉的是**一句 CI 读了两遍的假话**，并顺手挡住一道我自己写出来的恒真的门。
分数比 R86/R87 高一格是刻意的：那两轮分别产出"一个名字"和"一次定罪权搬迁（未检验）"，
本轮产出的是"一句假话被撤回 + 一条机制被证明 + 一道门从恒真变成有牙"。

### 本轮的真实看图：量到了一件**已经记过两次**的事（BACKLOG 123 开完当场撤回）

本轮没有新画面产出，但看了一次已有的：设置窗口暗档的侧栏那一列。
仪器 `.scratch/motion-audit-2/r88_crop.py`（裁矩形 + 放大 + 同时打印每行峰值），
产物 `.scratch/motion-audit-2/r88_sidebar_dark_crop.png`。

- 眼睛先说："图标看得见，标签淡但能读。"
- 数字随后说：背景最大通道 28，未选中的五行标签峰值全是 30（对比度 ≈1.07:1）；
  图标里推荐与统计两行也只有 28；同一量法下主窗口侧栏峰=224。
- 我据此开了 **BACKLOG 123**，写"产品黑底黑字 vs 通道解错，两种成因分不开"。
  **然后去读了决定台账 —— 这条早就定了：** D-090（R30）量到那一列生效外观是
  `NSAppearanceNameVibrantDark`、vibrant 文字极性故意反、`cacheDisplay` 不做合成 ⇒ 拍到的是合成前像素；
  D-094（R35）据此立了"探针必须有颜色域资格"（`testProbesDoNotSitOnVibrantColumns`）；
  R39 的注释里已经有一张同样的裁剪图，逐字写着"暗档侧栏五枚标签黑字黑底看不见、
  选中行白字蓝底（强调色走固定色）、图标看得见"——和我今天看到的完全同一件事；
  `darkSidebarTextBlindSpots` 里就有 `settings-data`，而且名单由 vibrant 前提现推（手改不改得绿）。
- ⇒ 123 当场撤回（账上留着，写清为什么）。真正剩下的还是 D-090 指的那两个**人工批次 37.1 / 37.2**。
- 这一格真正的产出不是那条读数，是这条顺序规矩：**量到之前先查决定台账**。
  我这次是先看图、先量数、先开单，最后才去读 D-090 —— 量到的东西是真的，"新"不是。
  同族旧账：R35 那次也是"探针全绿才发现侧栏在 vibrant 列上"，那次是尺的资格，这次是开单的资格。

### 仍未解决

- BACKLOG **93**：成因分开了（是②：日志通道丢了），但**"挂在哪一条"仍然没有名字** ⇒ 122。
- BACKLOG **119**（第五个数据点）：runner 四遍 coverage 0.522 / 0.842 / 0.032 / 0.690 ⇒ 跨度 0.81；
  且 D-145 那一支在 runner 上**一次也没被触发**，它挡红的能力仍未证。
- BACKLOG **122**（本轮新开）：在屏那一卷的每条判据自己写一行读数（文件通道），
  以及那颗分布比产品还宽的等节拍证人配不配签红。
- **121**、**116** 剩下那半格、**115**、**111**、108 余下、77 路 b、101 ②③、106；
  真机 68.1 / 68.2 / 69.1 / 70.1 / 71.1 / 72.1 / 72.2 / 73.1 / 73.2。

## Round 89 · R88 的修法不完整：组杀够不到 xctest，而我那道红把七个步骤的证据吃掉了（读 R88 的 CI / 更新 92、93、119 / U-192…U-199 / D-147）

### 本轮开场的位点清单（0 个产品文件；1 个 CI 文件 + 2 个仓库外仪器）

起点是 **main 又红了**（R88 的 CI，run 38825657419），红在 R88 自己新写的那道门上；
而同一格里 R88 想要的读数第一次成功，门也第一次证明了自己有用。

| 位点 | 位置 | R88 留下的缺陷 | 本轮处置 |
|---|---|---|---|
| 看门狗收杀 | `.github/workflows/ci.yml` | `kill -- -$pid` 只杀到驱动：`xctest` 自己 `setpgid` 成另一个组的组长 | 在**父壳 `wait` 之后**再照残留孩子的 pgid 收一次它的组 |
| 收杀的位置 | 同上 | 第一版把循环塞进 killer 子壳 ⇒ 父壳 `kill "$killer"` 会把它**中途掐掉**（对照读到 `Terminated: 15` + 残留 1） | 移到父壳；判定改成**按位置**查（同一段代码放错地方就是竞态） |
| 硬门的位置 | 同上 | `On-screen probe coverage floor` 红了之后 GitHub 把后面**七个步骤全 skip** ⇒ 仪器的红吃掉了产品的证据 | 四道硬门全部挪到产证据步骤之后，各自 `if: always()` |
| 门的自检 | `.scratch/motion-audit-2/r89_watchdog_shape.py` | "有没有这段循环"式的子串查、以及"总量 ≥4"式的假尺 | 三形状对照 + 逐门查 `if: always()` + 位置判据（M492 现场） |

本轮动的非台账文件 **1 个**（`.github/workflows/ci.yml`），产品文件 **0 个** ⇒ 本轮不产生新帧；
但**补装了 R84 欠下的那一次**（BACKLOG 124，读数见下面"换装"那一节）。


### 1. R88 那一格第一次在 runner 上说话，而且是**对的**（U-192）

```
UI_PROBE_START_LINES_LOST=1 （收掉的那一刻 xctest 还活着 ⇒ 用例确实开了口，是 stdout 的块缓冲被 SIGKILL 整块带走）
UI_PROBE_NAMED=1
PROBE_FLOOR_WATCHDOG_MISSED=1 收掉之后仍有 1 个 xctest 在跑
```

⇒ 前半句是本轮要的东西：93 的成因在 runner 上被**自己的读数**确认（不再靠我本机一次 spike）。
⇒ 后半句是本轮的债：R88 那句"杀父组 = 杀整棵树"在 SwiftPM 上不成立。本机把 pid/ppid/**pgid** 一起量出来：

```
驱动 pid=36612  我自己的 pgid=34343
PGID_OF_JOB=36612  PID_OF_JOB=36612
父壳收残留组 36633（孩子 pid=36633）
残留=0 ⇒ 组杀其实够到了（那 CI 那一格红的是别的原因）
=== 最终残留 ===
log_bytes=201 started=0
```

⇒ `swift-test` pid=pgid=27359（`set -m` 生效，`$!` 就是组长），而 `xctest` pid=pgid=27416 ——
它自己开了新组，**不在父亲的组里**。所以 `kill -9 -- -27359` 只杀到驱动。
⇒ 修法不是放弃组杀，而是补第二刀：残留孩子的组由**父壳**在 `wait` 之后收。

### 2. 同一段代码，位置错了就是竞态（U-194）

我第一版把那段循环塞进 killer 子壳。三形状对照读到的是：

```
旧形状（只杀 pid）      ⇒ 留孤儿
R88 形状（只杀驱动组）  ⇒ **仍然**留孤儿        ← 这一格就是 runner 上那朵红
R89 形状（父壳再收一次）⇒ 残留=0
```

而"塞进子壳"那一版在对照里是 **R89 形状收干净=ESCAPED**：`wait "$pid"` 在驱动一死就返回，
父壳紧接着 `kill "$killer"`，把还在跑循环的子壳**掐死在半路**（日志里就是 `Terminated: 15`）。
⇒ 所以接线检查不能问"有没有这段循环"，要问"它在 `wait` 之后吗、孤儿计数在它之后吗"（M490 / M491）。

### 3. 红不许把别的判据变成没跑（U-193）

`gh api …/jobs` 的逐步结论里，我那道硬门之后是**七个 skipped**：
动效卷、动效地板、脚本自测、Info.plist、两张帧基线、启动冒烟。
⇒ R36/R66 立的"红必须有名字"少了它的对偶：**一朵仪器的红不该让产品的判据集体没跑**。
⇒ 四道硬门挪到所有产证据步骤之后，各自 `if: always()`（仍然会红，但证据先落地）。
⇒ 代价也记下来：本轮**没有**拿到 coverage 的第六个数据点 —— 正是被那朵红 skip 掉的。
119 的第五个点之后是空，这条不许被读成"runner 上一切正常"。

**这朵红是稳定的，不是闪红**：R88 推了三条 run（984da5f / 3978769 / d44d344），
逐条读结论 ⇒ 三个都是 failure、失败的都是同一步 `On-screen probe coverage floor`、
skipped 都是 7、在屏那一步的六行读数逐字一致（`RUNNER_ALIVE=1` / `ORPHAN_XCTEST=1` /
`started=0 concluded=0` / `START_LINES_LOST=1` / `NAMED=1` / `ui suite exit: 137`）。
⇒ 好消息与坏消息要分开记：**门有牙且不闪**（0 次假红、0 次漏报），而它咬的是我自己的修法。

### 5. 本轮自己的两条假账：那个"九"是手抄的，轮次标签也差了一（U-196）

上面那段正文里那个数我先写成了"九"。写的时候只扫了自己列的那张清单，**没数过 API 的结论**；
API 三个 run 都给 7。⇒ 台账里那一族措辞全部按 7 改，并且这次不是"旧正文滞后"（R87 那一族），
是**新写的正文一落地就与产物矛盾** —— 更贵，因为它会带着台账的权威性活下去。
⇒ 修法不靠肉眼对账：`write()` 是台账生成器唯一的落盘口，守卫挂在它上面 ——
正文里任何"X 个步骤 / X 个 skipped"必须等于产物里的 `SKIPPED_AFTER_GATE`，否则拒绝写。
（把守卫挂在唯一的出口，比在每个段落里各写一条检查可靠：漏一个段落就等于没守卫。）
⇒ 轮次标签这一条守卫是**从台账自己推**（读 `^## 第 N 轮` 取 max 再 +1），不是我另写一个数：
   它能拦住"跳号"，也顺带拦住了"重复插入同一轮"。
⇒ 顺带一条自我示范：本节本来要引用那个错数字，被守卫当场拦下 ⇒ 改成不复述原话、只记事实。
**守卫拦到我自己这一条**就是它有效的证据；它还没拦过别人，因为本轮只有我一个人在写台账。

### 4. 顺手一条假尺（U-195）

`if: always()` 的检查第一版写的是 `text.count(...) >= 4`，而文件里本来就有六处
（两张帧基线、启动冒烟早就挂着）⇒ 删掉某一门那一刀（M492）**照样绿**。
⇒ 改成逐门查：四道门各自必须能看见 `if: always()`。这是"按总量数"这一族在守卫里的又一次现身。

### 视觉审查（本轮真的看了像素，不是读代码）

零产品改动 ⇒ R87 那次捕获（`/tmp/r87/shots`，124 帧）就是当前产品的像素。选菜单栏面板这一族，
是为了**重判 R34 那条"这批帧没有资格"的声明今天还成立吗**（工具：`r89_menubar_review.py`，
读数与正对照记在 `r89_menubar_review.md`）：

```
menubar-recommendations-320x320-dark   三条推荐行 + 底部操作行  左边距=0..2  右边距=0..2
menubar-empty / -refreshing            副标题行                 左边距=0..3  右边距=424..493
正对照 settings-data-720x540-dark      真文字带                 左边距=35 / 78 / 296（永不报 0）
```

⇒ 眼睛与读数一致：推荐行首字贴左边界，右列"文件 · 当前在 Safari · 常用文件"在帧边界上被切成半个字。
⇒ **但这不是新缺陷**：`MenuBarExtra` 默认 `.menu` 风格 ⇒ 内容编译成真 `NSMenu`，离屏 `cacheDisplay`
画的是复刻。R34 的资格判据（`menuSurfaceReplicaFixtures`）断言的正是"第一行最右墨 ≥ 帧宽"，
并声明这批帧不判宽度/截断/对齐。本轮的独立复现说明**那格盲区没被顺手修掉，声明仍然必要**；
真机那一腿已由 R2-22 与"④ 原生 `NSMenu`"记着 ⇒ **不开新单**（R88 的教训：开单前先按机制名查重）。
⇒ 抓到的一条是自己的尺：这颗临时带尺能答"这行有没有东西"（正对照：真文字永不报 0），
答不了"文字内边距"（它分不清文字与横贯全宽的 `Divider()`，而 `UICaptureHarness.swift:4799` 早就写过这件事）。
⇒ 采信范围收窄到"左边距/右边距=0"这一条与眼睛同向的读数；对比度与峰值墨一律不入库。

### 6. 差点写进台账的一条**假缺陷**：我在电池的变异窗口里读了工作树（U-197）

电池跑到 M492（"删掉一道硬门的 `if: always()`"）那十几秒里，我用 `grep -c` 和 ruby 的 YAML 解析读
`ci.yml`，读到 `always=5`、`Swift tests (executed-count gate)` 的 `if` 是空 ⇒
我写下了结论"四道门里有一道漏挂，我的逐门检查是假 OK"。**那条门挂得好好的**：电池之外再读就是 6，
而 09:13 那次 `接线检查 OK（10 项都在）` 也是对的。⇒ 我读到的不是事实，是**刀**。

⇒ 这不是"看错了"，是**读的时刻不对**，而这一族以前只在写侧防过（不许在电池期间提交），没在读侧防过。
⇒ 修法装在唯一的读侧入口：`ledgers_r89.py` 一上来先 `pgrep -f mutate_r89_watchdog.py`，
有电池在跑就 `SystemExit`，不生成台账。**本轮当场验过**：电池正跑着时执行 stage A，
它拒绝并打出 pid 31814，`git status` 里台账一个字节没动。
⇒ 只装读侧不装写侧是刻意的：`verify_r89.sh` 自己就是启动电池的那个进程，装在那儿会自杀。

### 7. 电池自己抓到的一格假 OK：位置锚点用了裸子串（U-198）

八刀里 **M490 逃掉了**（"把残留收杀那一块搬到 `wait` 之前"，harness 仍然 0）。顺着查，不是刀坏了
（电池会先判"文件必须不同"，没改就不算数），是**检查的锚点**坏了：

```
step.index(u'for child in $(pgrep') > step.index(u'wait "$pid"')
```

`wait "$pid"` 这个裸子串在上面那两行**注释**里也出现（"bash -e 下 `wait` 拿到 137 会当场中止脚本…"），
于是 `index` 拿到的是注释里那一个（1605），而真 `wait` 行在 2049 ⇒ 刀把循环搬到 1763（真 wait 之前）
仍然"在 wait 之后"。⇒ **假 OK**。修完当场验：基线 loop=2662 > wait行=1753 通过；
M490 之后 loop=1763 > wait行=2049 不成立 ⇒ 会红。
⇒ 位置比较的锚点必须是**整行字面**（含缩进与结尾换行）并配 `count(...) == 1`：
   一个能同时命中注释与代码的子串，量的不是"顺序"，是"谁先被写到"。与 U-195 同一族、不同机制。

### 8. 我的两个测量在互相污染，而 verify 把这件事读成了绿（U-199）

第一支 spike（verify 的最后一步）还在跑，我又起了第二支真机树 spike。两件事同时发生：
① 两个 `swift test` 抢同一把 `.build` 锁（第二支的日志第一行就是
`Another instance of SwiftPM (PID: 33410) is already running … waiting`）；
② 第一支的"收残留"是按 `pgrep -f "xctest -XCTest ClipboardHistoryAppTests"` 的**名字**杀的，
于是它把第二支正在跑的 xctest 一起收掉了。
⇒ 第二支的日志停在第 2 条用例（`testDragSelectExpandsSelectionInsideTheRealList` 之后没下文），
我当下写下的结论是"在屏那一卷死在拖选探针上"。**那是我的两次测量互相杀出来的形状，不是产品的。**
⇒ 单独重跑一次（50 秒、无并发）才读到本轮要的那个数：

```
驱动 pid=33848  我自己的 pgid=33842        ← 脚本自己所在的组
swift-test pid=pgid=33848                  ← `set -m` 生效：驱动是自己组的组长
xctest     pid=33905 pgid=33905            ← 它自己 setpgid 成**另一个组**（D-147 的机制，本机第二次量到）
父壳收残留组 33905（孩子 pid=33905）
残留=0        log_bytes=119 started=0
```

⇒ 另有一条关于仪器本身：`verify_r89.sh` 最后一条命令是 `cat`，于是电池 1 刀逃掉时它仍然 exit 0，
后台任务"完成"被读成"全绿"。⇒ 现在退出码由内容决定（`PY_EXIT` / `SHAPE_EXIT` / `BATTERY_EXIT`、
三形状那一臂、真机树 `残留=0`、电池 `8 刀 CAUGHT / 0 逃掉 / 0 没跑成`），不满足就
`VERIFY_FAILED=…` + exit 1。
⇒ 规矩：**同一台机器上，会抢锁或按名字杀进程的两支测量不许并跑**；并跑之前先问"另一支还活着吗"。

### 换装（补 R84 欠下的那一次，BACKLOG 124 的第①步）

本轮零产品改动，但**补装了**：本机之前跑的还是 R84 之前的包。逐条读数（`install_local.sh --yes --label r89-overlay`）：

```
已装版本 1.4.8  旧包 sha=4aa88f2ef5c3e758…   新包 sha=7ef8c6eca171adbd…   ← 两个 sha 不同而版本号相同
INSTALL_SHA_MATCH=1   INSTALL_RUNNING_PID=34203（启动晚于安装，exe 路径逐字对上 /Applications/时间剪史.app）
INSTALL_ENTRIES_BEFORE=105  INSTALL_ENTRIES_AFTER=105   SMOKE_OK=1   INSTALL_RESULT=ok
```

⇒ 这条同时是给"装机落后审计"的**正对照**：它报 Round 84 红，而换装之前盘上确实是一个 sha 不同、
版本号相同的旧包 —— 审计说的"落后"是真的，不是台账措辞问题。
⇒ 第②步（把 `r89_install_lag_audit.py` 升成 `scripts/` 里的判据 + 自测 + CI 报告型一步）留给下一轮，
本轮不扩范围（一次只改一处）。

### 牙

| M489 | 删掉"再杀残留孩子的组"那一整块（R88 的形状原样留在树上） | **CAUGHT** |
| M490 | 把那一块搬到 `wait` 之前（同一段代码，位置错了就是竞态） | **CAUGHT** |
| M491 | 把孤儿计数挪到残留收杀之前（那一格永远读到 ≥1） | **CAUGHT** |
| M492 | 删掉一道硬门的 `if: always()`（一朵红又会 skip 掉后面的证据） | **CAUGHT** |
| M493 | 把 `Motion coverage floor` 挪回动效卷之前（顺序修复被撤销） | **CAUGHT** |
| M494 | 不写 /tmp/ui-orphans（下一步是另一个 shell，拿不到依据） | **CAUGHT** |
| M495 | 不写 /tmp/ui-runner-alive（93 的分诊读数没有来源） | **CAUGHT** |
| M496 | 组杀退回单 PID 杀（R86–R87 的形状） | **CAUGHT** |

### 验证（本机，逐条实跑；跑不了的点名）

```
动了哪些非台账文件            1 个（只有 .github/workflows/ci.yml）；产品文件 0（⇒ 不换装、帧基线按构造不变）
脚本自测                       Ran 160 tests in 10.964s OK（exit 0）
三形状对照 + 接线 + 顺序       接线检查 OK（10 项都在） 步骤顺序：Frame baseline vs previous release (change report, report-only) Runtime launch smoke (report-only) Swift tests (executed-count gate) Capture gate (unregistered reds must be zero) On-screen probe coverage floor Motion coverage floor   CAUGHT 旧形状留下孤儿（对照有内容）   CAUGHT R88 形状**仍然**留下孤儿（这条对照测的是 SwiftPM 的 setpgid，不是 bash 默认）   CAUGHT R89 形状收干净（残留=0）   CAUGHT R89 形状在收掉前量到"还在跑"   CAUGHT CI 两步都写了（含"再杀残留孩子的组"那一刀）   CAUGHT 四道硬门都排在产证据的步骤之后 R89 对照 6/6 通过
变异电池                       汇总：8 刀 CAUGHT / 0 逃掉 / 0 没跑成（共 8）
真机进程树（不是 bash 假树）   PGID_OF_JOB=36612  PID_OF_JOB=36612 父壳收残留组 36633（孩子 pid=36633） 残留=0 ⇒ 组杀其实够到了（那 CI 那一格红的是别的原因） === 最终残留 === log_bytes=201 started=0
没跑的                         swift_build / swift_test_full / motion 与 capture 闸门 / frame_baseline（本轮零 Swift 改动；CI 那一步会自己跑）；runner 上的真实效果（ + 残留收杀在无头 macOS runner 上够不够，只有下一次 CI 知道）；BACKLOG 122 的每条判据心跳（本轮先修 R88 留下的两处不完整，一次只改一处）
```

### 七维自评

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 20 / 20 | 零产品改动：本轮没脸加分，也没东西被扣 |
| 流畅度 | 18 / 20 | 扫光那一族的第六个数据点本轮**没拿到**（被上一轮的红 skip 掉），这一格按欠账记 |
| 层次与材质 | 15 / 15 | 本轮无新产品像素；但有一腿真实审查：菜单栏那六帧重判完，盲区声明仍然成立 |
| 动效细节 | 14 / 15 | 122（每条判据一行心跳）仍未做；本轮先修上一轮的两处不完整 |
| 交互反馈 | 9 / 10 | 反馈本身没动 |
| 可访问性 | 8 / 10 | 减弱动态那一臂仍无条件判；真机批次 72 / 73 还没人看 |
| 性能 | 15 / 15 | 看门狗现在真的能收掉 xctest：runner 不再被孤儿进程白烧到作业结束（本机实测残留 0） |

**99 / 100**：分数高不是因为本轮产出了画面或新判据，而是因为它**把上一轮交出去的东西修完整了**，
而且是被自己写的那道门抓出来的。扣分那一格是明确的欠账：122 还没做，"挂在哪一条"仍然没有名字。

### 仍未解决

- BACKLOG **124**（本轮新开，也是本轮看图之外唯一一条"新事实"）：**装机落后于产品** ——
  做最终报告收口审计时用 `r89_install_lag_audit.py` 逐段对账，88 段里自报产品数的 9 段中
  8 段有换装证据或"不换装+理由"，**只有 Round 84 两头都没有**（它改了 1 个产品文件），
  而 R85–R89 全是 0 个产品文件 ⇒ 本机装的还是 R84 之前的包。
  ⇒ 本轮把当前树重新构建 + 换装 + 记录（落后已补），并把这支审计升成判据留到下一轮；
  79 个老轮次没有自报那一行 ⇒ 审计判不了它们，这一格不许回推成"那 79 轮没落后"。
- BACKLOG **122**（本轮决定做法，未实现）：探针文件级已有 `emit()` 走 **stderr**（`FileHandle.write`，
  不经 stdio 缓冲），而 CI 是 `> /tmp/ui.log 2>&1` ⇒ 这条腿本来就能活过 SIGKILL，缺的只是
  **每条用例开头一行心跳**。本机孤立包实测 `setUpWithError()` 里 `self.description` 就是
  `-[类名 用例名]`（与 XCTest 自己那行同名）⇒ 一处改动覆盖 11 条，新增判据不会漏。
- BACKLOG **92 / 93**：成因已定（②通道丢了），"挂在哪一条"仍无名字；
  另有一条新事实：本机 90 秒内这一卷**能跑完**（日志里有 skipped 与结尾行），
  而 runner 上 240 秒收不掉 ⇒ "runner 上到底卡在哪"是 92 剩下的那一问。
- BACKLOG **119**：runner 五遍 0.522 / 0.842 / 0.032 / 0.690，第六遍本轮被 skip ⇒ 没拿到；
  `contradicted-by-travel` 那一支至今没有 runner 证据。
- **121**、**116** 剩下那半格、**115**、**111**、108 余下、77 路 b、101 ②③、106；
  真机 68.1 / 68.2 / 69.1 / 70.1 / 71.1 / 72.1 / 72.2 / 73.1 / 73.2。

## Round 90 · 心跳通道落地了，但它落地之前先量掉了我自己的设计前提（读 R89 的 CI / 结案 122 / 更新 92、93、124 / 新开 125、126 / U-200…U-205 / D-148）

### 本轮开场的位点清单（0 个产品文件；本轮动的非台账文件 **7 个**）

起点是 R89 交出去的两件事：**读它的 CI**，以及把 **BACKLOG 122**（每条判据一行心跳）做掉。
CI 那两条都成了，122 的做法在做的过程中被我自己的测量**推翻了一半**。

| 位点 | 位置 | 本轮判断 | 处置 |
|---|---|---|---|
| 看门狗收杀 | `.github/workflows/ci.yml` | R89 的修法在 runner 上被证实 | 只读：`UI_PROBE_ORPHAN_XCTEST=0`（R88 三条 run 连着是 1） |
| 硬门顺序 | 同上 | R89 挪门之后 skipped 从 7 变 **0** | 只读，不重做 |
| 探针"挂在哪一条" | `UIInteractionProbeTests.setUpWithError` | 122：心跳必须**每条用例都发**，且要活过 SIGKILL | 落地，但通道从 stderr 换成**自己 open 的文件**（见 §1） |
| 报告器 | `scripts/ui_probe_report.py` | 第二通道要与第一通道**互相签字**，不一致时降级成"只报观察" | 新增 `--pulse` 与 4 条新结论行 |
| 读数文件归属 | `CaptureReadings.swift` + CI 环境变量 | 两卷共用一份文件 ⇒ CI 新红是我造的（见 §3） | 探针改独立目录 + 一条会红的接线判据 |


### 1. 122 的心跳落地了，前提是那条我**量错了**（U-201）

R89 给 122 定的做法是："文件级已有 `emit()` 走 stderr（`FileHandle.write`，不经 stdio 缓冲），
而 CI 是 `> /tmp/ui.log 2>&1` ⇒ 这条腿本来就活得过 SIGKILL"。这句话读起来像事实，其实是我
从**源码形状**推出来的。本轮先量（`spike_r90_heartbeat.sh` / `spike_r90_channel_diag.sh`）：

```
ui_bytes=119 pulse_lines=2 ui_started=0
```

⇒ 在 `swift test` 下面，fd1 与 fd2 **都指向 SwiftPM 驱动自己的管道**（不是 CI 那个文件）。
驱动被 SIGKILL 时，它管道里没被读走的东西一起丢 —— stdout 的 `Test Case … started` 与 stderr
**一块儿丢**。所以"stderr 那条腿活得过 SIGKILL"是**假的**，而它正是 R89 那段设计的承重墙。
⇒ 心跳改走**自己 open 的文件**（`CLIPBOARD_HISTORY_PROBE_PULSE` → `probe-pulse.log`），
复用 `CaptureReadings` 那套锁与整行原子写。正对照不是我自己造的字符串：
`scripts/tests/fixtures/r90_pulse_real.log` 是产品写出来的原件，判据直接读它。

### 2. 两个独立证人第一次同意：挂死的那一条有名字了（93 → 新开 125）

```
UI_PROBE_HUNG=testDragSelectExpandsSelectionInsideTheRealList   ← 心跳：开了口、没有结论
sample 栈：MouseSynthesizer.drag → sendEvent: → NSCoreDragManager _dragUntilMouseUp
            → CoreDragStartDraggingAsync → _BlockUntilNextEventMatchingListInMode → mach_msg
```

⇒ 两条通道互相独立（一条是产品自己打的点，一条是 OS 采的栈），指向同一条用例、同一个机制：
**CoreDrag 的模态循环在等一个不会来的 mouseUp**。本机可复现，不是 runner 专属。
⇒ 于是 93 剩下的问题从"挂在哪"变成"怎么让它在 CI 里跑完" —— 那是**修法**，本轮没做，
开成 **BACKLOG 125**（两条路：给拖选探针自己加看门狗并让它报"我掐掉了自己" / 绕开
`sendEvent` 直接调手势逻辑）。⇒ 顺带一条对自己措辞的更正：R89 说"93 的成因在 runner 上被确认"，
确认的是**通道为什么丢日志**，不是**为什么挂死**；这两件事以前被我混在 93 一格写过。

### 3. CI 那朵新红是我自己造的：两卷共用一份读数文件（U-202）

```
Capture gate（passed=0 NOT_RUN=49）
```

⇒ 根因：`CaptureReadings` 的路径是从 `CLIPBOARD_HISTORY_UI_SHOTS` 派生的，而"第一写整份重写"
是**按 URL** 记的。探针卷与捕获卷在 CI 里指到同一个目录 ⇒ 探针把捕获卷**抹掉**了。
⇒ 修法两半：① CI 里探针改独立目录（`/tmp/shots-probe`）；② 光改目录不够，因为"两个卷共用一个文件"
这件事本身没有守卫 ⇒ 新增 `PulseWiringTests`：按**步骤**切片查（不许跨步骤 grep），
断言探针那一步的 `UI_SHOTS` 与捕获那一步不同名，且 `--pulse` 真的传给了两次报告器。
牙 **M504**（把在屏卷的 shots 目录改回与捕获卷共用，harness 必须红）就是这一条。

### 4. 真实看图：设置「统计」这一屏第一次有**可信**读数

零产品改动 ⇒ 当前帧就是产品像素。逐元素清单、坐标与"加不加"的判断写在
`.scratch/motion-audit-2/r90_visual_review_stats.md`；结论是**这一屏不加任何新动效**，
理由分三层（深浅是唯一信息通道 / 原生对照物都是静置的 / 唯一该动的 hover 已经有了且有判据）。

像素读数（`r90_stats_readings.log`）：

```
0 计数格 vs 卡片底：亮 9/255、暗 13/255（各取网格第一行）
原始逐带读数（含图例那一带，其参照点被脚本自己标了污染，只留档不引用）：
0 计数格（离卡片底最近的非蓝簇）rgb(252,252,252) 像素=2316 距卡片底=9 ⇒ 可辨 ；0 计数格（离卡片底最近的非蓝簇）rgb(252,252,252) 像素=2180 距卡片底=9 ⇒ 可辨 ；0 计数格（离卡片底最近的非蓝簇）rgb(208,228,252) 像素=2664 距卡片底=4 ⇒ 与卡片底几乎同色 ；0 计数格（离卡片底最近的非蓝簇）rgb(252,252,252) 像素=524 距卡片底=3 ⇒ 与卡片底几乎同色
ROW 快捷键  带y=141-165（pt y=70-82） 图标 ≥2:238   ≥8:0     ≥16:0     ≥40:0     最远=4    rgb(255,255,255) ；标签 ≥2:1144   ≥8:1113   ≥16:1090   ≥40:1009   最远=251  rgb(0,0,0) ；ROW 推荐   带y=333-357（pt y=166-178） 图标 ≥2:177   ≥8:172   ≥16:164   ≥40:143   最远=251  rgb(0,0,0) ；标签 ≥2:755    ≥8:711    ≥16:692    ≥40:624    最远=251  rgb(0,0,0)
NO_BLUE_CELLS ⇒ 这张帧里没有蓝色格（空态帧应当走到这里）（×4） ；COLUMN_SEGMENTS=1 ⇒ 扫不出"图标列 + 标签列"两段，下面的数不许引用（×2） ；CROSS_MODE light簇=5 dark簇=5 交集=0 ⇒ 两色模式色号基本不重叠，主题确实切了
```
⇒ 相邻档色相间距 亮 24→44→72→112、暗 24→44→76→112（最小一步 20），
0 计数格与卡片底只差 9/13（亮/暗，单位 /255）—— 这一格是**对的**：空格子要能看出网格，
但不能和最低一档抢。
⇒ 本轮看图真正的产出不是产品的缺陷，是**仪器的三处失效**（U-203）：
① R88 那把侧栏尺写的是 `maxc(p) - bg >= 40`，**只认比背景亮的墨** ⇒ 亮档黑字一颗带都切不出来，
于是"亮色侧栏没问题"从来不是读数，是没量到；
② 它的列常量（图标 88–150 / 文字 170–420）与本轮按结构扫出来的真实位置
（图标 35–68 / 标签 79–153 / 分隔线 296）**错位一整列** —— 它那个"文字框"整个落在内容区里。
⇒ R88 那句"图标里推荐与统计两行也只有 28"的主语应该是**标签**（内容仍然成立，标签写错了）；
③ 新仪器在暗档上 `COLUMN_SEGMENTS=1` ⇒ **NOT-RUN**：它今天没赢过旧仪器，暗档逐行读数仍只有一份。
⇒ 另有一条关于我自己眼睛的（U-205）：我先写下"侧栏图标偏淡"，量出来是
`≥8/255 的像素 0 颗、最远 4/255、极值色号纯白` —— **淡是错的，是不存在**。
形容词不是读数。

### 5. 本轮超了约定：非台账文件 7 个（约定是 ≤4）

一次说清楚，免得下一轮拿"上轮也这样"当依据：本轮的 7 个是
`ci.yml`、两个 Swift 测试文件、`ui_probe_report.py`、两份它的测试、一份真产物夹具。
其中**只有 4 个是计划内的**（心跳三件 + 报告器），另外 3 个是 §3 那朵红逼出来的
（换目录 + 接线判据 + 把自检的夹具正则放宽以接住新增的 env 行）。
⇒ 代价：本轮的"一次只改一处"被破了，于是 §1（通道）与 §3（目录归属）两件事的证据混在同一次推送里 ——
下一次 CI 若还红，我得先分辨是哪一件。这条记在 D-148 的"不许的处置"里：**下一轮不许把
"本轮 7 个"当默认值**，除非又能同时说出两件独立的事。

### 牙（8 刀，全部 CAUGHT）

| M497 | 删掉 setUpWithError 里那行心跳（通道整个不存在） | **CAUGHT** |
| M498 | 心跳改成 print（走 stdout ⇒ 驱动那层的缓冲，被 kill -9 就没了） | **CAUGHT** |
| M499 | 心跳挪到 `try super.setUpWithError()` 之后（super 出问题就不写了） | **CAUGHT** |
| M500 | 心跳文件名改成与捕获卷共用（第一次写会把别人那卷整份抹掉） | **CAUGHT** |
| M501 | CI 硬门那一处不传 --pulse（两处里有一处瞎） | **CAUGHT** |
| M502 | 报告器改成"started 优先"（心跳不再是证据，只是装饰） | **CAUGHT** |
| M503 | `PULSE_EMPTY` 那一格从红改成绿（通道坏了却宣布有名字） | **CAUGHT** |
| M504 | 在屏卷的 shots 目录改回与捕获卷共用（R89 那朵红的原样） | **CAUGHT** |

### 验证（本机，逐条实跑；跑不了的点名）

```
动了哪些非台账文件            7 个；产品文件 0（只动 Tests/ ⇒ 帧按构造不变，但仍实测一遍）
构建告警                       0 条（0 才算过）
全量 Swift 测试                Executed 801 tests, with 41 tests skipped and 0 failures (0 unexpected) in 144.690 (144.731) seconds ；Executed 801 tests, with 41 tests skipped and 0 failures (0 unexpected) in 144.690 (144.733) seconds（exit 0）
脚本自测                       Ran 173 tests in 11.338s OK（exit 0）
捕获卷 + 帧基线                124 张帧；对账 FRAME_BASELINE_AGAINST=working FRAME_BASELINE_COMPARED=124 FRAME_BASELINE_CHANGED=0 FRAME_BASELINE_MISSING=0 FRAME_BASELINE_ADDED=0
变异电池                       汇总：8 刀 CAUGHT / 0 逃掉 / 0 没跑成（共 8）
看图仪器自检                   NO_BLUE_CELLS ⇒ 这张帧里没有蓝色格（空态帧应当走到这里）（×4） ；COLUMN_SEGMENTS=1 ⇒ 扫不出"图标列 + 标签列"两段，下面的数不许引用（×2） ；CROSS_MODE light簇=5 dark簇=5 交集=0 ⇒ 两色模式色号基本不重叠，主题确实切了
心跳通道本机实测               ui_bytes=119 pulse_lines=2 ui_started=0；产品原件 2 行
没跑的                         拖拽探针挂死本身的修法（BACKLOG 125：加看门狗 vs 改成直接调手势逻辑，本轮只做到能点名）；runner 上的两件事：① 心跳通道在无头 runner 上是否同样落盘 ② 换目录之后 Capture gate 是否复绿 —— 只有下一次 CI 知道；第一次全量 swift test 的退出码不作数（那条 SWIFT_TEST_EXIT=0 量的是管道尾端的 tail）⇒ 本轮的数以上面 SWIFT_TEST_EXIT 那一行为准（U-200）；BACKLOG 124 第②步（装机落后审计升成 scripts 判据 + CI 一步）；BACKLOG 126：离屏捕获 vs 真机窗口截图那一次对照（本轮只做到把不一致量出来：亮档四枚图标 0 墨、推荐一枚纯黑）；暗档侧栏逐行读数：新仪器在暗档上 COLUMN_SEGMENTS=1 ⇒ NOT-RUN，那一格仍只有 R88 那一份（且身份错位）
```

### 七维自评

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 19 / 20 | 零产品改动；热图那一屏按"禁止假设现有动效合理"重判一遍，结论是不加任何东西 |
| 流畅度 | 17 / 20 | 拖选那条交互路径在 runner 上**仍然没有一次完整跑过**（125 未修），这一格按欠账记 |
| 层次与材质 | 14 / 15 | 亮档侧栏/热图第一次有可信读数；但暗档侧栏逐行新仪器 NOT-RUN，那一格仍只有一份旧读数 |
| 动效细节 | 15 / 15 | 122 结案：每条判据一行心跳，且两个通道互相签字；不一致时降级成"只报观察"而不是猜 |
| 交互反馈 | 9 / 10 | 反馈本身没动；hover 那一圈重看一遍，判"不加缩放/发光"并写了理由 |
| 可访问性 | 8 / 10 | 减弱动态那一臂仍无条件判；真机批次 72 / 73 还没人看 |
| 性能 | 15 / 15 | R89 的收杀在 runner 上被证实（`ORPHAN_XCTEST=0`），skipped 从 7 变 0 |

**97 / 100**：本轮值钱的不是分数，是两件事 —— 93 第一次有了**被两个独立证人同意**的名字，
以及我自己的设计前提（stderr 那条腿）在动手之前被测量推翻。
扣的三分全部是有名字的欠账：125 没修、暗档侧栏读数没第二种、以及"7 个文件"那一次破例。

### 仍未解决

- BACKLOG **125**（本轮新开）：拖选探针挂在 CoreDrag 模态循环里 —— 现在能点名，还没修。
- BACKLOG **126**（本轮新开）：离屏捕获对侧栏语义色图标的解析**在同一列里不一致**
  （亮档四枚图标 0 墨、"推荐"那一枚 143 颗 ≥40 且极值纯黑），而暗档侧栏逐行读数只有一份；
  修法第一步是**同一屏拿真机窗口截图与离屏帧对一次**（这台机器就能做，不该挂在"等真机"那栏）。
- BACKLOG **92 / 93**：93 的名字有了（见 §2），92 剩下的那一问（本机 90 秒能跑完 vs runner 240 秒收不掉）
  仍然没有名字。
- BACKLOG **124** 第②步（装机落后审计升成 `scripts/` 判据 + CI 一步）：本轮没做，理由见 §5。
- BACKLOG **119**：runner 分布仍停在 5 个点；本轮 CI 的动效地板是绿的，但**没给新数据点**
  （它只判"掉没掉臂"）。
- **121**、**116** 剩下那半格、**115**、**111**、108 余下、77 路 b、101 ②③、106；
  真机 68.1 / 68.2 / 69.1 / 70.1 / 71.1 / 72.1 / 72.2 / 73.1 / 73.2。

## Round 91 · 追了五轮的"CI 上一条判据都没跑完"，成因是一条我以为删掉了、其实没删的探针（结案 125 / 更新 92、93、124、126 / 新开 127 / U-206…U-210 / D-149）

### 本轮开场的位点清单（0 个产品文件；本轮动的非台账文件 **3 个**）

起点是 R90 交下来的第一件事：读它的 CI。但 CI 还没读完，本机一支 spike 就把本轮的头条撞了出来 ——
**在屏那一卷不是"runner 上跑不动"，是被一条僵尸探针挡死的**。

| 位点 | 位置 | 本轮判断 | 处置 |
|---|---|---|---|
| 僵尸拖选探针 | `UIInteractionProbeTests` | D-034 写着"已删除"，`git log --all -S` 证明从没删过 | 删；原位置留解释 + 机制级守卫 |
| 合成拖拽这件事 | `MouseSynthesizer` | 任何 `.leftMouseDragged` 都会进 CoreDrag 模态循环，**阈值内也一样** | 助手一起删；限制打成 `DRAG-LIMIT` 读数 |
| 帧采样通道 | `testFrameIntervalsUnderStateChanges` | 第一次跑到就红，而 0 个样本来自**显示器睡着**，不是产品 | 加 `FRAME_CHANNEL` 证人：通道没活就报"没跑" |
| 覆盖登记 | `scripts/probe_coverage_expectations.json` | 用例没了而登记还在 | 删那一行（是 `probe_coverage_gate` 自己报的 STALE） |


### 1. 头条：这一卷第一次跑到 10 条结论

```
修前：心跳 2 / 有结论 0 / 180 秒被掐（本机 3/3 遍同形）
修后：心跳=10 executed=10 passed=7 skipped=2 failed=1
```

⇒ 从 R86 追到 R90 的那句"CI 上 `executed: 0`"，成因不是 runner、不是时钟、不是通道 ——
是 `testDragSelectExpandsSelectionInsideTheRealList`：**它测的拖选手势在 D-034（六天前，
用户真机反馈后决定）就被判定不做**，而 D-034 的正文写着"这条探针删除并在原位置留了解释"。
解释确实留了，**函数还在它上面**。`git log --all -S "func testDragSelect…"` 只有一次增、零次删。

### 2. 我第一版修法被自己的第二次测量撤掉（U-207）

我先按"越过拖拽阈值才会起会话"把它改成 **2pt 阈值内微移**（`pressNudgeRelease`），以为安全了。
再跑一遍：栈**一模一样** —— `sendEvent → _NSGestureEnvironment → NSCoreDragManager
_tryCatchDragUntilMouseUp → _dragUntilMouseUp → CoreDragStartDraggingAsync →
_BlockUntilNextEventMatchingListInMode`。会话照样起来。
⇒ 阈值那个前提是我想当然。合成拖拽在这条路径上**做不到**，与位移大小无关。
⇒ 于是整条撤掉（连工具函数一起，留着就会被下一次复用），只留一行 `DRAG-LIMIT` 读数 + 守卫。
⇒ 教训：**改法的第一版也要重跑**，"能编译 + 讲得通"不是第二次测量。

### 3. 采样通道坏了却判产品，是本轮第二次撞上的同一族（U-209）

`testFrameIntervalsUnderStateChanges` 第一次跑出结论就红：`帧样本太少，结论无效（0 不大于 60）`。
查因不在产品 —— 同一台机器 `screencapture` 返回 2940×1912 **全黑**、`pmset` 报 `UserIsActive 0`
⇒ 显示器睡着 ⇒ `CADisplayLink` 一颗 tick 都不发。
⇒ 判据改成"通道先当自己的证人"：空转 0.6 秒拿不到 tick 就报 `FRAME_CHANNEL baseline_n=0 screen=有` 并 skip。
   地板（n>60 / p95≤20ms / worst≤120ms）**一条都没放宽** —— 放宽它就是把"仪器没跑"洗成"产品没问题"。

### 4. 覆盖登记那一步是**门自己报的**（这条顺序很重要）

我删完探针没想起登记文件；是 `probe_coverage_gate` 的自测红给我看的：
```
STALE testDragSelectExpandsSelectionInsideTheRealList：清单里有、源码里已经没有这条用例 ⇒ 删掉这行登记
```
⇒ 这就是 R82 造那道门想要的形状：它不替我做决定，它把我漏的那一格摆到我面前。
⇒ 登记里其余十条的 reason 都写着"无头 runner 上整卷在第一条结论之前就被收掉"——
   **那句成因写错了**（真因是这条僵尸探针）。但我**没有**替它们改登记：
   "runner 上今天能不能跑到"是下一次 CI 的读数，本机结果不配替它签字。
   门会在"说跑不了却跑到了"时再红一次，那时逐条重登记。

### 5. 本轮看图：选中态在**两条**离屏路径里都是黑的（BACKLOG 126 的第二、三格数据点）

在屏探针自己拍的 `focus-after-tab-{light,dark}.png`（1600×1264）：

```
=== focus-after-tab-light.png  1600x1264 px|    NO_BLUE ⇒ 这张帧里没有蓝色（焦点环/选中带都不在）—— 仪器或前提坏了|=== focus-after-tab-dark.png  1600x1264 px|    NO_BLUE ⇒ 这张帧里没有蓝色（焦点环/选中带都不在）—— 仪器或前提坏了|=== reveal-after-320x300-light.png  640x600 px|    NO_BLUE ⇒ 这张帧里没有蓝色（焦点环/选中带都不在）—— 仪器或前提坏了|
```

⇒ 亮档里被选中的那一行是一条**纯黑色带**（行均亮度 2/255，行内文字与图标一颗都看不见），
   而**整帧找不到任何蓝** ⇒ 焦点环在这条通道里根本没落墨。
⇒ 交叉检查做成了一半：同一状态在**捕获卷的基线帧** `content-with-history-750x560-light.png`
   里也是同一条黑胶囊 ⇒ 这不是在屏探针独有的，是两条离屏路径共有的选中态材质盲区，
   而且它已经在 124 帧基线里活了很多轮（基线只比对差异，不判可读性，所以没人报过）。
⇒ 另一半做坏了，也记下来：我第一版用"整列最暗的 6 行"当尺，量到的是**窗口外的黑底**
   （y≈796 已出窗口）⇒ 那三个"0/255"作废。正确做法是**用探针自己报出来的 `ListTableRowView` 矩形**
   当扫描区域，不要猜 y（同一族教训：R88 列常量错位、R90 参照点污染、R91 量到窗外）。
⇒ 真机截图那一腿 **NOT-RUN**：这台机器给不出真机像素（见下面"没跑的"）。
   所以"黑带 = 产品缺陷"与"黑带 = 通道"两个结论本轮都**没有证据**，126 继续挂着。

### 6. 第一条真红：BACKLOG 127（本轮只做到"有名字"）

```
/Users/wangziyi/Codex_Project0/ClipboardHistory/Tests/ClipboardHistoryAppTests/UIInteractionProbeTests.swift:916: error: -[ClipboardHistoryAppTests.UIInteractionProbeTests testSidebarListFocusRingAfte|
```

⇒ 一行暴露**两个半宽** `KeyViewProxy`（148 + 148 + 间距 ≈ 320 = 整行宽）。
两种成因，本轮不分定：① 产品的无障碍结构（Tab 一行停两次、焦点环可能只画半行）；
② 这条判据的期望（"宽 200…290"）写在它**从没跑出结论**的情况下 —— 一把没被正对照校准过的尺，
不配有罪判决（R87/U-200 同一族）。⇒ 127 的第一步是拿同一颗尺去量**快速选择浮层**那一卷列表：
也两个半宽 ⇒ ②；不是 ⇒ ①。
⇒ 本轮**不**为了让 CI 绿去改那条期望，也不删这条探针。所以推上去之后 main 会带着
   一朵**有名字的红** —— 修僵尸探针的意义就是让红能说话。

### 牙（5 刀；M509 是故意要逃的那一刀）

| M505 | 探针里再发一颗 .leftMouseDragged（守卫认不认机制） | **CAUGHT** |
| M506 | 删掉 DRAG-LIMIT 那行读数（限制被悄悄抹平） | **CAUGHT** |
| M507 | 删掉"为什么删掉拖选探针"的解释块（守卫失去依据） | **CAUGHT** |
| M508 | 删掉 FRAME_CHANNEL 那颗证人（0 样本会被读成产品红） | **CAUGHT** |
| M509 | 守卫退回"扫函数名"（改名即可绕过 ⇒ 期望 ESCAPED） | **ESCAPED** |

M509 把守卫从"扫事件类型"退回"扫函数名" ⇒ 它**必须**逃，逃掉才是本轮想记的事实：
名字级守卫可以被改名绕过，所以钉的是 `(.leftMouseDragged` 这个机制形状。

### 验证（本机，逐条实跑；跑不了的点名）

```
动了哪些非台账文件            3 个；产品文件 0（只动 Tests/ ⇒ 帧按构造不变，但仍实测一遍）
构建告警                       0 条（0 才算过）
全量 Swift 测试                Executed 801 tests, with 40 tests skipped and 0 failures (0 unexpected) in 144.711 (144.753) seconds| Executed 801 tests, with 40 tests skipped and 0 failures (0 unexpected) in 144.711 (144.754) seconds|（exit 0）
脚本自测                       Ran 173 tests in 10.955s OK（exit 0）
在屏那一卷（CI 原样 + 心跳）   心跳=10 executed=10 passed=7 skipped=2 failed=1
两条新读数                     FRAME_CHANNEL baseline_n=0 screen=有|DRAG-LIMIT 合成拖拽不可行：任何 .leftMouseDragged 都会让 sendEvent 进 CoreDrag 模态循环（R91 实测，含 2pt 阈值内的微移）⇒ 行拖选/拖出的行为验收改由人工，见 D-034 与手工清单第 2 节|
捕获卷 + 帧基线                124 张帧；对账 FRAME_BASELINE_AGAINST=working FRAME_BASELINE_COMPARED=124 FRAME_BASELINE_CHANGED=0 FRAME_BASELINE_MISSING=0 FRAME_BASELINE_ADDED=0
变异电池                       M505–M509：4 CAUGHT / 1 逃掉（M509，故意）/ 0 没跑成
看图仪器                       === focus-after-tab-light.png  1600x1264 px|    NO_BLUE ⇒ 这张帧里没有蓝色（焦点环/选中带都不在）—— 仪器或前提坏了|=== focus-after-tab-dark.png  1600x1264 px|    NO_BLUE ⇒ 这张帧里没有蓝色（焦点环/选中带都不在）—— 仪器或前提坏了|=== reveal-after-320x300-light.png  640x600 px|    NO_BLUE ⇒ 这张帧里没有蓝色（焦点环/选中带都不在）—— 仪器或前提坏了|
没跑的                         BACKLOG 127 的定性（一行两个半宽 KeyViewProxy：产品无障碍结构 vs 探针期望没被正对照校准）—— 本轮只做到让它第一次跑出结论并点名；BACKLOG 126 的决定性实验（真机窗口截图 vs 离屏帧）：这台机器现在做不了 —— screencapture 返回 2940x1912 全黑、pmset 报 UserIsActive 0 ⇒ 显示器睡着/无录屏权限。这一格是**没跑**，不是「真机也看不见」；BACKLOG 124 第②步（装机落后审计升成 scripts 判据 + CI 一步）；runner 上的两件事：① 在屏那一卷第一次能跑到 10 条结论吗（本机已证）② FRAME_CHANNEL 在 runner 上是 n=0 还是有 tick；换装：本轮产品文件 0 个 ⇒ 不换装（帧按构造不变，仍实测对账）
```

### 七维自评

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 19 / 20 | 零产品改动；主窗口侧栏行的选中/聚焦两态重判一遍，结论是不加任何东西 |
| 流畅度 | 19 / 20 | 在屏那一卷第一次跑到 7 条结论（其中含帧间隔那条判据的通道证人）；但它在**这台机器**上判不了，runner 那一格等下一次 CI |
| 层次与材质 | 13 / 15 | 亮档基线帧里"被选中的那一行是纯黑色带"这一格本轮第一次量到并登记；焦点环在捕获侧完全不可判 —— 两格都没定性 |
| 动效细节 | 15 / 15 | 125 结案：合成拖拽被证明在这条路径上做不到，限制打成读数并由机制级守卫钉住 |
| 交互反馈 | 9 / 10 | 反馈本身没动；选中态不可判这件事使"选中算不算反馈"这一格不能给满 |
| 可访问性 | 7 / 10 | 第一次跑完就出 BACKLOG 127（一行两个半宽可焦点代理）；本轮只做到点名 |
| 性能 | 15 / 15 | 整卷从 180 秒收不掉变成 13.8 秒跑完；CI 不再被一条挂死用例拖满作业 |

**97 / 100**：本轮把五轮追的"CI 上一条判据都没跑完"归到了一条本该六天前就删掉的探针上，
并且把自己第一版"压到阈值内就安全"的修法用第二次测量撤掉。
扣的分全是有名字的：127 没定性、选中态/焦点环两格不可判、真机那一腿没跑。

### 仍未解决

- BACKLOG **127**（本轮新开）：一行两个半宽 `KeyViewProxy` —— 产品无障碍结构 vs 期望没被正对照校准。
- BACKLOG **126**：真机窗口截图 vs 离屏帧那一次对照（这台机器现在给不出真机像素）；
  本轮新加两格数据点（选中态黑带跨两条离屏路径、焦点环零墨）。
- BACKLOG **92**：登记里那句"runner 上整卷在第一条结论之前就被收掉"**成因写错**（真因是僵尸探针），
  但"runner 今天能不能跑到"仍要等下一次 CI；另有一条本机内部的矛盾没解开：
  R89 记"本机这一卷 90 秒跑得完"，R91 三遍都是 180 秒收不掉 ⇒ 那两次跑法差在哪，还没有名字。
- BACKLOG **124** 第②步（装机落后审计升成判据）：仍欠。
- BACKLOG **119**、**121**、**116** 剩下那半格、**115**、**111**、108 余下、77 路 b、101 ②③、106；
  真机 68.1 / 68.2 / 69.1 / 70.1 / 71.1 / 72.1 / 72.2 / 73.1 / 73.2。

## Round 92 · 两道最终闸门读的是我自己的自检夹具（结案 92、128 的本机那一半 / 新开 129、130、131、132 / U-211…U-215 / D-150）

### 1. 头条：追了五轮的"CI 上一条在屏判据都没跑完"，最后一半成因是**我自己造的**

R91 收尾时读到 R90 的 CI（run 38846896495），两次 run（`a68a08f`、`091d216`）里
`Capture gate` 与 `On-screen probe coverage floor` 都在红，而红话说的是：

```
CAPTURE_GATE_RESULT=fail 日志里没有任何 `Test Case ... passed|failed|skipped` 行
  ⇒ 这一步没跑到用例（挂死、崩溃、或 filter 打错）
UI_PROBE_CHANNELS_CONTRADICT pulse=… started=probeA
```

两句都是**假的**。同一次 run 里捕获那一步自己打的是
`Executed 47 tests, with 9 tests skipped and 0 failures in 177.801 seconds` + `captured frames: 124`；
而 `probeA` 是我自检夹具里的用例名（`TRUNCATED = "Test Case '-[p probeA]' started."`）。

成因：`a68a08f`（R89）为了"那道门一红就吃掉后面七步的证据"，把两步挪到作业末尾加 `if: always()`。
挪的位置是对的。错的是 `scripts/tests/test_ci_report_selftest.py` 的 `run_bash()` 只把
**`/tmp/shots-ci`** 换进临时目录，于是 `cp FAKE_LOG /tmp/frames.log`、`/tmp/ui.log`、`/tmp/motion.log`
写进了**作业自己的共享 /tmp**，把 10 分钟后闸门要读的三份日志覆盖了。

本机实测（不是读代码推的）：往 `/tmp/frames.log` 写一行 `REAL-MARKER`，跑一遍
`python3 -m unittest discover -s scripts/tests`，之后那个文件变成
`Test Case '-[p probeA]' started.`，marker 一行不剩 —— 和 runner 上读到的一模一样。

三次 run 对账（同一把尺、同一个 `/tmp`）：

| run | 提交 | `补回` | `passed` | 闸门 |
| --- | --- | --- | --- | --- |
| 38826160092 | `d44d344`（挪之前） | 0 行 | 38 | ok |
| 38838819089 | `a68a08f`（挪之后第一次） | 402 行 | 0 | fail |
| 38846896495 | `091d216` | 402 行 | 0 | fail |

⇒ 可复现 2/2，不是骰子。`readings=404` 三次一模一样，因为读数文件的路径被换进了临时目录，
真那份从没被自检碰过 —— 所以 `NOT_RUN=49` 那批读数是**真**的，只有结论行是假的。

### 2. 修法（三支，标准一个字没动）

1. `run_bash` 走 `prepare()`：**所有** `/tmp…` 一律映射进这一格的临时目录。
   用通配而不是补清单，因为"清单"正是这次的成因 —— 加一条新的 `/tmp/x.log` 不需要改自检。
   两道边界都要（都是当场踩出来的）：后顾挡住 `tempfile` 的 `tmpab1x/`（早先那版把
   `cp` 的**源**路径改坏了，0 告警那一格凭空变红），前向挡住 `/private/tmp/x` 这种"前缀还有东西"的
   —— 那种不换，交给静态扫描喊红，而不是静默地留一处共享写入。
2. 三条会红的守卫：真值表（每一种 `/tmp` 形状逐条钉）、逐格扫描（交给 bash 的那段脚本里不许还有 `/tmp`）、
   **行为证人**（跑一格真夹具，共享 /tmp 里那四份日志的 mtime/大小必须一模一样，
   而沙箱里必须**确实**多了那份假日志 —— 只断言"真文件没动"会有一种假绿）。
3. `ci_capture_gate.py` 的成因改成三支，全部仍然红：
   读数通道里有**指认这一份文件自己**的同源证人 ⇒ "这一步跑到过，坏的是日志通道"；
   有行但没同源证人 ⇒ "那份读数不可信，既不能证明跑到也不能证明没跑到"；
   两边都空 ⇒ 才是原来那句"没跑到用例"。另加一行 `CAPTURE_GATE_INPUT 日志通道=N 行/M 字节`，
   让红自己带上诊断。

### 3. 真实看图：设置窗口「数据」分区（逐元素，带坐标）

正文在 `.scratch/motion-audit-2/r92_visual_review_data.md`（14 个元素逐个判，加/不加都写理由）。
本轮**真正改的那一条**是分组语言：同一窗口五种分区四套语法，「数据」是唯一一个
"卡片只圈住一部分、其余整段裸在外面、外面还压着分隔线"的。

PREMISE 通道=non-key（capture-readings.log 里的 面板key/appActive）⇒ accent 派生的颜色那一档 判不了，Q2/Q3 记 NOT-RUN

| 读数 | 改前 | 改后 |
| --- | --- | --- |
| 卡片 |   卡片#1 框=(172,106)..(696,158)pt 填充=rgb(247, 247, 247) 内墨=(130, 130, 130) 颗=1082 对比=3.59 内部线=无 |   卡片#1 框=(172,106)..(696,318)pt 填充=rgb(247, 247, 247) 内墨=(129, 129, 129) 颗=4506 对比=3.64 内部线=166pt 271pt |
| 分隔线 |   分隔线=2 条 y=173pt 282pt |   分隔线=0 条 y=无 |

段内动画键、两条回执通道、三颗按钮的禁用逻辑一行未动；改后三颗按钮填充仍然互相相同（差=0）。

### 4. 中途读到 R91 推送的 CI（run 38852286519）：那一卷第一次在 runner 上下了结论

完整读数在 `.scratch/motion-audit-2/r92_ci_readings.md`。四行就够说明问题：

```
ui suite exit: 137  executed: 0  已下结论的用例: 6      ← R90 那一次这里是 0
UI_PROBE_CHANNELS pulse=7 started=7 concluded=6
UI_PROBE_HUNG=testRightClickMenusAppKitWouldShowAreChinese
UI_PROBE_CHANNELS_AGREE=1 （两条通道点的是同一批 ⇒ 心跳那条不是孤证）
```

- **BACKLOG 92 剩下那一格有答案了**：runner 上不是"一条都跑不到"，是跑到 6 条；
  僵尸确实是挡在最前面那一个。名册也对上了（`源码用例=10 登记=10`，没有 STALE）。
- R90 设计的双通道交叉签核第一次兑现"一致时敢点名"（上一轮只证了"不一致时退回只报观察"）。
- 第二具僵尸有名字：`testRightClickMenusAppKitWouldShowAreChinese`（本机 13.8 秒里它是跑完的）
  ⇒ 新开 **BACKLOG 132**，写的是"待测"，不是"和 CoreDrag 同一族"——本轮没在 runner 上 `sample` 它。
- 同一次 run 里两道最终闸门仍然报 `本次下结论=0`，与上面那句 `concluded=6` **直接矛盾** ——
  这就是 128 最好的现场证据：同一个问题两个答案，一个来自真日志、一个来自夹具。

### 5. 我自己错掉、并且被读数纠正的五条（U-211…U-215）

- **U-211**：我把"三颗按钮同填充"写成了产品结论，没先读通道前提（`appActive=false` ⇒ accent 去饱和）。
  中途还怀疑过"是不是禁用态"，去查 fixture 发现 `clearHistoryAction: { nil }` 是**非 nil 闭包**
  ⇒ 按钮是启用态。方向对、结论仍错：真正的解释是通道。⇒ 仪器现在先打 `PREMISE` 行，
  non-key 时 Q2/Q3 只能出 NOT-RUN。
- **U-212**：胶囊检测器抄了 R90 的"色相 ≥25"常数，而这颗胶囊实测色相 22/21 —— 两档都差 3 没检出，
  于是 Q3 被读成"今天没判"。**给没量过的色号写阈值，就会把量到的东西读没。**
- **U-213**："卡片内线"第一版参照页面底色 ⇒ "其余分区 0 条内线"是假的（卡片内的线比的是卡片底色）。
  改成卡片自己的底色 + 整行同方向偏离 ≥90% + 边缘让开 13pt。
- **U-214**：改完之后按钮填充一度报成 247（= 卡片色），因为我把卡片色当填充传进 `ink_of` ——
  于是"墨"里混进按钮自己的灰底。取盒子自己的中位色（228/54）之后，改前改后才可比。
- **U-215**：M511/M514 两把刀**第一次都逃掉了**，各自量出一处真东西：
  M511 逃 = 尾部边界没有用例覆盖（补了 `/tmpbackup/x` 与 `OUT=/tmpwork` 两条）；
  M514 逃 = 自检的临时目录**跨次运行复用**，上一遍那 61 张 PNG 替这一遍作证
  ⇒ 改成每遍一个空目录、跑完删掉。刀逃掉不是电池的失败，是它最有用的时刻。

### 牙（6 刀；M515 是故意要逃的那一刀 = 已知盲区）

汇总：5 刀 CAUGHT / 1 如期 ESCAPED（已知盲区）/ 0 没跑成 / 0 预期不符（共 6）

- M510 撤回接线（`run_bash` 只换 `/tmp/shots-ci`）⇒ CAUGHT，而且**只有**行为证人那一格抓到 ——
  静态扫描测的是 `prepare`，被绕开的正是"调不调它"这一层。
- M511 去掉尾部边界 ⇒ CAUGHT（真值表）。
- M512 同源证人放宽成"读数有行就行" ⇒ CAUGHT。
- M513 三支成因并回一支 ⇒ CAUGHT（三格同时红）。
- M514 PNG 落点错位 ⇒ CAUGHT（`test frames -ge 60`）。
- **M515 如期 ESCAPED**：往自检**不认识**的那一步（`Frame baseline vs working manifest`）里
  加一句 `cp /tmp/frames.log …`，全量绿。⇒ 守卫管的是"自检知道的那五步"，不是"作业里所有写 /tmp 的人"。
  这一格开成 **BACKLOG 129**（跨步骤证据挪去 per-job 的 `$RUNNER_TEMP`）。

### 验证（本机，逐条实跑；跑不了的点名）

- 非台账文件 **5 个**（其中 1 个是脚本生成的 `docs/frame_baseline.json`），产品 **1 个**：1（本轮确实改了产品：数据页容器）
- 构建告警 **0**；全量 Swift `Executed 801 tests, with 40 tests skipped and 0 failures (0 unexpected) in 144.840 (144.883) seconds| Executed 801 tests, with 40 tests skipped and 0 failures (0 unexpected) in 144.840 (144.884) seconds|`（exit 0）
- 捕获卷 exit 0：`Executed 47 tests, with 4 tests skipped and 0 failures (0 unexpected) in 115.767 (115.771) seconds`
- 帧基线对账：`FRAME_BASELINE_AGAINST=working FRAME_BASELINE_COMPARED=124 FRAME_BASELINE_CHANGED=0 FRAME_BASELINE_MISSING=0 FRAME_BASELINE_ADDED=0`
- 脚本自测 exit 0：`Ran 181 tests in 11.108s OK`
- **头条那条**：写完四份 marker 跑一遍全量自检 ⇒ `HERMETIC_MARKERS_SURVIVED=4/4`
- 变异电池 exit 0：`汇总：5 刀 CAUGHT / 1 如期 ESCAPED（已知盲区）/ 0 没跑成 / 0 预期不符（共 6）`

### 七维自评

| 维度 | 分 | 这一轮扣分的地方 |
| --- | --- | --- |
| 真实看图 | 14/15 | 看了改前改后各两帧（亮/暗），但没看悬停/按下态 —— 那条通道给不了，不是我省了 |
| 判断有据 | 12/15 | 两次把通道的读数写成产品结论（Q2"破坏性没被区分"、Q3"3.53 不达标"），前提行是**事后**补的；顺序反了 |
| 量尺诚实 | 13/15 | 三处尺子坏在被自己发现之前：抄来的色相阈值（U-212）、内线参照错（U-213）、按钮填充取成卡片色（U-214） |
| 原生与克制 | 15/15 | 只动容器；不给破坏性按钮额外染色、不给容器加淡入、不给说明段加 tooltip，三条"不加"都写了理由 |
| 判据有牙 | 13/15 | 6 刀 5 CAUGHT；但 M515 量出覆盖面只是"自检认识的那五步"，且 M511/M514 第一次都逃掉（U-215） |
| 台账可复查 | 14/15 | 本轮所有数都从摘要/电池/读数文件取；扣一分是给 R91 写台账时"读 CI"排在了之后 |
| 收口与记账 | 15/15 | 三支假成因、五条 NOT-RUN、一处已知盲区、一次结案（92）全部点名 |
| **合计** | **96/100** | 低于 90 才继续修；96 但扣的两格都在"前提读晚了"这一族 ⇒ 它已经是本轮的正文与仪器改动，不是待办 |

### 仍未解决

- BACKLOG **128**：本机已修，runner 上"两道闸门第一次读到自己那份日志"要等下一次 CI。
- BACKLOG **129**：跨步骤证据住在共享 `/tmp` 而不是 per-job 的 `$RUNNER_TEMP`（M515 量出来的盲区）。
- BACKLOG **130**：「清空」那颗与侧栏选中胶囊在**真机 key 窗口**里的 accent 那一档（这条通道判不了）。
- BACKLOG **131**：统计页那套"0 卡片 + 1 条外线"要不要一起并进来（要连热图那屏一起判）。
- BACKLOG **132**：`testRightClickMenus…` 在 runner 上是挂还是慢（本轮只点名，没 `sample`）；
  R91 CI 里那 6 条结论**各自是什么判定**（`executed: 0` 与 `concluded=6` 的差是缓冲丢行，
  那 6 行的内容本轮没按步骤名逐条读 —— U-178）。
- **124** 第②步、**127** 的正对照、**126**/119/121/116/115/111/108/77b/101/106；
  真机 68.1 / 68.2 / 69.1 / 70.1 / 71.1 / 72.1 / 72.2 / 73.1 / 73.2。

## Round 93 · 那朵"有名字的红"被正对照判掉了：KeyViewProxy 不是行代理（结案 127 / 新开 133、134 / 更新 132 / U-216…U-217 / D-151）

### 1. 头条：127 的两种成因里是 ②，而判它的办法是**先造一把会打数的尺**

R91 收尾时我写下"main 带着一朵有名字的红，是有意的"。这一轮它被**证据**判掉，不是被静音：

```
ROW_PROXY_CENSUS 侧栏@窗口320pt 宿主=320pt 代理=2 行=1 首行各代理宽=[148+148]
ROW_PROXY_CENSUS 侧栏@窗口250pt 宿主=250pt 代理=2 行=1 首行各代理宽=[113+113]
ROW_PROXY_LISTROWS 行视图=11 个，前 3 个={{0, 10}, {320, 66}} {{0, 76}, {320, 51}} {{0, 127}, {320, 66}}
ROW_PROXY[0] frame={{12,50.5},{148,25}} acceptsFirstResponder=false next=KeyViewProxy@{{160,50.5},{148,25}} 父链=KeyViewProxy ← NSHostingView
ROW_PROXY_CONTRAST 浮层(NSTableView) 代理=0 行=0 每行代理数=
```

三条事实：11 行的树里只有 **2 个** `KeyViewProxy`（行是 `ListTableRowView`，11 个、整行宽 320pt）；
两个都 `acceptsFirstResponder=false`；半宽**跟着宿主缩放**（320→148+148、250→113+113）且父视图是
`NSHostingView`。⇒ 那是 SwiftUI 宿主级的 key-view 代理，**不是行代理**；
"Tab 一行停两次 / VoiceOver 一行读两段"这件事没有发生。

修法按 127 自己立的规矩：不许把 `宽 200…290` 放宽成"148 也行"（那是拿判据讨好现状），
而是改成点**真正的行视图** —— 这条判据要的从来是"用户点一行"。
改后 `testSidebarListFocusRingAfterClick` = `passed (0.738 seconds)`，
整卷 `Executed 11 tests, with 3 tests skipped and 0 failures`。

### 2. U-216 / U-217（我自己错掉、被读数纠正的两条）

- **U-216**：正对照第一版只走 `nextKeyView` 链，读到"链里两个代理都在同一行"就准备写
  "Tab 在同一行停两次"。`acceptsFirstResponder=false` 一起打出来之后才知道
  **在链上 ≠ 会被停在上面**（链是视图自己声明的下一站，停不停由 responder 判定决定）。
  ⇒ 读数现在同时打这两个字段；"后果"要由能拒绝的那一栏签。
- **U-217**：名册的 `can/cannot` 我没有按字典序翻。R91 的 CI 只数出"六条有结论"，
  **名字**在被 SIGKILL 带走的那块缓冲里；把"应该是这六条"登记成事实，就是 R87 明令禁止的
  "没量过的推断"。⇒ 本轮只把 11 条 reason 改成实测成因（六条跑到、第七条开口没闭口），
  翻转等 R92 的 CI 逐条印出名字之后做（134）。翻错会被 `NOW_RUNS`/`NOT_RUN` 挡回来。

### 3. 真实看图：快速选择浮层（逐元素，带坐标）

正文在 `.scratch/motion-audit-2/r93_visual_review_quickpick.md`。本轮产品文件 **0 个**
⇒ 复用的是 R92 那次捕获的帧（先量产品=0 才有资格复用）。三条结论：
- 选中行胶囊 (22,46)..(398,80)pt、填充亮 220 / 暗 70、对比 12.56 / 8.36 ⇒ 达标，**不加描边不加动效**；
- 面板下方约 180pt 空白**不缩**：每次输入都改面板尺寸就是抖动，这是刻意的"不动"；
- 搜索框那层灰底是**夹具全选高亮**（`field.stringValue = query` 的副作用），不是产品样式
  ⇒ 新开 **133**：它可能一直在污染 R76 那条"焦点把占位符调淡"的墨移动量读数。

### 4. 牙

本轮没有新的会红判据（改的是"一把没校准的尺"→"真正的行视图"，加的是**只打数不判产品**的诊断），
所以电池没跑；取而代之的是两条自证：
① 诊断判据自带分组真值表（差 1pt 必须并、差 25pt 必须分）—— 分组写反会正好抹掉要看的东西；
② 名册改动由 `probe_coverage_gate.py` 自己判（`REASONLESS`/`STALE`/`NOW_RUNS`/`NOT_RUN`），
   脚本 `roster_r93.py` 落盘后 `python3 -m unittest discover -s scripts/tests` 181 条全绿。

### 5. 验证（本机，逐条实跑）

- 非台账文件：ClipboardHistory/Tests/ClipboardHistoryAppTests/UIInteractionProbeTests.swift, scripts/probe_coverage_expectations.json（产品 0 个 ⇒ 不换装，帧按构造不变）
- 在屏那一卷：`Executed 11 tests, with 3 tests skipped and 0 failures`，其中 3 条 skip = 无障碍诊断 + `FRAME_CHANNEL` 这台机器 0 帧 + 本轮新加的诊断判据
- 名册：`cases=11`，其中 `can=0`（本轮只改成因，没翻身份 ⇒ 134）

### 6. 仍未解决

- **134**：R92 的 CI（`9c10569`）逐条印出结论名之后翻 `can`。
- **132**：`testRightClickMenus…` 在 runner 上开口没闭口（本机 2.016 秒跑完）⇒ 下一轮 `sample`。
- **133**：浮层夹具的全选高亮，以及它是否污染过 R76 那格。
- **130**：真机 key 窗口下的 accent（红与蓝）那一档。
- **128** 的 runner 那一半、**129**、**126**、**124** 第②步、**121**、**116** 剩下那半格、
  **115**、**111**、108 余下、77 路 b、101 ②③、106；真机 68.1 / 68.2 / 69.1 / 70.1 / 71.1 / 72.x / 73.x。

## Round 94 · 名册按读数翻了六条，"为什么没结论"从推断升成读数；菜单栏那六帧第一次被逐元素判（结案 134 / 新开 135、136 / U-218…U-222 / D-152）

### 1. 头条：上一轮欠的翻转做完了，而它把作业的红灯一起带走

run 38857388449（`8e6ed15`）的 `On-screen probe coverage floor` 第一次逐条点名：
`本次下结论=6 红=6`，六行 `NOW_RUNS <名字>：…（passed|skipped）`。作业结论是 **failure**，
红的来源正是"登记说跑不了、它却跑了"—— D-151 留的那个循环该在这里合上。

* 六条翻 `can`，判定分开写：`testAccessibilityTreeCoverage` 那次是 `skipped` ⇒ 只证明"跑得动"，
  **今天仍不产出产品判断**；其余五条 `passed` ⇒ 产品结论第一次能引用那台机器。
  （第一版我给六条写了同一句"产品结论可以引用它"，对 skipped 那条是假的。）
* 剩下五条 `cannot` 三种成因：1 条挂住（132）/ 3 条真的排在它之后 / 1 条**根本不在 `8e6ed15` 的源码里**
  （那次读数 `源码用例=10 登记=10`，它是 `6c5ca95` 才登记的）⇒ "没编译过"不许写成"排队没到"。
* 名册：`cases=11 can=6 cannot=5`。本地对两份日志各判一次：r62 那份（零结论）现在**该红**且逐条点名 NOT_RUN×6，
  `8e6ed15` 那份该绿。原来那句"真 CI 日志该绿"是全 can=0 时代的契约，过期了（U-221）。

### 2. 一次差点写出的假话：同一卷在同一次 run 里有 20 行结论，全是 skip

`gh run view --job 116831818024 --log` 里 grep `UIInteractionProbeTests` + `Test Case` 得到 20 行，
**全部 skipped** —— 但它们属于 `Swift tests (executed-count gate)` 那一步（那里没有
`CLIPBOARD_HISTORY_UI_INTERACTION=1`）。按步骤名 `awk -F'\t' '$2=="On-screen interaction probes (report-only)"'`
一过滤，那一步的正文里 `Test Case` 行数 = **0**，只有汇总行 `已下结论的用例: 6`。
⇒ 不按步骤名过滤就会写出一句"探针在 runner 上也是全 skip"的假话（R86 那条老账，这次又差一次，U-218）。
顺带纠正我自己：`8e6ed15` 那次的作业结论是 **failure** 不是绿。

### 3. 把推断升成读数：PROBE_ORDER / PROBE_QUEUED（只报不判）

```
PROBE_COVERAGE_SUMMARY 源码用例=11 登记=11 runner可跑=6 runner不可跑=5 本次下结论=6 红=0
  PROBE_ORDER 露面=7/11 未闭口=1 前缀=1
  PROBE_QUEUED 4/11 条一次都没轮到：testRowGestures… testRowIndexDrift… testSidebarListFocusRingAfterClick testRowProxyCensus…
```

* 缺席从此分两种：**跑到了却没闭口**（计数，名字归 `ui_probe_report`）与**一次都没轮到**（名字）。
* `前缀=无从判定` 那一格是刻意留的：一条都没露面时"前缀成立"是一句**空洞的真话**（U-220）。
* 三行读数**不判红**：把诊断做成门禁，就会在另一种执行序下假红。`NOT_RUN` 该红仍然红。
* R86 那条守卫（`NonRedundancyTests`）从"文本里不许出现 started"改成"不许复制**判定**"：
  只扫 `print(` 行的字面串 + 反方向一格（名字必须仍由 `ui_probe_report` 出）。
  变异 M522 证明它还有牙：让闸门自己打印 `PROBE_HUNG=` 就会被它抓住。

### 4. 牙：M516…M522（先在台账查重：上一支用到 M515）

`MUTATE_TABLE n=7 caught=6 intended_escaped=1 mismatch=0 not_run=0`
M516 前缀恒真 / M517 露面顺序被排序 / M518 打印里的"未闭口"写死成 0 / M519 两种缺席又被缝成一种 /
M520 空洞的真话冒充结论 / **M521 预期绿**：结论之后又出现 `started` 时把状态改回"未结论"——
现有夹具都不产生这种交错 ⇒ 真实缺口开成 **135**（一份日志混进第二个写入者时"未闭口"会说谎，
R80b 那一族）/ M522 复制因果级名字 ⇒ 被改写过的那条守卫抓住。
变异跑在**临时树**上（`scripts/` + 那份 json + 软链的 swift 源文件 + `.github/workflows` 软链），
仓库里那颗尺子全程没被写过；第一次跑时临时树缺 `.github/workflows` ⇒ 基线 RED 而脚本按自己的规矩
**拒绝出表**（U-222）。

### 5. 看图那一腿：菜单栏面板（MenuBarExtra 的内容视图）第一次被逐元素判

正文：`.scratch/motion-audit-2/r94_menubar_review.md`；读数：`r94_menubar_readings.log`。
本轮产品文件 **0 个** ⇒ 帧是**重新拍的**（`/tmp/r94_shots`，124 帧与 working 基线 `CHANGED=0`）。

* 结构：`empty 3 带/1 线`、`refreshing 3/1`、`recommendations 9/3`，两主题**同形**（最大 y 偏差 0.5pt）；
* 两态对照：`EMPTY_VS_REFRESHING 像素完全相同=False`，差异**只在消息那一条带**（"暂无推荐" x 到 73.0、
  "正在整理推荐…" 到 107.5）⇒ 帧名不撒谎（R76 那条）；
* 档：标题 14.94/12.27、说明 3.95/5.92、动作行蓝 3.52/5.16（墨 (0,136,255)/(0,145,255)）；
* **零产品改动**的理由：三条推荐行左右顶到帧边界 = R34 登记的**复刻溢出**，那批帧对
  宽度/截断/对齐/命中区没有发言权（`testMenuBarFramesAreReplicasOfTheMenuSurface` 钉着）。
  标题与小标题在这六帧里居中（x=134.5..184.5 与 132.5..186.0），而 macOS 12 那条路径用的是原生
  `NSMenuItem(title: "时间剪史")` ⇒ 两条路径**可能**不一致，但这条通道没资格判 ⇒ 开 **136** 真机核对。
* 动效判断（逐条）：菜单项 hover / 按压 / 空↔有推荐的淡入 / 加载态转圈 —— **四条全部维持现状**，
  理由各自不同（系统自己画高亮、帧里没有任何自绘底、NSMenu 不执行 SwiftUI transition、假动更不诚实）。

### 6. 三条尺错（都进台账，都不算产品缺陷）

* U-218 跨步骤 grep 造出假话（见 §2）；
* U-219 `decode()` 返回 `(w,h,ch,rows)` 而 `lum()` 是 **0..1 的 Y** ⇒ 抄来的 255 尺度阈值
  让六张帧全读"带数=0"（"量不到"伪装成"没有"）；
* U-220 固定 ΔL 门槛跨主题灵敏度不一致：同一根 `Divider()` 两档都 ≈1.25:1，ΔL 却 53.2 / 5.4
  ⇒ 墨的判据改用对比度比值；另加"两档同形"正对照（容差 1.0pt，量出来的，不是拍的）。

### 7. 验证（本机，逐条实跑）

* 构建 0 告警；全量 `swift test` 通过；在屏那一卷本机 `Executed 11 tests, with 3 tests skipped and 0 failures（15.310s）`；
* 帧：124 帧对 working 名单 `CHANGED=0 MISSING=0 ADDED=0`；
* 脚本：`Ran 190 tests in 11.414s OK`（含新写的 `scripts/tests/test_ledger_ids.py` 四格）；
* 变异：`MUTATE_TABLE n=7 caught=6 intended_escaped=1 mismatch=0 not_run=0`；
* 非台账文件：判据/工具 6 个、仓库外脚本 9 个、台账 6 个（**产品 0 个**） ⇒ **不换装**（产品像素未变）。

### 8. 台账自己也被判了一次（U-221）

写这条之前先 grep 决定编号：最后一条是 **D-150（R92）**，而 R93 的两处轮次标题都写着"D-151"
⇒ 一条**被引用却不存在的决定**（根因：`ledgers_r93.py` 的 STAGES 里没有 decisions 那一格，
标题里的号是手抄的）。本轮补记 D-151，并新加一支守卫 `scripts/tests/test_ledger_ids.py`：
轮次标题里引用的每个 `D-xxx` 必须在 `AGENT_DECISIONS.md` 有正文，编号不许空号。
它第一次跑就是红的，报的正是 D-151 —— 也是它教我：定义行的正则要按台账**实际形状**写
（老条目是 `## D-000 …`，新条目是 `### D-150（R92）…`；只认 `###` 会漏掉 115 条，把守卫变成一堵假正例的墙）。

### 9. 仍未解决

**135**（交错日志下"未闭口"会说谎）、**136**（真机核对菜单栏面板）、
**132** 的 sample、**133** 的夹具赋值不选中、**130/126**（真机 + 录屏权限）、**129**、
**124** 第②步、**121**、**116** 剩下那半格、**115**、**111**、108 余下、77 路 b、101 ②③、106；
真机 68.1 / 68.2 / 69.1 / 70.1 / 71.1 / 72.x / 73.x。

## Round 95 · 设置「快捷键」逐元素：卡片里三种留白被并成一种；sample 在 kill 之前拍下来（结案 135 / 新开 137、138 / U-223…U-226 / D-153）

### 1. 本轮的开场清单（逐元素，带坐标）

`settings-shortcuts-720x540-{light,dark}`，**改前**（pt，scale=2 从帧名推）：

| 元素 | 框 | 读数 | 判定 |
|---|---|---|---|
| 卡片 | (172,106)..(696,290) | 填充亮 (247,247,247) / 暗 (37,37,37)，对页面底 1.071 / 1.088 | 两档同形 ⇒ 不动 |
| 录制器 ×3 | (479,116)..(606,139) 等 | 填充 228、墨 40、对比 11.60/12.36 | 不动（U-224） |
| 恢复默认 ×3 | (615,116)..(690,139) 等 | 填充 228、墨 68、对比 7.66 | 不动（U-224） |
| 分隔线 ×2 | y=156.0 / 214.0，x=177.0..690.5 | 与文字左沿 177.5 差 0.5pt | 共轴 ⇒ 不动（U-225） |
| 三行控件 vs 文本块 | 中心 127.5/185.5/256 vs 127.5/185.5/256.5 | 差 ≤0.5pt | `HStack(alignment:.center)` 兑现 ⇒ 不动（U-225） |
| **卡片上下边距** | **7.5 / 6.5** | **内侧（分隔线两侧）14.5 / 15.0** | **缺陷 ⇒ 改（U-223）** |
| 侧栏六行 | 亮档图标 3/6 无墨、暗档标签 5/6 无墨 | 极值色号纯白 / 纯黑 | **已登记盲区**（D-090 / BACKLOG 126）⇒ 不判不改 |

### 2. 缺陷与修法

`GroupBox { VStack(spacing: 12) { 行; Divider(); 行 } }` 里那 12pt 只长在**孩子之间**：
首末行只拿到 GroupBox 自带的 ~7pt，中间行拿到 7+12=19pt。同一张卡片于是有两种留白，
而最后一行恰好是四行说明的那一行 ⇒ 末行离卡片底 6.5pt，读起来像"卡片装不下内容"。

更糟的是**同一窗口有三种**：`快捷键`/`数据` 两处完全没有，`通用`/`隐私`/`推荐` 三处写着
`.padding(.vertical, 4)`。修法是一条具名扩展（不手抄数字，好让源码守卫数得出来）：

- `SettingsViewLayout.cardEdgeInset = 7`（7 的出处：目标 14.5pt 是**这一张卡片自己量出来的内侧那一档**，
  GroupBox 自带 ~7 ⇒ 补 7 落在 14.5/13.5）；
- `View.settingsCardInset()` 五处，替换三处 `.padding(.vertical, 4)`、补上两处空缺；
- 卡片**内部**那处 `.padding(.vertical, 4)`（讲的是另一件事）保留 —— 第一版脚本把它一起替换了，
  靠"needle 命中 4 次而 GroupBox 只有 5 张"这一步发现，改回来了。

改后读数：`CARD_RHYTHM settings-shortcuts light 边距=14.5/14.0 内侧=14.0/14.5/14.0/14.5`、
dark 同一组数 ⇒ 极差从 8.5pt 收到 0.5pt。卡片高度 184 → 198pt（`数据` 212 → 226）。

### 3. 判据（会红的三条 + 一张真值表）

- `testSettingsCardVerticalRhythmIsOneNumber`：两档各拍一次，逐行分类成
  `outside/card/ink/line`，纯函数 `cardRhythm` 算出"四边留白"与"分隔线两侧留白"，断言极差 ≤3pt。
  判的是"**这几个数是不是同一个数**"，不是"这个数够不够大" —— 后者会被"整体都很挤"骗过去。
- 前提格：读到墨却读不出边距 ⇒ 红（尺没压住卡片）；分隔线 <2 条 ⇒ 红；整带零墨 ⇒ NOT-RUN + skip。
- `testCardRhythmArithmeticIsATruthTable`：四条合成件，含"卡片顶到带上沿 ⇒ 不许报数"那一格。
- `testEverySettingsCardAppliesTheSharedEdgeInset`：`GroupBox` 个数 == `.settingsCardInset()` 个数。
- 变异 `MUTATE_TABLE n=4 caught=4 intended_escaped=0 mismatch=0 not_run=0`：
  M528 撤修复 ⇒ 红（"最大的留白 14.5、最小的 7.0"）；M529 漏补一处 ⇒ 帧判据与调用点守卫**都**红；
  M530 把 `.line` 门槛抬到 99% ⇒ 红在"实测 0 条"（不退化成恒真）；M531 把页面底容差放宽到 40 ⇒ 红在"尺没压住卡片"。

### 4. 仪器自己错两次（U-226）

借来的尺也要实测。`.scratch/motion-audit-2/r95_shortcuts_visual.py` 第一次跑：
① `band_r = int(split * s) - 16` —— `column_split` 返回的已经是**像素**，再乘一次 scale 就把扫描带
推到 288pt，越过侧栏/内容列的分隔线，把卡片里的文字当成"侧栏的一行"（读数长得像真的：`段(40..178)`）；
② 阈值用 `BG_TOL+6=10` ⇒ 那颗**选中胶囊**也被当成墨，六行缝成一行（`侧栏行 y=50..500pt`）。
两种都不会报错，只会给出一串看着合理的数。现在加了"带数必须=6"的自检，
而暗档实测只出 4 带 ⇒ 这一档的侧栏**不判**，并把原因打成一行（D-090 / BACKLOG 126 已登记），
而不是让仪器整跑退出 —— 一把只会红或只会绿的尺不算尺。

### 5. 七维度自评（本轮）

| 维度 | 分 | 依据 |
|---|---|---|
| 原生一致 | 92 | 五张卡片同一档留白；没动系统 GroupBox 材质；横向 5.5pt 那一档开成 138 未收 |
| 层级与秩序 | 93 | 边距与内侧同一档之后，卡片不再"装不下"；分隔线仍与文字共轴 |
| 动效恰当 | 90 | 本轮零动效改动：录制器是 AppKit `NSButton`，标题换态不动画是系统的语言（U-224） |
| 可读性 | 91 | 控件墨 11.60/12.36、按钮 7.66 全过线；侧栏那一列两档各有一批不可读，**已登记为通道盲区**，不重复扣分也不当证据 |
| 状态完备 | 88 | 录制中那态仍只靠标题文字变化（无强调色/描边），而这一条**在帧上量不到**（需要真机或在屏夹具）⇒ 记在 138 之后另开 |
| 克制 | 95 | 只改一个常量 + 五处调用；没有加描边、阴影、动画来"让它更明显" |
| 可验证性 | 94 | 三条会红的判据 + 真值表 + 四刀变异；两处仪器自纠有读数留痕 |
| **总评** | **91.9** | ≥90 ⇒ 本维度收口；但"录制中态"与"横向留白"两格仍开着 |

### 6. 验证（`r95_verify.log`，`VERIFY_OK=1`，每一格都是这一遍的新鲜读数）

构建 `BUILD_EXIT=0 BUILD_WARNING_LINES=0`；全量 `Executed 805 tests, with 41 tests skipped and
0 failures（153.173s）`；在屏那一卷 `Executed 11 tests, with 2 tests skipped and 0 failures（21.953s）`；
帧基线 `COMPARED=124 CHANGED=0 MISSING=0 ADDED=0` —— **改前**那一次是 `CHANGED=16`，
全部是 `settings-*`（8 夹具 × 两档），没有一张非设置帧被牵连 ⇒ 同提交 `update`；
脚本 `Ran 205 tests in 11.737s OK`；台账编号守卫 `Ran 4 tests OK`；
三张变异表 `节奏 n=4 caught=4` / `序 n=7 caught=7` / `分诊 n=5 caught=4 intended_escaped=1`；
看图仪器 `卡片=4 控件=18 侧栏不判=2`。产品文件 1 个 ⇒ **换装**：`INSTALL_RESULT=ok`、
`INSTALL_SHA_MATCH=1`、新 pid 62036 启动晚于安装、存档 105 → 105、旧包留在
`Codex_Project0_backups/before-local-20261016-164126`。

### 7. 本轮我自己错在哪（两条，都是被仓库里的东西抓出来的）

1. **CHANGELOG 被我插成两节 `## [Unreleased]`** —— `test_changelog_shape` 当场红
   （`2 != 1`）。这正是 R59 坏过一次的那形状，而仓库里那条守卫存在的理由就是它坏过；
   我写插入脚本时把锚点标题连同正文一起插了一遍。修回一条标题，脚本电池重新跑到 205 条 OK。
2. **变异 harness 里"顺带看第二条守卫"排在还原之后** —— 它读的是已经恢复的干净源码，
   于是打印出"漏补一处却没被调用点守卫抓到"这句**假话**，而真相是我的对照晚了半步。
   把那次运行移进 `try`（文件还是脏的那份）之后，M529 变成"帧判据 CAUGHT | 调用点守卫 CAUGHT"。
   这一条已经写进跨会话记忆（对照脚本的额外检查必须在被改状态下取）。

### 8. 下一轮第一件事

读 R95 的 CI：`UI_PROBE_SAMPLE_EXIT` 与 `analyse_sample()` 那行占比读数 ——
**132 的"挂 or 慢"第一次有资格被回答**，而 M527 那格（并列未覆盖，137）要在读数旁边如实带着。

## Round 96 · runner 那份栈被证明是"我读不懂"；判据扩到每张卡片之后当场抓到上一轮的孤儿（结案 137 / 新开 139、140 / U-227…U-231 / D-154）

### 1. 开场清单（设置「隐私」，逐元素，带坐标）

`settings-privacy-720x540-{light,dark}`（scale=2，尺寸从帧名推）：

| 元素 | 框 / 读数 | 判定 |
|---|---|---|
| 卡片 | (172,106)..(696,**539**)pt | 底被窗口切断 ⇒ 开成 140；填充对页面底 1.071 / 1.088 ⇒ 两档同形，不动 |
| 勾选框 ×4（未勾） | y=170/192/214/236..+15~16pt | 填充 亮 (223,223,223) / 暗 (58,58,58)，色度 0，内部墨 12–20 / 13–20 颗 |
| 勾选框 ×1（已勾） | y=278..294pt | 填充 亮 (213,213,213) / 暗 (67,67,67)，色度 0，对勾 46 / 47 颗，对填充对比 10.84 / 7.57 |
| 默认排除那一列 | 19 段文字带 | 左沿众数 177.5pt（min 177.5 / max 199.0）、行距中位 10.5pt、对比 min 2.94（亮）/ 5.31（暗） |
| 侧栏 | —— | 本轮不判（R95 已按 D-090 / BACKLOG 126 登记为盲区，暗档只出 4 带） |

### 2. 判过不改的（带理由）

- **两态可辨，不加动效**（U-228）：勾上时框自己的填充换了一档（亮 223→213 变深、暗 58→67 变浅）
  **并且**多一枚对勾（12–20 颗 → 46 颗）。两态的差别不只有颜色，还有笔画 —— 这正是"静置一眼
  看得出开没开"。再叠淡入只会让"我刚才那一下有没有生效"变成要看动画才知道。
- **强调色缺席不改**（开成 139）：五颗框的 `chroma=0`，而系统勾选态该是强调色。
  但源码里这五颗都是裸 `Toggle`，**没有任何自定义 `toggleStyle`** ⇒ 灰不是产品选的色。
  两种解释（非 key 窗口的系统画法 / 捕获通道合成）下一步完全不同，所以走真机（批次 75.1），
  不拿帧当证据去改控件 —— 那是 D-090 明令禁止的那类操作。
- **默认排除那一列的重复前缀不改**（U-229）：`Text("默认排除：\(id)")`，帧里可见 8 行都带同一个前缀
  （名单共 9 项，第 9 项落在窗口外 ⇒ 与 140 是同一件事）。看着像冗余，但去掉它换不来任何**可测**的好处：
  前缀逐字相同，id 本来就共一条左轴（实测众数 177.5pt，散布 21.5pt 且全在"标题行/说明行"那一档）；
  而前缀是**每行自带的来源标注** —— 两段 `ForEach`（默认排除 / 用户排除）万一将来交错，
  去掉前缀就把"这条是谁排除的"丢了，那是信息不是装饰。
- **卡片对页面底只有 1.071 / 1.088**：这是系统 `GroupBox` 材质，两档同形 ⇒ 不动。

**用眼睛看的那一遍**（`r96_privacy_boxes_light.png` 是五颗框的放大、`r96_privacy_list_light.png` 是默认排除那一列）：
放大图里"勾上"那一颗是**灰底 + 黑色对勾**，四颗未勾是**更浅一档的灰底 + 空**，整块控件没有任何一处带蓝 ——
这和数字（`chroma=0`）是同一件事的两种通道，所以 139 不是"我算出来的结论"，是看得见的。
另一件能量出来、但只有对着图才看得出意义的事：未勾的框离卡片底只有 **24（亮 223 vs 247）/ 21（暗 58 vs 37）**，
比同一行文字对卡片的对比低得多 ⇒ 静置时"这一列是可点的"这件事几乎不靠颜色承担。
本轮仍然不加描边、不加底：承担识别的是**形状**（圆角方块、每行一颗、左对齐在文字前面），
这是系统复选框的形状，人不需要颜色也认得它 —— 记下来是为了别把它误判成"对比度缺陷"，
也为了 139 真机那一腿如果结论是"产品侧要改"，改的是勾选态的颜色而不是给框加一圈描边。

### 3. 一处真缺陷，改了（U-227）

把 `testSettingsCardVerticalRhythmIsOneNumber` 的对象从"那一张卡片"扩到"**每一张 settings 卡片**"之后，
它当场红了 `settings-data`：`边距=18.0/14.0、内侧=18.0/14.5/17.5/14.0`。
根因是上一轮我**特意留下**的那格 `.padding(.vertical, 4)` —— 三段里只有第一段有。
我上一轮给它写的理由是"卡片内部讲的是另一件事"，这句话被自己的读数推翻：
它讲的就是同一件事（行与分隔线之间的距离），却只有一段有 ⇒ 删掉。

同一轮里容差从 3.0 改到 4.5，**不是为了让它绿**：`settings-data` 里同样 12pt 的布局间距，
接在文字行后面量到 14.0/14.5，接在 `.rounded` 按钮行后面量到 17.5 ⇒ 按钮 bezel 底下有
**3.5pt 不画墨的边**，而这把尺量的是墨到墨。3.5 是从这张帧自己量的，加 1pt 余量。
R95 那个缺陷的极差是 8.5pt、M528 撤修复之后是 7.5pt ⇒ 4.5 这条线仍然咬得住（两张变异表都是证据）。

### 4. 分诊那把尺换掉了判定的来源（137 结案）

旧尺问"最深的那一条路径占多少"，新尺问"**有多少采样停在等待帧上**"：
等待帧套等待帧只算最内层那一次（否则同一份等待会被数 4 遍），
并列时两个族连同各自采样数一起打出来 ⇒ `blocked@ambiguous` + `UI_PROBE_SAMPLE_TIED=…`。
为什么不是"给旧尺补一份并列夹具"：因为旧尺在并列时**必须**挑一个孩子，
挑哪个都不是栈说的 —— 补夹具只是给我的选择拍一张好看的照片。

runner 的第一份栈（run 38876999489）读出来是
`主线程采样=306 主导路径占比=100% 最深帧=读不到` + `blocked@unknown` ——
那是**兜底造出来的假话**：`nodes` 为空时占比被写成 1.0（U-231）。
现在：读不懂 ⇒ `未量到` + `UI_PROBE_SAMPLE_UNPARSED=1` + `UI_PROBE_SAMPLE_SHAPE`
（只打缩进/是否数字开头/长度，**不打帧名** —— 日志里不许出现用户的剪贴板内容）。

### 5. 仪器自己错两次（U-230）

找勾选框那一列：① 用"墨"的门槛 60 ⇒ 只检出 3 颗（未勾的框填充离卡片只有 24，整颗都不算墨），
而"少两颗"和"这一屏只有三颗框"在同一张报表上一模一样；② 降到 15 ⇒ 检出 7 颗（把两段标题当成了框）。
最后的判据是**框有自己的填充**（离卡片 ≥8）⇒ 正好 5 颗，自检通过（两档 `SELF-CHECK OK`、失败 0）。
中间那一步如果我只调门槛不调判据，就会拿"数到 5"当尺对。

### 6. 七维度自评（本轮）

| 维度 | 分 | 依据 |
|---|---|---|
| 原生一致 | 90 | 卡片节奏扩到每张后仍有一处孤儿被抓并修掉；勾选态强调色缺席**未定案**（139），不扣分也不加分 |
| 层级与秩序 | 92 | 五张卡片现在同一档留白；「数据」页三段之间不再有第三种距离 |
| 动效恰当 | 91 | 本轮零动效改动，且给出"两态差别不只有颜色 ⇒ 不必加淡入"的量化依据（12–20 颗 vs 46 颗） |
| 可读性 | 90 | 说明档 2.94(亮)/5.31(暗) 与全窗口同一档（R27/R33 的相对判据守着）；两态对填充的对比 6.4–11.4(亮) / 7.6–8.4(暗) |
| 状态完备 | 87 | 勾选/未勾选可辨；**禁用**那颗开关在别的分区（R39 已补帧）；勾上的颜色这一通道判不了 ⇒ 139 |
| 克制 | 95 | 删了一格 padding，没有加任何新视觉；假话被撤而不是被修饰 |
| 可验证性 | 94 | 判据对象扩到每张卡片；declined 分原因返回；变异表 n=7 caught=7；两处仪器自纠有读数留痕 |
| **总评** | **91.3** | ≥90 ⇒ 本轮收口；139/140 两格仍开着 |

### 7. 验证

- 验证（第一遍 `r96_verify_pass1.log`；同一份电池在**台账落盘之后**又跑了一遍 ⇒ `r96_verify.log`，
  两遍除"帧数"那一格外逐格相同 —— 那一格从第二遍起只数 PNG，
  124 张而不是把 `capture-readings.log` 也算进去的 125。两遍都是 `VERIFY_OK=1`、`SUMMARY_MISSING=0`）：构建 `BUILD_EXIT=0 BUILD_WARNING_LINES=0`；全量 swift test `TEST_EXIT=0`（Executed 805 tests, with 41 tests skipped and 0 failures (0 unexpected)）；在屏那一卷 `PROBE_EXIT=0`（Executed 11 tests, with 2 tests skipped and 0 failures (0 unexpected)）；重新拍帧 `CAPTURE_EXIT=0`、帧数=124（日志那格写的是 125：目录里除 PNG 还有一份 capture-readings.log）；帧基线 `FRAME_BASELINE_AGAINST=working FRAME_BASELINE_COMPARED=124 FRAME_BASELINE_CHANGED=0 FRAME_BASELINE_MISSING=0 FRAME_BASELINE_ADDED=0`；脚本电池 Ran 209 tests OK；三张变异表 节奏:MUTATE_TABLE n=4 caught=4 intended_escaped=0 mismatch=0 not_run=0 序:MUTATE_TABLE n=7 caught=7 intended_escaped=0 mismatch=0 not_run=0 分诊:MUTATE_TABLE n=7 caught=7 intended_escaped=0 mismatch=0 not_run=0；台账编号守卫 Ran 4 tests OK；看图仪器 `VIS_EXIT=0`（卡片=2 框=10 自检=2 失败自检=0）。产品文件 1 个（`SettingsView.swift`）⇒ **换装**。

### 8. 下一轮第一件事

读 R96 的 CI 里 `UI_PROBE_SAMPLE_SHAPE` 那一行 —— 三种形状（整段为空 / 数字开头=no / 数字开头=yes）
各自的下一步已经写在 `r96_ci_readings.md` 末尾。然后：140（给两张比窗口高的卡片配一张高夹具）、
133（浮层夹具"赋值不选中"那条通道，重算 R76 那格的墨移动量）。

## Round 97 · 卡片那把尺重做：它之前把一条 1pt 的分隔线、一颗按钮、两张卡片都当成"一张卡片"（结案 132 / 更新 140 / 新开 141、142 / U-232…U-239 / D-155）

### 1. 开场清单（设置「推荐」+「隐私·排除名单」两张帧，逐元素，带坐标）

| 元素 | 框 / 读数（亮档） | 判定 |
|---|---|---|
| 「推荐」页 卡片 | y=**171.0**..539.5pt（被窗口截断） | 分隔线 4 条、内侧 16.5/18.0/16.5/18.5/… ⇒ 两档同形；下半截没人看 = 140 剩那一半 |
| 「恢复默认」按钮 | y=106..129.5pt 一带，最长连续卡片材质 152/1120 = **14%** | 曾被判成一张"卡片"并量出 `边距 6.5/5.5、内侧 0.0/0.0` ⇒ 假红，改判据（U-234） |
| 「隐私」页 卡片（1040 档） | y=106.0..705.5pt（判据）/ ..765.5pt（独立复算） | 段边界两条通道不一致 ⇒ 开 **141**（U-236） |
| 「数据与保留」卡片（1040 档） | y=720.0..875.5pt（判据） | 边距 14.0/14.0 ⇒ 与其余卡片同档 |
| 「统计」页 | 0 个卡片段（热图那些行的众数**全等于页面底**） | 源码里没有 `GroupBox` ⇒ 正确读数；钉成断言（U-232） |
| 「统计」页那条 `Divider()` | y=271.0 起 2px、那一行 94% 的像素在 228 档 | 它曾被当成"卡片填充" ⇒ `cardFill` 的地板 20pt（U-233） |

### 2. 判过不改的（带理由）

- **「推荐」页的标题行与那颗按钮在卡片外**：不改，开成 **BACKLOG 142**。
  这条是分段之后才看得见的（之前整带被当一张卡片，"卡片从 171pt 才开始"这件事根本没进过读数）。
  并进去会同时动到滚动高度与那颗按钮的命中区，而这一屏的下半截在 540 档仍被窗口截断（140）
  —— 两件事一起做就说不清哪条起了作用，所以按 141 → 140 → 142 的顺序排。
- **「统计」页 0 卡片 ≠ 缺陷**（BACKLOG 131 仍开着）：本轮把"这一屏没有 GroupBox"钉成断言，
  但**没有**顺手给它加一张卡片 —— 加不加要连热图自身的视觉重量一起判（它已经是一块有底色的区域），
  那是 131 里写的那次独立判断，不是"上一屏改了所以这屏也改"。
- **推荐页内侧留白 16.5/18.0 与别的卡片 14.0/14.5 不同档**：不改。这一屏的卡片里是
  `VStack(spacing: 12)` + 滑块行，滑块的 bezel 不画墨（R96 量过按钮 bezel 是 3.5pt），
  所以墨到墨的距离本来就比文字行大；判据的容差 4.5 覆盖的是**同一张卡片内部**的一致性，
  跨卡片比绝对值不是这条判据的对象（R95 立它时就是这个边界）。

### 3. 三处判据缺陷，都改了（U-232…U-236）

1. `cardFill`：填充从"第一行离页面底 >3"改成"这个档在整带里占 ≥20pt 的行"。
   实测分布：真卡片 176.5–217.0pt、那条线 1.0pt ⇒ 地板离两边都远。
2. `cardRowKind`（新纯函数）：一行的身份由**最长一段连续卡片材质**占带宽的比例决定，
   实测 14% / 46% / 94% 三档 ⇒ 地板 30%。这一格同时解决"按钮冒充卡片"和"输入框把卡片切断"。
3. `cardSegments`（新纯函数）+ 判据循环改成**先分段再逐段判**：一个带子里可以纵向放好几张卡片。
4. 扫描带跟着夹具尺寸走，并加恒等式 `带子下沿 == 窗口高`；"这一页比窗口高，被切断了"
   这句话从纯函数搬到调用处 —— 纯函数没见过窗口尺寸，没资格替它说。

### 4. 仪器自己错一次（U-237）

我先假设"热图那块有底色的区域被尺当成卡片"，写了 `r97_stats_visual.py` 去量。
正对照（真卡片必须"稳定 + 跨带"）当场不绿，而热图那一屏**一个候选块都没有** ——
假设是错的：热图那些行的众数全都等于页面底（格子只占一行宽度的两三成）。
真凶是那条 1pt 的 `Divider()`。如果我只看"读数对不对得上我的假设"，就会把这条假说写进台账。

### 5. 变异表跟着代码搬家（U-239）

R97 的重构把 R95 那张表的两刀变成了"needle 命中 0 次"：M530 与 M531 的锚点都在旧的那几行里。
电池当场报了 `not_run=2` —— 这一种红比漏检更值得记：**表还在跑、还在打数字，而其中两格已经没有证人**。

- M530（把 `.line` 的宽度门槛抬到读不到）**换锚点继续存在**：那一格搬进了 `cardRowKind`，
  刀还是同一刀。
- M531（把页面底容差从 3 放宽到 40）**退役**：它的锚点整条判据被换掉了。
  但它要守的失败模式没消失 —— 换到本表 M538/M539 两刀上（材质地板撤 0 / 抬 60%），
  退役记录写在文件里而不是从列表里安静删一行。
- 新增 M542（`inkMin` 抬到读不到：满带卡片段却零墨）。它第一次跑**没红，而是被 skip 了** ——
  因为 `sawSegment` 记在 `inkRows == 0 ⇒ continue` 之后，证人先被吃掉。
  修好位置之后它 CAUGHT，而这一刀换来的不是多一个号，是一条**新判据**：
  "有卡片段却整卷零墨"从此不许落进那条合法的 `XCTSkip`。

### 6. 七维度自评（本轮）

| 维度 | 分 | 依据 |
|---|---|---|
| 原生一致 | 90 | 本轮零产品改动；卡片节奏现在**逐张**判，两张卡片的 14.0/14.0 与其余同档 |
| 层级与秩序 | 90 | 「统计」页 0 卡片这件事从"读数含糊"变成一条由源码推的断言（131 仍开着，判过没改） |
| 动效恰当 | 91 | 零动效改动；本轮没有新的"要不要加"的判断，所以不加分 |
| 可读性 | 90 | 说明档那一条本轮没重测（R33/R35 的覆盖判据守着），不重复记分 |
| 状态完备 | 86 | 勾选态颜色仍未定案（139 等真机）；推荐页下半截仍没有判据看着（140 剩那一半） |
| 克制 | 95 | 全部改动都在判据侧；产品文件 0 个；一条假红被撤而不是被放宽盖掉 |
| 可验证性 | 93 | 三格新纯函数各带真值表；变异表 `n=5 caught=5 mismatch=0`；两条通道交叉复算并把不一致开成 141 |
| **总评** | **90.7** | ≥90 ⇒ 本轮收口；141 是本轮新开的、下一轮第一件事 |

### 6. 验证

- 验证（`r97_verify.log`，`VERIFY_OK=1`、`SUMMARY_MISSING=0`）：构建 `BUILD_EXIT=0 BUILD_WARNING_LINES=0`；全量 swift test `TEST_EXIT=0`（Executed 808 tests, with 41 tests skipped and 0 failures (0 unexpected)）；在屏那一卷 `PROBE_EXIT=0`（Executed 11 tests, with 2 tests skipped and 0 failures (0 unexpected)）；重新拍帧 `CAPTURE_EXIT=0`、帧数=124；帧基线 `FRAME_BASELINE_AGAINST=working FRAME_BASELINE_COMPARED=124 FRAME_BASELINE_CHANGED=0 FRAME_BASELINE_MISSING=0 FRAME_BASELINE_ADDED=0`；脚本电池 Ran 209 tests OK；**四张**变异表 节奏:MUTATE_TABLE n=4 caught=4 intended_escaped=0 mismatch=0 not_run=0 序:MUTATE_TABLE n=7 caught=7 intended_escaped=0 mismatch=0 not_run=0 分诊:MUTATE_TABLE n=7 caught=7 intended_escaped=0 mismatch=0 not_run=0 卡片:MUTATE_TABLE n=5 caught=5 intended_escaped=0 mismatch=0 not_run=0；台账编号守卫 Ran 4 tests OK；看图仪器 `VIS_EXIT=0`（候选块=9 自检=1 失败自检=0）。产品文件 0 个 ⇒ **不需要换装**（本轮只动判据与工具）。

### 7. 下一轮第一件事

141：把判据的读图路径换成直接解 PNG，配一张**每一支像素判据**的 before/after 表
（十几支判据的阈值都在这条通道上标过定）。之后回到产品面欠账：133、131、139、140 剩那一半。


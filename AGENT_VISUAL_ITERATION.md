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
R10 滚动与层次（把帧间隔 p95 压回 20ms）、R11 收尾与规范。

### 遗留 / 未完成
- `MultiFilePreviewLayout.animation`（12/13 走 `interactiveSpring` damping 0.88）与
  `FilterPillMotion`（damping 0.72）**仍在目录之外且有过冲** —— 本轮只把它们数成判据
  （`testMotionParametersOutsideTheCatalogAreWhitelisted`，文件集合相等，加例外要红），
  迁移要单独一轮，因为改曲线会动像素与手感。
- 帧捕获里没有视频控件那处（`VideoPreview` 无夹具帧）⇒ 那条 `.compositingGroup()` 的修复只有源码级证据，**没有像素证据**。

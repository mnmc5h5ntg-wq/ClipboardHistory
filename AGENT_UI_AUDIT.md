# AGENT_UI_AUDIT · 视觉与交互审计（ macOS / SwiftUI + AppKit）

状态：**第 2 轮进行中**。捕获链路已跑通并修掉 4 类"假帧"；本轮修了 3 个真实缺陷（图标隐形、破坏性按钮重复、信息文字对比度不足），全部有改动前/后同参数帧与量化数字。
帧目录：`/tmp/shots5`（改后）与 `/tmp/shots4`（改前），共 54 张 = 27 个夹具 × 亮/暗。

## 方法：为什么不用截屏

本机是 macOS 27 beta。截图类通道有两个已知坑：
1. `screencapture` 在没有"屏幕录制"授权时返回全黑或报 `could not create image`，与页面是否真的绘制无关；
2. 后台窗口的动画时间线会冻结，产生"看起来空白"的假帧。

取证方式是**离屏渲染真实视图**：`NSWindow` + `NSHostingView` + `cacheDisplay(in:to:)` 绘制进 `NSBitmapImageRep` 再存 PNG。不需要任何系统授权，拿到的就是产品将要显示的那套视图树。

实现形态：**测试 target 内的捕获套件**（`Tests/ClipboardHistoryAppTests/UICaptureHarness.swift`），由 `CLIPBOARD_HISTORY_UI_SHOTS=<目录>` 触发，未设置时 `XCTSkip`，不拖慢普通测试。不改 `Package.swift`、不新增产品构建产物，随时可整体删除（回滚成本≈0）。

命令：
```
cd ClipboardHistory && CLIPBOARD_HISTORY_UI_SHOTS=/tmp/shots swift test --filter UICaptureTests
```

## 捕获链路自己产出的 4 类假帧（都已修，逐条有证据）

| # | 症状 | 根因 | 修法 | 证据 |
|---|---|---|---|---|
| A | 整块内容缩在左下角 | 裸 `NSHostingView` 没有 window，`GeometryReader`/`maxWidth` 退化 | 放进真实离屏 `NSWindow` | 修后 `content-*` 帧铺满 |
| B | 内容只占 1/4 画面 | 手工把 `rep.size` 翻倍，绘制仍按原尺寸 | 不改 `rep.size`，用 `bitmapImageRepForCachingDisplay` 给的尺寸 | 修后尺寸正确 |
| C | "暗色下详情区整块空白" | `cacheDisplay` 不画 AppKit 滚动视图/分栏的底 → 未绘制区是透明的，看图器把透明合成成白，于是"白底 + 白字" | 写 PNG 前铺一层该外观下的 `windowBackgroundColor`；并逐帧打印"未绘制像素比例"，>95% 直接判失败 | `settings-default-*-dark` 铺底后 5 个分类全部可见；比例数据见下表 |
| D | "暗色下侧栏是黑字，读不出来" | `NavigationSplitView` 的 sidebar 列在离屏 `cacheDisplay` 下不跟随强制外观：同一帧里详情列白字、侧栏列黑字；亮暗两帧侧栏像素 96.7% 完全相同 | 侧栏脱离分栏器单独拍（`sidebar-*` 夹具）；`content-*` 帧只用于核对几何与布局 | 最小复现 `/tmp/probe/split-dark.png`；同一 `HistoryRow` 独立拍是白字（`row-text-*-dark`） |

D 类值得记一笔：它一度看起来像 S1 级产品缺陷（暗色主界面完全不可读）。判据是**同一个组件在两种容器里的表现**——独立 `HistoryRow` 白字、`List`/`ScrollView` 探针白字、只有 `NavigationSplitView` 的 sidebar 列黑字。产品代码里没有任何硬编码黑字（`grep Color.black/Color.white` 只命中材质描边与阴影）。所以结论是"捕获限制"，不是缺陷；代价是 `content-*` 帧的侧栏颜色不可信，改用 `sidebar-*` 帧验收。

## 已知盲区（不当作已验收）

- 材质背景（`.thickMaterial` / `.ultraThinMaterial`）不被 `cacheDisplay` 绘制，`content-*` 帧 42–68%、`detail-*` 帧 78–87% 的像素是未绘制的；这些区域只能看几何，不能看颜色。
- `MenuBarRecommendationsView` / `MenuBarController` 不拍：构造 `AppDelegate()` 会加载**用户真实历史库**，为了拍帧去读真实数据是不可接受的。菜单文案改用 `EntryPresentation.menuLabel` 的单元测试覆盖。
- hover 态、拖拽选中间态（`.ultraThickMaterial` 选框）、`HotKeyRecorderView` 录制态、`MultiFileDetailView` 展开态：需要真实鼠标事件，离屏拿不到 → 未覆盖。
- macOS 12 的 `CompatibleSplitView` 分支：本机 13+，走不到。
- VoiceOver 实际朗读、键盘焦点跳转：无障碍树在离屏窗口里根本不建（BFS 只能走到根节点，实测"已遍历 1 个节点，标签样本=[]"）→ 只能做代码级清单，见下。

## 覆盖清单

| 视图 | 状态变体 | 尺寸 | 已拍 | 肉眼看过 | 结论 |
|---|---|---|---|---|---|
| `ContentView` | 空 / 有历史 / 无结果 / 最小 / 放大 | 600×440、750×560、1100×800 | ☑ | ☑（暗：有历史、空；亮：空） | 布局正常；侧栏颜色见盲区 D |
| `HistorySidebarView` | 单选 / 多选批量条 / 收藏筛选 / 无结果 | 300×520 | ☑ | ☑（暗：单选、多选、收藏） | 暗色文字可读；多选相邻行高亮有圆角接缝（U-10，低） |
| `HistoryRow` | 文本 / 图片 / 单文件 / 多文件 / 收藏星标 | 300×74 | ☑ | （暗：文本） | 正常 |
| `DetailView` | 文本 / 图片 / 文件 / 多文件 | 720×520 | ☑ | （暗：文本、多文件） | 正常；父目录文字改后达标 |
| `GlassPill` | 未收藏 / 已收藏 | 120×200 | ☑ | ☐ | 待肉眼复核 |
| `SearchField` | 空 / 有文本 | 320×96 | ☑ | ☐ | 待肉眼复核 |
| `EmptyStateView` | 空状态文案 | 320×160 | ☑ | ☑（亮，经 `content-empty`） | 对比度已修 |
| `SettingsView` | 快捷键 / 通用 / 隐私 / 推荐 / 数据 / 最小 | 720×540、640×440 | ☑ | ☑（暗：快捷键、通用、隐私；亮：通用、推荐、数据） | 5 个分类全部拍到；U-5、U-7 已修 |
| `RecommendationWeightsView` | 默认权重 | 520×560 | ☑ | ☐ | 待肉眼复核 |
| `MenuBarRecommendationsView` | — | — | ☐ |  | 故意不拍（会读真实数据） |
| `HotKeyRecorderView` | 常态 / 录制态 | — | ☐ |  | 未覆盖 |
| `MultiFileDetailView` | 折叠 / 展开 | — | ☑折叠 | ☑（暗） | 展开态未覆盖 |

## 量化检查

**1. 未绘制像素比例（假帧闸）** — 每帧打印，>95% 判失败。实测：自带底色的组件帧 0.0%；`content-min` 43.0%、`content-with-history` 54.1%、`content-wide` 68.3%、`settings-*` 28.6–74.1%、`detail-*` 78.3–87.1%。

**2. 文本对比度（WCAG）** — 从 PNG 直接取像素：背景=亮度众数，前景=偏离背景最大的 5% 像素均值。改动前（`/tmp/shots4`）→ 改动后（`/tmp/shots5`）：

| 文本 | 字号 | 改前 暗 / 亮 | 改后 暗 / 亮 | 判定 |
|---|---|---|---|---|
| 侧栏行时间戳 | 10pt | 2.22 / 1.89 | **5.79 / 3.98** | 暗达标 AA；亮为系统 secondaryLabelColor 上限 |
| 侧栏计数"5 条记录" | 15pt | 2.22 / 1.89 | **5.79 / 3.98** | 同上 |
| 详情"52 个字符" | 11pt | 2.47 / 2.00 | **5.65 / 4.39** | 暗达标；亮接近 AA |
| 多文件父目录 | 11pt | 2.22 / 1.89 | **5.79 / 3.98** | 同上 |
| 空状态标题 | 13pt | 2.22 / 1.89 | **5.79 / 3.98** | 同上 |
| 侧栏行标题（正文） | 12pt | 12.00 / 15.07 | 12.00 / 15.07 | 未改，一直达标 |

亮色下 3.98:1 是 macOS `secondaryLabelColor` 本身的值（50% 黑压白底）。再往上只剩 `.primary`，会抹掉整个信息层级，所以停在这里，把"亮色小字未达严格 AA 4.5:1"记为**有意取舍**而不是待修项。

**3. 截断与重叠** — 行标题 2 行 + 中间省略、文件名 middle truncation、父目录只显示上一级名，均在帧中确认无重叠、无溢出。

**4. 暗/亮一致** — 逐对比较：改前 `settings-default-*-dark` 详情区"空白"经铺底后确认为捕获产物；`content-*` 侧栏两帧像素 96.7% 相同 → 定位为盲区 D。

**5. 减少动态效果** — 审计时全仓 `grep reduceMotion` **0 命中**：17 处动画没有一处尊重系统设置（真实缺陷）。现在 `MultiFilePreviewLayout.animation(reduceMotion:)` 与 `collapsedScale(reduceMotion:)` 在系统开启「减弱动态效果」时把展开/收起与缩放退化为无动画/原尺寸；0.11–0.14s 的颜色与透明度渐变**刻意保留**（不是前庭刺激源，去掉只会让界面显得迟钝）。判定逻辑有 2 条单测；**真实开关下的观感未验证**（本环境无法切换该设置）。

## 可访问性（代码级清单，离屏拍不到）

- `EmptyStateView` 的图标从 `.quaternary` 提到 `.tertiary`：装饰图标在暗色下原本几乎不可见。
- 收藏星标用 `.foregroundStyle(entry.isFavorite ? .yellow : .clear)` 表达"未收藏"——VoiceOver 读不到状态，且 `.clear` 让未收藏行少一个视觉锚点。**未修，记为 U-11**：需要 `accessibilityLabel` 补状态，属于交互改造，风险高于本轮收益。
- `GlassPill` / `bulkActionButtons` 有 `.help()`，但 help ≠ accessibilityLabel。未修，同上。
- `ChineseMenuTextField` 吞掉 `rightMouseDown`：粘贴搜索词的路径受影响。未修。
- 键盘焦点：Tab 能否走到列表项、`⌘,` 后焦点归属，无法在离屏验证。

## 缺陷表

| ID | 现象 | 状态 | 严重度 |
|---|---|---|---|
| U-1 | 侧栏拖选行位置表只增不减 | 已修（R-40，`rowFrames = value`） | 中 |
| U-2 | 视频宽高未知时画 16:9 空播放器 | 已修（R-41，`VideoPreviewPlan.resolve` + 错误态） | 中 |
| U-3 | 详情整理解大图；KVO observer 未释放 | 已修（R-42，`deinit` 里 `invalidate`） | 中 |
| U-4 | 菜单/详情暴露正文与完整父目录 | 已修（R-43，`menuLabel` 脱敏 + `parentDirectoryLabel`） | 高 |
| U-5 | 设置侧栏未选中行的 SF Symbol 几乎不可见 | **已修**，见复验 R-a | 中 |
| U-6 | "清空未收藏记录 + 清空"在「通用」和「数据」各一份 | **已修**，只留「数据」，见复验 R-b | 中 |
| U-7 | 5 处承载信息的文字用 `.tertiary`，暗色实测 2.2:1 | **已修**，见复验 R-c | 中 |
| U-8 | `NavigationSplitView` 侧栏列离屏不跟随暗色 | 判定为**捕获限制**，改测法；非产品缺陷 | — |
| U-9 | macOS 12 设置分栏宽度约束冗余 | 未修（R-25） | 低 |
| U-10 | 多选时相邻行高亮各自圆角，交界处有暗色缺口 | 未修：要按邻居决定圆角，改动面 > 收益 | 低 |
| U-11 | 收藏状态只靠 `.clear`/`.yellow` 表达，VoiceOver 读不到 | 未修，需交互改造 | 低 |
| U-12 | 主窗口侧栏完整显示敏感 token 原文，菜单栏却脱敏 | 判定为**有意规则**：主窗口是用户显式打开的，菜单栏是环境常驻；规则写进 D-011 | 低 |

## 复验记录

**R-a（U-5）** `/tmp/shots3/settings-recommendations-720x540-light.png` vs 修复前帧。
取像素：未选中行图标核心亮度均值 (37–49)，同行文字 (46) —— 图标与文字已同为 `labelColor`；修复前图标随 `foregroundColor` 失效而落到系统弱化色。选中行图标 (22,121,246) = accentColor，正常。

**R-b（U-6）** `settings-general-720x540-light.png` 改前（`/tmp/shots2`）含"清空未收藏记录 + 清空"，改后（`/tmp/shots4`、`/tmp/shots5`）只剩"开机启动"；`settings-data-720x540-*` 仍保留该按钮与确认弹窗。测试：`swift test` 195 例全绿（无测试依赖被删）。

**R-c（U-7）** 同一夹具、同一坐标框、同一脚本，改前 `/tmp/shots4` vs 改后 `/tmp/shots5`，数字见"量化检查 2"表：5 个区域暗色全部从 2.2–2.5:1 提到 5.65–5.79:1，亮色从 1.89–2.00:1 提到 3.98–4.39:1。改动仅 5 处 `foregroundStyle` 取值，无布局变化。

## 规则

每项修复必须：改动前拍一组 → 改动后同参数再拍一组 → 在上表写清**哪两张对比、看到什么差别**。没有复验的项不得标"已完成"。

## 第二轮（2026-10-09）

外部审计（`~/Documents/时间剪史_审计_2026-10-09_第二轮/03-UI与HIG视觉审查.md`）对 UI 的判定：暗色达标、60fps 达标（p95 恒 16.67ms）、
**键盘可达性不达标**、**亮色下 chrome 不可见**、**拖拽能力为零**。本轮处理了其中三项，证据如下。

### 复验记录（第二轮）

| 项 | 对比 | 看到什么 |
|---|---|---|
| 亮色 chrome（R2-03，9 处 `.white.opacity` → `.separator` / `.quaternary` / `primary.opacity`） | `glass-pill-120x200-light.png`：`/tmp/r2_c1`（改前）vs `/tmp/r2_after2`（改后），用 `scripts/frame_audit.py` 逐像素 | 改前 chrome 像素 245–250 而背景平均 247.2 ⇒ **≤3 级差，肉眼不可见**；改后 202–207 ⇒ 43 级差，分隔线与外框出现。暗色同帧 81→64（背景 34），仍高出 30 级 |
| 捕获噪声底噪（方法级发现） | 同一份代码连拍两次：`/tmp/r2_c1` vs `/tmp/r2_c2` | **30/58 帧不同**，最大通道差 251 —— 亮色 `content-*` 帧 x≈262 处一条约 100px 高的竖线时有时无，是 field editor 的**闪烁插入点**。也就是说此前任何"逐帧差异 <0.6% ⇒ 无回归"的说法都测在这层噪声上 |
| 插入点消隐之后 | 同一份代码连拍两次（`/tmp/r2_after2` vs `/tmp/r2_after3`） | 降到 16/58 帧、0.02–0.46%、最大通道差 127，且**只在**含文本视图的 `content-*`/`detail-*`/`row-*`/`sidebar-*`；`settings-*`/`glass-pill`/`empty-state`/`notice-banner` 已完全确定 |
| 键盘批次（R2-02）有没有改坏视觉 | `/tmp/r2_c1`（改前）vs `/tmp/r2_after2`（改后）+ 上面的同代码对照 | 前后差异 30/58 帧、最大 0.46%，与**同代码连拍的对照同级** ⇒ 只能说"没有超出噪声的可测变化"，不能说"逐像素相同"。这也符合预期：本批改动（焦点环只在聚焦时出现、`.id()` 锚点、accessibility trait）在未聚焦的离屏帧上没有可绘制差异 |
| 非法 SF Symbol（R2-09） | 无法用帧验证（该错误态需要真实视频失败输入） | 改成扫描式守卫：`SystemSymbolValidityTests` 扫出 24 个符号名字面量 / 22 个不同名，全部可解析；识别器对含 `questionable` 的合成源自证有效，数量下限 18 由 grep 独立得出 |

### 第二轮的已知盲区（不当作已验收）

- **Tab 能否走到列表行**：本机 `AppleKeyboardUIMode = -1`（缺省 = 「完全键盘访问」关闭），此时 macOS 的 Tab 只在文本框与列表之间走，
  `.focusable()` 的自绘视图不进环。实测：真实 Tab 按键能到搜索框（`NSTextView(fieldEditor)`），但 8 次 Tab 都停在那里。
  方向键导航只有纯函数单测 + 接线守卫，**没有在屏证据**。复测方法：人工打开「系统设置 → 键盘 → 完全键盘访问」，
  然后 `CLIPBOARD_HISTORY_UI_INTERACTION=1 swift test --filter UIInteractionProbeTests`，看 `TAB-KEY-CHAIN` 里是否出现多种控件。
- **`selectNextKeyView` 不是 SwiftUI 焦点的正确探针**：改完焦点相关代码后 `FOCUS-CHAIN` 一个字都没变，而合成 Tab 按键的链变了。
  只测前者会把"修好了"读成"没修好"（也会反过来）。探针两条链都打，判据只用真实按键那条。
- `NSAlert` 的 Return/Escape 实际行为、拖拽（尚未实现）、菜单栏面板视觉（需要 R2-17 的 store 注入接缝）仍未验证。
- **帧对比规则升级**：从此每项视觉复验必须**同时**给出"同一份代码连拍两次"的对照数字，否则差异无法归因（见 R2-18）。
- **R2-19（本轮新发现的证据污染源）**：捕获夹具的行时间戳用 `Date()`（`UICaptureHarness.swift:254-277`），
  所以跨分钟连拍时**时钟字符串本身**就在变。11pt 字号那轮 row 帧差异 3.3–13.1%（对照带 0.12–0.38%）里混着这一项；
  肉眼核对 before/after 两帧确认字号确实变大且未裁切（`/tmp/r2_drag` vs `/tmp/r2_font` 的 `row-text-300x74-light.png`）。
  拖拽那轮的"无视觉变化"结论不受影响：它的差异（0.25–0.34%）与对照（0.12–0.38%）同量级，且都在同一分钟内拍完。

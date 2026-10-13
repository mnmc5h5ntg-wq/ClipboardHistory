# 阶段二 · 全量位点清单（2026-10-13 全新独立复审，两个只读 Explore 代理并行产出）

规则起点：**禁止假设任何现有动效合理或正确**，包括我自己 R1–R8 改过的。
这张表是选题池，不是结论 —— 每一行都要在轮次里用渲染像素重新判一次才算。

状态取值：`none` / `hover-only` / `animation(value:)` / `transition` / `AppKit-animation` /
`claimed-but-not-driven`（声明了但没有状态真的驱动它）/ `native-provided` / `menu-immovable`（NSMenu 项，AppKit 无钩子）。
判定候选：`add` / `recheck` / `deliberate-none` / `questionable-existing`。

路径前缀：`ClipboardHistory/Sources/ClipboardHistoryApp/`

---

## 第一部分：主窗口 + QuickPick（代理 A）

| # | file:line | 元素 | 当前状态 | 可感知状态 | 判定 |
|---|---|---|---|---|---|
| 1 | Views/ContentView.swift:32 | 顶部提示条容器 | animation(value:) | present/absent, warning/error | recheck：签名 5 位，正文换字不插值 |
| 2 | Views/ContentView.swift:48-81 | 五条 banner 插删 | transition | absent↔present | recheck：需像素证明滑动 |
| 3 | Views/ContentView.swift:7-8 | banner 挤下的 split view 位移 | none | 0 条 / ≥1 条 | **add**：banner 淡、内容整帧下移 ~34pt |
| 4 | Views/NoticeBanner.swift:28-44 | 提示条本体 | none | warning/error | deliberate-none（过渡在调用侧） |
| 5 | Views/SearchField.swift:11-47 | 搜索框 | animation ×2 (42,43) | hovered/idle, 空/非空 | recheck：`isActive` 不含键盘聚焦 |
| 6 | Views/SearchField.swift:20-29 | 「清除搜索」圆钮 | 有 animation 无 transition | absent↔present | **add**：每次按键硬生硬灭 |
| 7 | Views/SearchField.swift:24 | 清除钮图标色 | hover-only | 整框 hover | questionable：响应框悬停而非钮悬停 |
| 8 | Views/ChineseTextContextMenu.swift:138 | 搜索框焦点环 | native-provided | focused | deliberate-none |
| 9 | Views/HistorySidebarView.swift:19-24 | 分段筛选轨道+滑块 | animation @366 | 0/1 | recheck：见 40 |
| 10 | Views/HistorySidebarView.swift:344-350 | 段按钮字重切换 | none | selected | **add**：regular↔semibold 整帧换 |
| 11 | Views/HistorySidebarView.swift:371-397 | 段按钮 hover 1.08 | hover-only | hovered | questionable：环境 reduce ≠ catalog 门 |
| 12 | Views/HistorySidebarView.swift:29-30 | header Divider | none | — | deliberate-none |
| 13 | Views/HistorySidebarView.swift:56-59 | 「时间剪史」→「已选 N 条」 | none | bulk | **add**：兄弟文本淡入（67,73）它硬换 |
| 14 | Views/HistorySidebarView.swift:63-74 | 批量按钮组 vs 计数 | transition + anim @79 | 选中 ≤1/>1 | recheck |
| 15 | Views/HistorySidebarView.swift:84-124 | 五颗批量按钮 | none（`.borderless`） | hover/press/disabled | **add**：全组零按压零悬停，与 PressableStyle 前提矛盾 |
| 16 | Views/HistorySidebarView.swift:121 | 删除钮红色 | none | hovered | deliberate-none |
| 17 | Views/HistorySidebarView.swift:162-172 | 行增删/重排 | claimed-but-not-driven（:173-186 明示无过渡） | insert/remove/reorder | deliberate-none（实测死过，有档） |
| 18 | Views/HistorySidebarView.swift:162 | 行选中高亮 | native-provided | selected | deliberate-none |
| 19 | Views/HistoryRowViews.swift:20-52 | 整行 hover 底色 | none | hovered | **add**：整行没有悬停表达，只有星标有 |
| 20 | Views/HistoryRowViews.swift:81-119 | 行首星标 | hover-only + anim @106 | fav/hover/press | recheck：命中 20×20pt（:100）低于 28 |
| 21 | Views/HistoryRowViews.swift:97-99 | star↔star.fill | animation(value:) | 0↔1 | recheck：文件自注（:94-96）承认 List 内未测 |
| 22 | Views/HistoryRowViews.swift:129-149 | 固定徽标 pin.fill | transition @141 + anim @147 | pinned | recheck：行同时瞬移，淡入可能读不见 |
| 23 | Views/HistoryRowViews.swift:158-182 | 缩略图 vs 占位 | none | 异步落地 | **add**：`applyThumbnail`（HistoryStore:834）硬换 |
| 24 | Views/HistoryRowViews.swift:185-211 | 行文本列/时间戳 | none | 内容变化 | deliberate-none |
| 25 | Views/ThumbnailView.swift:3-23 | 16pt 图片缩略图 | none | decoded | **add**：首帧硬蹦 |
| 26 | Views/ThumbnailView.swift:25-44 | 类型占位符号 | none | — | deliberate-none |
| 27 | Views/ContentView.swift:84-91 | NavigationSplitView 收起 | none（AppKit 抑制） | collapsed | deliberate-none（WindowConfigurator:258-280） |
| 28 | Views/HistorySidebarView.swift:195-219 | 拖入落点虚线框 | transition @205 + anim @220 | targeted | recheck：需证明缩放真渲染 |
| 29 | Views/HistorySidebarView.swift:210-217 | 落点光晕 | transition @216 | targeted | questionable：自己注释（:208-209）说 HIG 不鼓励动画模糊 |
| 30 | Views/DetailView.swift:36-56 | 详情空态↔有条目 整块交换 | 只有空臂有 transition @47；anim @55 | selection nil/非 nil | **questionable**：:71-75 承诺的是**交叉**淡，入臂没有过渡 |
| 31 | Views/DetailView.swift:59-105 | selectedEntryView | animation @81 keyed by DetailPreviewKind | 类型变化 | recheck |
| 32 | Views/DetailView.swift:64 | preview 块换类型软交接 | transition + 有驱动 | text/image/file/files | recheck：键含 .renderedText/.rawText ⇒ markdown 切换也触发 |
| 33 | Views/DetailView.swift:61 | 头部 meta 一行 | none | 逐条目变化 | **add**：文字硬换、截断宽度变化都不动 |
| 34 | Views/DetailView.swift:180-184 | 「原文/渲染」按钮出现与否 | none | offered/not | **add**：某些行有某些行没有，整帧 |
| 35 | Views/DetailView.swift:217-251 | 该按钮 hover 底色 | hover-only（withAnimation @246） | hovered/pressed | recheck：命中高度=11pt 行高，无竖直 padding |
| 36 | Views/DetailView.swift:242 | 同按钮按压 | animation @PressableStyle:56 | pressed | recheck |
| 37 | Views/DetailView.swift:89-104 | GlassPill 随选中出现/消失 | none | present/absent | **add**：取消选中时整块弹出 |
| 38 | Views/DetailView.swift:114-157 | 「已复制」回执 1.1s | withAnimation(.emphasis) @120,153 | idle/confirmed/failed | recheck |
| 39 | Views/DetailView.swift:196 | `chrome.detailContentTopInset` 留白 | none（布局） | 26/33/35pt | questionable：随 resize/key 整帧跳（见 57） |
| 40 | Views/HistorySidebarView.swift:286-315,366 | FilterPillMotion 滑块 | animation，**0.38s spring damping 0.72** | 换档 | **questionable**：违反 catalog 自己的 ≤0.25s 与不过冲两条 |
| 41 | Views/DetailView.swift:339-371 | MultiFilePreviewLayout.animation | animation ×4 (307,476,477,542) | 展开/高度 | questionable：reduce ⇒ `.linear(duration:0)`（361）是清零不是替换 |
| 42 | Views/DetailView.swift:444-474 | 可展开预览高度 | animation @476-477 (frame height) | 展开/收起 | deliberate-none（有案可查的布局动画例外） |
| 43 | Views/DetailView.swift:538-542 | 展开箭头旋转 90° | animation @542 | collapsed/expanded | recheck |
| 44 | Views/DetailView.swift:524-588 | 多文件行 hover 底色+描边 | hover-only（withAnimation @584） | hovered/pressed | recheck |
| 45 | Views/DetailPreviewViews.swift:217-238 | 预览三态交换 | transition ×3 + animation @238 | loading/success/error | recheck：看着是对的，要像素 |
| 46 | Views/DetailPreviewViews.swift:289-300 | 骨架 + 「正在加载预览…」 | 手动 Timer | loading→gone | recheck |
| 47 | Views/DetailPreviewViews.swift:302-312 | 失败态 | transition @228 | error | recheck |
| 48 | Views/DetailPreviewViews.swift:277 | QuickLook 内嵌 NSView 落地 | none | not-ready/ready | **add**：外面淡、里面硬蹦 |
| 49 | Views/DetailPreviewViews.swift:347-359 | videoAspectRatio(for:) | n/a | n/a | unsure（疑似死代码，零调用） |
| 50 | Views/SkeletonShimmer.swift:104-151 | 扫光（30Hz Timer 改 phase） | 手动时钟，**无 .animation** | sweep/static | recheck：一周期 45 个离散档，档间不插值 |
| 51 | Views/ImagePreviewView.swift:6-21 | 大图 + 双向滚动 | none | loaded/oversized/scrolled | **add**：解码到达硬蹦；滚动偏移无声复位 |
| 52 | Views/VideoPreview.swift:250-258 | 播放进度 Slider | none（0.2s 发布） | currentTime | **add**：滑块 5 档/秒可见台阶 |
| 53 | Views/VideoPreview.swift:243-248,260-263 | 时间文本 | none | ticking | deliberate-none（等宽数字） |
| 54 | Views/VideoPreview.swift:228-241 | 播放/暂停换符号 | animation @238 + symbolMotion | playing/paused | recheck：命中 22pt，符号 16pt |
| 55 | Views/VideoPreview.swift:265-274 | 静音换符号 | animation @271 | muted | recheck |
| 56 | Views/VideoPreview.swift:226-288 | 控件条玻璃胶囊 | none（常驻） | shown/hidden | deliberate-none：根本不存在 auto-hide，可作为设计疑问记录 |
| 57 | Managers/WindowConfigurator.swift:214-217 | 交通灯带底边发布 | none | 10/26/33/35pt | recheck：驱动 39 的无动画跳位 |
| 58 | Managers/WindowConfigurator.swift:218-230 | `setFrameOrigin` 重摆三钮 | 直接设 frame（无动画） | toolbar 有无/宽度 | recheck：resize 时按钮瞬移 |
| 59 | Managers/WindowConfigurator.swift:144-150,153-178 | 反复移除 sidebar toggle | none | 按钮出现→消失 | questionable：启动后可能闪回约 1 秒 |
| 60 | Managers/WindowConfigurator.swift:97-100 | zoom 按钮禁用 | native-provided | disabled | deliberate-none |
| 61 | Managers/QuickPickController.swift:151 | 浮层呼出/关闭 | none（`animationBehavior = .none`） | visible/hidden | deliberate-none（快捷键规矩，已记录） |
| 62 | Managers/QuickPickController.swift:294-299 | 候选行增删 `.effectFade` | AppKit-animation | rows in/out | recheck：需真实按键证据 |
| 63 | Managers/QuickPickController.swift:289-292 | 整体重排退回首 `reloadData()` | none | 新复制置顶 | **add**：自己日志写着 "no row animation"，整屏闪 |
| 64 | Managers/QuickPickController.swift:305-307 | 行文案原地刷新 | none | 标题变化 | **add**：动画中的表里整帧换字 |
| 65 | Managers/QuickPickController.swift:226-227 | 选中行 + `scrollRowToVisible` | native（瞬时） | 索引移动 | **add**：方向键连发是硬切，无平滑滚动 |
| 66 | Managers/QuickPickController.swift:238-271 | 空结果淡入淡出 | AppKit-animation（`animator().alphaValue`） | empty/non-empty | questionable：自己注释（:236-237）说从未测过 |
| 67 | Managers/QuickPickController.swift:153-163 | 浮层搜索框文字 | none | typing | deliberate-none |
| 68 | Views/GlassControls.swift:21-74 | 胶囊本体 | animation ×2 @64,65 | favorite, pinned | recheck |
| 69 | Views/GlassControls.swift:47-54 | 复制键 doc→checkmark→! | withAnimation（来自 DetailView） | idle/confirmed/failed | recheck：三段都要有像素 |
| 70 | Views/GlassControls.swift:58 | 删除键 | hover-only | hovered/pressed | recheck：无破坏性额外表达 |
| 71 | Views/GlassControls.swift:81-87 | 胶囊内分隔线 | none | — | deliberate-none |
| 72 | Views/GlassControls.swift:164-169 | 44pt 圆 hover 底色 0.10 | hover-only | hovered | recheck |
| 73 | Views/GlassControls.swift:67-73 | 玻璃底/描边/投影 | none | static | deliberate-none：全仓没有材质过渡 |
| 74 | Views/MotionModifiers.swift:31-33 | `.symbolEffect(.replace)` 14+ | 依赖调用侧事务 | 符号身份变化 | recheck |
| 75 | Views/MotionModifiers.swift:37 | 12/13 臂 `.id(symbol).transition(contentFade)` | transition | 符号身份变化 | **questionable**：`.id()` 强制重建 ⇒ 不可能交叉淡，只有从透明淡入 = 一帧空白，正是 DetailView:72-74 要避免的那个 |
| 76 | Views/MotionModifiers.swift:46-48 | `.symbolEffect(.bounce, value:)` | animation | 0↔1 | questionable：bounceValue 取的是**结果态**，奇偶可能只响一次 |
| 77 | Views/PressableStyle.swift:37-58 | 全 App 按压态 | animation @56 | pressed | recheck |
| 78 | Views/PressableStyle.swift:51-54 | 按压底色 fillOpacity | claimed-but-not-driven | — | **questionable**：调用点硬写 `isHovered: false` ⇒ `VisualFill.hover` 档全 App 不可达 |
| 79 | Views/PressableStyle.swift:48-50 | 按压缩放 0.97 | animation | pressed | recheck：44pt 上只有 1.3pt；另有两处 `scales:false` |
| 80 | Views/ViewExtensions.swift:5-11 | 窗口材质 containerBackground | none | 外观切换 | deliberate-none |
| 81 | Views/EmptyStateView.swift:18-38 | 空态整体 | 调用侧 transition | 空态 A/B/C | recheck |
| 82 | Views/EmptyStateView.swift:31-35 | 空态里的「清除搜索」 | none | shown/hidden | **add**：已在淡的面板里整帧出现 |
| 83 | Views/NoticeBanner.swift:33-36 | StateLine 图标+文字 | none | warning/error、换字 | **add**：banner 不消失而换字时，"变了"这件事不可见 |
| 84 | Views/RecommendationWeightsView.swift:14-17 | 「恢复默认」 | none | pressed | **add**：所有滑轨 1 帧跳到 1.0 |
| 85 | Views/RecommendationWeightsView.swift:59-63,74-77 | 百分比文字三档色 | none | <1/=1/>1 | **add**：拖动中灰→主色→橙硬切 |
| 86 | Views/RecommendationWeightsView.swift:84 | Slider | native-provided | dragging | deliberate-none |
| 87 | Utilities/MarkdownAffordance.swift:15-47 | 纯判定 | n/a | n/a | deliberate-none（后果是 32/34） |
| 88 | Views/ChineseTextContextMenu.swift:497-503 | 自绘右键 NSMenu | native | opening/closing | deliberate-none |
| 89 | Views/ChineseTextContextMenu.swift:91-102,505-508 | `menuWillOpen` 里 sanitize 删项 | native | 项被删 | unsure：是否触发表面重排未证 |

### MotionCatalog 各档（Utilities/MotionCatalog.swift）

| role | line | 时长 | 实际曲线 | reduce 替换 | 是否被视图引用 |
|---|---|---|---|---|---|
| .hover | 42,80 | 0.12 | timingCurve(0.23,1,0.32,1) | 同形 | 是（PressableStyle/SearchField/Row/Sidebar/Detail×2/GlassControls/SettingsView:768/Heatmap:190） |
| .selection | 43,81 | 0.12 | timingCurve(entrance) | 同 | 是（Sidebar:79,392；Settings:769） |
| .bannerIn | 44,82 | 0.15 | spring(response .15, damping 1.0) slides=.top | 滑→淡（:139） | 是（ContentView ×6） |
| .bannerOut | 45,83 | 0.12 | timingCurve(0.2,0,1,0.9) | 同 | 是 |
| .emphasis | 46,84 | 0.16 | timingCurve(entrance) | 同 | 是（DetailView ×4；Glass ×2） |
| .dropTarget | 47,85 | 0.12 | timingCurve + .scale(0.98) | 缩放与光晕直落（:143-144） | 是（Sidebar ×4） |
| .contentFade | 48,86 | 0.16 | timingCurve(entrance) | 同 | 是（17 处） |
| .skeletonSweep | 50,87 | **1.5**（环境档，:66 豁免 0.25 上限） | timingCurve(linear) —— **曲线从未被消费**，只读 `duration(for:)`（SkeletonShimmer:112） | 根本不画带子 | 半死：curve/transition 两支是死的 |

其他：`maximumDuration`:55、`minimumAmbientDuration`:69 只有测试读；`criticalDamping`:75 只服务滑入分支；
`Shape.Slide.bottom/.leading/.trailing`（:114）**不可达** —— `shape(for:)`（:128-147）只产 `.none`/`.top`。
`animationsEnabled`:281 生产读点只有 MotionCatalog:202 与 QuickPickController:296。

### reduce-motion 读取点（两套互相矛盾的闸门）

| file:line | 读什么 | 替换成 |
|---|---|---|
| MotionCatalog.swift:259-270 | `accessibilityDisplayShouldReduceMotion` ∪ VoiceOver（唯一全源闸门） | :128-147 分档替换表，时长不清零 |
| AppDelegate.swift:125-133 | `accessibilityDisplayOptionsDidChangeNotification` | 触发 `historyStore.objectWillChange` 让 body 重读 |
| **HistorySidebarView.swift:334 与 :376** | `@Environment(\.accessibilityReduceMotion)` —— **只认系统开关，不认 VoiceOver** | `slideAnimation`→`.linear(duration:0)`（:306，**清零**）；`hoverScale`→1.0 |
| DetailView.swift:352,361,465 | `MotionCatalog.motionShouldBeReduced` | `.linear(duration:0)`（清零）；`collapsedScale`→1 |
| PressableStyle.swift:44,49 | 同上 | 缩放→1.0，底色保留 |
| SkeletonShimmer.swift:106,111 | 同上 | 条子仍画，带子与 Timer 不跑 |
| MotionModifiers.swift:46 | 同上 | bounce 撤，replace/fade 留 |
| QuickPickController.swift:246,295 | 同上 | 空态标签瞬时；行选项 → `[]`（:318） |

无人读 `NSReducedMotion` / UserDefaults。**"替换而非清零"这条 R1 定的规矩，在 Sidebar:306 与 Detail:361 两处其实被违反了**（`.linear(duration: 0)` 就是清零）。

---

## 第二部分：设置窗口 + 菜单栏（代理 B）

### SettingsView.swift

| file:line | 元素 | 状态 | 可感知状态 | 判定 |
|---|---|---|---|---|
| 221 | NavigationSplitView（13+） | native | 侧栏折叠 | deliberate-none |
| 230 | CompatibleSplitView（12，NSSplitView） | none | 分隔条像可拖 | questionable：:814 固定宽约束，拖不动 |
| 247 | 分类内容 Group + `.id(selectedCategory)` | transition | 换分类 | recheck：挂在 ScrollView 内首帧可疑 |
| 266 | `.transition(contentFade)` | transition | 换分类进出 | recheck：旧页高度不跟着淡 |
| 270 | `.animation(value: selectedCategory)` | animation | 换分类 | recheck：作用面只覆盖 VStack 直接子树 |
| 280/282/289/296 | 「快捷键」GroupBox + 三行 HotKeySettingsRow | none | — | recheck：行零 hover / 零焦点表达 |
| 696 | 「恢复默认」按钮（3 处共用） | native | pressed | **add**：⌘ 值瞬间跳回，无过渡无提示 |
| 702 | `settings.message` 红色错误行 | none | error 出现 | **add**：热键注册失败的唯一可见证据，突然出现 |
| 314 | 「开机启动」Toggle | native | on/off/disabled(:315) | deliberate-none；disabled 原因不可读 |
| 320 | 「暂停记录剪贴板」Toggle | native | on/off | questionable：暂停态在本页之外零处可见（菜单栏图标不变） |
| 321 | 暂停说明 caption | none | — | deliberate-none |
| 325/326 | OCR / 富文本 Toggle | native | on/off | deliberate-none |
| 337 | `loginItemSettings.message` | none | error | **add**（LoginItemSettings.swift:114 的文案突然出现） |
| 367-385, 390 | 上下文权限 4 + 推荐过滤 Toggle | native | on/off | deliberate-none |
| 408 | 默认排除 App 只读列表 | none | — | deliberate-none |
| 413 | 用户排除名单 ForEach | transition | 行增删 | recheck |
| 427 | 行 `.transition(contentFade)` | transition | 插入/移除 | recheck：移除臂无证据 |
| 417 | 「移除」`.borderless` 钮 | none | hover/press | **add**：破坏性小钮零反馈 |
| 430 | Bundle ID TextField | native | focused | deliberate-none（另记：无 `.onSubmit`） |
| 433 | 「添加」按钮 | native | pressed | recheck：六种结局只靠文字区分 |
| **443** | 排除回执 `ReceiptLine` | claimed-but-not-driven | 六种 outcome | **add**：四种不改 raw ⇒ 无事务 ⇒ 过渡不演 |
| 449 | `.animation(value: excludedBundleIDsRaw)` | animation | 名单长度 | questionable：键与回执状态**不同源**（`exclusionReceipt` 才是那半条） |
| 458 | OCR 存放方式 Picker(.radioGroup) | native | selected | native |
| 476, 567 | 说明 GroupBox ×2 | none | — | deliberate-none |
| 501 | 嵌入 RecommendationWeightsView | none | 见下节 | recheck |
| 510/515/520 | 「导出反馈数据」钮 / 回执 / `.alert` | native / claimed / native | success/error/noData | **add**：该 section 无一条 `.animation`；同一条信息两条通道 |
| 531/536 | 「统计」section / DailyCopyStatsSection | none | 数据刷新 | **add**：格子深浅整帧跳 |
| 539 | 账本缺失 `StateLine(.error)` | none | error | recheck：SettingsWindowController:77 注入前为 nil ⇒ 会真出现 |
| 847 | DailyCopyHeatmapView 宿主 | none | loading→data | **add**：无首帧淡入 |
| **848** | 写盘失败行 `Text("统计写入失败…")` | claimed-but-not-driven | error | **add（真 bug）**：`lastWriteError`（DailyCopyLedger:55）是**算属性读锁盒**，没有任何东西为它发布 ⇒ 不复制就不上屏，重启后永远是 nil |
| 589/591/594 | 导出/导入按钮 + `archiveMessage` ReceiptLine | native / claimed | success/error | **add**：dataSection 无对应 animation 键 |
| 613/618 | 「清空」.borderedProminent + .tint(.red) | native | pressed/disabled | deliberate-none |
| 620/630/635 | 清空回执 HStack / transition / animation | transition + animation | nil→有 | recheck（图标可单独强调一档） |
| 205 | 清空确认 `.alert` | native | 出现 | native |
| 718 | 分类侧栏 ForEach | none | selected | — |
| 743 | 分类行按钮 | AppKit（PressableStyle:56） | pressed | recheck：`scales:false` + `isHovered:false` |
| 747 / 762 | Label 上色 / 背景 fill | animation(768,769) | hover/selected | recheck：accent↔primary 色相硬切 |
| 755 | `.symbolRenderingMode(.hierarchical)` | none | selected | deliberate-none（已实测，别动） |
| **766** | 选中改 `.semibold` | none | selected | questionable：字重不可插值 ⇒ 文字宽度跳位，与 768/769 的淡入读起来矛盾 |
| 768/769/770 | `.animation(.hover)` / `.animation(.selection)` / `.onHover` | animation | hover/select | recheck（前轮改过 → 必须实测帧） |
| 869/874/876/863 | 回执「×」钮 / helpLabel / transition / 文字 | none / native / transition / none | hover/press/换字 | **add**：文案换字零过渡零播报；调用侧三处里两处无驱动 |

### RecommendationWeightsView（嵌「推荐」分类）

14 「恢复默认」native → **add**（10 条滑轨+百分比一起跳）；68 因子标题 deliberate-none；
74 百分比 Text（「默认」↔数字）none → **add**；76 `tintColor` 三档（secondary/accent/orange）none → **add**（本页唯一状态通道）；
84 Slider native deliberate-none；37/23 Divider/GroupBox deliberate-none。

### DailyCopyHeatmapView（阶段一新功能，逐元素）

| file:line | 元素 | 状态 | 判定 |
|---|---|---|---|
| 37 | 根 VStack | none | **add**：空态↔有数据整块换态无过渡 |
| 56 | 标题「每日复制」 | none | deliberate-none |
| 58 | 汇总行（总/日均/连续） | none | **add**：`counts` 每次 +1 整行硬换字 |
| 43 | 空态 `StateLine(.empty)` | none | **add**：第一条复制那一下最该被看见 |
| 71 | 网格容器 | none | recheck |
| 94/103 | 月标签行 ZStack + `.offset(x:)` | none | questionable：每天整行标签瞬移一格，可给一次平移 |
| 111/114 | 星期标签列 | none | deliberate-none |
| 142 | 未来/窗口外 `Color.clear` | none | deliberate-none（注释明确不能画灰格） |
| 145 | 格子填充色（bucket） | none | **add**：当天那格浅→深硬切，是唯一实时通道 |
| 153 | 悬停描边 0↔0.55 | hover-only | **add**：`.animation`（:190）只包页脚 Text ⇒ 格子描边硬生硬灭 |
| 157 | `.contentShape(Rectangle())` | none | deliberate-none（11pt 无命中补偿 → 可议） |
| 158 | 每格 `.onHover` | hover-only | recheck：126 个闭包；离开顺序可能留悬停残留 |
| 161 | `.accessibilityElement()` | none | deliberate-none |
| 165 | 每格 `.helpLabel(tooltip)` | native | questionable：同一条话同时是 tooltip 与页脚，双通道不同步 |
| 172/174 | 「少/多」+ 图例 5 格 | none | deliberate-none（图例 hover 联动该档 = 低优先可议） |
| 184/190 | 页脚详情 + `.animation(value: hovered?.dayKey ?? "")` | animation | **questionable**：驱动的是不可插值的字符串替换 ⇒ 声明但空转；键 `""` 不区分"未悬停"与"未定义格" |
| 196 | `footerDetail` 回落最忙日 | none | recheck：回落那一下读起来像文字自己跳 |

### HotKeyRecorderView（NSButton 自绘）

53 标题硬换 **add**；**66 进入录制态只换标题文字**（核心状态！无描边/底色/脉冲）→ **add**；
67 `makeFirstResponder` 靠系统环 recheck；83 无效组合回落 → **add**（错误唯一证据是 702 那行字）；
92 成功回显新组合 → **add**（现成的 `.emphasis` 档没人用）；97 点别处静默取消录制 → questionable；107 取消回落 → **add**。

### 政策 → 界面映射（六种结局）

`ExcludedAppListPolicy` 六结局唯一显示位 = SettingsView:443 的 `ReceiptLine`：
`.added`(55) / `.removed`(67) 改 `excludedBundleIDsRaw` ⇒ :449 有事务；
`.alreadyListed`(47) / `.coveredByDefault`(51) / `.emptyInput`(41) / `.notListed`(63) **不改 raw ⇒ 四种结局的回执永远不演过渡**。
`ClearHistoryReceiptPolicy`：`removed==0`(35) / `>0`(37) → SettingsView:620（视觉）+ :211 `VoiceOverReceipt.announce`。
**另一条清空路径** `AppCommand.clearHistory` → ApplicationShell:184-193：只有确认弹窗，**没有任何回执文本**（HistoryStore:602 的 `.clear` 也不产可见通知）⇒ 菜单入口清空后界面不说"清掉了多少"，与设置页路径**行为分叉**。

### 菜单栏 / NSMenu

| file:line | 元素 | 判定 |
|---|---|---|
| App.swift:24 | `MenuBarExtra(…,"clipboard")` 图标永不变 | questionable：暂停/条数/失败都不改（无动效钩子，只有"该不该发声"） |
| App.swift:26/32/33 | Divider / 退出 | menu-immovable |
| App.swift:27-31 | 4 条命令按钮恒 enabled | questionable：空历史也可点「清空未收藏」 |
| MenuBarController.swift:22-26 | 13+ 直接 return，NSStatusItem 路径不建 | 事实记录 |
| :39-44 | 状态栏按钮（imageOnly + 固定 toolTip） | questionable |
| :59-62 | `menuWillOpen` 整菜单 removeAllItems 重建 | menu-immovable（明确不编造钩子） |
| :70 / :88-107 / :140-144 / :146 | 标题项 / 推荐项 / 命令项 / target | menu-immovable |
| :75-86 | 「猜你要粘贴」小节整体出现/消失 | menu-immovable |
| :111-120 | 「都不是我想要的」蓝色项出现/消失、点击无回执 | menu-immovable + questionable |
| **:127** | `正在整理推荐…` ↔ `暂无推荐` 只在开菜单那一刻求值 | questionable：异步落地后菜单不说"算完了" |
| :129 | 占位项 isEnabled=false | menu-immovable |
| :187-222 | 自绘 template 状态栏图标 | questionable：与 App.swift:24 的 SF Symbol 是**两套图形语言** |
| MenuBarRecommendationsView:23-25 | StateLine(.loading/.empty) | menu-immovable；:26-29 注释明确刻意不挂 transition |
| :37-69 | 推荐行 Button(.plain) | deliberate-none（菜单自高亮，不叠自绘底） |
| :73-81 / :85-89 | 「都不是我想要的」/ onAppear 触发 refresh | questionable：结果落地时菜单已在显示，无再刷新通道 |
| SettingsWindowController:43-48 | `showWindow` + `center()` 每次回到屏幕正中 | questionable：窗位每次硬跳（非动效但纯视觉） |
| :55-66 / :77 | 窗口只建一次 / ledger 注入时机 | deliberate-none / recheck |
| MediaLoader:21-102 | loading/success/failure 状态机 | 设置/菜单侧**无消费方**，本轮无候选站 |

### 机械交叉核对（代理 B 范围内 grep 实测）

`.transition(` — SettingsView 266,427,630,876；DailyCopyHeatmapView **0 处**。
`.animation(` — SettingsView 270,449,635,768,769；Heatmap 190；PressableStyle 56。
`.onHover` — SettingsView 770；Heatmap 158。裸 `.help(` — 0。`.helpLabel(` — SettingsView 874；Heatmap 165。
`withAnimation` — **0 处**（HotKeyRecorderView / RecommendationWeightsView / MenuBarRecommendationsView / 所有 Managers 一行都没有）。

### 设置分类 × 控件种类（覆盖证明用）

| 分类 | 图标 | 控件种类 |
|---|---|---|
| 快捷键 | `command` | GroupBox、HotKeySettingsRow、NSButton 录制钮、`.rounded`「恢复默认」、Divider、红色错误 Text |
| 通用 | `gearshape` | Toggle×4、`.disabled`、caption、可选 message、GroupBox |
| 隐私 | `hand.raised` | Toggle×5、Divider、只读 Text 列表、可删行 + `.borderless`「移除」、TextField `.roundedBorder`、「添加」钮、ReceiptLine、Picker(.radioGroup)、GroupBox×2、静态 bullet |
| 推荐 | `wand.and.stars` | RecommendationWeightsView（Button + Slider×10 + 百分比 Text + Divider×9 + GroupBox）、`.bordered` 导出钮、ReceiptLine、`.alert` |
| 数据 | `folder` | 静态 Text/GroupBox、Button×2（disabled）、ReceiptLine、`.borderedProminent`+`.tint(.red)`、`.alert`、回执 HStack（`checkmark.circle`+Text）、Divider |
| 统计 | `chart.bar` | DailyCopyHeatmapView（标题、汇总、月标签行、星期列、26×7 方块 + strokeBorder hover、图例 5 格、页脚）、StateLine(.empty/.error)、Divider、静态说明 |

附带非动效观察：`VisualTokens.swift:73` 注释曾按 18 周估算而实现是 26 周（**已在阶段一收尾改为 26 并留 D-068**）；
`SettingsView.swift:430` 输入框无 `.onSubmit` 回车提交。

---

## 第三部分：两轮都要用的"最可能真缺陷"合并榜（去重后按可信度）

1. SettingsView:848 + DailyCopyLedger:55 —— 写盘失败文案**没有发布通道**（功能级 bug，不是动效）。
2. SettingsView:443/449 —— 六种排除结局里四种拿不到动画事务（键错）。
3. SettingsView:594 与 :515 —— 两处 `ReceiptLine` 有 transition 但所在 section 无 `.animation` ⇒ 永不演。
4. DetailView:38 vs :47 —— 只有空臂有过渡，注释承诺交叉淡（阶段二 R5 的旧账）。
5. PressableStyle:53 —— `isHovered: false` 硬编码 ⇒ `VisualFill.hover` 档全 App 不可达。
6. HistorySidebarView:300/366 —— 筛选滑块 0.38s / damping 0.72 越过硬上限与不过冲两条。
7. HistorySidebarView:334/376 + :306、DetailView:361 —— reduce 闸门两套且"清零而非替换"。
8. DailyCopyHeatmapView:153/190 —— 悬停描边无插值；`.animation` 驱动不可插值字符串 = 空转。
9. MotionModifiers:37 —— `.id()+.transition` 在 12/13 臂只有淡入，一帧空白。
10. QuickPickController:289-292 / 305-307 / 226-227 —— 重排退回首 `reloadData`、原地换字、滚动无平滑。
11. HistorySidebarView:84-124 —— 五颗批量按钮（含删除）零按压零悬停，`.borderless` 全 App 唯一一处。
12. HotKeyRecorderView:66 —— 录制态只换标题，没有描边/底色/脉冲；:97 失焦静默取消。
13. RecommendationWeightsView:74/76 —— 三档色 + 「默认」↔数字，本页唯一状态通道零动效。
14. ContentView:7-8 —— banner 淡、下方内容整帧位移 34pt。
15. SearchField:20-29 + EmptyStateView:31-35 —— 清除钮两次硬生硬灭。
16. SkeletonShimmer:113-116 + MotionCatalog:87 —— `.skeletonSweep` 曲线/过渡声明且被测试，但从未喂给 SwiftUI（45 个离散档不插值）。
17. MenuBarController:127 + MenuBarRecommendationsView:85-89 —— loading 只在开菜单那刻求值。
18. ApplicationShell:184-193 vs SettingsView:620 —— 两条清空路径回执分叉。
19. SettingsWindowController:43-48 —— 设置窗每次呼出硬跳回正中。
20. WindowConfigurator:214-217 → DetailView:196 —— 顶留白随 chrome 变化整帧跳。

## 轮次排期（R9 起，每轮 ≤4 文件，先看像素再动手）

### 排期会漂移，所以记两栏：计划 / 实际（截至 R13）

| 轮 | 计划时写的 | 实际做的 | 账 |
|---|---|---|---|
| R9 | 热图自检（缺陷 1、8、Ledger 发布通道） | 同：hover 供电、空转的 `.animation` 撤掉、两臂过渡配对 | D-068 / U-30 续、91 分 |
| R10 | 设置页三处"回执不演"（2、3） | **改道**：先做"写盘失败要能被看见"（`lastWriteError` 的发布通道）+ 探针名单从产品推导 | D-069 / U-32、90 分 |
| R11 | 侧栏批量按钮与字重跳变（11、15） | **改道**：淡入的可测性（冷采样闸门 + 双向 A/B ⇒ "源码已接、产物未量"这一类的定性方法） | U-33、92 分 |
| R12 | 筛选滑块越权与两套 reduce 闸门（6、7） | 同，并加"reduce 时悬停零反馈"那条空洞 | D-070 / U-34、93 分 |
| R13 | PressableStyle hover 死档（5） | 同 + 三处 `.borderless` 归队（缺陷 11 一起做掉了）+ 守卫检测面加宽 + M58 逃逸后补接缝判据 | D-071 / U-35 |

**两次改道的原因相同**：动手前发现"尺子看不见我要改的东西"，就先修尺子。
这不是发散 —— 在 R11 之前我并不知道纯 opacity 淡入不在 `cacheDisplay` 的可见面上。

### R14 起重排（把"证据通道"提到几何调整之前）

- **R14 · 让悬停与"只存在于交互之后的状态"可被取证**（BACKLOG 24 + 26）：
  ① 给交互探针加一条真 `mouseEntered` / tracking-area 通路，让 `MotionFilmstripTests`
  能框住单个控件判"悬停药丸是否真的画出来"；② 帧夹具补两帧
  （`settings-privacy-excluded`、`settings-data-receipt`），让「移除」与回执行第一次进基线。
  **这一轮不改产品观感**，改完全 App 约 15 处 hover-only 位点从"源码已接"升级成"产物已量"。
- **R15 · 悬停药丸的几何**（BACKLOG 25，缺陷 5 的后续）：有了 R14 才谈得上调。
- **R16 · 详情交叉淡兑现**（缺陷 4）· **R17 · QuickPick 三处**（10）· **R18 · HotKeyRecorder 录制态**（12，
  先读 D-066 "刻意不加动效"的原文再判）· **R19 · 推荐权重页色/百分比**（13）·
  **R20 · banner 位移**（14）· **R21 · 搜索/空态清除钮**（15）· **R22 · 骨架扫光曲线兑现**（16）·
  **R23 · 菜单栏与状态图标语言**（17）· **R24 · 两条清空路径分叉**（18）·
  **R25 · 窗口位置与 chrome 跳位**（19、20）· **R26 · 缩略图与图片落地**（23、25、51）·
  **R27 · 视频控件**（52、54、55）· **R28 · symbolEffect 12/13 臂**（9、76）·
  **R29 · GlassPill 与材质过渡**（37、73）· **R30 · 覆盖复核与欠账清账**。
  之后每轮继续，直到连续 ≥2 轮七维 ≥90 才允许收口。

# AGENT_UI_AUDIT · 视觉与交互审计（ macOS / SwiftUI + AppKit）

状态：**未开始（方法已定，待执行）**。本文件随审计推进填充；最终报告只引用这里已验证的部分。

## 方法：为什么不用截屏

本机是 macOS 27 beta。截图类通道有两个已知坑（上一轮在别的项目里踩过）：
1. `screencapture` 在没有"屏幕录制"授权时返回全黑或报 `could not create image`，与页面是否真的绘制无关；
2. 浏览器/后台窗口的 `document.hidden` 会让动画时间线冻结，产生"看起来空白"的假帧。

因此这里的取证方式是**离屏渲染真实视图**：`NSHostingView(rootView:)` + `cacheDisplay(in:to:)` 把实际视图绘制进 `NSBitmapImageRep` 再存 PNG。它不需要任何系统授权，拿到的就是产品将要显示的那套视图树（含 AppKit 桥接的 `NSTextView`、`QLPreviewView`、`AVPlayerLayer` 等）。

实现形态：**测试 target 内的捕获套件**（`UICaptureTests`），由环境变量 `CLIPBOARD_HISTORY_UI_SHOTS=<输出目录>` 触发，未设置时 `XCTSkip`。
选择它而不是新增 executable target 的理由：不改 `Package.swift` 结构、不引入第二个产品构建产物，随时可整体删除（回滚成本≈0）。

## 覆盖清单（每张都要肉眼看过，暗/亮各一遍）

| 视图 | 状态变体 | 尺寸变体 | 已拍 | 结论 |
|---|---|---|---|---|
| `ContentView` | 空历史 / 有历史 / 搜索有结果 / 搜索无结果 / 收藏筛选 | 600×440（最小）750×560（默认）1100×800（放大） | ☐ | |
| `HistorySidebarView` | 单选 / 多选(批量条) / 拖拽选中间态 | 窄栏 250 / 宽栏 340 | ☐ | |
| `HistoryRow` | 文本 / 长文本 / 图片 / 单文件 / 多文件 / 收藏星标 | 行宽 250–340 | ☐ | |
| `DetailView` | 文本 / 图片 / 文件(图/文/视频/QuickLook/未知) / 多文件展开 | 600 / 1100 宽 | ☐ | |
| `GlassPill` / `GlassCircleButton` | 未收藏 / 已收藏 / hover | — | ☐ | |
| `SearchField` | 空 / 有文本 / hover | 400 与 180 窄 | ☐ | |
| `EmptyStateView` | 两个调用点的文案 | — | ☐ | |
| `SettingsView` | 快捷键 / 通用 / 隐私 / 推荐 / 数据 五个分类 | 640×440 最小 与 720×540 | ☐ | |
| `HotKeyRecorderView` | 常态 / 录制态（"请输入快捷键"） | 128×28 | ☐ | |
| `RecommendationWeightsView` | 默认 / 0% / 200% | — | ☐ | |
| `MenuBarRecommendationsView` | 无推荐 / 有推荐 + 理由行 | 菜单宽度自适应 | ☐ | |
| `MultiFileDetailView` | 折叠 / 展开（文本、图片、视频、文档） | 600 / 1100 | ☐ | |

## 量化检查（脚本化，不只靠眼睛）

1. **空白帧判定**：每帧算"量化颜色种数 + 亮像素占比"，`≤3 种且 <0.1%` 判为无效帧重拍（避免把"渲染通道问题"当成产品结论）。
2. **对比度**：对文本区域取前景/背景亮度，按 WCAG AA（正文 4.5:1、大字 3:1）算比值并记录；`foregroundStyle(.tertiary)` 在浅底上最可能不达标。
3. **截断与重叠**：检查是否有 `truncationMode` 生效但仍挤在一起的情况；`fixedSize` + `layoutPriority` 的文件名扩展名是否始终可见。
4. **暗/亮一致**：同一视图两遍渲染，比较关键元素是否存在且非隐形（`.clear` 前景色、只在高对比度下可见的描边等）。
5. **减少动态效果**：`NSWorkspace.shared.accessibilityDisplayShouldReduceMotion` 为 true 时，动画路径是否退化为无位移（代码级检查 + 快照）。

## 可访问性（代码级清单）

- 所有 `Image(systemName:)` 装饰性图标是否需要 `accessibilityHidden`；收藏星标当前用 `.foregroundStyle(.clear)` 表达"未收藏"，VoiceOver 读不到状态。
- `Button` 仅有图标时是否都有 `.help()`（现有 `GlassPill`/`bulkActionButtons` 有 help，但 help 不等于 accessibilityLabel）。
- 键盘焦点：主窗口是否可 Tab 到列表项、搜索框、`⌘,` 打开设置后的焦点归属；`HotKeyRecorderButton` 录制态失焦是否能退出（已有 `resignFirstResponder` 处理，需实机确认）。
- 搜索框右键被完全吞掉（`ChineseMenuTextField.rightMouseDown` 不调 super）——粘贴搜索词的路径是否受影响。

## 已发现的 UI 缺陷（待修，与 AGENT_BACKLOG.md 对应）

| ID | 现象（先在代码/静态层发现，视觉审计复验） | backlog |
|---|---|---|
| U-1 | 侧栏拖选的行位置表只增不减，过滤后可能命中已消失的行 | R-40 |
| U-2 | 视频宽高未知时画 16:9 空播放器而非错误态 | R-41 |
| U-3 | 详情整解大图；KVO observer 未释放 | R-42 |
| U-4 | 菜单/详情直接暴露正文与完整父目录 | R-43 |
| U-5 | 设置里"清空未收藏"在两个分类各出现一次（重复） | 待补 |
| U-6 | macOS 12 设置分栏宽度约束冗余（侧栏不可拖） | R-25 |

## 修复后的复验规则

每项修复必须：改动前拍一组 → 改动后同参数再拍一组 → 在下方"复验记录"里写清**哪两张对比、看到什么差别**。没有复验的项不得标"已完成"。

## 复验记录

（待填）

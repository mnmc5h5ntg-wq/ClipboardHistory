# 时间剪史 v1.2.1 架构审查

> 历史快照：本文记录 v1.2.1 时期的架构状态，包含当时的 `ClipboardManager` / `ClipboardReader` 等旧模块名称。当前 v1.3 工作区已经以 `HistoryStore`、`ClipboardIntake`、`MediaLoader`、`ClipboardWriter` 和 `ApplicationShell` 为核心；继续开发请优先参考 `docs/ARCHITECTURE_REFACTOR_2026_06_08.md`、`docs/SUBAGENT_CODE_REVIEW_2026_06_08.md` 和 `docs/REVIEW_FIX_PROGRESS_2026_06_08.md`。

## 1. 当前架构概览

项目主体是一个 Swift Package，可执行 target 位于 `ClipboardHistory/Sources/ClipboardHistoryApp`，最低支持 macOS 12，继续兼容 Intel 与 Apple Silicon。

当前源码已按职责拆分为四类目录：

```text
ClipboardHistory/Sources/ClipboardHistoryApp/
├── App.swift
├── Managers/
│   ├── AppDelegate.swift
│   ├── ClipboardManager.swift
│   ├── ClipboardReader.swift
│   ├── MenuBarController.swift
│   ├── WindowConfigurator.swift
│   └── WindowManager.swift
├── Models/
│   ├── ClipboardEntry.swift
│   ├── EntryContent.swift
│   └── StoredImage.swift
├── Utilities/
│   ├── ClipboardDateFormatters.swift
│   ├── FileTypeSupport.swift
│   └── LifecycleDebugLogger.swift
└── Views/
    ├── ContentView.swift
    ├── DetailPreviewViews.swift
    ├── DetailView.swift
    ├── EmptyStateView.swift
    ├── GlassControls.swift
    ├── HistoryRowViews.swift
    ├── HistorySidebarView.swift
    ├── ImagePreviewView.swift
    ├── SearchField.swift
    ├── ThumbnailView.swift
    └── ViewExtensions.swift
```

### 应用入口与生命周期

- `App.swift`：SwiftUI 入口、主窗口 Scene、菜单命令、macOS 13+ `MenuBarExtra`。
- `AppDelegate.swift`：AppKit 生命周期桥接，负责启动、激活、Dock 重新打开、退出清理。
- `WindowConfigurator.swift`：集中配置 `NSWindow`，包括透明标题栏、禁用原生全屏、关闭按钮隐藏应用。
- `WindowManager.swift`：集中处理主窗口查找、显示、恢复逻辑。
- `MenuBarController.swift`：macOS 12 `NSStatusItem` 菜单栏实现。

### 剪贴板业务层

- `ClipboardManager.swift`：管理历史记录、选中项、搜索状态和剪贴板轮询。
- `ClipboardReader.swift`：负责 `NSPasteboard` 解析、文件缩略图、图片与视频缩略图生成。
- `Models/`：保存剪贴板条目、内容类型与图片包装对象。

### UI 层

- `ContentView.swift`：只保留 macOS 13+ / macOS 12 的主导航容器分支。
- `HistorySidebarView.swift`：边栏搜索、标题、清空按钮、历史列表。
- `DetailView.swift`：详情区 header、文本/图片/文件内容分发、右下角操作按钮。
- `DetailPreviewViews.swift`：文件预览、QuickLook、文本文件预览和 fallback。
- `ImagePreviewView.swift`：统一详情区图片缩放预览布局。
- `ThumbnailView.swift`：统一边栏缩略图样式。
- `GlassControls.swift`：统一 glass 圆形/胶囊按钮。

## 2. 已完成整理

### 文件职责拆分

- 将 `ClipboardManager.swift` 中的模型拆到 `Models/`。
- 将剪贴板读取逻辑保留在 `ClipboardReader.swift`，避免状态管理和数据解析混在一起。
- 将主窗口查找、显示、恢复逻辑从 `MenuBarController.swift` 提取到 `WindowManager.swift`。
- 将 `ContentView.swift` 拆为 `HistorySidebarView.swift`、`DetailView.swift`、`EmptyStateView.swift`。
- 将图片预览布局提取到 `ImagePreviewView.swift`。
- 将边栏缩略图样式提取到 `ThumbnailView.swift`。

### 消灭重复代码

- 详情区图片预览与图片文件预览共用 `ImagePreviewView`。
- 图片缩略图和文件占位缩略图统一由 `ThumbnailView.swift` 提供。
- 日期格式化继续集中在 `ClipboardDateFormatters.swift`。
- 文件类型判断继续集中在 `FileTypeSupport.swift`。
- 主窗口显示与恢复逻辑集中到 `WindowManager.swift`。

### 死代码与无用代码清理

- 删除旧的 `CLIPBOARD_HISTORY_UI_EXPERIMENT`、`redDetail`、`testDetail` 调试分支。
- 删除发布版永远关闭的剪贴板 `dbg` / `initLog` 调试函数。
- 删除 `DetailImageView` 中未实际用于 UI 的 `containerSize` 状态。
- 删除 `HistoryRow` 未使用的 `selected` 参数。
- 移除 `MenuBarController` 不必要的 `ObservableObject` 声明。

### 当前文件规模

当前没有超过 300 行的 Swift 文件，最大文件为 `MenuBarController.swift`，约 150 行。核心大文件已被拆分到更小、更明确的模块中。

## 3. 发现的问题

### 性能风险

1. 缩略图生成仍可能在剪贴板读取路径中同步发生。
   - 图片文件缩放、视频首帧生成都可能造成瞬时主线程压力。
   - 当前没有改变行为，只记录为后续优化点。

2. 文件预览仍由 View 直接触发磁盘读取。
   - `DetailFileView` 会读取图片文件和文本文件。
   - 大文件预览可能造成短暂卡顿。

3. 历史记录目前存储在内存中。
   - 适合当前轻量版本。
   - 后续如提高历史上限，需要考虑持久化与缩略图缓存。

### 生命周期风险

1. macOS 12 的 Dock 重开、关闭窗口隐藏应用、菜单栏唤醒涉及多个 AppKit 入口。
   - 本轮已将窗口查找/显示提取到 `WindowManager`。
   - `AppDelegate`、`WindowConfigurator`、`MenuBarController` 仍共同参与生命周期，需要继续谨慎维护。

2. 原生全屏仍被禁用。
   - 这是为了规避 macOS 15 下全屏标题栏白条问题。
   - 不属于本轮架构整理范围。

### 发布风险

1. `make bundle` 生成的是 ad-hoc 签名本地测试包。
   - 适合本机和受控测试。
   - 对普通用户公开分发仍建议 Developer ID 签名与 Apple notarization。

2. 项目根目录仍存在历史报告文件和测试 DMG。
   - 本轮未修改发布产物。
   - 后续发布前建议统一检查根目录清洁度。

## 4. 后续建议

### P0：保持稳定

- 生命周期相关改动必须继续在 macOS 12 虚拟机和当前系统双测。
- 暂不恢复原生全屏，除非能稳定解决 macOS 15 顶部白条问题。
- 保持 `LifecycleDebugLogger` 默认关闭，只在 `CLIPBOARD_HISTORY_DEBUG=1` 时启用。

### P1：性能优化

- 将视频缩略图生成移到后台任务。
- 为图片、视频、文件缩略图增加轻量缓存。
- 避免 `DetailFileView` 在 View body 路径重复读取大文件。

### P2：模型与展示进一步解耦

- 将 `EntryContent.preview` 和 `EntryContent.sizeDescription` 提取为展示 formatter。
- 为 `ClipboardEntry` 增加更明确的 kind/payload/preview 语义层。

### P3：测试与发布工程

- 增加基础单元测试：搜索过滤、文件类型判断、文件名截断、Entry 去重。
- 明确区分本地测试包、GitHub Release 包和正式签名公证包。
- 发布前检查 `.dmg`、`.app`、历史文档是否符合仓库整理规则。

## 验证状态

本轮 v1.2.1 架构整理完成后需要保持：

- `swift build` 通过。
- `make bundle` 通过。
- macOS 12 / macOS 13+ 兼容分支不变。
- 不新增用户可见功能。
- 不修改现有 UI 和交互逻辑。

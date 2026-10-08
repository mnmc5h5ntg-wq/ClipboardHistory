# ClipboardHistory Handoff

最后更新：2026-06-14 12:00 +0800

## 1. 状态快照

- App「时间剪史」，GitHub `mnmc5h5ntg-wq/ClipboardHistory`
- 本地：v1.4.5，OCR/反馈/推荐/粘贴 均已完成
- 构建：`swift build` ✅，`swift test` ✅（实测 `Executed 224 tests, 1 skipped, 0 failures`；
  那个 skip 是离屏视觉捕获套件，只在设置 `CLIPBOARD_HISTORY_UI_SHOTS` 时才跑）；DMG：`时间剪史_v1.4.5.dmg`
- 五维度审查报告：`docs/CODE_REVIEW_v1.4.4.md`（安全/质量/Bug/并发/架构）—— 仓库里没有 v1.4.5 那份
- 已修复 8 项中高优先级审查问题（含隐私过滤开关可配置化）
- 工作区干净（`git status --short` 无输出）；提交都还没 push 到远端

## 2. 核心架构决策

### 2.1 粘贴机制

**结论**：`CGEvent.postToPid` 在 macOS 15 上对 Terminal/Finder/微信 等应用**无效**。最终方案：`Process` + `osascript` 执行 `keystroke "v" using command down`。

**流程**：`copyAndPasteHistoryEntry(id:)` → `copyAndPasteEntry(entry)` → 写剪贴板 → 0.1s 后激活前一个 App → 0.15s 后 osascript ⌘V。总延迟 ~0.25s。

**前置条件**：应用必须被授予**辅助功能权限**，且**不能从 `/tmp/` 运行**。macOS 拒绝给 `/tmp` 下的应用授权。必须从固定路径启动（项目目录 `.app` 或 `/Applications`）。

**调试方法**：`AXIsProcessTrusted()` 检查权限；AppleScript 错误码 1002 表示被拒绝。

### 2.2 OCR 图片文字搜索

**管线**：`.image` / `.file(url)` 双路径 → Vision OCR → `entry.ocrText` 持久化。OCR 仅跑一次，结果持久化到 `history.json`。启动后只扫描 `ocrText == nil` 的条目。

### 2.3 推荐反馈系统

| 功能 | 位置 |
|------|------|
| 隐私过滤器 | `RuleBasedRecommendationEngine.containsSensitiveContent()`（Slack/JWT/PEM/DB/Auth 全覆盖）|
| 隐私过滤开关 | 设置 → 隐私 → 推荐过滤 → 过滤敏感内容（默认开，关后敏感内容可进入推荐）|
| 「都不是我想要的」 | `MenuBarRecommendationsView` 蓝色按钮 → `AppCommand.dismissAllRecommendations` |
| 显露偏好追踪 | 推荐展示后 30s 窗口监听手动复制 |
| 反馈回流引擎 | `negativeFeedbackScore` 含 24h 衰减 |
| 频率×新鲜度混合排序 | `hybridFrequencyRecencyScore`：采纳次数/年龄^1.5 |
| 反馈数据导出 | 设置→推荐→JSONL 导出（已设 `0o600` 权限）|

> **已移除**：`copySequence`（死代码 — 序列模式识别未实现，审查中清理）

### 2.4 Finder 上下文（设置→隐私，默认关闭）

- Finder 当前目录：AppleScript → 同目录条目 +0.5
- Finder 选中文件扩展名：AppleScript → 同扩展名条目 +0.4

## 3. 当前文件结构

```
Sources/ClipboardHistoryApp/
├── App.swift                          # @main, WindowGroup + MenuBarExtra
├── Intelligence/
│   ├── ContextSnapshot.swift          # 上下文数据模型
│   ├── ContextEvent.swift             # 事件日志
│   ├── ContextPreferenceSettings.swift
│   ├── EntryIntelligence.swift
│   ├── ClipboardEntryIntelligenceAdapter.swift
│   ├── LocalRecommendationService.swift
│   ├── RecommendationModels.swift     # 推荐打分模型
│   ├── RecommendationWeights.swift    # 9因子权重
│   ├── RecommendationFeedbackStore.swift  # 反馈收集+导出
│   ├── RuleBasedRecommendationEngine.swift  # 规则推荐引擎（含隐私过滤）
│   ├── SystemContextCollector.swift   # 前台App/窗口/Finder/OCR
│   └── AIProviderModels.swift / AIPrivacyPolicy.swift
├── Managers/
│   ├── AppDelegate.swift              # 生命周期 + copyAndPasteHistoryEntry
│   ├── ApplicationShell.swift         # 命令路由 + paste 实现
│   ├── ClipboardIntake.swift          # 剪贴板读取（file-url > png > tiff > text）
│   ├── ClipboardWriter.swift          # 剪贴板写入
│   ├── ClipboardHistoryCommands.swift
│   ├── GlobalHotKeyController.swift
│   ├── HistoryPersistence.swift       # 持久化（含 ocrText）
│   ├── HistoryStore.swift             # 核心状态管理
│   ├── HotKeySettings.swift
│   ├── LoginItemSettings.swift
│   ├── MediaLoader.swift
│   ├── MenuBarController.swift        # NSStatusItem (macOS 12) + 菜单管理
│   ├── SettingsWindowController.swift
│   ├── WindowConfigurator.swift
│   └── WindowManager.swift
├── Models/
│   ├── AppCommand.swift               # 命令枚举（含 dismissAllRecommendations）
│   ├── ClipboardEntry.swift           # 条目模型（含 ocrText）
│   ├── EntryContent.swift             # 内容类型：text/image/file/files
│   ├── EntryPresentation.swift
│   ├── FilePreview.swift
│   ├── HistoryPrivacyCopy.swift
│   ├── HotKeyAction.swift / HotKeyShortcut.swift
│   └── StoredImage.swift
├── Utilities/
│   ├── ClipboardDateFormatters.swift
│   ├── FileTypeSupport.swift
│   ├── HotKeyPreferences.swift
│   └── LifecycleDebugLogger.swift     # CLIPBOARD_HISTORY_DEBUG=1 启用
└── Views/
    ├── ContentView.swift
    ├── DetailView.swift / DetailPreviewViews.swift
    ├── EmptyStateView.swift
    ├── GlassControls.swift
    ├── HistorySidebarView.swift / HistoryRowViews.swift
    ├── ImagePreviewView.swift / VideoPreview.swift
    ├── MenuBarRecommendationsView.swift  # macOS 13+ 菜单栏推荐
    ├── ChineseTextContextMenu.swift
    ├── SearchField.swift
    ├── SettingsView.swift              # 五栏设置：快捷键/通用/隐私/推荐/数据
    ├── HotKeyRecorderView.swift
    ├── RecommendationWeightsView.swift
    ├── ThumbnailView.swift
    └── ViewExtensions.swift
```

## 4. 关键避坑记录

| 坑 | 症状 | 根因 | 方案 |
|----|------|------|------|
| **粘贴不生效** | CGEvent.postToPid 无效果 | macOS 15 阻止，且 /tmp 下应用无 AX 权限 | Process+osascript，从非 /tmp 路径启动 |
| **Finder PNG 文件 OCR 失效** | 一般图片搜不到 | file-url 优先级最高 → 归类 .file → OCR 跳过 | scheduleOCRIfNeeded 新增 .file(url) case |
| **中文输入法搜索丢失** | 组字结束后文本未推送 | controlTextDidChange 在 markedRange 清除前触发 | controlTextDidEndEditing 兜底 |
| **NSStatusItem 透明** | macOS 12 菜单栏图标不可见 | 模板图像渲染问题 | 使用正确的 NSImage.isTemplate 设置 |
| **隐私过滤器不完整** | 缺 Slack/JWT/PEM 检测 | 仅检测 3 种模式 | 扩展到 9 种（xoxb/eyJ/PEM/数据库等） |
| **AppleScript 主线程阻塞** | 点击推荐卡顿 | CGWindowList+NSAppleScript 同步调用 | `skipAppleScript: true` 跳过高频路径 |
| **反馈导出无权限保护** | JSONL 可被其他用户读取 | 未设 POSIX 权限 | `0o700`/`0o600` + `guard let` 解包 |
| **非 Sendable 跨 Task.detached** | Swift 6 兼容风险 | `NSImage` 非 Sendable | `@unchecked Sendable` on `ClipboardEntry`/`StoredImage` |
| **togglePredictionSuggestions 重复块** | 每次切换触发两次刷新 | 重复 if/else | 删除重复块 |
| **`dir!` 强制解包** | 路径不可用时崩溃 | 可选链后 `!` | `guard let` 安全解包 |

## 5. 未来规划池

| 想法 | 价值 | 复杂度 |
|------|------|--------|
| 反馈时间衰减 | 高 | 低 |
| 推荐多样性约束 | 高 | 低 |
| 上下文相似度匹配 | 高 | 中 |
| 序列模式匹配接入引擎 | 高 | 中 |
| 冷启动引导 | 中 | 中 |
| 用户可标注 | 中 | 中 |
| 视频 OCR | 中 | 高 |
| 历史持久化优化（SQLite） | 中 | 中 |
| 缩略图缓存系统 | 中 | 中 |
| iCloud 同步 | 低 | 高 |

## 6. 已知未完成

- 提交已全部落在本地分支，未推送 GitHub
- 折叠按钮移除方案不优雅
- 窗口/浏览器域名采集时机需修复
- DMG 为 ad-hoc 签名，未 notarize
- 剪贴板内容明文存储（history.json + images/）— 高优先级加密待做
- 搜索框右键菜单未能彻底清除（field editor 层级复杂）
- HistoryStore 928 行 God Object 倾向 — 建议后续提取 PredictionCoordinator

## 7. 测试启动命令

从项目目录启动（有 AX 权限）：
```bash
osascript -e 'quit app "时间剪史"' 2>/dev/null; sleep 1
open -n /Users/wangziyi/Documents/Codex_Project0/时间剪史.app
```
## macOS 12 兼容性审查 (2026-06-12)

### 发现并修复
- **SettingsView HSplitView**: 原代码在 `#available(macOS 13,*)` 的 else 分支使用 `HSplitView`（macOS 14+ API），macOS 12 运⾏时会崩溃。已替换为 `CompatibleSplitView`——基于 `NSSplitView` + `NSViewRepresentable` 的自定义组件。
- **Finder 选中文件 开关**: 重建 SettingsView 时曾遗漏该隐私开关，已补充。

### 验证状态
- `swift build` ✅
- `swift build --triple arm64-apple-macosx12.0` ✅
- `swift test` ✅ 224 执行 / 1 按设计 skip / 0 失败
- `make bundle` ✅ (Universal Binary, ad-hoc signed)
- 所有 11 处 `#available`/`@available` 守卫均有正确的退化路径

### 已知 macOS 12 差异（设计如此，非缺陷）
| 功能 | macOS 12 | macOS 13+ |
|------|----------|-----------|
| 主窗口 | NavigationView | NavigationSplitView |
| 菜单栏图标 | NSStatusItem + 程序化模板图标 | MenuBarExtra + SF Symbol |
| 设置分栏 | CompatibleSplitView (NSSplitView) | NavigationSplitView |
| 动画 | .interactiveSpring（参数对齐） | .snappy |
| 窗口背景 | .background(.thickMaterial) | .containerBackground |
| 登录项 | AppleScript → System Events | SMAppService |

### macOS 12 体验对齐 (2026-06-12)

已消除之前存在的 macOS 12/13+ 体验差异：

| 差异 | 之前 | 现在 |
|------|------|------|
| 登录项 | "系统不支持" | AppleScript → System Events，功能完整 |
| 菜单栏图标 | 手绘线条图标 | SF Symbol `clipboard`，与 MenuBarExtra 一致 |
| 设置分割条 | 粗分割线 | `.thin` 风格，贴近 NavigationSplitView |
| 动画 | `.interactiveSpring` | 参数已调至接近 `.snappy`（response=0.22, damping=0.88） |

剩余微小差异仅限系统 API 无法回退的更深层机制（NavigationView vs NavigationSplitView 底层实现不同），视觉和功能体验已经高度一致。

## 8. 当前阻塞问题

### 8.1 macOS 12 红色关闭按钮后无法恢复窗口

**现象**：仅 macOS 12 上出现。Cmd+H 正常，红色按钮后 Dock/快捷键/菜单都无法唤回窗口。macOS 15+ 无此问题。

**已尝试**：
- `NSApp.hide(nil)` 直接调用 ← 不行
- `sender.orderOut(nil)` ← 不行  
- `DispatchQueue.main.async { NSApp.hide(nil) }`延迟执行 ← 不行
- 弱引用直接窗口恢复 ← 不行

**当前状态**：已加入详细诊断日志（WindowConfigurator.windowShouldClose / windowWillClose + WindowManager.showMainWindow）。LifecycleDebugLogger **默认关闭**，只有设 `CLIPBOARD_HISTORY_DEBUG=1` 才写，且写在 `~/Library/Logs/时间剪史/`（目录 0700、文件 0600）—— 早先「临时默认开启 + 写 /tmp」那一版已经改掉。

**下一步**：在 macOS 12 虚拟机上测试，抓取 `/tmp/时间剪史_lifecycle_debug.log`，分析 `windowShouldClose` 返回 false 后系统是否仍然销毁了窗口。

### 8.2 状态恢复崩溃（已修复）
macOS 12 上 `NSPersistentUIRequiresSecureCoding` crash → AppDelegate 新增 `applicationSupportsSecureRestorableState` 返回 false + 清除 `.savedState`。

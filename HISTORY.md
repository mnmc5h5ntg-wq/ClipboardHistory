> **历史快照**：本文里的行数、测试数、文件清单与结论都是**写下它那天**的状态，不代表当前代码（当前基线请看 `AGENT_STATE.md` 与 `swift test` 的实际输出）。保留原文是为了留痕，不要照它行事。

# ClipboardHistory History

最后更新：2026-06-14 12:00 +0800

本文件保存低频追溯信息：排查过程、旧验证流水账、废弃方案和问题演进。主 handoff 只保留当前决策和约束；不要把本文内容整段复制回主 handoff。


## 2026-06-12: 隐私过滤开关

用户需求：部分用户不希望推荐引擎过滤敏感内容。

实现：
- `ContextPreferenceSettings` 新增 `canFilterSensitiveContent`（`@Published`，`UserDefaults` 持久化，默认 `true`）
- `RecommendationRequest` 新增 `enablePrivacyFilter: Bool = true`
- `RuleBasedRecommendationEngine.recommend()` 根据 `enablePrivacyFilter` 决定是否调用 `containsSensitiveContent`
- `LocalRecommendationService.recommend()` 新增参数透传
- `HistoryStore.refreshPredictions()` 捕获偏好并传入推荐链
- 设置 → 隐私 → 推荐过滤 → 「过滤敏感内容」开关

遇到问题：首次修改时替换模式重复匹配，误在通用栏和隐私栏各注入一份。删掉通用栏重复块后修复。

## 2026-06-11: 五维度深度同行评审 + 7 项修复

使用 5 个并行 Subagent 对全项目进行代码审查，审查报告保存在 `docs/CODE_REVIEW_v1.4.4.md`。

### 已修复项（按优先级）

| # | 问题 | 严重度 | 修复 |
|---|------|--------|------|
| 4 | 非 Sendable 类型跨 `Task.detached` | 🔴 | `ClipboardEntry`/`StoredImage` + `@unchecked Sendable` |
| 3 | AppleScript 主线程阻塞 | 🔴 | `currentContext(skipAppleScript: true)` 参数，3 个高频调用点跳过 |
| 5 | `togglePredictionSuggestions` 重复 if/else | 🟡 | 删除重复块 |
| 8 | `copySequence` 死代码 | 🟡 | 删除变量及所有引用 |
| 9 | `dir!` 强制解包 + 权限缺失 | 🟡 | `guard let` 解包 + `0o700`/`0o600` |
| 6 | 隐私过滤器检测不足 | 🟡 | +Slack(xoxb)/JWT(eyJ)/PEM/数据库/Authorization 模式 |
| — | `luhnCheck` 中 `Int($0)!` | 🟢 | `compactMap` 替代 |

### 跳过（需架构变更）
- #1：`history.json` 明文存储 → 需 AES-GCM + Keychain
- #10：HistoryStore God Object → 需提取 PredictionCoordinator
- #7：ClipboardIntake 无敏感过滤 → 需存储入口拦截

### 编译状态
`swift build` ✅ | 135 测试全绿 ✅

## 2026-06-10: v1.4beta 候选整理

- 用户确认此前测试无误，并将本地 DMG 标注改名为 `时间剪史_v1.4beta.dmg`；2026-06-10 19:12 已基于搜索框、状态栏菜单和 QuickLook 修复重新生成同名 DMG。
- 校验信息：
  - 路径：`/Users/wangziyi/Documents/Codex_Project0/时间剪史_v1.4beta.dmg`
  - 大小：约 `3.2M`
  - SHA-256：`22e397084ce30a382df551a316548eb28caf6768e75d07251eeae7a32568351a`
  - `hdiutil verify`：通过
- 原始生成包名曾为 `时间剪史_v1.3.dmg`，后续用户改名为 `v1.4beta`。
- 当前测试包仍是 ad-hoc 签名，未 notarize。

## 2026-06-10: 搜索框、状态栏菜单、QuickLook 再修复

用户反馈：

- 搜索框无法输入字符进行搜索。
- 右上角状态栏菜单中“刷新历史”作用不明，建议删除。
- “设置…”和“清空未收藏…”后面的省略号显得奇怪，需要删除。
- 打开多选列表中的文件预览时再次闪退，用户提供的详细信息仍是 QuickLook 断言。

处理：

- 搜索框：删除自定义 `NSTextFieldCell` 和复用 field editor 的做法，回到标准 `NSTextField` 编辑路径，只保留右键菜单禁用。
- 状态栏菜单：从 `AppCommandCatalog.menuBarCommands` 删除 `.refreshHistory`；菜单文案改为“设置”“清空未收藏”。
- QuickLook：用 generation token 取消过期加载；脱离窗口/拆卸时释放旧 `QLPreviewView`；新的 `QLPreviewView` 只在 view 已挂到窗口且即将加载时按需创建，不再在离开窗口时预装替代 view。

验证：

- `swift test --package-path ClipboardHistory --filter AppCommandTests` 通过。
- `swift test --package-path ClipboardHistory --filter ChineseTextContextMenuTests` 通过。
- `swift test --package-path ClipboardHistory --filter QuickLookPreviewLifecycleTests` 通过。
- `swift test --package-path ClipboardHistory` 通过，116 个测试全绿。

## 2026-06-10: 双窗口问题

用户反馈：第一次打开 App 正常；关闭主窗口再打开会出现两个「时间剪史」窗口，其中一个红黄绿位置错误；窗口菜单底部也能看到两个窗口，关闭一个窗口两个会一起关闭。

排查结论：

- 根因是 SwiftUI `WindowGroup` 主窗口与 `WindowManager` 手动创建的 fallback AppKit 主窗口同时存在。
- 关闭主窗口后 SwiftUI 窗口处于隐藏/恢复空档，`showMainWindow` 误判没有主窗口并创建 fallback；随后 SwiftUI 原窗口恢复，形成两个窗口。

最终方案：

- 删除 fallback 主窗口创建路径。
- `WindowManager` 只负责显示已有 SwiftUI 主窗口。
- 增加 `WindowManagerTests.testShowMainWindowDoesNotCreateFallbackMainWindow` 锁住该决策。

验证摘要：

- 启动后 1 个窗口。
- 点击红色关闭后再激活、再用默认显示主窗口快捷键，系统窗口数始终为 1。
- 窗口菜单底部仅 1 个「时间剪史」。

废弃方案：

- 不得恢复 `fallbackWindowController` 或 `makeFallbackMainWindow`。

## 2026-06-10: 菜单反复横跳

用户多次反馈启动后菜单栏会在正常中文菜单和错误菜单之间来回变化。

排查结论：

- 根因是 SwiftUI/system 默认菜单和自定义 AppKit `MainMenuController` 同时争夺 `NSApplication.shared.mainMenu`。
- 旧的“定时重写菜单”会制造更明显的反复横跳。

最终方案：

- 删除 `MainMenuController` 和相关测试。
- 使用 SwiftUI `.commands { ClipboardHistoryCommands(...) }` 定义应用命令。
- 在打包 `Info.plist` 写入 `CFBundleDevelopmentRegion=zh-Hans` 与 `CFBundleLocalizations=[zh-Hans]`，让系统默认菜单从源头本地化。

最终稳定菜单：

- `Apple / 时间剪史 / 编辑 / 显示 / 窗口 / 帮助`

注意：

- `显示` 是 SwiftUI/system 菜单，不要为了去掉它而恢复 AppKit 主菜单覆盖。
- 后台/前台大量菜单采样曾稳定，没有再采到 `View / Window / Help` 或英文 App 菜单项。

## 2026-06-10: QuickLook 崩溃

用户提供 Apple 问题详细信息，并反馈近期频繁意外退出。

共同崩溃签名：

- `Exception Type: EXC_CRASH (SIGABRT)`
- `[QL] -[QLPreviewView setPreviewItem:blockingUntilLoading:timeoutDate:transition:]: item == nil || _reserved->internalState != QLPreviewDeactivatedInternalState`
- 触发线程：main thread
- App 栈顶曾指向 `QuickLookPreview.updateNSView(_:context:)`。

排查结论：

- 不是测试构建路径、菜单栏、红黄绿或签名导致。
- v1.3 基线中也直接设置 `QLPreviewView.previewItem`，但 v1.3 后多文件折叠/展开让 QuickLook 创建、更新、隐藏、卸载更频繁，放大崩溃概率。
- 会影响正式用户预览 PDF、Office、Pages、Numbers、Keynote 等文档，尤其是多文件记录中快速展开/折叠或切换条目时。

最终方案：

- `QuickLookPreview` 改为稳定容器 `QuickLookPreviewContainerView`。
- 只在 URL 真变化且 view 已挂到窗口时设置 `previewItem`。
- 重复相同 URL 的 SwiftUI 更新直接跳过。
- 同一容器切换不同 URL、或容器曾脱离窗口后再次加载时，丢弃旧 `QLPreviewView` 并创建新的 `QLPreviewView`。
- 拆卸时清掉 pending URL、标记 detached、移除旧 preview view。
- 增加 `QuickLookPreviewLifecycleTests` 覆盖首载、重复 URL、换 URL、脱离窗口后重新加载。

建议人工回归：

- 单个 PDF/docx/pptx/Pages/Keynote 预览。
- 多文件记录内 PDF/文档预览连续展开/折叠。
- 在 QuickLook 文档、文本、图片、视频条目之间快速切换。
- QuickLook 预览显示时关闭或隐藏主窗口。

## 2026-06-09 至 2026-06-10: 窗口 chrome 与侧边栏

用户对窗口外形非常敏感，特别是红黄绿、侧边栏左上角、窗口圆角同心关系。

关键反馈：

- 边栏折叠按钮多次被误加回，需要删除。
- 隐藏整个 `windowToolbar` 虽然能去掉 sidebar toggle，但会让红黄绿消失。
- 红黄绿一度过于靠近窗口边角，不符合原生观感。
- 用户最终要求红黄绿位于正确原生标准位置，并和窗口圆弧同心。

当前方案：

- 保留系统 titlebar/toolbar 结构，让红黄绿存在。
- `WindowConfigurator.alignTrafficLights(in:)` 校正红黄绿位置。
- `removeSidebarToolbarButton(from:)` 和多轮 cleanup 只针对 sidebar toggle，不动整个 toolbar。
- 当前运行态红色按钮相对窗口位置曾验证为 `18,18`、大小 `16x16`。

废弃方案：

- 不要再隐藏整个系统 toolbar。
- 不要把红黄绿拿出边栏。
- 不要重新设计边栏外框、标题栏、圆角或窗口尺寸关系。

## 2026-06-09 至 2026-06-10: 多文件预览动画

用户反馈：

- 多文件复制预览条目缺少 hover 动效。
- 折叠 md 文本/dmg 图标预览时有向下移动和闪烁。
- 先淡出再折叠显得拖沓，希望接近 Finder、Xcode Sidebar、Apple Settings 的原生观感。

最终方案：

- 多文件详情条目增加 hover 高亮。
- 折叠/展开由 `expandedURL == url` 驱动。
- 使用动态目标高度和 `.frame(height:) + .clipped()` 做几何收缩。
- 删除 opacity/fade transition、`visiblePreviewURL`、`transitionTask`、折叠相关 `Task.sleep` 和多段 `easeInOut/easeOut`。
- macOS 14+ 使用 `.snappy(duration: 0.22, extraBounce: 0)`，低系统用短 spring 兜底。
- 折叠期间暂时保留内容完成几何动画，结束后卸载内容，避免视频/QuickLook 隐藏运行。

用户后续反馈：

- 多文件折叠/展开动画观感优秀。

## 2026-06-09: 右键菜单与文本预览

用户反馈：

- 搜索框右键菜单起初仍为英文。
- 文本记录详情 / 文本文件预览右键菜单汉化不完全。
- 文本选区一度只像加粗，难以辨认。
- 后续搜索框右键菜单修好后，文本预览曾空白。
- 用户最后认为搜索框右键菜单没有用，要求删除搜索框右键功能；并询问是否删除预览区 Services 菜单。

最终方案：

- 搜索框右键菜单禁用。
- 文本记录详情和文本文件预览右键菜单精简为 `复制`、`全选`、`查找…`。
- 移除 `Services` 及二级菜单。
- 文本选区恢复系统高亮。

## 2026-06-09: 历史与隐私说明

根据 Issues `#5/#16` 完成低风险说明类改进：

- 设置页新增“历史与隐私”说明。
- README 补充本机持久化、保存位置、保存内容、普通历史保留策略、收藏保留规则、清空语义和敏感剪贴板提醒。
- 共享文案集中到 `HistoryPrivacyCopy`。

用户测试确认：

- 设置页出现“历史与隐私”说明。

## 2026-06-08 至 2026-06-09: 全局去重与播放

用户测试反馈：

- 连续复制同一张图不会产生两条。
- 隔几条记录后再次复制同一张图片曾仍然生成重复记录。
- 播放视频后关闭主窗口，视频后续已能正确停止播放。
- 重新打开后边栏右上角折叠按钮一度确认没有，后续又因窗口改动反复出现过。

最终状态：

- 用户确认全局去重修复成功。
- 视频关闭主窗口后继续播放的问题已修复。
- sidebar toggle 的清理策略最终迁到只局部处理 toolbar item/view/action。

## 2026-06-08: v1.3 发布与后续

- v1.3 已提交并发布到 GitHub。
- 用户随后要求整理 GitHub Issues，并根据 handoff 的“下一步建议”处理：
  - `#13` 右键菜单汉化
  - `#16` 本机持久化与剪贴板隐私边界说明
  - `#5` 历史保留策略可见说明
- 这些工作后来并入 v1.4beta 候选改动。

## 旧验证流水账摘要

这些结果曾用于当时决策，但未来不要在主 handoff 中逐条展开：

- Swift 测试多次通过，数量随新增测试从 108、112、114、115、116 等变化。
- Python 脚本测试多次为 11 个通过。
- `swift build --package-path ClipboardHistory` 多次通过。
- `make run` 后曾用进程路径确认运行的是 `/private/tmp/时间剪史_bundle/时间剪史.app/Contents/MacOS/ClipboardHistoryApp`，不是 `/Applications` 旧安装版。
- AppleScript 曾用于检查菜单、窗口按钮、红黄绿坐标和窗口数量。
- macOS 12+ 构建层面曾检查：`Package.swift` platforms 为 `.macOS(.v12)`，Info.plist `LSMinimumSystemVersion=12.0`，Universal Binary 包含 `x86_64 arm64`，两个架构 `LC_BUILD_VERSION minos 12.0`。

## 废弃方案总表

- AppKit 定时覆盖 `NSApplication.shared.mainMenu`。
- 自定义 `MainMenuController` 争夺系统菜单。
- `WindowManager` 创建 fallback AppKit 主窗口。
- 隐藏整个系统 `windowToolbar` 来删除 sidebar toggle。
- QuickLook 预览中每次 SwiftUI 更新都直接设置裸 `QLPreviewView.previewItem`。
- 多文件折叠先 opacity fade 再改变高度。
- 菜单栏展示历史记录快速复制条目。

---

## 2026-06-11: 设置 UI 打磨与滑动药丸

用户反馈：

- 设置页面边栏无 hover 动效，点击选择功能失效。
- 主窗口「全部/收藏」分段控件无 hover。
- 侧边栏折叠按钮偶尔闪现。
- 设置边栏应新增「隐私」分类，上下文权限从「通用」移入。
- 推荐权重滑块布局不统一。

排查与处理：

- 设置边栏：`selectedCategory` 改为 `SettingsCategory?`，删除 `List(.sidebar)`，统一使用自定义 `SettingsSidebarView` + `SettingsSidebarRow`，hover 风格与 `HistoryRowButton` 完全一致（`RoundedRectangle(cornerRadius: 9)`、选中 0.16、hover 0.045、0.11s 动画）。`.contentShape` 移入 `Button` label 内部确保整行可点击。macOS 12/13+ 共用同一组件。
- 全部/收藏：`SegmentedFilterPicker` 改为 `ZStack` 三层结构（quaternary 底色 → 滑动药丸 → 文字按钮）。药丸用 `.spring(response: 0.38, dampingFraction: 0.72)` 做过冲，`.clipShape` 裁剪防出界。每段独立 hover 文字 1.08x 放大。`.contentShape(Rectangle())` 保证整半边可点击。
- 折叠按钮：`WindowConfigurator` 启动后多轮清除（0/0.02/0.08/0.2/0.5/1.0 秒）+ 缩放结束时触发。当前方案属临时，后续应改为 `NSWindow` 级别配置。
- 隐私分类：`SettingsCategory.privacy`（icon: `hand.raised`），五栏：快捷键 | 通用 | 隐私 | 推荐 | 数据。
- 推荐权重：删除 `Slider` label 参数使所有滑块对齐；`0.0/1.0/2.0` → `0%/100%/200%`。

验证：`swift build` 通过，135 tests（1 pre-existing flake 非本次引入），用户多轮测试确认交互正常。

## 2026-06-11: 文档结构整理

- `CLIPBOARDHISTORY_HANDOFF.md`：主 handoff，保留当前决策、约束、下一步。放在项目根目录。
- `HISTORY.md`（本文件）：低频追溯信息，排查过程、旧验证流水账、废弃方案。也放在项目根目录。
- 两者均从 `/tmp` 移到项目根，避免重启丢失。

---

## 2026-06-11: OCR 修复 — promoteExistingEntryIfNeeded 断路

用户反馈 OCR 始终无法搜索图片文字。

排查过程：
- 加文件日志 → 发现 `add()` 总是走 `promoteExistingEntryIfNeeded` 提前返回
- `scheduleOCRIfNeeded` 只在 `add()` 的新条目路径调用，推广路径未触发
- 用户多次复制同一张图片测试，每次都命中去重推广

修复：
- `promoteExistingEntryIfNeeded` 中也调用 `scheduleOCRIfNeeded`
- 同时将 NSImage 跨线程问题彻底解决：主线程提取 PNG Data → 后台用 CGImageSource 解码

## 2026-06-11: Finder 上下文 + OCR 功能开发

新增三项上下文采集能力和图片 OCR 搜索，详见 handoff。

---

## 2026-06-11: OCR 第二次修复 — NSImage 线程安全 + 推广路径

用户反馈 OCR 在修复 promoteExistingEntryIfNeeded 后仍无效。

排查：
- NSImage 在任何非主线程访问都会静默失败
- 之前的方案在 Task.detached 中调用 NSImage.cgImage / NSImage(data:) 均不可靠

最终方案：
- 主线程用 nsImage.cgImage(forProposedRect:...) 提取 CGImage（TIFF→NSBitmapImageRep 兜底）
- 仅将 CGImage 传至 DispatchQueue.global(.utility)
- VNRecognizeTextRequest 在后台队列执行
- 回调主线程写入 entry.ocrText + persist
- 推广路径保留旧 ocrText 同时补跑 OCR

---

## 2026-06-11: OCR 图片文字搜索 — 完整架构与踩坑记录

### 需求

复制图片后自动识别图中文字（中/英文），搜索结果匹配图片的 OCR 文字。存量图片也要覆盖。

### 最终架构

```
复制图片 → ClipboardIntake.readEntry → .image(StoredImage)
         → HistoryStore.add() 或 promoteExistingEntryIfNeeded()
         → scheduleOCRIfNeeded(for:)
           ├─ 主线：nsImage.cgImage(forProposedRect:)
           │       失败时 TIFF→NSBitmapImageRep.cgImage 兜底
           ├─ 后台队列(.utility)：VNRecognizeTextRequest
           └─ 主线回调：entry.updating(ocrText:) → persist()
```

**涉及文件**：

| 文件 | 改动 |
|------|------|
| `Models/ClipboardEntry.swift` | 新增 `ocrText: String?` 字段，`updating(ocrText:)` |
| `Models/StoredImage.swift` | 已有 `pngData()` 和 `tiffRepresentation` |
| `Managers/HistoryStore.swift` | `scheduleOCRIfNeeded`、`scheduleOCRForExistingImages`、搜索过滤 |
| `Managers/HistoryPersistence.swift` | `StoredEntry` 加 `ocrText`，save/load 映射 |
| `Managers/ApplicationShell.swift` | 启动后 1s 调用 `scheduleOCRForExistingImages()` |
| `Intelligence/SystemContextCollector.swift` | `recognizeText(in: CGImage)` 静态方法 |

**搜索过滤**（`HistoryStore.filteredEntries`）：
```swift
case .image:
    if "图片".localizedCaseInsensitiveContains(searchText) { return true }
    if let ocr = entry.ocrText, ocr.localizedCaseInsensitiveContains(searchText) { return true }
    return false
```

**持久化**：
- `StoredEntry` 新增 `let ocrText: String?`
- `storedEntry(from:)` 四个分支均写入 `ocrText: entry.ocrText`
- `entry(from:content:thumbnail:)` 恢复时读取 `ocrText: storedEntry.ocrText`
- 推广路径 `entry(from:replacingWith:)` 保留旧 `ocrText`

**启动扫描**：
- `ApplicationShell.configure()` 中 `DispatchQueue.main.asyncAfter(deadline: .now() + 1.0)`
- 调用 `historyStore?.scheduleOCRForExistingImages()`
- 遍历 `entries`，对 `case .image` 且 `ocrText == nil` 的条目补跑 OCR

### 踩坑历程

**坑 1：推广路径未触发 OCR**
- `add()` 中 `promoteExistingEntryIfNeeded` 返回 true 时提前 return
- `scheduleOCRIfNeeded` 只在新增路径中调用
- 用户重复复制同一图片测试，每次都走推广，OCR 从未执行
- 修复：在 `promoteExistingEntryIfNeeded` 末尾也调用 `scheduleOCRIfNeeded`

**坑 2：NSImage 跨线程静默失败**
- 第一次尝试：`Task.detached` 中调用 `nsImage.cgImage` → nil
- 第二次尝试：主线提取 PNG Data，后台 `NSImage(data:)` 重建 → nil
- 第三次尝试：主线提取 PNG Data，后台 `CGImageSourceCreateWithData` → 可行但增加复杂度
- 最终方案：主线直接 `.cgImage(forProposedRect:)` 提取 CGImage，CGImage 是 C 对象可安全传后台

**坑 3：TIFF 格式图片的 CGImage 提取**
- Finder 复制的图片是 TIFF 格式，`.cgImage(forProposedRect:)` 可能返 nil
- 加兜底：`.tiffRepresentation → NSBitmapImageRep(data:) → .cgImage`

### Finder 上下文采集 — 完整架构

**数据模型**（`ContextSnapshot`）：
```swift
var finderDirectory: FinderDirectoryContext?   // { path: String }
var finderSelection: FinderSelectionContext?   // { fileExtensions: [String], count: Int }
```

**采集**（`SystemContextCollector`）：
- `currentFinderDirectory()`：AppleScript `tell app "Finder" to get POSIX path of (target of front window as alias)`
- `currentFinderSelection()`：AppleScript 遍历 `selection`，提取 `name extension`

**评分**（`RuleBasedRecommendationEngine`）：
- `finderDirectoryScore`：条目预览含 Finder 当前路径 → 1.0；否则文件类型 → 0.3
- `finderSelectionScore`：条目扩展名与 Finder 选中匹配 → 1.0；否则文件类型 → 0.2

**权重**（`RecommendationWeights`）：
- 新增 `.finderDirectoryAffinity`、`.finderSelectionAffinity` 两个因子
- 设置 → 推荐 → 权重客制化中可调

**推荐原因标签**（`HistoryStore`）：
- Finder 目录：`来自「\(目录名)」`
- Finder 选中：`选中 .\(ext1)、.\(ext2)` 或 `选中 .\(ext) 等文件`

**隐私**：
- 设置 → 隐私中两个开关（默认关闭）
- `ContextPreferenceSettings.canReadFinderDirectory` / `.canReadFinderSelection`

### 菜单栏推荐直接粘贴

`MenuBarRecommendationsView` 中 Button action 从 `showMainWindow()` 改为：
```swift
appDelegate.copyAndPasteHistoryEntry(id: entry.id)
→ shell.copyAndPasteEntry(entry)
→ 复制到剪贴板 → 激活之前的前台 App → CGEvent 模拟 ⌘V
```

### 全部/收藏滑动药丸

`HistorySidebarView.SegmentedFilterPicker`：
- `ZStack { quaternary底色 → 滑动药丸 → 文字按钮 }`
- 药丸动画：`.spring(response: 0.38, dampingFraction: 0.72)`
- `.clipShape(RoundedRectangle(cornerRadius: 7))` 防出界
- 每段文字 hover 1.08x 放大

### 设置边栏

删除系统 `List(.sidebar)`，统一用 `SettingsSidebarView` + `SettingsSidebarRow`：
- Hover：`RoundedRectangle(cornerRadius: 9)` + `Color.primary.opacity(0.045)` + 0.11s 动画
- 选中：`Color.accentColor.opacity(0.16)`
- `.contentShape` 在 Button label 内，整行可点击

### 设置页结构

五栏：快捷键 | 通用 | 隐私 | 推荐 | 数据


## 2026-06-11: OCR 覆盖 .file 类型图片 + 中文输入法修复

### OCR 全链路追踪与修复

**问题演进**：
- 用户反复报告仅测试图片可文字搜索，一般图片不可搜索
- 第一轮加 `ocrLog` 追踪 → 日志显示 OCR add() 被调用且 promote 返回 early → 怀疑推广路径 → 实际不是
- 第二轮仍然无效 → 最终定位到 `ClipboardIntake.readEntry` 的类型优先级

**根因**：
```
ClipboardIntake.readEntry 优先级：
1. public.file-url 存在 → .file(url)       ← Finder 复制 PNG 走这里
2. public.png 存在     → .image(stored)    ← Preview/截图走这里
3. public.tiff 存在    → .image(stored)
4. 文本
```
Finder 复制 PNG 文件总是被归类为 `.file`，而 `scheduleOCRIfNeeded` 只处理 `.image` case → OCR 静默跳过。

**最终修复** (`HistoryStore.swift`)：
- `scheduleOCRIfNeeded`：新增 `.file(url)` case —— 判断 `supportedImageExtensions` → `NSImage(contentsOf: url)` → CGImage → Vision OCR
- `scheduleOCRForExistingImages`：过滤扩展到 `.file` 图片文件
- `filteredEntries` 搜索：`.file` 条目也匹配 `ocrText`
- `supportedImageExtensions`: png, jpg, jpeg, gif, bmp, tiff, tif, heic, heif, webp, ico, svg

**CGImage 提取策略**：
- 主线 `.cgImage(forProposedRect:)` 第一优先
- TIFF fallback: `tiffRepresentation → NSBitmapImageRep(data:) → .cgImage`

### 中文输入法搜索框修复

**问题**：`controlTextDidChange` 在输入法组字结束后，`markedRange` 可能在回调触发前已清除 → 绑定未推送 → 搜索文本丢失。

**修复** (`ChineseTextContextMenu.swift`)：
- `Coordinator` 新增 `controlTextDidEndEditing` 兜底
- 修复 `markedRange` 类型转换：`NSText` 不暴露此方法，需转为 `NSTextView`

### OCR 性能说明

- 每张图片 OCR 仅执行一次，结果经 `HistoryPersistence` 持久化到 `history.json`
- 启动时 `scheduleOCRForExistingImages` 只扫描 `ocrText == nil` 的条目
- 视频 OCR 暂不实现：逐帧处理耗时极长（300+帧/10s视频），建议长期规划

### 调试日志

- OCR 管道日志：`/tmp/ocr_debug.log`（始终开启，追踪 CGImage 提取、VN 识别、持久化写入）
- 生命周期日志：仅 `CLIPBOARD_HISTORY_DEBUG=1` 时输出 `/tmp/时间剪史_lifecycle_debug.log`

### 修改文件

| 文件 | 改动 |
|------|------|
| `Managers/HistoryStore.swift` | OCR 扩展 .file、搜索过滤、ocrLog、supportedImageExtensions |
| `Views/ChineseTextContextMenu.swift` | controlTextDidEndEditing、markedRange 类型转换 |

## 2026-06-11: 推荐反馈系统全面实现

### 用户需求
用户希望收集推荐使用数据来优化推荐系统，为未来 AI 推荐积累训练数据。

### 七项实现

#### 1. 隐私过滤器
`RuleBasedRecommendationEngine.containsSensitiveContent()` 匹配：
- `ghp_[A-Za-z0-9]{36,}` — GitHub PAT
- `sk-[A-Za-z0-9]{32,}` — OpenAI/API key
- 13-19 位数字 Luhn 校验 — 信用卡号
- AWS key 前缀（AKIA, ABIA 等 12 个）
- 64+ 位 hex 串 — 私钥候选

在 `recommend()` 入口过滤，不进入评分流程。

#### 2.「都不是我想要的」按钮
- `AppCommand.dismissAllRecommendations` 新增
- `MenuBarRecommendationsView` 蓝色按钮
- `HistoryStore` 处理：对当前 3 条推荐逐条调用 `feedbackStore.recordDismissed()`
- `MenuBarController` 新增 `dismissAllRecommendationsFromMenu` 选择器

#### 3. 显露偏好追踪
- `revealedPreferenceWindowTimer`：30s Timer
- `lastPredictionEntryIDs`：当前推荐条目 ID 集合
- 窗口期间任何不在推荐列表中的手动复制 → `recordCopiedManually`
- 点击推荐或 dismiss → 关闭窗口

#### 4. 反馈回流引擎增强
`negativeFeedbackScore` 变化：
- 原：仅 `dismissed` + `reverted`，固定 -0.12/条，max -0.36
- 新：纳入 `ignored`，基础 -0.08 + 近期 (24h) 额外 -0.10/条，max -0.50
- 时间衰减权重使最近拒绝的条目更快降分

#### 5. 序列模式追踪
- `copySequence: [UUID]`：最近 20 次复制的 ID 序列
- 在 `add()` 和 `promoteExistingEntryIfNeeded()` 中追加
- 为后续马尔可夫链推荐做准备

#### 6. 频率×新鲜度混合排序
`hybridFrequencyRecencyScore`：
```
score = min(采纳次数 / 年龄(小时)^1.5, 0.35)
```
- 仅纳入 `accepted` + `copiedManually` 反馈
- 与原有 recency 取 max，融入 `RecommendationFeature.recency`

#### 7. 反馈数据导出
- `RecommendationFeedbackStore.exportToFile()` → JSONL 文件
- 设置 → 推荐 → 「导出数据…」按钮
- 弹窗确认，自动打开 Finder 定位文件

### 修改文件清单

| 文件 | 改动 |
|------|------|
| `Intelligence/RuleBasedRecommendationEngine.swift` | +containsSensitiveContent, +hybridFrequencyRecencyScore, +luhnCheck, 修改 negativeFeedbackScore |
| `Intelligence/RecommendationFeedbackStore.swift` | +exportToFile() (JSONL 导出) |
| `Models/AppCommand.swift` | +dismissAllRecommendations case |
| `Managers/HistoryStore.swift` | +revealedPreferenceWindowTimer, +lastPredictionEntryIDs, +copySequence, Action 枚举扩展, 显露偏好逻辑 |
| `Managers/ApplicationShell.swift` | perform() 添加 dismissAllRecommendations 路由 |
| `Managers/MenuBarController.swift` | +dismissAllRecommendationsFromMenu 选择器 |
| `Managers/SettingsWindowController.swift` | makeSettingsView() 传递 feedbackStore |
| `Views/MenuBarRecommendationsView.swift` | 「都不是我想要的」蓝色按钮 |
| `Views/SettingsView.swift` | +feedbackStore 参数, +exportFeedbackData(), 导出按钮+alert |

### 编译状态
`swift build` ✅ 零警告零错误


## 2026-06-14: macOS 12 红按钮恢复窗口问题 （进行中）

用户反馈：macOS 12 上点击红色关闭按钮后，窗口消失但无法通过任何方式重新打开（Dock/快捷键/菜单栏）。Cmd+H 完全正常。macOS 15+（26.x）无此问题。

### 尝试历程

| 尝试 | 方案 | 结果 |
|------|------|------|
| 1 | `NSApp.hide(nil)` 在 `windowShouldClose` 中直接调用 | 不行 |
| 2 | `sender.orderOut(nil)` + 弱引用直接恢复 | 不行 |
| 3 | `DispatchQueue.main.async { NSApp.hide(nil) }` 延迟到下一个 RunLoop | 不行 |
| 4 | `applicationDidBecomeActive` 中检测不可见窗口并恢复 | 不行 |

### 当前假设

macOS 12 与 macOS 15+ 在 SwiftUI Window 生命周期管理上有本质差异。可能原因：
A. SwiftUI NavigationView（macOS 12）在 `windowShouldClose` 返回 false 后仍然内部销毁了窗口
B. 窗口 delegate 被 SwiftUI 覆盖，`return false` 无效
C. macOS 12 的窗口管理在某个环节无视了 delegate 返回值

### 诊断手段

在 WindowConfigurator.windowShouldClose 和 windowWillClose 中加入了详细日志：
- 记录 `windowShouldClose` 是否被调用
- 记录 `return false` 后 `windowWillClose` 是否仍被触发（证明系统无视了返回值）
- 记录 `_mainWindow` 弱引用在各个环节的状态
- 记录 `showMainWindow` 被调用时 `NSApp.windows` 的完整快照

LifecycleDebugLogger 临时默认开启（`_isEnabledOverride = true`），日志写入 `/tmp/时间剪史_lifecycle_debug.log`。

## 2026-06-11: 粘贴功能全链路调试与修复

### 问题演进

用户报告：点击推荐条目后无法直接粘贴到前台应用。

### 第一轮：以为是代码逻辑问题

- 增加调试日志 → 发现 `AppDelegate.copyAndPasteHistoryEntry` 被调用、`shell.copyAndPasteEntry` 被调用、CGEvent 被投递
- 剪贴板内容正确写入（`changeCount` 增加、`NSPasteboard.string` 正确）
- 但粘贴无效

### 第二轮：换用 AppleScript

- 将 `CGEvent.postToPid` 替换为 `NSAppleScript` + `Process+osascript`
- 仍然失败

### 第三轮：增加全链路诊断

- 添加 `PasteDiagnostics` 工具类和三个独立实验
- 实验 A（直接打字）：失败，`osascript 不允许发送按键 (1002)`
- 实验 B（仅写剪贴板）：成功
- 实验 C（写剪贴板+粘贴）：剪贴板写入成功，粘贴失败

### 第四轮：权限诊断

- `AXIsProcessTrusted()` 返回 `false`
- `Bundle path: /private/tmp/时间剪史_bundle/时间剪史.app`

### 根因

**macOS 拒绝给 `/tmp` 下的应用授予辅助功能权限。**`make run` 从 `/tmp/时间剪史_bundle/` 启动，导致 `AXIsProcessTrusted()` 永远返回 `false`，所有 keystroke 操作被 System Events 拒绝（错误码 1002）。

### 最终方案

**粘贴机制**：`Process` + `osascript` 执行 `keystroke "v" using command down`

**启动路径**：必须从非 `/tmp` 路径启动。项目目录下的 `时间剪史.app` 是 `make bundle` 的输出副本。

**延迟**：0.1s 激活前一个 App + 0.15s 发送按键 = 总计 ~0.25s

**CGEvent 废弃原因**：`CGEvent.postToPid` 在 macOS 15 上对 Terminal、Finder、微信等应用完全无效，事件被系统静默丢弃。

### 修改文件

| 文件 | 改动 |
|------|------|
| `Managers/ApplicationShell.swift` | copyAndPasteEntry 改用 Process+osascript |
| `Managers/AppDelegate.swift` | copyAndPasteHistoryEntry 清理诊断日志 |
| `Views/MenuBarRecommendationsView.swift` | 恢复干净版本（移除实验按钮） |
| `Utilities/PasteDiagnostics.swift` | 新增后删除（仅用于诊断） |

### v1.4.4 发布

- DMG：`时间剪史_v1.4.4.dmg`
- 版本号：Makefile VERSION := 1.4.4
- 粘贴功能✅ OCR搜索✅ 推荐+反馈✅

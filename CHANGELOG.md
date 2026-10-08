# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project follows semantic-style version naming for public releases.

## [v1.4] - 2026-06-11

### Added

- **OCR 图片文字搜索**：基于 Vision 框架对图片内容进行 OCR 识别，识别结果持久化并与原图关联，支持搜索图片内的中文、英文和数字文字。
- **智能推荐引擎**：基于规则的多因子加权推荐系统（`RuleBasedRecommendationEngine`），综合近因、频率、内容匹配、上下文相似度等 9 项因子打分排序。
- **菜单栏推荐面板**（macOS 13+ 用 `MenuBarExtra`，macOS 12 走 `NSStatusItem` 菜单，两条入口都有 Top 3）：点击右上角标签菜单展开推荐列表，显示 Top 3 推荐粘贴条目，支持一键粘贴到当前前台应用。
- **推荐反馈系统**（7 项）：
  - 隐私过滤器：自动排除含 GitHub Token、API Key、信用卡号等敏感内容的条目。
  - 「都不是我想要的」按钮：一键记录本次全部推荐为无效反馈，降低对应条目权重。
  - 显露偏好追踪：推荐展示后 30 秒窗口内监听手动复制，捕获未被点击采纳但实际需要的条目。
  - 反馈回流引擎：负面反馈含 24 小时时间衰减，高频拒绝条目快速降分。
  - 序列模式追踪：记录最近 20 次复制 ID 序列，为序列模式推荐奠定基础。（后续版本已移除该字段，当前 `Sources/` 内 `copySequence` 无命中）
  - 频率×新鲜度混合排序：采纳次数/年龄^1.5 融入 recency 评分。
  - 反馈数据 JSONL 导出：设置 → 推荐 → 导出数据，供分析和调优。
- **推荐权重客制化**：设置页新增「推荐」栏目，用户可独立调节 9 项因子权重（0%-200%），含恢复默认按钮，修改后实时生效。
- **Finder 上下文采集**（设置→隐私，默认关闭）：
  - Finder 当前目录：同目录条目获得加分。
  - Finder 选中文件扩展名：同扩展名条目获得加分。
- **设置页面重构**：改为左侧边栏 + 右侧主栏布局（快捷键 / 通用 / 隐私 / 推荐 / 数据），支持点击整行切换栏目，hover 动效与主窗口边栏统一。
- **全部/收藏切换药丸动效**：按 Apple 原生滑块动效样式做左右非线性速度曲线且带轻微过冲形变的移动切换。
- **右键菜单汉化**：搜索框和文本预览的右键菜单完成汉化，移除无关系统项。
- **搜索框 hover 动效**：鼠标经过搜索框时视觉高亮。
- **文件名扩展名始终显示**：长文件名省略中间部分，扩展名始终保持可见。

### Changed

- **粘贴机制重写**：`CGEvent.postToPid`（macOS 15 已失效）→ `Process` + `osascript` 执行 `keystroke "v" using command down`，确保跨应用粘贴可靠。
- **主菜单彻底本地化**：移除 `MainMenuController`（旧 AppKit 主菜单覆盖方案），全面采用 SwiftUI `.commands` + `ClipboardHistoryCommands`，配合 `Info.plist` 设置 `CFBundleDevelopmentRegion=zh-Hans`，系统菜单从源头本地化。
- **边栏列表 hover 动效**：改为接近 Apple 原生列表风格的 hover 高亮方式。
- **边栏时间显示**：从精确到秒改为 HH:mm 时刻格式，取消每秒刷新，消除列表跳动。
- **历史条目日期显示**：边栏时间前增加日期，按「6月7日 14:23」格式展示。
- **版本号体系**：从 v1.3 经 v1.4beta → v1.4.4，Makefile VERSION 同步更新。
- **菜单栏「刷新历史」移除**：减少无用菜单项。
- **菜单文案优化**：「设置…」→「设置」，「清空未收藏…」→「清空未收藏」。
- **搜索框省略号**：从「搜索历史…」改为中文正确省略号「搜索历史……」。
- **项目结构扩展**：新增 `Intelligence/` 目录（10+ 文件），新增 `Views/MenuBarRecommendationsView.swift`、`Views/RecommendationWeightsView.swift`、`Views/ChineseTextContextMenu.swift`、`Managers/ClipboardHistoryCommands.swift`。
- **启动性能**：生命周期调试日志默认关闭，仅 `CLIPBOARD_HISTORY_DEBUG=1` 环境变量启用。
- **首次复制捕获保障**：窗口显示后延迟 0.3-0.5 秒启动剪贴板监听，不影响首次复制被捕获。

### Fixed

- **推荐项点击无法粘贴**：根因为 `/tmp` 启动路径导致 macOS 拒绝授予辅助功能权限，`AXIsProcessTrusted()=false`。改为从项目固定路径启动 + `Process` + `osascript` 方案彻底解决。
- **OCR 对 Finder PNG 文件无效**：`ClipboardIntake` 将 `file-url` 优先归类为 `.file(url)`，OCR 跳过该分支。修复：`scheduleOCRIfNeeded` 新增 `.file(url)` case，判断图片扩展名后从磁盘加载 NSImage 执行 OCR。
- **中文输入法搜索丢失文本**：`controlTextDidChange` 在 markedRange 清除前触发导致组字未完成即推送。修复：`controlTextDidEndEditing` 兜底推送。
- **QuickLook 频繁崩溃**（`QLPreviewView setPreviewItem: item == nil || internalState != QLPreviewDeactivatedInternalState`）：用 generation token 取消过期加载，脱离窗口时释放旧 `QLPreviewView`，仅在 view 已挂窗口时按需创建。
- **双窗口问题**：关闭主窗口后 `showMainWindow` 误判创建 fallback AppKit 窗口，SwiftUI 原窗口恢复后形成双窗口。修复：删除 fallback 主窗口创建路径，`WindowManager` 仅显示已有 SwiftUI 主窗口。
- **macOS 12 菜单栏图标透明**：`NSStatusItem` 模板图像渲染配置修正。
- **macOS 12 关闭窗口后 Dock 图标无法恢复**：`applicationShouldHandleReopen` 未被正确触发，窗口关闭语义调整。
- **菜单栏菜单反复横跳**：SwiftUI 默认菜单与旧 `MainMenuController` 争夺 `NSApplication.shared.mainMenu`。修复：删除 `MainMenuController`，全面使用 SwiftUI `.commands`。
- **搜索框输入失效**：删除自定义 `NSTextFieldCell` 和复用 field editor 方案，回到标准 `NSTextField` 编辑路径。
- **全部/收藏切换需精确点击文字**：改为点击半按钮区域即可切换。
- **设置页边栏需精确点击文字**：改为点击整个 hover 高亮范围即可切换栏目。
- **菜单栏「推荐」项跳转到应用而非直接粘贴**：修复为直接粘贴到当前前台应用。
- **推荐匹配率不随前台 App 切换更新**：修正推荐列表更新触发逻辑。

### Release

- DMG：`时间剪史_v1.4.4.dmg`（该产物未留在仓库里，仓库只有 v1.4.5 的 DMG）
- 构建：`swift build` ✅（当时 116 个测试全绿；执行数以当次 `swift test` 输出为准）
- 签名：ad-hoc 签名（未 notarize）
- 兼容：macOS 12+ / Intel + Apple Silicon

## [v1.3] - 2026-06-09

### Added

- 新增历史持久化，文本、图片、文件引用和缩略图可在重启后恢复。
- 新增收藏功能，收藏项可在侧边栏筛选和菜单栏收藏区快速使用。
- 新增开机启动设置，支持在系统允许时从设置窗口开启或关闭。
- 新增菜单栏入口，可显示主窗口、打开设置、刷新历史、清空历史和退出应用。
- 新增“再次复制”全局快捷键，默认 `⌃⌥C` 复制当前选中记录，并支持在设置中自定义和恢复默认。
- 新增发布流程文档，说明本地发版、校验和人工检查步骤。

### Changed

- 历史保留策略改为普通记录默认 500 条 / 30 天，收藏项不受自动清理影响。
- 清空历史改为只清空未收藏记录，收藏记录会保留。
- 视频文件预览改用原生播放器，默认静音自动播放。
- 视频控制条改为保留右下角操作区空间，避免宽视频控件被收藏/复制/删除按钮遮挡。
- 主窗口改为固定边栏布局，移除边栏折叠入口。
- 发布脚本默认先运行自动测试，构建后校验 App `Info.plist` 版本号。
- README 更新为 v1.3 持久化版本的实际能力和数据保存说明。

### Fixed

- 修复同一张图片隔多条记录后再次复制仍生成重复历史的问题。
- 修复视频预览控件需要折叠/展开边栏后才容易出现的问题。
- 修复关闭主窗口后视频仍继续播放的问题。
- 修复竖屏视频下方播放控件缺少进度条调节能力的问题。
- 修复边栏折叠按钮在重新打开窗口后又出现的问题。
- 测试环境改用内存存储，避免单元测试读取或污染本机真实历史记录。
- 持久化启动加载只读取一次历史文件，减少不必要磁盘读取。
- 统一左侧清空按钮和右侧悬浮操作按钮的玻璃样式与 hover 动效。

### Release

- DMG：`releases/时间剪史_v1.3.dmg`
- SHA256：`8a59d872cdccfe4caa334c055c1bf92a62facb7fa36d148345e5abfb8c095538`

## [v1.2.2beta] - 2026-06-08

### Added

- 新增设置窗口，可修改和恢复呼出主窗口的全局快捷键。
- 新增快捷键录制控件，支持在设置中直接录入组合快捷键。
- 新增本轮架构重构总结文档，记录五个模块深化点和验证结果。

### Changed

- 深化剪贴板输入模块，将轮询、解析、缩略图生成、来源 UTI 和相邻去重集中到 `ClipboardIntake`。
- 深化文件预览模块，将文件类型判断、文本读取、QuickLook 与 fallback 预览集中到 `FilePreview`。
- 深化应用外壳模块，将应用生命周期意图、主菜单、菜单栏、设置窗口和窗口恢复逻辑从 `AppDelegate` 中拆分。
- 深化快捷键配置模块，将偏好保存、Carbon 注册、失败回滚和错误提示集中管理。
- 将条目展示文案、文件名、大小和预览文本集中到 `EntryPresentation`，减少视图中的格式化逻辑。
- 更新 Release / 仓库整理文档，继续保持 DMG、App bundle 和分析产物不进入源码提交。

### Fixed

- 改善文件、图片和文本预览路径的一致性，减少视图层直接做磁盘读取的情况。
- 改善关闭窗口后的快捷键呼出路径，快捷键注册失败时会回滚到上一个可用配置。

## [v1.2.1] - 2026-06-06

### Added

- 菜单栏模式，支持显示主窗口、刷新历史、清空历史和退出应用。
- 视频文件预览，常见视频文件可通过 QuickLook 在详情区查看。
- 视频缩略图，Finder 复制视频文件时显示首帧缩略图。
- 标签/语义分类基础，区分文本、图片内容和文件引用。
- macOS 12 支持完善，补齐 `NavigationView` 与 `NSStatusItem` 兼容路径。

### Fixed

- 修复搜索无结果时错误显示“暂无剪贴板历史”的问题。
- 修复边栏时间精确到秒导致列表频繁跳动的问题。
- 修复边栏标题“时间剪史”在窄宽度下换行的问题。
- 完善关于窗口内容，补充版本、作者、GitHub、License 和项目简介。
- 优化按钮 Hover 动效，减少不一致和溢出感。
- 统一图片、视频、文件缩略图样式。
- 修复 macOS 12 关闭窗口后 Dock 图标无法重新打开主窗口的问题。
- 修复 macOS 12 菜单栏图标透明问题。
- 修复打包流程中的签名与扩展属性问题，降低“损坏无法打开”的概率。

### Changed

- 项目架构整理，将源码按 `Managers`、`Models`、`Utilities`、`Views` 分组。
- 拆分 `ContentView`、`ClipboardManager` 等核心文件，降低单文件职责复杂度。
- 生命周期管理优化，集中主窗口显示和恢复逻辑。
- 启动性能优化，默认关闭生命周期日志并延迟启动剪贴板监听。
- 打包流程优化，生成 Intel + Apple Silicon 通用 App。

## [v1.1] - 2026-06-06

### Added

- macOS 12+ 兼容构建。
- 常见文件格式预览。

### Fixed

- 移除调试绿框。
- 修正 Dock 图标尺寸。

## [v1.0] - 2026-06-05

### Added

- 初始版本。
- 剪贴板文本、图片和文件历史记录。
- SwiftUI 主窗口界面。
- DMG 打包流程。

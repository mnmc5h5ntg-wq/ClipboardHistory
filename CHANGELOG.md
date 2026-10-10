# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project follows semantic-style version naming for public releases.

## [Unreleased]

### Added

- **设置「通用」页两项全局开关**（第三轮审计 D-3）：「暂停记录剪贴板」与「识别截图文字用于搜索」。
  暂停只挡后台自动采集（changeCount 照常推进，恢复时不会补记暂停期间的旧内容），
  用户点名拖入的文件仍然入库；OCR 关闭后不再对新入库图片排识别任务。两项都持久化在 UserDefaults。
- 拖入文件被忽略时给出横幅反馈（D-4）："拖入的 N 项不是本机文件，未加入历史" / "已加入历史，另有 N 项…已忽略"。

### Fixed

- **列表拖出与拖选争用**（D-1，S2）：侧栏改用系统 `List(selection:)`，拖出只从行首把手发起。
  以前整行挂 `onDrag`，系统在每个阈值处先开拖出会话，**拖选在大多数条目上已经失效**。
  顺带把单击选中、shift/⌘ 多选、方向键与滚动跟随、VoiceOver selected 语义交回系统实现。
- 推荐理由不再把"前台是浏览器"说成"偏好链接"（D-2）：内容类型标签改由条目自身类型决定。
- 存档"只加可选字段不升版"这一决定补上新→旧→新往返用例（D-5），边界写进 `migrate` 注释。
- 降采样后的图片现在自带新尺寸的 PNG 字节（D-6）：首次 PNG 编码不再落在主线程的保存快照
  或用户按住鼠标拖出的那一瞬间。
- 设置侧栏不再混用实心与描线符号（D-8）：`sparkles` → `wand.and.stars`。

- **右键菜单未汉化且含无关系统项**（issue #13）：搜索框（编辑态与非编辑态）现在弹
  `撤销 / 重做 / 剪切 / 复制 / 粘贴 / 全选`，详情只读区弹 `复制 / 全选 / 查找…`，每一项都是中文，
  不再出现快速查看附件 / 字体 / 书写方向 / 布局方向 / 服务 / 查询 / Show All Tabs 这类系统注入项。
  编辑态的右键原本落在**窗口共享的 field editor** 上（改它的 `menu` 会被 AppKit 复原），
  现在由 `FieldEditorRightClickInterceptor` 在派发前截走；只认领我们自己的搜索框，别的控件不受影响。
  屏幕上的观感仍需人眼核对：`docs/MANUAL_TEST_v1.4.8_issue13.md`。

### Changed

- CI 新增一个报告型步骤，真的执行在屏交互探针与帧捕获并打印执行数/帧数（D-7，`continue-on-error` 起步）。
- 视觉基线重拍：`sidebar-*`/`row-*` 帧因系统列表 chrome 发生变化；离屏帧里 `List` 的选中高亮会画成整块黑
  （语义色伪影，跟随选中集合），不作为产品判据。

## [v1.4.8] - 2026-10-10

### Added

- **行内直接操作**：双击列表条目 = 复制这一条（与详情区浮层「再次复制」同一个动作，会把这条顶到最前）；
  行首星标 = 一键收藏/取消。带 shift / command 的双击不复制（那两个键是范围选择/多选的前缀）。
  星标做成行的**兄弟控件**而不是嵌在行按钮里，实测点它只翻收藏、不改变选中集合。
- **拖拽双向**：条目可拖出（文本 / PNG / 单个文件引用，`EntryDrag`）；文件可拖入列表入库
  （`DroppedFileImport`，多个文件记成一条 `.files`）。落点刻意只在列表区域，不抢详情文本视图的文字拖放。
- 只含非文件 `NSURL`（网页链接）的剪贴板现在记成文本条目，不再静默丢弃。
- 离屏视觉夹具新增菜单栏面板三个状态与行内星标两态：帧数 58 → 68。

### Changed

- 行首星标从"未收藏即 `.clear`（不可见）"变成真控件：未收藏 `primary.opacity(0.55)`
  （实测对比度 3.54:1 亮 / 4.64:1 暗），已收藏压深成琥珀 `(0.86,0.45,0)`（3.90:1 / 4.28:1）。
  行内星标与浮层共用 `FavoriteTogglePresentation`，并有源码扫描禁止两处各写字面量。
- 左侧列表支持方向键移动选择（`SidebarKeyboardNavigation`）+ `ScrollViewReader` 滚动到选中项；
  macOS 14+ 抑制列表容器的系统焦点环（12/13 无对应 API，仍会出现，已在守卫里注明）。
- 菜单栏面板区分「正在整理推荐…」与「暂无推荐」（`isRefreshingPredictions`）——
  菜单同步构建而预测异步计算，把"还不知道"说成"没有"是本轮自己引入又修掉的误导。
- 亮色 chrome：9 处 `.white.opacity` 换成 `.separator` / `.quaternary` / `primary.opacity`；
  破坏性确认框 Return 改为「取消」，破坏性按钮标 `hasDestructiveAction` 且不带快捷键。
- 详情预览加 8 秒兜底（`PreviewLoadTimeoutPolicy`）；系统「减少动态效果」接入筛选 pill 动画与悬停放大。
- 推荐理由不再一行里把来源 App 说两遍；隐私页文案披露"来源 App 名称"及其用途。

### Fixed

- **启动闪退（S1）**：D-019 给 `AppDelegate` 加 `init(historyStore:)` 后，ObjC 的 `-init` 只剩编译器留下的
  trap 桩，而 SwiftUI 的 `@NSApplicationDelegateAdaptor` 正是通过它构造 delegate ⇒ 新包一打开就
  `EXC_BREAKPOINT`。补 `override convenience init()`。328 个用例与 CI 全绿都看不见它
  （Swift 侧 `AppDelegate()` 解析到带默认参数的那个 init），线上 v1.4.7 不受影响。
- 存档含同 id 两条时，预测管线 `Dictionary(uniqueKeysWithValues:)` 触发 fatalError：改为保留首条，
  并补一条走 `HistoryStore` 全链路的端到端守卫。
- 快捷键录制成功后按钮仍显示「请输入快捷键」（`shortcut.didSet` 在录制态跳过回显，之后再没人改）：录完立刻回显。
- 保存不再重写未变更的图片文件、被取代的落盘任务会取消；`load()` 不再遗留只读标志。
- 超长文本的字符统计改为有界计数；图片入库按 4096px 上限降采样（4K 及以下逐字节不变）。
- 来源 App 归属（`sourceAppBundleID` / `sourceAppName`）落盘并在重启后恢复；schema 仍 v1，字段可选。
- 字号/图标可达性若干：行时间戳与菜单理由行 10pt → 11pt、非法 SF Symbol `"questionable"` → `questionmark.circle`、
  缩略图与图片预览补无障碍名称。

### Build / Release

- **发布链路新增启动闸门**（`scripts/prepare_release.py`）：反汇编包内二进制，若 `AppDelegate` 还留着
  「未实现初始化器」桩就拒绝发布。arm64 上类名字面量离调用点二十几行，所以按桩块扫描而不是固定窗口回看。
- AI 草案代码移出产品 target（`ClipboardHistoryDesignDrafts` + `ClipboardHistoryIntelligenceCore`），
  `nm` 证明草案符号在产品二进制里为 0；本地网络守卫的扫描根收窄到产品目录。
- 测试判据不再依赖机器负载：性能守卫改为"N 次同操作采样取最快 + 样本跨度超阈值才 skip"，阈值未动。

### Tests

- Swift 单元测试 328 例 / 9 跳过 / 0 失败；发布脚本测试 30 例通过；`swift build` 0 告警。
- 在屏交互探针（`CLIPBOARD_HISTORY_UI_INTERACTION=1`）：合成真实鼠标事件，在**完整侧栏容器**里验证
  单击选中 / 双击恰好复制一次 / 点星标不动选中；焦点环以视图树清点为判据（截图那条路不可信）。
- 每条新守卫都做过变异对照（含"删掉调用点 ⇒ 恰好那条红"），源码按 sha 逐字节还原。

### Release

- DMG：`releases/时间剪史_v1.4.8.dmg`
- SHA256：`c31a16e0c144d71063e522f980a25c5cad17409d08a2ab09bac5451a6997e88d`

## [v1.4.7] - 2026-10-09

### Fixed

- **卷根目录下的文件不再把父目录标签渲染成 `…/..`**：`URL.parentDirectoryLabel` 先 `standardizedFileURL`
  再取目录名，并在守卫里补上 `..`。旧实现在部分 Foundation 版本上（CI 的 macOS 15 / Swift 6.1.2）会把
  `/a.txt` 的父路径算成 `/..`；macOS 26/27 上原本显示正确，所以本版是补严谨而非救急。

### Tests

- 测试不再覆写 XCTest 的 `tearDown()`：原 `try await super.tearDown()` 在 CI 的 Swift 6.1.2 下被判
  「sending value of non-Sendable type 'XCTestCase' risks causing data races」，整个测试 target 编译失败；
  改为每条用例开头复位偏好设置，用例顺序无关。
- 父目录标签补两条断言：`/a.txt → …`、`/Applications/X.app → …/Applications`。
- 发布脚本环境加一条断言：交给子进程的 `SDKROOT` 必须等于 `xcrun` 解析出来的那个。

### Release

- DMG：`releases/时间剪史_v1.4.7.dmg`
- SHA256：`5046475defcf6f25b829bd872595475b93cfda7e832cdcb0a78e13db499073a2`

## [v1.4.6] - 2026-10-09

### Added

- **设置 → 隐私「数据与保留」分组**：保存位置、保存内容类型、500 条 / 30 天、收藏长期保留、清空历史语义、敏感内容提醒 —— 这些文案此前只存在于代码里，产品从未显示（对应 #16）。
- **窗口顶部提示条**：存档恢复结果、自动粘贴失败原因、成批清理过期记录三类事件第一次变得可见（对应 #5）。
- **CI workflow**：构建零告警 + `Executed N tests` 只准涨不准跌 + 发布脚本测试 + Info.plist 闸。已在 main 上跑通（首跑抓到两条只在 CI 工具链下暴露的缺陷，见下）。
- **无障碍**：纯图标按钮在悬停提示之外补上 `accessibilityLabel`，并加静态守卫防止回归。
- **系统「减弱动态效果」**：展开 / 收起与缩放改为尊重该设置；0.11–0.14s 的颜色渐变有意保留。

### Changed

- **主线程热点（实测）**：保存一条记录 667.8ms → 约 5ms；启动载入 413.9ms → 3ms；复制一张 3000×2000 图片时 `add()` 94ms → 0.04–0.77ms；图片去重比较 434ms → 147ms；列表派生 14.07ms/次 → 0.00ms/次；2.4MB 文本预览 45.8ms → 0.02ms。
- **推荐预测由 2 秒轮询改为事件驱动**（新复制 / 打开菜单 / 前台切换），并加代际防护丢弃过期结果。
- **OCR 的像素解码移出主线程**，改用 ImageIO 直接解出有界尺寸的一帧，串行后台队列执行；OCR 日志只记长度不记内容。
- **`Info.plist` 由模板 + 脚本生成并逐键校验**，缺任一必需键即构建失败（此前是 20 行 `PlistBuddy` 且每行 `|| true`）；新增 `NSAppleEventsUsageDescription`、`CFBundlePackageType`、`NSPrincipalClass`。
- **`make dmg` 同时产出 `.sha256` 并自校验**；`make build` 在 SwiftPM 构建库被半删除时给出可执行的恢复提示。
- **README 与 20+ 处文档更正**：删掉「点击推荐不会粘贴」「侧边栏 Magic」「菜单里有刷新历史」等与代码相反的承诺；带日期的旧文档统一加「历史快照」横幅。

### Fixed

- **存档损坏不再连带删库**：先保全 `history.corrupt-<时间>.json`（不删原件）再从滚动备份恢复，两条路都失败时仍保住被引用的图片文件。
- **菜单栏「清空未收藏」补上二次确认**（此前带弹窗的函数没有任何调用者）。
- **同 bundle 的第二份进程不再并存**：两份会各自整库写存档、后写的整片盖掉先写的记录。
- **降级不再毁数据**：读到更高 `version` 的存档改为只读打开并说明原因（`version` 字段此前只写不读）。
- **自动粘贴失败不再静默**：`osascript` 的退出码与 stderr 现在翻译成可执行指引并显示出来。
- **浏览器链接不再被当成本地文件条目**；重复复制不再丢失来源 App 归因。
- **推荐排序确定化**：同一份历史在两次启动之间不再给出不同结果；同一条记录不再占两个推荐名额。
- **敏感内容误判收紧**（前缀需紧跟 ≥12 位 `[A-Z0-9]`）；反馈载荷不再保存剪贴板原文且随删除 / 清空级联清理；导出失败不再假装成功。
- **界面**：设置侧栏未选中行图标恢复可见；破坏性「清空」按钮不再在两个分类各放一份；5 处信息文字对比度暗色 2.22:1 → 5.79:1、亮色 1.89:1 → 3.98:1。
- **CI 首跑抓到的两条本机看不出的缺陷**（runner 是 Swift 6.1.2，开发机是 6.2.1）：`HotKeySettingsTests` 覆写的 `tearDown() async throws` 在 runner 上因 `await super.tearDown()` 被判并发错误、整个测试 target 编译不过（改为用例内复位，不再依赖 XCTest 生命周期签名）；`URL.parentDirectoryLabel` 对根目录下的文件返回 `…/..`（先 `standardizedFileURL` 再取名字）。
- **视频宽高未知时显示错误态而非 16:9 空播放器**；播放器 KVO 观察者在 `deinit` 释放；侧栏拖选的行位置表不再只增不减。

### Tests

- `swift test` 229 例（1 例按设计 skip）、0 失败，连跑 6 次一致；清空 `.build` 后干净重建 0 编译告警。
- 发布脚本测试 18 例通过；修复了 `prepare_release.py` 在本机必然失败的环境缺陷（`/usr/bin/python3` 给子进程注入 CommandLineTools 的 `SDKROOT`，而编译器来自 Xcode）。
- 修掉一条恒绿的假基准（计时对象是构造而非行为），并修正一处过紧的性能界值导致的偶发红。

### Release

- DMG：`releases/时间剪史_v1.4.6.dmg`
- SHA256：`9ed54be3144d5f5bc3f0751f7f8846dcfe8886d39fddae85ea65c69715bf2837`

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

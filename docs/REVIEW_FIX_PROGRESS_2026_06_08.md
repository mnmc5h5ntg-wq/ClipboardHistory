# Review Fix Progress 2026-06-08

目标：按 `docs/SUBAGENT_CODE_REVIEW_2026_06_08.md` 的修复顺序，逐项解决有价值的问题。
约束：不新增功能、不重构目录结构、不引入新的架构抽象；优先保证行为正确性。
状态：进行中。最近更新：2026-06-09 02:53。

## 当前关键决策

- 按审查文档顺序推进，先处理“阶段 1：可靠性热修”。
- 每完成一个问题后运行编译验证，并补充或更新自动测试。
- 修复时保持现有模块边界；如果某项建议不值得实现，会在最终汇总中明确说明原因。
- agent 工作流配置仍不作为本轮应用修复的一部分。
- 人工测试结果优先级高于自动测试；如果自动测试通过但真实 App 仍复现问题，文档状态必须标记为未完成。
- 当前最优先问题：隔几条记录后再次复制同一张图片仍会生成重复记录。下一轮应先诊断真实剪贴板读写路径，不要只根据单元测试判断已修复。

## 已完成

- 已创建审查总结文档：`docs/SUBAGENT_CODE_REVIEW_2026_06_08.md`。
- 已创建本持续进度文档：`docs/REVIEW_FIX_PROGRESS_2026_06_08.md`。
- 2026-06-09 人工回归结果：
  - 通过：播放视频后点击左上角关闭主窗口，视频已正确停止播放。
  - 通过：重新打开主窗口后，边栏右上角折叠按钮已消失。
  - 未通过：隔几条记录后再次复制同一张图片，仍会生成重复历史记录。
- 已完成 1. 剪贴板写回失败被当成成功。
  - `ClipboardWriting.write` 现在会抛出写入失败错误。
  - `HistoryStore` 只有在写入成功后才更新 pasteboard changeCount。
  - `copyAndPromote` 只有在写入成功后才置顶、选中和持久化。
  - 新增测试覆盖普通复制失败和再次复制失败。
- 已完成 2. 快捷键注册失败回滚不可靠。
  - `GlobalHotKeyController.updateShortcut` 现在返回 `HotKeyUpdateResult`，明确区分成功、失败但旧快捷键仍可用、失败且旧快捷键也未能恢复。
  - 更新流程改为先用 probe hotkey id 探测新快捷键是否可注册，再切换真实快捷键，避免先卸载旧快捷键。
  - `HotKeySettings.start()` 在保存快捷键不可用时会尝试恢复默认快捷键，并给出明确提示。
  - 新增测试覆盖保存失败、旧快捷键恢复失败、启动时回退默认快捷键、启动时快捷键完全不可用。
- 已完成 3. 主窗口识别依赖不稳定 identifier。
  - `WindowConfigurator` 现在为主窗口设置 `WindowManager.mainWindowIdentifier`。
  - `WindowManager` 使用精确 identifier 判断应用主内容窗口。
  - 新增 `WindowManagerTests` 覆盖主窗口、普通其它窗口和 panel 的识别规则。
- 部分完成 4. 图片去重按对象身份判断。
  - `StoredImage` 已从对象身份比较改为内容指纹比较，并补充了相邻重复图片不会重复入库的自动测试。
  - 2026-06-09 追加过一次“历史中已有同一图片时提升旧条目”的尝试，并新增自动测试覆盖模拟场景。
  - 真实人工测试仍失败：隔几条记录后再次复制同一张图片，仍会生成重复历史记录。
  - 当前判断：自动测试没有覆盖真实系统剪贴板的图片读写差异。下一轮需要先抓取真实复制路径中的 pasteboard types、图片尺寸、bitmap 参数、指纹结果和历史匹配结果，再决定是否调整指纹策略或历史合并策略。
- 已完成 5. 文件丢失或移动后仍进入预览/复制流程。
  - `MediaLoader` 在文件不存在时返回明确失败状态，不再进入空 QuickLook、空视频或 fallback 预览。
  - `SystemClipboardWriter` 写文件 URL 前先检查文件是否存在；缺失时抛出 `ClipboardWriteError.fileDoesNotExist`，且不会先清空系统剪贴板。
  - `HistoryStore` 沿用复制失败保护：缺失文件再次复制失败时，不置顶、不持久化、不更新 pasteboard changeCount。
  - 新增测试覆盖缺失文件同步预览、异步预览和剪贴板写入失败。
- 已完成 6. 视频缩略图生成阻塞主线程。
  - `ClipboardIntake` 读到视频文件 URL 时不再同步使用 AVFoundation 生成视频帧缩略图。
  - 视频文件仍会进入历史；详情预览继续由 `MediaLoader` 和内置播放器处理。
  - 如果系统剪贴板本身提供 TIFF 或 icns 图标，仍可作为轻量缩略图使用。
  - 本次没有新增后台缩略图模块，原因是当前约束是不引入新的架构抽象；先消除主线程阻塞风险。
  - 新增测试覆盖视频文件 URL intake 不生成缩略图。
- 已完成 7. 持久化在 MainActor 同步全量写盘。
  - `FileHistoryPersistence` 现在先在 MainActor 上生成可跨线程的保存快照，再把 JSON 写入、图片文件写入和旧图片清理放到串行后台队列执行。
  - `HistoryStore` 增加 `flushPendingPersistence()`，应用退出时会等待最后一次保存完成，避免后台写盘还没落盘就退出。
  - `FileHistoryPersistence.load()` 会先等待同实例待保存任务完成，保证保存后立刻读取的行为仍可靠。
  - 新增测试证明 `save()` 不会同步写出 `history.json`，恢复保存队列并 flush 后才落盘。
  - 取舍：图片转 PNG 快照仍在 MainActor 上完成，因为当前模型包含 `NSImage`；跨线程处理 AppKit 对象属于第 8 项单独收口。
- 已完成 8. `Task.detached` 与 `@unchecked Sendable` 掩盖 AppKit 跨线程问题。
  - `MediaLoader` 的后台任务现在只返回 `FilePreviewPayload`，内容为 `Data`、`String`、视频比例或预览类型，不再在后台创建或跨线程传递 `NSImage` / `FilePreview`。
  - `FilePreview` 已移除 `@unchecked Sendable`。
  - `MediaLoadHandle` 现在是 MainActor 句柄，负责把后台 payload 转成主线程上的 `FilePreview`。
  - 新增测试证明图片文件的后台 payload 只携带 Data。
- 已完成 9. 视频播放器资源释放不完整。
  - `VideoPlaybackController.stop()` 现在会暂停、移除 time observer、清空当前 `AVPlayerItem`，并重置播放时间、时长和播放状态。
  - 切换到不同视频 URL 时，会先卸载旧 item，再加载新 item。
  - `VideoPlayerSurface.dismantleNSView` 会断开 `AVPlayerLayer.player`，避免 SwiftUI 视图拆卸后继续持有播放器。
  - 新增测试覆盖 stop 卸载当前 player item、切换 URL 替换当前 player item。
- 已完成 10. 明文持久化剪贴板内容。
  - 在不新增产品功能的约束下，本轮没有实现首次启动说明、暂停记录、隐私模式或历史加密。
  - 已对现有本机持久化做权限硬化：历史根目录和图片目录权限设置为 `700`，`history.json` 和图片文件权限设置为 `600`。
  - 新增测试覆盖历史目录、图片目录、JSON 文件和图片文件的权限。
  - 暂缓项：首次启动说明、暂停记录、隐私模式、退出时清除、敏感内容自动清理、Keychain 派生密钥加密历史。这些都属于新产品功能或较大设计，不在本轮“只处理审查修复、不新增功能”的范围内。
- 已评估 11. 收藏绕过保留策略。
  - 当前产品决策是“清空未收藏记录”，收藏长期保留；这个行为也符合用户之前明确要求。
  - 报告建议的“清空全部，包括收藏”和“疑似敏感内容收藏二次确认”属于新增危险操作/新增确认流程，不符合本轮“不新增功能”的约束。
  - 本轮不改代码，保留现有行为；后续如果要做，应作为独立产品设计项处理。
  - 已验证现有测试 `HistoryStoreTests/testPerformSelectDeleteAndClearKeepsFavorites` 通过，证明清空仍保留收藏。
- 已完成 12. 菜单栏直接暴露最近内容。
  - macOS 12 状态栏菜单和 macOS 13+ `MenuBarExtra` 的快速复制条目都改用隐私标题。
  - 菜单栏默认显示“最近文本记录 / 收藏文件记录”等类型信息，不再显示真实文本摘要或文件名。
  - 快速复制行为不变，仍通过条目 id 找到对应历史记录后复制。
  - 新增测试覆盖隐私菜单标题不包含文本内容或文件名。
- 已完成 13. 文件路径在 UI 和 JSON 中暴露。
  - 详情头部的文件描述从完整路径改为只显示文件名。
  - fallback 文件预览不再显示完整路径，避免默认暴露用户名、项目名和目录结构。
  - JSON 中仍保留真实文件 URL，因为再次复制文件需要原路径；bookmark / 存储层脱敏属于更大设计，本轮不做。
  - 新增测试覆盖文件描述不包含完整路径。
- 已完成 14. macOS 13+ 菜单栏快速复制绕过 `ApplicationShell`。
  - `App.swift` 的 `MenuBarExtra` 快速复制不再直接调用 `historyStore.perform(.copyAndPromote(entry))`。
  - `AppDelegate` 新增基于 entry id 的 `copyHistoryEntry(id:)` 入口。
  - `ApplicationShell.copyHistoryEntry(_:)` 现在转为 `copyHistoryEntry(id:)`，再从当前 `HistoryStore.entries` 重新解析条目后复制，避免菜单持有过期条目对象。
  - macOS 12 状态栏菜单和 macOS 13+ `MenuBarExtra` 都统一通过 shell 路径执行快速复制。
  - 新增 `ApplicationShellTests` 覆盖按 id 重新解析当前条目，以及缺失 id 不复制。
- 已完成 15. `DetailPreviewViews.swift` 过重。
  - 在不重构目录结构、不引入新架构抽象的约束下，本轮只做同目录文件拆分。
  - 将已经存在的视频预览、播放控制器、播放参数和时间格式化移动到 `Views/VideoPreview.swift`。
  - `DetailPreviewViews.swift` 现在保留 QuickLook bridge 和 `DetailFileView` 文件预览组合逻辑。
  - 这是“搬家不装修”的维护性修复，没有改变视频播放 UI 或行为。
- 已完成 16. `ClipboardIntake` 仍承担媒体处理。
  - `ClipboardIntake` 保留直接读取剪贴板图片数据的能力，因为这是剪贴板内容本身，不属于文件预览媒体处理。
  - 文件 URL intake 阶段不再同步读取图片文件、不再缩放文件缩略图，避免剪贴板轮询路径做磁盘 IO 和图像处理。
  - 如果系统剪贴板随文件 URL 同时提供 TIFF 或 icns 轻量图标，仍会使用它作为缩略图；这不需要读取源文件。
  - 详情预览继续由 `MediaLoader` 负责读取图片文件、文本文件、视频和 QuickLook 预览。
  - 新增测试覆盖图片文件 URL 不会在 intake 阶段同步生成缩略图。
- 已完成 17. 发布脚本失败回滚不完整。
  - `prepare_release.py` 现在在发布流程开始前记录 Makefile、CHANGELOG、release notes、checksum 和既有 release DMG 状态。
  - 失败时会恢复 Makefile / CHANGELOG，恢复或删除 checksum / release notes，删除半成品 release DMG，并把已归档的旧 DMG 移回原位。
  - 新增测试注入 changelog 写入阶段失败，验证旧 DMG、checksum、release notes、CHANGELOG 和 Makefile 都被回滚。
- 已完成 18. 发布/安装说明鼓励绕过 Gatekeeper。
  - `README.md` 和 DMG 内 `安装说明.txt` 不再给普通用户提供 `xattr -cr` 终端命令。
  - 普通用户打开受阻时，只引导 Control-点击打开、系统设置允许打开，或删除后重新从 DMG 拖入 Applications。
  - `docs/RELEASE_PROCESS.md` 新增“内部测试排查”段落，说明 `xattr -cr` 只允许作为开发者本机排查本地构建产物的临时手段。
  - `Makefile` 中用于本地打包产物清理的 `xattr` 保留，因为它不是普通用户安装说明。
- 已完成 19. GitHub Issue 脚本与本地 `.scratch/` 工作流冲突。
  - `scripts/create_issues.py` 保留为 release-only helper，默认只预演，不创建 GitHub Issue。
  - 真正发布必须显式传入 `--confirm-release-publish`。
  - 开发期继续使用 `.scratch/` 本地 markdown；脚本输出也会提示这一点。
  - 脚本不再使用 `curl` 子进程传递 token，改为 Python `urllib` 在内存中设置 Authorization header。
  - token 只从 `GITHUB_TOKEN` 环境变量读取，不再交互式输入。
  - 新增测试覆盖默认预演、缺少 token 时拒绝发布、确认发布时调用安全 HTTP helper。
- 已完成 20. 文档与实现不一致。
  - `README.md` 中视频说明从 QuickLook / 首帧缩略图改为当前实现：内置播放器预览，默认静音自动播放；图片文件说明改为详情区加载图片预览。
  - About 面板 License 从 MIT 改为 WTFPL，并补充视频预览能力。
  - `docs/ARCHITECTURE_REVIEW.md` 增加历史快照提示，避免旧 `ClipboardManager` / `ClipboardReader` 架构误导当前维护。
  - `docs/ARCHITECTURE_REFACTOR_2026_06_08.md` 同步视频内置播放器路径、MainActor 创建 AppKit 对象的当前并发边界、最新测试数量和人工冒烟项目。
  - 历史 release notes / changelog 中属于旧版本发布事实的描述没有强行改写；当前 Unreleased 和 README 已表达现行行为。

## 待办清单

### 阶段 1：可靠性热修

- [x] 1. 剪贴板写回失败被当成成功。
- [x] 2. 快捷键注册失败回滚不可靠。
- [x] 3. 主窗口识别依赖不稳定 identifier。
- [ ] 4. 图片去重按对象身份判断。代码已部分改造，但真实 App 人工测试仍失败，需要继续诊断并修复。
- [x] 5. 文件丢失或移动后仍进入预览/复制流程。

### 阶段 2：稳定性与性能

- [x] 6. 视频缩略图生成阻塞主线程。
- [x] 7. 持久化在 MainActor 同步全量写盘。
- [x] 8. `Task.detached` 与 `@unchecked Sendable` 掩盖 AppKit 跨线程问题。
- [x] 9. 视频播放器资源释放不完整。

### 阶段 3：隐私与产品策略

- [x] 10. 明文持久化剪贴板内容。
- [x] 11. 收藏绕过保留策略。当前约束下暂缓新增危险操作。
- [x] 12. 菜单栏直接暴露最近内容。
- [x] 13. 文件路径在 UI 和 JSON 中暴露。

### 阶段 4：架构收口

- [x] 14. macOS 13+ 菜单栏快速复制绕过 `ApplicationShell`。
- [x] 15. `DetailPreviewViews.swift` 过重。
- [x] 16. `ClipboardIntake` 仍承担媒体处理。

### 阶段 5：发布与文档

- [x] 17. 发布脚本失败回滚不完整。
- [x] 18. 发布/安装说明鼓励绕过 Gatekeeper。
- [x] 19. GitHub Issue 脚本与本地 `.scratch/` 工作流冲突。
- [x] 20. 文档与实现不一致。

## 重要文件修改记录

- `docs/REVIEW_FIX_PROGRESS_2026_06_08.md`：记录长期修复进度，供上下文压缩后恢复。
- `ClipboardHistory/Sources/ClipboardHistoryApp/Managers/ClipboardWriter.swift`：剪贴板写入失败现在会抛出 `ClipboardWriteError`。
- `ClipboardHistory/Sources/ClipboardHistoryApp/Managers/HistoryStore.swift`：复制失败时记录错误，不更新 changeCount，不置顶，不持久化。
- `ClipboardHistory/Tests/ClipboardHistoryAppTests/HistoryStoreTests.swift`：新增复制失败行为测试。
- `ClipboardHistory/Tests/ClipboardHistoryAppTests/TestSupport.swift`：测试用剪贴板写入器支持抛错。
- `ClipboardHistory/Sources/ClipboardHistoryApp/Managers/GlobalHotKeyController.swift`：快捷键更新返回明确结果，并使用 probe id 先探测新快捷键可用性。
- `ClipboardHistory/Sources/ClipboardHistoryApp/Managers/HotKeySettings.swift`：启动和保存失败时给出更准确的恢复状态。
- `ClipboardHistory/Sources/ClipboardHistoryApp/Models/HotKeyAction.swift`：新增 probe hotkey id。
- `ClipboardHistory/Tests/ClipboardHistoryAppTests/HotKeySettingsTests.swift`：新增快捷键失败恢复测试。
- `ClipboardHistory/Sources/ClipboardHistoryApp/Managers/WindowConfigurator.swift`：为主窗口设置稳定 identifier。
- `ClipboardHistory/Sources/ClipboardHistoryApp/Managers/WindowManager.swift`：主窗口识别改为精确匹配稳定 identifier。
- `ClipboardHistory/Tests/ClipboardHistoryAppTests/WindowManagerTests.swift`：新增窗口识别测试。
- `ClipboardHistory/Sources/ClipboardHistoryApp/Models/StoredImage.swift`：图片相等和哈希改为基于内容指纹。
- `ClipboardHistory/Tests/ClipboardHistoryAppTests/HistoryStoreTests.swift`：新增相邻重复图片去重测试。
- `ClipboardHistory/Sources/ClipboardHistoryApp/Managers/HistoryStore.swift`：2026-06-09 曾追加“历史中已有同图时提升旧条目”的逻辑，但真实人工测试仍显示同图会重复入库；下一轮要继续诊断真实剪贴板路径。
- `ClipboardHistory/Tests/ClipboardHistoryAppTests/HistoryStoreTests.swift`：2026-06-09 新增的模拟同图提升测试通过，但没有覆盖用户复现的真实问题，不能作为该问题完成证据。
- `ClipboardHistory/Sources/ClipboardHistoryApp/Managers/ClipboardWriter.swift`：写文件 URL 前检查文件存在性，缺失时不清空剪贴板。
- `ClipboardHistory/Sources/ClipboardHistoryApp/Managers/MediaLoader.swift`：文件缺失时返回 `missingFileMessage` 失败状态；同步预览返回 `nil`。
- `ClipboardHistory/Tests/ClipboardHistoryAppTests/ClipboardWriterTests.swift`：新增缺失文件 URL 写入失败且保留原剪贴板内容的测试。
- `ClipboardHistory/Tests/ClipboardHistoryAppTests/MediaLoaderTests.swift`：同步预览改为显式 unwrap，并新增缺失文件同步/异步预览测试。
- `ClipboardHistory/Sources/ClipboardHistoryApp/Managers/ClipboardIntake.swift`：移除视频文件 URL intake 阶段的同步 AVFoundation 缩略图生成。
- `ClipboardHistory/Tests/ClipboardHistoryAppTests/ClipboardIntakeTests.swift`：新增视频文件 URL 仍入库但不生成缩略图的测试。
- `ClipboardHistory/Sources/ClipboardHistoryApp/Managers/HistoryPersistence.swift`：默认文件持久化改为后台串行写盘，增加 `flushPendingSaves()`。
- `ClipboardHistory/Sources/ClipboardHistoryApp/Managers/HistoryStore.swift`：增加 `flushPendingPersistence()`，作为退出/测试等待后台保存的入口。
- `ClipboardHistory/Sources/ClipboardHistoryApp/Managers/ApplicationShell.swift`：应用退出时等待待保存历史落盘。
- `ClipboardHistory/Tests/ClipboardHistoryAppTests/HistoryPersistenceTests.swift`：新增后台保存队列测试，并为直接文件断言增加 flush。
- `ClipboardHistory/Sources/ClipboardHistoryApp/Managers/MediaLoader.swift`：后台加载结果改为 `FilePreviewPayload`，AppKit 预览对象在 MainActor 创建。
- `ClipboardHistory/Sources/ClipboardHistoryApp/Models/FilePreview.swift`：移除 `@unchecked Sendable`。
- `ClipboardHistory/Sources/ClipboardHistoryApp/Views/DetailPreviewViews.swift`：同步新的 `MediaLoadHandle` 类型。
- `ClipboardHistory/Tests/ClipboardHistoryAppTests/MediaLoaderTests.swift`：测试类改为 MainActor，并新增图片 payload 只携带 Data 的测试。
- `ClipboardHistory/Sources/ClipboardHistoryApp/Views/DetailPreviewViews.swift`：视频停止、切换和视图拆卸时释放播放器资源。
- `ClipboardHistory/Tests/ClipboardHistoryAppTests/VideoPlaybackTests.swift`：新增视频播放器资源释放测试。
- `ClipboardHistory/Sources/ClipboardHistoryApp/Views/VideoPreview.swift`：2026-06-09 增加主窗口隐藏时暂停播放；人工测试确认关闭主窗口后视频已停止播放。
- `ClipboardHistory/Sources/ClipboardHistoryApp/Views/ContentView.swift`：2026-06-09 在 macOS 14+ 使用系统 `toolbar(removing: .sidebarToggle)` 移除边栏折叠按钮。
- `ClipboardHistory/Sources/ClipboardHistoryApp/Managers/WindowConfigurator.swift`：2026-06-09 增加主窗口隐藏通知，并保留窗口工具栏层面的边栏折叠按钮清理兜底；人工测试确认重新打开后折叠按钮未再出现。
- `ClipboardHistory/Sources/ClipboardHistoryApp/Managers/HistoryPersistence.swift`：本机历史目录和文件写入后设置私有权限。
- `ClipboardHistory/Tests/ClipboardHistoryAppTests/HistoryPersistenceTests.swift`：新增历史文件权限测试。
- `ClipboardHistory/Tests/ClipboardHistoryAppTests/HistoryStoreTests.swift`：已有清空保留收藏测试继续作为第 11 项验证证据。
- `ClipboardHistory/Sources/ClipboardHistoryApp/Models/EntryPresentation.swift`：新增菜单栏隐私标题。
- `ClipboardHistory/Sources/ClipboardHistoryApp/Managers/MenuBarController.swift`：macOS 12 状态栏快速复制条目使用隐私标题。
- `ClipboardHistory/Sources/ClipboardHistoryApp/App.swift`：macOS 13+ `MenuBarExtra` 快速复制条目使用隐私标题。
- `ClipboardHistory/Tests/ClipboardHistoryAppTests/EntryPresentationTests.swift`：新增隐私菜单标题测试。
- `ClipboardHistory/Sources/ClipboardHistoryApp/Models/EntryPresentation.swift`：文件描述改为只显示文件名。
- `ClipboardHistory/Sources/ClipboardHistoryApp/Views/DetailPreviewViews.swift`：fallback 文件预览不再显示完整路径。
- `ClipboardHistory/Tests/ClipboardHistoryAppTests/EntryPresentationTests.swift`：新增文件描述不暴露完整路径测试。
- `ClipboardHistory/Sources/ClipboardHistoryApp/App.swift`：macOS 13+ `MenuBarExtra` 快速复制改为通过 `AppDelegate.copyHistoryEntry(id:)` 进入 shell。
- `ClipboardHistory/Sources/ClipboardHistoryApp/Managers/AppDelegate.swift`：新增快速复制 entry id 转发入口。
- `ClipboardHistory/Sources/ClipboardHistoryApp/Managers/ApplicationShell.swift`：快速复制按 entry id 重新解析当前历史条目，避免复制过期菜单条目对象。
- `ClipboardHistory/Tests/ClipboardHistoryAppTests/ApplicationShellTests.swift`：新增快速复制 shell 路由测试。
- `ClipboardHistory/Sources/ClipboardHistoryApp/Views/DetailPreviewViews.swift`：移出视频播放相关类型，只保留文件预览组合逻辑。
- `ClipboardHistory/Sources/ClipboardHistoryApp/Views/VideoPreview.swift`：承载视频预览、播放器控制器、播放控件参数和时间格式化。
- `ClipboardHistory/Sources/ClipboardHistoryApp/Managers/ClipboardIntake.swift`：文件 URL intake 不再同步读取图片文件缩略图，只接受剪贴板自带 TIFF/icns 轻量缩略图。
- `ClipboardHistory/Tests/ClipboardHistoryAppTests/ClipboardIntakeTests.swift`：新增图片文件 URL 不同步生成缩略图测试。
- `scripts/prepare_release.py`：发布失败时恢复 Makefile、CHANGELOG、release notes、checksum 和既有 release DMG。
- `scripts/tests/test_prepare_release.py`：新增发布后段失败回滚测试。
- `README.md`：普通用户安装说明移除 `xattr -cr` 终端绕过命令。
- `安装说明.txt`：DMG 安装说明移除终端绕过方法。
- `docs/RELEASE_PROCESS.md`：把 `xattr -cr` 限定为开发者内部测试排查说明。
- `scripts/create_issues.py`：改为默认预演、release-only、使用 Python HTTP 请求并从环境变量读取 token。
- `scripts/tests/test_create_issues.py`：新增 GitHub Issue 发布脚本工作流测试。
- `ClipboardHistory/Sources/ClipboardHistoryApp/Managers/AppDelegate.swift`：About 面板许可证改为 WTFPL，并同步能力描述。
- `README.md`：同步视频内置播放器、图片文件预览和安装说明文案。
- `docs/ARCHITECTURE_REVIEW.md`：标注为 v1.2.1 历史快照。
- `docs/ARCHITECTURE_REFACTOR_2026_06_08.md`：同步当前媒体加载、视频预览、测试数量和人工冒烟说明。

## 整体架构思路

- `HistoryStore` 继续作为历史状态入口。
- `ClipboardWriter` 负责系统剪贴板写入边界，失败必须显式反馈给调用方；历史状态只有在写入成功后才能变化。
- `GlobalHotKeyController` 负责 Carbon 快捷键注册边界；设置层只根据注册结果更新偏好和提示，不假设回滚一定成功。
- `WindowConfigurator` 负责给真实 SwiftUI 主窗口补齐 AppKit 层面的稳定标识，`WindowManager` 只识别这个标识。
- `StoredImage` 代表图片内容，不代表某个 `NSImage` 对象实例；历史去重应基于内容。
- 图片去重目前仍是未闭环问题：单元测试里的 `StoredImage` 内容比较通过，不代表真实 App 剪贴板复制路径稳定。后续应把图片指纹作为可诊断、可持久化、可日志化的领域数据，而不是只依赖临时 `NSImage` 重新编码结果。
- `MediaLoader` 继续作为详情预览加载入口；文件不存在属于预览加载失败，而不是有效 fallback 预览。
- `ClipboardIntake` 继续负责剪贴板读取，但视频文件不再在 intake 阶段做重媒体处理；详情预览阶段再处理视频。
- `FileHistoryPersistence` 继续实现 `HistoryPersisting`，但默认磁盘写入已经从调用栈移到后台串行队列；`flushPendingSaves()` 是退出和测试的稳定性边界。
- `MediaLoader` 的后台任务只负责生成可安全跨线程的 payload；所有 `NSImage` 和 `FilePreview` 组装都在 MainActor 发生。
- `VideoPlaybackController` 负责播放器资源生命周期；SwiftUI 视图消失和 URL 切换都必须卸载旧 `AVPlayerItem`。
- 主窗口关闭在当前产品语义中是“隐藏应用”而不是销毁 SwiftUI 视图；视频播放不能只依赖 `onDisappear` 停止，必须响应主窗口隐藏事件并暂停播放。
- 边栏折叠功能不属于当前产品体验；macOS 14+ 优先使用 SwiftUI 原生移除接口，旧系统用 `WindowConfigurator` 清理工具栏按钮兜底，同时保持 v1.2.1 及以前的边栏位置、尺寸、红绿灯位置和窗口圆角关系。
- 隐私硬化优先选择不改变产品行为的底层保护；需要新 UI 或新用户决策的隐私功能先记录为暂缓。
- 收藏长期保存是当前明确产品行为；“清空全部，包括收藏”应作为独立新功能设计，不在本轮审查修复中实现。
- 菜单栏属于共享屏幕高暴露区域，默认使用隐私标题；主窗口仍保留完整查看体验。
- 文件路径在 UI 中默认脱敏到文件名；持久化层仍保存 URL 以维持文件再次复制能力。
- `ApplicationShell` 继续作为系统命令入口，后续会收口 macOS 13+ 菜单栏旁路。
- macOS 13+ `MenuBarExtra` 和 macOS 12 状态栏菜单都必须只发起“复制某个 entry id”的行为，由 `ApplicationShell` 在当前历史状态中重新解析并执行复制。
- 视频预览是独立的视图子域；`DetailFileView` 只负责根据 `FilePreview` 选择预览类型，不直接承载播放器生命周期细节。
- `ClipboardIntake` 的职责边界是读取系统剪贴板当前提供的数据；源文件内容读取、图片文件解码和视频元数据解析属于 `MediaLoader` 预览阶段。
- 发布脚本写入用户可见产物时必须能回滚；失败后不应留下半成品 DMG、checksum、release notes 或 changelog。
- 普通用户安装说明不应推荐绕过 Gatekeeper；本地测试包的隔离属性排查只应出现在内部发布流程文档中。
- 开发期问题追踪继续使用 `.scratch/` 本地 markdown；批量创建 GitHub Issue 只能作为 release 准备阶段的显式人工动作。
- 当前实现的公开文档优先以 README、CHANGELOG Unreleased、发布流程文档和本进度文档为准；旧架构审查报告必须标注为历史快照。

## 最终审计

对照 `docs/SUBAGENT_CODE_REVIEW_2026_06_08.md` 的 20 个问题：

| 编号 | 审查问题 | 处理结论 |
| --- | --- | --- |
| 1 | 剪贴板写回失败被当成成功 | 已修复，写入失败显式抛错且不置顶/不持久化 |
| 2 | 快捷键注册失败回滚不可靠 | 已修复，使用 probe 注册和明确结果 |
| 3 | 主窗口识别依赖不稳定 identifier | 已修复，主窗口使用稳定 identifier |
| 4 | 图片去重按对象身份判断 | 部分修复；对象身份问题已处理，但真实 App 中跨历史再次复制同图仍会重复，待继续诊断 |
| 5 | 文件丢失或移动后仍进入预览/复制流程 | 已修复，预览和写入前检查缺失 |
| 6 | 视频缩略图生成阻塞主线程 | 已修复，intake 阶段不再生成视频缩略图 |
| 7 | 持久化在 MainActor 同步全量写盘 | 已修复，磁盘写入转后台串行队列 |
| 8 | AppKit 对象跨线程传递 | 已修复，后台只返回安全 payload |
| 9 | 视频播放器资源释放不完整 | 已修复，停止/切换/拆卸时释放播放器资源 |
| 10 | 明文持久化剪贴板内容 | 已做权限硬化；隐私模式/加密属于新功能，暂缓 |
| 11 | 收藏绕过保留策略 | 已评估；保留“清空未收藏、收藏长期保存”的当前产品决策 |
| 12 | 菜单栏直接暴露最近内容 | 已修复，菜单栏使用隐私标题 |
| 13 | 文件路径在 UI 和 JSON 中暴露 | UI 已脱敏；JSON 保留 URL 以维持再次复制 |
| 14 | macOS 13+ 菜单栏快速复制绕过 `ApplicationShell` | 已修复，统一通过 shell 按 id 解析当前条目 |
| 15 | `DetailPreviewViews.swift` 过重 | 已处理，视频预览拆到同目录文件 |
| 16 | `ClipboardIntake` 仍承担媒体处理 | 已处理，文件 URL intake 不再同步读源文件缩略图 |
| 17 | 发布脚本失败回滚不完整 | 已修复，失败回滚发布产物和文档 |
| 18 | 发布/安装说明鼓励绕过 Gatekeeper | 已修复，普通用户文档移除绕过命令 |
| 19 | GitHub Issue 脚本与 `.scratch/` 工作流冲突 | 已修复，脚本改为 release-only 默认预演 |
| 20 | 文档与实现不一致 | 已修复当前公开文档；历史 release notes 保留旧版本事实 |

### 暂缓/不机械执行项

- 首次启动隐私说明、暂停记录/隐私模式、历史加密、退出时清除、敏感内容自动清理：属于新增产品功能，不在本轮“只处理审查修复、不新增功能”的范围内。
- “清空全部，包括收藏”和疑似敏感收藏二次确认：属于新增危险操作/新增确认流程，而且与用户之前要求“清空全部记录仅删除未收藏历史，保留收藏”冲突。
- JSON 存储层文件路径脱敏/bookmark data：会改变文件再次复制语义，属于更大存储设计，本轮只做 UI 脱敏。
- 正式 Developer ID 签名、公证、hardened runtime：需要 Apple 开发者证书和发布策略，不属于本轮代码修复。

### 风险与人工确认点

- 剪贴板历史仍会在本机持久化保存；目前已做文件权限硬化，但还没有产品化隐私模式或加密。
- 图片去重仍有真实 App 回归：隔几条记录后再次复制同一张图片仍会生成重复记录。下一轮先不要提交当前图片去重相关代码，优先构造能复现真实剪贴板路径的诊断日志或自动化回归。
- 文件记录仍依赖原始路径；原文件移动或删除后会明确失败，但不会自动重新定位。
- 视频预览和 QuickLook 真实渲染仍依赖 macOS 运行环境，自动测试只能覆盖核心状态和分支选择，需要人工冒烟确认。
- 本轮没有提交或推送；工作区仍包含大量未提交改动和 agent 工作流配置文件，提交前需要按用户确认的范围筛选。

### 当前最高优先级待办

1. 修复真实 App 中“隔几条记录后再次复制同一张图片仍生成重复记录”的问题。
2. 建议诊断顺序：
   - 在 `ClipboardIntake.readEntry` 和 `HistoryStore.add` 附近临时记录图片 pasteboard types、图片尺寸、bitmap 表示、指纹、历史中候选图片指纹。
   - 用真实 App 复现一次：复制图片 A，复制若干文本或文件，再复制图片 A。
   - 判断失败原因是新旧图片指纹不同、历史匹配只查了错误字段、持久化加载后丢失指纹，还是复制来源其实变成了文件 URL/图片两种不同 content。
   - 修复后补能覆盖真实原因的测试，再删临时日志。
3. 保留已确认通过的两项回归：
   - 关闭主窗口后视频停止播放。
   - 边栏右上角折叠按钮不再出现。

### 人工冒烟测试清单

- 文本复制、搜索、再次复制、快捷键再次复制。
- 图片内容复制、去重、详情预览。
- Finder 图片文件复制，确认历史记录进入文件类型，详情区加载图片预览。
- 文档文件复制，确认 QuickLook 预览。
- 视频文件复制，确认内置播放器预览、默认静音、播放控件进度条和右下角按钮不遮挡。
- 删除原文件后打开对应历史，确认显示“文件已移动或删除”，再次复制不清空现有剪贴板。
- 收藏、收藏筛选、清空未收藏后收藏保留。
- 菜单栏最近记录/收藏记录快速复制，确认不显示真实内容摘要。
- 呼出主窗口快捷键、再次复制快捷键修改与恢复默认。
- 菜单栏显示主窗口、设置、刷新历史、清空未收藏、退出。
- 重启 App 后确认历史持久化恢复，退出时最后一次修改已落盘。

### 2026-06-09 人工测试记录

- 未通过：隔几条记录后再次复制同一张图片仍然会生成重复记录。
- 通过：播放视频后点左上角关闭主窗口，视频正确停止播放。
- 通过：重新打开主窗口后，边栏右上角折叠按钮没有出现。

## 最近验证

- 2026-06-09 00:01：`swift test --package-path ClipboardHistory` 通过，68 个 Swift 测试，0 失败。
- 2026-06-09 00:14：`swift test --package-path ClipboardHistory` 通过，71 个 Swift 测试，0 失败。
- 2026-06-09 00:20：`swift test --package-path ClipboardHistory --filter WindowManagerTests` 通过，3 个测试，0 失败。
- 2026-06-09 00:20：`swift test --package-path ClipboardHistory` 通过，74 个 Swift 测试，0 失败。
- 2026-06-09 00:25：`swift test --package-path ClipboardHistory --filter HistoryStoreTests` 通过，14 个测试，0 失败。
- 2026-06-09 00:25：`swift test --package-path ClipboardHistory` 通过，75 个 Swift 测试，0 失败。
- 2026-06-09 00:36：`swift test --package-path ClipboardHistory --filter ClipboardWriterTests` 通过，1 个测试，0 失败。
- 2026-06-09 00:36：`swift test --package-path ClipboardHistory --filter MediaLoaderTests` 通过，9 个测试，0 失败。
- 2026-06-09 00:36：`swift test --package-path ClipboardHistory` 通过，78 个 Swift 测试，0 失败。
- 2026-06-09 00:40：`swift test --package-path ClipboardHistory --filter ClipboardIntakeTests` 通过，6 个测试，0 失败。
- 2026-06-09 00:40：`swift test --package-path ClipboardHistory` 通过，79 个 Swift 测试，0 失败。
- 2026-06-09 00:57：`swift test --package-path ClipboardHistory --filter FileHistoryPersistenceTests` 通过，6 个测试，0 失败。
- 2026-06-09 00:58：`swift test --package-path ClipboardHistory` 通过，80 个 Swift 测试，0 失败。
- 2026-06-09 01:05：`swift test --package-path ClipboardHistory --filter MediaLoaderTests` 通过，10 个测试，0 失败。
- 2026-06-09 01:06：`swift test --package-path ClipboardHistory` 通过，81 个 Swift 测试，0 失败。
- 2026-06-09 01:10：`swift test --package-path ClipboardHistory --filter VideoPlayback` 通过，7 个测试，0 失败。
- 2026-06-09 01:10：`swift test --package-path ClipboardHistory` 通过，83 个 Swift 测试，0 失败。
- 2026-06-09 01:15：`swift test --package-path ClipboardHistory --filter FileHistoryPersistenceTests` 通过，7 个测试，0 失败。
- 2026-06-09 01:15：`swift test --package-path ClipboardHistory` 通过，84 个 Swift 测试，0 失败。
- 2026-06-09 01:18：`swift test --package-path ClipboardHistory --filter HistoryStoreTests/testPerformSelectDeleteAndClearKeepsFavorites` 通过，1 个测试，0 失败。
- 2026-06-09 01:22：`swift test --package-path ClipboardHistory --filter EntryPresentationTests` 通过，6 个测试，0 失败。
- 2026-06-09 01:22：`swift test --package-path ClipboardHistory` 通过，85 个 Swift 测试，0 失败。
- 2026-06-09 01:26：`swift test --package-path ClipboardHistory --filter EntryPresentationTests` 通过，7 个测试，0 失败。
- 2026-06-09 01:26：`swift test --package-path ClipboardHistory` 通过，86 个 Swift 测试，0 失败。
- 2026-06-09 01:42：`swift test --package-path ClipboardHistory --filter ApplicationShellTests` 通过，2 个测试，0 失败。
- 2026-06-09 01:42：`swift test --package-path ClipboardHistory` 通过，88 个 Swift 测试，0 失败。
- 2026-06-09 01:46：`swift test --package-path ClipboardHistory --filter VideoPlayback` 通过，7 个测试，0 失败。
- 2026-06-09 01:46：`swift test --package-path ClipboardHistory` 通过，88 个 Swift 测试，0 失败。
- 2026-06-09 01:48：`swift test --package-path ClipboardHistory --filter ClipboardIntakeTests` 通过，7 个测试，0 失败。
- 2026-06-09 01:49：`swift test --package-path ClipboardHistory` 通过，89 个 Swift 测试，0 失败。
- 2026-06-09 01:51：`python3 -m unittest discover -s scripts/tests` 通过，8 个 Python 测试，0 失败。
- 2026-06-09 01:52：`swift test --package-path ClipboardHistory` 通过，89 个 Swift 测试，0 失败。
- 2026-06-09 01:54：`python3 -m unittest discover -s scripts/tests` 通过，8 个 Python 测试，0 失败。
- 2026-06-09 01:54：`swift test --package-path ClipboardHistory` 通过，89 个 Swift 测试，0 失败。
- 2026-06-09 02:00：`python3 -m unittest discover -s scripts/tests` 通过，11 个 Python 测试，0 失败。
- 2026-06-09 02:00：`swift test --package-path ClipboardHistory` 通过，89 个 Swift 测试，0 失败。
- 2026-06-09 02:03：`python3 -m unittest discover -s scripts/tests` 通过，11 个 Python 测试，0 失败。
- 2026-06-09 02:03：`swift test --package-path ClipboardHistory` 通过，89 个 Swift 测试，0 失败。
- 2026-06-09 02:48：`swift test --package-path ClipboardHistory` 通过，90 个 Swift 测试，0 失败。注意：该结果未覆盖真实 App 中图片跨历史重复问题。
- 2026-06-09 02:48：`python3 -m unittest discover -s scripts/tests` 通过，11 个 Python 测试，0 失败。
- 2026-06-09 02:53：人工测试确认视频关闭停止和边栏折叠按钮修复通过；图片跨历史重复问题仍未通过。

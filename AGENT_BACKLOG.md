# AGENT_BACKLOG · 模块 × 审计维度矩阵与待办

矩阵：10 模块 × 19 维度 = **190 格**。单元格含义：
`F:R-xx` = 已审计且有发现（见下方 backlog）· `OK` = 已审计且无问题 · `NA` = 不适用（附理由在"矩阵说明"）· `?` = **待审，必须归零**。

当前：**待审 0 · NA 48 · 有发现 114 · 已审无问题 28**（合计 190 格，判定率 100%）。

| 模块 | 正确性 | 边界 | 错误 | 并发 | 性能 | 内存 | 安全 | 可靠 | 兼容 | 无障碍 | 国际化 | 可观测 | 测试 | 类型 | 构建 | 打包 | 迁移 | 回滚 | 文档 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| M1 入口/生命周期  | F:R-03 | F:R-52 | F:R-13 | F:R-11 | F:R-01/R-21 | OK | F:R-13 | F:R-02 | F:R-24 | F:R-54 | F:R-31 | F:R-01 | F:R-26 | F:R-01 | OK | F:R-34 | F:R-20 | F:R-35 | F:R-33 |
| M2 核心·剪贴板  | F:R-04/R-05 | F:R-22 | F:R-04 | F:R-19 | F:R-08/R-23 | F:R-22 | F:R-06 | F:R-05 | F:R-24 | NA | F:R-31 | F:R-01 | F:R-26 | OK | OK | NA | F:R-20 | F:R-22 | F:R-33 |
| M3 数据·持久化  | OK | F:R-22 | F:R-02 | OK | F:R-07 | F:R-07 | F:R-06/R-30 | F:R-02 | F:R-20 | NA | NA | F:R-02 | F:R-26 | OK | OK | F:R-34 | F:R-20 | F:R-02 | F:R-33 |
| M4 状态·推荐  | F:R-17/R-18 | F:R-55 | F:R-16 | F:R-11/R-19 | F:R-09/R-11 | F:R-06 | F:R-06 | F:R-11 | F:R-06 | NA | F:R-18 | OK | F:R-26 | F:R-19 | OK | NA | OK | OK | F:R-33 |
| M5 UI·视图与窗口  | F:R-40 | F:R-27 | F:R-41 | OK | F:R-09/R-10 | F:R-42 | F:R-43 | F:R-40 | F:R-24 | F:R-54 | F:R-31 | F:R-01 | F:R-27 | OK | OK | NA | NA | NA | F:R-33 |
| M6 网络  | NA | NA | NA | NA | NA | NA | F:R-44 | NA | NA | NA | NA | NA | F:R-44 | NA | NA | NA | NA | NA | F:R-44 |
| M7 构建  | F:R-15 | F:R-53 | F:R-15 | OK | OK | NA | F:R-34 | F:R-15 | F:R-24 | NA | NA | F:R-15 | F:R-45 | OK | F:R-15 | F:R-34 | F:R-15 | F:R-35 | F:R-33 |
| M8 测试  | F:R-01 | F:R-26 | F:R-26 | F:R-28 | F:R-29 | F:R-29 | F:R-45 | F:R-01 | F:R-24 | F:R-27 | NA | F:R-01 | F:R-26 | F:R-28 | OK | NA | F:R-20 | OK | F:R-46 |
| M9 文档  | F:R-33 | NA | NA | NA | NA | NA | F:R-33 | NA | F:R-33 | NA | NA | OK | F:R-33 | NA | F:R-33 | NA | F:R-33 | F:R-35 | F:R-33 |
| M10 依赖  | OK | NA | NA | NA | OK | OK | F:R-47 | OK | F:R-24 | NA | NA | NA | NA | OK | OK | OK | NA | F:R-35 | F:R-47 |

## 最后 15 格的判定（本轮填平，待审归零）

| 格 | 判定 | 依据 |
|---|---|---|
| M1×边界 | F:R-52 | 没有任何「已经有一份在跑」的检查 ⇒ 两个实例各自整库写 history.json，后写的整片盖掉先写的记录；而 `make run` 用的正是 `open -n`。已修（83d3a11） |
| M1×内存 | OK | `applicationWillTerminate` 成对 removeObserver 并摘掉 Apple Event handler；`stopMonitoring()` 同时 cancel 延迟任务、invalidate 定时器、移除前台切换观察者；`WindowManager` 持窗口用 weak |
| M1×无障碍 | F:R-54 | 启动后焦点归属（窗口是否成为 key、⌘, 之后焦点在哪）无法在离屏环境验证；与 M5×无障碍同一处置 |
| M1×打包 | F:R-34 | bundle 缺 NSPrincipalClass / CFBundlePackageType / 用途描述也能「构建成功」；现在由模板 + 脚本生成并逐键校验 |
| M1×迁移 | F:R-20 | 见 D-012：读到更高 version 就只读打开，不覆盖 |
| M2×无障碍 | NA | 剪贴板采集/写入这一层没有界面元素；无障碍问题全部落在 M5（见 R-54） |
| M2×迁移 | F:R-20 | intake 产出的条目结构与存档同版本；降级只读闸门同样覆盖这一层 |
| M4×边界 | F:R-55 | 补 8 条边界用例（空历史、单条、limit 0/负数、500 条、全 0 权重、未来时间戳、重复 id、隐私开关两侧）；其中「重复 id」暴露出真实缺陷并已修 |
| M4×兼容 | F:R-06 | 旧反馈 blob 与新精简快照互相兼容解码；缺字段容错，不要求重写用户数据 |
| M5×边界 | F:R-27 | 离屏帧覆盖最小 600×440 / 放大 1100×800 / 空 / 无结果 / 多选 / 收藏筛选 / 提示条插入后的布局 |
| M5×并发 | OK | Swift 6 严格并发下 0 告警（不是靠 nonisolated(unsafe) 静音）；OCR、预测、保存的回调一律 hop 回主线程 |
| M5×无障碍 | F:R-54 | 收藏状态只靠 .clear/.yellow 表达、help 不等于 accessibilityLabel、离屏窗口根本不建无障碍树 ⇒ 只能做代码级检查，VoiceOver 实测在本环境无法完成 |
| M7×边界 | F:R-53 | 实测复现：`.build/x86_64-apple-macosx` 被部分删除后 `make build` 报 swift-version not registered 并卡死，只能整目录清掉；`|| true` 类吞错已收干 |
| M7×迁移 | F:R-15 | 20 行 PlistBuddy ⇒ 模板 + scripts/make_info_plist.sh，可单测、可回滚（还原 Makefile 即回旧路） |
| M9×迁移 | F:R-33 | 数据格式变更的说明进 AGENT_DECISIONS.md（D-012/D-013），带日期的旧文档统一加「历史快照」横幅 |


---

## Backlog（按价值排序；高=必须做，中=应该做，低=只记录不强行改）

状态标记：`待办` / `进行中` / `已完成(提交号)` / `记录不改(理由)`

**进度**：高价值 6 项中 R-01…R-06 已完成；性能主线 R-07…R-10 已完成（实测见 AGENT_STATE.md）；R-48 排序确定性、R-49 注入失效、R-50 测试环境依赖 为本轮新发现并已关闭。

### 高价值 · 数据丢失、信任面、质量闸

| ID | 项 | 证据（file:line） | 修复方案 | 验证方式 | 价值 | 状态 |
|---|---|---|---|---|---|---|
| R-01 | 删 `_isEnabledOverride`，日志移到 `~/Library/Logs` | `Utilities/LifecycleDebugLogger.swift:7-9`；HEAD 版本是 env 门控 | 只保留 `CLIPBOARD_HISTORY_DEBUG=1` 门控；路径改 `~/Library/Logs/时间剪史/`，目录 0700；OCR 日志并入同一开关 | `swift test` 退出码 0 且 `Executed N≈135`；`ls /tmp/*.log` 不再新增 | 高 | 已完成(cb8db30) |
| R-02 | 存档损坏时禁止覆盖写 + 保留原件 | `Managers/HistoryPersistence.swift:111-116,356-369`；探针 P-06（图片 2→0） | `load()` 区分"文件不存在/解析失败"；失败时改名 `history.corrupt-<ts>.json` 并进入"只读不覆盖"态；`removeUnusedImages` 仅删本次已知文件 | 新增单测：写半截 JSON → 载入 → add → 断言旧图片仍在、原件被保留 | 高 | 已完成(0792e6b) |
| R-03 | 菜单栏"清空未收藏"必须二次确认 | `Managers/MenuBarController.swift:154,226-228` → `ApplicationShell.swift:168-169`；带 alert 的函数无调用者 | `.clearHistory` 改走 `confirmAndClearHistory()`；删除无人使用的 `AppDelegate.confirmAndClearHistory` 转发 | 新增单测（注入确认器）：未确认 ⇒ entries 不变；确认 ⇒ 只删未收藏 | 高 | 已完成(cc0c2df) |
| R-04 | 浏览器链接被当文件条目、回写必失败 | `Managers/ClipboardIntake.swift:100-110`；探针 P-15 `.file(https://…)` | `readObjects` 加 `.urlReadingFileURLsOnly: true` | 新增单测：pasteboard 放 http NSURL ⇒ 结果为 `.text` | 高 | 已完成(cc0c2df) |
| R-05 | 重复复制丢失来源 App 归因 | `Managers/HistoryStore.swift:831-847`；探针 P-01 | `entry(from:replacingWith:)` 保留 `sourceAppBundleID/sourceAppName`（intake 优先，回退旧条目） | 翻转探针 P-01 为期望行为断言；夹具 `TestSupport.makeClipboardEntry` 增加来源参数 | 高 | 已完成(cc0c2df) |
| R-06 | 反馈载荷内嵌剪贴板原文，清空历史不清 | `Intelligence/RecommendationFeedbackStore.swift:68-79`、`Intelligence/ClipboardEntryIntelligenceAdapter.swift:57-68`；探针 P-05 | 反馈只存 `entryID/kind/createdAt/轻量上下文`（不含 recentEntries）；`clearAll`/`delete` 级联清理；旧数据兼容解码（缺字段容错） | 单测：编码后 JSON 不含 preview；清空后 feedback 为空；旧格式 plist 仍能解码 | 高 | 已完成(0792e6b) |
| R-07 | 每次保存主线程重编码全部 PNG | `Managers/HistoryPersistence.swift:141-146,184-192,276-285`；P-12 = 667.8ms | `StoredImage` 缓存 PNG 字节；快照只对"库里没有的文件名"编码；`save` 加去抖 + `cancel` 旧任务 | 基准测试：12 张图的库，第二次保存 <50ms；`persist` 合并后队列任务数=1 | 高 | 已完成(f8ce4dd) |
| R-08 | 图片指纹整幅绘制 + SHA256（主线程） | `Models/StoredImage.swift:52-90`；P-07 单张 7.4ms、P-14 启动 605.8ms | 指纹优先用"尺寸 + 原始字节哈希"，仅在无字节时回退像素哈希；保持 `==`/`hash` 语义 | 基准：8 张 2000×1500 载入 <150ms；去重语义单测不变（跨 pasteboard 往返仍相等） | 高 | 已完成(f8ce4dd) |
| R-09 | 派生列表与预测重复全表计算 | `Managers/HistoryStore.swift:55-82,143,146`；P-20 = 14.07ms/次，一帧多次 | `filteredEntries` 改为在 `searchText`/`filter`/`entries` 变化时算一次的缓存值；预测流程只走一遍 summaries+intelligence | 基准：500 条 + 搜索词一次 <3ms；视图不改动语义 | 高 | 已完成(f8ce4dd) |
| R-10 | 大文本预览/尺寸文案 O(n) | `Models/EntryPresentation.swift:15-43`；P-18 单条 45.7ms、整表 916.6ms | 先按 `utf16`/前缀截断再替换与判长；`sizeDescription` 用 `utf16.count` | 基准：2.4MB 文本单条 preview <1ms；文案输出与今天逐字一致（保留旧断言） | 高 | 已完成(f8ce4dd) |
| R-11 | 预测无代际防护 + 2s 轮询 | `Managers/HistoryStore.swift:145-289`、`Views/MenuBarRecommendationsView.swift:8,53-55` | 加 `predictionGeneration`，回主线程丢弃过期代；刷新改事件驱动（打开菜单/新复制/前台切换），删 2s 定时器 | 单测：连投两次预测，旧代结果被丢弃；CPU：静置 60s 内不再出现预测重算 | 高 | 已完成(cb3a69b) |
| R-13 | Info.plist 缺 Apple Events 用途描述 + 授权失败不可见 | `时间剪史.app/Contents/Info.plist`（11 key）、`ApplicationShell.swift:150-157`、`LoginItemSettings.swift:45-83` | 构建脚本写入 `NSAppleEventsUsageDescription`；osascript 失败（退出码/stderr）落到可见状态与日志；`AXIsProcessTrusted` 状态在设置页显示 | 单测：注入失败的 paste 执行器 ⇒ UI 状态为"未授权/失败"而非静默 | 高 | 已完成(654a787,1d442f5) |
| R-12 | README 三条与行为相反的承诺 | `README.md:19,24,96-97` vs `MenuBarRecommendationsView.swift:27`、`MenuBarController.swift:141-142` | 二选一并记录：加"粘贴前确认/长按"或把文档改成真实描述；同步"侧边栏 Magic"“刷新历史”两处虚描述 | 逐条 grep 复验；视觉审计确认菜单实际项 | 高 | 已完成(1d442f5) |

### 中价值 · 行为正确性、稳健性、契约

| ID | 项 | 证据 | 方案 | 验证 | 价值 | 状态 |
|---|---|---|---|---|---|---|
| R-15 | 构建脚本：版本 5 处来源、`|| true` 吞错、PlistBuddy 20 行拼 plist | `Makefile:2,26-58`、`scripts/prepare_release.py:209-224` | 引入 `Resources/Info.plist` 模板 + 单一版本源；`prepare_release` 校验 DMG mtime 晚于构建开始；收窄 `|| true` | `make dmg` 产物含用途描述；故意让一步失败时脚本非 0 退出 | 中 | 已完成(1d442f5) |
| R-16 | 敏感过滤误报（前缀表命中普通词） | `Intelligence/RuleBasedRecommendationEngine.swift:136-139`；P-03 = 2/4 误报 | 前缀需紧跟 ≥12 位 `[A-Z0-9]`；对全文计算一次并缓存标记 | 单测：`ASIA-East…`、`AROA …` 不再判敏感；`ghp_…`/`sk-…` 仍判敏感 | 中 | 已完成(cb3a69b) |
| R-17 | 推荐"复用 N 次"随权重显示错误数字；权重全 0 仍打分 | `Managers/HistoryStore.swift:193`、`RuleBasedRecommendationEngine.swift:63-64`；P-02 | 文案直接用 feedback 计数；hybrid 分数乘 `weights.recency` | 单测：权重 0.5 ⇒ 次数不变；全 0 ⇒ 排序退化为收藏/时间为序 | 中 | 已完成(cb3a69b) |
| R-18 | Finder 目录因子不可达 + 6 位数字过度标注 | `RuleBasedRecommendationEngine.swift:236-249` vs `ClipboardEntryIntelligenceAdapter.swift:57-68`；P-04 | summary 带上目录路径使因子可达；验证码规则要求"验证码/短信/校验"上下文词 | 单测：同目录文件得 1.0；`会议室 823417` 不再标 verificationCode | 中 | 已完成(cb3a69b) |
| R-19 | `@unchecked Sendable` 让 NSImage 进后台 | `Models/ClipboardEntry.swift:3`、`StoredImage.swift:4`、`HistoryStore.swift:145-146` | detached 任务只接收 `ClipboardEntrySummary`（值类型），NSImage 不入后台 | `swift build -Xswiftc -strict-concurrency=complete` 告警数下降；行为不变 | 中 | 已完成(cb3a69b) |
| R-20 | 历史数据 version 字段从未做迁移；时钟异常即批量丢弃 | `HistoryPersistence.swift:188`（`version: 1` 从不读）、P-16 | 载入时按 version 走显式迁移函数（当前 v1→v1 占位）；~~过期项移到 `history.expired.json`~~ **这一半从未实现，2026-10-09 更正：已被 D-012 的 NoticeBanner 取代**（成批过期出可关闭提示并写日志，不移文件） | 单测：version=2 的存档能载入；41 天条目不被静默删除（现为"出提示"，见 `ArchiveVersionAndRetentionTests`） | 中 | 已完成(6c08620)；expired 文件部分记录不改（D-012，R2-14 关闭） |
| R-21 | 三个轮询从不暂停（电池） | `HistoryStore.swift:344,626`、`MenuBarRecommendationsView.swift:8` | App 切换改 `NSWorkspace.didActivateApplicationNotification`；失焦时降频/暂停 | 实测静置 60s 的定时器触发次数（前/后） | 中 | 已完成(cb3a69b) |
| R-22 | 无剪贴板体积/张数上限 | `ClipboardIntake.swift:80-83`、`MediaLoader.swift:124-127`、P-08（2MB 入库） | 文本 256KB 截断标记；预览读 256KB；图片像素上限只存缩略 | 单测：2MB 文本入库后 `content` 有截断标记且 <阈值；预览不含全量 | 中 | 已完成(50e5a4e) |
| R-23 | 图片/文件条目的 OCR 取帧在主线程 | `HistoryStore.swift:528-556`（`scheduleOCRIfNeeded` 同步 `NSImage(contentsOf:)` + `cgImage(forProposedRect:)`，只有 Vision 调用进了后台队列）；启动路径 `ApplicationShell.swift:50 → scheduleOCRForExistingImages()` 对**每一张**待 OCR 图片各跑一遍；P-13 = 16.9ms/张 | 取帧移到后台队列，主线程只写回 `ocrText` | 单测：`add` 期间无 `NSImage(contentsOf:)` 主线程调用（以计时/替身验证） | 中 | 已完成(4324441) |
| R-24 | macOS 12/13/14 三条分支的**运行时**行为无法在本机验证 | `App.swift`、`ContentView.swift`、`MenuBarController.swift`、`ViewExtensions.swift` 等 11 处可用性守卫 | 编译期已经有闸：`Package.swift` 声明 `.macOS(.v12)`，任何未按版本守卫的新 API 都会编译失败，CI 每次都编两个 triple。**运行时**需要 12/13/14 三套系统，本机（macOS 27 beta）拿不到 ⇒ 记为已知限制，不做假验证 | `swift build` 通过 = 编译期结论；运行时结论一律标注「未验证」 | 中 | 记录不改(环境不可得) |
| R-26 | 测试覆盖缺口（本次全部缺陷都无守卫） | `Tests/` 23 文件 135 用例名清单 | 为 R-02..R-11 各补 1–2 条回归用例；夹具支持来源 App 与损坏存档 | 用例数上升且全部执行（退出码 0） | 中 | 已完成(195 例全绿) |
| R-27 | UI 层零测试 + 视觉从未验证 | `GlassControls`/`HistoryRowViews`/`WindowConfigurator` 无测试 | 新增离屏渲染工具 target 产出真实像素；关键视图加像素/布局断言 | 快照文件存在且肉眼检查记录在 `AGENT_UI_AUDIT.md` | 中 | 已完成(95b4301) |
| R-28 | 并发/异步测试缺失（预测竞态、取消） | `HistoryStore.swift:145-289` | 用可控时钟 + 假服务写竞态测试；`Task` 取消路径测试 | 新用例能通过"删掉代际防护"变异打出红 | 中 | 已完成(cb3a69b) |
| R-30 | `/tmp` 可预测路径 + 跟随符号链接截断 | `LifecycleDebugLogger.swift:9,12-18`、`HistoryStore.swift:607-619` | 与 R-01 合并：日志进 `~/Library/Logs`，写前先判断是否为符号链接 | 单测：路径为 symlink 时拒绝写；目录权限 0700 | 中 | 已完成(cb8db30) |
| R-31 | 国际化：仅中文硬编码，无本地化资源 | `Package.swift:15-18`（只打包图标）、各界面字符串、`docs/ISSUE_STATUS_REPORT.md:28` | 判定：产品定位就是中文单语言，**不做本地化改造**；但把用户可见字符串集中到一处（现有 `AppCommand`/`HistoryPrivacyCopy` 已部分做到），并修 `EntryPresentation` 中混排的表情符号 | 记录不改（低价值改造成本高）| 中 | 记录不改 |
| R-33 | 文档与代码不符（20+ 条） | `docs/ARCHITECTURE_REVIEW.md:60,96`、`docs/CODE_REVIEW_v1.4.4.md:77-80`、`CLIPBOARDHISTORY_HANDOFF.md:9,10`、`安装说明.txt:2`、`CHANGELOG.md` 顺序 | 逐条更正；把"测试全绿"改为带执行数；`AGENTS.md` 不再声称 `CONTEXT.md`/`docs/adr/` 存在 | 每条更正后 `grep` 复验 | 中 | 已完成(4b95b12) |
| R-34 | 打包内容：无 entitlements、无用途描述、quarantine 被剥、DMG 无校验文件 | `Makefile:46-58,63-72`；`spctl` rejected | 打包阶段生成 `Info.plist` 全量键；`make dmg` 同时产出 `.sha256`；文档写清真实报错与解法 | `plutil -p` 含用途描述；`shasum -a 256 -c` 通过 | 中 | 部分完成(1d442f5) |
| R-35 | 回滚：数据格式/目录变更没有可回退路径 | `HistoryPersistence.swift:159-165` | 所有数据布局改动都走"新写旧读"，保留 `history.json` 原名与 v1 兼容；迁移前自动 `.bak` | 单测：新格式写入后，旧版本可读回（字段不删只加可选） | 中 | 已完成(36768e8) |
| R-40 | UI 行为缺陷：`rowFrames` 只增不减（拖选可能命中已消失行） | `Views/HistorySidebarView.swift:7,183-193` | 用最新一帧完整字典替换，或按可见 ID 裁剪 | 视觉/交互验证 + 单测（若可抽纯函数） | 中 | 已完成(50e5a4e) |
| R-41 | UI 错误态：视频宽高拿不到时画 16:9 空播放器 | `Managers/MediaLoader.swift:129-131`、`DetailPreviewViews.swift:254-266` | 无比例 ⇒ 显示"无法读取视频信息 + 在 Finder 中显示" | 快照对比 | 中 | 已完成(50e5a4e) |
| R-42 | UI 内存：详情整解大图、QuickLook/PlayerLayer 常驻 | `DetailPreviewViews.swift:148`、`VideoPreview.swift:46,50` | 预览按需缩放解码（`NSImage` 只取所需尺寸）；KVO observer 在 `deinit`/`stop` invalidate | 长时间切换条目的内存曲线 | 中 | 已完成(95b4301) |
| R-43 | UI 隐私：菜单/详情直接暴露正文与完整父目录 | `MenuBarController.swift:91`、`Views/DetailView.swift:319`、`EntryPresentation.swift:45`（无调用者） | 恢复脱敏标题（`menuTitle` 已存在）；多文件行显示相对/截断路径；`EntryPresentationTests` 断言改回"不含正文" | 快照 + 单测 | 中 | 已完成(50e5a4e) |

### 低价值 · 只记录，不强行改

| ID | 项 | 证据 | 判定 | 价值 | 状态 |
|---|---|---|---|---|---|
| R-14 | 死代码：`HistoryPrivacyCopy` 已接入隐私页（见 D-013）；`registerMainWindow` 已有调用者；剩余 AI 层与 `docs/ai/` 保留为设计稿（AI 层 250 行、`HistoryPrivacyCopy` 未接入、`menuTitle`、`recordIgnored/Reverted/reset/forEntry`、`switchPattern`、`markCurrentChangeCount`、`reset*Shortcut`、`registerMainWindow`、侧栏 Magic 状态、孤儿注释、空 `if let`） | `02-确认缺陷.md` D-1 全清单 | **选择性做**：删空 `if let`（唯一告警）、把 `HistoryPrivacyCopy` 接入隐私页（有价值的文案）、`registerMainWindow` 补调用或删死分支；AI 层与 `docs/ai/` 保留但标注"设计稿"（删除会毁掉设计意图记录） | 低-中 | 部分完成(隐私文案已接入) |
| R-16b | `ocrLog` 无条件写 | 并入 R-01/R-30 | 低 | 已完成(cb8db30) |
| R-25 | `CompatibleSplitView` 双宽度约束冗余 | `SettingsView.swift` 尾部 | **不改**：本机 macOS 13+，该分支不可达，删了无法视觉复验；与 R-24 同一处置 | 低 | 记录不改 |
| R-29 | 测试无性能基准；本轮引入 4 条基准用例后需注意其耗时 | 新增 `PerfBudgetTests` | 基准用"上界断言"，设宽松阈值避免抖动 | 低 | 已完成(4324441) |
| R-32 | 快捷键键名表 59 项手写、未覆盖符号键 | `HotKeyShortcut.swift:82-144` | 只补 `/`、`-`、`=`、`[`、`]`，不引入 `UCKeyTranslate` | 低 | 已完成(本提交) |
| R-36 | 9 个推荐滑杆可减到 3 个 | `RecommendationWeights.swift` | **不做**：用户可自定权重是产品卖点，R-17 修好后才有意义 | 低 | 记录不改 |
| R-37 | 拆 `HistoryStore` | 848 行 | **不做**：只搬 95 行推荐理由文案 | 低 | 记录不改 |
| R-38 | 历史改 SQLite / 加密 / 沙箱 / 云同步 | — | **不做**（推翻既有承诺，成本高于收益） | 低 | 记录不改 |
| R-39 | 严格并发全改造以零警告 | — | **不做**：只做 R-19 的边界收敛 | 低 | 记录不改 |
| R-44 | 网络维度整体不适用 | `Sources` 内无 `URLSession`/`NWConnection`；`AIProviderModels` 是纯类型 | 保留一条守卫测试：断言产品 target 不出现网络 API 符号（这是"本地优先"承诺的机器化） | 低-中 | 已完成(cb8db30) |
| R-45 | 无 CI | 仓库无 `.github/workflows` | 加一个最小 workflow（build 零告警 + `Executed N` 只准涨不准跌 + python 用例数下限 + Info.plist 闸）；**启用需 push**，本轮只把闸放进仓库 | 中 | 已完成(已在 main 上跑绿，7 步全 success) |
| R-46 | `docs/agents/*` 引用 `.scratch/` 约定但目录为空；`AGENTS.md` 声称 `CONTEXT.md`/`docs/adr/` 存在 | `AGENTS.md:13` | 更正 `AGENTS.md`；`.scratch/` 保持空或写入首条 PRD | 低 | 已完成(4b95b12) |
| R-47 | `skills-lock.json` + `.agents/skills`（30+ 第三方技能文件）是仓库内唯一外部来源内容 | `.agents/`（曾未跟踪） | 纳入跟踪或明确声明"不属于产品"；不做代码改动 | 低 | 已完成(声明为非产品资产) |
| R-34b | 发布链路剩余：`quarantine` 被 `xattr -cr` 剥掉、ad-hoc 签名被 `spctl` 拒绝、无 entitlements（`make dmg` 现在已产出 `.sha256` 并自校验） | `Makefile:46-58,63-72`；审计 06 附 6.2(3) 实测 rejected | **不改**：本机自用场景下公证需要 Developer ID（Roadmap 已列）；README 已写清真实报错与解法 | `spctl` 仍 rejected（记为已知限制，不是回归） | 中 | 记录不改 |
| R-52 | 第二实例会整片覆盖第一实例写入的存档（数据丢失） | `AppDelegate.applicationDidFinishLaunching` 原先没有任何「已在运行」检查；`Makefile` 的 run 目标用 `open -n` 强制新实例 | `InstanceGuard`：纯函数判定 + 适配器读真实进程列表；命中即记日志并静默退出（不弹窗，与 macOS 对单实例 App 的常规行为一致） | `InstanceGuardTests` 7 条（含「自己不算冲突」「已退出的实例不算」「无 bundle id 时放行」）；适配器那条拿 Finder 做真实数据 | 高 | 已完成(83d3a11) |
| R-53 | `.build/<triple>` 被部分删除后 make build 卡死 | 实测：删掉 `.build/x86_64-apple-macosx` 后 `swift build --triple` 报 swift-version not registered 与 missing inputs: DerivedSources/resource_bundle_accessor.swift，失败点在 build 阶段（本轮真实撞到两次，第三次靠 `rm -rf .build` 才通） | make 检测到该报错时提示「先 rm -rf ClipboardHistory/.build 再试」；或把这条恢复路径写进 README 编译方法 | 复现命令能稳定触发；改后给出可执行提示而不是裸报错 | 中 | 已完成(本提交) |
| R-54 | 无障碍：收藏状态与纯图标按钮读不到；焦点无法验证 | `HistoryRowViews.swift` 用 `.foregroundStyle(isFavorite ? .yellow : .clear)` 表达收藏；`GlassPill`/`bulkActionButtons` 只有 `.help()`；离屏窗口不建无障碍树（实测 BFS 只走到根节点） | 给收藏星标与图标按钮补 `accessibilityLabel`；Tab 焦点顺序需要真机 VoiceOver，本机环境做不到 | 单测只能锁 label 存在；VoiceOver 朗读结果记为未验证 | 中 | 已完成(ba707d4) |
| R-55 | 同一个 entryID 可以占掉两个推荐名额 | `RuleBasedRecommendationEngine.recommend` 逐条生成候选，不按 id 去重；存档可被手改或从半截恢复出同 id 两条，界面按 id 回查会让 Top 3 显示成两行同样内容 | 排序后、截断前按 entryID 去重 | `RecommendationBoundaryTests` 8 条边界用例覆盖；重复 id 那条在修复前确实变红 | 中 | 已完成(4bb02ef) |
| R-51 | 图片去重要为每张新图算一次 64px 采样：稳态一次 83ms，启动后第一次比较 147ms（3200x2100，主线程） | `Models/StoredImage.swift` 的 `sampledFingerprint(fromPNG:)`；`HistoryStore.add` 只与 `entries.first` 比较，故每次复制最多一对 | **不改**：本轮实测推翻了原设想。把采样值随存档持久化只能省掉「启动后第一次」那一侧的 64ms，省不掉新图自身那次采样 —— 而做到与编码方式无关的去重（TIFF 往返必须认得是同一张）恰恰依赖那次采样。代价却是数据格式变更 | `PerfBudgetTests` 已把 147/83ms 两个数字钉住（含「一侧焐热后必须更快」这条缓存共享断言），将来要优化有基线 | 中 | 记录不改(实测收益不足) |

## 发布前检查单（全部为绿才写最终报告）

- [ ] `swift build` 零告警（当前 **0 条**；判据 `swift build > /tmp/b.log 2>&1; grep -c 'warning:' /tmp/b.log`）
- [ ] `swift test` 退出码 0 且 `Executed N tests` ≥ 源码用例数（当前 229 例 / 1 skip / 0 失败；判据 `grep -E 'Executed [0-9]+ tests' /tmp/test.log | tail -1`）
- [ ] `python3 -m unittest discover -s scripts/tests` OK（当前 18 例；**必须在仓库根目录跑**）
- [ ] 性能基准达标签（R-07..R-10 的上界）
- [ ] 视觉审计：所有关键视图 + 暗亮色 + 边界尺寸有快照且逐张看过，缺陷修复后重拍
- [ ] 矩阵 `?` 归零
- [ ] backlog 无"高/中价值 且 状态≠已完成/记录不改"
- [ ] `AGENT_DECISIONS.md` 覆盖所有数据/接口/依赖/架构改动，且每条写明回滚方式
- [ ] `git log` 每项一个可 revert 提交；工作区与 HEAD 一致

## 第二轮（2026-10-09）待办 · R2-*

来源：`/Users/wangziyi/Documents/时间剪史_审计_2026-10-09_第二轮/`。价值排序即下面的顺序；
每条动手前先在当前代码上复核一遍（审计清单也会掺误报），做完要有会红的测试 + 变异对照。

**进度快照（2026-10-09 本轮结束时，以下表为准，上面那张清单的状态列可能已滞后）**：

- 已完成：**R2-01**（N-1 端到端守卫 + 变异对照，`ca12531`）· **R2-03**（9 处亮色 chrome，`6a2c040`）·
  **R2-04**（保存不再重写未变图片 + 取消被取代的落盘，`9ac4661`）· **R2-06**（Return 变成取消，`a841337`）·
  **R2-07**（来源 App 落盘，见 D-016，`d8d11f4`）· **R2-09**（非法符号 + 菜单空态 + spinner 兜底，`1214526`）·
  **R2-10**（pill 减少动态门控，`2438aa6`）· **R2-11**（有界字符计数并把 20ms 上界收回 5ms，`8cfdfe5`）·
  **R2-02 的一部分**（搜索框焦点环 + 列表可聚焦 + 方向键 + 行 selected 语义 + 清除按钮标签，`d4edf1f`）。
- 仍待办：**R2-02 的剩余验证**（需人工开「完全键盘访问」后用 `UIInteractionProbeTests` 复测 Tab 能否到达列表行）·
  **R2-05** 拖拽 · **R2-08** 图片像素上限 · **R2-12** 粘贴前复核目标 App · **R2-13** 行时间戳 10pt ·
  **R2-14** 文档更正 · **R2-15** AI 脚手架移出产品路径 · **R2-16** 待决策 · **R2-17** 菜单栏面板的 store 注入接缝 ·
  UI 批次 A 的剩余两处（设置侧栏符号风格统一、GlassPill 图标重量统一）。
- 新增：**R2-18** 视觉捕获仍有 30/58 帧的时序噪声（同一份代码连拍两次即有 0.02–0.46% 差异、最大通道差 127，
  集中在 `row-*`/`sidebar-*`/`content-*`/`detail-*`），所以"逐帧对比无回归"这类结论必须**同时**给出同代码连拍的对照；
  根治办法是在 harness 里让动画先落定（捕获前跑一段 runloop 或禁用 transaction 动画），尚未做。

**进度快照 2（本轮收尾时）**：

- 又完成：**R2-05**（拖出条目，`d463ef9`；多文件条目刻意不给拖拽，真机拖放未验证）·
  **R2-08**（4096px 上限，`1183f9f`，D-017，含端到端采集用例与变异对照）·
  **R2-12**（粘贴前复核目标 App，`d218803`，含"复核在注入之前"的顺序守卫与变异对照）·
  **R2-13 的行时间戳部分**（10pt→11pt，同提交；菜单理由行已在 `1214526` 改过）。
- 仍待办：**R2-02 的在屏复测**（需人工开「完全键盘访问」）· **R2-14** 文档更正 · **R2-15** AI 脚手架移出产品路径 ·
  **R2-16** 待决策 · **R2-17** 菜单栏面板的 store 注入接缝 · UI 批次 A 剩两处（设置侧栏符号风格、GlassPill 图标重量）。
- 新增：**R2-19** 捕获夹具的行时间戳用 `Date()`（`UICaptureHarness.swift:254-277`），跨分钟连拍时**时钟字符串本身**
  就会改变像素 —— 这是 R2-18 噪声的一个可消除来源（本轮 row 帧 3.3–13% 的差异里混着它）。
  修法：夹具改用固定参考时刻；改完要重测噪声底噪，预期 row/sidebar 帧降到接近 0。

| # | 审计出处 | 价值 | 状态 | 内容 |
|---|---|---|---|---|
| R2-01 | 02 §A N-1 | 高 | **待办（实现已改，守卫未补）** | 补"存档含同 id 两条 ⇒ 预测刷新不崩且只出一条"的**端到端**用例：走 `HistoryStore` 的预测刷新路径，不走 `engine().recommend`（`RecommendationBoundaryTests:96-103` 正是这样绕过了 adapter，所以 `876c015` 之前一直是绿的）。做完用变异对照证明：把实现改回 `Dictionary(uniqueKeysWithValues:)` ⇒ 该用例必须红/崩 |
| R2-02 | 03 §3.1 / §1.10 | 高 | 待办 | 键盘焦点链。实测 14 次 `selectNextKeyView` 全落在同一个 `NSTextView`；`ChineseTextContextMenu.swift:40` 把搜索框 `focusRingType` 设成 `.none`；全仓 `.buttonStyle(.plain)` 无焦点环、无 `.focusable()`/`@FocusState`。**不采纳**"整体换 `List(selection:)`"（`.draggable` 需 macOS 13+，本项目下限 12；系统 chrome 会改掉 4 个 `sidebar-*` 帧像素；会丢 `dragSelectRange` 锚点语义）。改最小方案：搜索框恢复焦点环、列表容器 `focusable` + `onMoveCommand` 映射到既有 store 动作（`selectOnly`/`selectRange`/`toggleSelection`）、行上 `accessibilityAddTraits(.isSelected)`、必要时 `ScrollViewReader` 滚到选中项 |
| R2-03 | 03 §3.2 / 14-06 | 高 | 待办 | 亮色 chrome：`GlassControls.swift:49,55,138,151-152`、`ThumbnailView.swift:14,28,32`、`VideoPreview.swift:272` 共 9 处 `.white.opacity(0.08–0.42)` 换 `.separator`/`.quaternary`/`controlBorderColor`；顺带统一设置侧栏符号风格（outline 与 filled 混用）与 GlassPill 图标重量（`doc.on.doc` 因 `.hierarchical` 比 `star`/`trash` 淡）。改前改后各拍 58 帧，给逐帧差异与对比度数字 |
| R2-04 | 02 §B B-1 | 高 | 待办 | `saveSnapshot` 每次保存仍重写**每个**图片文件（`HistoryPersistence.swift:264-272,401-405`），无去抖、不 cancel 旧 work item（`:212-226`）⇒ 磁盘 IO 与图片数线性。按内容指纹/已存在且同尺寸跳过未变文件 + 去抖并取消旧任务；测试要证明"N 次保存不再重写未变图片"（写入计数或 mtime），并保持崩溃/回滚语义 |
| R2-05 | 03 §3.4 / §1.5 | 中高 | 待办 | 拖拽能力为零（`onDrag/draggable/NSItemProvider/onDrop` 全仓 0 命中）。给行加 `onDrag { NSItemProvider }`（macOS 10.15+，**不要**用 13+ 的 `.draggable`）：文件给 fileURL、图片给 PNG、文本给 string。真实拖放无法离屏验证 ⇒ 验证等级要分开写（实现+单测 vs 人工拖一次） |
| R2-06 | 03 §3.3 / §1.7 | 中 | 待办 | `DestructiveConfirmation.swift:23-29` 的 `NSAlert` 里"清空"是第一个即默认按钮、无 cancel 角色 ⇒ 违反 HIG"默认按钮 = 最安全动作、Escape 取消"。改成取消为默认，或与设置页 `.alert` 共用同一语义 |
| R2-07 | 02 §B B-2 | 中 | 待办 | `StoredEntry`（`HistoryPersistence.swift:52-69`）无 `sourceAppBundleID/Name` ⇒ 重启后来源归因全丢、`appAffinity` 对载入历史恒 0。加**可选**字段（schema 仍 v1：旧存档缺字段读为 nil），补"存盘再载入仍带来源 App"的往返测试；写进 `AGENT_DECISIONS.md` |
| R2-08 | 02 §B B-4 | 中 | 待办 | 图片无像素上限，原分辨率 PNG 整张入库（`ClipboardIntake.swift:110-114`），一张 4K 截图数十 MB。阈值要有依据并写进决策/README；只影响新采集、不改已存图片；测试覆盖"超限被降采样、未超限逐字节不变" |
| R2-09 | 03 §3.5 | 中 | 待办 | `DetailPreviewViews.swift:263` 的 `"questionable"` 不是合法 SF Symbol ⇒ 视频信息不可用时画空白图标，改 `"questionmark"`；菜单栏推荐面板补"暂无推荐/加载中"空态（`MenuBarRecommendationsView.swift:14-52`）；详情 spinner 加超时兜底（`:234-243`） |
| R2-10 | 03 §3.6 / §1.12 | 中 | 待办 | 筛选 pill 的 `spring(0.38,0.72)` 过冲与 hover `scaleEffect(1.08)`（`HistorySidebarView.swift:244,259`）不读 `accessibilityDisplayShouldReduceMotion` ⇒ 门控；纯函数分支要有单测 |
| R2-11 | 02 §B B-3 | 中 | 待办 | `sizeDescription` 仍全串 `string.count`（`EntryPresentation.swift:40`），`PerfBudgetTests.swift:129` 自述把上界放宽到 20ms。改 O(1)/缓存后**把上界收回来**（放宽的阈值不许留着） |
| R2-12 | 02 §B B-6 / 03-04 | 中 | 待办 | 注入前不复核"250ms 后前台是否还是预期 App"（`ApplicationShell.swift` paste 流程）；补校验，失败原因走既有 NoticeBanner |
| R2-13 | 03 §3.7 | 中低 | 待办 | 字号越线两处：行时间戳 10pt（`HistoryRowViews.swift:84`）、菜单理由行 10pt `.tertiary`（`MenuBarController.swift:96-97`、`MenuBarRecommendationsView.swift:18`）；约 40 处固定字号可分批换 text style，先换用户必读的三处 |
| R2-14 | 02 §B B-5 | 低 | 待办 | backlog 里"过期项移到 `history.expired.json`"从未实现（被 D-012 的 NoticeBanner 方案取代），文档行未更正 ⇒ 改成"记录不改（理由）" |
| R2-15 | 02 §C 仍开放 / 10-07 | 低中 | 待办 | AI 脚手架仍在产品路径：`AIProviderModels.swift`/`AIPrivacyPolicy.swift` 在 `Sources/` 且零产品调用。移出产品 target 或删除（**不许**顺手删掉守着真行为的测试） |
| R2-16 | N-4 副产物 | 待定 | 待决策 | 只含非文件 `NSURL`（`public.url`）的剪贴板当前**不记录**。要不要记成文本条目？浏览器复制链接同时带字符串所以日常无感，但"复制即丢"对剪贴板管理器是功能缺口。决定后改 `ClipboardIntake` 并翻转 `ClipboardSourceAttributionTests` 里那条钉住"不记录"的断言 |
| R2-17 | 03 §0 / 04 §4.2 N-1 | 中 | 待办 | 菜单栏面板至今拍不到帧：构造 `AppDelegate` 会读用户真实存档，而 `HOME` 重定向实测**不改变** `applicationSupportDirectory`。给 `AppDelegate` 加一个 store 注入接缝（`AppDelegate(store:)`）后即可安全拍帧 —— 这是"UI 验收覆盖菜单栏"的前置条件 |

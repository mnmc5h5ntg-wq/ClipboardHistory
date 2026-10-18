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

**进度快照 3（同日晚些）**：

- 又完成：**R2-18 + R2-19**（夹具改固定参考时刻后，同一份代码连拍两次 **0/58 帧不同**，逐帧对比恢复为精确证据；
  `bdb557b`）· **GlassPill 图标重量统一**（monochrome，同提交；帧差 0.69% 且只落在含该控件的帧上）·
  **R2-16**（只含 `public.url` 的剪贴板现在记成文本，D-018，`f7398f3`，变异对照红过）·
  **R2-17**（`AppDelegate` 注入接缝 + 2 条用例，D-019，同提交；**但菜单栏仍 NOT-RUN**，理由更新为"离屏画不出菜单表面"，实测 97.7% 未绘制）·
  **R2-14**（R-20 那行的 `history.expired.json` 假承诺已更正，同提交）·
  **R2-15**（AI 草案拆出产品 target，D-020，`d0b2416`；`nm` 证明草案符号数为 0，用例整体搬走未删）。
- 本轮**证伪**的审计结论：R2-15 的"零产品调用"不成立 —— `AIPrivacyScope`/`AIPrivacySensitivity` 被 4 个产品文件使用，
  整体搬走会编译失败；已按编译器给出的事实拆成"词汇表 target + 草案 target"。
- 仍待办：**R2-02 在屏复测**（需人工开「完全键盘访问」）· **设置侧栏符号风格统一**（离屏证据不可信，见 `SettingsView.swift` 注释，标 NOT-RUN）·
  **菜单栏面板视觉**（等 R2-17 的在屏探针路线）· **多文件条目的拖出**（需要 NSView 级 dragging session）。

**进度快照 4（同夜最后三件）**：

- **性能闸改成可数的不变量**（`268ccaa`）：`f7398f3` 在 CI 上红过一次，原因是"热比较必须快于冷比较"这条计时判据
  在 2 核 runner 上没有分辨力（冷 34.5ms / 热 40.7ms，缓存其实是好的）。现在 `_FingerprintCache` 自带计算次数计数，
  测试断言"焐热后再比 3 次，旧图一侧计算次数为 0、新图一侧恰好 1"。变异对照（摘掉缓存早退）两条计数断言都红。
  绝对上界 `<250ms` 保留不变。
- **图片对 VoiceOver 命名**（`b7c9002`）：行缩略图与详情大图各给固定文案（"图片缩略图"/"图片内容"，**绝不含内容**），
  占位符号显式 `accessibilityHidden(true)`；静态用例钉住。并给出本轮第一个**精确**视觉证据：改动前后 **0/58 帧不同**。
- 剩余、且**明确不在本轮做**的：把约 40 处 `.font(.system(size:))` 换成 text style（macOS 上语义字号是否真的随系统设置缩放未验证，
  先验证再动，避免为改而改）；把设置窗口改成 `Settings` scene（审计自己也说"二选一，别叠两层"）；拖入文件入库（`.onDrop`，
  需要真实拖放才能验收）。

**进度快照 5（菜单覆盖，D-021）**：`populate(_:)` 从 private 放宽到 internal，新增 `MenuBarPopulationTests` 6 条 ——
关闭审计 09-08（"populate 无测试"）与 13-08 的一部分（菜单内容此前只能靠 `menuLabel` 间接覆盖）。
写这批测试时**暴露了本轮自己引入的一个误导**：菜单同步构建而预测异步计算，所以打开瞬间必然空，
"暂无推荐"会在有候选的机器上先闪一下。已用 `isRefreshingPredictions` 把"还在算"与"确实没有"分开（两条菜单路径同步改），
并有变异对照证明这条区分是承重的。当前判据：`swift test` 293 例 / 5 skip / 0 失败、`swift build` 0 告警、58 帧 0/58 不同。

**进度快照 6（拖入文件，D-022）**：R2-05 的另一半也做完了 —— 侧栏列表接受 `public.file-url` 拖入，
1 个文件成 `.file`、多个成**一条** `.files`、非文件 URL 拒收；落点刻意不覆盖整窗（详情文本视图本来就要吃文字拖放）。
8 条用例 + 变异对照（去掉 `isFileURL` 过滤 ⇒ 5 条红）；58 帧 0/58 不同。**真实鼠标拖放仍无法验收**（审计 04 §4.2 N-4 同判）。
当前判据：`swift test` **301 例 / 5 skip / 0 失败**、`swift build` 0 告警。

**进度快照 7（性能守卫的自我推翻，D-023）**：`53bbe85` 在 CI 第四次红（搜索词代价均值 69.0ms vs 上界 60ms，本地 14.1ms）。
我先加的 load1/核数 > 2 闸门**是错的**：CI 原始日志实测 `load1=11.8 活跃核=3` ⇒ 比值 3.9，那道闸门会把 5 条性能守卫
在唯一的自动化环境里永久变成 skip，本地安静时才裁决 —— 正是"只在没人看着的地方失效"的绿。已删除，改为
「判据打在 N 次同操作采样的**最快**值 + `最慢−最快 > 该条阈值` 才 skip」，**阈值 1/5/60/200/250ms 一个没动**，
最快/均值/最慢/n/load1 一律先打印。双向变异对照都实跑：缓存短路改成 `&& false` ⇒ 该条**红而不是 skip**（跨度 0.50ms < 1ms）；
阈值临时改 0.01 ⇒ skip 分支真的点亮。反面证据：本机 12 个 `yes` 把 load1 顶到 44.4，`preview(2.4MB)` 跨度仍只有 0.07ms，
即"机器忙"从来不等于"这条判据不可用"。同提交把只测一次的计时改成 3 次采样（同字节比较第 2/3 次会量到已焐热的缓存）。
当前判据：`swift build` 0 告警 · `swift test` 301 例 / 5 skip / 0 失败 · python 25 例 OK · 连拍三次 58 帧 sha 集合完全一致。
**已核**：`c952905` 的 CI 日志里 runner 是 `load1=27.7 / 活跃核=3`，8 条 `PERF[...]` 全部下结论、零 skip —— 旧闸门会把它们全变成 skip。

**进度快照 8（菜单栏面板第一次有像素，D-024）**：以前"离屏拍不到菜单栏"只对 macOS 12 的 NSMenu 路径成立；
13+ 真正上线的是 `MenuBarExtra`，它的 body 是普通 SwiftUI View，配上 D-019 的注入接缝就能和其他夹具一样离屏渲染。
帧数 **58 → 64**（有推荐 / 还在整理 / 暂无推荐 × 亮暗），同代码连拍两次 sha 完全一致。
`Fixture` 加了 `settle` 钩子（内容要等异步刷新才落定的帧用），"正在整理"那一帧在快门前断言刷新仍在途；
变异对照（`refreshPredictions()` 直接 return）⇒ 捕获套件红 4 次。
**看画面立刻抓到一个内容缺陷**：推荐理由 `文本 · Safari · 偏好链接 · 回到Safari · 24%` 一行里把来源 App 说两遍，
`16d658d` 修掉（断言先写、对旧实现报红 2 次）。仍 NOT-RUN：系统菜单材质/圆角/菜单项 chrome（需要在屏捕获）。
当前判据：`swift build` 0 告警 · `swift test` 301 例 / 5 skip / 0 失败 · python 25 例 OK · 64 帧连拍两次 sha 一致。

**进度快照 9（把"侧栏图标不可见"量成数字，D-025）**：审计 1.9 那一项原来靠一句推断（"真机不可能长这样"）判成捕获伪影。
现在有三组数：产品里未选中四行图标列墨水 **0.0000**；同一图标临时改固定 `Color.black` → **0.175–0.402**；
复刻的 `List(.sidebar)` 行里 `.primary` 与固定色一样能画（带/不带 `.plain` Button 四种组合全测）。
⇒ 判为离屏语义色伪影，**产品一字未改**，注释换成测量。中途我先动了实现（icon 闭包 + `.monochrome`），
复刻实验一出来就回退了 —— 教训写进 D-025："帧里看不见"要先问管线会不会说谎。
探针形状：常规套件只留版本无关的前提断言（固定色必须画得出来），语义色部分与视觉审计同开关、只打印结论不做断言。
删掉了十分钟前自己写的一条通过 `.primary` 断言产品可见性的用例（读法无效，被替换而非删绿）。
当前判据：`swift build` 0 告警 · `swift test` **303 例 / 6 skip / 0 失败** · python 25 例 OK · 64 帧与改注释前 sha 全同。

**进度快照 10（探针自己红了一次 + 补上工具栏删除判断的测试）**：
`2817a93` 那条离屏图标探针在 CI 上第五次红 —— 它把"文字列能数出 5 行"当断言，而 macos-15 runner 上同一段列表只数出 4 行。
`e8a59e4` 把判据换成"整列图标墨水"（与行几何无关），并配一条变异（符号名换成不存在的 ⇒ 墨水 0.0000 判红）证明它不是装饰。
`85c6ba5` 关掉矩阵里的 08-08 / 13-08：`isSidebarToolbarItem`（靠关键词决定**从工具栏删哪个按钮**）现在有 9 条正反用例，
负向更承重（自己的复制/筛选/搜索项不许被误删）。两条实测发现进了注释：
① `item.view = nil` 会顺手清掉 `item.action`（第一版夹具因此红，红的是夹具不是产品）；
② 函数里那条 action 直判是**冗余保险**（删掉仍全绿，字符串路径也会命中），用例按这个口径写。
当前判据：`swift build` 0 告警 · `swift test` **312 例 / 6 skip / 0 失败** · python 25 例 OK · 64 帧 sha 一致 · CI 绿到 `e8a59e4`。

**进度快照 11（录制器：6 条用例抓到一条真缺陷，D-027）**：审计 13-08 剩下的可测部分做了 ——
`HotKeyRecorderButton` 现在只按可观测行为测（标题 / 两个回调 / 谁持有第一响应者），6 条里 5 条直接绿，
第 3 条红并且**红的是产品**：录下合法组合后按钮仍写着"请输入快捷键"（`shortcut.didSet` 在录制态跳过回显，
之后再没人改），只等下一次 SwiftUI 刷新才恢复。`14a37a0` 加一行显式回显修掉，变异对照证明失焦那条守卫承重。
两条夹具坑都进了注释：裸 `NSView` 不接受第一响应者（失焦用例会红在夹具上）、`item.view = nil` 会清掉 `item.action`。
13-08 仍欠两块：**设置页交互**与**生命周期回调**没有测试 —— 本轮没做，不是因为做不完，
而是这两块的可测面需要先加接缝（`AppDelegate` 的生命周期回调目前只能靠真启动 App 触发），
按"不在没接缝的地方硬凑测试"处理，留在下轮。
当前判据：`swift build` 0 告警 · `swift test` **318 例 / 6 skip / 0 失败** · python 25 例 OK · 64 帧与修复前 sha 全同。

**进度快照 13（v1.4.8 出包，D-031）**：用户授权后发布，tag `v1.4.8` 打在 `e4aee3c`，线上 Latest 已切换。
出包前先把 R2-21 的闸门补上：`prepare_release.py` 反汇编包内二进制，`AppDelegate` 还留着「未实现初始化器」桩就拒绝发布
—— D-029 那一版正是"327 例绿、CI 绿、codesign 有效，用户一打开就闪退"，而链路里没有任何一步真的执行过它。
闸门做成静态读产物而不是启动用户的 app（后者会读他真实存档）。两个坑都踩过并写进注释：
arm64 上类名字面量离调用点二十几行（固定窗口回看会在坏产物上报"干净"），
文件路径字面量含 `.swift` 会被当成类名（在正确产物上误报）。
变异对照两轮：把 D-029 装回去重打包 ⇒ 闸门点名 `ClipboardHistoryApp.AppDelegate`、端到端用例红；
删掉 `prepare()` 里的调用点 ⇒ 接线用例红。发布说明与 CHANGELOG 的占位内容全部重写成真实改动并列出"还没做到的"。
**R2-21 只标部分完成**：静态桩证明不了"窗口建得起来"，运行时冒烟（真的打开、活过 N 秒）仍欠。
当前判据（发布提交上实测）：`swift build` 0 告警 · `swift test` 328 例 / 9 skip / 0 失败 ·
发布脚本测试 30 例 OK · 68 帧基线 · 线上 Latest = v1.4.8。

**进度快照 12（用户提的交互需求：行内双击复制 + 星标收藏，D-028）**：收藏/复制以前只在详情区右下角浮层里，
鼠标要横穿整个窗口。现在行上直接有：双击 = 与浮层"再次复制"同一个动作（`.copyAndPromote`），
行首星标 = 就地收藏/取消。星标做成行的**兄弟控件**而不是嵌套 Button，双击用
`Button + simultaneousGesture(TapGesture(count:2))`（改成 `onTapGesture(count:2)+onTapGesture` 会让每次单击等一个双击间隔）。
带 shift/command 的双击不复制，规则抽成 `RowDoubleTap.shouldCopy`，并有守卫去读 `select(_:)` 实际用的修饰键。
颜色全部量化：未收藏的星从 `.clear`（这个控件此前不可见）提到 `primary.opacity(0.55)`，
实测对比度 1.76/2.17 → **3.54/4.64**；已收藏从 `Color.yellow`（亮色 1.67:1）换成压深的琥珀 → **3.90/4.28**。
**这次是真点验证**：在屏探针往一行投递合成鼠标事件，断言"单击选中 / 1→2 恰好一次复制 / 点星标翻收藏且不动选中"。
探针最初红是它自己的错 —— 按 74pt 行高点 y=37，而自然行高是 47、星标只有 20pt；网格扫描证明控件是活的。
新增 R2-20（收藏会把多选收成一条，浮层一直如此，现在更顺手所以更容易撞）。
当前判据：`swift build` 0 告警 · `swift test` **325 例 / 8 skip / 0 失败** · 68 帧（64→68）两次连拍 sha 相同。
并且**在真实容器里也真点验过**：整条侧栏摆上屏，按几何挑出 6 个星标代理与 6 个行代理，
点最下面那一行 ⇒ 星标翻收藏、行改选中、双击恰好写一次剪贴板且写的就是那条、并被顶到最前；
删掉双击手势立刻红（变异对照），这条探针自己也错过一次（把 148×25 的筛选 pill 当成了行）。
**待观察**：新头推送后去 CI 日志 `grep "PERF\["` 确认 5 条守卫真的下结论而不是全部 skip（命令已写进报告 10.3）。

| # | 审计出处 | 价值 | 状态 | 内容 |
|---|---|---|---|---|
| R2-01 | 02 §A N-1 | 高 | 已完成(876c015+ca12531) | 补"存档含同 id 两条 ⇒ 预测刷新不崩且只出一条"的**端到端**用例：走 `HistoryStore` 的预测刷新路径，不走 `engine().recommend`（`RecommendationBoundaryTests:96-103` 正是这样绕过了 adapter，所以 `876c015` 之前一直是绿的）。做完用变异对照证明：把实现改回 `Dictionary(uniqueKeysWithValues:)` ⇒ 该用例必须红/崩 |
| R2-02 | 03 §3.1 / §1.10 | 高 | 部分完成(d4edf1f)：真实 Tab 到搜索框已实测；「Tab 能否走到列表行」需人工开完全键盘访问后复测 | 键盘焦点链。实测 14 次 `selectNextKeyView` 全落在同一个 `NSTextView`；`ChineseTextContextMenu.swift:40` 把搜索框 `focusRingType` 设成 `.none`；全仓 `.buttonStyle(.plain)` 无焦点环、无 `.focusable()`/`@FocusState`。**不采纳**"整体换 `List(selection:)`"（`.draggable` 需 macOS 13+，本项目下限 12；系统 chrome 会改掉 4 个 `sidebar-*` 帧像素；会丢 `dragSelectRange` 锚点语义）。改最小方案：搜索框恢复焦点环、列表容器 `focusable` + `onMoveCommand` 映射到既有 store 动作（`selectOnly`/`selectRange`/`toggleSelection`）、行上 `accessibilityAddTraits(.isSelected)`、必要时 `ScrollViewReader` 滚到选中项 |
| R2-03 | 03 §3.2 / 14-06 | 高 | 已完成(6a2c040)：9 处亮色 chrome；设置侧栏符号风格已量成数字，判为离屏语义色伪影，产品不改(D-025) | 亮色 chrome：`GlassControls.swift:49,55,138,151-152`、`ThumbnailView.swift:14,28,32`、`VideoPreview.swift:272` 共 9 处 `.white.opacity(0.08–0.42)` 换 `.separator`/`.quaternary`/`controlBorderColor`；顺带统一设置侧栏符号风格（outline 与 filled 混用）与 GlassPill 图标重量（`doc.on.doc` 因 `.hierarchical` 比 `star`/`trash` 淡）。改前改后各拍 58 帧，给逐帧差异与对比度数字 |
| R2-04 | 02 §B B-1 | 高 | 已完成(9ac4661) | `saveSnapshot` 每次保存仍重写**每个**图片文件（`HistoryPersistence.swift:264-272,401-405`），无去抖、不 cancel 旧 work item（`:212-226`）⇒ 磁盘 IO 与图片数线性。按内容指纹/已存在且同尺寸跳过未变文件 + 去抖并取消旧任务；测试要证明"N 次保存不再重写未变图片"（写入计数或 mtime），并保持崩溃/回滚语义 |
| R2-05 | 03 §3.4 / §1.5 | 中高 | 已完成(d463ef9 拖出 + 53bbe85 拖入)；多文件拖出未做(需 NSView dragging session) | 拖拽能力为零（`onDrag/draggable/NSItemProvider/onDrop` 全仓 0 命中）。给行加 `onDrag { NSItemProvider }`（macOS 10.15+，**不要**用 13+ 的 `.draggable`）：文件给 fileURL、图片给 PNG、文本给 string。真实拖放无法离屏验证 ⇒ 验证等级要分开写（实现+单测 vs 人工拖一次） |
| R2-06 | 03 §3.3 / §1.7 | 中 | 已完成(a841337) | `DestructiveConfirmation.swift:23-29` 的 `NSAlert` 里"清空"是第一个即默认按钮、无 cancel 角色 ⇒ 违反 HIG"默认按钮 = 最安全动作、Escape 取消"。改成取消为默认，或与设置页 `.alert` 共用同一语义 |
| R2-07 | 02 §B B-2 | 中 | 已完成(d8d11f4, D-016) | `StoredEntry`（`HistoryPersistence.swift:52-69`）无 `sourceAppBundleID/Name` ⇒ 重启后来源归因全丢、`appAffinity` 对载入历史恒 0。加**可选**字段（schema 仍 v1：旧存档缺字段读为 nil），补"存盘再载入仍带来源 App"的往返测试；写进 `AGENT_DECISIONS.md` |
| R2-08 | 02 §B B-4 | 中 | 已完成(1183f9f, D-017) | 图片无像素上限，原分辨率 PNG 整张入库（`ClipboardIntake.swift:110-114`），一张 4K 截图数十 MB。阈值要有依据并写进决策/README；只影响新采集、不改已存图片；测试覆盖"超限被降采样、未超限逐字节不变" |
| R2-09 | 03 §3.5 | 中 | 已完成(1214526) | `DetailPreviewViews.swift:263` 的 `"questionable"` 不是合法 SF Symbol ⇒ 视频信息不可用时画空白图标，改 `"questionmark"`；菜单栏推荐面板补"暂无推荐/加载中"空态（`MenuBarRecommendationsView.swift:14-52`）；详情 spinner 加超时兜底（`:234-243`） |
| R2-10 | 03 §3.6 / §1.12 | 中 | 已完成(2438aa6) | 筛选 pill 的 `spring(0.38,0.72)` 过冲与 hover `scaleEffect(1.08)`（`HistorySidebarView.swift:244,259`）不读 `accessibilityDisplayShouldReduceMotion` ⇒ 门控；纯函数分支要有单测 |
| R2-11 | 02 §B B-3 | 中 | 已完成(8cfdfe5) | `sizeDescription` 仍全串 `string.count`（`EntryPresentation.swift:40`），`PerfBudgetTests.swift:129` 自述把上界放宽到 20ms。改 O(1)/缓存后**把上界收回来**（放宽的阈值不许留着） |
| R2-12 | 02 §B B-6 / 03-04 | 中 | 已完成(d218803) | 注入前不复核"250ms 后前台是否还是预期 App"（`ApplicationShell.swift` paste 流程）；补校验，失败原因走既有 NoticeBanner |
| R2-13 | 03 §3.7 | 中低 | 已完成(1214526 + d218803) | 字号越线两处：行时间戳 10pt（`HistoryRowViews.swift:84`）、菜单理由行 10pt `.tertiary`（`MenuBarController.swift:96-97`、`MenuBarRecommendationsView.swift:18`）；约 40 处固定字号可分批换 text style，先换用户必读的三处 |
| R2-14 | 02 §B B-5 | 低 | 已完成(f7398f3) | backlog 里"过期项移到 `history.expired.json`"从未实现（被 D-012 的 NoticeBanner 方案取代），文档行未更正 ⇒ 改成"记录不改（理由）" |
| R2-15 | 02 §C 仍开放 / 10-07 | 低中 | 已完成(d0b2416, D-020)；审计前提被部分否证(两个枚举确实在产品路径) | AI 脚手架仍在产品路径：`AIProviderModels.swift`/`AIPrivacyPolicy.swift` 在 `Sources/` 且零产品调用。移出产品 target 或删除（**不许**顺手删掉守着真行为的测试） |
| R2-16 | N-4 副产物 | 待定 | 已完成(f7398f3, D-018)：改为记成文本条目 | 只含非文件 `NSURL`（`public.url`）的剪贴板当前**不记录**。要不要记成文本条目？浏览器复制链接同时带字符串所以日常无感，但"复制即丢"对剪贴板管理器是功能缺口。决定后改 `ClipboardIntake` 并翻转 `ClipboardSourceAttributionTests` 里那条钉住"不记录"的断言 |
| R2-17 | 03 §0 / 04 §4.2 N-1 | 中 | 已完成(f7398f3 接缝 + 37f43f6 补拍 6 帧)；系统菜单材质与菜单项 chrome 仍 NOT-RUN | 菜单栏面板至今拍不到帧：构造 `AppDelegate` 会读用户真实存档，而 `HOME` 重定向实测**不改变** `applicationSupportDirectory`。给 `AppDelegate` 加一个 store 注入接缝（`AppDelegate(store:)`）后即可安全拍帧 —— 这是"UI 验收覆盖菜单栏"的前置条件 |
| R2-18 | 03 §方法 | 高 | 已完成(bdb557b) | 视觉捕获的时序噪声：同一份代码连拍两次即有 30/58 帧不同(闪烁插入点)。修法是拍前交出第一响应者并把插入点画成透明 |
| R2-19 | 03 §方法 | 高 | 已完成(bdb557b) | 捕获夹具用 Date() 当时钟 ⇒ 跨分钟连拍时字符串本身在变像素。改用固定参考时刻，此后同代码连拍 0 帧不同 |
| R2-21 | D-029 | 高 | **部分完成(d698a4c)** | 发布链路加了启动闸门，但只挡住 D-029 那一类：`prepare_release.py` 现在反汇编包内二进制，`AppDelegate` 若还留着「未实现初始化器」桩就拒绝发布（v1.4.8 已按此闸门出包，且对 DMG 内产物重跑过一次）。**仍欠的是「真的打开一次」**：进程活过 N 秒 / 启动日志里出现「守卫放行 + 窗口建好」这类运行时冒烟还没做 —— 静态桩只能证明不会在 `-init` 上 trap，证明不了窗口建得起来。原建议（CI 里 `make bundle` 后跑启动冒烟，fresh runner 无用户数据）仍然有效 |
| R2-22 | D-032 | 中 | 未开始 | 右键菜单"屏幕上真弹出来的样子"无法在仓库里自动断言：`NSMenu.popUpContextMenu` 模态，实测 `didBeginTracking` 里 `cancelTrackingWithoutAnimation()` 也叫它不返回。现在靠 `docs/MANUAL_TEST_v1.4.8_issue13.md` 人眼核对。**可做的修法**：给菜单窗口做屏上取证（弹一份自己的菜单 → `CGWindowListCreateImage` 截那块 → 立刻 `perform` 一个取消），需要屏幕录制权限，先验可行性再动仓库；否则每次 UI 发版都要把清单第 1/3 节重跑一遍 |
| R2-23 | D-032 | 低 | 未开始 | 拦截器只认领 `ChineseMenuTextField` 里的 field editor。今天全仓库只有搜索框一处可编辑文本所以够用；**新增任何文本输入**若不走 `ChineseMenuTextField`，那份右键菜单就又会是系统 12 项。修法：要么把 `TextField` 统一包一层（配合一条源码守卫"Sources 里不许出现裸 `TextField(`"），要么把认领判据扩成"本 App 窗口内的 field editor"并补反面对照 |
| R3-D1 | 第三轮 D-1 | 高(S2) | 已完成(D-033 + D-034) | 拖出与拖选手势争用。**真机反馈否掉了"把手才拖出"的设计**：`List` 会把行内任何 `.onDrag` 提升成整行拖拽源 ⇒ 拖选与拖出不能共存。取舍是保留整行拖出、删掉拖选（连 `dragSelectRange` 动作与行位置表一起清，不留半套死码）；列表换 `List(selection:)`，单击/shift/⌘/方向键/VO 交回系统。行为验收见手工清单第 1、2 节。 |
| R3-D2 | 第三轮 D-2 | 中 | 已完成(D-033) | 推荐理由里内容类型标签改由条目决定；一条钉住旧缺陷的用例按事实翻转。 |
| R3-D3 | 第三轮 D-3 | 中 | 已完成(D-033) | 「通用」补 F1/F4 两项（暂停记录 / OCR 可关），判据 `RecordingGate`，键落 UserDefaults。 |
| R3-D4 | 第三轮 D-4 | 中 | 已完成(D-033) | 拖入被忽略的项走 `NoticeBanner`；`ignoredCount` 终于有读者。 |
| R3-D5 | 第三轮 D-5 | 低 | 已完成(D-033) | 新→旧→新往返用例 + `migrate` 注释写明 additive 边界。 |
| R3-D6 | 第三轮 D-6 | 中 | 已完成(D-033) | 降采样后在同一后台路径算出新尺寸 PNG 字节。 |
| R3-D7 | 第三轮 D-7 | 低 | 已完成(D-033)，报告型 | CI 跑在屏探针与帧捕获并打印执行数/帧数；`continue-on-error` 起步，稳定性证明后再转硬门。 |
| R3-D8 | 第三轮 D-8 | 低 | 已完成(D-033) | 设置侧栏符号统一描线（`sparkles`→`wand.and.stars`）+ 守卫。 |
| R3-D9 | D-033 / D-034 | 中 | 部分完成(D-034) | **在屏表格行为没有自动化覆盖**：合成鼠标事件送不进 `NSTableView`（`clickedRow` 恒 -1）。D-034 已把"拖选"这条从需求里去掉（取舍），剩下的点选 / shift 扩选 / ⌘ 加选 / 双击复制 / 拖出落地仍只能真机看，每版发版前请把 `docs/MANUAL_TEST_v1.4.9_round3.md` 第 1、2 节人肉跑一遍。要么找一条能真正驱动表格的通道（CGEvent + 辅助功能授权，代价是要权限），要么接受这条人工门。 |
| R3-D10 | D-033 | 低 | 未开始 | 多文件条目仍不能拖出（需要 `NSView` 级 dragging session，R2-05 的另一半）。换 `List` 之后做它的成本比之前低（行由表格管理），下一轮做 U-2 时顺手。 |
| R3-D11 | D-033 / CI 实测 | 中 | 部分完成(D-037) | **CI runner 上才有的两条事实**（run 38050339974 / 38050990090）：① `content-wide-1100x800` 亮暗两帧在 macos-15 runner 上有 95% 像素未被绘制 ⇒ 捕获失效闸门锁住不认它，真机这两帧正常，需要判定是 runner 的离屏渲染限制还是尺寸相关的产品问题（**仍未定，报告型不挡发布**）；② `UIInteractionProbeTests` 在 runner 上挂死，现在自带 240 秒看门狗 —— D-037 又发现"汇报了却一行数字都没有"其实是汇报行自己的 grep 在单数 `Executed 1 test` 上失手导致 `bash -e` 中止，已修并有守卫（`test_ci_report_selftest.py`）钉住"结论行必然打印"。两条都不挡发布，但都是下一轮 CI 加固的入口。 |
| R3-D12 | 用户真机反馈 | 中 | 已完成(D-035) | 图片文件条目在左侧列表没有预览：剪贴板不带图像数据时 `.file` 条目的 thumbnail 是空的。现在 add 后在后台解一张 ≤256px 缩略图写回并落盘，启动时回填老历史；新增 `row-file-thumb` 亮暗两帧把这件事钉进帧集合（68→70）。 |
**进度快照 13（D-029：修掉自己带进去的启动闪退）**：用户报「从仓库根目录打开新版 app 闪退」。
两份 .ips 的崩溃 PC 紧跟 `_unimplementedInitializer(AppDelegate, "init()")` + `brk #1`，包 UUID 与仓库产物一致 ⇒ D-019 给 `AppDelegate` 加显式 `init(historyStore:)` 之后，ObjC 的 `-init` 变成编译器留下的 trap 桩，而 SwiftUI 的 `@NSApplicationDelegateAdaptor` 正是通过元类型调它。
327 个用例与 CI 全绿挡不住的原因：Swift 侧 `AppDelegate()` 解析到带默认参数的那个 init，永远走不到 `-init`；CI 也从不启动 .app。修法是三行 `override convenience init()`，守卫两条互补（运行时走元类型 + 源码扫描必须声明 override init）。修之前那条运行时守卫原地复现了同一句 fatal error（signal 5），修之后绿。
重打包 `make bundle VERSION=1.4.7-fix1`：新 UUID `8A1FB38C…`、AppDelegate 的桩消失、unimplemented 站点 4→3（剩下 3 个是只在 Swift 侧构造的 Coordinator / 自定义 NSView，良性）。**真机启动待用户确认**；结构性缺口开成 R2-21（CI 没有「能不能启动」这一关）。
当前判据：`swift build` 0 告警 · `swift test` **327 例 / 8 skip / 0 失败** · 包已重打并二进制层核对。
**进度快照 14（D-030：关掉列表那圈蓝框）**：用户报"双击后左侧列表周围出现一个蓝色框"。
定性过程里有两次反直觉：第一响应者的 `focusRingType` 本来就是 `.none`（⇒ 环不是 AppKit 画的），
而拍窗口再肉眼看的办法在"已聚焦的真实窗口"上会画歪（⇒ 像素不能当证据）。
最后用视图树清点 SwiftUI 的 `_FocusRingView` 拿到可判别信号：改前 15 个（含整块列表那圈 {{0,125},{320,335}}），
改后 2 个（筛选 pill 自己的）。修法保留 `.focusable()`（方向键不能坏），加 macOS 14+ 的 `focusEffectDisabled()`；
**macOS 12/13 上环仍会出现**，平台没有对应开关，探针失败消息里写明这一区分。
守卫三条（在屏探针 + 源码扫描同时钉 focusable 与抑制 + 抑制函数不许是空壳），②的牙用变异对照验过。
顺带记一个 Swift 坑：`XCTAssertEqual(x?.enum, .none)` 的 `.none` 是 `Optional.none`，断言恒不成立。
当前判据：`swift build` 0 告警 · `swift test` **328 例 / 9 skip / 0 失败** · 68 帧与改动前 sha 全同 ·
包重打为 `1.4.7-fix2`（UUID `1FBD7DF5…`）。
**进度快照 15（D-032：issue #13 右键菜单汉化）**：真正修好的不是"菜单文案"，而是"编辑态的右键根本不归我们"。
被实测证伪的三条自己人做法（`hitTest` 让位 / 给共享 field editor 挂 `menu` / 就地改 `menu(for:)` 那份）
与"让菜单真弹起来量"这条一起记进 D-032；最后落地的是 `addLocalMonitorForEvents` 在派发前截走。
两个值得留下来的手感：① **探针的挂住本身是证据** —— 变异"让拦截不吞事件"时进程卡死在 AppKit 那份模态菜单上，
这既证明拦截器是有效路径，也证明"量弹出来的那份"这条判据不能进仓库；于是加了 20 秒看门狗
（写清原因再 `exit(73)`），broken 时是有边界的红而不是钉住机器。
② "源码里写了 `editor.menu =`"曾经被当成已修 —— 读回来是系统那 12 项（快速查看附件/字体/书写方向/布局方向都在），
所以留了一条**反模式守卫**禁止这条路再回来。
当前判据：`swift build` 0 告警 · `swift test` **339 例 / 10 skip / 0 失败** · 在屏右键探针绿 ·
5 组变异对照全部按预期点亮。屏幕上真弹出来的样子仍需人眼（R2-22，清单在 `docs/MANUAL_TEST_v1.4.8_issue13.md`）。
**进度快照 16（2026-10-10 夜：第三轮审计 D-1…D-8，D-033）**：用户指定 D-1 走修法③（换 `List(selection:)`）、
D-3 给「通用」补两项而不是合并 —— 两条都按指定做完，其中 D-1 是对我们自己 R2-02 决定的**有据推翻**
（三条原理由逐条对账写在 D-033 里）。
本轮最贵的一条不是代码而是**测量边界换了**：换成系统表格之后，合成鼠标事件送不进去
（`clickedRow` 恒 -1 + `isKeyWindow=false`），于是"点选/双击复制/拖选扩选"从可自动测退成只能真机看。
处理方式是把判据拆开而不是假装还在测：结构判据留在常规套件，行为判据进手工清单第 1、2 节，
并新开 R3-D9 记这条缺口。同时新增一条离屏伪影账：`List` 的选中高亮在帧里画成整块黑，
判据是"黑块精确跟随选中集合"（三行选中⇒三块黑），与 D-025 同源，不据此判产品。
还有一条老毛病又犯：变异脚本里 ASCII 双引号混进中文导致 python 语法错（第 6 次），
以及"变异没落地就报 0 红" —— 这次靠 `assert 锚点 in text` 挡住了，判据是**先证明改动落地再跑测试**。
当前判据：`swift build` 0 告警 · `swift test` **355 例 / 10 skip / 0 失败** · 68 帧连拍两次 sha 相同 ·
5 组变异对照点亮 · CI 新增报告型在屏步骤。
**进度快照 17（2026-10-10 深夜：D-034 与 D-035，两条都是用户真机反馈抓到的）**：这一夜连续两条缺陷都是自动化闸门放过去的 —— ① 拖选：我那条「拖出入口恰好一处且挂在把手上」的守卫在源码层为真、效果层为假（`List` 会把行内任何 `.onDrag` 提升成整行拖拽源），取舍改成保留整行拖出、删掉拖选；② 图片文件行没有预览：夹具里从来就没有一条「带缩略图的 .file 行」，所以那格像素无人看过，补了 `row-file-thumb` 亮暗两帧（68→70，其余逐帧不变）。
两条教训合起来是一句话：**源码扫描钉得住写法，钉不住 AppKit 怎么处理这个写法；帧集合只覆盖它包含的形状**。凡是归属、作用域、有没有画出来这类判断，要么落到真实容器上测，要么造一帧出来，否则就是把闸门当成装饰。
当前判据：`swift build` 0 告警 · `swift test` **362 例 / 10 skip / 0 失败** · 70 帧中新增 2 帧、其余 68 帧与上一版逐帧相同 · 变异对照 7 组（D-034 三组 + D-035 四组）逐一点亮。

**进度快照 18（2026-10-10 深夜：D-036，为了过离屏探针改了产品行为）**：真机反馈第三条。
前两条（D-034/D-035）是闸门放过真缺陷，这一条是我明知离屏探针的宿主不代表真实 `List`，
还是把手势改成它认得的形状 —— 代价是点选延迟一个双击间隔，由用户的鼠标承担。
改回 `simultaneousGesture(TapGesture(count: 2))`，自动化侧只留"写法"层反向守卫，
"点选无延迟 / 双击仍可复制"两条效果转人工（清单 §1 的 1.1 / 1.5 已具名）。
新增规矩：**为点亮判据而改产品交互之前，先证明夹具代表真实容器；不代表就只能改判据。**
第二条更基本：**改到过去明确钉过的设计，先读那条决定的原文** —— 这个延迟的答案就在 D-028 里写着
（"不要换成 onTapGesture(count:2)，会让每次点选慢半拍"），我改的时候没查，等于账本白记。
当前判据：`swift build` 0 告警 · `swift test` **362 例 / 10 skip / 0 失败** ·
70 帧逐帧不变 · 变异对照累计 8 组（D-034 三 + D-035 四 + D-036 一）。

**进度快照 19（2026-10-10 深夜：D-037，报告型 CI 步骤第三次"红了但没有数字"）**：这次坏在汇报行自己
—— 抽取 `Executed N tests` 的 grep 在 runner 上匹配不到**单数** `Executed 1 test`，非零 + `pipefail` +
`bash -e` 让脚本在 echo 之前中止。同族第三次（前两次是 tee 与 wait），已归纳成规矩并落成守卫：
新脚本把两个步骤的 run 正文原文抽出来喂三种日志形状，随 CI 的 unittest discovery 真执行。
**第一版修法之后 run 38064293655 仍然缺结论行**：离屏步骤打出来了（`captured frames: 70 executed: 1 捕获失效帧: 2`），
在屏步骤还是只有 `Killed: 9` + `exit code 1` —— 第二条中止点换到了 `kill "$killer"`：
看门狗执行完 kill 自己就退出了，而 `2>/dev/null` 只闭嘴不改退出码。已一并兜底，并给自检补两格
（看门狗已退出 / 帧目录不存在），变异对照下这两格都会"结论行缺失"。
当前判据：`python3 -m unittest discover -s scripts/tests` **31 例 / OK（自检 5 个形状）** ·
变异 2 组点亮（还原 `cmp` 相同）· Swift 侧不变：362 例 / 10 skip / 0 失败。

## 快照 17（2026-10-11，批次 2 收尾）

- 本轮做完：F-1（默认排除名单 + 用户名单 + 设置页表 + Store 侧验收）、
  F-4（OCR 只索引不落盘 + 设置页单选）、F-5（固定置顶/豁免清理/行内徽标/浮层按钮/导出导入）。
- 验证：全量 382 tests 0 失败；`make bundle` 0 warning；帧 76 张两次同 sha；
  4 条新守卫全部做过变异对照（含一条最初是假守卫、加强后才红的）。
- 未闭合：R3-F4 的端到端识别落盘证明、R3-F5 的导出导入面板手点 —— 都进手测清单。
- 下一批：批次 3 = U-4（详情排版 + 搜索命中高亮）、U-5（状态语言统一）。

## 快照 18（2026-10-11，批次 3 收尾）

- 本轮做完：U-4（可读行长 68ch/652pt、meta 单行左对齐含来源、搜索命中高亮走临时属性）
  与 U-5（`StatePresentation` + `StateLine` 统一三处状态；空态补「清除搜索」）。
- 验证：407 tests 0 失败；`make bundle` 0 warning；78 帧两次同 sha；
  5 条新守卫全部变异对照（M1 最初因替换文本不完整而变成编译错误 —— 那不算红，已修正重跑）。
- **未做，标 ready-for-human**：U-5 的"12/13 焦点环改自绘细环"。
  原因：需要行级键盘焦点信号（`List(selection:)` 不给）+ 一台 12/13 真机才能验证；
  先关系统环又画不出替代环，会在最老的两个系统版本上删掉唯一的焦点指示。
  取舍与理由写在 D-039。
- 下一批：批次 4 = U-2（拖出 drag image，含多文件）+ F-2（RTF/HTML 保真，带字节上限与开关）。

## 快照 19（2026-10-11，批次 4 收尾）

- 本轮做完：F-2（RTF/HTML 采集+写回+存档+导出如实报告，默认关）与 U-2 的多文件拖出
  （`NSFilenamesPboardType` 路径数组，解码核对）。
- 刻意不做：自定义 drag image 卡片 —— 系统跟手剪影已是那一行本身（含预览与缩略图），
  要换成自定义图必须自起 dragging session，而那个形状在 D-034 被真机否掉。理由记在 D-040。
- 验证：416 tests 0 失败；`make bundle` 0 warning；78 帧两次同 sha；5 条新守卫变异对照全过；
  「通用」设置页帧有变化而其余分区 0 差异。
- 契约变更：`SidebarListSelectionTests` 里"多文件不许承诺拖拽"改成"有载荷必须承诺"，
  旧不变量（空列表不许许空愿）保留。
- 下一批：批次 5 = F-3（⌘⇧V 快速选择浮层，**先 spike**：非激活面板的键盘焦点是 macOS 的已知坑）
  + C-4（对构建产物做运行时启动冒烟，需要安全的数据目录覆盖，绝不碰用户真实存档）。

## 快照 20（2026-10-11，批次 5 收尾 = 第三轮 15 条建议全部落地或写明不做的原因）

- 本轮做完：F-3（⌃⌥⇧V 快速选择浮层：搜索 → ↑↓ → 回车走产品里现成的"复制 + 粘回原应用"，Esc 不动任何东西；
  菜单栏也加了同一命令的入口）与 C-4（`CLIPBOARD_HISTORY_DATA_DIR` 隔离开关 +
  `scripts/launch_smoke.py` 运行时启动冒烟，CI 报告型步骤 + 判定逻辑硬门自测）。
- spike 的价值：审计 §7 要求先 spike 再做 F-3。spike 在裸二进制里**没有判别力**
  （激活前后 `isKeyWindow` 都是 false），所以"非激活面板接键盘"这条路没有被赌进去，
  改成复用产品已验证的激活路径。理由与读数记在 D-041。
- 验证：430 tests 0 失败；`make bundle` 0 warning；78 帧两次同 sha；
  只有「快捷键」与 `settings-min` 两帧变了（其余分区逐字节 0 差异）；5 条新守卫变异对照全过；
  Python 自测 43 个用例 OK（CI 下限从 17 提到 40）。
- **待查（新）**：直接 exec 包内二进制起第二个实例时，`InstanceGuard` 没挡住（本机实测：
  用户实例 54005 在跑，冒烟实例仍开出了窗口）。要么守卫覆盖不到这种启动方式，
  要么它依赖 LaunchServices 会话。真机上值得确认一次。
- **本轮唯一没照抄审计的两处**，都写明了理由：F-3 的默认组合键（⌘⇧V 会抢走浏览器/编辑器的
  "粘贴并匹配样式"）与 U-2 的自定义 drag image 卡片（系统跟手剪影已是那一行本身，见 D-040）。
- 15 条建议的账面状态：C-1 ✅ C-2 ⚠️ 部分（CI 已有帧捕获与本地逐帧 diff，"对上一版本基线"仍未自动化）
  C-3 ✅ C-4 ✅ C-5 ✅ / U-1 ✅ U-2 ✅（卡片那半见 D-040）U-3 ✅ U-4 ✅ U-5 ✅（12/13 焦点环见 D-039）
  F-1 ✅ F-2 ✅ F-3 ✅（组合键见 D-041）F-4 ✅ F-5 ✅。

## 快照 21（2026-10-11，C-2 补完 = 第三轮 15 条账面结清）

- C-2 落地：`scripts/frame_baseline.py` + `docs/frame_baseline.json`（78 帧的 sha256）+
  CI 两步（少帧硬门 / 变帧报告）+ 自测 7 例（含变异对照）。
- Python 用例 43 → 50，CI 下限 40 → 48。
- 15 条建议账面：全部要么落地、要么写明不做的理由（见 `AGENT_FINAL_REPORT.md` §16 的表）。
- 待办只剩三类：真机手点清单、InstanceGuard 对直接 exec 的第二实例是否漏判、12/13 焦点环。

## 快照 22（2026-10-11，修回 CI 形状）

- 23f8da5 把 main 的流水线打成 0 秒失败（步骤名里裸的冒号+空格）。已修（加引号）。
- 新增 `scripts/tests/test_ci_workflow_shape.py`：4 例，不依赖 pyyaml，纳入 Python 硬门步骤。
  Python 用例 50 → 54。变异对照做过（去掉引号即红）。
- 观察点：`gh run view --json jobs` 为空数组 + 日志 not found ⇒ 工作流没解析成功，不是步骤失败。

## 快照 23（2026-10-11，C-2 硬门修到能跑）

- `frame_baseline.py check --allow-missing`（按名字赦免）；CI 复用 /tmp/shots-ci 不再重拍。
- Python 用例 54 → 55。CI run 38073307465 那次红是这一步自己的形状错（D-045），不是产品回归。
## 快照 24（2026-10-11）

- `--allow-missing` 的 help 串里裸 `%` 让 CI 的 python 3.14 构造 parser 就炸（D-046）。已改成 `%%`。
- 新增 `scripts/tests/test_script_help_runs.py`：每个脚本的 `--help` 都要跑得动。Python 用例 55 → 57。

## 快照 25（2026-10-11，C-2 补成"逐版本"）

- `snapshot` / `--against` / `prepare_release` 挂钩 + 真 v1.4.8 基线（worktree 重拍 68 帧）。
- 本轮 vs v1.4.8：变 62 帧、新增 12、缺席 2（glass-pill 改名）。硬门 vs 工作基线 = 全 0。
- Python 用例 57 → 63；CI 两个步骤分别答"纪律"和"历史"两个问句。
- CI 实测（run 38074651028）：全部步骤绿，含 `Runtime launch smoke → SMOKE_OK=1 / SAW_START=True`
  —— C-4 的运行时证据是在 CI 的干净 runner 上拿到的，不是在本机。
## 快照 26（2026-10-11）

- `AGENTS.md` 的 C-5 守卫名是过期的（指向已被变异证伪的均值判据）→ 改为 `testHistoryStoreStaysThin`，
  并新增 `DocumentationAnchorTests` 让"文档点名的守卫必须存在"变成一条会红的判据。
- 那条测试第一版 91.8 秒（平方级扫描），改单遍后 0.06 秒。Swift 430 → 432 例（浮层面板 2 例、文档锚点 1 例）。
- CI run 38075436591 全绿：帧基线两步 + 运行时启动冒烟都过了。
- 又抓到自己一次：一条提交说明写了"已加守卫"而脚本没加上（锚点凭记忆写错）。补上并变异对照；
  教训与 D-048 同族 —— **说明文字描述的东西要当场 grep 一遍是否存在**。
## 快照 27（2026-10-11）

- 删掉 `prepare_release` 里一段永远走不到的回滚码，顺序改成被测试钉住的"最后一步"；
  Python 用例 63 → 64（走完整 `prepare()` 的集成测试 + 失败路径不留基线）。

## 快照 28（2026-10-11，F-4 端到端补齐）

- `HistoryStore.ocrRecognizer` 接缝 + `testIndexOnlyOCRStaysSearchableButLeavesTheArchiveClean`：
  只索引模式下**存档字节里没有识别文本**、搜索仍能命中；落盘模式作正向对照。
  两条变异对照（恒真分支 / 删掉内存索引）都点亮预期判据。
- 15 条建议里对"从产品入口验收"最敷衍的一条已经补平。Swift 433 / Python 64 / bundle 0 告警。

## 快照 29（2026-10-11 晚，新增功能：右侧预览渲染 Markdown）

- 三层判据齐：纯函数 54 例（`MarkdownParsingTests`）+ 呈现层/产品入口/视图树/锚点 28 例
  （`Round4MarkdownTests`）+ 在屏探针 1 例（真窗口里 `.md` 文件确实画成渲染结果）。
  14 条新守卫变异对照全跑：14/14 红在该红的那条，文件逐字节还原。
- 顺手修掉两个不属于本功能的真实缺陷：详情正文与 meta 差 5pt（TextKit `lineFragmentPadding`，D-051 ②）、
  帧基线随系统外观漂移 18 帧（D-052，加了双向守卫）。
- 被实测否掉后放弃的做法记在 D-051：`withAlphaComponent` 烤色（暗色下 1.22:1）、
  源码锚点当行为判据（改成把视图铺进离屏窗口读回属性串）、SwiftUI 按钮的点击自动化（三条路都不通）。

### 这一轮新欠的（下次按价值排的时候带上）

1. **全局次要文字对比度**：`.secondary`（`secondaryLabelColor`）在亮色帧上实测 **4.10:1**，
   低于小字 4.5:1。详情头部 meta、那颗「原文」控件、行、设置、菜单都在用同一档。
   本轮只把新增的那几档做到达标，全局清扫没做（改动面大、要重拍一批基线）。
2. **Markdown 子集缺的部分**：引用式链接、图片、脚注、HTML 块、裸 URL 自动链接、表格列重排
   —— 全部按"原样显示"处理，不丢字但也不渲染。真实 README 里最常碰到的是**图片**和**表格重排**。
3. **文件预览没有搜索命中高亮**（本轮沿用旧行为）：文本条目有、文件条目没有，
   而用户搜完关键词确实会去点开一个 `.md`。要么两边都给，要么明确不给。
4. **链接点击手势未确认**：只读 `NSTextView` 上是单击还是 ⌘-击打开，代码里没写死也没测到，
   手工清单 6.6 条由人确认。
5. **v1.4.9 仍未打包发布**（没人要求；`prepare_release.py` 与帧基线快照链路已在上轮修好并测过）。

## 快照 30（2026-10-11 晚，同一功能的三处收尾）

- 「原文 / 渲染」的入口改成**要求文件还在**（`offers(for:exists:)`，存在性注入进来，
  产品侧走真实 `fileExists`、测试侧走桩），并补了一条变异对照（去掉那个 `&&` 点亮预期判据）。
- 去掉控件的 2pt 纵向 padding：它原本比 meta 文字高，会让头部高度取决于"这条记录有没有第二种看法"，
  换选时下面的列表上下跳。发现方式是重拍帧做差（按钮只占 457 像素，其余 3.4% 全是几何移动）。
  复量三帧的分隔线都在 y=34–35pt。记在 D-051 ⑤ 与 U-17。
- 顺手清掉一个值为 0 的"可调常数"（`baseGutter`）和一条讲反了的注释（文本条目默认渲染，不是默认原文）。
- 判定再收一格：**孤立的反引号不再算"行内码"信号**（必须成对，与解析器要求闭栏是同一条定义）。
  原来任何一个反引号都算一类信号，于是"`# 注释` 开头 + 正文里一个孤立反引号"就凑够两类，
  会把一段日志或配置排成带标题的文档。变异对照（退回 `body.contains("`")`）点亮新那条判据。
- 加了一条**随机模糊**守卫 `MarkdownFuzzTests`：固定种子 20000 例，字符表含标记符、代理对 emoji 与组合变音符号，
  三条判据是「不崩」「单次耗时上有界」「属性串不许短于模型的可见文字」。
  实测全过：稳态单次 < 1ms，最坏一次 25.7ms 是首条的预热（字体与色板惰性加载）。
  手写解析器自己拥有的两种失败形状（没人想到的形状崩掉、某个形状把主线程挂住）真值表覆盖不到，只能模糊。
- 数字：Swift 520 例 / 11 skip / 0 失败；82 帧与工作基线 `CHANGED=0 MISSING=0 ADDED=0`；`swift build` 0 告警。

## 快照 31（2026-10-11 晚，用户真机报：收起侧栏后详情头部压在交通灯上）

- 根因是 v1.2.1 留下的 `.ignoresSafeArea(edges: .top)`：详情头部从窗口顶 10pt 起，
  而交通灯带实测在 19–33pt。侧栏开着时灯压在侧栏上，收起侧栏就撞上。
- 修法：让位量由**摆放按钮的那段代码在运行时发布**（`WindowChromeMetrics`），
  不写常数 —— 带工具栏时标题栏容器 66pt，`max(h-33, 6)` 那个公式把灯带底边稳定钉在 33pt，
  我一开始按 32pt 容器算出的 28pt 常数其实不够。首帧兜底 35pt。
- 改完实测：meta 顶部 10pt → 42pt；22/82 帧变化，基线已更新；Swift 526 例 / 11 skip / 0 失败；
  5 条变异对照全部红在该红的那条（其中一条判据第一版"删掉发布也照样绿"，被变异当场打回）。
- 本机 app 已换成含此修复的构建（`/Applications`，二进制 sha `bf761424…`）；
  上一份留在 `~/Documents/Codex_Project0_backups/before-markdown-preview-20261011-202717/`。

### 这一轮新欠的

6. **帧基线看不见窗口装饰（结构性缺口，不是漏拍）**：离屏帧捕获的是 `contentView`，
   交通灯与标题栏容器不在画面里，所以"内容 vs 窗口装饰"这类缺陷对整条视觉验收流水线不可见。
   可选补法：①给帧加一张"含标题栏"的捕获（需要屏幕录制授权，跨机器不可复现，谨慎）；
   ②更可行的是把这条判据推广 —— 凡是用了 `ignoresSafeArea(edges: .top)` 的视图，
   都必须消费 `WindowChromeMetrics`，做成一条会红的扫描测试（现在只有详情区一处，靠人记着）。
7. **详情头部与侧栏首行的水平关系没有判据**：现在 meta 在 42pt、侧栏搜索框在 62pt，
   两列首行不对齐（差 20pt）。本轮没动它，因为改哪一边都是设计决定。

## 快照 32（2026-10-12 凌晨，用户提议：撤销"收起侧栏"这个能力）

- 收起侧栏的三条路清点完：工具栏那颗（14+ 由 `toolbar(removing:)`、以下由 AppKit 摘）、
  菜单 ⌃⌘S（空组）都早就没了；**真正缺的是拖分隔条**。现在窗口配置器把侧栏列
  `canCollapse = false`，且已折叠的列当场展开（`NavigationSplitView` 会把列可见性存档，
  收起过的那台机器装上新版第一帧就是空的 —— 只关不展开等于没修）。
- 实测：分隔条最左从未钉住的 **-1pt** 变成 **250pt**；硬按到 0pt 之后列宽仍是 250pt（下限由列自己报）。
- 两处被实测打回（详见 D-054）：① 分栏器查找第一版只走控制器树，而真窗口
  `window.contentViewController` **是 nil**，生产里等于永远空跑；② "旧存档展开"那条第一版
  **假绿** —— 换根视图会重建 `NSSplitViewItem`，判据盯的是废弃的壳，补 `XCTAssertIdentical` 才暴露。
- 数字：Swift **531 例 / 0 失败**（+5 条判据）；**7 条变异 7/7 红在该红的那条**（含"钉错列"）；
  82 帧与工作基线 `CHANGED=0 MISSING=0 ADDED=0`；`swift build` 0 告警；Python 64 例 OK。
- 取法：`cd ClipboardHistory && swift test 2>&1 | grep -E 'Executed [0-9]+ tests' | tail -1`；
  帧：`CLIPBOARD_HISTORY_UI_SHOTS=/tmp/shots swift test --filter UICaptureTests` 之后
  `python3 scripts/frame_baseline.py check /tmp/shots --against working`。
- 推上去之后 CI 服务端结论 **success**（`e4b5359`，Swift 6.1.2 / macOS 15）：531 例 / 11 skip / 0 失败，
  且日志里有 `SIDEBAR_PIN 起始宽度=280.0pt 列下限=250.0pt 分隔条最左=250.0pt 按到 0pt 后=250.0pt`
  与 `未钉住：最左=-1.0pt` —— 这五条新判据在 macOS 15 上是真的执行过、数字与本机一致，不是被跳过。
- 已装机：`/Applications` 换成 `14f2f079…`，上一份 `bf761424…` 移到
  `~/Documents/Codex_Project0_backups/before-pinned-sidebar-20261012-002001/`；
  装完用 `ps`/`lsof` 确认跑起来的是新路径那一份；`history.json` 与 `images/` 前后逐字节未变（84 条 / 8 图）。

### 这一轮新欠的

8. **macOS 12/13 上这条没实测**（not-run）：本机 27、CI 15。那两台上 `NavigationSplitView`
   落到的容器不一定带 `.sidebar` behavior；`sidebarItem(of:)` 会退回第一列（真值表钉的就是这个兜底），
   但"退回去之后钉的是不是侧栏"证不了。CI 绿只支持 macOS 15。
9. **用户真机验收还没做**：这一轮改动的唯一人眼判据是"试着拖分隔条，拖不动即成立"，
   已写进 `docs/MANUAL_TEST_v1.4.9_round3.md` 批次 7。
10. **`minimumThickness` 是 SwiftUI 翻译出来的**：判据绑的是"列自己报的下限"，
    所以 `navigationSplitViewColumnWidth(min:)` 改小时判据不会红（这是刻意的：它测的是拖不动，不是宽度值）。
    若哪一天 SwiftUI 不再把它翻译成 AppKit 的下限，"起始宽度 ≥ 下限"那条会先红 —— 届时该重新设计这条判据，
    而不是把 250 抄回测试里。
11. **`WindowConfigurator` 里"补做"的时间点是硬编码的**（`[0, 0.02, 0.08, 0.2, 0.5, 1.0]`）：
    侧栏与工具栏按钮都靠它兜住 SwiftUI 的多次重建。现在有四条事件（成为 key / 成为 main /
    resize / 结束实时缩放）+ 这 6 个延迟兜着，本机够用；但它本质是"轮询到看起来稳定"，
    慢机器上仍可能有一瞬能拖。真正的修法需要 SwiftUI 侧的 API，目前没有。

12. **动效专项（D-055）留下的三条欠账**：
    - Switch Control 那一格降级门没接 —— 没有公开 API，同类是读 `com.apple.universalaccess` 私有键。
      本轮只做到"reduce-motion ∪ VoiceOver"。
    - 设置页换分类、菜单栏状态行两处淡入**没有各自的像素判据**：探针的夹具宿主是 `ContentView`，
      换宿主要再建一套离屏窗口。机制与已量到的三条同源（普通容器上的 `.transition` +
      `.animation(value:)`），但"同源"不是"测过"。
    - CI 上 `Motion filmstrip` 是**报告型**：无头 runner 不绘制 SwiftUI 内容（82 帧里那两帧
      95% 空白是既有事实），所以像素判据在 CI 上大概率是 `MOTION_NOT_RUN`。
      它至少现在**有人跑、退出码有人接**，不再是"注释说跑过"。
13. **`git checkout -- .` 不能当还原手段**：本轮一句它扫掉了 9 个未提交文件（作用域是当时所在目录）。
    凡是会改工作区的脚本，还原一律用事前逐文件 `cp` 备份；变异脚本还必须区分
    `CAUGHT / ESCAPED / DID-NOT-RUN`（补丁没打上时打印"结论无效"，不许输出绿或红）。

## 快照 33（2026-10-12 晚，动效补做：M1 替代路径 / 骨架扫光 / 落点光晕 / 符号反馈）

用户反馈"新版本没加什么动画"。重读报告之后确认是覆盖漏洞而非观感偏差：M1 的**替代路径**
（QuickPick 是真 `NSTableView`）、M5 的**叠加档**（`replace` + `bounce`，MC-12 原话给的两个选项之一）、
M9 的**扫光**、M8 的**后半句**（命中发光）被我一起判成了"砍"。四条全部补上，
决定与取证见 D-056 / U-21，人工验收见 `docs/MANUAL_TEST_v1.4.9_round3.md` 批次 9。

**已实测**：588 tests / 22 skipped / 0 failures；两个 triple 各 0 warning；82 帧 `CHANGED=0`
（`detail-2-file-{light,dark}` 两帧是这次刻意改的加载态，基线已随包更新）；
26 条新判据；16 支变异里 15 支红在该红的那条，第 16 支（M5）故意让它逃逸，据此删了一条死守卫。
像素：QuickPick 行动画 开 11 帧 / 关 1 帧、产品形状（插完行紧接着写同一个选中）11 帧 / 选中真变了 1 帧 —— 这两条要求进程处于**激活**状态（AppKit 的规矩），拿不到时判据报 `MOTION_NOT_RUN=app-not-active` 并 skip，所以本机套件是 13 跑 / 11 过 / 2 not-run；骨架扫 23 对在变 / 减弱动态 0 对。

**欠账（这一节新增的，都带复现命令）**：

0. **① 的两条像素判据在本机是 not-run**：裸 `swift test` 进程拿不到 `NSApp.isActive`（试过 `setActivationPolicy(.regular)` + 1.5 秒重试仍是 false），而 `NSTableView` 非激活就不跑行动画。CI 那台 runner 能拿到。要让它**在本地也可复现**，得把探针跑在一个真能激活的宿主里（`.app` 包内起测试，或在允许激活的登录会话里跑）—— 在那之前本地报 not-run 是正确行为，**不要**为了让它变绿去降低门槛。


0. **CI 报告型那一步会偶发红，原因已经定位**：`testTransitionsAreActuallyRunning` 要求"过渡至少摊到 3 帧"，
   而 runner 的采样比本机粗（本机≈46–54ms/帧，runner≈26–30ms/帧，见 `MOTION_NATIVE 采样≈` 那几行）。
   run 38262248887 里 `notice-banner=2` ⇒ 红；上一次同一份代码是 3 ⇒ 过。**判据本身没错，错在它把
   "帧数"当绝对量，而帧数依赖采样间隔。** 正确的写法是把门槛变成 `declared_duration / 实测采样间隔`
   的函数（下限仍是 2 帧，一帧跳变永远过不了），改之前要先用变异证明"改成函数之后仍然会红"。
   现在**没有**为了消红去动它 —— 这一步是报告型，红不挡发布，而"为了让它绿而调门槛"正是仓库红线里那条。
1. **② 系统符号动效仍然量不到**（两臂同为 1 帧 / 峰值 0.190）。要么哪天换成自绘淡入让它可测，
   要么永远只靠人工 9.3 / 9.4。判据 `testSystemSymbolEffectsAreOutOfThisRulersReach` 会在
   尺子重新看得见它的那天自己变红 —— 不要提前删。
2. **④b 落点光晕没有任何像素证据**：真拖放需要鼠标 + 辅助功能授权（D-034 那一族）。
   现在只有"参数在表里 + 侧栏确实读了它"两条守卫。
3. **`reduce-transparency` 门没接**（本轮 ④c 主动撤下）。要做的是：把 7 处
   `.ultraThinMaterial`（`ViewExtensions.swift:7,9`、`DetailView.swift:159`、
   `HistorySidebarView.swift:353`、`GlassControls.swift:91,179`、`VideoPreview.swift:269`）
   收敛成一份 `GlassSurface` 纯值表，再挂门控 —— 先决定"不透明时是什么底色"，
   那是一个视觉判断 + 一次 82 帧基线重生成，别和动效混在一轮里。
4. **帧间隔判据这次是红的，而且红得不是地方**：`FPS-LOADED p95=28.68ms` 超 20ms 上界，
   但**同一次运行**里 `FPS-MOTION-OFF p95=27.67ms`（曲线全关）同样超，空载基线 16.67ms
   ⇒ 责任在环境（当时 WindowServer 45% CPU、本机还有一份装好的旧包在跑 32%）。
   复现：`CLIPBOARD_HISTORY_UI_INTERACTION=1 swift test --filter UIInteractionProbeTests`。
   待机器安静时复测一次；如果两臂仍然一起超，说明**判据的上界本身要重定**（20ms 是 60fps 的
   理想值，而这条探针在真实桌面上跑），那属于"闸门设计"问题，不该由一次红来偷偷改掉。
5. **一条比本轮更早的红**：`UIInteractionProbeTests/testSidebarListFocusRingAfterClick`
   —— "找不到行代理"。在 `66b6314^` 的干净 worktree 里同样红，把 `HistoryRowViews.swift`
   换成 HEAD 版本再测也红 ⇒ **不是本轮引入**。现场（已写进失败消息）：320pt 宽的侧栏里
   一行变成**两个 148pt 半宽 `KeyViewProxy`**（x=12 与 x=160），探针要求单个 200…290pt。
   两种可能没分清：无障碍结构真退化了（一行被读成两个停靠点），或者只是行内布局变了而
   探针的几何写死。**先按前者查**，因为如果是真的，那是 VoiceOver 用户每天撞的事。
   复现：`CLIPBOARD_HISTORY_UI_INTERACTION=1 swift test --filter UIInteractionProbeTests/testSidebarListFocusRingAfterClick`。
6. **动效胶片套件的判据在测采样率，不是在测动画**（R1 三臂交替实测，D-058）：同一台机器上
   R1 树 → HEAD 树 → R1 树 跑出三套**互不相同**的红集合（3/3/3 全绿、2/3/2 两条红、3/3/3 但另一条红），
   而 HEAD 比 R1 更差。其中 `testListRowsDoNotAnimateAndNothingClaimsTheyDo` 的阳性对照自己读出
   "连横幅淡入都读不出残余 ⇒ 这把尺子在这个维度上没有分辨率"。
   这条**不是 R1 引入的**（ab7a759 已记下同一现象，并明确禁止"调到绿为止"）。
   修法已在下一轮立项：把"过渡帧数 ≥3""after: 3 之后残余"这类**绝对帧数**判据换成
   由"声明时长 ÷ 实测采样间隔"推出来的分辨率感知判据（地板 2 帧，一帧跳变仍然要红），
   且必须带自己的变异对照（`animationsEnabled=false` 那一臂在任何采样率下都要红，不许变成 skip）。
   **已结案（R2 / D-059）**：判据改成分辨率感知 + 触发帧锚点 + 毫秒上限，8 支变异 8/8 CAUGHT；
   过程中还摘掉一条假证据（`notice-banner` 那一卷首尾逐像素相同 ⇒ 改报 `premise-not-visible`）。
7. **两条本轮留下的观测缺口**（都不影响功能，影响的是"下一条判据能不能被相信"）：
   ① `VideoPreview` 的播放控件没有任何夹具帧 ⇒ R1 给它补的分组合成**只有源码级证据**；
   ② `testNoDeadSurfaceInViews` 只扫 `struct X: View`，`ViewModifier` / `ButtonStyle` 那类死包装还在视野外。


8. **`detail-kind-change` 在本机从"判绿"变成 not-run**（R5 / D-063 的代价，不许忘）：
   判据换成时长之后，760×560 窗口的事件内最粗采样 61ms > 0.3×160=48ms ⇒
   `MOTION_NOT_RUN=clock-coarse-in-window`，本机 `judged=1/3`。
   三条可选修法（**都不许改成"把阈值放宽到能过"**）：
   ① 抓帧只抓详情区那一条带（`deltas(_:band:)` 已有，但抓帧成本是整窗的，要先量能不能降）；
   ② 给这个场景单独声明更长的过渡档（改产品参数迁就尺子，优先考虑反面）；
   ③ 接受"本机不判、CI 判"，并把 `judged=n/m` 的下限做成一条判据（**推荐**：
   CI 上 `judged` 必须 ≥2/3，本机只作参考）。
   在 ③ 落地之前，任何人看到 `judged=1/3` 都该知道那是覆盖掉了两条，不是"三条都绿"。
9. **`Views/` 按族扫描的覆盖面仍然只有 `.transition(`**：同一族的"声明了但没供电"还有
   `.animation(value:)` 挂在不存在的键上、`withAnimation` 包住一个不触发视图更新的闭包、
   `symbolEffect` 用在 12/13 的产物上（D-055 已量：`cacheDisplay` 抓不到系统 symbol effect）。
   现在这三类**没有一个按族判据**。R6 若动状态切换，先把 `.animation(value:)` 那一类补上。


10. **「暂停记录剪贴板」缺的是常驻指示器，不是动画**（R6 判定，刻意没做）。
    真值有、开关有、行为有，界面 0 痕迹 —— 但 Toggle 自己已经表达了"此刻是开的"。
    剩下的风险是"三天后忘了自己关过"，那需要菜单栏图标的常驻变体（12/13 与 14+ 两套画法），
    是一件事而不是一帧动画。**用动效化妆会把缺陷留住还多出一层噪音。**
11. **`judged=n/m` 的下限还没有做成判据**（R5 换时长判据之后本机覆盖从 2/3 掉到 1/3）。
    推荐修法 ③：CI 上 `judged` 必须 ≥2/3，低于就把这一步记成未覆盖（红），
    并把这条判定写进 `scripts/ci_report` 的自检夹具。


11. **已结案（R7）**：动效覆盖率下限现在是 CI 里会红的一步（`Motion coverage floor`），
    四个形状钉住它自己（含"该红那格"）。本机 `judged=1/3` 仍然如实存在 ——
    那是抓帧时钟的问题，不是判据放松了；转正需要 ①/② 那两条（分带抓帧或更长过渡档）。


12. **`ReceiptLine` 的自动消失被一条反向判据挡住了**（R8 / M23）。
    如果哪天产品决定"结果文案 3 秒后自己收掉"，**先改判据再改产品**，
    别把判据当阻力绕过去 —— 它挡的是"信息被时间拿走"这一类。
13. **AppKit 混合层的可达性播报仍欠**：QuickPick 空态、设置页回执都只有视觉表达。
    SwiftUI 侧有 `VoiceOverReceipt`（14+），AppKit 侧要 `NSAccessibility.post(notification:argument:)`
    （10.15+ 可用），是独立一轮，别夹在动效轮里顺手做。

## 阶段一（每日复制热图）留下的账 · 2026-10-13

14. **已结案（R10）**：`lastWriteError` 曾经没有发布通道（`DailyCopyLedger` + `SettingsView:848`）。
    它是"计算属性读加锁盒子"——值不会丢，但**没有任何东西为它 `objectWillChange`**：
    写盘失败后若用户不再复制，那一行不上屏；重启后永远 `nil`。
    现在是 `@Published` 镜像 + 一个**只送"该重绘"、不送值**的主队列回头看一眼：
    盒子仍是唯一的值来源，所以通知被丢掉只是晚显示而不是静默（原来那半条性质保住了）；
    `flushPendingSaves()` 也自己同步一次（退出路径上没有"下一次去抖到期"）。
    判据 4 条：不再复制第二次也要看得见 / flush 要报 / 恢复要撤 / **没失败时不许多说话**。
    见 U-32、批次 19。
15. **已结案（R9）**：热图的 hover 动画当时是"声明了但空转"（`DailyCopyHeatmapView:190`）。
    `.animation(.hover, value: hovered?.dayKey ?? "")` 驱动的是不可插值的字符串替换；
    真正会变的格子描边 0↔0.55 与当天那格的深浅都不在事务里 ⇒ 硬生硬灭。
    现在：事务挂在 `onHover` 的变更点上，格子按 `bucket` 插值，页脚那条撤掉并写明"为什么不做"。
    判据 M33/M34/M35/M36/M37 五支钉住。见 U-31。
16. **已结案（R10）**：`OffscreenSymbolInkProbeTests.symbolNames` 曾是手抄的，而且已经漂了。
    名单是 `["command","gearshape","hand.raised","sparkles","folder"]` —— `sparkles` 早就不是
    产品用的图标（推荐分类是 `wand.and.stars`），新增的 `chart.bar` 不在名单里：
    一条"每次视觉审计重新量一遍"的探针，量的是**五个已经不存在的图标**。
    现在名单从 `SettingsCategory.allCases.map(\.icon)` 推导，并加了两条判据：
    `testProbeCoversEveryCategoryIcon`（名单 == 产品）、
    `testEveryCategoryIconActuallyDrawsSomething`（**逐枚**量墨水，抓"符号名写错 / 这枚在 macOS 12 上不存在"
    —— 那种情况下 SwiftUI 不报错，只是什么都不画，整列墨水会被其余五枚抬着走）。
    刻意**没有**加"源码里不许出现字面量名单"那条扫描：名单退回字面量后只要今天恰好相等它就绿，
    而真正会红的是"产品改了它没跟着改" —— 那句话由上面这条覆盖判据负责，扫自己源码只会多一个自匹配坑。
    **顺带记一条判据纪律**：我看 `settings-stats-populated` 帧时把「统计」图标判成"实心柱混进描线那一列"
    （以为踩回 U-8），**这个判断是错的** —— 该探针表头写着未选中行图标列墨水 = 0.0000，
    那一帧只有选中行可见。判图标语言必须按墨水数字判，不能按这一帧的观感判。
    R10 逐枚量出来的数字见下面第 22 条（它同时**否证**了我那个目测结论）。
17. **已结案（R9）**：空态与零值汇总同时说话（`heatmap-empty-*` 帧）。
    现在"共 0 次 · 日均 0.0 · 连续 0 天"整行不出现（决定进策略：`summaryLine(for:hasRecords:) -> String?`），
    「这张图怎么读」也改成跟着图出现 —— 而且写在**观察账本那一层**：
    挂在 `SettingsView.body` 上读到的是开页快照，用户复制第一条之后说明永远不出现（新的"变了但界面不说"）。
    M38/M41/M42 三支钉住。见 U-31。
21. **R9b（下一支）· 新加的三条动画还欠像素证据**：本轮只有结构判据 + 静帧。
    要做的是让 `MotionFilmstripTests` 的 `Scenario` 能挂**非主窗口**的根视图
    （现在 `recordFrames` 把根视图写死成 `ContentView(historyStore:)`），
    然后加一条 `heat-cell-deepens` 场景：从产品入口 `store.add(...)` 触发，
    量那一格包围盒里的"变化段时长 / 事件内最粗采样"，并配 `animationsEnabled=false` 的 A/B。
    **别用静帧代替这一步** —— 静帧只能证明"画出来了"，不能证明"分摊到几帧"。
22. **新量出来的一条：设置侧栏六枚图标里「推荐」那枚细一半**（R10 逐枚墨水，固定黑、和产品同构的    `List(.sidebar)` + `.plain` Button + `.hierarchical` + 13pt）：
    ```
    INK 逐枚 chart.bar=0.0138 command=0.0143 folder=0.0124 gearshape=0.0130 hand.raised=0.0118 wand.and.stars=0.0052
    ```
    五枚挤在 0.0118–0.0143，`wand.and.stars` 只有 0.0052 —— **比同列最轻的那枚还轻 2.3 倍**。
    两件事同时被这条数据确定：① 我上一轮目测的"`chart.bar` 是实心柱、混进描线那一列"**是错的**
    （它是第二重的一枚，不是异类）；② 真正的异类是「推荐」，而它从 D-8 那一轮起就在，
    只是当时整列一起量、看不出来。
    **本轮刻意没改**：换符号（`wand.and.stars` → `sparkles` / `star.leadinghalf.filled` …）
    是"图标语义 vs 视觉重量"的取舍，得连着"推荐这一页到底想说什么"一起判，
    归到设置页那一轮（R11/R12 的选题池里）而不是顺手换掉。
    阈值判据也**没有**现在加：拿今天的六个数反推一个"不得低于中位数 60%"的门槛，
    等于把一次观测写成规律 —— 等真去改那一枚时再决定要不要钉。
18. **`/tmp/verify_phase1.sh` 里 `grep -cE "error:"` 数出 110 条"错误"，全是 CoreData/AddressBook 噪声**
    （`com.apple.contactsd.persistence` 那一族）。**计数命令自己没被证伪过**（这一族记过很多次）。
    下一版只数 XCTest 的失败行，并把"噪声行"单独报成一个数而不是并进错误里。
19. **阶段二的全量位点清单在 `.scratch/motion-audit-2/00-inventory.md`**：
    两个只读代理并行产出，主窗口/QuickPick 89 行 + 设置/菜单栏约 90 行，
    含 MotionCatalog 八档引用表（`.skeletonSweep` 的 curve/transition 与 `Shape.Slide.bottom/leading/trailing` 是死的）、
    两套互相矛盾的 reduce 闸门、以及去重后的 20 条"最可能真缺陷"合并榜 + R9–R28 排期。
    **它是选题池不是结论**：每一行都要在轮次里用渲染像素重判一次才算。
20. **「连统计一起抹」是独立动作，本轮刻意没做**：导出/导入/清空历史/隐私擦除都不碰 `daily-copy.json`。
    真要"抹掉统计"得单开一个入口并在 `AGENT_DECISIONS` 立案（它现在只被"保留 730 天"这一条管着）。
23. **动效像素判据的可见面 = 模型树逐帧变化，纯 opacity 淡入不在里面**（R11 双向 A/B 实测）。
    `MOTION_HEAT_FADE_A/B 开 帧数=1 峰值=0.225 关 帧数=1 峰值=0.225` —— 目录开着与关掉读数一模一样，
    因为 `cacheDisplay` 抓的是**模型树**，而淡入活在 presentation 层。
    这条限制影响的是**怎么读以前所有轮的 MOTION 数字**：
    能量到的是带布局位移的那类（提示条滑入、换类型时整块预览换位、空态↔列表、AppKit 行动画），
    量不到的是纯淡入淡出（`contentFade` 那一档的大多数用法）。
    所以"MOTION_SUMMARY 3/3/3"从来不代表"所有动效都被验过"，它只代表"能被看见的那几件在动"。
    **待办**：要么给这类过渡加一个可测的形状（淡入 + 1pt 位移，位移活在模型树里），
    要么在总报告里把"已验证/源码已接产物未量/人眼判"三类分开列清楚。
    现在选的是后者（诚实且不为了讨好尺子改产品手感）。
24. **让"悬停"可被取证（R13 候选，做成一次解锁一片）**：清单里约 15 处位点的唯一反馈是 hover
    （行底色、清除钮图标、44pt 圆按钮、多文件行、热图描边、这次的段按钮底色…），
    而仓库**没有**任何一条判据能证明"悬停时那层东西真的画出来了" ——
    合成 hover 这条路一直没打通（`NSApp.currentEvent` 在合成事件期间是 nil，那一族记过），
    离屏捕获又永远以 `isHovered = false` 渲染。
    要做的是给交互探针加一条**真** `mouseEntered`/tracking-area 通路（在能激活的宿主里发事件），
    并让 `MotionFilmstripTests` 能框住单个控件的包围盒判"变化段时长"。
    做成 ⇒ 上面这些位点从"源码已接"升级成"产物已量"；做不成 ⇒ 它们永远只能靠人眼批次。


25. **悬停药丸的几何 = label 的包围盒，比系统工具栏的那颗小一圈**（R13 复核时想到，**刻意没在本轮改**）：
    `PressedStyle` 的底色铺在 `configuration.label` 上，所以 16pt 图标的悬停高亮就是一圈紧贴笔画的
    圆角矩形；系统工具栏按钮的高亮是"图标 + 每边约 4–6pt"，且**命中区与高亮同尺寸**。
    改法有两条，选哪条要先能看见：① `PressedLabel` 内给 label 加 `labelPadding`（默认 0，
    只在图标类站点抬），命中区跟着长；② 只把 overlay 用负 padding 放大，布局一动不动，
    但会出现"药丸比可点区大"。本轮**不做**的理由：BACKLOG 24 没做之前这两条都无法验收，
    而 ① 会改动多处静止态（要重审一批帧）。**顺序：先证据通道（R14），再几何（R15 候选）。**
26. **有些状态从来没有帧**（R13 发现）：本轮改了排除名单的「移除」与回执的 ×，
    但 `FRAME_BASELINE_CHANGED=2` 里**没有**设置页的帧 —— 因为这两个控件只在
    "用户自己加过排除 App"与"刚导出/刚清空"之后才存在，90 帧夹具里没有这两种状态。
    也就是说这两处的改动是**源码已接、产物未量**（不是没生效，是尺子那儿根本没有这一帧）。
    R14 与 BACKLOG 24 一起做：给夹具补两帧（`settings-privacy-excluded`、`settings-data-receipt`），
    让"回执行"与"移除钮"第一次进入基线。


27. **用户自己加的排除项被埋在 10 行默认清单之后**（R14 拍新帧时发现）：
    隐私页的「不记录这些 App 的复制」里，`ForEach(默认)` 在前、`ForEach(用户)` 在后，
    真实窗口 540 高 ⇒ 用户那一行与它的「移除」在折叠线以下，**要滚动才看得到**
    （我的夹具帧第一次拍 540 高时根本没拍到它，才改到 1040）。
    该不该反过来（自己的在前、默认清单收成一段说明或折叠）是一个交互决定，不在动效轮里顺手改。
    判据侧已经先受益：那颗「移除」从本轮起有帧了。

28. **约 15 处 hover-only 位点的"表达"从此可量、"触发"永远只能人眼**（R14 结案 BACKLOG 24）：
    `testFillLaddersAreVisibleOnBothControlClasses` 量的是底色台阶（含真实尺寸与两种外观），
    它**不**证明指针能触发那一档。以后每一轮新增 hover 位点，
    要么把它的档位并进这条梯子（可证），要么明确记"只有人眼"（不可证）——
    不许再写"已验证悬停反馈"这种把两半混起来的话。

29. **R13/R14 这一对给出的通用规矩**：新增一档视觉强度时，必须同时看它**左右两个邻居**的台阶，
    而不是只看"它比 0 大不大"。R13 抬 `controlHover` 时只证明了"比 idle 看得出来"，
    没证明"与 pressed 还分得开"，于是修一个反馈弄没另一个，而当时所有判据全绿。
    这条应该在 R15 做成一条守卫：**任何 `VisualFill` 档位变动，都要跑一遍两类控件的完整梯子**
    （现在只有测试里有，没有"改了令牌必须跑它"的强制路径）。


30. **帧夹具只会拍 SwiftUI，AppKit 表面一张帧都没有**（R17 发现，结构性缺口）：
    `UICaptureTests` 的 `Fixture` 是 `() -> AnyView`，整个 96 张基线全部经由 `NSHostingView` 产出。
    于是这些表面**从来没有**被静态复核过：
    ① 快速选择浮层（`QuickPickController` 自建的 `NSPanel` + `NSTableView`，行是 `NSTableCellView`）；
    ② 详情区的 `NSTextView` 富文本/Markdown 渲染层（SwiftUI 里只是一个 `NSViewRepresentable` 壳，
       壳能拍到、里面的排版拍不到）；③ 视频预览的 `AVPlayerView` 表面；④ 菜单栏的原生 `NSMenu`。
    这解释了为什么 R13/R14 里"某些控件没有帧"看起来是"状态不存在"，
    而**更深一层的原因是那个表面根本进不了夹具**。
    要做的是给 `Fixture` 加一条 AppKit 通路（`buildAppKit: () -> NSView`，
    渲染时同样走 `cacheDisplay`），然后至少补三张：`quickpick-list`、`quickpick-empty`、
    `quickpick-scrolled`。**在那之前，任何关于 QuickPick 观感的结论都只能是胶片 + 人眼**，
    本轮（R17）就是这种情况，已在账本里如实记。
    → **R18 结论"因为材质不可合成所以补不上"是错的，R19 推翻**：浮层里根本没有材质视图，
    而裸材质离屏画得出来（spike 读数 `(58,58,58,a=255)`）。真正的原因量出来了：
    产品的 `NSStackView` 在捕获环境里只有 **24pt 宽**（真实 App 里 420×300）⇒ 滚动视图 0×0 ⇒
    `NSTableView.visibleRect` 0×0 ⇒ 5 行画不出一行。**这条继续开着**，下一步要答的是
    "让 stack 拿到宽度该由谁做"：产品侧（它本来就打算撑满，是 autoresizing 在离屏没生效）、
    还是夹具侧（那就得接受帧画的是夹具想要的布局 —— 目前判为不可接受）。
    → **R63 把 ① 结掉**：答案是"产品侧"，而且不是"离屏没生效"—— `NSStackView` 生下来
    `translatesAutoresizingMaskIntoConstraints == false`，那两行**在真机上同样是空操作**
    （最小对象图 spike + 两条路各量一次）。修完补进基线三张 × 亮暗 = 6 张：
    `quickpick-list / -typed / -empty`，116 → **122 帧**。
    **②③④ 仍然开着**（详情区 `NSTextView` 的排版、`AVPlayerView`、原生 `NSMenu`）——
    这一轮证明的是"AppKit 表面进得了夹具"，不是"那三个表面已经能看"。
    判据现在是三层（症状 / 标题 / 原因），见 `testQuickPickOverlayCannotBeCapturedYet`。

31. **选中态在离屏帧里是一块纯黑，只数得出来、看不见**（R18 发现，与 30 同一机制）：
    系统 `List` 的选中高亮是材质 ⇒ 离屏画成 #000（亮暗都一样），
    于是"选中"这个用户点名要审的状态**没有像素证据**：颜色、对比度、圆角、内边距全都量不到。
    现在每张帧报 `blackBandPt`，8 个夹具名钉在 `materialBlindSpotFixtures` 里（多一个红、少一个也红）。
    两条候选路，**①已经试过了**（R19）：
    ① 把捕获窗口真的 `orderFront` 到屏幕外 + 转 runloop + `tile()` + `display()` ⇒
       **那块黑仍然在**（`blackBandPt` 逐帧不变），而 `isKeyWindow=false`。
       所以它要的不是"上屏"，是 **key window** —— 而测试进程拿不到（拿到的代价是抢用户前台，
       这条是测试套件的硬边界）。风险记录：`orderFront` 会让窗口真的进入窗口列表，
       在 CI 那种无头 runner 上行为可能不同 ⇒ 这一套现在**只作用于 AppKit 夹具**。
    ② 自绘选中底色 —— **仍然不许顺手做**：D-034 明确否掉过"系统一套 + 自己一套"的选中语言。
    剩下可试的只有：让捕获进程成为激活应用（`NSApp.activate`）—— 那会在用户屏幕上抢焦点，
    除非能证明它只在无头 runner 上发生，否则不做。

32. **夹具的高度仍然是记下来的数**（R18 发现，M76 证伪了"有守卫"这个错觉）：
    `weights` 那帧裁掉头部九轮没人发现，本轮把它改成 880 —— 可是**改小回去不会有任何测试会红**
    （变异 M76 = ESCAPED，是这一轮唯一一条"知道会漏还故意放"的变异）。
    为什么没有现成的尺：`host.fittingSize` 在夹具里有 `.frame(height:)` 时恒等于被钉死的那个数
    （实测 +32pt 标题栏），是**一条恒真的尺**；而"边缘有没有墨"这种像素判据对
    `content-*` 那类满幅布局必然误报。
    可行的做法（下一轮或下下轮）：给 `Fixture` 加一个 `contentMustFit: Bool`，
    为 true 时**先不带 `.frame(height:)` 量一次真实内容高度**（`fixedSize` + 顶对齐 + 墨迹范围），
    再断言夹具声明的高度 ≥ 量出来的高度。代价是这类夹具多拍一次。
    **R20 进展**：`search-field` 那帧自己撞上了这一类（320×96 一直在裁下半条，抬到 112 才完整），
    而 `testSearchFieldKeepsTheSameHeightInBothStates` 用的正是"把夹具内容真的量一遍"的手法 ——
    它证明了这条路可行（`filledBands` 找带 + 高差 ≤ 2px），只是现在只覆盖了一处。
    **R22 已做**：`Fixture.contentMustFit`（10 张自包含帧点名开启）+ 判据"帧的**最底一行**不该有墨"
    + 一张**正对照**（`sidebar-history` 底行 100% 有墨，防止把阈值调到天上而没人红）。
    变异 M97（`weights` 改回 560）与 M98（`search-field` 改回 96）都抓到了，M99（把尺弄瞎）由正对照抓到。
    列表/滚动区那批**刻意不开** —— 它们天生会被裁，判它们等于把滚动视图的正常行为报成缺陷。

35. **一条文字的警告横幅占 88pt，两行文字的错误横幅只占 50pt**（R22 新增帧量出来的，未修）：
    `content-with-two-notices-750x560` 沿一列的色度扫描 ——
    y 0–88 是 `rgb(255,241,229)`（橙 12%）、y 90–140 是 `rgb(254,235,235)`（红 10%）、y≥145 是详情区底。
    两个候选解释**都还没排除**：
    ① 全尺寸内容窗口（产品 `WindowConfigurator` 确实设了 `.fullSizeContentView` + 透明标题栏）下，
       横幅的**底色涂到了标题栏后面**，而文字被安全区顶下去 ⇒ 第一条横幅看起来上半截是空的；
    ② 那 88pt 里其实是**两条**同色横幅（`makePopulatedStore()` 是否自带恢复提示还没核）。
    为什么本轮不修：**没读懂之前不动产品** —— ①的修法是让底色不越安全区，
    ②的修法是夹具多挂了一条横幅，两种改法互斥，猜错就是把界面改坏。
    R23 第一件事：用 `inspect_r20.swift column`（新加的色度扫描，亮度分不开的那两块用 R-B 分）
    沿 x=400 与 x=40 各扫一遍，数 `Divider` 的条数，判掉解释②；
    再决定①要不要修（系统里"提示条不该把颜色涂到红绿灯后面"是我的判断，需要人工批次复核）。
    **R23 已判已修**：解释②出局（那里没有第二条横幅 —— 沿列扫只有一处墨）；
    ①成立：`safeAreaTop=52` 而底色从 y=0 就铺上去 ⇒ 根因是
    `.background(ShapeStyle)` 在 SwiftUI 4 默认 `ignoresSafeAreaEdges: .all`。
    修后一条文字的横幅 88pt → **38pt**，装饰区 `R-B` +26 → **0.0**，
    行带尺确认 4 张帧只有 `0.0–52.0pt` 不同（零布局位移）。判据 `testNoticeTintDoesNotReachTheTitlebar`
    自带正对照，变异 M101–M103 全 CAUGHT。

36. **组件帧 `notice-banner` 展示的布局在产品里不存在**（R23 明确留下）：
    那张帧用 `VStack(spacing: 12)` 摆两条横幅，而产品是 `VStack(spacing: 0)` + 每条自带 `Divider`。
    R22 已经为这个毛病立过一次规矩（"夹具只能呈现产品的决定"），
    但当时只补了新帧、没改旧帧 ⇒ 旧帧仍然在教读者一个错的形状。
    改法：把组件帧改成 `spacing: 0`，让它与 `content-with-two-notices` 读出来一致
    （两张帧从此互为对照）；顺带把 `contentMustFit` 的那条断言复核一遍
    （间距从 12 变 0 之后 170pt 的框会多出 24pt 余量，可能反而暴露"帧比内容高太多"这种新问题 ——
    那是另一族：帧太大与帧太小一样会骗人）。
    **R24 已做**：组件帧改成 `spacing: 0`，与产品同值（带间缝 13pt → 1pt，两张帧从此互为对照）。
    估的那次"收高度"被自己的 `contentMustFit` 打红（150pt 会裁内容），量出来这张帧的内容是 y41–160
    ⇒ **高度保持 170**，"帧太大"这一族本轮只做到"能被看见"（判据会打印每条带的 y 范围），没有立闸。

33. **图标控件的静置对比度从来没有尺**（R20 看着帧量出来的，本轮未修）：
    搜索框清除 × 的字形 vs 它自己的底 = **暗色 2.22 / 亮色 1.86**，
    低于本仓自己的可辨线 3.0（同一帧里占位符文字 9.42 ⇒ 尺没坏，是颜色档选错了：
    `.tertiary` 是给注释用的，不是给"要点的东西"用的）。
    R20 把它的命中区从 14pt 抬到 22pt，于是这条更值得修 —— **看不见的大目标仍然是看不见**。
    要做的不是一处改色，是**一把尺**：把"字形 vs 它所在的底"的对比度从文字推广到控件，
    扫全部图标按钮（行首星标、清除 ×、播放、静音、药丸四颗、侧栏五颗批量按钮、回执 ×、排除名单「移除」）。
    现成的地基：`inspect_r20.swift stats`（仓库外，众数=背景、最暗/最亮 2% = 字形、WCAG 比值）。
    落进仓库的方式应该是夹具帧上的一条判据，而不是源码字符串判据 —— 这条判的是**产物**。
    修的方向：静置 `.secondary`（两态都过线），悬停那一下交给 R20 刚加的底色药丸 ——
    颜色说"这是控件"，药丸说"指针在这儿"。代价：静置与悬停不再靠颜色区分，要靠帧与人工两条覆盖。
    **R21 已做**：尺进了仓库（`UICaptureHarness.inkContrast` + 四处探针 × 两外观 + 算术真值表），
    两处不过线的控件抬到 `VisualInk.control`（× 3.74/5.34、箭头 3.85/6.06），
    `.tertiary` 从此有按文件点名的账本；变异 M90–M94 五支全 CAUGHT（M92 专门核"红得对"）。

34. **文字那一侧仍然没有对比度尺**（R21 明确留下，不做是因为"没有消费者的门槛等于没有门槛"）：
    本轮把地板推广到了**控件**（3:1），而 `smallText=4.5` 我第一版写了、然后删了 ——
    这一轮没有任何一条判据读它。现在能看到的候选缺陷（都还没量）：
    ① 热图的星期/月份刻度仍用 `.tertiary`（三处，已点名登记为"非控件"），
       11pt 以下的刻度文字按 4.5 判很可能不过线；
    ② `VisualFont.meta` 那一档（10–11pt）的次级说明文字（行内"…/Downloads"、设置里的说明段）；
    ③ 菜单栏里那两行灰色副标题（`MenuBarController` 用 `secondaryLabelColor`，R2 判过一次但没量）。
    做法与本轮同形：一把 `inkContrast` 的**文字版**（同一块底上取"最暗/最亮 2%"当字形），
    加一条按夹具点名的表；区别是地板换 4.5，而且**要区分"装饰性刻度"与"要读的信息"** ——
    后者过线，前者可以放（放的时候要写理由，就像 R21 对药丸那次一样）。
    **R27 把 ① 关掉**：热图三处刻度实测 1.88/2.27 ⇒ 提到 `.secondary`，
    并且把"装饰 vs 要读"这条线做成了**梯子**（`captionInk = 3.5`，不是 4.5 —— 系统 caption 档自己只有 4.0）。
    R21 给刻度开的免检被重新判过一次并撤销：要读的标签没有理由比能点的笔画更淡。
    ②③（`VisualFont.meta` 说明段、菜单栏副标题）仍开放 —— 尺与地板都在，缺的是逐处点名建表。
    **R33 把 ②③ 点名建表**：通用页三段 `.secondary` 说明 + 菜单栏副标题与行右端理由进了
    `captionInkProbes`（8 条 × 两档，比值 0.95–1.03），并且给整张表补了**天花板** ——
    原来那些"通过"只证明了框里有足够深的墨，没证明框里是说明段的墨（D-092 / 第 35 轮）。
    **R28 补记**：这条尺在 CI 上红过（`captionInk = 3.5` 是本机数，macos-15 runner 上
    `.secondary` 自己只读到 2.85 / 3.30，run 38443414396）⇒ 已改成
    "同一台机器、同一外观现拍的 `.secondary` 当参照"（`captionTierTolerance = 0.8`，D-087）。
    继续点名之前先确认自己用的是相对参照那条。
    **R24 部分完成**：尺进了仓库（`UICaptureHarness.noticeBands` + `testNoticeBodyTextStaysReadable`），
    地板按它点名的换成了 4.5，并且**不写死坐标**（逐行取众数自己找带，比"按夹具点名的表"更耐漂移）。
    第一个对象是**横幅正文**：亮色 3.82–3.92 → 12.98–13.94，暗色 5.26–5.58 → 10.48–11.54（D-083）。
    ①② 三处仍未点名建表 —— 尺已经有了，缺的是"这块文字是要读的信息还是装饰性刻度"的分工与逐处读数。

37. **多行横幅里那枚动作按钮跟着第一行走**（R24 开场看到，本轮未修）：
    `StateLine` 是 `HStack(alignment: .firstTextBaseline)`，所以正文两三行时"知道了"压在上三分之一处
    （组件帧实测：带 y 41–92，按钮中心 y≈66）。系统里那类顶部提示条（邮件/备忘录/设置）
    动作位是**垂直居中**的，读起来像"这个动作管整条"，而不是"管第一行那句话"。
    难点不在改一行 `.center`：`StateLine` 同时服务横幅、菜单栏行、空态三种表面，
    单行时 first-baseline 与 center 的差就是图标要不要下沉的那 1–2pt。
    改法应该是**按 surface 分**（这也是 `alignment(for:)` 早就分了、而 `StateLine` 没用它的原因要重查），
    并且要先量"单行时居中会不会让图标与文字错位" —— 判据现成：`notice-banner` 与 `content-with-notice`
    两张帧的按钮中心 y 与带中心的差。
    **R25 已做**：先量后改 —— 偏移实测 单行 0pt / 两行 −6.5pt / 三行 −14.5pt；
    改法是"一行里两根轴"（内层 baseline 钉图标+文字，外层 `.center` 只管动作位），
    所以"单行时图标会不会浮半格"这一问根本不会发生。修后 10 条带全部 +0.0。
    顺带量到两件新事：① 动作框的宽度必须贴着按钮（第一版 95pt 把正文混了进来）；
    ② 多行横幅因此矮 1pt（按钮下沿以前把行撑高 1pt）—— 本轮**不是**零位移，已写进 D-084。

38. **"带里有墨"这条地板拦不住"框里有别的控件"**（R24 的 M108 证伪了我自己的说法）：
    把文字列挪到 x=470 之后，那块区域里正好躺着"知道了"按钮 ⇒ 墨占比 10.9%（地板 2%）轻松过，
    真正拦住它的是对比度地板（量到 4.13）。也就是说这条地板只挡"框套在纯底色上"这一种漂移。
    要补的判据很具体：**左对齐的正文必须在带首 60pt 内有墨** ——
    如果哪天按钮换边、横幅变窄、或消息本身没渲染出来，尺就会开始量按钮而不是红。
    本轮不做的原因：不为一条"已知拦不到的假想漂移"扩范围，且 M108 显示今天有第二道拦网。
    **R26 已做**：左锚定地板进了判据（`testNoticeBodyTextStaysReadable` 里第 ①b 条：
    正文最左的墨必须落在文字列的左起三分之一内），并用 **M114**（R24 M108 的原样重放）验过牙口 ——
    这次红在该红的那句上（`这一列里没有正文，量到的墨是别的东西`），不再红在对比度上。

39. **详情区有三条左轴，不是一套语言**（R26 第一次拍加载态时量出来的，本轮不当判据）：
    骨架条带与那一句在 **20pt**（`DetailTypography.containerGutter`），
    详情头部的 meta 行在 **54.5pt**（它被 `columnWidth()` 限成可读列之后居中），
    而正文列的左缘约在 **95pt**。三件事叠在一起的意思是：
    "这条记录的内容从哪儿开始"没有唯一答案，取决于你看的是哪一块。
    为什么本轮不修也不钉：这是**设计决定**（要不要让头部与正文同列、骨架该承诺哪一列的宽度），
    不是可以量出来的缺陷；拿 54.5 去钉骨架，等于把"头部被居中"这个中间状态钉成规矩。
    要做的顺序建议：① 先定"详情区有几列、每列的左缘是谁"（写进 `DetailTypography`），
    ② 再把骨架承诺的宽度改成它替代的那一列（现在最宽那条是 0.86×面板，比正文列宽一截），
    ③ 判据用现成的 `leadingInkColumn`，两帧各量一次即可。

40. **「清空」这颗按钮在帧里不是红的**（R28 看到，本轮**没有判定**）：
    产品代码是 `Button(role: .destructive).buttonStyle(.borderedProminent).tint(.red)`
    （`SettingsView.swift:607-611`），而 `settings-data-*-light.png` 里它是浅灰药丸 + 黑字，
    与旁边两颗 `.bordered` 的「导出/导入」看起来同一档。
    两种解释都能自圆：① prominent 的填充是材质，在没上过屏的窗口里不合成
    （R18 那族盲区，`materialBlindSpotFixtures` 只登记了 List 选中那一族）；
    ② `.tint(.red)` 真的没吃到。**分不清，就不许当成缺陷去"修"** ——
    唯一的判据是一次真机截屏，已进人工批次 36。
    要做的顺序：真机看一次 → 若红色正常，就把这颗按钮登记进"材质盲区"名单并写清是哪一族；
    若真的不红，那是产品缺陷，判据可以照 R21 的 `controlInk` 写（红底上的白字对比度另算）。

41. **反相墨这条通道仍然只挡住了"图标"**（R28 的分类只覆盖了侧栏那一列）：
    `signedInk` 现在只在 `OffscreenSymbolInkProbeTests` 里用，而同一族故障（语义色在离屏被解析到
    另一套外观）理论上也会打到**文字**上 —— 今天没看到，是因为亮色帧里正文文字确实是黑的（R24 量到 12.98）。
    如果哪天某处文字也反相，`inkContrast` 会读出"对比度 1.0x"并把它报成"太淡"，
    而正确的结论是"这条帧不可信"。做法与本轮同形：把"偏亮 / 偏暗"分开数这件事
    从探针搬进 `UICaptureHarness.inkContrast`，让所有用它判"淡不淡"的地方都能被这条区分保护。
    **R29 已做**：`inkTailSplit` + `inkIsOnTheExpectedSide` 进了仓库尺，
    两条"太淡"判据（控件墨、说明文字梯子）的失败消息各挂一行方向诊断；
    正对照用真的坏帧（`图标列 亮35/暗0` vs `标题列 亮0/暗118`），真值表七条，变异 **M130** 有牙。
    **R29b 把最后那一半也收了**：先量后挂 —— 横幅正文在彩色带上的尾墨方向实测
    `content-with-notice light 亮0/暗2277`、`dark 亮2277/暗0`（四张帧 × 两外观全部单边、方向正确），
    确认"反相在那种底上会读到什么"之后才把诊断行与一条 `inkIsOnTheExpectedSide` 硬断言挂上去。

43. **CI 的 macos-15 runner 拍不出「设置」这一页**（R29 的 CI 红暴露的，run 38453566489）：
    `settings-general` 的图标列与标题列**都读到 0 个偏离像素**，`settings-shortcuts` 整帧墨量 0，
    而同一次运行里 430pt 的热图帧（比值 2.85/3.30）与 750pt 的横幅帧（正文 10.5–14.0）都正常。
    ⇒ 之前记的"宽度 >750pt 就不行"这个边界**也是错的**：720×540 的 `settings-general` 同样空白。
    现在能说的是：**空白跟着 `SettingsView` 走，不跟着尺寸走。**
    两条依赖设置页的判据（`testSettingsHelperTextIsNotClipped` / `testInkDirectionRulerReadsBothEnds`）
    改成"读到 0 就记 NOT-RUN 并打印诊断（帧尺寸 / scale / 透明率）"，
    本机仍然实跑（`720=23889 / 640=23868`、`图标列 亮35/暗0`、`标题列 亮0/暗118`）。
    要做的：下一次 CI 读 `TEXT_INK_FRAME` 那几行 —— 如果 `transparent=100%` 就是没画，
    如果是 `0%` 且像素均匀就是画了一块底色；两种的下一步完全不同。
    **R29c 已经读到答案**（run 38455986013，判据当场绿）：
    `px=720x540 scale=1.0 bpp=32 samples=4 bpr=2880 transparent=0.0% hist=0/0/0/0/0/0/1/99%`
    —— 三件事一次定清：
    ① **不是字节布局读错**（bpp=32 / samples=4 / bpr=宽×4，与尺的假设一致，本机同构）；
    ② **不是"没画"**（透明率 0%，窗口是有底色的）；
    ③ 是"**画了一块底色**"：99% 的像素落在最亮那一档，只有 1% 在次亮档 —— 也就是只有窗口
       边框/红绿灯那类东西，内容一个字都没有。本机同一张帧是 `hist=0/0/0/1/0/0/1/97%`。
    顺带量到一条之前谁都没说的：**runner 是 @1x 截图**（`scale=1.0`，本机 `scale=2.0`）。
    这条比"设置页空白"更普遍，而且它把 R27 那次 CI 红的解释换掉了：
    不是"平台把 `secondaryLabelColor` 解析得更淡"，是**半分辨率下细笔画根本进不了"最暗 2%"那一档**。
    仍开放：为什么只有 `SettingsView` 这一棵视图树在 macOS 15 的离屏路径上什么都不画。
    下一步不该是继续猜，而是换取证通道（真机截屏，或像 R19 那样试 orderFront）。

44. **帧基线是"同一台机器"的闸，不是跨机器的闸**（R29b 顺手查出来的，之前没人量过这件事）：
    最后一次绿的 CI（run 38441990109）里真实的那一次比较是
    `FRAME_BASELINE_COMPARED=102 / CHANGED=62 / MISSING=6` ——
    **102 张帧里有 62 张在 runner 上与本机的哈希不同**（含全部 `settings-*`、`row-*`、
    `sidebar-*`、`notice-banner`、`menubar-*`），只有约 40 张两边一致。
    这一步是"报告型不挡发布"，所以从来没人看见过这个数。
    它意味着两件事：① 逐字节帧闸的语义是"**我这台机器上，界面没有意外变化**"，
    跨机器比较无意义，也不该被当成"CI 验证了界面"；
    ② 任何**依赖某张帧的绝对像素读数**的判据都可能换平台就不成立 —— 这一族已经犯过两次
    （R27 的 `captionInk=3.5`、R28c/R29 的设置页空白），第二次比第一次更严重，
    因为它不是"数不同"，是"那一页什么都没有"。
    要做的：把 `CHANGED=62/102` 这个数字本身变成一条可打印的账
    （CI 里报"这台机器与本基线一致 X/102"），并规定**判据只能用比值/方向/单调性**，
    不能用绝对像素数。

42. **CI runner 上"宽离屏帧"这一档不可信（两次独立现象，根因未证明）**：
    ① R3-D11：`content-wide-1100x800` 亮暗两帧在 macos-15 runner 上 95% 像素未被绘制；
    ② R28b：`settings-shortcuts-wide-1100x540` 同一 runner 上**整帧读出 0 墨**（run 38449711539），
    本机同一份代码读到 23864 个文字像素。两条都落在 **1100pt**（@2x = 2200px，越过 2048）这一档，
    750 / 720 / 640 从未出过这个问题。
    要做的：把一张已知有内容的帧在 900 / 1024 / 1100 三档各拍一次，看读出墨量的**断崖在哪一档** ——
    断在 1024 与 1100 之间就支持"离屏表面尺寸上限"这条假设，否则要回头查布局。
    在此之前：任何以"宽帧"当参照或当证据的判据，**必须自带"参照必须有墨"那条红**
    （R28b 的教训：没有它，"两臂都空"会被读成"产品没问题"）。
    **R28c 追加一条把这条假设打脸的证据**：降到 **900pt 仍然整帧 0 墨**（run 38451162726），
    所以"越过 2048px"这个解释**已被证伪**。目前可复现的边界是
    "`≤750pt 的 100 张帧全部正常，>750pt 的两档（900 / 1100）全部读 0`"。
    因此判据侧已经改成**只用 ≤750pt 的臂**（参照臂换成更窄的那一臂），
    并新增一条资格断言"两臂都必须 ≤750pt" —— 这条断言就是本条账的看门人。

45. **暗档帧里"未选中的侧栏行"是黑字黑底，机制未定（R29d 量出来的，U-52）**：
    实测（@2x 本机帧，区域众数色当底、偏离 >8 记一侧）：
    `settings-shortcuts` / `settings-min` 暗档里第 2 行标签 587 个**暗**墨像素、0 个亮墨，
    第 5 行 668 暗 / 0 亮；亮档同一位点是 733 / 771 个暗墨（正常）。
    选中的那一行两档都正常（暗档 836 个亮墨）。⇒ 判别量是**选中与否**。
    **八种候选形状被十五臂复刻体全部否掉**（`sidebar_appearance_r29d.swift`）：
    绘制外观域 / orderFront 踢 / 嵌套 NSHostingView+NSSplitView / 运行时翻外观 /
    钉死嵌套视图外观 / 显式 `AnyShapeStyle(.primary)` / `Button{Label}+.plain` —— 全都画对。
    要做的：拿产品自己的 `SettingsView` 做二分 —— 先把侧栏单独摘出来拍一张（需要一个真小的接缝：
    把 `SettingsSidebarView` 从 `private` 放开到 `internal`，或给夹具一条「只搭侧栏」的入口），
    再逐层加回 `CompatibleSplitView` / `NavigationSplitView`。定位之前**不许改产品**（候选解药全被否掉时改就是猜）。
    在此之前这条盲区要能被数出来：`settings-*` 暗档帧的侧栏未选中文字**不能作为可读性证据**，
    任何新判据若要读那一列，必须先带上"读到的墨在期望侧"这条资格断言。

46. **肉眼复核这一条通道本身没有判据（R29d 犯的那条）**：
    目标要求"每轮都要做真实视觉审查（看渲染出来的画面）"，本轮我看了裁出来的暗档帧，
    报了"五个标签浅灰可读" —— 与文件里的像素相反（那一列最亮只比底亮 4）。
    眼睛读的是**布局应该长什么样**，不是文件里有什么；它和期望一致，而不是和像素一致。
    要做的：把"看帧"这一步接一条机器对账 —— 每轮肉眼结论必须同时给一个可数的读数
    （最亮/最暗像素、亮暗墨比例、bbox），两者矛盾时以像素为准并回看是不是尺取错了位。
    本轮之后 `AGENT_VISUAL_ITERATION.md` 的"真实视觉审查"一节按这条改写法执行（先量后看）。

**BACKLOG 45 已由 R30 回答（D-090 / U-53）**：机制量到了 —— 设置页侧栏列的 `NSHostingView`
生效外观是 `NSAppearanceNameVibrantDark`（内容区是 DarkAqua），`cacheDisplay` 不走 vibrancy 的
窗口服务器合成，于是拍到的是合成前像素。产品侧**无需改动**；
名单已改成由这条前提决定（两个方向都会红）。剩下的只有真机那两条（人工批次 37.1 / 37.2）。

**R31（边界，不是待办）**：`CGWindowListCreateImage` 在本机 SDK 已标 unavailable，
替代要录屏授权 + 真上屏 ⇒ **离屏测试进程里没有"走窗口服务器"的取图路径**。
所以 BACKLOG 40（「清空」红不红）与 BACKLOG 45（vibrant 侧栏）剩下的唯一取证通道是**真机截屏**
（人工批次 36.4 / 37.1 / 37.2）。以后有人提议"再搭一个捕获通道"，先引用
`.scratch/motion-audit-2/spike_r31_composite_capture.md`。

**BACKLOG 39 已由 R32 收口（U-54 / D-091）**：详情区左轴统一到 gutter（20pt），
可读列不再随窗口居中；实测五块 spread 从 35pt 降到 0.5pt（亮暗各一遍），
骨架承诺的那一列就是内容落地的那一列。判据 + 两条源码守卫 + 变异 M137–M140。
代价（宽窗口右侧留白变大）与退路（抬 ch 上限，而不是改回居中）都写在 D-091。

47. **菜单栏那个表面整体量不到（R33 提出、R34 改口径，U-56 收回 / D-093）**：
    R33 由看帧得到"产品的推荐理由被硬切成半字（墨到 x=319.5）"。R34 查清那不是产品：
    `MenuBarExtra` 没有 `.menuBarExtraStyle(.window)` ⇒ 默认 `.menu` ⇒ 内容被编译成**真 NSMenu**，
    而 `menubar-*` 帧拍的是离屏 `NSHostingView` 复刻。复刻里那一行在 320/400/520/720 四档宽度下
    **都顶到帧边界**（最右墨 320.0 / 398.0 / 518.0 / 718.5）⇒ 复刻根本没有右内边距，
    这句话描述的是复刻，不是产品。
    ⇒ 已登记 `menuSurfaceReplicaFixtures` + 资格判据（前提读源码、名单≡夹具、证据是顶边读数）：
    这批帧只可判颜色档，**不可判宽度 / 截断 / 对齐 / 命中区**。
    **剩下的开放项只有一个，而且要真机**（人工批次 39.1）：那个菜单实际多宽？
    长记录的理由是"…"收尾还是被切？两种答案对应两种处置 ——
    前者=什么都不用做（帧的锅），后者=给面板声明宽度并补一条"墨不许顶到帧边界"的判据。

48. **列表行行内 meta（复制时间）的档量不到（R35 / U-58 / D-094）**：那一列的生效外观是
    `NSAppearanceNameVibrantLight`（暗档 `…VibrantDark`）⇒ `cacheDisplay` 拍到的是 vibrancy
    **合成前**的像素，实测 `.primary` 行标题与 `.secondary` 的 meta 一样深（都是 (113,113,113)），
    而设置页内容列同样 `.primary` 的标签是 (38,38,38)。
    ⇒ 侧栏行内文字（标题 / 时间 / 来源）的**档与对比度**在离屏帧上不是产品的量。
    需要：一条合成后的取图通道（R31 已证离屏没有 ⇒ 要么真机截屏，要么 R19 那条 orderFront 路线），
    或者把这一列的判据搬到能画出来的表面上。
    同一条盲区还覆盖 R21 的 `sidebar-multi-select/批量操作按钮` 读数（已登记在
    `vibrantResolvedControlProbes`，不判产品）。

49. **CI 的帧捕获步骤是 report-only，红了不拦（R35 查口径查出来的，U-59）—— R36 已收口**：
    `.github/workflows/ci.yml` 里 `Offscreen frame capture` 那一步带 `continue-on-error: true`
    且命令尾巴 `|| true`。runner 上那 4 条红（run 38473962277，逐字日志已钉成
    `scripts/tests/fixtures/r36_runner_capture.log`）：
    ① 材质盲区名单"黑带消失了"（runner 上 `MATERIAL_BLIND_SPOTS 0 of 51`，本机是 9 —— 那两条
    名单是**机器相关**的，同一条守卫在一台机器上是另一台机器的假红）；
    ② 正对照帧 `sidebar-history` 底行读到 0% 墨 —— **这条的归因写错了**：
    不是"List 内容在 runner 上画不出来"（那一族在 runner 未绘制 0.0%，画得出来），
    而是那把尺量的本来就是"底行 vs 左上角那一个像素"的色差（U-60 / 本条 50）。
    ③④ 两张 `settings-privacy-excluded` 被"捕获失效"闸门锁住（这条是闸门正常工作：
    runner 上 settings 族 18 张**全部**未绘制 90.6–95.9%，本机是 20.8–78.8%）。
    ⇒ 收口方式就是当初写的那句"红必须有名字"：三条**机器可见前提**（`CaptureCapability`）
    把判不了的那一**条**登记成 `*_NOT_RUN`（带读数与原因），新增的硬门
    `Capture gate (unregistered reds must be zero)` 只问"还有没有没登记的红"，
    外加"一条用例都没跑到=红"与"判出绿的数量 < 15=红"（skip 不是通过）。
    **仍未验证的部分**：闸门在 runner 上第一次真跑会不会绿 —— 那要下一次 CI 的日志说话（见 50③）。

50. **`bottomInkFraction` 量的不是"底行有没有墨"，而是"底行与左上角那个像素差多少"（R36 看图看出来的，U-60）—— R37 已收口**：
    R22 写下 `contentMustFit`（"夹具不许裁自己的内容"）时，这把尺的参照点取的是**整帧的 (0,0) 那一个像素**，
    容差 12。R36 用 `.scratch/motion-audit-2/bottomedge_r36.swift` 把 51 张帧按两种参照各扫一遍：

    | 帧 | `ref=topLeft`（现在的实现） | `ref=rowMedian`（底行自己的底色） | 角点差 |
    |---|---|---|---|
    | sidebar favorites / history / multi-select / multi-select-min × 亮暗（8 张） | **100.0%** | **0.0%** | 30 / 45 |
    | detail 亮色 7 张 | **100.0%** | **0.0%** | 21 |
    | `sidebar-no-results` × 亮暗 | 0.0% | 0.0% | 0 ← 角点恰好同色，所以"没墨" |
    | `settings-privacy-light` | 0.1% | **6.7%** | 12 ← 反方向：漏报 |
    | `settings-privacy-dark` / `-recommendations-dark` | 72.8% / 72.8% | 27.2% / 42.4% | 27 |
    | `contentMustFit` 那 10 张 | 0.0% | 0.0% | 0 ← 它们的绿是真的 |

    触发点是**看图**：`sidebar-history-300x520-light` 的底 100pt 里黑药丸在上、下面是一整块空的浅灰
    （那块黑的真实区间是 pt 371..436.5 = 66pt 高，**下沿距帧底还有 83pt** ⇒ 它不可能是那 100% 的来源），
    而判据说那一行 100% 是墨 —— 两者不可能同时为真。侧栏亮色帧的角点落在搜索框里（白 255），
    底行是窗口灰（240），差 45 > 12 ⇒ 整行数成墨。
    ⇒ **后果**：那条正对照（`bottomEdgeInkCanary`）从写下那天起读的就是假 100%，
    所以 `contentMustFit` 十条判据十四轮里**没有一条有效的正对照**。

    下一轮（R37）要做：
    ① 参照改成**底行自身**（每通道中位色；不要用量化桶心 —— 桶心与真实像素可差 7×3=21 > 12，
       会把一行干净的底色读成 100% 墨，这是我第一版工具自己的假阳性，已改）；
    ② 造一张**真的会被裁**的对照帧（现有 51 张里没有一张底行真有墨 ⇒ 正对照不是"找到"而是"要做"），
       并让 `InkFloor.bottomEdgeInkAliveFraction` 那条绊线先红一次，确认它会红；
    ③ 修完重跑 `Capture gate`：runner 上 `settings-*` 那两处 6.7% / 42.4% 的真实底行墨
       会不会让 `contentMustFit` 新红 —— 那才是这批夹具第一次被这把尺真的判过；
    ④ 变异电池 M166 的语义会变（它现在钉的是"尺瞎了也算活着"，改对之后要重新选注入点）。

    **R37 收口记录**：①②③④ 全部做完 —— 参照点改成底行每通道中位数（三张合成图钉住：
    角点不同读 0 / 半行读 50 / **整行同色读 0，这是写下来的边界**）；
    正对照是**造**出来的 `row-clipped-control`（同一颗 `HistoryRowButton` + 58pt 外框 + `.clipped()`，
    实测 10.8% / 12.5%，线 5%）；`R36 那一版把"尺活着"做成机器前提`被撤掉 ——
    它现在无条件红，因为"这台机器上一帧都读不到墨"正是判据最该红的一次。
    改对之后又掉出**第二处**同族问题：尺读的是 raw rep 而不是落盘的 PNG（同一帧 3.4% vs 43.4%，
    方向还相反）⇒ 已改成读产物，并用 `content-min` 那块药丸帧当锁（M171）。
    新暴露的事实：`settings-recommendations`（42.4% / 19.9%）与 `settings-privacy`（27.2% / 6.7%）
    确实把最后一行切成半截 —— 滚动区的正常行为，不进 `contentMustFit`，但**从此可数**。

51. **push 之后没读到 CI 的逐步结论，就把"CI 绿"写进了账（R37 查出来的流程洞，U-61）**：
    R35 的两个 run（7d0a89b / 68027fc）都是 `failure`，红在 R35 新加的
    `testProbesDoNotSitOnVibrantColumns`（runner 上 settings 族整体没画出来，那棵树答"内容列压在
    vibrant 里"），而我在 R36 的账里写的是"收口提交在 runner 上绿"。
    ⇒ 规矩：**每次 push 之后必须 `gh api .../jobs/<id>` 读到逐步 conclusion**，
    并且"CI 绿"这句话只允许写**读过的那一次**。闸门（R36）能指名"哪一步红了"，
    但它不会替我去读 —— 一个没人读的硬门，和 report-only 只差一步。
    已同时把那条资格判据改成带机器前提（判据侧的洞补上了）。

52. **一台机器的读数不能当另一台机器的地板（R38 由闸门第一次真跑点出来，U-62）**：
    R37 写的两样东西都是**本机的量级**：`content-min 底行 ≥20%`（本机 43.4% / runner **9.3%**）
    与 `judged ≥ 20`（runner 上 20/40 恰好压线）。⇒ 规矩：
    ① 要钉"读的是哪个来源/哪个量"时，写成**恒等式或关系**（判据读数 == 从产物重算的读数），
       不要写成"至少读到 X%"；
    ② 地板要**从表推导**（可判对象必须全部判到 + 对象不许被清空），
       不要写一个"今天刚好过"的数字；
    ③ 任何新写的量级阈值，落库前先在**两台机器**上各打一次读数 ——
       现在这一步有地方自动做：闸门会把 runner 的那一次指名。
    已落地的：`BOTTOM_INK_IDENTITY`（104 张全对）、派生地板两条断言、变异 M175 / M176。
    **R38 已被 CI 追认**：run 38487277143 第 7 步 `CAPTURE_GATE_RESULT=ok 红=0`（闸门第一次真判）。



53. **`ReceiptLine` 声明了 `.contentFade`，但 `SettingsView` 全文 0 个 `withAnimation` ⇒ 空转的动效声明（R39 查出，U-63）· 已收口（R42 / D-101）**：
    `SettingsView.swift:973` 那行 `.transition(MotionCatalog.transition(for: .contentFade))`
    只在**周围有动画驱动**时才跑；而三处回执（`exportMessage` / `archiveMessage` / `exclusionReceipt`）
    全是裸 `@State` 赋值 ⇒ 今天它们**瞬间插入、瞬间消失**，声明等于零。
    对照：`DetailView` 的同类状态走的是 `withAnimation(MotionCatalog.animation(for: .emphasis))` ——
    成例在仓库里，只是这一页没做。
    为什么本轮不修：这条改动的效果**离屏帧量不到**（中间态不在任何一张帧里），
    而在屏胶片探针要真窗口 + 真点按钮（导出会弹 `NSSavePanel`），CI 上跑不了。
    R9 的先例是"撤掉空转的那条"，但那次撤的是**产品里没有对应体验**的声明；
    这一次体验是真的要变（回执插入的布局位移 R22 量过），所以处置应当是**供电**而不是撤。
    下一步：给三处 setter 加 `withAnimation(MotionCatalog.animation(for: .contentFade))`，
    并把"淡入到底跑没跑"交给胶片探针 + 人工批次（不许只凭源码有 `withAnimation` 就算交付）。
    **R42 收口，三处都改了形，且原账有三处不准（都记在这里）**：
    ① "三处全是裸赋值 ⇒ 瞬间插入"不准 —— 清空回执那一处（`:659`）**本来就有驱动**，
       而它根本不是 `ReceiptLine`；排除名单那一处有驱动，只是键缺了回执自己（名单没变的那两种情况推不动）。
       真正的死声明只有两处（导出反馈 `:555`、导出/导入历史 `:619`）。
    ② "全文 0 个 `withAnimation`"这句**数错了对象**：该问的是"这个调用点外面有没有一条 `.animation(value:)`"，
       而这条问句同时暴露了旧守卫的粒度问题（见 D-101：文件级守卫抓不到一个有 9 条键的文件里的死声明）。
    ③ 处置没按原案用 `withAnimation` 包 setter，而是给容器加 `.animation(value: <门控> == nil)` ——
       理由：仓库里唯一那条**已经能演**的回执（清空）用的就是这一族，跟着它才能让新判据读得到键。
       代价写进 BACKLOG 63：这条判据因此**只认一种写法**。
54. **`.disabled` 把标签淡到 1.82:1（亮档），低于本仓库给次要文字定的地板 2.2 —— 今天不可达，所以记账不修（R39，U-63）**：
    实测：`开机启动` 标签 启用 13.76 → 禁用 **1.82**（0.13 倍），暗档 11.43 → **2.29**（0.20 倍），
    而暗档禁用后的"算字像素"直接读到 **0**（`textInkMinDelta = 60` 那道门过不去，肉眼仍读得清）。
    今天这一支不可达：`SystemLoginItemManager.isSupported` 恒 `true`。
    所以本轮只把它**量出来并写进断言消息**：如果哪天 `isSupported` 真的会返回 false
    （比如给 macOS 12 加"没有自动化权限就判不支持"），**别用 `.disabled` 表达这个状态** ——
    让那句回执去说明，标签保持可读。
    同一轮还留下一条尺的读数：`TEXT_SIDE_BLIND_SPOTS` 现在是 **11 of 11** ——
    设置族每一张帧的暗档侧栏文字都结构上量不到（合成前的 vibrancy 极性，D-090）。
55. **守卫中止的那次启动在盘上什么都没留下 + 启动冒烟撞上它时报错原因（R39 换装时 A/B 实测，U-64）**：
    A/B（同一份包、同一台机器，唯一变量是"还有没有另一个同 bundle 实例在跑"）：
    有实例 ⇒ `SMOKE_OK=0 / 退出码 0`，日志里**既没有 `===== Lifecycle debug started =====`、
    也没有 `applicationDidFinishLaunching called`、也没有守卫自己那句"本次启动取消"**，
    只剩更晚的 `windowWillClose` / `applicationWillTerminate` 段；
    没实例 ⇒ `SMOKE_OK=1 / 退出码 -15`，header 与启动标记都在第 1、2 行。
    两半各修各的：
    ① **产品侧**：`AppDelegate.swift:100` 那句早退日志**落不到盘上**（为什么它连同它之前的行一起丢 —— 机制未定位，
       怀疑与 `LifecycleDebugLogger.reset()` 的 `sink.close()` + 紧接着的 `write()` 重开顺序有关）。
       这条属于"早退路径要留带内部状态的日志"那一族：用户双击图标没反应时，盘上必须有一行字解释为什么。
    ② **探针侧**：`scripts/launch_smoke.py` 在启动前应先 `InstanceGuard` 式地查一次冲突实例，
       查到了就报 **NOT-RUN**（"这台机器上已有实例，冒烟没有对象"），而不是把探针环境问题
       报成"启动失败"。判据本身（`evaluate`）也要能区分这两种。
    复现命令：`open -a /Applications/时间剪史.app` 之后
    `python3 scripts/launch_smoke.py /Applications/时间剪史.app --keep-logs`，再退出该实例跑同一条对照。
56. **新写一条"读像素"的判据，必须先回答"这一台画不出来时它说什么"（R39b 由 CI 点出来，U-65）**：
    R39 第一版的 `testDisabledToggleAndFailureReceiptAreVisible` 在本机全绿，推上去**第 5 步就恒红**
    （run 38494383404：runner 上设置页内容列是平涂 ⇒ 对比度 1.00、墨 0、差值 0）。
    这是同一族**第三次**（R35 资格判据恒红、R37 量级地板 9.3%、R39 这条），前两次都写进了规矩，
    第三次仍然犯 —— 说明规矩停在"事后修"，没停在"写之前问一句"。
    ⇒ 落库前的固定一问：**这条判据在"这一族画不出来"的那台机器上会输出什么？**
       答案必须是三选一且被测过：显式 NOT-RUN（带机器可见的标记）、或换成恒等式/关系、或它天然与机器无关。
       并且**那张"画不出来"的判定本身也要能被咬**（`settingsDrawability` 四格真值表 + M183 / M184），
       否则它是一张新免检牌。
57. **闸门报的 NOT_RUN 条数从 40 掉到 5，而本轮只可能让它变多（R39b 追认 CI 时发现，未解释）**：
    R38 那轮第 7 步 `CAPTURE_GATE_CASES … NOT_RUN=40`；R39b 这轮同一步 `NOT_RUN=5`。
    中间的两轮改动只会**新增**标记（两条新探针 × 两档外观 = 至多 4 条 `CAPTION_NOT_RUN`，
    加两档 `DISABLED_STATE_NOT_RUN`），不可能少 35 条。
    两种解释都还没证：① `ci_capture_gate.analyse` 数的是"含 `*_NOT_RUN` 的**行数**"，
       而这个"行数"在 R38 之后被某次改动换了来源（比如某条汇总行不再逐条打印）；
       ② runner 上有一批 NOT-RUN 打印路径这轮不再走到（例如被 `PROBE_DOMAIN` 的资格放行改成了静默跳过）。
    ⇒ 下一步先做**复现**：本机跑一次 `--filter UICaptureTests` 带 `CLIPBOARD_HISTORY_UI_SHOTS`，
       把闸门喂进去，看 5 是不是本机也报这个数；再对 R38 的那次日志逐条点名 40 条各来自谁。
       在复现之前，账本里这两个数字**不许**被当成同一把尺比较（U-62 的口径版）。
    **R46 又添两个数**（同一个计数器，两次 CI）：run 38514753036（R44）`NOT_RUN=8`、
    run 38519597818（R45）`NOT_RUN=24`，而两次的 `Executed 735/742 tests, with 36 skipped` 几乎一样。
    ⇒ 这条不再是「某两轮之间少 35 条」的孤例，而是**这个计数器每次都在动**：
    40 → 5 → 8 → 24。四个数、同一把尺，中间没有改过打印路径的轮次占多数。
    R46 的新闸门管的是动效那一族（它数的是**臂**，不是行数），管不到这里 —— 已明确记进 D-105。
    下一轮做这件事的方法不变：**先复现再解释**，本机跑一次带 `CLIPBOARD_HISTORY_UI_SHOTS` 的
    `--filter UICaptureTests` 把闸门喂进去，看本机报几；再对某一次 runner 日志逐条点名。
58. **复制失败的回执里嵌着系统错误原文，用户读不懂（R40 看帧看出，U-66）· 已收口（R41 / D-100）**：
    帧上那句是"复制到剪贴板失败：The operation couldn't be completed. (NSOSStatusErrorDomain error -100.)。
    已取消自动粘贴 —— 剪贴板里仍是原来的内容，没有被替换。"
    中英混排、没有下一步。仓库里**已有**成例：`SystemEventsPasteKey.reason(fromStderr:)`
    会把 `-1743` 映射成指向「系统设置 → 隐私与安全性 → 自动化」的人话，并有四条用例钉着。
    ⇒ 下一轮把同样的映射接到复制这条路上（`NSOSStatusErrorDomain` 的 -100 写失败 /
    剪贴板被别的过程持有 等），带真值表；同时判一遍"要不要保留原文"（原文对诊断有用，
    可以留给日志而不是界面）。
59. **保存失败仍然静默（R40 普查第 3 条，R41 已逐行复核 ⇒ 现象成立，本轮仍不修）**：
    复核结论（R41，读行号 + grep，不是回忆）：`HistoryStore.persist()`（:1066-1071）与
    `FileHistoryPersistence.makeSaveWorkItem`（:465-479）两处 catch **都只写 `LifecycleDebugLogger`**；
    `lastSaveError|saveFailure|didFailToSave|onSaveFailure` 在这两个文件里 **0 命中**；
    `HistoryStore` 现有 6 条 `@Published` 回执通道（`historyRecoveryNotice` / `pasteFailureNotice` /
    `clipboardWriteFailure` / `droppedFilesNotice` / `transferNotice` / `retentionNotice`）
    **没有一条是"存盘失败"**。
    ⇒ 与 D-099 那次不同：**没有现成通道可复用**，要先决定形状
    （一次性横幅 vs "只读模式"那种常驻标记 + 首次提示），再动。可达失败种类仍需实测确认
    （磁盘满 / 目录权限 / 图片编码失败），不许拿推断当缺陷修。
60. **静默失败普查里其余 12 条全部标着「未核」（R40，`.scratch/motion-audit-2/silent-failures-survey.md`）**：
    只读模式之后每次写盘被跳过、点已裁掉的推荐什么都没发生、菜单栏"清空未收藏"没有回执（设置页同动作有）、
    导出失败与"导出 N 条"两条横幅互相矛盾、热图账本损坏时显示"还没有可统计的记录"（文案是假的）、
    上下文权限开关显示"已开启"而实际未授权、`LoginItemSettings.refresh()` 那半边的 error 不读、
    权重/反馈/快捷键 encode 失败静默、拖出 plist 序列化失败、浮层 contentView 为 nil、
    以及一条不可达的死代码（`refreshHistory` 没有任何入口）。
    ⇒ 规矩：**未核的条目不许直接当缺陷修**（R34 的 U-56 就是拿没复核的推断去改，方向改错）。
    每轮挑 1–2 条先复核再动，复核结论写回这份清单。
61. **【已修，R61】程序化选中一条视口外的行 ⇒ 列表里连高亮都没有，而详情区仍在讲它（R41 量到，U-67 的副产物）**：
    现象读数（同一份数据、同一处选中行）：`content-min`（600×440 无横幅）`blackBandPt=43 / bottomInk=43.4%`
    ⇒ 选中行压在帧底、被裁一半；`content-min-with-copy-failure-notice`（600×440 + 一条 50pt 横幅）
    `blackBandPt=0 / bottomInk=0.1%` ⇒ 横幅把列表顶下去 50pt，那一行**整行**出了可视区。
    两张帧里详情区显示的都是同一条记录（"ghp_AAA…"）。⇒ 界面在讲一条用户看不见的记录。

    **R61 把这条从头到尾量了一遍，并且先证伪了本条目上一版的两句判断**（用户逐字对台账，所以更正写在正文里）：
    * 上一版（eeb16d0）说"启动选中第一条，新记录从顶部插入 ⇒ 被选中的那行会一行一行往下漂出视口"。**错。**
      `HistoryStore.add` 末尾调 `reconcileSelection(preferredEntryID: 新条目.id)` ⇒ 选中项每次都被**换成新记录**，
      它不漂。真正的问题是新记录的**落点**：`EntryOrdering.promotionIndex` = 开头那段固定项的长度。
    * 上一版给的修法（`ScrollViewReader.scrollTo(id)`，"macOS 12 就有"）**在产品侧不成立**：
      真的写进侧栏跑过，带 anchor、不带 anchor 各一次 —— 临时插桩 `GLUE_DEBUG` 证明胶水执行了、
      id 也解析到了，表格一步没滚（`selectedRow` 仍 -1、`documentVisibleRect` 仍在 y=0）。
      同一份形状在孤立 spike 里 0.25s 就从第 1 行滚到第 60 行；六臂 bisect
      （focusEffectDisabled / onDrop+overlay+animation / VStack 在 reader 内 / Button 行 /
      产品形状的行 / reader 在 if/else 分支里）全绿，找不到是哪一件按死的。⇒ 那三行已回滚，
      并由 `SelectedRowRevealTests.testSidebarDoesNotClaimTheSwiftUIScrollRoute` 钉住"不许没重测就写回来"。

    **可达性（R61 实测，不需要任何点击）**：夹具里固定 4 条 + 视口只装 2.6 行 ⇒
    `INTAKE_READING 新记录落点=4 在屏=false store 选中它=true 表格选中集合=[]`
    ⇒ 一次普通复制就把选中送到视口外，而表格的选中集合是**空**的（两条轴都量了：
    `selectedRow` 是主选中行、`selectedRowIndexes` 才是集合 —— 只用前者是本轮第三次读错轴）。
    默认窗口尺寸下门槛是"固定 ≥ 视口行数"（约 9 条），最小窗口下约 3 条。

    **修法（R61 落地）**：`SelectedRowRevealer` —— 一个只调 `NSTableView.scrollRowToVisible` 的宿主视图，
    挂在侧栏 `List` 的 `.background` 上。三条边界写死在代码里：
    ① **只滚不选**（选中集的唯一作者仍是 `List(selection:)`，D-1 修法③；守卫 `testRevealerOnlyScrollsAndNeverSelects`
       见到 `selectRowIndexes` 就打红）；② **已经在视口里就不动**（臂 1 后半句：否则用户点一行列表自己跳，
       那是 R22 那一族的自伤）；③ **选中变了才滚、行号漂了不滚**（闸门按选中项 id 判：
       删掉顶部一条无关记录会让选中项行号 60→59，id 与选中都没变，视口就不许动 ——
       这一格由 `testRowIndexDriftDoesNotMoveTheViewport` 单独钉，M313 把闸门换成按行号判只在那里红）。
    另外"推迟一个回合再滚"是实测逼出来的：同步滚会让**上一行的取消选中丢失**，
    读到 `selectedRowIndexes=[2, 60]` 而 store 只有 1 条 ⇒ 列表亮两行、详情讲一条，是新分裂。
    为什么"只滚"就够：同一轮臂 3 量到"把行滚进视口，SwiftUI 自己就把选中补上"（3/3 稳定，`[]` → `[60]`）。

    判据：`SelectedRowRevealTests`（`rowIndex` 真值表 4 格 + 两条源码守卫）+
    `UIInteractionProbeTests.testOffScreenProgrammaticSelectionIsRevealedAndNotJumped`（四臂）+
    `testIntakeBehindATallPinnedBlockRevealsTheNewRow`（采集路径，从 `store.add` 进）。
    帧基线 `FRAME_BASELINE_CHANGED=0`（116 张全等）⇒ **离屏通道结构上看不到这次改动**：
    静态帧里选中永远在第一行，揭示器正确地什么都不做。视觉复核改用探针取证的两张
    `reveal-before/after-320x300-light.png`（after：列表滚到新记录、那一行带填充；
    填充的**颜色**在这一通道里解析成黑块，属 R29/R30 那族材质盲区，只作位置取证、不作配色判据）。
    变异对照 M311–M316 见 `.scratch/motion-audit-2/r61_mutation_battery.log`。

62. **「导出反馈数据」同一件事有两条通道，而失败那条又是系统英文原文（R42 复核 BACKLOG 53 时看到）· 已收口（R43 / D-102）**：
    `SettingsView:172-179` 三个分支都写 `exportMessage` **并且** `showExportAlert = true`
    ⇒ 用户既看到模态弹窗、又看到行内 `ReceiptLine`，两条说的是同一句话（模态还会抢注意力）。
    而失败那一支是 `exportMessage = "导出失败：\(error.localizedDescription)"`
    ⇒ **U-67 同一族、另一个出口**：R41 只把"写剪贴板"那条路做了人话，这条路还在直出原文。
    ⇒ 处置要先定一件事：这一族回执**留行内还是留模态**（仓库里其余三处都是行内）。
    定了再动，不许两条都留着各改各的；原文按 D-100 的规矩进日志。
    注意 BACKLOG 60 里"导出失败与'导出 N 条'两条横幅互相矛盾"是**同一片代码**，一并判。
    **R43 收口记录**：判完发现不是一处而是**三处**（导出反馈 / 导出存档 / 导入存档都在拼
    `localizedDescription`），措辞集中进 `Utilities/ReceiptWordings.swift`，模态那条删掉，
    原文一律进日志；同时补了一条**夹具不许手写回执文案**的按族判据 ——
    `receipt-line` 那张帧从 R14 起画的产品根本没说过（全仓 grep 无此文案），
    换成真文案后 `contentMustFit` 又当场红出第二件事：那张帧一直在裁自己（56 → 72pt）。
    与 BACKLOG 60 那条"两条横幅互相矛盾"是同一片代码，那条仍开放（它问的是横幅之间，不是模态）。
63. **R42 那条新判据只认一种驱动写法（`.animation(value:)`），用 `withAnimation` 供电会被误报成没电**：
    判据读的是"门控状态名有没有出现在某条 `.animation` 的键里"，而 SwiftUI 里推动过渡的还有
    `withAnimation { state = … }` 那一族（`DetailView`、`GlassControls`、`DailyCopyHeatmapView` 都在用）。
    ⇒ 现在这是一条**约定**而不是事实。约定已写在 `ReceiptLine` 定义处的注释里（加调用点的人一定会看到组件名）。
    下一轮二选一：① 把 `withAnimation` 那一族也解析进来（要处理大括号配对，成本不低）；
    ② 把约定做成会红的判据（"回执门控不许用 `withAnimation` 供电"）。
    **不许再留成口头规矩**（BACKLOG 60 那一族"规矩停在事后修"的老毛病）。
64. **R42 那把"调用点级"的尺，现在只量了 `ReceiptLine` 一个组件（粒度修对了，覆盖面还没铺开）**：
    仓库里"声明了 `.transition` 却可能没人供电"的形状不止它一个 —— 文件级守卫
    （`testNoUnexecutedTransitionClaimsAcrossViews`）在**有驱动的文件**里一律看不见调用点级的死声明，
    这正是 R42 在 `SettingsView.swift`（9 条键）里抓到三处的机制。
    下一轮把同一把尺按组件参数化跑过剩下几个候选：`NoticeBanner`（`ContentView` 里五条并排，
    插入位移 R22 量过，但"每条的键是谁"没按调用点判过）、`EmptyStateView`、
    热图那两条 `contentFade` 分支（`DailyCopyHeatmapView:44/50/78`，同文件另有 `.animation` 键 ⇒ 同一族隐身条件）。
    做法已经现成：`receiptGateConditions` + `receiptGateIsDriven` 换个组件名与门控形状就能复用。
    **R43 复核把这条从"待推广"改成"推广之前要先解决一个真问题"**：`ContentView` 那五条 `NoticeBanner`
    的驱动是**一条派生键** —— `:32` 的 `.animation(bannerIn, value: noticeSignature)`，
    而 `noticeSignature`（`:36-44`）是一个把五条回执的存在性压成 bitmask 的计算属性。
    ⇒ 按名字匹配的判据会把这五条**全部误报成没电**（键里出现的名字是 `noticeSignature`，不是那五个状态）。
    推广的第一步因此不是换组件名，而是**让判据会把派生键展开成它读的那几个状态**
    （读那个计算属性的 body，把里面点到的状态名并进门控集合）。
    好消息是这五条**确实有电**（R22 用像素量过插入位移），所以这不是漏网的缺陷，只是尺的表达能力。
    **R44 做掉了一半**：派生键展开已进判据（`drivingStates`，只增不减、读不懂不放行也不报错），
    `NoticeBanner` 那五个调用点已进名单 —— 读数`BANNER_DRIVE 调用点 5 个、键 1 条、展开后状态 13 个、无驱动 0 个`。
    **剩下一半**：热图那两处（`DailyCopyHeatmapView:44/50/78`）不是"组件调用点 + `if let` 门控"，
    而是 `if 布尔 { 一块视图 } else { 另一块 }` 的**分支**形状 ⇒ 扫描器要先会认分支；`EmptyStateView` 同理还没进名单。
    所以这条**仍然开着**，别因为"NoticeBanner 做完了"就划掉。
65. **`ReceiptLine` 的 × 顶对齐，而横幅的「知道了」垂直居中（R43 看帧判过，刻意不动）**：
    R25 / D-084 把**横幅**（`StateLine`）的动作位改成垂直居中，理由是"两三行正文时按钮压在上三分之一，
    读起来像这个动作只管第一句"。`ReceiptLine` 是 `HStack(alignment: .firstTextBaseline)` ⇒
    × 跟着第一行。本轮**没统一**，因为两族的动作语义不同：
    「知道了」是**对整条消息的确认**，× 是**收起这一条**（贴着它要收起的那句话的首行更像"这个 × 管这条"）。
    需要人来判的一问：两行回执时，那个 × 让你觉得它只管第一行吗？（人工批次 45 里没问，
    因为本轮帧刚换文案 —— 下一轮若做 BACKLOG 64 的推广，顺手把这一问带进批次。）

66. **动效覆盖地板在 runner 上从 4/4 掉到 3/4，而那一关还是绿的**（R45 读 CI 时看到）**—— R46 已收口**：判据搬进 `scripts/motion_floor_gate.py` + 登记表 `scripts/motion_floor_expectations.json`，八条规则各配一支变异（M216–M222）。剩下的是**下一台机器**的问题：这张表说的是 runner 的前提，不是本机的。
    run 38514753036（R44）报 `MOTION_RESOLVE_SUMMARY judged=3/4 not-run=notice-banner-dismiss`、
    `MOTION_SUMMARY … notice-banner-dismiss=2`，而 R42/R42b/R43 三次都是 `4/4 not-run=-`。
    同一批代码、同一台 runner、没有产品改动 ⇒ 这是**采样漂移**（BACKLOG 57 那一族），
    不是产品回归。真正的问题是形状：地板现在判的是"这些判据跑没跑"，
    所以"某一臂这次没采满"**不会让它红** —— 掉了一臂这件事没人报，我也只能靠人肉对比 run 日志发现。
    下一轮要做的不是把地板抬到 4/4（那会让它恒红），而是给它一个会红的形状：
    例如"同一臂连续两次 run not-run ⇒ 红"，或者把 not-run 的**名字**登记进已知清单、
    清单外的名字出现两次就红。判据依赖的环境前提要写进判据本身。
67. **悬停的"触发"那一半仍然只能人眼验**（R45 记账，不是 R45 的缺陷）：
    `HeatmapHoverEvidenceTests` 量的是**表达**（给定 `isHovered` 画出来看不看得见），
    而"鼠标真的划过去会不会出现那一圈"依赖 `.onHover` 被回调 —— 三条合成通道 R14 实测全断。
    现在这一半挂在人工批次 22 与 47.1 上。若哪天要做机器通道，先重读
    `.scratch/motion-audit-2/spike_hover_channel.md` 再动手，别把三条死路再走一遍。
68. **热图淡入那条 A/B 用错了轴：它判"看得见"用的是帧数，而帧数会随采样相位漂**（R46 跑真日志时撞出来的）：
    `MotionFilmstripTests.testHeatmapFadeIsNotVisibleToThisRuler` 的放行条件是
    `onSpan == offSpan && |peak(on) - peak(off)| < 0.02`。本机真跑一遍的读数是
    `开 帧数=2 峰值=0.226 / 关 帧数=1 峰值=0.226` —— **两臂峰值完全相同**，只有帧数不同，
    于是它走进 `XCTFail("两臂读数不同 ⇒ 这把尺现在看得见这条淡入")` 那一支。
    而"帧数会漂"正是 R2 已经证伪过的事（同一份代码本机跑过 2/3/2，
    原始记录写在 `changedRunElapsedMilliseconds` 开头）。
    ⇒ 这条判据在拿一个自己宣布过不可靠的量做判据，红的是尺，不是产品。
    下一轮（R47）：A/B 换成**时长轴**（两臂 `changedRunElapsedMilliseconds` 之差），
    峰值差作第二证据；并把"只漂帧数不许算看得见"写成一条真值表 + 一支变异。
    **R47 已照这一条做完**，而且比原计划多做了一件：本机反复抓到 258–307ms 的变化段
    （声明只有 160ms）⇒ 只设下限会被它骗，于是加了**上限**（声明 + 2×间隔）。
    那段变化到底是什么，见下面第 69 条。
69. **那条 A/B 反复抓到的 258–307ms 变化段到底是什么**（R47 实测；**R48 已解释**，见第 70、73 条）：
    热图"空态↔日历"那条过渡声明 160ms，而本机 isolated 连跑反复抓到
    `258 / 259 / 260 / 265 / 307ms` 的"画面还在变"段，**一次进程只出现一次**、
    出现在第几遍抓取上不固定。它不是这条淡入（比声明长出 60–90%），
    R47 因此给判据加了上限把它挡掉。但"挡掉"不等于"知道是什么"：
    候选是①首次布局/字体度量、②账本去抖落盘引发的二次刷新、③`DailyCopyLedger` 的临时文件写。
    **为什么值得查**：如果是 ②/③，那就是**采集路径上有同步磁盘写** —— 目标里明令禁止的东西，
    性质从"测量噪声"变成"产品缺陷"。
    **R48 更新**：那段不是"过程演了 266ms"，是**一段连续变化里有一次 260ms 的抓帧空档**
    （段内最粗采样 260ms，整卷中位 8ms）。"采集路径上有同步磁盘写"这个最坏解释
    **没有被这条读数否证** —— 恰恰相反，它现在有了一个可量的读数（`worstIntervalMilliseconds`），
    于是问题从"这段读数是什么"升级成"那一刻是谁占住主线程"，另开第 73 条接着查。
    怎么证：给这条通道加一条对照臂 —— 把 `DailyCopyLedger` 的去抖写盘堵住（或换成内存账本）再抓一遍，
    看那段长变化是否消失；消失即坐实落盘，不消失再往布局那侧查。**不许猜着修。**

70. **【R48 已收口，U-74 / D-107】**`changedRunElapsedMilliseconds` 量的不是「一段」，是「首尾」（R47 看图 + 读码）：
    它的取法是 `moving = fractions.indices.filter { $0 >= peak * stepFloorRatio }` 然后取
    `moving.first` 到 `moving.last` —— **不要求连续**。于是「触发后 7ms 内变完，静止 250ms，
    又有一帧因为别的原因变了」会被读成一段 258ms 的「画面还在变」。
    这正好是 BACKLOG 69 那串 258–307ms 读数的一个候选解释，而且解释的是**尺**不是产品。
    怎么证（不许猜着修）：先给这条通道打一行 per-frame 序列（帧号 + 相对时刻 + 变化量），
    抓到一次长读数时看它是不是**两波带空隙**；是 ⇒ 把函数改成「取包含峰值的那一段连续 run」，
    并补真值表（单波 / 两波带空隙 / 峰值在第二波）+ 变异。
    **R48 的实际收口与原计划不同，且把本轮自己的假设也否掉了**：
    ① 改名 + 新建连续段那把尺确实做了（真值表 8 格 + 变异 M230–M234）；
    ② 但"两波被并成一段"这个解释**错了** —— 补上 per-run 打印之后真形状是
    `开A [345–612@0.226/粗260] 帧数=2 整卷中位=8ms`：**一段连续的**变化，
    段内有一次 **260ms 的抓帧空档**。所以那条长读数既不是"过程演那么久"，也不是"两波被并"，
    而是**钟在过程中间停了** —— 缺的是分辨率轴，不是连续性。两把尺都补上了（D-107），
    而"是谁卡的"另开第 73 条（性质比第 69 条硬，因为它发生在用户刚按下 ⌘C 的那一刻）。
    **注意代价**：这个函数不止那条 A/B 在用（R2 起多处判据用它当时间读数），
    语义一改，别的判据的读数会一起变 ⇒ 必须逐条复核，不许只改不核。
71. **热图梯子的相邻档从来没有一条判据**（R47 看图看出）：`VisualHeat.ladder = [0.18, 0.34, 0.56, 0.85]`
    加 `empty = 0.055` 一共五个台阶，R45 量的是「悬停那一圈相对于整条数据范围响不响」，
    **没有量过「第 1 档与空格子能不能分开」**。本轮看暗色帧：图例最左那一格几乎与背景同色。
    如果 1 次/天 与 0 次/天 在暗档下肉眼分不开，这张图就在把「没数据」和「有一点数据」抹成同一个意思 ——
    这是数据可读性缺陷，不是审美问题。
    怎么判：拿 R45 已有的渲染夹具（`renderCell(level:hovered:appearance:scale:)`）扩一条判据，
    要求**相邻两档**的均值差 ≥ 恰可察觉台阶（沿用 `perceptibleBand255 = 18` 那把尺，
    但地板要从实测推导，不许照抄），亮/暗两档、1×/2× 两尺度各跑一遍。
    如果暗档第 1 级过不了 ⇒ 改 `empty` 或改梯子（**改数值必须同时改这条判据的期望**，
    并且帧基线要 `update`，因为格子颜色会变）。
    **R51 的预览实测**（`.scratch/motion-audit-2/heat_ladder_preview.py`，对
    `heatmap-cell-strip-still-90x140-{dark,light}.png`，Rec.709 亮度、`perceptibleBand255 = 18`；
    **格子按"像素数指纹"配对，不按亮度排序** —— 第一版按亮度排序，把灰色的 `empty`（`primary`）
    与蓝色的第 1 档（`accent`）排成了两套次序，见下面那条更正）：

    | 相邻台阶 | 暗档 Δ | 亮档 Δ |
    |---|---|---|
    | 背景 → 空格子 | +11 | −12 |
    | 空 → 第 1 档 | **+4** | −13 |
    | 第 1 → 第 2 档 | +13 | −23 |
    | 第 2 → 第 3 档 | +17 | −32 |
    | 第 3 → 第 4 档 | +21 | −42 |

    ⇒ **暗档"0 次 vs 1 次"只差 4/255**，是本仓库恰可察觉线（18）的四分之一；亮档那一格是 13，也没过线。
    暗档第 1→2 档（13）同样在线下。R47 那句看图结论现在有了数，而且**比先记的更糟**
    （先记的是"暗档最低两级 15 / 13"，那是归位错的表）。
    R52 当时该做的（R54 已做，见下面那条结案）：把这条变成 `renderCell` 上的判据（相邻档 Δ ≥ 从实测推导的地板），
    并决定是抬 `empty` 还是抬梯子第 1 级 —— 改数值要同时改判据期望并 `frame_baseline.py update`。
    **一个先验约束**：`empty` 用 `primary`、四档用 `accent`，所以"空→第 1 档"这一步跨了两个色族；
    抬 `empty` 会让 126 个空格子一起变响（不喧宾夺主那条），抬第 1 档则会把第 1→2 档压回去 ——
    这两条互相牵着，R52 要把它们一起判，不许只调一个数就宣布修好。
    **【R54 已结案，U-80 / D-113】答案是"梯子没错，尺的轴错了"**：
    判据 `testAdjacentHeatLevelsAreSeparableOnTheRightAxis` 已立（4 对 × 2 外观 × 2 尺度 = 16 条读数），
    距离取**逐像素最大通道差**，地板沿用 `perceptibleBand255 = 18`。
    实测最小一条是 `dark empty→bucket1 = 30.00`（同一对在亮度轴上只有 2.16）⇒ **16 条全过，
    产品数值一个没改，帧基线不需要 update**。
    上面那条"抬 `empty` 还是抬第 1 级"的选择题因此不成立：那是按亮度轴做的决定，
    真按它改会把一张没病的图改响。变异 M264（把梯子第 1 级压到 0.06）与 M265（把轴换回均值）都会红。
    **R52 把这条的度量轴更正了（上面那张表的结论作废）**：`perceptibleBand255 = 18` 是**亮度**尺，
    而 `empty` 用 `primary`（灰）、四档用 `accent`（蓝），"空 → 第 1 档"主要是**色相**翻转。
    同一份像素按通道取最大差：暗档那一步是 **30**（B 通道 41→71）、亮档是 28（R 通道 243→215），
    都在 18 之上 —— 所以"0 次与 1 次分不开"这个结论**不成立**，是我用错轴造出来的
    （本仓库记过这一族：只用亮度判两态可否分辨 = 用错轴）。
    R53 的判据因此改成：① 距离必须取**通道最大差或 ΔE**，不许只用 Rec.709 亮度；
    ② 先跑判据再决定改不改数值 —— 现在的数据倾向于"梯子不用动"；
    ③ 人工批次 53.1 的那一眼是这条的**主判据**，我的尺退到"别用错轴"的位置。

72. **其余调用点还站在"跨度"那把尺上**（R48 / D-107 留下的口子）：
    `worstIntervalInsideChangedRun` 与那条通用场景判据（`MotionFilmstripTests` 里 `judgeScenario`
    一路）仍然用首尾跨度。本轮没迁移，理由是它们喂的 R2 夹具
    `coarseSampling = [0.11, 0.001, 0.10, 0, 0, 0]` **本身是两波带空隙**的形状，
    而"真机上一次 135ms 的淡入会不会被采成这个形状"从没对过账。
    连续段那把尺会把它读成两段（45ms + 45ms），跨度那把尺读成一段 135ms ——
    同一个数据，两把尺差 3 倍，而这条判据今天还在用后者。
    怎么判（不许两种读法都留着不写理由）：拿真胶片（`empty-state` / `detail-kind-change` 各一卷）
    数一遍"段内掉回地板以下"出现过没有；从没出现 ⇒ 那个夹具是虚构的，按连续段重写并改掉 R2 那句话；
    出现过 ⇒ 采样真的会漏，跨度才是对的，那连续段只该用于"两波之间有明显空隙"的场合。
    **R51 已经把这道题答了一半**：`.scratch/motion-audit-2/answer_backlog_72.py` 对每一卷同时算两把尺，
    并且把本文件的实现与日志里 Swift 自己打的 `变化段时长` / `事件内最粗` **逐场景对账**
    （`RULER_AGREEMENT=ok` 才允许下结论 —— 第一版因为正则分组下标数错，把 182ms 读成 3ms，
    这道对账就是它自己的解药，属"计数命令本身没证伪"那一族）。
    本机 2026-10-14 那一次 `CLIPBOARD_HISTORY_UI_MOTION=1` 出 3 卷真胶片
    （`notice-banner-dismiss` 182ms / `detail-kind-change` 177ms / `empty-state` 144ms，
    原文存在 `.scratch/motion-audit-2/r51-motion-films.log`）：
    **段数全是 1、段内低谷全是 0** ⇒ 那个夹具的形状在真胶片里没出现过。
    **还欠 runner 那几卷**：runner 的采样比本机粗 3–7 倍（本机整卷中位 20–50ms，runner 事件内 55–62ms），
    那才是"掉回地板以下"最可能出现的地方。两批都是 0 才动迁移 —— 否则 72 的答案是反的（R53 的活）。
73. **【R49 已收口，U-75 / D-108】**触发之后那次 260ms 的抓帧空档 —— 是谁占住了这段时间（R48 新读数，当时性质比 BACKLOG 69 更硬）：
    `heat-first-record` 的 `段内最粗采样 = 260ms`（整卷中位 8ms）说明抓帧器在触发后那一段挤不进去。
    候选：①首次布局 26 周 × 7 天 = 182 个格子的 SwiftUI 布局；②`DailyCopyLedger.record` 主线程侧的工作；
    ③去抖落盘（它在 `saveQueue` 上，但发布 `@Published` 会回主线程）。
    **为什么值得查**：这条发生在**用户刚按下 ⌘C 的那一刻**，而目标里明令"采集路径上不许有同步磁盘写"。
    如果这 260ms 是我们自己的代码占住主线程，那是可感知的卡顿，不是探针噪声。
    怎么量：`worstIntervalMilliseconds` 已经是现成的读数 —— 拿同一条通道跑一次"设置窗口没打开"的对照
    （只有 `HistoryStore.add`，没有热图视图），如果停顿消失 ⇒ 是视图布局；不消失 ⇒ 往采集/落盘那侧查。
    **不许猜着修。**\n    **R49 的答案**：不是产品的采集链。产品侧 `HistoryStore.add` 实测 40 个样本中位 0.56–0.63ms、最差 3.08ms，且复制之后盘上不多一个文件（`CapturePathWriteBudgetTests`，两条判据；M240 拿产品代码做过变异，确实会红）。那 260ms 落在**探针自己**对新生子树的首帧 `cacheDisplay` —— 同一份文件里 R11 早就记着『新窗口的头两次 cacheDisplay 要 260–340ms 一帧』，量级与位置都对得上。剩下的产品侧问题（淡入第一帧到底贵不贵）另开第 74 条，因为现在这个读数混着冷缓存，不能直接当产品数用。
74. **淡入第一帧在真机上值多少毫秒**（R49 归因之后剩下的产品侧问题）：
    R48 读到 `开臂 段内最粗 260ms / 关臂 6ms`，R49 证明产品的 `HistoryStore.add` 只有 0.6ms 中位、
    且盘上不多文件 ⇒ 那 260ms 不是采集链。但它也不是干净的读数：
    它混着探针自己"新窗口头两次 `cacheDisplay` 要 260–340ms"的冷缓存（R11 原文）。
    现在能确定的只有一件事：**开臂有、关臂没有** ⇒ 这段成本与"带着过渡的新子树"绑定。
    怎么量成产品数：同一份内容、**同一个已经渲染过一次热图的窗口**里再触发一次淡入
    （第二次不再有冷缓存），读段内最粗采样；再与"关掉曲线"的同一形状对比。
    两个数还差很多 ⇒ 淡入本身的第一帧成本是真的，值得优化（比如首帧只画可见列）；
    差不多 ⇒ 那 260ms 全是探针的账，BACKLOG 73 就此结案。
    **另有一条只能靠人**：人工批次 50.2 问的是"复制那一下你有没有感觉到 0.1–0.3 秒停顿"。

75. **runner 第一次跑完 `testNativeRowMoveIsVisibleToTheRuler`，它红了**（R48 的 CI，run 38536051202）：
    ```
    MOTION_NATIVE row-insert 开 帧数=4 峰值=0.052 采样≈28ms / 关 帧数=1 峰值=0.061 采样≈18ms
    MOTION_NATIVE row-move   开 帧数=1 峰值=0.047 采样≈28ms / 关 帧数=1 峰值=0.047 采样≈15ms
    ```
    这条判据以前每次都是 `MOTION_NOT_RUN=app-not-active`（非激活进程里 NSTableView 不跑行动画），
    所以它**从来没有在 runner 上出过结论**。这一次出了，而且是红。
    为什么这次不能直接归给探针：**同一卷里 `row-insert` 看得见**（开 4 帧、关 1 帧）
    ⇒ 那台机器、那个进程、那次采样是**能看见行动画的**，只有"移动"这一条两臂完全相同。
    产品语义上这条最该动：复制一条已有记录会把它**移到列表顶部**，
    如果它是瞬移，用户看到的是"这一条消失了、另一条冒出来"，而不是"它跑到上面去了"。
    怎么查（不许猜着修，也不许先改判据）：
    ① 本机复现 —— 想办法让探针进程真的激活（`NSApp.activate` 之后 `NSApp.isActive` 必须为 true，
       这条判据现在就是靠它 skip 的），拿到与 runner 同一形状的第二份读数；
    ② 读产品代码：那条移动走的是 `List` 的数据重排还是 `withAnimation`？
       如果重排发生在 `HistoryStore` 里而外面没有动画事务，那"看不见"就是**产品没做**；
    ③ 若 ② 成立 ⇒ 补一段 `withAnimation(.rowReorder)` 并让这条判据从"看不见=红"
       变成"看不见=红且能看见=绿"的正常形状；若 ② 不成立（有事务仍看不见）
       ⇒ 那是 `List` 在 macOS 12 上不做行移动动画，要写进"这一维的上限"，别再空转。
    **这一步的判别力关键**：`row-insert` 在同一卷里是好的，所以"探针不行"这个解释已经被否掉一半。
75. **（R50 推进，仍未结案）**runner 第一次跑完 `testNativeRowMoveIsVisibleToTheRuler` 就报红：
    `row-insert 开 4 帧/关 1 帧` 与 `row-move 开 1 帧/峰值 0.047 = 关 1 帧/峰值 0.047` 出自同一次运行。
    R50 做了两件事：① 删掉探针在 move 臂里对六行文案的 rename（那是产品没做的动作，
    留着就不能把结论算在产品头上）；② 结论分三态，"峰值都是 1 帧但形状不同"从此叫
    `native-move-sampling-missed`，不再冒充"瞬移"。
    **还欠的**：修完探针之后的 runner 第二次样本。三种可能各自怎么走 ——
    a) `判定=动了` ⇒ 上一轮那次红是探针 rename 造成的，BACKLOG 75 结案，不写进任何产品缺陷；
    b) `判定=瞬移` ⇒ 产品侧缺陷成立（`moveRow` 的隐式动画在 macOS 12 这条路上不产生可见中间帧），
       下一轮去查 `NSAnimationContext` 的 duration 与 `runAnimationGroup` 的同步语义，
       并考虑像侧栏那样退回"整表刷新 + 淡入"这种确定看得见的表达；
    c) `判定=采样错过` ⇒ 这台机器今天量不了，继续挂着，**不许改成常绿**。
    人工批次 52.1 同时问用户的眼睛（快速选择浮层里候选重排那一下有没有滑）。
    **R53 推进（打印顺序）**：`MOTION_NATIVE_MOVE 判定=` 以前打在 `requireAppWasActive` **之后**，
    所以 runner 每次跳过这一臂就只剩两臂读数、没有结论（38543090198 / 38543812477 两次都是这个形状）。
    现在结论行挪到闸门之前、`XCTFail` 留在闸门之后，并加了一条顺序守卫（变异 M260–M263 全 CAUGHT）。
    **这条判据仍然只有 runner 能验收**：本机每次 `app-not-active` ⇒ skip。
    a/b/c 三种读法各自怎么走不变（见上面 R50 那段）。
76. **主线程那条链没有分段读数**（R51 / M253 实测开）：480 条的库里一次复制 `median≈2.4ms`，
    而把整库快照 `saveSnapshot` 跑两遍只涨 0.5ms ⇒ **快照只占约 1/5**，剩下 1.9ms 不知道在哪
    （候选：`ClipboardEntryIntelligenceAdapter` 的整库摘要、去重索引、降采样规划、`@Published` 引发的视图 diff）。
    现在这条判据只能说"总共多少"，不能说"哪一段在长"。
    为什么现在不修：目标里那句硬要求是"**不许有同步磁盘写**"，那一条已经由行为判据钉住（M249 会红）；
    这 1.9ms 里没有写盘，是纯计算，且 2.4ms 远在可感知线（≈100ms）之下。
    什么时候必须修：`CAPTURE_PATH_FULL_ARCHIVE` 的 median 涨到接近门槛（20ms）的一半时 ——
    那时"先分段再决定搬什么"就不再是可选，因为盲搬会把两成的问题当全部（本轮我自己就先写错了这句话）。
    怎么量：在 `HistoryStore.add` 的四个段各打一次 `DispatchTime`，用一条真判据（从产品入口）断言
    "任一段的 median ≤ 总 median 的 60%"，超了就把那一段的名字打出来。
77. **横幅那一族的动效覆盖，两台机器今天都量不到**（R52 开，来自 `MOTION_FLOOR_THIN`）：
    `notice-banner` 声明 150ms、`notice-banner-dismiss` 声明 120ms，
    而"事件段内最粗的一次采样"实测 runner 73–76ms、本机 96–101ms —— 全部粗过 0.5×声明这条分辨率线，
    于是这两臂只能报 `clock-coarse-in-window`（本机 `notice-banner` 甚至是 `premise-not-visible`）。
    R46 的登记表当时把它们写成"必须判到"，R52 按实测放行并打 THIN；**放行不是修好**。
    根因是抓帧器自己：一帧 `cacheDisplay` 在事件段内要 70–100ms（BACKLOG 74 那条的同一件事），
    而 150ms 的过渡只有 2–3 帧可拍。三条候选路（R54 之前先想清楚再动）：
    a) **降每帧成本**：把 `Grabber` 的位图尺寸按 1× 拍（现在按 backingScale 拍 2×，像素数是 4 倍）；
    b) **给判据一个慢动作夹具**：一个 `declared=600ms` 的"故意慢版"横幅，专供量"有没有过程"，
       产品仍按 150ms 走 —— 这不算为过夹具改产品，因为改的是**测试里的注入参数**；
    c) **承认这一族交给人眼**：把它写进人工批次并从覆盖地板里除名（最诚实也最弱，要先有人批准）。
    判"该走哪条"的证据：本机与 runner 各一卷 `MOTION notice-banner*` 的 `时刻ms=[…]` 全列。
    **R54 补的账**：同一条 runner 六次运行 `4/4（R48）/ 2/4（R49）/ 无读数（R51a）/ 3/4（R51b）/ 4/4（R51 更正）/ 4/4（R52）` ⇒ 这是**漂移**而不是坏了；登记放宽与 `MOTION_FLOOR_THIN` 都据此站得住。
    **R55 补的账（归因落地，路 a 被选出来）**：`Grabber` 现在逐帧记 `cacheDisplay` 的毫秒数，
    粗钟 not-run 行带上 `归因=…（解释=NN%…）`。本机三遍：主窗口那几卷抓帧中位 38.7–49.7ms，
    而**整卷中位间隔** 43–44ms（事件段内最粗 95–97ms）⇒ **一个采样间隔≈一次抓帧 + 一次等待**。新判据量出成本随面积**子线性**走
    （端到端 12.3–13.0 倍 vs 面积 29.8 倍，地板 ≈3ms）⇒ **路 a（按 1× 拍）是主杠杆**，
    1× 预计把 41.7ms 打到 ≈11ms（**推算，未实测**：R56 落地时必须自带 before/after 两张实测）。
    路 c（交给人眼）现在没有证据支持。另开一条更靠前的：见 U-82 / BACKLOG 79 ——
    **读数通道自己会整次消失**，归因挂在这条通道上，通道丢一次这一轮的判读也丢。
    **R57 结案（路 a 落地，但走的是"缩区域"而不是"降倍率"）**：`Scenario.captureRect` +
    `Grabber(rect:)` 把横幅两臂的捕获从整窗（1520×1346px）收到顶部一条带（1520×96px，面积 1/14），
    仍然按 2× 拍。本机三次连续跑（同一份代码，`.scratch/motion-audit-2/r57_motion_readings.log`）：
    抓一帧的中位成本 39.5–39.8ms → **4.4–4.6ms（≈9 倍）**，整卷中位间隔 44–45ms → **9–10ms**，
    同一场景 A/B 的过渡帧数 3–4 → **10–11**，`MOTION_RESOLVE_SUMMARY judged=4/4 not-run=-`
    （这一族以前在本机是 2/4）。比 R55 那条"按 1× 拍 ⇒ ≈11ms"的推算更好，
    而且**没有牺牲分辨率** —— 那条推算今天被实测超过了，记录留在这儿不删。
    登记表跟着改回严格：两臂 `must_judge=true`、`thin_warnings` 清空（放行理由已被修掉，
    留着它等于把修好的洞留给下一次）。
    **仍未闭合的一半**：runner 侧还没有一次带捕获的读数。若 CI 红在 `UNDERCOVERED`，
    那是闸门在说真话（R55 那次 `NO_RESOLVE` 是同一族），不是这一改坏了 ——
    下一步是把 runner 的读数抄进登记表，或走路 b（慢动作夹具）。
78. **run 38543090198：动效那一族整次没打任何读数，原因至今未证实**（R52 开）：
    `Executed 28 tests`、`胶片: 9`、`motion suite exit: 0`，而 `MOTION_SUMMARY` 与
    `MOTION_RESOLVE_SUMMARY` 一行都没有，`---- 动效读数 ----` 段是空的。
    原始 `motion.log` 没上传，所以**我不能说它是为什么**（R42 那一族：读到 0 要先证三件事）。
    候选：① 场景判据 `testTransitionsAreActuallyRunning` 被 `XCTSkipUnless` skip 掉
    （env 没进到测试进程？它的 skip 原因不带 `MOTION_NOT_RUN=`，所以那一步的 grep 看不见）；
    ② 记录到一半窗口没开成 ⇒ `frames.count <= 4` 走了 `XCTFail`+continue？不，那会打红；
    ③ 打印被 XCTest 吞掉（本机全量跑里也观察到过 stdout 丢失，见 R51 那次
    `CAPTURE_PATH` 在全量日志里一行都没有）。
    R52 已经把这一格变成**有名字的红**（`MOTION_FLOOR_SKIPS` 会把 skip 原因逐条打出来），
    结案条件：下一次 runner 运行里读那一行 —— 它要么直接给出原因，要么证明"连 skip 都没有"，
    那时 ③ 就是唯一剩下的解释，要单独查打印通道。
    **R56 补的关键一块**：这条通道**加固过了**（读数同时进 `motion-readings.log`，CI 取并集），
    所以"CI 上有没有读数"从此不再取决于 stdout。加固后第一遍本机就抓到
    stdout 只剩 2 行而文件有 56 行 ⇒ 当初那次"整次没读数"如果重演，
    地板拿到的仍是完整读数，`NO_RESOLVE` 那一支只在**两条通道都空**时才红。
    机制仍未证实（见 BACKLOG 79 的结案条件）。

79. **动效读数会整次消失：本机 1/3 复现，原因未证实**（R55 开 / U-82）：
    同一条命令（`CLIPBOARD_HISTORY_UI_MOTION=1 swift test --filter MotionFilmstripTests`）
    在本机相隔 12 分钟跑三遍，两遍有全部 `MOTION_*` 行，
    第三遍（`.scratch/motion-audit-2/r55_motion_stdout_lost.log`）**一行都没有**，
    而 stderr 侧一切正常：`Executed 32 tests, with 4 tests skipped and 0 failures`、
    每条 `Test Case … passed` 都在，胶片也写出来了。
    ⇒ 丢的只是测试进程 `print` 到 stdout 的那一段。
    这与 BACKLOG 78 是同一件事，但**这次不用靠 CI 的一次孤例**：本机可复现、与运行次序无关。
    为什么现在不修：还不知道机制（SwiftPM 转发子进程 stdout？stdio 缓冲与退出路径？），
    而**猜出来的修法会把一条判据建在流沙上**。
    什么时候必须修：R56 —— 而且它比"缩捕获"更靠前，因为本轮的归因、覆盖率地板、
    `MOTION_SUMMARY` 的键集合全都住在这条通道里；通道丢一次，那些判据就一起变成"今天没跑"。
    怎么修（候选，按代价排）：① 判据把每一行读数**同时**写进 `outDir` 里的一个 `.log`
    （"胶片写出来了"与"读数留下了"变成同一件事，代价最小、可被现有 `MOTION_FLOOR_NO_RESOLVE` 直接验证）；
    ② 查 SwiftPM 的 stdout 转发并在 CI 里改用 `--xctestlist`/直接跑 `.xctest`；
    ③ 给覆盖率地板加一条"stdout 空但 suite 跑完 ⇒ 红"（**已经有了**：`NO_RESOLVE`，
    所以这一格今天在 CI 上是会红的 —— 也就是说这条通道的故障**已被记账**，只是没被解释）。
    **R56 已加固（机制仍未证实）**：44 处 `MOTION_*` 读数全部改走 `emit`
    （stdout + `<outDir>/motion-readings.log`，第一次整份重写、之后追加），
    CI 的 `Motion filmstrip` 那一步把两条通道**取并集**并打
    `MOTION_CHANNEL_UNIONED=1 stdout=N 文件=M`。
    兑现得比预期快：加固后第一遍本机就出现 **stdout 2 行 / 文件 56 行**
    （活下来的正是 `MOTION_SUMMARY` 与结论行，死掉的是 54 行理由与逐卷读数）。
    守卫 `testMotionReadingsUseTheFileChannel`（含正对照）+ 变异 M277–M285 九支全 CAUGHT。
    **结案条件改窄成"查机制"**：现在能说的是"丢的是子进程 stdout，stderr 与 FileManager 写盘不丢，
    且可部分发生（三次：0 / 全 / 2 行）"；还没能说的是为什么。
    下一次再看到 `stdout=N 文件=M` 且 N≠M，就把两边的行做集合差，看丢的是不是**同一个前缀段**
    —— 那能区分"缓冲没刷"与"两个写者抢同一个 fd"。

80. **`changedFraction(band:)` 的归一化带是上下颠倒的：用过 `band:` 的旧结论要重算**（R57 开，实测）：
    那个函数把带矩形按 `yStart=(1-maxY)*h, yEnd=(1-minY)*h` 映射进缓冲区，注释写着
    "缓冲区第 0 行是画面的底边"。R57 实测这两件事对不上：
    带那一臂的第 0–95 行与整窗那一帧的第 0–95 行**逐像素相同**（差 0.000），
    而与整窗的第 1250–1345 行差 0.954 ⇒ 缓冲区第 0 行就是**画面顶边**，
    于是 `band.minY=0` 取到的其实是窗口的**底部**一条。
    直接证据：同一场景、同一次运行，带上的首尾差 0.885，而该函数算出来的"顶部带"只有 0.071。
    受影响的调用点（`MotionFilmstripTests` 里 7 处 `band:` 矩形，逐个算镜像区间，不是一句"都可能错"）：
    `CGRect(x:0.05,y:0.02,w:0.90,h:0.20) // 横幅那一条` 量的是 y∈[0.78,0.98] 那条 ⇒ **整条跑偏**；
    `侧栏第 4 行的星标列 y∈[0.26,0.38]` 量的是 y∈[0.62,0.74] 那一行 ⇒ **整条跑偏**；
    `表格区 y∈[0.10,0.88]` 量的是 y∈[0.12,0.90] ⇒ 上下各偏 0.02（小，但不是零）；
    `详情区 y∈[0.12,0.88]` 与 `列表中部 y∈[0.35,0.65]` 因为**关于中线对称**而恰好没跑偏；
    还有 R2 那台分带归因的网格（`row/cols` 那个）行序整个是反的 ⇒ 当时"哪一行在动"的读法要重看。
    为什么本轮不修：修它会让上面每一条判据的地板全部重算（它们是在"量错的地方"上调出来的数），
    而 R57 的活儿是带捕获。本轮的做法是**绕开**：新的位置判据直接逐行比两份缓冲区，
    不经过那个映射（见 `bandHeadTailDiff`）。
    结案条件：单独一轮，把映射改对 ⇒ 逐条重跑那 7 个调用点 ⇒ 每条地板重新由实测决定 ⇒
    账本里写明"哪几条旧结论被推翻"。**这一条在"动效判据的可信度"上排在 77 之前**。
    **R58 结案（三层都做了，第三层是意外）**：
    ① 先给方向写真值表（`testBandRectMapsToTheEndItClaims`，合成位图上/下/左三处差异 × 六格 +
    夹具自检）。它在坏的映射上先红四格，横轴与整幅那两格全绿 ⇒ **红的形状本身就是诊断**。
    ② 映射改对（一行：`yStart = minY*h`），变异 M295/M296/M297 三支分别把 y 倒回去、把 x 也倒回去、
    让带永远不生效，全部 CAUGHT。
    ③ 逐个重算 7 个调用点：`详情区 y 0.12–0.88` 与 `列表中部 y 0.35–0.65` **关于中线对称**
    ⇒ 五轮以来一直是对的（也因此从来没有能力发现这个 bug）；`表格区` 上下各偏 0.02（可忽略）；
    实质跑偏的是两条 —— `// 横幅那一条`（y 0.02–0.22 → 实际 0.78–0.98）与
    `侧栏第 4 行的星标列`（→ y 0.62–0.74）。后者的读数从 0.221 变 0.260（同一判据、同一台机器）。
    **意外的那一层**：`// 横幅那一条` 那个调用点从 R57 起传的已经是**带捕获那一卷**，
    所以它真正的病不是镜像而是**嵌套** —— 三个数并排：镜像错 帧 11/≈121ms、
    嵌套错 帧 6/≈66ms、修完 帧 15/≈165ms，**三个都没让任何判据变红**
    （上限 2×声明+一个采样间隔 = 311ms）。⇒ 新守卫
    `testNoTestFramesABandInsideABandCapturedFilm`（带捕获那一卷上不许再传非 nil `band:`，
    谓词是"场景变量→胶片变量→传 band 的调用点"那一点点数据流；它第一版**假红**，
    被 `testListRowsDoNotAnimate…` 顶回来），M298/M300 两支 CAUGHT。
    还剩一条没钉住的记成 BACKLOG 84（网格行序）。

81. **带的高度（48pt）没有"必须盖住横幅"的判据**（R57 开）：
    `bannerBand` 取顶部 48pt，实测横幅那条是 38pt + 分隔线 2px ⇒ 现在装得下，余 10pt。
    但文案变两行、或动作按钮换成长文案，横幅就会**溢出带外**，
    而带外那部分仍然在演 —— 于是"带上的过渡帧数"会安静地少掉，不会红。
    今天拦得住它的是 `bandMustHoldChangeFraction=0.02`（实测 0.885，要掉到 1/40 才红，余量太大）。
    候选修法：① 带高从**帧里量出来**（找那条浅底带的下边界）而不是写常数；
    ② 给"横幅高度"单独一条判据（它本来就该在排版那一族里）；
    ③ 把地板从 0.02 提到实测的某个分数 —— 但那是拿一次读数当锁，R38 那一族反对过。

82. **离屏帧里横幅的半透明底合成到透明 backing 上：按帧量横幅对比度量的不是产品**（R57 开，看图）：
    `/tmp/r57e-motion/diag-full-first.png`（暗色模式那一卷）里横幅那条是**浅粉底 + 白字**，
    而同一帧其余部分是 `27,27,27` 的暗底。原因：底调是 `Color.orange.opacity(0.12)`，
    离屏 `cacheDisplay` 没有窗口背景可合成 ⇒ 平铺到 PNG 的白底上，
    而文字是 `.primary`（暗色=白）不透明。
    ⇒ 任何"从横幅那一条帧里读墨与底"的对比度尺，在暗色模式下会量到 白字/浅粉底 ≈ 1.x:1，
    那是**捕获通道的产物**，不是产品缺陷；反过来它也可能把真缺陷洗成"环境如此"。
    R24 那条 `testNoticeBodyTextStaysReadable` 今天没被这件事骗到（它跑的是亮色夹具），
    但这条边界没写进任何判据。结案条件：要么在判据里显式声明"横幅底不许从离屏帧取"，
    要么给夹具补一层不透明窗口背景（那是 BACKLOG 39 那一条捕获通道边界的续）。

83. **CI 的动效读数摘录用的是硬编码前缀白名单 ⇒ 每一轮新增的读数族在 CI 上看不见**（R58 开并修，R59 结案 / U-85）：
    `.github/workflows/ci.yml` 那一步打的是
    `grep -E "MOTION_(SUMMARY|RESOLVE_SUMMARY|NATIVE|SHIMMER|SEQUENCE|CONTROL|CUT|DETAIL|AB|BLANK|SETTLE|SYMBOL)"`。
    后果是实测出来的：想在 run 38570965657（R57）的日志里回答"runner 上带捕获到底成没成功"，
    而 `MOTION_BAND` 一行都没有 —— R55 加的 `MOTION_GRAB` / `MOTION_GRAB_AREA` 也不在列表里，
    所以那两步的读数从来没进过 CI 日志。那一步只剩 `judged=4/4`，
    而**带捕获之前的 R56 也是 4/4** ⇒ 两个形状在日志里分不开。
    **R58 已修**：改成先报 `MOTION_LINES=$(grep -cE '^MOTION_' …)` 再 `grep '^MOTION_' | head -120`，
    并给自检加一格 `family_not_in_any_list`（喂一行没有任何白名单提过的 `MOTION_BAND`，
    要求它出现在输出里）。M299 把白名单放回去 ⇒ 那一格立刻红。
    为什么这条值得单独立账：白名单不是一次性错误，是**每一轮都会重新失效**的形状 ——
    加一条新读数的时候，没有人会想起来去改另一份文件里的列表。
    **R59 结案**（run 38576482491，摘录存在 `.scratch/motion-audit-2/ci_r58/motion_step_runner.md`）：
    那一步的日志里 `MOTION_LINES=122`，`MOTION_GRAB` 与 `MOTION_BAND` **同时读到了**，
    并且据此判了一次"带捕获在 runner 上成没成"：**成了，但它买到的是时间不是分辨率** ——
    带=抓帧中位 5.6ms / 间隔中位 22ms / 760x48px，整窗=14.1ms / 22ms / 760x588px，
    两臂的 `过渡帧数` 都是 3。本机那对 44→9ms 的采样增益在 runner 上不存在（那边时钟就是 22ms 一跳）。
    ⇒ 登记表里 R57 那句"runner 侧还没有一次带捕获的读数"已按这个更正（`motion_floor_expectations.json`）。

84. **分带归因网格的行序没有判据**（R58 开 / R60 结案）：`changeGrid` 把窗口切成 cols×rows 打印"哪一格在动"，
    R58 之前它的**行序是反的**（第 0 行打印的是窗口底部）。现在对了，但没有任何判据钉住它 ——
    它只输出字符串，不参与任何断言。
    已核对的一半：历史上用它得出的结论里，M1 那条"斜坡全部来自右侧详情区"是按**列**读的 ⇒ 不受影响。
    没核对的一半：任何按**行**读过的网格输出（R2/R3 的诊断段）都要重看一遍才能引用。
    **R60 结案**：`changeGrid` 拆成"位图版 + 薄壳"（`changeGrid(bitmaps:…)`），
    新判据 `testChangeGridPrintsRowZeroAtTheTop` 用合成位图把差异分别放在顶边 / 底边 / 左边，
    要求第 0 行整行亮、其余行全暗，底边与左列同理。M308 把行序翻回去 ⇒ 三格同时红
    （`.scratch/motion-audit-2/r60_mutation_battery.log`）。
    顺带把 R58 那条测试里的合成分位图闭包提成共用的 `syntheticPair`
    —— 各自一份就会有一份跟着实现变旧；M309 把夹具的 `&&` 改成 `||` ⇒ 两条测试都该红。
    没核对的那一半（R2/R3 按行读过的诊断段）仍然没重读，但**从本轮起它再读也不会被行序骗**。


85. **看图看见的"横幅被横切半截"是真的，但我给它配的两个"证据数"本轮都被自己证伪了**（R59 开 / U-86、U-87）：
    R59 第一次把带捕获那一卷按**原始像素**堆成逐帧图（`testBannerFrameStacksAreReadableEvidence`），
    于是看见了以前看不见的东西 —— 第 4~5 帧（约 45–55ms）里：
    ① 侧栏那一侧（x<280pt）：搜索框的圆角矩形已经上移到横幅那一行，并且**画在还没淡完的横幅文字之上**
      —— 字的下半是被它**盖住**的，不是被裁掉的（这一点本轮重看逐帧图才分清）；
    ② 详情区那一侧（x>280pt）同一行文字的尾巴"无法自动粘贴。"与那颗"知道了"还留在原来的高度上淡，
      而列表内容已经从它下面滚上来；横幅那层粉底**整幅都还在**，是被内容盖在上面。
    `ContentView.swift:8` 里 `notices` 是 splitView **之上的整幅一行**，一条整幅视图不该有两个 y。
    **这条留着，是本轮唯一还能站住的看图结论**，但它原来带的两个数都被推翻了：
    ①~~两栏以不同进度消失~~ —— 那是 `transitionFrameCount` 的门槛取**各自峰值**的 15%：
      侧栏峰值 0.305 ⇒ 线 0.046，详情区 0.237 ⇒ 线 0.036，两条线不一样，
      比出来的"谁先停"就是**墨量差**。换成同一条绝对线（`sharedMovingFloor`）之后，
      本机五遍两栏**"最后一个还在变的帧号"完全相同**（16/16、17/17、17/17、17/17、16/16，
      `r59_motion_readings.log` 第 3.1 节）
      ⇒ "侧栏先落定 2–5 帧"作废，措辞改由 `columnSettlementVerdict` 从帧号生成
      （合成真值表 `testSharedFloorColumnComparisonIsATruthTable` 钉住四种形状，M306/M307 有牙）。
    ②~~图标质心上移 6.5pt ⇒ 横幅在被抬走~~ —— 那是**判色阈值在动**：图标淡到线以下时
      还活着的只剩一部分，质心必然朝那半边漂。补了外框这条轴（`MOTION_TRACK_BOX`，只看
      像素数 ≥ 首帧一半的强帧）之后：外框 **4/5 遍一格没挪**（首末都是 [29,50]），
      强帧质心跨度 2.6 / 0 / 0 / 0 / 0px ⇒ 那个"上移"没有这回事。
      但也不许反过来写死"绝对没动"：第 1 遍下沿上移 4px，正落在"淡出时高饱和边缘先脱落"的量级里，
      而 ±2px 的容差分不开"边缘脱落"与"一边被裁"（要分开得换一条**不吃饱和度**的轴）。
      R22 当年"它是淡出，不是塌陷"这句在**淡出**这一半被证实（它只有一帧可看，结论对了但没证据）。
    ⇒ 剩下的问题从"两条时间线"缩小成一条**层叠顺序**问题：撤走的那 120ms 里，
    横幅还在画（整幅粉底 + 文字 + 按钮都在淡），而**底下的内容已经重新排好并盖了上来**。
    两种解释这台机器仍然分不开：① 产品真的让布局立刻塌陷、只把 `.opacity` 留给横幅
    （那就是"淡出中的文字与搜索框重叠 50ms"，是真缺陷，且修法明确：先淡后塌）；
    ② 离屏 `cacheDisplay` 把"布局提交"和"淡出层"画在不同进度上（BACKLOG 82 那条通道的续，
    那就不是产品的事）。本轮**不写地板**，也不写"这是缺陷"。
    **本轮不写地板**（把"我看着不对"写成判据就是背书）。结案条件：批次 59.1 有人看真屏幕，
    问句改成二选一 ——「撤走那一下，横幅是**整条一起淡**，还是**侧栏那半截的字被横切**」。
    若答"被横切" ⇒ 修法候选：移除改成"先淡后塌"（`.opacity` 配延迟的高度收拢），
    或给横幅一个固定高度的容器让内容不被切；两者都要带新的逐帧判据。


86. **动效那一步的红在 CI 上等于没跑：`continue-on-error` 把 exit 1 吞了，日志里连红的理由都没有**（R59 开 / U-87，证据 `.scratch/motion-audit-2/ci_r58/motion_step_runner.md`）：
    那份摘录里有名有姓的一行是
    `MotionFilmstripTests testTransitionsAreActuallyRunning]' failed (7.443 seconds).`
    同一步还打出 `motion suite exit: 1`、`executed: 37`、`MOTION_LINES=122`，
    而**整个 run 的结论是 success**（38576482491 与 38576483610 两个都是）。
    两半毛病：
    ① **红的理由读不到** —— 那一步只 `grep` 了测试名字，没有 `XCTAssert` 原文，
       所以"哪条判据、因为什么"要重新在本地复现才知道。
       **R59 已修这半边**：新增 `grep -E "error: -\[" /tmp/motion.log | head -12`，
       自检 `red_test_prints_its_reason` 要求日志里能读到 `一帧跳变` 那句原文；
       M305 把这句摘掉 ⇒ 自检立刻红。
    ② **红不影响结论** —— `continue-on-error: true`（ci.yml:165）是 R36 之前留下的，
       当时的理由是"runner 是无屏环境，抓帧可能拿不到帧"。这个理由现在**已经被证伪了一半**：
       同一次运行里 `judged=4/4`、带捕获读数齐全（`MOTION_BAND … 帧=760x48px`），
       说明这条通道在 runner 上确实出帧。但"红"这一次是 `testTransitionsAreActuallyRunning`，
       它是**采样类**判据，runner 上红一次很可能是环境而不是产品。
       所以本轮不直接把它改成有闸 —— 改成有闸需要一次"红的确实是产品"的样本，
       否则就是拿 CI 结论换我自己的猜测当判据（R47 那次帧数地板的教训）。
    结案条件：连续两次 runner 运行都在这一步给出**可解释的读数**（`MOTION_BAND` 的
    `间隔中位` 与 `过渡帧数` 都在，且没有测试红），然后把 `continue-on-error` 换成
    真的 `exit "$status"`（那一步已经写好了 `exit 0` / `exit "$status"` 的分叉），
    并给"环境拿不到帧"留一条**具名**的 not-run，而不是整步吞掉。


87. **"0 告警"这条 CI 闸门只管 `Sources/`，测试目标里的告警从来没人看**（R59 开 / R60 结案 / U-88）：
    `.github/workflows/ci.yml:29` 那一步跑的是 `swift build`（不带 `--build-tests`），
    而 R58 提交的 `testBandRectMapsToTheEndItClaims` 里有一条
    `warning: variable 'a' was never mutated` —— 它在 `swift test` 的编译输出里明明白白，
    在 CI 里从来没出现过，所以 R58 那两次 run 都是绿的。
    这不是"测试代码不重要"的问题，是**判据的覆盖面被它的命令拼写悄悄定了**：
    台账与 AGENTS.md 写的都是"构建 0 告警"，读的人会以为整个包 0 告警。
    **本轮已经收紧**（没留到下轮）：先量了一次真正的清洁基线 ——
    `swift build --build-tests --scratch-path /tmp/r59-cleanbuild`（全新目录、构建期间不碰任何文件）
    ⇒ **exit 0、`warning:` 行数 0**。（第一次试的时候我在构建中途改了测试文件，构建以
    `input file was modified during the build` 失败，那次计数不可信 —— 本轮第二次撞上
    "别拿没跑完的数当结论"。）于是那一步的命令改成 `swift build --build-tests`，
    并且**红了要能读**：多打一行 `grep 'warning:' /tmp/build.log | head -12`（与 BACKLOG 86 同一课）。
    新守卫 `test_build_step_gates_the_test_target_too` 不是查字符串就完事：它把 ci.yml 里那段
    真脚本抽出来跑两遍（假日志 0 告警 ⇒ 必须绿；1 告警 ⇒ 必须红，且输出里能读到是哪一条）。
    剩下的最后一格：runner 上的 Swift 6.1.2 比本机严（历史上出现过），它会不会在测试目标里
    报出本机没有的告警 —— 下一次 CI 见分晓。**若真报了，修告警，不许把闸门放宽成"N 以下"。**


88. **R59 留下的那条"淡出中的横幅被搜索框盖住"，三条不依赖颜色的轴都没能量出来**（R60 开 / U-89）：
    它是 R59 证伪掉两个数之后**唯一还站着的看图结论**（`f5-left-3x.png`，3 倍放大能看见
    字的下半被那片圆角填充盖住、红图标的尖还在它上面）。所以本轮想把它变成一条判据，
    试了三条轴，全部失败，失败原因各不相同：
    ① **中灰像素数 ≥60**（`probe.swift`）—— 淡到一半的横幅白字正好落进中灰亮度带，
       第 5 帧在 rows 30–47 报了 82，那不是框，是正在消失的字。
    ② **最长均匀段 ≥60**（`probe2.swift`）—— 每帧第 0–3 行都是 200：横幅那片**平底本身就是均匀的**。
    ③ **水平直边（相邻两行亮度差 ≥12 的最长连续 x 段 ≥120）**（`probe3.swift`）——
       只在第 0–1 帧检出 rows 78/80 那条边（横幅底部分隔线），第 2 帧起**整卷再没有任何一条
       ≥120px 的边**，于是"框的上边"根本没被检出（框的边是软渐变，不是硬线）。
    三条都写进了 `.scratch/motion-audit-2/r60_evidence/`，连同 3 倍放大的两帧裁剪图。
    **本轮的结论是方法级的**：在这条 96px 的带卷上，"两个东西重叠"这件事**没有一条阈值能钉住**，
    因为重叠双方都在动（一个在淡、一个在位移），任何按亮度/颜色/边界的判据都会被其中一方污染。
    下一步不是再试第四条阈值，而是**换捕获方式**（R61 的靶）：
    同一场景跑两臂 —— 一臂 `MotionCatalog.animationsEnabled = false`（只剩布局移动、没有淡），
    一臂开着 —— 用**同一帧号**上两臂之差把"淡出的贡献"减掉，剩下的就是纯几何。
    这正是仓库里那条老规矩（"整窗像素会把动效归因给错的元素 ⇒ 要框区域 + 关掉效果的 A/B"）
    第一次用到横幅带上。结案条件：那条 A/B 能给出"横幅还在的帧里，搜索框的上边 y < 横幅文字的下边 y"
    或者给出反证；两种结果都算结案，因为那时要么能写判据、要么能撤掉这个观察。


89. **runner 上那条"提示条只演了 57ms ⇒ 一帧跳变"的红，是判据缺一条"跨度自己够不够被分辨"的前提**（R60 开 / U-90）：
    run 38586812301（R59 的 CI，整作业 success 因为那一步 `continue-on-error`）里现在能读到原文了 ——
    这正是 R59 那条 grep 换来的东西：
    `notice-banner：画面只变了 57ms 就停了，而声明的过渡是 150ms（事件内最粗采样 38ms）⇒ 这是一帧跳变，不是过渡`。
    同一个数在 runner 上已经红了两次（R58 的 38576482491 只留了名字、这次留了原文），本机同一把尺是绿的。
    为什么这条红**不能算产品的**：它量到的"变化段"是 57ms，而它自己报出来的"事件内最粗一次采样"是 38ms
    ⇒ **57 < 2×38**，也就是说整段"变化"连两次采样都不到。两次都不到的时候，
    "演了一帧就停"和"演了很久但我只抓到一帧"这两种形状给出同一个读数 —— 这把尺在这一格没有分辨率。
    现有的 `clockTooCoarse` 门槛是"最粗间隔 ≥ 0.3×声明时长"（38 < 45 ⇒ 放行到判定），
    它管的是**间隔 vs 声明**，没管**测到的跨度 vs 间隔本身**；缺的正是后者。
    候选修法（R61）：给 `judgeMotion` 加一格 `.spanUnresolved` ——
    `elapsed < 2 × worstInterval` ⇒ 既不判红也不判绿，报 not-run。
    它是机器无关的（两个数都来自同一卷），不像"本机 2x / runner 1x"那种常数。
    **为什么本轮没顺手改**：这条 not-run 一旦发出去，覆盖率闸门会看见 `notice-banner` 出现在
    `MOTION_NOT_RUN` 里，而登记表对它是 `must_judge=true` ⇒ 会翻成 UNDERCOVERED 红
    （R46/R52 那一族的正相反方向）。改之前必须先拿一份夹具把"judged 与 not-run 同时出现时闸门怎么判"
    钉下来 —— 那是 `scripts/tests/test_motion_floor_gate.py` 里现在没有的一格。
    结案条件：那一格夹具 + `.spanUnresolved` + 登记表跟着改，且 runner 与本机都不出假红。

90. **把视口滚回顶部之后，表格的选中集里会多留一行（`selectedRowIndexes=[0, 60]` 而 store 只有 1 条）——R61 顺手量到，本轮不修**（新开 / U-91）：
    读数（`UIInteractionProbeTests.testOffScreenProgrammaticSelectionIsRevealedAndNotJumped` 臂 3，
    同一行还打了 `store 里条数=1`）：程序化选中第 60 行、揭示生效之后，手工把视口滚回顶部，
    表格的选中集变成 `[0, 60]` —— 第 0 行被**并进**了选中集，而 store 仍然只有那一条。
    ⇒ 用户看到的是「列表亮两行、详情讲一条」。
    **我最初从这条读数推出过一句更重的话**（"批量动作会作用在用户没选过的记录上"），
    它被同一行读数否掉了：分裂只在表格这一侧，`applyListSelection` 没有被这次变化调用，
    store 侧的收藏/固定/删除仍按那一条走。写在这里是为了下次别再从读数多走一步。
    本轮**不判红**：把它写成断言会让整个套件红，而红要留给 61 本身；
    它现在是探针里一条显式登记的观察（注释里指名 BACKLOG 90）。
    与 61 的关系：61 是"选中了却看不见"，这条是"看见了却多亮一行" —— 同一个作者问题
    （`List(selection:)` 在行的物化/回收上会自己动选中集）的两半，修法要一起想。

91. **【已结案，R62：原判据成立，是我第二版电池自己坏了】`SelectedRowRevealer` 的闸门"有没有读数"**：
    R61 记的是「M313、M317 双双存活 ⇒ 那条闸门没有分辨率」。**这个结论错了，而且错得有价值**：
    两刀的 filter 指着 `testOffScreenProgrammaticSelectionIsRevealedAndNotJumped`，
    而漂移那一臂在 R61 中途被拆进了独立测试 `testRowIndexDriftDoesNotMoveTheViewport` ——
    **判据根本没被执行**，却被读成"判据没牙"。
    R62 把 filter 修好重跑：两刀都 CAUGHT，红在同一句上 ——
    `XCTAssertEqualWithAccuracy failed: ("2125.0") is not equal to ("0.0")`（选中项只是行号漂了，视口却动了）。
    ⇒ 闸门有读数，产品行为与 R61 写的一致；R61 那句「SwiftUI 在 rowIndex 不变时不再调 updateNSView」
    只对"重算但选中没变"那一格成立（臂 3 确实读不出差别），**不**推广到整条闸门。
    电池本身跟着修了两件：① 每刀的 filter 必须能证明"那一臂在被跑的那条测试里"（脚本现在要求
    基线日志里能看到每条判据的结论行，缺一条就整套拒跑）；② M319 在连跑时判成 SURVIVED、
    单独跑判成 CAUGHT —— 是 `__pycache__` 的 mtime/size 撞车 ⇒ 电池统一加 `PYTHONDONTWRITEBYTECODE=1`。
    **结论会随跑序变的电池不能当证据。**

    两刀都落下了、测试全绿：
    * M313 把闸门的键从选中 id 换成行号 ⇒ `testRowIndexDriftDoesNotMoveTheViewport` 照样绿
      （读数：`行号 Optional(60)→Optional(59) id 没变=true originY=0.0`）。
    * M317 把闸门整个拆掉 ⇒ 同样绿。
    **机制**：SwiftUI 在 `updateNSView` 的输入没变时压根不再调用它 —— 删掉顶部一条无关记录、
    收藏再撤掉这两次重算，都没有让宿主视图带着新行号再跑一次。于是"该滚 / 不该滚"这两套代码
    在同一台机器上读不出差别 ⇒ 判据没有分辨率（不是产品坏了，是我这句话没法证伪）。
    与 R42 那条"要么供电要么撤声明"同一族：本轮**先记账、不粉饰**，代码里那句注释暂时保留
    （它是设计意图，不是已验证行为），下一轮二选一：
    ① 找到一条真能让 `updateNSView` 带着"行号变了、id 没变"再跑一次的产品路径（候选：搜索框输入
       使可见集合收缩、或固定项数量变化导致的重排），把它做成第六臂；
    ② 或者把闸门换成"每次重算都滚但带可见判定"，让 M312 那条有分辨率的闸承担全部行为，
       并删掉这句没有读数的声明。

92. **【已结案，R62】R61 那三条"揭示"判据在 CI 上一条都没跑完 —— 现在缺席要逐条点名，登记是硬门**（R61 的 CI 读出来的 / 与 86、89 同族）：
    runner 的 `On-screen interaction probes` 那一步给出 `ui suite exit: 137  executed: 0  已下结论的用例: 0`
    —— 240 秒看门狗收掉了整卷，一条用例都没下结论（这是 D-7 时代就记过的"这一类探针在 runner 上会挂死"，
    本轮第一次因为它而**让一条产品判据在 CI 上不存在**）。
    ⇒ 61 的回归在 CI 侧只有 `SelectedRowRevealTests`（`rowIndex` 真值表 + 两条源码守卫，不依赖 env，
    确实在 772 例里跑过）兜着；"选中视口外的行会不会被滚出来"这件事**只有本机判得**。
    两条出路（R62 选一条，别默认"反正本机能跑"）：
    ① 把这三臂拆成一条**能在 240s 内跑完**的形状（候选：只留臂 2 + 臂 5 那一格、把夹具从 60 条降到 12 条、
       窗口高度固定，别再用 `UI_AUDIT_ENTRIES` 的默认量）；
    ② 或者明确登记成"本机专属判据"，并在 CI 步骤里把这条缺席写成一行有名字的汇报。

    **R62 选了 ②，并且把它做成一条会红的门**：新增 `scripts/probe_coverage_gate.py` +
    `scripts/probe_coverage_expectations.json`（11 条在屏判据逐条登记 `runner=can/cannot` + 理由），
    CI 里在探针那一步之后加一步 `On-screen probe coverage floor`（**硬门，不是报告型**）。
    它判形状不判耗时：`UNLISTED`（源码里有、清单里没有）/ `STALE`（清单里有、源码里没了）/
    `REASONLESS`（说跑不了却不写为什么）/ `NOT_RUN`（说跑得了却没下结论）/
    `NOW_RUNS`（说跑不了却跑到了 ⇒ 逼着改登记）/ `BAD_RUNNER_FIELD` / `FAILED`（红必须指名）。
    对真 CI 那份日志（`fixtures/r62_runner_ui.log`，run 38603034761 逐字片段）它绿，
    但同时打 `PROBE_NOT_RUN 11/11 条在屏判据这次没下结论：…` —— **绿得有内容**，
    这是这条门存在的理由：既不许恒红（R39 那一族：恒红的守卫最后被人删掉），
    也不许绿得像什么都没发生。
    判据：`scripts/tests/test_probe_coverage_gate.py` 12 条（含"登记必须与源码同一批"这条
    会随新探针用例变红的活检查）；电池 **M318–M324 七刀全 CAUGHT**
    （`.scratch/motion-audit-2/r62_mutation_battery.log`）。
    **仍然开着的另一半**：这 11 条今天确实只有作者本机跑过 —— 本门让这件事可见，
    没有让它消失。真要 runner 上跑出结论，得先查清探针在无头 runner 上挂在哪一句（新 BACKLOG 93）。

    → **R86 更新（不结案）**：接上了 `scripts/ui_probe_report.py` ——
    它把 `Test Case ... started` 与有结论的行做差，输出 `UI_PROBE_HUNG=<用例名>` /
    `UI_PROBE_NO_CASE_STARTED=1` / `UI_PROBE_ALL_CONCLUDED=1`，
    而"给不出名字"的四种形状（日志不完整、喂的是步骤摘要、空日志、文件读不到）**一律红**。
    CI 两步各用一次：`On-screen interaction probes`（报告型）只把名字打出来，
    `On-screen probe coverage floor`（硬门）要求名字必须给得出 ⇒ `PROBE_FLOOR_STOP_UNNAMED=1` 才红。
    为什么不需要测试自己打点：本机 spike（50 秒 `kill -9`，退出码 137）实测 started 行留在日志里，
    13 started / 12 concluded 的差集正好点名那条正在跑的
    （`.scratch/motion-audit-2/r86_spike_partial_output.md`）。
    **仍然开着的理由**：runner 上到底是"第一条就挂住"还是"一条都没开始"，
    是**下一次 CI 的读数**，本轮不许替它回答；那之后才谈得上"路 b"（让能跑的那几条真的跑起来）。
    牙 M465–M472 共八刀全部 CAUGHT（M472 是元层那一刀：给"两支闸门不冗余"的守卫自己喂一个假阳性）。

    → **R89 拿到一条新事实（也欠一条）**：本机按 CI 原样跑，这一卷在 90 秒内**能跑完**
    （日志里有 `testAccessibilityTreeCoverage skipped (0.623s)`、下一条 started、以及 swift-testing 的结尾行），
    而 runner 上 240 秒收不掉 ⇒ "runner 上卡在哪"与"本机为什么能跑完"之间的差**还没有名字**。

    → **R91 把这一格翻面了**：本机按 CI 原样跑，三遍都是 **180 秒收不掉、有结论 0**
    ⇒ R89 那句"本机 90 秒跑得完"与今天矛盾（差在哪还没有名字），而"runner 上跑不动"这个前提
    本身也被推翻：真因是那条僵尸拖选探针（见 125）。⇒ 修完本机第一次跑到
    `心跳=10 executed=10 passed=7 skipped=2 failed=1`。登记里那十行 reason 写的"runner 上整卷在第一条结论之前就被收掉"**成因错了**，
    但"runner 今天能不能跑到"仍要等下一次 CI —— 不许拿本机结果替它改口。
    R89 把看门狗修到真的能收掉 xctest（D-147），但这条差本身要等下一次 CI 的
    `UI_PROBE_RUNNER_ALIVE` / `UI_PROBE_ORPHAN_XCTEST` 两格才算有读数。

    → **R90 的读数**：`UI_PROBE_ORPHAN_XCTEST=0`（R88 三条 run 连着是 1）⇒ R89 的收杀够到了；
    `skipped 步骤数 = 0`（R88 是 7）⇒ 四道硬门挪位置生效，仪器的红不再吃掉产品的证据。
    92 剩下的那一问仍然是：**本机 90 秒能跑完 vs runner 240 秒收不掉**，这一格还没有名字。

93. **在屏探针在无头 runner 上到底挂在哪一句**（R62 开 / 92 的另一半）：
    R62 的覆盖门让「11 条判据今天只有作者本机跑过」这件事可见了，但没让它消失。
    已知事实：runner 上 `swift test --filter UIInteractionProbeTests` 在 240s 内**一条用例都没下结论**
    （run 38603034761），而本机同一卷 3 条揭示相关用例 6.3s 跑完、全量在屏探针也就几十秒。
    ⇒ 挂的位置在**第一条用例内部**（按字母序第一条是 `testAccessibilityTreeCoverage`），
    候选原因三条：无头会话里 `NSApp.activate` / `makeKeyAndOrderFront` 等不到窗口真正上屏；
    `RunLoop.main.run(until:)` 在没有窗口服务器时不返回；或者 AX 遍历在沙盒里被权限卡住。
    下一轮做法：CI 那一步先只跑**一条最便宜的用例**并带 30s 看门狗，把「挂死」与「慢」分开
    （同 R36 那条：挂死和跑得很慢必须区分开），拿到名字之后再决定是修探针还是永久登记为不能跑。
    为什么值得做：只要这一卷在 runner 上跑不动，**所有在屏行为判据都只在一个人身上生效**，
    而 R61 那类「选中/滚动」的回归恰恰只有真实表格能判。

    → **R87 有了第一个读数，而它推翻了一半推断（所以仍不结案）**：
    R86 接上的 `scripts/ui_probe_report.py` 在 runner 上报的是
    `UI_PROBE_PROGRESS started=0 concluded=0` + `UI_PROBE_NO_CASE_STARTED=1`（`UI_PROBE_NAMED=1`，
    所以那道硬门没红 —— 它给得出名字）。
    ⇒ 原文那句"挂在按字母序的第一条用例内部"（预测名 `testAccessibilityTreeCoverage`）**没有被证实**。
    但 `started=0` 有两种成因，这一份日志分不开：
    ① 进程真的在第一条用例开口之前死了（启动/会话层）；
    ② 用例其实跑了，而 `swift test` 的 stdout 在 `kill -9` 时整块丢
       （重定向到文件 ⇒ 块缓冲；这一族本仓库 R64 / R84 各现场一次。
       R86 的 spike 只证明"能留住"13 行，没证明"每次都留得住"）。
    ②为真时 `NO_CASE_STARTED` 就是一句关于产品的假话。
    ⇒ 分开它的方法（R88 做）：那一步同时读**产物通道** ——
    `/tmp/shots-ci` 里有没有帧、探针的 readings 文件有没有写。有帧没日志 ⇒ ②；没帧没日志 ⇒ ①。
    原文那句"下一轮做法：先只跑一条最便宜的用例并带 30s 看门狗"本轮**没有采用**：

    → **R89 在 runner 上确认**：`UI_PROBE_START_LINES_LOST=1`（收掉那一刻 xctest 还活着）
    ⇒ 成因是②（stdout 块缓冲被 SIGKILL 整块带走），不是①。这一格从此不再依赖我本机那一次 spike。
    而"挂在哪一条"仍然没有名字 ⇒ 交给 **122**：本轮定了做法
    （探针文件级已有的 `emit()` 走 stderr=直接 `write(2)`，CI 的 `2>&1` 会把它收进同一份日志；
    缺的只是每条用例开头一行心跳，而 `setUpWithError()` 里 `self.description` 就给出
    `-[类名 用例名]`，与 XCTest 那行同名 ⇒ 一处改动覆盖 11 条）。

    → **R88 把成因分开了（但这一条仍不结案，因为"哪一条"还没名字）**：
    本机按 CI 原样重跑（`.scratch/motion-audit-2/r88_spike_partial_channel.md`）读到
    `kill -9` 之后 `xctest` 带着 11 条用例名继续活着、而日志 119 字节零条 started
    ⇒ 上面列的 ② 为真：**是通道丢了，不是没开始**。R86–R87 那两遍 CI 读的 `NO_CASE_STARTED` 是假话。
    修法见 D-146：看门狗改杀进程组，成因由"收掉那一刻的进程表"签。
    ⇒ 剩下的那一半仍然没有名字：**挂在哪一条**。日志通道做不到（它会被整块带走），
    产物通道也只覆盖 11 条里的 3 条（本轮量到的：focus-chain 两张、reveal 两张，
    字母序第一条 `testAccessibilityTreeCoverage` 不写盘 ⇒ "没帧"证不了任何事）。
    ⇒ 那一半交给 **BACKLOG 122**（每条判据自己写一行读数，R56 给动效卷用过的那个形状）。
    R86 的 started 差集已经能点名（只要日志留得住），而②这一格是那条做法也解决不了的。

    → **R86 更新（不结案，但把答案变成一个会被读到的读数）**：原文写的下一步是
    『CI 那一步先只跑一条最便宜的用例并带 30s 看门狗』。本轮换了个更一般的做法：
    不预设跑哪一条，而是把 `Test Case ... started` 与有结论的行做差 ——
    `swift test` 自己就在打点，`kill -9` 之后那些行留在日志里（本机 spike 实测 13 started / 12 concluded，
    退出码 137 与 CI 同形）。⇒ 新增 `scripts/ui_probe_report.py`，CI 两步各用一次，
    硬门那一步要求『说不出为什么停』必须红。
    **预测先登记在这里**（免得事后挑一个解释）：下一次 CI 若报
    `UI_PROBE_HUNG=testAccessibilityTreeCoverage`，就证实原文那句『挂在按字母序的第一条用例内部』；
    若报 `UI_PROBE_NO_CASE_STARTED=1`，则挂死发生在 XCTest 开始报用例之前（启动/会话层），
    那时原文列的三条候选原因要整条重排；若报 `UI_PROBE_ALL_CONCLUDED=1`，
    说明 92/93 的前提（runner 上跑不动）已经不成立，那两条一起结案。
    三种结果都是答案，而这一格的价值就在于它**不许**留成『大概是无头会话的问题』。

    → **R90：这一格第一次有名字，而且是两个独立证人同意的**。
    ① 产品自己发的心跳（`probe-pulse.log`，`setUpWithError` 每条用例一行）点名
    `testDragSelectExpandsSelectionInsideTheRealList`：开了口、没有结论；
    ② `sample` 采到的栈：`MouseSynthesizer.drag → NSWindow sendEvent: → _NSGFGestureEnvironment
    → NSCoreDragManager _dragUntilMouseUp → CoreDragStartDraggingAsync
    → _BlockUntilNextEventMatchingListInMode → mach_msg`（0% CPU，在睡，不是在转）。
    ⇒ 机制：**CoreDrag 的模态循环在等一个不会来的 mouseUp**，本机可复现，不是 runner 专属。
    ⇒ 一条措辞更正：R89 说"93 的成因在 runner 上被确认"，确认的是**通道为什么丢日志**，
    不是**为什么挂死**。修法（加看门狗 vs 绕开 `sendEvent` 直接调手势逻辑）开成 **BACKLOG 125**。

    → **R91 结案（本机侧）**：名字有了（心跳点名）+ 机制有栈（CoreDrag 模态循环）+ 修法落地
    （撤掉合成拖拽，见 125）。剩下的一格交给 92：**runner 上**现在跑到几条，等下一次 CI。

    → **R91 收尾时读到 R90 的 CI（run 38846896495），补一条与"能不能跑到"无关、但会影响
    后面所有 CI 读数的更正**：那一次与上一次（38838819089）里，**最后两道闸门读的不是真日志**。
    `Capture gate` 的 `CAPTURE_GATE_RESULT=fail …这一步没跑到用例` 与 probe floor 的
    `UI_PROBE_CHANNELS_CONTRADICT … started=probeA` 都是**假红**：`probeA` 是我自己自检夹具里的
    用例名。成因是 `a68a08f`（R89）把这两步挪到作业末尾之后，`Release script tests` 那一步的
    `run_bash()` 只把 `/tmp/shots-ci` 换进临时目录，于是 `cp FAKE_LOG /tmp/frames.log` 这类夹具
    写进了**作业的共享 `/tmp`**，把闸门要读的那三份日志覆盖了。本机实测：先写 `REAL-MARKER`，
    跑一遍自检，文件变成 `Test Case '-[p probeA]' started.`，marker 一行不剩。
    **按真读数重判**（那些行是 03:51:51 在屏那一步自己打的，早于自检）：
    `UI_PROBE_ORPHAN_XCTEST=0`（R90 的看门狗结论成立）、`RUNNER_ALIVE=1`、`ui suite exit: 137
    已下结论的用例: 0`、心跳 `pulse=2` 点名 `testAccessibilityTreeCoverage` 与那具僵尸
    ⇒ 僵尸在 runner 上确实开了口，R91 删它不需要撤回。修法开成 **BACKLOG 128**。
    全部读数与时间线见 `.scratch/motion-audit-2/r91_ci_readings.md`。

    → **R92 结案（那一格有答案了）**：读到 R91 推送的 CI（run 38852286519）——
    `已下结论的用例: 6`、`started=7`、`UI_PROBE_CHANNELS_AGREE=1`、名册 `源码用例=10 登记=10` 无 STALE。
    ⇒ runner 上不是"一条都跑不到"，僵尸确实是挡在最前面那一个；追了五轮的这一格到此为止。
    第 7 条 `testRightClickMenusAppKitWouldShowAreChinese` 是新的一格，开成 **BACKLOG 132**
    （本机它是跑完的 ⇒ 只做到点名，没在 runner 上 `sample`，不写"同一族"）。

94. **浮层与侧栏的行首用 📄 emoji 当文件图标**（R63 看 `quickpick-typed-420x300-light.png` 时看到）：
    来源是 `EntryPresentation.preview(for:)` 里 `"📄 \(url.lastPathComponent)"` ——
    也就是**侧栏、浮层、详情**共用同一条字符串。三个问题：
    ① Apple Color Emoji **不吃 tint**，暗档里它保持自己的颜色，与旁边 `.secondaryLabelColor` 的
       灰字不同极性（这一条本轮只看了帧，没量对比度）；
    ② 与全产品其余图标（SF Symbols）不是同一套语言 —— 同一族问题 R2-8 已经为设置侧栏记过一次；
    ③ 它进了**参与搜索匹配的字符串**（`QuickPickModel.filtered` 与侧栏都拿 `shortPreview` 比），
       所以"📄 "这两个字符是搜索语义的一部分，改它不是纯视觉改动。
    下一轮做法：先量暗/亮两档下这一格的对比度与基线（帧已经有了），再把图标改成
    `NSImageView` + `NSImage(named: NSImage.Name("doc"))`/SF Symbol 的**结构**（不进字符串），
    同时给"改字符串会影响搜索"补一条真值表。**本轮不动**：这是跨三个表面的呈现层决定，
    塞进 R63 会让这一轮的改动面失控。
    → **R65 结案，并且先把 R63 的推广纠正掉**：那句"**侧栏、浮层、详情共用同一条字符串**"是错的 ——
    读代码的结果：侧栏的 `RowTextColumn` 对 `.file` / `.files` 走的是 `FileNameText` / `MultiFileTitle`
    （**不经过** `shortPreview`），详情走 `sizeDescription`（"文件: report.pdf"），
    菜单栏走 `menuTitle`（自己拼，不带 emoji）。⇒ 那个 📄 **唯一可见的表面是快速选择浮层**，
    而"参与搜索匹配"那一条是真的（`QuickPickModel.filtered` 拿整条 `shortPreview` 比）。
    交付：`EntryPresentation.preview` 里那三处 `"📄 …"` 去掉（文案只说"是哪一条"）；
    浮层每行一枚 SF Symbol（`doc.text` / `photo` / `doc` / `doc.on.doc`，16pt 列、`.secondaryLabelColor`），
    名字与侧栏 `RowLeadingVisual` 一一对上；`photo` 沿用详情头已经在用的那个名字。
    判据 5 条（真值表 + 尺的正对照 + 名字画得出 + 两边同一套名字 + 每行有图且共享一条左轴），
    电池 **M343–M349 七刀全 CAUGHT**。浮层那 4 张帧（`list` / `typed` × 亮暗）随之更新，
    其余 **118 张逐字节不变**。①那条"emoji 不吃 tint、暗档极性不同"本轮**没有量对比度**，
    它随 emoji 一起消失了，不需要再量。

95. **在屏像素通道在这台机器上是"尺寸正确但全空"**（R63 实测）：
    `CGWindowListCreateImage(.null, [.optionIncludingWindow], windowID, [.bestResolution])`
    返回 932×692 的图（= 420×300 @2x + 投影），但**每一个像素都是透明的**
    （`alpha ≤ 0.02` 占 100%）。同一件事在 `screencapture -x -R…` 上表现为
    "could not create image from rect"。⇒ 这个通道的读数**不能**当判据，
    而且它比返回 `nil` 更危险：`nil` 会被读成"没跑"，而一张尺寸正确的空图会被读成"屏上是好的"。
    本轮的处置：所有像素判据一律走 `cacheDisplay`（与 122 张基线同一条通道），
    并把这条写进探针的注释里。要真正拿到"用户屏幕上那一张"，需要
    给测试宿主开 Screen Recording 权限，或换 ScreenCaptureKit（macOS 12.3+，
    但要 entitlement / 用户授权，且会引入新依赖）—— 与 BACKLOG 93 同族（都是"这一类事实
    今天只能通过一条没人管着的通道拿"），但对象不同：93 是探针挂死，这条是截图通道空转。

96. **本机 `swift test` 会丢一卷测试后半段的 stdout**（R63 撞到两次）：
    `testCaptureKeyViews` 的 `CAPTURED 122 -> …`（第 454 行）到了日志里，
    而同一个函数后半段的 `BOTTOM_INK_IDENTITY`、`SPARSE_EXEMPTION` 三条**一条都没到**；
    `MotionFilmstripTests` 更明显：stdout 只剩 4 条 `MOTION_NOT_RUN`，
    `MOTION_RESOLVE_SUMMARY` 整个不见，于是 `motion_floor_gate.py` 判
    `MOTION_FLOOR_NO_RESOLVE` + `REDS=1` —— **一次假红**，指错了方向。
    动效那一卷靠 R11 立的**文件通道**（`<MOTION_OUT>/motion-readings.log`）活了下来：
    换它之后同一道门是 `judged=4/4 REDS=0`。
    要做的是给捕获卷补同一条通道（或把结论行挪到该函数**前半段**，见 R53 那条
    "结论行要打在能力闸门之前"），否则 CI 上任何以 stdout 为唯一来源的捕获结论
    都建立在这台机器"今天没丢"的运气上。
    → **R63 的 CI 读数（run 38685562002）把这条从"本机现象"升级成"两台机器都会"**：
    runner 上 `CAPTURE_PROBE quickpick` 与本轮新写的 `QUICKPICK_FIXTURE_ROWS` 各 **0 行**，
    而同一个测试类里 `QUICKPICK_EMPTY_SENTENCE` / `QUICKPICK_LONG_QUERY` / `BOTTOM_INK_IDENTITY`
    全都在。本机也有同一形状 —— 本轮十遍跑里三个标记各自到没到的计数（逐份 `grep -c` 数出来的）：
    `r63_capture.log` 0/0/0、`capture2` 0/0/1、`capture3` 0/0/0、`capture5` 1/1/1、`capture6` 1/1/1、
    `capture7` 0/0/0（那一遍是 crash 那遍）、`capture8` 2/1/1、`full` 1/1/1、`full2` 1/1/0、
    `full3` 0/0/1（SPARSE / BOTTOM_INK_IDENTITY / CAPTURE_PROBE）。
    ⇒ **上面那句"丢的是函数后半段"是我当时把机制说过头了**：真实形状是**按条随机丢**，
    位置不是决定因素（这条现在只有"两台机器各丢过哪几条"这个级别的证据）。
    → **R64 把"按条随机"也更正掉**：那同样是我加的解释，不是量出来的。见下面 R64 那一段的
    两份真 artifact —— 形状是**连续大块丢**，切点落在行中间。
    两条结论：① 唯一能证明"这条判据跑过"的是 XCTest 自己那行 `Test Case … passed`
    —— 本轮三条浮层判据在 runner 上都有这一行，所以判据确实跑了，这一点不需要靠读数证明；
    ② 任何"读数只在 print 里"的判据都必须补文件通道，**动效卷 R11 已经做过一次，捕获卷照抄即可**。
    → **R64 做完，并且把形状量清楚了**（本机两遍真 artifact + 两份 runner 日志逐行比对）：
    ① **丢的是连续大块**：捕获卷 488 行读数，`--filter` 那一遍 stdout 只剩前 164 行，
    后 **324 行整块不见**（66.4%，切点在行中间：`…bottomI` 直接接 `Test Case …`）；
    全量那一遍（CI 的 `2>&1 | tee` 形状）少了 **238 行**（48.8%），是 **3 块**（读数下标 0–48、142–217、296–408）。
    两遍里五条判据自写的 marker（`CAPTURE_PROBE quickpick`、`QUICKPICK_FIXTURE_ROWS`、
    `QUICKPICK_EMPTY_SENTENCE`、`QUICKPICK_LONG_QUERY`、`CAPTURE_READINGS_SELFTEST`）**全丢**，
    而 37 / 775 条 `Test Case … passed|skipped` 结论行**一条没少**，作业 0 退出。
    ①′ **同一个命令形状再跑一遍，丢的是同一块**（第二、三遍都是下标 164–487 那 324 行）
    ⇒ 在 `--filter` 这个形状上它是**可复现的位置**，不是"这次运气差"；
    324 行实例 = 316 条不同的行（闸门报的 `补回=316` 是去重后的数）。
    ⇒ 丢不丢**不影响红绿灯**，只影响"今天判了什么"还在不在。
    ② runner 那两份只算现场证据（GitHub 的日志本身也可能截，所以不能拿它当机制）：
    run 38683762166 的捕获那一步 4 个浮层 marker 到 **0/4**，run 38687419144 到 **2/4**
    —— 同一批代码，两次结果不同，这一条才是"这次没丢"不能当理由的直接证据。
    ③ **交付**：`CaptureReadings.swift`（文件通道，第一次整份重写 + 之后 FileHandle 追加）、
    捕获卷 69 处 `print(` → `emit(`、守卫 `testCaptureReadingsUseTheFileChannel`
    （规则是绝对的：那个文件里 `print` 出现次数 = 0，所以通道实现单独住一个文件）、
    `ci_capture_gate.py --readings`（**并集 + 缺通道算一条有名字的红**，
    本机拿真 artifact 跑一次：`补回=316 行`，不给 `--readings` 同一份日志仍然是绿的）。
    电池 M337–M342 六刀全 CAUGHT（`.scratch/motion-audit-2/r64_mutation_battery2.log`），
    其中 M338 抓到的是**我自己这轮写的第一版正对照**：它拿 needle 拼对照，
    needle 改坏成多一个空格时对照仍然 3/3 ⇒ 已改成 `\u{0070}` 转义的独立串。
    **这条继续开着**，等 R64 的 CI 那一步真把 `补回=k>0` 打出来才收（`--readings` 在 runner 上第一次跑）。
    → **R64 的 CI 已读到（run 38693365411 / commit 0614466）⇒ 结案**：那一步打出
    `CAPTURE_GATE_CHANNELS stdout=1 readings=376 行 补回=65 行`，整作业 success、18/18 全绿、
    `CAPTURE_GATE_RESULT=ok`。**工资的形式和我预期不同，这点如实记**：那一遍五条浮层 marker
    **恰好都在 stdout**（丢是偶发的，这次没丢），真正被补回来的是**登记** ——
    `CAPTURE_GATE_CASES` 的 `NOT_RUN` 从上一遍（不带 `--readings`）的 **25** 涨到 **50**，
    也就是说上一份"绿"的报表里有 **25 条『这台机器判不了』的登记根本没被看见**。
    ⇒ 同一族缺陷的另一个方向：不是红被吞，是**已知盲区被吞**，而吞掉它的不是 `continue-on-error`，是 stdout。
    它开出的下一条见 **98**。

98. **在屏探针那一步（`ui.log`）仍然只有一条通道**（R64 结案时开 / 96 的下一步）：
    捕获那一步现在有 `--readings`，而 `On-screen interaction probes` 那一步的结论只有
    `tee /tmp/ui.log` 一份 —— 同一台机器、同一个 `swift test`、同一种"成块丢"。
    今天它的表现是 `PROBE_COVERAGE_SUMMARY … 本次下结论=0`（11 条全部登记为未跑，BACKLOG 93），
    于是"这一步到底有没有跑到"与"跑到了而结论行没打出来"在报表上**长得一模一样**。
    要做的不是新判据，是把 `CaptureReadings` 那一条通路复制给探针卷（`probe-readings.log`），
    再让 `probe_coverage_gate.py` 也吃并集。**在那之前，探针那一步的"0 条下结论"不能当结论用**。

101. **`fade-clock-snaps-here` 是一条"整卷级"的未覆盖，而覆盖地板只数"臂级"的**（R66 开 / 与 49、92、100 同族）：
    `motion_floor_gate.py` 的 UNREGISTERED / REASONLESS / BAD_REASON 三格读的都是
    `MOTION_RESOLVE_SUMMARY judged=n/m not-run=<臂名>`，而 R66 新加的这条 skip 不属于任何一臂
    （它整卷一条：`testListRowsDoNotAnimateAndNothingClaimsTheyDo` 被环境挡掉了）。
    今天它的可见度只有两行：日志里的 `MOTION_FADE_CLOCK … 判定=拍成跳变` 与
    `Test Case … skipped - MOTION_NOT_RUN=fade-clock-snaps-here …`，
    而后者只在 `MOTION_RESOLVE_SUMMARY` 缺席时才会被 `MOTION_FLOOR_SKIPS` 打出来。
    ⇒ 登记没有 run 号、没有计数、也没有"这条今天第几次缺席"的趋势 ——
    BACKLOG 49 的原话就是这种形状：一条说得清理由的缺席，如果数不出来，慢慢就变成免检牌。
    要做的：给闸门加一层 `suite_not_run`（理由白名单 + 每次运行都打计数），
    并把 `MOTION_FADE_CLOCK` 的判定并进结论行（例如 `MOTION_RESOLUTION=能分辨/拍成跳变/探针坏了`），
    让人一眼能看出"这一卷的淡入判据今天有没有牙"。

    → **R75 推进一半**：`notice-banner` 那条缺席从今天起是**臂级**登记的
    （`MOTION_NOT_RUN=witness-snaps-here notice-banner` 进 `MOTION_RESOLVE_SUMMARY` 的 not-run 名单，
    闸门按 REASONLESS / UNREGISTERED / BAD_REASON 三格数它），证人判定也进了每条臂的
    `MOTION_JUMP_WITNESS` 行。剩下两格仍然欠着，其中③是 R75 新认下来的：
    ② `suite_not_run` 那一层（整卷一条的缺席仍然只活在 skip 行里）；
    ③ **闸门不查矛盾** —— 某臂报 `witness-snaps-here`，而同一份日志里证人 `判定=能分辨`，
    今天只有判据自己守着（`jumpAdjudication` 只在证人 snap 时才赦免），闸门层没有这道冗余。
    这一条记在这里而不是新开条目，是因为它和 101 原话是同一件事：**缺席要数得出来，
    而且数的时候得顺手看一眼给它签字的那台机器当天有没有牙**。

102. **runner 上的现象看不到图：动效那一步的读数被 `head -120` 截掉，胶片又从不上传**（R66 读 CI 时撞到）：
    R65 那一步自己打的 `MOTION_LINES=146`，而控制台只 `grep -E '^MOTION_' | head -120`
    ⇒ **至少有 26 行从没进过日志**（`MOTION notice-banner frames=… 逐帧=[…]` 就不在控制台里，
    而它在 `/tmp/r66_motion.log` 里每遍都有）。
    注意这一格有两种成因、我没有分开：`head -120` 的截断，与 R64 那条"stdout 会成块丢"
    （两处都会让同一行到不了日志，而 /tmp/motion.log 没上传，无法反查是哪一个）。
    ⇒ 分开它们的前提恰恰是下面这半条：**把日志与胶片交出来**。

    另一半：那一步在 `/tmp/motion-ci` 里写了 11 张 `*-strip.png`，作业结束就没了
    （`grep upload-artifact .github/workflows/ci.yml` = 0 命中）⇒
    "只有 runner 上才看得见的现象"没有图可看，而 R66 的整件事正是这一类：
    我只能用数字推断"runner 把 150ms 的淡入拍成了跳变"，没法像本机那样逐帧看。
    要做的：① 读数改成按族分块全打（或把上限抬到读数总数之上并显式记账"截了几行"）；
    ② 把 `/tmp/motion-ci` 作为 artifact 上传（`if: always()`，只留 `*-strip.png`，
    一轮约 2–3MB），并在日志里打一句"哪些胶片被上传了"。
    两条都不改判据，改的是"红能不能被看见"这一层。

103. **捕获通道里没有"窗口底"，所以悬停那一档的"够不够响"至今没有机器判据**（R67 开）：
    `quickpick-hover-*` 两张帧里，行底是**透明**的（同帧 `transparent=76.4%`），
    那一层 6% 的灰是直接画在透明上的 ⇒ 合成到中灰底才能读出变化，
    而真屏幕上它是画在一块实心材质上的。后果分成两半，都不许糊过去：
    ① **亮度那一半判不了大小**：同一档灰在亮档合成后只动 −2.15/255、暗档动 +6.33/255
       （实测，`OVERLAY_HOVER` 那两行），所以判据只敢判**符号**（极性），
       "抬升 ≥ 令牌推导线的一半"用的是 alpha 而不是亮度 —— 这是把尺换掉了，不是把线放宽了；
    ② **"0.06 这一档在真屏幕上看不看得出来"没有读数**，今天靠两件事顶着：
       R15 在侧栏同一枚令牌上量过的 `idle→hover 15.9 / 14.0`（继承），与人工批次 67（用户看）。
    要做的：把浮层的捕获从"拍 `NSWindow` 的 contentView"改成拍**带窗口底的那一层**
    （`frameView` / `window.frameView.documentView` 那条路），让实心底真的进帧；
    成功后 ① 的亮度判据可以升级成大小，② 可以撤掉"靠继承"这半条。
    代价先写清楚：换捕获对象会把 **124 张帧全部重画**，而且 R19 那条"搬家会弄坏布局"的旧账
    要重新量一遍（R63 已证明不搬家也塌，所以这不是新风险，但基线要按同提交 update）。

104. **runner 上动效那一步连着四遍 `exit 1`，红的是不同的判据，而淡入时钟比它要作证的判据更粗**
    （R67 读 R66 的 CI 时撞到 / 与 49、92、100、101 同族）：

    | run | 提交 | `motion suite exit` | 红的用例 |
    |---|---|---|---|
    | 38693365411 | R64 | 1 | 自校验那条 |
    | 38696695788 | R65 | 1 | 自校验那条 |
    | 38699044800 | R65 台账 | **1**（而整份 CI 是**绿**的） | `testBandCaptureIsCheaperAndStillSeesTheMotion`（26.04 > 22.20） |
    | 38706222682 | R66 | 1 | `testTransitionsAreActuallyRunning`（notice-banner 只变 53ms，线 150ms） |

    两件事同时成立：**新闸门是对的** —— 38699044800 那一遍就是 BACKLOG 100 说的"红着绿过去"，
    R66 的 `MOTION_FLOOR_SUITE_RED=1` 第一次把它点了名（名字与断言原文都进了日志）；
    **但这两条红都还没有归因** —— 它们量的都是"这台机器的采样率"，
    而本轮 runner 的证人读数是 `MOTION_FADE_CLOCK … 中间态帧数=0 帧数=26 采样≈80ms 判定=拍成跳变`
    （本机同一颗探针：中间态 8–11 帧、采样≈21ms、判定=能分辨）。

    **为什么今天不能拿这条证人给 notice-banner 免检**（这才是这一条的正事）：
    证人自己采到 80ms，而它要作证的判据用的是"事件内最粗采样 35ms"——
    **证人比被告粗，就没有资格作证**：一个 150ms 的淡入在 80ms 间隔上本来就只能落 1–2 帧，
    `中间态帧数=0` 是证人的分辨率，不是产品的跳变。
    拿它去 skip 等于把"我没看清"写成"它没动"（R66 的 M356 抓的就是这个形状，只是方向相反）。

    要做的：把证人搬到与判据**同一颗尺子**上 —— 同一种夹具（`Grabber` 同一条抓帧路径）、
    同一种帧尺寸（760×48 那条带）、同一种 runloop 节奏，然后重新问一次 runner：
    ① 若证人变成"能分辨" ⇒ notice-banner 的红是**产品**的，必须修（或按 100 的规矩登记成有名字的未覆盖）；
    ② 若证人仍是"拍成跳变"（此时它已经和判据一样粗）⇒ 那才是环境，两条判据一起改判 `not-run`，
       并按 101 那条把"整卷级缺席"计进 `suite_not_run`。
    在①/②分出来之前，`suite_reds` 保持为空 ⇒ CI 红着，这是**如实记账**，不是漏修。
    → **R72 把证人换到有资格回答的形状，并证伪了 R68 的因果**：runner 上证人 `采样≈81ms`（R66 是 80ms），
    而面积已经小了 12.6 倍 ⇒ **面积不是原因，睡眠节拍才是**（证人 `sleep 0.02` vs 判据那条 `0.004`）。
    现在证人用同一个节拍，且 `MOTION_FADE_CLOCK_COST` 把"间隔"与"抓帧中位"分成两个数打出来
    （本机 `采样≈4ms 抓帧中位=0.1ms`）。①/② 仍要下一次 CI 才分得出来 ——
    但这一次是**有资格的**一次：若 runner 落到 ≈16ms ⇒ `可分数段=9 ⇒ 合格` ⇒ 判红就是产品的事；
    若仍 >50ms ⇒ 那才是环境，两条判据一起改判 not-run 并进 101 的 `suite_not_run`。
    同一遍还给出另一条本机数：`MOTION_BAND` 带 26.0ms vs 整窗 44.4ms ⇒ 省 1.70×，
    而那条判据的线写的是 2× ⇒ 与 R38 同一课，R72 改成"只判方向、倍数只报"（D-130 决定 2）。
    → **R68 交了第一半**：证人抓帧区域从整张 320×180pt 改成 190×24pt（判据那条带是 760×48pt ⇒
    证人从此是它的 **1/8**，结构上不可能比被告贵），并且决定表多了一根轴
    （`qualifies(declaredDurationMilliseconds:)`：证人自己那条淡入要切得出 ≥3 段才有资格免检）。
    本机读数 `证人采样≈20ms 声明=150ms 可分数段=7 合格=是`；runner 那一遍 80ms ⇒ 1 段 ⇒ 不合格 ⇒
    **红着并指名去修证人**，不再偷偷 skip。①/② 谁成立仍要下一次 CI 回答（R67 那一遍在到达动效步之前就红了）。

    → **R75 结案（①②都有答案，而②的答案是我没预期到的第三种）**：

    ① 那 80ms 里抓帧只占 **0.4–0.5ms**（`MOTION_FADE_CLOCK_COST 帧数=75 采样≈32ms 抓帧中位=0.5ms`），
    其余全是睡眠节拍 ⇒ R68 那句"面积决定证人采得粗"彻底作废，R72 的 0.004 把采样买到 **32ms**、
    `可分数段=4` ⇒ 证人第一次 `合格=是`。
    ② 红不是产品，也不是含糊的"环境"：**是判据把一次采样间隔当成了过渡时长**。
    三遍 runner 同一份判据代码：`notice-banner` 都是 2 帧，时长 32 / ≥60 / 36ms ⇒ 红、绿、红
    （run 38726667469 / 38726991211 / 38730788527）；
    而证人三遍同一句 `采样≈32ms 可分数段=4 合格=是 判定=拍成跳变（中间态帧数=0）`。
    同一次运行里两条判据对同一台机器给相反处置 —— 阳性对照那支问证人，四臂那支不问。
    修在 R75：`jumpAdjudication` 把证人接到 `.jump`（M392/M393 两刀钉它有牙），
    登记表按实测把这一臂放宽成**有名字的未覆盖** `witness-snaps-here`（带 run 号）。
    剩下的那一半（让判据不吃帧数）仍在 **BACKLOG 77 路 b**，而证人从今天起是它的验收工具。

105. **1× 的捕获通道量不出参照物的圆角：R67 那条"逐行轮廓"判据在 runner 上是假红**（R69 读 R67 的 CI 时撞到 / 与 38、60、89 同族）：
    同一条判据、同一份产品，两台机器的读数（都换算成 pt）：

    | 读数 | 本机 2× | runner 1× |
    |---|---|---|
    | 药丸左沿内缩跨度 | 11px = **5.5pt** | 2px = **2pt** |
    | 灰带左沿内缩跨度 | 11px = **5.5pt** | 5px = **5pt** |
    | 逐行最大偏差（首行） | 0px | **3px** ⇒ 判红 |
    | 中行 x 范围 | 两边相同（44…795 / 22…382） | 两边相同 |

    ⇒ **不稳的那一方是参照物**：灰带是被我改出来的东西，它的读数在两台机器上都是 5–5.5pt；
    而 AppKit 那颗药丸（同一个对象、同一个圆角）从 5.5pt 掉到 2pt。
    机制假设（**没证实**）：药丸是材质，角上的 alpha 不是覆盖率的线性函数，
    而 `alphaLiftProfile` 的门是 `≥4/255` ⇒ 1× 下角上那几个像素过不了门，轮廓被"啃"平了。
    R69 的处置是把这一轴按机器分开：`pillInset < 4px` ⇒ 发 `FRAME_CORNER_AXIS_NOT_RUN=1` 点名"今天没判"，
    同时保留三条两台机器都有牙的断言（灰带自己是圆的 `fillInset ≥ 1`、中行宽度 ≤2px、行数一致）——
    直角版在 1× 上仍然会红（M369 那一刀的形状与缩放无关）。
    要做的：① 在 runner 上把 `floor` 从 4/255 降到 1/255 复量一次，
    如果药丸内缩回到 ≈2pt 以上就证明是门的问题，那条 `≥4px` 的地板就能改回按 pt 表达；
    ② 或者按 BACKLOG 103 换捕获对象（拍 frame view，让窗口底进来），材质在实底上就不是半透明边缘了。
    两条都能把这一轴在 1× 上赎回来；**在它赎回来之前，"圆角与系统一致"这一条只有 2× 的证据**。
    → **R70 交了①的量法**：判据里对**参照物**用三道门（1/2/4）各量一遍内缩跨度并全部打出来
    （`OVERLAY_HOVER_DOOR`），线一个数没动。本机 2× 读数 `药丸内缩@门1/2/4 = 10/11/11px`、
    `灰带@门1/4 = 11/11px` ⇒ **在 2× 上门几乎不影响这件事**（10 vs 11 是抗锯齿的一格）。
    → **R73 读 R70 的 CI，①的答案是"不是门"，这一条结案**：runner 1× 上
    `OVERLAY_HOVER_DOOR 药丸内缩@门1/2/4 = 2/2/2px，灰带@门1/4 = 4/5px`
    ⇒ 把 `≥4/255` 降到 `≥1/255`，药丸读数一动没动 ⇒ **R69 写在注释里的那条机制假设作废**。
    同时灰带在两档缩放上都量得对（1× 理论 5.2 / 实测 4–5；2× 理论 12.0 / 实测 11）
    ⇒ 坏的是**参照物那一侧的读数**（AppKit 那颗材质药丸的角在 1× 的离屏合成里被吃掉），不是产品。
    ⇒ 赎回这条轴只剩 ②那一条路（BACKLOG **103**：换捕获对象，让窗口底真的进来）。
    在 103 做完之前，"悬停与系统同曲率"这一条**只有 2× 的证据**，1× 上由
    `FRAME_CORNER_AXIS_NOT_RUN=1` 点名"今天没判"（R69 的处置原样保留，理由从假设换成结论）。

    → **R70 交了①的量法**：判据里对**参照物**用三道门（1/2/4）各量一遍内缩跨度并全部打出来
    （`OVERLAY_HOVER_DOOR`），线一个数没动。本机 2× 读数 `药丸内缩@门1/2/4 = 10/11/11px`、
    `灰带@门1/4 = 11/11px` ⇒ **在 2× 上门几乎不影响这件事**（10 vs 11），
    所以"1× 量不出圆角"到底是门还是通道，只能由下一次 runner 那一遍回答：
    若门=1 时药丸内缩回到 ≈5px ⇒ 是门，这条轴能赎回来（地板改成按 pt 表达）；
    三道门都给 2px ⇒ 是通道的性质，只能走 103（换捕获对象）。

114. **runner 那一遍到底带不带得动产品那一档（30Hz / 抬 0.12）的常驻循环**（R82 开 / 113 的续问、与 110、38 同族）：

    R81 的 CI 上并排的两行是本机无法解释的：产品 `变化帧对=2 / 帧数=27 / 峰值=0.015 / 采样≈86ms`，
    而那颗 20Hz、抬 0.45 的证人 `帧数=21 变化帧对=13 峰值=0.029`。
    R82 把证人换成与产品同节拍同抬升之后，本机三遍读到的是 20/45 vs 21/45、23/47 vs 23/47、    19/44 vs 19/43 —— **最多差一对**（换尺之前是 20 vs 41）。
    于是 runner 那悬殊的 2 vs 13 有三种可能，本轮没有依据区分：
    ①**参数**：那一档节拍的 Timer 在无头 runner 上就是带不动（那 13 对属于抬升更高的那颗）；
    ②**归属**：产品的 `SkeletonPreviewView` 那份时钟有它自己的问题（它的 `onReceive` 挂在
      `if let step` 的分支上，而证人挂在 `body` 顶上 —— 这是两者唯一剩下的结构差别）；
    ③**通道**：`coverage` 这把尺在 1× 上有别的性质（与 111 同族）。
    下一遍 CI 的三行 `MOTION_SHIMMER*` 就是分诊表：
    等节拍证人 looping 而产品 not ⇒ 命中 ②，`loopAdjudication` 会**红**，那时才动产品；
    两颗证人都不 looping ⇒ 命中 ①，判据点名 `MOTION_NOT_RUN=loop-clock-not-sustainable-at-product-rate`；
    两颗证人的 coverage 本身算不出来 ⇒ 命中 ③，回到 111 那条路。
    不许的处置：抬 `minCoverage`、把 ①② 合并成"反正都算没跑"、或者在拿到那三行之前先改产品。
    → **R83 结案（落在预登记的第一支，而且是被那把等节拍证人量出来的）**：
    runner 那一遍 `MOTION_SHIMMER 扫 帧数=21 变化帧对=0 峰值=0.000 采样≈118ms`、
    等节拍证人 `帧对=35 在变=2 coverage=0.284`、粗节拍证人 `帧对=26 在变=23 coverage=1.000`
    ⇒ 这台机器带得动 20Hz 的常驻循环，带不动 30Hz 那一档 —— 与"视图归谁"无关（②排除），
    也不是 coverage 这把尺算不出来（③排除：两颗证人都算出来了）。
    处置走 `MOTION_NOT_RUN=loop-clock-not-sustainable-at-product-rate`，判据不判产品。
    同轮修掉两朵**上一轮我自己造的**假红（U-160 卷长钉子挂在结论尺的输出上、
    U-162 绝对峰值地板不管处置说话），以及闸门那格单位不一致（U-161）。
    剩下的那一半不是 114 的问题，是登记的问题 ⇒ 新开 **118**。


115. **`TableProbe` 仍然把抓帧时刻存在对象身上**（R82 开 / 与 U-155 同一条，本轮自己留下的第二处）：

    本轮把 `SkeletonProbe` 与 `StateTickProbe` 改成返回 `GrabbedFilm(frames:stamps:)`，
    因为它们的"时刻"要进一条**时间之比**的判据；而 `TableProbe`（行动画那两条）留着
    `private(set) var lastStamps`，四个调用点都是"record 之后当场读"。
    今天它没有错 —— 但 U-155 的证据是：**当场读这件事，写错了也没有断言会红**
    （M443 第一版四条全绿）。行动画那两条判据吃的是"变化段时长 / 采样间隔"，
    与循环那条同一种性质，所以这里迟早也要绑成一卷。
    修法照抄本轮：探针返回一对，删掉共享的可变时刻。优先级不高，但不许忘掉。

116. **同一提交的全量卷里，skip 的条数会自己动 7 条，而那五条没有一行"为什么今天没跑"**（R82 开 / 与 96、100、111 同族）：

    `Executed 796 tests, with 38 tests skipped`（R81 第一遍）与 `Executed 796 tests, with 45 tests skipped`
    （R81 另一遍，同一提交、同一台机器、时长不同）；R82 是 799 / 40。
    差集是这五条 `UICaptureTests`：`testSettingsHelperTextIsNotClipped`、
    `testInkDirectionRulerReadsBothEnds`、`testRowTierProfileSeparatesCaptionFromTitle`、
    `testSettingsCaptionSitsCloserToItsOwnToggle`、`testDarkSettingsSidebarTextIsACountedBlindSpot`。
    它们 skip 的时候台账上看不见，跑的时候也是绿的 ⇒ **判据有没有跑**这件事今天没人审计。
    要做的一小步：这五条各打一行 `CAPTION_PROBE_NOT_RUN=<原因>`（与捕获卷那族同一个形状，
    闸门那边已经有"已登记的 NOT-RUN 逐条列出"的通道），然后 R83 起用两遍跑对比"跑了几条"。
    本轮**没给原因**：第一版怀疑是变异电池的临时目录串了，读源码不成立
    （这五条各用 `temporaryDirectory/r28-clip-<UUID>`）—— 没量出来就别写。

    R86 **收窄**（四遍测量 + 读 R85 的 CI，产物 `.scratch/motion-audit-2/r86_skip_readings.md`）：
    ① 同一提交两遍全量 `801 / 41 skipped`、两遍捕获 `47 / 4 skipped`，**名单逐名相同**
    ⇒ 原文那句"同一提交两遍差 7 条"今天复现不出来（不能据此说不存在，只能说它不是这一版代码
    在默认通道上的稳定性质）；
    ② 原文那句"那五条没有一行为什么今天没跑"在**捕获这一族已经不成立**：
    runner 上它们确实 skip 了，而闸门列出了名字与原因
    （`TEXT_SIDE_NOT_RUN settings-shortcuts dark 侧栏列读到 0 个偏离像素（同帧内容区读到 0 个）`）；
    ③ 仍然成立的是反方向：**闸门只报它找到的 `*_NOT_RUN`，不报它没找到的那些** ——
    一条判据既没跑、也没打 `*_NOT_RUN`（整行缺席）时今天仍然没人红。
    这一格与 R85 给 `loops` 那一层修的正是同一件事（`LOOP_SILENT`），只是捕获这一族还没有那一格。
    ⇒ 待办从"给五条各打一行原因"改成"给闸门加'缺席就红'那一格"，交给 R87。

117. **骨架扫光的亮带是"每根条各扫各的"，不是"一块光穿过整组骨架"**（R82 看图看出 / 逐帧条带图 `r82_skeleton_sweep_strip.png`）：

    `SkeletonMotion.unitPoints(phase:)` 给的是 `UnitPoint`，而它被用在**每根条自己的**
    `LinearGradient` 上；`UnitPoint` 按被填充形状的边界归一化 ⇒ 同一相位下亮带在三根条上的
    绝对位置按 `barFractions = [0.42, 0.86, 0.64]` 各自放大，**不可能落在同一条竖线上**。
    机制这一步是推出来的（读代码即可，不依赖机器），看图与它一致。
    代价是可读性：系统的骨架与 GitHub 那类呼吸感都是"一个光源扫过整组"，
    而这里是三根条以三种速度各自亮一遍 —— 抬升只有 0.12，所以不刺眼，但**不原生**。
    下一轮先量再改：①逐帧量三根条上亮斑中心的 x（正对照：同一根条两个相位必须不同；
    反对照：三根条同一相位的中心必须**不**共线 —— 这条现在是本轮结论的载体）；
    ②若要改，把渐变抬到**容器**层（一个 `LinearGradient` 盖住整组，或按容器宽度换算 `unitPoints`），
    那会改到静置画面 ⇒ 124 张帧必须同提交 `frame_baseline.py update`。
    本轮不动产品：这是看图看出来的新缺陷，按"先 spike 再动仓库"的规矩排在下一次。

    → **R84 结案（改完，且改对了的地方有读数）**：整组一个形状（`SkeletonBarsShape`），
    渐变填在容器坐标系里 ⇒ 一条亮带横穿三根条。同帧内三根条亮斑的**绝对**中心
    169pt → **0pt**，**归一化** 0.005 → **0.450**（两把尺反向才是修对了），
    两份实现（判据 + `.scratch/motion-audit-2/r84_band_fanout.py`）同结论。
    判据 `testSkeletonSweepIsOneBand`：合成正对照两份必须分得开、真片行程 ≥20pt、
    处置由"同一把尺读高对比证人"签；真值表 13 格；牙 M451（把产品改回本轮之前的画法）CAUGHT。
    静置画面：**视觉上没变，但字节变了** —— 把 R83 与 R84 的同名帧解码到像素级比了一遍，
    差异只落在骨架那三根条的区域（y 40…83pt、x 从详情区左轴 20pt 起），最大通道差 5/255、
    98% 的差像素只差 1 级（抗锯齿边缘）⇒ 帧基线按哈希判，4 张同提交 update，
    update 之后复核 FRAME_BASELINE=FRAME_BASELINE_AGAINST=working FRAME_BASELINE_COMPARED=124 FRAME_BASELINE_CHANGED=0 FRAME_BASELINE_MISSING=0 FRAME_BASELINE_ADDED=0。原来那句"静置画面预计不变"要说得更准：不变的是**看得见的部分**。
    顺带一条没预料到的：coverage 那把尺的峰值 0.015 → 0.023（亮带变宽，每拍扫过的面积更大）。

119. **常驻循环那一族的 runner 处置会翻面：单次读数不配判产品红**（R84 开 / 与 114、118、113、110 同族）：

    同一份产品代码（R83 没动产品），同一类机器，两遍 CI 给了相反的处置：

    | run | 产品 coverage | 等节拍证人 coverage | 处置 |
    |---|---|---|---|
    | R82 38781113064 | 0.000（0/21 对） | 0.284 | `.notRunEnvironment` ⇒ 点名 `loop-clock-not-sustainable-at-product-rate` |
    | R83 38786182395 | 0.050（1/22 对） | 0.837 | `.productRed` ⇒ 红着说"产品这一份没在跑" |

    ⇒ 翻面的是**证人**那一边（0.284→0.837），而产品的读数两遍都是"几乎没拍到"。
    也就是说：在 ~110ms 的采样网格上，2.5 秒的一卷里"变化帧对落在哪几对"本身就不稳，
    拿它当"环境 vs 产品"的签字人，等于让同一件事在两轮里有两个罪名。
    要做的一小步：那一支的判定要**几遍读数**才配定罪（或换成不吃采样网格的量 —— 113 结案时
    换的 coverage 仍然是网格的函数），并把"几遍"写成数据而不是写成一次运气。
    R84 已经做掉的那半：新加的位置判据**不复用**这个处置，改由"同一把尺去读高对比证人"签
    （`bandAdjudication`），所以 119 不会把 R84 那条判据一起拖红。
    不许的处置：抬 `minCoverage` 到 runner 能过的数（110 禁止的同一件事）、

    R87 的处置改了，但这一条**不结案**：
    ① 新读数（第四遍）：coverage 0.032 / 行程 134pt / 可用帧 12 —— 同一卷上两把尺相反，
    而 coverage 那把把 main 判红了。⇒ 分布宽度现在只有 4 个点（runner 三遍 + 本机那一遍），
    "几遍才配定罪"仍然没写成数据；
    ② 本轮写进去的是**同一次运行内**的第二把尺（位置），不是跨遍状态 ——
    所以 119 的原文那一半（"要几遍读数才配定罪"）仍然没做，
    只是它最贵的那一种后果（单遍读数给产品定罪）被 D-145 挡住了。
    ③ 新形状带来的新问题另开 **BACKLOG 120**：位置判据今天仍被 `loopCapable` 关着，
    而它恰恰是唯一有资格说话的那把尺 —— 谁给谁签字，这件事本轮只改了一半。

    R89 **没有**拿到第六个数据点：R88 那道硬门红了之后 GitHub 把动效卷整个 skip 掉
    （见 D-147 第二条）。⇒ 分布宽度仍然停在 5 个点（0.522 / 0.842 / 0.032 / 0.690 + 本机那一遍），
    而 `contradicted-by-travel` 那一支至今零次在 runner 上触发。
    这一格按欠账记，不许被读成"runner 上一切正常"。

    R88 的第五个数据点（run 38818629423，同画法同机器类别）：coverage **0.690**、
    变化帧对 2/23、可用帧与行程见 Round 88 那节引的 CI 原文。
    ⇒ 四遍 runner：0.522 / 0.842 / 0.032 / 0.690 —— 跨度 0.81，两遍在地板上、两遍在地板下。
    ⇒ 更要紧的一条：**这一遍红消失不是 D-145 挡的**。coverage 自己回到地板上，
    `travel` 那一支没被触发，`LOOP_NOT_JUDGED=…contradicted-by-travel` 至今没在 runner 上出现过。
    所以 D-145 的证据现在只有"真值表 + 本机八刀"，runner 证据 = 0。
    这一条不结案的两个理由：① 分布宽度仍然只是 5 个点，没写成"几遍才配定罪"的判据；
    ② 新通道要等一次 coverage 真的掉到地板下的 run 才算被检验 —— 那是**记账**，不是猜测。
    把这朵红登记进 `suite_reds`（红要有成因，不是有名字就行）、或者反过来据此断言
    "产品的扫光在 runner 上确实没跑"（两遍读数互相矛盾，哪一遍都不能当结论）。

    R85 补一条**新的成因**（不改这一条的待办，只改归因顺序）：R84 把亮带改成整组一条之后，
    同一台 runner 上产品 coverage 从 0.050 跳到 **0.522**（时钟、节拍、抬升、声明时长一个都没动）
    ⇒ "读不到运动"除了"环境带不动"与"判据吃采样"，还有第三种可能：**这份画法在这台机器的
    像素门槛下本来就近乎不可见**。以后要动这一支的地板，先按 117 那次的账排除第三种。
    另外登记现在有了（`loops` 那一节，见 118 的结案），所以"整族没说一句话"这种坏法已经会红。

118. **一朵有名字的未覆盖，登记表里却没有它的位置：常驻循环那一族不进覆盖地板**（R83 开 / 与 100、114、92 同族）：

    `motion_floor_expectations.json` 按**四条场景臂**统计 judged/not-run，而骨架扫光不是场景臂 ——
    它是 `testSkeletonSweepActuallySweeps` 自己的一卷。于是 R83 之后这一位的状态是：
    本机判（coverage 0.95–1.00），runner 永远点名 `loop-clock-not-sustainable-at-product-rate`，
    而**覆盖地板既不数它也不许它缺席** —— 它红的时候闸门报红，它不红的时候没人知道它今天判没判。
    这正是 R46 建这张表要治的"掉了一臂没人报"，只是这一族不在表的形状里。
    R84 之后这一族里已经有**两格**读数（峰值地板的 `MOTION_SHIMMER_PEAK_NOT_JUDGED`、位置判据的 `MOTION_SHIMMER_BAND_NOT_JUDGED`），而它们都不在表的形状里。要做的一小步：给登记表加一节 `loops`（或把扫光当成一条虚拟臂），
    登记"必须判到 or 允许哪几种点名"，并让 `motion_floor_gate.py` 数它 ——
    判据是**两格**：点名时不红、缺席时红（与 R36 给捕获卷立的那条同形）。
    不许的处置：把扫光从判据里删掉来让表自洽；或者把 114 的点名当成"已经有人负责了"。

    → **R85 结案**：`motion_floor_expectations.json` 新增 `loops` 一节（两行登记），
    `motion_floor_gate.py` 新增 `loop_verdicts`，判据的两条出口各自打一行状态
    （`MOTION_SHIMMER_STATE` / `MOTION_SHIMMER_BAND_STATE`）。判据正是这里要的那两格：
    点名在登记之内 ⇒ 不红但打一行 `MOTION_FLOOR_LOOP_NOT_JUDGED=…`；状态行整行缺席 ⇒
    `MOTION_FLOOR_LOOP_SILENT=…` 红。两条状态行还各有一道源码级守卫**数次数**
    （`testTheLoopWitnessStillMirrorsTheProductLoop`）—— 因为"没人断言自己打过字"
    是这一层最容易无声失效的地方（U-174）。
    牙 M458–M464 共七刀，全部 CAUGHT（M461 / M462 第一版 ESCAPED，把守卫从"出现过"改成"两条出口各一次"之后抓到）。
    没做的那半：`must_judge` 仍然 false —— R84 的 runner 读数 0.522 只比地板 0.50 高 0.022，
    一次读数不配当硬门（R38），收紧要等几遍稳定读数，那一格交给 119。

113. **扫光那条"循环 vs 跳变"的判据在数帧对 —— 它和 110 是同一族病，只是换了个位点，而且是 R77 把轴修好之后才开始判的**（R81 开）：

    R80 的 CI（run 38766914234）里 `Motion coverage floor` 红了：
    `testSkeletonSweepActuallySweeps`：`("2") is less than ("3") — 只读到 2 对在变 ⇒ 那不是循环，是一次跳变`。
    三次 runner 读数并排（原文都来自 `gh api .../jobs/<id>/logs`）：
    | run | 读数 | 那一步的结论 |
    |---|---|---|
    | R73 38726991211 | `帧数=23 变化帧对=0 峰值=0.000 采样≈98ms` | **没判**（能力闸门 not-run） |
    | R75 38735395615 | `帧数=20 变化帧对=0 峰值=0.000 采样≈125ms` | **没判**（同上） |
    | R80 38766914234 | `帧数=23 变化帧对=2 峰值=0.015 采样≈115ms` | **第一次真判 ⇒ 红** |
    ⇒ 这朵红不是新坏的，是 **R77 那把并集轴的成果**：alpha 进判定之后 runner 第一次看得见这个渐变，
    免检的位点变成要检的位点。要修的是判据形状：**"数变化的帧对"跟着采样网格走**
    （115ms 的网格上，一条 1.2s 的循环最多被采到几对，全看相位落在哪儿）。
    该换成的形状（与 R47 那条"从帧数换成时长轴"同一句话）：
    ① 变化段的**时间跨度**（首尾时间差），或 ② **不连续段的段数 ≥2**（循环必然至少两次起伏，
    跳变只有一段）—— 两条都与采样密度无关。处置仍然按机器分开：2× 红、1× 点名，
    不许把 113 的地板抬到 runner 能过的数值（那是 110 被禁止的同一件事）。

    → **R82 结案（判据形状换了，但 runner 那一问另开 114）**：
    ①"数帧对"换成 **coverage** = 首尾两个还在变的帧对之间的时间 ÷ 整卷时长 ⇒ 与帧数无关，
      地板 0.5（本机三遍真值 **0.955 / 0.977 / 1.000**、一次跳变 **0.05** ⇒ 不在刀尖上）。      地板一个数没为哪台机器挪过。coverage 自己那三个数的差别来自"亮带首尾落在哪一帧"，      与采样密度无关 —— 后者才是这条判据换尺要消掉的东西，它已经由真值表第③格钉住。
    ②证人从一颗变**两颗**：R81 的 CI 上唯一那颗证人是 20Hz / 抬 0.45，而产品是 30Hz / 抬 0.12，
      所以它当时的 13 对在变**不足以**判产品红。新加的等节拍证人（`GradientTickView.productRate()`，
      四个数写死并由 `testTheLoopWitnessStillMirrorsTheProductLoop` 钉住仍等于产品）
      决定"产品红 vs 环境不行"，粗节拍那颗只守"证人坏没坏"（空支票守卫）。
    本机三卷（全量那一遍）：产品 coverage **1.000**（23/47 对在变、峰值 0.015）、
    等节拍证人 **1.000**（21/45、峰值 0.015）、粗节拍证人 **1.000**（41/45、峰值 0.026）
    ⇒ 参数对齐之后，"视图归谁"在本机上几乎不产生差别，所以 runner 那 2 对很可能大部分是**参数差**。
    这件事只能由 runner 那一遍回答 ⇒ **新开 114**；113 这条（判据形状）到此结清。

112. **读数通道在并发下会把两行缝成一行 —— 它会毁掉别人的读数，而闸门只看"这行在不在"**（R80 开）：

    R79 那一遍 CI 里，`QUICKPICK_FOCUS 暗 …` 整行不见了，它被缝进另一条判据的行：
    `MENUBAR_FITTING 声明宽=320 hosting.fittingSize=0.08px 宽=87.0pt(聚焦 12…98) 地板=40pt ⇒ 存在性尺说这一格画了东西…`
    —— 前半是 MENUBAR_FITTING、后半是我的焦点行，**MENUBAR_FITTING 自己的结论被吃掉**。
    `CaptureReadings.emit` 两条腿都不是原子的：`print(line)`（stdio 把内容与换行分两次 write）、
    文件通道的 `seekToEndOfFile()` + `write()`（两个线程可以 seek 到同一个偏移互相覆盖），
    而 `opened` 那个 `nonisolated(unsafe) static var` 本身就是竞争点（两个线程都可能走"整份重写"）。
    R64 量过"stdout 会整块丢"（BACKLOG 96），但**丢**与**缝进别人的行**是两种坏法：
    后者会让一条**本来绿的**判据的读数消失，而 `ci_capture_gate.py --readings` 只问"这行在不在文件里"，
    缝在中间的那半行它看不见。⇒ 本轮那把决定 109 的读数就是这么没的（我改用**红的行号**反证闸门开没开）。
    → **R81 结案（两条都做了，而且这一刀比预想的更狠）**：`emit` 的 stdout 那一条腿改成
    一次 `FileHandle.standardOutput.write(整行+换行)`（`print` 会把它拆成两次 write，那就是缝点）；
    文件那一条腿整段进 `NSLock`；`opened` 那个共享布尔换成**按 URL 记**的 `openedURLs`
    （共享布尔会让临时文件的第一行以为"已经开过卷"，于是去 open 一份不存在的文件）。
    新判据 `testConcurrentReadingsNeitherSpliceNorDropALine`：8 线程 × 60 条 900B 长行，
    三条断言各拦一种坏法（行数=整卷被抹、**行首与行尾的 (t,i) 必须相等**=缝行、
    每个 (t,i) 恰好一次=覆盖）。牙：M434/M435 把锁拿掉 ⇒ **3/3 遍 SIGSEGV**
    （两个线程同时改同一个 Set / FileHandle 不是"读数变脏"，是进程直接段错误）；
    M436 让"整份重写"每次都走 ⇒ 3/3 遍红。复现率 100%，这一格不是陪着绿的装饰。
    同轮抓到电池自己的分类器只认两种形状（U-151：崩溃被归成"编译没过"）。
    原来写的两条：①`emit` 的两条写各加一把锁、每行一次 write；②一条**有牙**的并发锤击判据
    （K 线程各写 M 条长行 ⇒ 行数对、每行以 marker 开头、能整行回读），
    并实测它的判别力（把锁去掉必须红；复现不出来就照实记"这条修没有红钉着"，不许写成钉住了）。

111. **焦点那条轴在 runner 上怎么赎回来**（R80 开 / 与 103 同一条路）：

    R80 把判据换成"搬动了多少 pt² 的墨 + 占比"，并给"看不见"分成两支（`行为不在这台机器上` /
    `这一格对这把尺失明`），两支都由证人臂决定、都由 `QUICKPICK_FOCUS_AXIS_NOT_RUN` 点名。
    换尺消掉的是**网格**那一半（合成夹具证明旧尺按 缩放² 变：2000 vs 8000 个像素）；
    消不掉的是**剩下那一半**：runner 那一遍的带墨面积按均值换算只有本机的 ~1/3，
    而聚焦搬动只有本机的 ~1/79 ⇒ 下一次 CI 的 `QUICKPICK_FOCUS_INK` 才知道是哪种。
    两条路的下一步不同：若是"行为不在" ⇒ 这条轴只能由真机判（批次 71.1 的非 Retina 外接屏那一问），
    判据保留 2× 红 + 1× 点名；若是"尺瞎" ⇒ 与 103 合并（换捕获对象，让窗口底真的进来）。
    不许的处置：把地板抬到 runner 能过的数值、或把两支合并成一支"反正都算没跑"。

110. **分辨率判据用的是"事件内最粗那一次采样"——一个单样本统计，它会把一臂在判到/判不到之间翻脸**（R78 开 / 与 77 路 b、47、38 同族；**R81 加了第二个实例：113**；**R82 交了第一实例的修法：闸门改吃事件内 P75**）：

    `detail-kind-change` 那一臂声明 160ms，判"这台机器看不看得见过程"的线是 `0.5×声明 = 80ms`。
    三遍本机读数（`.scratch/motion-audit-2/r78_motion_flip.log` 里三段并列）：
    | 遍 | 整卷中位 | **事件内最粗** | 变化段时长 | 结论 |
    |---|---|---|---|---|
    | R77 | 51ms | **61ms** | 172ms | 判到（judged=4/4） |
    | R78 第一遍 | 51ms | **81ms** | 200ms | `clock-coarse-in-window` ⇒ not-run |
    | R78 第二遍（单独跑） | 50ms | **81ms** | 201ms | 同上 |
    中位数两遍都是 50–51ms（稳定），翻脸的是**那一次最慢的抓帧**：61 → 81ms，
    正好跨过 80ms 那道线 ⇒ 一条臂的"判到 / 判不到"押在**单个样本**上。
    这与 R47 说的"帧数会翻脸"是同一句话的另一半：**max 也是单样本统计**。
    要做的：① 分辨率判据换成稳健量（事件内**中位**或 75 分位 + 一个"最粗不得超过中位 K 倍"的
    形状约束，K 由实测抖动带定），并把 81ms 那一次归因（R55 那套：抓帧成本 vs runloop 空等）；
    ② 改完必须能同时解释"runner 上 witness 33ms 可分数段=4"与本机这两遍；
    ③ 不许用"把 `clock-coarse-in-window` 登记进 detail-kind-change 的允许理由"当解药 ——
    那是把尺子的抖动登记成产品的性质（R75 那次放宽是有证人读数撑着的，这一条今天没有）。

109. **runner 上焦点那一格到底画没画 —— R78 那道存在性闸门够不够用，要等 CI 的读数回来**（R78 开）：

    R78 把焦点判据的像素两条改成"有墨才判"，并按机器分开处置（2× 没画 ⇒ 红，1× 没画 ⇒ 点名 not-run）。
    这道闸门的有效性完全押在一个还没测到的数上：**runner 那一遍的 `占位区有墨=…` 是多少**。
    · 若 ≈0 ⇒ 通道确实没画那串字，闸门按设计生效，`QUICKPICK_FOCUS_NOT_RUN` 就是这句的正式记账；
    · 若 ≥20 而两态差仍是 0 ⇒ 那两条红是**真的**（焦点在 runner 上确实没有后果），
      闸门不会替它遮丑，它会照旧红 —— 那时要查的是产品/通道，不是把地板抬高。
    两种结果都要在这一条下面记账，不许"CI 绿了"就算完。
    → **R79 走了一步（但答案仍未回来）**：R78 的 CI（run 38757049151）里那四条红**原样还在**
    ⇒ 计数型闸门在 runner 上没关（放大镜一个人就凑够 20 个像素，U-143）。
    R79 把闸门换成两根独立证人（包围盒宽度 ≥40pt + "只有占位字能待的那一块"有墨 ≥20，
    本机实测 86.5pt / 675 个像素，而图标自己只有 17.0pt），并加了一条"只框图标必须过不了闸门"的对照
    （D-137 / M419–M422）。**剩下的还是这一条原来的问**：R79 的 CI 把
    `文字独占区有墨=…` 与 `宽=…pt` 打回来才知道闸门开没开 ——
    若独占区非 0 而两态差仍是 0，那四条红就是真的，要查产品/通道，不许再抬地板。
    → **R80 答了一半（预登记的第二分支命中）**：R79 的 CI（run 38760347161）里
    `QUICKPICK_FOCUS_GATE 暗 … 占位整条宽=87.0pt … 闸门开`，而四条红原样在 1531/1539 ——
    **两档的闸门都开了**（闸门关的话红会落在 1523 那条 `XCTAssertLessThan(scale, 2)` 上，
    而不是落在像素那两条上；这一格是"用红的行号当读数"的记账，因为那一行本身被 112 缝掉了）。
    ⇒ 按预登记：那四条红是真的，本轮**没有抬地板**，做的是换尺
    （`≥500 个像素` ⇒ `≥40pt² 的墨 + ≥8% 占比`，地板从本机实测 98.7/113.3pt² 推，
    并加三条证人臂把"看不见"分成两支）+ D-138。
    **仍未答的是 runner 那一遍落在哪一支** ⇒ 剩下的部分挪到 111，本条留开。
    → **R81 结案（答案回来了，是决定性的那一支）**：R80 的 CI（run 38766914234）
    `QUICKPICK_FOCUS_AXIS_NOT_RUN=1 亮/暗` 两行都落在**第二支**：
    焦点搬动 **0.0pt²**（两档都是，一位小数都没有），而同一把尺在同一格里读出
    撤占位字 **88.9 / 112.3pt²**、打进字 **113.4 / 143.2pt²**、同态噪声 **0.0pt²**
    ⇒ **尺不瞎**，是这台机器的 AppKit 不为非 key 窗口调淡占位符。
    上一轮那句"最多 3/4 是网格"现在被量掉了：网格不成立，聚焦在 runner 上真的什么都没做。
    顺带一条新事实（记下来免得重查）：runner 那一格的墨只有本机的 **1/3**
    （88.9 vs 268.7）—— 与焦点无关，是 1× 上那串占位字本身画得更淡。
    剩下的赎回义务全在 111。

108. **反方向的盲区：只读 alpha 的两态尺，以及那一族只读亮度的单帧电平尺**（R77 开 / 与 107、88 同族）：

    R77 把"两态相减必须读两根轴"钉成守卫时，顺手把**反方向**也数了一遍：
    今天有 5 把尺子做两态减法却**只读 alpha** ——
    `UICaptureHarness.alphaBandDelta` / `alphaLiftProfile`（R67 为"那层灰在亮度上量不到"而故意写的），
    以及 R77 自己新建的三条报告尺（`alphaFraction`×2、`meanAlphaDelta`）。
    → **R78 更正（这一条开出去的时候就是错的）**：原本列在这里的 `paintedXRange`
    **全仓零调用点** —— 它不是"故意只读 alpha 的活尺"，是一把没人用的死尺，
    而 R77 的守卫把它收进名册、理由里还替它写了调用者。R78 删掉了它，
    并给守卫加了"每条登记必须有人调"那一格（U-137 / D-136）。
    同轮 R77 的扫描还漏了 `alphaBandDelta`：检测器认的是减法写法，而它写的是
    `abs(maxA - maxB) > floor` ⇒ 换成签名形状（参数表里两份位图）才抓得住（U-138）。
    这两条的代价是真的：一层**只改颜色、不改透明度**的效果（例如把墨从灰改成蓝、
    或 R52 那一族色相档）会被它们读成"没变"，而它们的调用点正在判"这层灰画没画出来"。
    要做的：① 给这两把尺同形状的第二个数（亮度那一根的变化量），先把"这一档只在 alpha 上"
    变成读数而不是注释；② 判一次"这两个调用点的结论有没有落在盲区里"
    —— 方法与 R77 对亮度轴做的完全一样；③ 顺带把 `meanLevel` / `meanLuma` / `inkContrast`
    那一族**单帧电平尺**列进同一张表（它们不是两态尺，守卫故意不管，但同一族盲区在这里）。



    浮层搜索框聚焦时那一串占位字退后 —— 框内 1797 个像素在动，可**亮度轴只读 -0.66/255**。
    本轮抓出来纯属运气：`changedPixelCount` 恰好把 alpha 合成进来了，
    而我另外那批"说明文字/图例/相邻档"的判据走的是 `meanLuminance` 与对比度轴
    （R21、R27、R35 那一族）。⇒ 任何"画在半透明层上、RGB 不变只变 alpha"的效果
    （占位符退后、禁用态、部分 `.opacity` 过渡、材质层）都可能**在产物里真的变了而所有判据读不出**。
    要做的：给捕获卷加一条**轴对照**读数 —— 同一块矩形同时打
    `亮度差` 与 `alpha 差`（本轮的 `QUICKPICK_FOCUS` 行就是这个形状），
    并加一条守卫：任何"两态相减"的判据必须显式声明它读哪根轴，
    只读亮度而两态差主要在 alpha 的那一族 ⇒ 要么补 alpha 轴，要么点名"这一轴今天没判"
    （`FRAME_*_NOT_RUN` 那一族已经有先例）。
    → **R77 结案（三条都做了，而"今天有多少东西落在盲区里"是被量的，不是被假设的）**：
    ① **轴对照读数进卷**：`MOTION_AXIS <臂> 帧对=… 亮度峰值=… alpha峰值=… 并集峰值=… 仅alpha在动=K/N`
       打在**所有能力闸门之前**（R53 那一课），`MOTION_BLANK` 同形状，
       按压那一族是 `PRESS_AXIS … 亮度差=/alpha差=/并集差=`，梯子是 `FILL_STEP … alpha差=…/255`。
    ② **并集成为语义**：`axisPair` 一次算三根轴，`changedFraction`（三处）与 `bandHeadTailDiff`
       全部改成"任一轴过地板就算变"（D-135）。亮度那一根仍然可得（`axisPair.rgb`），
       所以旧读数没被作废，只是不再是做结论的那个数。
    ③ **守卫 + 双向名册**：`testEveryTwoStateRulerReadsBothAxes` 扫四份文件，
       只读亮度 3 条、只读 alpha 5 条，每条带 ≥60 字理由，`changedFraction`/`axisPair` 不许进名册；
       两个正对照（读了不用 / 注释里提一句）+ 两个元层变异（M411/M412）。
    今天的量出来的答案：**四臂 + 空白全部 `仅alpha在动=0/N`** ⇒ 没有一条旧结论被翻掉
    （`judged=4/4`、`MOTION_SUMMARY` 与 R75 同判）；而 alpha 峰值本身与亮度同量级（0.25 vs 0.28）
    ⇒ 这条通道确实带透明度，"实心"只是落盘之后的性质（写出去的 PNG alpha 全 255）。
    反方向的代价没消失，只是被点名了 ⇒ 开 **108**。

106. **重排那两条读数都来自手工语料，而真实的那一个就躺在盘上**（R74 开 / 与 U-128 同族）：

    `OVERLAY_HOVER_REFLOW` 那两行分别是"帧夹具 5 条"与"嵌套前缀 8 条"，
    两个形状都是**我挑的** —— 一个证明会重排、一个证明不会。
    这正是 U-128 说的那种错的下一步：**判据已经诚实了，语料的选择权还在我手上**。
    本机存档里有 **105 条真实记录**（R71 装包时 `INSTALL_ENTRIES=105`）。
    要做的：从真存档（或它的脱敏副本）量"每多打一个字，候选集变小的比例"，
    只打**计数与比例**、不打文案（帧与日志都不许出现用户内容 —— R18 那条"帧不许跟着桌面变"的近亲）。
    两种结果都收，而且都改东西：真实语料若接近 1/6（一打就收敛到一条），
    那"不加淡入"的理由要换成**系统同形**（AppKit 的行高亮本来就是即时描色）而不是重排频率；
    若接近 7/8，本轮那条按语料限定的结论就升格成全称，`U-115` 的措辞也要跟着改。

100. **动效那一步在 runner 上连着两遍是红的，而整份报表里没有一条红有名字**（R65 读 CI 时撞到 / 与 49、92 同族）：

    `motion suite exit:` —— run 38687419144（R63 台账）= **0**，run 38693365411（R64）= **1**，
    run 38696695788（R65）= **1**。红的是同一条自校验：
    `MotionFilmstripTests testListRowsDoNotAnimateAndNothingClaimsTheyDo` 断言
    `XCTAssertGreaterThan failed: ("0.0253") is not greater than ("0.15")`，消息写着
    "连横幅淡入都读不出残余 ⇒ 这把尺子在这个维度上没有分辨率，上面那条绿是空的"。
    也就是说**判据自己做对了**（它拒绝让一条没有分辨率的绿站着），但这一步是 report-only，
    而 `motion_floor_gate.py` 的 `MOTION_FLOOR_REDS` 数的是**它自己那四臂的结论**
    （源码里 `reds += 1 if is_red`，`is_red` 来自臂的判定），**不看测试有没有失败**
    ⇒ 两遍都是 `MOTION_FLOOR_OK=4/4 REDS=0`，而作业里躺着一个 exit 1。
    更坏的是 R64 那一遍：`motion suite exit: 1` 在，而那条 `error: -[…]` 断言行
    **整条从 stdout 里没了**（逐字 `grep -c` = 0）—— 同一台机器、同一个通道问题，
    这一遍（R65）它才恰好活着被我读到。⇒ **红必须有名字**这条规矩（R36）现在只覆盖捕获那一步。
    下一轮做法（R66）：① 照 R36 的形状给动效那一步加一道硬门，扫 `error: -[类 方法]` 与
    `Test Case … failed`，未登记的即红；② 这条自校验在 runner 上的正确形态不是红，
    是**登记**：把"这一维度在这台机器上没有分辨率"打成 `MOTION_RESOLUTION_NOT_RUN`（带读数与原因），
    并保留"本机必须仍然判红"的那一臂 —— 否则登记会变成新的免检牌（BACKLOG 49 的原话）。
    → **R66 结案（两条都做了，但 ② 的形态被一次实测改掉）**。
    **先把"到底是机器还是产品"这件事量清楚**，再谈登记：本轮把同一份判据在本机跑了一遍，
    并顺手量了 runner 那一步留下的另外两条读数 ——
    | 读数 | 本机（R66） | runner（run 38696695788） |
    |---|---|---|
    | `MOTION_CUT_CONTROL notice-banner` 落定残余 | **0.719 / 0.974**（同码两遍） | **0.025** |
    | 同一条淡入的采样间隔 | ≈10ms | ≈21ms |
    | `MOTION_SETTLE banner-in` 到位帧 ⇒ 实测落定 | 16 帧 ⇒ ≈160ms | 4 帧 ⇒ **≈76ms** |
    | 声明时长（`MotionCatalog.bannerIn`） | 150ms | 150ms |
    两台机器的采样只差 2 倍（21ms 采一条 150ms 的淡，本该有 ≈7 级可分），
    而残余差 **29 倍**、实测落定差一倍 ⇒ "采样太粗"解释不了它。
    于是原来的 ② 不能照写：把 `落定残余 <= 0.15` 直接登记成"这台机器没分辨率"，
    等于让**被告自己作证** —— 哪天横幅的淡入真的退化成跳变，那条登记会替它说话。
    **改法：请一个与被告无关、机制相同的证人**（`FadeClockProbe`）：
    测试自己的夹具（白底 + 盖满视口的黑块，`if shown { Rectangle().transition(.opacity) }`
    配 `withAnimation(.easeInOut(duration: 0.15))`，150ms 写在**测试里**而不是读 `MotionCatalog` ——
    读产品的话，哪天有人把 `bannerIn` 改成 0.01s，证人跟着变短，就永远"能分辨"了），
    逐帧读**平均亮度电平**（不是帧间差：差没有极性，数不出"中间态"），
    判定三档：跨度 < 0.05 ⇒ 证人自己坏了（**判红**，不 skip）；
    中间态 ≥ 2 帧 ⇒ 这台机器能分辨 ⇒ 产品读不出就是**红**；
    中间态 < 2 帧而跨度够 ⇒ 环境看不见 ⇒ `MOTION_NOT_RUN=fade-clock-snaps-here`（带读数）+ skip。
    本机实测：`MOTION_FADE_CLOCK 声明=150ms 跨度=1.000 中间态帧数=10 帧数=87 采样≈21ms 判定=能分辨`
    —— 注意**证人在 21ms 的采样下给出了 10 级**，与 runner 那 21ms 同量级，
    所以"runner 读不出"如果是同一件事造成的，下一次 CI 会把它登记成 `fade-clock-snaps-here`；
    如果不是，那一步会红，而红现在**有名字**了。
    **① 硬门**：`motion_floor_gate.py` 多了 `suite_verdicts()` 一层 ——
    扫 `Test Case '-[类 方法]' failed` 与 `error: -[类 方法] : <XCTAssert 原文>`，
    外加 `Executed N tests, with … K failures` 那个汇总数：
    未登记的红 ⇒ `MOTION_FLOOR_SUITE_RED=n`（红，且把名字与断言原文一起打出来）；
    汇总说红了而日志里名字不够 ⇒ `MOTION_FLOOR_SUITE_NAMELESS_RED=n`（红 —— 这才是"红必须有名字"
    本身被钉住，R64 那条"stdout 会成块丢"随时能把名字吞掉）；
    登记过的红 ⇒ 不挡发布但打 `MOTION_FLOOR_REGISTERED_REDS=n`（靠登记过的绿要数得出来）；
    登记条目这次没复现 ⇒ `MOTION_FLOOR_SUITE_STALE`（不红，提醒删）。
    这一层排在 `verdicts()` 里两处提前 return **之前** —— 判据自己崩的时候
    常常既没结论行又红，旧形状会把红一起吃掉（`testSuiteRedSurvivesTheMissingResolveLine` 钉住）。
    判据的判别力：正对照是**逐字从 runner 日志抄来的那一卷**
    （`scripts/tests/fixtures/r66_motion_runner_red.log`：run 38696695788 那一步的
    `---- 红的理由 ----` 小节把它原样打了出来），它的关键性质是**臂一级全在登记之内**
    （`judged=4/4 not-run=-`）而这一卷红着 ⇒ `testArmLevelRulesAloneWouldHavePassedIt`
    把用例级判据摘掉后必须全绿，那就是"两次 exit 1 绿过去"的最小复现。
    登记表 `suite_reds` 今天**故意是空的**（`testRegistryIsEmptyOnPurposeAndEntriesNeedProvenance`）：
    ② 的成因已经量清，正确处置是修判据而不是登记。
    变异 M350–M361 十二刀**全部被抓**（`.scratch/motion-audit-2/r66_mutation_battery.log`），
    其中 M356 就是那张新免检牌（证人能分辨时把"产品跳变"改成 skip）——
    它必须由 `testTheControlJudgmentIsATruthTable` 抓到，而这要求那段决定是**纯函数**：
    原来它长在只有走进 `residual <= floor` 才会执行的分支里，本机永远进不去
    （残余 0.719/0.974），于是分支里三条判定在本机一条都没被执行过 ⇒ 抽成
    `controlJudgment(residual:clock:)` + 六格真值表，红/绿/skip 的分界不再依赖某台机器恰好会 snap。
    M354 是本轮**真踩过**的坑：`SUMMARY_FAILURES` 第一版漏了 `with `，于是恒读成 0，
    而 NAMELESS 那一格恰好因为"名字数与 0 一致"不红 —— 三条用例一起红才发现，
    补了 `testSummaryFailureLineIsParsedInBothShapes`（两种形状 + 多行取最大）。

99. **浮层那一行的字号是硬编码的 13pt，而令牌 `VisualFont.row` 是 12pt**（R65 改那一列时顺手读到的）：
    `QuickPickController` 建 cell 时写 `text.font = .systemFont(ofSize: 13)`，
    而侧栏的行是 `.font(.system(size: VisualFont.row))` = 12。
    本轮（R65）**判为不动，但这个判断本身还没量过**：我猜的理由是"两个表面的行高不同
    （浮层 rowHeight 34pt；侧栏行高本轮没量）所以字号跟着走是常态"，
    这是一条**没读数的解释**，不能当结论用（U-95 那一族）。
    要做的：① 量侧栏一行的实际高度与浮层一行的实际高度（帧上都能量，同一把尺）；
    ② 若两者行高差 < 4pt，那 1pt 的字号差就是"两个列表说两套话"，应统一成 `VisualFont.row`；
    ③ 若行高差足够大，就把"为什么浮层用 13"写进代码注释并加一条守卫：
       这一卷里 `.systemFont(ofSize:` 后面出现**字面量**就红（现在 R15 那条"令牌必须进梯子"只管 SwiftUI 侧）。
    → **R71 结案（三条都做了，但①的答案把②的前提打掉了）**：
    ① 同一把尺（帧上按亮度找墨段、2× 换算）量到的**行距**：浮层 33–35pt（单行）
       vs 侧栏 38–47pt（双行：标题 + meta）⇒ 两者不可比，"行高差 < 4pt 就统一"这条规则**用不上**。
       真正决定的是"同一条记录的标题"这一件事：侧栏 / 行视图 / 搜索建议五处全是 `VisualFont.row`(12)，
       浮层是唯一那一处 13 ⇒ 换 `VisualFont.row`。搜索框那处原来是 14，而主窗口那颗是 `body`(13)
       ⇒ 同一个控件在两个表面响一档，也换成 `body`。
    ② 换完的读数：`QUICKPICK_TYPE 行数=5 行标签字号=[12,12,12,12,12] 期望=12 搜索框字号=13 期望=13`；
       帧上墨高 12.0/12.0/11.5/12.0pt ⇒ 11.0/11.5/10.5/11.5pt（与侧栏那 10.5–12.5pt 同带），
       而且**同一行截断点右移了一个词**（"包含足够长度…" ⇒ "包含足够长度以便…"）—— 小一档换来更多信息。
    ③ 守卫按原话加了，而且加在 R15 那条的家里（`testTextSizesComeFromTheScale`）：
       它原来**只扫 SwiftUI 那一半**（`.font(.system(size:`、只在 `Views/`），
       现在两半都扫（`.systemFont(ofSize:` + `Managers/`），并带一条正对照喂假源码。
       顺带把 `MenuBarController` 四处与 `ChineseTextContextMenu` 一处的字面量换成同值令牌
       （11⇒`meta`、13⇒`body`，**数值一个没动** ⇒ 那几张帧 `CHANGED=0` 就是这条的证明）。

97. **浮层行的标签没有共同左轴：纯文本行 35.0pt，文件行 56.5pt**（R64 逐像素量 `quickpick-list-420x300-light.png`）：
    同一个 `NSTableView` 里，带图标的行是"图标 36.0–50.0pt + 标签从 56.5pt 起"，
    纯文本行没有图标列，标签直接从 34.5–35.0pt 起 ⇒ 五行里两种左轴，差 **22pt**，
    在 420pt 宽的面板上肉眼可读（第 1、2、5 行与第 3、4 行错开）。
    同一张帧上的**好消息**（记下来免得下轮重查）：选中不产生位移
    （选中行标签 34.5pt vs 未选中 35.0pt，0.5pt 是字形边距），
    选中药丸 y=47–81pt（正好一行高）、亮档 Δ亮度 35.3 / 暗档 40.2 ⇒ 选中态机器可见；
    空态那句在列表槽里居中，中心 209.25pt vs 面板中心 210pt（差 0.75pt）。
    要做的是二选一：① 给纯文本行也放一个类型符号（与主列表的语言一致，主列表每行都有类型位）；
    ② 保留"只有文件行有图标"，但给标签统一加一条左轴约束。
    与 **94 同一族**（94 说的是那个图标本身是 📄 emoji 还是 SF Symbol）——
    先定图标语言，再定左轴，否则两遍都要改。本轮（R64）判为**不动产品**：
    那一轮的文件预算在通道上，而且 ①/② 的选择取决于 94 的结论。
    → **R65 结案（选 ①，与 94 一起做）**：每一行都有一枚 16pt 的类型符号，标签共享一条左轴。
    同一把尺、同一套坐标（帧上按 2× 换算回 pt）：
    | | 改前（R64 量的） | 改后（R65 量的） |
    |---|---|---|
    | 纯文本行标签左沿 | **34.5–35.0pt** | 56.0–57.0pt |
    | 文件行标签左沿 | **56.5–57.5pt** | 56.0–57.0pt |
    | 两种左轴的差 | **22pt** | 帧上 1.0pt（字形边距），布局上 **0.00pt** |
    布局侧的硬证据是判据直接读的：`QUICKPICK_ROW_AXIS rows=5 取到标签=5 取到图标=5 无图行=0
    标签左轴散布=0.00pt 图标列散布=0.00pt 标签 minX=42.0,42.0,42.0,42.0,42.0`（表格坐标）。
    帧上那 1pt 的差是"图"与"合"的左侧空距不同，不是布局 —— 所以判据钉的是视图的 minX，
    不是像素的第一列墨（后者会把字形边距当成缺陷，R37 那一族）。

120. **位置判据今天仍被 coverage 关着，而它恰恰是唯一有资格签字的那把尺**（R87 开 / 与 119、110、104 同族）：

    `bandAdjudication(..., loopCapable:)` 的 `loopCapable` 传的是 `shimmerDisposition() == .ok` ——
    也就是"coverage 判到绿，位置判据才有资格判"。R84 立这条时是对的（那时 coverage 是唯一有处置的运动尺），
    但 R87 之后它自己变成了矛盾的来源：run 38811457259 上 coverage 读 0.032 ⇒ 处置不是 ok ⇒
    位置判据打的是 `判定=notRunEnvironment 原因=loop-not-capable`，
    而它**手上那份读数**是"可用帧 12、行程 134pt、整组一条带"——今天全卷最可信的一条。
    ⇒ 要判断的是：位置那一族该不该由**它自己的证人**（粗节拍那颗，同一把尺）签字，
    不再看 coverage 的脸色？如果该，`loopCapable` 这个入参就该换成"位置尺自己有没有读数"；
    如果不该（怕位置判据在 coverage 不可用时误判产品），那就要写出**它误判的具体形状**并给它一格真值表。
    本轮没做的原因：D-145 已经改了定罪权，一次改两处会分不清是哪一处让红消失的（R58 那一课）。
    不许的处置：把两件事捆成一次提交；或者反过来把 coverage 判据删掉让位置尺独判 ——
    位置尺看不见"根本没在扫"（一根钉在原地的亮带与一卷空白在它那里长得一样）。

121. **脚本自测那一步的地板是静态数，而"少一层目录"的 discovery 会打印 `Ran 0 tests` + `OK`**（R87 开 / 与 110、116、118 同族）：

    本轮照抄台账里那行命令（`python3 -m unittest discover -s scripts`，我 R80 起连续八轮把它抄漏了
    `/tests` 那一层）跑了一遍：**`Ran 0 tests in 0.000s` / `OK` / 退出码 0**。
    八轮的验证块里写的是 `Ran 140–155 tests` ⇒ 真正跑的一定是另一条命令（`verify_r8*.sh` 与 CI 都是
    `-s scripts/tests`），错的是台账那一格，已逐行改对（八处）。

    ⇒ 但这一格值一条 backlog：CI 的 `Release script tests` 只有 `grep -q "OK"` 加
    `test "$executed" -ge 48`。0 会红（地板挡住了最坏那一格），**可如果 discovery 只收到一半文件，
    `Ran 78 / OK` 照样绿** —— 而这正是"脚本层判据整块没跑"的形状（R46 那一条在 Swift 卷上已经修过一次）。
    要的判断：这条地板该不该改成**登记的单调量**（像 `HistoryStore` 那两个上限一样只准升不准降，
    升的时候必须留 run 号 —— 与 R50/D-? 那条"放宽必须留 run 号"同形）？
    还是维持静态数、把"条数对不对"交给人读台账那一格？
    本轮没做的理由：这是**工具层**的一条门，跟 D-145 那次定罪权搬迁无关，捆在一起会让下一轮读不出
    是哪一处让红消失（R58 那一课）。
    不许的处置：把地板抬到 155 了事 —— 那只是把静态数换个值，下次少收一半仍然看不见"少收了什么"；
    要的是**点名少了哪几个文件/哪几条**（`--readings` 那一族已经证明"点名"比"计数"有用）。

122. **在屏那一卷需要"每条判据自己写一行读数"的通道；以及那颗等节拍证人配不配签红**（R88 开 / 与 93、96、110、112 同族）：

    本轮把"日志为什么是空的"分开了（D-146），但**没解决"跑到哪一条"**：
    stdout 会被 SIGKILL 整块带走，而产物通道只覆盖 11 条里的 3 条（focus-chain 两张、reveal 两张），
    字母序第一条不写盘 ⇒ "没帧"证不了任何事。⇒ 要的是每条在屏判据在**自己**开头写一行
    （文件通道，R56 给动效卷用过、R81 钉过原子性的那个形状），CI 读它而不是读 stdout。
    同一轮里第二件事：`MOTION_SHIMMER_WITNESS 等节拍证人` 在 run 38818629423 上读
    **0.043**（"只动了一下"），而产品同遍读 0.690。它三遍 runner 的分布
    （0.671 / 1.000 / 0.043）比产品自己还宽。今天没造成错判（产品在动⇒直接判 ok，证人没被问），
    但 D-145 的红路正是"产品说没在动 + 证人说在动 ⇒ 红" ——
    这颗证人有约 1/3 的概率在那一格先说"没在动"，把假红变成假绿的对立面。
    ⇒ 要判断的是：证人该不该也吃 `travel` 那一类**位置**证据？还是它的地板要按"它自己几遍的分布"重定？
    不许的处置：把它的地板抬到 0.043 之上了事（110 禁止的同一件事）；
    或者拿"今天没造成错判"当它尽职的证据。

    R89 定了做法但**没做**（一次只改一处）：
    ① 通道不用新造 —— `UIInteractionProbeTests` 文件级已有 `emit()`，写的是
      `FileHandle.standardError`（直接 `write(2)`，不经 stdio 块缓冲），而 CI 那一步是
      `swift test … > /tmp/ui.log 2>&1` ⇒ 这条腿本来就活得过 SIGKILL；
    ② 心跳挂在 `setUpWithError()`：本机孤立包实测 `self.description` == `-[类名 用例名]`，
      与 XCTest 自己那行 `Test Case '-[…]' started.` **同一个名字空间** ⇒ `ui_probe_report.py`
      现有的 `CASE` 正则可以直接用；`invocation` 那条要 `NSStringFromSelector(inv.selector)`
      且带 `AndReturnError:` 后缀，不许拿它当用例名；
    ③ 取不到名字时心跳要自己说"取不到"，不许静默写一条没名字的行；
    ④ 整行一次 write（R81 那一课：内容与换行分两次写会被并发缝在一起）。

    → **R90 结案**，但**通道与 R89 定的不一样**：先量再动手，结果量掉了自己写的前提 ——
    `swift test` 下 fd1/fd2 都指向 SwiftPM 驱动的管道，驱动被 SIGKILL 时 stdout 与 stderr
    **一起丢**（`spike_r90_channel_diag.sh`），所以"stderr 那条腿活得过 SIGKILL"是假的。
    实际落地：心跳写**自己 open 的文件**（`CLIPBOARD_HISTORY_PROBE_PULSE` → `probe-pulse.log`，
    复用 `CaptureReadings` 的锁与整行原子写），`ui_probe_report.py --pulse` 把它与 stdout
    的 started/concluded 做**双通道对照**：一致才点名（`UI_PROBE_CHANNELS_AGREE=1`），
    不一致就退回"只报观察不报成因"（`UI_PROBE_CHANNELS_CONTRADICT`）。
    正对照用的是产品写出的原件（`scripts/tests/fixtures/r90_pulse_real.log`），不是我造的字符串。
    牙 M497–M504 共八刀全 CAUGHT；其中「心跳改成 print（走 stdout ⇒ 驱动那层的缓冲，被 kill -9 就没了）」与「`PULSE_EMPTY` 那一格从红改成绿（通道坏了却宣布有名字）」两刀管的就是通道本身
    （一刀把心跳退回 print ⇒ 它又变成会被驱动吞掉的装饰；一刀把 `PULSE_EMPTY` 改成绿 ⇒
    通道坏了却宣布"有名字"）。

123. **（R88 开 → R88 当场撤回）设置侧栏暗档那五行"黑字黑底"不是新发现，是 D-090 / D-094 / R39 已经量过并守卫住的通道盲区**：

    我开了这条的依据：`settings-data-720x540-dark.png` 侧栏未选中五行标签峰值 30、背景 28（对比度 ≈1.07:1），
    而主窗口侧栏同一量法峰=224。查下去之后**这条不成立为"未定"**：
      * D-090（R30）已经量到那一列的生效外观是 `NSAppearanceNameVibrantDark`，
        并写明 vibrant 文字极性是故意反的、`cacheDisplay` 不做合成那一步 ⇒ 拍到的是合成前像素；
      * D-094（R35）由此立了"探针必须有颜色域资格"，判据 `testProbesDoNotSitOnVibrantColumns`；
      * R39 的注释里已经有一张同样的裁剪图，并且逐字写着：暗档侧栏五枚标签黑字黑底看不见、
        选中行白字蓝底（强调色走固定色不受极性影响）、图标看得见 —— 与我今天看到的**一模一样**；
      * `darkSidebarTextBlindSpots` 名单里就有 `settings-data`，而且这个名单由 vibrant 前提现推
        （`testDarkSettingsSidebarTextIsACountedBlindSpot`），手改不改得绿。
    ⇒ 撤回，不占用下一轮。真正剩下的开放项还是 D-090 指的那两个：**人工批次 37.1 / 37.2（真机）**。

    ⇒ 但这一格留着的价值是这条规矩：**开单前先在决定台账里查重**（搜"机制名 + 表面名"，
    这次该搜 `vibrant` 与 `侧栏`）。我这轮是先看了图、先量了数、先写了 123，才去读 D-090 ——
    顺序反了。量到的东西是真的，"新"不是。
124. **装机落后于产品：R84 改了产品文件却没换装，而这条规矩没有守卫**（R89 开 / 与 96、121 同族）：

    做最终报告收口审计时对了一遍台账才看见这件事 —— `r89_install_lag_audit.py` 逐段读
    `## Round N` 里自报的"N 个产品文件"与该段有没有换装证据（`INSTALL_RESULT=ok` /
    `INSTALL_SHA_MATCH=1`）或"不换装+理由"，读数：

    ```
    INSTALL_LAG_ROUNDS total=88 有产品数=9 无该行(老轮次,不判)=79
    INSTALL_LAG_OK=8
    INSTALL_LAG_RED=Round 84 自报产品文件=1 而段内既无换装记录、也无"不换装+理由
    ```

    ⇒ R84（亮带那一族的产品改动）之后 R85–R89 全是 0 个产品文件 ⇒ **本机装的还是 R84 之前的包**，
    而这五轮的帧、判据、账本描述的都是 R84 之后的产品。"交付默认自己构建换装"这条规矩立过，
    但它只能被"想起来"、不能被"跑出来" —— 这就是它漏掉一整轮的原因（与 121 同一族：
    规矩没有变成会红的东西，就等于没有）。
    ⇒ 两步修法：① 本轮把当前树构建 + 换装 + 记录（做完在本条里结案"落后已补"）；
    ② 把这支审计升成判据（进 `scripts/` + 自测 + CI 报告型一步），并让每轮验证摘要里
    "自报产品数 > 0"与"换装证据"绑成一条会红的话。
    ⇒ 老实记一格：79 个老轮次没有"N 个产品文件"那一行（那个自报格式是 R66 之后才有的）⇒
    审计**判不了它们**，这一格不许被回推成"那 79 轮没落后"。
    ⇒ **第①步本轮已结案（落后已补）**：`install_local.sh --yes --label r89-overlay` →
    `INSTALL_RESULT=ok`，旧包 sha `4aa88f2ef5c3e758…` 换成新包 `7ef8c6eca171adbd…`（版本号都是 1.4.8，
    所以"版本号相同"完全不能当"包相同"的证据），`INSTALL_SHA_MATCH=1`、`INSTALL_RUNNING_PID=34203`
    （启动晚于安装、exe 路径逐字对上 `/Applications/时间剪史.app`）、存档 105→105、`SMOKE_OK=1`。
    第②步（升成 `scripts/` 里的判据 + 自测 + CI 报告型一步）仍然开着，交下一轮。

    R90 **没做第②步**：本轮非台账文件已到 7 个（约定 ≤4），再叠一步会让"哪一处让 CI 变了"分不清
    （见 D-148 与本轮正文 §5）。这条欠账继续挂着，不许被读成"已经升成判据了"。

    R91 仍**没做**第②步（本轮非台账文件 3 个：探针卷、守卫、覆盖登记 —— 再加一步就分不清
    是哪一处让 CI 变了）。欠账继续挂着。
125. **拖选探针挂在 CoreDrag 的模态循环里：现在能点名，还没修**（R90 开 / 与 92、93、122 同族）：

    R90 把 122 做完之后，93 第一次有了名字 —— 心跳点名
    `testDragSelectExpandsSelectionInsideTheRealList`，`sample` 的栈独立同意机制：
    `NSCoreDragManager _dragUntilMouseUp → CoreDragStartDraggingAsync →
    _BlockUntilNextEventMatchingListInMode → mach_msg`（0% CPU 在睡）。
    ⇒ 这是**合成 mouseDown 之后系统进了拖拽模态循环，而合成的 mouseUp 永远送不进去**。
    本机可复现（不是 runner 专属），所以它不是"CI 慢"，是这条探针的结构问题。
    ⇒ 两条路，都要先 spike 再动仓库：
    ① 给这条探针自己加一层超时：到点就 `NSApp.stopModal`/直接结束拖拽会话，并**主动打一行
    "我掐掉了自己"** —— 宁可少一条判据，也不要一条会挂死的判据；
    ② 绕开 `sendEvent`：直接调手势/选择逻辑（`List` 的 selection 变更那条），
    代价是它不再经过真实事件路径 ⇒ 判据资格要重谈（与 104"证人必须与判据同一颗尺子"同族）。
    ⇒ 不许的处置：把这条探针删掉（那是删测试绕开检查）；或者把它标成"已知会挂"就完事 ——
    看门狗现在能收尸、报告器能点名，但**收尸不等于修好**。

    → **R91 结案**，但**两条路都没走**（都不需要走）：先量再选路，结果量到的是
    "这条路本身在进程内做不到"。三遍本机复现（180 秒被掐、心跳 2、有结论 0）+ `sample` 的栈：
    `sendEvent → NSCoreDragManager _tryCatchDragUntilMouseUp → CoreDragStartDraggingAsync →
    _BlockUntilNextEventMatchingListInMode` —— CoreDrag 等的是窗口服务器的真 mouseUp，
    而探针的 mouseUp 排在 `sendEvent` 下游。⇒ 撤掉合成拖拽（连 `MouseSynthesizer.drag` 一起），
    限制打成 `DRAG-LIMIT` 读数，机制级守卫 `testProbeSuiteNeverSynthesizesADragSession` 钉住。
    ⇒ 另有一条：这条探针测的手势 D-034 就决定不做，而 D-034 写着"探针已删除"——**那句是假的**
    （`git log --all -S` 只有增、没有删）。⇒ 见 U-206。
126. **离屏捕获对侧栏语义色图标的解析在同一列里不一致；暗档侧栏逐行读数只有一份**（R90 开 / 与 96、116、123 同族）：

    R90 重做设置「统计」这一屏的看图时，第一次用**双边**尺量到两件事：

    ```
    亮档侧栏：标签 最远 251/255（六行都可读）
    亮档图标：快捷键/通用/隐私/数据 ≥8/255 的像素 **0 颗**，最远 4/255，极值色号纯白 (255,255,255)
              推荐 ≥40 的 143 颗，极值纯黑 (0,0,0)      ← 同一列里两种解析结果
    ```

    ⇒ 与 `SettingsView.swift:808–815` 里 R30 记下的那条（`OffscreenSymbolInkProbeTests`
    量到未选中行墨水比 0.0000，换成固定 `Color.black` 能到 0.175–0.402）是**同一族**：
    离屏管线解析语义色。**但不是同一份读数**：R30 那份是"未选中四行全 0"，
    今天这张帧是"四枚 0、`wand.and.stars` 那一枚纯黑" ⇒ 解析结果取决于**符号本身**。
    ⇒ 三步：① **同一屏拿真机窗口截图（`screencapture`）与离屏帧对一次** ——
    这件事这台机器就能做，以前被挂在"等用户真机"那一栏是记账错误；
    ② 若真机可见 ⇒ 把"离屏帧不判图标可辨性"写成一格**声明**（与 `menuSurfaceReplicaFixtures` 同形状），
    而不是每次看图时靠人记得；③ 若真机也不可见 ⇒ 那是产品缺陷，改着色路径。
    ⇒ 顺带一条仪器欠账：本轮新写的 `r90_stats_visual.py` 在**暗档**上
    `COLUMN_SEGMENTS=1 ⇒ NOT-RUN`（分隔线只有 ~10/255，门槛降到 8 之后 vibrancy 噪声把两列连成一段）。
    修法是把列位置从**同主题亮档帧**推，或改用行投影切列。在那之前，暗档侧栏逐行读数只有 R88 那一份，
    而那一份的**列身份**已被本轮证明错位（见 U-203）。

    R91 加两格数据点，并且**这台机器现在做不了那一次决定性对照**：

    ```
    focus-after-tab-light.png 1600x1264  NO_BLUE（焦点环零墨）
    同一帧被选中的那一行：整条纯黑色带，行均亮度 2/255，行内文字与图标全不可见
    交叉检查：捕获卷基线帧 content-with-history-750x560-light.png 同一状态也是同一条黑胶囊
    screencapture -x → 退出 0、2940x1912、采样 2500 点全 (0,0,0)；pmset UserIsActive 0
    ```

    ⇒ 选中态材质在**两条离屏路径里都是黑的**（不是在屏探针独有），而焦点环在捕获侧完全不可判；
    ⇒ 真机那一腿 **NOT-RUN**（显示器睡着/无录屏权限）⇒ 本轮**没有**资格说"真机也看不见"。
    ⇒ 下一步（126 里原来那三步仍然有效）：亮屏 + 授权后对一次；若真机正常 ⇒ 把
    "离屏帧不判选中态材质与焦点环"写成**声明**（与 `menuSurfaceReplicaFixtures` 同形状），
    而不是每次靠人记得。另：交叉检查第一版量到窗外（"整列最暗 6 行"命中窗口外黑底），
    扫描区域必须改用探针自己报的 `ListTableRowView` 矩形（U-210）。
127. **在屏卷第一次跑完就红：一行暴露两个半宽 `KeyViewProxy`**（R91 开 / 与 126、116、104 同族）：

    僵尸探针删掉之后，`testSidebarListFocusRingAfterClick` 第一次跑出结论，红话是：

    ```
    找不到行代理（要求 KeyViewProxy 宽 200…290、高 <40）
    宿主 (0,0,320,460)；实际 KeyViewProxy@(12.0, 50.5, 148.0, 25.0) 与 (160.0, 50.5, 148.0, 25.0)
    ```

    ⇒ 一行**两个半宽**可焦点代理（148 + 148 + 间距 ≈ 320 = 整行宽）。两种成因，本轮**不分定**：
    ① 产品的无障碍结构 —— Tab 一行停两次、VoiceOver 把一行读成两段、焦点环可能只画半行；
    ② 这条判据的期望（"宽 200…290"）写在它**从没跑出过结论**的情况下 ——
      一把没被正对照校准过的尺不配有罪判决（R87 / U-200 同一族）。
    ⇒ 第一步是**正对照**：同一颗尺去量快速选择浮层那一卷列表的行代理。
      也两个半宽 ⇒ ②（SwiftUI `List` 的固有结构，期望要按实测重推，并写进 D 台账）；
      只有一个全宽 ⇒ ①（产品缺陷，改无障碍结构，并同步这条判据）。
    ⇒ 不许的处置：为了让 CI 绿直接把期望改成"148 也行"（那是拿判据讨好现状）；
      或者把这条探针删掉 —— 它现在**能跑出结论**，正是 R91 之前所有在屏判据缺的那种东西。
    ⇒ 本轮推上去之后 main 带着这朵红，是有意的：修僵尸探针的意义就是让红能说话。

    → **R93 结案，判的是 ②（判据的期望写错），而且是被正对照判掉的**：
    新加的诊断判据 `testRowProxyCensusAsksTheConsequenceNotTheShape` 打出
    `ROW_PROXY_CENSUS 侧栏@窗口320pt 宿主=320pt 代理=2 行=1 首行各代理宽=[148+148]`、`ROW_PROXY_CENSUS 侧栏@窗口250pt 宿主=250pt 代理=2 行=1 首行各代理宽=[113+113]`、`ROW_PROXY_LISTROWS 行视图=11 个，前 3 个={{0, 10}, {320, 66}} {{0, 76}, {320, 51}} {{0, 127}, {320, 66}}`、`ROW_PROXY_CONTRAST 浮层(NSTableView) 代理=0 行=0 每行代理数=`
    ⇒ 11 行的树里只有 2 个 `KeyViewProxy`（行是 `ListTableRowView`，11 个、整行宽），
    两个都 `acceptsFirstResponder=false`，半宽还跟着宿主缩放 ⇒ 它们不是行代理，
    "Tab 一行停两次"没有发生。修法按 127 自己写的规矩来：**没有**把 200…290 放宽成"148 也行"，
    而是改成点真正的行视图 ⇒ `testSidebarListFocusRingAfterClick` 从红变
    `passed (0.738 seconds)`，整卷 `Executed 11 tests, with 3 tests skipped and 0 failures`。
    顺带一条我自己的错（U-216）：第一版只走 `nextKeyView` 链，差点据此说"同一行被停两次" ——
    **在链上 ≠ 会被停在上面**，现在读数同时打 `acceptsFirstResponder`。

128. **自检夹具覆盖了作业共享 `/tmp`，两道最终闸门连着两次读的是假日志**（R92 开 / 与 92、96、122、125 同族）：
    现象、复现、修法都在 Round 92 正文与 D-150。本机这一半已结：`prepare()` 通配映射 + 三条守卫 +
    闸门三支成因，`HERMETIC_MARKERS_SURVIVED=4/4`，电池 5 CAUGHT / 1 如期 ESCAPED。
    **剩下那一格只有下一次 CI 知道**：`Capture gate` 与 `On-screen probe coverage floor`
    第一次读到"自己那一步留下的日志"，`补回` 应当回到 0 附近、`started=probeA` 这种夹具名字应当消失；
    同时僵尸探针已删（R91），在屏那一卷在 runner 上第一次有资格跑到结论。
    验收：读 R92 的 CI 时按步骤名取那两行，不许跨步骤 grep（U-178）。

129. **跨步骤证据住在共享 `/tmp`，而不是 per-job 的 `$RUNNER_TEMP`**（R92 开 / 与 96、122、128 同族）：
    M515 那把刀明量出来的盲区：`test_cell_commands_never_address_the_shared_tmp` 只扫自检认识的
    那五步，往 `Frame baseline vs working manifest` 里加一句 `cp /tmp/frames.log /tmp/frames-snapshot.log`
    全量仍然绿。⇒ 只要还有一个步骤能写 `/tmp/frames.log`，"闸门读到自己那份日志"就只是暂时的。
    出路：CI 里跨步骤的日志/读数/证人一律写到 `$RUNNER_TEMP`（GitHub 每个 job 独立），
    或至少给每条被下游读的路径加一条"只有它能被写"的登记判据。不在本轮做：它要改的是整条
    步骤间协议，不是某一步的写法。

130. **「清空」那颗是不是红的、以及侧栏选中那颗蓝在 key / 非 key 两态下会不会变 —— 这两问这条通道答不了**（R92 开 / 与 116、126、104 同族；**标题 R102 收窄过一次，理由见下面追记**）：
    `SettingsView.swift` 里那颗是 `Button(role:.destructive).buttonStyle(.borderedProminent).tint(.red)`，
    而离屏捕获通道 `面板key=false appActive=false` ⇒ AppKit 把 accent 去饱和成灰。
    本机读数：三颗按钮填充 235/235/235（改前）、228/228/228（改后），红占优=0；
    侧栏选中胶囊 rgb(217,229,251) 配蓝标签 rgb(6,113,245) ⇒ 对比 3.53（暗档 3.47）。
    **这两个数都是通道的读数，不是产品给人的样子。**
    **R102 追记（标题为什么收窄）**：本单原题把"侧栏选中胶囊"也算成"通道判不了"，
    但**正文自己就给过胶囊的色读数**，本轮在同一批帧上复现成功
    （亮 `217,229,251` 配标签 `0,112,245`，暗 `28,43,64` 配 `0,122,255`，各 3865/3866 与 128/130 px）
    ⇒ **颜色本身这条通道看得见**（饱和度 34/36，不是灰）。真正判不了的只有"key / 非 key 那一对照"
    （捕获永远是 `key=false`）。所以标题改成两问：① 那颗是不是红的；② 那颗蓝在两态下会不会变。
    旁证一格（同一轮量到，说明"accent 能不能解析"不能按整条通道回答）：
    快速选择浮层那颗选中在**同一通道**里是**纯灰**（暗 `70,70,70` / 亮 `220,220,220`，色度 0）
    —— **猜测的**机制是 AppKit `NSTableView` 在非 key 窗口下画未强调态、而 SwiftUI 那颗 `List` 选中走 accent 解析；
    **机制没有实测**（要实测得开一次 key 窗口，属 149 那一类），所以这里只登记"同一通道对两种选中给出两种颜色"这个读数。⇒ 139（勾选框色度为 0）与 130 要**按控件判**，
    不能再共用一句"通道不解析 accent"。
    要判的是真机（或至少 key 窗口）里：① 那颗是不是红的、和确认框那颗怎么配合；
    ② 选中胶囊在 key / 非 key 两态下各是什么色号。⇒ 需要用户真机或授权，本轮记 NOT-RUN。

131. **统计页那套"0 卡片 + 1 条外线"要不要一起并进来**（R92 开 / 与 36、124 同族）：
    本轮量到五种分区四套分组语法（通用 1/0/0、快捷键 1/0/2、隐私 1/0/3、统计 0/1/0、数据改前 1/2/0），
    只把「数据」这一屏并进了多数语法。统计页是阶段一那个新功能的落点，它没有卡片、
    只有一条压在页面底色上的分隔线 —— 要不要一起并，得连热图那屏的视觉重量一起判
    （热图本身已经是"一块有底色的区域"，再套一层卡片可能反而重）。
    本轮**没有**顺手改它：那需要一次独立的判断，而不是"上一屏改了所以这屏也改"。

    → **R100 补两个读数，并把"下一轮怎么做"写死**（这条仍开放，未动产品）。
    发现方式是 R100 那把横向尺的**未判名单**：`CARD_INSET_DECLINED settings-stats /
    settings-stats-populated 两档 = 这一带读不到卡片`。这个"读不到"此前一直被当成正确答案
    （R97 的读数：那一屏源码里确实没有 `GroupBox`，`testEverySettingsCardAppliesTheSharedEdgeInset`
    扫源码也证实），本轮逐张看帧才看出它同时**就是这一条问的那件事**：
    那一屏的内容长在页面底上，热图与「这张图怎么读」之间靠一条裸 `Divider()` 分隔 ——
    正是 R92 从「数据」屏删掉、R99 从「推荐」屏删掉的那个形状。
    现在这扇窗口五屏守规矩（卡片内分段），一屏不守。
    本轮**新增的反对证据**（131 原来那句"再套一层卡片可能反而重"仍然成立，所以不结案也不改）：
    横向内缩这一族量出来系统 `GroupBox` 自己就是 5.5pt（见 138 结案），
    ⇒ 并进来在"留白"这一维没有任何收益，收益只在"分组语言统一"这一维；
    而代价是热图那块有底色的区域外面再套一层材质，两层底色。
    **下一轮若做，做法已定**：热图 + 图例 + 汇总行收进第一张 `GroupBox`，
    「这张图怎么读」收成第二张（抄 R99 在「推荐」屏的形状，含
    `.frame(maxWidth: .infinity, alignment: .leading)` 那一格 —— 不写它卡片按内容缩窄、
    尺读不到材质，见 U-256），只动容器、不动行为与文案；
    并且**必须先让名单收得下它**：`settings-stats` 现在是被"读不到卡片"合理拒掉的，
    改完卡片之后它必须进名单并读出"上方 1 段 / 下方 0 段"，
    否则就是"改了容器而尺看不见"（R95 那一课：守卫只扫 `SettingsView.swift` 时漏掉过另一文件里的卡片）。

    → **R101 结案：改了产品，而且形状是先 spike 出来再定的**（不是"上一屏改了所以这屏也改"）。
    做法：先按上面那段"做法已定"里**最省事的那一版**（整块 `DailyCopyStatsSection` 包进一张
    `GroupBox`，标题留在卡片里）出一张帧，**看图 + 看尺**同时驳回它：
    那一版让这一屏变成全窗口唯一"分区标题在卡片内"的一屏，而它自己那条
    `CARD_ABOVE` 当场报回"卡片顶之上读到 0 段墨，而规矩是只剩分区标题那 1 段"
    （`.scratch/motion-audit-2/r101_spike_*`，帧与红都在）。
    ⇒ 换成"标题裸在卡片之上 + 一张卡片装下热图/图例/汇总行/那条 `Divider()`/说明段"，
    与通用·快捷键·隐私·数据四屏同一套语法。
    **与上面那份"做法已定"的差**：那份写的是**两张**卡片（说明段单独一张，抄 R99 的「推荐」）。
    本轮选了一张，理由是"这张图怎么读"是**从属于**图的说明，不是与图并列的第二格内容；
    而 R99 那两张卡片之所以分开，是因为第二张（「推荐反馈数据」）是一组**独立开关**，不是说明。
    代价写清楚：一张卡片里只有 1 条分隔线 ⇒ 节奏判据（要 ≥2 条才有对象）对这一屏仍然 declined，
    也就是"卡片内部留白节奏"这件事这一屏量不到 —— 两条路都有这一格损失，不是选一张才有的。
    **改完的读数**（本机，pass 见 `r101_verify.log`）：
    `CARD_ABOVE settings-stats light 卡片顶=116.0 … 详情区墨带=1 详情区段=78.5..91.5`、
    `CARD_BELOW … 墨带=0`、`CARD_INSET settings-stats-populated light 内缩=5.5pt`（= 系统参照同档）、
    `CARD_INSET_CAPABILITY 候选=26 有材质=26（被告=24 参照=2）量到=24 未判=0`
    —— **未判从 4 格降到 0 格**：这扇窗口现在没有一屏躲在那三条判据外面了。
    帧：8 张换（`settings-stats*` 四张 + `heatmap-populated` / `heatmap-empty` 四张 —— 后四张是因为
    标题从组件里搬出去了），其余 **122 张逐字节不变**，`ADDED=0 MISSING=0`。
    产品文件两个：`SettingsView.swift`（`statsSection` 与 `DailyCopyStatsSection`）、
    `DailyCopyHeatmapView.swift`（`header` 只剩汇总行）。
    **顺手被这条改出来的两格判据**（都不是原计划里的）：
    ① `.settingsCardInset()` 第一版挂到了 `GroupBox` **外面**，节奏尺量出 `边距=7.0/7.0`
      而**没有任何断言会红**（这一屏只有 1 条分隔线，`dividers >= 2` 那道地板让它走 declined）
      ⇒ 新加一条一边的下界判据（≥10pt，出处见 Round 101 §3），牙是 M563；
    ② 空态那一臂的首墨是 `StateLine` 的图标不是文字，量到 6.5pt 对文字参照 5.0/5.5
      ⇒ 没有放宽等式，改成给这一格一条**有界的**替代判据（侧边距 ∈ [+0.5, +2.0]），牙是 M566，
      读数 `CARD_INSET_ICON_FIRST`。

132. **第二具在屏僵尸有名字了：`testRightClickMenusAppKitWouldShowAreChinese` 在 runner 上吃满 240 秒**（R92 开 / 与 92、125、128 同族）：
    R91 推送的 CI（run 38852286519）里 `已下结论的用例: 6`、`started=7`，第 7 条就是它，
    两条通道同意（`UI_PROBE_CHANNELS_AGREE=1`）。本机 R91 那一遍它是**跑完的**（10 条 13.782 秒）
    ⇒ 不是"它一定挂"，是"它在这台 runner 上要么挂要么慢到吃满看门狗"。
    它管的正是人工清单里挂着"要真机"的那一条（R2-22 原生 `NSMenu` 的中文标题）。
    **本轮只做到点名**：没在 runner 上 `sample`，所以不写"和 CoreDrag 同一族"。
    R93 的第一格：在 runner 上给这条加一次 `sample`（或把它单独 `--filter` 出来跑一遍），
    分清"挂死"与"慢"；如果是慢，要量的是慢在哪一段，而不是把 240 秒的看门狗放宽。

    → **R94 更新（读数到手，处置没做）**：run 38857388449 里它仍是那条开口没闭口的
    （`UI_PROBE_HUNG=testRightClickMenusAppKitWouldShowAreChinese`、`started=7 concluded=6`、
    `UI_PROBE_CHANNELS_AGREE=1`），而本机这一遍它 `passed (2.016s)` ⇒ "挂 or 慢"仍未分。
    本轮新加的 `PROBE_ORDER 露面=…/未闭口=…` 与 `PROBE_QUEUED 4/11 条一次都没轮到`
    把"排在它之后"从推断升成读数（下一次 runner 上就能被证伪），
    但 **sample 那一格仍欠着** —— 它才是 132 的第一格。

    → **R95 更新（工具上 runner 了，栈还没读）**：`.github/workflows/ci.yml` 的看门狗现在在
    `kill` 之前先 `sample "$victim" 2 5 > /tmp/ui-sample.txt`（先 `pgrep -f "xctest -XCTest
    ClipboardHistoryAppTests.UIInteractionProbeTests"` 点名，找不到就写 `none`），
    两份报告调用都带 `--sample /tmp/ui-sample.txt`；`ui_probe_report.py` 里 `analyse_sample()`
    把"挂 vs 慢"变成占比读数（主导路径落在叶子上的采样 ÷ 主线程总采样 ≥0.85 ⇒ `blocked@族`）。
    **判据的三条前提**都各有一格：没有 `Call graph:` ⇒ 不判；有它却找不到主线程那一行 ⇒ 不判；
    占比只从**主线程那块**算（`Sort by top of stack` 是跨线程的，拿它算会把主线程挂读成"在往前走"）。
    132 仍然开着：这一轮的 CI 才有第一份 runner 栈。

    → **R96 更新（第一份栈到手，但那份读数是假的，已撤）**：run 38876999489 里
    `UI_PROBE_SAMPLE_EXIT=0`、`UI_PROBE_SAMPLE 主线程采样=306 主导路径占比=100% 最深帧=读不到`、
    `UI_PROBE_HUNG_KIND=blocked@unknown` —— 前一半是真的（主线程那一行确实读到 306 个采样），
    后一半是**兜底造出来的**：`nodes` 为空时旧写法把占比写成 1.0。
    ⇒ 撤掉兜底（读不懂就是未量到，占比 0.0 而不是 1.0），并新增 `UI_PROBE_SAMPLE_UNPARSED=1`
    + `UI_PROBE_SAMPLE_SHAPE`（只打缩进/是否数字开头/长度，不打帧名）。
    132 的"挂 or 慢"仍未回答，但下一次的红/绿有了明确的入口：那行 SHAPE。
    三种形状（整段为空 / 数字开头=no / 数字开头=yes）各自的下一步写在
    `.scratch/motion-audit-2/r96_ci_readings.md` 末尾。
    → **R97 结案**：run 38884429809（`278415e`）里
    `UI_PROBE_SAMPLE 主线程采样=314 等待帧占比=100% 主导路径占比=100% 等待终端=1 个`
    + `UI_PROBE_SAMPLE_WAITING=mach_msg2_trap  (in libsystem_kernel.dylib) + 8(314)`
    + `UI_PROBE_HUNG_KIND=blocked@runloop-wait`，且 `UI_PROBE_SAMPLE_UNPARSED` 没出现
    ⇒ 314 行全解析出来了。答案：**挂**（主线程整个停在 runloop 的 mach_msg 等待上），不是慢。
    这一句现在才有资格说，因为它由 314 个采样、一个等待终端、一个族签，而不是由一个兜底的 1.0。
    顺带：R96 准备的"三种形状各一条下一步"一条都没用上 —— 那是给"读不懂"准备的，
    而这一次读懂了。**登记的分支没发生，不算白做**（它逼出了 `未量到` 那一格，才让这次的"读到"可信）。

133. **浮层帧里搜索框带着一层"全选高亮"的灰底，可能污染过 R76 那格的墨移动量**（R93 开 / 与 95、108、116 同族）：
    夹具走 `field?.stringValue = query` 赋值 ⇒ `quickpick-typed` 与 `quickpick-empty` 两张帧里
    查询文字外面有一层 rgb(220,220,220)（暗档 70,70,70）的底，块尺寸 26x16pt / 64x16pt。
    两个后果：① 浮层搜索框的**静置外观**在这条通道里没有帧可看；
    ② R76 那条 `testOverlaySearchFieldFocusRecedesThePlaceholderAndDrawsNoRing` 比的是"焦点那一档
    墨移动了多少 pt²"，而一层灰底会同时改变"有墨"的定义 ⇒ 那格的读数可能混着两种成因。
    本轮**没有**动它：要先给夹具一条"赋值但不选中"的路径（`currentEditor.selectedRange = NSMaxRange…`
    或改走 `setQuery`），再重跑那格的地板与正对照。不许直接把地板调低。

134. **在屏名册的 `can/cannot` 还欠一次翻转，等 R92 的 CI 逐条印出结论名**（R93 开 / 与 92、128、132 同族）：
    run 38852286519 只数出"六条有结论"，名字随被 SIGKILL 带走的 stdout 缓冲一起丢了。
    按字典序猜是哪六条 = 登记没量过的推断（R87 那一课），所以 R93 只改了成因、没翻身份。
    R92 推送的 `9c10569` 第一次带上"闸门读自己那份日志"的修法 ⇒ 那一步会逐条印出结论名。
    验收：翻完之后 `probe_coverage_gate.py` 不许报 `NOW_RUNS` 或 `NOT_RUN`；
    如果它报了，说明翻错，按它点名的那条改回去 —— 这两格存在的理由就是这个。

    → **R94 结案**（run 38857388449 / `8e6ed15` 的 `On-screen probe coverage floor` 逐条点名之后）：
    六条翻成 `can`，判定是**读来的**且分开写 —— `testAccessibilityTreeCoverage` 那次是 `skipped`
    ⇒ 它只证明"runner 跑得动"，今天仍不产出产品判断；其余五条是 `passed` ⇒ 产品结论第一次能引用那台机器。
    剩下五条 `cannot` 的成因分三种写法：1 条就是挂住的那条（132）、3 条真的排在它之后、
    1 条（R93 新登记的那条）**根本不在 `8e6ed15` 的源码里**（那次闸门读数是 `源码用例=10 登记=10`）
    ⇒ 不许把"没编译过"写成"排队没到"。名册：`cases=11 can=6 cannot=5`。
    翻转之后本地对两份真日志各判一次：r62 那份（零结论）现在**该红**且逐条点名（NOT_RUN ×6），
    8e6ed15 那份该绿 —— 这两格替代了原来那句"真 CI 日志该绿"的旧契约。

135. **执行序这把尺遇到"交错日志"会说谎：结论行之后再出现一次 `started.` 会把状态改回未结论**（R94 开 / 与 112、132、80b 同族）：
    变异 M521 是**故意留着绿**的那一刀 —— 现有任何夹具都不产生"结论之后又见面"的形状，
    所以 `execution_order()` 里那格 `if kind != "started."` 的写法没有判据覆盖。
    真实风险：`/tmp/ui.log` 是 `swift test > … 2>&1` 的**共享**通道，如果哪一步把第二个进程的
    输出并进来（R80b 那次是两行被缝成一行），"未闭口"的计数就会凭空多出来，而它现在是登记的依据之一。
    修法（下一轮，别在改产品的那一轮顺手做）：喂一份**交错**的夹具（A started、A passed、A started、B passed）
    并断言 `露面/未闭口/前缀` 三个读数，再决定"后到的 started"算重跑还是算噪声。

    → **R95 结案**：`execution_order()` 改成三元组 `(order, concluded, interleaved)` ——
    结论**粘住**（下过 passed/failed/skipped 就不再被后来的 `started.` 抹掉），交错本身升成一格读数
    `PROBE_ORDER_INTERLEAVED <n> 条…`（仍只报不判，名字归 `ui_probe_report`）。
    新夹具 `r94_runner_ui.log` 之外补一份真的交错日志进 `InterleavedLogTests`，
    M521 从"预期绿的洞"变 `CAUGHT` ⇒ `MUTATE_TABLE n=7 caught=7 intended_escaped=0 mismatch=0 not_run=0`。

136. **菜单栏面板：标题与小标题在复刻里居中，而 macOS 12 那条路径用的是原生 `NSMenuItem(title:)` —— 两条系统路径可能不一致，这条通道没资格判**（R94 开 / 与 130、126、R2-22 同族）：
    实测（`r94_menubar_readings.log`）：`时间剪史` 的墨带 x=134.5..184.5（帧宽 320 ⇒ 居中），
    `猜你要粘贴` x=132.5..186.0（也居中），而三条推荐行与动作行的带是 x≈0..319.5（左贴边、右溢出）。
    源码侧事实：`MenuBarRecommendationsView` 里那两个 `Text` 没有 `.frame(maxWidth:.infinity, alignment:.leading)`，
    隐式栈因此把它们居中；`MenuBarController.swift:70`（macOS 12 那条）用的是
    `NSMenuItem(title: "时间剪史", …)`，AppKit 自己左对齐。
    **为什么本轮不改产品**：`menubar-*` 这批帧对宽度/截断/**对齐**/命中区没有发言权
    （R34 的 `testMenuBarFramesAreReplicasOfTheMenuSurface` 钉着，本轮 6/6 帧复核它仍然成立）。
    真机那一腿要核对三件事：① 菜单里的标题到底居中还是左对齐；② 动作行那层蓝在真实菜单底色上的对比
    （复刻里是 3.52 / 5.16，底色是夹具的 `windowBackgroundColor`）；③ 理由列在真实菜单里是被截断还是把菜单撑宽。
    核对完再决定要不要给那两个 `Text` 加左轴 —— **不许**先改产品再拿复刻当证据。

137. **`analyse_sample()` 在并列处没有判据：主导路径每层取"最后一个 count==total 的孩子"，改成"第一个"也一样绿**（R95 开 / 与 132、104、127 同族）：
    变异 M527 是**故意留着绿**的那一刀 —— 现有五份 sample 夹具里没有任何一份出现
    "同一层有两个 count 都等于 total 的孩子"。真实风险不是学术性的：`sample` 的树是按采样数折叠的，
    一个分叉成两条等权路径的栈（比如主线程同时在等两个信号）就会并列，那时"挂在哪件事上"
    由我取哪一个孩子决定，而族（`coredrag` / `menu-tracking` / …）就是从那个叶子推出来的。
    做法：造一份并列夹具（同一父节点下两个 `count==total` 的孩子，一个 `TrackMouse`、一个 `mach_msg2_trap`），
    先决定期望（并列时**不许**只挑一个 —— 应当报"并列"并把两个族都打出来，或者按叶子深度定序），
    再给 M527 一条期望。在那之前 132 的 runner 读数要带一句"并列未覆盖"。

    → **R96 结案**：修法不是补夹具，而是**换掉判定的来源**。`_waiting_leaves` 数的是
    "有多少采样停在等待帧上"（等待帧套等待帧只算最内层那一次），并列时两个族连同各自采样数
    一起打出来 ⇒ `blocked@ambiguous` + `UI_PROBE_SAMPLE_TIED=2 个族分不开：menu-tracking=300、runloop-wait=300`。
    新夹具 `sample_tied_branches.txt`；变异 M534（"并列时只报第一个族"）现在**必红**；
    M525 的锚点随 `_dominant_path` 退出判定而消失 ⇒ 退役，M527 由 M534 替代，
    两条退役记录写在 `mutate_r96_triage.py` 的文档串里（"表里少一格"与"那一格永远绿"是同一种失忆）。

138. **设置卡片的横向内边距是 5.5pt，而 macOS 自己的分组卡通常 16–20pt**（R95 开 / 与 124、131 同族）：
    R95 把竖向那一档统一了（边距 14.5/14.0 vs 内侧 14.0/14.5），横向没动，因为它不是"两种规矩"而是
    **一种一致的紧**：文字左沿 177.5、卡片左界 172.0 ⇒ 5.5pt；右侧对称（`恢复默认` 右界 690.5 / 卡片 695.5）；
    分隔线左右各 5.0pt ⇒ 与文字同轴（差 0.5pt = 光栅）。八张 `settings-*` 帧两档同一组数。
    **为什么不在本轮顺手改**：抬横向留白会**缩正文可用宽度**，而 R28 那条
    `testSettingsHelperTextIsNotClipped` 判的就是这一屏的说明段被截断 —— 那是一条耦合，
    改完必须重跑截断判据并逐张看帧（第三行说明本来已经排到四行）。
    做法：先量"抬到 14.5pt 之后第三行会不会把 `（那是浏览器和编辑器里的"粘贴并匹配样式"…` 挤出可视高度"，
    再决定抬哪一档；不许拿"看着更松"当理由。

    → **R99 复现了一次，并且把这句话收窄成"墨到边"（U-265）**。用 R99 刚交付的帧（诊断通道，不作证人）：
    卡片左沿 **172.0pt**、第一行墨 **177.5pt**（快捷键屏）/ **178.5pt**（推荐屏）⇒ 5.5 / 6.5pt 这个数是真的，
    但它是**墨到卡片边**，含字形侧边距 ⇒ 它**系统性低报布局 padding**。与"系统惯例"可比的量只有一个：
    **控件外框（勾选框方框 / 按钮 bezel）到卡片边**。所以这一条在 R100 动手之前还欠两个前提：
    ① 换成 bezel 到边重量（判据侧做，不许用 /tmp 手搓尺 —— R99 试了一次：越界 IndexError，
      而且它没有"这一行到底有没有墨"的正对照闸门，会把"没找到"报成 −172pt 这种距离）；
    ② 核对"macOS 分组卡通常 16–20pt"是**量出来的还是印象**。若是印象，判据要换成本窗口内部那条左轴
      （先例：R26 把骨架条带与说明钉在同一条左轴），**不许给没量过的数写阈值**。

    → **R100 结案：这一条不是缺陷，那条"16–20pt"是没有出处的印象。产品一行都没改。**
    两个前提都补上了，且结论与预期相反：
    ① **系统自己那一档量出来了 = 5.5pt**（新夹具 `cardprobe-groupbox-default`：一个什么都不加的
      `GroupBox { Text }`，夹具声明 `.padding(24)` ⇒ 卡片左沿读 24.0pt、第一个字形读 29.5pt）。
      亮暗两档同一个数。产品六张卡片：左沿 172.0、第一处墨 177.0~177.5 ⇒ **5.0~5.5pt**，
      与系统参照差在一像素之内。`.settingsCardInset()` 只加**纵向**留白
      （`SettingsView.swift:38` `padding(.vertical, …)`），横向一个像素都没加 ⇒
      这个 5.5 完全是 `GroupBox` 给的。**按 16pt 去改会让这扇窗口更不像系统**，
      与目标里"优先系统 API / 原生材质 / 对标系统原生能力"三条反着走 ⇒ 不改。
    ② 右沿同法量得 **5.0pt**（`r100_right.py`，门限 20 才看得见控件：亮档控件边框 luma=223，
      在门限 60 下不算墨 ⇒ 与 139 那条"勾选框色度为 0"是同一族盲区）⇒ 左右对称，没有"一边紧一边松"。
    ③ 门限扫过 12/16/24/32/48/64 六档（`.scratch/motion-audit-2/r100_gate_sweep.txt`）：
      八屏 × 两档在**每一档**都读 5.0/5.5 ⇒ 读数对门限不敏感，这条数不是挑出来的。
    ④ 138 原来那句"要换成 bezel 到边"的顾虑在这里不成立：本轮的比法是**两侧同一种元素**
      （参照与卡片都取第一个字形的墨），字形侧边距这一项在差里抵消；
      只有拿"文字的左沿"去比"控件的左沿"时才需要 bezel 口径（右沿那一格用的就是控件）。
    守住的判据：`testSettingsCardHorizontalInsetIsMeasuredAgainstTheSystemGroupBox`
    —— 等式（每格与系统参照差 ≤1pt）+ 绝对锚点（参照左沿必须落在夹具声明的 24pt 上）。
    变异 M556（给共享 modifier 加 12pt 横向留白 ⇒ 二十格红 17.0pt）、
    M557/M558/M559 见 Round 100。
139. **设置里的勾选框在帧里色度为 0：勾上不是强调蓝，而是"换一档的灰"**（R96 开 / 与 126、45、130 同族）：
    实测（`r96_privacy_readings.log`，`settings-privacy` 两档）：五颗框的 `chroma=0`；
    未勾的填充亮 (223,223,223) / 暗 (58,58,58)，勾上的亮 (213,213,213) / 暗 (67,67,67)，
    对勾那颗的墨 46（亮）/ 47（暗）颗 vs 未勾 12–20 / 13–20 颗。
    源码侧事实：那五颗全是裸 `Toggle("…", isOn:)`，`SettingsView.swift` 里**没有任何自定义 `toggleStyle`**
    ⇒ 灰**不是产品选的颜色**，而是"离屏/非 key 窗口里系统怎么画"或"捕获通道怎么合成"。
    两种解释的下一步完全不同（前者什么都不用做，后者是通道盲区），所以：
    ① 真机核对（人工批次 75.1）：勾选一颗，看它是不是强调色；
    ② 若真机是蓝 ⇒ 把"勾选态的颜色"写成一格**声明的盲区**（与 `menuSurfaceReplicaFixtures` 同形状），
       而不是每次看图时靠人记得；
    ③ 若真机也是灰 ⇒ 那是 `accentColor` 没进这棵树，改的是窗口侧不是这一屏。
    **本轮不改产品**：拿帧当证据去改一颗我没资格判的控件，正是 D-090 禁止的那类操作。

    **R132 结案（真机通道判到：那是离屏通道，不是产品）**：新增 `scripts/real_screen_control_chroma.py` ——
    走产品入口打开设置窗口、按坐标切到「通用」那一屏（并**用同一帧里侧栏选中那一行的移动**验收那一下点击落地），
    只截这一扇窗口的矩形，然后在**同一张帧**里比两块区域的 `b-r` 色度：
    参照（侧栏选中那一行，系统一定在画强调色）最大 194、强蓝 1032 颗、包围盒 x=17..64 y=82..95pt；
    内容区最大 190、强蓝 2463 颗、包围盒 x=177..192 y=98..219pt（正好是那一列勾选框住的位置）；
    比值 0.979 ⇒ 预登记的判法（≥0.50 有色 / <0.25 无色 / 参照下限 10）给出 `accent_in_content`。
    ⇒ 真机上勾选框就是强调蓝，本条那句"勾上不是强调蓝，而是换一档的灰"是**离屏通道不解析语义色**，
    与 126 / 130 / 172 同一族；产品不改（当初"不改"的决定现在有了真机证据，而不只是推断）。
    两条通道互相签字：数字（0.979 / 2463 颗）与我自己看那张真机帧（三颗蓝勾 + 一颗灰勾）方向一致。
    判据侧的账：U-438（点之前的探针被读成"尺坏了"，假阴性）、U-439（包围盒四个数印成 `x=177..98` 这种倒区间，
    形状像结论而对象是错的 ⇒ 现在有一条恒等式与一个 `BAD_BOX` 出口）、
    U-440（一条通道的能力要按**寻址方式**分开记：按名字不通、按坐标可通 —— 整条判"不通"会放弃这条通道）；
    变异第 35 张 `mutate_r132.py` 两臂 CAUGHT。
140. **三张设置卡片比窗口高，节奏判据对它们无从下手**（R96 开 / 与 138、43 同族）：
    `cardRhythm` 现在会把"为什么没量到"分原因返回（R96 新加），于是
    `settings-privacy` / `settings-recommendations` / `settings-privacy-excluded` 三张报的是
    `CARD_RHYTHM_DECLINED … 原因=卡片底到扫描带下沿 ⇒ 这一页比窗口高，被切断了`
    —— 它们**不是**"没有分隔线"，是"尺看不到卡片底"。
    这一屏在 720×540 的夹具里被截断是合理的（内容本来就要滚动，`detailScrollView` 在那儿），
    但代价是：卡片**下半部分**的留白节奏没有任何判据看着 —— 而 R96 那个缺陷（三段里只有一段有
    `.padding(.vertical, 4)`）恰好就长在卡片的**下半截**，这一轮能抓到是因为它在 `settings-data`，
    那一张没有比窗口高。换句话说：同样的缺陷在 privacy / recommendations 上是**测不到**的。
    做法：给这两屏各加一张更高的夹具（`settings-privacy-tall-720x1040`，与已有的
    `settings-privacy-excluded-720x1040` 同一族），让卡片完整落进带子里再判；
    帧数从 124 涨到 128 是可接受的成本。**别为了绿把 declined 那一格放宽**。
    顺带把边界写清楚，免得下一轮把两类混成一类：`settings-stats`（整带没有卡片）与
    `settings-stats-populated`（卡片里没有一行被判成墨）报的是**另外两种**原因，
    不属于"被窗口切断"这一类，140 不覆盖它们。
    → **R97 更新（真病根不是夹具，是写死的扫描带）**：`testSettingsCardVerticalRhythmIsOneNumber`
    的带子是 `CGRect(x:155, y:60, width:560, height:440)` —— 照 720×540 那一档定的，
    所以 1040 那一档"卡片到不了底"是**带子**短，不是页面高。改成 `height: fixture.size.height - 60`
    并加一条恒等式（`带子下沿 == 窗口高`，变异 M540 撤它就红）之后，
    `settings-privacy-excluded` 第一次被逐张判：段1 边距 14.5/14.0、段2 边距 14.0/14.0（两档一致）。
    **但 140 不结案**，因为还剩两件事：① `settings-privacy` / `settings-recommendations` 在 540 那一档
    仍然被窗口截断（判据报"卡片底到带子下沿"）⇒ 那两屏的下半截还是没人看，高夹具那一半照做；
    ② 新开的 **141**（判据读的是重编码位图）没解决之前，高夹具上的边界读数本身是**暂定**的。
    → **R98 结案（两件事都做了，而且 ① 立刻抓到一条真缺陷）**。
    高夹具 `settings-privacy-tall` / `settings-recommendations-tall`（各 720×1040，亮暗两张）
    进了帧基线，**124 → 128 帧**。读数：
    ```
    CARD_RHYTHM settings-privacy-tall light 段1/2 y=106.0..705.5pt 边距=14.5/14.0 内侧=13.5/14.5/14.0/14.0/17.5/14.0
    CARD_RHYTHM settings-privacy-tall light 段2/2 y=720.0..875.5pt 边距=14.0/14.0（无分隔线 ⇒ NO_DIVIDER，不判）
    CARD_RHYTHM settings-recommendations-tall light 段1/1 y=171.0..853.5pt 分隔线=8
                  边距=14.5/12.5 内侧=12.5/14.0/12.5/14.5/…（改后）
    ```
    改之前那一屏是 `边距=11.5/9.5` 对 `内侧=16.5/18.0` ⇒ 首末行贴卡片边、比彼此之间紧 5~9pt，
    与 R95 在「快捷键」上修的是同一个形状。修法：`VStack(spacing: 16 → 12)` +
    孤儿 `.padding(.vertical, 4)` 换成共享的 `.settingsCardInset()`（产品一个文件）。
    为什么这一屏以前逃过 R95 那一次：见**新开的 143**（守卫按文件划，而这张卡片长在另一个文件里）。
    ② 那句"暂定"随 141 被撤而解除 —— 141 的机制是错的，读图通道没漂，漂的是被量的那张图。
    两屏的下半截现在都有判据看着了：`settings-privacy` 那张卡片底在 705.5pt（540 档从来看不见），
    `settings-recommendations` 那张在 853.5pt。**不许把 declined 放宽**这条也守住了：
    540 档那两张照旧报 `CARD_RHYTHM_DECLINED`，只是旁边多了能判的那两张。

141. **卡片那把尺读的是重编码后的位图，不是它刚写下的那张 PNG**（R97 开 / 与 D-090、126、43 同族）：
    实测（`CARD_LAYOUT` 那一行）：`bytesPerRow=5760 bitsPerPixel=32 hasAlpha=true planar=false
    色彩空间=NSCalibratedRGBColorSpace` —— 判据走的是 `NSImage → tiffRepresentation → NSBitmapImageRep`，
    而 `NSCalibratedRGBColorSpace` 不是 PNG 落盘用的那个空间。
    后果不是"偏一点点"，是**边界换地方**：同一张 `settings-privacy-excluded` 亮档，
    判据给段1 = 106.0..705.5pt，而直接读 PNG 的独立复算给 106.0..765.5pt（顶边一致、
    段2 高度一致 155.5pt、段1 的底差 60pt）。卡片材质与页面底只差 8 个单位（244 vs 252），
    一次色彩空间换算的量级正好压在这条缝上。
    再补一格读数好让下一轮少猜：**两条通道在"平涂色"上是一致的**
    （Swift 报 `页底=252 填充=244` / `页底=28 填充=36`，直接读 PNG 复算也是 252/244、28/36），
    不一致只出现在**阴影与渐变带**上（卡片圆角外那几行）。
    ⇒ 141 的 before/after 表要按两类分开列：**边界类**判据（卡片段、分隔线、骨架条带、落点线）
    会随通道移动；**色号类**判据（对比度地板、热图相邻档、勾选框填充那一档）在平涂上不动。
    前者必须逐条重量，后者可以抽查——但"抽查"要写明抽了哪几条。
    ⇒ 本轮所有"边距 14.5/14.0 通过"的读数在高夹具上记成**暂定**：判据自洽，但它量的那张图
    不是交付的那张图 —— 这一族在账本里已经有名字了（D-090 是合成前，这次是重编码后）。
    做法（**必须成对做，不能顺手改**）：把判据的读图路径换成直接解 PNG 字节
    （`NSBitmapImageRep(contentsOfFile:)` 或 `ImageIO`），然后对**每一支像素判据**出一张
    before/after 表 —— 仓库里十几支判据的阈值（`inkGate=60`、`lineGate=6`、对比度地板、
    热图相邻档那一条）都是在这条通道上标定的，换通道就是换尺的零点。
    验收：换完之后 `settings-*` 的段边界要与独立复算**逐段相同**，且所有阈值重新量一遍出处。
    → **R98：这条的机制被撤，换一个真的（141 结案，但结的不是它自己开的那一单）**。
    R98 先按它写的做法把第二条读图通道接进来做对照（`pngRep` + 逐段比形状 + 比页底/填充），
    量出来的读数是：
    ```
    CARD_CHANNEL_SUMMARY 不一致=0 解不了PNG=0
    CARD_CHANNEL settings-privacy-excluded light 一致=yes
                 旧(TIFF)=106.0..705.5|720.0..875.5 新(PNG)=106.0..705.5|720.0..875.5 页底 252/252 填充 244/244
    ```
    ⇒ **两条通道在 settings 族 20 帧上逐段一致**，"重编码把边界挪走了"这件事没有发生，
    连"阴影与渐变带"那一格也没有（页底、填充两边同数）。R97 那句"同一张帧两条通道给出不同边界"
    错在一个**没验过的前提**：它假设 705.5 与 765.5 读的是同一张图。
    真相是两张不同的图 —— 逐字节对照（`CARD_BYTES`）里 settings 族 10 对只有**一对**不同，
    而那一对正是全仓唯一声明了 `seed:` 的夹具：
    ```
    CARD_BYTES settings-privacy-excluded light 本用例=319980 捕获卷=333059 字节数不同
    （其余 9 对：字节数相同；同一支用例连跑两次 md5 相同 ⇒ 不是抖动）
    ```
    逐行指纹（`.scratch/motion-audit-2/r98_seed_divergence.py`）把分歧起点钉在 **566.0pt**，
    870.5..936.0pt 交付帧 54 行墨 / 判据帧 0 行，右边缘那一列（x 684..706pt）
    交付帧读到 2 段「移除」、判据帧 0 段 —— 差的正是种子那两行。
    **根因**：`Fixture.seed` 的"种 + 还原"只写在 `testCaptureKeyViews` 一处，
    其余二十多个 `render` 调用点（全是"判据自己重渲染一张帧再量像素"那些）把它当不存在。
    所以这条 141 原本要求的"换读图通道"**不该做**：尺的零点没漂，漂的是被量的那张图。
    R98 的修法与判据见 D-155（把种子搬进 `render` 这个唯一咽喉 +
    `testSeededFixtureRendersTheSeededPage` 三格判据 + 变异 M543~M548）。
    修完的读数：`CARD_BYTES ... 本用例=333059 捕获卷=333059 字节数相同`。
    **这一句的范围要说准**：那一次运行打出的**亮档 10 对**全部 `字节数相同`
    （shortcuts / general / privacy / recommendations / data / stats /
    general-login-unsupported / general-login-failed / privacy-excluded / stats-populated），
    暗档我只逐条看了 `settings-privacy-excluded` 那一对（同一支用例，同一套代码路径）。
    结论不依赖那 10 对：依赖的是"唯一有种子的那一对现在相同了"，
    以及下面那条与独立复算对上的段边界。
    而 140 提到的"高夹具上的边界读数暂定"随之解除 ——
    `CARD_RHYTHM settings-privacy-excluded light 段1/2 y=106.0..**765.5**pt`
    第一次与独立复算相同（之前判据给 705.5，是因为它看的是少两行的那一页）。
142. **「推荐」页把分区标题与「恢复默认」放在卡片外，而卡片里第一行才是「近因」**（R97 开 / 与 124、131 同族）：
    实测（`CARD_BAND settings-recommendations`）：卡片段 y=**171.0**..539.5pt，
    而 y=106..129.5 那一带（"推荐权重客制化" + 那颗按钮）与它下面那行说明**都在卡片外**，压在页面底色上。
    其余几屏的写法是"标题与内容一起进卡片"（快捷键、隐私、数据），或整屏就没有卡片（统计，见 131）。
    ⇒ 同一句"这几行属于同一组"在同一个设置窗口里被说了三种话。
    **本轮不改**：把标题与按钮并进卡片会动到那一屏的滚动高度与按钮命中区（那颗按钮现在是
    `.bordered` + `pressedStyle`，R13 收过），而这一屏的卡片下半截在 540 档仍被窗口截断（140），
    两件事一起做就没法说清是哪一条起了作用。顺序：先 141（换读图通道），再 140 的高夹具，
    最后带着完整的段边界来判这一屏。
    → **R98：它等的那两件事都齐了，但本轮只交出一半**。
    141 的机制被撤（读图通道没漂）、140 的高夹具已进基线 ⇒ 这一屏的段边界现在是完整的：
    `settings-recommendations-tall light 段1/1 y=171.0..853.5pt 分隔线=8`。
    本轮对这一屏动了一次产品（留白档：`spacing 16→12` + 共享 `.settingsCardInset()`，见 140 的 R98 更新），
    那是"卡片内部的节奏"，与这一条说的"标题与按钮在卡片外"是两件事，没有顺手合并做。
    **仍然不改**：把标题与那颗按钮搬进卡片会同时改到卡片高度、按钮命中区、以及
    `settings-recommendations` 与 `-tall` 两档的段边界 —— 一次动三个变量就说不清是哪一条起了作用。
    下一轮判它的时候，读数已经齐了（853.5pt 的卡片底 + 8 条分隔线 + 四边 14.5/12.5）。
    → **R98 补一格：这条的"其余几屏"那半句是错的，本轮把它换成分屏的坐标**。
    我为了判这条写了一张 python 仪器（`r99_card_outside.py`），它先把自己的不可信暴露出来：
    它报的卡片顶比 Swift 那把尺早 **14pt**（92.0 vs 106.0），亮暗两档还互相差 7pt
    （`settings-recommendations` 亮 180.0 / 暗 173.0），并且把「统计」那张热图切成 **11 段"卡片"**
    —— 而 Swift 判据钉死的正确读数是 0 段（R97 / U-233）。
    ⇒ 这张表**不出**（记 U-251）：证人必须与被告同一颗尺子（BACKLOG 104），
    而"卡片外有几行字"这件事不依赖卡片顶到底在哪一格，所以下面这几条只取**卡片顶之上**的墨带，
    用肉眼看帧复核过，不取那张表里的段数。
    ```
    settings-shortcuts        卡片外墨带：78.5..90.0            ← 只有分区标题「快捷键」
    settings-recommendations  卡片外墨带：78.5..90.0、112.5..124.0、146.0..154.5
                                                            ← 分区标题 + 卡片级标题行(带那颗「恢复默认」) + 说明句
    ```
    ⇒ 142 真正的差别**不是**"标题在卡片外"（每屏的分区标题都在卡片外，那是 macOS 设置页的常规），
    而是：只有这一屏把**卡片自己的标题、它的动作按钮、以及一句说明**三行留在卡片外，
    卡片里第一行直接是内容（「近因」）。所以修法要判的是那三行该不该进卡片，
    而"把标题并进卡片"这个原写法会连带改掉每屏共有的分区标题那一层 —— 那是另一种统一。
    → **R99 结案（这一次它有读数，不再是"我看代码看出来的印象"）**。
    判据 `testSettingsCardVerticalRhythmIsOneNumber` 新增两格名单：**有卡片的每一屏，
    卡片顶之上恰好 1 段墨（分区标题），最后一张卡片之下 0 段**。改前两档 × 十屏实测：
    上方九屏各 1 段（78.5..90.5pt）、推荐屏 **3** 段（多出 112.5..124.5 的卡片级标题行 +
    「恢复默认」、146.0..155.0 的说明段）；下方推荐屏 tall 档 **2** 段
    （885.0..895.0 的「推荐反馈数据」标题、911.5..923.5 的按钮），其余各屏 0 段。
    ⇒ 这一屏不只"标题在外面"，它还有**一条压在页面底上的裸 `Divider()`** ——
    与 R92 当年给「数据」屏删掉的形状一模一样，而 R92 的登记话就写在源码注释里
    （"向多数靠拢，只动容器"）。本轮照同一句话办：两段内容都收进卡片（后者收成第二张卡片，
    与「隐私」那一屏的两张卡片同套），卡片级标题字号 `.headline → .subheadline` 并入其余
    卡片内小标题那一档。**只动容器**：按钮、回执通道、`.animation` 键、`restoreDefaults()` 一行没改。
    改后：`CARD_ABOVE_SUMMARY` 20 格全 `=1`、`CARD_BELOW_SUMMARY` 16 格全 `=0`。
    两条只有看图才抓得到的（详见 Round 99 §5、§6）：第二张卡片会按内容缩成 250pt 宽
    （⇒ 卡片尺读不到材质，"没有第二张卡片"与"卡片太窄"共用一个读数），
    以及标题与按钮同行时那颗 22pt 的按钮把标题往下推 4pt（⇒ 极差 6.0 > 4.5 判红，
    改法是抄 `清空未收藏记录` 那段"标题+说明在左块、按钮 trailing 居中"）。
    证人：变异表 `r99` 四刀，其中 M554 是**还原臂**（两个产品文件整体换回 `git show HEAD:` 那一版）
    ⇒ 上方 3 段、下方 2 段同时红；M555 撤 `maxWidth` ⇒ 下方 2 段红。

143. **数卡片的源码守卫按"一个文件"划范围，而卡片可以长在任何一个文件里**（R98 开 / 已修 / 与 140、D-090 同族）：
    `testEverySettingsCardAppliesTheSharedEdgeInset` 从 R95 起只扫 `Views/SettingsView.swift`，
    数那里的 `GroupBox {` 与 `.settingsCardInset()` 是否等量。R95 那次"五处一起补留白"因此
    漏掉了长在 `Views/RecommendationWeightsView.swift` 里的第六张卡片 —— 它带着一个孤儿
    `.padding(.vertical, 4)` 一直活到 R98，而**帧上也不会红**：那张卡片比 540 的窗口高，
    节奏判据对它一直是 `CARD_RHYTHM_DECLINED`（140）。两条盲区叠在一起 = 四轮的漏网。
    这条要记的不是"那个文件也要扫"，而是**按文件划的守卫永远追不上按组件长的东西**：
    名单要有人记得改，而"有人记得"这件事在 R95 已经被证明不可靠（我自己就没想起来还有一张）。
    R98 的修法：守卫改成枚举 `Sources/ClipboardHistoryApp/Views/` 下的每一个 `.swift`
    （`productViewSources()`，按文件名排序好让报表两次运行逐字对齐），
    并且失败消息**点名在哪个文件少了几处** —— 否则"7 张卡片 / 6 处留白"这句话还得人去猜。
    证人：变异 M551（撤掉这一张的 `.settingsCardInset()`）必须同时红两条 ——
    节奏判据量到 4.5pt 容差之外，调用点守卫数出 7/6 并点名 `RecommendationWeightsView.swift`；
    M550（只改行距）必须**只**红节奏判据、不许动调用点守卫 —— 一条守卫管间距就变成两件事互相顶包。

144. **R98 新立的种子判据欠 runner 第一个读数**（R98 开 / 与 43、134、137 同族）：
    `testSeededFixtureRendersTheSeededPage` 的未运行闸门是"**整页**一条墨带都没有 ⇒ 这台机器拍不出这一页"。
    这个形状在 runner 上是**半安全**的：runner 的 settings 族实测未绘制 90.6–95.9%（不是 100%），
    所以存在一种中间态 —— 页面别处画得出、而「移除」那两行所在的区域画不出 ⇒ 这条判据会在 runner 上红，
    而那一次红**不是产品**。本机判不出这件事（本机两档都画得出来：`整页墨带=34`、`右边缘墨带=2`）。
    做法（**不许**为了 CI 变绿把闸门改成"整页墨带 ≥ N 才判" —— 那个 N 只能从另一台机器的读数借，
    而 R38 已经证明借来的地板会互相取消）：
    ① 读 R98 推送的 CI，看这条判据在 runner 上是绿、红、还是 skip；
    ② 若红 ⇒ 把"这一区域在这台机器上画没画出来"变成**同帧的读数**再判
      （比如要求被 judged 的那一段自己先报"有没有墨"，没有就记 NOT-RUN 并点名区域），
      而不是加地板；
    ③ 若绿或 skip ⇒ 把那一格的 runner 读数抄进登记，这条就可以关。
    → **R99 结案（读的是 run `38898253512` 那一次）**：走的是上面 ③ 那一支 —— 既不是绿也不是红，
    而是 **NOT_RUN**，且它自己把话说全了：
    ```
    SEED_GUARD settings-privacy-excluded light 期望=2 右边缘墨带=0 整页墨带=0
    SEED_GUARD_NOT_RUN settings-privacy-excluded light（整页零墨 ⇒ 这台机器拍不出这一页）
    SEED_GUARD_NOT_RUN：两档所有种子夹具都画不出墨 ⇒ 种子通道记为未运行（BACKLOG 43 同族），不算通过
    ```
    这条判据在 runner 上**没有把"拍不出"读成"通过"**，也没有像 ① 里担心的那样红在中间态
    （runner 上那一屏是整页零墨，不是"别处画得出、那两行画不出"）⇒ 不必加地板、不必改闸门。
    但答案本身留下一条新的开放项：**种子通道至今在 runner 上没有真值点**（本机两档都有）⇒ 开 145 的兄弟项 146。

145. **CI 的探针那一步只报"哪条红了"，不报"红在哪一句"—— 而那句话就在同一行里**（R99 开 / 已修 / 与 R59、BACKLOG 86 同族）：
    run `38898253512`（R98 的 CI）那一步打的是
    `FAILED testFrameIntervalsUnderStateChanges：XCTAssertLessThanOrEqual 在这份日志里打红了 ⇒ 红要能被读，也要有人负责`。
    名字有、断言类型有，**那一句为什么没有** —— 而 XCTest 那一行本来是完整的：
    `error: -[… testX] : XCTAssertLessThanOrEqual failed: ("6.0") is greater than ("4.5") - <判据自己写的理由>`。
    `probe_coverage_gate.py` 的 `ASSERTION_RED` 只取到 `XCTAssert\w+` 就停了，把后半段丢掉；
    而那一步的日志里也没有别的通道能补上（`/tmp/motion.log` 不上传，`ui.log` 里的那一行被正则截短）。
    ⇒ "runner 上到底红了什么数"只能靠猜，而这一族里靠猜出来的修法已经错过一次（R51 那条红得不正确）。
    R99 的修法：正则把行尾一起取回来，结论行带原文（截 300 字），
    `test_probe_coverage_gate.py` 加一条钉它 —— **数值那一半与判据那句理由都必须在**，
    缺任何一个这条 python 判据红。同一个教训 R59 在 motion 那一步已经记过一次
    （`红的理由（XCTAssert 原文，最多 12 条）`），这一支当时漏了 ⇒ 记成"两条通道要同形"，
    而不是"再补一次这一步"。

146. **`testFrameIntervalsUnderStateChanges` 在 runner 上为什么红：本轮没有答案，也不许猜**（R99 开 / 与 145、134、43 同族）：
    同一支判据在 R97 的 run（`38891183309`）里是 `本次下结论=6 红=0`，在 R98 的 run 里是 `红=2`
    ⇒ 这一红随 R98 的推送出现。但 R98 的产品改动只有「推荐」那张卡片的留白档（设置窗口），
    而这条判据量的是**主窗口状态变化时的帧间隔**（`UIInteractionProbeTests:268` 起，
    900×640 的窗口 + `syntheticStore()` 灌数据），两者没有已知的因果路径。
    现在能说的只有：① 它不是"环境噪声所以忽略"——R97 同一支判据在同一个 runner 上是 0 红；
    ② 它也不是"R98 改坏了产品"——本机 R99 那一卷 `PROBE_EXIT=0`（见 Round 99 §8）。
    判它需要什么：**145 修好之后，下一次 run 里那一句原文**（哪个数、超过哪条线）。
    同一次 run 还要看第二条：`NOT_RUN testOffScreenProgrammaticSelectionIsRevealedAndNotJumped`
    （登记 `runner=can`、`PROBE_ORDER 未闭口=1`）会不会随红的那条一起消失 ——
    若仍不闭口，那是一问独立的（R61 那条 reveal 判据在 runner 上到底跑没跑完）。

    → **R100 读到了 run `38913173905`（R99 的 CI），两条都有答案，且都不是猜的**（145 的修法第一次生效）：
    ① **145 有效**：那一步现在打的是完整一句 ——
      `error: -[… testSettingsCardVerticalRhythmIsOneNumber] : XCTAssertFalse failed - 没有一屏进得了「卡片外几段墨」的名单 ⇒ 这条判据没有对象…`
      以及 `XCTAssertGreaterThanOrEqual failed: ("0") is less than ("8") - 名单只有 0 格`。
      名字、断言类型、数、判据自己写的理由，四样都在。
    ② **红的不是 146 原本等的那条**：`testFrameIntervalsUnderStateChanges` 在这一次没有出现在红里，
      红的是 **R99 自己新加的那格名单判据**（`CAPTURE_GATE_CASES passed=46 skipped=10 failed=1`）。
      所以 146 那一问（R98 的帧间隔红）**本轮仍然没有答案**，它欠的是同一次 run 里那条判据的原文 ——
      而它这次没红，说明它是随 run 波动的，不随 R99 的改动出现。这条不结案，等下一次它红的时候读原文。
    ③ 真正的答案是**顺带掉出来的另一件事**：runner 上 `CARD_BAND` 二十格全是
      `填充=-1 墨行=0 卡片段=0 scale=1.0`，页底 light=236 / dark=52
      ⇒ **CI 那台机器看不见卡片材质**（`GroupBox` 的填充落在页面底 ±3 以内，`cardFill` 第一关就没有一行过关）。
      这不是 R99 改坏的，是 R99 让**一直存在**的盲区第一次说话 —— 见新开 147。

147. **R95–R100 整族"卡片"判据在 CI runner 上一个真值点都没有：那台机器看不见卡片材质**（R100 开 / 与 146、43、128、R28b 同族）：
    run `38913173905` 的 `CARD_BAND` 二十格（10 屏 × 两档）全是 `填充=-1 墨行=0 卡片段=0 scale=1.0`，
    页底 light=**236** / dark=**52**；本机同一批帧是 页底 255/30、填充 247/37（差 8/7）。
    机制：`cardFill` 的第一关是 `abs(modal - pageLuma) > 3`，而 runner 上 `GroupBox` 的填充与页面底差 ≤3
    ⇒ 没有一行过关 ⇒ 参照色为 nil ⇒ 整族判据（竖向节奏 R95、卡片外几段墨 R99、横向内缩 R100）
    在那台机器上**从来没有对象**。
    **为什么这条值得单独记**：这五轮里"卡片"这一族的每一次"全绿"都只有本机一个证人，
    而 R99 把名单地板写成常量 8 之后，它在 runner 上变成**永久红** ——
    两个收场都错：静默通过是把"没跑"记成"通过"（BACKLOG 43 那一族），
    永久红是把机器前提记成产品缺陷，之后真缺陷会被这条淹掉。
    R100 的做法（已交付）：地板从**上游那一关**推导 —— `min(8, 读到材质的格数)`，
    材质格数由 `cardRowKinds` 的 `fill >= 0` 数出来（**不能从名单自己推**，那是恒真式，
    M553 那种"把尺弄瞎"的刀就咬不住）；材质格数为 0 时 `throw XCTSkip`，
    跳过会被执行数闸门数进 `skipped=` ⇒ 看得见、有名字，不是静默。
    读数通道：`CARD_ABOVE_CAPABILITY settings格=24 有材质=20 进名单=20`、
    `CARD_INSET_CAPABILITY 候选=26 有材质=22 量到=20 未判=4`（本机）。
    **R100 收尾补的第三格（原来只有"下一轮"两件事，现在它们有了一条能自己说话的通道）**：
    `cardRowKinds` 多返回一格 `modals`，两把尺在 `fill < 0` 那一格打
    `CARD_FILL_CANDIDATES <夹具> <档> 页底=… 前三=(色号:行数) … 门槛=abs(档-页底)>3且行数/倍率>=20pt`。
    设计要点两条，都是台账里旧教训的形状：
    ① 证人吃的是**判据自己那一个数组**（`cardFill` 读的 `modals` 原样交回来），
      不是调用点重扫一遍带子 —— 重扫就不是同一颗尺子了（BACKLOG 104 / R68）；
      渲染也拆成唯一的纯函数 `fillCandidatesLine`，纵向与横向两处共用，
      否则"两台机器打的是同一句话"这个前提迟早被两份手写副本拆掉。
    ② 前三名**必须含页底那一档**（不是只报"离页底够远"的那些），否则
      「材质在但差 ≤3」与「根本没画材质」这两种形状在这一行读数里长得一样；
      空档时必须打「无」而不是空串 —— 空串与"那一行压根没打出来"（第三种形状）在日志里同形。
    **这条通道在本机已经自己正过一次**：它把 147 的成因与 131 的产品事实分开了 ——
    `settings-stats light 页底=252 前三=(252:960)`、`dark 页底=28 前三=(28:960)`
    （两档前三名**全等于页底**；`settings-stats-populated` 才多出第二档 ——
    light 的 `(228:2)`、dark 的 `(52:2)`，各只占 **2 行**，过不了 20pt 那一档地板），⇒「统计这一屏读不到卡片」不是门限问题，是**那一屏确实没有 `GroupBox`**
    （源码侧 R97 早已看过 `SettingsView.statsSection` 直接放 `DailyCopyStatsSection`），
    而现在这句话是**读出来的**，不再是论证出来的。这也解释了两条能力读数里
    `候选=26 有材质=22`、`settings格=24 有材质=20` 各自缺的那 4 格 = 统计两屏 × 两档。
    **还欠的**：① 本机与 runner 的材质差是 8 vs ≤3 —— 这条差是 runner 的半透明材质不合成，
    还是 1x 光栅把 8 档差摊平了？本轮没有 runner 上的像素，答不了；
    **但从下一次 run 起不用再猜**：那一次 run 的 `CARD_FILL_CANDIDATES` 会把二十格里
    每一格的前三名连行数一起打出来，三种形状（门限 / 通道 / 判据没走到）在那一次里就能压成一种。
    判据表：`mutate_r100b.py` 的 M562（把名次改成按色号排 ⇒ 真值表红）+
    `testFillCandidatesSeparatesNoMaterialFromMaterialTooCloseToPage` 六格。
    **诚实记账**：调用点那一句 `if fill < 0 {` 的打印闸门本身**没有判据**
    （`declined.count ≤ 6` 数的是"读不到卡片"的格数，与这一行打没打无关）——
    所以这条通道在本机只有真值表一层保护，它的验收发生在下一次 run 读到这一行的那一刻。
    ② 若确认是通道盲区，要么给这一族换一条**不依赖材质分离**的左轴（内部左轴先例：R26），
    要么把它登记成"只有本机能判"的家族（与 126/130/136/139 那几条真机项同栏）。

    → **R101 结案（读的是 run `38927822527`，R100 那一次推送）**：走的是 ② 那一支 —— **通道问题**，
    而且比"差 ≤3 被门限挡掉"更干净：**那台机器上根本没有第二个色档**。
    上一轮装的 `CARD_FILL_CANDIDATES` 在 runner 上打了 48 行，每一行都是同一个形状：
    ```
    CARD_FILL_CANDIDATES settings-shortcuts light 页底=236 前三=(236:480) 门槛=abs(档-页底)>3且行数/倍率>=20pt
    ```
    ⇒ 前三名里**只有页底那一档**，而且它占满整带 480 行 —— 不是"材质与页面底差 1~3 被门限吃掉"，
    是**那一带逐行众数从头到尾只有一个值**。所以重标 `gate` 不会有任何用（没有可分开的两档），
    这一族正式登记成**只有本机能判**：`CARD_INSET_CAPABILITY 候选=26 有材质=2 量到=0 未判=25`、
    `CARD_ABOVE_CAPABILITY settings格=24 有材质=0 进名单=0`。
    **但成因比"runner 不画材质"窄，这一格是本轮最值钱的一条**：那 2 格有材质的是**参照**
    （`cardprobe-groupbox-default` 亮档在 runner 上量出 `内缩=6.0pt`，与本机 5.0/5.5 同一档量级），
    而 24 格被告**全没有**。⇒ 不是 `GroupBox` 在这台机器上画不出材质层，
    是**这扇设置窗口里的**卡片画不出来（真机差 16、本机离屏差 7、runner 上设置窗 0 而独立窗口 6.0）。
    这个收窄把"以后要不要给整族换一条左轴"的问题变成了"设置窗口这一条通道的合成问题"，
    并且给了下一次一个可查的方向：设置窗口用的是 `Form`/侧栏那一套容器，
    而参照用的是裸 `WindowGroup` —— 差在容器，不在 `GroupBox`。
    **顺带修掉一条我自己上一轮装的闸门**（这条如果不读 CI 就会一直红着）：
    `materialCells` 把参照与被告数成了同一个量，于是 runner 上"参照有、被告无"这个形状
    既不满足 skip（`materialCells != 0`）也不满足地板（`0 ≥ min(16,2)`）⇒ 三朵红，
    而它们说的都不是产品。R101 拆成 `defendantMaterial` / `controlMaterial`，
    "没有对象"响成 skip、"没有对照"响成红，两件事各有自己的牙（M564 / M565）。
    **这一族的 runner 身份从此写死**：CI 上这三条判据（竖向节奏 / 卡片外几段墨 / 横向内缩）
    合法收场是 **skip 且带名字**，不是绿。下一次 run 若 `skipped=` 少了这两条，
    要问的是"runner 什么时候开始能画设置了"，不是"判据变好了"。

148. **【结案 · R104】快速选择浮层：搜索框的字比它下面那一列内容的左轴还靠左 9.5pt（浮层里第二条左轴）**（R100 开 / 与 26、32、34、76 同族，**产品改动，已做**）：
    实测（`quickpick-list-420x300` 亮/暗、`quickpick-typed-420x300` 暗，2x，
    尺：`.scratch/motion-audit-2/r100_overlay_axis.py`，只作诊断不作证人 —— 它没有正对照）：
    同一张 420pt 宽的浮层面板里，从上到下三条左轴是
    **搜索框文字 12.5pt** → **行背景（选中/悬停那颗胶囊）22.0pt** → **行内图标 35.5~37.5pt**。
    也就是说占位语「搜索历史记录…」比它正下方那一列的**底色边**还往左突出 9.5pt，
    视觉上那一行字像贴在面板毛边上、而不是站在这列表自己的列里。
    **通道可信度**：这张帧不是复刻体 —— `QuickPickCapturePanel.builder` 走的是
    `QuickPickController.windowForCapture(...)`（`QuickPickController.swift:87`），
    里面 `ensurePanel()` 拿的就是真浮层那一个 panel，`field?.stringValue = query` 写的也是产品那颗字段
    ⇒ 这三条左轴是产品事实（BACKLOG 36 那一族"组件帧与产品对齐"这次站在我们这边）。
    **为什么本轮不改**：① R100 的产物是判据，帧基线正按当前状态 `update`，中途改浮层会让
    "基线=本轮产物"这条对账失效（U-263 那一族）；② 这一改需要先定"哪一条是想要的轴"，
    而那是一个判断不是读数 —— 两个方向都说得通：把搜索框右移到 22（与胶囊同轴，浮层内部自洽），
    或把整列内容左移到 12.5（与系统 `NSTableView` 无边距那一档一致）。
    **R102 追记（三条，其中一条推翻本单自己的一个说法）**：
    ① "22.0 是胶囊左沿"**成立且两档都成立** —— 但本单引用的那把尺（`r100_overlay_axis.py`，门限"与填充差 ≥40 灰阶"）
      在**亮档读不到这一带**：实测"胶囊 vs 页面底"的灰阶差是 暗 **40.0**（70,70,70 对 30,30,30）/ 亮 **35.0**
      （220,220,220 对 255,255,255）⇒ 亮档刚好在门限下面。**门限在这一对上是悬崖不是平台**，
      所以 R103 立判据要么把门限降到 ≤30，要么换成"与页面底差 ≥12 且连续 ≥6px"那种与色档无关的列计数。
    ② 胶囊几何已量：**左沿 22.0 / 右沿 397.5**（面板 420 ⇒ 左右 22.0 / 22.5，对称）
      ⇒ 那 10pt（stack 内缩 12 → 胶囊 22）是 `NSTableView`/滚动视图那一层的**行内缩**，不是对齐问题；
      改轴只需要动一个常数，且**不需要两处一起改**：浮层那颗是 AppKit `QuickPickSearchField`
      （`QuickPickController.swift:202`，`isBordered=false drawsBackground=false`），
      主窗口侧栏那颗是 SwiftUI `SearchField`（`HistorySidebarView.swift:12`，自带 `.padding(.horizontal, 9)`）—— 两个容器。
    ③ 浮层这颗选中在离屏通道里**色度为 0**（两档纯灰），而设置侧栏那颗 SwiftUI 选中在同一通道里是蓝
      （暗 `28,43,64` / 亮 `217,229,251`）⇒ 130 那句"accent 这一档判不了"要**收窄到按控件说**，
      不能当成整条通道的性质（这一条同时是 139 的旁证：勾选框灰、侧栏蓝、浮层灰，三格三种答案）。
    **下一轮做之前必须先量的两件事**：
    ① 真机 key 窗口下搜索框有没有焦点环/底 —— 捕获卷是非 key 窗口，
      焦点环会把"框"的可见边界往左推，那样 12.5 就不是肉眼看到的"框的左边"（与 130 同族盲区）；
    ② 主窗口侧栏那颗搜索框（账本 line 537 记过它 62pt）与浮层这颗是不是同一个容器样式 ——
      若是，改轴要两处一起改，别只改浮层（R95 那次"五处一起补"漏一处的教训）。
    判据形状（改完之后）：一条"浮层内所有左轴必须落在同一条上"的像素判据，
    与 R26 给骨架条带立的那条同形；参照物用**胶囊自己的左沿**，不用面板边（R37 那一课：
    参照点选错会让判据量的不是那件事）。

    **R104 结案（产品改一处常数 + 一条像素判据 + 四刀变异表）**。
    ① **轴取哪一条**：取**药丸的左沿 22.0pt**，不取行边界 12.5。理由是"看得见的才是那一列"——
      行边界在这张帧上不可见，药丸是行里唯一有边的东西；而把整列左移到 12.5 需要
      `table.style = .plain`，那是 macOS 13+ 的 API ⇒ 12 上抹不掉，
      同一扇浮层会在两个系统版本上给出两条轴，比现在更坏。
    ② **改了什么**：`QuickPickController.searchFieldLeadingInset = hoverFillInset`（一个常数，
      与药丸同源），落在 `QuickPickSearchFieldCell` 的 `drawingRect` / `edit` / `select` 上。
      为什么走 cell 不走约束：那颗字段是 `NSStackView` 的 arranged subview，前缘已被 required 优先级钉死
      （R63 那一族的实测形态就是"面板只剩一角"）。
    ③ **改完的读数**（本机，两档一致）：
      `QUICKPICK_SEARCH_AXIS light 药丸左沿=22.0pt 搜索第一列墨=22.5pt 差=1px`、
      `QUICKPICK_SEARCH_AXIS dark 药丸左沿=22.0pt 搜索第一列墨=22.5pt 差=1px`（改之前是 12.5pt，差 19px）。
      那 0.5pt 是字形的左余距，不是内缩算错（10pt 内缩只被加了一次 —— 这一条由真值表第 ① 格钉住）。
    ④ **帧**：8 张 quickpick 帧换哈希（4 态 × 两档），其余 126 张逐字节不变；`update` 与判据同提交。
    ⑤ **牙**：M577 撤产品常数 ⇒ 等式红在 19px；M578/M579 各放宽尺子的一道地板 ⇒ 真值表红；
      M580 把参照物换成常量 0 ⇒ 正对照那一格红（拦"参照点选错=假绿"）。
    ⑥ **仍然欠真机那一格**（本单开场列的 ①）：非 key 窗口下没有焦点环，所以"12.5 是不是肉眼看到的框的左边"
      这一格在真机上仍未判 —— 但**它不再影响这一改的成立**：等式的两边现在都是同一张帧上的可见物，
      焦点环只会让框更明显，不会把 22.0 挪回去。真机那一格并进批次 82。
    ⑦ 判据为什么走 PNG 而不是 R67 那条 alpha 通道，记在 U-314（第一版判据红在"搜索那一行一个像素都没有"）。

149. **真机观测通道在 R100 中途打开了：截图与 AX 都通了，但"切分区"这一格还不通**（R100 开 / 与 126、130、139、批次 78.6 同族）：
    本轮起因是另一件事：在屏那一卷里 `testFrameIntervalsUnderStateChanges` 从 R99 的 **skipped**
    变成 R100 的 **passed**（同一台机器、两轮之间产品零改动）。它的 skip 条件是
    `baseline.n == 0`（`UIInteractionProbeTests.swift:287`，注释写着"CADisplayLink 在显示器睡着时…"）
    ⇒ 显示器醒了。顺手试 `screencapture -x`：**2940×1912，115080 个采样点里非黑 114737（99.7%）**
    —— 而批次 78.6 记的那次是"尺寸正确但全黑"。也就是说挡了约十轮的
    **126 / 130 / 79.1 的前提没了**。
    已经真做掉的（都只截设置窗口那块区域，主窗口里是用户真实剪贴板内容，**一律不入镜、不入仓**）：
    ① AX 走状态菜单：`menu bar 2 item 1` → 15 个菜单项 → 按标题匹配"设置"并点击（**只比较标题、不打印标题**，
      因为那个菜单里会出现用户剪贴板原文）→ 设置窗口真的开了（`设置` 375,101 720x572）；
    ② `AXRaise` 把它提到主窗口之上再截 —— 不 raise 的话主窗口压在它上面，截到的是用户内容；
    ③ 真机暗档下侧栏选中那颗胶囊是**强调蓝底 + 蓝字**（**这是看图看出来的，不是量出来的**，
      见下面那条"量它失败了"），而离屏帧里是浅蓝底 + 深字
      ⇒ 与 130 那条"accent 派生色在离屏通道不解析"的假设同向，但**证据等级只是肉眼**；
    ④ 真机上卡片材质看得见（页面底 38 / 卡片 54，差 **16**），离屏帧同一处差只有 **7**
      ⇒ 离屏通道**压缩了材质对比度**。这条对 147 有直接含义：runner 上那个 ≤3 很可能就是
      "通道不合成材质"那一端，而不是产品没有卡片。
    ⑤ 真机状态菜单**自己的几何**（AX 直接读那一个 menu，配方与注意项都在
      `.scratch/motion-audit-2/r100_menu_geom.applescript`）：
      `pos=1073,34 size=207x294`、15 项。⇒ 复刻夹具 `menubar-*` 那 **320pt** 的宽第一次有了对面那个数
      （207 vs 320，差 1.55 倍）。**这一条不改规矩**：`menuSurfaceReplicaFixtures` 与
      `testMenuBarFramesAreReplicasOfTheMenuSurface` 早就声明这类帧不许判宽度/截断/对齐/命中区。
      要做的是补**对面那个数**：那处注释今天有复刻体自己的 `320`（R34 实测"墨画到 x=320.0"），
      但没有真机那一边 ⇒ "这是复刻"这句话一直只有一单边有据，R101 把 207 写进去、出处写这条。
      通道边界也一起记：NSMenu 在跟踪期间拿不到**逐项**几何（只能拿到整块 menu 的），
      所以"某一项文案是否被截断"这类问题这条通道答不了；菜单是否已关闭也读不出来
      （AX 的 `visible` 在这块拿不到值 ⇒ 批次 79.4 只能把它写成"未能证明"）。
    **还不通的那一格**：`click at {x,y}` 打到侧栏行的坐标，AX 返回了那个 group，但**分区没换**
    （两张截图 md5 一模一样：`87f247ce…`）⇒ SwiftUI `List` 的选中要真的鼠标事件，
    坐标点击喂不进去。所以 139（勾选框是不是强调色）与 130 的"清空那颗红"仍然没量到 ——
    它们需要的是**换分区**，不是换窗口。
    **下一轮怎么补**：① 把仓库里那颗尺改成能吃"任意 PNG 路径"，拿真机截图跑一遍
      （本轮试过一把 /tmp 手搓尺，读出 `内缩 2.5pt`、patch 众数自相矛盾 ⇒ 那个数不作证，
      这正是"临时尺只配形成问题"的第 N 次）；② 换分区改用键盘：先 `AXRaise`，
      再给侧栏发方向键（`key code 125`）或 Tab 过去 —— 侧栏是 List，`onMoveCommand` 已经接了方向键；
      所以"这一格现在能用了"这句话**每一轮都要重新量**，不要引用上一轮。
    **R101 更正（这条的开单前提翻了一次）**：本轮电池里
    `testFrameIntervalsUnderStateChanges` 又回到 **skipped** ——
    而它自己打的读数是 `FRAME_CHANNEL baseline_n=0 screen=有`。
    ⇒ 两件事被 R100 混成了一件：**屏幕在**（`screencapture` 可用，上面 ①–⑤ 那些证据仍然成立）
    与 **CADisplayLink 有刷新**（0.6s 空转里一帧都没发 ⇒ 这一格没跑）。
    所以"真机通道开了"要说成两句：截图/AX 那条**通**，帧时钟那条**在翻脸**
    （R99 skip、R100 pass、R101 skip —— 两个数据点，产品零改动）。
    ⇒ 下面第 ③ 句"通道随时可能再关"比 R100 写的时候更硬：它不是"可能"，是**已经关过一次**，
    而且关的时候屏幕是亮着的。以后引用这条之前先读当轮那行 `FRAME_CHANNEL`。

    **R132 追记（「切分区」这一格打通了，但不是靠辅助功能）**：本条记的"切分区还不通"今天被绕过 ——
    这扇 SwiftUI 窗口在 System Events 里的树只有 `group / splitter group / button`，`name` 全是 `missing value`
    （整棵树里唯一有名的是窗口标题那枚 static text），所以"按名字 AXPress"这条路**不通**（实测返回 `NO_ROW`）。
    通的是另一条：按**坐标**点，且落地与否不靠"内容区变了"来猜，而靠同一帧里侧栏选中那一行（强调蓝药丸）
    的中心有没有移动到目标行中心来验收 —— 实测 `点击前药丸=50.5pt 点击后药丸=82.0pt 目标=88.0pt ⇒ moved`。
    ⇒ 149 的"切分区"从"不通"改成"按坐标可通、按名字不通"，真机观测通道因此能回答 139 这种问题。
150. **runner 上"设置窗口的卡片没有材质、独立窗口的 `GroupBox` 有"—— 这一条差把 147 从"通道盲区"变成"可做的实验"**（R101 开 / 与 147、128、R28b、36 同族）：
    147 结案时留下的最硬的一条读数：同一台 runner、同一次 run 里，
    `cardprobe-groupbox-default`（一个裸 `GroupBox` 装在 `WindowGroup` 风格的夹具窗口里）**亮档量得出材质**，
    `CARD_INSET cardprobe-groupbox-default light … 内缩=6.0pt`（与本机 5.0/5.5 同一档量级），
    而 `settings-*` 那 24 格被告**逐格都是**`前三=(236:480)` —— 整带只剩页底一个色档。
    ⇒ 不是"CI 那台机器不画 `GroupBox` 的材质层"，是"**这扇设置窗口**里的卡片不画"。
    **为什么这条值得单独开而不是并进 147**：147 的处置是"登记成只有本机能判"，那是**接受**这个差；
    而这一条说差有边界、有对照、有方向 —— 接受一个还能查的差，就是把一条判据永久降级。
    **下一次要做的实验（一次就能出结论，成本是一次 CI）**：
    给参照夹具再加一臂 —— 把同一个 `GroupBox { Text }` 装进**与设置页同一个容器**里
    （`Form { … }`，或 `NavigationSplitView` 的 detail 侧），其余坐标、门限、尺全部不动。
    **R102 更正（这条做法里 `Form` 那一半是猜的，而猜错了）**：这扇设置窗口**没有 `Form`** ——
    `SettingsView.settingsContent` 是 `NavigationSplitView { SettingsSidebarView } detail: { ScrollView { VStack(spacing:20) { 分区 } } }`
    （macOS 12 那一臂是 `CompatibleSplitView`）。装进 `Form` 的实验做完了也不能回答本条问的问题。
    ⇒ 本轮把它做成**容器梯子**（臂 0 裸 `GroupBox` / 臂 1 加 `ScrollView` / 臂 2 加真分栏与真侧栏，
    夹具 `cardprobe-scroll-groupbox`、`cardprobe-split-groupbox`，帧 130 → **134**），
    每一臂打一行 `CARD_PROBE_ARM`（材质 / 卡片段 / **墨行** / 带子 / 前三名）。
    **本机预检已过**：三臂全部 `材质=有 卡片段=1`，内缩 5.0（亮）/ 5.5（暗）逐臂相同，
    臂 2 的卡片左沿 172.5pt 与产品卡片的 172.0pt 同一档 ⇒ 梯子问的是同一个对象。
    下面三个分支现在**只等 runner 那一次读数**。
    三种结果各是一条结论：
    ① 装进 `Form` 之后 runner 上也没材质 ⇒ **容器**是成因（`Form`/`List` 在 1x 光栅下不合成那层材质），
      那么这一族的"只有本机能判"要改写成"依赖 `Form` 的判据只有本机能判"，
      并且给设置窗口找一条不依赖材质的左轴有了明确对象（内部左轴先例：R26）；
    ② 装进 `Form` 之后仍有材质 ⇒ 成因在设置窗口**别处**（侧栏？窗口样式？`Settings` 场景的容器？），
      下一步换一臂只加侧栏不加 `Form`，二分它；
    ③ 参照两臂在 runner 上都没材质 ⇒ 147 那条"参照有"的读数是别的格子贡献的，
      先回头核对是哪两格有材质（这一格本轮没能从日志里唯一定位 —— 见下面那条诚实记账）。
    **诚实记账（这条开单的根据里有一格没钉死）**：runner 那一次报的是
    `候选=26 有材质=2 量到=0 未判=25`。26 − 25 = 1，而"有材质"数出来是 2 ⇒
    两格里有一格**有材质却没进 `measured`**（它declined 在后面的"读不到左沿/读不到墨"那一档），
    而它印在 `CARD_INSET_DECLINED` 里的原因是"这一带读不到卡片"——**两个字段自相矛盾**。
    本轮没有为这一格加打印，所以"参照亮档有材质"这条根据只到 `CARD_INSET` 那一行为止是硬的，
    第二格是谁不硬。⇒ 做上面那个实验之前，先把"有材质但未量到"的那一格点名打出来
    （一行 print 的事，且它同时是 147 与 150 共用的通道）。
    **R101 收尾时把那一行 print 找到了，它比"没打"更微妙**：`CARD_INSET_DECLINED` 早就有
    （`UICaptureHarness.swift:6601`，本机 `未判=0` 所以它一个字都不打），
    但 6549 那一格写的是 `guard fill >= 0, let first = cardSegments(...).first else { declined.append("…=这一带读不到卡片") }`
    —— **两个不同的成因共用同一句话**：① `fill < 0`（这一带根本没有第二层），
    ② `fill >= 0` 但 `cardSegments` 找不到段（**有材质却没量到卡片**，正是上面那个自相矛盾的形状）。
    所以 runner 上"有材质却 declined"的那一格印出来的原因恰好是假的那一句。
    ⇒ R102 的动作很小但必须是两处：把这一句按 `fill` 拆成两条不同的原因，并给原因串带上角色
    （`参照` / `被告`）。拆完再跑一次 CI，150 的三个分支才有资格判。
    **R102 已做完**：横向那格的 `declined` 现在分两条
    （`…[参照/被告]=这一带没有第二层（fill=-1）` 与 `…=有材质但找不到卡片段（fill=N）`），
    并且每一臂另有 `CARD_PROBE_ARM` 一行。牙的实情记在 M570：
    **没有任何断言读这些字符串 ⇒ 这一格在本机无判别力，它的牙在 runner 上人读那几行。**
    **R103 追记（本条从"等读数"变成"等一次修好证人之后的读数"）**：run `38958447236` 里六臂读数是
    亮档臂 0/1 `材质=有 卡片段=1 墨行=11`、亮档臂 2 与暗档三臂 `墨行=0`（四朵红，见 `.scratch/motion-audit-2/r102_ci_readings.md`）。
    查到底发现**红的不是容器，是这一行证人**：`墨行` 当时写的是 `rows.filter { $0 == .ink }.count`，
    而 `rows` 来自 `cardRowKinds` —— 那是**材质那条通道**的中间量，`fill < 0` 时整带交回 `.outside`
    ⇒ 证人在"判据说没有材质"的那一臂里**结构上必然**报 0。
    于是本条原本设计的那道闸门恰好对**它要防的那种假答案**永远闭嘴：
    臂 2 的 `材质=无` 是本条三个分支里最想要的那个答案，而它是唯一一格证人不可能亮的位置。
    ⇒ R103 的修法（证人自己扫字节的存在性判据 + 参考条反方向断言 + 四刀变异表 r103）已落盘，
    **本条仍不结案**：答案要等下一次的 runner 读数，而读数还没回来。
    **R104 追记（读数回来了，答案与 150 原来猜的三个分支都不一样）**：run `38967377231` 的六行
    `CARD_PROBE_ARM`（全文 `.scratch/motion-audit-2/r103_ci_readings_v2.md`）给出：
    ① 臂 1 与臂 0 在两档逐字同读数 ⇒ **`ScrollView` 不吃材质**（分支①的前半被否）；
    ② 臂 2 在两档都是 `墨像素=0`、`最大偏离=0/2` ⇒ **那条带子里一个像素都不离底**，
      也就是臂 2 在那台机器上**根本没有对象**（不是"材质被吃掉"）⇒ 分支③成立，且它卡住了整条二分；
    ③ 被告 24 格照旧无材质（`候选=30 有材质=4（被告=0 参照=4）`）。
    ⇒ 本条的"容器"这一支**改写成等 157**：先量清臂 2 在 runner 上画了什么（侧栏列宽？detail 是不是 0 宽？），
    再谈哪一层吃掉材质。范围这次确实收窄了：不是 `GroupBox`、不是 `ScrollView`。

151. **【结案 · R102】同一张帧上，两把尺把"页面底/卡片底"量成两个数（各差 2–3 灰阶），而本轮的视觉结论同时引用了它们**（R101 开 / 与 104、R68 那一族"证人要与它作证的判据同一颗尺子"同族）：
    本轮收尾把 §4 那组灰阶重做成仓库里的尺（`.scratch/motion-audit-2/r101_luma.py`，
    跑在与帧基线逐字节相同的那一版帧上）时，两把尺各自报：
    判据 `CARD_BAND settings-stats-populated light 页底=252 填充=244`、`dark 28 / 36`；
    python 尺 `light (255, 247)`、`dark (30, 37)`。⇒ **亮档差 3、暗档差 2，两个方向一致**。
    先试的解释是"采样区混进了侧栏那一列"，**实测否掉了**：
    把采样左沿从 150pt 挪到 172pt，页面底众数一动不动（255 / 30）。
    本轮**没有**继续查（也**没有**为此改任何判据），因为结论一侧两把尺说的是同一件事
    （卡片边界 0.031/0.027 < 空格边界 0.047/0.043 < 色档边界 0.115/0.099）。
    **为什么这仍然要单独开一条**：台账里"卡片 vs 页面底差 8 灰阶"这句话以后会被引用，
    而现在有两条通道都能声称自己是那个 8；一旦哪天其中一条被改（比如判据换了众数的取样带），
    另一条不会红，读者也不会知道它们曾经不一致 —— 这正是 R104/D-162 那一族
    "读数没有作者"的形状。
    **下一次要做的（一次就能收口，成本几乎为零）**：
    ① 读 `cardFill` / `CARD_BAND` 那一段，写清楚它的"页底"到底取的是哪一带、
      是众数还是均值（现在只有 python 尺那一侧的定义写在脚本里）；
    ② 给 `r101_luma.py` 加一条**等式自检**：它算出的 (页面底, 卡片底) 必须等于
      同一遍 `CARD_BAND` 打印的那一对，不等就非 0 退出并打印两侧 ——
      这样两把尺要么一致，要么**响**，不会安静地各说各话；
    ③ 若两条定义本就该不同（例如判据的带子含窗口圆角那一行），把这个差**写进两边的注释**，
      并把台账里所有灰阶句子改成点名尺子（本轮 §4 已经这么做了）。
    结案动作（都做完了）：脚本 `.scratch/motion-audit-2/r101_luma.py` 换成判据那颗权重，
    并新增 `--judge` 等式自检 —— **逐字复现** `CARD_BAND` 打的那一对，不等就非 0 退出
    （本机 `LUMA_RECONCILE=ok`、exit 0）。⇒ 151 原本要求的"要么一致、要么响"这一格落地。
    顺带把 R101 §4 那组数第三次微调（空格 亮 13→12、最近色档 亮 27→26 / 暗 13→14）：
    **结论一侧仍然没变**（卡片 0.031/0.027 仍是这一屏最弱的边界），但从今往后只有一个版本有效。

152. **如果容器梯子三臂在 runner 上都有材质，147 的"只有本机能判"就要换个问法**（R102 开 / 与 147、150 同族）：
    150 的三分支里第三条（三臂全有 ⇒ 容器不是成因）留下的下一步没有着落。
    那时剩下的嫌疑只有：`Settings` 场景本身、fixture 窗口与真设置窗口的差异（`cacheDisplay` 的
    渲染路径、窗口样式、是否 key 窗）、或 runner 的显示管线。
    ⇒ 那时候要做的不是再猜一层容器，而是**换问的对象**：
    把同一棵视图树分别用"设置场景"与"夹具窗口"各拍一次，比较两次的 `CARD_BAND`。
    现在不开实验、只登记，因为它的成本与前置都依赖 150 先出结果。

153. **竖向判据里还有没有别的"无条件断言"？本轮只修了撞上的那一格**（R102 开 / 与 147、D-164、D-166 同族）：
    R101 的 `settings-stats 必须 1 段` 是**这一格**被 runner 抓到；同一函数里还有
    `aboveRoster` 地板、`declined` 上限、边距 `>= 10.0` 三处，它们各自有没有"这台机器读不到材质"的前提？
    本轮读过：地板与上限都从 `materialCells` 推（有前提），边距那一格在 `segments` 非空时才跑（有前提）
    ⇒ **今天没有第二格无条件**。但这是**一次人工通读**的结论，不是判据；
    下一次动这个函数时要把它重做一遍（或者把它做成一条守卫：任何 `XCTAssert*` 若在循环之内，
    必须先看见 `fill >= 0` 或 `materialCells` —— 目前还没有能表达这条的机器形式）。
154. **帧基线不分操作系统版本，而臂 2 那张夹具是 macOS 13+ 才建的 ⇒ 在 12 上跑捕获会报「缺 2 张」**（R102 开 / 与 147、150、U-285 同族，**通道账，不是产品缺陷**）：
    实测到的三件事：① `docs/frame_baseline.json` 今天 134 条（`git show HEAD:` 那份是 130 条，
    本轮新增 4 条 = `cardprobe-scroll-groupbox` 与 `cardprobe-split-groupbox` × 亮暗）；
    ② 其中**只有 `cardprobe-split-groupbox-*` 这两张**受版本门控 —— 夹具在
    `UICaptureHarness.swift:3390` 的 `if #available(macOS 13.0, *)` 里才 append，
    而判据那一侧的名册守卫（`:6714`）**跟着同一个门** ⇒ 判据在 12 上不会误报，这是本轮做对的一半；
    ③ `scripts/frame_baseline.py check` 没有"按版本 / 按档位"这一维，白名单只有两张
    （`.github/workflows/ci.yml:362-363` 的 `--allow-missing content-wide-1100x800-{light,dark}.png`）。
    ⇒ 推论（**没有实测过，这台机器是 27、runner 是 15，谁都没有 12**）：真在 macOS 12 上跑一次捕获，
    `check` 会报 `MISSING=2` 并红，而那两张帧"不存在"是**正确行为**。
    三条候选修法，等能真跑 12 的那天再定（不要现在猜）：
    (a) 白名单按版本推导（与 `:6714` 用同一个条件，两边由两条式子算出 = 恒等式，R99 那一族）；
    (b) 基线按 OS 大版本分表（代价：多一份表、每次改界面要 update 两处）；
    (c) 把臂 2 从**帧基线**里摘掉，只留作判据夹具（它存在的意义是回答 150，不是给人看的图）。
    **这一条不许被写成"已修"**：它今天没有红过，它是一格**形状**上的缺口；
    引用它之前先看当轮有没有真的在 12 上跑过捕获（U-285 的教训：「这次通了」不是一张长期通行证）。

155. **运动地板那把尺在 runner 上自己红了：带捕获之后整卷中位间隔从 23.48ms 涨到 32.19ms**（R103 开 / 与 77 路 a、R55 的抓帧成本归因、147 同族，**判据账，不是产品缺陷**）：
    读 R102 的 CI（run `38958447236` 步骤 16）拿到的原文：
    `testBandCaptureIsCheaperAndStillSeesTheMotion: XCTAssertLessThanOrEqual failed:
    ("32.19") is greater than ("23.48") - 带捕获之后整卷中位间隔没有变细 ⇒ 省下的钱没进采样率，这一臂仍然判不了`。
    这条是 R57（BACKLOG 77 路 a）装的地板：**省下的抓帧成本必须换成采样率**，否则那一次优化没有产物。
    它比的是**同一卷里两个臂的中位间隔**，而地板那一侧（23.48）来自不带带的对照臂 ⇒
    两种读法都还没被排除：① runner 上带捕获那一臂真的更慢（那 R57 的结论只在成立在本机，要分开记账）；
    ② runner 的整体调度把两臂都拖慢了而比值不变（那这条判据在 CI 上量的不是它声称的东西）。
    **本轮不动它**（证人那一支已经是一件事，两件事一起改就分不出是谁的功劳 —— R87 那条分配规则），
    下一步先问"它在 runner 上到底为什么"：按 147/146 那一族的做法，把两个臂的**绝对**间隔与各自动机信息
    打进行内读数（现在只打了比值），一次 CI 就能分清 ① 与 ②。
    **R104 更正（本条开单时把一次样本说成了稳定）**：R103 那一版推上去之后（run `38967377231`）
    步骤 16 **没有红**。⇒ 它不是"runner 上稳定红"，是**同一版两遍之间会翻**的偶发红，
    而这恰好是本条 ② 那一读法（调度把两臂一起拖慢）的一个证据方向。
    处置：先要一次"同一版重跑两遍"的分布，再谈成因 —— 不许再把它写成"runner 上红着"（U-317）。
    **R130 追记 2（仪器已就位，本机第一跑就有结论，但 runner 的那一行还没到手）**：
    `MotionFilmstripTests.bandIntervalFacts` 现在把 **间隔 − 抓帧 = 调度地板** 打进 `MOTION_BAND_INTERVAL`，
    并带机器键（与 171 同形）。本机：`带间隔=9.27 整窗间隔=43.16 带抓帧=4.24 整窗抓帧=38.17 ｜ 带地板=5.03 整窗地板=4.99 谁细=带`
    ⇒ 在这台机器上 ② 被排除（两臂地板差 0.04ms，间隔差完全由抓帧解释）。**这条不外推到 runner**：
    下一次 CI 只要看同一行的两个地板 —— 若两臂地板都远大于本机那 5ms 且彼此接近，② 成立（这条判据在 CI 上量的不是它声称的东西）；
    若带的地板明显大于整窗的，① 成立（带捕获那一臂在那台机器上真的更慢，R57 的结论要按机器分开记）。
    仍不动阈值、不用 `suite_reds` 登记绕过（那条路被 `test_motion_floor_gate.py` 钉成空表）。
    **R129 追记（本条还活着，而且我上一批账本把它说没了）**：`gh run view --log-failed` 三跑原文 ——
    `39031123341`（R124）`28.44 > 25.38`、`39032407018`（R125）`32.49 > 27.46`、`39033755171`（R126）`32.16 > 31.81`。
    ⇒ ① 它不是"偶发翻红"，是**连续三跑都红**（R104 那句更正按这一批证据要再更正一次：偶发的判断来自一次没红的样本，样本不够）；
    ② 两臂的**绝对**中位间隔都在 25–32ms 这一档，而本机带捕获那一臂能到 9ms ⇒ ② 那一读法（runner 的调度把两臂一起拖住，
    所以这条判据在 CI 上量的不是它声称的东西）第一次有了数，但仍然没被**证实**：两臂谁慢与机器身份没打在行内。
    ③ 差值从 +12% → +18% → +1% 在收窄，说明这是一条**贴着阈值翻**的判据，任何一侧的噪声都能决定结论。
    下一轮（不改阈值、不用 `suite_reds` 登记绕过 —— 那条路被 `test_motion_floor_gate.py` 钉死为空表）：
    把两臂的绝对间隔、抓帧中位、以及机器键（`arm64/macOS x.y/Nx`，与 171 同一把键）打进行内读数，
    一次 CI 就能把 ① 与 ② 分开。

    **R132 追记 3（runner 的两个地板到手了 —— ② 那一条第一次有了测量支撑，而这一跑 ⑤ 恰好是绿的）**：
    run `39036587208`（R130 那一跑，job=**success**）步骤 `Motion filmstrip (report-only)` 原文：
    `MOTION_BAND_INTERVAL 机器=arm64/macOS 15.7/1x 带间隔=26.72ms 整窗间隔=38.44ms 带抓帧=5.44ms 整窗抓帧=15.07ms ｜ 带地板=21.27ms 整窗地板=23.37ms 谁细=带`，
    同一次 run 的 `Motion coverage floor` 报 `MOTION_FLOOR_REDS=0 红的用例=-`。⇒ 三件事一次说清：
    ① **这台机器的调度地板是 21.3 / 23.4ms**，是本机（5.03 / 4.99ms）的 4 倍以上，而两臂地板只差 2.1ms；
    ② 抓帧确实省了（5.44 对 15.07，2.77×），间隔也确实细了（26.72 对 38.44）⇒ 这一跑 ⑤ 判"通过"；
    ③ 但**间隔里 80% 是调度**（21.3/26.7 与 23.4/38.4），胜负由剩下那 20% 决定 ⇒ 前面三跑（28.44>25.38、32.49>27.46、32.16>31.81）
    与这一跑的差别不需要产品变任何东西就能翻面 —— 本条 ② 那个读法（这条判据在 CI 上量的不是它声称的东西）
    第一次被**同一把尺自己印出的数**支持，而不是被我的推断支持。
    ⇒ 处置另开一条（174）：把 ⑤ 改成"地板主导时报成有名字的未覆盖"，走 `MOTION_NOT_RUN` 那条已登记的通道，
    **不许**动阈值、**不许**用 `suite_reds` 登记绕过（那张表被 `test_motion_floor_gate.py` 钉成空表）。
    本条本身仍不结案：它要的"① 还是 ②"现在有了答案（②），但那条答案要落到判据上才算还完。
    （R104 那句"不许再把它写成 runner 上红着"仍然有效：四跑是三红一绿，红不是恒常的。）
 `材质=有 卡片段=0` 说：`cardRun` 那一格（"这行还在卡片里吗"）在那台机器上是抛硬币**（R103 开 / 与 147、150、D-155 同族，**判据账**）：
    R102 的读数里暗档臂 0 同时报了这两件事：`cardFill` 按"整带有 ≥20 行同一个色档"认出了卡片（`材质=有`），
    而 `cardSegments` 找不到**任何一段**（`卡片段=0`）。后者要求"某一行里最长一段'更像卡片而不像页面'的像素 ≥ 带宽 30%"，
    而那台机器上 `页底=52 卡片=60` —— **两个参照只差 8 个灰阶**，逐像素判"更像谁"就在 56 那条线两侧翻。
    本机同一把尺在同一档外观（`页底=28 卡片=36`，也是差 8）给的是 `卡片段=1`，
    所以这不是门限写错，是**那台机器的暗档材质层带噪声**（1x 光栅 + 抖动），
    差 8 的分离量喂不饱一颗逐像素的比较器。
    ⇒ 后果比"参照臂读不到段"更大：设置窗口那 24 格被告的**竖向节奏与横向内缩**两条判据都吃 `cardSegments`，
    它们在 runner 上的 declined 有一部分成因是这一格，而不是 147 说的"整带只有页底一个色档"。
    R103 只把**证人**从这条通道上摘了下来（见 150 追记），判据本体还在上面。
    三条候选（都不许在没实测之前动产品）：
    (a) 把 `cardRun` 的判据从"逐像素比谁近"换成"逐像素离页底 ≥N 且离卡片 ≤M"（把 8 那一档的噪声显式吃掉，
        N/M 要在这台机器上量，不能凭印象 —— 与 `testTextInkGateTruthTable` 同一规矩）；
    (b) 用整带众数档做**行级**判定（`modals[i] == fill` 就算这行在卡片里），代价是被字打断的行会掉；
    (c) 接受"runner 上这两条判据没有对象"，把它并进 147 的处置（那 150 的"容器"分支也只能靠参照臂读）。
    **本条不许写成已修**：它现在是一格形状上的缺口，今天没有为它红过。

    **R136 结案（② 成立，而修法不是调阈值）**：本条从 R103 开到今天，四种处置都被逐一排除 ——
    "runner 上稳定红"（R104 撤回：四跑三红一绿）、"带那一臂真的更慢"（①，被 R136 的读数排除）、
    "登记成已知红"（`suite_reds` 被自检钉成空表，走不通）、"调阈值"（会把判据改成它声称之外的东西）。
    最后落在这一步：给判据加第三个出口，前提由同一次运行量出来的 `min(两臂地板) > 两臂抓帧差` 决定
    （runner 22.13 > 5.64 ⇒ 判不了；本机 4.99 < 33.93 ⇒ 照判）。
    ⇒ 本条与 174 同批结案；留下的耐久事实是这条判据**按机器分范围**，跨机器的地板不许互借（R38 / D-155 同一族）。
    **样本口径**：runner 这条读数只有一跑。R87 那条"单遍读数不配给产品定罪"在这里不挡结论，
    因为它不给产品定罪、只给判据划范围 —— 这一点写进结案理由，而不是混过去。

157. **臂 2（`NavigationSplitView` + 真侧栏 + `ScrollView` + `GroupBox`）在 runner 上整条扫描带是空的：一个像素都不离底**（R104 开 / 与 150、147、128、R28b 同族，**通道账**）：
    开场读数就是 R103 那一遍 CI 的两行（`.scratch/motion-audit-2/r103_ci_readings_v2.md` ② 的第 2 条）：
    ```
    cardprobe-split-groupbox light 材质=无 卡片段=-1 墨行=0 墨像素=0 最大偏离=0 带子=170..720pt 页底=236 前三=(236:100)
    cardprobe-split-groupbox dark  材质=无 卡片段=-1 墨行=0 墨像素=0 最大偏离=2 带子=170..720pt 页底=52 前三=(52:100)
    ```
    带子里 **100 行全是页底一个色档**（`前三` 只有一项），而臂 0/1 在同一台机器、同一次 run 里
    是 `(236:74) (228:24) (220:2)` ⇒ 不是"颜色不显"，是**那一片根本没画东西**。
    三种成因都值得查，而且各自要的东西不同：
    ① 详情列在那台机器上被排成 0 宽（`navigationSplitViewColumnWidth(min:ideal:max:180)` 与 1x 光栅的交互）
      ⇒ 那 170..720 就落在侧栏之外、内容之外；
    ② `NavigationSplitView` 在非 key 的离屏窗口里延迟建视图（R19/R63 那一族：离屏通道的边界）
      ⇒ 那是**捕获通道**的问题，150 的臂 2 在这台机器上永远没有对象；
    ③ 它真的画了一整片页底（detail 背景盖住了卡片）⇒ 那才是 150 要的"容器吃掉材质"。
    **下一次要做的实验（一次 CI 就分得开，别再靠猜）**：臂 2 另打两行读数——
    (a) 详情列的**整列**包围盒（把 `SettingsSidebarView` 那一列的宽度与 detail 的宽度直接打出来，
        走 `frame(in:)` 而不是像素）；(b) 把带子换成**整窗**（x 0..720）再打一次 `墨行/最大偏离`。
    (a) 判 ①，(b) 判 ②/③：整窗有墨而带子没墨 ⇒ 东西画在别处（带子错）；整窗也没墨 ⇒ 那台机器上这棵视图没画。
    **本条不许写成已修，也不许在它之前动产品**：150 的"哪一层容器"这一支现在就卡在这里。

158. **runner 上快速选择浮层的占位语一个像素都不落地：等式的另一边在那台机器上不存在**（R105 开 / 与 147、150、157、130、R28b 同族，**通道账**）：
    开场事实来自读 R104 的 CI（run `38975204376`，本条就是那一跑里唯一的新红）：
    ```
    UICaptureHarness.swift:572: error: … testQuickPickSearchLineSharesTheRowsColumn :
      failed - light：搜索那一条带（y=0..44px）里一个墨像素都没有
    ```
    同一跑里参照物那一侧**是好的**：药丸左沿两档都读得到（否则红会先在正对照那一格），
    而 `QUICKPICK_ROW_AXIS` 那一行在 runner 上照旧打得出（行标签/图标的视图树读数正常）。
    ⇒ 坏的不是整张帧、不是布局，是**浮层那一行字在那台机器上没画出来**（或画得低于 60 灰阶的门限）。
    三种成因都还开着，本条不猜：
    ① 占位语在**非 key 窗口**上就不画（`placeholderString` 的绘制路径与 first responder 有关）——
      那么它与 130/139 那一族同源（离屏通道的 key 态盲区），而且**产品真机上是好的**；
    ② runner 的 1x 光栅 + 该档字色让占位语与面板底差低于 60 —— 那是**门限跨机器不成立**，
      与 148 的 R102 追记 ① 同一族（那道 40 的悬崖）；
    ③ 那张夹具帧在 runner 上整条上部带子没画（布局/滚动视图那一条），
      那 158 就并回 157（同一台机器上另一棵视图也没画东西）。
    **R105 已经做的**：判据不再红，改成 D-166 的形状 ——
    `QUICKPICK_AXIS_CAPABILITY 候选=N 有对象=M 未判=K` + `QUICKPICK_AXIS_DECLINED …（带内墨行/墨像素/**最大偏离**）`，
    全都没有对象 ⇒ `XCTSkip`，而"有对象却有一档没判"仍然红。
    下一轮（R106）要做的**一次 CI 就能分成因**：那一行现在带着 `最大偏离` 与带子高度，
    ① 与 ③ 会让 `最大偏离` 很小（≤ 几），②会让它落在 20~59 之间；
    而带子高度（本机 90px 对 runner 44px）本身就是"两机倍率不同"的读数，能排除"带子算错"这一种。
    **本条不许写成已修**：产品侧什么都没改，改的是判据的收场形状；148 那条结案**不撤回**
    （本机两档 差=1px 是产品事实），但"CI 绿"这句话在 158 判清之前对浮层这一格不成立。

159. **两张"名字叫 typed / empty"的浮层帧里画着一块真实使用里不存在的灰色选中底：帧基线把假象钉了 40 多轮**（R105 开 / 与 R63 那一族（名字叫 typed、内容是 empty）、130/139（离屏 key 态盲区）、U-315（我以为的尺的行为）同族，**夹具忠实性账**）：
    开场事实来自本轮 §4 看图，不是读数 —— 我把 `quickpick-typed` / `quickpick-empty` 顶部 0..70pt 放大三倍看，
    搜索那一行字底下有一块**实心灰矩形**。第一眼我读成"只选中了「zzz 」那半截"（U-324：看图会看错），
    同一颗尺量出来是**整条查询都被选中**（U-325：读数纠正了看图）：
    ```
    typed  light/dark  灰块 x=44..95px（22.0..47.5pt）宽 52px=25.5pt  y=24..55px（12.0..27.5pt）高 16pt
    empty  light/dark  灰块 x=44..170px（22.0..85.0pt）宽 127px=63.5pt（同一 y）
    list   （query=""）  没有灰块，只有占位语的墨 x=44..217px
    ```
    宽度与那两串字的排版宽度对得上（「访达」2×13pt≈25.5pt；「zzz 不存在」≈63.5pt），
    两档、两态的**几何完全一致**，只有墨色翻面 ⇒ 它不是渲染噪声，是一个成形的绘制。
    **与 R104 无关，而且反过来给 R104 加了一格证据**：同一颗尺读 R104 之前那批帧
    （`/tmp/r103_shots`）得到 `x=24..75` / `x=24..150` —— 宽度逐像素相同、整体右移 20px=10pt
    ⇒ 这块灰底从 R63 那三张帧进基线起就在，而 R104 的内缩**对选中底也生效**（不只是对字形），
    这比我原来写的"占位语进列"更强：整个字段的绘制矩形都挪了。
    三种成因都还开着，本条不猜：
    ① `windowForCapture` 里 `field?.stringValue = query` 让 cell 带着一个覆盖整串的选中区间，
      而离屏窗口不是 key ⇒ 选中底画成**灰**而不是强调色（产品路径 `show()` 是 `= ""` 且随后
      `panel.makeFirstResponder(field)`，用户逐字敲进去时没有这个区间）；
    ② 字段自己的 `drawsBackground`/高亮态（`isHighlighted`）—— 那它与选中无关，是真机上也会有的东西；
    ③ 单元格在被程序化赋值后进入"编辑中"外观（`currentEditor()` 存在过）。
    **下一次要做的实验（先别动产品，一次跑就分得开）**：
    (a) 在捕获卷的 `inspect:` 钩子里把浮层字段的状态打出来 ——
        `window.firstResponder is NSText`、`(firstResponder as? NSText)?.selectedRange`、
        `field.currentEditor() != nil`、`field.isHighlighted`，四行读数进 `emit`；
        ①会让 `selectedRange.length == 串长`，②/③ 会让它为零而 `isHighlighted`/`currentEditor` 非空。
    (b) 真机那一条（批次 83.1）：热键呼出浮层后输入两个字，看查询串**整条有没有底色**。
        如果真机也有 ⇒ 它不是夹具问题而是"下一次按键会替换掉整个查询"的交互缺陷，优先级立刻升高。
    **为什么这条值得单独开而不并进 149**：① 帧基线的作用是把"正确答案"钉成字节，
      而这两张帧钉进去了一块**产品不会显示**的色块 —— 下一轮任何人读这一条带都会被迫解释它；
    ② R104/R105 的左轴判据正好扫这块地方（药丸之上那一条带），灰底与字的墨在同一个 8..45 灰阶档里，
      我的 `firstInkColumnInStrip` 只是因为它读的是"偏离 >60"才没被它骗到 —— 这是运气不是设计；
    ③ 修法（若 ① 成立）落在 `windowForCapture` 这个**捕获入口**里，产品路径 0 影响，代价是 4 张帧换哈希。
    **本条不许写成已修**：本轮只把它量出来并进了账，产品与夹具代码一行未动。

---

### R106 追记：158 与 159 同一天拿到答案，两个都结案（数字全来自 runner 与本机读数，不是推的）

**158 结案 —— 三成因里的是②：全局地板 60 在另一台机器上不成立，占位语其实画了。**
读 R105 的 CI（run `38984669003`，failure）那两行未判名单：
```
QUICKPICK_SEARCH_AXIS light 药丸左沿=22.0pt 搜索第一列墨=没有 差=- 带子 y=0..44px 带内墨行=0 墨像素=0 最大偏离=58（门限 60） 页底档=236 倍率=1.0x 帧宽=420px
QUICKPICK_SEARCH_AXIS dark  … 最大偏离=49（门限 60） 页底档=52 倍率=1.0x 帧宽=420px
```
`最大偏离` 落在 **58 / 49** —— 正是 R105 §9 预言的"②会让它落在 20~59 之间"那一档，
而 ①/③ 会让它 ≤ 几。⇒ **占位语画了**，只是那台机器面板底更暗（236/52 对本机 252/28），
对比度落在全局地板之下。修法不是把全局地板改低（那会让别的判据一起失去判别力），
而是**这一条带的地板由这一条带自己推出**：`bandFloor = max(20, 带里最大偏离 / 2)`，
带里最大偏离 < 20 才叫"真的什么都没画" ⇒ 不判并点名。
本机两档在新地板下读数不变（`差=1px`，bandFloor 62/63），真值表第 ⑦ 格把"低对比那台必须读到同一列"
钉成合成件（页底 236 / 字 178 ⇒ 偏离 58），并留了反向牙：全局地板下那一块**必须**读不到。
**这一格还欠 runner 的确认**：下一次 CI 的 `QUICKPICK_SEARCH_AXIS … 本条带用 29` 若给出 `差=` 一个数（不是 `-`）⇒ 158 才算在两台机器上都结案。

**159 结案 —— 那块灰底是"字段成为第一响应者时默认全选"，而离屏窗口不是 key 所以底是灰的。**
机制读数（`QUICKPICK_FIELD_STATE`，两档一致）：
```
字段类名=QuickPickSearchField 串长=2 有editor=true editor选中=(0,2) 选中覆盖整串=true
firstResponder=NSTextView firstResponder就是editor=true 窗口是key=false 字段高亮=false 有边框=false 画底色=false
```
⇒ 三种候选里是 ①（cell/字段带着覆盖整串的选中区间），② 被 `字段高亮=false`、`画底色=false` 否掉。
**修在捕获通道而不是产品**：`render` 在拍之前调 `collapsePhantomSelections(in:)`，
与 `silenceCarets` 同族（闪烁的、瞬时的、产品路径上不成立的状态不许进基线）；
产品路径 `show()` 赋的是空串、用户逐字敲，从来没有这一刻 ⇒ **产品代码 0 行改动**。
第一版我把修复写在 `windowForCapture` 里（`panel.firstResponder as? NSText`）—— **那是空操作**，
因为 editor 是在后面的上屏周期里才装上的；同一份读数原样不动才暴露了它（U-330），已回滚。
修后读数：`editor选中=(2,0)`、灰块从 `32 行 / 1115 像素 / 纯灰行最宽 52px` 掉到
`1 行 / 71 像素 / 纯灰行最宽 1px`（亮），暗档 `0 行 / 101 像素 / 0px`；
判据钉的是"纯灰行最宽 ≤ 最宽墨行"（52>36 红、1≤33 绿），四张帧（typed/empty × 两档）换哈希、其余 130 张逐字节不变。
批次 83.1 仍然欠着（真机上打完字查询串有没有底色）—— 那一句问的是产品，而我修的是通道，两件事不能互顶。

**U-333 的账（R106）**：`assertion_containment.py` 的"取断言后第一个字符串"扫的是后 4000 字符，
会越过这一次调用的右括号 ⇒ 本轮只是**插入**了新判据，它就报了 `CONTAINMENT_LOST=1`（pass-2 红）。
已修成按调用自身的括号深度扫描，并复跑它的三条自测（构造丢失被抓 / 改插值不误报 / 少一条同文断言要报）全过。
这一条不开新目（它是工具自己的账，记在这里与 Round 106 §6）。

**158 结案（R106 收尾，读 run `38993610812` = b31ffb5 那一版）—— 两台机器都判到了**：
```
QUICKPICK_SEARCH_AXIS light 药丸左沿=22.0pt 搜索第一列墨=23.0pt 差=1px … 最大偏离=58（全局门限 60，本条带用 29） 页底档=236 倍率=1.0x 帧宽=420px
QUICKPICK_SEARCH_AXIS dark  药丸左沿=22.0pt 搜索第一列墨=23.0pt 差=1px … 最大偏离=49（全局门限 60，本条带用 24） 页底档=52  倍率=1.0x
QUICKPICK_AXIS_CAPABILITY 候选=2 有对象=2 未判=0
```
⇒ D-172 那个"由这一条带自己推地板"的修法在**另一台机器上第一次判到了等式**（本机 `22.5 对 22.0 差 1px`、
runner `23.0 对 22.0 差 1px`，1x 下 1px 就是 1pt 的分辨率）。
同一跑里 `QUICKPICK_FIELD_STATE … editor选中=(2,0) 选中覆盖整串=false` ⇒ **159 的修复在 runner 上也成立**。
`CAPTURE_GATE_CASES passed=52 skipped=11 failed=1 有名字的红=1` ⇒ 现在 runner 上唯一剩下的红
就是那朵按名登记的臂 2 证人（**157**），而 157 那一跑的 `最大偏离是 2 / 0` 是**真的空白**，
不是地板问题（与 158 恰好成对：一个是尺太高看不见，一个是确实没东西）。
**158 结案不撤回"这台机器画得出占位语"那句能力口径** —— 未判守卫仍然只在该机画得出时要求为空。

---

### R107 追记：157 的**实验对象自己**被查到不在帧内（这就是它为什么在 runner 上读 0 行墨）；另开 160

**157 追记（R107）**：本轮把 157 要的两行读数装上并当场用掉 —— 臂 2 的分栏内容盒是 **258pt 高**，
而夹具只给 140pt，包围盒读数（`CARD_PROBE_GEOMETRY`）打的是
`列0:_NSSplitViewItemViewWrapper[顶向下y=-85.0..173.0 高=258.0]`
⇒ 帧看到的是"从一块更高的内容里裁出来的一条窗口"，**而裁在哪儿取决于窗口装饰高度，也就是取决于机器**。
这正好是 157 那一朵红的形状：runner 上 `墨行=0 最大偏离=2`，本机同一臂 `墨行=24 最大偏离=206`，
两句都可以是"容器吃掉材质"，但前一句其实只需要"装饰比本机高 85pt"。
**处置**：臂 2 夹具 720×140 → **720×300**（带子随之放宽到 `24..284pt`），
溢出读数归零（`分栏内容溢出=0.0pt`，改前 85.0），并且**新增一条会红的断言**钉住它
（`splitOverflow ≤ 1pt`，M590 把高度改回 140 就红在 `85.0 > 1.0`）。
另加两行结构读数：`CARD_PROBE_WHOLE`（整窗墨行/墨像素/**最大偏离**）与
`CARD_PROBE_WHOLE_FILL`（整窗材质有无 + 填充行落在哪一段 y），
配一条**尺自检**：整窗包含带子 ⇒ 整窗的极值与墨像素不可能低于带子（M589 把整窗矩形改成 1pt 高就红）。
**下一跑（R107 这次 CI）的判法**：臂 2 若 `整窗材质=有` 且 `整窗填充行y` 与带子相交 ⇒ 容器没吃材质，
150 那一支正式否掉；若 `整窗材质=无` 而 `整窗最大偏离` 也只有个位数 ⇒ 那台机器上这棵树真的没画第二层墨，
并回 147 那一族；若 `分栏内容溢出 > 1pt` ⇒ 红会自己说"实验对象又跑出帧了"，不必再猜。
**本条不许写成已修**：157 的答案在下一跑里，本轮只把"读不到"变成可解释的形状。

**160. 同一棵离屏窗口里，侧栏的选中是**蓝的**而浮层搜索字段的选中是**灰的**：130 / 159 那句"非 key ⇒ 一律灰"太宽**（R107 开 / 与 130、139、159、R76 那一族同源，**通道账**）：
开场事实来自本轮看图（`cardprobe-split-groupbox-720x300-dark.png`，夹具假数据）：
侧栏那一行"通用"的选中底是**强调蓝**（`rgb(28,43,64)` 一档配蓝标签），
而这一臂与浮层用的是**同一个离屏窗口、同一个 `key=false`**（R106 的 159 就是在这样的窗口里读到灰底的）。
⇒ "窗口不是 key 所以选中一律画成灰"这句**不是**一个全局事实，它是**按控件**成立的：
`NSTextField` 的 field editor 走非强调灰，而 SwiftUI `List(selection:)` 的选中行仍然画强调色。
为什么这条值得单独开：① 130 / 148① / 82.2 那几格真机问题问的是"活动与非活动窗口之间那颗蓝会不会变"，
而本轮证明**至少有一个表面在完全非 key 的情况下就已经是蓝的** ⇒ 真机那一格要按表面分开问，
不能一句"非 key ⇒ 灰"打包；② 我上一轮用"非 key"解释 159 的灰底时，隐含假设了这条全局规则 ——
结论没错（那一格确实由 key 态决定），但**理由的边界没量过**。
下一次要做的（不用真机就能做）：在同一棵离屏窗口里，把"侧栏选中行的填充色"与"浮层字段选中底的颜色"
各打一行读数（同一颗尺、同一档外观），把"谁跟着 key 变、谁不跟"钉成一条判据；
真机那一格并进批次 84（见 `docs/MANUAL_TEST_v1.4.9_round3.md`）。


### R108 追记：160 与 161 同日结案，而 157 的 CI 答案落在预登记判法**没列举的那一格**（结案 160、161 / 新开 162 / D-177）

**160 结案（判据 `testSelectionFillUnderInactiveWindowIsPerSurface`）**：两臂同一棵 `key=false` 的离屏窗口、
同一次捕获、同一颗尺（"最长同色段"），本机两档实测：
`SELECTION_CHROMA light 臂=列表 … 最彩段=y=184px 宽=226px rgb(217,229,251) 色度=34` /
`臂=字段 … 最宽无彩段=y=24px 宽=52px rgb(220,220,220) 彩度行=0`（暗档 36 与 `70,70,70` 同形）。
⇒ "非 key ⇒ 选中一律画成灰" **不是全局事实**，它是按控件成立的：
`NSTextField` 的 field editor 走非强调灰，SwiftUI `List(selection:)` 的选中行仍然画强调色。
断言四格各承重（列表段宽 ≥ 地板、列表色度 > 8、字段彩度行 = 0、字段色度 ≤ 8），
能力行 `SELECTION_KEYSTATE_CAPABILITY 候选=2 有对象=2 未判=0` 排在闸门之前（D-170）。
字段那一臂是**刻意把选中装回去**的一臂 —— 它问的是通道（这一刻真的出现时画什么颜色），
不是产品（产品路径 `show()` 赋空串、用户逐字敲，从来没有这一刻，见 159）。
runner 的判法（开跑前写死）：两臂都有对象且形状同本机 ⇒ 160 两台都成立；
列表那侧变成无彩度 ⇒ 读成"两台机器的通道不同"，不许换成"取两臂的比"把它吃掉。

**161 结案**：R106 留下的那 1 个纯灰像素。本轮给 `QUICKPICK_GREY_BAND` 加了 `残余灰=` 一格，实测
亮档 `纯灰行 y=28px x=59..59`、最近墨行 `y=29px`（差 1px）其墨 x 段 `47..86` ⇒ `落在其x内=true`；
暗档 `这一档没有纯灰行`。按开跑前写死的判法 ⇒ **字形自己的抗锯齿边**，判据不必管
（承重的是那条比值判据：1px 对最宽墨行 33px）。

**157 的 CI 答案（run `39002273057`）**：臂 2 换成 720×300 之后第一跑，
`CARD_PROBE_WHOLE cardprobe-split-groupbox light 整窗墨行=70 整窗墨像素=1420 整窗最大偏离=165 带子墨行=0 带子最大偏离=0`、
`CARD_PROBE_WHOLE_FILL … 整窗材质=无 … 分栏内容溢出=0.0pt`。
⇒ 溢出 0（对象在帧内）、整窗有墨（70 行、偏离 165）、带子 0 墨 ——
**这不是"容器吃掉材质"，也不是"这棵树没画第二层"，而是 runner 上臂 2 的详情那一格本来就是空的**
（本机同一臂的详情里画着那颗「分栏详情里」字段，本轮看图确认）。
157 追记里预登记的三条判法没有一条覆盖这个形状 ⇒ 见 **D-177**（预登记必须穷举格子）。

**162. runner 上臂 2 的详情那一格是空的：150 那台实验在 CI 上还没开始跑**（R108 开 / 与 157、150、147、141 同族，**夹具忠实性账**）：
开场事实就是上面那三行读数（整窗 70 行墨、带子 0 行、溢出 0）。
两种解释还没分开：① 详情视图在 runner 上**没被实例化**（`NavigationSplitView` 的 detail 需要 selection 才出内容，
而 selection 在 CI 那台机器上没落到"通用"）；② 详情画了但**位置在带子之外**（x 起点不同 ⇒ 170..720 那条带子又放错了）。
下一次要做的（不用真机）：给臂 2 的**详情列**也打一行包围盒（`CARD_PROBE_GEOMETRY` 已经有两列的 x 段，
本轮缺的是"详情列里到底有没有那颗字段"这一格 ⇒ 把 `firstSpanStart` 那颗尺按列各打一次），
下一跑 CI 就能把 ① 与 ② 分开。**本条不许写成已修**：150 的堵点从"读不到"变成"详情没渲染"，仍然是堵点。


### R109 追记：菜单栏那句理由的前提从没被写下来过（新开 163 / 162 的仪器装上 / D-178）

**R109 补（读 R108 的 CI `39005449295`）：160 在两台机器上结案**。
runner：`SELECTION_KEYSTATE_CAPABILITY 候选=2 有对象=2 未判=0`、
列表 `rgb(198,216,237)` 色度 39（暗 `rgb(17,37,58)` 色度 41）、字段 `rgb(220,220,220)` / `rgb(70,70,70)` 彩度行 0
⇒ 命中开跑前写死的第 ② 格（两台都成立）。闸门 `passed=53 skipped=11 failed=1 有名字的红=1` ⇒ 没有新增红。
另一条通道事实：runner 上 `标题栏底=没有pt`（那台机器的树里没有 `NSTitlebarBackgroundView`）⇒
扫描带起点降级为 0，而**降级在读数里看得见**，所以它没有静默改掉判据的定义。

**162 更新（仪器已装）**：本轮给了臂 2 一行**逐列**的读数
`CARD_PROBE_COLUMNS`（每列：x 段、顶向下 y 段、该列自己的众数页底、墨行、墨像素、最大偏离），
并当场量到"详情那一格在视图树里没有自己的 wrapper"（两块 `_NSSplitViewItemViewWrapper` 是
`x=0.0..148.0` 与 `x=0.0..720.0`）⇒ 详情列只能**推导**（外列 − 侧栏），本机推出来是 `x=148.0..720.0`。
另有一条尺自检钉住"带子必须与详情列有交集"（M596 把带子整个挪进侧栏就红在那里）。
**下一跑（R109 这次 CI）的判法**（按 D-177 把格子列全，不再只列想到的分支）：
| 详情列墨行 | 带子墨行 | 结论 |
|---|---|---|
| 0 | 0 | ① 详情那一格在 runner 上**没被实例化** ⇒ 夹具忠实性账（150 的实验还没开始跑） |
| >0 | 0 | ② 详情画了、带子放错 ⇒ 改 `cardprobeBands`，与容器无关 |
| >0 | >0 | ③ 两台的读数终于可比 ⇒ 157 的"材质"那一半才轮到 150 说话 |
| 尺自检红 | — | ④ 仪器坏了（M596 那一格），先修尺 |
| 列没打出来 | — | ⑤ 我的推导在那台机器上失败（比如侧栏宽度不同或只有一块 wrapper）⇒ 回来改仪器 |

**163. 菜单栏"这里不可能有动画"的理由，前提从来没被写进代码**（R109 开 / 与 D-034、D-055/M15、R74、R43 那族同源，**理由的承重账**）：
`MenuBarRecommendationsView.swift:27` 那句"内容会被编译成真的 `NSMenu`，SwiftUI 的过渡在那一层根本不执行"
是对的（本轮没有推翻它），但它依赖的 `.menuBarExtraStyle` **一次都没出现过** —— 依赖的是 SwiftUI 的默认值。
而钉住这族的守卫 `testNoUnexecutedTransitionClaimsAcrossViews` 数的是"文件里有没有 `animation(`"，
所以"有人把样式换成 `.window` ⇒ 过渡会执行 ⇒ 那句理由失效"这件事**不会让任何一条判据变红**。
本轮的处置：① 把前提写成代码（`App.swift` 里显式 `.menuBarExtraStyle(.menu)`）；
② 新守卫 `testMenuBarSurfaceIdentityIsDeclaredNotInherited` 三格（显式 `.menu` / 挂在 `MenuBarExtra(` 段内 /
整块在 `#available(macOS 13, *)` 内）；③ 变异表 M594（删掉声明）与 M595（换成 `.window`）各钉其中一格。
**顺带一条版本事实进台账**（U-348）：`MenuBarExtra` 在 macOS 12 上**不存在**，
12 上用户看到的菜单是 AppKit 那棵 `MenuBarController` ⇒ 三张 `menubar-*` 帧对面的是 13+ 那一棵，
"菜单栏已逐元素重判"这句话从今天起必须带版本限定（本机 `sw_vers` = 27.0，所以用户那一棵是 `MenuBarExtra`）。

**164. 菜单栏那颗图标在两棵表面上是两副身体（12 手画、13 系统符号）**（R110 开 / 与 D-178、R34 那族同源，**素材身份账**）：
`MenuBarExtra(_, systemImage: "clipboard")` 与 `MenuBarController.makeStatusBarIcon()` 的手画 `NSBezierPath`
没有任何一条线连着。本轮已按 D-179 收成 `MenuBarController.statusSymbolName` 一个常量 + 逐像素判据 +
源码"字面量只许一次" + 两张特写帧（`statusitem-glyph-160x90-{light,dark}`），变异表 r110 四刀全 CAUGHT 之后结案。
**还欠的一格**：12 上真菜单栏里那颗的基线/材质只有真机能看（批次 85），本机分支不执行（U-359）。
判法（先登记再动手）：真机上若与相邻系统图标明显偏大/偏小或垂直不居中 ⇒ 改 `NSStatusItem` 的占位而不是换素材，
并且把 18×18 那一格单独重测。

**165. macOS 12 的菜单会一直挂着「正在整理推荐…」**（R110 开 / 与 164 同形：**两棵表面行为不对等**）：
证据（读代码，非推测）：`populate` 只在 `makeMenu()`（`MenuBarController.swift:66`）与 `menuWillOpen`（`:73`）被调用；
这个文件里没有 `objectWillChange` / 通知订阅；`HistoryStore.refreshPredictions()`（`HistoryStore.swift:199`）
先置 `isRefreshingPredictions = true` 再派后台任务 ⇒ 打开菜单那一刻填的是"正在算"，算完**没有人重填**。
13 的 `MenuBarRecommendationsView` 观察 store，自动更新，所以这一格只有 12 有。
候选修法：① 实现 `menuNeedsUpdate:`（每次要显示前重填，系统菜单的标准做法）；② 订阅刷新收尾后
`populate`（菜单开着时会当场变）。**预登记判法**（跑一次再选）：
① 若"菜单没关、后台结果落地"这一格能读到菜单里出现候选行 ⇒ ②可行且必须；
② 若只有"重新打开菜单才更新" ⇒ ①就够，②不做（不要在菜单里塞常驻订阅）；
③ 两种都做不到（通道不允许）⇒ 把"正在整理推荐…"这句改成**只在打开时算一次**的诚实文案，并记为按实不做。

### R110 追记：162 拿到答案（①，不是②）/ 新开 166（runner 的动效红不可复现，而闸门没覆盖它）

**162 结案（读 R109 的 CI `39008599904`）**：本轮装的 `CARD_PROBE_COLUMNS` 第一次在 runner 上打出逐列读数 ——
臂 2 `cardprobe-split-groupbox`：列0（侧栏 wrapper `x=0.0..148.0`）`墨行=70/71 墨像素=1420/1662 最大偏离=165/211`，
而**详情那一列自己就有 wrapper**（`列1 x=151.0..720.0`，与本机"详情没有自己的 wrapper"不同，推导列 列2 与它同段），
它的读数是 `墨行=0 墨像素=0 最大偏离=0（亮）/2（暗）`。带子 `170..720` 落在 151..720 **之内**、
尺自检"带子必须与详情列有交集"**没有红** ⇒ 按 162 开跑前写死的两格，命中 **①：详情在 runner 上没被实例化**，
不是 ②（带子放错）。**所以 150 那台实验在 CI 上的堵点换了名字**：不是尺、不是带子，
是夹具的 detail 内容在那台机器上不出现 ⇒ 下一步是"让臂 2 的详情在 runner 上保证有内容"（selection 落点或显式给 detail），
而不是再动带子。**本条不许写成 150 已推进**：150 仍然开着，只是它的堵点第一次有了名字。

**166.（R119 结案：闸门已从 report-only 升成硬门）runner 上的动效红在两次运行之间换了一朵，而捕获闸门看不见它**（R110 开 / 与 155、R55/R57 那族同源，**机器侧可复现性账**）：
`39005449295`（R108）的去重后红是 `testBandCaptureIsCheaperAndStillSeesTheMotion`（26.84 > 23.88）+ 157 那两朵证人；
`39008599904`（R109，**产品只差一行声明**）的红的却是 `testFrameIntervalsUnderStateChanges`
（最差帧 196.77 > 120ms、p95 42.43 > 20ms）+ 同样那两朵证人 —— **bandCapture 那一跑绿了**。
同一台 runner、同一份尺、相邻两次跑，动效那两朵红**互相换班** ⇒ 这一族的地板在 runner 上是噪声主导的。
另一格事实：两次 `CAPTURE_GATE_CASES` 都是 `passed=53 skipped=11 failed=1 有名字的红=1` ⇒
那句"唯一的红是 157"只覆盖**捕获那一卷**，动效那一卷的红不在它的账里（R109 的账本恰好就是这么写的，见 STATE 的 R109 段）。
**四次相邻跑的基线（本轮补查，U-361）**：`38994712442`（R106）`FAILED testFrameIntervals=0 / FAILED testBandCapture=0`；
`39002273057`（R107）同样 0/0；`39005449295`（R108）bandCapture 红；`39008599904`（R109）frameIntervals 红。
⇒ "换了一朵"这件事要带上限：**这一族从 R108 那跑才开始出现红**，而 R108 与 R109 之间产品只差一行声明、
尺那边多了逐列扫描（R109 的 `CARD_PROBE_COLUMNS` 要在整窗字节上多扫两列）。
**分不清的两件事就分开记账**：既可能是 runner 噪声从 R108 起变高，也可能是我 R109 新加的扫描把那一卷拖慢
（`p95 42.4ms` 这种量级对整卷负载是敏感的）。能分开的办法就一条：**同一 commit 在 CI 上连跑两次**（155 的 runner 版），
若红在两跑之间换班 ⇒ 噪声；若 frameIntervals 每次都红而 bandCapture 每次都不红 ⇒ 是我加的扫描，
那时该做的是把逐列扫描挪出被测卷的计时窗口，而不是放宽门限。

**仪器已落（本轮）**：`scripts/ci_red_stability.py` 把两次跑的红**归约成身份**（用例名，抽不到名字时用消息指纹）
再分三格（两跑都红 / 只在一跑 / 形状换了），有换班就退 1。拿两份真日志对账的结果就是这一条：
`RED_STABILITY A=r108_ci.log 红=2 B=r109_ci.log 红=2`
`BOTH_RED testSettingsCardHorizontalInsetIsMeasuredAgainstTheSystemGroupBox 形状=XCTAssertGreaterThan`
`ONLY_A testBandCaptureIsCheaperAndStillSeesTheMotion 形状=XCTAssertLessThanOrEqual`
`ONLY_B testFrameIntervalsUnderStateChanges 形状=XCTAssertLessThanOrEqual`
`RED_STABILITY 两跑都红=1 只在一跑=2 形状换=0 换班=1` ⇒ **157 那朵证人两跑都在（可当真），动效那两朵各只出现一次（不能当真）**。
配套真值表 7 格（正对照 / 换班牙 / 裸 XCTFail 形状 / 形状换 / 读不到≠干净 / `--help` 退 0 /
无名红不许塞进同一个桶 = U-364）。

候选修法（先登记再动）：① 让动效那一卷也有"有名字的红"能力行，把 `testFrameIntervals*` / `testBandCapture*` 纳入同一份闸门账；
② 在 CI 上把这两条判据改成**同版两跑取交集**（与 155 的形状一致），只把两跑都红的算红；
③ 承认这两条判据在 runner 上不成立并登记成有名字的未覆盖（本机仍然判）。**不许做**的是放宽门限。

### 批次 85（R110 开 · 只有真机能做的两格，都不需要额外工具）

**85.1 状态项那颗图标的基线与材质**（164 的机器级那一格 / U-359）：本轮把 12 上那颗换成系统符号 `clipboard`，
但 12 那棵分支在本机（13+）不执行 ⇒ 我验的是**工厂交出的那张图**（逐像素 + 帧），不是真菜单栏里那颗。
请在装了 R110 之后那版包的机器上看一眼：菜单栏里那颗剪贴板与左邻右舍比，**垂直基线是否居中、大小是否同一档、
暗色菜单栏里是不是白墨**。若偏高/偏小 ⇒ 改的是 `NSStatusItem` 的占位（18×18 那一格），不是换素材 ——
164 里预登记的判法就是这一条。

**85.2 12 上打开菜单会不会一直挂着「正在整理推荐…」**（165）：macOS 12 的机器上，冷启动后**第一次**点菜单栏图标，
看那一行是不是"正在整理推荐…"，然后**不要关菜单**等 2~3 秒：候选行会不会自己出现？
（会 ⇒ 165 选②订阅刷新收尾重填；不会 ⇒ 选①`menuNeedsUpdate:` 或按实登记）本机是 13+，这一格只能由真机答。

### R111 追记：165 结案（本机量到的那条红就是它）

修前判据原文：`XCTAssertFalse failed - 刷新已经落地，这张菜单里那句「正在整理推荐…」还在`，
并打出当时的 9 项名单；修后 `MENU_LIVE_REFRESH 修前项数=9 修后项数=13 修前挂着正在整理=true 修后挂着正在整理=false 修后有候选区=true store候选数=2`。
处置选**订阅刷新落地后重填**而不是 `menuNeedsUpdate:`：后者只在要显示之前触发，而这一格要修的正是
「已经开着、结果后到」；`menuWillOpen` 已经在管「下次打开是新的」，再加一条等于把同一个洞补两遍。
规矩进 **D-180**（三条：订阅要被持有 / 重填要读到这一代写完的那一刻 / 分支不在本机执行就拆两格 + 真机那格另立批次）。
四刀 M602–M605 全 CAUGHT，其中 **M602 摘掉 `receive(on:)` 就红** —— 它钉的是「重填读哪一刻的值」，
因为 `HistoryStore` 先置 `isRefreshingPredictions = false` 后写候选（`HistoryStore.swift:252-260`）。
**165 结案范围要说清**：证的是「机制通 + 接线在」，12 上真菜单会不会当场变仍归批次 85.2（U-369）。

**R111 补（读 R110 的 CI `39013515969`）：换班拿到第三个数据点，而 ① 的代价要说清**。
三次相邻跑的红身份对账（`scripts/ci_red_stability.py`）：R108 只有 `testBandCaptureIsCheaperAndStillSeesTheMotion`、
R109 只有 `testFrameIntervalsUnderStateChanges`、**R110 两朵都没有**（只剩 157 那朵证人，三跑都在）。
⇒ 这一族在 runner 上不是"偶尔红"，是**每一跑换一朵**；捕获闸门三跑都报 `有名字的红=1`，
因为它只看 `/tmp/frames.log` 那一卷。
① 的真实代价（本轮读完闸门源码才知道，不写下来下一轮就会重估一遍）：`ci_capture_gate.py` 是通用的
（任何 swift-test 日志都能判），缺的不是能力而是**接线**——要么在 workflow 里对全量日志再跑一次闸门，
要么给它加"按步骤/按类名前缀切片"的入口。麻烦点在**切片**：CI 日志里同一个标记会由多个步骤各打一次且取值不同
（U-178 那一族），所以新加的 `--class-prefix` 必须连带把"这条红来自哪个步骤"打出来，否则就是把 166
换成一把新的会造假矛盾的尺。⇒ 这一格留给 R112（要改 workflow，验证要一次 CI 往返，不划算塞进收尾轮）。

**R112 补（读 R111 的 CI `39016053892`）：第一次拿到「换班=0」，但它还不满足升硬门的判法**。
`RED_STABILITY A=r110_ci.log B=r111_ci.log … 两跑都红=1 只在一跑=0 换班=0` ⇒ 连续两跑的红名单**第一次一致**
（只有 157 那朵证人）。**但这两跑是两个 commit**（`fa625f1` → `b5a1f5d`），而 166 的判法写的是
"同一 commit 两跑名单一致" ⇒ 这一格只能算**鼓励**，不能拿它去掉 `--report-only`（口径不许偷偷放宽）。
另两条同跑的读数：`MENU_LIVE_REFRESH 修前项数=9 修后项数=13 修前挂着正在整理=true 修后挂着正在整理=false 修后有候选区=true store候选数=2`
⇒ 165 的**机制那一格**在第二台机器上也是同一个数（接线那一格仍只在 12 上执行，归批次 85.2）；
`MENUBAR_GLYPH … 墨像素=891 包围盒px=10..60×7..67 与参考=相同` ⇒ 与 R110 那跑逐字相同，
本机 892 / runner 891 的 1 像素差**第二次复现**（素材读数也会跨机器抖，地板取实测一半是对的）。

**167.（R114 **撤回**）设置侧栏图标"暗档偏暗"—— 量完之后：不是缺陷，而且**台账早就反着记过**（与 D-090、R39 同一格）：
开单时我只有眼睛。撤回用的是同一把尺（`inkSideCounts` 的口径：与该列众数背景比、偏离 >16 记一侧）
加**台账里推出来的坐标**（`settingsSidebarTextColumn = x:40 y:96 w:102 h:154` ⇒ 图标列取 `x 8..40pt`、同一 y 段），
帧是本轮新拍的 `settings-stats-populated-720x540-{light,dark}`：

| 档 | 图标列 | 文字列 |
|---|---|---|
| 亮 | 背景 250，暗侧 3966 个偏离像素（极值 250 ⇒ 白底近黑墨），亮侧 0 | 暗侧 14997 |
| 暗 | 背景 27，**亮侧 1391**（极值 228 ⇒ 深底近白墨），暗侧 42 | 亮侧 677 / **暗侧 2151**（这就是 D-090 那个合成前极性，名单里第 9 张就是这一张） |

⇒ **图标在两档都落在期望侧**，"几乎看不见"的那枚是 `推荐` 的细笔画在我看的缩略图上被压掉了，
而文字那一列在暗档确实反侧 —— 那是**已经记账的盲区**（`darkSidebarTextBlindSpots`），不是新缺陷。
**R39 的名单注释当时就写着"图标也看得见"** ⇒ 这一单本不该开（见 U-377）。
不删这一条，留成"开单前查重"的反例。

  **R115 追记（这句结论要打折）**：逐行仪器上线后（`SIDEBAR_ICON_ROW`，行带从视图树取、
  墨的横向范围由帧自报），本机实测 156 行（2 档 × 13 夹具 × 6 行）里
  **light 无墨 43 行、dark 反侧 22 行**，且集中在具体符号上（见 170）。
  ⇒ 撤单正文那句「图标在两档都落在期望侧」**只在列级成立**，当逐行结论是错的：
  列级把"有些行根本没有墨"这件事抹平了。撤的仍然是「暗档图标比标签暗」那一格，仍然成立；
  同一批数据在行级开出了 170。

**168. 闸门结论行的「归属」没被验过：脚本电池的样张与 CI 真步打同一种标记**（R112 埋 / R115 结案）：
R112 给 `ci_capture_gate.py` 加了 `--label`，workflow 动效那一步用 `--label MOTION` ⇒ 结论行是
`MOTION_GATE_SCOPE` / `MOTION_GATE_CASES`。而 `scripts/tests/test_ci_capture_gate.py` 的样张当时也用
`--label MOTION`，并且 `_run`（只取退出码那一层）**不重定向 stdout** ⇒ 样张的结论行进到真实 stdout，
被 `Release script tests` 那一步原样写进同一份日志。runner 第一份读数的现场证据：
`MOTION_GATE_CASES passed=34 skipped=32 failed=0`（真步）与 `passed=1 skipped=0 failed=1`（夹具）同形并存。
⇒ 166 的升硬门判据「两跑名单一致」本来可以被夹具冒充。修法两层：样张标签换成 `SAMPLE`；
`_run` 内部吞掉 stdout 并把文本交给 `last_output`（`_capture` 只读它，不再套第二层重定向 ——
嵌套 `redirect_stdout` 会让外层读到空串，这是本轮改第一版时真红过的，U-385）。
守卫是 `scripts/tests/test_gate_marker_hygiene.py` 三条：生产标签从 workflow ∪ 闸门默认值里发现（不硬钉）、
**真跑一遍样张那一卷**看 stdout 里有没有生产标记（判产物不判源码文本）、正对照喂一条伪造标记必须被抓。
刀 M609 —— 但**要分开记**：M609 注入后红的是「样张那一卷自己没过」那一格（`_capture` 读不到文本），不是「stdout 里出现生产标记」那一格；两格都真，但后者目前只由正对照（伪造文本）证过，没被这刀单独证过（U-387）。脚本电池 236 → **239**。

**169.（R116 结案）台账里两条列级矩形的 y 带盖不全侧栏：`settingsSidebarTextColumn` 少盖第一行**（R115 开 / R116 修）：
视图树实测六行行带是 y 60..252（每行 32pt），而台账写的是 `y 96 h 154`（96..250）。
⇒ 以它为准的 `TEXT_SIDE` 读数与 `darkSidebarTextBlindSpots` 名单从阶段一加上「统计」那一行起就只覆盖 5/6 行；
R115 的仪器报出 `SIDEBAR_ICON_ROSTER_DRIFT …更早的行数=52/156`。
最可能的来历是 5 行时代的坐标没随第 6 行重推。本轮**没改它**：一改，13 个夹具的 `TEXT_SIDE` 名单会整体位移，
那种事要先真看帧，不能在一次仪器新增里顺手做。下一步：这两条矩形也换成 `sidebarRowRects`，
重算名单，并核对 `settingsContentPane` 是否同样过期。

**170.（R116 更正：机制不是新发现，R28 就量过）侧栏图标在离屏帧里按符号固定极性**（R115 开 / R116 更正口径）：
13 个设置夹具 × 2 档逐行实测（`SIDEBAR_ICON_BY_SYMBOL`）：

| 符号（分区） | light | dark |
|---|---|---|
| `command`（快捷键） | 期望 2 / 无墨 11 | 期望 13 |
| `gearshape`（通用） | 期望 3 / 无墨 10 | 期望 13 |
| `hand.raised`（隐私） | 期望 3 / 无墨 10 | 期望 13 |
| `folder`（数据） | 期望 1 / 无墨 12 | 期望 13 |
| `wand.and.stars`（推荐） | 期望 13 | 期望 2 / **反侧 11** |
| `chart.bar`（统计） | 期望 13 | 期望 2 / **反侧 11** |

「期望 3 / 无墨 10」= 只有 3 个夹具把这一行当选中行（选中行走强调色、药丸让它出墨），其余不出墨。
⇒ 读数指向的不是「暗档偏暗」，而是**同一列里 `.primary` 的解析按符号固定成某一种极性**：
四枚固定成白（亮档等于没有、暗档正常），两枚固定成黑（亮档正常、暗档反侧）。
与 D-090 的「合成前极性」同族，但多出一件 D-090 没说的事：**不是整列统一反侧，而是逐符号分裂**。
本轮不判产品（D-181：单次读数不给产品定罪）。下一步：(a) 让 CI 落第二份读数；
(b) 真机批次 86.1 —— 请用户在 12 与本机、两种外观下看侧栏六枚图标是否都在（伪影与产品缺陷的分界线就在这）。

**R116 更正（这一条我开重了）**：`OffscreenSymbolInkProbeTests` 的文件头注释里，**R28（第 22 项）** 就写着
「R28 实测它是**反相**… 每一枚符号的颜色在两帧里**恒定不随外观变**」，
并且同一条注释已经给出结论「**不能据此判产品缺陷（也不能据此改产品颜色）**」。
⇒ 本轮 170 的"新"只剩两件：(1) 逐符号的名册（哪四枚白、哪两枚黑）；(2) 一个常驻的逐行仪器（R115 之前那格靠 R28 的一次性 print）。
机制不是新的，也不欠第二份读数；欠的只有真机批次 86.1（确认那两枚在真机上不是真的浅色）。
开单前我没查这条 —— 与 U-377 同一族的第三次，而且这次连自己写的测试文件注释都没 grep（见 U-388）。
**顺带记一条"差点犯"**：本轮我一度想把 `.symbolRenderingMode(.hierarchical)` 换成 `.monochrome`
让六枚符号在两档都统一 —— 那正是台账（R28 注释 + D-090 那一族）明令禁止的"为了讨好这一帧改产品"，
是**已记的规矩挡住了它**，不是我想出来的（见 U-389）。

**170 追记（R116）**：**runner 的第一份逐行读数（R116 读到，run 39020070349 / `ffe65a1`）= 零信息**：`light 有墨行=78 无墨行=0 反侧行=0 | dark 有墨行=78 无墨行=0 反侧行=0`、六枚符号全 `期望=13`，而同跑紧接 `SIDEBAR_ICON_NOT_RUN all（内容区 0 墨）` + skip ⇒ 那串「零反侧」是噪声对称的产物，不是证据。因此把「等 CI 落第二份读数再判」划掉：BACKLOG 43 没解之前 CI 交不出样本。本轮已把能力位写进读数行本身（`能力=可判` / `能力=不可判(内容区 0 墨)`），见 U-391。

**150 追记（R117，装上了能分两种成因的尺）**：runner 那一跑（`ffe65a1` / run 39020070349）的
`CARD_PROBE_COLUMNS` 已经排掉一种：详情列的 wrapper **在树里存在**（x=151..720、全高 300pt），
但 `墨行=0 最大偏离=0`。剩下两种「详情没被实例化」与「画了但没进帧」在像素上同形，
所以本轮装 `CARD_PROBE_DETAIL_TREE`（列内视图数 + 嵌套 hosting 层数；本机基准 `hosting=6 列内视图数=16`）。
它只报数不判产品（D-163）。⇒ 150 的定性等 R117 的 CI 那一跑，不再靠猜。

**169 追记（R118：这条只结了一半，另一半是本轮重开的）**：**R116 那条对账守卫在 runner 上第一次跑就红**（run 39021652718 / `0ac7851`）：`SIDEBAR_ROSTER_RECT 台账=60..252 树给=342..534 行数=6 上界差=282.0pt 下界差=282.0pt` —— 同一份代码、同一个 720×540 帧，**整条侧栏在 runner 上往下挪了 282pt**，而行高（32pt）与行数（6）一点没变。
⇒ 「矩形换成实测行带」这个动作本身是对的（169 说的"少盖第一行"确实修了），
但 R116 结案时把**本机那台机器的绝对 y** 当成了跨机器契约，所以那条对账守卫在 runner 上必红。
本轮把判据改成比高度与行数、绝对偏移只报不判，并让 `TEXT_SIDE` 也改吃树给行带（x 仍来自台账）。
169 保持结案，但结论范围收窄成「本机矩形对齐」；跨机器对齐由 `SIDEBAR_ROSTER_OFFSET` 报数，不判。

**150 追记 2（R119：定性完成 —— 不是容器吃材质，是帧太矮把内容裁掉了）**：R117 那跑（run 39022854686）
的树侧证人给出答案：runner 上臂 2 的详情列**确实有东西** —— `嵌套hosting=4 列内视图数=7`（本机 `6 / 16`），
可像素那两把尺读到 `墨行=0 最大偏离=0`。同一天另一条读数把它解释了：
`SIDEBAR_ROSTER_RECT … 树给=342..534`（runner 上整列往下挪 **282pt**）。
臂 2 的夹具只有 **300pt 高** ⇒ 内容被挪到帧外面去了，"0 墨"是**裁切**，不是材质消失。
⇒ 本轮把夹具加高到 720×600（任何一台机器都装得下），并把带子的纵向范围改成**详情列自己**
（`bandYFromColumn`：x 仍来自台账，y 来自那台机器的树）。帧名随尺寸换掉（`…-720x600-{light,dark}`），
基线 `update` 后 `COMPARED=136 CHANGED=0 MISSING=0 ADDED=0`。
**runner 的红是否消失要等下一次 CI** —— 这条追记在拿到那一跑之前不算结案。

**166 结案（R119）**：这条自己写的判据是「同一 commit 两跑的 `MOTION_GATE_CASES` 名单一致 ⇒ 才允许去掉
`--report-only`」。R118 用 `gh run rerun` 把 `24b8936` 那一跑重跑成 attempt 2，两遍逐字相同：
`MOTION_GATE_CASES passed=34 skipped=32 failed=0 有名字的红=0 类未知名单=0 NOT_RUN=82`。
⇒ workflow 那一步已去掉 `--report-only` 与 `|| true`，改名为 `Motion gate (BACKLOG 166, promoted from
report-only census)`。附带一条：判据要按**登记的原文**执行 —— 本轮我一度想改成"三跑一致"才肯签，
那是临时加严；登记的是两跑，两跑一致就升。

**171. 暗档侧栏盲区名单的能力闸门吃错了对象：它问内容区，判据问侧栏 ⇒ runner 上的一条真信息被 skip 掩盖**（R120 开，**未修完**）：
R118 的 CI（run 39023798233）里两条读数放在一起看：
`TEXT_SIDE settings-general dark 亮侧=1503 暗侧=0 ⇒ 墨在期望侧`（侧栏**读得到、而且不反侧**）
与 `TEXT_SIDE_NOT_RUN all（这台机器拍不出 SettingsView：内容区也读到 0 个偏离像素）`（整条守卫 skip）。
⇒ 名单 `darkSidebarTextBlindSpots`（13 张"暗档侧栏文字不可信"）是**本机这台机器的现象**，
runner 那台不成立；而旧闸门 `contentInkTotal == 0` 让它在 runner 上根本不参与对账，
于是"名单是机器相关的"这件事一直没人看见。

R120 已做：闸门改成吃**侧栏自己**的墨（`sidebarInkTotal`），内容区降级成附注，
并加读数 `TEXT_SIDE_CAPABILITY 侧栏偏离=… 内容区偏离=… 判了 n/m ⇒ 闸门与判据同源`。
两刀：M614（把内容区矩形挪到帧内空白 ⇒ 测试必须**仍然跑**，旧写法会 skip）实测 PASSED；
M615（把侧栏 x 带挪进实测无内容的分栏阴影 148..160 ⇒ 必须**自己报未运行**）实测 SKIPPED
并报 `TEXT_SIDE_NOT_RUN all（侧栏列在 13 个夹具上读到 0 个偏离像素；同批内容区偏离=425863）`。

**剩下没做的（下一轮）**：闸门放开之后，runner 那台会让 `gone`（13 张"名单里的帧现在落在期望侧"）**红**——
这是对的（那条断言的原文就写着"两种都要真的去看那张帧"），但名单本身需要变成**按机器给**
（键：`HostInfo`/系统版本/是否 Retina），否则同一份名单在两台机器上永远只能对一台。
⇒ 171 保持开着，等 R121 的 CI 把那一朵红落下来，再决定"名单按机器分键"的写法。

**150 追记 3（R121：上一轮的成因被自己那一跑的 CI 证伪，正式定性）**

R119 写的是「帧太矮把内容裁掉了，不是容器吃材质」，并且把臂 2 的夹具从 300pt 抬到 600pt。
本轮读它自己那一跑（run 39024922502）的正文，三行读数把这句话打死：

- `CARD_PROBE_ARM cardprobe-split-groupbox light 材质=无 卡片段=-1 墨行=0 墨像素=0 最大偏离=0 带子=170..720pt 页底=236`
  —— 帧已经是 720×**600**，带子里仍然一个偏离像素都没有；
- `CARD_PROBE_WHOLE cardprobe-split-groupbox light 整窗墨行=70 整窗最大偏离=165 带子墨行=0 帧=720x600px 倍率=1.0x`
  —— **这台机器拍得出这一页**（整窗 70 行墨），所以「拍不出整页」也不成立；
- `CARD_PROBE_COLUMNS … 列0:_NSSplitViewItemViewWrapper[x=0.0..148.0] 墨行=70 … 列1/列2[x=151.0..720.0] 墨行=0 最大偏离=0..2`
  —— 那 70 行墨**全在侧栏那一列**，详情那一列（151..720）从头到尾是平涂。

⇒ **150 的答案**：runner 上「设置窗口的卡片没有材质」不是带子放错、不是帧太矮、也不是容器吃掉第二层，
而是**分栏的详情那一列在这台机器的离屏捕获里整列没画**（同一帧的侧栏列正常画）。
被告列 0 墨 ⇒ 任何放在这一列里的带子都不可能读到墨，`材质=无` 在这台机器上没有对象。
本机（Retina、2x）同一夹具：`整帧墨行=171 详情列墨行=24 带子墨行=24 ⇒ 可判`，`列内视图数=16 嵌套hosting=6`
vs runner `列内视图数=7 嵌套hosting=4`。⇒ 这条与 43 是同族但**范围不同**：43 说整页平涂，本轮实测只到详情列。
**43 的措辞本轮已按实测收窄**（`SIDEBAR_ICON_NOT_RUN all（…R121 的 CARD_PROBE_COLUMNS 已经把这台的盲区收窄到详情那一列 —— 侧栏列本身有墨，不许再写成「整页拍不出」）`）。

**这一轮为此换掉的仪器形状**（D-183）：R107 早就把「怎么分」写进注释（整窗最大偏离 ≥60 而带子个位数 ⇒ 改带子），
但**从没当判据跑过**，于是 R119 我在三种解释并存时挑了一种写下结论。现在它是 `cardprobeArmVerdict`：
证人从「整窗」换成**被告那一列自己**，四种出口各有名字（可判 / 框错红 / 详情列0墨不可判 / 整帧0墨不可判），
外加 `CARD_PROBE_CAPABILITY` 的恒等式「参照臂 = 可判 + 框错红 + 不可判」与 `CARD_PROBE_WITNESS` 的仪表自检。
四刀 M616–M619 全部 CAUGHT。下一跑 CI 的期望：`cardprobe-split-groupbox` 两档 ⇒ `不可判(整帧有墨而详情列0墨)`，
`参照臂=6 可判=4 框错红=0 不可判=2`，而**捕获那一卷不再因此变红**（红的位置换到 171 那一朵 `gone`）。

**171 追记（R121：R120 的 CI 把它预言的那朵红落下来了）**

run 39025878222：`TEXT_SIDE_CAPABILITY 侧栏偏离=19470 内容区偏离=0 判了 13/13 个夹具 ⇒ 闸门与判据同源（D-166）`
+ `testDarkSettingsSidebarTextIsACountedBlindSpot` **failed**：
「这些帧的暗档侧栏文字现在落在期望侧了：[settings-data, settings-general, settings-general-login-failed,
settings-general-login-unsupported, settings-min, settings-privacy, …]」。
⇒ 上一轮说的「闸门放开之后 runner 会让 `gone` 红」按预言发生，且**这条红是真的**：
`darkSidebarTextBlindSpots` 这份名单在本机成立、在 runner 不成立，而它一直按"全局权威"用。
**剩下没做的**：名单按机器分键（键必须来自实测：`HostInfo` / 系统版本 / 帧倍率），
并且分键之后两台的名单都要各自被自己的读数钉住 —— 不许变成「这台说没有就没有」。
171 保持开着，判据形状已经由本轮的 D-183 给出（分类函数 + 恒等式 + 各有名字的出口）。

174. **⑤ 那条采样率判据在 runner 上是抛硬币：间隔里 80% 是调度地板，而它没有为这件事留出口**（R132 开 / 与 155、R38、D-155、118 同族，**判据账**）：
    四跑读数：红 28.44>25.38 / 32.49>27.46 / 32.16>31.81，绿 26.72≤38.44（run `39036587208`）。
    同一次绿跑印出的分解：`带地板=21.27ms 整窗地板=23.37ms`，而抓帧差是 9.6ms ⇒
    **两臂的间隔主要由那台机器的调度决定，不由抓帧成本决定**，所以这条"A 臂比 B 臂细"的判据在 CI 上量的不是它声称的东西。
    现在它只有两个出口（通过 / 红），而真相需要第三个：**这台机器判不了这件事**。
    要做的一格（不改产品、不改阈值）：把"地板主导"做成**由同一次运行自己量出来**的前提
    （`min(两臂地板) > 两臂抓帧差` ⇒ 地板主导），成立时打 `MOTION_NOT_RUN … clock-coarse-in-window`
    （那个理由已在 `motion_floor_expectations.json` 的登记表里），不成立时才允许 ⑤ 判通过或红。
    必须同时配的三件：真值表（四行：细/粗/地板主导/无帧）、变异臂（摘掉前提那一格要红、把地板主导改成恒真要红）、
    以及一条**不许把 not-run 写成免检**的守卫（登记表里那一臂的 `must_judge` 今天怎么设，改完要重新对账）。
    禁止的两种偷懒：调 ⑤ 的阈值；把它登记进 `suite_reds`（那张表被钉成空表）。
    **R133 追记（第三个出口已就位，等 runner 见一次）**：`MotionFilmstripTests.samplingRateVerdict` 四出口
    （`判到=带更细` / `判到=带更粗且地板解释不了` / `这台机器判不了=调度地板 X 大于省下的 Y` / `无从判定=没有帧`），
    前提是同一次运行量出来的 `min(两臂地板) > 两臂抓帧差` —— 不是新阈值、没动 ⑤ 的线、没塞 `suite_reds`。
    本机第一跑 `出口=判到=带更细`（② 同一行报 `8.70×`）⇒ 判据没被改成恒真；
    下一次 CI 的期望：`MOTION_BAND_SAMPLING_VERDICT 机器=arm64/macOS 15.7/1x 出口=这台机器判不了=调度地板 … 大于省下的 …`，
    且 `MOTION_FLOOR_FACTS` 的 `judged` **不许掉档**（这个出口是**读数**，不走 `MOTION_NOT_RUN` 那条通道）。
    两条判据侧的账顺手钉住：U-442（变异表 needle 命中 2 次那一臂 DID-NOT-RUN 却整表 exit 0；红掉的测试名要按空格切）、
    U-443（放行一个出口要说清它放不掉什么）。本条等 runner 见过一次再结案。

172. **R122 开：亮档侧栏图标在离屏通道里几乎不画墨 —— 与暗档"反侧"是两种病，本轮只修了暗档**（R122 开 / 与 41、167、170、43 同族）：
    `SettingsSidebarRow` 的渲染模式从 `.hierarchical` 换成 `.monochrome` 之后，两档的读数**朝相反方向动**：

    - `dark 期望 56→78、反侧 22→0`（`wand.and.stars` 推荐 与 `chart.bar` 统计 是六枚里仅有的两枚多色符号，
      `.hierarchical` 会带它们自己的调色板 ⇒ 暗档黑底黑图标）—— 看帧确认：改后六枚图标与标签同亮。
    - `light 期望 35→13、无墨 43→65` —— 看帧也确认：亮档未选中行的图标淡到几乎看不见。

    为什么判它是**通道**而不是产品：同一行里标签文字用的就是同一个 `.primary`，文字照样是清晰的黑字，
    只有 Image 那一路不画 ⇒ 坏的是离屏通道对 `Image + .monochrome + 语义色` 的解析（审计第二轮 1.9
    的原始发现就是这一条：把颜色换成固定 `Color.black` 就能画到 0.175–0.402）。
    **没有定论的那一半记在这里**：真机上 `.monochrome` + `.primary` 是系统侧栏的标准做法，
    预期图标与标签同色；但这一轮的验收只到"帧 + 读数"，没到真机。
    ⇒ 判据只把**反侧**升成会红（`SIDEBAR_ICON_INVERTED`，M620/M621 两刀），亮档那一半写成
    `SIDEBAR_ICON_BLIND_SPOT` 登记行 —— 写成会红就会诱使下一轮拿固定色去填它，那才是真把颜色写死。
    下一步（R123）：装包到真机，用 `screencapture` 量亮档侧栏图标列的墨，与标签文字同列对照；
    真机若也淡，就把 `.monochrome` 撤回去并给多色符号单独配 `.palette`。

**150 追记 4（R122 读到 R121 的 CI：四种出口在 runner 上按预期落地）**

run 39027921504 正文（已解析进 `ci/r121_run_39027921504_readings.log`）：
`CARD_PROBE_ARM_VERDICT cardprobe-split-groupbox light 整帧墨行=70 详情列墨行=0 带子墨行=0 ⇒ 不可判(整帧有墨而详情列0墨=这台机器没画这一列)`
（暗档同形，整帧 59）+ `CARD_PROBE_CAPABILITY 参照臂=6 可判=4 框错红=0 不可判=2`
+ 另两臂四格 `⇒ 可判(带子里有内容)`。**捕获卷不再因这条变红**，那一跑只剩
`testDarkSettingsSidebarTextIsACountedBlindSpot` 一朵红（171 的 `gone`），与登记一致。
⇒ 150 的定性有了一台机器之外的第二份证据，且"不可判"是**带名字的**两格，不是 skip。

**171 追记 2（同一跑）**：`MOTION_GATE_CASES passed=34 skipped=32 failed=0 有名字的红=0` / `MOTION_GATE_RESULT=ok`
⇒ 动效那一卷干净；捕获卷那朵 `gone` 仍在，名单分键（键来自 `HostInfo`/系统版本/帧倍率）排 R123。

**172 追记（R123：暗档那一半已经有真机证据了，亮档那一半仍然只能等人）**

新通道：`scripts/real_screen_sidebar_icons.py` —— 走**产品自己的入口**（状态菜单里的「设置」）打开窗口，
只截这一扇窗口的矩形，按 2pt 步进在图标列里自动找行带。第一次跑（本机 · 系统暗档 · 装的是 R122 那一版）：
`REALSCREEN_GEOM 窗口=720x572pt 帧=1440x1144px 倍率=2.00x 背景亮度=38 ⇒ 外观=dark` +
`REALSCREEN_ICON_BAND 0..5`（六条全有墨，41–84 个偏离像素，最大偏离 184）+
`REALSCREEN_RATIO 图标列墨=379 文字列墨=3965 比值=0.096 行带数=6（期望 6）` ⇒ `REALSCREEN_VERDICT=ok`。
⇒ R122 那句"暗档两枚图标黑底黑图标、改完六枚与标签同亮"**在合成后的屏幕上成立**，不再只有离屏帧作证。

**亮档那一半没拿到**：给 App 域写 `AppleInterfaceStyle = Light` 并重启 App 之后，
所有读数与暗档**逐字相同**、`外观=dark` ⇒ 这台 macOS 不采纳按 App 强制浅色（只认强制深色）。
剩下的两条路都要人点头：把系统外观整体切到浅色（会改动用户桌面），或者用户自己看一眼
—— 人工批次 86.1 的问题就是它：**浅色下未选中行的图标，有没有它的标签那么黑？**
（那一跑的关键判据不是"好不好看"，而是"淡到什么程度"：如果与暗档同档清晰，则 172 判成纯通道，
`.monochrome` 留下；如果明显比标签淡，就撤回并给两枚多色符号单独配 `.palette`。）

**171 结案（R124：名单按机器分键，"没登记的那台"必须红）**

R120 的预言在 R122 的 CI（run 39029027567）里再次落地：那一跑**只剩一朵红**
`testDarkSettingsSidebarTextIsACountedBlindSpot`，正文是"这些帧的暗档侧栏文字现在落在期望侧了：[13 张]"。
⇒ 名单不是"错"，是**它从来只属于一台机器**：本机 vibrant 列在合成前反侧，runner 不反侧，两台都是真的离屏捕获。

改法（不是把红按下去）：`darkSidebarTextBlindSpotsByMachine` 一行一台，键由**量出来**的事实组成
（`arch / macOS 主次版本 / 帧倍率`），关系判据 `sidebarRosterVerdict` 给四种出口
（未登记 / 一致 / 新盲区 / 登记过的不再反侧），配 8 行真值表。
本机那一行由本轮打印出来的键填：`TEXT_SIDE_ROSTER_KEY arm64/macOS 27.0/2x 本机登记=13 实测反侧=13 判了 13/13 ⇒ 一致`。
**runner 那一行故意还没登记** —— 它下一跑会红成 `TEXT_SIDE_ROSTER_UNKEYED <它的键>`，
再由那一跑印出来的键去填。手挑一个"看起来像 runner 的键"就是拿猜测当前提（R118 的教训同形）。
空集也是一条**声明**（"这台不反侧"），它同样被 extra/gone 两格钉住，所以加一行之前必须真的去看那张帧。

三刀 M624（键里丢掉倍率）/ M625（未登记改成"当成一致"）/ M626（撤掉新盲区那一格）全部 CAUGHT。

    **R136 结案（runner 的两格期望都对上了）**：run `39038634407`（R133 那一跑，job=**success**）
    步骤 `Motion filmstrip (report-only)` 原文 ——
    `MOTION_BAND_SAMPLING_VERDICT 机器=arm64/macOS 15.7/1x 出口=这台机器判不了=调度地板 22.13ms 大于省下的 5.64ms ｜ 省没省钱由 ② 单独判（那里已经报过 1.78×）`；
    同一次 run 的 `Motion coverage floor` —— `MOTION_FLOOR_FACTS judged=3/4 executed=58 … 红的用例=- 汇总行报红=0` + `MOTION_FLOOR_REDS=0`。
    ⇒ ① 那台机器**说出了自己判不了**，而不是把一次调度噪声报成产品结论；② `judged` 仍是 3/4 ⇒ 这个出口是读数，没把覆盖率地板拖下来。
    全程未动 ⑤ 的阈值、未往 `suite_reds` 塞任何东西（那张表仍被 `test_motion_floor_gate.py` 钉成空表）。
    本机那一侧仍照判（`出口=判到=带更细`，R133 实测）⇒ 判据没被放弃，只是**按机器分了范围**。

173. **动效位点欠账：连续五轮零新增动效，而这一轮刚把「哪一档接在哪个文件」变成会红的清单**（R125 开 / 与 R42「要么供电要么撤声明」、R46 覆盖地板、103「悬停够不够响没有机器判据」同族）：
    `MOTION_KIND_COVERAGE` 第一次把九档动效的接线情况打成一行一行的读数
    （`hover=17 / selection=5 / bannerIn=6 / bannerOut=5 / emphasis=9 / dropTarget=3 / contentFade=38 / slider=3 / skeletonSweep=1`）。
    有了这张清单，下一轮就不该再问「还有哪里没接动效」，而要按清单点一个位答三句话：
    ① 这个状态变化现在有几帧过渡（`QUICKPICK_*` / 胶片那把尺读变化段）；
    ② 加了之后重排次数 / 采样帧里最大跳变有没有变（R74 的规矩：先量代价再决定）；
    ③ 两档外观与 reduce-motion 关掉时各自长什么样（帧 + 目视）。
    **本条不许被写成「清单已建 = 动效已做」**：清单是尺，不是交付。

**171 追记 3（R126：第二行按 runner 自己印的键登记，空集也是一条声明）**

R124 故意留的那朵红在 run 39031123341 里交出键来了：
`TEXT_SIDE_ROSTER_KEY arm64/macOS 15.7/1x 本机登记=-1 实测反侧=0 判了 13/13 个夹具 ⇒ 红(这台机器的位没登记)`。
⇒ 表里加第二行 `"arm64/macOS 15.7/1x": []`。
**空集不是占位，是一条会被两格钉住的声明**："这台机器上侧栏暗档文字不反侧"。
哪天它反侧 ⇒ `新盲区` 红；哪天有人把本机那 13 张抄进这一行 ⇒ 这一台的 `不再反侧` 红。
另加两格**本机就能红**的结构判据（不依赖 runner）：表必须 ≥2 行；键必须成形
（`arch/macOS 主次版本/倍率`，倍率只准 `1x`/`2x`）。理由：`runner`、`CI` 这种"看起来像"的键
能通过任何按数量的懒判据，却永远不会被命中 —— 那是一条死行，比没有更坏（D-188）。
⇒ 下一跑 CI 的期望：这一台读到 `⇒ 一致`，**捕获卷不再有红**（171 全结案）。

**173 追记（R126：这笔账不能用"再造一个动效"来还）**

本轮按清单侦察了四个候选位点，三个的结论是**这里已经量过并写下了不做的理由**：
① 热图格子悬停 —— `withAnimation(.hover)` 挂在变更点上、`hoverRingOpacity` 是有名字的数（R45 有帧）；
② 菜单栏推荐 —— `MenuBarExtraStyle.menu` 编译成**真 NSMenu**（D-055 / M15 实测），
   SwiftUI 过渡在那一层根本不执行，挂 `.transition` 就是自欺（R5 删过一条）；
③ 骨架扫光 —— 时钟形状、亮带宽度 0.3、30Hz、峰值抬升 0.05→0.12 才读得到东西，
   全部有取证记录（R84/R85），而覆盖率 0.522 对地板 0.50 这一格登记表里已写明"不抬成 must_judge"的理由。
⇒ 173 的下一步**不是**"随便挑一处加个动画"（那正是本目标禁止的"为动效而动效"），
而是等一次**用户可见的**观察：批次 86.1（亮档图标）与批次 83.1（真机浮层输入时整条查询有没有底色）
都是能给出"这里少了什么"的通道。本条保持开着，但把判据改成：
**要么由一次真机/用户观察指出具体缺陷再动，要么按 ①②③ 的样子把"不加"的理由量出来**。

**173 追记 2（R127：清账从口号变成数据 —— 18 格有结论、144 格显式未清账）**

新增 `docs/motion_surface_ledger.json`（18 个表面 × 9 个状态 = 162 格，已清账 18 行，
每行一个 verdict + 一条理由 + 一个证据指针）与 `scripts/motion_surface_gate.py`
（判行的形状：重格 / 名册外的格子 / verdict 不在词表 / 理由过短 / 没有证据指针 /
行数低于地板 / 地板大于行数）。读数：
`MOTION_LEDGER 表面=18 状态=9 格子=162 已清账=18 未清账=144 地板=18` +
`MOTION_LEDGER_VERDICTS added=7 kept=9 not-added=1 not-applicable=1` + `MOTION_LEDGER_RESULT=ok`。

**为什么"未清账"只数不红**：把没判过判成红，下一轮就会为了绿去填满 162 格 ——
那正是本目标禁止的"为动效而动效"。反过来，只数不红也必须配一条单调地板
（`floor_rows` 只准升），否则"清过的格子被悄悄删掉"就没人知道。

**下一轮该清的高价值格（不是加动画，是把判断写下）**：菜单栏/状态图标 × 悬停、
主窗口/搜索框 × 聚焦与禁用、设置窗口/说明段 × 空与错误、浮层/底部说明 × 禁用。
两格已知缺陷留在表外待办：**证据指针的形状没有判据**（U-424）、**地板只防删行、不防名册扩张**（U-425）。

**173 追记 3（R128：清账表补三格判据，未清账 136；闸门当场拦下我自己造的词）**

三格新判据（都是上一轮登记的账）：**EVIDENCE_SHAPE**（指针必须含可复查对象：`Sources/` `Tests/`
`docs/` `scripts/` `BACKLOG 号` `D-号` `批次号`，只写轮次号不算）、**SURFACE_UNCOVERED / STATE_UNCOVERED**
（名册里每个表面、每个状态至少一行 ⇒ 加表面不记账立刻红，覆盖率不再被分母稀释）、
地板从「总行数」改成「已清账格子数」，`not-measured` 不算已清账（占位行不许抬地板）。
表本身从 18 行扩到 **26 行**（`added=8 kept=13 not-added=3 not-applicable=2`，未清账 136/162）。

闸门第一次跑就红在我自己写的行上：`UNKNOWN_CELL 第 14 行（主窗口/提示条 × 消失）`
—— 「消失」不在这九个状态里，它是一次转换不是一个状态。这一行删掉，注释留在生成器里。
⇒ 173 的下一步不变：**不为还账造动画**；下一轮清的高价值格是
菜单栏/状态图标 × 其余状态、主窗口/搜索框 × 禁用、设置窗口/说明段 × 空与错误。

**173 追记（R140）**：本轮清掉八格（表 60 → **68 行**，未清账 94/162，地板 60 → 68），
但**产品 0 改动、且没有新增动效** —— 173 从 R126 起欠的那一次新动作仍然欠着，这条不许被"清账行数"稀释成已还。
本轮新清的八格：主窗口/详情区 × 选中（kept，`highlightQuery` 2 处）与 × 禁用（判过不加）、
主窗口/侧栏 × 选中（kept）、设置窗口/侧栏 × 空与 × 加载（判过不适用）、浮层/列表行 × 空与 × 错误、菜单栏/推荐面板 × 成功。
下一批点名的格（按"离用户最近、最容易登记成空白"排）：主窗口/搜索框 × 禁用、设置窗口/说明段 × 空与 × 错误、
菜单栏/状态菜单 × 加载与 × 错误、浮层/底部说明 × 聚焦。

**175. 缺席断言的射程没有判据（R140 新开，U-463，R141 的靶）**： —— 闸门只查「路径存在 + 那个词不在文件里」，
查不出「这个缺席说明的是不是当前这一格」。本轮的处置是靠规矩写窄：文件只装这一个表面才允许文件级缺席
（`QuickPickController` 可以、`SettingsView` 不行，因为它同时装侧栏与六个分区）。
下一步想把它变成**资格判据**：夹具的 surface→文件名单（`UICaptureHarness` 已有按表面的夹具）能给「这个文件主要装谁」提供事实，
先 spike 证明名单能区分这两例，再决定要不要红。**未做的原因**：本轮的八格已经要落盘，加一条新判据会把射程问题变成第二批数据返工。

**173 追记（R141）—— 欠的那一次真动效还上了**：快捷键录制器进录制态以前只换标题（瞬间换字），
本轮叠了一圈强调色描边（`HotKeyRecorderRing` 1.5pt + `controlAccentColor`，`.emphasis` 供电，不脉动不常驻），
判据 6 条 + 变异 6 把全 CAUGHT，清账表 68 → 70 行（新表面「设置窗口/快捷键录制器」）。
静置态逐像素不变 ⇒ 136 张旧帧 `CHANGED=0`。下一批点名的格不变：主窗口/搜索框 × 禁用、设置窗口/说明段 × 空与 × 错误、
菜单栏/状态菜单 × 加载与 × 错误、浮层/底部说明 × 聚焦。

176. **runner 上那条 20ms 的 p95 地板是绝对数，两跑之间会换班**（R141 开，读 `4486f6d` 那跑红的原文）：
    `On-screen probe coverage floor` 报 `FAILED testFrameIntervalsUnderStateChanges：26.939 > 20.0`，
    而上一跑（`39041957806`，同一份尺、相邻两跑）红=0 ⇒ `ci_red_stability.py` 判 **ONLY_B 换班**。
    那一跑只改了 `AGENT_STATE.md`，产品与尺都没动 —— 所以红的是"这台机器的调度节奏今天是多少"，不是"60fps 没达到"。
    **下一步（R142 的靶）**：把 `loaded.p95 ≤ 20` 换成**同一次运行内的相对判据**（`loaded.p95 / baseline.p95`，
    同一次跑里三臂都打了读数：baseline / motion-off / loaded），绝对数只留作读数与锚点（BACKLOG 42 的规矩）；
    配真值表 + 变异。**不许**登记成 `suite_reds`（那张表被自检钉成空表，红只能修不能登记）。
177. **录制态没有真帧**（R141 开）：本轮的像素判据是**组件级渲染**（`HotKeyRecorderRing` 两态同框），
    不是设置页真帧 —— 于是"那一圈在真实那一屏上压在 bezel 上还剩多少"没人看着。
    补法：给 `SettingsCategory.shortcuts` 那条夹具加一个录制态变体（基线 136 → 138，runner 期望与 `--must-include` 要同步改）。
    **代价说清楚**：改基线会让"逐字节不许变"那道闸在下一轮之前都读不到新帧的回归，所以要在同一轮里 `update`。
178. **暗档那三颗录制器的 bezel 与卡片底色几乎同色**（R141 开，R143 量完：印象被读数否掉，判为不改）：
    看图的位置是 `settings-shortcuts-720x540-dark` 里录制器在 x≈960–1200、y≈265 / 380 / 522，旁边「恢复默认」有看得见的边框。
    **R143 的读数**（`.scratch/motion-audit-2/r143_recorder_bezel.py`，最长同色段法，两档各三行）：
    亮档 卡片底 (247,247,247) ↔ 填充 (228,228,228) ⇒ Δ亮度 19.0、对比 **1.08:1**（三行全 19.0）；
    暗档 卡片底 (37,37,37) ↔ 填充 (54,54,54) ⇒ Δ亮度 17.0、对比 **1.40:1**（三行全 17.0）。
    两档都**没有独立描边**：填充段左沿外 6px 的最长段就是卡片底色本身（Δ 0.0）⇒ 那颗的可辨性全部来自填充差，
    这正是 `NSButton(.rounded)` 在系统里的画法。
    **参照那半句撤回**：`恢复默认` 在 `SettingsView.swift:815` 确实存在，但**不在这张帧里** ——
    y>560 的同一列只有窗口背景（亮 255 / 暗 30）与卡片底（247 / 37），130 条采样里没有第三种颜色 ⇒
    R141 那句"旁边有看得见的边框"不是这张帧给的（那颗在录制器下方，被 720×540 的窗口裁掉了）。
    **判**：暗档的对比比值反而**高于**亮档（1.40 vs 1.08），"暗档几乎同色"没有读数支持 ⇒ 结案不改产品。
    留一句真欠着的：若哪天要让它在暗档更立起来，那是一次**产品决定**（换 bezel 材质），不是修 bug。
    **R143 更正两件事**：① 这一段原来住在 180 的正文里，而 178 的编号被上一轮的一次「插入实为替换」
    吃剩成只有标题没有正文（U-456 那族第二次之后修的是**编号**，正文那一行没搬回来 —— 本轮才搬）；
    ② 「D-0xx 记过」是占位符没换成号，真正的记录是 `.scratch/motion-audit-2/r100_ci_readings.md:68`
    （R100 按两机实测重标材质分离度：真机 16 / 本机 7~8 / runner ≤3）。
    所以先量再判：同帧相对（录制器 bezel→卡片底 的 Δ 对 恢复默认 bezel→卡片底 的 Δ），两档各报一个数。
    若两档不一致，先怀疑门限（R102 那一族），不要先改产品。
179. **两条读数矛盾时，先证明两边量的是同一个对象**（R141 开成「通道不合成 overlay」，R143 **撤回原名并改判**，U-479）：
    R141 那一次我用离屏通道的「新增墨=0」推翻了真机通道的「1548 个高色度像素」，并把
    「`cacheDisplay` 不合成挂在 `NSViewRepresentable` 外面的 overlay」当成通道事实写进了台账。
    **那句话是错的**：那个 0 来自一把坏尺 —— `backgroundLuma` 把透明像素也并进中位数，
    于是 `inkPixels` 把整块控件矩形都数成墨（52800 = 440×120），`newInkPixels` 结构上恒为 0。
    换成色度轴之后**同一条离屏通道读得到那一圈**（R143 的原样读数）：
    `RECORDER_ENTRY 通道=cacheDisplay 不同像素=2940 静置高色度=0 点击后高色度=2924 四边高色度=上1354/下1354/左178/右178`。
    **撤回的处置**：`HotKeyRecorderEvidenceTests` 里那两条坏尺（`inkPixels` / `newInkPixels`）已删，
    产品入口那条用例改回判像素与形状（四边都要有墨 ⇒ 是圈不是横条），真机脚本降级成**第二证人**而不是唯一防线。
    **仍然欠（这一半没撤回）**：R141 之前凡是用「两态相减 + 中位数背景」这类尺子在 representable 混排形状上
    下过结论的地方，逐条重看 —— 现在知道这把尺在「背景是透明」时会把整块控件读成墨。
180. **七维度自评表的口径不一致**（R141 开）：表是 7 行 × 15 分 = **105**，而每轮标题写的是"自评 NN/100"，
    于是我这一轮第一次重算就发现自己抄错过数（R139 那节：行合计 98、标题写 93）。
    **修法**：标题一律写"七项合计 NN/105"，或者把每行改成 ×14 上限（14×7=98，仍不到 100，所以前者更干净）。
    历史各节不回改（回改就是把旧读数改成今天的口径，那正是"过期账本比没账本更坏"的反面），
    但**新节必须用 /105**，并配一条守卫：标题里的分母要等于表里行上限之和。

**176 追记（R142）**：判据换形完成 —— `loaded.p95 ≤ max(baseline.p95, off.p95) × 3.0`（同一次运行内的比值），
`worst ≤ 120` 降级为粗卡顿锚点，三臂读数从 `print` 改走 `emit` 并带机器键（`PROBE_FPS`）。
真值表 6 行 + 两条守卫（读数必须走 emit；本机数 20 不许回到判据位置）+ `mutate_r142.py` CAUGHT=4/4。
**这条不开新账也不算收口**：预算 3.0 是**未量的过渡值** —— 参照臂在 CI 上从来没有一份数，
而本机今天这条采样通道是死的（`FRAME_CHANNEL baseline_n=0 screen=有`，R91 那一格的原样）。
下一轮读 runner 的 `PROBE_FPS` 三个数，按 R118 的规矩（两跑都过地板也不配收硬门）决定收紧到几倍，再谈结案。
**173 追记（R143）**：R141 那节写的「判据 6 条 + 变异 6 把」到现在是 **9 条 + 9 把**（`CAUGHT=9/9、RESTORE_CLEAN=yes`）。
多的三条是审查轮补的：产品入口那条重建（换成色度轴，见 179 的撤回）、`makeFirstResponder` 被拒时不许承诺「我在听」
（F7 的产品修复 + 它的刀 M672）、以及 `onRecordingChange` 抽干 / overlay 钉死 false 两把状态边。
清账表本轮**没有新格可清**（70 格不变）：审查轮动的是判据与工具，不是表面。

**176 追记（R143）**：R142 的正文有一句与代码相反 ——「三臂读数从 `print` 改走 `emit`」当时只做到了**新增那一行**，
三行 `FPS-` 原地没动，而那条守卫只查 `emit("PROBE_FPS` 在不在，所以照绿（U-480）。本轮：
① 三行改成 `emit`；② 守卫加一格「这一条用例里不许再有 `print("FPS-`」；③ 再加一条**双向名册**
`testProbeFilePrintReadingsAreARosterNotACount`（实测 10 行 print 读数 / 9 种标记；新写法红、旧登记退场也红），
配两把刀 M673（把 `FPS-BASELINE` 写回 print）与 M674（把 `RINGVIEWS` 转成 emit）⇒ `mutate_r142.py CAUGHT=6/6`。
④ 顺带更正机制说法：CI 那一步是 `swift test … > /tmp/ui.log 2>&1`，两条通道都进同一个文件，
真正的原因是 `print` 的**块缓冲** + 没有任何步骤去 grep 那些行（R142 写成「CI 收集的是 stderr/文件通道」是错的）。
**这条仍然开着**：预算 3.0 至今没有 runner 的三份读数，`ui_probe_report.py` 的转发要到下一跑才验收得到。

**177 追记（R143，范围重开）**：这一条原来挂在「通道看不见那一层，所以拍不到」上；179 撤回之后这个理由没了 ——
离屏通道读得到（2924 个高色度像素）。于是 177 剩下的只是**夹具没做**：给 `SettingsCategory.shortcuts` 加一个
录制态变体（136 → 138 帧，runner 期望与 `--must-include` 同步改），代价句不变（要在同一轮里 `update` 基线）。

**180 追记（R143，部分修）**：`curve_from_ledger.py` 的两条死路已经修好并各自量过 —— `SCORE` 现在认
`**自评 N/100**` 与 `合计 NN/105`，`DIM_ROW` 现在认 `| 14/15 |`（取分子）；本轮读数：
`SCORES_BY_ROUND 139=93 140=83 141=95 142=88`。
**没修的那半**：「标题里的分母 = 表里行上限之和」那条守卫还没有，所以本轮复核查出 R141 那节
「七行合计 100/105」而**行相加是 99**（14+15+13+14+13+15+15）—— 这正是 180 存在的理由，不开新号。

181. **`AGENT_FINAL_REPORT.md` 的 §9.3 与台账相反，而它没有任何守卫**（R143 复核开，**R143 当场结案**）：
    它还写着「『新加一个有作用的动效』这一件仍未发生 —— 最近的一次是 R126」（R141 之后为假）、
    「清账表还有 102 格未判」（闸门本轮打的是 `未清账=101`）、第 5 条「这两条都还没有各自的自动化守卫 —— 挂着」
    （两半都已有守卫，正文自己过期）。本轮先改文字，**判据欠着**：§9.3 那三句要绑到读数上
    **结案读数**：判据落在 `scripts/tests/test_final_report_claims.py`（4 格：现状必须干净 + 三格内存伪造的正对照，
    伪造一个数 / 塞回"仍未发生" / 塞回"还没有守卫"，各自只点自己那一个名字）。
    未清账这把尺与闸门同源（`表面 × 状态 − 已清账行数`），三句绑的分别是这个数、表里 `added` 行数、两份守卫文件的存在性。
    电池 301 → **305**。⇒ §9.3 从此"停在旧读数"会红，不再靠我记得去对。
182. **三本账对同一件事没有对账尺**（R143 复核开，U-484）：R139 在一本账里声明 U-459…U-462、在另两本里声明
    U-459…U-461；`AGENT_VISUAL_ITERATION.md` 的 Round 140 一节里住着 **U-470/U-471 两条定义**
    （R141 的正文被追加进了上一节的节尾，`git blame` 是 `eeac488`），于是 U-379 那条「一节 = 一轮」又断了。
    `test_ledger_ids.py` 只查「最新一节的区间里有没有定义」，**不查「这一节里有没有区间外的定义」**，所以两次都没红。
    本轮把两条定义搬回 Round 141；把「区间外定义」与「跨账区间对账」升成会红的判据欠着。
183. **累计刀数没有仪器**（R143 复核开，U-483 的兄弟）：台账里「刀数 131 → 133，caught 130 → 132」这一类累计值，
    从来没有任何脚本打过这个数（每张表只打自己的 `n=` / `caught=`）。复核 agent 另数出一条形状：
    R126→R139 每轮都是 `caught == 刀数 − 1`，也就是两个数里至少一个是推的 —— **这一条我本轮没有复算**，
    下一轮要么复算要么删句。现在预检打 `ARM_TOTAL files=121 arms=486 dupes=0 repeats=0`，
    那是它自己口径的**声明行数**，不等于任何历史累计值；要引用就引这个读数，别再手抄。
184. **清账表的地板没有对上一版做差**（R143 复核开，**R143 当场结案**）：`BELOW_FLOOR` 只拿「已清账格子数」与 JSON 里的
    `floor_cleared` 比，而 `floor_cleared` 自己可以被改小 ⇒「删五行 + 地板降五」这一刀今天不会红
    （`test_floor_is_monotone_and_cannot_be_a_wish` 是在合成表上证「地板写不成愿望」，不是对 git 里上一版做差）。
    **结案读数**：闸门新增出口 `FLOOR_WENT_BACK`（基准 = `git show HEAD:docs/motion_surface_ledger.json` 的地板），
    临时落刀「删一行 + 地板 70→69」⇒ 旧判据 `BELOW_FLOOR` 是绿的（69 行 ≥ 地板 69），新出口红：
    `MOTION_LEDGER_FLOOR_BASELINE head=70 now=69` + `MOTION_LEDGER_RESULT=red 不合法格=1`；`git checkout --` 还原后 `RESULT=ok`。
    三格自检在 `scripts/tests/test_motion_surface_gate.py::FloorBaselineTests`（降了要红 / 没基准不许算红 /
    本仓库必须读得到基准），电池 298 → 301。
185. **结论句里的数字要能被脚本重算，否则它就是我手抄的印象**（R143 复核开，180 的一般形式）：
    本轮查出四处「能从仓库算出来却由我抄写」的数：R141 的「七行合计 100/105」（实 99）、
    「改成 `VisualShape.rounded` 之后 24 条全绿」（对不上任何一卷：`--filter HotKeyRecorder` 是 14 条、
    `VisualTokenTests` 是 12 条）、R140 的「八格 = 3 kept + 5 判过不适用」（实为 2 kept + 6 不适用，
    由 `6f0c609` 的 verdict 差值证明）与 `MISSING=134`（帧基线从 `fa625f1` 起就是 136）。
    判据先做最小的一格：**同一节里标题声明的分数要等于七维表行相加**（它已经红过一次），
    其余按 180/181 的路子走。另记一条卫生：`git blame` 显示这些都是**写入当轮就错**，不是后来漂移的。
**177 追记（R143 的第二半：spike 已答，这一条现在可做）**：动手前先跑了一次性 spike（临时文件跑完即删、不进提交），
问的是「F7 之后，捕获夹具那扇**非 key** 的窗口还进得了录制态吗」。两臂各一次，原样读数：
`SPIKE_R144 style=orderFrontRegardless key窗口=false 响应者前=NSWindow 后=HotKeyRecorderButton 录制中=true 高色度=1330`
`SPIKE_R144 style=makeKeyAndOrderFront key窗口=false 响应者前=NSWindow 后=HotKeyRecorderButton 录制中=true 高色度=1329`
⇒ 三点同时成立：① 非 key 窗口拿得到第一响应者（F7 那道守卫不会把夹具挡在录制态之外）；
② `makeKeyAndOrderFront` 在 App 未激活时同样给不到 key（两臂都是 `key窗口=false`）⇒ "要不要 makeKey"在这一格里不是变量；
③ 那一圈在离屏通道里画得出来（1330 / 1329，与 R143 修好的判据读数同量级）。
⇒ 177 照原计划做（`SettingsCategory.shortcuts` 加录制态变体，136 → 138，`--must-include` 同步改，同一轮里 `update` 基线），
**不再有"通道可能拍不到"这个前提**；下一轮（R144）第一件事就是它。
186. **runner 上在屏探针那一卷这次**挂**在 `testOffScreenProgrammaticSelectionIsRevealedAndNotJumped`**（R143 读 `1427e46` 那跑开，run 39052480365）：

**187. 在屏覆盖闸门还读那条会丢的通道 —— "它在 runner 上确实跑过"应改由心跳+闭合判**（R146）

**188. 把帧级状态自证接进 CI 的捕获步骤（第一遍 report-only）**（R147）

**188 追记（R148）**：本轮做的是 187 的 ①，188 仍欠（帧尺还没在 runner 上读过）。

**192. 两格已判完的动效位点还进不了表 —— 动效账本只能由生成器写，手改会被三格守卫同时抓住**（R151）
本轮真看了 `menubar-refreshing-320x120-light/dark` 并判完两格：**菜单栏/状态菜单 × 加载 = not-added**（`NSMenuItem` 挂不了动画视图，而 macOS 的原生菜单在加载时就是改文字；`Sources/ClipboardHistoryApp/Managers/MenuBarController.swift:147` 已经在这么做，再加一个假转的圈等于把「文字说在算、图形说没在动」同时讲给用户）；**× 错误 = not-applicable**（这扇表面没有错误态：算不出来回落到「暂无推荐」，真失败走提示条与详情回执，那是另外两个表面）。
但把它们手写进 `docs/motion_surface_ledger.json` 之后，电池当场红了四格，而且红得对：`test_the_committed_table_is_the_generators_own_output`（已提交的表 != 生成器输出 ⇒ 有一边是手改的）、`test_the_printed_row_count_is_the_committed_one`（70 != 72）、两格 `test_final_report_claims`（§9.3 写 101 格未判，而表算出来是 99 ⇒ 报告停在旧读数）。⇒ 已把手改**回退**，两格判定留在账上。
要做的：把这两行加进生成器的输入并按生成器重出表（同一轮里把 §9.3 的那句改成由表推导），并顺手回答 190（量纲分叉）—— 两者都是「手抄/手改共享表」这一族，守卫已经在了，缺的是走对入口。
**192 追记（R151 结案）**：两行已按生成器入表（`.scratch/motion-audit-2/make_surface_ledger.py` 加两条 tuple → `MOTION_LEDGER_ROWS=72 已清账=72 未清账=99`），§9.3 那两句陈旧计数同时改成由表推导的读数（`已判 60/未判 102` → `72/99`；`行数=70 … 未清账=101` → `72 … 99`），`MOTION_LEDGER_FLOOR_BASELINE head=70 now=72`（地板只升不降），电池 `Ran 333 tests … OK`。190（量纲分叉）**仍欠**。

**190 追记（R152 已修，守卫仍欠）**：仪器 `curve_from_ledger.py` 的推导改成**按每格自己的分母归一** —— 七分制表（`14/15`）走 `mean(num/den)×100`，百分制表（裸 `92`）走 `mean(num)`，两种都不再乘统一系数。真台账重读：`MEAN=91.9`、`PHASE2 n=144 mean=92.10 min=82 max=99`（修之前是 `mean=170.69 / max=617`）。而那批 612/609/605 是**我第一版修法**（一律 ×100/105）造出来的，被仪器自己打印的整条曲线当场抓到 —— 「把整条曲线打出来」这一格是有牙的。R146–R151 六轮现在读成 86/90/84/82/86/90，都 <90，与那几轮诚实扣掉的「真实视觉审查」一致。

**193. 七维表的量纲守卫还没写：两种约定必须落在同一尺度、混表必须拒绝推导**（R152 / 190 的尾巴）

**191 追记 3（R153：修法被 runner 证伪，问题改写）**：宽度那一维（`cardFill` 要求最长连续段 ≥40% 带宽）在 runner 上**没挡住**那两格 ——
`本机读到 2 格材质，「统计」却有 4 格没进卡片计数` 与 R150 逐字同形，且 `CARD_INSET_ALL settings-shortcuts-recording light=5.0` 说明那一层有左沿有首墨、是**宽的**。
所以问题从"怎么把窄层判掉"改成"**runner 上那两格宽的层到底是什么**"。下一步只做一件事、且不碰任何判据：
在 `CARD_INSET_CAPABILITY` 旁边加一行形状读数（每格：最长连续段 ÷ 带宽、过关行数、页底亮度、层色号），
让 runner 自己回答。两种候选解释各有对应的读数形状：整列同层 ⇒ 过关行数 ≈ 全带高、层色号与页底差 ~8；
描边带进来的行 ⇒ 过关行数少而集中、色号偏彩。看到读数之前不加出口、不降地板。

**194. runner 上六张 `-1040-` 高帧报「95% 像素未画」，被卡片那朵红盖着没单独读**（R153 / U-514）
`testCaptureKeyViews`（`UICaptureHarness.swift:3210`）在 run `39118326554` / `39118085686` 的 `STEP[13]` 里红：
`settings-privacy-tall / settings-recommendations-tall / settings-privacy-excluded` 的亮暗六张帧
「有 95% 像素未…」—— 与 R141 记过的 runner 空白帧是同一族通道事实。要做：先确认这一族**本来就该在 runner 上 skip**（帧内容画不出）
还是这条判据缺一个有名字的机器出口；不许把它并进 191，也不许直接放宽 95% 这个数。
仪器已经按每格分母归一（R152），但仓库里**没有一格测试**钉住这件事。下次有人写第三种表形状（例如 `| 名称 | 92/100 |` —— 分母 100 不在 `(14,15)` 里 ⇒ 那行被静默丢掉、七行凑不满就 `DERIVED_BAD`，而曲线照打旧数），量纲会再一次混进同一条曲线，而这次要问的是「数对不对」，不是「有没有断档」。要写的两格：① 合成台账里七分制 14/15 与百分制 93 必须给出同一个读数（±1）；② 同一张表里混两种约定必须 `DERIVED_BAD` 且不推数。写法照 `CurveGapGateTests`：合成台账写进临时目录 + 复用模块级 `run_curve(cwd)`，**不要 import 仪器**（两次 import 命中 `sys.modules` 缓存，第二遍读的是第一遍那份台账 —— 本轮第一次就错在这）。

**190. 自评曲线把两种单位加在了一起：R145 那类表出百分制，R146–R148 三节出 0–15 的每维均值**（R148）
仪器 `curve_from_ledger.py` 现在打的是 `145=91 146=13 147=14 148=12`，而它同一行还打 `PHASE2_TO_47 mean=91.30` ——
那个均值把百分制与 0–15 混在一起算，**已经不可引用**。要做的：先复现分叉（同一份台账里两节表各跑一遍，看仪器从哪一列取值），
再统一估计量（要么所有轮次都写 `**均分 NN.N**` 且仪器只读那一行，要么全部由表推导并固定一种刻度），
并配一格"同一份台账里所有轮次的分数量纲一致"的守卫（红要有名字：哪几节是 0–15、哪几节是百分制）。
在修好之前，任何引用 `PHASE2_*` 均值的账本句子都要先复核它读的是哪种单位。

**189. 覆盖闸门的 summary 要带机器键 —— 登记表说的是 runner，喂本机日志会造出 6 朵 `NOW_RUNS`**（R148 / U-502）

**191. runner 现在看得见 2 格卡片材质、却量不到任何卡片段（连系统参照也是）—— 两朵 capture 红自 R145 挂着，先分辨再动判据**（R149）
证据（run `39114424945` / `3a557fb`，R145 的 run `39103361921` 同形）：
  * `testSettingsCardHorizontalInsetIsMeasuredAgainstTheSystemGroupBox` ⇒ `系统参照只有 ["light"]`、`被告读到 2 格材质却只量到 1 格内缩`、`未判 29 格`，其中 `cardprobe-groupbox-default dark[参照]=有材质但找不到卡片段（fill=60）`；
  * `testSettingsCardVerticalRhythmIsOneNumber` ⇒ `本机读到 2 格材质，「统计」却有 4 格没进卡片计数（light/dark 全 `填充=-1`）`、`名单只有 1 格 < min(8, 2)`。
为什么先不修：R100 的机器前提（`materialCells == 0` ⇒ skip）已被这组读数推翻，新的形状有两种解释且修法相反 ——
① runner 镜像变了导致材质与背景同层（该加的是「参照自己读不到 ⇒ 这一档不判」的出口）；② 分段那一关在这台机器上真的看不见（该修尺，且**不许**加出口）。
分辨实验：读失败正文上方的 `CARD_FILL_CANDIDATES cardprobe-groupbox-default dark …` 那一行，比较 `fill=60` 与那一档页面亮度的差值 ——
差值小 ⇒ ①；差值大而仍读不到段 ⇒ ②。判据在实验出结果之前**一律不动**，两条红保持会红。
本机那一遍 `CLIPBOARD_HISTORY_UI_INTERACTION=1` 下 11 条全跑完，把它喂给闸门 ⇒ 六条登记为 `cannot` 的用例全被反驳成「runner 上其实能跑」。那句话是**假的**，因为主语错了：闸门读的是哪台机器的日志，输出里一个字都没写。要做的：summary 行带上与 `MotionFilmstripTests.filmstripMachineKey()` 同源（或直接读 `PROBE_FPS 机器=` 那一格）的机器键，并且当机器键不是 runner 那一台时，把 `NOW_RUNS` / `NOT_RUN` 降级成 `PROBE_GATE_WRONG_SUBJECT=<键>` 一句有名字的话 —— 登记判定只对它登记的那台机器成立。
`frame_recording_proof.py` 今天只对本机 `/tmp/shots_r145` 跑过一次。要做：① 在捕获那一步后面调用它（帧目录用 CI 自己的 `/tmp/shots-ci`），
**只汇报不拦**；② 读 runner 第一遍的 delta 与四边读数；③ 升硬门的判据先写死在这里 ——
runner 的四边读数 ≥ 本机最小读数（102）的 50%，且两档同形，才允许把 `FRAME_STATE_RESULT=red` 变成退出码。
不照抄本机地板当 runner 门限（U-486 就是这一步踩出来的）。
`probe_coverage_gate.py` 只吃 `/tmp/ui.log`：一条用例只要结论行没落盘就被记成 `NOT_RUN`，
而 R146 已经证明结论行会说谎（那块被 SIGKILL 带走的是 stdout，不是产品）。
要做的三格，按顺序：① 让它读同一份 `probe-pulse.log`，把"跑过"判成**有心跳且有闭合**（与报告脚本同一个口径，别再各算一套）；
② 缺席因此分成三种有名字的出口：`queued`（没轮到）/ `hung`（心跳未闭）/ `log-lost`（闭合了而日志没结论行）——
第三种不该算 runner 不可跑；③ 用一次真 CI 读数重判 `testOffScreen…` 该不该翻回 `can`，并把 186 的登记一起对齐。
不给这格配"翻回 can"的预设结论：本轮只有本机那一遍的 11/11，runner 上的闭合通道**还没量过一次**。
    三个读数一起看才是这一格的形状 —— `UI_PROBE_HUNG=testOffScreenProgrammaticSelectionIsRevealedAndNotJumped`
    与 `=testRightClickMenusAppKitWouldShowAreChinese`（后者一次没轮到）、
    `PROBE_COVERAGE_SUMMARY … 本次下结论=5 红=1`（那 1 条红就是 NOT_RUN：登记 `runner=can` 而日志里没有它的结论行）。
    ⇒ 这一跑 CI 红**不是**产品判据红，也不是我改的脚本坏（同一份合成日志在 `28246ed` 版脚本上退出码同样是 1，实测对过）；
    是那一卷没跑完。
    **第二跑已到（run 39054860497 / `f78af12`，同一台 runner）**：同一句
    `NOT_RUN testOffScreenProgrammaticSelectionIsRevealedAndNotJumped：登记为 runner=can，而这次日志里没有它的结论行`
    与 `本次下结论=5 红=1` **原样重复** ⇒ 它不是换班，是**连着两跑都挂在那一条**。
    同一步里另一件事：那跑还红在 `PYTHON_SUMMARY_MISSING=1 没有汇总行 OK` —— 那是 R143 part 2 我自己写窄的门
    （`^OK$` 不认 `OK (skipped=1)`，本机 0 skip 所以看不见），已修并记 **U-487**。
    **下一步**：不再等第三跑。按 R87/R118 的规矩，两跑同形已经够格改登记：
    就把这条用例的 `runner` 登记从 `can` 改成 `cannot` 并写清 reason（挂在哪、什么旁证），
    而不是把地板放松或把它 skip 掉。挂的成因候选：这条用例要真的 `orderFront` 一扇带选中行的列表窗口，
    而 runner 上窗口/事件循环的行为与本机不同（R60/R61 那一族的旧账）。
**186 追记（R144 改登记，处置完成一半）**：三跑同形已到（run 39052480365 / 39054860497 / 39056187840，
对应 `1427e46` / `f78af12` / `f26f4c9`，同一句 `NOT_RUN testOffScreenProgrammaticSelectionIsRevealedAndNotJumped`
原样重复）⇒ 不再等第四跑：名册里这条由 `can` 翻回 `cannot`，reason 带三跑 run 号、`UI_PROBE_HUNG=` 原文，
**以及 R94 的反证**（run 38857388449 那一跑它 `passed`）⇒ 结论收窄成"这台机器上它今天会挂"，
不是"runner 结构上拍不到"。两向门落进电池（`HungCaseRegistrationTests` 五格：can 缺结论红 /
cannot 带 reason 不红 / 没 reason 的 cannot 仍红 / cannot 而它跑完红在 NOW_RUNS / 今天的登记配今天的日志全绿），
新夹具 `fixtures/r144_probe_hung_ui.log`。**这条不开着的原因**：登记与"成因"是两件事 ——
挂在哪一帧仍未实测（`UI_PROBE_SAMPLE_UNPARSED=1`：读不懂文件 ≠ 它挂在未知帧上），
下一轮要真去 runner 上拿旁证；若哪一跑它又跑完，闸门会红在 `NOW_RUNS`，那时带着读数翻回去。
**177 追记（R145 动手了一半，把两处硬事实留在账上）**：本轮真的开始做那张夹具帧，撞到两件事，都值得下一轮直接用：
① **`Fixture.settle` 这个钩子放不了那一次点击** —— 捕获路径在 `settle` 之后还会 `window.makeFirstResponder(nil)`
清闪烁 caret，而录制态是靠第一响应者活的（`HotKeyRecorderButton.resignFirstResponder` 会 `cancelRecording`）
⇒ 先点再清 caret，等于自己把刚点出来的状态取消掉。要新增一个跑在 **caret 静默之后**的 `interact:(NSWindow)->Void` 钩子。
② Swift 侧的形状：`Fixture.init` 的 `build` 是**最后一个无标签参数**，一旦前面出现带标签的 `interact:`，
尾随闭包就不再映射到它（编译报 `expected ')' in expression list`）⇒ 正确写法是 `withAppKit` 那一族的
`withInteract(_:)` 复制器，而不是往 init 里加参数。
剩下的那一处编译错（闭包里 `HotKeyRecorderButton.self` 报 implicit use of `self`）本轮没来得及定位，
**改动已全部 `git checkout` 回退，仓库没有半成品**。下一步从"加 `interact` 钩子 + `withInteract`"起步，
136 → 138 之后要在同一轮里 `frame_baseline.py update`，并给那张帧配一条**状态自证**判据
（帧名声称"录制中"，就得由帧自己的高色度像素证明，别让它成为一张会撒谎的证人 —— D-024 那条规矩）。
**177 追记（R145 结案）**：录制态进了帧基线 —— 新夹具 `settings-shortcuts-recording`（亮 / 暗两张，136 → 138），
从产品入口 `performClick` 进入，夹具内断言 `window.firstResponder === button`。
帧自己的证据：差异包围盒 x 958..1212 / y 504..550，高色度 亮 386→829、暗 391→832；
基线同一轮 `update` 后 `COMPARED=138 CHANGED=0 MISSING=0 ADDED=0`；盲区名单被闸门逼着 +1（vibrancy 子树）。
**收尾还欠一格**（这条不撤，改成判据账）：把"录制态帧的高色度像素 ≥ 地板"变成电池里会红的断言 ——
今天它只由本轮脚本量过一次，帧名说谎目前还只能靠人眼发现。
**191 追记（R150 定性完成，未动手）**：分辨实验已在**现有**日志里跑完 —— `CARD_FILL_CANDIDATES settings-general/stats light|dark 前三=(页底:480)` 排除了「分段那一关真看不见」这一支；`CARD_INSET_ALL settings-shortcuts-recording light=5.0` 指出 runner 上唯一的「第二层」是 R145 新帧那颗高亮 pill（暗档 60 vs 页底 52，差 8 > 门限 3）。⇒ 因是**一张新帧顶翻了 `materialCells == 0` 这个机器前提**（U-506），不是产品少画了东西。
修法（下一轮做，本轮不动判据）：`cardFill` 除了行数还要问**这一层有多宽**（行内最长同色段占内容宽的比例；卡片横贯 ~600pt，pill 只有 87pt），而不是给录制态帧开具名豁免。验收两头都要看：runner 上 `materialCells` 回到 0 ⇒ R100 那条 skip 自己响、两朵红消失；本机 `CARD_INSET_CAPABILITY 有材质` 与 `CARD_ABOVE_CAPABILITY` 两行的数字**不许变小**（变小就是新尺把真卡片也挡掉了）。
门槛先量过再定（临时尺 `/tmp/r151_span_probe.py`，只用于形成问题、不进判据）：
  * **我第一个想到的「跨度」（该层最左出现到最右出现 ÷ 带宽）是不分辨的** —— 录制态 pill 那两行读到 0.87/0.91，真卡片行读到 0.95/0.96：pill 行的众数在带子两端都出现（与卡片底色同桶），最左最右把整幅框住了。照它写门槛，尺会*看起来*修好了而什么都没拦住（R110 那一族）。
  * 有分辨力的是**行内最长连续同色段 ÷ 带宽**：pill 行 0.08–0.13，真卡片行 0.58–0.96，空行 1.00。所以 `cardFill` 要数的是「有多少行的最长连续段 ≥ 门槛」，不是「有多少行的众数 ≠ 页底」。
  * 候选切点 0.4（两侧余量各 ≥3 倍），但**先扫 26 格帧的行分布再钉**（分档 ≥2/≥8/≥16/≥40 那一族口径）——现在只有 6 行样本，不够钉门槛。
**191 追记 2（R151 已动手）**：门槛扫过了（28 张帧逐行最长连续段：pill 0.08–0.13 / 卡片 0.58–1.00 / 空行 1.00 ⇒ 切点 0.4），`cardFill` 已加上这一维；本机三行能力读数与改前逐字相同（`有材质=32（被告=26 参照=6）量到=26 未判=0`），两格 runs 专项测试会红。
**仍欠 runner 那一半**：下一跑要看 `CARD_INSET_CAPABILITY 有材质` 从 6 掉回 4（只剩参照）或被告归零 ⇒ `materialCells == 0` 的 skip 重新响 ⇒ `STEP[13]`/`STEP[15]` 两朵红消失。看到那一行才结案。



**186 追记（R146 结案一半）**：成因有名字了，而且**不是产品** —— 那条被记成"这台机器上它今天会挂"的
`testOffScreenProgrammaticSelectionIsRevealedAndNotJumped`，本机同一份通道量到的真实顺序里它是第 6 颗心跳且**已闭合**；
CI 那次 `pulse=7 started=6 concluded=5` 里未闭的是第 7 颗 `testRightClickMenusAppKitWouldShowAreChinese`
⇒ 少掉的是它的**结论行**（stdout 尾巴随 SIGKILL 整块丢，R88/R90 各实测过一次）。
本轮落地的修法：探针加 `tearDownWithError` 的 `PROBE_DONE` 闭合行，报告脚本改成"心跳 − 闭合"这一份文件内部的减法
（`UI_PROBE_FILE_CHANNEL` / `…_CLOSED_ALL` / `…_AMBIGUOUS` / `UI_PROBE_HUNG_WITHOUT_CLOSE` / `UI_PROBE_LOG_CONCLUSION_LOST`），
两条讲不通的形状仍然红。登记值仍留 `cannot`，但 reason 已改写成仪器 —— **翻回 can 这件事交给 187**，
因为 coverage 闸门今天还读那条会丢的通道。欠一次真 CI 验收：下一跑要看到 `UI_PROBE_HUNG_CHANNEL=file`，
那时 186 才叫结案。

**177 追记（R147 结案）**：收尾那一格落地 —— 新尺 `scripts/frame_recording_proof.py` 读**已写出的 PNG**，
判"录制态比静置态多出的高色度 ≥ 900、四条边各 ≥ 40、改动包围盒 ≤ 340×90"；真帧读数 亮 1772 / 暗 1764、四边 上726/下726/左102/右102、
包围盒 x 958..1213 / y 503..550。电池 7 格合成对照把四条出口各自打红（`Ran 327 tests … OK`）。
177 到此结案；它派生的"接进 CI"另开 188，不再挂在这条上。

**195. 改过 `.py` 的变异跑必须禁写字节码，否则测的是上一版字节码（R154）**

R154 实测：把 `scripts/frame_recording_proof.py` 里 `return 1` 改成 `return 0`（**字节数不变**），跑完再 `cp` 还原；
还原与变异落在**同一秒**内 ⇒ macOS 放在仓库外的缓存
`~/Library/Caches/com.apple.python/Users/…/scripts/frame_recording_proof.cpython-39.pyc`
（失效判据＝源码整秒 mtime + size）自认新鲜 ⇒ 之后的全量电池**执行的是变异版**，
本地打出 `FAILED (failures=1)` 而源码是对的。`find scripts -name __pycache__ -delete` 无效（缓存在别处）。

下一步（做这件事的判据形状，不是"记得小心点"）：
① 变异执行器（`.scratch/motion-audit-2/mutate_*.py` 这一族）在**跑判据之前**统一带上
   `PYTHONDONTWRITEBYTECODE=1`（或 `python3 -B`），并把这条写进执行器而不是只写进台账；
② 若下一轮还会做 python 侧变异，配一格自检：**变异前后同名文件的 `co_consts` 必须不同**
   （不同才证明执行的是刚编译的那一份；相同 ⇒ 缓存没失效，这一格红）。
不许做的事：为了让本地绿而把 `cp` 换成 `touch`（那只掩盖整秒问题，size 相同这一半还在）。

与 188 的关系：`frame_recording_proof.py` 想接进 CI（report-only）之前要先决定
「runner 没 Pillow ⇒ 天天 `FRAME_STATE_NOT_RUN=pillow`」这一格算不算噪音：
要么 CI 装 Pillow，要么把接法改成"本机跑、读数入账"。这条决定归 188，不在这里。

**196. exit ② 的谓词落在"有没有材质"上，而 runner 的形状是"有材质但没有卡片段"（R156）**

现象（run `39120938129` / `8faef80` 的 `STEP[13]`，三句同因）：
`XCTAssertEqual ("1") is not equal to ("2")`（参照只剩 `["light"]`）、
`被告读到 2 格材质却只量到 1 格内缩`、`未判 29 格`（其中绝大多数是 `这一带没有第二层（fill=-1）`，
另有 `settings-shortcuts-recording dark` / `cardprobe-groupbox-default dark` / `cardprobe-scroll-groupbox dark`
是 `有材质但找不到卡片段（fill=60）`）。

为什么现在没 skip：`testSettingsCardHorizontalInsetIsMeasuredAgainstTheSystemGroupBox` 的出口 ② 写的是
`if defendantMaterial == 0 { throw XCTSkip(…) }`，而 runner 上 `defendantMaterial == 2`（那两格是 fill=60 那一类）
⇒ 谓词问的是"有没有第二层"，需要问的是"**有没有一段可判的卡片带**"。

下一步（形状，不是"小心点"）：
① 谓词换成"被告里量到卡片段的格数 == 0"（本机是 26 ⇒ 不受影响；runner 是 0 ⇒ 走出口）；
② skip **之前**发一行 `CARD_INSET_NOT_RUN=…`（带 `defendantMaterial` / `measured` / `fill` 三个读数与原因）——
   名字必须以 `_NOT_RUN` 结尾，`ci_capture_gate.py` 认这个后缀（R36 / U-59），且要满足 D-170 的"能力行排在闸门与 skip 之前"；
③ 本机先用**合成读数**验一正一负：一份"全 fill=-1"的假表 ⇒ 必须走 NOT_RUN；一份"26 格有段"的表 ⇒ 必须照旧判；
④ 不许顺手放宽 `未判 ≤ 4` 与 `measured ≥ min(16, defendantMaterial)` 这两条地板（那是把通道问题洗成产品结论）。
与 191 的边界：191 问的是"那两格假材质是什么形状"（已在本轮被 runner 读数收窄为"没显"），这条问的是"出口为什么没接住它"。

**196 追记（R157 落地，待 runner 验收）**：两处出口已换成"每一档至少有一格量到可判卡片段"
（`CARD_INSET_BANDS light|dark`、`CARD_ABOVE_BANDS light|dark`；skip 之前各发一行 `*_NOT_RUN` 带四个读数与原因）。
本机 `light=13 dark=13` ⇒ 两格照判、绿；runner 自己打印的 `量到=1`（暗档 0）代进同一谓词就是 skip —— 这是算术，
**执行证据等下一跑 CI**。四条地板一条没放宽。剩下的 ③：把"单档为 0 才 skip、两档都有段时不许 skip"
配成一格合成对照（两份假名册，一份两档都有、一份单档为空），在那之前这条出口只算接上、不算有反向守卫。
**194 追记（R161）：「屏幕装不下」这条解释被本机的读数证伪，别再往那边走**

我这一轮真的写了那条出口（`CAPTURE_NOT_RUN … 窗口要 1040pt 而主屏可视高 Npt`），然后在本机把它撤了：
`CAPTURE_SCREEN main=有 visibleHeightPt=847`，而同一次捕获里那六张 `settings-*-tall-720x1040` 是
`blank=0.0%`、画到第 2079 行（1440x2080 像素全画）⇒ **离屏窗口不被屏幕可视高夹住**，前提假。
第二条独立证据：闸门红的是"95% 未画"，而"帧名==像素尺寸"由 R18 那条守卫钉住 ⇒ runner 上那六张位图
**尺寸正确、内容缺失**；若窗口被夹小，先红的会是尺寸那一格。

下一步该打的三个数（都在 `render` 里，同源于那一次捕获，不做判定、只出读数）：
① `window.frame.height`（窗口实际多高）；② `contentView.frame.height`（内容视图多高）；
③ `rep.pixelsHigh / fixture.size.height`（位图与请求的比）。
三种成因各自的样子：窗口被收小 ⇒ ①<1040；内容视图没铺满 ⇒ ①=1040 而 ②<1040；
画了但整层不合成 ⇒ ①=②=1040 而 ③=1、内容却透明（这一种与 191/196 的"材质不合成"同族，
那时才该谈未运行，而且要按 196 的形状：带两个同源读数 + 名字 + 不放宽任何地板）。
不许做的事：把 95% 那条门槛调高、或把 `-1040-` 直接写进豁免名单（那正是这一轮差点犯的错）。
**197. 统计屏的热图比它上下的文字窄一条 118pt 的带（R166 量出来，本轮刻意没改）**

测量（`settings-stats-populated-720x540-light.png`，2x，1pt = 2px）：
网格右沿 **560.5pt**、说明段右沿 **688.5pt**、卡片内沿约 678.5pt ⇒ 图表块右侧有一条 **~118pt** 的空白带，
而同一张卡片里摘要行与两段说明都铺到内沿。用户看到的是"图没画满"，不是"图比较窄"。

两条候选修法（各自代价，先做 spike 再动仓库）：
① **让格子按可用宽度自适应**（`GeometryReader` 把 26 周铺满）：最贴近"铺满"的直觉，
   但格子尺寸会变 ⇒ 必须同时过 `testSettingsCardVerticalRhythmIsOneNumber` 的 4.5pt 极差、
   `contentMustFit`，并在同一笔里 `frame_baseline.py update`（138 帧会变）；
   hover 描边的粗细也要跟着格子缩放，否则 5pt 的描边在小格子上会糊。
② **保持格子尺寸，把整块居中**：改动最小、不动帧尺寸，但"居中"会让左轴与其余卡片不一致
   （这个 App 的左轴统一是 R31/R39/R104 一路判下来的），所以要先回答"图是内容还是控件"。

不许做的事：把 118pt 读成"26 周本来就这么多"就结案 —— 月份轴是**按网格宽度**分布的，
所以轴也一起停在 560.5pt，那是同一件事的两处表现，不是两条独立事实。
**194 追记 2（R167）：runner 的几何读数到手 ⇒ 收窄到第三种情形，但还差一根分辨轴，出口暂不加**

`--log`（不是 `--log-failed`；那行是 report-only 的捕获步骤打的）：
`CAPTURE_GEOMETRY settings-privacy-tall light requested=720x1040 content=720x1040 host=720x1040 screenVisibleHeightPt=681`
六张高帧同形。⇒ 前两种解释被同一行排除：窗口没被收小（content=1040）、内容视图铺满了（host=1040）。
剩两种没分开：**内容层没合成**（画了但没进位图）vs **根本没渲染**（画布是空的）。
分开它们的那根轴是"**最后一行有墨的 y / 画到的包围盒高**"：≈ 屏幕可视高 ⇒ 被裁；= 0 ⇒ 没渲染。
本轮把它加进 `CaptureMetrics` 之前**不加出口**（R153：两种解释修法相反时，判据保持会红）。
另一件已记进账的事：本轮我给出口造的两格正对照都是空的（本机没有空白高帧，强行放进循环的帧透明度 ~0，
两种实现都绿）⇒ "对照通过"不等于"对照有效"，先问对照里有没有对象。

**198. 变异名册里躺着一支陈旧死针（M541 命中=0），把预检的退出码混成"本轮也有问题"（R168）**

needle 预检现在打 `bad=1` 且**非零退出**，但那一格属于 `mutate_r97_card`（R97 时代的针，正文早被后续轮次改掉），
而本轮 M675–M683 九根针全部命中 1 次。两件事共用一个退出码 ⇒ 下一轮看到 `bad=1` 分不清"我的针是死的"还是"名册该清一次"，
最可能的行为是为了让它变绿去删那行 —— 那是把证据删掉。
该做的：预检按**表的新近度**分两栏报（本轮的表 vs 名册里的陈旧表），或对已被后续轮次改写的前任表显式登记 `retired`；
`ARM_TOTAL … dupes=0 repeats=0` 那一半保持硬红。判据要能红，但只该红在它真正说的那件事上。

**199. `CapturePathWriteBudgetTests` 的前提钉子挂在一次固定 0.4s 的 sleep 上，满载时会读不到刚写完的库（R168 实测红一次）**

原文：`XCTAssertEqual failed: ("459") is not equal to ("480") - 重新加载没拿到同一份库 ⇒ 下面测的是空库，白测`。
成因链：造 480 条之后只 `pumpMain(seconds: 0.4)`，而落盘在 `FileHistoryPersistence` 的保存队列上异步跑；
同一台机器同一份代码，整卷里那一格 8.6s 红、单跑 4 例 / 失败 0（退出码 0）绿 ⇒ 是**等待不够**，不是产品写丢了记录。
该做的修法（下一轮带自己的正对照）：把固定 sleep 换成**有界轮询**（每 0.1s 重开库比 count，等到相等或超时 5s；
超时才红，并把"等到了第几拍"打进读数），钉子从"睡多久"换成"落盘有没有落地"。
本轮**不改**：这一格是 R51 那批判据的承重，改等待方式要同时给"它仍能测出真的没落盘"配刀 —— 一笔 0 产品改动的轮次里做这件事，
验证预算不够，做了只会留下一个没对照的改动。

**194 追记 3（R168）：分辨轴已装好，等 runner 的 `CAPTURE_DRAW` 读数**

本轮把两件事分开落了：
① 放行决定 = `shouldRegisterBlankAsMachineGap`（可单测；M675–M678 四种错法全红）；
② 分辨轴 = `drawnBoundingBox` / `CAPTURE_DRAW`，三态哨兵把"量不到 / 根本没渲染 / 被裁 / 画满"分开（M680–M682 三种坏法全红）。
**出口仍然没接**：本机 census `with_geometry=0` —— 高帧一张都不空，谓词在本机的唯一证人是单测。
下一跑 runner 会自己打 `CAPTURE_DRAW settings-*-tall … drawnBoxPt=?`：`0` ⇒ 判"根本没渲染"；
`≈ screenVisibleHeightPt` ⇒ 判"被屏幕裁"（那时 161 那条被证伪的出口才以**另一种谓词**回来：按包围盒放行，不是按屏幕高）；
`≈ 1000` ⇒ 这把尺自己坏了，回头修尺。三种读数对应三种处置，谁也不再靠"最像"签字。

**200. `defaultWindowWeeks` 的注释说"最小窗口右栏约 412pt 可用"，这个数自卡片化之后从没被复量（R169）**

197 的两种修法各自撞的是不同的墙：`加周数` 撞组件帧（R169 已量成数：余量 19pt、一周占 14pt ⇒ 只够 +1 周），
`放大格子` 撞垂直节奏（一列 7 格，格子长多少整张图就高多少）。而**第三种可能**——"其实最小窗口也放得下 +2 周"——
现在没人能判，因为它依赖的那个 412pt 是 R 早期写在注释里的数，R101/R102 把统计屏卡片化之后从没复量过。
该做的读数：从产品自己的布局链取"最小窗口下热图那格的可用宽"（`SettingsViewLayout.minimumWindowSize` 那条链，
或一条带 `contentMustFit` 的最小窗口夹具），把它变成会红的判据而不是注释里的散文。
拿到那格数之后才谈 197 到底改不改、改哪一种；**顺序不能反过来**（R162/R167 那条）。

**197 追记（R169）：『加周数』这条候选被量成 +1 周放得下、+2 周顶破**

上一轮写"两条候选修法"时我以为 26 周是上限。本轮 `DailyCopyHeatmapWidthBudgetTests` 用产品自己的令牌与夹具那几行算出：
可用宽 398pt、26 周用 379pt（余量 19pt）、27 周 393pt（仍放得下，剩 5pt）、28 周 407pt（顶破）。
⇒ 『加周数』最多只能削 14pt，填不掉 118pt 的带；剩下的仍要等 200 那格最小窗口的读数。
另：预检本轮把两支活针（M684/M686）报成 `命中=0` —— 见 198 追记，处置是以真刀为准。

**198 追记（R169）：预检还有第三种坏法——把**活针**报成死针**

R168 记的是"名册里的陈旧死针与本轮针共用一个退出码"；R169 又添一种：`mutate_r169.py` 的 M684/M686
needle 在 `Sources/…/VisualTokens.swift`、`DailyCopyHeatPolicy.swift` 里各命中**恰好 1 次**（python 直接数过），
预检却报 `命中=0`，而真刀两把都 CAUGHT。⇒ 预检的 needle→path 解析对 `Sources/` 那一半不可靠。
规矩：**预检只当线索，裁决权在真刀**；下一轮把这支仪器的"报 0 但真刀 CAUGHT"做成一格可复查的对照（别改判据）。

**194 追记 4（R170）：分辨轴到手 ⇒ 结案为「通道限制」，出口只认实测到的形状**

runner `39152321051`（`72279ff`）六张高帧全部 `requested=1040 drawnBoxPt=205 drawnBottomPt=1040 transparent=95.9{'n_runner': '6', 'box': '205', 'bottom': '1040', 'screen': '681', 'blank': '95.9', 'req': '1040', 'local_boxes_lo': '1040', 'local_boxes_hi': '1040', 'local_n': '6', 'local_marker': '0', 'swift_n': '862', 'swift_skip': '42', 'swift_fail': '0', 'full_exit': '0', 'caught': '12', 'arms_total': '12', 'restore': 'yes', 'arm_map': 'M675→testGeometryAxesStillGateIndependentlyOfTheBox（ran=10）, M676→testShortFixturesAreNeverReleased（ran=10）, M677→testShortFixturesAreNeverReleased（ran=10）, M678→testBlankFrameLoopCallsThePredicate（ran=10）, M679→testTallFixtureThresholdHasOneSource（ran=10）, M680→testBoundingBoxConvertsPixelsToPointsByBackingScale（ran=10）, M681→testBoundingBoxUsesTheSameAlphaCeilingAsBlankness（ran=10）, M682→testBoundingBoxSeparatesNotRenderedFromClipped,, M683→testTallFixtureThresholdHasOneSource（ran=10）, M687→testRegistersOnlyTheBandShapeTheRunnerActuallyShowed（ran=10）, M688→testRegistersOnlyTheBandShapeTheRunnerActuallyShowed（ran=10）, M689→testReleaseBranchRegistersTheMarkerTheGateParses（ran=10）', 'compared': '138', 'changed': '0', 'surface': '行数=112 已清账=112 未清账=59 地板=112', 'frames': '138', 'cap_exit': '0', 'pre_bad': '3', 'run_id': '39152321051', 'run_sha': '72279ff'}creenVisibleHeightPt=681`，
本机同一批 `drawnBoxPt=1040…1040`、`transparent≈22%`。⇒ 三种解释各自被一条数排除：
`>0` 排除"根本没渲染"；`205 ≠ 681` 且带在下沿排除"裁到可视高"；几何三边相等排除"窗口被收小 / 内容没铺满"（R167 已排除过一次）。
处置：出口接线，条件是 `0 < drawnBoxPt < requested`，点火打 `CAPTURE_BLANK_NOT_RUN`（闸门 `*_NOT_RUN` 名字形状）；
两种形状**不放行**、红照旧：`==0`（捕获坏了）、`==requested`（画满却报空 = 两把尺矛盾，先修尺）。
**没结案的部分**：机制未命名（见新开 201），且本机点火 0 次 ⇒ 这条出口的真产物验收在 CI 下一跑（预期 `Capture gate` 那一步不再因这六张红）。
这一格从 R153 挂到今天，收的口是"不是产品缺陷"，不是"我知道为什么"。

**201. runner 的高窗离屏捕获只画出一条 205pt 的下沿带，机制未命名（R170 量到形状，没量到成因）**

形状（六张高帧同形，run `39152321051`）：`requested=1040 / drawnBoxPt=205 / drawnBottomPt=1040 / transparent=95.9% / screenVisibleHeightPt=681`。
本机同码同夹具：`drawnBoxPt=1040…1040`（画满）。
第一条猜测已经被否：「只画与屏幕可视区相交的那条带」——本机可视高 850 < 1040 却画满，猜测在自己身上就不成立。
第二条候选（"高窗的内容层在 runner 上只布局了底部一条"）需要一个**画到的带内是什么**的读数才能判：
下一轮可以从那 205pt 带里数一数量（有没有侧栏 / 卡片描边 / 文字行），与本机同一条带对账。
为什么现在不动产品：两种成因（通道 vs 布局）的处置完全相反，而 194 已经按"通道"结案了一半（出口只认形状），
布局那一半若有真缺陷，会在带内读数里露出来 —— 顺序是"先量带内是什么，再决定要不要怀疑产品"。

**199 追记（R171 落地）：固定 sleep 换成有界轮询，断言口径没动**

`pumpMain(seconds: 0.4)` → `awaitFlushedSnapshot(matching:in:)`：每一拍**重开一次库**（不读内存缓存），
由 `ArchiveReloadWait.outcome(seeded:reloaded:elapsed:)` 决定 `landed` / `keep-polling` / `timeout`，
到 `timeout=5.0s` 或 `maxPolls=60` 才红，并把 `轮询 N 拍 / 秒数 / 最后一拍 reloaded / 期望 / 成因` 写进取证文本。
真值表钉住两行容易糊的：`elapsed == timeout` 必须算超时（`>` 会永远多等一拍）；`reloaded > seeded` **不算落地**（那是读到了别的库 —— 临时目录被复用那一族）。
**仍欠（下一轮结案）**：打在 `==` 与 `>=` 上的两把变异刀本轮没跑 ⇒ 记 NOT-RUN；满载下的第二证人是真 CI 那一跑（本机全量卷 864 例 / 失败 0 只算一次抽样）。

**199 追记 2（R172）：三把刀补齐 ⇒ 结案（满载的第二证人仍待 CI 那一跑）**

R171 落地时明写"仍欠：打在 `==` 与 `>=` 上的两把刀"。本轮 `mutate_r172.py` 三臂全 CAUGHT、RESTORE_CLEAN=yes：
M690 `reloaded == seeded`→`>=` 红在 `testReloadWaitTruthTable`（读到比预期更多的库不许当落地）；
M691 `elapsed >= timeout`→`>` 红在同一格（边界那拍必须超时）；M692 `maxPolls=60`→`100000` 红在 `testReloadWaitIsBounded`（没上限会把这一格挂到 CI 超时）。
199 至此结案。仍记在账上的边界：满载下的**第二证人**是真 CI 那一跑（本机 R171 全量卷 864/42/0 只是 n=1 抽样）。

**194 追记 5（R172 复验）：出口在 CI 上真点火并被闸门认下 ⇒ 这一格正式结案**

run `39156179381`（= `546dc97`，R170 那笔接线）的 `--log`：`JOB build-and-test ⇒ success`，
`CAPTURE_GATE_RESULT=ok 红=0（已登记的 NOT-RUN 见上）`，整跑日志里 `Test Case … failed` **0 条** ——
这是自 R145 那两朵捕获红挂起来之后，这一族第一次不再红。
出口点火的原文六次（六张高帧各一次），形状如：
`BLANK_GAP_WOULD_RELEASE settings-privacy-tall-720x1040-light.png release=true requested=1040 content=1040 host=1040 drawnBoxPt=205 drawnBottomPt=1040 screenVisibleHeightPt=681`
配套 `CAPTURE_BLANK_NOT_RUN <帧名> …`，census `loop_items=8 with_geometry=6 would_release=6`。
**口径不变**：结案的是「不是产品缺陷」；那 205pt 的带里到底是什么**仍未命名** ⇒ BACKLOG 201 继续开着，
下一条读数该是「带内数量与本机同一条带对账」。

**202. 缺席文法只到文件粒度，所以「浮层/底部说明 × 空 / 选中」这两格本轮判不了（R173）**

六格清了，这两格**留白**：要证的是"这一行标签不可选中 / 空态时它本身就是空态文案"，
而 `缺席:<路径>=<词>` 只能在**整个文件**上复查 —— 那个文件里 `isSelected` 有 4 处（列表行用），
所以只要我写 `缺席:QuickPickController.swift=isSelected`，复查器就会红（它是诚实的），而我要的结论其实仍然成立。
正确下一步是**加粒度**不是放宽复查：在测试里用 `functionBody(named:)`/行级切片断言"底部标签那一段里没有 isSelected/onTapGesture"，
再把那条测试的路径写进 evidence。这一族 R143 记过一次（仪器粒度不够时，别把判据调松来迁就仪器）。

**203. 台账脚本靠"凭记忆写的锚点"插 STATE，锚点一过期就把块插到中间去（R173 撞到，已按声明轮次重排）**

R173 的 STATE 块被插到了 R170 之前而不是文件顶部，于是 `test_round_batch_consistency` 里那条
「STATE 自报轮次必须落在台账最近几轮标题的窗口内」当场红 —— 它报的是 `169 not found in [173,172,171,170]`，
而**读到的 current round 来自 STATE 顶部那块**，也就是说锚点错位会让"现在到底是第几轮"这件事被旧块顶掉。
另有一格同源脏数据：R169 那块的时间戳写成了 `02:2x` 占位、当时没钉，一直挂在文件顶部第二行。
本轮**已做**：写完台账后按块里声明的 `R\d+` 把 STATE 的块整体倒序重排（173/172/171/170/169/168…），并把 R169 那格 `02:2x` 占位时间戳钉成实际分钟；
下一步该把这条排序固化进收尾工具（`ledger-round-pipeline` / 台账批写脚本），而不是每轮靠人眼看顺序。

**204. 清账表里 `浮层/底部说明` 这个表面在今天的浮层里没有承载物：面板 stack 只有 field / empty / scroll 三个子视图（R174 量到）**

起因是我自己写理由时把主语当成"底部那一行"（R173 六格、以及更早的「悬停」那格都这么写）。
查 `QuickPickController.swift:262`：`NSStackView(views: [field, empty, scroll])` —— 面板里**没有**底部说明这一层，
`footerLabel` / `hintLabel` 两个名字在整个文件里 0 命中。R63 的账能对上：那句"空结果"的话原本挂在**表格下面**，
R63 把它挪到列表位置，于是"底部说明"这个名字留下来成了幽灵表面，而它真正的后继是 `empty`（属于「浮层/空态」那一表面）。
所以这不是"九格里判了七格"，而是**一个不存在的表面被逐格判过**。
两种处置，必须选一种并留下证据：① 认定这一层该有（键位提示、↑↓↩⎋ 之类）⇒ 那是一条产品需求，先做承载物、再判九格；
② 认定不该有 ⇒ 把表面从词表里撤掉，并在 DECISIONS 记"撤词表项"的理由，
   而不是留着它继续产生"每格都 not-applicable 所以已推进"的假进度（这正是目标禁止的那种"为清账而清账"）。
本轮只做了**换主语**（七条理由改成描述真实存在的视图 + 可复查的 `footerLabel`/`hintLabel` 缺席声明），
词表没动、格子数没动（仍 118/171）：选哪一种是下一轮的决定，且要有产品面的理由，不是为了让未清账变小。

**205. 看图那把 `frame_audit.py align` 是逐像素行的尺：它数出空态有 2 簇左边缘，却答不了"这两行同不同轴"（R174 量到形状，没量到成因）**

本轮看 `quickpick-empty-420x300-light/dark.png`（138 张盘上帧里挑的），同一把尺、threshold=40：
亮档 `有墨的行=50 跨度=415px 直方图=x≈108:18 x≈104:9 x≈44:7 x≈48:5` ⇒ 两簇（≈22pt / ≈55pt，帧 840px 宽 = 420pt，2px/pt）；
暗档 `x≈108:15 x≈104:11 x≈44:8 x≈48:5` 同形；对照 `quickpick-list-420x300-dark.png` 是 `x≈72:89 x≈68:18 x≈48:14 x≈76:10`（一簇为主、中位 75px）。
R64 的旧账写的是"空态那句在列表槽里**居中**，中心 209.25pt vs 面板 210pt" ⇒ 两件事不能同时是"一根轴"。
**为什么本轮不据此判产品**：`align` 取的是**每一像素行**的第一个有墨列，字号不同 / 长度不同的两行文本本来就会给出多簇，
它既没把像素行聚成"文本行"，也没报哪一簇属于哪一行 ⇒ 这把尺回答不了这个问句（R100 那条"尺要问得出问题"的规矩）。
下一步（有预算的一轮做）：按行带重切 —— 先把有墨的像素行按 y 聚成文本行，再对每行取 min-x，与列表行的标签轴（R65 结案后的 56.0–57.0pt）对账；
若空态两行确实落在两根不同的轴上，那才是排版缺陷，且要顺手复核 R64 那条"居中"是否已被 R65 之后的改动作废。

**205 追记（R175）：尺落地了，而它第一个结论是撤掉 R174 的前提；205 收窄成"按元素切带"**

新子命令 `python3 scripts/frame_audit.py bands <帧> --pt-width 420`：按 y 聚文本行带，每带报 `最左墨 / 众数左沿 / 行内散布`。
空态帧实测（亮暗两档逐位一致）：带0 `y=29..52 行数=24 最左墨=45px=22.5pt`、
带1 `y=76..101 行数=26 最左墨=107px=53.5pt` ⇒ **两带是两个元素**（搜索框那一行 vs 空态那一句），
不是"空态的两行落在两根轴上"。R174 的 U-582 读错了主语，本轮撤掉；R64 的"空态那句居中"与读数相容（空态只有一句）。
同一次对账还量出尺自己的漂：带0 的 `min_x` 两档同为 45px，`众数左沿` 却亮档 52.0pt / 暗档 22.0pt（带内散布 83px）
⇒ 主读数改成 `min_x`，并加闸门：**带内散布 >40px 报『不可判』**（本轮三张真帧全部 `不可判`，列表帧 6 带的轴 22.5pt 37.5pt 35.5pt 37.5pt 36.5pt 37.5pt 都是图标+文字混带）。
剩下的那一格（205 不结案的原因）：要谈"同一个表面里的两根轴"，得先在带内按 x 断簇、按**元素**切带；
现在这把尺只能报"每一带最左的墨在哪"，它答不了"这一带里最左的那块墨是不是我要问的那个元素"。

**206. 帧间隔那道绝对锚点是**单遍最大值**判的 ⇒ runner 上会换班（R176 量到形状，处置是"要颗数撑着"）**

触发它的读数：run `39157963970`（=`0dbcbb5`，只改台账那一笔）的 STEP[16] `On-screen probe coverage floor` 红在
`XCTAssertLessThanOrEqual failed: ("320.6537916667003 > 120")`，也就是 `testFrameIntervalsUnderStateChanges` 的 `worst ≤ 120ms` 绝对锚点；
而相邻两跑 `e61796c` / `9e1d3d4` 拿着同一份判据是绿的（正文里 `FAILED test` 行数=0）。三份 diff 之间没有产品改动
⇒ 120ms 这条线正落在 runner 单帧离群分布之内，红不红取决于一卷里最不稳的那一个数（最大值）。
本轮**不删锚点**（那是"删弱尺"，账里禁止过），改成要求它被**样本数**撑着：
`FrameMeter.stats()` 多一格 `overAnchor`（与 `worst` 取同一个 `sorted` ⇒ 两把尺不许各数各的），
判据换成 `FrameIntervalBudget.isWorstFrameJank(worstMs:overAnchorCount:)`——
`worst ≤ 120` 不红；超锚点且只有 1 颗 ⇒ 不红，另打 `PROBE_WORST_FRAME` / `WORST_OUTLIER` 两行读数；
超锚点且 ≥2 颗 ⇒ 红（真卡顿是一批帧掉下去，颗数不止 1）；`worst` 超锚点却数到 0 颗 ⇒ 两把尺矛盾，红给尺。
真值表 6 格在 `FrameIntervalBudgetTests.testTheWorstFrameAnchorNeedsMoreThanOneOutlier`（期望全部手算，U-432 那一族）。
**没验到的部分**：本机这条采样通道是死的（R91 原样 `FRAME_CHANNEL baseline_n=0`），所以新判据的**真产物验收在 CI 那一跑**；
本轮也没跑变异刀 ⇒ 记 NOT-RUN，不写成"验证通过"。

**204 追记（R177）：选了②（撤词表项），并把它做成一条显式通道；结案**

判据：这一层没有承载物（`QuickPickController.swift:262` 的 stack 只有 `field / empty / scroll`；`footerLabel` / `hintLabel` 产品源码 0 命中，缺席复查可验），
而它的**功能**已被就地承担 —— 唯一真正需要提示的场合（搜不到东西）由空态那一句在原地给了 Esc；
在 300pt 高的键盘驱动浮层里常驻一行键位 chrome 会与内容争注意力（与 D-171 同一取向）。⇒ 记 D-194，表面从词表撤下。
**留给产品的部分**：将来若要做键位提示行，那是一条新需求 —— 先做承载物，再逐格判；不许复活这个表面继续判 `not-applicable`。
撤项的代价也被处理了：地板是单调量，撤项在计数上与清账退步同形 ⇒ 新增 `retired_surfaces` + 四条闸门判据，降幅只从登记过的表面来
（本轮 `head=111` 由 HEAD 的 118 减去登记的 7 格得到）。未清账 53 → 51：其中 2 格（该表面的「空」「选中」）随表面消失，
**不是新判出来的** —— 这正是 202 说的那两格，202 继续开着（缺席粒度仍是文件级）。

**206 追记（R178）：三把刀补上，"颗数撑着"这句话有了反证；还原复跑那一格仍不绿**

`mutate_r178.py` 三臂全 CAUGHT（M693→testTheWorstFrameAnchorNeedsMoreThanOneOutlier、M694→testTheWorstFrameAnchorNeedsMoreThanOneOutlier、M695→testTheProbeWiresTheAnchorToTheSampleCount）：容差被放大后真卡顿不再红被抓、"超锚点却 0 颗"的矛盾分支被静音被抓、
探针里锚点断言被反装被抓（新格 `testTheProbeWiresTheAnchorToTheSampleCount` 扫的是剥掉行注释后的三处形状各恰好一次）。
**没结的部分**：`RESTORE_CLEAN=no` —— 表跑完的还原复跑报 `ran=0 broke=True`（没出测试结果），
而三处 needle 当场复查都是原形、随后单跑 5 格全绿 ⇒ 刀账成立，那一格按 NOT-RUN 记，成因未命名（候选：还原后立刻复跑撞上构建中间态）。
本机仍量不到真产物（采样通道死，R91 原样）⇒ 206 的 CI 复验还欠着：看 `PROBE_WORST_FRAME` 的颗数读数。

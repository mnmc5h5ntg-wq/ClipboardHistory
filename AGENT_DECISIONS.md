---
name: decisions
---

# AGENT_DECISIONS · 决策与迁移记录

每条：**背景 → 决定 → 理由 → 兼容性/迁移 → 回滚方式**。数据、接口、依赖、架构类改动必须在此登记后才能提交。

## D-000 基线与分支（2026-10-08）

- 背景：审计时工作区有 25 个未跟踪路径（含整个 `Intelligence/`），HEAD 停在 v1.3，任何修改都难以界定"我改的"和"WIP"。
- 决定：切分支 `fix/audit-remediation`，先做一次 checkpoint 提交 `8007b19`（`git add -A` + 提交），之后每个修复项一个独立提交。
- 理由：让每个改动都可 `git revert`，且能在 `8007b19` 上复现"修复前"状态做对照测量。
- 兼容性：纯版本控制动作，不改代码。
- 回滚：`git checkout main`（回到 `db077f6`）即完全丢弃本轮改动；`git revert <sha>` 丢弃单项。
  **2026-10-09 更新：这条回滚路径已经不存在了** —— 分支已 fast-forward 合进 `main` 并删除（本地与远端，删前用 `git log main..fix/audit-remediation` 验过为 0），
  且 v1.4.6/v1.4.7 已从 `main` 发布。现在只能按单项 `git revert <sha>`，不要再去找那个分支；判据 `git branch -a` 里应当没有它。

## D-001 日志开关与落盘位置（R-01 / R-30）

- 背景：`LifecycleDebugLogger` 的 `_isEnabledOverride = true` 让调试日志在正式版无条件开启，写 `/tmp/时间剪史_lifecycle_debug.log`（含窗口标题），并且是 `swift test` 崩进程（135 个用例只跑 3 个）的直接根因。`HistoryStore.ocrLog` 另写 `/tmp/ocr_debug.log`（含 OCR 文本前 80 字），连开关都没有。
- 决定：① 删除 override，只保留 `CLIPBOARD_HISTORY_DEBUG=1` 门控（与 HEAD v1.3 的原始设计一致）；② 日志目录改 `~/Library/Logs/时间剪史/`（0700），写盘走串行队列，写前拒绝符号链接目标；③ OCR 调试并入同一开关与同一文件，不再有第二条通道。
- 理由：`/tmp` 是全局可写目录、路径可预测，`createFile` 会跟随符号链接截断目标；把内容（窗口标题、OCR 文本）抄送到公共目录属于隐私与可靠性双问题。同时"测试进程里 `NSApp` 为 nil"这条崩溃路径只有在日志默认关闭时才不会触发。
- 兼容性/迁移：不涉及数据格式。旧 `/tmp` 日志文件**不主动删除**（不是本 Agent 生成的也可能存在），只停止写入。`logAppState` 的调用点与文案不变 ⇒ 依赖它排查的工作流只需加环境变量。
- 回滚：`git revert` 该提交即恢复原开关；无数据迁移。

## D-008 推荐刷新改为事件驱动 + 显露偏好窗口语义修正（R-11 / R-21）

- 背景：三处常驻轮询（0.5s 剪贴板、1s 前台 App、2s 菜单推荐）。2s 那次每次都对全库跑两套正则分析，且合上菜单也在跑。
- 决定：① 前台 App 改用 `NSWorkspace.didActivateApplicationNotification`（顺带修掉"1 秒内的来回切换被合并成一次"的漏采）；② 删掉 2s 定时器，改为"菜单内容 `onAppear` + 每次新复制 + 前台切换"三类事件驱动；③ 保留 0.5s 剪贴板轮询（NSPasteboard 没有变更回调，这是这类工具的必需项）；④ 预测任务加代际号，只有最新一代可回写界面。
- 行为变化（重要）：**"显露偏好窗口"（30s 内手动复制 ⇒ 记一条 copiedManually 隐式反馈）的开启时机从"开始计算推荐时"改为"推荐真正显示出来时"**。
  - 为什么：事件驱动后 `refreshPredictions()` 每次复制都会跑，若沿用"开始计算就开窗"，第二次复制起每一条复制都会被记成反馈，而引擎把 `copiedManually` 当作复用加分 ⇒ 排序自我强化。这个错误是我在改造过程中被自己的测试抓到的（反馈数 2 变 3）。
  - 影响面：反馈记录变少（只统计"看过推荐之后又复制了别的东西"），排序更保守；不改数据格式。
  - 回滚：`git revert` 本提交。
- 关联删除：`showsPredictionSuggestions` / `.togglePredictionSuggestions` 随死代码删除（全仓无调用者）；README 里"侧边栏 Magic 可展开"的承诺因此必须改（R-12，待办）。

## D-009 反馈载荷瘦身带来的跨版本读取差异（R-06 补充）

- 决定：`ClipboardEntrySummary` 新增两个**带默认值**的字段（`sensitivitySample`、`sourceDirectoryPath`）。
- 兼容性：成员初始化器对新字段给默认值 ⇒ 既有调用点与旧 `history.json`（不含这两个字段）都能解码；反馈 blob 已收窄为元数据，因此旧版本读新记录会得到"无反馈"而不是崩溃。
- 回滚：`git revert`。旧字段缺失时按默认值处理，不产生不可读状态。

## D-010 图片分析跨线程边界（R-19）

- 背景：`Task.detached` 里处理 `[ClipboardEntry]`（`.image` 携带 `NSImage`），靠 `@unchecked Sendable` 才编得过；上一轮文档把同类问题标成"已完成"。
- 决定：新增 `ClipboardEntryRawSnapshot`（纯字符串快照，含图片的像素尺寸描述），分析入口改为 `recommend(snapshots:)`；`ClipboardEntryIntelligenceAdapter` 的 entry 版本保留并委托给 snapshot 版本。
- 效果：NSImage 不再跨 actor；分析仍是一次全库扫描（现在只在事件驱动时发生）；`LocalRecommendationService.recommend(entries:)` 旧签名保留 ⇒ 现有测试与调用点不动。
- 回滚：`git revert`。

## D-008 图片重复判定改为"尺寸 + 64×64 采样哈希"（R-08）

- 背景：`StoredImage` 指纹原本把整张位图绘制进 `宽×高×4` 的缓冲区再做 SHA256，且在主线程、构造即算。实测 1200×900 单张 7.4ms；启动载入 8 张 2000×1500 共 605.8ms；12 张 1600×1200 载入 413.9ms。
- 决定：指纹改为「像素尺寸 + 固定 64×64 高质量采样哈希」，并**改为按需惰性计算**（第一次比较时才算）；同时 `StoredImage` 保存剪贴板/磁盘带来的原始 PNG 字节，`pngData()` 直接复用，不再二次编码。
- 语义影响（必须知道）：判定"同一张图"的条件从"全部像素相同"放宽为"尺寸相同且 64×64 缩略相同"。
  - 收益：去重仍然捕获"同一截图经不同来源/不同容器往返"（这是它本来的目的，且比按字节哈希更强）。
  - 代价：两张尺寸相同、缩略后恰好相同的图会被判为重复（例：都是纯色/都是同一空白窗口截图）——这类内容对用户本来就是同一个东西；差异只在极小区域时 64×64 采样仍能区分（新增用例 `testSampledFingerprintKeepsDistinctImagesDistinct` 用 1200×900 红底 + 24×24 蓝块验证"不同内容不得合并"）。
  - 兼容性：`StoredImage` 相等语义变了但**不改变磁盘格式**；`history.json` 里存的是文件名不是指纹 ⇒ 无需迁移，降级也安全。
- 回滚：`git revert`；无数据迁移。
- 实测（同一台机器、同一夹具，`swift test` 里 print）：
  | 指标 | 修复前（审计基线） | 修复后 |
  |---|---|---|
  | 启动载入 12 张 1600×1200 | 413.9ms | **3.2ms** |
  | 保存含 12 张图的库 | 667.8ms | **5.2ms** |
  | 单条 2.4MB 文本预览文案 | 45.8ms | **0.02ms** |
  | `filteredEntries` 求值（500 条 + 搜索词） | 14.07ms/次，一帧 3–5 次 | **0.00ms/次**（每字符一次重算 13.99ms） |
  | 单张 4000×3000 指纹 | 线性（1200×900 已 7.4ms） | **0.00ms**（惰性） |

## D-004 反馈存储格式瘦身（R-06）

- 背景：`RecommendationFeedback` 内嵌完整 `ContextSnapshot`，其 `recentEntries` 是最多 500 条 ×160 字的剪贴板正文预览。用户机器实测 `~/Library/Preferences/com.clipboardhistory.app.plist` 为 **66,724,574 字节**，其中该键 blob **66,716,424 字节**，每次启动在主线程解码。
- 决定：序列化只写元数据（前台 App bundleID/名称、事件数量、capturedAt）；`init(from:)` 同时接受旧的全量快照格式并在读出后立即丢弃正文，首次加载即把旧 blob 收窄回写；`entryID/kind/createdAt` 保持不变。删除条目或清空历史时级联删除其反馈。
- 理由：排序只读 `entryID/kind/createdAt`，`feedback[i].context` 在全仓**没有任何读取点**（grep 确认），因此正文副本是纯粹的隐私与性能负债。
- 兼容性/迁移：`version` 字段与文件路径不变；旧数据可读；旧版本读新 blob 会解码失败并退化为"无反馈记忆"（不崩溃、不影响历史本体）。**已知不可逆点**：被收窄掉的正文预览副本不会恢复，但这些文本在 `history.json` 里本就存在（反馈里的只是 160 字截断副本），且这正是"删除记录"应有的语义。
- 回滚：`git revert` 后旧实现会按旧格式继续写；已收窄的数据仍能被旧实现读（它读的是同一键，解码失败即空）。

## D-005 `ClipboardIntake.Entry` 增加来源字段（R-05）

- 背景：重复复制被提升为队首时，重建条目不带 `sourceAppBundleID/sourceAppName`（探针 P-01），导致 appAffinity 与"回到 X"标签失效。
- 决定：`Entry` 新增两个**带默认值的可选字段**，来源在读取 pasteboard 时确定；提升时"新一次复制的来源优先，缺失则回退旧条目"。
- 理由：来源本就该在复制那一刻定；放在构造条目时才查会让"注入测试来源"这件事不可能（本轮实测：测试因此读到用户真实剪贴板内容）。
- 兼容性：字段有默认值 ⇒ 所有现有调用点（含 `ClipboardIntakeTests`、`HistoryStoreTests` 夹具）无需改动即编译；持久化格式不变（这两个字段本来就已存进 `ClipboardEntry`）。
- 回滚：`git revert`；已写入历史的来源字段保持有效，不产生脏数据。
- 附带修正：`ClipboardIntake` 各读取方法的 `from:` 参数默认 `.general`，导致注入的 pasteboard 被静默忽略。现改为 `NSPasteboard? = nil` ⇒ 缺省用注入的那个，显式传入仍然优先（`testExplicitOverrideStillWins` 锁住）。

## D-006 破坏性操作确认改为可注入（R-03）

- 背景：`.clearHistory` 命令直接删；带 `NSAlert` 的 `confirmAndClearHistory()` 无调用者（审计 X-01）。
- 决定：新增 `DestructiveConfirming` 协议 + `SystemDestructiveConfirming`（NSAlert），`ApplicationShell.init` 增加**带默认值**的 `confirmation` 参数，`.clearHistory` 与 `confirmAndClearHistory()` 共用一条确认路径；删除 `AppDelegate` 里无人调用的转发方法。
- 兼容性：默认参数 ⇒ `AppDelegate` 构造点不变；设置页仍走它自己的 SwiftUI alert（`store.perform(.clear)` 语义不变，`testDirectClearActionStillAvailableForAlreadyConfirmedPaths` 锁住）。
- 回滚：`git revert`；无数据格式变化。

## D-007 推荐排序改为确定性次序（R-48，本轮实测定位）

- 背景：`HistoryStoreTests` 的排序断言 5 次挂 3 次。定位到两处跨进程不确定性：① 分数用 `features.values.reduce(0,+)` 在 Dictionary 上求和，字典迭代顺序按进程播种，浮点加法不满足结合律 ⇒ 同分候选差 1 ULP（实测 `0.23999999999999999` vs `0.24000000000000002`）；② 同分候选依赖 `sorted(by:)` 的稳定性，而 Swift 文档不保证稳定。
- 决定：抽出 `summedScore(from:)` 按 `RecommendationFeature.allCases` 固定顺序求和；比较器补显式次级键（分数 → 理由 → `copiedAt` 降序 → `uuidString`）。
- 理由：这不是测试洁癖——**同一份历史在两次启动之间给出不同"猜你要粘贴"** 是用户可见的行为不一致；固定次序也才能被回归测试守住。
- 兼容性：候选集合与分数量级不变，仅次序在"原本并列"时变得确定 ⇒ 不影响数据、不改变 Top-N 的成员判定阈值。
- 回滚：`git revert` 即回到旧次序行为。
- 守卫强度说明：`testScoreSummationDoesNotDependOnDictionaryOrder` 是**概率性**守卫（同进程字典顺序固定，某些播种下两种实现结果相同）；主守卫是确定性的同分排序用例，变异检查证明去掉次级键必然变红。

## D-003 存档损坏时的恢复策略与滚动备份（R-02）

- 背景：旧 `load()` 用 `try?` 把"文件存在但解析失败"折叠成空历史；随后第一次保存会覆盖 `history.json`，并让 `removeUnusedImages` 把所有旧图片文件删掉（审计探针 P-06 实测：images 2 → 0）。
- 决定：① 每次成功保存都同步写 `history.json.bak`（同一份快照，0600）；② `load()` 在主存档解析失败时先按顺序尝试：备份 → 从损坏文本里尽力提取图片文件名并加入"本次运行的保护集" → 才以空历史启动；③ 损坏原件复制为 `history.corrupt-<时间戳>.json`，**永不删除或移动原件**；④ 正常路径的清理语义**不变**（删除条目的图片下一次保存即清理，`testSaveRemovesUnusedImageFiles` 继续锁住）。
- 理由：既堵住数据丢失，又不引入"只读模式"这种会让新记录静默不保存的新状态机；保护集只存在于本次运行，下次启动主存档正常时孤儿图片仍会被回收，不会无限增长。
- 兼容性/迁移：数据格式与 `version` 字段不变（仍是 v1、同文件名、同字段）。新增的 `.bak` 与 `history.corrupt-*.json` 是**附加文件**：旧版本读不到它们也不受影响，因此**降级可运行**。`HistoryPersisting` 新增 `recoveryNotice` 需求但有扩展默认实现 `nil`，`RecordingHistoryPersistence` 等替身无需改动。
- 回滚：`git revert` 本提交。回滚后 `.bak` 文件成为无害残留（可手工删）；不会造成读不回的情况。
- 验证：4 条新回归测试（含"无备份时保住被引用图片 + 孤儿图片仍清理"）；变异检查确认去掉修复后它们以正确的失败原因变红（"P-06 修复验证：图片文件不得被连带删除"）。

## D-002 用户真实数据不被本轮验证流程触碰

- 背景：`FileHistoryPersistence.defaultRootDirectory()` 指向 `~/Library/Application Support/时间剪史/`，是用户真实剪贴板历史；R-02 修复前，任何"以默认目录启动真实 App"的动作都可能触发数据丢失路径。
- 决定：所有验证只用临时目录（测试夹具）或进程环境变量重定向；不删除、不改写、不备份后清空用户目录内容。
- 理由：审计已证明该应用存在"存档损坏 + 一次复制 ⇒ 全量删除"的缺陷（探针 P-06）。在修复并加守卫之前，触碰真实数据的风险不可接受。
- 兼容性：为验证而新增的数据目录环境变量重定向（若实现）默认不生效，行为与今天完全一致。
- 回滚：无。

## D-011 视觉验收需要的最小接缝，以及"哪里显示原文"的规则

- 背景：离屏捕获要拍设置页的 5 个分类，而分类是 `SettingsView` 的私有 `@State`。先试的是**无障碍动作真点一次**（`accessibilityPerformPress`），实测离屏窗口的无障碍树根本不建（BFS 只能走到根节点：`已遍历 1 个节点，标签样本=[]`），这条路走不通。
- 决定：① `SettingsCategory` 从 `private` 升为 `internal`，`SettingsView.init` 末尾追加 `initialCategory: SettingsCategory? = .shortcuts`，默认值就是改动前的字面量；② 捕获套件在写 PNG 前铺一层该外观下的 `windowBackgroundColor`，并逐帧量化"未绘制像素比例"，>95% 判失败；③ 内容展示规则定为：**主窗口显示原文，菜单栏常驻入口脱敏**——主窗口是用户显式打开、自己负责的动作，菜单栏会在肩窥/截屏里长期可见，所以走 `EntryPresentation.menuLabel`。这条规则用来解释"为什么侧栏能看到完整 token 而菜单不能"，不是遗漏。
- 理由：接缝只加一个带默认值的参数，比给测试开后门式地暴露 `@Binding`、或把私有视图拆成可注入组件，改动面小得多；而且它同时是有用处的公开能力（将来"从菜单跳到某分类"可以直接复用）。
- 兼容性：所有既有调用点不传该参数 ⇒ 行为与今天逐字节一致；数据格式、持久化、网络均无关。
- 回滚：删掉参数与 `_selectedCategory = State(initialValue:)` 一行、把枚举改回 `private` 即可；`UICaptureHarness.swift` 在测试 target 内，整体删除不影响产品构建。
- 验证：5 个分类帧的"未绘制像素比例"互不相同（28.6% / 49.8% / 65.7% / 71.6% / 74.1%），证明确实拍到了 5 个不同界面；`swift test` 195 例全绿，未删改任何测试。

## D-012 存档版本闸门：读到更高版本就只读打开（R-20）

- 背景：`history.json` 里 `version` 字段以前**只写不读**（恒为 1）。一旦用户装了更新的版本（或将来我们改格式）再退回本版本，新字段会被解码器忽略，而"载入 → 下一次复制 → 保存"这条链会把存档原样重写回 v1 —— 新版本写进去的内容被静默抹掉。README 的"已知问题"里恰好写着用户会反复装卸新旧版。
- 决定：① `FileHistoryPersistence.currentSchemaVersion = 1`；② 载入时解码出的 `version` 大于当前 ⇒ 置 `isArchiveFromNewerVersion`，给出 `recoveryNotice`（走已有的顶部提示条），并且 `save()` 直接返回不写盘；③ 小于等于当前 ⇒ 走 `migrate(_:)` 这个唯一入口（今天只有 `case 1`，作用是让"忘了写迁移"成为一件会被看见的事）；④ 内容仍照常读出，不是"拒绝打开"。
- 同时补的第二件事：成批按时间过期现在会报告（≥10 条时给一条可关掉的提示，并写日志）。刻意**没有**做"检测到时钟异常就不裁剪"的启发式 —— 一次清掉几十条，既可能是用户两个月没打开 App（策略本就该执行），也可能是系统时间被往前调，两者从时间戳上无法区分；让程序去赌会留下"永远不过期"的洞，所以只把数字和原因摆出来让人判断。
- 兼容性：数据格式不变（仍 v1、同字段、同文件名）。只读闸门只在"版本比本程序高"这一种以前根本没定义的情况下生效；正常存档的读写路径逐字节不变（`testCurrentVersionArchiveStillWrites` 锁住）。新增的 `retentionNotice` 是内存态，不落盘。
- 回滚：`git revert` 本提交。回滚后回到"高版本存档会被降级写回"的旧行为，无残留状态、无需数据修复；已写出的存档本来就是本版本读的格式。
- 验证：`ArchiveVersionAndRetentionTests` 4 条（只读 + 不覆盖 + 正常版本照写 + 单条过期不打扰）；变异检查：摘掉 `save()` 的闸门 ⇒ 以"只读模式绝不能把更高版本的存档覆盖回 v1"变红。全量 `swift test` 209 例、退出码 0、0 编译告警。

## D-013 隐私承诺要出现在产品里，而不只是文档里（R-14）

- 背景：`Models/HistoryPrivacyCopy.swift` 里那 5 条隐私说明（保存位置、保存内容、保留策略、清空语义、敏感内容提醒）早就写好并有单测守着不重复不为空，但**产品里没有任何地方显示它们** —— 设置页的「隐私」只有上下文权限与推荐过滤。同时 README 的"历史与隐私"章节在上一轮被查出有与代码相反的承诺（R-12）。
- 决定：把 `HistoryPrivacyCopy.settingsBullets` 作为「数据与保留」分组接进设置页隐私分类；不改文案内容（它们与代码事实一致：默认 `HistoryRetentionPolicy.default = 500 条 / 30 天`、`~/Library/Application Support/时间剪史/`、清空只删未收藏）。
- 理由：隐私声明只有用户在界面里能看到，才算产品行为；否则它只是仓库里的字符串。这一步同时把一处死代码变成有调用者的代码，比删掉它更有价值。
- 兼容性：纯展示层新增，无数据、无接口变化。
- 回滚：删除 `privacySection` 里那个 `GroupBox` 块即可（一个 hunk）。
- 验证：离屏帧 `settings-privacy-720x540-{light,dark}.png` 改动前后对比 —— 该帧"未绘制像素比例"从 49.8% 降到 31.4%（证明确实多画了一整块内容），暗色下 5 条文案逐行可读；`swift test` 209 例全绿、0 编译告警。

## D-014 第二实例改为静默退出（R-52）

- 背景：审计矩阵 M1×边界 格时发现，应用对"已经有一份在跑"没有任何检查。两个实例会各自轮询剪贴板、各自把**整库**写回 `history.json`，后写的一次会把先写的那次整片盖掉 —— 与 P-06 同类的数据丢失，触发方式只是"再开一次"。而 `make run` 用的正是 `open -n`（强制新实例），这条路径对本项目作者是日常路径。
- 决定：新增 `InstanceGuard`（纯函数判定 + 读 `NSWorkspace.runningApplications` 的薄适配器）。启动时若发现同 bundle 的另一个未退出实例，记一条日志并 `NSApp.terminate`，**不弹窗**。三条判定例外都留了测试：自己不算冲突、`isTerminated` 的残留记录不算冲突、拿不到 bundle id（裸可执行文件 / `swift run`）时一律放行。
- 为什么不弹窗：正常双击第二个图标时，macOS 本来就是把已有实例带到前台，用户根本看不到第二个进程；只有 `-n` 才会真的起第二份。弹一个"已经在运行"的框，对普通用户是噪音，对开发者是每次 `make run` 都要点一下。
- 兼容性：无数据格式变化；对单实例用户完全无感。
- 回滚：删掉 `applicationDidFinishLaunching` 开头那段 guard（一个 hunk）即可，`InstanceGuard.swift` 可整体删除。
- 验证：`InstanceGuardTests` 7 条，其中一条拿本机真实存在的 Finder 进程喂给适配器，证明"读系统进程列表"这条路不是空跑。**未做**端到端双实例实跑：那需要真的启动 App，而它会读写用户真实数据目录（D-002 明令禁止），除非先给数据目录加一个环境变量接缝（已记在报告"未验证清单"里）。

## D-015 仓库移出 iCloud 同步范围（2026-10-09）

- 背景：`~/Documents` 在 iCloud「桌面与文稿」的同步范围内。判据不是"它是不是符号链接"（它不是，我这样误判过一次），而是 `~/Library/Mobile Documents/com~apple~CloudDocs/Documents -> ~/Documents` 这条反向链接加上 `bird`/`cloudd` 在跑。同步在这个仓库里留下了 **29 个 `名字 2.扩展名` 的重复副本**，其中含 `Sources/**.swift`；SwiftPM 按目录 glob 编译 ⇒ 同一批类型声明出现两遍 ⇒ `swift build` 报类型歧义，而报错会伪装成 SDK 不兼容。**重复副本由谁产生没有查清**：`Codex_Project0_backups` 是 6 月 8 日的手工快照、`Codex_Project0.zip` 是 6 月 5 日的，实测都不是元凶；移出同步范围只消除了最可能的一条路径，不保证不复发。
- 决定：整仓复制到 `/Users/wangziyi/Codex_Project0`，旧路径 `~/Documents/Codex_Project0` 换成指向新位置的符号链接；那 29 个副本先逐字节与原件比对、确认全同，再连同临时目录一起删掉。
- 为什么不是 `mv`：跨出同步边界的 `mv` 以 `Operation timed out` 失败（File Provider 要先物化）。改成 `rsync -a` 复制 → 校验 → 删源；旧 rsync(2.6.9) 不支持 `--info=stats1`，会打 usage 退出。
- 兼容性：仓库内容零改动（与旧路径唯一的差异是 `.git/index`）。旧路径以符号链接保持可用，指向 `~/Documents/Codex_Project0` 的既有习惯不破。项目级记忆的键随绝对路径改变，已把 `~/.qoder-cn/projects/-Users-wangziyi-Documents-Codex_Project0/memory/` 复制到 `-Users-wangziyi-Codex_Project0`（只带记忆目录，8K）。已发布产物与 tag 不受影响。
- 回滚：两条互相独立 —— ① 只撤销链接：`rm ~/Documents/Codex_Project0 && rsync -a /Users/wangziyi/Codex_Project0/ ~/Documents/Codex_Project0/`；② 整体退回旧路径同上。任何一条都不涉及数据迁移，`history.json` 在 `~/Library/Application Support/` 下、本来与仓库位置无关。
- 验证：两侧文件数相同（`find . -path ./.build -prune -o -type f -print | wc -l`，当时 1158/1158）、`git rev-parse HEAD` 相同、`git status` 干净、`git fsck` 无报错、`diff -rq` 只差 `.git/index`。新路径上重新跑过全套判据：`swift build` 0 告警、`swift test` 229 例全绿（1 条按设计 skip）、`python3 -m unittest discover -s scripts/tests` 18 例 OK、视觉套件 58 帧且未绘制比例闸门全过（退出码 0）、`make bundle` 产出 x86_64+arm64 通用二进制、包内版本 1.4.7、`codesign --verify --deep --strict` 退出码 0、Info.plist 16 键。**复发时的特征**：`Sources/` 下出现 `* 2.swift`，判据 `find ClipboardHistory/Sources -name '* 2.*' | wc -l` 应为 0（本轮结束时实测 0）。

## D-016 来源 App 落盘：`StoredEntry` 新增两个可选字段（第二轮 B-2 / R2-07）

- 背景：`ClipboardEntry` 一直带着 `sourceAppBundleID` / `sourceAppName`（采集时从 `NSWorkspace.frontmostApplication` 取），但 `StoredEntry` **没有**这两个字段 ⇒ 每次重启后归因全部丢失，推荐权重里的 `appAffinity` 对"载入的历史"恒为 0。也就是说那一项权重从上线起就没真正生效过，而界面上它一直显示为可调项。
- 决定：`StoredEntry` 新增 `sourceAppBundleID: String?` 与 `sourceAppName: String?`，四种内容类型（文本 / 图片 / 文件 / 多文件）一律写入，`entry(from:)` 读回。**schema 版本保持 1，不加迁移步骤。**
- 理由：两个字段都是 Optional —— 旧存档缺键时解出 `nil`（有一份手写旧 JSON 的用例钉住）；旧版本程序遇到多出来的键会忽略（`Codable` 默认行为），所以**双向兼容**。刻意不升版本号：升了反而会让"新版本写出的存档"在旧版本里被判成只读（D-012 的闸门），那是更差的取舍。
- 隐私影响（必须一起改）：这是**新增的落盘内容**，所以设置页的隐私说明同步改了 —— `HistoryPrivacyCopy.capturedContent` 现在明写"以及复制时的来源 App 名称（仅用于推荐排序）"，并有一条用例钉住"文案必须提到来源 App，且这条文案真的出现在设置页的 bullets 里"。落盘内容与界面承诺不一致，比不落盘更坏。
- 兼容性/迁移：无需迁移。旧存档读出的条目来源为 `nil`，`appAffinity` 对这些条目仍为 0（与改动前一致），新复制的条目开始累积归因。
- 回滚：`git revert` 本提交。回滚后新写出的存档少这两个键，已写出的存档里多出的键被忽略 ⇒ 无残留状态、无需数据修复。
- 验证：`SourceAppAttributionPersistenceTests` 4 条（文本往返、图片+文件往返、旧存档仍可读且读成 `nil`、隐私文案披露）。变异对照已实跑：把四处写入改成 `sourceAppBundleID: nil, sourceAppName: nil` ⇒ 前两条用例红（消息正是"bundle id 没有落盘"），随后按 sha 逐字节还原。全量 `swift test` 265 例 / 5 skip / 0 失败。

## D-017 采集图片设 4096px 最长边上限（第二轮 B-4 / R2-08）

- 背景：剪贴板图片以前**原分辨率整张入库**，一张 4K 截图就是数十 MB 的 PNG；库上限 500 条 ⇒ 磁盘占用能长到十几 GB，而且每次保存都要过一遍这些字节（与 R2-04 是同一条 IO 链）。
- 决定：新增 `ImageIntakePolicy`（最长边 **4096**）与 `StoredImage.downsamplingIfNeeded(_:pngData:limit:)`，接在 `ClipboardIntake` 的三条图片路径上（PNG、TIFF、文件条目的缩略图）。**只降不升**；读不到尺寸或降采样失败时一律退回原图 —— 宁可这一次多占磁盘，也不能因为缩放失败把用户复制的图片丢掉。
- 阈值依据（不是随手取的）：4K 截图 3840×2160 的最长边 3840 ≤ 4096 ⇒ **逐字节不动**；界面最宽的详情列约 1100pt（`content-wide-1100x800` 夹具，2× 也只需 2200px）；OCR 走 1200px 降采样；去重指纹只用 64px。也就是说 4096 高于本产品任何一处显示/分析需求，只有 5K/6K 截图与相机原图会被缩。
- 兼容性：只影响**新采集**的图片。已入库的图片不动、不迁移、不重写（配合 R2-04 的"同名同长度就跳过"，旧文件连一次写都不会有）。存档格式不变：仍是 PNG 文件 + v1 JSON。
- 隐私：不新增落盘内容，反而减少磁盘上的原图数据量；隐私文案无需改动。
- 回滚：`git revert` 本提交（一个 helper 文件 + 三处调用点）。**唯一的不可逆面**：已经降采样入库的图片无法还原，信息已经丢了 —— 这正是把阈值取在"常见截图完全不受影响"那一侧的原因。
- 验证：`ImageIntakePolicyTests` 6 条，其中一条走**真实采集管线**（pasteboard → `ClipboardIntake.readChangedEntry`），断言入库像素 ≤ 4096 且落盘字节数严格小于原图；另有"未超限的图逐字节保留"（不重新编码）与"非图片数据返回 nil 而不是编一组宽高"。顺带记下一条容易踩的事实：`makeStoredImage` 在本机以 **2×** 位图渲染，所以 41×17 点的图会得到 82×34 像素 —— 所有捕获帧也是"名字里是点、文件里是 2× 像素"；**CI runner 是 1×**，所以断言不能写死任何一种倍率（`d160b52` 就是修这个）。

## D-018 只含 `public.url` 的剪贴板记成文本条目（第二轮 N-4 副产物 / R2-16）

- 背景：N-4 把那条假绿断言换成"钉住现状"之后，暴露一个真行为：剪贴板里只有非文件 `NSURL` 时 `readEntry` 返回 nil ⇒ 这次复制凭空消失。浏览器复制链接通常同时带字符串，所以日常无感；但只发布 URL 对象的应用（部分终端 / IDE 的"复制链接"）会让记录直接丢掉 —— 对剪贴板管理器这是功能缺口。
- 决定：在字符串分支之后、`return nil` 之前加兜底：读到非文件 `NSURL` 就记成 `.text(absoluteString)`（仍过 `bounded` 体积上限）。
- 理由：与"链接带字符串时记成文本"的既有行为一致；文件路径不会走到这里（`readFileURLs` 限定 `.urlReadingFileURLsOnly` 且先返回），所以不会复活 P-15 那类"Web URL 被当文件"的缺陷。
- 兼容性：只影响以前被丢弃的输入；已存数据与存档格式都不变。
- 回滚：`git revert` 本提交，回滚后这类剪贴板恢复为不记录。
- 验证：翻转 `ClipboardIntakeURLKindTests.testWebURLOnlyPasteboardIsNotMistakenForFileEntry` —— 现在断言"必须记到、且是文本、且不是 `.file`"。变异对照已实跑：把兜底条件反转（`first.isFileURL`）⇒ 该用例红（"只含 Web URL 的剪贴板不应被丢弃"）；第一次跑变异时**过滤器写错类名导致 0 条用例执行**，那轮"绿"作废重跑，这也是"0 条执行 = 探针没跑"的又一次现场。

## D-019 `AppDelegate` 的 store 注入接缝（第二轮 R2-17）

- 背景：菜单栏面板的视觉从第一轮起就标 NOT-RUN。原因链：构造 `AppDelegate` 会求值 `static let sharedHistoryStore = HistoryStore()`，也就是读用户真实存档；而 `HOME=/tmp/…` 重定向实测**不改变** `applicationSupportDirectory`（审计 04 §4.1(6)），所以隔离只能靠注入。
- 决定：`AppDelegate.init(historyStore: HistoryStore? = nil)`。默认 `nil` 时仍取 `sharedHistoryStore`，产品路径一字不变；`@NSApplicationDelegateAdaptor` 走的就是这个默认路径。
- **结果要诚实记下来**：接缝加上了，但菜单栏**离屏仍然拍不了** —— 试拍一帧发现菜单表面 97.7% 像素未被绘制（离屏 `cacheDisplay` 不画菜单的材质表面），被捕获 harness 自己的"未绘制 >95% 判失败"闸门拦下。那道闸门是对的：假帧不能当证据。所以菜单栏视觉继续标 NOT-RUN，但理由从"怕碰真实存档"更新为"离屏画不出菜单表面"；接缝保留给在屏探针路线（`UIInteractionProbeTests`）。
- 兼容性/回滚：默认参数保证所有既有调用点不变；`git revert` 即回到隐式 init。
- 验证：`AppDelegateStoreInjectionTests` 2 条 —— 注入的 store 确实被 delegate 使用（身份比较）；默认构造仍然拿到共享 store（接缝没有改变产品路径）。试拍的 97.7% 记在 `UICaptureHarness` 的注释里，防止下一个人再花一次同样的时间。

## D-020 AI 草案拆出产品 target，共享词汇表另立 target（第二轮 R2-15）

- 背景：审计第二轮 10-07 说"AI 脚手架仍在产品路径且零产品调用"。**第一次整体搬走就编译失败**：`AIPrivacyScope` / `AIPrivacySensitivity` 被 4 个产品文件用着（`RecommendationModels.swift:34`、`ContextSnapshot.swift`、`EntryIntelligence.swift`、`ClipboardEntryIntelligenceAdapter.swift:138`）—— 那条审计结论只对了一半。
- 决定：拆成三个 target。`ClipboardHistoryIntelligenceCore` 只放这两个枚举（产品 target 依赖它）；`ClipboardHistoryDesignDrafts` 放真正无人调用的 `AIProviderModels.swift` 与 `AIPrivacyPolicy` / `AIPrivacyDecision`；`ClipboardHistoryApp` 不变。草案的既有用例**整体搬**到新的 `ClipboardHistoryDesignDraftsTests`（用 `@testable` 取内部 API），一条没删，也不必把草案 API 改成 public。
- 理由：草案不该进交付二进制；但"什么算没人用"必须由编译器裁定，不能靠 grep 的印象（这次 grep 就漏了 `AIPrivacySensitivity`）。
- 兼容性：无数据、无对外接口变化。顺带修掉一个守卫的洞：`LocalOnlyGuardTests` 以前扫整个 `Sources/` 再按文件名跳过两个草案文件，现在扫描根就是产品 target 目录，例外名单删除。
- 回滚：`git revert` 本提交（Package.swift + 5 处 import + 3 个文件位置 + 1 个测试目录）。
- 验证：用 `nm` 数产品可执行文件里的符号 —— `AIProviderKind` / `AIPrivacyPolicy` / `AIPrivacyDecision` 均为 **0**，`AIPrivacyScope` 61、`AIPrivacySensitivity` 110（仍在，因为真的在用）。`swift build` 0 告警、`swift test` 286 例 / 5 skip / 0 失败。
- ~~同一提交里的另一处方法修正：图片比较的性能闸在负载 28.8（10 核）时报出 997ms 假红，而单跑三次是 155–171ms。现在它先打印 `load1` 与活跃核数，比值 > 2 时 skip 而不是误判回归；**<250ms 的判据本身没动**（仍低于它要否证的旧值 434ms）。~~ **该做法已被 D-023 推翻并删除**：load1 比值在 CI runner 上是 3.9，会把全部性能守卫变成 skip。

## D-021 菜单区分"还在算推荐"与"确实没有推荐"（第二轮 R2-09 的后续）

- 背景：本轮给菜单栏补了空态文案（"暂无推荐"）之后，写 `MenuBarPopulationTests` 时暴露一个**我自己引入的误导**：
  `menuWillOpen` 先发起异步刷新、再**同步**填菜单，所以每次打开的那一刻候选必然是空 ⇒ 界面会先说一句"暂无推荐"，
  过一会儿才出候选。把"还不知道"说成"没有"，比原来的整段消失更糟。
- 决定：`HistoryStore` 增加 `@Published private(set) var isRefreshingPredictions`：`refreshPredictions()` 开头置 true，
  结果回写时**仅当代次仍是最新**才置 false（被更新的代次取代时保持 true）。两条菜单路径
  （macOS 12 的 AppKit `populate` 与 macOS 13 的 `MenuBarRecommendationsView`）据此在"空"时分两种说法：
  "正在整理推荐…" / "暂无推荐"。
- 理由：菜单必须同步给出内容，这是 AppKit 的约束；能改的是**别让它说谎**。用代次守卫而不是"永远 true"，
  是为了让真的空库仍然显示"暂无推荐"。
- 兼容性：新增的是只读发布属性，无数据格式变化；两条菜单路径同步改文案，不留分叉。
- 回滚：`git revert` 本提交（属性 + 两处赋值 + 两处文案分支）。回滚后回到"打开瞬间误报暂无推荐"。
- 验证：`MenuBarPopulationTests` 6 条（`populate` 从 private 放宽到 internal 才可测，行为未变）：真的空库说"暂无推荐"、
  刷新在飞时说"正在整理推荐…"且不得同时出现"暂无推荐"、有候选时表头 + ≤3 条 + 标题以脱敏标签开头、
  疑似令牌原文不得出现在任何标题、命令区完整。变异对照已实跑：把 `isRefreshingPredictions = true` 改成 `false`
  ⇒ 三条断言红（消息里带实际标题列表）；文件按 sha 逐字节还原。`swift build` 0 告警、`swift test` 293 例 / 5 skip / 0 失败、
  58 帧 **0/58 不同** —— 这是零噪声捕获管道第一次用来证明"这个改动不画任何东西"。

## D-022 接受把文件拖进列表入库（第二轮 1.5 / R2-05 的另一半）

- 背景：审计第二轮 1.5 判"拖拽不达标"，缺口有两半：拖不出（已由 `d463ef9` 处理）和**拖不进** —— 全仓 `onDrop`/`dropDestination` 零命中，把文件拖到窗口上什么也不会发生。
- 决定：新增 `DroppedFileImport`（纯规划：1 个文件 → `.file`，多个 → `.files`，非文件 URL 一律不收）与 `HistoryStore.addDroppedFiles(urls:timestamp:)`（返回入库条数），侧栏列表挂 `.onDrop(of: [public.file-url])`，悬停时画一圈虚线。
- 为什么不整窗接收：详情的文本视图本来就接受文字拖放，窗口级 `.onDrop` 会抢走它 —— 落点收窄到列表区域，避免为了补一个 affordance 弄坏另一个。
- 语义选择：一次拖入多个文件产生**一条**多文件记录（与"在 Finder 里复制多个文件"的既有记录形状一致），而不是 N 条。
- 兼容性：无数据格式变化（`.file` / `.files` 早就存在）；不拖东西时行为完全不变。
- 回滚：`git revert` 本提交（一个工具文件 + 一个 store 方法 + 侧栏的 `.onDrop`/overlay）。
- 验证：`DroppedFileImportTests` 8 条，含"拖入的两条文件存盘再载入仍然是 `.files`"和"只拖进来 Web 链接 ⇒ 返回 0 且不留空记录"。变异对照已实跑：把 `filter(\.isFileURL)` 去掉 ⇒ 8 条里 5 条红（含"被丢掉的项要能被数出来"与"store 不能收下纯链接"），文件按 sha 逐字节还原。视觉侧 58 帧 **0/58 不同**。
- **未验证**：真实鼠标拖放（需要拖拽事件与接收方 App，离屏测不了；审计 04 §4.2 N-4 同样标 NOT-RUN）。provider 解码那段胶水刻意写得很薄 —— 可判定的逻辑全在上面两处有测试的地方。

## D-023 性能守卫的"机器太吵就 skip"改成"样本自己跨度太大才 skip"（第二轮收尾，CI 第四次红）

- 现象：`53bbe85` 在 CI 上红在 `PERF 改一次搜索词`：**均值 69.0ms vs 上界 60ms**，本地同一条是 14.1ms。
  上一次同类红是本机的图片比较（997ms vs 单跑 155–171ms）。我最初的修法是加一道 load1/活跃核 > 2 的闸门。
- **那道闸门本身是缺陷，而且是更坏的那种**：拉下最新 CI 原始日志实测 `PERF 环境：load1=11.8 活跃核=3` —— 比值 3.9 > 2。
  也就是说按我那写法，5 条性能守卫在**唯一的自动化环境**里会永久变成 skip，而在本地安静时照常跑。
  "只在没人看着的地方失效的守卫"比没有守卫更糟：它让绿变成不可解释的绿。已把这条记进假绿清单。
- 决定：删掉 load1 判定，改为两个与环境统计无关的规则 ——
  ① 判据一律打在 **N 次同操作采样的最快值**上（真实数量级回归会让每一次都超线，均值/最慢会被邻居用例的调度噪声吃掉；
  ② 只有当 `最慢 − 最快 > 该条判据自己的阈值` 时才 `XCTSkip`：那一刻噪声幅度比要分辨的差值还大，红和绿都不说明改动。**所有阈值一个都没动**（1 / 5 / 60 / 200 / 250ms），
  数字一律先打印（最快/均值/最慢/n/load1/活跃核），skip 不掩盖现场。load1 从此只做上下文打印。
- 为什么 ② 比负载闸门强：本机注入 12 个 `yes` 进程把 load1 顶到 **44.4**（旧闸门会 skip），
  而 `preview(2.4MB)` 的样本跨度只有 **0.07ms** —— 这条判据在"机器很忙"时依然完全分辨得清，旧闸门是**误 skip**；
  反过来 997ms 那次跨度约 840ms ≫ 250ms 阈值，新规则照样 skip。噪声大不等于这条判据不可用，样本跨度才是证据。
- 双向变异对照（都实跑、跑完 `cmp` 逐字节还原）：
  红侧 —— 把 `filteredEntries` 的缓存短路改成 `&& false` ⇒ `最快13.86ms（阈值 1.0ms）` **判红而不是 skip**（样本跨度 0.50ms < 1ms）；
  skip 侧 —— 把 `preview` 那条的阈值参数临时改成 0.01 ⇒ 该条 `skipped`，断言未执行。skip 分支不是永不可达的死代码。
- 顺带把同一条测试里两处"只测一次"的计时改成 3 次采样（同字节比较那对原来第 2、3 次会量到已焐热的缓存，所以每轮都换新对象）。
- 回滚：`git revert` 本提交，只动 `Tests/ClipboardHistoryAppTests/PerfBudgetTests.swift`，产品代码零改动。
- 已观察（`c952905` 的 CI 原始日志，实跑核对）：runner 上 **load1=27.7 / 活跃核=3**（比值 9.2 —— 比我先删掉的那道闸门
  的 2.0 高四倍多），而 8 条 `PERF[...]` 采样**全部下结论、零 skip**：搜索词代价 最快 25.04 / 均值 37.07 / 最慢 56.99ms
  （跨度 31.95 < 阈值 60）、图片比较 47.83/57.76/76.27ms（跨度 28.4 < 250）、filteredEntries 0.00/0.00/0.01ms。
  也就是说旧闸门会把这 8 条全部变成 skip，而它们其实完全分辨得清 —— 这条判据在 CI 上是活的。
  若后续出现"同操作样本跨度 > 阈值"的 skip，说明该判据在 runner 上真的不可用，应按 runner 重新定标而不是留着一条永不裁决的守卫。

## D-024 菜单栏面板从"拍不到"变成三个可复现的帧（顺带修掉一行重复文案）

- 背景：D-019 记下"菜单栏离屏拍不到 —— 菜单表面 97.7% 像素未绘制"，此后这一项一直挂 NOT-RUN。
  那句话**只对 macOS 12 的 NSStatusItem/NSMenu 路径成立**：`MenuBarController.configure` 在 13+ 直接 return，
  真正上线的是 `App.swift:24` 的 SwiftUI `MenuBarExtra`，它的 body（`MenuBarRecommendationsView`）就是一个普通 View，
  可以像其他 63 个夹具一样离屏渲染。之前"拍不到"是把"NSMenu 拍不到"错当成"整个面板拍不到"。
- 决定：帧数 58 → 64，三个状态各拍亮/暗：有推荐、`isRefreshingPredictions == true`（"正在整理推荐…"）、
  确实没有（"暂无推荐"）。给 `Fixture` 加一个可选 `settle`（布局完成、按快门之前跑一次），
  专给"内容要等一次异步刷新才落定"的视图；不 settle 的帧只能拍到刷新途中，而那一帧是不是最终态取决于机器快慢。
- **"正在整理"那一帧在快门前断言刷新仍在途**：帧名声称的状态必须由帧自己证明，
  否则"名字叫 refreshing、画面上写着暂无推荐"这种错，肉眼比对 diff 也发现不了。
  变异对照（`refreshPredictions()` 直接 return）⇒ 该套件红 4 次（两个状态 × 亮暗），说明这两道闸都有牙。
- 数据安全：store 一律 `RecordingHistoryPersistence` + `TestClipboardWriter`，`AppDelegate` 走 D-019 的注入接缝，
  不调 `configure()`、不 `startMonitoring()` ⇒ 不读不写 `~/Library/Application Support/时间剪史/`（D-002）。
- 可复现性前提（必须先确认，否则这组帧不能进逐字节比对集合）：reason 文案含"当前在<App 名>"，
  取自 `effectiveFrontmostApp()`；测试进程 `lastFrontmostBundleID` 恒 nil ⇒ 回落到"第一条记录的来源 App"，由夹具固定。
  实测同代码连拍两次 **64 帧 sha 集合完全一致**。
- 结果（这才是做视觉审计的目的）：**第一次用眼睛看这一面板就发现一处内容缺陷** ——
  首行 `文本 · Safari · 偏好链接 · 回到Safari · 24%` 把来源 App 在同一行里说了两遍，
  而该行只有两行位置。`16d658d` 修掉：先算 App 亲和标签，只有没有任何标签点过来源 App 时才补裸名；
  无亲和标签时裸名保留（唯一来源信息），跨应用（`Safari→Notes`）也钉成只出现一次。断言先写、对旧实现报红（2 次）后才改实现。
- 明确不做的：不在离屏帧上判"按钮宽度不齐/文字居中"是缺陷 —— 真实 `MenuBarExtra` 是菜单样式，
  Button 会变成整宽左对齐的菜单项，离屏宿主给的是 `.bordered` 居中圆角按钮。系统菜单的材质/圆角仍 NOT-RUN，
  那两层需要在屏捕获（未做）。
- 兼容性/回滚：`RecommendationPresenter.reason` 只改文案组合，签名、特征、打分全未变；
  数据格式未变。回滚 = `git revert 16d658d 37f43f6`。
- 验证：`swift build` 0 告警、`swift test` **301 例 / 5 skip / 0 失败**（含新写的 3 条 reason 断言）、
  64 帧两次连拍 sha 相同、变异对照双向点亮（红侧 + skip 侧，见 D-023 与本条）。

## D-025 "侧栏图标不可见"量成数字：判为离屏语义色伪影，产品不改（第二轮 1.9 收尾）

- 背景：审计 1.9 说设置侧栏图标未选中的比选中的轻。`settings-*-light.png` 里那列确实几乎看不见，
  而 `SettingsView.swift` 里有一条注释用"真机不可能长这样"把它判成捕获伪影 —— 那是**推断**，不是测量。
  本轮先按 D-024 的思路补了一条像素判据（逐行量图标列墨水），想顺手把这一项关掉。
- 测量结果（同一套离屏管线，`Color.black` 与 `.primary` 只差在颜色）：
  产品里未选中四行图标列 = **0.0000**，选中行 0.3885（其实是高亮底色）；换成固定 `Color.black` → 0.175–0.402 全画出来；
  而复刻的 `List(.sidebar)` 行里 `.primary` 和固定色**一样**能画（带不带 `.plain` Button 四种组合都试了）。
- 决定：**产品代码一字不改**，`.hierarchical` 保持。理由：能证明的是"这一帧在这一组合下不解析语义色"，
  不能证明产品错；反过来如果为了讨好这帧把 `.primary` 写成固定色，就会在真实深浅色切换时把颜色写死 —— 用伪影去改产品是净损失。
  注释换成上面那组数字（含"仍未定论是哪一层导致的"）。
- 中途走错的一步已回退：看到"产品里 primary 画不出来"时，我先改了实现（`Label{...}icon:{...}` + `.monochrome`），
  那是在**没排除测量工具本身**的情况下动产品；复刻实验一出来就还原了。教训：帧里"看不见"先问管线会不会说谎，再改代码。
- 探针的形状：常规套件里只留**版本无关**的前提断言（固定色必须画得出来，否则整问不可测）；
  语义色那部分只在视觉审计开关下量、把结论 `print` 出来，不写成断言 —— 具体比例随 macOS 版本变，
  写成断言只会得到"CI 环境红"（本轮已经为这类红付过四次代价，见 D-023）。
- 顺带删掉一条我自己十分钟前写的用例（`SettingsSidebarIconVisibilityTests`）：它通过 `.primary` 去断言产品可见性，
  而本条测量证明那个读法无效。它是被替换、不是被删掉让测试变绿 —— 同一问题现在由上面那条前提断言 + 打印结论覆盖。
- 兼容性/回滚：只动注释与一个测试文件；`git revert 2817a93` 即可。
- 验证：`swift build` 0 告警、`swift test` **303 例 / 6 skip / 0 失败**、64 帧与改动前 **sha 全同**（证明注释改动不改变画面）。
- **仍未验收**：真机上这一列图标到底长什么样（需要在屏捕获；`CGWindowListCreateImage` 在 14+ 已废弃，
  用在测试里会打破 CI 的 0 告警闸门，ScreenCaptureKit 又要屏幕录制授权 —— 会弹用户机器的权限框，故未做）。

## D-026 给"猜出来再删按钮"的判断补上测试（第二轮 08-08 / 13-08）

- 背景：`WindowConfigurator.Coordinator.isSidebarToolbarItem` 靠一串关键词决定从窗口工具栏**摘掉哪些项**，
  审计两轮都记着它没有任何测试（08-08、13-08）。误判的代价是用户少一个按钮且没有任何提示，
  所以这条比一般的"没测试"更值得补。
- 决定：`private` 放宽到 internal（与 D-021 放宽 `populate(_:)` 同一手法，行为一字未改），
  补 `WindowToolbarSidebarClassificationTests` 9 条：正向覆盖 SwiftUI 生成的标识、英文 label / paletteLabel / toolTip、
  中文「边栏」「侧边栏」、包在自定义 view 里的子视图 action、无障碍标签、AppKit 的 tracking separator；
  负向（更承重）覆盖我们自己的复制/筛选/搜索项、空项、只含「窗口」「side」「split」的项必须活下来。
- 两条实测发现，都写进了注释：
  1. **`item.view = nil` 会顺手清掉 `item.action`**。第一版夹具无条件赋值，于是"按 action 认出 toggleSidebar"那条红了 ——
     红的是夹具不是产品（`swift` 脚本单独复现：赋 view=nil 后 action 读回 nil）。
  2. **函数里那条 `item.action == #selector(toggleSidebar(_:))` 直判是冗余保险**：把它删掉，9 条仍然全绿，
     因为字符串路径也会命中 `"togglesidebar:"`。用例注释按这个口径写，不让读者以为那条分支被覆盖了。
- 变异对照（都实跑、跑完 `cmp` 逐字节还原）：删「边栏」关键词 ⇒ 恰好中文那条红；删子视图递归 ⇒ 恰好 custom-view 那条红。
- 兼容性/回滚：只有可见性放宽 + 新测试文件；`git revert` 本提交即可。
- 验证：`swift build` 0 告警、`swift test` **312 例 / 6 skip / 0 失败**。
- 同批另一条（`e8a59e4`，CI 第五次红）：离屏图标探针把"文字列数出 5 行"写进了断言，
  macos-15 runner 上同一段列表只数出 4 行 ⇒ 红。改成量"整列墨水"（不依赖行几何），
  并用"把符号名换成不存在的名字 ⇒ 墨水 0.0000 判红"证明这条判据不是装饰。
  **同一个根因（本机实测数字进断言）这一轮已经付过五次代价**，见 D-023 与 `AGENT_STATE.md` 的 CI 记录。

## D-027 快捷键录制器补测试，顺带修掉"录完还显示请输入快捷键"（第二轮 13-08）

- 背景：审计 13-08 列的覆盖缺口里，`HotKeyRecorderView` 的失焦路径没有测试。这个控件录制时**吃掉所有按键**，
  卡在录制态就等于窗口里按什么都没反应，而界面上只有一行小字 —— 属于"退出路径比进入路径更要紧"的那类。
- 决定：只测可观测的东西（按钮标题、两个回调、窗口第一响应者），不读私有的 `isRecording`。6 条用例：
  进入录制显示提示语 / Esc 取消且不改快捷键 / 合法组合被采纳并回调 / 无修饰键被拒且保留原值 /
  **录制中途失焦必须退出** / 空闲时失焦不许改标题。
- 结果：5 条直接绿，第 3 条红 —— 而且红的是产品：录下 ⌃K 之后按钮仍写着"请输入快捷键"，
  因为 `shortcut` 的 `didSet` 在 `isRecording` 还是 true 的那一步跳过改标题，之后再没人回显；
  它只在下一次 SwiftUI 刷新把同一个值重新赋一遍时才恢复。修法就是录完立刻显式回显（`14a37a0`）。
- 夹具坑（写进测试注释）：裸 `NSView` 的 `acceptsFirstResponder` 是 false，
  用它当"接走焦点"的目标会让 `makeFirstResponder` 直接失败 —— 那样失焦用例红的是夹具不是产品。
  与 D-026 里 `item.view = nil` 会清掉 `item.action` 是同一类：**探针自己会造红**。
- 兼容性/回滚：只加一行标题回显，无数据、无接口变化；`git revert 14a37a0` 即可。
- 验证：`swift build` 0 告警、`swift test` **318 例 / 6 skip / 0 失败**、64 帧与修复前 **sha 全同**
  （这条路径不在捕获夹具里，帧不变是预期，但仍然是测出来的）；
  变异对照：删掉 `resignFirstResponder` 覆写 ⇒ 恰好失焦那条红。
- 13-08 剩下的两块（设置页交互、生命周期回调）本轮**没做**，理由记在 `AGENT_BACKLOG.md` 快照 11。

## D-031 v1.4.8 出包与发布（用户授权）

- 触发：用户看完侧边任务修掉的两个缺陷（D-029 启动闪退、D-030 焦点环）后说"这一版可以封装为 release 提交为 v1.4.8"。
  本轮整改的全部改动（审计第二轮 N-1…N-4 / R2-01…R2-19 + 行内交互 D-028）第一次进交付物。
- 决定 1：**出包前先补发布链路的启动闸门**（`d698a4c`，见 R2-21）。理由是 v1.4.8 的前一版构建物就是"全绿但打不开"，
  而链路上没有任何一步真的执行过它。闸门做成静态读反汇编而不是启动用户的 app：后者会读他真实存档、还可能触发写盘（D-002）。
- 决定 2：**发布说明与 CHANGELOG 由脚本草稿重写成真实内容**。脚本产出的是"待补充/待确认"占位（v1.4.6 那次差点发出去，
  已写在 `docs/RELEASE_PROCESS.md` 的坑里），本版逐条对着提交历史重写，并明确列出"还没做到的"四条
  （未公证、多文件拖出、AI 未接线、Tab 到列表行未在其机器复测）。
- 决定 3：**R2-21 只标"部分完成"**。静态闸门证明的是"不会在 `-init` 上 trap"，证明不了"窗口建得起来"；
  运行时冒烟（进程活过 N 秒 / 启动日志出现守卫放行）仍是缺口。把闸门当成功劳全关掉，下一轮就不会再有人补那一步。
- 资产命名沿用 v1.4.7 的实测口径：仓库内 `releases/时间剪史_v1.4.8.dmg(.sha256)`（中文），
  GitHub 资产用 ASCII 名 `ClipboardHistory_v1.4.8.dmg(.sha256)`，且**上传的那份 .sha256 里写的是 ASCII 文件名** ——
  否则用户下回来 `shasum -c` 必然失败（v1.4.6 踩过）。
- 交付验证（都对**产物**做，不是对构建前的中间物）：
  · DMG `hdiutil verify` 通过；挂载后 `Info.plist` 的 `CFBundleShortVersionString` = 1.4.8、`CFBundleExecutable` = ClipboardHistoryApp；
  · 启动闸门对 DMG 内的二进制再跑一次：通过，且仍读到 2 个良性桩类名（证明解析器不是瞎的，"通过"是有内容的通过）；
  · `codesign --verify --deep --strict` 有效；`spctl -a -t execute` **rejected** —— ad-hoc 签名未公证，预期如此，
    所以发布说明里保留 Control-点击「打开」的指引；
  · 发布后自检：`gh release list` 的 Latest = v1.4.8；`gh release view --json assets` 里 GitHub 自己算的
    `sha256:c31a16e0…e88d` 与本地/仓库内 .sha256 逐字一致（独立第二估计器）；
    在仓库外目录 `gh release download` 后 `shasum -a 256 -c` 报 OK。
- 代码状态：`e4aee3c`（tag `v1.4.8`，轻量 tag 打在发布准备提交上，与 v1.3 起的做法一致）。
  该提交上实测 `swift build` 0 告警 · `swift test` 328 例 / 9 skip / 0 失败 · 发布脚本测试 30 例 OK · 68 帧基线。
- 回滚：线上 Latest 可退回 v1.4.7（`gh release edit v1.4.7 --latest` 语义等价于把 Latest 指回去）；
  存档格式仍是 v1，v1.4.7 读 v1.4.8 写出的存档只会忽略两个新增可选字段。


## D-029 修掉 D-019 带进去的启动闪退（S1：产品一打开就 trap）

- 现象（用户报）：从仓库根目录打开新打的包**闪退**。`~/Library/Logs/DiagnosticReports/` 里 23:05 有两份 .ips，
  历史里这个 app 从未崩溃过 ⇒ 新包特有。
- 定性：崩溃 PC `0x100011620` 的上一条是
  `bl _unimplementedInitializer(className:"ClipboardHistoryApp.AppDelegate", initName:"init()", file:"AppDelegate.swift")`，
  紧跟 `brk #0x1`（`EXC_BREAKPOINT`/SIGTRAP）。即 Swift 的**"未实现初始化器"桩**，不是空指针、不是手势改动。
  包的 arm64 UUID `6993EE12-…308B2` 与崩溃报告一致 ⇒ 就是仓库根目录那个包。
- 根因：D-019 把 `AppDelegate` 从"只有隐式 init + 属性默认值"改成显式
  `init(historyStore: HistoryStore? = nil)`。NSObject 子类一旦自己声明 designated initializer 而**不**
  `override init()`，编译器就给 ObjC 的 `-init` 留 trap 桩；而 SwiftUI 的
  `@NSApplicationDelegateAdaptor(AppDelegate.self)` 存的是**元类型**，正是通过 ObjC 发 `-init`。
- 为什么 327 个用例与 CI 全绿却挡不住：Swift 侧写 `AppDelegate()` 会解析到 `init(historyStore: nil)`
  （默认参数），**永远碰不到** `-init` 那条路径；CI 只跑 `swift build && swift test`，从不启动 .app。
  对照：`81bce8d`（v1.4.7 那条线）没有显式 init，所以线上版本不会崩 —— 这个崩溃从没进过任何发布。
- 修法：`override convenience init() { self.init(historyStore: nil) }`（三行，产品语义一字未变）。
- 守卫两条，形状不同所以互补：
  ① 运行时 —— `(AppDelegate.self as NSObject.Type).init()`，走的就是 SwiftUI 那条元类型调用。
     **修之前它让测试进程原地打出同一句 fatal error 并 signal 5 退出**（与 .ips 同一条消息），修之后绿。
     代价是这条红法是"整个进程没"，所以不能只靠它。
  ② 源码扫描 —— `AppDelegate.swift` 的正文（去注释后）必须含 `override init()` / `override convenience init()`。
     便宜、确定性、上面那条被删也还在。
- 顺带记下：二进制里还剩 3 个同类桩（两个 SwiftUI `Coordinator` + `ChineseSelectableNSTextView`），
  它们都只在 Swift 侧被显式构造，不经 ObjC 元类型 ⇒ 良性。下次审计别再从零查一遍。
- 交付验证（不启动用户 app 也能盖章）：`make bundle VERSION=1.4.7-fix1` 重打，
  新包 arm64 UUID `8A1FB38C-…`（≠ 崩溃那份，证明确实重编过），反汇编里 AppDelegate 的桩消失、
  `unimplemented` 站点 4 → 3。**真机启动仍待用户确认**（我不去启用户的 app：会读他真实存档并可能触发写盘）。
- 兼容性/回滚：`git revert` 本提交即可；无数据格式变化。本地包版本标成 `1.4.7-fix1` 只是为让用户能分辨，
  仓库里的 `Makefile: VERSION := 1.4.7` 未动 —— 发不发 v1.4.8 仍是用户决定。
- 结构性缺口另开条目（R2-21，高）：**发布链路没有"能不能启动"这一关**。

## D-030 关掉列表容器的系统焦点环（用户报"双击后列表外圈蓝框"）

- 现象：双击一行之后，整个左侧列表外面出现一圈蓝色边框，用户要求移除。
- 定性：那是 R2-02 加的 `.focusable()`（为了让方向键能走列表）带来的**系统焦点环**。
  探针先给出两个反直觉的读数：① 第一响应者 `KeyViewProxy` 的 `focusRingType` 本来就是 `.none`
  ⇒ 环不是 AppKit 画的；② 视图树里是 SwiftUI 的 `_FocusRingView`，其中一个是
  `{{0,125},{320,335}}` —— 尺寸正好是整块列表，就是那圈蓝框。
  顺带还踩到自己写过的那个坑：`XCTAssertEqual(holder?.focusRingType, .none)` 里的 `.none`
  被解析成 `Optional.none`（nil），断言永远不成立 —— 可空值上的"某个枚举的 none case"必须写全名。
- 试过又放弃的验证路：把窗口拍一帧用眼睛看。`cacheDisplay` 在"已聚焦的真实窗口"上会画歪
  （亮暗都错、只画出一行），拿它当"环在不在"的证据是不可靠的 ⇒ 判据换成结构化的环视图清点。
- 决定：`.focusable()` 保留（方向键导航不能坏），在它后面加 `sidebarFocusRingHidden()`，
  内部是 macOS 14+ 的 `focusEffectDisabled()`。
  **macOS 12/13 上这圈环仍然会出现** —— 平台没有对应开关，不是漏做；探针的失败消息里写明这一区分。
- 前后都是量出来的：改前 `_FocusRingView` 共 15 个（含列表整块那个），改后 2 个（筛选 pill 自己的，与列表无关）。
- 守卫三条：① 在屏探针断言"不允许存在覆盖整块列表的焦点环视图"（`CLIPBOARD_HISTORY_UI_INTERACTION=1` 才跑）；
  ② 源码扫描同时钉住"还挂着 `.focusable()`"和"环被抑制"两件事，防止改一个坏另一个；
  ③ 再加一条"抑制函数里必须真的调用 `self.focusEffectDisabled()`"，防止 ② 被一个空壳函数骗过。
  ② 的牙都用变异对照验过：删掉调用点 ⇒ 恰好那条红。
- 兼容性/回滚：纯视觉，无数据无接口变化；`git revert` 本提交。
- 验证：`swift build` 0 告警 · `swift test` **328 例 / 9 skip / 0 失败** · 68 帧与改动前 **sha 全同**
  （焦点环在未聚焦的离屏夹具里本来就不画，所以帧不变是预期，仍是测出来的）·
  包重打为 `1.4.7-fix2`（UUID `1FBD7DF5-…`，与 fix1 的 `8A1FB38C`、崩溃那份的 `6993EE12` 都不同）。

## D-028 行内直接操作：双击复制 + 行首星标收藏（用户提出）

- 需求（用户原话）："选了一条记录要把鼠标滑到最右边才能操作收藏和复制" ⇒ 双击条目复制、点行首星标收藏/取消。
  这两个动作以前**只存在于详情区右下角的浮层**（`DetailView` 的 `GlassPill`），行上没有任何入口。
- 结构决定：星标做成行的**兄弟控件**，不是嵌在行 Button 里的控件。嵌套 Button 在 macOS 上点击归属不可靠；
  并且这条决定是可测的 —— 在屏探针断言"点星标之后选中集合不变"，实测 `favoriteFired=1 / selectFired+=0`。
  双击用 `Button(单击选中) + .simultaneousGesture(TapGesture(count: 2))`，**不是**把行改成
  `onTapGesture(count:2)+onTapGesture`：后者会让系统为一个可能的双击先等一个间隔，每次点选都慢半拍。
  代价是双击时第一击照常选中（幂等），实测 `copyFired=1`、`selectFired+=2`，符合预期。
- 语义选择：双击 = `.copyAndPromote`，与浮层那颗"再次复制"**同一个动作**（会写剪贴板并把这条顶到最前）。
  带 shift / command 的双击**不复制**（那两个键是本列表范围选择/多选的前缀，误双击不该写剪贴板），
  规则抽成 `RowDoubleTap.shouldCopy`，并有一条守卫去读 `select(_:)` 真正用了哪些修饰键 ——
  将来选择侧改用 option，这条会红着提醒例外名单要同步。
- 颜色是量出来的，不是挑的：未收藏的星以前是 `.clear`（等于这个控件不存在）。
  `primary.opacity(0.28)` 实测对比度 **1.76:1（亮）/ 2.17:1（暗）**，低于可交互控件的 3:1 下限；
  提到 0.55 后 **3.54:1 / 4.64:1**。已收藏的星从 `Color.yellow`（亮色 **1.67:1**）压深成琥珀
  `Color(red:0.86,green:0.45,blue:0)` ⇒ **3.90:1 / 4.28:1**。行内星标与浮层共用
  `FavoriteTogglePresentation`（符号/文案/收藏色），并有一条源码扫描守卫禁止两处再各写字面量。
- 验证（关键区别：这次是**真点**）：`UIInteractionProbeTests.testRowGesturesFireTheRightActions` 往一扇
  真实在屏窗口里的孤立一行投递合成的 `leftMouseDown/Up`，断言三件事 —— 单击选中、1→2 序列恰好触发一次复制、
  点星标翻收藏且不动选中。
  **探针一开始是错的**：它按"行高 74"点了 y=37，而 `HistoryRowButton` 的自然高度是 47，星标只有 20pt 高，
  于是表现为"点星标毫无反应"。网格扫描（x=8..26 / y=16..28 全部命中）证明控件是活的、是探针瞄偏了 14pt。
  修法是把 y 从宿主视图真实高度推，不写死。
- 补一条**真实容器**里的同一验证（`testRowGesturesWorkInsideTheRealSidebarContainer`）：孤立一行没有外层
  `ScrollView` + `LazyVStack` + 列表级拖选 `DragGesture` + `.focusable()`，而双击恰恰要穿过这一层。
  从宿主视图树里按几何挑出 6 个星标代理 (16,y,20×20) 与 6 个行代理 (38,y,266×31)，
  点最下面那一行：实测星标翻收藏、行改选中、双击**恰好写一次剪贴板**且写的就是刚点中的那条、并被顶到列表最前。
  这条探针也先错过一次：用"宽度 ≥26"挑行，结果挑中了 148×25 的筛选 pill，又是探针点错东西。
  判据改用 `TestClipboardWriter.writtenContents` 的计数与内容 —— 不依赖"第几行在最上面"这种几何猜测，
  也不会因为点的正好是第一行而恒真。变异对照：删掉 `.simultaneousGesture(TapGesture(count: 2))` ⇒
  该条立刻红（"写了 0 次"），还原后 `cmp` 逐字节相同。
- 兼容性/回滚：无数据格式变化；`HistoryRowButton` 多了两个闭包参数（调用点只有侧栏与夹具）。
  回滚 = `git revert` 本提交。`HistoryRow` 不再自带星标，`row-*` 夹具改为拍整条可交互行（帧 64 → 68）。
- 验证汇总：`swift build` 0 告警 · `swift test` **324 例 / 7 skip / 0 失败** · 68 帧两次连拍 sha 相同 ·
  与颜色改动前的帧相比 `row-*`/`sidebar-*` 有预期差异（新增星列），其余帧不变。
- 已知遗留（记成 R2-20，未修）：`toggleFavorite` 走 `reconcileSelection(preferredEntryID:)`，
  会把多选**收成那一条**。这是浮层收藏一直以来的行为，行内星标只是把它搬近了手边。

## D-032 右键菜单汉化：编辑态的右键只能从事件层截走（issue #13）

- 需求（issue #13）：应用内右键菜单里有未汉化的系统项（快速查看附件 / 字体 / 书写方向 / 布局方向 / 服务 / 查询…），
  既英文又与本产品无关。
- **四条被实测证伪的做法**（前三条都曾经是这里的方案）：
  1. "给搜索框子类化的 `hitTest` 做让位，就能把右键从共享 field editor 手里拿回来" —— 实测编辑态下 AppKit 把
     `rightMouseDown` **直接投给 field editor**：`ChineseMenuTextField` 既不收到 `rightMouseDown`、`menu(for:)` 也不被问；
     而 `NSApp.currentEvent` 在合成事件派发期间**逐条为 nil**（7 条 HITTEST 日志全 nil），
     所以"看当前事件类型"那条分支连测都测不出来。这套机制已从仓库删除，不留下测不到的代码。
  2. "`editor.menu = 我们那份` 就能改掉 field editor 的右键菜单" —— 实测会被 AppKit 复原：右键时读 `editor.menu`
     得到 12 项「剪切/拷贝/粘贴/粘贴并匹配样式/**快速查看附件**/**字体**/拼写和语法/替换/转换/语音/**书写方向**/**布局方向**」，
     正是 issue #13 报的那一串。那段挂菜单的代码看着像修好了，其实什么都没改。
  3. "`menu(for:)` 返回的是可以就地改的那一份" —— 实测每次现造新的（两次调用 `!==`）；把第一份 `removeAllItems()`
     并关 `allowsContextMenuPlugIns` 之后再问一次，内容又是满的（7 项）、开关又回到 `true`。
  4. "让菜单真弹起来量屏幕上那份" —— `NSMenu.popUpContextMenu` 是模态的，在 `NSMenu.didBeginTrackingNotification`
     回调里 `cancelTrackingWithoutAnimation()` **不能**让它返回（8 秒监视线程直接 exit）。判据因此改用
     AppKit 决定菜单的那个入口（`NSResponder.menu(for:)`）+ 拦截器的实际交付，不靠"弹出来再看"。
- 采用的机制：`NSEvent.addLocalMonitorForEvents(matching: [.rightMouseDown, .otherMouseDown])`
  （新类型 `FieldEditorRightClickInterceptor`，装在 `ApplicationShell.applicationWillFinishLaunching`）。
  它在 AppKit 派发**之前**看到事件，只作用于本 App 的事件流，不需要换 window delegate、不碰私有 API。
  认领判据 = "第一响应者是 `NSTextView`，且它沿 superview 往上属于某个 `ChineseMenuTextField`" ——
  实测 field editor 确实挂在搜索框子树里（`editor.superview == _NSKeyboardFocusClipView`、
  `isDescendant(of: 搜索框) == true`），所以不需要私有 API 也能把"这次编辑是谁的"问出来。
  认领就吞掉事件并弹我们那份，不认领原样交回 —— 别的控件的右键不受影响（有反面对照钉着）。
  范围是完整的：全仓库只有 `SearchField.swift` 一处可编辑文本（`grep "TextField("` 只有它 + 它自己的构造），
  只读详情区由 `ChineseSelectableNSTextView` 自己接管，非编辑态搜索框由 `menu(for:)` 接管。
- 交付的菜单（每一项都中文、都 `allowsContextMenuPlugIns = false`、弹出前再 `sanitize` 一次）：
  搜索框 `撤销/重做/剪切/复制/粘贴/全选`；只读详情区 `复制/全选/查找…`。
  另加 `NSWindow.allowsAutomaticWindowTabbing = false`（建窗之前设）从源头压掉「Show All Tabs」那一类窗口级项。
- 验证：
  - 单元 `ChineseTextContextMenuTests` 13 例：菜单内容与顺序、通用"任何一项都必须含中文"、
    `sanitize` 的阳性对照与首尾分隔线规则、`menuWillOpen` 真会清、拦截器认领判据的**两个方向**、
    三条源码守卫（不许回到 `editor.menu =` 反模式、启动时必须 `install()`、`install()` 不许装到视图层）。
  - 在屏（`CLIPBOARD_HISTORY_UI_INTERACTION=1`）`testRightClickMenusAppKitWouldShowAreChinese`：
    真左键进编辑态 → 装监视器 → 投**真实右键事件** → 断言交出去的就是那六项；只读区取 `visibleRect`
    而不是 `bounds`（bounds 比视口大得多，拿它的角去点会点到窗口外，报假缺陷）。
  - 变异对照 5 组，全部按预期点亮：删 `install()` ⇒ 启动守卫红；把认领判据改成"凡是文本视图都认领" ⇒ 3 条红；
    让 `handle` 不吞事件 ⇒ 在屏探针挂在 AppKit 那份模态菜单上，**看门狗 20 秒写清原因后 `exit(73)`**
    （所以这条探针 broken 时是 bounded 的红，不是把机器钉住）；往菜单塞一项挡名单外的英文 ⇒ 两条路径同时红；
    把 `editor.menu =` 那段加回来 ⇒ 反模式守卫红。每组还原后 `cmp` 逐字节相同。
  - `swift build` 0 告警 · `swift test` **339 例 / 10 skip / 0 失败**（skip 全是 env 门控的在屏探针）。
- 兼容性/回滚：无数据格式变化、无依赖变化、无对外 API 破坏，新增类型都是 internal；
  监视器成对提供 `install()/uninstall()` 且幂等。回滚 = `git revert` 本提交。
- 已知遗留（进 `AGENT_BACKLOG.md`）：① 屏幕上"真弹出来的样子"无法在仓库里自动断言（模态），
  只能手工核对，清单在 `docs/MANUAL_TEST_v1.4.8_issue13.md`；② 将来若新增可编辑文本控件，
  必须走 `ChineseMenuTextField`，否则拦截器不认领，那份右键菜单又会是系统的。

## D-033 第三轮审计整改：列表换成 `List(selection:)`（用户指定修法③）+ D-2…D-8

- 输入：`/Users/wangziyi/Documents/时间剪史_审计_2026-10-10_第三轮/00-第三轮审计与改进方向.md`，本轮 8 条新缺陷 D-1…D-8。
  用户点名两处做法：**D-1 用文档里的第三种修法**；**D-3 给「通用」补上真正属于它的两项**（不选"合并进数据"那条）。
- **D-1（S2）换 `List(selection:)`，是对 R2-02/D-028 那条"不要整体换成 List"决定的推翻**。
  推翻的理由写清，否则下一个读账本的人会以为我在反复：当初三条理由里 ——
  ① `.draggable` 要 macOS 13：现在仍然不用它，拖出走 `onDrag` + 把手；
  ② 系统 chrome 会改掉 `sidebar-*` 帧：接受，帧已重基线（`sidebar-history-dark` 与审计帧差 72.87%）；
  ③ 会丢 `dragSelectRange` 锚点语义：拖选仍然是我们自己的手势，store 动作一个没删。
  收益就是审计说的那四件事一起解决：单击选中、shift/⌘ 多选、方向键与滚动跟随、VoiceOver 的 selected 语义
  全部交回系统，`SidebarKeyboardNavigation`（方向键落点纯函数）与 `onMoveCommand` / `ScrollViewReader` 一起删除。
- **拖出与拖选的分工**写在 `EntryDragGate.prepareForDrag(origin:content:)`：只有 `.handle`（行首缩略图/图标）
  且条目有载荷才开拖出会话；`.rowBody` 永远判 false —— 那正是缺陷的形状（整行挂 `onDrag` ⇒ 系统在每个阈值处
  先开会话，拖选整片失效）。行体不再自带"选中用的 Button"，选中只剩系统一套语言。
- **一条被实测出来的测量限制（重要）**：换成 `List` 之后**合成鼠标事件驱动不了表格**
  （`NSApp.sendEvent` 与 `window.sendEvent` 两条都试过；`table.clickedRow` 恒为 -1，
  伴随 `isKeyWindow=false isActive=false` —— xctest 进程拿不到激活）。
  后果：D-1 的三条行为判据（点选 / 双击复制 / 拖选扩选）与孤立行的星标点击**都不再能自动化**。
  处理是拆开而不是假装：结构判据进常规套件（真 `NSTableView`、`allowsMultipleSelection`、行数=可见条目数、
  把手是唯一拖出入口、双击与星标的接线守卫），行为判据进手工清单第 1/2 节。
  原 `testRowGesturesFireTheRightActions` 删除 —— 它测的是"孤立一行 + 行内 Button"，那个东西按修法③已不存在；
  判据的去处写在探针文件原位置的一段注释里，不留"看起来还在测"的空壳。
- **D-2**：`contentTypeTag` 从"看前台 App 的 bundle id"改成"看条目自身类型"（常用链接/常用文本/常用文件/常用多文件）。
  这里有一条**旧用例钉的就是缺陷**（`testContentTypeTagsPerFrontmostApp` 断言 Safari⇒偏好链接）：
  按事实把它**翻转**成"同一份条目，前台怎么变标签都不许变"，而不是删掉。
- **D-3**：「通用」补两项，取审计 §5 点名的 F1/F4 —— 暂停记录、识别截图文字（OCR）。
  两个开关落 `UserDefaults`（用户偏好，不是历史数据，守 D-002 的数据目录边界）；
  OCR 的键写成 `ocrSearchDisabled` **取反**，因为 `bool(forKey:)` 对没写过的键返回 false，
  正向键会让"从没进过设置页的用户"默认关掉 OCR —— 那是悄悄改行为。
  判据抽成 `RecordingGate`：暂停只挡后台自动采集，**用户点名拖入的文件照常入库**，
  且 changeCount 照常推进（恢复瞬间不会补记暂停期间的旧内容）。
  开关刻意**每次决策时读** UserDefaults 而不是缓存成 `@Published`：跨窗口双向同步的坑不值得为省一次读换进来。
- **D-4**：`addDroppedFiles` 现在读 `ignoredCount` 并发 `droppedFilesNotice`，`ContentView` 用既有 `NoticeBanner` 呈现。
  以前这个数算出来没人读 ⇒ 用户看到落点框闪一下就什么都没发生。
- **D-5**：给 D-016"只加可选字段不升版"补上**新→旧→新往返用例**（真实写入器产出的 `history.json`
  交给一份按"加字段之前"形状定义的解码器，必须解得动、条目不缩水），并把边界写进 `migrate` 注释：
  改语义/删字段必须升 v2。
- **D-6**：降采样之后在同一后台路径里算出**新尺寸**的 PNG 字节再交给 `StoredImage`，
  首次编码不再掉到保存快照（`@MainActor`）或用户按住鼠标拖出的那一瞬间。
- **D-7**：CI 增加一个 `continue-on-error: true` 的步骤，真的跑 `UIInteractionProbeTests|UICaptureTests`
  并打印执行数与帧数（帧数 <60 或执行数 0 判这一步红）。先报告型不转硬门：无头 runner 上在屏窗口稳定性未证。
- **D-8**：设置侧栏 `sparkles`（实心）→ `wand.and.stars`（描线），与同列四项统一；配一条守卫禁止这组里再出现实心符号。
  **注意**：D-025 已证明"图标看不见"是离屏语义色伪影，这条只是设计一致性，不是对比度问题。
- 验证：`swift build` 0 告警 · `swift test` **355 例 / 10 skip / 0 失败** · 68 帧同代码连拍两次 sha 相同 ·
  变异对照 5 组（暂停开关恒真 / 拖入不提反馈 / 把手分工放宽 / 符号改回实心 / 标签回去看前台 App）逐一点亮，
  其中"拖入不提反馈"第一次因正则没命中而**变异没落地**，改用 python 断言锚点命中后重跑才拿到红。
- **帧里新出现的伪影要记账**：`sidebar-*`/`row-*` 帧里被选中的行画成一整块黑（文字不可见、缩略图还在），
  黑块精确跟随选中集合（三行选中⇒三块黑）⇒ 判定为 `List` 选中高亮在离屏 `cacheDisplay` 下的语义色伪影，
  与 D-025 同源，**不据此判产品**；真机看手工清单第 1 节即可确认。
- 兼容性与回滚：无存档格式变化（D-5 明确不升版）、无新依赖；`HistoryStore.add` 新增的是**带默认值的参数**；
  `SidebarKeyboardNavigation` 的删除是唯一被移除的旧符号（只有视图与它的用例用过）。
  回滚 = `git revert` 本轮提交；两个 UserDefaults 键即使留着，旧版也不读，不影响回退。

## D-034 拖选与拖出不能共存于 `List`：保留拖出、放弃拖选（用户真机反馈后决定）

- 触发：D-033 落地后用户真机一试就报"从第 1 行按下拖到第 n 行不会多选，只会把第一行拖成一个半透明条目跟着鼠标走"。
  这正是 D-1 的验收点（清单第 1.2 条），也是我在 D-033 里明说"只能真机看"的那条缺口被抓到。
- **被实测否掉的设计**：修法③原本想"拖出只从行首把手发起、行体留给拖选"，代码也确实只把 `.onDrag`
  挂在 30pt 的 `RowDragHandle` 上。但 `List` 底下是 `NSTableView`，**SwiftUI 会把行内任何一处 `.onDrag`
  提升成"整行是拖拽源"** —— 作用域不在子视图上。于是从行里任意位置按下都会开会话，
  而会话一旦开始，挂在容器上的 `DragGesture(minimumDistance: 4)` 就拿不到这串鼠标事件，拖选必然不发生。
  结论：在 `List` 里这个分工做不到，不是实现细节问题。
- 三条候选与取舍：① 自己实现 AppKit 级拖拽源（`NSView` 只占把手那一格，`mouseDragged` 里
  `beginDraggingSession`）可以同时保住拖出与拖选；② **保留整行拖出、去掉拖选**；③ 退回自绘列表用①的分工
  （但会丢掉修法③换来的原生键盘/VO/多选）。用户选 ②，理由与系统行为一致：
  macOS 的侧栏本来不做橡皮筋多选（Finder 侧栏也不做），而"拖一行去别的应用"是这个产品最有用的动作之一。
- 因此删除的东西要列清楚，避免下一轮有人以为是漏实现：`HistorySidebarView` 的 `DragGesture`、
  `updateDragSelection`/`endDragSelection`/`entry(at:)`/`rowFrameReader`/`HistoryRowFramePreferenceKey`、
  `rowFrames` 与 `dragSelectionAnchorID` 状态；`HistoryStore.Action.dragSelectRange`
  （`selectRange(from:to:)` 保留，锚点来源收回 shift 扩选一处）；`EntryDragGate` 从
  `prepareForDrag(origin:content:)` 退化成 `offersDrag(for:)`，`RowDragHandle` 这层消失，
  拖出与提示改挂在整行上（`EntryDragModifier` + `RowDragHelpModifier`）。
  **没有留任何半套死码**：一个永远抢不过表格会话的手势，比没有手势更坏，因为它让人以为拖选还在。
- 判据（都是能被打红的）：`testNoCompetingDragSelectGestureRemains`（侧栏不许再出现 `DragGesture`/
  `dragSelectRange`/`rowFrames`，store 里不许留 `dragSelectRange`）、
  `testDragAffordanceIsExactlyOneAndLivesOnTheRow`（出入口恰好一处、`RowDragHandle` 不许回来）、
  `testOffersDragOnlyWhenSomethingWouldActuallyBeCarriedOut`、`testDragHelpTextMatchesTheAffordance`、
  `testSidebarIsWiredToTheSystemList`。原来那条拖选探针（`testDragSelectExpandsSelectionInsideTheRealList`）
  删除并在原位置留了一段解释 —— 被测手势已不存在，留着就是假闸门。
- 变异对照三组，逐一点亮：把手势加回侧栏 ⇒ 守卫红；把手层写回行视图 ⇒ 守卫红；
  `offersDrag` 改成恒真 ⇒ 真值表与提示文案共 4 条红。三组还原后 `cmp` 逐字节相同。
- **一条对判据层的教训**（与"源码已修≠已交付"同族）：D-033 里我有一条守卫是"拖出入口恰好一处且挂在把手上"，
  它在**源码层为真**、在**效果层为假**，因为效果取决于 `List` 怎么提升作用域。守卫量错了层，
  所以它绿着放过了一个真回归。规矩：**凡是"作用域/归属"类断言，要有一条能落到真实容器上的判据**
  （这里只能落到真机清单），源码扫描只能钉"写法"，钉不住"AppKit 怎么处理这个写法"。
- 验证：`swift build` 0 告警 · `swift test` **355 例 / 10 skip / 0 失败** ·
  离屏 68 帧与改动前逐帧相同（`frame_audit.py diff` 合计 0/68 有变化）——
  这次改的是手势与拖拽源归属，不动像素，所以帧基线不需要重录。
- 兼容性与回滚：删掉的是 internal 的 `Action` case 与视图私有状态，无对外 API、无存档格式变化；
  回滚 = `git revert` 本次提交（要恢复拖选则需同时回退 D-034 与 D-033 的把手设计，或改走候选①）。

## D-035 图片文件条目补行内缩略图（用户真机反馈）

- 现象（用户截图）：详情区能显示 `board-icon-fullbleed…png` 的内容，左侧列表那一行却只有通用文档符号；
  同一列表里"图片 1188×1280"那条（剪贴板直接带图像数据的）是有预览的。
- 根因是**两条路径的差别**，不是渲染坏了：`.file` 条目的 `thumbnail` 来自剪贴板**顺带**给的
  TIFF/icns（`ClipboardIntake.readEntry`），从 Finder 复制文件时系统通常不给 ⇒ `thumbnail == nil`
  ⇒ 行首退回 `doc` 符号；详情区是按 URL 现读文件，所以两边不一致。拖拽入库（`addDroppedFiles`）
  更是直接写死 `thumbnail: nil`。
- 修法：新增 `FileThumbnailPolicy`（判据 + 从磁盘解图），`HistoryStore.attachFileThumbnailIfNeeded`
  走 OCR 那一套既有形状 —— **后台队列解码、主线程写回、写回后 `persist()`**，
  在 `add(...)` 里与 `scheduleOCRIfNeeded` 并排调用；另加启动回填 `attachMissingFileThumbnails()`
  （与 `scheduleOCRForExistingImages()` 同一时机），让老历史里那些条目也能补上。
- 两个刻意的设计约束：
  ① **只解小图**（长边 256px）。缩略图会落盘（`thumbnailFileName`），解全尺寸等于把用户文件
     复制一份进历史目录；行首只有约 32pt，256px 在 retina 上已经够清晰。实测 1200×900 的 PNG
     解出 256×192、1031 字节。
  ② **扩展名集合与 OCR 那条不同**：用 `FileTypeSupport.imageExtensions`（不含 svg），
     因为 ImageIO 解不了 SVG；OCR 的集合里有 svg（识别失败只是白跑）。两个集合的差别写在代码注释里，
     避免以后有人"顺手统一成一个"。
- 写回只有一条路：`applyThumbnail(entryID:thumbnail:)` 里"条目已不存在 ⇒ false"、
  "已经有缩略图 ⇒ false（不覆盖剪贴板带来的那一份）"，成功才 `persist()`。
  抽成独立方法而不是内联在闭包里，是为了让这一步能被直接测 —— 不用赌后台队列什么时候跑完。
- 验证：新增 `FileThumbnailTests` 7 例（真值表 6 个方向、真实 PNG 解码 + 尺寸上限 + 自带 PNG 字节、
  文件不存在/非图片返回 nil、写回一次且不覆盖、**端到端 `add` 后异步补上**、启动回填与行首分支两条接线守卫）。
  夹具新增 `row-file-thumb` 亮暗两帧（帧数 **68 → 70**，其余 68 帧逐帧不变）——
  这条帧存在的意义就是"图片文件行有预览"从此有像素可查。
  变异对照四组逐一点亮：判据恒 false ⇒ 2 条红；缩略图不限尺寸 ⇒ 尺寸判据红；
  `add` 里不排补图 ⇒ 端到端红；行首 `.file` 分支不看缩略图 ⇒ 2 条红。还原后 `cmp` 逐字节相同。
  `swift build` 0 告警 · `swift test` **362 例 / 10 skip / 0 失败**。
- 一条判据强度的自我更正：`testStartupBackfillIsWired` 里"store 必须包含
  `attachFileThumbnailIfNeeded(for: entry)`"这一条**分不清**调用点在 `add` 还是在启动回填里
  （两处文本相同），所以真正抓住 P3 的是端到端那条。留着它是因为它还钉着"启动必须回填"，
  但别再把它当成"新复制的条目接上了"的证据。
- 兼容性与回滚：无存档格式变化（`thumbnailFileName` 早就存在，只是以前对这类条目是空的）；
  新增的都是 internal 类型与方法。回滚 = `git revert` 本次提交，已补的缩略图留在磁盘上但不再显示，
  不影响读取。

## D-036 点选延迟一个双击间隔：为了过离屏探针改了产品行为（用户真机反馈）

- 现象（用户原话）："现在点击列表条目到显示为已选择有可感知的延迟，这是bug吗"。是 bug，而且是我这条会话里改出来的。
- 引入点：D-1 把行从 `Button` 换成 `HistoryRowButton`（行里没有兄弟手势了）之后，离屏交互探针测到
  `simultaneousGesture(TapGesture(count: 2))` 在**孤立宿主**里收不到第二击（`copyFired=0`），
  而 `.onTapGesture(count: 2)` 会。我于是把手势换成 `onTapGesture(count: 2)`，并在注释里写
  "单击选中仍然立刻生效 —— 那是 NSTableView 在 mouseDown 里做的，不与这个手势竞争"。
- 根因：那句注释是**假设，不是测量**。`count: 2` 的 tap 识别器要等一个双击间隔才能确定"这只是一次单击"，
  而换 `List(selection:)` 之后行的选中正是经由这一套行内点击识别下发的，于是高亮整体推迟了一个双击间隔。
  `simultaneousGesture` 不参与"谁赢"的仲裁，所以它没有这个副作用（D-028 当年在真实侧栏容器里验过这个形状）。
- **真正的错误在方法论**：夹具不代表真实容器，我却拿产品行为去迁就它。
  离屏探针的宿主是临时挂上去的行视图，不在 `List` 的层级里，它的"收不到第二击"是夹具属性；
  正确的处置是**把这条判据标记为测不到、转人工**（和拖选探针同一处置，见 D-034），
  而不是改手势让假绿变绿。规矩：**任何"为了让某条自动化判据点亮而改产品交互"的动作，
  先问这个夹具代不代表真实容器；不代表就只能改判据，不能改产品。**
- **更疼的一点**：这条延迟**仓库里早就写着**。D-028 原文就是"双击用 `Button + .simultaneousGesture(TapGesture(count: 2))`，
  **不是**把行改成 `onTapGesture(count:2)+onTapGesture`：后者会让系统为一个可能的双击先等一个间隔，每次点选都慢半拍"。
  我在 D-1 里把它换成了 `onTapGesture(count: 2)`，**没有去读自己那条决定的原文**就改了它。
  对照：D-033 推翻 R2-02（"不换 List"）时逐条对账、写在账本里，那次是对的；这次跳过了对账这一步，
  于是账本里那条理由白记了。规矩补一句：**改到别人（包括过去的自己）明确钉过的设计时，先读那条决定的原文再动** ——
  账本的价值正好等于你有没有去查它。
- 修法：行上的双击改回 `.simultaneousGesture(TapGesture(count: 2).onEnded { ... })`，
  例外名单（shift/⌘ 双击不写剪贴板）与 `copyAction()` 接线不变。
- 判据（这次钉"写法"，效果转人工）：`testRowGesturesAreStillWiredToTheirActions` 现在要求
  源里出现 `TapGesture(count: 2).onEnded` 与 `.simultaneousGesture(`，并新增一条**反向守卫**
  —— `.onTapGesture(count: 2)` 不许再出现在行上（出现即红，红由这条延迟回归本身引起，不是加载报错）。
  双击复制与点选无延迟这两条**效果**只能真机看，写进手工清单 §1 的 1.1 / 1.5 并具名。
- 验证：`swift build --build-tests` 0 告警 · `swift test` **362 例 / 10 skip / 0 失败** ·
  `SidebarListSelectionTests` 单跑 11 例全绿 ·
  变异对照：把行上手势改回 `.onTapGesture(count: 2)` ⇒ 该文件 3 条红，还原后 `cmp` 逐字节相同 ·
  离屏帧改前改后**0/70 有变化**（这次改的是手势仲裁，不动像素，帧基线无需重录）。
- 兼容性与回滚：无 API、无存档变化，纯视图层手势修饰符。回滚 = `git revert` 本次提交。

## D-037 CI 报告型步骤：汇报行自己的 grep 也能中止脚本（同族第三次）

- 现象：CI 两个"报告型"步骤（离屏帧 / 在屏探针）在 run 38062956819 里**又是红了但没有数字**。
  日志尾部只有 `##[error]Process completed with exit code 1.`，`captured frames:` 与 `ui suite exit:`
  两行根本没打出来。
- 根因不在被测命令，那层早就 `|| true` 了。坏在**汇报行自己的抽取命令**：
  - 离屏步骤里 runner 的 XCTest 只打了 `Executed 1 test,`（**单数**，因为只有 1 个用例被 filter 命中），
    而抽取用的是 `grep -oE 'Executed [0-9]+ tests'` ⇒ 匹配失败返回 1，`set -o pipefail` 把非零传给
    赋值语句，`bash -e` 当场中止。
  - 在屏步骤同理：看门狗收掉进程后日志被截断、根本没有汇总行 ⇒ 抽取非零 ⇒ 中止 ⇒
    我为"没跑完"写的那条分支**永远走不到**，而那条分支就是这段脚本存在的理由。
- 修法：抽取行全部 `|| true`，正则改成 `tests?`（以及 `tests? skipped`）。
- **同族第三次**（前两次：run 38050990090 的 `pipefail + tee`、run 38051846033 的 `wait "$pid"; status=$?`）。
  归纳出的规矩：**在 `bash -e` 里，"允许失败"的步骤中每一处可能非零的命令都必须自带兜底，
  包括那些只为拼一行日志而存在的 grep/awk** —— 汇报行不是日志，它就是这一步的全部产出。
- 判据：新增 `scripts/tests/test_ci_report_selftest.py`，它把 ci.yml 里这两个步骤的 run 脚本**原文**抽出来，
  只把被测命令换成夹具，喂三种形状（单数汇总 / 截断日志 / 正常复数）断言结论行必然打印、退出码符合预期。
  文件名按 `scripts/tests` 的 `test_*.py` 约定，所以 CI 的 `unittest discover` 会真的执行它（31 例）。
- 变异对照（本地实测）：把两处抽取改回旧写法 ⇒ `AssertionError: offscreen/singular_summary: 结论行缺失`、
  `Ran 31 tests ... FAILED (failures=1)`、退出码 1；还原后 `cmp` 逐字节相同、`Ran 31 tests / OK`。
  另有一条**自证**：这个自检第一版自己被吊死在超时上 —— 看门狗的 `sleep 240` 变成孤儿后仍持有继承的
  stdout 管道，`communicate()` 等不到 EOF；改成"输出写文件 + 独立会话按 pgid 收组"才通。
  教训：**测别人的挂死时，自己的夹具不能靠管道读输出**（真实 runner 不挂是因为它一直在读管道）。
- 兼容性与回滚：只动工作流与新增测试脚本，不碰产品码。回滚 = `git revert`。

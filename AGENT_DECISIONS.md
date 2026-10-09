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
- 同一提交里的另一处方法修正：图片比较的性能闸在负载 28.8（10 核）时报出 997ms 假红，而单跑三次是 155–171ms。现在它先打印 `load1` 与活跃核数，比值 > 2 时 skip 而不是误判回归；**<250ms 的判据本身没动**（仍低于它要否证的旧值 434ms）。

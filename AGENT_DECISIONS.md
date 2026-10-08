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

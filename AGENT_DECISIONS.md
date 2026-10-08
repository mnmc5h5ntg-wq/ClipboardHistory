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

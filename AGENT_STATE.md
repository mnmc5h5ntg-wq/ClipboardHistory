# AGENT_STATE · 当前工作状态（自主修复引擎）

最后更新：2026-10-09 01:4x（本地）
**仓库位置（2026-10-09 起）**：`/Users/wangziyi/Codex_Project0`。
原先在 `~/Documents/Codex_Project0`，那在 iCloud「桌面与文稿」同步范围内（`CloudDocs/Documents` 是指向 `~/Documents` 的符号链接，
`bird` 在跑），同步会在仓库里留下 `名字 2.扩展名` 的重复副本 —— 本次就出现 29 个，SwiftPM 把 `Sources/` 下的类型编译两遍，构建直接崩，
第一次发布准备因此失败。旧路径现在是一个指向新位置的**符号链接**（保住旧书签/旧会话路径），确认无误后可以删掉它。
搬离时实测：跨出同步边界的 `mv` 会 `Operation timed out`（File Provider 需要先物化），要用 `rsync -a` 复制 + 校验 + 再删源。
分支：`fix/audit-remediation` 已删除（本地与远端；其提交全部在 `main` 上，删除前用 `git log main..分支` 验过为 0）
回滚基线：提交 `8007b19` "Checkpoint: 1.4.5 working state before audit remediation" —— 修复前工作区的全部 WIP（含此前未被 git 跟踪的 `Intelligence/` 等 25 个路径）已入该提交。**任何一步都可以 `git revert` 或 `git diff 8007b19..HEAD` 审查。**

## 权限与边界（本轮）

- 工作区内可读写增删；允许 git 写操作（不 push，不 `--force`，不改 config，不跳过钩子）。
- 禁止：伪造验证、删测试或改断言来"绕过"、把工作区外的破坏性操作当副作用。
- 数据/接口/依赖/架构变更必须兼容、可迁移、可回滚、有记录 → 一律写进 `AGENT_DECISIONS.md`。
- **用户真实数据保护（重要）**：`~/Library/Application Support/时间剪史/` 是用户真实剪贴板历史。在 A-3（损坏存档 + 一次复制即全量删除）修复之前，**不得**以默认数据目录启动真实 App；所有验证都用临时目录或环境变量重定向。

## 基线数字（已实测，作为改进的对照）

| 指标 | 基线 | 命令 |
|---|---|---|
| `swift build` | OK，5.81s（含 1 条编译告警） | `cd ClipboardHistory && swift build` |
| `swift test` | **退出码 1**，`passed=3 started=4`，1 次 `Fatal error` | `swift test > /tmp/baseline-test.log 2>&1; echo $?` |
| 用例总数（源码计数） | 135 个 `func test` / 23 文件 | `grep -c "func test" Tests/**/*.swift` |
| `scripts/tests` | OK，11 tests（Python 3.9.6） | `python3 -m unittest discover -s scripts/tests` |
| 一次 `save()`（12 张 1600×1200） | **667.8ms 主线程** | 审计探针 P-12 |
| 启动 `load()`（8 张 2000×1500） | **605.8ms 主线程** | 审计探针 P-14 |
| `filteredEntries`（500 条 ×1KB + 搜索词） | **14.07ms/次** | 审计探针 P-20 |
| Gatekeeper | `spctl -a -t execute` → rejected（ad-hoc，无 entitlements） | 见审计 06 附 6.2(3) |

## 执行顺序（按价值，见 AGENT_BACKLOG.md 的分数）

第一批（S1，数据/信任/闸）：R-01 调试开关与日志位置 → R-02 损坏存档保护 → R-03 菜单无确认清空 → R-04 Web URL 误判 → R-05 来源 App 丢失 → R-06 反馈载荷含原文。
第二批（性能，实测驱动）：R-07 PNG 字节缓存 + 保存去抖 → R-08 图片指纹去绘制 → R-09 派生列表缓存 → R-10 预览文案先截断 → R-11 预测改事件驱动。
第三批（契约与可观测）：R-12 README/安装说明与行为对齐 → R-13 Info.plist 用途描述 + 授权失败可见 → R-14 死代码清理 → R-15 构建脚本与版本单一来源。
第四批（UI 视觉审计与修复）：U-01..U-0n，方法见 `AGENT_UI_AUDIT.md`（离屏渲染真实视图取像素，不依赖屏幕录制授权）。
第五批（矩阵新维度补审计）：边界/错误/内存/兼容/可访问性/国际化/可观测性/类型/迁移/回滚 逐格填平，`待审` 必须归零。

## 已完成（每项 = 提交号 + 验证方式）

| 项 | 提交 | 验证结果 |
|---|---|---|
| R-01 调试日志门控 + 移出 /tmp（顺带恢复测试闸） | `cb8db30` | `swift test` 退出码 0，**Executed 135→146→176** 用例全绿；`/tmp` 两个日志不再新增；`DebugLoggingTests` 7 条守卫 |
| R-02 存档损坏恢复 + 滚动备份 + 原件保全 | `0792e6b` | 4 条 `HistoryPersistenceRecoveryTests`；变异检查：去掉修复即报 "P-06 修复验证：图片文件不得被连带删除" |
| R-03/R-04/R-05 菜单确认、Web URL 误判、来源 App 归因 | `cc0c2df` | 3 组新测试；各自变异回旧实现即复现缺陷 |
| R-06 反馈不再存正文 + 级联清理 + 导出失败可见 | `0792e6b` | `FeedbackStorageHygieneTests` 7 条；实测用户 plist 该键 66,716,424 字节会被收窄 |
| R-48 推荐排序确定性 | `f17fc86`/`f8ce4dd` | `RecommendationDeterminismTests` 4 条；两处变异各自可复现地变红 |
| R-07/R-09/R-10 主线程热点（保存/派生列表/预览文案） | `f8ce4dd` | `PerfBudgetTests`：667.8→5.2ms、14.07→0.00ms/次、45.8→0.02ms |
| R-11/R-17/R-18/R-19/R-21 事件驱动预测 + 语义收敛 | `cb3a69b` | `PredictionSchedulingTests`（含代际丢弃）；静置不再 2s 轮询 |
| R-22/R-40/R-41/R-42/R-43 上限、拖选表、视频错误态、观察者释放、菜单脱敏 | `50e5a4e` | `DisplayPrivacyAndCapsTests` 等；离屏帧复验 |
| 第四批 · 视觉审计链路与 3 个真实缺陷 | `95b4301` | 离屏捕获 54 帧；修：设置侧栏图标隐形、破坏性按钮重复、5 处信息文字 `.tertiary`（暗色 2.2:1 → 5.79:1，亮色 1.89 → 3.98） |
| R-13 自动粘贴失败可见 + 存档恢复提示上屏 | `654a787` | `PasteFailureVisibilityTests` 7 条；变异（把上报改成空函数）⇒ 以正确原因变红；离屏帧确认横幅不破坏布局 |
| R-12/R-15/R-34 README 三条虚承诺、Info.plist 模板化、DMG 新鲜度与校验 | `1d442f5`,`fd59dbb` | `make dmg` 全链路跑通：通用二进制 + 16 键 Info.plist（含 `NSAppleEventsUsageDescription`）+ `.sha256`；挂载 DMG 复核内部产物；`scripts/tests` 17 条（新增 6 条，含"缺键必须构建失败"与"mtime 未变必须拒发"，两条都做过变异验证） |
| R-23 OCR 像素解码移出主线程 + R-08 残留的图片比较成本 | `4324441` | 实测 `add(3000x2000)` 主线程 94ms → 0.04~0.77ms；冷 `==` 4000x3000 217ms → 148ms（同字节重复 0.17ms）；`PerfBudgetTests` 那条**恒绿假守卫**（计时对象根本没算指纹）已重写 |

当前基线（复跑命令见下方恢复指令；本轮结束时的最终复跑见 AGENT_FINAL_REPORT.md）：

| 指标 | 现在 |
|---|---|
| `swift build`（清空 .build 后干净重建） | OK，**0 告警** |
| `swift test` | 退出码 0，**Executed 229 tests, 1 test skipped, 0 failures**（2026-10-09 在新路径复跑核实；现取方法：`swift test > /tmp/test.log 2>&1; rc=$?; grep -E 'Executed [0-9]+ tests' /tmp/test.log | tail -1`（`tail -1` 单独用会取到 swift-testing 那行 `Test run with 0 tests`，看着像"一条都没跑"），别信这里写的数字）；那个 skip 是离屏视觉套件，按设计只在设了 `CLIPBOARD_HISTORY_UI_SHOTS` 时跑 |
| `python3 -m unittest discover -s scripts/tests` | OK，**18 tests**（必须在**仓库根目录**跑；`ClipboardHistory/` 下没有 `scripts/tests`，在那里跑以退出码 1 报 `Start directory is not importable`） |
| `make build` / `make bundle` / `make dmg` | 全部退出码 0；DMG 挂载后复核：通用二进制（x86_64 + arm64）、`codesign --verify --deep --strict` 通过、Info.plist 16 键含 `NSAppleEventsUsageDescription`、`.sha256` 可校验且改一个字节就失败 |
| 离屏视觉捕获 | 64 帧（32 夹具 × 亮/暗；第二轮末加了菜单栏面板的三个状态），未绘制比例全部 <95%，同代码连拍 sha 完全一致 |
| 审计矩阵 | 190/190 格全部判定完毕，**待审 0** |
| Backlog | 54 行，**待办 0**（其余为 已完成(提交号) / 记录不改(理由)） |
| 工作区 | `git status` 干净；**已推送并核对，Latest = v1.4.7**（v1.4.6 保留；CI 在发布提交与之后的账本提交上都全绿）。当日一度因 GitHub 不可达而落后，网络恢复后推上去了，并用 API 核对：远端 `main` == 本地 `main`、`v1.4.6→e4ac62b`、`v1.4.7→5190ad1`，两个 Release 附件的 sha256 与本地 `.dmg.sha256` 逐字相同。核对命令写在文末"恢复指令"第 6 条（别信这里写的 SHA，跑一遍现取） |

本轮新发现（原审计未覆盖，已进 backlog）：
- **R-49** `ClipboardIntake` 各读取方法的 `from:` 默认 `.general` ⇒ 注入的 pasteboard 被静默忽略，测试会读到**用户真实剪贴板内容**。已修（R-05 同批），断言改成"只报类型不报正文"。
- **R-48** 推荐排序跨启动不稳定。已修。
- **R-50** `HistoryStoreTests` 排序断言依赖前台 App。已修。
- **R-51** 图片去重仍要"同尺寸不同内容"时两侧各解一帧（148ms/次，主线程）。已比旧实现快 2.9×，残留部分记为待办：把 64px 采样值随条目一起持久化即可彻底摘掉。
- **守卫本身的失效模式**（方法级发现）：`PerfBudgetTests` 的指纹用例计时的是"构造"而不是"比较"，惰性缓存令它永远 0.00ms —— 已重写，并把"每类比较用各自第一次被比较的对象"写进注释。同类问题也出现在视觉捕获上（4 类假帧，见 `AGENT_UI_AUDIT.md`）。
- **实测确认 R-06 的现实规模**：`~/Library/Preferences/com.clipboardhistory.app.plist` = 66,724,574 字节，其中反馈键 66,716,424 字节。

## 恢复指令（若上下文丢失，从这里续做）

## 第二轮审计（2026-10-09）· 修复进度

审计交付在仓库外：`/Users/wangziyi/Documents/时间剪史_审计_2026-10-09_第二轮/`
（`00-README` / `01-增量台账`（15 模块 × 9 维度 = 135 格全覆盖）/ `02-新缺陷与回归` / `03-UI与HIG视觉审查` / `04-验证附录` + `frames/` + `probes/`），
被审对象是 HEAD `81bce8d`（v1.4.7，工作区干净）。它的结论：修复轮质量高于平均，但自己留下 4 条新缺陷（N-1…N-4，其中 2 条是"为修 A 引入 B"），
UI 侧暗色与 60fps 达标、**键盘可达性实测不达标**、亮色 chrome 不可见、拖拽能力为零。

本轮已完成（每条一个提交；提交后 `swift build` 0 告警、`swift test` **229 例 / 1 skip / 0 失败**）：

| 审计项 | 提交 | 做了什么 |
|---|---|---|
| N-1（S2 崩溃） | `876c015` | `intelligenceByEntryID` 两个重载不再用 `Dictionary(uniqueKeysWithValues:)`（重复键 = `fatalError`），改为保留首条 |
| N-2（S2 数据丢失） | `bacde44` | `HistoryStore.init` 不再写盘，首次写回推迟到 `startMonitoring`（守卫已放行）；3 条原"init 即持久化"的用例保留全部断言并新增"init 阶段零写入" |
| N-3（S4） | `fb37c4b` | `load()` 开头复位 `isArchiveFromNewerVersion` |
| N-4（S4 假绿） | `a56f2e5` | `guard … else { return }` 换成钉住两侧的断言；**顺带暴露一个真行为**：只含非文件 `NSURL` 的剪贴板当前不被记录（`readFileURLs` 限定 `.urlReadingFileURLsOnly`，是 P-15 的修法） |

本轮**还欠**（明细见 `AGENT_BACKLOG.md` 的 R2-* 条目，按价值排序）：

1. **N-1 的端到端守卫还没写** —— 审计明确要求"走 `HistoryStore`、不走 engine"的用例（存档含同 id 两条 ⇒ 预测刷新不崩且只出一条）。
   现在只有实现改动，`RecommendationBoundaryTests:96-103` 仍然绕过 adapter ⇒ **这条修复还没有一条会红的测试**，
   必须补上并用变异对照（把实现改回 `uniqueKeysWithValues`）证明它真的会红。这是本轮第一优先。
2. B-1…B-6（保存仍重写全部图片文件、来源 App 不落盘、`sizeDescription` 全串计数、图片无像素上限、过期项文档、粘贴前不复核目标 App）。
3. UI 批次 A/B/C：亮色 chrome 9 处 `.white.opacity`、`"questionable"` 非法符号、破坏性确认的默认按钮、减少动态未门控、
   **键盘焦点链**（审计实测 14 次 Tab 全落在同一个 `NSTextView`）、拖拽缺失。
4. 一个待决策的产品问题：只含 `public.url` 的剪贴板要不要记成文本条目（现在是丢弃；浏览器复制链接同时带字符串，所以日常不受影响）。

子代理调研结论（只读，已采纳）：**不要**把自绘列表整体换成 `List(selection:)` —— `.draggable` 是 macOS 13+ 而本项目下限是 macOS 12，
`List` 的系统 chrome 会改掉 4 个 `sidebar-*` 帧的像素，还会丢掉 `dragSelectRange` 的锚点语义（只有 store 级测试钉着）。
改走最小方案：恢复搜索框焦点环、行 `focusable` + `onMoveCommand` 方向键映射到既有 store 动作、行上暴露 `isSelected` 语义；
拖出条目用 `onDrag { NSItemProvider }`（macOS 10.15+ 可用），不是 `.draggable`。

### 第二轮进度快照（本节为最新状态，上面那份"还欠"清单写于开工时）

已完成并推送（每条一个提交，全部有会红的测试；`swift build` 0 告警、`swift test` **265 例 / 5 skip / 0 失败**、`python3 -m unittest discover -s scripts/tests` **25 例 OK**）：

| 审计项 | 提交 | 证据 |
|---|---|---|
| N-1 端到端守卫（R2-01） | `ca12531` | 变异对照：改回 `uniqueKeysWithValues` ⇒ 测试进程 `Fatal error: Duplicate values for key`，退出码 1；随后按 sha 逐字节还原 |
| R2-09 非法符号 / 菜单空态 / spinner 兜底 | `1214526` | 新增 `SystemSymbolValidityTests`：扫出 **24 个符号名字面量 / 22 个不同名**，全部可解析；识别器用含 `questionable` 的合成源自证；数量下限 18 由 grep 独立得出 |
| R2-03 亮色 chrome（9 处） | `6a2c040` | `scripts/frame_audit.py`：亮色 pill 的 chrome 从 245–250（背景 247，≤3 级差 = 不可见）变成 202–207（43 级差）；暗色 81→64（背景 34，仍高 30 级） |
| R2-06 破坏性确认默认按钮 | `a841337` | `DestructiveAlertLayoutTests` 2 条钉住按钮顺序/角色/快捷键与 `runModal` 返回值映射 |
| R2-10 pill 减少动态门控 | `2438aa6` | `FilterPillMotionTests` 3 条（含接线守卫：视图里不许再出现写死的 `.spring(response: 0.38`） |
| R2-11 有界字符计数 | `8cfdfe5` | 2.4MB 文本 `sizeDescription` 实测 **0.87–1.11ms**（旧实现基线 5.5ms），性能上界从 20ms 收回 **5ms** |
| R2-04 保存不再重写全部图片 | `9ac4661` | `ImageWriteAmortizationTests` 4 条，判据是 inode（原子写必换 inode）+ "history.json 必须每次换 inode" 的阳性对照；变异对照：去掉跳过 ⇒ 2 条红 |
| R2-07 来源 App 落盘（D-016） | `d8d11f4` | 4 条用例（文本/图片/文件往返、手写旧存档仍可读且读成 nil、隐私文案披露）；变异对照：四处写 nil ⇒ 2 条红 |
| R2-02 键盘可达性（部分） | `d4edf1f` | 在屏探针实测：真实 Tab 按键现在能到搜索框（`NSTextView(fieldEditor)`）；改动前 14 次 Tab 全停在详情的 `NSTextView` |

顺手修掉的一个**测试环境依赖**（`fe4ca27`）：`InstanceGuardTests` 有一条断言"本机没有产品 bundle id 的其他进程"，
用户一打开 `/Applications/时间剪史.app` 它就红（本轮实测 pid 75412）—— 那是在断言机器状态而不是代码行为。
现在改成按测试进程自己的 bundle id 判定，本机因为 xctest 不是 GUI App 而 skip；**Finder 那个阳性对照单独成一条用例**，
否则一个 skip 会把它一起染成"没跑过"。

新工具：`scripts/frame_audit.py`（`diff` / `stats` / `band`，纯标准库解 PNG，自带 7 条单测；它自己抓到一个真 bug ——
亮度用截断而非四舍五入会把纯白算成 254）。捕获 harness 也修了一处证据污染源：**闪烁的插入点**曾让同一份代码连拍两次
有 30/58 帧不同（最大通道差 251），现在捕获前交出第一响应者并把插入点设为透明，噪声降到 16/58 且只剩 `content-*`/`detail-*`。

**验证等级要分清**（本轮明确记为未验证的）：Tab 能否走到列表行 —— 本机 `AppleKeyboardUIMode` 读出来是 `-1`（缺省，
即「完全键盘访问」关闭），此时 macOS 的 Tab 只在文本框与列表之间走，`.focusable()` 的自绘视图根本不进环；
所以"键盘用户能用方向键浏览列表"目前只有**纯函数单测 + 接线守卫**，没有在屏证据，需要人工开一次该开关后用
`CLIPBOARD_HISTORY_UI_INTERACTION=1 swift test --filter UIInteractionProbeTests` 复测。
同理未验证：`NSAlert` 的真实按键行为（Return/Escape）、真实拖放（拖出已实现并有单测，但需要鼠标拖拽与接收方 App，离屏测不了）。
菜单栏面板视觉在 D-019 加了注入接缝之后**仍然** NOT-RUN，理由更新为"离屏 `cacheDisplay` 不画菜单表面材质，试拍帧 97.7% 未绘制，被捕获闸门判为无效证据"。

### 第二轮进度快照 2（收尾时；上面那张表仍有效，这里是增量）

| 审计项 | 提交 | 证据 |
|---|---|---|
| R2-05 拖出条目 | `d463ef9` | 7 条用例（含把 PNG 字节从 provider 里读回来比对）；多文件条目刻意不给拖拽（半截动作比没有更糟）；真机拖放未验证 |
| R2-08 图片 4096px 上限 | `1183f9f` | D-017；端到端采集用例断言入库 ≤4096 且字节数严格变小；4K（3840）逐字节不动；变异对照红过并还原 |
| R2-12 粘贴前复核目标 App | `d218803` | 6 条真值表 + "复核必须在注入之前"的顺序守卫；变异对照（延时直接注入）红过并还原 |
| R2-13 行时间戳 11pt | `d218803` | 帧差异 3.3–13.1% vs 同代码对照 0.12–0.38%；肉眼核对未裁切；**差异里混着夹具时钟字符串变化（R2-19）** |

当前判据：`swift build` 0 告警 · `swift test` **301 例 / 5 skip / 0 失败** · `python3 -m unittest discover -s scripts/tests` **25 例 OK** ·
远端 `main` 与本地一致 · CI 最近三次（`d0b2416`/`a22d394`/`268ccaa`）全 success；再往后的以 `gh run list --limit 3` 现取。
本轮之后又加了：菜单内容直测 + "还在算/确实没有"的区分（D-021）、拖入文件入库（D-022）。
本轮 CI 一共红过五次，根因全都是同一类：**把本机测出来的数字写进断言**。分别是
`@MainActor` 测试类的 setUp 写隔离属性（6.1.2 更严）、把本机 2× 渲染倍率当契约、
"热比较快于冷比较"这条在 2 核 runner 上没有分辨力的计时判据、搜索词代价取均值，
以及"离屏列表能数出 5 行"（runner 只数出 4 行，`e8a59e4` 改成量整列墨水）。
五次都是**本地绿、远端红**，所以"本机全绿"在本项目里从来不算交付证据。
第四次的修法顺手否证了我自己给它的修法：先加的 load1/核数闸门，实测 CI 是 `load1=11.8 活跃核=3`（比值 3.9），
会把 5 条性能守卫在唯一的自动化环境里全部变成 skip —— 改用"样本自身跨度 > 该条阈值才 skip"，阈值一个没动（D-023）。

**CI 红过两次，都是同一类错**（`1183f9f`/`d218803`）：`testPixelDimensionsReadsARealPNG` 把本机的 2× 渲染倍率当成了契约，
CI runner 是 1×，"编码后严格大于点尺寸"立刻红。已在 `d160b52` 改成与倍率无关的不变量（与 `NSImage` 自己的位图表示一致）。
教训记在 `~/.qoder-cn/memory/feedback-probe-and-assertion-hygiene.md`：**本机实测的数字进断言前，先问别的机器上它还是不是这个数**。

仍未做（明细与理由在 `AGENT_BACKLOG.md` 的 R2-* 与"进度快照 3"）：R2-02 的在屏复测（需人工开「完全键盘访问」）、
设置侧栏符号风格统一（离屏证据不可信，标 NOT-RUN）、菜单栏面板视觉（等 D-019 的接缝走在屏探针）、
多文件条目的拖出（需要 NSView 级 dragging session）。
本轮**证伪**的一条审计结论：R2-15 说 AI 脚手架"零产品调用"，实际 `AIPrivacyScope`/`AIPrivacySensitivity` 被 4 个产品文件使用，
整体搬走编译失败；最终按编译器给的事实拆成"词汇表 target + 草案 target"（D-020）。

### 第二轮进度快照 3（同夜最后两件：性能判据的自我推翻 + 菜单栏面板补拍）

- CI 第四次红（搜索词代价均值 69.0ms vs 上界 60ms）后我先加的 load1 闸门**是错的**：CI 实测 `load1=11.8/3 核`，
  比值 3.9 ⇒ 5 条性能守卫会在唯一的自动化环境里永久 skip。已改成"N 次同操作采样取最快 + 跨度 > 该条阈值才 skip"，
  阈值一个没动，双向变异对照都实跑（D-023）。**已核**：`c952905` 的 CI 上 runner 是 `load1=27.7/3 核`，
  8 条 `PERF[...]` 全部下结论、零 skip。
- 菜单栏面板从"从未画出一帧"变成 6 帧（有推荐 / 还在整理 / 暂无推荐 × 亮暗，58 → 64）：
  以前那句"离屏拍不到"只对 macOS 12 的 NSMenu 成立，13+ 的 `MenuBarExtra` body 是普通 View（D-024）。
  第一次看画面就抓到"来源 App 在一行里说两遍"，`16d658d` 修掉。
- **已发布 v1.4.8**（2026-10-10，用户授权）：轻量 tag `v1.4.8` 打在发布准备提交 `e4aee3c`，线上 Latest 已切换。
  产物级验证与"仍欠运行时冒烟"都记在 D-031 与 `AGENT_FINAL_REPORT.md` §11。
- 当前判据（发布提交上实测）：`swift build` 0 告警 · `swift test` **328 例 / 9 skip / 0 失败** ·
  发布脚本测试 **30 例 OK**（`python3 -m unittest discover -s scripts/tests`）·
  68 帧同代码连拍两次 sha 完全一致。
  **已确认**：`14a37a0`（录制器修复）与账本提交在 CI 上 success（run 37927639110），
  远端 `main` 与本地 HEAD 一致（`git ls-remote origin refs/heads/main`，与 API 是两条独立通道）。
  中途 12:05–12:11 GitHub 两条通道同时不可达过一次（`git ls-remote` 端口 22 被关 + `gh` API EOF），
  那段时间里"推上去了吗"无法定性 —— 记下来是因为下一次很容易把它当成"没推上去"而重推。
- 矩阵里 08-08 / 13-08 两块补了测试：工具栏"猜出来再删"的判断（9 条正反用例，D-026）、
  快捷键录制器的退出路径（6 条，D-027）—— 后者当场抓到一条真缺陷（录完仍显示"请输入快捷键"，`14a37a0` 修）。
  13-08 仍欠"设置页交互"与"生命周期回调"两块：要先加接缝才好测，本轮不硬凑，记在 backlog 快照 11。
- **启动闪退回归（D-029，S1）**：D-019 给 `AppDelegate` 加的显式 init 让 ObjC 的 `-init`
  变成 trap 桩，而 SwiftUI 的 `@NSApplicationDelegateAdaptor` 正是走那条 —— 327 个用例全绿、包一打开就死。
  已修（`override convenience init()`）+ 两条守卫（运行时走元类型 / 源码扫描），包重打为 `1.4.7-fix1` 并在
  二进制层核对桩已消失。缺口记成 R2-21：CI 里没有「能不能启动」这一关。
- 用户提出"收藏/复制要滑到最右边"⇒ 行内直接可操作（D-028，`1395425`）：双击行复制、行首星标就地收藏。
  星标从 `.clear` 指示器变成真控件，对比度量化到 ≥3:1；**这次是在屏合成点击真点验证的**
  （单击选中 / 双击恰好一次复制 / 点星标不动选中）。遗留 R2-20：收藏切换会把多选收成一条。
- 审计 1.9 的"侧栏图标看不见"从推断升级为测量（D-025）：产品里 0.0000、固定色 0.175–0.402、复刻 List 行里
  `.primary` 正常 ⇒ 离屏语义色伪影，**产品一字未改**；真机那一列仍未验收（在屏捕获要付权限框或废弃 API 的代价）。

## 恢复指令（若上下文丢失，从这里续做）

1. `git log --oneline` 与 `git diff 8007b19..HEAD --stat` 看清已完成什么。
2. 跑 `cd ClipboardHistory && swift build && swift test`（**必须看退出码与 `Executed N tests`，不要用管道**）。
2b. 视觉帧：`cd ClipboardHistory && CLIPBOARD_HISTORY_UI_SHOTS=/tmp/shots swift test --filter UICaptureTests`（改 UI 前后各拍一组同参数帧，见 AGENT_UI_AUDIT.md 的复验规则）。
3. 读 `AGENT_BACKLOG.md` 找第一条未关闭的高/中价值项；`AGENT_DECISIONS.md` 读最近 5 条决定；`AGENT_UI_AUDIT.md` 看视觉项。
4. 外部参考：审计报告在仓库外 `/Users/wangziyi/Documents/时间剪史_审计_2026-10-08/`（145 条记录 + 21 条探针源码 `probes/`，探针断言的是"缺陷存在"，接入仓库时需逐条翻转）。
5. 停止条件见本文件开头与 AGENT_BACKLOG.md 末尾的"发布前检查单"。
6. 远端一致性核对（本轮遗留项已做完，这段留作随时复查的入口）：
   ```bash
   cd /Users/wangziyi/Codex_Project0
   git log --oneline origin/main..main                  # 空 = 没有未推送的提交
   git push origin main                                 # 当日 GitHub 只在这一刻通：443/22 其余时间被断
   gh api repos/mnmc5h5ntg-wq/ClipboardHistory/branches/main --jq '.commit.sha'
   for t in v1.4.6 v1.4.7; do gh api "repos/mnmc5h5ntg-wq/ClipboardHistory/git/refs/tags/$t" --jq '.object.sha + " " + .ref'; done
   gh release view v1.4.7 --json assets --jq '.assets[] | .name + " " + .digest'
   ```
   实测结果（2026-10-09 04:52 CST）：远端 `main` 与本地相同，`refs/tags/v1.4.6 = e4ac62b`、`v1.4.7 = 5190ad1`，
   与本地 `git rev-list -n1 <tag>` 一致；两个 Release 附件的 `digest` 与本地 `时间剪史_v1.4.x.dmg.sha256` 逐字相同。
   **注意 `git ls-remote` 走 22 端口、`gh` 走 443 API：同一时刻前者可能失败而后者成功**，别因为一条失败就判定"没推上去"。
   另外用户从新路径确认过项目能打开之后，旧路径的兼容符号链接 `~/Documents/Codex_Project0` 可以直接删除。

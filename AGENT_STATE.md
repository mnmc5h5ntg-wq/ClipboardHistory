# AGENT_STATE · 当前工作状态（自主修复引擎）

最后更新：2026-10-13 12:3x（本地）

## 当前状态（2026-10-13 · 视觉与动效长跑 R1）

用户新开一轮长跑：把视觉与动效做到"Apple 原生、流畅、华丽但克制、细节相当丰富"，
每轮出可编译代码 + 自评，**连续五轮 ≥90 且无 P0/P1 回归才停**；轮次现场记在
**`AGENT_VISUAL_ITERATION.md`**（设计令牌表 + 每轮已完成/未完成/风险/下一轮）。

- **R1 做完的事**：R0 审计数出的 6 种圆角 / 3 种发丝线 / 4 处投影 / 3 档悬停底色 / 4 处材质字面量
  全部收进新的 `Utilities/VisualTokens.swift`，并把"只有一个作者"做成 11 条会红的判据
  （出现字面量、令牌没人读、死表面、强度次序反转都打红）。顺带删掉两个死表面
  `GlassCircleButton`（连带三个永远只剩一种取值的参数）与 `HistoryRow`（注释的复用理由是假的），
  并把"正在加载预览…"从 12pt 接回自家规范的 13pt。决定见 **D-058**，视觉账见 **U-22**。
- **数字（本轮现场）**：`swift build` 0 warning；`swift test` **600 / 23 skipped / 0 failures**
  （HEAD 同口径 589 ⇒ 本轮 +11）；`scripts/tests` 72 passed；
  82 帧采齐、**28 帧有变化且逐帧归因**（最大通道差 1/2–8 的是描边与缩略图角，
  唯一的大差 124–127 是那句加载文案 12→13，bbox 86×12.5pt = 一行字；`glass-pill-*` 像素不变），
  基线 `FRAME_BASELINE_UPDATED=82` 与改动同提交、复跑 `CHANGED=0`；
  **10 支变异体 10/10 CAUGHT**（含一次"0 支有效"的自证修复：python3 注入的 `SDKROOT` 让每个变异体都编不过，
  分类器全判 `DID-NOT-RUN`，见 D-058）。
- **动效那一步本轮不算绿也不算红**：三臂交替（R1 → HEAD → R1）在同一台机器上给出三套不同的红集合，
  HEAD 那臂比 R1 更差 ⇒ 判据在测采样率而不是测动画。**没有为了绿去调阈值**；
  "把动效判据与采样率解耦"立项为下一轮主题（BACKLOG 快照第 6 条），它要带自己的变异对照。
- **自评**：80 / 100（<90 ⇒ 按规矩继续，不等确认）。扣分全部扣在同一事实上：本轮是地基
  （收口 + 减法 + 判据），可见的"华丽与细节丰富"还没增长 —— 按压态 / 焦点态 / 边缘高光 /
  内容类型层次 / 滚动层次都还没动。分数明细见 `AGENT_VISUAL_ITERATION.md` 的 R1 打分表。
- **未推送 / 未部署**：本轮改动提交后推送；**装到本机**按 D-057 那条默认动作做（几何变了，值得亲眼看一次）。

## 当前状态（2026-10-13 · 视觉迭代 R2：动效判据与采样率解耦）

- **本轮不碰外观**：82 帧 `CHANGED=0`（视觉完全惰性），改的全在 `MotionFilmstripTests` + CI 汇报行。
- **为什么先做这个**：R1 收尾时动效套件是红的，三臂交替（R1 全绿 → HEAD 两条红 → R1 另一条红）
  证明红来自尺子。"用绝对帧数表达判据，其实判的是采样率"（ab7a759 早就写下），
  而底座是"绿不表示验到了"时继续做九轮美化，等于写在沙子上。
- **改了什么**：要求帧数 = `min(3, floor(声明时长 / 实测采样间隔))`、地板 2 帧、切不出就报
  `clock-too-coarse`；取样锚点从预卷改到**触发那一帧**；"落定"从 `≤6 帧` 改成毫秒；
  新增前提检查"触发前后必须逐像素不同"；CI 结论行加 `MOTION_RESOLVE_SUMMARY judged=n/m`（自检 13→14 形状）。
- **修尺子修出来的假证据**：`MOTION_SUMMARY notice-banner=3` 原来被当成"横幅淡入量到了"。
  实测那一卷整窗逐帧差距 `[0.000, 0.222, 0.222, 0.067, 0.000 …]` —— 首尾相同、中段变了又回来，
  而模型里提示条一直在 ⇒ **离屏 `cacheDisplay` 抓不到落定之后的横幅**。
  现在如实报 `premise-not-visible`（本机 judged=2/3）。覆盖面退一步，可信度进一步。
- **数字**：605 tests / 23 skipped / 0 failures（R1 后 600，+5）；动效套件 18 条 0 failures / 3 skipped
  （每条带 not-run 原因）；**8 支变异 8/8 CAUGHT**（含前提恒真/恒假两支）；`scripts/tests` 全绿；产品代码零改动。
- **自评 85 / 100**（分数低在"界面上没有新细节"，换回来的是后面每一轮动效分数的可信度）。
- **下一轮（R3）**：排版与间距节奏 —— 10 档字号收成一族、空态两套统一、9pt 徽标复量对比度。

## 当前状态（2026-10-13 · 视觉迭代 R3：字号刻度与层级修正）

- **改了什么**：文本字号从 8 档收成 4 档（`meta 11 · row 12 · body 13 · title 14`）+ 8 个具名符号档；
  修掉侧栏"15 条记录"比标题还大一号的**层级倒置**、把 9pt 的"固定"徽标抬到 10 并写成全 App 下限；
  `body` 改为引用 `StatePresentation.messageFontSize`（不再抄数字）。
- **数字**：607 tests / 23 skipped / 0 failures（+2 条判据）；**20/82 帧变化并逐组归因**
  （`row-pinned-on` 只有已固定那一版变、`detail-*` 与 `glass-pill-*` 完全没变），基线已同提交更新；
  **5 支变异 5/5 CAUGHT**（第一轮 2 支 ESCAPED，据此修掉两条假守卫：按名字查消费者会被
  `controlHover` 这类前缀白拿；数值断言证明不了来源，13 就等于 13）；`scripts/tests` 全绿。
- **自评 88 / 100**（<90 ⇒ 继续）。R2 的 CI 已确认 success。
## 当前状态（2026-10-13 · 视觉迭代 R4：按压态）

- **改了什么**：新增 `Views/PressableStyle.swift`（`PressedStyle: ButtonStyle` + `PressableAppearance` 纯函数），
  9 处按钮接上"缩放 0.97 + 底色 0.12 / 0.12s"的按压反馈；整行类不缩放只加深底色；
  菜单栏两处刻意不接（系统菜单自己的高亮就是反馈，理由在代码旁边 + 白名单判据）；
  新增 `MotionCatalog.pressScale` 与 `VisualFill.pressed`，次序 `hover < pressed < selected` 有判据。
- **焦点那一半没做**：读码发现搜索框的 `focusRingType = .default` 早就恢复了（R2-02），再画就是两圈；
  剩下的缺口（筛选段/设置行的键盘焦点）要先量 `List` 行代理，单独一轮。
- **数字**：613 tests / 24 skipped / 0 failures（+6 条判据）；0 warning；**82 帧 `CHANGED=0`**；
  5 支变异 5/5 CAUGHT（第一版 1 支 ESCAPED：像素断言把缩放与底色混在一起量，拆成分通道才打红）；
  `scripts/tests` 72 passed。
- **自评 90 / 100**（第一轮达到阈值线，但**这一分不敢给满**：按压态只有源码级与合成级证据）。
- **按压态的产物级证据仍缺**：真按下探针在 xctest 里 `送达=0`、`keyWindow=nil isActive=false`
  ⇒ SwiftUI Button 的按下跟踪要 key 窗口。已如实记为"源码已接、产物未量"，转人工批次 12.1–12.7。
- **已装到本机**（R1–R4 一起进去）：`install_local.sh --yes` 跑通 —— `INSTALL_RESULT=ok`、
  `INSTALL_SHA_MATCH=1`（staged 与 installed 都是 `ea29552ee41f0624…`）、新 pid 19048 的 exe
  逐字对上 `/Applications/时间剪史.app`、存档 92→92 条、运行时冒烟 `SMOKE_OK=1`；
  旧包留在 `~/Documents/Codex_Project0_backups/before-local-20261013-045123`。
  **请按批次 12 判手感**（尤其 12.1 按住收藏键、12.6 开减弱动态再来一遍）。

- **下一轮（R4）**：按压态与焦点态（全 App 现在只有 hover 一种反馈；`testSidebarListFocusRingAfterClick`
  那条已知红也在那一轮处理），并把间距节奏（padding 一族）一并收。


## 历史状态（2026-10-12 晚 · 动效补做批次）

- **HEAD**：`6fc8224`，工作树干净，全部已推送；CI 对最后一个代码提交 `155de63` 是绿的。
- **已交付到本机**（D-057）：`install_local.sh --yes` 跑通并正在运行新构建
  （pid 75839、exe 逐字对上 `/Applications/时间剪史.app`、`INSTALL_SHA_MATCH=1`、存档 92→92 条，
  旧包留在 `~/Documents/Codex_Project0_backups/before-motion-batch9/`）。
  注意版本号字符串仍是 **1.4.8**（`Makefile VERSION` 要到发版时才抬，CHANGELOG 里这批挂在 `[Unreleased]`）——
  所以"看版本号判断装没装上"是无效的，要按上面的 exe/sha/pid 认。
- **这一批做完的事**：用户反馈"新版本没加什么动画"→ 重读报告找回四条被我判错的条目
  （QuickPick 原生行动画 / 收藏固定的 `replace`+`bounce` 叠加 / M9 骨架扫光 / M8 落点光晕），
  两条主动撤下并写明理由（`reduce-transparency` 门、"跳转才动"的滚动策略）。
  决定见 **D-056**，视觉账见 **U-21**，报告见 **§20**，人工验收见手工清单**批次 9**。
- **数字**：588 tests / 22 skipped / 0 failures；两个 triple 各 0 warning；
  82 帧 `CHANGED=0`（2 帧是这次刻意改的加载态，基线已随包更新）；26 条新判据（22 纯值/守卫 + 4 像素）；本机像素套件 13 条全绿；
  16 支变异 15 支红在该红的那条 + 1 支故意逃逸（据此删了一条死守卫）。
  像素证据：QuickPick 行动画 开 11 帧 / 关 1 帧、产品形状（插完行紧接着写选中）11 帧 vs 1 帧 —— 这两条**带前提**：`NSTableView` 只在激活的 App 里跑行动画，裸测试进程拿不到激活态时判据自己报 `MOTION_NOT_RUN=app-not-active` 并 skip（本机当前就是这个状态；CI 那台 runner 拿到了：3 帧 vs 1 帧）；骨架扫 23 对在变 / 减弱动态 0 对。
  CI 的动效那一步补了两行固定输出（各条读数 + 红用例名字，由 motion/failing_test_names 形状钉住）；三条新像素判据在 runner 看不见位移时改报 MOTION_NOT_RUN + skip，而不是红。
- **两条已知红（都不是这批造成的，也都记着）**：帧间隔判据 `p95=28.68ms` 超 20ms
  （同一次运行里"曲线全关"那臂 27.67ms ⇒ 环境）；
  `testSidebarListFocusRingAfterClick` 找不到行代理（在整轮动效之前的提交上同样红，
  现场是一行变成两个半宽 `KeyViewProxy`，疑无障碍结构退化，BACKLOG 快照 33 第 5 条）。
- **下一步该做的**：装包做批次 9 的 8 条人工验收（尤其 9.4 符号动效、9.5 扫光观感）；
  机器安静时复测帧间隔；单独一轮查行代理分裂。

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

### 第二轮进度快照 4（2026-10-10 夜：issue #13 右键菜单汉化，D-032）

- 用户点名修 #13。落地的不是"改文案"，是**把编辑态右键的所有权拿回来**：
  实测共享 field editor 才是右键的接收者，`hitTest` 让位 / 给 `editor.menu` 赋值 / 就地改 `menu(for:)` 三条
  都被数字推翻（第三位的证据是两次调用 `!==`，改完再问又是满的、`allowsContextMenuPlugIns` 回到 `true`）。
  最终用 `addLocalMonitorForEvents` 在派发前截走，认领判据是"field editor 沿 superview 往上属于 `ChineseMenuTextField`"。
- 菜单交付：搜索框 `撤销/重做/剪切/复制/粘贴/全选`、只读详情区 `复制/全选/查找…`；
  `NSWindow.allowsAutomaticWindowTabbing = false` 建窗前设；每次弹出前 `sanitize`（常驻 `MenuSanitizer` 代理，
  因 `NSMenu.delegate` 是 weak）。
- **测量上的一条硬限制**：`popUpContextMenu` 模态且 `didBeginTracking` 里 `cancelTrackingWithoutAnimation()`
  叫它不返回（8 秒看门狗 exit） ⇒ "屏幕上真弹出来的样子"不进仓库判据，改成
  `docs/MANUAL_TEST_v1.4.8_issue13.md` 人眼核对（记成 R2-22；顺带 R2-23：将来新增裸 `TextField` 会绕开拦截器）。
- 在屏探针 `testRightClickMenusAppKitWouldShowAreChinese` 带反面对照（搜索框没在编辑时 `owns == false`）
  和 20 秒看门狗；变异对照 5 组逐一点亮，其中"让拦截不吞事件"那一组表现为**挂住后看门狗报红**，
  这正是它有效的方式。
- 当前判据：`swift build` 0 告警 · `swift test` **339 例 / 10 skip / 0 失败** · 在屏右键探针绿。
  10 条 skip 已逐条核对，全是 env 门控的在屏探针（含这条新增的）。
- CI 定性（现取，别信这里写的数）：`gh run list --branch main --limit 1` —— 本次两个提交的那一跑是
  `success`（`gh run view <id> --json conclusion,jobs`）。
- **#13 已经关闭，但不是我主动关的**：账本提交 `eb7c767` 的标题里有 "…to fix #13…"，
  GitHub 把 `fix #13` 当闭合关键字自动关了它（timeline 里 `closed` 事件带的 commit_id 就是它）。
  记下来有两个原因：① 上一轮的口径是"没碰右键菜单所以不顺手关掉它"，这次是修完且 CI 绿才关，结论没错但**动作不是我做的**；
  ② 提交消息里出现 `#<编号>` 会引用、`fix/close/resolve #<编号>` 会**真的改外部状态** —— 写提交标题时要有这个意识。

### 第三轮进度快照（2026-10-10 夜，D-033）

- 输入：仓库外 `~/Documents/时间剪史_审计_2026-10-10_第三轮`，8 条新缺陷 D-1…D-8 全部处理完。
  用户点名的两处按指定做：**D-1 用修法③**（`List(selection:)` + 把手拖出 + `EntryDragGate`），
  **D-3 给「通用」补两项**（暂停记录 / OCR 可关，取 §5 的 F1/F4）。
- 推翻了自己上一轮的决定（R2-02 说不换 List）——理由逐条对账写在 D-033，不留"看起来反复"的账。
- **测量边界**：换成系统表格后合成鼠标事件送不进去（`clickedRow` 恒 -1），
  点选/双击/拖选三条行为判据转人工（手工清单 `docs/MANUAL_TEST_v1.4.9_round3.md`），
  结构判据留在常规套件；这条缺口记成 R3-D9，别把它当成"已经自动化了"。
- 新离屏伪影一条：`List` 选中高亮在帧里是整块黑，判据是黑块跟随选中集合 ⇒ 不据此判产品（见 AGENT_UI_AUDIT.md）。
- 当前判据（现取，别信这里写的数）：`cd ClipboardHistory && swift build && swift test`
  → 本轮实测 0 告警、355 例 / 10 skip / 0 失败；帧：`CLIPBOARD_HISTORY_UI_SHOTS=/tmp/shots swift test --filter UICaptureTests`
  → 68 帧、同代码连拍两次聚合 sha 相同。
- **D-034 更正（同一夜，用户真机反馈）**：修法③原本"拖出只从行首把手发起、行体留给拖选"被实测否掉 ——
  `List` 会把行内任何一处 `.onDrag` 提升成整行拖拽源，于是按下就开会话、容器上的拖选手势拿不到事件。
  取舍（用户定）：**保留整行拖出、删掉拖选**，`dragSelectRange` 动作 + 行位置表 + 拖选探针全部清掉，
  不留半套死码；选中靠单击 / shift / ⌘ / 方向键。改动 0 帧变化，判据换成
  "拖出入口恰好一处（在行上）+ 拖选残留必须为空 + 真值表"，变异对照三组点亮。
  教训：**源码扫描钉得住写法，钉不住 AppKit 怎么处理这个写法**；"作用域/归属"类断言要有一条落到真实容器上的判据。

- **D-035（同一夜，用户截图反馈）**：图片文件条目在列表里没有预览 —— 根因是 `.file` 的 thumbnail 只来自剪贴板顺带给的图像数据，从 Finder 复制时通常没有。改成 `add` 后在后台解一张 ≤256px 缩略图写回并落盘，启动时回填老历史；夹具补 `row-file-thumb` 亮暗两帧（68→70）。判据与变异见 D-035。

- **D-036（同一夜，用户真机反馈：点选有延迟）**：这条与上两条不同 —— 上两条是闸门放过真缺陷，这条是**我为了迁就一条不代表真实容器的离屏探针，主动改坏了产品交互**。D-1 之后行内没有兄弟手势，离屏孤立宿主里 `simultaneousGesture(TapGesture(count:2))` 收不到第二击，我就换成 `.onTapGesture(count:2)`，并写了一句没测过的注释"单击选中仍然立刻生效"。实际 `count:2` 的识别器要等一个双击间隔才确定"这只是单击"，而新 `List` 的选中正走这条路 ⇒ 高亮延迟。现在改回 `simultaneousGesture`。判据只剩源层反向守卫（行上出现 `.onTapGesture(count: 2)` 即红），"点选无延迟 / 双击仍可复制"转人工清单 §1 的 1.1 / 1.5（具名）。**规矩：为了让自动化判据点亮而改产品交互之前，先证明那个夹具代表真实容器；不代表就只能改判据或转人工。** 判据：0 告警 · 362 例 / 10 skip / 0 失败 · 变异 1 组点亮 · 帧 0/70 变化。
  **交付形态**：本机正在跑 `make bundle VERSION=1.4.8-fix4` 的产物（仓库根 `时间剪史.app`，universal，
  ad-hoc 签名）；"点选无延迟 / 双击仍可复制"两条要由用户在真机确认（清单 §1.1 / §1.5），我测不到。

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

- **D-037（同一夜，CI 侧）**：报告型步骤第三次"红了但没有数字"，根因换到了汇报行自己身上
  （runner 的 XCTest 打单数 `Executed 1 test`，抽取用的 `grep 'Executed [0-9]+ tests'` 失手 ⇒ 非零 ⇒
  `bash -e`+`pipefail` 中止 ⇒ 结论行没打、"没跑完"分支永远走不到）。修法：抽取行全部 `|| true` + 正则允许单数；
  新增 `scripts/tests/test_ci_report_selftest.py`（抽 ci.yml 原文、喂日志形状变体，随 CI discovery 真执行，
  变异对照已点亮）。**这条修法还不够**：run 38064293655 里离屏步骤打出来了（`captured frames: 70 executed: 1
  捕获失效帧: 2`），在屏步骤仍只有 `Killed: 9` —— 第二条中止点是 `kill "$killer"`（看门狗执行完 kill 自己退出了，
  `2>/dev/null` 不改退出码），一并兜底并给自检补两格。规矩：**`bash -e` 里"允许失败"的步骤，
  每一行都要问"它非零了脚本还活着吗"，包括清理动作与取值动作。**附带一条自检教训：测"看门狗挂死"时自己的夹具**不能用管道读子进程输出** ——
  孤儿 `sleep` 持有继承的 stdout，`communicate()` 等不到 EOF，实测把自己吊死在超时上；改写文件 + 独立会话按 pgid 收。

## 当前状态（2026-10-11，批次 2 收尾）

- 第三轮审计 §5 的 F-1 / F-4 / F-5 已落地并验证：全量 382 tests 0 失败、`make bundle` 0 warning、
  帧 76 张两次同 sha、4 条新守卫全部变异对照（其中一条最初是假守卫，加强后才红）。
- 下一批：批次 3 = U-4（详情排版 ≤68ch / 单行左对齐 meta / 搜索命中高亮）+ U-5（状态语言统一）。
  再往后：批次 4（U-2 拖拽图像、F-2 RTF/HTML 保真）、批次 5（F-3 快速选择浮层——**先 spike**、C-4 运行时启动冒烟）。
- 恢复要点：`cd ~/Codex_Project0/ClipboardHistory && swift test`；帧
  `CLIPBOARD_HISTORY_UI_SHOTS=/tmp/shots_x swift test --filter UICaptureTests`；
  用 python 驱动 swift 时必须显式设 `SDKROOT=$(xcrun --sdk macosx --show-sdk-path)`（否则报 SDK 不兼容，
  那条红是环境问题）。

## 当前状态（2026-10-11，批次 3 收尾）

- §4 U-4 与 U-5 已落地并验证：407 tests 0 失败、`make bundle` 0 warning、78 帧两次同 sha、5 条新守卫变异对照全过。
- U-5 的"12/13 自绘焦点环"这半条**刻意没做**，理由与所需前提写在 D-039 与快照 18，backlog 标 ready-for-human。
- 下一批：批次 4（U-2 拖出 drag image 含多文件 / F-2 RTF·HTML 保真）。
- 帧取证的一个新坑（别再撞）：逐行取最右墨点会把右下角浮层的按钮数成正文行 ——
  这类"改动有没有进像素"的问题，用两两帧 diff 的包围盒比用行数统计更难被污染。

## 当前状态（2026-10-11，批次 4 收尾）

- §5 F-2 与 §4 U-2（多文件拖出）已落地：416 tests 0 失败、`make bundle` 0 warning、78 帧两次同 sha、
  5 条新守卫变异对照全过、设置页改动的作用范围核对（其余分区 0 像素差异）。
- 最后一批：F-3（⌘⇧V 快速选择浮层，**先做 spike**：`NSPanel` 非激活样式下的键盘焦点是已知坑，
  spike 不通过就不要动仓库）+ C-4（构建产物运行时启动冒烟，必须用可覆盖的数据目录，D-002 不许破）。

## 当前状态（2026-10-11，批次 5 收尾）

- 第三轮 15 条建议（C-1…C-5 / U-1…U-5 / F-1…F-5）全部要么落地、要么在账本里写明了不做的理由。
- 最后一道验证：全量 430 tests / 10 skipped / 0 failures；`make bundle` 0 warning；
  78 帧两次同 sha；本批 5 条新守卫变异对照全过；Python 自测 43 例 OK。
- 剩下的两项都不是"忘了"：C-2 的"对上一版本帧基线做自动对比"仍未自动化；
  InstanceGuard 对直接 exec 启动的第二实例是否漏判，需要真机确认（快照 20）。
## 当前状态（2026-10-11，账面收口）

- 15 条建议全部落地；F-4 的写回分支补成端到端（D-049），15 条里不再有"只测了纯函数"的欠账。
- 现取判据：Swift 433 例 / 10 skip / 0 失败 · Python 64 例 · `make bundle` 0 告警 ·
  78 帧两次同 sha · 24 条守卫变异对照 · CI 全绿（含帧基线两步与运行时启动冒烟）。
- 留给真机的：批次 2–5 的手点清单；待查：InstanceGuard 对直接 exec 第二实例的漏判。

## 当前状态（2026-10-11 晚，新增功能：右侧预览渲染 Markdown）

- 功能已交付并验证：`.md` / `.markdown` 文件与"两类以上 Markdown 语法"的文本条目，
  详情区默认渲染，头部同一行给「原文 / 渲染」。渲染只改看法，存档/搜索/复制路径一行未动。
- 账本：D-050（为什么自己写子集而不是引依赖）、D-051（四个被实测否掉的做法）、
  D-052（帧基线会随系统外观漂移，已钉死并加了双向守卫）。
  视觉验收在 `AGENT_UI_AUDIT.md` U-17（含每个元素的实量对比度）。
- 数字：Swift 520 例 / 11 skip / 0 失败；Python 64 例；`swift build` 与 `make bundle` 0 告警；
  82 帧多次连拍与工作基线 `CHANGED=0 MISSING=0 ADDED=0`（且是在系统深色时段拍的，修之前会漂 18 帧）。
  取法：`cd ClipboardHistory && swift test 2>&1 | grep -E 'Executed [0-9]+ tests' | tail -1`。
- 新守卫 14 条全部实跑变异对照，**14/14 红在该红的那条用例**，跑完逐字节还原。
- 还没做的：v1.4.9 打包发布（没人要求）；那颗控件的"按下去真的会切换"只有手工清单（D-051 ④）。

## 当前状态（2026-10-11 晚，用户真机报的窗口装饰遮挡已修并装机）

- 缺陷：收起侧栏后详情头部与交通灯叠在一起（账本 D-053 / 视觉 U-18）。
- 修法：让位量由 `WindowChromeMetrics` 在运行时发布（谁摆按钮谁发布），详情头部消费它；
  首帧兜底 35pt。实测 meta 顶部 10pt → 42pt，灯带底边 33pt。
- 数字：Swift 526 例 / 11 skip / 0 失败；`swift build` 0 告警；82 帧与工作基线 0/0/0
  （22 帧因头部下移而变化，属预期）；5 条新守卫变异对照 5/5 红在该红的那条。
- 取法：`cd ClipboardHistory && swift test 2>&1 | grep -E 'Executed [0-9]+ tests' | tail -1`。
- 本机 `/Applications/时间剪史.app` 已是含此修复的构建（二进制 sha `bf761424…`），
  版本串仍是 1.4.8（v1.4.9 未发布）。上一份留在备份目录，未删。

## 当前状态（2026-10-12 凌晨，侧栏改成"永远显示"：已验证、已装机）

- 用户提议撤销"收起侧栏"这个能力：工具栏按钮与菜单命令本来就已摘掉，本轮补的是**拖分隔条**这条路 ——
  窗口配置器把侧栏列钉成不可折叠，已折叠的（旧存档）当场展开。账本 D-054 / 视觉 U-19。
- 实测：分隔条能去的最左位置 **-1pt → 250pt**；硬按到 0pt 之后列宽仍是 250pt（下限由列自己报）。
- 数字：Swift **531 例 / 0 失败**（+5 条判据）；**7 条变异 7/7 红在该红的那条**（含"钉错列"）；
  82 帧与工作基线 `CHANGED=0 MISSING=0 ADDED=0`（与新判据同进程拍的）；`swift build` 0 告警；Python 64 例 OK。
  取法：`cd ClipboardHistory && swift test 2>&1 | grep -E 'Executed [0-9]+ tests' | tail -1`。
- CI `e4b5359` 服务端结论 **success**（Swift 6.1.2 / macOS 15）：531 例 / 11 skip / 0 失败，
  5 条新判据在 CI 上**真的执行过**（不是被跳过），日志里的 `SIDEBAR_PIN` 数字与本机一致：
  钉住后最左 250pt、未钉住 -1pt。
- **状态由这一条决定**：`/Applications/时间剪史.app` 的二进制已是 `14f2f079…`（含本轮钉侧栏），
  装机前那份 `bf761424…` 留在 `~/Documents/Codex_Project0_backups/before-pinned-sidebar-20261012-002001/`
  （只此一份，另一份重复副本已清掉）。装完进程是从新路径起来的（pid 58939，`ps`/`lsof` 都指向 /Applications），
  不是"旧进程还在跑"那种假装机。
- 用户数据前后逐字节未变：`history.json` 70527 bytes / sha `98b00782…` / 84 条 / mtime 不变，`images/` 8 个文件。
- 留给真机的：**拖一次分隔条**（拖不动即成立，批次 7 第 7.1 条）；macOS 12/13 上这条判据没跑过（欠账 8）。

## 当前状态（2026-10-12 清晨，动效专项：交付 + 砍单，账本 D-055 / 视觉 U-20）

- 输入是 501 行的动效专项审计报告（含它自己 §11/§13 的 15 条 MC 缺陷）。用户要"先判出最不合理的
  约 10% 并说明为什么不做，剩下的实现"。结果：**加进去的 7 处动效，价值都来自先砍掉的 8 条**
  （M1 列表行过渡、M3/M10 热键呼出、M4 整块淡入、M9 扫光、M12 共享元素、M13 高亮、M14 stagger、M18 彩带）。
- 本轮最值钱的一条实测：**分带归因**。把动画事务挂到 `HistoryStore` 变更漏斗上之后，
  整窗逐帧从"一帧跳变"变成 4 帧斜坡，看起来 M1 成了 —— 但只量列表中部那条带（第 4~8 行）
  是 `0.304` 一帧到位、落定残余 0.000，与关掉曲线时一模一样。斜坡全部来自详情区。
  ⇒ 报告的结论成立，M1 在 `List` 上做不成；差点把"详情区在淡"当成"列表在滑"交付出去。
- 尺子自己也换了两轮驱动：`CADisplayLink` 在显示器休眠时 `ticks` 恒为 0（本机实测），
  `Timer` 被 App Nap 节流，最后用**自旋循环**当时钟 + `cacheDisplay` 离屏合成。
  顺带摘掉整个类的 `@available(macOS 15.0, *)` —— 那扇门本来只为 `CADisplayLink` 存在。
- 数字：`swift build` **0 告警**；`swift test` **560 例 / 0 失败 / 17 skip**；
  `MotionCatalogTests` 21 条、`MotionFilmstripTests` 8 条（`MOTION_SUMMARY notice-banner=3
  detail-kind-change=3 empty-state=4`，反向 `list-insert=一帧`、`same-kind=0.000`）；
  **7 个变异 7/7 红在该红的那条**；82 帧 `CHANGED=0`（动效只改在途帧，与基线闸门零冲突）；
  帧间隔对照臂：动画开 p95 16.67ms / worst 50.5ms，动画关 p95 16.67ms / worst 39.1ms ⇒ 量不出代价。
  `HistoryStore` 1094 行（比本轮开始前还低 7 行）。
- **一件自伤要记**：变异脚本里一句 `git checkout -- .` 把 9 个未提交文件还原到了 HEAD。
  靠事前 5 份 `cp` 备份 + 逐条重放恢复，恢复后所有数字是**重新跑出来的**，不是推测的。
  规矩：还原只准逐文件字节级 `cp`。
- 留给真机：批次 8 的 9 条（尤其 8.3 方向键连翻、8.6 VoiceOver 听那句"已复制"、
  8.7 中途打开减弱动态当场生效、8.8 热键呼出确实无动画）。
- **CI 那道像素闸的正文终于读到了**（run 38224108646）：`motion suite exit: 0 executed: 8`
  + `MOTION_SUMMARY notice-banner=3 detail-kind-change=4 empty-state=3` ⇒ MC-8 关闭，
  8 条判据在 CI 上真的执行且与本机同数。根因是日志噪声（一次 `swift test` 打 360 万条
  colorspace 消息，占 97.4%），过滤后整份日志 2386 行。
  我先前把"读不到"记成"下载不下来"，那是错的解释（下载只是慢，放宽超时就完成了）—— 已就地更正。
- 未覆盖：Switch Control 那一格（无公开 API）；设置页/菜单栏两处淡入没有各自的像素判据
  （机制与已量到的三条同源）；500 条时那一次 56ms 帧仍未定位（M1 砍掉后动效不再随条目数增长）；
  macOS 12/13 全档未跑（本机 27、CI 15）。


## 2026-10-12 17:13 换装：新版已装到 /Applications 并在跑（HEAD `b4ee260`）

- 用户要求"以后要手动运行检测都这么干"：需要真机验收的判据由我构建+换装+跑起来，不让他自己编。
- 已装：universal 包，二进制 sha `aaa032b463dfc13b…`；**版本号仍是 1.4.8**（自上次发布没 bump），
  所以"是哪一版"按 sha 与 HEAD 认，不要看 About 框。
- 旧包（`14f2f079…`）移到 `~/Documents/Codex_Project0_backups/before-motion-round-20261012-171308/`，没删。
- 证据链：`SMOKE_OK=1`（先退出旧版才拿得到，见下）→ staged 与 installed sha 相同 →
  `codesign --verify --deep --strict` 通过 → 新 pid 44938、启动时刻晚于安装、`lsof` 的 txt 指向
  `/Applications/…` → 存档 85 条未减少 → `DiagnosticReports` 无新崩溃。
- 流程已固化成 **`scripts/install_local.sh`** + 4 条自检（`scripts/tests/test_install_local.py`）：
  默认 dry-run、`--yes` 才动、失败自动回滚；沙箱三条判据（预检不过不许动现场 /
  sha 必须相等 / **回滚回来的必须与新包内容可分辨**）都真跑过。脚本 68 条自检全过。
- 三个坑写进了脚本注释与长期记忆：① 冒烟闸门必须排在退出旧版之后（守卫按 bundleIdentifier
  找第二实例，否则假报 `SMOKE_OK=0`）；② 活着的 App 随时写存档，"逐字节相同"不是有效判据，
  改判"条数只增不减"；③ CJK 路径在 `ps`/`lsof` 里是转义输出，别直接喂给 `shasum`。
- 交给用户的只剩人眼判据：批次 8 的 9 条（本轮新增一条往返测试由用户自己点：复制一次看历史长没长）。


---

## 状态 · 视觉迭代 R5（2026-10-13）

- 本轮是**第一轮把"全部页面全部元素"当范围**：约 206 个位点过完，产出 `.scratch/motion-audit/`，
  其中 8 条我自己读码核实、6 条已修、2 条证伪并写明理由。
- 连续 ≥90 的轮次：**R1 80 → R2 85 → R3 88 → R4 90 → R5 91**（R5 是第一个 ≥90 的下一轮，
  目标要求"连续五轮 ≥90"，所以还差三轮）。
- 全量测试 615 / 24 skipped / 0 failures；动效套件 20 / 3 skipped / **0 failures**（开工前它是红的）；
  0 warning；82 帧 `CHANGED=0`；`scripts/tests` 72 passed；变异 M6 2/2 + M8 1/1 CAUGHT。
- `HistoryStore` 零改动（1093/1120 行，上限只降不升那条守卫仍然绿）。
- 本机安装：R5 的包在提交后换装（`scripts/install_local.sh --yes`），
  人眼判据见 `docs/MANUAL_TEST_v1.4.9_round3.md` 批次 13。
- 下一轮（R6）主题已经立项：**"状态变化的可读性"** —— 详情预览三态硬换、
  设置页清空后的数字回执、暂停采集那一下的指示（三条共用同一个判据形状）。


---

## 状态 · 视觉迭代 R6（2026-10-13）

- 连续 ≥90 的轮次：**R4 90 → R5 91 → R6 92**（目标要"连续五轮 ≥90"，还差两轮）。
- R6 主题「状态变化的可读性」：预览三态软交接、清空后的数字回执（含播报）、展开箭头与揭示同曲线。
- 新增判据一族 `MotionDriverTests`（8 条）：**恒真的 `.animation(value:)` 键**是 R5 那族守卫的镜像，
  带真值表；回执的"先数再清"用两行代码的先后钉住。
- 验证：623 tests / 24 skipped / 0 failures；动效套件 20 / 4 skipped / 0 failures；
  0 warning；82 帧 `CHANGED=0`；`scripts/tests` 72 passed；变异 6/6 CAUGHT。
- 未闭环：预览三态与回执淡入的**产物级**证据（人工批次 14）；QuickPick 空结果；
  排除名单增删过程；本机 `judged=1/3` 的覆盖损失（BACKLOG 第 8 条，推荐修法 ③ 尚未落地）。
- R7 建议主题：**浮层与临时状态**（QuickPick 空结果一句话 + 落选态、批量条出现/消失的可插值落点、
  视频两颗图标接 `symbolMotion`）+ 把 BACKLOG 第 8 条的 `judged` 下限做成判据。


---

## 状态 · 视觉迭代 R7（2026-10-13）

- 连续 ≥90：**R4 90 → R5 91 → R6 92 → R7 93**（还差一轮就到"连续五轮 ≥90"）。
- R7 收掉 QuickPick 空结果、批量条两臂、视频两颗图标，新增"符号替换只有一个作者"一族判据，
  并把动效覆盖率下限做成 CI 里会红的一步（BACKLOG 第 11 条结案）。
- 验证：629 tests / 24 skipped / 0 failures；动效套件 20 / 4 / 0；0 warning；
  82 帧 `CHANGED=0`；`scripts/tests` 72 passed；变异 5/5 CAUGHT。
- 本机安装：R7 包在提交后换装（人工判据 = 批次 15）。
- 未闭环：QuickPick 淡入与空态播报的产物级证据（AppKit 侧，D-055）；
  排除名单增删（P2）；设置分区切换的 Scenario（P3）；实验 E1/E2/E3。
- R8 建议主题：**设置窗口专轮**（分区切换过渡转正为可量场景、排除名单增删过程、
  三处 caption 的"永不清空"、快捷键录制态），因为那 50 个位点里已核实的一批还没动。


---

## 状态 · 视觉迭代 R8（2026-10-13）· 目标达成

- **连续五轮 ≥90 达成**：R4 90 → R5 91 → R6 92 → R7 93 → R8 93；无新增 P0/P1 回归。
- R8 做掉设置窗口已核实的三条：排除名单六种结局各有话术（纯函数 `ExcludedAppListPolicy`）、
  名单增删过渡、三处结果文案统一成可关掉的 `ReceiptLine`（不自动消失）。
- 验证：632 tests / 24 skipped / 0 failures；动效套件 20 / 4 / 0；0 warning；
  82 帧 `CHANGED=0`；`scripts/tests` 72 passed；变异 M20–M23 4/4 CAUGHT。
- 本机安装：R8 包在提交后换装；人眼判据 = 批次 16。
- 仍未闭环（不粉饰）：AppKit 侧淡入与播报的产物级证据（D-055 边界）；
  菜单栏原生菜单在打开期间不重绘（P4，动效是唯一不该用的修法）；
  设置分区切换仍无 Scenario；实验 E1/E2/E3 未跑；
  已知两条红（`testSidebarListFocusRingAfterClick`、帧间隔 p95）本轮之前就存在。
- 总报告：`AGENT_FINAL_REPORT.md`。


---

## 状态 · 视觉迭代目标收口（2026-10-13 23:25）

- **目标达成**：连续五轮 ≥90（R4 90 / R5 91 / R6 92 / R7 93 / R8 93），
  全页面逐元素审计约 206 个位点已做完并落成 `.scratch/motion-audit/`。
- main 的 CI：R8b 与总报告两次 run **均成功**；R8 那次红由覆盖率闸门指出真实覆盖空洞，
  已在 R8b 用"三档判据"修掉（CI `judged` 0/3 → 2/3，门槛未动）。
- 本机跑的就是 R8 的包（pid 41157，sha 与 staged 相同，存档 92 → 92）；
  R8b 只改测试与账本，**不需要重装**。
- 人眼判据累计欠账：批次 12（按压态）、13（R5 空态与失败回执）、14（R6 预览三态与清空回执）、
  15（R7 QuickPick 空态与批量条）、16（R8 排除名单与结果文案）。
- 未闭环项都写在 BACKLOG 第 8/9/10/12/13 条与总报告 §21.4，没有"顺手当完成"的。
- 总报告：`AGENT_FINAL_REPORT.md` §21。

## 状态 · 目标模式阶段一完成，阶段二起跑（2026-10-13 12:30 本地）

**阶段一 · 每日复制热图已交付**（新功能，不是动效轮）：
设置 → 新增「统计」分类，26 周 × 7 天日历热图 + 汇总行 + 图例 + 原生 tooltip + 悬停详情 + 空态。
数据源是**单独的只追加账本** `daily-copy.json`（日键→条数，保留 730 天，损坏改名保原字节），
**不是**从 `entries` 现算 —— 后者有 500 条上限，现算出来的历史会随旧条目被淘汰而**倒退**。
首次为空时从存档时间戳回填一次；采集路径零同步磁盘写；退出同步 flush；回滚 = 删那一个文件。
决定见 **D-068**，视觉账见 **U-30**，人工验收见批次 **17**，轮次现场见 `AGENT_VISUAL_ITERATION.md` 阶段一节。

- **数字**：0 warning；653 tests / 16 skipped / **0 failures**（+21 条新用例）；
  动效套件 20 / 4 / 0，`judged=2/3`（与 R8b 同档，未退）；帧基线 **82 → 90**，
  `check --against working` = `COMPARED=90 CHANGED=0 MISSING=0 ADDED=0`（同提交 update）；
  `scripts/tests` 72 passed；`HistoryStore` 只加 4 行胶水（`lines=1111 funcs=52 longest=66`，只减不加的闸仍绿）。
- **变异 9 支**（M25、M25b、M26–M32）：第一次 8/9 —— **M31 逃逸**，因为它的判据用 `debounce: 60`
  且从不等待，"排了写盘"与"没排"看起来一模一样（恒真判据）；重写后 9/9 CAUGHT。
  M32 是本轮真实崩溃（MainActor 闭包被 `dispatch_assert_queue` 打断 → SIGTRAP）转成的回归判据，
  顺带把变异分类器教成"崩溃 = `CAUGHT=crash`，不是没跑"。
- **自评 88 / 100**（<90 ⇒ 按规矩继续修；扣在"动效细节"与"可访问性"两栏，都是新界面自己的账）。

**阶段二已准备**：`.scratch/motion-audit-2/00-inventory.md` —— 两个只读代理并行产出的全量位点清单
（主窗口/QuickPick 89 行 + 设置/菜单栏约 90 行，含 MotionCatalog 八档引用表、两套互相矛盾的 reduce 闸门、
去重后 20 条"最可能真缺陷"合并榜、R9–R28 排期）。
**这一轮明确禁止沿用 R1–R8 的结论当"已经对了"**：包括 D-066 里"快捷键录制态刻意不加动效"那一条，
R16 会带着原文理由重新判一次。

**下一步（R9 的三条头账）**：①`lastWriteError` 发布通道（BACKLOG 14）；②热图 hover 插值兑现（15）；
③`OffscreenSymbolInkProbeTests` 名单从产品枚举取 + 加"名单 == 产品"守卫（16）。
本机换装：见下面"本机跑的就是…"一行，阶段一的包在提交后重装并独立核对 sha / pid / 存档条数。

## 状态 · R9 完成（阶段二第 1 轮，2026-10-13 12:5x 本地）

审的是**上一轮自己交的东西**。六条改动全部来自看帧或读事务形状，读代码看不出来：
悬停描边与"当天变深"进了事务（键是 `bucket` 不是 `count`）、页脚那条**永远不演**的动画
被撤掉并写明理由（本轮唯一"减"的一条）、空↔网格两臂补齐过渡并由 `counts.isEmpty` 驱动、
零值汇总行与「这张图怎么读」不再在没有图的屏上说话。账见 **U-31 / D-069**，人工验收批次 18。

- **数字**：0 warning；658 tests / 16 skipped / 0 failures（+5）；动效套件 20 / 4 / 0、`judged=2/3` 未退；
  帧基线 `update` 后 `CHANGED=0`，本轮只有 4 张空态帧变（有数据的 8 张逐字节不变 ⇒ 重排没动布局）；
  `scripts/tests` 72 passed；变异 **M33–M42 十支全 CAUGHT**（第一次 M39 只改声明 ⇒ 编译不过 ⇒
  那是"没跑"不是"抓住"，改成连调用点一起改名后才红）。
- **自评 91 / 100**：新加的两条动画目前只有**结构证据 + 静帧**，像素证据排在 R9b
  （胶片套件的 `Scenario` 要能挂非主窗口的根视图，那条改动单独一支）。
- **CI 的第一发红了，红的是编译器**：Swift 6.1.2 在 `emitLazyGlobalInitializer → emitRawApply`
  SIGSEGV，本机 6.2.1 不复现。绕法与"为什么不做二分"见 **D-069**。
  这一发要盯：如果这次 CI 还红在同一个栈上，说明嫌疑不止那两处，得换一条绕法。
- **R10 的头一条已经定死**：`lastWriteError` 的发布通道（BACKLOG 14）——
  本轮刻意没顺手做，它是功能级缺陷，混在动效轮里做会让两件事的判据互相借光。

## 状态 · R10 完成（2026-10-13 13:1x 本地）

**R9 的 CI 绿了**（run 38348602329，8m12s：0 warning / 658 executed / 90 帧 / 0 捕获失效），
D-069 那条"全局惰性初始化器"绕法成立 —— 但**没有定位到具体是哪一处**，注释里写的是"嫌疑"。

R10 做的是 R9 留下的两条：
- `lastWriteError` 现在有发布通道（`@Published` 镜像 + 只送"该重绘"不送值的主队列回看 +
  flush 自己同步 + **没失败时不许多发**的反向判据）；
- 图标墨水探针的名单改成从 `SettingsCategory.allCases` 推导，并加"名单 == 产品"与逐枚墨水两条判据。

**顺手被数字否证的一个目测结论**：`chart.bar` 不是"实心柱混进描线那一列"（它是第二重的，0.0138 vs 同列 0.0118–0.0143）；
真正的异类是 `wand.and.stars` = 0.0052，比同列最轻的还轻 2.3 倍，而且从 D-8 那轮起就在。
本轮**不改**（换符号是语义 vs 重量的取舍），也**不加阈值判据**（拿六个数反推门槛 = 把一次观测写成规律）。
记 BACKLOG 22 + 人工验收 19.3，把判断交给人眼。

- **数字**：0 warning；664 tests / 16 skipped / 0 failures（+6）；动效套件 20 / 4 / 0、`judged=2/3` 未退；
  帧基线 `CHANGED=0 MISSING=0 ADDED=0`（本轮零像素变化，这是正确的结论）；`scripts/tests` 72 passed；
  变异 M43–M46 四支全 CAUGHT。自评 **90 / 100**（本轮按设计没有视觉交付，分数如实反映）。
- **下一轮（R11）**：回到像素 —— R9b 那三条动画的胶片证据（`Scenario` 要能挂非主窗口根视图），
  然后按清单进主窗口（侧栏批量按钮零按压反馈 / 行没有 hover / 筛选滑块 0.38s 越权那三条）。

## 状态 · R11 完成（2026-10-13 14:0x 本地）

去兑现 R9 欠的"像素证据"，结果**推翻的是结论不是分数**。

`Scenario` 现在能挂非主窗口的根视图（宿主是产品自己的 `DailyCopyStatsSection`，
为此 `private` → internal），新场景 `heat-first-record` 第一次跑就把 main 判红：一帧到位。
按这个方向改了两版产品代码，**两版读数一模一样**；于是做仓库里已有的那件工具 —— 双向 A/B：

```
MOTION_HEAT_FADE_A/B 开 帧数=1 峰值=0.225 冷闸=true  关 帧数=1 峰值=0.225
```

**关掉动效目录读数不变 ⇒ 这把尺看不见纯 opacity 的淡入**（`cacheDisplay` 抓模型树）。
所以这条淡入定为**「源码已接、产物未量」**：不写进已验证，也不反过来说产品没做。
影响面比这一条大：**以前几轮的 MOTION 数字只覆盖带布局位移的那类过渡**（记 BACKLOG 23，
总报告要把"已验证 / 产物未量 / 人眼判"三类分开列）。

同轮补的：冷采样闸门 `clockIsWarm`（新窗口头两帧 260–340ms，触发落在上面会把 160ms 的过程拍成两三个样本）、
说明块「这张图怎么读」的过渡与驱动成对（它以前是整块硬蹦的）。
**我自己写的守卫先红了一次且红得不对**：needle 把 `private struct` 写死了，
去掉 `private` 就找不到目标 —— 产品没坏，守卫锁了个不相关的语言细节（已改并写进注释）。

- **数字**：0 warning；666 tests / 16 skipped / 0 failures（+2）；
  动效套件 21 / 4 skipped / 0 failures，`MOTION_SUMMARY` 三键形状不变、`judged=2/3` 未退；
  帧基线 `CHANGED=0`（说明块包进 `VStack(spacing:16)` 后布局逐字节不变）；`scripts/tests` 72 passed；
  变异 **M47–M49 三支全 CAUGHT**（M49 打的是尺子自己的闸门：`warmIntervalMilliseconds` 设成达不到 ⇒
  "看不见"这条结论必须作废，不许拿冷采样宣布尺子的极限）。自评 **92 / 100**（性能栏扣 6 分给预卷放宽与 A/B 多录一卷）。
- **人眼欠账**：批次 20 就是这条淡入的验收 —— 机器量不到，只能看。
- **R12 选题**（清单里的第 6/7 条，都是"我改过的要重新判"）：
  筛选滑块 0.38s / damping 0.72 越过目录自己的 ≤0.25s 与不过冲两条；
  同一个文件里两套 reduce 闸门（`@Environment(\.accessibilityReduceMotion)` 只认系统开关、不认 VoiceOver，
  且 `.linear(duration: 0)` 是**清零**而不是替换 —— 违反 R1 定的规矩）。

## 状态 · R12 完成（2026-10-13 14:3x 本地）

清的是**自己前几轮留下的两笔账**（全新清单第 6、7 条）：侧栏筛选胶囊
`0.38s / damping 0.72` 越目录上限且必有过冲（它是点出来的，不是手势跟手）；
它的 reduce 闸门只读系统开关、不认 VoiceOver；而这一段悬停**只有缩放一种表达** ⇒
开了「减弱动态效果」= 悬停零反馈。
现在：目录新增 `.slider`（0.20s、临界阻尼）、闸门取或、悬停补一层 `controlHover` 底色。
**性质是清账不是发现** —— 目录注释当时就写着"这两处有过冲，是已知例外"，知道了没排上。
账见 **D-070 / U-34**，人工验收批次 21。

- **翻案**：`FilterPillMotionTests` 原有一条把"过冲是想要的"钉成了规矩；先读原文（R2-10 的
  动机是"滑块不读 reduce 开关"，那半条仍成立并保留），只推翻"过冲"这半句，理由写在测试上方。
- **设计好的摩擦**：目录白名单守卫立刻红了 —— `HistorySidebarView.swift` 不再在目录外写曲线，
  名字已按提示删掉。顺带把 `Shape.Slide.leading` 这条死分支用起来。
- **数字**：0 warning；667 tests / 16 skipped / 0 failures；动效套件 21 / 4 / 0、`judged=2/3` 未退；
  帧基线 `CHANGED=0`（静止态逐字节不变是这一轮应有的结果）；`scripts/tests` 72 passed；
  变异 **M50–M53 四支全 CAUGHT**（M51 故意打到另一个套件）。自评 **93 / 100**。
- **欠**：悬停态无像素证据（BACKLOG 24）、"0.20s 且不过冲"尺子量不到（纯 transform，同 R11 那族）。
- **R13 选题**：清单第 11 条 —— 侧栏五颗批量按钮（含删除）用 `.buttonStyle(.borderless)`，
  零按压、零悬停，是全 App 唯一一处绕开 `PressableStyle` 的地方；
  以及第 19 条 `PressableStyle:53` 那个硬写的 `isHovered: false` 让 `VisualFill.hover` 档全 App 不可达。


## 状态 · R13 完成（2026-10-13 15:3x 本地）

清的是**我自己在 R4 留下的那一半**：`PressedStyle.makeBody` 里硬写 `isHovered: false`
（`ButtonStyle` 不能有 `@State`），于是 `VisualFill.hover` 这一档在**全 App 12 处按钮**上
运行时不可达，而真值表、令牌、字段名全都绿着 —— 载荷绿、消费侧坏。
现在样式内部多了一个真的视图持有它；顺带把三处 `.buttonStyle(.borderless)`
（侧栏五颗批量按钮含**删除**、排除名单「移除」、回执 ×）收进同一档，
并给小控件新增 `hoverLevel` 参数（0.10，其余站点保持 0.06 不动）。
账见 **D-071 / U-35**，人工验收批次 22。

- **视觉复核第一次用 bbox 定位**：`CHANGED=2` 两帧都在多选条，整帧看不出差别，
  逐像素 diff 指到 `(343,220)-(529,266)` ＝ 四颗描线图标，明暗各 0.19%、最大通道差 264/201。
  判读：**图标从灰提到满**（`.borderless` 对 label 的处理，不是暗色对比度问题）；
  红色 trash 一像素没动（它带显式 `foregroundStyle`）⇒ 反证压暗来自样式。
  这五颗全文件零 `.disabled(` ⇒ 压暗不携带信息，只是把可用动作画成禁用。**改善，无回归。**
- **变异第一次 4/5**：M58（样式转交时把 `hoverLevel` 换成默认档）全绿通过 ——
  本轮新加的参数自己重演了本轮修的缺陷族。补"花括号配平区域 + 转交点不许出现常量 +
  全仓恰好三处消费者"的接缝判据后 **5/5**，区域助手另配真值用例。
- **一条关于报告型数字的新认识**：`MOTION_RESOLVE_SUMMARY` 是**负载敏感**的 ——
  同一场景单独跑最粗采样 70ms（判）、全量并跑 81ms（门槛 48ms ⇒ 拒判）。
  两个数都记；以后既不许把 2→1 当回归去追，也不许当"都验过"去报。
- **数字**：0 warning；全量（开在屏探针）670 tests / 16 skipped / 0 failures；
  胶片单独 21 / 4 / 0、`judged=2/3` 与 R12 同；脚本 72 passed；
  帧基线 `update` 后 `CHANGED=0 MISSING=0 ADDED=0`；自评 **94 / 100**（R9 91 / R10 90 / R11 92 / R12 93）。
- **核对过的一条老账**：`--against auto` 对 v1.4.8 报 `MISSING=2` 是
  `glass-pill-120x200` → `120x232` 的改名（R1/R2 之间刻意改高），不是夹具掉帧。
- **R14 选题（改尺子，不改观感）**：① 给交互探针加一条**真** `mouseEntered` / tracking-area 通路，
  让胶片能框住单个控件判"悬停药丸画没画出来" —— 做成一次解锁清单里约 15 处 hover-only 位点；
  ② 帧夹具补两帧（`settings-privacy-excluded`、`settings-data-receipt`），
  让「移除」与回执行**第一次**进基线（本轮这两处是"源码已接、产物未量"）。
  R15 再谈药丸几何与命中区（BACKLOG 25）。

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R43 的台账写入（一次一份，锚点全部 assert，写不进去就报错而不是静默）。"""
import io

ROUND = '''
---

## 第 45 轮 · R43：导出/导入那三条回执 —— 一件事被说两遍，而失败那句又是英文（U-69 / D-102）

### 开场缺陷清单（坐标）

R42 复核 BACKLOG 53 时顺手看到的（当时只记成 BACKLOG 62）。本轮把它判完，
而**判完发现不是一处是三处**：

| 位点 | 修前 | 为什么是缺陷 |
|---|---|---|
| `SettingsView:172-179` 导出反馈 | 三个分支都写 `exportMessage`（行内）**并且** `showExportAlert = true`（模态） | 同一句话说两遍，其中一遍还是**打断式**的；而仓库其余三处回执（清空历史 / 导出导入存档 / 排除名单）都是行内 |
| `SettingsView:177` 失败那一支 | `"导出失败：\\(error.localizedDescription)"` | `ExportError` 不是 `LocalizedError` ⇒ 界面写的是 "The operation couldn't be completed. (…)" |
| `SettingsWindowController:94` 导出存档 | `"导出失败：\\(error.localizedDescription)"` | 同上 |
| `SettingsWindowController:104` 导入存档 | `"导入失败：\\(error.localizedDescription)"` | 同上 |

⇒ **U-67 那一族根本没收口**：R41 只把"写剪贴板"那条路做了人话，界面上还剩三个出口在直出系统原文。
本轮把这三个出口一起接进同一层措辞。

### 修法：措辞集中成一个文件，通道只留一条

新增 `Utilities/ReceiptWordings.swift`：`FeedbackExportReceipt`（成功 / 暂无 / 两种失败）
与 `ArchiveTransferReceipt`（导出失败 / 导入失败）。三个 catch 全部改成
「原文进 `LifecycleDebugLogger` + 界面用映射器」，模态那条 `.alert` 与 `@State showExportAlert` 删掉。

为什么集中成一个文件：这一族**同时**被三个产品入口消费，而它们的坏法一模一样；
分开放就会分家 —— R41 收了写剪贴板那一条，这一族当时就没人管。

### 判据（7 条新，全 CI 每轮跑）

- `testFeedbackExportReceiptTruthTable`（5 格）：成功说文件名 / **空数据不许被说成失败** /
  写盘失败给下一步且**不含 payload** / 未分类也说"文件没有生成" / 每一格都不许含 `ErrorDomain` 与英文原文。
- `testArchiveTransferReceiptTruthTable`：两句都含下一步、都不含原文，
  外加一格**前提判据** —— "记录没有任何变化"这句是真的，因为 `importArchiveJSON` 的抛出点
  在 `entries = ` 之前（`HistoryStore.swift:493-495`，判据直接比这两个位置）。
  以后有人改成流式就地写入，这句会变成假话，而**红的就是这一格**。
- `testExportFeedbackActionSpeaksThroughTheMapperOnce` / `testArchiveActionsSpeakThroughTheMapperAndLogTheRawError`：
  读**产品源码里那两个真动作**（`exportFeedbackData` 里是 `NSSavePanel` + Finder，测试进程碰不得），
  判"走映射器 + 不含 `localizedDescription` + 全文件不再有第二条通道 + 两个 catch 各有一条日志"。
- `testEmptyDataStillGoesThroughTheMapperRatherThanASpecialCase`：动作里不许手抄那一句。
- `testHarnessNeverHandWritesReceiptCopy` + `testHandWrittenReceiptScanIsATruthTable`（4 格）：
  **本轮最意外的一条** —— `receipt-line` 那张帧从 R14 起画的是
  `"已导出 94 条记录到 ~/Desktop/时间剪史-导出.json"`，而**全仓 grep 不到这句产品话**。
  也就是说这张帧一直在给一个不存在的文案做保：产品怎么改它都不红。
  这是 R24 那条"夹具只能呈现产品的决定"的又一次违反，只是这次违反的是**文案**而不是间距。

### 真实视觉审查（含一张被自己的守卫当场打红的帧）

换成产品自己那句话之后，`contentMustFit` 立刻红了两张：
`receipt-line-430x56` 底行读到 **18.4%（亮）/ 20.2%（暗）** 的墨 ⇒ 56pt 放不下两行 ⇒
**这张帧以前也在裁自己展示的内容**。抬到 **72pt** 之后 `bottomInk=0.0%`。
⇒ 又一次印证 R22 那条：`contentMustFit` 这类"底行不许有墨"的闸门，价值不在它绿，
在它**换内容就会红**。

看帧（430×72，亮暗各一次）：正文两行完整、无半字、× 在第一行右端（`firstTextBaseline`），
文字与 × 之间无重叠；亮档黑字 / 暗档白字，底色都是窗口灰。
⇒ 组件帧合格。R25 那次把**横幅**的动作位改成垂直居中，`ReceiptLine` 这一族仍是顶对齐 ——
一行回执与两行回执里 × 都跟着第一行；本轮**没动**它，因为 × 是"收起这一条"而不是"管整条的动作"，
顶对齐在系统里也是常见写法。这条差异记进 BACKLOG 65，别让它变成"看起来一致但其实没判过"。

### 本轮查出、**没**在本轮修的

- **BACKLOG 64 的推广被一条真问题挡住了**：`ContentView` 那五条 `NoticeBanner` 的驱动是
  一条**派生键** —— `:32` `.animation(bannerIn, value: noticeSignature)`，
  而 `noticeSignature`（`:36-44`）把五条回执的存在性压成一个 bitmask。
  ⇒ 按名字匹配的判据会把这五条**全部误报成没电**。推广的第一步不是换组件名，
  是让判据会把派生键**展开**成它读的那几个状态。好消息：这五条确实有电（R22 用像素量过）。
- **BACKLOG 65（新）**：`ReceiptLine` 的 × 是顶对齐，横幅的"知道了"是垂直居中（R25 / D-084）——
  两族动作位语言不同，本轮判过、刻意不动；要统一得先说清"× 管整条还是管第一行"。

### 换装本机（12:48）

`install_local.sh --yes --no-build --label r43-receipt-wording` ⇒ `INSTALL_RESULT=ok`、
`INSTALL_SHA_MATCH=1`（`0a752818…` → `a5c52cbe…`）、新 pid 34026、**存档 103 → 103 条**、
`SMOKE_OK=1`。旧包留在 `before-r43-receipt-wording`。

### 验证

733 tests / 29 skipped / **0 failures**（+7 条判据）；`swift build` 0 告警；
闸门 `passed=704 skipped=29 failed=0 有名字的红=0 NOT_RUN=0 ⇒ ok`；
帧基线 112 张（`receipt-line` 因改名 430x56 → 430x72：`MISSING=2 / ADDED=2`，同 commit update，
改完复跑 `CHANGED=0 / MISSING=0 / ADDED=0`）；脚本 83 全绿；
变异 **M199–M205** 七支全 CAUGHT、`未被抓到=0 红得不对=0 还原不干净=0`
（needle 全部来自 `--measure` 那一遍打印的失败消息原文 —— R42 立的流程第一次真跑）。
**CI 待读**。
'''

DECISION = '''

---

### D-102 · R43：一条"报告失败"的话，界面上只能有一个出口、一种语言

- **背景**：R41 的 D-100 把"写剪贴板失败"翻成人话，但当时**没有过一遍这一族的其它出口**。
  R42 复核回执时看到三个：导出反馈（`SettingsView:177`）、导出存档（`SettingsWindowController:94`）、
  导入存档（`:104`）—— 全是 `"…失败：\\(error.localizedDescription)"`，
  而这些错误类型都不是 `LocalizedError` ⇒ 界面会写 "The operation couldn't be completed. (…)"。
  另外导出反馈还**同时**弹模态（`showExportAlert`）+ 走行内回执，一件事说两遍。
- **决定**：① 这一族的措辞集中到一个文件（`Utilities/ReceiptWordings.swift`，两个纯枚举），
  界面只说"发生了什么 + 下一步"，**原文一律进 `LifecycleDebugLogger`**；
  ② 通道只留一条 —— 删掉模态，跟着仓库里其余三处回执（都是行内 `ReceiptLine`）走。
- **决定 2（为什么"记录没有任何变化"这句敢写）**：它不是感觉，是查过的 ——
  `importArchiveJSON` 的抛出点（读文件、`ArchiveTransfer.import`）都在 `entries` 被改之前
  （`HistoryStore.swift:493-495`）。而且这一条**被做成了判据**（真值表里比这两个位置），
  所以以后改成流式就地写入时，界面不会继续说一件不再成立的事。
- **决定 3（夹具不许替产品写文案）**：`receipt-line` 那张帧从 R14 起画的产品**根本没说过**的一句话
  （grep 全仓无此文案）。新增一条按族判据：`ReceiptLine(text: "字面量"` 出现在夹具里就红。
  这是 R24"夹具只能呈现产品的决定"在**文案**维度的补票。
- **代价**：+2 个纯枚举文件、+7 条判据；`receipt-line` 帧从 430×56 变 430×72
  （`contentMustFit` 当场红 ⇒ 那张帧一直在裁自己）；删掉一个模态 ⇒ 如果有人就喜欢模态，
  这是可回滚的一行（人工批次 45.2 专门问这一条）。
- **谁守着**：真值表 2（5 格 + 3 格含前提）、接线判据 3、夹具文案判据 2；变异 M199–M205 七支全 CAUGHT。
- **仍未验证**：真机上这三条失败**造不出来**（要磁盘满 / 目录不可写 / 文件被移走）。
  本轮验的是"如果失败，界面会说什么、说几遍"，不是"失败真的发生时"。
  人工批次 45.1 给的是可操作近似（把导出目标选在一个不可写的位置）。
'''

STATE = '''

---

## R43 · 导出/导入那三条回执：一件事被说两遍，而失败那句又是英文（第 45 轮 / U-69 / D-102）

- **复核把"一个出口"扩成三个**：`SettingsView:177`、`SettingsWindowController:94`、`:104`
  全在把 `error.localizedDescription` 拼进界面，而这三条路上的错误类型都不是 `LocalizedError`
  ⇒ **U-67 那一族 R41 根本没收口**，只是收了一条。
- **修法**：新增 `Utilities/ReceiptWordings.swift`（`FeedbackExportReceipt` + `ArchiveTransferReceipt`），
  三处 catch 改成「原文进日志 + 界面用映射器」；导出反馈那条**同时**存在的模态 `.alert` 与
  `showExportAlert` 删掉（仓库其余三处回执都是行内）。
- **两条"顺带"才是本轮最值钱的**：
  ① `receipt-line` 那张帧从 R14 起画的是**产品根本没说过的一句话**（全仓 grep 无此文案）
     ⇒ 新增夹具文案判据 `testHarnessNeverHandWritesReceiptCopy`；
  ② 换成真文案之后 `contentMustFit` 当场红两张（底行 18.4% / 20.2% 有墨）
     ⇒ 那张帧**一直在裁自己**，56 → 72pt 才放得下。
- **BACKLOG 64 被一条真问题挡住**：`ContentView` 五条 `NoticeBanner` 的驱动是派生键
  `noticeSignature`（bitmask）⇒ 按名字匹配的判据会把它们全部误报成没电。
  推广之前要先让判据会把派生键展开成它读的那几个状态。新开 BACKLOG 65（× 顶对齐 vs 横幅动作居中）。
- **验证**：733 tests / 29 skipped / 0 failures（+7）、`swift build` 0 告警、
  闸门 `有名字的红=0 NOT_RUN=0`、帧基线 112（改名 `MISSING=2 / ADDED=2` 同 commit update，复跑全 0）、
  脚本 83 全绿、变异 M199–M205 七支全 CAUGHT（needle 全部实测抄来 —— R42 立的流程第一次真跑）。
- **换装本机（12:48）**：`INSTALL_RESULT=ok`、`INSTALL_SHA_MATCH=1`（`a5c52cbe…`）、
  新 pid 34026、存档 103 → 103、`SMOKE_OK=1`。
- **CI 待读**。
- **下一步（R44）**：① BACKLOG 64 的派生键展开（做成了才能把调用点级守卫推广到 NoticeBanner / 热图）；
  ② BACKLOG 59 的存盘失败通道形状（一次性横幅 vs 常驻只读标记）；③ BACKLOG 61 等人工批次 43.4 的回答。
'''

CHANGELOG = '''
### Fixed（R43 · 导出/导入那三条回执：一件事被说两遍，而失败那句又是英文）

- **R41 那一族其实没收口**：界面上还有三个出口在把 `error.localizedDescription` 拼进回执
  （`SettingsView:177` 导出反馈、`SettingsWindowController:94` 导出存档、`:104` 导入存档），
  而这些错误类型都不是 `LocalizedError` ⇒ 用户看到的是
  "The operation couldn't be completed. (…)"。本轮三个一起接进同一层措辞。
- 新增 `Utilities/ReceiptWordings.swift`：`FeedbackExportReceipt` + `ArchiveTransferReceipt`
  两个纯枚举。界面只说"发生了什么 + 下一步"，**原文一律进 `LifecycleDebugLogger`**（D-100 同一条分工）。
- 「导出反馈数据」原来**同时**弹模态与发行内回执 ⇒ 删掉模态，只留行内
  （仓库其余三处回执都是行内）。
- 一句被写成判据的前提："导入失败……记录没有任何变化"是真的，因为 `importArchiveJSON`
  的抛出点在 `entries` 被改之前 —— 判据直接比这两个位置，以后改成就地流式写入会先红。
- **两条顺带查出的**：① `receipt-line` 那张帧从 R14 起画的是**产品没说过的一句话**
  （全仓 grep 不到那句文案）⇒ 新增"夹具不许手写回执文案"的按族判据；
  ② 换成真文案后 `contentMustFit` 当场红两张（底行 18.4% / 20.2% 有墨）
  ⇒ 那张帧一直在裁自己，56 → **72pt** 才放得下。
- 判据 +7（真值表 2 / 接线 3 / 夹具文案 2），变异 **M199–M205** 七支全 CAUGHT，
  needle 全部从 `--measure` 的失败消息原文抄（R42 立的流程第一次真跑）。
- 新开 BACKLOG 65（`ReceiptLine` 的 × 顶对齐 vs 横幅动作垂直居中，本轮判过、刻意不动）；
  BACKLOG 64 的推广被一条真问题挡住：`NoticeBanner` 那五条的驱动是**派生键** `noticeSignature`，
  按名字匹配会全部误报 ⇒ 先让判据会展开派生键。
- 本机已换装：`INSTALL_RESULT=ok`、sha `a5c52cbe…`、`SMOKE_OK=1`、存档 103 → 103 条。
- 验证：733 tests / 29 skipped / 0 failures、`swift build` 0 告警、闸门
  `有名字的红=0 NOT_RUN=0`、脚本 83 全绿、帧基线 112（改名两张，同 commit update）。

'''

VISUAL = '''
---

## Round 43 · 导出/导入那三条回执：一件事被说两遍，而失败那句又是英文（R43 / U-69 / D-102）

**这一轮问的问题**：R42 复核动效时看到 BACKLOG 62 挂在旁边 —— 本轮把它判完，
而"一处措辞问题"判成了**三个出口 + 一条重复通道**：
`SettingsView:177`、`SettingsWindowController:94`、`:104` 全在把 `localizedDescription` 拼进界面，
导出反馈还同时弹模态 + 发行内回执。⇒ R41 的 U-67 那一族当时**只收了一条路**。

**做了什么**：`Utilities/ReceiptWordings.swift`（两个纯枚举）+ 三处 catch 改道 + 删掉模态。
"导入失败……记录没有任何变化"这句是查过抛出点才写的，而且把那个前提做成了判据。

**真实视觉审查（这次有新画面可看，而且是守卫替我找到的）**：
换成产品自己那句话之后 `contentMustFit` 立刻红两张 —— `receipt-line-430x56` 底行
18.4%（亮）/ 20.2%（暗）有墨 ⇒ **这张帧从 R14 起就在裁自己展示的内容**；抬到 72pt 后 `bottomInk=0.0%`。
看帧：两行完整、无半字、× 在第一行右端、亮暗都正常。
而更该记的是：**那张帧以前画的文案产品根本没说**（全仓 grep 不到）——
于是新增一条按族判据，让"夹具替产品写文案"这件事从此会红。

**流程上的第一次真跑**：变异 needle 全部来自 `--measure` 那一遍打印的失败消息原文
（R41/R42 三次踩同一个坑之后，这条从"规矩"变成"脚本的两遍跑法"）。

### 自评 92 / 100

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 18 / 20 | 删掉模态之后，回执这一族在设置页只有一种表达（行内 + × 收起），跟系统那类非打断提示一致；扣 2：真机层级仍未看 |
| 流畅度 | 13 / 20 | 本轮没动时序；`流畅度` 自 R39 起一直卡在这一格（BACKLOG 53 那半已在 R42 补，但淡入仍无像素证据） |
| 层次与材质 | 14 / 15 | 组件帧第一次画的是产品真话，且不再被裁（56 → 72pt 是 `contentMustFit` 逼出来的）；扣 1：× 顶对齐 vs 横幅动作居中这一差异仍未判（BACKLOG 65） |
| 动效细节 | 13 / 15 | 沿用 R42；本轮零时序改动 |
| 交互反馈 | 10 / 10 | 失败不再被说两遍，也不再要求用户读懂英文 |
| 可访问性 | 9 / 10 | +1：三个出口的英文系统原文清零，每句都带下一步；扣 1：读屏播报仍未核（旧账，独立一轮） |
| 性能 | 15 / 15 | 零成本（两个纯枚举 + 少一个模态）；采集路径与磁盘写没动 |

**为什么连续三轮停在 91–92**：`流畅度` 与 `动效细节` 这两格要涨，必须先解决"淡入量不到"这件事
（BACKLOG 64 的派生键展开 + 一条能进设置窗口的胶片通道）。下一轮要么做那个通道，
要么承认这一维只能靠人眼并把分数上限写死。

**验证**：733 tests / 29 skipped / 0 failures、`swift build` 0 告警、闸门
`passed=704 skipped=29 failed=0 有名字的红=0 NOT_RUN=0 ⇒ ok`、帧基线 112（改名两张，同 commit update）、
脚本 83 全绿、变异 M199–M205 七支全 CAUGHT。**CI 待读**。
'''

MANUAL = '''
---

## 批次 45 · R43 导出/导入的回执只说一次，而且说的是人话（U-69 / D-102）

机器侧的证据：判据 +7（真值表 2 含一格"前提判据"、接线 3、夹具文案 2）；
变异 M199–M205 七支全 CAUGHT；`receipt-line` 那张组件帧从 430×56 抬到 430×72
（`contentMustFit` 当场红 ⇒ 它以前一直在裁自己），现在画的是产品真话。
已换装到 `/Applications/时间剪史.app`（sha `a5c52cbe…`，存档 103 条一条没丢）。

| # | 怎么试 | 我的预测（先写下再去对） | 如果不对 |
|---|---|---|---|
| 45.1 | 设置 → 推荐（或数据）里点「导出反馈数据」，**有数据**的那一次 | 只出现**一行行内回执**"已导出：feedback_export_….json"，**不再弹模态框**；Finder 会打开并选中那个文件 | 还弹模态 ⇒ 我删的那半被加回来了（判据会红，说明你装的不是这份包，告诉我版本号）；Finder 没打开 ⇒ 那是另一半行为，本轮没动它，我单独查 |
| 45.2 | 同一处，**先把反馈数据清空**（或在全新存档下）再点导出 | 行内那句应该是"**暂无反馈数据可导出**" —— 不带"失败"两个字，也不该有红色/警告语气 | 它说成"导出失败…" ⇒ 真值表第 ② 格在真机上被推翻（那条判据钉的就是这个），把原话抄给我 |
| 45.3 | 想看见失败那句话：把导出目标选到一个**不可写**的位置（例如只读卷、或系统盘根目录） | 界面写"导出失败：这些反馈数据没能写进磁盘，文件没有生成。请确认磁盘没有写满、这个 App 的数据目录可写，再试一次。" —— **全中文、两句、没有英文错误域** | 出现 "The operation couldn't be completed" 或 `NSCocoaErrorDomain` ⇒ 那条出口没接上映射器（判据读的是源码，说明还有第四个出口我没找到），把原话抄给我 |
| 45.4 | 「导出历史…」选一个不可写位置；再拿一个**不是本项目导出**的 JSON 点「导入历史…」 | 两句都该是中文且都带"没有任何变化"：导出说"历史记录本身没有任何变化"，导入说"记录没有任何变化" | 若导入那句其实**变了**历史（比如它清掉了旧记录）⇒ 那是真缺陷且优先级最高，立刻告诉我，因为那句话是我在判据里钉住的前提 |

**批次 44 的四条仍然有效**（回执淡入 / 模态与行内 / 存档导出导入 / 减弱动态）。
其中 44.2 那句"还会弹一个模态框"到本轮**已经不成立** —— 模态被删了，这是本轮的修法之一。
'''

BACKLOG_CLOSE = (
    "62. **「导出反馈数据」同一件事有两条通道，而失败那条又是系统英文原文（R42 复核 BACKLOG 53 时看到，未修）**：",
    "62. **「导出反馈数据」同一件事有两条通道，而失败那条又是系统英文原文（R42 复核 BACKLOG 53 时看到）· 已收口（R43 / D-102）**：",
)

BACKLOG_NOTE = (
    "    注意 BACKLOG 60 里\"导出失败与'导出 N 条'两条横幅互相矛盾\"是**同一片代码**，一并判。",
    "    注意 BACKLOG 60 里\"导出失败与'导出 N 条'两条横幅互相矛盾\"是**同一片代码**，一并判。\n"
    "    **R43 收口记录**：判完发现不是一处而是**三处**（导出反馈 / 导出存档 / 导入存档都在拼\n"
    "    `localizedDescription`），措辞集中进 `Utilities/ReceiptWordings.swift`，模态那条删掉，\n"
    "    原文一律进日志；同时补了一条**夹具不许手写回执文案**的按族判据 ——\n"
    "    `receipt-line` 那张帧从 R14 起画的产品根本没说过（全仓 grep 无此文案），\n"
    "    换成真文案后 `contentMustFit` 又当场红出第二件事：那张帧一直在裁自己（56 → 72pt）。\n"
    "    与 BACKLOG 60 那条\"两条横幅互相矛盾\"是同一片代码，那条仍开放（它问的是横幅之间，不是模态）。",
)

BACKLOG_65 = '''65. **`ReceiptLine` 的 × 顶对齐，而横幅的「知道了」垂直居中（R43 看帧判过，刻意不动）**：
    R25 / D-084 把**横幅**（`StateLine`）的动作位改成垂直居中，理由是"两三行正文时按钮压在上三分之一，
    读起来像这个动作只管第一句"。`ReceiptLine` 是 `HStack(alignment: .firstTextBaseline)` ⇒
    × 跟着第一行。本轮**没统一**，因为两族的动作语义不同：
    「知道了」是**对整条消息的确认**，× 是**收起这一条**（贴着它要收起的那句话的首行更像"这个 × 管这条"）。
    需要人来判的一问：两行回执时，那个 × 让你觉得它只管第一行吗？（人工批次 45 里没问，
    因为本轮帧刚换文案 —— 下一轮若做 BACKLOG 64 的推广，顺手把这一问带进批次。）
'''


def patch(path, pairs):
    text = io.open(path, encoding="utf-8").read()
    for old, new in pairs:
        assert text.count(old) == 1, (path, text.count(old), old[:70])
        text = text.replace(old, new)
    io.open(path, "w", encoding="utf-8").write(text)


import os
os.chdir("/Users/wangziyi/Codex_Project0")

# 1. 视觉台账：追加第 45 轮
with io.open("AGENT_UI_AUDIT.md", "a", encoding="utf-8") as f:
    f.write(ROUND.lstrip("\n"))

# 2. 决定台账：D-102
with io.open("AGENT_DECISIONS.md", "a", encoding="utf-8") as f:
    f.write(DECISION.lstrip("\n"))

# 3. 状态
patch("AGENT_STATE.md", [
    ("- **下一步（R43）**：① BACKLOG 62 那片代码一次判完（回执留行内还是留模态 + 原文进日志）；\n"
     "  ② 或 BACKLOG 61（选中行滚进可视区）先问用户接不接受；③ 电池脚本补\"needle 不符 ⇒ DID-NOT-RUN\"。",
     "- **下一步（R43）**：① BACKLOG 62 那片代码一次判完（回执留行内还是留模态 + 原文进日志）；\n"
     "  ② 或 BACKLOG 61（选中行滚进可视区）先问用户接不接受；③ 电池脚本补\"needle 不符 ⇒ DID-NOT-RUN\"。\n"
     + STATE),
])

# 4. CHANGELOG
patch("CHANGELOG.md", [
    ("## [Unreleased]\n", "## [Unreleased]\n\n" + CHANGELOG),
])

# 5. 迭代日志
with io.open("AGENT_VISUAL_ITERATION.md", "a", encoding="utf-8") as f:
    f.write("\n" + VISUAL)

# 6. BACKLOG：62 收口 + 65 新开
patch("AGENT_BACKLOG.md", [BACKLOG_CLOSE, BACKLOG_NOTE])
with io.open("AGENT_BACKLOG.md", "a", encoding="utf-8") as f:
    f.write(BACKLOG_65)

# 7. 人工清单
with io.open("docs/MANUAL_TEST_v1.4.9_round3.md", "a", encoding="utf-8") as f:
    f.write("\n" + MANUAL)

print("R43 七份台账已写入")

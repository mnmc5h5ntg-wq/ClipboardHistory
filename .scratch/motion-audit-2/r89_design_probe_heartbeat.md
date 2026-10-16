# R89 预备（读代码得到的设计，不是结论）：BACKLOG 122 的每条判据心跳该挂在哪

## 已经存在的东西（本轮读到的，别重做）

1. `UIInteractionProbeTests.swift` 文件级已经有一个 `emit(_:)`：
   ```swift
   /// stderr 是无缓冲的：探针被监视线程/超时杀掉时，已经写出的行还在，`print` 的会丢。
   private func emit(_ string: String) {
       FileHandle.standardError.write((string + "\n").data(using: .utf8)!)
   }
   ```
   ⇒ **它写的是 stderr**，而 CI 那一步是 `swift test … > /tmp/ui.log 2>&1` ⇒ stderr 与 stdout 进同一个文件。
   `FileHandle.write` 是直接 `write(2)`，不经 stdio 缓冲 ⇒ SIGKILL 不会带走它。
   ⇒ 这条通道**本来就能活过看门狗**。R88 我把它记成"要么文件通道、要么没有"，那是漏看了这一条。
2. `CaptureReadings.emit` 是"两条腿"（stdout 整行一次 write + 文件），并且为并发加了进程内锁
   （R79/R81：`print` 把内容与换行分两次 write，两条读数会被缝成一行）。
   ⇒ 若走文件通道，必须复用这一套而不是新写一份。

## 设计（R89 要判的三件事）

| # | 问题 | 为什么不能想当然 |
|---|---|---|
| A | 心跳挂在**每条用例开头**，还是挂在 `setUpWithError()`？ | 11 处手写 = 新增一条判据就会漏（R10 立的规矩是"名单从产品推导"）。`setUp` 每例必到、且拿得到当前用例名 ⇒ 一处改动覆盖 11 条。要先实测 `setUpWithError` 里能不能取到用例名（Swift 6 的 `XCTestCase` 没有公开 `name`，可能要 KVC 或 `invocation`） |
| B | stderr 那条腿在 **runner** 上真能留住吗？ | 本机 spike 的 ui-40.log 里一条探针行都没有 —— 但那可能是"第一条用例（字母序 `testAccessibilityTreeCoverage`）在 emit 之前就挂了"，两种解释要分开：给 setUp 加心跳后重跑同一形状（120s kill），看第一行心跳在不在 |
| C | 有了心跳，`ui_probe_report.py` 的哪一格升级？ | `UI_PROBE_START_LINES_LOST`（R88 新加）应升级为"点名最后一条有心跳、没有结论的用例"；而 R88 的 `--runner-alive` 那一格仍要留着 —— 它管的是"日志的沉默能不能信"，心跳管的是"信了之后是谁" |

## 不许的处置

- 把心跳写成"每条用例里手动加一行"（A 的失败形态）；
- 用 stdout 而不是 stderr（R88 已证明它会被整块带走）；
- 先改 `ui_probe_report.py` 再去看心跳在不在（顺序反了 —— 那会让报告器替一个不存在的通道签字）。

## 实测（2026-10-16 07:56，仓库外的孤立 SwiftPM 包 `/tmp/namepkg`，不是猜的）

问题 A 已经有答案：**`setUpWithError()` 里能取到当前用例名，一处改动覆盖全部用例。**

```
HEARTBEAT describing=NameProbe | invocation=testAlphaProbeAndReturnError: | description=-[NameProbe testAlphaProbe]
HEARTBEAT describing=NameProbe | invocation=testBetaProbeAndReturnError:  | description=-[NameProbe testBetaProbe]
```

- `self.description` 是最干净的一条：`-[类名 用例名]`，与 XCTest 自己打的 `Test Case '-[…]' started.`
  **同一个名字空间** ⇒ `ui_probe_report.py` 现有的 `CASE` 正则可以直接复用，不用新增第二种名字。
- `invocation.selectorName` 编译不过（Swift 的 NSInvocation 没这个成员），要用
  `NSStringFromSelector(inv.selector)`，而且它带 `AndReturnError:` 后缀 ⇒ 别拿它当用例名。
- `String(describing: type(of: self))` 只有类名，没有用例名 ⇒ 不够。
- 心跳必须**整行一次** `FileHandle.standardError.write`（R81 那一课的同一个坑：
  内容与换行分两次写，并发下会被缝进别人的行）。
- 还要一格守卫：`description` 里取不出 `test…` 名字时，心跳要自己说"取不到"，
  不许静默写一条没有名字的行（否则 122 变成"有通道没读数"那一族）。

⇒ 剩下的只有问题 B（runner 上这条腿到底留不留得住）—— 那要等 R88 那三次 CI 落地才知道，
而它恰好就是本轮 ① 要读的东西。

## 顺带量到的一条（BACKLOG 106 的语料测量必须先抄这个，别自己发明谓词）

浮层的候选不是"全文包含"，读代码得到的是（`QuickPickModel.filtered`）：

- 匹配 `entry.shortPreview`（= `content.preview`），**不是整段正文**；
- 外加 `sourceAppName`；`.file` 再匹配 `lastPathComponent`；`.text` / `.image` 走 preview 那一支；
- `localizedCaseInsensitiveContains`（与侧栏 `HistoryStore.filteredEntries` 同一套，刻意的）；
- 候选还有**上限**：无查询词 12 条、有查询词 60 条（`maximumUnfilteredCount` / `maximumFilteredCount`）。

⇒ 106 那句"每多打一个字候选集变小的比例"必须按**这个**谓词与**这个**上限量：
用全文包含会低估收敛（正文比 preview 长），而不加 12/60 的截断会把"看起来没变"
误读成"没收敛"——上限本身就是"重排到底看不看得见"的一部分。

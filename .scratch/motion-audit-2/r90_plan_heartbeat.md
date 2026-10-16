# R90 的施工单（BACKLOG 122 · 每条判据一行心跳）——本轮不落地，先把形状钉死

依据：`r89_design_probe_heartbeat.md`（A 已被仓库外孤立包实测回答：`setUpWithError()` 里
`self.description` == `-[UIInteractionProbeTests testName]`，一处改动覆盖 11 条）。

## 1. 产品侧（`ClipboardHistory/Tests/ClipboardHistoryAppTests/UIInteractionProbeTests.swift`）

`emit(_:)` 是**文件级** private func（`:1323`，写 stderr、不经 stdio 块缓冲），类里直接可用。
在 `final class UIInteractionProbeTests` 顶部加：

```swift
    /// R90 / BACKLOG 122 · 每条判据开头一行心跳。
    /// 为什么要它：`swift test` 的 `Test Case … started.` 走 stdout 的**块缓冲**，
    /// 被 `kill -9` 收掉时整块丢失（R88 实测：日志停在 119 字节，而用例还在跑）。
    /// stderr 是直接 `write(2)` ⇒ 活得过看门狗，于是"被收掉时正在跑哪一条"第一次能点名。
    /// 挂在 `setUpWithError` 而不是 11 条用例里各手写一行：新增判据不会漏（R10 的规矩）。
    override func setUpWithError() throws {
        emit("PROBE_HEARTBEAT \(self.description)")
        try super.setUpWithError()
    }
```

**不许**顺手把 `emit` 改成 stdout、也不许给它加锁（R79/R81 那条"两行缝成一行"的教训只发生在
`print` 分两次 write 上；这里一次 write 一整行）。

## 2. 报告侧（`scripts/ui_probe_report.py`）

新增一条正则与一格升级，**保留** R88 的 `--runner-alive` 三岔（它管"沉默能不能信"，心跳管"信了之后是谁"）：

```python
HEARTBEAT = re.compile(r"PROBE_HEARTBEAT -\[[^\]]*?\b([A-Za-z0-9_]+)\]")
```

- 心跳集合 `beaten`：开了口（有心跳）的用例。
- `UI_PROBE_HUNG=<name>` 的依据从"started 差集"升级成**优先用心跳差集**（`beaten - concluded`），
  心跳差集为空而 started 差集非空时仍报 started（两条通道谁有证据用谁，但要说清用的谁）。
- 新增一行 `UI_PROBE_CHANNELS started=N heartbeat=M`：两条通道各给了多少证据。
  **为什么必须显式分开**：R88 的教训是"一条通道坏了会被读成产品的结论"，
  两条通道混在一个差集里就是同一个错的温和版。
- 若 `M == 0`（这一卷一条心跳都没有）⇒ 说明心跳那条腿在 runner 上没活下来，
  必须打 `UI_PROBE_NO_HEARTBEAT=1` 并让 `--runner-alive=1` 时判**不有名**（红），
  因为"我加了心跳而它没出现"是关于仪器的结论，不能悄悄退回 started 通道。

## 3. 判据侧（`scripts/tests/test_ui_probe_report.py`）至少四格

1. 只有心跳、没有 started/concluded ⇒ 点名挂死的那条 + `UI_PROBE_CHANNELS`；
2. 心跳与 started 都有 ⇒ 用心跳，且 `UI_PROBE_HUNG` 只出现一次（不许两条通道各报一遍）；
3. started 与心跳**互相矛盾**（started 说 A 在跑、心跳说 B 在跑）⇒ 红，并打出 `UI_PROBE_CHANNELS_CONTRADICT`；
4. `M == 0` 且 runner 活着 ⇒ `UI_PROBE_NO_HEARTBEAT=1` 且不给名字。

## 4. 牙（变异电池，编号从 M497 起）

- M497 删掉 `setUpWithError` 里那行心跳 ⇒ 覆盖它的那条守卫必须红；
- M498 把心跳改成 `print` ⇒ 必须红（stdout 会被整块带走，这条是本轮的全部理由）；
- M499 把 `ui_probe_report.py` 里"心跳优先"改成"started 优先" ⇒ 矛盾那一格必须红；
- M500 让 `M == 0` 时静默退回 started ⇒ `UI_PROBE_NO_HEARTBEAT` 那一格必须红。

## 5. 顺序（不许反）

先在本机跑一次"120 秒 kill"形状的 spike，确认心跳第一行**在**日志里；
再改 `ui_probe_report.py`；最后才登记 BACKLOG 122 的结案。
反过来就是"让报告器替一个不存在的通道签字"（R88 的错）。

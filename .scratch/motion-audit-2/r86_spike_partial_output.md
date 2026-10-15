# R86 的 spike：不动判据代码，能不能给"在屏那一卷被看门狗收掉"这件事一个名字？

## 为什么要先 spike

BACKLOG 92（R62 开）说的是同一件事的两种坏法：`On-screen interaction probes` 那一步在 runner 上
`ui suite exit: 137 executed: 0 已下结论的用例: 0`，而那一步顺手留了一句解释
（"在屏探针在无头 runner 上不可用"）⇒ **整卷成了免检牌**，R61 修的侧栏跟随选中那三条行为判据
的回归在 CI 上一条都没跑，作业还是绿的。

要修的是"没跑完也要有名字"。最省的做法是**让测试自己打点**（每条用例入口写一行 `STARTED=`），
但那是 11 处产品测试代码。先量一下"只读日志"够不够 —— 如果 `swift test` 的
`Test Case ... started.` 在 `kill -9` 之后还在文件里，那就不需要动测试。

## 实测（本机，2026-10-15 21:13，同一提交 `0f0cced`）

命令刻意用**捕获卷**而不是在屏卷：在屏卷会开真窗口抢前台（现在是凌晨，不该为一次 spike 打扰），
而这里要问的只是"**SIGKILL 之后，XCTest 的 started 行还在不在文件里**"——
这与是哪一卷无关，两卷走的是同一个 `swift test` 输出通道。

```
( swift test --filter UICaptureTests > log 2>&1 & pid=$!; sleep 50; kill -9 $pid )
exit=137                                   # 与 CI 那一步看到的数字同形
grep -c "Test Case.*started"    → 13
grep -cE "Test Case.*(passed|failed|skipped)" → 12
日志最后一条 started = testDisabledToggleAndFailureReceiptAreVisible（它没有结论行）
```

⇒ **够了**：`started` 减去 `concluded` 正好点名"被收掉时正在跑的那一条"，
不需要测试自己打点。本轮因此只加一个读日志的脚本 + CI 两步接线，**产品与测试代码零改动**。

## 这个 spike 没有证明的那半（如实记账）

1. **没证明 runner 上也是如此**。runner 的 stdout 成块丢（R64 / R84 各现场一次）恰恰会把
   `started` 行丢掉而留下结论行 —— 那时差集会**假报**一条挂死的用例。
   ⇒ 所以脚本把"有结论却没有它的 started 行"判成 `UI_PROBE_CONCLUDED_WITHOUT_START` 并**红**，
   而不是继续给一个名字。这一格是这一轮唯一能挡住"日志不完整冒充点名成功"的形状。
2. **没证明在屏卷的第一条用例就是挂死点**。CI 那一步现在只打 `已下结论的用例: 0`，
   连"有没有 started 行"都没报 ⇒ 本轮接上之后，**下一次 CI 才知道答案**
   （三种可能：挂在哪条 / 一条都没开始 / 两遍并进来导致集合自相矛盾而红）。
   在那之前 92 不结案。
3. **50 秒这个数是本机捕获卷的节奏**，不是在屏卷的；在屏卷的看门狗是 240 秒。
   这条差别不影响上面那个问题（"kill 之后行还在不在"），但别把它读成"我复现了 CI 的挂死"。

# R87 读 R86 的 CI（run 38811457259 · #235 · commit f18c52b · 21:38:55→21:53 · build-and-test = **failure**）

失败的步骤是 **`Motion coverage floor`**（不是我本轮新接的那道 UI 硬门）。两件事同时发生：

1. 常驻循环那一族在 runner 上**把产品判成了红**（第三遍），而位置尺在同一卷上说亮带走完了整幅；
2. 在屏那一卷的停机**第一次有了名字** —— 而那个名字把 BACKLOG 93 的预测推翻了一半。

## 1. coverage 与行程：同一份产品代码，两把尺给相反答案

```
MOTION_SHIMMER 扫 帧数=23 变化帧对=1 峰值=0.028 采样≈98ms coverage=0.032(地板 0.50) 记录时长=2324ms 判定=只动了一下
MOTION_SHIMMER_WITNESS 等节拍证人(30Hz 抬升 0.12，与产品同数字) 帧对=25 在变=6 峰值=0.028 coverage=0.671 判定=一直在动
MOTION_SHIMMER_WITNESS 粗节拍证人(20Hz 抬升 0.45) 帧对=31 在变=23 峰值=0.040 coverage=1.000 判定=一直在动
MOTION_SHIMMER_BAND 帧=23 比例=1pt≈1.00px 可用帧=12 丢掉=11 同帧绝对中心最大散布=1.0pt 归一化散布=0.450 行程=134.0pt 判定=整组一条带
MOTION_SHIMMER_BAND_SAMPLE 可用帧首=[21.0, 21.0, 21.0] 末=[155.0, 155.0, 155.0]
MOTION_SHIMMER_STATE 判定=productRed 原因=-
MOTION_SHIMMER_BAND_STATE 判定=notRunEnvironment 原因=loop-not-capable
MOTION_FLOOR_SUITE_RED=1 … 红的用例=testSkeletonSweepActuallySweeps
MOTION_FLOOR_LOOP_RED_NAMED=skeleton-loop=productRed
MOTION_FLOOR_LOOP_NOT_JUDGED=skeleton-band-position=loop-not-capable
MOTION_FLOOR_REDS=1
```

**四遍读数并排（R84 换画法之后，产品代码一行没改；最后一行是本轮 R87 的全量验证那一遍）**：

| run | 帧数 | 变化帧对 | coverage | 可用帧 | 行程 | 处置 |
|---|---|---|---|---|---|---|
| 38798408040 (R84) | 24 | 2 | 0.522 | 11 | 109.0pt | ok |
| 38805382593 (R85) | 22 | 2 | 0.842 | 12 | 134.0pt | ok |
| 38811457259 (R86) | 23 | **1** | **0.032** | 12 | **134.0pt** | **productRed（CI 红）** |
| 本机 R87 验证那一遍 | 48 | 20 | 1.000 | 7 | 121.5pt | ok |

⇒ coverage 的支撑是 **1–2 个变化帧对**（分母 22–24 对里只有 1–2 对在变），
而行程的支撑是 runner 三遍的 **11–12 个可用帧**（本机那一遍 7 帧，也够），且它在两台机器、四遍里都落在 109–134pt。
"亮带从 x=21pt 走到 x=155pt"是**位置**证据，它不依赖采样网格；
coverage 依赖。⇒ 本轮把"两把尺矛盾时谁签字"写进判据（`loopAdjudication` 的 `travel` 入参）。

## 2. 在屏那一卷：停机有了名字，而名字推翻了我上一轮登记的预测

```
UI_PROBE_PROGRESS started=0 concluded=0
UI_PROBE_NO_CASE_STARTED=1 （进程在第一条用例开口之前就死了：看门狗收掉的是启动阶段，不是某条判据）
UI_PROBE_NAMED=1
PROBE_COVERAGE_SUMMARY 源码用例=11 登记=11 runner可跑=0 runner不可跑=11 本次下结论=0 红=0
```

R86 我在 BACKLOG 93 里**预先登记**了三种结果各意味着什么，其中一条是：
"若报 `UI_PROBE_HUNG=testAccessibilityTreeCoverage` 就证实挂在字母序第一条用例内部"。
实际报的是 `NO_CASE_STARTED` ⇒ 原文那条"挂在第一条用例内部"的推断**没有被证实**，
它连"XCTest 有没有开始报用例"都没到。

**但这一格不能就这么收**（这是本轮最该诚实的地方）：`started=0` 有两种成因，
而这一份日志分不开它们：

* ① 进程真的在第一条用例开口之前就死了（启动/会话层）；
* ② 用例其实跑了，但 `swift test` 的 stdout 在 `kill -9` 时整块丢了
  —— 这一族本仓库见过两次（R64 的捕获卷、R84 的动效卷），而 `> /tmp/ui.log 2>&1` 是重定向到文件，
  块缓冲被 SIGKILL 掐掉是**默认行为**，本机那次 spike 只证明了"能留住"（13 行），
  没证明"每次都留得住"。

⇒ ②如果为真，那 `UI_PROBE_NO_CASE_STARTED=1` 就是一句关于产品的假话（它说的是"没开始"，
而真相是"开始了我没看见"）。这一格交给 R88：在屏那一步同时看**产物通道**
（`/tmp/shots-ci` 里有没有帧、探针有没有写 readings），
有帧没日志 ⇒ ②；没帧没日志 ⇒ ①。这是 BACKLOG 93 剩下的那一步，也是它不结案的理由。

## 3. 其余步骤（一次读完，免得下次靠记忆）

* `Capture gate`：`passed=38 skipped=9 failed=0 有名字的红=0 NOT_RUN=54` ⇒ 捕获这一族照旧绿，
  而那五条在 runner 上确实 skip（116 剩下的那半句仍然成立）。
* `ui suite exit: 137 executed: 0 已下结论的用例: 0` ⇒ BACKLOG 92 的形状没变（它本来就没结案）。
* 动效那一步 `motion suite exit: 1` —— 红的是判据本身，闸门把它翻译成了有名字的 `SUITE_RED`
  + `LOOP_RED_NAMED`，这正是 R85 那层要的形状（红有名字、有人负责）。

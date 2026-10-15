# R86 读 R85 的 CI（run 38805382593 · #234 · commit 0f0cced · 20:51:59→21:04 · build-and-test = success）

这是**常驻循环那一族第一次在 runner 上自己说"今天判到了"**，也是 `loops` 那一层第一次判自己。

## 1. 状态行与 `loops` 那一层（R85 新加的，本轮第一次在 runner 上落地）

```
MOTION_SHIMMER_STATE 判定=ok 原因=-
MOTION_SHIMMER_BAND_STATE 判定=ok 原因=-
MOTION_FLOOR_FACTS judged=4/4 executed=54 not-run=- summary=detail-kind-change=3 empty-state=4 notice-banner=2 notice-banner-dismiss=3 红的用例=- 汇总行报红=0
MOTION_FLOOR_LOOP_JUDGED=skeleton-loop 这一族今天判到了（状态 ok）
MOTION_FLOOR_LOOP_JUDGED=skeleton-band-position 这一族今天判到了（状态 ok）
MOTION_FLOOR_SUITE_CLEAN=0 这一卷没有红用例（汇总行也没说有）
MOTION_FLOOR_OK=4/4 全部臂都在登记之内
MOTION_FLOOR_REDS=0
```

⇒ 结案 118 的那半句"整族没说一句话就会红"已经在 runner 上生效：
两行状态都读到了，闸门两行都点了名。

## 2. 扫光那一族（三遍 → 四遍并排，119 的第三个数据点）

| run | 画法 | 产品 coverage | 等节拍证人 | 位置判据 | 处置 |
|---|---|---|---|---|---|
| R82 38781113064 | 每根条各扫各的 | 0.000（0/21 对） | 0.284 | — | 点名环境 |
| R83 38786182395 | 每根条各扫各的 | 0.050（1/22 对） | 0.837 | — | 判产品红 |
| R84 38798408040 | **整组一条带** | 0.522（2/24 对，采样≈112ms） | 0.594 | 可用帧 11 / 散布 1.0pt | 判绿 |
| R85 38805382593 | **整组一条带** | **0.842**（2/22 对，峰值 0.016，采样≈103ms） | — | **可用帧 12 / 丢掉 10 / 散布 1.0pt / 归一化 0.450 / 行程 134.0pt / 判定=整组一条带** | **判绿** |

⇒ **两遍连续判绿**，而且第二遍比第一遍高出一大截（0.522 → 0.842）。
这仍然**不**构成把 `must_judge` 改成 true 的理由：0.522 与 0.842 之间的跨度本身就说明
这一支的读数在 runner 上还不稳（同一种画法、同一台机器类别，两遍差 0.32）。
R38 那句话在这里的读法是反过来的——**波动大恰恰是"还不能当硬门"的证据**，不是"已经稳了"。
下一格（119 的待办）要的"几遍读数才配定罪"，现在有了 4 个数据点：0.000 / 0.050 / 0.522 / 0.842，
前两个属于旧画法，后两个属于新画法 ⇒ 新画法两遍都在地板上，但**分布宽度 0.32** 还没量过第三遍。

## 3. 仍然没跑的那一卷（BACKLOG 92 的形状，本轮改的就是它）

```
ui suite exit: 137  executed: 0  skipped: ?  已下结论的用例: 0
```

R85 之前这一步到此为止。本轮（R86）加了 `scripts/ui_probe_report.py`：
它把 `Test Case ... started` 与有结论的行做差，输出 `UI_PROBE_HUNG=<用例名>` /
`UI_PROBE_NO_CASE_STARTED=1` / `UI_PROBE_ALL_CONCLUDED=1`，
而"给不出名字"（日志不完整或喂错了文件）会**红**。⇒ 下一次 CI 才知道 runner 上到底是
"第一条就挂住"还是"一条都没开始"。

## 4. 读 CI 时踩到的一个新坑（值得单独记一条）

`gh run view --log` 把**所有步骤**拼在一起，而 `MOTION_SHIMMER_STATE` 这类状态行会在
两个步骤里各出现一次、取值还不同：

| 步骤 | 行 |
|---|---|
| `Swift tests (executed-count gate)`（全量卷，没设开关） | `MOTION_SHIMMER_STATE 判定=skipped 原因=capability-gate` |
| `Motion filmstrip (report-only)`（设了开关那一卷） | `MOTION_SHIMMER_STATE 判定=ok 原因=-` |

⇒ 我第一遍 grep 整份日志时读到"同一族既 ok 又 skipped"，差点把它当成 R85 那层的排序 bug
（闸门是"按最后一条判"）。按步骤名过滤之后才看清：**两条行来自两次不同的运行**。
闸门读的是 `/tmp/motion.log`（只有设了开关那一卷写它），所以它没被骗 —— 会被骗的是读日志的人。
⇒ 台账里写一句：读 CI 必须**按步骤名**过滤，跨步骤 grep 出来的"自相矛盾"多半是拿错了范围。

## 5. 捕获那一步（顺带，与 116 有关）

```
CAPTURE_GATE_CHANNELS stdout=1 readings=404 行 补回=0 行（stdout 没有的读数）
CAPTURE_GATE_CASES passed=38 skipped=9 failed=0 有名字的红=0 NOT_RUN=54
  被 skip 的用例（skip 不是通过，它只是不红）：testDarkSettingsSidebarTextIsACountedBlindSpot testInkDirectionRuler…
  TEXT_SIDE_NOT_RUN settings-shortcuts dark 侧栏列读到 0 个偏离像素（同帧内容区读到 0 个）
```

⇒ 116 原文那句"那五条没有一行为什么今天没跑"在**捕获这一族已经不成立**：
闸门不但列出了它们的名字，还带着读数与原因。116 剩下的那半句仍然成立，见
`r86_skip_readings.md`（"闸门只报它找到的 NOT_RUN，不报它没找到的那些"）。

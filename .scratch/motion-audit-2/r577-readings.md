# R577 读数台账（工作笔记，随本轮台账笔提交；所有串都由落盘文件派生，不是手打的）

## ⓪ CI（`scripts/ci_read.py` + `gh run view --log` 落盘 `/tmp/r577/ci-41979751613.log`，摘录 `/tmp/r577/ci_extract.txt`，失败步骤清单 `/tmp/r577_steps.txt`）

| run | commit | 结论 | 全部失败步骤（逐字） |
| --- | --- | --- | --- |
| `41979751613` | `ae11a92`（R576 主笔） | `completed / failure` | `STEP[15] Swift tests (executed-count gate)`、`STEP[17] Capture gate (unregistered reds must be zero)`、`STEP[19] Motion coverage floor`（**`STEP[18]` 绿**） |
| `41980266648` | `c013d5d`（R576 补记笔） | `in_progress / conclusion 空` | **未到数**（不轮询、不读成绿或红） |

- 日志字节数 `3,281,881` ⇒ "不在失败列表里"这次可以当读数用。步骤名这次**可用**（`field2` 不是全量 `UNKNOWN STEP`），但正文仍按 emit 通道串取（同一把尺两种形状都验过才敢换）。
- 上轮那张按机器登记的表在 runner 上：`LAYER_TREE_COLD 树=主窗 倍率=1.00x 实测=层树没建 登记=层树没建 判=与登记一致`、`树=浮层 … 判=与登记一致`、`LAYER_TREE_COLD_SUMMARY 倍率=1.00x 主窗甲=层树没建 主窗甲第二次=层树没建 主窗乙=层树建了没画进料 主窗丙=层树没建 浮层甲=层树建了没画进料 夹具那步之后未画比例=0.8495` ⇒ **登记值没翻面，本机一字未改**。
- 同一跑的解释②：`LAYER_TREE_COLD_MECH 解释=②置层要等上屏 判=被支持_甲无树而乙有树` ⇒ 本轮被自己的空刀推翻（**过度归因**：甲臂=夹具树、乙臂=判据树，且乙臂把 `orderFront` 与 `display()` 捆在一起）。
- `executed=` 先读：判据卷 `Executed 230 tests, with 34 tests skipped and 14 failures`；全量 `Executed 1437 tests, with 89 tests skipped and 14 failures`；动效卷 `Executed 79 tests, with 33 tests skipped and 0 failures`；**`ui suite exit: 137  executed: 0  skipped: ?  已下结论的用例: 8`**。
- `CAPTURE_GATE_CASES passed=196 skipped=33 failed=1 有名字的红=1 类未知名单=0 NOT_RUN=183`；`MOTION_GATE_CASES passed=47 skipped=46 failed=0 有名字的红=0 类未知名单=0 NOT_RUN=182`；`MOTION_FLOOR_SUITE_RED=1`（上轮两跑是 3 与 2 ⇒ 这一格在漂，只现读不动它）；`MOTION_FLOOR_BAD_REASON empty-state 的理由是 witness-snaps-here，而登记过的是 无 ⇒ 同一臂换了一种坏法 = 新缺陷`。
- `PROBE_DOMAIN_NOT_RUN 放行 22 条`、`PROBE_COVERAGE_SUMMARY 源码用例=14 登记=14`、`PROBE_DOMAIN 问了 44 条、判成 20 条`。
- 电池：`Ran 725 tests in 115.403s` / `python cases: 725`，`STEP[9]` 不在失败列表 ⇒ 脚本电池由那一跑自己签绿。
- D12 映射表第三次逐字相同：`D12_CHANNEL_MAP_SUMMARY 条=8 runner可判=0 只能真机=1 今天无证人=7 角度驱动文件数=0 折叠路径文件数=2 折叠期改alpha文件数=0 真机键=关 离屏alpha通道采样=20160 不透明=2547 全透明=16733 产物采样=26320 产物全透明=0 窗口宽=750.0`。
- **红名单归因对照**：`41979751613` 6 朵 = `MotionFilmstripTests.testEmptyStateStillFadesWhenMotionIsReduced`、`UICaptureTests.testActionableInkStaysAboveTheLegibilityFloor`、`testCaptionTextStaysOnTheSecondaryTier`、`testDetailAreaHasASingleLeftAxis`、`testDetailStatusBarShowsTheRealSourceAppIconOnlyWhenAttributed`、`testQuickPickKeyboardHintClearsTheContrastFloor`；上轮 `41843233864` 8 朵、`41845985973` 7 朵 ⇒ **本轮没有新名字**（少掉的两朵 `testDetailEmptyToContentCrossfadeIsMeasuredOrDeclaredBlind`、`testMarkdownModeLabelChangeIsAVisibleProcess` 都是"有时出现"的样本红）⇒ 写"没有新红"，不写"红变少了"。

## ② 本轮新判据（本机 2x，`/tmp/r577/arms3.log` 与 `/tmp/r577/criteria.log`）

```
SAME_TREE_ONSCREEN 臂=甲从未上屏 子层=-1 contents=无 不透明=-1 全透明=-1 采样=0
SAME_TREE_ONSCREEN 臂=甲第二次另一棵 子层=-1 contents=无 不透明=-1 全透明=-1 采样=0
SAME_TREE_ONSCREEN 臂=乙A只上屏 子层=2 contents=无 不透明=20160 全透明=0 采样=20160
SAME_TREE_ONSCREEN 臂=乙B只走显示通路 子层=2 contents=无 不透明=20160 全透明=0 采样=20160
SAME_TREE_ONSCREEN 臂=乙C只跑runloop 子层=2 contents=无 不透明=20160 全透明=0 采样=20160
SAME_TREE_ONSCREEN 臂=乙D上屏但不跑runloop 子层=-1 contents=无 不透明=-1 全透明=-1 采样=0
SAME_TREE_ONSCREEN 臂=乙E走display但不跑runloop 子层=2 contents=无 不透明=20160 全透明=0 采样=20160
SAME_TREE_ONSCREEN 臂=诊断_同一棵上屏之后 子层=2 contents=无 不透明=20160 全透明=0 采样=20160
SAME_TREE_ONSCREEN 臂=诊断_同一棵再走显示通路 子层=2 contents=无 不透明=20160 全透明=0 采样=20160
EXPLANATION2 倍率=2.00x 实测=被否_不上屏只走display就建得出而上屏不display建不出 声明=被否_不上屏只走display就建得出而上屏不display建不出 判=与声明一致
```
⇒ **②被否**：`乙E`（不上屏、不跑 runloop、只调一次 `window.display()`）有树，而 `乙D`（上了屏、一次 display 都不调）没树 ⇒ 层树等的是**一次显示通路**（显式 `display()`，或 runloop 里 AppKit 自己那遍 —— `乙C` 也 `子层=2`），不是"上屏"。`contents` 那一列**四臂全 `无`** ⇒ 它今天没参与判定（下一轮要说清它什么时候才有资格进分类器）。

## 刀（`/tmp/r577/knives.log`）

- **M1516 第一次落下 = PASSED（空刀）**：刀落在"乙B（`display()` + 跑 runloop）"的 `display()` 那一行 ⇒ 摘掉之后 `子层` 照旧 2 ⇒ **捆臂形状**里"有树"不是 `display()` 给的。⇒ 重测矩阵、重写分类器、把刀落在**乙E**那一步 ⇒ **M1516 CAUGHT、RESTORE_CLEAN=yes**。
- **M1517 CAUGHT、RESTORE_CLEAN=yes**：把分类器里"所有臂逐字相同 ⇒ 尺坏"那一支改成误判成"被否" ⇒ 合成负对照当场红。
- 下一轮从 **M1518** 起。

## ③ 漂移那条（具名 `FRAME_ALPHA_TOTAL_CLEAR_DRIFT_NOT_A_WITNESS`）

- 跨轮：同码同机 `全透明 17180 → 17261`（+81 ≈ 0.4%），`不透明=2068` 未变。
- 本轮新读数：`同遍两读数相同=1` ⇒ **同一进程内两棵独立构造的树读到逐字相同** ⇒ 漂移在跨会话状态，不在这个量自己的分辨率里。
- ⇒ 不能当证人、不许放地板；与 640 那句"`CHANGED=0` 不是漂移反证"是两件事（帧基线像素口径 vs 通道侧 alpha 三分数口径）；不构成"捕获通道不稳"的结论（645/648 那一族）。**有读数、无刀** ⇒ 具名"无刀、靠账"。

## ④ amend 证人重抄（本轮现读）

```
AGENT_STATE.md               4735598=1  ae11a92=2
AGENT_UI_AUDIT.md            4735598=0  ae11a92=0
AGENT_VISUAL_ITERATION.md    4735598=0  ae11a92=0
CHANGELOG.md                 4735598=0  ae11a92=0
AGENT_FINAL_REPORT.md        4735598=0  ae11a92=0
AGENT_BACKLOG.md             4735598=0  ae11a92=0
AGENT_DECISIONS.md           4735598=0  ae11a92=0
git log: c013d5d R576 补记… / ae11a92 R576：… / 3bafac2 R575 补记…
```
⇒ STATE 那一处 = 上轮 ⑩ 自己那句"全 0"的正文 ⇒ **改前的 0 是真的，句子不带取数时刻就会被自己作废**。

## ⑥ 禁碰证人（本轮碰的是捕获夹具那份测试文件）

`TRANSPARENCY_STATE … 带内最小alpha=255 半透明样本=0/39342 洞范围=无`、`TRANSPARENCY_HITTEST … 底衬0/容器3/内容0 底衬自身 hitTest=让位`（两条与 R576 逐字同），第三条走真机键 `CLIPBOARD_HISTORY_UI_REALSCREEN=1`（本轮单独跑到数，见 `/tmp/r577/realscreen.log`）。⇒ **禁碰数不抬（仍 14 面）**。

# -*- coding: utf-8 -*-
"""R558 ⓪ 开工节：CI 读单（三跑红名 + 两笔 cancelled + 本轮四跑未读）+ 基线全现读 + 禁碰逐字抄。"""
import io

P = 'AGENT_STATE.md'
s = io.open(P, encoding='utf-8').read()

anchor = u'## R557 状态（2026-11-02 · 第 556 轮 / Round 554 · 产品 2 文件 + 判据 2 文件 + 三把刀）'
assert s.count(anchor) == 1, s.count(anchor)

body = u"""## R558 ⓪ 开工（2026-11-02 · 第 557 轮 / Round 555 · CI 读单 + 基线全现读）

> 本节是**开工节**，不是轮次节（标题不写「状态」两字 —— `product_streak.py` 按第一个 `## Rnnn 状态（` 认当前轮）。

**前置实读**：`git log --oneline -3` = `ff15906` / `61285b6` / `5d05578`；已跟踪改动 **0**；ahead=**0**（HEAD=origin=`ff15906`）；`git rev-parse --short HEAD` 与 `origin/main` 同为 `ff15906`。

**① CI 读单（只登记、不轮询）**

R557 ⓪ 那三跑收口时到手，本轮逐条对照。三跑 conclusion 都是 **failure**，唯一失败步骤都是 **STEP[9] Release script tests**；步骤名通道这次仍是坏的（`41450045802` 的 `--log-failed` 13791/13791 行是 `UNKNOWN STEP`），正文靠 grep/emit 通道拿。**「不在失败列表里」不等于「没跑」** —— 本轮另用 `gh run view --json jobs` 把整张步骤表读全：STEP[1]–[8]、STEP[15]–[19]、STEP[38]–[39] 全 **success**，只有 STEP[10]–[14] 是 skipped。

| run ↔ commit | conclusion | 全部失败步骤 | STEP[9] 红名（逐条） |
| --- | --- | --- | --- |
| `41450045802 ↔ 5ba5b2f`（R556 刀表笔，同批覆盖产品笔 `1a7e31c`） | failure | STEP[9]；10–14 skipped；15–19 success | `Ran 695 tests in 108.977s` ⇒ `FAILED (failures=2, skipped=2)`：① `test_sources_cell_second_source…test_the_cell_agrees_with_its_own_source`（`0 != 1 : 报告里那一格与 git 派生的不一致`）② `test_skip_roster…test_the_roster_matches_what_this_machine_actually_skips`（`None is not true : 内层没有结论行`） |
| `41450081248 ↔ 680aea3`（R556 台账笔） | failure | 同上 | `Ran 695 tests in 119.049s` ⇒ `FAILED (failures=3, skipped=2)`：① `test_final_report_headline…test_the_sources_cell_agrees_with_git` ② `test_the_cell_agrees_with_its_own_source` ③ skip_roster 借红 |
| `41450601769 ↔ ccab101`（R556 补记笔） | failure | 同上 | `Ran 695 tests in 122.714s` ⇒ `FAILED (failures=3, skipped=2)`：同 680aea3 三条 |

- **对照结论（不冒充读数）**：这三跑推的时候 R557 的台账还没落盘 ⇒ sources-cell 那一族是**注定时序红**（账上格 = R556/`1a7e31c`，git 已指到更新的产品笔），不是产品回归；skip_roster 是它的**借红**（见 634）。所以「STEP[9] 到没转绿」**本轮无从判定** —— 能给这一格作证的只有台账之后的跑，而本轮四跑（`41464892684↔ce4da8f`、`41465486002↔5d05578`、`41467173705↔61285b6`、`41467585182↔ff15906`）取号时**全部 in_progress**（已等 1209/989/342/192s，`同workflow前面=0/1/2/3` ⇒ macOS runner 在串行排队）⇒ 四跑一律 **NOT-RUN**，R559 必读。
- **cancelled 两笔（具名 NOT-RUN，永不重开）**：`41452722560 ↔ 58851c2`、`41455782587 ↔ 598b253` —— 各跑 15m01s 被取消、失败步骤 0 条、`--log-failed` 0 行；对后者取正文直接 `log not found: 125311960175`。这是「读到 0 行」的第四种坏法（作业被取消 ⇒ 日志从未落盘）。
- **无新红的面**：三跑 STEP[15]（Swift 卷 executed-count 门）/ STEP[16]（Motion gate）/ STEP[17]（Capture gate）/ STEP[18]（探针覆盖地板）/ STEP[19]（Motion 覆盖地板）**全 success** ⇒ 569 的倍率口径在 runner 上连三跑无红（第四、五、六次佐证）；622/624/627 **没有新红**。⚠ 但它们的**具体毫秒读数本轮拿不到**：`--log-failed` 只含失败步骤正文，STEP[16]/[18] 的正文要 `--log` 全量才有 ⇒ 本轮只登「无红」，不写值。

**② 基线（本轮全部现读，不抄上一轮）**：帧 **354**（`docs/frame_baseline.json` 现数）；预检 **tables=345 covered=295 arms=757 bad=0**；`ARM_TOTAL files=438 arms=1244 dupes=0 repeats=0`；`HIDDEN_ARMS 表=432 可判=1183 rot=0 抽不出=6 已声明表=6 已声明死针=0 处置=ok`；清账 **162/63/0**；streak **1**（`python3 scripts/product_streak.py --streak-for 557` 现读，last=`2ca9501`/556 ⇒ 与 R557 台账的预期一致）；判据卷 **217/4 skipped/0**、全量 **1399/55/0（765.8s）**、电池 **695/5**、安装 **433=433**+`INSTALL_SIGNATURE=local` 均为 R557 收口现读，本轮动过判据/电池就重跑。

**③ 禁碰清单（现读逐字抄自 R557 节 ⑤ 与 R555 节，共 9 面）**：R546 登录失败图标、R547 默认排除行锁、R548 250pt 批量标题、R549 无序列表项目符 ⦁、R550 浮层提示「Esc」、R551 收藏星尺寸、R552 折叠过渡、R553 本机码签身份链、R555 星判据的捕获倍率口径。九面本轮一律不动；**4.5 地板、150 上限、120ms 阈值、Motion ≥2 帧地板、2x 的 8.0pt 跨度地板、1x 的 6.0pt 整行地板全部冻结不许降**。

**④ 本轮靶（头两格上一轮已定死，不重开讨论）**
- **(a) 629 按 (B)「换判据对象」落地。** 三个 runner 真数（`41450045802`/`41450081248`/`41450601769`）已经把 (A) 加密录制否掉：每格 22.6–28.1ms 够密，但 27 帧里**只有 2 格**相邻差非零、其余逐格 `0.0000` ⇒ 加密只多得零。所以判据要换对象：**「相邻差的非零计数」是「有没有插值」的代理量**，改成两端夹逼 —— 每帧分别量它离「触发前静置」与离「settle 后静置」的距离，**既不像前态也不像后态**的帧才算过程帧。`≥2` 这个数字不动（新口径下仍然要 ≥2 才放行），120ms 阈值、声明时长、`.contentFade` 0.20 一个字不改。落地带：新读数 emit、一把刀 M1446（把新尺退回旧口径 / 把中间帧抹平成硬切，必须红）、一条正对照（硬切臂必须读 0）。
- **(b) 634：把 `test_skip_roster` 的一格拆成两格。** 现在的形状是 `SKIPPED_SUMMARY` 只匹配 `OK (skipped=N)`，内层只要有任何一条红，汇总行就成 `FAILED (…)` ⇒ 这一格以「内层没有结论行」红，把**被观察者的红借成自己的缺席**。拆法：①「有没有汇总行」（真缺席 ⇒ 具名出口 NOT-RUN，不再冒充缺席）②「汇总是 FAILED」（ ⇒ 仍红，但正文必须原样带上内层汇总行与内层红名，不许再说「没跑完」）。同时把 `machine_key`/`machine_class` 读数打出来。**这一格不许放宽任何门、不许把红改成 skip。**
- **(c) 真实推进与换新类别**：(a) 是动效判据卷（R557 是隐私计数器，类别不同），(b) 是电池观察者本身 ⇒ 本轮产品面是否改动**先不承诺**；若 (a) 只换尺不动产品，就照实写「产品 0 文件」，不许为了「有推进」去碰禁碰面或动 `.contentFade`。
- 633 仍等用户人工回执；622/624/627 继续挂；628/625/626/569/616/632 已落地那半不重开；刀号 **M1446** 起（现读最高 `M1445`）；推送规矩 = **验证链跑完一次性 push，不分批**。

"""

s = s.replace(anchor, body + anchor, 1)
io.open(P, 'w', encoding='utf-8').write(s)
print('R558 ⓪ written')

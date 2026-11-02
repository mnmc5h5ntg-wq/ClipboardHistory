# -*- coding: utf-8 -*-
"""R562 台账（第 561 轮 / Round 559）：636 退场第一步落地 —— 三级列表夹具 + 正文列步进判据；产品 0 文件。

用法：`python3 ledgers_r562.py --check` 只验锚点与 NUM 是否填好；不带参数才真写七本账。
所有数字都是**现读**填进 NUM，没有一格从上一轮抄；派生格（streak / sources）一律**落盘之后**再现读。

R561 的自伤在这一支里被钉成代码：`fill()` 从前只查 `%(`，于是裸 `%s` 能一路落盘（同坑第四回）。
现在它两种形状都查 —— 写完还要再跑一次 `addendum_r562.py` 里那条回读计数。
"""
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

NUM = {
    "FULL": '1405/57/0（686.4s）',
    "INSTALL": '`INSTALL_RESULT=ok / INSTALL_SHA_MATCH=1 / INSTALL_ENTRIES=433=433 / SMOKE_OK=1 / INSTALL_SIGNATURE=local flags=0x0`（固定身份 ⇒ 授权可以跨轮活下来）（版本 1.4.8→1.4.8，PID→30437，启动晚于安装、exe 路径逐字对上，备份 `before-R562`）',
    "BATTERY": '696/5',
    "ABSENCE": 'ABSENCE_PENDING',
    "STREAK": 'STREAK_PENDING',
    "STREAK_RAW": 'STREAK_RAW_PENDING',
    "CAPTURE": '221/4 skipped/0 失败（675.1s）',
    "FRAMES": '356 张 —— update 之前 `COMPARED=356 CHANGED=0 MISSING=0 ADDED=2`（新增的两个名字逐字是 `detail-markdown-bullet-nested-720x520-light.png` / `…-dark.png`，**名单外一个帧也没有**），同一笔 `update` 之后复跑 `COMPARED=356 CHANGED=0 MISSING=0 ADDED=0`',
    "PRECHECK": 'tables=361 covered=295 arms=757 bad=0',
    "ARM": 'files=454 arms=1244 dupes=0 repeats=0',
    "HIDDEN": '表=448 可判=1183 rot=0 抽不出=6 已声明表=6 处置=ok',
    "CI_CLOSE": '**收口前复述 `queue`：`41519677393 ↔ f12f50d` = concluded success（已等 3591s）⇒ 三格当场从 NOT-RUN 转成读数，而且 `gh run view --json jobs` 现读 7/9/11/15/16/17/18/19 全部 `success`（不是从「不在失败名单」推的）。**⓪(a) 本轮最要紧的一条：R561 那把几何派生尺在 runner 上真的判到了** —— `HEAT_LEGEND_COVERAGE light 格色=6 图例色=5 缺=[] 格宽=11px 倍率=1.0x 网格下缘 y=164 实心判定 格6px/图例3px 地板 格4/图例4 每方块采样点 格9/图例9`（dark 同形，共 4 行，来自 `Offscreen frame capture` 与 `Swift tests` 两步），而 `HEAT_LEGEND_NOT_RUN` **没有一行** ⇒ 连续三跑（R559/R560/R561 那两跑）的 `scale-too-low` 出口断了，**R561 账上预测的「预期这一跑打 `HEAT_LEGEND_COVERAGE … 倍率=1.0x 地板 格4/图例4`」被 runner 逐字证实**（连地板的两个数都没差）。**⓪(b) `过渡帧数=` 第四个 runner 真数 = 5** —— 逐字 `MOTION_MARKDOWN_MODE_FADE scale=1x 帧数=27 过渡帧数=5 相邻差帧数=2 首末连续差=0.0048 峰值=0.0145 声明=200ms 窗口=752ms 每格=28.9ms`，STEP[19] `Motion coverage floor` 本跑 `success` ⇒ 四跑并排 **2 / 5 / 0 / 5**（每格 71.5 / 26.0 / 75.6 / 28.9ms）⇒ 629 那句「≥2 在那台机器的钟上不是恒可满足」被同一份代码的第四个数再确认一次（红是**间歇**的，这一跑恰好过）。**⓪(c)** STEP[9] `SKIP_ROSTER 键=github-runner 内层Ran=696 内层skip汇总=3 解析=2 名单外=无 名册未跳=无` ⇒ 634 **连续第四跑**绿；STEP[18] `On-screen probe coverage floor` = `success` ⇒ 622 本跑无新值（第十四值仍是 219.7ms/2 颗）。**另记一格具名**：`BULLET_LEVELS` 在这一跑**没有一行**，而这不是通道坏 —— 这一跑的 sha 是 `f12f50d`（R561 头笔），**根本不含本轮那条判据**（它在未推的 `ff2cb9f` 里）⇒ 具名「判据未推」，不许写成「runner 上判不到」，也不许拿它当「这条尺在 1x 走出口」的证据 ⇒ 那一格留给 R563 ⓪。',
    "ONEX": '`probe_r562_1x_preview.py`（LANCZOS 把 2x 帧缩到 1x 再跑同一把尺的四道筛）现读 `light 1.0x 带=7 行=7 筛后=6 列=3 左沿=[36, 52, 68] 步进=[16, 16] 容差=1px 步进地板=8px`、dark 同形 ⇒ 列数不塌、步进等距（漂移 0px vs 容差 1px）、步进 16px ≥ 地板 8px（余量 2 倍）。⚠ 它**不是**真 1x 渲染 ⇒ 只回答「四道筛还剩多少余量」，不回答「runner 判到了」',
}


UI = u"""## 第 561 轮（R562 · 2026-11-03 · U-2419…U-2425）：636 的退场第一步落地 —— 三级列表夹具让 `◦`/`▪` 第一次有帧对象，正文列步进判据把「回退字体把列推歪」这一族钉住；实测 `▪` 的 advance 被钳位吸收 ⇒ 636 的「列被推歪」这一格被证伪（**三级尺寸没有被判过 ⇒ 单子继续开**）；产品 0 文件

- **U-2419：⓪ CI 读单（只登记、不轮询）。** 开场 HEAD=origin=`f12f50d`、ahead=0、已跟踪改动 0、`api=200 / apple=200`。`41519677393 ↔ f12f50d`（R561 那一批头笔 = 补记笔，含 R561 全部代码）状态 **queued、已等 232s**，`steps` 打的 `conclusion=` 是**空串**、`JOB build-and-test ⇒` 也是空 ⇒ 这是「**没有结论**」不是「没红」⇒ 三格当时**具名 NOT-RUN**：(a) 几何派生尺 `SolidRuler` 在 runner 的真 1x 帧上到底判没判到；(b) `过渡帧数=` 第四个 runner 真数；(c) STEP[9] `SKIP_ROSTER` 第四跑 + STEP[18] 622。同批无独立跑 ⇒ 具名 `CI_UNREAD`：R561 的 `5e08357`/`a8adab4`/`324c513`、R560 的 `0a49b5f`/`631f910`/`700dee9`/`8004a42`/`22bd17d`、R558 的 `b8949f5`/`1ea1bb7`；永不重开 `41452722560↔58851c2`、`41455782587↔598b253`。已读不必重读：`41509855001↔26c1939` = concluded failure、只红 STEP[19]（四格读数在 `### R561 补记` ②）。%(CI_CLOSE)s
- **U-2420：第二格为什么走「补夹具」而不是「修派生式」—— 优先序 ① 是被**读数没到**挡住的，不是被现读否掉的。** 发令给的顺序是：① ⓪(a) 若仍走 `solid-unresolved` 就修派生式；② 否则落 636 的退场第一步。开场时那一跑还是 queued ⇒ (a) 没有读数 ⇒ ① 这条路今天**不能选**（选了就是拿猜测当读数）；同时它也**没有被否掉** ⇒ 账里两件事分开写，并把它原样交给 R563 ⓪ 的头格。于是本轮落 ②：**让 `◦`(depth1) 与 `▪`(depth2) 第一次有帧对象**。为什么不破 R549 禁碰：禁碰的是产品那颗 `⦁` 的**绘制面**（R549 改的是 glyph 选择与墨高，并已签收 2.8→3.9pt），这一步只在 `Tests/` 里加一段正文，产品一行没动 ⇒ 事后 `FRAME_BASELINE_CHANGED=0`（既有 354 张逐字节不变）就是这句话的证人，不是我的声明。
- **U-2421：夹具本体 + 一个把 R561 那一格照出来的写法坑。** 新夹具 `detail-markdown-bullet-nested`（720×520，两档外观）+ 正文 `UICaptureTests.nestedBulletFixtureBody`。正文**刻意写成转义串而不是三引号块**：Swift 的多行串会按闭合那一行的缩进整块 dedent，而 R561 扫夹具时命中的正是这个形状（五段含列表正文 dedent 之后相对缩进全为 0 ⇒ depth 塌成 {0}）。产品侧 `depth = 行首空格数 / 2`（`MarkdownParsing.listItem`）⇒ 2 个空格 = depth1、4 个 = depth2。帧名单：`FRAME_BASELINE_COMPARED=356 CHANGED=0 MISSING=0 ADDED=2` ⇒ 新增的就是这张夹具的两档，**其余 354 张逐字节不变**。
- **U-2422：看图与像素现读（本机 2x）。** 先看图（列表区 2 倍放大，light/dark 各一张）：三级阶梯读起来是**一致**的 —— 第三级的 `▪` 没有比第一级的 `⦁` 明显大，正文列逐级右移，肉眼看不出哪一级被推歪。再量（一次性探针 `probe_r562_nested_bullets.py`）：项目符墨 bbox light **8×8 / 7×6 / 8×8 px**（4.00 / 3.00 / 4.00pt）、dark **9×9 / 7×7 / 8×8 px**；正文左沿 x=**73 / 105 / 137 px** ⇒ 步进 **32px / 32px = 16.0pt / 16.0pt，漂移 0px**。⚠ 判据落地之前先做过 **1x 降采样体检**（本机拍不出真 1x 帧）：%(ONEX)s
- **U-2423：判据落的是「有对象 + 正文列等距」，不是「三级同尺寸」—— 后者会把设计钉成缺陷。** `testNestedBulletLevelsKeepOneUniformTextColumn` 判两格：① **列数 == 产品解析出的深度集合**（从产品入口 `MarkdownParser.parse(nestedBulletFixtureBody)` 拿 {0,1,2}，再断言帧上数到的正文列一样多 ⇒ 有一级没画出来就红，不许退化成"读不到就算了"）；② **相邻步进彼此相等**（容差 `1pt×scale`）且每一级步进 **≥ 8pt**（地板由实测 16pt 的一半推，防"三列塌成一列 ⇒ 等距恒真"这种退化假绿）。三级各自的墨 bbox **只打印不断言**：R549 有意让三档用三个不同字形（`⦁ ◦ ▪`），"同尺寸"不是产品契约。
  ⇒ **636 里被证伪的只有「列被推歪」这一格**：机制上 `▪` 的 advance 12.00pt 确实比 `⦁` 的 8.11pt 宽，但正文列取 `max(minimumAdvance=16, markerWidth + markerGap=2)` ⇒ 12+2=14 ≤ 16 被**钳位吸收**；像素上三级步进实测 16.0/16.0pt、漂移 0px ⇒ 这一格与 R560 那个「两态差 2.5pt」的勾选框**不是同一类**。
  ⚠ **本轮证的只是「有对象可量 + 正文列步进不漂」，不是「三级项目符尺寸已验」** —— 三档各自的墨 bbox 是**读数不是判据**（R549 只签过 depth0 那颗 `⦁` 的墨高 ≥3.5pt，`◦`/`▪` 至今没有任何尺寸契约）。要不要给三级尺寸定一条契约，会直接撞 R549 禁碰面（改的就是那个函数）⇒ **636 保持开单**，剩下的这一格归用户点头，本轮不自行落地。
- **U-2424：三把刀 + 两把**空刀（撤了、没登记）**。** **M1460** CAUGHT：夹具第三级的缩进**两行一起**抹平 ⇒ 解析出 `[0, 1]`、帧上数到 2 列 ⇒ 两格同时红；**M1461** CAUGHT（真牙）：产品 `ListHangingIndent.minimumAdvance` 16→12 ⇒ 第三级正文列被推歪，读数 `步进=[32, 38]px(16.0/19.0pt)` ⇒ 红在等距断言，出容差 2px；**M1462** CAUGHT：列合并容差 0.5pt→20pt ⇒ 三列塌成两列（`列=2 步进=[64]px`）⇒ 红在列数断言，证明"数到三级"是帧上的一句话、不是聚类参数的一句话。三把 `RESTORE_CLEAN=yes`。
  ⚠ **两把空刀在登记前被 ④ 的自检抓住**：① 第一版 M1460 只抹平**一行**缩进 ⇒ 读数逐字不变（另一行还留着 4 个空格 ⇒ depth2 仍在）；② 另一把把「项目符宽 ≤8pt」抬到 40pt ⇒ 读数逐字不变 —— 窗口工具栏那一行在 y=73..93px，而判据从 `60pt×scale`=120px 才开始扫 ⇒ 它是被 **y 窗口**筛掉的，不是被宽度筛掉的。**这一格自读进账**：那道宽度筛在当前帧上是冗余的（它不是错的，只是今天没有东西靠它筛掉）。三张表登记进名册：现读 **%(PRECHECK)s**、`ARM_TOTAL %(ARM)s`、`HIDDEN_ARMS %(HIDDEN)s`；与前几批同形 ⇒ 静态抽不出 needle、不在 `covered` 里，会红性只由上面三把真跑证明。
- **U-2425：③ 验证链与④⑤ 账（顺序未换）。** `swift build --build-tests` 告警 **0**；判据 filter 绿（`Executed 1 test, with 0 failures`，读数见 U-2422/U-2423）；三把刀全 CAUGHT；判据卷 `UICaptureTests` **%(CAPTURE)s**；帧重捕 **%(FRAMES)s**（新增两帧走**同一笔** `frame_baseline.py update` 收进台账这一笔，名单外一个帧不许有）；全量 **%(FULL)s**；预检三读**串行**；换装 %(INSTALL)s。清账 **%(ABSENCE)s**；电池 **%(BATTERY)s**（台账与 `--write` 之后复跑，只抄 `Ran`/`OK`/`FAILED`，`&&` 链里不插 grep）；产品面连续零改动 **%(STREAK)s** 轮（**台账落盘之后**现读 `python3 scripts/product_streak.py` ⇒ `%(STREAK_RAW)s`）。**636 半落地**（退场第一步 = 夹具已补 + 列步进判据已配三把刀；「列被推歪」这一格被证伪，但**三级项目符的尺寸没有被判过** ⇒ 单子继续开，剩下的那一格要不要定契约归用户）；629 保持「(B) 已落地 + 635 已结案 + runner 三跑实测 2/5/0 ⇒ ≥2 在那台机器的钟上不是恒可满足」，两条出路仍等用户点头；622/624/627 继续；628/625/626/569/616/632/634/635 已落地那半不重开；**633 仍等用户人工回执**（本轮没拿到 ⇒ 不写任何结论）。下一轮 R563（第 562 轮 / Round 560）：⓪ 必读本轮 push 头笔那一跑（取号时未创建 ⇒ 现在去读；中间笔具名 `CI_UNREAD`）；头三格 = (a0) **本轮这条 `BULLET_LEVELS` 在 runner 1x 走哪条**（判到就报 px 与步进；打 `*_NOT_RUN=detail-frame-plain` 就具名入账并补内容墨证人，**不许降墨下界、不许改期望、不许加豁免**）、(a) **R561 那把几何派生尺在 runner 上判到了没有**（`HEAT_LEGEND_COVERAGE … 倍率=1.0x` 还是 `solid-unresolved`；仍走出口就是门限算错，按读数修，不许降地板）、(b) `BULLET_LEVELS` 这条新判据在 runner 1x 走哪条（**1x 体检只做了一次降采样代理，不是真 1x 帧**）、(c) `过渡帧数` 第四个真数（读到几都按 629 具名入账，再 ≤1 就把两条出路的代价摆给用户，**不自行登记 `sampled`**）+ STEP[9]/[18]。禁碰清单 **11 面**不变（本轮产品 0 文件 ⇒ 不抬数）；刀号 **M1463** 起；4.5 地板、150 上限、120ms 阈值、Motion ≥2 帧地板、2x 8.0pt、1x 6.0pt、`probeInkFraction=3%` 均不动；`.contentFade` 0.20 与声明时长一字未改；全量 skipped 只记现读。

"""


ITER = u"""
## Round 559 · R562（第 561 轮 · 2026-11-03）：让 `▪` 有帧对象，然后发现「列被推歪」这一格不是缺陷 —— 636 按机制与像素两条证伪到一半，判据落的是"列数 + 步进等距"

R560 开 636 时说第三级项目符 `▪` 由冬青黑体回退画出，"与 R560 修掉的任务勾选框是同一类缺陷"，而 R561 量出**今天没有任何夹具画到 depth2** ⇒ 那一格只能具名 NOT-RUN。本轮先补夹具（只在 `Tests/` 里加一段三级列表正文，产品 0 文件），让 `◦`/`▪` 第一次有帧对象，再量：三级项目符的墨 bbox 是 8×8 / 7×6 / 8×8 px（light），正文左沿 73 / 105 / 137 px ⇒ **步进 16.0pt / 16.0pt、漂移 0px**。机制上也对得上：`▪` 的 advance 12.00pt 比 `⦁` 宽，但正文列取 `max(minimumAdvance=16, markerWidth+2)`，12+2=14 被钳位吸收 ⇒ **「列被推歪」这一格不成立**，它和"两态差 2.5pt"的勾选框不是一类 —— 但账里要说清本轮只证到"有对象可量 + 列步进不漂"，**三级项目符的尺寸没有被判过**（墨 bbox 只印不判，`◦`/`▪` 至今没有尺寸契约；要不要定一条会撞 R549 禁碰 ⇒ 636 保持开单，那一格归用户）。判据因此没有照 636 原文的"三级同尺寸"去写 —— 那会把 R549 有意为之的三档三字形钉成缺陷 —— 而是判**帧上正文列数 == 产品解析出的深度集合**与**相邻步进等距（并带 8pt 地板防塌平）**，配三把刀（抹平缩进 / 把钳位降到 12 让列真被推歪 / 把合并容差抬到能吞掉一级）。登记前自检抓住两把空刀：只抹平一行缩进、以及把宽度筛抬到 40pt —— 后者暴露了一格真话：工具栏那行是被 **y 窗口**筛掉的，那道宽度筛在当前帧上冗余。上 runner 之前做了一次 1x 降采样体检（本机拍不出真 1x 帧，所以它只回答"四道筛还剩多少余量"，不回答"判到了"）。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉看图 | 14/15 | 新夹具的两档帧真看了（列表区 2 倍放大，light/dark），看图结论与像素读数同向（阶梯一致、无被推歪的列）；扣的一分是本轮没有**产品画面**的变化可看，看的是新夹具而非新界面。 |
| 判据有效性 | 15/15 | 判据从产品入口取深度集合再与帧上列数对账，等距断言带 8pt 地板防退化；M1461 把钳位降到 12 时读数真的从 [32,32] 翻成 [32,38] ⇒ 这条尺判的是产品行为，不是夹具写法。 |
| 假绿防御 | 15/15 | 三把刀分别打穿"对象证人""等距断言""列数不是聚类的产物"；两把空刀在登记前被变化量自检抓住并照实进账（一把还暴露了宽度筛在当前帧上冗余）。 |
| 产品面推进 | 9/15 | 产品 0 文件（推进在夹具与判据上）；连续第三轮没有改画面，这一维不能再靠"尺的推进"抵账 —— R563 要么落 ⓪(a) 的修尺，要么按看图另取一个真实位。 |
| 台账一致性 | 15/15 | 写账前核三条硬格式；派生格（streak / sources）落盘之后现读；生成器的 `fill()` 这一轮起两种形状都查：「percent+左括号」的具名占位符与「percent+字母」的裸占位符（R561 那格未渲染占位符的根因补进代码，不只写在散文里）。 |
| 交付诚实性 | 15/15 | ⓪ 三格按 queued 具名 NOT-RUN（不轮询不猜）；优先序 ① 写成"被读数没到挡住"而不是"被否掉"；636 **只报证到的那一半**（有对象可量 + 列不漂），不写成"三级尺寸已验"，并写清它推翻的是自己上一轮开的单、保留 advance 越过 14pt 时会红的边界。 |
| 可复核性 | 15/15 | 夹具正文、探针脚本、四道筛的 pt 界值、三把刀与两把空刀的 needle 全部逐字进账；1x 体检的**能与不能**分开写（它只回答余量，不回答判到了）。 |

"""


CHG = u"""### 636 退场第一步落地：三级列表夹具让 `◦`/`▪` 第一次有帧对象，正文列步进判据钉住「回退字体把列推歪」；实测 `▪` 的 advance 被钳位吸收 ⇒ 636 的「列被推歪」这一格被证伪（R562 / 第 561 轮 / Round 559）

R560 开 636 时说第三级项目符 `▪` 由冬青黑体回退画出、"与任务勾选框同一类"，R561 又量出今天没有夹具画到 depth2 ⇒ 只能具名 NOT-RUN。本轮补上夹具（`detail-markdown-bullet-nested`，正文写成转义串以免三引号 dedent 把内容缩进吃掉；产品 0 文件），`◦`/`▪` 第一次有帧对象。看图 + 像素现读：项目符墨 bbox light 8×8 / 7×6 / 8×8 px、dark 9×9 / 7×7 / 8×8 px，正文左沿 73 / 105 / 137 px ⇒ 步进 16.0pt / 16.0pt、**漂移 0px**。机制同向：正文列取 `max(minimumAdvance=16, markerWidth+2)`，`▪` 的 12.00+2=14 被钳位吸收 ⇒ **636 的「列被推歪」这一格不成立**（机制 + 像素两条），本轮落的是第三条判据、**只承认证到的那一半** ⇒ 636 保持开单（原判据形状"三级同尺寸"会把 R549 有意为之的三档三字形钉成缺陷；三级尺寸契约要撞禁碰面 ⇒ 归用户）。新判据 `testNestedBulletLevelsKeepOneUniformTextColumn` 判两格：帧上正文列数 == 产品 `MarkdownParser.parse` 出的深度集合，以及相邻步进等距（容差 1pt、地板 8pt 防塌平）；三级墨 bbox 只印不判。刀 **M1460 / M1461 / M1462** 全 CAUGHT、RESTORE_CLEAN=yes（M1461 把 `minimumAdvance` 降到 12 ⇒ 步进实测翻成 [32,38]px=16/19pt，是这条判据的真牙）；**两把空刀在登记前撤掉并照实进账**。帧 `COMPARED=356 CHANGED=0 ADDED=2` ⇒ 既有 354 张逐字节不变（禁碰面一帧未动），新增两帧走同一笔 update。上 runner 前做一次 1x 降采样体检（本机无真 1x 帧 ⇒ 它只回答四道筛的余量，不回答"判到了"）。全量 %(FULL)s；build 0 告警；电池 %(BATTERY)s；4.5 / 150 / 120ms / Motion ≥2 帧 / 2x 8.0pt / 1x 6.0pt / `probeInkFraction=3%` 一律未动。

"""


B636 = u"""    退场第一步（R562 落地，产品 0 文件）：新夹具 `detail-markdown-bullet-nested` + 正文 `UICaptureTests.nestedBulletFixtureBody`（转义串写法，避免三引号 dedent 吃掉内容缩进）⇒ `◦`(depth1)/`▪`(depth2) **第一次有帧对象**（`FRAME_BASELINE_COMPARED=356 CHANGED=0 ADDED=2`，其余 354 张逐字节不变）。看图 + 像素现读（本机 2x）：项目符墨 bbox light **8×8 / 7×6 / 8×8 px**（4.00/3.00/4.00pt）、dark 9×9/7×7/8×8 px；正文左沿 **73 / 105 / 137 px** ⇒ 步进 **16.0pt / 16.0pt、漂移 0px**。
    半落地（R562，两条独立证据，只证到一半）：**「回退字形把正文列推歪」这一格不成立**。机制上 `▪` 的 advance 12.00pt 确实比 `⦁` 的 8.11pt 宽，但正文列取 `max(minimumAdvance=16, markerWidth + markerGap=2)` ⇒ 12+2=14 ≤ 16 被**钳位吸收**；像素上三级步进实测 16.0/16.0pt、漂移 0px ⇒ 与 R560 修掉的「两态差 2.5pt」勾选框**不是同一类**（那一类是同控件两态尺寸不等，这一格是三档各有自己的字形）。⚠ **这一格只证「有对象可量 + 列步进不漂」，没有证「三级项目符尺寸已验」**：三档墨 bbox 是读数不是判据，`◦`/`▪` 今天没有任何尺寸契约（R549 只签 depth0 的 `⦁` 墨高 ≥3.5pt）。要不要给三级定一条尺寸契约，改的就是 `bulletGlyph`/`markerFont` 那个函数 ⇒ **撞 R549 + R560 两个禁碰面 ⇒ 归用户点头，本轮不自行落地 ⇒ 636 保持开单**。
    退场条件（原两格都不该硬套，本轮落的是第三条，且只满足一半）：从前写「要么"三级项目符同尺寸"判据配刀落地，要么具名"没有帧对象"」—— 前者会把 R549 有意为之的三档三字形钉成缺陷，后者已被本轮夹具换掉。落的是：`testNestedBulletLevelsKeepOneUniformTextColumn` 判 **帧上正文列数 == 产品解析出的深度集合** + **相邻步进等距（容差 1pt、地板 8pt）**，三级墨 bbox 只印不判；刀 **M1460/M1461/M1462** 全 CAUGHT（M1461 把 `ListHangingIndent.minimumAdvance` 16→12 ⇒ 步进实测 `[32, 38]px` = 16.0/19.0pt ⇒ 红）。**留一格真话**：若哪天回退字形的 advance 越过 14pt（=16−2），正文列会真的漂，而那一格由 M1461 这一族钉着；判据在 runner 1x 走哪条留给 R563 ⓪（本机只做过降采样体检）。
"""


DEC = u"""## D-562（R562 · 2026-11-03）：开单时的缺陷断言也是**待证的假设**；判据必须判"被设计承诺的那个属性"，不是判"探针量到的那个量"

① **自己上一轮开的单，本轮可以证伪它 —— 但证伪要拿两条独立证据。** 636 是 R560 用一次性字体探针开的（`▪` advance 12.00pt、由 `.HiraKakuInterface-W4` 回退画出），当时写成"与任务勾选框同一类缺陷"。本轮补夹具让三级第一次有帧对象，量到步进 16.0/16.0pt、漂移 0px（像素），并且对上 `max(minimumAdvance=16, markerWidth+2)` 的钳位（机制）⇒ 两条同向才敢把那句话撤回。**只有机制没有像素**（R560 那把 Menlo 空刀的教训）或**只有像素没有机制**（1x 上可能就是另一个数）都不够。
② **"探针量到的量"不等于"产品承诺的属性"。** advance 是字体度量，用户看不见；看得见的是正文列有没有被推歪。636 原文的退场判据写成"三级项目符同尺寸"，而三档三个字形是 R549 的**设计**（`⦁ ◦ ▪`，墨高 2.8→3.9pt 那一次签收的）⇒ 照原文写判据会把设计钉成缺陷。落地的判据因此判**列数对账 + 步进等距**，墨 bbox 只印不判。
③ **退场条件也可以被证伪，但"改写第三条"不等于结案。** 636 原来的两个退场分支都不该硬套（一个是坏判据 —— 会把 R549 的三档三字形钉成缺陷；一个已被本轮动作换掉 —— 现在有帧对象了）。本轮显式落第三条（列数对账 + 步进等距），**并且只承认它证到的那一半**：列不漂。三级尺寸仍无契约、单子继续开 —— 否则下一轮就能拿"按退场条件结案"的名义做假动作。
④ **空刀在登记前抓住，比抓住之后解释便宜。** 两把：只抹平一行缩进（另一行还留着 depth2 ⇒ 读数逐字不变）、把宽度筛抬到 40pt（工具栏那行是被 **y 窗口**筛掉的 ⇒ 读数逐字不变）。后者顺带量出一格真话：**那道宽度筛在当前帧上是冗余的**。冗余不等于错，但账里不许把它写成"有牙的筛"。
⑤ **新判据上 runner 之前的 1x 体检，只许回答"余量"，不许冒充"判到了"。** 本机拍不出真 1x 帧 ⇒ 降采样代理能算出四道筛（y 窗口、宽度、间隙、合并）在 1x 还剩多少余量，但**不能**证明 runner 上判据真的判到 —— 那一句只能由含这条判据那一笔的跑作证（R555/R561 同族：修尺那一笔的跑签不了自己）。
⑥ **撤回**：把夹具正文的第三级缩进改回去（M1460 抓）、把 `minimumAdvance` 改动留在产品里（M1461 抓，且本轮 `RESTORE_CLEAN=yes`）、把合并容差抬高（M1462 抓）⇒ 三种坏法各有红；判据本身退化成"只印不判"的形态由列数断言与 8pt 地板一起钉。
"""


def insert_after_line(t, line_prefix, block, label):
    u"""按**行首前缀**定位那一行，插到它后面（长行里有反引号与百分号时比抄整行稳）。"""
    hits = [i for i, ln in enumerate(t.split(u"\n")) if ln.startswith(line_prefix)]
    if len(hits) != 1:
        sys.stderr.write("ANCHOR_BAD %s lines=%d\n" % (label, len(hits)))
        sys.exit(1)
    i = t.index(line_prefix)
    j = t.find(u"\n", i)
    return t[:j + 1] + block + t[j + 1:]


def rd(name):
    return io.open(os.path.join(ROOT, name), encoding="utf-8").read()


def wr(name, t):
    io.open(os.path.join(ROOT, name), "w", encoding="utf-8").write(t)


def once(t, old, new, label):
    n = t.count(old)
    if n != 1:
        sys.stderr.write("ANCHOR_BAD %s hits=%d\n" % (label, n))
        sys.exit(1)
    return t.replace(old, new, 1)


def fill(text):
    out = text
    for key, value in NUM.items():
        out = out.replace(u"%%(%s)s" % key, value)
    if u"%(" in out:
        i = out.find(u"%(")
        sys.stderr.write("PLACEHOLDER_LEFT %s\n" % out[i:i + 30])
        sys.exit(1)
    # R561 的自伤钉成代码：裸 `%`+字母（当年那格 `。%s 同批无独立跑`）也从没被查过。
    bad = re.search(u"%(?=[a-zA-Z])", out)
    if bad:
        i = bad.start()
        sys.stderr.write("BARE_PERCENT_LEFT %s\n" % out[max(0, i - 30):i + 30])
        sys.exit(1)
    return out


def main():
    check = "--check" in sys.argv

    for key, value in NUM.items():
        if value.startswith(u"@@") and value.endswith(u"@@"):
            sys.stderr.write("NUM_NOT_FILLED %s\n" % key)
            return 1

    state = rd("AGENT_STATE.md")
    if state.count(u"## R562 ⓪ 开工") != 1:
        sys.stderr.write("ANCHOR_BAD state R562 ⓪ 节不存在 ⇒ 不许两轮写进同一节\n")
        return 1
    if u"## R562 状态（" in state:
        sys.stderr.write("ANCHOR_BAD state R562 状态节已存在\n")
        return 1

    n = "AGENT_UI_AUDIT.md"
    t = rd(n)
    a = u"## 第 560 轮（R561 · 2026-11-03 · U-2412…U-2418）"
    if t.count(a) != 1:
        sys.stderr.write("ANCHOR_BAD ui\n")
        return 1
    if not check:
        wr(n, t.replace(a, fill(UI) + a, 1))

    n = "AGENT_VISUAL_ITERATION.md"
    t = rd(n)
    if u"## Round 559 · R562" in t:
        sys.stderr.write("ANCHOR_BAD iteration Round 559 已存在\n")
        return 1
    if not t.endswith(u"\n"):
        t += u"\n"
    if not check:
        wr(n, t + fill(ITER))

    n = "CHANGELOG.md"
    t = rd(n)
    a = u"## [Unreleased]\n\n"
    if t.count(a) != 1:
        sys.stderr.write("ANCHOR_BAD changelog\n")
        return 1
    if not check:
        wr(n, t.replace(a, a + fill(CHG), 1))

    n = "AGENT_BACKLOG.md"
    t = rd(n)
    t = insert_after_line(t, u"    退场条件（两步，顺序不许换）：① 先补一段 depth2 的夹具正文", B636, u"backlog636")
    if not check:
        wr(n, t)

    n = "AGENT_DECISIONS.md"
    t = rd(n)
    if not t.endswith(u"\n"):
        t += u"\n"
    if not check:
        wr(n, t + fill(DEC))

    n = "AGENT_FINAL_REPORT.md"
    t = rd(n)
    for old, new, label in [
        (u"R9–R558，559 节自评", u"R9–R559，560 节自评", u"title"),
        (u"阶段二 **551 轮**审计（R9–R558；以 `curve_from_ledger.py` 的 `PHASE2 n=551` 为准，最新一节是 `AGENT_VISUAL_ITERATION.md` 的 Round 558",
         u"阶段二 **552 轮**审计（R9–R559；以 `curve_from_ledger.py` 的 `PHASE2 n=552` 为准，最新一节是 `AGENT_VISUAL_ITERATION.md` 的 Round 559", u"§1"),
        (u"| 视觉台账 | U-31 … U-2418", u"| 视觉台账 | U-31 … U-2425", u"U 上界"),
        (u"以 `AGENT_STATE.md` 的 R561 节 ② 为准", u"以 `AGENT_STATE.md` 的 R562 节 ② 为准", u"state pointer"),
        (u"## 18. R458 → R561 这一段", u"## 18. R458 → R562 这一段", u"§18 head"),
        (u"R561 续到 561 —— 这份报告第七次差点停在几十轮之前）",
         u"R562 续到 562 —— 这份报告第七次差点停在几十轮之前）", u"§18 tail"),
    ]:
        t = once(t, fill(old), fill(new), label)
    anchor = u"全量 1404/57/0（678.1s）；build 0 告警；电池 696/5。\n"
    bullet = (u"- **R562（636 退场第一步：三级列表夹具 + 正文列步进判据；产品 0 文件）**："
              u"R560 开的那条单说 `▪` 由冬青黑体回退画出、与任务勾选框同一类；本轮补夹具让三级第一次有帧对象，"
              u"量到**步进 16.0/16.0pt、漂移 0px**，机制上 `▪` 的 advance 12.00+2 被 `minimumAdvance=16` 钳位吸收 "
              u"⇒ **「列被推歪」这一格被两条独立证据证伪**（原判据形状「三级同尺寸」会把 R549 的三档三字形钉成缺陷；三级尺寸契约要撞禁碰面 ⇒ 636 保持开单、归用户）。"
              u"新判据判**帧上正文列数 == 产品解析出的深度集合** + **相邻步进等距**（容差 1pt、地板 8pt 防塌平）。"
              u"刀 **M1460/M1461/M1462 全 CAUGHT**（M1461 把钳位降到 12 ⇒ 步进真翻成 [32,38]px），"
              u"**两把空刀在登记前撤掉并照实进账**。帧 `CHANGED=0 ADDED=2` ⇒ 既有 354 张逐字节不变；"
              u"⓪ 那跑开场 queued ⇒ 三格具名 NOT-RUN。全量 %(FULL)s；build 0 告警；电池 %(BATTERY)s。\n")
    t = once(t, anchor, anchor + fill(bullet), u"§18 bullet")
    if not check:
        wr(n, t)

    n = "AGENT_STATE.md"
    t = rd(n)
    body = u"""## R562 状态（2026-11-03 · 第 561 轮 / Round 559 · 产品 0 文件 + 夹具 1 张 + 判据 1 条 + 三把刀）

① ⓪ 那跑：`41519677393↔f12f50d`（R561 那一批头笔 = 补记笔）开场 **queued（232s）**、`steps` 的 `conclusion=` 是空串 ⇒ 三格当时**具名 NOT-RUN**（(a) `SolidRuler` 在 runner 真 1x 上判没判到、(b) `过渡帧数` 第四数、(c) STEP[9]/[18]）；同批无独立跑 ⇒ `CI_UNREAD`（R561 三笔 + R560 五笔 + R558 两笔）；cancelled 两笔永不重开；`41509855001↔26c1939` 已读（failure、只红 STEP[19]）⇒ 不重读。%(CI_CLOSE)s
② ② 第二格走的是**补夹具**（优先序 ①「修派生式」不是被现读否掉，是 ⓪(a) 读数没到 ⇒ 原样交给 R563）。新夹具 `detail-markdown-bullet-nested` + `nestedBulletFixtureBody`（**转义串**写法：三引号会按闭合行整块 dedent ⇒ 内容缩进被吃掉，R561 扫夹具命中的正是这个）⇒ `◦`/`▪` 第一次有帧对象；产品 0 文件 ⇒ `FRAME_BASELINE_COMPARED=356 CHANGED=0 ADDED=2`，其余 354 张逐字节不变（= R549 那张 `detail-markdown-bullet` 与全部禁碰面一帧未动的证人）。
③ ②(b) **636 的「列被推歪」这一格被证伪（单子继续开，只证到"有对象可量 + 列不漂"）**：看图（列表区 2 倍放大，light/dark）+ 像素现读 ⇒ 项目符墨 bbox light 8×8/7×6/8×8px、正文左沿 73/105/137px ⇒ **步进 16.0/16.0pt、漂移 0px**；机制 ⇒ 正文列取 `max(minimumAdvance=16, markerWidth+2)`，`▪` 的 12.00+2=14 被钳位吸收 ⇒ 与 R560 的"两态差 2.5pt"**不是同一类**；⚠ **本轮只证「有对象可量 + 列步进不漂」，三级项目符的尺寸没有被判过**（墨 bbox 只印不判 ⇒ 636 保持开单，定尺寸契约要撞 R549/R560 两个禁碰面 ⇒ 归用户）。新判据 `testNestedBulletLevelsKeepOneUniformTextColumn` 不写"三级同尺寸"（那会把 R549 的三档三字形钉成缺陷），判 **列数 == 产品解析深度集合** + **相邻步进等距（容差 1pt、地板 8pt 防塌平）**，墨 bbox 只印不判。⚠ 1x 只做过**降采样体检**（%(ONEX)s）⇒ 真读数留给 R563。
④ ③ 验证链（顺序未换）：`swift build --build-tests` 告警 **0**；判据 filter 绿（`Executed 1 test, with 0 failures`）；三把刀 **M1460/M1461/M1462 全 CAUGHT、RESTORE_CLEAN=yes**；**两把空刀在登记前撤掉**（只抹平一行缩进；把宽度筛抬到 40pt ⇒ 工具栏那行其实是被 y 窗口筛掉的 ⇒ 那道筛当前冗余）；三张表登记进名册；判据卷 **%(CAPTURE)s**；帧重捕 **%(FRAMES)s**（新增两帧走**同一笔** `update`）；全量 **%(FULL)s**；预检 **%(PRECHECK)s**、`ARM_TOTAL %(ARM)s`、`HIDDEN_ARMS %(HIDDEN)s`（三读**串行**）；换装 %(INSTALL)s。
⑤ ④⑤ 账与交接：清账 **%(ABSENCE)s**；电池 **%(BATTERY)s**（台账与 `--write` 之后复跑，只抄 `Ran`/`OK`/`FAILED`）；产品面连续零改动 **%(STREAK)s** 轮（**台账落盘之后**现读 `python3 scripts/product_streak.py` ⇒ `%(STREAK_RAW)s`）。**636 半落地、单子继续开**；629 保持「(B) 已落地 + 635 已结案 + runner 三跑实测 2/5/0 ⇒ ≥2 在那台机器的钟上不是恒可满足」，两条出路等用户点头、本轮不自行登记 `sampled`；622/624/627 继续；628/625/626/569/616/632/634/635 已落地那半不重开；**633 仍等用户人工回执**（本轮没拿到 ⇒ 不写任何结论）。⑥ 一次性 push（本轮四笔：⓪ 开工 + A 夹具与刀 + 台账 + 补记）⇒ 只有头笔建跑。R563 ⓪ 必读它；头三格 = (a) R561 那把几何派生尺在 runner 上判到没有（仍走 `solid-unresolved` 就是门限算错，按读数修、不许降地板）、(b) 本轮这条 `BULLET_LEVELS` 在 1x 走哪条（体检只是降采样代理）、(c) `过渡帧数` 第四数 + STEP[9]/[18]。刀号 **M1463** 起；禁碰清单 **11 面**不变（本轮产品 0 文件 ⇒ 不抬数）；4.5 地板、150 上限、120ms 阈值、Motion ≥2 帧地板、2x 8.0pt、1x 6.0pt、`probeInkFraction=3%` 均不动；`.contentFade` 0.20 与声明时长一字未改。

"""
    a = u"\n## R562 ⓪ 开工（2026-11-03 · 第 561 轮 / Round 559 · CI 读单 + 基线全现读 + 第二格选定）"
    t = once(t, a, u"\n" + fill(body).rstrip(u"\n") + a, u"state body")
    if not check:
        wr(n, t)

    sys.stdout.write("LEDGERS_R562_%s\n" % ("CHECK_OK" if check else "WRITTEN"))
    return 0


if __name__ == '__main__':
    sys.exit(main())

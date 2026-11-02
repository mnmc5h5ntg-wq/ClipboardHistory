# -*- coding: utf-8 -*-
"""R563 台账（第 562 轮 / Round 560）：六个候选位全部被现读否掉 ⇒ 落「改账 + 盲区补真机对照数」。

用法：`python3 ledgers_r563.py --check` 只验锚点与 NUM；不带参数才真写。
R562 的两条教训钉在代码里：① **每一本都有幂等守卫**（不是只给一本）；② 守卫搜索的串不许出现在守卫自己写的正文里；
③ `fill()` 两种占位符形状都查（具名与裸 percent+字母）。
"""
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

NUM = {
    "FULL": '1405/57/0（701.2s）',
    "INSTALL": '`INSTALL_RESULT=ok / INSTALL_SHA_MATCH=1 / INSTALL_ENTRIES=433=433 / SMOKE_OK=1 / INSTALL_SIGNATURE=local flags=0x0`（版本 1.4.8→1.4.8，PID→66415，启动晚于安装、exe 路径逐字对上，备份 `before-R563`）',
    "BATTERY": '696/5',
    "ABSENCE": "ABSENCE_PENDING",
    "STREAK": "STREAK_PENDING",
    "STREAK_RAW": "STREAK_RAW_PENDING",
    "CAPTURE": '221/4 skipped/0 失败（602.2s）',
    "FRAMES": '**356 CHANGED=0 MISSING=0 ADDED=0**（本轮只改了 `Tests/` 里一段注释 ⇒ 基线本来就该不动；这一格同时是「产品与 11 个禁碰面一帧未动」的证人）',
    "PRECHECK": "tables=361 covered=295 arms=757 bad=0",
    "ARM": "files=454 arms=1244 dupes=0 repeats=0",
    "HIDDEN": "表=448 可判=1183 rot=0 抽不出=6 已声明表=6 处置=ok",
    "CI_CLOSE": '**收口前复述 `queue`：`41531750912 ↔ 75b32d6` = concluded failure（已等 4019s），但 `gh run view --json jobs` 现读 `build-and-test cancelled` ⇒ 这一跑的失败**不是任何一条判据红**，而是作业被取消；`ci_read.py readings` 直接报 `gh run view … --log 失败（exit=1）：log not found: 125573433836` ⇒ 日志从未落盘。**四格因此全部维持具名 NOT-RUN（成因=cancelled、日志取不到）**，不许写成「没红」，也不许写成「判到了/判不到」：(a) `HEAT_LEGEND_*` 复核、(b) `BULLET_LEVELS` 在 1x 走哪条、(c) `过渡帧数` 第五数、(d) STEP[9]/[18] 全部未到。⇒ 这一对与 `41452722560↔58851c2`、`41455782587↔598b253` 同形，**进「永不重开」名单**；R562 那条新判据 `BULLET_LEVELS` **至今没有任何 runner 读数**（上一跑 `41519677393↔f12f50d` 不含它，这一跑没有日志）⇒ 账上写「判据未推」，R564 ⓪ 只能读它自己那一跑。',
}

UI = u"""## 第 562 轮（R563 · 2026-11-03 · U-2426…U-2431）：六个候选位全部被现读否掉 —— 本轮落的是「把一处账改齐」＋「给一处老盲区补上另一通道的读数」；产品 0 文件、判据 0 条、刀 0 把（一把写到一半撤掉）

- **U-2426：⓪ CI 读单（只登记、不轮询）。** 开场 HEAD=origin=`75b32d6`、ahead=0、已跟踪改动 0、`api=200 / apple=200`。`41531750912 ↔ 75b32d6`（R562 那一批头笔 = 补记笔）状态 **queued、已等 229s**、`steps` 的 `conclusion=` 是空串 ⇒ 四格当时**具名 NOT-RUN**：(a) `HEAT_LEGEND_*` 走哪条（⚠ 本轮只是**复核** —— 首次签收已在 `41519677393↔f12f50d`，不许记成第二次首次）；(b) `BULLET_LEVELS` 在 runner 1x 走哪条；(c) `过渡帧数=` 第五数；(d) STEP[9] 第五跑 + STEP[18]。同批无独立跑 ⇒ `CI_UNREAD`：R563 的中间笔与 R562 的 `327bc53`/`ff2cb9f`/`5d71660`/`c8c950f`、R561 三笔、R560 五笔、R558 两笔；永不重开 `41452722560↔58851c2`、`41455782587↔598b253`。%(CI_CLOSE)s
- **U-2427：本轮第 ⓪ 格额外要消的一处账内矛盾 —— 改的是措辞，不是门。** 监工交叉核对发现同一轮里 636 挂着两种状态：轮次节 ②(b)/⑤ 与台账笔 `5d71660` 写「半落地、单子继续开（三级项目符的尺寸没有被判过）」，而 `### R562 补记` ④ 写「636 本轮结案」⇒ 互斥。按证据取**继续开单**（墨 bbox 只印不判；定尺寸契约要撞 R549/R560 两个禁碰面 ⇒ 归用户），开工笔 `851b124` 把补记那一格逐字改齐并写明矛盾成因（补记笔沿用了上一轮的口径措辞，没跟同一轮里**已落盘**的另外两处交叉核对）。**没有撤判据、没有降地板、没有加豁免**；两处矛盾不许并存到 R564。
- **U-2428：第二格（要求落 `Sources/`）的取靶全程 —— 六个候选，六个被现读否掉，一个都没硬落。** ① ⓪(a) 修派生式：读数没到（queued）⇒ 不能选，且它也只是复核。② 636 的三级尺寸契约：改的就是 `bulletGlyph`/`markerFont` ⇒ 同时撞 **R549 与 R560** 两个禁碰面 ⇒ 归用户。③ 侧栏选中行的纯黑带（看图第一发现）：真实捕获通道的视图树现读定位到 `ListTableRowView x=0 y=397 w=280 h=66 selected=true` 里那枚 `NSVisualEffectView x=10 y=397 w=260 h=66 material=4`；再用**另一条通道**对照（真机只截主窗口 750×492、量完即删、不入仓）：非选中行背景 (52,52,39) vs 选中行 (80,80,68) ⇒ **每通道 +28，屏上选中态清楚可见** ⇒ 黑的是通道不是产品，且这处**早已登记**在 `materialBlindSpotFixtures`（R206/R40/R523 三次登记，注释里连 66pt 都写着）⇒ **不新开单**。④ 三枚行内标记（`text.viewfinder`/`link`/`textformat`）的墨高：写到一半撤掉，见 U-2430。⑤ `heatmap-empty` 的 3.97:1：主色现读 light 底 (255,255,255)/墨 (128,128,128) ⇒ WCAG ≈3.95:1，dark (30,30,30)/(154,154,154) ≈4.54:1 —— 那块墨是**空热图的格子**（装饰性数据底），不是文本 ⇒ 4.5 地板不适用。⑥ 选中态是否把行撑高（列表抖动）：五行高度现读 `66/51/51/51/66`pt，首尾两行 66pt 是因为它们标题排了**两行**（长中文句 / 40 字符无空格 token），与选中无关。⇒ **本轮产品 0 文件**，streak 到 %(STREAK)s；这不是"没干活"，是"六个候选各自都被数否掉了"，硬凑一个改动才是这轮能犯的最贵的错。
- **U-2429：老盲区补上另一通道的读数（本轮唯一的代码改动，在 `Tests/`）。** `materialBlindSpotFixtures` 的注释从前只有离屏一侧的证据 ⇒ "这块黑到底是产品画的还是通道画的"这句话账上**从没答过**；本轮把真机对照数写进去（+28/通道 vs 离屏 (0,0,0)），并明写这条名单**不许被读成"产品把选中行画黑了"**，它说的是"这几张帧里选中行的像素不可用作证据"。这格的价值不在新读数本身，而在**它把一处登记了 300 多轮的盲区从"单向断言"变成"双向对照"**。
- **U-2430：一把撤掉的判据（不登记、不留文件）—— 尺读错对象时撤，比修好话更便宜。** 想补的那一轴是真的缺口：现有三条判据（R475/R480/R487 族）判的都是"标记出现了没有"（成对帧的墨量差、末列差），**没有一条判它多大**。但我的尺把"时间行最右一段墨"当成标记，本机 2x 现读 `row-image-ocr 10.50×10.50pt 间隙=13px`、`row-link-text 8.50×5.50pt 间隙=2px`、`row-rich-text 1.50×2.00pt 间隙=3px` —— 后两枚读到的是**一枚字形里的一个笔画**（链环两圈之间、`格式` 两字之间都有 >2px 的空）；加 1pt 合并容差仍切不开。看图确认三枚标记真实墨高都 ≥8pt（`textformat` 在中文区域解析到 **CJK 变体**，画出来就是「格式」两个字，最宽约 22pt）⇒ **产品没有缺陷，是我的尺不成** ⇒ 判据整条 `git checkout` 撤掉，**没登记刀**（刀号 **M1463 未使用**，下一轮现读后仍从 M1463 起）。留一格真话：这条轴要判，得先有"标记区域"的**独立身份**（成对帧的负臂末列，或让产品自己报标记的取证键），不能拿"最右一段"凑。
- **U-2431：③ 验证链与④⑤ 账。** `swift build --build-tests` 告警 **0**；判据卷 `UICaptureTests` **%(CAPTURE)s**；帧 **%(FRAMES)s**（本轮没动产品、也没动任何被拍的视图 ⇒ 基线不该动，动了就是漏改）；全量 **%(FULL)s**；预检三读**串行** **%(PRECHECK)s**、`ARM_TOTAL %(ARM)s`、`HIDDEN_ARMS %(HIDDEN)s`；换装 %(INSTALL)s。清账 **%(ABSENCE)s**；电池 **%(BATTERY)s**（台账与 `--write` 之后复跑，只抄 `Ran`/`OK`/`FAILED`）；streak **台账落盘之后**现读 `python3 scripts/product_streak.py` ⇒ `%(STREAK_RAW)s`。**636 措辞已全账统一**；629 保持「(B) 已落地 + 635 已结案 + runner 三跑实测 2/5/0 ⇒ ≥2 在那台机器的钟上不是恒可满足」，两条出路仍等用户点头、本轮不自行登记 `sampled`；622/624/627 继续；628/625/626/569/616/632/634/635 已落地那半不重开；**633 仍等用户人工回执**（本轮没拿到 ⇒ 不写任何结论）。下一轮 R564（第 563 轮 / Round 561）：⓪ 必读本轮 push 头笔那一跑（取号时未创建 ⇒ 现在去读；中间笔具名 `CI_UNREAD`），头四格 = (a) `HEAT_LEGEND_*` 复核是否仍判到、(b) `BULLET_LEVELS` 在 1x 走哪条（两条出路已在 `### R563 补记` ③ 逐字写好）、(c) `过渡帧数` 第五数、(d) STEP[9]/[18]；**产品面这一格要请用户定向**：六个候选今天全被否掉，剩下的合法路径只有 632 的两格（② 合成一次取样 = 要重钉估高度算式并配刀；① 图片整文件读 = 账上已判"可接受"）或用户指定一个面 —— 我不再自己凑第三个候选。刀号 **M1463** 起（未使用）；禁碰清单 **11 面**不变（产品 0 文件 ⇒ 不抬数）。

"""


ITER = u"""
## Round 560 · R563（第 562 轮 · 2026-11-03）：六个候选位全部被现读否掉 —— 把一处盲区从"单向断言"改成"双向对照"，把一处矛盾账改齐，然后承认今天没有产品位

这一轮的靶要求落一个 `Sources/` 真实位（产品面已连续两轮 0 文件）。取靶走了六个候选，每一个都拿到自己的数之后再放弃：⓪(a) 修派生式——读数没到（那一跑 queued），而且它只是复核；636 三级尺寸契约——改的就是 `bulletGlyph`/`markerFont`，同时撞 R549 与 R560 两个禁碰面；侧栏选中行的纯黑带——先用真实捕获通道的视图树定位到 `NSVisualEffectView material=4`（选中层），再用**另一条通道**对照：真机里非选中行背景 (52,52,39)、选中行 (80,80,68)，每通道 +28 ⇒ 屏上选中态清楚可见，黑的是离屏合成，不是产品，而且这处早在 R206 就登记进 `materialBlindSpotFixtures`（注释里连 66pt 都写着）⇒ 不新开单，只把真机那条对照数补进名册，让它从"单向断言"变成"双向对照"；三枚行内标记的墨高——判据写到一半发现我的"最右一段墨"读的是**一枚字形里的一个笔画**（链环两圈、CJK 变体「格式」两字之间都有 >2px 的空），看图确认三枚都 ≥8pt ⇒ 产品无缺陷、尺不成，整条撤掉、不登记刀；`heatmap-empty` 的 3.95:1 是空热图的格子（装饰性数据底，不是文本）；选中行 66pt 是因为它标题排了两行，不是选中撑的。于是本轮产品 0 文件、判据 0 条、刀 0 把，落地的只有：把 `### R562 补记` ④ 那句与同一轮另外两处互斥的「636 本轮结案」按证据改成「半落地、单子继续开」（改措辞，不动任何门），和上面那条名册注释。写下来不难看：**"没找到缺陷"和"没干活"是两件事**——硬凑一个改动、或者拿判据账冒充产品位，才是这一轮能犯的最贵的错。产品面下一步要用户定向（632 的两格各有代价，或指定一个面），我不再自己凑第三个候选。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉看图 | 12/15 | 真看了：三张行帧的 meta 行 2 倍放大（看清 `link` 是链条、`textformat` 是 CJK 变体「格式」）、侧栏整列、真机截图（量完即删）；扣的三分是本轮没有新画面可看，看的全是老帧。 |
| 判据有效性 | 7/15 | 想补的那一轴（标记多大）是真缺口，但尺不成 ⇒ 整条撤掉，本轮判据 0 条。留了下一步的正确形状：标记身份要独立取证，不能拿"最右一段"凑。 |
| 假绿防御 | 14/15 | 撤判据而不是放宽它；不登记刀就不占号（M1463 未使用）；六个候选各自的否证都留了数（+28/通道、3.95:1、66/51 行高、1.5pt 笔画），下一轮不能拿同一批候选再猜一遍。 |
| 产品面推进 | 4/15 | 产品 0 文件、连第三轮（streak 到 %(STREAK)s）；这一维本轮确实没推进，账里不拿"改账 + 名册注释"抵它。 |
| 台账一致性 | 15/15 | 同一轮里 636 的两种说法交叉核对后统一（改措辞、不动门）；派生格落盘后现读；写手每一本都有幂等守卫、两种占位符形状都查、回读计数写进报告。 |
| 交付诚实性 | 15/15 | ⓪ 四格按 queued 具名 NOT-RUN；六个候选全部给出否证读数，没有一个是"感觉不像缺陷"；明写本轮没有产品位并请用户定向，不猜第三个候选。 |
| 可复核性 | 14/15 | 视图树读数、真机对照数、三枚标记的 px/pt 数、撤掉的判据形状全部进账；扣一分是真机截图未留档（隐私红线：主窗口含剪贴板内容，量完即删 ⇒ 只有数留在账上，别人无法重放那一步）。 |

"""


CHG = u"""### 侧栏选中行那块黑终于被分辨清楚：真机 +28/通道 vs 离屏 (0,0,0) ⇒ 是通道不是产品，名册从单向断言改成双向对照；六个候选位全部被现读否掉 ⇒ 本轮产品 0 文件、判据 0 条、刀 0 把（R563 / 第 562 轮 / Round 560）

看图第一发现是侧栏最后一行在 light 帧里是一整块 258×66pt 的纯黑。用真实捕获通道的视图树定位：`ListTableRowView x=0 y=397 w=280 h=66 selected=true` 里那枚 `NSVisualEffectView x=10 y=397 w=260 h=66 material=4` —— 系统给选中行铺的 vibrancy 层，离屏没有 backdrop 可合成就落纯黑。再用另一条通道对照：真机只截主窗口 750×492、逐行取侧栏背景，**非选中 (52,52,39) vs 选中 (80,80,68) ⇒ 每通道 +28**，屏上选中态清楚可见 ⇒ 黑的是通道。这处早在 R206 就登记进 `materialBlindSpotFixtures`（注释里连 66pt 都写着），所以本轮不新开单，只把真机那条对照数补进名册注释 —— 从前它只有离屏一侧的证据，"黑是产品还是通道"这句话账上从没答过。其余四个候选也各自拿到数后放弃：三枚行内标记（判据写到一半撤，我的"最右一段墨"读到的是笔画不是标记，`textformat` 在中文区域是 CJK 变体「格式」）；`heatmap-empty` 的 3.95:1 是装饰性空格子不是文本；选中行 66pt 是标题两行所致；636 的尺寸契约要撞 R549/R560 两个禁碰面。另落一格改账：`### R562 补记` ④ 的「636 本轮结案」与同一轮另外两处互斥 ⇒ 按证据改成「半落地、单子继续开」，没撤判据、没降地板、没加豁免。判据卷 %(CAPTURE)s；帧 %(FRAMES)s；全量 %(FULL)s；build 0 告警；电池 %(BATTERY)s；刀号 M1463 未使用；4.5 / 150 / 120ms / Motion ≥2 帧 / 2x 8.0pt / 1x 6.0pt / `probeInkFraction=3%` / `.contentFade` 0.20 一律未动。

"""


B636 = u"""    措辞统一（R563 改账）：R562 那一轮里 636 同时挂着两种状态 —— 轮次节 ②(b)/ 与台账笔 `5d71660` 写「半落地、单子继续开」，而 `### R562 补记` ④ 写「本轮结案」⇒ 互斥。按证据取**继续开单**：三级项目符的墨 bbox 是**只印不判**的读数，`◦`/`▪` 至今没有尺寸契约；要定一条就得改 `bulletGlyph`/`markerFont`，同时撞 **R549 与 R560** 两个禁碰面 ⇒ **归用户点头**。本轮没有撤任何判据、没有降任何地板、没有加豁免 —— 改的只是一个措辞（矛盾成因：补记笔沿用了上一轮的口径，没跟同一轮里已落盘的另外两处交叉核对）。
"""


DEC = u"""## D-563（R563 · 2026-11-03）：看图必须走到能分辨「通道 vs 产品」为止；尺读错对象就撤，不登记；「没找到缺陷」不等于「没干活」，硬凑才是错

① **一块黑要两条通道才算分辨完。** 侧栏选中行在离屏帧里是纯黑，这件事 R206 就登记进 `materialBlindSpotFixtures` 了，但登记只说了"离屏画成黑"，从没回答"产品自己黑不黑"。本轮补真机对照（非选中 (52,52,39) vs 选中 (80,80,68)，每通道 +28）⇒ 结论是通道。**一条只写"我们看到黑"的名单，会被后人读成"产品画了黑"** —— 盲区条目必须写清它是**哪一侧**的事实。
② **尺读错对象时，撤掉比修话便宜。** 想补的那一轴（三枚行内标记的墨高）是真缺口，但"时间行最右一段墨"这个定义在 `link`（链环两圈）与 `textformat`（中文区域解析成 CJK 变体「格式」两字）上都退化成笔画：现读 5.5pt / 2.0pt 宽。修法要么给合并容差（抬到能吞掉字间空，就会连文字一起吞）要么改判对象（要成对帧负臂或产品自报的取证键）——两条都不是本轮该顺手做的。**撤判据、不登记刀、把正确形状写进账**，比留一条会误红的尺便宜。
③ **候选被数否掉之后，剩下的合法路径要交给用户，而不是自己凑第三个。** 六个候选全部带数（queued、禁碰面、通道 artifact、尺坏、装饰性数据底、两行标题），继续自己找下去的边际收益已经低于"问一次"的成本 ⇒ 本轮明写：产品面下一步要么 632 的两格（各有代价），要么用户指定一个面。
④ **同一轮里的单子状态要交叉核对。** 636 的两种说法并存了一轮（轮次节 + 台账笔 vs 补记 ④）——补记是那一轮**最后**写的笔，它用了上一轮的措辞。规矩：写补记时把本轮已落盘的所有提法 grep 一遍再下笔；收口报告要把同一单子的两处说法对照读一次。
⑤ **边界**：本轮的"没干活"是可复核的没干活 —— 六个候选每个都留了否证读数；如果下一轮仍拿不出产品位，那就不是取靶问题，是**清单问题**（该问用户要靶，而不是再猜）。
"""


def insert_after_line(t, line_prefix, block, label):
    u"""按**行首前缀**定位那一行，插到它后面。"""
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


def guard(t, marker, label):
    """幂等守卫：**每一本都要有**（R562 只给一本加 ⇒ 中途崩之后重跑把 UI 那一本写成两份）。"""
    if marker in t:
        sys.stderr.write("ALREADY_WRITTEN %s ⇒ 先去重再写，不许重跑\n" % label)
        sys.exit(1)


def fill(text):
    out = text
    for key, value in NUM.items():
        out = out.replace(u"%%(%s)s" % key, value)
    if u"%(" in out:
        i = out.find(u"%(")
        sys.stderr.write("PLACEHOLDER_LEFT %s\n" % out[i:i + 30])
        sys.exit(1)
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
    if state.count(u"## R563 ⓪ 开工") != 1:
        sys.stderr.write("ANCHOR_BAD state R563 ⓪ 节不存在 ⇒ 不许两轮写进同一节\n")
        return 1
    if u"## R563 状态（" in state:
        sys.stderr.write("ANCHOR_BAD state R563 状态节已存在\n")
        return 1

    n = "AGENT_UI_AUDIT.md"
    t = rd(n)
    guard(t, u"## 第 562 轮（R563", u"ui")
    a = u"## 第 561 轮（R562 · 2026-11-03 · U-2419…U-2425）"
    if t.count(a) != 1:
        sys.stderr.write("ANCHOR_BAD ui\n")
        return 1
    if not check:
        wr(n, t.replace(a, fill(UI) + a, 1))

    n = "AGENT_VISUAL_ITERATION.md"
    t = rd(n)
    guard(t, u"## Round 560 · R563", u"iteration")
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
    guard(t, u"（R563 / 第 562 轮 / Round 560）", u"changelog")
    if not check:
        wr(n, t.replace(a, a + fill(CHG), 1))

    n = "AGENT_BACKLOG.md"
    t = rd(n)
    guard(t, u"    措辞统一（R563 改账）", u"backlog636")
    t = insert_after_line(t, u"    退场条件（原两格都不该硬套，本轮落的是第三条，且只满足一半）", B636, u"backlog636-anchor")
    if not check:
        wr(n, t)

    n = "AGENT_DECISIONS.md"
    t = rd(n)
    guard(t, u"## D-563", u"decisions")
    if not t.endswith(u"\n"):
        t += u"\n"
    if not check:
        wr(n, t + fill(DEC))

    n = "AGENT_FINAL_REPORT.md"
    t = rd(n)
    guard(t, u"R563 续到 563", u"final-report")
    for old, new, label in [
        (u"R9–R559，560 节自评", u"R9–R560，561 节自评", u"title"),
        (u"阶段二 **552 轮**审计（R9–R559；以 `curve_from_ledger.py` 的 `PHASE2 n=552` 为准，最新一节是 `AGENT_VISUAL_ITERATION.md` 的 Round 559",
         u"阶段二 **553 轮**审计（R9–R560；以 `curve_from_ledger.py` 的 `PHASE2 n=553` 为准，最新一节是 `AGENT_VISUAL_ITERATION.md` 的 Round 560", u"§1"),
        (u"| 视觉台账 | U-31 … U-2425", u"| 视觉台账 | U-31 … U-2431", u"U 上界"),
        (u"以 `AGENT_STATE.md` 的 R562 节 ② 为准", u"以 `AGENT_STATE.md` 的 R563 节 ② 为准", u"state pointer"),
        (u"## 18. R458 → R562 这一段", u"## 18. R458 → R563 这一段", u"§18 head"),
        (u"R562 续到 562 —— 这份报告第七次差点停在几十轮之前）",
         u"R563 续到 563 —— 这份报告第七次差点停在几十轮之前）", u"§18 tail"),
    ]:
        t = once(t, fill(old), fill(new), label)
    anchor = u"全量 1405/57/0（686.4s）；build 0 告警；电池 696/5。\n"
    bullet = (u"- **R563（六个候选位全部被现读否掉；产品 0 文件、判据 0 条、刀 0 把）**："
              u"看图第一发现是侧栏最后一行在 light 帧里是一整块 258×66pt 纯黑 ⇒ 视图树定位到 "
              u"`NSVisualEffectView material=4`（系统给选中行铺的 vibrancy），**再用真机对照：非选中 (52,52,39) vs 选中 (80,80,68) ⇒ 每通道 +28，屏上选中态清楚可见** "
              u"⇒ 黑的是通道不是产品，且这处 R206 就登记进 `materialBlindSpotFixtures` ⇒ 不新开单，"
              u"只把名册从**单向断言**改成**双向对照**。三枚行内标记的墨高判据写到一半撤掉（我的"
              u"「最右一段墨」读到的是笔画：`link` 链环两圈、`textformat` 在中文区域是 CJK 变体「格式」）⇒ 尺不成，"
              u"**不登记刀、M1463 未使用**。另落一格改账：`### R562 补记` ④ 的「636 本轮结案」与同一轮另外两处互斥 ⇒ 按证据改成「半落地、单子继续开」（没撤判据、没降地板）。"
              u"⓪ 那跑开场 queued ⇒ 四格具名 NOT-RUN。判据卷 %(CAPTURE)s；帧 %(FRAMES)s；全量 %(FULL)s；build 0 告警；电池 %(BATTERY)s。\n")
    t = once(t, anchor, anchor + fill(bullet), u"§18 bullet")
    if not check:
        wr(n, t)

    n = "AGENT_STATE.md"
    t = rd(n)
    guard(t, u"## R563 状态（", u"state")
    body = u"""## R563 状态（2026-11-03 · 第 562 轮 / Round 560 · 产品 0 文件 + 判据 0 条（撤一把）+ 刀 0 把 + 一处改账）

①  那跑：`41531750912↔75b32d6`（R562 那一批头笔 = 补记笔）开场 **queued（229s）**、`steps` 的 `conclusion=` 空串 ⇒ 四格当时具名 NOT-RUN（(a) `HEAT_LEGEND_*` 复核、(b) `BULLET_LEVELS` 在 1x 走哪条、(c) `过渡帧数` 第五数、(d) STEP[9]/[18]）；同批无独立跑 ⇒ `CI_UNREAD`（R562 四笔 + R561 三笔 + R560 五笔 + R558 两笔）；cancelled 两笔永不重开。%(CI_CLOSE)s
② ⓪ 附加的一格**改账**：`### R562 补记` ④ 从前写「636 本轮结案」，与同一轮里轮次节 ②(b)/⑤ 和台账笔 `5d71660` 的「半落地、单子继续开」互斥 ⇒ 按证据取后者并逐字改齐（墨 bbox 只印不判；定尺寸契约要撞 R549/R560 两个禁碰面 ⇒ 归用户）。**没撤判据、没降地板、没加豁免**；成因写进账（补记笔沿用上一轮措辞、没跟同一轮已落盘的两处交叉核对）。
③ ② 第二格（要求落 `Sources/`）：**六个候选全部被现读否掉 ⇒ 产品 0 文件**。③-a 修派生式 = 读数没到（queued）且只是复核；③-b 636 尺寸契约 = 撞两个禁碰面；③-c 侧栏选中行纯黑带 = 视图树定位到 `NSVisualEffectView material=4`，**真机对照 (52,52,39) vs (80,80,68) ⇒ 每通道 +28 ⇒ 黑的是通道**，且 R206 已登记进 `materialBlindSpotFixtures` ⇒ 不新开单；③-d 三枚行内标记墨高 = 判据写到一半**撤掉**（"最右一段墨"在 `link`/`textformat` 上读成笔画，实测 5.5pt/2.0pt 宽；三枚真实墨高都 ≥8pt）⇒ 不登记刀、**M1463 未使用**；③-e `heatmap-empty` 3.95:1 = 装饰性空格子不是文本；③-f 选中行 66pt = 标题两行所致（五行 66/51/51/51/66）。唯一代码改动在 `Tests/`：把 ③-c 的真机对照数补进名册注释 ⇒ 那处盲区从**单向断言**变成**双向对照**。
④ ③ 验证链（顺序未换）：`swift build --build-tests` 告警 **0**；判据卷 **%(CAPTURE)s**；帧重捕 **%(FRAMES)s**（没动产品、没动任何被拍视图 ⇒ 基线不该动）；全量 **%(FULL)s**；预检 **%(PRECHECK)s**、`ARM_TOTAL %(ARM)s`、`HIDDEN_ARMS %(HIDDEN)s`（三读**串行**）；换装 %(INSTALL)s。
⑤ ④⑤ 账与交接：清账 **%(ABSENCE)s**；电池 **%(BATTERY)s**（台账与 `--write` 之后复跑）；产品面连续零改动 **%(STREAK)s** 轮（**台账落盘之后**现读 `python3 scripts/product_streak.py` ⇒ `%(STREAK_RAW)s`）。**636 措辞已全账统一、单子继续开**；629 保持「(B) 已落地 + 635 已结案 + runner 三跑实测 2/5/0 ⇒ ≥2 在那台机器的钟上不是恒可满足」，两条出路等用户点头、本轮不自行登记 `sampled`；622/624/627 继续；628/625/626/569/616/632/634/635 已落地那半不重开；**633 仍等用户人工回执**（本轮没拿到 ⇒ 不写任何结论）。⑥ 一次性 push（本轮四笔：⓪ 开工 + A 名册注释 + 台账 + 补记）⇒ 只有头笔建跑。R564 ⓪ 必读它；头四格 = `HEAT_LEGEND_*` 复核 / `BULLET_LEVELS` 在 1x 走哪条（两条出路预先写死）/ `过渡帧数` 第五数 / STEP[9]+STEP[18]。**产品面请用户定向**：六个候选今天全被数否掉，剩下合法路径只有 632 的两格（各有代价）或指定一个面。刀号 **M1463** 起（未使用）；禁碰清单 **11 面**不变（产品 0 文件 ⇒ 不抬数）；4.5 地板、150 上限、120ms、Motion ≥2、2x 8.0pt、1x 6.0pt、`probeInkFraction=3%`、`.contentFade` 0.20 一律不动。

"""
    a = u"\n## R563 ⓪ 开工（2026-11-03 · 第 562 轮 / Round 560 · CI 读单 + 基线全现读 + 一处账内矛盾改账 + 产品位待挑）"
    t = once(t, a, u"\n" + fill(body).rstrip(u"\n") + a, u"state body")
    if not check:
        wr(n, t)

    sys.stdout.write("LEDGERS_R563_%s\n" % ("CHECK_OK" if check else "WRITTEN"))
    return 0


if __name__ == '__main__':
    sys.exit(main())

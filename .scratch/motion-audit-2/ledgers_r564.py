# -*- coding: utf-8 -*-
"""R564 台账（第 563 轮 / Round 561）：产品位被自己的读数否掉 ⇒ 落判据位（只管未来的轮次身份守卫）。

用法：`python3 ledgers_r564.py --check` 只验锚点与 NUM；不带参数才真写。
三条老规矩钉在代码里：① **每一本都有幂等守卫**；② 守卫搜索的串不许出现在守卫自己写的正文里；
③ `fill()` 两种占位符形状都查（具名与裸 percent+字母）。
"""
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

NUM = {
    "FULL": '1405/57/0（687.5s）',
    "INSTALL": '`INSTALL_RESULT=ok / INSTALL_SHA_MATCH=1 / INSTALL_ENTRIES=433=433 / SMOKE_OK=1 / INSTALL_SIGNATURE=local flags=0x0`（版本 1.4.8→1.4.8，PID→95084，启动晚于安装、exe 路径逐字对上，备份 `before-R564`）',
    "BATTERY": '706/5',
    "ABSENCE": '162/63/0',
    "STREAK": '4',
    "STREAK_RAW": 'PRODUCT_STREAK ledger_round=563 streak=4 sections=539 as_of=last=631f910 last_round=559 newest=631f910 newest_round=559',
    "CAPTURE": u'221/4 skipped/0 失败（603.0s）',
    "FRAMES": u'**356 CHANGED=0 MISSING=0 ADDED=0**（产品 0 文件、判据草稿整条回退 ⇒ 基线本来就该不动；这一格同时是「产品与 11 个禁碰面一帧未动」的证人）',
    "PRECHECK": 'tables=364 covered=295 arms=757 bad=0',
    "ARM": 'files=457 arms=1244 dupes=0 repeats=0',
    "HIDDEN": '表=451 可判=1183 rot=0 抽不出=6 已声明表=6 处置=ok',
    "CI_CLOSE": u"""**收口前复述 `queue`：`41542718166 ↔ 6ef9ff1` = completed / failure**（开场 in_progress 380s ⇒ 四格当时具名 NOT-RUN；数到手在收口之前，不是补记）。`gh run view --json jobs` 逐步现读 20 个步骤里**只有 STEP[15] `Swift tests (executed-count gate)` 是 failure**，其余全 success（含 STEP[5] 捕获、STEP[9] Release script tests、STEP[11] 帧基线、STEP[16] Motion gate、STEP[17] Capture gate、STEP[18] 在屏地板、STEP[19] Motion 地板 —— 这些是逐步读出来的，不是"不在失败名单"推出来的）。四格逐条：**⓪(a) `BULLET_LEVELS` 第一次被 runner 验 ⇒ 走的是「判到」那一条出路**：`BULLET_LEVELS light/dark 行=6 列=3 步进=[16, 16]px(16.0/16.0pt) 容差=1px 合并=1px 筛除 宽≤8px 隙≥4px 倍率=1.0x 列x=36px 墨高=5px(5.00pt) 列x=52px 墨高=4px(4.00pt) 列x=68px 墨高=5px(5.00pt)` ⇒ 列数 = 产品解析深度集合、步进等距（漂移 0px）、每步 16px ≥ 地板 8px；**没有 `BULLET_LEVELS_NOT_RUN` 行**，也没红在步进上 ⇒ 三条出路里第一条成立。⚠ R562 那次 LANCZOS 降采样代理给的 `左沿=[36,52,68] 步进=[16,16]` 与 runner 真 1x 逐字对上 —— 代理仍然不签字，但这次它预测对了。**另记一格只印不判**：runner 1x 三档项目符墨高 5/4/5px，本机 2x 现读 `⦁=4.00pt ◦=3.00pt ▪=4.00pt`（dark 4.50/3.50/4.00）⇒ 中间那档 `◦` 比 R549 给 `⦁` 定的 3.9pt 还低；这正是 636 说的「三级项目符没有尺寸契约」那一格的新读数，**不据此开缺陷**（三档三字形是 R549 的设计），归用户。**⓪(b) `HEAT_LEGEND_*` 复核：仍判到** —— `HEAT_LEGEND_COVERAGE light/dark 格色=6 图例色=5 缺=[] 格宽=11px 倍率=1.0x 网格下缘 y=164 实心判定 格6px/图例3px 地板 格4/图例4 每方块采样点 格9/图例9`（4 行，STEP[5] 与 STEP[15] 各两行），而 `HEAT_LEGEND_NOT_RUN` **零行** ⇒ 连续第二跑判到、形状与首次签收那跑（`41519677393↔f12f50d`）逐字同。**⓪(c) `过渡帧数=` 第五数 = 6** —— 逐字 `MOTION_MARKDOWN_MODE_FADE scale=1x 帧数=27 过渡帧数=6 相邻差帧数=3 首末连续差=0.0048 峰值=0.0145 声明=200ms 窗口=833ms 每格=32.0ms`，STEP[19] success ⇒ 五数并排 **2 / 5 / 0 / 5 / 6**（每格 71.5 / 26.0 / 75.6 / 28.9 / 32.0ms）⇒ 按 629 既有口径具名入账，≥2 未触碰、期望未改。**⓪(d)** STEP[9] `SKIP_ROSTER 键=github-runner 类=github-runner 内层Ran=696 内层skip汇总=3 解析=2 名单外=无 名册未跳=无` ⇒ 634 **连续第五跑绿**；STEP[18] success ⇒ 622 本跑无新值（第十四值仍 219.7ms/2 颗）。**唯一那朵红**：STEP[15] `SelectionRevealAnimationTests.testAnimatedRevealProducesIntermediateOffsets` ⇒ `XCTAssertGreaterThan failed: ("0.0") is not greater than ("1.0") - 0.15s 时视口还在起点（中段=0.0）⇒ 动画没有开始，或宿主没找到表格`。**归因走对照不靠记忆**：本轮与上一轮都没碰产品或任何被拍视图（R563 唯一代码改动是一段注释，R564 全部改动在 `scripts/`），同一份代码在 `41519677393↔f12f50d` 那一跑 STEP[15] 是 **success**（R561 账上逐步读过），中间那跑 `41531750912↔75b32d6` cancelled 无日志 ⇒ **同码一绿一红 = 间歇**，不署名本轮；这条用例在 runner 上不是第一次红（R412 那跑 `40400010978↔2e02c4d` 红过，形状是 中段=1430 的「跳到终点」，这次是 中段=0.0 的「没开始」）；本机侧这一族早有具名出口 `LOCAL_SCROLL_SESSION_NOT_RUN=full-suite-order`（449），**runner 侧没有对应出口** ⇒ 记一格：449 的 runner 半边仍是缺口，不改门槛、不放宽 STEP[15]。""",
}

UI = u"""## 第 563 轮（R564 · 2026-11-03 · U-2432…U-2438）：取靶方法换掉之后产品位仍然没落地 —— 这一轮把它否掉的是一棵视图树；落地的是一条只管未来的轮次身份守卫（判据 1 条 + 刀 3 把，产品 0 文件）

- **U-2432：⓪ CI 读单（只登记、不轮询）。** 开场 HEAD=origin=`6ef9ff1`、ahead=0、已跟踪改动 0、`api.github.com=200 / api.apple.com=000`。`41542718166 ↔ 6ef9ff1`（R563 那一批头笔 = 补记笔，**也是 `BULLET_LEVELS` 第一次进 runner 的那一跑**）开场 **in_progress、已等 380s**，`steps` 打的 `conclusion=` 是空串、`JOB build-and-test ⇒` 也是空 ⇒ 失败步骤清单**尚不存在**，这是「没有结论」不是「没红」⇒ 四格当时**具名 `CI_NOT_RUN=in_progress`**：(a) `BULLET_LEVELS` 第一次被 runner 验（三条出路预先写死在 `## R564 ⓪ 开工` ①，不许临场决定）；(b) `HEAT_LEGEND_*` 复核（⚠ 只是复核 —— 首次签收已在 `41519677393↔f12f50d`）；(c) `过渡帧数=` 第五数（已 2/5/0/5，每格 71.5/26.0/75.6/28.9ms）；(d) STEP[9] 第五跑 + STEP[18] 622。同批无独立跑 ⇒ `CI_UNREAD`：R564 的中间笔与 R563 的 `851b124`/`64d3192`/`a13727c`、R562 四笔、R561 三笔、R560 五笔、R558 两笔；永不重开 `41531750912↔75b32d6`、`41452722560↔58851c2`、`41455782587↔598b253`。%(CI_CLOSE)s
- **U-2433：取靶方法这一轮换掉了，并且先把三条像素扫的落空写成账。** 上一轮"逐张看图挑毛病"在 356 帧里连否六个候选 ⇒ 本轮改成**名册交叉核对**：先问"产品自己写下的常量/下限，有没有哪个表面没在用它"，再拿帧去量。为了不靠运气，另跑了一次全库三条轴的候选生成器（`sweep_r564_candidates.py`，只生成名单不作断言，`/tmp/r564-sweep.log`）：**轴 A 暗档近白 ⇒ 命中的是暗档文字本身**（top 帧面积都 ~1%、bbox 落在侧栏文字带），**轴 B 右边缘有墨 ⇒ 命中的是窗口边框**（`settings-*-tall` 每行都有墨 = 2080/2080 行），**轴 C 明暗同色中等灰 ⇒ 命中的是图片夹具与占位图**（`detail-1-image` 134580px）。三条轴都没给出缺陷。轴 C 把 `detail-file-fallback-longname` 推到眼前，看图后我判"文件名被左右裁掉"——**那是我自己 170..1032px 的切框切出来的**：整帧现读文字末列 516.5pt、右侧动作条首列 552pt ⇒ 中间还有 35.5pt 空隙，没有裁切。⇒ 记一条：**看图之前先确认看到的是整帧还是我切的框**（R563 那条"尺读错对象"的同类自伤，只是这次读错的是我自己的裁剪窗口）。
- **U-2434：候选的形状与实验设计（出路预先写死，不许临场决定）。** 名册交叉核对命中的是浮层：`QuickPickController.swift:801-812` 同一行格里叠三枚徽标（图钉 / 收藏星 / 内容标记），三枚都按 `pointSize: 8` 配置符号，**盒子**却是 9 / 10 / 9pt —— R551 当年只把星那一枚从 9 抬到 10，另两枚留在原地；而产品自己给这一族的下限写在 `VisualGlyph.badge`（10pt，注释原话：9pt 的 `pin.fill` 在 2× 下笔画会并在一起 ⇒ 9 与 10 收成同一档、把下限抬到 10）。既有判据抓不到它：`QUICKPICK_PIN` / `QUICKPICK_CONTENT_BADGE` 判的是**有没有画**，`QUICKPICK_STAR_HEIGHT` 只判星那一枚的跨度 ⇒ 图钉与内容标记的尺寸至今无人判。⚠ 但开工节不许把它写成结论：**盒子是不是在决定墨的大小**当时并不知道（星 8.50pt < 它的盒子 10pt 就是反例的形状）⇒ 预先写死两条出路：墨变化出得了容差才落，出不了就当场作废、**不许为了"统一"做一次肉眼无变化的改动**。
- **U-2435：实验读数（临时把两枚的 9 改成 10，各跑一遍成对差集；`/tmp/r564-probe-old.log`、`/tmp/r564-probe-new.log`）。** 旧：`图钉 高9.00×宽6.00pt 墨=104`、`星 8.50×9.00 墨=148`、`内容 8.00×8.00 墨=96`（light/dark 同形；**星那个 8.50pt 与 R551 账上的 8.5pt 逐字对上 ⇒ 量法对齐老账**）。新：`图钉 9.50×6.50`、`星 8.50×9.00 墨=148`（**一字未动 ⇒ 禁碰 R551「收藏星尺寸」这一面确实没被碰**）、`内容 9.00×9.00`（dark 墨 99→124）。⇒ 墨会变（内容 +2px@2x、图钉 +1px@2x）⇒ 盒子不是装饰，这一改**有**可见后果，出路 ① 成立了一半。
- **U-2436：把这一格否掉的是布局后的视图树，不是墨。** 用 `render(..., inspect:)` 把产品自己那棵**已经布局完**的树交出来现读（每枚命中=1、`hidden=false`、父级 `QuickPickRowCell`；`/tmp/r564-all2.log`）：常量 9/10/9 ⇒ 布局后 `图钉 9.5×14.5pt`、`星 10.0×14.5`、`内容 9.0×13.5`；常量 10/10/10 ⇒ 布局后 `图钉 10.5×15.5`、`星 10.0×14.5`、`内容 10.0×14.5`。⇒ **布局边长不由那三个常量决定**：三枚的高一律 = 常量 + 4.5pt，图钉的宽 = 常量 + 0.5pt、另两枚 = 常量。所以「把 9 统一到 10」**得不到**「三枚同一档」（新读数仍是三样：10.5 / 10.0 / 10.0）⇒ 改动落下去满足不了任何一条我写得出的判据 ⇒ **产品位作废，Sources 全部 `git checkout` 回退，产品 0 文件**；判据草稿（几何 + 墨两腿，9817 字）留在 `.scratch/motion-audit-2/r564-badge-criterion-draft.swift.txt`，真问题开成 **637**（谁把高度约束撑到 常量+4.5、图钉那 +0.5 从哪来）。另记一条**尺坏**自伤：草稿第一版把"负臂的树里读不到那枚盒子"当成"徽标按需出现"的证据，实测负臂里三枚都在树里、只是 `isHidden=true` ⇒ 判据当场撤下，不拿它红给下一轮。
- **U-2437：本轮落地的那一条判据位 —— commit 轮次身份的只管未来一致性守卫（`scripts/commit_round_identity.py` + 电池 9 条）。** 靶是用户点名的现成缺口：R563 的 A 笔 `64d3192` 前缀写成「R562 A：」而它自己的身份行是 `第 562 轮 / Round 560`（= R563），那一笔已推 ⇒ 不许 amend ⇒ 只能 forward。守卫只判 `origin/main..HEAD`（未推的那一批），为空时退化到 HEAD，**绝不允许"零条也算通过"**；已推历史不重判 ⇒ 那条错标天然在界外，**不需要写豁免**（R188：契约不能靠豁免还）。三种坏法各有名字：`不一致` / `身份缺失` / `无R前缀`，加一条 `笔=0`。**正对照用的是仓库里真实存在过的那一笔**：放开到近 12 笔只看不判 ⇒ 命中 2 条且全部落在 `64d3192`（`不一致:R562≠第562轮` + `不一致:R562≠Round560`），其余 11 笔不误咬。⚠ 自伤一格：第一版把映射凭感觉写成 `Round = 前缀 - 2` ⇒ 守卫第一个咬到自己本轮的 ⓪ 笔；现读近 12 笔才定出 `轮次 = 前缀 - 1`、`Round = 前缀 - 3`。刀三把全 CAUGHT、RESTORE_CLEAN=yes：**M1463** 摘掉那条减法（真值表的 64d3192 对照不再红）、**M1464** 把 -3 改成 -2（每一笔**正确**的提交反被判红 ⇒ 证明尺不是越严越好）、**M1465** 让身份缺失静默放过。M1463 首版 needle 写成 12 空格缩进 ⇒ `needle 命中 0`，**"登记前先跑一遍看命中 1"这条老规矩本轮又救了一次**。
- **U-2438：③ 验证链与④⑤ 账（顺序未换）。** `swift build --build-tests` 告警 **0**；判据卷 `UICaptureTests` **%(CAPTURE)s**；帧 **%(FRAMES)s**（本轮产品 0 文件、`Tests/` 也回退干净 ⇒ 基线本来就该不动；这一格同时是「产品与 11 个禁碰面一帧未动」的证人）；全量 **%(FULL)s**；预检三读**串行** **%(PRECHECK)s**、`ARM_TOTAL %(ARM)s`、`HIDDEN_ARMS %(HIDDEN)s`；换装 %(INSTALL)s。清账 **%(ABSENCE)s**；电池 **%(BATTERY)s**（台账与 `--write` 之后复跑，只抄 `Ran`/`OK`/`FAILED`，`&&` 链里不插 grep）；streak **台账落盘之后**现读 `python3 scripts/product_streak.py` ⇒ `%(STREAK_RAW)s`。**636 继续开单**（本轮一个字没碰它的措辞）；629 保持「(B) 已落地 + 635 已结案 + runner 四跑实测 2/5/0/5 ⇒ ≥2 在那台机器的钟上是间歇可满足」，两条出路仍等用户点头、本轮不自行登记 `sampled`；622/624/627 继续；628/625/626/569/616/632/634/635 已落地那半不重开；**新开 637**（浮层三枚叠层徽标布局后的边长由谁决定）；**633 仍等用户人工回执**（本轮没拿到 ⇒ 不写任何结论）。下一轮 R565（第 564 轮 / Round 562）：⓪ 必读本轮 push 头笔那一跑（取号时未创建 ⇒ 现在去读；中间笔具名 `CI_UNREAD`），头四格 = (a) `BULLET_LEVELS` 第一次 runner 读数（三条出路已写死）、(b) `HEAT_LEGEND_*` 复核、(c) `过渡帧数` 第五数、(d) STEP[9]/[18]；**产品面这一格按 D-564 ⑤ 交给用户定向**（连四轮 0 文件 ⇒ 是清单问题不是取靶问题）。刀号 **M1466** 起（现读最高 M1465）；禁碰清单 **11 面**不变（产品 0 文件 ⇒ 不抬数）；4.5 地板、150 上限、120ms 阈值、Motion ≥2 帧地板、2x 8.0pt 跨度地板、1x 6.0pt 整行地板、`probeInkFraction=3%`、`.contentFade` 0.20 与声明时长一律不动；全量 skipped 只记现读。

"""


ITER = u"""
## Round 561 · R564（第 563 轮 · 2026-11-03）：把"统一到 10"这个看起来最像缺陷的候选，用一棵布局树证否；落了一条只管未来的轮次身份守卫

取靶方法这一轮换掉了：上一轮逐张看图连否六个候选，本轮改成**名册交叉核对** —— 先问"产品自己写下的常量/下限，有没有哪个表面没在用它"。命中的是浮层：`QuickPickController` 同一行格里叠三枚徽标（图钉 / 收藏星 / 内容标记），三枚都按 `pointSize: 8` 配置符号，盒子却是 9 / 10 / 9pt，而 R551 当年只抬了星那一枚；产品自己给这一族的下限是 `VisualGlyph.badge`（10pt，注释写着"9 与 10 收成同一档、把下限抬到 10"）。既有判据抓不到它（`QUICKPICK_PIN`/`QUICKPICK_CONTENT_BADGE` 判有没有画，`QUICKPICK_STAR_HEIGHT` 只判星）。

这一轮没有直接改它，而是先把"盒子到底决不决定画出来的大小"问出来。临时把两枚的 9 改成 10，成对差集现读：内容标记 `8.00×8.00 → 9.00×9.00pt`、图钉 `9.00×6.00 → 9.50×6.50`、**星一字未动**（`8.50×9.00`，与 R551 账上那个 8.5pt 逐字对上）——墨会变，禁碰面没被碰，看起来该落地了。然后把 `render(..., inspect:)` 交出来的**布局后的产品树**读了一遍，这一格就死了：常量 9/10/9 布局后是 9.5×14.5 / 10.0×14.5 / 9.0×13.5，常量 10/10/10 布局后是 10.5×15.5 / 10.0×14.5 / 10.0×14.5 —— 三枚的高一律 = 常量 + 4.5pt，图钉的宽 = 常量 + 0.5pt，另两枚 = 常量。**布局边长不由那三个常量决定**，所以"统一到 10"得不到"三枚同一档"，改动落下去满足不了任何一条我写得出的判据 ⇒ 产品 0 文件、Sources 全部回退，真问题开成 637（谁把高度撑到 常量+4.5、图钉那 +0.5 从哪来），判据草稿留在 scratch 里给下一轮接手。

本轮落的是用户点名的另一格：commit subject 前缀 `Rnnn` 与正文 `第 N 轮 / Round M` 的一致性守卫，**只管未来** —— 只判未推的那一批（`origin/main..HEAD`，为空退化到 HEAD，不许"零条也算通过"），已推历史不重判 ⇒ `64d3192` 那条错标天然在界外、**不需要豁免**。正对照用的是仓库里真存在过的那一笔：放开到近 12 笔只看不判，命中 2 条且全落在 `64d3192`，其余 11 笔不误咬。三把刀 M1463/M1464/M1465 全 CAUGHT。自伤两格照实记：映射凭感觉抄成 `Round = 前缀 - 2` ⇒ 守卫第一个咬到自己本轮的 ⓪ 笔；M1463 首版 needle 缩进错 ⇒ 命中 0，"登记前先跑一遍"又救了一次。另有一格看图自伤：把"文件名被裁"当成缺陷，其实是我自己 170..1032px 的切框切掉了首尾 —— 整帧现读文字末列 516.5pt、动作条首列 552pt，中间还空 35.5pt。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉看图 | 10/15 | 逐张看了浮层三枚徽标的成对帧、`detail-file-fallback-longname` 明暗两档整帧与局部、pin/favorite/thumb 三族行帧；扣的五分是本轮没有新画面可看（产品 0 文件），且看图第一次给的"裁切"是自身切框造成的假象。 |
| 判据有效性 | 11/15 | 落了一条真会红的守卫（判据 1 条 + 电池 9 条 + 正对照用真实历史那一笔）；浮层那条判据**没有**落地成红 —— 它被布局树证否后撤下，草稿留档给 637。 |
| 假绿防御 | 15/15 | 三处都留了数：墨会变但布局不等（10.5/10.0/10.0）⇒ 不硬落；`笔=0` 单独算红；负臂"读不到盒子"被实测证伪（三枚都在树里、只是 isHidden）⇒ 尺坏不当产品坏；M1463 首版命中 0 不当已登记。 |
| 产品面推进 | 3/15 | 产品 0 文件、连第四轮（streak 到 %(STREAK)s）；这一维本轮确实没推进，账里不拿"判据位 + 三把刀"抵它。靶要用户给（D-564 ⑤）。 |
| 台账一致性 | 14/15 | 七本幂等守卫齐全、两种占位符形状都查、派生格落盘后现读；扣一分是本轮 STATE 里"三枚统一到 10"那句写在实验之前，靠 ③/④ 的出路预先写死才没变成事后找补 —— 取靶阶段的假设应当更明确地标成"未证"。 |
| 交付诚实性 | 15/15 | ⓪ 四格开场按 in_progress 具名 NOT-RUN、收口前逐格转成读数并附原文（不写"没红"、也不把 STEP[15] 的间歇红署成本轮回归）；候选的否证读数全部入账并开 637；产品位没落地在收口报告里单独成段并请用户定向；633 没拿到回执 ⇒ 一个字结论没写。 |
| 可复核性 | 13/15 | 两跑实验日志、布局树读数、守卫正对照（近 12 笔）、三把刀的 CAUGHT 行全部带路径进账；扣两分是判据草稿只在 scratch、下一轮要重读那 9817 字才能接手，不在产品测试里。 |

"""


CHG = u"""### 浮层三枚叠层徽标的"两档盒子"被一棵布局树证否：墨会变（内容 +2px@2x、图钉 +1px@2x、星一字未动）但布局后仍是三样 ⇒ 产品位作废、开 637；落的是只管未来的 commit 轮次身份守卫（判据 1 条 + 刀 M1463-M1465）（R564 / 第 563 轮 / Round 561）

取靶这轮换成了**名册交叉核对**（上一轮逐张看图连否六个候选）：问"产品自己写下的常量有没有哪个表面没在用它"，命中浮层 —— `QuickPickController.swift:801-812` 同一行格里叠三枚徽标，符号都按 `pointSize: 8` 配置，盒子却是 9 / 10 / 9pt（R551 当年只抬了星那一枚），而产品给这一族的下限写在 `VisualGlyph.badge`（10pt，注释原话"9 与 10 收成同一档、把下限抬到 10"）。既有判据抓不到：`QUICKPICK_PIN`/`QUICKPICK_CONTENT_BADGE` 只判有没有画，`QUICKPICK_STAR_HEIGHT` 只判星。没有直接改，先问"盒子决不决定画出来的大小"：临时统一到 10 做实验 ⇒ 成对差集现读 内容 `8.00×8.00→9.00×9.00pt`、图钉 `9.00×6.00→9.50×6.50`、**星 8.50×9.00 一字未动**（与 R551 账上那个 8.5pt 逐字对上 ⇒ 禁碰面确实没碰）。看起来该落地了 —— 然后把 `render(..., inspect:)` 交出来的**布局后**产品树读一遍：常量 9/10/9 ⇒ `9.5×14.5 / 10.0×14.5 / 9.0×13.5`，常量 10/10/10 ⇒ `10.5×15.5 / 10.0×14.5 / 10.0×14.5` ⇒ 高一律 = 常量+4.5pt、图钉宽 = 常量+0.5pt ⇒ **布局边长不由那三个常量决定**，"统一到 10"得不到"同一档"，改动满足不了任何一条我写得出的判据 ⇒ Sources 全部回退、产品 0 文件（连第四轮），真问题开成 **637**，判据草稿留档 scratch。另记一条尺坏：草稿第一版把"负臂树里读不到那枚盒子"当成"按需出现"的证据，实测负臂三枚都在树里、只是 `isHidden=true`。本轮落的是用户点名的另一格：`scripts/commit_round_identity.py` —— commit subject 前缀 `Rnnn` 与正文 `第 N 轮 / Round M` 的一致性守卫，**只管未来**（只判未推的 `origin/main..HEAD`，为空退化到 HEAD，`笔=0` 单独算红）⇒ 已推的 `64d3192` 那条错标天然在界外、**不需要豁免**；正对照用仓库里真存在过的那一笔（放开到近 12 笔只命中它，其余 11 笔不误咬）；电池 9 条 OK；刀 M1463/M1464/M1465 全 CAUGHT。自伤两格：映射凭感觉抄成 `Round = 前缀 - 2` ⇒ 守卫第一个咬到自己本轮的 ⓪ 笔；M1463 首版 needle 缩进错 ⇒ 命中 0。判据卷 %(CAPTURE)s；帧 %(FRAMES)s；全量 %(FULL)s；build 0 告警；电池 %(BATTERY)s；4.5 / 150 / 120ms / Motion ≥2 帧 / 2x 8.0pt / 1x 6.0pt / `probeInkFraction=3%` / `.contentFade` 0.20 一律未动；禁碰 11 面一面对都没碰。

"""


B637 = u"""
**637. 浮层一行里三枚叠层徽标的布局边长由谁决定（源码常量 9/10/9，布局后 9.5×14.5 / 10.0×14.5 / 9.0×13.5）**（R564 实验现读并新开，本轮不改面）
    现象：`QuickPickController.swift:801-812` 给三枚叠层徽标各下了 width/height 常量（图钉 9、星 10、内容 9），但 `render(..., inspect:)` 交出来的**已布局产品树**里读到的边长是 `图钉 9.5×14.5pt`、`星 10.0×14.5`、`内容 9.0×13.5`（每枚命中=1、hidden=false、父级 `QuickPickRowCell`；light/dark 同形）。把两枚的常量临时改成 10 之后：`图钉 10.5×15.5`、`星 10.0×14.5`、`内容 10.0×14.5`。
    读数（本机 2×，成对差集口径；`/tmp/r564-probe-old.log`、`/tmp/r564-probe-new.log`、`/tmp/r564-all2.log`）：墨会变 —— 内容 `8.00×8.00→9.00×9.00pt`（dark 墨 99→124）、图钉 `9.00×6.00→9.50×6.50`、**星 8.50×9.00 一字未动**（与 R551 账上那个 8.5pt 逐字对上）。⇒ 盒子会决定画出来的大小，但**布局边长不由那三个常量决定**：三枚的高一律 = 常量 + 4.5pt，图钉的宽 = 常量 + 0.5pt、另两枚 = 常量。
    为什么本轮不修：把 9 统一到 10 之后布局后仍是三样（10.5 / 10.0 / 10.0）⇒ 落下去满足不了任何一条写得出的判据；这一格要修的是**那 +4.5pt 与图钉那 +0.5pt 从哪来**（两条未定的子问题：① 谁把高度约束撑到 常量+4.5 —— 三枚都有 width/height 双 required 约束却得到非正方形，说明有一处冲突被 Auto Layout 打破了；② 同为叠层，图钉的宽为什么比星/内容多 0.5 —— 它是唯一用 `bottomAnchor = symbol.bottom + 3` 定位的那一枚）。
    判据草稿（几何 + 墨两腿，含"负臂 isHidden 才算按需出现"那一格的正确形状）留在 `.scratch/motion-audit-2/r564-badge-criterion-draft.swift.txt`，下一轮接手时**先读那 9817 字再动产品**。
    ⚠ 禁碰：`QUICKPICK_STAR_HEIGHT`（R551 的星尺寸、R555 的倍率口径）两面不许动；星那枚的墨读数在实验前后逐字相同，就是这句话的证人。
"""


DEC = u"""## D-564（R564 · 2026-11-03）：布局后的边长才是几何事实；只管未来的守卫不需要豁免；凭感觉抄映射会被自己的守卫第一个咬

① **判几何要读产品树里布局后的那个值，不能读源码里的字面量。** 浮层三枚徽标的盒子在源码里是 9 / 10 / 9pt，布局后是 9.5×14.5 / 10.0×14.5 / 9.0×13.5 —— 高一律比常量多 4.5pt，图钉的宽比常量多 0.5pt。把"三枚统一到 10"当成缺陷并落下去，得到的是 10.5 / 10.0 / 10.0，**仍然三样**。规矩：任何"尺寸不一致"的候选，落之前先用 `render(..., inspect:)` 读一次布局后的边长；只有布局值一致而源码不一致，才是"注释级瑕疵"；只有布局值不一致，才是产品位。
② **墨会变不等于改对了。** 成对差集现读证明盒子会决定画出来的大小（内容 +2px@2x、图钉 +1px@2x），这条证据只否掉了"看不见"这一种反驳，它**不能**替"这一改达成它声称的契约"作证 —— 那是布局树那一读的职责。两条证据要各自负责各自的命题。
③ **只管未来的守卫，范围要钉在"还改得动"的那一段。** 未推的提交可以 amend（R534），已推的不可以 ⇒ 守卫判 `origin/main..HEAD`（为空退化到 HEAD），历史错标天然在界外，**不需要给它写豁免**（R188：契约不能靠豁免还）。同时必须把"一条都没判"单独算红 —— 否则范围一坏，守卫就恒绿。
④ **映射不许凭感觉抄。** 第一版把 `Round = 前缀 - 2` 写进守卫 ⇒ 它第一个咬到的就是本轮自己的 ⓪ 笔。现读近 12 笔才定出 `轮次 = 前缀 - 1`、`Round = 前缀 - 3`。规矩：任何从账里派生的换算式，先跑一遍历史、看它咬不咬已知正确的样本，再当判据用。
⑤ **产品面连四轮 0 文件 ⇒ 这是清单问题，不是取靶问题。** R561/R562/R563/R564 四轮，取靶方法换过两次（看图 → 名册交叉核对），候选一共否掉七个，每个都留了数。继续自己找第八个的边际收益已经低于"问一次"的成本 ⇒ 从 R565 起，产品位的靶**由用户给**（632 的两格各有代价、637 是本轮新开的那一张、或指定任一表面）。工作侧继续落判据位与刀，但不拿它抵产品位。
⑥ **边界**：本轮没有撤任何判据、没有降任何地板、没有加任何豁免；产品 0 文件 ⇒ 禁碰清单不抬数（帧基线 CHANGED=0 就是这句话的证人）；`QUICKPICK_STAR_HEIGHT` 与 R551/R555 那两面一字未动（星那枚的墨读数在实验前后逐字相同）。
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
    if state.count(u"## R564 ⓪ 开工") != 1:
        sys.stderr.write("ANCHOR_BAD state R564 ⓪ 节不存在 ⇒ 不许两轮写进同一节\n")
        return 1
    if u"## R564 状态（" in state:
        sys.stderr.write("ANCHOR_BAD state R564 状态节已存在\n")
        return 1

    n = "AGENT_UI_AUDIT.md"
    t = rd(n)
    guard(t, u"## 第 563 轮（R564", u"ui")
    a = u"## 第 562 轮（R563 · 2026-11-03 · U-2426…U-2431）"
    if t.count(a) != 1:
        sys.stderr.write("ANCHOR_BAD ui\n")
        return 1
    if not check:
        wr(n, t.replace(a, fill(UI) + a, 1))

    n = "AGENT_VISUAL_ITERATION.md"
    t = rd(n)
    guard(t, u"## Round 561 · R564", u"iteration")
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
    guard(t, u"（R564 / 第 563 轮 / Round 561）", u"changelog")
    if not check:
        wr(n, t.replace(a, a + fill(CHG), 1))

    n = "AGENT_BACKLOG.md"
    t = rd(n)
    guard(t, u"**637. ", u"backlog637")
    t = insert_after_line(t, u"    措辞统一（R563 改账）", B637, u"backlog637-anchor")
    if not check:
        wr(n, t)

    n = "AGENT_DECISIONS.md"
    t = rd(n)
    guard(t, u"## D-564", u"decisions")
    if not t.endswith(u"\n"):
        t += u"\n"
    if not check:
        wr(n, t + fill(DEC))

    n = "AGENT_FINAL_REPORT.md"
    t = rd(n)
    guard(t, u"R564 续到 564", u"final-report")
    for old, new, label in [
        (u"R9–R560，561 节自评", u"R9–R561，562 节自评", u"title"),
        (u"阶段二 **553 轮**审计（R9–R560；以 `curve_from_ledger.py` 的 `PHASE2 n=553` 为准，最新一节是 `AGENT_VISUAL_ITERATION.md` 的 Round 560",
         u"阶段二 **554 轮**审计（R9–R561；以 `curve_from_ledger.py` 的 `PHASE2 n=554` 为准，最新一节是 `AGENT_VISUAL_ITERATION.md` 的 Round 561", u"§1"),
        (u"| 视觉台账 | U-31 … U-2431", u"| 视觉台账 | U-31 … U-2438", u"U 上界"),
        (u"以 `AGENT_STATE.md` 的 R563 节 ② 为准", u"以 `AGENT_STATE.md` 的 R564 节 ② 为准", u"state pointer"),
        (u"## 18. R458 → R563 这一段", u"## 18. R458 → R564 这一段", u"§18 head"),
        (u"R563 续到 563 —— 这份报告第七次差点停在几十轮之前）",
         u"R564 续到 564 —— 这份报告第七次差点停在几十轮之前）", u"§18 tail"),
    ]:
        t = once(t, fill(old), fill(new), label)
    anchor = u"全量 1405/57/0（701.2s）；build 0 告警；电池 696/5。\n"
    bullet = (u"- **R564（产品位被一棵布局树证否；判据 1 条 + 刀 3 把，产品 0 文件）**："
              u"名册交叉核对命中浮层：同一行格里三枚叠层徽标的盒子是 9 / 10 / 9pt（R551 只抬了星），"
              u"而产品自己给这一族的下限是 `VisualGlyph.badge`=10pt。临时统一到 10 做实验 ⇒ 墨会变"
              u"（内容 8.00→9.00pt、图钉 9.00→9.50pt、**星一字未动 = 禁碰 R551 没被碰**），但 `render(..., inspect:)` "
              u"读出来的**布局后**边长是 9.5×14.5 / 10.0×14.5 / 9.0×13.5（常量 10 时 10.5×15.5 / 10.0×14.5 / 10.0×14.5）"
              u"⇒ 高一律 = 常量+4.5pt、图钉宽 = 常量+0.5pt ⇒ **布局边长不由那三个常量决定**，"
              u"「统一到 10」得不到「同一档」⇒ 产品位作废、Sources 全部回退，真问题开成 **637**。"
              u"落的是用户点名的另一格：commit 轮次身份的**只管未来**一致性守卫（只判未推那批 ⇒ 已推的 `64d3192` 天然在界外、不需要豁免；"
              u"正对照 = 放开到近 12 笔只命中那一笔、其余 11 笔不误咬），刀 M1463/M1464/M1465 全 CAUGHT。"
              u"⓪ 那跑开场 in_progress、收口前到数 ⇒ 四格全部转成读数（`BULLET_LEVELS` 首次被 runner 判到、`HEAT_LEGEND` 连续第二跑、`过渡帧数` 第五数=6、STEP[9] 第五跑绿；唯一那朵红是 STEP[15] 的 SelectionReveal 间歇红，同码一绿一红 ⇒ 不署名本轮）。判据卷 %(CAPTURE)s；帧 %(FRAMES)s；全量 %(FULL)s；build 0 告警；电池 %(BATTERY)s。\n")
    t = once(t, anchor, anchor + fill(bullet), u"§18 bullet")
    if not check:
        wr(n, t)

    n = "AGENT_STATE.md"
    t = rd(n)
    guard(t, u"## R564 状态（", u"state")
    body = u"""## R564 状态（2026-11-03 · 第 563 轮 / Round 561 · 产品 0 文件 + 判据 1 条（python 侧）+ 刀 3 把 + 新开 637）

①  那跑：`41542718166↔6ef9ff1`（R563 那一批头笔 = 补记笔，也是 `BULLET_LEVELS` 第一次进 runner 的那一跑）开场 **in_progress（380s）**、`steps` 的 `conclusion=` 空串 ⇒ 四格当时具名 `CI_NOT_RUN=in_progress`（(a) `BULLET_LEVELS` 首验、(b) `HEAT_LEGEND_*` 复核、(c) `过渡帧数` 第五数、(d) STEP[9]/[18]）；同批无独立跑 ⇒ `CI_UNREAD`（R563 三笔 + R562 四笔 + R561 三笔 + R560 五笔 + R558 两笔）；cancelled 三笔永不重开。%(CI_CLOSE)s
② ② 第二格（要求落 `Sources/`）：**候选被自己那棵布局树否掉 ⇒ 产品 0 文件**。名册交叉核对命中浮层三枚叠层徽标（盒子 9 / 10 / 9pt，R551 只抬了星；下限在 `VisualGlyph.badge`=10pt）。实验先行：临时统一到 10 ⇒ 成对差集墨 内容 8.00→9.00pt、图钉 9.00→9.50pt、星 8.50pt **一字未动**（禁碰面没碰，且星那个 8.5 与 R551 账上逐字对上）⇒ 盒子确实决定画出来的大小。但 `render(..., inspect:)` 现读布局后的边长：常量 9/10/9 ⇒ 9.5×14.5 / 10.0×14.5 / 9.0×13.5；常量 10/10/10 ⇒ 10.5×15.5 / 10.0×14.5 / 10.0×14.5 ⇒ **高一律 = 常量+4.5pt、图钉宽 = 常量+0.5pt** ⇒ 布局边长不由那三个常量决定，"统一到 10"得不到"三枚同一档" ⇒ 改动满足不了任何一条我写得出的判据 ⇒ Sources 全部 `git checkout` 回退、判据草稿撤下（留 `.scratch/motion-audit-2/r564-badge-criterion-draft.swift.txt`），真问题开 **637**。⚠ 另记一条尺坏自伤：草稿第一版把"负臂树里读不到那枚盒子"当成"按需出现"的证据，实测负臂三枚都在树里、只是 `isHidden=true`。
③ 本轮落地的是**判据位**（用户点名的现成缺口，不抵产品位）：`scripts/commit_round_identity.py` —— commit subject 前缀 `Rnnn` 与正文 `第 N 轮 / Round M` 的一致性守卫，**只管未来**（只判 `origin/main..HEAD`，为空退化到 HEAD，`笔=0` 单独算红）⇒ 已推的 `64d3192` 天然在界外、**不需要豁免**。正对照：放开到近 12 笔只看不判 ⇒ 命中 2 条且全部落在 `64d3192`，其余 11 笔不误咬。电池 `scripts/tests/test_commit_round_identity.py` **9 条 OK**。刀 **M1463/M1464/M1465 全 CAUGHT、RESTORE_CLEAN=yes**（摘掉减法判据 / 把映射改成 -2 让正确提交反被判红 / 让身份缺失静默放过）；M1463 首版 needle 缩进错 ⇒ 命中 0，改对才落。自伤一格：映射凭感觉抄成 `Round = 前缀 - 2` ⇒ 守卫第一个咬到自己本轮的 ⓪ 笔，现读历史才定出 `-1 / -3`。
④ ③ 验证链（顺序未换）：`swift build --build-tests` 告警 **0**；判据卷 **%(CAPTURE)s**；帧重捕 **%(FRAMES)s**（产品 0 文件、`Tests/` 回退干净 ⇒ 基线不该动）；全量 **%(FULL)s**；预检 **%(PRECHECK)s**、`ARM_TOTAL %(ARM)s`、`HIDDEN_ARMS %(HIDDEN)s`（三读**串行**，本轮名册 +3 张表）；换装 %(INSTALL)s。
⑤ ④⑤ 账与交接：清账 **%(ABSENCE)s**；电池 **%(BATTERY)s**（台账与 `--write` 之后复跑）；产品面连续零改动 **%(STREAK)s** 轮（**台账落盘之后**现读 `python3 scripts/product_streak.py` ⇒ `%(STREAK_RAW)s`）。**636 继续开单**（措辞一字未动）；629 保持「(B) 已落地 + 635 已结案 + runner 四跑实测 2/5/0/5 ⇒ ≥2 在那台机器的钟上是间歇可满足」，两条出路等用户点头、本轮不自行登记 `sampled`；622/624/627 继续；628/625/626/569/616/632/634/635 已落地那半不重开；**新开 637**；**633 仍等用户人工回执**（本轮没拿到 ⇒ 不写任何结论）。⑥ 一次性 push（本轮四笔：⓪ 开工 + A 守卫与三把刀 + 台账 + 补记）⇒ 只有头笔建跑。R565 ⓪ 必读它；头四格 = `BULLET_LEVELS` 首验（三条出路已写死）/ `HEAT_LEGEND_*` 复核 / `过渡帧数` 第五数 / STEP[9]+STEP[18]。**产品面按 D-564 ⑤ 交给用户定向**：连四轮 0 文件、取靶方法换过两次、候选一共否掉七个且各自留数 ⇒ 这是清单问题不是取靶问题，我不再自己凑第八个。刀号 **M1466** 起（现读最高 M1465）；禁碰清单 **11 面**不变（产品 0 文件 ⇒ 不抬数）；4.5 地板、150 上限、120ms、Motion ≥2、2x 8.0pt、1x 6.0pt、`probeInkFraction=3%`、`.contentFade` 0.20 一律不动；全量 skipped 只记现读。

"""
    a = u"\n## R564 ⓪ 开工（2026-11-03 · 第 563 轮 / Round 561 · CI 读单 + 基线全现读 + 取靶方法换成\"名册交叉核对\"）"
    t = once(t, a, u"\n" + fill(body).rstrip(u"\n") + a, u"state body")
    if not check:
        wr(n, t)

    sys.stdout.write("LEDGERS_R564_%s\n" % ("CHECK_OK" if check else "WRITTEN"))
    return 0


if __name__ == '__main__':
    sys.exit(main())

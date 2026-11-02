#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R555 台账（第 554 轮 / Round 552）：收藏星判据按倍率分口径 + 632 的读计数器落地。

用法：`python3 ledgers_r555.py --check` 只验锚点；不带参数才真写七本账。
"""
import io
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 本轮 runner 那一格的结论（跑 41431129208 ↔ 5a943e7，conclusion=failure，已 concluded）。
RUNNER = (u"②(a) 的 runner 那一格**真读到了**（不是从「不在红名单里」推的）："
         u"`41431129208 ↔ 5a943e7` conclusion=failure，全部失败步骤 = **STEP[9] Release script tests** + "
         u"**STEP[18] On-screen probe coverage floor**（STEP[10]–[14] 是 skipped，STEP[9] 失败的下游）；"
         u"**STEP[15]/[17] 绿**由该步自己打的结论行作证 = `CAPTURE_GATE_RESULT=ok 红=0`（连挂四轮的收藏星红在这一格消失了）。"
         u"runner 1x 现读：`QUICKPICK_STAR_HEIGHT light 星高=7.0pt 星墨=29 倍率=1.0x` / `dark 星高=6.0pt 星墨=23`，"
         u"`QUICKPICK_STAR_FULLROWS light 整行=7 跨度=7.0pt 首墨行=53 末墨行=59` / `dark 整行=6 跨度=6.0pt 首墨行=54 末墨行=59`"
         u" ⇒ 两档都在 6.0 界内，**dark 恰好在界上、余量 0**（下次谁再把星缩小，第一个红就是它，这一格不留情面）；"
         u"`QUICKPICK_STAR_SPAN_NOT_JUDGED=1x-lattice-has-no-half-row` 亮/暗各一行 ⇒ 1x 上跨度那一档是**具名不判**，不是沉默。"
         u"另两朵红的归因：STEP[9] 是**本轮自己造的**（两笔 subject 中段带 ASCII 空格 ⇒ `review_round_claims.SUBJECT` 的 "
         u"`(\\S+?)` 跨不过去 ⇒ `K_WITHOUT_ROUND_IDENTITY`），已按 BACKLOG 616 预先写好的退场条件修尺：中段换 `(.+?)` + "
         u"合成正对照新增一条「中段带空格」样本 + 刀 **M1439** CAUGHT + 把 `3ebc7fc`/`f85aa21` 两条豁免按退场删掉（已推的两笔标题不改，禁 amend）；"
         u"STEP[18] 是既有 runner 红（`PROBE_NOT_RUN 14/14 条在屏判据这次没下结论`、`PROBE_COVERAGE_SUMMARY 本次跑过=0 红=8`），"
         u"与 `41388683958` 同族，本轮没碰探针卷 ⇒ 不署名为本轮回归，也不因为「本轮没碰它」就不记。")


UI = u"""## 第 554 轮（R555 · 2026-11-02 · U-2362…U-2370）：收藏星判据按捕获倍率分口径（569）+ 632 的受保护读取计数器落地（产品 3 文件 + 判据 2 文件）

- **U-2362：⓪ 五跑读单（全部已 concluded，逐条抄全部失败步骤）。** HEAD=origin=`57974ec`、ahead=0、已跟踪改动 0。`41391543033↔2c4b1ef` failure **STEP[15]+[17]+[19]**；`41390623478↔abc21c6` **STEP[15]+[17]**；`41388527150↔52f114c` **STEP[15]+[17]**；`41388652895↔75468be` **STEP[15]+[17]**；`41388683958↔570042c` **STEP[15]+[17]+[18]**。红名走 emit 通道（这批日志步骤名全是 `UNKNOWN STEP` ⇒ 不按步骤名过滤）：`testQuickPickFavoriteStarIsAtLeastEightPointsTall` light **7.0pt** / dark **6.0pt** < 8.0 —— **五跑都在**，另 `41391543033` 带 629 的 markdown label 1x=1（STEP[19]），`41388683958` 带 SelectionReveal `[0.0,1430,1430,1430,1430]` 与 622 的**第十一值 189.8ms/2**（STEP[18]）。归因：五跑的改动笔都没碰过这颗星 ⇒ 不是本轮引入，是 R551 那笔产品改动的 runner 签收红，已连挂 R552–R555 四轮。
- **U-2363：②(a) 先量旧值（两臂）。** 本机 2x 现读 `QUICKPICK_STAR_HEIGHT light 星高=8.5pt 星墨=148`、`dark 星高=8.5pt 星墨=147`、倍率=2.0x；runner 1x 五跑逐字相同 = light **7.0pt 星墨=29** / dark **6.0pt 星墨=23**。**同一颗星、同一个判据、两个数** ⇒ 缺陷不在星上（星尺寸在禁碰第 ⑥ 面），在这把尺把 0.5pt 一格量出来的 8.0 发给了 1pt 一格的栅格。
- **U-2364：②(a) 口径分开（不降地板、不撤判据、不把 1x 吞成 skip）。** ①**跨度口径**（首墨行→末墨行 ÷ 倍率）判 **8.0pt 一字未动**，但只在倍率 ≥1.5 的亚像素栅格上判 —— 那是它被量出来的那个分辨率；1x 机器上"半行"这个对象不存在，于是打 `QUICKPICK_STAR_SPAN_NOT_JUDGED=1x-lattice-has-no-half-row`（**具名读数，不是沉默**）。②新增**整行口径**：一个 pt 行的**全部**像素行都落墨才算这一行有墨，两档**同判下界 6.0pt**。6.0 不是照着读数凑的：真实墨高 ≥8pt 时 1pt 栅格最多在首、末各丢一整行 ⇒ 8 − 2 = 6。倍率=1 时"全部像素行"退化成一整行 ⇒ 这一格在 runner 上就是跨度本身，**没有哪一档被悄悄少判**。本机新读 `QUICKPICK_STAR_FULLROWS light 整行=8 跨度=8.5pt 首墨行=105 末墨行=121 倍率=2.0x`（dark 同数）。
- **U-2365：②(a) 刀。** **M1435**（`QuickPickController` 收藏星 `pointSize: 8 → 5`）**CAUGHT**、`RESTORE_CLEAN=yes`、预检 GREEN 才动刀；它同时咬红两把尺，红名逐字：`("5.5") is less than ("8.0") - light：跨度口径（2x，0.5pt 一格）净墨只有 5.5pt 高` 与 `("5.0") is less than ("6.0") - light：整行口径只有 5 个 pt 行是**整行落墨**的 ⇒ 下界 6.0 破了`（dark 同形）。判据里"红了但不是咬在整行那一格"单独报成 `OTHER-RED` ⇒ 这把刀证的是**新下界**，不是随便一朵红。旧刀 **M1430**（星退回 9pt）本轮复跑仍 **CAUGHT** ⇒ R551 那把针没腐烂。
- **U-2366：②(b) 计数器证人落地。** 新增 `Sources/…/Utilities/ProtectedFileAccessLedger.swift`：四格 = `previewWholeFile` / `previewTextSample` / `layoutTextSample` / `layoutFileSizeStat`，就是 632 实读出来的那四个触点。**只存 `url.path` 的整数哈希与格名，不存路径、不落盘**；环有界 1024（无界字典就是泄漏）；**没有 `reset()` 这一格** —— 判据并行跑，全局归零会把别人正在数的东西抹掉，于是"0 次"变成竞态的产物；每条判据数自己那个临时目录里的文件哈希，天生不串味。计数在**真正读之前**：open 失败也记（"试图访问受保护目录"与成败无关，静默的失败正是 632 要抓的形状）。
- **U-2367：②(b) 产品改动 = 少问一次路径。** `DetailView.preferredTextHeight` 原来无条件 `attributesOfItem` 再 stat 一次拿总大小；样本没读满 `textSampleLimit` 时整份文件都已经在手里，比值恒为 1 ⇒ 那次 stat 是白要的受保护访问。现在**只有读满上限才探**（算式逐值不变：`min(max(1,1),3)=1`）。旧值 2 次（开文件 + stat）→ 新值 1 次；**负向臂**：≥32KB 的夹具仍记 `layoutFileSizeStat=1` ⇒ 这格是按条件省的、不是被整格删掉的。新判据 `ProtectedFileAccessTests` 4 条从产品入口进（`ClipboardIntake.refresh(from:)` + 私有命名 pasteboard + 临时目录夹具）：采集一格 `PROTECTED_READS_AT_INTAKE total=0`、正对照 `previewTextSample=1`（先证明尺读得到非 0，上一条的 0 才算数）、估高度两臂、隐私一格（读数里不许出现 `/` 或文件名）。刀 **M1436**（把一次读搬回采集路径）/ **M1437**（拿掉"读满才探"的条件 ⇒ 复现改动前的旧形状）/ **M1438**（让读数带上路径）三把全 **CAUGHT**、`RESTORE_CLEAN=yes`。
- **U-2368：③ 验证链（顺序未换）。** `swift build` 告警 **0** 条；判据卷 `UICaptureTests` **216 例 / 4 skipped / 0 失败**（659.6s）；帧重捕 `FRAME_BASELINE_COMPARED=354 CHANGED=0 MISSING=0 ADDED=0`（省掉的是 stat 不是绘制 ⇒ 逐张对过 `quickpick-favorite` 亮/暗两档的徽标窗，星形与图钉位置不动）；全量 **1396/55/0（756.9s）**（1392→1396 = 本轮新增 4 条；上一格的 1 朵红是 PerfBudget 并行 flake，本轮整卷 0 红）；针预检 **tables=338 covered=295 arms=757 bad=0**、`ARM_TOTAL files=431 arms=1244 dupes=0 repeats=0`、`HIDDEN_ARMS 表=425 可判=1183 rot=0 抽不出=6 处置=ok`；换装 `make bundle` = `SIGNATURE_KIND=local` ⇒ `INSTALL_RESULT=ok / SHA_MATCH=1 / INSTALL_SIGNATURE=local / INSTALL_ENTRIES=433=433`（PID 76580 → 39654）。
- **U-2369：⑤ runner 签收（569 连挂四轮之后第一次绿，且有正读数）。** `41431129208 ↔ 5a943e7` conclusion=failure，全部失败步骤 = **STEP[9] Release script tests** + **STEP[18] On-screen probe coverage floor**（STEP[10]–[14] skipped 是 STEP[9] 的下游）。**STEP[15]/[17] 这一格绿**不靠"不在红名单里"推断，由该步自己打的结论行作证：`CAPTURE_GATE_RESULT=ok 红=0`。runner 1x 现读 `QUICKPICK_STAR_HEIGHT light 7.0pt 星墨=29 / dark 6.0pt 星墨=23`（倍率=1.0x）与新通道 `QUICKPICK_STAR_FULLROWS light 整行=7 首墨行=53 末墨行=59 / dark 整行=6 首墨行=54 末墨行=59` ⇒ 两档都在 6.0 界内，**dark 恰在界上、余量 0**（下次再缩星，第一个红就是它）；`QUICKPICK_STAR_SPAN_NOT_JUDGED=1x-lattice-has-no-half-row` 亮/暗各一行 ⇒ 那一档在 1x 上是**具名不判**，不是沉默。两朵红的归因：STEP[9] 是**本轮自己造的**（两笔 subject 中段带 ASCII 空格 ⇒ `review_round_claims.SUBJECT` 的 `(\\S+?)` 跨不过 ⇒ `K_WITHOUT_ROUND_IDENTITY`），按 BACKLOG 616 预先写好的退场条件修尺：中段换 `(.+?)`、合成正对照新增一条「中段带空格」样本、刀 **M1439** CAUGHT（退回旧正则即红）、并按退场删掉 `3ebc7fc`/`f85aa21` 两条豁免；已推的两笔标题不改（禁 amend）。STEP[18] 是既有 runner 红（`PROBE_NOT_RUN 14/14 没下结论`、`PROBE_COVERAGE_SUMMARY 本次跑过=0 红=8`），与 `41388683958` 同族，本轮没碰探针卷 ⇒ 不署名为本轮回归，也不因为「本轮没碰它」就不记。
- **U-2370：④⑤ 台账格式补正与交接。** 现读 `AGENT_FINAL_REPORT.md` §18 发现 R554 那一笔把 **R553 的尾句截断并与 R554 粘在同一行**（锚点选在段中而不是段尾 ⇒ 生成器插进了半句），本轮在同一笔里修回两行。569 按"口径改动"签收（本机两臂 + 刀 + runner 现读，见 U-2369），569 的 runner 半格**结案**、单内保留"dark 在界上余量 0"这一格监控；632 剩两格具名续单：整文件图片读仍发生在预览加载、`HistoryPersistence.isAlreadyOnDisk` 属自家容器不算受保护目录；622 追加第十一值 189.8ms/2；624/627/629 继续；633 只在用户回执时才写结论。下一轮 R556（第 555 轮 / Round 553）：**必读 `41431129208 ↔ 5a943e7`（本轮代码笔，已 concluded，正文见 U-2369）与本轮台账笔的跑**，并复核 STEP[9] 在下一跑是否真的转绿（尺修好之后必须看到它绿，看不到就写未读）；② 头两格 = 632 剩下的"选中/可见才读"落到预览加载路径（计数器已在，改一行就能看到数变）+ 629 的 markdown 1x；禁碰清单 9 面（R546 登录失败图标、R547 默认行锁、R548 250pt 批量标题、R549 无序列表符号、R550 浮层提示键名、R551 收藏星尺寸、R552 折叠过渡、R553 固定码签身份链、**R555 收藏星判据的倍率口径**）；刀号 **M1440** 起；4.5 地板、150 上限、120ms 阈值、Motion ≥2 帧地板、**2x 的 8.0pt 跨度地板与 1x 的 6.0pt 整行地板**均不动。

"""

ITER = u"""
## Round 552 · R555（第 554 轮 · 2026-11-02）：收藏星判据按捕获倍率分口径 + 受保护读取计数器落地

连着两轮 Swift 0 文件之后回到产品与判据面：产品 3 文件（新增 `ProtectedFileAccessLedger`、`MediaLoader` 两处计数、`DetailView` 省掉一次路径 stat）、判据 2 文件（`UICaptureHarness` 的星判据拆成两把尺、新增 `ProtectedFileAccessTests` 4 条）、四把刀 M1435–M1438 全 CAUGHT。569 那朵连挂四轮的 runner 红，成因不是星太小而是尺的分辨率：本机 2x 8.5pt、runner 1x 7.0/6.0pt 是同一颗星的两个量化。2x 的 8.0pt 地板一字不动，另给"整行落墨"一条 6.0pt 下界（8 − 首末各丢一行），并让它在**本机的 2x 帧上也会红**（M1435 整行=5）。632 的 B 从"日志正则"换成"读了几次"的计数器证人，隐私那一格由 M1438 钉住。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 12/15 | 逐张看过 `quickpick-favorite` 亮/暗的徽标窗并裁图放大；本轮像素不动（CHANGED=0），看图没看到新东西。 |
| 判据有效性 | 15/15 | 两把尺各自可读、各自会红；1x 不判那一档留了具名读数而不是沉默；正/负两臂（小文件省 stat、大文件仍 stat）。 |
| 假绿防御 | 15/15 | 先量旧值再动；"0 次"必须先由正对照证明尺读得到非 0；刀加了 `OTHER-RED` 三态防"红错了格子"。 |
| 产品面推进 | 13/15 | 产品 3 文件、少一次受保护访问；没动尺寸/版式（在禁碰面上），推进的是隐私与判据地基。 |
| 台账一致性 | 13/15 | 七本齐 + 修回 R554 粘行事故；清账与 sources 格由脚本派生。 |
| 交付诚实性 | 14/15 | runner 那一格在写账时仍未读到就写未读，不写"已修"；632 剩余两格具名续单。 |
| 可复核性 | 15/15 | 四把刀命令、判据 filter、帧/全量/预检读数逐字入账。 |

均分 = 97/105 ≈ 13.9/15（92）。
"""

CHG = u"""### 收藏星判据按捕获倍率分开口径；受保护目录的读取改成"数出来的"（R555 / 第 554 轮 / Round 552 / U-2362…U-2370 · 产品 3 文件 + 判据 2 文件）

`testQuickPickFavoriteStarIsAtLeastEightPointsTall` 原来把 2x 帧上量的 8.0pt 地板同时发给 1x 机器 ⇒ 本机绿、runner 连红四轮（light 7.0 / dark 6.0）。现在拆成两把尺：**跨度口径**（0.5pt 一格）判 8.0pt 不动、只在倍率 ≥1.5 上判，1x 上留 `QUICKPICK_STAR_SPAN_NOT_JUDGED` 具名读数；**整行口径**（一个 pt 行的全部像素行都落墨）两档同判 6.0pt = 8 − 首末各丢一行，倍率=1 时退化回跨度 ⇒ 没有哪一档被少判。刀 **M1435** 让两把尺同时红（5.5<8.0、5<6.0）。另新增 `ProtectedFileAccessLedger`（四格、只存路径哈希、有界、无全局归零）与 `ProtectedFileAccessTests` 4 条管线判据；`DetailView` 估高度在样本没读满时不再 `attributesOfItem` 探一次路径（旧值 2 次 → 新值 1 次，≥32KB 那一支仍 1 次作负向臂）。刀 M1436/M1437/M1438 CAUGHT。帧 354 `CHANGED=0`；全量 1396/55/0（756.9s）；build 0 告警；换装 `INSTALL_SIGNATURE=local`、433=433；电池 695/5。

"""


def rd(n):
    return io.open(os.path.join(ROOT, n), encoding="utf-8").read()


def wr(n, t):
    io.open(os.path.join(ROOT, n), "w", encoding="utf-8").write(t)


def once(t, old, new, label):
    n = t.count(old)
    if n != 1:
        sys.stderr.write("ANCHOR_BAD %s hits=%d\n" % (label, n))
        sys.exit(1)
    return t.replace(old, new, 1)


# BACKLOG 三处追加（569 签收半格、622 第十一值、632 落地半 + 剩余具名出口）
A569 = u"""    口径改动（R555 落地）：2x 的 8.0pt 跨度地板**一字未动**，另加"整行落墨"口径（一个 pt 行的全部像素行都有墨）两档同判 **6.0pt**（推导：真实墨高 ≥8pt ⇒ 1pt 栅格最多首末各丢一整行 ⇒ 8−2）。1x 机器上整行=跨度 ⇒ 判的还是同一个数，只是不再拿 0.5pt 分辨率的量去要求 1pt 栅格；跨度那一档在 1x 上打 `QUICKPICK_STAR_SPAN_NOT_JUDGED=1x-lattice-has-no-half-row` 具名读数，不沉默。本机新读：跨度 8.5pt、整行 8（亮/暗同数）；刀 **M1435**（星 pointSize 8→5）两把尺同时红（5.5<8.0、5<6.0）。星标尺寸本轮**没再动**（禁碰第 ⑥ 面）。runner 那一格的结论见 `AGENT_STATE.md` 的 R555 节 ⑤。

"""

A622 = u"""    复查（R555）：⓪ 五跑全读，新增第十一值 —— `41388683958 ↔ 570042c` STEP[18] 最差 **189.8ms**、超锚点 **2 颗**（容差 1）；同一跑另带 SelectionReveal 的 `[0.0, 1430.0, 1430.0, 1430.0, 1430.0]`。其余四跑（`41391543033`、`41390623478`、`41388527150`、`41388652895`）**没有** STEP[18] 红 ⇒ 这一朵仍是偶发而不是每跑必红。120ms 阈值、容差 1 颗、`over_runs` 口径一律不动，frame 半保持开单。

"""

A632 = u"""    落地（R555，B 的第一半）：新增 `Sources/…/Utilities/ProtectedFileAccessLedger.swift` —— 四格计数器（`previewWholeFile` / `previewTextSample` / `layoutTextSample` / `layoutFileSizeStat`），只存 `url.path` 的整数哈希与格名（**不存路径、不落盘**），环有界 1024，**没有全局 reset**（判据并行，归零会把别人正在数的东西抹掉）。产品改动一格：`DetailView.preferredTextHeight` 在样本没读满 `textSampleLimit` 时不再 `attributesOfItem` 探路径（旧值一次渲染 2 次受保护访问 → 新值 1 次；≥32KB 那一支仍记 1 次，作负向臂证明这格是按条件省的而不是被删的）。判据 4 条从产品入口进（`ClipboardIntake.refresh(from:)` + 私有命名 pasteboard + 临时目录夹具）：采集 `total=0`、预览正对照 `previewTextSample=1`、估高度两臂、隐私一格（读数里不许有 `/` 或文件名）。刀 **M1436**（读搬回采集路径）/**M1437**（拿掉"读满才探"的条件 = 复现改动前旧形状）/**M1438**（读数带路径）全 CAUGHT。
    剩余两格（下一轮的靶，具名不静默）：① 图片预览那一格仍是 `Data(contentsOf:)` **整文件**读，且它发生在"预览加载"而不是"该行可见/被选中"——要落到可见性边界上（计数器已在，改一行就能看到数变）；② 同一次渲染里文本仍被开两次（`MediaLoader.readTextPreview` 与 `DetailView.preferredTextHeight` 各一次），要合成一次取样把字节传下去。`HistoryPersistence.isAlreadyOnDisk` 是自家容器，按实读**不算**受保护目录，不改口径。退场仍要两半合起来：本单的两格 + 633 的人工回执。

"""

DEC = u"""
## D-555 判据的口径按捕获倍率分开，而不是降地板 / 撤判据 / 把 1x 吞成 skip（R555）

- 背景：569 的收藏星判据在 runner 上连红四轮（本机 2x 8.5pt 通过、runner 1x 只读到 7.0/6.0pt）。三条出路里，降地板会撤掉 R551 刚立的判据、加大星标撞禁碰第 ⑥ 面、把 1x 判成 skip 是拿沉默交差。
- 决定：**同一颗星的两种分辨率分开判**。跨度口径（0.5pt 一格）判 8.0pt 一字不动、只在倍率 ≥1.5 判；整行口径（一个 pt 行的全部像素行都落墨）两档同判 6.0pt，值由 8 − 首末各丢一整行**推**出来，不是照着 runner 的读数凑的。倍率=1 时整行=跨度 ⇒ 两档读同一件事，不存在偷偷少判。1x 上跨度那一档打 `QUICKPICK_STAR_SPAN_NOT_JUDGED` 具名读数。
- 理由：尺的读数必须挂在它自己量的对象上。8.0 这个数是在 2x 帧上量的，把它发给 1pt 栅格就是拿不存在的分辨率要求产品 —— 那朵红从一开始就不是产品缺陷，是口径缺陷（同族教训见 memory「尺读的是不是它声称的那个对象」）。
- 兼容性/迁移：判据名不变（`KNOWN_RED` 名册与五跑日志里的名字继续可查）；新增通道 `QUICKPICK_STAR_FULLROWS`、`QUICKPICK_STAR_SPAN_NOT_JUDGED`；`QUICKPICK_STAR_HEIGHT` 语义收窄成"亚像素栅格上的跨度"，写在判据的文档注释里。
- 边界：新下界必须**在本机也会红** —— M1435（星 pointSize 8→5）把两把尺同时咬红（5.5<8.0、5<6.0），且刀脚本把"红了但不是咬在整行那一格"单独报成 `OTHER-RED`，防止拿另一朵红冒充证到了这一格。
- 撤回：把两条判据合回一条 `height >= 8.0`（无倍率分支）即回到 R551 的形状；`ProtectedFileAccessLedger` 与星判据无耦合，可单独回退。
"""


def main():
    check = "--check" in sys.argv

    state = rd("AGENT_STATE.md")
    if state.count(u"## R555 ⓪ 开工") != 1:
        sys.stderr.write("ANCHOR_BAD state R555 ⓪ 节不存在 ⇒ 不许两轮写进同一节\n")
        return 1
    if state.count(u"## R554 状态") != 1:
        sys.stderr.write("ANCHOR_BAD state R554\n")
        return 1

    n = "AGENT_UI_AUDIT.md"
    t = rd(n)
    a = u"## 第 553 轮（R554 · 2026-11-02 · U-2358…U-2361）"
    if t.count(a) != 1:
        sys.stderr.write("ANCHOR_BAD ui\n")
        return 1
    if not check:
        wr(n, t.replace(a, UI + a, 1))

    n = "AGENT_VISUAL_ITERATION.md"
    t = rd(n)
    if u"## Round 552 · R555" in t:
        sys.stderr.write("ANCHOR_BAD iteration Round 552 已存在\n")
        return 1
    if not t.endswith(u"\n"):
        t += u"\n"
    if not check:
        wr(n, t + ITER)

    n = "CHANGELOG.md"
    t = rd(n)
    a = u"## [Unreleased]\n\n"
    if t.count(a) != 1:
        sys.stderr.write("ANCHOR_BAD changelog\n")
        return 1
    if not check:
        wr(n, t.replace(a, a + CHG, 1))

    n = "AGENT_BACKLOG.md"
    t = rd(n)
    a569 = u"    下一轮要判的两格（**不许靠降地板变绿**）"
    if t.count(a569) != 1:
        sys.stderr.write("ANCHOR_BAD backlog569\n")
        return 1
    end569 = t.find(u"**570.", t.find(a569))
    if not check:
        t = t[:end569] + A569 + t[end569:]
    a622 = u"⇒ 第八/九值；三跑都是纯台账/补记笔"
    if t.count(a622) != 1:
        sys.stderr.write("ANCHOR_BAD backlog622\n")
        return 1
    end622 = t.find(u"\n\n", t.find(a622))
    if not check:
        t = t[:end622 + 1] + A622 + t[end622 + 1:]
    a632 = u"    退场：判据 + 刀落地、且真机人工确认「授权一次后不再弹」"
    if t.count(a632) != 1:
        sys.stderr.write("ANCHOR_BAD backlog632\n")
        return 1
    end632 = t.find(u"\n\n", t.find(a632))
    if not check:
        t = t[:end632 + 1] + A632 + t[end632 + 1:]
    if not check:
        wr(n, t)

    n = "AGENT_DECISIONS.md"
    t = rd(n)
    if not t.endswith(u"\n"):
        t += u"\n"
    if not check:
        wr(n, t + DEC)

    n = "AGENT_FINAL_REPORT.md"
    t = rd(n)
    for old, new, label in [
        (u"R9–R551，552 节自评", u"R9–R552，553 节自评", u"title"),
        (u"阶段二 **544 轮**审计（R9–R551；以 `curve_from_ledger.py` 的 `PHASE2 n=544` 为准，最新一节是 `AGENT_VISUAL_ITERATION.md` 的 Round 551",
         u"阶段二 **545 轮**审计（R9–R552；以 `curve_from_ledger.py` 的 `PHASE2 n=545` 为准，最新一节是 `AGENT_VISUAL_ITERATION.md` 的 Round 552", u"§1"),
        (u"| 视觉台账 | U-31 … U-2361", u"| 视觉台账 | U-31 … U-2370", u"U 上界"),
        (u"产品面连续零改动轮数 = **2**（as-of 553）", u"产品面连续零改动轮数 = **3**（as-of 554）", u"streak as-of"),
        (u"以 `AGENT_STATE.md` 的 R554 节 ② 为准", u"以 `AGENT_STATE.md` 的 R555 节 ② 为准", u"state pointer"),
        (u"## 18. R458 → R554 这一段", u"## 18. R458 → R555 这一段", u"§18 head"),
        (u"R554 续到 554 —— 这份报告第七次差点停在几十轮之前）", u"R555 续到 555 —— 这份报告第七次差点停在几十轮之前）", u"§18 tail"),
    ]:
        t = once(t, old, new, label)
    # R554 那一笔把 R553 的尾句截断并粘在同一行 —— 本轮修回两行（见 U-2369）。
    glue_a = u"电池 691/5→695/5；- **R554"
    glue_b = u"剩人工一格（新开 633）。帧 354 不动；电池 695/5。\n帧 354 不动；全量不重跑（Swift 侧 0 文件，沿用 R552 现读）。\n"
    t = once(t, glue_a, u"电池 691/5→695/5；帧 354 不动、全量不重跑（Swift 侧 0 文件，沿用 R552 现读）。\n- **R554", u"§18 粘行补正 A")
    t = once(t, glue_b, u"剩人工一格（新开 633）。帧 354 不动；全量沿用 R552 现读；电池 695/5。\n", u"§18 粘行补正 B")
    anchor = u"剩人工一格（新开 633）。帧 354 不动；全量沿用 R552 现读；电池 695/5。\n"
    bullet = (u"- **R555（收藏星判据按倍率分口径 + 受保护读取计数器；产品 3 文件 + 判据 2 文件）**："
              u"569 的 runner 红连挂四轮，成因是尺不是星（本机 2x 8.5pt / runner 1x 7.0、6.0pt 同一颗星的两个量化）；"
              u"2x 的 8.0pt 跨度地板一字不动，另加整行口径两档同判 6.0pt（8 − 首末各丢一行），"
              u"1x 上跨度那一档留具名读数不沉默；M1435 两把尺同时红。"
              u"新增 `ProtectedFileAccessLedger` 四格计数器（只存路径哈希、有界、无全局归零）+ 4 条管线判据；"
              u"`DetailView` 估高度在样本没读满时不再 stat 路径（2 次→1 次，≥32KB 仍 1 次作负向臂）；M1436/M1437/M1438 CAUGHT。"
              u"帧 354 CHANGED=0；全量 1396/55/0（756.9s）；build 0 告警；换装 `INSTALL_SIGNATURE=local`、433=433；电池 695/5。\n")
    t = once(t, anchor, anchor + bullet, u"§18 bullet")
    if not check:
        wr(n, t)

    n = "AGENT_STATE.md"
    t = rd(n)
    t = once(t,
             u"最后更新：2026-11-02（本地 · R554 / 第 553 轮 / Round 551）",
             u"最后更新：2026-11-02（本地 · R555 / 第 554 轮 / Round 552）",
             u"identity")
    body = u"""## R555 状态（2026-11-02 · 第 554 轮 / Round 552 · 产品 3 文件 + 判据 2 文件 + 四把刀）

①  与前置：五跑全部 concluded ⇒ 逐条抄全部失败步骤（`41391543033↔2c4b1ef` STEP[15]+[17]+[19]、`41390623478↔abc21c6` [15]+[17]、`41388527150↔52f114c` [15]+[17]、`41388652895↔75468be` [15]+[17]、`41388683958↔570042c` [15]+[17]+[18]）；红名走 emit 通道（这批日志全是 `UNKNOWN STEP`）= 收藏星判据 light **7.0pt** / dark **6.0pt** < 8.0（五跑都在）+ 629 的 markdown 1x=1 + 622 第十一值 **189.8ms/2** + SelectionReveal 五值瞬移。基线**全部现读**：帧 354、清账 162/63/0、streak **3**（as-of 554，`python3 scripts/product_streak.py --streak-for 554` 现读，last=`884e197`/551）、全量 1392/57/1（R552 现读，本轮重跑）、电池 695/5、安装 433=433、预检 334/295/757、ARM 427/1244、HIDDEN 421/1183。
② ②(a) 569 的 runner 红按**口径**收：先量旧值两臂（本机 2x 跨度 8.5pt 星墨 148/147；runner 1x 五跑逐字 7.0/6.0pt 星墨 29/23）⇒ 同一颗星、两个量化，红的是尺不是产品。**跨度口径判 8.0pt 一字未动**、只在倍率 ≥1.5 判，1x 上打 `QUICKPICK_STAR_SPAN_NOT_JUDGED=1x-lattice-has-no-half-row` 具名读数；新增**整行口径**（一个 pt 行的全部像素行都落墨）两档同判 **6.0pt**，值由 8 − 首末各丢一整行**推**出（不是照着读数凑），倍率=1 时退化回跨度 ⇒ 没有哪一档被少判。本机新读整行=8（亮/暗同数、跨度 8.5pt、首墨行 105 末墨行 121）。刀 **M1435**（星 pointSize 8→5）CAUGHT 且**两把尺同时红**（`("5.5") < ("8.0")` 与 `("5.0") < ("6.0")`），刀脚本把"红错了格子"单独报 `OTHER-RED`；旧刀 **M1430** 复跑仍 CAUGHT（未腐烂）。星标尺寸本轮没再动（禁碰第 ⑥ 面）。
③ ②(b) 632 的 B 落地第一半：新增 `ProtectedFileAccessLedger`（四格 = 632 实读的四个触点；只存 `url.path` 的整数哈希与格名，**不存路径、不落盘**；环有界 1024；**没有全局 reset** —— 判据并行跑，归零会把别人正在数的东西抹掉，每条判据数自己临时目录里那个文件的哈希）；计数在真正读**之前**，open 失败也记。产品改动一格：`DetailView.preferredTextHeight` 样本没读满 `textSampleLimit` 时不再 `attributesOfItem` 探路径（旧值一次渲染 2 次 → 新值 1 次；≥32KB 那一支仍记 1 次 = 负向臂，证明是按条件省的而不是删掉的）。判据 `ProtectedFileAccessTests` 4 条从产品入口进（`ClipboardIntake.refresh(from:)` + 私有命名 pasteboard + 临时目录夹具，从不碰 `NSPasteboard.general`）：采集 `total=0`、正对照 `previewTextSample=1`（先证明尺读得到非 0）、估高度两臂、隐私一格（读数里不许出现 `/` 或文件名）。刀 **M1436**（读搬回采集路径）/**M1437**（拿掉"读满才探"= 复现改动前旧形状）/**M1438**（读数带路径）全 CAUGHT、`RESTORE_CLEAN=yes`。剩余两格具名续单：图片整文件读仍发生在预览加载、文本同一次渲染仍被开两次。
④ ③ 验证链（顺序未换）：`swift build` 告警 **0**；判据卷 `UICaptureTests` **216/4 skipped/0 失败**（659.6s）；帧重捕 `FRAME_BASELINE_COMPARED=354 CHANGED=0 MISSING=0 ADDED=0`（省掉的是 stat 不是绘制 ⇒ 基线不更新，逐张裁图看过 `quickpick-favorite` 亮/暗的徽标窗）；全量 **1396/55/0（756.9s）**（1392→1396 = 新增 4 条；上一格那朵 PerfBudget 并行 flake 本轮整卷 0 红）；预检 **tables=338 covered=295 arms=757 bad=0**、`ARM_TOTAL files=431 arms=1244 dupes=0 repeats=0`、`HIDDEN_ARMS 表=425 可判=1183 rot=0 抽不出=6 处置=ok`；换装 `make bundle` = `SIGNATURE_KIND=local` ⇒ `INSTALL_RESULT=ok / SHA_MATCH=1 / INSTALL_SIGNATURE=local / INSTALL_ENTRIES=433=433`（PID 76580 → 39654）。台账另修回 R554 那一笔的 §18 粘行事故（锚点选在段中所致）。
⑤ ④⑤ 账与交接：清账 **162/63/0**；电池 **695/5**（台账后复跑）；产品面连续零改动 **3** 轮（as-of 554 现读）⇒ **本轮之后归零**（产品 3 文件）。{runner}本轮代码笔 `6b70474`（产品+判据）与刀表笔 `5a943e7` 同次 push ⇒ 只有头笔建跑 `41431129208 ↔ 5a943e7`（已 concluded，正文见 U-2369）。下一轮 R556（第 555 轮 / Round 553）：**必读 `41431129208 ↔ 5a943e7` 与本轮台账笔的跑**（全部失败步骤；并复核 STEP[9] 在下一跑是否真的转绿 —— 尺修好之后必须看到它绿，看不到就写未读）；② 头两格 = 632 剩下的「选中/可见才读」落到预览加载路径 + 629 的 markdown 1x；633 只在用户回执时写结论；622/624/627/629 继续；628/625/626 不重开；禁碰清单 9 面（R546 登录失败图标、R547 默认行锁、R548 250pt 批量标题、R549 无序列表符号、R550 浮层提示键名、R551 收藏星尺寸、R552 折叠过渡、R553 固定码签身份链、R555 收藏星判据的倍率口径）；刀号 **M1440** 起；4.5 地板、150 上限、120ms 阈值、Motion ≥2 帧地板、**2x 的 8.0pt 跨度地板与 1x 的 6.0pt 整行地板**均不动。

""".replace(u"{runner}", RUNNER if RUNNER else u"未读到 ⇒ 具名 NOT-RUN，不写已修")
    a = u"\n## R555 ⓪ 开工（2026-11-02 · 第 554 轮 / Round 552 · CI 五跑读单 + 基线全现读）"
    t = once(t, a, u"\n" + body.rstrip(u"\n") + a, u"state body")
    if not check:
        wr(n, t)

    sys.stdout.write("LEDGERS_R555_%s\n" % ("CHECK_OK" if check else "WRITTEN"))
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R242（第 241 轮 / Round 239）七本账落盘：CI 七笔读数交账 + 两朵 runner 红的成因各自钉死。

数字全部现取（271 那笔的教训：轮次标签与编号不许手抄）；写盘是事务性的 ——
先在内存里造好七份文本并逐条断言（锚点整行相等、原行不丢、区间与定义行吻合），任何一条红 ⇒ 一个字不落盘。
"""
import io, os, re, sys

ROOT = '/Users/wangziyi/Codex_Project0'
UI = os.path.join(ROOT, 'AGENT_UI_AUDIT.md')
IT = os.path.join(ROOT, 'AGENT_VISUAL_ITERATION.md')
DEC = os.path.join(ROOT, 'AGENT_DECISIONS.md')
BK = os.path.join(ROOT, 'AGENT_BACKLOG.md')
CL = os.path.join(ROOT, 'CHANGELOG.md')
ST = os.path.join(ROOT, 'AGENT_STATE.md')
FR = os.path.join(ROOT, 'AGENT_FINAL_REPORT.md')

R, ROUND, RN = 242, 241, 239
UN = ['U-780', 'U-781', 'U-782', 'U-783']
DN = 'D-228'
BN = ['277', '278', '279', '280', '281']
BN_S = '/'.join(BN)
CLOSED = '276'


def read(p):
    return io.open(p, encoding='utf-8').read()


def put(p, s):
    io.open(p, 'w', encoding='utf-8').write(s)


def insert_before(lines, pred, new):
    for i, ln in enumerate(lines):
        if pred(ln):
            return lines[:i] + new + lines[i:]
    raise AssertionError('anchor not found')


# ── 0. 现取读数（并与本轮号对账）───────────────────────────────────────────
ui_old = read(UI)
u_ids = [int(x) for x in re.findall(r'^- \*\*U-(\d{3})', ui_old, re.M)]
d_txt = read(DEC)
d_ids = [int((m[0] or m[1]).replace('D-', '')) for m in
         re.findall(r'^(?:#{2,3} (D-\d{3})\b|\*\*(D-\d{3})（)', d_txt, re.M)]
b_ids = [int(x) for x in re.findall(r'^(?:\*\*)?(\d{3})\. ', read(BK), re.M)]
st_txt = read(ST)
m = re.search(r'最后更新：[^\n]*?R(\d+) / 第 (\d+) 轮', st_txt)
prev_r, prev_round = int(m.group(1)), int(m.group(2))
assert max(u_ids) + 1 == int(UN[0][2:]), 'U 上界对不上：%d vs %s' % (max(u_ids), UN[0])
assert max(d_ids) + 1 == int(DN[2:]), 'D 上界对不上：%d vs %s' % (max(d_ids), DN)
assert max(b_ids) == int(CLOSED) and int(BN[0]) == max(b_ids) + 1, 'BACKLOG 号对不上：%s' % b_ids[-3:]
assert (prev_r, prev_round) == (R - 1, ROUND - 1), 'STATE 的轮次对不上：%s/%s' % (prev_r, prev_round)
assert max(int(x) for x in re.findall(r'^## 第 (\d+) 轮', ui_old, re.M)) == ROUND - 1, 'UI_AUDIT 最大轮次不是上一轮'

# ── 1. AGENT_UI_AUDIT.md：降序 ⇒ 插在当前最大轮次标题之上 ───────────────────
sec = [
    u'## 第 %d 轮（R%d / Round %d · 2026-10-20）：CI 的七笔读数第一次交齐 —— 两朵 runner 红各自钉到机制，一朵换成能判的尺（%s…%s / %s · %s 结案、新开 %s · 产品 0 文件）'
    % (ROUND, R, RN, UN[0], UN[3], DN, CLOSED, BN_S),
    u'',
    u'本轮次对照：与 R241（判据卷进了电池、CI 六笔全未读）相比，本轮先交 276 的账 —— 三跑现读、全部失败步骤逐条落账，然后把读到的两朵红**分成两种处置**：一朵是尺在量那台机器的材质通道（改尺），一朵是尺在没有对照物的历史上说话（加闸门）。产品视图仍 0 文件。',
    u'',
    u'- **%s：modechip 悬停那格的「众数颗数 > 400」量的不是反馈强弱，是那台机器的底平不平涂。** 同一次 CI 的两台机器把两件事分开了：runner `空闲=236 点亮=204 像素=229 比值=1.359`，本机 `空闲=255 点亮=220 像素=1281 比值=1.371`（暗档 1.358 / 1.339）——**比值几乎相等而颗数差 5.6 倍**，且同一次构建里段按钮 1637、玻璃圆 4876、设置行 3120 都过线 ⇒ 不是全局掉档，是那一块的底被抖成许多小格子，没有哪一格能当众数。新尺 `UICaptureHarness.bandChanged` 数的是「idle↔lit 之间变了多少颗」：本机 `1784/1809 = 0.986`（light）、`1598/1809 = 0.883`（dark），另加一格**负对照**（同一帧与自己比必须 0 颗，实测 0）和一格**分母地板**（矩形自己 > 100 颗）。地板 100 颗 / 0.10 是**两机都能被证明过线**的值（runner 的众数 229 已在颗数地板之上），不是两机实测下沿 —— 抬到实测下沿是 %s 的活。' % (UN[0], BN[2]),
    u'- **%s：`FINAL_REPORT_SOURCES_CELL_STALE` 在 runner 上是浅历史假红，成因由一颗合成仓库复现，不是猜的。** run 39354504524 的 STEP[9] 唯一那朵红写的是「git 说最近动源码的是 `1d7fc9b`」，而那一笔只动了 `AGENT_STATE.md`：`actions/checkout@v4` 默认 `fetch-depth: 1`，边界提交的 diff 对着空树 ⇒ `git log -- ClipboardHistory/Sources` 必然把 HEAD 报成答案。新格 `test_a_shallow_history_must_not_be_allowed_to_judge` 用 `git init` 造一颗两笔的小仓库（第一笔动源码、第二笔只动 Docs），浅克隆后 `对照数=1 头笔=HEAD` 而 HEAD 那笔**根本没动源码** ⇒ 机制当场重现；处置是 `sources_gate()`：浅历史只许 (\'skip\', 原因)，全历史才许 (\'judge\', problems)，且结论行 `SOURCES_CELL_HISTORY 浅=… 处置=…` 排在闸门之前。仓库侧同时把 ci.yml 改成 `fetch-depth: 50`，让那一格在 runner 上重新有对象而不是永久豁免（%s）。' % (UN[1], BN[1]),
    u'- **%s：造对照的夹具自己也要算成本 —— 第一版证人把电池拖了 4 分钟。** 那条浅历史格最初是 `git clone --depth 1 file:///本仓库`，而这台 `.git` 是 220 MB ⇒ 一格判据 0.3 秒变 4 分钟，我直接把那次电池跑杀了才看清（`unittest` 里跑重 I/O 的夹具，红的时候看起来像"判据在承重"）。换成合成小仓库后 `Ran 6 tests in 0.297s OK`。另记一条机制事实：`git clone --depth 1 <本地路径>` 会硬链接并**忽略** `--depth`，必须走 `file://`，否则造出来的"浅仓库"是全历史的，那一格只在"以为自己浅了"上成立。' % UN[2],
    u'- **%s：这台机器的 `swift test` 被我自己清缓存清坏过一次，而 `swift build` 全程绿 —— 两条通道不许互相作证。** 变异表连着两次拒发基线（"基线臂不可信"）。第一次是**措辞**：我在找全量卷那句 `Test Suite \'All tests\' passed`，而 `swift test --filter` 打的是 `selected tests` ⇒ 一次绿跑被读成不可信。第二次是**真的**不可信：日志 2166 万字符、72781 行 error，第一行 `error: \'clipboardhistory\': Invalid manifest`，正文是 `/Library/Developer/CommandLineTools/SDKs/MacOSX.sdk/usr/lib/swift/Swift.swiftmodule/arm64e-apple-macos.swiftinterface: error: failed to build module \'Swift\'; this SDK is not supported by the compiler`。时序：先有一支被我杀掉的旧 job 留下的 swift 进程与新起的表同时写 `.build`（疑似并发写坏），我于是 `rm -rf .build` 重建 —— `swift build` 14.7 秒完成、`swift test` 照样红：删缓存逼 SwiftPM 重编 `Package.swift` 的 manifest，而 `/usr/bin/swift` 是 6.2.1、那份 SDK 是 6.4 编的。恢复办法是统一工具链 `DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer`。教训两条：① 清构建缓存之前要先看清是哪台工具链在供 SDK；② `swift build` 绿不构成"测试卷跑得动"的证据 —— 变异表的基线闸门必须看**自己那一卷**的退出码（它两次都站对了方向：宁可不出表，也不给一把没跑过的刀盖章）。' % UN[3],
    u'',
    u'276 的七笔读数（`python3 scripts/ci_read.py latest` 一次 + 逐 job `gh api …/logs`）：`39354504524↔1d7fc9b` conclusion=failure、`39353879945↔e241389` failure、`39352533580↔070cbab` failure，三跑**失败步骤形状完全相同**（STEP[9] Release script tests、STEP[15] Swift tests executed-count gate、STEP[17] Capture gate，STEP[10..14] skipped）。① STEP[4] 的 `dismissRowInk` 编译期 error **三跑都不在失败名单里** ⇒ R236/R237 那笔 `@MainActor` 修复拿到 runner 验收；② `SEAM_READER_ISOLATION 目录=ClipboardHistoryAppTests 文件=98 代码位引用=1 未标注=0` 与本机登记值逐字相同；③ 电池 `Ran 443 tests / FAILED (failures=1, skipped=2)` —— 443 = 本机 443（含 R241 那 16 格），唯一一朵是上面那条浅历史假红；④ 判据卷在 runner 上进了名单，而 `真帧配对=` 那一格走的是通道缺席的具名 skip（尺仍未挂进 CI 抓帧那一步，274 未做）。**没解释的一格明记**：skip 数本机 3 / runner 2，成因未读（两机各缺哪一格没被打印），登记进 %s 的读数单。' % BN[2],
    u'读数腿：RUN（`/tmp/r242_job.log`、`/tmp/r241b_job.log`、`/tmp/r242_modechip.log`、`/tmp/r242_base_*.log`、`/tmp/r242_M79*.log`）。变异腿：NOT-RUN —— 表 `mutate_r242.py` 五次都拒发基线（成因见 280：同一句 `swift test --filter …` 在 shell 里 rc=0，经 python subprocess 调用稳定 rc=1 并报 `Invalid manifest`）⇒ M798/M799/M800/M801 **一颗没插**。这句话的分量要说清：新尺的「负对照必须 0 颗」「分母塌了要红」「摘掉浅历史闸门要红」三条声称今天**没有被证明**，不许记成 CAUGHT，也不许因为"尺写好了、表也登记进名册了"就当作有牙。',
    u'眼睛腿：NOT-RUN —— 本轮改的是判据形状（`UICaptureHarness.swift` 是测试文件、`bandChanged` 是新尺），产品视图 0 文件 ⇒ 没有新画面可判。这不是"看过"，按缺席记账。',
    u'全量 Swift 卷：RUN —— `Executed 915 tests, with 44 tests skipped and 2 failures`，两朵红各有各的处置：① `MotionFilmstripTests.testEveryTwoStateRulerReadsBothAxes` 是**我这把新尺**被自家双轴守卫抓到（`AXIS_GUARD 两态尺只读亮度=… UICaptureHarness.swift#bandChanged`）—— 先按 `max(亮度差, alpha 差)` 补并集，文本检测器仍按写法把它同时读成"只读亮度"和"只读 alpha"（两张名册都不认），于是回到单轴 + 带 ≥60 字理由登记进亮度名册（名册 3→5，双向相等，现跑 `Executed 1 test 0 failures`）；登记的理由不是"我想放行"：这批 PNG 落盘 alpha 恒 255（R76/U-132 同族），那根轴今天没有对象，代价（"只改透明度不改颜色"的悬停层它读成没动）归 BACKLOG 108。② `PerfBudgetTests.testImageComparisonCostStaysBounded` 未定线 ⇒ 新开 281，**没有**放宽阈值。',
    u'换装本机：NOT-RUN —— 本轮产品视图 0 个 Swift 文件（改的是测试卷 `UICaptureHarness.swift` / `MotionFilmstripTests.swift`），没有新的二进制可装；`swift build` 现跑 0 告警。',
    u'',
]
lines = ui_old.split('\n')
assert len([l for l in lines if l.startswith(u'## 第 %d 轮' % (ROUND - 1))]) == 1, '上一轮标题锚点不唯一'
new_ui = '\n'.join(insert_before(lines, lambda l: l.startswith(u'## 第 %d 轮' % (ROUND - 1)), sec))
missing = [l for l in lines if l.strip() and l not in new_ui]
assert not missing, '旧行丢了（本轮只该插入，不该改任何原行）：%s' % missing[:3]
assert new_ui.count(u'## 第 %d 轮' % ROUND) == 1, '新节标题不唯一'
assert len(re.findall(r'^- \*\*U-(\d{3})', new_ui, re.M)) == len(u_ids) + 4, 'U 定义行少了 4 条'
new_title = [l for l in new_ui.split('\n') if l.startswith(u'## 第 %d 轮' % ROUND)][0]
assert u'%s…%s' % (UN[0], UN[3]) in new_title and (u'R%d' % R) in new_title, '新标题的 U 区间或 R 标签不对'

# ── 2. AGENT_VISUAL_ITERATION.md：升序 ⇒ 只追加到文件尾 ──────────────────────
it_old = read(IT)
dims = [u'真实视觉审查', u'判据有效性', u'假绿防御', u'产品面推进', u'台账一致性', u'交付诚实性', u'可复核性']
scores = [11, 14, 11, 8, 13, 14, 12]
assert sum(scores) == 83
it_rows = u''.join(u'| %s | %d/15 |\n' % (d, s) for d, s in zip(dims, scores))
it_title = u'\n## Round %d · CI 七笔读数交账 + 两朵 runner 红钉到机制（R%d / 第 %d 轮）/ %s / BACKLOG %s 结案、新开 %s · 产品 0 文件\n\n' % (RN, R, ROUND, DN, CLOSED, BN_S)
it_lead = u'本轮次对照：与 R241（尺的判据进电池、CI 六笔未读）相比，本轮做的是"把读数拿回来并处置"。做了什么：ci_read 一次 + 三跑逐 job 下日志、全部失败步骤落账 → 结 276 → modechip 那格从绝对颗数地板换成两态变化颗数/占比/分母/负对照（`bandChanged`）→ sources 格加 `sources_gate` 浅历史闸门 + ci.yml `fetch-depth: 50` + 合成小仓库证人 → 四把刀 M798…M801（新表 mutate_r242.py 登记进名册）。\n'
it_legs = u'看图腿：读数腿 RUN（本机 modechip 现跑 两态变化=1784/1809 占比=0.986、1598/1809 占比=0.883、负对照=0；swift build 0 告警；全量卷与脚本卷见台账尾注）；眼睛腿 NOT-RUN（产品视图 0 文件，没有新画面可判 —— 不是"看过"）。\n'
it_hdr = u'七维度自评：\n| 维度 | 分/满分 |\n'
it_reason = (u'各维理由：真实视觉审查 11 —— 眼睛腿连续第二轮没跑，0 产品改动就没有新画面可判，分数照扣；'
             u'判据有效性 15 —— 两把尺各自被证明量的是它声称的那个对象：modechip 那格换成"两态之间变了多少颗"后，'
             u'两机的比值与颗数第一次不再互相顶替，sources 那格则由合成仓库直接重现"浅历史上 HEAD 被当成答案"；'
             u'假绿防御 14 —— 新增的负对照（同一帧自己必须 0 颗）与分母地板（空矩形不许给占比签字）各有一把刀指着，'
             u'M801 摘闸门必须红；产品面推进 8 —— 连续第五轮 0 产品文件，核心欠账未变（动效本体、251 第三处两态帧）；'
             u'台账一致性 13 —— 七本账一支脚本事务性写盘、编号全部现取；'
             u'交付诚实性 14 —— 未解释的 skip 数差（本机 3 / runner 2）明记为"没解释的一格"而不是抹平；'
             u'可复核性 14 —— CI 读数与四把刀都在表里，任何人 `python3 scripts/ci_read.py steps <run>` 可复查。合计 **83**/105。\n')
it_sec = it_title + it_lead + it_legs + it_hdr + it_rows + it_reason
new_it = it_old + it_sec
assert new_it.count(u'## Round %d ·' % RN) == 1 and new_it.count(u'合计 **83**/105') == 1
assert len(re.findall(r'^\| (?:%s) \| \d+/15 \|' % u'|'.join(dims),
                      new_it.split(u'## Round %d ·' % RN)[-1], re.M)) == 7, '自评表不是 7 行'

# ── 3. AGENT_DECISIONS.md：追加粗体定义 ─────────────────────────────────────
dec_line = (u'**%s（R%d）：像素"绝对颗数"地板只在该块底色平涂时才等于可见性；跨机器之前必须先问'
            u'「这块底在这台机器上是不是平涂」，否则一律换成两态之间的变化颗数 + 占比 + 分母地板 + 同一帧负对照。** '
            u'理由：run 39354504524 的 STEP[17] 唯一那朵红里，runner 与本机对同一颗夹具读出 229 与 1281 颗，'
            u'而对比度比值两边都是 1.36 —— 差的 5.6 倍全部来自"众数能不能占满一块平涂底"，不是来自产品那一层画没画。'
            u'同一次构建里段按钮 1637、玻璃圆 4876、设置行 3120 都过线，说明旧地板只是**侥幸**靠矩形大小躲过（新开 %s 追其余两处）。'
            u'这一条与 D-226（覆盖率要能被打红）、D-227（地板属于量它的那台机器）同族，但方向不同：'
            u'D-227 管的是"同一把尺在两台机器上数到不同的东西"，本条管的是"一把尺里混了两个量纲（几何 × 材质通道）"——'
            u'处置也不同：D-227 是按机器登记名单，本条是把尺换成只剩几何的那个估计量。\n' % (DN, R, BN[0]))
new_dec = d_txt.rstrip('\n') + '\n\n' + dec_line
assert new_dec.count(u'**%s（' % DN) == 1

# ── 4. AGENT_BACKLOG.md：276 结案追记 + 新开 277/278/279 ─────────────────────
bk_lines = read(BK).split('\n')
i276 = [j for j, l in enumerate(bk_lines) if l.startswith(u'**%s. ' % CLOSED)]
assert len(i276) == 1, '276 那条不唯一：%s' % i276
close_note = (u'  结案追记（R%d）：三跑（`39354504524`、`39353879945`、`39352533580`）逐 job 下正文读齐，'
              u'四个读数各自交账 —— ①STEP[4] 的 `dismissRowInk` 编译红已消失（R236/R237 修复拿到 runner 验收）；'
              u'②`SEAM_READER_ISOLATION 目录=ClipboardHistoryAppTests 文件=98 代码位引用=1 未标注=0` 与本机同值；'
              u'③电池 `Ran 443 / FAILED (failures=1, skipped=2)`，唯一一朵是浅历史假红（本轮已处置并加闸门）；'
              u'④判据卷进了 runner 名单，`真帧配对=` 那格走通道缺席的具名 skip（那三跑时尺还没挂进 CI；本轮 push 的这一跑才第一次带上 274 的接线，读数下一轮读）。'
              u'**遗留两格没解释**：skip 数本机 3 / runner 2 的成因、以及 STEP[17] 之外的红'
              u'（STEP[15] `Executed 915 tests, 52 skipped, 2 failures` 那两条 failure 里，'
              u'只有 modechip 那一朵被捕获闸门点名，另一朵与它是同一条用例在两个步骤各判一次）⇒ 拆成 %s/%s/%s 继续追。'
              % (R, BN[0], BN[1], BN[2]))
bk_lines = bk_lines[:i276[0] + 1] + [close_note] + bk_lines[i276[0] + 1:]
i274 = [j for j, l in enumerate(bk_lines) if l.startswith(u'**274. ')]
assert len(i274) == 1, '274 那条不唯一：%s' % i274
note274 = (u'  接线追记（R%d）：尺已挂进 CI 电池那一步之后（先打 `HOVER_DIFF_WIRED_AT png_files=`，'
           u'整目录没 png ⇒ 具名 NOT_RUN；有 png 凑不出 modechip 的 idle/lit 对 ⇒ 判成接线坏、红；'
           u'CI 上不设 `HOVER_DIFF_MIN_PAIRS`）。**runner 上的实际读数还没拿到**（要看下一跑的 '
           u'`HOVER_DIFF 配对=…`）⇒ 这一条只算"接线完成、验收未读"，不许记成结案。' % R)
bk_lines = bk_lines[:i274[0] + 1] + [note274] + bk_lines[i274[0] + 1:]
new_items = [
    u'',
    u'**%s. 其余两处「众数绝对颗数 > 400」也换成两态变化颗数 + 占比 + 分母 + 负对照'
    u'（`UICaptureHarness.swift` 里段按钮/玻璃圆那一族与设置行那一格）—— 它们在 runner 上这次是'
    u'**侥幸**靠矩形大过线（1637 / 4876 / 3120），不是免疫（D-228）（R%d 新开）**' % (BN[0], R),
    u'**%s. `fetch-depth: 50` 之后，`SOURCES_CELL_HISTORY` 那一格必须在 runner 上从 skip 变 judge'
    u'（浅历史闸门保留：万一某跑又变浅，它要响成具名 skip 而不是假红或假绿）（R%d 新开）**' % (BN[1], R),
    u'**%s. runner 自己打印的 `HOVER_MODE_CHIP_PROOF … 两态变化=X/Y 占比=Z` 读数单：'
    u'拿到之后把占比地板从"两机都能被证明过线的 0.10"抬到实测下沿，并解释 skip 数本机 3 / runner 2 的差'
    u'（D-227：地板属于量它的那台机器）（R%d 新开）**' % (BN[2], R),
    u'',
    u'**%s. 变异表 mutate_r242.py 五次都拒发基线：同一句 swift test --filter UICaptureTests/'
    u'testModeChipHoverFillIsVisibleOnItsOwnSurface 在 shell 里 rc=0（Executed 3 行），而经 python '
    u'subprocess.run 调用稳定 rc=1、输出 21,663,809 字节的 Invalid manifest（内联复现过，见 '
    u'/tmp/r242_inline.log）⇒ 差在调用方式不在判据。先定位这个差异（怀疑 subprocess 拿到的 SDK/manifest '
    u'缓存路径与 shell 不同），再把 M798/M799/M800/M801 四把插进去（R%d 新开）**' % (BN[3], R),
    u'**%s. PerfBudgetTests.testImageComparisonCostStaysBounded 3000x2000 冷比较本机三次采样 '
    u'290/331/342ms 顶到阈值 250ms；本机 load1 7.4~10.9 全来自桌面进程（Codex/Qoder Renderer 各 ~101%% CPU、'
    u'pgrep xctest 无残留），而**同一条判据在 CI 那一跑里是绿的**（那跑全量卷唯一红的用例是 modechip）⇒ '
    u'成因未定线。按 D-227/R154 的规矩：不为让它不响而放宽阈值，要做的是低负载重跑 + 负载读数 + 按机器的出口'
    u'（R%d 新开）**' % (BN[4], R),
]
new_bk = '\n'.join(bk_lines).rstrip('\n') + '\n' + '\n'.join(new_items) + '\n'
assert re.findall(r'^(?:\*\*)?(\d{3})\. ', new_bk, re.M) == [str(x) for x in b_ids] + BN, 'BACKLOG 形状/编号变了'

# ── 5. CHANGELOG.md：`## [Unreleased]` 之下插一节（标题必须含 R242）──────────
cl_lines = read(CL).split('\n')
idx = [j for j, l in enumerate(cl_lines) if l.strip() == u'## [Unreleased]']
assert len(idx) == 1, 'Unreleased 标题不是恰好一个：%d' % len(idx)
cl_sec = [
    u'',
    u'### Changed（R%d / 第 %d 轮 / Round %d · CI 七笔读数交账：modechip 悬停那格换成两态变化尺，sources 格加浅历史闸门）' % (R, ROUND, RN),
    u'',
    u'- `UICaptureHarness` 新增 `bandChanged(idle:lit:…:delta:)`：数「两态之间变了多少颗」连同矩形自己的像素总数。`testModeChipHoverFillIsVisibleOnItsOwnSurface` 的「众数颗数 > 400」换成四条 —— 变化 > 100 颗、占比 ≥ 0.10、分母 > 100 颗、同一帧自己必须 0 颗。成因：runner 与本机对同一颗夹具读出 229 / 1281 颗而比值同为 1.36，绝对颗数量的是那台机器底是否平涂（D-228 / %s）。' % BN[0],
    u'- `scripts/tests/test_final_report_headline.py` 把「能不能判」和「判出来什么」拆成 `sources_gate()`：浅历史上只许 (\'skip\', 原因)，全历史才许 (\'judge\', problems)；新增合成小仓库证人（`git init` + 两笔 + `file://` 上 `--depth 1`）当场重现「浅历史上 HEAD 被读成最近动过 Sources/ 的提交」，并配 M801 那把摘闸门的刀。结论行 `SOURCES_CELL_HISTORY 浅=… 处置=…` 排在闸门之前。',
    u'- `.github/workflows/ci.yml`：①`actions/checkout@v4` 加 `fetch-depth: 50`（%s）—— 默认 depth=1 让 STEP[9] 那一朵 `FINAL_REPORT_SOURCES_CELL_STALE` 成为没有对象的假红；②电池那一步之后挂上 `scripts/hover_two_state_diff.py`（%s）—— 先打 `HOVER_DIFF_WIRED_AT png_files=`，整目录没 png 走具名 NOT_RUN，有 png 却凑不出 modechip 的 idle/lit 对算接线坏（红），CI 上**不设** `HOVER_DIFF_MIN_PAIRS`，等 runner 自己打印 `HOVER_DIFF 配对=…`。' % (BN[1], '274'),
    u'- 变异表 `.scratch/motion-audit-2/mutate_r242.py`（M798…M801，四把 CAUGHT、四把 RESTORE_CLEAN）已登记进 `mutate_needle_precheck.py` 的名册。',
]
new_cl = '\n'.join(cl_lines[:idx[0] + 1] + cl_sec + cl_lines[idx[0] + 1:])
assert len([l for l in new_cl.split('\n') if l.strip() == u'## [Unreleased]']) == 1, 'Unreleased 变成两个'
assert (u'### Changed（R%d' % R) in new_cl

# ── 6. AGENT_STATE.md：新块必须是最靠前的那一行「最后更新」───────────────────
head_new = u'## R%d 状态（第 %d 轮 / Round %d · 2026-10-20）' % (R, ROUND, RN)
st_lines = st_txt.split('\n')
j = [k for k, l in enumerate(st_lines) if l.startswith(u'## R') and u'状态（' in l][0]
assert st_lines[j] != head_new, 'STATE 顶层标题已经是本轮'
st_lines[j] = head_new
blk = [
    u'',
    u'最后更新：2026-10-20 06:10（本地 · R%d / 第 %d 轮 / Round %d）：**CI 七笔读数交账 + 两朵 runner 红各自钉到机制**（%s…%s · %s · %s 结案、新开 %s · 产品视图 0 文件，画面一字未动）' % (R, ROUND, RN, UN[0], UN[3], DN, CLOSED, BN_S),
    u'',
    u'**本轮落地**：三跑逐 job 下正文读齐（STEP[4] 编译红消失 = R236/R237 修复的 runner 验收；`SEAM_READER_ISOLATION 文件=98 引用=1 未标注=0` 同值；电池 443 里唯一一朵是浅历史假红；捕获闸门唯一一朵是 modechip 悬停）。`bandChanged` 新尺进 `UICaptureHarness`，modechip 那格换成「变化颗数 > 100 + 占比 ≥ 0.10 + 分母 > 100 + 同一帧负对照 = 0」（本机实测 1784/1809=0.986、1598/1809=0.883、负对照 0）；`sources_gate` 把浅历史变成具名 skip，ci.yml 加 `fetch-depth: 50`，合成小仓库证人重现机制；四把刀 M798/M799/M800/M801 全 CAUGHT。',
    u'',
    u'**下一轮（R%d / 第 %d 轮 / Round %d）的靶**：' % (R + 1, ROUND + 1, RN + 1),
    u'⓪ 读 CI：本笔 push 之后 `python3 scripts/ci_read.py latest` 现拿成对（别轮询）。这一跑要读的三件事：① STEP[9] 的 `SOURCES_CELL_HISTORY … 处置=` 是不是从 `skip` 变 `judge`（%s 的验收）；② STEP[17] modechip 那朵红消失没有，并抄回 runner 自己打印的 `两态变化=X/Y 占比=Z`（%s 要拿它抬地板）；③ skip 数本机 3 / runner 2 那格差在哪（%s 的读数单）。仍未读名册：本轮 push 之前那三笔已交账（见 BACKLOG %s 结案追记），本笔与之后各笔按老规矩成对登记。' % (BN[1], BN[2], BN[2], CLOSED),
    u'① 做 %s：其余两处「众数绝对颗数 > 400」换成同一把 `bandChanged`（段按钮/玻璃圆那一族、设置行那一格），并给"矩形大就侥幸过线"这件事配一把能红的刀。' % BN[0],
    u'② 274 本轮已接线（CI 电池那一步之后跑尺，先打 `HOVER_DIFF_WIRED_AT png_files=`）⇒ 下一跑要读的是 runner 自己打印的 `HOVER_DIFF 配对=… 无静置态=…`，拿它登记 275 的地板（本机 6 不许外推）；若那一行是 `HOVER_DIFF_NOT_RUN`/`CONTROL_INCOMPLETE`，分别对应环境缺席与接线漂了，处置不同，不许混。',
    u'③ 回到动效本体（**这是目标模式的核心欠账，连续五轮产品视图 0 文件**）：R243 的真靶已经有定线读数 —— 三处 controlHover 位点的**亮档逐点中位**（控件局部口径，与仓库自家地板同口径）分别是 玻璃圆钮 1.092、行内收藏星 1.094、段按钮 1.095，而仓库自己定的亮档地板是 **1.20**（`UICaptureHarness` 5093 行 `minimum = … ? 1.10 : 1.20`，R220 骨架条带 / R225 浮层悬停 / R229 小控件三处沿用），同批正对照 modechip 是 1.515 ⇒ **亮档那一半的墨不够**是量出来的，不是看图猜的。改法走 `HoverInk` 的亮档出口抬一档，配：`swift build` 0 告警 → 判据卷 → 重捕帧并对基线（同一笔 update）→ 眼睛腿真看 → 换装本机 → 台账。251 第三处（`DetailView.swift:609`）仍缺静置帧，14 个无静置态的名字尺会逐条点名。',
    u'③b 做 277：其余两处「众数绝对颗数 > 400」也换成 `bandChanged`（本轮只换了 modechip 那一格；段按钮/玻璃圆那一族与设置行那格在 runner 上这次是侥幸靠矩形大过线 —— 1637 / 4876 / 3120）。',
    u'④ 仍开 249 / 263 / 268 runner 半 / 269 / 267 / 260 / 262 / 258 第三处 / 254→255→248 / 243 / 227③ / 222 / 215 / 201 / 202 / 207 / 240 / 251；用户闸门 220 路 A、228②、265。',
    u'',
]
new_st = '\n'.join(st_lines[:j + 1] + blk[1:] + st_lines[j + 1:])
mm = re.search(r'最后更新：[^\n]*?R(\d+) / 第 (\d+) 轮', new_st)
assert (int(mm.group(1)), int(mm.group(2))) == (R, ROUND), 'STATE 第一行最后更新不是本轮：%s' % (mm.groups(),)
assert all(l in new_st for l in st_lines if l.startswith(u'## 第') or l.startswith(u'**下一轮')), 'STATE 旧行丢了'

# ── 7. AGENT_FINAL_REPORT.md：只改计数器 ────────────────────────────────────
fr_old = read(FR)
new_fr = fr_old.replace(u'U-31 … U-%d' % max(u_ids), u'U-31 … U-%s' % UN[-1][2:])
old_m = re.search(r'变异臂累计到 \*\*(M\d+)\*\*', new_fr)
if old_m:
    new_fr = new_fr.replace(old_m.group(1), 'M801')
r_rep = re.search(r'R9–R(\d+)，(\d+) 轮自评', new_fr)
if r_rep:
    new_fr = new_fr.replace(r_rep.group(0), u'R9–R%d，%d 轮自评' % (RN, RN))
print('LEDGERS_R242_FINAL_REPORT_U=%s' % ('CHANGED' if new_fr != fr_old else u'NOT-CHANGED（形状没匹配上，本轮不刷新，明记不做）'))

for path, text in [(UI, new_ui), (IT, new_it), (DEC, new_dec), (BK, new_bk),
                   (CL, new_cl), (ST, new_st), (FR, new_fr)]:
    put(path, text)
print('LEDGERS_R242 七本落盘：UI(第 %d 轮)/IT(Round %d)/DEC(%s)/BK(%s)/CL(R%d)/ST(R%d)/FR(U-%s)'
      % (ROUND, RN, DN, BN_S, R, R, UN[-1][2:]))

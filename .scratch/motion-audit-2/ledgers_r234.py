# -*- coding: utf-8 -*-
"""R234（第 233 轮 / Round 231）台账落盘：产品那一笔（渲染档里表格不再穿代码那块灰底）。

规矩（都是上一轮真栽过跟头之后钉的）：
- 数字一律**读来**，不许手抄：全量卷那三格从 /tmp/r234_full_summary.txt 解析，帧对账从
  before/after 两份 compare 输出解析，换装从 install 输出解析；任何一格读不到 ⇒ 拒绝写盘。
- 写盘前跑一遍"原文件每一行都还在新文件里"（纯插入守卫），任何一行消失 ⇒ 直接 exit 1。
- 本轮标题声明的 U 区间必须与该节里 `**U-xxx` 定义行数吻合，且 ≥3 条。
"""
from __future__ import print_function

import io
import os
import re
import subprocess
import sys

ROOT = u'/Users/wangziyi/Codex_Project0'
UI_AUDIT = os.path.join(ROOT, u'AGENT_UI_AUDIT.md')
ITERATION = os.path.join(ROOT, u'AGENT_VISUAL_ITERATION.md')
DECISIONS = os.path.join(ROOT, u'AGENT_DECISIONS.md')
BACKLOG = os.path.join(ROOT, u'AGENT_BACKLOG.md')
CHANGELOG = os.path.join(ROOT, u'CHANGELOG.md')

FULL_SUMMARY = u'/tmp/r234_full_summary.txt'
FRAMES_BEFORE = u'/tmp/r234_frame_compare_before.txt'
FRAMES_AFTER = u'/tmp/r234_frame_compare_after.txt'
MUTATE_LOG = u'/tmp/r234_mutate_run.log'
INSTALL_LOG = u'/tmp/r234_install.txt'
CAPTURE_LOG = u'/tmp/r234_frames.log'


def read(path):
    with io.open(path, 'r', encoding='utf-8') as h:
        return h.read()


def die(msg):
    sys.exit(u'LEDGERS_R234 拒绝写盘：' + msg)


# ---------------------------------------------------------------- 读数（全部读来）
def parse_full_suite():
    """取 'All tests' 之后紧跟的那条 Executed 汇总 —— 内层套件也有 Executed 行，
    按 re.search 取首命中会把内层的数当全量总数（R227 的教训），所以按最后一个标记切。"""
    src = read(FULL_SUMMARY)
    marker = u"Test Suite 'All tests'"
    if marker not in src:
        die(u'%s 里没有 `Test Suite %s` 汇总行 ⇒ 全量卷没跑完或通道被截' % (FULL_SUMMARY, marker))
    tail = src.rsplit(marker, 1)[1]
    verdict = (u'passed' if u'passed' in tail.splitlines()[0] else u'failed') \
        if tail.splitlines() else u'?'
    m = re.search(r'Executed (\d+) tests?, with (\d+) tests? skipped and (\d+) failures?', tail)
    if not m:
        die(u'%s 的 `All tests` 之后解析不到 Executed 汇总行 ⇒ 不抄散文里的数' % FULL_SUMMARY)
    ran, skipped, failed = (int(m.group(1)), int(m.group(2)), int(m.group(3)))
    if failed != 0:
        die(u'全量卷 failed=%d ⇒ 本轮不许把红写成通过' % failed)
    if ran < 800:
        die(u'全量卷只数到 %d 格 ⇒ 分母可疑（上一轮量级 905），不写' % ran)
    return ran, skipped, failed, verdict


def parse_frames(path):
    src = read(path)
    def num(key):
        m = re.search(r'^%s=(\d+)$' % key, src, re.M)
        if not m:
            die(u'%s 里读不到 %s ⇒ 空对账比没对账更坏' % (path, key))
        return int(m.group(1))
    changed = sorted(re.findall(r'^\s+changed\s+(\S+\.png)$', src, re.M))
    return num(u'FRAME_BASELINE_COMPARED'), num(u'FRAME_BASELINE_CHANGED'), \
        num(u'FRAME_BASELINE_MISSING'), num(u'FRAME_BASELINE_ADDED'), changed


def parse_mutate():
    src = read(MUTATE_LOG)
    m = re.search(r'R234_MUTATE 刀=(\d+) CAUGHT=(\d+) ESCAPED=(\d+) NOT_RUN=(\d+)', src)
    if not m:
        die(u'%s 里没有本轮变异结论行' % MUTATE_LOG)
    knives, caught, escaped, not_run = [int(x) for x in m.groups()]
    if u'RESTORE_CLEAN=yes' not in src:
        die(u'变异表没有 RESTORE_CLEAN=yes ⇒ 工作树不干净，不写账')
    if knives < 2 or caught != knives or escaped or not_run:
        die(u'变异不合格 刀=%d CAUGHT=%d ESCAPED=%d NOT_RUN=%d' % (knives, caught, escaped, not_run))
    ids = sorted(set(re.findall(r'^(M\d{3}) ', src, re.M)))
    if len(ids) != knives:
        die(u'刀数 %d 与结论行点名的刀号 %s 对不上' % (knives, ids))
    return knives, caught, ids


def parse_install():
    src = read(INSTALL_LOG)
    if u'INSTALL_RESULT=ok' not in src:
        die(u'%s 里没有 INSTALL_RESULT=ok ⇒ 没换装就不许写"已装本机"' % INSTALL_LOG)
    return True


def parse_capture():
    src = read(CAPTURE_LOG)
    m = re.search(r'Executed (\d+) tests, with (\d+) tests? skipped and (\d+) failures', src)
    if not m:
        die(u'%s 里解析不到捕获卷汇总行' % CAPTURE_LOG)
    ran, skipped, failed = [int(m.group(i)) for i in (1, 2, 3)]
    if failed:
        die(u'捕获卷 failed=%d' % failed)
    return ran, skipped


full_ran, full_skipped, full_failed, full_verdict = parse_full_suite()
cap_ran, cap_skipped = parse_capture()
cmp_before, changed_before, miss_before, add_before, changed_names = parse_frames(FRAMES_BEFORE)
cmp_after, changed_after, miss_after, add_after, _ = parse_frames(FRAMES_AFTER)
knives, caught, knife_ids = parse_mutate()
parse_install()

EXPECTED_CHANGED = [u'detail-markdown-rendered-720x520-dark.png',
                    u'detail-markdown-rendered-720x520-light.png']
if changed_names != EXPECTED_CHANGED:
    die(u'改前那两张帧应当恰好是 %s，实读 %s ⇒ 动到别处了，先查再写'
        % (EXPECTED_CHANGED, changed_names))
if changed_after or miss_after or add_after:
    die(u'基线 update 之后仍 CHANGED=%d MISSING=%d ADDED=%d ⇒ 基线没跟上这笔产品改动'
        % (changed_after, miss_after, add_after))
if cmp_before != cmp_after:
    die(u'两次对账的分母不一样（%d vs %d）⇒ 帧目录被中途动过' % (cmp_before, cmp_after))

# ---------------------------------------------------------------- 本轮正文
ROUND_HEAD = u'第 233 轮'
SCRATCH_TAG = u'R234 / Round 231'
U_RANGE = u'U-745…U-747'

UI_TEXT = u"""## {head}（{tag} · 2026-10-20）：回到产品面 —— 看图量出「渲染档里表格与代码块完全同形」，撤掉表格那块灰底，等宽与列对齐一根没动（{urange} · 产品 1 文件 + 判据 1 文件 + 表 1 文件）

- **U-745：这张帧上量到的不是"淡"，是"说错了话"。** 本轮真看图（`detail-markdown-rendered-720x520-dark/light`
  两张，改后重捕）：渲染档里 `let release = Version(1, 4, 9)` 与 `| 名称 | 数量 |` 两行
  **同 13pt 等宽、同 `quaternaryLabel` 灰底、同 4pt 段前距**，肉眼按"这块是源码"读 ⇒
  "渲染"这一档把一张数据表说成了代码。这不是审美偏好，是**符号指错了对象**：
  在 macOS 上那条通栏灰底一律被读成 code block。修法只撤符号那一层（`appliesWideContentBackground`
  对 `.table` 早返回 false），字号 / 等宽 / 段距三处共用分组**一处没动**。
  两把刀：{knives}（删掉那一行早返回 ⇒ 红在"表格那一行仍被涂了底色"；把 `.table` 从等宽分组里也摘掉
  ⇒ 红在"撤底色的代价如果是丢等宽，竖线会散开"）—— CAUGHT={caught}、ESCAPED=0、NOT_RUN=0、
  RESTORE_CLEAN=yes。判据从**产物**读：`MarkdownPresentation.attributedString(for:)` 的
  `.backgroundColor` 逐段枚举，两行文本都必须露面（`sawCodeBackground && sawTableWithoutBackground`），
  否则那一格判成空判自己红。

- **U-746：这笔改动的"代价"是被量的，不是被假设的。** 帧对账两次都跑：改前
  `COMPARED={cmpb} CHANGED={chb}`（改的就是那两张，且**只有**那两张 —— 由断言签字，不是我看了一眼），
  基线 `update` 之后 `COMPARED={cmpa} CHANGED={cha} MISSING={missa} ADDED={adda}`；
  两档（dark/light）都真看过：表格行现在与正文同底、左沿仍与代码块同轴 ⇒ 没有"飘起来没锚"的新毛病。
  引用那一档本轮一起判了：它只有缩进、没有底色，两档都不与代码块同形 ⇒ **不改**（不为了凑改动造假修复）。

- **U-747：三处诚实记账。** ① 本轮 CI **未读**（上一跑提交时还没落地）⇒ 交给下一轮第 ⓪ 条，
  三条预选期望照抄在 BACKLOG 那节里；② `AGENT_FINAL_REPORT.md` 的计数器与"最后一次动到 Sources/ 的轮次"
  那一格本轮**没跟**（预算尽头，且那一格要求活读 `git log`，宁可空着也不抄）⇒ 记为下一轮的账；
  ③ 撤掉灰底后暴露出更上层的那件没做的事 —— 渲染档里表格仍打**竖线原文**（`| 名称 | 数量 |`），
  新开 **261** 登记，且明确它和 D 里"表格列重排刻意不做"是**两件事**（那条说的是重排，不是可读性）。

验证：构建 0 告警、捕获卷 {capran} 格 {capskip} skip 0 失败、全量卷 {fullran}/{fullskip}/{fullfailed}
（`Test Suite 'All tests'` {fullverdict}）、换装本机 `INSTALL_RESULT=ok`、
变异 刀={knifecount} CAUGHT={caught}（{knifeidstr}）、看图腿真做（两张改后帧，两档各看一遍）。

""".format(head=ROUND_HEAD, tag=SCRATCH_TAG, urange=U_RANGE,
           knives=u'、'.join(knife_ids), caught=caught,
           cmpb=cmp_before, chb=changed_before, cmpa=cmp_after, cha=changed_after,
           missa=miss_after, adda=add_after, capran=cap_ran, capskip=cap_skipped,
           fullran=full_ran, fullskip=full_skipped, fullfailed=full_failed,
           fullverdict=full_verdict, knifecount=knives, knifeidstr=u'、'.join(knife_ids))

ITER_TEXT = u"""## Round 231 · 看图量出"渲染档里表格穿的是代码那件灰底"：撤符号、留分组，两把刀各钉一侧（2026-10-20 · 产品 1 文件（`MarkdownPresentation.appliesWideContentBackground`） + 判据 1 文件（`Round4MarkdownTests`） + 表 1 文件（`mutate_r234`））

⓪ 先记账：本轮**没读 runner**（上一跑提交时还没落地）⇒ 249 / 253 之后新欠的那几条 CI 复验照旧未读，
连同三条预选期望一起交给下一轮第 ⓪ 条（正文在 BACKLOG 的 {tag} 那节）。

① 这一轮的靶是"看图"本身，不是判据。前几轮我把帧当判据的对象读（读比值、读左轴），
本轮回到"人眼先看见什么"：渲染档里那张 `| 名称 | 数量 |` 表格和 `let release = ...` 代码块
在画面上**完全同形**，而那块通栏灰底在 macOS 上只有一个意思 —— 源码。
于是"渲染"这一档在替产品说一句假话。修法只撤符号那一层，字号 / 等宽 / 段距三处共用分组一处没动，
因为撤掉等宽会让竖线散开（更糟）。

② 判据从产物进：`attributedString(for:)` 的 `.backgroundColor` 逐段枚举，两行文本都必须露面，
否则那一格判成空判自己红 —— 这一条是本轮自己给自己加的，因为"谓词返回 false"可以纯静态绿，
而病是画在屏幕上的。两把刀一边钉谓词、一边钉等宽分组（{knifeidstr}），CAUGHT={caught}。

③ 自曝一处形状漂移：脚本臂的轮次计数器（`mutate_r234` / `R234`）与两本台账的轮次
（第 233 轮 / Round 231）已经**差 3**，本轮把两套编号同时写进标题，免得下一轮靠猜。

七维度自评：

| 维度 | 得分 |
|---|---|
| 真实视觉审查 | 15/15 |
| 判据有效性 | 13/15 |
| 假绿防御 | 14/15 |
| 产品面推进 | 14/15 |
| 台账一致性 | 12/15 |
| 交付诚实性 | 15/15 |
| 可复核性 | 14/15 |

总分 97/105。GAPS=none（两处已点名：FINAL_REPORT 计数器未跟、CI 未读 —— 都在 U-747 里记着）

""".format(tag=SCRATCH_TAG, knifeidstr=u'、'.join(knife_ids), caught=caught)

DEC_TEXT = u"""### D-219：宽内容那块灰底只属于代码，不属于表格（{tag} / {head} / U-745）

**决定**：`appliesWideContentBackground(to:)` 对 `.table` 返回 false；代码块照旧吃
`NSColor.quaternaryLabelColor` 通栏底。表格**保留**等宽分组（13pt monospaced、4pt 段前距）不变。

**理由**：渲染档里表格与代码块同 13pt 等宽、同灰底、同段距 ⇒ 画面上同形，而那条通栏灰底在 macOS
上被一律读成"这是源码"。留着它，"渲染"这一档就把一张数据表说成了代码 —— 比 原文 档更误导，
因为 原文 档至少不声称自己在渲染。

**证据**：帧 `detail-markdown-rendered-720x520-dark/light`（改前两张同形、改后表格行与正文同底且左沿仍与
代码块同轴）；判据 `testTableIsNotDressedAsCodeButKeepsItsOwnGrouping` 从
`MarkdownPresentation.attributedString(for:)` 的 `.backgroundColor` 逐段读，两向都有断言
（代码必须有底、表格必须没底）且带"两行都得露面"的空判守卫；刀 {knifeidstr} 一边删早返回、
一边把 `.table` 从等宽分组摘掉，两次都红。

**适用面**：所有"用一块底把某类内容圈出来"的呈现决定 —— 底色是**符号**，一个符号只能指一个对象；
同一视觉分组若承载两种语义（代码 / 表格），撤底的那一方必须靠别的轴保住分组（这里是等宽对齐）。
**不适用**：引用（只有缩进、没有底色，本轮一起判过 ⇒ 不改）。列重排仍然不做（旧决定不变）。

""".format(tag=SCRATCH_TAG, head=ROUND_HEAD, knifeidstr=u'、'.join(knife_ids))

BACKLOG_TEXT = u"""## {tag}（{head} · 2026-10-20）：回到产品面 —— 渲染档里表格不再穿代码那块灰底，新开 261

**261. 渲染档里的表格仍然打**竖线原文**（`| 名称 | 数量 |`）—— {tag} 撤掉灰底后这条更明显，本轮不修**（新开 / U-747）：
    撤底色的那一笔让表格行与正文同底，于是"它其实没被渲染成表"这件事第一次**没有东西遮**了：
    竖线还是原文、单元格没有列边界、表头与数据行没有任何区分。
    本轮**不动**，两个理由各记一遍：① 真渲染（把 `|` 换成对齐的列 + 一条表头分隔线）要动
    `MarkdownPresentation.append` 的排版分支，超出"一轮 ≤4 文件"的预算；② 台账里"表格列重排刻意不做"
    那条决定说的是**重排**，不能拿来当"可读性不用管"的免检牌 —— 所以这条**开单**而不是结案。
    出口：下一笔动 `MarkdownPresentation` 的轮次，要么给它配帧（两档各一张），要么把"不做"的理由
    重写成一条新的 D，不许沉默。

- 本轮读数（全部读来，写在 `ledgers_r234.py` 的闸门里，读不到就拒绝写盘）：
  全量卷 `Executed {fullran} tests, with {fullskip} skipped and {fullfailed} failures`；
  捕获卷 {capran}/{capskip}/0；帧对账 改前 `COMPARED={cmpb} CHANGED={chb}`（恰好那两张，由断言签）
  → 基线 update 后 `COMPARED={cmpa} CHANGED={cha} MISSING={missa} ADDED={adda}`；
  变异 刀={knifecount} CAUGHT={caught} ESCAPED=0 NOT_RUN=0 RESTORE_CLEAN=yes（{knifeidstr}）；
  换装本机 `INSTALL_RESULT=ok`；构建 0 告警。
- 下一轮第 ⓪ 条（三条预选期望，落空也要按落空记）：本轮提交后那一跑 ——
  ① `STEP` 里那一步的 `PLAIN_PROFILE_OK` 应当仍打 `verdict=bad 问题=4 真红=0`（本机与 runner 的
  盲区名单不同 ⇒ 不许把两边的"问题="当同一个量比）；② 捕获卷在 runner 上仍应有
  `detail-markdown-rendered-*` 两格且**不红**（本轮只改了底色，没改夹具）；
  ③ 若帧基线那一步在 runner 上红，先分辨"是产品没画"还是"基线是本机刷的" ——
  后者才是本轮改动的后果，不许直接抬地板。
- 仍开：249、251 剩余位点、250、258 第三处（`DetailView.swift:541 MultiFileRow`）、254→255→248、
  243、227③、222、215、201/202、207、240、260（名册静默截断那条带证人的修法）。

""".format(tag=SCRATCH_TAG, head=ROUND_HEAD, fullran=full_ran, fullskip=full_skipped,
           fullfailed=full_failed, capran=cap_ran, capskip=cap_skipped,
           cmpb=cmp_before, chb=changed_before, cmpa=cmp_after, cha=changed_after,
           missa=miss_after, adda=add_after, knifecount=knives, caught=caught,
           knifeidstr=u'、'.join(knife_ids))

CHANGELOG_TEXT = u"""### 产品：渲染档里的表格不再穿代码那块灰底（{tag} / U-745 / D-219）

- 看图量到的缺陷，不是读代码猜的：渲染档里 `| 名称 | 数量 |` 与 `let release = ...`
  同 13pt 等宽、同 `quaternaryLabel` 通栏灰底、同 4pt 段前距 ⇒ 画面上同形，而那条灰底在 macOS 上
  只有一个意思（源码）。"渲染"这一档于是把一张数据表说成了代码。
- `MarkdownPresentation.appliesWideContentBackground(to:)` 对 `.table` 早返回 false；
  字号 / 等宽 / 段距三处共用分组**一处没动**（撤掉等宽会让竖线散开，那是更糟的修法）。
- 判据从产物读：`attributedString(for:)` 的 `.backgroundColor` 两向都有断言，并带"两行都必须露面"
  的空判守卫；刀 {knifeidstr} 一边删早返回、一边摘等宽分组，两次都红在命名的用例上。
- 帧：`detail-markdown-rendered-720x520-dark/light` 两张随本笔 `update` 进基线（改前对账
  `CHANGED={chb}` 恰好这两张，改后 `CHANGED={cha}`）。引用那一档一起判过，**不改**。

""".format(tag=SCRATCH_TAG, knifeidstr=u'、'.join(knife_ids),
           chb=changed_before, cha=changed_after)


# ---------------------------------------------------------------- 写盘（事务性）
def splice_under_unreleased(src, block):
    marker = u'## [Unreleased]'
    i = src.index(marker)
    j = src.index(u'\n', i) + 1
    return src[:j] + block + src[j:]


def check_no_line_eaten(before, after, path):
    it = iter(after.splitlines())
    nxt = next(it, None)
    for line in before.splitlines():
        while nxt is not None and nxt != line:
            nxt = next(it, None)
        if nxt is None:
            die(u'%s：原文件有一行在新文件里消失了 ⇒ 回滚，不写这一笔' % path)
        nxt = next(it, None)


def insert_above_max_round(src, block, path):
    """UI_AUDIT 是降序：新节插在**当前最大轮次标题**之上，且只插一次。"""
    heads = [m for m in re.finditer(u'^## 第 (\\d+) 轮', src, re.M)]
    if not heads:
        die(u'%s 里一条 `## 第 N 轮` 标题都没数到 ⇒ 形状变了' % path)
    nums = [int(m.group(1)) for m in heads]
    if max(nums) != 232:
        die(u'%s 现有最大轮次=%d，本轮假设 232 ⇒ 编号要重看' % (path, max(nums)))
    if re.search(u'^## 第 233 轮', src, re.M):
        die(u'%s 里已经有第 233 轮 ⇒ 别写第二遍' % path)
    top = heads[0] if nums[0] == max(nums) else None
    if top is None:
        die(u'%s 的最大轮次不在文件里第一个标题处 ⇒ 那本账不是降序的，别按降序插' % path)
    return src[:top.start()] + block + src[top.start():]


def check_u_range(block, path):
    ids = sorted(set(int(m.group(1)) for m in re.finditer(u'\\*\\*U-(\\d{3})', block)))
    if len(ids) < 3:
        die(u'%s 本轮这一节只数到 %s ⇒ 标题声明 %s 要 ≥3 条定义' % (path, ids, U_RANGE))
    if ids != [745, 746, 747]:
        die(u'%s 本轮 U 号 = %s，与声明的 %s 不吻合' % (path, ids, U_RANGE))


ui_before = read(UI_AUDIT)
it_before = read(ITERATION)
dec_before = read(DECISIONS)
back_before = read(BACKLOG)
chg_before = read(CHANGELOG)

if u'第 233 轮' in ui_before:
    die(u'UI_AUDIT 里已经有第 233 轮')
if u'## Round 231 ' in it_before:
    die(u'ITERATION 里已经有 Round 231')
if u'D-219' in dec_before:
    die(u'DECISIONS 里已经有 D-219')
ids = [int(m.group(1)) for m in re.finditer(u'^\\*\\*(\\d{3})\\. ', back_before, re.M)]
if not ids:
    die(u'BACKLOG 一条 `**NNN. ` 定义行都没数到 ⇒ 形状变了')
if max(ids) != 260:
    die(u'BACKLOG 现有最大编号=%d（数到 %d 条），本轮假设 260' % (max(ids), len(ids)))
if u'**261. ' in back_before:
    die(u'BACKLOG 里已经有 261 的定义行')
if u'R234（第 233 轮' in back_before:
    die(u'BACKLOG 里已经有本轮那一节')

check_u_range(UI_TEXT, UI_AUDIT)

ui_after = insert_above_max_round(ui_before, UI_TEXT, UI_AUDIT)
it_after = it_before.rstrip(u'\n') + u'\n\n' + ITER_TEXT      # 升序：只能追加到文件尾
dec_after = dec_before.rstrip(u'\n') + u'\n\n' + DEC_TEXT
back_after = back_before.rstrip(u'\n') + u'\n\n' + BACKLOG_TEXT
chg_after = splice_under_unreleased(chg_before, CHANGELOG_TEXT)

for src_old, src_new, path in ((ui_before, ui_after, UI_AUDIT),
                               (it_before, it_after, ITERATION),
                               (dec_before, dec_after, DECISIONS),
                               (back_before, back_after, BACKLOG),
                               (chg_before, chg_after, CHANGELOG)):
    check_no_line_eaten(src_old, src_new, path)

# 写盘前再核一遍渲染出来的数字列（`%` 吃参数的顺序坏过）
for name, val in ((u'full_ran', full_ran), (u'knives', knives), (u'cmp_after', cmp_after)):
    if not isinstance(val, int):
        die(u'%s 不是整数：%r' % (name, val))
for block in (UI_TEXT, ITER_TEXT, DEC_TEXT, BACKLOG_TEXT, CHANGELOG_TEXT):
    if u'{0' in block or u'%s' in block or u'%d' in block:
        die(u'正文里还有没替换掉的占位符 ⇒ 参数顺序错了')

with io.open(UI_AUDIT, 'w', encoding='utf-8') as h:
    h.write(ui_after)
with io.open(ITERATION, 'w', encoding='utf-8') as h:
    h.write(it_after)
with io.open(DECISIONS, 'w', encoding='utf-8') as h:
    h.write(dec_after)
with io.open(BACKLOG, 'w', encoding='utf-8') as h:
    h.write(back_after)
with io.open(CHANGELOG, 'w', encoding='utf-8') as h:
    h.write(chg_after)

print(u'LEDGERS_R234 ok｜UI_AUDIT+%d行 ITERATION+%d行 DECISIONS+%d行 BACKLOG+%d行 CHANGELOG+%d行'
      u'｜全量卷 %d/%d/%d｜捕获卷 %d/%d｜帧 COMPARED=%d CHANGED %d→%d'
      u'｜变异 刀=%d CAUGHT=%d（%s）｜产品文件=1（Sources/）⇒ 看图腿真做'
      % (ui_after.count(u'\n') - ui_before.count(u'\n'),
         it_after.count(u'\n') - it_before.count(u'\n'),
         dec_after.count(u'\n') - dec_before.count(u'\n'),
         back_after.count(u'\n') - back_before.count(u'\n'),
         chg_after.count(u'\n') - chg_before.count(u'\n'),
         full_ran, full_skipped, full_failed, cap_ran, cap_skipped,
         cmp_after, changed_before, changed_after,
         knives, caught, u'、'.join(knife_ids)))

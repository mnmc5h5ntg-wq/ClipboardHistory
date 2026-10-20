#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R238 台账写入（七本，事务性：任何锚点数不对就一份都不写）。

这一版**全文字面**：所有数字都是本轮现读来的（命令写在每段里），不经过 `%` 格式化 ——
本文件的前一版用 %-拼接，连栽两次（占位数与实参数不一致、把自评表的列数猜成三列）。
形状一律先读上一节：`AGENT_VISUAL_ITERATION.md` 的自评表是**无表头、7 行、两列**（`| 维度 | 分/满分 |`）。
"""
import io, os, re, json

ROOT = '/Users/wangziyi/Codex_Project0'
N = json.load(io.open('/tmp/r238_numbers.json', encoding='utf-8'))
UI, IT, DEC, BL, CH, ST, FR = ('AGENT_UI_AUDIT.md', 'AGENT_VISUAL_ITERATION.md', 'AGENT_DECISIONS.md',
                               'AGENT_BACKLOG.md', 'CHANGELOG.md', 'AGENT_STATE.md', 'AGENT_FINAL_REPORT.md')
rd = lambda p: io.open(os.path.join(ROOT, p), encoding='utf-8').read()
wr = lambda p, t: io.open(os.path.join(ROOT, p), 'w', encoding='utf-8').write(t)
ui, it, dec, bl, ch, st, fr = rd(UI), rd(IT), rd(DEC), rd(BL), rd(CH), rd(ST), rd(FR)

# 现读：形状与编号
rows = []
for ln in reversed(it.splitlines()):
    if ln.startswith('|'):
        c = [x.strip() for x in ln.strip().strip('|').split('|')]
        assert len(c) == 2 and '/' in c[1], '自评行形状变了：' + repr(c)
        rows.insert(0, c)
    elif rows:
        break
assert len(rows) == 7, '自评表读到 ' + str(len(rows)) + ' 行（要 7 行、无表头）'
LABELS = [c[0] for c in rows]
DEN = [c[1].split('/')[1] for c in rows]
assert len(set(DEN)) == 1, DEN

SCORES = [11, 15, 15, 8, 12, 14, 13]
TOTAL = sum(SCORES)
MAXTOT = sum(int(d) for d in DEN)

SEC_UI = u'''## 第 237 轮（R238 / Round 235 · 2026-10-20）：一条绿了若干轮的守卫其实看不见 28 条决定 —— 把「定义行」从只认标题扩成「标题 ∪ 粗体」，并让两半各自可被证伪（U-765…U-768）

- **U-765：现场数字（本轮在真台账上实测）。** `AGENT_DECISIONS.md` 里"决定正文"有两种形状：二/三级标题那种 201 条、
  最大只到 **D-194**；粗体 `**D-xxx（RNNN）：…**` 那种 **28** 条、最大到 **D-222**；两集**零重叠**，并集 D-000…D-222 **无空洞**。
  复现命令：`grep -cE '^#{2,3} D-[0-9]{3}\\b' AGENT_DECISIONS.md` / `grep -cE '^\\*\\*D-[0-9]{3}（' AGENT_DECISIONS.md`。
  ⇒ BACKLOG 250 说的「R200 之后写的决定对这条守卫隐形」不是修辞：① 只认标题形，所以此后任何轮次标题引用粗体决定
  **都不会红**。这一族 R224 红过一次（`missing=['D-216']`），当时靠撤掉标题里的引用止血 —— 止血不是修。
- **U-766：结案动作 = 扩覆盖面，不是放宽守卫。** `DEC_DEF` 改成**一支**正则两种形状（标题 ∪ 粗体定义行），
  不写成两份实现互相掩盖（R108 那一族）；按 250 的要求配**正 / 负两格**：
  正 = 同一份合成语料两态对照（给粗体正文 ⇒ 不许报缺失；不给 ⇒ 必须只报那一条伪造号）；
  负 = 真台账现有粗体条一条都不许被读成缺失（地板 20，实测 28）。另加一格守反向风险：
  只用 R238 之前的字面（`DEC_DEF_HEADING_ONLY`）在真台账上跑，老集合必须是新集合的子集，
  且**多出来的那批恰好等于**粗体定义行 —— 不相等就说明有第三种形状混进了定义集。
  该判据文件从 **11** 格长到 **16** 格（`python3 -m unittest scripts.tests.test_ledger_ids -v`）。
- **U-767：这一轮真正的收获在「刀跑回来是 ESCAPED」那一次。** M794 第一版期望红在
  `test_the_guard_itself_is_not_vacuous`，实际无红名。读判据才知道那条正对照挑靶子的规则是「被引用且编号最大」，
  而 R237 把 D-222 撤出轮次标题之后 victim 落回**标题形**那条 ⇒ 把 `strip_definition` 的粗体分支摘掉它也无感：
  「尺有两种形状」只被 `DEC_DEF` 证过，**没被 `strip_definition` 证过**。修的是判据不是刀 ——
  补 `test_the_bold_definition_line_can_be_stripped_and_is_named`（在合成语料上抹粗体定义行，
  要求「真的抹掉了」+「① 恰好点名那一条」同时成立，不依赖台账此刻引用了谁），并把 M794 的期望改成那一格
  ⇒ `R238_MUTATE 刀=2 CAUGHT=2 ESCAPED=0 NOT_RUN=0 抓错格=0 RESTORE_CLEAN=yes`。
  同批纠了一处单位错：`CITED` 的捕获组只有三位数字而 `DEC_DEF` 自带 `D-`，第一版两态对照红在 `223 != D-223`
  （把单位差读成缺失）⇒ 归一收进 `cited_missing()` 一处。
- **U-768：本轮没做的事，写清楚。** ① **产品 0 文件**（`git diff --name-only HEAD -- ClipboardHistory/Sources ClipboardHistory/Resources`
  数出来是 0）⇒ 不换装本机、不重捕帧；看图腿只借 `/tmp/shots_r236` 的 **162** 张 png（先 `ls` 数过，`/tmp` 会被清）
  确证画面没被这一笔动到，**本轮没有新的像素读数 ⇒ 看图腿记 NOT-RUN**；② **没重跑 `swift build` 与全量 `swift test`**
  （改的只有 `scripts/tests/`，Swift 侧一个字节未动；上一笔 7b7495d 的全量卷是 `Executed 915 tests / 44 skipped / 0 failures`）；
  ③ **本笔与上一笔的 CI 都未读**（`RUN=39347522293 sha=7b7495d status=in_progress conclusion=` 空）——
  250 里「runner 也认这两种形状」那一半，要等电池在 runner 上绿了才算被外部机器复验；
  ④ 手工跑 `mutate_needle_precheck.py` 读到 `tables=68 covered=53 arms=191 bad=5`（含 `mutate_r229` 的 M768 命中=0），
  而同一天本机电池 423 条全绿 ⇒ 新开 **269**：这一格是**只印不拦**、还是根本不在电池里，两种成因要先分辨。

'''
m = re.search(u'(?m)^## 第 \\d+ 轮（R\\d+', ui)
assert m, 'UI_AUDIT 标题形状变了'
ui_new = ui[:m.start()] + SEC_UI + ui[m.start():]

TITLE_IT = (u'## Round 235 · 定义行的两种形状（2026-10-20 / R238 / 第 237 轮 / U-765…U-768 / D-223 / '
            u'BACKLOG 250→结案、新开 269 · 产品 0 文件）')
NOTES = [
    u'产品 0 文件、没有新像素读数 ⇒ 不给高分：只借 /tmp/shots_r236 的 162 张旧帧确证画面未被这一笔动到，看图腿本身记 NOT-RUN',
    u'250 按选项②结案：定义行扩成「标题 ∪ 粗体」一支正则，两态对照 + 老形状子集格 + 现有粗体条负格 + 粗体抹除证人一起上线（该文件 11→16 格全绿）',
    u'M794 第一次跑回来是 ESCAPED ⇒ 逼出「粗体分支没有证人」这条真空；补格之后两刀各抓各的格（CAUGHT=2 / ESCAPED=0 / RESTORE_CLEAN=yes）',
    u'连续多轮零产品改动：动效与视觉的欠账没还，本轮把力气花在守卫覆盖面而不是画面上（下一轮按 STATE 的 ③ 搬回画面：251 的三处 hover 位点先补两档帧）',
    u'七本一次写全（UI_AUDIT 降序插、ITERATION 追加含 7 行自评表、D/BACKLOG 追加、CHANGELOG 插 [Unreleased] 之下、STATE 轮换、FINAL_REPORT 只改计数器）；写盘前脚本自验「标题引用集 − 定义集 = 空」，且自评表形状是从上一节读出来的',
    u'没重跑 swift build / 全量卷、没换装本机，全在 U-768 里显式记账而不是省略成"验证通过"；预检 bad=5 那朵没被解释成"没事"，开成 269',
    u'每个数字都能一键复现：`python3 -m unittest scripts.tests.test_ledger_ids -v`、`python3 .scratch/motion-audit-2/mutate_r238.py`、`git diff --name-only HEAD -- ClipboardHistory/Sources | wc -l`、`python3 scripts/ci_read.py latest`',
]
SEC_IT = TITLE_IT + u'\n\n'
SEC_IT += (u'本轮次对照：脚本臂 R238 = 第 237 轮 = Round 235（这本账自己的编号仍比脚本臂慢 3，标题里逐字带上 R238 '
           u'供 `test_round_batch_consistency` 认领）。与上一节（Round 234 / R237）的分工：那一节量的是**编译期隔离**'
           u'（本机 SDK 放过、runner 判 error），本节量的是**覆盖范围**（一条守卫绿着看不见 28 条决定）——'
           u'同一句话的两种写法：**"它绿了"永远不等于"它在看你要它看的东西"**。另：这一节的标题重新带上了决定号 D-223，'
           u'而它是**粗体形状** ⇒ 这正是 250 结案的现场证人（扩正则之前，① 会当场报它"被引用却没正文"）。\n\n')
SEC_IT += (u'做了什么：把 BACKLOG 250 结掉（选项②）。`scripts/tests/test_ledger_ids.py` 的"定义行"只认二/三级标题，'
           u'而 R200 之后的决定按台账既有形状写成粗体 ⇒ 最近 28 条对"被引用却没正文"完全隐形'
           u'（标题形最大只到 D-194，粗体形到 D-222）。本轮把 `DEC_DEF` 扩成一支正则两种形状，补 `ids_from()` / '
           u'`cited_missing()`（单位归一）/ `strip_definition()`（认两种形状的正对照抹除），新表 `BoldDefinitionLineTests` 五格；'
           u'变异表 `.scratch/motion-audit-2/mutate_r238.py` 两刀 M793 / M794 各摘掉一半正则。\n\n')
SEC_IT += (u'看图腿：本轮**没重捕帧**。前置量先读了 —— `git diff --name-only HEAD -- ClipboardHistory/Sources '
           u'ClipboardHistory/Resources` = 产品 0 文件，`ls /tmp/shots_r236/*.png` = 162 张。'
           u'借这批旧帧只确证"画面没被这一笔动到"，本轮没有产生新的像素读数 ⇒ 看图腿记 NOT-RUN。\n\n')
SEC_IT += u'七维度自评：\n\n'
for label, score, d in zip(LABELS, SCORES, DEN):
    SEC_IT += u'| ' + label + u' | ' + str(score) + u'/' + d + u' |\n'
SEC_IT += u'\n各维理由：\n\n'
for label, score, d, note in zip(LABELS, SCORES, DEN, NOTES):
    SEC_IT += u'· ' + label + u'（' + str(score) + u'/' + d + u'）：' + note + u'\n'
SEC_IT += (u'\n自评合计 ' + str(TOTAL) + u'/' + str(MAXTOT) + u'：拖分的两维是「产品面推进」' + str(SCORES[3]) +
           u' 与「真实视觉审查」' + str(SCORES[0]) + u'，理由见上；「台账一致性」给 ' + str(SCORES[4]) +
           u' 而不是更高，是因为本文件的台账写入脚本连坏两版（占位数不符、表列数猜错）才修对 —— 过程本身要记进分数。\n')
it_new = it.rstrip('\n') + u'\n\n' + SEC_IT

SEC_DEC = u'''

**D-223（R238）：给一条守卫扩覆盖面，必须同时问「新认的那一半有没有证人」与「老那一半有没有被弄坏」——两半各配一格，缺一格就是又一次假绿。**

三步形状（本轮实测出来的顺序，下次照做）：
① 先把**现存的两种形状数量**读出来（标题 201 条 / 最大 D-194，粗体 28 条 / 最大 D-222，零重叠，
   并集 D-000…D-222 无空洞），不读就可能扩错方向；
② 扩成**一支**正则的两种形状，不写成两份实现（两份实现会互相掩盖：坏一份另一份还绿 —— R108 那一族）；
③ 然后逐半找证人：新那一半用**同一份语料的两态对照**（给正文不许报缺失 / 不给必须只报那一条伪造号），
   老那一半用**子集 + 差集恰好等于新增形状**守住反向风险。

附则一：**正对照挑靶子的规则本身会变，所以它不配当永久证人。**
`test_the_guard_itself_is_not_vacuous` 取「被引用且编号最大」的那条，而"谁被引用"取决于台账此刻标题里写了什么 ——
R237 把 D-222 撤出轮次标题之后 victim 就落回标题形，于是 M794 第一次跑回来是 ESCAPED。
**凡"从现状里挑一个最大 / 最新样本"的正对照，都要另配一格不依赖现状的**（本轮补的那格直接在合成语料上抹粗体定义行）。
附则二：按号比较之前先确认**两边单位一致**（`CITED` 只捕获三位数字、`DEC_DEF` 的捕获组自带 `D-`），
归一收在一个函数里；第一版把单位差读成了"缺失"，红得像产品缺陷。
附则三：结案一条"隐形"类账目，判据是**这条守卫现在会拒绝什么**，不是"我改了正则"。
'''
dec_new = dec.rstrip('\n') + SEC_DEC

SEC_BL = u'''

## R238 补记（250 结案：定义行从「只认标题」扩成「标题 ∪ 粗体」，两半各自配证人 / 新开 269）

**结案（250）**：选了 250 里写的**选项②**（把 `DEC_DEF` 扩成"标题 ∪ 粗体定义行"，配正 / 负两格），
没选①（把 28 条粗体决定升成三级标题）—— 升标题会撞上 `test_decision_numbers_have_no_gaps` 对更早空洞的点名风险，
而且那是**改台账迁就守卫**，不是让守卫看见台账。
现场数字（本轮实测）：标题形 201 条 / 最大 D-194，粗体形 28 条 / 最大 D-222，零重叠，并集 D-000…D-222 无空洞。
落盘的东西：`DEC_DEF`（一支正则两种形状）+ `DEC_DEF_HEADING_ONLY`（老字面，只当对照）+ `BOLD_DEF`、
`ids_from()` / `cited_missing()`（单位归一）、`strip_definition()`（认两种形状的正对照抹除），
新表 `BoldDefinitionLineTests` 五格，变异表 `.scratch/motion-audit-2/mutate_r238.py` 两刀 M793 / M794
⇒ `R238_MUTATE 刀=2 CAUGHT=2 ESCAPED=0 NOT_RUN=0 抓错格=0 RESTORE_CLEAN=yes`。
该判据文件从 11 格长到 16 格；本机电池 `Ran 423 tests`、汇总行 `OK (skipped=2)`。
**250 没结案的那一半**：runner 上这一卷电池认不认这两种形状 —— 本笔 CI 未读，而它与 268 的 runner 验收挂的是同一批跑，
读的时候一起读；编译红没恢复之前，那几朵下游红一律不许当产品读数。

**269. R238 手工跑 `mutate_needle_precheck.py` 读到 `bad=5`（含 `mutate_r229` 的 M768 命中=0），而同一天本机电池 423 条全绿 ⇒ 这一格要么不在电池里、要么在但不拦（新开）**

现场：预检自己打的收尾行是 `NEEDLE_PRECHECK tables=68 covered=53 arms=191 bad=5`，另有「覆盖不全：那几支的 needle 藏在
lambda 里」那句免责；它当时的**退出码我没记**，而电池整卷 OK ⇒ 至少"红名册不为零"这件事没有把电池弄红。
两种成因、修法相反：① 预检根本不在电池的清单里（那要接线，并配"没接新通道时旧的红照旧红"的正对照）；
② 它在但只印不拦（那要加闸门，并把"允许历史死针"做成显式名册，不许放宽成沉默 —— R108：只印不拦的读数等于没读数）。
下一轮顺序：先分辨是哪一种（看 workflow 正文里到底调没调这支、以及 `scripts/tests` 里有没有对应守卫），再决定接哪一半；
死针本身（M768）要按"命中=0 的两种成因"分辨：早年被源码改动摘掉，还是此刻正有一支表把它注入着。
不许做的事：为了让 `bad=0` 而清名册、删那支表，或把预检放宽。
'''
bl_new = bl.rstrip('\n') + SEC_BL

SEC_CH = u'''### 判据与尺：台账编号守卫的「定义行」从只认标题扩成「标题 ∪ 粗体定义行」（R238 / U-765…U-768 / D-223 · 产品 0 文件，画面一字未动）

- `scripts/tests/test_ledger_ids.py` 过去只把二/三级标题当决定正文，而 R200 以后的决定按台账既有形状写成粗体
  ⇒ 最近 28 条决定对"被引用却没正文"这条守卫**完全隐形**（标题形最大只到 D-194，粗体形到 D-222；BACKLOG 250，R224 曾红过一次）。
  本轮按 250 的选项②扩成两种形状（仍是**一支**正则），并按要求补齐正 / 负两格对照；该文件从 11 格长到 16 格。
- 两把变异刀各摘掉一半：M793 摘粗体 ⇒ 两态对照必须红；M794 把 `strip_definition` 退回只认标题形 ⇒
  "抹掉粗体定义行"那格必须红。M794 第一版期望写在「被引用且编号最大」那条正对照上，跑回来是 ESCAPED ——
  因为 victim 此刻是标题形；据此补了一格不依赖台账现状的证人，两刀才各自抓到各自该抓的格。
- 本轮**产品 0 文件**：不换装、不重捕帧、没重跑 `swift build` 与全量 `swift test`（Swift 侧未变），看图腿记 NOT-RUN；
  runner 上这一卷电池认不认两种形状，与 268 的 runner 验收一起待读。另新开 269（预检 `bad=5` 与电池的关系要先分辨成因）。

'''
lines = ch.splitlines(True)
hits = [i for i, ln in enumerate(lines) if ln.strip() == u'## [Unreleased]']
assert len(hits) == 1, 'CHANGELOG 里 [Unreleased] 标题数=' + str(len(hits)) + '（要恰好 1）'
lines.insert(hits[0] + 1, u'\n' + SEC_CH)
ch_new = u''.join(lines)
assert len([ln for ln in ch_new.splitlines() if ln.strip() == u'## [Unreleased]']) == 1, '插坏了：标题行不唯一'

SEC_ST = u'''
## R238 状态（第 237 轮 / Round 235 · 2026-10-20）

最后更新：2026-10-20 08:50（本地 · R238 / 第 237 轮 / Round 235）

**这一轮在做什么**：把 BACKLOG 250 结掉 —— 台账编号守卫的"定义行"只认标题，而 R200 之后的决定写成粗体，
于是最近 28 条对"被引用却没正文"隐形（标题形最大只到 D-194，粗体形到 D-222）。扩成「标题 ∪ 粗体」一支正则
+ 两态对照 + 老形状子集格 + 现有粗体条负格 + 粗体抹除证人，两刀 M793 / M794 各摘一半。
**产品 0 文件、画面一字未动**（动效的账继续欠着，这一维仍然拖总分）。

**现读计数器**：脚本电池 `Ran 423 tests` / `OK (skipped=2)`；台账 U 到 U-768、D 到 D-223、BACKLOG 到 269、刀到 M794；
帧 162 张在 `/tmp/shots_r236`（本轮没重捕）；曲线 R235=88。判据文件 `test_ledger_ids` 从 11 格长到 16 格；
全量 `swift test` 本轮**没重跑**（Swift 侧未变，上一笔 7b7495d 是 `Executed 915 / 44 skipped / 0 failures`）。

**下一轮（R239 / 第 238 轮 / Round 236）的靶**
⓪ **本笔与上一笔的 CI 都还没读**：`RUN=39347522293 sha=7b7495d status=in_progress conclusion=`（空）。
   先 `python3 scripts/ci_read.py latest` 现拿 run↔commit 成对（别轮询），要验三件事：STEP[4] 有没有转绿、
   `SEAM_READER_ISOLATION` 在 runner 上打的那一行、以及**电池那一卷认不认粗体定义行**（250 的 runner 半）。
   编译没恢复之前，STEP[15]/[17]/[18]/[19] 那几朵红一律不许当成产品读数。
① 249（R225 亮档反馈梯的 runner 复验）与 263 —— 都要等 ⓪ 把那朵编译红摘掉才谈得上。
② 268 的 runner 半（本机绿 ≠ runner 绿，D-222 那条规矩）。
③ **回到画面**：251（三处共用 `VisualFill.hover` 的位点 —— 段按钮 / 玻璃圆钮 / DetailView：先各补两档帧，
   再按 R225 的形状各判一次，最后每处一刀；不许在没有帧的位点上先改数值）。
④ 269（预检 `bad=5` 与电池的关系要先分辨成因）、267、260、262、258 第三处、254→255→248、243、227③、222、215、201/202、207、240；250 与 253 已结。
⑤ 需要用户真机或授权的：220 路 A（要授权改全局 `AppleKeyboardUIMode`）、228②、265。

**核心欠账没变**：阶段二"足够华丽 / 合理 / 原生"那一句仍未达成 —— 产品动效面连续多轮 0 改动，七维曲线长期在 90 以下，
主要拖在「产品面推进」与「真实视觉审查」两维。下一轮把力气搬回画面：从 ③ 挑一处，先补两档帧 → 判 → 加刀 → 真操作一遍。
'''
m_st = re.search(u'(?m)^# .*\\n', st)
assert m_st, 'STATE 里没有一级标题'
st_new = st[:m_st.end()] + SEC_ST + u'\n' + st[m_st.end():]

fr_new = fr.replace(u'U-31 … U-764', u'U-31 … U-768', 1)
assert fr_new != fr, 'FINAL_REPORT 的 U 格锚点没命中'
fr_new = re.sub(u'R9–R234，233 轮自评', u'R9–R235，234 轮自评', fr_new, count=1)
assert re.search(u'R9–R235，234 轮自评', fr_new), 'FINAL_REPORT 标题格锚点没命中'

heads = u'\n'.join(re.findall(u'(?m)^## (?:第 \\d+ 轮|Round \\d+) ·.*$', it_new + u'\n' + ui_new))
cited = set(u'D-' + n for n in re.findall(u'\\bD-(\\d{3})\\b', heads))
defined = set()
for mm in re.finditer(u'(?m)^(?:#{2,3} (D-\\d{3})\\b|\\*\\*(D-\\d{3})（)', dec_new):
    defined.add(mm.group(1) or mm.group(2))
assert cited - defined == set(), u'引用了却没正文：' + str(sorted(cited - defined)) + u' ⇒ 拒绝写盘'
assert u'D-223' in defined, u'新决定没落进定义集 ⇒ 本轮扩的正则白做'

for p, t in [(UI, ui_new), (IT, it_new), (DEC, dec_new), (BL, bl_new), (CH, ch_new), (ST, st_new), (FR, fr_new)]:
    wr(p, t)
wr('.scratch/motion-audit-2/r238_labels.json',
   json.dumps({'labels': LABELS, 'scores': SCORES, 'total': TOTAL, 'max': MAXTOT, 'round': 'R238'},
              ensure_ascii=False, indent=1))
print(u'LEDGERS_R238 写了 7 本：' + u' / '.join([UI, IT, DEC, BL, CH, ST, FR]))
print(u'自评行标签：' + u' | '.join(LABELS) + u' / 分数 ' + str(SCORES) + u' = ' + str(TOTAL) + u'/' + str(MAXTOT))

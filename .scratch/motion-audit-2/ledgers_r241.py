#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R241（第 240 轮 / Round 238）七本账落盘：尺的判据卷进电池。

所有数字**从台账现取**（271 那笔的教训：轮次标签与编号不许手抄）：
  U 的上界来自 AGENT_UI_AUDIT 的 `^- **U-xxx`，D 来自 DECISIONS 的定义形状，
  BACKLOG 的新号来自 `ITEM` 形状的最大值，轮次号来自 STATE 第一行 `最后更新` 的 R/第 N 轮。
写盘是事务性的：先在内存里造好七份文本并逐条断言（锚点整行相等、原行不丢、区间与定义行吻合），
任何一条断言红 ⇒ 一个字都不落盘。
"""
# -*- coding: utf-8 -*-
import io, os, re, sys

ROOT = '/Users/wangziyi/Codex_Project0'
UI = os.path.join(ROOT, 'AGENT_UI_AUDIT.md')
IT = os.path.join(ROOT, 'AGENT_VISUAL_ITERATION.md')
DEC = os.path.join(ROOT, 'AGENT_DECISIONS.md')
BK = os.path.join(ROOT, 'AGENT_BACKLOG.md')
CL = os.path.join(ROOT, 'CHANGELOG.md')
ST = os.path.join(ROOT, 'AGENT_STATE.md')
FR = os.path.join(ROOT, 'AGENT_FINAL_REPORT.md')

R, ROUND, RN = 241, 240, 238
UN = ['U-777', 'U-778', 'U-779']
DN = 'D-227'
BN = ['274', '275']
CLOSED = '273'


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
d_ids = [int((m[0] or m[1]).replace('D-', '')) for m in re.findall(r'^(?:#{2,3} (D-\d{3})\b|\*\*(D-\d{3})（)', d_txt, re.M)]
bk_txt = read(BK)
b_ids = [int(x) for x in re.findall(r'^(?:\*\*)?(\d{3})\. ', bk_txt, re.M)]
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
    u'## 第 %d 轮（R%d / Round %d · 2026-10-20）：尺的判据卷第一次进了电池 —— 两个口径各配一把刀，闸门两向都有证人（%s…%s / %s · %s 结案、新开 %s/%s）'
    % (ROUND, R, RN, UN[0], UN[2], DN, CLOSED, BN[0], BN[1]),
    u'',
    u'本轮次对照：与 R240（尺在仓库里、但只有它自己印的数）相比，本轮把「这把尺坏不坏」变成会红的判据卷 `scripts/tests/test_hover_two_state_diff.py`（16 格：11 格纯函数 / 5 格走 CLI 子进程量闸门），并给三句话各配一把刀。产品 0 文件、画面一字未动。',
    u'',
    u'- **%s：两口径第一次钉在同一份合成帧上，期望值来自手算而不是尺的输出。** 2×5 的整块亮档 ⇒ `changed=10 / share=10.0 / band_mean=per_pixel=2.17`（(80/255+0.05)/(30/255+0.05)=0.3637254902/0.1676470588=2.16959）；同一尺寸里只让一行两端各变一颗 ⇒ 包围盒 (0,5,10,6) 含 10 颗而真变只有 2 颗 ⇒ `band_mean=1.234`（带内均值 (2×80+8×30)/10=40）而 `per_pixel=2.17`。**两数相差 0.94 才是这一格真正的承重**：R239 那次差点改 `VisualFill.hover`，错的就是拿 1.2 那一档去对历史账里 1.16 那一档（同数不同估计量）。' % UN[0],
    u'- **%s：真帧卷在通道在场时 16/16 全跑，配对读数原样复现 R240。** `CLIPBOARD_HISTORY_UI_SHOTS=/tmp/shots_r239`（162 帧先 `ls` 数过）⇒ `Ran 16 tests / OK`、`真帧配对=6 无静置态=14`；通道缺席那一跑是 `OK (skipped=1)` 且 skip 文本点名 `CLIPBOARD_HISTORY_UI_SHOTS`。覆盖率地板按机器走环境变量 `HOVER_DIFF_MIN_PAIRS`（本机登记 6），**CI 上故意不设**：runner 的帧数与本机不同，共用一个地板会造出跨机的假红（%s）。' % (UN[1], DN),
    u'- **%s：M796 的第一版 needle 命中 3 次，被表自己的 count==1 拦下。** 锚点写的是 `for n in changed]`，而这一串在尺里出现三处（`changed = [...]`、`for n in changed]` 两处别行）⇒ 表直接 NOT_RUN 而不是把刀插错地方。这是「锚点恰好命中一次」这条规矩第二次救场（第一次是 R238 的 M794 期望写错）。锚点换成 `sum(pb[n]) / 3.0) for n in changed]` 之后 CAUGHT。' % UN[2],
    u'',
    u'读数腿：RUN（`/tmp/r241_ruler_tests.log`、`/tmp/r241_ruler_real.log`）。变异腿：RUN（`/tmp/r241_mutate.log`）—— M795 门槛 4→100 ⇒ CAUGHT（5 格红，含两向证人里「干净一跑必须绿」那一格）；M796 稀释吞进 `per_pixel` ⇒ CAUGHT（2 格红，正是两口径那两格）；M797 摘掉缺 `--control` 的 `rc = 1` ⇒ CAUGHT（只红那 1 格，说明闸门与读数是分开的两件事）。三把 RESTORE_CLEAN（逐字节还原并复核）。',
    u'眼睛腿：NOT-RUN —— 本轮产品 0 文件、帧与 R240 同一批（重捕只会得到同一批帧），没有新的画面判断要做；这不是「看过」，账里按缺席记（R154 那一族：环境/未做/不存在三种成因，这里成因是「本轮没有可看的新技术画面」）。',
    u'换装本机：NOT-RUN —— 没有新的产品二进制可装（Swift 文件 0 个 ⇒ `swift build` / 全量 Swift 卷同样跳过并记账，不许记成 0 告警通过）。',
    u'未做（逐条）：① 尺没挂进 CI 的抓帧那一步（新开 %s）；② runner 那一格的地板数还没有（新开 %s：CI 上 `HOVER_DIFF_MIN_PAIRS` 该登记几，要等 runner 自己打印一次配对数，不许猜）；③ CI 六笔未读（`39352533580` 是本笔、仍 `in_progress/conclusion=空` ⇒ 只能说未读）；④ `DetailView.swift:609` 第三处仍无两态帧（251 未结）。' % (BN[0], BN[1]),
    u'',
]
lines = ui_old.split('\n')
assert len([l for l in lines if l.startswith(u'## 第 %d 轮' % (ROUND - 1))]) == 1, '上一轮标题锚点不唯一'
new_ui = '\n'.join(insert_before(lines, lambda l: l.startswith(u'## 第 %d 轮' % (ROUND - 1)), sec))
missing = [l for l in lines if l.strip() and l not in new_ui]
assert not missing, '旧行丢了（本轮只该插入，不该改任何原行）：%s' % missing[:3]
assert new_ui.count(u'## 第 %d 轮' % ROUND) == 1, '新节标题不唯一'
assert len(re.findall(r'^- \*\*U-(\d{3})', new_ui, re.M)) == len(u_ids) + 3, 'U 定义行少了 3 条'
new_title = [l for l in new_ui.split('\n') if l.startswith(u'## 第 %d 轮' % ROUND)][0]
assert u'%s…%s' % (UN[0], UN[2]) in new_title and (u'R%d' % R) in new_title, '新标题的 U 区间或 R 标签不对'

# ── 2. AGENT_VISUAL_ITERATION.md：升序 ⇒ 只追加到文件尾 ──────────────────────
it_old = read(IT)
dims = [u'真实视觉审查', u'判据有效性', u'假绿防御', u'产品面推进', u'台账一致性', u'交付诚实性', u'可复核性']
scores = [11, 14, 14, 8, 13, 14, 14]
assert sum(scores) == 88
it_rows = u''.join(u'| %s | %d/15 |\n' % (d, s) for d, s in zip(dims, scores))
it_title = u'\n## Round %d · 尺的判据卷进电池（R%d / 第 %d 轮）：三句话各配一把刀，闸门两向都有证人 / %s / BACKLOG %s 结案、新开 %s/%s · 产品 0 文件\n\n' % (RN, R, ROUND, DN, CLOSED, BN[0], BN[1])
it_lead = u'本轮次对照：与 R240（尺在仓库里、只有它自己印的数）相比，本轮量的是「这把尺坏不坏」。做了什么：写 scripts/tests/test_hover_two_state_diff.py 共 16 格（11 格纯函数 + 5 格走 CLI 量闸门）→ 三把刀 M795/M796/M797 → 新表 mutate_r241.py 登记进预检名册 → 台账。\n'
it_legs = u'看图腿：读数腿 RUN（合成帧 Ran 16 OK (skipped=1)；真帧 162 张在场时 Ran 16 OK、真帧配对=6 无静置态=14，与 R240 同值）；眼睛腿 NOT-RUN（产品 0 文件、帧是同一批，本轮没有新的画面判断要做）。\n'
it_hdr = u'七维度自评：\n| 维度 | 分/满分 |\n'
it_reason = u'各维理由：真实视觉审查 11 —— 眼睛腿本轮没跑（0 产品改动就没有新画面可判，但分数照扣，不许把没做记成没缺陷）；判据有效性 14 —— 两口径钉在同一份合成帧上、期望值由手算推出（2.17 与 1.234 与尺的读数逐位一致），扣 1 是尺仍未挂进 CI；假绿防御 14 —— 三把刀分别摘门槛、摘口径分离、摘闸门，且「干净一跑必须 rc=0」与「空名单必须 rc=1」两向都有证人；产品面推进 8 —— 连续又一轮 0 产品文件，核心欠账（动效本体、251 第三处两态帧）未变；台账一致性 13 —— 七本账同一脚本事务性写盘、编号全部现取；交付诚实性 14 —— 未做四项逐条写成因；可复核性 14 —— 判据卷进了电池，任何人跑 discover 就能重跑这把尺，命令不再要手搓。合计 **88**/105。\n'
it_sec = it_title + it_lead + it_legs + it_hdr + it_rows + it_reason
new_it = it_old + it_sec
assert new_it.count(u'## Round %d ·' % RN) == 1 and new_it.count(u'合计 **88**/105') == 1
assert len(re.findall(r'^\| (?:%s) \| \d+/15 \|' % u'|'.join(dims), new_it.split(u'## Round %d ·' % RN)[-1], re.M)) == 7, '自评表不是 7 行'

# ── 3. AGENT_DECISIONS.md：追加粗体定义 ─────────────────────────────────────
dec_line = (u'**%s（R%d）：同一把尺的覆盖率地板按机器各自登记，跨机共用一个地板等于造假红 —— '
            u'本机 `HOVER_DIFF_MIN_PAIRS=6` 写进账，CI 上先不设默认，等 runner 自己打印一次配对数再登记。** '
            u'理由：判据卷的 11 格纯函数在任何机器上都同值（合成帧是我造的），可以钉死；'
            u'而「配到几对」取决于那台机器有没有帧、有几个 `-hover` 位点，'
            u'把本机的 6 压到 runner 上，红了说的不是产品。这一条与 D-038（要红就绑单调量）、'
            u'D-226（覆盖率要有一根能被打红的地板）是同族：地板必须有，但地板属于量它的那台机器。\n' % (DN, R))
new_dec = d_txt.rstrip('\n') + '\n\n' + dec_line
assert new_dec.count(u'**%s（' % DN) == 1

# ── 4. AGENT_BACKLOG.md：273 结案追记 + 新开 274/275 ─────────────────────────
bk_lines = bk_txt.split('\n')
i273 = [j for j, l in enumerate(bk_lines) if l.startswith(u'**%s. ' % CLOSED)]
assert len(i273) == 1, '273 那条不唯一：%s' % i273
close_note = (u'  结案追记（R%d）：尺接进 `scripts/tests/test_hover_two_state_diff.py`（16 格，已进电池）'
              u'—— 合成帧验两口径（2.17 / 1.234，期望手算）、缺 `--control` 必须红、空名单必须红而非 skip、'
              u'帧尺寸不符必须报缺帧、`--min-pairs` 地板两向证人；"不给真帧就 skip 且点名通道"也落地了'
              u'（skip 文本写 `CLIPBOARD_HISTORY_UI_SHOTS=`）。**CI 那一步仍未接**，拆成 %s/%s 继续追。' % (R, BN[0], BN[1]))
bk_lines = bk_lines[:i273[0] + 1] + [close_note] + bk_lines[i273[0] + 1:]
new_items = [
    u'',
    u'**%s. 尺挂进 CI 的抓帧那一步（runner 上帧目录缺席时这一格必须走有名字的 skip，不许静默通过），'
    u'并给那一格的退出码接上 grep（R109：新读数要接在它被打印的那一步上）（R%d 新开）**' % (BN[0], R),
    u'**%s. `HOVER_DIFF_MIN_PAIRS` 在 runner 上该登记几：先让 CI 跑一次并把配对数写进豁免名册的机器键，'
    u'再决定要不要设地板（D-227：地板属于量它的那台机器，本机数不许外推）（R%d 新开）**' % (BN[1], R),
]
new_bk = '\n'.join(bk_lines).rstrip('\n') + '\n' + '\n'.join(new_items) + '\n'
assert re.findall(r'^(?:\*\*)?(\d{3})\. ', new_bk, re.M) == [str(x) for x in b_ids] + BN, 'BACKLOG 形状/编号变了'

# ── 5. CHANGELOG.md：`## [Unreleased]` 之下插一节（标题必须含 R241）──────────
cl_old = read(CL)
cl_lines = cl_old.split('\n')
idx = [j for j, l in enumerate(cl_lines) if l.strip() == u'## [Unreleased]']
assert len(idx) == 1, 'Unreleased 标题不是恰好一个：%d' % len(idx)
cl_sec = [
    u'',
    u'### Changed（R%d / 第 %d 轮 / Round %d · 两态差尺的判据卷进电池：两个口径各一把刀，闸门两向证人）' % (R, ROUND, RN),
    u'',
    u'- `scripts/tests/test_hover_two_state_diff.py`（16 格）：合成帧把 `band_mean` 与 `per_pixel` 钉成两个可复查的数（整带都变 ⇒ 2.17=2.17；带内只有 2/10 颗变 ⇒ 1.234 ≠ 2.17），期望值由手算推出；闸门用 CLI 子进程量（无通道 exit 2、空名单 exit 1 且不打「退出=0」、缺 `--control` exit 1、`--min-pairs` 高于实际配对 exit 1，而同一批帧在地板之内必须 exit 0）。',
    u'- 尺的覆盖率地板改由环境变量 `HOVER_DIFF_MIN_PAIRS` 按机器登记（本机 6，R240 实测）；真帧那一格在通道缺席时是有名字的 skip。',
    u'- 三把变异刀 M795/M796/M797（表 `.scratch/motion-audit-2/mutate_r241.py`）：门槛、口径分离、闸门各摘一半，三把 CAUGHT、三把 RESTORE_CLEAN。',
]
new_cl = '\n'.join(cl_lines[:idx[0] + 1] + cl_sec + cl_lines[idx[0] + 1:])
assert len([l for l in new_cl.split('\n') if l.strip() == u'## [Unreleased]']) == 1, 'Unreleased 变成两个'
assert new_cl.count(u'R%d' % R) >= 1 and (u'### Changed（R%d' % R) in new_cl

# ── 6. AGENT_STATE.md：新块必须是最靠前的那一行「最后更新」───────────────────
head_new = u'## R%d 状态（第 %d 轮 / Round %d · 2026-10-20）' % (R, ROUND, RN)
head_old = u'## R%d 状态（第 %d 轮 / Round %d · 2026-10-20）' % (prev_r, prev_round, RN - 1)
blk = [
    u'',
    u'最后更新：2026-10-20 01:30（本地 · R%d / 第 %d 轮 / Round %d）：**两态差尺的判据卷进电池 —— 两个口径各配一把刀，闸门两向都有证人**（%s…%s · %s · %s 结案、新开 %s/%s · 产品 0 文件，画面一字未动）' % (R, ROUND, RN, UN[0], UN[1], DN, CLOSED, BN[0], BN[1]),
    u'',
    u'**本轮落地**：`scripts/tests/test_hover_two_state_diff.py` 16 格（合成帧两口径 2.17/1.234 手算对账、CLI 四道闸门两向证人、配对两种写法、真帧地板按机器 `HOVER_DIFF_MIN_PAIRS`）；真帧卷 `Ran 16 OK`（配对 6/无静置态 14，与 R240 同值）；M795/M796/M797 三把全 CAUGHT、RESTORE_CLEAN；新表 `mutate_r241.py`。',
    u'',
    u'**下一轮（R%d / 第 %d 轮 / Round %d）的靶**：' % (R + 1, ROUND + 1, RN + 1),
    u'⓪ 读 CI：`python3 scripts/ci_read.py latest` 现拿成对（别轮询）。未读六笔：`39352533580↔070cbab`（本笔，取数时仍 `in_progress`、`conclusion` 空 ⇒ 只能说未读）、`39352046610↔5252c05`、`39351035433↔6927880`、`39350006461↔3e90ab4`、`39347522293↔7b7495d`、`本笔↔?`；要验 STEP[4] 是否转绿、`SEAM_READER_ISOLATION` 那一行、电池认不认两种形状（250/270 的 runner 半）、以及新判据卷在 runner 上是不是「skip 且点名通道」。编译红没恢复前下游红不当产品读数。',
    u'① 做 274/275：把尺挂进 CI 抓帧那一步（接在它被打印的那一步的 grep 上），并拿 runner 自己打印的配对数登记 `HOVER_DIFF_MIN_PAIRS`。',
    u'② 251 第三处（`DetailView.swift:609`）补两态帧 —— 只有先有静置帧，尺才量得动；14 个无静置态的名字尺会逐条点名（不许把它们当成「没问题」）。',
    u'③ 动效本体仍欠（连续 0 产品文件）：从 173/清账表里挑一个**两态读数已经能定线**的位点做真改动，别再凭未定线的尺改档。',
    u'④ 仍开 249 / 263 / 268 runner 半 / 269 / 267 / 260 / 262 / 258 第三处 / 254→255→248 / 243 / 227③ / 222 / 215 / 201 / 202 / 207 / 240 / 251；用户闸门 220 路 A、228②、265。',
    u'',
]
st_lines = st_txt.split('\n')
j = [k for k, l in enumerate(st_lines) if l.startswith(u'## R') and u'状态（' in l][0]
assert st_lines[j] != head_new, 'STATE 顶层标题已经是本轮'
st_lines[j] = head_new
new_st = '\n'.join(st_lines[:j + 1] + blk[1:] + st_lines[j + 1:])
mm = re.search(r'最后更新：[^\n]*?R(\d+) / 第 (\d+) 轮', new_st)
assert (int(mm.group(1)), int(mm.group(2))) == (R, ROUND), 'STATE 第一行最后更新不是本轮：%s' % (mm.groups(),)
assert all(l in new_st for l in st_lines if l.startswith('## 第') or l.startswith('**下一轮')), 'STATE 旧行丢了'

# ── 7. AGENT_FINAL_REPORT.md：只改计数器 ────────────────────────────────────
fr_old = read(FR)
new_fr = fr_old.replace(u'U-31 … U-%d' % max(u_ids), u'U-31 … U-%s' % UN[-1][2:])
old_m = re.search(r'变异臂累计到 \*\*(M\d+)\*\*', new_fr)
if old_m:
    new_fr = new_fr.replace(old_m.group(1), 'M797')
r_rep = re.search(r'R9–R(\d+)，(\d+) 轮自评', new_fr)
if r_rep:
    new_fr = new_fr.replace(r_rep.group(0), u'R9–R%d，%d 轮自评' % (RN, RN))

print('LEDGERS_R241_FINAL_REPORT_U=%s' % ('CHANGED' if new_fr != fr_old else u'NOT-CHANGED（形状没匹配上，本轮不刷新 U 区间，明记不做）'))

# ── 写盘（全部断言通过之后）────────────────────────────────────────────────
for path, text in [(UI, new_ui), (IT, new_it), (DEC, new_dec), (BK, new_bk),
                   (CL, new_cl), (ST, new_st), (FR, new_fr)]:
    put(path, text)
print('LEDGERS_R241 七本落盘：UI(第 %d 轮)/IT(Round %d)/DEC(%s)/BK(%s,%s)/CL(R%d)/ST(R%d)/FR(U-%s)'
      % (ROUND, RN, DN, BN[0], BN[1], R, R, UN[-1][2:]))

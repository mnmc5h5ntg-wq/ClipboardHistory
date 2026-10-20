#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R247（第 246 轮 / Round 244）七本账落盘：CI 抓帧那一步的正文第一次有自己的判据卷，三把刀全 CAUGHT。

沿用 R246 的规矩：**不用 % 格式化**（R245 两次 arity 崩盘），数字硬写并断言与日志现读一致。
"""
import io, os, re

ROOT = '/Users/wangziyi/Codex_Project0'
UI = os.path.join(ROOT, 'AGENT_UI_AUDIT.md')
IT = os.path.join(ROOT, 'AGENT_VISUAL_ITERATION.md')
DEC = os.path.join(ROOT, 'AGENT_DECISIONS.md')
BK = os.path.join(ROOT, 'AGENT_BACKLOG.md')
CL = os.path.join(ROOT, 'CHANGELOG.md')
ST = os.path.join(ROOT, 'AGENT_STATE.md')
FR = os.path.join(ROOT, 'AGENT_FINAL_REPORT.md')
VERDICT = 'R247_MUTATE 刀=3 CAUGHT=3 ESCAPED=0 NOT_RUN=0 抓错格=0 RESTORE_CLEAN=yes'


def read(p):
    return io.open(p, encoding='utf-8').read()


def put(p, s):
    io.open(p, 'w', encoding='utf-8').write(s)


ui_old = read(UI)
u_ids = [int(x) for x in re.findall(r'^- \*\*U-(\d{3})', ui_old, re.M)]
d_ids = [int((m[0] or m[1]).replace('D-', '')) for m in
         re.findall(r'^(?:#{2,3} (D-\d{3})\b|\*\*(D-\d{3})（)', read(DEC), re.M)]
b_ids = [int(x) for x in re.findall(r'^(?:\*\*)?(\d{3})\. ', read(BK), re.M)]
st_txt = read(ST)
m = re.search(r'最后更新：[^\n]*?R(\d+) / 第 (\d+) 轮', st_txt)
assert max(u_ids) + 1 == 797, 'U 上界对不上'
assert max(d_ids) + 1 == 233, 'D 上界对不上'
assert max(b_ids) == 287, 'BACKLOG 上界对不上'
assert (int(m.group(1)), int(m.group(2))) == (246, 245), 'STATE 的轮次对不上'
assert max(int(x) for x in re.findall(r'^## 第 (\d+) 轮', ui_old, re.M)) == 245
live = [l for l in read('/tmp/r247_mutate2.log').split('\n') if l.startswith('R247_MUTATE')]
assert live == [VERDICT], '结论行与日志现读不同：%s' % live
wiring = read('/tmp/r247_mutate2.log')
assert '基线绿：kind=python' in wiring, '没有现读的基线绿行'

sec = [
    '## 第 246 轮（R247 / 第 246 轮 / Round 244 · 2026-10-20）：CI 抓帧那一步的正文有了自己的判据卷（6 格）+ 三把刀全 CAUGHT；274 结案（U-797…U-799 / D-233 · 274 结案、新开 288/289 · 产品 0 文件）',
    '',
    '本轮次对照：与 R246（把 274 的接线修好，但证人只有我手工抽出来的那一次 `/tmp/r246_step.sh`）相比，本轮把那条手工腿永久化成判据卷，并按仓库的硬规矩给它插刀。产品 0 文件、画面一字未动。',
    '',
    '- **U-797：`scripts/tests/test_ci_hover_wiring.py`（6 格）把 `ci.yml` 里那段 bash **抽出来、dedent、`bash -n`、再对着合成帧目录真跑**。** 三种缺席各自有证人：完整一对 ⇒ 退出 0 且 `HOVER_DIFF_CONTROL=` 恰好是那两颗（`-light` 那颗故意在场，上一版的 grep 会把它也吃进去）；缺 idle ⇒ 点名 `HOVER_DIFF_CONTROL_INCOMPLETE=1` 且非 0；缺 lit ⇒ 同样点名（两半各证一次，只证一边会被"另一半恒空"喂饱）；整目录没 png ⇒ 点名 `HOVER_DIFF_NOT_RUN=1` 而**这一步是绿的**（环境缺席 ≠ 缺陷）。另有两格管抽取本身：`bash -n` 过关 + 起点在 workflow 里恰好一处（两处就会抽到第一处而判的是另一处）。本机 `Ran 6 tests OK`。',
    '- **U-798：一把刀第一跑报的是 WRONG_CELL，而它比 CAUGHT 更值钱。** M808 想把闸门退回 R244 的「逗号切出两段」，预期只红"缺 idle"那一格；实跑红了**完整一对**那一格 ⇒ 说明旧写法有两个缺陷（空 IDLE + 非空 LIT 也会数出两段；而 `wc -l` 数的是换行数，`a,b` 只得 1 ⇒ 好接线在旧闸门下也恒红）。登记按实改：M808 的期望证人换成"完整一对必须绿"那一格，改完重跑 ⇒ `R247_MUTATE 刀=3 CAUGHT=3 ESCAPED=0 NOT_RUN=0 抓错格=0 RESTORE_CLEAN=yes`。这条同时把 274 结掉：修法不再只对我手工跑的那一次负责。',
    '- **U-799：那一步的 stdout 里漏非 UTF-8 字节（本轮实测），判据卷为此改成按字节收再 errors=replace。** 第一版用 `text=True`，在帧目录列完之后抛 `UnicodeDecodeError: 0xbc` ⇒ 崩溃的证人不是判据。改成 `stdout=PIPE` 收字节后六格全绿。**成因未归**（哪一个命令写的、是不是 `tee` 与 `ls` 的竞态，都还没量）⇒ 新开 289，不许因为"绕过它了"就当成已解释。执行器侧一并改进：`mutate_r247.sh` 的 kind 与 rel 都从 `arms_r247/manifest.tsv` 现取，所以本表（只有 python 臂）不再白跑一次 swift 基线。',
    '',
    '读数腿：RUN —— `Ran 6 tests OK`（判据卷）；`/tmp/r247_mutate2.log`（基线绿 + 三行刀 + 一行总结）。',
    '眼睛腿：NOT-RUN —— 产品 0 文件、无新帧（帧仍是 R239 那 162 张），没有新的画面判断要做；连续第四轮记 NOT-RUN。',
    '变异腿：RUN —— M808/M809/M810 全 CAUGHT、三把 RESTORE_CLEAN（逐字节还原并复核）；M808 的期望格按实改过一次，改前的 WRONG_CELL 读数留在 U-798 里。',
    'Swift 腿：NOT-RUN —— 本轮一行 Swift 都没改（只新增 python 判据与 `.github` 正文的引用），`swift build` / 全量卷 / 重捕帧 / 换装本机都没跑；最近的 Swift 侧读数仍是 R246 的 `Executed 2 tests, with 0 failures`。',
    '未做（逐条）：① 289（那一步 stdout 漏非 UTF-8 字节的成因）；② 288（其余 CI 步骤还没有"正文判据卷"，只有这一步有）；③ 287 的 runner 半 —— `HOVER_TWO_STATE_277` 的 runner 读数还没有，地板仍不判（D-232）；④ 284/286 未做（M798…M801 一颗没插、r169/r217/r229 的锚点腐烂未处置）；⑤ CI 两笔仍 `in_progress`（`39475884846↔550fb43`、`39474398455↔09a8763`）⇒ 只能说未读；⑥ 产品动效本体仍 0 文件。',
    '',
]
lines = ui_old.split('\n')
assert len([l for l in lines if l.startswith('## 第 245 轮')]) == 1, '上一轮标题锚点不唯一'
idx = [i for i, l in enumerate(lines) if l.startswith('## 第 245 轮')][0]
new_ui = '\n'.join(lines[:idx] + sec + lines[idx:])
missing = [l for l in lines if l.strip() and l not in new_ui]
assert not missing, '旧行丢了：%s' % missing[:3]
assert new_ui.count('## 第 246 轮') == 1
assert len(re.findall(r'^- \*\*U-(\d{3})', new_ui, re.M)) == len(u_ids) + 3, 'U 定义行少了 3 条'

dims = ['真实视觉审查', '判据有效性', '假绿防御', '产品面推进', '台账一致性', '交付诚实性', '可复核性']
scores = [11, 14, 15, 8, 13, 14, 14]
assert sum(scores) == 89
it_rows = ''.join(['| ' + d + ' | ' + str(s) + '/15 |\n' for d, s in zip(dims, scores)])
it_sec = ('\n## Round 244 · CI 抓帧那一步的正文有了自己的判据卷（6 格）+ 三把刀全 CAUGHT、274 结案（R247 / 第 246 轮）/ D-233 · 新开 288/289 · 产品 0 文件\n\n'
          + '本轮次对照：与 R246（手工抽正文跑通一次）相比，本轮把手工腿变成会红的判据卷，并给它插三把刀（闸门退回数逗号 / 选择退回名字含 idle-lit / 环境缺席改成红）。全部 CAUGHT。\n'
          + '看图腿：读数腿 RUN（`' + VERDICT + '`、判据卷 `Ran 6 OK`）；眼睛腿 NOT-RUN（0 产品改动、0 新帧）。\n'
          + '七维度自评：\n| 维度 | 分/满分 |\n' + it_rows
          + '各维理由：真实视觉审查 11 —— 眼睛腿连续第四轮没跑，照扣不豁免；'
            '判据有效性 14 —— 新六格把"接线"这件事变成能在本机被打红的对象，其中两格管抽取本身（抽错边界也算红）；'
            '假绿防御 15 —— 三把刀全 CAUGHT 且 M808 的 WRONG_CELL 被当成读数用（它暴露旧闸门连好接线也恒红），这是本表里本轮唯一满分的一格；'
            '产品面推进 8 —— 仍 0 产品文件；'
            '台账一致性 13 —— 七本一支脚本、不用百分号格式化、结论行断言与日志现读逐字相同；'
            '交付诚实性 14 —— 五条腿 + 六条未做逐条写成因，"绕过 UnicodeDecodeError"没写成已解释（新开 289）；'
            '可复核性 14 —— 判据卷进电池（任何人 discover 就能重跑这条手工腿）。合计 **89**/105。\n')
new_it = read(IT) + it_sec
assert new_it.count('## Round 244 ·') == 1 and new_it.split('## Round 244 ·')[-1].count('合计 **89**/105') == 1
assert len(re.findall(r'^\| (?:' + '|'.join(dims) + r') \| \d+/15 \|', new_it.split('## Round 244 ·')[-1], re.M)) == 7

dec_line = ('**D-233（R247）：CI 步骤正文的判据一律按字节收 stdout 再解码（errors=replace），不用 `text=True`；'
            '而"抽正文 + dedent + `bash -n` + 真跑合成对象"是 workflow 里任何一步可复用的判据形状。** '
            '理由：本轮实测那一步的 stdout 里漏非 UTF-8 字节（`0xbc`），`text=True` 直接抛 UnicodeDecodeError —— '
            '判据崩溃与判据通过长得不一样，但两者都不算读数（R90 那一族：通道事实要真跑一遍才知道）。'
            '另一半：改 CI 的 bash 时，唯一的本机复现通道就是把那段正文抽出来跑；这件事以前每次手工做，因此从来没有证人。'
            '与 D-232 同族但对象不同：那里管"换尺那一跑不定线"，这里管"给 CI 正文建判据的接法"。\n')
new_dec = read(DEC).rstrip('\n') + '\n\n' + dec_line
assert new_dec.count('**D-233（') == 1

bk_lines = read(BK).split('\n')
j = [i for i, l in enumerate(bk_lines) if l.startswith('**274. ')]
assert len(j) == 1, '274 那条不唯一'
note274 = ('  结案追记（R247）：runner 半也齐了 —— ① 配对按 (状态 × 色档) 各取一颗、闸门改成"两颗都非空"（R246）；'
           '② `scripts/tests/test_ci_hover_wiring.py` 6 格把那一步正文抽出来真跑（完整一对=0 / 缺 idle=点名红 / 缺 lit=点名红 / 空目录=点名绿 / `bash -n` / 起点恰好一处）；'
           '③ 三把刀 M808/M809/M810 全 CAUGHT（M808 的期望格按实改过一次：旧"数逗号"闸门在好接线下也恒红，因为 `wc -l` 数换行 ⇒ 两颗只得 1）。'
           '**遗留**：那一步 stdout 漏非 UTF-8 字节的成因未归 ⇒ 新开 289；其余 CI 步骤还没有同类判据卷 ⇒ 新开 288。')
bk_lines = bk_lines[:j[0] + 1] + [note274] + bk_lines[j[0] + 1:]
new_items = [
    '',
    '**288. 把"抽正文 + dedent + `bash -n` + 合成对象真跑"这把尺推广到其余 CI 步骤（现在只有 HOVER_DIFF 那一步有判据卷；'
    '捕获闸门、帧基线、`SEAM_READER_ISOLATION` 那几步的红仍只能在 runner 上第一次发现）（R247 新开）**',
    '**289. CI 抓帧那一步的 stdout 漏非 UTF-8 字节（本轮实测 `UnicodeDecodeError 0xbc`，位置在帧目录列完之后）：判据卷已按 D-233 改成按字节收，'
    '但成因未归 —— 要分辨是 `tee /tmp/hoverdiff.log`、`ls` 与帧名里的非 ASCII、还是尺自己 print 了字节；不许把"绕过解码"记成"已解释"（R247 新开）**',
]
new_bk = '\n'.join(bk_lines).rstrip('\n') + '\n' + '\n'.join(new_items) + '\n'
assert re.findall(r'^(?:\*\*)?(\d{3})\. ', new_bk, re.M) == [str(x) for x in b_ids] + ['288', '289'], 'BACKLOG 编号/形状变了'

cl_lines = read(CL).split('\n')
idx = [i for i, l in enumerate(cl_lines) if l.strip() == '## [Unreleased]']
assert len(idx) == 1
cl_sec = [
    '',
    '### Changed（R247 / 第 246 轮 / Round 244 · CI 抓帧那一步的正文进判据卷：六格 + 三把刀，274 结案）',
    '',
    '- `scripts/tests/test_ci_hover_wiring.py`（6 格，已进电池）：从 `.github/workflows/ci.yml` 抽出抓帧那一步的 bash、dedent、`bash -n`，再对着合成帧目录真跑。四种处置各有证人：完整一对 ⇒ 退出 0 且正对照恰好那两颗（另一色档那颗故意在场）；缺 idle / 缺 lit ⇒ 点名 `HOVER_DIFF_CONTROL_INCOMPLETE=1` 且非 0；整目录无 png ⇒ 点名 `HOVER_DIFF_NOT_RUN=1` 而退出 0。另两格管抽取本身（语法、起点唯一）。',
    '- 按 D-233 收字节：这一步的 stdout 漏非 UTF-8 字节（实测 `0xbc`），判据改成 `stdout=PIPE` + `errors=replace`；成因未归，新开 289。',
    '- 新执行器形状：`mutate_r247.sh` 的 kind 与 rel 从 `arms_r247/manifest.tsv` 现取（只有 python 臂的表不再白跑 swift 基线）；`mutate_r247.py` 是影子登记表，已进预检名册。三把刀 `R247_MUTATE 刀=3 CAUGHT=3 ESCAPED=0 NOT_RUN=0 抓错格=0 RESTORE_CLEAN=yes`。',
    '- M808 的期望证人按实改登记（第一跑是 WRONG_CELL）：旧"逗号切两段"闸门在好接线下也恒红 —— `wc -l` 数换行数，`a,b` 只得 1。这条读数把 274 的修法从"比旧写法好"升级成"旧写法本来就是错的"。',
    '- 产品侧 0 文件；眼睛腿与 Swift 腿 NOT-RUN（一行 Swift 都没改）。',
]
new_cl = '\n'.join(cl_lines[:idx[0] + 1] + cl_sec + cl_lines[idx[0] + 1:])
assert len([l for l in new_cl.split('\n') if l.strip() == '## [Unreleased]']) == 1

st_lines = st_txt.split('\n')
j = [i for i, l in enumerate(st_lines) if l.startswith('## R') and '状态（' in l][0]
st_lines[j] = '## R247 状态（第 246 轮 / Round 244 · 2026-10-20）'
blk = [
    '',
    '最后更新：2026-10-20 12:10（本地 · R247 / 第 246 轮 / Round 244）：**CI 抓帧那一步的正文有了自己的判据卷（6 格）+ 三把刀全 CAUGHT、274 结案**（U-797…U-799 · D-233 · 新开 288/289 · 产品 0 文件，眼睛腿与 Swift 腿 NOT-RUN）',
    '',
    '**本轮落地**：`scripts/tests/test_ci_hover_wiring.py`（`Ran 6 OK`，已进电池）；`arms_r247/manifest.tsv` + `mutate_r247.sh`（kind/rel 从 manifest 现取）+ `mutate_r247.py`（影子表，进名册）；`R247_MUTATE 刀=3 CAUGHT=3 ESCAPED=0 NOT_RUN=0 抓错格=0 RESTORE_CLEAN=yes`；D-233（CI 正文判据按字节收 + 抽正文真跑是可复用形状）。',
    '',
    '**下一轮（R248 / 第 247 轮 / Round 245）的靶**：',
    '⓪ 读 CI：`python3 scripts/ci_read.py latest` 现拿成对。未读：`39475884846↔550fb43`（R246）、`39474398455↔09a8763`（R245）—— 两笔取数时都仍 `in_progress`、`conclusion` 空 ⇒ 只能说未读；本笔 push 之后现取再登记，账里不留问号 commit。要读的还是 287 那三件事：runner 自己印的 `HOVER_TWO_STATE_277 … 两态变化=X/Y 占比=Z`（定线用，D-232）、`HOVER_DIFF_CONTROL=` 是否只剩两颗（274 的复验）、`SOURCES_CELL_HISTORY … 处置=` 是否从 skip 翻成 judge（278 的复验）。',
    '① 做 284/286：补跑 M798…M801（280 的机制到这才允许升级成已命名）；处置 r169/r217/r229 的锚点腐烂（换锚重跑并登记新 CAUGHT，或显式退役那张表并摘出名册）。',
    '② 做 288：把"抽正文真跑"推广到捕获闸门与帧基线那两步 —— 那是产品读数真正进来的地方，现在它们的红只能在 runner 上第一次发现。',
    '③ 动效本体：产品文件连续多轮 0，自评里最弱的两格就是"真实视觉审查 + 产品面推进"。能落产品改动的靶要先补两态帧（`DetailView.swift:609` 与 14 个无静置态的名字）；不许为了破 0 纪录加动效。',
    '④ 仍开 249 / 263 / 268 runner 半 / 269 / 267 / 260 / 262 / 258 第三处 / 254→255→248 / 243 / 227③ / 222 / 215 / 201 / 202 / 207 / 240 / 251 / 275 / 279 / 281 / 282 / 284 / 285 / 286 / 287 / 288 / 289；用户闸门 220 路 A、228②、265。',
    '',
]
new_st = '\n'.join(st_lines[:j + 1] + blk[1:] + st_lines[j + 1:])
mm = re.search(r'最后更新：[^\n]*?R(\d+) / 第 (\d+) 轮', new_st)
assert (int(mm.group(1)), int(mm.group(2))) == (247, 246), 'STATE 第一行不是本轮'
assert '本笔=`?' not in new_st

fr_old = read(FR)
new_fr = fr_old.replace('U-31 … U-796', 'U-31 … U-799')
r_rep = re.search(r'R9–R(\d+)，(\d+) 轮自评', new_fr)
if r_rep:
    new_fr = new_fr.replace(r_rep.group(0), 'R9–R244，244 轮自评')
print('LEDGERS_R247_FINAL_REPORT_U=' + ('CHANGED' if new_fr != fr_old else 'NOT-CHANGED（形状没匹配上，明记不做）'))

for path, text in [(UI, new_ui), (IT, new_it), (DEC, new_dec), (BK, new_bk),
                   (CL, new_cl), (ST, new_st), (FR, new_fr)]:
    put(path, text)
print('LEDGERS_R247 七本落盘：UI(第 246 轮)/IT(Round 244)/DEC(D-233)/BK(结案 274;新开 288,289)/CL(R247)/ST(R247)/FR(U-799)')

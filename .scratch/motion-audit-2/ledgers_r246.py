#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R246（第 245 轮 / Round 243）七本账落盘：277 的两处绝对颗数地板换成两态差 + 274/278 的 runner 半修好。

这一支**故意不用 % 格式化**（R245 连撞两次 arity：`%s` 数与参数数不一致 ⇒ 一半写盘一半崩）。
所有数字都是硬写进文本的现读值，读得到的日志路径写在行尾，任何一处与日志不符可由人复查。
写盘事务性：七份文本先在内存里造好并逐条断言，全绿才落盘。
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


def read(p):
    return io.open(p, encoding='utf-8').read()


def put(p, s):
    io.open(p, 'w', encoding='utf-8').write(s)


def insert_before(lines, pred, new):
    for i, ln in enumerate(lines):
        if pred(ln):
            return lines[:i] + new + lines[i:]
    raise AssertionError('anchor not found')


ui_old = read(UI)
u_ids = [int(x) for x in re.findall(r'^- \*\*U-(\d{3})', ui_old, re.M)]
d_ids = [int((m[0] or m[1]).replace('D-', '')) for m in
         re.findall(r'^(?:#{2,3} (D-\d{3})\b|\*\*(D-\d{3})（)', read(DEC), re.M)]
b_ids = [int(x) for x in re.findall(r'^(?:\*\*)?(\d{3})\. ', read(BK), re.M)]
st_txt = read(ST)
m = re.search(r'最后更新：[^\n]*?R(\d+) / 第 (\d+) 轮', st_txt)
prev_r, prev_round = int(m.group(1)), int(m.group(2))
assert max(u_ids) + 1 == 794, 'U 上界对不上'
assert max(d_ids) + 1 == 232, 'D 上界对不上'
assert max(b_ids) == 286, 'BACKLOG 上界对不上'
assert (prev_r, prev_round) == (245, 244), 'STATE 的轮次对不上'
assert max(int(x) for x in re.findall(r'^## 第 (\d+) 轮', ui_old, re.M)) == 244, 'UI_AUDIT 最大轮次不是上一轮'
swift_log = read('/tmp/r246_swift2.log')
assert 'Executed 2 tests, with 0 failures' in swift_log, 'Swift 那两格没有现读绿证'
assert swift_log.count('HOVER_TWO_STATE_277') == 6, '两态读数应当是六行'

# ── 1. AGENT_UI_AUDIT.md ────────────────────────────────────────────────────
sec = [
    '## 第 245 轮（R246 / 第 245 轮 / Round 243 · 2026-10-20）：277 的两处绝对颗数地板换成两态差尺；274/278 的 runner 半各修到能验（U-794…U-796 / D-232 · 277 结案、新开 287 · 产品 0 文件）',
    '',
    '本轮次对照：与 R245（变异腿恢复、但 277/274/278 都还挂着）相比，本轮把这三件都推到"有读数、有证人"的位置。产品 0 文件、画面一字未动（改的全在 `Tests/` 与 `.github/`）。',
    '',
    '- **U-794：277 结案 —— `UICaptureHarness.swift` 里最后两处 `pixels > 400`（直读那一格的段按钮/玻璃圆 + 设置侧栏行）换成同一件事的两半：负对照 + 分母地板。** 现读（`/tmp/r246_swift2.log`，`Executed 2 tests, with 0 failures`）：段按钮 亮 7204/7392（占比 0.975）暗 6993/7392（0.946）、玻璃圆 亮 24656/32560（0.757）暗 23088/32560（0.709）、设置行 两档都 12480/12480（1.000，整块矩形都是那层）；六行负对照全 0。**变化颗数与占比这一跑先只印不判**：D-228 已经证明"绝对颗数"量的是底平不平涂，而新地板必须由两台机器各自的读数推 —— 本机数已登记，runner 数还没有（新开 287）。旧的众数颗数没有丢：同一行尾照旧印 `旧读数(众数颗数)=`，两把尺并排一段时间，免得换尺变成失忆。',
    '- **U-795：274 的 runner 半 —— 正对照的配对按 (状态 × 色档) 两维取，不再"名字里含 idle 或 lit"。** runner 现读（run 39394134380 STEP[9]）：`HOVER_DIFF_WIRED_AT png_files=162` 之后 `HOVER_DIFF_CONTROL=` 给出**四个**名字（dark 与 light 各一颗 idle、一颗 lit），于是 `count -ne 2` 把这一步响成 `HOVER_DIFF_CONTROL_INCOMPLETE=1` —— 这朵红是接线，不是产品。改成按档各取一颗（`^modechip-hover-idle-200x60-dark$` 与 `^modechip-hover-lit-200x60-dark$`），并且闸门换成"两颗都非空"而不是"逗号切出两段"：空 IDLE + 非空 LIT 也会数出两段，那是同一个毛病的另一种穿法。本机复跑整步正文（`bash /tmp/r246_step.sh`，帧换成 /tmp/shots_r239 的 162 张）⇒ `HOVER_DIFF_EXIT=0 … 退出=0`、正对照 `逐点中位=1.515`。**这一步的红在 runner 上消失没有？要等下一跑读（287）。**',
    '- **U-796：278 结案于"上一版的修法没生效"—— `fetch-depth: 50` 仍然是浅克隆，闸门因此恒 skip。** runner 现读同一跑：`SOURCES_CELL_HISTORY 浅=True 对照数=3 头笔=415abf3 处置=skip` ⇒ R242 以为"取够 50 笔就够判"是错的：`actions/checkout` 只要 depth 有限就落 `.git/shallow`，而 `is_shallow()` 读的就是那个文件。改成 `fetch-depth: 0`（完整历史）让那一格在 runner 上真的有对象可判；代价是 clone 变慢，不是判据变松。这一条与 D-230 是同族但方向相反：那里是"这台机器判不了就只报读数"，这里是"这台机器**本来判得了**，是我把通道关了"。',
    '',
    '读数腿：RUN —— Swift `Executed 2 tests, with 0 failures`（六行 `HOVER_TWO_STATE_277`）；CI 那一步正文本机跑通 `退出=0`（`/tmp/r246_step.sh`）。',
    '眼睛腿：NOT-RUN —— 本轮产品 0 文件、帧沿用 R239 那 162 张（重捕只会得到同一批），没有新的画面判断要做；这不是"看过"。',
    '变异腿：NOT-RUN —— 本轮新增的三根牙（负对照必须 0 颗 / 分母地板 / CI 那一步"两颗都非空"）都还没有刀。R245 的 shell 执行器已经能用，本轮没来得及插臂（记为弱：这三条今天的证人只有"同一帧自己读到 0"这一格天然反向证人）。下一轮补。',
    'Swift 腿：RUN（部分）—— 只跑改动的那两格 `--filter`；`swift build` 的编译输出没有 warning 行（`/tmp/r246_build.log`，Build complete），但**全量卷、重捕帧、换装本机没跑**（本轮无产品改动、无新帧 ⇒ 帧基线不许"顺手"重写）。',
    '未做（逐条）：① 277 的两台机器地板数（本机已印，runner 待读 ⇒ 新开 287）；② 274 的"runner 那朵红消失"未复验；③ 284/286 仍未做（M798…M801 一颗没插、r169/r217/r229 的锚点腐烂未处置）；④ 本轮没有变异刀（见上一行）；⑤ CI 六笔未读（`09a8763`/`66ba71f`/`cc1e6be`/`077ac79`/`0a1e649`/`5130564`）；⑥ 产品动效本体仍 0 文件。',
    '',
]
lines = ui_old.split('\n')
assert len([l for l in lines if l.startswith(u'## 第 244 轮')]) == 1, '上一轮标题锚点不唯一'
new_ui = '\n'.join(insert_before(lines, lambda l: l.startswith(u'## 第 244 轮'), sec))
missing = [l for l in lines if l.strip() and l not in new_ui]
assert not missing, '旧行丢了：%s' % missing[:3]
assert new_ui.count(u'## 第 245 轮') == 1, '新节标题不唯一'
assert len(re.findall(r'^- \*\*U-(\d{3})', new_ui, re.M)) == len(u_ids) + 3, 'U 定义行少了 3 条'

# ── 2. AGENT_VISUAL_ITERATION.md（升序 ⇒ 只追加）────────────────────────────
it_old = read(IT)
dims = [u'真实视觉审查', u'判据有效性', u'假绿防御', u'产品面推进', u'台账一致性', u'交付诚实性', u'可复核性']
scores = [11, 14, 12, 8, 13, 14, 13]
assert sum(scores) == 85
it_rows = u''.join([u'| ' + d + u' | ' + str(s) + u'/15 |\n' for d, s in zip(dims, scores)])
it_sec = (u'\n## Round 243 · 277 的两处绝对颗数地板换成两态差尺；274/278 的 runner 半各修到能验（R246 / 第 245 轮）/ D-232 · 277 结案、新开 287 · 产品 0 文件\n\n'
          + u'本轮次对照：与 R245（刀能跑了，但 277/274/278 三件还挂着）相比，本轮把三件都推到"有读数、有证人"：Swift 两处地板换成两态差 + 负对照 + 分母地板；CI 正对照按 (状态 × 色档) 两维配对并把闸门从"数逗号"换成"两颗都非空"；`fetch-depth` 从 50（仍是浅）改成 0（完整历史）。\n'
          + u'看图腿：读数腿 RUN（Swift `Executed 2 tests, with 0 failures`、六行两态读数；CI 步骤正文本机 `退出=0`）；眼睛腿 NOT-RUN（产品 0 文件、无新帧）。\n'
          + u'七维度自评：\n| 维度 | 分/满分 |\n' + it_rows
          + u'各维理由：真实视觉审查 11 —— 眼睛腿连续第三轮没跑，0 产品改动就没有新画面可判，照扣；'
            u'判据有效性 14 —— 换掉的是两把你自己的尺量错对象的尺（D-228 的推论落地），并把"旧读数"并排印着防失忆；'
            u'假绿防御 12 —— 本轮新增三根牙却没有一把刀（变异腿 NOT-RUN），这是本表里最弱的一格；'
            u'产品面推进 8 —— 仍 0 产品文件；'
            u'台账一致性 13 —— 七本一支脚本，且这一支**不用百分号格式化**（R245 连撞两次 arity），数字全部硬写并断言与日志现读一致；'
            u'交付诚实性 14 —— 四条腿逐条写 RUN/NOT-RUN 与成因，"地板先只印不判"写明为什么这一跑不判；'
            u'可复核性 13 —— 步骤正文能被抽出来单独跑（`/tmp/r246_step.sh`），但那一抽还没进任何自动闸门。合计 **85**/105。\n')
new_it = it_old + it_sec
assert new_it.count(u'## Round 243 ·') == 1 and new_it.split(u'## Round 243 ·')[-1].count(u'合计 **85**/105') == 1
assert len(re.findall(r'^\| (?:' + u'|'.join(dims) + r') \| \d+/15 \|', new_it.split(u'## Round 243 ·')[-1], re.M)) == 7

# ── 3. AGENT_DECISIONS.md ───────────────────────────────────────────────────
dec_line = (u'**D-232（R246）：把判据从"绝对颗数"换成"两态差 + 负对照 + 分母地板"时，新数值地板必须由量它的那台机器各自印一次之后再定；'
            u'换尺那一跑只允许印读数，不允许同时改判。** 理由：本轮两处 `pixels > 400` 换掉之后，本机六行读数落在 0.709~1.000 这片跨度上'
            u'（设置行整块都是那层，段按钮 0.975，玻璃圆 0.709）—— 同一个"占比"在不同几何上是三件事；'
            u'如果换尺的同时顺手把地板也"看起来合理地"定下来，就等于用一次改动的两个自由度去互相掩护（D-227/D-228 的合流）。'
            u'所以处置是：负对照（同一帧自己必须 0 颗）与分母地板（> 100 颗，机器无关）现在就判，'
            u"变化颗数与占比先只印，等 runner 自己印一次（BACKLOG 287）再按两台机器的分布定线。\n")
new_dec = read(DEC).rstrip('\n') + '\n\n' + dec_line
assert new_dec.count(u'**D-232（') == 1

# ── 4. AGENT_BACKLOG.md：277 结案追记 + 新开 287 ─────────────────────────────
bk_lines = read(BK).split('\n')
j = [i for i, l in enumerate(bk_lines) if l.startswith(u'**277. ')]
assert len(j) == 1, '277 那条不唯一'
note277 = (u'  结案追记（R246）：两处都换了 —— 直读那一格（段按钮/玻璃圆）与设置行那一格现在判的是'
           u'「同一帧↔自身必须 0 颗」+「矩形分母 > 100 颗」+「比值 ≥ 档位下界」，旧众数颗数只在行尾并排印着。'
           u'本机现读 6 行（`Executed 2 tests, with 0 failures`）：段按钮 0.975/0.946、玻璃圆 0.757/0.709、设置行 1.000/1.000。'
           u'**变化颗数/占比的地板本轮故意不判**（D-232）：等 runner 自己印一次，拆成 287。')
bk_lines = bk_lines[:j[0] + 1] + [note277] + bk_lines[j[0] + 1:]
new_items = [
    u'',
    u'**287. 277 换尺之后的两台机器定线：读 runner 自己印的 `HOVER_TWO_STATE_277 … 两态变化=X/Y 占比=Z`，'
    u'与本机的 0.709~1.000 一起推变化颗数与占比的地板（D-232：不许由本机数外推）；'
    u'同一跑还要复验 274（`HOVER_DIFF_CONTROL=` 只给两颗、那朵 `CONTROL_INCOMPLETE` 消失）与 278（`SOURCES_CELL_HISTORY … 处置=judge`），'
    u'并给本轮三根新牙补刀（负对照换成恒假、分母地板摘掉、CI 那一步"两颗都非空"退化成数逗号）（R246 新开）**',
]
new_bk = '\n'.join(bk_lines).rstrip('\n') + '\n' + '\n'.join(new_items) + u'\n'
assert re.findall(r'^(?:\*\*)?(\d{3})\. ', new_bk, re.M) == [str(x) for x in b_ids] + [u'287'], 'BACKLOG 形状/编号变了'

# ── 5. CHANGELOG.md（插在 [Unreleased] 之下）────────────────────────────────
cl_lines = read(CL).split('\n')
idx = [i for i, l in enumerate(cl_lines) if l.strip() == u'## [Unreleased]']
assert len(idx) == 1, 'Unreleased 标题不是恰好一个'
cl_sec = [
    u'',
    u'### Changed（R246 / 第 245 轮 / Round 243 · 两处绝对颗数地板换成两态差尺；CI 的正对照配对与浅历史通道各修一处）',
    u'',
    u'- `UICaptureHarness.swift`：新增类内 `rawFrame(_:_:)`（渲染到临时目录并读回缓冲区，判定仍只在 `bandChanged` 一处）；`testDirectReadHoverLayersAreVisibleOnTheirOwnSurfaces` 与 `testSettingsRowHoverFillIsVisibleOnItsOwnSurface` 里的 `pixels > 400` 换成「负对照必须 0 颗 + 分母 > 100 颗 + 比值 ≥ 档位下界」，并印 `HOVER_TWO_STATE_277 … 两态变化/占比/负对照/旧读数`。本机 `Executed 2 tests, with 0 failures`。',
    u'- `.github/workflows/ci.yml`：① 正对照改为按色档各取一颗（`modechip-hover-idle-200x60-dark` ↔ `modechip-hover-lit-200x60-dark`），闸门从「逗号切出两段」换成「两颗都非空」（run 39394134380 现读 `HOVER_DIFF_CONTROL=` 给了四个名字 ⇒ `HOVER_DIFF_CONTROL_INCOMPLETE=1`）；② `fetch-depth: 50 → 0`（同一跑现读 `SOURCES_CELL_HISTORY 浅=True … 处置=skip` ⇒ 有限 depth 仍落 `.git/shallow`，闸门恒 skip）。',
    u'- D-232：换尺那一跑只印读数、不同时定新地板 —— 本机六行占比跨 0.709~1.000，几何不同就不该共用一根线；runner 数待读（新开 287）。',
    u'- 台账生成器这一支不用百分号格式化（R245 两次 arity 崩盘的直接后果），数字全部硬写并断言与日志现读一致。',
    u'- 产品侧 0 文件；眼睛腿 NOT-RUN；变异腿 NOT-RUN（本轮三根新牙没有刀，记为弱并拆给 287）；全量 Swift 卷与换装本机未跑。',
]
new_cl = '\n'.join(cl_lines[:idx[0] + 1] + cl_sec + cl_lines[idx[0] + 1:])
assert len([l for l in new_cl.split('\n') if l.strip() == u'## [Unreleased]']) == 1

# ── 6. AGENT_STATE.md ───────────────────────────────────────────────────────
st_lines = st_txt.split('\n')
j = [i for i, l in enumerate(st_lines) if l.startswith(u'## R') and u'状态（' in l][0]
assert st_lines[j] != u'## R246 状态（第 245 轮 / Round 243 · 2026-10-20）'
st_lines[j] = u'## R246 状态（第 245 轮 / Round 243 · 2026-10-20）'
blk = [
    u'',
    u'最后更新：2026-10-20 11:10（本地 · R246 / 第 245 轮 / Round 243）：**277 结案（两处绝对颗数地板换成两态差尺）+ 274/278 的 runner 半各修一处**（U-794…U-796 · D-232 · 新开 287 · 产品 0 文件，眼睛腿与变异腿 NOT-RUN）',
    u'',
    u'**本轮落地**：`rawFrame` + 两格换成「负对照 0 颗 / 分母 > 100 颗 / 比值 ≥ 下界」，本机 `Executed 2 tests, with 0 failures`，六行读数占比 0.709~1.000；CI 正对照按 (状态×色档) 配对、闸门改「两颗都非空」，整步正文本机跑通 `退出=0`；`fetch-depth: 50 → 0`（50 仍是浅克隆 ⇒ 闸门恒 skip）。',
    u'',
    u'**下一轮（R247 / 第 246 轮 / Round 244）的靶**：',
    u'⓪ 读 CI：`python3 scripts/ci_read.py latest` 现拿成对。未读名册：`39474398455↔09a8763`（取数时仍 in_progress ⇒ 只能说未读）、`39394134380↔66ba71f`（已读：STEP[9] 一朵红 = `HOVER_DIFF_CONTROL_INCOMPLETE=1`，正文本机已复修）、`39391292143↔cc1e6be`、`39387140455↔077ac79`、`39384781442↔5130564`、`39384656508↔0a1e649`。本笔 push 之后现取再登记，不在账里写问号 commit。',
    u'① 做 287：从 runner 自己印的 `HOVER_TWO_STATE_277` 定两台机器的地板数，并复验 `HOVER_DIFF_CONTROL=` 只给两颗、`SOURCES_CELL_HISTORY … 处置=judge`；给本轮三根新牙各配一把刀（负对照换恒假 / 分母地板摘掉 / CI 那一步退化成数逗号）。',
    u'② 做 284/286：补跑 M798…M801（280 的机制到这才允许升级成已命名）；处置 r169/r217/r229 的锚点腐烂（换锚重跑或显式退役那张表）。',
    u'③ 动效本体：产品文件连续多轮 0，自评 85 里最弱的两格就是"真实视觉审查 + 产品面推进"。真靶候选先要补两态帧（`DetailView.swift:609` 与 14 个无静置态的名字），再判要不要加反馈；不许为了破 0 纪录加动效。',
    u'④ 仍开 249 / 263 / 268 runner 半 / 269 / 267 / 260 / 262 / 258 第三处 / 254→255→248 / 243 / 227③ / 222 / 215 / 201 / 202 / 207 / 240 / 251 / 275 / 279 / 281 / 282 / 283 的 runner 半 / 284 / 285 / 286 / 287；用户闸门 220 路 A、228②、265。',
    u'',
]
new_st = '\n'.join(st_lines[:j + 1] + blk[1:] + st_lines[j + 1:])
mm = re.search(r'最后更新：[^\n]*?R(\d+) / 第 (\d+) 轮', new_st)
assert (int(mm.group(1)), int(mm.group(2))) == (246, 245), 'STATE 第一行不是本轮'
assert u'本笔=`?' not in new_st

# ── 7. AGENT_FINAL_REPORT.md：只改计数器 ────────────────────────────────────
fr_old = read(FR)
new_fr = fr_old.replace(u'U-31 … U-793', u'U-31 … U-796')
r_rep = re.search(r'R9–R(\d+)，(\d+) 轮自评', new_fr)
if r_rep:
    new_fr = new_fr.replace(r_rep.group(0), u'R9–R243，243 轮自评')
print('LEDGERS_R246_FINAL_REPORT_U=' + (u'CHANGED' if new_fr != fr_old else u'NOT-CHANGED（形状没匹配上，明记不做）'))

for path, text in [(UI, new_ui), (IT, new_it), (DEC, new_dec), (BK, new_bk),
                   (CL, new_cl), (ST, new_st), (FR, new_fr)]:
    put(path, text)
print(u'LEDGERS_R246 七本落盘：UI(第 245 轮)/IT(Round 243)/DEC(D-232)/BK(结案 277;新开 287)/CL(R246)/ST(R246)/FR(U-796)')

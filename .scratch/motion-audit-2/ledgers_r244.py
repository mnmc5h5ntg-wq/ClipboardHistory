#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R244（第 243 轮 / Round 241）七本账落盘：地板判定进尺 + 底平涂前提 + 280 三条排除。

编号全部现取；写盘事务性（任何断言红 ⇒ 一个字不落盘）。本轮无结案项 ⇒ 标题里不许出现「结案」。
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

R, ROUND, RN = 244, 243, 241
UN = ['U-787', 'U-788', 'U-789']
DN = 'D-230'
BN = ['283']


def read(p):
    return io.open(p, encoding='utf-8').read()


def put(p, s):
    io.open(p, 'w', encoding='utf-8').write(s)


def insert_before(lines, pred, new):
    for i, ln in enumerate(lines):
        if pred(ln):
            return lines[:i] + new + lines[i:]
    raise AssertionError('anchor not found')


# ── 0. 现取读数 ─────────────────────────────────────────────────────────────
ui_old = read(UI)
u_ids = [int(x) for x in re.findall(r'^- \*\*U-(\d{3})', ui_old, re.M)]
d_txt = read(DEC)
d_ids = [int((mm[0] or mm[1]).replace('D-', '')) for mm in
         re.findall(r'^(?:#{2,3} (D-\d{3})\b|\*\*(D-\d{3})（)', d_txt, re.M)]
b_ids = [int(x) for x in re.findall(r'^(?:\*\*)?(\d{3})\. ', read(BK), re.M)]
st_txt = read(ST)
m = re.search(r'最后更新：[^\n]*?R(\d+) / 第 (\d+) 轮', st_txt)
prev_r, prev_round = int(m.group(1)), int(m.group(2))
assert max(u_ids) + 1 == int(UN[0][2:]), 'U 上界对不上：%d vs %s' % (max(u_ids), UN[0])
assert max(d_ids) + 1 == int(DN[2:]), 'D 上界对不上：%d vs %s' % (max(d_ids), DN)
assert max(b_ids) + 1 == int(BN[0]), 'BACKLOG 新号不连续：%s' % b_ids[-3:]
assert (prev_r, prev_round) == (R - 1, ROUND - 1), 'STATE 的轮次对不上：%s/%s' % (prev_r, prev_round)
assert max(int(x) for x in re.findall(r'^## 第 (\d+) 轮', ui_old, re.M)) == ROUND - 1, 'UI_AUDIT 最大轮次不是上一轮'

# ── 1. AGENT_UI_AUDIT.md ────────────────────────────────────────────────────
sec = [
    u'## 第 %d 轮（R%d / Round %d · 2026-10-20）：地板判定进了尺 —— 底不平涂就只报读数，六对真帧在 WCAG 口径下全部过线（%s…%s / %s · 新开 %s · 产品 0 文件）'
    % (ROUND, R, RN, UN[0], UN[2], DN, BN[0]),
    u'',
    u'本轮次对照：与 R243（发现两口径不是一回事、把候选缺陷判掉）相比，本轮把那句话变成**尺自己会说**：地板判定进 `hover_two_state_diff.py`，并给它加了一个前提 —— 底不平涂时不判。顺带把 280 那朵"刀跑不起来"的嫌疑排掉了三条。',
    u'',
    u'- **%s：地板判定进尺（`FLOOR_LIGHT=1.20 / FLOOR_DARK=1.10`，只对 WCAG 那一列生效），六对真帧全部过线 ⇒ 「亮档偏淡」不再是印象账，是有判据的撤销。** 尺现在每对打印 `底平涂=是/否 判定=过线|低于地板|只报读数（底不平涂）`，低于地板时另打一行 `HOVER_DIFF_FLOOR_RED=1` 并 exit 1。真帧现读（162 帧、`退出=0`、`FLOOR_RED` 零行）：玻璃圆钮 暗 1.220 / 亮 1.220、收藏星 暗 1.211 / 亮 1.225、段按钮 暗 1.239 / 亮 1.224，正对照 modechip 暗 1.339 / 亮 1.371 ⇒ 282 的悬停那一族重判完成（Swift 侧两处 `pixels > 400` 仍开，那是 277）。判据卷 20 格、电池 `Ran 448 OK (skipped=4)`。' % UN[0],
    u'- **%s：「底平不平涂」我第一版算在了点亮那帧上，被合成对照当场红出来。** `measure(dirpath, a, b)` 的调用形状是 `(hover, idle)` ⇒ `pa` 是点亮帧、`pb` 才是底；我写的是 `pa[n]`，于是合成棋盘底（众数应占 0.5）被读成 `idle_flat=True`，`assertFalse` 直接红。这条不是吹毛求疵：底判错就会把 runner 那片抖动底（R242：空闲=236 而本机=255）当成平涂硬判，造出跨机假红。修完之后重测的分布才是真的：六对真帧 0.962 / 0.955 / 0.931 / 0.892 / 0.828 / 0.827，棋盘对照 0.500 ⇒ 平涂线取 0.70（最低真帧之下 0.13、抖动对照之上四成），并把"第一版算错帧"这件事写进注释，免得有人再拿旧的 0.741~0.957 那组数去比。' % UN[1],
    u'- **%s：280 那朵"刀跑不起来"排掉三条嫌疑，全部指向同一个事实：失败是确定性的。** ① `/Users/wangziyi/Codex_Project0` **不是符号链接**（`pwd -P` 同路径），两条路径经 python 起都 rc=1；② `stdin=DEVNULL` 与 `stdin=PIPE` 一样；③ 登录 shell 与非登录 shell 的 `env` 差集为空。而三次的日志字节数**一模一样**（21,663,809）⇒ 不是竞态、不是随机，是同一份被缓存的 manifest 诊断在重放。下一轮不再查环境，改用 **bash 驱动**跑刀（同一条命令在 shell 里 rc=0 是今天验过的），新开 %s。' % (UN[2], BN[0]),
    u'',
    u'读数腿：RUN —— 判据卷 `Ran 20 tests OK`（含真帧那一格：带 `CLIPBOARD_HISTORY_UI_SHOTS` 时 `HOVER_FLOOR_REAL 配对=6 退出=0 判定=…过线`），尺 CLI `退出=0`、`FLOOR_RED=0`；脚本电池 `Ran 448 OK (skipped=4)`。',
    u'眼睛腿：NOT-RUN —— 本轮没有新画面（产品 0 文件、帧沿用 R239 那 162 张），也没有新看任何一张；R243 那一张的结论不外推到这里。',
    u'变异腿：NOT-RUN —— 见 %s；本轮新加的三格（地板判定 / 平涂前提 / 真帧 standing 判据）因此没有刀。它们今天唯一的证人是那两格合成对照（一块已知低于地板、一块已知不平涂），这比没有强，但比"摘掉判据必须红"弱，账里按弱记。' % BN[0],
    u'Swift 腿：NOT-RUN —— 本轮只改 python；`swift build`、全量卷、重捕帧、换装本机都没跑（R242 的全量卷 915/44/2 仍是最近一次 Swift 侧读数）。',
    u'',
]
lines = ui_old.split('\n')
assert len([l for l in lines if l.startswith(u'## 第 %d 轮' % (ROUND - 1))]) == 1, '上一轮标题锚点不唯一'
new_ui = '\n'.join(insert_before(lines, lambda l: l.startswith(u'## 第 %d 轮' % (ROUND - 1)), sec))
missing = [l for l in lines if l.strip() and l not in new_ui]
assert not missing, '旧行丢了：%s' % missing[:3]
assert new_ui.count(u'## 第 %d 轮' % ROUND) == 1, '新节标题不唯一'
assert len(re.findall(r'^- \*\*U-(\d{3})', new_ui, re.M)) == len(u_ids) + 3, 'U 定义行少了 3 条'
new_title = [l for l in new_ui.split('\n') if l.startswith(u'## 第 %d 轮' % ROUND)][0]
assert u'%s…%s' % (UN[0], UN[2]) in new_title and (u'R%d' % R) in new_title, '新标题的 U 区间或 R 标签不对'
assert u'结案' not in new_title, '本轮没有结案项'

# ── 2. AGENT_VISUAL_ITERATION.md ────────────────────────────────────────────
it_old = read(IT)
dims = [u'真实视觉审查', u'判据有效性', u'假绿防御', u'产品面推进', u'台账一致性', u'交付诚实性', u'可复核性']
scores = [11, 15, 13, 8, 13, 14, 13]
assert sum(scores) == 87
it_rows = u''.join(u'| %s | %d/15 |\n' % (d, s) for d, s in zip(dims, scores))
it_sec = (u'\n## Round %d · 地板判定进尺：底不平涂只报读数，六对真帧在 WCAG 口径下全过线（R%d / 第 %d 轮）/ %s / 新开 %s · 产品 0 文件\n\n'
          % (RN, R, ROUND, DN, BN[0])
          + u'本轮次对照：与 R243（人发现两口径不同）相比，本轮让尺自己说出口径与前提：`FLOOR_LIGHT/FLOOR_DARK` 只比 WCAG 那一列、底不平涂时降级成"只报读数"、低于地板另打 `HOVER_DIFF_FLOOR_RED=1` 并 exit 1。另外把 280 的三条嫌疑（符号链接路径 / stdin / 登录 shell）排干净，指向"确定性重放的 manifest 诊断"。\n'
          + u'看图腿：读数腿 RUN（判据卷 20 OK、真帧 CLI 退出=0 / FLOOR_RED=0、电池 448 OK）；眼睛腿 NOT-RUN（没有新画面，也没看任何一张）。\n'
          + u'七维度自评：\n| 维度 | 分/满分 |\n' + it_rows
          + u'各维理由：真实视觉审查 11 —— 眼睛腿本轮没跑（0 产品改动、0 新帧），照扣不豁免；'
            u'判据有效性 15 —— 撤销一条候选缺陷的同时把它变成 standing 判据（真帧那一格以后谁把悬停墨调淡都会红）；'
            u'假绿防御 13 —— 合成对照当场红出我算错帧的 bug（这是真牙），但整轮没有变异刀，比 R241 那种"三把刀各摘一句"弱一档；'
            u'产品面推进 8 —— 产品文件仍 0（本轮的结论是"不改"，且现在有判据守着这个"不改"）；'
            u'台账一致性 13 —— 七本账一支脚本、编号现取、无结案项所以标题不出现「结案」；'
            u'交付诚实性 14 —— 三条 NOT-RUN（眼睛 / 变异 / Swift）逐条写成因，注释里连"第一版算错帧"和旧数字都留着；'
            u'可复核性 13 —— 判据卷能重跑，刀还跑不起来（283 是下一轮的活）。合计 **87**/105。\n')
new_it = it_old + it_sec
assert new_it.count(u'## Round %d ·' % RN) == 1, 'Round 标题不唯一'
assert new_it.split(u'## Round %d ·' % RN)[-1].count(u'合计 **87**/105') == 1, '新节里没有本轮的合计行'
assert len(re.findall(r'^\| (?:%s) \| \d+/15 \|' % u'|'.join(dims),
                      new_it.split(u'## Round %d ·' % RN)[-1], re.M)) == 7, '自评表不是 7 行'

# ── 3. AGENT_DECISIONS.md ───────────────────────────────────────────────────
dec_line = (u'**%s（R%d）：跨帧比值型的地板判定必须绑一个"底平不平涂"的前提 —— 底不平涂（变化像素上静置值众数占比 < 0.70）'
            u'时降级成"只报读数"，既不判过线也不判缺陷，也不许把整行吞掉。** '
            u'理由：R242 在同一次 CI 里看到 runner 的空闲底是 236（本机 255、暗档 50 对 30）—— 那片底被抖成许多小格子时，'
            u'"对底比值"没有单一的底可对；硬判会把机器差异读成产品缺陷（那朵 229 颗的红就是这么来的）。'
            u'反过来，如果因为"这台机器判不了"就整行不打，就又变成沉默通过。所以处置是**保留读数、撤掉判定**，'
            u'并把占比本身印出来（`HOVER_DIFF_BASE … 底众数占比=`）让前提可复查。'
            u'与 D-227（地板属于量它的机器）、D-228（绝对颗数量的是底平不平涂）、D-229（比值与地板必须同口径）同族，'
            u'本条管的是**判定需要什么前提才允许存在**。\n' % (DN, R))
new_dec = d_txt.rstrip('\n') + '\n\n' + dec_line
assert new_dec.count(u'**%s（' % DN) == 1

# ── 4. AGENT_BACKLOG.md ─────────────────────────────────────────────────────
new_bk = read(BK).rstrip('\n') + u'\n\n' + (
    u'**%s. 变异表改用 bash 驱动跑（同一条 `swift test --filter …` 在 shell 里 rc=0 已验，经 python '
    u'subprocess 稳定 rc=1 且日志字节数恒定 21,663,809 ⇒ 症状是同一份 manifest 诊断在重放）：'
    u'把 M798/M799/M800/M801 四把插进去，并给本轮新加的三格（地板判定 / 平涂前提 / 真帧 standing 判据）各配一把刀；'
    u'破了之后回头补 280 的成因（R%d 新开）**' % (BN[0], R) + u'\n')
b_ids2 = [int(x) for x in re.findall(r'^(?:\*\*)?(\d{3})\. ', new_bk, re.M)]
assert b_ids2 == b_ids + [int(BN[0])], 'BACKLOG 形状/编号变了'

# ── 5. CHANGELOG.md ─────────────────────────────────────────────────────────
cl_lines = read(CL).split('\n')
idx = [j for j, l in enumerate(cl_lines) if l.strip() == u'## [Unreleased]']
assert len(idx) == 1, 'Unreleased 标题不是恰好一个：%d' % len(idx)
cl_sec = [
    u'',
    u'### Changed（R%d / 第 %d 轮 / Round %d · 地板判定进尺：只对 WCAG 列生效，底不平涂降级成只报读数）' % (R, ROUND, RN),
    u'',
    u'- `scripts/hover_two_state_diff.py` 新增 `FLOOR_LIGHT=1.20 / FLOOR_DARK=1.10 / FLAT_SHARE=0.70`：每对给出 `底平涂=… 判定=…`，低于地板时打 `HOVER_DIFF_FLOOR_RED=1` 并 exit 1；底不平涂时**不判**但照打读数，另印 `HOVER_DIFF_BASE … 底众数占比=`。平涂线由真帧分布推（六对 0.827~0.962、棋盘对照 0.500），不是拍的。',
    u'- 判据卷加三格（共 20 格）：`FloorVerdictTests` 两格（平涂底上弱悬停必须被点名并 exit 1；同一块弱填充放棋盘底上必须只报读数、不红），`RealFrameFloorTests` 一格 standing 判据（真帧每一对都必须"过线"或被具名降级，否则红；无帧通道时是有名字的 skip）。',
    u'- 一条自坏明记：底占比第一版算在点亮帧上（`measure(a=hover, b=idle)` 里我用 `pa`），被合成棋盘对照当场红出来；修完重测的分布与旧数字都留在注释里（D-230）。',
    u'- 280 排掉三条嫌疑（符号链接路径 / stdin / 登录 shell 环境变量），失败确定性重放 ⇒ 新开 283：变异表改 bash 驱动，破了再回头补成因。本轮变异腿、眼睛腿、Swift 腿均 NOT-RUN。',
]
new_cl = '\n'.join(cl_lines[:idx[0] + 1] + cl_sec + cl_lines[idx[0] + 1:])
assert len([l for l in new_cl.split('\n') if l.strip() == u'## [Unreleased]']) == 1, 'Unreleased 变成两个'
assert (u'### Changed（R%d' % R) in new_cl

# ── 6. AGENT_STATE.md ───────────────────────────────────────────────────────
head_new = u'## R%d 状态（第 %d 轮 / Round %d · 2026-10-20）' % (R, ROUND, RN)
st_lines = st_txt.split('\n')
j = [k for k, l in enumerate(st_lines) if l.startswith(u'## R') and u'状态（' in l][0]
assert st_lines[j] != head_new, 'STATE 顶层标题已经是本轮'
st_lines[j] = head_new
blk = [
    u'',
    u'最后更新：2026-10-20 08:30（本地 · R%d / 第 %d 轮 / Round %d）：**地板判定进尺 + 底平涂前提 + 280 三条排除**（%s…%s · %s · 新开 %s · 产品 0 文件，眼睛腿未跑）' % (R, ROUND, RN, UN[0], UN[2], DN, BN[0]),
    u'',
    u'**本轮落地**：`hover_two_state_diff.py` 加 `FLOOR_LIGHT/FLOOR_DARK/FLAT_SHARE`（判定只对 WCAG 列生效、底不平涂只报读数、低于地板 exit 1）；判据卷 17→20 格（两格合成对照 + 一格真帧 standing 判据）；真帧六对全部过线（1.211~1.371）；电池 `Ran 448 OK (skipped=4)`；280 排掉符号链接 / stdin / 登录 shell 三条嫌疑（失败确定性重放，日志字节数恒定）。',
    u'',
    u'**下一轮（R%d / 第 %d 轮 / Round %d）的靶**：' % (R + 1, ROUND + 1, RN + 1),
    u'⓪ 读 CI：`python3 scripts/ci_read.py latest` 现拿成对（别轮询）。未读名册（push 后把本笔的 run 补进来）：`cc1e6be`（R243）、`077ac79`（R242 收尾）、`0a1e649`（R242 主体）、`5130564`（R242 STATE 成对）、本笔。每笔要读的四件事照 BACKLOG 276 结案追记：① STEP[9] 的 `SOURCES_CELL_HISTORY … 处置=` 是否 skip→judge（278）；② STEP[17] modechip 那朵是否消失 + runner 自印的 `两态变化=X/Y 占比=Z`（279）；③ `HOVER_DIFF_WIRED_AT png_files=` 与 `HOVER_DIFF 配对=`（275）；④ skip 数本机 3 / runner 2 的成因。这一跑还要多看一眼新加的 `HOVER_DIFF_BASE` 与 `判定=` 列 —— runner 的底若被判成不平涂，说明 D-230 的前提在 runner 上真的需要。',
    u'① 做 283：变异表改 **bash 驱动**（`swift test` 在 shell 里 rc=0 已验），把 M798…M801 插进去，并给本轮三格各配一把刀；这是"变异对照"这条硬规矩目前唯一的堵点。',
    u'② 做 277：Swift 侧其余两处 `pixels > 400` 换成 `bandChanged`（段按钮/玻璃圆那一族、设置行那格），配刀。',
    u'③ 动效本体：产品文件连续多轮 0。真靶候选要按 282 的口径重判后再定 —— 悬停那一族已证明过线（撤销），所以剩下能改的是**没有两态帧**的位点（`DetailView.swift:609` 与 14 个无静置态的名字）：先补夹具与静置帧，再判要不要加反馈。不许为了破 0 纪录加动效。',
    u'④ 仍开 249 / 263 / 268 runner 半 / 269 / 267 / 260 / 262 / 258 第三处 / 254→255→248 / 243 / 227③ / 222 / 215 / 201 / 202 / 207 / 240 / 251 / 275 / 277 / 278 / 279 / 280 / 281 / 282 / 283；用户闸门 220 路 A、228②、265。',
    u'',
]
new_st = '\n'.join(st_lines[:j + 1] + blk[1:] + st_lines[j + 1:])
mm = re.search(r'最后更新：[^\n]*?R(\d+) / 第 (\d+) 轮', new_st)
assert (int(mm.group(1)), int(mm.group(2))) == (R, ROUND), 'STATE 第一行最后更新不是本轮：%s' % (mm.groups(),)
assert all(l in new_st for l in st_lines if l.startswith(u'## 第') or l.startswith(u'**下一轮')), 'STATE 旧行丢了'

# ── 7. AGENT_FINAL_REPORT.md ────────────────────────────────────────────────
fr_old = read(FR)
new_fr = fr_old.replace(u'U-31 … U-%d' % max(u_ids), u'U-31 … U-%s' % UN[-1][2:])
r_rep = re.search(r'R9–R(\d+)，(\d+) 轮自评', new_fr)
if r_rep:
    new_fr = new_fr.replace(r_rep.group(0), u'R9–R%d，%d 轮自评' % (RN, RN))
print('LEDGERS_R244_FINAL_REPORT_U=%s' % ('CHANGED' if new_fr != fr_old else u'NOT-CHANGED（形状没匹配上，明记不做）'))

for path, text in [(UI, new_ui), (IT, new_it), (DEC, new_dec), (BK, new_bk),
                   (CL, new_cl), (ST, new_st), (FR, new_fr)]:
    put(path, text)
print('LEDGERS_R244 七本落盘：UI(第 %d 轮)/IT(Round %d)/DEC(%s)/BK(%s)/CL(R%d)/ST(R%d)/FR(U-%s)'
      % (ROUND, RN, DN, BN[0], R, R, UN[-1][2:]))

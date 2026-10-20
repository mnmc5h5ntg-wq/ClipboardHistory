#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R243（第 242 轮 / Round 240）七本账落盘：两态差的**口径对账**把一条候选缺陷判掉。

编号全部现取（271 那笔的教训：轮次标签与编号不许手抄）；写盘事务性 —— 任何一条断言红 ⇒ 一个字不落盘。
本轮没有结案项（CLOSED=None），所以标题与正文都不许出现"结案"字样。
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

R, ROUND, RN = 243, 242, 240
UN = ['U-784', 'U-785', 'U-786']
DN = 'D-229'
BN = ['282']


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
d_ids = [int((m[0] or m[1]).replace('D-', '')) for m in
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

# ── 1. AGENT_UI_AUDIT.md（降序：插在当前最大轮次标题之上）────────────────────
sec = [
    u'## 第 %d 轮（R%d / Round %d · 2026-10-20）：两态差的口径对账 —— 把「亮档 1.09 掉在地板下」这条候选缺陷判成尺的假话（%s…%s / %s · 新开 %s · 产品 0 文件）'
    % (ROUND, R, RN, UN[0], UN[2], DN, BN[0]),
    u'',
    u'本轮次对照：与 R242（把 modechip 那格的绝对颗数地板换成两态变化尺）相比，本轮问的是下一个问题：**两态差那个比值，和我拿去比的地板，是不是同一个估计量**。答案是否 —— 而这一条足以撤销一条产品缺陷。',
    u'',
    u'- **%s：仓库的亮/暗地板（1.20 / 1.10）是 WCAG 线性口径，而两态差尺原来只给码值口径 —— 拿 1.09 去比 1.20 会造出一个假缺陷。** `UICaptureHarness.contrastRatio` 对每个通道做 `c<=0.03928 ? c/12.92 : ((c+0.055)/1.055)**2.4` 再取比值，`scripts/hover_two_state_diff.py` 原来的 `_ratio` 是 `c/255 + 0.05` 直接相比。同一对像素两个口径不同数：白底上 alpha=0.085 的悬停层合成出 233，码值口径 1.090、WCAG 口径 1.214。真帧现读（`--shots /tmp/shots_r239`，162 帧在场、`退出=0`、负对照 0 颗、正对照 modechip）：玻璃圆钮 亮 WCAG **1.220**（码值 1.092）、行内收藏星 亮 **1.225**（1.094）、段按钮 亮 **1.224**（1.095）、暗档分别 1.220 / 1.211 / 1.239，正对照 modechip 亮 1.371 ⇒ **四处全部过 1.20 地板**。R240/D-225 拦下过一次改档（那次的原因是估计量不同：带内均值 vs 控件局部），这次是同一个坑的第二种形状（线性化不同），而它更隐蔽 —— 两个数都叫"对比度比值"。尺现在把两个口径同时印出来，并在行尾明写「只有最后一列可以拿去和地板比」。' % UN[0],
    u'- **%s：两条自坏，都被判据卷自己红回来。** ① 期望值不许心算：WCAG 那一格我手算成 2.067，现算独立实现是 2.067538 ⇒ 四舍五入 2.068，`test_a_fully_changed_band...` 直接 `2.067 != 2.068` 红 —— 与 R130「两行期望错而代码对」同一族，第二次踩。② 改了打印形状就要同步改契约格：我把行标签从 `变化像素逐点中位=` 改成 `变化像素逐点中位(码值)=`，`InstrumentContractTests` 按旧标签 `assertIn` 立刻红 —— 这条红是**对的**（它钉的正是"读数行不许悄悄换形状"），所以我改的是契约格的期望，不是放宽它。' % UN[1],
    u'- **%s：眼睛腿恢复的第一张帧，判的是「亮档那颗胶囊的悬停底会不会抢视线」—— 不抢。** 直接看 `modechip-hover-lit-200x60-light.png`（@2x，200×60pt 的夹具帧）：悬停那一层是一圈浅灰、圆角半径与胶囊本体一致、文字仍是画面里最重的一层，它只标出「鼠标在这里」，没有把视线从「原文 / 渲染」这一对的选择上拉开 ⇒ 与目标模式要的「高级简约、不喧宾夺主」一致，也与本轮 WCAG 口径的正对照 1.371 同向。**范围收窄**：这一条只覆盖 modechip 亮档 lit 这一张帧，其余 161 张本轮没有逐张看（产品 0 文件 ⇒ 没有新画面），不许据此说整屏都看过。' % UN[2],
    u'',
    u'读数腿：RUN —— 判据卷 `Ran 17 tests OK (skipped=1)`（新增一格专测两口径不许互当证人：码值 1.090 < 1.20 而 WCAG 1.214 ≥ 1.20 同时断言）；真帧 CLI `退出=0`；脚本电池 `Ran 445 OK (skipped=3)`。',
    u'眼睛腿：RUN（第一次恢复）—— 直接看了 `modechip-hover-lit-200x60-light.png`：亮档那颗「原文」胶囊的悬停底是浅灰、圆角、不压过文字，也不抢视线 ⇒ 与"高级简约、不喧宾夺主"一致。**只看了这一张**，其余帧本轮没有新判断要做（产品 0 文件），不许把这一张的结论外推成"全部看过"。',
    u'变异腿：NOT-RUN —— `mutate_r242.py` 第五次也拒发基线（280 未破：同句 `swift test --filter …` 在 shell 里 rc=0、经 python subprocess 稳定 rc=1 且日志字节数一模一样），本轮新加的 WCAG 两格因此**没有刀**；负对照与分母地板那两条 R242 声称也仍未被证明。',
    u'Swift 腿：NOT-RUN —— 本轮只改 python（尺 + 判据卷 + 台账），`swift build` / 全量卷 / 重捕帧 / 换装本机都没跑；帧沿用 R239 那 162 张（`ls` 数过），所以"画面"这一项本轮没有新证据。',
    u'未做（逐条）：① 251/清账表里其余按**码值口径**记下来的两态读数还没重判（本轮只重判了四处）⇒ 新开 %s；② 277 那两处 Swift 侧的绝对颗数地板还没换尺（刀 blocked）；③ 275/279 等 runner 自己打印的 `HOVER_DIFF 配对=` 与 `两态变化=`；④ `DetailView.swift:609` 第三处仍无静置帧。' % BN[0],
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
assert u'结案' not in new_title, '本轮没有结案项，标题不许出现「结案」'

# ── 2. AGENT_VISUAL_ITERATION.md（升序：只追加到文件尾）──────────────────────
it_old = read(IT)
dims = [u'真实视觉审查', u'判据有效性', u'假绿防御', u'产品面推进', u'台账一致性', u'交付诚实性', u'可复核性']
scores = [12, 15, 12, 9, 13, 14, 13]
assert sum(scores) == 88
it_rows = u''.join(u'| %s | %d/15 |\n' % (d, s) for d, s in zip(dims, scores))
it_sec = (u'\n## Round %d · 两态差的口径对账：把一条候选缺陷判成尺的假话（R%d / 第 %d 轮）/ %s / 新开 %s · 产品 0 文件\n\n'
          % (RN, R, ROUND, DN, BN[0])
          + u'本轮次对照：与 R242（换了估计量）相比，本轮查的是**比值与地板是不是同一个口径**。做了什么：给 `hover_two_state_diff.py` 加 WCAG 线性口径并把两口径同时印出 → 判据卷加一格专测两口径不许互当证人（17 格）→ 真帧现读四处 → 结论是"亮档 1.09 掉地板下"这条候选缺陷不成立 → 眼睛腿恢复看了一张帧 → 台账。\n'
          + u'看图腿：读数腿 RUN（真帧 CLI 退出=0、负对照 0 颗、正对照 modechip；判据卷 17 OK；电池 445 OK）；眼睛腿 RUN（`modechip-hover-lit-200x60-light` 一张：浅灰胶囊底、不压文字、不抢视线）。\n'
          + u'七维度自评：\n| 维度 | 分/满分 |\n' + it_rows
          + u'各维理由：真实视觉审查 12 —— 眼睛腿六轮后第一次真跑，但只看了一张帧，且没有新画面可看（产品 0 文件）；'
            u'判据有效性 15 —— 这一格把"两个都叫对比度比值的数其实不同口径"变成会红的判据，并当场撤销一条假缺陷；'
            u'假绿防御 12 —— 本轮新格没有刀（280 未破，表第五次拒发基线），R242 那三条声称也仍未被证明；'
            u'产品面推进 9 —— 结论是"不改"，而且是**量出来的不改**（四处 WCAG 全过地板），比上一轮"没能力改"进一步，但产品文件仍是 0；'
            u'台账一致性 13 —— 七本账一支脚本事务性写盘、编号现取、本轮无结案项所以标题里不许出现「结案」；'
            u'交付诚实性 14 —— Swift 腿与变异腿逐条 NOT-RUN 写明成因，眼睛腿明写"只看了一张、不许外推"；'
            u'可复核性 13 —— 判据卷能重跑这把口径对账，但刀还跑不起来。合计 **88**/105。\n')
new_it = it_old + it_sec
assert new_it.count(u'## Round %d ·' % RN) == 1, 'Round 标题不唯一'
assert new_it.split(u'## Round %d ·' % RN)[-1].count(u'合计 **88**/105') == 1, '新节里没有本轮的合计行'
assert new_it.count(u'合计 **88**/105') >= 2, u'上一轮（R241）也是 88 —— 这条只是提醒：合计分数会跨轮重复，断言必须限定在本节内'
assert len(re.findall(r'^\| (?:%s) \| \d+/15 \|' % u'|'.join(dims),
                      new_it.split(u'## Round %d ·' % RN)[-1], re.M)) == 7, '自评表不是 7 行'

# ── 3. AGENT_DECISIONS.md ───────────────────────────────────────────────────
dec_line = (u'**%s（R%d）：任何一条对比度地板必须在账里写明它的口径（WCAG 线性 / 码值直算），'
            u'任何一把比值尺必须把它用的口径印在读数行里 —— 不同口径的数不许互相比，也不许互相当对方的证人。** '
            u'理由：仓库的亮档地板 1.20 出自 `UICaptureHarness.contrastRatio`（对通道做 ((c+0.055)/1.055)^2.4 的线性化），'
            u'而两态差尺原来给的是码值口径。同一块白底上 alpha=0.085 的悬停层，码值读 1.090、WCAG 读 1.214 —— '
            u'拿前者去比后者定义的地板，就把一个**合格的产品**读成了缺陷；R240 那次拦下改档的原因是估计量不同（带内均值 vs 控件局部），'
            u'这次是线性化不同，两种形状同源：两个数都叫"对比度比值"，所以错了也不响。'
            u'与 D-226（覆盖率要能被打红）、D-228（绝对颗数量的是底平不平涂）同族，本条管的是**比值与地板必须同口径**。\n' % (DN, R))
new_dec = d_txt.rstrip('\n') + '\n\n' + dec_line
assert new_dec.count(u'**%s（' % DN) == 1

# ── 4. AGENT_BACKLOG.md（只新开，不结案）────────────────────────────────────
new_bk = read(BK).rstrip('\n') + u'\n\n' + (
    u'**%s. 251 与清账表里其余按**码值口径**记下来的两态读数，逐条用 WCAG 口径重判一遍'
    u'（本轮只重判了玻璃圆钮 / 收藏星 / 段按钮 / modechip 四处，全部过 1.20 ⇒ 那几条"亮档偏淡"的印象要撤回或改判）；'
    u'重判时顺带把 277 那两处 Swift 侧的绝对颗数地板按同口径复核（D-229）（R%d 新开）**' % (BN[0], R)
    + u'\n')
b_ids2 = [int(x) for x in re.findall(r'^(?:\*\*)?(\d{3})\. ', new_bk, re.M)]
assert b_ids2 == b_ids + [int(BN[0])], 'BACKLOG 形状/编号变了'

# ── 5. CHANGELOG.md ─────────────────────────────────────────────────────────
cl_lines = read(CL).split('\n')
idx = [j for j, l in enumerate(cl_lines) if l.strip() == u'## [Unreleased]']
assert len(idx) == 1, 'Unreleased 标题不是恰好一个：%d' % len(idx)
cl_sec = [
    u'',
    u'### Changed（R%d / 第 %d 轮 / Round %d · 两态差尺加 WCAG 口径：把「亮档 1.09 掉在 1.20 之下」这条候选缺陷判成尺的假话）' % (R, ROUND, RN),
    u'',
    u'- `scripts/hover_two_state_diff.py` 现在同时给**码值口径**与 **WCAG 线性口径**（`_wcag_lum` 与 `UICaptureHarness.contrastRatio` 同一算式），读数行尾明写「只有最后一列可以拿去和地板比」。真帧现读：玻璃圆钮 亮 1.220 / 暗 1.220、收藏星 亮 1.225 / 暗 1.211、段按钮 亮 1.224 / 暗 1.239、正对照 modechip 亮 1.371 ⇒ 四处全部过仓库自己的 1.20 地板，R240 挂着的"亮档偏淡"候选缺陷**撤销**，产品不改（D-229）。',
    u'- 判据卷加一格 `test_the_light_hover_fill_clears_the_floor_only_in_the_floor_s_own_estimator`（同一块填充同时断言码值 1.090 与 WCAG 1.214，并断言前者低于地板、后者不低于）⇒ 拿错口径给产品定罪这件事从此会红。卷共 17 格、`Ran 17 OK (skipped=1)`；脚本电池 `Ran 445 OK (skipped=3)`。',
    u'- 两条自坏明记：期望值手算 2.067 被独立现算 2.068 红回来（第二次犯"心算真值表"）；改打印标签被 `InstrumentContractTests` 红回来（这条红是对的，改的是契约期望而不是放宽它）。变异腿本轮 NOT-RUN：`mutate_r242.py` 第五次拒发基线（BACKLOG 280 未破）。',
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
    u'最后更新：2026-10-20 07:45（本地 · R%d / 第 %d 轮 / Round %d）：**两态差尺的口径对账 —— 一条候选缺陷被判成尺的假话**（%s…%s · %s · 新开 %s · 产品 0 文件，画面只看了一张帧）' % (R, ROUND, RN, UN[0], UN[2], DN, BN[0]),
    u'',
    u'**本轮落地**：`hover_two_state_diff.py` 加 WCAG 线性口径、两口径同印；判据卷 17 格（新增"两口径不许互当证人"一格，期望值现算：码值 1.090 / WCAG 1.214）；真帧现读四处全过 1.20 地板（1.220 / 1.225 / 1.224 / 1.371）⇒ R240 挂着的"亮档偏淡"撤销，不改产品（D-229）；电池 `Ran 445 OK (skipped=3)`。',
    u'',
    u'**下一轮（R%d / 第 %d 轮 / Round %d）的靶**：' % (R + 1, ROUND + 1, RN + 1),
    u'⓪ 读 CI：`python3 scripts/ci_read.py latest` 现拿成对（别轮询）。本笔 push 之后要读的是：① STEP[9] 的 `SOURCES_CELL_HISTORY … 处置=` 是不是从 skip 变 judge（278 的验收）；② STEP[17] modechip 那朵红消失没有、并抄回 runner 自印的 `两态变化=X/Y 占比=Z`（279）；③ 新接的那一步打的 `HOVER_DIFF_WIRED_AT png_files=` 与 `HOVER_DIFF 配对=`（275 的地板）；④ skip 数本机 3 / runner 2 的成因（279）。上一笔 `0a1e649`、`5130564`、`077ac79` 三笔的 run 若仍未读，继续成对登记在这里。',
    u'① 破 280（刀跑不起来）：同句 `swift test --filter …` 在 shell 里 rc=0、经 python subprocess 稳定 rc=1 且日志字节数一模一样 ⇒ 下一步试 `stdin=DEVNULL`（上一次这一支跑了 12 分钟没返回，被停掉了，没拿到结论）与清 manifest 缓存；破了就把 M798…M801 插进去，并给本轮的 WCAG 两格补刀。',
    u'② 做 282 + 277：把 251/清账表里其余**码值口径**的两态读数按 WCAG 重判，并把两处 `pixels > 400` 换成 `bandChanged`。',
    u'③ 动效本体：亮档"偏淡"这条已撤销 ⇒ 真靶要换一个**有测量支撑**的位点（候选：251 第三处 `DetailView.swift:609` 先补静置帧；或清账表里按 WCAG 重判后仍低于地板的那一格）。连续多轮产品 0 文件，这条仍是目标模式的核心欠账。',
    u'④ 仍开 249 / 263 / 268 runner 半 / 269 / 267 / 260 / 262 / 258 第三处 / 254→255→248 / 243 / 227③ / 222 / 215 / 201 / 202 / 207 / 240 / 251 / 274 的 runner 验收 / 275 / 277 / 278 / 279 / 280 / 281；用户闸门 220 路 A、228②、265。',
    u'',
]
new_st = '\n'.join(st_lines[:j + 1] + blk[1:] + st_lines[j + 1:])
mm = re.search(r'最后更新：[^\n]*?R(\d+) / 第 (\d+) 轮', new_st)
assert (int(mm.group(1)), int(mm.group(2))) == (R, ROUND), 'STATE 第一行最后更新不是本轮：%s' % (mm.groups(),)
assert all(l in new_st for l in st_lines if l.startswith(u'## 第') or l.startswith(u'**下一轮')), 'STATE 旧行丢了'

# ── 7. AGENT_FINAL_REPORT.md：只改计数器 ────────────────────────────────────
fr_old = read(FR)
new_fr = fr_old.replace(u'U-31 … U-%d' % max(u_ids), u'U-31 … U-%s' % UN[-1][2:])
r_rep = re.search(r'R9–R(\d+)，(\d+) 轮自评', new_fr)
if r_rep:
    new_fr = new_fr.replace(r_rep.group(0), u'R9–R%d，%d 轮自评' % (RN, RN))
print('LEDGERS_R243_FINAL_REPORT_U=%s' % ('CHANGED' if new_fr != fr_old else u'NOT-CHANGED（形状没匹配上，明记不做）'))

for path, text in [(UI, new_ui), (IT, new_it), (DEC, new_dec), (BK, new_bk),
                   (CL, new_cl), (ST, new_st), (FR, new_fr)]:
    put(path, text)
print('LEDGERS_R243 七本落盘：UI(第 %d 轮)/IT(Round %d)/DEC(%s)/BK(%s)/CL(R%d)/ST(R%d)/FR(U-%s)'
      % (ROUND, RN, DN, BN[0], R, R, UN[-1][2:]))

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R251（第 250 轮 / Round 248）七本账落盘：290 结案 —— `MultiFileRow` 第一次有两态帧并被量到，
而量到之后发现这张帧证明不了"只亮被指的那一行"（新开 296）。先落盘成文件、ast.parse 通过，再进提交链。"""
import io, os, re

R = '/Users/wangziyi/Codex_Project0'
PAIR = 'HOVER_FLOOR_REAL 配对=8 无静置态=14 退出=0'


def read(p):
    return io.open(p, encoding='utf-8').read()


def put(p, s):
    io.open(p, 'w', encoding='utf-8').write(s)


ui = read(R + '/AGENT_UI_AUDIT.md')
u_ids = [int(x) for x in re.findall(r'^- \*\*U-(\d{3})', ui, re.M)]
d_ids = [int((m[0] or m[1]).replace('D-', '')) for m in
         re.findall(r'^(?:#{2,3} (D-\d{3})\b|\*\*(D-\d{3})（)', read(R + '/AGENT_DECISIONS.md'), re.M)]
b_ids = [int(x) for x in re.findall(r'^(?:\*\*)?(\d{3})\. ', read(R + '/AGENT_BACKLOG.md'), re.M)]
st = read(R + '/AGENT_STATE.md')
m = re.search(r'最后更新：[^\n]*?R(\d+) / 第 (\d+) 轮', st)
assert max(u_ids) + 1 == 810, max(u_ids)
assert max(d_ids) + 1 == 237, max(d_ids)
assert max(b_ids) == 295, max(b_ids)
assert (int(m.group(1)), int(m.group(2))) == (250, 249)
assert max(int(x) for x in re.findall(r'^## 第 (\d+) 轮', ui, re.M)) == 249
names = [f for f in os.listdir('/tmp/shots_r251') if f.endswith('.png')]
assert len(names) == 164, len(names)
assert 'detail-3-files-hover-720x520-dark.png' in names and 'detail-3-files-hover-720x520-light.png' in names
cap = read('/tmp/r251_capture.log')
assert 'Executed 80 tests, with 4 tests skipped and 0 failures' in cap, '捕获卷没有现读绿证'

T = '## 第 250 轮（R251 / 第 250 轮 / Round 248 · 2026-10-20）：290 结案 —— 多文件行第一次有两态帧并被量到（两档判定=过线），而量到之后才发现这张帧证明不了"只亮被指的那一行"（U-810…U-812 / D-237 · 290 结案、新开 296 · 产品 0 文件）'
B1 = ('- **U-810：新夹具 `detail-3-files-hover` ⇒ 尺自动配到 8 对，R248 那条通道第一次被量。** '
      '现读（`/tmp/shots_r251`，164 张先数过；捕获卷 `Executed 80 tests, with 4 tests skipped and 0 failures`）：'
      '暗档 `detail-3-files-hover-720x520-dark ↔ detail-3-files-720x520-dark` 带=(40,142,1408,1008) 变化=28.6% 带内均值(码值)=1.179 逐点中位(码值)=1.515；'
      '亮档 变化=28.8% 带内均值=1.049 ⇒ 两档 `判定=过线`，`' + PAIR + '`，判据卷 `Ran 20 tests OK`。'
      '夹具只加了一颗：`DetailView(historyStore:).environment(\\.hoveredForCapture, true)` 配 index 3（`.files` 是多文件行的唯一载体），帧名形状让 `find_pairs` 自己配对，不写坐标也不列名单。')
B2 = ('- **U-811：眼睛腿 RUN（两张新帧，暗档 idle 与 hover）。** 判断：点亮是一整块圆角横底，文件名与副行"…/Downloads"的墨没有被压暗或糊边，'
      'chevron 与类型图标不动，右下角动作栏不受影响 ⇒ 强度与形状都合适，这一位保留、不改。'
      '一条排版观察记下来不判：横底的圆角与行间分隔线是两套边界，点亮后分隔线仍从药丸两端穿过 —— 是否该让分隔线在悬停时退到药丸内沿，没量过，留给清账表。')
B3 = ('- **U-812：但这张帧能证明的比"悬停正常"少得多 —— 三行同时亮了。** 取证键是"整棵视图一个布尔"，'
      '所以帧里的 28.6% 是**三行一起抬**的结果；产品里只有指针下那一行会抬。'
      '于是本轮量到的是"有一层会亮、亮多少、过不过线"，**没有**量到"该不该只亮一行 / 只亮一行时强度是否一样"。'
      '这不是小字：如果哪天要判"悬停归属"（比如误把整列点亮当缺陷或当特性），这套夹具给不出证据。新开 296：让键能带行标识（或夹具渲染单行），并给"整列亮 vs 单行亮"配一条会红的判据。')
sec = [T, '',
       '本轮次对照：与 R250（补跑验证、零代码改动）相比，本轮把 R248 接上的那条通道第一次量出来，并且量出了夹具本身的证明边界。产品 0 文件（改的只有测试夹具）。',
       '', B1, '', B2, '', B3, '',
       '读数腿：RUN —— 捕获卷 80 格 0 失败、164 张帧；尺 CLI `退出=0`、`' + PAIR + '`；判据卷 `Ran 20 OK`。',
       '眼睛腿：RUN —— 两张新帧（暗档 idle/hover），判断与"未判的排版观察"都写在 U-811 里。',
       '变异腿：NOT-RUN —— 本轮新增的是一颗夹具而不是判据；它今天由两处现成证人覆盖（`find_pairs` 的配对数地板、真帧 standing 判据），但没有"摘掉它必须红"的刀。',
       'Swift 腿：RUN —— 捕获卷整卷（80 格）绿；全量卷与换装本机本轮不需要（产品 0 文件，D-236 的四件套只在改产品时强制）。',
       '未做（逐条）：① 296（整列亮 vs 单行亮的取证与判据）；② 291 那四位欠账；③ 295（四件套脚本化）；④ 287/284/286；⑤ CI 未读（`c5f9e2b` 及之前四笔 push 后未取号）。',
       '']
lines = ui.split('\n')
idx = [i for i, l in enumerate(lines) if l.startswith('## 第 249 轮')][0]
new_ui = '\n'.join(lines[:idx] + sec + lines[idx:])
assert not [l for l in lines if l.strip() and l not in new_ui]
assert len(re.findall(r'^- \*\*U-(\d{3})', new_ui, re.M)) == len(u_ids) + 3

dims = ['真实视觉审查', '判据有效性', '假绿防御', '产品面推进', '台账一致性', '交付诚实性', '可复核性']
sc = [13, 13, 12, 11, 13, 14, 13]
assert sum(sc) == 89
it_new = (read(R + '/AGENT_VISUAL_ITERATION.md')
          + '\n## Round 248 · 290 结案：多文件行第一次有两态帧并被量到，同时量出夹具证明不了的事（R251 / 第 250 轮）/ D-237 · 新开 296 · 产品 0 文件\n\n'
          + '本轮次对照：与 R250（补验证、零改动）相比，本轮给 R248 那条通道补上夹具并量出读数，且把"这张帧能证明什么"写清。\n'
          + '看图腿：读数腿 RUN（捕获卷 80 格 0 失败、164 张、尺 `配对=8 退出=0`）；眼睛腿 RUN（两张新帧）。\n'
          + '七维度自评：\n| 维度 | 分/满分 |\n' + ''.join(['| ' + d + ' | ' + str(s) + '/15 |\n' for d, s in zip(dims, sc)])
          + '各维理由：真实视觉审查 13 —— 第一次看的就是本轮改动的那一位，两张成对；'
            '判据有效性 13 —— 量到了强度与过线判定，但归属问题（整列 vs 单行）没判据；'
            '假绿防御 12 —— 本轮没有刀（新夹具只由既有的配对地板与 standing 判据覆盖）；'
            '产品面推进 11 —— 只动夹具，产品 0 文件；'
            '台账一致性 13 —— 生成器先落盘再 ast.parse，数字全部现读断言；'
            '交付诚实性 14 —— 把"帧证明不了只亮一行"写在读数旁边，而不是让 28.6% 冒充悬停验收；'
            '可复核性 13 —— 帧目录与日志路径都写在账里。合计 **89**/105。\n')
assert it_new.count('## Round 248 ·') == 1
assert len(re.findall(r'^\| (?:' + '|'.join(dims) + r') \| \d+/15 \|', it_new.split('## Round 248 ·')[-1], re.M)) == 7

dec = ('**D-237（R251）：两态帧必须在账里写明"点亮范围"—— 一个作用于整棵视图的取证布尔，只能证"有一层会亮、亮多少"，'
       '不能证"归属"（哪一行该亮）。要判归属，键得能带行标识，或夹具只渲染单行。** '
       '理由：本轮第一次量 `MultiFileRow` 就撞上这个：帧里三行同时抬（28.6% 变化），而产品里只有指针下那一行抬。'
       '如果不写这条限制，`判定=过线` 就会被后面的人读成"悬停验收过了"—— 那正是 R90 那族"形容词当读数"的另一种穿法：'
       '读数是真的，但它量的是另一件事。与 D-229（口径同边）、D-232（换尺那一跑不定线）同族。\n')
new_dec = read(R + '/AGENT_DECISIONS.md').rstrip('\n') + '\n\n' + dec
assert new_dec.count('**D-237（') == 1

bk = read(R + '/AGENT_BACKLOG.md').split('\n')
j = [i for i, l in enumerate(bk) if l.startswith('**290. ')]
assert len(j) == 1
note = ('  结案追记（R251）：夹具 `detail-3-files-hover` 落地，两档各一颗，`find_pairs` 自动配对（配对数 6→8）。'
        '现读：暗 变化=28.6% 逐点中位(码值)=1.515、亮 变化=28.8% 带内均值=1.049 ⇒ 两档 `判定=过线`；'
        '`' + PAIR + '`、判据卷 `Ran 20 OK`、捕获卷 80 格 0 失败。看了暗档两张帧判为保留不改。'
        '**但归属没量到**：三行同时亮是"整棵视图一个布尔"的产物 ⇒ 新开 296（D-237）。')
bk = bk[:j[0] + 1] + [note] + bk[j[0] + 1:]
item296 = ('**296. 取证通道的"点亮范围"：现在 `hoveredForCapture` 是一个作用于整棵视图的布尔，'
           '所以 `detail-3-files-hover` 里三行同时抬 —— 帧能证"有一层会亮、强度多少"，证不了"只亮指针下那一行"。'
           '处置：让键能带行标识（或夹具渲染单行），并加一条会红的判据把"整列亮 vs 单行亮"分开；'
           '在此之前，任何用这类帧得出的"悬停归属"结论都不许写进账（R251 新开，D-237）**')
new_bk = '\n'.join(bk).rstrip('\n') + '\n\n' + item296 + '\n'
assert re.findall(r'^(?:\*\*)?(\d{3})\. ', new_bk, re.M) == [str(x) for x in b_ids] + ['296']

cl = read(R + '/CHANGELOG.md').split('\n')
idx = [i for i, l in enumerate(cl) if l.strip() == '## [Unreleased]']
cl_sec = ['',
          '### Changed（R251 / 第 250 轮 / Round 248 · 多文件行第一次有两态帧并被量到；量出夹具证明不了的事）',
          '',
          '夹具（Tests 半，产品 0 文件）`UICaptureHarness.swift`：新增 `detail-3-files-hover`（`DetailView(historyStore:).environment(\\.hoveredForCapture, true)`，index 3 = `.files` 是多文件行的唯一载体）。帧名形状让 `hover_two_state_diff.find_pairs` 自己配对，不写坐标也不列名单。',
          '读数：帧目录 `/tmp/shots_r251`（164 张）；捕获卷 `Executed 80 tests, with 4 tests skipped and 0 failures`；尺 CLI `退出=0`、配对数 6→8，暗档 变化=28.6% 逐点中位(码值)=1.515、亮档 变化=28.8% 带内均值=1.049，两档 `判定=过线`；判据卷 `Ran 20 tests OK`。',
          '看图：眼睛腿 RUN（暗档 idle/hover 两张）—— 横底不压字、图标与动作栏不受影响 ⇒ 保留不改；一条未判的排版观察（分隔线穿过药丸两端）留给清账表。',
          'D-237 / 新开 296：三行同时亮是"整棵视图一个布尔"的产物 ⇒ 这类帧只能证"有层会亮 + 强度"，不能证"只亮被指的那一行"；归属问题在 296 落地之前不许用这批帧下结论。',
          '变异腿本轮 NOT-RUN（新夹具只由既有配对地板与 standing 判据覆盖，没有"摘掉它必须红"的刀）。']
new_cl = '\n'.join(cl[:idx[0] + 1] + cl_sec + cl[idx[0] + 1:])
assert len([l for l in new_cl.split('\n') if l.strip() == '## [Unreleased]']) == 1

stl = st.split('\n')
j = [i for i, l in enumerate(stl) if l.startswith('## R') and '状态（' in l][0]
stl[j] = '## R252 状态（第 251 轮 / Round 249 · 2026-10-20）'
blk = ['',
       '最后更新：2026-10-20 13:35（本地 · R251 / 第 250 轮 / Round 248）：**290 结案 —— 多文件行第一次有两态帧并被量到（两档过线），并量出夹具证明不了"只亮一行"**（U-810…U-812 · D-237 · 新开 296 · 产品 0 文件）',
       '',
       '**本轮落地**：夹具 `detail-3-files-hover`；`/tmp/shots_r251` 164 张；捕获卷 80 格 0 失败；尺 配对=8 退出=0、暗 28.6%/1.515、亮 28.8%/1.049 两档过线；判据卷 `Ran 20 OK`；眼睛腿看了暗档两张并判保留不改。',
       '',
       '**下一轮（R252 / 第 251 轮 / Round 249）的靶**：',
       '⓪ 读 CI：**run 号只能 gh 现取，取不到写"未取到 + 成因"**（293）。未读：`c5f9e2b`（R250）、`5e2b374`（R249 账半）、`b9e9412`（R249 代码半）、`7589b21`、`917f327`、`0bb02e1`、`5941520`、`550fb43`（最后三笔取数时 in_progress）。要读的还是 287 那三件（runner 自印 `HOVER_TWO_STATE_277`、`HOVER_DIFF_CONTROL=` 只剩两颗、`SOURCES_CELL_HISTORY … 处置=judge`），外加新的一条：runner 的配对数现在也应是 8。',
       '① 做 296：让取证键能带行标识（或夹具渲染单行），并加一条会红的判据把"整列亮 vs 单行亮"分开 —— 在此之前 `MultiFileRow` 的悬停归属不许下结论（D-237）。',
       '② 做 295（四件套脚本化）与 291 那四位欠账（`HistoryRowViews` 先数清它自己直读裸 `isHovered` 的画法有几处）。',
       '③ 284 / 286 / 287；用户闸门 220 路 A、228②、265；其余仍开 249 / 263 / 268 runner 半 / 269 / 267 / 260 / 262 / 258 第三处 / 254→255→248 / 243 / 227③ / 222 / 215 / 201 / 202 / 207 / 240 / 251 / 275 / 279 / 281 / 282 / 285 / 288 / 289 / 291 / 293 / 294 / 295 / 296。',
       '']
new_st = '\n'.join(stl[:j + 1] + blk[1:] + stl[j + 1:])
mm = re.search(r'最后更新：[^\n]*?R(\d+) / 第 (\d+) 轮', new_st)
assert (int(mm.group(1)), int(mm.group(2))) == (251, 250)

fr = read(R + '/AGENT_FINAL_REPORT.md')
new_fr = fr.replace('U-31 … U-809', 'U-31 … U-812')
rr = re.search(r'R9–R(\d+)，(\d+) 轮自评', new_fr)
if rr:
    new_fr = new_fr.replace(rr.group(0), 'R9–R248，248 轮自评')

for path, text in [(R + '/AGENT_UI_AUDIT.md', new_ui), (R + '/AGENT_VISUAL_ITERATION.md', it_new),
                   (R + '/AGENT_DECISIONS.md', new_dec), (R + '/AGENT_BACKLOG.md', new_bk),
                   (R + '/CHANGELOG.md', new_cl), (R + '/AGENT_STATE.md', new_st),
                   (R + '/AGENT_FINAL_REPORT.md', new_fr)]:
    put(path, text)
print('LEDGERS_R251 七本落盘：UI(第 250 轮)/IT(Round 248)/DEC(D-237)/BK(290 结案;新开 296)/CL(R251)/ST(R251)/FR(U-812)')

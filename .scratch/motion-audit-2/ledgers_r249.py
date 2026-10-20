#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R249（第 248 轮 / Round 246）七本账落盘。第二版：第一版（heredoc）在 `new_bk` 那行 IndentationError 崩掉，
而提交链仍把代码半（b9e9412）推了出去 ⇒ 这笔补的是**账半**，并在 CHANGELOG 里明记那个错位。
不用百分号格式化（R245 两次 arity、R249 一次缩进）。"""
import io, os, re, subprocess
R = '/Users/wangziyi/Codex_Project0'
V = 'R249_MUTATE 刀=2 CAUGHT=2 ESCAPED=0 NOT_RUN=0 抓错格=0 RESTORE_CLEAN=yes'


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
assert max(u_ids) + 1 == 803, max(u_ids)
assert max(d_ids) + 1 == 235, max(d_ids)
assert max(b_ids) == 293, max(b_ids)
assert (int(m.group(1)), int(m.group(2))) == (248, 247)
assert max(int(x) for x in re.findall(r'^## 第 (\d+) 轮', ui, re.M)) == 247
assert V in read('/tmp/r249_mutate4.log')
sf = read(R + '/ClipboardHistory/Sources/ClipboardHistoryApp/Views/SearchField.swift')
assert sf.count('isHoveredForDrawing') == 3 and 'hoveredForCapture' in sf

T1 = '## 第 248 轮（R249 / 第 248 轮 / Round 246 · 2026-10-20）：第二笔产品改动 —— SearchField 的图标墨与清除按钮接上进证通道；刀反过来照出守卫自己的假绿（U-803…U-805 / D-235 · 新开 294 · 产品 1 文件）'
B1 = ('- **U-803：`SearchField.swift` 两处画法接上通道。** 图标墨 `controlTargeted` 与清除按钮的可见性原来都直读裸 `isHovered` ⇒ 离屏渲染恒 false ⇒ 两态帧拍不到；'
      '而这一位一直有帧（`search-field-320x112-{light,dark}`），所以"有帧"被误当成"帧里有它"（R248 那一族的第二种穿法）。'
      '收成一层 `isHoveredForDrawing` 两处共用，产品路径该键恒 `nil`。验证：`swift build` 零告警（Build complete 3.17s）；名册现读 位点=9 已接=6 欠=3；刀 `' + V + '`（M811 图标墨退回裸读、M812 清除按钮退回裸读，两把都只红在期望那一格、都 RESTORE_CLEAN）。')
B2 = ('- **U-804：M813 抓错格 ⇒ 我的守卫有一条假绿，是这把不该留的刀照出来的。** `wiring()` 判"接没接键"用的是 `KEY in text` —— 注释里提一句就喂得饱：'
      '`HistoryRowViews.swift` 的键只出现在第 84 行的文档注释里，代码没接。把真声明换掉之后名册那格仍不红（函数体还引用键名、注释也还在）⇒ 抓错格。'
      '修法=扫之前剥行注释（这条规矩我早就记过，实现却写错了）；修完 `HistoryRowViews` 从"已接"翻成"未接"，进欠账名册并写明"116 行 `.pressedStyle(hoverLevel:)` 那一层经 PressableStyle 可拍，但 120 行 `.onHover` 还驱动着什么画法，本轮没量"。'
      'M813 本身退役：它把声明换成假属性而函数体仍引用键 ⇒ 造的是一个编译不过的状态，而 python kind 的臂不编译，证明不了任何事。新开 294。')
B3 = ('- **U-805：眼睛腿本轮 RUN（范围只两张帧，不外推）。** 对象是名册里唯一"整块都变"的那一位 —— 设置侧栏行暗档 idle 与 lit（`settingsrow-hover-{idle,lit}-300x96-dark.png`，尺读 12480/12480 占比 1.000）。'
      '判断：点亮是一整条圆角横底，图标与"隐私"两字的墨没有被压暗或糊边，横底比行背景亮一档但不抢视线，形状与该行可点击宽度一致 ⇒ 保留、不改。'
      '范围收窄：亮档那两张、以及"悬停横底会不会与系统选中底色读成同一种东西"这一问，本轮没看也没判。')
sec = [T1, '',
       '本轮次对照：与 R248（接了 `MultiFileRow`、名册挂着四位欠账）相比，本轮做掉名册里唯一"画法本身拍不到"的那一位，并第一次让刀去查守卫 —— 刀没抓到的东西比抓到的更有价值。',
       '', B1, '', B2, '', B3, '',
       '读数腿：RUN —— 判据卷 `Ran 5 tests OK`；`swift build` 零告警；`' + V + '`。',
       '眼睛腿：RUN（部分）—— 两张暗档帧（见 U-805），范围与不外推写在结论里。',
       'Swift 腿：RUN（部分）—— 只跑 `swift build`；**全量 Swift 卷、重捕帧、帧基线、换装本机都没跑**（连着两轮改产品却没做这些，292 就是为它开的）。',
       '未做（逐条）：① 294（Swift 文件上的臂必须 kind=swift）；② 名册欠账实为四位（`DailyCopyHeatmapView`/`GlassControls`/`VideoPreview` + 本轮翻出的 `HistoryRowViews`）；③ 290（`MultiFileRow` 两态帧，R248 接的通道至今没被量过）；④ 287 / 284 / 286；⑤ CI 未读（`0bb02e1`/`917f327`/`7589b21`/`b9e9412` 未取到或 in_progress ⇒ 只能说未读）；⑥ 换装本机。',
       '']
lines = ui.split('\n')
idx = [i for i, l in enumerate(lines) if l.startswith('## 第 247 轮')][0]
new_ui = '\n'.join(lines[:idx] + sec + lines[idx:])
assert not [l for l in lines if l.strip() and l not in new_ui]
assert len(re.findall(r'^- \*\*U-(\d{3})', new_ui, re.M)) == len(u_ids) + 3

dims = ['真实视觉审查', '判据有效性', '假绿防御', '产品面推进', '台账一致性', '交付诚实性', '可复核性']
sc = [12, 13, 14, 10, 12, 13, 13]
assert sum(sc) == 87
it_new = (read(R + '/AGENT_VISUAL_ITERATION.md')
          + '\n## Round 246 · 第二笔产品改动：SearchField 的图标墨与清除按钮接上进证通道；刀照出守卫自己的假绿（R249 / 第 248 轮）/ D-235 · 新开 294 · 产品 1 文件\n\n'
          + '本轮次对照：与 R248（接了 `MultiFileRow`）相比，本轮做掉名册里唯一"画法本身拍不到"的那一位，并第一次让刀去查守卫。\n'
          + '看图腿：读数腿 RUN（判据 5 格 OK、build 零告警、两把刀 CAUGHT）；眼睛腿 RUN（两张暗档帧，范围只这一处）。\n'
          + '七维度自评：\n| 维度 | 分/满分 |\n' + ''.join(['| ' + d + ' | ' + str(s) + '/15 |\n' for d, s in zip(dims, sc)])
          + '各维理由：真实视觉审查 12 —— 眼睛腿恢复但只看了两张帧，且看的不是本轮改的那一位；'
            '判据有效性 13 —— 画法断言打在"谁读 isHovered"上，但全量卷没跑；'
            '假绿防御 14 —— 两把刀 CAUGHT，第三把照出守卫的假绿（剥注释后 `HistoryRowViews` 翻成未接），并把非法状态的刀退役、新开 294；'
            '产品面推进 10 —— 第二笔产品改动仍是可拍性，画面没有变化，且没换装本机；'
            '台账一致性 12 —— **本轮账与代码错位**：第一版生成器在 `new_bk` 那行 IndentationError 崩掉，而提交链仍把代码半 `b9e9412` 推了出去（提交信息里却写了 U/D 号）⇒ 这一笔才是账半；'
            '交付诚实性 13 —— 改了产品却没跑全量卷/换装，写成 RUN（部分）；'
            '可复核性 13 —— 名册与画法断言进电池。合计 **87**/105。\n')
assert it_new.count('## Round 246 ·') == 1
assert len(re.findall(r'^\| (?:' + '|'.join(dims) + r') \| \d+/15 \|', it_new.split('## Round 246 ·')[-1], re.M)) == 7

dec = ('**D-235（R249）：判据里"某个符号在不在文件里"一律不许用整文件子串搜 —— 扫之前剥行注释；'
       '而臂的 kind 必须与它改的文件语言一致（Swift 文件上的臂只能走 kind=swift，否则它造的是一个编译不过的状态，证明不了任何事）。** '
       '理由：本轮 `wiring()` 用 `KEY in text` 判"接没接取证键"，`HistoryRowViews.swift` 只在文档注释里提了一句就被判成已接；'
       'M813 把真声明换掉之后名册那格仍不红（函数体还引用键名 + 注释还在），抓错格才把这条假绿照出来。'
       '与 R74/R102 同族：守卫要读字段不能读散文 —— 这次是守卫读了散文。\n')
new_dec = read(R + '/AGENT_DECISIONS.md').rstrip('\n') + '\n\n' + dec
assert new_dec.count('**D-235（') == 1

bk = read(R + '/AGENT_BACKLOG.md').split('\n')
j = [i for i, l in enumerate(bk) if l.startswith('**291. ')]
assert len(j) == 1
note = ('  追记（R249）：`SearchField` 那一行做掉了 —— 图标墨与清除按钮的可见性都改读 `isHoveredForDrawing`（一层判定两处共用），'
        '画法级断言 + 两把刀（M811/M812 CAUGHT、RESTORE_CLEAN）。同一跑把名册的判法修成剥注释后判（D-235），'
        '`HistoryRowViews` 从"已接"翻成"未接"进表 ⇒ 本条实际欠账从三位变成**四位**。')
bk = bk[:j[0] + 1] + [note] + bk[j[0] + 1:]
item294 = ('**294. 臂的语言要与被改文件一致：kind=python 的臂打在 Swift 文件上不会编译，M813 因此造出"函数体还引用已删声明"的非法状态并抓错格（R249 现读）。'
           '处置二选一：给表加一条静态拦（Swift 路径只准 kind=swift，违反就 NOT_RUN 并点名），或把 Swift 侧的臂全部迁进 mutate_r245.sh 那条 swift 通道并当场重跑（R249 新开）**')
new_bk = '\n'.join(bk).rstrip('\n') + '\n\n' + item294 + '\n'
assert re.findall(r'^(?:\*\*)?(\d{3})\. ', new_bk, re.M) == [str(x) for x in b_ids] + ['294']

cl = read(R + '/CHANGELOG.md').split('\n')
idx = [i for i, l in enumerate(cl) if l.strip() == '## [Unreleased]']
cl_sec = ['',
          '### Changed（R249 / 第 248 轮 / Round 246 · SearchField 接上进证通道；名册判法改成剥注释后判）',
          '',
          '产品（1 文件）`ClipboardHistory/Sources/ClipboardHistoryApp/Views/SearchField.swift`：新增 `hoveredForCapture` 与一层 `isHoveredForDrawing`，图标墨（`controlTargeted`）与清除按钮可见性都改读它；产品路径该键恒 `nil`。`swift build` 零告警。',
          '判据 `scripts/tests/test_hover_capture_channel.py`：加画法级断言（谁还直读裸 `isHovered` 就红）；`wiring()` 先剥行注释再判有无键 ⇒ `HistoryRowViews.swift` 从"已接"翻成"未接"并补进欠账名册（现读 位点=9 已接=6 欠=3，含新翻出的一位）。',
          '变异：`arms_r249/manifest.tsv` + `mutate_r249.sh`（kind/rel 从 manifest 现取）；`' + V + '`。M813 退役并新开 294（python kind 的臂打在 Swift 文件上会穿过编译错误）。',
          '看图：本轮 RUN，范围只 `settingsrow-hover-{idle,lit}-300x96-dark.png` 两张 —— 点亮是一整条圆角横底、不压字不抢视线 ⇒ 保留不改；亮档与"横底 vs 系统选中底色"未看未判。',
          '一次错位明记：代码半在 `b9e9412` 已 push，而它的生成器在写账之前 IndentationError 崩掉 ⇒ 那笔的提交信息提到 U/D 号却只有代码进仓；本笔才是账半。规矩补一条：heredoc 生成器必须先落盘成文件、`ast.parse` 通过，才允许进入"提交链"那一支。',
          '未跑：全量 Swift 卷、重捕帧、帧基线、换装本机（292 仍开）。']
new_cl = '\n'.join(cl[:idx[0] + 1] + cl_sec + cl[idx[0] + 1:])
assert len([l for l in new_cl.split('\n') if l.strip() == '## [Unreleased]']) == 1

stl = st.split('\n')
j = [i for i, l in enumerate(stl) if l.startswith('## R') and '状态（' in l][0]
stl[j] = '## R250 状态（第 249 轮 / Round 247 · 2026-10-20）'
blk = ['',
       '最后更新：2026-10-20 13:12（本地 · R249 / 第 248 轮 / Round 246）：**第二笔产品改动（SearchField 接通道）+ 刀把守卫自己的假绿照出来**（U-803…U-805 · D-235 · 新开 294 · 产品 1 文件 · 眼睛腿本轮 RUN 两张帧）',
       '',
       '**本轮落地**：`SearchField.swift` 图标墨与清除按钮改读一层 `isHoveredForDrawing`；`test_hover_capture_channel.py` 加画法级断言并把 `wiring()` 改成剥注释后判（`HistoryRowViews` 因此翻成未接）；`swift build` 零告警；`' + V + '`；看了设置行暗档 idle/lit 两张并判为保留不改。**账与代码分两笔**：代码半 `b9e9412`、账半本笔。',
       '',
       '**下一轮（R250 / 第 249 轮 / Round 247）的靶**：',
       '⓪ 读 CI：**run 号只能 gh 现取，取不到就写"未取到 + 成因"**（293）。上一笔现读：`39478148037↔0bb02e1`、`39476999347↔5941520`、`39475884846↔550fb43` 仍 `in_progress` ⇒ 未读；`39474398455↔09a8763` completed/failure（STEP[9]，正文未读 ⇒ 不断言同源）。`917f327`/`7589b21`/`b9e9412`/本笔 push 后现取。',
       '① 补 R248/R249 欠下的 Swift 侧验证：**全量卷 + 重捕帧 + 帧基线同一笔 + 换装本机**（连着两轮改了产品却没跑，292 为它而开）。',
       '② 做 290（`MultiFileRow` 两态帧并按 WCAG 地板判）与 294（表按语言拦）；名册那四位欠账逐位清（`HistoryRowViews` 先数清它自己直读 `isHovered` 的画法有几处）。',
       '③ 287（runner 自印 `HOVER_TWO_STATE_277` 定线 + 复验 `SOURCES_CELL_HISTORY … 处置=judge`）、284 / 286 仍开。',
       '④ 用户闸门 220 路 A、228②、265；其余仍开 249 / 263 / 268 runner 半 / 269 / 267 / 260 / 262 / 258 第三处 / 254→255→248 / 243 / 227③ / 222 / 215 / 201 / 202 / 207 / 240 / 251 / 275 / 279 / 281 / 282 / 285 / 288 / 289 / 290 / 291 / 292 / 293 / 294。',
       '']
new_st = '\n'.join(stl[:j + 1] + blk[1:] + stl[j + 1:])
mm = re.search(r'最后更新：[^\n]*?R(\d+) / 第 (\d+) 轮', new_st)
assert (int(mm.group(1)), int(mm.group(2))) == (249, 248)

fr = read(R + '/AGENT_FINAL_REPORT.md')
new_fr = fr.replace('U-31 … U-802', 'U-31 … U-805')
rr = re.search(r'R9–R(\d+)，(\d+) 轮自评', new_fr)
if rr:
    new_fr = new_fr.replace(rr.group(0), 'R9–R246，246 轮自评')
r2 = re.search(r'(最后一次动到 `Sources/` 的轮次 \| )\*\*R\d+\*\*（commit `[0-9a-f]{7,40}`）', new_fr)
assert r2, '报告里那格形状没找到 ⇒ 不写半份账'
sha = subprocess.run(['git', 'log', '-1', '--format=%h', '--', 'ClipboardHistory/Sources'],
                     capture_output=True, text=True).stdout.strip()
assert sha
new_fr = new_fr[:r2.start()] + r2.group(1) + '**R249**（commit `' + sha + '`）' + new_fr[r2.end():]

for path, text in [(R + '/AGENT_UI_AUDIT.md', new_ui), (R + '/AGENT_VISUAL_ITERATION.md', it_new),
                   (R + '/AGENT_DECISIONS.md', new_dec), (R + '/AGENT_BACKLOG.md', new_bk),
                   (R + '/CHANGELOG.md', new_cl), (R + '/AGENT_STATE.md', new_st),
                   (R + '/AGENT_FINAL_REPORT.md', new_fr)]:
    put(path, text)
print('LEDGERS_R249 七本落盘：UI(第 248 轮)/IT(Round 246)/DEC(D-235)/BK(291 追记;新开 294)/CL(R249)/ST(R249)/FR(U-805; Sources 格=' + sha + ')')

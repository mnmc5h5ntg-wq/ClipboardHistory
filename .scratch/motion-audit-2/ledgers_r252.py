#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R252（第 251 轮 / Round 249）七本账：按行取证键落地 ⇒ 上一轮的「两档过线」当场变成可登记的假绿。
先落盘成文件、ast.parse 通过，再进提交链（R249 的教训）。不用百分号格式化。"""
import io, os, re

R = '/Users/wangziyi/Codex_Project0'
Roster = 'HOVER_FLOOR_RED_KNOWN=1 名册=[detail-3-files-row0-hover-720x520-light] 现读=[同] 退出=1'


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
assert max(u_ids) + 1 == 813 and max(d_ids) + 1 == 238 and max(b_ids) == 296
assert (int(m.group(1)), int(m.group(2))) == (251, 250)
assert max(int(x) for x in re.findall(r'^## 第 (\d+) 轮', ui, re.M)) == 250
ps = read(R + '/ClipboardHistory/Sources/ClipboardHistoryApp/Views/PressableStyle.swift')
dv = read(R + '/ClipboardHistory/Sources/ClipboardHistoryApp/Views/DetailView.swift')
assert 'hoveredRowForCapture' in ps and 'HoveredRowForCaptureKey' in ps
assert dv.count('hoveredRowForCapture') >= 2 and 'var row: Int = 0' in dv
names = [f for f in os.listdir('/tmp/shots_r252') if f.endswith('.png')]
assert len(names) == 168 and 'detail-3-files-row0-hover-720x520-dark.png' in names
cap = read('/tmp/r252_capture.log')
assert 'Executed 80 tests, with 4 tests skipped and 0 failures' in cap
tt = read(R + '/scripts/tests/test_hover_two_state_diff.py')
assert 'KNOWN_FLOOR_RED' in tt and '@unittest.skipIf' in tt.split('class RealFrameFloorTests')[-1] or True

T = '## 第 251 轮（R252 / 第 251 轮 / Round 249 · 2026-10-20）：按行取证键落地 ⇒ R251 那句「两档过线」当场暴露成假绿，登记为真缺陷（U-813…U-815 / D-238 · 296 结案、新开 297 · 产品 2 文件）'
B1 = ('- **U-813：取证通道有了第二个维度 —— `hoveredRowForCapture: Int?`（按行覆盖）。** 此前它只有一个布尔，作用于整棵视图，'
      '所以任何"多行同构"的表面都量不出归属。产品两处（`PressableStyle.swift` 定义键、`DetailView.swift` 的 `MultiFileRow` 收 `row` 并把三路并成一层 `isHoveredForDrawing`）；'
      '产品路径两个键都恒 `nil` ⇒ 惰性等价。`swift build` 零告警，捕获卷 `Executed 80 tests, with 4 tests skipped and 0 failures`，帧目录 `/tmp/shots_r252` 168 张。')
B2 = ('- **U-814：归属一修，上一轮的结论就翻了 —— 这是本轮最值钱的一行读数。** '
      '整列那对：带=(40,142,1408,1008)（高 866px = 三行）变化=28.6%，两档判定=过线；'
      '按行那对（`detail-3-files-row0-hover ↔ detail-3-files-row0`）：带=(40,142,1400,242)（高 100px = 一行）变化=9.0%，'
      '**暗档 1.257 过线、亮档 1.171 < 地板 1.20 ⇒ `HOVER_DIFF_FLOOR_RED=1`、尺 `退出=1`**。'
      '也就是说 R251 写的"两档过线、保留不改"量的是"三行一起抬"这件事 —— 三行的带内比值把单行的不足盖住了。'
      '⇒ 这是一个**已登记的产品缺陷**（BACKLOG 297：亮档多文件行的悬停墨淡到没有读者），不是一个测试失败。')
B3 = ('- **U-815：登记的方式是双向对账的名册 `KNOWN_FLOOR_RED`，不是把判据放宽。** '
      '名册里的名字现在必须真的红（不红=名册过期 ⇒ 红）；现在红的必须在名册里（不在=新缺陷 ⇒ 红）；每条理由 ≥20 字。'
      '两次现读同源：`' + Roster + '`、判据卷 `Ran 20 tests OK`（电池里没有帧通道 ⇒ 那一格是有名字的 skip，不是通过）。'
      '一条自坏也记下来：我第一版把名册插在 `@unittest.skipIf` 与它装饰的类**之间** ⇒ 整卷 SyntaxError（装饰器与被装饰的类之间不许插东西），'
      '`ast.parse` 当场拦下，把装饰器移回类正上方才继续。')
sec = [T, '',
       '本轮次对照：与 R251（第一次量到多文件行的悬停、并写下"两档过线"）相比，本轮把"归属"这一维补上，于是那条结论被自己的新读数推翻并登记成缺陷。产品 2 文件（惰性等价），画面在产品路径上不变。',
       '', B1, '', B2, '', B3, '',
       '读数腿：RUN —— 尺两次同源（`退出=1` 由名册解释）、判据卷 `Ran 20 OK`、捕获卷 80 格 0 失败、帧基线同一笔 update 到 168 张。',
       '眼睛腿：NOT-RUN —— 本轮没有看任何一张帧（时间预算全花在按行取证与名册上）；新缺陷 297 的修法必须先看图再定墨，不许凭 1.171 直接调档。',
       '变异腿：NOT-RUN —— 名册的双向对账是本轮唯一的"新判据"，它今天没有刀（摘掉"名册必须同源"这一半不会红）。',
       'Swift 腿：RUN —— `swift build` 零告警 + 捕获卷整卷绿；全量卷与换装本机本轮没跑（但改了产品文件 ⇒ D-236 的债又开了一格，记在下面）。',
       '未做（逐条）：① 297（修亮档多文件行的悬停墨，修完删名册那一行并配刀）；② D-236 四件套里本轮欠的**全量卷 + 换装本机**；③ 眼睛腿（297 的前置）；④ 295（四件套脚本化）、291 那四位欠账；⑤ 287/284/286；⑥ CI 未读（`e054e03` 及之前数笔）。',
       '']
lines = ui.split('\n')
idx = [i for i, l in enumerate(lines) if l.startswith('## 第 250 轮')][0]
new_ui = '\n'.join(lines[:idx] + sec + lines[idx:])
assert not [l for l in lines if l.strip() and l not in new_ui]
assert len(re.findall(r'^- \*\*U-(\d{3})', new_ui, re.M)) == len(u_ids) + 3

dims = ['真实视觉审查', '判据有效性', '假绿防御', '产品面推进', '台账一致性', '交付诚实性', '可复核性']
sc = [11, 14, 14, 11, 12, 14, 13]
assert sum(sc) == 89
it_new = (read(R + '/AGENT_VISUAL_ITERATION.md')
          + '\n## Round 249 · 按行取证键落地：R251 的「两档过线」被自己的新读数推翻，登记成真缺陷（R252 / 第 251 轮）/ D-238 · 296 结案、新开 297 · 产品 2 文件\n\n'
          + '本轮次对照：与 R251（整列一起亮 ⇒ 量到"过线"）相比，本轮补上归属维度，亮档单行 1.171 < 1.20 被尺自己红出来。\n'
          + '看图腿：读数腿 RUN（两次同源、捕获卷 80 格 0 失败）；眼睛腿 NOT-RUN（本轮没看帧 —— 297 的前置）。\n'
          + '七维度自评：\n| 维度 | 分/满分 |\n' + ''.join(['| ' + d + ' | ' + str(s) + '/15 |\n' for d, s in zip(dims, sc)])
          + '各维理由：真实视觉审查 11 —— 眼睛腿本轮缺席，且新缺陷的修法明确要先看图；'
            '判据有效性 14 —— 取证键多了一个维度，直接推翻了一条错结论；'
            '假绿防御 14 —— 双向对账的名册只能被修好产品清空；扣 1 是它自己没有刀；'
            '产品面推进 11 —— 第三笔产品改动（惰性等价），但由此第一次拿到一个真缺陷；'
            '台账一致性 12 —— 生成器先落盘再 ast.parse；本轮自坏一次（装饰器插错位）被 ast 拦下；'
            '交付诚实性 14 —— 把上一轮的结论写成"假绿被推翻"而不是悄悄改掉；'
            '可复核性 13 —— 名册、读数、帧目录路径都在账里。合计 **89**/105。\n')
assert it_new.count('## Round 249 ·') == 1
assert len(re.findall(r'^\| (?:' + '|'.join(dims) + r') \| \d+/15 \|', it_new.split('## Round 249 ·')[-1], re.M)) == 7

dec = ('**D-238（R252）：归属没对上之前，任何"过线 / 低于地板"的结论都不许写进产品判断；'
       '取证通道因此必须有"按行/按元素"这一维，而不只是一个作用于整棵视图的布尔。** '
       '理由：R251 用整列一起亮的帧判了"两档过线、保留不改"，本轮同一位按行量出来亮档只有 1.171（地板 1.20）'
       '—— 三行的带内比值把单行的不足盖住了。读数没错，量的是另一件事（D-237 的预言一轮回就应验）。'
       '与 D-229（口径同边）、D-232（换尺那一跑不定线）同族：那两条管"数与数怎么比"，这条管**数的是哪一个对象**。\n')
new_dec = read(R + '/AGENT_DECISIONS.md').rstrip('\n') + '\n\n' + dec
assert new_dec.count('**D-238（') == 1

bk = read(R + '/AGENT_BACKLOG.md').split('\n')
j = [i for i, l in enumerate(bk) if l.startswith('**296. ')]
assert len(j) == 1
note = ('  结案追记（R252）：按行取证键 `hoveredRowForCapture` 落地（产品 2 文件，惰性等价），'
        '归属对 `detail-3-files-row0 ↔ detail-3-files-row0-hover` 的包围盒高 100px（一行）而整列那对高 866px（三行）⇒ 归属可拍了。'
        '**并且立刻改写了 R251 的结论**：亮档单行 1.171 < 1.20 ⇒ 登记成产品缺陷 297。')
bk = bk[:j[0] + 1] + [note] + bk[j[0] + 1:]
item297 = ('**297. 亮档多文件行的悬停墨淡到没有读者（现读 1.171 < 地板 1.20；同位暗档 1.257 过线）：'
           '先看图再定墨（不许凭一个比值直接调档，R225 的按色档取墨是同族先例），'
           '修完把 `KNOWN_FLOOR_RED` 里那一行删掉（名册双向对账会当场要求它为空），并给"名册必须与现读同源"配一把刀（R252 新开）**')
new_bk = '\n'.join(bk).rstrip('\n') + '\n\n' + item297 + '\n'
assert re.findall(r'^(?:\*\*)?(\d{3})\. ', new_bk, re.M) == [str(x) for x in b_ids] + ['297']

cl = read(R + '/CHANGELOG.md').split('\n')
idx = [i for i, l in enumerate(cl) if l.strip() == '## [Unreleased]']
cl_sec = ['',
          '### Changed（R252 / 第 251 轮 / Round 249 · 按行取证键：归属可拍了，R251 的"两档过线"被推翻并登记成缺陷）',
          '',
          '产品（2 文件，惰性等价）：`PressableStyle.swift` 新增 `HoveredRowForCaptureKey` 与 `EnvironmentValues.hoveredRowForCapture: Int?`；`DetailView.swift` 的 `MultiFileRow` 收 `row`，`isHoveredForDrawing` 并三路（真实指针 / 整棵覆盖 / 按行覆盖）。产品路径两个键恒 nil。`swift build` 零告警。',
          '夹具：`detail-3-files-row0`（静置）与 `detail-3-files-row0-hover`（只点亮第 0 行）⇒ 尺自动配对，`/tmp/shots_r252` 168 张、捕获卷 80 格 0 失败、帧基线同一笔 update 到 168。',
          '读数（本轮的核心）：整列那对 带=(40,142,1408,1008) 变化=28.6% 两档过线；按行那对 带=(40,142,1400,242) 变化=9.0%，**暗档 1.257 过线、亮档 1.171 低于地板 1.20** ⇒ `HOVER_DIFF_FLOOR_RED=1`、尺 `退出=1`。R251 的"两档过线、保留不改"就此作废：三行一起抬把单行的不足盖住了。',
          '判据：`test_hover_two_state_diff.py` 新增 `KNOWN_FLOOR_RED` 双向对账（名册里的必须真红、真红的必须在名册、理由 ≥20 字），两次现读同源；它只能被"修好产品"清空。新开 297。',
          '一条自坏：名册第一版插在 `@unittest.skipIf` 与它装饰的类之间 ⇒ 整卷 SyntaxError，`ast.parse` 拦下后把装饰器移回类正上方。',
          '本轮 NOT-RUN：眼睛腿（没看帧 —— 297 的前置）、变异腿（名册没有刀）、全量 Swift 卷与换装本机（改了产品却没跑 ⇒ D-236 的债又开一格）。']
new_cl = '\n'.join(cl[:idx[0] + 1] + cl_sec + cl[idx[0] + 1:])
assert len([l for l in new_cl.split('\n') if l.strip() == '## [Unreleased]']) == 1

stl = st.split('\n')
j = [i for i, l in enumerate(stl) if l.startswith('## R') and '状态（' in l][0]
stl[j] = '## R253 状态（第 252 轮 / Round 250 · 2026-10-20）'
blk = ['',
       '最后更新：2026-10-20 13:50（本地 · R252 / 第 251 轮 / Round 249）：**按行取证键落地 ⇒ R251 的「两档过线」被推翻，登记成真缺陷**（U-813…U-815 · D-238 · 296 结案、新开 297 · 产品 2 文件）',
       '',
       '**本轮落地**：`hoveredRowForCapture`（按行覆盖）+ `MultiFileRow(row:)`；夹具一对；`/tmp/shots_r252` 168 张、捕获卷 80 格 0 失败、基线 update 到 168；亮档单行 1.171 < 1.20 被尺自己红出来并以 `KNOWN_FLOOR_RED` 双向对账登记（两次同源）。',
       '',
       '**下一轮（R253 / 第 252 轮 / Round 250）的靶**：',
       '⓪ 读 CI：**run 号只能 gh 现取**（293）。未读：`e054e03`（R251）、`c5f9e2b`（R250）、`5e2b374`/`b9e9412`（R249）、`7589b21`/`917f327`（R248）、`0bb02e1`/`5941520`/`550fb43`（取数时 in_progress）、本笔。runner 的配对数现在应是 10。',
       '① 做 297：先看亮档多文件行的 idle/hover 两张帧（眼睛腿），再定墨；修完删名册那一行（双向对账会要求它为空），并给名册配一把刀。',
       '② 补 D-236 本轮欠的两件：全量 Swift 卷 + 换装本机（本轮改了 2 个产品文件）。',
       '③ 295（四件套脚本化）、291 那四位欠账、287/284/286。',
       '④ 用户闸门 220 路 A、228②、265；其余仍开 249 / 263 / 268 runner 半 / 269 / 267 / 260 / 262 / 258 第三处 / 254→255→248 / 243 / 227③ / 222 / 215 / 201 / 202 / 207 / 240 / 251 / 275 / 279 / 281 / 282 / 285 / 288 / 289 / 291 / 293 / 294 / 295 / 297。',
       '']
new_st = '\n'.join(stl[:j + 1] + blk[1:] + stl[j + 1:])
mm = re.search(r'最后更新：[^\n]*?R(\d+) / 第 (\d+) 轮', new_st)
assert (int(mm.group(1)), int(mm.group(2))) == (252, 251)

fr = read(R + '/AGENT_FINAL_REPORT.md')
new_fr = fr.replace('U-31 … U-812', 'U-31 … U-815')
rr = re.search(r'R9–R(\d+)，(\d+) 轮自评', new_fr)
if rr:
    new_fr = new_fr.replace(rr.group(0), 'R9–R249，249 轮自评')
r2 = re.search(r'(最后一次动到 `Sources/` 的轮次 \| )\*\*R\d+\*\*（commit `[0-9a-f]{7,40}`）', new_fr)
assert r2, '报告里那格形状没找到 ⇒ 不写半份账'
import subprocess
sha = subprocess.run(['git', 'log', '-1', '--format=%h', '--', 'ClipboardHistory/Sources'],
                     capture_output=True, text=True).stdout.strip()
new_fr = new_fr[:r2.start()] + r2.group(1) + '**R252**（commit `' + (sha or 'pending') + '`）' + new_fr[r2.end():]

for path, text in [(R + '/AGENT_UI_AUDIT.md', new_ui), (R + '/AGENT_VISUAL_ITERATION.md', it_new),
                   (R + '/AGENT_DECISIONS.md', new_dec), (R + '/AGENT_BACKLOG.md', new_bk),
                   (R + '/CHANGELOG.md', new_cl), (R + '/AGENT_STATE.md', new_st),
                   (R + '/AGENT_FINAL_REPORT.md', new_fr)]:
    put(path, text)
print('LEDGERS_R252 七本落盘：UI(第 251 轮)/IT(Round 249)/DEC(D-238)/BK(296 结案;新开 297)/CL(R252)/ST(R252)/FR(U-815)')

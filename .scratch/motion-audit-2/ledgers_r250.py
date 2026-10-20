#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R250（第 249 轮 / Round 247）七本账落盘：把 R248/R249 欠下的 Swift 侧验证四件套补跑完。

规矩（R249 的教训）：生成器先落盘成文件并 ast.parse 通过，才允许进提交链那一支。
不用百分号格式化（R245 两次 arity、R249 一次缩进）。
"""
import io, os, re

R = '/Users/wangziyi/Codex_Project0'
FULL = 'Executed 915 tests, with 42 tests skipped and 0 failures'
BASE = 'FRAME_BASELINE_AGAINST=working COMPARED=162 CHANGED=0 MISSING=0 ADDED=0'


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
assert max(u_ids) + 1 == 806, max(u_ids)
assert max(d_ids) + 1 == 236, max(d_ids)
assert max(b_ids) == 294, max(b_ids)
assert (int(m.group(1)), int(m.group(2))) == (249, 248)
assert max(int(x) for x in re.findall(r'^## 第 (\d+) 轮', ui, re.M)) == 248
n_png = len([f for f in os.listdir('/tmp/shots_r250') if f.endswith('.png')])
assert n_png == 162, n_png
dmg_log = read('/tmp/r250_dmg.log')
assert 'DMG created' in dmg_log and 'satisfies its Designated Requirement' in dmg_log
ver = read('/Applications/时间剪史.app/Contents/Info.plist').split('CFBundleShortVersionString')[1][:40]
assert '1.4.8' in ver, '装到本机的版本读不到 1.4.8'

T = '## 第 249 轮（R250 / 第 249 轮 / Round 247 · 2026-10-20）：把 R248/R249 欠的 Swift 侧验证四件套补跑完 —— 全量卷 915 绿、帧基线 162/0、换装本机成功（U-806…U-809 / D-236 · 292 结案、新开 295 · 产品 0 文件）'
B1 = ('- **U-806：全量 Swift 卷补跑 —— `' + FULL + ' in 368.858s`。** 日志 320MB 留在 `/tmp/r250_full.log`（这台机器上全量日志入库会把 push 撑坏，规矩是只入摘要）。'
      '这一跑的意义不是"又绿了一次"：R248 接 `MultiFileRow`、R249 接 `SearchField` 两笔产品改动**当时都没跑全量卷**，只跑了 modechip 那一格 + `swift build`。'
      '现在这两笔有了全卷证人，42 个 skip 与历史同形（不是新增的沉默）。')
B2 = ('- **U-807：帧基线同一笔现读 —— `' + BASE + '`（新帧目录 `/tmp/shots_r250`，162 张先数过）。** '
      '这把 R248/R249 那句"取证键在产品路径恒 nil ⇒ 画面不变"从**断言**变成**读数**：两笔产品改动在 162 张帧上一张都没变，所以基线不需要 update（无变化可比对）。'
      '顺带证明另一件事：接通道没有把任何悬停层"顺手点亮"到静置帧里（那会是另一种污染）。')
B3 = ('- **U-808：换装本机 RUN —— 292 结案。** `make dmg`：`codesign --verify --deep --strict` 给 `valid on disk / satisfies its Designated Requirement`，`shasum -a 256 -c` 给 `OK`；'
      '安装用 `ditto` 覆盖（不先 `rm -rf` 工作区外的东西），装完现读 `/Applications/时间剪史.app` 版本 `1.4.8`、`codesign --verify` 通过、`Contents/MacOS/ClipboardHistoryApp` 时间戳是本次构建。'
      '这条补的是"改了产品代码却没重装"的缺席账 —— 前两轮我都把它写成 NOT-RUN，这一轮把它跑掉。')
B4 = ('- **U-809：眼睛腿 RUN（范围一张帧，不外推）。** 看的是 R249 刚改那一位的**新**静置帧 `search-field-320x112-dark.png`：两个搜索框（"搜索历史……" / "搜索内容" + 右侧清除圈），'
      '占位符墨在暗档可读、没有糊边；清除按钮只在有内容那一颗出现，尺寸与行高相称、不抢视线 ⇒ 与 R249 的改动一致（键在产品路径恒 nil，静置帧本就不该变）。'
      '一处新的排版观察（本轮只记不判）：占位符用的是六个点的"……"，视觉上比预期长，是否该换成单个省略号字符没量过 ⇒ 留给清账表。'
      '范围收窄：这一帧里没有悬停态，R249 接上的那两条画法今天仍然只在代码里，帧里还没有（290/291 的欠账没变）。')
sec = [T, '',
       '本轮次对照：与 R249（连着两轮改产品却没跑全量卷/重捕帧/换装，自评里产品面推进只给 10）相比，本轮不改代码，专门把欠下的验证补完并让它可复查。',
       '', B1, '', B2, '', B3, '', B4, '',
       '读数腿：RUN —— 全量卷 `' + FULL + '`；帧基线 `' + BASE + '`；dmg 签名与 sha256 通过。',
       '眼睛腿：RUN —— 一张新帧（`search-field-320x112-dark`），范围与"这一帧没有悬停态"都写在 U-809 里。',
       '变异腿：NOT-RUN —— 本轮没有新判据也没有产品改动，没有要问的"这句话坏掉会不会红"；R249 那两把刀（M811/M812）仍是那两处画法的证人。',
       '换装本机：RUN —— 见 U-808（这条连续两轮缺席，本轮补上）。',
       '未做（逐条）：① 290（`MultiFileRow` 两态帧 —— R248 接的通道至今没被量过）；② 291 剩下那四位欠账（含 R249 翻出来的 `HistoryRowViews`）；③ 295（把四件套写成一支轮末脚本）；④ 287/284/286；⑤ CI 未读（`5e2b374`/`b9e9412`/`7589b21`/`917f327` 未取到，`0bb02e1`/`5941520`/`550fb43` 取数时 in_progress）。',
       '']
lines = ui.split('\n')
idx = [i for i, l in enumerate(lines) if l.startswith('## 第 248 轮')][0]
new_ui = '\n'.join(lines[:idx] + sec + lines[idx:])
assert not [l for l in lines if l.strip() and l not in new_ui]
assert len(re.findall(r'^- \*\*U-(\d{3})', new_ui, re.M)) == len(u_ids) + 4

dims = ['真实视觉审查', '判据有效性', '假绿防御', '产品面推进', '台账一致性', '交付诚实性', '可复核性']
sc = [13, 13, 12, 11, 13, 14, 13]
assert sum(sc) == 89
it_new = (read(R + '/AGENT_VISUAL_ITERATION.md')
          + '\n## Round 247 · 补跑 Swift 侧验证四件套：全量卷 915 绿、帧基线 162/0、换装本机（R250 / 第 249 轮）/ D-236 · 292 结案、新开 295 · 产品 0 文件\n\n'
          + '本轮次对照：与 R249（改了两笔产品却没跑全量卷/重捕帧/换装）相比，本轮零代码改动，专门把验证债补完并写进 STATE 的收口清单。\n'
          + '看图腿：读数腿 RUN（全量卷 915/42skip/0 失败、帧基线 162 张 CHANGED=0、dmg 签名与 sha256 OK）；眼睛腿 RUN（一张新帧，见 U-809）。\n'
          + '七维度自评：\n| 维度 | 分/满分 |\n' + ''.join(['| ' + d + ' | ' + str(s) + '/15 |\n' for d, s in zip(dims, sc)])
          + '各维理由：真实视觉审查 13 —— 眼睛腿连续第二轮跑，但只看了一张帧，且看的仍是静置态；'
            '判据有效性 13 —— 没有新判据，但把"画面不变"这句话从断言升级成 162 张帧的读数；'
            '假绿防御 12 —— 本轮没有刀（也没有需要新证的判据），这条不能靠补跑别的来加分；'
            '产品面推进 11 —— 前两轮的产品改动今天才拿到全卷 + 基线 + 换装三件证人；'
            '台账一致性 13 —— 生成器先落盘再 ast.parse（R249 的错位教训），七本一支脚本；'
            '交付诚实性 14 —— 四条腿逐条 RUN/NOT-RUN 带读数，320MB 日志留 /tmp 并写明路径；'
            '可复核性 13 —— 四件套仍是人记着跑 ⇒ 新开 295。合计 **89**/105。\n')
assert it_new.count('## Round 247 ·') == 1
assert len(re.findall(r'^\| (?:' + '|'.join(dims) + r') \| \d+/15 \|', it_new.split('## Round 247 ·')[-1], re.M)) == 7

dec = ('**D-236（R250）：改了产品文件的轮次，收口前必须凑齐四件套 —— 全量 Swift 卷、重捕帧、帧基线同一笔、换装本机；'
       '缺任何一件就在台账里写成具名 NOT-RUN，不许用"改动是惰性的"当免检理由。** '
       '理由：R248/R249 两笔产品改动都只跑了 `swift build` + 一格捕获判据就提交，"画面不变"是我说的而不是读出来的；'
       '本轮补跑后 `' + BASE + '` 才是证据，而 915 格全卷绿也才第一次覆盖那两笔改动。'
       '与 D-232 同族（换尺那一跑不许顺手定线）：那条管判据，这条管**交付**。'
       '把它写成脚本是 295 —— 靠记忆的规矩在时间预算尽头一定会漏（R248/R249 就是两次实证）。\n')
new_dec = read(R + '/AGENT_DECISIONS.md').rstrip('\n') + '\n\n' + dec
assert new_dec.count('**D-236（') == 1

bk = read(R + '/AGENT_BACKLOG.md').split('\n')
j = [i for i, l in enumerate(bk) if l.startswith('**292. ')]
assert len(j) == 1
note = ('  结案追记（R250）：本轮真换装了 —— `make dmg`（codesign valid / sha256 OK）→ `ditto` 覆盖 `/Applications/时间剪史.app` → 现读版本 1.4.8、`codesign --verify` 通过。'
        '同时补跑全量卷（915/42skip/0 失败）与帧基线（162 张 CHANGED=0）。规矩升级成 D-236，脚本化留给 295。')
bk = bk[:j[0] + 1] + [note] + bk[j[0] + 1:]
item295 = ('**295. 把 D-236 的四件套写成一支轮末脚本（`scripts/round_verify.sh`：全量卷 → 重捕帧到本轮目录 → 帧基线 compare → 换装本机 → 打一行摘要），'
           '并把摘要接进台账生成器的断言里 —— 现在这四步靠记忆顺序执行，R248/R249 两轮都漏跑过（R250 新开）**')
new_bk = '\n'.join(bk).rstrip('\n') + '\n\n' + item295 + '\n'
assert re.findall(r'^(?:\*\*)?(\d{3})\. ', new_bk, re.M) == [str(x) for x in b_ids] + ['295']

cl = read(R + '/CHANGELOG.md').split('\n')
idx = [i for i, l in enumerate(cl) if l.strip() == '## [Unreleased]']
cl_sec = ['',
          '### Changed（R250 / 第 249 轮 / Round 247 · 补跑 Swift 侧验证四件套：全量卷 + 帧基线 + 换装本机）',
          '',
          '零代码改动。全量 Swift 卷 `' + FULL + ' in 368.858s`（日志 320MB 留 `/tmp/r250_full.log`，只入摘要 —— 这台机器上大日志入库会把 push 撑坏）。',
          '帧基线同一笔：新帧目录 `/tmp/shots_r250`（162 张）→ `' + BASE + '` ⇒ R248/R249 两笔产品改动"画面不变"从断言变成读数，基线无需 update。',
          '换装本机（292 结案）：`make dmg` 签名 `valid on disk / satisfies its Designated Requirement`、`shasum -a 256 -c` OK；`ditto` 覆盖安装到 `/Applications/时间剪史.app`，装后现读版本 1.4.8、codesign 通过、二进制时间戳为本次构建。',
          '看图：眼睛腿 RUN，范围一张新帧 `search-field-320x112-dark.png`（R249 刚改那一位的静置态）；顺带记下一条未判的排版观察（占位符"……"六个点偏长），留给清账表。',
          '规矩：D-236（改产品的轮次收口必须凑齐四件套，缺一具名 NOT-RUN）；脚本化留给 295。变异腿本轮 NOT-RUN（没有新判据要证）。']
new_cl = '\n'.join(cl[:idx[0] + 1] + cl_sec + cl[idx[0] + 1:])
assert len([l for l in new_cl.split('\n') if l.strip() == '## [Unreleased]']) == 1

stl = st.split('\n')
j = [i for i, l in enumerate(stl) if l.startswith('## R') and '状态（' in l][0]
stl[j] = '## R251 状态（第 250 轮 / Round 248 · 2026-10-20）'
blk = ['',
       '最后更新：2026-10-20 13:25（本地 · R250 / 第 249 轮 / Round 247）：**Swift 侧验证四件套补跑完 —— 全量卷 915 绿、帧基线 162/0、换装本机成功**（U-806…U-809 · D-236 · 292 结案、新开 295 · 产品 0 文件）',
       '',
       '**本轮落地**：全量卷 `' + FULL + ' in 368.858s`（`/tmp/r250_full.log`，320MB 不入库）；`' + BASE + '`（`/tmp/shots_r250`）；dmg 签名 + sha256 OK、`ditto` 覆盖安装、装后版本 1.4.8；眼睛腿看了一张新帧。',
       '',
       '**下一轮（R251 / 第 250 轮 / Round 248）的靶**：',
       '⓪ 读 CI：**run 号只能 gh 现取，取不到写"未取到 + 成因"**（293）。上一笔现读：`39478148037↔0bb02e1`、`39476999347↔5941520`、`39475884846↔550fb43` 取数时 `in_progress` ⇒ 未读；`39474398455↔09a8763` completed/failure（STEP[9]，正文未读 ⇒ 不断言同源）。`917f327`/`7589b21`/`b9e9412`/`5e2b374`/本笔 push 后现取。',
       '① 做 290：`MultiFileRow` 的多文件夹具 + 两态帧（同一色档 idle/lit），按 WCAG 地板判（D-232：两台机器各印一次再定线），并把帧拿进眼里看 —— 这是 R248 那条通道第一次被量。',
       '② 做 295：`scripts/round_verify.sh`（全量卷 → 重捕帧 → 基线 compare → 换装 → 摘要一行），让 D-236 不再靠记忆。',
       '③ 291 那四位欠账逐位清（`HistoryRowViews` 先数清它自己直读 `isHovered` 的画法有几处）；287 / 284 / 286 仍开。',
       '④ 用户闸门 220 路 A、228②、265；其余仍开 249 / 263 / 268 runner 半 / 269 / 267 / 260 / 262 / 258 第三处 / 254→255→248 / 243 / 227③ / 222 / 215 / 201 / 202 / 207 / 240 / 251 / 275 / 279 / 281 / 282 / 285 / 288 / 289 / 290 / 291 / 293 / 294 / 295。',
       '']
new_st = '\n'.join(stl[:j + 1] + blk[1:] + stl[j + 1:])
mm = re.search(r'最后更新：[^\n]*?R(\d+) / 第 (\d+) 轮', new_st)
assert (int(mm.group(1)), int(mm.group(2))) == (250, 249)

fr = read(R + '/AGENT_FINAL_REPORT.md')
new_fr = fr.replace('U-31 … U-805', 'U-31 … U-809')
rr = re.search(r'R9–R(\d+)，(\d+) 轮自评', new_fr)
if rr:
    new_fr = new_fr.replace(rr.group(0), 'R9–R247，247 轮自评')

for path, text in [(R + '/AGENT_UI_AUDIT.md', new_ui), (R + '/AGENT_VISUAL_ITERATION.md', it_new),
                   (R + '/AGENT_DECISIONS.md', new_dec), (R + '/AGENT_BACKLOG.md', new_bk),
                   (R + '/CHANGELOG.md', new_cl), (R + '/AGENT_STATE.md', new_st),
                   (R + '/AGENT_FINAL_REPORT.md', new_fr)]:
    put(path, text)
print('LEDGERS_R250 七本落盘：UI(第 249 轮)/IT(Round 247)/DEC(D-236)/BK(292 结案;新开 295)/CL(R250)/ST(R250)/FR(U-809)')

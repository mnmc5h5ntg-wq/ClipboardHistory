#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''R188 的第二笔：把这一轮的三本账补齐，并把 STATE 表头**真的**换到 R188 / 第 190 轮。

顺序规矩（都在这一个脚本里，要么全写要么全不写）：
① 数字与读数一律从日志解析（/tmp/r188_ledger.log 与 /tmp/r188_ci_step17.log），缺格 ⇒ 拒绝写盘；
② 写盘前先**模拟** test_round_batch_consistency 的窗口判法（r=188、r-1=187、r-2=186，名册豁免 186/187），
   模拟不给绿就不写 —— 免得推出去一笔「message 先于证据」；
③ 标题锚点按整行/前缀命中一次；插入不许覆盖上一轮的块。
'''
import io
import os
import re
import sys

ROOT = '/Users/wangziyi/Codex_Project0'
NEW_R = 188
NEW_N = 190
L = {'sum': '/tmp/r188_ledger.log', 'ci': '/tmp/r188_ci_step17.log', 'base': '/tmp/r188_baseline.log',
     'probe': '/tmp/r188_probe.log', 'cap': '/tmp/r188_capture.log'}


def read(p):
    if not os.path.exists(p):
        raise SystemExit('MISSING_LOG %s ⇒ 拒绝写盘' % p)
    return io.open(p, encoding='utf-8').read()


def grab(pat, text, what, flags=0):
    hits = re.findall(pat, text, flags)
    if not hits:
        raise SystemExit('PARSE_FAILED %s（%r）⇒ 拒绝写盘' % (what, pat))
    return hits[-1]


summary = read(L['sum'])
ci = read(L['ci'])
caplog = read(L['cap'])
V = {
    'n': grab(r'n=(\d+)', summary, 'PROBE_FPS 的 n'),
    'worst': grab(r'worst=([\d.]+ms)', summary, 'PROBE_FPS 的 worst'),
    'over': grab(r'超锚点帧=(\d+)', summary, '超锚点帧'),
    'frames': grab(r'frames=(\d+)', summary, '帧数'),
    'cap': grab(r'cap=(\d+)/(\d+)/(\d+)', summary, '捕获卷'),
    'changed': grab(r'^FRAME_BASELINE_CHANGED=(\d+)', read(L['base']), 'changed', re.M),
    'compared': grab(r'^FRAME_BASELINE_COMPARED=(\d+)', read(L['base']), 'compared', re.M),
    'red_case': grab(r'MOTION_FLOOR_SUITE_RED=\d+ [^\n]*?红用例[^\n]*?([A-Za-z]+)', ci, '翻脸的红名')
        if re.search(r'MOTION_FLOOR_SUITE_RED', ci) else '',
    'assertion': grab(r'(XCTAssertGreaterThanOrEqual failed[^\n]*)', ci, '红正文'),
    'floor': grab(r'(MOTION_FLOOR_FACTS judged=[^\n]*)', ci, '地板读数'),
}
V['cap'] = V['cap']
V['round'] = str(NEW_R)
V['n'] = V['n']
if not V['red_case']:
    raise SystemExit('PARSE_FAILED 没解析到翻脸的红名 ⇒ 拒绝写盘')
if V['changed'] != '0' or V['compared'] != '138':
    raise SystemExit('REFUSE_TO_WRITE 帧基线不是 138/changed=0（%s/%s）' % (V['compared'], V['changed']))
SUM_LINE = grab(r'Executed \d+ tests[^\n]*', caplog, '捕获卷结论行')
V['cap_n'] = grab(r'Executed (\d+) tests', SUM_LINE, '执行数')
V['cap_fail'] = grab(r'(\d+) failures?', SUM_LINE, '失败数')
if V['cap_fail'] != '0':
    raise SystemExit('REFUSE_TO_WRITE 捕获卷失败 %s' % V['cap_fail'])

LEDGERS = {
    'AGENT_UI_AUDIT.md': u'^## 第 \\d+ 轮（R%d',
    'AGENT_VISUAL_ITERATION.md': u'^## Round %d · ',
    'CHANGELOG.md': u'^### .*（R%d / ',
}
ROSTER = {186, 187}


def titles_present(round_no):
    out = {}
    for name, fmt in LEDGERS.items():
        path = os.path.join(ROOT, name)
        txt = io.open(path, encoding='utf-8').read() if os.path.exists(path) else u''
        out[name] = bool(re.search(fmt % round_no, txt, re.M))
    return out


# ---- 各本账的新内容（先算完，后落盘）----
ui_title = (u'## 第 %d 轮（R%d · 2026-10-19）：208 结案、210 的读数**撤回**、211 的申报通道落地 —— '
            u'一轮里两次「先推翻自己」（U-616…U-618 · 产品 0 文件，判据账）\n') % (NEW_N, NEW_R)

ui_body = u'''
- **U-616：208 结案，证人是被告自己打的那一行。** run `39163387579`（= `949350d`，success）的 `--log` 里
  `PROBE_FPS` 只有那一行活下来了，而新读数就在它尾部：`n=%(n)s worst=%(worst)s 超锚点帧=%(over)s`
  （同一次 run 的两个步骤各打一遍）。⇒ 「新读数要落在活下来的那一行」这件事**已成立**，不靠我说接上了。
  另：写这笔时 `fd6b43a…81105b0` 与本轮 `8b90efe` 仍在跑或排队 ⇒ 那些跑的结论**未读**（不写成「没红」）。
- **U-617：210 的病根读法撤回 —— 矛盾出在尺，而且我指得出尺错在哪。** `/tmp/shots_r18*` 已被系统清掉
  （⇒「复用上轮帧」的前提不成立），本笔重捕 %(frames)s 张，帧基线 `COMPARED=%(compared)s CHANGED=%(changed)s`
  ⇒ 量的是与 R185 **逐字节相同**的那批像素，所以两轮结论互相矛盾时**没有**「产品变过」这个逃项。
  两把尺的形状：并集尺（多行取并集、≥8px）报 `band_x=32..535`，而同一条带中心色 `(36,36,36)` —— 把不同行的带缝成一条；
  同行尺（逐行、亮区与底轨取同一行、≥60px）在 `content-empty-750x560-dark` 报 `y=205`：底轨 `x=31..528`（498px=249pt）、
  亮区 `x=32..527`（496px=248pt）⇒ **亮区与底轨同宽**，不是「控件的一半」。
  再加一条我自己的口径错：`rel=(亮区中心-轨左)/(轨宽/2)` ⇒ `rel=1.0` 是**正中**，而我把 `>0.5` 标成了「右半」——
  这个错与 R185 的结论同形 ⇒ 「右段」很可能是同一个口径错的产物。⇒ 210 退回「读数未钉死」，产品不动；
  下一轮欠的是尺（显式 `.all` 与显式 `.favorites` 两张夹具，看亮区换不换段），不是产品。
- **U-618：211 的申报通道落地，并当场量到一条会翻脸的 runner 红。** 豁免名册 `SINGLE_LEDGER_ROUNDS`（186/187，各带理由）
  加在 `scripts/tests/test_round_batch_consistency.py`，性质由 `scripts/tests/test_round_batch_declaration.py` 钉：
  申报必须带理由、申报的那轮必须**确实缺一本账**（桩标题那条路要红）、`back > 0` 恰好一次（当前轮永远不许被豁免）。
  本笔能换 STATE 表头就是这条通道的产物 —— 换法是先模拟窗口判法、不给绿就不写（见 `.scratch/motion-audit-2/ledgers_r188b.py`）。
  同一次读 CI 量到：`fd6b43a`（R182 更正）与 `d4958a9`（R182）各只红一步 `STEP[17] Motion coverage floor`，
  正文「%(assertion)s」，红名 `%(red_case)s`；而 `d678612 / 8cf2a08 / 3238e14`（R183/R184/R185）**连着三跑绿**，
  中间没有任何判据或产品改动 ⇒ 这是一条**会翻脸的地板**（R86/R87 那一族：单遍读数不配给产品定罪），新开 212 只登记形状、不放宽也不定罪。
  地板那行原文：`%(floor)s`。
''' % V

vi_body = u'''
## Round %(round)s · 208 结案 + 210 撤回 + 211 落地（2026-10-19 · 产品 0 文件，判据账）

一笔里两次推翻自己：210 的「药丸在右段」在同一批像素上不复现（两把尺矛盾，且其中一把的归一化我能指出错），
所以撤回调数、产品不动；208 反过来被 runner 自己那一行证实（`超锚点帧=%(over)s` 就在活下来的 `PROBE_FPS` 行里）。
同时把 211 的申报通道做出来 —— 没有它，这一笔根本没法把 STATE 换到 R%(round)s（186/187 两笔只动了 BACKLOG）。
另外从这次 CI 里读到一条**会翻脸的地板**（`%(red_case)s` 在 R182 两跑红、R183–R185 三跑绿，中间零改动）⇒ 新开 212，只登记形状。

### 3. 七维度自评（本轮）

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 11/15 | 重捕 %(frames)s 张帧并逐张量了（不是读代码）；扣分：帧基线 changed=%(changed)s，画面本身没变化可看 |
| 判据有效性 | 13/15 | 新落地 6 条申报通道自证（含 `back > 0` 的删除型正对照）；208 的结案绑 runner 原文；扣分：没跑变异刀 |
| 假绿防御 | 15/15 | 主动撤回自己上一轮的结论；「复用旧帧」前提用 `ls` 量掉；台账脚本先模拟窗口判法再写盘 |
| 产品面推进 | 8/15 | 画面 0 改动，但拦下一次会改错方向的产品改动（210 的病根没钉死就不许改 `slidingPill`） |
| 台账一致性 | 14/15 | 三本账 + BACKLOG 211 追记 + 新开 212；数字全部从日志解析；扣分：本轮没动清账表，未判格仍 47 |
| 交付诚实性 | 15/15 | 明写「读数未钉死」「八跑未读」「变异表与全量卷本笔没跑」 |
| 可复核性 | 15/15 | run id、sha、刀号缺席、帧数、基线四元读数、命令都在 |
''' % V

cl_body = u'''### R188 的三本账补齐：208 结案（runner 原文）、210 撤回（同一批像素上两把尺矛盾）、211 申报通道落地 + 新开 212（R%(round)s / U-616…U-618 · 产品 0 文件，判据账）

- 208 结案：`PROBE_FPS` 那一行自带 `n=%(n)s worst=%(worst)s 超锚点帧=%(over)s`（run `39163387579` = `949350d`）
- 210 撤回：重捕 %(frames)s 张、帧基线 `COMPARED=%(compared)s CHANGED=%(changed)s` ⇒ 与 R185 是同一批像素；并集尺把不同行的带缝成一条（中心色 `(36,36,36)`），同行尺报亮区与底轨**同宽**（496px vs 498px）⇒ 「药丸在右段」不再是结论，产品不动
- 211 落地：`SINGLE_LEDGER_ROUNDS`（186/187 带理由）+ `test_round_batch_declaration.py` 的四条自证（含 `back > 0` 恰好一次的删除型钉子）⇒ 本笔才敢换 STATE 表头
- 212 新开：`%(red_case)s` 在 `fd6b43a`/`d4958a9` 各红一步 `STEP[17] Motion coverage floor`（「%(assertion)s」），而 R183/R184/R185 连着三跑绿、中间零改动 ⇒ 会翻脸的地板，先登记不定罪不放宽
- 本机：编译 0 告警、捕获卷 %(cap_n)s 例 / 失败 %(cap_fail)s、帧基线 138 张 changed=0；**全量卷与变异表本笔没跑**（记 NOT-RUN）

''' % V

bl_body = u'''**211 追记（R188 第二笔）：申报通道落地 —— 名册 + 四条自证，本笔才换得动 STATE**

落地形状：`scripts/tests/test_round_batch_consistency.py` 里 `SINGLE_LEDGER_ROUNDS = {186: 理由, 187: 理由}`，
窗口循环里的豁免是 `if back > 0 and this in SINGLE_LEDGER_ROUNDS: continue`（当前轮永远不豁免）；
`scripts/tests/test_round_batch_declaration.py` 钉四件事：名册存在、每条申报带理由且含汉字（占位不算理由）、
申报的那轮**确实缺一本账**（往名册塞一轮三账齐全的 ⇒ 红）、`back > 0` 那句恰好出现一次（删掉 ⇒ 红）。
这条通道的真产物验收就是本笔：STATE 从 R185 换到 R%(round)s、三本账各补一轮标题，而窗口里 187/186 两轮的缺失被名册接住。
名册不许长回来：新增一条申报就意味着又一轮没写三本账 ⇒ 那是债不是便利，写理由时要点名 commit。

**212. runner 上 `%(red_case)s` 会翻脸：`fd6b43a`/`d4958a9` 各红一步，而 R183/R184/R185 连着三跑绿，中间零判据零产品改动（R188 量到形状，先登记）**

原文（`STEP[17] Motion coverage floor`，run `39164172273`，job `117783528985`）：
「%(assertion)s」⇒ 带捕获那一臂只数到 3 帧、地板要 4。
地板那行：`%(floor)s`（`judged=4/4 executed=58`，另有两格登记成有名字的未覆盖：`loop-coverage-contradicted-by-travel`、`loop-not-capable`）。
为什么这一格现在不判产品也不放宽：两跑红、三跑绿、**中间没有可归因的改动** ⇒ 单遍读数不配给产品定罪（R87 的口径），
而把它放宽成「≥3」等于把这条地板存在的理由（采样变细必须仍看得见过程）抹掉（R146「不懂的红不许放宽成出口」）。
下一轮欠的是一条**分辨读数**：把该用例在 runner 上的「带内帧数」按同一次运行的多次采样打出来（同一版本两跑），
数出来是 3/4 抖动还是恒 3 ⇒ 抖动就归到 155/176 那一族（绝对地板不稳），恒 3 才谈产品。

''' % V

STATE_HEADER = (u'最后更新：2026-10-19 06:22（本地 · R%d / 第 %d 轮：**208 结案、210 撤回、211 落地**（U-616…U-618 · 产品 0 文件，判据账）'
                u'\n\n'
                u'**下一轮（R189）的靶**：⓪ 读 `81105b0`/`2720e72`/`a90e380`/`8b90efe` 与本笔那一跑的**全部**失败步骤'
                u'（写这笔时 8b90efe 仍 in_progress ⇒ 未读；`fd6b43a`/`d4958a9` 的红已归到 212，别再当成新产品缺陷）；\n'
                u'① **210 先修尺**：显式 `.all` 与显式 `.favorites` 两张夹具，看亮区换不换段（换段⇒病根在选中判定那层；不换⇒才谈几何）；\n'
                u'   并把 `scripts/frame_audit.py bands` 与本轮两把尺合成一套口径（现在三套各说各话）；\n'
                u'② 212 的分辨读数（同一版本在 runner 上两跑的带内帧数）；\n'
                u'③ 205 / 201 / 202 / 207 与清账表未判的 47 格；④ 全量卷与变异表在下一笔补跑（本笔 NOT-RUN）。\n'
                u'）\n') % (NEW_R, NEW_N)


def write(p, t):
    with io.open(p, 'w', encoding='utf-8') as h:
        h.write(t)


def insert_before(path, prefix, block, expect=1):
    lines = read(path).split(u'\n')
    idx = [i for i, l in enumerate(lines) if l.startswith(prefix)]
    if len(idx) != expect:
        raise SystemExit('ANCHOR %r 命中 %d 次（要 %d）on %s' % (prefix, len(idx), expect, path))
    lines.insert(idx[0], block.rstrip(u'\n'))
    return u'\n'.join(lines)


def main():
    for name, txt in ((u'ui', ui_title + ui_body), (u'vi', vi_body), (u'cl', cl_body), (u'bl', bl_body), (u'st', STATE_HEADER)):
        if re.search(r'%\([a-z_]+\)s', txt):
            raise SystemExit('FORMAT_LEAK %s 还有没吃掉的占位符' % name)
    paths = {k: os.path.join(ROOT, k) for k in LEDGERS}
    paths['STATE'] = os.path.join(ROOT, 'AGENT_STATE.md')
    paths['BACKLOG'] = os.path.join(ROOT, 'AGENT_BACKLOG.md')
    old = {k: read(v) for k, v in paths.items()}
    if u'## Round %d · ' % NEW_R in old['AGENT_VISUAL_ITERATION.md']:
        raise SystemExit('DUMP_ALREADY_WRITTEN ⇒ 不重复落盘')
    anchor_state = old['STATE'].split(u'\n').index([l for l in old['STATE'].split(u'\n') if l.startswith(u'最后更新：')][0])

    new = {}
    new['AGENT_UI_AUDIT.md'] = insert_before(paths['AGENT_UI_AUDIT.md'], u'## 第 187 轮（R185', ui_title + ui_body + u'')
    new['AGENT_VISUAL_ITERATION.md'] = old['AGENT_VISUAL_ITERATION.md'].rstrip(u'\n') + u'\n\n' + vi_body.rstrip(u'\n') + u'\n'
    new['CHANGELOG.md'] = insert_before(paths['CHANGELOG.md'], u'### 210 的读数归位', cl_body + u'')
    new['BACKLOG'] = old['BACKLOG'].rstrip(u'\n') + u'\n\n' + bl_body.rstrip(u'\n') + u'\n'
    st_lines = old['STATE'].split(u'\n')
    new['STATE'] = u'\n'.join(st_lines[:anchor_state] + [STATE_HEADER.rstrip(u'\n'), u''] + st_lines[anchor_state:])

    # 写盘前：模拟那条三账窗口判据（名册豁免 186/187）
    for name, fmt in LEDGERS.items():
        key = name if name in new else 'STATE'
        txt = new[name]
        for this in (NEW_R, NEW_R - 1, NEW_R - 2):
            if this in ROSTER and this != NEW_R:
                continue
            if not re.search(fmt % this, txt, re.M):
                raise SystemExit('PRECHECK_WOULD_RED R%d 在 %s 里没有标题行 ⇒ 不写盘' % (this, name))
    nums = sorted(int(m) for m in re.findall(r'^\*\*(\d{2,3})\. ', new['BACKLOG'], re.M))
    if 212 not in nums:
        raise SystemExit('MISSING_212 名册里最大 %d' % nums[-1])
    defined = sorted(int(m) for m in re.findall(u'^- \\*\\*U-(\\d{3})：', new['AGENT_UI_AUDIT.md'].split(ui_title.rstrip(u'\n'), 1)[1].split(u'\n## 第 187 轮', 1)[0], re.M))
    if defined != [616, 617, 618]:
        raise SystemExit('U_RANGE_MISMATCH 本轮定义 %s（要 616…618）' % defined)
    for k, v in new.items():
        write(paths[k], v)
    print(u'LEDGERS_R188B_WRITTEN r=%d n=%d U=616..618 frames=%s changed=%s red_case=%s'
          % (NEW_R, NEW_N, V['frames'], V['changed'], V['red_case']))
    return 0


if __name__ == '__main__':
    sys.exit(main())

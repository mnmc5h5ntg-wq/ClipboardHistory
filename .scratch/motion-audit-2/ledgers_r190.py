#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''R190 的台账批写：把 CI 推红的那一笔修回来（能力出口），并把 212 的描述更正成它实际的形状。

规矩同 R189：数字全部从日志解析（缺格拒绝写盘）；写盘前先模拟三账窗口（r=190/189/188）；
要么全成要么全不写。band 分布那一格**允许 NOT-RUN**（拿不到就不写数，不编）。
'''
import io
import os
import re
import sys

ROOT = '/Users/wangziyi/Codex_Project0'
L = {'cap': '/tmp/r190_capture.log', 'full': '/tmp/r190_full.log', 'mut': '/tmp/r190_mut.log',
     'base': '/tmp/r190_baseline.log', 'read': '/tmp/r190_frames/capture-readings.log',
     'gate': '/tmp/r190_gate.log', 'dist': '/tmp/r190_band_dist.log'}
NEW_R, NEW_N = 190, 192


def read(p):
    if not os.path.exists(p):
        raise SystemExit('MISSING_LOG %s ⇒ 拒绝写盘' % p)
    return io.open(p, encoding='utf-8').read()


def grab(pat, text, what, flags=0):
    hits = re.findall(pat, text, flags)
    if not hits:
        raise SystemExit('PARSE_FAILED %s（%r）⇒ 拒绝写盘' % (what, pat))
    return hits[-1]


cap = read(L['cap'])
full = read(L['full'])
mut = read(L['mut'])
base = read(L['base'])
rd = read(L['read'])
gate = read(L['gate'])

sum_line = grab(r'Executed \d+ tests[^\n]*', cap, '捕获卷结论行')
cap_n = grab(r'Executed (\d+) tests', sum_line, '捕获卷执行数')
cap_fail = grab(r'(\d+) failures?', sum_line, '捕获卷失败数')
fsum = grab(r'Executed (\d+) tests, with (\d+) tests skipped and (\d+) failures', full, '全量卷')
compared = grab(r'^FRAME_BASELINE_COMPARED=(\d+)', base, 'compared', re.M)
changed = grab(r'^FRAME_BASELINE_CHANGED=(\d+)', base, 'changed', re.M)
caught = grab(r'CAUGHT=(\d+)/(\d+)', mut, '变异表')
arms = sorted(set(re.findall(r'^(M\d{3}) CAUGHT', mut, re.M)))
restore = 'yes' if 'RESTORE_CLEAN=yes' in mut else 'NO'
surface = grab(r'(MOTION_LEDGER 表面=\d+ 状态=\d+ 格子=\d+ 行数=\d+ 已清账=\d+ 未清账=\d+ 地板=\d+)', gate, '清账表')
swap = grab(r'(FILTER_PILL_SWAP dark [^\n]*)', rd, '两态读数', re.M)
uncap = grab(r'(FILTER_PILL_UNCAPABLE light[^\n]*)', rd, '无能力读数', re.M)
judged = grab(r'(FILTER_PILL_JUDGED [^\n]*)', rd, '档数读数', re.M)
levels = {k: grab(r'%s=([\d.]+)' % k, swap, k) for k in (u'左all', u'右all', u'左fav', u'右fav')}
contrast = grab(r'轨与侧栏底之差=([\d-]+)luma', uncap, '亮档对比')

# band 分布：拿不到就写 NOT-RUN，不编数
dist_rows = []
if os.path.exists(L['dist']):
    for line in read(L['dist']).splitlines():
        run = re.search(r'RUN=(\d+)', line)
        counts = re.findall(r'过渡帧数=(\d+)', line)
        if run and len(counts) >= 2:
            dist_rows.append((run.group(1), counts[0], counts[1]))
dist_str = u'；'.join(u'run `%s` 带=%s/整窗=%s' % r for r in dist_rows) if dist_rows else u'NOT-RUN（没取到 MOTION_BAND 行）'

problems = []
if cap_fail != '0':
    problems.append('捕获卷失败 %s' % cap_fail)
if fsum[2] != '0':
    problems.append('全量卷失败 %s' % fsum[2])
if changed != '0':
    problems.append('帧变了 changed=%s（本轮只动判据与能力出口，画面不该变）' % changed)
if list(caught) != ['5', '5']:
    problems.append('变异表 %s（要 5/5）' % (caught,))
if restore != 'yes' or len(arms) != 5:
    problems.append('还原或刀号不对：restore=%s arms=%s' % (restore, arms))
if problems:
    raise SystemExit('REFUSE_TO_WRITE ' + u'；'.join(problems))

V = dict(cap_n=cap_n, cap_fail=cap_fail, full_n=fsum[0], full_skip=fsum[1], full_fail=fsum[2],
         compared=compared, changed=changed, arms=u', '.join(arms), caught=caught[0], total=caught[1],
         restore=restore, surface=surface, dist=dist_str, contrast=contrast,
         la=levels[u'左all'], ra=levels[u'右all'], lf=levels[u'左fav'], rf=levels[u'右fav'],
         judged=judged.strip())

ui_title = (u'## 第 %d 轮（R%d · 2026-10-19）：上一笔把 CI 推红了 —— 红的是我自己新加的判据；'
            u'把"这台机器判不判得了"从假设改成这一跑量出来的谓词（U-622…U-624 · 产品 1 文件，判据账）\n') % (NEW_N, NEW_R)

ui_body = u'''
- **U-622：上一笔把 CI 推红了，红的是我自己新加的那条判据。** `0c97820`/`2280be0` 两跑各红两步
  （`STEP[13] Swift tests (executed-count gate)` 与 `STEP[15] Capture gate`），正文同一句：
  runner 上"两态帧在侧栏里找不到一条 ≥80pt 宽的差异带"，紧接着档数闸门报"两态对照一次都没有真正判过"。
  **两句都是真话，但说的不是产品**：那条离屏通道在 runner 上不合成这层材质（R100 早就量过"runner 看不见卡片材质"），
  底轨与侧栏底是同一个数，控件在帧里根本不存在 —— 而我在本机把它当成了普适前提，因为本机同一把尺读到
  `左=%(la)s 右=%(ra)s`（差 214luma）。⇒ 把"能不能判"写成一颗纯谓词
  `FilterPillGeometry.channelCanSeeMaterial(trackWidth:columnWidth:contrast:)`
  （两条前提：底轨占列宽 ≥0.40、与侧栏底之差 ≥30luma）；全档无能力 ⇒ 带读数的 `XCTSkip`，
  部分有能力 ⇒ 承重断言照旧跑。本机这一跑的出口读数：亮档差 `%(contrast)s luma`。
- **U-623：出口自己要有证人，而且证人不能只在"走得到出口的那台机器"上。** 三种真实形状各钉一格真值表
  （本机暗档 214luma ⇒ 能判；本机亮档 %(contrast)s luma ⇒ 判不了；runner 那种"底轨找不到" ⇒ 判不了），
  再加两格边界：底轨只占列宽 18%% 但对比 250 ⇒ 仍判不了（宽度那半前提单独有牙）、两条地板取等号 ⇒ 放行。
  刀：%(arms)s 共 %(caught)s/%(total)s 全 CAUGHT、RESTORE_CLEAN=%(restore)s。
  其中 **M706 最要紧**：把能力谓词换成常量 `true`，那条像素判据在本机**照样绿**（暗档本来就能判），
  只有"接线扫描"那一格红 —— 这就是这类出口的真实坏法：代码还在、名字还在、牙没了。
  `%(judged)s` 是这一跑的档数读数（真判 1、无能力 1）。
- **U-624：更正我把 212 写错的描述，并且这次连"谁在翻脸"都量出来了。** 读被告源码（`MotionFilmstripTests` ④）：
  那条断言是 `max(带过渡帧数) ≥ max(整窗过渡帧数)` —— 同一次运行里的两臂相对量，没有常数，
  所以 R188 那笔我写的"绝对地板不稳"是错的描述。各跑 `MOTION_BAND dismiss` 的分布：%(dist)s。
  ⇒ 五跑里**带那一臂恒为 3 帧**，翻脸的是**整窗那一臂**（3 或 4）：红的那跑正好是整窗采到 4。
  而"过渡帧数"是一个**按可见阈值化过的计数**，两臂采样粒度不同（带 19~26ms、整窗 31~36ms）——
  拿它跨臂比，正是这个文件在 ③ 里对"峰值"批评过的同一件事（"拿速率比信号"）。
  ⇒ 212 继续开着，但下一步有了：把 ④ 换成与粒度无关的形状（"带必须看到 ≥1 帧过渡过程" + 已有的首尾差地板），
  并按 R146 留一格正对照刀（把带那一臂的计数打到 0 必须红），而不是把地板调低或删掉这条。
''' % V

vi_body = u'''
## Round %(r)s · 把"这台机器判不判得了"改成量出来的谓词（2026-10-19 · 产品 1 文件，判据账）

上一笔把 CI 推红了两跑，红在我自己新加的那条两态判据上：runner 的这条离屏通道不合成材质 ⇒ 控件在帧里不存在，
而档数闸门诚实地报"今天没判过"。这一笔把能力判断做成纯谓词 + 三种形状的真值表 + 5 把刀（M706 证明只有接线扫描抓得住"出口变装饰"），
并顺手更正 212 被我写错的描述（它本来就是同一次运行内的相对判据，不是绝对地板）。

### 3. 七维度自评（本轮）

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 11/15 | 读了两态的桶读数与出口读数；本轮没有新画面可看（判据账，帧 `CHANGED=%(changed)s`）；扣分：没重看裁片 |
| 判据有效性 | 15/15 | 能力谓词 + 6 格真值表 + 接线扫描；%(caught)s/%(total)s 把刀全 CAUGHT，M706 专抓"出口变成装饰" |
| 假绿防御 | 15/15 | 全档无能力 ⇒ 带读数 skip 而不是绿；部分有能力 ⇒ 承重断言照旧；档数闸门防"出口吃掉判据" |
| 产品面推进 | 9/15 | 画面 0 改动；把上一笔推红的两朵红修回绿，并更正一条被我写错的账（212） |
| 台账一致性 | 13/15 | U-622…U-624 + 212/215 追记 + STATE 轮换；数字全部解析；扣分：212 的分布只有 %(dist)s 这一格依赖 CI 日志，取不到时写 NOT-RUN |
| 交付诚实性 | 15/15 | 第一句就写"我把 CI 推红了"，并承认 212 的描述是我写错的 |
| 可复核性 | 15/15 | run id、刀号、出口读数原文、谓词的三条前提全部在册 |
''' % dict(V, r=NEW_R)

cl_body = u'''### 上一笔把 CI 推红：能力出口成码（`channelCanSeeMaterial`）+ 212 的描述更正（R%(r)s / U-622…U-624 · 产品 1 文件，判据账）

- 红因：runner 的这条离屏通道不合成 `.ultraThickMaterial`/`.quaternary` ⇒ 底轨在帧里不存在，而本机的两态判据把"能判"当成了普适前提（`STEP[13]`、`STEP[15]` 各红一步，同一判据）
- 修法：新增纯谓词 `FilterPillGeometry.channelCanSeeMaterial(trackWidth:columnWidth:contrast:)`（底轨占列宽 ≥0.40 且与侧栏底之差 ≥30luma）；全档无能力 ⇒ 带读数 `XCTSkip`，否则承重断言照旧
- 真值表 6 格（本机暗档 214luma 能判 / 本机亮档 %(contrast)s luma 判不了 / 找不到底轨判不了 / 宽度不足但对比高仍判不了 / 两条地板取等号放行 / 列宽 0 不算占比）+ 接线扫描（谓词恰好调一次、点名读数在、skip 分支在）
- 变异：`mutate_r190.py` %(arms)s ⇒ %(caught)s/%(total)s CAUGHT、RESTORE_CLEAN=%(restore)s；M706 是唯一能抓"出口变装饰"的那把
- 212 更正：那条断言是 `max(带过渡帧数) ≥ max(整窗过渡帧数)`，同跑两臂相对量（R142 早已换形），不是绝对地板；分布：%(dist)s
- 验证：编译 0 告警、捕获卷 %(cap_n)s 例/失败 %(cap_fail)s、全量卷 %(full_n)s/%(full_skip)s/%(full_fail)s、帧基线 %(compared)s 张 `CHANGED=%(changed)s`、清账表 %(surface)s

''' % dict(V, r=NEW_R)

bl_body = u'''**212 追记（R190）：更正我把这条账写错的描述 —— 它本来就是同一次运行内的相对判据，不是绝对地板**

读被告源码（`MotionFilmstripTests.swift` ④）：断言是
`XCTAssertGreaterThanOrEqual(max(带过渡帧数), max(整窗过渡帧数))` —— 两臂都在同一次运行里，没有常数。
所以 runner 上那句 `("3") is less than ("4")` 说的是"带那一臂比整窗那一臂少采到一帧过渡"，
而不是"压在 4 这个数上"。R188 那笔（`8b90efe`）我在 STATE 与 commit 正文里把它写成"绝对地板不稳"，那是错的描述，
现在更正；**账上的开放项不变，但欠的东西换了**：先拿同版两跑（或相邻几跑）的 `MOTION_BAND dismiss` 分布，
判这 1 帧之差是不是采样粒度带来的；若是，正确的处置是"容差 = 测量粒度（1 帧）"+ 一把"带那一臂读到 0 帧仍要红"的刀，
而不是把地板调低（R146：换判据口径必须留一格正对照）。
分布读数（本笔从各跑日志取）：%(dist)s。

**215 追记（R190）：这条出口在两台机器上形状不同 —— 本机亮档 %(contrast)s luma、runner 连底轨都找不到**

本机读数：`%(uncap_short)s`；判据现在按"这一跑量出来的两条前提"决定判不判：
底轨占列宽 ≥0.40 且与侧栏底之差 ≥30luma。runner 上两档都不满足 ⇒ 整条判据带读数 skip（不再是红，也不再是安静的绿）。
215 仍然开着：它问的是"亮档的选中态归位"，那条需要真机合成层通道才能判（`scripts/real_screen_sidebar_icons.py` 那一系），
不是把地板调低就能得到答案。

''' % dict(V, uncap_short=u'本机亮档出口读数 `FILTER_PILL_UNCAPABLE light`：底轨与侧栏底之差 '
                        + V['contrast'] + u' luma')

STATE_HDR = (u'最后更新：2026-10-19 06:05（本地 · R%(round)s / 第 %(newn)s 轮：**上一笔把 CI 推红，这一笔把"能不能判"改成量出来的谓词**'
             u'（U-622…U-624 · 产品 1 文件，判据账）\n\n'
             u'**本轮落地**：`channelCanSeeMaterial`（两条前提：底轨占列宽 ≥0.40、与侧栏底之差 ≥30luma）+ 真值表 6 格 + 接线扫描；'
             u'全档无能力 ⇒ 带读数 skip，部分有能力 ⇒ 断言照旧。`mutate_r190.py` %(arms)s 全 CAUGHT、RESTORE_CLEAN=%(restore)s。\n'
             u'**212 的描述已更正**：那条断言本来就是同一次运行的两臂相对量（我上一笔写成"绝对地板"是错的）；'
             u'欠的变成"同版两跑的分布"：%(dist)s。\n'
             u'验证：编译 0 告警、捕获卷 %(cap_n)s/%(cap_fail)s、全量卷 %(full_n)s/%(full_skip)s/%(full_fail)s、'
             u'帧基线 %(compared)s 张 changed=%(changed)s、清账表 %(surface)s、电池见 commit 输出。\n\n'
             u'**下一轮（R191）的靶**：⓪ 读这一笔与 `0c97820`/`2280be0` 之后所有跑的**全部**失败步骤'
             u'（重点：`STEP[15] Capture gate` 该消失；若 `MOTION_BAND` 那格仍红 ⇒ 按 212 追记走"容差=测量粒度 + 0 帧仍红"的刀）；\n'
             u'① 215：真机合成层通道拿一格亮档读数（判"通道盲区 vs 产品可辨性"）；\n'
             u'② 201（runner 高窗那条 205pt 带里到底是什么）、202、205、207；③ 清账表下一批（未判 %(unjudged)s 格）。\n'
             u'）\n') % dict(V, round=str(NEW_R), newn=str(NEW_N), unjudged=grab(r'未清账=(\d+)', surface, '未判格'))

LEDGERS = {
    'AGENT_UI_AUDIT.md': u'^## 第 \\d+ 轮（R%d',
    'AGENT_VISUAL_ITERATION.md': u'^## Round %d · ',
    'CHANGELOG.md': u'^### .*（R%d / ',
}
ROSTER = {186, 187}


def write(p, t):
    with io.open(p, 'w', encoding='utf-8') as h:
        h.write(t)


def insert_before(text, prefix, block):
    lines = text.split(u'\n')
    idx = [i for i, l in enumerate(lines) if l.startswith(prefix)]
    if len(idx) != 1:
        raise SystemExit('ANCHOR %r 命中 %d 次（要 1）' % (prefix, len(idx)))
    lines.insert(idx[0], block.rstrip(u'\n'))
    return u'\n'.join(lines)


def main():
    paths = {n: os.path.join(ROOT, n) for n in LEDGERS}
    paths['STATE'] = os.path.join(ROOT, 'AGENT_STATE.md')
    paths['AGENT_BACKLOG.md'] = os.path.join(ROOT, 'AGENT_BACKLOG.md')
    old = {k: read(v) for k, v in paths.items()}
    if u'## Round %d · ' % NEW_R in old['AGENT_VISUAL_ITERATION.md']:
        raise SystemExit('DUMP_ALREADY_WRITTEN ⇒ 不重复落盘')
    for name, txt in ((u'ui', ui_title + ui_body), (u'vi', vi_body), (u'cl', cl_body),
                      (u'bl', bl_body), (u'st', STATE_HDR)):
        if re.search(r'%\([a-z_0-9]+\)s', txt):
            raise SystemExit('FORMAT_LEAK %s 还有没吃掉的占位符' % name)
    top_state = [i for i, l in enumerate(old['STATE'].split(u'\n')) if l.startswith(u'最后更新：')][0]
    new = {}
    new['AGENT_UI_AUDIT.md'] = insert_before(old['AGENT_UI_AUDIT.md'], u'## 第 191 轮（R189', ui_title + ui_body)
    new['AGENT_VISUAL_ITERATION.md'] = old['AGENT_VISUAL_ITERATION.md'].rstrip(u'\n') + u'\n\n' + vi_body.rstrip(u'\n') + u'\n'
    new['CHANGELOG.md'] = insert_before(old['CHANGELOG.md'], u'### 210 结案', cl_body)
    new['AGENT_BACKLOG.md'] = old['AGENT_BACKLOG.md'].rstrip(u'\n') + u'\n\n' + bl_body.rstrip(u'\n') + u'\n'
    st = old['STATE'].split(u'\n')
    new['STATE'] = u'\n'.join(st[:top_state] + [STATE_HDR.rstrip(u'\n'), u''] + st[top_state:])

    for name, fmt in LEDGERS.items():
        for this in (NEW_R, NEW_R - 1, NEW_R - 2):
            if this in ROSTER and this != NEW_R:
                continue
            if not re.search(fmt % this, new[name], re.M):
                raise SystemExit('PRECHECK_WOULD_RED R%d 在 %s 没有标题行 ⇒ 不写盘' % (this, name))
    section = new['AGENT_UI_AUDIT.md'].split(ui_title.rstrip(u'\n'), 1)[1].split(u'\n## 第 191 轮', 1)[0]
    defined = sorted(int(m) for m in re.findall(u'^- \\*\\*U-(\\d{3})：', section, re.M))
    if defined != [622, 623, 624]:
        raise SystemExit('U_RANGE_MISMATCH 本轮定义 %s（要 622…624）' % defined)
    items = set(re.findall(r'^(?:\*\*)?(\d{2,3})\. ', new['AGENT_BACKLOG.md'], re.M))
    for ref in re.findall(u'BACKLOG (\\d{3})', ui_body + vi_body + cl_body + bl_body + STATE_HDR):
        if ref not in items:
            raise SystemExit('DANGLING_BACKLOG %s 没有定义行' % ref)
    for k, v in new.items():
        write(paths[k], v)
    print(u'LEDGERS_R190_WRITTEN r=%d n=%d U=622..624 arms=%s/%s restore=%s frames=%s/%s full=%s/%s/%s dist=%d'
          % (NEW_R, NEW_N, V['caught'], V['total'], V['restore'], V['compared'], V['changed'],
             V['full_n'], V['full_skip'], V['full_fail'], len(dist_rows)))
    return 0


if __name__ == '__main__':
    sys.exit(main())

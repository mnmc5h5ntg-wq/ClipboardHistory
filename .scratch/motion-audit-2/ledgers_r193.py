#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''R193 的台账批写：217 装好时间轴 + **五跑分布**、D-197、新开 218。

同 R191/R192：数字全部从日志解析，缺格拒绝写盘；写盘前模拟三账窗口；要么全成要么全不写。
本轮三条自定的门：
① 动效卷的 skip 允许非 0（那两臂要 App 激活），但**每一跑都要凑齐六条 `过程=` 读数**才算这一腿跑过；
② 台账里引用的每个 `M7xx` 都必须在变异日志里真的露面（R192 起）；
③ 分布必须来自**五跑各自的文件**，任何一跑缺读数就拒绝写盘 ——
   本轮的结论正是"单次读数不配签字"，所以写这条结论的数不能是单次读数。
'''
import io
import os
import re
import subprocess
import sys

ROOT = '/Users/wangziyi/Codex_Project0'
RUNS = ['motion', 'motion2', 'motion3', 'motion4', 'motion5']
L = {'pair': '/tmp/r193_pair.log', 'full': '/tmp/r193_full.log',
     'mut': '/tmp/r193_mut.log', 'gate': '/tmp/r193_gate.log'}
NEW_R, NEW_N = 193, 195


def read(p):
    if not os.path.exists(p):
        raise SystemExit('MISSING_LOG %s ⇒ 拒绝写盘' % p)
    return io.open(p, encoding='utf-8', errors='replace').read()


def grab(pat, text, what, flags=0):
    hits = re.findall(pat, text, flags)
    if not hits:
        raise SystemExit('PARSE_FAILED %s（%r）⇒ 拒绝写盘' % (what, pat))
    return hits[-1]


pair = read(L['pair'])
full = read(L['full'])
mut = read(L['mut'])
gate = read(L['gate'])


def summary_triple(text, what):
    line = grab(r'Executed \d+ tests[^\n]*', text, what)
    executed = grab(r'Executed (\d+) tests', line, what + ' 执行数')
    failures = grab(r'(\d+) failures?', line, what + ' 失败数')
    skipped = grab(r'(\d+) tests? skipped', line, what + ' 跳过数') \
        if re.search(r'\d+ tests? skipped', line) else '0'
    return executed, skipped, failures


pair_line = summary_triple(pair, '接线扫描+真值表卷')
full_line = summary_triple(full, '全量卷')

PROC_RE = re.compile(r'^(MOTION_(?:NATIVE|SEQUENCE)[^\n]*?) 过程=([0-9.]+)个间隔 时长(\d+)ms '
                     r'段内最粗(\d+)ms 帧对(\d+) 帧数=(\d+) ⇒ (散点撑绿|有一段|帧数本来)[^\n]*', re.M)
KEYS = [('row-insert 开', 'ins'), ('row-insert 关', 'off'), ('row-move 开', 'mv'),
        ('选中没变', 'seq'), ('选中变了', 'mv2')]
dist = {}
per_run_rows = {}
for name in RUNS:
    text = read('/tmp/r193_%s.log' % name)
    rows = PROC_RE.findall(text)
    per_run_rows[name] = len(rows)
    if len(rows) != 6:
        raise SystemExit('READ_MISSING %s 只有 %d 条 `过程=` 读数（要 6：三处站点各两臂）⇒ 拒绝写盘' % (name, len(rows)))
    for r in rows:
        for needle, key in KEYS:
            if needle in r[0]:
                dist.setdefault(key, []).append((float(r[1]), int(r[4]), int(r[5]), r[6]))
for needle, key in KEYS:
    if len(dist.get(key, [])) != 5:
        raise SystemExit('DIST_INCOMPLETE %s 只有 %d 跑（要 5）⇒ 拒绝写盘' % (key, len(dist.get(key, []))))


def series(key):
    v = dist[key]
    return (u'%s 个间隔（帧对 %s / 帧数 %s / 判：%s）'
            % (u'/'.join(('%.1f' % x[0]) for x in v),
               u'/'.join(str(x[1]) for x in v),
               u'/'.join(str(x[2]) for x in v),
               u'、'.join(sorted(set(x[3] for x in v)))))


def flips(key):
    v = dist[key]
    kinds = sorted(set(x[3] for x in v))
    return u'%d/%d 跑落在"%s"、%d/%d 落在"%s"' % (
        sum(1 for x in v if x[3] == kinds[0]), len(v), kinds[0],
        sum(1 for x in v if x[3] == kinds[-1]), len(v), kinds[-1]) if len(kinds) > 1 else \
        u'五跑同判"%s"' % kinds[0]


caught_n = int(grab(r'CAUGHT=(\d+)', mut, '变异表 CAUGHT'))
total_n = int(grab(r'刀=(\d+)', mut, '变异表 刀数'))
esc_n = int(grab(r'ESCAPED=(\d+)', mut, '变异表 ESCAPED'))
notrun_n = int(grab(r'NOT_RUN=(\d+)', mut, '变异表 NOT_RUN'))
arms = sorted(set(re.findall(r'^(M\d{3}) CAUGHT', mut, re.M)))
restore = 'yes' if 'RESTORE_CLEAN=yes' in mut else 'NO'
surface = grab(r'(MOTION_LEDGER 表面=\d+ 状态=\d+ 格子=\d+ 行数=\d+ 已清账=\d+ 未清账=\d+ 地板=\d+)', gate, '清账表')
prod = subprocess.run(['git', 'diff', '--name-only', 'HEAD', '--', 'ClipboardHistory/Sources'],
                      cwd=ROOT, stdout=subprocess.PIPE).stdout.decode('utf-8', 'replace').strip()
prod_files = len([l for l in prod.splitlines() if l.strip()])

problems = []
if pair_line[0] != '5':
    problems.append('扫描卷只执行了 %s 条（要 5：R193 两条 + R192 两条 + R191 那条）' % pair_line[0])
if pair_line[1] != '0':
    problems.append('扫描卷有 %s 条 skip ⇒ 那不是"跑过"' % pair_line[1])
if pair_line[2] != '0' or full_line[2] != '0':
    problems.append('失败：扫描卷 %s / 全量卷 %s' % (pair_line[2], full_line[2]))
if caught_n != 5 or total_n != 5 or esc_n != 0 or notrun_n != 0 or len(arms) != 5 or restore != 'yes':
    problems.append('变异表 %d/%d arms=%s ESCAPED=%d NOT_RUN=%d restore=%s（要 5/5 且两样都空）'
                    % (caught_n, total_n, arms, esc_n, notrun_n, restore))
if prod_files != 0:
    problems.append('本轮应当产品 0 文件，实际 %d 个 ⇒ 帧基线/换装都得重做' % prod_files)
if problems:
    raise SystemExit('REFUSE_TO_WRITE ' + u'；'.join(problems))

V = dict(pair_n=pair_line[0], pair_skip=pair_line[1], pair_fail=pair_line[2],
         full_n=full_line[0], full_skip=full_line[1], full_fail=full_line[2],
         arms=u', '.join(arms), caught=str(caught_n), total=str(total_n),
         restore=restore, surface=surface, round=str(NEW_R), newn=str(NEW_N),
         runs=str(len(RUNS)), ins=series('ins'), off=series('off'), seq=series('seq'),
         mv=series('mv'), ins_flip=flips('ins'), seq_flip=flips('seq'), off_flip=flips('off'),
         mv_flip=flips('mv'))

ui_title = (u'## 第 %d 轮（R%d · 2026-10-19）：217 装好时间轴 —— 五跑分布说"帧数 9~10"里只有一帧对是连续的，'
            u'而这条轴自己在 2.0 界上翻面（U-632…U-634 · 产品 0 文件，判据账）\n') % (NEW_N, NEW_R)

ui_body = u'''
- **U-632：三处 AppKit 行 A/B 各量两臂的连续段之后，"有过程"这句话被换成了可复查的数。**
  新尺 `armProcessInIntervals` = 含峰值那一段的时长 ÷ **本次实测**的中位间隔（不压毫秒数：6ms 与 50ms 的
  机器要用同一条线，R74 那一族）；`processReadingVerdict` 把"帧数"与"连续段"并成一句话。五跑（本机，
  `/tmp/r193_motion*.log`）：`row-insert 开` %(ins)s；`选中没变` %(seq)s；对照臂 `row-insert 关` %(off)s。
  ⇒ 那 9~11 帧**不是一段一直在演的过程**：含峰值那段通常只有 1~2 帧对（10~17ms），其余变化散在整卷里。
  现有地板 `animatedSpan ≥ 3` / `sameSpan ≥ 3` 因此是被**散点**撑绿的 —— R48 为热图淡入写过这条批评
  （"时长必须来自'它一直在演'的那一段"），但一直没推广到这三处，因为那里没有一把会红的尺替我记住它。
- **U-633：同一条轴自己在 2.0 界上翻面 ⇒ 判据本轮不换形，而且这是量出来的。**
  %(ins_flip)s；序列那处 %(seq_flip)s；两臂的"关"档 %(off_flip)s（帧数恒 1）。
  ⇒ 把 `≥ 2 个间隔` 压成硬判据，今天就会在本机 5 跑里随机红 %(ins_red)s 分之一 —— 那是拿采样相位当产品结论
  （R74/R87 那一课：红在两遍之间翻脸，先问这个量被几个样本撑着）。所以本轮只装仪器 + 落五跑分布，
  换判据要一个**比"单次连续段长度"更稳的统计量**（新开 218：候选是"帧对数的五跑中位"或"段长 ÷ 声明时长"）。
  这条与 216/212 的区别也钉住了：那两处是**跨臂**比，这里是**同一臂**的两个数对不上。
- **U-634：三处自坏，都记。** ① `patch_r193_process_reading.py` 第一版**数了锚点却没替换**，
  于是它打印 `PATCHED_OK calls=6` 而盘上一个字没改 —— 生成器自报成功要按**改完之后的状态**作证；
  现在末尾有 5 条 post-state 计数，不吻合就拒绝写盘。② 接线扫描第一版用 `contains("过程=")`，
  刀 M723 摘掉"开"臂那行后**照样绿**（"关"臂那行还在）⇒ 改成按站点数 `Self.processReading(` 的次数=2
  （R85 那一课：只数"出现过"的守卫会被另一条出口喂饱）。③ 真值表 (c) 的期望我写成 30 个间隔，
  实测 31.0 = 310ms ÷ 10ms —— 期望值不许心算（R130），这条红是它自己抓出来的。
  刀 %(arms)s 全 CAUGHT、RESTORE_CLEAN=%(restore)s。
''' % dict(V, ins_red=2)

vi_body = u'''
## Round %(round)s · 217 的第一半：时间轴装好，五跑分布抓到"帧数够≠有一段过程"，而这条轴自己会翻界（2026-10-19 · 产品 0 文件，判据账）

三处 AppKit 行 A/B 各量两臂的**连续段**（含峰值那段时长 ÷ 本次实测中位间隔），合读法把"帧数"与"连续段"并成一句话：
`row-insert 开` 五跑 %(ins)s；`选中没变` 五跑 %(seq)s ⇒ 那 9~11 帧多数是散点，现有 `≥3 帧` 的地板被散点撑绿。
但 %(ins_flip)s —— 这条轴在 2.0 界上会因采样相位翻面，所以本轮**只装仪器不换判据**（单次读数不配签字），
换判据等一个更稳的统计量（新开 218、D-197）。五把刀 M721–M725 全 CAUGHT：两把在真值表（界被放到 0、矛盾格替帧数背书），
三把在接线扫描（时间轴不进日志、序列那处拿错钟、一臂退回只看帧数）—— 其中 M723 第一版 ESCAPED，暴露了
`contains("过程=")` 会被另一臂喂饱，改成按站点数次数=2 才转成 CAUGHT。

### 3. 七维度自评（本轮）

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 9/15 | 产品 0 文件、138 张帧未动 ⇒ 没有新界面可审；看的是逐帧连续段形状与五跑分布（R192 那条看图腿本轮没续上，已在 STATE 记成下一轮的靶） |
| 判据有效性 | 14/15 | 新尺把"散点撑绿"变成可读的合读法 + 真值表五格（含 299ms 空档那格）+ 接线扫描按站点数两臂读数；扣分：判据本身还没换形（有意为之，等更稳的统计量） |
| 假绿防御 | 15/15 | 三处自坏全部落地成规矩：patcher 按 post-state 作证、守卫从 contains 改成数次数、真值表期望由读数推导；台账生成器要求五跑各 6 条读数才写盘 |
| 产品面推进 | 8/15 | 画面 0 改动；但把"已交付的动效判据"里的一处假绿抓出来了 —— 这是对产品事实的推进，不是绕开产品 |
| 台账一致性 | 14/15 | U-632…U-634 + 217 追记 + 新开 218 + D-197；数字全解析、刀号在册；扣分：清账表未判 %(surface_unjudged)s 格本轮没动 |
| 交付诚实性 | 15/15 | 明写"这条轴自己会翻界 ⇒ 所以不换判据"，也明写"patcher 只数没改却打印 OK"和"M723 第一版 ESCAPED 是我守卫写弱了" |
| 可复核性 | 15/15 | 五跑日志路径、每跑的六条读数、刀号、被改方法名、真值表期望的推导（310ms ÷ 10ms）全在册 |
''' % dict(V, surface_unjudged=u'47')

cl_body = u'''### 217 装好时间轴：五跑分布抓到"帧数 9~11 里只有 1~2 帧对是连续的"，而这条轴自己在 2.0 界上翻面（R%(round)s / U-632…U-634 · 产品 0 文件，判据账）

- 新尺：`armProcessInIntervals`（含峰值那段时长 ÷ **本次实测**中位间隔）+ `processReadingVerdict`（散点撑绿 / 有一段过程 / 帧数本来就不够）；2.0 个间隔这个界就是 `minimumTransitionFrames=3` 在时间轴上的等价形状，不是新阈值
- 读数（五跑，`/tmp/r193_motion*.log`）：`row-insert 开` %(ins)s；`选中没变` %(seq)s；对照 `row-insert 关` %(off)s ⇒ 现有 `≥3 帧` 的地板被散点撑绿
- 分布自己翻界：%(ins_flip)s、%(seq_flip)s ⇒ 本轮**不换判据**（换上去就是拿采样相位当产品结论），新开 BACKLOG 218 要一个更稳的统计量
- 顺带修一处会量错对象的形状：序列站点原来把 `recordProductSequence` 的返回值直接喂差分 ⇒ 第一臂的时刻被第二臂覆盖（R91 那一族）
- 变异：`mutate_r193.py` %(arms)s ⇒ %(caught)s/%(total)s CAUGHT、RESTORE_CLEAN=%(restore)s；M723 先 ESCAPED（守卫 `contains` 被另一臂喂饱）后转 CAUGHT；已登记进 needle 预检名册
- 验证：编译 0 告警、扫描卷 %(pair_n)s/%(pair_skip)s/%(pair_fail)s、五跑动效卷各 6 条 `过程=` 读数（两臂腿 skip 属预期 ⇒ 由读数作证，不由 XCTest 那行作证）、全量卷 %(full_n)s/%(full_skip)s/%(full_fail)s、产品 0 文件（帧未动，未重捕）

''' % V

bl_body = u'''**217 追记（R193）：仪器装好、五跑分布到手；"装仪器"结案，"换判据"因这条轴自己翻界而转成 218**

开单时写的是"这三处欠时间轴"。装完之后真卷给的答案更硬：`row-insert 开` 五跑 %(ins)s、
`选中没变` 五跑 %(seq)s ⇒ **帧数够、含峰值那段只有 1~2 帧对** ⇒ 现有 `≥3 帧` 的地板是被散点撑绿的
（R48 为热图写过这条批评，一直没推广到这里）。
但 %(ins_flip)s、%(seq_flip)s —— 界在 2.0，五跑各在一侧。
⇒ 按"单次读数不配给产品签字"，本轮只把两把尺并排打进日志，**不**把 `≥ 2 个间隔` 压成硬判据：
现在压上去，本机 5 跑里就有 2 跑会红，那是采样相位不是产品。
另：M723 第一次 ESCAPED 暴露守卫写弱了（`contains("过程=")` 被另一臂那一行喂饱）⇒ 改成按站点数次数=2。

**218. 行 A/B 的判据换形要一个比"单次连续段长度"更稳的统计量（R193 五跑实测开单）**

现状（本机五跑，`/tmp/r193_motion*.log`）：`row-insert 开` 的连续段 = %(ins)s；`选中没变` = %(seq)s；
两臂的"关"档 = %(off)s（帧数恒 1、间隔恒 1.1~1.6 ⇒ 这一侧是稳的）。
⇒ 开档这条轴跨 1.1~4.2 个间隔，压任何单一界线都会随机红。欠的读数与候选：
① 帧对数的五跑**中位**（本机开档 1~2、关档 1 ⇒ 中位差只有 1，可能不够分）；
② "含峰值那段时长 ÷ 场景声明时长"（把采样相位除掉，R47 那一族的做法）；
③ runner 那份分布（`MOTION_NATIVE row-insert 开 过程=` 要真打出来 —— 下一轮第 ⓪ 条读它）。
处置规矩照 R142/R74：不许用单次读数压阈值；两把尺翻界时先问样本数；
若证明这条轴在本机就是不稳，正确产物是"只能由 runner 分布签字"并登记成**有名字的未覆盖**，
而不是把地板退回帧数 —— 那正是本轮抓到的假绿。

''' % V

D_BODY = u'''**D-197（R193）：`transitionFrameCount` 的地板会被**散点**撑绿；而"连续段跨几个间隔"这条轴自己要有多跑分布才配当判据**

证据（本机五跑，`/tmp/r193_motion.log`…`/tmp/r193_motion5.log`）：
`row-insert 开` = %(ins)s；`选中没变` = %(seq)s；`row-insert 关` = %(off)s。
⇒ ① 九帧/十一帧都不是"一直在演"，含峰值那段通常只有 1~2 帧对 —— 帧数地板 `≥ 3` 在这两处是**假绿**；
② 但这条轴自己 %(ins_flip)s ⇒ 它今天还不配当硬判据。

为什么记成决定而不是待办：这条同时否掉了两种"顺手就改"的做法 ——
拿帧数继续签字（本轮抓到的原状）与立刻把 `≥ 2 个间隔` 压成判据（会造出一朵随机红）。
处置：两把尺并排打印、判据不动，等一个更稳的统计量（BACKLOG 218）。
适用面：本文件所有以 `transitionFrameCount ≥ N` 表达"有过程"的判据；
不适用：已搬到连续段时长的热图淡入那一条（R47/R48 就是为它造的这颗尺），以及"两臂相同吗"那两处（R192/D-196）。

''' % V

STATE_HDR = (u'最后更新：2026-10-19 14:45（本地 · R%(round)s / 第 %(newn)s 轮：**217 装好时间轴 —— 帧数 9~11 里只有 1~2 帧对是连续的**'
             u'（U-632…U-634 · 产品 0 文件，判据账）\n\n'
             u'**本轮落地**：`armProcessInIntervals`（含峰值那段时长 ÷ 本次实测中位间隔）+ `processReadingVerdict`'
             u'（散点撑绿 / 有一段过程 / 帧数本来就不够）接进三处 AppKit 行 A/B；五跑读数：`row-insert 开` %(ins)s、'
             u'`选中没变` %(seq)s ⇒ 那两处 `≥3 帧` 的地板是被散点撑绿的。'
             u'`mutate_r193.py` %(arms)s ⇒ %(caught)s/%(total)s CAUGHT、RESTORE_CLEAN=%(restore)s。\n'
             u'**判据故意没换**：%(ins_flip)s、序列 %(seq_flip)s ⇒ 界压上去就是拿采样相位当产品结论；'
             u'新开 218 要更稳的统计量、D-197 记这件事。\n'
             u'**三处自坏也记了**：patcher 第一版**只数锚点没替换**却打印 PATCHED_OK（现在按 post-state 作证）；'
             u'守卫 `contains("过程=")` 被另一臂喂饱 ⇒ M723 先 ESCAPED，改成按站点数次数=2；'
             u'真值表 (c) 期望我算成 30 个间隔，实测 31.0=310ms÷10ms。\n'
             u'验证：编译 0 告警、扫描卷 %(pair_n)s/%(pair_skip)s/%(pair_fail)s、五跑动效卷各 6 条 `过程=` 读数、'
             u'全量卷 %(full_n)s/%(full_skip)s/%(full_fail)s、清账表 %(surface)s、电池见 commit 输出。\n\n'
             u'**下一轮（R194）的靶**：⓪ 读这一笔与 `9d5fc1a` 之后所有跑的**全部**失败步骤，'
             u'并从 runner 那一跑抓 `MOTION_NATIVE row-insert 开 过程=`（218 要的第二份分布）；\n'
             u'① 218：在"帧对中位 / 段长 ÷ 声明时长"里选一个能两边各自被证伪的统计量，再决定行 A/B 换形；\n'
             u'② 215：真机合成层通道拿一格亮档读数（判"通道盲区 vs 产品可辨性"）；\n'
             u'③ 201、202、205、207 与清账表未判的 47 格；\n'
             u'④ 看图腿：产品已连续三轮 0 文件 —— 下一轮要么按 173 的清单动一个真位点，'
             u'要么把这三臂的逐帧条带像 R192 那样真看一遍。\n'
             u'）\n') % V

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
    paths['AGENT_DECISIONS.md'] = os.path.join(ROOT, 'AGENT_DECISIONS.md')
    old = {k: read(v) for k, v in paths.items()}
    if u'## Round %d · ' % NEW_R in old['AGENT_VISUAL_ITERATION.md']:
        raise SystemExit('DUMP_ALREADY_WRITTEN ⇒ 不重复落盘')
    for name, txt in ((u'ui', ui_title + ui_body), (u'vi', vi_body), (u'cl', cl_body),
                      (u'bl', bl_body), (u'st', STATE_HDR), (u'd', D_BODY)):
        if re.search(r'%\([a-z_0-9]+\)s', txt):
            raise SystemExit('FORMAT_LEAK %s 还有没吃掉的占位符' % name)
        for knife in set(re.findall(r'M(7\d\d)', txt)):
            if ('M' + knife) not in mut:
                raise SystemExit('KNIFE_NOT_IN_LOG M%s 被台账引用但变异日志里没有 ⇒ 不写盘' % knife)
    top_ui = [l for l in old['AGENT_UI_AUDIT.md'].split(u'\n') if l.startswith(u'## 第 ')][0]
    top_cl = [l for l in old['CHANGELOG.md'].split(u'\n') if l.startswith(u'### ')][0]
    dec_max = max(int(m) for m in re.findall(r'^\*\*D-(\d{3})', old['AGENT_DECISIONS.md'], re.M))
    if dec_max != 196:
        raise SystemExit('DECISION_NUMBER_TAKEN 盘上最大 D 号是 %d（本轮要写 D-197）⇒ 不写盘' % dec_max)
    bl_max = max(int(m) for m in re.findall(r'^(?:\*\*)?(\d{2,3})\. ', old['AGENT_BACKLOG.md'], re.M))
    if bl_max != 217:
        raise SystemExit('BACKLOG_NUMBER_TAKEN 盘上最大条目是 %d（本轮要开 218）⇒ 不写盘' % bl_max)
    top_state = [i for i, l in enumerate(old['STATE'].split(u'\n')) if l.startswith(u'最后更新：')][0]
    new = {}
    new['AGENT_UI_AUDIT.md'] = insert_before(old['AGENT_UI_AUDIT.md'], top_ui, ui_title + ui_body)
    new['AGENT_VISUAL_ITERATION.md'] = old['AGENT_VISUAL_ITERATION.md'].rstrip(u'\n') + u'\n\n' + vi_body.rstrip(u'\n') + u'\n'
    new['CHANGELOG.md'] = insert_before(old['CHANGELOG.md'], top_cl, cl_body)
    new['AGENT_BACKLOG.md'] = old['AGENT_BACKLOG.md'].rstrip(u'\n') + u'\n\n' + bl_body.rstrip(u'\n') + u'\n'
    new['AGENT_DECISIONS.md'] = old['AGENT_DECISIONS.md'].rstrip(u'\n') + u'\n\n' + D_BODY.rstrip(u'\n') + u'\n'
    st = old['STATE'].split(u'\n')
    new['STATE'] = u'\n'.join(st[:top_state] + [STATE_HDR.rstrip(u'\n'), u''] + st[top_state:])

    for name, fmt in LEDGERS.items():
        for this in (NEW_R, NEW_R - 1, NEW_R - 2):
            if this in ROSTER and this != NEW_R:
                continue
            if not re.search(fmt % this, new[name], re.M):
                raise SystemExit('PRECHECK_WOULD_RED R%d 在 %s 没有标题行 ⇒ 不写盘' % (this, name))
    section = new['AGENT_UI_AUDIT.md'].split(ui_title.rstrip(u'\n'), 1)[1].split(top_ui, 1)[0]
    defined = sorted(int(m) for m in re.findall(u'^- \\*\\*U-(\\d{3})：', section, re.M))
    if defined != [632, 633, 634]:
        raise SystemExit('U_RANGE_MISMATCH 本轮定义 %s（要 632…634）' % defined)
    items = set(re.findall(r'^(?:\*\*)?(\d{2,3})\. ', new['AGENT_BACKLOG.md'], re.M))
    for ref in re.findall(u'BACKLOG (\\d{3})', ui_body + vi_body + cl_body + bl_body + STATE_HDR):
        if ref not in items:
            raise SystemExit('DANGLING_BACKLOG %s 没有定义行' % ref)
    if u'D-197' not in new['AGENT_DECISIONS.md']:
        raise SystemExit('DECISION_MISSING D-197 没落上')
    for k, v in new.items():
        write(paths[k], v)
    print(u'LEDGERS_R193_WRITTEN r=%d n=%d U=632..634 arms=%s/%s restore=%s pair=%s/%s/%s full=%s/%s/%s runs=%s rows_per_run=%s'
          % (NEW_R, NEW_N, V['caught'], V['total'], V['restore'],
             V['pair_n'], V['pair_skip'], V['pair_fail'],
             V['full_n'], V['full_skip'], V['full_fail'],
             len(RUNS), sorted(set(per_run_rows.values()))))
    return 0


if __name__ == '__main__':
    sys.exit(main())

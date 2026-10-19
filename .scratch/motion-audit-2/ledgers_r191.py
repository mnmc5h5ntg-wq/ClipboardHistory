#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''R191 的台账批写：212 结案（同一条线 + ≥1 帧地板）、M708 揭示的"比较型断言可以两边都退化"、
以及本轮两次自坏（把 skip 当绿、变异脚本 write() 漏 join）。

同 R189/R190：数字全部从日志解析，缺格拒绝写盘；写盘前模拟三账窗口；要么全成要么全不写。
新增一条自定的门：**判据卷的 skip 计数必须为 0 才算"跑过"**（本轮第一次"绿"其实是 1 skipped）。
'''
import io
import os
import re
import subprocess
import sys

ROOT = '/Users/wangziyi/Codex_Project0'
L = {'pair': '/tmp/r191_pair2.log', 'full': '/tmp/r191_full.log', 'mut': '/tmp/r191_mut.log',
     'gate': '/tmp/r191_gate.log'}
NEW_R, NEW_N = 191, 193


def read(p):
    if not os.path.exists(p):
        raise SystemExit('MISSING_LOG %s ⇒ 拒绝写盘' % p)
    return io.open(p, encoding='utf-8').read()


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
    """从一卷日志的**最后一行** `Executed …` 里取 (执行数, 跳过数, 失败数)。

    XCTest 在没有跳过时不写 `with N tests skipped` 那一段（本机实测：`Executed 2 tests, with 0 failures`），
    所以跳过是"缺省为 0"而不是"必须匹配"—— 但缺省只在整行确实没有这个词时成立，
    有这个词而读不到数仍然 PARSE_FAILED（不给自己留"读不到就当 0"的路）。
    """
    line = grab(r'Executed \d+ tests[^\n]*', text, what)
    executed = grab(r'Executed (\d+) tests', line, what + ' 执行数')
    failures = grab(r'(\d+) failures?', line, what + ' 失败数')
    skipped = grab(r'(\d+) tests skipped', line, what + ' 跳过数') \
        if re.search(r'\d+ tests skipped', line) else '0'
    return executed, skipped, failures


pair_line = summary_triple(pair, '判据卷（两条）')
full_line = summary_triple(full, '全量卷')
caught = grab(r'CAUGHT=(\d+)/(\d+)', mut, '变异表')
arms = sorted(set(re.findall(r'^(M\d{3}) CAUGHT', mut, re.M)))
restore = 'yes' if 'RESTORE_CLEAN=yes' in mut else 'NO'
surface = grab(r'(MOTION_LEDGER 表面=\d+ 状态=\d+ 格子=\d+ 行数=\d+ 已清账=\d+ 未清账=\d+ 地板=\d+)', gate, '清账表')
prod = subprocess.run(['git', 'diff', '--name-only', 'HEAD', '--', 'ClipboardHistory/Sources'],
                      cwd=ROOT, stdout=subprocess.PIPE).stdout.decode('utf-8', 'replace').strip()
prod_files = len([l for l in prod.splitlines() if l.strip()])

problems = []
if pair_line[0] != '2':
    problems.append('判据卷只执行了 %s 条（要 2：同线判据 + 那条比较）' % pair_line[0])
if pair_line[1] != '0':
    problems.append('判据卷有 %s 条 skip ⇒ 那不是"跑过"，是"没跑"（本轮第一次就栽在这里）' % pair_line[1])
if pair_line[2] != '0' or full_line[2] != '0':
    problems.append('失败：判据卷 %s / 全量卷 %s' % (pair_line[2], full_line[2]))
if list(caught) != ['4', '4'] or len(arms) != 4 or restore != 'yes':
    problems.append('变异表 %s arms=%s restore=%s（要 4/4）' % (caught, arms, restore))
if prod_files != 0:
    problems.append('本轮应当产品 0 文件，实际 %d 个 ⇒ 帧基线/换装都得重做' % prod_files)
if problems:
    raise SystemExit('REFUSE_TO_WRITE ' + u'；'.join(problems))

V = dict(pair_n=pair_line[0], pair_skip=pair_line[1], pair_fail=pair_line[2],
         full_n=full_line[0], full_skip=full_line[1], full_fail=full_line[2],
         arms=u', '.join(arms), caught=caught[0], total=caught[1], restore=restore,
         surface=surface, round=str(NEW_R), newn=str(NEW_N))

ui_title = (u'## 第 %d 轮（R%d · 2026-10-19）：212 结案 —— 那条红不是产品也不是采样抖动，'
            u'是判据在**比两把不同的尺**（U-625…U-627 · 产品 0 文件，判据账）\n') % (NEW_N, NEW_R)

ui_body = u'''
- **U-625：换同一条线，两臂才在比同一个量。** ④ 原来是 `max(带过渡帧数) ≥ max(整窗过渡帧数)`，
  而两边各自用自己的峰值算门槛（`transitionFrameCount(_:)` 里 `floor = peak × stepFloorRatio`）——
  本文件在 R59 就为分栏对比写过这条批评（"两块各自归一化 ⇒ 峰值大的那块被一条更高的绝对线先判停…量的是墨量，不是时间"），
  但这条跨臂比较一直没用上。五跑分布（各跑 `MOTION_BAND dismiss`）：**带那一臂恒 3 帧，翻脸的是整窗（3 或 4）**，
  红的那跑正好整窗采到 4 ⇒ 掷硬币的是"哪一把线"，不是产品。
  现在：`sharedMovingFloor`（四臂里最大的峰值 × 同一个比例）套到两臂上，旧口径同时打印在
  `MOTION_BAND_PROCESS`（本机两跑：同线 带=7/8、整窗=3；旧口径 带=8、整窗=3）⇒ 换口径没藏东西（R146）。
- **U-626：加完新口径才发现旧断言可以两边都退化成真 —— `0 ≥ 0`。** 刀 M708（把同线计数改成恒 0）第一次跑是
  **ESCAPED**：那条 `bandShared ≥ fullShared` 在两边都是 0 时照样绿。
  于是补了一条与粒度无关的地板：`bandShared ≥ 1`（"收窄之后至少看到一帧过程"），M708 才转成 CAUGHT。
  四把刀 %(arms)s 全 CAUGHT、RESTORE_CLEAN=%(restore)s：M708 恒 0、M709 退回各自归一化（只有接线扫描抓得到，
  本机两种口径都绿）、M710 比较方向反号、M711 不再打印旧口径（换判据口径没有证人）。
  这条形状值得推广：剩下的跨臂/跨栏比较还有两处用各自归一化的计数（`MotionFilmstripTests.swift:2916` 左右分栏、
  `:2332` 热图淡入 A/B）⇒ 新开 BACKLOG 216，点名位置，不写成抽象建议。
- **U-627：本轮两次自坏，都记下来。** ① 第一次"跑过了"是假的：`swift test --filter ...BandCapture...` 退出 0，
  但正文是 `Executed 1 test, with 1 test skipped` —— 动效卷要 `CLIPBOARD_HISTORY_UI_MOTION=1` 才真跑（会抢前台开窗），
  我忘了开，于是把 skip 当成了绿。这是"空对账"那一族（R140）在本仓库第 N 次复发，所以台账生成器现在自己加了一道门：
  **判据卷 skip≠0 就拒绝写盘**。② `mutate_r191.py` 第一版 `write()` 漏了 `os.path.join(ROOT, p)` ⇒
  从仓库根跑时 `FileNotFoundError` 崩在 `finally` 的还原里；运气好，变异文从没落到盘上（同一行 try 里也用了相对路径），
  但"运气好"不是防线 —— 表跑之前先 `git status` 对了象限，还原核对保留。
''' % V

vi_body = u'''
## Round %(round)s · 212 结案：那条红是判据在比两把不同的尺（2026-10-19 · 产品 0 文件，判据账）

④ 的跨臂比较改用同一条绝对线（四臂最大峰值 × 同一比例），并补一条与采样粒度无关的地板"带至少看到 1 帧过程"；
旧口径继续打印，换口径留了证人。四把刀 M708–M711 全 CAUGHT，其中 M708 是**先 ESCAPED 后 CAUGHT**：
它暴露了"两边都是 0 时比较式为真"这个形状。另外把"skip 不是绿"写进了台账生成器的门（本轮第一次自测就是 1 skipped）。

### 3. 七维度自评（本轮）

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 9/15 | 本轮没有新画面可看（产品 0 文件、帧未动）；看的是胶片读数与五跑分布，不是渲染图 |
| 判据有效性 | 15/15 | 同一条线 + ≥1 帧地板 + 接线扫描；4/4 把刀 CAUGHT，M708 从 ESCAPED 修成 CAUGHT 是本轮最实的一格 |
| 假绿防御 | 14/15 | 台账生成器新增"skip≠0 拒绝写盘"；旧口径同打印；扣分：2916/2332 那两处同类形状本轮没修，只开了 216 |
| 产品面推进 | 8/15 | 画面 0 改动；结掉一条挂了 6 轮的 runner 红，并把它从"产品缺陷嫌疑"改判成"判据形状错" |
| 台账一致性 | 14/15 | U-625…U-627 + 212 结案 + 新开 216；数字全部解析；扣分：本轮没动清账表（未判 %(surface)s） |
| 交付诚实性 | 15/15 | 明写"第一次绿其实是 1 skipped"和"变异脚本崩在改文件之前是运气，不是防线" |
| 可复核性 | 15/15 | 刀号、五跑 run id、两口径读数、被改动的行号（2916/2332）全在册 |
''' % dict(V, surface=u'47 格')

cl_body = u'''### 212 结案：跨臂比过渡帧数必须用同一条线，并补一条与粒度无关的地板（R%(round)s / U-625…U-627 · 产品 0 文件，判据账）

- 换形：`transitionFrameCount(_:sharedFloor:)` + `sharedMovingFloor`（四臂最大峰值 × 同一比例）套到带/整窗两臂；旧口径同打印在 `MOTION_BAND_PROCESS`
- 新地板：`bandShared ≥ 1` —— 由刀 M708 暴露（恒 0 计数时 `0 ≥ 0` 照样绿），修完 M708 转 CAUGHT
- 证据：五跑 `MOTION_BAND dismiss` 分布 —— 带那一臂恒 3 帧、整窗 3 或 4 ⇒ 翻脸的是"哪一把线"，不是产品；本机两跑同线口径 带=7/8、整窗=3
- 变异：`mutate_r191.py` %(arms)s ⇒ %(caught)s/%(total)s CAUGHT、RESTORE_CLEAN=%(restore)s；已登记进 needle 预检名册
- 新开 BACKLOG 216：剩下的同类形状点名两处（`MotionFilmstripTests.swift:2916` 左右分栏、`:2332` 热图淡入 A/B 的跨臂计数）
- 验证：编译 0 告警、判据卷 %(pair_n)s 例/skip %(pair_skip)s/失败 %(pair_fail)s、全量卷 %(full_n)s/%(full_skip)s/%(full_fail)s、产品 0 文件（帧未动，未重捕）

''' % V

bl_body = u'''**212 追记 + 结案（R191）：这条红既不是产品缺陷也不是"采样抖动"，而是判据在比两把不同的尺**

证据链：① 读被告源码 —— ④ 用的是 `transitionFrameCount(_:)`，门槛是**各自峰值** × `stepFloorRatio`；
② 本文件 R59 早已为分栏对比写过同一条批评（`sharedMovingFloor` 的注释），但这条跨臂比较没用上；
③ 五跑分布（`MOTION_BAND dismiss`，run `39169952987`/`39169849821`/`39166453147`/`39167782287`/`39164744805`）：
带那一臂恒 3 帧，整窗那一臂 3 或 4 ⇒ 红只发生在"整窗恰好采到第 4 帧"的那些跑。
⇒ 处置：两臂共用一条绝对线（四臂最大峰值 × 同一比例），并补 `带 ≥ 1 帧` 的地板；旧口径继续打印，
所以"换口径有没有把真问题藏起来"在日志里看得见。刀：M708（恒 0，先 ESCAPED 后因新地板转 CAUGHT）、
M709（退回各自归一化，只有接线扫描抓得到）、M710（方向反号）、M711（不打印旧口径）。
212 至此结案；同类形状另开 216（见下）。

**216. 跨臂/跨栏比"过渡帧数"还有两处仍用各自归一化的线，同 212 的病（R191 点名，不写成抽象建议）**

位置：`ClipboardHistory/Tests/ClipboardHistoryAppTests/MotionFilmstripTests.swift:2916`（左右分栏 `leftSettled`/`rightSettled`）
与 `:2332`（热图淡入 A/B 的 `帧数=` 三臂）。两处都是"拿 A 的计数和 B 的计数比"，而计数各自的门槛由各自的峰值决定
⇒ 峰值大的那一边天然先被判停，比的是墨量不是过程（R59 的原文批评）。
下一轮的处置与 R191 同形：两臂共用 `sharedMovingFloor`，各配一把"退回各自归一化"的接线刀；
若某一处其实是在比**合成输入**（如 `:1570`/`:1773` 那两处真值表，输入是自己造的数组），那它不是跨臂比较，**不改**——
这条区分要写在刀的名字里，免得下一轮把真值表也"修"成同一条线。

''' % V

STATE_HDR = (u'最后更新：2026-10-19 06:20（本地 · R%(round)s / 第 %(newn)s 轮：**212 结案 —— 那条红是判据在比两把不同的尺**'
             u'（U-625…U-627 · 产品 0 文件，判据账）\n\n'
             u'**本轮落地**：④ 换同一条绝对线（`sharedMovingFloor` 套两臂）+ 新地板"带至少看到 1 帧过程"；'
             u'旧口径同打印。`mutate_r191.py` %(arms)s ⇒ %(caught)s/%(total)s CAUGHT、RESTORE_CLEAN=%(restore)s；'
             u'M708 先 ESCAPED（`0 ≥ 0` 也算绿）后转 CAUGHT —— 这条已在账里当形状记下来。\n'
             u'**两次自坏也记了**：第一次"绿"其实是 1 skipped（动效卷要 `CLIPBOARD_HISTORY_UI_MOTION=1`）⇒ '
             u'台账生成器现在 skip≠0 就拒绝写盘；`mutate_r191.py` 第一版 write() 漏 join，崩在改文件之前（运气，不是防线）。\n'
             u'验证：编译 0 告警、判据卷 %(pair_n)s 例/skip %(pair_skip)s/失败 %(pair_fail)s、全量卷 %(full_n)s/%(full_skip)s/%(full_fail)s、'
             u'清账表 %(surface)s、电池见 commit 输出。\n\n'
             u'**下一轮（R192）的靶**：⓪ 读这一笔与 `2a7c829` 之后所有跑的**全部**失败步骤'
             u'（关键预期：`STEP[17] Motion coverage floor` 与 `STEP[13]/[15]` 都不该再因为 212/两态判据红）；\n'
             u'① 216：把同一条线推广到 `:2916` 左右分栏与 `:2332` 热图淡入 A/B，各配一把"退回各自归一化"的刀（真值表那两处不改，区分写进刀名）；\n'
             u'② 215：真机合成层通道拿一格亮档读数（判"通道盲区 vs 产品可辨性"）；\n'
             u'③ 201、202、205、207 与清账表未判的 47 格。\n'
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
    old = {k: read(v) for k, v in paths.items()}
    if u'## Round %d · ' % NEW_R in old['AGENT_VISUAL_ITERATION.md']:
        raise SystemExit('DUMP_ALREADY_WRITTEN ⇒ 不重复落盘')
    for name, txt in ((u'ui', ui_title + ui_body), (u'vi', vi_body), (u'cl', cl_body),
                      (u'bl', bl_body), (u'st', STATE_HDR)):
        if re.search(r'%\([a-z_0-9]+\)s', txt):
            raise SystemExit('FORMAT_LEAK %s 还有没吃掉的占位符' % name)
    top_state = [i for i, l in enumerate(old['STATE'].split(u'\n')) if l.startswith(u'最后更新：')][0]
    new = {}
    new['AGENT_UI_AUDIT.md'] = insert_before(old['AGENT_UI_AUDIT.md'], u'## 第 192 轮（R190', ui_title + ui_body)
    new['AGENT_VISUAL_ITERATION.md'] = old['AGENT_VISUAL_ITERATION.md'].rstrip(u'\n') + u'\n\n' + vi_body.rstrip(u'\n') + u'\n'
    new['CHANGELOG.md'] = insert_before(old['CHANGELOG.md'], u'### 上一笔把 CI 推红', cl_body)
    new['AGENT_BACKLOG.md'] = old['AGENT_BACKLOG.md'].rstrip(u'\n') + u'\n\n' + bl_body.rstrip(u'\n') + u'\n'
    st = old['STATE'].split(u'\n')
    new['STATE'] = u'\n'.join(st[:top_state] + [STATE_HDR.rstrip(u'\n'), u''] + st[top_state:])

    for name, fmt in LEDGERS.items():
        for this in (NEW_R, NEW_R - 1, NEW_R - 2):
            if this in ROSTER and this != NEW_R:
                continue
            if not re.search(fmt % this, new[name], re.M):
                raise SystemExit('PRECHECK_WOULD_RED R%d 在 %s 没有标题行 ⇒ 不写盘' % (this, name))
    section = new['AGENT_UI_AUDIT.md'].split(ui_title.rstrip(u'\n'), 1)[1].split(u'\n## 第 192 轮', 1)[0]
    defined = sorted(int(m) for m in re.findall(u'^- \\*\\*U-(\\d{3})：', section, re.M))
    if defined != [625, 626, 627]:
        raise SystemExit('U_RANGE_MISMATCH 本轮定义 %s（要 625…627）' % defined)
    items = set(re.findall(r'^(?:\*\*)?(\d{2,3})\. ', new['AGENT_BACKLOG.md'], re.M))
    for ref in re.findall(u'BACKLOG (\\d{3})', ui_body + vi_body + cl_body + bl_body + STATE_HDR):
        if ref not in items:
            raise SystemExit('DANGLING_BACKLOG %s 没有定义行' % ref)
    for k, v in new.items():
        write(paths[k], v)
    print(u'LEDGERS_R191_WRITTEN r=%d n=%d U=625..627 arms=%s/%s restore=%s pair=%s/%s/%s full=%s/%s/%s'
          % (NEW_R, NEW_N, V['caught'], V['total'], V['restore'],
             V['pair_n'], V['pair_skip'], V['pair_fail'], V['full_n'], V['full_skip'], V['full_fail']))
    return 0


if __name__ == '__main__':
    sys.exit(main())

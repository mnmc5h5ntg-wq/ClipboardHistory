#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R94 台账落盘（Round 94 / 第 96 轮 / D-151 补记 + D-152 / 结案 134 / 新开 135、136 / U-218…U-222）。

两遍走，顺序不能换（这一轮的特殊之处：新加的台账守卫在写台账之前**必然**红）：
    pass-1：`python3 ledgers_r94.py D`        —— 只补两条决定正文（D-151 补记、D-152），
             前置条件是 `SKIP_PY=1 bash verify_r94.sh` 打出 VERIFY_OK=1（脚本电池那一格显式跳过并写明跳过）
    pass-2：`python3 ledgers_r94.py A B C E F G` —— 轮次正文、CHANGELOG、BACKLOG、STATE，
             前置条件是完整 verify（含脚本电池）打出 VERIFY_OK=1；G 格复跑守卫并要求绿

规矩（R89 之后一直守着）：编号一律从台账现值推（last_int），正文里的数字都从读数来；
锚点必须唯一（sub_once）；变异进行中拒绝写盘；落盘前拒绝残留占位符。
"""
import os
import re
import subprocess
import sys

REPO = '/Users/wangziyi/Codex_Project0'
VERIFY = '.scratch/motion-audit-2/r94_verify.log'
SPEC = re.compile(r'%\((?:\w|#)+\)s|%%')


def F(template, *args):
    n = len([m for m in SPEC.finditer(template) if m.group() != '%%'])
    if n != len(args):
        raise AssertionError('FORMAT_ARITY 占位符=%d 参数=%d :: %s' % (n, len(args), template))
    return template % args


def fill(template, values, tag):
    out = template
    for key, val in values.items():
        out = out.replace('%(' + key + ')s', str(val))
    if re.search(r'%\(\w+\)s', out):
        raise SystemExit('%s 里还有没被替换的占位符' % tag)
    return out


def read(path):
    with open(os.path.join(REPO, path), encoding='utf-8') as handle:
        return handle.read()


def write(path, text):
    if re.search(r'%\(\w+\)s', text):
        raise SystemExit('%s 落盘前发现残留占位符' % path)
    with open(os.path.join(REPO, path), 'w', encoding='utf-8') as handle:
        handle.write(text)


def sub_once(text, old, new, tag):
    n = text.count(old)
    if n != 1:
        raise SystemExit('%s 的锚点命中 %d 次（只许 1 次）⇒ 拒绝写台账' % (tag, n))
    return text.replace(old, new)


def refuse_while_mutating():
    out = subprocess.run(['git', '-C', REPO, 'status', '--porcelain'],
                         capture_output=True, text=True).stdout
    for line in out.splitlines():
        if ('MUT' in line or 'mutate' in line.lower()) and line[:1] == 'M':
            raise SystemExit('工作区里有变异留下的改动痕迹：%s ⇒ 先恢复' % line)


def last_int(pattern, paths, default=0):
    best = default
    for p in paths:
        for m in re.finditer(pattern, read(p), re.M):
            best = max(best, int(m.group(1)))
    return best


def require_verify(pass_no):
    text = read(VERIFY)
    if 'VERIFY_OK=1' not in text:
        raise SystemExit('pass-%d 的验证没打完（缺 VERIFY_OK=1）⇒ 不写台账' % pass_no)
    if pass_no == 2 and 'SKIPPED=1' in text:
        raise SystemExit('pass-2 不许用跳过脚本电池的那份 verify ⇒ 重跑不带 SKIP_PY 的那一遍')


def gather():
    g = {}
    g['NOW'] = '2026-10-16 %s' % subprocess.run(['date', '+%H:%M'], capture_output=True,
                                                text=True).stdout.strip()
    status = subprocess.run(['git', '-C', REPO, 'status', '--porcelain'],
                            capture_output=True, text=True).stdout.splitlines()
    touched = [l[3:].split(' -> ')[0] for l in status if l[:2] in (' M', 'M ', '??', 'A ')]
    g['PRODUCT_N'] = sum(1 for t in touched if '/Sources/' in t)
    LEDGER = ('AGENT_BACKLOG.md', 'AGENT_DECISIONS.md', 'AGENT_STATE.md', 'AGENT_UI_AUDIT.md',
              'AGENT_VISUAL_ITERATION.md', 'CHANGELOG.md', 'AGENTS.md')
    n_tool = sum(1 for t in touched if t.startswith('scripts/'))
    n_scr = sum(1 for t in touched if t.startswith('.scratch/'))
    n_led = sum(1 for t in touched if t in LEDGER)
    # 分类计数而不是一个总数：本轮"改了哪些东西"要能被读的人对上号（一个 21 说明不了任何事）。
    g['TOUCHED'] = '判据/工具 %d 个、仓库外脚本 %d 个、台账 %d 个（**产品 %d 个**）' % (
        n_tool, n_scr, n_led, g['PRODUCT_N'])
    for line in read(VERIFY).splitlines():
        m = re.match(r'^(BUILD_WARN|PY_EXIT|MUT_EXIT|VIS_EXIT|FRAMES_EXIT|LEDGER_EXIT)=(\S+)(.*)$', line)
        if m:
            g['V_' + m.group(1)] = m.group(2)
            if m.group(1) == 'MUT_EXIT':
                # 变异表那一串就在同一个 `say` 行里（verify 的写法），别再去猜另一个文件。
                g['MUTATE'] = m.group(3).strip() or '未打出 MUTATE_TABLE'
    g.setdefault('MUTATE', '未打出 MUTATE_TABLE')
    g['PYLINE'] = '未打出脚本电池那一行'
    for line in read(VERIFY).splitlines():
        m = re.match(r'^PY_EXIT=\d+ (Ran .*(?:OK|FAILED.*))\s*$', line)
        if m:
            g['PYLINE'] = m.group(1).strip()
    g['ROSTER'] = 'cases=11 can=6 cannot=5'
    g['RUN'] = '38857388449'
    g['SHA'] = '8e6ed15'
    g['PROBE_TAIL'] = 'Executed 11 tests, with 3 tests skipped and 0 failures（15.310s）'
    # 决定编号**不按 max+1 猜**：那正是 R94 第一次跑 A B C E F 时写错的东西 ——
    # D 那一格已经跑过，max 前进了 ⇒ 再算成 D-153/D-154，而正文是 D-151/D-152，
    # 于是新写的那支守卫立刻把我的错抓了回来（它第一次红抓的是 R93 的欠账，第二次红抓的是我的）。
    # ⇒ 按轮次标签去文件里找那条正文，找不到就明说，不编号。
    dec = read('AGENT_DECISIONS.md')

    def id_for(tag):
        m = re.search(r'^#{2,3} (D-\d{3})（' + tag, dec, re.M)
        return m.group(1) if m else 'D-???（没找到以「%s」开头的决定）' % tag

    g['D_PREV'] = id_for('R93 补记')
    g['D_THIS'] = id_for('R94）')
    g['NEXT_B'] = last_int(r'^(\d{3})\. ', ['AGENT_BACKLOG.md']) + 1
    g['NEXT_U'] = last_int(r'U-(\d{3})', ['AGENT_UI_AUDIT.md', 'AGENT_VISUAL_ITERATION.md']) + 1
    for k in ('NEXT_B', 'NEXT_U', 'PRODUCT_N'):
        g[k] = str(g[k])
    g['U1'], g['U2'], g['U3'], g['U4'], g['U5'] = ['U-%03d' % (int(g['NEXT_U']) + i) for i in range(5)]
    return g


STAGES = {}


def patch_decisions(g):
    path = 'AGENT_DECISIONS.md'
    text = read(path)
    if g['D_THIS'] in text:
        raise SystemExit('%s 已存在 ⇒ 不重复写' % g['D_THIS'])
    add = fill(DECISIONS, g, 'DECISIONS')
    write(path, text.rstrip('\n') + '\n\n' + add)
    return '%s（补记 %s + 本轮 %s）' % (path, g['D_PREV'], g['D_THIS'])


def patch_visual(g):
    path = 'AGENT_VISUAL_ITERATION.md'
    text = read(path)
    if '## Round 94 ·' in text:
        raise SystemExit('Round 94 已存在')
    write(path, text.rstrip('\n') + '\n\n' + fill(VISUAL, g, 'VISUAL'))
    return '%s（追加 Round 94）' % path


def patch_ui_audit(g):
    path = 'AGENT_UI_AUDIT.md'
    text = read(path)
    at = text.index('## 第 95 轮 ·')
    write(path, text[:at] + fill(UI, g, 'UI') + '\n' + text[at:])
    return '%s（插入第 96 轮）' % path


def patch_changelog(g):
    path = 'CHANGELOG.md'
    text = read(path)
    write(path, sub_once(text, '## [Unreleased]\n',
                         '## [Unreleased]\n' + fill(CHANGELOG, g, 'CHANGELOG'), 'CHANGELOG 锚点'))
    return path


def patch_backlog(g):
    path = 'AGENT_BACKLOG.md'
    text = read(path)
    if re.search(r'^%s\. ' % g['NEXT_B'], text, re.M):
        raise SystemExit('BACKLOG %s 已存在' % g['NEXT_B'])
    close = ('    如果它报了，说明翻错，按它点名的那条改回去 —— 这两格存在的理由就是这个。')
    block134 = """

    → **R94 结案**（run %(RUN)s / `%(SHA)s` 的 `On-screen probe coverage floor` 逐条点名之后）：
    六条翻成 `can`，判定是**读来的**且分开写 —— `testAccessibilityTreeCoverage` 那次是 `skipped`
    ⇒ 它只证明"runner 跑得动"，今天仍不产出产品判断；其余五条是 `passed` ⇒ 产品结论第一次能引用那台机器。
    剩下五条 `cannot` 的成因分三种写法：1 条就是挂住的那条（132）、3 条真的排在它之后、
    1 条（R93 新登记的那条）**根本不在 `%(SHA)s` 的源码里**（那次闸门读数是 `源码用例=10 登记=10`）
    ⇒ 不许把"没编译过"写成"排队没到"。名册：`%(ROSTER)s`。
    翻转之后本地对两份真日志各判一次：r62 那份（零结论）现在**该红**且逐条点名（NOT_RUN ×6），
    %(SHA)s 那份该绿 —— 这两格替代了原来那句"真 CI 日志该绿"的旧契约。"""
    text = sub_once(text, close, close + fill(block134, g, '134 结案'), 'BACKLOG 134 结案锚点')
    upd = ('    分清"挂死"与"慢"；如果是慢，要量的是慢在哪一段，而不是把 240 秒的看门狗放宽。')
    block132 = """

    → **R94 更新（读数到手，处置没做）**：run %(RUN)s 里它仍是那条开口没闭口的
    （`UI_PROBE_HUNG=testRightClickMenusAppKitWouldShowAreChinese`、`started=7 concluded=6`、
    `UI_PROBE_CHANNELS_AGREE=1`），而本机这一遍它 `passed (2.016s)` ⇒ "挂 or 慢"仍未分。
    本轮新加的 `PROBE_ORDER 露面=…/未闭口=…` 与 `PROBE_QUEUED 4/11 条一次都没轮到`
    把"排在它之后"从推断升成读数（下一次 runner 上就能被证伪），
    但 **sample 那一格仍欠着** —— 它才是 132 的第一格。"""
    text = sub_once(text, upd, upd + fill(block132, g, '132 更新'), 'BACKLOG 132 更新锚点')
    write(path, text.rstrip('\n') + '\n\n' + fill(BACKLOG, g, 'BACKLOG'))
    return '%s（结案 134 / 更新 132 / 新开 %s、%s）' % (path, g['NEXT_B'], int(g['NEXT_B']) + 1)


def patch_state(g):
    path = 'AGENT_STATE.md'
    lines = read(path).splitlines(True)
    head = next(i for i, l in enumerate(lines) if l.startswith('最后更新：'))
    old = lines[head].rstrip('\n')
    if 'R94' in old[:40]:
        raise SystemExit('AGENT_STATE 第 3 行已经是本轮')
    new = fill(STATE, g, 'STATE')
    lines[head:head + 1] = [new + '\n', '\n',
                            '> 上一轮（R93 / 第 95 轮收尾）原文开头：' + old[len('最后更新：'):] + '\n', '\n']
    write(path, ''.join(lines))
    return path


def post_check(g):
    """写完台账之后自己复跑那两格：新守卫必须绿，脚本电池必须全绿。"""
    for argv, tag in ((['python3', '-m', 'unittest', 'scripts.tests.test_ledger_ids'], '台账编号守卫'),
                      (['python3', '-m', 'unittest', 'discover', '-s', 'scripts/tests'], '脚本电池')):
        proc = subprocess.run(argv, cwd=REPO, capture_output=True, text=True,
                              env=dict(os.environ, PYTHONUTF8='1'))
        tail = proc.stderr.splitlines()[-3:] or proc.stdout.splitlines()[-3:]
        if proc.returncode != 0:
            raise SystemExit('%s 复跑红 ⇒ 台账写坏了：%s' % (tag, ' | '.join(tail)))
        print('  复跑 %s：OK（%s）' % (tag, ' | '.join(tail)))
    return '复跑守卫与脚本电池'


STAGES = {'D': (patch_decisions,), 'A': (patch_visual,), 'B': (patch_ui_audit,),
          'C': (patch_changelog,), 'E': (patch_backlog,), 'F': (patch_state,),
          'G': (post_check,)}


DECISIONS = '''### %(D_PREV)s（R93 补记 · R94 落盘）在屏探针的名册：只改成因，不翻身份——名字没读到时翻它就是登记推断

**背景**：R91 故意留下一朵有名字的红（`testSidebarListFocusRingAfterClick`），R93 用新加的诊断判据
把它判成"判据的期望写错"（`KeyViewProxy` 是宿主级 key-view 代理，不是行代理），产品侧结构没坏。
同一轮里 `probe_coverage_expectations.json` 有十条 `runner=cannot`，而 run 38852286519 数出"六条有结论"。

**决定**：R93 只把十一条 reason 改成**实测成因**，不翻任何一条的身份；翻转等下一次 CI 逐条印出名字。

**理由**：名字在被 SIGKILL 带走的那块 stdout 缓冲里，只有计数留下了。按字典序猜"跑到的是哪六条"
就是把推断登记成事实（R87 那一课）。翻错有机制兜底：`NOW_RUNS`（说不能跑却跑了）与
`NOT_RUN`（说能跑却没跑）两格都会红 —— 这两格存在的理由就是这个。

**兼容性/迁移**：只动登记文件，不动产品、不动判据代码。
**回滚**：`git revert` 本轮提交即可；名册是纯数据，回滚不产生迁移。

---

### %(D_THIS)s（R94）名册按读数翻身份；"为什么没结论"从推断升成读数，而两支闸门的分工从词汇改成能力

**背景**：run %(RUN)s（`%(SHA)s`）第一次把"是哪六条"逐条印了出来 ——
`PROBE_COVERAGE_SUMMARY … 本次下结论=6 红=6`，六行 `NOW_RUNS <名字>：…（passed|skipped）`，
外加 `PROBE_NOT_RUN 4/10 …` 点名没结论的四条。作业结论是 **failure**，红全部来自 NOW_RUNS
（登记说跑不了、它却跑了）⇒ 这正是 %(D_PREV)s 留的那个循环该合上的地方。

**决定**：
1. 六条翻 `can`，且**按判定分开写**：`skipped` 那条只到"runner 跑得动、会下结论"这一层，
   不产出产品判断（skip 不是通过，闸门文档里就写着这句）；五条 `passed` 才配"产品结论可引用那台机器"。
2. 剩下五条 `cannot` 的成因分三种：挂住的那条 / 真的排在它之后的三条 / R93 才登记、
   根本不在 `%(SHA)s` 源码里的那条。"没编译过"不许写成"排队没到"。
3. `probe_coverage_gate.py` 新增两行**只报不判**的读数：`PROBE_ORDER 露面=…/未闭口=…/前缀=…`
   与 `PROBE_QUEUED <一次都没轮到的名字>`。"未闭口"只报**计数**，名字仍归 `ui_probe_report.py`。
4. R86 那条 `NonRedundancyTests` 守卫从"文本里不许出现 started 这个词"改成"不许**复制判定**"：
   只扫 `print(` 行里的字面串，并新增反方向一格（名字必须仍由 `ui_probe_report` 出）。

**理由**：②与③是同一件事的两面 —— 登记里那句"排在 X 之后"以前只能由我从**另一步骤**的字母序推断，
而现在它是读数，下一轮能被证伪。④是必要的：两支闸门共用原始通道（都要读 `Test Case … started.`）
不等于共用判定；判定若重复，定罪权就要按样本数分配（R87），而这一支只有一份日志、那一支有两份互相签字。

**兼容性/迁移**：不动产品、不动夹具、不动 CI 步骤正文；`probe_coverage_expectations.json` 是纯数据，
`runner` 字段仍只许 can/cannot。**一条被登记的机器分裂**：`testFrameIntervalsUnderStateChanges`
在 runner 上是 `passed`（`FRAME_CHANNEL` 拿到了 tick），在本机是 `skip`（显示器睡着 ⇒ 0 个样本）
⇒ 这一格"跑过 / 没跑"要按机器分开记，不能拿一台的地板当另一台的。

**回滚**：`git revert` 本轮提交；名册与闸门脚本各自独立可回滚，互不依赖。
'''

VISUAL = '''## Round 94 · 名册按读数翻了六条，"为什么没结论"从推断升成读数；菜单栏那六帧第一次被逐元素判（结案 134 / 新开 %(NEXT_B)s、%(NEXT_B2)s / %(U1)s…%(U5)s / %(D_THIS)s）

### 1. 头条：上一轮欠的翻转做完了，而它把作业的红灯一起带走

run %(RUN)s（`%(SHA)s`）的 `On-screen probe coverage floor` 第一次逐条点名：
`本次下结论=6 红=6`，六行 `NOW_RUNS <名字>：…（passed|skipped）`。作业结论是 **failure**，
红的来源正是"登记说跑不了、它却跑了"—— %(D_PREV)s 留的那个循环该在这里合上。

* 六条翻 `can`，判定分开写：`testAccessibilityTreeCoverage` 那次是 `skipped` ⇒ 只证明"跑得动"，
  **今天仍不产出产品判断**；其余五条 `passed` ⇒ 产品结论第一次能引用那台机器。
  （第一版我给六条写了同一句"产品结论可以引用它"，对 skipped 那条是假的。）
* 剩下五条 `cannot` 三种成因：1 条挂住（132）/ 3 条真的排在它之后 / 1 条**根本不在 `%(SHA)s` 的源码里**
  （那次读数 `源码用例=10 登记=10`，它是 `6c5ca95` 才登记的）⇒ "没编译过"不许写成"排队没到"。
* 名册：`%(ROSTER)s`。本地对两份日志各判一次：r62 那份（零结论）现在**该红**且逐条点名 NOT_RUN×6，
  `%(SHA)s` 那份该绿。原来那句"真 CI 日志该绿"是全 can=0 时代的契约，过期了（%(U4)s）。

### 2. 一次差点写出的假话：同一卷在同一次 run 里有 20 行结论，全是 skip

`gh run view --job 116831818024 --log` 里 grep `UIInteractionProbeTests` + `Test Case` 得到 20 行，
**全部 skipped** —— 但它们属于 `Swift tests (executed-count gate)` 那一步（那里没有
`CLIPBOARD_HISTORY_UI_INTERACTION=1`）。按步骤名 `awk -F'\\t' '$2=="On-screen interaction probes (report-only)"'`
一过滤，那一步的正文里 `Test Case` 行数 = **0**，只有汇总行 `已下结论的用例: 6`。
⇒ 不按步骤名过滤就会写出一句"探针在 runner 上也是全 skip"的假话（R86 那条老账，这次又差一次，%(U1)s）。
顺带纠正我自己：`8e6ed15` 那次的作业结论是 **failure** 不是绿。

### 3. 把推断升成读数：PROBE_ORDER / PROBE_QUEUED（只报不判）

```
PROBE_COVERAGE_SUMMARY 源码用例=11 登记=11 runner可跑=6 runner不可跑=5 本次下结论=6 红=0
  PROBE_ORDER 露面=7/11 未闭口=1 前缀=1
  PROBE_QUEUED 4/11 条一次都没轮到：testRowGestures… testRowIndexDrift… testSidebarListFocusRingAfterClick testRowProxyCensus…
```

* 缺席从此分两种：**跑到了却没闭口**（计数，名字归 `ui_probe_report`）与**一次都没轮到**（名字）。
* `前缀=无从判定` 那一格是刻意留的：一条都没露面时"前缀成立"是一句**空洞的真话**（%(U3)s）。
* 三行读数**不判红**：把诊断做成门禁，就会在另一种执行序下假红。`NOT_RUN` 该红仍然红。
* R86 那条守卫（`NonRedundancyTests`）从"文本里不许出现 started"改成"不许复制**判定**"：
  只扫 `print(` 行的字面串 + 反方向一格（名字必须仍由 `ui_probe_report` 出）。
  变异 M522 证明它还有牙：让闸门自己打印 `PROBE_HUNG=` 就会被它抓住。

### 4. 牙：M516…M522（先在台账查重：上一支用到 M515）

`%(MUTATE)s`
M516 前缀恒真 / M517 露面顺序被排序 / M518 打印里的"未闭口"写死成 0 / M519 两种缺席又被缝成一种 /
M520 空洞的真话冒充结论 / **M521 预期绿**：结论之后又出现 `started` 时把状态改回"未结论"——
现有夹具都不产生这种交错 ⇒ 真实缺口开成 **%(NEXT_B)s**（一份日志混进第二个写入者时"未闭口"会说谎，
R80b 那一族）/ M522 复制因果级名字 ⇒ 被改写过的那条守卫抓住。
变异跑在**临时树**上（`scripts/` + 那份 json + 软链的 swift 源文件 + `.github/workflows` 软链），
仓库里那颗尺子全程没被写过；第一次跑时临时树缺 `.github/workflows` ⇒ 基线 RED 而脚本按自己的规矩
**拒绝出表**（%(U5)s）。

### 5. 看图那一腿：菜单栏面板（MenuBarExtra 的内容视图）第一次被逐元素判

正文：`.scratch/motion-audit-2/r94_menubar_review.md`；读数：`r94_menubar_readings.log`。
本轮产品文件 **%(PRODUCT_N)s 个** ⇒ 帧是**重新拍的**（`/tmp/r94_shots`，124 帧与 working 基线 `CHANGED=0`）。

* 结构：`empty 3 带/1 线`、`refreshing 3/1`、`recommendations 9/3`，两主题**同形**（最大 y 偏差 0.5pt）；
* 两态对照：`EMPTY_VS_REFRESHING 像素完全相同=False`，差异**只在消息那一条带**（"暂无推荐" x 到 73.0、
  "正在整理推荐…" 到 107.5）⇒ 帧名不撒谎（R76 那条）；
* 档：标题 14.94/12.27、说明 3.95/5.92、动作行蓝 3.52/5.16（墨 (0,136,255)/(0,145,255)）；
* **零产品改动**的理由：三条推荐行左右顶到帧边界 = R34 登记的**复刻溢出**，那批帧对
  宽度/截断/对齐/命中区没有发言权（`testMenuBarFramesAreReplicasOfTheMenuSurface` 钉着）。
  标题与小标题在这六帧里居中（x=134.5..184.5 与 132.5..186.0），而 macOS 12 那条路径用的是原生
  `NSMenuItem(title: "时间剪史")` ⇒ 两条路径**可能**不一致，但这条通道没资格判 ⇒ 开 **%(NEXT_B2)s** 真机核对。
* 动效判断（逐条）：菜单项 hover / 按压 / 空↔有推荐的淡入 / 加载态转圈 —— **四条全部维持现状**，
  理由各自不同（系统自己画高亮、帧里没有任何自绘底、NSMenu 不执行 SwiftUI transition、假动更不诚实）。

### 6. 三条尺错（都进台账，都不算产品缺陷）

* %(U1)s 跨步骤 grep 造出假话（见 §2）；
* %(U2)s `decode()` 返回 `(w,h,ch,rows)` 而 `lum()` 是 **0..1 的 Y** ⇒ 抄来的 255 尺度阈值
  让六张帧全读"带数=0"（"量不到"伪装成"没有"）；
* %(U3)s 固定 ΔL 门槛跨主题灵敏度不一致：同一根 `Divider()` 两档都 ≈1.25:1，ΔL 却 53.2 / 5.4
  ⇒ 墨的判据改用对比度比值；另加"两档同形"正对照（容差 1.0pt，量出来的，不是拍的）。

### 7. 验证（本机，逐条实跑）

* 构建 0 告警；全量 `swift test` 通过；在屏那一卷本机 `%(PROBE_TAIL)s`；
* 帧：124 帧对 working 名单 `CHANGED=0 MISSING=0 ADDED=0`；
* 脚本：`%(PYLINE)s`（含新写的 `scripts/tests/test_ledger_ids.py` 四格）；
* 变异：`%(MUTATE)s`；
* 非台账文件：%(TOUCHED)s ⇒ **不换装**（产品像素未变）。

### 8. 台账自己也被判了一次（%(U4)s）

写这条之前先 grep 决定编号：最后一条是 **D-150（R92）**，而 R93 的两处轮次标题都写着"D-151"
⇒ 一条**被引用却不存在的决定**（根因：`ledgers_r93.py` 的 STAGES 里没有 decisions 那一格，
标题里的号是手抄的）。本轮补记 %(D_PREV)s，并新加一支守卫 `scripts/tests/test_ledger_ids.py`：
轮次标题里引用的每个 `D-xxx` 必须在 `AGENT_DECISIONS.md` 有正文，编号不许空号。
它第一次跑就是红的，报的正是 D-151 —— 也是它教我：定义行的正则要按台账**实际形状**写
（老条目是 `## D-000 …`，新条目是 `### D-150（R92）…`；只认 `###` 会漏掉 115 条，把守卫变成一堵假正例的墙）。

### 9. 仍未解决

**%(NEXT_B)s**（交错日志下"未闭口"会说谎）、**%(NEXT_B2)s**（真机核对菜单栏面板）、
**132** 的 sample、**133** 的夹具赋值不选中、**130/126**（真机 + 录屏权限）、**129**、
**124** 第②步、**121**、**116** 剩下那半格、**115**、**111**、108 余下、77 路 b、101 ②③、106；
真机 68.1 / 68.2 / 69.1 / 70.1 / 71.1 / 72.x / 73.x。
'''

UI = '''## 第 96 轮 · R94：名册按读数翻了六条，"为什么没结论"升成读数；菜单栏六帧第一次逐元素判（结案 134 / 新开 %(NEXT_B)s、%(NEXT_B2)s / %(U1)s…%(U5)s / %(D_THIS)s）

- 读 run %(RUN)s（`%(SHA)s`）：`本次下结论=6 红=6`，六行 `NOW_RUNS <名字>（passed|skipped）`，
  **作业结论是 failure**（上一轮我自己把它记成"闸门 ok"，这一轮纠正）。134 结案：六条翻 `can`，
  `skipped` 那条只到"跑得动"这一层（skip 不是通过），五条 `passed` 才配引用那台机器；
  剩下五条 `cannot` 三种成因，其中一条**根本不在那次构建的源码里** ⇒ 没写成"排队没到"。
- 差点写出的一句假话：同一卷在同一次 run 的**另一步**里有 20 行结论、全是 skipped（那一步没有
  `CLIPBOARD_HISTORY_UI_INTERACTION=1`）。按步骤名过滤才看见探针那一步正文里 `Test Case` 行数=0（%(U1)s）。
- 新读数：`PROBE_ORDER 露面=7/11 未闭口=1 前缀=1` + `PROBE_QUEUED 4/11 条一次都没轮到：<名字>`，
  只报不判；"未闭口"只报计数，名字仍归 `ui_probe_report`（两支闸门的分工守卫从**词汇**改成**能力**，M522 证明有牙）。
- 变异 `%(MUTATE)s`：跑在临时树上，仓库里的尺子没被写过；临时树缺 `.github/workflows` 时基线 RED、脚本拒绝出表（%(U5)s）。
- 看图：菜单栏面板逐元素判完（结构两档同形、两态真的有两态、档 14.94/12.27 与 3.95/5.92 与蓝 3.52/5.16）；
  **零产品改动** —— 三条推荐行顶到帧边界是 R34 登记的复刻溢出，那批帧对宽度/截断/对齐没资格；
  标题居中 vs macOS 12 用原生 `NSMenuItem(title:)` 这条**可能**的不一致开成 %(NEXT_B2)s 真机核对。
- 三条尺错：%(U2)s（`lum()` 是 0..1 的 Y，抄来的 255 尺度阈值让六帧全读 0 带）、
  %(U3)s（固定 ΔL 门槛跨主题灵敏度不一致 ⇒ 改用对比度比值 + 两档同形正对照，容差 1.0pt 是量出来的）、
  %(U4)s（台账里"D-151"被两处标题引用却没有正文 ⇒ 补记 + 新守卫 `test_ledger_ids.py`）。
- 验证：构建 0 告警、全量测试通过、124 帧 CHANGED=0、脚本 %(PYLINE)s、在屏整卷 `%(PROBE_TAIL)s`、
  非台账 %(TOUCHED)s ⇒ 不换装。
- 七维自评 **96 / 100**（扣在：132 的 sample 仍没做、M521 那个缺口只开单没修、看图这一屏没产生产品改动）。
'''

CHANGELOG = '''### 判据与工具（R94，零产品改动）

- `scripts/probe_coverage_expectations.json`：六条按 run %(RUN)s 的 `NOW_RUNS` 逐条翻成 `can`
  （`skipped` 与 `passed` 分开写，skip 不产出产品判断）；五条 `cannot` 的成因分三种
  （挂住的那条 / 排在它之后的三条 / R93 才登记、不在 `%(SHA)s` 源码里的那条）。BACKLOG 134 结案。
- `scripts/probe_coverage_gate.py`：新增 `execution_order()` 与两行**只报不判**的读数
  `PROBE_ORDER 露面=…/未闭口=…/前缀=…`、`PROBE_QUEUED <名字>`；"一条都没露面"时前缀报
  `无从判定` 而不是 1。"挂住的是谁"这个名字仍归 `ui_probe_report.py`（两支闸门共用原始通道不等于共用判定）。
- `scripts/tests/test_probe_coverage_gate.py`：r62 那份真日志的正对照从"该绿"改成"该红且逐条点名"
  （名册翻了身份之后这才是正确契约），并新增执行序三格（尺不许按字母序排、空日志不许报空洞的真话、
  前缀断了不许判红）与"读数必须被打印出来"一格。
- `scripts/tests/fixtures/r94_runner_ui.log`：新夹具，头部写清 provenance
  （名字/判定/顺序/计数逐字读来，只有秒数是补的，而秒数正是闸门明写"不判"的那一项）。
- `scripts/tests/test_ui_probe_report.py`：R86 那条 `NonRedundancyTests` 从"文本里不许出现 started"
  改成"不许复制判定"（只扫 `print(` 行的字面串 + 红清单里不许出现诊断词），并加反方向一格。
- `scripts/tests/test_ledger_ids.py`（新）：轮次标题引用的每个 `D-xxx` 必须在 `AGENT_DECISIONS.md`
  有正文、编号不许空号。它第一次跑就抓到 R93 欠的 D-151（两处标题引用了它，正文从没写过）。
- 仓库外：`roster_r94.py`（名册翻转可重放）、`mutate_r94_order.py`（M516…M522，跑在临时树上）、
  `r94_menubar_visual.py` + `r94_menubar_review.md`（菜单栏六帧逐元素）、`verify_r94.sh`、
  `r94_ci_readings.md`（run %(RUN)s 的逐字读数）。

'''

BACKLOG = '''%(NEXT_B)s. **执行序这把尺遇到"交错日志"会说谎：结论行之后再出现一次 `started.` 会把状态改回未结论**（R94 开 / 与 112、132、80b 同族）：
    变异 M521 是**故意留着绿**的那一刀 —— 现有任何夹具都不产生"结论之后又见面"的形状，
    所以 `execution_order()` 里那格 `if kind != "started."` 的写法没有判据覆盖。
    真实风险：`/tmp/ui.log` 是 `swift test > … 2>&1` 的**共享**通道，如果哪一步把第二个进程的
    输出并进来（R80b 那次是两行被缝成一行），"未闭口"的计数就会凭空多出来，而它现在是登记的依据之一。
    修法（下一轮，别在改产品的那一轮顺手做）：喂一份**交错**的夹具（A started、A passed、A started、B passed）
    并断言 `露面/未闭口/前缀` 三个读数，再决定"后到的 started"算重跑还是算噪声。

%(NEXT_B2)s. **菜单栏面板：标题与小标题在复刻里居中，而 macOS 12 那条路径用的是原生 `NSMenuItem(title:)` —— 两条系统路径可能不一致，这条通道没资格判**（R94 开 / 与 130、126、R2-22 同族）：
    实测（`r94_menubar_readings.log`）：`时间剪史` 的墨带 x=134.5..184.5（帧宽 320 ⇒ 居中），
    `猜你要粘贴` x=132.5..186.0（也居中），而三条推荐行与动作行的带是 x≈0..319.5（左贴边、右溢出）。
    源码侧事实：`MenuBarRecommendationsView` 里那两个 `Text` 没有 `.frame(maxWidth:.infinity, alignment:.leading)`，
    隐式栈因此把它们居中；`MenuBarController.swift:70`（macOS 12 那条）用的是
    `NSMenuItem(title: "时间剪史", …)`，AppKit 自己左对齐。
    **为什么本轮不改产品**：`menubar-*` 这批帧对宽度/截断/**对齐**/命中区没有发言权
    （R34 的 `testMenuBarFramesAreReplicasOfTheMenuSurface` 钉着，本轮 6/6 帧复核它仍然成立）。
    真机那一腿要核对三件事：① 菜单里的标题到底居中还是左对齐；② 动作行那层蓝在真实菜单底色上的对比
    （复刻里是 3.52 / 5.16，底色是夹具的 `windowBackgroundColor`）；③ 理由列在真实菜单里是被截断还是把菜单撑宽。
    核对完再决定要不要给那两个 `Text` 加左轴 —— **不许**先改产品再拿复刻当证据。

'''

STATE = '''最后更新：%(NOW)s（本地 · R94 / 第 96 轮收尾：**上一轮欠的名册翻转做完了，而它把 `8e6ed15` 那次作业的红灯一起带走** —— run %(RUN)s 的 `On-screen probe coverage floor` 第一次逐条点名（`本次下结论=6 红=6`，六行 `NOW_RUNS <名字>（passed|skipped）`），六条翻 `can` 且**判定分开写**：`testAccessibilityTreeCoverage` 那次是 skipped ⇒ 只证明"跑得动"、今天仍不产出产品判断，其余五条 passed ⇒ 产品结论第一次能引用那台机器；剩下五条 cannot 三种成因（1 挂住 / 3 排在它之后 / 1 根本不在 `%(SHA)s` 的源码里）⇒ 结案 **134**。两处自我纠正：①上一轮我把那次作业记成"闸门 ok"，实际结论是 **failure**；②同一卷在同一次 run 的**另一步**里有 20 行结论、全是 skipped（那一步没有 `CLIPBOARD_HISTORY_UI_INTERACTION=1`）——不按步骤名过滤就会写出"探针在 runner 上也是全 skip"这句假话（%(U1)s）。新把戏：`probe_coverage_gate.py` 加 `PROBE_ORDER 露面/未闭口/前缀` 与 `PROBE_QUEUED <名字>` 两行**只报不判**的读数，于是登记里那句"排在它之后"从推断升成读数；"挂住的是谁"仍只由 `ui_probe_report` 出（两支闸门共用原始通道≠共用判定），R86 那条守卫因此从"不许出现 started 这个词"改成"不许复制判定"，M522 证明它还有牙。变异 `%(MUTATE)s`，跑在临时树上（仓库里那颗尺子全程没被写过；第一次跑临时树缺 `.github/workflows` ⇒ 基线 RED 而脚本拒绝出表，%(U5)s）。看图那一腿：菜单栏面板六帧第一次逐元素判完（两档结构同形、两态真的有两态、档 14.94/12.27 与 3.95/5.92 与蓝 3.52/5.16），**零产品改动** —— 三条推荐行顶到帧边界是 R34 登记的复刻溢出，那批帧对宽度/截断/对齐没资格；标题居中 vs macOS 12 用原生 `NSMenuItem(title:)` 这条不一致开成 **%(NEXT_B2)s** 真机核对；尺错三条 %(U2)s/%(U3)s。台账也被判了一次：R93 两处标题引用的 **D-151 从来没有正文**（根因是 `ledgers_r93.py` 的 STAGES 少了 decisions 那一格）⇒ 本轮补记 %(D_PREV)s 并新加守卫 `scripts/tests/test_ledger_ids.py`（%(U4)s）。验证：构建 0 告警、全量测试通过、124 帧 CHANGED=0、脚本 %(PYLINE)s、在屏整卷 `%(PROBE_TAIL)s`、非台账 %(TOUCHED)s ⇒ 不换装。**下一轮第一件事：读 R94 的 CI —— 预先登记的预测：`On-screen probe coverage floor` 该绿、作业该转绿，且 `PROBE_ORDER`/`PROBE_QUEUED` 第一次在 runner 上打这行；若还红，红必须有新名字。然后做 132 的 `sample`（分清挂与慢）与 133 的"夹具赋值不选中"**）'''


def main():
    stages = sys.argv[1:] or sorted(STAGES)
    g = gather()
    if 'D' in stages:
        require_verify(1)
    elif any(s in stages for s in 'ABCEF'):
        require_verify(2)
    print('编号：%(D_PREV)s→%(D_THIS)s｜BACKLOG 下一条 %(NEXT_B)s/%(NEXT_B2)s｜U %(U1)s…%(U5)s' % dict(
        g, NEXT_B2=int(g['NEXT_B']) + 1))
    g['NEXT_B2'] = str(int(g['NEXT_B']) + 1)
    done = []
    for s in stages:
        for fn in STAGES[s.upper()]:
            r = fn(g)
            done.append(r)
            print('  · %s' % r)
    print('写了：%s' % '、'.join(done))
    return 0


if __name__ == '__main__':
    sys.exit(main())

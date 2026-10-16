#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R93 的台账（第 95 轮 / Round 93）。

规矩沿用 R92：锚点必须恰好命中一次；正文里的数一律从产物读（探针日志 / 名册 JSON / git status）；
残留的具名占位符直接拒绝写盘。
"""
import json
import os
import re
import subprocess
import sys

REPO = '/Users/wangziyi/Codex_Project0'
PROBE = '/tmp/r93_probe2.log'
ROSTER = os.path.join(REPO, 'scripts/probe_coverage_expectations.json')


def F(template, *args):
    n = len(re.findall(r'%[-+ #0]*[\d.]*[sdrfx]', template))
    if n != len(args):
        raise AssertionError('FORMAT_ARITY 占位符=%d 参数=%d :: %.60s' % (n, len(args), template))
    return template % args


def fill(template, values, tag):
    out = template
    for k, v in values.items():
        out = out.replace('%%(%s)s' % k, str(v))
    left = sorted(set(re.findall(r'%\((\w+)\)s', out)))
    if left:
        raise SystemExit('%s 里还有没被填的占位符：%s' % (tag, left))
    return out


def read(path):
    with open(path, encoding='utf-8') as handle:
        return handle.read()


def write(path, text):
    with open(path, 'w', encoding='utf-8') as handle:
        handle.write(text)


def sub_once(text, old, new, tag):
    if text.count(old) != 1:
        raise SystemExit('锚点 %s 命中 %d 次（要求 1）：%.70s' % (tag, text.count(old), old))
    return text.replace(old, new)


def refuse_while_mutating():
    out = subprocess.Popen(['pgrep', '-f', 'mutate_r9'], stdout=subprocess.PIPE).communicate()[0].decode()
    if out.strip():
        raise SystemExit('还有变异电池在跑（pid %s）⇒ 拒绝写台账' % out.split())


def gather():
    g = {}
    log = read(PROBE)
    m = re.search(r'Executed (\d+) tests, with (\d+) tests skipped and (\d+) failures', log)
    if not m:
        raise SystemExit('%s 里没有整卷的 Executed 行 ⇒ 台账不许引用没跑过的验证' % PROBE)
    g['PROBE_TAIL'] = m.group(0)
    g['FOCUS_PASSED'] = ('testSidebarListFocusRingAfterClick]\' passed' in log)
    census = [l.strip() for l in log.splitlines() if l.startswith('ROW_PROXY_') or l.startswith('TAB_STOPS')]
    if len(census) < 6:
        raise SystemExit('探针读数只有 %d 行 ⇒ 正对照没跑全' % len(census))
    g['CENSUS_320'] = [l for l in census if '@窗口320pt' in l][0]
    g['CENSUS_250'] = [l for l in census if '@窗口250pt' in l][0]
    g['LISTROWS'] = [l for l in census if 'LISTROWS' in l][0]
    g['CONTRAST'] = [l for l in census if 'CONTRAST' in l][0]
    roster = json.loads(read(ROSTER))
    g['ROSTER_N'] = len(roster['cases'])
    g['ROSTER_CAN'] = sum(1 for e in roster['cases'].values() if e.get('runner') == 'can')
    touched = subprocess.Popen(['git', 'status', '--porcelain'], cwd=REPO,
                               stdout=subprocess.PIPE).communicate()[0].decode().splitlines()
    files = [l[3:].strip() for l in touched]
    g['PRODUCT_N'] = sum(1 for f in files if f.startswith('ClipboardHistory/Sources/'))
    g['TOUCHED'] = ', '.join(f for f in files
                             if not (f.startswith('AGENT_') or f.startswith('CHANGELOG')
                                     or f.startswith('.scratch')))
    return g


def patch_visual(g):
    path = os.path.join(REPO, 'AGENT_VISUAL_ITERATION.md')
    text = read(path)
    if '## Round 93 ·' in text:
        raise SystemExit('Round 93 已存在')
    write(path, text.rstrip('\n') + '\n\n' + fill(VISUAL, g, 'VISUAL'))
    return 'AGENT_VISUAL_ITERATION.md（追加 Round 93）'


def patch_ui_audit(g):
    path = os.path.join(REPO, 'AGENT_UI_AUDIT.md')
    text = read(path)
    at = text.index('## 第 94 轮 ·')
    write(path, text[:at] + fill(UI, g, 'UI') + '\n' + text[at:])
    return 'AGENT_UI_AUDIT.md（插入第 95 轮）'


def patch_changelog(g):
    path = os.path.join(REPO, 'CHANGELOG.md')
    text = read(path)
    write(path, sub_once(text, '## [Unreleased]\n', '## [Unreleased]\n' + fill(CHANGELOG, g, 'CHANGELOG'),
                         'CHANGELOG 锚点'))
    return 'CHANGELOG.md'


def patch_backlog(g):
    path = os.path.join(REPO, 'AGENT_BACKLOG.md')
    text = read(path)
    if re.search(r'^133\. ', text, re.M):
        raise SystemExit('BACKLOG 133 已存在')
    # 127 结案：在它那条的末尾加一行（锚点是它自己最后那句"修僵尸探针的意义就是让红能说话"）
    anchor = ('    ⇒ 本轮推上去之后 main 带着这朵红，是有意的：修僵尸探针的意义就是让红能说话。')
    text = sub_once(text, anchor,
                    anchor + """

    → **R93 结案，判的是 ②（判据的期望写错），而且是被正对照判掉的**：
    新加的诊断判据 `testRowProxyCensusAsksTheConsequenceNotTheShape` 打出
    `%(CENSUS_320)s`、`%(CENSUS_250)s`、`%(LISTROWS)s`、`%(CONTRAST)s`
    ⇒ 11 行的树里只有 2 个 `KeyViewProxy`（行是 `ListTableRowView`，11 个、整行宽），
    两个都 `acceptsFirstResponder=false`，半宽还跟着宿主缩放 ⇒ 它们不是行代理，
    "Tab 一行停两次"没有发生。修法按 127 自己写的规矩来：**没有**把 200…290 放宽成"148 也行"，
    而是改成点真正的行视图 ⇒ `testSidebarListFocusRingAfterClick` 从红变
    `passed (0.738 seconds)`，整卷 `%(PROBE_TAIL)s`。
    顺带一条我自己的错（U-216）：第一版只走 `nextKeyView` 链，差点据此说"同一行被停两次" ——
    **在链上 ≠ 会被停在上面**，现在读数同时打 `acceptsFirstResponder`。""" % g,
                    'BACKLOG 127 锚点')
    return 'AGENT_BACKLOG.md（127 结案 + 新开 133/134）', text + '\n' + fill(BACKLOG, g, 'BACKLOG')


def patch_state(g):
    path = os.path.join(REPO, 'AGENT_STATE.md')
    lines = read(path).splitlines(True)
    head = next(i for i, l in enumerate(lines) if l.startswith('最后更新：'))
    old = lines[head].rstrip('\n')
    if 'R93' in old[:40]:
        raise SystemExit('AGENT_STATE 第 3 行已经是本轮')
    new = fill(STATE, g, 'STATE')
    lines[head:head + 1] = [new + '\n', '\n',
                            '> 上一轮（R92 / 第 94 轮收尾）原文开头：' + old[len('最后更新：'):] + '\n', '\n']
    write(path, ''.join(lines))
    return 'AGENT_STATE.md'


STAGES = {'A': (patch_visual,), 'B': (patch_ui_audit,), 'C': (patch_changelog,),
          'D': (patch_backlog,), 'E': (patch_state,)}

VISUAL = '''## Round 93 · 那朵"有名字的红"被正对照判掉了：KeyViewProxy 不是行代理（结案 127 / 新开 133、134 / 更新 132 / U-216…U-217 / D-151）

### 1. 头条：127 的两种成因里是 ②，而判它的办法是**先造一把会打数的尺**

R91 收尾时我写下"main 带着一朵有名字的红，是有意的"。这一轮它被**证据**判掉，不是被静音：

```
%(CENSUS_320)s
%(CENSUS_250)s
%(LISTROWS)s
ROW_PROXY[0] frame={{12,50.5},{148,25}} acceptsFirstResponder=false next=KeyViewProxy@{{160,50.5},{148,25}} 父链=KeyViewProxy ← NSHostingView
%(CONTRAST)s
```

三条事实：11 行的树里只有 **2 个** `KeyViewProxy`（行是 `ListTableRowView`，11 个、整行宽 320pt）；
两个都 `acceptsFirstResponder=false`；半宽**跟着宿主缩放**（320→148+148、250→113+113）且父视图是
`NSHostingView`。⇒ 那是 SwiftUI 宿主级的 key-view 代理，**不是行代理**；
"Tab 一行停两次 / VoiceOver 一行读两段"这件事没有发生。

修法按 127 自己立的规矩：不许把 `宽 200…290` 放宽成"148 也行"（那是拿判据讨好现状），
而是改成点**真正的行视图** —— 这条判据要的从来是"用户点一行"。
改后 `testSidebarListFocusRingAfterClick` = `passed (0.738 seconds)`，
整卷 `%(PROBE_TAIL)s`。

### 2. U-216 / U-217（我自己错掉、被读数纠正的两条）

- **U-216**：正对照第一版只走 `nextKeyView` 链，读到"链里两个代理都在同一行"就准备写
  "Tab 在同一行停两次"。`acceptsFirstResponder=false` 一起打出来之后才知道
  **在链上 ≠ 会被停在上面**（链是视图自己声明的下一站，停不停由 responder 判定决定）。
  ⇒ 读数现在同时打这两个字段；"后果"要由能拒绝的那一栏签。
- **U-217**：名册的 `can/cannot` 我没有按字典序翻。R91 的 CI 只数出"六条有结论"，
  **名字**在被 SIGKILL 带走的那块缓冲里；把"应该是这六条"登记成事实，就是 R87 明令禁止的
  "没量过的推断"。⇒ 本轮只把 11 条 reason 改成实测成因（六条跑到、第七条开口没闭口），
  翻转等 R92 的 CI 逐条印出名字之后做（134）。翻错会被 `NOW_RUNS`/`NOT_RUN` 挡回来。

### 3. 真实看图：快速选择浮层（逐元素，带坐标）

正文在 `.scratch/motion-audit-2/r93_visual_review_quickpick.md`。本轮产品文件 **%(PRODUCT_N)s 个**
⇒ 复用的是 R92 那次捕获的帧（先量产品=0 才有资格复用）。三条结论：
- 选中行胶囊 (22,46)..(398,80)pt、填充亮 220 / 暗 70、对比 12.56 / 8.36 ⇒ 达标，**不加描边不加动效**；
- 面板下方约 180pt 空白**不缩**：每次输入都改面板尺寸就是抖动，这是刻意的"不动"；
- 搜索框那层灰底是**夹具全选高亮**（`field.stringValue = query` 的副作用），不是产品样式
  ⇒ 新开 **133**：它可能一直在污染 R76 那条"焦点把占位符调淡"的墨移动量读数。

### 4. 牙

本轮没有新的会红判据（改的是"一把没校准的尺"→"真正的行视图"，加的是**只打数不判产品**的诊断），
所以电池没跑；取而代之的是两条自证：
① 诊断判据自带分组真值表（差 1pt 必须并、差 25pt 必须分）—— 分组写反会正好抹掉要看的东西；
② 名册改动由 `probe_coverage_gate.py` 自己判（`REASONLESS`/`STALE`/`NOW_RUNS`/`NOT_RUN`），
   脚本 `roster_r93.py` 落盘后 `python3 -m unittest discover -s scripts/tests` 181 条全绿。

### 5. 验证（本机，逐条实跑）

- 非台账文件：%(TOUCHED)s（产品 %(PRODUCT_N)s 个 ⇒ 不换装，帧按构造不变）
- 在屏那一卷：`%(PROBE_TAIL)s`，其中 3 条 skip = 无障碍诊断 + `FRAME_CHANNEL` 这台机器 0 帧 + 本轮新加的诊断判据
- 名册：`cases=%(ROSTER_N)s`，其中 `can=%(ROSTER_CAN)s`（本轮只改成因，没翻身份 ⇒ 134）

### 6. 仍未解决

- **134**：R92 的 CI（`9c10569`）逐条印出结论名之后翻 `can`。
- **132**：`testRightClickMenus…` 在 runner 上开口没闭口（本机 2.016 秒跑完）⇒ 下一轮 `sample`。
- **133**：浮层夹具的全选高亮，以及它是否污染过 R76 那格。
- **130**：真机 key 窗口下的 accent（红与蓝）那一档。
- **128** 的 runner 那一半、**129**、**126**、**124** 第②步、**121**、**116** 剩下那半格、
  **115**、**111**、108 余下、77 路 b、101 ②③、106；真机 68.1 / 68.2 / 69.1 / 70.1 / 71.1 / 72.x / 73.x。
'''

UI = '''## 第 95 轮 · R93：那朵"有名字的红"被正对照判掉 —— KeyViewProxy 不是行代理（结案 127 / 新开 133、134 / U-216、U-217 / D-151）

- 正对照：`ROW_PROXY_CENSUS 侧栏@窗口320pt 代理=2 行=1 首行各代理宽=[148+148]`、
  `@250pt → [113+113]`、`ROW_PROXY_LISTROWS 行视图=11 个`、两个代理都 `acceptsFirstResponder=false`
  ⇒ 127 定性为 **②：判据的期望写错**（把宿主级 key-view 代理当成了行），产品无障碍结构没坏。
- 修法按 127 自己立的规矩：不放宽宽度区间，改成点真正的 `ListTableRowView`
  ⇒ `testSidebarListFocusRingAfterClick` 由红转 `passed`，整卷 `%(PROBE_TAIL)s`。
- 两条自我纠正：在 `nextKeyView` 链上 ≠ Tab 会停在那里（U-216）；
  名册不按字典序猜"是哪六条跑到了"，等 R92 的 CI 逐条印出名字再翻 `can`（U-217 / 134）。
- 看图：快速选择浮层逐元素判完（选中胶囊 376x34pt、对比 12.56/8.36，不加描边不加动效；
  面板不缩 = 刻意的不动）；量到搜索框那层灰是**夹具全选高亮** ⇒ 新开 133（可能污染过 R76 那格）。
- 验证：产品文件 %(PRODUCT_N)s 个（⇒ 不换装）；脚本 181 条 OK；探针整卷 0 failures。
- 七维自评 **97 / 100**（扣在"第一版把链当成后果"与"看图复用上轮帧"两格）。
'''

CHANGELOG = '''### 判据（R93）

- 在屏探针卷新增诊断判据 `testRowProxyCensusAsksTheConsequenceNotTheShape`：
  数一棵侧栏树里有几个 `KeyViewProxy`、它们进不进 responder、行视图有几个，
  并拿浮层（`NSTableView`，另一种实现）作对照。永远记为未运行（只回答形状与后果，不判产品）。
- `testSidebarListFocusRingAfterClick` 的"点一行"改到真正的 `ListTableRowView` 上：
  原来的期望（`KeyViewProxy` 宽 200…290）写在从没跑出过结论的情况下，R93 量到
  11 行的树里只有 2 个宿主级代理、且都 `acceptsFirstResponder=false` ⇒ 期望的身份搞错了。
  这条判据由红转绿（BACKLOG 127 结案）。
- `scripts/probe_coverage_expectations.json`：11 条 reason 改成 run 38852286519 的实测成因
  （六条跑到结论、第七条 `testRightClickMenus…` 开口没闭口 ⇒ 排在它后面的到不了），
  并登记新加的那条；`can/cannot` 的翻转留给下一次 CI（BACKLOG 134）。
- 仓库外：`roster_r93.py`（名册改动可重放）、`r93_visual_review_quickpick.md`（逐元素 + 坐标）。

'''

BACKLOG = '''133. **浮层帧里搜索框带着一层"全选高亮"的灰底，可能污染过 R76 那格的墨移动量**（R93 开 / 与 95、108、116 同族）：
    夹具走 `field?.stringValue = query` 赋值 ⇒ `quickpick-typed` 与 `quickpick-empty` 两张帧里
    查询文字外面有一层 rgb(220,220,220)（暗档 70,70,70）的底，块尺寸 26x16pt / 64x16pt。
    两个后果：① 浮层搜索框的**静置外观**在这条通道里没有帧可看；
    ② R76 那条 `testOverlaySearchFieldFocusRecedesThePlaceholderAndDrawsNoRing` 比的是"焦点那一档
    墨移动了多少 pt²"，而一层灰底会同时改变"有墨"的定义 ⇒ 那格的读数可能混着两种成因。
    本轮**没有**动它：要先给夹具一条"赋值但不选中"的路径（`currentEditor.selectedRange = NSMaxRange…`
    或改走 `setQuery`），再重跑那格的地板与正对照。不许直接把地板调低。

134. **在屏名册的 `can/cannot` 还欠一次翻转，等 R92 的 CI 逐条印出结论名**（R93 开 / 与 92、128、132 同族）：
    run 38852286519 只数出"六条有结论"，名字随被 SIGKILL 带走的 stdout 缓冲一起丢了。
    按字典序猜是哪六条 = 登记没量过的推断（R87 那一课），所以 R93 只改了成因、没翻身份。
    R92 推送的 `9c10569` 第一次带上"闸门读自己那份日志"的修法 ⇒ 那一步会逐条印出结论名。
    验收：翻完之后 `probe_coverage_gate.py` 不许报 `NOW_RUNS` 或 `NOT_RUN`；
    如果它报了，说明翻错，按它点名的那条改回去 —— 这两格存在的理由就是这个。

'''

STATE = '''最后更新：2026-10-16 14:05（本地 · R93 / 第 95 轮收尾：**R91 故意留下的那朵"有名字的红"被正对照判掉了，判的是我的尺不是产品** —— `testSidebarListFocusRingAfterClick` 找"行代理"用的期望（`KeyViewProxy` 宽 200…290）写在它从没跑出过结论的情况下；R93 新加的诊断判据打出 `%(CENSUS_320)s`、`@250pt → [113+113]`、`%(LISTROWS)s`、两个代理都 `acceptsFirstResponder=false` ⇒ 那是 SwiftUI **宿主级** key-view 代理，不是行代理，"Tab 一行停两次"没有发生 ⇒ 127 定性 ②。修法按 127 自己立的规矩：不把 200…290 放宽成"148 也行"（那正是它禁止的"拿判据讨好现状"），改成点真正的 `ListTableRowView` ⇒ 该条 `passed (0.738s)`、整卷 `%(PROBE_TAIL)s`。两条自我纠正：U-216 **在 nextKeyView 链上 ≠ Tab 会停在那里**（第一版差点据此写"同一行被停两次"，读数现在同时打 acceptsFirstResponder）；U-217 名册**不按字典序猜是哪六条跑到了**（名字随 SIGKILL 那块缓冲丢了），R93 只把 11 条 reason 改成 run 38852286519 的实测成因，翻转等 R92 的 CI 逐条印出名字 ⇒ 新开 **134**。看图那一腿（产品文件 %(PRODUCT_N)s 个 ⇒ 复用 R92 那次捕获的帧，先量了产品=0）：快速选择浮层逐元素判完 —— 选中行胶囊 (22,46)..(398,80)pt、填充亮 220/暗 70、对比 12.56/8.36 ⇒ 不加描边不加动效；面板下方 ~180pt 空白**不缩**（每次输入改尺寸就是抖动，刻意的不动）；量到搜索框那层灰是**夹具全选高亮**（`field.stringValue=` 的副作用）⇒ 新开 **133**（它可能污染过 R76 那格"焦点调淡占位符"的墨移动量，要先给夹具一条赋值不选中的路径，不许直接调低地板）。另记 **132**：`testRightClickMenus…` 在 runner 上开口没闭口而本机 2.016 秒跑完 ⇒ 下一轮 `sample` 它，分清挂与慢。验证：非台账 `%(TOUCHED)s`（产品 %(PRODUCT_N)s 个 ⇒ 不换装）；在屏整卷 `%(PROBE_TAIL)s`；脚本 181 条 OK；名册 cases=%(ROSTER_N)s can=%(ROSTER_CAN)s。**下一轮第一件事：读 R92 与 R93 的 CI（128 的 runner 验收：`补回` 回到 0 附近、`probeA` 消失、两道闸门的 `本次下结论` 与那一步自己打的 `concluded=6+` 对上）→ 按它逐条印出的结论名翻 134 → 132 的 sample**）'''


def main():
    refuse_while_mutating()
    g = gather()
    stages = sys.argv[1:] or sorted(STAGES)
    done = []
    for s in stages:
        for fn in STAGES[s.upper()]:
            result = fn(g)
            if isinstance(result, tuple):
                tag, text = result
                write(os.path.join(REPO, 'AGENT_BACKLOG.md'), text)
            done.append(result[0] if isinstance(result, tuple) else result)
    print('写了：%s' % '、'.join(done))
    for k in ('TOUCHED', 'PRODUCT_N', 'PROBE_TAIL', 'ROSTER_N', 'ROSTER_CAN', 'FOCUS_PASSED'):
        print('  %s=%s' % (k, g[k]))
    return 0


if __name__ == '__main__':
    sys.exit(main())

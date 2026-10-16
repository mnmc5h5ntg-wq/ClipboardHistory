#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R92 的台账写入（第 94 轮 / AGENT_UI_AUDIT 的 Round 92）。

三条规矩都来自本轮自己踩的坑，不是装饰：
 · 电池在跑就拒写（`mutate_r92_clobber.py` 会临时改仓库文件，那一刻读到的"产物"是变异态）；
 · 每个锚点必须**恰好命中一次**，否则拒绝（R91 的 BACKLOG 124 锚点命中 0 次就是靠这条抓出来的）；
 · 台账里的数一律从 verify 摘要 / 电池日志 / 仪器读数文件里读，不手抄（U-200 那一族）。
"""
import os
import re
import subprocess
import sys

REPO = '/Users/wangziyi/Codex_Project0'
SUM = os.path.join('/tmp', 'r92_verify', 'summary.log')
BATTERY = os.path.join('/tmp', 'r92_verify', 'battery.log')
BEFORE = os.path.join(REPO, '.scratch/motion-audit-2/r92_data_readings_before.log')
AFTER = os.path.join(REPO, '.scratch/motion-audit-2/r92_data_readings_after.log')
SPEC = re.compile(r'%[-+ #0]*[\d.]*[sdrfx%]')


def F(template, *args):
    n = len([m for m in SPEC.finditer(template) if m.group() != '%%'])
    if n != len(args):
        raise AssertionError('FORMAT_ARITY 占位符=%d 参数=%d :: %.60s' % (n, len(args), template))
    return template % args


def read(path):
    with open(path, encoding='utf-8') as handle:
        return handle.read()


def write(path, text):
    with open(path, 'w', encoding='utf-8') as handle:
        handle.write(text)


def refuse_while_mutating():
    out = subprocess.Popen(['pgrep', '-f', 'mutate_r92_clobber.py'],
                           stdout=subprocess.PIPE).communicate()[0].decode()
    if out.strip():
        raise SystemExit('变异电池还在跑（pid %s）⇒ 现在读到的仓库文件是变异态，拒绝生成台账' % out.split())


def key(name, path=SUM, default=None):
    for line in read(path).splitlines():
        if line.startswith(name + '='):
            value = line[len(name) + 1:].strip()
            if value:
                return value
    if default is None:
        raise SystemExit('摘要里 %s 没有值（%s）⇒ 台账不许引用空读数' % (name, path))
    return default


def line_with(needle, path, prefix=''):
    for line in read(path).splitlines():
        if needle in line:
            return prefix + line.strip()
    raise SystemExit('在 %s 里找不到含 %r 的那一行' % (path, needle))


def sub_once(text, old, new, tag):
    count = text.count(old)
    if count != 1:
        raise SystemExit('锚点 %s 命中 %d 次（要求 1）：%.70s' % (tag, count, old))
    return text.replace(old, new)


def fill(template, values, tag):
    """具名填空：`%(KEY)s` 一个一个换，换完还剩 `%(` 就拒绝生成。

    为什么不用 `template % dict`：正文里有 `≥90%`、`99/100` 这种字面 `%`，
    走 %-格式就得先转义一遍 —— 而"忘了转义"的失败模式是 ValueError 或串行，
    两种都不如"点名替换 + 收尾查残留"来得直白。
    """
    out = template
    for k, v in values.items():
        out = out.replace('%%(%s)s' % k, str(v))
    left = sorted(set(re.findall(r'%\((\w+)\)s', out)))
    if left:
        raise SystemExit('%s 里还有没被填的具名占位符：%s' % (tag, left))
    return out


def refuse_stray_placeholders(text, tag):
    stray = sorted(set(re.findall(r'%\(\w+\)s', text)))
    if stray:
        raise SystemExit('%s 里还留着没被替换的占位符：%s' % (tag, stray[:6]))


# ────────────────────────────── 从产物里取数
def gather():
    g = {}
    g['TOUCHED'] = key('TOUCHED_NON_LEDGER')
    g['PRODUCT'] = key('PRODUCT_TOUCHED')
    g['PY'] = key('PY_EXIT')
    g['SCRIPT_TESTS'] = key('SCRIPT_TESTS')
    g['HERMETIC'] = key('HERMETIC_MARKERS_SURVIVED')
    g['BATTERY_EXIT'] = key('BATTERY_EXIT')
    g['BATTERY'] = key('BATTERY')
    g['BUILD_WARNINGS'] = key('BUILD_WARNINGS')
    g['SWIFT'] = key('SWIFT_TEST_EXIT')
    g['SWIFT_TAIL'] = key('SWIFT_TEST_TAIL')
    g['CAPTURE'] = key('CAPTURE_EXIT')
    g['CAPTURE_TAIL'] = key('CAPTURE_TAIL')
    g['BASELINE'] = key('BASELINE')
    # 电池里每一刀的归属（M515 是故意要逃的那一刀）
    g['KNIFE_LINES'] = [l.strip() for l in read(BATTERY).splitlines() if re.match(r'^M5\d\d ', l)]
    # 改前 / 改后的那三句关键读数
    g['B_CARD'] = line_with('卡片#1', BEFORE, '  ')
    g['A_CARD'] = line_with('卡片#1', AFTER, '  ')
    g['B_DIV'] = line_with('分隔线=', BEFORE, '  ')
    g['A_DIV'] = line_with('分隔线=', AFTER, '  ')
    g['PREMISE'] = line_with('PREMISE', AFTER)
    return g


# ────────────────────────────── 各文件的补丁
def patch_visual_iteration(g):
    path = os.path.join(REPO, 'AGENT_VISUAL_ITERATION.md')
    text = read(path)
    if '## Round 92 ·' in text:
        raise SystemExit('Round 92 已经写过了，拒绝重复追加')
    section = fill(VISUAL_SECTION, g, "VISUAL_SECTION")
    refuse_stray_placeholders(section, 'VISUAL_SECTION')
    write(path, text.rstrip('\n') + '\n\n' + section)
    return 'AGENT_VISUAL_ITERATION.md（追加 Round 92）'


def patch_ui_audit(g):
    path = os.path.join(REPO, 'AGENT_UI_AUDIT.md')
    text = read(path)
    anchor = '## 第 93 轮 ·'
    at = text.index(anchor)
    section = fill(UI_SECTION, g, "UI_SECTION")
    refuse_stray_placeholders(section, 'UI_SECTION')
    write(path, text[:at] + section + '\n' + text[at:])
    return 'AGENT_UI_AUDIT.md（插入第 94 轮）'


def patch_decisions(g):
    path = os.path.join(REPO, 'AGENT_DECISIONS.md')
    text = read(path)
    if '### D-150' in text:
        raise SystemExit('D-150 已存在')
    section = fill(DECISION, g, "DECISION")
    refuse_stray_placeholders(section, 'DECISION')
    write(path, text.rstrip('\n') + '\n\n' + section)
    return 'AGENT_DECISIONS.md（追加 D-150）'


def patch_changelog(g):
    path = os.path.join(REPO, 'CHANGELOG.md')
    text = read(path)
    section = fill(CHANGELOG, g, "CHANGELOG")
    refuse_stray_placeholders(section, 'CHANGELOG')
    write(path, sub_once(text, '## [Unreleased]\n', '## [Unreleased]\n' + section, 'CHANGELOG 锚点'))
    return 'CHANGELOG.md'


def patch_backlog(g):
    path = os.path.join(REPO, 'AGENT_BACKLOG.md')
    text = read(path)
    if re.search(r'^128\. ', text, re.M):
        raise SystemExit('BACKLOG 128 已存在')
    section = fill(BACKLOG, g, "BACKLOG")
    refuse_stray_placeholders(section, 'BACKLOG')
    tail = text.rstrip('\n')
    if not tail.endswith('\n'):
        tail += '\n'
    write(path, tail + '\n' + section)
    return 'AGENT_BACKLOG.md（新开 128–131）'


def patch_state(g):
    """本轮摘要顶到第 3 行，R91 那段降为"上一轮原文"，插在它前面（不是替换 line 5）。

    R91 的写法就是"新摘要 + 把上一轮原文插在 R90 那行之前"，所以历史是一层一层往下堆的；
    第一版这里写成"改写 `> 上一轮（R91` 那一行"，而那一行**还不存在** ⇒ StopIteration。
    """
    path = os.path.join(REPO, 'AGENT_STATE.md')
    lines = read(path).splitlines(True)
    head_idx = next(i for i, l in enumerate(lines) if l.startswith('最后更新：'))
    old_head = lines[head_idx].rstrip('\n')
    if old_head.startswith('最后更新：2026-10-16 13:30'):
        raise SystemExit('AGENT_STATE 第 3 行已经是本轮的摘要 ⇒ 拒绝再写一遍')
    new_head = fill(STATE, g, 'STATE')
    prev = '> 上一轮（R91 / 第 93 轮收尾）原文开头：' + old_head[len('最后更新：'):]
    lines[head_idx:head_idx + 1] = [new_head + '\n', '\n', prev + '\n', '\n']
    write(path, ''.join(lines))
    return 'AGENT_STATE.md（本轮摘要顶上去，R91 那段降为"上一轮原文"）'


def patch_backlog92(g):
    """给 BACKLOG 92 补一条结案行（锚点是 R91 收尾时我加的那句"全部读数与时间线见…"）。"""
    path = os.path.join(REPO, 'AGENT_BACKLOG.md')
    text = read(path)
    anchor = '    全部读数与时间线见 `.scratch/motion-audit-2/r91_ci_readings.md`。'
    add = anchor + """

    → **R92 结案（那一格有答案了）**：读到 R91 推送的 CI（run 38852286519）——
    `已下结论的用例: 6`、`started=7`、`UI_PROBE_CHANNELS_AGREE=1`、名册 `源码用例=10 登记=10` 无 STALE。
    ⇒ runner 上不是"一条都跑不到"，僵尸确实是挡在最前面那一个；追了五轮的这一格到此为止。
    第 7 条 `testRightClickMenusAppKitWouldShowAreChinese` 是新的一格，开成 **BACKLOG 132**
    （本机它是跑完的 ⇒ 只做到点名，没在 runner 上 `sample`，不写"同一族"）。"""
    return 'AGENT_BACKLOG.md（92 结案）', sub_once(text, anchor, add, 'BACKLOG 92 锚点')


STAGES = {
    'A': (patch_visual_iteration,),
    'B': (patch_ui_audit,),
    'C': (patch_decisions,),
    'D': (patch_changelog,),
    'E': (patch_backlog,),
    'F': (patch_state,),
    'G': (patch_backlog92,),
}


def main():
    refuse_while_mutating()
    if not os.path.exists(SUM):
        raise SystemExit('没有 %s ⇒ 先跑 verify_r92.sh，台账不许引用没跑过的验证' % SUM)
    if 'VERIFY_OK=1' not in read(os.path.join('/tmp', 'r92_verify_run.log')):
        raise SystemExit('verify 还没到 VERIFY_OK=1，先等它跑完再写台账')
    g = gather()
    stages = sys.argv[1:] or sorted(STAGES)
    done = []
    for s in stages:
        for fn in STAGES[s.upper()]:
            result = fn(g)
            if isinstance(result, tuple):
                tag, text = result
                write(os.path.join(REPO, 'AGENT_BACKLOG.md'), text)
                done.append(tag)
            else:
                done.append(result)
    print('写了：%s' % '、'.join(done))
    print('引用到的读数：')
    for k in ('TOUCHED', 'PRODUCT', 'PY', 'SCRIPT_TESTS', 'HERMETIC', 'BATTERY', 'BATTERY_EXIT',
              'BUILD_WARNINGS', 'SWIFT', 'SWIFT_TAIL', 'CAPTURE', 'CAPTURE_TAIL', 'BASELINE'):
        print('  %s=%s' % (k, g[k]))
    print('  %s' % g['PREMISE'])
    return 0


# ────────────────────────────── 正文模板
VISUAL_SECTION = '''## Round 92 · 两道最终闸门读的是我自己的自检夹具（结案 92、128 的本机那一半 / 新开 129、130、131、132 / U-211…U-215 / D-150）

### 1. 头条：追了五轮的"CI 上一条在屏判据都没跑完"，最后一半成因是**我自己造的**

R91 收尾时读到 R90 的 CI（run 38846896495），两次 run（`a68a08f`、`091d216`）里
`Capture gate` 与 `On-screen probe coverage floor` 都在红，而红话说的是：

```
CAPTURE_GATE_RESULT=fail 日志里没有任何 `Test Case ... passed|failed|skipped` 行
  ⇒ 这一步没跑到用例（挂死、崩溃、或 filter 打错）
UI_PROBE_CHANNELS_CONTRADICT pulse=… started=probeA
```

两句都是**假的**。同一次 run 里捕获那一步自己打的是
`Executed 47 tests, with 9 tests skipped and 0 failures in 177.801 seconds` + `captured frames: 124`；
而 `probeA` 是我自检夹具里的用例名（`TRUNCATED = "Test Case '-[p probeA]' started."`）。

成因：`a68a08f`（R89）为了"那道门一红就吃掉后面七步的证据"，把两步挪到作业末尾加 `if: always()`。
挪的位置是对的。错的是 `scripts/tests/test_ci_report_selftest.py` 的 `run_bash()` 只把
**`/tmp/shots-ci`** 换进临时目录，于是 `cp FAKE_LOG /tmp/frames.log`、`/tmp/ui.log`、`/tmp/motion.log`
写进了**作业自己的共享 /tmp**，把 10 分钟后闸门要读的三份日志覆盖了。

本机实测（不是读代码推的）：往 `/tmp/frames.log` 写一行 `REAL-MARKER`，跑一遍
`python3 -m unittest discover -s scripts/tests`，之后那个文件变成
`Test Case '-[p probeA]' started.`，marker 一行不剩 —— 和 runner 上读到的一模一样。

三次 run 对账（同一把尺、同一个 `/tmp`）：

| run | 提交 | `补回` | `passed` | 闸门 |
| --- | --- | --- | --- | --- |
| 38826160092 | `d44d344`（挪之前） | 0 行 | 38 | ok |
| 38838819089 | `a68a08f`（挪之后第一次） | 402 行 | 0 | fail |
| 38846896495 | `091d216` | 402 行 | 0 | fail |

⇒ 可复现 2/2，不是骰子。`readings=404` 三次一模一样，因为读数文件的路径被换进了临时目录，
真那份从没被自检碰过 —— 所以 `NOT_RUN=49` 那批读数是**真**的，只有结论行是假的。

### 2. 修法（三支，标准一个字没动）

1. `run_bash` 走 `prepare()`：**所有** `/tmp…` 一律映射进这一格的临时目录。
   用通配而不是补清单，因为"清单"正是这次的成因 —— 加一条新的 `/tmp/x.log` 不需要改自检。
   两道边界都要（都是当场踩出来的）：后顾挡住 `tempfile` 的 `tmpab1x/`（早先那版把
   `cp` 的**源**路径改坏了，0 告警那一格凭空变红），前向挡住 `/private/tmp/x` 这种"前缀还有东西"的
   —— 那种不换，交给静态扫描喊红，而不是静默地留一处共享写入。
2. 三条会红的守卫：真值表（每一种 `/tmp` 形状逐条钉）、逐格扫描（交给 bash 的那段脚本里不许还有 `/tmp`）、
   **行为证人**（跑一格真夹具，共享 /tmp 里那四份日志的 mtime/大小必须一模一样，
   而沙箱里必须**确实**多了那份假日志 —— 只断言"真文件没动"会有一种假绿）。
3. `ci_capture_gate.py` 的成因改成三支，全部仍然红：
   读数通道里有**指认这一份文件自己**的同源证人 ⇒ "这一步跑到过，坏的是日志通道"；
   有行但没同源证人 ⇒ "那份读数不可信，既不能证明跑到也不能证明没跑到"；
   两边都空 ⇒ 才是原来那句"没跑到用例"。另加一行 `CAPTURE_GATE_INPUT 日志通道=N 行/M 字节`，
   让红自己带上诊断。

### 3. 真实看图：设置窗口「数据」分区（逐元素，带坐标）

正文在 `.scratch/motion-audit-2/r92_visual_review_data.md`（14 个元素逐个判，加/不加都写理由）。
本轮**真正改的那一条**是分组语言：同一窗口五种分区四套语法，「数据」是唯一一个
"卡片只圈住一部分、其余整段裸在外面、外面还压着分隔线"的。

%(PREMISE)s

| 读数 | 改前 | 改后 |
| --- | --- | --- |
| 卡片 | %(B_CARD)s | %(A_CARD)s |
| 分隔线 | %(B_DIV)s | %(A_DIV)s |

段内动画键、两条回执通道、三颗按钮的禁用逻辑一行未动；改后三颗按钮填充仍然互相相同（差=0）。

### 4. 中途读到 R91 推送的 CI（run 38852286519）：那一卷第一次在 runner 上下了结论

完整读数在 `.scratch/motion-audit-2/r92_ci_readings.md`。四行就够说明问题：

```
ui suite exit: 137  executed: 0  已下结论的用例: 6      ← R90 那一次这里是 0
UI_PROBE_CHANNELS pulse=7 started=7 concluded=6
UI_PROBE_HUNG=testRightClickMenusAppKitWouldShowAreChinese
UI_PROBE_CHANNELS_AGREE=1 （两条通道点的是同一批 ⇒ 心跳那条不是孤证）
```

- **BACKLOG 92 剩下那一格有答案了**：runner 上不是"一条都跑不到"，是跑到 6 条；
  僵尸确实是挡在最前面那一个。名册也对上了（`源码用例=10 登记=10`，没有 STALE）。
- R90 设计的双通道交叉签核第一次兑现"一致时敢点名"（上一轮只证了"不一致时退回只报观察"）。
- 第二具僵尸有名字：`testRightClickMenusAppKitWouldShowAreChinese`（本机 13.8 秒里它是跑完的）
  ⇒ 新开 **BACKLOG 132**，写的是"待测"，不是"和 CoreDrag 同一族"——本轮没在 runner 上 `sample` 它。
- 同一次 run 里两道最终闸门仍然报 `本次下结论=0`，与上面那句 `concluded=6` **直接矛盾** ——
  这就是 128 最好的现场证据：同一个问题两个答案，一个来自真日志、一个来自夹具。

### 5. 我自己错掉、并且被读数纠正的五条（U-211…U-215）

- **U-211**：我把"三颗按钮同填充"写成了产品结论，没先读通道前提（`appActive=false` ⇒ accent 去饱和）。
  中途还怀疑过"是不是禁用态"，去查 fixture 发现 `clearHistoryAction: { nil }` 是**非 nil 闭包**
  ⇒ 按钮是启用态。方向对、结论仍错：真正的解释是通道。⇒ 仪器现在先打 `PREMISE` 行，
  non-key 时 Q2/Q3 只能出 NOT-RUN。
- **U-212**：胶囊检测器抄了 R90 的"色相 ≥25"常数，而这颗胶囊实测色相 22/21 —— 两档都差 3 没检出，
  于是 Q3 被读成"今天没判"。**给没量过的色号写阈值，就会把量到的东西读没。**
- **U-213**："卡片内线"第一版参照页面底色 ⇒ "其余分区 0 条内线"是假的（卡片内的线比的是卡片底色）。
  改成卡片自己的底色 + 整行同方向偏离 ≥90% + 边缘让开 13pt。
- **U-214**：改完之后按钮填充一度报成 247（= 卡片色），因为我把卡片色当填充传进 `ink_of` ——
  于是"墨"里混进按钮自己的灰底。取盒子自己的中位色（228/54）之后，改前改后才可比。
- **U-215**：M511/M514 两把刀**第一次都逃掉了**，各自量出一处真东西：
  M511 逃 = 尾部边界没有用例覆盖（补了 `/tmpbackup/x` 与 `OUT=/tmpwork` 两条）；
  M514 逃 = 自检的临时目录**跨次运行复用**，上一遍那 61 张 PNG 替这一遍作证
  ⇒ 改成每遍一个空目录、跑完删掉。刀逃掉不是电池的失败，是它最有用的时刻。

### 牙（6 刀；M515 是故意要逃的那一刀 = 已知盲区）

%(BATTERY)s

- M510 撤回接线（`run_bash` 只换 `/tmp/shots-ci`）⇒ CAUGHT，而且**只有**行为证人那一格抓到 ——
  静态扫描测的是 `prepare`，被绕开的正是"调不调它"这一层。
- M511 去掉尾部边界 ⇒ CAUGHT（真值表）。
- M512 同源证人放宽成"读数有行就行" ⇒ CAUGHT。
- M513 三支成因并回一支 ⇒ CAUGHT（三格同时红）。
- M514 PNG 落点错位 ⇒ CAUGHT（`test frames -ge 60`）。
- **M515 如期 ESCAPED**：往自检**不认识**的那一步（`Frame baseline vs working manifest`）里
  加一句 `cp /tmp/frames.log …`，全量绿。⇒ 守卫管的是"自检知道的那五步"，不是"作业里所有写 /tmp 的人"。
  这一格开成 **BACKLOG 129**（跨步骤证据挪去 per-job 的 `$RUNNER_TEMP`）。

### 验证（本机，逐条实跑；跑不了的点名）

- 非台账文件 **%(TOUCHED)s 个**（其中 1 个是脚本生成的 `docs/frame_baseline.json`），产品 **1 个**：%(PRODUCT)s
- 构建告警 **%(BUILD_WARNINGS)s**；全量 Swift `%(SWIFT_TAIL)s`（exit %(SWIFT)s）
- 捕获卷 exit %(CAPTURE)s：`%(CAPTURE_TAIL)s`
- 帧基线对账：`%(BASELINE)s`
- 脚本自测 exit %(PY)s：`%(SCRIPT_TESTS)s`
- **头条那条**：写完四份 marker 跑一遍全量自检 ⇒ `HERMETIC_MARKERS_SURVIVED=%(HERMETIC)s`
- 变异电池 exit %(BATTERY_EXIT)s：`%(BATTERY)s`

### 七维自评

| 维度 | 分 | 这一轮扣分的地方 |
| --- | --- | --- |
| 真实看图 | 14/15 | 看了改前改后各两帧（亮/暗），但没看悬停/按下态 —— 那条通道给不了，不是我省了 |
| 判断有据 | 12/15 | 两次把通道的读数写成产品结论（Q2"破坏性没被区分"、Q3"3.53 不达标"），前提行是**事后**补的；顺序反了 |
| 量尺诚实 | 13/15 | 三处尺子坏在被自己发现之前：抄来的色相阈值（U-212）、内线参照错（U-213）、按钮填充取成卡片色（U-214） |
| 原生与克制 | 15/15 | 只动容器；不给破坏性按钮额外染色、不给容器加淡入、不给说明段加 tooltip，三条"不加"都写了理由 |
| 判据有牙 | 13/15 | 6 刀 5 CAUGHT；但 M515 量出覆盖面只是"自检认识的那五步"，且 M511/M514 第一次都逃掉（U-215） |
| 台账可复查 | 14/15 | 本轮所有数都从摘要/电池/读数文件取；扣一分是给 R91 写台账时"读 CI"排在了之后 |
| 收口与记账 | 15/15 | 三支假成因、五条 NOT-RUN、一处已知盲区、一次结案（92）全部点名 |
| **合计** | **96/100** | 低于 90 才继续修；96 但扣的两格都在"前提读晚了"这一族 ⇒ 它已经是本轮的正文与仪器改动，不是待办 |

### 仍未解决

- BACKLOG **128**：本机已修，runner 上"两道闸门第一次读到自己那份日志"要等下一次 CI。
- BACKLOG **129**：跨步骤证据住在共享 `/tmp` 而不是 per-job 的 `$RUNNER_TEMP`（M515 量出来的盲区）。
- BACKLOG **130**：「清空」那颗与侧栏选中胶囊在**真机 key 窗口**里的 accent 那一档（这条通道判不了）。
- BACKLOG **131**：统计页那套"0 卡片 + 1 条外线"要不要一起并进来（要连热图那屏一起判）。
- BACKLOG **132**：`testRightClickMenus…` 在 runner 上是挂还是慢（本轮只点名，没 `sample`）；
  R91 CI 里那 6 条结论**各自是什么判定**（`executed: 0` 与 `concluded=6` 的差是缓冲丢行，
  那 6 行的内容本轮没按步骤名逐条读 —— U-178）。
- **124** 第②步、**127** 的正对照、**126**/119/121/116/115/111/108/77b/101/106；
  真机 68.1 / 68.2 / 69.1 / 70.1 / 71.1 / 72.1 / 72.2 / 73.1 / 73.2。
'''

UI_SECTION = '''## 第 94 轮 · R92：两道最终闸门读的是我自己的自检夹具，而在屏那一卷第一次在 runner 上下了 6 条结论（结案 92、128本机 / 新开 129–132 / U-211…U-215 / D-150）

- 头条：`Capture gate` 的"这一步没跑到用例"与 probe floor 的 `started=probeA` 都是假红 ——
  自检的 `run_bash` 只把 `/tmp/shots-ci` 换进临时目录，`cp FAKE_LOG /tmp/frames.log` 写进了作业共享 /tmp。
  本机实测复现（marker 被覆盖），三次 run 对账（挪位置前 补回=0/passed=38/ok，挪之后两次 402/0/fail）。
- 修：所有 `/tmp` 一律映射进临时目录（通配，不补清单）+ 三条守卫（真值表 / 逐格扫描 / 行为证人）
  + 闸门成因改成三支（同源证人 / 异源 / 两边都空），标准一字未动，另加 `CAPTURE_GATE_INPUT` 自报读到了多大。
- 看图：设置「数据」分区逐元素判完（14 项，含坐标），真正改的是**分组语言** ——
  五种分区四套语法，这一屏是唯一"卡片只圈一部分 + 外面压两条线"的；三段并进一张卡片，线挪进卡片内。
  卡片 (172,106)..(696,158) → (696,318)，外部线 2 → 0，内部线 0 → 2（166pt、271pt），说明段对比 3.59 → 3.64。
- 撤回两条：`appActive=false` 这条通道判不了 accent 派生的红/蓝（U-211）；
  抄来的"色相 ≥25"把一颗量得到的胶囊读成没判（U-212）。
- 牙：6 刀 5 CAUGHT / 1 如期 ESCAPED（M515 = 自检不认识的那一步仍能写共享 /tmp ⇒ BACKLOG 129）。
  另两条刀第一次逃掉，各自量出一处真东西（U-215）。
- 验证：非台账 %(TOUCHED)s 个（产品 1）、构建告警 %(BUILD_WARNINGS)s、全量 exit %(SWIFT)s、
  捕获 exit %(CAPTURE)s、帧 124 张 `%(BASELINE)s`、脚本 exit %(PY)s `%(SCRIPT_TESTS)s`、
  共享 /tmp 四份 marker `%(HERMETIC)s` 存活、电池 exit %(BATTERY_EXIT)s。
- 中途读到 R91 的 CI（run 38852286519）：`已下结论的用例: 6`（R90 是 0）、
  `UI_PROBE_CHANNELS_AGREE=1`、名册 `源码用例=10 登记=10` 无 STALE ⇒ **BACKLOG 92 结案**；
  第 7 条 `testRightClickMenusAppKitWouldShowAreChinese` 吃满 240 秒 ⇒ 新开 132（只点名，没 sample）。
  同一次 run 里两道闸门仍报 `本次下结论=0`，与那句 `concluded=6` 直接矛盾 ⇒ 128 最好的现场证据。
- 七维自评 **96 / 100**（扣在"前提读晚了"、"三处尺子坏在被发现之前"、"守卫覆盖面"三格）。
'''

DECISION = '''### D-150（R92）夹具与闸门：写共享路径的必须被自己钉住，而"读不到结论"不许说成"没跑到"

**背景**：R89 把两道最终闸门挪到作业末尾（理由正当：它们一红就吃掉后面七步的证据），
R90 据此得出"runner 上在屏判据一条都没跑完"，R91 追到一条僵尸探针 —— 都对，但都不完整。
真正让那两道门连着两次红的是：自检 `run_bash()` 只把 `/tmp/shots-ci` 换进临时目录，
其余 `/tmp/frames.log`、`/tmp/ui.log`、`/tmp/motion.log` 是字面量，写进了作业共享的 /tmp。

**决定**：

1. 自检**一律**不许写共享 `/tmp`：`prepare()` 用通配把所有 `/tmp…` 映射进每格的临时目录。
   不用清单，因为"加一条新路径不需要改自检"就是这次的成因。
2. 这件事由三条会红的守卫管：形状真值表、逐格扫描"交给 bash 的那段脚本里不许还有 /tmp"、
   以及**行为证人**（跑一格真夹具，共享 /tmp 那四份日志的 mtime/大小不许变，
   同时沙箱里必须确实多出那份假日志）。静态扫描单独存在不够 —— 它测 `prepare`，
   而上次坏的是"调不调它"那一层（M510 只有行为证人抓到）。
3. 闸门的结论行**必须有证据才许说成因**。"日志里没有结论行"有三种成因（跑到过但通道丢了 /
   读数通道异源 / 真的没跑到），处置完全不同；以前只印最后一种，于是两次假红把我送去了
   查产品与 filter，而该查的是通道。三支**全部保持红**：改的是话，不是标准。
4. 同源证人必须指认**这一份文件**（`CAPTURE_READINGS_SELFTEST … @ <同一路径>`）。
   只要"读数通道有行"就放行，等于让另一卷的读数替这一卷作证 —— 那是 R89 那朵红的原样。

**放弃的方案**：把闸门挪回捕获那一步之后。它能让这次的假红消失，但会把 R89 花一轮换来的
"红不许吃掉后面七步的证据"退回去。位置留着，把共享路径这件事本身修掉。

**代价与后续**：守卫的覆盖面是"自检认识的那五步"。M515 明量了这一点：往
`Frame baseline vs working manifest` 里加一句 `cp /tmp/frames.log …`，全量仍然绿。
彻底的做法是把跨步骤证据搬到 per-job 的 `$RUNNER_TEMP` —— 开成 BACKLOG 129，不在本轮做。
'''

CHANGELOG = '''### 产品（R92）

- 设置窗口「数据」分区的分组语言向多数对齐：三段（历史记录存储 / 导出与导入 / 清空未收藏记录）
  全部进同一张 `GroupBox`，两条原本压在页面底色上的 `Divider()` 挪进卡片内部。
  本机读数：卡片 (172,106)..(696,158) → (172,106)..(696,318)，外部线 2 条 → 0 条，
  内部线 0 条 → 2 条（166pt、271pt），说明段对比 3.59 → 3.64（与通用页 3.74 同档）。
  段内动画键、两条回执通道、三颗按钮的禁用逻辑一行未动。
- 帧基线 `docs/frame_baseline.json` 同提交更新（124 张，CHANGED=2 即这两帧）。

### CI 与判据（R92）

- `scripts/tests/test_ci_report_selftest.py`：`run_bash` 改走 `prepare()`，把**所有** `/tmp…`
  路径映射进每格临时目录（以前只换 `/tmp/shots-ci`，于是 `cp FAKE_LOG /tmp/frames.log`
  覆盖了作业末尾那两道闸门要读的日志）；临时目录改成每遍一个空目录。
- 同文件新增三条守卫：`/tmp` 形状真值表、逐格"生成的命令里不许还有 /tmp"扫描、
  以及"跑一格真夹具之后共享 /tmp 那四份日志不许变"的行为证人。
- `scripts/ci_capture_gate.py`：`没有结论行` 从一句成因改成三支（同源证人 / 异源 / 两边都空），
  全部仍然红；新增 `CAPTURE_GATE_INPUT` 自报读到了多少行多少字节。
- `scripts/tests/test_ci_capture_gate.py`：新增 5 格（三支各一、三句必须互不相同、输入规模行）。

### Docs（R92）

- `AGENT_BACKLOG.md`：新开 128（夹具覆盖共享 /tmp，本机已修、runner 待读）、
  129（跨步骤证据搬去 per-job `$RUNNER_TEMP`）、130（真机 key 窗口里 accent 那一档）、
  131（统计页那套分组要不要并入）；92 补一条"两次假红的真成因"。
- `AGENT_DECISIONS.md`：D-150。`AGENT_VISUAL_ITERATION.md`：Round 92（含 U-211…U-215 与逐元素清单）。
- 仓库外：`r92_data_visual.py` + 改前/改后两份读数、`r92_visual_review_data.md`、
  `mutate_r92_clobber.py`（6 刀）、`verify_r92.sh`、`r91_ci_readings.md`（R90 那次 CI 的完整读数）。

'''

BACKLOG = '''128. **自检夹具覆盖了作业共享 `/tmp`，两道最终闸门连着两次读的是假日志**（R92 开 / 与 92、96、122、125 同族）：
    现象、复现、修法都在 Round 92 正文与 D-150。本机这一半已结：`prepare()` 通配映射 + 三条守卫 +
    闸门三支成因，`HERMETIC_MARKERS_SURVIVED=4/4`，电池 5 CAUGHT / 1 如期 ESCAPED。
    **剩下那一格只有下一次 CI 知道**：`Capture gate` 与 `On-screen probe coverage floor`
    第一次读到"自己那一步留下的日志"，`补回` 应当回到 0 附近、`started=probeA` 这种夹具名字应当消失；
    同时僵尸探针已删（R91），在屏那一卷在 runner 上第一次有资格跑到结论。
    验收：读 R92 的 CI 时按步骤名取那两行，不许跨步骤 grep（U-178）。

129. **跨步骤证据住在共享 `/tmp`，而不是 per-job 的 `$RUNNER_TEMP`**（R92 开 / 与 96、122、128 同族）：
    M515 那把刀明量出来的盲区：`test_cell_commands_never_address_the_shared_tmp` 只扫自检认识的
    那五步，往 `Frame baseline vs working manifest` 里加一句 `cp /tmp/frames.log /tmp/frames-snapshot.log`
    全量仍然绿。⇒ 只要还有一个步骤能写 `/tmp/frames.log`，"闸门读到自己那份日志"就只是暂时的。
    出路：CI 里跨步骤的日志/读数/证人一律写到 `$RUNNER_TEMP`（GitHub 每个 job 独立），
    或至少给每条被下游读的路径加一条"只有它能被写"的登记判据。不在本轮做：它要改的是整条
    步骤间协议，不是某一步的写法。

130. **「清空」那颗与侧栏选中胶囊的 accent 那一档，这条通道判不了**（R92 开 / 与 116、126、104 同族）：
    `SettingsView.swift` 里那颗是 `Button(role:.destructive).buttonStyle(.borderedProminent).tint(.red)`，
    而离屏捕获通道 `面板key=false appActive=false` ⇒ AppKit 把 accent 去饱和成灰。
    本机读数：三颗按钮填充 235/235/235（改前）、228/228/228（改后），红占优=0；
    侧栏选中胶囊 rgb(217,229,251) 配蓝标签 rgb(6,113,245) ⇒ 对比 3.53（暗档 3.47）。
    **这两个数都是通道的读数，不是产品给人的样子。**
    要判的是真机（或至少 key 窗口）里：① 那颗是不是红的、和确认框那颗怎么配合；
    ② 选中胶囊在 key / 非 key 两态下各是什么色号。⇒ 需要用户真机或授权，本轮记 NOT-RUN。

132. **第二具在屏僵尸有名字了：`testRightClickMenusAppKitWouldShowAreChinese` 在 runner 上吃满 240 秒**（R92 开 / 与 92、125、128 同族）：
    R91 推送的 CI（run 38852286519）里 `已下结论的用例: 6`、`started=7`，第 7 条就是它，
    两条通道同意（`UI_PROBE_CHANNELS_AGREE=1`）。本机 R91 那一遍它是**跑完的**（10 条 13.782 秒）
    ⇒ 不是"它一定挂"，是"它在这台 runner 上要么挂要么慢到吃满看门狗"。
    它管的正是人工清单里挂着"要真机"的那一条（R2-22 原生 `NSMenu` 的中文标题）。
    **本轮只做到点名**：没在 runner 上 `sample`，所以不写"和 CoreDrag 同一族"。
    R93 的第一格：在 runner 上给这条加一次 `sample`（或把它单独 `--filter` 出来跑一遍），
    分清"挂死"与"慢"；如果是慢，要量的是慢在哪一段，而不是把 240 秒的看门狗放宽。

131. **统计页那套"0 卡片 + 1 条外线"要不要一起并进来**（R92 开 / 与 36、124 同族）：
    本轮量到五种分区四套分组语法（通用 1/0/0、快捷键 1/0/2、隐私 1/0/3、统计 0/1/0、数据改前 1/2/0），
    只把「数据」这一屏并进了多数语法。统计页是阶段一那个新功能的落点，它没有卡片、
    只有一条压在页面底色上的分隔线 —— 要不要一起并，得连热图那屏的视觉重量一起判
    （热图本身已经是"一块有底色的区域"，再套一层卡片可能反而重）。
    本轮**没有**顺手改它：那需要一次独立的判断，而不是"上一屏改了所以这屏也改"。

'''

STATE = '''最后更新：2026-10-16 13:30（本地 · R92 / 第 94 轮收尾：**两道最终闸门读的是我自己的自检夹具** —— R90 CI（run 38846896495）里 `Capture gate` 那句"这一步没跑到用例"与 probe floor 的 `started=probeA` 都是假红：`probeA` 是我夹具里的用例名，而 `run_bash()` 只把 `/tmp/shots-ci` 换进临时目录，`cp FAKE_LOG /tmp/frames.log`、`/tmp/ui.log`、`/tmp/motion.log` 写进了作业共享的 /tmp，把挪到末尾的两道门要读的日志覆盖了。本机实测复现（写完 marker 跑一遍自检，marker 一行不剩），三次 run 对账钉住"是 R89 挪位置之后才有的"（挪之前 补回=0/passed=38/ok，之后两次 402/0/fail）。修：`prepare()` 通配映射所有 /tmp + 三条守卫（真值表 / 逐格扫描 / 行为证人成对断言）+ 闸门成因改三支（同源证人 / 异源 / 两边都空，标准一字未动）+ `CAPTURE_GATE_INPUT` 自报读到了多大（U-211…U-215、D-150）。中途读到 R91 的 CI（run 38852286519）：删掉僵尸之后在屏那一卷**第一次在 runner 上下了结论** —— `已下结论的用例: 6`、`started=7`、`UI_PROBE_CHANNELS_AGREE=1`、名册 10/10 无 STALE ⇒ **BACKLOG 92 结案**；第 7 条 `testRightClickMenusAppKitWouldShowAreChinese` 吃满 240 秒，本机它是跑完的 ⇒ 新开 132（只点名，没在 runner 上 `sample`，不写"同一族"）；同一次 run 里两道闸门仍报 `本次下结论=0`，与 `concluded=6` 直接矛盾 ⇒ 128 最好的现场证据。牙 M510–M515：5 CAUGHT / 1 如期 ESCAPED（M515 = 自检不认识的那一步仍能写共享 /tmp ⇒ 新开 129），另有两把刀第一次逃掉各自量出真东西（U-215：尾部边界没覆盖、临时目录跨次复用让上一遍的 PNG 替这一遍作证）。真实看图那一腿：设置「数据」分区逐元素判完（14 项带坐标），真正改的是**分组语言** —— 五种分区四套语法，这一屏唯一"卡片只圈一部分 + 外面压两条线"，三段并进一张卡片、线挪进卡片内：卡片 (172,106)..(696,158)→(696,318)、外部线 2→0、内部线 0→2（166pt、271pt）、说明段对比 3.59→3.64（与通用 3.74 同档），动画键/回执/禁用一行未动。**两条结论被读数撤回**：`appActive=false` 这条通道判不了 accent 派生的红与蓝（那颗 `.tint(.red)` 的按钮、那颗选中胶囊 3.53/3.47 都是通道的数，进 130 等真机）；抄来的"色相 ≥25"把一颗量得到的胶囊读成没判（U-212）。验证：非台账文件 %(TOUCHED)s 个（产品 1 个：SettingsView.swift，另 1 个是脚本生成的帧基线清单）；构建告警 %(BUILD_WARNINGS)s；全量 %(SWIFT_TAIL)s（exit %(SWIFT)s）；捕获 exit %(CAPTURE)s `%(CAPTURE_TAIL)s`；帧 124 张 %(BASELINE)s；脚本 exit %(PY)s `%(SCRIPT_TESTS)s`；头条那条 hermeticity：四份 marker `%(HERMETIC)s` 存活；电池 exit %(BATTERY_EXIT)s `%(BATTERY)s`。没跑的：runner 上这两道门第一次读到真日志（128 剩下那一格，只有下一次 CI 知道）；132（`testRightClickMenus…` 在 runner 上是挂还是慢，本轮只点名）；R91 CI 里那 6 条结论各自是什么判定（没按步骤名逐条读，U-178）；「清空」与选中胶囊在真机 key 窗口的 accent 那一档（130）；统计页那套分组要不要并入（131）；BACKLOG 127 的正对照；BACKLOG 124 第②步；BACKLOG 92 剩下那一格。**下一轮第一件事：读 R92 的 CI（`补回` 必须回到 0 附近、`probeA` 这种夹具名必须消失、两道闸门的 `本次下结论` 必须与那一步自己打的 `concluded=6+` 对上），然后 BACKLOG 132 的 `sample` 与 127 的正对照**）'''

if __name__ == '__main__':
    sys.exit(main())

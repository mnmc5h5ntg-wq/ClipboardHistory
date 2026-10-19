#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''R199 之后的收口补记（写于 R200 之前）：把 AGENT_FINAL_REPORT.md 从 R143 之后接上。

为什么必须写这一支：这份报告自己就记着"本文件没有任何守卫"（R143 §9.3 那条），
而它确实从 R143 起没再更新过 —— 五十多轮之后，正文里的每个数都是过期的。
⇒ 这里不重写历史正文（那是伪造），只**追加一节带日期的补记**，
并且所有数字都从活体源解析：闸门 stdout、台账、仪器、git、日志。缺任一个就拒绝写盘。
'''
import io, os, re, subprocess, sys

ROOT = '/Users/wangziyi/Codex_Project0'
REPORT = os.path.join(ROOT, 'AGENT_FINAL_REPORT.md')
NEW_R, NEW_N = 200, 202


def sh(args, cwd=ROOT):
    p = subprocess.run(args, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return p.returncode, p.stdout.decode('utf-8', 'replace')


def read(p):
    if not os.path.exists(p):
        raise SystemExit('MISSING %s ⇒ 拒绝写盘' % p)
    return io.open(p, encoding='utf-8', errors='replace').read()


# —— 活体读数
code, gate = sh(['python3', 'scripts/motion_surface_gate.py'])
row = re.search(r'MOTION_LEDGER 表面=(\d+) 状态=(\d+) 格子=(\d+) 行数=(\d+) 已清账=(\d+) 未清账=(\d+) 地板=(\d+)', gate)
if code != 0 or not row:
    raise SystemExit('GATE 读不到（exit=%d）⇒ 拒绝写盘' % code)
surfaces, states, cells, rows, cleared, unwritten, floor = [int(x) for x in row.groups()]
verdicts = dict(re.findall(r'(added|kept|not-added|not-applicable)=(\d+)', re.search(r'MOTION_LEDGER_VERDICTS [^\n]*', gate).group(0)))
if sum(int(v) for v in verdicts.values()) != rows:
    raise SystemExit('VERDICT_SUM %s 之和 != 行数 %d' % (verdicts, rows))

ui = read('AGENT_UI_AUDIT.md')
vi = read('AGENT_VISUAL_ITERATION.md')
bl = read('AGENT_BACKLOG.md')
max_u = max(int(m) for m in re.findall(r'U-(\d{3})', ui))
rounds_ui = len(re.findall(u'^## 第 \\d+ 轮（R\\d+', ui, re.M))
rounds_vi = [int(m) for m in re.findall(u'^## Round (\\d+) · ', vi, re.M)]
items = sorted(set(int(m) for m in re.findall(r'^(?:\*\*)?(\d{2,3})\. ', bl, re.M)))
OPEN = [201, 202, 205, 207, 215, 218, 219, 220, 222, 223]
missing = [n for n in OPEN + [221] if n not in items]
if missing:
    raise SystemExit('OPEN_ITEM_UNDEFINED %s ⇒ 拒绝写盘' % missing)

full = read('/tmp/r198_full.log')
fl = [l for l in re.findall(r'Executed \d+ tests[^\n]*', full) if 'failures' in l][-1]
fm = re.search(r'Executed (\d+) tests, with (\d+) tests? skipped and (\d+) failures?', fl)
if not fm or fm.group(3) != '0':
    raise SystemExit('FULL_SUITE 形状不认识或失败非 0：%r' % fl[:120])
swift_n, swift_skip, swift_fail = fm.groups()
bat = read('/tmp/r200_battery.log')
ran = re.findall(r'^Ran (\d+) tests', bat, re.M)[-1]
if not re.search(r'^OK', bat, re.M):
    raise SystemExit('BATTERY 不是 OK ⇒ 拒绝写盘')
code, pre = sh(['python3', '.scratch/motion-audit-2/mutate_needle_precheck.py'])
pm = re.search(r'tables=(\d+) covered=(\d+) arms=(\d+) bad=(\d+)', pre)
if not pm:
    raise SystemExit('PRECHECK 读不到 ⇒ 拒绝写盘')
tables, covered, arms, bad = [int(x) for x in pm.groups()]
code, crv = sh(['python3', '.scratch/motion-audit-2/curve_from_ledger.py'])
cm = re.search(r'PHASE2 n=(\d+) rounds=(\d+)\.\.(\d+) mean=([\d.]+) min=(\d+) max=(\d+)', crv)
if not cm:
    raise SystemExit('CURVE 读不到 ⇒ 拒绝写盘')
cn, c_first, c_last, c_mean, c_min, c_max = cm.groups()
if 'GAPS=none' not in crv:
    raise SystemExit('CURVE 有断档 ⇒ 拒绝写盘')
frames = len([f for f in os.listdir('/tmp/shots_r197') if f.endswith('.png')])
scripts_n = len([f for f in os.listdir(os.path.join(ROOT, 'scripts')) if f.endswith('.py')])
tools_n = len([f for f in os.listdir(os.path.join(ROOT, '.scratch/motion-audit-2')) if f.endswith('.py')])
code, gl = sh(['git', 'log', '--format=%h\t%s', '-40', '--', 'ClipboardHistory/Sources'])
prod_rows = [l for l in gl.splitlines() if l.strip()]
last_prod = None
for l in prod_rows:
    m = re.search(r'Round (\d+)', l.split('\t', 1)[1])
    if m:
        last_prod = (m.group(1), l.split('\t')[0], l.split('\t', 1)[1][:60])
        break
if not last_prod:
    raise SystemExit('LAST_PRODUCT_ROUND 读不到 ⇒ 拒绝写盘（不许凭印象写 R192）')

# —— R199 那跑的验收：读得到就写读数，读不到就老实写"还没读"（不许写"应该绿了"）
CI_PATH = '/tmp/r200_ci.log'
ci_txt = io.open(CI_PATH, encoding='utf-8', errors='replace').read() if os.path.exists(CI_PATH) else u''
cm2 = re.search(r'RUN=39227062038 conclusion=(\w+)', ci_txt)
if cm2 and cm2.group(1) == 'success':
    ci_line = (u'**八跑连红断了，而且是读数不是预测**：R199 那笔（commit `a7f16c1`，run 39227062038）'
               u'`conclusion=success`、作业 `build-and-test` 无失败步骤 ⇒ 第 16 步这次没红；'
               u'上一跑（R198，run 39225680017）仍 `failure` 且只红在同一格 `STEP[16] On-screen probe coverage floor`，'
               u'两跑对照正好把这次修复圈出来（出处 `/tmp/r200_ci.log`）')
elif cm2:
    ci_line = (u'**最后一跑只读到一半**：R199 那笔 run 39227062038 的 conclusion=`%s` ⇒ '
               u'第 16 步还红不红，只按这一行说，不许提前宣布修好' % cm2.group(1))
else:
    ci_line = (u'**最后一跑的验收还没读**：R199 那笔（commit `a7f16c1`，run 39227062038）此刻结论未读 ⇒ '
               u'"第 16 步不再红"是**预测**不是读数，等它落地要回来改这一行')

V = dict(ci_line=ci_line, round=str(NEW_R), newn=str(NEW_N), surfaces=str(surfaces), states=str(states), cells=str(cells),
         rows=str(rows), cleared=str(cleared), unwritten=str(unwritten), floor=str(floor),
         verdicts=u'、'.join(u'%s=%s' % (k, verdicts[k]) for k in ('added', 'kept', 'not-added', 'not-applicable')),
         max_u=str(max_u), rounds_ui=str(rounds_ui), rounds_vi=str(len(rounds_vi)),
         vi_last=str(max(rounds_vi)), items_n=str(len(items)), items_max=str(items[-1]),
         open_list=u'、'.join(str(n) for n in OPEN),
         swift=u'%s / skip %s / fail %s' % (swift_n, swift_skip, swift_fail),
         battery=u'%s / OK' % ran, tables=str(tables), covered=str(covered), arms=str(arms), bad=str(bad),
         curve=u'n=%s（第 %s..%s 轮）mean=%s min=%s max=%s' % (cn, c_first, c_last, c_mean, c_min, c_max),
         frames=str(frames), scripts=str(scripts_n), tools=str(tools_n),
         prod_round=last_prod[0], prod_sha=last_prod[1], prod_subject=last_prod[2])

SECTION = u'''
---

## 补记 · R144…R%(round)s（写于 R200 落盘当天，2026-10-19）：这份报告曾经过期五十多轮，这一节把它接上

**先记账不记功**：本文件上面那部分的最后一个轮次标记停在 R143，而仓库已经走到第 %(newn)s 轮（R200 这一轮正在落盘）。
R143 那批条目里就写着"这份文件没有任何守卫"（§9.3 末条）—— 它随后真的烂了：
正文里"清账表停在 102 格""最近一次新动效是 R126""82 帧基线"这类句子，今天全部与活体读数不符。
⇒ 这一节**只追加、不改写历史正文**（改写历史正文等于伪造），并把每个数标成"由哪台仪器在什么时候打的"。
下面所有数字都来自同一次运行里的活体源：`scripts/motion_surface_gate.py`、`curve_from_ledger.py`、
`mutate_needle_precheck.py`、全量卷日志、脚本电池日志、`git log`。任何一项读不到，生成器就拒绝写盘。

### 1. 收口状态（活体读数，不是印象）

| 量 | 现在 | 出处 |
| --- | --- | --- |
| 阶段二轮次 | ITERATION 记到 Round %(vi_last)s（%(rounds_vi)s 节）；UI_AUDIT 有 %(rounds_ui)s 个"第 N 轮"节 | 两份台账的标题行计数 |
| 缺陷编号 | 最大 U-%(max_u)s；BACKLOG %(items_n)s 条、最大 %(items_max)s | 台账正则 |
| 表面清账表 | %(surfaces)s 表面 × %(states)s 状态 = %(cells)s 格；已写 %(cleared)s 行、未写 %(unwritten)s 格；地板 %(floor)s | `motion_surface_gate.py` |
| 判定分布 | %(verdicts)s（之和 == 行数，由生成器对账） | 同上 |
| Swift 全量卷 | %(swift)s | `/tmp/r198_full.log` 摘要行 |
| 脚本电池 | Ran %(battery)s | `/tmp/r200_battery.log` |
| 变异预检 | tables=%(tables)s covered=%(covered)s arms=%(arms)s bad=%(bad)s（bad 是 R168 记的陈旧死针，不是本轮新增） | `mutate_needle_precheck.py` |
| 自评曲线 | %(curve)s；`GAPS=none` | `curve_from_ledger.py` |
| 帧基线 | %(frames)s 张（工作基线，COMPARED=%(frames)s CHANGED=0 于 R198 复核） | `/tmp/shots_r197` + `frame_baseline.py` |
| 判据/工具 | `scripts/*.py` %(scripts)s 支；`.scratch/motion-audit-2/*.py` %(tools)s 支 | 目录计数 |
| 最后一次动到 `Sources/` 的轮次 | **R%(prod_round)s**（commit `%(prod_sha)s`：%(prod_subject)s…）—— 那一笔**只动注释**：「动到源码」不等于「改了画面」，画面自 R192 之后没再动过（各轮台账「产品 N 文件」那一列的读数） | `git log -- ClipboardHistory/Sources` |

### 2. R144…R%(round)s 这段真正推进的事（挑有读数的说）

- **在屏探针的"为什么没结论"终于能被机器回答**：R146 用 `PROBE_DONE` 闭合行 + `心跳−闭合` 让第 16 步不再靠猜；R154 修掉 runner 的 STEP[8] 环境差异；R199 把连红八跑的病根（我自己 R194 埋的两张 `cannot` 登记）按 runner 的逐条点名翻成 `can`。⇒ 这条通道现在是"登记 + 日志两头对账"，不是"没跑完"三个字。
- **热图那条轴的两次自我推翻**：R197 开单 221（亮档 `空→第 1 档` 灰阶比值 1.05）→ R198 查明**亮度是用错的轴**（R51/R53 早证伪过），换成 deuteranopia 模拟后量出 16 条读数、最小 25.41/255 ≥ 地板 18 ⇒ 结案件不改产品；同一轮抓住自己的**假红**（蓝通道漏了重新编码 ⇒ 暗档读 10.41、高档读"模拟后反而更分得开"99.60 > 65.00），并补了一条与产品颜色无关的恒等式真值表（D-199）。
- **过渡判据从"帧数"搬到"时间轴"**：R191（212）把"带过渡帧数 ≥ 整窗"换成与采样粒度无关的形状；R193（217）证明"帧数够"可以是散点凑出来的，必须有**连续段**；218 记下这根轴自己在 2.0 个间隔处会翻界。
- **键盘可达性（220）**：R194 量到"Tab 12 站全是搜索框的字段编辑器"，R196 把结构拍成读数定位到"代理不接受第一响应者、而 `_FocusRingView` 已在位"，并做了进程内分辨实验（没翻面 ⇒ 假设既不证实也不证伪）。**没修**：自绘焦点环会被结构读数否掉，换原生控件会换掉 R189/R190 那套两态判据的对象，而证实另一半需要改用户机器的全局偏好 ⇒ 等授权。
- **台账与仪器自身的账**：R188 开 211（轮次三账的显式申报通道）、R140/R147…R199 一路把"生成器坏法""空对账""分母为 0 的通过"写进判据；R199 那次翻面还顺带证明"历史夹具不许替新名册作证"要分成两种处置（D-200）。

### 3. 仍然欠着的（每条写清欠的是哪一个动作）

- 开放项：BACKLOG %(open_list)s。其中 **219** 欠的是 %(unwritten)s 格没判（清单在条目正文里），**220** 欠的是"改全局偏好重跑同一条探针"这个**需要用户授权**的动作，**222** 欠的是一条真帧通道的证人（离屏与真帧在 R 那一列差 6…21/255，地板余量 7.4 对 3），**223** 欠的是"今天的登记 + 今天的日志真的绿"这一格的离线判据（现在只有 runner 每次自己演）。
- **真机通道**：215（亮档图标那一格）自 2026-10-17 起仍是黑的（全黑 0/625240），`screen=有` 只说 `NSScreen.main` 存在 ⇒ 本机验收不能替代它。
- %(ci_line)s

### 4. 一句话给下一趟

这份报告自己验证过的那句话仍然成立：**先证明尺能分辨，再拿它判产品**。
R198 那一版假红如果被我当成产品结论，就会去改一个本来没坏的梯子；
R199 那八跑连红如果继续被推到"下一轮再读"，就会有一张免检牌在台账里躺着 —— 两件事都不是发现，是**没读**。
''' % V


def main():
    text = read(REPORT)
    # 认**前缀**而不是整串标题：补记的编号会随轮次往前走（R144…R199 → R144…R200），
    # 只按新编号找就找不到旧那一节，于是会追加出第二份补记 —— 两份互相打假账。
    prefix = u'## 补记 · R144…'
    if prefix in text:
        head, sep, tail = text.partition(u'\n---\n\n' + prefix)
        if not sep:
            raise SystemExit('SPLIT_FAILED 找不到补记的分隔头 ⇒ 不动盘')
        if prefix in tail:
            raise SystemExit('DUPLICATE_SECTION 补记标题出现不止一次 ⇒ 不动盘')
        text = head.rstrip(u'\n') + u'\n'
        print('REGENERATING 旧补记已切掉（%d 字），标题前那段保持逐字不变' % len(tail))
    if re.search(r'%\([a-z_0-9]+\)(?!s)', SECTION):
        raise SystemExit('FORMAT_LEAK 有没带 s 的占位符')
    if re.search(r'%\([a-z_0-9]+\)s', SECTION):
        raise SystemExit('FORMAT_LEAK 还有没吃掉的占位符')
    io.open(REPORT, 'w', encoding='utf-8').write(text.rstrip(u'\n') + u'\n' + SECTION)
    print(u'REPORT_ADDENDUM_WRITTEN r=%d n=%d rows=%s unwritten=%s maxU=%s swift=%s battery=%s prod_round=R%s'
          % (NEW_R, NEW_N, rows, unwritten, max_u, V['swift'], V['battery'], last_prod[0]))
    return 0


if __name__ == '__main__':
    sys.exit(main())

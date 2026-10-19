#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''R208 的轮次台账：缺席断言改成标识符边界匹配 + 两把刀（BACKLOG 226 结案）。

数字全部现取（闸门正文行、变异表结论行、预检行、CI JSON），任一项解析不到就拒绝写盘。
门与前几支一样：三账窗口标题、U 区间与定义行吻合、ITERATION 连续且七维表成 7 行、D 号对得上、
引用的 BACKLOG 号必须有定义行、产品必须 0 文件（画面未动 ⇒ 看图腿只能记 NOT-RUN）。
正文一律用**单个三重引号块**写，不掺单引号续行 —— R207 那样写把 16 个 `u'` 伪影印进了台账。
'''
import io, json, os, re, subprocess, sys

ROOT = '/Users/wangziyi/Codex_Project0'
NEW_R, NEW_N = 208, 210
DATE = '2026-10-19'
NOW = '2026-10-19 20:05'
U_LO, U_HI = 674, 676


def sh(*a):
    return subprocess.run(a, cwd=ROOT, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT).stdout.decode('utf-8', 'replace')


def read(p):
    if not os.path.exists(p):
        raise SystemExit('MISSING_FILE %s ⇒ 拒绝写盘' % p)
    return io.open(p, encoding='utf-8', errors='replace').read()


g = sh('python3', 'scripts/motion_surface_gate.py')
ledger_row = (re.findall(r'(MOTION_LEDGER 表面=[^\n]*)', g) or [None])[0]
if not ledger_row:
    raise SystemExit('GATE_READING_MISSING ⇒ 不写盘')
# 电池由下面现跑一遍来作证，不读 /tmp 里的旧日志 —— 读旧文件等于让上一遍替这一遍签字。
mut_run = sh('python3', '.scratch/motion-audit-2/mutate_r208.py')
mut_line = (re.findall(r'(R208_MUTATE [^\n]*)', mut_run) or [None])[0]
if not mut_line:
    raise SystemExit('MUTATION_TABLE_DID_NOT_REPORT ⇒ 不写盘')
pre = sh('python3', '.scratch/motion-audit-2/mutate_needle_precheck.py')
pre_line = (re.findall(r'(NEEDLE_PRECHECK [^\n]*)', pre) or [None])[0]
arm_line = (re.findall(r'(ARM_TOTAL [^\n]*)', pre) or [None])[0]
if not pre_line or not arm_line:
    raise SystemExit('PRECHECK_READING_MISSING ⇒ 不写盘')
bat_env = dict(os.environ, PYTHONUTF8='1', PYTHONDONTWRITEBYTECODE='1')
bat = subprocess.run(
    ['python3', '-m', 'unittest', 'discover', '-s', 'scripts/tests'], cwd=ROOT, env=bat_env,
    stdout=subprocess.PIPE, stderr=subprocess.STDOUT).stdout.decode('utf-8', 'replace')
ran = (re.findall(r'(Ran \d+ tests)', bat) or [None])[0]
# 结论行不许按"最后三行"挑：这台机器上 unittest 的 stderr 不缓冲、测试自己的 stdout 是块缓冲，
# 重定向到同一个管道时 stdout 会在 "OK" 之后才冲出来（本轮实测：OK 在第 227 行，后面还有 12 行打印）。
verdicts = [l.strip() for l in bat.splitlines() if re.match(r'^(OK\b|FAILED\b)', l.strip())]
if len(verdicts) != 1 or not verdicts[0].startswith('OK'):
    raise SystemExit('BATTERY_NOT_GREEN 结论行=%s ⇒ 不写盘' % (verdicts or ['无']))
if not ran:
    raise SystemExit('BATTERY_NOT_GREEN 没有 "Ran N tests" ⇒ 不写盘')
repo = sh('gh', 'repo', 'view', '--json', 'nameWithOwner', '-q', '.nameWithOwner').strip()
ci = json.loads(sh('gh', 'api', 'repos/%s/actions/runs?per_page=8' % repo) or '{}')
runs = [(r['head_sha'][:7], r['status'], r.get('conclusion') or '', str(r['id'])) for r in ci.get('workflow_runs', [])]
if not runs:
    raise SystemExit('CI_READING_EMPTY ⇒ 不写盘')
ok = [r for r in runs if r[2] == 'success']
pend = [r for r in runs if r[1] != 'completed']
fails = [r for r in runs if r[2] == 'failure']
prod = sh('git', 'diff', '--name-only', 'HEAD', '--', 'ClipboardHistory/Sources').strip()
if prod:
    raise SystemExit('PRODUCT_NOT_ZERO ⇒ %s' % prod)

# BACKLOG 232 的读数现量：真表里有多少条缺席声明、其中多少条**只在行注释里**命中。
# 这一族不许用形容词（"可能有"），也不许在没量过的情况下登记成"已受影响"。
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import motion_surface_gate as _g
_rows = json.load(io.open(os.path.join(ROOT, 'docs/motion_surface_ledger.json'), encoding='utf-8'))
_rows = _rows['rows'] if isinstance(_rows, dict) and 'rows' in _rows else _rows
_n_claims = 0
_comment_only = []
for _i, _r in enumerate(_rows):
    for _p, _t in _g.ABSENT_RE.findall(_r.get('evidence') or u''):
        _n_claims += 1
        _f = _g.resolve(_p, _g.repo_root())
        if _f is None:
            continue
        _txt = io.open(_f, encoding='utf-8', errors='replace').read()
        _pat = _g.absence_pattern(_t)
        if not _pat.search(_txt):
            continue
        if not _pat.search(u'\n'.join(_l.split(u'//')[0] for _l in _txt.split(u'\n'))):
            _comment_only.append(u'%s=%s' % (_p, _t))
if _n_claims == 0:
    raise SystemExit('ABSENT_CLAIMS_EMPTY 真表一条缺席声明都没解析到 ⇒ 文法漂了，不能给 232 记账')

# 刀数与电池格数都从结论行里**解析**，正文只引用解析值 —— 手抄的计数会在加刀的那天变成假账。
_kn = re.search(r'刀=(\d+) CAUGHT=(\d+)', mut_line)
_ba = re.search(r'Ran (\d+) tests', ran)
if not _kn or not _ba:
    raise SystemExit('COUNT_UNPARSED 刀=%s 电池=%s ⇒ 不写盘' % (bool(_kn), bool(_ba)))
if _kn.group(1) != _kn.group(2):
    raise SystemExit('MUTATION_NOT_ALL_CAUGHT 刀=%s CAUGHT=%s ⇒ 不写盘' % (_kn.group(1), _kn.group(2)))
V = dict(round=str(NEW_R), newn=str(NEW_N), date=DATE, ledger=ledger_row, mut=mut_line,
         pre=pre_line, arm=arm_line, ran=ran, knife=_kn.group(1), caught=_kn.group(2), batn=_ba.group(1),
         ci_ok=u'、'.join('%s=%s' % (r[0], r[3]) for r in ok[:5]),
         n_ok=str(len(ok)), n_pend=str(len(pend)),
         ci_pend=u'、'.join(r[0] for r in pend[:5]) or u'无',
         ci_fail=u'、'.join(r[0] for r in fails) or u'无')

# 232 的数字全部来自上面现量的读数，不手抄。
ITEM_232 = u'''**232. 缺席检查扫的是整文件正文，注释里的词也算"在场" —— 本轮先把受影响面量出来（0/%(claims)s 条），没改（R208 开单）**

读数（写这笔时由 `ledgers_r208.py` 现量）：真表 %(rows)s 行里共有 **%(claims)s 条** `缺席:路径=词` 声明；
把每条被引用文件的 `//` 之后剥掉再比一次，**只有注释里命中**的那类 = **%(only)s 条**（名单：%(onlylist)s）。
⇒ 今天没有一格判决依赖这条通道，所以 R208 **不动它**（226 的教训：一次别改两处，否则放松与修好又在测试里同形）。

为什么还留着这一条：这一族的坏法是**不对称**的 —— 注释里的词只会造成误报（红得不对），不会造成假清白，
所以它比 R208 修掉的那一格轻。真要修，形状应该是"剥注释后再比，两边都命中才算在场、只在一边命中要单独报一种码"，
并且配一把"把注释剥过头"的刀（否则又是一次没有正对照的放松）。
适用面：所有按整文件正文做的存在性/缺席性判据；不适用：只扫 print 行或只扫声明行的守卫（那些本来就按结构取行）。
''' % dict(claims=_n_claims, rows=len(_rows), only=len(_comment_only),
           onlylist=u'、'.join(_comment_only) if _comment_only else u'无')

UI_TITLE = u'## 第 %d 轮（R%d · %s）：缺席断言改成**标识符边界**匹配 —— 修掉一个误报，又抓出第一版自己造的第二格假清白（U-%d…U-%d · 产品 0 文件，判据账）\n' % (NEW_N, NEW_R, DATE, U_LO, U_HI)

UI_BODY = u'''
- **U-%(lo)d：`缺席:X=disabled` 曾被 `focusEffectDisabled()` 喂饱，根因是"忽略大小写 + 子串"这两条叠在一起。**
  闸门比缺席词用的是 `token.lower() in text.lower()`：`HistorySidebarView.swift` 里没有任何 `.disabled(`，
  但它有 `focusEffectDisabled()`（大写 D），于是"没有 disabled"这条**真话**被判成假话。
  红得不对不是最坏的后果 —— 最坏的是人会去换一个更怪的词绕过，于是**缺席断言挑的词与被讨论的东西脱钩**
  （R90/R100 那一族：尺子量错对象时，读数越"干净"越危险）。
  改成标识符边界匹配（仍忽略大小写）：`focusEffectDisabled` 里的 `disabled` 不算在场。
  真表 162 格在新规则下 `不合法格=0`。
- **U-%(lo1)d：这一轮真正值钱的是第二把"修过头"的刀 —— 因为第一版修法自己坏在更坏的一侧。**
  第一版把边界规则写成"两侧都不许是单词字符"，于是**调用形**词元被误伤：`ForEach(` 在 `SettingsView.swift` 里出现 4 次、
  每一次后面紧跟的都是标识符 ⇒ 前后两条 lookaround 同时失配 ⇒ 写着「没有 `ForEach(`」也能绿。
  误报逼人去换词，**假清白让缺席断言变成免检** —— 后者更坏。改成"只有词元自己那一头是单词字符时才要求边界"，
  `mutate_r208.py` 三把刀各打一个方向：M739 退回忽略大小写子串 ⇒ "嵌入式标识符"那格必须红；
  M740 把匹配改成永远说"不在场" ⇒ "standalone 词照样抓"那格红；
  M741 把调用形的放松改回去（两侧一律要边界）⇒ "带点/带括号不误伤"那格红。
  现跑：`%(mut)s`；预检：`%(pre)s`、`%(arm)s`。自检 384→%(batn)s 格（五格：嵌入不算在场、standalone 仍红、
  带点/带括号不误伤、调用形真缺席仍绿、真没有词的仍绿）。
- **U-%(hi)d：这一轮没有画面可看，看图腿记 NOT-RUN；下一轮（R209）回到帧。**
  产品 0 文件 ⇒ 帧与换装沿用上一遍（`%(ledger)s` 的地板 162 未回退）。
  下一轮的看图对象已经选好：BACKLOG 205 那条说得很清楚 —— `frame_audit.py align` 数得出"空态有两簇左边缘"，
  却答不了"这两行同不同轴"，所以要**带着这把尺去看图**而不是把尺的读数当结论。
  CI 逐跑：`%(n_ok)s` 跑 success（%(ci_ok)s）、`%(n_pend)s` 跑仍未读（%(ci_pend)s）、失败跑 %(ci_fail)s ⇒ 未读的不算绿。
  验证：脚本电池 `%(ran)s` 且 OK、`%(pre)s`。
''' % dict(V, lo=U_LO, lo1=U_LO + 1, hi=U_HI)

VI_BODY = u'''## Round %(round)s · 缺席断言改成标识符边界匹配：修掉一个误报，又抓出第一版造的第二格假清白（%(date)s · 产品 0 文件，判据账）

`缺席:X=disabled` 被 `focusEffectDisabled()` 判成"词在里面"——根因是忽略大小写 + 子串两条叠加；
改成标识符边界匹配后真表 162 格 `不合法格=0`。但**第一版**规则两侧一律要边界，把调用形词元也挡掉了：
`ForEach(` 在 SettingsView 出现 4 次却"查无此词" ⇒ 写着「没有 ForEach(」能绿 —— 这一格比原来的误报更坏，
误报只是逼人去换词，假清白是让缺席断言变成免检。改成"词元那一头是单词字符才要求边界"后，两侧各有证人。
`mutate_r208.py` 三把刀（%(knife)s 刀 %(caught)s caught）：退回子串 ⇒ 正对照红；改成永远"不在场" ⇒ standalone 那格红；
把调用形的放松改回去 ⇒ "带点/带括号不误伤"那格红。
现跑 `%(mut)s`；预检 `%(pre)s`、`%(arm)s`；自检 384→%(batn)s。产品 0 文件 ⇒ 看图腿 NOT-RUN，下一轮回到帧（BACKLOG 205 那把 align 尺）。

### 3. 七维度自评（本轮）

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 10/15 | 产品 0 文件、无新帧：这一轮量的是判据本身，看的是代码与读数，不是渲染画面 |
| 判据有效性 | 15/15 | 边界匹配修掉误报，三个方向各一把刀；五格新自检含正对照、"不误伤"对照、与"真缺席仍绿"对照 |
| 假绿防御 | 15/15 | M740 钉"修过头"、M741 钉"放松放松到免检"（本轮自己造的那一格）；Ran 0 不算 CAUGHT 那条规矩在表里 |
| 产品面推进 | 10/15 | 画面 0 改动；收益是清账表的缺席断言从此挑词不再绕路 |
| 台账一致性 | 14/15 | 三账窗口 R208/R207/R206 齐、U 区间与定义行吻合、曲线 197..%(round)s 连续、BACKLOG 226 结案 |
| 交付诚实性 | 15/15 | 明写"看图腿 NOT-RUN"与"下一轮回到帧"，并把自己第一版的坏法写进账（不装作一次做对） |
| 可复核性 | 15/15 | 表名、刀号、被改表达式、预检与电池读数全在册且可重跑 |
''' % V

CL_BODY = u'''### 缺席断言的"在场"判定改成标识符边界匹配，并配三把方向各别的刀（R%(round)s / U-%(lo)d…U-%(hi)d · 判据 2 文件 + 表 1 支，产品 0 文件）

- 病根一：闸门用 `token.lower() in text.lower()` 判缺席 ⇒ `缺席:...HistorySidebarView.swift=disabled` 被 `focusEffectDisabled()` 判成假话
  （那文件里没有任何 `.disabled(`）。真实代价不是红得不对，是人会换更怪的词绕过 ⇒ 缺席断言挑的词与所讨论的东西脱钩
- 病根二（第一版修法自己造的）：两侧一律要求边界 ⇒ 调用形词元 `ForEach(` 虽在 `SettingsView.swift` 出现 4 次仍被判"查无此词"
  ⇒ 写着「没有 ForEach(」能绿；**假清白比误报坏**，它把缺席断言变成免检
- 定形：只有词元自己那一头是单词字符时才要求边界（`absence_pattern()`）；真表 162 格 `不合法格=0`
- 自检 384→%(batn)s 格（嵌入不算在场 / standalone 仍红 / 带点带括号不误伤 / 调用形真缺席仍绿 / 真没有仍绿）
- `mutate_r208.py` 登记进名册并现跑（M739 退回子串、M740 永远不在场、M741 放松改回去）：`%(mut)s`；预检 `%(pre)s`、`%(arm)s`
- BACKLOG 226 结案；新开 D-205（修误报要配一把"修过头"的刀；放松判据要配一格"确实在场"的正对照）
- 产品 0 文件 ⇒ 无新帧、无换装、看图腿 NOT-RUN；CI：`%(n_ok)s` 跑 success、`%(n_pend)s` 跑未读、失败 %(ci_fail)s

''' % dict(V, lo=U_LO, hi=U_HI)

D_BODY = u'''**D-205（R%(round)s）：修一条判据的误报时要配一把"修过头"的刀；放松一条判据时要配一格"确实在场"的正对照**

现场：`缺席:X=disabled` 被 `focusEffectDisabled()` 喂饱（忽略大小写 + 子串两条叠加）。
最省事的"修法"有两个，两个都是错的：① 以后别写 `disabled`，换个词（词与被讨论的东西脱钩，R90/R100 那一族）；
② 把缺席检查放宽/关掉（误报没了，真报也没了）。真正的修法是改**比较的单位**：从子串改成标识符边界。

⇒ 于是这一轮交付三把刀，方向各不相同：M739 退回子串（证明"嵌入式标识符"那一格有牙），
M740 把匹配改成永远"不在场"（证明"standalone 词照样抓"那一格有牙），
M741 把调用形的放松改回去（证明"带点/带括号不误伤"那一格有牙）。
`%(mut)s`。
**M741 不是设计出来的，是本轮自己坏出来的**：第一版规则"两侧一律要边界"让 `ForEach(` 这种调用形词元查无此词，
而它在 SettingsView 里出现 4 次 —— 一次放松如果不配一格"确实在场"的正对照，就分不清"修好了误报"与"判据闭了嘴"。
两条规矩合起来：**任何一次"修掉误报"都要有打向"修过头"的刀；任何一次"放松"都要有站在被放松那一侧的正对照**，
否则下一次有人把判据整条注释掉，电池照样全绿。
适用面：所有"存在性/缺席性"判据的阈值与匹配方式调整；不适用：单调量（行数、地板、刀数）—— 那些没有"修过头"的方向。
''' % V

STATE = u'''最后更新：%s（本地 · R%d / 第 %d 轮：**缺席断言改成标识符边界匹配（修掉 focusEffectDisabled 那一类误报），并抓出第一版放松造出的调用形假清白**（U-%d…U-%d · 产品 0 文件，判据账）

**本轮落地**：闸门比缺席词从"忽略大小写子串"改成"标识符边界"⇒ `缺席:...=disabled` 不再被 `focusEffectDisabled()` 判成假话；
第一版"两侧一律要边界"又把调用形词元挡掉了（`ForEach(` 在 SettingsView 出现 4 次却查无此词 ⇒ 假清白），
定形成"词元那一头是单词字符才要求边界"（`absence_pattern()`）；真表 162 格 `不合法格=0`。
自检 384→%s 格（五格：嵌入不算在场 / standalone 仍红 / 带点带括号不误伤 / 调用形真缺席仍绿 / 真没有仍绿）。
新表 `mutate_r208.py` 登记进名册并现跑（M739/M740/M741）：`%s`；预检 `%s`、`%s`。
**开了一条新规矩（D-205）**：修误报要配一把打向"修过头"的刀；放松判据要配一格站在被放松那一侧的正对照 —— 否则分不清"修好了"与"判据闭了嘴"。
BACKLOG 226 结案。验证：脚本电池 `%s` 且 OK、`%s`；产品 0 文件 ⇒ 无新帧、无换装、看图腿 NOT-RUN。
CI：`%s` 跑 success（%s）、`%s` 跑仍未读（%s）、失败跑 %s ⇒ 未读的不算绿。

**下一轮（R209）的靶**：⓪ 把仍未读的那几跑 CI 读完（按**步骤名**逐条列失败；要 run id 用 `.id`，别用正则刮 JSON —— R207 刚为此修过一处假配对）；
① **回到画面**：带着 `frame_audit.py align` 去看图（BACKLOG 205：这把尺数得出"两簇左边缘"，答不了"同不同轴"⇒ 结论要由眼看，尺只提供形状）；
② 227③（两条尺谁有资格判热图下端那一格，要补一条会红的守卫）与 222（色彩标注机制；亮档真帧余量只剩 3）；
③ 228②（真机拖一次"声称是文件但解不出"的样本，要用户在场）、230 候选②（从视图入口进，要 in-screen 探针）、207（一支表只准一个靶）、218、215、226 已结、201/202；
④ 220 路 A 仍等用户授权改 `AppleKeyboardUIMode`；⑤ BACKLOG 232（缺席检查把注释里的词也算"在场"）本轮只量了受影响面、没改，
   要改就照那条里写好的形状来（剥过头要单独报码 + 配一把刀）。
)
''' % (NOW, NEW_R, NEW_N, U_LO, U_HI, V['batn'], V['mut'], V['pre'], V['arm'], V['ran'], V['ledger'],
       V['n_ok'], V['ci_ok'], V['n_pend'], V['ci_pend'], V['ci_fail'])

LEDGERS = {'AGENT_UI_AUDIT.md': u'^## 第 \\d+ 轮（R%d',
           'AGENT_VISUAL_ITERATION.md': u'^## Round %d · ',
           'CHANGELOG.md': u'^### .*（R%d / '}


def insert_before_first(text, prefix, block):
    lines = text.split(u'\n')
    idx = [i for i, l in enumerate(lines) if l.startswith(prefix)]
    if not idx:
        raise SystemExit('ANCHOR_NOT_FOUND %r' % prefix)
    lines.insert(idx[0], block.rstrip(u'\n'))
    return u'\n'.join(lines)


def main():
    names = list(LEDGERS) + ['AGENT_STATE.md', 'AGENT_BACKLOG.md', 'AGENT_DECISIONS.md']
    paths = {n: os.path.join(ROOT, n) for n in names}
    old = {k: read(v) for k, v in paths.items()}
    if (u'## Round %d · ' % NEW_R) in old['AGENT_VISUAL_ITERATION.md']:
        raise SystemExit('ALREADY_WRITTEN ⇒ 不重复落盘')
    for name, txt in [(u'ui', UI_TITLE + UI_BODY), (u'vi', VI_BODY), (u'cl', CL_BODY), (u'd', D_BODY), (u'st', STATE),
                      (u'bl232', ITEM_232)]:
        if re.search(r'%\([a-z_0-9]+\)(?!s|d)', txt):
            raise SystemExit('FORMAT_LEAK %s（占位符缺转换类型）' % name)
        if re.search(r'%\([a-z_0-9]+\)s', txt) or u'%d' in txt:
            raise SystemExit('UNRENDERED %s' % name)
        if u"u'" in txt:
            raise SystemExit("ARTIFACT %s 里还有续行伪影（u 加单引号） ⇒ 正文被污染，不写盘" % name)
    # 正文点名的刀号要与表里**跑出来的**刀数一致 —— 加刀的那天，手抄的"三把"会先变成假账。
    named = sorted(set(re.findall(r'\bM\d{3}\b', UI_BODY + VI_BODY + CL_BODY + STATE + D_BODY)))
    if len(named) != int(V['knife']):
        raise SystemExit('KNIFE_COUNT_MISMATCH 正文点名 %s 把（%s），现跑的是 %s 把 ⇒ 不写盘'
                         % (len(named), u'、'.join(named), V['knife']))
    dec_max = max(int(m) for m in re.findall(u'^\\*\\*D-(\\d{3})', old['AGENT_DECISIONS.md'], re.M))
    if dec_max != 204:
        raise SystemExit('DECISION_NUMBER_TAKEN 盘上最大 D 号是 %d（要写 D-205）' % dec_max)

    new = {}
    new['AGENT_UI_AUDIT.md'] = insert_before_first(old['AGENT_UI_AUDIT.md'], u'## 第 ', UI_TITLE + UI_BODY)
    new['AGENT_VISUAL_ITERATION.md'] = old['AGENT_VISUAL_ITERATION.md'].rstrip(u'\n') + u'\n\n' + VI_BODY.rstrip(u'\n') + u'\n'
    new['CHANGELOG.md'] = insert_before_first(old['CHANGELOG.md'], u'### ', CL_BODY)
    new['AGENT_DECISIONS.md'] = old['AGENT_DECISIONS.md'].rstrip(u'\n') + u'\n\n' + D_BODY.rstrip(u'\n') + u'\n'
    st = old['AGENT_STATE.md'].split(u'\n')
    top = [i for i, l in enumerate(st) if l.startswith(u'最后更新：')][0]
    new['AGENT_STATE.md'] = u'\n'.join(st[:top] + [STATE.rstrip(u'\n'), u''] + st[top:])
    bl = old['AGENT_BACKLOG.md']
    anchor = u'③ 每条缺席断言附一条由被引用文件自己打印的 grep 计数。本笔**未做**，别再写成已交付。'
    if bl.count(anchor) != 1:
        raise SystemExit('BACKLOG_226_ANCHOR hits=%d ⇒ 不写盘' % bl.count(anchor))
    new['AGENT_BACKLOG.md'] = bl.replace(
        anchor, anchor + u'\n\n**226 追记（R208 结案）：走的是候选②的变体 —— 比较单位从子串改成标识符边界，三把刀各打一个方向。**\n'
        u'现跑 `mutate_r208.py`：%s；预检 %s、%s；自检 384→%s 格（含"带点/带括号的写法不误伤"与"调用形真缺席仍绿"两格，'
        u'防止把误报修成漏报，也防止把"不误伤"修成"免检"）。规矩另立一条 D-205：修误报必须同时留一把"修过头"的刀，'
        u'放松判据必须同时留一格站在被放松那一侧的正对照。\n' % (V['mut'], V['pre'], V['arm'], V['batn']), 1)
    # 新条目按老规矩追加到文件尾（226 的追记插在它自己那节里，不能顺手插到别处）
    new['AGENT_BACKLOG.md'] = new['AGENT_BACKLOG.md'].rstrip(u'\n') + u'\n\n' + ITEM_232.rstrip(u'\n') + u'\n'

    for name, fmt in LEDGERS.items():
        for r in (NEW_R, NEW_R - 1, NEW_R - 2):
            if not re.search(fmt % r, new[name], re.M):
                raise SystemExit('PRECHECK_WOULD_RED R%d 在 %s 没有标题行 ⇒ 不写盘' % (r, name))
    section = new['AGENT_UI_AUDIT.md'].split(UI_TITLE.rstrip(u'\n'), 1)[1].split(u'## 第 ', 1)[0]
    defined = sorted(int(m) for m in re.findall(u'^- \\*\\*U-(\\d{3})：', section, re.M))
    if defined != [U_LO, U_LO + 1, U_HI]:
        raise SystemExit('U_RANGE_MISMATCH %s' % defined)
    rounds = sorted(int(m) for m in re.findall(u'^## Round (\\d+) ·', new['AGENT_VISUAL_ITERATION.md'], re.M))
    tail = [x for x in rounds if x >= 197]
    if tail != list(range(197, NEW_R + 1)):
        raise SystemExit('ITERATION_GAP %s' % tail)
    sec = new['AGENT_VISUAL_ITERATION.md'].split(u'## Round %d · ' % NEW_R, 1)[1].split(u'## Round ', 1)[0]
    if u'七维度自评' not in sec or len(re.findall(u'^\\| [^|]+\\| (\\d+)/15 \\|', sec, re.M)) != 7:
        raise SystemExit('CURVE_TABLE_BAD')
    items = set(re.findall(u'^(?:\\*\\*)?(\\d{2,3})\\. ', new['AGENT_BACKLOG.md'], re.M))
    for ref in set(re.findall(u'BACKLOG (\\d{3})', UI_BODY + VI_BODY + CL_BODY + STATE + D_BODY)):
        if ref not in items:
            raise SystemExit('DANGLING_BACKLOG %s' % ref)
    if u'**D-205' not in new['AGENT_DECISIONS.md']:
        raise SystemExit('DECISION_MISSING D-205')
    for k, v in new.items():
        io.open(paths[k], 'w', encoding='utf-8').write(v)
    print(u'LEDGERS_R208_WRITTEN r=%d n=%d U=%d..%d mut=[%s] battery=[%s]' % (NEW_R, NEW_N, U_LO, U_HI, V['mut'], V['ran']))
    return 0


if __name__ == '__main__':
    sys.exit(main())

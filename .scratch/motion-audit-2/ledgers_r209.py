#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''R209 的轮次台账：看图腿真做了一遍（三帧 + 两把尺），并把看图读数搬回仓库成一支可复查的尺。

数字全部现取（闸门行、尺的真帧结论行、尺的自检行、电池行、CI JSON、产品 diff），任一项解析不到就拒绝写盘。
本轮变异表 NOT-RUN：判据对象是新写的 python 尺，它自带五格真值表（四种坏法各一红），
刀留给"把这支尺接进 CI 步骤"那一轮一起配 —— 这条欠账写成 BACKLOG 234，不许当成已交付。
正文一律用**单个三重引号块**写，不掺单引号续行（R207 那样写把 16 个伪影印进了台账）。
'''
import io, json, os, re, subprocess, sys

ROOT = '/Users/wangziyi/Codex_Project0'
NEW_R, NEW_N = 209, 211
DATE = '2026-10-19'
NOW = '2026-10-19 20:42'
U_LO, U_HI = 677, 679
SHOTS = '/tmp/shots_r207'


def sh(*a, **kw):
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1')
    env.update(kw.pop('env', {}))
    return subprocess.run(a, cwd=ROOT, env=env, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT).stdout.decode('utf-8', 'replace')


def read(p):
    if not os.path.exists(p):
        raise SystemExit('MISSING_FILE %s ⇒ 拒绝写盘' % p)
    return io.open(p, encoding='utf-8', errors='replace').read()


g = sh('python3', 'scripts/motion_surface_gate.py')
ledger_row = (re.findall(r'(MOTION_LEDGER 表面=[^\n]*)', g) or [None])[0]
if not ledger_row:
    raise SystemExit('GATE_READING_MISSING ⇒ 不写盘')

ax = sh('python3', 'scripts/surface_left_axes.py', '--shots', SHOTS)
ax_line = (re.findall(r'(LEFT_AXIS_VERDICT [^\n]*)', ax) or [None])[0]
ax_rows = re.findall(r'^LEFT_AXIS ([ABC] [^\n]*)', ax, re.M)
if not ax_line or len(ax_rows) != 3:
    raise SystemExit('RULER_DID_NOT_REPORT ⇒ 不写盘（真帧读数缺格：%s）' % ax_rows)
ax_self = sh('python3', 'scripts/surface_left_axes.py', '--self-test')
ax_self_line = (re.findall(r'(LEFT_AXIS_SELFTEST [a-z]+)', ax_self) or [None])[0]
if ax_self_line != 'LEFT_AXIS_SELFTEST ok':
    raise SystemExit('RULER_SELFTEST_NOT_OK %s ⇒ 不写盘' % ax_self_line)

bat = sh('python3', '-m', 'unittest', 'discover', '-s', 'scripts/tests')
_ba = re.search(r'Ran (\d+) tests', bat)
verdicts = [l.strip() for l in bat.splitlines() if re.match(r'^(OK\b|FAILED\b)', l.strip())]
if not _ba or len(verdicts) != 1 or not verdicts[0].startswith('OK'):
    raise SystemExit('BATTERY_NOT_GREEN 结论行=%s ⇒ 不写盘' % (verdicts or ['无']))
ran = 'Ran %s tests' % _ba.group(1)

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

V = dict(round=str(NEW_R), newn=str(NEW_N), date=DATE, ledger=ledger_row, ran=ran,
         ax=ax_line, axA=ax_rows[0], axB=ax_rows[1], axC=ax_rows[2], axself=ax_self_line,
         ci_ok=u'、'.join('%s=%s' % (r[0], r[3]) for r in ok[:5]),
         n_ok=str(len(ok)), n_pend=str(len(pend)),
         ci_pend=u'、'.join(r[0] for r in pend[:5]) or u'无',
         ci_fail=u'、'.join(r[0] for r in fails) or u'无')

UI_TITLE = u'## 第 %d 轮（R%d · %s）：看图腿真做了一遍 —— 三帧 + 两把尺，把"看起来没对齐"量成三条关系判据（U-%d…U-%d · 产品 0 文件，看图账 + 判据账）\n' % (NEW_N, NEW_R, DATE, U_LO, U_HI)

UI_BODY = u'''
- **U-%(lo)d：看图产生的第一句形容词又被自己的尺否掉了（第七次）。**
  浮层 `quickpick-list` 我第一句写的是"搜索框与行内容没对齐"。量出来三条轴各自成轴：
  药丸左缘 22.0pt / 右内缩 22.0pt（**对称，差 0.0pt**）、搜索框占位墨 24.0pt、行图标 35.5pt。
  统计页卡片内三条文字轴全在 148.0pt（跨度 0.0pt），热图网格右缘 558.5pt 而说明文字右缘 678.5pt ⇒ 网格比文字列短 120pt。
  两处都判**不改**，理由写死：网格的格子尺寸是"一天一格"的编码前提，拉宽等于把宽度变成第二个编码通道（同样深浅的两格在不同窗口宽度下会不一样大）；
  浮层那三轴本来就是三种不同控件的三种内缩，没有一条是"错的那一条"。
- **U-%(lo1)d：新尺 `scripts/surface_left_axes.py` 落地，只留关系判据、不留绝对值，并且自带五格真值表。**
  三条规矩：A 对称（药丸左右内缩差 ≤1pt）、B 同轴（同组左轴跨度 ≤1pt）、C 不越过（网格右缘不得越过说明文字右缘）。
  绝对值会把今天的形状钉成契约（R83 那一族），而关系判据在窗口变宽、字号变档时说得出话。
  真值表五格：正对照·今天的样子 ⇒ 绿；药丸只往右缩 ⇒ ASYMMETRIC；月份行换一条轴 ⇒ OFF_AXIS；网格越过文字右缘 ⇒ GRID_PAST_TEXT；全空帧 ⇒ NOT_RUN。
  现跑：`%(axself)s`、真帧 `%(ax)s`。
  **第一版这把尺坏在最坏的一侧**：背景色是从探针窗口自己的众数取的，于是"占满窗口大部分格子的药丸"把背景吃掉，量出左内缩 0.0pt ——
  那是把"对象"当成了"底"。现在底由每颗探针另给的空白窗口取，且要求那块窗口几乎是纯色（不纯色 ⇒ NOT_RUN）。
- **U-%(hi)d：`detail-loading` 是**组件帧**，所以"加载时头部消失"这句假话不能由它作证（新开 233）。**
  我看那张帧时写的第二句怀疑是"详情区加载时头部整块没了"。查代码：`DetailView.selectedEntryView` 是
  `header(for:) + Divider + preview(for:)`（`DetailView.swift:69-72`），头部恒在；那张帧只画了 `DetailLoadingView(reduceMotion:)` 自己。
  ⇒ 组件帧只证明"这一块长什么样"，不证明"它在真实组合里出现时长什么样"；关于相邻关系的结论必须由**组合帧**或产品入口的探针签。
  这一格立成 D-206，覆盖洞开 BACKLOG 233（加载态没有组合帧 ⇒ 头部↔骨架的关系在产物通道上不可判）。
  另两笔账：218 的 runner 分布答案拿到了（同一次代码两跑 `row-insert 开` 连续段 = 0.4 / 1.3 个间隔，而"关"档 = 1.0 / 1.0 ⇒ 这条轴在 runner 上同样分不开两臂 ⇒ **不升硬门**，按 218 自己的处置规矩登记）；
  CI 逐跑：`%(n_ok)s` 跑 success（%(ci_ok)s）、`%(n_pend)s` 跑仍未读（%(ci_pend)s）、失败跑 %(ci_fail)s ⇒ 未读的不算绿。
  验证：脚本电池 `%(ran)s` 且 OK、清账表 `%(ledger)s`；产品 0 文件 ⇒ 无新帧、无换装，看的是 `/tmp/shots_r207` 那 140 张工作基线。
''' % dict(V, lo=U_LO, lo1=U_LO + 1, hi=U_HI)

VI_BODY = u'''## Round %(round)s · 看图腿真做了一遍：三帧 + 两把尺，把"看起来没对齐"量成三条关系判据（%(date)s · 产品 0 文件，看图账 + 判据账）

浮层与统计页各量出三条轴（药丸 22.0/22.0pt 对称、占位墨 24.0pt、行图标 35.5pt；卡片内三轴同在 148.0pt，网格比文字列短 120pt），
两处形容词都被读数否掉 ⇒ 都判**不改**，理由写清（格子尺寸是"一天一格"的编码前提；三种控件三种内缩）。
新尺 `scripts/surface_left_axes.py` 只留关系判据（对称/同轴/不越过）并自带五格真值表；第一版把背景从被量对象自己那块窗口取，
于是药丸把背景吃掉、量出 0.0pt —— 坏在最坏的一侧，已改成"底另给空白窗口 + 不纯色就 NOT_RUN"。
`detail-loading` 是组件帧，所以"加载时头部消失"这句怀疑被代码否掉（头部恒在），覆盖洞开成 233、机制立成 D-206。
218 的 runner 分布答案：两跑 0.4 / 1.3 个间隔 vs 关档 1.0 / 1.0 ⇒ 这条轴在 runner 上也分不开 ⇒ 不升硬门。
现跑 `%(axself)s`、真帧 `%(ax)s`；电池 `%(ran)s` 且 OK。变异表本轮 NOT-RUN（欠账开成 234）。

### 3. 七维度自评（本轮）

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 13/15 | 真看了三帧（详情文本/详情加载/浮层列表/统计页）并各配读数；但没有重捕帧、也没看到组合态的加载画面 |
| 判据有效性 | 13/15 | 新尺三条关系判据各自能红；只在本机承重，还没接进 CI 步骤（234） |
| 假绿防御 | 12/15 | 尺自带五格真值表（四种坏法各一红 + 空帧 NOT_RUN），但本轮没有变异刀 —— 判据被整条注释掉暂时不会红 |
| 产品面推进 | 11/15 | 产品 0 文件；收益是两条"看起来"变成读数，一处覆盖洞被点名 |
| 台账一致性 | 14/15 | 三账窗口 R209/R208/R207 齐、U 区间与定义行吻合、曲线 197..%(round)s 连续、新开 233/234、218 有答案 |
| 交付诚实性 | 15/15 | 把自己看图时说的两句假话（"没对齐"、"头部消失"）逐条撤回并留下否证；NOT-RUN 写明 |
| 可复核性 | 14/15 | 尺、探针坐标、容差、真值表、帧目录全在册；缺 CI 接线那一半 |
''' % V

CL_BODY = u'''### 看图腿：浮层与统计页的左轴量成三条关系判据，新尺 `scripts/surface_left_axes.py` 入库（R%(round)s / U-%(lo)d…U-%(hi)d · 判据 2 文件，产品 0 文件）

- 浮层 `quickpick-list`：药丸左缘 22.0pt / 右内缩 22.0pt（对称差 0.0pt）、占位墨 24.0pt、行图标 35.5pt ⇒ "没对齐"这句撤回
- 统计页：卡片内三条文字轴同在 148.0pt；热图网格右缘 558.5pt、说明文字右缘 678.5pt ⇒ 网格短 120pt，**判为不改**（格子尺寸是一天一格的编码前提）
- 新尺只留关系判据（A 对称 / B 同轴 / C 不越过），容差 1.0pt，探针坐标钉死并断言有墨；空帧 ⇒ NOT_RUN 不给绿
- 第一版的坑记进尺的注释：背景色不许从被量对象自己那块窗口取（药丸把背景吃掉 ⇒ 读出 0.0pt）
- `detail-loading` 是组件帧 ⇒ "加载时头部消失"被 `DetailView.swift:69-72` 否掉；机制立 D-206，覆盖洞开 BACKLOG 233
- 218 结案方向：runner 两跑 `row-insert 开` 连续段 0.4 / 1.3 个间隔、关档 1.0 / 1.0 ⇒ 分不开 ⇒ 不升硬门（登记，见 BACKLOG 218 追记）
- 变异表 NOT-RUN（本轮判据对象是新 python 尺，刀与 CI 接线一起配）⇒ 新开 BACKLOG 234
- 验证：`%(axself)s`、真帧 `%(ax)s`、电池 `%(ran)s` 且 OK、`%(ledger)s`；产品 0 文件 ⇒ 无新帧、无换装

''' % dict(V, lo=U_LO, hi=U_HI)

D_BODY = u'''**D-206（R%(round)s）：组件帧只证明"这一块长什么样"，不证明"它在真实组合里出现时长什么样"**

现场：看 `detail-loading` 时我写下"详情区加载时头部整块消失"。查代码 ——
`DetailView.selectedEntryView` 是 `header(for:) + Divider + preview(for:)`（`DetailView.swift:69-72`），头部恒在；
而那张帧画的是 `DetailLoadingView(reduceMotion:)` 单独一个视图（夹具 `UICaptureHarness.swift:4641`），本来就没有头部。
⇒ 帧是真的，结论是假的：**夹具拍的是组件，我按整屏读**。

规矩：任何形如"某状态下相邻元素还在不在 / 两条轴在真实界面里同不同轴"的结论，必须由**组合帧**（从产品入口把整块面板摆出来）
或产品入口的探针签；组件帧只准回答"这一块自身的形状、颜色、文字"。
为什么不能靠"读代码"补这一格：代码说头部恒在，但**恒在的东西在合成时也可能被挤掉**（R22 的夹具高度、R18 的帧名=尺寸都是同一族），
所以缺的是那张帧，不是那句注释。
适用面：所有按视图单独拍的夹具（`detail-*`、`row-*`、`glass-pill-*`、`notice-banner`）；不适用：整窗夹具（`content-*`、`settings-*`）。
''' % V

ITEM_233 = u'''**233. 加载态没有"组合帧"：头部↔骨架的关系在产物通道上不可判（R209 看图开单，被代码否掉的那句假话就是它欠的读数）**

形状：`detail-loading` 拍的是 `DetailLoadingView` 一个视图，而产品里它永远嵌在
`DetailView.selectedEntryView` 的 `header + Divider + preview` 里（`DetailView.swift:69-72`）。
⇒ 今天没有任何一张帧能回答"加载时头部在不在、头部左缘与骨架左缘同不同轴"，
而我看图时正好把这句话**说错了**（详见 D-206）。现在的近似证人是跨帧比：
`detail-loading` 的条带左缘 vs `detail-2-file` 的头部左缘 —— 那是两张不同的渲染，任何一侧改了内缩都会静默通过。

要做的（下一轮起，先做实验再动产品）：给 `DetailFileView` 的加载分支加一个**注入点**（默认值 = 现行为），
让夹具能确定地画"头部 + 骨架"这一组合，再把那条跨帧比换成同帧内的关系判据（`scripts/surface_left_axes.py` 已经能读左轴，接进去即可）。
不许用"拍得快一点"造这张帧 —— 那是按墙钟判的夹具，R22 记过（夹具自检不许判跑测试的那一刻）。
适用面：详情区加载态；同一族的还有 `row-*` 组件帧（行在 List 里的选中/悬停组合另有 `sidebar-*` 整块帧覆盖）。
'''

ITEM_234 = u'''**234. `surface_left_axes.py` 只在本机承重：没接进 CI 步骤、也没配变异刀（R209 自己记账）**

读数：本轮 R209 的尺现跑 `%(axself)s`、真帧 `%(ax)s`，电池 `%(ran)s` 且 OK —— 但 CI 那一跑里没有它的任何一步，
而本轮**没有** mutate 表（判据对象是新写的 python 尺）。
⇒ 两种坏法今天抓不到：① 有人在 CI 上把这张尺整支注释掉，流水线照绿；② 判据被放宽到恒真（比如把容差改成 999），
本机电池会红（真值表四格反对照），但没有任何一格钉住"CI 上它跑过"。
要补的形状：CI 加一步 `surface_left_axes.py --shots <捕获目录>`（与帧基线同目录，失败即红），
并配一把"把 C 判据改成恒真"的刀 —— 刀与接线同一轮做，因为接线本身会改变尺的读数对象（帧目录从 /tmp 换到 runner 的目录）。
''' % V

STATE = u'''最后更新：%s（本地 · R%d / 第 %d 轮：**看图腿真做了一遍 + 新尺 `surface_left_axes.py` 入库（只留关系判据，自带五格真值表）**（U-%d…U-%d · 产品 0 文件，看图账 + 判据账）

**本轮落地**：浮层三条左轴量成 22.0 / 24.0 / 35.5pt（药丸左右内缩差 0.0pt ⇒ 对称），统计页卡片内三轴同在 148.0pt、
热图网格右缘比说明文字右缘短 120pt ⇒ 两处**都判不改**，理由写进台账（格子尺寸是"一天一格"的编码前提；三种控件三种内缩）。
新尺只留关系判据（A 对称 / B 同轴 / C 不越过，容差 1.0pt，探针坐标钉死且必须读到墨），空帧 ⇒ NOT_RUN 不给绿。
**我自己看图时说的两句假话都撤回了**："搜索框与行没对齐"（量出来各自成轴）、"加载时头部消失"（`DetailView.swift:69-72` 头部恒在，
那张帧是组件帧）⇒ 机制立成 D-206，覆盖洞开成 BACKLOG 233。
218 的 runner 分布答案拿到了：两跑 `row-insert 开` 连续段 0.4 / 1.3 个间隔、"关"档 1.0 / 1.0 ⇒ 这条轴在 runner 上也分不开 ⇒ **不升硬门**（追记已落）。
现跑：`%s`、真帧 `%s`、电池 `%s` 且 OK、清账表 `%s`。
**变异表本轮 NOT-RUN**（判据对象是新 python 尺，刀与 CI 接线同轮配）⇒ 新开 BACKLOG 234。
CI：`%s` 跑 success（%s）、`%s` 跑仍未读（%s）、失败跑 %s ⇒ 未读的不算绿。

**下一轮（R210）的靶**：⓪ 读 `bbc5642` 与本轮这一跑的 CI（按步骤名逐条列失败）；
① 233 的注入点 + 组合帧（详情加载态第一次有组合像素，并把跨帧比换成同帧关系判据）；
② 234：把 `surface_left_axes.py` 接进 CI 步骤 + 配刀（这两件必须同一轮）；
③ 227③、222（亮档真帧余量只剩 3）、215（真机通道能不能拿到第二格读数）、201/202、207；
④ 220 路 A 与 228② 仍等用户（授权改 `AppleKeyboardUIMode` / 真机拖一次样本）。
)
''' % (NOW, NEW_R, NEW_N, U_LO, U_HI, V['axself'], V['ax'], V['ran'], V['ledger'],
       V['n_ok'], V['ci_ok'], V['n_pend'], V['ci_pend'], V['ci_fail'])

APPENDIX = u'''**218 追记（R209）：③ 的 runner 分布拿到了 —— 这条轴在 runner 上同样分不开两臂，所以处置是"不升硬门 + 登记"**

两跑读数（`scripts/ci_read.py readings`，通道 `MOTION_NATIVE`，步骤 `Motion filmstrip (report-only)`）：
run `39247806444`（04ccf7a）`row-insert 开 帧数=3 峰值=0.057 采样≈34ms 过程=0.4个间隔 时长13ms 帧对1`；
run `39247153666`（3073943）`row-insert 开 帧数=4 峰值=0.057 采样≈33ms 过程=1.3个间隔 时长42ms 帧对2`；
同两跑的"关"档 = 1.0 / 1.0 个间隔（帧数恒 1）。
⇒ 开档两跑相差 3 倍（0.4↔1.3），而关档落在它们中间 ⇒ **这条轴不能把两臂分开**，无论阈值压在哪一侧都会随机红。
按本条自己写的处置规矩（"若证明这条轴不稳，正确产物是只能由分布签字并登记成有名字的未覆盖"）：
不升硬门、不放宽、不改产品；`row-insert`/`row-move` 的过程性由 `MOTION_GATE` 那两道 skip 与已登记名单承重，本条继续开着等 ①② 之外的新通道。
''' % V

LEDGERS = {'AGENT_UI_AUDIT.md': u'^## 第 \\d+ 轮（R%d',
           'AGENT_VISUAL_ITERATION.md': u'^## Round %d · ',
           'CHANGELOG.md': u'^### .*（R%d / '}


def insert_before_first(text, prefix, block):
    lines = text.split(u'\n')
    idx = [i for i, l in enumerate(lines) if l.startswith(prefix)]
    if not idx:
        raise SystemExit('ANCHOR_NOT_FOUND %s' % prefix)
    lines.insert(idx[0], block.rstrip(u'\n'))
    return u'\n'.join(lines)


def main():
    names = list(LEDGERS) + ['AGENT_STATE.md', 'AGENT_BACKLOG.md', 'AGENT_DECISIONS.md']
    paths = {n: os.path.join(ROOT, n) for n in names}
    old = {k: read(v) for k, v in paths.items()}
    if (u'## Round %d · ' % NEW_R) in old['AGENT_VISUAL_ITERATION.md']:
        raise SystemExit('ALREADY_WRITTEN ⇒ 不重复落盘')
    for name, txt in [(u'ui', UI_TITLE + UI_BODY), (u'vi', VI_BODY), (u'cl', CL_BODY), (u'd', D_BODY),
                      (u'st', STATE), (u'bl233', ITEM_233), (u'bl234', ITEM_234), (u'bl218', APPENDIX)]:
        if re.search(r'%\([a-z_0-9]+\)(?!s|d)', txt):
            raise SystemExit('FORMAT_LEAK %s（占位符缺转换类型）' % name)
        if re.search(r'%\([a-z_0-9]+\)s', txt) or u'%d' in txt:
            raise SystemExit('UNRENDERED %s' % name)
        if u"u'" in txt:
            raise SystemExit("ARTIFACT %s 里还有续行伪影（u 加单引号） ⇒ 正文被污染，不写盘" % name)
    dec_max = max(int(m) for m in re.findall(u'^\\*\\*D-(\\d{3})', old['AGENT_DECISIONS.md'], re.M))
    if dec_max != 205:
        raise SystemExit('DECISION_NUMBER_TAKEN 盘上最大 D 号是 %d（要写 D-206）' % dec_max)

    new = {}
    new['AGENT_UI_AUDIT.md'] = insert_before_first(old['AGENT_UI_AUDIT.md'], u'## 第 ', UI_TITLE + UI_BODY)
    new['AGENT_VISUAL_ITERATION.md'] = old['AGENT_VISUAL_ITERATION.md'].rstrip(u'\n') + u'\n\n' + VI_BODY.rstrip(u'\n') + u'\n'
    new['CHANGELOG.md'] = insert_before_first(old['CHANGELOG.md'], u'### ', CL_BODY)
    new['AGENT_DECISIONS.md'] = old['AGENT_DECISIONS.md'].rstrip(u'\n') + u'\n\n' + D_BODY.rstrip(u'\n') + u'\n'
    st = old['AGENT_STATE.md'].split(u'\n')
    top = [i for i, l in enumerate(st) if l.startswith(u'最后更新：')][0]
    new['AGENT_STATE.md'] = u'\n'.join(st[:top] + [STATE.rstrip(u'\n'), u''] + st[top:])
    new['AGENT_BACKLOG.md'] = (old['AGENT_BACKLOG.md'].rstrip(u'\n') + u'\n\n'
                               + ITEM_233.rstrip(u'\n') + u'\n\n' + ITEM_234.rstrip(u'\n') + u'\n\n'
                               + APPENDIX.rstrip(u'\n') + u'\n')

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
    if u'**D-206' not in new['AGENT_DECISIONS.md']:
        raise SystemExit('DECISION_MISSING D-206')
    for k, v in new.items():
        io.open(paths[k], 'w', encoding='utf-8').write(v)
    print(u'LEDGERS_R209_WRITTEN r=%d n=%d U=%d..%d battery=[%s] ruler=[%s]'
          % (NEW_R, NEW_N, U_LO, U_HI, ran, ax_line))
    return 0


if __name__ == '__main__':
    sys.exit(main())

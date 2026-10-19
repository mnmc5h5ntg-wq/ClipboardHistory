#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''R210 的轮次台账：把 R209 那支看图尺接进 CI，并给"该红/该跳"两个出口各配一把刀（BACKLOG 234 结案）。

数字全部现取（闸门行、尺的 CI 行、尺自检行、变异表结论行、预检两行、电池行、CI JSON、产品 diff），
任一项解析不到就拒绝写盘。正文一律用**单个三重引号块**写，不掺单引号续行。
'''
import io, json, os, re, subprocess, sys

ROOT = '/Users/wangziyi/Codex_Project0'
NEW_R, NEW_N = 210, 212
DATE = '2026-10-19'
NOW = '2026-10-19 20:48'
U_LO, U_HI = 680, 682
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


ledger_row = (re.findall(r'(MOTION_LEDGER 表面=[^\n]*)', sh('python3', 'scripts/motion_surface_gate.py')) or [None])[0]
if not ledger_row:
    raise SystemExit('GATE_READING_MISSING ⇒ 不写盘')

ci_out = sh('python3', 'scripts/surface_left_axes.py', '--shots', SHOTS, '--ci')
ci_line = (re.findall(r'(LEFT_AXIS_CI [^\n]*)', ci_out) or [None])[0]
if not ci_line or 'verdict=ok' not in ci_line:
    raise SystemExit('RULER_CI_NOT_OK ⇒ %s' % ci_line)
self_line = (re.findall(r'(LEFT_AXIS_SELFTEST [a-z]+)', sh('python3', 'scripts/surface_left_axes.py', '--self-test')) or [None])[0]
if self_line != 'LEFT_AXIS_SELFTEST ok':
    raise SystemExit('RULER_SELFTEST_NOT_OK %s ⇒ 不写盘' % self_line)

mut_out = sh('python3', '.scratch/motion-audit-2/mutate_r210.py')
mut_line = (re.findall(r'(R210_MUTATE [^\n]*)', mut_out) or [None])[0]
if not mut_line:
    raise SystemExit('MUTATION_TABLE_DID_NOT_REPORT ⇒ 不写盘')
pre_out = sh('python3', '.scratch/motion-audit-2/mutate_needle_precheck.py')
pre_line = (re.findall(r'(NEEDLE_PRECHECK [^\n]*)', pre_out) or [None])[0]
arm_line = (re.findall(r'(ARM_TOTAL [^\n]*)', pre_out) or [None])[0]
if not pre_line or not arm_line:
    raise SystemExit('PRECHECK_READING_MISSING ⇒ 不写盘')

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

_kn = re.search(r'刀=(\d+) CAUGHT=(\d+)', mut_line)
if not _kn or _kn.group(1) != _kn.group(2):
    raise SystemExit('MUTATION_NOT_ALL_CAUGHT %s ⇒ 不写盘' % mut_line)
named = sorted(set(re.findall(r'\bM\d{3}\b', u'%(ui)s%(vi)s%(cl)s' % dict(ui='', vi='', cl=''))))

V = dict(round=str(NEW_R), newn=str(NEW_N), date=DATE, ledger=ledger_row, ran=ran,
         ciexit=ci_line, axself=self_line, mut=mut_line, pre=pre_line, arm=arm_line,
         knife=_kn.group(1), caught=_kn.group(2),
         ci_ok=u'、'.join('%s=%s' % (r[0], r[3]) for r in ok[:5]),
         n_ok=str(len(ok)), n_pend=str(len(pend)),
         ci_pend=u'、'.join(r[0] for r in pend[:5]) or u'无',
         ci_fail=u'、'.join(r[0] for r in fails) or u'无')

UI_TITLE = u'## 第 %d 轮（R%d · %s）：看图尺接进 CI —— "该红"与"该跳"是两个出口，各配一把刀（U-%d…U-%d · 产品 0 文件，判据账 + CI 接线）\n' % (NEW_N, NEW_R, DATE, U_LO, U_HI)

UI_BODY = u'''
- **U-%(lo)d：接线的价值全在"它真的能让流水线红"这一格上 —— M742 就是钉这一格的。**
  R209 那支尺只在本机承重（BACKLOG 234 记的就是这笔欠账）。本轮把它接成 CI 的一步
  （`Surface left-axis ruler (BACKLOG 234, wired in R210)`，跑 `--ci`，判据与出口处置全在 python 里 ——
  R64 的教训：shell 里的 awk 没有一份自测能证明它把"该红"和"该跳"分对了）。
  刀 M742 把出口改成 `return 0`（永远不红）⇒ `test_a_real_violation_still_goes_red` 必须红。
  **接了线不承重比不接更坏**：日志里会有一行 `verdict=red` 而流水线照绿，那是在制造"已经管住了"的错觉。
- **U-%(lo1)d：环境缺席不许被报成产品结论 —— 这是相反方向的那把刀（M743）。**
  无头 runner 的高窗只画一条下沿带（BACKLOG 201），所以探针可能取不到墨；那种情况必须走
  `verdict=skipped` + exit 0，并把缺席写成**读数**（`not_run=几颗、missing_frames=几帧`），不是一条沉默。
  M743 把 NOT_RUN 也算进 hard ⇒ `test_absent_frames_are_skipped_not_red` 必须红 —— 这一刀钉的是 R154 那朵假红的形状。
  第三个出口 `verdict=unavailable`（没有像素库）由 `test_missing_pillow_is_unavailable_not_red` 钉，
  装库那一步 `continue-on-error: true`：它失败只该让尺说"我没库"，不该让整条流水线说"产品坏了"。
- **U-%(hi)d：三把刀各打一个方向，加上"容差被放大"那把 ⇒ 尺的牙是可证的，不是声称的。**
  M744 把 `TOL_PT` 从 1.0 改成 999.0 ⇒ 尺自带的四格反对照全部不红 ⇒ `LEFT_AXIS_SELFTEST` 从 ok 变 bad ⇒
  `test_self_test_passes_and_names_every_control` 红。这一刀顺便证明**真值表不是只在正对照上跑过**。
  现跑：`%(mut)s`；预检 `%(pre)s`、`%(arm)s`；CI 模式本机真帧 `%(ciexit)s`；自检 `%(axself)s`；
  电池 `%(ran)s` 且 OK（新增 6 格：CI 四出口 + workflow 两格形状）。清账表 `%(ledger)s`（地板未回退）。
  看图腿本轮 NOT-RUN（没有新帧、也没有重捕，做的是接线与判据）；上一轮的看图读数已经在这支尺里承重。
  CI 逐跑：`%(n_ok)s` 跑 success（%(ci_ok)s）、`%(n_pend)s` 跑仍未读（%(ci_pend)s）、失败跑 %(ci_fail)s ⇒ 未读的不算绿；
  **这一步在 runner 上的第一跑结论还没读到**（本机是 ok，runner 大概率是 skipped —— 两个出口谁替谁签字要由那一跑说，开成 BACKLOG 235）。
''' % dict(V, lo=U_LO, lo1=U_LO + 1, hi=U_HI)

VI_BODY = u'''## Round %(round)s · 把看图尺接进 CI：给"该红"和"该跳"两个出口各配一把刀（%(date)s · 产品 0 文件，判据账 + CI 接线）

R209 的 `surface_left_axes.py` 只在本机承重（BACKLOG 234）。本轮接成 CI 一步（`--ci`，处置逻辑写在 python 里、不写在 shell 里），
并配三把方向各别的刀：M742 把出口改成恒 0（接了线不承重 ⇒ 日志有 `verdict=red` 而流水线照绿）；
M743 把 NOT_RUN 算成真红（无头 runner 高窗只画一条下沿带，BACKLOG 201 ⇒ 环境缺席被报成产品结论，R154 那一族）；
M744 把容差放大到 999pt（判据恒真 ⇒ 尺自带的四格反对照全部不红，顺带证明真值表不是只在正对照上跑过）。
第三个出口 `unavailable`（没有像素库）由装库那一步的 `continue-on-error` 与一格测试钉住。
现跑 `%(mut)s`；预检 `%(pre)s`、`%(arm)s`；本机真帧 `%(ciexit)s`、`%(axself)s`；电池 `%(ran)s` 且 OK。
看图腿本轮 NOT-RUN（无新帧、无重捕）；runner 上这一步的第一跑结论未读 ⇒ BACKLOG 235。

### 3. 七维度自评（本轮）

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 10/15 | 本轮没有看新帧、也没重捕：做的是接线与出口判据；上一轮的看图读数由尺本身继续承重 |
| 判据有效性 | 14/15 | 尺从"只在本机跑"升成 CI 一步，三种出口各有证人；但 runner 那一跑还没读到，有效性只算本机一半 |
| 假绿防御 | 15/15 | 三把刀（恒绿出口 / 缺席算真红 / 容差恒真）全 CAUGHT，且 RESTORE_CLEAN=yes |
| 产品面推进 | 10/15 | 产品 0 文件；收益是像素级关系判据从此在 CI 上承重 |
| 台账一致性 | 14/15 | 三账窗口 R210/R209/R208 齐、U 区间与定义行吻合、曲线 197..%(round)s 连续、234 结案、新开 235 |
| 交付诚实性 | 15/15 | 明写"看图腿 NOT-RUN"与"runner 首跑未读 ⇒ 不许说已交付到 CI" |
| 可复核性 | 15/15 | 步骤名、刀号、被改表达式、预检与电池读数全在册且可重跑 |
''' % V

CL_BODY = u'''### 看图尺接进 CI 一步，并给三种出口各配证人（R%(round)s / U-%(lo)d…U-%(hi)d · 判据 2 文件 + workflow 1 文件 + 表 1 支，产品 0 文件）

- `scripts/surface_left_axes.py` 加 `--ci`：真红 ⇒ exit 1；只有 NOT_RUN ⇒ `verdict=skipped` exit 0（缺席写成读数 not_run/missing_frames）；没有像素库 ⇒ `verdict=unavailable` exit 0
- `.github/workflows/ci.yml` 新增两步：`Pillow for the frame rulers`（continue-on-error）与 `Surface left-axis ruler (BACKLOG 234, wired in R210)`（**不** continue-on-error）
- 判据与出口处置放在 python 而不是 shell：R64 的教训 —— awk 没有一份自测能证明它把"该红"和"该跳"分对了
- `mutate_r210.py` 三把刀：M742 恒绿出口、M743 缺席算真红、M744 容差放大成恒真 ⇒ `%(mut)s`；预检 `%(pre)s`、`%(arm)s`
- 电池 `%(ran)s` 且 OK（新增 6 格：CI 四出口 + workflow 两格形状）；本机真帧 `%(ciexit)s`、`%(axself)s`
- BACKLOG 234 结案；新开 235（这一步在 runner 上的第一跑结论未读 —— 本机 ok 不等于 CI ok）
- 产品 0 文件 ⇒ 无新帧、无换装、看图腿 NOT-RUN

''' % dict(V, lo=U_LO, hi=U_HI)

D_BODY = u'''**D-207（R%(round)s）：一条接进 CI 的像素判据必须有两个分开的出口 —— "产品不合格"与"这台机器量不到"，两侧各配一把刀**

现场：R209 那支尺要在 runner 上跑，就得回答两件事：帧没拍到该不该红？判据真违反该不该红？
把它们合成一个出口，两种坏法都会发生且方向相反 ——
① 缺席也算红：无头 runner 的高窗只画一条下沿带（BACKLOG 201），于是每一步都红，人学会无视这一步（R36/R154 的学费）；
② 红也算不红：把判据写成 report-only，于是它永远绿，而日志里有一行结论冒充"管住了"。
本轮的定形：`verdict=red|skipped|unavailable` 三态 + exit 只在 red 时为 1，
且**每个方向各一把刀**（M742 打"恒绿"、M743 打"把缺席当真红"），再加 M744 打"容差被放大成恒真"。
规矩：**任何新接进 CI 的判据，落地那一轮就要有"把它改成恒绿"的刀**；只有正对照的判据不算接完。
适用面：所有由 runner 执行的像素/产物判据；不适用：编译与单元测试那类"跑不动就是红"的步骤（它们没有"合法缺席"这一态）。
''' % V

ITEM_235 = u'''**235. `Surface left-axis ruler` 在 runner 上的第一跑结论未读：本机 ok 不等于 CI ok（R210 接线当轮开单）**

已知的只有本机：`%(ciexit)s`、`%(axself)s`。runner 上这一步会走哪个出口，取决于两件事，两件都没量过：
① `/tmp/shots-ci` 里有没有 `quickpick-list-420x300-dark.png` 与 `settings-stats-populated-720x540-dark.png`；
② 那两张帧在 runner 上是不是**部分未画**（BACKLOG 201：高窗只画一条下沿带 ⇒ 探针窗口可能整块无墨 ⇒ skipped）。
处置：下一轮第 ⓪ 条读这一跑的 `LEFT_AXIS_CI` 行（按**步骤名**过滤），把结论填回本条；
读出来若是 skipped ⇒ 这条尺在 CI 上暂时只是"能红"而没有"在判"，要按 201 的通道问题另开分辨实验；
读出来若是 ok ⇒ 才允许在台账里把 234 写成"已交付到 CI"。**在那之前 234 只算本机结案。**
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
    for name, txt in [(u'ui', UI_TITLE + UI_BODY), (u'vi', VI_BODY), (u'cl', CL_BODY),
                      (u'd', D_BODY), (u'st', STATE), (u'bl235', ITEM_235)]:
        if re.search(r'%\([a-z_0-9]+\)(?!s|d)', txt):
            raise SystemExit('FORMAT_LEAK %s（占位符缺转换类型）' % name)
        if re.search(r'%\([a-z_0-9]+\)s', txt) or u'%d' in txt:
            raise SystemExit('UNRENDERED %s' % name)
        if u"u'" in txt:
            raise SystemExit("ARTIFACT %s 里还有续行伪影（u 加单引号） ⇒ 正文被污染，不写盘" % name)
    ids = sorted(set(re.findall(r'\bM\d{3}\b', UI_BODY + VI_BODY + CL_BODY + STATE + D_BODY)))
    if len(ids) != int(V['knife']):
        raise SystemExit('KNIFE_COUNT_MISMATCH 正文点名 %s 把（%s），现跑 %s 把 ⇒ 不写盘'
                         % (len(ids), u'、'.join(ids), V['knife']))
    dec_max = max(int(m) for m in re.findall(u'^\\*\\*D-(\\d{3})', old['AGENT_DECISIONS.md'], re.M))
    if dec_max != 206:
        raise SystemExit('DECISION_NUMBER_TAKEN 盘上最大 D 号是 %d（要写 D-207）' % dec_max)

    new = {}
    new['AGENT_UI_AUDIT.md'] = insert_before_first(old['AGENT_UI_AUDIT.md'], u'## 第 ', UI_TITLE + UI_BODY)
    new['AGENT_VISUAL_ITERATION.md'] = old['AGENT_VISUAL_ITERATION.md'].rstrip(u'\n') + u'\n\n' + VI_BODY.rstrip(u'\n') + u'\n'
    new['CHANGELOG.md'] = insert_before_first(old['CHANGELOG.md'], u'### ', CL_BODY)
    new['AGENT_DECISIONS.md'] = old['AGENT_DECISIONS.md'].rstrip(u'\n') + u'\n\n' + D_BODY.rstrip(u'\n') + u'\n'
    st = old['AGENT_STATE.md'].split(u'\n')
    top = [i for i, l in enumerate(st) if l.startswith(u'最后更新：')][0]
    new['AGENT_STATE.md'] = u'\n'.join(st[:top] + [STATE.rstrip(u'\n'), u''] + st[top:])
    new['AGENT_BACKLOG.md'] = (old['AGENT_BACKLOG.md'].rstrip(u'\n') + u'\n\n'
                               + ITEM_235.rstrip(u'\n') + u'\n')

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
    if u'**D-207' not in new['AGENT_DECISIONS.md']:
        raise SystemExit('DECISION_MISSING D-207')
    for k, v in new.items():
        io.open(paths[k], 'w', encoding='utf-8').write(v)
    print(u'LEDGERS_R210_WRITTEN r=%d n=%d U=%d..%d mut=[%s] battery=[%s] ci=[%s]'
          % (NEW_R, NEW_N, U_LO, U_HI, mut_line, ran, ci_line))
    return 0


STATE = u'''最后更新：%s（本地 · R%d / 第 %d 轮：**看图尺接进 CI —— 三种出口（red/skipped/unavailable）各配证人，三把刀全 CAUGHT**（U-%d…U-%d · 产品 0 文件，判据账 + CI 接线）

**本轮落地**：`scripts/surface_left_axes.py` 加 `--ci`（真红才 exit 1；只有 NOT_RUN ⇒ skipped 并把缺席写成读数；没有像素库 ⇒ unavailable），
`.github/workflows/ci.yml` 加两步：装 pillow（continue-on-error）与 `Surface left-axis ruler (BACKLOG 234, wired in R210)`（**不** continue-on-error）。
处置逻辑写在 python 里而不是 shell 里（R64）。新表 `mutate_r210.py`：M742 恒绿出口 / M743 缺席算真红 / M744 容差放大成恒真 ⇒
`%s`；预检 `%s`、`%s`。规矩立成 **D-207**：任何新接进 CI 的判据，落地那一轮就要有"把它改成恒绿"的刀。
电池 `%s` 且 OK（新增 6 格）；本机真帧 `%s`、`%s`；清账表 `%s`。
**BACKLOG 234 只算本机结案**：这一步在 runner 上的第一跑结论未读 ⇒ 新开 235，下一轮第 ⓪ 条读它。
CI：`%s` 跑 success（%s）、`%s` 跑仍未读（%s）、失败跑 %s ⇒ 未读的不算绿。

**下一轮（R211）的靶**：⓪ 读本轮这一跑的 CI，按**步骤名**过滤 `LEFT_AXIS_CI` 那一行（ok / skipped / unavailable 三种出口谁出现），
并把 235 填回账；顺带把 `bbc5642` 之后仍未读的那几跑逐条落账；
① 233：详情加载态的组合帧注入点（产品半：给 `DetailFileView` 的加载分支一个默认值=现行行为的 seam）+ 把跨帧比换成同帧关系判据；
② 227③、222（亮档真帧余量只剩 3）、215（真机通道的第二格读数）、201/202、207；
③ 回到画面：本轮看图腿 NOT-RUN，下一轮至少看两帧新拍的（换夹具或换档）；
④ 220 路 A 与 228② 仍等用户（授权改 `AppleKeyboardUIMode` / 真机拖一次样本）。
)
''' % (NOW, NEW_R, NEW_N, U_LO, U_HI, V['mut'], V['pre'], V['arm'], V['ran'], V['ciexit'],
       V['axself'], V['ledger'], V['n_ok'], V['ci_ok'], V['n_pend'], V['ci_pend'], V['ci_fail'])


if __name__ == '__main__':
    sys.exit(main())

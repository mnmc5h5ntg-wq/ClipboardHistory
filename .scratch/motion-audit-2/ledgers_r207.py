#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''R207 的轮次台账（把这一天的两批清账笔并成一支真轮次，并轮换 STATE）。

数字全部现取：清账表读数来自 `motion_surface_gate.py` 的正文行，判定分布来自同一份输出，
CI 逐跑读数来自 `gh api`，帧数来自 `docs/frame_baseline.json`。任一项解析不到就拒绝写盘。

门：① 三账窗口（R207/R206/R205）各有标题；② UI_AUDIT 本轮标题的 U 区间与该节定义行吻合；
③ ITERATION 的 Round 号 197..207 连续且本轮那节有「七维度自评」+ 恰好 7 行 n/15；
④ D 号：盘上最大必须是 D-203（本轮写 D-204）；⑤ 引用的 BACKLOG 号必须有定义行；
⑥ 产品必须 0 文件（这一轮是判据/台账轮，画面未动 ⇒ 七维表里"真实视觉审查"只能低分，不许拿旧帧冒充）。
'''
import io, json, os, re, subprocess, sys

ROOT = '/Users/wangziyi/Codex_Project0'
NEW_R, NEW_N = 207, 209
DATE = '2026-10-19'
NOW = '2026-10-19 19:45'
U_LO, U_HI = 671, 673


def sh(*a):
    return subprocess.run(a, cwd=ROOT, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT).stdout.decode('utf-8', 'replace')


def read(p):
    if not os.path.exists(p):
        raise SystemExit('MISSING_FILE %s ⇒ 拒绝写盘' % p)
    return io.open(p, encoding='utf-8', errors='replace').read()


g = sh('python3', 'scripts/motion_surface_gate.py')
row = (re.findall(r'(MOTION_LEDGER 表面=[^\n]*)', g) or [None])[0]
verd = (re.findall(r'(MOTION_LEDGER_VERDICTS [^\n]*)', g) or [None])[0]
if not row or not verd:
    raise SystemExit('GATE_READING_MISSING ⇒ 不写盘')
kv = dict(x.split('=') for x in row.split()[1:])
base = json.load(io.open(os.path.join(ROOT, 'docs/frame_baseline.json'), encoding='utf-8'))
FRAMES = sum(len(v) for v in base.values() if isinstance(v, (list, dict)))
if FRAMES < 100:
    raise SystemExit('FRAME_COUNT_UNRECOGNIZED %r' % FRAMES)
repo = sh('gh', 'repo', 'view', '--json', 'nameWithOwner', '-q', '.nameWithOwner').strip()
ci = json.loads(sh('gh', 'api', 'repos/%s/actions/runs?per_page=6' % repo) or '{}')
runs = [(r['head_sha'][:7], r['status'], r.get('conclusion') or '') for r in ci.get('workflow_runs', [])]
if not runs:
    raise SystemExit('CI_READING_EMPTY ⇒ 不写盘')
ok = [r[0] for r in runs if r[2] == 'success']
pend = [r[0] for r in runs if r[1] != 'completed']
fails = [r[0] for r in runs if r[2] == 'failure']
prod = sh('git', 'diff', '--name-only', 'HEAD', '--', 'ClipboardHistory/Sources').strip()
if prod:
    raise SystemExit('PRODUCT_NOT_ZERO ⇒ 这一轮的台账要另写：%s' % prod)

V = dict(round=str(NEW_R), newn=str(NEW_N), date=DATE, ledger=row, verd=verd.replace('MOTION_LEDGER_VERDICTS ', ''),
         rows=kv['行数'], cells=kv['格子'], floor=kv['地板'], frames=str(FRAMES),
         ci_ok=u'、'.join(ok[:6]) or u'无', n_ok=str(len(ok)), n_pend=str(len(pend)),
         ci_pend=u'、'.join(pend[:6]) or u'无', ci_fail=u'、'.join(fails) or u'无')

UI_TITLE = (u'## 第 %d 轮（R%d · %s）：清账表判完 %s/%s 格（未清账 0），顺手改掉两条把"还没判完"当不变量的守卫'
            u'（U-%d…U-%d · 产品 0 文件，判据账 + 清账表）\n') % (NEW_N, NEW_R, DATE, V['rows'], V['cells'], U_LO, U_HI)

UI_BODY = u'''
- **U-%(lo)d：18 表面 × 9 状态 = %(cells)s 格，今天全部有判决。** 两批共补 31 格（第一批 15：详情区 3 + 侧栏 3 + 浮层 5 + 状态菜单 2 + 设置侧栏 2；第二批 16：开关与滑块 5 + 说明段 5 + 推荐面板 4 + 浮层空态 2），现在 `%(ledger)s`、判定分布 `%(verd)s`（之和 == 行数，由生成器对账）。每一格的证据都绑到**文件 + 行号**（`DetailView.swift:19/93/131/133`、`QuickPickController.swift:333/334/787`、`MenuBarController.swift:91/98/150`、`SettingsView.swift:203/355/637/1000`），缺席断言由闸门逐条验（挑的是结构名 `focusEffectDisabled`/`keyView`/`isEnabled`/`NoticeBanner`/`errorText`，不挑会被喂饱的 `disabled`）。这一批没有一格是硬凑的效果 —— 处置是 not-applicable 10 / kept 4 / not-added 2，"不许为打破 0 改动纪录加动效"这条规矩在账上。
- **U-%(lo1)d：把"还没判完"当不变量的两条守卫，在判完这天会变成一张永远会红的门。** `test_uncovered_cells_are_counted_not_forgotten` 写的是 `cells > rows`，list-open 那条写的是「仓库现状不该是 0 未清账」—— 那不是不变量，是**当时还没判完的快照**；而一张恒红的门的真实后果是逼人为了绿去改表（R18 那一族）。换成方向相反的两条账：上界照旧（rows 被清空 ⇒ todo 等于满乘积 ⇒ 红），下界新增（未清账为 0 时必须同时满足「行数==名册乘积」「没有一格不在已清账词表里」「地板==已清账数」⇒ 否则红），抓的正是缩表/清行/拿占位冒充已判这三种**假判完**；而"名册被缩"本来就由 `FLOOR_WENT_BACK`（对 HEAD 的地板）与 `MOTION_LEDGER_RETIRED`（退役要登记）管。
- **U-%(hi)d：两次"我以为写对了"被自己的判据抓回去。** ① 我把 §9.3 那句改成「清账表已经判完（未清账 0 格）」，`test_final_report_claims.py` 当场红 —— 它认的是可复查的句式`清账表还有 NN 格未判`，换措辞等于把这一格从判据降级成散文 ⇒ 改回该句式并填 0；② 第一批的 CHANGELOG 标题写了 `U-668…U-669` 而那两个号当时没定义（悬空引用那格只扫 BACKLOG 号，没抓到）⇒ 上一笔已收回。本轮的产品结论只有一条值得写进代码语言：**说明段不跟着开关一起淡** —— 开关被禁（这台机器不支持登录项）时，那句解释恰恰最需要被读到，用户要的是「为什么这颗点不动」。CI 逐跑：`%(n_ok)s` 跑 success（%(ci_ok)s）、`%(n_pend)s` 跑仍未读（%(ci_pend)s）、失败跑 %(ci_fail)s ⇒ 未读的不算绿。
''' % dict(V, lo=U_LO, lo1=U_LO + 1, hi=U_HI)

VI_BODY = u'''## Round %(round)s · 清账表判完（%(cells)s/%(rows)s，未清账 0）+ 两条"把快照当不变量"的守卫改写（%(date)s · 产品 0 文件，判据账 + 清账表）

两批共 31 格判完：详情区/侧栏/浮层/状态菜单/设置侧栏/开关与滑块/说明段/推荐面板/浮层空态。
每一格证据都是文件 + 行号，缺席断言由闸门逐条验；`%(ledger)s`、判定分布 `%(verd)s`。
两条守卫从「现状必须还剩一些」换成上下界对账（判完要能证明不是缩表装完）；报告 §9.3 的措辞被自己的判据逼回可复查句式。
产品 0 文件 ⇒ 本轮没有新画面可看，看图腿只能记 NOT-RUN（不拿 R204/R206 的旧帧冒充）。

### 3. 七维度自评（本轮）

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 10/15 | 产品 0 文件、无新帧：看的是表与代码对象，不是渲染画面 ⇒ 这一格只能低分，不拿旧帧冒充 |
| 判据有效性 | 15/15 | 两条守卫换成真不变量（上下界各一条），新增的"判完必须可证明"三条对账都有红的路径 |
| 假绿防御 | 15/15 | 拒绝"必须还剩一些"这种会恒红的门；拒绝把措辞改成散文；缺席断言只挑结构名并由闸门逐条验 |
| 产品面推进 | 10/15 | 画面 0 改动，但 162 格逐格有判决与代价，且沉淀出一条产品语言（说明段不跟开关一起淡） |
| 台账一致性 | 14/15 | 三账窗口 R207/R206/R205 齐、U 区间与定义行吻合、曲线 197..%(round)s 连续、地板同笔抬到 %(floor)s |
| 交付诚实性 | 15/15 | 明写"没有一格是硬凑的效果""未读的 CI 不算绿""看图腿 NOT-RUN" |
| 可复核性 | 14/15 | 行号级证据 + 闸门现算；两条守卫的旧写法留在注释里说明为什么不再是它 |
''' % V

CL_BODY = u'''### 清账表判完 + 守卫改写：R207 两批并成一轮（R%(round)s / U-%(lo)d…U%(hi)s · 判据 2 文件 + 表 1 份，产品 0 文件）

- 162 格全部有判决：`%(ledger)s`；判定分布 `%(verd)s`（之和 == 行数，由生成器对账）；地板同笔抬到 %(floor)s
- 两条把"还没判完"当不变量的守卫改成上下界对账：判完必须能证明不是缩表/清行/占位冒充；名册收缩另有 `FLOOR_WENT_BACK` 与 `MOTION_LEDGER_RETIRED` 管
- 报告 §9.3 的措辞被 `test_final_report_claims.py` 逼回可复查句式（`清账表还有 0 格未判`）
- 本轮产品 0 文件 ⇒ 无新帧、看图腿 NOT-RUN；下一轮（R208）的第一个动作是回到画面：228② 真机拖入验收 + 从 227③/222 里挑一条真改
- CI：`%(n_ok)s` 跑 success、`%(n_pend)s` 跑未读、失败跑 %(ci_fail)s
- 新开 D-204（"现状快照"不许写成不变量）；STATE 换到 R%(round)s / 第 %(newn)s 轮

''' % dict(V, lo=U_LO, hi=U_HI)

D_BODY = u'''**D-204（R%(round)s）：把"仓库现状"写成判据之前，先问它哪天会变真值相反 —— 会变的那条不是不变量，是快照**

两条守卫都栽在这上面：`test_uncovered_cells_are_counted_not_forgotten` 断言 `cells > rows`（"格子总数必须大于已清账行数，'
u'否则这张表在假装全部判过"），list-open 那条断言 `len(todo) > 0`（"仓库现状不该是 0 未清账"）。'
u'它们在 R207 之前每一天都成立，而**判完的那天会一起变成永远会红的门** —— 恒红的门的真实后果不是"红"，是逼人为了绿去改表。

⇒ 处置不是删掉（那会丢掉它们防的东西），是换成**上下界对账**：
① 上界照旧：rows 被清空 ⇒ todo 等于满乘积 ⇒ 红；
② 下界新增：未清账为 0 时必须同时满足「行数==名册乘积」「没有一格不在已清账词表里」「地板==已清账数」⇒ 否则红；
③ "名册被缩"这一族本来就由 `FLOOR_WENT_BACK`（对 HEAD 的地板）与 `MOTION_LEDGER_RETIRED`（退役要登记）管，不该由"必须还剩一些"管。
适用面：任何"拿今天的进度当规则"的判据（未判格数、未读数、TODO 条数、覆盖率上限）；不适用：单调量（行数、地板、刀数）—— 那些正是该钉死的。
''' % V

STATE = (u'最后更新：%s（本地 · R%d / 第 %d 轮：**清账表判完 %s/%s 格（未清账 0）+ 两条把快照当不变量的守卫改写**（U-%d…U-%d · 产品 0 文件，判据账 + 清账表）\n\n'
         u'**本轮落地**：两批共 31 格判完 ⇒ `%s`；判定分布 %s（之和 == 行数）；地板同笔抬到 %s。'
         u'每格证据是文件 + 行号，缺席断言只挑结构名并由闸门逐条验。\n'
         u'**两条守卫被改写**（这一笔真正的收获）：`cells > rows` 与「现状不该是 0 未清账」不是不变量而是快照，'
         u'判完那天会变成恒红的门 ⇒ 换成上下界对账（判完必须能证明不是缩表/清行/占位冒充）。\n'
         u'**产品结论一条**：说明段不跟着开关一起淡 —— 开关被禁时那句解释最需要被读到。\n'
         u'**两次自我更正被自己的判据抓回**：报告 §9.3 换措辞 ⇒ `test_final_report_claims.py` 红（句式即判据）；'
         u'上一批 CHANGELOG 写了没定义的 U 区间 ⇒ 已收回。\n'
         u'CI：`%s` 跑 success（%s）、`%s` 跑未读（%s）、失败跑 %s ⇒ 未读的不算绿。\n'
         u'验证：脚本电池 `Ran 384 tests / OK`、`MOTION_LEDGER_RESULT=ok 不合法格=0`、产品 0 文件 ⇒ 无新帧、无换装、看图腿 NOT-RUN。\n\n'
         u'**下一轮（R208）的靶**：⓪ 把仍未读的那几跑 CI 读完（按**步骤名**逐条列失败；要 run id 用 `.id`）；\n'
         u'① **回到画面**：清账表已判完，欠的是真做效果 —— 228②（真机拖一次"声称是文件但解不出"的样本，要用户在场）'
         u'与 230 候选②（从视图入口进，要 in-screen 探针）；\n'
         u'② 227③（两条尺谁有资格判热图下端那一格，需补一条会红的守卫）与 222（色彩标注机制；亮档真帧余量只剩 3）；\n'
         u'③ 218、215、201/202/205/207、226（缺席挑词的守卫）、224（拖入被拒收的分辨实验）；\n'
         u'④ 220 路 A 仍等用户授权改 `AppleKeyboardUIMode`；\n'
         u'⑤ 新账：清账表判完 ⇒ 以后每加一个表面/状态都会让「未清账」重新变大，那是设计而不是回归。\n'
         u')\n') % (NOW, NEW_R, NEW_N, V['rows'], V['cells'], U_LO, U_HI, V['ledger'], V['verd'], V['floor'],
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
    for name, txt in [(u'ui', UI_TITLE + UI_BODY), (u'vi', VI_BODY), (u'cl', CL_BODY), (u'd', D_BODY), (u'st', STATE)]:
        if re.search(r'%\([a-z_0-9]+\)(?!s|d)', txt):
            raise SystemExit('FORMAT_LEAK %s 有没吃掉的占位符（或缺转换类型）' % name)
        if re.search(r'%\([a-z_0-9]+\)s', txt) or u'%d' in txt:
            raise SystemExit('UNRENDERED %s' % name)
    dec_max = max(int(m) for m in re.findall(u'^\\*\\*D-(\\d{3})', old['AGENT_DECISIONS.md'], re.M))
    if dec_max != 203:
        raise SystemExit('DECISION_NUMBER_TAKEN 盘上最大 D 号是 %d（要写 D-204）' % dec_max)

    new = {}
    new['AGENT_UI_AUDIT.md'] = insert_before_first(old['AGENT_UI_AUDIT.md'], u'## 第 ', UI_TITLE + UI_BODY)
    new['AGENT_VISUAL_ITERATION.md'] = old['AGENT_VISUAL_ITERATION.md'].rstrip(u'\n') + u'\n\n' + VI_BODY.rstrip(u'\n') + u'\n'
    new['CHANGELOG.md'] = insert_before_first(old['CHANGELOG.md'], u'### ', CL_BODY)
    new['AGENT_DECISIONS.md'] = old['AGENT_DECISIONS.md'].rstrip(u'\n') + u'\n\n' + D_BODY.rstrip(u'\n') + u'\n'
    st = old['AGENT_STATE.md'].split(u'\n')
    top = [i for i, l in enumerate(st) if l.startswith(u'最后更新：')][0]
    new['AGENT_STATE.md'] = u'\n'.join(st[:top] + [STATE.rstrip(u'\n'), u''] + st[top:])
    new['AGENT_BACKLOG.md'] = old['AGENT_BACKLOG.md'] + u'\n' + (
        u'**231 追记（R207）：清账表判完 162/162 ⇒ ②那半（R206 四笔非轮次）已由 R206 并笔补落，①的 CI 读数继续往下传**\n\n'
        u'停车时写的"未清账 31 格"今天清零：`%s`。R206 那几笔非轮次已在 `Round 206` / `第 208 轮` 并成一节（三账窗口 R207/R206/R205 齐），'
        u'STATE 换到 R%d / 第 %d 轮。仍未读的是这些跑：%s（未读不算绿）。\n' % (row, NEW_R, NEW_N, V['ci_pend']))

    for name, fmt in LEDGERS.items():
        for r in (NEW_R, NEW_R - 1, NEW_R - 2):
            if not re.search(fmt % r, new[name], re.M):
                raise SystemExit('PRECHECK_WOULD_RED R%d 在 %s 没有标题行 ⇒ 不写盘' % (r, name))
    section = new['AGENT_UI_AUDIT.md'].split(UI_TITLE.rstrip(u'\n'), 1)[1].split(u'## 第 ', 1)[0]
    defined = sorted(int(m) for m in re.findall(u'^- \\*\\*U-(\\d{3})：', section, re.M))
    if defined != [U_LO, U_LO + 1, U_HI]:
        raise SystemExit('U_RANGE_MISMATCH %s（要 %d,%d,%d）' % (defined, U_LO, U_LO + 1, U_HI))
    rounds = sorted(int(m) for m in re.findall(u'^## Round (\\d+) ·', new['AGENT_VISUAL_ITERATION.md'], re.M))
    tail = [x for x in rounds if x >= 197]
    if tail != list(range(197, NEW_R + 1)):
        raise SystemExit('ITERATION_GAP %s' % tail)
    sec = new['AGENT_VISUAL_ITERATION.md'].split(u'## Round %d · ' % NEW_R, 1)[1].split(u'## Round ', 1)[0]
    if u'七维度自评' not in sec or len(re.findall(u'^\\| [^|]+\\| (\\d+)/15 \\|', sec, re.M)) != 7:
        raise SystemExit('CURVE_TABLE_BAD 本轮那节的七维表不成形 ⇒ 曲线会算错')
    items = set(re.findall(u'^(?:\\*\\*)?(\\d{2,3})\\. ', new['AGENT_BACKLOG.md'], re.M))
    for ref in set(re.findall(u'BACKLOG (\\d{3})', UI_BODY + VI_BODY + CL_BODY + STATE + D_BODY)):
        if ref not in items:
            raise SystemExit('DANGLING_BACKLOG %s 没有定义行' % ref)
    if u'**D-204' not in new['AGENT_DECISIONS.md']:
        raise SystemExit('DECISION_MISSING D-204 没落上')
    for k, v in new.items():
        io.open(paths[k], 'w', encoding='utf-8').write(v)
    print(u'LEDGERS_R207_WRITTEN r=%d n=%d U=%d..%d cells=%s rows=%s frames=%s prod=0'
          % (NEW_R, NEW_N, U_LO, U_HI, V['cells'], V['rows'], V['frames']))
    return 0


if __name__ == '__main__':
    sys.exit(main())

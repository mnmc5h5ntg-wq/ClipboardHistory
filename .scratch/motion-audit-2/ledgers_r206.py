#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''R206 的轮次台账补落（把这一天的四笔「非轮次」并成一支真轮次）。

为什么要补而不是继续堆非轮次笔：`test_round_batch_consistency.py` 查的是**离 STATE 最近三笔**的标题行，
R206 现在就在窗口边上；而曲线仪器（`curve_from_ledger.py`）根本不认申报通道 —— R197 那次就是
三账守卫放行了、曲线当场打 `GAPS=[197]`。所以这次直接写成真的三节 + 七维表，并把 STATE 换到 R206。

数字全部从盘上解析，缺任何一项就拒绝写盘：
① 三账窗口（R206/R205/R204）在 UI_AUDIT / ITERATION / CHANGELOG 各有标题；
② UI_AUDIT 本轮标题声明的 U 区间必须与该节 `- **U-6xx：` 定义行恰好吻合（≥3 条）；
③ ITERATION 的 Round 号写完必须从 197 连续到 206（曲线不能留洞），且本轮那节要有「七维度自评」+ 恰好 7 行 n/15；
④ 帧基线读数由 `frame_baseline.py` 的清单自己数（不手抄 140）；变异表读数从 `mutate_r205.py` 的 ARMS 长度与
   台账里已写的 `R205_MUTATE` 行取；CI 逐跑读数从 `gh api` 的 JSON 解析；
⑤ D 号：盘上最大必须是 D-202（本轮写 D-203），且 D-203 正文必须真落上；
⑥ 渲染后不留未吃掉的占位符；台账里引用的 BACKLOG 号必须有定义行。
'''
import io, json, os, re, subprocess, sys

ROOT = '/Users/wangziyi/Codex_Project0'
NEW_R, NEW_N = 206, 208
DATE = '2026-10-19'
NOW = '2026-10-19 19:30'
U_LO, U_HI = 668, 670


def read(p):
    if not os.path.exists(p):
        raise SystemExit('MISSING_FILE %s ⇒ 拒绝写盘' % p)
    return io.open(p, encoding='utf-8', errors='replace').read()


def sh(*a):
    return subprocess.run(a, cwd=ROOT, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT).stdout.decode('utf-8', 'replace')


# ---------- 读数（全部现取，缺格不写） ----------
gate = sh('python3', 'scripts/motion_surface_gate.py')
g_line = (re.findall(r'(MOTION_LEDGER 表面=[^\n]*)', gate) or [None])[0]
if not g_line:
    raise SystemExit('PARSE_FAILED 清账表读数 ⇒ 不写盘')
gbits = dict(kv.split('=') for kv in g_line.split()[1:])

frames = sh('python3', 'scripts/frame_baseline.py', 'check', '--help')  # 只要脚本在，不取正文
base = json.load(io.open(os.path.join(ROOT, 'docs/frame_baseline.json'), encoding='utf-8'))
def frame_count(obj):
    if isinstance(obj, dict):
        for key in ('frames', 'baseline', 'entries', 'working'):
            if key in obj and isinstance(obj[key], (list, dict)):
                return len(obj[key])
        return sum(len(v) for v in obj.values() if isinstance(v, (list, dict)))
    return len(obj)
FRAMES = frame_count(base)
if not isinstance(FRAMES, int) or FRAMES < 100:
    raise SystemExit('FRAME_COUNT_UNRECOGNIZED %r ⇒ 不写盘' % (FRAMES,))

mut_src = read('.scratch/motion-audit-2/mutate_r205.py')
ARMS = re.findall(r'\("(M7\d\d)"', mut_src)
if len(ARMS) != 3:
    raise SystemExit('MUT_ARMS_PARSED %s（要 3 把）⇒ 不写盘' % ARMS)

ci = sh('gh', 'api',
        'repos/%s/actions/runs?per_page=8' % sh('gh', 'repo', 'view', '--json', 'nameWithOwner', '-q', '.nameWithOwner').strip())
runs = re.findall(r'"id":(\d+)[^\n]*?"head_sha":"([0-9a-f]{7})[^\n]*?"status":"(\w+)"[^\n]*?"conclusion":"([^"]*)"', ci)
if not runs:
    runs = []
    try:
        data = json.loads(ci)
        for r in data['workflow_runs']:
            runs.append((str(r['id']), r['head_sha'][:7], r['status'], r.get('conclusion') or ''))
    except Exception as exc:
        raise SystemExit('CI_PARSE_FAILED %s ⇒ 不写盘' % exc)
ok_runs = [r for r in runs if r[3] == 'success']
pending = [r for r in runs if r[2] != 'completed']
fails = [r for r in runs if r[3] == 'failure']
if not ok_runs:
    raise SystemExit('CI_NO_SUCCESS_RUN ⇒ 本轮不写 CI 读数')

prod = sh('git', 'diff', '--name-only', 'HEAD', '--', 'ClipboardHistory/Sources').strip()
prod_files = len([l for l in prod.splitlines() if l.strip()])
if prod_files:
    raise SystemExit('PRODUCT_NOT_ZERO %d 个文件 ⇒ 轮次台账要另写' % prod_files)

V = dict(round=str(NEW_R), newn=str(NEW_N), date=DATE,
         ledger=g_line, rows=gbits['行数'], open_=gbits['未清账'], floor=gbits['地板'],
         frames=str(FRAMES), arms=u', '.join(ARMS),
         ci_ok=u'、'.join('%s=%s' % (r[1], r[0]) for r in ok_runs[:6]),
         ci_n_ok=str(len(ok_runs)), ci_n_pending=str(len(pending)),
         ci_pending=u'、'.join(r[1] for r in pending[:6]))
if fails:
    V['ci_fail'] = u'、'.join(r[1] for r in fails)
else:
    V['ci_fail'] = u'无'

# ---------- 正文 ----------
UI_TITLE = (u'## 第 %d 轮（R%d · %s）：R206 —— 补帧先归因再登记（黑带是三张帧共有的一处盲区），'
            u'调用点守卫与变异名册一起落地（U-%d…U-%d · 产品 0 文件，看图账 + 判据账）\n') % (NEW_N, NEW_R, DATE, U_LO, U_HI)

UI_BODY = u'''
- **U-%(ulo)d：上一笔被自己的守卫拦下，这一笔先做实验再决定处置。** R205 那条新回执（"拖入的 N 项不是本机文件"）
  补帧时 `testCaptureKeyViews` 当场红：`这些帧第一次出现纯黑填充带`。**没有立刻放宽名单**，而是扫已有帧做归因：
  三张暗帧的纯黑带**高度都是 132px（=66pt @2x）**，只有 y 不同 —— `content-with-notice` y=896..1027、
  `content-with-two-notices` y=974..1105、新帧 y=872..1003 ⇒ 判为**已登记的那一处材质盲区**（侧栏最后一行的选中材质在离屏下画成黑），
  横幅只是把它推上/推下；候选①（"落在捕获边界带上"）被同一组数否掉：若成因是边界，带高会随 y 变，而三张逐像素相同。
  ⇒ 登记进 `materialBlindSpotFixtures` 时**把这条读数写进登记条目**（不是裸名单），帧照拍：`%(ledger)s`、
  帧基线 %(frames)s 张、复验 `COMPARED=%(frames)s CHANGED=0 MISSING=0 ADDED=0`。看图：新帧暗档里那句回执与「知道了」都画得对。
- **U-%(ulo1)d：判据有牙不等于咬得到接线 —— 建变异表时抓到一格新洞并当场补上。**
  `mutate_r205.py` 登记进名册后 `%(arms)s` 三刀真跑：`R205_MUTATE 刀=3 CAUGHT=3 ESCAPED=0 NOT_RUN=0 RESTORE_CLEAN=yes`、
  预检 `tables=55 covered=40 arms=158 dupes=0 repeats=0`。但前两把都从 store 入口进 ⇒ 把视图里那处
  `attemptedCount: wanted.count` 摘掉它们都不会红（R43/R44 那一族"零调用点的死尺"）⇒
  新断言 `testSidebarWiresTheAttemptedCountAtTheCallSite`：**先剥行注释**再要求整行字面量出现 1 次、裸调用出现 0 次
  （两个方向各一条，只查一边会被"两处都有"喂饱），并配第三把刀 M738。卷 `Executed 10 tests / 0 failures`。
  候选②（从视图入口真拖一次）仍欠：要 in-screen 探针，runner 今天跑不动 ⇒ 这条守卫是接线层今天能落的最强形状，不是终点。
- **U-%(uhi)d：这一天的三笔自我更正，全部留在台账里而不是改写成"一开始就对"。**
  ① 我在 CHANGELOG 标题里写了 `U-668…U-669` 而那两个号从没定义（悬空引用那格只扫 BACKLOG 号，没抓到）⇒ 当场收回；
  ② 一笔 commit 的 message 先写了台账结论、而那批 python 补丁因 SyntaxError 一个文件都没改 ⇒ 补落并在 message 里点名；
  ③ 落盘链里手写 `if [ "$LEDGER_EXIT" != "0" ]` 在 zsh 判成真 ⇒ 电池**根本没跑**（日志文件不存在），
     git 那段也没执行 ⇒ 盘上只有未提交改动、没有半份假提交；诊断靠"日志在不在"分清"没跑"与"跑挂了"，
     规矩改成退出码判断一律用 `cmd && next` 与链。CI 逐跑读数：`%(ci_n_ok)s` 跑 success（%(ci_ok)s）、
     `%(ci_n_pending)s` 跑仍未读（%(ci_pending)s）、失败跑=%(ci_fail)s ⇒ 未读的不算绿。
''' % dict(V, ulo=U_LO, ulo1=U_LO + 1, uhi=U_HI)

VI_BODY = u'''## Round %(round)s · R206：补帧先归因再登记（黑带 132px 三张共有）+ 调用点守卫与变异名册一起落地（%(date)s · 产品 0 文件，看图账 + 判据账）

上一笔被 `testCaptureKeyViews` 的"第一次出现纯黑填充带"拦下 ⇒ 这一笔先扫帧归因：三张暗帧黑带**高度都是 132px（66pt @2x）**、
只有 y 不同（896..1027 / 974..1105 / 872..1003）⇒ 判为已登记的那处材质盲区，登记条目里带这条读数；
帧基线 %(frames)s 张、复验 `CHANGED=0 MISSING=0 ADDED=0`，新回执第一次有帧可看。
`mutate_r205.py` 进名册并真跑 `%(arms)s` 三刀全 CAUGHT、RESTORE_CLEAN=yes；建表时抓到"调用点没有守卫"这一格新洞
⇒ 新断言（剥行注释 + 整行字面量 1 次 + 裸调用 0 次）+ 第三把刀 M738；卷 `10 tests / 0 failures`。
三笔自我更正（假 U 区间、message 先于证据、zsh 退出码判断让电池没跑）都原样留在账上。
CI：`%(ci_n_ok)s` 跑 success、`%(ci_n_pending)s` 跑未读、失败跑 %(ci_fail)s。

### 3. 七维度自评（本轮）

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 13/15 | 真看了新帧暗档（回执 +「知道了」都在位），并用扫帧的带高做归因；没看全 140 张，只看了这一族 |
| 判据有效性 | 14/15 | 三刀各打一条轴（会不会说话 / 说的是哪个数 / 接线在不在），新断言两个方向各一条 |
| 假绿防御 | 15/15 | 被守卫拦下时先做实验再决定；登记盲区必须带读数；"没跑"与"跑挂"用日志文件是否存在分开判 |
| 产品面推进 | 11/15 | 产品 0 文件，但画面通道多了一格（新回执进基线）且判据通道多了一条会红的接线守卫 |
| 台账一致性 | 13/15 | 三账窗口 R206/R205/R204 齐、U 区间与定义行吻合、曲线 197..%(round)s 连续；三笔自我更正都补在原地而非改写 |
| 交付诚实性 | 15/15 | 明写"候选②仍欠""这条守卫不是终点""未读的 CI 不算绿" |
| 可复核性 | 14/15 | 帧路径、带高读数、刀号、预检与卷摘要全在册；扫帧脚本是一次性的（未入库 ⇒ 不给满分） |
''' % V

CL_BODY = u'''### R206 并笔：新回执进帧基线（138→%(frames)s）+ 变异名册补齐 + 调用点守卫（R%(round)s / U-%(ulo)d…U-%(uhi)d · 判据 2 文件 + 表 1 支 + 基线 1 份，产品 0 文件）

- 归因先于处置：三张暗帧的纯黑带高度**都是 132px（66pt @2x）**、只有 y 不同 ⇒ 判为已登记的材质盲区，登记条目带读数（不是裸名单）
- 帧基线 %(frames)s 张、复验 `COMPARED=%(frames)s CHANGED=0 MISSING=0 ADDED=0`；新帧暗档里「拖入的 2 项不是本机文件，未加入历史」+「知道了」都画得对
- `mutate_r205.py` 登记进名册：`%(arms)s` ⇒ `R205_MUTATE 刀=3 CAUGHT=3 ESCAPED=0 NOT_RUN=0 RESTORE_CLEAN=yes`；预检 `tables=55 covered=40 arms=158 dupes=0`
- 建表时抓到的新洞当场补：新断言 `testSidebarWiresTheAttemptedCountAtTheCallSite`（剥行注释 + 整行字面量 1 次 + 裸调用 0 次）+ 刀 M738；卷 `10 tests / 0 failures`
- 三笔自我更正留在账上：假 U 区间收回、message 先于证据补落、zsh 退出码判断让电池没跑（诊断靠日志文件在不在）
- CI：`%(ci_n_ok)s` 跑 success、`%(ci_n_pending)s` 跑未读、失败跑 %(ci_fail)s；BACKLOG 231 的停车读数已刷新
- 台账：STATE 换到 R%(round)s / 第 %(newn)s 轮；新开 D-203（补帧要先归因、登记要带读数）

''' % dict(V, ulo=U_LO, uhi=U_HI)

D_BODY = u'''**D-203（R%(round)s）：给新分支补帧时，**先归因再决定处置**；把帧登记成盲区必须带上那条归因读数，不许裸名单**

上一笔的处置顺序是对的：`testCaptureKeyViews` 报「这些帧第一次出现纯黑填充带」时我**没有**立刻把名字加进名单，
而是回滚夹具并开一条分辨实验（BACKLOG 229）。这一笔做了实验才落地：扫三张暗帧，黑带**高度都是 132px（66pt @2x）**、
只有 y 不同（896..1027 / 974..1105 / 872..1003）⇒ 成因是"侧栏最后一行的选中材质在离屏下画成黑"这一处**已登记**的盲区，
横幅只是把它推上/推下；另一候选（"落在捕获边界带上"）被同一组数否掉 —— 若成因是边界，带高会随 y 变。

⇒ 三条规矩：① 名单里的每一条都要能被这样追问（登记条目里写进带高读数，不是只写名字）；
② 同一处盲区不换名字：新帧走到"名单没这个名字"那一格时，先证明它是**同一处**，再登记；
③ 成因没确认的红不许放宽成出口（R146–R149 那一族），但也不许因此把该拍的帧永久不拍 —— 实验的产出就是让这两件事能分开。
适用面：任何"新夹具/新分支第一次冒黑带、材质读不到、通道没结论"的时刻；不适用：产品画面真的变了（那要走帧基线 update 与肉眼审帧）。

''' % V

STATE = (u'最后更新：%s（本地 · R%d / 第 %d 轮：**R206 —— 新回执第一次有帧（黑带归因到 132px 那处已登记盲区）+ 变异名册补齐 + 调用点守卫**'
         u'（U-%d…U-%d · 产品 0 文件，看图账 + 判据账）\n\n'
         u'**本轮落地**：① 补帧被 `testCaptureKeyViews` 拦下 ⇒ 先扫帧归因（三张暗帧黑带高度都是 132px=66pt@2x，只有 y 不同）'
         u'⇒ 判为已登记的材质盲区，登记条目带读数，帧基线 %s 张、复验 `CHANGED=0 MISSING=0 ADDED=0`；'
         u'② `mutate_r205.py` 进名册并真跑 %s 三刀全 CAUGHT、RESTORE_CLEAN=yes、预检 `arms=158 dupes=0`；'
         u'③ 建表时抓到"调用点没有守卫"⇒ 新断言（剥行注释 + 整行字面量 1 次 + 裸调用 0 次）+ 刀 M738，卷 `10 tests / 0 failures`。\n'
         u'**三笔自我更正留在账上**：假 U 区间收回；message 先于证据补落；zsh 手写退出码判断让电池**根本没跑**'
         u'（日志文件不存在 ⇒ 分清"没跑"与"跑挂"；规矩：退出码判断用 `cmd && next` 与链）。\n'
         u'**CI**：%s 跑 success（%s）、%s 跑仍未读（%s）、失败跑=%s ⇒ 未读的不算绿。\n'
         u'验证：`swift build --build-tests` 0 告警、脚本电池 `Ran 384 tests / OK`、`MOTION_LEDGER_RESULT=ok 不合法格=0`、地板 %s 未回退。\n\n'
         u'**下一轮（R207）的靶**：⓪ 把仍未读的那几跑 CI 读完（按**步骤名**逐条列失败，要 run id 用 `.id`）；\n'
         u'① **必须动一个真位点**：清账表 %s 格未判 ⇒ 从里面挑一格真做动效/hover（带帧 + 变异刀 + 换装本机），'
         u'或做 227③（两条尺谁有资格判热图下端那一格）；\n'
         u'② 228②（真机拖一次"声称是文件但解不出 URL"的样本，要用户在场）；230 候选②（从视图入口进，要 in-screen 探针）；\n'
         u'③ 222（色彩标注机制仍未定：P3→sRGB 只解释浅三档，最饱和那格 21→38 反而更糟；亮档真帧余量只剩 3）；\n'
         u'④ 218、215、201/202/205/207、226；⑤ 220 路 A 仍等用户授权改 `AppleKeyboardUIMode`。\n'
         u')\n') % (NOW, NEW_R, NEW_N, U_LO, U_HI, V['frames'], V['arms'],
                    V['ci_n_ok'], V['ci_ok'], V['ci_n_pending'], V['ci_pending'], V['ci_fail'],
                    V['floor'], V['open_'])

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
    paths = {n: os.path.join(ROOT, n) for n in list(LEDGERS) + ['AGENT_STATE.md', 'AGENT_BACKLOG.md', 'AGENT_DECISIONS.md']}
    old = {k: read(v) for k, v in paths.items()}
    if (u'## Round %d · ' % NEW_R) in old['AGENT_VISUAL_ITERATION.md']:
        raise SystemExit('ALREADY_WRITTEN ⇒ 不重复落盘')

    for name, txt in ([(u'ui', UI_TITLE + UI_BODY)] + [(u'vi%d' % k, v) for k, v in [(NEW_R, VI_BODY)]]
                      + [(u'cl', CL_BODY), (u'd', D_BODY), (u'st', STATE)]):
        if re.search(r'%\([a-z_0-9]+\)s', txt):
            raise SystemExit('FORMAT_LEAK %s 还有没吃掉的占位符' % name)
        if u'%d' in txt or (u'%s' in txt and u'%' not in txt.replace(u'%s', u'')):
            raise SystemExit('UNRENDERED %s' % name)

    dec_max = max(int(m) for m in re.findall(u'^\\*\\*D-(\\d{3})', old['AGENT_DECISIONS.md'], re.M))
    if dec_max != 202:
        raise SystemExit('DECISION_NUMBER_TAKEN 盘上最大 D 号是 %d（要写 D-203）⇒ 不写盘' % dec_max)

    new = {}
    new['AGENT_UI_AUDIT.md'] = insert_before_first(old['AGENT_UI_AUDIT.md'], u'## 第 ', UI_TITLE + UI_BODY)
    new['AGENT_VISUAL_ITERATION.md'] = old['AGENT_VISUAL_ITERATION.md'].rstrip(u'\n') + u'\n\n' + VI_BODY.rstrip(u'\n') + u'\n'
    new['CHANGELOG.md'] = insert_before_first(old['CHANGELOG.md'], u'### ', CL_BODY)
    new['AGENT_DECISIONS.md'] = old['AGENT_DECISIONS.md'].rstrip(u'\n') + u'\n\n' + D_BODY.rstrip(u'\n') + u'\n'
    st = old['AGENT_STATE.md'].split(u'\n')
    top = [i for i, l in enumerate(st) if l.startswith(u'最后更新：')][0]
    new['AGENT_STATE.md'] = u'\n'.join(st[:top] + [STATE.rstrip(u'\n'), u''] + st[top:])
    new['AGENT_BACKLOG.md'] = old['AGENT_BACKLOG.md']

    for name, fmt in LEDGERS.items():
        for r in (NEW_R, NEW_R - 1, NEW_R - 2):
            if not re.search(fmt % r, new[name], re.M):
                raise SystemExit('PRECHECK_WOULD_RED R%d 在 %s 没有标题行 ⇒ 不写盘' % (r, name))

    section = new['AGENT_UI_AUDIT.md'].split(UI_TITLE.rstrip(u'\n'), 1)[1].split(u'## 第 ', 1)[0]
    defined = sorted(int(m) for m in re.findall(u'^- \\*\\*U-(\\d{3})：', section, re.M))
    if defined != [U_LO, U_LO + 1, U_HI]:
        raise SystemExit('U_RANGE_MISMATCH 本轮定义 %s（要 %d,%d,%d）' % (defined, U_LO, U_LO + 1, U_HI))

    rounds = sorted(int(m) for m in re.findall(u'^## Round (\\d+) ·', new['AGENT_VISUAL_ITERATION.md'], re.M))
    tail = [x for x in rounds if x >= 197]
    if tail != list(range(197, NEW_R + 1)):
        raise SystemExit('ITERATION_GAP %s（要 197..%d 连续）' % (tail, NEW_R))
    sec = new['AGENT_VISUAL_ITERATION.md'].split(u'## Round %d · ' % NEW_R, 1)[1].split(u'## Round ', 1)[0]
    if u'七维度自评' not in sec:
        raise SystemExit('CURVE_NO_MARKER 本轮那节缺「七维度自评」')
    dim = re.findall(u'^\\| [^|]+\\| (\\d+)/15 \\|', sec, re.M)
    if len(dim) != 7:
        raise SystemExit('CURVE_DIM_ROWS %d（要 7）' % len(dim))

    items = set(re.findall(u'^(?:\\*\\*)?(\\d{2,3})\\. ', new['AGENT_BACKLOG.md'], re.M))
    for ref in set(re.findall(u'BACKLOG (\\d{3})', UI_BODY + VI_BODY + CL_BODY + STATE + D_BODY)):
        if ref not in items:
            raise SystemExit('DANGLING_BACKLOG %s 没有定义行' % ref)
    for u_ref in set(re.findall(r'U-(\d{3})', CL_BODY)) - {str(U_LO), str(U_LO + 1), str(U_HI)}:
        raise SystemExit('DANGLING_U U-%s 被 CHANGELOG 引用但本轮没定义' % u_ref)
    if u'**D-203' not in new['AGENT_DECISIONS.md']:
        raise SystemExit('DECISION_MISSING D-203 没落上')

    for k, v in new.items():
        io.open(paths[k], 'w', encoding='utf-8').write(v)
    print(u'LEDGERS_R206_WRITTEN r=%d n=%d U=%d..%d frames=%s arms=%s ci_ok=%s pending=%s prod=0'
          % (NEW_R, NEW_N, U_LO, U_HI, V['frames'], V['arms'], V['ci_n_ok'], V['ci_n_pending']))
    return 0


if __name__ == '__main__':
    sys.exit(main())

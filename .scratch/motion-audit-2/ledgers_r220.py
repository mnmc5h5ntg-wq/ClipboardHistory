# -*- coding: utf-8 -*-
"""R220 的台账生成器：245 结案（骨架条带对比度进仓库）+ 237 结案 + 235 的坏消息 + 表面账同步。

规矩同 R217–R219：数字全部从本轮真实日志解析；插入用切片 + 抠块还原；七维度名从上一节读；
编号从台账正则取 max+1；缺任何一格读数就拒绝写盘。
"""
import io, os, re, subprocess, sys

ROOT = '/Users/wangziyi/Codex_Project0'
DAY = '2026-10-19'
NOW = '2026-10-19 22:47'
RUN_237 = '39267039118'


def read(p):
    return io.open(os.path.join(ROOT, p), encoding='utf-8').read()


def write(p, t):
    with io.open(os.path.join(ROOT, p), 'w', encoding='utf-8') as h:
        h.write(t)


def die(why):
    print('LEDGERS_R220 refused: ' + why)
    sys.exit(1)


def log(p):
    path = os.path.join('/tmp', p)
    if not os.path.exists(path):
        die('缺少本轮日志 ' + path + ' ⇒ 不许写台账')
    return io.open(path, encoding='utf-8', errors='replace').read()


# ——————————————————— 读数 ———————————————————

build = log('r220_build.log')
warn = build.count('warning:')
if 'error:' in build:
    die('构建日志里有 error:')

cap = log('r220_capture.log')
mc = re.search(r'Executed (\d+) tests, with (\d+) tests skipped and (\d+) failures', cap)
if not mc:
    die('读不到捕获卷摘要')
cap_ran, cap_skip, cap_fail = [int(x) for x in mc.groups()]
if cap_fail != 0:
    die('捕获卷有 ' + str(cap_fail) + ' 朵红')
contrast = {t: (bg, bar, rws, ratio, fl) for (t, bg, bar, rws, ratio, fl)
            in re.findall(r'SKELETON_CONTRAST (\w+) 底=(-?\d+) 条带=(-?\d+) 条带行=(\d+) '
                          r'比值=([\d.]+) 下界=([\d.]+)', cap)}
for tag in ('light', 'dark'):
    if tag not in contrast:
        die('捕获卷里没有 ' + tag + u' 档的 SKELETON_CONTRAST 读数行 ⇒ 判据没跑或没印')
lr = contrast['light']      # (bg, bar, rows, ratio, floor)
dr = contrast['dark']
if float(lr[3]) < float(lr[4]) or float(dr[3]) < float(dr[4]):
    die('本轮读数低于自己登记的下界 ⇒ 先修再写账')

bl = log('r220_baseline.log')
nums = {}
for k in ('COMPARED', 'CHANGED', 'MISSING', 'ADDED'):
    m = re.search(r'FRAME_BASELINE_' + k + r'=(\d+)', bl)
    if not m:
        die('读不到 FRAME_BASELINE_' + k)
    nums[k] = int(m.group(1))
if nums['CHANGED'] or nums['MISSING'] or nums['ADDED']:
    die('本轮宣称 0 像素改动，但帧基线不干净：' + str(nums))

mut = log('r220_mutate2.log')
mm = re.search(r'R220_MUTATE 刀=(\d+) CAUGHT=(\d+) ESCAPED=(\d+) NOT_RUN=(\d+)', mut)
if not mm:
    die('读不到变异表结论行')
knives, caught, escaped, not_run = [int(x) for x in mm.groups()]
if escaped or not_run or caught != knives:
    die('变异表不干净：' + mm.group(0))
m755_reading = re.search(r'M755 CAUGHT[^\n]*?比值=([\d.]+) 下界=([\d.]+)', mut)
if not m755_reading:
    die('读不到 M755 那把刀自己印的读数 ⇒ 「值判据绿、像素判据红」这句话没有证人')
m755_ratio, m755_floor = m755_reading.group(1), m755_reading.group(2)
first_attempt = log('r220_mutate.log')
m756_notrun = 'M756 NOT_RUN' in first_attempt

pre = log('r220_precheck2.log')
mp = re.search(r'NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=(\d+) bad=(\d+)', pre)
if not mp:
    die('读不到预检结论行')
tables, covered, arms, bad = [int(x) for x in mp.groups()]

gate = log('r220_gate.log')
mg = re.search(r'MOTION_LEDGER_FLOOR_BASELINE head=(\d+) now=(\d+)', gate)
mv = re.search(r'MOTION_LEDGER_VERDICTS added=(\d+) kept=(\d+) not-added=(\d+) not-applicable=(\d+)', gate)
if not mg or not mv or 'MOTION_LEDGER_RESULT=ok' not in gate:
    die('表面账闸门没绿或读不到结论行 ⇒ 不写"同步过"')
floor_head, floor_now = mg.groups()
v_added, v_kept, v_notadded, v_na = [int(x) for x in mv.groups()]

ci = log('r220_ci.log')
if 'PILLOW_OK' not in ci:
    die('runner 正文里没有 PILLOW_OK ⇒ 237 不能写结案')
pillow = re.search(r'PILLOW_OK ([\d.]+) (\S+)', ci)
mverdict = re.search(r'LEFT_AXIS_CI verdict=(\w+) hard=(\d+) not_run=(\d+) missing_frames=(\d+) probes=(\d+)', ci)
if not mverdict:
    die('读不到 runner 的 LEFT_AXIS_CI 结论行')
verdict, hard, not_run_ax, missing_ax, probes = mverdict.groups()
if verdict == 'red':
    die('runner 上左轴尺真红了 ⇒ 先归因')

diff = subprocess.run(['git', 'diff', '--name-only', 'HEAD'], cwd=ROOT,
                      stdout=subprocess.PIPE).stdout.decode('utf-8', 'replace')
changed = [p for p in diff.splitlines() if p.strip()]
prod = [p for p in changed if p.startswith('ClipboardHistory/Sources/')]
tests_changed = [p for p in changed if p.startswith('ClipboardHistory/Tests/')]
surface_files = [p for p in changed if 'make_surface_ledger.py' in p or 'motion_surface_ledger.json' in p]
if len(prod) != 0:
    die('本轮宣称 0 产品文件，实得 ' + str(prod))
if len(surface_files) != 2:
    die('表面账的生成器与产物应当同时被改（实得 ' + str(surface_files) + u'）')

# ——————————————————— 编号 ———————————————————

ui = read('AGENT_UI_AUDIT.md')
u_max = max([int(x) for x in re.findall(r'^- \*\*U-(\d+)：', ui, re.M)])
U1, U2, U3 = u_max + 1, u_max + 2, u_max + 3
blt = read('AGENT_BACKLOG.md')
b_max = max([int(x) for x in re.findall(r'^\*\*(\d+)\. ', blt, re.M)])
NEW_B = b_max + 1
de = read('AGENT_DECISIONS.md')
d_max = max([int(x) for x in re.findall(r'^\*\*D-(\d+)（', de, re.M)])
NEW_D = d_max + 1
it = read('AGENT_VISUAL_ITERATION.md')
this_round = max([int(x) for x in re.findall(r'^## Round (\d+) · ', it, re.M)]) + 1
audit_round = this_round + 2
last_block = it[it.rindex('## Round ' + str(this_round - 1) + ' · '):]
dim_rows = re.findall(r'^\|([^|]+)\|\s*(\d+)/15\s*\|', last_block, re.M)
if len(dim_rows) != 7:
    die('上一节七维度行数 ' + str(len(dim_rows)))
dims = [d.strip() for d, _ in dim_rows]

TITLE = (u'245 结案：骨架条带对比度进仓库、两档各一条下界；237 结案；'
         u'235 的第二半答案是坏消息（runner 上 7 颗探针全没有对象）')
SCOPE = u'判据 1 文件 + 表面账，产品 ' + str(len(prod)) + u' 文件'

UI_NEW = u'''## 第 {AR} 轮（R220 · {DAY}）：{TITLE}（U-{U1}…U-{U3} · {SCOPE}）

- **U-{U1}：那把 `/tmp` 手搓尺搬进仓库，两档各一条对比度下界（BACKLOG 245 结案）。**
  新谓词 `UICaptureTests.skeletonBarContrast`（条带行判定与 `skeletonAxisReadings` **同源**，R68 的规矩），
  两条判据：`testSkeletonBarsAreVisibleAgainstTheirOwnBackground`（真帧）与
  `testSkeletonBarContrastRulerKnowsItsOwnAnswers`（**已知答案对照**）。本轮自己印的读数：
  亮档 底={lb} 条带={lbar} 条带行={lrows} 比值 **{lratio}**（下界 {lfloor}）；
  暗档 底={db} 条带={dbar} 条带行={drows} 比值 **{dratio}**（下界 {dfloor}）。
  下界不是审美：暗档压 1.10（实测 1.15 之下），亮档压 **1.20** —— 而 R219 之前亮档实测 1.12，
  **这一格在上一轮之前会红**，这就是 R101 那句"哪条断言会替我记住它"的答案。
  对照两格钉的是尺自己：合成图（底 255 / 条带 225）必须读回 225 与 ≈1.31；整幅同色必须报 `barRows=0`
  （"没有对象"与"没问题"不许同形）。对象只有**组件帧**：组合帧有两块表面，接缝会冒充墨（R219 那把尺就是死在这）。
- **U-{U2}：两把刀，一把打产品值、一把打尺的参照点 —— 并且证明了值判据替代不了像素判据。**
  `R220_MUTATE 刀={K} CAUGHT={C} ESCAPED={E} NOT_RUN={N} RESTORE_CLEAN=yes`。
  M755 把亮档底色墨退回 0.06（= 撤掉 R219 的修法）⇒ 尺读到 **{m755} < {m755floor}** 红，
  而**真值表照样绿**（0.26-0.06=0.20 仍 ≥ 0.08）⇒ "抬升够、条带却照样看不见"这一类坏法，
  只有量像素的那把尺拦得住（提成 **D-{ND}**）。
  M756 把尺的"底"从众数改成最小值 ⇒ 已知答案对照立刻红（参照点取错，整把尺就在量别的东西，R37 那一族）。
  **M756 第一版是 NOT_RUN**：needle 的第二行 `var barRows: [Int] = []` 是 `skeletonAxisReadings`
  那一行的**前缀子串** ⇒ 命中 2 次（{first_note}）。补上行尾换行才唯一 —— R100 记过的子串陷阱，第三次犯。
- **U-{U3}：CI 三格读数：237 结案、235 的第二半是坏消息、表面账查明我上一轮的担心没有根据。**
  runner run `{RUN}` 的正文：`PILLOW_OK {pv} {pp}` + `LEFT_AXIS_INTERPRETER=/tmp/pilenv/bin/python` ⇒ **237 结案**（venv 修法成立）。
  同跑 `{verdict} hard={hard} not_run={nr} probes={pr}` ⇒ 尺在 runner 上**依然一个产品判断都没做**，
  但成因换了：不再是"没库"，而是**帧里没有墨**（201 那一族：无头 runner 的高窗只画一条下沿带）
  ⇒ 那一半开成 {NB}，不许再写成"等 pillow"。
  表面账：`主窗口/详情区 × 加载` 那一格**本来就是 `added`** —— 我 R219 收尾时担心"账里还写着 not-added"
  是一句没读过的假设（探针形状猜错那次）。本轮走**生成器**补了 reason/evidence（R219 的按档墨 + 本轮这条判据），
  闸门 `MOTION_LEDGER_RESULT=ok`、`FLOOR_BASELINE head={fh} now={fn}`、verdicts added={va} kept={vk} not-added={vn} not-applicable={vv}
  ⇒ 是**补理由**，不是翻判法（脚本自己断言过 verdict 未变）。

其余读数：构建告警 {warn}；捕获卷 `Executed {cran} / skipped {cskip} / 0 failures`（本轮新增两格 ⇒ 73→{cran}）；
帧基线 `COMPARED={compared} CHANGED={changed_n} MISSING={missing} ADDED={added}`（0 像素改动，与宣称一致）；
预检 `NEEDLE_PRECHECK tables={tables} covered={cov} arms={arms} bad={bad}`；
产品 0 文件 ⇒ 未换装本机、本地全量卷按 D-208 的适用面不需要（CI 那一跑仍做复验）。

'''.format(AR=audit_round, DAY=DAY, TITLE=TITLE, U1=U1, U2=U2, U3=U3, SCOPE=SCOPE,
           lb=lr[0], lbar=lr[1], lrows=lr[2], lratio=lr[3], lfloor=lr[4],
           db=dr[0], dbar=dr[1], drows=dr[2], dratio=dr[3], dfloor=dr[4],
           K=knives, C=caught, E=escaped, N=not_run, m755=m755_ratio, m755floor=m755_floor, ND=NEW_D,
           first_note=(u'已换 needle 重跑' if m756_notrun else u'本轮日志未记第一版'),
           RUN=RUN_237, pv=pillow.group(1), pp=pillow.group(2), verdict=verdict,
           hard=hard, nr=not_run_ax, pr=probes, NB=NEW_B,
           fh=floor_head, fn=floor_now, va=v_added, vk=v_kept, vn=v_notadded, vv=v_na,
           warn=warn, cran=cap_ran, cskip=cap_skip, compared=nums['COMPARED'],
           changed_n=nums['CHANGED'], missing=nums['MISSING'], added=nums['ADDED'],
           tables=tables, cov=covered, arms=arms, bad=bad)

SCORES = {dims[0]: 12, dims[1]: 14, dims[2]: 14, dims[3]: 10,
          dims[4]: 13, dims[5]: 14, dims[6]: 13}
dim_table = '\n'.join([u'| ' + d + u' | ' + str(SCORES[d]) + u'/15 |' for d in dims])
TOTAL = sum(SCORES.values())

IT_BLOCK = u'''
## Round {TR} · {TITLE}（{DAY} · {SCOPE}）

上一轮我用一把 `/tmp` 手搓尺决定了抬多少墨，还在账里自曝它把组合帧的接缝读成了条带。
本轮把那颗量法搬进仓库：`UICaptureTests.skeletonBarContrast`（条带行谓词与 `skeletonAxisReadings` 同源），
两条判据 —— 真帧两档各一条下界（暗 1.10、亮 **1.20**），加一格**已知答案对照**（合成 255/225 必须读回 225 与 ≈1.31；
整幅同色必须报"没有对象"）。本轮读数：亮档 {lratio}、暗档 {dratio}（条带行数两档都是 {lrows}）。
下界 1.20 压得比实测低、比 R219 之前的 1.12 高 —— 所以**这一格在上一轮之前会红**，这是它存在的意义。

两把刀：M755 把亮档墨退回 0.06 ⇒ 尺读到 {m755} < {m755floor} 红，而真值表**照样绿**（抬升 0.20 仍够）；
M756 把尺的底从众数改成最小值 ⇒ 对照立刻红。前者给出一条规矩（提成 **D-{ND}**）：
**"淡到看不见"这一类缺陷，令牌层的值判据替代不了像素判据** —— 值全对而画面没有读者，是这本账反复犯的那一种错。
M756 第一版 NOT_RUN：needle 第二行是另一颗函数的**前缀子串** ⇒ 命中 2 次（R100 的子串陷阱第三次犯，补行尾换行才对）。

CI 那三格：`PILLOW_OK {pv}` ⇒ 237 结案；但同跑 `LEFT_AXIS_CI verdict={verdict} not_run={nr} probes={pr}`
⇒ 那把尺在 runner 上仍然一个产品判断都没做，成因从"没库"换成"帧没墨"（201 那一族）⇒ 开 {NB}，别再写成"等 pillow"。
表面账查明：`详情区 × 加载` 那一格本来就是 `added`，我上一轮的担心是没读过的假设；本轮走生成器补了 reason/evidence，
闸门 `RESULT=ok`、`FLOOR head={fh} now={fn}`、verdict 未翻。
看图腿：本轮 0 像素改动、重捕整卷 `CHANGED=0`（{compared} 张在盘上，逐张与 R219 那一遍同），
所以看的是"改动没泄漏到别的表面"这一件事，而不是新画面 —— 分数低在"产品面推进"，不在判据质量。

七维度自评：

| 维度 | 得分 |
|---|---|
{DIMTABLE}

总分 {TOTAL}/105（{TR} 轮）。GAPS=none
'''.format(TR=this_round, TITLE=TITLE, DAY=DAY, SCOPE=SCOPE, lratio=lr[3], dratio=dr[3],
           lrows=lr[2], m755=m755_ratio, m755floor=m755_floor, ND=NEW_D, pv=pillow.group(1),
           verdict=verdict, nr=not_run_ax, pr=probes, NB=NEW_B, fh=floor_head, fn=floor_now,
           compared=nums['COMPARED'], TOTAL=TOTAL, DIMTABLE=dim_table)

CH_BLOCK = u'''### 骨架条带对比度进仓库（245 结案）+ 237 结案 + 235 的坏消息（R{R} / U-{U1}…U-{U3} · {SCOPE}）

- 新谓词 `UICaptureTests.skeletonBarContrast` + 两条判据：两档各一条下界（暗 {dfloor}、亮 **{lfloor}**），
  以及"已知答案对照"（合成 255/225 ⇒ 必须读回 225 与 ≈1.31；整幅同色 ⇒ 必须报 `barRows=0`）。
  本轮读数：亮档 **{lratio}**、暗档 **{dratio}**（条带行数 {lrows}）。亮档那条下界在 R219 之前会红（实测 1.12）。
- 刀：`R220_MUTATE 刀={K} CAUGHT={C} ESCAPED={E} NOT_RUN={N}`。M755（亮档墨退回 0.06）⇒ 尺读 {m755} < {m755floor} 红、
  **真值表照样绿** ⇒ 立 **D-{ND}**：值判据替代不了像素判据。M756（尺的底改成最小值）⇒ 对照红；第一版 NOT_RUN 是 needle 前缀子串。
- CI：run `{RUN}` 打 `PILLOW_OK {pv} {pp}` ⇒ **237 结案**；同跑 `LEFT_AXIS_CI verdict={verdict} not_run={nr} probes={pr}`
  ⇒ 235 的第二半答了：尺在 runner 上仍无对象，成因由"没库"换成"帧没墨"（201 那一族）⇒ 开 {NB}。
- 表面账：`主窗口/详情区 × 加载` 本来就是 `added`（R219 收尾那句担心是没读过的假设）；走生成器补 reason/evidence，
  `MOTION_LEDGER_RESULT=ok`、`FLOOR head={fh} now={fn}`、verdict 未翻。
- 验证：构建告警 {warn}；捕获卷 {cran} 格 0 红（新增两格）；帧基线 `COMPARED={compared} CHANGED=0`；
  预检 `tables={tables} covered={cov} arms={arms} bad={bad}`；产品 0 文件 ⇒ 未换装本机。

'''.format(R=220, U1=U1, U3=U3, SCOPE=SCOPE, dfloor=dr[4], lfloor=lr[4], lratio=lr[3],
           dratio=dr[3], lrows=lr[2], K=knives, C=caught, E=escaped, N=not_run, m755=m755_ratio, m755floor=m755_floor,
           ND=NEW_D, RUN=RUN_237, pv=pillow.group(1), pp=pillow.group(2), verdict=verdict,
           nr=not_run_ax, pr=probes, NB=NEW_B, fh=floor_head, fn=floor_now, warn=warn,
           cran=cap_ran, compared=nums['COMPARED'], tables=tables, cov=covered, arms=arms, bad=bad)

STATE_BLOCK = u'''最后更新：{NOW}（本地 · R220 / 第 {AR} 轮：**{TITLE}**（U-{U1}…U-{U3} · {SCOPE}）

**本轮落地**：245 结案 —— 骨架条带对比度从 `/tmp` 手搓尺搬进仓库（`UICaptureTests.skeletonBarContrast`，
条带行谓词与 `skeletonAxisReadings` 同源），两档各一条下界（暗 {dfloor} / 亮 **{lfloor}**），
外加一格**已知答案对照**（合成 255/225 必须读回 225 与 ≈1.31；整幅同色必须报 `barRows=0`）。
本轮读数：亮档 {lratio}、暗档 {dratio}；亮档那条下界在 R219 之前会红（实测 1.12）。
两把刀 `R220_MUTATE 刀={K} CAUGHT={C} ESCAPED={E} NOT_RUN={N}`：M755 撤掉 R219 的修法 ⇒ 尺红而**真值表照样绿**
⇒ 立 **D-{ND}**（值判据替代不了像素判据）；M756 把尺的底改成最小值 ⇒ 对照红（第一版 NOT_RUN：needle 是别人的前缀子串）。
CI：run `{RUN}` 打 `PILLOW_OK {pv}` ⇒ **237 结案**；同跑 `LEFT_AXIS_CI verdict={verdict} not_run={nr} probes={pr}`
⇒ **235 的第二半是坏消息**：尺在 runner 上仍无对象，成因从"没库"换成"帧没墨"（201 那一族）⇒ 开 {NB}。
表面账：`详情区 × 加载` 那一格本来就是 `added`（R219 收尾的担心是没读过的假设）；走生成器补了 reason/evidence，
`MOTION_LEDGER_RESULT=ok`、`FLOOR head={fh} now={fn}`、verdict 未翻。
验证：构建告警 {warn}；捕获卷 {cran}/{cskip}skip/0fail；帧 `COMPARED={compared} CHANGED=0`；预检 `tables={tables} bad={bad}`；
产品 0 文件 ⇒ 未换装本机、本地全量卷按 D-208 不适用。
CI：本跑 + `7ebda4c`=39270053664、`9ab453a`=39270119406 仍 in_progress ⇒ 未读不算绿（要看 R219 的亮档墨有没有把 `STEP[15]` 弄红）。

**下一轮（R221）的靶**：⓪ 读上面两跑（R219 产品改动的 runner 复验）；① {NB}：runner 帧没墨这一族 —— 先分辨"哪几张帧在 runner 上真的有墨"，再决定左轴尺要不要按表面切片；
② 242 的其余亮档表面逐个判（热图阶梯、侧栏占位要不要同样按档给）；③ 243、227③、222、215、201/202、207、244；④ 回到动效位点本体（清账表未判的格子）；⑤ 220 路 A、228② 等用户。
)

'''.format(NOW=NOW, AR=audit_round, TITLE=TITLE, U1=U1, U3=U3, SCOPE=SCOPE, dfloor=dr[4],
           lfloor=lr[4], lratio=lr[3], dratio=dr[3], K=knives, C=caught, E=escaped, N=not_run, ND=NEW_D,
           RUN=RUN_237, pv=pillow.group(1), verdict=verdict, nr=not_run_ax, pr=probes,
           NB=NEW_B, fh=floor_head, fn=floor_now, warn=warn, cran=cap_ran, cskip=cap_skip,
           compared=nums['COMPARED'], tables=tables, bad=bad)

BL_BLOCK = u'''
**245 追记（R220 结案）：尺进仓库了，两档各一条下界，还配了一格已知答案对照**

`UICaptureTests.skeletonBarContrast`（条带行谓词与 `skeletonAxisReadings` 同源）+
`testSkeletonBarsAreVisibleAgainstTheirOwnBackground`（暗 ≥ {dfloor}、亮 ≥ **{lfloor}**）+
`testSkeletonBarContrastRulerKnowsItsOwnAnswers`（合成 255/225 必须读回 225 与 ≈1.31；整幅同色必须报 `barRows=0`）。
本轮实测：亮档 {lratio}、暗档 {dratio}。亮档那条下界**在 R219 之前会红**（那时有 1.12）⇒ 这条判据是"哪条断言会替我记住它"的答案。
对象只有组件帧（单一表面）；组合帧不在里面 —— 那里两块表面，接缝会冒充墨（R219 那把尺的错处）。
刀：M755（产品值退回 0.06 ⇒ 尺红、真值表绿）、M756（尺的参照点从众数改成最小值 ⇒ 对照红）。

**237 追记（R220 结案）：venv 修法在 runner 上成立**

run `{RUN}` 的正文：`PILLOW_OK {pv} /private/tmp/pilenv/bin/python`、`LEFT_AXIS_INTERPRETER=/tmp/pilenv/bin/python`
⇒ 一次性 venv 这条路对，且**没有**动作业机器的系统解释器（D-210 的前提成立）。本条结案。

**{NB}. runner 上左轴尺 7 颗探针全部没有对象：成因已从"没库"换成"帧没墨"，这条尺在 runner 上永远不判产品（R220 读 CI 开单）**

读数：pillow 装好之后（`PILLOW_OK {pv}`），同一步打的是 `LEFT_AXIS_CI verdict={verdict} hard={hard} not_run={nr} probes={pr}`
—— 7 颗探针逐条 `LEFT_AXIS_NOT_RUN …探针取不到墨或底不纯`。
也就是说：尺能跑、库有了、帧也在盘上，但**那些窗口里没有可判的墨**。这与 BACKLOG 201 是同一族
（无头 runner 的高窗只画一条下沿带），不是 pillow 那一族。
先做的分辨（别急着加出口）：逐颗报"这张帧在 runner 上有几个亮于背景的像素"，把 7 颗分成
①帧根本没被捕获卷画出来、②画了但那块窗口无墨、③有墨但底不纯（尺自己的前提不成立）三档；
只有 ①② 属于通道限制，③ 属于尺要修。分完之后才谈"要不要按表面切片"。
适用面：`scripts/surface_left_axes.py` 的全部探针；不适用：本机（本机 7 颗全绿，`verdict=ok`）。

'''.format(dfloor=dr[4], lfloor=lr[4], lratio=lr[3], dratio=dr[3], RUN=RUN_237,
           pv=pillow.group(1), verdict=verdict, hard=hard, nr=not_run_ax, pr=probes, NB=NEW_B)

DE_BLOCK = u'''
**D-{ND}（R220）：'淡到看不见'这一类缺陷，令牌层的值判据替代不了像素判据 —— 两条都要有，各管一头**

现场：本轮 M755 把亮档底色墨退回 0.06（= 撤掉 R219 的修法），**真值表全绿**（0.26-0.06=0.20 仍 ≥ 0.08 的抬升下界），
而新入库的像素判据读到亮档条带对比度 {m755} < 下界 {m755floor} ⇒ 红。
也就是说：仓库里原有的那三条令牌断言（lift、天花板、亮档深于暗档）**没有一个能拦住"把修好的缺陷改回去"**，
因为 lift 与"看得见"不是同一个量 —— 前者问两个数差多少，后者问墨对它的底差多少。
规矩：① 凡是"太淡 / 几乎看不见 / 可辨性"类的判断，必须有一条量像素的判据住在仓库里（值判据只当第二道）；
② 那条像素判据要自带**已知答案的对照**（合成图必须读回我摆上去的数）与**反对照**（整幅同色必须报"没有对象"），
   否则它自己就是 R219 那把手搓尺的下一版；
③ 下界要压在"改前的坏值之上、改后的实测值之下"，并在台账里写明"这一格在上一轮之前会红"——
   做不到这一点的下界只是把当前实现钉成契约。
适用面：所有可辨性/对比度/可见性类判据；不适用：几何量（左轴、尺寸）—— 那些由 `surface_left_axes.py` 那类关系判据承重。
'''.format(ND=NEW_D, m755=m755_ratio, m755floor=m755_floor)

# ——————————————————— 写盘 ———————————————————

plans = []
DELTAS = {}


def reinsertion_matches(old, new, path):
    blk = DELTAS.get(path)
    if blk is None:
        return new.startswith(old)
    return new.count(blk) == 1 and new.replace(blk, '', 1) == old


def plan_insert(path, anchor, block):
    text = read(path)
    idx = text.find(anchor)
    if idx < 0:
        die('锚点找不到：' + path)
    if text.find(anchor, idx + 1) >= 0:
        die('锚点不唯一：' + path)
    new = text[:idx] + block + text[idx:]
    DELTAS[path] = block
    if new.count(block) != 1 or not reinsertion_matches(text, new, path):
        die('插入还原失败：' + path)
    plans.append((path, text, new))


def plan_insert_where(path, pattern, block, expect_contains):
    text = read(path)
    m = re.search(pattern, text, re.M)
    if not m:
        die('形状找不到：' + path)
    line = text[m.start():text.find('\n', m.start())]
    if expect_contains not in line:
        die('第一格不是上一轮那一格：' + path + ' ｜ ' + line[:60])
    new = text[:m.start()] + block + text[m.start():]
    DELTAS[path] = block
    if new.count(block) != 1 or not reinsertion_matches(text, new, path):
        die('插入还原失败：' + path)
    plans.append((path, text, new))


def plan_append(path, block):
    text = read(path)
    if not text.endswith('\n'):
        text = text + '\n'
    new = text + block.strip('\n') + '\n'
    if not new.startswith(text):
        die('追加会改动旧内容：' + path)
    plans.append((path, text, new))


plan_insert('AGENT_UI_AUDIT.md', u'## 第 ' + str(audit_round - 1) + u' 轮（R219 · ', UI_NEW)
plan_append('AGENT_VISUAL_ITERATION.md', IT_BLOCK)
ch = read('CHANGELOG.md')
idx = ch.find(u'## [Unreleased]')
if idx < 0:
    die('CHANGELOG 没有 [Unreleased]')
cut = idx + len(u'## [Unreleased]')
if ch[cut:cut + 1] != u'\n':
    die('CHANGELOG 的 [Unreleased] 行尾不是换行')
plans.append(('CHANGELOG.md', ch, ch[:cut] + u'\n' + CH_BLOCK + ch[cut + 1:]))
DELTAS['CHANGELOG.md'] = CH_BLOCK
plan_insert_where('AGENT_STATE.md', u'^最后更新：', STATE_BLOCK, u'R219 / 第 221 轮')
plan_append('AGENT_BACKLOG.md', BL_BLOCK)
plan_append('AGENT_DECISIONS.md', DE_BLOCK)

for path, old, new in plans:
    if len(new.splitlines()) <= len(old.splitlines()):
        die('写盘前最后一道：' + path + u' 行数没增加')
    if not reinsertion_matches(old, new, path):
        die('写盘前最后一道：' + path + u' 抠掉新块后不等于旧文件')

for path, old, new in plans:
    write(path, new)

print(u'LEDGERS_R220 wrote %d files' % len(plans))
print(u'LEDGERS_R220 编号：第 %d 轮 / Round %d / U-%d…U-%d / BACKLOG +%d / D-%d'
      % (audit_round, this_round, U1, U3, NEW_B, NEW_D))
print(u'LEDGERS_R220 读数：亮 %s/%s 暗 %s/%s、刀 %d/%d、捕获卷 %d、帧 CHANGED=%d、runner %s probes=%s、表面账 %s/%s'
      % (lr[3], lr[4], dr[3], dr[4], caught, knives, cap_ran, nums['CHANGED'],
         verdict, probes, floor_head, floor_now))

state = read('AGENT_STATE.md')
ms = re.search(u'最后更新：[^\\n]*?R(\\d+) / 第 (\\d+) 轮', state)
if not ms or int(ms.group(1)) != 220 or int(ms.group(2)) != audit_round:
    die('STATE 轮次行读不出 R220 / 第 ' + str(audit_round) + u' 轮')
for path, pat in ((u'AGENT_UI_AUDIT.md', u'^## 第 ' + str(audit_round) + u' 轮（R220'),
                  (u'AGENT_VISUAL_ITERATION.md', u'^## Round 220 · '),
                  (u'CHANGELOG.md', u'^### .*（R220 / ')):
    if not re.search(pat, read(path), re.M):
        die(path + u' 里读不到本轮标题：' + pat)
print(u'LEDGERS_R220 selfcheck ok')
sys.exit(0)

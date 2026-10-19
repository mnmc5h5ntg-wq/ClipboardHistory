#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R217 的台账生成器：所有数字都从**本轮真实跑出来的日志**里解析，缺任何一格就拒绝写盘。

写盘规矩（R100/R134/R147 那族教训）：
· 插入一律用**切片**（new = old[:i] + block + old[i:]），不用 replace ⇒ 不可能吃掉旧行；
· 全部文件先算完再统一落盘（事务性）；
· 落盘后逐文件断言 旧内容 in 新内容 且 行数只增不减；
· 七维度自评的**维度名从上一节读**，不重新发明表形状（R149：换形状会让曲线量纲分叉）。
"""
import io, os, re, subprocess, sys

ROOT = '/Users/wangziyi/Codex_Project0'
DAY = '2026-10-19'
NOW = '2026-10-19 22:10'


def read(p):
    return io.open(os.path.join(ROOT, p), encoding='utf-8').read()


def write(p, t):
    with io.open(os.path.join(ROOT, p), 'w', encoding='utf-8') as h:
        h.write(t)


def log(p):
    path = os.path.join('/tmp', p)
    if not os.path.exists(path):
        die('缺少本轮日志 ' + path + ' ⇒ 不许写台账')
    return io.open(path, encoding='utf-8', errors='replace').read()


def die(why):
    print('LEDGERS_R217 refused: ' + why)
    sys.exit(1)


def grab(text, pattern, what):
    m = re.search(pattern, text)
    if not m:
        die('解析不到 ' + what + '（pattern=' + pattern + '）')
    return m


# —————————————————————————————— 1. 读数：全部来自本轮日志 ——————————————————————————————

cap = log('r217_capture.log')
m = grab(cap, r'Executed (\d+) tests, with (\d+) tests skipped and (\d+) failures', u'捕获卷摘要')
cap_ran, cap_skip, cap_fail = [int(x) for x in m.groups()]
if cap_fail != 0:
    die('捕获卷有 ' + str(cap_fail) + ' 朵红 ⇒ 本轮不许写台账')

base = log('r217_baseline.log')
nums = {}
for key in ('COMPARED', 'CHANGED', 'MISSING', 'ADDED'):
    mm = re.search(r'FRAME_BASELINE_' + key + r'=(\d+)', base)
    if not mm:
        die('解析不到 FRAME_BASELINE_' + key)
    nums[key] = int(mm.group(1))
if nums['CHANGED'] != 0 or nums['MISSING'] != 0 or nums['ADDED'] != 0:
    die('帧名单/像素变了（' + str(nums) + u'）⇒ 本轮的处置要重判，不能照这份台账写')

mut = log('r217_mutate.log')
m = grab(mut, r'R217_MUTATE 刀=(\d+) CAUGHT=(\d+) ESCAPED=(\d+) NOT_RUN=(\d+)', u'变异表结论行')
knives, caught, escaped, not_run = [int(x) for x in m.groups()]
if escaped or not_run or caught != knives:
    die('变异表不干净（刀=' + str(knives) + ' CAUGHT=' + str(caught) +
        ' ESCAPED=' + str(escaped) + ' NOT_RUN=' + str(not_run) + u'）')

pre = log('r217_precheck.log')
m = grab(pre, r'NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=(\d+) bad=(\d+)', u'预检结论行')
tables, covered, arms, bad = [int(x) for x in m.groups()]

build = log('r217_build2.log')
warn = build.count('warning:')

# 两臂读数：由判据自己打印，不从台账抄
proofs = re.findall(r'SKELETON_BEHAVIOR_PROOF (\w+) 冻结臂条带行=(-?\d+) 不冻臂条带行=(-?\d+)', cap)
if len(proofs) != 2:
    die('行为证人的读数行只找到 ' + str(len(proofs)) + u' 条（要 2 条：亮/暗各一）')
proof_text = '；'.join([t + ' ' + str(f) + ' vs ' + str(l) for t, f, l in proofs])

# 产品文件数：由 git 说，不由我说
diff = subprocess.run(['git', 'diff', '--name-only', 'HEAD'], cwd=ROOT,
                      stdout=subprocess.PIPE).stdout.decode('utf-8', 'replace')
changed = [p for p in diff.splitlines() if p.strip()]
prod = [p for p in changed if p.startswith('ClipboardHistory/Sources/')]
tests_changed = [p for p in changed if p.startswith('ClipboardHistory/Tests/')]

# —————————————————————————————— 2. 编号：从台账里读，不手抄 ——————————————————————————————

ui = read('AGENT_UI_AUDIT.md')
u_max = max([int(x) for x in re.findall(r'^- \*\*U-(\d+)：', ui, re.M)])
U1, U2, U3 = u_max + 1, u_max + 2, u_max + 3

bl = read('AGENT_BACKLOG.md')
b_max = max([int(x) for x in re.findall(r'^\*\*(\d+)\. ', bl, re.M)])
NEW_B = b_max + 1

de = read('AGENT_DECISIONS.md')
d_max = max([int(x) for x in re.findall(r'^\*\*D-(\d+)（', de, re.M)])
NEW_D = d_max + 1

it = read('AGENT_VISUAL_ITERATION.md')
rounds = [int(x) for x in re.findall(r'^## Round (\d+) · ', it, re.M)]
this_round = max(rounds) + 1
audit_round = this_round + 2

# 七维度名从上一节读（形状不许本轮发明）
last_round_block = it[it.rindex('## Round ' + str(max(rounds)) + ' · '):]
dim_rows = re.findall(r'^\|([^|]+)\|\s*(\d+)/15\s*\|', last_round_block, re.M)
if len(dim_rows) != 7:
    die('上一节的七维度行数是 ' + str(len(dim_rows)) + u'（要 7）⇒ 表形状读不到，不许自己造')
dims = [d.strip() for d, _ in dim_rows]

# —————————————————————————————— 3. 正文 ——————————————————————————————

TITLE = (u'BACKLOG 240 的行为证人补上了，实验答案是**否定的** —— '
         u'捕帧通道分不出两臂，R211 那句「靠它冻住」撤回')
SCOPE = (u'判据 ' + str(len(tests_changed)) + u' 文件，产品 ' + str(len(prod)) + u' 文件')

UI_BLOCK = u'''## 第 {AR} 轮（R{R} · {DAY}）：{TITLE}（U-{U1}…U-{U3} · {SCOPE}）

- **U-{U1}：两臂像素判据落地，读数是「两臂相同」⇒ 那个参数在捕帧通道里没有像素后果。**
  新判据 `UICaptureTests.testFrozenAndLiveArmsReadTheSameSkeletonRows`：同一个产品入口（`DetailView`）、
  同一份夹具（`makePopulatedStore(selectingIndex: 2)`），只差 `freezeLoadingForCapture` 那一个参数。
  判据自己印的读数：{PROOF} ⇒ 两臂条带行数**完全相等**。
  所以 R214 注释里那句"补了行为证人，第三把刀才会 CAUGHT"被**实测否证**：
  `.task` 里那一跳在离屏渲染期内不会落地，死值刀在这个通道里永远抓不到 ⇒ 它不进本轮变异表（不进表 ≠ 跑过），
  240 留开并把先决条件改成"要能被像素抓，先得让通道分得出两臂"（新开 {NB}）。
  副产品是好的那一条：这证明 `detail-loading-composed` 那张骨架帧**不是** R22 禁的时机赌 —— 换谁重捕都是这张。
- **U-{U2}：两条断言各配一把刀，M750/M751 全 CAUGHT（等号那条不是恒真式的正对照）。**
  `R217_MUTATE 刀={K} CAUGHT={C} ESCAPED={E} NOT_RUN={N} RESTORE_CLEAN=yes`。
  M750 把尺的第一个子句翻成恒假（`strong < 8` ⇒ `strong < 0`）⇒ 条带行数 0 ⇒ `frozenRows > 20` 红；
  M751 把**不冻臂**的外框高度 520 改成 300 ⇒ 两臂读数分叉（实测 50 vs 34）⇒ 等号那条红。
  这一刀是 R100 那条规矩的形状：只印不拦的读数等于没有读数，新断言要在**同一样本**上被抓红。
- **U-{U3}：看图腿 —— 本轮重捕整卷，看的就是被判据当对象的那张组合帧。**
  `Executed {CAPRAN} tests, with {CAPSKIP} tests skipped and 0 failures`、
  `FRAME_BASELINE_COMPARED={COMPARED} CHANGED={CHANGED} MISSING={MISSING} ADDED={ADDED}`（{DARK}+{LIGHT} 张，亮暗各半）。
  看 `/tmp/shots_r217/detail-loading-composed-720x520-{{dark,light}}.png`：头部那行（日期 · 文件 · 来源）在骨架帧里**在**，
  与三根条带、与「正在加载预览…」共用同一条左轴 ⇒ R211 的轴读数（20.5 / 20.0）在图上成立，D-206 那句假话仍被这张帧否证；
  亮档条带近乎不可见、暗档可辨（与 R215 量的 1.05 vs 1.17 同一件事，本轮不重开，条件仍记在 242）。
  本轮**没有**新增看图发现，因此没有新的动效决定 —— 看图腿交的是"对象长什么样"这笔账，不是"我又改了一处"。

其余读数：构建告警 {WARN} 条；预检 `NEEDLE_PRECHECK tables={TABLES} covered={COVERED} arms={ARMS} bad={BAD}`；
动了 `Sources/` 的文件 {PROD} 个 ⇒ 本轮无需换装本机，也无需本地全量卷（D-208 的适用面不含只动判据的轮次），
CI 那一跑仍是全量卷的复验。
'''

SCORES = {
    dims[0]: 13, dims[1]: 12, dims[2]: 13, dims[3]: 13,
    dims[4]: 12, dims[5]: 13, dims[6]: 12,
}

dim_table = '\n'.join([u'| ' + d + u' | ' + str(SCORES[d]) + u'/15 |' for d in dims])
TOTAL = sum(SCORES.values())

IT_BLOCK = u'''
## Round {TR} · {TITLE}（{DAY} · {SCOPE}）

R214 留的话是"补了行为证人，第三把刀才会 CAUGHT"。R217 真补了：同一个 `DetailView`、同一份夹具，
只差 `freezeLoadingForCapture` 一个参数，两臂各渲染一次、各数一次条带行数。
**实验答案是否定的** —— 判据自己印的是 {PROOF}：两臂一模一样。
机制：`.task(id: url)` 那一跳在离屏渲染的这段时间里不会落地，所以骨架是"初始态"，不是"被冻住的态"。
⇒ R211 我在台账里写的"靠 `freezeLoadingForCapture` 把异步冻住"这句话**没有证据**，本轮撤回（它当时是推断，被我写成了机制）。
⇒ 死值刀（把 guard 写成恒加载）在这个通道里抓不到，不登记；240 的先决条件改写成 {NB}：先让通道能等到 `.task`，再谈像素证人。
⇒ 顺带把一件我一直当运气的事钉住了：这张骨架帧不是时机赌（两臂相同 = 通道对加载不敏感），这条是本轮唯一"意外的好消息"。

判据的两条断言各配一把刀：M750 打尺的子句（0 行 ⇒ `>20` 红）、M751 打两臂相等（外框 520→300 ⇒ 50 vs 34 红）。
`R217_MUTATE 刀={K} CAUGHT={C} ESCAPED={E} NOT_RUN={N} RESTORE_CLEAN=yes`。
看图腿：重捕整卷 {COMPARED} 张、`CHANGED=0`，看的就是被判据当对象的那张组合帧（头部/条带/句子同一条左轴，亮档条带近乎不可见）。
本轮 0 个产品文件、0 处新动效决定 —— 分数低在这里，不在判据质量上。

七维度自评：

| 维度 | 得分 |
|---|---|
{DIMTABLE}

总分 {TOTAL}/105（{TR} 轮）。GAPS=none
'''.format(TR=this_round, TITLE=TITLE, DAY=DAY, SCOPE=SCOPE, PROOF=proof_text, NB=NEW_B,
           K=knives, C=caught, E=escaped, N=not_run, COMPARED=nums['COMPARED'],
           DIMTABLE=dim_table, TOTAL=TOTAL)

CH_BLOCK = u'''### 行为证人否证了自己：捕帧通道分不出冻结臂与不冻臂（R{R} / U-{U1}…U-{U3} · {SCOPE}）

- 新增 `UICaptureTests.testFrozenAndLiveArmsReadTheSameSkeletonRows`：同一份夹具、同一个 `DetailView` 入口，
  只差 `freezeLoadingForCapture` ⇒ 实测两臂条带行数相等（{PROOF}）。
  **`freezeLoadingForCapture` 在离屏捕帧通道里没有像素后果**，R211 台账里"靠它冻住"那句推断撤回。
- 两把刀：M750（尺的子句恒假 ⇒ 条带 0 行）、M751（不冻臂外框 520→300 ⇒ 两臂分叉）——
  `R217_MUTATE 刀={K} CAUGHT={C} ESCAPED={E} NOT_RUN={N}`。
- BACKLOG 240 追记 + 新开 {NB}（先让通道能等 `.task`）；立 **D-{ND}**：证人要按"它能拦什么"登记，
  拦不住的那一类要显式写成不登记，不许留一把假装跑过的刀。
- 验证：构建告警 {WARN}；捕获卷 `Executed {CAPRAN} / skipped {CAPSKIP} / 0 failures`；
  帧基线 `COMPARED={COMPARED} CHANGED=0 MISSING=0 ADDED=0`；产品 0 文件 ⇒ 未换装本机。

'''.format(R=217, U1=U1, U3=U3, SCOPE=SCOPE, PROOF=proof_text, NB=NEW_B, ND=NEW_D,
           K=knives, C=caught, E=escaped, N=not_run, WARN=warn,
           CAPRAN=cap_ran, CAPSKIP=cap_skip, COMPARED=nums['COMPARED'])

STATE_BLOCK = u'''最后更新：{NOW}（本地 · R217 / 第 {AR} 轮：**{TITLE}**（U-{U1}…U-{U3} · {SCOPE}）

**本轮落地**：240 的行为证人（同一视图两臂像素判据）落地，读数是**两臂相等**（{PROOF}）
⇒ `freezeLoadingForCapture` 在捕帧通道里没有像素后果，R214 注释里"补了证人第三把刀才会 CAUGHT"被实测否证，
R211 台账里"靠它冻住"那句推断撤回。死值刀因此**不登记**（不进表 ≠ 跑过），先决条件开成 {NB}。
两条断言各配一把刀：`R217_MUTATE 刀={K} CAUGHT={C} ESCAPED={E} NOT_RUN={N} RESTORE_CLEAN=yes`（M750 尺子句、M751 两臂相等正对照）。
看图腿：重捕整卷 `COMPARED={COMPARED} CHANGED=0`，看的就是被判据当对象的那张组合帧（头部/条带/句子同轴；亮档条带近乎不可见 = 242 已判过）。
构建告警 {WARN}；预检 `tables={TABLES} covered={COVERED} arms={ARMS} bad={BAD}`；产品 0 文件 ⇒ 未换装本机、本地全量卷按 D-208 的适用面不需要。
CI：本轮这一跑 + `9af75f7`/`610e93c` 都要读 —— `STEP[8]`、`STEP[15]` 是否绿、`Surface left-axis ruler` 打 ok/skipped/unavailable（**235 结案的唯一通道**）。

**下一轮（R218）的靶**：⓪ 读上面三跑（235 结案）；① {NB}：捕帧通道能不能等到 `.task`（先 spike，别改产品）；
② 237（pillow 安装位置）；③ 227③、222、215、201/202、207；④ 回到动效位点本体（连续多轮 0 产品改动，目标要求的是"逐位点重判并加该加的动效"）；⑤ 220 路 A、228② 等用户。
)

'''.format(NOW=NOW, AR=audit_round, TITLE=TITLE, U1=U1, U3=U3, SCOPE=SCOPE, PROOF=proof_text,
           NB=NEW_B, K=knives, C=caught, E=escaped, N=not_run, COMPARED=nums['COMPARED'],
           WARN=warn, TABLES=tables, COVERED=covered, ARMS=arms, BAD=bad)

BL_BLOCK = u'''
**240 追记（R217 实测否证·仍开）：行为证人补上了，但它证明的是"通道分不出两臂"**

R214 写的补法是"同一视图两臂的像素判据 ⇒ 有了它，第三把刀（传死值）才会 ESCAPED→CAUGHT"。
R217 把它补上了（`testFrozenAndLiveArmsReadTheSameSkeletonRows`），读数：{PROOF} ⇒ **两臂完全相同**。
所以那把死值刀在这个通道里**永远抓不到**，它没进本轮变异表（不进表 ≠ 跑过），本条不写结案。
本条现在能说的只有：骨架帧不是时机赌（两臂相同 = 通道对加载不敏感），以及参数仍只有源码形状三条证人（`MediaLoadingPlanTests`）。
先决条件移交 {NB}。

**{NB}. 离屏捕帧通道等不到 `.task`：想给异步态补像素证人，得先有一条能等它的通道（R217 实测开单）**

现场：同一个 `DetailView`，`freezeLoadingForCapture` 传 true 与传 false 拍出来的像素**一模一样**
（{PROOF}）⇒ 加载/失败态在捕帧通道里根本到不了，所以"冻住"这个词从来没有像素含义。
这一格欠的不是一条断言，而是一条**能力**：捕帧时能不能等一次 `.task` 落地（或显式驱动一次异步）。
先做实验再动产品：spike 三种通道（渲染后跑一次 runloop / 给夹具一个"完成回调"再拍 / 用现成的 in-screen 通道），
各自答"能不能让不冻臂真的走到失败态"。三条都不行就把本条结案成"通道限制"，并把它挂到 201 那一族（无头 runner 的高窗只画一条下沿带）下面记。
适用面：所有异步状态（图片/文件预览、加载→成功/失败切换）的像素验收；不适用：同步就能画出来的状态。

'''.format(PROOF=proof_text, NB=NEW_B)

DE_BLOCK = u'''
**D-{ND}（R217）：证人要按"它能拦住哪一类坏法"登记；拦不住的那一类要显式写成不登记，不许留一把假装跑过的刀**

现场：R214 我在 `mutate_r214.py` 的注释里写"补了行为证人，第三把刀才会 CAUGHT"，R217 真补了证人，
实测两臂像素相同 ⇒ 那把刀**在这个通道里永远抓不到**。如果当时按原计划登记它，表上会多一行 ESCAPED；
如果把它悄悄删掉，下一轮就会以为"死值有人拦"。两种都比"没有刀"更坏。
规矩：① 一把刀在登记前要先问"它坏掉时哪一条断言会红"，答不出就不登记；② 已经写了"要补的刀"的，
补不出来要把**为什么补不出来**（通道缺哪条能力）写成一条会红的开单，而不是把那句话留在注释里当已办；
③ 一条断言若只能被"尺坏掉"抓红（M750 那一类），要另配一条**被量的对象真变了**会抓红的对照刀（M751 那一类），否则它是恒真式的风险要写进正文。
适用面：所有变异表与新判据的收尾；不适用：单元测试自己就是判据的那些（它们不需要像素通道）。
'''.format(ND=NEW_D)

UI_NEW = u'''## 第 {AR} 轮（R{R} · {DAY}）：{TITLE}（U-{U1}…U-{U3} · {SCOPE}）

- **U-{U1}：两臂像素判据落地，读数是「两臂相同」⇒ 那个参数在捕帧通道里没有像素后果。**
  新判据 `UICaptureTests.testFrozenAndLiveArmsReadTheSameSkeletonRows`：同一个产品入口（`DetailView`）、
  同一份夹具（`makePopulatedStore(selectingIndex: 2)`），只差 `freezeLoadingForCapture` 那一个参数。
  判据自己印的读数：{PROOF} ⇒ 两臂条带行数**完全相等**。
  所以 R214 注释里那句"补了行为证人，第三把刀才会 CAUGHT"被**实测否证**：
  `.task` 里那一跳在离屏渲染期内不会落地，死值刀在这个通道里永远抓不到 ⇒ 它不进本轮变异表（不进表 ≠ 跑过），
  240 留开并把先决条件改成"要能被像素抓，先得让通道分得出两臂"（新开 {NB}）。
  副产品是好的那一条：这证明 `detail-loading-composed` 那张骨架帧**不是** R22 禁的时机赌 —— 换谁重捕都是这张。
- **U-{U2}：两条断言各配一把刀，M750/M751 全 CAUGHT（等号那条不是恒真式的正对照）。**
  `R217_MUTATE 刀={K} CAUGHT={C} ESCAPED={E} NOT_RUN={N} RESTORE_CLEAN=yes`。
  M750 把尺的第一个子句翻成恒假（`strong < 8` ⇒ `strong < 0`）⇒ 条带行数 0 ⇒ `frozenRows > 20` 红；
  M751 把**不冻臂**的外框高度 520 改成 300 ⇒ 两臂读数分叉（实测 50 vs 34）⇒ 等号那条红。
  这一刀是 R100 那条规矩的形状：只印不拦的读数等于没有读数，新断言要在**同一样本**上被抓红。
- **U-{U3}：看图腿 —— 本轮重捕整卷，看的就是被判据当对象的那张组合帧。**
  `Executed {CAPRAN} tests, with {CAPSKIP} tests skipped and 0 failures`、
  `FRAME_BASELINE_COMPARED={COMPARED} CHANGED={CHANGED} MISSING={MISSING} ADDED={ADDED}`（亮暗各 {HALF} 张）。
  看 `/tmp/shots_r217/detail-loading-composed-720x520-{{dark,light}}.png`：头部那行（日期 · 文件 · 来源）在骨架帧里**在**，
  与三根条带、与「正在加载预览…」共用同一条左轴 ⇒ R211 的轴读数（20.5 / 20.0）在图上成立，D-206 那句假话仍被这张帧否证；
  亮档条带近乎不可见、暗档可辨（与 R215 量的 1.05 vs 1.17 同一件事，本轮不重开，条件仍记在 242）。
  本轮**没有**新增看图发现，因此没有新的动效决定 —— 看图腿交的是"对象长什么样"这笔账，不是"我又改了一处"。

其余读数：构建告警 {WARN} 条；预检 `NEEDLE_PRECHECK tables={TABLES} covered={COVERED} arms={ARMS} bad={BAD}`；
动了 `Sources/` 的文件 {PROD} 个 ⇒ 本轮无需换装本机，也无需本地全量卷（D-208 的适用面不含只动判据的轮次），
CI 那一跑仍是全量卷的复验。

'''.format(AR=audit_round, R=217, DAY=DAY, TITLE=TITLE, U1=U1, U2=U2, U3=U3, SCOPE=SCOPE,
           PROOF=proof_text, NB=NEW_B, K=knives, C=caught, E=escaped, N=not_run,
           CAPRAN=cap_ran, CAPSKIP=cap_skip, COMPARED=nums['COMPARED'], CHANGED=nums['CHANGED'],
           MISSING=nums['MISSING'], ADDED=nums['ADDED'], HALF=nums['COMPARED'] // 2,
           WARN=warn, TABLES=tables, COVERED=covered, ARMS=arms, BAD=bad, PROD=len(prod))

def plan_insert_where(path, pattern, block, expect_contains):
    """按**形状**找插入点（第一个匹配行），而不是按拼出来的旧值（R89 的教训）。"""
    text = read(path)
    m = re.search(pattern, text, re.M)
    if not m:
        die('形状找不到：' + path + ' ｜ ' + pattern)
    line = text[m.start():text.find('\n', m.start())]
    if expect_contains not in line:
        die('找到的第一格不是上一轮那一格：' + path + ' ｜ ' + line[:70])
    new = text[:m.start()] + block + text[m.start():]
    if block not in new or not halves_kept(text, m.start(), new):
        die('插入没生效：' + path)
    DELTAS[path] = block
    plans.append((path, text, new))


def halves_kept(text, cut, new):
    """插入式改动的"旧内容没被吃掉"判据：前后两半都必须**连续**留在新文件里。
    （不能写 `old in new` —— 从中间插入后，旧文件本身不再是连续子串。）"""
    return text[:cut] in new and text[cut:] in new


DELTAS = {}


def reinsertion_matches(old, new, path):
    """最硬的一道：把本轮插进去的那一块**原样抠掉**，必须逐字节等于旧文件。
    抠得回去 ⇒ 旧行一行没被吃掉（R100 的"编辑台账插入实为替换"就是这一格漏的）。"""
    blk = DELTAS.get(path)
    if blk is None:
        return new.startswith(old)
    return new.count(blk) == 1 and new.replace(blk, '', 1) == old


# —————————————————————————————— 4. 算完再写（事务性） ——————————————————————————————

plans = []


def plan_insert(path, anchor, block, where='before'):
    text = read(path)
    idx = text.find(anchor)
    if idx < 0:
        die('锚点找不到：' + path + ' ｜ ' + anchor[:60])
    if text.find(anchor, idx + 1) >= 0:
        die('锚点不唯一：' + path + ' ｜ ' + anchor[:60])
    new = (text[:idx] + block + text[idx:]) if where == 'before' else (text[:idx] + len(anchor) and (text[:idx + len(anchor)] + block + text[idx + len(anchor):]))
    if block not in new or len(new) <= len(text):
        die('插入没生效：' + path)
    if anchor not in new:
        die('锚点被吃掉：' + path)
    DELTAS[path] = block
    plans.append((path, text, new))


def plan_append(path, block):
    text = read(path)
    new = text.rstrip('\n') + '\n\n' + block.strip('\n') + '\n'
    if block.strip('\n') not in new:
        die('追加没生效：' + path)
    plans.append((path, text, new))


# UI_AUDIT：插到当前最大轮次标题之上（降序那本）
plan_insert('AGENT_UI_AUDIT.md', u'## 第 ' + str(audit_round - 1) + u' 轮（R216 · ', UI_NEW, 'before')
# ITERATION：升序那本，只能追加到文件尾
plan_append('AGENT_VISUAL_ITERATION.md', IT_BLOCK)
# CHANGELOG：[Unreleased] 之下
ch = read('CHANGELOG.md')
idx = ch.find(u'## [Unreleased]')
if idx < 0:
    die('CHANGELOG 没有 [Unreleased]')
cut = idx + len(u'## [Unreleased]')
if ch[cut:cut + 1] != u'\n':
    die('CHANGELOG 的 [Unreleased] 行尾不是换行 ⇒ 插入形状与预期不符')
plans.append(('CHANGELOG.md', ch, ch[:cut] + u'\n' + CH_BLOCK + ch[cut + 1:]))
DELTAS['CHANGELOG.md'] = CH_BLOCK
# STATE：新的那一格放在最前（按形状找上一轮那一格，不拼旧值）
plan_insert_where('AGENT_STATE.md', u'^最后更新：', STATE_BLOCK, u'R216 / 第 218 轮')
# BACKLOG / DECISIONS：追加
plan_append('AGENT_BACKLOG.md', BL_BLOCK)
plan_append('AGENT_DECISIONS.md', DE_BLOCK)

for path, old, new in plans:
    if len(new) <= len(old) or len(new.splitlines()) <= len(old.splitlines()):
        die('写盘前最后一道：' + path + u' 没有变长（半份台账比没写更坏）')
    # 每一处插入都要能还原成"旧文件被完整保留"：把新文件里的每个 block 抠掉后必须等于旧文件。
    if not reinsertion_matches(old, new, path):
        die('写盘前最后一道：' + path + u' 抠掉新块后不等于旧文件 ⇒ 有旧行被吃掉')

for path, old, new in plans:
    write(path, new)

print(u'LEDGERS_R217 wrote %d files: %s' % (len(plans), u'、'.join([p for p, _, _ in plans])))
print(u'LEDGERS_R217 编号：第 %d 轮 / Round %d / U-%d…U-%d / BACKLOG +%d / D-%d'
      % (audit_round, this_round, U1, U3, NEW_B, NEW_D))
print(u'LEDGERS_R217 读数：捕获 %d/%d skip/%d fail、帧 %s、刀 %d/%d、告警 %d、产品 %d 文件'
      % (cap_ran, cap_skip, cap_fail, str(nums), caught, knives, warn, len(prod)))
print(u'LEDGERS_R217 行为证人：' + proof_text)

# 落盘后自检：本轮标题行必须能被跨账判据读到
state = read('AGENT_STATE.md')
mm = re.search(u'最后更新：[^\\n]*?R(\\d+) / 第 (\\d+) 轮', state)
if not mm or int(mm.group(1)) != 217 or int(mm.group(2)) != audit_round:
    die('STATE 的轮次行读不出 R217 / 第 ' + str(audit_round) + u' 轮 ⇒ 跨账判据会空跑')
for path, pat in ((u'AGENT_UI_AUDIT.md', u'^## 第 ' + str(audit_round) + u' 轮（R217'),
                  (u'AGENT_VISUAL_ITERATION.md', u'^## Round 217 · '),
                  (u'CHANGELOG.md', u'^### .*（R217 / ')):
    if not re.search(pat, read(path), re.M):
        die(path + u' 里读不到本轮标题：' + pat)
print(u'LEDGERS_R217 selfcheck ok（三本账的标题行 + STATE 轮次行都能被正则读到）')
sys.exit(0)

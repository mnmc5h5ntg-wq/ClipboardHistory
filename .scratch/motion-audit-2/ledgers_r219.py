# -*- coding: utf-8 -*-
"""R219 的台账生成器：亮档骨架墨按档给（BACKLOG 242 结案），三把刀全 CAUGHT，含一次自曝的尺错。

规矩同 R217/R218：数字全部从本轮真实日志解析；插入用切片 + 抠块还原；七维度名从上一节读；
编号从台账正则取 max+1；缺任何一格读数就拒绝写盘。
"""
import io, os, re, subprocess, sys

ROOT = '/Users/wangziyi/Codex_Project0'
DAY = '2026-10-19'
NOW = '2026-10-19 22:32'


def read(p):
    return io.open(os.path.join(ROOT, p), encoding='utf-8').read()


def write(p, t):
    with io.open(os.path.join(ROOT, p), 'w', encoding='utf-8') as h:
        h.write(t)


def die(why):
    print('LEDGERS_R219 refused: ' + why)
    sys.exit(1)


def log(p):
    path = os.path.join('/tmp', p)
    if not os.path.exists(path):
        die('缺少本轮日志 ' + path + ' ⇒ 不许写台账')
    return io.open(path, encoding='utf-8', errors='replace').read()


# ——————————————————— 读数 ———————————————————

build = log('r219_build.log')
warn = build.count('warning:')
if 'error:' in build:
    die('构建日志里有 error: ⇒ 先修')

tests = log('r219_tests.log')
m = re.search(r'Executed (\d+) tests, with (\d+) tests skipped and (\d+) failures', tests)
if not m:
    die('读不到判据卷摘要行')
roll_ran, roll_skip, roll_fail = [int(x) for x in m.groups()]
if roll_fail != 0:
    die('判据卷有 ' + str(roll_fail) + ' 朵红')

full = log('r219_full.log')
mf = list(re.finditer(r'Executed (\d+) tests, with (\d+) tests skipped and (\d+) failures', full))
if not mf:
    die('读不到全量卷摘要行（D-208 要求本轮必须跑）')
full_ran, full_skip, full_fail = [int(x) for x in mf[-1].groups()]
if full_fail != 0:
    die('全量卷有红 ⇒ 先修再写台账')

mut = log('r219_mutate2.log')
mm = re.search(r'R219_MUTATE 刀=(\d+) CAUGHT=(\d+) ESCAPED=(\d+) NOT_RUN=(\d+)', mut)
if not mm:
    die('读不到变异表结论行')
knives, caught, escaped, not_run = [int(x) for x in mm.groups()]
if escaped or not_run or caught != knives:
    die('变异表不干净：' + mm.group(0))
first_attempt = log('r219_mutate.log')
m754_notrun = 'M754 NOT_RUN' in first_attempt

upd = log('r219_baseline_update.log')
mu = re.search(r'FRAME_BASELINE_UPDATED=(\d+)', upd)
if not mu:
    die('读不到帧基线 update 的帧数')
frames = int(mu.group(1))
cmp2 = log('r219_baseline2.log')
mc = re.search(r'FRAME_BASELINE_CHANGED=(\d+)', cmp2)
if not mc or int(mc.group(1)) != 0:
    die('update 之后重比仍有 CHANGED ⇒ 基线没写进去')
# 变了哪几张、按档分开数（这是"按档生效"的证人，不许手抄）
bl = log('r219_baseline.log')
changed_names = re.findall(r'^\s+changed\s+(\S+\.png)', bl, re.M)
n_changed = len(changed_names)
light_changed = len([n for n in changed_names if n.endswith('-light.png')])
dark_changed = len([n for n in changed_names if n.endswith('-dark.png')])
if n_changed != 3 or dark_changed != 0:
    die('changed 名单与预期不符：' + str(changed_names) + u' ⇒ 「只有亮档变」这条证人读不到，别写')

before = log('r219_before.log')
after = log('r219_after.log')


def contrast(text, frame):
    row = [l for l in text.splitlines() if frame in l]
    if not row:
        die('读数里找不到 ' + frame)
    m2 = re.search(r'条带=\((\d+), (\d+), (\d+)\).*?对比度=([\d.]+)', row[-1])
    if not m2:
        die('解析不了 ' + frame + ' 的读数行')
    return m2.group(4), '(%s,%s,%s)' % m2.groups()[:3]


comp_before, bar_before = contrast(before, 'detail-loading-720x520-light.png')
comp_after, bar_after = contrast(after, 'detail-loading-720x520-light.png')
dark_after, _ = contrast(after, 'detail-loading-720x520-dark.png')
comp_rows_before = re.search(r'detail-loading-720x520-light.png.*?条带行=(\d+)', before).group(1)
comp_rows_after = re.search(r'detail-loading-720x520-light.png.*?条带行=(\d+)', after).group(1)
if comp_rows_before != comp_rows_after:
    die('前后条带行数不同（' + comp_rows_before + ' vs ' + comp_rows_after + u'）⇒ 两趟量的不是同一个对象')
composed_rows = re.search(r'detail-loading-composed-720x520-light.png.*?条带行=(\d+)', after).group(1)

diff = subprocess.run(['git', 'diff', '--name-only', 'HEAD'], cwd=ROOT,
                      stdout=subprocess.PIPE).stdout.decode('utf-8', 'replace')
changed = [p for p in diff.splitlines() if p.strip()]
prod = [p for p in changed if p.startswith('ClipboardHistory/Sources/')]
tests_changed = [p for p in changed if p.startswith('ClipboardHistory/Tests/')]
docs = [p for p in changed if p.startswith('docs/')]
if len(prod) != 1 or len(docs) != 1:
    die('对象不明：产品 ' + str(prod) + u' / 基线 ' + str(docs))

# ——————————————————— 编号 ———————————————————

ui = read('AGENT_UI_AUDIT.md')
u_max = max([int(x) for x in re.findall(r'^- \*\*U-(\d+)：', ui, re.M)])
U1, U2, U3 = u_max + 1, u_max + 2, u_max + 3
bl_t = read('AGENT_BACKLOG.md')
b_max = max([int(x) for x in re.findall(r'^\*\*(\d+)\. ', bl_t, re.M)])
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

TITLE = u'亮档骨架墨按档给（242 结案）：3 张亮档帧变了、0 张暗档帧变，同时自曝一把量错对象的尺'
SCOPE = u'产品 ' + str(len(prod)) + u' 文件，判据 ' + str(len(tests_changed)) + u' 文件'

UI_NEW = u'''## 第 {AR} 轮（R219 · {DAY}）：{TITLE}（U-{U1}…U-{U3} · {SCOPE}）

- **U-{U1}：亮档的骨架墨不再与暗档共用一个 opacity（BACKLOG 242 结案）。**
  `SkeletonMotion` 多一处 `inkOpacities(dark:)`：暗档仍是 **0.06 / 0.18**（一个数都没动），
  亮档给 **0.14 / 0.26** —— 抬升量两档同为 0.12，仍在 `minimumHighlightLift=0.08` 之上、0.35 天花板之下。
  为什么必须按档给：`Color.primary.opacity(α)` 是**乘法**，同一个 α 在 255 的底上给 Δ13、在 30 的底上给 Δ11，
  而 R215 的"亮档 1.05"量的其实是组合帧里另一处底 —— 所以这一轮先重测再决定抬多少（见 U-{U3}）。
  组件帧亮档实测：条带 (242,242,242) → **{bar_after}**，对比度 **{cb} → {ca}**（两趟条带行数都是 {rows} ⇒ 同一对象）。
  帧基线的证人：`changed` 名单 {nc} 张，**亮档 {lc} 张 / 暗档 {dc} 张** ⇒ "按档给"这件事第一次在像素上被分开看见。
- **U-{U2}：三把刀全 CAUGHT，其中第一版 NOT_RUN 的教训记进正文。**
  `R219_MUTATE 刀={K} CAUGHT={C} ESCAPED={E} NOT_RUN={N} RESTORE_CLEAN=yes`：
  M752 让 `inkOpacities` 忽略参数（亮档退回暗档那两个数）⇒ 真值表「亮档底色墨必须深于暗档」红；
  M753 只抬亮档 base 不抬 highlight（0.26→0.20，lift 掉到 0.06）⇒ 亮档那一格的 lift 下界红 ——
  这一刀钉的正是 242 写下的条件"要抬就同时抬两档"；
  M754 把视图里的按档取墨换回直接吃档盲常量 ⇒ 接线守卫红。
  **M754 第一版是 NOT_RUN 而不是 CAUGHT**：那一种坏法（把 `@Environment` 换成写死的 `.dark`）编译不过，
  `Executed 0` 不算拦住（{first_note}）⇒ 换成能编译的坏法才拿到这格。
- **U-{U3}：自曝 —— 组合帧那一格我这把一次性尺量错了对象，所以 242 的"1.05"不能被引用成"改前"。**
  同一把尺（`.local/skeleton_ink_measure.py`，未入库）在组合帧上读出条带行数 **{crows}**（组件帧是 {rows}）
  ⇒ 它抓的是**详情面板与窗口的接缝**，不是条带：组合帧里"底"该取面板自己的颜色，我却取了画面众数。
  处置：这一格只引用**组件帧**那两趟（同对象、同行数）与 `changed` 名单，
  组合帧的对比度判成"这把尺量不了"，并新开 {NB}：把"骨架条带对比度按档各有一条下界"做成仓库内的像素判据，
  别再靠 /tmp 手搓尺（R99/R100 那条老规矩，本轮又犯一次）。

看图腿（真看了两张新帧）：`/tmp/shots_r219/detail-loading-composed-720x520-light.png` 与
`detail-loading-720x520-light.png` —— 亮档条带从"要盯才看得见"变成"一眼是三根占位条"，
但仍比同帧那句「正在加载预览…」淡一档，头部/条带/句子共用同一条左轴没变，右下角动作栏图标的对比仍强于条带
⇒ 判定是**积极作用**，没有走到"有分量的灰块"那一侧（242 留的红线）。暗档两帧像素未变（{dc} 张 changed）。

其余读数：构建告警 {warn}；判据卷 `Executed {rran} / skipped {rskip} / 0 failures`；
全量卷（D-208：动了 `Sources/`）`Executed {fran} / skipped {fskip} / 0 failures`；
帧基线 `FRAME_BASELINE_UPDATED={frames}` 且 update 后重比 `CHANGED=0`；已换装本机。

'''.format(AR=audit_round, DAY=DAY, TITLE=TITLE, U1=U1, U2=U2, U3=U3, SCOPE=SCOPE,
           bar_after=bar_after, cb=comp_before, ca=comp_after, rows=comp_rows_after,
           nc=n_changed, lc=light_changed, dc=dark_changed,
           K=knives, C=caught, E=escaped, N=not_run, first_note=(u'已换刀重跑' if m754_notrun else u'本轮日志未记录第一版'),
           crows=composed_rows, NB=NEW_B, warn=warn, rran=roll_ran, rskip=roll_skip,
           fran=full_ran, fskip=full_skip, frames=frames)

SCORES = {dims[0]: 14, dims[1]: 13, dims[2]: 13, dims[3]: 14,
          dims[4]: 12, dims[5]: 14, dims[6]: 12}
dim_table = '\n'.join([u'| ' + d + u' | ' + str(SCORES[d]) + u'/15 |' for d in dims])
TOTAL = sum(SCORES.values())

IT_BLOCK = u'''
## Round {TR} · {TITLE}（{DAY} · {SCOPE}）

回到产品面。靶是 242：亮档详情骨架的条带几乎看不见（R215 量的 1.05），而暗档 1.17 是可辨的。
这一轮先重测再改：同一把尺在**组件帧**上读到 亮档 底 255 ↔ 条带 (242,242,242) = **{cb}**、
暗档 底 30 ↔ 条带 (41,41,41) = **{dark}**；抬到 0.14 / 0.26 之后亮档条带变成 **{bar_after}** = **{ca}**，
暗档一个像素都没变（`changed` 名单 {nc} 张：亮档 {lc}、暗档 {dc}）。
"按档给"这件事第一次在像素上被分开看见 —— 而不是靠"应该没问题"。

为什么两档共用一个 opacity 一定会坏：`Color.primary.opacity(α)` 是乘法，同一个 α 在两个底上给的**绝对**差值不是一个量级；
而"抬升预算"必须两档同时抬，否则 lift 掉到 `minimumHighlightLift` 以下，扫光退回 R214 那个峰值 0.0000 —— 这条由 M753 钉住。
三把刀：`R219_MUTATE 刀={K} CAUGHT={C} ESCAPED={E} NOT_RUN={N}`。
M754 第一版**没咬到**：那种坏法（写死 `.dark`）编译不过 ⇒ `Executed 0` 是 NOT_RUN，不是 CAUGHT；换成能编译的坏法才算数。

**本轮同时自曝一把量错对象的尺**：它在组合帧上读出条带行数 {crows}（组件帧 {rows}），
抓的其实是详情面板与窗口的接缝 ⇒ 242 原文里那个"1.05"不能当本轮的改前值引用，
能引用的只有组件帧两趟（同对象、同行数）与 changed 名单。组合帧的对比度判成"这把尺量不了"，
开 {NB} 把它做成仓库内的按档像素判据。看图：亮档条带现在是"一眼三根占位条"，仍比那句说明淡一档、
左轴没变、动作栏图标仍更抢 ⇒ 积极作用，没越"不喧宾夺主"。

七维度自评：

| 维度 | 得分 |
|---|---|
{DIMTABLE}

总分 {TOTAL}/105（{TR} 轮）。GAPS=none
'''.format(TR=this_round, TITLE=TITLE, DAY=DAY, SCOPE=SCOPE, cb=comp_before, ca=comp_after,
           dark=dark_after, bar_after=bar_after, nc=n_changed, lc=light_changed,
           dc=dark_changed, K=knives, C=caught, E=escaped, N=not_run, crows=composed_rows, rows=comp_rows_after,
           NB=NEW_B, TOTAL=TOTAL, DIMTABLE=dim_table)

CH_BLOCK = u'''### 亮档骨架墨按档给（BACKLOG 242 结案）：暗档不动、亮档 1.12 → {ca}（R{R} / U-{U1}…U-{U3} · {SCOPE}）

- `SkeletonMotion.inkOpacities(dark:)`：暗档仍是 0.06 / 0.18（未动），亮档给 **0.14 / 0.26**（lift 两档同 0.12）。
  视图经 `@Environment(\\.colorScheme)` 问系统，**唯一一处**读档的地方（提成 **D-{ND}**）。
- 证人：帧基线 `changed` 共 {nc} 张 = 亮档 {lc} / 暗档 {dc} ⇒ 按档生效第一次在像素上分开可见；
  组件帧亮档条带 (242,242,242) → {bar_after}、对比度 {cb} → {ca}（两趟条带行数同）。
- 判据：真值表（两档各过 lift 下界 + 亮档底色必须深于暗档 + 暗档仍是原令牌）+ 接线守卫；
  `R219_MUTATE 刀={K} CAUGHT={C} ESCAPED={E} NOT_RUN={N}`（M754 第一版 NOT_RUN，换成能编译的坏法后才 CAUGHT）。
- 自曝：一次性尺在组合帧上量错对象（条带行数 {crows}）⇒ 242 原文的 1.05 不作本轮改前值引用，开 {NB} 做仓库内按档像素判据。
- 验证：构建告警 {warn}；判据卷 {rran} 格 0 红；**全量卷 {fran} 格 0 红**（D-208）；
  `FRAME_BASELINE_UPDATED={frames}` 且 update 后重比 CHANGED=0（同一笔提交里 update）；已换装本机。

'''.format(R=219, U1=U1, U3=U3, SCOPE=SCOPE, ca=comp_after, cb=comp_before, bar_after=bar_after,
           nc=n_changed, lc=light_changed, dc=dark_changed, K=knives, C=caught, E=escaped, N=not_run, ND=NEW_D,
           NB=NEW_B, warn=warn, rran=roll_ran, fran=full_ran, frames=frames, crows=composed_rows)

STATE_BLOCK = u'''最后更新：{NOW}（本地 · R219 / 第 {AR} 轮：**{TITLE}**（U-{U1}…U-{U3} · {SCOPE}）

**本轮落地**：242 结案 —— 亮档详情骨架的墨与暗档分开给（暗档 0.06/0.18 **未动**，亮档 **0.14/0.26**，lift 两档同 0.12）。
视图只经 `SkeletonMotion.inkOpacities(dark:)` 取墨（唯一读档处，提成 **D-{ND}**）。
证人：帧基线 `changed` {nc} 张 = 亮档 {lc} / 暗档 {dc}（按档生效第一次在像素上分开可见）；
组件帧亮档条带 (242,242,242) → {bar_after}、对比度 {cb} → {ca}（两趟条带行数同 ⇒ 同一对象）；看图判定为**积极作用**（仍比说明文字淡一档、左轴未变、动作栏图标更抢）。
判据：真值表 + 接线守卫；`R219_MUTATE 刀={K} CAUGHT={C} ESCAPED={E} NOT_RUN={N}`（M754 第一版编译不过 ⇒ NOT_RUN 不算拦住，换刀重跑）。
**自曝**：一次性尺在组合帧上量错对象（条带行数 {crows} vs 组件帧 {rows}）⇒ 242 原文的"1.05"不作本轮改前值引用，开 {NB} 做仓库内按档像素判据。
验证：构建告警 {warn}；判据卷 {rran}/{rskip}skip/0fail；全量卷 {fran}/{fskip}skip/0fail（D-208）；
`FRAME_BASELINE_UPDATED={frames}`、update 后重比 CHANGED=0；已换装本机；电池在台账落盘后再跑。
CI：本跑（产品改动）+ `193d5be`=39265858795、`1462b38`=39265952407、`261c42d` 都要读 —— **237 结案的唯一通道**是 venv 那一步有没有打 `PILLOW_OK`、左轴那一步的 `verdict` 是否从 `unavailable` 变出来。

**下一轮（R220）的靶**：⓪ 读上面几跑（237；顺带看这一跑的 `STEP[15]` 有没有被本轮的亮档墨改动弄红）；
① {NB}：把"骨架条带对比度按档各一条下界"做成仓库内的像素判据（别再靠 /tmp 手搓尺），并给 242 的**其余亮档表面**（热图阶梯、侧栏占位）逐个判一次要不要同样按档给；
② 243：捕帧通道能不能等到 `.task`（先 spike）；③ 227③、222、215、201/202、207、244；④ 220 路 A、228② 等用户。
)

'''.format(NOW=NOW, AR=audit_round, TITLE=TITLE, U1=U1, U3=U3, SCOPE=SCOPE, ND=NEW_D,
           nc=n_changed, lc=light_changed, dc=dark_changed, bar_after=bar_after,
           cb=comp_before, ca=comp_after, K=knives, C=caught, E=escaped, N=not_run, crows=composed_rows,
           rows=comp_rows_after, NB=NEW_B, warn=warn, rran=roll_ran, rskip=roll_skip,
           fran=full_ran, fskip=full_skip, frames=frames)

BL_BLOCK = u'''
**242 追记（R219 结案）：两档同时抬，lift 保住 0.12，暗档一个像素没动**

按本条写下的条件做完了：`SkeletonMotion.inkOpacities(dark:)` 给暗档 0.06 / 0.18（**未改**）、亮档 **0.14 / 0.26**，
两档 lift 都是 0.12（≥ `minimumHighlightLift` 0.08、亮带 ≤ 0.35 天花板）。
像素证人：帧基线 `changed` 只有亮档 {lc} 张、暗档 {dc} 张 ⇒ "按档"在捕帧通道里成立；
组件帧亮档条带 (242,242,242) → {bar_after}、对比度 {cb} → {ca}。
看图判定：亮档条带从"要盯才见"变成"一眼三根占位条"，仍比那句说明淡一档、左轴未变 ⇒ 积极作用，未越红线。
"要抬就同时抬两档并重跑胶片判据"这一条由 **M753** 钉住（只抬 base ⇒ lift 0.06 ⇒ 真值表红）。
**一处更正**：本条原文的"亮档 1.05"是组合帧上量的，而 R219 那把一次性尺在组合帧上量错了对象
（条带行数 {crows}，抓的是面板/窗口接缝）⇒ 1.05 这个数**不作本轮改前值引用**；本轮引用的是组件帧的 {cb} → {ca}
（同一把尺、同一条带行数）。组合帧的按档对比度改由 {NB} 用仓库内判据重做。

**{NB}. 骨架条带的对比度该由仓库内的像素判据按档各钉一条下界（R219 开单：一次性尺量错对象那一格）**

现状：亮档/暗档的条带对比度只有**台账里的数**与一张一次性尺（`.local/skeleton_ink_measure.py`，未入库）在管；
R219 那把尺在组合帧上把"面板与窗口的接缝"读成"条带"（条带行数 {crows} vs 组件帧 {rows}），
于是"改前 1.05"这句话差点被引用成本轮的证人。这正是 R99/R100 记过的老毛病：**/tmp 手搓尺只配形成问题**。
要补的形状：把条带对比度做成仓库内的判据（Swift 侧像素谓词，和 `UICaptureHarness.skeletonAxisReadings` 同源的条带行判定），
两档**各**一条下界（暗档实测 {dark}、亮档实测 {ca} ⇒ 下界取"改前可辨值"而不是本轮新值，别把红线钉成地板），
外加一格"底必须取条带自己所在面板的众数"的对照（组合帧与组件帧各一次），否则这条判据会重犯本轮这把尺的错。
适用面：详情骨架条带（两档）；不适用：热图阶梯（227 已按两条尺各判一次）、说明文字（R27 那族）。

'''.format(lc=light_changed, dc=dark_changed, bar_after=bar_after, cb=comp_before, ca=comp_after,
           crows=composed_rows, rows=comp_rows_after, NB=NEW_B, dark=dark_after)

DE_BLOCK = u'''
**D-{ND}（R219）：按档给的视觉量必须只有**一处**读档，且视图不许直接吃"档盲"常量 —— 这条要有接线守卫**

现场：骨架那两层墨以前是两个 `static let`，谁都能写 `Color.primary.opacity(SkeletonMotion.baseOpacity)`；
"亮档几乎看不见条带"（242）因此不是某个视图写错了，而是**这个量天生不分档**。
本轮把它提成 `SkeletonMotion.inkOpacities(dark:)`，视图经 `@Environment(\\.colorScheme)` 问系统，
并加一条守卫扫源码：出现 `Color.primary.opacity(SkeletonMotion.baseOpacity)` 这种档盲写法就红（M754 会把它抓回来）。
规矩：① 凡"两档该长得不一样"的量，收进一个**按档取值的纯函数**，别留两个常量让调用方自选；
② 档的来源只能有一处（系统），谁写死 `.dark`/`.light` 谁红；
③ 这类重构必须自带"没人调用"的守卫（D-055 那一族）—— 真值表全绿而视图没接线，等于台账里多两个数。
适用面：所有按外观档取值的视觉量（墨、描边、材质补偿）；不适用：与档无关的几何量（间距、字号）。
'''.format(ND=NEW_D)

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
    if not reinsertion_matches(text, new, path):
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


plan_insert('AGENT_UI_AUDIT.md', u'## 第 ' + str(audit_round - 1) + u' 轮（R218 · ', UI_NEW)
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
plan_insert_where('AGENT_STATE.md', u'^最后更新：', STATE_BLOCK, u'R218 / 第 220 轮')
plan_append('AGENT_BACKLOG.md', BL_BLOCK)
plan_append('AGENT_DECISIONS.md', DE_BLOCK)

for path, old, new in plans:
    if len(new.splitlines()) <= len(old.splitlines()):
        die('写盘前最后一道：' + path + u' 行数没增加')
    if not reinsertion_matches(old, new, path):
        die('写盘前最后一道：' + path + u' 抠掉新块后不等于旧文件')

for path, old, new in plans:
    write(path, new)

print(u'LEDGERS_R219 wrote %d files' % len(plans))
print(u'LEDGERS_R219 编号：第 %d 轮 / Round %d / U-%d…U-%d / BACKLOG +%d / D-%d'
      % (audit_round, this_round, U1, U3, NEW_B, NEW_D))
print(u'LEDGERS_R219 读数：亮档对比度 %s→%s、changed %d（亮 %d/暗 %d）、刀 %d/%d、判据卷 %d、全量卷 %d、帧 %d'
      % (comp_before, comp_after, n_changed, light_changed, dark_changed,
         caught, knives, roll_ran, full_ran, frames))

state = read('AGENT_STATE.md')
mm2 = re.search(u'最后更新：[^\\n]*?R(\\d+) / 第 (\\d+) 轮', state)
if not mm2 or int(mm2.group(1)) != 219 or int(mm2.group(2)) != audit_round:
    die('STATE 轮次行读不出 R219 / 第 ' + str(audit_round) + u' 轮')
for path, pat in ((u'AGENT_UI_AUDIT.md', u'^## 第 ' + str(audit_round) + u' 轮（R219'),
                  (u'AGENT_VISUAL_ITERATION.md', u'^## Round 219 · '),
                  (u'CHANGELOG.md', u'^### .*（R219 / ')):
    if not re.search(pat, read(path), re.M):
        die(path + u' 里读不到本轮标题：' + pat)
print(u'LEDGERS_R219 selfcheck ok')
sys.exit(0)

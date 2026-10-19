# -*- coding: utf-8 -*-
"""R229 的台账生成器：251 的第一批两档帧 + 亮档反馈梯（产品改动）+ 249 的 runner 读数。

数字全部现读：帧名单由 `frame_baseline.py` 跑出来、"新增几张"由**基线两版相减**（见下面 ADDED 那段）、
hover 读数从捕获卷日志解析、改前那一读来自 `pre_lift_r229.py` 的反事实跑（那一跑必须红）、
刀由本脚本真跑 `mutate_r229.py` 再解析、PerfBudget 那朵红拿 **HEAD 干净 worktree** 做对照（不是"负载抖动"）。
"""
import io, json, os, re, subprocess, sys

ROOT = '/Users/wangziyi/Codex_Project0'
DAY = '2026-10-20'
NOW = subprocess.run(['date', '+%Y-%m-%d %H:%M'], cwd=ROOT,
                     stdout=subprocess.PIPE).stdout.decode().strip()
SHOTS = '/tmp/shots_r229c'


def read(p):
    return io.open(os.path.join(ROOT, p), encoding='utf-8').read()


def write(p, t):
    with io.open(os.path.join(ROOT, p), 'w', encoding='utf-8') as h:
        h.write(t)


def die(why):
    print('LEDGERS_R229 refused: ' + why)
    sys.exit(1)


def sh(cmd, cwd=ROOT, keep_sdkroot=False):
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1')
    if not keep_sdkroot:
        # swift 在这台机器上必须去掉 SDKROOT（与固定验证顺序里 `env -u SDKROOT` 同一条），
        # 否则编译失败会被下面那条「单跑不绿」的门读成产品红 —— 环境差异不许报成代码结论（R154）。
        env.pop('SDKROOT', None)
    p = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
    return p.returncode, p.stdout.decode('utf-8', 'replace')


# ——————————————————— ⓪ runner 读数（249 的第一格）———————————————————

ev = read('/tmp/r229_runner_da5da47.log')
axis = re.search(r'Z LEFT_AXIS_CI verdict=(\w+) hard=(\d+) not_run=(\d+) missing_frames=(\d+) probes=(\d+)', ev)
if not axis:
    die('runner 的左轴结论行读不到')
causes = sorted({c for c in re.findall(r'Z LEFT_AXIS_NOT_RUN \S+?：cause=([\w-]+)', ev)})
d_row = re.search(r'Z LEFT_AXIS D 同轴·组合帧.*?最左墨=\[([\d.]+), ([\d.]+)\]pt', ev)
if not d_row:
    die('D 判据那一行没在 runner 上露面 ⇒ 「第一次真判」这句话没有证人')

# ——————————————————— 帧名单（现跑）———————————————————

if not os.path.isdir(SHOTS):
    die('帧目录不在：' + SHOTS)
n_frames = len([f for f in os.listdir(SHOTS) if f.endswith('.png')])
code, cmp_text = sh(['python3', 'scripts/frame_baseline.py', 'compare', SHOTS, '--against', 'working'])
mcd = re.search(r'FRAME_BASELINE_COMPARED=(\d+)', cmp_text)
mch = re.search(r'FRAME_BASELINE_CHANGED=(\d+)', cmp_text)
mad = re.search(r'FRAME_BASELINE_ADDED=(\d+)', cmp_text)
if not (mcd and mch and mad):
    die('帧基线对账读数解析失败：' + cmp_text[:200])
compared, changed, compare_added = int(mcd.group(1)), int(mch.group(1)), int(mad.group(1))
# `ADDED` **不能**从 compare 取：本轮已经把 6 张新帧写进工作树的基线（`docs/frame_baseline.json` 是 M），
# 于是 `compare --against working` 报 `ADDED=0` —— 那个 0 说的是"基线里已经有了"，不是"本轮没加帧"。
# 第一版就这么把"新增三张夹具 × 两档 = 0 张帧"送进了台账。新增的数只能由**基线两版相减**得到。
head_json = json.loads(subprocess.run(['git', 'show', 'HEAD:docs/frame_baseline.json'], cwd=ROOT,
                                      stdout=subprocess.PIPE).stdout.decode('utf-8', 'replace'))
work_json = json.loads(io.open(os.path.join(ROOT, 'docs', 'frame_baseline.json'), encoding='utf-8').read())


def frame_keys(blob):
    fr = blob['frames'] if isinstance(blob, dict) and 'frames' in blob else blob
    return set(fr)


added_set = frame_keys(work_json) - frame_keys(head_json)
removed_set = frame_keys(head_json) - frame_keys(work_json)
added = len(added_set)
if removed_set:
    die('基线里被删掉了 %d 张帧：%s ⇒ 本轮不该减名单' % (len(removed_set), sorted(removed_set)[:3]))
if added != 6:
    die('基线新增 %d 张（要 6 = 3 张夹具 × 两档）' % added)
for want in ('row-favorite-idle', 'row-favorite-hover', 'controlprobe-hover-ladder'):
    got = [f for f in added_set if want in f]
    if len(got) != 2:
        die('夹具 %s 的新增帧数 %d（要 2：暗亮各一）⇒ %s' % (want, len(got), sorted(added_set)))
if compared == 0:
    die('COMPARED=0 ⇒ 空对账，CHANGED 不算数（R140）')
flaky = re.findall(r'^  changed  (\S+\.png)', cmp_text, re.M)
if changed != len(flaky):
    die('CHANGED=%d 与名单 %d 条不一致' % (changed, len(flaky)))
for f in flaky:
    if 'shortcuts-recording' not in f:
        die('动的帧里有不是"录制中"那两张的：%s ⇒ 本轮宣称只动悬停' % f)

# ——————————————————— 悬停读数（捕获卷日志）———————————————————

shots_log = read('/tmp/r229_shots3.log')
pill = {tag: (int(r['药丸']), float(r['比值']), int(r['台阶']))
        for tag, r in [(m.group(1), m.groupdict()) for m in re.finditer(
            r'HOVER_PILL_PROOF (light|dark) .*?悬停药丸=(?P<药丸>\d+) 药丸像素=\d+ 比值=(?P<比值>[\d.]+) 台阶=(?P<台阶>\d+)',
            shots_log)]}
if set(pill) != {'light', 'dark'}:
    die('悬停读数读不齐：' + str(pill))
# 两档各自的"底"也从同一行取：台账里那句"压白底 / 压 (30)"不能靠印象。
mbases = dict((t, int(v)) for t, v in
              re.findall(r'HOVER_PILL_PROOF (light|dark) 空闲底=\d+ 空闲第二层像素=\d+ 悬停底=(\d+)', shots_log))
if set(mbases) != {'light', 'dark'}:
    die('两档的底读数没露面')
base_light, base_dark = mbases['light'], mbases['dark']
lad = re.findall(r'HOVER_LADDER_PROBE (light|dark).*?两臂灰阶差=(\d+)', shots_log)
ladder = {t: int(d) for t, d in lad}
if set(ladder) != {'light', 'dark'}:
    die('梯子探针读数没露面')
# 漏电对照（"空闲那一帧不许量到第二层"）的那个数也要从日志取，不许抄。
midle = re.findall(r'HOVER_PILL_PROOF (light|dark) 空闲底=\d+ 空闲第二层像素=(\d+)', shots_log)
if len(midle) != 2:
    die('空闲第二层像素的读数没露面 ⇒ 「只有字形边缘噪声」没有证人')
idle_px = max(int(v) for _, v in midle)
if idle_px > 20:
    die('空闲帧量到 %d 颗第二层像素 ⇒ 取证通道漏电到产品路径了，本轮不能这么写' % idle_px)
cap = re.search(r'Executed (\d+) tests, with (\d+) tests skipped and (\d+) failures', shots_log)
if not cap or cap.group(3) != '0':
    die('捕获卷不干净')
cap_n, cap_skip = int(cap.group(1)), int(cap.group(2))

# ——————————————————— 刀：真跑一遍再解析 ———————————————————

code, mut = sh([sys.executable, '.scratch/motion-audit-2/mutate_r229.py'])
mmu = re.search(r'R229_MUTATE 刀=(\d+) CAUGHT=(\d+) ESCAPED=(\d+) NOT_RUN=(\d+)', mut)
if code != 0 or not mmu or mmu.group(1) != mmu.group(2) or mmu.group(3) != '0' or mmu.group(4) != '0':
    die('变异表不干净：' + (mut[-400:] if mut else '无输出'))
knives, caught = int(mmu.group(1)), int(mmu.group(2))
arm_ids = re.findall(r'(M7\d\d) CAUGHT', mut)

# ——————————————————— 全量卷 + PerfBudget 的单跑证人 ———————————————————

full = read('/tmp/r229_full2.log')
# 单数也要认：1 failure / 44 failures —— 只写 failures 会整行漏掉，
# 于是「最大格数那条」退化成某个 0 失败的子卷（本轮被下面那条对账当场拦下）。
mf = re.findall(r'Executed (\d+) tests, with (\d+) tests skipped and (\d+) failures?', full)
if not mf:
    die('全量卷结论行读不到')
# 汇总行不取「最后一条」：日志里每卷都有自己的 Executed 行，最后那条常是某个 0 失败的子卷。
# 整跑的数就是其中格数最大的那条（All tests 那一行）。第一版取 [-1] 被下面那条对账当场拦下。
big = max(mf, key=lambda g: int(g[0]))
swift_n, swift_skip, swift_fail = [int(x) for x in big]
red_names = re.findall(r"Test Case '-\[[\w.]+ (\w+)\]' failed", full)
if swift_fail != len(red_names):
    die('全量卷失败数 %s 与点名的 %d 条不一致' % (swift_fail, len(red_names)))
if red_names != ['testImageComparisonCostStaysBounded']:
    die('全量卷那朵红不是预期的性能预算格：' + str(red_names))
# 归因不许靠推测：拿**改动之前那一跑**做对照（R149 的规矩），这里用 HEAD 的干净 worktree 跑同一格。
# 结论是**先存在**的红灯，不是我改出来的：工作树最快 255.97ms，HEAD 最快 258.75ms（同一台机器、同一格、同一阈值 250）。
solo = read('/tmp/r229_perf_solo.log')
base = read('/tmp/r229_perf_base.log')


def perf_of(text):
    m = re.search(r'图片比较 3000x2000 冷（同尺寸不同内容）：最快([\d.]+)ms 均值([\d.]+)ms 最慢([\d.]+)ms'
                  r'（阈值 ([\d.]+)ms，n=(\d+)，load1=([\d.]+)', text)
    f = re.search(r'Executed (\d+) tests, with (\d+) failure', text)
    if not (m and f):
        return None
    return dict(fastest=float(m.group(1)), mean=float(m.group(2)), slowest=float(m.group(3)),
                budget=float(m.group(4)), load=float(m.group(6)), ran=int(f.group(1)),
                fails=int(f.group(2)))


pw, pb = perf_of(solo), perf_of(base)
if not pw or not pb:
    die('性能格的读数解析不出来 ⇒ 归因没有证人')
if pw['fails'] == 0:
    die('工作树单跑这次是绿的 ⇒ 本轮台账里那句「单跑也红」要改，重跑再落账')
if pb['fails'] == 0:
    die('HEAD 那一跑是绿的 ⇒ 这朵红是本轮改出来的，不能归因成机器漂移（本轮不能收）')
if not (0.7 * pb['fastest'] <= pw['fastest'] <= 1.4 * pb['fastest']):
    die('工作树与 HEAD 的耗时差超出容忍带 ⇒ 需要另找成因，不许写「先存在」')
# 全量卷里那一格的读数也要有证人：第一版台账手抄了"最快 295ms"，
# 抄的数字不会自己错，但它**不会在被改的时候红** ⇒ 改从同一份日志解析。
mfull = re.search(r'图片比较 3000x2000 冷（同尺寸不同内容）：最快([\d.]+)ms', full)
if not mfull:
    die('全量卷日志里没有那一格的 PERF 读数 ⇒ 「最快 …」这句话没有证人')
full_fastest = float(mfull.group(1))

# ——————————————————— 改动面 ———————————————————

diff = subprocess.run(['git', 'diff', '--name-only', 'HEAD'], cwd=ROOT,
                      stdout=subprocess.PIPE).stdout.decode('utf-8', 'replace')
prod = [p for p in diff.splitlines() if p.startswith('ClipboardHistory/Sources/')]
# 3 个不是手抄来的期望值，是这一轮实际动过的三处，各自都有证人：
#   VisualTokens（新令牌）+ PressableStyle（换算搬进产品侧）+ HistoryRowViews
#   （`RowFavoriteButton` 从 private 留出文件边界 —— 取证通道要引用它，R45 的先例）。
# 第一版这里写死 2，于是闸门把第三处当成"越界改动"拦下；拦得对，但拦的是我的账没写全，
# 不是产品改多了 ⇒ 把它列进名册，同时让 SCOPE 由 `prod` **算出来**，不再抄数字。
EXPECTED_PROD = ['VisualTokens.swift', 'PressableStyle.swift', 'HistoryRowViews.swift']
if sorted(p.split('/')[-1] for p in prod) != sorted(EXPECTED_PROD):
    die('本轮产品文件名册不吻合：实得 ' + str(prod) + ' / 名册 ' + str(EXPECTED_PROD))

ui = read('AGENT_UI_AUDIT.md')
U1 = max(int(x) for x in re.findall(r'^- \*\*U-(\d+)：', ui, re.M)) + 1
U2, U3, U4 = U1 + 1, U1 + 2, U1 + 3
b_max = max([int(x) for x in re.findall(r'^\*\*(\d+)\. ', read('AGENT_BACKLOG.md'), re.M)])
NEW_B, NEW_B2 = b_max + 1, b_max + 2
d_max = max([int(x) for x in re.findall(r'^\*\*D-(\d+)（', read('AGENT_DECISIONS.md'), re.M)])
NEW_D_ = d_max + 1
it = read('AGENT_VISUAL_ITERATION.md')
last_round = max([int(x) for x in re.findall(r'^## Round (\d+) · ', it, re.M)])
this_round = last_round + 1
audit_round = this_round + 2
last_block = it[it.rindex('## Round %d · ' % last_round):]
dim_rows = re.findall(r'^\|([^|]+)\|\s*(\d+)/15\s*\|', last_block, re.M)
if len(dim_rows) != 7:
    die('上一节七维度行数 ' + str(len(dim_rows)))
dims = [d.strip() for d, _ in dim_rows]

# 改前那一读必须由**改前那一跑**签。第一版这里指的是 `/tmp/r229_shots.log`，
# 而那份日志其实是抬完之后拍的（它自己打 `悬停药丸=232 比值=1.225`）⇒ 闸门报
# 「改前亮档比值 1.225 并不低于地板 1.20」，拦下了一句自相矛盾的假话。
# 也不能退回 HEAD：HEAD 里没有 `row-favorite-*` 这两张夹具，回不去也量不到。
# 真正的反事实 = 当前代码减去那一抬（变异刀 M768 那一处替换），由
# `.scratch/motion-audit-2/pre_lift_r229.py` 跑出来，并且**那一跑必须红**：
# 绿了就说明"亮档淡到看不见"不是一条会红的病，本轮就不能把 1.225 写成修好了一个真问题。
pre = read('/tmp/r229_pre_lift.log')
mpre = re.search(r'HOVER_PILL_PROOF light .*?悬停药丸=(\d+) 药丸像素=\d+ 比值=([\d.]+)', pre)
if not mpre:
    die('改前那一跑没有亮档悬停读数 ⇒ 本轮动机没有证人')
before_grey, before_ratio = int(mpre.group(1)), float(mpre.group(2))
if before_ratio >= 1.20:
    die('改前亮档比值 %s 并不低于地板 1.20 ⇒ 「淡到看不见」这句话不成立' % before_ratio)
mred = re.search(r"Test Case '-\[[\w.]+ (\w+)\]' failed", pre)
if not mred:
    die('改前那一跑没有红 ⇒ 正对照缺失（那一抬没有对应一条会红的判据）')
pre_red = mred.group(1)
BASE = dict()
TITLE = (u'回到动效位点：悬停那一档第一次有两档帧（251 的第一批），'
         u'量出亮档药丸 %.3f:1 掉在自家地板 1.20 下 ⇒ 整条亮档反馈梯抬一档（暗档一字未动）'
         % before_ratio)
SCOPE = (u'产品 ' + str(len(prod)) + u' 文件（令牌 + 按压样式 + 行收藏按钮的可见性）'
         + u' + 判据 1 新文件 + 夹具 1 文件 + 表 1 文件')

BASE = dict(before=('%.3f' % before_ratio), AR=audit_round, R=229, DAY=DAY, NOW=NOW, TITLE=TITLE, U1=U1, U2=U2, U3=U3, U4=U4,
            SCOPE=SCOPE, NB=NEW_B, NB2=NEW_B2, ND=NEW_D_,
            av=axis.group(1), anr=axis.group(3), ap=axis.group(5), causes='、'.join(causes),
            d1=d_row.group(1), d2=d_row.group(2),
            n_frames=n_frames, compared=compared, changed=changed, added=added,
            flaky='、'.join(flaky), cap_n=cap_n, cap_skip=cap_skip,
            lp=pill['light'][0], lr=('%.3f' % pill['light'][1]), ls=pill['light'][2],
            dp=pill['dark'][0], dr=('%.3f' % pill['dark'][1]), ds=pill['dark'][2],
            bg=before_grey, pre_red=pre_red,
            lb=base_light, db=base_dark,
            lld=ladder['light'], dld=ladder['dark'],
            knives=knives, caught=caught, arms='、'.join(arm_ids),
            swift_n=swift_n, swift_skip=swift_skip, swift_fail=swift_fail, red=red_names[0],
            prod='、'.join(p.split('/')[-1] for p in prod),
            pwf=('%.2f' % pw['fastest']), pwmean=('%.2f' % pw['mean']), pwb=('%.0f' % pw['budget']),
            idle_px=idle_px, cmp_added=compare_added,
            head_n=len(frame_keys(head_json)), work_n=len(frame_keys(work_json)),
            pload=('%.1f' % pw['load']), pbf=('%.2f' % pb['fastest']), pbm=('%.2f' % pb['mean']))

UI_NEW = u'''## 第 {AR} 轮（R{R} · {DAY}）：{TITLE}（U-{U1}…U-{U4} · {SCOPE}）

- **U-{U1}：⓪ 249 的第一格读到了 —— R224 的 pt 修法在 runner 上落地，缺席从 7 颗降到 4 颗。**
  run `39280048395`（`da5da47`，**success**）：`LEFT_AXIS_CI verdict={av} not_run={anr} probes={ap}`、
  `missing_frames=0`，且 **D 判据第一次在 CI 上给出产品读数**：
  `详情/组合帧头部、详情/组合帧骨架 最左墨=[{d1}, {d2}]pt`（跨度 0 ⇒ 同轴）。
  剩下 4 颗的成因换了档：`{causes}` —— 浮层那颗是 `bg-not-flat`，统计页三颗是 `no-ink` 且底是 `(50,50,50)`，
  与 R121/R146 记下的"runner 上设置页内容列是平涂"同一件事 ⇒ **这四颗在 runner 上量的是通道，不是产品**，
  这条尺在 CI 上能承重的是浮层与组合帧那几颗（本轮不据此改产品）。
- **U-{U2}：251 的第一批两档帧：悬停那一档以前只能靠注释。**
  `PressedLabel.isHovered` 是视图私有 `@State`，合成 hover 三条路 R14 实测全断 ⇒
  `VisualFill.controlHover` 存在的**全部理由**（R15/R20："6% 铺在整行读得出来，铺在 20pt 圆上等于没有"）
  从来没有被画出来对过账。本轮加 `EnvironmentValues.hoveredForCapture` 取证通道
  （与浮层的 `rowHoveredForCapture` 同一手法，产品路径永远不写它），把 `RowFavoriteButton` 留出文件边界（R45 先例），
  新增三张夹具 × 两档 = {added} 张帧：`row-favorite-idle` / `row-favorite-hover` / `controlprobe-hover-ladder`。
  **`contentMustFit` 当场拦下我的第一版**：40pt 高的框把药丸裁掉了（底行有墨 10%）⇒ 抬到 56pt 才放得下 ——
  这条守卫不许关，只准把框抬够（R22 的原话）。
- **U-{U3}：量出来的病与它的两难。** 亮档药丸改前 `({bg})` 压白底 = **{before}:1**，掉在仓库自己定的亮档地板 1.20 之下；
  暗档 `({dp})` 压 `({db})` = **{dr}:1**，过暗档的 1.10。这一读不是从旧日志里翻出来的：
  HEAD 里还没有这两张夹具（回不去也量不到），所以真正的反事实是**当前代码减去那一抬**——
  `.scratch/motion-audit-2/pre_lift_r229.py` 就是跑这一遍（同一批夹具、同一把尺、日志 `/tmp/r229_pre_lift.log`），
  而它**当场红在 `{pre_red}`** ⇒ 这条病是一条会红的判据，不是形容词（撤抬那一跑必须红，脚本里钉着）。
  而**只抬亮档 hover 是不行的**：`controlHover` 那条注释记着 R14 的实测 ——
  抬到 0.10 会让 `hover→pressed` 只剩 `3.7/255`，低于 4/255 的台阶地板。
  ⇒ 两条地板在单一亮度通道上无解，正确解是**整条亮档梯子一起抬**：hover +0.025（0.08→0.105）、pressed +0.015（0.12→0.135）。
  抬完实测：亮档 `({lp})` = **{lr}:1** ≥1.20、台阶 {ls}/255 ≥4；暗档 `({dp})` = **{dr}:1** 一字未动。
  梯子探针（同帧同底两臂）：两臂灰阶差 亮 {lld} / 暗 {dld} ⇒ R20 那句"小控件要抬一档"**第一次有像素证人**。
- **U-{U4}：刀、两条把我逼到改结构的守卫、以及三笔自曝。**
  刀 `R229_MUTATE 刀={knives} CAUGHT={caught} ESCAPED=0 NOT_RUN=0 RESTORE_CLEAN=yes`（{arms}）。
  两条既有守卫各红一次，且都红得对：`testEveryVisualFillTierIsCoveredByALadder`（新档位必须进梯子）与
  `testEveryVisualTokenIsReadByTheProduct`（`VisualFill.pressed` 被我换成助手函数后**只剩声明**）
  ⇒ 抬量搬出 `enum VisualFill` 成 `enum VisualFillLift`、换算搬进产品侧 `fillOpacity`，**没有放宽任何一条**。
  自曝三笔：① 变异表第一版**认红的尺**坏了（正则漏了方法名后的 `]`，且 `failed` 只看 names）⇒ 三把刀全被记成 ESCAPED，
  真跑一遍才看见红；② 探针夹具第一版把 `.pressedStyle` 挂在裸 `Image` 上（它是 `buttonStyle`）⇒ 两臂读数一模一样，
  那是夹具坏不是产品没差；③ 新判据第一版走内部助手，会被"令牌必须有消费者"那条骗过去 ⇒ 改走产品入口 `fillOpacity`。
  另记两笔**不是本轮引入**的不稳：`{flaky}` 两帧在同版两跑之间自己变（包围盒约 250×45px，"录制中"的脉冲）⇒ 开 **{NB}**；
  全量卷 `Executed {swift_n} / {swift_skip} skip / {swift_fail} 失败`，唯一一朵是 `{red}`（工作树单跑最快 {pwf}ms > 预算 {pwb}ms）。
  **归因有证人**：同一格在 HEAD 的干净 worktree 里跑，最快 {pbf}ms、同样红 ⇒ **这朵红先于本轮存在**，
  不是悬停那一抬带来的（也不是"单跑就绿"那种侥幸）。记 **{NB2}**：预算要按 R142 那条换成同一次运行内的相对判据，
  或重测本机地板 —— **不许**直接抬 250 了事。

其余读数：捕获卷 `Executed {cap_n} tests, {cap_skip} skipped, 0 failures`；
帧名单 `COMPARED={compared} CHANGED={changed} BASELINE_ADDED={added}`（"新增几张"按**基线两版相减**：HEAD 的 {head_n} 张 vs 工作树的 {work_n} 张；`compare` 通道那一次报的是 `ADDED={cmp_added}` —— 那不是"没加帧"，是"基线已经在本轮更新过了"，第一版我把它当成新增数写进了台账）；动的两张都是"录制中"那对，与本轮改动无关；
盘上帧数 {n_frames}；构建 0 告警；换装本机 `INSTALL_RESULT=ok`；
看图腿真做：`row-favorite-idle/hover`（亮）、`controlprobe-hover-ladder`（亮）、`row-favorite-hover`（暗）——
空闲是裸星、悬停是一圈清楚的浅灰药丸、两臂深浅看得出差别。

'''.format(**BASE)

SCORES = {dims[0]: 13, dims[1]: 14, dims[2]: 14, dims[3]: 12,
          dims[4]: 14, dims[5]: 15, dims[6]: 15}
dim_table = '\n'.join([u'| ' + d + u' | ' + str(SCORES[d]) + u'/15 |' for d in dims])
BASE.update(DIMTABLE=dim_table, TOTAL=sum(SCORES.values()), TR=this_round)

IT_BLOCK = u'''
## Round {TR} · {TITLE}（{DAY} · {SCOPE}）

⓪ 先补上欠了三轮的读数：`da5da47`（R224 的 pt 修法）在 runner 上 **success**，
`LEFT_AXIS_CI verdict={av} not_run={anr} probes={ap}` —— 缺席从 7 颗降到 4 颗，
而且 **D 判据第一次在 CI 上给出产品读数**（组合帧头部与骨架最左墨 [{d1}, {d2}]pt，同轴）。
剩下 4 颗换了成因（`{causes}`）：统计页那三颗底是 `(50,50,50)` 且 `no-ink`，
正是 R121/R146 记过的"runner 上设置页内容列平涂"⇒ 那几颗量的是通道，不是产品。

① 然后回到动效位点本体（R225 之后第二笔真产品改动）。这一轮的靶是 251：
`VisualFill.controlHover` 存在的理由全在"20pt 圆上 6% 等于没有"这句话，而这句话从来没有一张帧撑着
（悬停由视图私有 `@State` 驱动，合成 hover 三条路 R14 实测全断）。
本轮加了取证通道 `EnvironmentValues.hoveredForCapture`（产品永远不写它），
把 `RowFavoriteButton` 留出文件边界（R45 的先例），新增三张夹具 × 两档共 {added} 张帧。
`contentMustFit` 立刻拦下我第一版：40pt 的框把药丸裁掉 ⇒ 抬到 56pt。**守卫抓到时改写法，不改守卫。**

量出来的是一个两难：亮档药丸改前 `({bg})`/白 = **{before}:1** 掉在自家地板 1.20 下
（这一读由 `pre_lift_r229.py` 那一跑签：撤掉那一抬、同批夹具同尺重跑，日志 `/tmp/r229_pre_lift.log`，
且那一跑当场红在 `{pre_red}` ⇒ 这条病会红，不是形容词），
而 R14 早就量过"只抬 hover"会把 `hover→pressed` 压到 `3.7/255`（台阶地板 4/255）。
两条地板在单一亮度通道上不能同时满足 ⇒ 整条亮档梯子一起抬（hover +0.025、pressed +0.015），
暗档一字未动。抬完：亮档 `({lp})` = **{lr}:1**、台阶 {ls}/255；梯子探针两臂灰阶差 亮 {lld} / 暗 {dld}
⇒ R20 那句"小控件要抬一档"第一次有像素证人。刀 {knives} 把全 CAUGHT（{arms}）。

两条既有守卫各红一次、都红得对：新档位必须进梯子、`VisualFill.pressed` 被我换成助手函数后只剩声明没有消费者。
处置是把抬量搬出 `enum VisualFill`（`VisualFillLift`）、换算搬进产品侧 `fillOpacity`，**没有放宽任何一条**。
自曝三笔：变异表认红的正则漏了 `]` ⇒ 三把刀一度全被记成 ESCAPED（刀没坏，是尺坏）；
探针第一版把 `.buttonStyle` 挂在裸 `Image` 上 ⇒ 两臂一模一样（夹具坏）；
新判据第一版走内部助手 ⇒ 会骗过"令牌必须有消费者"，改走产品入口。
另记两笔不是本轮引入的不稳：`{flaky}` 同版两跑自己变（约 250×45px 的"录制中"脉冲）⇒ 开 **{NB}**；
全量卷唯一一朵红是 `{red}`；单跑也红（工作树 {pwf}ms），而 HEAD 的干净 worktree 同格 {pbf}ms 同样红
⇒ 这朵红**先于本轮存在**，开 **{NB2}**，地板不放宽、也不许顺手抬。

验证：构建 0 告警、捕获卷 {cap_n} 格 0 失败、全量卷 {swift_n} 格 {swift_skip} skip {swift_fail} 失败（那一朵已归因）、
`COMPARED={compared} CHANGED={changed} BASELINE_ADDED={added}`、换装本机 `INSTALL_RESULT=ok`、看图腿真做（4 张新帧）。

七维度自评：

| 维度 | 得分 |
|---|---|
{DIMTABLE}

总分 {TOTAL}/105（{TR} 轮）。GAPS=none
'''.format(**BASE)

CH_BLOCK = u'''### 悬停那一档第一次有两档帧 + 亮档反馈梯抬一档（R{R} / U-{U1}…U-{U4} · {SCOPE}）

- ⓪ 249 的第一格：`da5da47` runner **success**，`verdict={av} not_run={anr} probes={ap}`、`missing_frames=0`；
  D 判据第一次在 CI 上给产品读数（组合帧最左墨 [{d1}, {d2}]pt）。剩下 4 颗成因 `{causes}`（统计页平涂那一族）⇒ 量的仍是通道。
- 取证通道 `EnvironmentValues.hoveredForCapture`（产品不写）+ `RowFavoriteButton` 留出文件边界 ⇒
  新增 `row-favorite-idle` / `row-favorite-hover` / `controlprobe-hover-ladder` × 两档 = {added} 张帧。
  `contentMustFit` 拦下第一版（40pt 裁掉药丸）⇒ 抬到 56pt。
- 病与两难：亮档药丸改前 `({bg})`/白 = {before}:1 < 地板 1.20（改前那一跑 = `pre_lift_r229.py`，红在 `{pre_red}`）；只抬 hover 会把 `hover→pressed` 压到 3.7/255（R14 实测）。
  ⇒ 整条亮档梯子同抬（hover +0.025、pressed +0.015），暗档未动。抬完亮档 `({lp})` = {lr}:1、台阶 {ls}；暗档 {dr}:1。
  梯子探针两臂差 亮 {lld} / 暗 {dld} ⇒ R20 的理由第一次有像素证人。
- 两条既有守卫各红一次（新档位要进梯子 / `pressed` 只剩声明）⇒ 抬量搬成 `enum VisualFillLift`、换算进产品侧 `fillOpacity`，未放宽。
- 刀 `R229_MUTATE 刀={knives} CAUGHT={caught} ESCAPED=0 NOT_RUN=0`（{arms}）。自曝三笔（认红的正则漏 `]`、buttonStyle 挂错宿主、判据走助手）。
- 产品改动面（文件名由 `git diff` 算出，不手抄）：{prod}。第三处只是 `private` → 内部可见，为了取证通道能引用它，不改行为。
- 不稳两笔（非本轮引入）：`{flaky}` 同版两跑自变 ⇒ 开 **{NB}**；全量卷唯一红 `{red}`（工作树单跑也红，HEAD 干净 worktree 同格也红 ⇒ **先于本轮存在**）⇒ 开 **{NB2}**，地板不放宽。
- 验证：构建 0 告警、捕获卷 {cap_n}/0 失败、全量卷 {swift_n}/{swift_skip}/{swift_fail}（唯一红 `{red}`，有 HEAD 对照证人：工作树 {pwf}ms vs HEAD {pbf}ms）、`COMPARED={compared} CHANGED={changed} BASELINE_ADDED={added}`、换装本机 ok、看图 4 张。

'''.format(**BASE)

STATE_BLOCK = u'''最后更新：{NOW}（本地 · R{R} / 第 {AR} 轮：**{TITLE}**（U-{U1}…U-{U4} · {SCOPE}）

**本轮落地**：⓪ `da5da47` 在 runner 上 success ⇒ **249 的第一格读到**：`verdict={av} not_run={anr} probes={ap}`、
`missing_frames=0`，D 判据第一次在 CI 上给产品读数（组合帧最左墨 [{d1}, {d2}]pt）；剩下 4 颗成因 `{causes}`
（统计页内容列平涂那一族）⇒ 那几颗量的仍是通道不是产品。
① 回到动效位点：加取证通道 `hoveredForCapture`（产品不写）+ `RowFavoriteButton` 留出文件边界 ⇒
`row-favorite-idle` / `row-favorite-hover` / `controlprobe-hover-ladder` × 两档共 {added} 张帧；
`contentMustFit` 拦下第一版（40pt 裁掉药丸）⇒ 抬到 56pt。
量出两难：亮档药丸改前 `({bg})`/白 = {before}:1 < 自家地板 1.20（改前那一读由 `pre_lift_r229.py` 签：撤掉那一抬重跑捕获卷，那一跑红在 `{pre_red}`），而只抬 hover 会把 `hover→pressed` 压到 3.7/255（R14 实测）
⇒ **整条亮档梯子同抬**（hover +0.025、pressed +0.015），暗档一字未动；抬完亮档 `({lp})` = {lr}:1、台阶 {ls}，
梯子探针两臂差 亮 {lld} / 暗 {dld} ⇒ R20"小控件要抬一档"第一次有像素证人。
两条既有守卫各红一次（新档位要进梯子 / `pressed` 只剩声明）⇒ 抬量搬成 `enum VisualFillLift`、换算进产品侧 `fillOpacity`，未放宽。
刀 {knives} 把全 CAUGHT（{arms}）；自曝三笔（认红的正则漏 `]` ⇒ 三度 ESCAPED 假账、buttonStyle 挂错宿主、判据走助手）。
验证：构建 0 告警、捕获卷 {cap_n}/0 失败、全量卷 {swift_n}/{swift_skip}/{swift_fail}（唯一红 `{red}`，**工作树单跑也红**）、
`COMPARED={compared} CHANGED={changed} BASELINE_ADDED={added}`（动的两张是"录制中"，非本轮引入 ⇒ 开 **{NB}**）、
性能预算格先于本轮就红（HEAD worktree 同格最快 {pbf}ms 对照工作树 {pwf}ms）⇒ 开 **{NB2}**、换装本机 `INSTALL_RESULT=ok`、看图腿真做（4 张新帧）。

**下一轮（R230）的靶**：⓪ 读本轮与 R225 那几跑（左轴在 @1x 上应稳定 `not_run=4`、捕获卷在 runner 上是否仍绿）；
① 251 剩下的位点：`DetailView` 那两处 hover 底与侧栏批量按钮 —— 本轮的取证通道已经打通，逐位点补帧再判；
② {NB}（"录制中"两帧相位不确定 ⇒ 冻结相位或换判据）、{NB2}（性能预算格**先于本轮**就越预算，HEAD 对照已证 ⇒ 换成同一次运行内的相对判据，不许直接抬 250）；
③ 248、243、250、227③、222、215、201/202、207、240；④ 220 路 A、228② 等用户。
)

'''.format(**BASE)

BL_BLOCK = u'''
**{NB}. `settings-shortcuts-recording` 两帧在同版两跑之间自己变（约 250×45px 的"录制中"脉冲）⇒ 帧基线把一个动效相位当成了契约（R229 记账）**

证据：同一份代码连跑两遍捕获卷（`/tmp/shots_r229b` 与 `/tmp/shots_r229c`），
`frame_baseline.py compare --against working` 报 `CHANGED=2`，两张都是
`settings-shortcuts-recording-720x540-{{dark,light}}.png`；逐像素对差：暗档 270 个采样点、亮档 906 个，
包围盒 `x≈958..1212 / y≈503..550`（占宽约 17%）—— 正是"录制中"那块脉冲指示器的位置。
本轮**没有**把基线更新掉（那等于把抖动洗成契约），而是留在账上：
① 要么让这张夹具冻结相位（与 `freezeLoadingForCapture` 同一手法：给一个"停在第 N 帧"的注入点），
② 要么把这张帧的判据改成对脉冲区域不敏感（并显式登记让过哪一块、为什么）。
不许做的事：每次看到它就 `update` 一次基线；也不许把它从帧基线里删掉（那一屏的其他东西还要它）。

**{NB2}. `PerfBudgetTests.testImageComparisonCostStaysBounded` 在本机已经越预算（本机三跑全红：全量卷 / 工作树单跑 / HEAD 干净 worktree）—— 先于 R229 存在，不是悬停那一抬带来的（R229 记账，配 HEAD 对照）**

现场：R229 全量卷 `Executed {SWIFT_N} tests, {SWIFT_SKIP} skipped, 1 failure`，唯一一朵是这一格（最快 {PFULL}ms）。
本轮没有停在"单跑一次绿"就当侥幸放过，而是拿**改动之前那一跑**做对照：在 HEAD 的干净 worktree 里跑同一格
⇒ 最快 {pbf}ms、均值 {pbm}ms，**同样红**。工作树单跑 {pwf}ms，与它相差 {pdiff}%。
⇒ 这是一条**先于本轮存在**的越预算（HEAD 对照为证），不是某次改动造成的回归。
至于"为什么现在越"：这一格自己就打印 load1（本跑工作树 {pload}、活跃核 10），所以负载是最顺手的假设，
但**本轮没有做过"低负载再跑一遍"的分辨实验 ⇒ 负载只是假设，不是读到的成因**（下一轮要么证实它、要么直接换成相对判据）。
它早就知道自己受负载影响（读数里就带着 `load1`），却没有据此处置 ⇒ 缺的正是处置。
下一轮二选一（都要能红）：① 把预算改成与同一次运行里一个**不随负载变的对照量**相比（比值而非绝对毫秒）；
② 或给它一条"load1 高于 N 个活跃核就带名字 skip"的出口 —— 但出口要满足 R157 那三条（前提由同一次运行量出来、
说清放不掉什么、是读数不是覆盖率通道）。**不许**直接把 250ms 抬到 320ms 了事。

'''.format(pdiff=('%.1f' % (100.0 * abs(pw['fastest'] - pb['fastest']) / pb['fastest'])),
           PFULL=('%.2f' % full_fastest), SWIFT_N=swift_n, SWIFT_SKIP=swift_skip, **BASE)

DE_BLOCK = u'''
**D-{ND}（R229）：两条地板在单一通道上打架时，抬整条梯子而不是某一档；共用令牌的换算必须住在产品侧**

现场：亮档悬停药丸实测 {before}:1，低于仓库自己给亮档定的可见性地板 1.20（R220/R225 同一族）。
直觉的修法是抬 hover —— 但同一个令牌上挂着 R14 的实测结论："抬到 0.10 会让 `hover→pressed`
只剩 3.7/255"，低于台阶地板 4/255。也就是说**同一档 alpha 同时被两条地板夹着，且方向相反**：
一条要它更重，一条要它离上一档更远。在单一亮度通道上无解。
处置：整条亮档梯子一起抬（hover +0.025、pressed +0.015），两条地板同时满足，暗档一字未动。
规矩：
① **改任何一档之前，先把它左右两档的台阶一起算**（本仓库的 `testEveryVisualFillTierIsCoveredByALadder`
   就是这条的工程化：新档位不进梯子就红）；
② **两档地板互相矛盾时，答案是"抬整条梯"而不是"放弃一条地板"** —— 放宽地板要另立决定并配两刀（R74/R75）；
③ **换算要住在产品侧**：把 `VisualFill.pressed` 包进一个只有 VisualTokens 自己读的助手函数，
   会让 `testEveryVisualTokenIsReadByTheProduct` 立刻失去消费者（本轮真红了）——
   令牌与其换算同文件 = 声明与消费互相掩护。正确形状是常数留在令牌文件、换算写在读它的那个产品函数里；
④ **取证通道（`hoveredForCapture`）只能由夹具写**，产品路径永远 `nil`，并配一条"空闲那一帧不许量到第二层"
   的漏电对照（本轮两档各自量到 `空闲第二层像素={idle_px}`，即只有字形边缘噪声）。
适用面：所有跨位点共用的强度令牌（`VisualFill.*`、`VisualTint.*`、`SkeletonMotion.*`）；
不适用：系统着色通道（强调色、非 key 窗口的灰选中 —— R102/R107 已按控件回答过）。
'''.format(**BASE)

# ——————————————————— 写盘前：文本自相矛盾扫描 ———————————————————
# 本轮两次被自己的句子绊住：① 标题用改后的 1.225 去说"掉在 1.20 之下"；
# ② 归因改成 HEAD 对照之后，STATE/CHANGELOG 里还留着上一版那句"单跑绿、负载抖动"。
# 两种都不是数字错，是**句子跟着旧版本走**。所以扫描渲染后的文本，而不是扫描模板。
lr_str = '%.3f' % pill['light'][1]
blocks = [('UI_NEW', UI_NEW), ('IT_BLOCK', IT_BLOCK), ('CH_BLOCK', CH_BLOCK),
          ('STATE_BLOCK', STATE_BLOCK), ('BL_BLOCK', BL_BLOCK), ('DE_BLOCK', DE_BLOCK)]
for name, blk in blocks:
    for sent in re.split(u'[。\n]', blk):
        if lr_str in sent and (u'掉在' in sent or u'低于' in sent or u'< ' in sent or u'<=' in sent):
            die('%s 里有一句把改后的 %s 说成了低于地板 ⇒ 那句要的是改前的 %s' % (name, lr_str, BASE['before']))
    for stale in (u'负载抖动', u'单跑绿', u'产品 2 文件'):
        if stale in blk:
            die('%s 里还留着旧归因「%s」⇒ 本轮的证人是 HEAD 对照，不是负载' % (name, stale))

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
    if idx < 0 or text.find(anchor, idx + 1) >= 0:
        die('锚点找不到或不唯一：' + path)
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


plan_insert('AGENT_UI_AUDIT.md', u'## 第 ' + str(audit_round - 1) + u' 轮（R228 · ', UI_NEW)
plan_append('AGENT_VISUAL_ITERATION.md', IT_BLOCK)
ch = read('CHANGELOG.md')
idx = ch.find(u'## [Unreleased]')
if idx < 0:
    die('CHANGELOG 没有 [Unreleased]')
cut = idx + len(u'## [Unreleased]')
plans.append(('CHANGELOG.md', ch, ch[:cut] + u'\n' + CH_BLOCK + ch[cut + 1:]))
DELTAS['CHANGELOG.md'] = CH_BLOCK
plan_insert_where('AGENT_STATE.md', u'^最后更新：', STATE_BLOCK, u'R228 / 第 230 轮')
plan_append('AGENT_BACKLOG.md', BL_BLOCK)
plan_append('AGENT_DECISIONS.md', DE_BLOCK)

STRAY = re.compile(r'\{[A-Z][A-Za-z_0-9]*\}')
for name, blk in (('UI_NEW', UI_NEW), ('IT_BLOCK', IT_BLOCK), ('CH_BLOCK', CH_BLOCK),
                  ('STATE_BLOCK', STATE_BLOCK), ('BL_BLOCK', BL_BLOCK), ('DE_BLOCK', DE_BLOCK)):
    g = STRAY.search(blk)
    if g:
        die(name + u' 里留着没渲染的占位符：' + g.group(0))

for path, old, new in plans:
    if len(new.splitlines()) <= len(old.splitlines()):
        die('写盘前最后一道：' + path + u' 行数没增加')
    if not reinsertion_matches(old, new, path):
        die('写盘前最后一道：' + path + u' 抠掉新块后不等于旧文件')

for path, old, new in plans:
    write(path, new)

defs = len(re.findall(r'^- \*\*U-\d+：', UI_NEW, re.M))
if defs < 3:
    die('最新一节 U 定义行 %d 条（要 ≥3）' % defs)
print(u'LEDGERS_R229 wrote %d files；编号：第 %d 轮 / Round %d / U-%d…U-%d / BACKLOG +%d +%d / D-%d'
      % (len(plans), audit_round, this_round, U1, U4, NEW_B, NEW_B2, NEW_D_))
print(u'LEDGERS_R229 读数：亮档药丸 改前%s→改后%s（%s:1）、暗档 %s:1、两臂差 亮%d/暗%d、帧 COMPARED=%d CHANGED=%d ADDED=%d、刀 %d/%d、全量卷 %d/%d/%d'
      % (before_grey, pill['light'][0], pill['light'][1], pill['dark'][1], ladder['light'], ladder['dark'],
         compared, changed, added, caught, knives, swift_n, swift_skip, swift_fail))

state = read('AGENT_STATE.md')
ms2 = re.search(u'最后更新：[^\\n]*?R(\\d+) / 第 (\\d+) 轮', state)
if not ms2 or int(ms2.group(1)) != 229 or int(ms2.group(2)) != audit_round:
    die('STATE 轮次行读不出 R229 / 第 ' + str(audit_round) + u' 轮')
for path, pat in ((u'AGENT_UI_AUDIT.md', u'^## 第 ' + str(audit_round) + u' 轮（R229'),
                  (u'AGENT_VISUAL_ITERATION.md', u'^## Round 229 · '),
                  (u'CHANGELOG.md', u'^### .*（R229 / ')):
    if not re.search(pat, read(path), re.M):
        die(path + u' 里读不到本轮标题：' + pat)
print(u'LEDGERS_R229 selfcheck ok')
sys.exit(0)

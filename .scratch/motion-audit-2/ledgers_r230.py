# -*- coding: utf-8 -*-
"""R230 的台账生成器：251 的第二批 —— 两处"不走样式表"的直读悬停位点搬进同一条换算。

数字全部现读：帧名单由 `frame_baseline.py` 跑出来、"新增几张"由**基线两版相减**、
两档悬停读数从本轮捕获卷日志解析、**改前那一读**从 `pre_read_r230.py` 的两个证人目录解析
（玻璃圆 1.175 BELOW_FLOOR、段按钮选中段 GHOST 233→228），刀由本脚本真跑 `mutate_r230.py` 再解析，
名册读数 `HOVER_TOKEN_ROSTER` 从**全量卷**日志里取（不是从上一轮的过滤卷里抄）。
"""
import io, json, os, re, subprocess, sys

ROOT = '/Users/wangziyi/Codex_Project0'
DAY = '2026-10-20'
NOW = subprocess.run(['date', '+%Y-%m-%d %H:%M'], cwd=ROOT,
                     stdout=subprocess.PIPE).stdout.decode().strip()
SHOTS = '/tmp/shots_r230d'
SHOTS_LOG = '/tmp/r230_shots4.log'
PRE_LOG = '/tmp/r230_pre_read.log'
FULL_LOG = '/tmp/r230_full.log'
INSTALL_LOG = '/tmp/r230_install.log'


def read(p):
    return io.open(os.path.join(ROOT, p), encoding='utf-8').read() \
        if not p.startswith('/') else io.open(p, encoding='utf-8').read()


def write(p, t):
    with io.open(os.path.join(ROOT, p) if not p.startswith('/') else p, 'w', encoding='utf-8') as h:
        h.write(t)


def die(why):
    print('LEDGERS_R230 refused: ' + why)
    sys.exit(1)


def sh(cmd, cwd=ROOT, keep_sdkroot=False):
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1')
    if not keep_sdkroot:
        env.pop('SDKROOT', None)
    p = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
    return p.returncode, p.stdout.decode('utf-8', 'replace')


# ——————————————————— 帧名单（现跑，并且**只登记新增**）———————————————————

if not os.path.isdir(SHOTS):
    die('帧目录不在：' + SHOTS + ' ⇒ 看图腿与帧对账都没有对象（空对账，R140）')
n_frames = len([f for f in os.listdir(SHOTS) if f.endswith('.png')])
code, cmp_text = sh(['python3', 'scripts/frame_baseline.py', 'compare', SHOTS, '--against', 'working'])
mcd = re.search(r'FRAME_BASELINE_COMPARED=(\d+)', cmp_text)
mch = re.search(r'FRAME_BASELINE_CHANGED=(\d+)', cmp_text)
mad = re.search(r'FRAME_BASELINE_ADDED=(\d+)', cmp_text)
if not (mcd and mch and mad):
    die('帧基线对账读数解析失败：' + cmp_text[:200])
compared, changed, compare_added = int(mcd.group(1)), int(mch.group(1)), int(mad.group(1))
if compared == 0:
    die('COMPARED=0 ⇒ 空对账，CHANGED 不算数（R140）')
if changed != 0:
    flaky = re.findall(r'^  changed  (\S+\.png)', cmp_text, re.M)
    die('CHANGED=%d（%s）⇒ 本轮不打算把任何旧帧的像素洗进基线；'
        '若是"录制中"那对自变（254），重跑一遍捕获卷拿稳定值再落账，别 update' % (changed, '、'.join(flaky)))

head_json = json.loads(subprocess.run(['git', 'show', 'HEAD:docs/frame_baseline.json'], cwd=ROOT,
                                      stdout=subprocess.PIPE).stdout.decode('utf-8', 'replace'))


def frame_keys(blob):
    return set(blob['frames'] if isinstance(blob, dict) and 'frames' in blob else blob)


head_frames = head_json['frames'] if 'frames' in head_json else head_json
# `ADDED` **不能**从 update 之后的 compare 取（那是"基线里已经有了"，不是"本轮没加帧"）—— R229 的坑，本轮照防。
code, upd = sh(['python3', 'scripts/frame_baseline.py', 'update', SHOTS])
if code != 0:
    die('frame_baseline update 失败：' + upd[-300:])
work_json = json.loads(read('docs/frame_baseline.json'))
work_frames = work_json['frames'] if 'frames' in work_json else work_json
added_set = frame_keys(work_json) - frame_keys(head_json)
removed_set = frame_keys(head_json) - frame_keys(work_json)
added = len(added_set)
if removed_set:
    die('基线里被删掉了 %d 张帧：%s ⇒ 本轮不该减名单' % (len(removed_set), sorted(removed_set)[:3]))
# 旧帧的**值**一个都不许动：本轮的像素改动只在"以前根本没拍过"的那几张里。
moved = [k for k in frame_keys(head_json) & frame_keys(work_json)
         if head_frames[k] != work_frames[k]]
if moved:
    die('update 改动了 %d 张旧帧的哈希：%s ⇒ 与 CHANGED=0 自相矛盾，先查是谁写的' % (len(moved), moved[:3]))
if added != 6:
    die('基线新增 %d 张（要 6 = 3 张夹具 × 两档）' % added)
for want in ('segmented-filter-idle', 'segmented-filter-hover', 'glass-pill-hover'):
    got = [f for f in added_set if want in f]
    if len(got) != 2:
        die('夹具 %s 的新增帧数 %d（要 2：暗亮各一）⇒ %s' % (want, len(got), sorted(added_set)))

# ——————————————————— 两档悬停读数（本轮捕获卷日志）———————————————————

if not os.path.isfile(SHOTS_LOG):
    die('捕获卷日志不在：' + SHOTS_LOG)
shots_log = read(SHOTS_LOG)
cap = re.search(r'Executed (\d+) tests, with (\d+) tests skipped and (\d+) failures', shots_log)
if not cap or cap.group(3) != '0':
    die('捕获卷不干净或结论行读不到：' + (cap.group(0) if cap else '无'))
cap_n, cap_skip = int(cap.group(1)), int(cap.group(2))

DR = r'HOVER_DIRECT_READ_PROOF (light|dark) 段按钮 空闲底=(\d+) 悬停=(\d+) 比值=([\d.]+) 像素=(\d+) ' \
     r'选中段 空闲=(\d+) 悬停=(\d+) \| 玻璃圆 空闲底=(\d+) 悬停=(\d+) 比值=([\d.]+) 像素=(\d+) 下界='
direct = {}
for m in re.finditer(DR, shots_log):
    t = m.group(1)
    direct[t] = dict(seg_idle=int(m.group(2)), seg_hov=int(m.group(3)), seg_ratio=float(m.group(4)),
                     seg_px=int(m.group(5)), sel_idle=int(m.group(6)), sel_hov=int(m.group(7)),
                     gl_idle=int(m.group(8)), gl_hov=int(m.group(9)), gl_ratio=float(m.group(10)),
                     gl_px=int(m.group(11)))
if set(direct) != {'light', 'dark'}:
    die('两档的直接读数结论行没露面 ⇒ 新判据这次没打印')
for tag, mn in (('light', 1.20), ('dark', 1.10)):
    d = direct[tag]
    if not (d['seg_ratio'] >= mn and d['gl_ratio'] >= mn):
        die('%s 档有位点低于地板 %s：段 %.3f / 玻璃 %.3f ⇒ 本轮不能写"都过线"' % (tag, mn, d['seg_ratio'], d['gl_ratio']))
    if d['sel_hov'] != d['sel_idle']:
        die('%s 档选中段在点亮帧里从 %d 变成 %d ⇒ 幽灵层又回来了（`level == 0` 那条出口失效）' % (tag, d['sel_idle'], d['sel_hov']))

# 共用路径那两个数（R229 修好的行收藏药丸）本轮**不该动**：动了就说明我改换算时碰坏了旧位点。
PL = r'HOVER_PILL_PROOF (light|dark) .*?悬停药丸=(\d+) 药丸像素=\d+ 比值=([\d.]+) 台阶=(\d+)'
pill = {m.group(1): (int(m.group(2)), float(m.group(3)), int(m.group(4))) for m in re.finditer(PL, shots_log)}
if set(pill) != {'light', 'dark'}:
    die('R229 那条药丸读数本轮没露面 ⇒ 「旧位点没被碰坏」这句话没有证人')

# ——————————————————— 改前那一读（两个证人目录，由 pre_read_r230.py 签）———————————————————

if not os.path.isfile(PRE_LOG):
    die('改前证人日志不在：' + PRE_LOG + ' ⇒ 本轮动机没有读数（先跑 pre_read_r230.py）')
pre = read(PRE_LOG)
mgl = re.search(r'^PRE_READ 玻璃圆\S* (light|dark) 空闲=(\d+) 悬停=(\d+) 比值=([\d.]+) 像素=(\d+) '
                r'地板=([\d.]+) ⇒ (\w+)', pre, re.M)
if not mgl or mgl.group(1) != 'light' or mgl.group(7) != 'BELOW_FLOOR':
    die('玻璃圆改前那一读不是 BELOW_FLOOR ⇒ 「自绘层比共用路径弱」这句话没有证人')
pre_gl_grey, pre_gl_ratio = int(mgl.group(3)), float(mgl.group(4))
mghost = re.search(r'^PRE_READ 段按钮\S* 选中段 (light|dark) 空闲=(\d+) 悬停=(\d+) 比值=([\d.]+) .*?⇒ (\w+)', pre, re.M)
if not mghost or mghost.group(1) != 'light' or mghost.group(5) != 'GHOST':
    die('段按钮选中段改前那一读不是 GHOST ⇒ 「R229 那一抬带着洞上线」这句话没有证人')
pre_sel_idle, pre_sel_hov = int(mghost.group(2)), int(mghost.group(3))
mclean = re.search(r'^PRE_READ 段按钮\S* 选中段 dark 空闲=(\d+) 悬停=(\d+) .*?⇒ (\w+)', pre, re.M)
if not mclean or mclean.group(3) != 'CLEAN' or mclean.group(1) != mclean.group(2):
    die('暗档选中段那一格不是 CLEAN ⇒ 「只有亮档被抬出一层灰」这个两态对照不成立（少了一条腿）')
pre_sel_dark = int(mclean.group(1))

# ——————————————————— 刀：真跑一遍再解析 ———————————————————

code, mut = sh([sys.executable, '.scratch/motion-audit-2/mutate_r230.py'])
mmu = re.search(r'R230_MUTATE 刀=(\d+) CAUGHT=(\d+) ESCAPED=(\d+) NOT_RUN=(\d+)', mut)
if code != 0 or not mmu or mmu.group(1) != mmu.group(2) or mmu.group(3) != '0' or mmu.group(4) != '0':
    die('变异表不干净：' + (mut[-500:] if mut else '无输出'))
if 'RESTORE_CLEAN=yes' not in mut:
    die('变异表没打 RESTORE_CLEAN=yes ⇒ 还原没自证，本轮不出表')
knives, caught = int(mmu.group(1)), int(mmu.group(2))
arm_ids = re.findall(r'(M7\d\d) CAUGHT', mut)
if len(arm_ids) != knives:
    die('刀号 %d 个与 CAUGHT %d 不吻合 ⇒ 结论行与名单没对账' % (len(arm_ids), caught))

# ——————————————————— 全量卷 + 名册读数 ———————————————————

if not os.path.isfile(FULL_LOG):
    die('全量卷日志不在：' + FULL_LOG + '（Sources 改过 ⇒ 全量卷是硬门，D-208）')
full = read(FULL_LOG)
mf = re.findall(r'Executed (\d+) tests, with (\d+) tests skipped and (\d+) failures?', full)
if not mf:
    die('全量卷结论行读不到')
big = max(mf, key=lambda g: int(g[0]))
swift_n, swift_skip, swift_fail = [int(x) for x in big]
red_names = re.findall(r"Test Case '-\[[\w.]+ (\w+)\]' failed", full)
if swift_fail and not red_names:
    die('全量卷报 %d 个失败却一条都没点名 ⇒ 结论行与点名通道对不上，先查日志形状' % swift_fail)
mros = re.search(r'HOVER_TOKEN_ROSTER files=(\d+) reads=(\d+)', full)
if not mros:
    die('名册结论行没在全量卷里露面 ⇒ 「直读位点还剩几处」这句话没有证人')
ros_files, ros_reads = int(mros.group(1)), int(mros.group(2))
if ros_reads > 4:
    die('名册 reads=%d > 4 ⇒ 又长了新的自绘悬停位点，本轮不能顺手收口' % ros_reads)

# ——————————————————— 换装本机 ———————————————————

inst = read(INSTALL_LOG) if os.path.isfile(INSTALL_LOG) else ''
mi = re.search(r'INSTALL_RESULT=(\w+)', inst)
if not mi or mi.group(1) != 'ok':
    die('换装本机没有 ok 结论行：' + (mi.group(0) if mi else '无 INSTALL_RESULT'))
install = mi.group(1)

# ——————————————————— 改动面 ———————————————————

diff = subprocess.run(['git', 'diff', '--name-only', 'HEAD'], cwd=ROOT,
                      stdout=subprocess.PIPE).stdout.decode('utf-8', 'replace')
prod = [p for p in diff.splitlines() if p.startswith('ClipboardHistory/Sources/')]
EXPECTED_PROD = ['GlassControls.swift', 'HistorySidebarView.swift', 'PressableStyle.swift']
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

BASE = dict(
    AR=audit_round, R=230, DAY=DAY, NOW=NOW, U1=U1, U2=U2, U3=U3, U4=U4,
    NB=NEW_B, NB2=NEW_B2, ND=NEW_D_, TR=this_round,
    n_frames=n_frames, compared=compared, changed=changed, added=added,
    head_n=len(frame_keys(head_json)), work_n=len(frame_keys(work_json)),
    cmp_added=compare_added,
    cap_n=cap_n, cap_skip=cap_skip,
    swift_n=swift_n, swift_skip=swift_skip, swift_fail=swift_fail,
    reds=('（无）' if not red_names else '、'.join(sorted(set(red_names)))),
    ros_files=ros_files, ros_reads=ros_reads,
    knives=knives, caught=caught, arms='、'.join(arm_ids),
    prod='、'.join(p.split('/')[-1] for p in prod), install=install,
    # 亮档
    ls_ratio=('%.3f' % direct['light']['seg_ratio']), ls_idle=direct['light']['seg_idle'],
    ls_hov=direct['light']['seg_hov'], ls_px=direct['light']['seg_px'],
    lsel=('%d→%d' % (direct['light']['sel_idle'], direct['light']['sel_hov'])),
    lg_ratio=('%.3f' % direct['light']['gl_ratio']), lg_idle=direct['light']['gl_idle'],
    lg_hov=direct['light']['gl_hov'], lg_px=direct['light']['gl_px'],
    # 暗档
    ld_ratio=('%.3f' % direct['dark']['seg_ratio']), ld_idle=direct['dark']['seg_idle'],
    ld_hov=direct['dark']['seg_hov'], ld_px=direct['dark']['seg_px'],
    ldsel=('%d→%d' % (direct['dark']['sel_idle'], direct['dark']['sel_hov'])),
    lgd_ratio=('%.3f' % direct['dark']['gl_ratio']), lgd_idle=direct['dark']['gl_idle'],
    lgd_hov=direct['dark']['gl_hov'], lgd_px=direct['dark']['gl_px'],
    # 改前
    pgl=('%d' % pre_gl_grey), pglr=('%.3f' % pre_gl_ratio),
    pghost=('%d→%d' % (pre_sel_idle, pre_sel_hov)), pdark=('%d→%d' % (pre_sel_dark, pre_sel_dark)),
    # R229 那条旧位点（不许被本轮碰坏）
    lp=pill['light'][0], lr=('%.3f' % pill['light'][1]), dp=pill['dark'][0], dr=('%.3f' % pill['dark'][1]),
)
BASE['TITLE'] = (u'悬停那一层灰全仓只留一条换算：两处"不走样式表"的自绘位点搬进 `HoverInk`，'
                 u'并抓到 R229 那一抬带着一个洞上线（亮档选中段 %s 凭空一层灰）' % BASE['pghost'])
BASE['SCOPE'] = (u'产品 ' + str(len(prod)) + u' 文件（换算出口 + 段按钮让位 + 玻璃圆改走共用路径）'
                 + u' + 判据 2 文件 + 夹具 1 文件 + 表 1 文件')

UI_NEW = u'''## 第 {AR} 轮（R{R} · {DAY}）：{TITLE}（U-{U1}…U-{U4} · {SCOPE}）

- **U-{U1}：⓪ 本轮 CI 未读（诚实记账，不是"绿了"）。**
  上一跑（`a7e3154` / run `39301400951`）在提交时仍未落地，本轮没有再取 runner 读数 ⇒
  249 与 253 的"接进 CI"那一半**照旧未读**，写进 R231 的第 ⓪ 条。
  本机这一轮能签字的是：捕获卷 `Executed {cap_n} tests, {cap_skip} skipped, 0 failures`、
  全量卷 `Executed {swift_n} / {swift_skip} skip / {swift_fail} 失败`（点名：{reds}）。
- **U-{U2}：R229 那一抬**带着一个洞上线了**，而且是帧抓到的，不是想出来的。**
  `HoverInk.opacity(level:dark:)` 第一版把亮档抬量**无条件**加上去 ⇒ 写 `hoverLevel: 0` 的位点
  （"这一家的悬停我不画"：R20 的 `GlassPillButton`、本轮之前的段按钮）被抬成 0.025 = 屏幕上凭空一层灰。
  两态对照（`/tmp/shots_r230` vs `/tmp/shots_r230b`，`pre_read_r230.py`）：亮档 `segmented-filter-hover`
  的**选中那一段**（它根本没有悬停层）`{pghost}`，而暗档同一格 `{pdark}` 一动不动 ⇒ 多出来的正是那一抬。
  修法四件套：`guard level > 0 else {{ return 0 }}` 出口 + 真值表补 `hoverLevel: 0` 那一格 +
  像素断言（点亮帧里选中段必须与空闲帧同灰）+ 刀 M772（删掉那行 guard 必须红）。
  **这一条记的不是"以后要注意"**：`a7e3154` 已经推上去了。
- **U-{U3}：两处"不走样式表"的直读位点搬进同一条换算，并量出一个新机制。**
  ① 侧栏段按钮原本叠着**两层**悬停灰（`PressedLabel` 默认档 0.06+抬量，和它自己画的 `controlHover`）⇒
  样式那一层让位（`hoverLevel: 0`，R20 的双层规矩反过来用），只留一层。
  ② 玻璃圆钮（`GlassIconControl`）在 `.compositingGroup()` **内部**自绘那一层 ⇒
  同一个名义 alpha 比共用路径**实测更弱**：改前亮档 `{pgl}`/底 = **{pglr}:1**（低于自家地板 1.20），
  而共用路径上同一个令牌量到 {lr}:1。处置不是给它单独配一个数，是**删掉自绘层**
  （连带删掉 `isHovered` / `colorScheme` / `hoverLayer` 三处只服务于那一层的配置），
  让它走 `pressedStyle(in: Circle(), hoverLevel: VisualFill.controlHover)`。
  修完两档直接读数（每档各自压自己那片底）：段按钮 亮 {ls_idle}→{ls_hov} = **{ls_ratio}**（像素 {ls_px}）、
  暗 {ld_idle}→{ld_hov} = **{ld_ratio}**（像素 {ld_px}）；玻璃圆 亮 {lg_idle}→{lg_hov} = **{lg_ratio}**（像素 {lg_px}）、
  暗 {lgd_idle}→{lgd_hov} = **{lgd_ratio}**（像素 {lgd_px}）。地板 亮 ≥1.20 / 暗 ≥1.10 全过；
  选中段点亮帧 {lsel}（亮）/ {ldsel}（暗）⇒ 幽灵层没了。
  旧位点没被碰坏：R229 那条行收藏药丸仍是 亮 {lp} = {lr}:1、暗 {dp} = {dr}:1。
- **U-{U4}：把"还有几处自己画悬停层"换成一个只准降的数，外加两笔自曝。**
  新守卫 `HOVER_TOKEN_ROSTER files={ros_files} reads={ros_reads}` —— 扫 `Sources/` 里读 `VisualFill.controlHover`
  / 调 `HoverInk.opacity` 的位点，**剥掉行注释后**按文件点名；豁免名册只有 `VisualTokens.swift`（定义处）与
  `PressableStyle.swift`（换算本身），`QuickPickController.swift` 按设计豁免（AppKit 浮层自绘）。
  目标：DetailView 那两处 + SettingsView 那一处搬进 `HoverInk` 后 reads 从 {ros_reads} 降到 0 ⇒ 开 **{NB}**。
  自曝两笔：① 判断矩形第一版按"26pt 胶囊居中在 60pt 框里"**猜**（pt 17…43）⇒ 两块都落在纸上，
  比值 1.000、面积 5376 的假读数；真带是 px 66…118 = pt 33…59。现在三块矩形升成**类级共享常量**，
  已知答案对照与产品判据读同一组坐标，并加一条前提断言"两段不许读到同一个灰阶"（否则上面两条断言说的都不是产品）。
  ② `pillReading` 里我新写了一个 `contrastRatio`，撞上文件里**早就有**的那颗 WCAG 尺（`invalid redeclaration`）⇒
  改成调用既有那颗；于是"已知答案对照"那条同形断言失效，补了一条与顺序无关的判据（R100 的"同形 assert"坑）。

其余读数：帧名单 `COMPARED={compared} CHANGED={changed} BASELINE_ADDED={added}`
（HEAD 的 {head_n} 张 vs 工作树的 {work_n} 张；`compare` 那一次报 `ADDED={cmp_added}` —— 那是**更新之前**的数，
本轮把"新增几张"仍按基线两版相减来记，并且钉了一条"旧帧哈希一个都不许动"的断言：
`update` 之后若有旧帧值被改写就红）；盘上帧数 {n_frames}；构建 0 告警；换装本机 `INSTALL_RESULT={install}`。
看图腿真做（6 张新帧全看了）：`segmented-filter-idle/hover`（亮 + 暗）—— 空闲是干净的段，点亮帧里
未选中那一段浮起一圈清楚的胶囊、**选中那一段纹丝不动**，深浅两档都像系统分段控件；
`glass-pill-hover`（亮 + 暗）—— 四颗圆钮各浮起一层柔灰圆斑、图标不被压暗。
**但这张帧只配当"这一层看不看得见"的证据**：取证通道是环境值，整条胶囊一起亮，
而产品上永远只有一颗被悬停 ⇒ 逐颗的态要另一张夹具，开 **{NB2}**。

'''.format(**BASE)

SCORES = {dims[0]: 13, dims[1]: 14, dims[2]: 14, dims[3]: 12,
          dims[4]: 14, dims[5]: 15, dims[6]: 15}
dim_table = '\n'.join([u'| ' + d + u' | ' + str(SCORES[d]) + u'/15 |' for d in dims])
BASE.update(DIMTABLE=dim_table, TOTAL=sum(SCORES.values()))

IT_BLOCK = u'''
## Round {TR} · {TITLE}（{DAY} · {SCOPE}）

⓪ 先记账：本轮**没读 runner**（上一跑提交时还没落地），249 / 253 的"接进 CI"那一半照旧未读 ⇒ 交给 R231 的 ⓪。
本机签了字的是：捕获卷 {cap_n} 格 0 失败、全量卷 {swift_n} 格 {swift_skip} skip {swift_fail} 失败（{reds}）。

① 这一轮的靶还是 251，但先撞见一个**上一轮已经上线的洞**：`HoverInk.opacity` 第一版把亮档抬量无条件加上，
于是写 `hoverLevel: 0`（"这家的悬停我不画"）的位点被抬成 0.025 ⇒ 屏幕上凭空一层灰。
抓它的是帧不是推理：`segmented-filter-hover` 亮档**选中那一段**（它没有悬停层）`{pghost}`，
暗档同一格 `{pdark}` 一动不动 ⇒ 两态一对照，多出来的正是那一抬。
修成 `guard level > 0` + 真值表那一格 + 像素断言 + 刀 M772。**"注释里写以后注意"救不了已推上去的那版。**

② 然后把两处"不走样式表"的直读位点搬进同一条换算。段按钮原来叠着两层灰（样式默认档 + 自己画的 `controlHover`）
⇒ 样式让位、只留一层。玻璃圆钮在 `.compositingGroup()` 内部自绘 ⇒ **同一名义 alpha 实测更弱**
（改前亮档 {pgl}/底 = {pglr}:1，低于地板 1.20；共用路径上同一令牌是 {lr}:1）。
处置是删掉自绘层改走 `pressedStyle`，而不是给它单独配一个数 —— 否则"亮档那一档灰"又多了两个定义处。
修完：段按钮 亮 {ls_ratio} / 暗 {ld_ratio}，玻璃圆 亮 {lg_ratio} / 暗 {lgd_ratio}，四格全压自己那片底、全过线；
选中段点亮帧 {lsel} / {ldsel} ⇒ 幽灵层没了；R229 那条旧药丸仍是 {lr} / {dr} ⇒ 没被碰坏。

③ 形状上多了一条会红的账：`HOVER_TOKEN_ROSTER files={ros_files} reads={ros_reads}` ——
"还有几处自己画悬停层"从散文变成一个**只准降的数**，豁免名册按方向各列（定义处 / 换算本身 / AppKit 浮层）。

自曝两笔：判断矩形第一版是**猜**的（pt 17…43 落在纸上，读出比值 1.000、面积 5376 的假数）⇒
真带 px 66…118 = pt 33…59，矩形升成共享常量 + 一条"两段不许同灰"的前提断言；
`pillReading` 里我重写了文件里**早就有**的那颗 WCAG 尺（`invalid redeclaration`）⇒ 改调用既有那颗，
再把因此变成同形的已知答案断言换成与顺序无关的判据。

验证：构建 0 告警、捕获卷 {cap_n}/0 失败、全量卷 {swift_n}/{swift_skip}/{swift_fail}、
`COMPARED={compared} CHANGED={changed} BASELINE_ADDED={added}`（旧帧哈希一条没动，由断言签）、
刀 `R230_MUTATE 刀={knives} CAUGHT={caught} ESCAPED=0 NOT_RUN=0 RESTORE_CLEAN=yes`（{arms}）、
换装本机 `INSTALL_RESULT={install}`、看图腿真做（6 张新帧，含"四颗同时亮"这张帧的**能力边界**已记账 {NB2}）。

七维度自评：

| 维度 | 得分 |
|---|---|
{DIMTABLE}

总分 {TOTAL}/105（{TR} 轮）。GAPS=none
'''.format(**BASE)

CH_BLOCK = u'''### 悬停那一层灰全仓只留一条换算 + 抓到 R229 那一抬的洞（R{R} / U-{U1}…U-{U4} · {SCOPE}）

- 洞（**上一轮已上线**）：`HoverInk.opacity` 少一个 `level == 0` 出口 ⇒ 写 `hoverLevel: 0` 的位点被抬量抬成 0.025，
  屏幕上凭空一层灰。由帧抓到：亮档 `segmented-filter-hover` 选中段 `{pghost}`、暗档同一格 `{pdark}`（两态对照）。
  修：`guard level > 0` + 真值表那一格 + 像素断言 + 刀 M772。
- 两处直读位点搬进同一条换算：段按钮原来**两层灰叠着**⇒ 样式层让位（`hoverLevel: 0`）；
  玻璃圆钮在 `.compositingGroup()` 内自绘 ⇒ 同一名义 alpha 实测更弱（改前亮档 {pgl} = {pglr}:1 < 地板 1.20，
  共用路径同令牌 {lr}:1）⇒ 删自绘层（连带 `isHovered`/`colorScheme`/`hoverLayer`）改走 `pressedStyle`。
- 修完两档直接读数：段按钮 亮 {ls_idle}→{ls_hov} = {ls_ratio}、暗 {ld_idle}→{ld_hov} = {ld_ratio}；
  玻璃圆 亮 {lg_idle}→{lg_hov} = {lg_ratio}、暗 {lgd_idle}→{lgd_hov} = {lgd_ratio}（地板 1.20/1.10 全过）；
  选中段 {lsel} / {ldsel}；R229 旧药丸仍 {lr} / {dr}（未碰坏）。
- 新守卫 `HOVER_TOKEN_ROSTER files={ros_files} reads={ros_reads}`：把"还有几处自己画悬停层"变成只准降的数
  （剥行注释后按文件点名；豁免=定义处/换算本身/AppKit 浮层）⇒ 剩下的三处开 **{NB}**，逐颗悬停帧开 **{NB2}**。
- 产品改动面（由 `git diff` 算出，不手抄）：{prod}。
- 自曝两笔：判断矩形第一版是猜的（两块都落在纸上 ⇒ 比值 1.000 假读数）⇒ 真带 px 66…118 = pt 33…59，
  矩形升成共享常量 + "两段不许同灰"前提断言；`pillReading` 重写了文件里已有的 `contrastRatio` ⇒ 改调用既有那颗，
  再把变同形的已知答案断言换成与顺序无关的判据。
- 验证：构建 0 告警、捕获卷 {cap_n}/0 失败、全量卷 {swift_n}/{swift_skip}/{swift_fail}（{reds}）、
  `COMPARED={compared} CHANGED={changed} BASELINE_ADDED={added}`（旧帧哈希未动，由断言签）、
  刀 {knives}/{caught} 全 CAUGHT（{arms}）、换装本机 `INSTALL_RESULT={install}`、看图 6 张新帧。
- **CI 未读**：`a7e3154`（run `39301400951`）提交时未落地 ⇒ 249 / 253 的"接进 CI"那一半照旧未读。

'''.format(**BASE)

STATE_BLOCK = u'''最后更新：{NOW}（本地 · R{R} / 第 {AR} 轮：**{TITLE}**（U-{U1}…U-{U4} · {SCOPE}）

**本轮落地**：① 抓到**上一轮已上线**的洞 —— `HoverInk.opacity` 少 `level == 0` 出口 ⇒
写 `hoverLevel: 0` 的位点被亮档抬量抬成 0.025（凭空一层灰）。两态对照签：亮档选中段 `{pghost}`、暗档 `{pdark}`。
修成 guard + 真值表 + 像素断言 + 刀 M772。
② 两处"不走样式表"的直读位点搬进同一条换算：段按钮原来两层灰叠着 ⇒ 样式层让位；
玻璃圆钮在 `.compositingGroup()` 内自绘 ⇒ **同一名义 alpha 实测更弱**（改前亮档 {pgl} = {pglr}:1 < 1.20，
共用路径同令牌 {lr}:1）⇒ 删自绘层改走 `pressedStyle`。修完四格读数 亮 {ls_ratio}/{lg_ratio}、暗 {ld_ratio}/{lgd_ratio} 全过线，
选中段 {lsel}/{ldsel} 无幽灵层，R229 旧药丸未碰坏（{lr}/{dr}）。
③ 新守卫 `HOVER_TOKEN_ROSTER files={ros_files} reads={ros_reads}`：把"还剩几处自己画悬停层"变成**只准降的数**。
刀 {knives} 把全 CAUGHT（{arms}）；帧 `COMPARED={compared} CHANGED={changed} BASELINE_ADDED={added}`（旧帧哈希一条没动）；
捕获卷 {cap_n}/0 失败、全量卷 {swift_n}/{swift_skip}/{swift_fail}（{reds}）；换装本机 `INSTALL_RESULT={install}`；
看图腿真做 6 张新帧，并记下 `glass-pill-hover` 的能力边界（整条胶囊一起亮 ⇒ 逐颗的态另开 **{NB2}**）。

**下一轮（R231）的靶**：⓪ 读 `a7e3154`（run `39301400951`）与本轮这一跑的 CI —— 249 / 253 的"接进 CI"那一半仍未读；
① {NB}：DetailView 那两处 + SettingsView 那一处搬进 `HoverInk`，把名册 reads 从 {ros_reads} 降到 0；
② {NB2} 逐颗悬停帧；③ 254（"录制中"两帧相位不确定：本轮又是靠重跑拿稳定值，第二次了）、
255（性能预算格换成同一次运行内的相对判据，不许直接抬 250）；
④ 248、243、250、227③、222、215、201/202、207、240；⑤ 220 路 A、228② 等用户。
)

'''.format(**BASE)

BL_BLOCK = u'''
**{NB}. 还剩 {ros_reads} 处"自己画悬停层"的位点没进 `HoverInk`（`HOVER_TOKEN_ROSTER` 已把它们数成可数的数，R230 记账）**

现场：R230 把段按钮与玻璃圆钮搬进共用换算之后，名册守卫打印 `HOVER_TOKEN_ROSTER files={ros_files} reads={ros_reads}` ——
剩下的是 `DetailView.swift` 两处（chip / card，读行档 `VisualFill` 直画一层灰）与 `SettingsView.swift` 一处（`backgroundOpacity`）。
`QuickPickController.swift` 那处按设计豁免（AppKit 浮层自己画，不走 SwiftUI 样式表）。
为什么非做不可：这一族病（R219 骨架墨 / R225 浮层悬停 / R229 小控件 / R230 幽灵层）的**共同形状**就是
"共用一个令牌、但拿不到按档给的那一等"。名册守卫只钉住"数量不许涨"，**结案要的是 reads=0**：
每搬一处都要留两样东西 —— 两档各自的像素读数（压自己那片底），和一条把该位点从豁免/名册里划掉的守卫改动。
不许做的事：把 reads 的地板抬到当前值然后宣布结案。

**{NB2}. `glass-pill-hover` 是"四颗圆钮同时亮"——它证明这一层看得见，不证明悬停时长什么样（R230 看图时记账）**

现场：取证通道 `EnvironmentValues.hoveredForCapture` 是**环境值**，写在 `GlassPill` 上就整条胶囊一起亮；
本轮看图确认亮/暗两档的四层柔灰圆斑都读得出来（{lg_ratio} / {lgd_ratio}），但产品上永远只有一颗被悬停。
⇒ 这张帧配当"这一层在自家底上看不看得见"的证据，**不配**当"悬停态的观感"证据；
后者要一颗逐颗的夹具（把钩子挂在 `GlassPillButton` 自身、只点亮其中一颗，与 `row-favorite-hover` 同一手法）。
另记：本轮 `frame_baseline.py compare` 两次都在"录制中"那对上抖动（254 的第二次），
处置与 R229 相同 —— **重跑捕获卷拿稳定值，不把抖动 update 进基线**；这条重复出现本身就是 254 的读数。

'''.format(**BASE)

DE_BLOCK = u'''
**D-{ND}（R230）：一层悬停灰只允许一条换算路径；给常数加"抬量"时必须先枚举所有 0 的调用点**

现场：R229 为了让亮档小控件的悬停看得见，给 `HoverInk` 加了 +0.025 的抬量。它同时**默认了另一件事**：
所有调用点都会画这一层。而 `hoverLevel: 0` 在这仓里是一个**有语义的值**（R20 起，`GlassPillButton`
用它表示"这家的悬停我不画，只留缩放"），抬量一加，0 就变成 0.025 ⇒ 屏幕上凭空一层灰。
这一版已经推上线（`a7e3154`），抓它的是**帧的两态对照**而不是读代码：亮档选中段 `{pghost}`、暗档同一格 `{pdark}`。
规矩：
① **改常数的换算，先枚举这个常数的所有取值语义**，特别是 0 / 空 / 默认档 —— 0 常常不是"没量"而是"作者决定不画"。
   这一条由 `HoverInk.opacity` 的 `guard level > 0` 与真值表那一格钉住，由刀 M772 保证它会红；
② **同一个视觉量只许有一条换算路径**：不走样式表、自己 `.fill()/.overlay()` 画一层的位点是这一族病的温床
   （R219 / R225 / R229 / R230 四次同一个形状）。处置顺序是**先搬进共用路径**，
   搬不动才允许自绘，且自绘必须问 `HoverInk` 而不是自己 `+ 0.025`；
③ **画法的差异会改变读数**：同一名义 alpha 画在 `.compositingGroup()` **内部**比画在共用 `PressedLabel`
    overlay 上实测更弱（本轮量到 {pglr}:1 vs {lr}:1，同一令牌、同一档）。⇒ 遇到"这一家就是淡"先怀疑**画法**，
   不要给某个位点单独配一个数（那等于把第二条换算路径合法化）；
④ **守卫要能数出剩余债**：把"还有几处没搬"做成一个只准降的读数（`HOVER_TOKEN_ROSTER`），
   而不是写在散文里 —— 写在注释里的分类法不会红（R107 的原话）。
适用面：所有跨位点共用的强度/颜色令牌；不适用：系统着色通道（强调色、非 key 窗口的灰选中 —— R102/R107 已按控件回答过）。
'''.format(**BASE)

# ——————————————————— 写盘前：文本自相矛盾 / 陈旧归因扫描 ———————————————————

blocks = [('UI_NEW', UI_NEW), ('IT_BLOCK', IT_BLOCK), ('CH_BLOCK', CH_BLOCK),
          ('STATE_BLOCK', STATE_BLOCK), ('BL_BLOCK', BL_BLOCK), ('DE_BLOCK', DE_BLOCK)]
for name, blk in blocks:
    for sent in re.split(u'[。\n]', blk):
        # 改后的数不许被说成低于地板；改前的数不许被说成"修好了"。
        if re.search(r'1\.2[2-9]\d?|1\.[3-9]\d*', sent) and (u'掉在' in sent or u'低于' in sent):
            if BASE['pglr'] not in sent:
                die('%s 里有一句把改后的读数说成了低于地板：%s' % (name, sent[:80]))
    for stale in (u'负载抖动', u'单跑绿', u'产品 2 文件', u'R229 那一轮真红过）', u'CI 绿'):
        if stale in blk:
            die('%s 里还留着旧一轮的说法「%s」' % (name, stale))
    if u'未读' not in blk and u'CI' in blk:
        pass  # 允许"CI 未读"以外的 CI 提及，但下面这条兜底：不许出现"runner 已验收"。
    if u'runner 已验收' in blk or u'CI 已验收' in blk:
        die('%s 里出现了 CI 验收的说法，而本轮 CI 未读 ⇒ 假话' % name)

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
        die('锚点找不到或不唯一：' + path + ' ｜ ' + anchor)
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


plan_insert('AGENT_UI_AUDIT.md', u'## 第 ' + str(audit_round - 1) + u' 轮（R229 · ', UI_NEW)
plan_append('AGENT_VISUAL_ITERATION.md', IT_BLOCK)
ch = read('CHANGELOG.md')
idx = ch.find(u'## [Unreleased]')
if idx < 0:
    die('CHANGELOG 没有 [Unreleased]')
cut = idx + len(u'## [Unreleased]')
plans.append(('CHANGELOG.md', ch, ch[:cut] + u'\n' + CH_BLOCK + ch[cut + 1:]))
DELTAS['CHANGELOG.md'] = CH_BLOCK
plan_insert_where('AGENT_STATE.md', u'^最后更新：', STATE_BLOCK, u'R229 / 第 231 轮')
plan_append('AGENT_BACKLOG.md', BL_BLOCK)
plan_append('AGENT_DECISIONS.md', DE_BLOCK)

STRAY = re.compile(r'\{[A-Z][A-Za-z_0-9]*\}')
for name, blk in blocks:
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
print(u'LEDGERS_R230 wrote %d files；编号：第 %d 轮 / Round %d / U-%d…U-%d / BACKLOG +%d +%d / D-%d'
      % (len(plans), audit_round, this_round, U1, U4, NEW_B, NEW_B2, NEW_D_))
print(u'LEDGERS_R230 读数：段按钮 亮%s/暗%s、玻璃圆 亮%s/暗%s、改前 玻璃%s 幽灵%s、帧 COMPARED=%d CHANGED=%d ADDED=%d、'
      u'刀 %d/%d、名册 files=%d reads=%d、全量卷 %d/%d/%d'
      % (BASE['ls_ratio'], BASE['ld_ratio'], BASE['lg_ratio'], BASE['lgd_ratio'],
         BASE['pglr'], BASE['pghost'], compared, changed, added, caught, knives,
         ros_files, ros_reads, swift_n, swift_skip, swift_fail))

state = read('AGENT_STATE.md')
ms2 = re.search(u'最后更新：[^\\n]*?R(\\d+) / 第 (\\d+) 轮', state)
if not ms2 or int(ms2.group(1)) != 230 or int(ms2.group(2)) != audit_round:
    die('STATE 轮次行读不出 R230 / 第 ' + str(audit_round) + u' 轮')
for path, pat in ((u'AGENT_UI_AUDIT.md', u'^## 第 ' + str(audit_round) + u' 轮（R230'),
                  (u'AGENT_VISUAL_ITERATION.md', u'^## Round 230 · '),
                  (u'CHANGELOG.md', u'^### .*（R230 / ')):
    if not re.search(pat, read(path), re.M):
        die(path + u' 里读不到本轮标题：' + pat)
print(u'LEDGERS_R230 selfcheck ok')
sys.exit(0)

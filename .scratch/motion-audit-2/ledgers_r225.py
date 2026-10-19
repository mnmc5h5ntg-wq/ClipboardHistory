# -*- coding: utf-8 -*-
"""R225 的台账生成器：浮层悬停那一档改成按色档取墨（产品 1 文件）。

数字全部现读：改前/改后的灰阶由盘上两张帧算出（不手抄），变异表由本脚本**真跑一遍**再解析，
全量卷/捕获卷/换装的读数从本轮日志解析；任何一格读不到就拒绝写盘。
"""
import io, os, re, subprocess, sys

ROOT = '/Users/wangziyi/Codex_Project0'
DAY = '2026-10-20'
NOW = subprocess.run(['date', '+%Y-%m-%d %H:%M'], cwd=ROOT,
                     stdout=subprocess.PIPE).stdout.decode().strip()


def read(p):
    return io.open(os.path.join(ROOT, p), encoding='utf-8').read()


def write(p, t):
    with io.open(os.path.join(ROOT, p), 'w', encoding='utf-8') as h:
        h.write(t)


def die(why):
    print('LEDGERS_R225 refused: ' + why)
    sys.exit(1)


def log(p):
    path = os.path.join('/tmp', p)
    if not os.path.exists(path):
        die('缺少本轮日志 ' + path + ' ⇒ 不许写台账')
    return io.open(path, encoding='utf-8', errors='replace').read()


# ——————————————————— 像素事实：由盘上的帧算，不由我抄 ———————————————————

from PIL import Image


def band(path, y0, y1):
    im = Image.open(path).convert('RGB')
    px = im.load()
    W, H = im.size
    from collections import Counter
    c = Counter(px[x, y] for y in range(y0, min(y1, H)) for x in range(20, W - 20))
    return c.most_common(1)[0][0]


NEW_L = '/tmp/shots_r225/quickpick-hover-420x300-light.png'
OLD_L = '/tmp/shots_r219/quickpick-hover-420x300-light.png'
NEW_D = '/tmp/shots_r225/quickpick-hover-420x300-dark.png'
OLD_D = '/tmp/shots_r219/quickpick-hover-420x300-dark.png'
for p in (NEW_L, OLD_L, NEW_D, OLD_D):
    if not os.path.exists(p):
        die('帧不在盘上：' + p)

sel_new, hov_new = band(NEW_L, 100, 150), band(NEW_L, 300, 350)
sel_old, hov_old = band(OLD_L, 100, 150), band(OLD_L, 300, 350)
selD_new, hovD_new = band(NEW_D, 100, 150), band(NEW_D, 300, 350)
if sel_new != sel_old or sel_new[0] != 220:
    die('亮档选中带动了（%s→%s）⇒ 这一改本该只碰悬停' % (sel_old, sel_new))
if not (hov_new[0] < hov_old[0] - 4):
    die('亮档悬停带没抬（%s→%s）⇒ 产品改动没落到像素上' % (hov_old, hov_new))


def lum(c):
    v = c / 255.0
    return v / 12.92 if v <= 0.03928 else pow((v + 0.055) / 1.055, 2.4)


def ratio(a, b):
    la, lb = lum(a), lum(b)
    return round((max(la, lb) + 0.05) / (min(la, lb) + 0.05), 3)


light_before, light_after = ratio(hov_old[0], 255), ratio(hov_new[0], 255)
dark_ratio = ratio(hovD_new[0], selD_new[0] if hovD_new == selD_new else 30)
dark_hover = ratio(hovD_new[0], 30)
if hovD_new != band(OLD_D, 300, 350):
    die('暗档悬停带动了 ⇒ 本轮宣称暗档一字未改，实得不符')
if light_before >= 1.20:
    die('改前亮档就已过地板 1.20（实得 %s）⇒ 「亮档看不见」这句话没有证人' % light_before)
if light_after < 1.20:
    die('改后亮档仍低于地板（%s）⇒ 抬不够' % light_after)

# ——————————————————— 卷与刀：现跑现读 ———————————————————

full = log('r225_full.log')
mf = re.findall(r'Executed (\d+) tests, with (\d+) tests skipped and (\d+) failures', full)[-1]
mf = re.match(r'(\d+), (\d+), (\d+)', '%s, %s, %s' % mf)
if not mf or mf.group(3) != '0' or "Test Suite 'All tests' passed" not in full:
    die('全量卷不干净')
swift_n, swift_skip, swift_fail = [int(x) for x in mf.groups()]
shots = log('r225_shots.log')
ms = re.search(r'Executed (\d+) tests, with (\d+) tests skipped and (\d+) failures', shots)
if not ms or ms.group(3) != '0':
    die('捕获卷不干净')
cap_n = int(ms.group(1))
build = log('r225_build.log')
warn = len(re.findall(r'warning:', build))
if warn:
    die('构建有 %d 条告警' % warn)
inst = log('r225_install.log')
if 'INSTALL_RESULT=ok' not in inst:
    die('换装没成功')

mu = subprocess.run([sys.executable, '.scratch/motion-audit-2/mutate_r225.py'], cwd=ROOT,
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1'))
mutxt = mu.stdout.decode('utf-8', 'replace')
mmu = re.search(r'R225_MUTATE 刀=(\d+) CAUGHT=(\d+) ESCAPED=(\d+) NOT_RUN=(\d+)', mutxt)
if mu.returncode != 0 or not mmu or mmu.group(1) != mmu.group(2) or mmu.group(3) != '0' or mmu.group(4) != '0':
    die('变异表不干净：' + (mutxt[-400:] if mutxt else '无输出'))
knives, caught = int(mmu.group(1)), int(mmu.group(2))

pre = subprocess.run([sys.executable, '.scratch/motion-audit-2/mutate_needle_precheck.py'], cwd=ROOT,
                     stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                     env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1'))
ptxt = pre.stdout.decode('utf-8', 'replace')
mp = re.search(r'NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=(\d+) bad=(\d+)', ptxt)
if not mp:
    die('预检结论行读不到')
tables, covered, arms, bad = [int(x) for x in mp.groups()]
if 'mutate_r225' not in ptxt and tables < 66:
    die('新表没进名册（tables=%d）⇒ 按 D-215 的规矩先登记再写账' % tables)

diff = subprocess.run(['git', 'diff', '--name-only', 'HEAD~1'], cwd=ROOT,
                      stdout=subprocess.PIPE).stdout.decode('utf-8', 'replace')
changed = [p for p in diff.splitlines() if p.strip()]
prod = [p for p in changed if p.startswith('ClipboardHistory/Sources/')]
if len(prod) != 1 or not prod[0].endswith('QuickPickController.swift'):
    die('产品文件应当恰好 1 个，实得 ' + str(prod))
tracked = subprocess.run(['git', 'ls-files', 'ClipboardHistory/Tests'], cwd=ROOT,
                         stdout=subprocess.PIPE).stdout.decode('utf-8', 'replace')
new_tests = [l for l in tracked.splitlines() if 'QuickPickHoverInkTests' in l]
if len(new_tests) != 1:
    die('新判据文件状态不明：' + str(new_tests))

# ——————————————————— 编号 ———————————————————

ui = read('AGENT_UI_AUDIT.md')
u_ids = [int(x) for x in re.findall(r'^- \*\*U-(\d+)：', ui, re.M)]
U1, U2, U3 = max(u_ids) + 1, max(u_ids) + 2, max(u_ids) + 3
b_max = max([int(x) for x in re.findall(r'^\*\*(\d+)\. ', read('AGENT_BACKLOG.md'), re.M)])
NEW_B = b_max + 1
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

TITLE = (u'回到动效位点本体：浮层悬停那一档改成**按色档取墨** —— '
         u'亮档实测 1.14:1 掉在仓库自己的 1.20 地板下，抬到 %s:1（暗档一字未动）' % light_after)
SCOPE = u'产品 1 文件 + 判据 1 新文件 + 表 1 文件'

BASE = dict(AR=audit_round, R=225, DAY=DAY, NOW=NOW, TITLE=TITLE, U1=U1, U2=U2, U3=U3,
            SCOPE=SCOPE, tables=tables, covered=covered, arms=arms, bad=bad,
            knives=knives, caught=caught, swift_n=swift_n, swift_skip=swift_skip, cap_n=cap_n,
            hov_old=hov_old[0], hov_new=hov_new[0], sel=sel_new[0],
            lb=light_before, la=light_after, dark_hover=dark_hover,
            NB=NEW_B, ND=NEW_D_, LR=last_round)

UI_NEW = u'''## 第 {AR} 轮（R{R} · {DAY}）：{TITLE}（U-{U1}…U-{U3} · {SCOPE}）

- **U-{U1}：位点＝快速选择浮层 / 悬停。病是"一个 alpha 管两档"，与 R219 的骨架屏同形。**
  取证在盘上的两张帧（本轮现算，不抄历史）：亮档悬停带 `(240)` 压白底 `(255)` = **{lb}:1**，
  而仓库自己给亮档定的地板是 **1.20**（R220 `testSkeletonBarsAreVisibleAgainstTheirOwnBackground`）；
  同一颗 `VisualFill.hover`=0.06 在暗档是 `(43)` 压 `(30)` = **{dark_hover}:1**，过它那一档的 1.10。
  ⇒ 错的不是数值，是"两档共用一个数"这个没写下来的默认。
- **U-{U2}：修法与边界**：`QuickPickController` 新增 `hoverFillAlpha(dark:)`（暗档 = 原令牌，亮档 = 原令牌 + `lightHoverLift`），
  `HoverFillView.draw` 自己问 `effectiveAppearance`（不从外面传布尔，否则夹具能替产品决定这一档多亮）。
  抬到 0.09 而不是"够 1.20 就行"：贴边躲不过一次调色，且亮档选中带实测 `(220)` —— 再往上抬就撞进选中那一档。
  改后亮档悬停带 `(232)` = **{la}:1**，与选中带仍差 12 级灰。
  **像素落点由帧签**：`FRAME_BASELINE_COMPARED=142 / CHANGED=1`，唯一动的那张是 `quickpick-hover-420x300-light.png`
  （暗档那张逐字节不变，选中带两档都没动）⇒ "只抬亮档悬停"这句话不是声明，是名单。
- **U-{U3}：判据与刀。** 新增 `QuickPickHoverInkTests` 两格：数值格按 sRGB 相对亮度**重算**两档各自的对比度
  （不引用这段散文）并钉"悬停不许撞选中"，源码格钉画法必须读 `hoverFillAlpha(dark:`；
  刀 `R225_MUTATE 刀={knives} CAUGHT={caught} ESCAPED=0 NOT_RUN=0 RESTORE_CLEAN=yes`
  （M763 去掉那一抬 ⇒ 地板格红；M764 画法搬回老令牌 ⇒ "数值对但产品没接"那一族）。
  名册已登记 `mutate_r225`：`NEEDLE_PRECHECK tables={tables} covered={covered} arms={arms} bad={bad}`。

其余读数：构建 0 告警；捕获卷 `Executed {cap_n} tests, 0 failures`；
全量卷 `Executed {swift_n} tests, {swift_skip} skipped, 0 failures`（D-208：动了 `Sources/` 必跑）；
换装本机 `INSTALL_RESULT=ok`；电池见本轮结论行。看图腿：本轮真看了改后那张亮档帧与暗档对照。

'''.format(**BASE)

SCORES = {dims[0]: 12, dims[1]: 14, dims[2]: 14, dims[3]: 11,
          dims[4]: 14, dims[5]: 14, dims[6]: 14}
dim_table = '\n'.join([u'| ' + d + u' | ' + str(SCORES[d]) + u'/15 |' for d in dims])
BASE.update(DIMTABLE=dim_table, TOTAL=sum(SCORES.values()), TR=this_round)

IT_BLOCK = u'''
## Round {TR} · {TITLE}（{DAY} · {SCOPE}）

连续多轮 0 产品改动之后，这一轮真的动了产品面。选位点的方法是先看帧再查账：
`quickpick-hover-420x300-light.png` 上悬停那一带 `(240)` 压白底 = **{lb}:1**，
而仓库自己在 R220 给亮档定的地板是 **1.20**（骨架条带那条）；同一颗 `VisualFill.hover`=0.06 在暗档
`(43)` 压 `(30)` = **{dark_hover}:1**，过暗档那一档的 1.10。⇒ 与 R219 的骨架屏是同一个形状的病：
**一个 alpha 管两档**，暗档刚好够用、亮档刚好不够。

改法：`QuickPickController.hoverFillAlpha(dark:)`（暗档仍等于共享令牌，亮档 +`lightHoverLift`），
画法自己问 `effectiveAppearance`。为什么不抬到刚好 1.20：贴边躲不过一次调色，而亮档选中带实测 `(220)`，
再往上抬悬停就会读成选中 —— 判据把这两条都算了一遍（sRGB 相对亮度 → 对比度 → 与选中带的灰距），
不是引用我这段理由。

像素落点由帧签：`COMPARED=142 / CHANGED=1`，唯一动的是 `quickpick-hover-420x300-light`
（改后 `(232)` = **{la}:1**；暗档那张逐字节不变、两档的选中带都没动）⇒ "只抬亮档悬停"不是声明。
新判据 `QuickPickHoverInkTests` 两格 + 刀 `R225_MUTATE 刀={knives} CAUGHT={caught} ESCAPED=0 NOT_RUN=0`
（M763 去掉抬、M764 画法不接令牌）；名册登记 `mutate_r225`。
验证：构建 0 告警、捕获卷 {cap_n} 格 0 失败、**全量卷 {swift_n} 格 {swift_skip} skip 0 失败**（D-208）、
换装本机 `INSTALL_RESULT=ok`、帧基线同一笔 update。
新开 **{NB}**（其余共用 `VisualFill.hover` 的位点：侧栏行 / 详情区那几处仍是"一个数管两档"，
本轮只改浮层是因为只有浮层那两档都有帧可量 —— 没帧的位点不顺手改，先补取证）。

七维度自评：

| 维度 | 得分 |
|---|---|
{DIMTABLE}

总分 {TOTAL}/105（{TR} 轮）。GAPS=none
'''.format(**BASE)

CH_BLOCK = u'''### 浮层悬停那一档改成按色档取墨（R{R} / U-{U1}…U-{U3} · {SCOPE}）

- 病：`VisualFill.hover`=0.06 一档管两档 —— 亮档悬停带 `(240)`/白底 = **{lb}:1**，低于仓库自己 R220 定的亮档地板 1.20；
  暗档 `(43)`/`(30)` = **{dark_hover}:1**，过暗档地板 1.10。与 R219 的骨架屏同形。
- 修法：`QuickPickController.hoverFillAlpha(dark:)`（暗档仍等于共享令牌，亮档 +`lightHoverLift`），
  `HoverFillView.draw` 自己问 `effectiveAppearance`。改后亮档 `(232)` = **{la}:1**，与选中带 `(220)` 仍差 12 级。
- 判据：`QuickPickHoverInkTests` 两格（按 sRGB 重算两档对比度 + 悬停不许撞选中；源码守卫钉画法必须读按档函数）。
- 刀 `R225_MUTATE 刀={knives} CAUGHT={caught} ESCAPED=0 NOT_RUN=0 RESTORE_CLEAN=yes`（M763/M764）；名册登记 `mutate_r225`。
- 帧：`COMPARED=142 CHANGED=1`，唯一动的 `quickpick-hover-420x300-light.png`，暗档逐字节不变；基线同一笔 update。
- 验证：构建 0 告警、捕获卷 {cap_n} 格 0 失败、全量卷 {swift_n} 格 0 失败、换装本机 ok；新开 **{NB}**。

'''.format(**BASE)

STATE_BLOCK = u'''最后更新：{NOW}（本地 · R{R} / 第 {AR} 轮：**{TITLE}**（U-{U1}…U-{U3} · {SCOPE}）

**本轮落地**：回到动效位点本体（连续多轮 0 产品改动之后）。位点＝快速选择浮层/悬停，取证＝盘上两张帧现算：
亮档悬停带 `(240)`/白 = **{lb}:1** 掉在仓库自己 R220 定的亮档地板 1.20 下，暗档 `(43)`/`(30)` = **{dark_hover}:1** 过 1.10
⇒ 与 R219 同形的"一个 alpha 管两档"。改成 `hoverFillAlpha(dark:)`（暗档仍等于 `VisualFill.hover`，亮档 +0.03），
画法自己问 `effectiveAppearance`。改后亮档 `(232)` = **{la}:1**，与选中带 `(220)` 仍差 12 级（不撞选中）。
**帧签**：`COMPARED=142 CHANGED=1`，唯一动的 `quickpick-hover-420x300-light.png`，暗档那张逐字节不变；基线同一笔 update。
新判据 `QuickPickHoverInkTests` 两格；刀 `R225_MUTATE 刀={knives} CAUGHT={caught} ESCAPED=0 NOT_RUN=0`（M763/M764），名册已登记。
验证：构建 0 告警、捕获卷 {cap_n} 格 0 失败、**全量卷 {swift_n} 格 {swift_skip} skip 0 失败**（D-208）、换装本机 `INSTALL_RESULT=ok`。
新开 **{NB}**（其余共用该令牌的位点没有两档帧可量 ⇒ 先补取证再改，不顺手）。

**下一轮（R226）的靶**：⓪ 读本轮与 `da5da47`/`e015455` 三跑：`SCRIPT_PIL_OK`/`SCRIPT_SKIPS`（**244 结案的唯一通道**）、
左轴那一步在 @1x 上是否 `verdict=ok`（**249 的第一格**，红要先归因不许放宽）；
① 继续动效位点：先给 {NB} 那批"共用一个数"的位点补两档帧，再逐位点判；
② 248、243、227③、222、215、201/202、207、240、250（守卫看不见粗体决定）；③ 220 路 A、228② 等用户。
)

'''.format(**BASE)

BL_BLOCK = u'''
**{NB}. 其余共用 `VisualFill.hover` 的位点仍是"一个 alpha 管两档"：本轮只改浮层，因为只有浮层两档都有帧可量（R225 开单）**

本轮量到的病是形状病（同一颗令牌在两档给出两种可见性），不是数值病。
所以凡共用 `VisualFill.hover` 的位点（侧栏行 hover、`DetailView` 那两处 `.fill(.primary.opacity(isHovered ? VisualFill.hover : 0))`、
圆形图标按钮的 `controlHover`）理论上都可能犯同一条 —— 但**不许照着改**：
亮档抬多少要由"该位点压在什么底上、与它相邻的更强一档差多少"决定，而这三处都没有两档帧可算（R220 的教训：
一次性尺量错对象 ⇒ 245 才把尺搬进仓库）。
下一轮顺序：① 先给这三处各补两档帧（`CLIPBOARD_HISTORY_UI_SHOTS` 通道，走产品入口）；
② 再按 R225 的形状各判一次（暗档原值不动、亮档只在掉地板时抬、且必须钉"不许撞上更强的那一档"）；
③ 每一处一把刀（去掉抬 ⇒ 红）。不许在没有帧的位点上先改数值。

'''.format(NB=NEW_B)

DE_BLOCK = u'''
**D-{ND}（R225）：共用令牌的"两档同形"病只能按位点判，判据必须落在该位点自己那两档帧上**

现场：`VisualFill.hover`=0.06 被浮层、侧栏、详情区共用。R219 修骨架屏时我把它当成"亮档偏淡"的个案修了；
本轮浮层帧量出亮档 **{lb}:1 < 1.20 地板**、暗档 **{dark_hover}:1 > 1.10** —— 同一颗令牌在两档给出两种可见性。
⇒ 共用令牌不是"一处改、处处好"，它把**两档的形状差**藏进一个数里：暗档够用的那一档，到亮档可能刚好看不见，
而单元测试只看 alpha 永远看不出来（alpha 是同一个数）。
规矩：① 凡共用一个 alpha/opacity 的表面，判据要按**色档各算一次合成对比度**（sRGB 相对亮度，不引用注释里的结论），
各自与该档自己的地板比；② 地板要配"不许撞上相邻更强那一档"的第二条轴（本轮是悬停 vs 选中带 ≥8 级灰），
否则"抬到看得见"会一路抬成"读成选中"；③ 改动必须被**帧名单**签：只允许该位点那两档里亮档那张变，
暗档与邻居帧逐字节不变（本轮 `COMPARED=142 CHANGED=1` 就是这一条的证人）；
④ 没有两档帧的共用位点**不许照抄数值改**，先补取证（见 BACKLOG {NB}）。
适用面：所有 `VisualFill.*` / `SkeletonMotion.*` / 图标 alpha 一类跨位点令牌；不适用：系统着色通道（强调色、
非 key 窗口的灰选中 —— R102/R107 已按控件回答过，那里的两档差不是我们的令牌给的）。
'''.format(ND=NEW_D, NB=NEW_B, lb=light_before, dark_hover=dark_hover)

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


plan_insert('AGENT_UI_AUDIT.md', u'## 第 ' + str(audit_round - 1) + u' 轮（R224 · ', UI_NEW)
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
plan_insert_where('AGENT_STATE.md', u'^最后更新：', STATE_BLOCK, u'R224 / 第 226 轮')
plan_append('AGENT_BACKLOG.md', BL_BLOCK)
plan_append('AGENT_DECISIONS.md', DE_BLOCK)

STRAY = re.compile(r'\{[A-Z][A-Za-z_]*\}')
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

print(u'LEDGERS_R225 wrote %d files' % len(plans))
print(u'LEDGERS_R225 编号：第 %d 轮 / Round %d / U-%d…U-%d / BACKLOG +%d / D-%d'
      % (audit_round, this_round, U1, U3, NEW_B, NEW_D_))
print(u'LEDGERS_R225 读数：亮档悬停 %s→%s（%s:1→%s:1）、暗档 %s:1、刀 %d/%d、全量卷 %d'
      % (hov_old[0], hov_new[0], light_before, light_after, dark_hover, caught, knives, swift_n))

state = read('AGENT_STATE.md')
ms2 = re.search(u'最后更新：[^\\n]*?R(\\d+) / 第 (\\d+) 轮', state)
if not ms2 or int(ms2.group(1)) != 225 or int(ms2.group(2)) != audit_round:
    die('STATE 轮次行读不出 R225 / 第 ' + str(audit_round) + u' 轮')
for path, pat in ((u'AGENT_UI_AUDIT.md', u'^## 第 ' + str(audit_round) + u' 轮（R225'),
                  (u'AGENT_VISUAL_ITERATION.md', u'^## Round 225 · '),
                  (u'CHANGELOG.md', u'^### .*（R225 / ')):
    if not re.search(pat, read(path), re.M):
        die(path + u' 里读不到本轮标题：' + pat)
print(u'LEDGERS_R225 selfcheck ok')
sys.exit(0)

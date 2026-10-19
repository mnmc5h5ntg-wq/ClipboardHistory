# -*- coding: utf-8 -*-
"""R218 的台账生成器：235 结案、237 的成因由 runner 正文签死、venv 修法落地。

规矩同 R217：数字全部从本轮真实日志解析；插入用切片；写盘前"把新块原样抠掉必须等于旧文件"；
七维度名从上一节读；编号从台账正则取 max+1。缺任何一格读数就拒绝写盘。
"""
import io, os, re, subprocess, sys

ROOT = '/Users/wangziyi/Codex_Project0'
DAY = '2026-10-19'
NOW = '2026-10-19 22:15'
RUN = '39262764467'


def read(p):
    return io.open(os.path.join(ROOT, p), encoding='utf-8').read()


def write(p, t):
    with io.open(os.path.join(ROOT, p), 'w', encoding='utf-8') as h:
        h.write(t)


def die(why):
    print('LEDGERS_R218 refused: ' + why)
    sys.exit(1)


def log(p):
    path = os.path.join('/tmp', p)
    if not os.path.exists(path):
        die('缺少本轮日志 ' + path + ' ⇒ 不许写台账')
    return io.open(path, encoding='utf-8', errors='replace').read()


# ——————————————————— 读数 ———————————————————

ev = log('r218_evidence.log')
if 'externally-managed-environment' not in ev:
    die('runner 正文里没有 externally-managed-environment ⇒ 237 的成因没签住，不许写成"已定位"')
if 'PILLOW_INSTALL_FAILED' not in ev:
    die('runner 正文里没有 PILLOW_INSTALL_FAILED 那行 echo ⇒ 装失败与"没跑"分不开')
m = re.search(r'LEFT_AXIS_CI verdict=(\w+) reason=([\w-]+) hard=(\d+) not_run=(\d+) '
              r'missing_frames=(\d+) probes=(\d+)', ev)
if not m:
    die('读不到 runner 自己印的 LEFT_AXIS_CI 结论行')
verdict, reason, hard, not_run, missing, probes = m.groups()
if verdict != 'unavailable':
    die('runner 那一跑的出口是 ' + verdict + u'，与本轮要写的账不符 ⇒ 重读，别照抄')

st = log('r218_selftest.log')
if 'LEFT_AXIS_SELFTEST ok' not in st:
    die('尺的自检没绿 ⇒ 本轮不许写"尺本身没坏"')

bat = log('r218_battery1.log')
mb = re.search(r'Ran (\d+) tests in [\d.]+s', bat)
if not mb or re.search(r'^(FAILED|ERROR)', bat, re.M):
    die('电池不绿 ⇒ 先修再写台账')
ran = int(mb.group(1))
if 'OK' not in bat:
    die('电池日志里读不到 OK 行')

yaml_log = log('r218_yaml.log')
yaml_ran = 'YAML_OK' in yaml_log
yaml_note = (u'YAML 静态解析：本机有 PyYAML，已跑' if yaml_ran else
             u'YAML 静态解析 NOT-RUN：本机没有 PyYAML（ModuleNotFoundError），'
             u'结构证人换成仓库自己的 ci.yml 形状守卫 + 电池 ' + str(ran) + u' 格 OK')

# 帧：本轮 0 像素改动 ⇒ 沿用上一遍，但"沿用"要先证明那批帧还在盘上
prev = log('r217_baseline.log')
mp = re.search(r'FRAME_BASELINE_COMPARED=(\d+)', prev)
if not mp:
    die('读不到上一遍的帧数')
prev_frames = int(mp.group(1))
frames_on_disk = len([f for f in os.listdir('/tmp/shots_r217') if f.endswith('.png')]) if os.path.isdir('/tmp/shots_r217') else 0
if frames_on_disk < prev_frames:
    die('/tmp/shots_r217 只剩 ' + str(frames_on_disk) + u' 张，不足 ' + str(prev_frames) +
        u' ⇒ 「沿用上一遍」是空对账，看图腿要记 NOT-RUN 且不引用帧数')

diff = subprocess.run(['git', 'diff', '--name-only', 'HEAD'], cwd=ROOT,
                      stdout=subprocess.PIPE).stdout.decode('utf-8', 'replace')
changed = [p for p in diff.splitlines() if p.strip()]
prod = [p for p in changed if p.startswith('ClipboardHistory/Sources/')]
ci = [p for p in changed if p.startswith('.github/workflows/')]
if len(ci) != 1:
    die('本轮要改的正好是 1 个 workflow 文件，实得 ' + str(len(ci)) + u' ⇒ 对象不明')

# 连续几轮 0 产品文件：从 git 数，不手抄（R89 的"台账里的数字不许手抄"）
def product_streak():
    commits = subprocess.run(
        ['git', 'log', '-40', '--pretty=%H'], cwd=ROOT,
        stdout=subprocess.PIPE).stdout.decode('utf-8', 'replace').split()
    n = 0
    for sha in commits:
        files = subprocess.run(
            ['git', 'show', '--name-only', '--pretty=format:', sha], cwd=ROOT,
            stdout=subprocess.PIPE).stdout.decode('utf-8', 'replace').splitlines()
        if any(f.startswith('ClipboardHistory/Sources/') for f in files if f.strip()):
            break
        n += 1
    return n


STREAK = product_streak() + 1   # +1 是本轮自己（还没提交）

# ——————————————————— 编号 ———————————————————

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
this_round = max([int(x) for x in re.findall(r'^## Round (\d+) · ', it, re.M)]) + 1
audit_round = this_round + 2
last_block = it[it.rindex('## Round ' + str(this_round - 1) + ' · '):]
dim_rows = re.findall(r'^\|([^|]+)\|\s*(\d+)/15\s*\|', last_block, re.M)
if len(dim_rows) != 7:
    die('上一节的七维度行数是 ' + str(len(dim_rows)) + u'（要 7）')
dims = [d.strip() for d, _ in dim_rows]

TITLE = u'235 结案成「接线对、runner 没 Pillow」，237 的成因由 runner 正文签死并换成一次性 venv'
SCOPE = u'CI 1 文件，产品 ' + str(len(prod)) + u' 文件'

CI_STEP = 'Surface left-axis ruler (BACKLOG 234, wired in R210; venv interpreter in R218)'

UI_NEW = u'''## 第 {AR} 轮（R218 · {DAY}）：{TITLE}（U-{U1}…U-{U3} · {SCOPE}）

- **U-{U1}：235 结案，但结的是"接线正确"而不是"runner 判过产品"。**
  runner 自己印的结论行（run `{RUN}`，步骤 `{STEP}`）：
  `LEFT_AXIS_CI verdict={V} reason={RS} hard={H} not_run={NR} missing_frames={MF} probes={PR}`。
  出口处置完全按 R210 设计工作：环境缺席 ⇒ `unavailable` + exit 0，**没有**被报成产品结论。
  但 `probes=0` 要说白：那把尺至今**没在 runner 上判过一次产品像素**，235 不许写成"runner 已验收"。
  同跑 `STEP[8]`/`STEP[15]` 全绿（job `completed success`）⇒ R216 修的两朵红在 runner 上确认消失。
- **U-{U2}：237 的成因由 runner 的正文签死，不是我的猜测；修法换成一次性 venv。**
  正文：`error: externally-managed-environment` + `PILLOW_INSTALL_FAILED=1`（PEP 668 的机器闸门），
  于是 `python3 -m pip install pillow` 从来没装成过。R217 我在 STATE 的 ⓪ 里猜的是
  "装 python 的那台解释器和下一步是不是同一个" —— **这条猜测被正文否证并已撤回**（真因是同一台解释器拒绝被装）。
  修法：`python3 -m venv /tmp/pilenv` + 装进 venv + 下一步**显式**用 `/tmp/pilenv/bin/python` 跑；
  三种成因分三条 echo（`PILLOW_VENV_FAILED` / `PILLOW_INSTALL_FAILED` / `PILLOW_IMPORT_FAILED`），
  下次再读就不用猜。**不用 `--break-system-packages`**：那要动作业机器的系统解释器，提成 {ND}。
- **U-{U3}：验证边界要写清 —— YAML 静态解析没跑，结构证人换成了仓库自己的守卫。**
  {YNOTE}；尺的自检 `LEFT_AXIS_SELFTEST ok`（7 格真值表，本轮没动 python 侧）；
  步骤改名后那条接线守卫（`test_surface_left_axes.py` 按子串 `Surface left-axis ruler` 认）仍咬得住，已实测；
  电池 `Ran {RAN} tests ... OK`（台账落盘之前先跑过一遍，落盘之后还要再跑一遍）。
  **runner 能不能真装上 pillow 仍是未读**（要下一跑）⇒ 237 不写结案，只写"修法落地、待 runner 验收"，
  并把"电池那一步仍用系统解释器 ⇒ 判据卷里 NEEDS_PIL 的格子在 runner 上恒 skip"开成 {NB}。
  看图腿本轮 NOT-RUN：0 个像素改动、无新帧（盘上那 {PF} 张是 R217 那一遍的，不替本轮作证）。

其余读数：产品文件 {PROD} 个、workflow 文件 {CIN} 个 ⇒ 无需换装本机；帧沿用上一遍（{PF} 张在盘上）。

'''.format(AR=audit_round, DAY=DAY, TITLE=TITLE, U1=U1, U2=U2, U3=U3, SCOPE=SCOPE, RUN=RUN,
           STEP=CI_STEP, V=verdict, RS=reason, H=hard, NR=not_run, MF=missing, PR=probes,
           ND=NEW_D, YNOTE=yaml_note, RAN=ran, NB=NEW_B, PF=prev_frames,
           PROD=len(prod), CIN=len(ci))

SCORES = {dims[0]: 6, dims[1]: 13, dims[2]: 13, dims[3]: 7,
          dims[4]: 13, dims[5]: 13, dims[6]: 12}
dim_table = '\n'.join([u'| ' + d + u' | ' + str(SCORES[d]) + u'/15 |' for d in dims])
TOTAL = sum(SCORES.values())

IT_BLOCK = u'''
## Round {TR} · {TITLE}（{DAY} · {SCOPE}）

开场读数来自 R217 收尾时那一跑：`610e93c` = run `{RUN}` **completed success** ⇒ R216 修掉的两朵红在 runner 上确认消失；
同跑 `{STEP}` 打的是 `LEFT_AXIS_CI verdict={V} reason={RS} probes={PR}`。
235 因此结成一个**受限**的案子：出口处置按设计工作（环境缺席没有被报成产品结论），但 `probes=0` 说明那把尺
在 runner 上**一次产品像素都没判过** —— 我把这条写进账，而不是写成"CI 已验收"。

237 的成因是 runner 正文自己签的：`error: externally-managed-environment` + `PILLOW_INSTALL_FAILED=1`。
R217 我在 STATE 的 ⓪ 里写过一句猜测（"装的和用的可能不是同一台解释器"），**这句被正文否证**：
是同一台解释器按 PEP 668 拒绝被装。修法因此不是换 `python3` 的路径，而是开一次性 venv，
下一步显式用 `/tmp/pilenv/bin/python`；三种成因（venv 建不起来 / 装失败 / 装了 import 不到）分三条 echo。
拒用 `--break-system-packages`：一把像素尺不该去动作业机器的系统解释器（提成 {ND}）。

诚实边界：本机没有 PyYAML ⇒ 我**没能**静态解析这份 workflow（{YNOTE}），结构证人只有仓库自己的 `test_ci_workflow_shape.py`
+ 电池 `Ran {RAN} tests OK`，以及"接线守卫按子串认步骤名、改名后仍咬得住"这一格实测。
runner 真装上 pillow 没有，要下一跑才知道 ⇒ 237 只写"修法落地、待验收"。
看图腿 NOT-RUN：本轮 0 像素改动、无新帧，盘上那 {PF} 张是 R217 的，不替本轮作证。

本轮是连续第 {STREAK} 笔 0 产品改动的提交（由 `git log` 数出来，含补账那一类笔），七维里"真实视觉审查"和"产品面推进"两格因此只有 {S0}+{S3}。
下一轮（R219）的靶把**动效位点本体**提到 ①：清账表里还有未判的格子，220 那条键盘可达性在等真机或授权。

七维度自评：

| 维度 | 得分 |
|---|---|
{DIMTABLE}

总分 {TOTAL}/105（{TR} 轮）。GAPS=none
'''.format(TR=this_round, TITLE=TITLE, DAY=DAY, SCOPE=SCOPE, RUN=RUN, STEP=CI_STEP,
           V=verdict, RS=reason, PR=probes, ND=NEW_D, YNOTE=yaml_note, RAN=ran,
           PF=prev_frames, TOTAL=TOTAL, DIMTABLE=dim_table, STREAK=STREAK,
           S0=SCORES[dims[0]], S3=SCORES[dims[3]])

CH_BLOCK = u'''### 235 结案（受限）+ 237 的成因由 runner 正文签死并换成一次性 venv（R{R} / U-{U1}…U-{U3} · {SCOPE}）

- runner run `{RUN}`（commit `610e93c`）**completed success**：R216 修的 `STEP[8]`/`STEP[15]` 两朵红确认消失。
- 同跑 `{STEP}` 打 `LEFT_AXIS_CI verdict={V} reason={RS} probes={PR}` ⇒ 235 结案成"接线正确、
  但尺在 runner 上没判过产品像素"（`probes=0` 明写，不写成已验收）。
- 237 真因：`error: externally-managed-environment`（PEP 668）—— 不是"两台解释器"，
  R217 写在 STATE ⓪ 的那句猜测已撤回。修法：一次性 venv + 下一步显式用 venv 解释器，
  三种成因三条 echo；拒用 `--break-system-packages`（**D-{ND}**）。
- 边界：{YNOTE}；电池 `Ran {RAN} tests OK`；看图腿 NOT-RUN（0 像素改动、无新帧）。
- 新开 {NB}：判据卷（`STEP[8]`）仍用系统解释器 ⇒ NEEDS_PIL 那几格在 runner 上恒 skip。

'''.format(R=218, U1=U1, U3=U3, SCOPE=SCOPE, RUN=RUN, STEP=CI_STEP, V=verdict, RS=reason,
           PR=probes, ND=NEW_D, YNOTE=yaml_note, RAN=ran, NB=NEW_B)

STATE_BLOCK = u'''最后更新：{NOW}（本地 · R218 / 第 {AR} 轮：**{TITLE}**（U-{U1}…U-{U3} · {SCOPE}）

**本轮落地**：`610e93c`=`39262764467` **completed success** ⇒ R216 修的两朵红在 runner 上消失；
同跑左轴那一步打 `LEFT_AXIS_CI verdict={V} reason={RS} probes={PR}` ⇒ **235 结案成"接线正确、runner 没判过产品像素"**（probes=0 明写）。
237 的真因由 runner 正文签：`error: externally-managed-environment`（PEP 668）+ `PILLOW_INSTALL_FAILED=1`，
R217 我猜的"两台解释器"**已撤回**；修法换成一次性 venv + 下一步显式用 venv 解释器，三种成因三条 echo，
拒用 `--break-system-packages`（**D-{ND}**）。新开 {NB}：判据卷仍用系统解释器 ⇒ NEEDS_PIL 的格子在 runner 上恒 skip。
验证边界：{YNOTE}；尺自检 `LEFT_AXIS_SELFTEST ok`；电池 `Ran {RAN} tests OK`（台账落盘后还要再跑）；
看图腿 NOT-RUN（0 像素改动、无新帧，盘上 {PF} 张属 R217）；产品 0 文件 ⇒ 未换装本机。
CI：本跑（venv 修法）+ `193d5be`=39265858795、`1462b38`=39265952407 仍 in_progress ⇒ 未读不算绿。

**下一轮（R219）的靶**：⓪ 读 venv 那一跑：`PILLOW_OK <版本>` 有没有露面、左轴那一步是否从 `unavailable` 变成 `ok/skipped/red`（**237 结案的唯一通道**）、`193d5be`/`1462b38` 的结论；
① **回到动效位点本体**（已经连续 {STREAK} 笔 0 产品改动）：清账表里未判的格子挑一位点真做动效 + 帧 + 刀，别再交判据账；
② 243：捕帧通道能不能等到 `.task`（先 spike，别改产品）；③ 227③、222、215、201/202、207；④ 220 路 A、228② 等用户。
)

'''.format(NOW=NOW, AR=audit_round, TITLE=TITLE, U1=U1, U3=U3, SCOPE=SCOPE, V=verdict,
           RS=reason, PR=probes, ND=NEW_D, NB=NEW_B, YNOTE=yaml_note, RAN=ran, PF=prev_frames,
           STREAK=STREAK)

BL_BLOCK = u'''
**235 追记（R218 结案·受限）：runner 那一跑读到了，出口按设计工作，但尺没判过产品像素**

`610e93c` = run `39262764467`（`completed success`）里 `{STEP}` 打的正文：
`LEFT_AXIS_CI verdict={V} reason={RS} hard={H} not_run={NR} missing_frames={MF} probes={PR}`。
本条问的是"接线在 runner 上到底怎么处置"，答案：环境缺席 ⇒ `unavailable` + exit 0，没被报成产品结论 ⇒ **结案**。
但结案的范围要写死：`probes=0` 意味着那把尺**从未在 runner 上判过一张产品像素**，
"runner 已验收"这句话不成立；那一半移交 {NB} 与 237（pillow 装上之后重读才算）。

**237 追记（R218 成因签死·修法落地待 runner 验收）**

真因不是"两台解释器"，是同一台按 PEP 668 拒绝被装：正文 `error: externally-managed-environment`
+ `PILLOW_INSTALL_FAILED=1`（run `39262764467`）。R217 我写在 STATE ⓪ 的那句猜测已撤回。
修法（已入库）：`python3 -m venv /tmp/pilenv` ⇒ 装进 venv ⇒ 下一步**显式**用 `/tmp/pilenv/bin/python` 跑尺；
三条 echo 分开三种成因（venv 建不起来 / 装失败 / 装了 import 不到）。
仍欠：venv 那台解释器在 runner 上能不能真装上 pillow（下一跑读 `PILLOW_OK <版本>` 与新的 `LEFT_AXIS_CI`）。

**{NB}. 判据卷（`STEP[8]`）仍用系统解释器：装了 pillow 的 venv 只对左轴那一步生效，NEEDS_PIL 的格子在 runner 上恒 skip（R218 开单）**

R218 把 pillow 装进 `/tmp/pilenv`，并让 `{STEP}` 显式用那台解释器 —— 但 `Release script tests`（脚本电池）
仍跑系统 `python3`，于是 `scripts/tests/test_surface_left_axes.py` 里 `@NEEDS_PIL` 那几格在 runner 上继续 skip。
后果：**像素判据的自检真值表在 CI 上从未执行过**，只有本机跑过。
要不要把电池整体搬进 venv 是个决定，不是显然：搬了以后"CI 上的 skip"会从"环境缺席"变成"环境有"，
那几格第一次在 runner 上真判 ⇒ 可能立刻冒出新的红（R154 那一族）。先做的实验：只把带 `NEEDS_PIL` 的那一支
单独用 venv 解释器跑一遍，看它在 runner 上给什么结论，再决定要不要整体搬。
适用面：所有 `@NEEDS_PIL` 守卫的格子；不适用：不需要像素的那些（它们本来就在系统解释器上跑）。

'''.format(STEP=CI_STEP, V=verdict, RS=reason, H=hard, NR=not_run, MF=missing, PR=probes, NB=NEW_B)

DE_BLOCK = u'''
**D-{ND}（R218）：判据不许为了让 CI 变绿去动作业机器的系统解释器 —— 要装依赖就开一次性 venv**

现场：runner 上 `python3 -m pip install pillow` 被 PEP 668 挡下（正文 `error: externally-managed-environment`），
pip 自己给的出路是 `--break-system-packages`。那条路能让这一步变绿，代价是把 GitHub 作业机器（本机则是任何
跑这套 workflow 的机器）的系统 Python 改了 —— 一把像素尺的验收不该要这种副作用，而且它会污染同一次运行里
**其它**步骤的环境（同一台机器上后面还有 swift 卷与电池卷在读）。
规矩：① 判据需要第三方库时，装进一次性 venv（`python3 -m venv /tmp/<name>`），
需要那台解释器的步骤**显式**用它的绝对路径，别指望 PATH；
② 三种"装不上"要分三条读数（venv 建不起来 / pip 装失败 / 装了 import 不到），否则下一轮又要猜；
③ 换 venv 只解决"那一步"的环境，其它步骤仍是系统解释器 ⇒ 由此产生的 skip 要另开一条账（本轮 {NB}），
不许顺手写成"CI 已经有 pillow"。
适用面：所有需要在 runner 上装第三方库的判据步骤；不适用：仓库自带、无需安装的纯标准库判据。
'''.format(ND=NEW_D, NB=NEW_B)

# ——————————————————— 事务性写盘 ———————————————————

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
        die('锚点找不到：' + path + ' ｜ ' + anchor[:60])
    if text.find(anchor, idx + 1) >= 0:
        die('锚点不唯一：' + path + ' ｜ ' + anchor[:60])
    new = text[:idx] + block + text[idx:]
    DELTAS[path] = block
    if new.count(block) != 1 or not reinsertion_matches(text, new, path):
        die('插入还原失败：' + path)
    plans.append((path, text, new))


def plan_insert_where(path, pattern, block, expect_contains):
    text = read(path)
    m = re.search(pattern, text, re.M)
    if not m:
        die('形状找不到：' + path + ' ｜ ' + pattern)
    line = text[m.start():text.find('\n', m.start())]
    if expect_contains not in line:
        die('第一格不是上一轮那一格：' + path + ' ｜ ' + line[:70])
    new = text[:m.start()] + block + text[m.start():]
    if new.count(block) != 1:
        die('插入块不唯一：' + path)
    DELTAS[path] = block
    plans.append((path, text, new))


def plan_append(path, block):
    text = read(path)
    if not text.endswith('\n'):
        text = text + '\n'
    new = text + block.strip('\n') + '\n'
    if not new.startswith(text):
        die('追加会改动旧内容：' + path)
    plans.append((path, text, new))


plan_insert('AGENT_UI_AUDIT.md', u'## 第 ' + str(audit_round - 1) + u' 轮（R217 · ', UI_NEW)
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
plan_insert_where('AGENT_STATE.md', u'^最后更新：', STATE_BLOCK, u'R217 / 第 219 轮')
plan_append('AGENT_BACKLOG.md', BL_BLOCK)
plan_append('AGENT_DECISIONS.md', DE_BLOCK)

for path, old, new in plans:
    if len(new.splitlines()) <= len(old.splitlines()):
        die('写盘前最后一道：' + path + u' 行数没增加')
    if not reinsertion_matches(old, new, path):
        die('写盘前最后一道：' + path + u' 抠掉新块后不等于旧文件 ⇒ 有旧行被吃掉')

for path, old, new in plans:
    write(path, new)

print(u'LEDGERS_R218 wrote %d files' % len(plans))
print(u'LEDGERS_R218 编号：第 %d 轮 / Round %d / U-%d…U-%d / BACKLOG +%d / D-%d'
      % (audit_round, this_round, U1, U3, NEW_B, NEW_D))
print(u'LEDGERS_R218 读数：runner %s/%s probes=%s、电池 %d 格 OK、帧沿用 %d、产品 %d、workflow %d'
      % (verdict, reason, probes, ran, prev_frames, len(prod), len(ci)))
print(u'LEDGERS_R218 边界：' + yaml_note)

state = read('AGENT_STATE.md')
mm = re.search(u'最后更新：[^\\n]*?R(\\d+) / 第 (\\d+) 轮', state)
if not mm or int(mm.group(1)) != 218 or int(mm.group(2)) != audit_round:
    die('STATE 的轮次行读不出 R218 / 第 ' + str(audit_round) + u' 轮')
for path, pat in ((u'AGENT_UI_AUDIT.md', u'^## 第 ' + str(audit_round) + u' 轮（R218'),
                  (u'AGENT_VISUAL_ITERATION.md', u'^## Round 218 · '),
                  (u'CHANGELOG.md', u'^### .*（R218 / ')):
    if not re.search(pat, read(path), re.M):
        die(path + u' 里读不到本轮标题：' + pat)
print(u'LEDGERS_R218 selfcheck ok')
sys.exit(0)

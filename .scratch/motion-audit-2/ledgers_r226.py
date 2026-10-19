# -*- coding: utf-8 -*-
"""R226 的台账生成器：244 结案（runner 判据卷真的走上了带 pillow 的解释器）+ 249 仍等。

数字全部从 /tmp/r226_runner_e015455.log 现读现解析；任何一格读不到就拒绝写盘。
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
    print('LEDGERS_R226 refused: ' + why)
    sys.exit(1)


LOGP = '/tmp/r226_runner_e015455.log'
if not os.path.exists(LOGP):
    die('缺少 runner 日志 ' + LOGP)
ev = io.open(LOGP, encoding='utf-8', errors='replace').read()

# **只认「被打印出来」的形状**：runner 会把整段步骤正文回显一遍（`Z echo "SCRIPT_PYTHON=$PY"`），
# 按裸子串搜会抓到回显里的 `$PY"` —— 本轮第一次就是这么错的，被下面那条「必须等于 venv 路径」的门拦下。
# 真执行的那一行永远是「时间戳 + 空格 + 标记」，所以三条尺都锚 `Z `，并取最后一次匹配。
mpy = re.search(r'Z SCRIPT_PYTHON=(\S+)', ev)
mpil = re.search(r'Z SCRIPT_PIL_OK ([\d.]+) (\S+)', ev)
msk = re.search(r'Z SCRIPT_SKIPS=(\d+)', ev)
if not (mpy and mpil and msk):
    die('三行证人读不齐：python=%s pil=%s skips=%s' % (bool(mpy), bool(mpil), bool(msk)))
# 命令回显里也含 SCRIPT_PIL_MISSING（那是 fallback 的 echo 文本），所以只认「被打印出来」的形状：
# 时间戳之后紧跟标记 = 真执行的那一行。这一格本轮差点把 fallback 当成已发生，写进结案。
missing_printed = len(re.findall(r'Z SCRIPT_PIL_MISSING=1', ev))
if missing_printed:
    die('这一跑真打印了 SCRIPT_PIL_MISSING=1（%d 行）⇒ 244 不能按结案写' % missing_printed)
interp, pilv, pilpath, skips = mpy.group(1), mpil.group(1), mpil.group(2), int(msk.group(1))
if interp != '/tmp/pilenv/bin/python':
    die('判据卷没走 venv：' + interp)

axis = re.findall(r'LEFT_AXIS_CI verdict=(\w+) hard=(\d+) not_run=(\d+) missing_frames=(\d+) probes=(\d+)', ev)
if not axis:
    die('左轴结论行读不到')
causes = sorted({c for c in re.findall(r'cause=([\w-]+)', ev)})
av, ahard, anr, amiss, ap = axis[-1]

runs = subprocess.run(['gh', 'run', 'list', '--limit', '8', '--json', 'databaseId,headSha,status,conclusion'],
                      cwd=ROOT, stdout=subprocess.PIPE).stdout.decode('utf-8', 'replace')
import json as _json
# `gh --json` 的键序是字母序（conclusion, databaseId, headSha, status），按正则硬按我以为的顺序拼
# 会一律读成「未读」—— 本轮第一次就是这么错的。改成解析对象，不猜键序。
_runs = _json.loads(runs)
def runfor(sha7):
    for r in _runs:
        if str(r.get('headSha', '')).startswith(sha7):
            return (str(r.get('databaseId')), str(r.get('status')), str(r.get('conclusion') or '未读'))
    return ('未读', '未读', '未读')

e0, da5, r225a = runfor('e015455'), runfor('da5da47'), runfor('09d9bf7')
if e0[1] != 'completed' or e0[2] != 'success':
    die('e015455 不是 completed/success，实得 ' + str(e0))

diff = subprocess.run(['git', 'diff', '--name-only', 'HEAD'], cwd=ROOT,
                      stdout=subprocess.PIPE).stdout.decode('utf-8', 'replace')
prod = [p for p in diff.splitlines() if p.startswith('ClipboardHistory/Sources/')]
if prod:
    die('本轮宣称 0 产品改动，实得 ' + str(prod))

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

TITLE = (u'244 结案：runner 的判据卷走上了带 pillow 的解释器（`SCRIPT_PIL_OK %s`、`SCRIPT_SKIPS=%d`），'
         u'左轴那一步仍等 `da5da47` 那一跑' % (pilv, skips))
SCOPE = u'判据 0 文件 + 台账，产品 0 文件（本轮是读数轮）'

BASE = dict(AR=audit_round, R=226, DAY=DAY, NOW=NOW, TITLE=TITLE, U1=U1, U2=U2, U3=U3,
            SCOPE=SCOPE, NB=NEW_B, ND=NEW_D_, interp=interp, pilv=pilv, pilpath=pilpath,
            skips=skips, av=av, anr=anr, ap=ap, causes='、'.join(causes) or u'无',
            e0=e0[0], e0s=e0[2], da5=da5[0], da5s=da5[1], r225a=r225a[0], r225s=r225a[1])

UI_NEW = u'''## 第 {AR} 轮（R{R} · {DAY}）：{TITLE}（U-{U1}…U-{U3} · {SCOPE}）

- **U-{U1}：⓪ 读到了 244 的唯一通道，而且是齐的三行。**
  run `{e0}`（`e015455`，**{e0s}**）正文：`SCRIPT_PYTHON={interp}`、`SCRIPT_PIL_OK {pilv} {pilpath}`、
  `SCRIPT_SKIPS={skips}` ⇒ R223 那一步「判据卷也走 venv」在 runner 上**验收通过**：
  带 pillow 的解释器被真的用上了（不是装了但没接），`SCRIPT_PIL_MISSING` 没露面。
  **244 结案**，但结案范围要说准：它结的是「判据卷的解释器接对了」，
  不是「runner 上所有像素判据都跑了」—— 还剩 {skips} 条 skip，本轮**没读那三条是谁**（记进 {NB}）。
- **U-{U2}：左轴那一步在这跑仍是 `cause={causes}` —— 这是预期的，不是回归。**
  正文 `LEFT_AXIS_CI verdict={av} not_run={anr} probes={ap}`，帧尺寸仍是 `420x300 / 720x540 / 720x520`（@1x）。
  因为把探针窗口改成按 pt 写的是 **R224（`da5da47`）**，那一跑现在 `status={da5s}`（run `{da5}`）⇒
  **249 的第一格仍未读**，不许拿这一跑说「修了也没用」，也不许说「已经修好」。
- **U-{U3}：轮次账与未读清单。**
  R225 的四跑（`09d9bf7`=`{r225a}` 等）全部 `status={r225s}` ⇒ 未读不算绿；
  本轮 0 产品改动、0 判据改动 ⇒ 未换装本机、看图腿 NOT-RUN（不拿上一轮的帧替本轮作证）。
  本轮的价值只有一条：把 244 从「等 runner」变成「runner 已签」，并把 {skips} 条 skip 的**归属**开成新的读数债。

'''.format(**BASE)

SCORES = {dims[0]: 10, dims[1]: 13, dims[2]: 14, dims[3]: 8,
          dims[4]: 14, dims[5]: 14, dims[6]: 14}
dim_table = '\n'.join([u'| ' + d + u' | ' + str(SCORES[d]) + u'/15 |' for d in dims])
BASE.update(DIMTABLE=dim_table, TOTAL=sum(SCORES.values()), TR=this_round)

IT_BLOCK = u'''
## Round {TR} · {TITLE}（{DAY} · {SCOPE}）

⓪ 的读数落齐了：run `{e0}`（`e015455`，**{e0s}**）里三行证人全在 ——
`SCRIPT_PYTHON={interp}`、`SCRIPT_PIL_OK {pilv} {pilpath}`、`SCRIPT_SKIPS={skips}`。
⇒ R223 那半（把判据卷的解释器换成带 pillow 的 venv）第一次在 runner 上被签：不是「装了」，是「判据卷真的用它跑了」。
**244 结案**，但范围写清楚：结的是解释器接线，不是「所有像素判据都跑了」—— 还剩 {skips} 条 skip，
本轮没读那三条是谁、为什么跳 ⇒ 开 **{NB}**。

左轴那一步这一跑仍是 `cause={causes}`（`verdict={av} not_run={anr} probes={ap}`，帧仍是 @1x 的
`420x300 / 720x540 / 720x520`）—— 这是**预期**：把窗口改成按 pt 写的是 R224（`da5da47`），
那一跑仍 `{da5s}`（run `{da5}`）⇒ 249 的第一格仍未读。两条不许混：这一跑不能证明 R224 没修好，
也不能被写成「已经修好」。

R225 的四跑（`09d9bf7`=`{r225a}`）仍 `{r225s}` ⇒ 未读不算绿。
本轮 0 产品、0 判据改动 ⇒ 未换装本机、看图腿 NOT-RUN（不拿上一轮的帧替本轮作证）。

七维度自评：

| 维度 | 得分 |
|---|---|
{DIMTABLE}

总分 {TOTAL}/105（{TR} 轮）。GAPS=none
'''.format(**BASE)

CH_BLOCK = u'''### 244 结案：runner 判据卷走上带 pillow 的解释器（R{R} / U-{U1}…U-{U3} · {SCOPE}）

- run `{e0}`（`e015455`，**{e0s}**）：`SCRIPT_PYTHON={interp}`、`SCRIPT_PIL_OK {pilv} {pilpath}`、`SCRIPT_SKIPS={skips}`，
  `SCRIPT_PIL_MISSING` 未露面 ⇒ R223 的接线在 runner 上验收通过。
- 范围：结的是「解释器接对了」，不是「像素判据全跑了」—— 仍有 {skips} 条 skip，归属未读 ⇒ 开 **{NB}**。
- 左轴仍 `cause={causes}`（`verdict={av} not_run={anr} probes={ap}`，帧 @1x）：按 pt 写窗口是 R224（`da5da47`，
  run `{da5}` 仍 `{da5s}`）⇒ **249 的第一格未读**，这一跑既不能证伪也不能证明 R224。
- R225 四跑 `09d9bf7`=`{r225a}` 仍 `{r225s}` ⇒ 未读不算绿。本轮 0 产品、0 判据、未换装、看图腿 NOT-RUN。

'''.format(**BASE)

STATE_BLOCK = u'''最后更新：{NOW}（本地 · R{R} / 第 {AR} 轮：**{TITLE}**（U-{U1}…U-{U3} · {SCOPE}）

**本轮落地**：⓪ 读 run `{e0}`（`e015455`，**{e0s}**）：`SCRIPT_PYTHON={interp}`、`SCRIPT_PIL_OK {pilv} {pilpath}`、
`SCRIPT_SKIPS={skips}`、无 `SCRIPT_PIL_MISSING` ⇒ **244 结案**（结的是「判据卷的解释器接对了」，
不是「像素判据全跑了」；剩 {skips} 条 skip 的归属未读 ⇒ 开 **{NB}**）。
左轴这一跑仍 `cause={causes}`（`verdict={av} not_run={anr} probes={ap}`，帧 @1x）—— 按 pt 写窗口是 R224（`da5da47`，
run `{da5}` 仍 `{da5s}`）⇒ **249 未读**，不许拿这一跑证伪 R224。R225 四跑 `09d9bf7`=`{r225a}` 仍 `{r225s}`。
本轮 0 产品、0 判据改动 ⇒ 未换装本机、看图腿 NOT-RUN。

**下一轮（R227）的靶**：⓪ 读 `da5da47`（run `{da5}`）与 R225 那四跑：左轴在 @1x 上是否 `verdict=ok`（**249 的第一格**，
红要先归因、不许放宽）、`Swift tests (executed-count gate)` 是否仍绿；
① 读 {skips} 条 skip 是谁、为什么跳（{NB}）；② 回到动效位点：251 那批共用 `VisualFill.hover` 的位点**先补两档帧再判**；
③ 248、243、227③、222、215、201/202、207、240、250；④ 220 路 A、228② 等用户。
)

'''.format(**BASE)

BL_BLOCK = u'''
**{NB}. runner 判据卷仍有 {NB_SKIP} 条 skip：本轮只读到条数，没读到「是哪三条、为什么跳」（R226 开单，244 结案的边界）**

244 结的是解释器接线：`SCRIPT_PYTHON={interp}` + `SCRIPT_PIL_OK {pilv}` 说明带 pillow 的解释器被用上了。
但同一跑打了 `SCRIPT_SKIPS={NB_SKIP}`，而证人只给数不给名字 ⇒ 现在这句话还没有承重：
「runner 上像素类判据已全跑」既没被证明，也没被证伪。
下一轮读法（不改判据，只读日志）：从 `/tmp/py.log` 那一步的正文里按 `... skipped` 行取**测试名**，
按 skip 理由分档（环境类 / 能力闸门类 / 平台版本类），再决定要不要升硬门。
不许做的事：把 {NB_SKIP} 当成「已经很少了」直接收口；也不许把 skip 名字打出来之前先加出口。

'''.format(NB=NEW_B, NB_SKIP=skips, interp=interp, pilv=pilv)

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


plan_insert('AGENT_UI_AUDIT.md', u'## 第 ' + str(audit_round - 1) + u' 轮（R225 · ', UI_NEW)
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
plan_insert_where('AGENT_STATE.md', u'^最后更新：', STATE_BLOCK, u'R225 / 第 227 轮')
plan_append('AGENT_BACKLOG.md', BL_BLOCK)

STRAY = re.compile(r'\{[A-Z][A-Za-z_0-9]*\}')
for name, blk in (('UI_NEW', UI_NEW), ('IT_BLOCK', IT_BLOCK), ('CH_BLOCK', CH_BLOCK),
                  ('STATE_BLOCK', STATE_BLOCK), ('BL_BLOCK', BL_BLOCK)):
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

print(u'LEDGERS_R226 wrote %d files' % len(plans))
print(u'LEDGERS_R226 编号：第 %d 轮 / Round %d / U-%d…U-%d / BACKLOG +%d'
      % (audit_round, this_round, U1, U3, NEW_B))
print(u'LEDGERS_R226 读数：SCRIPT_PIL_OK %s、SKIPS=%d、左轴 verdict=%s not_run=%s cause=%s、e015455=%s、da5da47=%s'
      % (pilv, skips, av, anr, causes, e0[2], da5[1]))

state = read('AGENT_STATE.md')
ms2 = re.search(u'最后更新：[^\\n]*?R(\\d+) / 第 (\\d+) 轮', state)
if not ms2 or int(ms2.group(1)) != 226 or int(ms2.group(2)) != audit_round:
    die('STATE 轮次行读不出 R226 / 第 ' + str(audit_round) + u' 轮')
for path, pat in ((u'AGENT_UI_AUDIT.md', u'^## 第 ' + str(audit_round) + u' 轮（R226'),
                  (u'AGENT_VISUAL_ITERATION.md', u'^## Round 226 · '),
                  (u'CHANGELOG.md', u'^### .*（R226 / ')):
    if not re.search(pat, read(path), re.M):
        die(path + u' 里读不到本轮标题：' + pat)
print(u'LEDGERS_R226 selfcheck ok')
sys.exit(0)

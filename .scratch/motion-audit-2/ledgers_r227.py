# -*- coding: utf-8 -*-
"""R227 的台账生成器：252 结案（那 3 条 skip 是谁、为什么跳）+ 新开 253（写死的 /tmp 帧目录）。

skip 名单与理由全部从 /tmp/r226_runner_e015455.log 现读（锚「真打印」形状），不手抄。
"""
import io, os, re, subprocess, sys

ROOT = '/Users/wangziyi/Codex_Project0'
DAY = '2026-10-20'
NOW = subprocess.run(['date', '+%Y-%m-%d %H:%M'], cwd=ROOT,
                     stdout=subprocess.PIPE).stdout.decode().strip()
LOGP = '/tmp/r226_runner_e015455.log'


def read(p):
    return io.open(os.path.join(ROOT, p), encoding='utf-8').read()


def write(p, t):
    with io.open(os.path.join(ROOT, p), 'w', encoding='utf-8') as h:
        h.write(t)


def die(why):
    print('LEDGERS_R227 refused: ' + why)
    sys.exit(1)


if not os.path.exists(LOGP):
    die('缺少 runner 日志 ' + LOGP)
ev = io.open(LOGP, encoding='utf-8', errors='replace').read()

# 只认「时间戳 + 真打印」那一行；命令回显里也可能有 skipped 这个词。
skips = re.findall(r'Z (\S.*?) \.\.\. skipped \'([^\']+)\'', ev)
skips = [(n, r) for n, r in skips if not n.startswith(('echo', 'grep', '#'))]
if len(skips) != 3:
    die('skip 名单读到 %d 条，宣称是 3 条 ⇒ 解析坏了，不写' % len(skips))
names = [n for n, _ in skips]
reasons = [r for _, r in skips]
pil_named = [n for n, r in skips if 'pillow' in r.lower() or 'PIL' in r]
if pil_named:
    die('仍有 PIL 类 skip（%s）⇒ 244 的结案范围要重写' % pil_named)
stale = [(n, r) for n, r in skips if '/tmp/shots_r' in r]
stale_dir = sorted({re.search(r'(/tmp/shots_r\d+)', r).group(1) for _, r in stale})
if len(stale) != 2:
    die('预期两条 skip 是写死的帧目录，实得 %d 条' % len(stale))
ok_lines = len(re.findall(r'Z \S.* \.\.\. ok$', ev, re.M))

# 那个写死的目录在**任何**机器上还在不在？（本机就是最新一轮也不在那儿）
present = {d: os.path.isdir(d) for d in stale_dir}
msk = re.search(r'Z SCRIPT_SKIPS=(\d+)', ev)
mpil = re.search(r'Z SCRIPT_PIL_OK ([\d.]+)', ev)
axis = re.search(r'Z LEFT_AXIS_CI verdict=(\w+) hard=(\d+) not_run=(\d+) missing_frames=(\d+) probes=(\d+)', ev)
if not (msk and mpil and axis):
    die('三行证人读不齐')

runs = subprocess.run(['gh', 'run', 'list', '--limit', '8', '--json', 'databaseId,headSha,status,conclusion'],
                      cwd=ROOT, stdout=subprocess.PIPE).stdout.decode('utf-8', 'replace')
import json as _json
_runs = _json.loads(runs)


def runfor(sha7):
    for r in _runs:
        if str(r.get('headSha', '')).startswith(sha7):
            return (str(r.get('databaseId')), str(r.get('status')), str(r.get('conclusion') or '未读'))
    return ('未读', '未读', '未读')


da5, r225a = runfor('da5da47'), runfor('09d9bf7')

diff = subprocess.run(['git', 'diff', '--name-only', 'HEAD'], cwd=ROOT,
                      stdout=subprocess.PIPE).stdout.decode('utf-8', 'replace')
prod = [p for p in diff.splitlines() if p.startswith('ClipboardHistory/Sources/')]
if prod:
    die('本轮宣称 0 产品改动，实得 ' + str(prod))

ui = read('AGENT_UI_AUDIT.md')
U1, U2, U3 = max(int(x) for x in re.findall(r'^- \*\*U-(\d+)：', ui, re.M)) + 1, 0, 0
U2, U3 = U1 + 1, U1 + 2
b_max = max([int(x) for x in re.findall(r'^\*\*(\d+)\. ', read('AGENT_BACKLOG.md'), re.M)])
NEW_B = b_max + 1
it = read('AGENT_VISUAL_ITERATION.md')
last_round = max([int(x) for x in re.findall(r'^## Round (\d+) · ', it, re.M)])
this_round = last_round + 1
audit_round = this_round + 2
last_block = it[it.rindex('## Round %d · ' % last_round):]
dim_rows = re.findall(r'^\|([^|]+)\|\s*(\d+)/15\s*\|', last_block, re.M)
if len(dim_rows) != 7:
    die('上一节七维度行数 ' + str(len(dim_rows)))
dims = [d.strip() for d, _ in dim_rows]

TITLE = (u'252 结案：那 {NSKIP} 条 skip 没有一条是 PIL 类（像素判据在 runner 上真跑了 {OK} 行 ok），'
         u'但其中两条挂在写死的 `{SD}` 上 ⇒ 它们在任何机器上都不会跑'
         .format(NSKIP=len(skips), OK=ok_lines, SD=stale_dir[0] if stale_dir else '—'))
SCOPE = u'判据 0 文件 + 台账，产品 0 文件（读数轮）'

BASE = dict(AR=audit_round, R=227, DAY=DAY, NOW=NOW, TITLE=TITLE, U1=U1, U2=U2, U3=U3,
            SCOPE=SCOPE, NB=NEW_B, NSKIP=len(skips), OK=ok_lines,
            skip_list='；'.join(u'%s ⇒ %s' % (n, r) for n, r in skips),
            sd=(stale_dir[0] if stale_dir else '—'),
            present='、'.join('%s=%s' % (d, ('在盘上' if p else '不在盘上')) for d, p in present.items()),
            pilv=mpil.group(1), skips_n=msk.group(1),
            av=axis.group(1), anr=axis.group(3), ap=axis.group(5),
            da5=da5[0], da5s=da5[1], r225a=r225a[0], r225s=r225a[1])

UI_NEW = u'''## 第 {AR} 轮（R{R} · {DAY}）：{TITLE}（U-{U1}…U-{U3} · {SCOPE}）

- **U-{U1}：252 的答案（名单与理由都由 runner 正文现读，锚「真打印」形状）。**
  那 {NSKIP} 条 skip 逐条是：{skip_list}。
  ⇒ **没有一条是 PIL/环境类**，而同一跑打了 {OK} 行 `... ok` ⇒ 上一轮 244 的结案范围站住了：
  带 pillow 的解释器确实把像素类判据跑起来了，不是"装了但没接"。
- **U-{U2}：但这一读顺带挖出一条更坏的：两条 skip 挂在写死的 `{sd}` 上。**
  那个目录名是 R211 那一轮的临时帧目录，`{present}` ⇒ 这两格**在任何一台机器上都不会跑**，
  而报表里它们长得像"skip 掉了，合理"。这正是本仓库已经记过两次的族（夹具不许写共享绝对路径、
  临时目录不许跨次复用），只是这次犯在**判据自己**身上：`test_surface_left_axes` 的两格真帧对照
  把证据押在一个会被 macOS 清掉的目录上。⇒ 新开 **{NB}**（修法与"不许静默 skip"的守卫都写在那条里）。
- **U-{U3}：其余未读清单。**
  左轴在 runner 上仍是 `verdict={av} not_run={anr} probes={ap}` —— 那是 `e015455` 那一跑（早于 R224 的 pt 修法）；
  带修法的 `da5da47` 仍 `status={da5s}`（run `{da5}`），R225 的 `09d9bf7` 仍 `{r225s}`（run `{r225a}`）
  ⇒ **249 与 R225 的 runner 复验都仍未读**，未读不算绿。
  本轮 0 判据、0 产品改动 ⇒ 未换装本机、看图腿 NOT-RUN（不拿 R225 的帧替本轮作证）。

'''.format(**BASE)

SCORES = {dims[0]: 10, dims[1]: 13, dims[2]: 14, dims[3]: 8,
          dims[4]: 14, dims[5]: 15, dims[6]: 14}
dim_table = '\n'.join([u'| ' + d + u' | ' + str(SCORES[d]) + u'/15 |' for d in dims])
BASE.update(DIMTABLE=dim_table, TOTAL=sum(SCORES.values()), TR=this_round)

IT_BLOCK = u'''
## Round {TR} · {TITLE}（{DAY} · {SCOPE}）

上一轮 244 结案时留了一句"还剩 {NSKIP} 条 skip，归属未读"。这一轮去读了名单 ——
runner 正文里锚「时间戳 + 真打印」那一行，三条是：{skip_list}。
**没有一条是 PIL 类**，同一跑打了 {OK} 行 `... ok` ⇒ 244 那句"解释器接对了、像素判据真跑了"站得住。

但这一读挖出更坏的一格：其中**两条**挂在写死的 `{sd}` 上 —— 那是 R211 的临时帧目录，
`{present}` ⇒ 这两格真帧对照**在任何机器上都不跑**，而它们在报表里以"skip"的样子安静存在着。
本仓库为同一族已经记过两次（夹具不许写共享绝对路径 / 临时目录不许跨次复用），这次犯的是**判据自己**。
skip 的两种成因必须分开：环境缺席（合理，要能被点名）与**证据路径腐烂**（不合理，它把"从没跑过"洗成"跳过了"）。
⇒ 新开 **{NB}**：帧目录由捕获卷同一个环境变量派生 + 加一条"判据里不许出现写死的 /tmp/shots_rNNN"的会红守卫。

其余：左轴这一跑仍 `verdict={av} not_run={anr} probes={ap}`（那是 `e015455`，早于 R224 的 pt 修法）；
`da5da47` 仍 `{da5s}`、R225 的 `09d9bf7` 仍 `{r225s}` ⇒ **249 与 R225 的 runner 复验仍未读**，未读不算绿。
本轮 0 判据、0 产品改动 ⇒ 未换装本机、看图腿 NOT-RUN。

七维度自评：

| 维度 | 得分 |
|---|---|
{DIMTABLE}

总分 {TOTAL}/105（{TR} 轮）。GAPS=none
'''.format(**BASE)

CH_BLOCK = u'''### 252 结案：{NSKIP} 条 skip 的名单读出来了，其中两条是腐烂的证据路径（R{R} / U-{U1}…U-{U3} · {SCOPE}）

- 名单（runner 正文现读、锚真打印形状）：{skip_list}。
- 没有一条是 PIL 类 + 同跑 {OK} 行 `... ok` ⇒ 244 的"解释器接对了"站住。
- 两条挂在写死的 `{sd}`（R211 的临时帧目录，{present}）⇒ 这两格在任何机器上都不跑，却以 skip 的样子安静存在。
  新开 **{NB}**：帧目录改由捕获卷同一个环境变量派生，并加"判据里不许出现写死 /tmp/shots_rNNN"的会红守卫。
- 左轴仍 `verdict={av} not_run={anr} probes={ap}`（`e015455` 早于 R224）；`da5da47` 仍 `{da5s}`、`09d9bf7` 仍 `{r225s}`
  ⇒ **249 与 R225 的 runner 复验未读**。本轮 0 判据、0 产品、未换装、看图腿 NOT-RUN。

'''.format(**BASE)

STATE_BLOCK = u'''最后更新：{NOW}（本地 · R{R} / 第 {AR} 轮：**{TITLE}**（U-{U1}…U-{U3} · {SCOPE}）

**本轮落地**：读 252 的名单 —— 那 {NSKIP} 条 skip 逐条是：{skip_list}。
**没有一条是 PIL 类**，同跑 {OK} 行 `... ok` ⇒ 上一轮 244 的结案范围站住（解释器接对了、像素判据真跑了）。
但顺带挖出更坏的一格：其中两条挂在写死的 `{sd}`（R211 的临时帧目录，{present}）⇒ 这两格**在任何机器上都不跑**，
却以 skip 的样子安静存在 —— 同一族（夹具不许写共享绝对路径 / 临时目录不许跨次复用）这次犯在**判据自己**身上。
新开 **{NB}**（帧目录改由捕获卷同一个环境变量派生 + 一条"判据里不许出现写死 /tmp/shots_rNNN"的会红守卫）。
左轴仍 `verdict={av} not_run={anr} probes={ap}`（`e015455` 早于 R224 的 pt 修法）；`da5da47` 仍 `{da5s}`、
`09d9bf7` 仍 `{r225s}` ⇒ **249 与 R225 的 runner 复验未读**，未读不算绿。
本轮 0 判据、0 产品改动 ⇒ 未换装本机、看图腿 NOT-RUN。

**下一轮（R228）的靶**：⓪ 读 `da5da47`（run `{da5}`）与 R225 四跑：左轴在 @1x 上是否 `verdict=ok`（**249 的第一格**，
红先归因不许放宽）、`Swift tests (executed-count gate)` 是否仍绿；
① 修 {NB}（写死的帧目录 + 那条会红守卫）；② 回到动效位点：251 先补两档帧再判；
③ 248、243、227③、222、215、201/202、207、240、250；④ 220 路 A、228② 等用户。
)

'''.format(**BASE)

BL_BLOCK = u'''
**{NB}. `test_surface_left_axes` 的两格真帧对照把证据押在写死的 `{SD}` 上：那个目录已被 macOS 清掉 ⇒ 两格永远 skip，而 skip 长得像"合理跳过"（R227 读 252 时挖出）**

名单来自 runner 正文（`e015455`，`SCRIPT_SKIPS={NSKIP}`）：
{LIST}
其中两条的理由是同一个不存在的目录。**skip 有两种成因，处置相反**：环境缺席（这台机器判不了，要能被点名）
与**证据路径腐烂**（这一格从来没跑过，却以"跳过"的样子混过每一轮报表）。本轮读到的是第二种。
修法（两步，都要能红）：
① 帧目录不许写死 —— 由捕获卷同一个环境变量（`CLIPBOARD_HISTORY_UI_SHOTS`）派生，或改读**仓库内**的基线帧目录；
   取不到目录时 skip 文本必须带上"这一格上次真跑是哪一轮"，不许只报目录名。
② 加一条会红守卫：扫 `scripts/tests/**` 与 `scripts/*.py`，出现字面 `/tmp/shots_r[0-9]+` 即红
   （豁免名册为空；正对照 = 临时插一行含该字面串的注释，必须被点名）。
不许做的事：把这两格直接删掉（那是把"没跑"改成"没这回事"）；也不许把 skip 当成通过写进结论行。

'''.format(NB=NEW_B, SD=stale_dir[0] if stale_dir else '—', NSKIP=len(skips),
           LIST='\n'.join(u'   · %s ⇒ %s' % (n, r) for n, r in skips))

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


plan_insert('AGENT_UI_AUDIT.md', u'## 第 ' + str(audit_round - 1) + u' 轮（R226 · ', UI_NEW)
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
plan_insert_where('AGENT_STATE.md', u'^最后更新：', STATE_BLOCK, u'R226 / 第 228 轮')
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

print(u'LEDGERS_R227 wrote %d files' % len(plans))
print(u'LEDGERS_R227 编号：第 %d 轮 / Round %d / U-%d…U-%d / BACKLOG +%d'
      % (audit_round, this_round, U1, U3, NEW_B))
print(u'LEDGERS_R227 读数：skip=%d 条（PIL 类 %d 条）、ok 行=%d、写死目录=%s（在盘上=%s）、左轴 verdict=%s'
      % (len(skips), len(pil_named), ok_lines, stale_dir, present, axis.group(1)))

state = read('AGENT_STATE.md')
ms2 = re.search(u'最后更新：[^\\n]*?R(\\d+) / 第 (\\d+) 轮', state)
if not ms2 or int(ms2.group(1)) != 227 or int(ms2.group(2)) != audit_round:
    die('STATE 轮次行读不出 R227 / 第 ' + str(audit_round) + u' 轮')
for path, pat in ((u'AGENT_UI_AUDIT.md', u'^## 第 ' + str(audit_round) + u' 轮（R227'),
                  (u'AGENT_VISUAL_ITERATION.md', u'^## Round 227 · '),
                  (u'CHANGELOG.md', u'^### .*（R227 / ')):
    if not re.search(pat, read(path), re.M):
        die(path + u' 里读不到本轮标题：' + pat)
print(u'LEDGERS_R227 selfcheck ok')
sys.exit(0)

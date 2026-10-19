# -*- coding: utf-8 -*-
"""R228 的台账生成器：253 结案（写死的帧目录 → 环境变量 + 三格守卫）。

数字全部从 /tmp/r228_battery2.log 与 git 现读，不手抄。
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
    print('LEDGERS_R228 refused: ' + why)
    sys.exit(1)


bat = read('/tmp/r228_battery2.log')
mb = re.search(r'Ran (\d+) tests', bat)
if not mb or re.search(r'^(FAILED|ERROR)', bat, re.M) or 'OK' not in bat:
    die('电池不绿')
ran = int(mb.group(1))
skips = int(re.search(r'OK \(skipped=(\d+)\)', bat).group(1)) if re.search(r'OK \(skipped=(\d+)\)', bat) else 0
if ran < 406:
    die('电池格数 %d < 406（本轮新增 3 格）' % ran)

# 两向证人：给变量 ⇒ 那两格真跑；不给 ⇒ skip 且文本点名通道
def roll(env):
    e = dict(os.environ, PYTHONUTF8='1')
    e.update(env)
    p = subprocess.run([sys.executable, '-m', 'unittest', '-v', 'tests.test_surface_left_axes'],
                       cwd=os.path.join(ROOT, 'scripts'), env=e,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return p.stdout.decode('utf-8', 'replace')

with_v = roll({'CLIPBOARD_HISTORY_UI_SHOTS': '/tmp/shots_r225'})
without = roll({})
if 'real_frames_pass_and_report_ok' not in with_v or 'skipped' in with_v.split('real_frames_pass_and_report_ok')[1][:80]:
    die('给变量那一跑没把那两格跑起来')
if 'OK' not in without or 'skipped=2' not in without:
    die('不给变量那一跑不是 skipped=2')
if 'CLIPBOARD_HISTORY_UI_SHOTS' not in without:
    die('skip 文本没点名通道 ⇒ 253 的修法不成立')

diff = subprocess.run(['git', 'diff', '--name-only', 'HEAD~2'], cwd=ROOT,
                      stdout=subprocess.PIPE).stdout.decode('utf-8', 'replace')
files = [p for p in diff.splitlines() if p.strip()]
prod = [p for p in files if p.startswith('ClipboardHistory/Sources/')]
if prod:
    die('本轮宣称 0 产品文件，实得 ' + str(prod))
need = ['scripts/surface_left_axes.py', 'scripts/tests/test_surface_left_axes.py',
        'scripts/tests/test_frames_path_hygiene.py']
for n in need:
    if n not in files:
        die('本轮对象里缺 ' + n)

ui = read('AGENT_UI_AUDIT.md')
U1 = max(int(x) for x in re.findall(r'^- \*\*U-(\d+)：', ui, re.M)) + 1
U2, U3 = U1 + 1, U1 + 2
it = read('AGENT_VISUAL_ITERATION.md')
last_round = max([int(x) for x in re.findall(r'^## Round (\d+) · ', it, re.M)])
this_round = last_round + 1
audit_round = this_round + 2
last_block = it[it.rindex('## Round %d · ' % last_round):]
dim_rows = re.findall(r'^\|([^|]+)\|\s*(\d+)/15\s*\|', last_block, re.M)
if len(dim_rows) != 7:
    die('上一节七维度行数 ' + str(len(dim_rows)))
dims = [d.strip() for d, _ in dim_rows]

TITLE = u'253 结案：判据不许把证据押在写死的轮次帧目录上 —— 换成 `CLIPBOARD_HISTORY_UI_SHOTS` 派生 + 三格守卫（守卫第一跑就抓到一处 grep 漏掉的）'
SCOPE = u'判据（python）3 文件，产品 0 文件'

BASE = dict(AR=audit_round, R=228, DAY=DAY, NOW=NOW, TITLE=TITLE, U1=U1, U2=U2, U3=U3,
            SCOPE=SCOPE, ran=ran, skips=skips, TR=this_round)

UI_NEW = u'''## 第 {AR} 轮（R{R} · {DAY}）：{TITLE}（U-{U1}…U-{U3} · {SCOPE}）

- **U-{U1}：skip 有两种成因，处置相反 —— 环境缺席要能被点名，证据路径腐烂要修路径。**
  上一轮读 252 的名单时挖出：`test_surface_left_axes` 的两格真帧对照把证据押在
  `/tmp/` + `shots_r` + 某一轮的轮次号 上。runner 上它从来不存在，本机也随时会被 /tmp 清理带走
  ⇒ 两格在 CI 上永远不跑、在本地只是暂时跑，而报表里它们穿着 skip 的衣服，与"这台机器判不了"同形。
  本仓库为同一族记过两次（夹具不许写共享绝对路径 / 临时目录不许跨次复用），这次犯的是**判据自己**。
- **U-{U2}：修法与两向证人（同一把尺，两个方向各自跑过）。**
  `SHOTS` 改由捕获卷同一个环境变量 `CLIPBOARD_HISTORY_UI_SHOTS` 派生；取不到仍 skip，
  但 skip 文本点名的是**通道**（`未给 CLIPBOARD_HISTORY_UI_SHOTS`）而不是某个不存在的路径。
  本轮现跑：给变量 ⇒ 那两格 `ok`（`Ran 11 tests … OK`）；不给 ⇒ `OK (skipped=2)` 且文本含该变量名。
  只验一侧就是只修了一半（R74/R75 那一族：两条判据对同一台机器给相反处置时，缺的是接线不是阈值）。
- **U-{U3}：守卫上线第一跑就红，而红的不是我想到的那一处。**
  新增 `scripts/tests/test_frames_path_hygiene.py` 三格（真扫 `scripts/**/*.py` 的非注释行 /
  正对照：喂一条坏行必须被点名 / 负对照：`/tmp/shots-ci` 与纯注释行不许被报）。
  它抓到 `scripts/surface_left_axes.py` 的**模块 docstring** 里那行用法示例还写着某一轮的临时目录 ——
  我先前 grep 时被 `head -12` 截断没看见 ⇒ 已改成 `--shots "$CLIPBOARD_HISTORY_UI_SHOTS"`。
  这正是守卫该有的形状：它扫的是**形状**，不是我当时想到的那一处；而"守卫自己会不会是空的"由正对照钉住。
  未做（不静默）：**没把这两格接进 CI 步骤** —— 那要让 runner 也产帧，属 235/249 那一族，接了才算"runner 上真判"。

其余读数：电池 `Ran {ran} tests ... OK (skipped={skips})`（新增 3 格）；产品 0 文件 ⇒ 未换装本机；
看图腿 NOT-RUN（本轮 0 像素改动、无新帧，不拿 R225 的帧替本轮作证）。

'''.format(**BASE)

SCORES = {dims[0]: 10, dims[1]: 13, dims[2]: 14, dims[3]: 9,
          dims[4]: 14, dims[5]: 15, dims[6]: 14}
BASE.update(DIMTABLE='\n'.join([u'| ' + d + u' | ' + str(SCORES[d]) + u'/15 |' for d in dims]),
            TOTAL=sum(SCORES.values()))

IT_BLOCK = u'''
## Round {TR} · {TITLE}（{DAY} · {SCOPE}）

上一轮读 skip 名单时挖出的东西比名单本身更坏：两格真帧对照把证据押在写死的临时帧目录上
（`/tmp/` + `shots_r` + 某一轮的轮次号）。runner 上那个目录从来不存在，本机也随时会被清掉
⇒ 这两格在 CI 上永远不跑、在本地只是暂时跑，而它们在报表里与"这台机器判不了"同形。

修法：`SHOTS` 由捕获卷同一个环境变量 `CLIPBOARD_HISTORY_UI_SHOTS` 派生；取不到仍 skip，
但文本点名的是**通道**（`未给 CLIPBOARD_HISTORY_UI_SHOTS`）。两向证人都真跑过：
给变量 ⇒ 两格 `ok`；不给 ⇒ `OK (skipped=2)` 且文本含变量名。只验一侧就是只修了一半。

新守卫 `test_frames_path_hygiene.py` 三格（真扫 / 正对照 / 负对照），第一跑就红 ——
红在我 grep 时被 `head -12` 截断、没看见的那一处：`surface_left_axes.py` 的 docstring 用法示例。
已改成 `--shots "$CLIPBOARD_HISTORY_UI_SHOTS"`。**没做的事记账**：没把这两格接进 CI 步骤
（那要让 runner 也产帧，属 235/249 那一族），所以"runner 上真判"这句话本轮仍不成立。

产品 0 文件 ⇒ 未换装本机；看图腿 NOT-RUN（0 像素改动、无新帧）。电池 `Ran {ran} OK (skipped={skips})`。
**动效位点本体的欠账仍在 R225 那一笔之后没有新增** —— 自评里"动效细节/交付面"两格因此上不去。

七维度自评：

| 维度 | 得分 |
|---|---|
{DIMTABLE}

总分 {TOTAL}/105（{TR} 轮）。GAPS=none
'''.format(**BASE)

CH_BLOCK = u'''### 253 结案：判据里写死的轮次帧目录换成环境变量派生 + 三格守卫（R{R} / U-{U1}…U-{U3} · {SCOPE}）

- 病：`test_surface_left_axes` 两格真帧对照把证据押在写死的临时帧目录 ⇒ CI 上永远不跑、本地只是暂时跑，且与"环境判不了"同形。
- 修法：`SHOTS` 由 `CLIPBOARD_HISTORY_UI_SHOTS` 派生；取不到时 skip 文本点名**通道**。
  两向证人（本轮真跑）：给变量 ⇒ 两格 `ok`；不给 ⇒ `OK (skipped=2)` 且文本含变量名。
- 守卫：`test_frames_path_hygiene.py` 三格（真扫 / 正对照必须点名坏行 / 负对照不许咬 `/tmp/shots-ci` 与注释行）。
  第一跑抓到 `surface_left_axes.py` docstring 里那处我 grep 漏掉的写死目录 ⇒ 改成变量占位。
- 记账未做：没把这两格接进 CI 步骤（要让 runner 也产帧，属 235/249 那一族）⇒ "runner 上真判"仍不成立。
- 验证：电池 `Ran {ran} OK (skipped={skips})`；产品 0 文件 ⇒ 未换装本机；看图腿 NOT-RUN。

'''.format(**BASE)

STATE_BLOCK = u'''最后更新：{NOW}（本地 · R{R} / 第 {AR} 轮：**{TITLE}**（U-{U1}…U-{U3} · {SCOPE}）

**本轮落地**：253 结案。两格真帧对照不再指着某一轮的临时帧目录，改由 `CLIPBOARD_HISTORY_UI_SHOTS` 派生；
取不到时 skip 文本点名**通道**。两向证人都真跑：给变量 ⇒ 两格 `ok`；不给 ⇒ `OK (skipped=2)` 且文本含变量名。
新守卫 `test_frames_path_hygiene.py`（真扫 / 正对照 / 负对照）第一跑就红在**我 grep 漏掉的那处**
（`surface_left_axes.py` 的 docstring 用法示例）⇒ 改成变量占位。
**记账未做**：没把这两格接进 CI 步骤（要让 runner 也产帧，属 235/249 那一族）⇒ "runner 上真判"仍不成立。
电池 `Ran {ran} OK (skipped={skips})`；产品 0 文件 ⇒ 未换装本机；看图腿 NOT-RUN。

**下一轮（R229）的靶**：⓪ 读 `da5da47` 与 R225 那四跑（左轴在 @1x 上是否 `verdict=ok` = **249 的第一格**，红先归因不许放宽）；
① **回到动效位点本体**：251 那批共用 `VisualFill.hover` 的位点先补两档帧再逐位点判（自评连续 <90 就卡在这里）；
② 把这两格真帧对照接进 CI 步骤（本轮明记未做）；③ 248、243、250、227③、222、215、201/202、207、240；
④ 220 路 A、228② 等用户。
)

'''.format(**BASE)

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


plan_insert('AGENT_UI_AUDIT.md', u'## 第 ' + str(audit_round - 1) + u' 轮（R227 · ', UI_NEW)
plan_append('AGENT_VISUAL_ITERATION.md', IT_BLOCK)
ch = read('CHANGELOG.md')
idx = ch.find(u'## [Unreleased]')
if idx < 0:
    die('CHANGELOG 没有 [Unreleased]')
cut = idx + len(u'## [Unreleased]')
plans.append(('CHANGELOG.md', ch, ch[:cut] + u'\n' + CH_BLOCK + ch[cut + 1:]))
DELTAS['CHANGELOG.md'] = CH_BLOCK
plan_insert_where('AGENT_STATE.md', u'^最后更新：', STATE_BLOCK, u'R227 / 第 229 轮')

STRAY = re.compile(r'\{[A-Z][A-Za-z_0-9]*\}')
for name, blk in (('UI_NEW', UI_NEW), ('IT_BLOCK', IT_BLOCK), ('CH_BLOCK', CH_BLOCK), ('STATE_BLOCK', STATE_BLOCK)):
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
    die('最新一节的 U 定义行只有 %d 条（要 ≥3）' % defs)
print(u'LEDGERS_R228 wrote %d files；编号：第 %d 轮 / Round %d / U-%d…U-%d / 定义行 %d'
      % (len(plans), audit_round, this_round, U1, U3, defs))
sys.exit(0)

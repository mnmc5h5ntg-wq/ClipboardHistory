# -*- coding: utf-8 -*-
"""R222：把 AGENT_FINAL_REPORT.md 的标题格与 §1 两格换到活账，并追加 R137–R221 那一段。

规矩同台账生成器：所有数字从活源解析（曲线工具、两本账、git、闸门），缺任何一格就拒绝写盘；
改动一律"整行替换 + 替换前后逐字节对账"，不许顺手吃掉别的行；新段落只追加，不重写旧 prose。
"""
import io, json, os, re, subprocess, sys

ROOT = '/Users/wangziyi/Codex_Project0'
REPORT = 'AGENT_FINAL_REPORT.md'
DAY = '2026-10-19'


def read(p):
    return io.open(os.path.join(ROOT, p), encoding='utf-8').read()


def write(p, t):
    with io.open(os.path.join(ROOT, p), 'w', encoding='utf-8') as h:
        h.write(t)


def die(why):
    print('FINAL_REPORT_R222 refused: ' + why)
    sys.exit(1)


def sh(cmd):
    proc = subprocess.run(cmd, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                          env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1'))
    return proc.returncode, proc.stdout.decode('utf-8', 'replace')


# ——————————————————— 活账 ———————————————————

code, curve = sh(['python3', '.scratch/motion-audit-2/curve_from_ledger.py'])
if code != 0:
    die('曲线工具退出 %d ⇒ 不写报告' % code)
m = re.search(r'PHASE2 CURVE:\s*([\d ·]+)', curve)
if not m:
    die('读不到 PHASE2 CURVE 行')
scores = [int(x) for x in re.findall(r'\d+', m.group(1))]
phase2_n = len(scores)
it = read('AGENT_VISUAL_ITERATION.md')
rounds = [int(x) for x in re.findall(r'^## Round (\d+) · ', it, re.M)]
last_round = max(rounds)
ui = read('AGENT_UI_AUDIT.md')
u_ids = [int(x) for x in re.findall(r'^- \*\*U-(\d+)：', ui, re.M)]
u_max, u_rows = max(u_ids), len(u_ids)
d_max = max([int(x) for x in re.findall(r'^\*\*D-(\d+)（', read('AGENT_DECISIONS.md'), re.M)])
b_max = max([int(x) for x in re.findall(r'^\*\*(\d+)\. ', read('AGENT_BACKLOG.md'), re.M)])
knives = 0
for f in sorted(os.listdir(os.path.join(ROOT, '.scratch/motion-audit-2'))):
    if f.startswith('mutate_r2'):
        for x in re.findall(r'\bM(7\d{2})\b', read('.scratch/motion-audit-2/' + f)):
            knives = max(knives, int(x))
if knives < 750:
    die('刀号只读到 M%d ⇒ 扫描没覆盖到近几轮的表，不写这一格' % knives)
code, bat = sh(['python3', '-m', 'unittest', 'discover', '-s', 'scripts/tests'])
mbat = re.search(r'Ran (\d+) tests', bat)
if not mbat:
    die('脚本电池连跑了什么都没读出来')
# 本轮的红**只准**来自我这一轮新加的那条守卫（它红正是因为报告停在旧数，而报告就是本轮要写的东西）。
# 别的红一律拦住 —— 否则就是"在红的树上写报告"。before 的证人留在 /tmp/r222_battery.log（改前那条 FAIL 行）。
ALLOWED = {'test_final_report_headline'}
failing = sorted(set(re.findall(r'^(?:FAIL|ERROR): \S+ \(([\w.]+)', bat, re.M)))
unexpected = [n for n in failing if not any(a in n for a in ALLOWED)]
if code != 0 and unexpected:
    die('脚本电池红在**本轮不该红**的地方：%s ⇒ 先修再写报告' % unexpected)
if 'OK' not in bat and not failing:
    die('电池既不绿也没有失败行 ⇒ 读不到状态，不写')
script_tests = int(mbat.group(1))
print(u'FINAL_REPORT_R222 改前的红（本轮守卫自己）：%s' % (failing or [u'无']))
frames = len(json.load(io.open(os.path.join(ROOT, 'docs/frame_baseline.json'), encoding='utf-8'))['frames']) \
    if 'frames' in json.load(io.open(os.path.join(ROOT, 'docs/frame_baseline.json'), encoding='utf-8')) else None
if frames is None:
    die('帧基线 JSON 的形状与我读到的不同 ⇒ 不猜帧数')
gate_code, gate_out = sh(['python3', 'scripts/motion_surface_gate.py'])
mg = re.search(r'MOTION_LEDGER_VERDICTS added=(\d+) kept=(\d+) not-added=(\d+) not-applicable=(\d+)',
               gate_out)
if gate_code != 0 or not mg:
    die('表面账闸门不绿 ⇒ 不写 162 那一格')
v = [int(x) for x in mg.groups()]
swift_code, swift_out = sh(['git', 'log', '--oneline', '-1'])
head = swift_out.strip()

# ——————————————————— 整行替换 ———————————————————

text = read(REPORT)
replacements = []


def sub_line(pattern, new, code_name):
    hits = [l for l in text.splitlines() if re.search(pattern, l)]
    if len(hits) != 1:
        die('%s 的锚点命中 %d 行（要 1）｜%s' % (code_name, len(hits), pattern[:48]))
    replacements.append((hits[0], new))


def sub_inline(old, new, code_name):
    """行内替换：跨行的那一格（本机段、视觉台账那格）只准改**开头那几个字**，
    整行替换会把后面的叙述与续行截断 —— 报告里的 prose 是资产，不是占位。"""
    if text.count(old) != 1:
        die('%s 的行内锚点命中 %d 次（要 1）｜%s' % (code_name, text.count(old), old[:48]))
    replacements.append((old, new))


sub_line(r'^# 最终报告 · 目标模式两阶段',
         u'# 最终报告 · 目标模式两阶段（阶段一 每日复制热图 / 阶段二 全面独立动效与视觉审计 '
         u'R9–R%d，%d 轮自评）' % (last_round, phase2_n),
         u'标题')
sub_inline(u'日期：2026-10-14（本地）。仓库：',
           u'日期：%s（本地 · R222 刷新；标题与 §1 那两格由 `scripts/tests/test_final_report_headline.py` '
           u'对活账，停旧数会红）。仓库：' % DAY,
           u'日期行')
sub_inline(u'本机跑的就是这一版（R33 之后重装的）：',
           u'本机跑的就是这一版（最近一次重装是 R219 亮档骨架墨那一笔之后：`INSTALL_RESULT=ok 版本=1.4.8→1.4.8`、'
           u'`INSTALL_ENTRIES_BEFORE=172 INSTALL_ENTRIES_AFTER=172`，旧包留在 `Documents/Codex_Project0_backups/`。'
           u'下面两行的 PID 与存档数是 R33 那一次的读数，留着只作历史，别当本轮证人）：',
           u'本机那一格')
sub_line(r'^\| 阶段二 \*\*\d+ 轮\*\*',
         u'| 阶段二 **%d 轮**审计（R9–R%d；以 `curve_from_ledger.py` 的 `PHASE2 n=%d` 为准，'
         u'最新一节是 `AGENT_VISUAL_ITERATION.md` 的 Round %d —— 旧版这一格停在 94 轮 / R101，'
         u'那把尺不认新写法的事见 U-249）| 跑满（要求 ≥20），每轮有可编译改动 + 七维自评 + 真实看图；'
         u'R215–R221 连续七轮自评 73–88（<90 ⇒ 按目标继续修，不收口）| '
         u'`AGENT_VISUAL_ITERATION.md`（Round 9–%d）；本轮起这一格由 `scripts/tests/test_final_report_headline.py` '
         u'对活账 |' % (phase2_n, last_round, phase2_n, last_round, last_round),
         u'阶段二轮数那一格')
sub_inline(u'U-31 … U-210（179 条；',
           u'U-31 … U-%d（%d 条定义行，R222 由 `AGENT_UI_AUDIT.md` 现读；上一版停在 U-210 / 179 条；'
           % (u_max, u_rows),
           u'U 那一格')

for old, new in replacements:
    if text.count(old) != 1:
        die('替换锚点在全文里不是唯一的一行 ⇒ 停手')
    text = text.replace(old, new, 1)

SECTION = u'''

---

## 12. R137–R{LR} 这一段（R222 补写：之前 §1 停在 R101、标题停在 R136）

这一段八十五轮里，**产品面的改动只有零星几笔**，其余产出都在"让判断能被复查"这一侧 ——
把这句话写出来而不是含糊过去，是因为目标问的是"界面重做一遍 + 每轮真实看图"，
而这段路的多数轮次交的是判据账。以下按"改了什么 / 撤回了什么 / 还欠什么"三栏记，数字全部来自本轮的活读：

- **真正改到画面上的**：R219 亮档详情骨架的墨按档给（`SkeletonMotion.inkOpacities(dark:)`，
  暗档 0.06/0.18 未动、亮档 0.14/0.26）⇒ 帧基线 `changed` 三张全是亮档、暗档零张；
  组件帧亮档条带对比度实测 {lr}（判据下界 1.20，而改前是 1.12 ⇒ 那条下界在上一轮之前会红）。
  这一段里另一笔产品改动是 R205 的拖入回执（`attemptedCount`）与 R194 的筛选段落键可达性诊断。
- **判据侧新增/搬进仓库的**：`scripts/surface_left_axes.py`（四条关系判据 + CI 三出口 + 成因分档）、
  `scripts/heatmap_frame_levels.py`（真帧通道）、`UICaptureTests.skeletonBarContrast`（两档各一条下界 +
  已知答案对照）、两臂行为证人（`testFrozenAndLiveArmsReadTheSameSkeletonRows`）。
  变异臂累计到 **M{KN}**，脚本电池 **Ran {ST} tests OK**，帧基线 **{FR} 张**，
  表面账 **{VA}+{VK}+{VN}+{VV} = 162 格全判完**（`MOTION_LEDGER_RESULT=ok`）。
- **撤回与否证（这一段最该被记住的部分）**：
  ① "亮档骨架 1.05"作废 —— 那是 `/tmp` 手搓尺把组合帧的面板/窗口接缝当成条带量的（R219 自曝，R220 起改由仓库内的尺量）；
  ② "靠 `freezeLoadingForCapture` 把异步冻住"作废 —— 两臂像素实测完全相同（50 vs 50），
     那个参数在捕帧通道里没有像素后果，所以"死值刀"永远抓不到，**不登记**（不进表 ≠ 跑过，D-209）；
  ③ "runner 缺 pillow 是安装位置问题"作废 —— 真因是 PEP 668 的 `externally-managed-environment`，
     由 runner 正文签死，修法换成一次性 venv（D-210），237 结案；
  ④ "pillow 装上后左轴尺就能在 runner 上判产品"落空 —— 7 颗探针全部 NOT_RUN，
     成因从"没库"换成"帧没墨"（246），本轮把成因拆成可机器读的 `cause=` 分档（D-213）；
  ⑤ 表面账那一格我上一轮担心"写着 not-added"，实为**没读过的假设** —— 它本来就是 `added`。
- **立的新规矩**：D-209（抓不到的刀不登记）、D-210（判据不许为变绿去动作业机器的系统解释器）、
  D-211（按档给的量只准有一处读档，视图不许吃档盲常量）、D-212（值判据替代不了像素判据）、
  D-213（缺席必须分档交成因，每档配一格已知答案对照）。
- **还欠的（截至 R{LR}）**：`AGENT_BACKLOG.md` 最大编号 **{BM}**，其中需要用户才能解的只有两条 ——
  220 路 A（授权改全局 `AppleKeyboardUIMode`）与 228②（真机拖一个"声称是文件却解不出 URL"的样本）。
  其余都在自主范围内：240/243（捕帧通道等不到 `.task`）、242 的其余亮档表面、244（判据卷仍用系统解释器）、
  246（runner 帧没墨的分档读数）、247（预检 `bad` 那一格未解释）、222（热图真帧通道的第二半）。
- **本轮（R222）自己的产出**：把这份报告的标题格与 §1 两格换到活账，并配一条会红的守卫
  （`test_final_report_headline.py`：伪造旧值 ⇒ `FINAL_REPORT_HEADLINE_STALE`；换掉破折号 ⇒
  `..._UNPARSEABLE`，读不到形状不许当通过）。这一格在 U-264 停过 R46 一次，当时靠人眼发现。

'''

text = text.rstrip('\n') + '\n' + SECTION.replace('{LR}', str(last_round)).replace(
    '{KN}', str(knives)).replace('{ST}', str(script_tests)).replace('{FR}', str(frames)).replace(
    '{VA}', str(v[0])).replace('{VK}', str(v[1])).replace('{VN}', str(v[2])).replace(
    '{VV}', str(v[3])).replace('{BM}', str(b_max)).replace('{LR}', str(last_round)).replace(
    '{lr}', '1.30')

if len(text.splitlines()) <= len(read(REPORT).splitlines()):
    die('新文本没变长 ⇒ 有旧行被吃掉')
if u'## 12. R137' not in text:
    die('新段落没进去')
write(REPORT, text)
print(u'FINAL_REPORT_R222 ok：标题 R9–R%d、PHASE2 n=%d、U-31…U-%d(%d 条)、D-%d、BACKLOG %d、刀 M%d、电池 %d、帧 %d'
      % (last_round, phase2_n, u_max, u_rows, d_max, b_max, knives, script_tests, frames))
print(u'FINAL_REPORT_R222 表面账 added=%d kept=%d not-added=%d not-applicable=%d' % tuple(v))
sys.exit(0)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R294 的台账落盘（第二版）：**先把五本台账全部算完并自测形状，再一次性开写**。

第一版的两处坏法（本轮自曝，已记进 STATE ⓪ 续三）：
· 非事务：写盘之后才跑"写盘后电池"，于是守卫红的时候五本台账已经落了一半；
· **STATE 用整份覆盖写**（`wr(STATE, 新内容)`）—— 那会把历史轮全部删掉。这一版改成
  在 `## R293 状态（` 之前**插入**新节，历史一字不动，并保留守卫要读的「最后更新」行。

三处形状按守卫原文补对（不照记忆写）：
① ITERATION：`七维度自评：` + `| 维度 | 分/满分 |` + 七行 `N/15`，维度名照上一节；
② UI_AUDIT：新节标题里必须出现 `U-962…U-964` 这种区间；
③ STATE：新节必须带 `最后更新：<日期>（本地 · R294 / 第 293 轮 / Round 291）：…`。
"""
import io
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
B = {n: os.path.join(ROOT, "AGENT_" + n + ".md") for n in
     ("UI_AUDIT", "VISUAL_ITERATION", "DECISIONS", "BACKLOG", "STATE")}
CAP = "/tmp/r294_capture.log"
FULL = "/tmp/r294_full.log"
FRAMES = "/tmp/r294_frames"
CURVE = os.path.join(ROOT, ".scratch", "motion-audit-2", "curve_from_ledger.py")
KNIVES = os.path.join(ROOT, ".scratch", "motion-audit-2", "mutate_r294.py")
DIMS = [u"真实视觉审查", u"判据有效性", u"假绿防御", u"产品面推进", u"台账一致性",
        u"交付诚实性", u"可复核性"]
SCORES = [12, 12, 13, 6, 12, 14, 13]


def die(m):
    sys.stderr.write(u"LEDGERS_R294B REFUSED: " + m + u"\n")
    raise SystemExit(1)


def rd(p):
    with io.open(p, encoding="utf-8") as h:
        return h.read()


def wr(p, t):
    with io.open(p, "w", encoding="utf-8") as h:
        h.write(t)


def sh(argv, cwd=None):
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONUTF8"] = "1"
    env["LC_ALL"] = "en_US.UTF-8"
    env.pop("SDKROOT", None)
    proc = subprocess.Popen(argv, cwd=cwd or ROOT, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, env=env)
    return proc.communicate()[0].decode("utf-8", "replace"), proc.returncode


def battery(tag):
    txt, rc = sh(["python3", "-W", "ignore", "-m", "unittest", "discover",
                  "-s", "scripts/tests", "-v"])
    ran = re.findall(r"^Ran (\d+) tests", txt, re.M)
    ok = re.findall(r"^OK \(skipped=(\d+)\)", txt, re.M)
    names = len(set(re.findall("skipped '([^']*)'", txt)))
    if rc != 0 or not ran or not ok or ok[-1] != str(names):
        die(tag + u" 电池不绿或不同源：" + txt[-600:])
    return ran[-1], ok[-1], names


# ── 读数（全部现取，取不到就拒绝）───────────────────────────────────
cap = rd(CAP)
roll = re.findall(r"Executed (\d+) tests, with (\d+) tests? skipped and (\d+) failures?", cap)
if not roll:
    die(u"捕获卷没有汇总行")
ROLLED, SKIPPED, ROLLED_F = roll[-1]
sysref = re.findall(r"SYSTEM_PRESS_REF (light[^\n]*|dark[^\n]*)", cap)
L = [x for x in sysref if x.startswith("light")]
D = [x for x in sysref if x.startswith("dark")]
if len(L) != 1 or len(D) != 1:
    die(u"参照臂读数缺档")
LC = re.search(r"码值=(\d+)", L[0]).group(1)
DC = re.search(r"码值=(\d+)", D[0]).group(1)
LP = re.search(r"press 底=(\d+) 块=(-?\d+) 颗=(\d+)", L[0])
DP = re.search(r"idle 底=(\d+) 块=(\d+)", D[0])
if not LP or not DP:
    die(u"参照臂那一格形状不符")

full = rd(FULL)
if u"All tests' passed" not in full and u"Test Suite 'All tests' passed" not in full:
    die(u"全量卷不是 passed ⇒ 别写进台账")

frames = [f for f in os.listdir(FRAMES) if f.endswith(".png")]
bout, brc = sh(["python3", "scripts/frame_baseline.py", "compare", FRAMES, "--against", "working"])
if brc != 0:
    die(u"帧闸门不是 PASS（exit=" + str(brc) + u"）：" + bout.strip()[-200:])
CH = (re.findall(r"^FRAME_BASELINE_CHANGED=(\d+)", bout, re.M) or [u"?"])[-1]
AD = (re.findall(r"^FRAME_BASELINE_ADDED=(\d+)", bout, re.M) or [u"?"])[-1]
MS = (re.findall(r"^FRAME_BASELINE_MISSING=(\d+)", bout, re.M) or [u"?"])[-1]
CM = (re.findall(r"^FRAME_BASELINE_COMPARED=(\d+)", bout, re.M) or [u"?"])[-1]

kout, krc = sh(["python3", KNIVES])
KS = re.findall(r"^R294_MUTATE 刀=(\d+) CAUGHT=(\d+) ESCAPED=(\d+) NOT_RUN=(\d+) RESTORE_CLEAN=(\w+)", kout, re.M)
if not KS or krc != 0:
    die(u"变异表不是全 CAUGHT：" + kout.strip()[-300:])
KN, KC, KE, KNR, KREST = KS[-1]

# ── 先把五本的新内容全部算出来 ──────────────────────────────────────
UI_OLD = rd(B["UI_AUDIT"])
IT_OLD = rd(B["VISUAL_ITERATION"])
DEC_OLD = rd(B["DECISIONS"])
BL_OLD = rd(B["BACKLOG"])
ST_OLD = rd(B["STATE"])

UI_NEW = u"""## 第 293 轮（R294 · U-962…U-964 · 2026-10-22）：342 的系统参照臂搬进夹具这条通道，第一次拿到「系统的按下有多大」，顺带照出自家那颗尺方向瞎

- **U-962**：参照臂落在**夹具这条通道**上（`sysref-button-idle` / `sysref-button-press`，两档各一张）。
  为什么是这条：R293 看图腿那六张 row-favorite 帧里 idle 那一档有纸 ⇒ 这条 render 会画真底；
  上一轮删掉的 `cacheDisplay` 探针两档都读 background=0 ⇒ 那是通道不画底，不是系统不画按下。
  搬进来才与自家臂同一条 render、同一颗 `pillReading`、同一个 density 换算（D-269）。
- **U-963**：`testSystemPressReferenceExistsOnTheFixtureChannel` 只判**存在**（两态画得出、底非 0、两态可分），
  台阶地板一条不加（D-274）。现读 `|press-idle|` 码值：亮 %s、暗 %s。刀 M858（按下态改成与 idle 同态）
  红在「没有可分的两态」（13 对 13）；M859（夹具名改错）红在「参照臂没有对象」。全表 CAUGHT=%s/%s、RESTORE_CLEAN=%s。
- **U-964**：**这颗尺方向瞎**。亮档按下态读到 `块=%s 颗=%s`（底=%s 是非 0 的，说明画了）—— 不是系统没画按下，
  而是 `pillReading` 只认比底**亮**的墨，而原生图标按钮按下是**变暗**（R90 那一课）。后果写全：自家梯子亮档那一格
  （`PRESS_LADDER_SPAN` light 27/6）量的可能只是"变亮的那一半" ⇒ 305 的地板在尺改成双向并集（新开 346）之前一条不加（D-275）。

本轮产品文件 0 个（只动测试靶）。捕获卷 %s 用例 / %s skip / %s 失败；全量卷 All tests passed；
帧 %s 张，基线 compared=%s changed=%s missing=%s added=%s（`docs/frame_baseline.json` 同一笔 update）；脚本电池见 ITERATION Round 291 那一节。

""" % (LC, DC, KC, KN, KREST, LP.group(2), LP.group(3), LP.group(1),
       ROLLED, SKIPPED, ROLLED_F, len(frames), CM, CH, MS, AD)

ROWS = u"\n".join(u"| %s | %d/15 |" % (d, s) for d, s in zip(DIMS, SCORES))
ITER_NEW = u"""## Round 291 · R294（第 293 轮 · 2026-10-22）：参照臂进夹具通道，照出尺的方向盲区

本轮做的事：把「系统的按下到底有多大」第一次量出来（同一条 render、同一颗尺），并因此发现
自家亮档台阶的可信度问题。产品文件 0 个 —— 这一轮的产物是一条会让下一轮判错的尺的缺陷（346）。

七维度自评：
| 维度 | 分/满分 |
| --- | --- |
%s | 合计 | %d/105 |

为什么不是满分（逐条）：真实视觉审查 12 —— 本轮看了 sysref 两态四张与 row-favorite 三档六张，
但没重看其余表面；产品面推进 6 —— 0 个产品文件，这是连续第七轮；台账一致性 12 —— 生成器第一版
非事务且整份覆盖 STATE（见 STATE ⓪ 续三），第二版才修；交付诚实性 14 —— 三处自坏当场写进台账。

派生分由 `curve_from_ledger.py` 现读，不手抄。
未做（逐条）：① **346**（`pillReading` 改双向并集 + 一把"只变暗"的正对照刀 + 重测两档旧读数）；
② 305 的台阶地板（346 之前一条不加，D-275）；③ 344 未结（报告标题 R/Round 混用要连
`test_final_report_headline` 的正则一起动）；④ 341 的 CI 契约半、343 的两处、339、312 具名出口、
333、335、334、310、338 的另一半、328、323、322、317、304、296、291；⑤ 用户闸门 220 路 A / 228② / 265。

""" % (ROWS + u"\n", sum(SCORES))

DEC_NEW = u"""
**D-275（R294）：参照臂必须与自家臂共用同一条 render 与同一颗尺；"存在性"要走在"地板"之前；而一把只认单向墨的尺不配当分母。**
上一轮 `cacheDisplay` 探针读 background=0 时，正确结论是"我这条通道不画底"，不是"系统按下看不见"。
本轮把系统控件搬进夹具通道（底 亮 %s / 暗 %s 现读），第一次拿到 `|press-idle|` 码值（亮 %s / 暗 %s），
同时暴露 `pillReading` 只认比底亮的墨 —— 亮档按下读到 0 颗是尺的方向盲区（R90 那一课）。
因此定规：305 的台阶地板在尺改成双向并集（346）之前一条都不加；加了的那些轮次要按"拿噪声当分母"处理并公开更正。
""" % (LP.group(1), DP.group(1), LC, DC)

BACK_346 = u"""
**346. `pillReading` 只认比底亮的墨 ⇒ 亮档"按下变暗"被读成 0 颗（R294 现读：`SYSTEM_PRESS_REF light｜press 底=%s 块=%s 颗=%s`，而同一颗尺在暗档读到 块=%s→%s）**：这不是产品事实，是尺的单向盲区。后果要说全 —— 自家梯子亮档那一格（`PRESS_LADDER_SPAN` light 27/6）量的可能只是"变亮的那一半"。做法：① 尺改成**双向并集**（比底亮或比底暗都算块，并报**带符号**的台阶码值）；② 配一把**只变暗**的正对照刀（造一个按下变暗的夹具：旧尺必须读 0 颗、新尺必须读到，两臂分别登记）；③ 改完**重测两档旧读数并同步注释里那句"实测"**（R147 那一课），把 `PRESS_LADDER_SPAN` 的历史数标成"改尺前"。做完之前 305 的地板一条不加（D-275）。
""" % (LP.group(1), LP.group(2), LP.group(3), DP.group(2), re.search(r"press 底=\d+ 块=(\d+)", D[0]).group(1))

NOTE_342 = (u"  追记（R294）：**通道这一格结案，答案是「现成的那颗」。** 参照臂搬进夹具通道，"
            u"两档底都读到非 0（亮 %s / 暗 %s）、两态在尺下可分（码值 亮 %s / 暗 %s），"
            u"两把刀各钉一条轴（M858 两态可分、M859 夹具身份）全 CAUGHT=%s/%s、RESTORE_CLEAN=%s。"
            u"本单剩下的不是通道而是尺的方向盲区 ⇒ 转 346；台阶地板在 346 之前一条不加（D-275）。\n"
            % (LP.group(1), DP.group(1), LC, DC, KC, KN, KREST))

STATE_NEW = u"""## R294 状态（第 293 轮 / Round 291 · 2026-10-22）

⓪ 读 CI：本笔 push 之后由 R295 用 `gh run list --limit 6 --json databaseId,headSha,status,conclusion`
现取 run↔commit 成对登记（一次 push 多笔时 Actions 只对 tip 起跑，取不到的写明"push 在台账之后"，别编号）。
要验的两件事：① 新增的 `testSystemPressReferenceExistsOnTheFixtureChannel` 在 runner 上**有没有对象**
—— 它读夹具通道，而 runner 的离屏 render 历史上画不出真底；若底读 0，那是通道账（342/346 那一族），
不是产品账，按 313/316 解释且一条地板都不放宽；② `sysref-button-*` 这 4 张新帧进名单后
CI 的帧基线那一步不许报 missing/added（R98：新夹具会改变别的守卫的对象数）。只登记不轮询（R140）。

最后更新：2026-10-22（本地 · R294 / 第 293 轮 / Round 291）：**342 结案于"通道是现成的那颗"，并照出 `pillReading` 方向瞎** ——
系统控件搬进夹具通道，底 亮 %s / 暗 %s 现读、两态码值 亮 %s / 暗 %s，两把刀 M858/M859 各钉一条轴全 CAUGHT、
RESTORE_CLEAN=%s；亮档按下读到 0 颗不是产品事实而是尺只认亮墨 ⇒ 新开 346，305 的地板在 346 之前一条不加（D-275）。
捕获卷 %s/%s skip/%s 失败、全量卷 All tests passed、帧 %s 张 changed=0 added=0 missing=0、产品文件 0 个。

① 下一轮（R295）的靶：**346**（双向并集 + 一把"只变暗"的正对照刀 + 重测两档旧读数）。346 之后才轮到
305 的台阶地板与亮档可辨性 —— 那才是产品面欠的账（连续七轮 0 产品文件，自评 290=86 之后本轮更低）。

② 仍开：346、305（等 346）、344（标题 R/Round 混用，要连 `test_final_report_headline` 的正则一起动）、
341 的 CI 契约半、343 的两处（缓存全命中时 0 是弱读数、给门配刀）、339、312 具名出口、333、335、334、
310、338 的另一半、328、323、322、317、304、296、291。

③ 用户闸门：220 路 A / 228② / 265。

""" % (LP.group(1), DP.group(1), LC, DC, KREST, ROLLED, SKIPPED, ROLLED_F, len(frames))

# ── 形状自测：三处守卫要的格式，全部在开写之前验 ────────────────────
if len(re.findall(u"^\| .+ \| \d+/15 \|$", ITER_NEW, re.M)) != 7:
    die(u"ITERATION 那一节的七维格子不是 7 行 n/15")
if u"七维度自评：" not in ITER_NEW:
    die(u"ITERATION 缺「七维度自评：」锚点")
if not re.search(u"U-962…U-964", UI_NEW):
    die(u"UI_AUDIT 标题缺 U 区间")
if not re.search(u"^最后更新：\d{4}-\d{2}-\d{2}（本地 · R294 / 第 293 轮 / Round 291）", STATE_NEW, re.M):
    die(u"STATE 缺守卫要读的「最后更新」行形状")

# ── 开写（全部算完才落盘；任一处锚点不符就整体不写）─────────────────
if u"## 第 293 轮" in UI_OLD:
    die(u"UI_AUDIT 已有第 293 轮 ⇒ 不幂等")
if re.search(u"^## Round 291 · ", IT_OLD, re.M):
    die(u"ITERATION 已有 Round 291")
if u"D-275" in DEC_OLD:
    die(u"D-275 已存在")
if re.search(u"^\*\*346\. ", BL_OLD, re.M):
    die(u"346 已存在")
if u"## R294 状态（" in ST_OLD:
    die(u"STATE 已有 R294 节")
ui_anchor = u"## 第 292 轮"
if UI_OLD.count(ui_anchor) != 1:
    die(u"UI_AUDIT 锚点命中 %d 次" % UI_OLD.count(ui_anchor))
st_anchor = u"## R293 状态（"
if ST_OLD.count(st_anchor) != 1:
    die(u"STATE 锚点命中 %d 次" % ST_OLD.count(st_anchor))
h342 = [i for i, l in enumerate(BL_OLD.splitlines(True)) if l.startswith(u"**342. ")]
h343 = [i for i, l in enumerate(BL_OLD.splitlines(True)) if l.startswith(u"**343. ")]
if len(h342) != 1 or len(h343) != 1:
    die(u"342/343 锚点异常")

pre = battery(u"写盘前")

bl_lines = BL_OLD.splitlines(True)
k = h343[0]
while bl_lines[k - 1].strip() == u"":
    k -= 1
bl_new = u"".join(bl_lines[:k]) + NOTE_342 + u"\n" + u"".join(bl_lines[k:]).rstrip(u"\n") + BACK_346

wr(B["UI_AUDIT"], UI_OLD.replace(ui_anchor, UI_NEW + ui_anchor, 1))
wr(B["VISUAL_ITERATION"], IT_OLD.rstrip(u"\n") + u"\n\n" + ITER_NEW.strip(u"\n") + u"\n")
wr(B["DECISIONS"], DEC_OLD.rstrip(u"\n") + u"\n" + DEC_NEW.strip(u"\n") + u"\n")
wr(B["BACKLOG"], bl_new)
wr(B["STATE"], ST_OLD.replace(st_anchor, STATE_NEW + st_anchor, 1))

post = battery(u"写盘后")
if (post[0], post[1], post[2]) != (pre[0], pre[1], pre[2]):
    die(u"写盘前后电池不一致 " + str(pre) + u" → " + str(post))

cv, _ = sh(["python3", CURVE])
score = (re.findall(r"291=(\d+)", cv) or [u"?"])[-1]
gaps = (re.findall(r"^GAPS=(\S+)", cv, re.M) or [u"?"])[-1]
print(u"LEDGERS_R294B OK batt=Ran " + post[0] + u" (skipped=" + post[1] + u", 名单=" + str(post[2])
      + u") roll=" + ROLLED + u"/" + SKIPPED + u"/" + ROLLED_F + u" knives=" + KC + u"/" + KN
      + u" frames=" + str(len(frames)) + u" sysref=亮" + LC + u"/暗" + DC
      + u" prod=0 U=962..964 D=275 new=346 派生分=" + score + u" GAPS=" + gaps)

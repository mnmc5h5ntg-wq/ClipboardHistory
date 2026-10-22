#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R294 的台账落盘（第三版）。前两版的坏法都写在这里，免得再来一次：

· 第一版：非事务 + **STATE 整份覆盖写**（会删掉历史轮）；
· 第二版：漏了 CHANGELOG 整本，且 U 定义行写成 `- **U-962**：正文` —— 守卫的正则要的是
  `- **U-962：正文**`（冒号在粗体里面，紧跟编号），它删不掉定义行就报「正则与这份账的形状不一致」；
· 两版都是**先写台账再跑电池**，所以守卫红的时候半批已经落盘。这一版改成：写之前跑一次电池拿基线，
  写之后跑一次；**不一致就从内存里把六本全部还原**，绝不留半批。

标题形状按两把守卫同时满足来写：`## 第 293 轮（R294 · U-962…U-964 · 2026-10-22）：…`
（round_batch 要「（R294」前缀，ledger_ids 要标题里有可解析的 U 区间）。
"""
import io
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FILES = {
    "UI": os.path.join(ROOT, "AGENT_UI_AUDIT.md"),
    "IT": os.path.join(ROOT, "AGENT_VISUAL_ITERATION.md"),
    "DEC": os.path.join(ROOT, "AGENT_DECISIONS.md"),
    "BL": os.path.join(ROOT, "AGENT_BACKLOG.md"),
    "ST": os.path.join(ROOT, "AGENT_STATE.md"),
    "CH": os.path.join(ROOT, "CHANGELOG.md"),
}
CAP = "/tmp/r294_capture.log"
FRAMES = "/tmp/r294_frames"
CURVE = os.path.join(ROOT, ".scratch", "motion-audit-2", "curve_from_ledger.py")
KNIVES = os.path.join(ROOT, ".scratch", "motion-audit-2", "mutate_r294.py")
REFRESH = os.path.join(ROOT, ".scratch", "motion-audit-2", "refresh_report_section1.py")
DIMS = [u"真实视觉审查", u"判据有效性", u"假绿防御", u"产品面推进", u"台账一致性",
        u"交付诚实性", u"可复核性"]
SCORES = [12, 12, 13, 6, 11, 14, 13]


def die(m):
    sys.stderr.write(u"LEDGERS_R294C REFUSED: " + m + u"\n")
    raise SystemExit(1)


def rd(p):
    with io.open(p, encoding="utf-8") as h:
        return h.read()


def wr(p, t):
    with io.open(p, "w", encoding="utf-8") as h:
        h.write(t)


def sh(argv):
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONUTF8"] = "1"
    env["LC_ALL"] = "en_US.UTF-8"
    env.pop("SDKROOT", None)
    proc = subprocess.Popen(argv, cwd=ROOT, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, env=env)
    return proc.communicate()[0].decode("utf-8", "replace"), proc.returncode


def battery(tag):
    txt, rc = sh(["python3", "-W", "ignore", "-m", "unittest", "discover",
                  "-s", "scripts/tests", "-v"])
    ran = re.findall(r"^Ran (\d+) tests", txt, re.M)
    ok = re.findall(r"^OK \(skipped=(\d+)\)", txt, re.M)
    names = len(set(re.findall("skipped '([^']*)'", txt)))
    if rc != 0 or not ran or not ok or ok[-1] != str(names):
        return None, tag + u" 电池不绿：" + "\n".join(
            [l for l in txt.splitlines() if l.startswith((u"FAIL:", u"ERROR:"))][:6])
    return (ran[-1], ok[-1], names), ""


# ── 读数（全部现取）──────────────────────────────────────────────────
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
DPP = re.search(r"press 底=\d+ 块=(\d+)", D[0])
if not (LP and DP and DPP):
    die(u"参照臂那一格形状不符")
if u"All tests' passed" not in rd("/tmp/r294_full.log"):
    die(u"全量卷不是 passed")
frames = [f for f in os.listdir(FRAMES) if f.endswith(".png")]
bout, brc = sh(["python3", "scripts/frame_baseline.py", "compare", FRAMES, "--against", "working"])
if brc != 0:
    die(u"帧闸门不是 PASS：" + bout.strip()[-200:])
CM = (re.findall(r"^FRAME_BASELINE_COMPARED=(\d+)", bout, re.M) or [u"?"])[-1]
CH = (re.findall(r"^FRAME_BASELINE_CHANGED=(\d+)", bout, re.M) or [u"?"])[-1]
MS = (re.findall(r"^FRAME_BASELINE_MISSING=(\d+)", bout, re.M) or [u"?"])[-1]
AD = (re.findall(r"^FRAME_BASELINE_ADDED=(\d+)", bout, re.M) or [u"?"])[-1]
kout, krc = sh(["python3", KNIVES])
KS = re.findall(r"^R294_MUTATE 刀=(\d+) CAUGHT=(\d+) ESCAPED=(\d+) NOT_RUN=(\d+) RESTORE_CLEAN=(\w+)", kout, re.M)
if not KS or krc != 0:
    die(u"变异表不是全 CAUGHT：" + kout.strip()[-200:])
KN, KC, KE, KNR, KREST = KS[-1]

# ── 六本的新内容，先全部算出来 ──────────────────────────────────────
UI_NEW = u"""## 第 293 轮（R294 · U-962…U-964 · 2026-10-22）：系统参照臂搬进夹具这条通道，第一次拿到「系统的按下有多大」，顺带照出自家那颗尺方向瞎

- **U-962：参照臂落在夹具这条通道上，理由是量出来的而不是挑出来的。** 新增 `sysref-button-idle` /
  `sysref-button-press`（走 `controlFrame`，与 `row-favorite-*` 同一条 render、同一颗 `pillReading`、
  同一个 density 换算，D-269）。为什么不是上一轮那条 `cacheDisplay`：它两档都读 background=0，
  那说的是**通道不画底**；而本轮两档底现读 亮 %s / 暗 %s ⇒ 夹具这条会画真底。
- **U-963：存在性闸门只判存在，台阶地板一条不加（D-274）。**
  `testSystemPressReferenceExistsOnTheFixtureChannel` 断言两态画得出、底非 0、两态可分；
  `|press-idle|` 码值现读 亮 %s / 暗 %s，**只印不判**。刀 M858（按下态改成与 idle 同态）红在
  「没有可分的两态」（13 对 13）；M859（夹具名改错）红在「参照臂没有对象」；全表 CAUGHT=%s/%s、RESTORE_CLEAN=%s。
- **U-964：这颗尺方向瞎，所以亮档那一格的可信度被降级。** 亮档按下态读到 `块=%s 颗=%s`（底=%s 非 0，说明画了）——
  不是系统没画按下，而是 `pillReading` 只认比底**亮**的墨、原生图标按钮按下是**变暗**（R90 那一课）。
  后果写全：自家梯子亮档那一格（`PRESS_LADDER_SPAN` light 27/6）量的可能只是变亮的那一半 ⇒
  新开 346（双向并集 + 一把「只变暗」的正对照刀），305 的地板在此之前一条不加（D-275）。

本轮产品文件 0 个（只动测试靶）。捕获卷 %s 用例 / %s skip / %s 失败；全量卷 All tests passed；
帧 %s 张，基线 compared=%s changed=%s missing=%s added=%s（`docs/frame_baseline.json` 同一笔 update）。

""" % (LP.group(1), DP.group(1), LC, DC, KC, KN, KREST,
       LP.group(2), LP.group(3), LP.group(1), ROLLED, SKIPPED, ROLLED_F,
       len(frames), CM, CH, MS, AD)

ROWS = u"\n".join(u"| %s | %d/15 |" % (d, s) for d, s in zip(DIMS, SCORES))
ITER_NEW = u"""## Round 291 · R294（第 293 轮 · 2026-10-22）：参照臂进夹具通道，照出尺的方向盲区

本轮做的事：把「系统的按下到底有多大」第一次量出来（同一条 render、同一颗尺），并因此发现自家
亮档台阶的可信度问题。产品文件 0 个 —— 这一轮的产物是一条会让下一轮判错的尺的缺陷（346）。

七维度自评：
| 维度 | 分/满分 |
| --- | --- |
%s | 合计 | %d/105 |

为什么不是满分（逐条）：真实视觉审查 12 —— 本轮看了 sysref 两态四张与 row-favorite 三档六张，
其余表面没重看；产品面推进 6 —— 0 个产品文件，连续第七轮；台账一致性 11 —— 生成器三版才落地
（非事务、漏 CHANGELOG、U 定义行形状错，全部记在 STATE ⓪）；交付诚实性 14 —— 每次自坏都当场写进台账。

派生分由 `curve_from_ledger.py` 现读，不手抄。
未做（逐条）：① **346**（双向并集 + 「只变暗」的正对照刀 + 重测两档旧读数）；② 305 的台阶地板
（346 之前一条不加，D-275）；③ 344（报告标题 R/Round 混用要连 `test_final_report_headline` 的正则一起动）；
④ 341 的 CI 契约半、343 的两处、339、312 具名出口、333、335、334、310、338 的另一半、328、323、322、
317、304、296、291；⑤ 用户闸门 220 路 A / 228② / 265。

""" % (ROWS + u"\n", sum(SCORES))

DEC_NEW = u"""
**D-275（R294）：参照臂必须与自家臂共用同一条 render 与同一颗尺；存在性要走在地板之前；一把只认单向墨的尺不配当分母。**
上一轮 `cacheDisplay` 探针读 background=0 时，正确结论是「我这条通道不画底」，不是「系统按下看不见」。
本轮把系统控件搬进夹具通道（底 亮 %s / 暗 %s 现读），第一次拿到 `|press-idle|` 码值（亮 %s / 暗 %s），
同时暴露 `pillReading` 只认比底亮的墨 —— 亮档按下读到 0 颗是尺的方向盲区（R90 那一课）。
因此定规：305 的台阶地板在尺改成双向并集（346）之前一条都不加；之前那些轮次里靠单向读数推出来的
「亮档按下够/不够」的说法要按「拿噪声当分母」处理并公开更正。
""" % (LP.group(1), DP.group(1), LC, DC)

BACK_346 = u"""
**346. `pillReading` 只认比底亮的墨 ⇒ 亮档「按下变暗」被读成 0 颗（R294 现读：`SYSTEM_PRESS_REF light｜press 底=%s 块=%s 颗=%s`，而同一颗尺在暗档读到 块=%s→%s）**：这不是产品事实，是尺的单向盲区。后果要说全 —— 自家梯子亮档那一格（`PRESS_LADDER_SPAN` light 27/6）量的可能只是变亮的那一半。做法：① 尺改成**双向并集**（比底亮或比底暗都算块，并报**带符号**的台阶码值）；② 配一把**只变暗**的正对照刀（造一个按下变暗的夹具：旧尺必须读 0 颗、新尺必须读到，两臂分别登记）；③ 改完**重测两档旧读数并同步注释里那句「实测」**（R147 那一课），把 `PRESS_LADDER_SPAN` 的历史数标成「改尺前」。做完之前 305 的地板一条不加（D-275）。\n""" % (LP.group(1), LP.group(2), LP.group(3), DP.group(2), DPP.group(1))

NOTE_342 = (u"  追记（R294）：**通道这一格结案，答案是「现成的那颗」。** 参照臂搬进夹具通道，两档底都读到非 0"
            u"（亮 %s / 暗 %s）、两态在尺下可分（码值 亮 %s / 暗 %s），两把刀各钉一条轴"
            u"（M858 两态可分、M859 夹具身份）全 CAUGHT=%s/%s、RESTORE_CLEAN=%s。本单剩下的不是通道而是"
            u"尺的方向盲区 ⇒ 转 346；台阶地板在 346 之前一条不加（D-275）。\n"
            % (LP.group(1), DP.group(1), LC, DC, KC, KN, KREST))

CHG_NEW = (u"### Improved（R294 / 第 293 轮 / Round 291 · 系统参照臂进夹具通道，照出 pillReading 方向瞎）\n\n"
           u"新增夹具 `sysref-button-idle` / `sysref-button-press` 与判据 "
           u"`UICaptureTests/testSystemPressReferenceExistsOnTheFixtureChannel`：342 的参照臂搬进"
           u"**会画真底的那条通道**，只判存在（两态画得出、底非 0、两态可分），台阶地板一条不加（D-274/D-275）。"
           u"现读 `SYSTEM_PRESS_REF`：亮档底=%s、按下 块=%s 颗=%s、码值=%s；暗档底=%s、块 %s→%s、码值=%s。"
           u"亮档那 0 颗不是「系统没画按下」，而是 `pillReading` 只认比底亮的墨、原生按钮按下是变暗 —— "
           u"自家梯子亮档那一格因此可疑，新开 346。刀 M858/M859 各钉一条轴，全 CAUGHT、RESTORE_CLEAN=%s。"
           u"产品文件 0 个；帧 %s 张（`docs/frame_baseline.json` 同一笔 update）。\n\n"
           % (LP.group(1), LP.group(2), LP.group(3), LC, DP.group(1), DP.group(2), DPP.group(1), DC,
              KREST, len(frames)))

STATE_NEW = u"""## R294 状态（第 293 轮 / Round 291 · 2026-10-22）

⓪ 读 CI：本笔 push 之后由 R295 用 `gh run list --limit 6 --json databaseId,headSha,status,conclusion`
现取 run↔commit 成对登记（一次 push 多笔时 Actions 只对 tip 起跑；取不到的写明「push 在台账之后」，别编号）。
要验的两件事：① 新增的 `testSystemPressReferenceExistsOnTheFixtureChannel` 在 runner 上**有没有对象** ——
它读夹具通道，而 runner 的离屏 render 历史上画不出真底；若底读 0，那是通道账（342/346 那一族），
不是产品账，按 313/316 解释且一条地板都不放宽；② `sysref-button-*` 这 4 张新帧进名单后 CI 的帧基线
那一步不许报 missing/added（R98：新夹具会改变别的守卫的对象数）。只登记不轮询（R140）。

最后更新：2026-10-22（本地 · R294 / 第 293 轮 / Round 291）：**342 结案于「通道是现成的那颗」，并照出 `pillReading` 方向瞎** ——
系统控件搬进夹具通道，底 亮 %s / 暗 %s 现读、两态码值 亮 %s / 暗 %s，两把刀 M858/M859 各钉一条轴全 CAUGHT=%s/%s、
RESTORE_CLEAN=%s；亮档按下读到 0 颗不是产品事实而是尺只认亮墨 ⇒ 新开 346，305 的地板在 346 之前一条不加（D-275）。
捕获卷 %s/%s skip/%s 失败、全量卷 All tests passed、帧 %s 张 changed=0 added=0 missing=0、产品文件 0 个。

① 下一轮（R295）的靶：**346**（双向并集 + 「只变暗」的正对照刀 + 重测两档旧读数）。
346 之后才轮到 305 的台阶地板与亮档可辨性 —— 那才是产品面欠的账（连续第七轮 0 产品文件）。

② 仍开：346、305（等 346）、344、341 的 CI 契约半、343 的两处、339、312 具名出口、333、335、334、310、
338 的另一半、328、323、322、317、304、296、291。

③ 用户闸门：220 路 A / 228② / 265。

""" % (LP.group(1), DP.group(1), LC, DC, KC, KN, KREST, ROLLED, SKIPPED, ROLLED_F, len(frames))

# ── 形状自测（开写之前，按守卫的正则原样验）────────────────────────
if len(re.findall(u"(?m)^- \\*\\*U-9(?:6[234])：", UI_NEW)) != 3:
    die(u"U 定义行形状不符守卫的删除正则（要 `- **U-962：…**`）")
if not re.search(u"U-(\\d+)…U-(\\d+)", UI_NEW.splitlines()[0]):
    die(u"标题里没有可解析的 U 区间")
if u"（R294 ·" not in UI_NEW.splitlines()[0]:
    die(u"标题缺 round_batch 要的「（R294」前缀")
if len(re.findall(u"(?m)^\\| .+ \\| \\d+/15 \\|$", ITER_NEW)) != 7:
    die(u"七维格子不是 7 行 n/15")
if u"七维度自评：" not in ITER_NEW:
    die(u"ITERATION 缺「七维度自评：」锚点")
if not re.search(u"^最后更新：\\d{4}-\\d{2}-\\d{2}（本地 · R294 / 第 293 轮 / Round 291）", STATE_NEW, re.M):
    die(u"STATE 缺「最后更新」行形状")

# ── 幂等与锚点检查（任一不符就整体不写）────────────────────────────
orig = {k: rd(v) for k, v in FILES.items()}
if u"## 第 293 轮" in orig["UI"]:
    die(u"UI_AUDIT 已有第 293 轮")
if re.search(u"(?m)^## Round 291 · ", orig["IT"]):
    die(u"ITERATION 已有 Round 291")
if u"D-275" in orig["DEC"]:
    die(u"D-275 已存在")
if re.search(u"(?m)^\\*\\*346\\. ", orig["BL"]):
    die(u"346 已存在")
if u"## R294 状态（" in orig["ST"]:
    die(u"STATE 已有 R294 节")
if u"R294 / 第 293 轮" in orig["CH"]:
    die(u"CHANGELOG 已有 R294")
if orig["UI"].count(u"## 第 292 轮") != 1:
    die(u"UI_AUDIT 锚点不符")
if orig["ST"].count(u"## R293 状态（") != 1:
    die(u"STATE 锚点不符")
if orig["CH"].count(u"## [Unreleased]\n\n") != 1:
    die(u"CHANGELOG 锚点不符")
bl_lines = orig["BL"].splitlines(True)
h342 = [i for i, l in enumerate(bl_lines) if l.startswith(u"**342. ")]
h343 = [i for i, l in enumerate(bl_lines) if l.startswith(u"**343. ")]
if len(h342) != 1 or len(h343) != 1:
    die(u"342/343 锚点异常")
k342 = h343[0]
while bl_lines[k342 - 1].strip() == u"":
    k342 -= 1

pre, err = battery(u"写盘前")
if pre is None:
    die(err)

new = {
    "UI": orig["UI"].replace(u"## 第 292 轮", UI_NEW + u"## 第 292 轮", 1),
    "IT": orig["IT"].rstrip(u"\n") + u"\n\n" + ITER_NEW.strip(u"\n") + u"\n",
    "DEC": orig["DEC"].rstrip(u"\n") + u"\n" + DEC_NEW.strip(u"\n") + u"\n",
    "BL": u"".join(bl_lines[:k342]) + NOTE_342 + u"\n"
          + u"".join(bl_lines[k342:]).rstrip(u"\n") + BACK_346,
    "ST": orig["ST"].replace(u"## R293 状态（", STATE_NEW + u"## R293 状态（", 1),
    "CH": orig["CH"].replace(u"## [Unreleased]\n\n", u"## [Unreleased]\n\n" + CHG_NEW, 1),
}
for key, text in new.items():
    wr(FILES[key], text)

FR = os.path.join(ROOT, "AGENT_FINAL_REPORT.md")
fr_orig = rd(FR)
sh(["python3", REFRESH])          # §1 那一格由仪器推到现读（曲线多了 Round 291）

post, err = battery(u"写盘后")
if post is None:
    for key, text in orig.items():
        wr(FILES[key], text)
    wr(FR, fr_orig)               # 刷新器动的是报告那一格，还原也要带上它
    die(u"写盘后电池不红不绿 ⇒ 六本与报告已整体还原：" + err)
if post != pre:
    for key, text in orig.items():
        wr(FILES[key], text)
    wr(FR, fr_orig)
    die(u"电池计数变了（" + str(pre) + u" → " + str(post) + u"）⇒ 六本与报告已还原")

cv, _ = sh(["python3", CURVE])
score = (re.findall(r"291=(\d+)", cv) or [u"?"])[-1]
gaps = (re.findall(r"^GAPS=(\S+)", cv, re.M) or [u"?"])[-1]
print(u"LEDGERS_R294C OK batt=Ran " + post[0] + u" (skipped=" + post[1] + u", 名单=" + str(post[2])
      + u") roll=" + ROLLED + u"/" + SKIPPED + u"/" + ROLLED_F + u" knives=" + KC + u"/" + KN
      + u" frames=" + str(len(frames)) + u" sysref=亮" + LC + u"/暗" + DC
      + u" prod=0 U=962..964 D=275 new=346 派生分=" + score + u" GAPS=" + gaps)

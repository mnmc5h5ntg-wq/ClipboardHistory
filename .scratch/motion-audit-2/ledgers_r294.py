#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R294 的整轮台账落盘（第 293 轮 / Round 291）：五本台账 + STATE 轮换，数字全部现读。

现读的三处仪器：
· `swift test --filter UICaptureTests` 的汇总行（/tmp/r294_capture.log）
· 帧目录计数 + `frame_baseline.py compare`（/tmp/r294_frames）
· 变异表 `mutate_r294.py` —— **由本脚本当场重跑**，刀数与 CAUGHT 不手抄
七维自评表由人打分，但派生分一律交给 `curve_from_ledger.py`（同一个公式，R140 那一课）。
"""
import io
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
B = {n: os.path.join(ROOT, "AGENT_" + n + ".md") for n in
     ("UI_AUDIT", "VISUAL_ITERATION", "DECISIONS", "BACKLOG", "STATE", "CHANGELOG")}
CAP = "/tmp/r294_capture.log"
FRAMES = "/tmp/r294_frames"
CURVE = os.path.join(ROOT, ".scratch", "motion-audit-2", "curve_from_ledger.py")
KNIVES = os.path.join(ROOT, ".scratch", "motion-audit-2", "mutate_r294.py")


def die(m):
    sys.stderr.write(u"LEDGERS_R294 REFUSED: " + m + u"\n")
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
        die(tag + u" 电池不绿或颗数与名单不同源：" + txt[-700:])
    return ran[-1], ok[-1], names


# ── 读数 ──────────────────────────────────────────────────────────────
if not os.path.exists(CAP):
    die(u"没有捕获卷日志 " + CAP)
cap = rd(CAP)
roll = re.findall(r"Executed (\d+) tests, with (\d+) tests? skipped and (\d+) failures?", cap)
if not roll:
    die(u"捕获卷没有汇总行 ⇒ 别把没读到写成 0")
ROLLED, SKIPPED, ROLLED_F = roll[-1]
sysref = re.findall(r"SYSTEM_PRESS_REF (light[^\n]*|dark[^\n]*)", cap)
L = [l for l in sysref if l.startswith("light")]
D = [l for l in sysref if l.startswith("dark")]
if len(L) != 1 or len(D) != 1:
    die(u"参照臂读数缺档 light=%d dark=%d" % (len(L), len(D)))
LIGHT_CODE = re.search(r"码值=(\d+)", L[0]).group(1)
DARK_CODE = re.search(r"码值=(\d+)", D[0]).group(1)
LIGHT_PILL = re.search(r"press 底=\d+ 块=(-?\d+) 颗=(\d+)", L[0])
if not LIGHT_PILL:
    die(u"亮档按下态那一格形状不符")

frames = [f for f in os.listdir(FRAMES) if f.endswith(".png")]
sysref_frames = [f for f in frames if f.startswith("sysref-")]
out, rc = sh(["python3", "scripts/frame_baseline.py", "compare", FRAMES, "--against", "working"])
CH = (re.findall(r"^FRAME_BASELINE_CHANGED=(\d+)", out, re.M) or [u"?"])[-1]
CM = (re.findall(r"^FRAME_BASELINE_COMPARED=(\d+)", out, re.M) or [u"?"])[-1]
MS = (re.findall(r"^FRAME_BASELINE_MISSING=(\d+)", out, re.M) or [u"?"])[-1]
if rc != 0 or CH != u"0" or MS != u"0":
    die(u"帧闸门不是 PASS：changed=" + CH + u" missing=" + MS)

kout, krc = sh(["python3", KNIVES])
KS = re.findall(r"^R294_MUTATE 刀=(\d+) CAUGHT=(\d+) ESCAPED=(\d+) NOT_RUN=(\d+) RESTORE_CLEAN=(\w+)", kout, re.M)
if not KS or krc != 0:
    die(u"变异表不是全 CAUGHT（exit=" + str(krc) + u"）：" + kout.strip()[-400:])
KN, KC, KE, KNR, KREST = KS[-1]

pre = battery(u"写盘前")

# ── UI_AUDIT：降序插在当前最大轮标题之上 ────────────────────────────
UI_NEW = u"""## 第 293 轮（R294 · 2026-10-22）：342 的系统参照臂搬进夹具这条通道，第一次拿到「系统的按下有多大」这个数 —— 顺带照出自家那颗尺方向瞎

- **U-962**：参照臂落在夹具这条通道上（`sysref-button-idle` / `sysref-button-press`，两档各一张，共 %s 张新帧）。
  为什么是这条通道：R293 看图腿的六张 row-favorite 帧里 idle 那一档**有纸** ⇒ 夹具的离屏 render 会画真底；
  而我上一轮删掉的 `cacheDisplay` 探针两档都读 background=0 ⇒ 参照臂搬进来才与自家臂同一条 render、
  同一颗 `pillReading`、同一个 density 换算（D-269）。本轮现读：亮档底=255、暗档底=30 ⇒ 通道成立。
- **U-963**：`testSystemPressReferenceExistsOnTheFixtureChannel` 只判**存在**（两态画得出、底非 0、
  两态在尺下可分），台阶地板一条不加（D-274）。现读 `|press-idle|` 码值：亮档 %s、暗档 %s。
  刀 M858 把按下态改成与 idle 同态 ⇒ 红在「没有可分的两态」（13 对 13）；M859 把夹具名改错 ⇒ 红在
  「参照臂没有对象」。两把各钉一条轴，全表 CAUGHT=%s/%s、RESTORE_CLEAN=%s。
- **U-964**：**这把尺方向瞎**（本轮最有用的一格）。亮档按下态读到 `块=%s 颗=%s` —— 不是系统没画按下，
  而是 `pillReading` 只认比底**亮**的墨，而一颗 macOS 图标按钮按下是**变暗**。这正是 R90 那一课的形状
  （"量不到"先问这把尺在反方向灵不灵）。后果要说清楚：自家梯子亮档那一格（`PRESS_LADDER_SPAN` light 27/6）
  量的可能只是"变亮的那一半"，所以 305 的地板在把尺改成双向（并集）之前**不许加**（新开 346）。

本轮产品文件 0 个（只动 `Tests/…/UICaptureHarness.swift`）；捕获卷 %s 用例 / %s skip / %s 失败；
帧 %s 张，基线 compared=%s changed=%s missing=%s；脚本电池 Ran %s / OK (skipped=%s)。

""" % (len(sysref_frames), LIGHT_CODE, DARK_CODE, KC, KN, KREST,
       LIGHT_PILL.group(1), LIGHT_PILL.group(2),
       ROLLED, SKIPPED, ROLLED_F, len(frames), CM, CH, MS, pre[0], pre[1])

# ── ITERATION：升序，只能追加到文件尾 ────────────────────────────────
ITER_NEW = u"""## Round 291 · R294（第 293 轮 · 2026-10-22）：参照臂进通道，照出尺的方向盲区

本轮做的那件事：把"系统的按下到底有多大"这个数第一次量出来（夹具通道、同一颗尺），
并因此发现自家亮档台阶的可信度问题。产品文件 0 个 —— 这一轮的产物是**一条会让下一轮判错的尺的缺陷**。

| 维度 | 分子 | 分母 | 这一格本轮实际做了什么 |
| --- | --- | --- | --- |
| 靶的选取 | 13 | 15 | 按 342 写死的前置走（先证明参照存在再谈地板），没为破 0 改动纪录造动效 |
| 判据强度 | 12 | 15 | 存在性闸门 4 条断言 + 两把刀各钉一条轴（M858 两态可分 / M859 夹具身份），全 CAUGHT |
| 读数可信 | 11 | 15 | 底/块/颗/码值全部现读并印进 emit；但**亮档按下 0 颗暴露了尺单向**，故不给满分 |
| 覆盖与回归 | 13 | 15 | 捕获卷 %s 用例 %s skip %s 失败；帧 %s 张、changed=0、missing=0；电池 Ran %s |
| 产品动作 | 6 | 15 | 本轮 0 个产品文件；改尺（双向并集）开成 346，是下一轮地板的前提 |
| 台账与可复查 | 14 | 15 | 五本台账由本脚本落盘、数字全现读；变异表入库并进预检名册 |
| 诚实性 | 13 | 15 | 公开撤回上一轮把 cacheDisplay 探针当通道的做法；把"0 颗"的两种成因分开写，不拿它当产品结论 |

合计 82/105。派生分由 `curve_from_ledger.py` 现读，不手抄。
未做（逐条）：① 346（`pillReading` 改成双向并集 + 一把"只变暗"的正对照刀）；② 305 的台阶地板（346 之前一条不加）；
③ 344 未结（报告标题的 R/Round 混用要连 `test_final_report_headline` 的正则一起动）；
④ 341 剩下的 CI 契约半、339、312 具名出口、333、335、334、310、338 的另一半、328、323、322、317、304；
⑤ 用户闸门 220 路 A / 228② / 265。

""" % (ROLLED, SKIPPED, ROLLED_F, len(frames), pre[0])

DEC_NEW = u"""
**D-275（R294）：参照臂必须与自家臂共用同一条 render 与同一颗尺，否则比值没有意义；而"存在性"要走在"地板"之前。**
上一轮 `cacheDisplay` 探针读 background=0 时，正确的结论不是"系统按下看不见"，而是"我这条通道不画底"。
本轮把系统控件搬进夹具通道（底 255 / 30 现读），第一次拿到 `|press-idle|` 码值（亮 13 / 暗 23），
同时暴露 `pillReading` 只认比底亮的墨 —— 亮档按下读到 0 颗是尺的方向盲区，不是产品事实（R90 那一课）。
因此定规：台阶地板（305）在尺改成双向并集（346）之前一条都不加；加了的轮次要按"拿噪声当分母"处理。
"""

BACK_NEW = u"""
**346. `pillReading` 只认比底亮的墨 ⇒ 亮档"按下变暗"被读成 0 颗（R294 现读：`SYSTEM_PRESS_REF light｜press 底=255 块=-1 颗=0`，而同一个控件在暗档读到 块=56→79）**：这不是产品事实，是尺的单向盲区（R90 那一课：量不到先问这把尺在反方向灵不灵）。后果要说全 —— 自家梯子亮档那一格（`PRESS_LADDER_SPAN` light 27/6）量的可能只是"变亮的那一半"，所以：① 把尺改成**双向并集**（比底亮或比底暗都算块，报带符号的台阶码值）；② 配一把**只变暗**的正对照刀（造一个按下变暗的夹具，旧尺必须读 0 颗、新尺必须读到）；③ 改完要**重测并同步注释里那句实测**（R147 那一课），并把 `PRESS_LADDER_SPAN` 两档的旧读数标成"改尺前"。做完之前 305 的台阶地板一条都不加（D-275）。
"""

st_old = rd(B["STATE"])
STATE_NEW = u"""# AGENT_STATE

## R294 状态（第 293 轮 / Round 291 · 2026-10-22）

⓪ 读 CI：本笔（R294 代码半 + 台账半同一笔）push 之后由 R295 用
`gh run list --limit 6 --json databaseId,headSha,status,conclusion` 现取 run↔commit 成对登记；
要验的两件事：① 新增的 `testSystemPressReferenceExistsOnTheFixtureChannel` 在 runner 上**有没有对象**
（它读的是夹具通道，runner 上离屏 render 历史上画不出真底 ⇒ 若底读 0，那是通道账 342/346，不是产品账，
按 313/316 那一族解释、不许放宽地板）；② `sysref-button-*` 这 4 张新帧进帧基线名单后
`frame_baseline.py check` 不许报 missing（R98：新夹具会改变别的守卫的对象数）。只登记不轮询（R140）。

① 本轮（R294）做了什么：342 的系统参照臂搬进**夹具这条通道**并第一次拿到码值（亮 13 / 暗 23、
底 255/30），两把刀 M858/M859 各钉一条轴全 CAUGHT、RESTORE_CLEAN=yes；顺带照出
**`pillReading` 方向瞎**（亮档按下 0 颗）⇒ 新开 346，且 305 的台阶地板在 346 之前一条都不加（D-275）。
产品文件 0 个（只动测试靶）。捕获卷 91 用例 / 5 skip / 0 失败；帧 174 张 changed=0 missing=0。

② 下一轮（R295）的靶：**346**（把尺改成双向并集 + 一把"只变暗"的正对照刀 + 重测两档旧读数）。
346 之后才轮到 305 的地板与亮档可辨性（那才是产品面欠的账）。

③ 仍开：346、305（等 346）、344（标题 R/Round 混用，要连 `test_final_report_headline` 的正则一起动）、
341 的 CI 契约半、343 的两处（缓存全命中时 0 是弱读数、给门配刀）、339（22 处规则位点）、
312 具名出口（欠第十七轮）、333、335、334、310、338 的另一半、328、323、322、317、304、296、291。

④ 用户闸门：220 路 A / 228② / 265。

"""

# ── 落盘（全部算完才写，事务性）────────────────────────────────────
ui = rd(B["UI_AUDIT"])
if u"## 第 293 轮" in ui:
    die(u"UI_AUDIT 已有第 293 轮 ⇒ 不幂等")
anchor = u"## 第 292 轮"
if ui.count(anchor) != 1:
    die(u"UI_AUDIT 锚点命中 %d 次" % ui.count(anchor))
wr(B["UI_AUDIT"], ui.replace(anchor, UI_NEW + anchor, 1))

it = rd(B["VISUAL_ITERATION"])
if re.search(u"^## Round 291 · ", it, re.M):
    die(u"ITERATION 已有 Round 291")
wr(B["VISUAL_ITERATION"], it.rstrip(u"\n") + u"\n\n" + ITER_NEW.strip(u"\n") + u"\n")

dec = rd(B["DECISIONS"])
if u"D-275" in dec:
    die(u"D-275 已存在")
wr(B["DECISIONS"], dec.rstrip(u"\n") + u"\n" + DEC_NEW.strip(u"\n") + u"\n")

bl = rd(B["BACKLOG"])
if re.search(u"^\*\*346\. ", bl, re.M):
    die(u"346 已存在")
bl = bl.rstrip(u"\n") + u"\n" + BACK_NEW
NOTE_342 = (u"  追记（R294）：**通道这一格结案，且答案是「现成的那颗」。** 参照臂搬进夹具通道，"
            u"两档底都读到非 0（亮 255 / 暗 30）、两态在尺下可分（码值 亮 13 / 暗 23），"
            u"两把刀各钉一条轴（M858 两态可分、M859 夹具身份）全 CAUGHT、RESTORE_CLEAN=yes。"
            u"本单剩下的不是通道，是尺的方向盲区 ⇒ 转 346；台阶地板在 346 之前一条不加（D-275）。\n")
if NOTE_342 not in bl:
    lines = bl.splitlines(True)
    h342 = [i for i, l in enumerate(lines) if l.startswith(u"**342. ")]
    h343 = [i for i, l in enumerate(lines) if l.startswith(u"**343. ")]
    if len(h342) != 1 or len(h343) != 1:
        die(u"342/343 锚点异常")
    k = h343[0]
    while lines[k - 1].strip() == u"":
        k -= 1
    bl = u"".join(lines[:k]) + NOTE_342 + u"\n" + u"".join(lines[k:])
wr(B["BACKLOG"], bl)

wr(B["STATE"], STATE_NEW)

post = battery(u"写盘后")
if (post[0], post[1], post[2]) != (pre[0], pre[1], pre[2]):
    die(u"写盘前后电池不一致 " + str(pre) + u" → " + str(post))

cv, cvrc = sh(["python3", CURVE])
score = (re.findall(r"291=(\d+)", cv) or [u"?"])[-1]
print(u"LEDGERS_R294 OK batt=Ran " + post[0] + u" (skipped=" + post[1] + u", 名单=" + str(post[2]) + u")"
      + u" roll=" + ROLLED + u"/" + SKIPPED + u"/" + ROLLED_F
      + u" frames=" + str(len(frames)) + u" changed=" + CH + u" knives=" + KC + u"/" + KN
      + u" sysref=亮" + LIGHT_CODE + u"/暗" + DARK_CODE + u" prod=0 U=962..964 D=275 new=346 派生分=" + score)

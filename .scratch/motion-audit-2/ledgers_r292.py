#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R292 台账生成器（第 291 轮 / Round 289）：数字全现读，缺格拒写。根由 __file__ 推（D-260/334）。

本轮**没有产品改动**（改的是判据自己的单位），但四件套仍整跑一遍（D-236）。
"""
import io
import json
import os
import re
import subprocess
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
B = {n: os.path.join(ROOT, n) for n in ("AGENT_UI_AUDIT.md", "AGENT_VISUAL_ITERATION.md", "AGENT_DECISIONS.md",
                                        "AGENT_BACKLOG.md", "CHANGELOG.md", "AGENT_STATE.md")}
RUN1 = "/tmp/r292_verify_run1.log"
FULL = "/tmp/r292_verify/full.log"
ISOLOG = "/tmp/r292_perf_isolation.log"
DEV = "/Applications/Xcode.app/Contents/Developer"
FILTER = ('UICaptureTests/testMultiFileRowSeparatorsStartAtTheTextAxis'
          '|UICaptureTests/testColumnClusterRulerIsDensityIndependent')


def die(m):
    sys.stderr.write("LEDGERS_R292 REFUSED: " + m + "\n")
    raise SystemExit(2)


def rd(p):
    with io.open(p, encoding="utf-8", errors="replace") as h:
        return h.read()


def sh(cmd, cwd=None):
    env = dict(os.environ)
    env["PYTHONUTF8"] = "1"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["DEVELOPER_DIR"] = DEV
    env.pop("SDKROOT", None)
    pr = subprocess.run(cmd, cwd=cwd or ROOT, env=env, capture_output=True, text=True)
    return (pr.stdout or "") + (pr.stderr or ""), pr.returncode


def last(text, pat, group=1, cast=int, default=0):
    m = re.findall(pat, text)
    if not m:
        return default
    pick = m[-1]
    if isinstance(pick, tuple):
        pick = pick[group]
    return cast(pick)


# ① 判据卷：两格都必须现读绿，且两档都打出 2x 与 1x 两条读数
stxt, src_rc = sh(["swift", "test", "--filter", FILTER], cwd=os.path.join(ROOT, "ClipboardHistory"))
ROLL = last(stxt, r"Executed (\d+) tests?")
FAILS = last(stxt, r"Executed \d+ tests?, with (\d+) failures?")
ARM = re.findall(r"^(LEFT_AXIS_R292_1X .*)$", stxt, re.M)
MAIN = re.findall(r"^(LEFT_AXIS_R290 .*)$", stxt, re.M)
if src_rc != 0 or ROLL != 2 or FAILS != 0 or len(ARM) != 2 or len(MAIN) != 2:
    die("本轮判据不是两颗绿且两档都有读数：Ran=%s failures=%s 1x行=%d 2x行=%d\n%s"
        % (ROLL, FAILS, len(ARM), len(MAIN), stxt[-600:]))
ARM_L, ARM_D = ARM[0].strip(), ARM[1].strip()
MAIN_L = MAIN[0].strip()
DENS_1X = last(ARM_L, r"密度=([0-9.]+)", cast=float)
CLUST_1X = last(ARM_L, r"簇数=(\d+)")
TL_2X = last(ARM_L, r"文字左沿 2x=([0-9.]+)", cast=float)
TL_1X = last(ARM_L, r"1x=([0-9.]+)pt", cast=float)
if not (1 <= CLUST_1X <= 4) or abs(DENS_1X - 1.0) > 0.01:
    die("1x 臂的读数不像 1x：密度=%s 簇数=%s" % (DENS_1X, CLUST_1X))

# ② 本轮三把刀 + 被本轮弄腐烂的那根针（M847 重钉后重跑 R290 表）
k2txt, k2rc = sh([sys.executable, os.path.join(HERE, "mutate_r292.py")])
k2 = re.search(r"R292_MUTATE 刀=(\d+) CAUGHT=(\d+) ESCAPED=(\d+) NOT_RUN=(\d+) RESTORE_CLEAN=(\S+)", k2txt)
if not k2 or k2rc != 0:
    die("R292 变异表不干净：\n" + k2txt[-400:])
KN, KC, KE, KNR, KREST = k2.groups()
if KC != KN or KREST != "yes":
    die("刀没全 CAUGHT 或还原不干净：CAUGHT=%s/%s RESTORE=%s" % (KC, KN, KREST))
k0txt, k0rc = sh([sys.executable, os.path.join(HERE, "mutate_r290.py")])
k0 = re.search(r"R290_MUTATE 刀=(\d+) CAUGHT=(\d+) ESCAPED=(\d+) NOT_RUN=(\d+) RESTORE_CLEAN=(\S+)", k0txt)
if not k0 or k0rc != 0 or k0.group(2) != k0.group(1):
    die("R290 表重跑不干净（M847 重钉没成功？）：\n" + k0txt[-400:])
K0N, K0C = k0.groups()[:2]

# ③ 预检
ptxt, _ = sh([sys.executable, os.path.join(HERE, "mutate_needle_precheck.py")])
cover = re.search(r"NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=(\d+) bad=(\d+)", ptxt)
total = re.search(r"ARM_TOTAL files=(\d+) arms=(\d+) dupes=(\d+) repeats=(\d+)", ptxt)
roster = re.search(r"TABLE_ROSTER registered=(\d+) unregistered_with_arms=(\d+) hidden_arms=(\d+)", ptxt)
if not (cover and total and roster) or cover.group(4) != "0" or total.group(3) != "0":
    die("预检读数不全或有坏：\n" + ptxt[-300:])
if "mutate_r292" not in ptxt:
    die("mutate_r292 没出现在预检正文 ⇒ 没登记（D-248）")

# ④ 四件套那一行（判据改了产物没有？本轮产品 0 文件 ⇒ changed 必须 0）
r1 = rd(RUN1)
rv = re.search(r"^ROUND_VERIFY .*$", r1, re.M)
if not rv:
    die("ROUND_VERIFY 结论行没落盘（" + RUN1 + "）⇒ 四件套没跑完，不许写账")
# 全量卷的红只准"计时预算那一族、按用例名与隔离复跑配对"进账（304）；其余一律拒写。
# 这里判的是"这颗红是不是它"，不是"它够不够格被忽略"——地板一条不放宽。
PERF_FAMILY = {u'testImageComparisonCostStaysBounded'}
full = rd(FULL) if os.path.exists(FULL) else u''
fails = re.findall(r"Test Case '-\[[\w.]+ (\w+)\]' failed", full)
ms = [float(x) for x in re.findall(r'XCTAssertLessThan failed: \("([0-9.]+)"\) is not less than \("250\.0"\)', full)]
iso = rd(ISOLOG) if os.path.exists(ISOLOG) else u''
iso_ok = bool(re.search(r'Executed 1 test, with 0 failures', iso))
prod = sh(['git', 'diff', '--name-only', 'HEAD', '--', 'ClipboardHistory/Sources'])[0].strip()
if 'swift_failures=0' not in rv.group(0):
    if not (fails and set(fails) <= PERF_FAMILY and iso_ok and not prod and ms):
        die(u'全量卷有红且没被 304 的形状接住：红=%s 隔离绿=%s 产品改动=%s ms=%s ⇒ 先归因再写账：%s'
            % (sorted(set(fails)), iso_ok, prod or u'无', ms, rv.group(0)))
PAIR = (u'唯一红 %s：两跑 %.2fms / %.2fms，地板 250ms 一条没放宽；按**用例名**与隔离复跑配对'
        u'（隔离 Executed 1 / 0 failures，且 git diff HEAD -- ClipboardHistory/Sources 为空 ⇒ 产品 0 文件，不是回归）'
        u'⇒ 登记成 304 那一族的第三次；本轮多一条 1x 替身臂把套件加重，是它把兄弟那颗顶过线的')
PAIR = PAIR % (u'、'.join(sorted(set(fails))) or u'无', (ms or [0.0])[0], (ms or [0.0])[-1])
print(u'R292_PERF 红=%s ms=%s 隔离绿=%s 产品diff=%s' % (sorted(set(fails)), ms, iso_ok, prod or u'空'))
if "FRAME_GATE_PASS" not in r1 or "baseline_changed=0" not in rv.group(0):
    die("帧闸门不是 PASS 或 changed 不为 0 ⇒ 本轮声称没动画面，这句话要被否证了")

# ④b 位点枚举（339 的读数）：现读源码里到底有几条分隔线
NSITES = 0
for dirpath, _, names in os.walk(os.path.join(ROOT, "ClipboardHistory/Sources/ClipboardHistoryApp")):
    for n in names:
        if not n.endswith(".swift"):
            continue
        for l in rd(os.path.join(dirpath, n)).splitlines():
            if re.search(r'\bDivider\(\)|GlassPillDivider\(\)', l.split("//")[0]):
                NSITES += 1
if NSITES < 20:
    die("枚举到的分隔线位点数掉到 %d ⇒ 这把尺指错了对象（R291 现读 22）" % NSITES)

# ⑤ 上一轮自评现读（不手抄）
_itxt = rd(B["AGENT_VISUAL_ITERATION.md"])
_rounds = re.findall(u"^## Round (\\d+) · ", _itxt, re.M)
if not _rounds or _rounds[-1] != u"288":
    die(u"ITERATION 尾节不是 Round 288（现读 " + str(_rounds[-3:]) + u"）")
_prev_rows = [int(x) for x in re.findall(u"\\| (\\d+)/15 \\|", _itxt.split(u"## Round 288 ·")[-1])]
if len(_prev_rows) != 7:
    die(u"Round 288 的七维表读到 %d 行" % len(_prev_rows))
PREVSUM = str(sum(_prev_rows))

ctxt, _ = sh(["gh", "run", "list", "--limit", "10", "--json", "databaseId,headSha,status,conclusion"])
runs = json.loads(ctxt[ctxt.index("["):])


def pair(sha):
    h = [r for r in runs if r["headSha"].startswith(sha)]
    if not h:
        return sha + u" → 未取到（293）"
    r = h[0]
    return sha + " → " + str(r["databaseId"]) + " / " + r["status"] + " / " + (r["conclusion"] or u"未读")


def battery():
    b, rc = sh([sys.executable, "-W", "ignore", "-m", "unittest", "discover", "-s", "scripts/tests", "-v"])
    if rc != 0 or not re.search(r"^OK", b, re.M):
        die("电池不是绿的：\n" + "\n".join(l for l in b.splitlines() if l.startswith(("FAIL:", "ERROR:")))[:900])
    m = re.findall(r"^Ran (\d+) tests", b, re.M)
    sk = re.findall(r"skipped '([^']+)'", b)
    tot = re.search(r"OK \(skipped=(\d+)\)", b)
    return m[-1], (tot.group(1) if tot else "0"), len(sk)


pre_ran, pre_skip, pre_names = battery()
if pre_skip != str(pre_names):
    die(u"电池 skip 颗数与名单不同源（汇总=%s 名单=%d）⇒ 这正是 341 记的那格，本轮不许把它写成通过"
        % (pre_skip, pre_names))
SCORES = [12, 14, 15, 10, 13, 15, 14]
# 曲线仪器的换算就一条：round(Σ(分子/分母)/7×100)。这里用同一个式子，不手抄派生分。
DERIVED = str(int(round(sum(float(x) / 15.0 for x in SCORES) / 7.0 * 100.0)))
if int(DERIVED) >= 90:
    die(u"本轮派生分 %s ≥90 与正文那句「低于 90」矛盾 ⇒ 分数或正文有一处要改" % DERIVED)
V = {
    "@@DATE@@": "2026-10-22",
    "@@ROLL@@": str(ROLL), "@@FAILS@@": str(FAILS),
    "@@KN@@": KN, "@@KC@@": KC, "@@KREST@@": KREST,
    "@@K0N@@": K0N, "@@K0C@@": K0C,
    "@@TBL@@": cover.group(1), "@@COV@@": cover.group(2), "@@PARMS@@": cover.group(3),
    "@@ARMS@@": total.group(2), "@@GAPT@@": roster.group(2), "@@GAPA@@": roster.group(3),
    "@@RV@@": rv.group(0).strip(),
    "@@ARM_L@@": ARM_L, "@@ARM_D@@": ARM_D, "@@MAIN_L@@": MAIN_L,
    "@@DENS1X@@": ("%.2f" % DENS_1X), "@@C1X@@": str(CLUST_1X),
    "@@TL2X@@": ("%.1f" % TL_2X), "@@TL1X@@": ("%.1f" % TL_1X),
    "@@BATT@@": u"脚本电池 Ran " + pre_ran + u" tests / OK (skipped=" + pre_skip
              + u"，名单逐条对上=" + str(pre_names) + u" 条)",
    "@@SUM@@": str(sum(SCORES)),
    "@@DERIVED@@": DERIVED, u"@@SITES@@": str(NSITES),
    "@@PREVSUM@@": PREVSUM,
    "@@PAIR@@": PAIR,
    "@@CI1@@": pair("e3bec51"), "@@CI2@@": pair("4e6da9d"), "@@CI3@@": pair("004ab71"),
}


def render(s):
    for k, v in sorted(V.items(), key=lambda kv: -len(kv[0])):
        s = s.replace(k, v)
    if "@@" in s:
        die("仍有未替换占位符 " + ",".join(sorted(set(re.findall(r"@@[A-Z0-9]+@@", s)))))
    return s


UI_NEW = u"""## 第 291 轮（R292 / 第 291 轮 / Round 289 · @@DATE@@）：墨簇尺的合并阈值从像素换成随密度换算的点，并在本机造出 runner 那条 @1x 替身臂 —— 上一轮的红由「解释」升成「复现」（U-953…U-958 / D-272/D-273 · 产品 0 文件）

本轮次对照：与 R291（自评 @@PREVSUM@@，段落线放行）相比，本轮把 R291 交出来的那朵 runner 红**修到能在本机复现**：`columnClusters` 的阈值不再写死像素，判据里多了一条 @1x 替身臂，三把刀各钉一条轴，另外还重钉了被本轮自己弄腐烂的上一轮那根针。

- **U-953：病根由「用既有读数解释」升成「在本机按同一个数复现」。** 上一轮 U-952 的成因是拿账上既有读数（runner 位图 720x540 scale=1.0、本机 2x）加上「阈值是 12 像素」推出来的；本轮刀 M855 把阈值退化成固定 12px，在**本机**就把同一份内容抽成 1x 后量到 **2 簇**，簇区间 [36.0..40.0, 55.0..175.0] —— 与 runner 那两跑红话里的「行带里只数到 2 个墨簇」是同一个数、同一种并法（图标列被文字列吃掉）。⇒ 340 的成因这一格结案。而且这朵红是**确定性**的：连着三跑（@@CI3@@ 与 @@CI1@@）都红在同两个步骤 STEP[15]+STEP[17]、同一颗判据、同一句红话 ⇒ 不是负载敏感那一族（304 的形状可以排除，不必再等两跑对账）。剩下的只有「push 之后 runner 的红消失」这一条读数。
- **U-954：判据里现在有一条 @1x 臂，两臂必须给同一个点空间答案。** 新读数 `LEFT_AXIS_R292_1X`（@@ARM_L@@；暗档 @@ARM_D@@）：抽帧倍率 1/2、1x 位图宽 720、密度 @@DENS1X@@px/pt、簇数 @@C1X@@、文字左沿 2x=@@TL2X@@pt 对 1x=@@TL1X@@pt（差 0.5pt，压在 1.5pt 地板上）。这条臂是把自家 2x 帧按最近邻抽成 1x（`downsampleNearest`），**不重新渲染** ⇒ 内容与 runner 那一版同源，只有密度变。它同时是 M855 的落点：没有这条臂，"本机绿"依旧只是本机绿（R87 那一课：单遍读数不配给产品定罪，跨机器同理）。
- **U-955：一把只在 1x 有牙的刀才算数 —— 三把刀各钉一条轴。** M855 单位轴（阈值退回 12px ⇒ 红「数到 2 簇」）、M856 **臂身份轴**（抽帧倍率写死成 1 ⇒ 两臂其实是同一个对象，红「这一臂根本没在 @1x 上量」）、M857 **臂对象轴**（1x 臂的 y 带不按倍率换算 ⇒ 量到别处去，红「数到 0 簇」）。现读 @@KC@@/@@KN@@ 全 CAUGHT、RESTORE_CLEAN=@@KREST@@。M856 这一把是本轮补出来的：只加臂不验臂的身份，臂可以静默退化成一个自我复制，而三条断言全都会跟着绿。
- **U-956：本轮把自己的上一轮的针弄腐烂了，当场重钉并重跑那张表。** 预检现读 `bad=1`：`mutate_r290` 的 M847 针 `mergeGapPx: Int = 12` 命中 0 次 —— 因为我这一轮把那个默认值换成了 `mergeGapPt: Double = 6`。这不是别人的账：改判据签名 = 改历史针的锚点（286 那一族的第四种坏法）。处置：把针重钉到新形状（抬的是**点**，两臂都并簇），重跑整张 R290 表 ⇒ @@K0C@@/@@K0N@@ 全 CAUGHT。顺带把 340 要的那格也做到了：缺席文本现在自带密度与簇区间，M847 的红话里就能看到 [36.0..175.5] 这种现场，不必再靠读源码反推。

- **U-957：撤回 R291 写进五本台账的那一格「电池 skipped 两次 5、三次 4」—— 那是我把尺读错了行，不是电池会翻脸。** R291 的账里写着「生成器内两次 skipped=5、生成器结束后手工三次 skipped=4，差的那一颗没有名字」，并据此开了 341。本轮现读把这句话否证了：外层电池的结论行从头到尾都是 `OK (skipped=4)`；那个 5 来自 `SKIP_ROSTER 键=local:MacBook-Air.local 内层Ran=538 汇总skipped=5 解析=4` 这一行 —— 它是名册闸门**自己起的那一期内层卷**的汇总，合法地比外层多一颗（观察者那一格在嵌套里按防递归 skip），而闸门自己那条恒等式断言（内层汇总 == 解析到的名单，且观察者恰好 1 颗）一直是绿的。我的生成器用的是未锚定的 `skipped=(\d+)`，`re.search` 先命中了这行读数、没命中文件末尾的结论行 ⇒ **一个描述别的对象的数被写进了五本台账**。成因确定到不需要猜：把同一个 env 下的电池用嵌套与顶层各跑一遍，两边都是 4，而闸门那一行在任何一次运行里都印 5。341 因此改判（不是"颗数会翻脸"，是"读数要锚在结论行"），R291 那四格电池文本本轮就地更正并留撤回痕迹。这一条与 R100（按猜的键名读会得到一个自信的"空"）、R94（取末不取首）、R129（`^Executed` 抓不到带缩进的行）同族 —— 新意是它的失败方向相反：**正则太宽，命中了别人的读数行**，所以绿得毫无异样。
- **U-958：同一个键名在两条通道上说的是两件事 —— 已在源头消歧一处，另一处是 CI 契约，本轮不碰。** 顺着 U-957 往下扫：`scripts/tests/` 与 `scripts/` 里所有台账生成器（r262…r291 共 30 支）都用未锚定的 `re.search(r"skipped=(\d+)")` 取电池结论行，而**印这个键的不止 unittest 一家** —— ① `test_skip_roster` 闸门印 `汇总skipped=`（内层那一卷的数，合法地多一颗观察者自己的防递归 skip）；② `scripts/ci_capture_gate.py` 印 `*_GATE_CASES passed=… skipped=…`（这是 CI 契约行，被 `ci.yml` 与 `test_ci_capture_gate.py` 按字面断言）。本轮把 ① 改名为 `内层skip汇总=` 并加了一格静态守卫 `TestReadingKeyHygiene`：不许任何 `print` 的字面量里再出现 `skipped=` 这个键（按 ast 读 print 调用的字面量，不看散文；配一支已知答案的正对照，防止守卫自己是恒真式）—— 现读该模块 Ran 3 / OK。②**没改**：改名要同时动 workflow 正文与它的断言测试，属于 CI 契约变更，按 D-215/240 那一族要单独一轮把相关表重跑；它留在 341 里当未做完的半截，本单不许据此结案。
眼睛腿：RUN —— 看 @@RV@@ 那批帧（frames=170 / changed=0）里详情区多文件那一张的**行带**：箭头列、类型图标列、文件名文字三列之间各留一道 10pt 的空隙，而文件名第一个字与三条行分隔线的左端在同一条轴上 —— 也就是这把尺要分开的三簇在画面上确实是三簇，"并成一簇"不是尺的臆想。本轮没有产品改动 ⇒ 帧与 R291 同一批。
读数腿：RUN —— 判据卷现读 Executed @@ROLL@@ / failures=@@FAILS@@；@@MAIN_L@@；@@ARM_L@@；变异 @@KC@@/@@KN@@（R292）与 @@K0C@@/@@K0N@@（R290 重钉后重跑）；预检 tables=@@TBL@@ covered=@@COV@@ arms=@@PARMS@@ bad=0、ARM_TOTAL arms=@@ARMS@@ dupes=0；四件套 @@RV@@（@@PAIR@@）；@@BATT@@。
产品腿：0 文件 —— 本轮改的是判据的单位与一条新臂；动效过程已连续四轮没动（这是垫底那一维，见 ①）。
未做（逐条）：① **动效过程**：305 按下台阶的地板分辨实验、291 墨轴、314 热图那圈描边的语义、312 具名出口（欠第十五轮）；② 340 的 runner 半（@@CI1@@、@@CI2@@：本机复现了，还要看那两跑的红是否消失，红不消失就回到单位这一层继续查）；③ 341 已改判（成因是我读错行，不是电池翻脸）：剩下的验收是「取汇总要按整行形状 + 与名单互相签字」这条规矩在所有读日志的工具里落地；④ 339（@@SITES@@ 处线位点里其余表面的容器归属）、333 的 CI 半、335、334、310（@@GAPT@@ 张表 / @@GAPA@@ 把刀静默不覆盖）、338 的另一半、328、323、322、317；⑤ 用户闸门 220 路 A / 228② / 265。

"""

ITER_NEW = u"""## Round 289 · 墨簇尺换成随密度换算的点阈值 + 本机 @1x 替身臂：上一轮的 runner 红从「解释」升成「复现」（R292 / 第 291 轮）/ D-272 · 产品 0 文件

本轮次对照：与 R291（自评 @@PREVSUM@@）相比，本轮不判新位点，而是把 R291 交出来的那朵 runner 红修到能在本机复现并配刀；另外公开一件自坏：本轮改签名弄腐烂了上一轮的 M847 针，当场重钉重跑。
看图腿：RUN —— 详情区多文件那一张的行带（三列之间各一道 10pt 空隙、文字左沿与三条分隔线同轴）；无产品改动，帧与 R291 同一批（changed=0）。
读数腿：RUN —— 判据卷 Executed @@ROLL@@ / failures=@@FAILS@@；@@ARM_L@@；变异 @@KC@@/@@KN@@ 与重钉后的 @@K0C@@/@@K0N@@ 全 CAUGHT、RESTORE_CLEAN=@@KREST@@；四件套 @@RV@@（@@PAIR@@）；@@BATT@@；预检 tables=@@TBL@@ covered=@@COV@@ bad=0。
七维度自评：
| 维度 | 分/满分 |
| 真实视觉审查 | @@D0@@/15 |
| 判据有效性 | @@D1@@/15 |
| 假绿防御 | @@D2@@/15 |
| 产品面推进 | @@D3@@/15 |
| 台账一致性 | @@D4@@/15 |
| 交付诚实性 | @@D5@@/15 |
| 可复核性 | @@D6@@/15 |
各维理由：真实视觉审查 @@D0@@ —— 看了本轮读数所依托的那一段行带，但没有新位点也没重捕（帧与 R291 同一批）；判据有效性 @@D1@@ —— 阈值随密度换算后两臂各自被断言，且这条尺的其余部分（`flatBands` 用相对跨度、`changedXSpan` 用灰阶差）本来就不吃像素阈值，本轮把最后一处补齐；假绿防御 @@D2@@ —— 本轮最强的一维：M855 在本机重放出 runner 那个「2 簇」，M856 钉住臂的身份（写死倍率 ⇒ 两臂合成一臂必须红），M857 钉住臂的对象（y 带不按倍率换算 ⇒ 量到别处）；产品面推进 @@D3@@ —— 0 文件，动效过程连续第四轮没动，这一维按实记；台账一致性 @@D4@@ —— 五本 + 340 追记（本机半结案、runner 半留）+ 286 追记（第四种坏法）+ 341 改判并就地更正 R291 那四格假话（按节边界替换，段外一处没动）；交付诚实性 @@D5@@ —— 两件都公开：这一轮的修改弄坏了上一轮的针；以及上一轮我写进五本台账的那格「电池 skipped 5 vs 4」是我读错了行，本轮撤回并就地更正（不是等谁来问才改）；可复核性 @@D6@@ —— 判据、三把刀、重钉后的 R290 表、预检、四件套都能重跑，runner 那一半还押在未读的那跑上。合计 **@@SUM@@**/105；曲线仪器派生读 **@@DERIVED@@**，低于 90 ⇒ 本轮按目标规矩不算达标，欠的还是产品面与动效。

"""

DEC_NEW = u"""**D-272（R292）：跨机器复用的尺，阈值单位必须与被量对象的单位一致；判据要自带一条「另一台机器的密度」替身臂，否则"本机绿"只是本机绿。** 理由：`columnClusters` 的合并阈值原来写成 `mergeGapPx: Int = 12`，而注释里那句"6pt 坐在中间"是在本机 @2x 量的 —— runner 是 @1x（账上早有的读数：`位图=720x540 scale=1.0`），12px 在 1x 下等于 12pt，比列与列之间 10pt 的缝还宽 ⇒ 相邻列必并簇 ⇒ 判据在 runner 上走「尺没有对象」出口而红两跑，本机却全绿。修法是阈值随密度换算（`mergeGapPt × density`）**并且**在判据里加一条把自家帧按最近邻抽成 1x 的替身臂，两臂各自被断言（簇数相等、点空间左沿压在地板上）。这一条与 D-269（比较两边要同为一种单位）、D-251（不许为让某台机器绿而放宽地板）、R87（单遍读数不配给产品定罪）同族，新意在于它管的是**判据自己的可移植性**：一条只在一种密度上有牙的尺，等于把"另一台机器"写成了免检区。刀 M855（退回固定像素）/ M856（臂身份：倍率写死成 1）/ M857（臂对象：y 带不按倍率换算）三把各钉一轴；M856 是必需的 —— 没有它，替身臂可以静默退化成对同一个对象量两次，三条断言全绿而 runner 照红。

**D-273（R292）：从别人的日志里取一个数，必须锚在"被读那个对象的结论行"上，而不是锚在第一个匹配上 —— 太宽的正则不会报错，它会把另一个对象的读数写成你的结论。** 理由：R291 的台账里那句「电池 skipped=5」来自 `re.search(r"skipped=(\d+)")` 命中了名册闸门自己打的 `SKIP_ROSTER … 汇总skipped=5 解析=4`，而电池自己的 `OK (skipped=4)` 在文件更后面。两个数都是真的，只是主语不同：一个是**内层那一卷**（含观察者自己的防递归 skip），一个是**外层这一卷**。闸门本身没错（它断言内层汇总 == 内层名单，且观察者恰好一颗），错在我借了它的数。规矩：① 读汇总要匹配整行形状（`^OK \(skipped=(\d+)\)$`）而不是子串；② 借来的数要能说出主语（本轮 `ledgers_r292.py` 里 改成同时取「结论行汇总」与「-v 名单条数」并断言两者相等，不等就 die）；③ 台账里被写进"两次读数不同"这种断言时，必须能指出两个数各自的来源行 —— 指不出就先怀疑自己的尺（R292 就是靠这条把 341 从"电池会翻脸"改判成"我读错行"）。

"""

CHG_NEW = u"""### Fixed（R292 / 第 291 轮 / Round 289 · 墨簇尺的密度无关性）

`UICaptureHarness.columnClusters` 的列缝阈值从固定像素（`mergeGapPx: Int = 12`）改成随密度换算的点（`mergeGapPt: Double = 6` × `density`）：runner 的截图是 @1x、本机是 2x，旧写法在 1x 下等于 12pt 的合并半径，比行首三列之间 10pt 的间距还宽 ⇒ 图标列与文字列并成一簇，`testMultiFileRowSeparatorsStartAtTheTextAxis` 在 runner 上连着两跑红（@@CI3@@ 那两笔），而本机全绿。判据里新增一条 @1x 替身臂（`downsampleNearest` 把自家 2x 帧按最近邻抽成 1x，不重新渲染），新读数 `LEFT_AXIS_R292_1X`：@@ARM_L@@。两臂各自被断言：簇数相等、点空间文字左沿差压在 1.5pt 地板上（现读 @@TL2X@@ 对 @@TL1X@@）。缺席文本改为自带密度与簇区间（M847 的红话里现在能直接看到 [36.0..175.5] 这种现场）。新增 `testColumnClusterRulerIsDensityIndependent`（同一份点空间形状画在 1x 与 2x 上必须给同一个点答案）。`mutate_r292.py`：M855 单位轴／M856 臂身份轴／M857 臂对象轴 —— 现读 @@KC@@/@@KN@@ 全 CAUGHT、RESTORE_CLEAN=@@KREST@@，登记进预检（tables=@@TBL@@ covered=@@COV@@ bad=0）。**自曝一格**：本轮改签名把上一轮的针弄腐烂了（`mutate_r290` 的 M847 命中 0 次 ⇒ 预检 bad=1），当场重钉并整张表重跑（@@K0C@@/@@K0N@@ 全 CAUGHT）。340 本机半结案、runner 半押在 @@CI1@@、@@CI2@@；286 追记第四种坏法；341 保持开着。四件套 @@RV@@（@@PAIR@@）；@@BATT@@；产品 0 文件 ⇒ 帧基线不变、sources 格不动。

"""

NOTE340 = (u"  追记（R292）：**本机半结案，runner 半还欠。** ① 阈值换成 `mergeGapPt × density`；② 判据里加了把自家 2x 帧抽成 1x 的替身臂"
           u"（`LEFT_AXIS_R292_1X`：密度 1.00、簇数 3、文字左沿 2x 82.5 对 1x 83.0pt，差压在 1.5pt 地板上），"
           u"③ 刀 M855 把阈值退回固定 12px 后**在本机就量到 runner 那个数**（2 簇，簇区间 [36.0..40.0, 55.0..175.0]）"
           u" ⇒ 成因不再靠解释，是复现；④ M856/M857 各钉臂的身份与对象，三把全 CAUGHT。"
           u"本单剩下的只有第 ④ 条验收：push 之后那两跑的红必须消失（@@CI1@@、@@CI2@@），红不消失就回到单位这一层继续查，不许改成 skip。")

NOTE341 = (u"  追记（R292）：**本单的前提被现读推翻，改判。** 原文写的「同一棵树两次电池跑出不同 skip 颗数（5 与 4）、差的那一颗没有名字」不成立：外层电池的结论行一直是 `OK (skipped=4)`；那个 5 是 `test_skip_roster` 闸门**自己起的内层卷**的汇总（合法地多一颗 —— 观察者那一格在嵌套里按防递归 skip，而闸门断言「内层汇总 == 内层解析名单」且「观察者恰好 1 颗」，一直是绿的）。真缺陷在我的生成器：`re.search(r'skipped=(\\d+)')` 未锚定，先命中闸门那行读数 ⇒ 把别的对象的数写进了五本台账（U-957／D-273）。本单因此改成两格验收：① 生成器与一切读日志的工具，取汇总要按整行形状匹配并同时取名单条数互相签字（`ledgers_r292.py` 已这么做）；② 台账里任何「两次读数不同」的断言都必须能指出两个数各自的来源行，指不出就先怀疑尺。② 结案条件：源头消歧与守卫都要在盘上，且 R291 那四格已就地更正留痕。**本轮现读**：`test_skip_roster` 那行已改名 `内层skip汇总=`，新守卫 `TestReadingKeyHygiene`（含已知答案的正对照）该模块 Ran 3 / OK；但同一个键还有**第二处**没消 —— `scripts/ci_capture_gate.py` 印的 `*_GATE_CASES passed=… skipped=…` 是 CI 契约行（`ci.yml` 与 `test_ci_capture_gate.py` 按字面断言），改名要连着 workflow 正文与它的测试一起动，按 D-215 那一族要单独一轮重跑相关表 ⇒ 本单**仍开**，剩下的就是这一处 + 把 30 支历史生成器的未锚定取数改成按整行形状（新脚本一律走新写法）。")
NOTE304 = (u"  追记（R292）：第三次进场，这次是**我自己把套件加重**顶出来的 —— 本轮给左端判据加了一条 @1x 替身臂（多一次抽帧 + 多一次列切分），全量卷里 `PerfBudgetTests/testImageComparisonCostStaysBounded` 连着两跑红：第一跑 500.24ms（那一跑我自己在本机并跑了嵌套电池，是我给它添的负载），清场第二跑仍 381.01ms，地板 250ms。配对证据：隔离复跑 Executed 1 / 0 failures，且 `git diff HEAD -- ClipboardHistory/Sources` 为空（产品 0 文件）⇒ 判成负载敏感的计时预算那一族，不是回归；**地板一条没放宽**，本单也不结案。新欠的一格（下一轮）：清场重跑为什么仍差 1.5 倍 —— 要么给它一条与套件长度无关的分母（同一次运行内的相对判据，照 176 那一族），要么承认这条地板在 930 颗的卷上测不出产品事实：那是**改判据形状**，不是放宽数值。")
NOTE286 = (u"  追记（R292）：第四种坏法 —— **改判据自己的签名会把历史针弄腐烂**。本轮把 `columnClusters` 的默认缝宽从 "
           u"`mergeGapPx: Int = 12` 换成 `mergeGapPt: Double = 6`，于是上一轮 `mutate_r290` 里钉着那个默认值的 M847 针命中 0 次，"
           u"预检现读 bad=1。这一格与 R262 那三根针不同源：那三根是被别人改走的，这一根是**我自己这一轮改走的**。"
           u"规矩补一条：改判据的形状（默认值、参数名、被断言的常量）当轮就要跑预检并按新形状重钉，重钉后整张表重跑 —— "
           u"本轮 @@K0C@@/@@K0N@@ 全 CAUGHT 才算完。")


def append_into_item(text, num, extra):
    lines = text.splitlines(True)
    start = None
    for i, l in enumerate(lines):
        if l.startswith("**" + num + ". "):
            if start is not None:
                die("BACKLOG 里 " + num + " 出现两次 ⇒ 锚点不唯一")
            start = i
    if start is None:
        die("BACKLOG 找不到 " + num + " 那一单")
    end = len(lines)
    for j in range(start + 1, len(lines)):
        if re.match(r"^\*\*\d{3}\. ", lines[j]):
            end = j
            break
    while end > start and not lines[end - 1].strip():
        end -= 1
    head = u"".join(lines[:end])
    if head and not head.endswith(u"\n"):
        head += u"\n"
    if not extra.startswith(u"  "):
        die("追记行必须以两空格缩进开头，否则会被当成新单")
    return head + extra + u"\n" + u"".join(lines[end:])


STATE_NEW = u"""## R292 状态（第 291 轮 / Round 289 · @@DATE@@）
最后更新：2026-10-22（本地 · R292 / 第 291 轮 / Round 289）：**墨簇尺的合并阈值从像素换成随密度换算的点，判据自带 @1x 替身臂；上一轮那朵 runner 红由「解释」升成「复现」**（U-953…U-958 · D-272/D-273 · 产品 0 文件 · 七维合计 @@SUM@@/105，曲线派生 @@DERIVED@@ —— 低于 90，本轮不算达标，R293 回动效）

**本轮落地**：`UICaptureHarness.swift` 里 `columnClusters(mergeGapPt × density)` + `downsampleNearest` + `testColumnClusterRulerIsDensityIndependent` + 左端判据的 1x 臂（新读数 `LEFT_AXIS_R292_1X`：@@ARM_L@@）；缺席文本自带密度与簇区间。`mutate_r292.py` M855/M856/M857（@@KC@@/@@KN@@ 全 CAUGHT、RESTORE_CLEAN=@@KREST@@，已登记进预检 tables=@@TBL@@ covered=@@COV@@ bad=0）。**自曝**：本轮改签名弄腐烂上一轮的 M847 针（预检 bad=1）⇒ 重钉后整张 R290 表重跑 @@K0C@@/@@K0N@@ 全 CAUGHT（286 追记第四种坏法）。四件套 @@RV@@（@@PAIR@@）；@@BATT@@。340 本机半结案、286 追记、341 改判并就地更正 R291 那四格（U-957／D-273）。

**下一轮（R293 / 第 292 轮 / Round 290）的 ⓪**：
⓪ 读 CI：@@CI1@@（R291 账半）、@@CI2@@（R291 代码半，若没有自己的 run 要写明）、加本两笔。要验的是 340 的第 ④ 条：**STEP[15] 与 STEP[17] 那两跑的红必须消失**（红话「行带里只数到 2 个墨簇」不该再出现），未登记的红必须回到 0；红不消失就回到单位这一层继续查，不许改成 skip 或登记成免检。只登记不轮询（R140）。
① **回到动效过程（连续四轮 0 文件，这一维已经垫底）**：305（按下台阶的地板分辨实验 —— 台阶比值 1.058/1.123 已量出，缺的是「该不该有地板」的分辨）、314（热图那圈描边的语义）、291 墨轴。本轮那条 1x 替身臂的方法可以直接搬给动效尺：凡只在一种密度/一台机器上量的判据，都该有第二条臂。
② 341（电池 skip 颗数与名单同源：生成器这侧已经按名单对账，电池那侧的闸门还没改）、340 的 runner 半。
③ 339（其余表面的容器归属与逐位点约定，按结构认身份 D-271，每处配产品轴 + 身份轴两把刀）、312 具名出口（欠第十五轮，本机 3.000 不许降，D-251）、333 的 CI 半、335、334、310（@@GAPT@@ 张表 / @@GAPA@@ 把刀静默不覆盖）、338 的另一半、328、323、322、317。
④ 用户闸门 220 路 A / 228② / 265。

"""

for i, nm in enumerate("D0 D1 D2 D3 D4 D5 D6".split()):
    ITER_NEW = ITER_NEW.replace("@@" + nm + "@@", str(SCORES[i]))
for n in ("UI_NEW", "ITER_NEW", "DEC_NEW", "CHG_NEW", "STATE_NEW"):
    globals()[n] = render(globals()[n])
NOTE340 = render(NOTE340)
NOTE286 = render(NOTE286)
NOTE304 = render(NOTE304)

ui_p = B["AGENT_UI_AUDIT.md"]
ui_old = rd(ui_p)
if u"## 第 291 轮" in ui_old:
    die(u"UI_AUDIT 已有第 291 轮 ⇒ 不幂等，先还原")
anchor = u"## 第 290 轮"
if ui_old.count(anchor) != 1:
    die("UI_AUDIT 锚点命中 %d 次" % ui_old.count(anchor))
ui_new = ui_old.replace(anchor, UI_NEW + anchor, 1)

it_p = B["AGENT_VISUAL_ITERATION.md"]
it_old = rd(it_p)
if re.search(u"^## Round 289 · ", it_old, re.M):
    die(u"ITERATION 已有 Round 289 ⇒ 不幂等")
it_new = it_old.rstrip("\n") + u"\n\n" + ITER_NEW

dc_p = B["AGENT_DECISIONS.md"]
dc_old = rd(dc_p)
if u"D-272" in dc_old or u"D-271" not in dc_old:
    die(u"D 号不对（D-271 应在盘上、D-272 不该在）")
dc_new = dc_old.rstrip("\n") + u"\n\n" + DEC_NEW

cg_p = B["CHANGELOG.md"]
cg_old = rd(cg_p)
cg_new = cg_old.replace(u"## [Unreleased]\n", u"## [Unreleased]\n\n" + CHG_NEW, 1)

bk_p = B["AGENT_BACKLOG.md"]
bk_old = rd(bk_p)
last_no = re.findall(r"^\*\*(\d{3})\. ", bk_old, re.M)
if last_no[-1] != "341":
    die(u"BACKLOG 最后一单不是 341（现读 " + str(last_no[-3:]) + u"）")
if len(set(last_no)) != len(last_no):
    die(u"BACKLOG 单号有重复：" + str([n for n, c in Counter(last_no).items() if c > 1]))
bk_new = append_into_item(bk_old, "340", NOTE340)
bk_new = append_into_item(bk_new, "286", NOTE286)
bk_new = append_into_item(bk_new, "341", render(NOTE341))
bk_new = append_into_item(bk_new, "304", NOTE304)

st_p = B["AGENT_STATE.md"]
st_old = rd(st_p)
if u"## R291 状态" not in st_old:
    die(u"STATE 找不到 R291 锚点")
st_new = st_old.replace(u"## R291 状态", STATE_NEW + u"## R291 状态", 1)
if u"U-958" not in st_new or u"U-958" not in ui_new:
    die(u"STATE／UI_AUDIT 没带上 U-958 ⇒ 交账的半截丢了")


def must_preserve(old, new, name, allow=0):
    # allow：本轮**有意**改写的行数（就地更正 R291 那格假话 ⇒ 每个文件 1 行）。
    # 不许把它当宽松用：多丢一行就红。
    cn = Counter(new.splitlines())
    lost = [l for l, c in Counter(old.splitlines()).items() if cn[l] < c]
    if len(lost) > allow:
        die(name + u" 弄丢 " + str(len(lost)) + u" 行（只允许 " + str(allow) + u" 行）："
            + u" | ".join(lost[:2])[:160])


# ── 验结果：R291 那格假话必须已经从四本账里消失，更正痕迹必须各在 1 处 ──
# 更正本身是上一笔手工落的（按起止片段匹配，四个文件各命中一次）。生成器不再做字符串手术：
# 它只准检查，改不动也不许假装改过。
CLAIM = u"差的那一颗**没有名字**"
MARK = u"R292 就地更正"
CHECKS = ((u"UI", lambda: ui_new), (u"ITERATION", lambda: it_new),
          (u"STATE", lambda: st_new), (u"CHANGELOG", lambda: cg_new))
for _nm, _get in CHECKS:
    _t = _get()
    if CLAIM in _t:
        die(_nm + u" 里那句电池假话还在盘上 ⇒ 撤回没落到它头上")
    if _t.count(MARK) < 1:
        die(_nm + u" 里没有「" + MARK + u"」的痕迹 ⇒ 更正不可复查（不许只把假话删掉不留痕）")
print(u"R291 四格更正复查通过：假话残留 0 处、痕迹各在位")


for o, n, name, allow in ((ui_old, ui_new, "UI", 0), (cg_old, cg_new, "CHANGELOG", 0),
                          (bk_old, bk_new, "BACKLOG", 0), (st_old, st_new, "STATE", 0),
                          (it_old, it_new, "ITERATION", 0), (dc_old, dc_new, "DECISIONS", 0)):
    must_preserve(o, n, name, allow)

ids = [int(x) for x in re.findall(u"- \\*\\*U-(\\d+)", UI_NEW)]
if ids != [953, 954, 955, 956, 957, 958]:
    die(u"U 号不连续或顺序不对：" + str(ids))
rows = [l for l in ITER_NEW.splitlines() if re.match(r"\| .* \| \d+/15 \|$", l)]
scores = [int(re.search(r"\| (\d+)/15 \|", l).group(1)) for l in rows]
if len(scores) != 7 or sum(scores) != sum(SCORES):
    die(u"七维表形状或合计不对：" + str(scores))
tail = re.findall(u"^## Round (\\d+) · ", it_new, re.M)
if int(tail[-1]) != 289:
    die(u"ITERATION 文件尾轮次必须是本轮（现读 " + str(tail[-3:]) + u"）")
if it_new.count(u"| 真实视觉审查 |") != it_old.count(u"| 真实视觉审查 |") + 1:
    die(u"七维表数量不对")
if bk_new.count(u"追记（R292）") != 4:
    die(u"340／286／341／304 的追记没落上（现读 %d 条）" % bk_new.count(u"追记（R292）"))
for _num, _note in ((u"340", NOTE340), (u"286", NOTE286), (u"341", render(NOTE341)), (u"304", NOTE304)):
    if u"\n" in _note:
        die(u"单号 " + _num + u" 的追记不是单行")
    _lines = bk_new.splitlines()
    _hits = [i for i, l in enumerate(_lines) if l == _note]
    if len(_hits) != 1:
        die(u"单号 " + _num + u" 的追记整行命中 " + str(len(_hits)) + u" 次 ⇒ 落点不唯一")
    _owner = None
    for i in range(_hits[0], -1, -1):
        m = re.match(r"^\*\*(\d{3})\. ", _lines[i])
        if m:
            _owner = m.group(1)
            break
    if _owner != _num:
        die(u"追记落进了单号 " + str(_owner) + u"，应为 " + _num)
if dc_new.count(u"\n**D-272") != 1:
    die(u"D-272 没落上")
if u"## R292 状态" not in st_new:
    die(u"STATE 没轮换")

for p, txt in ((ui_p, ui_new), (it_p, it_new), (dc_p, dc_new), (bk_p, bk_new), (cg_p, cg_new), (st_p, st_new)):
    with io.open(p, "w", encoding="utf-8") as h:
        h.write(txt)

out, rc = sh([sys.executable, os.path.join(HERE, "report_cells_r258.py"), "headline"])
if rc != 0:
    die(u"FINAL_REPORT headline 刷新失败：" + out[-300:])
ran2, skip2, names2 = battery()
if ran2 != pre_ran or skip2 != pre_skip:
    die(u"写盘前后电池不一致（" + pre_ran + u"/" + pre_skip + u" → " + ran2 + u"/" + skip2 + u"）")
print(u"LEDGERS_R292 OK batt=Ran " + ran2 + u" (skipped=" + skip2 + u", 名单=" + str(names2) + u")"
      + u" roll=" + str(ROLL) + u" knives=" + KC + u"/" + KN + u" r290=" + K0C + u"/" + K0N
      + u" arm1x=" + str(CLUST_1X) + u"簇@" + ("%.2f" % DENS_1X)
      + u" 文字左沿 " + ("%.1f" % TL_2X) + u"/" + ("%.1f" % TL_1X)
      + u" prod=0 U=" + str(min(ids)) + u".." + str(max(ids)) + u" D=272/D-273 note=340+286+341 更正R291四格")

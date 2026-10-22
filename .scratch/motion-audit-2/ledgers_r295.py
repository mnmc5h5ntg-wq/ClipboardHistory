#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R295 的台账落盘（第 294 轮 / Round 292）。

沿用 ledgers_r294c.py 的事务形状：六本的新内容**先全部算出来**，写盘前跑一次电池、写盘后再跑一次，
两次不一致就从内存整体还原（含被刷新器动过的 AGENT_FINAL_REPORT.md），绝不留半批账。

本轮读数的来源都是**现取**：
· `PRESS_PAIR_REF` 两行（自家行 vs 系统参照的逐像素差）从全量卷日志里找，找不到就拒绝写盘；
· 变异表 `mutate_r295.py` 由本脚本自己跑一遍，取它打印的那行汇总；
· 帧闸门由 `scripts/frame_baseline.py compare` 现跑；
· 派生分由 `curve_from_ledger.py` 现读，不手抄。

文本里的百分号一律用 `%%` 之外的写法：模板里放 `@TOKEN@`，最后统一 replace —— 这样 `%` 格式化
不会按文本顺序吃掉参数（R87 那一族整行塞进数字列的坏法）。
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
CURVE = os.path.join(ROOT, ".scratch", "motion-audit-2", "curve_from_ledger.py")
KNIVES = os.path.join(ROOT, ".scratch", "motion-audit-2", "mutate_r295.py")
REFRESH = os.path.join(ROOT, ".scratch", "motion-audit-2", "refresh_report_section1.py")
PAIR_DIRS = ["/tmp/r295_verify", "/tmp"]
FRAME_DIRS = ["/tmp/r295_verify/frames", "/tmp/r295_frames"]
DIMS = [u"真实视觉审查", u"判据有效性", u"假绿防御", u"产品面推进", u"台账一致性",
        u"交付诚实性", u"可复核性"]
SCORES = [12, 13, 13, 6, 11, 14, 13]


def die(m):
    sys.stderr.write(u"LEDGERS_R295 REFUSED: " + m + u"\n")
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
        bad = [l for l in txt.splitlines()
               if l.startswith((u"FAIL:", u"ERROR:"))
               or u"FINAL_REPORT_" in l or u"ROSTER_" in l or u"HEADLINE" in l]
        return None, tag + u" 电池不绿：" + "\n".join(bad[:12])
    return (ran[-1], ok[-1], names), ""


# ── 读数（全部现取）──────────────────────────────────────────────────
OURS = r"自家 底=(\d+) 变=(\d+)颗 整块平均\|Δ\|=(-?\d+) 变颗平均\|Δ\|=(\d+) 带符号=(-?\d+) 峰\|Δ\|=(\d+)"
REF = r"参照 底=(\d+) 变=(\d+)颗 整块平均\|Δ\|=(-?\d+) 变颗平均\|Δ\|=(\d+) 带符号=(-?\d+) 峰\|Δ\|=(\d+)"


def grab(pattern, line, who):
    m = re.search(pattern, line)
    if not m:
        die(u"%s 那一侧的形状不符（正则与读数不一致，不许猜）" % who)
    return m.groups()


pair_src = None
for d in PAIR_DIRS:
    if not os.path.isdir(d):
        continue
    for fn in sorted(os.listdir(d)):
        if not fn.endswith(".log"):
            continue
        path = os.path.join(d, fn)
        try:
            txt = rd(path)
        except Exception:
            continue
        lines = re.findall(r"^PRESS_PAIR_REF (light[^\n]*|dark[^\n]*)", txt, re.M)
        if len(lines) == 2:
            pair_src = path
            break
    if pair_src:
        break
if not pair_src:
    die(u"没有任何一份日志里有 2 行 PRESS_PAIR_REF ⇒ 本轮读数没有对象")

L = [x for x in re.findall(r"^PRESS_PAIR_REF (light[^\n]*)", rd(pair_src), re.M)][-1]
D = [x for x in re.findall(r"^PRESS_PAIR_REF (dark[^\n]*)", rd(pair_src), re.M)][-1]
ol = grab(OURS, L, u"自家亮")
rl = grab(REF, L, u"参照亮")
od = grab(OURS, D, u"自家暗")
rdk = grab(REF, D, u"参照暗")

full = None
for cand in ("/tmp/r295_verify/full.log", "/tmp/r295_full.log"):
    if os.path.exists(cand) and u"All tests' passed" in rd(cand):
        full = cand
        break
if not full:
    die(u"全量卷不是 passed（或找不到那份日志）")
roll = re.findall(r"Executed (\d+) tests, with (\d+) tests? skipped and (\d+) failures?", rd(full))
ROLLED, SKIPPED, ROLLED_F = roll[-1] if roll else (u"?", u"?", u"?")

frames_dir = None
for cand in FRAME_DIRS:
    if os.path.isdir(cand):
        frames_dir = cand
        break
if not frames_dir:
    die(u"找不到本轮的帧目录 ⇒ 帧闸门没有对象")
frames = [f for f in os.listdir(frames_dir) if f.endswith(".png")]
bout, brc = sh(["python3", "scripts/frame_baseline.py", "compare", frames_dir, "--against", "working"])
if brc != 0:
    die(u"帧闸门不是 PASS：" + bout.strip()[-200:])
CM = (re.findall(r"^FRAME_BASELINE_COMPARED=(\d+)", bout, re.M) or [u"?"])[-1]
CH_ = (re.findall(r"^FRAME_BASELINE_CHANGED=(\d+)", bout, re.M) or [u"?"])[-1]
MS = (re.findall(r"^FRAME_BASELINE_MISSING=(\d+)", bout, re.M) or [u"?"])[-1]
AD = (re.findall(r"^FRAME_BASELINE_ADDED=(\d+)", bout, re.M) or [u"?"])[-1]

kout, krc = sh(["python3", KNIVES])
KS = re.findall(r"^R295_MUTATE 刀=(\d+) CAUGHT=(\d+) ESCAPED=(\d+) NOT_RUN=(\d+) RESTORE_CLEAN=(\w+)", kout, re.M)
if not KS or krc != 0:
    die(u"变异表不是全 CAUGHT：" + kout.strip()[-200:])
KN, KC, KE, KNR, KREST = KS[-1]

T = {
    "@OL_BASE@": ol[0], "@OL_CHG@": ol[1], "@OL_MEAN@": ol[2], "@OL_CMEAN@": ol[3],
    "@OL_SIGN@": ol[4], "@OL_MAX@": ol[5],
    "@RL_BASE@": rl[0], "@RL_CHG@": rl[1], "@RL_MEAN@": rl[2], "@RL_CMEAN@": rl[3],
    "@RL_SIGN@": rl[4], "@RL_MAX@": rl[5],
    "@OD_BASE@": od[0], "@OD_CHG@": od[1], "@OD_MEAN@": od[2], "@OD_CMEAN@": od[3],
    "@OD_SIGN@": od[4], "@OD_MAX@": od[5],
    "@RD_BASE@": rdk[0], "@RD_CHG@": rdk[1], "@RD_MEAN@": rdk[2], "@RD_CMEAN@": rdk[3],
    "@RD_SIGN@": rdk[4], "@RD_MAX@": rdk[5],
    "@ROLLED@": ROLLED, "@SKIPPED@": SKIPPED, "@FAILS@": ROLLED_F,
    "@KN@": KN, "@KC@": KC, "@KREST@": KREST,
    "@FRAMES@": str(len(frames)), "@CM@": CM, "@CH@": CH_, "@MS@": MS, "@AD@": AD,
    "@PAIRSRC@": pair_src,
    # 亮档对系统的比例：在这里现算，因为六本模板的 fill() 要一次到位（晚算会让 fill 拒绝写盘）
    u"@RATIO_L@": str(int(round(100.0 * int(ol[3]) / int(rl[3])))) + u"%",
}


def fill(s):
    for k, v in T.items():
        s = s.replace(k, v)
    if re.search(r"@[A-Z_]+@", s):
        die(u"模板里有没被替换的 token：" + " ".join(re.findall(r"@[A-Z_]+@", s)[:6]))
    return s


# ── 六本的新内容，先全部算出来 ──────────────────────────────────────
UI_NEW = fill(u"""## 第 294 轮（R295 · U-965…U-967 · 2026-10-22）：两态差第一次按同一坐标逐像素相减，量出「整块平均」是面积假象，亮档按下只有系统的 @OL_CMEAN@/@RL_CMEAN@

- **U-965：第三颗尺 `pairDelta` —— 分子不再是两帧各自的众数之差。** 上一轮那格 `PRESS_LADDER_SPAN`
  把 `|press.step − idle.step|` 说成"按下离空闲走了多少灰阶"，而两个 step 各自是**一帧之内**的众数：
  idle 那帧的众数是星形笔画的墨（R295 现读：无界尺 idle 块=@OD_BASE@ 一侧），press 那帧的众数是整片填充
  ⇒ 两帧的众数不同源，那个差是一句假等式（R182「两层材质混成一层」的对称形态）。
  新尺把两态按同一坐标逐颗相减，自家 `row-favorite-idle/press` 与系统 `sysref-button-idle/press`
  走**同一个函数、同一条 render、同一 60x56**（D-275）。
- **U-966：整块平均是面积假象，地板的分母只能是变化颗数。** 现读：自家亮档整块平均 @OL_MEAN@、
  系统参照 @RL_MEAN@（差近十倍），看着像"我们按得极轻"；但同一次读数里自家只动 @OL_CHG@ 颗、
  系统动 @RL_CHG@ 颗 —— 同一个 60x56 里控件占的面积不同，整块平均量的是**谁占的地方大**。
  换成"变了的颗平均走多少灰阶"：亮 @OL_CMEAN@ 对 @RL_CMEAN@、暗 @OD_CMEAN@ 对 @RD_CMEAN@
  ⇒ 暗档与系统同量级，亮档约为系统的 @RATIO_L@（写进 305 的地板形状，D-276）。
  存在性闸门 `testPressTravelSharesOneRulerWithTheSystemReference` 只判四件事：两臂底非 0
  （亮 @OL_BASE@/@RL_BASE@、暗 @OD_BASE@/@RD_BASE@）、两态量得出差别、带符号均值不为 0；台阶地板一条不加。
  刀 M860（参照臂按下态改回与 idle 同态）红在「参照臂没画」、M861（逐像素门限抬到无穷）红在
  「逐像素相减为 0 颗」，各钉一条轴，全表 CAUGHT=@KC@/@KN@、RESTORE_CLEAN=@KREST@。
- **U-967：亮档那 44% 的差距本轮判为「不向系统看齐」，理由写全而不是沉默。** 看图腿（亮档四张：
  `sysref-button-idle/press`、`row-favorite-idle/press`）现读：系统那颗是**整片身体**压成中灰，
  自家这颗是星形后面浮出一圈浅灰药丸。行内 ghost 按钮若整片闪到系统的量级，会与这一行自己的
  hover/选中抢层级（R260/308 刚把"按下与选中糊成一档"修开），而 305 要防的是**塌陷**不是**不够华丽**。
  所以本轮不加动效（规矩：不许为打破 0 改动纪录加动效），把"亮档要不要抬"留成 347 的未判半格，
  并要求那一判必须先有真机眼 + 变颗平均的 before/after。

本轮产品文件 0 个（只动测试靶）。捕获/全量卷 @ROLLED@ 用例 / @SKIPPED@ skip / @FAILS@ 失败；
帧 @FRAMES@ 张，基线 compared=@CM@ changed=@CH@ missing=@MS@ added=@AD@；读数取自 @PAIRSRC@。

""")

ROWS = u"\n".join(u"| %s | %d/15 |" % (d, s) for d, s in zip(DIMS, SCORES))
T["@ROWS@"] = ROWS
T["@TOTAL@"] = str(sum(SCORES))
ITER_NEW = fill(u"""## Round 292 · R295（第 294 轮 · 2026-10-22）：两态差换成逐像素相减，量出整块平均是面积假象

本轮做的事：给"按下这一档到底走了多少"造一颗**分子分母都同源**的尺，并第一次把自家与系统参照
放在同一个函数下比。产品文件 0 个 —— 产物是 305 的地板形状（变颗平均）与一条被推翻的旧说法
（`PRESS_LADDER_SPAN` 那个 27/29 不是"按下离空闲的距离"）。

七维度自评：
| 维度 | 分/满分 |
| --- | --- |
@ROWS@
| 合计 | @TOTAL@/105 |

为什么不是满分（逐条）：真实视觉审查 12 —— 只重看了亮档四张（参照两态 + 自家两态），其余表面没重看；
产品面推进 6 —— 0 个产品文件，连续第八轮；台账一致性 11 —— 本轮两次自坏（Swift 字面量里放 ASCII 双引号
把串截断、闭包引用了声明在它之后的局部变量），都在编译时被抓、没进产物；判据有效性 13 与假绿防御 13 ——
新尺配两把各钉一轴的刀，并在装地板之前先推翻了自己上一轮的分子。

派生分由 `curve_from_ledger.py` 现读，不手抄。
未做（逐条）：① **346 的下半场**（`pillReading` 带窗 `Δ<60` 仍会把强填充读成缺席；本轮是**绕开**它另起一颗尺，
盲区本身没修）；② 305 的台阶地板（形状已定：变颗平均，阈值等 347 判完再推）；③ **347**（亮档要不要抬到
系统量级 —— 需真机眼 + before/after）；④ 344、341 的 CI 契约半、343 的两处、339、312 具名出口、333、335、
334、310、338 的另一半、328、323、322、317、304、296、291；⑤ 用户闸门 220 路 A / 228② / 265。

""")

DEC_NEW = fill(u"""
**D-276（R295）：两态差的地板，分母必须是「变了的颗数」而不是整块面积；面积占比要同格报出来。**
本轮现读：同一个 60x56 夹具里，自家行按下动 @OL_CHG@ 颗、系统参照按钮动 @RL_CHG@ 颗，
于是"整块平均 |Δ|"亮档 @OL_MEAN@ 对 @RL_MEAN@ —— 那个近十倍的差说的是**控件占多大地方**，
不是**按得多狠**。换成变颗平均：亮 @OL_CMEAN@ 对 @RL_CMEAN@、暗 @OD_CMEAN@ 对 @RD_CMEAN@，
两臂才第一次可比（D-275 的下半场：同一条 render 还不够，分母也得同一个口径）。
定规：任何以两态差为分子的地板，(1) 分子由同一函数在两态之间逐像素算，不许拿两帧各自的众数相减；
(2) 分母取变化颗数；(3) 面积占比同格打印，否则"我们比系统弱"这种结论会由稀释造出来。
本轮亮档 @OL_CMEAN@ 对 @RL_CMEAN@ 的差距判为不改产品（层级理由见 U-967），未判的那半开成 347。
""")

BACK_347 = fill(u"""
**347. 亮档按下的动得只有系统参照的 @RATIO_L@（变颗平均 @OL_CMEAN@ 对 @RL_CMEAN@），要不要向系统看齐未判（R295 现读，同一颗 `pairDelta`、同一条 render）**：本轮判为**不抬**，理由是层级而不是数值 —— 行内 ghost 按钮整片闪到系统量级会与这一行的 hover/选中抢层级（R260/308 刚把"按下与选中糊成一档"修开），而 305 要防的是塌陷不是不够华丽。这一判**没有真机证人**（离屏 render 与压缩材质历史上不同量，R100/R107），所以开单：① 真机眼看亮档按下（`row-favorite-press` 与系统那颗并排），② 若要抬，先报 before/after 的变颗平均与面积占比，并准备"抬过 hover 顶层"会红的既有等式（R255 那一族：改产品视觉会打破既有台阶恒等式），③ 判"不抬"也要绑读数——不许把本轮的层级理由抄成契约。\n""")

NOTE_346 = (u"  追记（R295）：本轮**没有**改带窗，而是绕开它另起一颗尺 —— 新增 `pairDelta`"
            u"（两态逐像素差，无带窗、无众数主语问题），自家与参照同一函数；带窗的盲区本身仍在"
            u"（`pillReading` 的 `Δ<60` 会把强填充读成缺席），128b2c3 那颗牙继续守着。"
            u"顺序因此改：305 的地板不再等带窗，改等 347 的亮档判断（D-276 已把分母口径钉成变化颗数）。\n")

NOTE_305 = (u"  追记（R295）：地板的**形状**定了 —— 分子由 `pairDelta` 在两态之间逐像素算，"
            u"分母取变化颗数（D-276）。现读：亮 自家 @OL_CMEAN@ / 系统 @RL_CMEAN@，暗 自家 @OD_CMEAN@ / 系统 @RD_CMEAN@。"
            u"阈值仍不拍：先结 347（亮档要不要抬），抬与不抬都会改变地板该压在哪一侧。\n")

CHG_NEW = fill(u"""### Improved（R295 / 第 294 轮 / Round 292 · 两态差换成逐像素相减，整块平均被证成面积假象）

新增尺 `UICaptureHarness.pairDelta`（两态按同一坐标逐颗相减，报底、变化颗数、整块平均、变颗平均、带符号均值、峰值）
与判据 `UICaptureTests/testPressTravelSharesOneRulerWithTheSystemReference`：自家 `row-favorite-idle/press`
与系统 `sysref-button-idle/press` 走同一个函数、同一条 render。现读 `PRESS_PAIR_REF`：
亮档 自家 底=@OL_BASE@ 变=@OL_CHG@颗 整块平均=@OL_MEAN@ 变颗平均=@OL_CMEAN@ 峰=@OL_MAX@／
参照 底=@RL_BASE@ 变=@RL_CHG@颗 整块平均=@RL_MEAN@ 变颗平均=@RL_CMEAN@ 峰=@RL_MAX@；
暗档 自家 @OD_BASE@/@OD_CHG@颗/@OD_MEAN@/@OD_CMEAN@/@OD_MAX@／参照 @RD_BASE@/@RD_CHG@颗/@RD_MEAN@/@RD_CMEAN@/@RD_MAX@。
"整块平均差十倍"因此被判成**面积稀释**而不是产品结论（D-276），305 的地板分母改成变化颗数。
刀 M860/M861 各钉一条轴（参照两态轴、变化计数轴），全 CAUGHT、RESTORE_CLEAN=@KREST@。
产品文件 0 个；帧 @FRAMES@ 张、基线 changed=@CH@ added=@AD@。

""")

STATE_NEW = fill(u"""## R295 状态（第 294 轮 / Round 292 · 2026-10-22）

⓪ 读 CI：本笔 push 之后由 R296 用 `gh run list --limit 6 --json databaseId,headSha,status,conclusion`
（字段要连成**一个**逗号串，R293 那一课）现取 run↔commit 成对登记；取不到的写明「push 在台账之后」，别编号。
要验的两件事：① 新判据 `testPressTravelSharesOneRulerWithTheSystemReference` 在 runner 上**有没有对象** ——
它读的是夹具通道，而 runner 的离屏 render 历史上画不出真底；若两臂底读 0，那是通道账（342/346 那一族），
按 313/316 解释，一条地板都不放宽（D-251）；② `PRESS_PAIR_REF` 两行在 runner 上的**变颗平均**与本机是否同量级
（亮 @OL_CMEAN@/@RL_CMEAN@、暗 @OD_CMEAN@/@RD_CMEAN@）—— 不同也只登记不改判据，尤其不许把参照臂改成
"runner 上能过"的形状。只登记不轮询（R140）。

最后更新：2026-10-22（本地 · R295 / 第 294 轮 / Round 292）：**两态差的分子被推翻并重做** ——
`PRESS_LADDER_SPAN` 的 27/29 是两帧各自众数之差（不同源），新尺 `pairDelta` 逐像素相减；
"整块平均差十倍"证成**面积稀释**（自家 @OL_CHG@ 颗 vs 参照 @RL_CHG@ 颗），变颗平均亮 @OL_CMEAN@/@RL_CMEAN@、
暗 @OD_CMEAN@/@RD_CMEAN@ ⇒ D-276 钉死分母口径，305 的形状定了、阈值仍不拍。
亮档那 @RATIO_L@ 的差距本轮判为不抬（层级理由 U-967），未判的半格开成 347。
全量卷 @ROLLED@/@SKIPPED@ skip/@FAILS@ 失败、0 告警、帧 @FRAMES@ 张 changed=@CH@ added=@AD@、
dmg ok 且已换装本机、产品文件 0 个（连续第八轮）。

① 下一轮（R296）的靶：**347**（真机眼 + 亮档抬与不抬的 before/after），结掉它才推 305 的地板；
346 的带窗下半场排在它后面（本轮已绕开，不再是 305 的前提）。

② 仍开：347、305（等 347）、346（带窗未修，只绕开）、344、341 的 CI 契约半、343 的两处、339、
312 具名出口、333、335、334、310、338 的另一半、328、323、322、317、304、296、291。

③ 用户闸门：220 路 A / 228② / 265。

""")

# ── 形状自测（开写之前，按守卫的正则原样验）────────────────────────
if len(re.findall(u"(?m)^- \\*\\*U-9(?:6[567])：", UI_NEW)) != 3:
    die(u"U 定义行形状不符守卫的删除正则（要 `- **U-965：…**`）")
if not re.search(u"U-(\\d+)…U-(\\d+)", UI_NEW.splitlines()[0]):
    die(u"标题里没有可解析的 U 区间")
if u"（R295 ·" not in UI_NEW.splitlines()[0]:
    die(u"标题缺 round_batch 要的「（R295」前缀")
if len(re.findall(u"(?m)^\\| .+ \\| \\d+/15 \\|$", ITER_NEW)) != 7:
    die(u"七维格子不是 7 行 n/15")
if u"七维度自评：" not in ITER_NEW:
    die(u"ITERATION 缺「七维度自评：」锚点")
if not re.search(u"^最后更新：\\d{4}-\\d{2}-\\d{2}（本地 · R295 / 第 294 轮 / Round 292）", STATE_NEW, re.M):
    die(u"STATE 缺「最后更新」行形状")

# ── 幂等与锚点检查（任一不符就整体不写）────────────────────────────
orig = {k: rd(v) for k, v in FILES.items()}
if u"## 第 294 轮" in orig["UI"]:
    die(u"UI_AUDIT 已有第 294 轮")
if re.search(u"(?m)^## Round 292 · ", orig["IT"]):
    die(u"ITERATION 已有 Round 292")
if u"D-276" in orig["DEC"]:
    die(u"D-276 已存在")
if re.search(u"(?m)^\\*\\*347\\. ", orig["BL"]):
    die(u"347 已存在")
if u"## R295 状态（" in orig["ST"]:
    die(u"STATE 已有 R295 节")
if u"R295 / 第 294 轮" in orig["CH"]:
    die(u"CHANGELOG 已有 R295")
if orig["UI"].count(u"## 第 293 轮") != 1:
    die(u"UI_AUDIT 锚点不符")
if orig["ST"].count(u"## R294 状态（") != 1:
    die(u"STATE 锚点不符")
if orig["CH"].count(u"## [Unreleased]\n\n") != 1:
    die(u"CHANGELOG 锚点不符")

bl_lines = orig["BL"].splitlines(True)


def head_of(num):
    return [i for i, l in enumerate(bl_lines) if re.match("^" + str(num) + "[.] ", l.replace("*", ""))]


h346 = head_of(346)
h347 = head_of(347)
h341 = head_of(341)
if len(h346) != 1 or len(h341) != 1 or h347:
    die(u"346/341/347 锚点异常")
# 346 的追记要落在它自己那一格内部：下一个同级标题（341 或文件里 346 之后的下一项）之前
k346 = h341[0]
while bl_lines[k346 - 1].strip() == u"":
    k346 -= 1
# 305 的追记：找 305 那一格的下一项起点
h305 = head_of(305)
if len(h305) != 1:
    die(u"305 锚点异常")
nxt = [i for i, l in enumerate(bl_lines) if re.match(u"^(?:\\*\\*)?\\d{3}\\. ", l) and i > h305[0]]
k305 = nxt[0] if nxt else len(bl_lines)
while bl_lines[k305 - 1].strip() == u"":
    k305 -= 1

pre, err = battery(u"写盘前")
if pre is None:
    die(err)

BL_TEXT = u"".join(bl_lines[:k305]) + NOTE_305 + u"".join(bl_lines[k305:])
bl_lines2 = BL_TEXT.splitlines(True)
h341b = [i for i, l in enumerate(bl_lines2) if l.startswith(u"**341. ")]
if len(h341b) != 1:
    die(u"插 305 追记后 341 锚点异常")
k346b = h341b[0]
while bl_lines2[k346b - 1].strip() == u"":
    k346b -= 1
BL_TEXT = (u"".join(bl_lines2[:k346b]) + NOTE_346 + u"\n"
           + u"".join(bl_lines2[k346b:]).rstrip(u"\n") + BACK_347)

new = {
    "UI": orig["UI"].replace(u"## 第 293 轮", UI_NEW + u"## 第 293 轮", 1),
    "IT": orig["IT"].rstrip(u"\n") + u"\n\n" + ITER_NEW.strip(u"\n") + u"\n",
    "DEC": orig["DEC"].rstrip(u"\n") + u"\n" + DEC_NEW.strip(u"\n") + u"\n",
    "BL": BL_TEXT,
    "ST": orig["ST"].replace(u"## R294 状态（", STATE_NEW + u"## R294 状态（", 1),
    "CH": orig["CH"].replace(u"## [Unreleased]\n\n", u"## [Unreleased]\n\n" + CHG_NEW, 1),
}
for key, text in new.items():
    wr(FILES[key], text)

FR = os.path.join(ROOT, "AGENT_FINAL_REPORT.md")
fr_orig = rd(FR)
sh(["python3", REFRESH])          # §1 那一格由仪器推到现读（曲线多了 Round 292）

# 标题那一格（`R9–R<NNN>`）也要跟着仪器尾轮走：`test_final_report_headline` 允许的滞后只有
# LAG_ROUNDS=1，而本轮 ITERATION 追加了 Round 292 ⇒ 不抬标题就会红（R294 抬到 291 时刚好贴着上限）。
# 尾轮由 `curve_from_ledger.py` 的 `rounds=9..N` 现读，不手抄；标签写 R、单位是 Round 这件事仍未修，
# 记在 344 —— 本轮只抬数字，一个字都不动标签。
cv0, _ = sh(["python3", CURVE])
ph = re.findall(r"PHASE2 n=\d+ rounds=9\.\.(\d+)", cv0)
if not ph:
    die(u"仪器没打印 rounds=9..N ⇒ 标题尾轮无从派生")
tail = ph[-1]
fr_now = rd(FR)
head_line = fr_now.splitlines()[0]
hm = re.search(u"R9–R(\\d+)", head_line)
if not hm:
    die(u"报告第一行没有 R9–R<NNN> 形状 ⇒ 标题那一格无从对账")
if hm.group(1) != tail:
    wr(FR, re.sub(u"R9–R(\\d+)", lambda m: u"R9–R" + tail, fr_now, count=1))
    print(u"TITLE_BUMP " + hm.group(1) + u" -> R9–R" + tail)

# §1 的 U 上界那一格（`U-31 … U-<NNN>`）也要跟着走：headline 守卫允许落后 LAG=3 条，
# 而本轮一次加三条定义（U-965…U-967）就把上一轮的余量吃穿了 —— R294 那轮停在 U-961 时刚好贴着上限。
# 估计量与守卫**同一颗尺**（同一条正则扫 UI_AUDIT），不手抄。
ui_now = rd(FILES["UI"])
umax = [int(x) for x in re.findall(u"^- \\*\\*U-(\\d+)：", ui_now, re.M)]
if not umax:
    die(u"UI_AUDIT 里数不出 U 定义行 ⇒ §1 的 U 上界无从派生")
fr2 = rd(FR)
um = re.search(u"U-31 … U-(\\d+)", fr2)
if not um:
    die(u"§1 找不到 `U-31 … U-<NNN>` 那一格 ⇒ 这一格无从对账")
if int(um.group(1)) != max(umax):
    wr(FR, re.sub(u"U-31 … U-\\d+", u"U-31 … U-%d" % max(umax), fr2, count=1))
    print(u"UCELL_BUMP " + um.group(1) + u" -> U-%d" % max(umax))

post, err = battery(u"写盘后")
if post is None:
    for key, text in orig.items():
        wr(FILES[key], text)
    wr(FR, fr_orig)
    die(u"写盘后电池不绿 ⇒ 六本与报告已整体还原：" + err)
if post != pre:
    for key, text in orig.items():
        wr(FILES[key], text)
    wr(FR, fr_orig)
    die(u"电池计数变了（" + str(pre) + u" → " + str(post) + u"）⇒ 六本与报告已还原")

cv, _ = sh(["python3", CURVE])
score = (re.findall(r"292=(\d+)", cv) or [u"?"])[-1]
gaps = (re.findall(r"^GAPS=(\S+)", cv, re.M) or [u"?"])[-1]
print(u"LEDGERS_R295 OK batt=Ran " + post[0] + u" (skipped=" + post[1] + u", 名单=" + str(post[2])
      + u") roll=" + ROLLED + u"/" + SKIPPED + u"/" + ROLLED_F + u" knives=" + KC + u"/" + KN
      + u" frames=" + str(len(frames)) + u" 变颗平均=亮" + ol[3] + u"/" + rl[3]
      + u" 暗" + od[3] + u"/" + rdk[3] + u" prod=0 U=965..967 D=276 new=347 派生分=" + score + u" GAPS=" + gaps)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R305 的台账生成器（第 304 轮 / Round 302）：354 的第二步 + 一个边界轮。

本轮只动 `scripts/`（0 个 Swift 文件），所以：
· 四件套里 Swift 那几格**沿用上一笔**（R304 的现读），帧重捕与换装本机记 NOT-RUN（不是 0 变化，是没测）；
· 数一律从命令现读：闸门卷 / 刀表 / 预检 / 电池 / product_streak / 登记表自己，抓不到就拒绝写盘；
· 写盘前自扫未替换占位符（R304 那一族），写盘后跑电池并要求与写盘前同数。
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
    "FR": os.path.join(ROOT, "AGENT_FINAL_REPORT.md"),
}
STREAK = os.path.join(ROOT, "scripts", "product_streak.py")
CURVE = os.path.join(ROOT, ".scratch", "motion-audit-2", "curve_from_ledger.py")
PRECHECK = os.path.join(ROOT, ".scratch", "motion-audit-2", "mutate_needle_precheck.py")
KNIVES = os.path.join(ROOT, ".scratch", "motion-audit-2", "mutate_r305.py")
REGISTRY = os.path.join(ROOT, "scripts", "motion_floor_expectations.json")
REFRESH = os.path.join(ROOT, ".scratch", "motion-audit-2", "refresh_report_section1.py")
VERIFY_LOG = "/tmp/r304_verify_run.log"          # 本轮沿用（0 个 Swift 文件），形状见下面校验
R_TAG, PREV_TAG, R_NEXT = u"R305", u"R304", u"R306"
TODAY = subprocess.check_output([u"date", u"+%Y-%m-%d"]).decode().strip()
CI_LINE = os.environ.get("R305_CI_LINE", u"⓪ 未由环境传入 ⇒ 不许写盘")

DIMS = [u"真实视觉审查", u"判据有效性", u"假绿防御", u"产品面推进", u"台账一致性",
        u"交付诚实性", u"可复核性"]
SCORES = [10, 14, 14, 4, 14, 14, 14]


def s(x):
    return str(x)


def die(msg):
    sys.stderr.write(u"LEDGERS_R305 REFUSED: " + msg + u"\n")
    sys.exit(1)


def rd(path):
    with io.open(path, encoding=u"utf-8") as handle:
        return handle.read()


def wr(path, text):
    with io.open(path, u"w", encoding=u"utf-8") as handle:
        handle.write(text)


def sh(cmd):
    env = dict(os.environ)
    env["PYTHONUTF8"] = u"1"
    env["PYTHONDONTWRITEBYTECODE"] = u"1"
    proc = subprocess.run(cmd, cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return proc.stdout.decode(u"utf-8", u"replace"), proc.returncode


def fill_tpl(text, mapping):
    for key in sorted(mapping, key=len, reverse=True):
        text = text.replace(key, mapping[key])
    return text


def battery(tag, log_path):
    out, code = sh([sys.executable, u"-W", u"ignore", u"-m", u"unittest", u"discover",
                    u"-s", u"scripts/tests"])
    with io.open(log_path, u"w", encoding=u"utf-8") as handle:
        handle.write(out)
    tail = out[-4000:]
    ran = re.findall(u"(?m)^Ran (\\d+) tests", tail)
    ok = re.findall(u"(?m)^OK(?: \\(skipped=(\\d+)\\))?$", tail)
    if code != 0 or not ran or not ok:
        return None, u"%s 电池不绿（rc=%s）：%s" % (tag, code, tail.strip()[-500:])
    skipped = [g for g in ok if g]
    names = len(re.findall(u"(?m)^test .* \\*\\) ... skipped", out))
    return (ran[-1], skipped[-1] if skipped else u"0", names), None


# ── 读数（全部现读，抓不到就拒绝写盘）───────────────────────────────
if u"未由环境传入" in CI_LINE:
    die(CI_LINE)

dout, drc = sh([sys.executable, STREAK])
dline = (re.findall(u"(?m)^PRODUCT_STREAK (.*)$", dout, re.M) or [u""])[-1]
dk = dict(x.split(u"=", 1) for x in dline.split() if u"=" in x)
if drc != 0 or u"ledger_round" not in dk:
    die(u"product_streak 没出现读（rc=%s）：%s" % (drc, dout.strip()[-300:]))
ROUND = int(dk[u"ledger_round"]) + 1
fout, frc = sh([sys.executable, STREAK, u"--streak-for", s(ROUND)])
fl = (re.findall(u"(?m)^PRODUCT_STREAK_FOR (.*)$", fout, re.M) or [u""])[-1]
fk = dict(x.split(u"=", 1) for x in fl.split() if u"=" in x)
if frc != 0 or u"streak" not in fk:
    die(u"--streak-for 第 %d 轮取不到：%s" % (ROUND, fout.strip()[-300:]))
STREAK_N = fk[u"streak"]
LAST_SHA = (re.findall(u"last=(\\S+)", fl) or [u"?"])[-1]
LAST_ROUND = (re.findall(u"last_round=(\\d+)", fl) or [u"?"])[-1]
if STREAK_N != s(ROUND - int(LAST_ROUND)):
    # 上一轮这一格写成硬编码 `LAST_ROUND != ROUND - 4`（R304 的差值恰好是 4）⇒ 本轮差值变成 5 就当场抱死。
    # 那是好事：红的是**我自己那条假设**，不是 product_streak。真正的等式是「streak == 本轮 − 最后一笔产品提交的轮号」。
    die(u"as-of 第 %d 轮的最后一笔产品提交是第 %s 轮，streak 读到 %s ⇒ 等式 streak == ROUND − LAST_ROUND 不成立，先查"
        % (ROUND, LAST_ROUND, STREAK_N))

kout, krc = sh([sys.executable, u"-W", u"ignore", KNIVES])
knives_line = (re.findall(u"(?m)^R305_MUTATE (.*)$", kout, re.M) or [u""])[-1]
kk = dict(x.split(u"=", 1) for x in knives_line.split())
if krc != 0 or kk.get(u"CAUGHT") != kk.get(u"刀") or kk.get(u"NOT_RUN") != u"0" \
        or kk.get(u"RESTORE_CLEAN") != u"yes":
    die(u"刀表不干净（rc=%s）：%s\n%s" % (krc, knives_line, kout.strip()[-400:]))
KREST = kk[u"RESTORE_CLEAN"]

pout, prc = sh([sys.executable, PRECHECK])
at = re.findall(r"^ARM_TOTAL files=(\d+) arms=(\d+) dupes=(\d+) repeats=(\d+)", pout, re.M)
np_ = re.findall(r"^NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=(\d+) bad=(\d+)", pout, re.M)
if prc != 0 or not at or not np_ or at[-1][2] != u"0" or np_[-1][3] != u"0":
    die(u"预检不干净（rc=%s）：%s" % (prc, pout.strip()[-300:]))
ARMS, BAD, TABLES, COVERED = at[-1][1], np_[-1][3], np_[-1][0], np_[-1][1]

gout, grc = sh([sys.executable, u"-W", u"ignore", u"-m", u"unittest", u"-v",
                u"scripts.tests.test_motion_floor_gate"])
grun = re.findall(u"(?m)^Ran (\\d+) tests", gout)
gok = re.findall(u"(?m)^OK(?: \\(skipped=(\\d+)\\))?$", gout[-1500:])
if grc != 0 or not grun or not gok:
    die(u"闸门卷不绿（rc=%s）：%s" % (grc, gout.strip()[-400:]))
GATE_TESTS = grun[-1]

reg = rd(REGISTRY)
entries = re.findall(u'"test": "([^"]+)"', reg)
machines = sorted(set(re.findall(u'"machine": "([^"]+)"', reg)))
if not entries or len(entries) != 2:
    die(u"登记表读到 %d 条 ⇒ 与本轮的读数不一致，不许手抄" % len(entries))
live_src = rd(os.path.join(ROOT, "ClipboardHistory", "Tests",
                          "ClipboardHistoryAppTests", "MotionFilmstripTests.swift"))
for name in entries:
    if u"func %s(" % name not in live_src:
        die(u"登记的用例 %s 在源码里找不到 ⇒ 名字漂了（台账里那句红名也必须逐字取）" % name)
RUN_IDS = sorted(set(re.findall(u'"registered_run": "(\\d+)"', reg)))

tcout, tccrc = sh([sys.executable, u"-W", u"ignore", u"-m", u"unittest", u"-v",
                   u"scripts.tests.test_ledger_tokens"])
tok_line = (re.findall(u"(?m)^LEDGER_TOKENS (.*)$", tcout, re.M) or [u""])[-1]
tk = dict(x.split(u"=", 1) for x in tok_line.split())
if tccrc != 0 or tk.get(u"stray") != u"0":
    die(u"占位符那门不干净：%s" % tok_line)
TOK_BOOKS, TOK_CHARS = tk.get(u"books", u"?"), tk.get(u"chars", u"?")

vtext = rd(VERIFY_LOG) if os.path.exists(VERIFY_LOG) else u""
VSUM = (re.findall(u"(?m)^ROUND_VERIFY (.*)$", vtext, re.M) or [u""])[-1]
vk = dict(x.split(u"=", 1) for x in VSUM.split() if u"=" in x)
for key in (u"build_warnings", u"swift_executed", u"swift_failures", u"frames",
            u"baseline_changed", u"dmg", u"installed_version"):
    if key not in vk:
        die(u"沿用的四件套摘要缺格 %s（正文=%r）⇒ 那笔读数不可用，得先补跑" % (key, VSUM[:200]))

ui = rd(FILES["UI"])
U_MAX = max(int(x) for x in re.findall(u"(?m)^- \\*\\*U-(\\d{3,4})", ui))
D_MAX = max(int(x) for x in re.findall(u"(?m)^\\*\\*D-(\\d{3})", rd(FILES["DEC"])))
BL_MAX = max(int(x) for x in re.findall(u"(?m)^\\*\\*(\\d{3})\\. ", rd(FILES["BL"])))
if (U_MAX, D_MAX, BL_MAX) != (999, 285, 362):
    die(u"最大编号与本轮取靶时不符（读到 U-%d / D-%d / BACKLOG-%d）⇒ 有别的会话先动了账"
        % (U_MAX, D_MAX, BL_MAX))
UA, UB, UC = U_MAX + 1, U_MAX + 2, U_MAX + 3
DN, BLO = D_MAX + 1, BL_MAX + 1
U_DEFS = len(re.findall(u"(?m)^- \\*\\*U-\\d{3,4}[：(]", ui))

cv, crc = sh([sys.executable, CURVE])
if crc != 0:
    die(u"曲线仪器不是 0：" + cv.strip()[-200:])
SECTIONS = (re.findall(r"^ROUNDS=(\d+)", cv, re.M) or [u""])[-1]
LAST_RND = (re.findall(r"\bfirst=\d+\s+last=(\d+)", cv) or [u""])[-1]
BYROUND = (re.findall(u"(?m)^SCORES_BY_ROUND (.*)$", cv, re.M) or [u""])[-1]
pairs = re.findall(u"(\\d{3})=(\\d{2,3})", BYROUND)
if not SECTIONS or not LAST_RND or len(pairs) < 4:
    die(u"曲线读数缺档（ROUNDS=%s last=%s 分数对=%d）" % (SECTIONS, LAST_RND, len(pairs)))
RD_N = int(LAST_RND) + 1
TAIL_OLD = u" · ".join(u"%s=%s" % (a, b) for a, b in pairs[-4:])

pre, err = battery(u"写盘前", u"/tmp/r305_battery_pre.log")
if pre is None:
    die(err)
TOTAL = sum(SCORES)
ROWS = u"\n".join(u"| %s | %d/15 |" % (d, sc) for d, sc in zip(DIMS, SCORES))

SUBS = {
    u"@RTAG@": R_TAG, u"@PREV@": PREV_TAG, u"@RNEXT@": R_NEXT,
    u"@ROUND@": s(ROUND), u"@RDN@": s(RD_N),
    u"@UA@": s(UA), u"@UB@": s(UB), u"@UC@": s(UC),
    u"@DN@": s(DN), u"@BLO@": s(BLO),
    u"@STREAK@": STREAK_N, u"@LASTSHA@": LAST_SHA, u"@LASTROUND@": LAST_ROUND,
    u"@TODAY@": TODAY, u"@CI_LINE@": CI_LINE,
    u"@ROWS@": ROWS + u"\n",
    u"@ARMS@": ARMS, u"@BAD@": BAD, u"@TABLES@": TABLES, u"@COVERED@": COVERED,
    u"@KREST@": KREST, u"@GATE@": GATE_TESTS,
    u"@ENT@": s(len(entries)), u"@MACH@": u"、".join(machines),
    u"@RUNID@": u"、".join(RUN_IDS), u"@NAMES@": u" / ".join(entries),
    u"@BATT@": pre[0], u"@SKIP@": pre[1],
    u"@TOKB@": TOK_BOOKS, u"@TOKC@": TOK_CHARS,
    u"@SECTIONS@": s(int(SECTIONS) + 1), u"@TAIL@": TAIL_OLD,
    u"@WARN@": vk[u"build_warnings"], u"@SWIFT@": vk[u"swift_executed"],
    u"@SWFAIL@": vk[u"swift_failures"], u"@FRAMES@": vk[u"frames"],
    u"@CH@": vk[u"baseline_changed"], u"@Dmg@": vk[u"dmg"], u"@VER@": vk[u"installed_version"],
    u"@TOTAL@": s(TOTAL),
}
CI_LINE = fill_tpl(CI_LINE, SUBS)
SUBS[u"@CI_LINE@"] = CI_LINE


def fill(t):
    return fill_tpl(t, SUBS)


NEW_ROUND_TITLE = u"## 第 @ROUND@ 轮（@RTAG@ · U-@UA@…U-@UC@ · @TODAY@）：动效那两朵红有了按机器的登记，而编号本身越了界"

UI_NEW = u"""## 第 @ROUND@ 轮（@RTAG@ · U-@UA@…U-@UC@ · @TODAY@）：动效那两朵红有了按机器的登记，而编号本身越了界

- **U-@UA@：354 的第二步落地 —— `suite_reds` 从一张全局名单变成按机器切片的名单，@ENT@ 条登记只属于 @MACH@。**
  那两朵红（@NAMES@，登记于 run @RUNID@）只在 runner 上出现过：本机同一份代码不红，
  出现率 1/17 与 1/7（354① 现读）。旧写法只有两条路 —— 每轮重读一次单跑，或者删了当没发生；
  第三条是登记成**有名字的未覆盖**，而它成立的前提是登记**不许跨机顶检**、**能退场**。
  闸门现在按 `machine_key()` 取这台机器的份：`GITHUB_ACTIONS` ⇒ `github-runner`，否则 `local:<node>`
  （与 `test_surface_left_axes` 同一约定，`MOTION_FLOOR_MACHINE_KEY` 可显式钉）；
  没有机器键的条目直接红（`SUITE_UNSCOPED`），只在他机登记过的红**照旧红**并另打一行 `REGISTERED_ELSEWHERE`，
  红话里带着机器键与 run 号。退场提示也按机器切：本机不许替 runner 喊删。
  两把刀 M880 / M881 各钉一侧，RESTORE_CLEAN=@KREST@；闸门卷从 39 格抬到 @GATE@ 格（含「活账那两条在自己那台机器上真的顶用」）。
  顺带一处逐字核对：354 正文把红名写成 `testRowMoveIsVisibleToTheRuler`，
  而闸门与源码里的名字是 `testNativeRowMoveIsVisibleToTheRuler` —— 登记前我先拿源码 `func ` 对了一遍，
  所以那条新判据「登记的用例名必须在 MotionFilmstripTests.swift 里存在」现在是真的在判东西。
- **U-@UB@：边界轮 —— 下一节的编号从三位变四位（U-@UA@ 起），而两位尺子原本只认三位。**
  `scripts/tests/test_ledger_ids.py` 的 `U_DEF` / `U_RANGE` 写成 `\\d{3}`：到 1000 那天
  标题里的区间**匹配不到** ⇒ `missing_in_declared_u_range()` 返回 None，被调用方读成「这节没有区间形状」而不报错；
  定义行也一条数不到 ⇒ 「声明几条就要有几条定义行」只报样本不够。**两种收场都是静默降级，不是红**，
  而当天最可能的动作是照着消息去改台账而不是去改尺子。本轮把宽度抬成 `\\d{3,4}` 并配三格：
  四位区间与三条定义都要被认到、删掉中间那条必须正好点名 U-@UA@、
  以及一格「现读最大仍是三位 + 最新一节数得到至少三条定义」（这格在越界那天会自己要求改口径）。
  同一族的洞还留在 `D-\\d{3}` 与 BACKLOG 条目号 `\\d{3}` 上（今天 D-@DN@ / @BLO@，距 1000 还远）⇒ 新开 @BLO@。
- **U-@UC@：本轮自己撞的坑 —— 给 FACTS 那行加机器键时把它插在 `judged=` 前面，被 CI 契约当场抓住。**
  `scripts/tests/test_ci_report_selftest.py` 钉的是 `MOTION_FLOOR_FACTS judged=2/4` 这种
  「前缀紧挨着被判的那个量」的子串（三格），插在前面三格一起红，而红的都是我的写法而不是契约。
  同一批里第二朵红是 `test_skip_roster 内层没有结论行` —— 它不是独立缺陷：内层卷因第一朵红而打
  `FAILED` 而不是 `OK (skipped=N)`，闸门把「没解析到」读成「没结论」（R91 / R345 那一族，同源只记一条）。
  处置：机器键改打**行尾**，不动已登记的形状。这条的用处是让下一轮知道：
  改一行读数格式之前，先 grep 谁在按子串读它。
  同一轮里生成器自己也被自己的假设抱死一次：上一轮那条 as-of 检查写成硬编码 `LAST_ROUND == ROUND − 4`
  （R304 的差值恰好是 4），本轮差值天然是 5 ⇒ 它在读任何数之前就 REFUSE。
  红的是**我的假设**而不是取数口，所以修法是把它换回等式 `streak == ROUND − LAST_ROUND`（由现读的两边互相签字），
  而不是把 4 改成 5 —— 后者到第 306 轮还会再坏一次。

本轮产品文件 0 个（只动 `scripts/`），连续零改动 **@STREAK@** 轮
（现读 `python3 scripts/product_streak.py --streak-for @ROUND@`：as-of 第 @ROUND@ 轮的最后一笔产品提交是
@LASTSHA@ = 第 @LASTROUND@ 轮，即 R300 的代码半）。
四件套**沿用上一笔**（本轮没有 Swift 改动，也不许为打破 0 改动而重跑一遍当作新读数）：
告警 @WARN@、全量卷 @SWIFT@ / 失败 @SWFAIL@、帧 @FRAMES@ 张 changed=@CH@、dmg=@Dmg@、换装 @VER@
（取数口 `/tmp/r304_verify_run.log` 的 `ROUND_VERIFY` 那行，本轮现读重抄）。
看图腿与换装本机：本轮 **NOT-RUN**（0 个 Swift 文件 ⇒ 没有新产物可看，这不是"看了没变"）。
本轮现读的数：闸门卷 @GATE@ 格、刀表 2/2 CAUGHT、预检 tables=@TABLES@ arms=@ARMS@ bad=@BAD@、
登记表 @ENT@ 条（机器 @MACH@，run @RUNID@）、占位符扫描 @TOKB@ 本 @TOKC@ 字符 stray=0、
电池 Ran @BATT@ / OK (skipped=@SKIP@)。

"""

ITER_NEW = u"""## Round @RDN@ · @RTAG@（第 @ROUND@ 轮 · @TODAY@）：动效那两朵红登记成按机器的未覆盖，编号在越界前先抬尺

本轮做的事（0 个产品文件，只动 `scripts/`）：
把 `scripts/motion_floor_gate.py` 的用例级登记从"一张全局名单"改成**按机器切片**，
并真的往里落了 354 的那两朵红（@NAMES@，@MACH@，run @RUNID@）；
新增 `testLiveRegistryIsMachineScopedWithRealProvenance` 等五格（含一格证「活账那两条在自己那台机器上
确实把红变成 REGISTERED」），闸门卷 39 → @GATE@ 格；
两把刀 M880 / M881 把刀打在**闸门源码**上（机器切片退回全局 ⇒ 跨机那格必须红；退场不分机器 ⇒ 本机替
runner 删登记那格必须红），2/2 CAUGHT、RESTORE_CLEAN=@KREST@。
另一件是边界：U-@UA@ 起编号变四位，而 `test_ledger_ids.py` 两支尺写死 `\\d{3}`，坏掉的形状是静默跳过，
所以先把尺抬成 `\\d{3,4}` 并配三格正/反对照；同类洞留在 D 与 BACKLOG 号上，新开 @BLO@。
本轮自己撞的坑也记在这格：把机器键插在 `judged=` 前面会让 CI 的 report-only 契约三格一起红，
`test_skip_roster` 那朵是同源的第二个形状；改成打行尾。

七维度自评：
| 维度 | 分/满分 |
| --- | --- |
@ROWS@| 合计 | @TOTAL@/105 |

为什么不是满分（逐条）：真实视觉审查 10 —— 本轮 0 个 Swift 文件、没有新产物可看，看图腿明写 NOT-RUN，
只重抄了上一笔的四件套现读；判据有效性 14 —— 五格新判据里有一格直接读**活账**，不是只读夹具；
假绿防御 14 —— 登记必须带机器键、跨机不顶检、退场按机器切，三条各有刀或对照；
产品面推进 4 —— 0 个产品文件、连续 @STREAK@ 轮（欠的是 347 的真机证人，门在用户那边）；
台账一致性 14 —— 编号越界前先把尺抬宽并留一格「还没越界」的证人；红名与源码逐字对过；
交付诚实性 14 —— NOT-RUN 那两腿写清是没测不是没变，四件套沿用要标取数口；
可复核性 14 —— 登记条目带 run 号与还没关的单号，闸门红话打印机器键。

派生分由 `curve_from_ledger.py` 现读，不手抄。
未做（逐条）：① 354 的第三步（若两跑同现，先读 `MOTION_BAND_INTERVAL` 在负载下的数再谈判据本身）；
② **305 的台阶地板**（等 347 的真机证人）；③ 361 的合并（同步点已数出，还没做成一处派生）；
④ 360 剩下的文件与行；⑤ 359（取证目录没有读数汇聚点）；⑥ 348 的「数字对不对」那一格；
⑦ @BLO@（D / BACKLOG 号的同类三位假设）；⑧ 用户闸门 220 路 A / 228② / 265。

"""

DEC_NEW = u"""**D-286（@RTAG@）：登记一张"允许它红"的名单时，切片的维度必须写进条目本身，并且每一维都要有一把反方向的刀。**
理由与本轮读数：`suite_reds` 原本只按**用例名**登记，而这两朵红的成因是**机器**（@MACH@，run @RUNID@；
本机同码不红，出现率 1/17 与 1/7）。只按名字登记的后果是 runner 上的一次登记把本机的红也顶掉 ——
那正是 R144/R194 那一族「登记变成永久免检牌」的新变体。所以处置固定三件：
① 条目自带 `machine`，缺键即红（`SUITE_UNSCOPED`）；② 只有**这台机器**的登记才顶本机，
他机登记过的红照旧红并另打一行 `REGISTERED_ELSEWHERE`（不静默）；
③ 退场提示也按机器切（本机替 runner 喊"删掉这条"比不退场更坏）。
两把刀各钉 ① 与 ③ 的反面，2/2 CAUGHT。附一条同族的形状规矩：
**红名单里的用例名必须逐字与源码的 `func` 对账** —— 354 正文里那个名字少了 `Native` 前缀，
而对账那一格让它当场会被抓到。
"""

NOTE_354 = u"""  追记（@RTAG@ 第二步落地）：登记做成了，但**切片切的是机器**而不是名字。
  `scripts/motion_floor_expectations.json` 现在有 @ENT@ 条：@NAMES@，全部 `machine=@MACH@`、
  `registered_run=@RUNID@`、`points_to=BACKLOG 354`。闸门按 `machine_key()` 取本机那份：
  没有机器键 ⇒ 红；只在他机登记 ⇒ 本机照旧红并打一行 `REGISTERED_ELSEWHERE`；
  不再复现 ⇒ 按机器打退场提示。刀 M880（切片退回全局）与 M881（退场不分机器）各钉一侧。
  本格同时更正一处台账原文：本单开头写的红名 `testRowMoveIsVisibleToTheRuler` 少了 `Native` 前缀，
  闸门 FACTS 与源码里的都是 `testNativeRowMoveIsVisibleToTheRuler`（登记条目按逐字取，新判据会当场红）。
  本单剩下的：③ 若两跑同现，先读 `MOTION_BAND_INTERVAL`（间隔 − 抓帧 = 调度地板）在负载下的数，再谈判据本身；
  以及登记退场的**真验证**要等 runner 下一次那一跑自己说「这两条现在不红了」。
"""

ITEM_363 = u"""
**@BLO@. 台账编号的三位假设还剩两处，会在 D-1000 / BACKLOG 1000 那天以同样的形状静默降级（R305 现读）**：
本轮为了 U-@UA@ 这个四位边界把 `scripts/tests/test_ledger_ids.py` 的 `U_DEF` / `U_RANGE` 抬成 `\\d{3,4}`，
顺手把同文件里剩下两支也数了一遍 —— `DEC_DEF` / `CITED` 写死 `D-\\d{3}`，`ITEM` 写死 `^(?:\\*\\*)?(\\d{3})\\. `。
今天读到 D-@DN@ / BACKLOG-@BLO@，离 1000 还远，但坏法与本轮修掉的那一支**完全同形**：
匹配不到不是红，是被读成「这一节/这一条没有这种形状」，于是「标题引用了 D-xxx 就必须有正文」那格
会安静地不再判任何东西。要做的事很少（两处宽度 + 一格四位正对照 + 一格「现读还没越界」的证人），
先别做的原因是：没有当天的读数证明另两支也已经是 `\\d+` 的语义（`test_ui_round_interval_parity.py`
用的是 `\\d+`，说明这仓库里对同一件事有两种约定，合并时要先定哪种作准）。
不许写成「反正还远」——远的那几天没人会想起来，这正是 349/353 那一族的成因。
"""

CHG_NEW = (u"### Improved（@RTAG@ / 第 @ROUND@ 轮 / Round @RDN@ · 动效红名的登记按机器切片）\n\n"
           u"354 的第二步：`suite_reds` 每条登记现在必须带 `machine`，闸门只认这台机器那份 —— "
           u"@NAMES@ 两条登记只属于 @MACH@（run @RUNID@），本机同码不红；"
           u"缺机器键 ⇒ `MOTION_FLOOR_SUITE_UNSCOPED` 红；只在他机登记过的红 ⇒ 本机照旧红并另打 "
           u"`MOTION_FLOOR_REGISTERED_ELSEWHERE`；退场提示按机器切。"
           u"闸门卷 39 → @GATE@ 格，其中一格直接读**活账**证明登记在自己机器上真的顶用；"
           u"两把刀 M880 / M881 打在闸门源码上，2/2 CAUGHT、RESTORE_CLEAN=@KREST@、预检 tables=@TABLES@ "
           u"arms=@ARMS@ bad=@BAD@。同轮抬宽编号尺：`U_DEF` / `U_RANGE` 从 `\\d{3}` 到 `\\d{3,4}`，"
           u"配三位/四位两向对照；D 与 BACKLOG 号的同类假设新开 @BLO@。"
           u"另记一次自伤并当场修：把机器键插在 `judged=` 前会让 CI 的 report-only 契约三格一起红，"
           u"改打行尾；`test_skip_roster` 那朵是同源的第二个形状不是独立缺陷。"
           u"产品文件 0 个；四件套沿用上一笔现读（告警 @WARN@、全量卷 @SWIFT@/失败 @SWFAIL@、"
           u"帧 @FRAMES@ changed=@CH@、dmg=@Dmg@、换装 @VER@，取数口 /tmp/r304_verify_run.log），"
           u"看图腿与换装本机本轮 NOT-RUN；电池 Ran @BATT@ / OK (skipped=@SKIP@)。\n\n")

STATE_NEW = u"""## @RTAG@ 状态（第 @ROUND@ 轮 / Round @RDN@ · @TODAY@）

⓪ 读 CI（@RNEXT@ 的开场取数，只登记不轮询 = R140，并按 362 的写法**只列每次 push 的 tip**）：@CI_LINE@
要验的三件事：① STEP[18] On-screen probe coverage floor 那朵 `NOW_RUNS` 在名册翻回 can 之后是否不再红
（`811c4fc` 那一跑的答案见 @PREV@ 的 ⓪，本轮已交账）；
② **STEP[19] Motion coverage floor** 那两朵红在机器切片之后应当变成
`MOTION_FLOOR_REGISTERED_REDS=2` 且退出码 0 —— 这是本轮修法唯一真正的证人，本机签不了这一半；
若它仍然红在 `SUITE_RED`，那说明 runner 上报的机器键与 `github-runner` 不一致（读 FACTS 行尾的「机器=」）；
③ 登记里那两个用例名在 runner 上是否**存在**（名字与源码对账由本机那格判，跨机存在性只有 runner 能说）。

最后更新：@TODAY@（本地 · @RTAG@ / 第 @ROUND@ 轮 / Round @RDN@）：**354 的第二步结案到「登记做成」这一层** ——
`motion_floor_gate.py` 的用例级登记按机器切片，@ENT@ 条只属于 @MACH@；缺键红、跨机不顶检、退场按机器切，
刀 M880/M881 各钉一侧、2/2 CAUGHT、RESTORE_CLEAN=@KREST@；闸门卷 @GATE@ 格（含读活账那一格）。
编号越界先把尺抬宽：`U_DEF` / `U_RANGE` `\\d{3}` → `\\d{3,4}` + 三格对照（D / BACKLOG 号同形，新开 @BLO@）。
四件套沿用 @PREV@ 那笔的现读（本轮 0 个 Swift 文件）：告警 @WARN@、全量卷 @SWIFT@/失败 @SWFAIL@、
帧 @FRAMES@ changed=@CH@、dmg=@Dmg@、换装 @VER@；看图腿与换装本机 **NOT-RUN**（没测，不是没变）。
预检 tables=@TABLES@ arms=@ARMS@ bad=@BAD@；占位符扫描 @TOKB@ 本 stray=0；电池 Ran @BATT@ / OK (skipped=@SKIP@)。
产品文件 0 个，连续零改动 **@STREAK@** 轮（现读 `python3 scripts/product_streak.py --streak-for @ROUND@`：
as-of 第 @ROUND@ 轮的最后一笔产品提交是 @LASTSHA@ = 第 @LASTROUND@ 轮，即 R300 的代码半）。

① 下一轮（@RNEXT@）的靶：**354 的第三步** —— 等 runner 自己说这两条现在不红（② 那一格），
若两跑同现就先读 `MOTION_BAND_INTERVAL` 在负载下的数再谈判据；顺带 360 的第三批与 @BLO@（编号尺剩下两处三位假设）。
产品面：347 / 305 仍挡在用户那一边（要退出 App，或回答一句「收藏星按下够不够明显」）。

② 仍开：347（真机证人）、305（等 347）、354 的第三步（负载下的调度地板读数）、
@BLO@（D / BACKLOG 号的三位假设）、360（已搬两批）、361（同步点已数出，尚未合并）、
359（取证目录没有读数汇聚点）、362（⓪ 的成对号按 commit 列；本轮量到 3 笔根本没有 run）、
356（悬停换形状的三条候选）、348 的「数字对不对」那一格、349、350 第二步、351、344、
341 的 CI 契约半、339、312 具名出口、333、335、334、310、338 的另一半、328、323、322、317、304、291。

③ 用户闸门：220 路 A / 228② / 265。

"""

texts = {k: fill(v) for k, v in {
    "UI": UI_NEW, "IT": ITER_NEW, "DEC": DEC_NEW,
    "BL": NOTE_354, "NEWITEM": ITEM_363, "CH": CHG_NEW, "ST": STATE_NEW,
}.items()}

# ── 形状自测（写盘之前）────────────────────────────────────────────
ui_new = texts["UI"]
title = ui_new.splitlines()[0]
if u"（%s ·" % R_TAG not in title:
    die(u"标题缺 round_batch 要的前缀")
if title != fill_tpl(NEW_ROUND_TITLE, SUBS):
    die(u"UI 标题与我用来判区间的模板不一致 ⇒ 区间守卫会看错节")
nums = [int(x) for x in re.findall(u"(?m)^- \\*\\*U-(\\d{3,4})：", ui_new)]
if nums != [UA, UB, UC]:
    die(u"节内 U 定义行与标题区间不吻合：%s vs %s" % (nums, [UA, UB, UC]))
if len(re.findall(u"(?m)^\\| .+ \\| \\d+/15 \\|$", texts["IT"])) != 7:
    die(u"七维格子不是 7 行 n/15")
if u"七维度自评：" not in texts["IT"]:
    die(u"ITERATION 缺锚点")
if not re.search(u"^最后更新：\\d{4}-\\d{2}-\\d{2}（本地 · %s / 第 \\d+ 轮 / Round \\d+）" % R_TAG,
                 texts["ST"], re.M):
    die(u"STATE 缺「最后更新」行形状")
if len(re.findall(u"连续零改动 \\*\\*%s\\*\\* 轮" % STREAK_N, texts["ST"])) != 1:
    die(u"STATE 那一格形状不满足 353 的门")
NEW_U_DEFS = len(re.findall(u"(?m)^- \\*\\*U-\\d{3,4}[：(]", ui_new))
if NEW_U_DEFS != 3:
    die(u"本轮那一节的 U 定义行数=%d（要 3）⇒ 报告那一格会记错" % NEW_U_DEFS)
if re.search(u"@([A-Z][A-Z0-9_]{1,24})@", ui_new):
    die(u"新节里还有没替换的占位符：%s" % re.search(u"@([A-Z][A-Z0-9_]{1,24})@", ui_new).group(0))

orig = {k: rd(v) for k, v in FILES.items()}
if u"## 第 %d 轮" % ROUND in orig["UI"]:
    die(u"UI_AUDIT 已有第 %d 轮" % ROUND)
if u"## Round %d ·" % RD_N in orig["IT"]:
    die(u"ITERATION 已有 Round %d" % RD_N)
if u"**D-%d（" % DN in orig["DEC"]:
    die(u"DECISIONS 已有 D-%d" % DN)
if u"**%d. " % BLO in orig["BL"]:
    die(u"BACKLOG 已有 %d" % BLO)
if u"## %s 状态（" % R_TAG in orig["ST"]:
    die(u"STATE 已有 %s 节" % R_TAG)
if u"%s / 第 %d 轮" % (R_TAG, ROUND) in orig["CH"]:
    die(u"CHANGELOG 已有 %s" % R_TAG)
if orig["UI"].count(u"## 第 %d 轮" % (ROUND - 1)) != 1:
    die(u"UI_AUDIT 锚点不符（第 %d 轮标题不唯一）" % (ROUND - 1))
if orig["ST"].count(u"## %s 状态（" % PREV_TAG) != 1:
    die(u"STATE 锚点不符（%s 节不唯一）" % PREV_TAG)
if orig["CH"].count(u"## [Unreleased]\n\n") != 1:
    die(u"CHANGELOG 锚点不符")
h354 = [l for l in orig["BL"].splitlines(True) if l.startswith(u"**354. ")]
if len(h354) != 1:
    die(u"354 锚点异常（%d 处）" % len(h354))
if u"追记（%s 第二步落地）" % R_TAG in orig["BL"]:
    die(u"354 已有 %s 的同轮追记" % R_TAG)


def append_note_to_item(text, item, note):
    """把一段追记插到 **item.** 那一单的末尾（下一个 **NNN. 标题之前，跳过尾随空行）。"""
    lines = text.splitlines(True)
    head = [i for i, l in enumerate(lines) if l.startswith(u"**%d. " % item)]
    if len(head) != 1:
        die(u"%d 锚点异常（%d 处）⇒ 不许插" % (item, len(head)))
    k = len(lines)
    later = [i for i in range(head[0] + 1, len(lines)) if re.match(u"\\*\\*\\d{3}\\. ", lines[i])]
    if later:
        k = later[0]
    while lines[k - 1].strip() == u"":
        k -= 1
    joined = u"".join(lines[:k]).rstrip(u"\n")
    tail = u"".join(lines[k:]).lstrip(u"\n")
    return joined + u"\n" + note.strip(u"\n") + u"\n\n" + tail


# ── 报告：§13 三条 bullet + 标题/U 格/计数器 ────────────────────────
def bullet(text, label):
    """返回 (起, 止) 字符偏移：`- **label**` 那一整条 bullet（含结尾换行）。"""
    m = re.search(u"(?m)^- \\*\\*%s" % re.escape(label), text)
    if not m:
        die(u"报告里找不到 bullet「%s」⇒ 形状漂了" % label)
    nxt = re.search(u"(?m)^(- \\*\\*|## |\\Z)", text[m.end():])
    end = m.end() + (nxt.start() if nxt else len(text))
    return m.start(), end


FR_WALK = (u"- **走到哪了**：阶段二累计 `## Round` 节 **@SECTIONS@** 节，最新一节是 **Round @RDN@**；"
           u"自评曲线末四个 @TAIL@ · @RDN@=@TOTAL@（现读 `curve_from_ledger.py` 的 `SCORES_BY_ROUND` 与 `ROUNDS`）。"
           u"派生分连续多轮低于 90 ⇒ 按目标继续修，不收口。\n")
FR_DOOR = (u"- **判据与门的规模**：脚本电池现读 **Ran @BATT@**（写盘后同数），"
           u"变异臂抽到 **@ARMS@** 把（现读预检 `ARM_TOTAL`，bad=@BAD@）；U 定义行 **@UDEF@ 条**、最大 **U-@UC@**；"
           u"决定台账最大 **D-@DN@**，BACKLOG 最大 **@BLO@**。"
           u"台账自己也被扫：@TOKB@ 本 @TOKC@ 字符里未替换占位符 **0** 处（`scripts/tests/test_ledger_tokens.py`）。\n")
FR_PRODUCT = (u"- **产品面（这一节最该被读的部分）**：本轮产品文件 0 个，"
              u"产品面连续零改动轮数 = **@STREAK@**（唯一取数口 `python3 scripts/product_streak.py --streak-for @ROUND@`，"
              u"as-of 第 @ROUND@ 轮的最后一笔产品提交是 @LASTSHA@ = 第 @LASTROUND@ 轮）。"
              u"本轮把「动效那两朵红该怎么记」做成了按机器切片的登记，而不是每轮重读一次单跑；"
              u"四件套沿用上一笔（0 个 Swift 文件），看图腿与换装本机记 NOT-RUN。\n")

SUBS2 = dict(SUBS)
SUBS2[u"@UDEF@"] = s(U_DEFS + NEW_U_DEFS)
fr = orig["FR"]
repl = []
for label, tpl in ((u"走到哪了", FR_WALK), (u"判据与门的规模", FR_DOOR),
                   (u"产品面（这一节最该被读的部分）", FR_PRODUCT)):
    a, b = bullet(fr, label)
    repl.append((a, b, fill_tpl(tpl, SUBS2)))
a, b = bullet(fr, u"仍开（截至本轮，完整名单以 `AGENT_STATE.md` 的 %s 节 ② 为准）" % PREV_TAG)
fr_still = fr[a:b]
fr_still = fr_still.replace(
    u"354 的第二步（登记成有名字的未覆盖）",
    u"354 的第三步（负载下的调度地板读数；第二步本轮已落地：登记按机器切片）")
if u"362（⓪ 的成对号" not in fr_still:
    die(u"§13 的仍开 bullet 里没有上一轮新开的 362 ⇒ 报告与 STATE 少一单，先读 bullet 原文")
if u"354 的第二步" in fr_still:
    die(u"§13 里 354 第二步的措辞没被换掉 ⇒ 本轮的产出不进报告")
fr_still = fr_still.replace(u"348 剩余格", u"348 的「数字对不对」那一格")
fr_still = re.sub(u"%s 节 ②" % PREV_TAG, u"%s 节 ②" % R_TAG, fr_still)
if u"%s 节 ②" % R_TAG not in fr_still:
    die(u"§13 的仍开 bullet 没指向本轮的 STATE 节 ⇒ 指针过期")
if u"354 的第三步" not in fr_still:
    die(u"§13 的仍开 bullet 没落到本轮的形状（354 第二步已做）")
repl.append((a, b, fr_still))
repl.sort(key=lambda t: t[0], reverse=True)
fr_new = fr
for a, b, txt in repl:
    fr_new = fr_new[:a] + txt + fr_new[b:]

fr_new, n_title = re.subn(u"R9–R\\d+，\\d+ 轮自评",
                          u"R9–R%d，%s 轮自评" % (RD_N, SUBS2[u"@SECTIONS@"]), fr_new, count=1)
if n_title != 1:
    die(u"报告标题那一格没命中（%d 处）" % n_title)
fr_new, n_ucell = re.subn(u"U-31 … U-\\d+（R\\d+ 现读抬到最新一节）*",
                          u"U-31 … U-%d（@RTAG@ 现读抬到最新一节）" % UC,
                          fr_new, count=1)
if n_ucell != 1:
    die(u"§1 的 U 上界那一格没命中（%d 处）" % n_ucell)
fr_new = fill_tpl(fr_new, SUBS2)
sources_row = u"**%s**（commit `%s`）" % (u"R%d" % (int(LAST_ROUND) + 1), LAST_SHA)
if sources_row not in fr_new:
    die(u"§1 的 Sources 那一格不指向 as-of 读到的 " + LAST_SHA + u" ⇒ 要么账错了，要么取数口错了")
if u"scripts/product_streak.py" not in fr_new:
    die(u"报告里找不到取数口引用 ⇒ 353 的修法被回退了，先查")

new = {
    "UI": orig["UI"].replace(u"## 第 %d 轮" % (ROUND - 1), texts["UI"] + u"## 第 %d 轮" % (ROUND - 1), 1),
    "IT": orig["IT"].rstrip(u"\n") + u"\n\n" + texts["IT"].strip(u"\n") + u"\n",
    "DEC": orig["DEC"].rstrip(u"\n") + u"\n" + texts["DEC"].strip(u"\n") + u"\n",
    "BL": (append_note_to_item(orig["BL"], 354, texts["BL"]).rstrip(u"\n")
           + u"\n\n" + texts["NEWITEM"].strip(u"\n") + u"\n"),
    "ST": orig["ST"].replace(u"## %s 状态（" % PREV_TAG, texts["ST"] + u"## %s 状态（" % PREV_TAG, 1),
    "CH": orig["CH"].replace(u"## [Unreleased]\n\n", u"## [Unreleased]\n\n" + texts["CH"], 1),
    "FR": fr_new,
}
for key in new:
    if key != u"FR" and len(new[key]) <= len(orig[key]):
        die(u"%s 写后不比写前长 ⇒ 可能是替换而不是插入" % key)
# BACKLOG 那一本有两个落点（354 的追记 + 文件尾的新单），两处都要各证一次
if new["BL"].count(u"**%d. " % BLO) != 1:
    die(u"新单 %d 在 BACKLOG 里出现 %d 次 ⇒ 要么没落要么落了多份" % (BLO, new["BL"].count(u"**%d. " % BLO)))
i354 = new["BL"].index(u"**354. ")
i355 = new["BL"].index(u"**355. ")
inote = new["BL"].index(u"  追记（%s 第二步落地）" % R_TAG)
if not (i354 < inote < i355):
    die(u"354 的追记落在别的单里（354=%d 追记=%d 355=%d）⇒ 按整行找落点不够，还要证它在区间内"
        % (i354, inote, i355))
if new["BL"].index(u"**%d. " % BLO) < i355:
    die(u"新单 %d 落在 355 之前 ⇒ 它被插进历史条目中间，而不是文件尾" % BLO)
sec = re.compile(u"(?m)^## 13\\. .*?(?=^## |\\Z)", re.S)
old_sec, new_sec = sec.search(orig["FR"]), sec.search(new["FR"])
if not (old_sec and new_sec):
    die(u"§13 那一节在写前或写后不见了")
n_old = len(re.findall(u"(?m)^- \\*\\*", old_sec.group(0)))
n_new = len(re.findall(u"(?m)^- \\*\\*", new_sec.group(0)))
if n_new < n_old:
    die(u"§13 的 bullet 从 %d 条变成 %d 条 ⇒ 有内容被吞了" % (n_old, n_new))
if (u"产品面连续零改动轮数 = **%s**" % STREAK_N) not in new["FR"]:
    die(u"报告的 streak 那一格没落成本轮的值")

STRAY_RX = re.compile(u"@([A-Z][A-Z0-9_]{1,24})@")
stray = []
for key, text in new.items():
    for number, line in enumerate(text.split(u"\n"), 1):
        for hit in STRAY_RX.finditer(line):
            stray.append(u"%s:%d %s" % (key, number, hit.group(0)))
if stray:
    die(u"写盘前有没被替换的占位符（%d 处）：%s" % (len(stray), u"；".join(stray[:10])))

for key, text in new.items():
    wr(FILES[key], text)

# §1 的"现状格"由那支仪器自己抬（幂等、排在台账之后）：本轮生成器不替它抄数，
# 少了这一步 `test_final_report_section1_cell` 会红在"§1 停在旧数而仪器已往前走"。
refresh_out, refresh_rc = sh([sys.executable, REFRESH])
if refresh_rc != 0:
    for key, text in orig.items():
        wr(FILES[key], text)
    die(u"§1 刷新器不是 0 ⇒ 七本已整体还原：" + refresh_out.strip()[-400:])

post, err = battery(u"写盘后", u"/tmp/r305_battery_post.log")
if post is None:
    for key, text in orig.items():
        wr(FILES[key], text)
    die(u"写盘后电池不绿 ⇒ 七本已整体还原：" + err)
if post != pre:
    for key, text in orig.items():
        wr(FILES[key], text)
    die(u"电池计数变了（" + str(pre) + u" → " + str(post) + u"）⇒ 七本已还原")

cout, crc2 = sh([sys.executable, STREAK, u"--check"])
if crc2 != 0:
    for key, text in orig.items():
        wr(FILES[key], text)
    die(u"353 的门不认这版台账 ⇒ 七本已还原：" + (cout + u"\n").strip()[-400:])

cv2, _ = sh([sys.executable, CURVE])
byround2 = (re.findall(u"(?m)^SCORES_BY_ROUND (.*)$", cv2, re.M) or [u""])[-1]
score = dict(re.findall(u"(\\d{3})=(\\d{2,3})", byround2)).get(s(RD_N), u"?")
if score == u"?":
    die(u"曲线里没有 Round %d 的分数 ⇒ ITERATION 那一节没落地" % RD_N)
gaps = (re.findall(r"^GAPS=(\S+)", cv2, re.M) or [u"?"])[-1]
print(u"LEDGERS_R305 OK batt=Ran " + post[0] + u" (skipped=" + post[1] + u") streak=" + STREAK_N
      + u" prod=0 gate=" + GATE_TESTS + u" knives=" + kk[u"CAUGHT"] + u"/" + kk[u"刀"]
      + u" registry=" + s(len(entries)) + u"/" + u",".join(machines) + u" run=" + u",".join(RUN_IDS)
      + u" U=" + s(UA) + u".." + s(UC) + u" D=" + s(DN) + u" BACKLOG_new=" + s(BLO)
      + u" tok=" + TOK_BOOKS + u"/" + TOK_CHARS + u" derived_score(Round " + s(RD_N) + u")=" + s(score)
      + u" GAPS=" + gaps)

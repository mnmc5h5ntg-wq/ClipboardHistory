#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R306 的台账生成器（第 305 轮 / Round 303）：360 第三批搬完 + 363 结案 + 一次真看图腿。

数一律现读：覆盖率那一卷、Swift 名册解析器、刀表、预检、四件套摘要、曲线、电池、product_streak。
本轮改了 6 份 Swift（4 份搬动 + 名册 + 通道表）⇒ **被改过形状的文件会弄哑历史刀的 needle**（D-284 第二条），
所以除本轮表之外还重跑 R301 / R302 / R303 / R304 四张历史表，并要求预检 bad=0（静态证人）。
写盘前后各跑一次电池且要求同数；写盘前先自扫未替换占位符；任何一格读不到就整体不写。
"""
import io
import json
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
ROSTER_SRC = os.path.join(ROOT, "scripts", "readings_roster_source.py")
COV_ROLL = os.path.join("scripts", "tests", "test_readings_channel_coverage.py")
TOKEN_ROLL = os.path.join("scripts", "tests", "test_ledger_tokens.py")
KNIVES = os.path.join(ROOT, ".scratch", "motion-audit-2", "mutate_r306.py")
HIST = [("R301", os.path.join(ROOT, ".scratch", "motion-audit-2", "mutate_r301.py")),
        ("R302", os.path.join(ROOT, ".scratch", "motion-audit-2", "mutate_r302.py")),
        ("R303", os.path.join(ROOT, ".scratch", "motion-audit-2", "mutate_r303.py")),
        ("R304", os.path.join(ROOT, ".scratch", "motion-audit-2", "mutate_r304.py"))]
REFRESH = os.path.join(ROOT, ".scratch", "motion-audit-2", "refresh_report_section1.py")
CI_READ = os.path.join(ROOT, "scripts", "ci_read.py")
VERIFY_LOG = "/tmp/r306_verify_run.log"
FRAME_DIR = "/tmp/r306_verify/frames"
R_TAG, PREV_TAG, R_NEXT = u"R306", u"R305", u"R307"
TODAY = subprocess.check_output([u"date", u"+%Y-%m-%d"]).decode().strip()
CI_LINE = os.environ.get("R306_CI_LINE", u"⓪ 未由环境传入 ⇒ 不许写盘")
# 本轮看图的判断（写在代码里是因为它来自"看了哪几张 + 量到哪一格"，见下面 EYE 的断言）
EYE = os.environ.get("R306_EYE", u"")

DIMS = [u"真实视觉审查", u"判据有效性", u"假绿防御", u"产品面推进", u"台账一致性",
        u"交付诚实性", u"可复核性"]
SCORES = [12, 14, 14, 4, 14, 14, 14]


def s(x):
    return str(x)


def die(msg):
    sys.stderr.write(u"LEDGERS_R306 REFUSED: " + msg + u"\n")
    sys.exit(1)


def rd(path):
    with io.open(path, encoding=u"utf-8") as handle:
        return handle.read()


def wr(path, text):
    with io.open(path, u"w", encoding=u"utf-8") as handle:
        handle.write(text)


def sh(cmd, cwd=ROOT):
    env = dict(os.environ)
    env["PYTHONUTF8"] = u"1"
    env["PYTHONDONTWRITEBYTECODE"] = u"1"
    proc = subprocess.run(cmd, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return proc.stdout.decode(u"utf-8", u"replace"), proc.returncode


def fill_tpl(text, mapping):
    for key in sorted(mapping, key=len, reverse=True):
        text = text.replace(key, mapping[key])
    return text


def battery(tag, log_path):
    out, code = sh([sys.executable, u"-W", u"ignore", u"-m", u"unittest", u"discover",
                    u"-s", u"scripts/tests"])
    wr(log_path, out)
    tail = out[-4000:]
    ran = re.findall(u"(?m)^Ran (\\d+) tests", tail)
    ok = [g for g in re.findall(u"(?m)^OK(?: \\(skipped=(\\d+)\\))?$", tail) if g]
    if code != 0 or not ran or not ok:
        return None, u"%s 电池不绿（rc=%s）：%s" % (tag, code, tail.strip()[-500:])
    return (ran[-1], ok[-1]), None


def summary(out, prefix, rc, need):
    line = (re.findall(u"(?m)^%s (.*)$" % prefix, out, re.M) or [u""])[-1]
    kv = dict(x.split(u"=", 1) for x in line.split() if u"=" in x)
    if rc != 0 or any(k not in kv for k in need):
        die(u"%s 没有可判正文（rc=%s，缺=%s）：%s"
            % (prefix, rc, [k for k in need if k not in kv], line[:200]))
    return kv


# ── 读数 ───────────────────────────────────────────────────────────
if u"未由环境传入" in CI_LINE:
    die(CI_LINE)
if not EYE.strip():
    die(u"本轮要看图腿：R306_EYE 没传 ⇒ 不许把真实视觉审查写成沿用或省略（目标模式每轮都要看渲染出来的画面）")

dout, drc = sh([sys.executable, STREAK])
dk = summary(dout, u"PRODUCT_STREAK", drc, [u"ledger_round", u"streak"])
ROUND = int(dk[u"ledger_round"]) + 1
fout, frc = sh([sys.executable, STREAK, u"--streak-for", s(ROUND)])
fk = summary(fout, u"PRODUCT_STREAK_FOR", frc, [u"streak", u"last", u"last_round"])
STREAK_N, LAST_SHA, LAST_ROUND = fk[u"streak"], fk[u"last"], fk[u"last_round"]
if STREAK_N != s(ROUND - int(LAST_ROUND)):
    die(u"as-of 第 %d 轮：streak=%s 而 ROUND−LAST_ROUND=%s ⇒ 两边不同源，先查"
        % (ROUND, STREAK_N, s(ROUND - int(LAST_ROUND))))

vtext = rd(VERIFY_LOG) if os.path.exists(VERIFY_LOG) else u""
vk = summary(vtext, u"ROUND_VERIFY", 0,
             [u"build_warnings", u"swift_executed", u"swift_failures", u"swift_skipped",
              u"frames", u"baseline_compared", u"baseline_changed", u"baseline_missing",
              u"dmg", u"installed_version"])
for key, want in ((u"build_warnings", u"0"), (u"swift_failures", u"0"),
                  (u"baseline_changed", u"0"), (u"baseline_missing", u"0"), (u"dmg", u"ok")):
    if vk[key] != want:
        die(u"四件套不干净（%s=%s，要 %s）⇒ 先修再来落账" % (key, vk[key], want))
if int(vk[u"baseline_compared"]) == 0 or int(vk[u"frames"]) == 0:
    die(u"分母是 0（frames=%s compared=%s）⇒ 这是空对账，看图腿必须记 NOT-RUN 而不是 changed=0"
        % (vk[u"frames"], vk[u"baseline_compared"]))
on_disk = len([n for n in os.listdir(FRAME_DIR) if n.endswith(u".png")]) if os.path.isdir(FRAME_DIR) else 0
if on_disk == 0:
    die(u"帧目录 %s 里没有 PNG ⇒ 本轮不能声称看过画面" % FRAME_DIR)

cout, crc = sh([sys.executable, u"-W", u"ignore", u"-m", u"unittest", u"-v", COV_ROLL])
ck = summary(cout, u"READINGS_COVERAGE", crc,
             [u"files_scanned", u"emitters", u"clean_emitters", u"roster",
              u"bare_print_lines", u"ceiling", u"named_uncovered",
              u"swift_total", u"swift_files"])
if ck[u"bare_print_lines"] != ck[u"ceiling"]:
    die(u"棘轮不等（盘上 %s vs 登记 %s）⇒ 搬完没同轮改登记值" % (ck[u"bare_print_lines"], ck[u"ceiling"]))
if ck[u"clean_emitters"] != ck[u"roster"]:
    die(u"派生名册（%s）与声明名册（%s）不同数" % (ck[u"clean_emitters"], ck[u"roster"]))
if ck[u"named_uncovered"] != ck[u"bare_print_lines"]:
    die(u"按文件的未覆盖合计（%s）与盘上行数（%s）不一致 ⇒ 那份名单过期" % (ck[u"named_uncovered"], ck[u"bare_print_lines"]))

kout, krc = sh([sys.executable, u"-W", u"ignore", KNIVES])
kk = summary(kout, u"R306_MUTATE", krc, [u"刀", u"CAUGHT", u"ESCAPED", u"NOT_RUN", u"RESTORE_CLEAN"])
if kk[u"CAUGHT"] != kk[u"刀"] or kk[u"NOT_RUN"] != u"0" or kk[u"ESCAPED"] != u"0" or kk[u"RESTORE_CLEAN"] != u"yes":
    die(u"本轮刀表不干净：%s" % kout.strip()[-400:])
for tag, path in HIST:
    hout, hrc = sh([sys.executable, u"-W", u"ignore", path])
    hk = summary(hout, u"%s_MUTATE" % tag, hrc, [u"CAUGHT", u"刀", u"NOT_RUN", u"RESTORE_CLEAN"])
    if hk[u"CAUGHT"] != hk[u"刀"] or hk[u"NOT_RUN"] != u"0" or hk[u"RESTORE_CLEAN"] != u"yes":
        die(u"历史刀表 %s 不干净（本轮改过它 needle 住的 Swift 文件？）：%s" % (tag, hout.strip()[-400:]))
    print(u"HIST %s %s" % (tag, hk))

pout, prc = sh([sys.executable, PRECHECK])
at = re.findall(r"^ARM_TOTAL files=(\d+) arms=(\d+) dupes=(\d+) repeats=(\d+)", pout, re.M)
np_ = re.findall(r"^NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=(\d+) bad=(\d+)", pout, re.M)
if prc != 0 or not at or not np_ or at[-1][2] != u"0" or at[-1][3] != u"0" or np_[-1][3] != u"0":
    die(u"预检不干净：%s" % pout.strip()[-300:])
ARMS, BAD, TABLES, COVERED = at[-1][1], np_[-1][3], np_[-1][0], np_[-1][1]

tout, trc = sh([sys.executable, u"-W", u"ignore", u"-m", u"unittest", u"-v", TOKEN_ROLL])
tk = summary(tout, u"LEDGER_TOKENS", trc, [u"books", u"chars", u"stray"])
if tk[u"stray"] != u"0":
    die(u"台账里有未替换占位符：%s" % tk)

ui = rd(FILES["UI"])
U_MAX = max(int(x) for x in re.findall(u"(?m)^- \\*\\*U-(\\d{3,4})", ui))
D_MAX = max(int(x) for x in re.findall(u"(?m)^(?:#{2,3} D-|\\*\\*D-)(\\d{3,4})", rd(FILES["DEC"])))
BL_MAX = max(int(x) for x in re.findall(u"(?m)^\\*\\*(\\d{3,4})\\. ", rd(FILES["BL"])))
if (U_MAX, D_MAX, BL_MAX) != (1002, 286, 363):
    die(u"最大编号与本轮取靶时不符（U-%d / D-%d / BACKLOG-%d）⇒ 有别的会话先动了账" % (U_MAX, D_MAX, BL_MAX))
UA, UB, UC, UD = U_MAX + 1, U_MAX + 2, U_MAX + 3, U_MAX + 4
DN, BLO = D_MAX + 1, BL_MAX + 1
U_DEFS = len(re.findall(u"(?m)^- \\*\\*U-\\d{3,4}[：(]", ui))

# ──  的成对号与 runner 证人：现读现取，不手抄（362 + D-284）─────────────
FLOOR_RX = re.compile(u"(?m)^\\s*(?:\\[[^\\]]*\\]\\s*)?(MOTION_FLOOR[A-Z_]*)=(\\S+)")
LINE_RX = re.compile(u"(?m)^\\s*(?:\\[[^\\]]*\\]\\s*)?(MOTION_FLOOR_SUITE_\\w+=\\S+.*)$")
lout, lrc = sh([sys.executable, CI_READ, u"latest"])
pair = re.findall(u"(?m)^RUN=(\\d+) sha=(\\w+) status=(\\w+) conclusion=(\\S*)", lout)
if lrc != 0 or not pair:
    die(u"⓪ 的成对号读不到（rc=%s）：%s" % (lrc, lout.strip()[-200:]))
RUN_ID, TIP_SHA, TIP_STATUS, TIP_CONC = pair[-1]
hout, hrc = sh([u"git", u"rev-parse", u"--short", u"HEAD"])
if hrc != 0 or hout.strip() != TIP_SHA:
    die(u"⓪ 的 sha（%s）与本地 HEAD（%s）不符 ⇒ 有别的东西先落了一笔，那份日志不是这一笔的证人"
        % (TIP_SHA, hout.strip()))
if TIP_STATUS != u"completed":
    die(u"⓪ 那一跑（%s）还是 %s ⇒ 证人没到，不许把 354 的第三步写成已交账" % (RUN_ID, TIP_STATUS))
rout, rrc = sh([sys.executable, CI_READ, u"readings", RUN_ID, u"MOTION_FLOOR"])
floor = dict(FLOOR_RX.findall(rout))
if rrc != 0 or floor.get(u"MOTION_FLOOR_SUITE_CLEAN") != u"0" or u"MOTION_FLOOR_REDS" not in floor:
    die(u"runner 的 MOTION_FLOOR 那几行没解析到（rc=%s，键=%s）⇒ 按记忆写就是假证人"
        % (rrc, sorted(floor)))
SUITE_LINE = (LINE_RX.findall(rout) or [u""])[-1]
MACHINE = (re.findall(u"机器=(\\S+)", SUITE_LINE) or [u"?"])[-1]
NAMES = json.load(io.open(os.path.join(ROOT, u"scripts", u"motion_floor_expectations.json"),
                          encoding=u"utf-8")).get(u"suite_reds", [])
MINE = [e.get(u"test") for e in NAMES if e.get(u"machine") == MACHINE]
if not MINE:
    die(u"机器 %s 在 suite_reds 里没有登记 ⇒ 「两跑没红」这条读数没有对象，证人无从谈起" % MACHINE)

cv, crc = sh([sys.executable, CURVE])
if crc != 0:
    die(u"曲线仪器不是 0：" + cv.strip()[-200:])
SECTIONS = (re.findall(r"^ROUNDS=(\d+)", cv, re.M) or [u""])[-1]
LAST_RND = (re.findall(r"\bfirst=\d+\s+last=(\d+)", cv) or [u""])[-1]
BYROUND = (re.findall(u"(?m)^SCORES_BY_ROUND (.*)$", cv, re.M) or [u""])[-1]
pairs = re.findall(u"(\\d{3})=(\\d{2,3})", BYROUND)
if not SECTIONS or not LAST_RND or len(pairs) < 4:
    die(u"曲线读数缺档")
RD_N = int(LAST_RND) + 1
TAIL_OLD = u" · ".join(u"%s=%s" % (a, b) for a, b in pairs[-4:])

pre, err = battery(u"写盘前", u"/tmp/r306_battery_pre.log")
if pre is None:
    die(err)
TOTAL = sum(SCORES)
ROWS = u"\n".join(u"| %s | %d/15 |" % (d, sc) for d, sc in zip(DIMS, SCORES))

SUBS = {
    u"@RTAG@": R_TAG, u"@PREV@": PREV_TAG, u"@RNEXT@": R_NEXT,
    u"@ROUND@": s(ROUND), u"@RDN@": s(RD_N), u"@TODAY@": TODAY,
    u"@UA@": s(UA), u"@UB@": s(UB), u"@UC@": s(UC), u"@UD@": s(UD), u"@DN@": s(DN), u"@BLO@": s(BLO),
    u"@RUN@": RUN_ID, u"@SHA@": TIP_SHA, u"@CONC@": TIP_CONC or u"未读",
    u"@MACHINE@": MACHINE, u"@SUITELINE@": SUITE_LINE.strip(),
    u"@FLOOROK@": floor.get(u"MOTION_FLOOR_OK", u"?"),
    u"@FLOORREDS@": floor.get(u"MOTION_FLOOR_REDS", u"?"),
    u"@FLOORJUDGED@": floor.get(u"MOTION_FLOOR_FACTS", u"?"),
    u"@MINEN@": s(len(MINE)), u"@MINENAMES@": u" / ".join(sorted(x for x in MINE if x)),
    u"@PREVRUN@": (re.findall(u"(?m)^RUN=(\\d+)", lout) or [u"?"])[-1],
    u"@STREAK@": STREAK_N, u"@LASTSHA@": LAST_SHA, u"@LASTROUND@": LAST_ROUND,
    u"@ROWS@": ROWS + u"\n", u"@TOTAL@": s(TOTAL),
    u"@BATT@": pre[0], u"@SKIP@": pre[1],
    u"@ARMS@": ARMS, u"@TABLES@": TABLES, u"@COVERED@": COVERED,
    u"@K@": kk[u"刀"], u"@KC@": kk[u"CAUGHT"], u"@KREST@": kk[u"RESTORE_CLEAN"],
    u"@SECTIONS@": s(int(SECTIONS) + 1), u"@TAIL@": TAIL_OLD, u"@CI_LINE@": CI_LINE,
    u"@EYE@": EYE, u"@PNGS@": s(on_disk),
    u"@BARE@": ck[u"bare_print_lines"], u"@CEIL@": ck[u"ceiling"],
    u"@ROSTER@": ck[u"roster"], u"@FILES@": ck[u"files_scanned"], u"@EMIT@": ck[u"emitters"],
    u"@SWTOT@": ck[u"swift_total"], u"@SWFILES@": ck[u"swift_files"],
    u"@UNCOV@": ck[u"named_uncovered"],
    u"@WARN@": vk[u"build_warnings"], u"@SWIFT@": vk[u"swift_executed"],
    u"@SWFAIL@": vk[u"swift_failures"], u"@SWSKIP@": vk[u"swift_skipped"],
    u"@FRAMES@": vk[u"frames"], u"@CM@": vk[u"baseline_compared"], u"@CH@": vk[u"baseline_changed"],
    u"@MISS@": vk[u"baseline_missing"], u"@Dmg@": vk[u"dmg"], u"@VER@": vk[u"installed_version"],
    u"@TOKB@": tk[u"books"], u"@TOKC@": tk[u"chars"],
}
CI_LINE = fill_tpl(CI_LINE, SUBS)
SUBS[u"@CI_LINE@"] = CI_LINE
EYE = fill_tpl(EYE, SUBS)
SUBS[u"@EYE@"] = EYE


def fill(t):
    return fill_tpl(t, SUBS)


UI_NEW = u"""## 第 @ROUND@ 轮（@RTAG@ · U-@UA@…U-@UD@ · @TODAY@）：第三批裸 stdout 搬完，编号尺一次抬齐，看图腿回到 RUN，354 的 runner 证人到了

- **U-@UA@：360 的第三批 —— 四份判据卷 14 行搬进文件通道，棘轮 29 → 现读 @BARE@，派生名册 14 → @ROSTER@。**
  搬的是 `OffscreenSymbolInkProbeTests`（4：`INK 前提` / `INK 逐枚` / `INK 产品设置侧栏` / `INK 结论`）、
  `Round4MarkdownTests`（4：`COLOR_PROBE` + 三条 `MARKDOWN_PERF`）、`CapturePathWriteBudgetTests`
  （3：`CAPTURE_PATH_BLOCKED` / `CAPTURE_PATH_BUDGET` / `CAPTURE_PATH_FULL_ARCHIVE`）、
  `PerfBudgetTests`（3：`PERF[...]` / 小图采样 / 稳态一次比较）。
  同步点本轮数是**四处**：判据源码的调用、电池那一卷的登记值（29→@CEIL@）、按文件的未覆盖名单（15 份 29 行→
  11 份 @UNCOV@ 行）、Swift 那张名字名册的通道表（+`OffscreenSymbolInkProbeTests` +`PerfBudgetTests`，
  因为它们本来就在那 8 个文件的标记名册里 ⇒ 换了腿就得换通道）。三处都有证人：
  M882 写回一行裸 print ⇒ 红在「盘上有 登记值+1 行」（这一格的期望正文也是派生的）；M883 从通道表删名字 ⇒ Swift 红在与名册不符；
  M884（下面那格）打在编号尺上。刀 @KC@/@K@ 全 CAUGHT、RESTORE_CLEAN=@KREST@。
  而**重跑历史表**（D-284 第二条）这一格今天交出了五把坏刀：`mutate_r301` 的 M871 与 `mutate_r302` 的 M873
  钉在 Swift `roster` 的**头两行**，本轮按字母序插入新文件名把头部挤走 ⇒ 命中 0 次 = NOT_RUN；
  `mutate_r303` 的 M875/M876 与 `mutate_r304` 的 M879 把**棘轮旧值手抄进 needle 与期望正文**（「盘上有 30 行」，
  而同一张表的文件头还写着 43 ⇒ 一份表里三个数）⇒ WRONG_CELL / NOT_RUN。两根改成钉名单尾行（字母序只往上插），
  三根改成从守卫文件**现读登记值再派生** needle 与期望（与 R298「让判据自己定位生日」同一修法：
  推迟腐烂不是修，自己找数才是），本轮自己的 M882 也一并改成派生 —— 它原本写着「盘上有 16 行」，下一批搬完一样会烂。
  另把 r302 加进本轮的历史表名单（它也被本轮改过的文件喂着）。
- **U-@UB@：363 结案 —— D 号与 BACKLOG 条目号的三位假设一起抬成 `\\d{3,4}`，位数只当读数不当判据。**
  现读最大 D-@DN@、条目 @BLO@（都还是三位），而 R305 已经演示过一次三位假设坏掉的形状是**静默降级**：
  匹配不到就被读成「这条引用不存在 / 这节没有区间」，于是"引用了就必须有正文"那格安静地不再判任何东西。
  本轮把 `DEC_DEF_HEADING_ONLY` / `BOLD_DEF` / `DEC_DEF` / `CITED` / `ITEM` / `ITEM_HEADING_ONLY` / `ITEM_BOLD`
  七支一起抬宽，并加三格：四位决定号要被认到（正对照，期望值**从 findall 的元组形状摊平后比**，
  我第一版按单组心算 ⇒ 红在自己写的期望上）、四位条目号两形都认到、三位存量形状仍然认到；
  最后一格只 `print` 现读位数（`D_ID_BOUNDARY 决定最大=D-@DN@ 位数=3｜条目最大=@BLO@ 位数=3`）不做断言 ——
  R305 那格「还没越界」在越界当天红过一次，这次不再犯同一个错。
  **这一格是被自己的刀逼出来的一处真洞**：M884 第一版把 `DEC_DEF_HEADING_ONLY` 从 `\\d{3,4}` 改回 `\\d{3}`，
  26 格全绿 ⇒ `ESCAPED`。刀没坏，是判据缺一根轴 —— 那两支对照尺只在**真台账**上跑，而真台账今天全是三位号，
  所以"对照尺认得四位"这件事从来没有断言证过。补两条断言（标题形对照要认到 `D-1000`、粗体形对照要认到 `D-1001`）
  之后 M884 才红在该点名的那一格。这与「临时尺要配正对照」同族，但这次的证人是一把打空的刀，比推理便宜且不可辩驳。
- **U-@UC@：看图腿回到 RUN —— 看的是本轮重捕的 @PNGS@ 张帧（@FRAMES@ 张进基线对账、changed=@CH@、missing=@MISS@）。**
  @EYE@

- **U-@UD@：354 的 runner 证人到了，而它说的是「这一跑没红」⇒ 这张登记表缺的不是证据，是退场通道。**
  现读 run @RUN@（sha @SHA@，结论 @CONC@）的 STEP「Motion coverage floor」：@SUITELINE@
  —— 也就是这台机器（@MACHINE@）这一跑**一条红用例都没有**，而 `suite_reds` 里为它登记着 @MINEN@ 条
  （@MINENAMES@）。同一格在上一跑 39833209888 也是 CLEAN=0 ⇒ **连续两跑没红**。
  这一格不许读成「登记被证伪」：两条登记的理由自己写着出现率 1/17 与 1/7，一跑不红本就在预期之内
  （D-251：单遍读数既不配给产品定罪，也不配替产品脱罪）。真正的缺口在门自己身上 ——
  `suite_verdicts` 在 `not named and summary == 0` 那一支直接 `return`，于是"本机登记的名字这一跑没露面"
  连一行都不打 ⇒ 登记可以无限期留在表里慢慢变成免检牌堆；arms 那一侧早就有 `MOTION_FLOOR_STALE`
  专治这一格（判到了就点名删条目），`suite_reds` 这一侧没有对应物。同跑另两行现读：
  `MOTION_FLOOR_OK=@FLOOROK@`、`MOTION_FLOOR_REDS=@FLOORREDS@`。⇒ 354 加**第四步**：缺席要能被打点，而不是再等一跑。

本轮产品文件 0 个（Tests / scripts / .scratch），连续零改动 **@STREAK@** 轮
（现读 `python3 scripts/product_streak.py --streak-for @ROUND@`：as-of 第 @ROUND@ 轮的最后一笔产品提交是
@LASTSHA@ = 第 @LASTROUND@ 轮）。四件套现读（本轮重跑）：全量卷 @SWIFT@ / skip @SWSKIP@ / 失败 @SWFAIL@、
build 告警 @WARN@、帧 @FRAMES@ 张 compared=@CM@ changed=@CH@ missing=@MISS@、dmg=@Dmg@、换装 @VER@。
覆盖率现读：判据文件 @FILES@ 份、用文件通道 @EMIT@ 份、名册 @ROSTER@ 个、裸 stdout **@BARE@ 行 = 登记值**；
Swift 名字名册合计 @SWTOT@ 行、覆盖 @SWFILES@ 份文件。预检 tables=@TABLES@ arms=@ARMS@ bad=0、
R301 / R302 / R303 / R304 四张历史表本轮全 CAUGHT；电池 Ran @BATT@ / OK (skipped=@SKIP@)。

"""

ITER_NEW = u"""## Round @RDN@ · @RTAG@（第 @ROUND@ 轮 · @TODAY@）：第三批搬完、编号尺抬齐、看图腿回到 RUN

本轮做的事：把 360 的第三批 14 行裸 stdout 读数搬进 `CaptureReadings.emit`
（OffscreenSymbolInkProbeTests 4 / Round4MarkdownTests 4 / CapturePathWriteBudgetTests 3 / PerfBudgetTests 3），
登记值 29 → 现读 @BARE@、按文件名单 15 份 → 11 份 @UNCOV@ 行、派生名册 14 → @ROSTER@，
Swift 那张标记名册的通道表跟着加两个名字（这两份本来就在 8 个文件里，换了腿不加名字就是让名册去按 print 找已走 emit 的读数）。
363 结案：`test_ledger_ids.py` 七支三位假设一起抬成 `\\d{3,4}`，配四位正/反两向对照，位数只打读数。
这一格里 M884 第一次**打空**（把标题形对照尺改回三位，26 格全绿 ⇒ ESCAPED）—— 不是刀坏，是那两支对照尺
从没在四位样本上跑过（只在全是三位号的真台账上量过一遍）；补两条"对照尺也要认到 D-1000 / D-1001"之后才 CAUGHT。
本轮改了 6 份 Swift ⇒ 按 D-284 第二条重跑 R301 / R302 / R303 / R304 四张历史表 + 预检 bad=0。
重跑当场照出**五把坏刀**：两根针钉在 Swift `roster` 的头两行、被本轮的字母序插入挤走（NOT_RUN），
三根把棘轮旧值手抄进 needle 与期望正文（同一张表的说明里还写着第三个数 ⇒ WRONG_CELL）。
两根改钉尾行、三根改成从守卫文件现读登记值派生，本轮自己的 M882 也一并改成派生（它原本写死「16 行」）。
⓪ 交账：@SHA@ 那一跑（@RUN@，@CONC@）的 STEP「Motion coverage floor」现读 @SUITELINE@ ⇒ 354 第三步的 runner 证人到了，
答案是「本机登记的 @MINEN@ 条这一跑没露面」而不是预期的 `REGISTERED_REDS=2`（上一跑 39833209888 同格也是 CLEAN=0）。
两条登记的理由自己写着出现率 1/17 与 1/7 ⇒ 两跑没红**不配退场**，配的是问另一件事：门在「没露面」那一支直接 return，
缺席连一行都不打（arms 那侧有 `MOTION_FLOOR_STALE`，`suite_reds` 这侧没有）⇒ 转成 354 的第四步（U-@UD@）。
看图腿：重捕 @FRAMES@ 张帧并对账（changed=@CH@），@EYE_SHORT@

七维度自评：
| 维度 | 分/满分 |
| --- | --- |
@ROWS@| 合计 | @TOTAL@/105 |

为什么不是满分（逐条）：真实视觉审查 12 —— 本轮真的重捕并逐张看了（不是沿用上轮），但 0 个产品文件 ⇒ 没有新画面形状可判；
判据有效性 14 —— 三把刀各打一处同步点，其中 M884 打在编号尺自己身上；假绿防御 14 —— 通道表漏一个名字会红、
空清单冒充扫过了也会红，而 M884 第一次 ESCAPED 时被读成"判据缺一根轴"（对照尺从没见过四位号），补轴之后才 3/3 ⇒
没把打空的刀改成"这刀不重要"；产品面推进 4 —— 0 个产品文件、连续 @STREAK@ 轮（欠的是 347 的真机证人）；
台账一致性 14 —— 编号越界前把 D / 条目号两支也抬齐，历史三张表重跑；交付诚实性 14 —— ⓪ 按 push 的 tip 现读、
登记的证人写明"这跑没红不替登记作证"；可复核性 14 —— 所有数从卷自己打印的行取，抓不到就拒绝写盘。

派生分由 `curve_from_ledger.py` 现读，不手抄。
未做（逐条）：① 354 的第四步（登记的退场通道：本机登记的名字没露面时，门要能打点而不是直接 return）；② **305 的台阶地板**（等 347）；
③ 361 合并成一处派生；④ 360 剩下的 11 份 @BARE@ 行；⑤ 359 汇聚点；⑥ 348 的「数字对不对」；
⑦ 用户闸门 220 路 A / 228② / 265。

"""

DEC_NEW = u"""**D-287（@RTAG@）：台账编号的正则一律写成"能容纳越界"的宽度，位数只当读数；跨界之后仍然判形状的，是"最新一节要完整对上"这一类判据。**
理由与两次实测：R305 把 `U_DEF` / `U_RANGE` 从 `\\d{3}` 抬成 `\\d{3,4}` 时写了一格「现读最大仍是三位」的断言，
本轮 U-1000 落盘当天它就红；同一族洞在 D 号与 BACKLOG 条目号上还在（本轮一并抬宽并配四位正/反对照）。
所以规矩定成两句：① 宽度写 `\\d{3,4}`（不是 `\\d+`：那会让 `U-7`、`D-12` 这类**引用式写法**混进定义行计数，
而 `test_ui_round_interval_parity` 用的正是 `\\d+` —— 两种约定在本仓库并存，抬宽时选哪一种要写在这里，别混着改）；
② 任何"还没越界"的断言都不许存在，改成**跨界成立**判据（最新一节被两支尺认到、区间与定义吻合），位数 `print` 成读数。
"""

NOTE_360 = u"""  追记（@RTAG@ 第三批）：又搬 14 行（OffscreenSymbolInkProbeTests 4 / Round4MarkdownTests 4 /
  CapturePathWriteBudgetTests 3 / PerfBudgetTests 3），棘轮 29 → 现读 @BARE@，派生名册 14 → @ROSTER@，
  按文件的未覆盖名单从 15 份退到 11 份。本轮多一处同步点：**两份被搬的文件本来就在 Swift 那张标记名册的
  8 个文件里**（`INK*` 与 `PERF*` 是登记过名字的读数），所以通道表必须同时加名字 —— 只加 python 侧那张
  会留下"按 print 去找已经走 emit 的读数"的空清单（M883 钉的就是这一格）。
  剩下的 11 份 @BARE@ 行里最大的是 `WindowChromeLayoutTests` 3 行；本单继续开着直到清零。
"""

NOTE_363 = u"""  追记（@RTAG@ 结案）：两处三位假设都抬成 `\\d{3,4}` 并各自配了四位正对照（决定号：合成 `D-1000` / `D-1001`
  两种形状都要被 `DEC_DEF` 认到，且**摊平两个捕获组再比** —— 我第一版按单组心算期望，红在自己的期望值上；
  条目号：`**1000. ` 与 `1001. ` 两形分开认，并断言两形不相交）。位数改成一行读数（`D_ID_BOUNDARY`），
  不做"还没越界"的断言 —— R305 那一格在越界当天红过一次，形状与此完全同构。
  约定也定下来了（D-287）：抬宽一律用 `\\d{3,4}` 而不是 `\\d+`，因为 `\\d+` 会把 `U-7` / `D-12` 这种引用式写法
  数进定义行；`test_ui_round_interval_parity` 用 `\\d+` 是它自己那份"按形状分箱"的口径，不混着改。
  结案路上还有一处真洞是刀找出来的：M884 第一版把标题形那支**对照尺**改回三位，26 格全绿（ESCAPED）⇒
  说明对照尺从没在四位样本上跑过，它只在全是三位号的真台账上量过一遍。补了"标题形对照要认到 D-1000 /
  粗体形对照要认到 D-1001"两条断言，M884 才 CAUGHT 在该点名的格子。所以这一单的验收形状是：
  **并集尺与两支对照尺都要各自见过四位号**，只测并集等于没测那两支对照。
"""

NOTE_354 = u"""  追记（@RTAG@ 第三步交账 ⇒ 新开第四步）：证人到了，读的是 run @RUN@（sha @SHA@，@CONC@）自己打印的那一行 ——
  @SUITELINE@。也就是本机（@MACHINE@）登记的 @MINEN@ 条（@MINENAMES@）**这一跑没露面**，上一跑 39833209888 同一格也是 CLEAN=0。
  两种处置都不许做：① 不许据此删登记 —— 本单①的理由自己写着出现率 1/17 与 1/7，一跑没红本来就在预期之内（D-251：
  单遍读数既不配给产品定罪，也不配替产品脱罪）；② 更不许把「门没红」读成「门在看这件事」—— `suite_verdicts`
  在 `not named and summary == 0` 那一支直接 `return`，它连"本机登记的名字这一跑没露面"这一行都不打，
  于是这张表可以无限期留着慢慢变成免检牌堆（arms 那一侧早有 `MOTION_FLOOR_STALE` 专治这一格，`suite_reds` 这一侧没有对应物）。
  ⇒ **第四步**：缺席要能被打点 —— 本机登记的名字这一跑没露面时门必须发声，并配一把刀钉住「没露面 ⇒ 有声音」；
  「连续几跑没红才算退场」还是「要作者显式删」是下一步的事，先让它响再谈阈值（R39 那一族的教训是：恒红的守卫会被删，
  所以这一格只在"登记存在且这一跑没露面"时响，登记为空时不许响）。
"""

CHG_NEW = (u"### Improved（@RTAG@ / 第 @ROUND@ 轮 / Round @RDN@ · 第三批读数进文件通道 + 编号尺抬齐）\n\n"
           u"四份判据卷共 14 行裸 stdout 读数改走 `CaptureReadings.emit`，裸 stdout 棘轮 29 → 现读 @BARE@"
           u"（登记值同源改下来，两向各有刀），派生名册 14 → @ROSTER@；Swift 那张标记名册的显式通道表补两个名字 —— "
           u"这两份文件本来就在被登记的 8 个文件里，读数换了腿而不加通道，名册就会按 print 去找已经不存在的形状。"
           u"三把刀 M882 / M883 / M884 分别钉登记值、通道表、编号尺，@KC@/@K@ CAUGHT、RESTORE_CLEAN=@KREST@；"
           u"因为改了 6 份 Swift，按 D-284 第二条重跑 R301 / R302 / R303 / R304 四张历史表全部 CAUGHT、预检 bad=0。"
           u"363 结案：`test_ledger_ids.py` 七支三位正则抬成 `\\d{3,4}` 并配四位正/反对照，"
           u"位数只打成读数（D-287 定了宽度约定：不用 `\\d+`，那会把引用式写法数进定义行）。"
           u"354 第三步交账：runner 那一跑（@RUN@ / @SHA@）现读 @SUITELINE@ ⇒ 本机登记的 @MINEN@ 条没露面，"
           u"而门在「没露面」那一支直接 return、连一行都不打 ⇒ 转成第四步（缺席要能被打点），不据此删登记。"
           u"看图腿 RUN：重捕 @FRAMES@ 张帧、changed=@CH@。@EYE_SHORT@\n\n")

STATE_NEW = u"""## @RTAG@ 状态（第 @ROUND@ 轮 / Round @RDN@ · @TODAY@）

⓪ 读 CI（@RNEXT@ 的开场取数，只登记不轮询 = R140，成对号只列每次 push 的 tip = 362）：@CI_LINE@
已交账（@SHA@ / run @RUN@ / @CONC@）：STEP「Motion coverage floor」现读 @SUITELINE@
⇒ @PREV@ 那两处登记的证人**到了**，但答案是「这一跑没露面」而不是预期的 `REGISTERED_REDS=2`
（上一跑 39833209888 同一格也是 CLEAN=0 ⇒ 连续两跑）。登记的理由自己写着出现率 1/17 与 1/7，
所以两跑没红不配把登记删掉，配的是一句更难看的话：**门在「没露面」这一支直接 return，缺席连一行都不打**
⇒ 354 的第三步按这个读数改判，欠的变成第四步（见 U-@UD@）。
下一跑要验的两件事：① STEP[18] 在名册翻回 can 之后是否不再红（@PREV@ 已复验一次，红名回来要说清是哪一条）；
② 本轮新搬的四份卷（`INK*` / `COLOR_PROBE` / `MARKDOWN_PERF` / `CAPTURE_PATH_*` / `PERF*`）
在 runner 上是否仍在文件通道里落得下来（`READINGS_ROSTER derived=@ROSTER@ declared=@ROSTER@`）。

最后更新：@TODAY@（本地 · @RTAG@ / 第 @ROUND@ 轮 / Round @RDN@）：**360 的第三批搬完 + 363 结案 + 看图腿回到 RUN + 354 的 runner 证人交账** ——
14 行改走 `CaptureReadings.emit`，棘轮 29 → 现读 @BARE@（登记值与盘上相等），派生名册 14 → @ROSTER@，
Swift 标记名册的通道表 +2（M883 钉「从通道表删名字」）；`test_ledger_ids.py` 七支三位假设抬成 `\\d{3,4}`
并配四位正/反对照，位数只打读数 ⇒ D-287 定下宽度约定。本轮 0 个产品文件但**真的重捕并看了帧**
（@FRAMES@ 张、compared=@CM@、changed=@CH@）。
四件套现读：全量卷 @SWIFT@ / skip @SWSKIP@ / 失败 @SWFAIL@、告警 @WARN@、帧 changed=@CH@ missing=@MISS@、
dmg=@Dmg@、换装 @VER@；预检 tables=@TABLES@ arms=@ARMS@ bad=0；R301…R304 四张历史表全 CAUGHT（先修掉五把坏刀）；
电池 Ran @BATT@ / OK (skipped=@SKIP@)；`product_streak --check` 绿；`LEDGER_TOKENS stray=0`。
产品文件 0 个，连续零改动 **@STREAK@** 轮（现读 `python3 scripts/product_streak.py --streak-for @ROUND@`：
as-of 第 @ROUND@ 轮的最后一笔产品提交是 @LASTSHA@ = 第 @LASTROUND@ 轮）。

① 下一轮（@RNEXT@）的靶：① **354 的第四步** —— 给 `suite_reds` 补一条退场判据：本机登记的名字这一跑没露面时，
门要能打点（arms 那侧的 `MOTION_FLOOR_STALE` 是现成的形状），并配一把刀钉住「没露面 ⇒ 有声音」；
② 把 ⓪ 那两件事交账（STEP[18] 与 `READINGS_ROSTER`）；③ 360 的最后一批（从 `WindowChromeLayoutTests` 3 行起，
11 份 @BARE@ 行清零）；④ 361 的合并（同步点数量已能现读，合并成一处上游数据还没做）。
产品面：347 / 305 仍挡在用户那一边（要退出 App，或回答一句「收藏星按下够不够明显」）。

② 仍开：347（真机证人）、305（等 347）、354 的第四步（本机登记的缺席没有打点）、360（剩 11 份 @BARE@ 行）、361（同步点已数出，尚未合并）、
359（取证目录没有读数汇聚点）、362（⓪ 的成对号按 commit 列）、356（悬停换形状的三条候选）、
348 的「数字对不对」那一格、349、350 第二步、351、344、341 的 CI 契约半、339、312 具名出口、333、335、334、
310、338 的另一半、328、323、322、317、304、291。

③ 用户闸门：220 路 A / 228② / 265。

"""

SHORT_EYE = EYE.split(u"⇒")[0].strip()
texts = {k: fill(v) for k, v in {
    "UI": UI_NEW, "IT": ITER_NEW.replace(u"@EYE_SHORT@", SHORT_EYE),
    "DEC": DEC_NEW, "BL": NOTE_360, "NEWITEM": NOTE_363, "N354": NOTE_354,
    "CH": CHG_NEW.replace(u"@EYE_SHORT@", SHORT_EYE),
    "ST": STATE_NEW,
}.items()}

# ── 形状自测 ───────────────────────────────────────────────────────
ui_new = texts["UI"]
if u"（%s ·" % R_TAG not in ui_new.splitlines()[0]:
    die(u"标题缺 round_batch 要的前缀")
nums = [int(x) for x in re.findall(u"(?m)^- \\*\\*U-(\\d{3,4})：", ui_new)]
if nums != [UA, UB, UC, UD]:
    die(u"节内 U 定义行与标题区间不吻合：%s vs %s" % (nums, [UA, UB, UC, UD]))
if len(re.findall(u"(?m)^\\| .+ \\| \\d+/15 \\|$", texts["IT"])) != 7:
    die(u"七维格子不是 7 行 n/15")
if u"七维度自评：" not in texts["IT"]:
    die(u"ITERATION 缺锚点")
if u"@EYE_SHORT@" in texts["IT"] or u"@EYE_SHORT@" in texts["CH"]:
    die(u"看图腿那句短述没被替换")
if not re.search(u"^最后更新：\\d{4}-\\d{2}-\\d{2}（本地 · %s / 第 \\d+ 轮 / Round \\d+）" % R_TAG,
                 texts["ST"], re.M):
    die(u"STATE 缺「最后更新」行形状")
if len(re.findall(u"连续零改动 \\*\\*%s\\*\\* 轮" % STREAK_N, texts["ST"])) != 1:
    die(u"STATE 那一格形状不满足 353 的门")
NEW_U_DEFS = len(re.findall(u"(?m)^- \\*\\*U-\\d{3,4}[：(]", ui_new))
if NEW_U_DEFS != 4:
    die(u"本轮那一节的 U 定义行数=%d（要 4）" % NEW_U_DEFS)
if len(texts["UI"]) < 1500:
    die(u"本轮那一节短得不像一轮的账（%d 字符）" % len(texts["UI"]))

orig = {k: rd(v) for k, v in FILES.items()}
for key, probe in ((u"UI", u"## 第 %d 轮" % ROUND), (u"IT", u"## Round %d ·" % RD_N),
                   (u"DEC", u"**D-%d（" % DN), (u"BL", u"**%d. " % BLO),
                   (u"ST", u"## %s 状态（" % R_TAG), (u"CH", u"%s / 第 %d 轮" % (R_TAG, ROUND))):
    if probe in orig[key]:
        die(u"%s 已有本轮那一格（%s）⇒ 生成器不许重复落" % (key, probe))
if orig[u"UI"].count(u"## 第 %d 轮" % (ROUND - 1)) != 1:
    die(u"UI_AUDIT 锚点不符（第 %d 轮标题不唯一）" % (ROUND - 1))
if orig[u"ST"].count(u"## %s 状态（" % PREV_TAG) != 1:
    die(u"STATE 锚点不符（%s 节不唯一）" % PREV_TAG)
if orig[u"CH"].count(u"## [Unreleased]\n\n") != 1:
    die(u"CHANGELOG 锚点不符")


def append_note_to_item(text, item, note):
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


def bullet(text, label):
    m = re.search(u"(?m)^- \\*\\*%s" % re.escape(label), text)
    if not m:
        die(u"报告里找不到 bullet「%s」⇒ 形状漂了" % label)
    nxt = re.search(u"(?m)^(- \\*\\*|## |\\Z)", text[m.end():])
    return m.start(), m.end() + (nxt.start() if nxt else len(text))


FR_WALK = (u"- **走到哪了**：阶段二累计 `## Round` 节 **@SECTIONS@** 节，最新一节是 **Round @RDN@**；"
           u"自评曲线末四个 @TAIL@ · @RDN@=@TOTAL@（现读 `curve_from_ledger.py`）。"
           u"派生分连续多轮低于 90 ⇒ 按目标继续修，不收口。\n")
FR_DOOR = (u"- **判据与门的规模**：脚本电池现读 **Ran @BATT@**（写盘后同数），变异臂抽到 **@ARMS@** 把"
           u"（预检 tables=@TABLES@、bad=0）；U 定义行 **@UDEF@ 条**、最大 **U-@UD@**；"
           u"决定台账最大 **D-@DN@**，BACKLOG 最大 **@BLO@**。"
           u"读数通道的数：判据文件 @FILES@ 份里 @EMIT@ 份走文件通道、名册 @ROSTER@ 个、"
           u"仍在裸 stdout 的读数 **@BARE@ 行**（= 登记值；第三批之前是 29）；"
           u"占位符扫描 @TOKB@ 本 @TOKC@ 字符 stray=0。\n")
FR_PRODUCT = (u"- **产品面（这一节最该被读的部分）**：本轮产品文件 0 个，"
              u"产品面连续零改动轮数 = **@STREAK@**（唯一取数口 `python3 scripts/product_streak.py --streak-for @ROUND@`，"
              u"as-of 第 @ROUND@ 轮的最后一笔产品提交是 @LASTSHA@ = 第 @LASTROUND@ 轮）。"
              u"看图腿 RUN：重捕 @FRAMES@ 张帧对账 changed=@CH@。@EYE_SHORT@\n")

SUBS2 = dict(SUBS)
NEW_U_DEFS_2 = NEW_U_DEFS
SUBS2[u"@UDEF@"] = s(U_DEFS + NEW_U_DEFS_2)
SUBS2[u"@EYE_SHORT@"] = SHORT_EYE
fr = orig["FR"]
repl = []
for label, tpl in ((u"走到哪了", FR_WALK), (u"判据与门的规模", FR_DOOR),
                   (u"产品面（这一节最该被读的部分）", FR_PRODUCT)):
    a, b = bullet(fr, label)
    repl.append((a, b, fill_tpl(tpl, SUBS2)))
a, b = bullet(fr, u"仍开（截至本轮，完整名单以 `AGENT_STATE.md` 的 %s 节 ② 为准）" % PREV_TAG)
fr_still = fr[a:b]
fr_still = fr_still.replace(u"354 的第三步（负载下的调度地板读数；第二步本轮已落地：登记按机器切片）",
                            u"354 的第四步（证人到了：本机登记的 @MINEN@ 条在连续两跑里都没露面，而门在「没露面」那一支直接 return ⇒ 缺席没有打点）")
if u"354 的第四步" not in fr_still:
    die(u"§13 的仍开 bullet 里 354 那一格没被本轮更新 ⇒ 报告又把已交账的第三步当欠账写着")
fr_still = fr_still.replace(u"360（已搬两批，剩 @NAMED@ 份文件 @BARE@ 行）", u"360（已搬三批，剩 11 份 %s 行）" % ck[u"bare_print_lines"])
fr_still = fr_still.replace(u"360（已搬两批", u"360（已搬三批，剩 11 份 %s 行" % ck[u"bare_print_lines"]) if u"360（已搬两批" in fr_still else fr_still
fr_still = re.sub(u"%s 节 ②" % PREV_TAG, u"%s 节 ②" % R_TAG, fr_still)
if u"%s 节 ②" % R_TAG not in fr_still:
    die(u"§13 的仍开 bullet 没指向本轮的 STATE 节 ⇒ 指针过期")
if u"360（已搬三批" not in fr_still:
    die(u"§13 的仍开 bullet 没落到本轮的形状（360 的批次数没更新）")
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
    "BL": append_note_to_item(append_note_to_item(orig["BL"], 360, texts["BL"]),
                              354, texts["N354"]).rstrip(u"\n") + u"\n\n"
          + texts["NEWITEM"].strip(u"\n") + u"\n",
    "ST": orig["ST"].replace(u"## %s 状态（" % PREV_TAG, texts["ST"] + u"## %s 状态（" % PREV_TAG, 1),
    "CH": orig["CH"].replace(u"## [Unreleased]\n\n", u"## [Unreleased]\n\n" + texts["CH"], 1),
    "FR": fr_new,
}
for key in new:
    if key != u"FR" and len(new[key]) <= len(orig[key]):
        die(u"%s 写后不比写前长 ⇒ 可能是替换而不是插入" % key)
if u"追记（%s 第三批）" % R_TAG not in new["BL"]:
    die(u"360 的追记没落进去")
if u"追记（%s 结案）" % R_TAG not in new["BL"]:
    die(u"363 的结案追记没落进去")
if u"追记（%s 第三步交账" % R_TAG not in new["BL"]:
    die(u"354 的交账追记没落进去")
i354 = new["BL"].find(u"**354. ")
i355 = new["BL"].find(u"**355. ")
if not (0 <= i354 < new["BL"].find(u"第三步交账") < i355):
    die(u"354 的追记落在了 354 那一节之外（354=%d 追记=%d 355=%d）⇒ 会挂到别人的条目上"
        % (i354, new["BL"].find(u"第三步交账"), i355))
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

sh([sys.executable, REFRESH])
post, err = battery(u"写盘后", u"/tmp/r306_battery_post.log")
if post is None:
    for key, text in orig.items():
        wr(FILES[key], text)
    die(u"写盘后电池不绿 ⇒ 七本已整体还原：" + err)
if post != pre:
    for key, text in orig.items():
        wr(FILES[key], text)
    die(u"电池计数变了（" + str(pre) + u" → " + str(post) + u"）⇒ 七本已还原")

cout2, crc2 = sh([sys.executable, STREAK, u"--check"])
if crc2 != 0:
    for key, text in orig.items():
        wr(FILES[key], text)
    die(u"353 的门不认这版台账 ⇒ 七本已还原：" + (cout2 + u"\n").strip()[-400:])

cv2, _ = sh([sys.executable, CURVE])
byround2 = (re.findall(u"(?m)^SCORES_BY_ROUND (.*)$", cv2, re.M) or [u""])[-1]
score = dict(re.findall(u"(\\d{3})=(\\d{2,3})", byround2)).get(s(RD_N), u"?")
if score == u"?":
    die(u"曲线里没有 Round %d 的分数 ⇒ ITERATION 那一节没落地" % RD_N)
gaps = (re.findall(r"^GAPS=(\S+)", cv2, re.M) or [u"?"])[-1]
print(u"LEDGERS_R306 OK batt=Ran " + post[0] + u" (skipped=" + post[1] + u") streak=" + STREAK_N
      + u" prod=0 bare=" + ck[u"bare_print_lines"] + u"/" + ck[u"ceiling"] + u" roster=" + ck[u"roster"]
      + u" swift=" + vk[u"swift_executed"] + u"/" + vk[u"swift_failures"] + u" frames=" + vk[u"frames"]
      + u" knives=" + kk[u"CAUGHT"] + u"/" + kk[u"刀"] + u" U=" + s(UA) + u".." + s(UD)
      + u" D=" + s(DN) + u" derived_score(Round " + s(RD_N) + u")=" + s(score) + u" GAPS=" + gaps)

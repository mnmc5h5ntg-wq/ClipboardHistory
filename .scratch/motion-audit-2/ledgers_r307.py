#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R307 的台账生成器（第 306 轮 / Round 304）：354 第四步 —— 缺席要能被打点。

本轮只动 scripts（`motion_floor_gate.py` 的退场判据 + 它的判据卷 + 一张新刀表）：
产品 0 文件、Swift 0 文件 ⇒ 四件套里 Swift 那三条腿**没有新对象**，按 D-236 沿用上轮读数并写明理由，
而"沿用上轮的帧"这一格要先 `ls` 数出帧还在盘上（R140：/tmp 会被 macOS 清掉），数不到就记 NOT-RUN。

数一律现读：刀表、预检、历史表 r305、门那一卷、占位符扫描、曲线、电池、product_streak、git 的改动面。
写盘前后各一次电池且要求同数；写盘前自扫未替换占位符；任何一格读不到就整体不写。
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
TOKEN_ROLL = os.path.join("scripts", "tests", "test_ledger_tokens.py")
GATE_ROLL = os.path.join("scripts", "tests", "test_motion_floor_gate.py")
KNIVES = os.path.join(ROOT, ".scratch", "motion-audit-2", "mutate_r307.py")
HIST = [("R305", os.path.join(ROOT, ".scratch", "motion-audit-2", "mutate_r305.py"))]
REFRESH = os.path.join(ROOT, ".scratch", "motion-audit-2", "refresh_report_section1.py")
CI_READ = os.path.join(ROOT, "scripts", "ci_read.py")
FRAME_DIR = "/tmp/r306_verify/frames"
R_TAG, PREV_TAG, R_NEXT = u"R307", u"R306", u"R308"
TODAY = subprocess.check_output([u"date", u"+%Y-%m-%d"]).decode().strip()
EYE = os.environ.get("R307_EYE", u"")

DIMS = [u"真实视觉审查", u"判据有效性", u"假绿防御", u"产品面推进", u"台账一致性",
        u"交付诚实性", u"可复核性"]
SCORES = [6, 15, 15, 4, 14, 14, 13]


def s(x):
    return str(x)


def die(msg):
    sys.stderr.write(u"LEDGERS_R307 REFUSED: " + msg + u"\n")
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
if not EYE.strip():
    die(u"本轮要看图腿：R307_EYE 没传 ⇒ 不许把真实视觉审查写成省略（哪怕是零产品改动的轮次）")

# 本轮改动面：产品与 Swift 必须真的是 0（不许把"没跑"说成"没有对象"）
dout, drc = sh([u"git", u"diff", u"--name-only", u"HEAD", u"--"])
staged, src_rc = sh([u"git", u"diff", u"--name-only", u"--cached", u"--"])
changed = sorted(set(dout.splitlines()) | set(staged.splitlines()))
PROD = [f for f in changed if f.startswith(u"ClipboardHistory/Sources/")]
SWIFT = [f for f in changed if f.endswith(u".swift")]
if drc != 0 or src_rc != 0:
    die(u"读不到本轮改动面（rc=%s/%s）⇒ 产品文件数不许靠记忆写" % (drc, src_rc))
if PROD or SWIFT:
    die(u"生成器以为本轮是纯脚本轮，但改动面里有 Swift/产品文件：%s ⇒ 四件套与帧腿要按 Swift 轮重跑"
        % (PROD + SWIFT)[:6])

on_disk = len([n for n in os.listdir(FRAME_DIR) if n.endswith(u".png")]) if os.path.isdir(FRAME_DIR) else 0
FRAMES_ON_DISK = s(on_disk)
EYE_LEG = u"RUN" if on_disk > 0 else u"NOT-RUN"

# ⓪ 成对号：只登记不轮询；那一跑未落结论时**照实写未读**（R140），不许因此拒绝落账
lout, lrc = sh([sys.executable, CI_READ, u"latest"])
pair = re.findall(u"(?m)^RUN=(\\d+) sha=(\\w+) status=(\\w+) conclusion=(\\S*)", lout)
if lrc != 0 or not pair:
    die(u"⓪ 的成对号读不到（rc=%s）：%s" % (lrc, lout.strip()[-200:]))
RUN_ID, TIP_SHA, TIP_STATUS, TIP_CONC = pair[-1]
hout, hrc = sh([u"git", u"rev-parse", u"--short", u"HEAD"])
if hrc != 0 or hout.strip() != TIP_SHA:
    die(u"⓪ 的 sha（%s）与本地 HEAD（%s）不符 ⇒ 有别的东西先落了一笔" % (TIP_SHA, hout.strip()))
CI_STATE = (u"%s ↔ %s（%s%s）" % (TIP_SHA, RUN_ID, TIP_STATUS,
                                 u"" if TIP_STATUS == u"completed" else u"，结论未读"))

dk, d2 = sh([sys.executable, STREAK])
dk = summary(dk, u"PRODUCT_STREAK", d2, [u"ledger_round", u"streak"])
ROUND = int(dk[u"ledger_round"]) + 1
fout, frc = sh([sys.executable, STREAK, u"--streak-for", s(ROUND)])
fk = summary(fout, u"PRODUCT_STREAK_FOR", frc, [u"streak", u"last", u"last_round"])
STREAK_N, LAST_SHA, LAST_ROUND = fk[u"streak"], fk[u"last"], fk[u"last_round"]
if STREAK_N != s(ROUND - int(LAST_ROUND)):
    die(u"as-of 第 %d 轮：streak=%s 而 ROUND−LAST_ROUND=%s ⇒ 两边不同源" % (ROUND, STREAK_N, s(ROUND - int(LAST_ROUND))))

kout, krc = sh([sys.executable, u"-W", u"ignore", KNIVES])
kk = summary(kout, u"R307_MUTATE", krc, [u"刀", u"CAUGHT", u"ESCAPED", u"NOT_RUN", u"RESTORE_CLEAN"])
if kk[u"CAUGHT"] != kk[u"刀"] or kk[u"ESCAPED"] != u"0" or kk[u"NOT_RUN"] != u"0" or kk[u"RESTORE_CLEAN"] != u"yes":
    die(u"本轮刀表不干净：%s" % kout.strip()[-400:])
for tag, path in HIST:
    hout2, hrc2 = sh([sys.executable, u"-W", u"ignore", path])
    hk = summary(hout2, u"%s_MUTATE" % tag, hrc2, [u"CAUGHT", u"刀", u"NOT_RUN", u"RESTORE_CLEAN"])
    if hk[u"CAUGHT"] != hk[u"刀"] or hk[u"NOT_RUN"] != u"0" or hk[u"RESTORE_CLEAN"] != u"yes":
        die(u"历史刀表 %s 不干净（本轮改了它 needle 住的文件？）：%s" % (tag, hout2.strip()[-400:]))
    print(u"HIST %s %s" % (tag, hk))

pout, prc = sh([sys.executable, PRECHECK])
at = re.findall(r"^ARM_TOTAL files=(\d+) arms=(\d+) dupes=(\d+) repeats=(\d+)", pout, re.M)
np_ = re.findall(r"^NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=(\d+) bad=(\d+)", pout, re.M)
if prc != 0 or not at or not np_ or at[-1][2] != u"0" or at[-1][3] != u"0" or np_[-1][3] != u"0":
    die(u"预检不干净：%s" % pout.strip()[-300:])
ARMS, BAD, TABLES, COVERED = at[-1][1], np_[-1][3], np_[-1][0], np_[-1][1]

gout, grc = sh([sys.executable, u"-W", u"ignore", u"-m", u"unittest", u"-v", GATE_ROLL])
gr = (re.findall(u"(?m)^Ran (\\d+) tests", gout) or [u"?"])[-1]
rec = (re.findall(u"(?m)^SUITE_RED_RECURRENCE (.*)$", gout) or [u"没打印"])[-1]
if grc != 0 or rec == u"没打印":
    die(u"门那一卷不绿或没打退场读数：%s" % gout.strip()[-300:])

tout, trc = sh([sys.executable, u"-W", u"ignore", u"-m", u"unittest", u"-v", TOKEN_ROLL])
tk = summary(tout, u"LEDGER_TOKENS", trc, [u"books", u"chars", u"stray"])
if tk[u"stray"] != u"0":
    die(u"台账里有未替换占位符：%s" % tk)

ui = rd(FILES["UI"])
U_MAX = max(int(x) for x in re.findall(u"(?m)^- \\*\\*U-(\\d{3,4})", ui))
D_MAX = max(int(x) for x in re.findall(u"(?m)^(?:#{2,3} D-|\\*\\*D-)(\\d{3,4})", rd(FILES["DEC"])))
BL_MAX = max(int(x) for x in re.findall(u"(?m)^\\*\\*(\\d{3,4})\\. ", rd(FILES["BL"])))
if (U_MAX, D_MAX, BL_MAX) != (1006, 287, 363):
    die(u"最大编号与本轮取靶时不符（U-%d / D-%d / BACKLOG-%d）⇒ 有别的会话先动了账" % (U_MAX, D_MAX, BL_MAX))
UA, UB, UC = U_MAX + 1, U_MAX + 2, U_MAX + 3
DN = D_MAX + 1

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

pre, err = battery(u"写盘前", u"/tmp/r307_battery_pre.log")
if pre is None:
    die(err)
TOTAL = sum(SCORES)
ROWS = u"\n".join(u"| %s | %d/15 |" % (d, sc) for d, sc in zip(DIMS, SCORES))

SUBS = {
    u"@RTAG@": R_TAG, u"@PREV@": PREV_TAG, u"@RNEXT@": R_NEXT,
    u"@ROUND@": s(ROUND), u"@RDN@": s(RD_N), u"@TODAY@": TODAY,
    u"@UA@": s(UA), u"@UB@": s(UB), u"@UC@": s(UC), u"@DN@": s(DN), u"@BLO@": s(BL_MAX),
    u"@STREAK@": STREAK_N, u"@LASTSHA@": LAST_SHA, u"@LASTROUND@": LAST_ROUND,
    u"@ROWS@": ROWS + u"\n", u"@TOTAL@": s(TOTAL),
    u"@BATT@": pre[0], u"@SKIP@": pre[1],
    u"@ARMS@": ARMS, u"@TABLES@": TABLES, u"@COVERED@": COVERED,
    u"@K@": kk[u"刀"], u"@KC@": kk[u"CAUGHT"], u"@KREST@": kk[u"RESTORE_CLEAN"],
    u"@SECTIONS@": s(int(SECTIONS) + 1), u"@TAIL@": TAIL_OLD, u"@CI@": CI_STATE,
    u"@EYE@": EYE, u"@PNGS@": FRAMES_ON_DISK, u"@EYELEG@": EYE_LEG,
    u"@GRAN@": gr, u"@REC@": rec, u"@NPROD@": s(len(PROD)), u"@NSWIFT@": s(len(SWIFT)),
    u"@TOKB@": tk[u"books"], u"@TOKC@": tk[u"chars"],
}
EYE = fill_tpl(EYE, SUBS)
SUBS[u"@EYE@"] = EYE
SHORT_EYE = EYE.split(u"⇒")[0].strip()
SUBS[u"@EYE_SHORT@"] = SHORT_EYE


def fill(t):
    return fill_tpl(t, SUBS)


UI_NEW = u"""## 第 @ROUND@ 轮（@RTAG@ · U-@UA@…U-@UC@ · @TODAY@）：登记缺席要被打点 —— 退场判据从两份实现收成一份（U-@UA@…U-@UC@ · 产品 @NPROD@ 文件，判据账）

- **U-@UA@：354 第四步 —— 全卷干净那一支以前直接 return，于是"本机登记的名字没露面"连一行都不打。**
  现读证人（@PREV@ 那格交来的）：run 39837096189 与 39833209888 两跑都打 `MOTION_FLOOR_SUITE_CLEAN=0｜机器=github-runner`，
  而 `suite_reds` 里为它登记着两条 ⇒ 那两跑里门对这两条**一字未提**。修法是把它收成一份实现：
  新增 `retirement_verdicts(mine, named, machine)`，干净那支与红那支**都**走它。
  为什么"两份实现"本身就是缺陷：旧代码在红路上有一段 per-name 的 `MOTION_FLOOR_SUITE_STALE`（不红），
  而它恰好挂在"这卷还有别的红"那条路上 —— 全卷干净（正是登记最该被质疑的时刻）永远轮不到它响。
  这一格由 `test_there_is_exactly_one_retirement_implementation` 钉住：数**次数**而不是数"有没有提到"
  （键出现 1 次、`retirement_verdicts(` 出现 3 次 = def + 两条调用）。
- **U-@UB@：退场分三档，且"没写档位"要红 —— 默认值等于替作者选一个永远不会响的方向。**
  `always` 缺席 ⇒ **红**（写着每次都红却没露面 = 过期，逼退场）；`sampled` 缺席 ⇒ **点名不红**
  （这两条登记的理由自己写着出现率 1/17、1/7，一跑没抽中不配退场；做成红就得到一把恒红的守卫，
  而 R39 的教训是恒红的守卫最后被人删掉）；没写 `recurrence` ⇒ **红**。
  现读名册：`SUITE_RED_RECURRENCE @REC@`。两条既有登记都补成 `sampled`，reason 里的出现率被
  `test_the_live_registrations_declare_a_recurrence_backed_by_a_rate` 要求成 `n/m` 形状（不许只说"偶尔"）。
- **U-@UC@：看图腿 @EYELEG@ —— 本轮 0 份 Swift、@NPROD@ 个产品文件 ⇒ 没有新画面形状可判。**
  @EYE@

本轮改动面现读（`git diff --name-only`）：产品 @NPROD@ 份、Swift @NSWIFT@ 份 ⇒ 四件套的 Swift 三条腿
**没有新对象**，按 D-236 沿用上轮读数并写明理由（全量卷 @PREV@ 现读 933/44skip/0 失败、帧 changed=0、dmg=ok、换装 1.4.8），
不是"跑过"也不是"验过"。刀 @KC@/@K@ 全 CAUGHT、RESTORE_CLEAN=@KREST@；历史表 R305（钉着同一份 gate 文件）本轮全 CAUGHT；
预检 tables=@TABLES@ arms=@ARMS@ bad=0；门那一卷 Ran @GRAN@ 全绿；电池 Ran @BATT@ / OK (skipped=@SKIP@)。

"""

ITER_NEW = u"""## Round @RDN@ · @RTAG@（第 @ROUND@ 轮 · @TODAY@）：缺席打点与"一条规则一份实现"

本轮只动 scripts：把 `suite_reds` 的退场判据从"红路上有一份、干净路上没有"收成一份
`retirement_verdicts`，并分三档（always 缺席即红 / sampled 缺席只点名 / 没写 recurrence 红），
外加一格"登记为空时不许响"防恒红。刀 @K@ 把各钉一条轴（M885 降级红、M886 吃掉默认档、
M887 拿掉点名、M888 反过来造恒响），@KC@/@K@ CAUGHT；历史表 R305 重跑全 CAUGHT、预检 bad=0。
看图腿 @EYELEG@：@PNGS@ 张帧在盘上（本轮没有新帧，因为产品与夹具 0 改动）。@EYE_SHORT@

七维度自评：
| 维度 | 分/满分 |
| --- | --- |
@ROWS@| 合计 | @TOTAL@/105 |

为什么不是满分（逐条）：真实视觉审查 6 —— 本轮没有新画面对象，只复核了上轮看过的位点，看图腿按定义打折；
判据有效性 15 —— 四把刀各钉一条独立轴，含"不许恒响"这一条反向轴；假绿防御 15 —— "两份实现互相掩盖"被数次数钉住，
默认值不许替作者选档位；产品面推进 4 —— 0 个产品文件、连续 @STREAK@ 轮（欠的是 347 的真机证人）；
台账一致性 14 —— 报告计数器与仍开名单同步，历史表重跑；交付诚实性 14 —— Swift 三条腿写明"没有新对象"而不是"跑过"；
可复核性 13 —— ⓪ 那一跑若未落结论就照实写"未读"，退场读数由门自己打印。

派生分由 `curve_from_ledger.py` 现读，不手抄。
未做（逐条）：① 354 的第五步（sampled 那两条的**退场阈值**：连续几跑没红、还是要求作者显式删）；
② **305 的台阶地板**（等 347）；③ 361 合并成一处派生；④ 360 剩下的 11 份裸 stdout；⑤ 359 汇聚点；
⑥ 348 的「数字对不对」；⑦ 用户闸门 220 路 A / 228② / 265。

"""

DEC_NEW = u"""**D-288（@RTAG@）：一条规则只许一份实现；判据被"提前 return"吃掉的那一支，就是它最该响的那一支。**
理由与实测：`suite_verdicts` 的退场提示原本只长在"这一卷还有别的红"那条路上，而"全卷干净"那一支
在函数中段就 `return` —— 于是登记表可以无限期留着，而门在**登记最该被质疑的时刻**（整卷干净）永远不响。
R306 的 runner 证人（连两跑 `SUITE_CLEAN=0`）是这件事的第一份读数。
所以定两条：① 同一件事的多个出口必须汇到**同一个函数**，并由一格判据**数出现次数**
（`键 == 1`、`函数名( == def + 出口数`）—— 只扫"有没有提到"会放过第二份实现（R76/R77 那一族）；
② 给判据加"这台机器/这一跑判不了"的出口时，出口不许放在判据**之后** —— 放在之后就是把它自己吃掉。
"""

NOTE_354 = u"""  追记（@RTAG@ 第四步结案）：缺席现在会发声了。`suite_verdicts` 的两条路都走同一份
  `retirement_verdicts`：本机登记的名字这一跑没露面 ⇒ `always` 红（过期要退场）、`sampled` 点名不红
  （一跑没抽中不配退场，本单①的理由自己写着 1/17、1/7）、没写 `recurrence` 红（不许用默认值替作者选档位）。
  证人：R306 读到 runner 连两跑 `MOTION_FLOOR_SUITE_CLEAN=0｜机器=github-runner`，而旧代码对这两条一字未提 ——
  旧的那份 stale 实现挂在红路上，所以"全卷干净"这个最该质疑的时刻恰好是它永不响的那一支（D-288）。
  四把刀 M885…M888 各钉一条轴，含反向那条（登记为空时不许响 —— 恒红的守卫最后会被人删掉，R39）。
  剩下的第五步：`sampled` 的**退场阈值**还没定（连续几跑没红才算，还是要求作者显式删），
  这一步刻意不顺手定 —— 先让它响，再拿响过的次数当依据。
"""

CHG_NEW = (u"### Improved（@RTAG@ / 第 @ROUND@ 轮 / Round @RDN@ · 登记的缺席要被打点，退场判据收成一份实现）\n\n"
           u"`scripts/motion_floor_gate.py` 新增 `retirement_verdicts`，干净那支与红那支共用："
           u"本机登记的名字这一跑没露面时 `always` 红、`sampled` 点名、没写 `recurrence` 红，"
           u"登记为空时整段不响。起因是 @PREV@ 的 runner 证人（连两跑 `SUITE_CLEAN=0`）——"
           u"旧的退场提示只长在红路上，全卷干净那一支直接 return ⇒ 门恰好在登记最该被质疑的时刻不响（D-288）。"
           u"四把刀 M885…M888 各钉一条轴（含「不许恒响」这条反向轴），@KC@/@K@ CAUGHT、RESTORE_CLEAN=@KREST@；"
           u"历史表 R305 重跑全 CAUGHT、预检 bad=0、门那一卷 Ran @GRAN@ 全绿。"
           u"本轮产品 @NPROD@ 文件、Swift @NSWIFT@ 份 ⇒ Swift 三条腿没有新对象，按 D-236 沿用上轮读数并写明理由。"
           u"看图腿 @EYELEG@：@EYE_SHORT@\n\n")

STATE_NEW = u"""## @RTAG@ 状态（第 @ROUND@ 轮 / Round @RDN@ · @TODAY@）

⓪ 读 CI（@RNEXT@ 的开场取数，只登记不轮询 = R140，成对号只列每次 push 的 tip = 362）：@CI@
本轮新落的两笔 push 之后要验的两件事：① STEP「Motion coverage floor」在 runner 上是否打出
`MOTION_FLOOR_SUITE_NOT_SEEN=2`（这是第四步的第一份 runner 证人 —— 它证明"缺席会被点名"真的在响，
而不是只在本机夹具里响）；② STEP[18] 与 `READINGS_ROSTER` 那两格照旧（@PREV@ 已复验一次）。
若 runner 那一步反过来红在 `MOTION_FLOOR_SUITE_NO_RECURRENCE` ⇒ 说明它读到了没写档位的登记，
先查表而不是先怀疑门。

最后更新：@TODAY@（本地 · @RTAG@ / 第 @ROUND@ 轮 / Round @RDN@）：**354 第四步结案到「缺席会发声」这一层** ——
`suite_verdicts` 的两条路汇成一份 `retirement_verdicts`（always 缺席即红 / sampled 只点名 /
没写 recurrence 红 / 空表不响），D-288 把"一条规则一份实现 + 出口不许放在判据之后"定成规矩；
四把刀 M885…M888 全 CAUGHT、历史表 R305 重跑全 CAUGHT、预检 tables=@TABLES@ arms=@ARMS@ bad=0；
电池 Ran @BATT@ / OK (skipped=@SKIP@)；`product_streak --check` 绿；`LEDGER_TOKENS stray=0`。
本轮产品 @NPROD@ 文件、Swift @NSWIFT@ 份 ⇒ 四件套的 Swift 三条腿**没有新对象**，沿用上轮读数并写明理由
（不是"跑过"）；看图腿 @EYELEG@（@PNGS@ 张帧在盘上）。
产品文件 0 个，连续零改动 **@STREAK@** 轮（唯一取数口 `python3 scripts/product_streak.py --streak-for @ROUND@`，
同形用于 `--check`）。as-of 第 @ROUND@ 轮的最后一笔产品提交是 @LASTSHA@ = 第 @LASTROUND@ 轮。

① 下一轮（@RNEXT@）的靶：① 354 的第五步 —— `sampled` 的退场阈值要拿"响过的次数"当依据来定，
别再凭一次读数删登记；② 把 ⓪ 那两件事交账（尤其 `NOT_SEEN=2` 在 runner 上第一次响没响）；
③ 360 的最后一批（11 份裸 stdout 清零）；④ 361 的合并。
产品面：347 / 305 仍挡在用户那一边（要退出 App，或回答一句「收藏星按下够不够明显」）。

② 仍开：347（真机证人）、305（等 347）、354 的第五步（sampled 的退场阈值）、360（剩 11 行裸 stdout）、
361（同步点已数出，尚未合并）、359（取证目录没有读数汇聚点）、362（⓪ 的成对号按 commit 列）、
356（悬停换形状的三条候选）、348 的「数字对不对」那一格、349、350 第二步、351、344、341 的 CI 契约半、
339、312 具名出口、333、335、334、310、338 的另一半、328、323、322、317、304、291。

③ 用户闸门：220 路 A / 228② / 265。

"""

texts = {k: fill(v) for k, v in {
    "UI": UI_NEW, "IT": ITER_NEW, "DEC": DEC_NEW, "N354": NOTE_354,
    "CH": CHG_NEW, "ST": STATE_NEW,
}.items()}

# ── 形状自测 ───────────────────────────────────────────────────────
ui_new = texts["UI"]
if u"（%s ·" % R_TAG not in ui_new.splitlines()[0]:
    die(u"标题缺 round_batch 要的前缀")
nums = [int(x) for x in re.findall(u"(?m)^- \\*\\*U-(\\d{3,4})：", ui_new)]
if nums != [UA, UB, UC]:
    die(u"节内 U 定义行与标题区间不吻合：%s vs %s" % (nums, [UA, UB, UC]))
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

orig = {k: rd(v) for k, v in FILES.items()}
for key, probe in ((u"UI", u"## 第 %d 轮" % ROUND), (u"IT", u"## Round %d ·" % RD_N),
                   (u"DEC", u"**D-%d（" % DN), (u"ST", u"## %s 状态（" % R_TAG),
                   (u"CH", u"%s / 第 %d 轮" % (R_TAG, ROUND))):
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
           u"（预检 tables=@TABLES@、bad=0）；U 定义行 **@UDEF@ 条**、最大 **U-@UC@**；"
           u"决定台账最大 **D-@DN@**，BACKLOG 最大 **@BLO@**。"
           u"本轮新落的退场判据现读：`SUITE_RED_RECURRENCE @REC@`。\n")
FR_PRODUCT = (u"- **产品面（这一节最该被读的部分）**：本轮产品文件 @NPROD@ 个、Swift @NSWIFT@ 份，"
              u"产品面连续零改动轮数 = **@STREAK@**（唯一取数口 `python3 scripts/product_streak.py --streak-for @ROUND@`，"
              u"as-of 第 @ROUND@ 轮的最后一笔产品提交是 @LASTSHA@ = 第 @LASTROUND@ 轮）。"
              u"看图腿 @EYELEG@（@PNGS@ 张帧在盘上，本轮无新帧）。@EYE_SHORT@\n")

U_DEFS = len(re.findall(u"(?m)^- \\*\\*U-\\d{3,4}[：(]", ui))
SUBS2 = dict(SUBS)
SUBS2[u"@UDEF@"] = s(U_DEFS + 3)
fr = orig["FR"]
repl = []
for label, tpl in ((u"走到哪了", FR_WALK), (u"判据与门的规模", FR_DOOR),
                   (u"产品面（这一节最该被读的部分）", FR_PRODUCT)):
    a, b = bullet(fr, label)
    repl.append((a, b, fill_tpl(tpl, SUBS2)))
a, b = bullet(fr, u"仍开（截至本轮，完整名单以 `AGENT_STATE.md` 的 %s 节 ② 为准）" % PREV_TAG)
fr_still = fr[a:b]
# §13 的仍开 bullet 用正则改，不手抄整句：R306 写进去的那句括号里带着"2 条"这种派生数，
# 手抄锚点第二天就对不上（本轮 D-288 说的"抄来的常数会腐烂"，生成器自己也一样）。
before4 = fr_still.count(u"354 的第四步")
fr_still = re.sub(u"354 的第四步（[^）]*）",
                  u"354 的第五步（sampled 那两条的退场阈值：连续几跑没红才算，还是要求作者显式删）",
                  fr_still)
if before4 != 1 or u"354 的第五步" not in fr_still:
    die(u"§13 的仍开 bullet 没把 354 更新到第五步（改前 %d 处）⇒ 报告还在把已结案的第四步当欠账" % before4)
# 就地更正 R306 留下的叠写：那一次两条 replace 都命中同一句，产出"剩 11 份 15 行，剩 29 行"
# 这种半新半旧的格子（同一格里两个互相矛盾的数，比停在旧数更坏）。整格重写成一份现读值。
before360 = len(re.findall(u"360（[^）]*）", fr_still))
with io.open(os.path.join(ROOT, u"scripts", u"tests", u"test_readings_channel_coverage.py"),
             encoding=u"utf-8") as _h:
    _ceil = re.search(u"(?m)^BARE_PRINT_LINE_CEILING = (\\d+)", _h.read())
if not _ceil:
    die(u"读不到 BARE_PRINT_LINE_CEILING ⇒ 360 那一格的数不许手填")
fr_still = re.sub(u"360（[^）]*）",
                  u"360（已搬三批，剩 11 份 %s 行；R307 就地更正上一版这里的叠写）" % _ceil.group(1),
                  fr_still)
if before360 != 1 or u"R307 就地更正" not in fr_still:
    die(u"§13 的 360 那一格没被重写成一份干净的现读数（改前 %d 处）" % before360)
fr_still = re.sub(u"%s 节 ②" % PREV_TAG, u"%s 节 ②" % R_TAG, fr_still)
if u"%s 节 ②" % R_TAG not in fr_still:
    die(u"§13 的仍开 bullet 没指向本轮的 STATE 节 ⇒ 指针过期")
repl.append((a, b, fr_still))

new = {
    "UI": orig["UI"].replace(u"## 第 %d 轮" % (ROUND - 1), texts["UI"] + u"## 第 %d 轮" % (ROUND - 1), 1),
    "IT": orig["IT"].rstrip(u"\n") + u"\n\n" + texts["IT"].strip(u"\n") + u"\n",
    "DEC": orig["DEC"].rstrip(u"\n") + u"\n" + texts["DEC"].strip(u"\n") + u"\n",
    "BL": append_note_to_item(orig["BL"], 354, texts["N354"]),
    "ST": orig["ST"].replace(u"## %s 状态（" % PREV_TAG, texts["ST"] + u"## %s 状态（" % PREV_TAG, 1),
    "CH": orig["CH"].replace(u"## [Unreleased]\n\n", u"## [Unreleased]\n\n" + texts["CH"], 1),
    "FR": fr,
}
for a, b, t in sorted(repl, key=lambda x: x[0], reverse=True):
    new["FR"] = new["FR"][:a] + t + new["FR"][b:]

# §1 的「视觉台账 U-31 … U-<NNN>」那一格由闸门按 LAG_U=3 判 ⇒ 每轮现读抬，
# 停在上一轮的数就是 R307 写盘后电池里那朵 FINAL_REPORT_UCELL_STALE 的成因。
before_u = len(re.findall(u"U-31 … U-\\d+（R\\d+ 现读抬到最新一节）", new["FR"]))
if before_u != 1:
    die(u"§1 的 U 那一格锚点命中 %d 次（要恰好 1）⇒ 形状漂了，先打印原文再钉锚点" % before_u)
new["FR"] = re.sub(u"U-31 … U-\\d+（R\\d+ 现读抬到最新一节）",
                   u"U-31 … U-%d（%s 现读抬到最新一节）" % (UC, R_TAG),
                   new["FR"], count=1)
if u"U-31 … U-%d（%s 现读抬" % (UC, R_TAG) not in new["FR"]:
    die(u"§1 的 U 上界没抬到 U-%d ⇒ 写盘后那一格照旧会红" % UC)

for key in new:
    if key != u"FR" and len(new[key]) <= len(orig[key]):
        die(u"%s 写后不比写前长 ⇒ 可能是替换而不是插入" % key)
if u"追记（%s 第四步结案" % R_TAG not in new["BL"]:
    die(u"354 的结案追记没落进去")
i354 = new["BL"].find(u"**354. ")
i355 = new["BL"].find(u"**355. ")
i354note = new["BL"].find(u"第四步结案")
if not (0 <= i354 < i354note < i355):
    die(u"354 的追记落在 354 那一节之外（%d/%d/%d）⇒ 会挂到别人的条目上" % (i354, i354note, i355))

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
post, err = battery(u"写盘后", u"/tmp/r307_battery_post.log")
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
print(u"LEDGERS_R307 OK batt=Ran " + post[0] + u" (skipped=" + post[1] + u") streak=" + STREAK_N
      + u" prod=" + s(len(PROD)) + u" swift=" + s(len(SWIFT)) + u" eye=" + EYE_LEG
      + u" frames=" + FRAMES_ON_DISK + u" knives=" + kk[u"CAUGHT"] + u"/" + kk[u"刀"]
      + u" U=" + s(UA) + u".." + s(UC) + u" D=" + s(DN) + u" ci=" + CI_STATE
      + u" derived_score(Round " + s(RD_N) + u")=" + s(score) + u" GAPS=" + gaps)

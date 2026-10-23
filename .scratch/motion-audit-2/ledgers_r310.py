# -*- coding: utf-8 -*-
"""R310 的七本台账（第 309 轮 / Round 307 · 腐烂的针要能被数出来）。

机器与 R309 同一套（事务性、写盘前后电池同数、报告计数器由写完账之后的仪器刷、
写盘后崩在任何地方都整体还原）；正文与本轮读数不同。
"""
import argparse
import io
import json
import os
import re
import subprocess
import sys
from collections import OrderedDict

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FILES = {
    "UI": os.path.join(ROOT, "AGENT_UI_AUDIT.md"),
    "IT": os.path.join(ROOT, "AGENT_VISUAL_ITERATION.md"),
    "DEC": os.path.join(ROOT, "AGENT_DECISIONS.md"),
    "BL": os.path.join(ROOT, "AGENT_BACKLOG.md"),
    "CH": os.path.join(ROOT, "CHANGELOG.md"),
    "ST": os.path.join(ROOT, "AGENT_STATE.md"),
    "FR": os.path.join(ROOT, "AGENT_FINAL_REPORT.md"),
}
CURVE = os.path.join(ROOT, ".scratch", "motion-audit-2", "curve_from_ledger.py")
STREAK = os.path.join(ROOT, "scripts", "product_streak.py")
HA = os.path.join(ROOT, "scripts", "hidden_arms.py")
CHAIN = "/tmp/r310_chain.log"
KNIFE_LOG = "/tmp/r310_knives.log"
R_TAG, PREV_TAG, R_NEXT = u"R310", u"R309", u"R311"
PREV_ROUND, ROUND, RDN = 308, 309, 307
TODAY = u"2026-10-23"
EYE = os.environ.get("R310_EYE", u"")
WROTE, OK_EXIT = [], []


def die(msg):
    if WROTE:
        for key, text in orig.items():
            wr(FILES[key], text)
        msg = msg + u"（七本已整体还原）"
    sys.stderr.write(u"R310_LEDGERS_REFUSE " + msg + u"\n")
    sys.exit(1)


def rd(path):
    with io.open(path, encoding="utf-8") as h:
        return h.read()


def wr(path, text):
    with io.open(path, "w", encoding="utf-8") as h:
        h.write(text)


def sh(argv, cwd=None):
    env = dict(os.environ)
    env["PYTHONUTF8"] = "1"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    proc = subprocess.run(argv, cwd=cwd or ROOT, env=env,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return proc.stdout.decode("utf-8", "replace"), proc.returncode


def s(x):
    return x if isinstance(x, type(u"")) else json.dumps(x, ensure_ascii=False)


def fill(tpl, subs):
    out = tpl
    for k, v in subs.items():
        out = out.replace(k, s(v))
    return out


def battery(tag, log_path):
    out, rc = sh([sys.executable, "-W", "ignore", "-m", "unittest", "discover",
                  "-s", "scripts/tests"], cwd=ROOT)
    with io.open(log_path, "w", encoding="utf-8") as h:
        h.write(out)
    ran = re.findall(r"^Ran (\d+) tests", out, re.M)
    ok = re.search(r"^OK \(skipped=(\d+)\)$", out, re.M) or re.search(r"^OK$", out, re.M)
    if not ran or not ok:
        die(u"%s 电池没有结论行（rc=%d）⇒ 不许把「没解析到」当绿" % (tag, rc))
    if re.search(r"^FAILED", out, re.M):
        reds = [l for l in out.splitlines() if l.startswith(("FAIL:", "ERROR:"))][:6]
        die(u"%s 电池红：%s" % (tag, u" / ".join(reds)))
    return ran[-1], (ok.group(1) if ok.lastindex else u"0")


def once(text, anchor, replacement, label):
    if text.count(anchor) != 1:
        die(u"锚点「%s」命中 %d 次（要恰好 1）" % (label, text.count(anchor)))
    return text.replace(anchor, replacement, 1)


STRAY_RX = re.compile(u"@([A-Z][A-Z0-9_]{1,24})@")

ap = argparse.ArgumentParser(prog="ledgers_r310.py",
                             description=u"R310 的七本台账（判据轮）")
ap.add_argument("--eye", default=u"", help=u"看图腿正文（也可用环境变量 R310_EYE 传）")
ARGS = ap.parse_args()
EYE = (ARGS.eye or EYE).strip()
if not EYE:
    die(u"看图腿没传 R310_EYE / --eye ⇒ 真实视觉审查不许省略，也不许凭记忆写")

# ---------------------------------------------------------------- 现读
pre, pre_skip = battery(u"写盘前", u"/tmp/r310_battery_pre.log")

head_sub, _ = sh(["git", "log", "-1", "--format=%s"])
if R_TAG not in head_sub:
    die(u"HEAD 的 subject 不含 %s ⇒ 代码半还没提交，账不许先落（%s）" % (R_TAG, head_sub.strip()[:80]))
books = set(os.path.relpath(v, ROOT) for v in FILES.values())
log_out, _ = sh(["git", "log", "-12", "--format=%H\x1f%s"])
prod, swift_files, others, surface = [], [], [], []
for row in log_out.splitlines():
    if u"\x1f" not in row:
        continue
    sha_, subj_ = row.split(u"\x1f", 1)
    if R_TAG not in subj_:
        continue
    surface.append(sha_[:7])
    names, _ = sh(["git", "show", "--name-only", "--format=", sha_])
    for line in names.splitlines():
        line = line.strip()
        if not line or line in books:
            continue
        if line.startswith("ClipboardHistory/Sources/"):
            prod.append(line)
        elif line.startswith("ClipboardHistory/"):
            swift_files.append(line)
        else:
            others.append(line)
others = sorted(set(others))
if prod or swift_files:
    die(u"本轮按判据轮出账，改动面里却有 %d 产品 / %d Swift 文件 ⇒ 得按产品轮重跑 Swift 三条腿"
        % (len(prod), len(swift_files)))
if len(others) < 5 or not all(o.startswith(("scripts/", ".scratch/")) for o in others):
    die(u"改动面应当全是 scripts / .scratch 下的文件（≥5 个），现读 %s" % u", ".join(others))

chain = rd(CHAIN) if os.path.exists(CHAIN) else u""
for needle, label in ((u"### PRECHECK", u"预检"), (u"### KNIVES", u"刀表"),
                      (u"### HIDDEN_ARMS", u"腐烂针尺"), (u"### BUILD", u"构建"),
                      (u"### FRAMES", u"帧目录计数"), (u"### SWIFT_LEGS", u"Swift 三条腿 NOT-RUN")):
    if needle not in chain:
        die(u"验证链日志里没有「%s」那一节 ⇒ 那条腿没跑完或没写清" % label)
warn = re.findall(r"WARNINGS=(\d+)", chain)
if not warn or warn[-1] != u"0":
    die(u"构建告警不是 0（现读 %s）" % (warn[-1] if warn else u"没解析到"))
FRAMES = (re.findall(r"FRAMES_ON_DISK=(\d+)", chain) or [u""])[-1]
if not FRAMES:
    die(u"没读到帧目录在盘上的张数 ⇒ 看图腿不许凭记忆说「上一轮的帧还在」")
RD_LINE = (re.findall(r"(?m)^LEDGER_READINGS 小节前缀=.+$", chain) or [u""])[-1]
for leg in (u"FULL_SUITE=NOT-RUN", u"CAPTURE=NOT-RUN", u"INSTALL=NOT-RUN"):
    if leg not in chain:
        die(u"Swift 那条腿（%s）没在日志里写明 NOT-RUN ⇒ 没跑的腿必须可见" % leg)

knife = rd(KNIFE_LOG) if os.path.exists(KNIFE_LOG) else u""
km = re.search(r"R310_MUTATE 刀=(\d+) CAUGHT=(\d+) ESCAPED=(\d+) NOT_RUN=(\d+) RESTORE_CLEAN=(\w+)",
               knife)
if not km:
    die(u"刀表结论行没解析到 ⇒ 六把刀的读数不许手抄")
K_N, K_CAUGHT, K_ESC, K_NOTRUN, K_CLEAN = (int(km.group(1)), int(km.group(2)), int(km.group(3)),
                                          int(km.group(4)), km.group(5))
if K_CAUGHT != K_N or K_ESC or K_NOTRUN or K_CLEAN != u"yes":
    die(u"刀表不干净：刀=%d CAUGHT=%d ESCAPED=%d NOT_RUN=%d CLEAN=%s"
        % (K_N, K_CAUGHT, K_ESC, K_NOTRUN, K_CLEAN))
base = re.search(r"R310_MUTATE BASELINE 跑=(\d+) 失败=(\d+) exit=(\d+)", knife)
if not base or base.group(2) != u"0" or base.group(3) != u"0":
    die(u"刀表没有「未落刀先绿」那一行 ⇒ 后面的 CAUGHT 不说明任何事")
JUDGE_RUN = base.group(1)

pre_line = re.findall(r"NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=(\d+) bad=(\d+)", chain)
TABLES_N, COVERED, PRE_ARMS, PRE_BAD = (int(x) for x in pre_line[-1]) if pre_line else (0, 0, 0, 1)
if PRE_BAD:
    die(u"针预检 bad=%d ⇒ 有 needle 在册上腐烂" % PRE_BAD)
reg_line = re.findall(r"ARM_TOTAL files=(\d+) arms=(\d+) dupes=(\d+) repeats=(\d+)", chain)
if not reg_line:
    die(u"ARM_TOTAL 没读到 ⇒ 在册刀数不许手抄")
ARM_FILES, ARM_REG, ARM_DUPES, ARM_REPEATS = (int(x) for x in reg_line[-1])
if ARM_DUPES or ARM_REPEATS:
    die(u"名册报 dupes=%d repeats=%d ⇒ 先修跨表撞号" % (ARM_DUPES, ARM_REPEATS))
roster = re.findall(r"TABLE_ROSTER registered=(\d+) unregistered_with_arms=(\d+) hidden_arms=(\d+)",
                    chain)
HID_TABLES, HID_ARMS = (int(roster[-1][1]), int(roster[-1][2])) if roster else (0, 0)

ha_out, ha_rc = sh([sys.executable, HA])
HA_LINE = (re.findall(r"(?m)^HIDDEN_ARMS .+$", ha_out) or [u""])[-1]
if u"处置=ok" not in HA_LINE:
    die(u"腐烂针那把尺自己没签（rc=%d）：%s" % (ha_rc, HA_LINE[:160]))
ROT_NOW = (re.findall(r"rot=(\d+)", HA_LINE) or [u""])[-1]
OPAQUE_NOW = (re.findall(r"抽不出=(\d+)", HA_LINE) or [u"", u""])[-1]
JUDGED_NOW = (re.findall(r"可判=(\d+)", HA_LINE) or [u""])[-1]
TABLES_SCANNED = (re.findall(r"表=(\d+)", HA_LINE) or [u""])[-1]

st_out, st_rc = sh([sys.executable, STREAK, u"--streak-for", s(ROUND)])
STREAK_N = (re.findall(r"streak=(\d+)", st_out) or [u""])[-1]
if st_rc != 0 or not STREAK_N:
    die(u"product_streak 读不到（rc=%d）：%s" % (st_rc, st_out.strip()[-160:]))
LASTSHA = (re.findall(r"last=(\w+)", st_out) or [u""])[-1]
LASTROUND = (re.findall(r"last_round=(\d+)", st_out) or [u""])[-1]
prev_out, prev_rc = sh([sys.executable, STREAK, u"--streak-for", s(ROUND - 1)])
PREV_STREAK = (re.findall(r"streak=(\d+)", prev_out) or [u""])[-1]
if prev_rc != 0 or not PREV_STREAK:
    die(u"上一轮的产品面轮数读不到（rc=%d）" % prev_rc)
ci, _ = sh([sys.executable, os.path.join(ROOT, "scripts", "ci_read.py"), "latest"])
CI = ci.strip().replace(u"\n", u" ")
if u"RUN=" not in CI:
    die(u"⓪ 的 CI 配对没读到（ci_read latest 给的是「%s」）" % CI[:80])

SCORES_RX = re.compile(r"(\d+)=(\d+)")


def scores_by_round(out):
    line = (re.findall(r"^SCORES_BY_ROUND (.+)$", out, re.M) or [u""])[-1]
    return dict((int(a), int(b)) for a, b in SCORES_RX.findall(line))


dk, _ = sh([sys.executable, CURVE])
if (re.findall(r"^GAPS=(\S+)", dk, re.M) or [u""])[-1] != u"none":
    die(u"曲线尺报 GAPS ⇒ 升序台账被插在中间了")
SECTIONS = (re.findall(r"^ROUNDS=(\d+)", dk, re.M) or [u""])[-1]
DERIVED = scores_by_round(dk).get(RDN - 1)
if not SECTIONS or DERIVED is None:
    die(u"曲线仪器没给出上一轮 Round %s 的派生分" % (RDN - 1))

ui = rd(FILES["UI"])
U_MAX = max(int(x) for x in re.findall(r"(?m)^- \*\*U-(\d{3,4})[：(]", ui))
UA, UB, UC = U_MAX + 1, U_MAX + 2, U_MAX + 3
dec = rd(FILES["DEC"])
DN = max(int(x) for x in re.findall(r"(?m)^\*\*D-(\d{3,4})（", dec)) + 1
bl = rd(FILES["BL"])
BL_MAX = max(int(x) for x in re.findall(r"(?m)^\*\*(\d{3})\. ", bl))
BLNEW = BL_MAX + 1
if u"**364. " not in bl:
    die(u"BACKLOG 364 不在盘上 ⇒ 本轮的追记无处可挂")

SUBS = {u"@ROUND@": ROUND, u"@RTAG@": R_TAG, u"@RNEXT@": R_NEXT, u"@RDN@": RDN,
        u"@TODAY@": TODAY, u"@UA@": UA, u"@UB@": UB, u"@UC@": UC, u"@DN@": DN,
        u"@BLNEW@": BLNEW, u"@BATT@": pre, u"@SKIP@": pre_skip, u"@STREAK@": STREAK_N,
        u"@PREVSTREAK@": PREV_STREAK, u"@LASTSHA@": LASTSHA, u"@LASTROUND@": LASTROUND,
        u"@CI@": CI, u"@NOFILES@": len(others), u"@K_N@": K_N, u"@JUDGERUN@": JUDGE_RUN,
        u"@TABLES@": TABLES_N, u"@COVERED@": COVERED, u"@ARMREG@": ARM_REG,
        u"@ARMFILES@": ARM_FILES, u"@HIDTABLES@": HID_TABLES, u"@HIDARMS@": HID_ARMS,
        u"@FRAMES@": FRAMES, u"@RDLINE@": RD_LINE, u"@HALINE@": HA_LINE,
        u"@ROT@": ROT_NOW, u"@OPAQUE@": OPAQUE_NOW, u"@JUDGED@": JUDGED_NOW,
        u"@TSCANNED@": TABLES_SCANNED}
EYE = fill(EYE, SUBS)
SUBS[u"@EYE@"] = EYE
SUBS[u"@EYE_SHORT@"] = EYE.split(u"⇒")[0].strip()

# ---------------------------------------------------------------- 七本正文
UI_NEW = u"""## 第 @ROUND@ 轮（@RTAG@ · U-@UA@…U-@UC@ · @TODAY@）：腐烂的针要能被数出来 —— 静态 AST + 常量传播 + 双向棘轮（U-@UA@…U-@UC@ · 产品 0 文件，判据轮）

- **U-@UA@：藏在 lambda 与变量里的 needle 会腐烂而静态预检不响 —— 本轮把它做成可判、可归因的数：`scripts/hidden_arms.py` 现读 表=@TSCANNED@ 可判=@JUDGED@ rot=@ROT@ 抽不出=@OPAQUE@。**
  364 原本的形状是"名册只报规模"（registered=@TABLES@、未登记表 @HIDTABLES@ 张、隐藏臂 @HIDARMS@ 把），
  而规模不可归因：谁烂了、烂了几把，没人说得出。本轮的尺不 import 那些表
  （@TSCANNED@ 张里至少 10 张没有 `__main__` 守卫，import 就会真的落刀跑 swift 测试），
  只做静态 AST：顶层 `ARMS/MUTATIONS/CASES/TABLE` 逐臂取"能解析成字面量的字符串"当候选
  （变量名走常量传播），候选在盘上**一个都不命中** ⇒ 该臂腐烂，按表点名；抽不出的臂单独登记，
  不许静默丢掉。刀 M902…M907 各钉一条轴，全 CAUGHT。

- **U-@UB@：判法不成立时会造出大批假正例 —— 第一版把中文说明与目标路径当候选，@TSCANNED@ 张表上报 152 rot，其中包含当天刚全 CAUGHT 的 r308 / r309。**
  那是**尺坏**，不是仓库真烂了 152 把。两条修正：① 变量名必须走常量传播（否则针看不见 ⇒ 假"抽不出"）；
  ② 目标路径那一格不是针（它当然在盘上 ⇒ 会把死刀洗活）。与 R307「区间对账没分箱就数出 34 个假正例」
  同一课：**数出来一堆红时先怀疑分箱，不要先加门，更不要先把红写成缺陷清单**。
  M904 / M905 两根刀就是把这两条修正钉住 —— 摘掉任何一条，数立刻漂。

- **U-@UC@：双向棘轮 —— 上界必须**恰好**等于现读值；只判"不许超过"，另一半就没有牙。**
  `rot != ROT_CEILING` 就红：变多 = 有新腐烂；变少 = 名单被修掉了却没降上界
  （上界停在旧值，下一次真烂回去也没人知道）。`抽不出` 同理。
  正对照的基准取**真产物现读**而不是上界自己（拿上界当基准就是同义反复）。
  另记一条自伤：合成夹具的"死针"字符串住在 fixtures 目录里，而夹具自己也被扫进语料 ⇒
  死针命中自己、rot 数不出来 ⇒ 正对照当场失效（M906 钉的就是这一条）。

- **新开 @BLNEW@（腐烂名单要清）**：@ROT@ 把已点名的死刀要逐条处置 —— 重钉针，或按 D-284 写明
  "退役 + 证人"；每清一把就把上界降一格。本轮只把它们变成可归因的数，**没有**替"已处理完"作证。

读数（全部现读，同一遍验证链 /tmp/r310_chain.log）：构建告警 0（`swift build --build-tests`；本轮零 Swift 改动，仍跑是因为 0 告警是产品构建的契约）；
判据卷 scripts/tests/test_hidden_arms.py `Ran @JUDGERUN@ tests / OK`；
刀 M902…M907：本轮 @K_N@ 把全 CAUGHT、RESTORE_CLEAN=yes、NOT_RUN=0、未落刀先绿；
预检 tables=@TABLES@ covered=@COVERED@ arms 名册 files=@ARMFILES@ arms=@ARMREG@ dupes=0 bad=0；
腐烂针尺：`@HALINE@`；R309 那把读数尺互证：`@RDLINE@`；
脚本电池 `Ran @BATT@ / OK (skipped=@SKIP@)`（写盘后同数）；
产品面连续零改动 = **@STREAK@** 轮（取数口 `scripts/product_streak.py --streak-for @ROUND@`；上一轮 @PREVSTREAK@）。

Swift 侧三条腿 **NOT-RUN**（本轮 0 产品文件、0 Swift 文件 ⇒ 没有新字节可跑，也没有旧字节能被本轮弄坏）：
全量卷 NOT-RUN（沿用 R308 那一跑 934 / 44 skip / 0）；重捕帧 NOT-RUN（帧目录现读 @FRAMES@ 张还在盘上）；
换装 NOT-RUN（产物未变）。看图腿 RUN：@EYE@

七维度自评：
| 维度 | 分/满分 |
| --- | --- |
| 真实视觉审查 | 10/15 |
| 判据有效性 | 14/15 |
| 假绿防御 | 15/15 |
| 产品面推进 | 8/15 |
| 台账一致性 | 14/15 |
| 交付诚实性 | 15/15 |
| 可复核性 | 14/15 |
| 合计 | 90/105 |

为什么不是满分（逐条）：真实视觉审查 10 —— 判据轮对画面的净贡献是 0，本轮只复看上一轮那两张；
判据有效性 14 —— 三条新 U 都有尺真身与刀，扣分在"候选集"仍是启发式（长字符串 + 路径过滤），
仍有 @OPAQUE@ 把抽不出候选（要判只能真跑）；假绿防御 15 —— 六把刀各钉一条轴，
两次自伤（152 假正例、夹具进语料洗活死针）都是被对照当场抓住而不是收尾想起来；
产品面推进 8 —— 0 产品文件，这是判断不是遗漏：356 剩下那一半要先量候选，347 / 305 要用户的真机眼；
台账一致性 14 —— 七本一支脚本、报告计数器与 §13 由写完账之后的仪器刷；
交付诚实性 15 —— 新开 @BLNEW@ 把"@ROT@ 把死刀还没清"写在账上，不写成已处理；
可复核性 14 —— 尺、判据卷、刀表都能重跑，扣分在腐烂名单依赖盘上现状（换机器或删表就会漂，
漂了会响 —— 那是设计不是缺陷）。

"""

IT_NEW = u"""## Round @RDN@ · R310（第 @ROUND@ 轮 · @TODAY@）：腐烂的针要能被数出来 —— 静态 AST + 常量传播 + 双向棘轮（产品 0 文件，判据轮）

本轮把 BACKLOG 364 从"规模"做成"可归因的数"：`scripts/hidden_arms.py` 现读
表=@TSCANNED@ 可判=@JUDGED@ rot=@ROT@ 抽不出=@OPAQUE@；判法是双向棘轮（上界必须恰好等于现读值，
两个方向都响）。两次自伤都进账：第一版数出 152 rot 是**判法不成立**（中文说明与目标路径被当候选，
r308 / r309 当天刚全 CAUGHT 也被算成腐烂）；合成夹具住进语料把死针洗活 ⇒ 正对照当场失效。
刀 M902…M907 全 CAUGHT；新开 @BLNEW@ 登记"@ROT@ 把死刀还没逐条处置"。

读数：构建告警 0；判据卷 `Ran @JUDGERUN@ / OK`；刀 @K_N@ 把全 CAUGHT、RESTORE_CLEAN=yes；
预检 tables=@TABLES@ bad=0、名册 files=@ARMFILES@ arms=@ARMREG@；
腐烂尺 `@HALINE@`；脚本电池 `Ran @BATT@ / OK (skipped=@SKIP@)`（写盘后同数）；
产品面连续零改动 = **@STREAK@** 轮（上一轮 @PREVSTREAK@，取数口 `scripts/product_streak.py`）。
Swift 三条腿 NOT-RUN（理由逐条写在正文）；看图腿 RUN（@FRAMES@ 张在盘上，本轮无新帧）：@EYE@

七维度自评：
| 维度 | 分/满分 |
| --- | --- |
| 真实视觉审查 | 10/15 |
| 判据有效性 | 14/15 |
| 假绿防御 | 15/15 |
| 产品面推进 | 8/15 |
| 台账一致性 | 14/15 |
| 交付诚实性 | 15/15 |
| 可复核性 | 14/15 |
| 合计 | 90/105 |

"""

DEC_NEW = u"""**D-@DN@（R@RTAG@）：一条"数出多少坏"的判据，必须先自证它不会把好的数出来；做不到就只准报规模，不准报缺陷。**

理由（本轮实测）：同一件事（找腐烂的针）的第一版给出 152 把，其中包含当天刚全 CAUGHT 的两张表 ——
那不是仓库烂，是分箱错（候选集里混进了中文说明与目标路径）。修完是 @ROT@ 把，每一把都可归因到表与臂号。
与 R307（区间对账先分箱）、R298（按台账措辞数出来的"连续 N 轮"）同一族。

三条配套：① 新尺第一次跑出的"缺陷数"，必须先在**已知不该有缺陷的对象**上跑一遍；
② 判据自身的每条修正都要有刀（M904 常量传播、M905 路径过滤）—— 只有"能红"没有"谁让它红"，
下次改回去没人知道；③ 判据是**双向**的：上界必须恰好等于现读值，
只判一个方向等于另一半没有牙。
"""

BL_364 = u"""  追记（R310）：这一格从"规模"变成"可归因的数"。`scripts/hidden_arms.py` 现读
  表=@TSCANNED@ 可判=@JUDGED@ rot=@ROT@ 抽不出=@OPAQUE@，判法是双向棘轮（上界必须恰好等于现读值）；
  每一把腐烂都点名到表与臂号，刀 M902…M907 各钉一条轴（摘掉 rot 判定、只判单方向、摘常量传播、
  摘路径过滤、让夹具进语料、静默丢掉抽不出的臂 —— 六个坏法各红各的格子）。
  两条边界写清，免得这一格被读成"已结"：
  ① 登记面没变（registered=@TABLES@、未登记表 @HIDTABLES@ 张、隐藏臂 @HIDARMS@ 把）——
     那是"表没进名册"，与"进了名册但针烂了"是两件事；
  ② 数出来的 @ROT@ 把**还没逐条处置** ⇒ 新开 @BLNEW@ 登记。"""

BL_NEW = u"""**@BLNEW@. 数出来的 @ROT@ 把腐烂针要逐条处置（重钉，或按 D-284 写"退役 + 证人"）**（R310）

  R310 把"谁烂了"变成可归因的数（`python3 scripts/hidden_arms.py` 会逐条打
  `HIDDEN_ROT <表> <臂号>`），但**没有**替"已经处理完"作证。
  每条只有两种合法出口：重钉一根在盘上恰好命中一次的针并复跑那张表；
  或按 D-284 写明"这一臂退役 + 它的证人是谁"（不许直接删表绕开检查）。
  上界 `ROT_CEILING` 是双向棘轮：每清一把就降一格，降的时候
  `test_the_ceilings_equal_the_live_readings` 会替我确认没多降。
  另 @OPAQUE@ 把"静态抽不出候选"的臂是第二层欠账：要判只能真跑（把那张表纳入名册并复跑一次）。"""

CH_NEW = u"""### 腐烂的针要能被数出来：静态 AST + 常量传播 + 双向棘轮（R310 / U-@UA@…U-@UC@ · D-@DN@ · 产品 0 文件，判据轮）

- BACKLOG 364 从"规模"做成"可归因的数"：`scripts/hidden_arms.py` 现读 表=@TSCANNED@ 可判=@JUDGED@
  rot=@ROT@ 抽不出=@OPAQUE@；不 import 表（10+ 张没有 `__main__` 守卫 ⇒ import 会真落刀跑 swift 测试），
  只做 AST + 常量传播；判据是双向棘轮（上界必须恰好等于现读值）。
- 两次自伤进账：第一版 152 rot 是判法不成立（中文说明与目标路径被当候选，当天刚全 CAUGHT 的
  r308 / r309 也被算成腐烂）；合成夹具住进语料把死针洗活 ⇒ 正对照当场失效。
- 刀 M902…M907 全 CAUGHT、RESTORE_CLEAN=yes、未落刀基线 `Ran @JUDGERUN@ 失败=0`；
  新开 @BLNEW@ 登记"@ROT@ 把死刀还没逐条处置"；364 留追记（登记面 @HIDARMS@ 把隐藏臂是另一件事）。
- 判据轮：构建告警 0；判据卷 `Ran @JUDGERUN@ / OK`；预检 tables=@TABLES@ bad=0、名册 arms=@ARMREG@；
  脚本电池 `Ran @BATT@ / OK (skipped=@SKIP@)`（写盘后同数）；产品面连续零改动 **@STREAK@** 轮；
  Swift 三条腿 NOT-RUN 并逐条写理由。

"""

ST_NEW = u"""## @RTAG@ 状态（第 @ROUND@ 轮 / Round @RDN@ · @TODAY@）

本轮做"腐烂的针要能被数出来"：`scripts/hidden_arms.py`（AST + 常量传播 + 双向棘轮）现读
表=@TSCANNED@ 可判=@JUDGED@ rot=@ROT@ 抽不出=@OPAQUE@；判据卷 `Ran @JUDGERUN@ / OK`；
刀 M902…M907 全 CAUGHT。D-@DN@ 定「数缺陷的判据必须先自证它不会把好的数出来；
做不到只准报规模」；364 留追记（从规模变可归因）；新开 @BLNEW@ 登记 @ROT@ 把死刀待清。

最后更新：@TODAY@（本地 · @RTAG@ / 第 @ROUND@ 轮 / Round @RDN@）：**腐烂针第一次可点名**（产品 0 文件，判据轮）
现读：构建告警 0；判据卷 `Ran @JUDGERUN@ / OK`；刀 @K_N@ 把全 CAUGHT、RESTORE_CLEAN=yes；
预检 tables=@TABLES@ covered=@COVERED@ bad=0、名册 files=@ARMFILES@ arms=@ARMREG@ dupes=0；
腐烂尺 `@HALINE@`；R309 读数尺互证 `@RDLINE@`；电池 Ran @BATT@ / OK (skipped=@SKIP@)（写盘后同数）；
看图腿 RUN（@FRAMES@ 张在盘上，本轮无新帧 —— @EYE_SHORT@）。
产品文件 0 个，连续零改动 **@STREAK@** 轮（唯一取数口 `python3 scripts/product_streak.py --streak-for @ROUND@`，
同形用于 `--check`；上一轮 @PREVSTREAK@）。as-of 第 @ROUND@ 轮的最后一笔产品提交是 @LASTSHA@ = 第 @LASTROUND@ 轮。
Swift 三条腿 NOT-RUN 并写理由（0 Swift 文件 ⇒ 没有新字节可跑，也没有旧字节能被本轮弄坏）。

⓪ @RNEXT@ 开场要先读的（成对：run id ↔ commit）：@CI@
   —— 本轮与 R309 的 runner 结论都要读。另外两件事：
   ① `scripts/hidden_arms.py` 的语料是**盘上现状**，runner 上工作树相同 ⇒ 数相同；
      任何一台机器少一张表就会漂，而漂了会响（双向棘轮），别把它当机器差异放行；
   ② 判据卷里 `test_the_ceilings_equal_the_live_readings` 依赖 .scratch 的表都在 ——
      若 runner 的 checkout 少了文件，那一格按"缺产物算红"处理，不许 skip。

① 下一轮（@RNEXT@）的靶：① **回到产品面** —— 356 剩下那一半（暗档最细一步 17.33 低于地板 18、
   1x/2x 抗锯齿离散 1.7 倍）：先量"换通道"候选有没有产物证人，不许拿减档数当解药；
   ② @BLNEW@：@ROT@ 把腐烂针逐条处置，每清一把就降上界；
   ③ 348 剩下的读数族（帧数 / 刀数 / §8 格子数）各配一条恒等式；
   ④ 360 的最后一批（11 份裸 stdout）；⑤ 361 的合并；⑥ 347 / 305 仍欠用户的真机眼。

② 仍开：347（真机证人）、305（等 347）、356 的**那一半**、@BLNEW@（腐烂针待清）、
   364 的"抽不出候选的 @OPAQUE@ 把要真跑"、348 的"读数族还没纳全"、354 的第五步、
   360（剩 11 份）、361（未合并）、359、362、349、350 第二步、351、344、341 的 CI 契约半、
   339、312 具名出口、304、296、291；用户闸门 220 路 A / 228② / 265。

"""

# ---------------------------------------------------------------- 组装与落盘
orig = {k: rd(v) for k, v in FILES.items()}
for key, marker in ((u"UI", u"## 第 %d 轮" % ROUND), (u"IT", u"## Round %d ·" % RDN),
                    (u"ST", u"## %s 状态（" % R_TAG)):
    if marker in orig[key]:
        die(u"%s 里已经有本轮那一节 ⇒ 生成器不许重跑第二遍" % key)

texts = {u"UI": fill(UI_NEW, SUBS), u"IT": fill(IT_NEW, SUBS), u"DEC": fill(DEC_NEW, SUBS),
         u"BL364": fill(BL_364, SUBS), u"BLNEW": fill(BL_NEW, SUBS),
         u"CH": fill(CH_NEW, SUBS), u"ST": fill(ST_NEW, SUBS)}
for k, t in texts.items():
    hit = STRAY_RX.findall(t)
    if hit:
        die(u"文本 %s 里还有没替换的占位符：%s" % (k, u",".join(sorted(set(hit)))))

heads = [(int(m.group(1)), m.start()) for m in re.finditer(u"(?m)^## 第 (\\d+) 轮", orig["UI"])]
top = max(heads)[1]
new_ui = orig["UI"][:top] + texts["UI"] + orig["UI"][top:]
if new_ui.count(u"## 第 %d 轮" % ROUND) != 1:
    die(u"UI_AUDIT 新节没落在最大轮次标题之上")
nums = [int(m.group(1)) for m in re.finditer(u"(?m)^- \\*\\*U-(\\d{3,4})[：(]", texts["UI"])]
if nums != [UA, UB, UC]:
    die(u"新节的 U 定义行是 %s，要 %s" % (nums, [UA, UB, UC]))

new_it = orig["IT"].rstrip(u"\n") + u"\n\n" + texts["IT"].rstrip(u"\n") + u"\n"
if len(re.findall(u"(?m)^\\| (真实视觉审查|判据有效性|假绿防御|产品面推进|台账一致性|交付诚实性|可复核性) \\| (\\d+)/15 \\|$",
                  texts["IT"])) != 7:
    die(u"七维表不是恰好 7 行 ⇒ 曲线仪器会拒绝推导")

new_dec = orig["DEC"].rstrip(u"\n") + u"\n\n" + texts["DEC"].rstrip(u"\n") + u"\n"


def append_into_item(text, header_prefix, note, label):
    lines = text.split(u"\n")
    hits = [i for i, l in enumerate(lines) if l.startswith(header_prefix)]
    if len(hits) != 1:
        die(u"%s 的条目头命中 %d 行（要恰好 1）" % (label, len(hits)))
    h = hits[0]
    nxt = [i for i in range(h + 1, len(lines)) if re.match(u"\\*\\*\\d{3}\\. ", lines[i])]
    k = nxt[0] if nxt else len(lines)
    while lines[k - 1].strip() == u"":
        k -= 1
    head = u"\n".join(lines[:k])
    if not head.endswith(u"\n"):
        head += u"\n"
    out = head + note.rstrip(u"\n") + u"\n" + u"\n".join(lines[k:]).lstrip(u"\n")
    if not (0 <= out.find(header_prefix) < out.find(note.split(u"\n")[0].strip())):
        die(u"%s 的追记落点不对" % label)
    return out


new_bl = append_into_item(orig["BL"], u"**364. ", texts["BL364"], u"364")
if re.search(u"(?m)^\\*\\*%d\\. " % BLNEW, new_bl):
    die(u"BACKLOG %d 已存在 ⇒ 不许开第二张同题单，去追记原条目" % BLNEW)
new_bl = new_bl.rstrip(u"\n") + u"\n\n" + texts["BLNEW"].rstrip(u"\n") + u"\n"
if len(re.findall(u"(?m)^\\*\\*\\d{3}\\. ", new_bl)) != \
        len(re.findall(u"(?m)^\\*\\*\\d{3}\\. ", orig["BL"])) + 1:
    die(u"BACKLOG 条目头数量不是「原数 +1」⇒ 新单没落成一条")

new_ch = once(orig["CH"], u"## [Unreleased]\n\n", u"## [Unreleased]\n\n" + texts["CH"],
              u"CHANGELOG [Unreleased]")
if sum(1 for line in new_ch.split(u"\n") if line.strip() == u"## [Unreleased]") != 1:
    die(u"CHANGELOG 的 [Unreleased] 标题行不再是恰好 1 行")

new_st = once(orig["ST"], u"## %s 状态（" % PREV_TAG,
              texts["ST"] + u"## %s 状态（" % PREV_TAG, u"STATE 轮换")
if u"## %s 状态（" % PREV_TAG not in new_st or u"## %s 状态（" % R_TAG not in new_st:
    die(u"STATE 轮换后上一轮的标记没了")

fr = orig["FR"]
if len(re.findall(u"U-31 … U-\\d+（R\\d+ 现读抬到最新一节）", fr)) != 1:
    die(u"§1 的 U 那一格锚点命中不是 1")
fr = re.sub(u"U-31 … U-\\d+（R\\d+ 现读抬到最新一节）",
           u"U-31 … U-%d（%s 现读抬到最新一节）" % (UC, R_TAG), fr, count=1)
fr = once(fr, u"完整名单以 `AGENT_STATE.md` 的 %s 节 ② 为准" % PREV_TAG,
          u"完整名单以 `AGENT_STATE.md` 的 %s 节 ② 为准" % R_TAG, u"§13 仍开指针")

new = {u"UI": new_ui, u"IT": new_it, u"DEC": new_dec, u"BL": new_bl,
       u"CH": new_ch, u"ST": new_st, u"FR": fr}
for key in new:
    if key != u"FR" and len(new[key]) <= len(orig[key]):
        die(u"%s 写后不比写前长 ⇒ 可能是替换而不是插入" % key)
stray = [u"%s:%d %s" % (k, n, hit.group(0)) for k, t in new.items()
         for n, line in enumerate(t.split(u"\n"), 1) for hit in STRAY_RX.finditer(line)]
if stray:
    die(u"写盘前有没被替换的占位符（%d 处）：%s" % (len(stray), u"；".join(stray[:6])))

for key, text in new.items():
    wr(FILES[key], text)
WROTE.append(True)

import atexit


def _crash_guard():
    if WROTE and not OK_EXIT:
        for key, text in orig.items():
            wr(FILES[key], text)
        sys.stderr.write(u"R310_CRASH_RESTORED 未捕获异常 ⇒ 七本已整体还原\n")


atexit.register(_crash_guard)

txt = rd(FILES["FR"])
out, crc = sh([sys.executable, CURVE])
rounds_after = (re.findall(r"^ROUNDS=(\d+)", out, re.M) or [u""])[-1]
last_round = (re.findall(r"^PHASE2 n=\d+ rounds=9\.\.(\d+)", out, re.M) or [u""])[-1]
tail = (re.findall(r"^SCORES_BY_ROUND (.+)$", out, re.M) or [u""])[-1]
if not rounds_after or not last_round or not tail:
    die(u"写盘后曲线尺没给出 ROUNDS= / rounds=9..N / SCORES_BY_ROUND（rc=%d）" % crc)
lines = txt.split(u"\n")
m = re.search(u"R9–R(\\d+)，(\\d+) 节自评", lines[0])
if not m or lines[0].count(u"R9–R") != 1:
    die(u"报告标题那一行没找到 `R9–R<NNN>，<NNN> 节自评` ⇒ 不敢整行改写")
lines[0] = lines[0][:m.start()] + u"R9–R%s，%s 节自评" % (last_round, rounds_after) + lines[0][m.end():]
body = u"\n".join(lines)
prod_cell = (u"- **产品面（这一节最该被读的部分）**：本轮产品文件 0 个、Swift 0 份（判据轮：改动面 %s 个文件，"
             u"全在 `scripts/` 与 `.scratch/motion-audit-2/`），产品面连续零改动轮数 = **%s**"
             u"（唯一取数口 `python3 scripts/product_streak.py --streak-for %s`，as-of 第 %s 轮的最后一笔"
             u"产品提交是 %s = 第 %s 轮；上一轮那一格是 %s）。看图腿 RUN：帧目录现读 %s 张还在盘上，"
             u"本轮无新帧 ⇒ Swift 三条腿（全量卷 / 重捕帧 / 换装）按 NOT-RUN 记账并各写理由"
             % (len(others), STREAK_N, ROUND, ROUND, LASTSHA, LASTROUND, PREV_STREAK, FRAMES))
scale_cell = (u"- **判据与门的规模**：脚本电池现读 **Ran %s**（写盘后同数），"
              u"变异臂在册 **%s** 把 / %s 张表（预检 tables=%s covered=%s bad=%s，"
              u"未登记表 %s 张 / 隐藏臂 %s 把 ⇒ 364）；腐烂针尺现读 `@HALINE@`；"
              u"U 定义行 **%s 条**、最大 **U-%s**；决定台账最大 **D-%s**，BACKLOG 最大 **%s**"
              % (pre, ARM_REG, ARM_FILES, TABLES_N, COVERED, PRE_BAD, HID_TABLES, HID_ARMS,
                 len(re.findall(u"(?m)^- \\*\\*U-(\\d{3,4})[：(]", new_ui)), UC, DN, BLNEW))
where_cell = (u"- **走到哪了**：阶段二累计 `## Round` 节 **%s** 节，最新一节是 **Round %s**；"
              u"自评曲线按轮现读 %s（现读 `curve_from_ledger.py`）。派生分连续多轮低于 90 "
              u"⇒ 按目标继续修，不收口。" % (rounds_after, last_round, tail))
for label, cell in ((u"产品面（这一节最该被读的部分）", prod_cell),
                    (u"判据与门的规模", scale_cell), (u"走到哪了", where_cell)):
    parts = body.split(u"\n")
    hits = [i for i, l in enumerate(parts) if l.startswith(u"- **%s**：" % label)]
    if len(hits) != 1:
        die(u"§13 的「%s」那一格命中 %d 行（要恰好 1）" % (label, len(hits)))
    parts[hits[0]] = fill(cell, SUBS)
    body = u"\n".join(parts)
gout, grc = sh(["git", "log", "-40", "--format=%h\x1f%s", "--",
                os.path.join("ClipboardHistory", "Sources")])
src_rows = []
for line in gout.splitlines():
    if u"\x1f" not in line:
        continue
    sha_, subj_ = line.split(u"\x1f", 1)
    mb = re.match(u"^R(\\d+)", subj_.strip())
    src_rows.append((sha_.strip(), int(mb.group(1)) if mb else None, subj_.strip()))
picked = [r for r in src_rows if r[1] is not None and r[1] <= int(R_TAG[1:])]
if not picked:
    die(u"标签 ≤ %s 的源码提交一笔都没有 ⇒ 那一格不许拿「此刻最新」凑数" % R_TAG)
live_sha, live_src_round, _ = picked[0]
older = [r for r in src_rows if r[0] != live_sha and r[1] is not None]
prev_txt = (u"上一笔动 `Sources/` 的是 R%d（`%s`）。" % (older[0][1], older[0][0])) if older else u""
src_cell = (u"| 最后一次动到 `Sources/` 的轮次 | **R%d**（commit `%s`）—— 本轮是判据轮（改动面 %s 个文件"
            u"全在 `scripts/` 与 `.scratch/`，0 个 `Sources/` 文件）；这一格登记的是仓库里**最近一笔动过源码的提交**，"
            u"改了什么以 `AGENT_UI_AUDIT.md` 里 R%d 那一节为准（这一格只登记号与数，不复述结论）。%s|"
            % (live_src_round, live_sha, len(others), live_src_round, prev_txt))
parts = body.split(u"\n")
hits = [i for i, l in enumerate(parts) if l.startswith(u"| 最后一次动到 `Sources/` 的轮次 |")]
if len(hits) != 1:
    die(u"报告「最后一次动到 Sources/」那一格命中 %d 行" % len(hits))
parts[hits[0]] = src_cell
body = u"\n".join(parts)
if STRAY_RX.search(body):
    die(u"报告刷新后还有没替换的占位符：%s" % STRAY_RX.findall(body)[:4])
wr(FILES["FR"], body)
rf, rfc = sh([sys.executable, os.path.join(ROOT, ".scratch", "motion-audit-2",
                                           "refresh_report_section1.py")])
if rfc != 0 or u"REFUSED" in rf:
    die(u"§1 那一格的刷新器没签（rc=%d）：%s" % (rfc, rf.strip()[-200:]))

post, post_skip = battery(u"写盘后", u"/tmp/r310_battery_post.log")
if (post, post_skip) != (pre, pre_skip):
    die(u"电池计数变了（%s/%s → %s/%s）" % (pre, pre_skip, post, post_skip))
ck, crc = sh([sys.executable, STREAK, u"--check"])
if crc != 0:
    die(u"353 的门不认这版台账：" + (ck + u"\n").strip()[-400:])
cv2, _ = sh([sys.executable, CURVE])
if (re.findall(r"^GAPS=(\S+)", cv2, re.M) or [u""])[-1] != u"none":
    die(u"写盘后曲线尺报缺口 ⇒ 升序台账被插在中间")
DERIVED2 = scores_by_round(cv2).get(RDN)
if DERIVED2 is None:
    die(u"写盘后曲线尺没给出本轮 Round %s 的派生分" % RDN)
if u"R9–R%s" % last_round not in rd(FILES["FR"]).split(u"\n")[0]:
    die(u"报告标题没接上写盘后的尾轮 Round %s" % last_round)
if u"U-31 … U-%d" % UC not in rd(FILES["FR"]):
    die(u"报告 §1 的 U 上界不是本轮的 U-%d" % UC)

OK_EXIT.append(True)
print(u"LEDGERS_R310 OK batt=Ran " + post + u" (skipped=" + post_skip + u") streak=" + STREAK_N
      + u"(上一轮 " + PREV_STREAK + u") 改动面=" + s(len(others)) + u" 刀=" + s(K_N)
      + u" 在册=" + s(ARM_REG) + u"/" + s(ARM_FILES) + u"表 rot=" + s(ROT_NOW)
      + u" 抽不出=" + s(OPAQUE_NOW) + u" 可判=" + s(JUDGED_NOW)
      + u" U=" + s(UA) + u".." + s(UC) + u" D=" + s(DN) + u" BL=" + s(BLNEW)
      + u" 判据卷=" + s(JUDGE_RUN) + u" 帧=" + FRAMES
      + u" derived(Round " + s(RDN) + u")=" + s(DERIVED2)
      + u" report尾轮=Round " + s(last_round) + u" 节数=" + s(rounds_after))

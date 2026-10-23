# -*- coding: utf-8 -*-
u"""R317 的七本台账（第 316 轮 / Round 314 · 看图轮：零代码改动）。

与 @RPREVTAG@ 那支最大的不同：**本轮没有可编译的改动**，所以构建 / 全量卷 / 重捕帧 / 基线 / 换装
这五腿**不适用**（不是没跑）。闸门因此只留真能判的那几条：
① git 现读改动面必须只有台账文件；② 脚本电池写盘前后同数；③ 曲线尺 GAPS=none 且给出本轮派生分；
④ `product_streak --check` 必须签；⑤ 腐烂尺与针预检必须自己签（bad=0、处置=ok）；
⑥ 七维表恰好 7 行、U 定义行恰好三格、无残留占位符。
"""
import argparse
import atexit
import io
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FILES = {
    u"UI": os.path.join(ROOT, "AGENT_UI_AUDIT.md"),
    u"IT": os.path.join(ROOT, "AGENT_VISUAL_ITERATION.md"),
    u"DEC": os.path.join(ROOT, "AGENT_DECISIONS.md"),
    u"BL": os.path.join(ROOT, "AGENT_BACKLOG.md"),
    u"CH": os.path.join(ROOT, "CHANGELOG.md"),
    u"ST": os.path.join(ROOT, "AGENT_STATE.md"),
    u"FR": os.path.join(ROOT, "AGENT_FINAL_REPORT.md"),
}
CURVE = os.path.join(ROOT, ".scratch", "motion-audit-2", "curve_from_ledger.py")
STREAK = os.path.join(ROOT, "scripts", "product_streak.py")
HA = os.path.join(ROOT, "scripts", "hidden_arms.py")
PRECHECK = os.path.join(ROOT, ".scratch", "motion-audit-2", "mutate_needle_precheck.py")
BODIES = os.path.join(ROOT, ".scratch", "motion-audit-2", "r317_bodies.txt")
TODAY = u"2026-10-24"
R_TAG, PREV_TAG, R_NEXT = u"R317", u"R316", u"R318"
PREV_ROUND, ROUND, RDN = 315, 316, 314
NEEDLE_HOUSE = 367          # 腐烂针那笔债所在的条目（下面断言它在盘上）
WROTE, OK_EXIT = [], []


def die(msg):
    sys.stderr.write(u"R317_LEDGERS_REFUSE %s\n" % msg)
    if WROTE:
        for key, text in orig.items():
            wr(FILES[key], text)
        sys.stderr.write(u"R317_RESTORED 七本已整体还原\n")
    sys.exit(1)


def rd(p):
    h = io.open(p, encoding="utf-8")
    try:
        return h.read()
    finally:
        h.close()


def wr(p, t):
    h = io.open(p, "w", encoding="utf-8")
    try:
        h.write(t)
    finally:
        h.close()


def sh(argv, cwd=None):
    q = subprocess.Popen(argv, cwd=cwd or ROOT, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, close_fds=True)
    out, _ = q.communicate()
    return (out or b"").decode("utf-8", "replace"), q.returncode


def s(x):
    return x if isinstance(x, type(u"")) else str(x)


def fill(tpl, subs):
    out = tpl
    for k, v in subs.items():
        out = out.replace(k, s(v))
    return out


def battery(tag, log_path):
    out, rc = sh([sys.executable, u"-m", u"unittest", u"discover", u"-s", u"scripts/tests", u"-v"])
    io.open(log_path, "w", encoding="utf-8").write(out)
    ran = re.findall(r"(?m)^Ran (\d+) tests? in", out)
    if not ran:
        die(u"%s 电池没打印 Ran 行（rc=%d）" % (tag, rc))
    tail = out[out.rfind(u"Ran "):]
    if u"FAILED" in tail:
        die(u"%s 电池红：%s" % (tag, tail[:200].replace(u"\n", u" / ")))
    skip = re.findall(r"(?m)^OK \(skipped=(\d+)\)", tail)
    if not skip:
        if not re.search(r"(?m)^OK$", tail):
            die(u"%s 电池结论行不是 OK / OK (skipped=N)" % tag)
        skip = [u"0"]
    return ran[-1], skip[-1]


def once(text, anchor, replacement, label):
    n = text.count(anchor)
    if n != 1:
        die(u"%s 的锚点命中 %d 次（要恰好 1）：%r" % (label, n, anchor[:60]))
    return text.replace(anchor, replacement)


STRAY_RX = re.compile(u"@([A-Z][A-Z0-9_]{1,24})@")
ap = argparse.ArgumentParser(prog="ledgers_r317.py", description=u"R317 的七本台账（看图轮）")
ap.add_argument(u"--eye", default=os.environ.get(u"R317_EYE", u""),
                help=u"看图腿正文（也可用环境变量 R317_EYE 传）")
ARGS = ap.parse_args()
EYE = ARGS.eye.strip()
if not EYE:
    die(u"看图腿没传 R317_EYE / --eye ⇒ 真实视觉审查不许省略，也不许凭记忆写")

pre, pre_skip = battery(u"写盘前", u"/tmp/r317_battery_pre.log")
head_sub, _ = sh([u"git", u"log", u"-1", u"--format=%s"])
if R_TAG not in head_sub:
    die(u"HEAD 的 subject 不含 %s ⇒ 本轮那两笔还没提交（%s）" % (R_TAG, head_sub.strip()[:80]))

# 本轮"零代码改动"必须是**读出来的**：R317 的每一笔都只准动台账文件。
books = set(os.path.relpath(v, ROOT) for v in FILES.values())
log_out, _ = sh([u"git", u"log", u"-10", u"--format=%H\x1f%s"])
touched, ledger_only = set(), True
for row in log_out.splitlines():
    if u"\x1f" not in row:
        continue
    sha_, subj_ = row.split(u"\x1f", 1)
    if R_TAG not in subj_:
        continue
    names, _ = sh([u"git", u"show", u"--name-only", u"--format=", sha_])
    for line in names.splitlines():
        line = line.strip()
        if line:
            touched.add(line)
if not touched:
    die(u"读不到任何 %s 的改动面 ⇒ 不许写「本轮零代码改动」这种话" % R_TAG)
for f in touched:
    if f not in books and not f.startswith(u".scratch/"):
        ledger_only = False
if not ledger_only:
    die(u"本轮是看图轮：除台账与 .scratch 之外不许动任何文件，现读 %s"
        % u", ".join(sorted(f for f in touched if f not in books and not f.startswith(u".scratch/"))))

pc, _rc = sh([sys.executable, PRECHECK])
pre_line = re.findall(r"NEEDLE_PRECHECK tables=(\d+) covered=(\d+) arms=(\d+) bad=(\d+)", pc)
if not pre_line:
    die(u"NEEDLE_PRECHECK 没读到 ⇒ 预检那条腿没跑")
TABLES_N, COVERED, _PA, PRE_BAD = (int(x) for x in pre_line[-1])
if PRE_BAD:
    die(u"针预检 bad=%d ⇒ 有 needle 在册上腐烂" % PRE_BAD)
reg_line = re.findall(r"ARM_TOTAL files=(\d+) arms=(\d+) dupes=(\d+) repeats=(\d+)", pc)
if not reg_line:
    die(u"ARM_TOTAL 没读到")
ARM_FILES, ARM_REG, ARM_DUPES, ARM_REPEATS = (int(x) for x in reg_line[-1])
if ARM_DUPES or ARM_REPEATS:
    die(u"名册报 dupes=%d repeats=%d" % (ARM_DUPES, ARM_REPEATS))

ha_out, ha_rc = sh([sys.executable, HA])
HA_LINE = (re.findall(r"(?m)^HIDDEN_ARMS .+$", ha_out) or [u""])[-1]
if u"处置=ok" not in HA_LINE:
    die(u"腐烂针尺自己没签（rc=%d）：%s" % (ha_rc, HA_LINE[:160]))
ROT_NOW = (re.findall(r"rot=(\d+)", HA_LINE) or [u""])[-1]
OPAQUE_NOW = (re.findall(r"抽不出=(\d+)", HA_LINE) or [u"", u""])[-1]
DECLARED_TBL = int((re.findall(u"已声明表=(\\d+)", HA_LINE) or [u"0"])[-1])
HID_TABLES = int((re.findall(u"未登记表=(\\d+)", HA_LINE) or [u"0"])[-1]) or DECLARED_TBL
REMAIN_TABLES = HID_TABLES - DECLARED_TBL
KNIFE_SUM = (u"本轮 0 把刀、0 代码改动（看图轮）：证人 = runner 自印的 `CARD_INSET_*` 三行 + "
             u"浮层那一格 (181,181,181) vs (255,255,255)；五腿不适用不是没跑")

st_out, st_rc = sh([sys.executable, STREAK, u"--streak-for", s(ROUND)])
STREAK_N = (re.findall(r"streak=(\d+)", st_out) or [u""])[-1]
if st_rc != 0 or not STREAK_N:
    die(u"product_streak 读不到（rc=%d）" % st_rc)
LASTSHA = (re.findall(r"last=(\w+)", st_out) or [u""])[-1]
LASTROUND = (re.findall(r"last_round=(\d+)", st_out) or [u""])[-1]
prev_out, prev_rc = sh([sys.executable, STREAK, u"--streak-for", s(PREV_ROUND)])
PREV_STREAK = (re.findall(r"streak=(\d+)", prev_out) or [u""])[-1]
if prev_rc != 0 or not PREV_STREAK:
    die(u"上一轮的产品面轮数读不到")
ci, _ = sh([sys.executable, os.path.join(ROOT, "scripts", "ci_read.py"), u"latest"])
CI = ci.strip().replace(u"\n", u" ")
if u"RUN=" not in CI:
    die(u"⓪ 的 CI 配对没读到（%s）" % CI[:80])
dk, _ = sh([sys.executable, CURVE])
if (re.findall(r"^GAPS=(\S+)", dk, re.M) or [u""])[-1] != u"none":
    die(u"曲线尺报 GAPS ⇒ 升序台账被插在中间了")
DERIVED = dict((int(a), int(b)) for a, b in
               re.findall(r"(\d+)=(\d+)", (re.findall(r"^SCORES_BY_ROUND (.+)$", dk, re.M) or [u""])[-1])
               ).get(RDN - 1)
if DERIVED is None:
    die(u"曲线仪器没给出上一轮 Round %s 的派生分" % (RDN - 1))

ui = rd(FILES[u"UI"])
U_MAX = max(int(x) for x in re.findall(r"(?m)^- \*\*U-(\d{3,4})[：(]", ui))
UA, UB, UC = U_MAX + 1, U_MAX + 2, U_MAX + 3
dec = rd(FILES[u"DEC"])
DN = max(int(x) for x in re.findall(r"(?m)^\*\*D-(\d{3,4})（", dec)) + 1
bl = rd(FILES[u"BL"])
BL_MAX = max(int(x) for x in re.findall(r"(?m)^\*\*(\d{3})\. ", bl))
if u"**%d. " % NEEDLE_HOUSE not in bl:
    die(u"BACKLOG %d 不在盘上 ⇒ @BLMINUS@ 这个引用会指空" % NEEDLE_HOUSE)
if u"**%d. " % BL_MAX not in bl:
    die(u"BACKLOG 最大那一条（%d）不在盘上" % BL_MAX)

SUBS = {u"@ROUND@": ROUND, u"@RTAG@": R_TAG, u"@RPREVTAG@": PREV_TAG, u"@RNEXT@": R_NEXT,
        u"@RDN@": RDN, u"@TODAY@": TODAY, u"@UA@": UA, u"@UB@": UB, u"@UC@": UC, u"@DN@": DN,
        u"@BLMAX@": BL_MAX, u"@BLMINUS@": NEEDLE_HOUSE, u"@BATT@": pre, u"@SKIP@": pre_skip,
        u"@STREAK@": STREAK_N, u"@PREVSTREAK@": PREV_STREAK, u"@LASTSHA@": LASTSHA,
        u"@LASTROUND@": LASTROUND, u"@CI@": CI, u"@HALINE@": HA_LINE, u"@ROT@": ROT_NOW,
        u"@OPAQUE@": OPAQUE_NOW, u"@HIDTBL@": DECLARED_TBL, u"@HIDTBL2@": REMAIN_TABLES,
        u"@TABLES@": TABLES_N, u"@COVERED@": COVERED, u"@PREBAD@": PRE_BAD,
        u"@ARMREG@": ARM_REG, u"@ARMFILES@": ARM_FILES, u"@KNIFESUM@": KNIFE_SUM}
EYE = fill(EYE, SUBS)
SUBS[u"@EYE@"] = EYE
SUBS[u"@EYE_SHORT@"] = EYE.split(u"⇒")[0].strip()

if not os.path.exists(BODIES):
    die(u"正文文件 %s 不在盘上" % BODIES)
ns = {}
exec(compile(rd(BODIES), BODIES, u"exec"), ns)
for k in (u"UI_NEW", u"IT_NEW", u"DEC_NEW", u"CH_NEW", u"ST_NEW"):
    if k not in ns:
        die(u"正文缺 %s" % k)

orig = {k: rd(v) for k, v in FILES.items()}
for key, marker in ((u"UI", u"## 第 %d 轮" % ROUND), (u"IT", u"## Round %d ·" % RDN),
                    (u"ST", u"## %s 状态（" % R_TAG)):
    if marker in orig[key]:
        die(u"%s 里已经有本轮那一节 ⇒ 生成器不许重跑第二遍" % key)

texts = {u"UI": fill(ns[u"UI_NEW"], SUBS), u"IT": fill(ns[u"IT_NEW"], SUBS),
         u"DEC": fill(ns[u"DEC_NEW"], SUBS), u"CH": fill(ns[u"CH_NEW"], SUBS),
         u"ST": fill(ns[u"ST_NEW"], SUBS)}
for k, t in texts.items():
    hit = STRAY_RX.findall(t)
    if hit:
        die(u"文本 %s 里还有没替换的占位符：%s" % (k, u",".join(sorted(set(hit)))))

heads = [(int(m.group(1)), m.start()) for m in re.finditer(u"(?m)^## 第 (\\d+) 轮", orig[u"UI"])]
top = max(heads)[1]
new_ui = orig[u"UI"][:top] + texts[u"UI"] + orig[u"UI"][top:]
if new_ui.count(u"## 第 %d 轮" % ROUND) != 1:
    die(u"UI_AUDIT 新节没落在最大轮次标题之上")
nums = [int(m.group(1)) for m in re.finditer(u"(?m)^- \\*\\*U-(\\d{3,4})[：(]", texts[u"UI"])]
if nums != [UA, UB, UC]:
    die(u"新节的 U 定义行是 %s，要 %s" % (nums, [UA, UB, UC]))
new_it = orig[u"IT"].rstrip(u"\n") + u"\n\n" + texts[u"IT"].rstrip(u"\n") + u"\n"
if len(re.findall(u"(?m)^\\| (真实视觉审查|判据有效性|假绿防御|产品面推进|台账一致性|交付诚实性|可复核性) \\| (\\d+)/15 \\|$",
                  texts[u"IT"])) != 7:
    die(u"七维表不是恰好 7 行")
new_dec = orig[u"DEC"].rstrip(u"\n") + u"\n\n" + texts[u"DEC"].rstrip(u"\n") + u"\n"
new_bl = orig[u"BL"]          # 本轮不开单、不追记（373 已随看图腿落盘）
new_ch = once(orig[u"CH"], u"## [Unreleased]\n\n", u"## [Unreleased]\n\n" + texts[u"CH"],
              u"CHANGELOG [Unreleased]")
if sum(1 for line in new_ch.split(u"\n") if line.strip() == u"## [Unreleased]") != 1:
    die(u"CHANGELOG 的 [Unreleased] 不再是恰好 1 行")
new_st = once(orig[u"ST"], u"## %s 状态（" % PREV_TAG,
              texts[u"ST"] + u"## %s 状态（" % PREV_TAG, u"STATE 轮换")
if u"## %s 状态（" % PREV_TAG not in new_st or u"## %s 状态（" % R_TAG not in new_st:
    die(u"STATE 轮换后上一轮的标记没了")

fr = orig[u"FR"]
if len(re.findall(u"U-31 … U-\\d+（R\\d+ 现读抬到最新一节）", fr)) != 1:
    die(u"§1 的 U 那一格锚点命中不是 1")
fr = re.sub(u"U-31 … U-\\d+（R\\d+ 现读抬到最新一节）",
            u"U-31 … U-%d（%s 现读抬到最新一节）" % (UC, R_TAG), fr, count=1)
fr = once(fr, u"完整名单以 `AGENT_STATE.md` 的 %s 节 ② 为准" % PREV_TAG,
          u"完整名单以 `AGENT_STATE.md` 的 %s 节 ② 为准" % R_TAG, u"§13 仍开指针")

new = {u"UI": new_ui, u"IT": new_it, u"DEC": new_dec, u"BL": new_bl,
       u"CH": new_ch, u"ST": new_st, u"FR": fr}
for key in (u"UI", u"IT", u"DEC", u"CH", u"ST"):
    if len(new[key]) <= len(orig[key]):
        die(u"%s 写后不比写前长" % key)
stray = [u"%s:%d %s" % (k, n, hit.group(0)) for k, t in new.items()
         for n, line in enumerate(t.split(u"\n"), 1) for hit in STRAY_RX.finditer(line)]
if stray:
    die(u"写盘前有没被替换的占位符（%d 处）：%s" % (len(stray), u"；".join(stray[:6])))
for key, text in new.items():
    wr(FILES[key], text)
WROTE.append(True)


def _crash_guard():
    if WROTE and not OK_EXIT:
        for key, text in orig.items():
            wr(FILES[key], text)
        sys.stderr.write(u"R317_CRASH_RESTORED 未捕获异常 ⇒ 七本已整体还原\n")


atexit.register(_crash_guard)

txt = rd(FILES[u"FR"])
out, crc = sh([sys.executable, CURVE])
rounds_after = (re.findall(r"^ROUNDS=(\d+)", out, re.M) or [u""])[-1]
last_round = (re.findall(r"^PHASE2 n=\d+ rounds=9\.\.(\d+)", out, re.M) or [u""])[-1]
tail = (re.findall(r"^SCORES_BY_ROUND (.+)$", out, re.M) or [u""])[-1]
if not rounds_after or not last_round or not tail:
    die(u"写盘后曲线尺没给全（rc=%d）" % crc)
lines = txt.split(u"\n")
m = re.search(u"R9–R(\\d+)，(\\d+) 节自评", lines[0])
if not m or lines[0].count(u"R9–R") != 1:
    die(u"报告标题那一行没找到 `R9–R<NNN>，<NNN> 节自评`")
lines[0] = lines[0][:m.start()] + u"R9–R%s，%s 节自评" % (last_round, rounds_after) + lines[0][m.end():]
body = u"\n".join(lines)

prod_cell = (u"- **产品面（这一节最该被读的部分）**：本轮产品文件 0 个（**看图轮**：git 现读改动面只有台账，"
             u"零可编译改动 ⇒ 构建 / 全量卷 / 重捕帧 / 帧基线 / 换装五腿**不适用**，不是没跑），"
             u"产品面连续零改动轮数 = **%s**（唯一取数口 `python3 scripts/product_streak.py --streak-for %s`，"
             u"as-of 第 %s 轮的最后一笔产品提交是 %s = 第 %s 轮；上一轮那一格是 %s）。"
             u"看图腿 RUN：新位点 = 快速选择浮层的选中行，选中底 (181,181,181) 对页底 (255,255,255)"
             u" ⇒ 差 74、零强调色，但**同一轮标成这台机器判不了**（离屏非 key window）⇒ 新开 %s。"
             % (STREAK_N, ROUND, ROUND, LASTSHA, LASTROUND, PREV_STREAK, BL_MAX))
scale_cell = (u"- **判据与门的规模**：脚本电池现读 **Ran %s**（写盘后同数），"
              u"变异臂在册 **%s** 把 / %s 张表（预检 tables=%s covered=%s bad=%s）；"
              u"腐烂针尺现读 `%s`；U 定义行 **%s 条**、最大 **U-%s**；决定台账最大 **D-%s**，"
              u"BACKLOG 最大 **%s**（本轮不开单、不追记 —— 373 已随看图腿落盘）"
              % (pre, ARM_REG, ARM_FILES, TABLES_N, COVERED, PRE_BAD, HA_LINE,
                 len(re.findall(u"(?m)^- \\*\\*U-(\\d{3,4})[：(]", new_ui)), UC, DN, BL_MAX))
where_cell = (u"- **走到哪了**：阶段二累计 `## Round` 节 **%s** 节，最新一节是 **Round %s**；"
              u"自评曲线按轮现读 %s（现读 `curve_from_ledger.py`）。派生分连续多轮低于 90 "
              u"⇒ 按目标继续修，不收口。" % (rounds_after, last_round, tail))
for label, cell in ((u"产品面（这一节最该被读的部分）", prod_cell),
                    (u"判据与门的规模", scale_cell), (u"走到哪了", where_cell)):
    parts = body.split(u"\n")
    hits = [i for i, l in enumerate(parts) if l.startswith(u"- **%s**：" % label)]
    if len(hits) != 1:
        die(u"§13 的「%s」那一格命中 %d 行" % (label, len(hits)))
    parts[hits[0]] = fill(cell, SUBS)
    body = u"\n".join(parts)
if STRAY_RX.search(body):
    die(u"报告刷新后还有没替换的占位符：%s" % STRAY_RX.findall(body)[:4])
wr(FILES[u"FR"], body)
rf, rfc = sh([sys.executable, os.path.join(ROOT, ".scratch", "motion-audit-2",
                                           "refresh_report_section1.py")])
if rfc != 0 or u"REFUSED" in rf:
    die(u"§1 那一格的刷新器没签（rc=%d）：%s" % (rfc, rf.strip()[-200:]))

post, post_skip = battery(u"写盘后", u"/tmp/r317_battery_post.log")
if (post, post_skip) != (pre, pre_skip):
    die(u"电池计数变了（%s/%s → %s/%s）" % (pre, pre_skip, post, post_skip))
ck, crc = sh([sys.executable, STREAK, u"--check"])
if crc != 0:
    die(u"353 的门不认这版台账：" + (ck + u"\n").strip()[-400:])
cv2, _ = sh([sys.executable, CURVE])
if (re.findall(r"^GAPS=(\S+)", cv2, re.M) or [u""])[-1] != u"none":
    die(u"写盘后曲线尺报缺口")
DERIVED2 = dict((int(a), int(b)) for a, b in
                re.findall(r"(\d+)=(\d+)", (re.findall(r"^SCORES_BY_ROUND (.+)$", cv2, re.M) or [u""])[-1])
                ).get(RDN)
if DERIVED2 is None:
    die(u"写盘后曲线尺没给出本轮 Round %s 的派生分" % RDN)
if u"R9–R%s" % last_round not in rd(FILES[u"FR"]).split(u"\n")[0]:
    die(u"报告标题没接上写盘后的尾轮 Round %s" % last_round)
if u"U-31 … U-%d" % UC not in rd(FILES[u"FR"]):
    die(u"报告 §1 的 U 上界不是本轮的 U-%d" % UC)

OK_EXIT.append(True)
print(u"LEDGERS_R317 OK batt=Ran " + post + u" (skipped=" + post_skip + u") streak=" + STREAK_N
      + u"(上一轮 " + PREV_STREAK + u") 改动面=" + s(len(touched))
      + u" 预检bad=" + s(PRE_BAD) + u" 在册=" + s(ARM_REG) + u"/" + s(ARM_FILES) + u"表 rot=" + s(ROT_NOW)
      + u" 抽不出=" + s(OPAQUE_NOW) + u" U=" + s(UA) + u".." + s(UC) + u" D=" + s(DN)
      + u" BL最大=" + s(BL_MAX) + u" derived(Round " + s(RDN) + u")=" + s(DERIVED2)
      + u" report尾轮=Round " + s(last_round) + u" 节数=" + s(rounds_after))

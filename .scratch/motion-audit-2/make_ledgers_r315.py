# -*- coding: utf-8 -*-
u"""从 `ledgers_r314.py` 机械派生 `ledgers_r315.py`，并顺手补 `r315_bodies.txt` 的两处占位符笔误。

为什么用派生而不是复制：R314/R315 是同一族判据轮，生成器的骨架（现读 → 闸门 → 七本 → 写盘后对账）
一个字都不该漂；漂了的那部分必须是**本轮特有**的读数门。每一处替换都断言命中次数，
命中数不对就在写盘之前抱出（与台账生成器同一条地基）。
"""
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "ledgers_r314.py")
DST = os.path.join(HERE, "ledgers_r315.py")
BODIES = os.path.join(HERE, "r315_bodies.txt")

# (旧, 新, 期望命中次数)
PAIRS = [
    (u'u"""R314 的七本台账（第 313 轮 / Round 311 · 判据轮：空态补组合状态臂 + 自曝重复臂）。',
     u'u"""R315 的七本台账（第 314 轮 / Round 312 · 判据轮：撤销重复单 + 补同族对照 + 撤重复臂）。', 1),
    (u'BODIES = os.path.join(ROOT, ".scratch", "motion-audit-2", "r314_bodies.txt")',
     u'BODIES = os.path.join(ROOT, ".scratch", "motion-audit-2", "r315_bodies.txt")', 1),
    (u'CHAIN = u"/tmp/r314_chain.log"', u'CHAIN = u"/tmp/r315_chain.log"', 1),
    (u'TODAY = u"2026-10-23"', u'TODAY = u"2026-10-24"', 1),
    (u'R_TAG, PREV_TAG, R_NEXT = u"R314", u"R313", u"R315"',
     u'R_TAG, PREV_TAG, R_NEXT = u"R315", u"R314", u"R316"', 1),
    (u'PREV_ROUND, ROUND, RDN = 312, 313, 311', u'PREV_ROUND, ROUND, RDN = 313, 314, 312', 1),
    (u'prog="ledgers_r314.py"', u'prog="ledgers_r315.py"', 1),
    (u'R314 的七本台账（判据轮）', u'R315 的七本台账（判据轮）', 1),
    (u'R314_EYE', u'R315_EYE', 3),
    (u'R314_LEDGERS_REFUSE', u'R315_LEDGERS_REFUSE', 1),
    (u'R314_RESTORED', u'R315_RESTORED', 1),
    (u'R314_CRASH_RESTORED', u'R315_CRASH_RESTORED', 1),
    (u'LEDGERS_R314 OK', u'LEDGERS_R315 OK', 1),
    (u'u"/tmp/r314_battery_pre.log"', u'u"/tmp/r315_battery_pre.log"', 1),
    (u'u"/tmp/r314_battery_post.log"', u'u"/tmp/r315_battery_post.log"', 1),
    # ---- 正文键：BL_368 追记 → BL_370 追记；三张新单 → 一张
    (u'for k in (u"UI_NEW", u"IT_NEW", u"DEC_NEW", u"BL_368", u"BL_NEW", u"BL_NEW2", u"BL_NEW3",\n'
     u'          u"CH_NEW", u"ST_NEW"):',
     u'for k in (u"UI_NEW", u"IT_NEW", u"DEC_NEW", u"BL_370", u"BL_NEW", u"CH_NEW", u"ST_NEW"):', 1),
    (u'u"BL368": fill(ns[u"BL_368"], SUBS),', u'u"BL370": fill(ns[u"BL_370"], SUBS),', 1),
    (u'         u"BLNEW": fill(ns[u"BL_NEW"], SUBS), u"BLNEW2": fill(ns[u"BL_NEW2"], SUBS),\n'
     u'         u"BLNEW3": fill(ns[u"BL_NEW3"], SUBS), u"CH": fill(ns[u"CH_NEW"], SUBS),',
     u'         u"BLNEW": fill(ns[u"BL_NEW"], SUBS), u"CH": fill(ns[u"CH_NEW"], SUBS),', 1),
    (u'new_bl = append_into_item(orig[u"BL"], u"**368. ", texts[u"BL368"], u"368")',
     u'new_bl = append_into_item(orig[u"BL"], u"**370. ", texts[u"BL370"], u"370")', 1),
    (u'for key in (u"BLNEW", u"BLNEW2", u"BLNEW3"):\n    n = SUBS[u"@%s@" % key]',
     u'for key in (u"BLNEW",):\n    n = SUBS[u"@%s@" % key]', 1),
    (u'        len(re.findall(u"(?m)^\\\\*\\\\*\\\\d{3}\\\\. ", orig[u"BL"])) + 3:',
     u'        len(re.findall(u"(?m)^\\\\*\\\\*\\\\d{3}\\\\. ", orig[u"BL"])) + 1:', 1),
    (u'die(u"BACKLOG 条目头数量不是「原数 +3」⇒ 三张新单没落成三条")',
     u'die(u"BACKLOG 条目头数量不是「原数 +1」⇒ 新单没落成一条")', 1),
    (u'BLNEW, BLNEW2, BLNEW3 = BL_MAX + 1, BL_MAX + 2, BL_MAX + 3',
     u'BLNEW = BL_MAX + 1', 1),
    (u'if u"**368. " not in bl:\n    die(u"BACKLOG 368 不在盘上 ⇒ 本轮的追记无处可挂")',
     u'if u"**370. " not in bl:\n    die(u"BACKLOG 370 不在盘上 ⇒ 本轮的结案追记无处可挂")', 1),
    (u'u"@BLNEW@": BLNEW, u"@BLNEW2@": BLNEW2, u"@BLNEW3@": BLNEW3,\n'
     u'        u"@BLMAX@": BLNEW3, u"@BLMINUS@": BL_MAX,',
     u'u"@BLNEW@": BLNEW, u"@BLMAX@": BLNEW, u"@BLMINUS@": BL_MAX,', 1),
    # ---- 本轮特有的读数门：没有"两次捕获"，证人改成「撤帧那一笔的四件现读」
    (u'cap_block = chain[chain.find(u"### CAPTURE"):chain.find(u"### FRAMES")]\n'
     u'm1 = re.search(u"R314_CAPTURE1 红=(\\\\d+)", cap_block)\n'
     u'm2 = re.search(u"R314_CAPTURE2 (.+?) 红=(\\\\d+)", cap_block, re.S)\n'
     u'if not m1 or not m2:\n'
     u'    die(u"读不到两次捕获的结论行 ⇒ 本轮的证人不在盘上：%s" % cap_block[:160])\n'
     u'CAP1_REDS, CAP2_REDS = int(m1.group(1)), int(m2.group(2))\n'
     u'CAP2_LINE = (re.findall(r"(?m)^CAPTURED .+$", cap_block) or [u"没读到 CAPTURED 行"])[-1]\n'
     u'if CAP1_REDS < 1:\n'
     u'    die(u"第一跑零红 ⇒ 那两处名册缺口根本没被顶出来，第二跑的绿不说明任何事")\n'
     u'if CAP2_REDS:\n'
     u'    die(u"登记之后仍红 %d 朵 ⇒ 不许出账" % CAP2_REDS)\n'
     u'ICONS = (re.findall(u"R314_CAPTURE1_ICON_FIRST=(\\\\d+) 行", cap_block) or [u"0"])[-1]\n'
     u'KNIFE_SUM = (u"本轮 0 把新刀（判断，不是遗漏）：证人 = 同一轮两次捕获，第一跑红 %d 朵 → 登记后第二跑零红且 %s；"\n'
     u'             u"名册被删任何一条，下一次就红" % (CAP1_REDS, CAP2_LINE))',
     u'cap_block = chain[chain.find(u"### CAPTURE"):chain.find(u"### FRAMES")]\n'
     u'm1 = re.search(u"R315_REDS 红=(\\\\d+)", cap_block)\n'
     u'm2 = re.search(u"R315_M566 (ok|bad|没)", cap_block)\n'
     u'if not m1 or not m2:\n'
     u'    die(u"读不到本轮捕获结论行或 M566 那一臂的预检 ⇒ 证人不在盘上：%s" % cap_block[:160])\n'
     u'CAP_REDS, M566_STATE = int(m1.group(1)), m2.group(1)\n'
     u'CAP2_LINE = (re.findall(r"(?m)^CAPTURED .+$", cap_block) or [u"没读到 CAPTURED 行"])[-1]\n'
     u'if CAP_REDS:\n'
     u'    die(u"撤帧之后捕获卷仍红 %d 朵 ⇒ 不许出账" % CAP_REDS)\n'
     u'if M566_STATE != u"ok":\n'
     u'    die(u"针预检里 M566 不是 ok（现读 %s）⇒ 名册形状与针不同源" % M566_STATE)\n'
     u'ICONS = (re.findall(u"R315_ICON_FIRST=(\\\\d+) 行", cap_block) or [u"0"])[-1]\n'
     u'KNIFE_SUM = (u"本轮 0 把新刀（判断，不是遗漏）：证人 = 撤帧那一笔的四件现读 —— "\n'
     u'             u"%s、捕获卷零红、M566 预检 ok（针跟着名册回到单行）、基线同一笔 update" % CAP2_LINE)', 1),
    (u'for needle, label in ((u"### BUILD", u"构建"), (u"### CAPTURE", u"两次捕获"),\n'
     u'                      (u"### FRAMES", u"帧目录计数"), (u"### MD5", u"重复臂对拍"),\n'
     u'                      (u"### EMPTY_INK", u"空态墨带"), (u"### PRECHECK", u"针预检"),',
     u'for needle, label in ((u"### BUILD", u"构建"), (u"### CAPTURE", u"撤帧后的捕获卷"),\n'
     u'                      (u"### FRAMES", u"帧目录计数"), (u"### PANE", u"逐分区留白对照"),\n'
     u'                      (u"### EMPTY_INK", u"空态墨带"), (u"### PRECHECK", u"针预检"),', 1),
    (u'MD5_SAME = (re.findall(u"两档全等=(\\\\w+)", chain) or [u"no"])[-1]\n'
     u'if MD5_SAME != u"yes":\n'
     u'    die(u"重复臂对拍没给出「两档全等=yes」⇒ U 里那句自曝没有证人（现读 %s）" % MD5_SAME)\n'
     u'INK_ROWS = [l for l in chain.splitlines() if l.startswith(u"EMPTY_INK ")]\n'
     u'if len(INK_ROWS) < 3:\n'
     u'    die(u"空态墨带读数不足 3 行 ⇒ 0.533 / 0.252 那两个数没有证人")\n'
     u'INK_PAIR = (re.findall(u"R314_INK_PAIR .+$", chain) or [u""])[-1]',
     u'PANE_ROWS = [l for l in chain.splitlines() if l.startswith(u"PANE_INK settings-")]\n'
     u'if len(PANE_ROWS) < 7:\n'
     u'    die(u"逐分区留白读数不足 7 行 ⇒ U 里那句「不是异类」没有证人（现读 %d 行）" % len(PANE_ROWS))\n'
     u'INK_ROWS = [l for l in chain.splitlines() if l.startswith(u"EMPTY_INK ")]\n'
     u'if len(INK_ROWS) < 3:\n'
     u'    die(u"空态墨带读数不足 3 行 ⇒ 0.533 / 0.252 那两个数没有证人")\n'
     u'INK_PAIR = (re.findall(u"R315_PANE_DONE .+$", chain) or [u""])[-1]', 1),
    (u'if u"FRAME_BASELINE_COMPARED=176" not in BASE_ROWS or u"FRAME_BASELINE_CHANGED=0" not in BASE_ROWS:',
     u'if u"FRAME_BASELINE_COMPARED=174" not in BASE_ROWS or u"FRAME_BASELINE_CHANGED=0" not in BASE_ROWS:', 1),
    (u'die(u"帧基线对账没给出 COMPARED=176 / CHANGED=0 ⇒ 新增那两张帧没有同一笔基线证人：%s"\n'
     u'        % BASE_ROWS.strip()[:200])',
     u'die(u"帧基线对账没给出 COMPARED=174 / CHANGED=0 ⇒ 撤帧那一笔没有同一笔基线证人：%s"\n'
     u'        % BASE_ROWS.strip()[:200])', 1),
    # ---- 报告那一格里本轮特有的措辞：那一格跨三行、缩进易漂，改用 main 里的 POST 正则整段换
    (u'u"（唯一取数口 `python3 scripts/product_streak.py --streak-for %s`，as-of 第 %s 轮的最后一笔"\n'
     u'             u"产品提交是 %s = 第 %s 轮；上一轮那一格是 %s）。看图腿 RUN：重捕 %s 张、帧基线 %s"\n'
     u'             u"（新增两张 empty 帧，**同一笔 update**）；换装 %s。',
     u'u"（唯一取数口 `python3 scripts/product_streak.py --streak-for %s`，as-of 第 %s 轮的最后一笔"\n'
     u'             u"产品提交是 %s = 第 %s 轮；上一轮那一格是 %s）。看图腿 RUN：重捕 %s 张、帧基线 %s"\n'
     u'             u"（撤掉两张重复帧，**同一笔 update**）；换装 %s。', 1),
    (u'u"U 定义行 **%s 条**、最大 **U-%s**；决定台账最大 **D-%s**，BACKLOG 最大 **%s**"\n'
     u'              u"（本轮追记 %s、新开 %s/%s/%s）"',
     u'u"U 定义行 **%s 条**、最大 **U-%s**；决定台账最大 **D-%s**，BACKLOG 最大 **%s**"\n'
     u'              u"（本轮追记 370/371、新开 %s）"', 1),
    (u'% (pre, ARM_REG, ARM_FILES, TABLES_N, COVERED, PRE_BAD, HID_TABLES, HID_ARMS, HA_LINE,\n'
     u'                 len(re.findall(u"(?m)^- \\\\*\\\\*U-(\\\\d{3,4})[：(]", new_ui)), UD, DN, BLNEW3,\n'
     u'                 BL_MAX, BLNEW, BLNEW2, BLNEW3))',
     u'% (pre, ARM_REG, ARM_FILES, TABLES_N, COVERED, PRE_BAD, HID_TABLES, HID_ARMS, HA_LINE,\n'
     u'                 len(re.findall(u"(?m)^- \\\\*\\\\*U-(\\\\d{3,4})[：(]", new_ui)), UD, DN, BLNEW,\n'
     u'                 BLNEW))', 1),
    (u'u" 捕获1红=" + s(CAP1_REDS) + u" 捕获2红=" + s(CAP2_REDS)',
     u'u" 捕获红=" + s(CAP_REDS) + u" M566=" + M566_STATE', 1),
    (u'+ u" U=" + s(UA) + u".." + s(UD) + u" D=" + s(DN) + u" BL=" + s(BLNEW) + u".." + s(BLNEW3)',
     u'+ u" U=" + s(UA) + u".." + s(UD) + u" D=" + s(DN) + u" BL=" + s(BLNEW)', 1),
]

BODIES_FIX = [
    (u'@BLNEW@-1（`iconFirstCells` 自指 = 369，本轮第二次咬合作为证人）',
     u'369（`iconFirstCells` 自指 —— 本轮 M566 的针第二次被同一张名册咬，就是它的证人）', 1),
    (u'这就是 @BLMINUS@-1 那张单（369：名册手写且自指）要的证人',
     u'这就是 369 那张单（名册手写且自指）要的证人', 1),
]


def apply(text, pairs, label):
    bad = []
    for old, new, want in pairs:
        n = text.count(old)
        if n != want:
            bad.append(u"%s 锚命中 %d（要 %d）：%r" % (label, n, want, old[:80]))
            continue
        text = text.replace(old, new)
    if bad:
        sys.stderr.write(u"\n".join(bad) + u"\n")
        sys.exit(1)
    return text


def main():
    src = io.open(SRC, encoding="utf-8").read()
    src = apply(src, PAIRS, u"生成器")
    post = [
        (re.compile(u'本轮最该被读的一格是自曝：.*?产品侧缺席单 %s。', re.S),
         u'本轮最该被读的一格是撤销：@RPREVTAG@ 自己开的缺席单 371 被查重撤掉（R9 的决定 + 已有判据 + 同族不离群），'
         u'并把 @RPREVTAG@ 自曝的那张重复臂拿走（帧基线 176→174 同一笔 update）；新开 %s。', 1),
        (re.compile(r'INSTALL_LINE, BLNEW3\)\)'), u'INSTALL_LINE, BLNEW))', 1),
        (re.compile(u'R314_LOAD_RED'), u'R315_LOAD_RED', 2),
    ]
    for rx, rep, want in post:
        n = len(rx.findall(src))
        if n != want:
            sys.stderr.write(u"POST 正则命中 %d 次（要 %d）：%s\n" % (n, want, rx.pattern[:50]))
            sys.exit(1)
        src = rx.sub(rep, src)
    leftovers = [l for l in src.split(u"\n")
                 if re.search(u"R314|BLNEW2|BLNEW3|CAP1_REDS|MD5_SAME", l)
                 and u'PREV_TAG, R_NEXT' not in l]
    if leftovers:
        sys.stderr.write(u"派生物里还留着上一轮的东西（%d 行）：\n%s\n"
                         % (len(leftovers), u"\n".join(x.strip()[:120] for x in leftovers[:6])))
        sys.exit(1)
    io.open(DST, "w", encoding="utf-8").write(src)
    compile(src, DST, "exec")
    b = io.open(BODIES, encoding="utf-8").read()
    b = apply(b, BODIES_FIX, u"正文")
    io.open(BODIES, "w", encoding="utf-8").write(b)
    stray = sorted(set(re.findall(u"@([A-Z][A-Z0-9_]{1,24})@", b)))
    known = set(u"ROUND RTAG RPREVTAG RNEXT RDN TODAY UA UB UC UD DN BLNEW BLMAX BLMINUS BATT SKIP "
                u"STREAK PREVSTREAK LASTSHA LASTROUND CI JUDGERUN JUDGEFAIL WARN PREBAD TABLES COVERED "
                u"ARMREG ARMFILES FRAMES HALINE ROT OPAQUE JUDGED HIDTBL HIDTBL2 FULL CAP BASE INSTALL "
                u"KNIFESUM EYE EYE_SHORT INKPAIR PANE NOFILES RDLINE TSCANNED RUNNER HIDTABLES HIDARMS".split())
    if not set(stray) <= known:
        sys.stderr.write(u"正文里有没登记进 SUBS 的占位符：%s" % sorted(set(stray) - known))
        sys.exit(1)
    print(u"R315_MADE 生成器=%s 正文占位符=%d 全部已登记" % (os.path.basename(DST), len(stray)))
    return 0


if __name__ == u"__main__":
    sys.exit(main())

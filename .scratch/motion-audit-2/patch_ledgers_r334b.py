# -*- coding: utf-8 -*-
"""给 ledgers_r334.py 打第 2 版补丁（标签第二来源那一格）。

为什么用补丁而不是手改：这个文件里有七处 `%` 格式串，占位符与参数**按位置**配对，
手改一处漏一个参数 = 整批在落盘之前 TypeError（那还好），或者更坏：数串到别的句子里去（没人看得见）。
所以每一处替换都带 `assert count == 1`，且新加的那一段先 ast.parse 再落盘。
"""
import ast
import io
import sys

P = u"/Users/wangziyi/Codex_Project0/.scratch/motion-audit-2/ledgers_r334.py"
t = io.open(P, encoding=u"utf-8").read()
n = 0


def rep(old, new, times=1):
    global t, n
    c = t.count(old)
    if c != times:
        print(u"PATCH_R334B_DIED 锚点命中 %d 次（要 %d 次）：%s" % (c, times, old[:70]))
        sys.exit(1)
    t = t.replace(old, new)
    n += 1


# ① 区间上界：本轮有 7 条 U（1110…1116），标题里不能再写 UE（=1114）。
rep(u'% (AUDIT_N, ROUND, DATE, UA, UE, UA, UE))',
    u'% (AUDIT_N, ROUND, DATE, UA, UMAX, UA, UMAX))')
rep(u'u"（R%d / U-%d…U-%d · 产品 2 文件，动效主线）" % (ROUND, UA, UE))',
    u'u"（R%d / U-%d…U-%d · 产品 2 文件，动效主线）" % (ROUND, UA, UMAX))')
rep(u"BATT, ARM_TOTAL[1], ARM_TOTAL[0], PRE[0], PRE[1], PRE[2], udefs, UE, D1, B_LIGHT,\n"
    u"                B_REG, B_LIGHT, ARMS_NEW[0]",
    u"BATT, ARM_TOTAL[1], ARM_TOTAL[0], PRE[0], PRE[1], PRE[2], udefs, UMAX, D1, B_LIGHT,\n"
    u"                B_REG, B_LIGHT, ARMS_NEW[0]")
rep(u'      + u" U=" + s(UA) + u".." + s(UE)', u'      + u" U=" + s(UA) + u".." + s(UMAX)')

# ② 新增四个现读量（不许手抄 14 / 0 / 8）。
rep(u"""if None in (STREAK_N, STREAK_GIT):
    die(u"读不到产品面连读的数：" + st_cell.strip()[-200:])""",
    u"""if None in (STREAK_N, STREAK_GIT):
    die(u"读不到产品面连读的数：" + st_cell.strip()[-200:])

# R334b：标签的第二个来源**改了历史那一格的读数** ⇒ 四个数全部现读，一个都不许手抄。
st_prev_prev, _ = sh([sys.executable, STREAK, u"--streak-for", s(ROUND - 2)])
PREV_NOW = (re.findall(r"streak=(\\d+)", st_prev_prev) or [None])[-1]      # 同一颗尺现在对上一轮答几
der_txt, der_rc = sh([sys.executable, STREAK])
RECOVERED = (re.findall(u"标签补自台账=(\\\\d+)", der_txt) or [None])[-1]
prev_sec = re.search(u"(?m)^## R%d 状态.*?(?=\\n## R|\\\\Z)" % (ROUND - 1), rd(STA), re.S)
PREV_CELL = None
if prev_sec:
    PREV_CELL = (re.findall(u"连续零改动[ \\\\t]*\\\\*\\\\*(\\\\d+)\\\\*\\\\*[ \\\\t]*轮",
                            prev_sec.group(0)) or [None])[0]
if None in (PREV_NOW, RECOVERED, PREV_CELL):
    die(u"标签第二来源那三格读不到：PREV_NOW=%s RECOVERED=%s PREV_CELL=%s"
        % (PREV_NOW, RECOVERED, PREV_CELL))
if PREV_CELL == PREV_NOW:
    die(u"上一轮那一格（%s）与今天同一颗尺的回答（%s）相同 ⇒ 第二来源没有改变任何数，"
        u"那 U-1116 的『豁免只买不红』那句就没有证人，先查为什么" % (PREV_CELL, PREV_NOW))""")

# ③ UI_BODY 追加第 7 条。
rep(u"""  三张表本轮全部重跑：`%s`。
- **U-%d：§8 的搬运名单缺整族 `HOVER_`""",
    u"""  三张表本轮全部重跑：`%s`。
- **U-%d：豁免只买"不红"，买不到"数对" ⇒ 给 `product_streak` 加了标签的**第二个来源**（D-%d）** ——
  R334 第一版收口只在 `test_commit_subject_hygiene` 里登记了一张名单，而 `product_streak.py` 是另一颗尺：
  它要的是**分界**，红只是它的症状，缺了标签它照样给出一个数 —— 现读 `--streak-for 333` 当时答 **15**，
  而真值是 **1**。所以这里不写 sha→轮次的手抄表，改成**派生**：subject 里那一段 U 区间
  （`U-1105…U-1109`）与台账节标题里那一段是同一个串 ⇒ 命中唯一一节就是那一轮；
  多段区间 / 台账没有那一节 / 一节都对不上 ⇒ 一律 None，照旧红。现读 %s 笔产品提交的标签由此补上。
  **代价要写清**：同一颗尺对上一轮（第 332 轮）的回答从 `%s` 变成 `%s` —— 那一格是旧口径的真实读数，
  不改写它（用后来才有的尺重判历史 = 另一种假账），只在这里记下它为什么与今天的派生不同。
- **U-%d：§8 的搬运名单缺整族 `HOVER_`""")
rep(u"""       UD, UE, by_name[u"mutate_r230"][1] + u", RESTORE_CLEAN=yes", TABLE_SUMMARY,
       UF, B_ROSTER, HOVER_NAMES, HOVER_N, B_ROSTER)""",
    u"""       UD, UE, by_name[u"mutate_r230"][1] + u", RESTORE_CLEAN=yes", TABLE_SUMMARY,
       UG, D2, RECOVERED, PREV_CELL, PREV_NOW,
       UF, B_ROSTER, HOVER_NAMES, HOVER_N, B_ROSTER)""")

# ④ D 号：本轮立两条（D-328 subject 豁免、D-329 第二来源）。
rep(u"D1 = 328\n", u"D1 = 328\nD2 = 329\n")

# ⑤ 追加 D-329 正文（DECISIONS 一次写两条）。
rep(u"""另一条教训同时写进 Skill：**消息形状以守卫为准**，写之前 `git log --oneline -3` 现抄 ——
文档里的形状过期了，红的是执行文档的那个人。
\"\"\" % (D1, ROUND)""",
    u"""另一条教训同时写进 Skill：**消息形状以守卫为准**，写之前 `git log --oneline -3` 现抄 ——
文档里的形状过期了，红的是执行文档的那个人。

**D-%d（%d）：豁免必须接管被豁免那条判据要算的**那个量**，否则它把"红"换成"一个安静的错数"**
：D-328 那张名单落盘之后电池还是红的，而这一次的红比红更坏 —— `product_streak.py` 不是"另一条守卫"，
它是那一格的**唯一取数口**。subject 缺「第 N 轮」时它不报错也不空着：它跳过那一笔，
拿**更早**的产品提交当分界，于是 `--streak-for 333` 答 15（真值 1）。
如果 R334 只把 hygiene 那条买通，台账里就会出现一个**没有红、也没有依据**的数。
⇒ 规矩：给一条判据加豁免时，必须同时回答"被它算出来的那个量怎么办"。这一轮的答法是
**第二个来源**（subject 里的 U 区间 ↔ 台账节标题里的 U 区间，唯一命中才算，歧义一律 None），
而不是手抄的 sha→轮次表 —— 表要有退场条件，派生不需要（它自己会随区间消失而消失）。
配套：`derive()` 现在把 `标签补自台账=N(名单)` 原样印出来，第二来源不许是静默的。
\"\"\" % (D1, ROUND, D2, ROUND)""")

# ⑥ §13 的规模那一格：D 号上界改成 D-329。
rep(u"BATT, ARM_TOTAL[1], ARM_TOTAL[0], PRE[0], PRE[1], PRE[2], udefs, UMAX, D1, B_LIGHT,",
    u"BATT, ARM_TOTAL[1], ARM_TOTAL[0], PRE[0], PRE[1], PRE[2], udefs, UMAX, D2, B_LIGHT,")

# ⑦ STATE 里那句错的连读解释（"本来就是 0"）换成第二来源的真话。
rep(u"""产品面连续零改动 **%s** 轮（唯一取数口 `python3 scripts/product_streak.py --streak-for %d`，`--check` 同形；
本轮这一笔按 `--streak-for %d` 现读是 %s —— R333/R334 两笔都是产品提交，所以这一格本来就是 0）。""",
    u"""产品面连续零改动 **%s** 轮（唯一取数口 `python3 scripts/product_streak.py --streak-for %d`，`--check` 同形；
本轮这一笔按 `--streak-for %d` 现读是 %s，要等 commit 之后 git 才把本轮算进分界）。
这一格本轮换了口径：subject 缺「第 N 轮」时不再跳过那一笔，而是问第二个来源（台账节标题里的同一段 U 区间），
现读 %s 笔产品提交的标签由此补上 —— 同一颗尺对上一轮的回答因此从 **%s** 变成 **%s**
（U-%d / D-%d：豁免只买"不红"，买不到"数对"）。上一轮那一格不改写，它是旧口径的真实读数。""")
rep(u"""       STREAK_N, s(ROUND - 1), ROUND, STREAK_GIT, ROUND + 1)""",
    u"""       STREAK_N, s(ROUND - 1), ROUND, STREAK_GIT, RECOVERED, PREV_CELL, PREV_NOW, UG, D2,
       ROUND + 1)""")

# ⑧ ITERATION 正文：把这件事讲给读迭代账的人。数字不许手抄 ⇒ 先单独格式化成一个串，
#    再在正文里占一个 `%s`（参数表里对应位置加 `D329_PROSE`）。
rep(u"""TABLE_SUMMARY = u"；".join(u"%s %s（%s）" % (n, c, a) for n, c, a, _ in TABLE_ROWS)""",
    u"""TABLE_SUMMARY = u"；".join(u"%s %s（%s）" % (n, c, a) for n, c, a, _ in TABLE_ROWS)

D329_PROSE = (u"而 R334 的第一版收口是**不够的**：我只给 `test_commit_subject_hygiene` 登记了豁免，"
              u"`product_streak.py` 却照样答出一个数（`--streak-for 333` 当时答 15，真值 1）"
              u" —— 豁免把红换成了安静的错数。第二版把缺的那颗标签改成**派生**"
              u"（subject 的 U 区间 ↔ 台账节标题的 U 区间，唯一命中才算），现读 **%s** 笔产品提交的标签由此补上；"
              u"代价是同一颗尺对上一轮那一格的回答从 **%s** 变成 **%s** —— 那一格不改写（U-1116 / D-329）。") \\
    % (RECOVERED, PREV_CELL, PREV_NOW)""")
rep(u"""第三笔在工具上：§8 的搬运名单里**从来没有 `HOVER_` 这一支""",
    u"""%s
第三笔在工具上：§8 的搬运名单里**从来没有 `HOVER_` 这一支""")
rep(u"""       B_REG, B_LIGHT, B_LIGHT)""", u"""       B_REG, D329_PROSE, B_LIGHT, B_LIGHT)""")

# ⑨ CHANGELOG：加一条工具/判据的 bullet（无占位符 ⇒ 不动参数表）。
rep(u"""- 梯子守卫红了一次并补上：""",
    u"""- 收口的第二版（判据面）：登记式豁免只买"不红"、买不到"数对" —— `product_streak.py` 在 subject 缺
  「第 N 轮」时会跳过那一笔、拿更早的提交当分界，于是 `--streak-for 333` 答 15（真值 1）。
  本轮给它加了标签的**第二个来源**：subject 里的 U 区间 ↔ 台账节标题里的 U 区间，唯一命中才算，
  歧义一律 None 照旧红；现读 %s 笔补上，并把 `标签补自台账=N(名单)` 原样印出来（不静默）。D-329。
- 梯子守卫红了一次并补上：""")
rep(u"""       STEP.get(u"light idle(0.000)->pillHover(0.045)", u"?"),
       STEP.get(u"dark idle(0.000)->pillHover(0.045)", u"?"),
       STEP.get(u"light pillHover(0.045)->pressed(0.120)", u"?"),
       STEP.get(u"dark pillHover(0.045)->pressed(0.120)", u"?"),
       HOVER_NAMES, HOVER_N, B_ROSTER, UF,""",
    u"""       RECOVERED,
       STEP.get(u"light idle(0.000)->pillHover(0.045)", u"?"),
       STEP.get(u"dark idle(0.000)->pillHover(0.045)", u"?"),
       STEP.get(u"light pillHover(0.045)->pressed(0.120)", u"?"),
       STEP.get(u"dark pillHover(0.045)->pressed(0.120)", u"?"),
       HOVER_NAMES, HOVER_N, B_ROSTER, UF,""")

ast.parse(t)
io.open(P, "w", encoding="utf-8").write(t)
print(u"PATCH_R334B_OK 替换=%d 处 行数=%d" % (n, t.count(u"\n") + 1))

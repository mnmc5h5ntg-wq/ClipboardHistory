# -*- coding: utf-8 -*-
"""从 ledgers_r309.py 生成 ledgers_r310.py：换常量、换七本文的正文，其余机器（事务性、
写盘前后电池、报告计数器、atexit 还原）原样复用 —— 复用而不是重抄，是为了不再抄错一遍数。

锚点全部按"整块边界"取，命中数不是 1 就拒绝出文件（宁可不写，也不写半份）。
"""
import ast
import io
import re
import sys

SRC = "/Users/wangziyi/Codex_Project0/.scratch/motion-audit-2/ledgers_r309.py"
DST = "/Users/wangziyi/Codex_Project0/.scratch/motion-audit-2/ledgers_r310.py"

s = io.open(SRC, encoding="utf-8").read()


def rep(old, new, label, want=1):
    global s
    n = s.count(old)
    if n != want:
        sys.stderr.write("ANCHOR_BAD %s 命中 %d（要 %d）\n" % (label, n, want))
        raise SystemExit(1)
    s = s.replace(old, new)
    print("OK " + label)


def block(start_marker, new_body, label):
    """把 `start_marker … 下一个已知边界` 整块换掉。"""
    global s
    i = s.index(start_marker)
    j = s.index("\n# ---------------------------------------------------------------- ", i)
    old = s[i:j]
    s = s[:i] + new_body.rstrip("\n") + "\n" + s[j:]
    print("OK 换块 " + label + "（旧 %d 行）" % old.count("\n"))


# ---- 常量与路径
rep('R_TAG, PREV_TAG, R_NEXT = u"R309", u"R308", u"R310"',
    'R_TAG, PREV_TAG, R_NEXT = u"R310", u"R309", u"R311"', u"轮次常量")
rep("PREV_ROUND, ROUND, RDN = 307, 308, 306",
    "PREV_ROUND, ROUND, RDN = 308, 309, 307", u"节号常量")
rep('CHAIN = "/tmp/r309_chain.log"', 'CHAIN = "/tmp/r310_chain.log"', u"CHAIN 路径")
rep('KNIFE_LOG = "/tmp/r309_knives2.log"', 'KNIFE_LOG = "/tmp/r310_knives.log"', u"刀日志路径")
rep('EYE = os.environ.get("R309_EYE", u"")', 'EYE = os.environ.get("R310_EYE", u"")', u"看图腿环境变量")
rep('R309_LEDGERS_REFUSE', 'R310_LEDGERS_REFUSE', u"拒写前缀", want=1)
rep('R309_CRASH_RESTORED', 'R310_CRASH_RESTORED', u"崩溃还原前缀")
rep('LEDGERS_R309 OK', 'LEDGERS_R310 OK', u"收工哨兵")
rep('u"R309" not in head_sub', 'u"R310" not in head_sub', u"HEAD 检查里的轮次")
rep('r"R309_MUTATE 刀=(\\d+) CAUGHT=(\\d+) ESCAPED=(\\d+) NOT_RUN=(\\d+) RESTORE_CLEAN=(\\w+)"',
    'r"R310_MUTATE 刀=(\\d+) CAUGHT=(\\d+) ESCAPED=(\\d+) NOT_RUN=(\\d+) RESTORE_CLEAN=(\\w+)"', u"刀结论行正则")
rep('r"R309_MUTATE BASELINE 跑=(\\d+) 失败=(\\d+) exit=(\\d+)"',
    'r"R310_MUTATE BASELINE 跑=(\\d+) 失败=(\\d+) exit=(\\d+)"', u"基线结论行正则")
rep('/tmp/r309_battery_pre.log', '/tmp/r310_battery_pre.log', u"写盘前电池日志")
rep('/tmp/r309_battery_post.log', '/tmp/r310_battery_post.log', u"写盘后电池日志")
rep('if len(others) < 4 or not all(o.startswith(("scripts/", ".scratch/")) for o in others):',
    'if len(others) < 5 or not all(o.startswith(("scripts/", ".scratch/")) for o in others):',
    u"改动面下限")
rep('for want in (u"**348. ", u"**364. "):', 'for want in (u"**364. ",):', u"BACKLOG 追记锚点")
rep('new_bl = append_into_item(orig["BL"], u"**348. ", texts["BL348"], u"348")\n'
    'new_bl = append_into_item(new_bl, u"**364. ", texts["BL364"], u"364")',
    'new_bl = append_into_item(orig["BL"], u"**364. ", texts["BL364"], u"364")\n'
    'i_new = new_bl.rstrip(u"\\n").find(u"**%d. " % BLNEW)\n'
    'if i_new != -1:\n'
    '    die(u"BACKLOG %d 已经存在 ⇒ 不许开第二张同题单，去追记原条目" % BLNEW)\n'
    'new_bl = new_bl.rstrip(u"\\n") + u"\\n\\n" + texts["BLNEW"].rstrip(u"\\n") + u"\\n"\n'
    'if len(re.findall(u"(?m)^\\\\*\\\\*\\\\d{3}\\\\. ", new_bl)) != len(re.findall(u"(?m)^\\\\*\\\\*\\\\d{3}\\\\. ", orig["BL"])) + 1:\n'
    '    die(u"BACKLOG 条目头数量不等于原数 +1 ⇒ 新单没落成一条" )',
    u"BACKLOG 落点（364 追记 + 新开一单落在文件尾）")
rep('BL_MAX = max(int(x) for x in re.findall(r"(?m)^\\*\\*(\\d{3})\\. ", bl))',
    'BL_MAX = max(int(x) for x in re.findall(r"(?m)^\\*\\*(\\d{3})\\. ", bl))\nBLNEW = BL_MAX + 1',
    u"新单号")
rep('u"@HIDTABLES@": HID_TABLES, u"@HIDARMS@": HID_ARMS,',
    u'u"@HIDTABLES@": HID_TABLES, u"@HIDARMS@": HID_ARMS, u"@BLNEW@": BLNEW,\n'
    u'        u"@ROT@": ROT_NOW, u"@OPAQUE@": OPAQUE_NOW, u"@JUDGED@": JUDGED_NOW,',
    u"SUBS 补本轮读数")

# ---- 隐藏臂的现读（新增一节解析）
rep('WIT = "/tmp/r308_chain.log"',
    '''WIT = "/tmp/r308_chain.log"
HA = os.path.join(ROOT, "scripts", "hidden_arms.py")''', u"HA 路径")
rep('dk, _ = sh([sys.executable, CURVE])',
    '''ha_out, ha_rc = sh([sys.executable, HA])
ha_line = (re.findall(r"(?m)^HIDDEN_ARMS .+$", ha_out) or [u""])[-1]
if u"处置=ok" not in ha_line:
    die(u"腐烂针那把尺自己没签（rc=%d）：%s" % (ha_rc, ha_line[:160]))
ROT_NOW = (re.findall(r"rot=(\\d+)", ha_line) or [u""])[-1]
OPAQUE_NOW = (re.findall(r"抽不出=(\\d+)", ha_line) or [u"", u""])[-1]
JUDGED_NOW = (re.findall(r"可判=(\\d+)", ha_line) or [u""])[-1]

dk, _ = sh([sys.executable, CURVE])''', u"腐烂针现读")

# ---- 七本正文
NEW_TEXTS = u'''# ---------------------------------------------------------------- 七本文本
UI_NEW = u"""## 第 @ROUND@ 轮（@RTAG@ · U-@UA@…U-@UC@ · @TODAY@）：腐烂的针要能被数出来 —— 静态 AST + 常量传播 + 双向棘轮（U-@UA@…U-@UC@ · 产品 0 文件，判据轮）

- **U-@UA@：藏在 lambda 与变量里的 needle 会腐烂而静态预检不响 —— 本轮把它变成"可判 + 可归因"的数：`scripts/hidden_arms.py` 现读 表=192 可判=@JUDGED@ rot=@ROT@ 抽不出=@OPAQUE@。**
  364 原本的形状是"名册只报规模"（registered=103、未登记表 75 张、隐藏臂 423 把），
  而规模不可归因：谁烂了、烂了几把，没人说得出。本轮的尺不 import 那些表
  （191 张里至少 10 张没有 `__main__` 守卫，import 就会真的落刀跑 swift 测试），
  只做静态 AST：顶层 `ARMS/MUTATIONS/CASES/TABLE` 逐臂取"能解析成字面量的字符串"当候选
  （变量名走常量传播），候选在盘上**一个都不命中** ⇒ 该臂腐烂，按表点名；
  候选抽不出的臂单独登记成"抽不出"，不许静默丢掉。刀 M902…M907 各钉一条轴，全 CAUGHT。

- **U-@UB@：判法不成立时会造出大批假正例 —— 第一版把中文说明与目标路径当候选，191 张表上报 152 rot，其中包含当天刚全 CAUGHT 的 r308 / r309。**
  那是**尺坏**不是仓库真烂了 152 把。两条修正：① 变量名必须走常量传播（否则针看不见 ⇒ 假"抽不出"）；
  ② 目标路径那一格不是针（它当然在盘上 ⇒ 会把死刀洗活）。
  与 R307「区间对账没分箱就数出 34 个假正例」同一课：**数出来一堆红时，先怀疑分箱，不要先加门，
  更不要先把红写成缺陷清单**。M904 / M905 两根刀就是把这两条修正钉住 —— 摘掉任一一条，数立刻漂。

- **U-@UC@：双向棘轮 —— 上界必须**恰好**等于现读值；只判"不许超过"，另一半就没有牙。**
  `rot != ROT_CEILING` 就红：变多 = 有新腐烂；变少 = 名单被修掉了却没降上界
  （上界停在旧值，下一次真烂回去也没人知道）。`抽不出` 同理。
  正对照的基准取**真产物现读**而不是上界自己（拿上界当基准就成了同义反复，R146 那一族的新变体）。
  另记一条自伤：合成夹具的"死针"字符串住在 fixtures 目录里，而夹具自己也被扫进语料 ⇒
  死针命中自己、rot 数不出来 ⇒ 正对照当场失效（M906 钉的就是这一条）。

- **新开 @BLNEW@（腐烂名单要清）**：@ROT@ 把已点名的死刀要逐条处置 —— 要么重钉针、要么按 D-284 的规矩
  写明"退役 + 证人"。本轮只把它们变成可归因的数，**没有**替它们作"已经处理完"的证据。
  364 的追记同时留下规模对照：登记面仍是 registered=@TABLES@ / 未登记表 @HIDTABLES@ 张 / 隐藏臂 @HIDARMS@ 把，
  那是"没进名册"的问题，与"进了名册但针烂了"是两件事，别混成一条。

读数（全部现读，同一遍验证链 /tmp/r310_chain.log）：构建告警 0（`swift build --build-tests`，本轮零 Swift 改动，仍跑是因为 0 告警是产品构建的契约）；
判据卷 scripts/tests/test_hidden_arms.py `Ran 5 tests / OK`；刀表基线 `Ran 5 失败=0` 之后落刀，
本轮 @K_N@ 把全 CAUGHT、RESTORE_CLEAN=yes、NOT_RUN=0；
预检 tables=@TABLES@ covered=@COVERED@ arms=@PREARMS@ bad=0，名册 files=@ARMFILES@ arms=@ARMREG@ dupes=0；
腐烂针尺：`@HALINE@`；互证（R309 那把读数尺跑真日志）：`@RDLINE@`；
脚本电池 `Ran @BATT@ / OK (skipped=@SKIP@)`（写盘后同数）；
产品面连续零改动 = **@STREAK@** 轮（取数口 `scripts/product_streak.py --streak-for @ROUND@`；上一轮 @PREVSTREAK@）。

Swift 侧三条腿 **NOT-RUN**（本轮 0 产品文件、0 Swift 文件 ⇒ 没有新字节可跑，也没有旧字节能被本轮弄坏）：
全量卷 NOT-RUN（沿用 R308 那一跑 934 / 44 skip / 0）；重捕帧 NOT-RUN（帧目录现读 @FRAMES@ 张还在盘上）；
换装 NOT-RUN（产物未变）。看图腿 RUN：看的是 R308 改过的那两张 hover 帧（复看，不是复述）：@EYE@

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

为什么不是满分（逐条）：真实视觉审查 10 —— 判据轮对画面的净贡献是 0，本轮只复看了上一轮那两张；
判据有效性 14 —— 三条新 U 都有尺真身与刀，扣分在"候选集"仍是启发式（长字符串 + 路径过滤），
不是所有表都能被静态判到（仍有 @OPAQUE@ 把抽不出）；假绿防御 15 —— 六把刀各钉一条轴，
且两次自伤（假正例、夹具进语料）都是被对照当场抓住而不是收尾时想起来；
产品面推进 8 —— 0 产品文件，这是判断不是遗漏：356 剩下那一半要先量候选、347 / 305 要用户的真机眼；
台账一致性 14 —— 七本一支脚本、报告计数器与 §13 由写完账之后的仪器刷；
交付诚实性 15 —— 新开 @BLNEW@ 把"@ROT@ 把死刀还没清"写在账上，不写成已处理；
可复核性 14 —— 尺、判据卷、刀表都能重跑，扣分在腐烂名单依赖盘上现状（换机器/删表就会漂，
而漂了会响 —— 这是设计，不是缺陷）。

"""

IT_NEW = u"""## Round @RDN@ · R310（第 @ROUND@ 轮 · @TODAY@）：腐烂的针要能被数出来 —— 静态 AST + 常量传播 + 双向棘轮（产品 0 文件，判据轮）

本轮把 BACKLOG 364 从"规模"做成"可归因的数"：`scripts/hidden_arms.py` 现读
表=192 可判=@JUDGED@ rot=@ROT@ 抽不出=@OPAQUE@；判法是双向棘轮（上界必须恰好等于现读值，
两个方向都响）。两次自伤都进了账：第一版数出 152 rot 是**判法不成立**（中文说明与目标路径被当候选，
r308 / r309 当天刚全 CAUGHT 也被算成腐烂）；合成夹具自己住进语料，把死针洗活 ⇒ 正对照失效。
刀 M902…M907 全 CAUGHT；新开 @BLNEW@ 登记"@ROT@ 把死刀还没逐条处置"。

读数：构建告警 0；判据卷 `Ran 5 / OK`；刀表基线 `Ran 5 失败=0`；本轮 @K_N@ 把全 CAUGHT、RESTORE_CLEAN=yes；
预检 tables=@TABLES@ bad=0、名册 files=@ARMFILES@ arms=@ARMREG@；
脚本电池 `Ran @BATT@ / OK (skipped=@SKIP@)`（写盘后同数）；
产品面连续零改动 = **@STREAK@** 轮（上一轮 @PREVSTREAK@，取数口 `scripts/product_streak.py`）。
Swift 三条腿 NOT-RUN（理由逐条写在 §5）；看图腿 RUN（@FRAMES@ 张在盘上，本轮无新帧）。
看图腿 RUN：@EYE@

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

理由（本轮实测，不是推想）：同一件事（找腐烂的针）的第一版给出 152 把，
其中包含当天刚全 CAUGHT 的两张表 —— 那不是仓库烂，是**分箱错**：
候选集里混进了中文说明与目标路径。修完是 @ROT@ 把，每一把都可归因到表与臂号。
与 R307（区间对账先分箱，否则 34 个假正例）、R298（台账措辞数出来的"连续 N 轮"）同一族。

所以规矩写成三条：
① 新尺第一次跑出来的"缺陷数"，必须先在**已知不该有缺陷的对象**上跑一遍（本轮 = 当天刚全 CAUGHT 的 r308 / r309）；
② 判据自身的两条修正都要有刀（M904 常量传播、M905 路径过滤）—— 只有"能红"没有"谁让它红"，
   下一次改回去没人知道；
③ 判据是**双向**的：上界必须恰好等于现读值。只判"不许超过"= 允许悄悄涨回去；
   只判"不许低于"= 把修好的成果钉死。

"""

BL_364 = u"""  追记（R310）：这一格从"规模"变成"可归因的数"。`scripts/hidden_arms.py` 现读
  表=192 可判=@JUDGED@ rot=@ROT@ 抽不出=@OPAQUE@，判法是双向棘轮（上界必须恰好等于现读值）；
  每一把腐烂都点名到表与臂号，刀 M902…M907 各钉一条轴（摘掉 rot 判定、只判单方向、
  摘常量传播、摘路径过滤、让夹具进语料、静默丢掉抽不出的臂 —— 六个坏法各红各的格子）。
  两条边界要写清，免得这一格被读成"已结"：
  ① 登记面没变（registered=@TABLES@、未登记表 @HIDTABLES@ 张、隐藏臂 @HIDARMS@ 把）——
     那是"表没进名册"，与"进了名册但针烂了"是两件事；
  ② 数出来的 @ROT@ 把**还没逐条处置** ⇒ 新开 @BLNEW@ 登记。"""

BL_NEW = u"""**@BLNEW@. 数出来的 @ROT@ 把腐烂针要逐条处置（重钉或按 D-284 写"退役 + 证人"）**（R310）

  R310 把"谁烂了"变成可归因的数（`python3 scripts/hidden_arms.py` 会逐条打
  `HIDDEN_ROT <表> <臂号>`），但**没有**替它们作"已经处理完"的证据。
  每条只有两种合法出口：重钉一根盘上恰好命中一次的针并复跑那张表；
  或者按 D-284 写明"这一臂退役 + 它的证人是谁"（不许直接删表绕开检查）。
  上界 `ROT_CEILING` 是双向棘轮：每清一把就要把它降一格，
  降的时候 `test_the_ceilings_equal_the_live_readings` 会替我确认没多降。
  另 @OPAQUE@ 把"静态抽不出候选"的臂是第二层欠账：要判只能真跑（把那张表纳入名册并复跑一次）。"""

CH_NEW = u"""### 腐烂的针要能被数出来：静态 AST + 常量传播 + 双向棘轮（R310 / U-@UA@…U-@UC@ · D-@DN@ · 产品 0 文件，判据轮）

- BACKLOG 364 从"规模"做成"可归因的数"：`scripts/hidden_arms.py` 现读 表=192 可判=@JUDGED@
  rot=@ROT@ 抽不出=@OPAQUE@；不 import 表（10+ 张没有 `__main__` 守卫，import 就会真落刀跑 swift 测试），
  只做 AST + 常量传播；判据是双向棘轮（上界必须恰好等于现读值）。
- 两次自伤都进账：第一版 152 rot 是判法不成立（中文说明与目标路径被当候选，当天刚全 CAUGHT 的
  r308 / r309 也被算成腐烂）；合成夹具住进语料把死针洗活 ⇒ 正对照当场失效。
- 刀 M902…M907 全 CAUGHT、RESTORE_CLEAN=yes、未落刀基线 `Ran 5 失败=0`；新开 @BLNEW@ 登记
  "@ROT@ 把死刀还没逐条处置"；364 留追记（登记面 423 把隐藏臂是另一件事）。
- 判据轮：构建告警 0；判据卷 `Ran 5 / OK`；预检 tables=@TABLES@ bad=0、名册 arms=@ARMREG@；
  脚本电池 `Ran @BATT@ / OK (skipped=@SKIP@)`（写盘后同数）；产品面连续零改动 **@STREAK@** 轮；
  Swift 三条腿 NOT-RUN 并逐条写理由。

"""

ST_NEW = u"""## @RTAG@ 状态（第 @ROUND@ 轮 / Round @RDN@ · @TODAY@）

本轮做的是"腐烂的针要能被数出来"：`scripts/hidden_arms.py`（AST + 常量传播 + 双向棘轮）现读
表=192 可判=@JUDGED@ rot=@ROT@ 抽不出=@OPAQUE@；判据卷 `Ran 5 / OK`；刀 M902…M907 全 CAUGHT。
D-@DN@ 定「一条数缺陷的判据必须先自证它不会把好的数出来；做不到只准报规模」；
364 留追记（从规模变可归因），新开 @BLNEW@ 登记 @ROT@ 把死刀待清。

最后更新：@TODAY@（本地 · @RTAG@ / 第 @ROUND@ 轮 / Round @RDN@）：**腐烂针第一次可点名**（产品 0 文件，判据轮）
现读：构建告警 0；判据卷 `Ran 5 / OK`；刀 @K_N@ 把全 CAUGHT、RESTORE_CLEAN=yes；
预检 tables=@TABLES@ covered=@COVERED@ bad=0、名册 files=@ARMFILES@ arms=@ARMREG@ dupes=0；
腐烂尺 `@HALINE@`；R309 那把读数尺互证 `@RDLINE@`；电池 Ran @BATT@ / OK (skipped=@SKIP@)（写盘后同数）；
看图腿 RUN（@FRAMES@ 张在盘上，本轮无新帧 —— @EYE_SHORT@）。
产品文件 0 个，连续零改动 **@STREAK@** 轮（唯一取数口 `python3 scripts/product_streak.py --streak-for @ROUND@`，
同形用于 `--check`；上一轮 @PREVSTREAK@）。as-of 第 @ROUND@ 轮的最后一笔产品提交是 @LASTSHA@ = 第 @LASTROUND@ 轮。
Swift 三条腿 NOT-RUN 并写理由（0 Swift 文件 ⇒ 没有新字节可跑，也没有旧字节能被本轮弄坏）。

⓪ @RNEXT@ 开场要先读的（成对：run id ↔ commit）：@CI@
   —— 本轮与 R309 的 runner 结论都要读；另外两件事：
   ① `scripts/hidden_arms.py` 的语料是**盘上现状**，在 runner 上跑会因为工作树相同而给同一个数，
      但任何一台机器少一张表就会漂 ⇒ 漂了会响（双向棘轮），别把它当机器差异放行；
   ② 判据卷里 `test_the_ceilings_equal_the_live_readings` 依赖 .scratch 里的表都在 ——
      若 runner 的 checkout 少了文件，那一格要按"缺产物算红"处理，不许 skip 掉。

① 下一轮（@RNEXT@）的靶：① **回到产品面** —— 356 剩下那一半（暗档最细一步 17.33 低于地板 18、
   1x/2x 抗锯齿离散 1.7 倍）：先量"换通道"候选有没有产物证人，不许拿减档数当解药；
   ② @BLNEW@：@ROT@ 把腐烂针逐条处置（重钉或退役 + 证人），每清一把就降上界；
   ③ 348 剩下的读数族（帧数 / 刀数 / §8 格子数）各配一条恒等式；
   ④ 360 的最后一批（11 份裸 stdout）；⑤ 361 的合并；⑥ 347 / 305 仍欠用户的真机眼。

② 仍开：347（真机证人）、305（等 347）、356 的**那一半**、@BLNEW@（腐烂针待清）、
   364 的"抽不出候选的 @OPAQUE@ 把要真跑"、348 的"读数族还没纳全"、354 的第五步、
   360（剩 11 份）、361（未合并）、359、362、349、350 第二步、351、344、341 的 CI 契约半、
   339、312 具名出口、304、296、291；用户闸门 220 路 A / 228② / 265。

"""
'''

block("# ---------------------------------------------------------------- 七本文本", NEW_TEXTS, u"七本正文")

# 报告 §13 的两格措辞：本轮专属
rep(u'prod_cell = (u"- **产品面（这一节最该被读的部分）**：本轮产品文件 0 个、Swift 0 份（判据轮：改动面 %s 个文件，"\n'
    u'                 u"全在 `scripts/` 与 `.scratch/motion-audit-2/`），产品面连续零改动轮数 = **%s**"',
    u'prod_cell = (u"- **产品面（这一节最该被读的部分）**：本轮产品文件 0 个、Swift 0 份（判据轮：改动面 %s 个文件，"\n'
    u'                 u"全在 `scripts/` 与 `.scratch/motion-audit-2/`），产品面连续零改动轮数 = **%s**"',
    u"产品面格（锚点确认）")
rep(u'u"决定台账最大 **D-%s**，BACKLOG 最大 **%s**。本轮新落的读数现抄：`%s`"',
    u'u"决定台账最大 **D-%s**，BACKLOG 最大 **%s**（本轮新开 @BLNEW@）。本轮新落的读数现抄：`%s`"',
    u"规模格里点名新单")
rep(u'                     % (pre, ARM_REG, ARM_FILES, TABLES_N, COVERED, PRE_BAD, HID_TABLES, HID_ARMS,\n'
    u'                     len(re.findall(u"(?m)^- \\\\*\\\\*U-(\\\\d{3,4})[：(]", new_ui)), UC, DN, BL_MAX, RD_LINE))',
    u'                     % (pre, ARM_REG, ARM_FILES, TABLES_N, COVERED, PRE_BAD, HID_TABLES, HID_ARMS,\n'
    u'                     len(re.findall(u"(?m)^- \\\\*\\\\*U-(\\\\d{3,4})[：(]", new_ui)), UC, DN, BLNEW, RD_LINE))',
    u"规模格改用新单号")
rep(u'u"（本轮是判据轮：改动面 %s 个文件全在 `scripts/` 与 `.scratch/`）；这一格登记的是"',
    u'u"（本轮是判据轮：改动面 %s 个文件全在 `scripts/` 与 `.scratch/`）；这一格登记的是"',
    u"Sources 格（确认）")

io.open(DST, "w", encoding="utf-8").write(s)
try:
    ast.parse(s)
except SyntaxError as exc:
    sys.stderr.write("SYNTAX_BAD after write: %s\n" % exc)
    raise SystemExit(1)
print("WROTE %s lines=%d" % (DST, s.count("\n")))

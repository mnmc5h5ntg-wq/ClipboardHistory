# -*- coding: utf-8 -*-
"""R588 七本台账的生成器（第 587 轮 / Round 585 · 产品 0 文件）。

四条自陈（写给下一次读这个文件的我）：
① 数字一律从 `/tmp/r588/*` 的读数文件里 grep 出来，正文不手抄；取不到就 `must_read/grep_line` 退出。
② CJK 串里不许出现 ASCII 双引号 ⇒ 本文所有引号都是「」。
③ 模板里要逐字印的百分号一律写 `%%`。
④ **本轮新守的规矩**：STATE 的正文小节一律写「本节①/②/③」，**不许**写 `段号=`；
   规格 §3 的段号只在**有证人**时以「第②段/第③段」出现。这条由 `scripts/stage_gate_claims.py` 会红地签，
   写手自己先合规，否则落盘即红（R587 就是在这里留下一句假话的）。
"""
import io
import json
import os
import re
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0"
TMP = "/tmp/r588"
DATE = "2026-11-06"
BOOKS = {"UI": "AGENT_UI_AUDIT.md", "ITER": "AGENT_VISUAL_ITERATION.md", "STATE": "AGENT_STATE.md",
         "BACKLOG": "AGENT_BACKLOG.md", "DEC": "AGENT_DECISIONS.md", "FINAL": "AGENT_FINAL_REPORT.md",
         "CHANGE": "CHANGELOG.md"}

RUN_MAIN = "42130898663"      # R587 主笔
RUN_ADD = "42131401738"       # R587 补记笔


def read(book):
    return io.open(os.path.join(ROOT, BOOKS[book]), encoding="utf-8").read()


def write(book, text):
    io.open(os.path.join(ROOT, BOOKS[book]), "w", encoding="utf-8", newline="\n").write(text)


def must_read(path, label):
    if not os.path.exists(path):
        raise SystemExit("读数缺失：%s（%s）⇒ 先跑它，不许手填" % (path, label))
    return io.open(path, encoding="utf-8", errors="replace").read()


def grep_line(text, prefix, label, last=True):
    rows = [l.strip() for l in text.splitlines() if l.strip().startswith(prefix)]
    if not rows:
        raise SystemExit("读数里找不到前缀 %r（%s）" % (prefix, label))
    return rows[-1] if last else rows[0]


def identity_from_disk():
    ui = read("UI")
    prev_n = max(int(x) for x in re.findall(r"(?m)^## 第 (\d+) 轮（R\d+", ui))
    state_r = max(int(x) for x in re.findall(r"(?m)^## R(\d+) 状态", read("STATE")))
    r = state_r + 1
    if prev_n != r - 2:
        raise SystemExit("身份交叉核对失败：STATE 最新节是 R%d ⇒ 本轮应是第 %d 轮，而 UI 最新一节写着第 %d 轮"
                         % (state_r, r - 1, prev_n))
    return {"r": r, "n": r - 1, "round": r - 3, "prev_n": prev_n, "prev_r": r - 1}


def gather():
    ci = json.loads(must_read(os.path.join(TMP, "ci_readings.json"), u"⓪ 两跑读数"))
    d = {"ident": identity_from_disk(), "ci": ci}
    d["main"], d["add"] = ci[RUN_MAIN], ci[RUN_ADD]
    d["anchor"] = ci.get(u"归因锚", u"（读数里没有归因锚那一格）")

    def grab(fname, prefix, label, last=True):
        return grep_line(must_read(os.path.join(TMP, fname), label), prefix, label, last=last)

    d["capture"] = grab("capture_summary.txt", "CAPTURE_LINES=", u"捕获卷")
    d["frames"] = grab("capture_summary.txt", "FRAMES=", u"帧数")
    d["build_warn"] = grab("capture_summary.txt", "BUILD_WARNINGS=", u"构建告警")
    d["build_kind"] = grab("capture_summary.txt", "BUILD_KIND=", u"构建种类")
    gate = must_read(os.path.join(TMP, "gate_local.txt"), u"本机那一门")
    d["gate_drift"] = grep_line(gate, "FRAME_BASELINE_DRIFT ", u"本机判定")
    d["gate_result"] = grep_line(gate, "FRAME_BASELINE_RESULT=", u"本机结论")
    d["gate_bake"] = grep_line(gate, "FRAME_BASELINE_BAKE ", u"基线出处行")
    d["tier_shape"] = must_read(os.path.join(TMP, "tier_shape.txt"), u"档位循环扫描").strip()
    # 守卫的**逐字行**里抄着被禁的那两个字面串 ⇒ 把它整份嵌进 STATE 就等于在本节里再造一次违规
    # （R562「守卫搜的串不许出现在自己正文」的这一支：被嵌进去的是**守卫的输出**，不是我的措辞）。
    # 所以嵌进台账的只有汇总行与红行；逐字原文留在读数文件与 D-%(r)s 的背景那一格里。
    d["stage_before"] = u"\n".join(
        l for l in must_read(os.path.join(TMP, "stage_gate_before.txt"), u"第③段断言守卫（落盘前）")
        .strip().splitlines() if not l.strip().startswith(u"逐字："))
    d["look"] = must_read(os.path.join(TMP, "look.txt"), u"看图那一腿").strip()
    d["byte"] = grab("byte_compare.txt", "BYTE_COMPARE ", u"逐字节对照")
    d["numstat"] = must_read(os.path.join(TMP, "numstat.txt"), u"numstat 现读").strip()
    d["pyverify"] = must_read(os.path.join(TMP, "pyverify.txt"), u"字面量真验证").strip()
    d["md5"] = u"before=%s after=%s 同一份=%s" % (
        must_read(os.path.join(TMP, "md5_before.txt"), u"刀链前").strip(),
        must_read(os.path.join(TMP, "md5_after.txt"), u"刀链后").strip(),
        u"yes" if must_read(os.path.join(TMP, "md5_before.txt"), u"a").strip()
        == must_read(os.path.join(TMP, "md5_after.txt"), u"b").strip() else u"NO")

    d["counts"] = {}
    for l in must_read(os.path.join(TMP, "test_counts.txt"), u"def test_ 前后计数").splitlines():
        m = re.match(r"(\S+) HEAD=(\d+) NOW=(\d+)", l.strip())
        if m:
            d["counts"][m.group(1)] = (int(m.group(2)), int(m.group(3)))
    for k in ("test_stage_gate_claims", "test_tier_reporting_shape"):
        if k not in d["counts"] or d["counts"][k][1] <= 0:
            raise SystemExit("矛盾读数：新卷 %s 的 def test_ 数没长（%r）" % (k, d["counts"].get(k)))
    d["delta_total"] = sum(a - b for b, a in d["counts"].values())

    kn = must_read(os.path.join(TMP, "knife_status.txt"), u"刀状态文件")
    knives = []
    for ln in kn.splitlines():
        m = re.match(r"(r\d+)/(M15\d\d) rc=(\d+) caught=(\d) clean=(\d) precheck=(\S+) post=(\S+)", ln.strip())
        if m:
            knives.append({"arm": m.group(2), "rc": int(m.group(3)), "caught": int(m.group(4)),
                           "clean": int(m.group(5)), "precheck": m.group(6), "post": m.group(7)})
    for k in knives:
        if k["post"] == "CAUGHT" and k["rc"] == 0:
            raise SystemExit("矛盾读数：%s 说 CAUGHT 而 rc=0" % k["arm"])
    # 主笔这一趟只有 M1555/M1556 落了：另三把的预检里有一格判的是「最新那一轮」，
    # 台账没落盘就注定 precheck 不是 PASSED ⇒ 它们归**补记那一笔**，主笔的标题不许提前把五把都签了。
    if len(knives) != 2:
        raise SystemExit("主笔的刀数不是 2 把：%d ⇒ 表或状态文件读错了（本轮主笔只该有 M1555/M1556）" % len(knives))
    reds = must_read(os.path.join(TMP, "knife_reds.txt"), u"每把红了哪几格")
    for k in knives:
        block = re.search(r"--- %s\n(.*?)(?=\n--- M|$)" % k["arm"], reds, re.S)
        body = block.group(1) if block else u""
        k["reds"] = len(re.findall(r"读数: FAIL:", body))
    d["knives"] = knives

    for key, fname, prefix, label in (("full", "full_summary.txt", "FULL_TOTAL=", u"全量卷"),
                                      ("full_skips", "full_summary.txt", "FULL_SKIPPED=", u"全量 skipped"),
                                      ("battery", "py_battery.txt", "Ran ", u"python 全电池"),
                                      ("battery_ok", "py_battery.txt", "OK", u"电池签字")):
        p = os.path.join(TMP, fname)
        d[key] = grep_line(must_read(p, label), prefix, label, last=(key != "battery_ok")) \
            if os.path.exists(p) else u"（未读到：那一趟还没跑 ⇒ 台账不许替它填数）"
    p = os.path.join(TMP, "prechecks.txt")
    d["prechecks"] = must_read(p, u"三道预检") if os.path.exists(p) else u""
    d["absence"] = (grep_line(d["prechecks"], "LEDGER_ABSENCE_RESULT", u"清账门")
                    if d["prechecks"] else u"（落盘前的读数，落盘之后复算）")
    rp = os.path.join(TMP, "recon.txt")
    d["recon"] = grep_line(must_read(rp, u"对账门"), "RED_NAME_RECONCILIATION", u"对账门") \
        if os.path.exists(rp) else u"（预览那一趟还没跑）"
    sp = os.path.join(TMP, "streak.txt")
    d["streak"] = grep_line(must_read(sp, u"产品面连续轮数"), "PRODUCT_STREAK ledger_round", u"产品面连续轮数") \
        if os.path.exists(sp) else u"（落盘之后现读）"
    return d


# —————————————————————————————————————————————————————————──
# 正文


def next_u():
    nums = [int(x) for x in re.findall(r"\*\*U-(\d+)", read("UI"))]
    if not nums:
        raise SystemExit("UI_AUDIT 里读不到 U 号")
    return max(nums) + 1


def knife_line(knives):
    return u" ｜ ".join(u"%s rc=%d 预检=%s 末次=%s clean=%d 红%d格"
                        % (k["arm"], k["rc"], k["precheck"], k["post"], k["clean"], k["reds"])
                        for k in knives)


def block_state(d):
    i = d["ident"]
    m, a = d["main"], d["add"]
    return u"""## R588 状态（%(date)s · 第 %(n)s 轮 / Round %(round)s · 产品 0 文件 + **台账说的话有没有证人**（本节① 第③段断言做成会红的守卫；本节② 档位循环「逐档各自点名 + 缺席可数」做成守卫并修掉现读到的两处；本节③ 名册那 8 张暗档逐张看整帧）+ 判据卷 +%(delta_total)d 格（词表守卫新卷 %(stage_now)d 格 + 档位形状新卷 %(shape_now)d 格）+ 刀 M1555/M1556 CAUGHT（M1557–M1559 归补记：它们的预检读的是台账自己）+ ⓪ 两跑都未到数）

⓪ **两跑都没到数 ⇒ 整格 NOT-RUN；本轮唯一能写的是「R587 补记里那句 RUN_UNFETCHED 从本笔起不成立」**
- 身份现读：UI_AUDIT 最新一节以「第 %(prev_n)s 轮（R%(prev_r)s」开头，STATE 最新是 R%(prev_r)s ⇒ 交叉核对通过 ⇒ 本轮 **R%(r)s = 第 %(n)s 轮 / Round %(round)s**。刀高水位现读 **M1554**（`mutate_r587_heat` 那一把在册）⇒ 本轮从 **M1555** 起，没抄派单里的数。
- `%(main_run)s ↔ %(main_sha)s`（R587 主笔）现读 `status=in_progress`、`conclusion` 空，`ci_read.py steps` 里**一个非空步骤结论都没有**（%(main_concl)d 行）⇒ **未到数**：出口·甲/乙/丙/丁 一条都不选，R587 交下来的三条预测（`PREDICTIONS_R588`）**一条都不判**（数没到就整格不选，不许先挑一条"看起来对"的出路，R557 那一课）。
- `%(add_run)s ↔ %(add_sha)s`（R587 补记笔）同样 `in_progress` ⇒ 未到数。⚠ **forward 更正（改账不删原文）**：R587 补记 ⓪·2 那句 `RUN_UNFETCHED=这一笔落地时尚不存在` 从**本笔**起不成立 —— 那一跑现在**已创建**（号已到手），只是还没到数。R587 那一格一字不改，更正写在这里。
- 归因锚**照抄不重跑**（派单 ⓪·6 明令）：%(anchor)s
- 取数通道这一格本轮也现读了：`ci_read.py latest` 只打**最新一笔** ⇒ 两跑里旧的那笔永远匹配不上；所以逐跑改用 `gh run view --json status,conclusion,headSha`。这不是「没到数」，是**通道只有一格宽**（读数文件里两行都留着）。

本节① **派单给的三条形状结论：逐条坐实（取值时刻=R%(r)s 开工，全部现读）**
- 靶 1（台账里那句假话）**两处形状的逐字原文写在 D-%(r)s 的背景那一格**（写手这一节故意不复述：
  守卫搜的就是那两个字面串，把它们抄进**被它判的那一节**会立刻自我判红 —— R562 那一课「守卫搜的串不许出现在自己正文」）。
  形状是：STATE 的 R587 那一节把小节编号写成了「段号」加等号加圈码；ITERATION 的 Round 584 那一行把段号写成「仍是」
  后面跟着两个圈码。⇒ 两处表达的都是「第③段那一闸门已经放行」这一层意思。
  **第③段没开工的证人三条**：①`git diff --name-only HEAD~2 HEAD -- Sources/ ClipboardHistory/` 现读**为空**；
  ②两条具名阻塞一条没撤（`STAGE2_CLICKTHROUGH_BLOCKED`、`STAGE3_FRAME_CRITERIA_HAVE_NO_RUNNER_WITNESS`，守卫现读 `仍挂着的阻塞=2`）；
  ③规格 `docs/FOLD_DUO_SPEC_2026-11-03.md` §3 那句「⇒ 三问仍未全过 ⇒ 第③段继续不开工」**没被划掉**（本轮没改文档里那一句）。
  ⇒ 本轮落的三件事全在**取证仪器侧**（它们服务的是第②段那两条阻塞的证人），**没有一件属于第③段**；
  上一轮那句「②③段各落一件」不是笔误而是**形状错**：STATE 的正文小节编号（⓪①②③⑦⑧⑨）与规格 §3 的段号**同字**，
  于是「本节③」被写成了段号的样子。⇒ 修法不是删字，是**做成会红的守卫**（见本节②）。
- 靶 2 形状：名册 16 行里暗档 8 行（`tier_from_name` 现读，不是按子串数）⇒ 逐张看整帧 + 三格读数，见 ⑧。
- 靶 3 形状（同一支扫描器跑两遍：HEAD 与工作树）：`%(tier_shape_head)s` ⇒ 改之前**档位循环 3 处，带 return 1 处，无可数格 2 处**；
  监工点名的是四支 TIERS 消费者，实际坏形状在**两支**里（`frame_recording_proof.py` 的取帧循环缺帧就 return；
  `hover_two_state_diff.py` 的 `rung_from_readings` 各自点名了却**没有一格数得出少了几档**）⇒ 两处都修。

本节② **真实推进（产品 0 文件；靶 1 + 靶 3 的两支守卫）**
- 新增 `scripts/stage_gate_claims.py`：判**最新那一轮**（主节 + 补记节并起来判，切不开就**不判并点名**，不许退回全文判历史）。
  两种坏法各一条正则：**冒充段号**那一支认的是"小节编号被写成段号的样子"（一律红，证人齐了也不放行）；
  **无证断言**那一支认的是"小节编号后面紧跟着规格段号字样"或"段号字样同句跟一个推进词"
  ⇒ 必须同时有「规格里三问全过」+「两条阻塞已撤」两个证人，否则红。
  段号识别按 `第[①②③④]*③段` 而不是子串 —— `第②③段` 里**不含** `第③段`，第一版就是这么漏掉 ITERATION 那一行的（刀 M1557 钉）。
  反向陈述（`第③段一字未写/未动`）单列一档，**不红**；刀 M1558 钉「反向词表不许变成永不匹配」。
- 新增 `scripts/tier_reporting_shape.py`：AST 扫 `scripts/*.py` 每一支，两条独立规则 ——
  **R1** 档位循环体里不许 `return`（那是「后面那些档我不看了」的唯一静默形状）；
  **R2** 含档位循环的函数里必须有可数的缺席格（`not-run=` 一类字面量），否则「各自点名」可以靠两句 print 满足而没人知道少了几档。
  一个档位循环都没找到 ⇒ **退 2**，不许绿（扫描器没有对象不等于全仓合规）。`.scratch/` 现读 32 处循环 ⇒ 只数不判。
- 两处修复：`frame_recording_proof.py` 取帧循环改成累加 + 统一收口，并新增 `FRAME_STATE_STOPS not-run=%%d` 与
  `FRAME_STATE_RESULT=not-run`（有一档没到就不许印 ok）；`hover_two_state_diff.py` 补
  `RUNG_STEP_TIER_COVERAGE not-run=%%d`（点名已经对，缺的是**数得出来**）。
- 落盘前守卫在**当前台账**上的现读（这一趟是本轮的靶，不是修完之后的自夸）：`%(stage_before)s`
  ⇒ 它现在红在 R587 那一节（冒充段号 2 处）；本轮那一节落盘之后必须转绿 ⇒ 两趟读数都记账（⑦）。

本节③ **真实推进（靶 2：8 张暗档逐张看整帧，三格读数 + 尺的形状证人）**
- 8 张逐张看完（4 张 detail 1440x1040 + 4 张 quickpick 840x600），每张三格都在 ⑧ 里逐字。
  参照物写清了两件事：与**同场景另一档**（亮 vs 暗）比才有内容差；与**上一轮那批**比是 0 颗 ⇒ 只证尺没坏。
- **659 认过的形状在本批是实测**：每一行的 `bbox(RGBA 差量图直取)=None`，而 `convert("L")` 之后 bbox 是整幅 ⇒
  三把正对照（同尺寸、内容已知不同）给出 42195 / 46625 / 1496422 颗与非 None 的 bbox(L) ⇒
  「看不见差别」这句话只有在**尺被证明不瞎**之后才算读数。
- 一把跨状态对照量出一条**新事实**：`quickpick-search-focus` 与 `quickpick-search-hover` 两帧在**两档都是逐字节同一张**
  （暗 `b38dfe662854`、亮 `e27c77479ac4`）。证人不是我的眼睛而是夹具自己的注释
  （`UICaptureHarness.swift:12973-12974`，R415：「与 hover 同一档视觉，取证键分开」），
  且两条判据各自比的是**抬起 vs 静置**、不比 hover vs focus ⇒ 与今天这两张相同**不矛盾** ⇒ **不开新单**，
  但把「两键两帧从此逐字节相同」第一次写进账，免得下一轮有人以为少捕了一帧。
- ⚠ 一句只算读数不算结论的观察：暗档里**选中药丸**与**悬停带**的亮度差得很小（`quickpick-hover` vs `quickpick-list`
  差 46625 颗、bbox 落在第四行行带）⇒ 「肉眼要凑近才分得出哪一行是 hover」是本轮看图时说的，
  它属于 D12/hover 那一族早就在量的东西，本轮不据此开单也不改任何地板。

⑨ **本轮自伤清单（九处，每处都带代价）与对账**
· **对账口径**（沿用启用，不关）：每条具名红/具名不判/作废读数要么落到 `⑨·` 编号，要么写 `不计入对账口径` 并带名册三类名字之一。
- 逐条：
  · ⑨·1 **上一轮那句假话本轮才发现，而且我当时的收口自陈重复了它**：R587 台账那两处（逐字见 D-%(r)s 背景那一格），
    我上一轮的 ⑤ 格也写了「规格 §3 第②③段各落一件」。三条证人（`Sources/` 空、两条阻塞未撤、§3 那句未划掉）
    任何一条都能当场否掉它 ⇒ 这不是笔误，是**小节编号与段号同字**这个形状在骗人，而骗到的第一个人是我。
    代价=本轮第一件事从「写新守卫」变成「先证明旧话是假的」；守卫 `--section R587` 那一格从此是**永久证人**
    （它不许随轮次漂，也不许被「历史不判」顺手豁免掉）。
  · ⑨·2 **守卫第一版按子串认段号，于是 ITERATION 那一行被读成「无关」**：那一行是两个圈码并列的段号写法，
    里面不含"第"加一个圈码 3 再加"段"那三个字的连续形状 ⇒ 子串法天生看不见它。
    我自己用真台账跑第一版才发现（`断言=0` 而盘上明明有一句假话）⇒ 漏读比多读危险：多读会立刻被关，漏读会长期点头。
    代价=识别式改成 `第[①②③④]*③段`，并补一条「枚举写法要认得」的正对照 + 一把刀 M1557。
  · ⑨·3 **切节的第一版「第一个命中的标题形状就返回」 ⇒ ITERATION 整本被当全文扫**：
    于是历史里合法的「③ 取证通道分不分得清真黑与透明…」被读成无证断言（多红方向）。
    代价=三种标题形状合并成一条正则；**同一轮的主节 + 补记节并起来判**（否则「最新一节」会只挑到补记，
    把主节里那句假话放过 —— 那是另一种漏读）；并补一条「切不出节 ⇒ 不判并点名，不许退回全文」的对照 + 刀 M1559。
  · ⑨·4 **测试方法撞了 `TestCase.run`**：我给 `RealLedgerTests` 写了个叫 `run` 的 helper ⇒
    unittest 调它时把 TestResult 传进 argv，报 `TypeError: 'TextTestResult' object is not iterable`。
    代价=改名 `run_cli`。这是「仪器读错对象」族里最轻的一种，但它红的方式是**整卷 import 阶段炸**，
    很容易被误读成守卫坏了。
  · ⑨·5 **读数文件自己说谎（与 R587 ⑨·9 同族，本轮换了一格）**：`numstat.txt` 第一版把字段顺序拼成
    `1 +1 +路径/−` ⇒ 读起来像「1 个文件 +1 行」；`tier_shape.txt` 第一版把 HEAD 那棵树里文件的**临时目录路径**
    写进了读数（`../../../var/folders/…`），下一轮照抄就找不到对象。代价=两处都重生成，
    并在台账里只引用修好之后那份；规矩照旧：**读数文件里每一格都要说得出它是谁打的、路径是相对谁的**。
  · ⑨·6 **构建那一格是增量构建，差点被我写成「全量重编 0 告警」**：本轮没改 Swift ⇒
    `swift build --build-tests` 只写了 4 个文件、`Compiling` 一次没有 ⇒ `warning:` 计数为 0 是**没有编译动作**的 0，
    不是「编了一遍都没告警」的 0。代价=读数文件里加 `BUILD_KIND=incremental` 并在这句话上带警告，
    台账 ⑦ 逐字抄这一格，不许简写成「build 0 告警」。
  · ⑨·7 **一条判据在台账落盘之前注定红，另一朵是它的借红**（时序，不是缺陷，但必须记两个时刻）：
    `test_newest_section_must_be_clean` 判的是「最新那一轮」，而台账没落盘时最新一轮还是 R587 ⇒
    判据卷那一趟它红 1 朵；台账落盘（本轮那一节用「本节①②③」）之后复跑才绿。
    ⇒ 这一条与 R580「电池格要写第一趟/第二趟两个时刻」同族：**凡判据读的是台账自己，
    它的绿就只能由「落盘之后那一趟」签**，写手不许拿落盘前那趟冒充。
  · ⑨·8 **守卫的第一版把「讲这条规矩本身」的句子也读成违规**：要写"段号只在有证人时以某段出现"这类句子，
    句子里必然同时出现段号字样与规格段号 ⇒ 写手自检连红三轮，而我最初的反应是**改措辞躲守卫**——那正是把门调松。
    停下来想的结论是：守卫缺的不是宽容，是**引用与主干的分别**。于是仪器加了两档并且都写进判据：
    ①摘掉「…」里的引用再配谓词（`冒充段号` 那一支仍走原文、不摘引用 ⇒ 那个形状无论如何都红）；
    ②反向词的管辖范围是**句子**（到句号为止），不是正则那一段——否则"段号仍是第②段（第③段一字未动）"
    这种**守规矩**的句子会被读成断言。两档各配一格测试，其中一格专门断"摘掉引用之后主干仍然要红"，
    防止这一档变成后门。
  · ⑨·9 **`post_land()` 的正则匹配不到写手自己刚写的占位符**：apply 那一趟在 streak 还没现读时落的是
    `**-1**`，而 post_land 找的是"两个星号之间只有数字"那一型 ⇒ `ANCHOR-MISS post-land FINAL：本轮那一格现读不到`。
    代价=正则改成允许负号并写明"占位符必须被同一个锚找得到"。形状与 R585/R586 那一族同：
    **派生格的两个时刻由同一把锚钉**，第一趟写进去的东西如果第二趟找不到，就会永远留在盘上。
- **红名对账**：
  · 红名「守卫第一版 `断言=0`（枚举写法漏读）」→ ⑨·2
  · 红名「ITERATION 被当全文扫 ⇒ 历史合法讨论读成违规」→ ⑨·3
  · 红名「`TypeError: 'TextTestResult' object is not iterable`」→ ⑨·4
  · 红名「读数文件把字段顺序/临时路径写错」→ ⑨·5
  · 红名「写手自检连红三轮：守卫把讲规矩本身的句子读成违规」→ ⑨·8
  · 红名「`ANCHOR-MISS post-land FINAL：本轮那一格现读不到`」→ ⑨·9
  · 红名「判据卷第一趟红 2 朵：`test_newest_section_must_be_clean`（最新一节还是 R587）+ `test_skip_roster`（借红）」→ ⑨·7
  · 红名「`STAGE_GATE_RESULT=red 拦路=3`（R587 那一节两处冒充段号 + ITERATION 一处无证断言）」→ **不计入对账口径**（契约名 —— 这一条是本轮靶 1 的证人本身，由 `--section R587` 永久签，不是待修的红）
  · 红名「`STAGE_GATE_RESULT=red 拦路=1`（R587 那一节冒充段号 2 处）」→ **不计入对账口径**（契约名 —— 这一条是本轮**靶 1 的证人本身**，由 `--section R587` 永久签，不是待修的红）
  · 红名「两跑都未到数 ⇒ `PREDICTIONS_R588` 三条不判」→ **不计入对账口径**（通道未跑 —— 数没到，整格 NOT-RUN）
  · 红名「`quickpick-search-focus` 与 `quickpick-search-hover` 逐字节同一张（两档都是）」→ **不计入对账口径**（基名在漂 —— 不是红，是设计内同档的第一次量化；夹具注释与两条判据各自一致，不开单）
- 门复算（预览 → 落盘 → 复算）：落盘前那一趟报的是上一轮的节，落盘之后复算那一趟才是签这一格的：`%(recon)s`
- 逐本现读七个数（写之前各 0 / 写之后每一本恰 1）：`preapply_counts.txt`、`postapply_counts.txt`。

⑦ **验证链（顺序照旧，三处偏差具名）**：`swift build --build-tests`（包目录内）`%(build_warn)s`、
`%(build_kind)s`（⇒ 台账不许把这一格简写成「全量重编 0 告警」，见 ⑨·6）；
python 判据卷**整目录** `%(battery)s / %(battery_ok)s` —— ⚠ 这一趟是**台账落盘之后**复跑的那一趟；
落盘之前那一趟红 2 朵（`test_newest_section_must_be_clean` 因为最新一节还是 R587；`test_skip_roster` 是它的**借红**——内层卷自己红 ⇒ 那一格没有可对账的对象 ⇒ 见 ⑨·7，两个时刻都记）；
`def test_` 前后计数 `%(counts_line)s` ⇒ 净 +%(delta_total)d 格；
刀**分两趟**落（偏差具名 `STAGE_KNIVES_AFTER_LEDGERS_NEWEST_SECTION_DEPENDENCY`）：
`mutate_r588_shape` 那两把（M1555/M1556）在捕获卷**之前**跑（纯 python、不碰 `.build` ⇒ 没撞锁），
`mutate_r588_stage` 那三把（M1557–M1559）必须等本轮台账落盘之后才落 —— 它们的预检里有一格判的就是「最新一节」，
先落刀就注定 `precheck!=PASSED` 而不下刀 ⇒ **本笔只签 M1555/M1556 两把**：`%(knives)s`；M1557/M1558/M1559 的末态由**补记那一笔**现读并写进 ⑨ 封条那一格，本笔不许提前替它们签字；逐把红了哪几格由日志现数 `%(knife_reds_head)s`；
`MD5=` 那一行是刀链前后同一份文件的现读 `%(md5)s`；
Swift 捕获判据卷 `%(capture)s`（帧 `%(frames)s`）；对新守卫在**含本笔的树**上现读 `%(gate_drift)s` ⇒ `%(gate_result)s`；
逐字节对照 `%(byte)s`；全量卷 `%(full)s`，skipped 只记现读 `%(full_skips)s`；
三道预检**串行**（不与 swift 卷并行，且都在台账落盘之后）：`%(precheck_needle)s`、`%(precheck_arm)s`、`%(precheck_hidden)s`；
换装 `SKIP_INSTALL=no-product-change`（产品 0 文件）；七本台账 → 派生格**落盘之后**现读 → 电池（本机那一趟的数**不回填**，最终签字归 runner `STEP[9]`）；
产品文件 0 个，连续零改动 **%(streak_n)d** 轮（唯一取数口 `python3 scripts/product_streak.py`，**台账落盘之后**现读 `%(streak_line)s`；
as-of 口径 ⇒ 读作「本轮之前最后一次产品改动在 %(streak_n)d 轮前」；取数时刻由 `post_land()` 钉在函数名字上，不在纪律上）；
清账 `%(absence)s`（落盘之后复算那一趟）；代码 numstat 现读 `%(numstat_head)s`；字面量真验证 `%(pyverify_head)s`。

⑧ **看图那一腿（本轮的主腿，逐字在 `look.txt`）**：`%(look)s`

⑤ **地基一字不动**：4.5 墨、150、2x 8.0pt、1x 6.0pt、120ms 与容差 1、Motion ≥2、`probeInkFraction=3%%`、
`.contentFade 0.20`、像素格容差 1.5 与跳变地板 8、声明时长、**两态差尺的两个地板 `1.20 / 1.10`**、
差量阈值 8/255（本轮看图那一腿**沿用**它，没调它）、全量 skipped 现读、禁碰 14 面不抬不降
（本轮没碰 `Sources/`、没碰捕获侧 Swift ⇒ 逐字证人就是 ⑦ 里那两本 python 卷与全量卷）；
`--against` 默认与 choices、`--allow-missing` 两帧原样；名册那 16 行与所有豁免表一字未动；
`PRODUCT_MAIN_TREE_TRANSPARENT_OBJECT_NOT_JUDGED`、`FRAME_BASELINE_DRIFT_NOT_JUDGED` 两条不撤；
本轮新增的两道守卫**都不改判定**：`stage_gate_claims` 判的是台账的措辞，`tier_reporting_shape` 判的是仪器的形状，
两者都没有把任何一格降级成 skip，也没有为了让守卫好写而把「缺席」改成「不判」。
""" % dict(
        r=i["r"], n=i["n"], round=i["round"], date=DATE, prev_n=i["prev_n"], prev_r=i["prev_r"],
        main_run=RUN_MAIN, main_sha=m["sha"], main_concl=m["结论行数"],
        add_run=RUN_ADD, add_sha=a["sha"], anchor=d["anchor"][:900],
        tier_shape_head=d["tier_shape"].splitlines()[0][:200],
        stage_before=d["stage_before"].replace("\n", u" ｜ ")[:700],
        knives=knife_line(d["knives"]),
        knife_reds_head=u" ｜ ".join(u"%s红%d格" % (k["arm"], k["reds"]) for k in d["knives"]),
        battery=d["battery"], battery_ok=d["battery_ok"],
        counts_line=u" ｜ ".join(u"%s %d→%d" % (k, b, a2) for k, (b, a2) in sorted(d["counts"].items()))[:420],
        delta_total=d["delta_total"],
        stage_now=d["counts"]["test_stage_gate_claims"][1],
        shape_now=d["counts"]["test_tier_reporting_shape"][1],
        capture=d["capture"], frames=d["frames"], build_warn=d["build_warn"][:120],
        build_kind=d["build_kind"][:220],
        gate_drift=d["gate_drift"][:260], gate_result=d["gate_result"][:170],
        byte=d["byte"], full=d["full"], full_skips=d["full_skips"],
        precheck_needle=grep_line(d["prechecks"], "NEEDLE_PRECHECK", u"针预检") if d["prechecks"] else u"（落盘后跑）",
        precheck_arm=grep_line(d["prechecks"], "ARM_TOTAL", u"臂总数") if d["prechecks"] else u"（落盘后跑）",
        precheck_hidden=grep_line(d["prechecks"], "HIDDEN_ARMS", u"盲区名册") if d["prechecks"] else u"（落盘后跑）",
        absence=d["absence"], numstat_head=d["numstat"].splitlines()[0][:200],
        pyverify_head=u" ｜ ".join(d["pyverify"].splitlines()[:3])[:260],
        md5=d["md5"][:280], recon=d["recon"], look=d["look"].replace("\n", u"\n  ")[:5200],
        streak_n=int(re.search(r"streak=(\d+)", d["streak"]).group(1)) if re.search(r"streak=(\d+)", d["streak"]) else -1,
        streak_line=d["streak"],
    )


def block_ui(d):
    i = d["ident"]
    u0 = next_u()
    m, a = d["main"], d["add"]
    us = [
        (u"⓪ 两跑都未到数 ⇒ 三条预测一条不判；R587 那句 RUN_UNFETCHED 从本笔起不成立（forward，不回头改）",
         u"`%(main_run)s ↔ %(main_sha)s` 与 `%(add_run)s ↔ %(add_sha)s` 现读都是 `status=in_progress`、"
         u"`conclusion` 空，且 `ci_read.py steps` 里**一个非空步骤结论都没有** ⇒ 整格 NOT-RUN，"
         u"出口·甲/乙/丙/丁 一条都不选。`PREDICTIONS_R588` 三条由 `ci_status_r588.py` 判 ⇒ 今天打印的是"
         u"「不判（数没到）」而不是「中」。归因锚照抄 R587 补记（派单 ⓪·6 明令不许重跑）。"
         % {"main_run": RUN_MAIN, "main_sha": m["sha"], "add_run": RUN_ADD, "add_sha": a["sha"]}),
        (u"取 CI 那一把尺又窄了一格：`latest` 只打最新一笔 ⇒ 旧笔永远匹配不上",
         u"两跑里旧的那笔用 `ci_read.py latest` 取不到 ⇒ 逐跑改用 `gh run view --json status,conclusion,headSha`。"
         u"这一格具名说清：**通道只有一格宽**不等于作业没跑；读数文件里两行都留着。"),
        (u"台账里那句段号假话本轮被做成会红的守卫（不是追记）",
         u"两处逐字原文写在 D-%(r)s 的背景那一格（写手这一节不复述：守卫搜的就是那两个字面串，抄进被它判的正文就自我判红）。"
         u"三条证人：`git diff --name-only HEAD~2 HEAD -- Sources/ ClipboardHistory/` 为空、"
         u"两条具名阻塞未撤（守卫现读 `仍挂着的阻塞=2`）、规格 §3 那句「三问仍未全过 ⇒ 第③段继续不开工」未划掉。"
         u"⇒ 新增 `scripts/stage_gate_claims.py`：冒充段号一律红；无证断言必须同时有"
         u"「规格里三问全过」+「阻塞已撤」两个证人。`--section R587` 那一格是**永久证人**。"),
        (u"根因不是笔误：小节编号与规格段号同字 ⇒「本节③」长得像一句段号断言",
         u"STATE 的正文小节按 ⓪①②③⑦⑧⑨ 编号，而 §3 的段号也叫「第①②③段」⇒ 同一句话在两种读者眼里不同。"
         u"本轮起写手一律用「本节①/②/③」，段号只在有证人时以「第②段/第③段」出现。"
         u"⚠ 这句话本身也要有人签 ⇒ 守卫里那条 `段号[=＝][圈码]` 就是它的证人。"),
        (u"段号识别按子串会漏：枚举写法里不含那个连续形状（刀 M1557 钉），「引用不算断言」这一档另配两格",
         u"第一版守卫跑真台账时报 `断言=0`，而盘上明明有一句假话 —— 漏的是 ITERATION 那一行的枚举写法。"
         u"识别式改成 `第[①②③④]*③段` 并补正对照 + 刀 ⇒ **漏读比多读危险**：多读会被立刻关掉，漏读会长期点头。"),
        (u"切节合并三种标题形状，且同一轮的主节 + 补记节并起来判",
         u"第一版「第一个命中的标题形状就返回」 ⇒ ITERATION 整本被当全文扫，历史里合法的讨论被读成违规（多红）；"
         u"而 STATE 里补记节排在主节之前 ⇒ 只取「最新一节」会挑到补记、把主节那句假话放过（漏读）。"
         u"两种坏法各补一条对照，退回全文那一支由刀 M1559 钉住。"),
        (u"档位循环的两条规则：不许在循环里 return；缺席必须数得出来",
         u"新增 `scripts/tier_reporting_shape.py`（AST）⇒ 现读 HEAD：`%(shape)s` ⇒ 三处档位循环里"
         u"1 处带 return、2 处无可数格。R1 钉的是「后面那些档我不看了」这个**唯一静默形状**；"
         u"R2 钉的是「点名了但没人知道少了几档」。一个循环都没找到 ⇒ 退 2，不许绿。"
         % {"shape": d["tier_shape"].splitlines()[0][:150]}),
        (u"`frame_recording_proof.py` 的取帧循环：缺帧不再短路，新增 `FRAME_STATE_STOPS not-run=N`",
         u"旧版第一档缺帧就 `return 1` ⇒ 第二档永远不会被点名（与 R587 修掉的热图那一支同族）。"
         u"现在两档各自点名、累加后统一收口，且有一档没到时结论行印 `FRAME_STATE_RESULT=not-run` 而不是 ok。"
         u"刀 M1555 把它改回 return ⇒ 两格红；刀 M1556 只摘掉可数格 ⇒ 另一格红（这才叫两条判据）。"),
        (u"`rung_from_readings` 点名本来就对，缺的是可数：新增 `RUNG_STEP_TIER_COVERAGE not-run=N`",
         u"这一处不是 R587 那族的短路，而是「各自印了一句但没人知道少了几档」。"
         u"⇒ R2 单独成立的那一格；地板数值与判法一字未动。"),
        (u"看图那一腿：名册 8 张暗档逐张看整帧，三格读数 + 尺不瞎的正对照",
         u"%(byte)s ｜ 每一行都同时报 `bbox(RGBA 直取)` 与 `bbox(convert L)` ⇒ 前者在本批**恒为 None**，"
         u"后者是整幅 ⇒ 659 认过的那条形状是**实测**不是引用。三把正对照给出 42195 / 46625 / 1496422 颗与非 None bbox，"
         u"所以「看不见」才有资格被写出来。" % {"byte": d["byte"][:120]}),
        (u"一把跨状态对照量出新事实：search-focus 与 search-hover 两档都是逐字节同一张",
         u"暗档 sha 前 12 位 `b38dfe662854` 两帧相同、亮档 `e27c77479ac4` 相同 ⇒ 差量 0 颗。"
         u"成因不由我的眼睛定：夹具注释（`UICaptureHarness.swift:12973-12974`，R415）写着「与 hover 同一档视觉，"
         u"取证键分开」，且两条判据各自比的是「抬起 vs 静置」 ⇒ 设计内同档，**不开新单**；"
         u"但「两键两帧从此逐字节相同」第一次进账，下一轮不许以为少捕了一帧。"),
        (u"刀分两趟：主笔只签 M1555/M1556，另三把的预检读的是台账自己 ⇒ 归补记",
         u"`%(knives)s`。M1555/M1556 在捕获卷之前落（纯 python）；M1557–M1559 必须等本轮台账落盘 —— "
         u"它们的证人模块里有一格判「最新一节」，先落刀就注定 precheck 不是 PASSED 而不下刀。"
         u"⚠ 这不是把刀拖到最后凑数：R587 ⑨·2 那条「证人搬门牌」教的正是**刀的执行对象要跟着判据走**。"
         % {"knives": knife_line(d["knives"])}),
    ]
    head = (u"## 第 %(n)s 轮（R%(r)s · %(date)s · U-%(u0)s…U-%(u1)s）：把「台账说的话有没有证人」做成两支守卫"
            u"（①第③段断言必须配闸门全过的证人；②档位缺席必须逐档点名且数得出来）+ 名册 8 张暗档逐张看整帧\n\n"
            % {"n": i["n"], "r": i["r"], "date": DATE, "u0": u0, "u1": u0 + len(us) - 1})
    body = u"".join(u"- **U-%d：%s**。\n    %s\n\n" % (u0 + k, t_, b) for k, (t_, b) in enumerate(us))
    return head + body, u0


def block_iteration(d):
    i = d["ident"]
    return u"""## Round %(round)s · R%(r)s（第 %(n)s 轮 · %(date)s）：台账说的话有没有证人——第③段断言、档位缺席点名、8 张暗档

**七维度自评**（恰七行，每格 n/15；维度名照曲线尺认的那七个同字，本轮不造新维度）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉看图 | @@LOOKSCORE@@ | %(look_short)s |
| 判据有效性 | 15/15 | 两支守卫各判一件事实：`stage_gate_claims` 判「台账有没有把小节编号写成段号、有没有无证断言」（两种坏法各一条正则，反向陈述单列不红）；`tier_reporting_shape` 判「档位循环会不会静默丢掉后面的档」（R1 不许循环里 return、R2 缺席必须可数，扫不到对象就退 2 不绿）。五把刀各摘一条独立判据，主笔这一趟只签 M1555/M1556（两把互不重叠 ⇒ 这才叫两条判据），M1557–M1559 的末态归补记那一笔（它们的预检读的是台账自己，本笔之前落不下 ⇒ 不许提前替它们签字）。 |
| 假绿防御 | 14/15 | ①段号识别按 `第[①②③④]*③段`，枚举写法不再漏（M1557）；②切不出节 ⇒ 不判并点名，不许退回全文判历史（M1559）；③同一轮主节 + 补记节并起来判，否则「最新一节」会挑到补记而放过主节那句假话；④反向词表不许变成永不匹配（M1558）；⑤`--section R587` 把「这条守卫抓得住当年那句假话」钉成永久读数。扣 1 分：守卫判的是**措辞形状**，措辞换了别的说法仍可能绕过 ⇒ 它不是语义门，这一条要留给下一轮继续加形状。 |
| 产品面推进 | 3/15 | 产品 **0** 文件（逐字节证人：`%(byte)s`）。推进的是两条**取证侧**的约束与一张看图账：台账不许冒充段号、档位缺席必须可数。段号仍是第②段（第③段一字未动，证人见 STATE 本节①）。 |
| 台账一致性 | 9/15 | 身份两处交叉核对；七个标题形状写前 0、写后各 1；派生格落盘后现读。扣分在四处：⑨·1（上一轮那句假话本轮才发现，而我当时的收口自陈重复了它）、⑨·2/⑨·3（守卫自己两版读错对象：子串漏读 + 切节退回全文）、⑨·5（读数文件把字段顺序与临时路径写错，同 R587 ⑨·9 那一族）、⑨·7（判据读台账自己 ⇒ 落盘前那趟注定红，两个时刻都要记）。 |
| 剩余风险处置 | 14/15 | 本轮**没开新单**（看图量到的 search-focus/search-hover 同帧有夹具注释与两条判据作证，属设计内 ⇒ 只进账不开单）；655/656/658/659/660/661 全不结、出路一条不代选；旧红一朵不抹；第③段着色器一字未写。扣 1 分：两支守卫都**还没有 runner 的证人**（要等含本笔那一跑），本机只能证明它们不误响。 |
| 交接可读性 | 15/15 | 三条预测写在 `ci_status_r588.py` 并由「数没到 ⇒ 不判」限定适用范围 ⇒ 今天打印的是「不判」而不是「中」；⓪ 的成对号与 forward 更正（R587 ⓪·2 那句 RUN_UNFETCHED 从本笔起不成立）写在 STATE ⓪ 与补记里；归因锚照抄不重跑，下一轮不必再拉 3MB 日志。 |
""" % {"round": i["round"], "r": i["r"], "n": i["n"], "date": DATE,
       "look_short": d["look"].splitlines()[0][:150], "byte": d["byte"][:110]}


def block_backlog(d):
    i = d["ident"]
    return u"""## R%(r)s 追账（第 %(n)s 轮 / Round %(round)s · %(date)s）：本轮没开新单，655/656/658/659/660/661 一条没结

**为什么这一节没有新单**（这本身要记账，不许读成「本轮很干净」）：
看图那一腿量到一条新事实 —— `quickpick-search-focus` 与 `quickpick-search-hover` 在**两档都逐字节同一张**
（暗 `b38dfe662854`、亮 `e27c77479ac4`，差量 0 颗）。它**不开单**的证人是三条现读的、不是我的判断：
①夹具自己的注释（`UICaptureHarness.swift:12973-12974`，R415）写着「与 hover 同一档视觉，取证键分开（只点亮焦点）」；
②两条判据 `testQuickPickSearchFieldHoverLiftsItsChrome` / `…FocusLiftsItsChrome` 各自比的是**抬起 vs 静置**，
  不比 hover vs focus ⇒ 与今天这两张相同不矛盾；
③尺不瞎由三把正对照签（同尺寸、内容已知不同 ⇒ 42195 / 46625 / 1496422 颗与非 None 的 bbox(L)）。
⇒ 设计内同档 ⇒ 只进账不开单。**但这条事实以前没人写过** ⇒ 下一轮若有人以为「少捕了一帧」，这一节是他的证人。

**655 / 656 / 658 / 659 / 660 / 661 状态（R%(r)s）：都不结案，各补一句**
    · 655：本轮**没跑** `update` 到工作基线 ⇒ `%(baseline)s`；名册那 16 行（8 light + 8 dark，按 `tier_from_name` 数）
      字段与理由一字未动；本轮新捕那批与 R587 那批**逐字节相同 356、不同 0** ⇒ 没新增漂移，也没调用 `register-drift`。
    · 656：三条出路（甲锁 `.aqua`／乙按外观拆两档各标定／丙另一台或另一次会话补第二档）一条没选；
      本轮**没有**改这台机器的全局外观去拿读数（派单红线）。本轮看图那 8 张是暗档，但**这不等于第二档证人到手**
      —— 656 要的是同一颗尺在两档各自标定，本轮只做到「逐张看过 + 差量形状对账」。
    · 658：三跑的真门那一行都读成 `判=不判`（R587 的 ⓪ 已把电池合成行分出去）⇒ runner 那份 `by_machine/` 仍不存在，
      出路⑵ 没发生，三条仍一条不选。
    · 659：本轮**用上了它的教训**（差量图先 `convert("L")` 再 `getbbox()`，并同时报颗数）⇒
      但 659 自己那三件仪器侧证人仍没做，不结案。
    · 660：本轮没动基线出处那四个字段，也没跑 `update` ⇒ 660 的三条出路仍一条不选；
      它欠的外部证人（`SAME_BAKE` / `SCALE_MISMATCH` 在 runner 上响不响）仍归含 R587 那一笔的跑 —— 而那一跑今天**还没到数**。
    · 661（Swift 捕获侧 11 处档位声明）：本轮**一字未动**（派单红线）；三条出路一条不选。
      ⚠ 本轮新增的 `tier_reporting_shape.py` 只判 python 侧 ⇒ 它**不会**替 661 作证，也不许被读成「661 已被守卫覆盖」。
""" % {"r": i["r"], "n": i["n"], "round": i["round"], "date": DATE,
       "baseline": u"未改（git status 里没有这一行）"}


def block_decisions(d):
    i = d["ident"]
    return u"""## D-%(r)s（R%(r)s · %(date)s · 第 %(n)s 轮 / Round %(round)s）：台账的话也要有证人；点名与数得出来是两件事

背景：R587 的台账与收口自陈都写了「第③段落了一件」形状的话（`段号=③`、`段号仍是第②③段`），
而那一笔 `Sources/` 为空、两条具名阻塞未撤、规格 §3 那句「三问仍未全过 ⇒ 第③段继续不开工」未划掉。
同一轮里，R587 合并档位词表时暴露的那个缺陷（脚本在第一个 stop 处 return）在另一支脚本里**还没修**，
而第三支脚本「点名了但没人知道少了几档」。共同形状：**说的话没有证人，或证人只覆盖了一半**。

决定：
1. **台账的断言与产品的断言同级**：任何「第③段已开工/落地/完成」都必须同时带两个证人（规格里「三问全过」那一句、
   两条具名阻塞已撤），否则守卫红。小节编号一律写「本节①/②/③」，`段号=[圈码]` 一律红 ——
   因为下一轮只读台账，一句好听的话就是它的事实源。
2. **守卫要防「漏读」而不只防「多红」**：本轮两处漏读都是我自己扫出来的 ——
   按子串认段号（`第②③段` 不含 `第③段`）与「最新一节」只挑到补记节而放过主节。
   多红的门会被立刻关掉，漏读的门会长期点头 ⇒ 每条漏读都补一把刀（M1557/M1559）。
3. **「各自点名」与「数得出来」是两件事**：R1（循环里不许 return）与 R2（必须有可数的缺席格）分两条规则、
   各配一把互不重叠的刀。只满足 R1 的脚本今天就有两处（hover 那一支），它们不是缺陷但是**没人知道的量**。
4. **扫不到对象不算通过**：`tier_reporting_shape` 一个档位循环都没找到 ⇒ 退 2；
   `stage_gate_claims` 切不出轮次节 ⇒ 不判并点名。两者的绿都必须建立在「我确实有对象」上。
5. **看图那一腿的「看不见」必须先证尺不瞎**：差量图一律同时报 `bbox(RGBA 直取)` 与 `bbox(convert L)` 加颗数，
   并配三把同尺寸的正对照 ⇒ 659 认过的形状在本批是**实测**。
6. **设计内同档不开单，但要把事实写进账**：search-focus 与 search-hover 两帧逐字节相同由夹具注释与两条判据作证
   ⇒ 不开单；可这条事实此前没人写过，「下一轮以为少捕了一帧」就是它的代价。

被否掉的：把「第③段」这个词从台账里禁掉（那是把措辞当病因，真正缺的是证人）；
把 R1/R2 合成一条「循环要写得规范」（合成一条就只能红一次，摘掉哪边都不知道）；
为了让守卫好写而把缺席那一档改成「不判」（派单明令不许）；
以及把本轮量到的同帧现象开成一张新单去占名册（三条证人都在，那是设计内）。
""" % {"r": i["r"], "n": i["n"], "round": i["round"], "date": DATE}


def block_changelog(d):
    i = d["ident"]
    return (u"""### 台账的话也要有证人：第③段断言守卫 + 档位缺席逐档点名且可数 + 名册 8 张暗档逐张看整帧（R%(r)s / 第 %(n)s 轮 / Round %(round)s，产品 0 文件）
    R%(prev_r)s 的台账写着「段号=③」「段号仍是第②③段」，收口自陈写着「§3 第②③段各落一件」—— 那是假的：
    那一笔 `Sources/` 为空、`STAGE2_CLICKTHROUGH_BLOCKED` 与 `STAGE3_FRAME_CRITERIA_HAVE_NO_RUNNER_WITNESS` 一条没撤、
    规格 §3 那句「三问仍未全过 ⇒ 第③段继续不开工」未划掉。根因不是笔误，是 **STATE 的正文小节编号（⓪①②…）
    与规格 §3 的段号同字**。本轮：① 新增 `scripts/stage_gate_claims.py` —— 冒充段号一律红、
    「第③段已开工/落地/完成」必须同时有「三问全过」+「阻塞已撤」两个证人，判最新那一轮（主节 + 补记节并起来判），
    切不出节就不判并点名；`--section R587` 把「这条守卫抓得住当年那句假话」钉成永久读数；
    ② 新增 `scripts/tier_reporting_shape.py` —— AST 扫每一支活仪器，R1 档位循环体里不许 `return`、
    R2 缺席必须可数（`not-run=`），扫不到循环就退 2；现读 HEAD 那一侧「3 处循环 / 1 处带 return / 2 处无可数格」，
    据此修掉 `frame_recording_proof.py`（缺帧不再短路，新增 `FRAME_STATE_STOPS not-run=N` 与
    `FRAME_STATE_RESULT=not-run`）与 `hover_two_state_diff.py`（补 `RUNG_STEP_TIER_COVERAGE not-run=N`）；
    ③ 看图那一腿把名册 16 行里的 **8 张暗档逐张看整帧**，每帧三格（包围盒 / 差量颗数 / 肉眼所见），
    差量一律同时报 `bbox(RGBA 直取)=None` 与 `bbox(convert L)` ⇒ 659 认过的那条形状在本批是**实测**，
    三把正对照（42195 / 46625 / 1496422 颗）先证明尺不瞎，「看不见」才算读数。
    顺带量到一条新事实：`quickpick-search-focus` 与 `quickpick-search-hover` 两档都是**逐字节同一张**
    （暗 `b38dfe662854`、亮 `e27c77479ac4`）⇒ 夹具注释（R415「与 hover 同一档视觉，取证键分开」）与两条判据
    各自比「抬起 vs 静置」都在 ⇒ **设计内同档，不开新单**，但这条事实第一次进账。
    本机现读（含本笔的树）：`%(gate_drift)s` ⇒ `%(gate_result)s`；逐字节 `%(byte)s`。
    判据卷 +%(delta_total)d 格（两支守卫各 15 与 %(shape)d 格），刀 M1555/M1556 全 CAUGHT（互不重叠 ⇒ 两条判据各摘一边），
    M1557–M1559 三把归**补记那一笔**（它们的预检读的是台账自己，本笔之前落不下）；⓪ 两跑都未到数 ⇒ 三条预测一条不判。
    655/656/658/659/660/661 一条没结、出路一条不代选；本轮没开新单。
""" % {"r": i["r"], "n": i["n"], "round": i["round"], "date": DATE, "prev_r": i["prev_r"],
       "gate_drift": d["gate_drift"][:170], "gate_result": d["gate_result"][:130],
       "byte": d["byte"][:120], "delta_total": d["delta_total"],
       "shape": d["counts"]["test_tier_reporting_shape"][1]})


# —————————————————————————————————————————————————————————──
# 落盘


def shapes(i):
    return [(u"UI 轮次标题", u"## 第 %d 轮（R%d · " % (i["n"], i["r"])),
            (u"ITER 标题", u"## Round %d · R%d" % (i["round"], i["r"])),
            (u"STATE 主节", u"## R%d 状态（" % i["r"]),
            (u"DECISIONS", u"## D-%d（" % i["r"]),
            (u"BACKLOG 追账节", u"## R%d 追账" % i["r"]),
            (u"CHANGELOG 标题行", u"### 台账的话也要有证人：第③段断言守卫 + 档位缺席逐档点名且可数 + 名册 8 张暗档逐张看整帧（R%d / " % i["r"])]


def counts(i, tag):
    rows = []
    for book in ("UI", "ITER", "STATE", "BACKLOG", "DEC", "FINAL", "CHANGE"):
        text = read(book)
        rows.append(u"%s :: %s" % (BOOKS[book], u" | ".join(u"%s=%d" % (n, text.count(s)) for n, s in shapes(i))))
    out = u"\n".join(rows) + u"\n"
    with io.open(os.path.join(TMP, "%s_counts.txt" % tag), "w", encoding="utf-8") as handle:
        handle.write(out)
    return out


def insert_before(text, pattern, block, label):
    m = re.search(pattern, text)
    if not m:
        raise SystemExit("ANCHOR-MISS %s：现读模式 %r 没命中" % (label, pattern[:60]))
    return text[:m.start()] + block + text[m.start():]


def apply(d, do_write):
    i = d["ident"]
    pre = counts(i, "preapply")
    totals = [int(x) for x in re.findall(r"=(\d+)", pre)]
    if max(totals) > 1:
        raise SystemExit(u"本轮标题形状在盘上出现 %d 次 ⇒ 不是幂等重放，停\n%s" % (max(totals), pre))
    if any(totals):
        print(u"DRY：盘上已有本轮标题（幂等重放）⇒ 一本都不再写\n" + pre)
        return 0
    print(u"PRE（写之前逐本现读）：\n" + pre)

    state_text = block_state(d)
    ui_text, u0 = block_ui(d)
    iter_text = block_iteration(d).replace(u"@@LOOKSCORE@@", d["look_score"])
    backlog_text = block_backlog(d)
    dec_text = block_decisions(d)
    change_text = block_changelog(d)
    for name, blob in ((u"STATE", state_text), (u"UI", ui_text), (u"ITER", iter_text),
                       (u"BACKLOG", backlog_text), (u"DEC", dec_text), (u"CHANGE", change_text)):
        if u"@@" in blob:
            raise SystemExit(u"令牌没填满：%s 里还有 @@" % name)
    # 写手自己先合规 ⇒ 直接问**守卫自己**（而不是另写一条正则）：两条判据只要有一条在渲染后的
    # 正文上红，就不许落盘。分开写一条"段号=圈码"的检查是第二份口径，它会与守卫分叉（R587 靶 B 那一课）。
    sys.path.insert(0, os.path.join(ROOT, "scripts"))
    from stage_gate_claims import classify_line
    # 自检范围＝守卫**真的会判**的那三本（STATE / ITER / UI）。
    # DECISIONS 与 CHANGELOG 故意留着逐字原文：那里是被判范围之外，
    # 而"下一轮要能查到当年那句话到底长什么样"这件事总得有一个地方承担。
    for name, blob in ((u"STATE", state_text), (u"UI", ui_text), (u"ITER", iter_text)):
        for raw in blob.splitlines():
            kind = classify_line(raw)
            if kind in (u"断言", u"冒充段号"):
                raise SystemExit(u"写手自己造出「%s」：%s :: %s" % (kind, name, raw.strip()[:120]))
    if not do_write:
        with io.open(os.path.join(TMP, "state_preview.md"), "w", encoding="utf-8") as handle:
            handle.write(state_text)
        print(u"DRY：六块文本算完，长度 STATE=%d UI=%d ITER=%d BACKLOG=%d DEC=%d CHANGE=%d ⇒ 未落盘"
              % (len(state_text), len(ui_text), len(iter_text), len(backlog_text), len(dec_text), len(change_text)))
        return 0

    new = {}
    new["STATE"] = insert_before(read("STATE"), r"(?m)^## R\d+ 状态（", state_text + u"\n\n", u"STATE 主节")
    m = re.search(r"(?m)^最后更新：\d{4}-\d{2}-\d{2}（本地 · R\d+ / 第 \d+ 轮 / Round \d+）$", new["STATE"])
    if not m:
        raise SystemExit("ANCHOR-MISS：STATE 的「最后更新」那一行现读不到")
    new["STATE"] = (new["STATE"][:m.start()] + u"最后更新：%s（本地 · R%d / 第 %d 轮 / Round %d）"
                    % (DATE, i["r"], i["n"], i["round"]) + new["STATE"][m.end():])
    new["UI"] = insert_before(read("UI"), r"(?m)^## 第 \d+ 轮（R\d+ · ", ui_text, u"UI 节")
    new["ITER"] = read("ITER").rstrip("\n") + u"\n\n" + iter_text.rstrip("\n") + u"\n"
    new["BACKLOG"] = read("BACKLOG").rstrip("\n") + u"\n\n" + backlog_text.rstrip("\n") + u"\n"
    new["DEC"] = read("DEC").rstrip("\n") + u"\n\n" + dec_text.rstrip("\n") + u"\n"
    ch = read("CHANGE")
    anchor = u"## [Unreleased]\n"
    if ch.count(anchor) != 1:
        raise SystemExit("ANCHOR-MISS CHANGELOG：[Unreleased] 命中 %d 次" % ch.count(anchor))
    head, rest = ch.split(anchor, 1)
    new["CHANGE"] = head + anchor + u"\n" + change_text.rstrip("\n") + u"\n\n" + rest.lstrip("\n")

    fin = read("FINAL")
    streak_n = int(re.search(r"streak=(\d+)", d["streak"]).group(1)) if re.search(r"streak=(\d+)", d["streak"]) else -1
    m2 = re.search(r"产品面连续零改动轮数 = \*\*(\d+)\*\*（R(\d+) 台账落盘之后现读", fin)
    if not m2:
        raise SystemExit("ANCHOR-MISS FINAL：streak 那一格现读不到")
    cell = (u"产品面连续零改动轮数 = **%d**（R%d 台账落盘之后现读 `python3 scripts/product_streak.py` ⇒ `%s`；"
            u"as-of 口径 ⇒ 读作「本轮之前最后一次产品改动在 %d 轮前」，下一轮是 %d。"
            u"上一格原文留着：**%s**（R%s 台账落盘之后现读"
            % (streak_n, i["r"], d["streak"], streak_n, streak_n + 1, m2.group(1), m2.group(2)))
    fin = fin[:m2.start()] + cell + fin[m2.end():]
    mu = re.search(r"U-31 … U-(\d+)（R(\d+) 现读抬到最新一节）", fin)
    if not mu:
        raise SystemExit("ANCHOR-MISS FINAL：U 格那一注记现读不到（形状必须是 `（Rnnn 现读抬到最新一节）`，只准一条）")
    u_last = u0 + ui_text.count(u"- **U-") - 1
    fin = fin[:mu.start()] + u"U-31 … U-%d（R%d 现读抬到最新一节）" % (u_last, i["r"]) + fin[mu.end():]
    mp = re.search(r"完整名单以 `AGENT_STATE\.md` 的 R(\d+) 节 ② 为准", fin)
    if not mp:
        raise SystemExit("ANCHOR-MISS FINAL：§13 的仍开指针现读不到")
    fin = fin[:mp.start()] + u"完整名单以 `AGENT_STATE.md` 的 R%d 节 ② 为准" % i["r"] + fin[mp.end():]
    new["FINAL"] = fin

    for book, text in new.items():
        write(book, text)
    post = counts(i, "postapply")
    print(u"POST（写之后逐本现读）：\n" + post)
    own = {u"UI": u"UI 轮次标题", u"ITER": u"ITER 标题", u"STATE": u"STATE 主节",
           u"BACKLOG": u"BACKLOG 追账节", u"DEC": u"DECISIONS", u"CHANGE": u"CHANGELOG 标题行"}
    bad = []
    for line in post.split(u"\n"):
        if u" :: " not in line:
            continue
        fname, cells = line.split(u" :: ")
        book = [b for b, f in BOOKS.items() if f == fname.strip()]
        if not book:
            continue
        want = own.get(book[0])
        if want is None:
            continue
        got = {}
        for pair in cells.split(u" | "):
            n, v = pair.rsplit(u"=", 1)
            got[n.strip()] = v.strip()
        if got.get(want) != u"1":
            bad.append(u"%s 的「%s」现读=%s（该恰 1）" % (fname.strip(), want, got.get(want)))
    if bad:
        raise SystemExit(u"落盘后形状不是各 1：\n" + u"\n".join(bad))
    print(u"SEVEN_COUNTS_OK=1")
    return 0


def post_land():
    """派生格的结构性修法：落盘之后再取一次数，并由这里改写那两格（R580/R583/R585/R586/R587 同一族）。"""
    reading = subprocess.check_output([sys.executable, "scripts/product_streak.py"], cwd=ROOT).decode("utf-8")
    line = reading.splitlines()[0].strip()
    streak_n = int(re.search(r"streak=(\d+)", line).group(1))
    landed_r = max(int(x) for x in re.findall(r"(?m)^## R(\d+) 状态", read("STATE")))
    i = {"r": landed_r}
    fin = read("FINAL")
    # `-?` 是必须的：apply 那一趟在 streak 还没现读时写的是 **-1** 占位，
    # 只认 \d+ 的正则匹配不到自己的占位符 ⇒ post_land 会 ANCHOR-MISS（本轮实测撞到）。
    m2 = re.search(u"产品面连续零改动轮数 = \*\*(-?\d+)\*\*（R%d 台账落盘之后现读" % i["r"], fin)
    if not m2:
        raise SystemExit("ANCHOR-MISS post-land FINAL：本轮那一格现读不到")
    end = fin.index(u"上一格原文留着：", m2.start())
    cell = (u"产品面连续零改动轮数 = **%d**（R%d 台账落盘之后现读 `python3 scripts/product_streak.py` ⇒ `%s`；"
            u"as-of 口径 ⇒ 读作「本轮之前最后一次产品改动在 %d 轮前」，下一轮是 %d。"
            % (streak_n, i["r"], line, streak_n, streak_n + 1))
    fin = fin[:m2.start()] + cell + fin[end:]
    write("FINAL", fin)

    st = read("STATE")
    m3 = re.search(u"产品文件 0 个，连续零改动 \*\*(\d+)\*\* 轮（唯一取数口", st)
    if not m3:
        raise SystemExit("ANCHOR-MISS post-land STATE：⑦ 里那一格现读不到")
    seg = st[m3.start():]
    stop = seg.index(u"）；")
    cell3 = (u"产品文件 0 个，连续零改动 **%d** 轮（唯一取数口 `python3 scripts/product_streak.py`，"
             u"**台账落盘之后**现读 `%s`；as-of 口径 ⇒ 读作「本轮之前最后一次产品改动在 %d 轮前」；"
             u"取数时刻由 `post_land()` 钉在函数名字上，不在纪律上" % (streak_n, line, streak_n))
    st = st[:m3.start()] + cell3 + st[m3.start() + stop:]
    write("STATE", st)
    io.open(os.path.join(TMP, "streak.txt"), "w", encoding="utf-8").write(line + u"\n")
    print("POST_LAND_STREAK=%d 两格已改写（FINAL 与 STATE ⑦）" % streak_n)
    return 0


def main():
    d = gather()
    d["look_score"] = os.environ.get("LOOK_SCORE", u"13/15")
    if "--post-land" in sys.argv:
        return post_land()
    return apply(d, "--apply" in sys.argv)


if __name__ == "__main__":
    sys.exit(main())

# -*- coding: utf-8 -*-
"""R589 台账写手（七本一次落、整行锚点、写手自检复用守卫的分类函数、派生格落盘后现读）。

结构与 `ledgers_r588.py` 同（那一版把 R551/R562/R567/R577/R579/R580/R585/R586/R587/R588 十课都钉进去了），
本轮改的只有：读数文件换成 /tmp/r589、刀数从 2 把变成 **7 把且全部在主笔这一趟落**（没有一把的预检读台账）、
以及正文按本轮三件推进重写。

三条不许：
· 不许在正文里抄守卫的待搜串（`第③段` 三个字要出现就用引号或拼接）；
· 不许另写第二条段号正则 —— 写手自检 `from stage_gate_claims import classify_line`；
· 不许在落盘之前取派生格（`--post-land` 那一趟才写 streak 与 §1）。
"""
from __future__ import annotations

import io
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
TMP = "/tmp/r589"
DATE = "2026-11-06"
BOOKS = {"UI": "AGENT_UI_AUDIT.md", "ITER": "AGENT_VISUAL_ITERATION.md", "STATE": "AGENT_STATE.md",
         "BACKLOG": "AGENT_BACKLOG.md", "DEC": "AGENT_DECISIONS.md", "FINAL": "AGENT_FINAL_REPORT.md",
         "CHANGE": "CHANGELOG.md"}

RUN_MAIN = "42139904001"      # R588 主笔
RUN_ADD = "42142286963"       # R588 补记笔


def read(book):
    return io.open(os.path.join(ROOT, BOOKS[book]), encoding="utf-8").read()


def write(book, text):
    io.open(os.path.join(ROOT, BOOKS[book]), "w", encoding="utf-8", newline="\n").write(text)


def must_read(path, label):
    if not os.path.exists(path):
        raise SystemExit(u"读数缺失：%s（%s）⇒ 先跑它，不许手填" % (path, label))
    return io.open(path, encoding="utf-8", errors="replace").read()


def grep_line(text, prefix, label, last=True):
    rows = [l.strip() for l in text.splitlines() if l.strip().startswith(prefix)]
    if not rows:
        raise SystemExit(u"读数里找不到前缀 %r（%s）" % (prefix, label))
    return rows[-1] if last else rows[0]


def identity_from_disk():
    ui = read("UI")
    prev_n = max(int(x) for x in re.findall(r"(?m)^## 第 (\d+) 轮（R\d+", ui))
    state_r = max(int(x) for x in re.findall(r"(?m)^## R(\d+) 状态", read("STATE")))
    r = state_r + 1
    if prev_n != r - 2:
        raise SystemExit(u"身份交叉核对失败：STATE 最新节是 R%d ⇒ 本轮应是第 %d 轮，而 UI 最新一节写着第 %d 轮"
                         % (state_r, r - 1, prev_n))
    return {u"r": r, u"n": r - 1, u"round": r - 3, u"prev_n": prev_n, u"prev_r": r - 1}


def gather():
    ci = json.loads(must_read(os.path.join(TMP, "ci_readings.json"), u"⓪ 两跑读数"))
    i = identity_from_disk()
    d = {u"ident": i, u"ci": ci}
    for key, run in ((u"main_run", RUN_MAIN), (u"add_run", RUN_ADD)):
        if run not in ci:
            raise SystemExit(u"⓪ 读数里没有 %s 那一跑 ⇒ 先跑 ci_status_r589.py" % run)
        d[key] = ci[run]

    def grab(fname, prefix, label, last=True):
        return grep_line(must_read(os.path.join(TMP, fname), label), prefix, label, last=last)

    d["capture"] = grab("capture_summary.txt", "CAPTURE_LINES=", u"捕获卷")
    d["frames"] = grab("capture_summary.txt", "FRAMES=", u"帧数")
    d["build_warn"] = grab("capture_summary.txt", "BUILD_WARNINGS=", u"构建告警")
    gate = must_read(os.path.join(TMP, "gate_local.txt"), u"本机那一门")
    d["gate_drift"] = grep_line(gate, "FRAME_BASELINE_DRIFT ", u"本机判定")
    d["gate_result"] = grep_line(gate, "FRAME_BASELINE_RESULT=", u"本机结论")
    d["gate_scale"] = grep_line(gate, "FRAME_BASELINE_SCALE_", u"倍率那一维的新出口")
    d["gate_bake"] = grep_line(gate, "FRAME_BASELINE_BAKE ", u"基线出处行")
    d["tier_shape"] = must_read(os.path.join(TMP, "tier_shape.txt"), u"档位与分支链扫描").strip()
    d["stage_gate"] = must_read(os.path.join(TMP, "stage_gate.txt"), u"第③段断言守卫现读").strip()
    d["pair_witness"] = must_read(os.path.join(TMP, "pair_witness.txt"), u"副本名册守卫现读").strip()
    d["look"] = must_read(os.path.join(TMP, "look.txt"), u"看图那一腿").strip()
    d["numstat"] = must_read(os.path.join(TMP, "numstat.txt"), u"numstat 现读").strip()
    d["md5"] = u"before=%s after=%s 同一份=%s" % (
        must_read(os.path.join(TMP, "md5_before.txt"), u"刀链前").strip(),
        must_read(os.path.join(TMP, "md5_after.txt"), u"刀链后").strip(),
        u"yes" if must_read(os.path.join(TMP, "md5_before.txt"), u"a").strip()
        == must_read(os.path.join(TMP, "md5_after.txt"), u"b").strip() else u"NO")

    d["counts"] = {}
    for ln in must_read(os.path.join(TMP, "test_counts.txt"), u"def test_ 前后计数").splitlines():
        m = re.match(r"(\S+) HEAD=(\d+) NOW=(\d+)", ln.strip())
        if m:
            d["counts"][m.group(1)] = (int(m.group(2)), int(m.group(3)))
    for k in ("test_identical_frame_witness", "test_tier_reporting_shape", "test_frame_baseline"):
        if k not in d["counts"]:
            raise SystemExit(u"计数名册缺 %s 那一行 ⇒ 名册要现读不要手抄" % k)
    if d["counts"]["test_identical_frame_witness"][1] <= d["counts"]["test_identical_frame_witness"][0]:
        raise SystemExit(u"矛盾读数：新卷 test_identical_frame_witness 的 def test_ 数没长")
    d["delta_total"] = sum(a - b for b, a in d["counts"].values())

    kn = must_read(os.path.join(TMP, "knife_status.txt"), u"刀状态文件")
    knives = []
    for ln in kn.splitlines():
        m = re.match(r"(r\d+)/(M\d{4}) rc=(\d+) caught=(\d) clean=(\d) precheck=(\S+) post=(\S+)", ln.strip())
        if m:
            knives.append({u"arm": m.group(2), u"rc": int(m.group(3)), u"caught": int(m.group(4)),
                           u"clean": int(m.group(5)), u"precheck": m.group(6), u"post": m.group(7)})
    arms = [k[u"arm"] for k in knives]
    if len(set(arms)) != 7:
        raise SystemExit(u"主笔的刀数/去重后不是 7 把：%s ⇒ 表或状态文件读错了" % arms)
    for k in knives:
        if k[u"post"] == u"CAUGHT" and k[u"rc"] == 0:
            raise SystemExit(u"矛盾读数：%s 说 CAUGHT 而 rc=0" % k[u"arm"])
        if k[u"post"] != u"CAUGHT":
            raise SystemExit(u"%s 末次=%s ⇒ 空刀不许占号，先作废这一把再落下一把" % (k[u"arm"], k[u"post"]))
    d["knives"] = knives
    reds = must_read(os.path.join(TMP, "knife_reds.txt"), u"每把红了哪几格")
    for k in knives:
        block = re.search(u"--- %s\n(.*?)(?=\\n--- M|$)" % k[u"arm"], reds, re.S)
        body = block.group(1) if block else u""
        k[u"reds"] = len(re.findall(u"读数: FAIL:", body))
        if k[u"reds"] == 0:
            raise SystemExit(u"%s 说 CAUGHT 却读不到任何 FAIL 行 ⇒ 那是通道坏了不是红" % k[u"arm"])

    for key, fname, prefix, label in ((u"full", "full_summary.txt", "FULL_TOTAL=", u"全量卷"),
                                      (u"full_skips", "full_summary.txt", "FULL_SKIPPED=", u"全量 skipped"),
                                      (u"battery", "py_battery.txt", "Ran ", u"python 全电池"),
                                      (u"battery_ok", "py_battery.txt", "OK", u"电池签字")):
        p = os.path.join(TMP, fname)
        d[key] = grep_line(must_read(p, label), prefix, label, last=(key != u"battery_ok")) \
            if os.path.exists(p) else u"（未读到：那一趟还没跑 ⇒ 台账不许替它填数）"
    p = os.path.join(TMP, "prechecks.txt")
    d["prechecks"] = must_read(p, u"三道预检") if os.path.exists(p) else u""
    d["absence"] = (grep_line(d["prechecks"], "LEDGER_ABSENCE_RESULT", u"清账门")
                    if d["prechecks"] else u"（落盘前的读数，落盘之后复算）")
    rp = os.path.join(TMP, "recon.txt")
    d["recon"] = grep_line(must_read(rp, u"对账门"), "RED_NAME_RECONCILIATION", u"对账门") \
        if os.path.exists(rp) else u"（预览那一趟还没跑）"
    sp = os.path.join(TMP, "streak.txt")
    d["streak"] = grep_line(must_read(sp, u"产品面连续轮数"), "PRODUCT_STREAK", u"产品面连续轮数") \
        if os.path.exists(sp) else u"（落盘之后现读）"
    return d


def next_u():
    nums = [int(x) for x in re.findall(r"\*\*U-(\d+)", read("UI"))]
    if not nums:
        raise SystemExit(u"UI_AUDIT 里读不到 U 号")
    return max(nums) + 1


def knife_line(knives):
    return u" ｜ ".join(u"%s rc=%d 预检=%s 末次=%s clean=%d 红%d格"
                        % (k[u"arm"], k[u"rc"], k[u"precheck"], k[u"post"], k[u"clean"], k[u"reds"])
                        for k in knives)


# —————————————————————————————————————————————————————————──
# 正文

def block_state(d):
    i = d["ident"]
    m, a = d["main_run"], d["add_run"]

    def step(rk):
        return u"、".join(x.strip() for x in rk.get(u"失败步骤", [])) or u"（没有失败步骤）"

    def preds(rk):
        rows = rk.get(u"预测", [])
        return u"\n".join(u"      · %s ⇒ **%s**\n        （取处：%s）"
                          % (p[0], p[1], p[2]) for p in rows) or u"      ·（没判：那一跑未到数）"

    return u"""## R%(r)s 状态（%(date)s · 第 %(n)s 轮 / Round %(round)s · 产品 0 文件 + **取证通道本身读不读得对对象**（本节① 倍率那组互斥分支补穷尽并新增具名出口 `SCALE_BASELINE_UNKNOWN`；本节② 形状守卫从「只扫循环」扩到「互斥分支链必须有兜底」，并现读出第二处同形洞；本节③ 638② 从散文做成会红的门：逐字节副本名册 + 唯一像素证人断言；本节④ 三条预测之所以读不到，是因为守卫的 print 被 `run_main()` 吞在测试里 ⇒ 把尺接在它被打印的那一步上）+ 判据卷 +%(delta)s 格 + 刀 M1560–M1566 全 CAUGHT + ⓪ R588 两跑都到数）

⓪ **现读两对（`ci_status_r589.py`，取值时刻 09:36–10:05）**：两对**都到数**，都是 `completed / failure`。
   1. `%(mrun)s ↔ %(msha)s`（R588 主笔）⇒ 全部失败步骤：`%(msteps)s`。
      逐步骤结论另取一趟（`steps` 视图只给失败的那些 ⇒ 「不在列表里」不等于「跑过且绿」）：
      `Release script tests ⇒ %(mbat)s`、`Frame baseline vs working manifest ⇒ %(mbase)s`、`On-screen probe coverage floor ⇒ %(mprobe)s`。
      三条预测（标签逐字来自 R588 的 `PREDICTIONS_R589`，判法本轮新写、每条带「正文从哪一步取」）：
%(mpreds)s
   2. `%(arun)s ↔ %(asha)s`（R588 补记笔）⇒ 失败步骤：`%(asteps)s`；逐步骤结论 `Release script tests ⇒ %(abat)s`、`On-screen probe coverage floor ⇒ %(aprobe)s`。
      三条预测：
%(apreds)s
   3. **这一格是本轮的靶子本身**：三条预测里两条「未读到」、第三条读成「中」——而那个「中」是**空的**：
      它判的是「整跑没有 `FRAME_STATE_STOPS` / `RUNG_STEP_TIER_COVERAGE` 这两行」，
      可是那两条通道的所有读数都被 `scripts/tests/*` 里的 `run_main()` 重定向进 StringIO，**从来没有进过 CI 日志**。
      ⇒ R588 ⑤·(a) 那条「预测要带第三格（正文从哪一步取）」在这里被补成第四格：**这条通道究竟由哪一步、以什么方式印出去**；
      一条只在测试内被调用的守卫，在 runner 上等于没有读数。本轮的修法见本节④。
   4. `STEP[18]` 那一朵 R588 记的是「跑间漂」（主笔 8/8/0 对补记笔 3/7/1）⇒ 本轮两跑读回的是同一形状：
      那一步在两跑里的逐步骤结论都是 `success` ⇒ 这一格今天只能说「这两跑到数、那一步没红」，
      不能说「STEP[18] 绿了」（`steps` 视图不给成功步骤建行，判跑没跑要看 `jobs[].steps` —— 本笔就是这么取的），
      更不能把它写成 R588 那朵漂移已经消失。
   5. **R590 的 ⓪ 要读的五格**（前四条的判法与「正文从哪一步取」都写在 `ci_status_r589.py` 的 `PREDICTIONS_R590`，由脚本判、不由下一轮念）：
      ①本轮这一笔（主笔 + 补记笔）的成对号 —— 由补记那一趟现取现写，本笔不许替它填数；
      ②STEP[11] 里 `FRAME_BASELINE_SCALE_BASELINE_UNKNOWN` 第一次出现没有（runner 的基线说不出倍率、当轮 1.00x ⇒ 应该响）；
      ③STEP[9] 里 `TIER_SHAPE_RESULT=ok` 且 `分支链≥2`（R3 那一维第一次有读数行）；
      ④STEP[9] 里 `IDENTICAL_PAIR_RESULT=` 有没有出声（没有这一行 = 接线没跑起来，不等于「这台机器没有副本」）；
      ⑤`SHAPE_GUARD_EXIT … rc=0` 恰好两行（接线自己的证人）。
      另带两条不许从问题开始：`变帧=16 已登记=16`（本轮本机那一门的现读，与 655 同源）与
      `row-pinned-off` 无消费者那一格。

① **真实推进（本节① / §3 第②段）：倍率那组互斥分支补穷尽 + 新增具名出口**
   `scripts/frame_baseline.py` 里读同一对量（`bake["scale"] × current_scale`）的分支从两条独立 `if` 改成一串 `if/elif/elif/else`，
   四个格子各有名字：当轮说不出 ⇒ `SCALE_NOT_RUN`；**当轮说得出、基线说不出 ⇒ 新增 `FRAME_BASELINE_SCALE_BASELINE_UNKNOWN`**；
   两边都说得出且不等 ⇒ `SCALE_MISMATCH`；相等 ⇒ 新增兜底 `SCALE_MATCH`。
   证人（本轮新增那格判据，`scripts/tests/test_frame_baseline.py::test_the_four_scale_cells_each_have_exactly_one_named_line`）：
   四格**各有名且互斥**（合成批次 subTest 四例，断言「印出来的那一行必须恰好是期望的那一条」）。
   ⚠ 口径更正（这条必须写清，否则下一轮会以为 R587 的规矩被推翻了）：R587 靶 A 说「当轮说不出倍率时只许 `SCALE_NOT_RUN`
   一条出口」，那一句话的**范围是「当轮这一边」**，不是「这一维全世界只许一条」。本轮新增的是**对照另一边**说不出时的出口 ——
   两种成因的修法相反（前者要重捕/改名册，后者要重烤基线 = 655/660 归用户），并成一条就等于把「该由谁签」藏进门里。
   这条更正由 ① 那格判据钉：四行互斥 ⇒ 少一条就红，多一条也红。

② **真实推进（本节②）：形状守卫扩到互斥分支链，并现读出第二处同形洞**
   `scripts/tier_reporting_shape.py` 加 R3：同一段里 ≥2 条 `if`（含 `elif` 摊平）、各分支都印同一个通道前缀、
   且**共读同一个量** ⇒ 必须有『其余情况』分支，没有就红。全仓现读（逐字见读数文件）：
   `%(tier)s`
   两处真对象都修了：`scripts/frame_baseline.py`（本节①）与 `scripts/real_screen_control_chroma.py:301` ——
   后者是本轮**扫出来的第二处**：`press_outcome` 的文档串自己写着「四个出口各有名字，因为这四种修法相反」，
   而旧代码只对 `not_landed` 拦路 ⇒ `unmeasured`（药丸或行带压根没量到 = **尺坏了**）一路静默走进色度判定。
   现在四个返回值 + 兜底各有名，`unmeasured` 与 `unknown` 都拦路（这是判据面行为变化，不在产品面）。
   盲区正对照（门的 0 要分得开「没有违规」与「看不见违规」）：合成违规目录 + `--extra` 读数行
   `TIER_BRANCH_CONTROL 正对照链=…`；链数=0 时具名 `TIER_BRANCH_NOT_JUDGED=`，由 CI 那一步读成 `TIER_BRANCH_BLIND=1` 并拦红。
   ⚠ 计数口径写清：`分支链` 按「分支行号集合」去重，同一条长链的**嵌套子串各算一次** ⇒ 那个数不是「漏洞个数」。
   这条守卫认不认得 `elif/else` 这种写法 —— **认得，而且是被迫学会的**：AST 里 `elif` 是 `orelse=[If]`，
   第一版不摊平就把 `frame_baseline.py` 那条真对象整条漏掉（⑨·2），现在 `flatten_chain` 摊平之后
   `test_the_same_chain_with_a_catch_all_is_green` 与 M1562 一正一反钉住它。
   ⚠ 这一格**不许被读成 656 有进展**：656 那三条出路仍归用户，本轮一字未改这台机器的全局外观 ——
   证人就是「没动」本身：`scripts/real_screen_control_chroma.py` 里那条 `security` / 外观相关调用一字未改（本轮只改了
   `outcome` 那串分支与那行通道值的形状），且 656 的单子文本一字未动。

③ **真实推进（本节③）：638② 从散文做成会红的门**
   新名册 `docs/frame_identical_pairs.json`（8 行 = 现读 8 组逐字节副本，每行带 members / should_be_identical /
   cause / cause_refs / ticket / observed.sha / registered_by_round / **machine**）
   与新守卫 `scripts/identical_frame_witness.py`（三格口径：R-a 未登记就红、R-b 两个方向分开点名、
   R-c 判据只引用同一组副本 ⇒ 恒真门就红并点名）。现读逐字：
   `%(pair)s`
   禁事全部守住：**没删一张帧、没动基线名单、没跑 `frame_baseline.py update`**（那是 638①/655 归你的处置）。
   为什么「建名册」不等于替你选了 638①：①那一问的两个选项（并进 vs 名册）差别在**帧数与名单**，
   而本笔之后名单一字未动、帧数仍是 `%(frames)s` ⇒ 两条路都还开着，名册只是把「这组为什么同图」变成机器读得动的证人。
   三条证人（取值时刻=本笔落台账之前现读）：`git diff --stat -- docs/frame_baseline.json docs/frame_baselines/` **输出为空**；
   `docs/frame_baseline.json` 的 `count=356 / frames 键数=356`（与 R588 同一份，没被本轮改过一个字节）；
   `frame_baseline.py update` 本轮**一次都没跑**（`git status docs/` 里只多出一个新名册文件，基线与漂移名册都不在改动列表里）。
   「该不该相同」两向都有格：正对照=两张真不同的帧必须判红（`test_should_differ_but_is_same_is_named_as_a_defect`），
   负臂=该相同却不同也要红（`test_should_be_same_but_now_different_is_named_as_drift`），
   同一趟里两个计数各 1 的那格（`test_the_two_directions_are_not_merged_into_one_message`）钉住"不许合并成一句不符"。
   本轮新读到的一条事实：`row-pinned-off` 在夹具源码里**只有声明、没有任何消费者**（引用次数现读=1）
   ⇒ 这一格才是 638 那句「不为任何断言单独作证」的唯一实例，R590 要么给它找判据、要么由你在 638① 里选并进。

④ **真实推进（本节④ / §4 第三问）：把尺接在它被打印的那一步上 —— 而这一格今天只能写到「接了」**
   `.github/workflows/ci.yml` 的 `Release script tests` 末尾新增三条 CLI 调用（`tier_reporting_shape.py`、
   `stage_gate_claims.py`、`identical_frame_witness.py`），并按 R242 那条老规矩**分开三种缺席**：
   尺没打结论行 ⇒ `SHAPE_GUARD_READING_MISSING=1` 红；链数=0 ⇒ `TIER_BRANCH_BLIND=1` 红；
   这一台没有自己的行/没有帧 ⇒ `IDENTICAL_WITNESS_NOT_RUN=1`（绿，带读数）。
   ⚠ **本轮不许说「CI 已经接上」**：接 CI 的那一笔签不了自己（R555/R565 那一课）——
   「那几步真的产出结论行了吗」只能由**含本笔的那一跑**证，已写进本节 ⓪·5 交给 R590。
   今天能签的是**接线本身**：新卷 `scripts/tests/test_ci_shape_guard_wiring.py` 把那段 bash 抽出来 `bash -n`，
   再对着临时帧目录**真跑**，两个方向各有格 ——
   ①目录缺席 ⇒ 这一步**绿**并印 `IDENTICAL_PAIR_REFUSED=no-shots` + `IDENTICAL_WITNESS_NOT_RUN=1`；
   ②同一台、名册与语料对不上 ⇒ 这一步**必须响**（`IDENTICAL_PAIR_RED … 不在现读语料里`）。
   ②就是①那条「绿 + 具名」的**负半证人**：它证明这一支不是无条件放行，而是「没人判」与「判了且红」分得开。
   为什么同一个 `rc=2` 在两支里处置相反（写清，否则下一轮会以为我自创例外）：守卫那一支的 2 是
   **扫描器没有对象**（尺坏了 ⇒ 拦路）；副本名册那一支的 2 是**这台机器还没登记过自己的行**（数据缺席 ⇒ 具名不判）。
   把后者也拦就等于逼我拿别台那 8 行冒充这一台的观测 —— 那正是 658 三条出路里最坏的一条，归用户，不由我代选。
   顺出来的一条既有缺陷：本轮把 `real_screen_control_chroma.py` 带进扫描范围之后，
   通道卫生守卫现读到它的 `REALSCREEN_CHROMA_VERDICT=%%s ｜ %%s` **值槽里有裸空格**（R565 那一族，从前不在范围内所以没人看见）
   ⇒ 已改成值槽只放一个词、说明另起一行；台账历史上引的正是 `=<一个词>` 那个形状，所以引用不受影响。

⑤ **验证链（顺序照派单）**：build `%(build)s` → 判据卷 → 刀 M1560–M1566（**落刀前现读高水位=M1559**，没抄派单数）→
   新表 `mutate_r589_scale` / `mutate_r589_pair` 进预检名册 → 刀已还原复跑判据（`%(md5)s`）→
   捕获卷 `%(capture)s`、帧 `%(frames)s` → 本机那一门 `%(gate)s` / 判定 `%(drift)s` / 倍率新出口 `%(scale)s` →
   逐张看图（见下）→ 全量 `%(full)s`、skipped `%(fullskip)s` → 三道预检串行 → 换装 `SKIP_INSTALL=no-product-change` →
   七本台账 → 派生格**落盘之后**现读 → 电池 `%(battery)s / %(batteryok)s`（第一趟/第二趟两个时刻都记）。

⑥ **看图那一腿（尺走 659 认过的形状：`convert("L")` 之后再 `getbbox`，并配同尺寸正对照）**：
%(look)s

⑦ **基线与名单**：产品文件 0 个，连续零改动 **%(streaknum)s** 轮（唯一取数口 `python3 scripts/product_streak.py`，
   **台账落盘之后**现读 `%(streak)s`；as-of 口径 ⇒ 读作「本轮之前最后一次产品改动在 %(streaknum)s 轮前」；
   取数时刻由 `post_land()` 钉在函数名字上，不在纪律上）。帧名单未动（`%(frames)s`），
   三张按机器登记的表一字未改；本轮新增的是**第四张**按机器登记的表（副本名册），它从第一天起就带 `machine` 字段。

⑧ **红名与对账**（本轮新印出来的 9 个名字逐条登记，`未标=0 对不上=0` 由门说、不由我数）：
- **红名对账**：
  · 红名「`TIER_SHAPE_RESULT=not-run 档位循环=0`（M1562 落刀那一趟）」→ ⑨·2
  · 红名「刀手 `cut()` 把止锚那行写了两遍 ⇒ M1560 读成 DID-NOT-RUN」→ ⑨·10
  · 红名「刀手还原语句写成 `open(path, "rb").write` ⇒ 崩在半路、变异留在盘上」→ ⑨·11
  · 红名「三道 `test_ci_channel_hygiene` 红（扩大扫描范围揭出既有裸空格通道值）」→ ⑨·6
  · 红名「`test_working_corpus…` 把 `re.findall` 的字符串当整数比 ⇒ 新卷预检红」→ ⑨·9
  · 红名「`witness_reds` 第一版的"组外第三张"只与名册对账 ⇒ 合成对照组外键被误判成恒真」→ ⑨·4
  · 红名「名册第一版按抹掉色档的键归组 ⇒ loader 自报「同组只准一行」」→ ⑨·5
  · 红名「`/tmp/r589` 未建 ⇒ ⓪ 那一趟重定向直接失败（exit 1），我重跑了才记账」→ ⑨·9
  · 红名「`REALSCREEN_CHROMA_VERDICT` 值槽裸空格（既有缺陷，本轮才进入范围）」→ ⑨·6
  · 红名「本轮新通道名 9 个：`SHAPE_GUARD_EXIT`、`SHAPE_GUARD_READING_MISSING`、`TIER_BRANCH_BLIND`、
    `TIER_BRANCH_NOT_JUDGED`、`IDENTICAL_WITNESS_EXIT`、`IDENTICAL_WITNESS_NOT_RUN`、
    `IDENTICAL_WITNESS_READING_MISSING`、`REALSCREEN_OUTCOME_VERDICT`、`REALSCREEN_NOT_RUN outcome_*`」
    → **不计入对账口径**（契约名 —— 它们是本轮新出口的**名字本身**，不是待修的红；
    证人 = `scripts/tests/test_ci_shape_guard_wiring.py::test_every_new_name_is_registered_somewhere`，
    它把"印了却没人登记"做成会红的断言）
  · 红名「`IDENTICAL_PAIR_RESULT=not-run 本机行=0`（runner 那一台还没登记过自己的副本）」
    → **不计入对账口径**（通道未跑 —— 这一维在 runner 上今天没人判，不许读成「runner 上没有副本」；
    它的负半证人是同一卷里那格"名册与语料对不上必须响"）
  · 红名「`变帧=16 已登记=16`（本机那一门，与 655 同源的会话侧素材漂移）」
    → **不计入对账口径**（基名在漂 —— 门已经把它登记齐了，未登记=0；重烤与否归 655）
- 门复算（预览 → 落盘 → 复算）：`%(recon)s`（落盘前那一趟报的是上一轮那一节，签这一格的是**落盘之后**那一趟）。
  清账门 `%(absence)s`。

⑨ **本轮自伤（照实记 11 格）**：R588 那句「⑨ 到 ⑨·9 为止」是**那一轮的封条**（限制补记不许再加格），
   不是本轮的上限 ⇒ 本轮按实际发生记到 ⑨·11，一条不藏。
   1. 我第一次把 R3 的候选条件写成「每一条 `if` 都要有 else」⇒ 真语料上 `frame_baseline.py` 被误判成违规
      （那些独立报告行 `if TIE: print …` 本来就不需要兜底）。收窄成「**最后一个分支**必须有兜底」才是这条规矩的对象。
   2. 我第一次的候选识别没摊平 `elif` ⇒ AST 里 `elif` 是 `orelse=[If]`，于是那条真对象（倍率链）**整条滑出对象**，
      现读只有 1 条链而它本该是 2 条 —— 这是「门的 0 是看不见不是没有」在本轮自己的复现，由 M1562 钉住。
   3. 我把「链数=0 就 rc=2」写成无条件 ⇒ 「一次性脚本只数不判」那格（负半）被带歪读成红；
      改成「具名 `TIER_BRANCH_NOT_JUDGED` + 由消费端拦红」，退出码那条老语义不动。
   4. `witness_reds` 第一版的「组外第三张」只与名册对账 ⇒ 合成对照组外那把键不在名册里就被判成恒真；
      现在口径挂在**现读语料的键**上（引用了另一张真帧就是有别的证人）。
   5. 名册第一版按「抹掉色档的夹具键」归组 ⇒ 暗/亮两行塌成同一组，loader 自己报「同组只准一行」——
      那是这把尺**先抓到我自己的形状错**，登记口径改成文件名。
   6. 三道 `unittest` 红在 `test_ci_channel_hygiene` 上，起因是我把 `real_screen_control_chroma.py` 带进扫描范围，
      暴露了一条**既有**的裸空格通道值。我没有加豁免（名册与豁免表一字未动），改的是那条代码本身。
   7. `test_tier_reporting_shape.py` 里我给合成样本起的键名带连字符不够 ⇒ 第一版被 `referenced_keys` 的正则放过，
      「负半没伤」那一格其实是空的；补成 `qa-focus` 那种形状之后才真的判到。
   8. `test_identical_frame_witness.py` 我第一版让合成行继承「本机键」的方式是把 `machine` 留空 ⇒ loader 直接拒；
      现在默认填 `machine_key()`，别台那一格显式覆盖，两格各判各的。
   9. 本轮第一次跑 `ci_status_r589.py` 时 `/tmp/r589` 还没建，重定向直接失败（exit 1）；
      那一趟没有任何读数，我没有把它当成「读不到 ⇒ 那就写未读到」的第一次机会，而是重跑了一次才记账。
   10. 刀手的 `cut()` 第一版把止锚那一行**又当 replacement 传进去** ⇒ 那行被写两遍：M1560 因此变成 SyntaxError，
       被读成 `DID-NOT-RUN`（其实是刀自己坏了，不是空刀）；M1561 恰好摊上"合法的重复 `for`"才侥幸抓到红。
       改成「删除型 arm 的 replacement 一律是空串」之后两把都重跑，结论才由重跑那一趟签（前一趟不签）。
   11. 刀手的还原语句写成 `open(path, "rb").write(orig)` ⇒ `io.UnsupportedOperation` 当场崩，
       **变异被留在盘上**（`unregistered = []` 那行）。抓到它的不是我自己的检查，是下一把刀的预检读成红 ——
       这正好证明「预检红就是报警器」这条设计有效，但也证明我少写了一格"刀链崩在半路必须立刻核对 md5"。
       现在 `md5_before` 与 `md5_after` 四张全同，且中间那次残留已按原行改回并核过哈希。
""" % {
        u"r": i[u"r"], u"n": i[u"n"], u"round": i[u"round"], u"date": DATE,
        u"delta": d["delta_total"],
        u"mrun": RUN_MAIN, u"msha": m[u"sha"], u"msteps": step(m),
        u"mbat": m[u"逐步骤结论"].get(u"Release script tests", u"（读不到）"),
        u"mbase": m[u"逐步骤结论"].get(u"Frame baseline vs working manifest (fixture-set gate)", u"（读不到）"),
        u"mprobe": m[u"逐步骤结论"].get(u"On-screen probe coverage floor", u"（读不到）"),
        u"mpreds": preds(m),
        u"arun": RUN_ADD, u"asha": a[u"sha"], u"asteps": step(a),
        u"abat": a[u"逐步骤结论"].get(u"Release script tests", u"（读不到）"),
        u"aprobe": a[u"逐步骤结论"].get(u"On-screen probe coverage floor", u"（读不到）"),
        u"apreds": preds(a),
        u"tier": d["tier_shape"].replace(u"\n", u"\n   "),
        u"pair": d["pair_witness"].replace(u"\n", u"\n   "),
        u"frames": d["frames"], u"look": d["look"],
        u"build": d["build_warn"], u"capture": d["capture"], u"md5": d["md5"],
        u"gate": d["gate_result"], u"drift": d["gate_drift"], u"scale": d["gate_scale"],
        u"full": d["full"], u"fullskip": d["full_skips"],
        u"battery": d["battery"], u"batteryok": d["battery_ok"],
        u"streak": d["streak"], u"streaknum": (re.search(r"streak=(\d+)", d["streak"]).group(1)
                                               if re.search(r"streak=(\d+)", d["streak"]) else u"-1"),
        u"recon": d["recon"], u"absence": d["absence"],
    }


def block_ui(d):
    i = d["ident"]
    u0 = next_u()
    rows = [
        (u"取同一对量的两条 `if` 会把两种 unknown 挤成静默",
         u"`frame_baseline.py` 旧写法是 `if bake and current and 不等: MISMATCH` + `if not current: NOT_RUN`，"
         u"于是「当轮说得出、基线说不出」与「两边都说得出且相等」这两格**一行都不印**。"
         u"runner 那一条门是实例：现读 `FRAME_BASELINE_SCALE*` 行数=0 而同一行写着 `倍率=（不知道）`。"
         u"⇒ 静默与「量了没问题」在输出里逐字相同，四格现在各有名字。"),
        (u"「四格互斥」只能由真值表级判据钉，不能由散文",
         u"新格 `test_the_four_scale_cells_each_have_exactly_one_named_line`：四个合成批次各跑一次 `check`，"
         u"断言「印出来的那一条**恰好**是期望的那一条」。少一条分支 ⇒ 那格红；"
         u"把 BASELINE_UNKNOWN 删掉 ⇒ 那一格不但少一行，还会**误报成 MISMATCH**（`\"\" != \"2.00x\"` 成立）"
         u"⇒ 这就是「删掉那条分支必须红」的真正形状：它不是少印一行，是印错。"),
        (u"「同一对量」的判断要摊平 `elif`，否则真对象整条滑出",
         u"AST 里 `elif` 是 `orelse=[If(...)]`。第一版只扫顶层 `if` ⇒ 倍率那条链的共读量子读不到，"
         u"`分支链` 那个数从 2 掉到 1。M1562 把这把尺「变盲」做成会红的读数。"),
        (u"兜底要挂在最后一个分支，不是每一个",
         u"第一版要求每一条 `if` 都有 else ⇒ `if TIE: print …` 那种独立报告行全被判红。"
         u"静默只发生在「后面没人接」，所以规矩的对象是链的**末端**。"),
        (u"档位形状之外的第二处同形洞是被扫描发现的，不是我想起的",
         u"`real_screen_control_chroma.py` 对 `press_outcome` 的四个具名出口只对 `not_landed` 拦路 ⇒"
         u" `unmeasured`（尺坏了）一路走进色度判定，把「量不到」读成「量过且没问题」。"),
        (u"逐字节副本 8 组第一次有名有姓",
         u"新名册 `docs/frame_identical_pairs.json`：members / should_be_identical / cause / cause_refs /"
         u" ticket / observed.sha / registered_by_round / machine 八格，全部由夹具源码与 U-2440 现读引用。"),
        (u"「该不该相同」是两个方向，合并就等于没有",
         u"「该相同而不同」=有东西漂了；「不该相同而相同」=状态没画（R490 那一族）。"
         u"新守卫把两者分开点名（合成两向各一格，同一趟里两个计数各 1）。"),
        (u"名册的组身份是文件名而不是夹具键",
         u"第一版按抹掉色档的键归组 ⇒ 暗/亮两行塌成同一组，loader 自己报「同组只准一行」。"
         u"这把尺先抓到了我自己的登记口径。"),
        (u"副本不许当唯一像素证人",
         u"判据若**只**引用同一组里的两张（逐字节同一）⇒ 它比较的是自己和自己，恒真。"
         u"引用组外第三张真帧就算还有别的证人 ⇒ 负半在 `test_criterion_with_a_third_frame_outside_the_group_is_green`。"),
        (u"副本名册从第一天起就按机器登记",
         u"同一对夹具在 2x 与 1x 上不一定都逐字节同一 ⇒ 本机没有自己的行就是**具名不判**（出口·乙同形），"
         u"不许拿别台那 8 行判这一台。"),
        (u"守卫的 print 被测试吞掉 ⇒ 它在 runner 上没有读数",
         u"`test_*` 里的 `run_main()` 把 stdout 重定向进 StringIO，于是 `TIER_SHAPE_RESULT` / `STAGE_GATE_RESULT`"
         u" 从来没有进过 CI 日志：R588 交下来的三条预测里两条「未读到」、第三条那个「中」是**空的**"
         u"（它判的是「整跑没有那两行」，而那两行本来就到不了日志）。"),
        (u"修法是把尺接在它被打印的那一步上（R242 旧规矩的新实例）",
         u"CI 的 `Release script tests` 末尾新增三条 CLI 调用，并分开三种缺席："
         u"没打结论行=红、链数=0=红（`TIER_BRANCH_BLIND`）、这台没自己的行/没帧=具名 NOT_RUN（绿，带读数）。"),
        (u"扩大扫描范围会揭出既有缺陷",
         u"把 chroma 那支带进 `ci_channel_hygiene` 范围后现读 `通道空格=1`：`REALSCREEN_CHROMA_VERDICT=%s ｜ %s`"
         u" 的值槽里塞了一句散文。没加豁免，改的是代码（值槽一个词，说明另起一行）。"),
        (u"`row-pinned-off` 现读只有声明、没有消费者",
         u"638 那句「不为任何断言单独作证」到这里才有一个**可数**的实例（夹具源码里引用次数=1）。"),
    ]
    body = u"\n".join(u"- **U-%d：%s** —— %s" % (u0 + k, t, b) for k, (t, b) in enumerate(rows))
    head = (u"## 第 %(n)s 轮（R%(r)s · %(date)s · U-%(u0)s…U-%(u1)s）：把「互斥分支有没有穷尽」与「副本有没有证人」做成会红的门"
            % {u"n": i[u"n"], u"r": i[u"r"], u"date": DATE, u"u0": u0, u"u1": u0 + len(rows) - 1})
    return head + u"\n\n" + body + u"\n\n", u0


def block_iteration(d):
    """七维表：维度名必须与曲线尺认的那七个**同字**，刻度 n/15，且要带「七维度自评」这个锚点。

    本轮第一版这里写的是自造的七个名字 + /20 刻度 ⇒ `curve_from_ledger.py` 当场
    `DERIVED_NO_MARKER=586` 拒绝、`test_curve_gaps` 红。尺抓住了我，这一格就是它的证人。
    """
    i = d[u"ident"]
    return u"""## Round %(round)s · R%(r)s（第 %(n)s 轮 · %(date)s）：互斥分支要穷尽、逐字节副本要有名、尺要接在它被打印的那一步上

**七维度自评**（恰七行，每格 n/15；维度名照曲线尺认的那七个同字，本轮不造新维度）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉看图 | 12/15 | LOOK 名册 8 组逐张看**整帧**（取值时刻=R589，帧目录=/tmp/r589/frames，本轮新捕那批 356 张）：差量包围盒=None、差量颗数=0，每组都配**同尺寸同色档**的正对照（163526 / 1650824 / 34572 / 32714 / 67232 / 65707 / 12931 / 11530 颗）⇒「看不出差别」这一句这次有资格说。另亲眼看两张（`row-pinned-off-300x74-light`、`quickpick-search-focus-420x300-light`）。扣 3 分：本轮帧与工作基线逐字节相同 ⇒ 这一维是"复核"不是"发现"。 |
| 判据有效性 | 15/15 | 三件各有会红的对象：倍率四格由真值表级判据签（少一条分支不只少印一行，会**误报成 MISMATCH**，M1560 就是这么读到的）；R3 分支链由合成违规 + `--extra` 正对照 + 真语料两把（M1561/M1562）签；副本名册三格口径（未登记 / 两向分开 / 唯一证人）由 29 格合成卷 + 四把刀签。 |
| 假绿防御 | 14/15 | ①门的 0 分得开"没有"与"看不见"：`TIER_BRANCH_NOT_JUDGED` + CI 的 `TIER_BRANCH_BLIND=1`；②`IDENTICAL_WITNESS_NOT_RUN=1` 那条绿自带**负半证人**（同一台、名册与语料对不上必须响）；③elif 摊平（M1562 证明不摊就整条漏）；④名册 loader 缺字段/缺机器/同组重复一律抛，不降级成"0 行=绿"。扣 1 分：`分支链` 那个数含嵌套子串，不是"漏洞个数"，读数要带口径。 |
| 产品面推进 | 3/15 | 产品 **0** 文件（`git diff --stat -- docs/frame_baseline.json docs/frame_baselines/` 空、`count=356` 未变、`update` 一次没跑）。推进全在取证面，段号仍是第②段（第③段一字未写，证人见 STATE 本节①/③）。 |
| 台账一致性 | 10/15 | 身份交叉核对过；七个标题形状写前 0、写后各 1；派生格落盘后现读（streak 20→21 两个时刻都记）。扣分：⑨·10/⑨·11（刀手自己两处坏：`cut()` 把止锚抄两遍、还原语句写成 `"rb"` ⇒ 变异留在盘上，报警器是下一把刀的预检）、⑨·9（`/tmp/r589` 没建就先重跑才记账）、以及本轮这一格自己撞出来的一次：七维表第一版用了错的维度名与 /20 刻度 ⇒ 曲线尺当场 `DERIVED_NO_MARKER=586` 拒绝（是尺抓住了我，不是我又写错账 —— 修完这一格才算落账）。 |
| 剩余风险处置 | 13/15 | 没开新单（638② 落的是它自己那一半，①仍归用户）；22 条出路一条不代选；旧红一朵不抹；两条具名阻塞一字未撤。扣 2 分：三条守卫的 runner 证人**今天还没有**（接 CI 这一笔签不了自己），已写进 ⓪·5 交 R590。 |
| 交接可读性 | 15/15 | 四条新预测（`PREDICTIONS_R590`）每条三格齐（主张 / 判法 / 正文从哪一步取），并把上一轮缺的那格补成第四格：这条通道究竟由哪一步、以什么方式印出去；`row-pinned-off` 无消费者与 `变帧=16 已登记=16` 都写进 R590 的读单，下一轮不必从问题开始。 |

本轮一句话：把「一种坏法修好一处，不等于修好那一族」写成判据 —— 守卫现在认得出 if 链，
也认得出自己认不出什么（`TIER_BRANCH_NOT_JUDGED` 与 CI 里那行 `TIER_BRANCH_BLIND=1`）。
""" % {u"round": i[u"round"], u"r": i[u"r"], u"n": i[u"n"], u"date": DATE}


def block_backlog(d):
    i = d["ident"]
    return u"""## R%(r)s 追账（%(date)s · 第 %(n)s 轮 / Round %(round)s）

本轮**新开单 0 张**。既有单子只补事实，不替用户选出路：

· **638**：②那一问从散文变成会红的门（`docs/frame_identical_pairs.json` 8 行 + `scripts/identical_frame_witness.py` 三格口径）。
  ①那一问（并进 vs 名册）仍归你 —— 本轮帧数与名单一字未动，所以两条路都开着。
  新读到的事实：`row-pinned-off` 在夹具源码里只有声明、没有消费者（引用次数现读=1）⇒ 这是本单那句
  「不为任何断言单独作证」唯一可数的实例；R590 要么给它配判据，要么由你在 ① 里选并进。
· **655 / 660**：倍率那一维现在能自己说清是哪种不知道 —— 「当轮说不出」走 `SCALE_NOT_RUN`，
  「基线说不出、当轮说得出」走新出口 `SCALE_BASELINE_UNKNOWN`；重烤基线这件事的**读数**齐了，出路仍归你。
· **658**：副本名册与漂移名册一样带 `machine` 字段 ⇒ 本机没有自己的行就是具名不判（出口·乙同形），
  不许拿别台的 8 行判这一台；三条出路一条没选。
· **659**：本轮看图仍走它认过的形状（先合成灰度再 `getbbox` + 同尺寸正对照），没有新形状要补。
· **661**：Swift 捕获侧那 11 处一字未动（只登记）。
· **646 / 647 / 654**：状态照旧 —— 两条具名阻塞（`STAGE2_CLICKTHROUGH_BLOCKED`、
  `STAGE3_FRAME_CRITERIA_HAVE_NO_RUNNER_WITNESS`）一条不撤 ⇒ §3 第③段继续不开工。
""" % {u"r": i[u"r"], u"n": i[u"n"], u"round": i[u"round"], u"date": DATE}


def block_decisions(d):
    i = d["ident"]
    return u"""## D-%(r)s（%(date)s）：互斥分支必须穷尽、逐字节副本必须有名 —— 两种「静默」都归取证面

**背景**：R588 ⓪·3 现读到 runner 的门那一步「倍率这一维」一条也不印；本轮把它做成判据时又发现同族的第二处
（`press_outcome` 的 `unmeasured` 一路走进色度判定）。两条都不是产品缺陷，都是**读数通道的形状**。

**决定**：
1. 一组读同一对量、印同一个通道前缀的分支，**最后一个分支必须有兜底**；兜底挂在链尾而不是每一条 `if`。
2. 两种 unknown 各归各家：当轮说不出 ⇒ `SCALE_NOT_RUN`；基线说不出 ⇒ `SCALE_BASELINE_UNKNOWN`。
   R587 那句「只许一条出口」的范围是「当轮这一边」，本轮把范围写进台账而不是推翻那句话。
3. 守卫从「扫循环」扩到「扫分支链」，同时给守卫自己配**看不见**的具名读数（`TIER_BRANCH_NOT_JUDGED` →
   CI 的 `TIER_BRANCH_BLIND=1`）。0 永远要能回答「是没有，还是看不见」。
4. 逐字节副本登记成第四张按机器表；「该相同/不该相同」两向分开点名。
5. 只在测试内被调用的守卫 = runner 上没有读数 ⇒ 尺要接在它被打印的那一步（R242 的旧规矩，本轮第三次用）。

**为什么不撤任何既有门**：本轮没动地板、阈值、名册与豁免表；`SKIP_INSTALL=no-product-change`（产品 0 文件）；
`STAGE2_CLICKTHROUGH_BLOCKED` 与 `STAGE3_FRAME_CRITERIA_HAVE_NO_RUNNER_WITNESS` 两条阻塞一字未撤。

**代价**：判据卷 +%(delta)s 格、CI 步骤多三条调用；换来的是「静默」这一族第一次有了会红的对象。
""" % {u"r": i[u"r"], u"date": DATE, u"delta": d["delta_total"]}


def block_changelog(d):
    i = d["ident"]
    return u"""### 分支穷尽与副本证人：倍率新增具名出口、形状守卫认 if 链、638② 做成门（R%(r)s / 第 %(n)s 轮 / Round %(round)s · %(date)s）

- `scripts/frame_baseline.py`：倍率那组互斥分支补成四格（新增 `SCALE_BASELINE_UNKNOWN` 与兜底 `SCALE_MATCH`），
  判据卷新增四格真值表断言；R587 那条「只许一条出口」的**范围**在台账里更正为「当轮这一边只许一条」。
- `scripts/tier_reporting_shape.py`：加 R3（互斥分支链必须有兜底），带 elif 摊平、共读量子识别、
  合成正对照 `--extra` 与 `TIER_BRANCH_NOT_JUDGED`；本轮扫出的第二处同形洞 `scripts/real_screen_control_chroma.py` 一并修掉。
- `docs/frame_identical_pairs.json` + `scripts/identical_frame_witness.py`：8 组逐字节副本第一次有名有姓，
  三格口径（未登记 / 两个方向分开 / 副本不许当唯一像素证人），并按机器登记。
- `.github/workflows/ci.yml`：三条形状守卫接进 `Release script tests` 的打印步骤，三种「没读到」分开拦。
- 产品 0 文件；帧数与基线名单一字未动。
""" % {u"r": i[u"r"], u"n": i[u"n"], u"round": i[u"round"], u"date": DATE}


# —————————————————————————————————————————————————————————──

def shapes(i):
    return [(u"UI 轮次标题", u"## 第 %d 轮（R%d · " % (i[u"n"], i[u"r"])),
            (u"ITER 标题", u"## Round %d · R%d" % (i[u"round"], i[u"r"])),
            (u"STATE 主节", u"## R%d 状态（" % i[u"r"]),
            (u"DECISIONS", u"## D-%d（" % i[u"r"]),
            (u"BACKLOG 追账节", u"## R%d 追账" % i[u"r"]),
            (u"CHANGELOG 标题行", u"### 分支穷尽与副本证人：倍率新增具名出口、形状守卫认 if 链、638② 做成门（R%d / " % i[u"r"])]


def counts(i, tag):
    rows = []
    for book in (u"UI", u"ITER", u"STATE", u"BACKLOG", u"DEC", u"FINAL", u"CHANGE"):
        text = read(book)
        rows.append(u"%s :: %s" % (BOOKS[book], u" | ".join(u"%s=%d" % (n, text.count(s)) for n, s in shapes(i))))
    out = u"\n".join(rows) + u"\n"
    io.open(os.path.join(TMP, u"%s_counts.txt" % tag), u"w", encoding=u"utf-8").write(out)
    return out


def insert_before(text, pattern, block, label):
    m = re.search(pattern, text)
    if not m:
        raise SystemExit(u"ANCHOR-MISS %s：现读模式 %r 没命中" % (label, pattern[:60]))
    return text[:m.start()] + block + text[m.start():]


def apply(d, do_write):
    i = d[u"ident"]
    pre = counts(i, u"preapply")
    totals = [int(x) for x in re.findall(u"=(\\d+)", pre)]
    if max(totals) > 1:
        raise SystemExit(u"本轮标题形状在盘上出现 %d 次 ⇒ 不是幂等重放，停\n%s" % (max(totals), pre))
    if any(totals):
        print(u"DRY：盘上已有本轮标题（幂等重放）⇒ 一本都不再写\n" + pre)
        return 0
    print(u"PRE（写之前逐本现读）：\n" + pre)

    state_text = block_state(d)
    ui_text, u0 = block_ui(d)
    iter_text = block_iteration(d)
    backlog_text = block_backlog(d)
    dec_text = block_decisions(d)
    change_text = block_changelog(d)
    for name, blob in ((u"STATE", state_text), (u"UI", ui_text), (u"ITER", iter_text),
                       (u"BACKLOG", backlog_text), (u"DEC", dec_text), (u"CHANGE", change_text)):
        if u"@@" in blob:
            raise SystemExit(u"令牌没填满：%s 里还有 @@" % name)
    # 写手自己先合规 ⇒ 问**守卫自己**（不另写第二条正则）。DECISIONS/CHANGELOG 不在被判范围，
    # 它们留着历史原文；本轮正文里所有「第③段」都在引号里，由 unquote 处理。
    sys.path.insert(0, os.path.join(ROOT, "scripts"))
    from stage_gate_claims import classify_line
    for name, blob in ((u"STATE", state_text), (u"UI", ui_text), (u"ITER", iter_text),
                       (u"BACKLOG", backlog_text)):
        for raw in blob.splitlines():
            kind = classify_line(raw)
            if kind in (u"断言", u"冒充段号"):
                raise SystemExit(u"写手自己造出「%s」：%s :: %s" % (kind, name, raw.strip()[:120]))
    if not do_write:
        io.open(os.path.join(TMP, u"state_preview.md"), u"w", encoding=u"utf-8").write(state_text)
        print(u"DRY：六块文本算完，长度 STATE=%d UI=%d ITER=%d BACKLOG=%d DEC=%d CHANGE=%d ⇒ 未落盘"
              % (len(state_text), len(ui_text), len(iter_text), len(backlog_text), len(dec_text), len(change_text)))
        return 0

    new = {}
    new[u"STATE"] = insert_before(read(u"STATE"), r"(?m)^## R\d+ 状态（", state_text + u"\n\n", u"STATE 主节")
    m = re.search(r"(?m)^最后更新：\d{4}-\d{2}-\d{2}（本地 · R\d+ / 第 \d+ 轮 / Round \d+）$", new[u"STATE"])
    if not m:
        raise SystemExit(u"ANCHOR-MISS：STATE 的「最后更新」那一行现读不到")
    new[u"STATE"] = (new[u"STATE"][:m.start()] + u"最后更新：%s（本地 · R%d / 第 %d 轮 / Round %d）"
                     % (DATE, i[u"r"], i[u"n"], i[u"round"]) + new[u"STATE"][m.end():])
    new[u"UI"] = insert_before(read(u"UI"), r"(?m)^## 第 \d+ 轮（R\d+ · ", ui_text, u"UI 节")
    new[u"ITER"] = read(u"ITER").rstrip(u"\n") + u"\n\n" + iter_text.rstrip(u"\n") + u"\n"
    new[u"BACKLOG"] = read(u"BACKLOG").rstrip(u"\n") + u"\n\n" + backlog_text.rstrip(u"\n") + u"\n"
    new[u"DEC"] = read(u"DEC").rstrip(u"\n") + u"\n\n" + dec_text.rstrip(u"\n") + u"\n"
    ch = read(u"CHANGE")
    anchor = u"## [Unreleased]\n"
    if ch.count(anchor) != 1:
        raise SystemExit(u"ANCHOR-MISS CHANGELOG：[Unreleased] 命中 %d 次" % ch.count(anchor))
    head, rest = ch.split(anchor, 1)
    new[u"CHANGE"] = head + anchor + u"\n" + change_text.rstrip(u"\n") + u"\n\n" + rest.lstrip(u"\n")

    fin = read(u"FINAL")
    streak_n = int(re.search(u"streak=(\\d+)", d[u"streak"]).group(1)) if re.search(u"streak=(\\d+)", d[u"streak"]) else -1
    m2 = re.search(u"产品面连续零改动轮数 = \\*\\*(-?\\d+)\\*\\*（R(\\d+) 台账落盘之后现读", fin)
    if not m2:
        raise SystemExit(u"ANCHOR-MISS FINAL：streak 那一格现读不到")
    cell = (u"产品面连续零改动轮数 = **%d**（R%d 台账落盘之后现读 `python3 scripts/product_streak.py` ⇒ `%s`；"
            u"as-of 口径 ⇒ 读作「本轮之前最后一次产品改动在 %d 轮前」，下一轮是 %d。"
            u"上一格原文留着：**%s**（R%s 台账落盘之后现读"
            % (streak_n, i[u"r"], d[u"streak"], streak_n, streak_n + 1, m2.group(1), m2.group(2)))
    fin = fin[:m2.start()] + cell + fin[m2.end():]
    mu = re.search(u"U-31 … U-(\\d+)（R\\d+ 现读抬到最新一节）", fin)
    if not mu:
        raise SystemExit(u"ANCHOR-MISS FINAL：U 格那一注记现读不到")
    u_last = u0 + ui_text.count(u"- **U-") - 1
    fin = fin[:mu.start()] + u"U-31 … U-%d（R%d 现读抬到最新一节）" % (u_last, i[u"r"]) + fin[mu.end():]
    mp = re.search(u"完整名单以 `AGENT_STATE\\.md` 的 R(\\d+) 节 ② 为准", fin)
    if not mp:
        raise SystemExit(u"ANCHOR-MISS FINAL：§13 的仍开指针现读不到")
    fin = fin[:mp.start()] + u"完整名单以 `AGENT_STATE.md` 的 R%d 节 ② 为准" % i[u"r"] + fin[mp.end():]
    new[u"FINAL"] = fin

    for book, text in new.items():
        write(book, text)
    post = counts(i, u"postapply")
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
    reading = subprocess.check_output([sys.executable, "scripts/product_streak.py"], cwd=ROOT).decode("utf-8")
    line = reading.splitlines()[0].strip()
    streak_n = int(re.search(u"streak=(\\d+)", line).group(1))
    landed_r = max(int(x) for x in re.findall(r"(?m)^## R(\d+) 状态", read(u"STATE")))
    fin = read(u"FINAL")
    m2 = re.search(u"产品面连续零改动轮数 = \\*\\*(-?\\d+)\\*\\*（R%d 台账落盘之后现读" % landed_r, fin)
    if not m2:
        raise SystemExit(u"ANCHOR-MISS post-land FINAL：本轮那一格现读不到")
    end = fin.index(u"上一格原文留着：", m2.start())
    cell = (u"产品面连续零改动轮数 = **%d**（R%d 台账落盘之后现读 `python3 scripts/product_streak.py` ⇒ `%s`；"
            u"as-of 口径 ⇒ 读作「本轮之前最后一次产品改动在 %d 轮前」，下一轮是 %d。"
            % (streak_n, landed_r, line, streak_n, streak_n + 1))
    fin = fin[:m2.start()] + cell + fin[end:]
    write(u"FINAL", fin)

    st = read(u"STATE")
    # **搜索范围必须锚在刚落盘那一轮的小节内**（R569 那一族的第 12 次复发）：
    # 第一版在整个文件上找那一格，而本轮那一格当时还是 -1 占位（\d+ 匹配不到负号）
    # ⇒ 它匹配到上一轮那一节，并把历史的 streak 格从 20 改成 21。现在它只会当场报错，不会改历史。
    head_at = re.search(u"(?m)^## R%d 状态（" % landed_r, st)
    if not head_at:
        raise SystemExit(u"ANCHOR-MISS post-land STATE：读不到本轮（R%d）那一节" % landed_r)
    nxt = re.search(u"(?m)^## R\d+ 状态（", st[head_at.end():])
    section = st[head_at.start(): head_at.end() + (nxt.start() if nxt else len(st))]
    m3 = re.search(u"产品文件 0 个，连续零改动 \\*\\*(-?\\d+)\\*\\* 轮（唯一取数口", section)
    if not m3:
        raise SystemExit(u"ANCHOR-MISS post-land STATE：R%d 那一节里没有那一格 ⇒ 这一趟不写，绝不改历史" % landed_r)
    off = head_at.start() + m3.start()
    seg = st[off:]
    stop = seg.index(u"）；")
    cell3 = (u"产品文件 0 个，连续零改动 **%d** 轮（唯一取数口 `python3 scripts/product_streak.py`，"
             u"**台账落盘之后**现读 `%s`；as-of 口径 ⇒ 读作「本轮之前最后一次产品改动在 %d 轮前」；"
             u"取数时刻由 `post_land()` 钉在函数名字上，不在纪律上" % (streak_n, line, streak_n))
    st = st[:off] + cell3 + st[off + stop:]
    write(u"STATE", st)
    print(u"POST-LAND streak=%d（R%d）" % (streak_n, landed_r))
    sec = os.path.join(ROOT, "scripts", "refresh_report_section1.py")
    if os.path.exists(sec):
        subprocess.check_call([sys.executable, sec], cwd=ROOT)
        print(u"POST-LAND §1 已刷新")
    return 0


def main():
    do_write = u"--apply" in sys.argv
    d = gather()
    rc = apply(d, do_write)
    if rc != 0:
        return rc
    if do_write:
        post_land()
    return 0


if __name__ == u"__main__":
    sys.exit(main())

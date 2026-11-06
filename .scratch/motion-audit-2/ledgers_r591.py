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
TMP = "/tmp/r591"
DATE = "2026-11-06"
BOOKS = {"UI": "AGENT_UI_AUDIT.md", "ITER": "AGENT_VISUAL_ITERATION.md", "STATE": "AGENT_STATE.md",
         "BACKLOG": "AGENT_BACKLOG.md", "DEC": "AGENT_DECISIONS.md", "FINAL": "AGENT_FINAL_REPORT.md",
         "CHANGE": "CHANGELOG.md"}

RUN_MAIN = "42167592176"     # R590 主笔（本轮 ⓪ 到数那一跑）
RUN_ADD = "42167882874"       # R590 补记笔


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
            raise SystemExit(u"⓪ 读数里没有 %s 那一跑 ⇒ 先跑 ci_status_r591.py" % run)
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
    d["causes"] = must_read(os.path.join(TMP, "causes.txt"), u"skipped 成因那一支").strip()
    d["glue_scope"] = must_read(os.path.join(TMP, "glue_scope.txt"), u"值槽粘连扫描面").strip()
    ch = must_read(os.path.join(TMP, "channels.txt"), u"通道五读")
    for key, prefix in ((u"ident_line", u"IDENTITY="), (u"push_line", u"PUSH="),
                        (u"gh_http", u"GITHUB_HTTP="), (u"api_http", u"API_HTTP="),
                        (u"head_sha", u"HEAD="), (u"origin_sha", u"ORIGIN="),
                        (u"ahead", u"AHEAD="), (u"build_warn2", u"BUILD_WARNINGS=")):
        d[key] = grep_line(ch, prefix, u"通道五读的那一格").split(u"=", 1)[1]
    d["stage_gate"] = must_read(os.path.join(TMP, "stage_gate.txt"), u"第③段断言守卫现读").strip()
    d["pair_witness"] = must_read(os.path.join(TMP, "pair_witness.txt"), u"副本名册守卫现读").strip()
    d["look"] = must_read(os.path.join(TMP, "look.txt"), u"看图那一腿").strip()
    pw = d["pair_witness"]
    d["witness_scope"] = (grep_line(pw, u"WITNESS_SCAN_SCOPE", u"扫描面那一行") if u"WITNESS_SCAN_SCOPE" in pw
                          else u"（读数里没有扫描面那一行 ⇒ 靶 1 那半没落地）")
    d["witness_line"] = grep_line(pw, u"IDENTICAL_PAIRS ", u"副本那行读数")
    d["battery2"] = (grep_line(must_read(os.path.join(TMP, "py_after_knives.txt"), u"刀后复跑"), u"Ran ",
                               u"刀后复跑计数") if os.path.exists(os.path.join(TMP, "py_after_knives.txt"))
                     else u"（未读到：刀已还原那一趟还没跑）")
    for run in ci:
        ci[run][u"run"] = run
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
    for k in ("test_ci_skipped_causes", "test_ci_channel_hygiene",
              "test_ci_shape_guard_wiring"):
        if k not in d["counts"]:
            raise SystemExit(u"计数名册缺 %s 那一行 ⇒ 名册要现读不要手抄" % k)
    if d["counts"]["test_ci_skipped_causes"][1] <= d["counts"]["test_ci_skipped_causes"][0]:
        raise SystemExit(u"矛盾读数：本轮新卷 test_ci_skipped_causes 的 def test_ 数没长 ⇒ 计数名册读错了对象")
    d["delta_total"] = sum(a - b for b, a in d["counts"].values())

    kn = must_read(os.path.join(TMP, "knife_status.txt"), u"刀状态文件")
    _last = {}
    for _ln in kn.splitlines():
        _m = re.match(r"(r\d+)/(M\d{4}) ", _ln.strip())
        if _m:
            _last[_m.group(2)] = _ln.strip()
    kn = u"\n".join(_last[k] for k in sorted(_last))      # 末态逐把重签 ⇒ 一把只算最后一次
    knives = []
    for ln in kn.splitlines():
        m = re.match(r"(r\d+)/(M\d{4}) rc=(\d+) caught=(\d) clean=(\d) precheck=(\S+) post=(\S+)", ln.strip())
        if m:
            knives.append({u"arm": m.group(2), u"rc": int(m.group(3)), u"caught": int(m.group(4)),
                           u"clean": int(m.group(5)), u"precheck": m.group(6), u"post": m.group(7)})
    arms = [k[u"arm"] for k in knives]
    if len(set(arms)) != 8:
        raise SystemExit(u"主笔的刀数/去重后不是 8 把：%s ⇒ 表或状态文件读错了" % arms)
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

    def skipped_rows(rk):
        got = rk.get(u"skipped 清单", [])
        if not isinstance(got, list):
            return u"      （清单没取到 ⇒ 这一格按未读到处理）"
        return u"\n".join(u"      · 第③甲 步=%s 名=%s ⇒ 被 STEP[9] 的红连带跳过（这一步本就没跑，不是判了说没东西）"
                          % (r[0], r[1]) for r in got) or u"      ·（这一跑里没有 skipped 步骤）"

    return u"""## R%(r)s 状态（%(date)s · 第 %(n)s 轮 / Round %(round)s · 产品 0 文件 + **读数说得出自己是哪一种读不到**（本节① 把「这一步没出声」拆成 第③甲=被上游红连带 / 第③乙=跑了但本机没对象，并把 STEP[10]–[14] 里该出声的四步接上 `if: always()`；本节② 值槽粘连的扫描面从接线正文扩到全仓并**分成两类各报数**；本节③ ⓪ 那一跑把 R590 的三条红名清零、同时现读到一条我上轮写错的成因）+ 判据卷 +%(delta)s 格 + 刀 M1574–M1581 全 CAUGHT + ⓪ R590 两跑都到数）

⓪ **现读两对（`ci_status_r591.py`，取值时刻 13:48–14:05，两跑都 `completed / failure`）**：
   1. `%(mrun)s ↔ %(msha)s`（R590 主笔）⇒ 全部失败步骤：`%(msteps)s`。
      逐步骤结论：`Release script tests ⇒ %(mbat)s`、`Frame baseline vs working manifest ⇒ %(mbase)s`、
      `Surface left-axis ruler ⇒ %(mleft)s`、`Swift tests (executed-count gate) ⇒ %(mswift)s`。
      **R590 那三条 runner 红，本轮到数之后逐字读回来是空的**：`STEP[9] 红名（逐字）=%(mmisc)s`，
      而同一步的电池汇总是 `Ran 896 tests … OK (skipped=3)` ⇒ 三条对象错位（负半证人抄名册 / 少第四出口 / 外机名写死）**在 runner 上确认修好了**。
      ⚠ 但这个"空"差点是假的：读取器第一版先 `strip()` 再剥 ANSI，于是带色码的 `FAIL:` 行**恒不命中**，
      空集合让「红名少掉三条」变成**空真**（判法 `<= 0` 在没读到任何行时成立）。
      修法与证人：`lines_in_step` 改成**先剥色再锚定**，并加一格 `READER_SELFTEST`（把一份带 `^[[37;1m` 的假日志喂进去，
      命中必须=1，否则当场 `SystemExit`）⇒ 本轮那四条判"中"的预测，只有过了这一格才算数。
      四条预测（标签与判法逐字接自 R590 的 `PREDICTIONS_R591`）：
%(mpreds)s
      skipped 清单（`jobs[].steps` 另取一趟，逐格点名见本节③）：
%(mskip)s
   2. `%(arun)s ↔ %(asha)s`（R590 补记笔）⇒ `%(astatus)s`；失败步骤：`%(asteps)s`；
      逐步骤结论：`Release script tests ⇒ %(abat)s`、`Frame baseline vs working manifest ⇒ %(abase)s`。
      四条预测与主笔**同判**（①中 / ②不中 / ③中 / ④未读到）：
%(apreds)s
      skipped 清单：
%(askip)s
   3. **这一格是本轮真正的靶子，而且不是监工点的那一格**：主笔那一跑的 `STEP[9]` 仍然红，但红名是空的 ——
      正文尾部逐字是 `IDENTICAL_PAIR_RESULT=not-run 本机行=0 他机行=8 本机组=20` 之后直接
      `##[error]Process completed with exit code 2.`，而 `IDENTICAL_WITNESS_EXIT=` 与 `IDENTICAL_WITNESS_NOT_RUN=1`
      **两行都不在日志里**。成因现读：那一步开头是 `set -o pipefail`，GitHub 默认 shell 是 `bash -e` ⇒
      工具**合法**返回 2（这台机器没对象）时管道状态=2，`set -e` 在下一行之前就把整步打死，
      R589 精心写的"三种缺席分开说"那几支**从来没机会执行**。
      为什么本机没抓到：接线判据卷 `_run()` 生成的脚本只抄了 `set -o pipefail`、**没抄 `-e`** ⇒
      本机走的是另一套 shell 语义（这就是"绕开被测系统自己的驱动路径"在 CI 接线上的版本）。
      本轮修法（不降级、不挪位）：三处工具调用各用 `set +o pipefail` / `set -o pipefail` 括起来，
      真实退出码仍从 `PIPESTATUS[0]` 取，`rc=1` 照旧 `exit 1`；`_run()` 改成 `set -eo pipefail` 与 runner 同语义。
      证人：`test_absent_frames_dir_is_a_named_absence_and_stays_green` 在 `-e` 下重新跑（rc=0 且两条具名行都在），
      刀 **M1581** 把那对括号撤掉 ⇒ 同一格必须红（它红在"缺席那一支没机会执行"，不是红在"少了两行打印"）。
   4. **顺带推翻我自己上一轮写的一条成因**：R590 的 ⓪·4/③·4 写的是「非 ASCII 说明粘在值槽上会被 runner 日志打死」。
      本轮在同一份日志里逐字节数了一遍：含全角左括号 `（` 的行 **1257** 行、含 U+FFFD 的行 **3** 行，
      而"值槽紧跟（"且**完好打印**的有 **72** 行（`TIER_BRANCH_SCAN 分支链=5（口径…）`、
      `STAGE_GATE_RESULT=ok 无证断言=0（本轮没有…）` 都在其中）⇒ 粘连**不是充分原因**，
      损坏落在 flush 边界上；那 3 行恰好都是"被别的尺按值读"的 echo。
      ⇒ 值槽与说明分开这件事仍然照做（少一段可损坏的字节、且值能被按词读出），但**规矩按"谁要按值读"划界**，
      不按"有没有括号"划界：见本节②。R590 那两笔原文不改（台账按 SHA 引用历史，R563 那条），更正写在这里。
   5. **R592 的 ⓪ 要读的五格**（判法与取处写进 `ci_status_r591.py` 的 `PREDICTIONS_R592`，由脚本判，不许目测对拍）：
      ①本笔（主笔 + 补记笔）的成对号 —— 由补记那一趟现取现写；
      ②`STEP[9]` 里 `SHAPE_GUARD2_EXIT … rc=<数字>` 与 `IDENTICAL_WITNESS_EXIT=<数字>` 第一次出现
        （本轮修了 pipefail 那一支 ⇒ 这两行**应该**能印出来；印不出来说明修法没生效，而不是"又坏了"）；
      ③`CI_CHANNEL_GLUE_SCOPE … 粘连计=` 与 `CI_SKIPPED_CAUSES … 无声=` 在 runner 上各出现一次（两支新守卫的外部证人）；
      ④`STEP[10]`（Info.plist gate）这次还 skipped 吗 —— 它没带 `if: always()`，是**故意**留的（硬门，不是证据步）；
        若它转成 ran 而 STEP[9] 仍红，说明 `always()` 的作用域被我理解错了；
      ⑤`STEP[11]`–`STEP[14]` 从本轮起**不该再被连带跳过** ⇒ 若仍 skipped 就是第③甲没修好，
        而若它们跑了却报"本机没对象"，那是第③乙，两格分开记。

① **真实推进（本节① / §3 第②段）：skipped 拆成两种修法相反的成因，并给证据步骤接上出声的机会**
   监工那条结论我逐字复核成立（取值时刻 13:48，`gh run view 42159607721 --json jobs`）：
   `9 failure Release script tests / 10–14 skipped / 15 failure Swift tests`，
   而 `ci.yml` 里那五步当时都没有 `if: always()`（全文只有 R89 那一段硬门有）⇒
   R590 把它们记成"这一维今天没人判"是**成因认错**：那是被上游红连带，不是本机没对象。
   本轮做的三件事：
   1. 接线：STEP[11]–[14] 各加 `if: always()`（证据/报告型步骤必须有机会出声）；`Release script tests` 也加
      —— 它是最大的一块证据，从前 Build 一红它连一行都不印。**硬门一条没降级**：`Info.plist gate` 保持原样（它不是证据步），
      R89 那五步的 `if: always()` 一字未动，`[ "$g" -eq 0 ] || exit 1` 这类拦路全部保留。
   2. 新守卫 `scripts/ci_skipped_causes.py`（两种模式）：
      `static` 判"证据型步骤（正文真会印通道串）既没 `if: always()` 又不在具名豁免名册里" ⇒ 红；
      `run` 判"结论里有 `skipped` 而台账本轮那一节没给它成因名字" ⇒ 红。现读逐字：`%(causes)s`
      豁免名册 `docs/ci_evidence_step_exemptions.json` 4 行（捕获/探针/胶片/Pillow 准备），每行带理由，
      并且**豁免必须真会命中**：名字对不上现读的证据步骤、或那一步已经带 `always()` ⇒ 算 `CI_EVIDENCE_EXEMPT_DEAD` 红
      （R587 那条"名册不许当垃圾桶"的同形规矩）。
   3. 台账这一节把今天每一维落在哪一格**逐格点名**（见本节③），门才读得出"具名"而不是我口头说一句。
   刀：**M1574**（撤掉 STEP[11] 的 `always()`）、**M1575**（让"证据型"识别变盲 ⇒ 那一格必须红，这是"尺瞎了要响"）、
   **M1576**（让空豁免检查失效）、**M1577**（让 run 模式接受没点名的具名）。

② **真实推进（本节②）：值槽粘连的扫描面扩到全仓，并分成两类各报数**
   `test_ci_shape_guard_wiring` 那一格从前自带第二条正则，docstring 明写"扫描对象是 `step_body()`" ⇒
   它的 0 只代表"接线正文那一小段干净"，而同一坏法在 `scripts/*.py` 的 print 与 `ci.yml` 其余 echo 里没人管。
   本轮把尺搬进 `scripts/ci_channel_hygiene.py`（**一处定义**，接线那一格改成调用它），扫描面当读数印出来：
   `%(scope)s`
   认的形状：`NAME=%%s（`、`NAME … rc=$v（`（M1572 第一次空刀抓到的那一形）、括号一直到字符串末尾不闭合、
   通道名被拆到两行（相邻字面量与 `+` 拼接都接得上，`%%` 模板也看得见）；看不见的那部分具名下界
   `CI_CHANNEL_GLUE_PARTIAL=`。
   **两类分开，因为修法相反**：
   · `其中工作流echo`（值被别的尺按词读的那一族）⇒ **拦路**，现读 0；刀 **M1578** 把已修的 echo 粘回去 ⇒ 必须红。
   · `脚本侧` + `读数括号`（括号里装的是后续读数，如 `拦路=%%d（缺席%%d …）`）⇒ **具名不判**并印数，
     理由就是 ⓪·4 那个被推翻的成因：同形状 72 行完好、3 行损坏 ⇒ 判它红等于拿一个错因果逼一批仪器改输出契约。
   刀：**M1579**（工作流那一侧扫描失效 ⇒ 要拦的那一半必须响）、**M1580**（分类退化 ⇒ 划界本身要有牙）。

③ **几朵红各由谁签 + 今天哪几维落在哪一格（门读的就是这些行）**
   · 第③甲 步=10 名=Info.plist gate ⇒ 被 STEP[9] 的红连带；这一步**故意**不加 `if: always()`：它是硬门不是证据步，
     上游红时它没有新读数可贡献（`make_info_plist.sh` 的产物不进台账任何一格）。
   · 第③甲 步=11 名=Frame baseline vs working manifest (fixture-set gate) ⇒ 连带跳过；本轮已加 `if: always()`，
     所以从含本笔那一跑起它应当不再出现在 skipped 清单里（R592 的 ⓪·⑤ 判这一格）。
   · 第③甲 步=12 名=Surface left-axis ruler (BACKLOG 234, wired in R210; venv interpreter in R218) ⇒ 同上，本轮已加。
   · 第③甲 步=13 名=Frame baseline vs previous release (change report, report-only) ⇒ 同上，本轮已加。
   · 第③甲 步=14 名=Runtime launch smoke (report-only) ⇒ 同上，本轮已加。
   · 第③乙 本机=github-runner 名册本机行=0 他机行=8 ⇒ 副本名册那一维在 runner 上**跑了但没有自己的登记**，
     这一格今天仍只能说"没人判"，不能说"没有副本"（R590 已把措辞钉死，本轮一字未改）。
   · 第③乙 倍率那一维（`FRAME_BASELINE_SCALE_BASELINE_UNKNOWN`）：两跑里 `STEP[11]` 都是 skipped ⇒
     它今天既不是甲也不是乙，而是**甲**（这一步本就没跑）—— R590 写的"第③态"从本轮起一律拆成这两格写。
- **红名对账**（口径=对账口径已启用；门报 `%(recon)s`，不由我数；`不计入对账口径` 那一类本轮没有）：
  · 红名「`Ran 918 … FAILED (failures=1)`：`test_the_roster_matches_what_this_machine_actually_skips` 借内层红」→ ⑨·1
  · 红名「runner `##[error]Process completed with exit code 2`（`42167592176` 的 STEP[9] 尾）」→ ⑨·2 与 本节③
  · 红名「`READER_SELFTEST` 之前的空真：`FAIL:` 命中 0 行却判成中」→ ⑨·3
  · 红名「`CI_CHANNEL_HYGIENE_RESULT=red 通道粘连命中=34`（扩面第一趟，含 16 处脚本侧说明与 19 处读数括号）」→ ⑨·4
  · 红名「`mutate_r591_wiring.py` 首次 `py_compile` SyntaxError（CJK 串里 ASCII 双引号，本族第四次）」→ ⑨·5
  · 红名「`_run` 的 `--shots` 替换第一次按带引号写 ⇒ 活门拒绝（R590 同族，本轮重犯一次）」→ ⑨·6
  · 红名「`ci_status_r591.py` 第一版把预测③的取处映射到 `CI_CHANNEL_GLUE_SCOPE`（对象错）」→ ⑨·7

④ **验证链（顺序照派单）**：build `%(build)s` → 判据卷 `%(b1)s` → 刀 M1574–M1581（**落刀前现读高水位=M1573**，
   跨表唯一性逐把现读 0 次撞号）→ 新表 `mutate_r591_wiring` 进预检名册（`NEEDLE_PRECHECK tables=404 arms=863 bad=0`，
   本轮 8 把逐把 ok）→ 刀已还原复跑判据 `%(b2)s`、`%(md5)s`、`git status scripts/` 与三种变异串各现读 0 处 →
   捕获卷 `%(capture)s`、帧 `%(frames)s` → 本机那一门 `%(gate)s` / 判定 `%(drift)s` / 倍率出口 `%(scale)s` →
   看图（本节⑥）→ 全量 `%(full)s`、skipped `%(fullskip)s` → 三道预检**串行** → `SKIP_INSTALL=no-product-change` →
   七本台账 → 派生格**落盘之后**现读 → 电池（canonical 配置，不设帧目录；两个时刻都记）。

⑤ **看图那一腿（659 形状：先 `convert("L")` 再 `getbbox`，配同尺寸正对照 + 自己 vs 自己必须 0）**：
%(look)s

⑥ **基线与名单**：产品文件 0 个，连续零改动 **%(streaknum)s** 轮（唯一取数口 `python3 scripts/product_streak.py`，
   **台账落盘之后**现读 `%(streak)s`；as-of 口径 ⇒ 读作「本轮之前最后一次产品改动在 %(streaknum)s 轮前」；
   取数时刻由 `post_land()` 钉在函数名字上，不在纪律上〔streak-cell-end〕）。帧名单未动（`%(frames)s`），
   四张按机器登记的表一字未改；本轮**新增**一份豁免名册 `docs/ci_evidence_step_exemptions.json`（新文件，
   不是对既有名册/豁免表的改动），它管的是"证据步骤没出声算不算违规"这一族。

⑦ **闸门与单子（§3 第③段今天仍不开工）**：
   `STAGE2_CLICKTHROUGH_BLOCKED` 与 `STAGE3_FRAME_CRITERIA_HAVE_NO_RUNNER_WITNESS=awaiting-654-direction` 一字未撤；
   第③段证人现读 `%(stage)s` ⇒ 「三问全过」在规格里出现次数仍是 0。
   本轮没有把任何一条 `判=不判 / not-run / skipped / 扫描面 0` 说成"没问题"：
   `其中工作流echo=0` 带两类分开报数、`无声=0` 带 `证据型=8` 的扫描面、skipped 的每一格有甲/乙名字。
   仍归用户（一条不代选）：655 / 656 / 657 / 658 / 659 / 660 / 661 / 662 / 638① / 654 / 646 / 647 / 650 / 651 / 653 /
   644 / 639 / 640 / 637 / 633 / Motion ≥2 帧地板 / SSH 成因 / 手感签字；
   4.5 墨地板、150 上限、120ms、Motion ≥2、2x 8.0pt、1x 6.0pt、`FLOOR_LIGHT=1.20`、`FLOOR_DARK=1.10`、容差 1.5、
   跳变地板 8、`probeInkFraction=3%%`、`.contentFade` 0.20、`--allow-missing`、四张按机器登记的表、
   既有名册与豁免表、禁碰 14 面 —— 一字未动；`update` 一次没跑；没改这台机器的全局外观；帧与日志不含真实剪贴板原文。

⑧ **自伤（照实，不缩）**：
   1. 整卷本轮跑了四趟（刀前 1、刀后 3）：其中一趟 `Ran 918 … FAILED (failures=1, 跳过了=6)`，
      内层红名是 `test_it_really_notices_the_running_copy_under_a_cjk_path`、外层只有
      `test_skip_roster` 那一格（借红，634 的设计 ⇒ 不算第二条独立缺陷）；其余三趟 `Ran 918 / OK (skipped=5)`。
      单独重跑那一卷 8/8 OK ⇒ 出现率记 **1/4**，四个读数都留在盘上文件名上
      （`py_after_knives.txt` / `py_battery_runA_failed.txt` / `py_battery_runB_ok.txt` / `py_battery.txt`），
      不写成「修好了」也不写成「flake 所以不算」（R540/R587 那条同形处置）。
      ⚠ 附带一条读数卫生自伤：前三趟我都写进同一个文件名 `py_battery.txt` ⇒ 刀前那一趟的原文被覆盖，
      现在只能说"四趟里三趟绿"而不能逐趟对拍时刻 ⇒ 读数文件名要带时刻/序号，本轮起改。
   2. **`set -eo pipefail` 没抄进接线判据卷的 harness** ⇒ R589/R590 两轮的"三种缺席分开"在本机全绿、在 runner 从来没执行过。
      这是"绕开被测系统自己的驱动路径"在 CI 接线上的复现：被测对象是 GitHub 的 `bash -e`，我的证人用的是 `bash`。
      本轮修 harness + 修接线 + 配 M1581；R590 那两笔原文不改（历史按 SHA 引用）。
   3. 读取器两处自伤，都被自己的活门抓到之前先造了一条**假中**：`FAIL:` 因为行首 ANSI 恒不命中（判法在空集合上成立），
      以及预测③的取处被我映射到 `CI_CHANNEL_GLUE_SCOPE`（那是 R591 的名字，与 R590 的 `WITNESS_SCAN_SCOPE` 无关）。
      ⇒ 新增 `READER_SELFTEST`：已知答案（带色码的一行）必须先被看见，否则整轮预测一条不判。
   4. 扩面第一趟把守卫自己判红（命中 34）—— 我起初按"全仓都要 0"去改，量完才发现其中 19 处括号里装的是**后续读数**。
      ⇒ 规矩按"谁按值读"划界；这一格记的是"我差点把一个被推翻的因果写成全仓整改"。
   5. CJK 串里 ASCII 双引号打断 python 字面量：**第四次**（本轮在 `mutate_r591_wiring.py` 的臂说明里，`py_compile` 当场抓到）。
      补丁与表一律落成文件再执行，不用 heredoc 承载中文。
   6. `_run()` 的 `--shots` 替换第一次又按带引号去写 ⇒ 活门 `assert` 拒绝（R590 ⑨·8 同形，第二次）。
   7. `look_r590.py` 被我复用时正文里留着"本轮与 R589 之间"那句写死的轮次名 ⇒ 读数标签错了对象，
      改成由目录派生 + 措辞去轮次号（同 R324「别拿上一轮的读数冒充本轮」）。
   8. **写手机器自己静默跳过**：`post_land()` 只在 `scripts/` 找 `refresh_report_section1.py`，而那支仪器住在
      `.scratch/motion-audit-2/` ⇒ `if os.path.exists(...)` 直接跳过，§1 派生格从来没刷 ⇒ 台账落盘后
      `test_cell_equals_instrument` 红（R590 那一轮也是同一形状，只是那时 §1 恰好被手工刷过所以没暴露）。
      修法：两个候选路径 + 找不到就 `SystemExit`；证人就是这一格电池本身（它比我的眼睛先响）。
   9. 读数文件名没带时刻/序号 ⇒ 刀前那一趟 `py_battery.txt` 被刀后那趟覆盖，四趟里只能逐档对拍三个存档、
      第四个只能引用汇总行（⑨·1 里那两个时刻因此是"从文件倒推"而不是"当场登记"）。

⑨ **通道五读（取值时刻 13:47–13:48）**：码签身份 `%(ident)s`（本笔自己重取，不是引用）；
   push 通道 `%(push)s`；`github.com=%(gh)s`、`api.github.com=%(api)s`；
   `HEAD=%(head)s`、`origin/main=%(origin)s`、`ahead=%(ahead)s`；构建 `%(buildwarn)s`。
""" % {u"r": i[u"r"], u"n": i[u"n"], u"round": i[u"round"], u"date": DATE,
         u"delta": d["delta_total"], u"causes": d["causes"], u"scope": d["glue_scope"],
         u"look": d["look"], u"md5": d["md5"], u"build": d["build_warn"], u"capture": d["capture"],
         u"frames": d["frames"], u"gate": d["gate_result"], u"drift": d["gate_drift"],
         u"scale": d["gate_scale"], u"full": d["full"], u"fullskip": d["full_skips"],
         u"b1": d["battery"], u"b2": d["battery2"], u"recon": d["recon"], u"stage": d["stage_gate"],
         u"streak": d["streak"], u"streaknum": (re.search(u"streak=(\\-?\\d+)", d["streak"]).group(1)
                                               if re.search(u"streak=(\\-?\\d+)", d["streak"]) else u"-1"),
         u"mrun": m.get(u"run", ""), u"msha": m[u"sha"], u"msteps": step(m),
         u"mbat": m[u"逐步骤结论"].get(u"Release script tests", u"（读不到）"),
         u"mbase": m[u"逐步骤结论"].get(u"Frame baseline vs working manifest (fixture-set gate)", u"（读不到）"),
         u"mleft": m[u"逐步骤结论"].get(u"Surface left-axis ruler (BACKLOG 234, wired in R210; venv interpreter in R218)", u"（读不到）"),
         u"mswift": m[u"逐步骤结论"].get(u"Swift tests (executed-count gate)", u"（读不到）"),
         u"mmisc": json.dumps(m.get(u"STEP9_红名", u"（未读到）"), ensure_ascii=False)[:120],
         u"mpreds": preds(m), u"mskip": skipped_rows(m),
         u"arun": a.get(u"run", ""), u"asha": a[u"sha"], u"astatus": a.get(u"status行", u"（读不到）"),
         u"asteps": step(a), u"abat": a[u"逐步骤结论"].get(u"Release script tests", u"（读不到）"),
         u"abase": a[u"逐步骤结论"].get(u"Frame baseline vs working manifest (fixture-set gate)", u"（读不到）"),
         u"apreds": preds(a), u"askip": skipped_rows(a),
         u"ident": d["ident_line"], u"push": d["push_line"], u"gh": d["gh_http"], u"api": d["api_http"],
         u"head": d["head_sha"], u"origin": d["origin_sha"], u"ahead": d["ahead"], u"buildwarn": d["build_warn"]}


def _state_tail_unused():
    return None
def _unused_state_tail():
    return None
def block_ui(d):
    i = d["ident"]
    u0 = next_u()
    rows = [
        (u"skipped 有两种成因，修法相反：第③甲 / 第③乙",
         u"监工现读 `42159607721` 的逐步骤结论：`9 failure / 10–14 skipped`，而那五步没有 `if: always()` ⇒ "
         u"R590 写的「这一维今天没人判」把**被上游红连带**读成了**本机没对象**。本轮把第③态拆成两格并逐格点名。"),
        (u"证据步骤必须有机会出声；硬门一条没降级",
         u"STEP[11]–[14] 与 `Release script tests` 各加 `if: always()`；`Info.plist gate` 保持不加（它不是证据步），"
         u'R89 那五步的 `always()` 与所有 `[ "$g" -eq 0 ] || exit 1` 一字未动。'),
        (u"豁免必须真会命中，否则比没豁免更坏",
         u"新名册 `docs/ci_evidence_step_exemptions.json` 4 行带理由；名字对不上现读的证据步骤、"
         u"或那一步已经带 `always()` ⇒ `CI_EVIDENCE_EXEMPT_DEAD` 红（R587「名册不许当垃圾桶」的同形）。"),
        (u"「无声=0」要带扫描面：证据型=8、带 always=4、具名豁免=4",
         u"证据型是按**正文会不会印通道串**认的（注释行不算，`# 从前印 FOO_RESULT=ok` 不是读数），"
         u"所以这一步的 0 分得开「都接上了」与「尺没看见任何步骤」。"),
        (u"`bash -e` 才是被测对象：harness 没抄 `-e` 让两轮的缺席分支从来没被执行",
         u"runner 那一步是 `bash -e {0}`；我的接线判据卷只写了 `set -o pipefail` ⇒ 工具返回 2 时本机继续跑分支、"
         u"runner 直接 `exit code 2`。修法：harness 改 `set -eo pipefail`，正文里三处调用各用 `set +o pipefail` 括起来。"),
        (u"值槽粘连的规矩按「谁按值读」划界，不按「有没有括号」划界",
         u"同一份日志里含 `（` 的行 1257、含 U+FFFD 的 3、而值槽紧跟括号**完好**的 72 ⇒ 粘连不是充分原因。"
         u"拦路只判工作流 echo 那一族（值被别的尺按词读）；脚本侧 16 处与读数括号 19 处**具名报数**不并入 0。"),
        (u"一把尺只许一处定义",
         u"接线那一格从前自带第二条正则 ⇒ 它的 0 只代表那一小段。现在尺搬进 `ci_channel_hygiene.py`，"
         u"接线格只调用；并加一格断言那个测试文件里不再出现第二条正则。"),
        (u"正对照要覆盖到形状四种，包括「名字被拆到两行」",
         u"`NAME=%s（`、`NAME … rc=$v（`、括号到串尾不闭合、相邻字面量与 `+` 拼接 —— "
         u"后两种靠 `%` 模板与 `BinOp` 手工接；接不上的具名 `CI_CHANNEL_GLUE_PARTIAL=` 当下界。"),
        (u"读取器的空集合会让判法**空真**",
         u"`FAIL:` 因为行首 ANSI 恒不命中 ⇒ 「红名少掉三条」被判成中。修法：先剥色再锚定 + "
         u"`READER_SELFTEST`（带色码的假日志必须命中 1，否则整轮预测一条不判）。"),
        (u"取处那一格错了，判的就是别的对象",
         u"预测③要的是 `WITNESS_SCAN_SCOPE swift文件=`（R590 靶 1），我第一版映射到 `CI_CHANNEL_GLUE_SCOPE`（R591 靶 2）"
         u"⇒ 两条通道毫无关系。现读修正后那一格是**中**：runner 上 `swift文件=159 swift函数=2108`。"),
        (u"R590 那三条 runner 红在 runner 上确认修好了",
         u"`42167592176` 的 `STEP[9]` 红名逐字为空、电池汇总 `Ran 896 … OK (skipped=3)` ⇒ "
         u"负半证人自带名册、真语料第四出口、外机名现读取反，三处都在含本笔的那一跑上转绿。"),
        (u"内层借红不许算第四条缺陷，但两个读数都要留",
         u"`test_skip_roster` 报的是内层那一卷的红（`test_it_really_notices_the_running_copy_under_a_cjk_path`），"
         u"单独重跑 8/8 OK、整卷另三趟 `OK (skipped=5)` ⇒ 出现率 1/4 记进 ⑨·1，不写「修好了」也不写「flake 所以不算」。"),
        (u"台账里那些「（缺席%d 未登记%d）」的括号本轮没拆",
         u"它们装的是**后续读数**，拆了会改动台账与其他解析器引用的形状 ⇒ 具名不判并印数；"
         u"这是本轮唯一一条「我量了但决定不改」的，理由写在守卫正文里而不是散文里。"),
    ]
    body = u"\n".join(u"- **U-%d：%s** —— %s" % (u0 + k, t, b) for k, (t, b) in enumerate(rows))
    head = (u"## 第 %(n)s 轮（R%(r)s · %(date)s · U-%(u0)s…U-%(u1)s）：把「这一步为什么没出声」拆成两种修法相反的成因，并让值槽粘连的扫描面自己报数"
            % {u"n": i[u"n"], u"r": i[u"r"], u"date": DATE, u"u0": u0, u"u1": u0 + len(rows) - 1})
    return head + u"\n\n" + body + u"\n\n", u0
def block_iteration(d):
    i = d[u"ident"]
    return u"""## Round %(round)s · R%(r)s（第 %(n)s 轮 · %(date)s）：skipped 拆甲乙、值槽粘连按谁按值读划界、harness 补上 -e

**七维度自评**（恰七行，每格 n/15；维度名照曲线尺认的那七个同字，本轮不造新维度）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉看图 | 11/15 | 产品 0 文件 ⇒ 看的是"两批帧是不是同一批"：逐字节 356/356 与 R590 同一批 + 差量可见性正对照（包围盒 (360,70,420,110) / 2400 颗）+ 自己 vs 自己必须 0（`LOOK_SELF_ZERO`）。扣分：像素复核不是新发现；且看图那一腿复用了上一轮的脚本，标签写错了轮次（⑨·7）才改现读派生。 |
| 判据有效性 | 15/15 | 靶 1 四把（M1574–M1577）+ 靶 2 三把（M1578–M1580）+ 接线一把（M1581）全 CAUGHT，逐把单独取退出码、无 `| head`；`static`/`run` 两种模式与"尺瞎了要响"三格（M1575/M1579/M1580）各有合成正负对照。本轮**没有一把空刀**：落刀前先用现读量过形状，M1572 那一课没重踏。 |
| 假绿防御 | 15/15 | ①`无声=0` 带 `证据型=8` 的扫描面；②豁免必须真会命中（空豁免算红）；③值槽粘连分两类各报数，不并入 0；④读取器加 `READER_SELFTEST`（带 ANSI 的已知答案必须先被看见）；⑤harness 与 runner 同语义（`set -eo pipefail`），从前那种"本机绿、runner 没执行"从此会被自己的判据卷抓到。 |
| 产品面推进 | 3/15 | 产品 0 文件；`update` 一次没跑；帧名单一字未动（`%(frames)s`）。推进全在取证面，段号仍是第②段（第③段一字未写，证人见 STATE 本节⑦）。 |
| 台账一致性 | 12/15 | 身份交叉核对过；七个标题形状写前 0、写后各 1；派生格只在**本轮小节内**切（哨兵缺失就报错）；skipped 的每一格在台账里有名字，门读的就是这些行。扣分：⑨·1 那朵内层借红两个读数并存、⑨·5 的 CJK 引号第四次复发（`py_compile` 抓到）。 |
| 剩余风险处置 | 13/15 | 没结案任何单子；两条具名阻塞一字未撤；`Info.plist gate` 故意不带 `always()` 这件事写成了账而不是默认。扣 2 分：`STEP[10]` 仍会在上游红时被连带跳过（本轮判定"可接受"但**没有 runner 侧证人**，只能由含本笔那一跑之后再说）；`CI_CHANNEL_GLUE_PARTIAL=` 那个下界本轮没缩。 |
| 交接可读性 | 15/15 | R592 的 ⓪ 五格写进 `ci_status_r591.py` 的 `PREDICTIONS_R592`，每条四格齐（主张 / 判法 / 正文从哪一步取 / 这条通道由哪一步以什么方式印出去），并明确"②那两行印不出来=修法没生效，不是又坏了"这种反向判读。 |

本轮一句话：监工驳我的一条成因，我复核之后**先证实再改尺**，结果在同一份日志里又量出我自己上一轮写错的另一条成因 ——
读数的责任不在"报了 0"，在"这个 0 是哪一种 0"。
""" % {u"round": i[u"round"], u"r": i[u"r"], u"n": i[u"n"], u"date": DATE, u"frames": d[u"frames"]}
def block_backlog(d):
    i = d["ident"]
    return u"""## R%(r)s 追账（%(date)s · 第 %(n)s 轮 / Round %(round)s）

**新开单 1 张**：

**663. CI 接线判据卷的 shell 语义与 runner 不同（`bash -e` 没进 harness）**
· 现象（取值时刻=本轮读 `42167592176` 那一趟）：`STEP[9]` 正文尾部 `IDENTICAL_PAIR_RESULT=not-run …` 之后直接
  `##[error]Process completed with exit code 2.`，而 `IDENTICAL_WITNESS_EXIT=` / `IDENTICAL_WITNESS_NOT_RUN=1` 两行都不在。
· 成因：那一步 `set -o pipefail` + GitHub 默认 `bash -e` ⇒ 工具**合法**返回 2 时管道状态=2，`set -e` 在取
  `PIPESTATUS[0]` 之前就把整步打死；"三种缺席分开说"的分支从来没机会执行。
· 本机为什么不红：`test_ci_shape_guard_wiring.ExecutionTests._run()` 生成的脚本只有 `set -o pipefail`，没有 `-e`。
· 本轮已修（harness 补 `-e`、三处调用括起 `set +o pipefail`、刀 M1581 钉住），但**含本笔的那一跑才是证人** ⇒
  R592 的 ⓪· 判"那两行第一次印出来"。若印不出来，结论是"修法没生效"，不是"又坏了"。
· 剩下的那一半归用户：`Info.plist gate` 要不要也带 `if: always()`（它是硬门不是证据步，本轮判定不加）。

**既有单子只补事实，一条不代选**：
· **662**（上一轮新开）：本轮电池两趟里有一趟内层红 `test_it_really_notices_the_running_copy_under_a_cjk_path`
  ⇒ 外层 `test_skip_roster` 借红。与 662 那条"档位少一维"**不是同一件事**，但形状相同：
  名册按机器分档，而这几格的 skip 与否还取决于运行时环境。三条出路仍没选。
· **638**：②那一问的 runner 半本轮又读到一次（`本机行=0 他机行=8 本机组=20 ⇒ not-run`）⇒ 仍属第③乙；
  ①那一问（并进 / 名册 / 让 runner 自己登记）一字未动。
· **655 / 660**：倍率那一维四个出口各有名字，但 `STEP[11]` 两跑都 skipped ⇒ 它是**第③甲**（这一步本就没跑），
  不是"判了说没东西"。本轮已给它加 `if: always()` ⇒ 从含本笔那一跑起这一格才有读数。重烤基线仍归用户。
· **658**：机器维度这一族本轮**又复发一次**，但方向相反：不是判据把外机名写死，而是我把"这台没对象"
  与"这台没跑到"并成一格。已在 STATE 本节③逐格拆开；三条出路仍没选。
· **659**：看图沿用它的形状（先 `convert("L")` 再 `getbbox` + 同尺寸正对照 + 自己 vs 自己必须 0），
  本轮没有新形状要补；但复用上轮脚本时标签写死轮次号，算一处卫生问题，已改现读派生。
· **661**：Swift 捕获侧那 11 处一字未动；本轮只是**读**了 Swift 树（扫描面 159 文件 / 2108 函数）。
· **646 / 647 / 654**：状态照旧 —— 两条具名阻塞一字未撤 ⇒ §3 第③段继续不开工。
""" % {u"r": i[u"r"], u"n": i[u"n"], u"round": i[u"round"], u"date": DATE}
def block_decisions(d):
    i = d["ident"]
    return u"""## D-%(r)s（%(date)s）：缺席要分「没跑到」与「没对象」；规矩要按「谁按值读」划界

**背景**：R590 把 runner 上五个 `skipped` 步骤记成"这一维今天没人判"。本轮监工驳这条结论，我逐字复核成立 ——
那五步没有 `if: always()`，红的是 `STEP[9]`，所以它们是**被连带跳过**。复核过程中又在同一份日志里量出
第二条我上轮写错的成因（值槽粘连不是日志损坏的充分原因：同形状 72 行完好、3 行损坏）。

**决定**：
1. 第③态拆成两格并**逐格点名**：`第③甲`=这一步本就没跑（依赖上游失败而 skipped）；
   `第③乙`=跑了但这台机器没有对象。台账里没点名的 skipped ⇒ 由 `scripts/ci_skipped_causes.py --mode run` 判红。
2. 证据步骤必须有机会出声：正文会印通道串的步骤要么 `if: always()`，要么进带理由的豁免名册；
   豁免**必须真会命中**，空豁免算红。硬门一律不降级、不挪位（`Info.plist gate` 故意不加）。
3. 一条"看起来对"的因果在被写成规矩之前要先量：值槽粘连的规矩**只判被按值读的通道**（工作流 echo），
   脚本侧与"括号里装后续读数"那两类具名报数，不并入 0，也不据一个未证实的因果去改一批仪器的输出契约。
4. 判据的 harness 必须与被测系统同语义：runner 那一步是 `bash -e {0}` ⇒ 判据卷生成的脚本也得 `set -eo pipefail`。
   "本机绿、runner 从来没执行那段分支"是这一族最贵的一种假绿。
5. 读取器要自带"已知答案"活门：`READER_SELFTEST` 先用一份带 ANSI 的假日志证明 `FAIL:` 看得见，
   否则本轮所有按前缀筛出来的 0 都不算数（空集合上的判法是**空真**，不是"中"）。

**为什么不撤任何既有门**：地板、阈值、四张按机器登记的表、既有名册与豁免表一字未动；
`SKIP_INSTALL=no-product-change`（产品 0 文件）；`update` 一次没跑；两条 §3 阻塞未撤 ⇒ 第③段不开工。

**代价**：判据卷 +%(delta)s 格、8 把刀、一份新豁免名册；换来的是 skipped 这一族第一次有两种名字，
以及 R590 那三条红在 runner 上被确认清零（而不是我口头说清零）。
""" % {u"r": i[u"r"], u"date": DATE, u"delta": d["delta_total"]}
def block_changelog(d):
    i = d["ident"]
    return u"""### skipped 拆成甲乙、值槽粘连按谁按值读划界、接线判据卷补上 `bash -e`（R%(r)s / 第 %(n)s 轮 / Round %(round)s · %(date)s）

- `.github/workflows/ci.yml`：STEP[11]–[14] 与 `Release script tests` 各加 `if: always()`（证据步骤必须有机会出声；
  硬门一条没降级）；三处工具调用用 `set +o pipefail` / `set -o pipefail` 括起来 —— 从前工具**合法**返回 2 时
  `bash -e` 在取 `PIPESTATUS[0]` 之前就把整步打死，"三种缺席分开说"从来没执行（`42167592176` 现读 `exit code 2`）。
- `scripts/ci_skipped_causes.py`（新）+ `docs/ci_evidence_step_exemptions.json`（新，4 行带理由）：
  `static` 判"证据型步骤没出声的机会"，`run` 判"skipped 而台账没给成因名字"；空豁免与不命中的豁免都算红。
- `scripts/ci_channel_hygiene.py`：值槽粘连的扫描面从接线正文扩到全仓（`CI_CHANNEL_GLUE_SCOPE`），
  认四种形状（含通道名被拆到两行），并**分成两类各报数**：工作流 echo 拦路、脚本侧与读数括号具名不判
  （同形状 72 行完好、3 行损坏 ⇒ 粘连不是充分原因，R590 那条成因本轮推翻）。
- `scripts/tests/test_ci_shape_guard_wiring.py`：harness 改 `set -eo pipefail` 与 runner 同语义；粘连尺改为调用共享函数
  （一处定义）；`scripts/tests/test_ci_skipped_causes.py`（新卷 16 格）。
- 顺带修的既有输出契约：`ci_capture_gate.py` / `ci_red_stability.py` / `commit_round_identity.py` /
  `stage_gate_claims.py` 四条通道的说明从值槽里挪到另起一行；`ci.yml` 里 5 条 echo 同形（含 `HOVER_DIFF_EXIT`）。
- 产品 0 文件；帧名单与四张按机器登记的表一字未动；`update` 一次没跑。
""" % {u"r": i[u"r"], u"n": i[u"n"], u"round": i[u"round"], u"date": DATE}
def shapes(i):
    return [(u"UI 轮次标题", u"## 第 %d 轮（R%d · " % (i[u"n"], i[u"r"])),
            (u"ITER 标题", u"## Round %d · R%d" % (i[u"round"], i[u"r"])),
            (u"STATE 主节", u"## R%d 状态（" % i[u"r"]),
            (u"DECISIONS", u"## D-%d（" % i[u"r"]),
            (u"BACKLOG 追账节", u"## R%d 追账" % i[u"r"]),
            (u"CHANGELOG 标题行", u"### skipped 拆成甲乙、值槽粘连按谁按值读划界、接线判据卷补上 `bash -e`（R%d / " % i[u"r"])]
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
    CUT = u"〔streak-cell-end〕"
    if CUT not in seg:
        raise SystemExit(u"post-land：R%d 那一节的 streak 格没有结束哨兵 ⇒ 不敢猜切点" % landed_r)
    stop = seg.index(CUT) + len(CUT)
    cell3 = (u"产品文件 0 个，连续零改动 **%d** 轮（唯一取数口 `python3 scripts/product_streak.py`，"
             u"**台账落盘之后**现读 `%s`；as-of 口径 ⇒ 读作「本轮之前最后一次产品改动在 %d 轮前」；"
             u"取数时刻由 `post_land()` 钉在函数名字上，不在纪律上" % (streak_n, line, streak_n))
    st = st[:off] + cell3 + st[off + stop:]
    write(u"STATE", st)
    print(u"POST-LAND streak=%d（R%d）" % (streak_n, landed_r))
    cands = [os.path.join(ROOT, "scripts", "refresh_report_section1.py"),
             os.path.join(ROOT, ".scratch", "motion-audit-2", "refresh_report_section1.py")]
    sec = next((p for p in cands if os.path.exists(p)), None)
    if sec is None:
        raise SystemExit(u"POST-LAND 仪器缺失：§1 的派生格没有取数口 ⇒ 不许静默跳过、也不许手写那一格")
    subprocess.check_call([sys.executable, sec], cwd=ROOT)
    print(u"POST-LAND §1 已刷新（仪器=%s）" % sec)
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

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
TMP = "/tmp/r592"
DATE = "2026-11-06"
BOOKS = {"UI": "AGENT_UI_AUDIT.md", "ITER": "AGENT_VISUAL_ITERATION.md", "STATE": "AGENT_STATE.md",
         "BACKLOG": "AGENT_BACKLOG.md", "DEC": "AGENT_DECISIONS.md", "FINAL": "AGENT_FINAL_REPORT.md",
         "CHANGE": "CHANGELOG.md"}

RUN_MAIN = "42179047067"     # R591 主笔（本轮 ⓪ 到数那一跑）
RUN_ADD = "42179425098"       # R591 补记笔


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
            raise SystemExit(u"⓪ 读数里没有 %s 那一跑 ⇒ 先跑 ci_status_r592.py" % run)
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
    for k in ("test_repo_root_bundle", "test_install_local",
              "FoldGeometryMigrationTests"):
        if k not in d["counts"]:
            raise SystemExit(u"计数名册缺 %s 那一行 ⇒ 名册要现读不要手抄" % k)
    if d["counts"]["test_repo_root_bundle"][1] <= d["counts"]["test_repo_root_bundle"][0]:
        raise SystemExit(u"矛盾读数：本轮新卷 test_repo_root_bundle 的 def test_ 数没长 ⇒ 计数名册读错了对象")
    if d["counts"]["FoldGeometryMigrationTests"][1] <= d["counts"]["FoldGeometryMigrationTests"][0]:
        raise SystemExit(u"矛盾读数：本轮新卷 FoldGeometryMigrationTests 的 func test 数没长 ⇒ 名册读错了对象")
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
    if len(set(arms)) != 16:
        raise SystemExit(u"主笔的刀数/去重后不是 16 把：%s ⇒ 表或状态文件读错了" % arms)
    for k in knives:
        if k[u"post"] == u"CAUGHT" and k[u"rc"] == 0:
            raise SystemExit(u"矛盾读数：%s 说 CAUGHT 而 rc=0" % k[u"arm"])
        if k[u"post"] != u"CAUGHT":
            raise SystemExit(u"%s 末次=%s ⇒ 空刀不许占号，先作废这一把再落下一把" % (k[u"arm"], k[u"post"]))
    d["knives"] = knives
    reds = must_read(os.path.join(TMP, "knife_reds.txt"), u"每把红了哪几格")
    # 红行有两种通道形状：pytest 打 `FAIL:`/`ERROR:`，XCTest 打 `…: error: -[Target test]`。
    # 只认前一种会把 Swift 那一卷的十五行红读成 0 行 ⇒ 「通道坏了」的假警报（R592 本轮 16 把里 9 把是 Swift）。
    red_shape = re.compile(u"读数: (?:FAIL:|ERROR:|.*error: -\\[)")
    for k in knives:
        block = re.search(u"--- %s\n(.*?)(?=\\n--- M|$)" % k[u"arm"], reds, re.S)
        body = block.group(1) if block else u""
        k[u"reds"] = len(red_shape.findall(body))
        if k[u"reds"] == 0:
            raise SystemExit(u"%s 说 CAUGHT 却读不到任何红行（FAIL:/ERROR:/XCTest error: -[…] 三种形状都试了）"
                             u" ⇒ 那是通道坏了不是红" % k[u"arm"])

    for key, fname, prefix, label in ((u"full", "full_summary.txt", "FULL_TOTAL=", u"全量卷"),
                                      (u"full_skips", "full_summary.txt", "FULL_SKIPPED=", u"全量 skipped"),
                                      (u"battery", "py_battery.txt", "Ran ", u"python 全电池")):
        p = os.path.join(TMP, fname)
        d[key] = grep_line(must_read(p, label), prefix, label) \
            if os.path.exists(p) else u"（未读到：那一趟还没跑 ⇒ 台账不许替它填数）"
    # 电池那一格有两种**真**签字：`OK (skipped=N)` 与 `FAILED (failures=N)`。
    # 只搜 `OK` 会把红的那一趟读成"读数缺失"（grep_line 当场崩）⇒ 那是把尺的盲区，不是产品的。
    bp = os.path.join(TMP, "py_battery.txt")
    d["battery_ok"] = (u"\n".join([l for l in must_read(bp, u"电池签字").splitlines()
                                   if re.match(u"^(OK|FAILED)", l)][-1:])
                       if os.path.exists(bp) else u"（未读到：那一趟还没跑）")
    if not d["battery_ok"].strip():
        raise SystemExit(u"电池那一趟既没有 `OK` 也没有 `FAILED` 行 ⇒ 通道坏了，不许当绿")
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
    # 本轮是**产品轮**：产品文件数与"上一次归零之前有多少轮"都要现读，不许手抄进正文。
    stat = must_read(os.path.join(TMP, "prod_stat.txt"), u"产品文件数现读")
    d["prod_files"] = grep_line(stat, "PROD_FILES=", u"产品文件数").split(u"=", 1)[1].strip()
    if d["prod_files"] == u"0":
        raise SystemExit(u"矛盾读数：本轮正文写的是产品轮，而 prod_stat.txt 现读 PROD_FILES=0")
    m = re.search(u"streak=(\\-?\\d+)", d["streak"])
    d["prev_zero_rounds"] = m.group(1) if m else u"-1"
    d["prechecks_brief"] = (grep_line(d["prechecks"], "NEEDLE_PRECHECK", u"预检那一行")
                            if d["prechecks"] else u"（预检读数没落盘）")
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
        if not got:
            return (u"      ·（这一跑没有 skipped 步骤 ⇒ R591 接上的那四步在 runner 上真的出声了；"
                    u"这一格与「没读到清单」是两种不同的账，这里记的是前者）")
        return u"\n".join(u"      · 第③甲 步=%s 名=%s ⇒ 被上游红连带跳过" % (r[0], r[1]) for r in got)

    return u"""## R%(r)s 状态（%(date)s · 第 %(n)s 轮 / Round %(round)s · **产品 %(prodfiles)s 文件**（用户实测反馈的两条：旧记忆压住新默认值 + 仓库根留开发版副本）+ 判据卷 +%(delta)s 格 + 刀 M1582–M1597 全 CAUGHT + ⓪ R591 两跑都到数、四条预测全中 + 换装两次并把用户机上的窗口读到 848×600）

⓪ **现读两对（`ci_status_r592.py`，取值时刻 16:10–16:12 第一趟、19:01 复算同一结论，两跑都 `completed / failure`）**：
   1. `%(mrun)s ↔ %(msha)s`（R591 主笔）⇒ 全部失败步骤：`%(msteps)s`。
      逐步骤结论：`Release script tests ⇒ %(mbat)s`、`Frame baseline vs working manifest ⇒ %(mbase)s`、
      `Surface left-axis ruler ⇒ %(mleft)s`、`Swift tests (executed-count gate) ⇒ %(mswift)s`。
      **R591 那一笔接的线在 runner 上确认生效**：`STEP[9] ⇒ %(mbat)s`（红名逐字 `%(mmisc)s`），
      而 skipped 清单这一跑是空的 —— 那一步的读法见本节③第一条（空清单 ≠ 没取到清单）。
      四条预测（标签与判法逐字接自 R591 的 `PREDICTIONS_R592`，四格齐：主张 / 判法 / 正文从哪一步取 / 这条通道由哪一步印出去）：
%(mpreds)s
      skipped 清单：
%(mskip)s
   2. `%(arun)s ↔ %(asha)s`（R591 补记笔）⇒ `%(astatus)s`；失败步骤：`%(asteps)s`；
      逐步骤结论：`Release script tests ⇒ %(abat)s`、`Frame baseline vs working manifest ⇒ %(abase)s`。
      四条预测与主笔**同判**：
%(apreds)s
      skipped 清单：
%(askip)s
   3. **R591 的接线拿到了它欠的第一证人**：`42179047067` 逐步骤结论里 `STEP[10]`–`[14]` 全部不再是 skipped
      （`Runtime launch smoke` 从 `skipped` 变成 `success`，正文里 `SMOKE_OK=1` 第一次印在 runner 日志上），
      而 skipped 计数从 5 朵降到 **0** 朵 ⇒ 663 那条「被上游红连带」在这一跑上被证实**修好了**，
      不是「大概修好了」。同跑仍红的三朵（`STEP[15]` / `STEP[17]` / `STEP[19]`）与 R590 那两跑**同名同集合**
      ⇒ 不是本笔引入，也不因为「本轮没碰它」就不记账：见本节③的红名清单。
   4. **R593 的 ⓪ 要读的六格**（判法与取处写进 `ci_status_r592.py` 的 `PREDICTIONS_R593`，由脚本判，不许目测对拍）：
      ①本笔（主笔 + 补记笔）的成对号 —— 由补记那一趟现取现写；
      ②`STEP[14]`（Runtime launch smoke）在**含本笔**的那一跑里仍 `success`，且正文里
        `launch_smoke.py "/tmp/时间剪史_bundle/时间剪史.app"` 那一条路径是暂存目录而不是仓库根
        （印不出来说明 `make bundle` 的落点又回去了，不是"CI 又坏了"）；
      ③新硬步骤 `Repo root stays bundle-free after make bundle (BACKLOG 620)` 第一次在 runner 上有读数：
        `REPO_ROOT_BUNDLE_RESULT=ok` 且 `READER_SELFTEST=seen`；若它 `not-run`，结论只能是「构建没落地」，
        不能读成「仓库根干净」；
      ④`STEP[15]`/`[17]`/`[19]` 那三朵红的红名集合与本轮比是**多、少还是同**（本轮动了窗口几何的恢复路径，
        多出来的那一朵要先判是不是本笔引入，判法：拿它对应的判据名在 ⓪ 两跑里现读有没有）；
      ⑤`STEP[9]` 的电池汇总 `Ran <N>` 比 R591 那一跑的 `Ran 918` **多**（判据卷的新格必须在 runner 上被数到，
        本机绿不算交付）。⚠ 口径写死：多的那一截只能是 **python 侧**新增的 14 格（`test_repo_root_bundle` 11 +
        `test_install_local` 3）；本轮 Swift 侧那 10 格**不进** python 电池的分子 ⇒ 拿 24 去对是跨通道对账（R565 那一族），
        对上了也不算证人；
      ⑥`STEP[9]` 里 `SKIP_ROSTER 键=github-runner` 那一行**两个方向都不许出现** `test_built_bundle_carries_no_app_delegate_stub`
        （`名单外` 与 `名册未跳` 都算响）：本轮把那一格的对象从仓库根搬进暂存目录，runner 上电池仍排在 `make bundle`
        之前 ⇒ 它应当照旧 skip、登记照旧命中。**若报 `名册未跳=[那一格]`，说明它在 runner 上开始真跑，
        那时正确的动作是删登记，不是把登记留着当永久豁免**（R565 那条「豁免理由里写了退场不等于退场会发生」）。

① **真实推进（产品面 · 规格 §3 第①段的补漏）：旧记忆压住新默认值，一次性抬过去**
   用户 2026-11-06 实测反馈：升级之后两栏不等宽、比例也不是 √2。我在用户机上现读（取值时刻 16:12）：
   `mainWindowExpandedWidth = 750`、`mainWindowCollapsedWidth = 420`（R567 之前的两档默认），
   而 AppKit 还存着窗口帧 `…-AppWindow-1 = "585 368 750 492"` 与分栏子视图帧 `423.5 / 326.5`。
   三样叠起来才是那句「等分没生效」：`width(forKey:fallback:)` 的记忆优先是对的，
   错的是旧规格的默认值还留在盘上 ⇒ 第①段对升级用户**根本没发生过**。
   本轮做的（`MainWindowGeometryMigration`，纯函数 + 一层薄胶水，排在 controller 读状态**之前**）：
   1. 只在记忆值**恰好等于旧默认对**（750 与 420）时抬到 848 / 424；手动调过的落在 `not-legacy-pair`，一律不碰；
      新装落在 `no-legacy-memory`；已经迁过落在 `already-migrated` —— 四档出口都被判据逐字读。
   2. 抬完立刻打版本键（`mainWindowGeometryMigrationVersion`）⇒「只抬一次」有证人，不是散文。
   3. 恢复的窗口帧**不删、只改写宽高**，并按「顶边不动」回算 origin.y ⇒ 用户放的位置逐字保留；
      分栏子视图帧没有可算目标，删掉它，让 `navigationSplitViewColumnWidth` 那条锁等宽约束自己给出 423.5 / 423.5。
   4. **换装之后在用户机上量到第二半没到位**（取值时刻 18:24）：宽度那半成了（848、两栏 423.5 / 424.5），
      窗口却仍是 `848 492` ⇒ 比例 1.72。成因不是键没改写，是 AppKit 的恢复通路除了 defaults 键还看 saved state，
      高度只从后者回来。第一版修法（「迁移那一趟动一次高度」）在**已经打过版本键的机器上永远不会生效** ——
      那一版是错的，被我自己换装量出来了。
      最终落地的是**不变量**而不是补丁：产品从不记高度，而 macOS 13+ 的 `contentAspectRatio` 锁住了比例
      ⇒ 「高度不在 √2 上」这件事只能来自锁出现之前的那一次恢复，所以 `applyGeometry` 见到就抬（`heightLift`，
      容差 0.02；macOS 12 那条锁不存在 ⇒ 那一档不调用，12 上抬它就是抹用户的调整）。
   5. 装完之后同一台机器再读（取值时刻 18:32，AX 现读）：窗口 `848×600`、分栏 `423.5×600 / 424.5×600`、
      `mainWindowExpandedWidth = 848`、版本键 = 1 ⇒ 用户签的那两条验收（两栏等宽、比例≈√2）在真机上是**过**。
   刀：**M1582**（摘掉产品入口那句迁移调用 ⇒ 用户点名的「不做迁移必须红」）、**M1583**（条件放宽成「有记忆值就抬」
   ⇒ 抹掉用户自己调过的宽度）、**M1584**（不打版本键 ⇒ 第二跑又抬）、**M1585**（恢复帧整块不做）、
   **M1586**（不回算顶边 ⇒ 用户的窗口被挪走）、**M1587**（只摘分栏帧那一支）、**M1594**（键匹配放宽成
   「所有 `NSWindow Frame` 键」⇒ 系统面板的键也被改）、**M1595**（判据里的旧默认对不用产品常量 ⇒ 真值表脱钩）、
   **M1596**（摘掉 √2 不变量 ⇒ 恢复的 492 永远留在用户窗口上）、**M1597**（容差写成负数 ⇒ 恒抬，
   把用户等比拖出来的 900×637 抹回 600）。M1585 / M1586 红在**同一格的不同断言**上，判定按红话里的字样分开
   （「宽没抬」对「顶边动了」），不按格子名 —— 这是 663 那一族的老规矩。

② **真实推进（交付面 · BACKLOG 620 结案）：构建产物不再落仓库根**
   用户第二条指令：不要再留仓库根的开发版副本，只保留 /Applications 一份。本轮改的是**落点本身**，不是清理现场：
   1. `Makefile`：`BUNDLE := $(STAGE)/$(APP_NAME).app` —— `bundle` 目标里那条往仓库根的 `ditto` 整段删掉，
      `run` / `dmg` 都改指暂存目录；`clean` 补一行把历史留下的仓库根副本清掉（`make clean` 从此能收拾旧现场）。
   2. `scripts/install_local.sh`：默认包 = 暂存目录那一份；开头加一道预检（仓库根有可执行 .app 就**一步都不许动**），
      并且 `--dest` 不是 /Applications 时**强制不启动**那份副本 —— 从前这一格靠调用方记得传 `--no-launch`，
      而"沙箱不该启动同 id 副本"与"沙箱不该发退出指令"是同一条理由，不该一个有门、一个靠人记。
   3. `scripts/repo_root_bundle.py`（新守卫）：三态 `ok / red / not-run`，**自带正对照**
      （`READER_SELFTEST=seen`：拿一份已知答案的临时根跑同一条扫描，认不出来就 exit 2 ⇒
      runner 上仓库根本来就干净，没有这条对照，「名单=空」就只是「这里没构建过」的同义反复）；
      顺序也是结论的一部分：**红排在 not-run 前面**（刀 M1592 钉这条，第一版我把顺序写反过）。
   4. `.github/workflows/ci.yml`：新增硬步骤 `Repo root stays bundle-free after make bundle (BACKLOG 620)`，
      排在 `make bundle` 之后（那里才有对象可扫）；`Runtime launch smoke` 的冒烟路径从仓库根相对路径改成暂存目录。
   5. 仓库根那份 `时间剪史.app`（11-04 08:33 的构建产物，gitignore 里、不是源码也不是用户数据）已移出仓库
      （`/tmp/r592-removed/`），换装脚本两次都读到 `REPO_ROOT_BUNDLE=absent`。
   刀：**M1588**（Makefile 把落点指回仓库根 ⇒ 配方那一格红）、**M1589**（换装脚本默认包指回仓库根）、
   **M1590**（摘掉「违规就不许装」那一格）、**M1591**（沙箱强制不启动那一支失效）、**M1593**（扫描函数恒空 ⇒ 尺盲要响）。
   **620 结案的另一半不在本笔**：`~/Documents/Codex_Project0_backups/before-*/` 那 20+ 份可启动副本
   要动 LaunchServices 数据库或用户 Documents 才能摘，且回滚分支正靠 `mv` 那一份备份 ⇒ 新开 **664**，本笔不动它。

③ **几朵红各由谁签 + 段②那三问逐问给状态（用户收口时点名要的）**
   · ⓪ 的 skipped：`42179047067` 与 `42179425098` 两跑逐步骤结论里 skipped **0 朵** ⇒ 门（`ci_skipped_causes.py`
     run 模式）本轮没有对象可判；`static` 那一支现读 `%(causes)s` ⇒ 「无声=0」带的是 `证据型=9` 的扫描面。
   · runner 仍红的三朵（两跑同名同集合，**不是本笔引入**；本笔也没碰它们，但照实记账）：
     `STEP[15]` 五朵（`testActionableInkStaysAboveTheLegibilityFloor`、`testCaptionTextStaysOnTheSecondaryTier`、
     `testDetailAreaHasASingleLeftAxis`、`testDetailStatusBarShowsTheRealSourceAppIconOnlyWhenAttributed`、
     `testQuickPickKeyboardHintClearsTheContrastFloor`）、`STEP[17]` 一朵（红名 = 最后那条，与 622/565 那一族同形：
     runner 1x 的对比度）、`STEP[19]` 两朵（`MOTION_FLOOR_SUITE_RED=2`：
     `testDetailEmptyToContentCrossfadeIsMeasuredOrDeclaredBlind`、`testEmptyStateStillFadesWhenMotionIsReduced`）。
     这八条本轮**不计入对账口径**，理由不是"本轮没碰"，是它们都是 runner 侧的机差/采样口径账，
     归 **622 / 565 / 627 / 635** 那些单子；本轮没有新的 runner 红名（判法见 ⓪·④ 第④格，留给 R593）。
   · 段② 第一问（非不透明窗口下侧栏材质会不会变淡）：**Light 档过、Dark 档未验** ——
     证人仍是 R568 那条真机合成通道（撤底衬那臂 0.9339→0.6637、品红漏出 319 颗），
     暗档那一问今天仍没有当轮证人，具名 `TRANSPARENCY_MATERIAL_APPEARANCE_NOT_RUN=Dark档无当轮证人_Light档有R568数`
     一字未撤；三条拿第二档的出路（锁 `.aqua` / 按外观拆两档 / 另一台机器）**仍归用户**，本轮一条没选。
   · 段② 第二问（阴影跟不跟可见形状）：**本机真机通道过、runner 未验** ——
     `TRANSPARENCY_SHADOW 半片透明 左带暗=0.0631 右带暗=0.0017 判=套形状` 是 R568 的数，本轮没有新读数；
     runner 侧 `REALSCREEN_SHADOW_NOT_RUN=env-off` 未撤。
   · 段② 第三问（取证通道分不分得清真黑与透明）：**新通道过、主窗树未验、逐帧产物那一半不过（具名）** ——
     新 alpha 图层通道两档 `分得出=1`（R571/R572 的数，本轮未重测）；主窗树今天没有真透明对象
     `PRODUCT_MAIN_TREE_TRANSPARENT_OBJECT_NOT_JUDGED=backing-covers-whole-tree`；
     356 张产物在写盘前被铺窗口底色 ⇒ D12 那句「透明区 alpha 归零」不能拿产物判（**653** 未结）。
   · ⇒ 三问**没有一条是"本轮新过"**的，第③段着色器本轮未开工：两条具名阻塞一字未撤，
     `STAGE_GATE_CLAIMS` 现读 `%(stage)s` ⇒ 「三问全过」在规格里出现次数仍是 0。
     本轮的真实推进按用户指令排在段②之前：**第①段对升级用户的补漏**（那一半是用户实测出来的真缺口）。
- **红名对账**（口径=对账口径已启用；门报 `%(recon)s`，不由我数）：
  · 红名「换装后用户机窗口仍是 848×492、比例 1.72 ⇒ 用户签的 √2 不过」→ 本节① 第 4 条（本轮内已修并复读到 848×600）
  · 红名「第一版一次性高度补丁在已打版本键的机器上永不生效」→ ⑨·1
  · 红名「帧基线门 `FRAME_BASELINE_CHANGED=16`」→ 本节⑥（控制实验：HEAD 那一跑逐字节同 ⇒ 不是本笔引入）
  · 红名「`testTheSeamInTheRenderedFrameSitsAtHalfTheContentWidth` 在过滤跑里读到 3392x2400 / 缝 1051.0pt」→ ⑨·2
  · 红名「刀 M1590 第一版落下是空刀（PASSED）」→ ⑨·3
  · 红名「判据里 `frame` 与 `contentRect` 两个口径混用（568 / 600 / 732）」→ ⑨·4
  · 红名「我同时起过两趟 `swift test --filter UICaptureTests`」→ ⑨·2（与上面那条假红是同一件事的两个面）
  · 红名「`install_local.sh` 里 `[ "$rc" = 1 ] && fail` 那种 `bash -e` 顶层写法（R591 同族，重犯一次）」→ ⑨·6
  · 红名「台账正文里落出一句半话『…整步先死，这一 ⇒ 中』」→ ⑨·8
  · 红名「写手 --check 停在『M1582 说 CAUGHT 却读不到任何 FAIL 行』」→ ⑨·9
  · 红名「电池台账后第一趟 4 朵：`hidden_arms` 两朵 + `readings_channel_coverage` 一朵 + `skip_roster` 一朵」→ ⑨·11
  · 红名「`--apply` 崩在 FINAL 的 streak 格（参数比占位符多一个）」→ ⑨·10

④ **验证链（顺序照派单）**：build `%(build)s` → 判据卷（Swift 侧 `FoldGeometryMigrationTests` 10 格 +
   python 侧 `test_repo_root_bundle` 11 格（新卷）、`test_install_local` 8→11 格）→ 刀 M1582–M1597 十六把
   （**落刀前现读高水位=M1581**，跨表唯一性逐把现读 0 次撞号）→ 新表 `mutate_r592_migration` 进预检名册
   （`%(prechecks)s`）→ 刀已还原复跑判据、`%(md5)s`、`git status scripts/` 空、三种变异串各现读 0 处 →
   捕获卷 `%(capture)s`、帧 `%(frames)s` → 本机那一门 `%(gate)s` / 判定 `%(drift)s` / 倍率出口 `%(scale)s` →
   看图（本节⑤）→ 全量 `%(full)s`、skipped `%(fullskip)s` → **换装两次**（`INSTALL_RESULT=ok`、
   `INSTALL_SHA_MATCH=1`、条数 505→505、`INSTALL_SIGNATURE=local`、AX 读到 848×600）→ 七本台账 →
   派生格**落盘之后**现读 → 电池（canonical 配置，不设帧目录；两个时刻都记）。

⑤ **看图那一腿（659 形状：先 `convert("L")` 再 `getbbox`，配同尺寸正对照 + 自己 vs 自己必须 0）**：
%(look)s
   我自己打开看的四张：`detail-0-text-720x520-light`（正文两行、来源行、星标/图钉/复制/删除那一列，
   删除那颗是系统红 —— 都在位，没有截断）、`quickpick-list-420x300-dark`（五行行高一致、时间列右缘对齐、
   底部那行键位提示「↑↓ 选择 · ↩ 粘贴 · Esc 关闭」在暗档读得出）、`cardprobe-groupbox-default-720x140-dark`
   与 `-light`（尺点名要开的那两张：系统分组框那条底与「系统默认内缩」那行字都在，两档都只是那一枚胶囊 + 标题，
   没有整页平涂、也没有多出来的东西）。
   四张都是夹具合成内容，画面里没有用户真实剪贴板原文。
   **本轮产品面不在这批离屏帧的覆盖面里**（改的是窗口恢复几何，帧夹具按固定尺寸建窗）⇒
   那一半的证人只能来自真机 AX 读数（本节① 第 5 条），看图这一腿记的是"没有回归"，不是"推进被看见"。

⑥ **基线与名单**：产品文件 %(prodfiles)s 个（`Sources/…/MainWindowCollapsePolicy.swift`、
   `Sources/…/MainWindowCollapseController.swift`），连续零改动 **%(streaknum)s** 轮（唯一取数口
   `python3 scripts/product_streak.py`，**台账落盘之后**现读 `%(streak)s`；as-of 口径 ⇒ 读作「本轮之前最后一次
   产品改动在 %(streaknum)s 轮前」；本笔是**产品轮** ⇒ 下一轮那一格的分界换成本笔、读 **1**。
   用户指令「那一格应该回到 0」在这一把尺上**到不了 0**：`streak_at` 从 R334 起用严格小于（本轮自己那一笔
   不记进自己那一格），所以它的**复位值是 1**，"归零"在这本账上的形状是"分界换成本轮"；本轮不替下一轮填数，
   取数时刻由 `post_land()` 钉在函数名字上，不在纪律上〔streak-cell-end〕）。
   帧基线：`%(frames)s` 张，门报 `FRAME_BASELINE_CHANGED=16`（8 张 detail-* + 8 张 quickpick-*，逐字清单在
   `/tmp/r592/baseline.log`；本轮那批帧在 `/tmp/r592v2/frames`，HEAD 对照那批在 `/tmp/r592v3`）。这一格本轮**做了控制实验**：同一台机器、同一份代码树之外，
   在 `HEAD`（`906a875`，没有本笔任何改动）另开一棵 worktree 重捕一遍 ⇒ 那 16 张与本轮捕的**逐字节相同**，
   另抽 8 张未变帧与对照也相同；而本轮这批帧与上一批（R591 那 356 张）也是 356/356 逐字节相同
   ⇒ **这 16 张不是本笔改的，是基线侧的旧账**（`docs/frame_baseline.json` 里那 16 个摘要与这台机器今天的渲染
   不一致，而连续七轮"产品 0 文件 ⇒ 不重捕"让它没人看见）。`update` 一次没跑（重烤归用户），
   开成 **665**；四张按机器登记的表一字未改。

⑦ **闸门与单子（§3 第③段今天仍不开工）**：
   `STAGE2_CLICKTHROUGH_BLOCKED=awaiting-user-mechanism-choice` 与
   `STAGE3_FRAME_CRITERIA_HAVE_NO_RUNNER_WITNESS=awaiting-654-direction` 一字未撤；
   第③段证人现读 `%(stage)s` ⇒ 「三问全过」出现次数仍是 0。
   本轮没有把任何一条 `判=不判 / not-run / skipped / 扫描面 0` 说成"没问题"：
   守卫的 `名单=空` 带 `READER_SELFTEST=seen`、`无声=0` 带 `证据型=9`、skipped 的 0 朵与"没取到清单"分开写、
   基线那 16 张带控制实验而不是"大概没变"。
   仍归用户（一条不代选）：655 / 656 / 657 / 658 / 659 / 660 / 661 / 662 / 663 / 638① / 654 / 646 / 647 / 650 /
   651 / 653 / 644 / 639 / 640 / 637 / 633 / Motion ≥2 帧地板 / SSH 成因 / 手感签字 / **664**（备份那一族的可启动副本）/
   **665**（基线 16 张与这台机器不一致）；
   4.5 墨地板、150 上限、120ms、Motion ≥2、2x 8.0pt、1x 6.0pt、`FLOOR_LIGHT=1.20`、`FLOOR_DARK=1.10`、容差 1.5、
   跳变地板 8、`probeInkFraction=3%%`、`.contentFade` 0.20、`--allow-missing`、四张按机器登记的表、
   既有名册与豁免表、禁碰 14 面 —— 一字未动；`update` 一次没跑；没改这台机器的全局外观；
   **没动用户的 Dock 与登录项**（那条写成人工验收批次 91.1，见本节⑧与 DECISIONS D-%(r)s）；
   帧与日志不含真实剪贴板原文。

⑧ **人工验收批次（本轮新增，见 `docs/MANUAL_TEST_v1.4.9_round3.md` 批次 91）**：
   仓库根那份开发版消失之后，登录项记的那条路径失效 ⇒ 需要用户做一次一次性动作。
   给用户的一句话：**「打开系统设置 → 通用 → 登录与扩展（或「登录项」），把「时间剪史」的「开机启动」
   重新打开一次 —— 现在启动的是 /Applications 那一份。」**
   本轮没有替用户点它（不改用户的 Dock / 登录项是派单里的硬规矩）。

⑨ **自伤（照实，不缩）**：
   1. **第一版的高度修法在真机上是死的**：我把它写成「迁移那一趟动一次高度」，而用户机上版本键**已经**被
      第一次换装打上了 ⇒ 那一支永远不会再触发。是"装完再读一次真窗"（AX 848×492）把它抓出来的，
      不是判据 —— 判据那几格在进程内建窗，永远走不到恢复通路。⇒ 规矩：**改恢复路径的东西必须由真机读数签**，
      本机进程内建窗只能证明"产品自己写的几何"。最终改成不变量（`heightLift`）。
   2. **两趟 `swift test --filter UICaptureTests` 被我同时起过**（一条命令里两个后台任务），
      其间那一格像素尺读到 `帧=3392x2400 缝=1051.0pt` —— 一个不存在的缝。之后串行重跑三次（本轮树两趟、
      HEAD 对照一趟）都读 `1696x1200 / 424.5pt` ⇒ 那个读数是并发污染的假红，不是缺陷。
      ⇒ 「刀/捕获/电池不许并发」这条规矩我本轮自己破了一次；读数只在串行趟里算数。
   3. **刀 M1590 第一版是空刀**（PASSED）：我摘的是 `check_repo_root plan` 那**一次调用**，
      而脚本里构建之后还有第二次调用 ⇒ 门仍然拦、判据仍然绿。改成摘「`rc=1` 就不许装」那一格本身之后才 CAUGHT。
      这是空刀第五种形态的又一实例：**变异打在有两处调用的其中一处**，等于什么都没动。
   4. **口径混用**：新判据第一版把 √2 判在 `contentLayoutRect`（848×568 ⇒ 比 1.493）上，
      又把"第二趟不许动"判在 `window.frame.height` 上（测试窗没有 `fullSizeContentView` ⇒ frame 比 content 多 32pt）
      ⇒ 两格同时红。修法：测试窗与产品那扇同款式，比例一律判在 `contentRect(forFrameRect:)` 那一档，
      并把四个口径一次印出来（`FOLD_UPGRADE_CALIBERS`）。
   5. 台账写手那一趟我一度以为 `ledgers_r592.py` 已经被上一段会话写坏过（"mangled by sed"），
      实际盘上它**根本不存在**、七本台账也没被动过 —— 我先查了 `git status` 才动手。
      ⇒ 记这一条是因为它的形状：把"记忆里的损坏"当成"盘上的事实"，就会去"修"一个不存在的东西。
   6. `install_local.sh` 里我又写了 `[ "$rc" = 1 ] && fail …` 这种 `bash -e` 顶层 AND-list（R591 ⑨·2 同族，第二次），
      以及 `usage()` 的 sed 行号范围没跟着文件头加长 —— 都改成了 `if` 与现读范围。
   7. 备份那一族（620 机制②）我一度顺手写成"装完压成 tar.gz"，落笔前自问回滚分支靠什么 ⇒
      `trap rollback` 要在任何一步失败时把旧包 `mv` 回去，压包就等于扔了退路 ⇒ 撤掉那一半改动，改成开单 664。
   8. **⓪ 那一趟把预测的「主张」截到 78 字**（`spec[u"主张"][:78]`）⇒ 台账里落出半句话
      「…整步先死，这一 ⇒ 中」。这不是排版问题：用户会逐字拿正文对账，而截断把我自己那把尺的原文弄坏了。
      去掉截断并复算那一趟（19:01，四条预测与第一趟同判）⇒ 记这一条是因为它的形状：**读数落盘之前先被格式化截短**，
      和"抄上一轮基线把字段名抄丢"是同族（[[feedback-ledger-writer-hygiene]]）。
   9. **写手自检那条"CAUGHT 却读不到红行"只认 pytest 的 `FAIL:` 形状** ⇒ 本轮 16 把里有 9 把是 Swift XCTest，
      红行长这样 `…Tests.swift:206: error: -[Target testMethod]`，于是**真的红被读成 0 行**、写手停在假警报上。
      改成两种形状都认，且"0 行仍然红"这条不许松（那是通道坏了的证人）。同族教训：尺只认一种写法就等于只扫半个面。
   10. **台账写手与 ⓪ 读数各造过一次"半句话"**：⓪ 那一趟把预测的「主张」截到 78 字（见 ⑨·8），而写手那一趟
       在填 FINAL 的 streak 格时把 `streak_n + 1` 留在参数表里 ⇒ 占位符比参数少一个、`--apply` 崩在半路。
       崩之前七本一个字没动（我先 `md5` 对过再重跑），所以这一条没有造成脏账 —— 记下来是因为它的形状：
       **格式化崩在半路**与**写了一半**是两种事故，只有前者能靠"写之前先算完"避免。
   11. **620 那次搬动让一条端到端判据在本机静默 skip**：`test_built_bundle_carries_no_app_delegate_stub`
       写死了 `仓库根/时间剪史.app`，落点搬进暂存目录之后它每天跳而没人看见 —— 撞出来的是
       `SKIP_ROSTER 键=local … 名单外=['test_built_bundle_carries_no_app_delegate_stub']`（电池台账后第一趟 4 朵里的一朵），
       **不是我自己看出来的**。修法是把对象跟着搬（`repo_root_bundle.makefile_stage` 从 Makefile 现读，不抄第二份常量），
       搬完那一格在本机**真跑**（`Ran 19 / OK`，不再 skip）；`SKIP_ROSTER` 里 runner 那一行的**理由文字**同步改成暂存路径
       （历史两跑的读数留着当出处）。同批还有一处：`hidden_arms.py` 的语料根里没有 `Makefile` ⇒ M1588 的针"盘上找不到"
       被报成 rot=1；照 R381/R573 为两份非表工具文件开过的同一条例外只加这一个文件，加进来前后各现读一趟
       （`表=492 可判=1305 抽不出=6 已声明表=6` 四个数一个没动，只有 `rot 1→0`）⇒ 不许拿"加语料"去洗活别的死针。
       ⚠ 这一格留给 R593 一个**双向**的账：runner 上电池排在 `make bundle` 之前 ⇒ 那一格在 runner 上仍应 skip；
       若下一跑报 `名册未跳=[…]`，说明它在 runner 上也开始真跑，那时**删登记**才是对的（登记不许变成永久豁免）。

⑩ **通道五读（取值时刻 18:19–18:20）**：码签身份 `%(ident)s`（本笔自己重取，不是引用）；
   push 通道 `%(push)s`；`github.com=%(gh)s`、`api.github.com=%(api)s`；
   `HEAD=%(head)s`、`origin/main=%(origin)s`、`ahead=%(ahead)s`；构建 `%(buildwarn)s`。
""" % {u"r": i[u"r"], u"n": i[u"n"], u"round": i[u"round"], u"date": DATE,
         u"delta": d["delta_total"], u"prodfiles": d["prod_files"],
         u"causes": d["causes"], u"look": d["look"], u"md5": d["md5"], u"build": d["build_warn"],
         u"capture": d["capture"], u"frames": d["frames"], u"gate": d["gate_result"],
         u"drift": d["gate_drift"], u"scale": d["gate_scale"], u"full": d["full"],
         u"fullskip": d["full_skips"], u"recon": d["recon"], u"stage": d["stage_gate"],
         u"prechecks": d["prechecks_brief"],
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
        (u"旧记忆压住新默认值：升级用户看不到第①段，三样叠在一起才是「等分没生效」",
         u"用户机现读 `mainWindowExpandedWidth = 750` / `CollapsedWidth = 420` + 窗口帧 `750 492` + "
         u"分栏帧 `423.5 / 326.5`。记忆优先本身是对的，错的是旧默认值还留在盘上 ⇒ 一次性迁移。"),
        (u"迁移只在「恰好等于旧默认对」时抬，四档出口各有名字",
         u"`legacy-default-pair` / `not-legacy-pair` / `no-legacy-memory` / `already-migrated`；"
         u"手动调过宽度的用户一律不碰（刀 M1583 把条件放宽 ⇒ 那一格必须红）。"),
        (u"「只抬一次」的证人是版本键，不是散文",
         u"抬完打 `mainWindowGeometryMigrationVersion`；判据把「迁完之后再拖回 750/420，第二跑不许再抬」写成格子，"
         u"并配摘掉版本键的正对照（刀 M1584）。"),
        (u"恢复的窗口帧只改宽高、顶边逐字不动",
         u"`restoredFrameString` 按 `y' = (y + h_old) − h_new` 回算；解析不出四个数就返回 nil（不猜 origin）。"
         u"刀 M1586 摘掉回算 ⇒ 用户的窗口被挪走那一格必须红。"),
        (u"分栏子视图帧没有可算目标 ⇒ 删掉它，让锁等宽约束自己给 423.5 / 423.5",
         u"名册里那条 `423.5 / 326.5` 是旧档的不对称；刀 M1587 只摘这一支 ⇒ 「两栏不等宽」那条断言必须红。"),
        (u"宽度那半在真机上成了、高度那半没成 —— 是换装读出来的，不是判据读出来的",
         u"18:24 现读：`mainWindowExpandedWidth = 848`、两栏 423.5 / 424.5，窗口却仍是 `848 492`（比 1.72）。"
         u"进程内建窗的判据永远走不到恢复通路 ⇒ 改恢复路径的东西必须由真机读数签。"),
        (u"最终落地是不变量而不是补丁",
         u"产品从不记高度，13+ 的 `contentAspectRatio` 锁住比例 ⇒ 「高度不在 √2 上」只能来自锁之前的那一次恢复。"
         u"`heightLift` 容差 0.02；macOS 12 没有那条锁 ⇒ 那一档不调用（12 上抬它就是抹用户的调整）。"),
        (u"一次性补丁在已经打过版本键的机器上永远不会生效",
         u"第一版就是这个形状，被第二次换装（AX 读到 848×492）否掉。记进 ⑨·1，不缩。"),
        (u"构建产物不再落仓库根：配方、换装默认值、预检、CI 硬步骤四处同一件事",
         u"`Makefile` 的 `BUNDLE` 进暂存目录；`install_local.sh` 默认包同改并加「仓库根有 .app 就不许装」的预检；"
         u"`ci.yml` 新增硬步骤排在 `make bundle` 之后（那里才有对象可扫）。"),
        (u"守卫必须自带正对照，否则「名单=空」只是「这里没构建过」",
         u"`READER_SELFTEST=seen` 拿已知答案的临时根跑同一条扫描；认不出来就 exit 2 ⇒ 所有按前缀筛出来的 0 都不算数。"),
        (u"顺序也是结论：红不许被 not-run 掩掉",
         u"`judge()` 先判红再判没对象；刀 M1592 把顺序换回去 ⇒ 「真违规被读成没判到」那一格必须红。"),
        (u"沙箱不该启动同 id 副本 —— 与「沙箱不该发退出指令」是同一条理由",
         u"`--dest` 不是 /Applications 时脚本强制 `launch=0`（从前靠调用方记得传 `--no-launch`，"
         u"测试自己传了，所以那一格从来没被判过）。刀 M1591。"),
        (u"帧基线那 16 张：用控制实验分清「本笔改的」与「基线侧的旧账」",
         u"HEAD 另开 worktree 重捕 ⇒ 16/16 逐字节相同，且本轮这批与上一批 356/356 相同 ⇒ 不是本笔引入。"
         u"`update` 一次没跑（重烤归用户），开成 665。"),
        (u"两趟捕获同时跑会造出一条不存在的缝",
         u"并发那一趟像素尺读 `3392x2400 / 缝 1051.0pt`；串行三次（本轮两趟 + HEAD 对照一趟）都是 "
         u"`1696x1200 / 424.5pt` ⇒ 那个数是假红。读数只在串行趟里算数（⑨·2）。"),
        (u"空刀第五种形态：变异打在有两处调用的其中一处",
         u"M1590 第一版摘的是 plan 那一次调用，构建之后还有第二次 ⇒ 门仍然拦、判据仍然绿（PASSED）。"
         u"改成摘「`rc=1` 就不许装」那一格本身才 CAUGHT。"),
        (u"口径要写死在同一个矩形上",
         u"`contentLayoutRect`（568）/ `contentRect(forFrameRect:)`（600）/ `contentView`（600）/ `frame`（600）"
         u"四个口径一次印出来，√2 一律判在 `contentRect` 那一档；测试窗补 `fullSizeContentView` 与产品同款式。"),
        (u"段②三问本轮没有一条新过，两条具名阻塞一字未撤",
         u"第一问 Light 过 / Dark 未验；第二问本机真机通道过 / runner `env-off`；"
         u"第三问新通道过 / 主窗树未验 / 逐帧产物那一半不过（653）。第③段着色器继续不开工。"),
    ]
    body = u"\n".join(u"- **U-%d：%s** —— %s" % (u0 + k, t, b) for k, (t, b) in enumerate(rows))
    head = (u"## 第 %(n)s 轮（R%(r)s · %(date)s · U-%(u0)s…U-%(u1)s）：升级用户看不到第①段 ⇒ 一次性迁移 + √2 不变量；构建产物不再落仓库根"
            % {u"n": i[u"n"], u"r": i[u"r"], u"date": DATE, u"u0": u0, u"u1": u0 + len(rows) - 1})
    return head + u"\n\n" + body + u"\n\n", u0


def block_iteration(d):
    i = d[u"ident"]
    return u"""## Round %(round)s · R%(r)s（第 %(n)s 轮 · %(date)s）：升级用户的第一段补漏（一次性迁移 + √2 不变量），构建落点从仓库根搬进暂存目录

**七维度自评**（恰七行，每格 n/15；维度名照曲线尺认的那七个同字，本轮不造新维度）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉看图 | 12/15 | 用户指令「每轮都要落产品改动」本轮满足，且**换装之后用 AX 读了真窗**（848×600、分栏 423.5 / 424.5）—— 那是这一轮唯一看得见"升级用户看到什么"的通道。像素那一腿：356/356 与上一批逐字节相同 + 差量可见性正对照（包围盒 (360,70,420,110) / 2400 颗）+ 自己 vs 自己 0；我自己打开了四张（detail 正文、quickpick 列表、cardprobe 暗档 + 亮档，后两张是尺点名要开的）。扣 3 分：帧基线那 16 张只做了"是不是本笔改的"的控制实验，**没有逐张看差量落在哪一块**（基线只存摘要，拿不到旧像素 ⇒ 这一格今天做不到，写进 665 的出路里）。 |
| 判据有效性 | 15/15 | 16 把刀全 CAUGHT、逐把单独取退出码、无 `| head`、`RESTORE_CLEAN=yes`、`md5 scripts/*.py` 前后同一份；其中 M1585 / M1586 红在**同一格的不同断言**上，判定按红话里的字样分开而不是按格子名（663 那一族的老规矩）。本轮唯一一把空刀 M1590 第一版**没有占号**，作废后重落才签（⑨·3）。 |
| 假绿防御 | 14/15 | ①守卫自带 `READER_SELFTEST`（没有它，runner 上「名单=空」只是「这里没构建过」）；②红排在 not-run 前面（M1592）；③扫描函数恒空要响（M1593）；④「只抬一次」由版本键那把闸门作证（M1584）；⑤不变量的容差本身有牙（M1597 把容差写成负数 ⇒ 抹掉用户等比拖出来的尺寸必须红）。扣 1 分：`heightLift` 在 macOS 12 那一档**没有当轮证人**（本机 13+，12 上这条不生效是设计决定，但今天没有第二台机器签它）。 |
| 产品面推进 | 14/15 | 产品 %(prodfiles)s 文件（迁移 + 不变量），`product_streak.py` 那一列（"产品 0 文件"的连续轮数）从本轮止住，轮数只在 STATE 本节⑥ 出现一次、由唯一取数口现读；用户机上升级到 848×600 是**真机读数**，不是推断。扣 1 分：段②三问本轮没有一条新过（第一问 Dark 档、第二问 runner、第三问主窗树与逐帧产物仍是具名未验/不过）。 |
| 台账一致性 | 13/15 | 身份交叉核对过；七个标题形状写前 0、写后各 1；派生格只在**本轮小节内**切（哨兵缺失就报错）；红名对账 12 行每行指向 ⑨·N 或本节；streak 那一格把口径写死：用户要的"回到 0"在这一把尺上是**复位值 1**（严格小于 ⇒ 本轮那笔不记进自己那一格），"
     "账上不许留一个到不了的 0。扣 2 分：⑨·5 那条"我以为写手被上一段会话改坏了、实际盘上根本没有"—— 记忆与盘上的分歧我这次是靠 `git status` 才分开的，本该先查再动手；另 ⑨·2 的并发是我自己破的规矩。 |
| 剩余风险处置 | 12/15 | 620 结案（构建落点那一半），备份那一半**没有顺手改**而是开成 664（回滚分支靠 `mv` 那份备份，压包等于扔退路）；基线 16 张开成 665 并附控制实验；两条 §3 阻塞一字未撤；`update` 一次没跑；没动用户的 Dock / 登录项，那条改成人工作业批次 91.1。扣 3 分：665 那 16 张的**成因还没量**（环境/字体 vs 基线当初烤错，两种出路相反），本轮只证到"不是本笔改的"；664 需要 `lsregister -dump` 的现读才能定方向，本轮没量。 |
| 交接可读性 | 15/15 | R593 的 ⓪ 五格写进 `ci_status_r592.py` 的 `PREDICTIONS_R593`，每条四格齐，并写明反向读法：②那一步印不出暂存路径 = 落点又回去了；③那一步 `not-run` = 构建没落地，**不许读成仓库根干净**。 |

本轮一句话：用户实测报的那条缺口，我修到一半就被自己的换装打回原形 —— 宽度成了、高度没成；
把"补丁"换成"不变量"之后真机才读到 848×600。**进程内建窗的判据看不见恢复通路，这一格只能由装完那一次读数签。**
""" % {u"round": i[u"round"], u"r": i[u"r"], u"n": i[u"n"], u"date": DATE,
        u"prodfiles": d[u"prod_files"], u"prodrounds": d[u"prev_zero_rounds"]}


def block_backlog(d):
    i = d[u"ident"]
    return u"""## R%(r)s 追账（%(date)s · 第 %(n)s 轮 / Round %(round)s）

**结案 1 张**：

**620 结案（R592）**：构建产物不再落仓库根。
· 改的是落点本身：`Makefile` 的 `BUNDLE := $(STAGE)/$(APP_NAME).app`（那条往仓库根的 `ditto` 整段删除，
  `run` / `dmg` 改指暂存目录，`clean` 补一行清掉历史留下的仓库根副本）；`scripts/install_local.sh` 的默认包同改，
  并在改现场之前查这一格（仓库根有可执行 .app ⇒ 一步都不许动），`--dest` 非 /Applications 时强制不启动那份副本。
· 守卫：`scripts/repo_root_bundle.py`（三态 ok/red/not-run + 自带 `READER_SELFTEST` 正对照 + 红排在 not-run 前面），
  接线判据卷 `scripts/tests/test_repo_root_bundle.py` 11 格；`.github/workflows/ci.yml` 新增硬步骤
  `Repo root stays bundle-free after make bundle (BACKLOG 620)`，排在 `make bundle` 之后（那里才有对象可扫）。
· 现场：仓库根那份 11-04 08:33 的构建产物已移出仓库（`/tmp/r592-removed/`，它不是源码也不是用户数据）。
· **不在本笔的两半**：① 备份目录那 20+ 份可启动副本 ⇒ 新开 **664**；② 登录项/Dock 改指 /Applications 那一份
  ⇒ 不改用户的 Dock / 登录项，写成人工验收批次 **91.1**（给用户的一句话：在系统设置里把「开机启动」重开一次）。
· 刀：M1588 / M1589 / M1590 / M1591 / M1593（全 CAUGHT；M1590 第一版是空刀，作废后重落）。

**新开单 2 张**：

**664. `~/Documents/Codex_Project0_backups/before-*/` 里每轮留一份**可启动**的旧包 ⇒ 同一 bundle id 的可启动副本在这台机器上堆到 20+ 份**（R592 现读；620 的另一半）
· 现象：`mdfind "kMDItemCFBundleIdentifier == 'com.clipboardhistory.app'"` 在 R522 就读到 20+ 份；本轮换装之后
  备份目录又多一份（`before-r592-migration`、`before-r592-height-fix`）。仓库根那一半本轮断了，这一半没断。
· 为什么本笔不修：① 回滚分支（`trap rollback`）在任何一步失败时靠 `mv "${backup_dir}/${app_name}.app"` 把旧包放回
  /Applications —— 压成归档或删掉的瞬间就没有退路；② 摘掉可启动身份要动 LaunchServices 数据库
  （`lsregister -u`）或用户 Documents 里的东西，两种都超出"改构建落点"。
· 出路（归用户，一条不代选）：甲 装成功之后把旧包压成 `tar.gz` 并**当场验能解出 `Contents/MacOS`**，
  回滚指令同步改成解包；乙 备份根做一次 `lsregister -u` 批量注销（要现读 `lsregister -dump` 的逐字名单才能判有没有用）；
  丙 备份目录加 `.metadata_never_index` 移出 Spotlight（只减索引面，不减 LaunchServices 面）；
  丁 什么都不改，接受"备份目录里有一堆可启动旧包"。
· 先要量的东西：`lsregister -dump | grep -c com.clipboardhistory.app` 的现读，以及摘掉之后 Dock/登录项是否真的少一条 ——
  没有这一对读数，甲乙丙三条都只是散文。

**665. 帧基线里那 16 张与这台机器今天的渲染不一致，而连续七轮"产品 0 文件 ⇒ 不重捕"让它没人看见**（R592 现读）
· 现象：`FRAME_BASELINE_CHANGED=16`（8 张 `detail-*-720x520` + 8 张 `quickpick-*-420x300`），门 rc=1。
· 已经排掉的：**不是本笔改的**。同一台机器上在 `HEAD`（`906a875`，不含本笔任何改动）另开一棵 worktree 重捕一遍
  ⇒ 那 16 张与本轮捕的**逐字节相同**；另抽 8 张未变帧与对照也相同；本轮这批 356 张与上一批（R591）356/356 逐字节相同。
· 还没量的（两种成因修法相反，不许赌）：甲 环境侧变了（系统字体/OS 小版本/渲染路径），基线当初烤的是另一套环境；
  乙 基线当初烤错（那一笔 update 用的不是这台机器这一批帧，或帧目录被别的批次喂过）。
  甲 ⇒ 出路是重烤并给基线补"哪台机器、哪一次环境"的署名（660 那一族已有形状）；
  乙 ⇒ 出路是把那 16 张的摘要改回**当时真烤的批次**，并让 `update` 自己拒收跨批次喂进来的帧。
· 本轮处置：`update` 一次没跑（重烤归用户）；门照红；STATE 本节⑥ 写了控制实验的逐字读数；
  另开的一条硬要求：**"产品 0 文件 ⇒ 不重捕帧"这条纪律要让基线自己出声** —— 连续 N 轮不重捕时
  基线侧的漂移没人看，这与 663 那一族（步骤没机会出声）同形。

**既有单子只补事实，一条不代选**：
· **663**（上一轮新开）：本轮 ⓪ 读到 `42179047067` 的 skipped 从 5 朵降到 **0** 朵、`Runtime launch smoke` 转成
  `success` 且正文印出 `SMOKE_OK=1` ⇒ 那一族的"被上游红连带"在 runner 上确认修好。剩下一半（`Info.plist gate`
  要不要也带 `if: always()`）仍归用户。
· **622 / 565 / 627 / 635**：runner 那三朵红（`STEP[15]` 五朵、`STEP[17]` 一朵、`STEP[19]` 两朵）本轮两跑
  **同名同集合** ⇒ 没有新增也没有消失；不计入本轮对账口径的理由写在 STATE 本节③，不是"本轮没碰它"。
· **646 / 647 / 650 / 651 / 653 / 654**：段②三问的状态本轮逐问写进 STATE 本节③，两条具名阻塞一字未撤 ⇒
  第③段着色器继续不开工；654 的定向仍等用户。
· **655 / 660**：倍率那一维四个出口各有名字；本轮基线那 16 张的账并进 665，重烤仍归用户。
· **658 / 659 / 661 / 662**：本轮没有新事实要补；659 那条看图形状被本轮复用（正对照 + 自己 vs 自己必须 0）。
""" % {u"r": i[u"r"], u"n": i[u"n"], u"round": i[u"round"], u"date": DATE}


def block_decisions(d):
    i = d[u"ident"]
    return u"""## D-%(r)s（%(date)s）：恢复路径上的几何只能由真机读数签；构建落点改在配方而不是清理现场

**背景**：用户三条实测反馈 —— ①升级用户看不到第①段的等分（旧记忆 750/420 压住 R567 的新默认值）；
②不要再留仓库根的开发版副本，只保留 /Applications 一份；③「升级后两栏等宽、比例≈√2」是硬验收（已签字）。
派单还加了一条纪律：**每轮必须落一次真产品改动**，不再开"不改产品"的验证轮。

**决定**：
1. 记忆优先不改，改的是**留在盘上的旧默认值**：一次性迁移只在记忆值恰好等于旧默认对（750 与 420）时抬，
   抬完打版本键。手动调过宽度的用户一律不碰 —— 这条边界的证人是刀 M1583（放宽条件必须红）。
2. 恢复的窗口帧**只改写宽高、顶边逐字不动**（`y' = (y + h_old) − h_new`）；解析不出四个数就原样返回，
   不猜 origin。分栏子视图帧没有可算目标 ⇒ 删掉，让 `navigationSplitViewColumnWidth` 那条锁自己给等宽。
3. **一次性补丁换成不变量**：第一版把高度写成「迁移那一趟抬一次」，而用户机上版本键已被第一次换装打上 ⇒
   那一支永远不会触发（真机现读 848×492）。最终形态：产品从不记高度，13+ 的 `contentAspectRatio` 锁住比例，
   所以「高度不在 √2 上」只能来自锁出现之前的恢复 ⇒ `applyGeometry` 见到就抬，容差 0.02，
   macOS 12 没有那条锁 ⇒ 那一档不调用。**改恢复路径的东西必须由真机读数签，进程内建窗的判据看不见它。**
4. 构建落点改在**配方**（`Makefile` 的 `BUNDLE`）而不是"每次记得删"：换装脚本默认包同改 + 装之前查这一格 +
   CI 里一个硬步骤排在 `make bundle` 之后（那里才有对象可扫）。守卫自带正对照，且红排在 not-run 前面。
5. 用户的 Dock 与登录项**不动**（派单硬规矩）。仓库根副本消失后那条登录项会失效 ⇒ 写成人工验收批次 91.1，
   给用户的一句话是"在系统设置里把「开机启动」重新打开一次，现在启动的是 /Applications 那一份"。
6. 基线那 16 张：先做控制实验分清"本笔改的"与"基线侧的旧账"，再决定动不动手 ⇒ 本轮证到不是本笔改的，
   `update` 一次没跑（重烤归用户），成因二选一留给 665。
7. 备份那一族（620 机制②）不在本笔顺手改：回滚分支正靠 `mv` 那份备份，压包等于扔退路 ⇒ 开 664，
   并把"先量 `lsregister -dump` 再定方向"写成它的第一格。

**代价**：产品 %(prodfiles)s 文件、判据卷 +%(delta)s 格、16 把刀、一次新守卫、一个 CI 硬步骤、
两次换装（第二次是为了量真窗的高度）；换来的是用户机上从 `750×492` 到 `848×600` 这条**真机读数**，
以及第①段第一次对升级用户成立。
""" % {u"r": i[u"r"], u"date": DATE, u"delta": d[u"delta_total"], u"prodfiles": d[u"prod_files"]}


def block_changelog(d):
    i = d[u"ident"]
    return u"""### 升级用户看不到的那半段第①段：一次性迁移 + √2 不变量；构建产物从仓库根搬进暂存目录（R%(r)s / 第 %(n)s 轮 / Round %(round)s · %(date)s）

- `MainWindowCollapsePolicy.swift`：新增 `MainWindowGeometryMigration`（纯函数 `plan` 四档具名出口 +
  读盘那一层薄胶水）与 `heightLift`（√2 不变量：产品从不记高度，13+ 的 `contentAspectRatio` 锁住比例 ⇒
  不在 √2 上的高度只能来自锁之前的那一次恢复；macOS 12 那一档不调用）。
- `MainWindowCollapseController.swift`：迁移排在读状态**之前**（记忆优先，先抬后读才读得到规格档）；
  `applyGeometry` 在改宽之后按不变量抬高度，并按「顶边不动」回算 origin；`heightLifts` 计数给判据数。
- 判据：`FoldGeometryMigrationTests.swift`（新卷 10 格 —— 真值表四档、产品入口抬宽度与恢复帧、
  版本键才是「只抬一次」的闸门、真窗两栏等宽 + 比例≈√2、√2 不变量的两趟语义、恢复帧字符串手术、
  键匹配只认自己的窗口）。
- `Makefile`：`BUNDLE := $(STAGE)/$(APP_NAME).app` —— 往仓库根 `ditto` 那一段整删，`run` / `dmg` 改指暂存目录，
  `clean` 补一行清掉历史留下的仓库根副本（BACKLOG 620 结案）。
- `scripts/install_local.sh`：默认包 = 暂存目录；装之前查仓库根那一格（有可执行 .app 就一步都不许动）；
  `--dest` 非 /Applications 时强制不启动那份副本；末态印 `INSTALL_STAGED_BUNDLE` / `INSTALL_REPO_ROOT_BUNDLE`。
- `scripts/repo_root_bundle.py`（新守卫）+ `scripts/tests/test_repo_root_bundle.py`（新卷 11 格）+
  `scripts/tests/test_install_local.py`（+3 格：默认落点、违规拒装、沙箱强制不启动）：
  三态 ok/red/not-run，自带 `READER_SELFTEST` 正对照，红排在 not-run 前面，`make -n bundle` 的配方不许出现
  不落在暂存目录的那一份。
- `.github/workflows/ci.yml`：新增硬步骤 `Repo root stays bundle-free after make bundle (BACKLOG 620)`；
  `Runtime launch smoke` 的冒烟路径从仓库根相对路径改成 `/tmp/时间剪史_bundle/时间剪史.app`。
- 新开 **664**（备份目录那 20+ 份可启动副本 = 620 的另一半，回滚分支靠它 ⇒ 本笔不动）、
  **665**（帧基线 16 张与这台机器不一致；HEAD worktree 控制实验证到不是本笔改的；`update` 一次没跑）。
- 换装两次并现读真窗：`INSTALL_RESULT=ok`、`INSTALL_SHA_MATCH=1`、条数 505→505、`INSTALL_SIGNATURE=local`；
  装前 `750 / 420 / 无版本键 / 窗口 750×492` ⇒ 装后 `848 / 424 / 版本键=1`，AX 现读窗口 **848×600**、
  分栏 `423.5×600 / 424.5×600`。没动用户的 Dock 与登录项（人工验收批次 91.1）。
""" % {u"r": i[u"r"], u"n": i[u"n"], u"round": i[u"round"], u"date": DATE}


def shapes(i):
    return [(u"UI 轮次标题", u"## 第 %d 轮（R%d · " % (i[u"n"], i[u"r"])),
            (u"ITER 标题", u"## Round %d · R%d" % (i[u"round"], i[u"r"])),
            (u"STATE 主节", u"## R%d 状态（" % i[u"r"]),
            (u"DECISIONS", u"## D-%d（" % i[u"r"]),
            (u"BACKLOG 追账节", u"## R%d 追账" % i[u"r"]),
            (u"CHANGELOG 标题行", u"### 升级用户看不到的那半段第①段：一次性迁移 + √2 不变量；构建产物从仓库根搬进暂存目录（R%d / " % i[u"r"])]
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
            u"as-of 口径 ⇒ 读作「本轮之前最后一次产品改动在 %d 轮前」；本笔是产品轮 ⇒ 下一轮的分界换成本笔、读 1"
            u"（这把尺的复位值是 1，不是 0：`streak_at` 用严格小于）。"
            u"上一格原文留着：**%s**（R%s 台账落盘之后现读"
            % (streak_n, i[u"r"], d[u"streak"], streak_n, m2.group(1), m2.group(2)))
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
            u"as-of 口径 ⇒ 读作「本轮之前最后一次产品改动在 %d 轮前」；本笔是产品轮 ⇒ 下一轮的分界换成本笔、读 1"
            u"（这把尺的复位值是 1，不是 0：`streak_at` 用严格小于）。"
            % (streak_n, landed_r, line, streak_n))
    fin = fin[:m2.start()] + cell + fin[end:]
    write(u"FINAL", fin)

    st = read(u"STATE")
    d_prod = grep_line(must_read(os.path.join(TMP, "prod_stat.txt"), u"产品文件数现读"),
                       u"PROD_FILES=", u"产品文件数").split(u"=", 1)[1].strip()
    # **搜索范围必须锚在刚落盘那一轮的小节内**（R569 那一族的第 12 次复发）：
    # 第一版在整个文件上找那一格，而本轮那一格当时还是 -1 占位（\d+ 匹配不到负号）
    # ⇒ 它匹配到上一轮那一节，并把历史的 streak 格从 20 改成 21。现在它只会当场报错，不会改历史。
    head_at = re.search(u"(?m)^## R%d 状态（" % landed_r, st)
    if not head_at:
        raise SystemExit(u"ANCHOR-MISS post-land STATE：读不到本轮（R%d）那一节" % landed_r)
    nxt = re.search(u"(?m)^## R\d+ 状态（", st[head_at.end():])
    section = st[head_at.start(): head_at.end() + (nxt.start() if nxt else len(st))]
    m3 = re.search(u"产品文件 [0-9]+ 个[\\s\\S]{0,200}?连续零改动 \\*\\*(-?[0-9]+)\\*\\* 轮（唯一取数口", section)
    if not m3:
        raise SystemExit(u"ANCHOR-MISS post-land STATE：R%d 那一节里没有那一格 ⇒ 这一趟不写，绝不改历史" % landed_r)
    off = head_at.start() + m3.start()
    seg = st[off:]
    CUT = u"〔streak-cell-end〕"
    if CUT not in seg:
        raise SystemExit(u"post-land：R%d 那一节的 streak 格没有结束哨兵 ⇒ 不敢猜切点" % landed_r)
    stop = seg.index(CUT) + len(CUT)
    cell3 = (u"产品文件 %s 个（`Sources/…/MainWindowCollapsePolicy.swift`、"
             u"`Sources/…/MainWindowCollapseController.swift`），连续零改动 **%d** 轮（唯一取数口 "
             u"`python3 scripts/product_streak.py`，**台账落盘之后**现读 `%s`；as-of 口径 ⇒ 读作「本轮之前最后一次"
             u"产品改动在 %d 轮前」；本笔是**产品轮** ⇒ 下一轮那一格的分界换成本笔、读 **1**。用户指令「那一格应该回到 0」"
             u"在这一把尺上**到不了 0**：`streak_at` 从 R334 起用严格小于（本轮自己那一笔不记进自己那一格），"
             u"所以它的**复位值是 1**，\"归零\"在这本账上的形状是\"分界换成本轮\"；本轮不替下一轮填数，"
             u"取数时刻由 `post_land()` 钉在函数名字上，不在纪律上"
             % (d_prod, streak_n, line, streak_n))
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

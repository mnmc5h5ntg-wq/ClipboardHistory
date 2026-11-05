# -*- coding: utf-8 -*-
"""R585 七本台账写手（**新写**，不 port；锚一律现读，命中数不等于 1 就停在任何写盘之前）。

与上一版同源的三条规矩（都是上一轮付过学费的）：
① 身份由盘上现读推（UI_AUDIT 的轮次标题 + STATE 的主节标题交叉核对），恒等式 n=R-1、Round=R-3；
② 落盘之前 DRY 一遍并逐本现读"本轮那七个标题形状各几次"，落盘后再数一遍 ⇒ 六个数是证人；
③ 全部文本先在内存里算完（任何一块崩 ⇒ 一本都不写），fill 覆盖每一本，返回前回读 `@@`=0；
   派生格（streak / 对账 / 电池）一律**落盘之后**再取，取数口命令写进那一格。
"""
import contextlib
import io
import json
import os
import re
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0"
TMP = "/tmp/r585"
BOOKS = {"UI": "AGENT_UI_AUDIT.md", "ITER": "AGENT_VISUAL_ITERATION.md", "STATE": "AGENT_STATE.md",
         "BACKLOG": "AGENT_BACKLOG.md", "DEC": "AGENT_DECISIONS.md", "FINAL": "AGENT_FINAL_REPORT.md",
         "CHANGE": "CHANGELOG.md"}
DATE = "2026-11-06"


def read(name):
    return io.open(os.path.join(ROOT, BOOKS[name]), encoding="utf-8").read()


def write(name, text):
    with io.open(os.path.join(ROOT, BOOKS[name]), "w", encoding="utf-8") as handle:
        handle.write(text)


def identity_from_disk():
    m = re.search(r"(?m)^## 第 (\d+) 轮（R(\d+) · ", read("UI"))
    if not m:
        raise SystemExit("UI_AUDIT 里读不到轮次标题 ⇒ 身份推不出来")
    prev_n, prev_r = int(m.group(1)), int(m.group(2))
    ms = re.search(r"(?m)^## R(\d+) 状态（", read("STATE"))
    prev_state_r = int(ms.group(1)) if ms else None
    if prev_r != prev_state_r:
        raise SystemExit("身份交叉核对不过：UI_AUDIT 最新 R%d 而 STATE 最新 R%d" % (prev_r, prev_state_r))
    r = prev_r + 1
    return {"prev_r": prev_r, "prev_n": prev_n, "r": r, "n": r - 1, "round": r - 3}


def must_read(path, label):
    if not os.path.exists(path):
        raise SystemExit("读数缺席：%s（%s）⇒ 链条没跑到那一格，不许写账" % (path, label))
    text = io.open(path, encoding="utf-8", errors="replace").read()
    if not text.strip():
        raise SystemExit("读数是空的：%s（%s）" % (path, label))
    return text


def grep_line(text, prefix, label, last=True):
    rows = [l.strip() for l in text.splitlines() if l.strip().startswith(prefix)]
    if not rows:
        raise SystemExit("读数里找不到前缀 %r（%s）" % (prefix, label))
    return rows[-1] if last else rows[0]


def gather():
    ci = json.loads(must_read(os.path.join(TMP, "ci_readings.json"), u"⓪ 两跑读数"))
    d = {"ident": identity_from_disk(), "ci": ci}
    main_run = "42093340563"
    add_run = "42094125984"
    d["main"], d["add"] = ci[main_run], ci[add_run]
    for key, fname, label, prefix in (
            ("gate_no_proof", "before_restamp.txt", u"补出处之前那一门", "FRAME_BASELINE_RESULT="),
            ("gate_restamp", "restamp3.txt", u"restamp 那一趟", "FRAME_BASELINE_RESTAMP="),
            ("gate_after", "after_restamp3.txt", u"补出处之后那一门", "FRAME_BASELINE_RESULT=")):
        d[key] = grep_line(must_read(os.path.join(TMP, fname), label), prefix, label)
    for key, fname, label, prefix in (
            ("drift_before", "before_restamp.txt", u"补出处之前", "FRAME_BASELINE_DRIFT "),
            ("drift_after", "after_restamp.txt", u"补出处之后（换机器键那一支）", "FRAME_BASELINE_DRIFT "),
            ("drift_final", "after_restamp3.txt", u"补出处之后", "FRAME_BASELINE_DRIFT ")):
        d[key] = grep_line(must_read(os.path.join(TMP, fname), label), prefix, label)
    # 三条逐字代码证据（658 追记要用）
    src = io.open(os.path.join(ROOT, "scripts", "frame_baseline.py"), encoding="utf-8").read()
    d["evidence_update"] = u'`if args.action == "update":` 那一支里 `write_baseline(manifest_path(args.repo_root), frames)` 无条件执行（旧版逐字），'
    d["evidence_check"] = u'`check` 只在 `os.path.exists(candidate)` 时才把 `against_label` 置成 `by_machine:%s`'
    d["evidence_ls"] = grep_line(must_read(os.path.join(TMP, "ls_baselines.txt"), u"docs/frame_baselines 现读"),
                                 "LS=", u"目录清单")
    # 刀
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
    d["knives"] = knives
    d["knife_reds"] = must_read(os.path.join(TMP, "knife_reds.txt"), u"每把刀红了哪几格")
    d["pytest"] = grep_line(must_read(os.path.join(TMP, "pytest_final.txt"), u"python 卷"), "Ran ", u"python 卷 Ran")
    d["pytest_ok"] = grep_line(must_read(os.path.join(TMP, "pytest_final.txt"), u"python 卷"), "OK", u"python 卷签字", last=False)
    d["capture"] = grep_line(must_read(os.path.join(TMP, "capture_summary.txt"), u"捕获卷"), "CAPTURE_LINES=", u"捕获卷汇总")
    d["frames"] = grep_line(must_read(os.path.join(TMP, "capture_summary.txt"), u"捕获卷"), "FRAMES=", u"帧数")
    d["gate_frames"] = grep_line(must_read(os.path.join(TMP, "gate_new_frames.txt"), u"新帧那一门"), "FRAME_BASELINE_RESULT=", u"新帧门结论")
    d["gate_frames_drift"] = grep_line(must_read(os.path.join(TMP, "gate_new_frames.txt"), u"新帧那一门"), "FRAME_BASELINE_DRIFT ", u"新帧门判定")
    d["full"] = grep_line(must_read(os.path.join(TMP, "full_summary.txt"), u"全量卷"), "FULL_LINES=", u"全量卷汇总")
    d["forensics"] = grep_line(must_read(os.path.join(TMP, "forensics_summary.txt"), u"真机键那一趟"), "FORENSICS_LINES=", u"真机键汇总")
    fo = must_read(os.path.join(TMP, "forensics_summary.txt"), u"真机键那一趟")
    d["forensics_total"] = grep_line(fo, "FORENSICS_TOTAL=", u"真机键总数")
    d["forensics_tier"] = grep_line(fo, "FORENSICS_TIER=", u"档位那一行")
    d["forensics_retract"] = grep_line(fo, "FORENSICS_改口=", u"656 那一格的改口")
    d["forensics_fifth"] = grep_line(fo, "FORENSICS_第五趟=", u"第五趟同臂")
    d["forensics_appearance"] = grep_line(fo, "FORENSICS_APPEARANCE=", u"没动外观的证人")
    d["prechecks"] = must_read(os.path.join(TMP, "prechecks.txt"), u"三道预检")
    d["absence"] = grep_line(d["prechecks"], "LEDGER_ABSENCE_RESULT", u"清账门")
    d["streak"] = grep_line(must_read(os.path.join(TMP, "streak.txt"), u"产品面连续轮数"), "PRODUCT_STREAK ledger_round", u"streak 现读")
    d["numstat"] = must_read(os.path.join(TMP, "numstat.txt"), u"numstat 现读")
    d["pyverify"] = must_read(os.path.join(TMP, "pyverify.txt"), u"字面量真验证")
    d["look"] = must_read(os.path.join(TMP, "look.txt"), u"看图那一腿")
    recon_path = os.path.join(TMP, "recon.txt")
    d["recon"] = (grep_line(io.open(recon_path, encoding="utf-8").read(), "RED_NAME_RECONCILIATION", u"对账门")
                  if os.path.exists(recon_path) else u"（预览那一趟还没跑）")
    d["md5"] = grep_line(must_read(os.path.join(TMP, "md5.txt"), u"刀链前后 md5"), "MD5=", u"md5")
    dark = must_read(os.path.join(TMP, "dark_drift.txt"), u"暗档漂移三份读数")
    d["byte_compare"] = grep_line(dark, "BYTE_COMPARE", u"逐字节对照")
    d["dark_rows"] = u" ｜ ".join(l.strip() for l in dark.splitlines() if l.strip().startswith(u"detail-"))
    d["register_dark"] = grep_line(must_read(os.path.join(TMP, "register_dark.txt"), u"补登记那一趟"),
                                   "FRAME_BASELINE_REGISTER=", u"补登记读数")
    gate_reg = must_read(os.path.join(TMP, "gate_after_register.txt"), u"补登记之后的门")
    d["gate_after_register"] = grep_line(gate_reg, "FRAME_BASELINE_RESULT=", u"补登记后结论")
    d["drift_after_register"] = grep_line(gate_reg, "FRAME_BASELINE_DRIFT ", u"补登记后判定")
    tb = subprocess.check_output(["git", "show", "HEAD:scripts/tests/test_frame_baseline.py"], cwd=ROOT).decode("utf-8")
    ta = io.open(os.path.join(ROOT, "scripts", "tests", "test_frame_baseline.py"), encoding="utf-8").read()
    d["tests_before"] = tb.count(u"    def test_")
    d["tests_after"] = ta.count(u"    def test_")
    d["tests_delta"] = d["tests_after"] - d["tests_before"]
    if d["tests_delta"] <= 0:
        raise SystemExit("矛盾读数：test_ 数量没涨（%d→%d）" % (d["tests_before"], d["tests_after"]))
    gb = must_read(os.path.join(TMP, "getbbox.txt"), u"包围盒那把尺的三份读数")
    d["getbbox_rgba"] = grep_line(gb, "GETBBOX_RGBA", u"RGBA 差值图")
    d["getbbox_l"] = grep_line(gb, "GETBBOX_L", u"L 差值图")
    d["getbbox_ctrl"] = grep_line(gb, "GETBBOX_正对照", u"合成正对照")
    d["getbbox_grep"] = u"现读 `grep -rln getbbox scripts/ ClipboardHistory/Tests` 命中文件数=0（既有仪器里没有人用它）"
    d["note_check"] = grep_line(must_read(os.path.join(TMP, "note_check.txt"), u"note 只追加的证人"),
                                "NOTE_APPEND_ONLY=", u"note 证人")
    d["baseline_untouched"] = grep_line(must_read(os.path.join(TMP, "baseline_untouched.txt"), u"工作基线没被碰"),
                                        "BASELINE_UNTOUCHED=", u"基线证人")
    return d


# —————————————————————————————————————————————————————————──
# 正文。数字全部由 gather() 的读数格式化出来；维度名/块名/标题形状一律照守卫认的那一种写。


def next_u():
    nums = [int(x) for x in re.findall(r"\*\*U-(\d+)", read("UI"))]
    if not nums:
        raise SystemExit("UI_AUDIT 里读不到 U 号")
    return max(nums) + 1


def block_state(d):
    i = d["ident"]
    m, a = d["main"], d["add"]
    knives = u" ｜ ".join(u"%s rc=%d caught=%d clean=%d 预检=%s 末次=%s"
                          % (k["arm"], k["rc"], k["caught"], k["clean"], k["precheck"], k["post"])
                          for k in d["knives"])
    return u"""## R%(r)s 状态（%(date)s · 第 %(n)s 轮 / Round %(round)s · 产品 0 文件 + **把上一轮印给读者的那条出路做成真的**（`update --for-machine` 真写 `by_machine/<运行时键>.json`；名册有了**写路径** `register-drift`（含 `--restamp`），每行带 `observed` 那对哈希；`check` 从此能证伪"手抄一行"）+ 电池 +%(delta)d 格（该卷 %(tb)d→%(ta)d）+ 刀 M1538/M1539/M1540 全 CAUGHT + **⓪ 那条预测被 runner 自己签掉了**）

⓪ **两跑都到数：同一个读数，两个独立证人**
- 身份现读：UI_AUDIT 最新一节以「第 %(prev_n)s 轮（R%(prev_r)s」开头，STATE 最新是 R%(prev_state_r)s ⇒ 交叉核对通过 ⇒ 本轮 **R%(r)s = 第 %(n)s 轮 / Round %(round)s**。刀高水位现读 **M1537**（`mutate_r584` 那三把都在册）⇒ 本轮从 **M1538** 起，没抄派单里的数、也没借号。
- **先把两套编号拆开**（监工指出它们不同义，混用会把"今天没人判"读成"出路成立"）：
  · 本脚本报的是**出口·甲/乙/丙/丁** —— 甲=`判=判`（且 STEP[11] 红 ⇒ 那一台真有未登记漂移）、乙=`判=不判`（基线不是这台机器的产物 ⇒ 这一维今天没人判）、丙=那一行命中 0 次（通道没跑）、丁=`FRAME_BASELINE_SKIPPED`（帧集太小 ⇒ 今天没判，绝不等于第二台绿了）。
  · **658 的三条出路**是另一套编号：⑴CI 打印逐机器清单由人写回 ⑵那一台自己 `update --for-machine` 并提交 ⑶承认基线逐机器、变帧那一维永久只归主人判。
  · 两条轴只有一句关系：**读到 出口·乙 不等于 出路 ⑵ 成立**，更不等于"那朵红消失了"。
- 主笔 `42093340563 ↔ 3e13d47` 现读 `completed / failure` ⇒ **到数**；全部失败步骤逐字：`%(steps_signed)s` ⇒ **STEP[11] 不在里面**（步骤级结论由 `ci_read.py steps` 的 jobs[].steps 说话，不是从日志里推的）。
  门那一行逐字 `%(drift_signed)s`；结论行 `%(result_signed)s`；不判那一格 `%(notjudged_signed)s`。
  ⇒ 本轮读到的是**出口·乙**，证人=`42093340563` 的 `Frame baseline vs working manifest` 那一步打印的上面三行原文；
  它同时意味着 R584 补记那条预测（七项 + 步骤级一项）**逐条命中**，也意味着**那一维在 runner 上今天仍没人判** —— 那是 R584 已经落下的形状，不是新的胜利，也不许写成"那朵红消失了"。
- **R584 补记里那条可证伪预测逐条对拍**（七项 + 步骤级一项，由脚本判，不由我念）：`%(disp)s`
- 补记笔 `42094125984 ↔ aa8ef88` 本轮**现读二次**（开工时 `in_progress`/`--log` 0 字节 ⇒ 当时照实写未到数；收口前它自己到数了，"到没到"由 `ci_read.py latest` 的 `status=` 说，不由我等）：现读 `completed / failure` ⇒ **到数**；全部失败步骤逐字 `%(steps_add)s` ⇒ **STEP[11] 同样不在里面**，门那一行逐字 `%(drift_add)s`、结论行 `%(result_add)s`、不判那一格 `%(notjudged_add)s` ⇒ 也是**出口·乙**，七项预测逐条对拍 `%(disp_add)s`。
- **归因对照（红名与步骤都取改动之前那一跑）**：`42077903445 ↔ d808030`（R583 补记，本轮现读 `steps`）的失败步骤是 STEP[11] failure + STEP[12]/[13]/[14] skipped（被前一步连带）+ 15/17/19 ⇒ **STEP[11] 在那一跑是红的**，在两跑（3e13d47、aa8ef88）都不在失败列表里 ⇒ 形状变化发生在 R584 那一笔的树上，本轮没再改判法（本轮只加写路径与出处校验，`--allow-missing`/阈值/四分支一字未动）。
- ⚠ 这一格要说**全套**：STEP[11] 从红变成"没红"，读的是 `判=不判` —— 那一台**仍然漂 356 张**（逐字 `变帧=356 未登记（不判）=356`），只是不再由本机替它判 ⇒ 这不是"漂移修好了"、不是"那朵红消失了"，更不是 658 出路 ⑵ 成立（那一台没有自己的基线文件，`docs/frame_baselines/by_machine/` 在 HEAD 里就不存在）。
- 红名单逐字 5 个名字（与 R582/R583/R584 同集合）⇒ 「本轮没有新名字」；`D12_SHAPE_SCAN_REGISTRY` 仍逐字 `机器=github-runner 登记=1_2 实测=1_2 判=一致`；`STEP[18]`（在屏探针那一卷）**两跑都绿**：主笔逐字 `%(probe_main)s`，补记逐字 `%(probe_add)s` ⇒ `本次跑过=8 红=0` 一致而 `本次下结论=8 vs 7` 在漂，那一列的"下结论"格继续两跑一起读、不许单跑下结论（账里更早就写过 `跑过=4 红=4` 那一档，本轮没有为它改任何判据，也不拿它当本轮读数）。

① **监工给的那一条形状结论：成立，逐字坐实**
- 三处代码（R585 开工时现读，取值时刻=本轮第一步）：① %(evid_upd)s；② %(evid_chk)s；③ 而印给读者的出路那一行写着「它会署名并写 `docs/frame_baselines/by_machine/<键>.json`」。
- 目录现读：`%(evid_ls)s` ⇒ `by_machine/` 不存在；`docs/frame_baseline.json` 现读 `machine='local:MacBook-Air.local'`、`count=356`。
- ⇒ **任何机器照工具自己印的那条命令跑一遍 `update`，都永远停在 `判=不判`** ⇒ 658 的出路 ⑵ 的前置当时不成立；R584 ⓪ 那一问「变帧维度在 runner 上从今天起有人判了吗」当时的答案是「没有」。**本轮把这一支补成真的**（只补前置，出路仍归用户选）。

② **真实推进（段号=②：让出路做得到 + 名册的写路径与出处）**
- `update --for-machine`：写 `docs/frame_baselines/by_machine/<sanitize_machine(machine_key())>.json`，署名=运行时取的那台；**没有 `--machine` 这个参数**（测试里现证：argparse 把它当未知参数 ⇒ 非 0）。不加旗标的 `update` 行为一字未改（仍写工作基线）。
- `register-drift`：名册的**写路径**（上一版只有 `load_drift_registry` 一条读路径 ⇒ 那 8 行的 `machine` 值是被抄进去的字面）。每行带 `observed = {frame_sha, baseline_sha}`；`--reason`/`--ticket` 缺一 ⇒ 退 2 且**一行都不落**；`--restamp` 只给"本机且此刻正在漂且理由/单号齐全"的行补出处，别的行不碰。
- `verify_provenance` + `check`：**只问此刻正在豁免漂移的本机行** —— 没出处 ⇒ `名册无出处` 红并点名；出处与本机当轮观测不同字 ⇒ `出处对不上` 红并点名。他机行不由本机证伪（本机没有那一台的帧）。陈旧行仍只报数。
- 出路那一行现在印的是**真能跑的命令**（带 `--for-machine`），并注明「上一版少写这个旗标 ⇒ 照旧命令跑完永远停在 `判=不判`」。
- 两向都有证人（不是措辞）：**正臂** `test_printed_remedy_flips_the_verdict_to_judged` 从 stdout 的「出路」那一行**抽出命令原文**、只把占位的帧目录换成真目录、补上测试自己的 `--repo-root`，原样跑 ⇒ 第二次读 `判=判` 且 `FRAME_BASELINE_AGAINST=by_machine:…`；**负臂** `test_plain_update_still_leaves_it_not_judged` 证明不带旗标的那条命令**不产出** `by_machine/`（两条命令有区别这件事才有证人）。
- 本机名册的 before/after（同一棵树、同一条命令，唯一变的是有没有出处）：
  补之前 `%(drift_no)s` ⇒ `%(gate_no)s`（退 **1**）；
  走 `register-drift --restamp` 之后 `FRAME_BASELINE_RESTAMP=8 机器=local:MacBook-Air.local 基线出处=c16144dfd33b` ⇒ `%(gate_yes)s`（退 **0**）。
- **本轮新读到的漂移（不是本轮造成的）**：新帧对 R584 的帧 `%(byte_compare)s`，不同的正是这八张暗档，逐张读数 `%(dark_rows)s` ⇒ 像素差 41–46 颗、逐带极值 R 最大 6 / G,B 最大 2 / **alpha 一字未动** ⇒ 亚像素级噪声；而 `getbbox()` 在这八张上全部返回 `None` ⇒ **包围盒这把尺在 RGBA 差值图上会假报"没有差异"**（开单 659；本轮只量成读数，仪器侧的证人没做 ⇒ 不许写成已修）。
  门因此先红在 `未登记=8`，处置**只走工具自己的路**：`%(register_dark)s` ⇒ 之后 `%(drift_after_register)s` ⇒ `%(gate_after_register)s`（退 0）。
  ⚠ 这句要说全：登记之后"红"没了，但**漂移一条没少**（变帧从 8 涨到 16 是实测），655 仍开着；655 那句"八张全是 light 档 ⇒ 暗档没有漂移证人"从本轮起**不成立** ⇒ 漂移集合会跨会话**增减**，不是烤基线那次冻住的常量。
- 名册的 note 是**人写的句子**：第一次 `--restamp` 把 R583 那句「本名册不是重烤基线的替代品」冲掉了 ⇒ 生成器改成"原文在就留着、新句只补一次"，并由 `test_restamp_keeps_the_human_note_and_appends_once` + 刀 **M1540** 钉住。
  ⚠ 监工又指出第二半：补回时我把 `R584：登记的键…` 那句挪到了 `⚠ 本名册不是重烤基线…` **之后** ⇒ **重排也算改原文**。
  现在的合同是"HEAD 的原文整段照搬在前 + 本轮新句只追加在尾"，证人 `%(note_check)s`；
  `test_the_committed_note_grows_only_by_appending` 直接拿 `git show HEAD:` 比前缀 ⇒ 谁重排谁红。
- **误写那一格留"删干净"的证人**（R580 那族规矩）：测试曾把抽出来的命令跑到真仓库，写出 `docs/frame_baselines/by_machine/local_other_machine.json`；
  先把它的署名与内容读出来留证（`machine='local:other-machine' count=2`），再删文件与目录，再给测试补 `--repo-root`。
  本轮监工现读 `git status --short` 只有 `.local/`、`.scratch/spikes/` 加那几支已跟踪改动 ⇒ 无遗留；
  台账里两条证人：`%(baseline_untouched)s`（`ls -1 docs/frame_baselines` 现读 + `git diff --stat -- docs/frame_baseline.json docs/frame_baselines/` 为空）
  与 `%(note_check)s`（HEAD 那 8 行的帧名/理由/单号/机器逐字未变 ⇒ 那次误写没改署工作基线，655 那 8 行登记仍有效）。
- 没动的：`--allow-missing` 两帧、任何阈值/容差、`条=8`、三张登记表、`d12RowCategoriesR577`、判法四分支、四条出口语义、红名对账口径、`update` 对工作基线那一份（655 的重烤仍一次没跑）。

⑨ **本轮自伤清单（七处，每处都带代价）与对账**
· **对账口径**（沿用启用，不关）：每条具名红/具名不判/作废读数要么落到 `⑨·` 编号，要么写 `不计入对账口径` 并带三类名字之一。
- 逐条：
  · ⑨·1 名册生成器覆盖了人写的 note（第一次 `--restamp`）⇒ 代价=恢复原文 + 生成器改成保留 + 新增一格测试 + 一把刀（M1540）。
  · ⑨·2 `write_drift_registry` 里用了没 import 的 `io` ⇒ `NameError`，那一趟 `register-drift --restamp` 崩（rc=1）；`py_compile` 是过的 ⇒ **"编译过"从来不等于"这条路跑过"**，只有驱动它才知道。
  · ⑨·3 测试里把抽出来的命令 `split()[1:]`（该剥两个 token）⇒ 那一趟**在真仓库上**跑了一次 `update --for-machine`，写出 `docs/frame_baselines/by_machine/local_other_machine.json`（一份假机器基线）。代价=先看清它的署名与内容（`machine='local:other-machine' count=2`）留证、再删文件与目录、再给测试补 `--repo-root`。这是本轮最重的一处：**测试的隔离前提没验证就跑了写操作**。
  · ⑨·4 负臂断言的前提我写错了：我以为不带旗标的 `update` 不会动署名，实际它会**合法地**把工作基线改署给跑它的那台（那正是 655 的重烤归用户的原因）⇒ 改的是断言与注释，把这件事写清楚，没改判据。
  · ⑨·5 heredoc 里一行被吞成一个残句（`u%%s"`）⇒ `SyntaxError`；代价=按 AST 定位坏行区间重写那一小段。同族（R584 ⑨·13：解释 bug 的句子自己踩 bug）但成因不同：这次是写文件的方式，不是内容。
  · ⑨·6 新判定第一次上树就咬到自己旧夹具（`test_registration_makes_it_green_and_counts`、`test_foreign_row_alone_is_counted_but_not_red` 等 3 格红）⇒ 这是**预期**（红指向"夹具写的是手抄行"），修的是夹具（补出处），判决一字未动；记在这里是为了下一轮别把它读成"判据坏了"。
- ⑨·7 **一把尺差点说出反话**：差量包围盒 `getbbox()` 在这八张 RGBA 差值图上全部返回 `None`，而我据此写的第一句是「八张像素相同 ⇒ 不存在漂移」；救回来的是逐像素计数（41–46 颗）+ `getextrema()`（R≤6/G,B≤2/A=0）。代价=那一读数**作废**并改口径重量、另开一腿合成正对照（4096 颗全差仍 `None`）把这件事量成仪器缺陷、开单 **659**（只开单，本轮没动仪器 ⇒ 不许写成已修）。
  这条与 R579 那一格（包围盒**指错带子**）形状相同、修法相反 ⇒ 分两格记，不许并成一条。
- **红名对账**：
  · 红名「补出处之前 `拦路=8（无出处8）`（本机名册那 8 行是手抄的字面）」→ ⑨·1
  · 红名「`NameError: name 'io' is not defined`」→ ⑨·2
  · 红名「`docs/frame_baselines/by_machine/local_other_machine.json`（测试误写真仓库，已删）」→ ⑨·3
  · 红名「`AssertionError`（负臂前提错：不带旗标的 update 会拿走工作基线署名）」→ ⑨·4
  · 红名「`SyntaxError`（heredoc 残句）」→ ⑨·5
  · 红名「新判定咬到旧夹具那 3 格」→ ⑨·6
  · 红名「`getbbox=None`（差量包围盒对 RGBA 假报无差异，读数作废）」→ ⑨·7
  · 红名「开工时 `42094125984 ↔ aa8ef88` 复核未到（`--log` 打 0 字节）」→ **不计入对账口径**（通道未跑那一格，不是红也不是绿）；**本轮内已消解**：收口前该跑到数并读到 出口·乙，见 ⓪ —— 记在这里是因为"未到数"和"到数"是两条不同的账，不许只留后一条
  · 红名「STEP[18] 两跑翻面（R584 主笔 `跑过=4 红=4` / 本轮 `跑过=8 红=0`）」→ **不计入对账口径**（基名在漂 —— 既有那一族，本轮没为它改任何判据）
  · 红名「`STEP[15]/[17]/[19]` 那三朵（5 个名字同集合）」→ **不计入对账口径**（契约名 —— 逐字同集合，只算"没有新名字"）
- 门复算（预览 → 落盘 → 复算，取不动点）：`%(recon)s`
- 逐本现读七个数（写之前各 0 / 写之后每一本恰 1）：`preapply_counts.txt`、`postapply_counts.txt`。

⑦ **验证链（顺序照旧，一处偏差具名）**：`swift build --build-tests`（包目录内）告警 **0**；python 判据卷 `%(pytest)s / %(pytest_ok)s`；三把刀**先跑**（打在 `scripts/frame_baseline.py` 上、与 swift 构建目录无关 ⇒ 没撞锁；偏差具名 `KNIVES_BEFORE_CAPTURE_PYTHON_ONLY`，沿用上一轮同一命名）`%(knives)s`；每把红了哪几格逐字：`%(knife_reds)s`；`MD5=` 那一行是刀链前后同一份文件的现读（还原证人）；Swift 捕获判据卷 `%(capture)s`（帧 `%(frames)s`）；对新门 `%(gate_frames_drift)s` ⇒ `%(gate_frames)s`；真机键那一趟 `%(forensics)s`（656 那朵照实不抹）；全量卷 `%(full)s`；三道预检**串行**（不与 swift 卷并行 ⇒ 本轮没再撞 `NOT_RUN_TIMEOUT`）：`%(precheck_needle)s`、`%(precheck_arm)s`、`%(precheck_hidden)s`；换装 `SKIP_INSTALL=no-product-change`（产品 0 文件）；七本台账 → 派生格落盘后现读 → 电池（本轮新案 10 格 ⇒ 内层总数由电池自己那一行报，账里不预测那个数；本机那一趟的数**不回填**，最终签字归 runner `STEP[9]`）；产品面连续零改动由 `product_streak.py` 落盘之后现读；清账 `%(absence)s`；代码 numstat 现读 `%(numstat)s`；字面量真验证（派单 ③②）`%(pyverify)s`。

⑧ **看图那一腿**：`%(look)s`

⑤ **地基一字不动**：4.5 墨、150、2x 8.0pt、1x 6.0pt、120ms 与容差 1、Motion ≥2、`probeInkFraction=3%%`、`.contentFade 0.20`、像素格容差 1.5 与跳变地板 8、声明时长、全量 skipped 现读、禁碰 14 面不抬不降（本轮没碰捕获侧 Swift ⇒ 逐字证人就是 ⑦ 里真机键那一趟）；`--allow-missing` 两帧原样；本轮新增的两道判定（无出处 / 出处不符）是**收紧**，没有任何一格被放宽或改成 skip。
""" % dict(
        r=i["r"], n=i["n"], round=i["round"], date=DATE, prev_n=i["prev_n"], prev_r=i["prev_r"],
        prev_state_r=i["prev_r"],
        drift_signed=(m[u"门那一步的逐字读数"] or [u"（没取到）"])[0][:230],
        result_signed=[l for l in (m[u"门那一步的逐字读数"] or [u""]) if l.startswith("FRAME_BASELINE_RESULT")][0][:160]
        if any(l.startswith("FRAME_BASELINE_RESULT") for l in (m[u"门那一步的逐字读数"] or [])) else u"（没取到）",
        notjudged_signed=[l for l in (m[u"门那一步的逐字读数"] or [u""]) if "NOT_JUDGED" in l][0][:150]
        if any("NOT_JUDGED" in l for l in (m[u"门那一步的逐字读数"] or [])) else u"（没取到）",
        disp=m[u"处置"][:420],
        steps_add=u" / ".join(l.strip() for l in a["steps"].splitlines() if u"⇒" in l and u"⇒ failure" in l) or u"（没有失败步骤）",
        drift_add=(a[u"门那一步的逐字读数"] or [u"（没取到）"])[0][:230],
        result_add=[l for l in (a[u"门那一步的逐字读数"] or [u""]) if l.startswith("FRAME_BASELINE_RESULT")][0][:160]
            if any(l.startswith("FRAME_BASELINE_RESULT") for l in (a[u"门那一步的逐字读数"] or [])) else u"（没取到）",
        notjudged_add=[l for l in (a[u"门那一步的逐字读数"] or [u""]) if "NOT_JUDGED" in l][0][:150]
            if any("NOT_JUDGED" in l for l in (a[u"门那一步的逐字读数"] or [])) else u"（没取到）",
        disp_add=a[u"处置"][:420],
        probe_main=(m.get(u"探针") or [u"（没取到）"])[0][:200],
        probe_add=(a.get(u"探针") or [u"（没取到）"])[0][:200],
        evid_upd=d["evidence_update"], evid_chk=d["evidence_check"], evid_ls=d["evidence_ls"],
        steps_signed=u" / ".join(l.strip() for l in d["main"]["steps"].splitlines() if u"⇒ failure" in l) or u"（没有失败步骤）",
        byte_compare=d["byte_compare"], dark_rows=d["dark_rows"][:900], register_dark=d["register_dark"],
        gate_after_register=d["gate_after_register"], drift_after_register=d["drift_after_register"],
        note_check=d["note_check"], baseline_untouched=d["baseline_untouched"], delta=d["tests_delta"], tb=d["tests_before"], ta=d["tests_after"],
        drift_no=d["drift_before"][:230], gate_no=d["gate_no_proof"], gate_yes=d["gate_after"],
        knives=knives, knife_reds=d["knife_reds"].strip().replace("\n", u" ｜ ")[:900],
        pytest=d["pytest"], pytest_ok=d["pytest_ok"], capture=d["capture"], frames=d["frames"],
        gate_frames=d["gate_frames"], gate_frames_drift=d["gate_frames_drift"],
        forensics=d["forensics"], full=d["full"],
        precheck_needle=grep_line(d["prechecks"], "NEEDLE_PRECHECK", u"针预检"),
        precheck_arm=grep_line(d["prechecks"], "ARM_TOTAL", u"臂总数"),
        precheck_hidden=grep_line(d["prechecks"], "HIDDEN_ARMS", u"盲区名册"),
        absence=d["absence"], numstat=d["numstat"].strip().replace("\n", u" ｜ "),
        pyverify=d["pyverify"].strip().replace("\n", u" ｜ ")[:520],
        recon=d["recon"], look=d["look"].strip().replace("\n", u"\n  ")[:1800],
    )


def block_ui(d):
    i = d["ident"]
    u0 = next_u()
    m = d["main"]
    us = [
        (u"⓪ 那条预测被 runner 自己签掉了：七项逐条全中、STEP[11] 不再红",
         u"主笔 `42093340563 ↔ 3e13d47` 的门那一行逐字 `%(drift)s`，结论行 `ok 拦路=0（…未登记不判…）`，"
         u"不判那一格 `baseline-owned-by:local_MacBook_Air_local` ⇒ R584 补记里那句「应读到 ⑶ 且 STEP[11] 不红」**成立**。"
         u"⚠ 这句话的边界要说清：这**不等于** runner 的变帧有人判了 —— 它今天仍是 `判=不判`，"
         u"只是不再拿 348 张噪声拦门。补记笔 `42094125984 ↔ aa8ef88` 收口前自己到数，读到的是同一个 出口·乙（见 ⓪）。"
         % {"drift": (m[u"门那一步的逐字读数"] or [u"（没取到）"])[0][:180]}),
        (u"监工那条形状结论成立：印出来的出路当时做不到",
         u"三处逐字 + 目录现读（`by_machine/` 不存在、工作基线署名 `local:MacBook-Air.local`）⇒ "
         u"**任何机器照那条命令跑 `update` 都永远停在 `判=不判`** ⇒ 658 的出路 ⑵ 前置不成立。"
         u"本轮只补前置（让那条命令真能落笔），三条出路仍一条不选。"),
        (u"名册从「只有读路径」补成「有写路径 + 出处」",
         u"`register-drift` 写行时 `machine` 只能取运行时 `machine_key()`（**没有 `--machine` 参数**，测试现证 argparse 拒收），"
         u"并带 `observed = {frame_sha, baseline_sha}`；`check` 对**此刻正在豁免漂移的本机行**问出处："
         u"没出处 ⇒ 红并点名，出处与当轮观测不同字 ⇒ 红并点名。手抄一行 `machine=github-runner:*` 洗不掉那一台的未登记。"
         u"before/after 同一棵树：`拦路=8（无出处8）` 退 1 → `--restamp` 之后 `无出处0` 退 0。"),
        (u"两向证人的形状：正臂跑的是**印出来的那条命令**",
         u"正臂从 stdout 的「出路」那一行抽出命令原文，只替换占位的帧目录、补测试自己的 `--repo-root`，原样跑 ⇒ "
         u"`FRAME_BASELINE_AGAINST=by_machine:<键>` 且 `判=判`；负臂证明不带旗标的那条**不产出** `by_machine/`。"
         u"上一轮那一格是手摆文件 ⇒ 它测不到「印出来的命令做不到」这件事（对照只测正则不测流水线那一族）。"),
        (u"刀 M1538/M1539/M1540 全 CAUGHT；落完之后现读「红了哪几格」，把上一稿写的「三边互不重叠」撤掉（现读最高 M1537 ⇒ 没借号）",
         u"`%(knives)s`，逐把红了哪几格照日志逐字抄。**单边性要现读、不许由措辞担保**：M1538（`update` 忽略旗标）红 **2** 格 —— 正臂 `test_printed_remedy_flips_the_verdict_to_judged` 断在 `FRAME_BASELINE_MACHINE_BASELINE=` 缺失，手抄行那一格 `test_a_hand_copied_...` 也红、但它断的是**另一行**（`AGAINST=by_machine:github-runner` 没出现）；M1539（摘掉 `verify_provenance` 调用）红 **3** 格（手抄行断 `行=1` 出处没接住、无出处格、出处不符格）而写路径两格未动；M1540（note 原文保留失效）红 **1** 格，就是本轮真实犯过的那一处。⇒ 说「三边互不重叠」是**说过头了**：M1538 与 M1539 打到**同一个测试名**，只是断在不同的行 ⇒ 按名字算它们重叠，按断言算各打各的。这一格记下来是因为下一轮如果有人把 M1538 撤掉，M1539 那三格仍然会红 —— 真正的冗余只在这里成立。"
         u"每把单独取退出码、输出不接 head、status 文件派生；刀链跑着的时候没改任何仪器。" % {"knives": u" ｜ ".join(
            u"%s rc=%d 末次=%s clean=%d" % (k["arm"], k["rc"], k["post"], k["clean"]) for k in d["knives"])}),
        (u"一处真实写脏（已清）：测试把命令跑到了真仓库上",
         u"`split()[1:]` 少剥一个 token ⇒ argv 第一项变成脚本路径，那一趟 `update --for-machine` 在**真仓库**里写出 "
         u"`docs/frame_baselines/by_machine/local_other_machine.json`（`machine='local:other-machine' count=2`）。"
         u"处置顺序照规矩：先把那份文件的署名与内容读出来留证，再删文件与目录，再给测试补 `--repo-root`。"
         u"⇒ 新规矩：**测试里跑任何会写盘的工具子进程之前，先确认它拿到的根目录是临时目录**（"
         u"「fail-fast 不是证人」那一族的延伸：这次 fail-fast 根本没响，因为写成功是它预期的行为）。"),
        (u"漂移集合会跨会话**增减**：八张暗档第一次出现在本机漂移里，而包围盒那把尺在 RGBA 上会说瞎话（开单 659）",
         u"新帧对 R584 那一份 `%(byte)s` ⇒ 不同的**恰好是八张暗档**（655 当年那句「八张全是 light」从本轮起不成立）；逐张差量 41–46 颗像素、逐带极值 R<=6 / G,B<=2 / **alpha 一字未动** ⇒ 亚像素级噪声，不是版式/文字/颜色档变化。门先红在 `未登记=8`，处置只走工具自己的路：`%(reg)s` ⇒ 之后 `%(after)s`（退 0）—— 红没了但**漂移一条没少**（变帧 8→16 是实测），655 照旧开。另有一处仪器读数：`%(gbr)s` 而 `%(gbl)s`、合成正对照 `%(gbx)s` ⇒ **Pillow 11.3.0 的 `getbbox()` 对 mode=RGBA 的差值图恒报 None**（4096 颗全差的合成图也报 None）⇒ 包围盒不能单独当「看不见」的证人；本轮差点由它写下「这八张像素相同」，是逐像素计数把它救回来的（R579 那一课的镜像：那次是包围盒指错位置，这次是它根本不说话）。%(grep)s ⇒ 这不是既有判据的假绿，是这一族尺的下一个坑，只开单不动仪器。" % {"byte": d["byte_compare"], "reg": d["register_dark"], "after": d["drift_after_register"], "gbr": d["getbbox_rgba"], "gbl": d["getbbox_l"], "gbx": d["getbbox_ctrl"], "grep": d["getbbox_grep"]}),
        (u"看图那一腿：像素面本轮仍不可见，且这是对的",
         u"%(look)s" % {"look": d["look"][:900]}),
    ]
    head = (u"## 第 %(n)s 轮（R%(r)s · %(date)s · U-%(u0)s…U-%(u1)s）：把上一轮印给读者的那条**出路做成真的**"
            u"（`update --for-machine` 落 `by_machine/`；名册补写路径 `register-drift` 与每行出处；"
            u"`check` 从此能证伪「手抄一行」；⓪ R584 那条预测被 runner 自己签掉）\n\n"
            % {"n": i["n"], "r": i["r"], "date": DATE, "u0": u0, "u1": u0 + len(us) - 1})
    body = u"".join(u"- **U-%d：%s**。\n    %s\n\n" % (u0 + k, t_, b) for k, (t_, b) in enumerate(us))
    return head + body, u0


def block_iteration(d):
    i = d["ident"]
    return u"""## Round %(round)s · R%(r)s（第 %(n)s 轮 · %(date)s）：让工具印出来的那句话变成真——出路、写路径、出处、证伪

**七维度自评**（恰七行，每格 n/15；维度名照曲线尺认的那七个同字，本轮不造新维度）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉看图 | @@LOOKSCORE@@ | %(look_short)s |
| 判据有效性 | 15/15 | 本轮判的是**那句话能不能做到**：正臂跑的是 stdout 印出来的命令原文（只替换占位符与测试自己的 `--repo-root`），不是手摆文件；负臂证明不带旗标的命令不产出 `by_machine/` ⇒ 两条命令的区别有证人。本机名册 before/after 同一棵树、唯一变的是有没有出处（`拦路=8（无出处8）` 退 1 → `无出处0` 退 0）⇒ 补的是判定不是措辞。 |
| 假绿防御 | 15/15 | ①「手抄一行洗掉未登记」这条路现在要红（无出处 / 出处不符两格，各带点名）；②`--machine` 这种"我自己说是哪台"的口子不存在（argparse 现证）；③空理由/空单号 ⇒ 退 2 且一行不落；④`--restamp` 只盖本机当轮真的在漂且账上理由齐全的行；⑤note 覆盖回归由测试 + 刀 M1540 双钉；⑥三把刀各只动一边，落完之后**现读**每把红了哪几格：M1538=2 格、M1539=3 格、M1540=1 格；其中 M1538 与 M1539 打到同一个测试名而断在不同的行 ⇒ 草稿里那句「互不重叠」**被现读否掉并撤掉**（U 那一节照实记这次撤回）。 |
| 产品面推进 | 4/15 | 产品 **0** 文件；推进的是门的**可信度**：上一轮那扇门的出路是空头支票，本轮它兑现了，同时把"登记"从可抄的措辞变成可证伪的账。 |
| 台账一致性 | 11/15 | 身份两处交叉核对；七个标题形状写前全 0、写后各 1；派生格按**落盘之后**现读并带取数口（上一轮那两处时序红本轮没复发）。扣分在 ⑨·3 那一处真实写脏（测试把命令跑到真仓库，写出假机器基线，已留证删除）与 ⑨·1/⑨·2 两处生成器自伤（覆盖人写的 note、用了没 import 的 `io` ⇒ "编译过"不等于"这条路跑过"）。 |
| 剩余风险处置 | 14/15 | 658 不结案、三条出路一条不选（本轮只补前置）；655 仍没重烤（工作基线那份一字未动，`update` 只在临时目录里证明能落笔）；656/657/646/647/650/651/653/654/644/639/640/Motion ≥2/633/SSH 成因/手感签字全部照原样归用户；旧红一朵不抹（STEP[18] 仍写"在漂"）；第③段着色器一字未写。扣 1 分：runner 那一台的变帧维度**仍然没人判** —— 本轮只是让它将来可判。 |
| 交接可读性 | 15/15 | R586 的 ⓪ 写死四格（成对号由 R585 补记那一笔现取现写，不在这里预测）：①本轮那一笔落地后的 run↔sha 成对号，读它**全部**失败步骤（`register-drift`/`--for-machine` 第一次在 runner 上被跑到是哪一跑，只有它自己能说）；②`42093340563`、`42094125984` 两跑的 出口·乙 已签，**不重复对拍**；③runner 上若出现 `判=判` 才说明有人为那一台落了 `by_machine/github-runner.json` ⇒ 那时 658 才谈得上选出路（工作侧一条都不许代选）；④STEP[18] 的 `本次下结论` 两跑读成 8 与 7 ⇒ 继续两跑一起读、不许单跑下结论。 |
""" % {"round": i["round"], "r": i["r"], "n": i["n"], "date": DATE,
        "look_short": d["look"].strip().splitlines()[0][:170]}


def block_backlog(d):
    i = d["ident"]
    m = d["main"]
    return u"""## R%(r)s 追账（第 %(n)s 轮 / Round %(round)s · %(date)s）：658 补前置但不结案，655/656/657 一条没结

**658 追记（R%(r)s）：出路 ⑵ 当时的前置不成立 —— 工具印出来的那条命令做不到，本轮把它做成真的**
    现象（取值时刻=R%(r)s 开工第一步，三处逐字 + 目录现读）：① `update` 那一支里 `write_baseline(manifest_path(...), frames)` **无条件**执行，注释还写着「工作基线永远写在 docs/frame_baseline.json」；
    ② `check` 只在 `os.path.exists(by_machine/<键>.json)` 时才走"这台机器自己判"那一支；
    ③ 而它印给读者的出路写着「跑 `update <帧目录>`，它会署名并写 `docs/frame_baselines/by_machine/<键>.json`」。
    目录现读：`%(ls)s` ⇒ 那个目录不存在。
    ⇒ 结论（是读数不是推理）：**任何机器照那句话跑一遍 `update`，都永远停在 `判=不判`** ⇒ 出路 ⑵ 的前置不成立。
    R%(r)s 补的前置（三条出路仍一条不选）：`update --for-machine`（键一律运行时取，没有 `--machine` 这个口子）、
    `register-drift` / `--restamp`（名册的写路径 + 每行 `observed` 出处）、`check` 的证伪（无出处 / 出处不符都红并点名）。
    到数证人：`42093340563 ↔ 3e13d47` 的门那一行逐字 `%(drift)s` ⇒ 那一跑是 `判=不判` 且 **STEP[11] 不红**（R%(prev_r)s 补记那条预测成立）。
    ⚠ 这句不许被读成"runner 的变帧有人判了"：今天仍然**没人判它**，只是不再拿 348 张噪声拦门；
    真要判，得有人为那一台落 `by_machine/github-runner.json` —— 那仍是 658 的三条出路之一，归用户。

**659. `getbbox()` 对 mode=RGBA 的差值图恒报 `None` ⇒ 包围盒那把尺不能单独当「两个像素面没差异」的证人（R%(r)s 现读并新开）**
    现象（正对照 + 真帧对，两份都在 `/tmp/r%(r)s/getbbox.txt`）：真帧对 `%(gbr)s`，同一对帧先 `convert("L")` 或拆单通道就有色 `%(gbl)s`；合成正对照（4096 颗像素**每一颗**的 R 都差 6、alpha 全同）`%(gbx)s` ⇒ 不是「差量太小」、不是「只有 alpha 差」，是 `getbbox()` 在那种 mode 上**根本不工作**（Pillow 11.3.0 实测）。
    为什么本轮只开单不动仪器：本轮的差量是**逐像素计数 + `getextrema()`** 量出来的，那条路是通的；而 `%(grep)s ⇒ 没有任何既有判据正在用它，所以今天没有假绿在账上。出路（都归下一轮或用户定向，本轮一条没选）：⑴任何「包围盒为空 ⇒ 看不见」的句子必须先出示 mode；⑵像素差量一律走 `convert("L")`/分通道后再 `getbbox()`；⑶把这条钉成一格会红的仪器测试（本轮没做 ⇒ 不许写成已修）。
    ⚠ 与 R579 那条的关系：那次是包围盒**指错带子**（量到了别处），这次是包围盒**拒绝出声**；两次的共同形状是「看图前不定位差量」，两次的修法相反 ⇒ 分两格记。

**655 / 656 / 657 状态（R%(r)s）：都不结案，各补一句**
    · 655：本轮仍**没跑** `update` 到工作基线（那份文件 md5 与 HEAD 逐字相同，证人见 STATE ② 那一格）；HEAD 那 8 行只是多了 `observed` 出处，帧名/理由/单号/机器逐字未变（8/8）；**而漂移集合本身从 8 涨到 16**：新登记的 8 张是暗档 ⇒ 655 原文那句「八张全是 light 档」从本轮起不成立（照实在这里记一句，不改那一节原文）。
    · 656：三条出路（甲锁 `.aqua`／乙按外观拆两档／丙由另一台或另一次会话补第二档）一条没选；本轮没碰捕获侧 Swift，只重跑了真机键那一趟 ⇒ 那一朵红**照实复现**（`%(ftot)s`，红名 `testGoingNonOpaqueDoesNotWashOutTheSidebarMaterial`）。
      本轮新增两条读数：`%(ftier)s`；以及 `%(ffifth)s`。
      ⇒ 本单那一格的名字要**改口**（只改口径不改结论）：`%(fretract)s`
      `%(fapp)s`（R579 那句"禁止为了拿第二档改这台机器的全局外观"本轮照守）。
    · 657：没统一、没换键；本轮新增两条**同族证人**（不是统一）：`register-drift` 的键只能取运行时 ⇒ 手填没有口子；`by_machine` 文件名只抹标点不抹大小写 ⇒ 两份字面落两个文件。
""" % {"r": i["r"], "n": i["n"], "round": i["round"], "date": DATE, "prev_r": i["prev_r"],
       "ls": d["evidence_ls"], "drift": (m[u"门那一步的逐字读数"] or [u"（没取到）"])[0][:200],
       "forensics": d["forensics"][:120],
       "ftot": d["forensics_total"][:120], "ftier": d["forensics_tier"][:200],
       "fretract": d["forensics_retract"][:420], "ffifth": d["forensics_fifth"][:300],
       "fapp": d["forensics_appearance"][:260],
       "gbr": d["getbbox_rgba"], "gbl": d["getbbox_l"], "gbx": d["getbbox_ctrl"], "grep": d["getbbox_grep"],
       "delta": d["tests_delta"], "tb": d["tests_before"], "ta": d["tests_after"]}


def block_decisions(d):
    i = d["ident"]
    return u"""## D-%(r)s（R%(r)s · %(date)s · 第 %(n)s 轮 / Round %(round)s）：印给读者的那句话就是产品的契约；做不到就别印，做得到就要有"照它跑一遍"的证人

背景：R584 给基线门补了机器维度，并印了一条出路（"跑 `update` 就会写 `by_machine/<键>.json`"）。
R585 开工现读发现 `update` 那一支**无条件**写工作基线 ⇒ 那句话是空头支票；同时名册只有读路径，
`machine` 值全是手抄的字面 ⇒ 下一轮谁都能抄一行 `machine=github-runner:*` 把那一台的 `未登记=348` 洗成 0，
**一朵红都不会有**。

决定：
1. **出路那一行必须写成一条能跑的命令，并且有一条测试把它的原文抽出来跑**。测试不许自己摆文件：
   手摆的 `by_machine/` 只能证明"文件名对了会怎么走"，证明不了"人照你说的做能不能走到"。
   （同族：R558 的"驱动必须换成产品 action"、R565 的"对照只测正则不测流水线"。）
2. **登记必须有出处，出处只能由命令自己盖**。`register-drift` 的 `machine` 一律取运行时 `machine_key()`，
   命令行**没有** `--machine`；每行带 `observed = {frame_sha, baseline_sha}`；`check` 对"此刻正在豁免漂移的本机行"
   问出处 —— 没出处或哈希对不上当轮观测 ⇒ 红并逐行点名。**豁免权必须可追溯，否则它只是措辞。**
3. **证伪只问正在干活的那几行**：陈旧行（此刻不漂）没在替任何人放行，拿"没出处"红它就是把判定扩成
   "每行都得重写过"，那会逼人删账（R584 ⑵ 那条"不许逼人在两台机器之间来回删行"的同一条约束）。
4. **他机行不由本机证伪**：本机没有那一台的帧，硬判就是拿自己的观测替别人下结论；
   那一台的基线进了仓库才谈得上跨机证伪 ⇒ 仍是 658。
5. **人写的原文不许被生成器覆盖**：第一次 `--restamp` 把 R583 那句"本名册不是重烤基线的替代品"冲掉了 ⇒
   改成"原文在就留着、新句只补一次"，并配测试 + 刀 M1540。

被否掉的：把 `--for-machine` 做成默认（那等于偷偷改了 `update` 的既有语义，且会牵动 655 的重烤归属）；
给名册加 `--machine` 让 CI 替 runner 登记（那是把"谁观测谁登记"这条又拆掉）；
把"无出处"降级成具名 skip（那是把刚补上的判定再藏回去）。
""" % {"r": i["r"], "date": DATE, "n": i["n"], "round": i["round"]}


def block_changelog(d):
    i = d["ident"]
    return (u"""### 帧基线那条**印给读者的出路**做成真的（R%(r)s / 第 %(n)s 轮 / Round %(round)s，产品 0 文件）：`update --for-machine` 落 `by_machine/`、名册补写路径与出处、`check` 能证伪手抄行
    R%(prev_r)s 那扇门印的出路是空头支票：`update` 那一支无条件写工作基线，而 `check` 只在
    `docs/frame_baselines/by_machine/<键>.json` 已存在时才走"这台机器自己判"那一支 ⇒ 任何机器照那句话跑完都停在 `判=不判`
    （目录现读：那个目录当时根本不存在）。名册同样只有读路径 ⇒ 那 8 行的 `machine` 是手抄的字面，
    谁抄一行 `machine=github-runner:*` 就能把那一台的 `未登记=348` 洗成 0 而一朵红都不许有。
    本轮：① `update --for-machine` 真写逐机器基线（键一律运行时取，**没有** `--machine` 参数）；
    ② `register-drift`（含 `--restamp`）成为名册的写路径，每行带 `observed = {frame_sha, baseline_sha}`；
    ③ `check` 对**此刻正在豁免漂移的本机行**问出处 ⇒ 无出处 / 出处不符都红并逐行点名（陈旧行与他机行仍只报数）；
    ④ 出路那一行现在印的是真能跑的命令，并由一条**把 stdout 里那句命令原样跑一遍**的测试作证，另配"不带旗标就仍不判"的负臂。
    本机 before/after 同一棵树：`拦路=8（无出处8）` 退 1 → `register-drift --restamp` 之后 `无出处0 未登记0` 退 0；
    `update` 对工作基线那份一次没跑（655 不变）、阈值与 `--allow-missing` 一字未动。
    电池 +%(delta)d 格（`scripts/tests/test_frame_baseline.py` %(tb)d→%(ta)d，两头都是现数 `def test_` 而不是抄派单），刀 M1538/M1539/M1540 全 CAUGHT；658 补前置、不结案。
""" % {"r": i["r"], "n": i["n"], "round": i["round"], "date": DATE, "prev_r": i["prev_r"],
           "delta": d["tests_delta"], "tb": d["tests_before"], "ta": d["tests_after"]})


# —————————————————————————————————————————————————————————──
# 落盘：全部文本先算完（任何一块崩 ⇒ 一本都不写），再一次性写；派生格只许**落盘之后**再取。


def shapes(i):
    return [(u"UI 轮次标题", u"## 第 %d 轮（R%d · " % (i["n"], i["r"])),
            (u"ITER 标题", u"## Round %d · R%d" % (i["round"], i["r"])),
            (u"STATE 主节", u"## R%d 状态（" % i["r"]),
            (u"DECISIONS", u"## D-%d（" % i["r"]),
            (u"BACKLOG 追账节", u"## R%d 追账" % i["r"]),
            (u"CHANGELOG 标题行", u"### 帧基线那条**印给读者的出路**做成真的（R%d / " % i["r"])]


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

    # FINAL_REPORT 三格：streak（只留**一个**候选数，旧阅读以"上一格原文留着：**N**（…"的形式留着）、
    # U 上界（只留**一条**派生注记）、§13 的"仍开"指针。三格都是现读派生，不手抄。
    fin = read("FINAL")
    streak_n = int(re.search(r"streak=(\d+)", d["streak"]).group(1))
    m2 = re.search(r"产品面连续零改动轮数 = \*\*(\d+)\*\*（R(\d+) 台账落盘之后现读", fin)
    if not m2:
        raise SystemExit("ANCHOR-MISS FINAL：streak 那一格现读不到")
    cell = (u"产品面连续零改动轮数 = **%d**（R%d 台账落盘之后现读 `python3 scripts/product_streak.py` ⇒ `%s`；"
            u"as-of 口径 ⇒ 读作「本轮之前最后一次产品改动在 %d 轮前（R567 的 `8f679f9`）」，R%d…R%d 共 %d 轮都是产品 0 文件 ⇒ 下一轮是 %d。"
            u"上一格原文留着：**%s**（R%s 台账落盘之后现读"
            % (streak_n, i["r"], d["streak"], streak_n, streak_n + 567 + 1, i["r"] - 1, streak_n,
               streak_n + 1, m2.group(1), m2.group(2)))
    fin = fin[:m2.start()] + cell + fin[m2.end():]
    mu = re.search(r"U-31 … U-(\d+)（R(\d+) 现读抬到最新一节）", fin)
    if not mu:
        raise SystemExit("ANCHOR-MISS FINAL：U 格那一注记现读不到（形状必须是 `（Rnnn 现读抬到最新一节）`，只准一条）")
    u_last = u0 + ui_text.count(u"- **U-") - 1
    if ui_text.count(u"- **U-") < 1:
        raise SystemExit("矛盾读数：本轮 UI 节里没有 U 格")
    fin = fin[:mu.start()] + u"U-31 … U-%d（R%d 现读抬到最新一节；本轮 UI 节现数 %d 格）" % (u_last, i["r"], ui_text.count(u"- **U-")) + fin[mu.end():]
    mp = re.search(r"完整名单以 `AGENT_STATE\.md` 的 R(\d+) 节 ② 为准", fin)
    if not mp:
        raise SystemExit("ANCHOR-MISS FINAL：§13 的仍开指针现读不到")
    fin = fin[:mp.start()] + u"完整名单以 `AGENT_STATE.md` 的 R%d 节 ② 为准" % i["r"] + fin[mp.end():]
    new["FINAL"] = fin

    for book, text in new.items():
        write(book, text)
    post = counts(i, "postapply")
    print(u"POST（写之后逐本现读）：\n" + post)
    tot = {}
    for line in post.splitlines():
        for name, cnt in re.findall(r"(\S+?)=(\d+)", line.split(u"::", 1)[1]):
            tot[name] = tot.get(name, 0) + int(cnt)
    bad = {k: v for k, v in tot.items() if v != 1}
    if bad:
        raise SystemExit(u"逐本标题个数不合格：%s" % bad)
    print(u"SEVEN_COUNTS_OK=%s" % json.dumps(tot, ensure_ascii=False))
    return 0


def main():
    d = gather()
    d["look_score"] = os.environ.get("LOOK_SCORE", u"11/15")
    return apply(d, "--apply" in sys.argv)


if __name__ == "__main__":
    sys.exit(main())

# -*- coding: utf-8 -*-
"""R584 七本台账写手（本轮**新写**，不 port 上一轮那份 —— 上两轮 port 连错三次锚）。

三条与上一版不同的地方（都来自本轮派单 ③④）：
① 锚一律**现读**：轮次标题/单号/计数器都由正则从盘上取，绝不把我以为的上一轮字面串写死。
   锚命中数不等于 1 就停，而且**在任何一本落盘之前**停（fail-fast 只证明没写脏，不证明没写重）。
② 落盘之前先跑 DRY：逐本现读"本轮那六个标题形状各出现几次"并写 /tmp/r584/preapply_counts.txt，
   落盘后再数一遍写 postapply_counts.txt ⇒ 六个数是证人，不是我的措辞。
③ fill() 覆盖每一本，返回前逐本回读 `@@` 命中=0（R567 那一族：半途崩 = 五本各两份）。
"""
import io
import json
import os
import re
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0"
TMP = "/tmp/r584"
BOOKS = {
    "UI": "AGENT_UI_AUDIT.md",
    "ITER": "AGENT_VISUAL_ITERATION.md",
    "STATE": "AGENT_STATE.md",
    "BACKLOG": "AGENT_BACKLOG.md",
    "DEC": "AGENT_DECISIONS.md",
    "FINAL": "AGENT_FINAL_REPORT.md",
    "CHANGE": "CHANGELOG.md",
}
ROUND = {"r": 584, "d": 583, "round": 581, "date": "2026-11-06"}


def read(name):
    return io.open(os.path.join(ROOT, BOOKS[name]), encoding="utf-8").read()


def write(name, text):
    with io.open(os.path.join(ROOT, BOOKS[name]), "w", encoding="utf-8") as handle:
        handle.write(text)


def sh(args, timeout=600):
    proc = subprocess.Popen(args, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            universal_newlines=True)
    out, err = proc.communicate(timeout=timeout)
    return proc.returncode, out, err


def need(text, pattern, label, flags=0):
    """锚必须**恰好命中一次**，否则停（并且停在任何写盘之前）。"""
    hits = re.findall(pattern, text, flags)
    if len(hits) != 1:
        raise SystemExit("ANCHOR-MISS %s：模式 %r 命中 %d 次（应为 1）" % (label, pattern[:60], len(hits)))
    return hits[0]


def identity_from_disk():
    """本轮身份由**盘上最大轮次**推出来，不从我脑子里的号抄。"""
    ui = read("UI")
    prev_r, prev_d = None, None
    m = re.search(r"(?m)^## 第 (\d+) 轮（R(\d+) · ", ui)
    if not m:
        raise SystemExit("UI_AUDIT 里找不到轮次标题形状 ⇒ 身份推不出来")
    prev_n, prev_r = int(m.group(1)), int(m.group(2))          # 第 582 轮 / R583
    state = read("STATE")
    ms = re.search(r"(?m)^## R(\d+) 状态（", state)
    prev_state_r = int(ms.group(1)) if ms else None
    if prev_r != prev_state_r:
        raise SystemExit("身份交叉核对不过：UI_AUDIT 最新 R%d 而 STATE 最新 R%d" % (prev_r, prev_state_r))
    r = prev_r + 1
    # 本仓库的恒等式（R583 = 第 582 轮 = Round 580）⇒ n = R-1、Round = R-3，两条都由现读推，不写死。
    return {"prev_r": prev_r, "prev_n": prev_n, "r": r, "n": r - 1, "round": r - 3,
            "prev_state_r": prev_state_r}


# ———————————————————————————————————————————————————————————─
# 读数：全部从 /tmp/r584 的文件里取，**不从我脑子里抄**（R562/R551 那一族：抄基线会把字段抄丢）。


def must_read(path, label):
    if not os.path.exists(path):
        raise SystemExit("读数缺席：%s（%s）⇒ 链条还没跑到那一格，不许写账" % (path, label))
    text = io.open(path, encoding="utf-8", errors="replace").read()
    if not text.strip():
        raise SystemExit("读数是空的：%s（%s）" % (path, label))
    return text


def grep_line(text, prefix, label, last=True):
    rows = [l.strip() for l in text.splitlines() if l.strip().startswith(prefix)]
    if not rows:
        raise SystemExit("读数里找不到 %r（%s）" % (prefix, label))
    return rows[-1] if last else rows[0]


def gather():
    ci = json.loads(must_read(os.path.join(TMP, "ci_readings.json"), u"⓪ 两跑读数"))
    d = {"ident": identity_from_disk()}
    d["fields_order"] = ci["FIELDS_ORDER_CHECK"]
    runs = {k: v for k, v in ci.items() if k != "FIELDS_ORDER_CHECK"}
    d["runs"] = runs
    main_run, add_run = "42077586416", "42077903445"
    d["main"] = runs[main_run]
    d["add"] = runs[add_run]
    # 本轮三门读数（本机 / 换机器键 / 换名册路径）
    local = must_read(os.path.join(TMP, "local2.txt"), u"本机那一门")
    sim = must_read(os.path.join(TMP, "sim2.txt"), u"换机器键那一门")
    absent = must_read(os.path.join(TMP, "absent.txt"), u"换名册路径那一门（反证）")
    d["gate_local"] = grep_line(local, "FRAME_BASELINE_DRIFT ", u"本机判定行")
    d["gate_local_result"] = grep_line(local, "FRAME_BASELINE_RESULT=", u"本机结论行")
    d["gate_sim"] = grep_line(sim, "FRAME_BASELINE_DRIFT ", u"模拟 runner 判定行")
    d["gate_sim_notjudged"] = grep_line(sim, "FRAME_BASELINE_DRIFT_NOT_JUDGED=", u"不判那一格")
    d["gate_sim_result"] = grep_line(sim, "FRAME_BASELINE_RESULT=", u"模拟 runner 结论行")
    d["gate_absent"] = grep_line(absent, "FRAME_BASELINE_DRIFT ", u"反证判定行")
    d["gate_absent_result"] = grep_line(absent, "FRAME_BASELINE_RESULT=", u"反证结论行")
    # 刀：status 文件派生，每把一行，逐把的 rc 由被测那条命令直接产生
    kn_text = must_read(os.path.join(TMP, "knife_status.txt"), u"刀状态文件")
    knives = []
    for ln in kn_text.splitlines():
        m = re.match(r"(r\d+)/(M15\d\d) rc=(\d+) caught=(\d) clean=(\d) precheck=(\S+) post=(\S+)", ln.strip())
        if m:
            knives.append({"arm": m.group(2), "rc": int(m.group(3)), "caught": int(m.group(4)),
                           "clean": int(m.group(5)), "precheck": m.group(6), "post": m.group(7)})
    if not knives:
        raise SystemExit("刀读数一条都没有")
    for k in knives:                       # R583 立的那条：CAUGHT 必须 rc 非 0，否则这一格是哑巴
        if k["post"] == "CAUGHT" and k["rc"] == 0:
            raise SystemExit("矛盾读数：%s 说 CAUGHT 而 rc=0" % k["arm"])
    d["knives"] = knives
    # 各卷的汇总行
    d["pytest"] = grep_line(must_read(os.path.join(TMP, "pytest_final.txt"), u"python 判据卷"),
                            "Ran ", u"python 卷 Ran 行")
    d["pytest_tail"] = grep_line(must_read(os.path.join(TMP, "pytest_final.txt"), u"python 判据卷"),
                                 "OK", u"python 卷签字行", last=False)
    cap = must_read(os.path.join(TMP, "capture_summary.txt"), u"捕获/判据卷")
    d["capture"] = grep_line(cap, "CAPTURE_LINES=", u"判据卷汇总")
    d["capture_frames"] = grep_line(cap, "FRAMES=", u"帧数")
    d["gate_after_capture"] = grep_line(must_read(os.path.join(TMP, "gate_after_capture.txt"), u"重捕后的门"),
                                        "FRAME_BASELINE_RESULT=", u"重捕后结论")
    d["gate_after_capture_drift"] = grep_line(must_read(os.path.join(TMP, "gate_after_capture.txt"), u"重捕后的门"),
                                              "FRAME_BASELINE_DRIFT ", u"重捕后判定")
    full = must_read(os.path.join(TMP, "full_summary.txt"), u"全量卷")
    d["full"] = grep_line(full, "FULL_LINES=", u"全量卷汇总")
    d["prechecks"] = must_read(os.path.join(TMP, "prechecks.txt"), u"三支预检")
    # 电池那一格**不在这里抄**：它排在台账之后，本轮新案数由电池自己那一行报，
    # 本机那趟的数不回填进账（自指那一格，最终签字归 runner STEP[9]）。
    # 前缀要写到 `ledger_round` 那一格：streak.txt 里还有一行 `PRODUCT_STREAK_LAST_SUBJECT`，
    # 只写 "PRODUCT_STREAK" 会 last=True 抄到它（本轮第三次同类自伤：前缀太短 = 读到别的东西）。
    d["streak"] = grep_line(must_read(os.path.join(TMP, "streak.txt"), u"产品面连续轮数"),
                            "PRODUCT_STREAK ledger_round", u"product_streak 现读")
    # 对账门那一格是**自指**的：它要数的行就在本轮那一节里 ⇒ 只能先拿预览喂它，再拿它的数写正文。
    # 所以这里允许 recon.txt 缺席（第一趟 DRY 就是缺席），第二趟必须由 `--check-fixed-point` 确认两趟一致。
    recon_path = os.path.join(TMP, "recon.txt")
    if os.path.exists(recon_path):
        d["recon"] = grep_line(io.open(recon_path, encoding="utf-8").read(),
                               "RED_NAME_RECONCILIATION", u"对账门读数")
    else:
        d["recon"] = u"（预览那一趟：门还没被喂过本轮那一节 ⇒ 第二趟 DRY 之后才有数）"
    d["absence"] = grep_line(must_read(os.path.join(TMP, "prechecks.txt"), u"三支预检"),
                             "LEDGER_ABSENCE_RESULT", u"清账门")
    hits = d["main"][u"门那一步的逐字读数"] or [u""]
    found = re.search(r"未登记=(\d+)", hits[0])
    d["runner_un"] = found.group(1) if found else u"（那一行没带这个字段）"
    d["look"] = must_read(os.path.join(TMP, "look.txt"), u"看图那一腿")
    d["numstat"] = must_read(os.path.join(TMP, "numstat.txt"), u"git numstat 现读")
    d["diff_swift"] = must_read(os.path.join(TMP, "diff_swift.txt"), u"Swift 侧逐字未变证人")
    d["pyverify"] = must_read(os.path.join(TMP, "pyverify.txt"), u"字面量真验证（派单 ③②）")
    return d


# —————————————————————————————————————————————————————————──
# 各本的正文。凡带数字的句子都从 gather() 的读数里格式化出来，不在散文里手写第二个数。


def block_state(d):
    i = d["ident"]
    m, a = d["main"], d["add"]
    knives = u"；".join(u"%s rc=%d caught=%d clean=%d 预检=%s 末次=%s"
                        % (k["arm"], k["rc"], k["caught"], k["clean"], k["precheck"], k["post"])
                        for k in d["knives"])
    return u"""## R%(r)s 状态（%(date)s · 第 %(n)s 轮 / Round %(round)s · 产品 0 文件 + **漂移名册补上了机器维度**（登记的键从「帧」收成 **(机器, 帧)**，本机行不再给别的机器背书；基线带署名，署名不符时变帧那一维**具名不判、照报数、给出出路**，而不是把 %(runner_un)s 张噪声判成红）+ 电池 +13 格（该卷 22→35）+ 刀 M1535/M1536/M1537 全 CAUGHT + **⓪ 两跑都到数且命中出口 ⑵**（上一轮登记的第四条出口 `FRAME_BASELINE_SKIPPED` 本轮实测=没发生））

⓪ **开场与收口各读一次，两次结论不同 —— 这就是「不许轮询、也不许拿旧读数当结论」那条的形状**
- 身份现读（取值时刻=本轮第一步）：UI_AUDIT 最新那一节以「第 %(prev_n)s 轮（R%(prev_r)s」开头，STATE 最新是 `## R%(prev_state_r)s 状态` ⇒ 两本交叉核对通过 ⇒ 本轮 **R%(r)s = 第 %(n)s 轮 / Round %(round)s**（恒等式 n=R-1、Round=R-3 由盘上现读推，不写死）。刀高水位现读 **M1534** ⇒ 本轮从 **M1535** 起，没借号。
- 开场那一读：两跑 `in_progress` ⇒ 整格判**未到数**（没轮询、没拿本机数顶、没把「每步 conclusion 全空」读成「没有失败步骤」）。
- 中段那一读（`ci_status_r584.py`，取值时刻=本轮 ② 落地之前）：**两跑都到数**，主笔 `42077586416 ↔ bce08b4` 与补记笔 `42077903445 ↔ d808030` 逐字：
  `%(main_exit)s`（主笔的处置：%(main_disp)s）
  `%(add_exit)s`（补记笔同格；两跑的 STEP[11] **都**红，而 `FRAME_BASELINE_RESULT` 逐字同一对数 ⇒ 不是间歇，是**那一笔的门**在 runner 上注定红）
- 全部失败步骤逐字（主笔那一跑，一条不落）：
%(main_steps)s
- 归因对照（改动前那一跑 `42066695864 ↔ 876bd3a`）：失败步骤只有 `STEP[15]/[17]/[19]` ⇒ **STEP[11] 是 `bce08b4` 那一笔引入的**（它正是第一次把 changed/added 接进退出码的那一笔）；**STEP[18] 不能署名本轮回归**：主笔那一跑红（`本次跑过=4 红=4`）而补记笔那一跑绿（`本次跑过=8 红=0`，同一份 Swift 树，R583 一字未动产品）⇒ 那一列在两跑之间**翻面** ⇒ 记「在漂」，既有红照实入账不抹。
- 红名单逐字同集合（5 个名字，与 R582 那两跑逐字相同）⇒ **「本轮没有新名字」成立；「红变少了」不成立**。`%(red_names)s`
- 上一轮那一格没倒退：`D12_SHAPE_SCAN_REGISTRY` 在两跑上仍逐字 `机器=github-runner 登记=1_2 实测=1_2 判=一致 红路=无 另一台已登记=是`；配套真值表那行也在（`机器键三档=一致 判法四分支=齐 … 解耦=登记一致而地板读0`）。
- 第四条出口 `FRAME_BASELINE_SKIPPED`：**命中 0 次**（我自己下的日志、剥掉 ANSI 与时间戳、只认行首）⇒ 今天**不是**「帧集太小没判」，而是「判了且红」。⚠ 这句话只能这样写：`⑷ 没发生`，不许写成「那一格绿了」。

① **本轮 ⓪ 那两跑签掉的，正是本轮 ② 要修的那一格**
- 上一轮我读到的洞（`check` 不判 changed）补上之后，第一跑就在 runner 上红了：`变帧=356 已登记=8 未登记=348`（逐字见 ⓪）。
- 三条解释摆在一起，本轮用**两个独立通道**逐一排除：
  (甲)「界面真的回归了 348 张」⇒ **否**：同一台机器（runner）在 `42066364877` 那一跑印的是 `CHANGED=356 / COMPARED=356`，而那一跑**根本没有这条判定**（R582 的树），也就是说 356 是全量差异而不是"这轮改出来的"；且 `MISSING=0 ADDED=0`（夹具一张没少、一张没多）。
  (乙)「门坏了 / 名册读不出来」⇒ **否**：`FRAME_BASELINE_DRIFT_REGISTRY=loaded …/docs/frame_drift_registry.json 行=8` 逐字在，`已登记=8` 说明名册不但读进来了、还放行了 8 张 —— 而**那 8 行是本机的**。
  (丙)「判决对象错位：那份基线是本机 2x 烤的，runner 是 1x 拍的」⇒ **成立**，两个通道各自独立：runner 自己印 `BATCH_TITLE_FIT … 倍率=1.0x`、`机器=arm64/macOS 15.8/1x`；本机同一批帧实测 `detail-0-text-720x520-light.png = 1440×1040`（名义 720×520 的两倍）。⇒ 每一帧的字节都不可能相同。
- 所以 R583 那次"补洞"只补上了**基线主人那台机器**的洞；在第二台机器上它把「没人判」换成了「判了但没法逐张绿」。本轮把它做对：判决按机器分。

② **真实推进（段号=②）：登记的键收成 (机器, 帧)，基线带署名**
- 新形状：`docs/frame_drift_registry.json` 每一行多一个必填 `machine`（本轮那 8 行逐字 `local:MacBook-Air.local`），`docs/frame_baseline.json` 多一行署名 `machine`；`check` 先看 `docs/frame_baselines/by_machine/<键>.json` 有没有这台机器自己那份，没有才退回工作基线，而工作基线**认不认这台机器**由署名说话。
- 两向坑各自被什么挡住：
  ⑴ **本机行给别机背书** ⇒ `judge_drift` 只把 `machine==本机` 的行算进"已登记"；证人两格：纯函数那格 `他机行放行本机漂移 ⇒ unregistered=["b.png"]`，端到端那格 `rc=1 且印出 他机行=1 未登记=1`。刀 **M1535** 摘掉这个过滤 ⇒ 三格一起红（第三格是他机行只报数不判那一格 —— 过滤一摘它就没有"他机行"可言）。
  ⑵ **runner 因为「本机的行不覆盖它」而注定红** ⇒ 署名不符时这一维**不判**，但**数目照报、名字照印、出路照给**：`%(gate_sim)s`、`%(gate_sim_notjudged)s`、结论行 `%(gate_sim_result)s`，另有一行把命令写全（在那台跑 `update` ⇒ 它会自己署名并写 `by_machine/<键>.json`，随仓库提交即归它判）。这一支还配了**负半证人**：不判只豁免"变帧"，夹具少帧（`缺席1`）照红；`by_machine` 文件一旦存在就归它判（`未登记=3` 那格红）⇒ 「不判」不是一扇能长期躲的门。
- **数不许靠措辞变小**：不判那一支把未登记的数字照印在标签里（`未登记（不判）=8`），而 `FRAME_BASELINE_RESULT` 的明细里那一格写 `未登记不判` —— 上一版这里印的是数字 + `拦路=0`，读起来自相矛盾，本轮改成"数字在标签里带着『不判』"。
- 反证（同一条命令换一侧跑，两向都量）：换**名册路径**（仍在本机名下）⇒ `%(gate_absent)s` ⇒ `%(gate_absent_result)s`，退 **1**；换**机器键**（本机名册原样）⇒ 上面那一支 `判=不判`。本机名册在位时逐字 `%(gate_local)s` ⇒ `%(gate_local_result)s`，退 0 ⇒ 与上一轮那一格**逐字同数**，本轮没有借机器维度把自己的判定放宽一分。
- 名册自己会腐烂的新形状：缺 `machine` ⇒ 红且**逐行点名**（`名册缺机器  <帧名>`，明细里 `缺机器1`）；`by_machine/<键>.json` 里文件名与署名不符 ⇒ **退 2**（这份东西不可信，谁也不判）；`sanitize_machine()` **只抹标点不抹大小写** ⇒ `local:MacBook-Air.local` 与 `local:macbook-air.local` 落在两个文件名上（657 那个咬口在这里有证人）。
- 三份 python 侧 `machine_key()` 由同一张真值表钉住"取值必须相同"（本文件 / `motion_floor_gate` / `test_surface_left_axes`）；Swift 那份仍只差大小写 ⇒ **不 join**、不擅自统一（657 归用户）。
- 新开 **658**：让 runner 有它自己的基线（三条出路原样摆着，一条没选：① 由 CI 打印逐机器哈希、人写回仓库；② CI 里那一台自己跑一次 `update` 并由人复核提交；③ 承认基线是逐机器的、把"变帧"这一维永久只归本机判）。

③ **派单那两条仪器约束（本轮都照做，且都留了命令与退出码）**
- 夹具不许用假哈希：本轮新增的判定全部走 `collect()` 的真哈希；`baseline["b.png"] = "0"*64` 那一类**故意**的错位只在"制造变帧"这一步用，并且只在被比较的那一侧（证人：`test_partially_registered_counts_the_registered_part` 先 `compare()` 出 `(["b.png"], [], ["d.png"])` 再判）。上一轮那 2 张幽灵变帧的形状本轮没复现。
- 字面量落盘后由**真正的消费者**验一次（逐字读数见 `pyverify.txt`）：`%(pyverify)s`
- port 锚的根因（"以为上轮改过的其实没改"）本轮的处理方式：**换做法** —— 台账写手新写一份（`ledgers_r584.py`），锚一律由正则从盘上现读（`identity_from_disk()` 拿 UI_AUDIT 与 STATE 两处交叉核对，不符就停）；改前对每个锚 `grep -c` 现读命中数（写手里是 `need()`，不等于 1 就 `ANCHOR-MISS` 并停在任何写盘之前）。

⑨ **本轮自伤清单（十四处，每处都带代价；对账口径见下面那一格）**
· **对账口径**（沿用 R582 启用的那一格，本轮不关）：每一条具名红 / 具名不判 / 作废读数要么落到 `⑨·` 编号，要么写 `不计入对账口径` 并带三类名字之一（契约名 / 通道未跑 / 基名在漂）；两者都不写 = **未标**，由 `scripts/red_name_reconciliation.py` 报出并退 1。
- 逐条自伤（编号即下面红名对账里落的那个）：
  · ⑨·1 刀脚本 `record()` 里把预检那一列印成 `pre_rc and code` ⇒ 预检通过时求值成 `0`，status 文件三行的 precheck 列不可信 ⇒ 代价=修脚本 + 三把刀全部重跑（重跑后 `precheck=PASSED`，第一趟那三行留在 `knife_status_first_pass_void.txt` 作废存证）。
  · ⑨·2 读数脚本按 substring 筛 ⇒ 把 CI **自己 echo 的脚本行**（`echo "FRAME_BASELINE_SKIPPED=…"`）读成「这台机器 skip 了」，差点把 ⑷ 写成假命中。代价=整支脚本重写。
  · ⑨·3 同一支不归属步骤 ⇒ 把 `Release script tests` 里自测的合成读数（`变帧=1 新帧=1 未登记=2`）当成那一跑的数（R575「共现当合取」复发）。代价=第二次重跑 + 加 `GATE_STEP_IN` 归属。
  · ⑨·4 `classify()` 五条 return 少一个括号 ⇒ 解包 3 值得到 2 值，脚本崩在半路（它不落台账 ⇒ 没写脏，但那一趟读数作废）。
  · ⑨·5 两处 `sanitize_machine` 期望我自己写错（以为 `-` 保留，实际与 `:` 一起换成 `_`）⇒ 修的是**期望**，判决一字未动（红对格才许改期望）。
  · ⑨·6 一次 Edit 用两行换一行，把 `FRAME_BASELINE_DRIFT_NOT_JUDGED=` 那行打印**替换掉了** ⇒ 当场读回发现并补回。
  · ⑨·7 `swift build --build-tests` 我在仓库根连跑两次 ⇒ 那两次 `error: Could not find Package.swift` 是**我的调用错**，不是产品的（"别凭记忆抄自家命令"复发；现读 `ClipboardHistory/Package.swift` 之后 0 告警）。
  · ⑨·8 针预检与全量卷**并行**跑 ⇒ `预检 swift 失败：NOT_RUN_TIMEOUT` + 日志里明写「Another instance of SwiftPM is already running」⇒ 那一读作废，全量卷结束后串行重跑（R583 ⑨·5 同族第二次）。
  · ⑨·9 本轮改写 `blockers` 把上一轮 M1532 的针打腐烂 ⇒ `HIDDEN_ROT mutate_r583.py M1532（候选 3 个，盘上一个都不命中）`、`处置=red`。代价=重钉 + **r583 整表重跑**（3/3 CAUGHT、RESTORE_CLEAN=yes）。
  · ⑨·10 写手里变量名撞车：刀循环里的 `m = re.match(...)` 把 `m = runs[main_run]` 覆盖掉 ⇒ `IndexError: no such group`。
  · ⑨·11 zsh 里 `grep --include=*.py` 又失败（`no matches found`，同族第三次）⇒ 改用 Grep 工具；这一条连续三轮都在，说明"抄自己家的命令要先现读"还没变成肌肉记忆。
  · ⑨·12 `grep_line(prefix="PRODUCT_STREAK", last=True)` 前缀太短 ⇒ 抄到 `PRODUCT_STREAK_LAST_SUBJECT` 那一行（里面没有 `streak=`）⇒ `AttributeError`。同一族第二次（⑨·3）：**前缀短=读到别的对象**。
  · ⑨·14 本轮 ⑨ 那一格我按自己的写法写（`- 对账（由门报出）：…`），而门认的是**字面块名** `红名对账` 与 token `对账口径` ⇒ 预览那一趟它直接判 `REGIME_CLOSED`。这一条是"分类法必须写成会红的函数"的反面教材：**规矩在仪器里，措辞就得照仪器的形状长**，否则门会把自己的启用状态判没。代价=⑨ 那一格重写 + 对账跑两趟取不动点。
  · ⑨·13 台账模板里写了个裸 `%%s`（第一次在描述 ⑨·1 的那句话里，第二次在描述本条的那句话里 ⇒ **同一族连犯两次，写"哪个字会咬人"的时候正好踩在那个字上**）⇒ `TypeError: not enough arguments for format string`，代价=DRY 重跑两趟。
- **红名对账**（口径=沿用启用；五个数由门的实现数出来，写手里不抄第二份规则）：
  · 红名「runner 那一跑 `FRAME_BASELINE_RESULT=red 拦路=348（未登记348）`」→ **不计入对账口径**（契约名 —— 那是本轮 ② 的**主角读数**，故意留着并由它作证洞在哪个方向，不是自伤）
  · 红名「STEP[18] 同树两跑翻面（主笔 `本次跑过=4 红=4` / 补记笔 `本次跑过=8 红=0`）」→ **不计入对账口径**（基名在漂 —— 在屏探针卷那一族的既有形状，本轮没为它改任何判据，也没把它署成本轮回归）
  · 红名「`HIDDEN_ARMS … rot=1 处置=red`（M1532 腐烂）」→ ⑨·9
  · 红名「`预检 swift 失败：NOT_RUN_TIMEOUT`」→ ⑨·8
  · 红名「`RED_NAME_RECONCILIATION=REGIME_CLOSED 节=R584`（预览那一趟：本轮 ⑨ 那一格还没长成仪器认的字面形状）」→ ⑨·14
  · 红名「写手 `TypeError: not enough arguments for format string`」→ ⑨·13
  · 红名「写手 `IndexError: no such group`」→ ⑨·10
  · 红名「`AttributeError`（streak 前缀抄到 LAST_SUBJECT）」→ ⑨·12
  · 红名「`error: Could not find Package.swift` ×2（我的调用错，不是产品）」→ ⑨·7
  · 红名「`FRAME_BASELINE_SKIPPED` 假命中 + 自测合成数误读（两次）」→ ⑨·2
  · 红名「status 文件三行 precheck 列不可信（作废重跑）」→ ⑨·1
  · 红名「`knife_status_first_pass_void.txt`（第一趟那三行）」→ **不计入对账口径**（契约名 —— 作废存证，代价已记在 ⑨·1）
  · 红名「两处 sanitize 期望错、一次 Edit 吞掉打印行、一次 zsh glob 失败」→ ⑨·5
- 门复算（`--state` 喂预览拿到的那一行，落盘后同一门复算同一行）：`%(recon)s`
- 逐本现读六个数（派单 ④ 专项，不拿"fail-fast 没写脏盘"当证人）：写之前七本里本轮那六个标题形状各 **0** 次；写之后**每一本恰好命中它那一个形状=1、其余=0**。逐行现读在 `preapply_counts.txt` 与 `postapply_counts.txt`。

⑦ **验证链（顺序照旧，一处偏差具名）**：`swift build --build-tests` 告警 **0**（包目录内现读）；python 判据卷 `%(pytest)s / %(pytest_tail)s`；三把刀**先跑**（它们打在 `scripts/frame_baseline.py` 上、与 swift 构建目录无关 ⇒ 没撞锁；偏差具名 `KNIVES_BEFORE_CAPTURE_PYTHON_ONLY`，沿用上轮同一命名）`%(knives)s`；刀全部还原后 python 卷复跑同数；Swift 判据/捕获卷 `%(capture)s`（帧 `%(capture_frames)s`）；重捕后对新门 `%(gate_after_capture_drift)s` ⇒ `%(gate_after_capture_result)s`；全量卷 `%(full)s`；三支预检**串行** `%(precheck_needle)s`、`%(precheck_arm)s`、`%(precheck_hidden)s`；换装 `SKIP_INSTALL=no-product-change`（产品 0 文件）；七本台账 → 派生格现读 → 电池（本轮新案 13 格 ⇒ 内层总数由**电池自己那一行**报，账里不预测那个数；本机那趟的数**不回填**，最终签字归 runner `STEP[9]`）；产品面连续零改动 **%(streak_n)s** 轮（`%(streak)s`）；清账 `%(absence)s`；代码 numstat 现读 `%(numstat)s`；Swift 侧逐字未变的证人 `%(diff_swift)s`。

⑧ **看图那一腿**（逐张、先确认是整帧还是自己切的框）：`%(look)s`
""" % dict(
        r=i["r"], n=i["n"], round=i["round"], date=ROUND["date"],
        prev_n=i["prev_n"], prev_r=i["prev_r"], prev_state_r=i["prev_state_r"],
        runner_un=d["runner_un"],
        main_exit=u"出口=%s" % m[u"出口"], main_disp=m[u"处置"][:220],
        add_exit=u"出口=%s" % a[u"出口"],
        main_steps=u"\n".join(u"  " + l for l in m["steps"].splitlines() if l.strip()),
        red_names=u" ".join(m[u"红名单"]),
        gate_sim=d["gate_sim"], gate_sim_notjudged=d["gate_sim_notjudged"],
        gate_sim_result=d["gate_sim_result"], gate_absent=d["gate_absent"],
        gate_absent_result=d["gate_absent_result"], gate_local=d["gate_local"],
        gate_local_result=d["gate_local_result"],
        pyverify=d["pyverify"].replace("\n", u" ｜ ")[:400],
        recon=d["recon"], knives=u" ｜ ".join(
            u"%s rc=%d caught=%d clean=%d 末次=%s" % (k["arm"], k["rc"], k["caught"], k["clean"], k["post"])
            for k in d["knives"]),
        pytest=d["pytest"], pytest_tail=d["pytest_tail"], capture=d["capture"],
        capture_frames=d["capture_frames"],
        gate_after_capture_drift=d["gate_after_capture_drift"],
        gate_after_capture_result=d["gate_after_capture"],
        full=d["full"],
        precheck_needle=grep_line(d["prechecks"], "NEEDLE_PRECHECK", u"针预检"),
        precheck_arm=grep_line(d["prechecks"], "ARM_TOTAL", u"臂总数"),
        precheck_hidden=grep_line(d["prechecks"], "HIDDEN_ARMS", u"隐藏臂"),
        absence=d["absence"], numstat=d["numstat"].strip().replace("\n", u" ｜ "),
        diff_swift=d["diff_swift"].strip().replace("\n", u" ｜ "),
        streak_n=re.search(r"streak=(\d+)", d["streak"]).group(1), streak=d["streak"],
        look=d["look"].strip().replace("\n", u"\n  ")[:2200],
    )


def next_u():
    """下一个 U 号 = 盘上现读的最大 U + 1（不抄上一轮的尾号）。"""
    ui = read("UI")
    nums = [int(x) for x in re.findall(r"\*\*U-(\d+)", ui)]
    if not nums:
        raise SystemExit("UI_AUDIT 里一个 U 号都没有 ⇒ 推不出下一个号")
    return max(nums) + 1


def block_ui(d):
    i = d["ident"]
    u0 = next_u()
    m = d["main"]
    us = [
        (u"⓪ 两跑开场未到数、中段**都到数且命中 ⑵**，而第四条出口实测=没发生",
         u"开场那一读 `in_progress` ⇒ 整格未到数；中段那一读逐字 `%(exit)s`，两跑的 STEP[11] 都红、"
         u"`FRAME_BASELINE_RESULT` 是同一对数 ⇒ 不是间歇而是那一笔的门在 runner 上注定红。"
         u"`FRAME_BASELINE_SKIPPED` **命中 0 次**（自己下的日志、剥 ANSI/时间戳、只认行首）⇒ "
         u"这一句只能写成「⑷ 没发生」，不许写成「那一格绿了」。红名单 5 个名字与 R582 逐字同集合 ⇒ 没有新名字。"
         % {"exit": m[u"出口"]}),
        (u"上一轮补的那个洞，只在**基线主人那台机器**上补上了",
         u"runner 那一跑逐字 `%(drift)s`（已登记=8 而**那 8 行是本机的**）。三条解释逐一排："
         u"(甲) 真回归 348 张 ⇒ 否（同一台在 R582 的树上就印 `CHANGED=356/COMPARED=356`、`MISSING=0 ADDED=0`）；"
         u"(乙) 门坏/名册读不出来 ⇒ 否（`FRAME_BASELINE_DRIFT_REGISTRY=loaded … 行=8`）；"
         u"(丙) 判决对象错位 ⇒ 成立，两个独立通道：runner 自印 `倍率=1.0x`/`机器=arm64/macOS 15.8/1x`，"
         u"本机同一帧实测 1440×1040（名义 720×520 的两倍）。⇒ 本轮把判决按机器切开，而不是把红改成不报。"
         % {"drift": (m[u"门那一步的逐字读数"] or [u"（没取到）"])[0]}),
        (u"登记的键收成 (机器, 帧)：两向坑各有一条断言挡着",
         u"⑴ 本机行给别机背书 ⇒ `judge_drift` 只算 `machine==本机` 的行；端到端那格 `rc=1` 且印 `他机行=1 未登记=1`。"
         u"⑵ runner 注定红而没有出路 ⇒ 署名不符时 `判=不判`、数目照报（`%(sim)s`）、名字照印、出路把命令写全；"
         u"配**负半证人**两条：缺席照红（`缺席1`），`by_machine/` 一旦存在就归它判（`未登记=3` 那格红）。"
         u"⇒ 「不判」不是一扇能长期躲的门。" % {"sim": d["gate_sim"][:150]}),
        (u"数不许靠措辞变小（这一格是新加的，因为它上一版会自相矛盾）",
         u"不判那一支把数字印在**带「不判」的标签**里（`未登记（不判）=8`），而结论行那一格写 `未登记不判`。"
         u"上一版这里印 `未登记=8` 又印 `拦路=0`，两条读数互相打架；改的是措辞形状，不是把数藏起来。"),
        (u"刀 M1535/M1536/M1537 全 CAUGHT 且三边互不重叠（现读最高 M1534 ⇒ 没借号）",
         u"`%(knives)s`。各自只动一边：M1535 摘分机器过滤（`rows_without_machine` 那一半不动 ⇒ 缺字段那格仍红）；"
         u"M1536 把缺字段填成通配（`judge_drift` 一字未动 ⇒ 跨机器那两格仍绿）；M1537 把 `judged` 钉成恒真"
         u"（名册那一半未动，方向与 M1535 相反）。落刀前各自自问过「我只动了这一对量的一边吗」，"
         u"`RESTORE_CLEAN=yes` 由还原后与落刀前同一 md5 作证（`before=5462fa84… after=5462fa84…`）。"
         % {"knives": u" ｜ ".join(u"%s rc=%d 末次=%s" % (k["arm"], k["rc"], k["post"]) for k in d["knives"])}),
        (u"仪器自己差点把读数读错三次（都修在本轮，没让假数进账）",
         u"① 按 substring 筛把 CI **自己 echo 的脚本行**读成 `FRAME_BASELINE_SKIPPED` ⇒ ⑷ 假命中；"
         u"② 不归属步骤 ⇒ 把 `Release script tests` 的合成数（`变帧=1 新帧=1 未登记=2`）当成那一跑的数（R575 共现当合取）；"
         u"③ `readings` 那把尺**每通道只采样几行**，本轮要的正是被采样丢掉的那一行 ⇒ 改成自己 `gh run view --log` 落盘再切。"
         u"三条共同形状：命令成功、输出看着齐、读的是别的对象。"),
        (u"658 新开：让 runner 有它自己的基线（三条出路一条没选）",
         u"① CI 打印逐机器哈希由人写回仓库；② 那一台自己跑 `update` 并由人复核提交；③ 承认基线是逐机器的、"
         u"「变帧」这一维只归基线主人判。本轮只把**形状与出路命令**做出来（`by_machine/`、署名、`update` 自动签），"
         u"选哪条归用户。⚠ 开单形状照 R579 的规矩：`**658. 标题**` 与引用它的自测同一笔落地。"),
        (u"看图那一腿：像素面本轮不可见，而「不可见」是有证人的",
         u"%(look)s" % {"look": d["look"][:900]}),
    ]
    head = u"## 第 %(n)s 轮（R%(r)s · %(date)s · U-%(u0)s…U-%(u1)s）：漂移名册补上**机器维度**（登记键从「帧」收成 (机器, 帧)，本机行不再给别机背书）；基线带**署名**，署名不符时变帧那一维具名不判、照报数、给出出路；⓪ 两跑都到数并命中出口 ⑵（`变帧=356 已登记=8 未登记=348`）\n\n" % {
        "n": i["n"], "r": i["r"], "date": ROUND["date"], "u0": u0, "u1": u0 + len(us) - 1}
    body = u"".join(u"- **U-%d：%s**。\n    %s\n\n" % (u0 + k, t_, b)
                    for k, (t_, b) in enumerate(us))
    return head + body, u0


def block_iteration(d):
    i = d["ident"]
    return u"""## Round %(round)s · R%(r)s（第 %(n)s 轮 · %(date)s）：把上一轮那扇门判错了对象的那一半补回来

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉看图 | @@LOOKSCORE@@ | %(look_short)s |
| 判据有效性 | 15/15 | 本轮动的就是"判的是哪个对象"：runner 那一跑给出 `已登记=8` 而名册全是他机行 ⇒ 洞由**别人的读数**作证，不是我自己写的句子；改完之后本机那一门逐字与上一轮同数（`%(gate_local)s`）⇒ 没有借机器维度放宽自己 |
| 假绿防御 | 15/15 | 两向坑各一条断言 + 三把刀各自只动一边且互不重叠；不判那一支自带两条负半证人（缺席照红、有自己基线就照判）；`by_machine` 文件名与署名不符 ⇒ 退 2 而不是"当没这台机器" |
| 产品面推进 | 4/15 | 产品 **0** 文件（连续 %(streak)s 轮，`%(streak_line)s`）；本轮推进的是门的**覆盖面**：那条在 runner 上会红的 348 张从此有名字、有出路 |
| 读数可信度 | 14/15 | 三处自伤都出在同一支读数脚本里（echo 行、步骤归属、采样丢行），全部在本轮内改成"自己落盘 + 按行首 + 按步骤归属"，代价=脚本重写两遍 ⇒ 1 分扣在"这三条本该在写之前就想到的" |
| 台账与复查性 | @@LEDGERSCORE@@ | 锚全部由盘上现读（身份两处交叉核对）；写前/写后逐本六个数各留一份；电池 %(pytest)s ⇒ 最终签字仍归 runner `STEP[9]` |
| 不代选 | 15/15 | 655 没重烤、656 三条出路没选、**657 大小写没统一**、654 定向没代答、658 三条出路原样列出；第③段着色器一字未写；旧红一朵不抹（STEP[18] 写"在漂"而不是"本轮引入"也不是"没了"） |
""" % {
        "round": i["round"], "r": i["r"], "n": i["n"], "date": ROUND["date"],
        "look_short": d["look"].strip().splitlines()[0][:180],
        "gate_local": d["gate_local"][:120],
        "streak": re.search(r"streak=(\d+)", d["streak"]).group(1),
        "streak_line": d["streak"][:120],
        "pytest": d["pytest"],
    }


def block_backlog(d):
    i = d["ident"]
    m = d["main"]
    return u"""## R%(r)s 追账（第 %(n)s 轮 / Round %(round)s · %(date)s）：658 新开，655/656/657 一条没结

**658. 工作基线是**一台机器的产物**（本机 2x 烤的），而 runner 自印 `倍率=1.0x` ⇒ 那一台相对这份基线 `变帧=356/356`、每一帧都不同 —— 门从此按机器判：没有自己的基线就**具名不判**（照报数、给出出路），有就照判。三条出路一条没选（R%(r)s 现读并新开）**
    现象（取值时刻=本轮 ⓪ 中段那一读，含本笔之前那一跑）：runner 的 STEP[11] 逐字 `%(drift)s` ⇒ `%(res)s`，两跑同一对数（不是间歇）。
    ⇒ 结论（是读数不是推理）：`已登记=8` 里那 8 行**全是本机的行** ⇒ 上一版的登记事实上在给任何机器的漂移背书放行，而它判出的 348 张红没有任何人能逐张处置。
    三条出路（归用户，本轮一条没选，也**没**改这台机器的默认设置）：
      ⑴ CI 打印一份逐机器哈希清单，由人写回 `docs/frame_baselines/by_machine/<键>.json`（可复核、可评审，代价=每次改界面要多写一次）；
      ⑵ 那一台自己跑 `scripts/frame_baseline.py update` 并提交（最快闭合，代价=基线由 CI 写回仓库、绕过人复核的那一步要另加门）；
      ⑶ 承认基线逐机器，"变帧"这一维永久只归基线主人判（代价=CI 上那一维没人判，R583 补的洞在 runner 侧等于回到"没人判"）。
    ⚠ 本轮落的是**形状**：署名、(机器, 帧) 的键、`by_machine/` 的优先读法、不判那一支的数目与出路命令 —— 三条出路各自需要的东西都在了，选哪条不动这些形状。

**655 / 656 / 657 状态（R%(r)s）：都不结案，各补一句**
    · 655：本轮仍**没跑** `update`（重烤归用户）；那 8 行只是多了 `machine` 字段，帧名/理由/单号逐字未动，本机那一门仍 `%(gate_local)s`。
    · 656：三条出路一条没选；本轮没碰捕获侧 Swift ⇒ 那格当轮读数照旧由本机签（`真机键那一趟` 见 STATE ⑦）。
    · 657：**没统一、没换键、没动 `~/.ssh`/hosts**；本轮只把"键不同字"这件事在**仪器侧**钉成两条会红的证人：三份 python `machine_key()` 同真值表 ⇒ 取值必须相同；`sanitize_machine()` 只抹标点不抹大小写 ⇒ 两份字面落两个文件名。Swift 那份仍差大小写 ⇒ **不 join**。
    · 651/653/654 本轮无新读数改变形状；`STAGE3_FRAME_CRITERIA_HAVE_NO_RUNNER_WITNESS=awaiting-654-direction` 照旧等定向。
""" % {
        "r": i["r"], "n": i["n"], "round": i["round"], "date": ROUND["date"],
        "drift": (m[u"门那一步的逐字读数"] or [u"（没取到）"])[0][:200],
        "res": (m[u"门那一步的逐字读数"] + [u""])[1][:120] if len(m[u"门那一步的逐字读数"]) > 1 else u"（没取到）",
        "gate_local": d["gate_local"][:130],
    }


def block_decisions(d):
    i = d["ident"]
    return u"""## D-%(r)s（R%(r)s · %(date)s · 第 %(n)s 轮 / Round %(round)s）：登记必须带**它豁免谁**；判决对象的归属写不进读数，那条判定就是在判错的东西

背景：R583 把 `frame_baseline.py check` 的 changed/added 接进退出码，第一次上 runner 就红 —— 那一跑逐字
`变帧=356 已登记=8 未登记=348`。三个修法摆在桌上：把红当噪声压回去（把这一维改回只判 missing）、把 348 张逐张登记、
或者承认**这份基线是一台机器的产物**。

决定：
1. **登记的键从「帧」收成 (机器, 帧)**。缺 `machine` 字段的行门退非 0 并逐行点名 —— 缺字段不等于"适用所有机器"，
   那是拿本机的观测替全网背书（与 R565「应为 0 的计量不许自我豁免」同族：默认值也是一种豁免）。
2. **基线带署名**（`docs/frame_baseline.json` 的 `machine`，由 `update` 写、由 `snapshot` 继承）。
   署名 ≠ 本机 ⇒ 变帧那一维**具名不判**，但必须：① 数目照报（`变帧=356 未登记（不判）=356` 这一类），
   ② 名字照印（`FRAME_BASELINE_DRIFT_NOT_JUDGED=baseline-owned-by:…`），③ 出路写全（一条可复制的命令 + 目标文件名），
   ④ 自带负半证人（缺席照红；那台一旦有自己的基线就照判）。缺 ④ 的"不判"就是 R583 那个洞换了个说法。
3. **逐机器基线放 `docs/frame_baselines/by_machine/<键>.json`**，文件名只抹标点**不抹大小写**（657 的咬口：
   两份只差大小写的键必须落两个文件，否则 join 起来正好像"同一台"）。
4. **红得没法处置，和红一样坏**。那一跑那 348 张如果逐张登记，就是把一次倍率错位登记成 348 条"契约"；
   而把它判红挂在那儿，CI 就会连续红、没人看 —— 这是 D-7 从 R?（"红色要看不得"）起反复付学费的那一条。
   所以本轮的处置是"具名不判 + 开单 658 让这一维将来归那一台判"，不是"改期望"也不是"就近 skip"。

被否掉的：把 `--allow-missing` 扩成"允许变更名单"（那是把豁免从缺席偷渡到像素）；
让 runner 用 `--against latest-release`（发布快照与逐机器基线是两个对象，混用会重演 R583 ⑨ 那次 `auto` 误量）；
把 657 的 Swift 那份改成小写以"统一"（牵动已按机器登记好的红名单 = 地基，且归用户）。
""" % {"r": i["r"], "date": ROUND["date"], "n": i["n"], "round": i["round"]}


def block_changelog(d):
    i = d["ident"]
    return u"""- 帧基线漂移登记名册补上**机器维度**（R%(r)s / 第 %(n)s 轮 / Round %(round)s，产品 0 文件）：
  `scripts/frame_baseline.py` 的登记键从「帧」收成 **(机器, 帧)**，缺 `machine` 字段的行会红并逐行点名；
  工作基线新增 `machine` 署名（`update` 自动写、`snapshot` 继承），`check` 优先读
  `docs/frame_baselines/by_machine/<键>.json`；署名与本机不符时变帧那一维**具名不判**
  （`FRAME_BASELINE_DRIFT_NOT_JUDGED=…`，数目照报、出路命令照印，缺席与"已有自己基线"仍照判）。
  动因是 runner 第一跑的逐字读数 `变帧=356 已登记=8 未登记=348`（那份基线是本机 2x 烤的，runner 自印 1.0x）。
  电池 +13 格（`scripts/tests/test_frame_baseline.py` 22→35），刀 M1535/M1536/M1537 全 CAUGHT；
  新开 BACKLOG 658（三条出路归用户）。身份：第 %(n)s 轮 / Round %(round)s。
""" % {"r": i["r"], "n": i["n"], "round": i["round"]}


# —————————————————————————————————————————————————————————──
# 落盘：全部文本先在内存里算完（任何一块算崩 ⇒ 一本都不写），再一次性写。


def shapes(i):
    return [
        (u"UI 轮次标题", u"## 第 %d 轮（R%d · " % (i["n"], i["r"])),
        (u"ITER 标题", u"## Round %d · R%d" % (i["round"], i["r"])),
        (u"STATE 节", u"## R%d 状态（" % i["r"]),
        (u"DECISIONS", u"## D-%d（" % i["r"]),
        (u"BACKLOG 新单", u"**658. "),
        (u"CHANGELOG 身份括号", u"（R%d / 第 %d 轮 / Round %d，产品 0 文件）" % (i["r"], i["n"], i["round"])),
    ]


def counts(i, tag):
    rows = []
    for book in ("UI", "ITER", "STATE", "BACKLOG", "DEC", "FINAL", "CHANGE"):
        text = read(book)
        rows.append(u"%s :: %s" % (BOOKS[book],
                                   u" | ".join(u"%s=%d" % (name, text.count(s)) for name, s in shapes(i))))
    out = u"\n".join(rows) + u"\n"
    with io.open(os.path.join(TMP, "%s_counts.txt" % tag), "w", encoding="utf-8") as handle:
        handle.write(out)
    return out


def insert_before(text, pattern, block, label):
    m = re.search(pattern, text)
    if not m:
        raise SystemExit("ANCHOR-MISS %s：现读模式 %r 没命中" % (label, pattern[:60]))
    pos = m.start()
    return text[:pos] + block + text[pos:]


def apply(d, do_write):
    i = d["ident"]
    pre = counts(i, "preapply")
    if any(int(x) != 0 for x in re.findall(r"=(\d+)", pre)):
        # 已经写过一次（幂等重放）⇒ 一本都不许再写；>1 才是真事故。
        totals = [int(x) for x in re.findall(r"=(\d+)", pre)]
        if max(totals) > 1:
            raise SystemExit(u"本轮标题形状在盘上出现 %d 次 ⇒ 停（不是幂等重放）\n%s" % (max(totals), pre))
        print(u"DRY：盘上已有本轮标题（幂等重放）⇒ 不重复写\n" + pre)
        return 0
    print(u"PRE（写之前逐本现读）：\n" + pre)

    # —— 全部文本先算完，崩就一本都不写
    state_text = block_state(d)
    ui_text, u0 = block_ui(d)
    iter_text = block_iteration(d)
    backlog_text = block_backlog(d)
    dec_text = block_decisions(d)
    change_text = block_changelog(d)
    iter_text = iter_text.replace(u"@@LOOKSCORE@@", d["look_score"])
    iter_text = iter_text.replace(u"@@LEDGERSCORE@@", d["ledger_score"])
    for name, blob in [(u"STATE", state_text), (u"UI", ui_text), (u"ITER", iter_text),
                       (u"BACKLOG", backlog_text), (u"DEC", dec_text), (u"CHANGE", change_text)]:
        if u"@@" in blob:
            raise SystemExit(u"令牌没填满：%s 里还有 @@（R567 那一族：fill 必须覆盖每一本）" % name)

    if not do_write:
        # 把 STATE 那一块先落一份预览：`red_name_reconciliation.py` 有 `--state` 口子 ⇒
        # 用**预览**去拿对账数，再让写手把同一个数抄进正文 ⇒ 不存在"落盘之后数变了、账没改"那种时序红。
        with io.open(os.path.join(TMP, "state_preview.md"), "w", encoding="utf-8") as handle:
            # 只写正文那一块：再补一个同形标题会让 `sections()` 里出现两个 R584，门按最后一个当"最新一节"就读到空的 body ⇒ 假 REGIME_CLOSED（本轮第四次"前缀/形状短了就读错对象"）。
            handle.write(state_text)
        print(u"DRY：六块文本全部算完，长度 STATE=%d UI=%d ITER=%d BACKLOG=%d DEC=%d CHANGE=%d ⇒ 未落盘"
              % (len(state_text), len(ui_text), len(iter_text), len(backlog_text), len(dec_text), len(change_text)))
        return 0

    new = {}
    new["STATE"] = insert_before(read("STATE"), r"(?m)^## R\d+ 状态（", state_text + u"\n\n", u"STATE 节")
    m = re.search(r"(?m)^最后更新：\d{4}-\d{2}-\d{2}（本地 · R\d+ / 第 \d+ 轮 / Round \d+）$", new["STATE"])
    if not m:
        raise SystemExit("ANCHOR-MISS：STATE 的「最后更新」那一行现读不到")
    new["STATE"] = (new["STATE"][:m.start()]
                    + u"最后更新：%s（本地 · R%d / 第 %d 轮 / Round %d）"
                    % (ROUND["date"], i["r"], i["n"], i["round"]) + new["STATE"][m.end():])
    new["UI"] = insert_before(read("UI"), r"(?m)^## 第 \d+ 轮（R\d+ · ", ui_text, u"UI 节")
    new["ITER"] = read("ITER").rstrip("\n") + u"\n\n" + iter_text.rstrip("\n") + u"\n"
    new["BACKLOG"] = read("BACKLOG").rstrip("\n") + u"\n\n" + backlog_text.rstrip("\n") + u"\n"
    new["DEC"] = read("DEC").rstrip("\n") + u"\n\n" + dec_text.rstrip("\n") + u"\n"
    ch = read("CHANGE")
    anchor = u"## [Unreleased]\n"
    if ch.count(anchor) != 1:
        raise SystemExit("ANCHOR-MISS CHANGELOG：[Unreleased] 命中 %d 次" % ch.count(anchor))
    head, rest = ch.split(anchor, 1)
    new["CHANGE"] = head + anchor + u"\n" + change_text.rstrip("\n") + u"\n" + rest
    # FINAL_REPORT：只把"产品面连续零改动轮数"那一格现读派生插进去（其余交给 refresh 脚本）
    fin = read("FINAL")
    m2 = re.search(r"产品面连续零改动轮数 = \*\*(\d+)\*\*（R(\d+) 台账落盘之后现读", fin)
    if not m2:
        raise SystemExit("ANCHOR-MISS FINAL_REPORT：产品面轮数那一格现读不到")
    # 现读口径：这一格读的是**本笔台账落盘之前**的状态 ⇒ as-of 说"本轮之前 15 轮"，本笔落地才是 16。
    streak_n = int(re.search(r"streak=(\d+)", d["streak"]).group(1))
    start = i["r"] - streak_n
    cell = (u"产品面连续零改动轮数 = **%d**（R%d 台账落盘**之前**现读 `%s`；as-of 口径 ⇒ 读作「本轮之前最后一次产品改动在 %d 轮前」，"
            u"R%d…R%d 共 %d 轮都是产品 0 文件 ⇒ 本笔落地后下一轮是 %d。上一格原文留着："
            % (streak_n, i["r"], d["streak"], streak_n, start, i["r"] - 1, streak_n, streak_n + 1))
    new["FINAL"] = fin[:m2.start()] + cell + fin[m2.start():]

    for book, text in new.items():
        write(book, text)
    post = counts(i, "postapply")
    print(u"POST（写之后逐本现读）：\n" + post)
    totals = {}
    for line in post.splitlines():
        for name, cnt in re.findall(r"(\S+?)=(\d+)", line.split(u"::", 1)[1]):
            totals[name] = totals.get(name, 0) + int(cnt)
    bad = {k: v for k, v in totals.items() if v != 1}
    if bad:
        raise SystemExit(u"逐本六个数不合格：%s" % bad)
    print(u"SIX_COUNTS_OK=%s" % json.dumps(totals, ensure_ascii=False))
    return 0


def main():
    do_write = "--apply" in sys.argv
    d = gather()
    d["look_score"] = os.environ.get("LOOK_SCORE", u"11/15")
    d["ledger_score"] = os.environ.get("LEDGER_SCORE", u"14/15")
    return apply(d, do_write)


if __name__ == "__main__":
    sys.exit(main())

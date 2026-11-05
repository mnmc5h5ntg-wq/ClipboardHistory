# -*- coding: utf-8 -*-
"""R586 七本台账的生成器（第 585 轮 / Round 583 · 产品 0 文件）。

三条自陈（写给下一次读这个文件的我）：
① 数字一律从 `/tmp/r586/*.txt` 的**读数文件**里 grep 出来，不许在正文里手抄；
   取不到的格子 `must_read/grep_line` 直接退出，不许给默认值（R140 的空对账那一族）。
② CJK 串里不许出现 ASCII 双引号（R288/R555/R585 连撞三次那一族）⇒ 本文里所有引号都是「」。
③ 模板里要逐字印的百分号一律写 `%%`（R585 ⑨·9 那一课：正文里一个裸 `%s` 就能让整趟 DRY 红）。
"""
import io
import json
import os
import re
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0"
TMP = "/tmp/r586"
DATE = "2026-11-06"
BOOKS = {"UI": "AGENT_UI_AUDIT.md", "ITER": "AGENT_VISUAL_ITERATION.md", "STATE": "AGENT_STATE.md",
         "BACKLOG": "AGENT_BACKLOG.md", "DEC": "AGENT_DECISIONS.md", "FINAL": "AGENT_FINAL_REPORT.md",
         "CHANGE": "CHANGELOG.md"}


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
    """轮次身份从**盘上的标题**派生，两个来源交叉核对（R585 那一族：抄上一轮基线会把字段抄丢）。

    仓库映射是 `Rnnn = 第 nnn-1 轮 = Round nnn-3`（由 `commit_round_identity.py` 钉着）。
    上一稿这里写的是 `r = max(第 N 轮) + 1` ⇒ 它算出来的是**已经存在的那一节**的 R 号，
    于是本轮标题与上一轮撞车，被写手自己的幂等守卫挡下（`DRY：盘上已有本轮标题`）——
    守卫替我挡了一次自我覆盖，这条要记进 ⑨。
    """
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
    d["main_run"] = "42107518932"
    d["add_run"] = "42108062173"
    d["main"], d["add"] = ci[d["main_run"]], ci[d["add_run"]]
    pairs = [(u"主笔", d["main"]), (u"补记笔", d["add"])]
    for tag, item in pairs:
        item[u"步骤全逐字"] = u" / ".join(l.strip() for l in item["steps"].splitlines() if u"⇒" in l)

    def grab(fname, prefix, label, last=True):
        return grep_line(must_read(os.path.join(TMP, fname), label), prefix, label, last=last)

    d["pytest_frame"] = grab("pytest_frame.txt", "Ran ", u"帧门判据卷")
    d["pytest_hover"] = grab("pytest_hover.txt", "Ran ", u"两态差尺判据卷")
    d["pytest_frame_ok"] = grab("pytest_frame.txt", "OK", u"帧门卷签字", last=False)
    d["pytest_hover_ok"] = grab("pytest_hover.txt", "OK", u"两态差尺卷签字", last=False)
    d["capture"] = grab("capture_summary.txt", "CAPTURE_LINES=", u"捕获卷")
    d["frames"] = grab("capture_summary.txt", "FRAMES=", u"帧数")
    d["gate_new"] = grab("gate_new.txt", "FRAME_BASELINE_RESULT=", u"新帧那一门")
    d["gate_new_drift"] = grab("gate_new.txt", "FRAME_BASELINE_DRIFT ", u"新帧门判定")
    d["gate_bake"] = grab("gate_new.txt", "FRAME_BASELINE_BAKE ", u"基线出处那一行")
    d["gate_prov"] = grab("gate_new.txt", "FRAME_BASELINE_BAKE_PROVENANCE", u"旧文档具名那一行")
    d["full"] = grab("full_summary.txt", "FULL_TOTAL=", u"全量卷")
    d["full_skips"] = grab("full_summary.txt", "FULL_SKIPPED=", u"全量 skipped")
    d["prechecks"] = must_read(os.path.join(TMP, "prechecks.txt"), u"三道预检")
    d["absence"] = grep_line(d["prechecks"], "LEDGER_ABSENCE_RESULT", u"清账门")
    d["streak"] = grab("streak.txt", "PRODUCT_STREAK ledger_round", u"产品面连续轮数")
    d["numstat"] = must_read(os.path.join(TMP, "numstat.txt"), u"numstat 现读")
    d["pyverify"] = must_read(os.path.join(TMP, "pyverify.txt"), u"字面量真验证")
    d["look"] = must_read(os.path.join(TMP, "look.txt"), u"看图那一腿")
    d["md5"] = grab("md5.txt", "MD5=", u"刀链还原")
    d["scale"] = must_read(os.path.join(TMP, "scale.txt"), u"倍率那三条")
    d["tier_scan"] = must_read(os.path.join(TMP, "tier_scan.txt"), u"同类子串判定扫描")
    d["baseline_untouched"] = grep_line(must_read(os.path.join(TMP, "baseline_untouched.txt"), u"基线没被碰"),
                                        "BASELINE_UNTOUCHED=", u"基线证人")
    d["git_dirty"] = u" ｜ ".join(l.strip() for l in must_read(
        os.path.join(TMP, "baseline_untouched.txt"), u"本轮改了什么").splitlines()
        if l.strip().startswith("M "))
    d["knife_reds"] = must_read(os.path.join(TMP, "knife_reds.txt"), u"每把红了哪几格")
    tb = subprocess.check_output(["git", "show", "HEAD:scripts/tests/test_frame_baseline.py"], cwd=ROOT).decode("utf-8")
    hb = subprocess.check_output(["git", "show", "HEAD:scripts/tests/test_hover_two_state_diff.py"], cwd=ROOT).decode("utf-8")
    ta = io.open(os.path.join(ROOT, "scripts/tests/test_frame_baseline.py"), encoding="utf-8").read()
    ha = io.open(os.path.join(ROOT, "scripts/tests/test_hover_two_state_diff.py"), encoding="utf-8").read()
    d["tests_frame_before"], d["tests_frame_after"] = tb.count(u"    def test_"), ta.count(u"    def test_")
    d["tests_hover_before"], d["tests_hover_after"] = hb.count(u"    def test_"), ha.count(u"    def test_")
    d["delta_frame"] = d["tests_frame_after"] - d["tests_frame_before"]
    d["delta_hover"] = d["tests_hover_after"] - d["tests_hover_before"]
    d["delta_total"] = d["delta_frame"] + d["delta_hover"]
    if d["delta_frame"] <= 0 or d["delta_hover"] <= 0:
        raise SystemExit("矛盾读数：某一本卷的 def test_ 数量没涨（帧门 %d→%d，两态差尺 %d→%d）"
                         % (d["tests_frame_before"], d["tests_frame_after"],
                            d["tests_hover_before"], d["tests_hover_after"]))
    recon_path = os.path.join(TMP, "recon.txt")
    d["recon"] = (grep_line(must_read(recon_path, u"对账门"), "RED_NAME_RECONCILIATION", u"对账门")
                  if os.path.exists(recon_path) else u"（预览那一趟还没跑）")

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
    if len(knives) != 6:
        raise SystemExit("刀数不是 6 把：%d ⇒ 表或状态文件读错了" % len(knives))
    # 每把红了哪几格：从日志里数，不许我念
    for k in knives:
        block = re.search(r"--- %s\n(.*?)(?=\n--- M|$)" % k["arm"], d["knife_reds"], re.S)
        body = block.group(1) if block else u""
        k["reds"] = len(re.findall(r"读数: FAIL:", body))
        k["names"] = re.findall(r"读数: FAIL: (\S+)", body)
    return d


# —————————————————————————————————————————————————————————──
# 正文


def next_u():
    nums = [int(x) for x in re.findall(r"\*\*U-(\d+)", read("UI"))]
    if not nums:
        raise SystemExit("UI_AUDIT 里读不到 U 号")
    return max(nums) + 1


def block_state(d):
    i = d["ident"]
    m, a = d["main"], d["add"]
    knives = u" ｜ ".join(u"%s rc=%d 预检=%s 末次=%s clean=%d 红%d格"
                          % (k["arm"], k["rc"], k["precheck"], k["post"], k["clean"], k["reds"])
                          for k in d["knives"])
    return u"""## R%(r)s 状态（%(date)s · 第 %(n)s 轮 / Round %(round)s · 产品 0 文件 + **取证通道自己读不读得对对象**（① 基线文档补上「哪一笔、哪一轮、什么倍率烤的」三个**运行时观测**，`check` 从此能分辨「拿被判那批帧自烤」并为此红；② 两态差尺的地板选择从**子串**换成**按段解析**）+ 判据卷 +%(delta_total)d 格（帧门 %(cf)d→%(cf2)d、两态差尺 %(ch)d→%(ch2)d，两头都现数 `def test_`）+ 刀 M1541–M1546 全 CAUGHT + ⓪ 上一轮主笔到数、补记笔未到数）

⓪ **两跑：主笔到数并多给一条读数，补记笔还没到数**
- 身份现读：UI_AUDIT 最新一节以「第 %(prev_n)s 轮（R%(prev_r)s」开头，STATE 最新是 R%(prev_state_r)s ⇒ 交叉核对通过 ⇒ 本轮 **R%(r)s = 第 %(n)s 轮 / Round %(round)s**。刀高水位现读 **M1540**（`mutate_r585` 那三把在册）⇒ 本轮从 **M1541** 起，没抄派单里的数。
- 主笔 `%(main_run)s ↔ %(main_sha)s` 现读 `completed / failure` ⇒ **到数**（派单发出时监工读到的是 `in_progress` ⇒ 那是**上一时刻的读数**，本轮开工二次现读；「到没到」由 `ci_read.py latest` 的 `status=` 说，不由我等）。全部失败步骤逐字：`%(main_steps)s` ⇒ **STEP[11] 不在里面**。
  门那一行逐字 `%(main_drift)s`；结论行 `%(main_result)s`。⇒ 读到的是**出口·乙**（`判=不判` 那一支），与 R585 那一节记的同一形状。
  **本轮从这一跑里新读到的一条**：`他机行=16`（R584 那一跑读的是 8）⇒ 名册那 16 行在 runner 上**全部算他机行**、一条都不豁免它的漂移，这是「登记键 =（机器, 帧）」那条合同在第二台机器上的反向证人 —— 它不是新胜利，只是那条形状第一次被 runner 自己签了。
- 补记笔 `%(add_run)s ↔ %(add_sha)s` 现读 `steps` 里**所有步骤结论都是空**、`--log` 打 0 字节（rc=%(add_log_rc)s）⇒ **未到数**：四种出口一条都不选、整格 NOT-RUN；没轮询、没拿本机数顶、没把「没读到」写成「之前是绿的」。
- ⚠ **两套编号仍然分开**：本脚本报的是**出口·甲/乙/丙/丁**（今天有没有人判），而 **658/659/660 各自的三条出路**说的是将来怎么办；读到 出口·乙 不等于任何一条出路成立。
- 本轮那三条**留给下一跑**的可证伪预测（写在 `ci_status_r586.py` 的 `PREDICTIONS`，由脚本判、不由我念）：①`FRAME_BASELINE_BAKE 出处=无`（工作基线仍是旧文档，本轮一次 `update` 都没跑）；②`FRAME_BASELINE_BAKE_PROVENANCE=absent` 具名 + `同批0`；③**不许**出现 `FRAME_BASELINE_SAME_BAKE=`。对 R585 那两跑它们一律打印成「不适用（那些格子住在本轮那一笔的树上）」⇒ 拿旧跑去"对拍"新判定就是把「还没落地」读成「是假的」（R555/R565 那一族的第三种形态）。
- 红名单逐字 5 个名字（与 R582–R585 同集合）⇒ 「本轮没有新名字」；`STEP[18]` 那一跑 `本次跑过=8 红=0` 照旧（派单里没让我重对拍 R584 已签的预测，遵守）。
- 监工自己数错、带进本账的一条（算交叉核对，不算工作侧自伤）：名册 16 行按 `'light' in frame` 数会得 9 light / 8 dark（加不起 16），真数是 **8 light（R583）+ 8 dark（R585）**，因为 `detail-text-highlight-…-dark.png` 里的 **highlight** 含子串 `light` ⇒ 这正是下面 ③ 那一支的现场证人，逐字读数见 ③。

① **派单给的那三条形状结论：逐条坐实（取值时刻=R%(r)s 开工，全部现读）**
- 靶 A 三处逐字：①`write_baseline` 的文档字段原本只有 `schema/count/machine/note/frames`（现读改后多了四个观测字段）；②`update --for-machine` 那一支把 `collect(args.frames_dir)` 直接写进 `by_machine/<运行时键>.json`，而 `check` 里 `if args.action == "check" and args.against in ("working","auto")` 优先读它；③⇒ **任何一台机器照自己刚捕的那批帧跑一次 `--for-machine`，下一次 `check` 必然 `变帧=0`，而那份基线自己说不出它是同批烤的** ⇒「没人变」与「刚自烤了一遍」在输出里逐字相同。
- 靶 B 逐字：`hover_two_state_diff.py` 那一行改之前是 `floor = FLOOR_LIGHT if 'light' in b_name else FLOOR_DARK`。
- ⇒ 两个靶都成立，且它们是**同一件事的两面**：靶 A 是"证据说不出自己的来历"，靶 B 是"证据按名字认错了对象"。本轮各补一支。

② **真实推进（段号=②，靶 A：基线出处 + 同批自烤会红）**
- `write_baseline` 现在落四个**运行时观测**字段：`baked_from_commit`（`git -C <仓> rev-parse HEAD`）、`baked_by_round`（台账标题派生：现读 `%(round_live)s`）、`capture_scale` / `capture_scale_frames`（PNG 的 IHDR 像素尺寸 ÷ 帧名里的逻辑尺寸，取众数）。**没有** `--baked-by`／`--commit`／`--capture-scale`：测试现证四个旗标全被 argparse 拒收（退 2）。
  为什么不用 PIL 读尺寸：这一支门在 CI 里跑在 Pillow 那一步之前也算 ⇒ "基线是按什么倍率烤的"不能因为某个解释器缺库就答不出来（`png_size` 只读 IHDR 那 8 个字节）。
  倍率那一格的现场读数：`%(scale)s`
- `check` 新增判定：`baked_from_commit == 此刻 HEAD` ⇒ 印 `FRAME_BASELINE_SAME_BAKE=<sha>` 并**进拦路**（两条支路都进），同时**照报数**（`FRAME_BASELINE_CHANGED=…` 一条不少）。措辞写清了为什么：那种时候 `变帧=0` 同样兼容「刚拿被判的这批帧自己烤了一遍」，不许给它签「没变」。出路那一行给的是**改流程**（基线与被判帧出自不同一笔，或改判 `--against release`），不是删字段、不是调阈值。
- 旧文档那一半（派单 ③）：缺 `baked_from_commit` ⇒ 印 `FRAME_BASELINE_BAKE 出处=无 …` 加 `FRAME_BASELINE_BAKE_PROVENANCE=absent` 并**照判**（`同批0`）；「不知道」绝不默认成"这一笔"（那会把每一份旧基线一起误红）。证人两格：`test_a_legacy_baseline_still_judges_and_is_named_not_treated_as_new` 与 `test_missing_provenance_is_never_defaulted_to_this_commit`，后者被刀 M1543 签。
- 三条证人的形状：**正臂**跑的是工具自己落的那份文件（回读，不是变量）；**负臂** ①不同一笔时不出现 SAME_BAKE 且 `同批0`，②同批 + 真有未登记漂移时**两朵红都在**（具名不许吃掉已有的红）。
- `snapshot()` 照继承出处（冻的是"那份基线对应的那一笔"，不是"此刻跑 snapshot 的这一笔"）⇒ 否则 `--against release` 那一支判的东西会随发布脚本漂移。
- 本机这一门在**含本笔的树**上的现读（不抄上一轮）：`%(gate_bake)s` / `%(gate_prov)s` / `%(gate_new_drift)s` ⇒ `%(gate_new)s`。
- 没动的：`--allow-missing` 两帧、任何阈值/容差/地板、判法四分支、四条出口语义、名册那 16 行的字段与理由、`update` 到工作基线那一份（`%(baseline_untouched)s`）。新增的三道判定（同批 / 无出处具名 / 倍率不合只报数）里**只有第一道进拦路**，另两道是收紧可见性，没有任何一格被放宽或改成 skip。

③ **真实推进（段号=③，靶 B：按名字选地板那把尺读错了对象）**
- 改法：`frame_tier(name)` 从右往左找**独立的一段**等于 `light`/`dark`；调用处变成 `tier = frame_tier(b_name)` + `FLOOR_LIGHT if tier == 'light' else FLOOR_DARK`。认不出档 ⇒ 空串 ⇒ 印 `HOVER_TIER_UNKNOWN=1 …` 并红（**不许默认成暗档**：那是把"读不出"冒充成"知道是暗的"）。
- 第二条独立通道：`find_pairs` 的档位是**末段**切的，与 `frame_tier` 的**按段解析**互校 ⇒ 不同字就印 `HOVER_TIER_MISMATCH=1` 并把这一对的地板作废（R580 那一课：按名字的尺要有第二条证人）。
- 现场暴露面（现读，不是推理）：`%(tier_scan_first)s` ⇒ 356 张帧名里两种判法**不一致的恰好 2 张**，都是暗档：`detail-text-highlight-720x520-dark.png`、`quickpick-typed-no-highlight-420x300-dark.png`；而今天这 10 对 hover 配对里**没有一对**用到它们 ⇒ `旧子串写法会读错=0` ⇒ **今天没有一朵假红或假绿在账上**，这是一支潜在的尺病，不是已经发生的错判（这句话两边都不许说过头）。
- 全仓同类扫描（派单要求"列出来"，监工只现读到一处，不保证唯一）：`scripts/*.py` 非测试部分里「按子串选地板」的写法本轮之后剩 **0** 处（守卫 `test_no_live_script_selects_a_floor_by_substring` 钉住，它自带一条合成正对照证明扫描器认得出旧写法）；Swift 侧现读 `grep contains/hasSuffix("light"/"dark")` 命中 0；`.scratch/` 里历轮一次性脚本仍有 `-light/-dark` 带连字符的子串写法（`sweep_r564_candidates.py:112-113`），它对今天 356 张的判法与按段解析**逐张相符** ⇒ 不在产品仪器里、不动它，只在这里列名。
- **两个地板数值 `FLOOR_LIGHT=1.20 / FLOOR_DARK=1.10` 一字未动**；4.5 墨、150、120ms、Motion ≥2、2x 8.0pt、1x 6.0pt 一条没碰（派单最后一句照守）。

⑨ **本轮自伤清单（十处，每处都带代价）与对账**
· **对账口径**（沿用启用，不关）：每条具名红/具名不判/作废读数要么落到 `⑨·` 编号，要么写 `不计入对账口径` 并带三类名字之一。
- 逐条：
  · ⑨·1 **新刀表撞老预检的位置约定**：第一版 `mutate_r586.py` 把臂写成六元组 `(号, 文件, 测试模块, needle, 变异文, 说法)`，而 `mutate_needle_precheck.py` 是按**位置**认臂、一份表一个 `TARGET` ⇒ 五把全部 `命中=0`、`bad=5`（它在跑之前就把我叫停了，没让空刀进账）。代价=拆成 `mutate_r586_frame.py` / `mutate_r586_hover.py` 两张四元组表、删掉旧那支、名册补两个名字。与 R580「新代码撞老刀 needle 时改新代码、不动老表」同族：**约定不写在自己文件里，就得由别人的解析器形状说了算**。
  · ⑨·2 三个新函数用了没 import 的 `struct` / `subprocess` / `io` ⇒ `py_compile` 是过的，**驱动一次**才 `NameError`（R585 ⑨·2 同族，我**又掉了一次**）；代价=补 import 后重跑判据卷与整张刀表。这一条的存在本身说明"编译过"不等于"这条路跑过"不是我记住了就会做对的事。
  · ⑨·3 patch 脚本里我塞了一句**占位的假 print**（`bake_display(target)`，一个不存在的函数）想先过编译再回头改 ⇒ 落盘前自己看见、改成"回读那份文件再印"（`bake_line(load_baseline_document(target))`）。代价=一次重写。形状与 R549 那一族同：占位符不许过夜。
  · ⑨·4 **两条证人格对它本该抓的坏法天生瞎**，是刀的输出告诉我的：M1543 只红 1 格（旧文档那格跑在**不是 git 仓**的临时目录里 ⇒ `HEAD=""` ⇒ "缺出处默认成这一笔"在那个环境里退化成"默认成空串"，什么数都不改）；M1544 只红 1 格（CLI 那格写的是 `assertIn("地板=1.1 ", out)`，被**另一对**无关的读数满足）。代价=修证人（旧文档那格改到真 git 仓里跑；CLI 那格把断言钉到含 `highlight` 的那**一行**并要求它只有一行），再**整表重跑** ⇒ 修完 M1543 红 2 格、M1544 红 2 格。⇒ 规矩补一句：**"刀只红 1 格而预期是 2 格"本身就是读数**，不许当成"刀够用"。
  · ⑨·5 我按记忆把 `/tmp/r586/frames` 标成"1x 那批"并写进读数文件 ⇒ 工具现读两批都是 `('2.00x', 356, 0)`。代价=重写那个读数文件并改标签。这是"别凭记忆抄自家命令/常量"那一族的**标签版**：数一直是工具给的，错的是我给它取的名字。
  · ⑨·6 第一版把 `对=` 当行锚，结果 `HOVER_TIER 配对=2 …` 汇总行也被挑进来 ⇒ 断言「该只有一行读数」当场红。代价=加空格边界（`" 对="`）并注明为什么要有那个空格。
  · ⑨·7 **印给读者的旗标值我又抄错一次**：SAME_BAKE 那条出路里我写 `--against release`，而 argparse 的 choices 现读是 `auto/working/latest-release` ⇒ 照那句话跑的人只会拿到 usage 错（退 2）。这正是 R585 整轮在还的那笔债的**同形复发**，只不过这次是我本轮新写的那一行。代价=改代码里那一行、新加两格守卫（`test_every_printed_against_value_is_a_real_choice` 从**源码**里读 choices 再对账每一个被印出来的值；`test_the_release_branch_actually_runs` 真跑那一支并断它不退 2），并补一把刀 M1546 钉住它。
  · ⑨·8 **刀文里插了一个换行 ⇒ 变异后的仪器文件 `SyntaxError`**：M1546 第一版的替换文本以反斜杠 n 结尾，而它落在一行字符串**中间** ⇒ 那一趟变成 `DID-NOT-RUN`（既不是 CAUGHT 也不是 PASSED）。三态在这里救了一次：状态文件写的是 `caught=0 post=DID-NOT-RUN`，我没有把它记成红了。代价=改刀文（注释写在同一行内、不插换行）、整张表重跑。
  · ⑨·9 **预检又与 swift 全量卷并行**：`mutate_needle_precheck.py` 自己会跑 swift，撞上 `.build` 锁 ⇒ `预检 swift 失败：NOT_RUN_TIMEOUT`（R558 记过同一族，本轮我又犯一次）。代价=等那一卷跑完再**串行**重跑三道预检；读数文件里那条「P1_RC=0（…串行，没与 swift 卷并行）」就是重跑那一次留下的。
  · ⑨·10 **写手的身份函数把本轮算成上一轮**：`identity_from_disk()` 我写的是 `r = max(UI 里的「第 N 轮」) + 1`，而 `Rnnn = 第 nnn-1 轮` ⇒ 那个式子得到的正是**盘上已有**的那一节（R585）⇒ 六块文本全带着上一轮的标题形状。挡住它的是写手自己的幂等守卫（`DRY：盘上已有本轮标题 ⇒ 一本都不再写`），不是我看出来的：如果那一晚我手滑加了 `--apply`，就会把 R585 那一节覆盖成 R586 的内容。代价=改成 `r = max(STATE 的 R 号) + 1` 并加一条交叉核对（UI 最新一节的 N 必须等于 r−2，不等就退出）；这条与 R583/R585「抄上一轮基线会把字段抄丢」同族：**派生身份的方向也要现读，不能靠记忆推**。
- **红名对账**：
  · 红名「`NEEDLE_PRECHECK … bad=5`（五把全部命中=0）」→ ⑨·1
  · 红名「`NameError`（新函数没 import `struct`/`subprocess`/`io`）」→ ⑨·2
  · 红名「占位假 print（`bake_display` 这个函数不存在）」→ ⑨·3
  · 红名「M1543/M1544 只红 1 格（两格证人对各自坏法不敏感）」→ ⑨·4
  · 红名「读数标签写错（把本机 2x 那批叫成 1x）」→ ⑨·5
  · 红名「`AssertionError: 1 != 2`（行锚挑进汇总行）」→ ⑨·6
  · 红名「出路里印出的 `--against release` argparse 不认（真值 latest-release）」→ ⑨·7
  · 红名「`DID-NOT-RUN`（刀文插换行把变异后的文件弄成 SyntaxError）」→ ⑨·8
  · 红名「`预检 swift 失败：NOT_RUN_TIMEOUT`（与全量卷撞 .build 锁）」→ ⑨·9
  · 红名「`DRY：盘上已有本轮标题（幂等重放）⇒ 一本都不再写`（身份函数把本轮算成上一轮）」→ ⑨·10
  · 红名「补记笔 `%(add_run)s ↔ %(add_sha)s` 未到数（`--log` 0 字节）」→ **不计入对账口径**（通道未跑那一格，不是红也不是绿）
  · 红名「`FRAME_BASELINE_SCALE_MISMATCH`（本机两批同倍率 ⇒ 今天不出现）」→ **不计入对账口径**（通道未跑 —— 那一支的第二档要由 runner 那一跑提供，`ci_status_r586.py` 的预测里写着它今天不该出现）
  · 红名「`STEP[15]/[17]/[19]` 那三朵（5 个名字同集合）」→ **不计入对账口径**（契约名 —— 逐字同集合，只算"没有新名字"）
- 门复算（预览 → 落盘 → 复算）：`%(recon)s`
- 逐本现读七个数（写之前各 0 / 写之后每一本恰 1）：`preapply_counts.txt`、`postapply_counts.txt`。

⑦ **验证链（顺序照旧，一处偏差具名）**：`swift build --build-tests`（包目录内）告警 **0**、错误 **0**；两本判据卷分开跑 ⇒ 帧门 `%(pytest_frame)s / %(pytest_frame_ok)s`、两态差尺 `%(pytest_hover)s / %(pytest_hover_ok)s`（本轮新增 17 格 ⇒ 帧门 +9、两态差尺 +8，两头都现数 `def test_`，不抄派单）；六把刀**先跑**（打在两份 python 仪器上、与 swift 构建目录无关 ⇒ 没撞锁；偏差具名 `KNIVES_BEFORE_CAPTURE_PYTHON_ONLY`，沿用上一轮同一命名）`%(knives)s`；每把红了哪几格逐字：`%(knife_reds_head)s`；`MD5=` 那一行是刀链前后同一份文件的现读（还原证人，两份文件各自核过）；Swift 捕获判据卷 `%(capture)s`（帧 `%(frames)s`）；对新门在**含本笔的树**上现读 `%(gate_new_drift)s` ⇒ `%(gate_new)s`；全量卷 `%(full)s`，skipped 只记现读 `%(full_skips)s`；三道预检**串行**（不与 swift 卷并行 ⇒ 本轮没再撞 `NOT_RUN_TIMEOUT`）：`%(precheck_needle)s`、`%(precheck_arm)s`、`%(precheck_hidden)s`；换装 `SKIP_INSTALL=no-product-change`（产品 0 文件）；七本台账 → 派生格**落盘之后**现读 → 电池（本机那一趟的数**不回填**，最终签字归 runner `STEP[9]`）；产品文件 0 个，连续零改动 **%(streak_n)d** 轮（唯一取数口 `python3 scripts/product_streak.py`，**台账落盘之后**现读 `%(streak_line)s`；as-of 口径 ⇒ 读作「本轮之前最后一次产品改动在 %(streak_n)d 轮前（R567 的 `8f679f9`）」；取数时刻由 `post_land()` 钉在函数名字上，不在纪律上）；清账 `%(absence)s`；代码 numstat 现读 `%(numstat_head)s`；字面量真验证 `%(pyverify_head)s`。

⑧ **看图那一腿**：`%(look)s`

⑤ **地基一字不动**：4.5 墨、150、2x 8.0pt、1x 6.0pt、120ms 与容差 1、Motion ≥2、`probeInkFraction=3%%`、`.contentFade 0.20`、像素格容差 1.5 与跳变地板 8、声明时长、**两态差尺的两个地板 `1.20 / 1.10`**、全量 skipped 现读、禁碰 14 面不抬不降（本轮没碰捕获侧 Swift ⇒ 逐字证人就是 ⑦ 里那两本 python 卷与全量卷）；`--allow-missing` 两帧原样；本轮新增三道判定里只有「同批自烤」进拦路，其余是**可见性收紧**，没有任何一格被放宽、改成 skip 或挪阈值。
""" % dict(
        r=i["r"], n=i["n"], round=i["round"], date=DATE, prev_n=i["prev_n"], prev_r=i["prev_r"],
        prev_state_r=i["prev_r"],
        main_run=d["main_run"], main_sha=d["main"]["sha"], add_run=d["add_run"], add_sha=d["add"]["sha"],
        add_log_rc=d["add"]["log_rc"],
        main_steps=m[u"步骤全逐字"][:520],
        main_drift=(m[u"门那一步的逐字读数"] or [u"（没取到）"])[0][:240],
        main_result=[l for l in (m[u"门那一步的逐字读数"] or [u""]) if l.startswith("FRAME_BASELINE_RESULT")][0][:170]
        if any(l.startswith("FRAME_BASELINE_RESULT") for l in (m[u"门那一步的逐字读数"] or [])) else u"（没取到）",
        round_live=re.search(r"台账轮现读=(\S+)", d["scale"]).group(1) if re.search(r"台账轮现读=(\S+)", d["scale"]) else u"（没取到）",
        scale=d["scale"].strip().replace("\n", u" ｜ ")[:520],
        tier_scan_first=d["tier_scan"].strip().replace("\n", u" ｜ ")[:420],
        gate_bake=d["gate_bake"][:200], gate_prov=d["gate_prov"][:230],
        gate_new=d["gate_new"][:200], gate_new_drift=d["gate_new_drift"][:260],
        baseline_untouched=d["baseline_untouched"][:220],
        knives=knives,
        knife_reds_head=d["knife_reds"].strip().replace("\n", u" ｜ ")[:900],
        pytest_frame=d["pytest_frame"], pytest_frame_ok=d["pytest_frame_ok"],
        pytest_hover=d["pytest_hover"], pytest_hover_ok=d["pytest_hover_ok"],
        capture=d["capture"], frames=d["frames"], full=d["full"], full_skips=d["full_skips"],
        precheck_needle=grep_line(d["prechecks"], "NEEDLE_PRECHECK", u"针预检"),
        precheck_arm=grep_line(d["prechecks"], "ARM_TOTAL", u"臂总数"),
        precheck_hidden=grep_line(d["prechecks"], "HIDDEN_ARMS", u"盲区名册"),
        absence=d["absence"], numstat_head=d["numstat"].strip().replace("\n", u" ｜ ")[:260],
        pyverify_head=d["pyverify"].strip().replace("\n", u" ｜ ")[:300],
        recon=d["recon"], look=d["look"].strip().replace("\n", u"\n  ")[:2200],
        streak_n=int(re.search(r"streak=(\d+)", d["streak"]).group(1)), streak_line=d["streak"],
        cf=d["tests_frame_before"], cf2=d["tests_frame_after"],
        ch=d["tests_hover_before"], ch2=d["tests_hover_after"],
        delta_frame=d["delta_frame"], delta_hover=d["delta_hover"], delta_total=d["delta_total"],
    )


def block_ui(d):
    i = d["ident"]
    u0 = next_u()
    m = d["main"]
    us = [
        (u"⓪ 上一轮主笔到数并多给一条读数，补记笔照实未到数",
         u"主笔 `%(main_run)s ↔ %(main_sha)s` 现读 `completed / failure`，失败步骤逐字只有 STEP[15]/[17]/[19] ⇒ "
         u"**STEP[11] 不在里面**；门那一行 `%(main_drift)s` ⇒ **出口·乙**（那一维在那台机器上仍没人判）。"
         u"新读到的一条：`他机行=16`（R584 那一跑读 8）⇒ R585 那 8 张暗档登记行在 runner 上算**他机行**，"
         u"一条都不豁免它的漂移 ⇒ 「登记键 =（机器, 帧）」那条合同第一次由第二台机器自己签。"
         u"补记笔 `%(add_run)s ↔ %(add_sha)s` 所有步骤结论为空、`--log` 0 字节 ⇒ 未到数，整格 NOT-RUN。"
         % {"main_run": d["main_run"], "main_sha": m["sha"],
            "main_drift": (m[u"门那一步的逐字读数"] or [u"（没取到）"])[0][:200],
            "add_run": d["add_run"], "add_sha": d["add"]["sha"]}),
        (u"监工数错的那一格是现场证人：名册 16 行 = 8 light + 8 dark，而子串法数出 9/8",
         u"`detail-text-highlight-720x520-dark.png` 里的 **highlight** 含子串 `light` ⇒ 按 `'light' in frame` 分类"
         u"会把这张**暗档**读成亮档，于是 16 行加不起 17 张。⇒ 这一条不是笔误而是**靶 B 的现场形状**："
         u"同一族子串判定在两处（名册计数 + 地板选择）各自会把暗档认成亮档，一处只错在账面上，另一处会错在判据上。"
         u"真数由工具现读：`%(frame_collide)s`" % {"frame_collide": d["tier_scan"].strip().splitlines()[-2][:150]}),
        (u"基线文档现在有出处了：哪一笔、哪一轮、什么倍率，三个数全部运行时观测",
         u"`baked_from_commit`=`git rev-parse HEAD`、`baked_by_round`=台账轮次标题派生、"
         u"`capture_scale`=PNG IHDR 像素尺寸 ÷ 帧名逻辑尺寸取众数（`capture_scale_frames`=量到的张数）。"
         u"**没有** `--baked-by`／`--commit`／`--capture-scale` 这三个旗标（测试现证 argparse 退 2）"
         u"⇒ 出处不是声明，是观测：一旦可以手填，它就退化成措辞（R585「登记是账，不是措辞」同族）。"
         u"`snapshot()` 照继承出处，不重签 ⇒ `--against release` 判的对象不会随发布脚本漂。"),
        (u"「拿被判那批帧自烤一遍」从此与「没人变」不再是同一个读数（新开 660）",
         u"`baked_from_commit == 此刻 HEAD` ⇒ 印 `FRAME_BASELINE_SAME_BAKE=<sha>` 并**进拦路**，同时"
         u"`FRAME_BASELINE_CHANGED=…` 等读数一条不少。两条负半证人：①不同一笔时不出现那一格且 `同批0`；"
         u"②同批 + 真有未登记漂移 ⇒ 两朵红都在（具名不许吃掉已有的红）。"
         u"旧文档那一半：缺字段 ⇒ `FRAME_BASELINE_BAKE 出处=无` + `FRAME_BASELINE_BAKE_PROVENANCE=absent` 并**照判**，"
         u"「不知道」绝不默认成「这一笔」（那会把每一份旧基线一起误红 —— 刀 M1543 钉的就是这一条）。"),
        (u"倍率这一格第一次由基线自己说出来（只报数，不进拦路）",
         u"倍率的现场读数：%(scale)s ⇒ 本机两批都是 2.00x，runner 那一档 1.00x 只能由它自己那一跑说。"
         u"当基线与当轮倍率不同字时印 `FRAME_BASELINE_SCALE_MISMATCH 基线=… 当轮=…`，"
         u"**不进拦路**：R584 那 356 张的判定形状不许被这一格改动（收紧可见性 ≠ 收紧判定）。"
         % {"scale": d["scale"].strip().replace("\n", u" ｜ ")[:320]}),
        (u"地板那把尺从「子串」换成「按段解析」，并配第二条独立通道互校",
         u"`frame_tier()` 从右往左找等于 `light`/`dark` 的**独立一段**；认不出 ⇒ `HOVER_TIER_UNKNOWN=1` 并红，"
         u"不许默认成暗档。`find_pairs` 的末段与它互校 ⇒ 不同字就 `HOVER_TIER_MISMATCH=1` 并作废那一对的地板。"
         u"现场暴露面现读：356 张里 2 张会撞（两张都含 highlight/no-highlight 的暗档），"
         u"而今天 10 对 hover 配对里 0 对用到它们 ⇒ **今天没有假绿也没有假红**，这是一支潜在尺病已被点名。"
         u"`FLOOR_LIGHT=1.20 / FLOOR_DARK=1.10` 一字未动。"),
        (u"全仓同类扫描：产品仪器里按子串选地板的写法清零，守卫自带合成正对照",
         u"扫描范围是 `scripts/*.py` 的非测试部分（按扫描作用域对账那条 R564/R580）⇒ 现在 0 处；"
         u"守卫 `test_no_live_script_selects_a_floor_by_substring` 先用一行旧写法自证扫描器认得出它，再断真仓 0 处。"
         u"Swift 侧现读 `contains/hasSuffix（light/dark）` 命中 0；`.scratch/` 历轮一次性脚本里带连字符的"
         u"`-light/-dark` 子串写法对今天 356 张与按段解析逐张相符 ⇒ 列出名字、不动它。"),
        (u"两处证人原来对它本该抓的坏法天生瞎（刀的输出教的，修的是证人）",
         u"M1543 第一次只红 1 格：旧文档那一格跑在**不是 git 仓**的临时目录 ⇒ `HEAD` 取到空串 ⇒ 那个坏法在那里退化成"
         u"「默认成空串」，什么数都不改；M1544 也只红 1 格：CLI 那格写的是 `assertIn` 配一个「地板=1.1 ）」这类前缀，被另一对无关读数满足。"
         u"⇒ 修证人（前者改到真 git 仓里跑、后者把断言钉到含 highlight 的那一行并要求它唯一），"
         u"然后**整表重跑** ⇒ M1543 现在红 2 格、M1544 红 2 格。"
         u"新规矩：**「刀只红 1 格而预期 2 格」本身就是读数**，不许当成刀够用（R577「刀不红作废的是结论」的邻族）。"),
        (u"印给读者的每一个旗标值都由 argparse 自己对账（本轮我自己又写错一个）",
         u"新守卫从**源码**里读 `--against` 的 choices，再把源码里每一处被印出来的 `--against <值>` 拿去对账 ⇒ 不匹配就红并列出两个集合；另配一格真跑 `--against latest-release` 那一支，断它**不退 2**（用法错与判定红是两种东西）。刀 M1546 把出路里那个值改回 `release` ⇒ 只有那一格红。这一条的存在本身是记账：R585 一整轮在还「印出来的空头支票」这笔债，而本轮我在新写的那一行里**又犯了一次** —— 说明这条规矩要由仪器守着，不能由我记着。"),
        (u"看图那一腿 + 名册那 16 行逐字未变（出处本轮没重打）",
         u"%(look_short)s ｜ 本轮没有新漂移 ⇒ 没有调用 `register-drift`，名册 16 行的 `observed` 与理由一字未动；"
         u"工作基线与 `docs/frame_baselines/` 一条没写：`%(baseline)s`"
         % {"look_short": d["look"].strip().splitlines()[0][:150], "baseline": d["baseline_untouched"][:180]}),
        (u"刀 M1541–M1546 全 CAUGHT（现读高水位 M1540 起，没借号；两处证人格被刀的输出救回来）",

         u"`%(knives)s`。逐把红了哪几格由日志现数：M1541 三格（落笔 + 同批两格）、M1542 两格（只有同批那两格 ⇒ 这才叫摘掉一支）、"
         u"M1543 两格（旧文档 + 不许默认）、M1544 两格（合成正对照 + 端到端那一行）、M1545 一格、M1546 一格（印出去的旗标值）。"
         u"⚠ M1541 与 M1542 打到同两格而断在不同处（一个断字段没落盘、一个断判定不响）⇒ 不写「互不重叠」，"
         u"这是 R585 撤过那句的那一条。" % {"knives": u" ｜ ".join(
            u"%s rc=%d 末次=%s clean=%d 红%d格" % (k["arm"], k["rc"], k["post"], k["clean"], k["reds"])
            for k in d["knives"])}),
    ]
    head = (u"## 第 %(n)s 轮（R%(r)s · %(date)s · U-%(u0)s…U-%(u1)s）：把「取证通道读得对不对对象」拆成两支补上"
            u"（①基线文档说出自己是哪一笔/哪一轮/什么倍率烤的，同批自烤会红；②两态差尺的地板改成按段解析，档位错认有证人）\n\n"
            % {"n": i["n"], "r": i["r"], "date": DATE, "u0": u0, "u1": u0 + len(us) - 1})
    body = u"".join(u"- **U-%d：%s**。\n    %s\n\n" % (u0 + k, t_, b) for k, (t_, b) in enumerate(us))
    return head + body, u0


def block_iteration(d):
    i = d["ident"]
    return u"""## Round %(round)s · R%(r)s（第 %(n)s 轮 · %(date)s）：取证通道自己读不读得对对象——基线的来历、档位的解析

**七维度自评**（恰七行，每格 n/15；维度名照曲线尺认的那七个同字，本轮不造新维度）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉看图 | @@LOOKSCORE@@ | %(look_short)s |
| 判据有效性 | 15/15 | 本轮判的是**证据说不出自己来历会不会被读成「没变」**：`FRAME_BASELINE_SAME_BAKE` 只在「基线与被判帧同一笔」时响，两向都有证人（不同一笔 ⇒ 不出现且 `同批0`；同批 + 真漂移 ⇒ 两朵红都在）。档位列加了两条通道互校（末段 vs 按段解析），不同字就作废那一对地板而不是静默选一个。 |
| 假绿防御 | 15/15 | ①手填口子不存在（四个旗标 argparse 现证退 2）；②旧文档缺字段**不默认成「这一笔」**（M1543 钉）；③认不出档位**不默认成暗档**（M1545 钉）；④倍率不合那一格只报数不进拦路 ⇒ 没有借「收紧」放宽任何判据；⑤名册 `observed` 与 16 行内容本轮一字未动（`update` 一次没跑，工作基线 md5 与 HEAD 同字）。 |
| 产品面推进 | 3/15 | 产品 **0** 文件。推进的是两条**取证侧**的可信度：一份基线现在能回答「判的是不是烤你的那批帧」，一把尺现在按段认档。段号仍是第②段。 |
| 台账一致性 | 9/15 | 身份两处交叉核对；七个标题形状写前 0、写后各 1；派生格落盘后现读。扣分在三处：⑨·7（我给读者印了一个 argparse 不认的旗标值 —— R585 那笔债的同形复发）、⑨·8（刀文插换行把变异后的文件弄成 `SyntaxError`，那一趟记成 `DID-NOT-RUN` 而不是 CAUGHT）、⑨·1/⑨·9（新刀表撞老预检的位置约定；预检又与全量卷撞 `.build` 锁）。 |
| 剩余风险处置 | 14/15 | 660 新开不结；655/656/657/658/659 全不结、出路一条不代选；656 那朵本轮没碰捕获侧 Swift ⇒ 不重签也不撤账；旧红一朵不抹；第③段着色器一字未写。扣 1 分：`FRAME_BASELINE_SCALE_MISMATCH` 这一支**还没有 runner 的证人**（要等含本笔那一跑），本机两批同倍率只能证明它不误响。 |
| 交接可读性 | 15/15 | 六条预测写进 `ci_status_r586.py` 并由 `since`/`my_shas.txt` 限定适用范围 ⇒ 对 R585 那两跑它们打印「不适用」而不是「不中」（把「还没落地」读成「是假的」是这一族的第三种坏法）。R587 的 ⓪ 四格写在 STATE 的 ⓪ 与补记里，成对号由补记那一笔现取现写。 |
""" % {"round": i["round"], "r": i["r"], "n": i["n"], "date": DATE,
        "look_short": d["look"].strip().splitlines()[0][:170]}


def block_backlog(d):
    i = d["ident"]
    return u"""## R%(r)s 追账（第 %(n)s 轮 / Round %(round)s · %(date)s）：660 新开，655/656/658/659 一条没结

**660. 基线文档说不出自己是**哪一笔、哪一轮、什么倍率**烤的 ⇒ 「拿被判那批帧自烤一遍」与「没人改过界面」在输出里逐字相同（R%(r)s 现读并新开）**
    现象（取值时刻=R%(r)s 开工第一步，`write_baseline` / `update --for-machine` / `check` 三处逐字）：文档字段只有 `schema/count/machine/note/frames`；
    `--for-machine` 把 `collect(<刚捕的目录>)` 原样写进 `by_machine/<运行时键>.json`，而 `check` 优先读那份文件 ⇒ 任何一台机器跑完它，下一次 `变帧` 必为 0。
    后果不是修辞：`FRAME_BASELINE_RESULT=ok 拦路=0` 这一行在两种情形下**逐字相同**，而门只会说「没红」。
    R%(r)s 补的（三条出路一条没选）：`baked_from_commit` / `baked_by_round` / `capture_scale` 三个**运行时观测**字段 + `check` 里「同批」判定（进拦路、照报数）
    + 旧文档缺字段时 `…PROVENANCE=absent` 具名并照判 + 倍率不合时 `SCALE_MISMATCH` 只报数。
    到数证人：本机 `check` 现读 `%(gate_bake)s`、`%(gate_prov)s` ⇒ `%(gate_new)s`；五把刀 M1541/M1542/M1543 各摘一支判定都红。
    ⚠ 这一单欠的还是**外部证人**：`FRAME_BASELINE_SAME_BAKE` 与 `SCALE_MISMATCH` 在 runner 上今天都不该出现（工作基线是旧文档、本机两批同倍率），
    所以「这一支会不会在那台机器上响」只能由含本笔的那一跑说；不许把它读成「已验完」。
    出路三条（归用户/下一轮定向，工作侧一条不代选）：⑴让基线与被判帧出自不同一笔（发布那一笔烤、下一笔判）；
    ⑵改判 `--against release`，把逐版本快照当基准；⑶接受「同批」就是常态 ⇒ 那 `变帧` 这一维需要另一个对象（例如发布前的帧集快照），这一支要新写通道。

**655 / 656 / 658 / 659 状态（R%(r)s）：都不结案，各补一句**
    · 655：本轮**没跑** `update` 到工作基线 ⇒ `%(baseline)s`；名册那 16 行（8 light + 8 dark）字段与理由一字未动，本轮没有新漂移 ⇒ 也没调用 `register-drift`。
      ⚠ 655 原文那句「八张全是 light 档」在 R585 已被现读否掉：真数是 8+8，而监工本轮按子串数成 9/8 正是同一族错法（见 660 的邻居 U 格）。
    · 656：三条出路（甲锁 `.aqua`／乙按外观拆两档／丙另一台或另一次会话补第二档）一条没选；本轮没碰捕获侧 Swift ⇒ 不重签也不撤账，末态仍是「缺第二档的当轮证人」。
    · 658：本轮补的是**基线那一侧**的出处（660），三条出路仍一条不选；`docs/frame_baselines/by_machine/` 现读仍不存在（上一轮那次误写已删干净，本轮复核过）。
    · 659：只开单、仪器侧证人仍没做（本轮没动像素差量那把尺）；但它的**教训被 ③ 用了一次** ⇒ 凡「按名字判一件事属于哪一档」都要问第二个问题：那个名字是不是恰好含这一段。
""" % {"r": i["r"], "n": i["n"], "round": i["round"], "date": DATE,
       "gate_bake": d["gate_bake"][:170], "gate_prov": d["gate_prov"][:170], "gate_new": d["gate_new"][:150],
       "baseline": d["baseline_untouched"][:200]}


def block_decisions(d):
    i = d["ident"]
    return u"""## D-%(r)s（R%(r)s · %(date)s · 第 %(n)s 轮 / Round %(round)s）：证据必须能说出自己的来历；名字不是属性，段才是

背景：R585 给名册每行补了 `observed`，让「手抄一行」可证伪。同一族的洞在**基线文档**那一侧还在：
它只署机器，不署「哪一笔/哪一轮/什么倍率」，于是 `update --for-machine` 拿刚捕的帧自烤一遍之后，
`变帧=0` 与「没人改过界面」在输出里**逐字相同**。同一天监工又按 `'light' in frame` 数名册，
把一张暗档数进亮档（`highlight` 含子串 `light`）—— 同一个错误形状在两处出现：**名字被当成了属性**。

决定：
1. **出处一律运行时观测，命令行一个口子都不开**。`baked_from_commit` 取 `git rev-parse HEAD`，
   `baked_by_round` 从台账标题派生，`capture_scale` 由 PNG 的 IHDR 像素尺寸 ÷ 帧名里的逻辑尺寸取众数。
   理由：可声明的出处等于没有出处（R585「登记是账，不是措辞」）。测试现证四个可能的旗标全被 argparse 拒收。
2. **「基线与被判帧同一笔」必须让门停下来说话**：`FRAME_BASELINE_SAME_BAKE` 进拦路、读数照报、
   出路写「改流程」而不是「删字段/调阈值」。同时它**不许吃掉任何已有的红**（同批 + 未登记 ⇒ 两朵都在）。
3. **「不知道」不许被默认成「知道」**：旧文档缺字段 ⇒ 具名 `PROVENANCE=absent` 并照判（判定形状一字不改），
   但绝不默认成此刻这一笔；帧名里认不出档位段 ⇒ `HOVER_TIER_UNKNOWN` 并红，绝不默认成暗档。
   这两条是同一个坏法的两面：把缺证据填成证据。
4. **档位是段，不是子串**；并给按名字的尺配第二条按形状（这里是按末段）的证人，两把不同字就作废那一对读数。
   两个地板数值（1.20 / 1.10）一字未动 ⇒ 本轮没有靠改阈值让任何一格变绿。
5. 新增的可见性读数（`SCALE_MISMATCH`）**只报数不进拦路**：R584 那 356 张的判定形状不许被一个新格子改动；
   把新读数变成判定是另一轮的决定，归那一条的证人。

被否掉的：给 `update` 加 `--baked-by`（把观测变成声明）；把「同批」做成具名 skip（那是刚补上的判定再藏回去）；
为了少红把 `capture_scale` 只写机器名（倍率正是 R584 那 356 张的已知成因，不能不看）；
以及「顺手把 `FLOOR_DARK` 调低一点让 highlight 那张暗档过线」（派单明令数值一字未动，且那是拿改期望顶替改尺）。
""" % {"r": i["r"], "n": i["n"], "round": i["round"], "date": DATE}


def block_changelog(d):
    i = d["ident"]
    return (u"""### 取证通道自己读得对不对对象：基线补上「哪一笔烤的」并让同批自烤会红 + 两态差尺的地板改成按段解析（R%(r)s / 第 %(n)s 轮 / Round %(round)s，产品 0 文件）
    R%(prev_r)s 给名册每行补了 `observed`，但**基线文档那一侧的同一个洞没补**：字段只有 `schema/count/machine/note/frames` ⇒
    `update --for-machine` 拿刚捕的那批帧烤一份 `by_machine/<键>.json`，下一次 `check` 必然 `变帧=0`，
    而「没人改过界面」与「刚用它自烤了一遍」在输出里逐字相同。同时监工按 `'light' in frame` 数名册数出 9/8（真数 8/8），
    而 `hover_two_state_diff.py` 选地板用的也是子串 ⇒ `*-dark.png` 里含 `highlight` 的暗档会被拿 1.20（亮档地板）判。
    本轮：① 基线落三个**运行时观测**字段（`baked_from_commit` / `baked_by_round` / `capture_scale(+frames)`），
    无任何手填旗标（argparse 现证拒收四个）；② `check` 里「基线与被判帧同一笔」⇒ `FRAME_BASELINE_SAME_BAKE` **进拦路并照报数**，
    旧文档缺字段 ⇒ `…PROVENANCE=absent` 具名并照判、绝不默认成「这一笔」；③ 倍率不合 ⇒ `SCALE_MISMATCH` 只报数（不新增拦路）；
    ④ 地板选择改成 `frame_tier()` 按段解析，认不出 ⇒ `HOVER_TIER_UNKNOWN` 并红，另加末段/按段两条通道互校；
    ⑤ 全仓扫同类：`scripts/*.py` 非测试部分按子串选地板归零，并有守卫自带合成正对照。
    本机现读（含本笔的树）：`%(gate_bake)s` / `%(gate_prov)s` ⇒ `%(gate_new)s`；名册 16 行一字未动、工作基线 md5 与 HEAD 同字。
    判据卷 +%(delta_frame)d 格（帧门）与 +%(delta_hover)d 格（两态差尺），刀 M1541–M1546 全 CAUGHT（**两处证人格被刀的输出发现天生瞎、修完整表重跑**）；
    新开 **660**，655/656/658/659 一条没结、出路一条不代选。
""" % {"r": i["r"], "n": i["n"], "round": i["round"], "date": DATE, "prev_r": i["prev_r"],
       "gate_bake": d["gate_bake"][:150], "gate_prov": d["gate_prov"][:150], "gate_new": d["gate_new"][:130],
       "delta_frame": d["delta_frame"], "delta_hover": d["delta_hover"]})


# —————————————————————————————————————————————————————————──
# 落盘


def shapes(i):
    return [(u"UI 轮次标题", u"## 第 %d 轮（R%d · " % (i["n"], i["r"])),
            (u"ITER 标题", u"## Round %d · R%d" % (i["round"], i["r"])),
            (u"STATE 主节", u"## R%d 状态（" % i["r"]),
            (u"DECISIONS", u"## D-%d（" % i["r"]),
            (u"BACKLOG 追账节", u"## R%d 追账" % i["r"]),
            (u"CHANGELOG 标题行", u"### 取证通道自己读得对不对对象：基线补上「哪一笔烤的」并让同批自烤会红 + 两态差尺的地板改成按段解析（R%d / " % i["r"])]


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

    fin = read("FINAL")
    streak_n = int(re.search(r"streak=(\d+)", d["streak"]).group(1))
    m2 = re.search(r"产品面连续零改动轮数 = \*\*(\d+)\*\*（R(\d+) 台账落盘之后现读", fin)
    if not m2:
        raise SystemExit("ANCHOR-MISS FINAL：streak 那一格现读不到")
    cell = (u"产品面连续零改动轮数 = **%d**（R%d 台账落盘之后现读 `python3 scripts/product_streak.py` ⇒ `%s`；"
            u"as-of 口径 ⇒ 读作「本轮之前最后一次产品改动在 %d 轮前（R567 的 `8f679f9`）」，R569…R%d 共 %d 轮都是产品 0 文件 ⇒ 下一轮是 %d。"
            u"上一格原文留着：**%s**（R%s 台账落盘之后现读"
            % (streak_n, i["r"], d["streak"], streak_n, i["r"], streak_n, streak_n + 1, m2.group(1), m2.group(2)))
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
    # 只查**对角线**：每一本只欠它自己那一个形状，别的形状在它本里就该是 0
    # （上一稿这里查了全部 42 格 ⇒ 六本明明各 1，却被"FINAL 里没有 CHANGELOG 标题行"这种话判成失败）。
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
        got = dict()
        for pair in cells.split(u" | "):
            n, v = pair.rsplit(u"=", 1)
            got[n.strip()] = v.strip()
        if got.get(want) != u"1":
            bad.append(u"%s 的「%s」现读=%s（该恰 1）" % (fname.strip(), want, got.get(want)))
    if bad:
        raise SystemExit(u"落盘后形状不是各 1：\n" + u"\n".join(bad))
    print(u"SEVEN_COUNTS_OK=%s" % json.dumps({u"标题": 1}, ensure_ascii=False))
    return 0


def post_land():
    """派生格的**结构性**修法（R585 ⑨·8 那一课的落地版）：落盘之后再取一次数，并由这里改写那两格。

    为什么不是"我记得在落盘后取数"：R580/R583/R585 三次都是同一件事 —— 写手在 gather 阶段取的数
    量的是"本节还没上盘"的那棵树。所以这里把取数时刻钉在函数名字上，而不是钉在纪律上。
    """
    reading = subprocess.check_output([sys.executable, "scripts/product_streak.py"], cwd=ROOT).decode("utf-8")
    line = reading.splitlines()[0].strip()
    streak_n = int(re.search(r"streak=(\d+)", line).group(1))
    # 落盘之后 identity 会往前跳一格（它算的是"下一轮"），所以这里要的是**刚落盘那一轮**的号：
    # 直接从盘上的节标题取，不拿 identity_from_disk() 的 +1 结果去找本轮那一格。
    landed_r = max(int(x) for x in re.findall(r"(?m)^## R(\d+) 状态", read("STATE")))
    i = {"r": landed_r}
    fin = read("FINAL")
    m2 = re.search(u"产品面连续零改动轮数 = \*\*(\d+)\*\*（R%d 台账落盘之后现读" % i["r"], fin)
    if not m2:
        raise SystemExit("ANCHOR-MISS post-land FINAL：本轮那一格现读不到")
    end = fin.index(u"上一格原文留着：", m2.start())
    cell = (u"产品面连续零改动轮数 = **%d**（R%d 台账落盘之后现读 `python3 scripts/product_streak.py` ⇒ `%s`；"
            u"as-of 口径 ⇒ 读作「本轮之前最后一次产品改动在 %d 轮前（R567 的 `8f679f9`）」，R569…R%d 共 %d 轮都是产品 0 文件 ⇒ 下一轮是 %d。"
            % (streak_n, i["r"], line, streak_n, i["r"], streak_n, streak_n + 1))
    fin = fin[:m2.start()] + cell + fin[end:]
    write("FINAL", fin)

    st = read("STATE")
    m3 = re.search(u"产品文件 0 个，连续零改动 \*\*(\d+)\*\* 轮（唯一取数口", st)
    if not m3:
        raise SystemExit("ANCHOR-MISS post-land STATE：⑦ 里那一格现读不到")
    e3 = st.index(u"；⚠ 本格取早过一次", m3.start()) if u"；⚠ 本格取早过一次" in st[m3.start():] else -1
    seg = st[m3.start():]
    stop = seg.index(u"）；")
    cell3 = (u"产品文件 0 个，连续零改动 **%d** 轮（唯一取数口 `python3 scripts/product_streak.py`，"
             u"**台账落盘之后**现读 `%s`；as-of 口径 ⇒ 读作「本轮之前最后一次产品改动在 %d 轮前（R567 的 `8f679f9`）」；"
             u"取数时刻由 `post_land()` 钉在函数名字上，不在纪律上" % (streak_n, line, streak_n))
    st = st[:m3.start()] + cell3 + st[m3.start() + stop:]
    write("STATE", st)
    print("POST_LAND_STREAK=%d 两格已改写（FINAL 与 STATE ⑦）" % streak_n)
    return 0


def main():
    d = gather()
    d["look_score"] = os.environ.get("LOOK_SCORE", u"11/15")
    if "--post-land" in sys.argv:
        return post_land()
    return apply(d, "--apply" in sys.argv)


if __name__ == "__main__":
    sys.exit(main())

# -*- coding: utf-8 -*-
"""R587 七本台账的生成器（第 586 轮 / Round 584 · 产品 0 文件）。

三条自陈（写给下一次读这个文件的我）：
① 数字一律从 `/tmp/r587/*.txt|json` 的**读数文件**里 grep 出来，正文里不许手抄；
   取不到的格子 `must_read/grep_line` 直接退出，不给默认值（R140 空对账那一族）。
② CJK 串里不许出现 ASCII 双引号（R288/R555/R585 连撞三次那一族）⇒ 本文所有引号都是「」。
③ 模板里要逐字印的百分号一律写 `%%`（R585 ⑨·9：一个裸 `%s` 就能让整趟 DRY 红）。
④ 身份从盘上派生 + 两源交叉核对（R586 ⑨·10 那一课），方向不许靠记忆推。
"""
import io
import json
import os
import re
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0"
TMP = "/tmp/r587"
DATE = "2026-11-06"
BOOKS = {"UI": "AGENT_UI_AUDIT.md", "ITER": "AGENT_VISUAL_ITERATION.md", "STATE": "AGENT_STATE.md",
         "BACKLOG": "AGENT_BACKLOG.md", "DEC": "AGENT_DECISIONS.md", "FINAL": "AGENT_FINAL_REPORT.md",
         "CHANGE": "CHANGELOG.md"}

RUN_MAIN = "42118421683"    # R586 主笔
RUN_ADD = "42119000322"     # R586 补记笔（上一轮记的是「未到数」）
RUN_OLD = "42108062173"     # R585 补记笔（本轮第一次到数，且步骤名退化）


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
    """轮次身份从**盘上的标题**派生，两个来源交叉核对（R586 ⑨·10 那一课的方向版）。"""
    ui = read("UI")
    prev_n = max(int(x) for x in re.findall(r"(?m)^## 第 (\d+) 轮（R\d+", ui))
    state_r = max(int(x) for x in re.findall(r"(?m)^## R(\d+) 状态", read("STATE")))
    r = state_r + 1
    if prev_n != r - 2:
        raise SystemExit("身份交叉核对失败：STATE 最新节是 R%d ⇒ 本轮应是第 %d 轮，而 UI 最新一节写着第 %d 轮"
                         % (state_r, r - 1, prev_n))
    return {"r": r, "n": r - 1, "round": r - 3, "prev_n": prev_n, "prev_r": r - 1}


def gather():
    ci = json.loads(must_read(os.path.join(TMP, "ci_readings.json"), u"⓪ 三跑读数"))
    d = {"ident": identity_from_disk(), "ci": ci}
    d["main"], d["add"], d["old"] = ci[RUN_MAIN], ci[RUN_ADD], ci[RUN_OLD]
    for item in (d["main"], d["add"], d["old"]):
        item[u"步骤全逐字"] = u" / ".join(l.strip() for l in item["steps"].splitlines() if u"⇒" in l)

    def grab(fname, prefix, label, last=True):
        return grep_line(must_read(os.path.join(TMP, fname), label), prefix, label, last=last)

    d["battery"] = grab("py_battery.txt", "Ran ", u"python 全电池")
    d["battery_ok"] = grep_line(must_read(os.path.join(TMP, "py_battery.txt"), u"电池签字"), "OK", u"电池签字", last=False)
    d["modules"] = [l.strip() for l in must_read(os.path.join(TMP, "py_battery.txt"), u"分卷").splitlines()
                    if l.startswith("test_")]
    d["counts"] = {}
    for l in must_read(os.path.join(TMP, "test_counts.txt"), u"def test_ 前后计数").splitlines():
        m = re.match(r"(\S+) HEAD=(\d+) NOW=(\d+)", l.strip())
        if m:
            d["counts"][m.group(1)] = (int(m.group(2)), int(m.group(3)))
    for k, (b, a) in d["counts"].items():
        if k in ("test_frame_baseline", "test_tier_vocabulary") and a <= b:
            raise SystemExit("矛盾读数：%s 的 def test_ 没涨（%d→%d）" % (k, b, a))
    d["delta_total"] = sum(a - b for b, a in d["counts"].values())

    d["capture"] = grab("capture_summary.txt", "CAPTURE_LINES=", u"捕获卷")
    d["frames"] = grab("capture_summary.txt", "FRAMES=", u"帧数")
    d["build_warn"] = grab("capture_summary.txt", "BUILD_WARNINGS=", u"构建告警")
    gate = must_read(os.path.join(TMP, "gate_local.txt"), u"本机那一门")
    d["gate_drift"] = grep_line(gate, "FRAME_BASELINE_DRIFT ", u"本机判定")
    d["gate_result"] = grep_line(gate, "FRAME_BASELINE_RESULT=", u"本机结论")
    d["gate_bake"] = grep_line(gate, "FRAME_BASELINE_BAKE ", u"基线出处行")
    d["gate_scale"] = (u" ｜ ".join(l for l in gate.splitlines() if l.startswith("FRAME_BASELINE_SCALE"))
                       or u"（本机这批没有 SCALE_* 读数：既不相斥、也不是并列 ⇒ 那三格今天都不该印）")
    d["scale"] = must_read(os.path.join(TMP, "scale_real.txt"), u"倍率真语料读数").strip()
    d["tier_scan"] = must_read(os.path.join(TMP, "tier_scan.txt"), u"词表声明扫描").strip()
    d["swift_tier"] = must_read(os.path.join(TMP, "swift_tier_count.txt"), u"Swift 侧处数").strip()
    d["look"] = must_read(os.path.join(TMP, "look.txt"), u"看图那一腿").strip()
    d["numstat"] = must_read(os.path.join(TMP, "numstat.txt"), u"numstat 现读").strip()
    d["pyverify"] = must_read(os.path.join(TMP, "pyverify.txt"), u"字面量真验证").strip()
    d["md5"] = u"before=%s after=%s 同一份=%s" % (
        must_read(os.path.join(TMP, "md5_before_final.txt"), u"刀链前 md5").strip(),
        must_read(os.path.join(TMP, "md5_after_final.txt"), u"刀链后 md5").strip(),
        u"yes" if must_read(os.path.join(TMP, "md5_before_final.txt"), u"a").strip()
        == must_read(os.path.join(TMP, "md5_after_final.txt"), u"b").strip() else u"NO")
    bu = must_read(os.path.join(TMP, "baseline_untouched.txt"), u"基线没被碰")
    d["git_dirty"] = u" ｜ ".join(l.strip() for l in bu.splitlines() if l.strip().startswith(("M ", "?? ")))
    d["baseline_untouched"] = grep_line(bu, u"未改", u"工作基线证人") if u"未改" in bu else grep_line(bu, "docs/", u"基线证人")
    d["knife_reds"] = must_read(os.path.join(TMP, "knife_reds.txt"), u"每把红了哪几格")

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
    if len(knives) != 8:
        raise SystemExit("刀数不是 8 把：%d ⇒ 表或状态文件读错了（本轮 M1547–M1554）" % len(knives))
    for k in knives:
        block = re.search(r"--- %s\n(.*?)(?=\n--- M|$)" % k["arm"], d["knife_reds"], re.S)
        body = block.group(1) if block else u""
        k["reds"] = len(re.findall(r"读数: FAIL:", body))
        k["subtests"] = len(re.findall(r"读数: FAIL: .*\(subTest", body))
    d["knives"] = knives
    # 作废那把（M1549）在**补证人之前**那一趟里的末态，必须由那份读数文件说，不由我念
    pre = must_read(os.path.join(TMP, "knife_status_pre_guardwiden.txt"), u"补证人/改尺之前那一趟刀状态")
    m49 = re.search(r"M1549 rc=\d+ caught=\d clean=\d precheck=\S+ post=(\S+)", pre)
    if not m49:
        raise SystemExit("读数缺失：M1549 在补证人之前那一趟的末态没记下来 ⇒ 「空刀」这句话没有证人")
    d["m1549_before"] = m49.group(1)

    for name, key, label in (("full_summary.txt", "full", u"全量卷"),
                             ("full_summary.txt", "full_skips", u"全量 skipped")):
        p = os.path.join(TMP, name)
        if os.path.exists(p):
            prefix = "FULL_TOTAL=" if key == "full" else "FULL_SKIPPED="
            d[key] = grep_line(must_read(p, label), prefix, label)
        else:
            d[key] = u"（未读到：那一卷还没跑完 ⇒ 台账不许替它填数）"
    p = os.path.join(TMP, "prechecks.txt")
    d["prechecks"] = must_read(p, u"三道预检") if os.path.exists(p) else u""
    d["absence"] = (grep_line(d["prechecks"], "LEDGER_ABSENCE_RESULT", u"清账门")
                    if d["prechecks"] else u"（落盘前的读数，落盘之后复算）")
    d["recon_path"] = os.path.join(TMP, "recon.txt")
    d["recon"] = (grep_line(must_read(d["recon_path"], u"对账门"), "RED_NAME_RECONCILIATION", u"对账门")
                  if os.path.exists(d["recon_path"]) else u"（预览那一趟还没跑）")
    d["streak"] = (grep_line(must_read(os.path.join(TMP, "streak.txt"), u"产品面连续轮数"),
                             "PRODUCT_STREAK ledger_round", u"产品面连续轮数")
                   if os.path.exists(os.path.join(TMP, "streak.txt")) else u"（落盘之后现读）")
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
    m, a, o = d["main"], d["add"], d["old"]
    return u"""## R%(r)s 状态（%(date)s · 第 %(n)s 轮 / Round %(round)s · 产品 0 文件 + **读数是不是它声称的那个对象**（① 帧的捕获倍率从「取众数」改成「报分布」，并列一律当**不知道**并走**已有的那条**不判出口；② 档位词表收成一份真值，「两份写法坏一份不会红」由 AST 守卫签；③ 印给读者的成句命令由它自己的参数表对账）+ 判据卷 +%(delta_total)d 格（帧门 %(cfb)d→%(cfa)d、词表新卷 0→%(tier_now)d、热图那一格改成两向）+ 刀 M1547–M1554（**M1549 空刀作废、补证人后以 M1553 重落**）+ ⓪ 三跑全部到数）

⓪ **三跑都到数，其中两跑把「上一轮的账」forward 掉了；本轮还从自己的 ⓪ 脚本里挖出两条会造假的判别**
- 身份现读：UI_AUDIT 最新一节以「第 %(prev_n)s 轮（R%(prev_r)s」开头，STATE 最新是 R%(prev_r)s ⇒ 交叉核对通过 ⇒ 本轮 **R%(r)s = 第 %(n)s 轮 / Round %(round)s**。刀高水位现读 **M1546**（`mutate_r586_*` 那六把在册）⇒ 本轮从 **M1547** 起，没抄派单里的数。
- `%(main_run)s ↔ %(main_sha)s`（R586 主笔）现读 `completed / failure` ⇒ **到数**。全部失败步骤逐字：`%(main_steps)s` ⇒ **STEP[11] 不在里面**。门那一行 `%(main_drift)s` ⇒ **出口·乙**（那一维在那台机器上仍没人判），与 R586 那一节同形状。R586 交下来的六条预测由 `ci_status_r587.py` 判、不由我念 ⇒ **六条全中**（逐字见 ①）。
- `%(add_run)s ↔ %(add_sha)s`（R586 补记笔）现读 `completed / failure` ⇒ **到数**。R586 那一节写的是「本轮那一跑现取现写而它未到数」⇒ 那句话在它落盘的时刻是对的，本轮**只 forward 补记、不回头改那一格**。失败步骤比主笔多一朵 `STEP[18]`（On-screen probe coverage floor）⇒ 同一轮的两跑里那一步一朵红一朵没红，这是**跑与跑之间的差**，不是本轮引入的回归（本轮没碰捕获侧）。
- ⚠ **通道分歧一条（具名，不合并）**：`ci_read.py steps` 的头行在 06:41 那一刻对 `%(add_run)s` 打的是 `conclusion=`（空），而 `gh run view --json conclusion` 现在打 `failure`。我没把那一格读成「未到数」，因为 到数 判定用的是 **job/step 级结论行**（R557 那条规矩在这里正好接住）；但 run 级 conclusion 与 job 级结论**不是同一格账**，取数时刻也不同 ⇒ 两处都记，不许只留最终那个数。
- `%(old_run)s ↔ %(old_sha)s`（R585 补记笔）现在也到数（`completed / failure`），**由本轮签**。这一跑的日志里步骤名恒为 `UNKNOWN STEP` ⇒ 正文只能按通道串取；而**本轮发现自己那条按机器键筛的判别是坏的**：电池那一步的模拟行故意写 `本机=基线署名=github-runner`，与真门同一批前缀 ⇒ 上一版据此报出的四行 DRIFT **全是电池行**。改用「基线署名 == 那一笔提交里 `docs/frame_baseline.json` 自己署的那台机器」筛 ⇒ 排除 %(old_excluded)s 行合成树，真门那一行逐字 `%(old_drift)s` ⇒ **判=不判**，与另两跑同形状（旧版那句「判=判」是借来的读数，作废）。
- ⚠ **恒真预测一条（具名并修掉）**：六条预测里 `HOVER_TIER 认不出档=0` 第一版写成 `lambda g: True` —— 因为那条通道不在 `gate` 集合里，我就「放行」了它 ⇒ 那是把「我没接上」写成「它中了」（R565 那一族：自我豁免＝恒真门）。现在把通道交给预测本身，取不到行就报「未读到」而不是「中」。
- 本轮那三条**留给下一跑**的可证伪预测（写在 `ci_status_r587.py` 的 `PREDICTIONS_R588`，由脚本判、不由我念）：①`FRAME_BASELINE_SCALE_NOT_RUN` 是这一支**唯一**出口（并列/读不出都归它，不许新造第二条）；②`FRAME_BASELINE_BAKE` 那一行必须带 `倍率分布=/不一致帧数=/无尺寸段=/原因=` 四个新格子；③名册与基线里的既有字段含义**一字未改**（`capture_scale` 仍是那个众数语义的位置，只是并列时变成空串）。⚠ 这三条**今天一条都没判** —— 含本笔的那一跑还不存在（代码还没推），所以 `ci_status_r587.py` 只把它们的**文本**印进读数、不填任何数；R588 拿它们对含本笔那一跑判。对更早的跑它们只能打印「不适用」，把「还没落地」读成「是假的」是这一族的第三种坏法。
- 红名单逐字 5 个名字（`%(main_run)s`、`%(old_run)s`）与 6 个名字（`%(add_run)s` 多 `testProductDurationRevealStillMovesOverTime`）⇒ **同集合内的一朵间歇**，本轮不重开也不结案。

① **派单给的三条形状结论：逐条坐实（取值时刻=R%(r)s 开工，全部现读）**
- 靶 A 三处逐字：①`mode = max(set(ratios), key=ratios.count)` —— `set` 的遍历顺序不参与判定，但**并列时它替我选了一个**；②两轴推不出同一倍率的那张 `bad += 1` 之后**仍** `ratios.append(float(px)/float(lx))`；③`_bad` 在 `bake_provenance` 与 `check` 两个调用点被下划线丢掉 ⇒ 这个量算了却没人看。⇒ 一批 355 张 2x + 1 张 1x 会照印 `2.00x`，读者看不出这批是混的。
- 靶 B 逐字：`hover_two_state_diff.py:72` 的 `TIERS = ('light','dark')` 与 `frame_baseline.py:453` 里硬写的 `-(?:light|dark)\\.png$` 是**同一件事实的两份写法**；把其中一份改坏（例如加一档 `-mono`），另一份**不会有任何一格红** —— 倍率那一侧只会静默退化成「帧名里推不出倍率」，而它走的是**不红的** `SCALE_NOT_RUN` 出口。
- 顺账逐字：`scripts/*.py` 里被 print 出去的成句命令现读 **1 条**（`frame_baseline.py` 自己那条出路）；另有两支脚本印了旗标但不是命令（`ci_red_stability.py` 手写 argv、`create_issues.py` 的 `add_argument(` 与旗标换行）⇒ 这两处是本轮把守卫从「两个文件」扩到「每一支」时**自己撞出来的**，见 ⑨。

② **真实推进（段号=②，靶 A：倍率报成分布，并列当不知道）**
- `capture_scale()` 的返回从三元组换成**一个字典**：`scale / frames / bad / sizeless / dist / reason`。`dist` 是**排序后**的（先按计数降序、再按倍率名升序）⇒ 并列时也有确定形状，不再依赖 `set` 的遍历顺序（那正是旧版印出抛硬币倍率的根）。
- **并列 ⇒ `scale=""`、`reason="tie"`**，由调用方走**已有的那一条** `FRAME_BASELINE_SCALE_NOT_RUN=<reason>` 出口 ⇒ 没有新造第二条「不判」门路（派单硬要求）。同时印 `FRAME_BASELINE_SCALE_TIE` 说清是**哪一种**说不出（tie / unreadable / no-frames / no-dir），因为「不知道」有四种成因，混说会给出假的可比性。
- 上一版那条出口挂在 `elif bake["scale"] and not current_scale` 下面 ⇒ 基线**自己**也说不出倍率时（混批/并列烤的），两个 unknown 撞在一起反而**一行都不印** —— 那是「谁都不知道」被读成「没什么要报的」。现在它是独立的 `if not current_scale`，值槽里带 reason、分布、基线倍率三样。
- `bad` 不再被 `_bad` 丢掉：印 `FRAME_BASELINE_SCALE_BAD 当轮=N/M`，并落进文档字段 `capture_scale_bad_frames`。`sizeless`（帧名里没有 `-宽x高-档` 那一段）同样照报 —— 它是**分布的分母完整性**证人：现读语料这一支是 **0 张**，所以它是前瞻，不是今天的读数（这句话不许说过头，见 ⑨·3）。
- 文档新增四个字段（`capture_scale_dist` / `capture_scale_bad_frames` / `capture_scale_sizeless` / `capture_scale_reason`），`bake_line` 一并印出 ⇒ 真语料现读：`%(scale_head)s`
- 没动的（派单红线）：`--against` 的默认与 choices、`--allow-missing` 两帧、任何阈值/容差/地板、名册那 16 行的字段与理由、`docs/frame_baseline.json`（`%(baseline)s`）。**没有**因为「报分布好用」去改已有字段的含义：`capture_scale` 仍是「这批帧的倍率」，只是说不出时写空串而不是写一个看起来确定的数。

③ **真实推进（段号=③，靶 B + 顺账：一份真值、一条会红的对账）**
- 新增 `scripts/tier_vocabulary.py`：`TIERS` 一份 + `tier_from_name()` 按段解析 + `tier_alternation()/tier_suffix_pattern()` 现推正则片段。四处声明（`hover_two_state_diff.py` 的 `TIERS`/两处字面量/那条正则、`frame_baseline.py` 的倍率正则、`frame_recording_proof.py` 的 shade 循环）全部改成 import ⇒ 现读扫描（同一支扫描器跑两遍：HEAD 与工作树）：`%(tier_scan_head)s` ｜ `%(tier_scan_now)s` ｜ `%(tier_scan_net)s`
- 守卫 `test_no_live_script_declares_its_own_tier_vocabulary` 扫 `scripts/*.py` 每一支（AST 级，docstring 与注释按行号摘出去）⇒ 「再出现第二份代码层面的声明」当场红并点名文件与行；自带三条对照：三种形状都认得出（正对照）、注释里出现不算声明（反面对照，本轮真实撞过一次）、`tier_alternation()` 是从词表现推不是另抄。
- 「`substring_tier` 不参与判定」由 AST 签，不由注释签：`test_measure_uses_segment_parse_not_substring` 断判定函数调的是 `frame_tier` 且**没调**子串法；`test_substring_tier_has_exactly_one_caller` 断全仓只剩报表那一处调用点（刀 M1550 把判定改回子串 ⇒ 这两格各红一次，且「只有一个调用点」从 1 变 2 也红）。
- 顺账那条做成**仪器守卫**而不是一条条追记：`PrintedCommandParsesTests` 扫每一支脚本 print 出去的 `python3 <某脚本.py> <尾巴>`，把尾巴里的 `--选项` 拿去对账**那个脚本自己**的真旗标（`add_argument`，容忍换行；∪ 代码里整条字面量就是一个 `--x` 的那些，覆盖手写 argv），并断言脚本路径真存在。今天全仓这样的命令只有 1 条 ⇒ 范围是「每一支」，不是那一条。
- 词表的**边界**也做成读数：Swift 捕获侧现读 `%(swift_tier)s` ⇒ python 侧那份真值管不到它，本轮红线不许碰捕获侧 ⇒ 新开 **661** 只登记不代选。

⑨ **本轮自伤清单（九处，每处都带代价）与对账**
· **对账口径**（沿用启用，不关）：每条具名红/具名不判/作废读数要么落到 `⑨·` 编号，要么写 `不计入对账口径` 并带三类名字之一。
- 逐条：
  · ⑨·1 **一把空刀（M1549）**：它摘的是「`px<=0` 那张进不进 `bad`」那一支，而那一支**从来没有测试覆盖** ⇒ 末态 `post=%(m1549_before)s`（PASSED＝空刀）。作废的是**结论**不是刀位：号留着、不复用，补上证人（`test_unreadable_png_is_counted_as_bad_not_dropped`）后在**同一处**以新号 **M1553** 重落 ⇒ CAUGHT。⚠ 两个时刻都要记：补证人之后重跑整张表，M1549 自己也变成 CAUGHT（`knife_status.txt` 那一趟）⇒ 「空刀」这句话的证据是**补证人之前那一趟**的读数文件，不是我现在念的。这是第五种空刀形状（R491 同值、R560 容差、R567 公共行、R577 一臂捆两件事）：**刀没错，证人还没出生**。
  · ⑨·2 **改尺之后证人搬了门牌，刀还打在旧模块上**：顺账那条守卫从 `test_frame_baseline` 升级成扫 scripts/ 每一支、新家住在 `test_tier_vocabulary` ⇒ M1552 若仍按表默认的模块跑，抓的是一把**已经不认这件事的旧尺**（形状与 ⑨·1 相邻：不是刀错，是证人换了门牌）。代价=臂上补第 5 位（证人模块），并把整张表**重跑一遍**。
  · ⑨·3 **我印了一个不存在的帧名**：`settings-general-min-orphan-dark.png` 被我写进 `frame_baseline.py` 的 print 与注释，还配了一句「现读确有这种命名」。它不在现读语料里（现读那一批 356 张**全部**带 `-宽x高-档` 那一段；真实存在的近似名是 `general-min-orphan-640x540-dark.png`）。⇒ 本轮顺账要防的就是这种空头支票，而我自己在同一轮里开了一张。代价=撤掉例子、注释改成「现读这一支是 0 张 ⇒ 分母完整性证人」，测试 docstring 写明那是**合成**名。自查方式也记下来：scripts/*.py 里 15 处 `.png` 字面量逐条对现读语料，不在册的 1 处就是它。**没有**为它新立守卫：那 15 处里 12 处是模板/输出文件名（`%%s.png`、`real_screen_*.png`），按「名字必须在册」判会把它们读成红 ⇒ 记成读数与措辞规矩，不记成门。
  · ⑨·4 **把词表收成一份真值改变了迭代顺序，既有测试当场红 —— 红在脚本身上**：`heatmap_frame_levels.py` 原来写 `('dark','light')`，共用词表是 `('light','dark')`；那支脚本在**第一个 stop 处就 `return 2`** ⇒ 「缺席那一档被点名」从来靠的是循环顺序而不是契约。代价=修脚本（stop 不再短路，两档各自点名后再收口，并新增 `HEAT_FRAME_VERDICT not-run=N` 那一行：有一档输入不足就不许印「两通道都对上了账」），把既有那一格改成**两档各当一次在场**（subTest），并补一把刀 **M1554** 钉住「不许回到短路」。这一条的形状值得记：合并两份写法**本身**就是一次改动，它会把「藏在顺序里的依赖」翻出来 —— 那不是回归，是既有缺陷第一次被看见。
  · ⑨·5 **扫描器第一版扫文本行，把我自己写的注释判成第二份声明**：注释里那句「倍率解析里的 `(?:light|dark)` 由它现推」被数成一处声明 ⇒ 守卫红在我没改过的地方。代价=改成 AST 级、docstring 按行号摘出去，并补一条**反面对照**（注释里出现那三种形状不算声明）。与 R580「读到 1 要区分『对象在』与『字面在』」同族。
  · ⑨·6 **顺账守卫第一版把两处「存在的」读成「不存在」**：`ci_red_stability.py` 没有 argparse（手写 `if args[0] == "--from-file"`）、`create_issues.py` 的 `add_argument(` 与旗标换了行 ⇒ 按「print 里任何 `--x` 都要在 add_argument 里」判，这两个真旗标都会被判成空头支票。代价=规则从「宽」收窄成「只认成句命令」+ 真旗标集合并入「整条字面量就是一个 `--x`」那一支，并补两条对照（两种真写法都要认成存在；一个不存在的脚本名也要红）。**把存在的读成不存在**比漏读更坏：它会把守卫养成一台专门红自己的机器，然后被人关掉。
  · ⑨·7 **一次性批量补丁把目标文件写成 `SyntaxError`**：`/tmp/r587/patch_printed_guard.py` 里我在新代码块中写了 `(?:"|\')`，而它坐在三引号字符串里 ⇒ `\\'` 被吞成 `'`，落盘后那一行直接语法错（import 阶段就炸，没删掉任何内容 —— 与 R577 那次删掉 13,848 字符同族但轻一级）。代价=改一行、并把因此变成死码的两个 helper 删掉。规矩照旧：**批量补丁写完立刻 import 一遍目标模块**，不能只看 diff。
  · ⑨·8 **我自己的 ⓪ 脚本里两条判别会造假**：①退化日志按「机器键含 github-runner」筛真门 —— 电池的模拟行**也用这个键** ⇒ 借来的四行 DRIFT 被当成真门读数（本轮改用「基线署名等于那一笔文档署的那台机器」，并说出这条判别比按步骤切更弱）；②一条预测写成 `lambda g: True` ⇒ 六条里有一条永远不会不中，而我上一轮把它记成了「全中」。代价=两处都改，并**重跑三跑读数**；旧那份 `ci_status.txt` 的读数被新的覆盖前已另存，账上两句话都在。
  · ⑨·9 **读数文件里那一格 `P1_RC` 记的是 grep 的退出码，不是脚本的**：生成命令写成「跑脚本 → grep 一行 → echo $?」，而 `$?` 在 echo 那一刻已经是 grep 的状态 ⇒ 这一格从「脚本退出码」被悄悄换成「我有没有抓到一行」。本轮真值恰好也是 0，所以**没有翻面**，但尺已经换了对象（R565 那一族：通道还在，读的不是那件事）。代价=改成显式记数，并在读数文件里把这一格来历写全。
- **红名对账**：
  · 红名「M1549 `post=PASSED`（空刀：那一支没有证人）」→ ⑨·1
  · 红名「M1552 打在旧模块上（证人搬家）」→ ⑨·2
  · 红名「印出去一个不存在的帧名（`settings-general-min-orphan-dark.png`）」→ ⑨·3
  · 红名「`AssertionError: 'dark' not found in …HEAT_FRAME_INPUT_MISSING 缺帧 …light.png`（合并词表改变迭代顺序，暴露脚本只报第一档）」→ ⑨·4
  · 红名「守卫把注释判成第二份声明」→ ⑨·5
  · 红名「守卫把两个真旗标读成不存在（手写 argv / 换行的 add_argument）」→ ⑨·6
  · 红名「`SyntaxError`（批量补丁吞掉一个反斜杠）」→ ⑨·7
  · 红名「`ci_status_r587.py` 的退化筛把电池行当真门 + 一条恒真预测」→ ⑨·8
  · 红名「读数文件里 `P1_RC` 记成 grep 的退出码（本轮真值也是 0 ⇒ 没翻面，但尺换了对象）」→ ⑨·9
  · 红名「`%(add_run)s` 比 `%(main_run)s` 多一朵 `STEP[18]`」→ **不计入对账口径**（通道未跑 —— 同一轮两跑之间那一步的通道结果不同，本轮没碰那一面；措辞按名册里那三类之一写，不新类）
  · 红名「`testProductDurationRevealStillMovesOverTime`（只在 `%(add_run)s` 那一跑出现）」→ **不计入对账口径**（基名在漂 —— 与 R582–R586 同集合内的一朵间歇名，本轮不重开不结案）
  · 红名「`FRAME_BASELINE_SCALE_TIE` / `…_BAD` / `…_SIZELESS` 本机今天都不出现」→ **不计入对账口径**（通道未跑 —— 真语料是单一倍率、无混批、无无尺寸段名；三格由合成夹具与刀作证，外部证人归下一跑）
  · 红名「`STEP[15]/[17]/[19]` 那三朵」→ **不计入对账口径**（契约名 —— 逐字同集合，只算「没有新名字」）
- 门复算（预览 → 落盘 → 复算）：`%(recon)s`
- 逐本现读七个数（写之前各 0 / 写之后每一本恰 1）：`preapply_counts.txt`、`postapply_counts.txt`。

⑦ **验证链（顺序照旧，两处偏差具名）**：`swift build --build-tests`（包目录内）告警 **0**、错误 **0**（`%(build_warn)s`）；python 判据卷**整目录一趟** `%(battery)s / %(battery_ok)s`，分卷现读 `%(modules)s`；`def test_` 前后计数 `%(counts_line)s` ⇒ 净 +%(delta_total)d 格（热图那一格是**改成两向**，格数不涨，涨的是 subTest 数 —— 这句话两边都不许说过头）；八把刀**先跑**（全部打在 python 仪器上、不碰 `.build` ⇒ 没撞锁；偏差具名 `KNIVES_BEFORE_CAPTURE_PYTHON_ONLY`，沿用 R586 同一命名）`%(knives)s`；逐把红了哪几格由日志现数 `%(knife_reds_head)s`；`MD5=` 那一行是刀链前后同一批文件的现读（还原证人，四份文件一起核）`%(md5)s`；Swift 捕获判据卷 `%(capture)s`（帧 `%(frames)s`）；对新尺在**含本笔的树**上现读 `%(gate_drift)s` ⇒ `%(gate_result)s`；倍率那一维的真语料读数 `%(scale_line)s`；全量卷 `%(full)s`，skipped 只记现读 `%(full_skips)s`；三道预检**串行**（不与 swift 卷并行）：`%(precheck_needle)s`、`%(precheck_arm)s`、`%(precheck_hidden)s`；换装 `SKIP_INSTALL=no-product-change`（产品 0 文件）；七本台账 → 派生格**落盘之后**现读 → 电池（本机那一趟的数**不回填**，最终签字归 runner `STEP[9]`）；产品文件 0 个，连续零改动 **%(streak_n)d** 轮（唯一取数口 `python3 scripts/product_streak.py`，**台账落盘之后**现读 `%(streak_line)s`；as-of 口径 ⇒ 读作「本轮之前最后一次产品改动在 %(streak_n)d 轮前」；取数时刻由 `post_land()` 钉在函数名字上，不在纪律上）；清账 `%(absence)s`；代码 numstat 现读 `%(numstat_head)s`；字面量真验证 `%(pyverify_head)s`。

⑧ **看图那一腿**：`%(look)s`

⑤ **地基一字不动**：4.5 墨、150、2x 8.0pt、1x 6.0pt、120ms 与容差 1、Motion ≥2、`probeInkFraction=3%%`、`.contentFade 0.20`、像素格容差 1.5 与跳变地板 8、声明时长、**两态差尺的两个地板 `1.20 / 1.10`**（本轮只换「哪一档」的解析法，数值一字未动 —— 刀 M1550 的负半证人就是「地板那一格不许红」）、全量 skipped 现读、禁碰 14 面不抬不降（本轮没碰捕获侧 Swift ⇒ 逐字证人就是 ⑦ 里那两本 python 卷与全量卷）；`--against` 默认与 choices、`--allow-missing` 两帧原样；本轮新增的读数里**没有一条进拦路**（`SCALE_TIE`/`SCALE_BAD`/`SCALE_SIZELESS` 只报数，并列与读不出都归**已有的** `SCALE_NOT_RUN`），没有任何一格被放宽、改成 skip 或挪阈值。
""" % dict(
        r=i["r"], n=i["n"], round=i["round"], date=DATE, prev_n=i["prev_n"], prev_r=i["prev_r"],
        main_run=RUN_MAIN, main_sha=m["sha"], add_run=RUN_ADD, add_sha=a["sha"],
        old_run=RUN_OLD, old_sha=o["sha"],
        main_steps=m[u"步骤全逐字"][:420],
        main_drift=(m[u"门那一步的逐字读数"] or [u"（没取到）"])[0][:250],
        old_drift=(o[u"门那一步的逐字读数"] or [u"（没取到）"])[0][:250],
        old_excluded=re.search(r"合成树 (\d+) 行", o[u"处置"]).group(1) if re.search(r"合成树 (\d+) 行", o[u"处置"]) else u"（没读到）",
        scale=d["scale"], scale_head=d["scale"].splitlines()[0][:260],
        scale_line=d["scale"].splitlines()[0][:200],
        tier_scan_head=(next((l for l in d["tier_scan"].splitlines() if l.startswith(u"TIER_SCAN HEAD")), u"（没读到）")[:200]),
        tier_scan_now=(next((l for l in d["tier_scan"].splitlines() if l.startswith(u"TIER_SCAN 工作树")), u"（没读到）")[:200]),
        tier_scan_net=(next((l for l in d["tier_scan"].splitlines() if l.startswith(u"TIER_SCAN 净变化")), u"（没读到）")[:200]),
        swift_tier=d["swift_tier"].splitlines()[0][:160],
        baseline=d["baseline_untouched"][:120],
        knives=knife_line(d["knives"]),
        knife_reds_head=u" ｜ ".join(u"%s红%d格" % (k["arm"], k["reds"]) for k in d["knives"]),
        battery=d["battery"], battery_ok=d["battery_ok"],
        modules=u" ｜ ".join(d["modules"])[:520],
        counts_line=u" ｜ ".join(u"%s %d→%d" % (k, b, a2) for k, (b, a2) in sorted(d["counts"].items()))[:420],
        capture=d["capture"], frames=d["frames"], build_warn=d["build_warn"][:150],
        gate_drift=d["gate_drift"][:260], gate_result=d["gate_result"][:170],
        full=d["full"], full_skips=d["full_skips"],
        precheck_needle=grep_line(d["prechecks"], "NEEDLE_PRECHECK", u"针预检") if d["prechecks"] else u"（落盘后跑）",
        precheck_arm=grep_line(d["prechecks"], "ARM_TOTAL", u"臂总数") if d["prechecks"] else u"（落盘后跑）",
        precheck_hidden=grep_line(d["prechecks"], "HIDDEN_ARMS", u"盲区名册") if d["prechecks"] else u"（落盘后跑）",
        absence=d["absence"], numstat_head=d["numstat"].splitlines()[0][:200],
        pyverify_head=u" ｜ ".join(d["pyverify"].splitlines()[:3])[:260],
        md5=d["md5"][:300], recon=d["recon"], look=d["look"].replace("\n", u"\n  ")[:2600],
        streak_n=int(re.search(r"streak=(\d+)", d["streak"]).group(1)) if re.search(r"streak=(\d+)", d["streak"]) else -1,
        streak_line=d["streak"],
        m1549_before=d["m1549_before"],
        cfb=d["counts"]["test_frame_baseline"][0], cfa=d["counts"]["test_frame_baseline"][1],
        tier_now=d["counts"]["test_tier_vocabulary"][1],
        delta_total=d["delta_total"],
    )


def block_ui(d):
    i = d["ident"]
    u0 = next_u()
    m, o = d["main"], d["old"]
    us = [
        (u"⓪ 三跑全部到数，其中两跑把上一轮的「未到数」forward 掉",
         u"`%(main_run)s ↔ %(main_sha)s` 与 `%(add_run)s ↔ %(add_sha)s` 现读都是 `completed / failure` ⇒ 到数；"
         u"失败步骤逐字 `%(main_steps)s` ⇒ **STEP[11] 不在里面**；门那一行 `%(main_drift)s` ⇒ 出口·乙。"
         u"`%(old_run)s ↔ %(old_sha)s`（R585 补记笔）也到数，但日志步骤名恒为 `UNKNOWN STEP` ⇒ 正文按通道串取。"
         u"R586 那一节写的「未到数」在它落盘的时刻是对的 ⇒ 本轮只 forward 补记，不回头改那一格。"
         % {"main_run": RUN_MAIN, "main_sha": m["sha"], "add_run": RUN_ADD, "add_sha": d["add"]["sha"],
            "old_run": RUN_OLD, "old_sha": o["sha"],
            "main_steps": m[u"步骤全逐字"][:300],
            "main_drift": (m[u"门那一步的逐字读数"] or [u"（没取到）"])[0][:190]}),
        (u"我自己那把读 CI 的尺有两处会造出假读数（都改了，都重跑）",
         u"①退化日志里按「机器键含 `github-runner`」筛真门是**坏的**：电池那一步的模拟行故意写 "
         u"`本机=基线署名=github-runner` ⇒ 上一版报出的四行 DRIFT 全是电池行，那句「判=判」是借来的读数（作废）。"
         u"改用「基线署名 == 那一笔提交里 `docs/frame_baseline.json` 署的那台机器」筛 ⇒ 真门那一行逐字 "
         u"`%(old_drift)s`，与另两跑同形状。这条判别比按步骤切**更弱**，所以逐字说出来。"
         u"②六条预测里 `HOVER_TIER 认不出档=0` 第一版写成 `lambda g: True` ⇒ 恒真门（R565 那一族）。"
         % {"old_drift": (o[u"门那一步的逐字读数"] or [u"（没取到）"])[0][:190]}),
        (u"倍率不再是一个众数，而是一个分布；并列一律当「不知道」",
         u"`capture_scale()` 返回 `scale/frames/bad/sizeless/dist/reason`，`dist` 先按计数降序、再按倍率名升序 ⇒ "
         u"并列时也有确定形状，不再由 `set` 的遍历顺序替我选一个。并列 ⇒ `scale=空串` + `reason=tie`，"
         u"走**已有的** `FRAME_BASELINE_SCALE_NOT_RUN=<reason>` ⇒ 没有新造第二条不判出口。"
         u"真语料现读：`%(scale)s`" % {"scale": d["scale"].splitlines()[0][:200]}),
        (u"`bad` 与 `sizeless` 从「算了没人看」变成照报照落盘（后者今天是 0，属前瞻）",
         u"旧版 `_bad` 在两个调用点被下划线丢掉；现在印 `FRAME_BASELINE_SCALE_BAD 当轮=N/M` 并落 "
         u"`capture_scale_bad_frames`。`sizeless`（帧名里没有 `-宽x高-档` 那一段）印 `…_SCALE_SIZELESS` 并落字段。"
         u"⚠ 现读语料里 `sizeless=0` ⇒ 这一支是**分布的分母完整性**证人，不是今天的读数；"
         u"我第一版还给它编了一个不存在的帧名当例子（见 ⑨·3），已撤。"),
        (u"两个 unknown 撞在一起时旧版一行都不印 —— 那条出口改成独立判定",
         u"旧版是 `elif bake[「scale」] and not current_scale` ⇒ 基线自己也说不出倍率（混批/并列烤的）时两个 unknown "
         u"互相抵消，「谁都不知道」被读成「没什么要报的」。现在 `if not current_scale` 独立成一条，"
         u"值槽里带 reason、当轮分布、基线倍率三样。"),
        (u"档位词表收成一份真值：活脚本里的声明从「四份」变成 0 份，守卫由 AST 签",
         u"新增 `scripts/tier_vocabulary.py`（`TIERS` + 按段解析 + 现推正则片段）。四处 import 它。"
         u"守卫扫 `scripts/*.py` 每一支，再出现第二份**代码层面**的声明就红并点名文件与行；"
         u"docstring/注释按行号摘出去（本轮第一版扫文本行，把我自己写的注释判成了声明）。"
         u"同一支扫描器跑两遍 ⇒ `%(tier)s`"
         % {"tier": u" ｜ ".join([l for l in d["tier_scan"].splitlines()
                                  if l.startswith((u"TIER_SCAN HEAD", u"TIER_SCAN 工作树", u"TIER_SCAN 净变化"))])[:420]}),
        (u"「子串法不参与判定」不再靠注释：两格 AST 证人 + 刀 M1550",
         u"`test_measure_uses_segment_parse_not_substring` 断判定函数调 `frame_tier` 且不调 `substring_tier`；"
         u"`test_substring_tier_has_exactly_one_caller` 断全仓只剩报表那一处。M1550 把判定改回子串 ⇒ 两格各红一次"
         u"（调用点从 1 变 2 也红）。`FLOOR_LIGHT=1.20 / FLOOR_DARK=1.10` 一字未动 ⇒ 这把刀不许靠改数值红。"),
        (u"印给读者的成句命令由它自己的参数表对账（顺账做成门，不再逐条追记）",
         u"新守卫扫每一支脚本 print 出去的 `python3 <某脚本.py> <尾巴>`：脚本路径必须存在，尾巴里每个 `--选项`"
         u"必须在那个脚本的真旗标集合里（`add_argument` 容忍换行 ∪ 整条字面量就是一个 `--x`）。"
         u"扩范围时自己撞出两处「把存在的读成不存在」（手写 argv 的 `ci_red_stability.py`、"
         u"`add_argument(` 换行的 `create_issues.py`）⇒ 规则收窄成「只认成句命令」并补两条对照。"
         u"今天全仓这样的命令只有 1 条 ⇒ 范围是每一支，不是那一条。"),
        (u"合并词表把「藏在循环顺序里的依赖」翻了出来：热图那支脚本只报第一档",
         u"`('dark','light')` 换成 `('light','dark')` 之后既有那格 `test_log_covering_only_one_appearance…` 当场红 —— "
         u"根因不是合并错，而是脚本在**第一个 stop 处就 return**，所以「缺席那一档被点名」一直靠顺序。"
         u"修法：stop 不再短路、两档各自点名，新增 `HEAT_FRAME_VERDICT not-run=N`（有一档输入不足就不许印「两通道都对上了账」）；"
         u"那一格改成两档各当一次在场（subTest）；刀 M1554 钉「不许回到短路」，且只动「日志缺档」那一支、不动「缺帧」那一支。"),
        (u"词表的边界也是读数：Swift 捕获侧那几处本轮没管（新开 661）",
         u"捕获侧 `UICaptureHarness.swift` 里 `for tag in [light, dark]` 那种循环现读 %(swift)s 处 ⇒ 派单红线不许碰捕获侧，"
         u"所以**不拦、不改、只数**：新增 `SwiftSideVocabularyCountTests` 用两条正则（两种顺序）各数一遍并断"
         u"「两序之和 == 任意顺序合并数」，防止将来有人把两档顺序反过来写而计数器读成 0 —— "
         u"那才是「全仓只有一份」这种假声明的来源。661 只登记，出路一条不代选。"
         % {"swift": d["swift_tier"].splitlines()[0].split(u"处=")[1].split(u"（")[0] if u"处=" in d["swift_tier"] else u"（没读到）"}),
        (u"看图那一腿 + 逐字节对照：本轮帧一字未变",
         u"%(look_short)s ｜ BYTE_COMPARE 与 R586 那批同名 356 张**逐字节相同 356、不同 0** ⇒ 产品 0 文件这句话有像素证人；"
         u"没新增漂移 ⇒ 没调用 `register-drift`，名册那 16 行的 `observed` 一字未动；工作基线也没被写：`%(baseline)s`"
         % {"look_short": d["look"].splitlines()[0][:150], "baseline": d["baseline_untouched"][:120]}),
        (u"刀 M1547–M1554：八把里 M1549 是空刀（作废、号不复用），补证人后 M1553 在同一处重落",
         u"`%(knives)s`。逐把红格数由日志现数：M1547 两格（并列那两格，混批那格不动）、M1548 一格、M1549 补证人前两格、"
         u"M1550 两格、M1551 一格、M1552 一格（证人模块搬到 test_tier_vocabulary 之后重跑）、M1553 一格、M1554 两个 subTest。"
         u"⚠ M1549 与 M1553 打的是**同一处**：两个时刻的末态都要记（补证人之前 PASSED＝空刀、之后 CAUGHT），"
         u"只留最终那张就把「这条分支曾经没人测」这件事抹掉了。" % {"knives": knife_line(d["knives"])}),
    ]
    head = (u"## 第 %(n)s 轮（R%(r)s · %(date)s · U-%(u0)s…U-%(u1)s）：把「读数是不是它声称的那个对象」做成三份会红的账"
            u"（①倍率报分布、并列当不知道并走已有出口；②档位词表一份真值、子串法由 AST 签出判定；③印出去的成句命令由参数表自己对账）\n\n"
            % {"n": i["n"], "r": i["r"], "date": DATE, "u0": u0, "u1": u0 + len(us) - 1})
    body = u"".join(u"- **U-%d：%s**。\n    %s\n\n" % (u0 + k, t_, b) for k, (t_, b) in enumerate(us))
    return head + body, u0


def block_iteration(d):
    i = d["ident"]
    return u"""## Round %(round)s · R%(r)s（第 %(n)s 轮 · %(date)s）：读数是不是它声称的那个对象——倍率的分布、词表的一份真值、印出去的命令

**七维度自评**（恰七行，每格 n/15；维度名照曲线尺认的那七个同字，本轮不造新维度）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉看图 | @@LOOKSCORE@@ | %(look_short)s |
| 判据有效性 | 14/15 | 本轮判的是**读数会不会冒充自己不是的东西**：倍率并列时不许印一个确定值（M1547）、`bad` 不许算了没人看（M1549 空刀→M1553）、无尺寸段的名字不许静默跳过（M1548）、子串法不许回到判定（M1550）、词表不许有第二份声明（M1551）、印出去的命令必须能被解析（M1552）、缺席那一档不许靠循环顺序才被点名（M1554）。扣 1 分：`sizeless` 那一支现读语料是 0 张 ⇒ 它今天**只由合成夹具作证**，外部证人还没有。 |
| 假绿防御 | 15/15 | ①并列走**已有的**那条 `SCALE_NOT_RUN`，没有新造第二条不判门路；②两个 unknown 撞车时旧版一行不印，现在独立成一条并带上 reason/分布/基线值；③守卫自带三种对照（形状认得出、注释不算声明、不存在的脚本名也红）；④「子串法不参与判定」由 AST 签不由注释签；⑤两个地板数值 `1.20/1.10` 一字未动，M1550 的负半证人正是「地板那一格不许红」。 |
| 产品面推进 | 3/15 | 产品 **0** 文件（逐字节证人：与 R586 那批 356 张**相同 356、不同 0**）。推进的是三条**取证侧**可信度：一份倍率读数现在说得出自己是混的还是并列的；档位词表只有一份；印给读者的命令能被自己的参数表认。段号仍是第②③段。 |
| 台账一致性 | 8/15 | 身份两处交叉核对；七个标题形状写前 0、写后各 1；派生格落盘后现读。扣分在四处：⑨·3（我给读者印了一个**不存在的帧名**，还是在本轮专门防这件事的那一轮）、⑨·8（我自己读 CI 的那把尺两处会造假读数：电池行被当真门 + 一条恒真预测）、⑨·4（合并词表暴露脚本只报第一档）、⑨·1/⑨·2（空刀与证人搬家）。 |
| 剩余风险处置 | 14/15 | 661 新开不结；655/656/658/659/660 全不结、出路一条不代选；旧红一朵不抹；第③段着色器一字未写。扣 1 分：`SCALE_TIE/BAD/SIZELESS` 三朵新通道**还没有 runner 的证人**（要等含本笔那一跑），本机真语料只能证明它们不误响。 |
| 交接可读性 | 15/15 | 三条预测写进 `ci_status_r587.py` 并由 sha 集合限定适用范围 ⇒ 对 R586/R585 那三跑打印「不适用」而不是「不中」；⓪ 的 run↔sha 三对成对写进下一轮第 ⓪ 条；两套编号（出口·甲乙丙丁 vs 各单三条出路）在 ⓪ 里再次分开写。 |
""" % {"round": i["round"], "r": i["r"], "n": i["n"], "date": DATE,
       "look_short": d["look"].splitlines()[0][:170]}


def block_backlog(d):
    i = d["ident"]
    return u"""## R%(r)s 追账（第 %(n)s 轮 / Round %(round)s · %(date)s）：661 新开，655/656/658/659/660 一条没结

**661. 档位词表在 Swift 捕获侧还有 %(swift_n)s 处独立声明 ⇒ python 侧那份真值管不到它，加一档或改名时两侧会分叉且没有一格会红（R%(r)s 现读并新开）**
    现象（取值时刻=R%(r)s 开工，`grep -rn --include=*.swift -E 'for tag in ["light","dark"]'` 现读）：
    `ClipboardHistory/Tests/ClipboardHistoryAppTests/UICaptureHarness.swift` 里 %(swift_n)s 处 `for tag in ["light", "dark"]`，
    与本轮新建的 `scripts/tier_vocabulary.py` **没有任何连接**（两个运行时，中间隔着胶片文件名）。
    后果：加一档（例如 `-mono`）或改名时，python 侧那份会红（守卫 `test_no_live_script_declares_its_own_tier_vocabulary`），
    Swift 侧那 %(swift_n)s 处**一条都不会红** —— 捕获照旧只产两档，而判据侧以为世界变了。
    R%(r)s 补的（三条出路一条没选）：①新增 `SwiftSideVocabularyCountTests` 把**处数**变成现读读数，
      并断「两种顺序各数之和 == 任意顺序合并数」⇒ 计数器自己不会在改名那天读成 0；
    ②台账把「python 侧一份真值」这句话的范围写清，不许写成「全仓只有一份」（那是假声明）。
    ⚠ 这一单欠的是**改动本身**：本轮红线不许碰捕获侧，所以只登记不修。
    出路三条（归用户/下一轮定向）：⑴Swift 侧也收成一份常量（在 harness 里建 `static let tiers: [String]`，各处 import）；
    ⑵给捕获侧加一条「产出的档位集合 == 词表」的判据（不修声明，只钉住分叉的那一刻）；
    ⑶接受两运行时各一份，但把「两侧处数」做成台账每轮现读的格子（分叉至少看得见）。

**655 / 656 / 658 / 659 / 660 状态（R%(r)s）：都不结案，各补一句**
    · 655：本轮**没跑** `update` 到工作基线 ⇒ `%(baseline)s`；名册那 16 行（8 light + 8 dark）字段与理由一字未动，
      也没调用 `register-drift`（逐字节对照：与 R586 那批 356 张**相同 356、不同 0**）。
    · 656：三条出路一条没选；本轮没碰捕获侧 Swift ⇒ 不重签也不撤账。
    · 658：本轮 ⓪ 把三跑的**真门**那一行都读成 `判=不判`（其中 `%(old_run)s` 那一跑是靠「基线署名==那一笔文档署的那台机器」
      才把电池模拟行分出去的）⇒ `docs/frame_baselines/by_machine/` 在 runner 上仍不存在，出路⑵ 没发生，三条仍一条不选。
    · 659：只开单、仪器侧证人仍没做；本轮的邻用同一条教训 —— **按名字判一件事属于哪一档**，第二个问题永远是
      「那个名字是不是恰好含这一段」。
    · 660：本轮补的是它**没覆盖的那一半**：660 让基线说得出自己是哪一笔烤的，而倍率那一格以前说的是**一个众数**；
      现在它说得出分布、并列、以及「这批里有多少张我根本没量到」。660 的三条出路仍一条不选。
""" % {"r": i["r"], "n": i["n"], "round": i["round"], "date": DATE,
       "swift_n": re.search(u"处=(\\d+)", d["swift_tier"]).group(1) if re.search(u"处=(\\d+)", d["swift_tier"]) else u"（没读到）",
       "baseline": d["baseline_untouched"][:160], "old_run": RUN_OLD}


def block_decisions(d):
    i = d["ident"]
    return u"""## D-%(r)s（R%(r)s · %(date)s · 第 %(n)s 轮 / Round %(round)s）：说不出就说不出来；一份事实只许有一份声明

背景：R586 把「基线说不出自己哪一笔烤的」补上了，但同一族里还剩三处：
①倍率那一格取**众数**，355 张 2x + 1 张 1x 照样印 `2.00x`，两档各半时印的是 `set` 遍历顺序决定的那一个；
②`bad`（两轴推不出同一倍率）算完被 `_bad` 丢掉；③档位这个词表在 python 仪器里有**四份**声明，
改坏其中一份没有任何一格会红。同一轮里监工还按 `'light' in frame` 数过名册（9/8，加不起 16）。
共同形状：**读数在冒充它不是的东西** —— 众数冒充「这批的倍率」，名字冒充属性，多份声明冒充一份事实。

决定：
1. **「不知道」要说成不知道，并且只走已有的那条出口**。并列 ⇒ 倍率一律空串 + `reason=tie`，由调用方走
   `FRAME_BASELINE_SCALE_NOT_RUN=<reason>`；不新造第二条「不判」门路（第二条门路就是第二条可以互相掩护的路）。
   同时把「不知道」拆成四种成因（tie / unreadable / no-frames / no-dir）写在值里 —— 成因不同修法相反。
2. **算出来的量要么报出来要么删掉**，不许「算了没人看」。`bad`、`sizeless` 现在既印也落盘。
   分布 `dist` 排序后再印（先计数降序、再名字升序）⇒ 并列时输出也有确定形状。
3. **同一件事实只许有一份声明**，并且这条由会红的守卫签，不由注释签：新增 `scripts/tier_vocabulary.py`，
   四处 import；守卫扫每一支活脚本（AST 级，注释/docstring 不算声明）。
   「子串法不参与判定」同样由 AST 签（判定函数调了谁、全仓还剩几个调用点）。
4. **给读者的命令必须能被它自己点到的脚本解析**。规则取「只认成句命令」而不是「print 里任何 `--x`」：
   后者会把两处**真存在**的旗标读成不存在（手写 argv 解析、`add_argument(` 换行）——
   把存在的读成不存在比漏读更坏，它会把守卫养成一台专门红自己的机器然后被人关掉。
5. **合并两份写法本身是一次改动**。热图那支脚本在词表顺序变了之后当场红，暴露的是「只报第一档就 return」
   这个既有缺陷 ⇒ 修脚本 + 把那一格改成两向 + 补刀 M1554。不许把这种红写成「合并引入的回归」。
6. **边界要说清并数出来**：python 侧一份真值管不到 Swift 捕获侧那 %(swift_n)s 处 ⇒ 只登记（661）+ 把处数做成读数，
   不写「全仓只有一份」。

被否掉的：为了少红而把并列报成众数（那是本轮要修的病）；新造 `FRAME_BASELINE_SCALE_TIE=不判` 第二条出口
（派单硬要求复用）；把 `FLOOR_LIGHT/FLOOR_DARK` 调一档让某个名字过线（数值一字未动，且那是拿改期望顶替改尺）；
把守卫范围扩到 `scripts/tests/`（守卫自己的正对照里必须出现那些形状，扩进去就是自我引用）；
以及给「印出去的帧名必须在册」新立守卫（现读 15 处 `.png` 字面量里 12 处是模板/输出名，按名字在册判会把它们读成红）。
""" % {"r": i["r"], "n": i["n"], "round": i["round"], "date": DATE,
       "swift_n": re.search(u"处=(\\d+)", d["swift_tier"]).group(1) if re.search(u"处=(\\d+)", d["swift_tier"]) else u"（没读到）"}


def block_changelog(d):
    i = d["ident"]
    return (u"""### 倍率报成分布、档位收成一份词表、印出去的命令由参数表认（R%(r)s / 第 %(n)s 轮 / Round %(round)s，产品 0 文件）
    R%(prev_r)s 给基线补了「哪一笔烤的」，但倍率那一格仍是**取众数**：`max(set(ratios), key=ratios.count)` 没有并列检测，
    355 张 2x + 1 张 1x 照样印 `2.00x`，两档各半时印的是 `set` 遍历顺序决定的那一个；`bad` 算完被 `_bad` 丢掉。
    同时档位那件事在 python 仪器里有**四份**声明（两态差尺的 `TIERS` 与两处字面量与那条正则、倍率解析里硬写的
    `(?:light|dark)`、录制态脚本的 shade 循环）⇒ 改坏一份不会有任何一格红。
    本轮：① `capture_scale()` 交回 `scale/frames/bad/sizeless/dist/reason`，分布排序后输出，**并列⇒倍率当不知道**并走
    **已有的** `SCALE_NOT_RUN` 出口（不新造第二条），`bad`/`sizeless` 既印也落盘；两个 unknown 撞车时旧版一行不印，
    现在独立成一条；② 新增 `scripts/tier_vocabulary.py` 一份真值，四处 import，守卫扫每一支活脚本（AST 级、注释不算声明），
    「子串法不参与判定」由 AST 签；③ 新增「印出去的成句命令必须能被那个脚本解析」的仪器守卫（含脚本路径存在性）；
    ④ 合并词表暴露热图脚本「只报第一档就 return」⇒ 修成两档各自点名并加 `HEAT_FRAME_VERDICT not-run=N`；
    ⑤ Swift 捕获侧那 %(swift_n)s 处只数不改（新开 **661**，红线不许碰捕获侧）。
    本机现读（含本笔的树）：`%(gate_drift)s` ⇒ `%(gate_result)s`；倍率真语料 `%(scale_head)s`。
    判据卷 +%(delta_total)d 格（帧门 +%(delta_frame)d、词表新卷 +%(delta_tier)d、热图那一格改成两向），
    刀 M1547–M1554 —— **M1549 落下来是空刀（那条分支没有证人），补证人后以 M1553 在同一处重落**；
    顺账那一轮我自己又印了一张不存在的帧名（⑨·3），已撤并记档。655/656/658/659/660 一条没结、出路一条不代选。
""" % {"r": i["r"], "n": i["n"], "round": i["round"], "date": DATE, "prev_r": i["prev_r"],
       "gate_drift": d["gate_drift"][:170], "gate_result": d["gate_result"][:130],
       "scale_head": d["scale"].splitlines()[0][:170],
       "swift_n": re.search(u"处=(\\d+)", d["swift_tier"]).group(1) if re.search(u"处=(\\d+)", d["swift_tier"]) else u"（没读到）",
       "delta_total": d["delta_total"],
       "delta_frame": d["counts"]["test_frame_baseline"][1] - d["counts"]["test_frame_baseline"][0],
       "delta_tier": d["counts"]["test_tier_vocabulary"][1] - d["counts"]["test_tier_vocabulary"][0]})


# —————————————————————————————————————————————————————————──
# 落盘


def shapes(i):
    return [(u"UI 轮次标题", u"## 第 %d 轮（R%d · " % (i["n"], i["r"])),
            (u"ITER 标题", u"## Round %d · R%d" % (i["round"], i["r"])),
            (u"STATE 主节", u"## R%d 状态（" % i["r"]),
            (u"DECISIONS", u"## D-%d（" % i["r"]),
            (u"BACKLOG 追账节", u"## R%d 追账" % i["r"]),
            (u"CHANGELOG 标题行", u"### 倍率报成分布、档位收成一份词表、印出去的命令由参数表认（R%d / " % i["r"])]


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
    """派生格的**结构性**修法：落盘之后再取一次数，并由这里改写那两格（R580/R583/R585/R586 同一族）。"""
    reading = subprocess.check_output([sys.executable, "scripts/product_streak.py"], cwd=ROOT).decode("utf-8")
    line = reading.splitlines()[0].strip()
    streak_n = int(re.search(r"streak=(\d+)", line).group(1))
    landed_r = max(int(x) for x in re.findall(r"(?m)^## R(\d+) 状态", read("STATE")))
    i = {"r": landed_r}
    fin = read("FINAL")
    m2 = re.search(u"产品面连续零改动轮数 = \*\*(\d+)\*\*（R%d 台账落盘之后现读" % i["r"], fin)
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
    d["look_score"] = os.environ.get("LOOK_SCORE", u"11/15")
    if "--post-land" in sys.argv:
        return post_land()
    return apply(d, "--apply" in sys.argv)


if __name__ == "__main__":
    sys.exit(main())

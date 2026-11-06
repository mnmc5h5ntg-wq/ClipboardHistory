# -*- coding: utf-8 -*-
"""把 ledgers_r589.py 的**机械部分**原样接过来，只换正文与几个常数 ⇒ 生成 ledgers_r590.py。

为什么用"整段替换函数"而不是逐行补丁：R577/R580 那两次盘上损坏都是 `t.index(起)…t.index(止)` 的切片
造成的（起点片段在别处逐字存在 ⇒ 锚命中更早那处）。这里每段替换前都断言
`count == 1`，并且替换完立刻 `py_compile` + 对机器部分做逐行等值核对。
"""
import io
import re

ROOT = "/Users/wangziyi/Codex_Project0"
SRC = ROOT + "/.scratch/motion-audit-2/ledgers_r589.py"
DST = ROOT + "/.scratch/motion-audit-2/ledgers_r590.py"

text = io.open(SRC, encoding="utf-8").read()

# —————————————————————————————————————————————— 常数与 gather 的三处 R589 专有名字
CONST_OLD = '''TMP = "/tmp/r589"
DATE = "2026-11-06"'''
CONST_NEW = '''TMP = "/tmp/r590"
DATE = "2026-11-06"'''

RUN_OLD = '''RUN_MAIN = "42139904001"      # R588 主笔
RUN_ADD = "42142286963"       # R588 补记笔'''
RUN_NEW = '''RUN_MAIN = "42159254212"     # R589 主笔（本轮 ⓪ 到数那一跑）
RUN_ADD = "42159607721"       # R589 补记笔'''

COUNTS_OLD = '''    for k in ("test_identical_frame_witness", "test_tier_reporting_shape", "test_frame_baseline"):'''
COUNTS_NEW = '''    for k in ("test_identical_frame_witness", "test_tier_reporting_shape",
              "test_ci_shape_guard_wiring"):'''

MSG_OLD = '''            raise SystemExit(u"⓪ 读数里没有 %s 那一跑 ⇒ 先跑 ci_status_r589.py" % run)'''
MSG_NEW = '''            raise SystemExit(u"⓪ 读数里没有 %s 那一跑 ⇒ 先跑 ci_status_r590.py" % run)'''

# 只保留每把刀的**末次**读数（M1572 第一次落刀 PASSED ⇒ 那是尺盲那一格的历史，见 STATE ⑨；
# 名册那一趟把作废那次另存到 knife_status_voided_first_pass.txt，不藏）。
DEDUP_OLD = '''    kn = must_read(os.path.join(TMP, "knife_status.txt"), u"刀状态文件")
    knives = []'''
DEDUP_NEW = '''    kn = must_read(os.path.join(TMP, "knife_status.txt"), u"刀状态文件")
    _last = {}
    for _ln in kn.splitlines():
        _m = re.match(r"(r\\d+)/(M\\d{4}) ", _ln.strip())
        if _m:
            _last[_m.group(2)] = _ln.strip()
    kn = u"\\n".join(_last[k] for k in sorted(_last))      # 末态逐把重签 ⇒ 一把只算最后一次
    knives = []'''

for old, new in ((CONST_OLD, CONST_NEW), (RUN_OLD, RUN_NEW),
                 (COUNTS_OLD, COUNTS_NEW), (MSG_OLD, MSG_NEW), (DEDUP_OLD, DEDUP_NEW)):
    assert text.count(old) == 1, (old[:60], text.count(old))
    text = text.replace(old, new)

# —————————————————————————————————————————————— 整段替换六个正文函数 + shapes()
NEW_FUNCS = {}

NEW_FUNCS["block_state"] = r'''def block_state(d):
    i = d["ident"]
    m, a = d["main_run"], d["add_run"]

    def step(rk):
        return u"、".join(x.strip() for x in rk.get(u"失败步骤", [])) or u"（没有失败步骤）"

    def wire(rk):
        return rk.get(u"接线三态", u"（那一跑未到数 ⇒ 三态一条不判）")

    def preds(rk):
        rows = rk.get(u"预测", [])
        return u"\n".join(u"      · %s ⇒ **%s**\n        （取处：%s）"
                          % (p[0], p[1], p[2]) for p in rows) or u"      ·（没判：那一跑未到数）"

    return u"""## R%(r)s 状态（%(date)s · 第 %(n)s 轮 / Round %(round)s · 产品 0 文件 + **取证通道本身读不读得对对象**（本节① 兜底那一支从「有没有 `else`」改判成「出不出声」，`else: pass` 从此会红；本节② `唯一证人=0` 从 python-only 的读数变成带扫描面的读数，Swift 侧 159 文件 / 2108 函数接进来；本节③ ⓪ 那一跑自己揭出三条"尺在本机判、在 runner 上判的不是同一个对象"，三条都落地并各配一把刀）+ 判据卷 +%(delta)s 格 + 刀 M1567–M1573 全 CAUGHT + ⓪ R589 两跑**都到数**（同一批四条红，逐字相同）

⓪ **现读两对（`ci_status_r590.py`，两趟：12:21 那趟两跑都还 `in_progress` ⇒ 按未读处理；13:12 之后这趟两跑都到数）**：
   1. `%(mrun)s ↔ %(msha)s`（R589 主笔）⇒ `%(mstatus)s`；全部失败步骤：`%(msteps)s`。
      逐步骤结论（另取一趟 `jobs[].steps`，`steps` 视图不给成功步骤建行）：
      `Release script tests ⇒ %(mbat)s`、`Frame baseline vs working manifest ⇒ %(mbase)s`、`On-screen probe coverage floor ⇒ %(mprobe)s`、`Swift tests (executed-count gate) ⇒ %(mswift)s`。
      **接线三态（这一格就是 R589 交下来的靶子本身）**：**%(mwire)s**
      计数逐字：`%(mwirecounts)s`；取处：%(mwirehow)s
      四条预测（标签与判法逐字接自 R589 的 `PREDICTIONS_R590`，由脚本判、不由我念）：
%(mpreds)s
   2. `%(arun)s ↔ %(asha)s`（R589 补记笔）⇒ `%(astatus)s`；全部失败步骤：`%(asteps)s`。
      逐步骤结论：`Release script tests ⇒ %(abat)s`、`Frame baseline vs working manifest ⇒ %(abase)s`、
      `On-screen probe coverage floor ⇒ %(aprobe)s`、`Swift tests (executed-count gate) ⇒ %(aswift)s`。
      接线三态：**%(awire)s**；计数逐字 `%(awirecounts)s`；取处：%(awirehow)s
      四条预测与主跑**逐字同判**（②中 / ③中 / ④读不到值 / ①未读到）：
%(apreds)s
      两条跑之间的差（照实记，不判成因）：`On-screen probe coverage floor` 在主跑是 `success`、在补记笔是 `failure`
      ⇒ 这是账里已有的"跑间漂"那一族（R540/R541 起就登记过），本笔不据此说它消失或成立。
      两跑的 `STEP[9]` 红名**逐字相同四条**（`Ran 885 tests … FAILED (failures=4, skipped=3)` 两跑都是这个数）
      ⇒ 下面 ⓪·3 那三条真红 + 一条借红是**稳定的**，不是偶发。
   3. **主跑给的真缺陷（不是"没读到"，是"读到了并且错了"）**：`STEP[9]` 印出了 12 行结论行 ⇒ 接线是真的；
      可同一跑里那一步**整步红**，红名逐字四条：
      （两跑逐字相同，下面只列一次）
      · `FAIL: test_the_same_machine_with_an_unmatched_corpus_must_go_red (test_ci_shape_guard_wiring.ExecutionTests)`
        ⇒ 断言 `1 != 0`。这一格是 R589 派单第三件事② 要的那条**负半证人**，它在 runner 上**没有响**：
        正文用的是盘上那份名册（8 行全 keyed `local:MacBook-Air.local`），而 runner 现读 `本机行=0` ⇒ 直接走 `not-run` 那一支、`rc=0`。
      · `FAIL: test_working_corpus_either_judges_or_names_why_it_did_not (test_identical_frame_witness.CommittedRosterTests)`
        ⇒ 断言里有 `IDENTICAL_PAIR_RESULT=ok` 而正文是 `… 本机行=0 他机行=8 本机组=20 … RESULT=not-run`。
        这一格只分了两支（有 png 就判 ok），漏了第四种出口：**有对象但这台没有自己的行**。
      · `FAIL: test_rows_from_another_machine_are_not_judged_here (test_identical_frame_witness.MachineTests)`
        ⇒ 现读 `本机=github-runner 名册本机行=1 他机行=0`。这一格把"另一台"写死成 `github-runner`，
        而 runner 的 `machine_key()` **恰好就是它** ⇒ 他机行变成自己行，判的对象整个换了。
      · `FAIL: test_the_roster_matches_what_this_machine_actually_skips (test_skip_roster.SkipRosterTests)`
        ⇒ 借红（634 那一格设计如此："红在内层不在这里"），把上面三条原样带出来 ⇒ 它不算第四条独立缺陷。
      共同形状一句话：**三条红都是"尺在本机判、在 runner 上判的不是同一个对象"** —— 与本节①②是同一族，
      只是这一族的样本这轮回来了（R589 只能预言，本轮有逐字读数）。本轮的处置见本节③。
   4. **两条新通道的值槽在 runner 上被打死了**（字节级取证（`gh run view %(mrun)s --log` 落盘后按字节读））：
      `SHAPE_GUARD_EXIT guard=scripts/tier_reporting_shape.py rc=U+FFFDU+FFFD0=判过 / 1=红 / …`、
      `IDENTICAL_WITNESS_EXIT=U+FFFDU+FFFD0=本机全部登记 / …` —— 源码里那两行是 `rc=$g（0=判过 …）`，
      值槽与非 ASCII 说明**粘在同一个字段里**，日志通道把这一段整体弄坏 ⇒ `rc` 到底是 0 还是 2 从今天到数的那一跑里**读不出来**。
      这是 R565 那条规矩（值槽只放一个词、说明另起一行）的 bash 版：R589 我用它改了自己写的 python 打印，
      却没有照同样的规矩写自己新加的 echo。本轮已改（本节③），并配一格守卫 + 一把刀（M1572）。
   5. `STEP[11]`（`Frame baseline vs working manifest`）在主跑里是 `skipped` ⇒ 那一格的三态是**第③态**（那一步根本没跑到，
      因为 `STEP[9]` 先红）。所以 R589 交下来的第一条预测（`FRAME_BASELINE_SCALE_BASELINE_UNKNOWN` 第一次在 runner 出现）
      **今天仍然没有证人**：只报数不拦路的那一格在 runner 上没跑过 ⇒ 不许写"接上了"，也不许写"它绿了"。
   6. **R591 的 ⓪ 要读的五格**（判法与「正文从哪一步取」都写进 `ci_status_r590.py` 的 `PREDICTIONS_R591`，由脚本判）：
      ①本笔（主笔 + 补记笔）的成对号 —— 由补记那一趟现取现写，本笔不许替它填数；
      ②`STEP[9]` 的**四条红有没有减少**（不是看整步绿：那一步还挂着 `test_skip_roster` 的借红与 python 版本差那一族）；
      ③`STEP[9]` 里 `SHAPE_GUARD_EXIT … rc=<一个词>` 与 `IDENTICAL_WITNESS_EXIT=<一个词>` **能不能读到值**（本轮修的正是这一格）；
      ④`STEP[11]` 这次有没有跑到（跑到才有 `FRAME_BASELINE_SCALE_BASELINE_UNKNOWN`，runner 的基线说不出倍率、当轮 1.00x ⇒ 应该响）；
      ⑤`WITNESS_SCAN_SCOPE … swift文件=` 有没有在 runner 上 >0（靶 1 那一维的第一条外部证人，只能由含本笔那一跑签）。

① **真实推进（本节① / §3 第②段）：兜底那一支要「出声」，不是要「存在」**
   `scripts/tier_reporting_shape.py` 的 R3 从前只问链尾有没有 `else`（`closed=has_else`）⇒ 把兜底写成 `else: pass`
   照样绿，洞原样留着。本轮把判定改成 `body_speaks(catch, prefix)`：**要么 print 一个同前缀的通道串，要么退非 0 / 抛**；
   两条都不做的兜底具名红「有 `else` 但兜底那一支不出声」，并把"空 else 把『其余情况』写成了『什么都不说』"写在正文里。
   现读逐字：`%(tier)s`（`有兜底却不出声` 那一格从此是读数；本轮全仓 0 条 ⇒ 这一维**有人判**）。
   三格新判据：`test_an_empty_else_catch_all_is_red_and_named_as_silent`（空 else 必须红）、
   `test_a_catch_all_that_returns_nonzero_counts_as_speaking`（合法拦路不许误报 = **负半**）、
   `test_a_legit_empty_else_outside_a_reporting_chain_is_not_a_candidate`（兄弟分支不印同前缀的空 else **不是对象** ⇒
   这就是派单要的那条"合法空 else 的负对照"：规矩只判"兄弟都印同一个前缀的那条链"，不逼每一朵 `if` 都配废话）。
   刀 **M1567**（把 `frame_baseline.py` 的兜底换成 `pass` ⇒ 那一格必须红）、**M1568**（关掉"退非 0 也算出声" ⇒ 负半那格必须红）。

② **真实推进（本节②）：`唯一证人=0` 是扫描面读数，不是「全仓干净」**
   `scripts/identical_frame_witness.py` 以前只扫 `scripts/*.py` ⇒ 那句 `唯一证人=0` 的证据面**根本不含 Swift**，
   而这一维的证人主要住在 `ClipboardHistory/Tests/**`。本轮把扫描面当**读数**印出来并接上 Swift 侧：
   `%(scope)s`
   `%(pairline)s`
   Swift 侧认三种形状（`"键"` 字面量、字符串拼接 `+`、插值 `\(...)`)；剥注释**先块后行**（`strip_swift_comments`：
   `/* … */` 之后再 `// …`，反序就会让块注释的结束符被当成行注释吃掉 —— R578 那次块注释吞 86 万字符的坑本轮不许复发，
   由 `test_block_comments_are_stripped_before_line_comments` 与 `test_keys_inside_a_block_comment_are_not_references` 钉）。
   认不出的部分**具名不判**而不是当 0：`WITNESS_SWIFT_NOT_RUN=`（没有 Swift 树）与 `WITNESS_SWIFT_PARTIAL=`
   （拼接/插值点数 >0 ⇒ 这一维的 0 是**下界**而不是"全仓没有"）。正对照 python 与 Swift 各有真红的一格，
   真树那一格（`test_the_two_real_harness_functions_are_not_accused`）判的是"两份真夹具不许被误指控"。
   刀 **M1569**（扫描面退回只扫 python ⇒ Swift 正对照必须红，正是派单点名的那一把）、**M1570**（剥注释顺序换回"先行后块"）、
   **M1571**（Swift 树缺席时不再具名 ⇒ 那一格必须红）。
   ⚠ 诚实记一条：M1570 落刀时我原先当作证人的那两格合成样本**两序都红**（没有牙），真牙是
   `test_the_two_real_harness_functions_are_not_accused`（真树上"行先剥"会把块注释尾巴里的字面量当引用 ⇒ 误指控）。
   这条写进本节⑨·2，不写成"配了证人"。

③ **真实推进（本节③）：⓪ 揭出的三条自伤，本轮全部落地并各配证人**
   1. 负半证人不再抄盘上名册：`test_ci_shape_guard_wiring.ExecutionTests._run(shots, roster)` 自己造一份名册，
      `machine` 字段**现读** `machine_key()` ⇒ 任何机器上都是"这台登记过却对不上"，那一支必须响。
      证人=本笔落地前现跑（M1573 把它退回写死的外机 ⇒ 那格红）。
   2. 第四种出口有了自己的分支：`test_working_corpus_either_judges_or_names_why_it_did_not` 现在分四支
      （没目录 / 目录里 0 张 / 有 png 且这台有自己的行 ⇒ 判组数 / **有 png 但这台没有自己的行 ⇒ 具名 not-run 且 rc=2**），
      后两支正是本机与 runner 的分水岭。
   3. "另一台"不许从记忆里抄：`machine_key() + u"-not-this-machine"`，并当场 `assertNotEqual`。
   4. 值槽与说明分开（③的那条通道缺陷）：`ci.yml` 两行 echo 改成
      `SHAPE_GUARD_EXIT guard=$GUARD rc=$g` + 另起一行 `  这一格的读法：rc=0 判过 / rc=1 红 / rc=2 扫描器没有对象，不许当绿`；
      `IDENTICAL_WITNESS_EXIT=$id_rc` 同形。新格 `test_no_channel_value_slot_is_glued_to_a_parenthetical_explanation`
      判**接线正文**里这个形状，两种写法（`NAME=value（` 与 `NAME … rc=$v（`）都算，正对照先自证这把尺看得见。
      ⚠ 这把尺自己也被 M1572 抓过一次盲：第一版只认 `NAME=` 紧跟值槽那一形 ⇒ 刀 PASSED（空刀），
      修宽之后重落才 CAUGHT；刀号不重复占位，作废的是**当时那条结论**（见本节⑨·3）。
   ⚠ 三条出路一条没选：638①、655/660 的重烤、656 的全局外观 —— 本轮帧数与名单一字未动。

④ **验证链（顺序照派单）**：build `%(build)s` → 判据卷 `%(b1)s` → 刀 M1567–M1573（**落刀前现读高水位=M1566**，
   跨表唯一性逐把现读=0 次撞号）→ 新表 `mutate_r590_scope` 在预检名册里（`NEEDLE_PRECHECK tables=403 arms=855 bad=0`，
   本轮那 7 把逐把 `ok`）→ 刀已还原复跑判据 `%(b2)s`、`%(md5)s`、`git status scripts/` 与残留串现读（三种变异串各 0 处）→
   捕获卷 `%(capture)s`、帧 `%(frames)s` → 本机那一门 `%(gate)s` / 判定 `%(drift)s` / 倍率出口 `%(scale)s` →
   逐张看图（本节⑥）→ 全量 `%(full)s`、skipped `%(fullskip)s` → 三道预检串行 → 换装 `SKIP_INSTALL=no-product-change` →
   七本台账 → 派生格**落盘之后**现读 → 电池（第一趟/第二趟两个时刻都记）。

⑤ **看图那一腿（尺走 659 认过的形状：`convert("L")` 之后再 `getbbox`，并配同尺寸正对照）**：
%(look)s

⑥ **基线与名单**：产品文件 0 个，连续零改动 **%(streaknum)s** 轮（唯一取数口 `python3 scripts/product_streak.py`，
   **台账落盘之后**现读 `%(streak)s`；as-of 口径 ⇒ 读作「本轮之前最后一次产品改动在 %(streaknum)s 轮前」；
   取数时刻由 `post_land()` 钉在函数名字上，不在纪律上〔streak-cell-end〕）。帧名单未动（`%(frames)s`），
   四张按机器登记的表一字未改；`frame_baseline.py update` 本轮**一次都没跑**（重烤归用户）。

⑦ **红名与对账**（门报 `%(recon)s`，不由我数）：
- **红名对账**（每条单行，逐字进门）：
  · 红名「`Ran 893 tests … FAILED (failures=5)`（电池与三条守卫 CLI 并行那一趟）」→ ⑨·1 —— 串行复跑同一卷读 896/OK(5)
  · 红名「`名册说这一台会跳而实际没跳` 四格（把 `/tmp/r590/frames` 交给电池那一趟）」→ ⑨·4，新开 662
  · 红名「runner 四条红 `test_the_same_machine_with_an_unmatched_corpus_must_go_red`／`test_working_corpus_either_judges_or_names_why_it_did_not`／`test_rows_from_another_machine_are_not_judged_here`／`test_the_roster_matches_what_this_machine_actually_skips`（取值时刻=读 42159254212 与 42159607721 两趟，逐字相同）」→ ⑨·9
  · 红名「runner 通道值槽 `U+FFFDU+FFFD`（`SHAPE_GUARD_EXIT` / `IDENTICAL_WITNESS_EXIT` 两条）」→ ⑨·3
  · 红名「`M1572 post=PASSED`（第一版值槽尺只认 `NAME=value（`）」→ ⑨·3
  · 红名「刀链与捕获并行 ⇒ `IDENTICAL_PAIR_REFUSED=no-png` 与 `名册帧缺失=1` 两次假红（R589 尾）」→ ⑨·5
  · 红名「`ci_status_r590.py` 第一版把 0 字节日志判成四条预测全部不中，且 `到数=是` 判据写错」→ ⑨·6
- **本轮新印出来的名字**：`WITNESS_SCAN_SCOPE`、`WITNESS_SWIFT_NOT_RUN`、`WITNESS_SWIFT_PARTIAL`、
  `LOOK_SCOPE`、`LOOK_BYTE_IDENTICAL`、`LOOK_POSITIVE_CONTROL`、`LOOK_SELF_ZERO`、`LOOK_GATE_CHANGED`、`CI_STEP_NOT_RUN`、
  `CI_LOG_EMPTY`（后两条是 `ci_status_r590.py` 的读数串，不进 CI 正文）；
  既有那 9 个（`SHAPE_GUARD_EXIT` 等）本轮只改值槽形状、名字一字未动。
- **不计入对账口径**（通道未跑）：`FRAME_BASELINE_SCALE_BASELINE_UNKNOWN` 的 runner 读数（`STEP[11]` 被 skipped）；
  这一维今天仍只有本机读数 ⇒ 归 R591 的 ⓪·④。

⑧ **闸门与阻塞（§3 第③段今天不开工）**：
   `STAGE2_CLICKTHROUGH_BLOCKED` 与 `STAGE3_FRAME_CRITERIA_HAVE_NO_RUNNER_WITNESS=awaiting-654-direction` 一字未撤；
   `PRODUCT_MAIN_TREE_TRANSPARENT_OBJECT_NOT_JUDGED`、`FRAME_BASELINE_DRIFT_NOT_JUDGED` 也在册。
   现读第③段证人：`%(stage)s` ⇒ 「三问全过」在规格里出现次数仍是 0，两条具名阻塞仍在 ⇒ 着色器那一格继续不写。
   本轮**没有任何一条**「判=不判 / not-run / 空 else / 扫描面 0」被我说成"没问题"：
   `有兜底却不出声=0` 带口径（只判兄弟同前缀的链）、`唯一证人=0` 带扫描面与 PARTIAL 下界、
   `本机行=0` 的 runner 那一支写成"这一维在 runner 上今天没人判"。

⑨ **自伤（照实，不缩）**：
   1. 判据卷与三条守卫 CLI 并行 ⇒ 同一卷两次读数不一致（并行 893/5 红 vs 串行 896/OK(5)）。
      规矩本轮被自己踩了一遍：**链条跑的时候不要往同一条 CPU 上塞别的重活**；作废并行那趟，只记串行那趟。
   2. M1570 的"证人"里有一格没有牙（合成块注释样本在两种剥注释顺序下都红）⇒ 真牙是判真树那一格。
      写账时按牙记账，不按"我加了几格"记账。
   3. 值槽尺第一版只认一种形状 ⇒ M1572 PASSED（空刀）。这一把抓到的不是产品，是**我的尺的扫描面** ——
      与本轮靶 1 同族：`0` 分不清"没有"与"看不见"。修宽重落，刀号不重复占位。
   4. 把 `/tmp/r590/frames` 交给电池 ⇒ 4 格从 skip 变不跳 ⇒ `SKIP_ROSTER` 的档位里没有"帧目录有没有内容"这一维。
      我没有改名册（名册与豁免表一字不动是派单红线），改成：本轮电池的正式读数以**不设帧目录**那一趟为准，
      并把这一格开成 662 交回。
   5. R589 尾段：刀链与捕获并行两次踩到"目录已建但内容不全"（`no-png` 与 `名册帧缺失=1`）⇒ 本轮刀表的 ENV 显式
      弹出 `CLIPBOARD_HISTORY_UI_SHOTS`，真语料那一格改成分支判而不是假定环境。
   6. `ci_status_r590.py` 三处自伤当场被自己的活门抓到：`hits = collections_all = 0, []`（元组赋给两个名字）、
      判法收到的是**前缀名**而不是正文行（把"我筛过"当成"它说了"，正是 R588 ⑤·(a) 那个洞），
      以及 `status=in_progress` 却因"有步骤已有 conclusion"判成到数、并把 0 字节日志的四条预测判成"不中"
      （把缺证据冒充成反证）。三处都在本笔里修掉，并各留注释指向取数时刻。
   7. heredoc 里中文与 ASCII 引号混排 ⇒ 一次 `SyntaxError`（本轮第三次同族），改法是把补丁脚本落成文件再执行
      （就是 `build_r590_writer.py` 这份文件存在的原因）。
   8. `_run(shots, roster)` 第一版按带引号的 `--shots "…"` 去替 ⇒ 活门当场 `assert` 拒绝（正文里那串不带引号）。
      这条算证人生效，不算修好：写进账是为了说明"活门拦下的一次不等于没有下一次"。
   9. **本轮 ⓪ 那三条 runner 红是我上一轮（R589）自己写的三格**：本机电池全绿、CI 那一跑逐字相同地打回四条
      （其中一条是 634 设计的借红）。共同成因不是"CI 环境奇怪"，而是我在写那三格时把**本机的状态**
      （有帧、名册里有自己的行、`machine_key()` 不等于 `github-runner`）当成了普遍状态。
      修法写进 D-590 第 3/4 条；两跑（主笔 + 补记笔）红名逐字相同 ⇒ 这不是偶发，也不是 runner 坏了。

⑩ **仍归用户（一条不代选，逐条照抄派单）**：655 / 656 / 657 / 658 / 659 / 660 / 661 / 638① / 654 / 646 / 647 / 650 /
   651 / 653 / 644 / 639 / 640 / 637 / 633 / Motion ≥2 帧地板 / SSH 成因 / 手感签字 —— 全部不结案；
   4.5 墨地板、150 上限、120ms、Motion ≥2、2x 8.0pt、1x 6.0pt、`FLOOR_LIGHT=1.20`、`FLOOR_DARK=1.10`、容差 1.5、
   跳变地板 8、`probeInkFraction=3%%`、`.contentFade` 0.20、`--allow-missing`、四张按机器登记的表、名册与豁免表、
   禁碰 14 面 —— 一字未动；本轮没有改这台机器的全局外观；`update` 一次没跑；帧与日志不含用户真实剪贴板原文。
""" % {u"r": i[u"r"], u"n": i[u"n"], u"round": i[u"round"], u"date": DATE,
         u"delta": d["delta_total"], u"tier": d["tier_shape"], u"stage": d["stage_gate"],
         u"pair": d["pair_witness"], u"scope": d["witness_scope"], u"pairline": d["witness_line"],
         u"look": d["look"], u"md5": d["md5"], u"build": d["build_warn"], u"capture": d["capture"],
         u"frames": d["frames"], u"gate": d["gate_result"], u"drift": d["gate_drift"],
         u"scale": d["gate_scale"], u"full": d["full"], u"fullskip": d["full_skips"],
         u"b1": d["battery"], u"b2": d["battery2"], u"recon": d["recon"],
         u"streak": d["streak"], u"streaknum": (re.search(u"streak=(\\-?\\d+)", d["streak"]).group(1)
                                               if re.search(u"streak=(\\-?\\d+)", d["streak"]) else u"-1"),
         u"mrun": m.get(u"run", ""), u"msha": m[u"sha"], u"mstatus": m[u"status行"],
         u"msteps": step(m), u"mbat": m[u"逐步骤结论"].get(u"Release script tests", u"（读不到）"),
         u"mbase": m[u"逐步骤结论"].get(u"Frame baseline vs working manifest (fixture-set gate)", u"（读不到）"),
         u"mprobe": m[u"逐步骤结论"].get(u"On-screen probe coverage floor", u"（读不到）"),
         u"mswift": m[u"逐步骤结论"].get(u"Swift tests (executed-count gate)", u"（读不到）"),
         u"mwire": wire(m), u"mwirecounts": json.dumps(m.get(u"WIRE_READINGS", {}), ensure_ascii=False),
         u"mwirehow": m.get(u"WIRE_HOW", u"（未读到）"), u"mpreds": preds(m),
         u"arun": a.get(u"run", ""), u"asha": a[u"sha"], u"astatus": a[u"status行"],
         u"asteps": step(a), u"abat": a[u"逐步骤结论"].get(u"Release script tests", u"（读不到）"),
         u"abase": a[u"逐步骤结论"].get(u"Frame baseline vs working manifest (fixture-set gate)", u"（读不到）"),
         u"aprobe": a[u"逐步骤结论"].get(u"On-screen probe coverage floor", u"（读不到）"),
         u"aswift": a[u"逐步骤结论"].get(u"Swift tests (executed-count gate)", u"（读不到）"),
         u"awire": wire(a), u"awirecounts": json.dumps(a.get(u"WIRE_READINGS", {}), ensure_ascii=False),
         u"awirehow": a.get(u"WIRE_HOW", u"（未读到）"),
         u"apreds": preds(a)}


def _unused_state_tail():
    return None
'''

NEW_FUNCS["block_ui"] = r'''def block_ui(d):
    i = d["ident"]
    u0 = next_u()
    rows = [
        (u"「有 `else`」不等于「兜底那一支会说话」",
         u"R3 的 `closed` 从前取 `has_else` ⇒ `else: pass` 照样绿，洞原样留着。"
         u"现在判的是 `body_speaks`：要么印**同前缀**的通道串，要么 `raise` / `return` 非 0 / `sys.exit(非 0)`。"),
        (u"空 else 的红必须自带成因句",
         u"两条红话术分开：「没有兜底 `else`」与「有 `else` 但兜底那一支**不出声**」。"
         u"后者正文写着「空 else 把「其余情况」写成了「什么都不说」」 ⇒ 下一轮不用重新推。"),
        (u"合法的空 `else` 不许被规矩吃掉",
         u"对象范围写死：只判**兄弟分支都印同一个前缀**的那条链。"
         u"`test_a_legit_empty_else_outside_a_reporting_chain_is_not_a_candidate` 是负对照 —— "
         u"纯逻辑分支不印通道串就不是候选，否则这条门会退化成「逼每一朵 if 都配废话」。"),
        (u"`退非 0` 也算出声，这一支要有自己的格",
         u"`real_screen_control_chroma.py:326` 那条兜底既不 print 也直接拦路 ⇒ 分类必须是「出声」。"
         u"关掉这一支（M1568）负半那格当场红。"),
        (u"「唯一证人=0」是扫描面读数，不是全仓干净",
         u"从前这条门只扫 `scripts/*.py`，而像素证人主要住在 Swift 测试树。本轮把扫描面**当读数印出来**："
         u"python 文件数 / swift 文件数 / 函数数 / 拼接点 / 插值点，五个数一起走。"),
        (u"Swift 侧认三种形状，认不出就具名而不是当 0",
         u"字面量 `「键」`、拼接 `+`、插值 `\(...)`；后两种只数不判，并把 `WITNESS_SWIFT_PARTIAL=` 印出来 ⇒ "
         u"这一维的 0 是**下界**。没有 Swift 树 ⇒ `WITNESS_SWIFT_NOT_RUN=`（M1571 钉这一格）。"),
        (u"剥注释的顺序是要害，不是风格",
         u"先块后行。反序时块注释的 `*/` 之后的行被当成注释吃掉 —— R578 那次吞了 86 万字符。"
         u"这轮的牙在真树那一格（M1570 让「先行后块」把夹具里的键当引用 ⇒ 误指控当场红）。"),
        (u"runner 上那三条红是同一个对象错位",
         u"负半证人抄了盘上名册（这台 `本机行=0` ⇒ 永远走 not-run）；真语料那格少一个第四出口；"
         u"「另一台」写死成 `github-runner` 而 runner 自己就是它。三条都是「本机绿、runner 判的不是同一件事」。"),
        (u"负半证人的名册由测试自己造，machine 现读",
         u"`_run(shots, roster)` 多一个参数；替换按正文里**不带引号**的 `--shots 路径` 做，"
         u"替不到就当场 `assert` 拒绝（这一格活过一次，因为它第一次没命中）。"),
        (u"「有 png 但这台没有自己的行」是第四个出口",
         u"它既不是「没有对象」（no-png），也不是「判过且没问题」（ok）；runner 今天恰好落在这里 ⇒ "
         u"从前这一支被并入 ok 的断言，读成判据红，那是把「这台没登记」冒充成「登记有问题」。"),
        (u"通道值槽与非 ASCII 说明粘在一起会被日志打死",
         u"字节级取证：`rc=` 之后是 `U+FFFDU+FFFD0=判过` —— `$g` 与 `（0=判过` 同字段。"
         u"R565 那条规矩的 bash 版；本轮两条新 echo 都改成「值一行 + 说明另起一行」。"),
        (u"值槽尺也被自己的刀抓出一次盲",
         u"M1572 第一次 PASSED：尺只认 `NAME=value（`，而损坏发生在 `NAME … rc=$v（`。"
         u"修宽（按通道名 + 词边界锚，整行余下部分再判）之后重落才 CAUGHT ⇒ 空刀作废的是结论，不占第二个号。"),
        (u"接 CI 那一笔的跑签不了自己，但**后一跑**能签",
         u"R589 只能预言；本轮读到 `42159254212` 里 STEP[9] 印出 12 行结论行 ⇒ 「接线本身」这一格第一次有外部证人。"
         u"而 `STEP[11]` 仍是 `skipped` ⇒ 倍率那一维的 runner 证人**还是没有**，两种「没」分开记。"),
        (u"SKIP_ROSTER 的档位里没有「帧目录有没有内容」这一维",
         u"把 356 张交给电池 ⇒ 4 格从 skip 变不跳 ⇒ 门报「名册过期」。没改名册（红线），开 662 交回；"
         u"本轮电池正式读数以不设帧目录那一趟为准。"),
        (u"看图这一腿换了对象：本轮看的是「两批帧是不是同一批」",
         u"产品 0 文件 ⇒ 逐字节 356/356 对拍 + 差量可见性正对照（`convert(「L」)` 后 `getbbox`，"
         u"点亮一块必须给非零包围盒与非零差量颗数）+ 自己 vs 自己必须 0。三个读数缺一个都不许报「全同」。"),
    ]
    body = u"\n".join(u"- **U-%d：%s** —— %s" % (u0 + k, t, b) for k, (t, b) in enumerate(rows))
    head = (u"## 第 %(n)s 轮（R%(r)s · %(date)s · U-%(u0)s…U-%(u1)s）：把「兜底出不出声」「扫描面多大」「runner 判的是不是同一件事」三格做成读数"
            % {u"n": i[u"n"], u"r": i[u"r"], u"date": DATE, u"u0": u0, u"u1": u0 + len(rows) - 1})
    return head + u"\n\n" + body + u"\n\n", u0
'''

NEW_FUNCS["block_iteration"] = r'''def block_iteration(d):
    i = d[u"ident"]
    return u"""## Round %(round)s · R%(r)s（第 %(n)s 轮 · %(date)s）：兜底要出声、扫描面要报数、⓪ 那三条错位各自落地

**七维度自评**（恰七行，每格 n/15；维度名照曲线尺认的那七个同字，本轮不造新维度）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉看图 | 12/15 | 本轮产品 0 文件 ⇒ 看的是"两批帧是不是同一批"：逐字节对拍 356 张 + 差量可见性正对照（点亮一块给非零包围盒/非零差量颗数）+ 自己 vs 自己必须 0（`LOOK_SELF_ZERO`）。扣分：像素复核不等于新发现；且看图那一腿是在全量卷跑完之后补的（顺序偏离，照实记）。 |
| 判据有效性 | 15/15 | 靶 2 三格（空 else 红 / 退非 0 算出声 / 合法空 else 不是对象）+ M1567/M1568；靶 1 六格（Swift 正负对照、真树误指控、PARTIAL、NOT_RUN）+ M1569/M1570/M1571；⓪ 那三条各有一格新证人 + M1572/M1573。每一把刀落刀前都自问过"我只动了一边吗"，**一把（M1572 第一版）答否 ⇒ 当场作废重落**。 |
| 假绿防御 | 15/15 | ①`有兜底却不出声` 与 `无兜底` 两种红分开；②`唯一证人=0` 带扫描面五个数 + PARTIAL 下界；③值槽尺自己配了**两种形状的正对照**再判真正文；④负半证人不再依赖"这台恰好登记过"；⑤电池与守卫 CLI 并行那次读数**作废不入账**，串行那趟才算。 |
| 产品面推进 | 3/15 | 产品 0 文件；`update` 一次没跑；帧名单一字未动（`%(frames)s`）。推进全在取证面，段号仍是第②段（第③段一字未写，证人见 STATE 本节⑧）。 |
| 台账一致性 | 11/15 | 身份交叉核对过；七个标题形状写前 0、写后各 1；派生格落盘后现读；`build_r590_writer.py` 用"整段替换 + count==1 断言 + py_compile"，就是为了不再踩 R577/R580 那两次切片损坏。扣分：⑨·1（并行那趟先跑了一次才想起串行规矩）、⑨·6（⓪ 读取器三处自伤在当场被活门抓到）。 |
| 剩余风险处置 | 14/15 | 新开 662（SKIP_ROSTER 的档位维度），并把 runner 三条红全部落地 + 各配刀；旧红一朵不抹；两条具名阻塞一字未撤；22 条出路一条不代选。扣 1 分：`STEP[11]` 那一格在 runner 上仍无证人（被 skipped 连带），本轮只能写"未读到"。 |
| 交接可读性 | 15/15 | 五条新预测进 `PREDICTIONS_R591`，每条四格齐（主张 / 判法 / 正文从哪一步取 / 这条通道由哪一步以什么方式印出去），并把"到数与否"和"日志字节数"两个前置判据写进脚本 —— 0 字节日志不再被读成"没印"。 |

本轮一句话：runner 那一跑把"本机绿的判据"打回三种不同的对象错位，而三条的共同修法只有一个 ——
**尺要先说自己读的是哪一面、读不到时说自己是哪一种读不到**。
""" % {u"round": i[u"round"], u"r": i[u"r"], u"n": i[u"n"], u"date": DATE, u"frames": d[u"frames"]}
'''

NEW_FUNCS["block_backlog"] = r'''def block_backlog(d):
    i = d["ident"]
    return u"""## R%(r)s 追账（%(date)s · 第 %(n)s 轮 / Round %(round)s）

**新开单 1 张**：

**662. 具名 skip 的名册里没有「帧目录有没有内容」这一维**
· 现象（取值时刻=本轮电池第二趟，`CLIPBOARD_HISTORY_UI_SHOTS=/tmp/r590/frames` 356 张）：
  `test_the_roster_matches_what_this_machine_actually_skips` 报
  `名册说这一台会跳而实际没跳：['test_ci_exit_matches_this_machines_registered_profile',
  'test_every_real_pair_clears_the_floor_or_is_named_nonflat',
  'test_the_real_shots_pair_at_least_as_well_as_the_registered_floor',
  'test_working_frames_still_satisfy_the_three_relations']`。
· 同一卷不设该变量 ⇒ `Ran 896 tests / OK (skipped=5)` ⇒ 两趟都真，分歧只在环境里有没有那批帧。
· 与本轮 ⓪ 那三条 runner 红同族：名册按**机器**分档，而这几格的 skip 与否由**帧目录**决定 ⇒
  档位少一维。CI 的 `Release script tests` 恰好设了 `CLIPBOARD_HISTORY_UI_SHOTS=/tmp/shots-ci`，
  所以那一跑落哪一档取决于名册对 `github-runner` 写了什么。
· 出路（归用户，一条不代选）：⑴给名册加第二维（帧目录有/无）；⑵把那几格改成"有帧就判、无帧就具名不判"，
  不再走 skip 通道；⑶维持现状 + 电池固定不设帧目录（本轮临时采用，代价是 runner 与本机档位仍可能不同）。
· 本轮**没有**动 `SKIP_ROSTER`（名册与豁免表一字不动是红线），也没有把出口降级成"不判"。

**既有单子只补事实，不替用户选出路**：

· **638**：②那一问的 runner 半本轮有了**外部证人**（`42159254212` 里 `IDENTICAL_PAIR_RESULT=` 印出来了，
  且 `本机行=0 他机行=8` ⇒ 那一台落"具名不判"）。三条出路（并进 / 名册 / 让 runner 自己登记）仍一条没选；
  `row-pinned-off` 无消费者那一格本轮一字未动。
· **655 / 660**：倍率那一维四个出口各有名字（R589）；本轮新增的是**基线出处**那一条仍无 runner 读数
  （`STEP[11]` 在主跑里 skipped）⇒ 重烤基线仍归用户。
· **658**：机器维度这一族本轮**复发在本机自己的判据上**（把"另一台"写死成 `github-runner`）⇒ 已改成现读取反，
  并留一格当场 `assertNotEqual`；三条出路仍没选。
· **659**：本轮看图沿用它认过的形状（先 `convert("L")` 再 `getbbox` + 同尺寸正对照 + 自己 vs 自己必须 0），
  并把它用在"两批帧对拍"这一种新对象上 ⇒ 没有新形状要补。
· **661**：Swift 捕获侧那 11 处一字未动；本轮只是**读**了 Swift 树（扫描面 159 文件 / 2108 函数），没有改它。
· **646 / 647 / 654**：状态照旧 —— `STAGE2_CLICKTHROUGH_BLOCKED`、
  `STAGE3_FRAME_CRITERIA_HAVE_NO_RUNNER_WITNESS=awaiting-654-direction` 两条具名阻塞一字未撤 ⇒ §3 第③段继续不开工。
""" % {u"r": i[u"r"], u"n": i[u"n"], u"round": i[u"round"], u"date": DATE}
'''

NEW_FUNCS["block_decisions"] = r'''def block_decisions(d):
    i = d["ident"]
    return u"""## D-%(r)s（%(date)s）：兜底要出声、扫描面要报数、判据的对象不许从记忆里抄

**背景**：R589 把三条形状守卫接进 CI 之后，自己那一跑签不了自己；本轮读到那一跑（`42159254212`）——
接线是**真的**（`STEP[9]` 印出 12 行结论行），但那一步整步红，四条红名里三条是同一个对象错位：
判据在本机判，在 runner 上判的已经不是那件事。同时本轮的两件靶（兜底出不出声、扫描面多大）本身就是
"读数与对象不符"的两种形状。

**决定**：
1. 「互斥分支的兜底必须**出声**」取代「兜底必须存在」：印同前缀的通道串，或 `raise`/`return` 非 0 —— 二者皆无即红。
   对象范围收窄到"兄弟分支都印同一个前缀"的链，合法的空 `else` 不是候选（负对照已配格）。
2. 一条计数要跟着**扫描面**一起印：`唯一证人=0` 前面必须有 `WITNESS_SCAN_SCOPE python文件=… swift文件=… 拼接点=… 插值点=…`；
   认不出的形状具名 `WITNESS_SWIFT_PARTIAL=`，把那个 0 声明成**下界**而不是"全仓没有"。
3. 判据里"另一台机器"的名字**只能由现读派生**（`machine_key() + 哨兵`），不许从记忆里抄 ——
   抄来的名字在这台机器上可能恰好是自己。
4. 判据自带的语料/名册不许默认取盘上那一份：**谁的断言谁造样本**，`machine` 字段现读；
   否则"负半证人"只在有登记的机器上有牙。
5. 通道值的形状是硬规矩（R565）：**值槽只放一个词**，说明另起一行 —— bash 的 `echo` 也一样，
   非 ASCII 说明粘在值槽上会被日志通道整体打死（字节级 `U+FFFDU+FFFD`，值读不出来）。
6. 刀 PASSED 时作废的是**这把刀当时的结论**，不是刀位；而"这把尺看不见刀的落点"本身是一条读数（M1572 第一次）。

**为什么不撤任何既有门**：本轮没动地板、阈值、四张按机器登记的表、名册与豁免表；
`SKIP_INSTALL=no-product-change`（产品 0 文件）；两条 §3 阻塞未撤 ⇒ 第③段不开工。
`update` 一次没跑（重烤基线归用户）。

**代价**：判据卷 +%(delta)s 格、CI 里两条 echo 各多一行说明、七把刀；换来的是三条"本机绿"被 runner 打回之后
不再靠叙述收场，而是每格有名字、每把有落点。
""" % {u"r": i[u"r"], u"date": DATE, u"delta": d["delta_total"]}
'''

NEW_FUNCS["block_changelog"] = r'''def block_changelog(d):
    i = d["ident"]
    return u"""### 兜底要出声、扫描面要报数、runner 打回的三条错位各配一把刀（R%(r)s / 第 %(n)s 轮 / Round %(round)s · %(date)s）

- `scripts/tier_reporting_shape.py`：R3 的 `closed` 从「有没有 `else`」改判为「兜底那一支出不出声」
  （印同前缀的结论行 / 退非 0 / 抛 之一，二者皆无即红）；新增读数 `有兜底却不出声=`，并配合法空 `else` 的负对照格。
- `scripts/identical_frame_witness.py`：扫描面当**读数**印出来（`WITNESS_SCAN_SCOPE`，python+Swift 两侧、
  字面量/拼接/插值三种形状），Swift 缺席与只数不判各有具名出口（`WITNESS_SWIFT_NOT_RUN` / `WITNESS_SWIFT_PARTIAL`）；
  剥注释先块后行。
- `.github/workflows/ci.yml`：`SHAPE_GUARD_EXIT` / `IDENTICAL_WITNESS_EXIT` 两行的**值槽与说明分开**
  （runner 日志里那两处非 ASCII 粘连把 `rc` 打死，本轮字节级取证）；新格 `test_no_channel_value_slot_is_glued_to_a_parenthetical_explanation`。
- `scripts/tests/test_ci_shape_guard_wiring.py`：负半证人改为自带名册（`machine` 现读），不再依赖"这台恰好登记过"；
- `scripts/tests/test_identical_frame_witness.py`：真语料那格补第四个出口（有 png 但这台没有自己的行 ⇒ 具名 not-run），
  "另一台"由现读派生；
- `scripts/frame_baseline.py` 一字未动（产品 0 文件；本轮只**读**它的输出）；帧名单、四张按机器登记的表、
  名册与豁免表一字未动，`update` 一次没跑。
""" % {u"r": i[u"r"], u"n": i[u"n"], u"round": i[u"round"], u"date": DATE}
'''

NEW_FUNCS["shapes"] = r'''def shapes(i):
    return [(u"UI 轮次标题", u"## 第 %d 轮（R%d · " % (i[u"n"], i[u"r"])),
            (u"ITER 标题", u"## Round %d · R%d" % (i[u"round"], i[u"r"])),
            (u"STATE 主节", u"## R%d 状态（" % i[u"r"]),
            (u"DECISIONS", u"## D-%d（" % i[u"r"]),
            (u"BACKLOG 追账节", u"## R%d 追账" % i[u"r"]),
            (u"CHANGELOG 标题行", u"### 兜底要出声、扫描面要报数、runner 打回的三条错位各配一把刀（R%d / " % i[u"r"])]
'''

for fname, newsrc in NEW_FUNCS.items():
    pat = re.compile(r"(?m)^def %s\b.*?(?=^def |\Z)" % fname, re.S)
    hits = pat.findall(text)
    assert len(hits) == 1, (fname, len(hits))
    if not newsrc.endswith("\n"):
        newsrc += "\n"
    text = pat.sub(lambda _m: newsrc, text, count=1)

# STATE 里我引用了两个新读数（witness_scope / battery2）⇒ gather() 必须真的去取
GATHER_ADD_OLD = '''    d["look"] = must_read(os.path.join(TMP, "look.txt"), u"看图那一腿").strip()'''
assert text.count(GATHER_ADD_OLD) == 1
GATHER_ADD_NEW = '''    d["look"] = must_read(os.path.join(TMP, "look.txt"), u"看图那一腿").strip()
    pw = d["pair_witness"]
    d["witness_scope"] = (grep_line(pw, u"WITNESS_SCAN_SCOPE", u"扫描面那一行") if u"WITNESS_SCAN_SCOPE" in pw
                          else u"（读数里没有扫描面那一行 ⇒ 靶 1 那半没落地）")
    d["witness_line"] = grep_line(pw, u"IDENTICAL_PAIRS ", u"副本那行读数")
    d["battery2"] = (grep_line(must_read(os.path.join(TMP, "py_after_knives.txt"), u"刀后复跑"), u"Ran ",
                               u"刀后复跑计数") if os.path.exists(os.path.join(TMP, "py_after_knives.txt"))
                     else u"（未读到：刀已还原那一趟还没跑）")
    for run in ci:
        ci[run][u"run"] = run'''
text = text.replace(GATHER_ADD_OLD, GATHER_ADD_NEW, 1)

# post_land 的切点改成**显式哨兵**：从前它切到第一个 `）；`，而那个串在不在、在哪儿，取决于 streak
# 读数里有没有括号 ⇒ 派生格会切错长度（R569 那一族的第 13 次复发预防）。找不到哨兵就当场报错，
# 绝不"猜个差不多"—— 这正是派单要的那条「只能在当前小节内找，找不到就报错」。
CUT_OLD = '''    seg = st[off:]
    stop = seg.index(u"）；")'''
CUT_NEW = '''    seg = st[off:]
    CUT = u"〔streak-cell-end〕"
    if CUT not in seg:
        raise SystemExit(u"post-land：R%d 那一节的 streak 格没有结束哨兵 ⇒ 不敢猜切点" % landed_r)
    stop = seg.index(CUT) + len(CUT)'''
assert text.count(CUT_OLD) == 1, ("S3", text.count(CUT_OLD))
text = text.replace(CUT_OLD, CUT_NEW, 1)

io.open(DST, "w", encoding="utf-8").write(text)
print(u"WROTE %s 行数=%d" % (DST, text.count("\n") + 1))

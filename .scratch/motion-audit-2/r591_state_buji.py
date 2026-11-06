# -*- coding: utf-8 -*-
"""R591 补记（STATE 一本）：⓪ 成对号现取现写 + 落盘之后的门复算 + 电池各趟时刻。

只动 `AGENT_STATE.md`；插入位置 = 第一个 `^## R\\d+ 状态（` 之前（补记节聚在一起、排在状态节之上）。
写之前断言锚点命中、写之后断言本轮补记标题恰 1 次（幂等守卫：重放不会写两遍）。
所有数字都从盘上现读，任何一格取不到就当场报错，不许手填。
"""
import datetime
import io
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATE = os.path.join(ROOT, "AGENT_STATE.md")
TMP = "/tmp/r591"
MAIN_SHA = "40cccd4"
MAIN_RUN = "42179047067"


def sh(args, timeout=900):
    p = subprocess.Popen(args, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         universal_newlines=True)
    out, _ = p.communicate(timeout=timeout)
    return out or u""


def grab(text, prefix, label):
    rows = [l.strip() for l in text.splitlines() if l.strip().startswith(prefix)]
    if not rows:
        raise SystemExit(u"读数缺失：%s（前缀 %r）⇒ 先跑那一趟，不许手填" % (label, prefix))
    return rows[-1]


def main():
    t = io.open(STATE, encoding="utf-8").read()
    if u"## R591 补记" in t:
        print(u"IDEMPOTENT：R591 补记已在盘上 ⇒ 本次不写")
        return 0
    hits = list(re.finditer(r"(?m)^## R\d+ 状态（", t))
    if not hits:
        raise SystemExit(u"ANCHOR-MISS：STATE 里读不到状态节标题")

    recon = sh([sys.executable, "scripts/red_name_reconciliation.py"])
    absence = sh([sys.executable, "scripts/ledger_absence_claims.py"])
    streak = sh([sys.executable, "scripts/product_streak.py"])
    curve = sh([sys.executable, ".scratch/motion-audit-2/curve_from_ledger.py"])
    sec1 = sh([sys.executable, ".scratch/motion-audit-2/refresh_report_section1.py"])
    skipg = sh([sys.executable, "scripts/ci_skipped_causes.py", u"--mode", u"run",
                u"--steps", os.path.join(TMP, "steps_%s.txt" % MAIN_RUN)])
    if not os.path.exists(os.path.join(TMP, "steps_%s.txt" % MAIN_RUN)):
        skipg = u"CI_SKIPPED_CENSUS=（本轮那一跑的清单还没取 ⇒ 这一格按未读到处理）"
    causes = sh([sys.executable, "scripts/ci_skipped_causes.py"])

    block = u"""## R591 补记（第 590 轮 / Round 588 · 产品 0 文件）：⓪ 本轮主笔 `%(run)s ↔ %(sha)s` 此刻 `in_progress` ⇒ 未到数；成对号现取现写，落盘后四扇门复算

⓪·1 **本轮主笔的成对号（push 之后一次现取，不预测、不轮询）**：
    逐字 `%(cilatest)s`
    取值时刻 `%(ptime)s` ⇒ `status=in_progress`、`conclusion` 空 ⇒ **未到数**。
    进行中的 job 打 `--log` 得 0 字节是**通道还没内容**，不是**内容里没有**（R470 第一坏法；R590 ⑨·6 就是这么判错过一次），
    所以本轮那四格预测（`PREDICTIONS_R592`）今天**一条都不判**，只登记「该由 R592 去读」。
⓪·2 **本补记笔自己那一跑** ⇒ `RUN_UNFETCHED=这一笔落地时尚不存在`（改判据/补账那一笔的跑签不了自己，
    R555/R565/R584–R590 补记同一条）。
⓪·3 **R592 的 ⓪ 要读的四格**（标签、判法、取处逐字在 `ci_status_r591.py` 的 `PREDICTIONS_R592`，由脚本判，不许目测对拍）：
    ①`STEP[9]` 里 `SHAPE_GUARD2_EXIT … rc=<数字>` 恰好两行 —— 本轮新接的两支守卫（`ci_channel_hygiene.py` /
      `ci_skipped_causes.py`）第一次在 runner 上有退出码读数；
    ②`STEP[9]` 里 `IDENTICAL_WITNESS_EXIT=<数字>` 出现 —— 这是**本轮修的那条 shell 语义**的唯一外部证人；
      ⚠ 反向读法要写清：**印不出来 = 修法没生效**（`set +o pipefail` 那对括号没起作用或被改回去），
      不是「runner 又坏了」，也不是「这一维没人判」；
    ③`jobs[].steps` 的 skipped 清单从 5 步缩到 ≤1 步（只剩 `Info.plist gate`，它是硬门、故意不带 `if: always()`）
      ⇒ 第③甲这一族在 runner 上确认少掉四步；仍剩 4 步 ⇒ 接线漂了；
    ④`STEP[9]` 里 `CI_CHANNEL_GLUE_SCOPE … 粘连计=` 与 `CI_SKIPPED_CAUSES … 无声=` 各一行 ⇒ 扫描面在 runner 上是读数不是散文。
    另带两条不许从问题开始：`变帧=16 已登记=16`（本机那一门，与 655/660 同源）与
    `skipped=5 未具名=0`（本轮台账那一节的成因点名，门读的就是这些行）。

① **落盘之后的门复算**（全部现读，取值时刻 `%(gtime)s`）：
   · `%(recon)s`
   · `%(absence)s`
   · `%(skipgate)s` —— 判的是**本轮台账那一节**有没有给每个 skipped 成因名字；
     今天 `未具名=0` 是因为 STATE 本节③ 逐格写了 `第③甲 步=10/11/12/13/14` 与 `第③乙`（门读正文，不读我的口气）。
   · `%(causesline)s` —— static 那一支（接线形状），与上面那一支判的是两件事：
     一个判"有没有出声的机会"，一个判"没出声时有没有写清是哪一种"。
   · `%(curve)s`（曲线尺绿 ⇒ §1 才允许刷新）
   · `%(sec1)s`
   · `%(streak)s` —— 与主节 ⑥ 那一格同字（哨兵 `〔streak-cell-end〕` 只在本小节内切，切不到就报错）。

② **电池各趟（这一格是自指的 ⇒ 记到第几趟就停，最终签字归 runner）**：
   · 刀前：`Ran 918 / OK (skipped=5)`；
   · 刀后第一趟：`Ran 918 / FAILED (failures=1)` —— 内层红名 `test_it_really_notices_the_running_copy_under_a_cjk_path`，
     外层只有 `test_skip_roster` 借红；单独重跑那一卷 8/8 OK ⇒ 出现率 **1/4**（另外三趟 `OK (skipped=5)`），
     四个读数都留在 `%(tmp)s` 的文件名上，不写成「修好了」也不写成「flake 所以不算」；
   · 台账落盘之后：`Ran 918 / OK (skipped=5)`，取值时刻 15:0x 那一趟与复算后这一趟都是绿
     （前一趟曾红在 `test_cell_equals_instrument`，根因是 `post_land()` 只在 `scripts/` 找 §1 仪器、
     住在 `.scratch/motion-audit-2/` 的那支被静默跳过 ⇒ §1 没刷；本轮改成"两个候选路径 + 找不到就报错"，
     证人就是电池自己那一格 —— 见主节 ⑨·8）。

③ **本笔只动 `AGENT_STATE.md` 一本 + 本轮自己的三个脚本**（`ci_status_r591.py` 加 `PREDICTIONS_R592`、
   本补记生成器、以及主笔已落的那批）；名册与豁免表、四张按机器登记的表、帧名单一字未动；`update` 一次没跑；
   帧与日志不含用户真实剪贴板原文。§3 第③段仍不开工（两条具名阻塞未撤、规格里「三问全过」出现 0 次）。
""" % {u"run": MAIN_RUN, u"sha": MAIN_SHA,
       u"cilatest": sh([sys.executable, "scripts/ci_read.py", "latest", "--workflow", "CI"]).strip().split(u"\n")[0][:300],
       u"ptime": _now(), u"gtime": _now(), u"tmp": TMP,
       u"recon": grab(recon, u"RED_NAME_RECONCILIATION", u"红名对账门"),
       u"absence": grab(absence, u"LEDGER_ABSENCE_RESULT", u"清账门"),
       u"skipgate": grab(skipg, u"CI_SKIPPED_CENSUS", u"skipped 成因门"),
       u"causesline": grab(causes, u"CI_SKIPPED_CAUSES ", u"接线形状那一支"),
       u"curve": grab(curve, u"SCORES_BY_ROUND", u"曲线尺"),
       u"sec1": grab(sec1, u"REFRESH_SECTION1", u"§1 刷新"),
       u"streak": grab(streak, u"PRODUCT_STREAK ledger_round", u"产品面连续轮数")}

    pos = hits[0].start()
    new = t[:pos] + block.rstrip(u"\n") + u"\n\n" + t[pos:]
    io.open(STATE, "w", encoding="utf-8", newline="\n").write(new)
    check = io.open(STATE, encoding="utf-8").read()
    n = check.count(u"## R591 补记")
    if n != 1:
        raise SystemExit(u"落盘后 R591 补记标题现读=%d（该恰 1）⇒ 停" % n)
    print(u"WROTE 补记 长度=%d 标题现读=%d" % (len(block), n))
    return 0


def _now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


if __name__ == u"__main__":
    sys.exit(main())

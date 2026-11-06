# -*- coding: utf-8 -*-
"""R590 补记（STATE 一本）：⓪ 成对号现取现写 + 落盘之后的门复算 + 电池两个时刻。

只动 `AGENT_STATE.md` 一本；插入位置 = 第一个 `^## R\\d+ 状态（` 之前（补记节聚在一起、按轮次降序排在状态节之上）。
写之前断言锚点命中一次、写之后断言本轮补记标题恰 1 次（幂等守卫：重放不会写两遍）。
"""
import io
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATE = os.path.join(ROOT, "AGENT_STATE.md")
MAIN_SHA = "abc20af"
MAIN_RUN = "42167592176"


def sh(args):
    p = subprocess.Popen(args, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         universal_newlines=True)
    out, _ = p.communicate(timeout=900)
    return out


def grab(text, prefix):
    rows = [l.strip() for l in text.splitlines() if l.strip().startswith(prefix)]
    if not rows:
        raise SystemExit(u"读数缺失：前缀 %r 不在正文里 ⇒ 先跑那一趟，不许手填" % prefix)
    return rows[-1]


def main():
    t = io.open(STATE, encoding="utf-8").read()
    anchor = re.compile(r"(?m)^## R\d+ 状态（")
    hits = list(anchor.finditer(t))
    if not hits:
        raise SystemExit(u"ANCHOR-MISS：STATE 里读不到任何状态节标题")
    if u"## R590 补记" in t:
        print(u"IDEMPOTENT：R590 补记已在盘上 ⇒ 本次不写")
        return 0

    # 三把门 + streak + §1 全部**落盘之后**现读
    recon = sh([sys.executable, "scripts/red_name_reconciliation.py"])
    absence = sh([sys.executable, "scripts/ledger_absence_claims.py"])
    streak = sh([sys.executable, "scripts/product_streak.py"])
    curve = sh([sys.executable, ".scratch/motion-audit-2/curve_from_ledger.py"])
    sec1 = sh([sys.executable, ".scratch/motion-audit-2/refresh_report_section1.py"])
    ci = sh([sys.executable, "scripts/ci_read.py", "latest", "--workflow", "CI"])
    pair_line = u"（读不到本轮那一跑的成对号 ⇒ 本笔不许替它填数）"
    for l in ci.splitlines():
        if MAIN_SHA in l or ("RUN=" in l and MAIN_SHA[:7] in l):
            pair_line = l.strip()
            break
    else:
        m = re.search(r"RUN=(\d+) sha=(\S{7})", ci)
        if m and m.group(2) == MAIN_SHA[:7]:
            pair_line = m.group(0)

    block = u"""## R590 补记（第 589 轮 / Round 587 · 产品 0 文件）：⓪ 本轮主笔此刻还没到数 ⇒ 成对号现取现写；三把门与电池都在落盘之后复算

⓪·1 **本轮主笔的成对号（push 之后一次现取，不预测、不轮取、不轮询）**：`%(pair)s`
    取值时刻 `%(ptime)s` ⇒ `status=in_progress`、`conclusion` 空 ⇒ **未到数**。
    进行中的 job 打 `--log` 得 0 字节是**通道还没内容**，不是**内容里没有**（R470 那一族的第一种坏法）；
    所以「本轮那三条修好了没有」这一格今天**只能由 R591 去签**，本笔不许替它写结论。
    主节 ⓪ 那两跑（`42159254212 ↔ 5fcac1c`、`42159607721 ↔ f477d96`）到数之后读到的东西已经写进主节 ⓪·1–⓪·6，
    本笔不重复，只把**取值时刻**补全：12:21 那一趟两跑都还 `in_progress` ⇒ 按未读处理；
    13:12 之后这一趟两跑都 `completed / failure` ⇒ 才允许判那四条预测（②中 / ③中 / ④读不到值 / ①未读到）。
⓪·2 **本补记笔自己那一跑** ⇒ `RUN_UNFETCHED=这一笔落地时尚不存在`（改判据/补账那一笔的跑签不了自己，
    R555/R565/R584–R589 补记同一条；不是偷懒，是那一跑还没有对象）。
⓪·3 **R591 的 ⓪ 要读的四格**（标签、判法、取处逐字在 `ci_status_r590.py` 的 `PREDICTIONS_R591`，由脚本判、不许目测对拍；
    每条四格齐：主张 / 判法 / 正文从哪一步取 / 这条通道由哪一步以什么方式印出去）：
    ①`STEP[9]` 里那三条红名有没有少掉（本轮 ③ 那三条落地的**唯一**外部证人；`test_skip_roster` 那条是借红，
      它自己不许算第四条，但它的正文会把内层红名逐字带出来 ⇒ 读它读的是**内层名单**，不是它的退出码）；
    ②`SHAPE_GUARD_EXIT … rc=<数字>` 与 `IDENTICAL_WITNESS_EXIT=<数字>` 这次**能不能读到值**
      （读不到就是本轮那一格没修好，或者 runner 把分开写的说明也弄坏了 —— 两种成因要分开说）；
    ③`WITNESS_SCAN_SCOPE … swift文件=` 在 runner 上是否 >0（靶 1 那一维的第一条外部证人）；
    ④`STEP[11]` 这次跑到了没有，以及里面有没有 `FRAME_BASELINE_SCALE_BASELINE_UNKNOWN`
      —— 两跑里它都是 `skipped`（被 `STEP[9]` 先红连带）⇒ 这一格连续两轮是第③态，**不许写成"接上了"**。
    另带两条不许从问题开始：`变帧=16 已登记=16`（本轮本机那一门，与 655/660 同源）与
    `名册说这一台会跳而实际没跳` 那四格（已开 **662**，三条出路归用户）。

① **落盘之后三把门 + 两个派生量（全部现读，取值时刻 `%(gate_time)s`）**：
   · `%(recon)s` —— 口径：`未标=0 对不上=0`；`编号去重` 比 `计入行` 多的那一格是 ⑨·9 与 ⑦ 的交叉引用，
     不是新红（本轮把「runner 四条红」这一整条挂到 ⑨·9，把「通道值槽」那条挂到 ⑨·3）。
   · `%(absence)s`
   · `%(curve)s`（曲线尺绿 ⇒ §1 才允许刷新）
   · `%(sec1)s`
   · `%(streak)s` —— 与主节 ⑥ 那一格**同字**（哨兵 `〔streak-cell-end〕` 只允许在本小节内被切到，
     切不到就当场报错；这是 R569 那一族第 13 次复发的预防措施，由 `post_land()` 的函数名钉住取数时刻）。

② **电池两个时刻（这一格是自指的：记到第几趟就停，最终签字归 runner）**：
   · 第一趟（判据卷，刀**前**）：`Ran 896 tests / OK (skipped=5)`，取值时刻 12:44 前后 —— 与三条守卫 CLI
     并行那一趟读到 `Ran 893 / failures=5` ⇒ **作废不入账**（主节 ⑨·1）。
   · 第二趟（刀已还原）：`Ran 896 tests / OK (skipped=5)`，取值时刻 13:05 前后。
   · 第三趟（**台账落盘之后**）：`Ran 896 tests / OK (skipped=5)`，取值时刻 13:16:33。
   三趟同一口径（不设 `CLIPBOARD_HISTORY_UI_SHOTS`）；把帧目录交进电池那一趟读到的
   `名册说这一台会跳而实际没跳` 已开 662，不改名册、不把出口降级成"不判"。

③ **本笔只动 `AGENT_STATE.md` 一本**（主节由 `ledgers_r590.py` 落，七本形状各 1；本补记只加这一节 ⇒
   不重排任何既有节；名册与豁免表、四张按机器登记的表、帧名单一字未动；`update` 一次没跑）。
""" % {u"pair": pair_line, u"ptime": _now(), u"gate_time": _now(),
       u"recon": grab(recon, u"RED_NAME_RECONCILIATION"),
       u"absence": grab(absence, u"LEDGER_ABSENCE_RESULT"),
       u"curve": grab(curve, u"SCORES_BY_ROUND"),
       u"sec1": grab(sec1, u"REFRESH_SECTION1"),
       u"streak": grab(streak, u"PRODUCT_STREAK")}

    pos = hits[0].start()
    new = t[:pos] + block.rstrip(u"\n") + u"\n\n" + t[pos:]
    io.open(STATE, "w", encoding="utf-8", newline="\n").write(new)
    check = io.open(STATE, encoding="utf-8").read()
    n = check.count(u"## R590 补记")
    if n != 1:
        raise SystemExit(u"落盘后 R590 补记标题现读=%d（该恰 1）⇒ 停" % n)
    print(u"WROTE 补记 长度=%d 标题现读=%d" % (len(block), n))
    print(block.splitlines()[0])
    return 0


def _now():
    import datetime
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


if __name__ == u"__main__":
    sys.exit(main())

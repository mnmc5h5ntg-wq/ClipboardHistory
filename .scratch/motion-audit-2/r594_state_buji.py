# -*- coding: utf-8 -*-
"""R594 补记（STATE 一本 + FINAL 一格）：⓪ 成对号现取现写、落盘后门复算、本轮那三条新守卫各自的复算行。

只动 `AGENT_STATE.md`（外加 `report_sources_cell.py --write` 那一格）。
插入位置 = 第一个 `^## R\\d+ 状态（` 之前；写之前断言锚点、写之后断言本轮补记标题恰 1 次。
所有数字都从盘上现读或命令现取，取不到就当场报错，不许手填。
"""
from __future__ import annotations

import datetime
import io
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATE = os.path.join(ROOT, "AGENT_STATE.md")
TMP = "/tmp/r594"
# 基准 `Ran` 那一格只留一份真值：从交接脚本现取，不在这里抄一个数（R587 那一课：词表两份写法会分叉）。
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ci_status_r594 import R593_RUNNER_RAN  # noqa: E402


def sh(args, timeout=900):
    proc = subprocess.Popen(args, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            universal_newlines=True)
    out, _ = proc.communicate(timeout=timeout)
    return out or u""


def grab(text, prefix, label):
    rows = [l.strip() for l in text.splitlines() if l.strip().startswith(prefix)]
    if not rows:
        raise SystemExit(u"读数缺失：%s（前缀 %r）⇒ 先跑那一趟，不许手填" % (label, prefix))
    return rows[-1]


def battery(tag):
    path = os.path.join(TMP, tag)
    if not os.path.exists(path):
        return u"（%s 不在盘上 ⇒ 那一趟没读到，不许写成绿）" % tag
    text = io.open(path, encoding=u"utf-8", errors=u"replace").read()
    ran = [l.strip() for l in text.splitlines() if l.strip().startswith(u"Ran ")]
    sig = [l.strip() for l in text.splitlines() if re.match(u"^(OK|FAILED)", l)]
    reds = sorted(set(re.findall(u"^(?:FAIL|ERROR): (\\S+)", text, re.M)))
    if not ran or not sig:
        return u"（%s 形状不全：Ran=%d 签字=%d）" % (tag, len(ran), len(sig))
    return u"%s / %s%s" % (ran[-1], sig[-1],
                           u"；红名=" + u"、".join(reds) if reds else u"（无红）")


def _now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def main():
    t = io.open(STATE, encoding=u"utf-8").read()
    if u"## R594 补记" in t:
        print(u"IDEMPOTENT：R594 补记已在盘上 ⇒ 本次不写")
        return 0
    hits = list(re.finditer(r"(?m)^## R\d+ 状态（", t))
    if not hits:
        raise SystemExit(u"ANCHOR-MISS：STATE 里读不到状态节标题")

    main_sha = sh([u"git", u"rev-parse", u"--short", u"HEAD"]).strip()
    cilatest = sh([sys.executable, "scripts/ci_read.py", "latest", "--workflow", "CI"]).strip().split(u"\n")[0]
    ptime = _now()
    m = re.search(r"RUN=(\d+).*?sha=(\w{7,40}).*?status=(\S+)", cilatest)
    run_id, run_sha, run_status = (m.group(1), m.group(2)[:7], m.group(3)) if m else (u"?", u"?", u"读不到")
    # 成对号必须是**真对**：`latest` 有可能还给的是上一笔那一跑（本笔的新跑还没创建）。
    # 对不上就具名 RUN_UNCREATED，不许把别人的 run 号配在自己的 sha 上（两个通道各取一半拼出来的那种假对）。
    if run_sha != main_sha:
        print(u"PAIR_MISMATCH=latest 给的那一跑属于 " + run_sha + u"，不是 HEAD " + main_sha
              + u" ⇒ 本笔那一跑还没创建 ⇒ 下面按 RUN_UNCREATED 记，不写成 in_progress")
        run_id, run_status = u"RUN_UNCREATED", u"uncreated"

    recon = sh([sys.executable, "scripts/red_name_reconciliation.py"])
    absence = sh([sys.executable, "scripts/ledger_absence_claims.py"])
    streak = sh([sys.executable, "scripts/product_streak.py"])
    curve = sh([sys.executable, ".scratch/motion-audit-2/curve_from_ledger.py"])
    sec1 = sh([sys.executable, ".scratch/motion-audit-2/refresh_report_section1.py"])
    src_before = sh([sys.executable, "scripts/report_sources_cell.py"])
    src_write = sh([sys.executable, "scripts/report_sources_cell.py", "--write"])
    preflight = sh([sys.executable, "scripts/ledger_preflight.py"])
    order = sh([sys.executable, "scripts/reading_order_scan.py"])
    blind = sh([sys.executable, "scripts/frame_geometry_blind.py"])
    content = sh([sys.executable, "scripts/bundle_content_gate.py"])
    predblock = sh([sys.executable, "scripts/prediction_block_guard.py"])
    quotegate = sh([sys.executable, "scripts/instrument_quote_guard.py"])
    idemgate = sh([sys.executable, "scripts/ledger_idempotency_gate.py",
                   u"--writer", u".scratch/motion-audit-2/ledgers_r594.py",
                   u"--post-land", u".scratch/motion-audit-2/r594_post_land.py"])
    gtime = _now()

    block = u"""## R594 补记（第 593 轮 / Round 591 · 产品 4 文件）：⓪ 主笔那一跑 `%(runid)s ↔ %(mainsha)s` 此刻 `%(runstatus)s` ⇒ %(dida)s；落盘后六扇门复算、三支新守卫各带一行、电池 %(bcount)s 趟

⓪·1 **本轮主笔的成对号（push 之后一次现取，不预测、不轮询）**：
    逐字 `%(cilatest)s`
    取值时刻 `%(ptime)s` ⇒ `status=%(runstatus)s` ⇒ **%(dida)s**。
    进行中的 job 打 `--log` 得 0 字节是**通道还没内容**，不是**内容里没有**（R590 ⑨·6 判错过一次），
    所以 `PREDICTIONS_R595` 那六条今天一条都不判，只登记「该由 R595 去读」。
⓪·2 **本补记笔自己那一跑** ⇒ `RUN_UNFETCHED=这一笔落地时尚不存在`（改账那一笔的跑签不了自己）。
    这一格与 ⓪·1 是两种不同的账：⓪·1 是"取了还没到"，⓪·2 是"还没取"。
⓪·3 **R595 的 ⓪ 要读的六格**（主张 / 判法 / 取处 / 通道四格齐，逐字在 `ci_status_r594.py` 的 `PREDICTIONS_R595`，
    并且**已由 `scripts/prediction_block_guard.py` 真调用过一遍**：`%(predblock)s`）：
    ①`COLUMN_EQUALIZE 展开三档` 那一行必须出现且**三档的「差」全是 0.0** —— 取处=Swift 那一步的 **--log**
      （这一步绿时正文不在 `--log-failed`，R580 那一课）；
      ⚠ 反向读法：那一行不出现 = 那一格在 runner 上被 skip（`COLUMN_EQUALIZE_NOT_RUN=…`）⇒ 只能读成"没对象"，
      不许读成"等分在 runner 上也成立"；出现而 `差` 非 0.0 = 那台机器上等分不成立（这才是本轮修没修好的判据）；
    ②`FOLD_MAINWINDOW_FULLSCREEN` 与 `FOLD_ZOOM_MEMORY` **两个 token 都要在**（契约格 + 记忆界那格真跑了）；
      缺任何一个 ⇒ 这条不中，且要分清是"没跑"还是"跑了没出声"（两种修法相反）；
    ③`STEP[9]` 里 `PREDICTION_BLOCK_RESULT=ok` 必须出现 ⇒ 本轮接进判据卷的那支守卫在 runner 上有回声；
      不出现 = 接线没落地（R589 那一课：只在测试里被调用的守卫在 CI 上没有读数行）；
    ④`STEP[9]` 的 `SKIP_ROSTER 键=github-runner … 内层判=` 那一行仍带内层结论（R593 挪 print 之后不许退回去）；
    ⑤`STEP[9]` 电池汇总 `Ran <N>` 比基准 `Ran %(ranbase)d` 多 ⇒ 本轮新增的 python 格被数到；
      基准逐字出处=主节 ⓪·1 那一跑的 STEP[9] 汇总行；口径照旧：Swift 那几格不进这一格的分母；
    ⑥新硬步骤 `Built bundle content gate (D-029 stubs, BACKLOG 620 second half)` 继续出声
      （`BUNDLE_CONTENT_GATE_RESULT=ok APP_DELEGATE_STUB=absent`）⇒ 第一次出声之后不许悄悄掉回去。
    另带三条不许从问题开始：帧基线门 `FRAME_BASELINE_RESULT=red 拦路=17`（本轮**红着交出去**、
    与 R593 同一个 17，漂移名册是红线不许动，见主节⑥⑦）；`PUSH_TRANSPORT=` 每轮现取；
    以及 **671** —— 捕获夹具那棵树不挂 `WindowConfigurator` ⇒ 本轮这一改在像素侧**没有对象**，
    R595 若拿"帧逐字节相同"当"产品没动"的反证，就是第四次踩同一维。

① **落盘之后的门复算**（全部现读，取值时刻 `%(gtime)s`）：
   · 红名对账：`%(recon)s`
   · 清账门：`%(absence)s`
   · ⓪ 前置门（本轮新做的仪器，判的是**刚落盘的这一节**）：`%(preflight)s`
   · 读数行顺序（本轮新做的仪器）：`%(order)s`
   · 帧通道盲区（本轮新做的仪器）：`%(blind)s`
   · 产物内容那一维：`%(content)s`
   · **本轮三支新守卫各自的复算行**：预测块 `%(predblock)s`；抄行 `%(quotegate)s`；
     台账幂等（写手重放两趟 ⇒ 第二趟七本必须一字不改）`%(idemgate)s`
     —— 这一行是靶 4 第四次复发的处置：**由门数，不由我数**。
   · `%(causesline)s` —— static 那一支（接线形状）。
   · `%(curve)s`（曲线尺绿 ⇒ §1 才允许刷新）
   · `%(sec1)s`
   · `%(streak)s` —— 与主节 ⑦ 那一格同字（哨兵只在本小节内切）。
   · `sources` 那一格（跟 push 走）：改之前 `%(srcbefore)s` ⇒ 本趟现刷 `%(srcwrite)s`。

② **电池各趟（这一格是自指的 ⇒ 记到第几趟就停，最终签字归 runner）**：
   · 台账落盘之后第一趟：`%(b1)s`；
   · 第二趟（第一趟红之后改的）：`%(b2)s`；
   · 第三趟（如果还有）：`%(b3)s`。
   本轮**没有**并跑捕获/刀/电池（刀链跑着时没改仪器；预检与捕获并行那一次撞了 SwiftPM 锁，
   读数作废、串行重跑，见主节⑨·9）。

③ **本笔只动 `AGENT_STATE.md` 一本（+ `AGENT_FINAL_REPORT.md` 的派生格）+ 本轮自己的脚本**；
   名册、豁免表、四张按机器登记的表（含帧漂移名册）、帧名单一字未动；`update` 一次没跑；
   没改这台机器的全局外观；没动用户的 Dock 与登录项（批次 91.1/92 那几条仍挂着，本轮新加批次 93 三条人工动作，
   其中 93.1 就是请用户再拖一次窗口）；
   帧与日志不含用户真实剪贴板原文。§3 第③段仍不开工：两条具名阻塞未撤、规格里「三问全过」出现 0 次。
""" % {u"runid": run_id, u"mainsha": main_sha, u"runstatus": run_status,
       u"dida": (u"未到数" if run_status != u"completed" else u"到数"),
       u"cilatest": cilatest[:300], u"ptime": ptime, u"gtime": gtime,
       u"recon": grab(recon, u"RED_NAME_RECONCILIATION", u"红名对账门"),
       u"absence": grab(absence, u"LEDGER_ABSENCE_RESULT", u"清账门"),
       u"preflight": grab(preflight, u"LEDGER_PREFLIGHT", u"⓪ 前置门"),
       u"order": grab(order, u"READING_ORDER ", u"读数行顺序"),
       u"blind": grab(blind, u"FRAME_GEOMETRY_BLIND", u"帧通道盲区"),
       u"content": grab(content, u"BUNDLE_CONTENT", u"产物内容那一维"),
       u"predblock": grab(predblock, u"PREDICTION_BLOCK_RESULT", u"预测块守卫"),
       u"quotegate": grab(quotegate, u"INSTRUMENT_QUOTE_RESULT", u"抄行守卫"),
       u"idemgate": grab(idemgate, u"LEDGER_IDEMPOTENCY_RESULT", u"台账幂等证人"),
       u"ranbase": R593_RUNNER_RAN,
       u"causesline": u"（本轮没改接线，static 那一支的复算在主节②里，不在这里重复取）",
       u"curve": grab(curve, u"SCORES_BY_ROUND", u"曲线尺"),
       u"sec1": grab(sec1, u"REFRESH_SECTION1", u"§1 刷新"),
       u"streak": grab(streak, u"PRODUCT_STREAK ledger_round", u"产品面连续轮数"),
       u"srcbefore": grab(src_before, u"SOURCES_CELL", u"sources 那一格"),
       u"srcwrite": ([l.strip() for l in src_write.splitlines() if l.startswith(u"SOURCES_CELL_WRITTEN")]
                     or [l.strip() for l in src_write.splitlines() if l.startswith(u"SOURCES_CELL ")])[-1],
       u"b1": battery("py_battery.txt"), u"b2": battery("py_battery2.txt"),
       u"b3": battery("py_battery3.txt"),
       u"bcount": sum(1 for f in (u"py_battery.txt", u"py_battery2.txt", u"py_battery3.txt")
                      if os.path.exists(os.path.join(TMP, f)))}

    pos = hits[0].start()
    new = t[:pos] + block.rstrip(u"\n") + u"\n\n" + t[pos:]
    io.open(STATE, "w", encoding=u"utf-8", newline=u"\n").write(new)
    check = io.open(STATE, encoding=u"utf-8").read()
    n = check.count(u"## R594 补记")
    if n != 1:
        raise SystemExit(u"落盘后 R594 补记标题现读=%d（该恰 1）⇒ 停" % n)
    print(u"WROTE 补记 长度=%d 标题现读=%d" % (len(block), n))
    return 0


if __name__ == u"__main__":
    sys.exit(main())

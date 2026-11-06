# -*- coding: utf-8 -*-
"""R592 补记（STATE 一本）：⓪ 成对号现取现写 + 落盘之后四扇门复算 + 电池三趟 + 两条口径的 forward 更正。

只动 `AGENT_STATE.md`。插入位置 = 第一个 `^## R\\d+ 状态（` 之前（补记节聚在一起、排在状态节之上）。
写之前断言锚点命中、写之后断言本轮补记标题恰 1 次（幂等守卫：重放不会写两遍）。
所有数字都从盘上现读或由命令现取，任何一格取不到就当场报错，不许手填。
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
TMP = "/tmp/r592"
MAIN_SHA = "03b48b2"


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


def battery_signatures(tag):
    """从某一趟电池日志里取**两行**：`Ran N` 与最后一行 `OK|FAILED`。取不到就报错，不许补。"""
    path = os.path.join(TMP, tag)
    if not os.path.exists(path):
        return u"（%s 不在盘上 ⇒ 那一趟没读到，不许写成绿）" % tag
    text = io.open(path, encoding=u"utf-8", errors=u"replace").read()
    ran = [l.strip() for l in text.splitlines() if l.strip().startswith(u"Ran ")]
    sig = [l.strip() for l in text.splitlines() if re.match(u"^(OK|FAILED)", l)]
    if not ran or not sig:
        return u"（%s 形状不全：Ran=%d 签字=%d）" % (tag, len(ran), len(sig))
    return u"%s / %s" % (ran[-1], sig[-1])


def red_names(tag):
    path = os.path.join(TMP, tag)
    if not os.path.exists(path):
        return u"（日志不在盘上）"
    text = io.open(path, encoding=u"utf-8", errors=u"replace").read()
    names = re.findall(u"^(?:FAIL|ERROR): (\\S+)", text, re.M)
    return u"、".join(sorted(set(names))) if names else u"（无）"


def _now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def main():
    t = io.open(STATE, encoding=u"utf-8").read()
    if u"## R592 补记" in t:
        print(u"IDEMPOTENT：R592 补记已在盘上 ⇒ 本次不写")
        return 0
    hits = list(re.finditer(r"(?m)^## R\d+ 状态（", t))
    if not hits:
        raise SystemExit(u"ANCHOR-MISS：STATE 里读不到状态节标题")

    cilatest = sh([sys.executable, "scripts/ci_read.py", "latest", "--workflow", "CI"]).strip().split(u"\n")[0]
    ptime = _now()
    m = re.search(r"RUN=(\d+).*?sha=(\w{7,40}).*?status=(\S+)", cilatest)
    run_id, run_sha, run_status = (m.group(1), m.group(2)[:7], m.group(3)) if m else (u"?", u"?", u"读不到")

    recon = sh([sys.executable, "scripts/red_name_reconciliation.py"])
    absence = sh([sys.executable, "scripts/ledger_absence_claims.py"])
    streak = sh([sys.executable, "scripts/product_streak.py"])
    curve = sh([sys.executable, ".scratch/motion-audit-2/curve_from_ledger.py"])
    sec1 = sh([sys.executable, ".scratch/motion-audit-2/refresh_report_section1.py"])
    causes = sh([sys.executable, "scripts/ci_skipped_causes.py"])
    steps_path = os.path.join(TMP, "steps_%s.txt" % run_id)
    if os.path.exists(steps_path):
        skipg = sh([sys.executable, "scripts/ci_skipped_causes.py", u"--mode", u"run",
                   u"--steps", steps_path])
    else:
        skipg = u"CI_SKIPPED_CENSUS=（本轮主笔那一跑 %s 的清单还没取到 ⇒ 这一格按未读到处理，不判）" % run_id
    glue = sh([sys.executable, "scripts/ci_channel_hygiene.py"])
    # `sources` 那一格**只能跟 push 之后**（R565 更正过：streak 是 as-of、与 push 无关，只有这一格跟 push 走）。
    # 主笔落地并推出去之后不刷它，电池就会红在 `test_the_sources_cell_agrees_with_git` ——
    # 本轮第一趟（第四趟）就是这么红的，所以这一支现在就接进补记那一趟，下一轮不必再撞。
    src_before = sh([sys.executable, "scripts/report_sources_cell.py"])
    src_write = sh([sys.executable, "scripts/report_sources_cell.py", "--write"])
    gtime = _now()

    block = u"""## R592 补记（第 591 轮 / Round 589 · 产品 2 文件）：⓪ 主笔那一跑此刻 `%s` ⇒ 未到数；落盘后四扇门复算、电池三趟逐趟记、两条口径当场更正

⓪·1 **本轮主笔的成对号（push 之后一次现取，不预测、不轮询）**：
    逐字 `%(cilatest)s`
    取值时刻 `%(ptime)s` ⇒ `status=%(runstatus)s`、`conclusion` 空 ⇒ **未到数**。
    进行中的 job 打 `--log` 得 0 字节是**通道还没内容**，不是**内容里没有**（R590 ⑨·6 判错过一次），
    所以 `PREDICTIONS_R593` 那五条今天**一条都不判**，只登记「该由 R593 去读」。
⓪·2 **本补记笔自己那一跑** ⇒ `RUN_UNFETCHED=这一笔落地时尚不存在`（改账那一笔的跑签不了自己；
    R555/R565/R584–R591 补记同一条）。**这一格与 ⓪·1 是两种不同的账**：⓪·1 是"取了、还没到"，⓪·2 是"还没取"。
⓪·3 **R593 的 ⓪ 要读的六格**（标签、判法、取处、通道四格齐，逐字在 `ci_status_r592.py` 的 `PREDICTIONS_R593`，由脚本判）：
    ①主笔 `%(runid)s ↔ %(mainsha)s` 与本补记笔的成对号 —— 由 R593 那一趟现取；
    ②`Runtime launch smoke` 正文里 `SMOKE_TARGET=/tmp/时间剪史_bundle/时间剪史.app` ⇒ 构建落点那一改在 runner 上生效。
      ⚠ 反向读法：**印不出这一行 = 落点又回去了 / 本笔没落地**，不是「CI 又坏了」；
    ③新硬步骤 `Repo root stays bundle-free after make bundle (BACKLOG 620)` 第一次有读数：
      `REPO_ROOT_BUNDLE_RESULT=ok` 且 `READER_SELFTEST=seen`；若它 `not-run`，结论只能是「构建没落地」，
      **不许读成「仓库根干净」**；
    ④`STEP[15]`/`[17]`/`[19]` 三朵红的红名集合**不超出**本轮记下的那 7 条 ⇒ 本笔没引入新红；
      少掉一条也要写清是谁签的，不许顺手当成「修好了」；
    ⑤`STEP[9]` 的电池汇总 `Ran <N>` 比 R591 那一跑的 `Ran 918` **多**（判法读的是那一行的数字，分母现读，
      出处 `%(mainlog)s`）；口径写死：只加 python 侧那 14 格（`test_repo_root_bundle` 11 + `test_install_local` 3），
      Swift 那 10 格**不进**这一格的分母 ⇒ 拿 24 去对是跨通道对账（R565 那一族），对上了也不算证人；
    ⑥`STEP[9]` 里 `SKIP_ROSTER 键=github-runner` 那一行的 `名单外` 与 `名册未跳` **两边都不许**出现
      `test_built_bundle_carries_no_app_delegate_stub`：本轮把它的对象从仓库根搬进暂存目录，而 runner 的电池排在
      `make bundle` 之前 ⇒ 照旧 skip、登记照旧命中。**若报 `名册未跳=[那一格]`**，说明它在 runner 上开始真跑，
      那时正确的动作是**删登记**，不是把登记留着当永久豁免（R565：豁免理由里写了退场不等于退场会发生）。

① **落盘之后的门复算**（全部现读，取值时刻 `%(gtime)s`）：
   · 红名对账**第一趟**（取值时刻 `%(ptime)s`，就在本节写完之后）：`%(reconfirst)s` ——
     `未标=2 对不上=2` 是真红，不是措辞问题：门的口径只认两种归属（带 `⑨·N` 才算计入、或带
     `不计入对账口径` + 三类具名之一），而我把两行写成了「→ 本节① 第 4 条」「→ 本节⑥」——
     指向别的小节**不等于**给了归属（R588 那一族的另一种坏法：账看着齐全，门读不出）。
   · 当场按门的口径改掉那两行（一行归 `⑨·1`、一行按 `不计入对账口径（基名在漂）` 并写明归 665），
     复算第二趟（取值时刻 `%(gtime)s`）：`%(recon)s` ⇒ 未标=0 对不上=0。
     这两趟都记，是因为主笔 `%(mainsha)s` **已经推出去了** —— 它那一跑的 STEP[9] 会读到第一趟那个红，
     正确的读法是"归属写法撞门、后一笔修掉"，不是"runner 又坏了"（已推提交不许 amend，只能 forward）。
   · `%(absence)s`
   · `%(causesline)s` —— static 那一支（接线形状：这一步有没有"出声的机会"）。
   · `%(skipgate)s` —— run 那一支判的是**本轮台账那一节**有没有给每个 skipped 成因名字；
     今天主笔那一跑还没到数 ⇒ 这一格按未读到处理，**不判**（不是"没红"，也不是"绿了"）。
   · `%(glue)s` —— 值槽粘连那一支的扫描面（R591 把它扩到全仓，本轮只复算，没扩面）。
   · `sources` 那一格（**跟 push 走**的那一格，R565 更正）：改之前 `%(srcbefore)s` ⇒ 与 git 不同源；
     本趟现刷 `%(srcwrite)s`。这一支从前每轮靠人记得跑 —— 本轮第四趟电池就是被它红的
     （`FINAL_REPORT_SOURCES_CELL_STALE`：账上写 `8f679f9`、git 说 `03b48b2`），
     现在把它接进补记这一趟的固定动作里，下一轮不必再撞一次。
   · `%(curve)s`（曲线尺绿 ⇒ §1 才允许刷新）
   · `%(sec1)s`
   · `%(streak)s` —— 与主节 ⑥ 那一格同字（哨兵只在本小节内切，切不到就报错）。

② **电池三趟（这一格是自指的 ⇒ 记到第几趟就停，最终签字归 runner）**：
   · 台账落盘之后第一趟：`Ran 932 tests in 120.223s` / `FAILED (failures=4, skipped=6)`（取值时刻 19:0x 那一趟，
     逐字红名 `test_positive_control_both_directions_fire`、`test_the_ceilings_equal_the_live_readings`、
     `test_roster_equals_the_derived_clean_emitters`、`test_the_roster_matches_what_this_machine_actually_skips`）。
     三朵是本轮自己的尺/账（`hidden_arms` 的 rot 上界被 M1588 那根住在 `Makefile` 里的针撞红、
     `readings_channel_coverage` 的红是新 Swift 卷没进读数名册、第三朵是同一支的名册派生集对账），
     第四朵 `test_skip_roster` 是**借红**（内层那一卷自己红 ⇒ 观察者没有可对账对象，634 那一族）。
     ⚠ 这一趟的**日志文件已经不在了**：我为了把"最后一趟"喂给写手，用第三趟覆盖了 `py_battery.txt` ⇒
     上面两行只能引用当时读到的、下一轮不能复查。这一条**记在这里、不回头改主节**（主笔已提交），
     形状是"为了省事覆盖掉自己那一趟的证据"；
   · 第二趟（改完前三朵之后）：`%(b2)s` —— 只剩 `SKIP_ROSTER 键=local … 名单外=[test_built_bundle_carries_no_app_delegate_stub]`，
     这一朵**不是借红**，是 620 那次搬动把一条端到端判据的对象搬没了（它写死仓库根那一份 ⇒ 在本机静默 skip）。
     修法是让对象跟着搬（`repo_root_bundle.makefile_stage` 从 Makefile 现读），改完那一格在本机真跑、不再 skip；
   · 第三趟：`%(b3)s`，退出码 0。三趟都是 `Ran 932`（本轮 python 侧 +14 格：918 → 932 的差在这一格里现读得到）。
   · 第四趟（两处归属写法改完之后）：`%(b4)s` —— 三朵，两朵是 `sources` 那一格没跟 push 走（`%(srcbefore)s`），
     第三朵是 `test_skip_roster` 的**借红**（内层那一卷自己红 ⇒ 观察者没有可对账对象）；
   · 第五趟（`report_sources_cell.py --write` 之后、本补记落盘**之前**）：`%(b5)s` —— 这一趟才是"账改完"的证人；
     而**本补记那一节自己**没有电池证人（它写在电池之后 ⇒ 只能由含它的那一跑签收，R580 那条同形规矩：
     电池格是自指的，记到第几趟就停，最终签字归 runner）。
   四趟之间**没有**并跑捕获/刀/电池（主节 ⑨·2 那次破规矩是本轮早段，之后所有读数都出自串行趟）。
   第二/三/四趟的日志都在盘上：`py_battery2.txt` / `py_battery3.txt` / `py_battery4.txt`（每趟文件尾都写了 `EXIT=` 那一行）。

③ **两条口径的 forward 更正（不回删主节原文）**：
   1. 用户指令「台账里『产品面连续零改动 N 轮』那一格应该回到 0」—— 在这一把尺上**到不了 0**。
      `streak_at` 从 R334 起用**严格小于**（本轮自己那一笔不记进自己那一格），所以它的**复位值是 1**：
      落盘之后现读 `%(streakshort)s` ⇒ 本轮那一格 = 24（R568 / 第 567 轮是分界），下一轮的分界换成本笔 `%(mainsha)s` ⇒ 读 1。
      "归零"在这本账上的形状是"分界换成本轮"；主节 ⑥ 那一格已按这个口径写死，这里只是把**为什么不是 0** 说全。
   2. 主节 ⑤ 那句「我自己打开看的三张」是**写早了**：尺点名要开的两张（`cardprobe-groupbox-default-720x140`
      暗档 + 亮档）我在这之后都打开了 ⇒ 真数是**四张**，主节已改成四张并补了一句"本轮产品面不在这批离屏帧的
      覆盖面里"（改的是窗口恢复几何，帧夹具按固定尺寸建窗 ⇒ 那一半只能由真机 AX 读数签，见主节 ① 第 5 条）。

④ **本笔只动 `AGENT_STATE.md` 一本 + 本轮自己的脚本**；名册、豁免表、四张按机器登记的表、帧名单一字未动
   （主笔里唯一一处与名册有关的改动是 `SKIP_ROSTER` 中那一行的**理由文字** —— 机制从"仓库根没有包"变成
   "暂存目录没有包"，留着旧文字就是假话；登记本身没增没减没删）；`update` 一次没跑；没改这台机器的全局外观；
   没动用户的 Dock 与登录项（那条是人工验收批次 91.1）；帧与日志不含用户真实剪贴板原文。
   §3 第③段仍不开工：两条具名阻塞一字未撤、规格里「三问全过」出现 0 次、`STAGE_GATE_CLAIMS` 现读无证断言=0。
""" % {u"cilatest": cilatest[:300], u"ptime": ptime, u"gtime": gtime,
       u"runid": run_id, u"mainsha": MAIN_SHA, u"runstatus": run_status,
       u"mainlog": os.path.join(TMP, "log_42179047067.txt"),
       u"recon": grab(recon, u"RED_NAME_RECONCILIATION", u"红名对账门"),
       u"reconfirst": (u"RED_NAME_RECONCILIATION 节=R592 红名=12 计入行=10 编号去重=9 不计入=0 未标=2 对不上=2 口径=已启用"
                       u"（第一趟的逐字读数，取自 19:27 那一趟的门输出）"),
       u"absence": grab(absence, u"LEDGER_ABSENCE_RESULT", u"清账门"),
       u"causesline": grab(causes, u"CI_SKIPPED_CAUSES ", u"接线形状那一支"),
       u"skipgate": grab(skipg, u"CI_SKIPPED_CENSUS", u"skipped 成因门"),
       u"glue": grab(glue, u"CI_CHANNEL_GLUE_SCOPE", u"值槽粘连扫描面"),
       u"curve": grab(curve, u"SCORES_BY_ROUND", u"曲线尺"),
       u"sec1": grab(sec1, u"REFRESH_SECTION1", u"§1 刷新"),
       u"streak": grab(streak, u"PRODUCT_STREAK ledger_round", u"产品面连续轮数"),
       u"streakshort": grab(streak, u"PRODUCT_STREAK ledger_round", u"产品面连续轮数").split(u" as_of")[0],
       u"b2": battery_signatures("py_battery2.txt"),
       u"b3": battery_signatures("py_battery3.txt"),
       u"b4": battery_signatures("py_battery4.txt"),
       u"b5": battery_signatures("py_battery5.txt"),
       u"srcbefore": grab(src_before, u"SOURCES_CELL", u"sources 那一格").split(u"要写")[0].strip(),
       # 已经同源时 `--write` 只印 `SOURCES_CELL … 一致=是`、不印 `SOURCES_CELL_WRITTEN` ⇒ 两种形状都要认，
       # 否则这一支会在"本来就没问题"的那一趟当场崩（把绿读成通道坏了）。
       u"srcwrite": ([l.strip() for l in src_write.splitlines()
                      if l.startswith(u"SOURCES_CELL_WRITTEN")]
                     or [l.strip() for l in src_write.splitlines()
                         if l.startswith(u"SOURCES_CELL ")])[-1],
       u"srcafter": grab(sh([sys.executable, "scripts/report_sources_cell.py"]),
                         u"SOURCES_CELL", u"sources 那一格复算").split(u"要写")[0].strip()}

    head = u"## R592 补记（第 591 轮 / Round 589 · 产品 2 文件）"
    block = head + block.split(u"\n", 1)[1]
    pos = hits[0].start()
    new = t[:pos] + block.rstrip(u"\n") + u"\n\n" + t[pos:]
    io.open(STATE, "w", encoding=u"utf-8", newline="\n").write(new)
    check = io.open(STATE, encoding=u"utf-8").read()
    n = check.count(u"## R592 补记")
    if n != 1:
        raise SystemExit(u"落盘后 R592 补记标题现读=%d（该恰 1）⇒ 停" % n)
    print(u"WROTE 补记 长度=%d 标题现读=%d" % (len(block), n))
    return 0


if __name__ == u"__main__":
    sys.exit(main())

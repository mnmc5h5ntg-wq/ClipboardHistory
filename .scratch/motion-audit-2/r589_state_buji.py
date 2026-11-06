# -*- coding: utf-8 -*-
"""R589 补记笔的 STATE 那一节：⓪ 本轮那一跑现取现写（未到数）+ 落盘后门复算 + ⑨ 封条在 13 格。

锚：`## R589 状态（` 第一次出现处（补记插在它**上面**，与 R585–R588 补记同形）。
写前断言锚命中一次、写后回读计数；幂等：盘上已有 `## R589 补记` 就什么都不做。
本节文本要过它自己的守卫 ⇒ 落盘后立刻跑 `scripts/stage_gate_claims.py`（判最新一节 = R589 主节 + 本补记）。
"""
import io
import re

ROOT = "/Users/wangziyi/Codex_Project0"
P = ROOT + "/AGENT_STATE.md"
ANCHOR = u"## R589 状态（"
HEAD = u"## R589 补记（"

BLOCK = u"""## R589 补记（第 588 轮 / Round 586 · 产品 0 文件）：⓪ 本轮那一跑此刻还没到数 ⇒ 成对号现取现写；派生格与门复算都在落盘之后取

⓪·1 **本轮主笔的成对号（push 之后一次现取，不预测、不轮询）**：`42159254212 ↔ 5fcac1c`
    现读 `status=in_progress`、`conclusion=` 空 ⇒ **未到数**（取值时刻 11:53）。
    进行中的 job 打 `--log` 得到 0 字节是**通道还没内容**，不是**内容里没有**；这一格只登记「该由 R590 去读」。
⓪·2 **本补记笔自己那一跑 ⇒ `RUN_UNFETCHED=这一笔落地时尚不存在`**（修尺/补账那一笔的跑签不了自己，R555/R565/R584–R588 补记同一条）。
⓪·3 **R590 的 ⓪ 要读的五格**（判法与「正文从哪一步取」都写在 `ci_status_r589.py` 的 `PREDICTIONS_R590`，由脚本判、不许目测对拍）：
    ①`42159254212 ↔ 5fcac1c` 到数之后读**全部**失败步骤，并**逐步骤结论另取一趟**
      （`jobs[].steps` 的 conclusion —— `steps` 视图不给成功步骤建行，「不在失败列表里」不等于「跑过且绿」）；
    ②本补记那一跑（现取成对号再读）；
    ③`STEP[11]` 里 `FRAME_BASELINE_SCALE_BASELINE_UNKNOWN` 第一次出现没有 ——
      本机那一门今天已经真读到它（`基线出处=无 基线原因=（无） 当轮=2.00x（356 张 分布=2.00x:356）`），
      runner 那一份基线同样说不出倍率而它自印 1.00x ⇒ **这一跑应该响**，不响就是尺或接线的问题；
    ④`STEP[9]` 里 `TIER_SHAPE_RESULT=ok` 且 `分支链≥2`、`STAGE_GATE_RESULT=ok`、`IDENTICAL_PAIR_RESULT=` 有没有出声
      （没有 `IDENTICAL_PAIR_RESULT=` 这一行 = 接线没跑起来，**不等于**「runner 上没有副本」）；
    ⑤`SHAPE_GUARD_EXIT … rc=0` 恰好两行 —— 这是"接线本身"的证人，不是判据内容的证人。
    另两条不许从问题开始：`变帧=16 已登记=16`（本机那一门，与 655 同源）与 `row-pinned-off` 无消费者那一格
    （夹具源码里引用次数现读=1 ⇒ 638 那句「不为任何断言单独作证」的唯一可数实例）。

① **落盘之后的门复算（四个时刻都记，不合并）**：
    · 红名对账（本笔落盘**前**那一趟 = 主笔落盘之后）：`RED_NAME_RECONCILIATION 节=R589 红名=12 计入行=9 编号去重=7 不计入=3 未标=0 对不上=0 口径=已启用`
      —— `未标` 与 `对不上` 都归 0 是**门自己说的**，不是我数的；第一版我写的三条「不计入」是**跨行**的，
      门按行解析 ⇒ 读成 `未标=3 对不上=3`，改成单行之后才归 0（这是形状错，不是我把红说成了绿）。
    · 清账门：`LEDGER_ABSENCE_RESULT=ok 不成立=0/63`（格=162 声明=63）。
    · 段号守卫：`STAGE_GATE_RESULT=ok`（判的范围=STATE R589 + ITER 最新一节；`断言=0 冒充段号=0 提及或反向=1`），
      而 `三问全过证人=无`、`仍挂着的阻塞=2` ⇒ 闸门没被抬起来，本轮仍然只在第②段。
    · 派生格：`product_streak.py` 落盘前读 20、落盘之后读 **21**（`ledger_round=588 streak=21 sections=564`）；
      §1 由 `refresh_report_section1.py` 刷到 `n=579 尾轮=586`（第一趟它拒绝刷新并报「曲线尺不是绿的」——
      因为我那一版七维表用了自造的维度名与 /20 刻度，`curve_from_ledger.py` 当场 `DERIVED_NO_MARKER=586` 拒绝。
      **这是尺抓住了我**：修成曲线尺认的那七个名字 + n/15 之后才绿，`test_curve_gaps` 现读 3 格 OK）。
    · 电池：台账之前那一趟 `Ran 885 tests OK (skipped=5)`；台账之后那一趟也 `Ran 885 tests in 113.500s / OK (skipped=5)`
      —— 两趟之间红过 5 朵 + 1 错（§1、曲线、streak 两格、skip_roster 借红），全部按设计里写好的路走完之后复跑才绿；
      本机这一趟的数**不回填**成 runner 的签字，最终签字归 `STEP[9]`。

② **五把刀之外这轮的七把末态（本笔现读并签，主笔已签过、这里只复核还原）**：
    `M1560 / M1561 / M1562`（分支穷尽与守卫自身盲区）+ `M1563 / M1564 / M1565 / M1566`（副本名册四格）
    全部 `预检=PASSED`、`CAUGHT (rc=1)`、`RESTORE_CLEAN=yes`，每把单独取退出码、没接 `| head`；
    四张被改仪器对 **HEAD** 逐张 md5 现读全同（`630cd54a / cb2335c4 / 9d07e040 / beb3879c`，取值时刻 11:53），
    `git status scripts/` 空 ⇒ 刀链跑完的树就是含本笔的那棵树。
    刀高水位是**落刀前现读**的 M1559（没抄派单给的数），本轮用到 M1566。

③ **⑨ 的封条**：主笔那一节的 ⑨ 记到 **⑨·13** 为止（13 条都是本轮实际发生的，其中 ⑨·12 是"派生格跨节改写历史"
    那一族的第 12 次复发、⑨·13 是 heredoc 引号那一族在本轮第三次重犯 —— 两条都当场修了并留了证人，
    没写成"没发生"）。本补记**不往 ⑨ 里加新格**；本节新增的自陈只有两句：
    · ① 那一格里"七维表第一版用了错的维度名"这件事，我在主笔的 ⑨ 里**没有单列**，是因为它当时还没发生
      （台账落盘之后才被曲线尺抓住）—— 现在它记在 ITERATION 的「台账一致性」那一格里，位置要说清；
    · 本补记的 ⓪·1 是 push 之后一次取的，它 `in_progress` **不构成**对本轮任何判据的复核。

④ **台账计数器（本笔只动 STATE 一本）**：`## R589 补记` 形状写前现读=0、写后=1；
    UI/ITER/BACKLOG/DEC/FINAL/CHANGE 六本一字未动（补记不重复记账）。
    禁碰清单照旧逐轮携带：本轮没碰 `Sources/`、没碰捕获侧 Swift（`UICaptureHarness.swift` 那 11 处一字未动 ⇒ 只登记成 661）、
    没动三张按机器登记的表与 `registeredOffscreenVerdict(scale:)`、没动任何地板/阈值
    （4.5 墨地板 / 150 上限 / 120ms / Motion ≥2 / 2x 8.0pt / 1x 6.0pt / `FLOOR_LIGHT=1.20` / `FLOOR_DARK=1.10` /
    像素容差 1.5 / 跳变地板 8 / `probeInkFraction=3%` / `.contentFade` 0.20 / `--allow-missing` 一字未改）、
    名册与豁免表一字未改、`STAGE2_CLICKTHROUGH_BLOCKED` 与
    `STAGE3_FRAME_CRITERIA_HAVE_NO_RUNNER_WITNESS=awaiting-654-direction` 与
    `PRODUCT_MAIN_TREE_TRANSPARENT_OBJECT_NOT_JUDGED` 与 `FRAME_BASELINE_DRIFT_NOT_JUDGED` 四条一条没撤、
    着色器一字未写、这台机器的全局外观没动（656 那三条出路仍归用户）、
    **没删一张帧、没改基线名单、没跑 `frame_baseline.py update`**（638① 与 655 仍归用户）。

"""

text = io.open(P, encoding="utf-8").read()
if text.count(HEAD) >= 1:
    print(u"DRY：盘上已有 `## R589 补记`（幂等重放）⇒ 不动")
    raise SystemExit(0)
n = text.count(ANCHOR)
assert n == 1, u"锚 `## R589 状态（` 命中 %d 次 ⇒ 不是唯一，停" % n
print(u"锚后首行=%s" % text.split(ANCHOR, 1)[1].splitlines()[0][:60])
new = text.replace(ANCHOR, BLOCK + ANCHOR, 1)
io.open(P, "w", encoding="utf-8", newline="\n").write(new)
back = io.open(P, encoding="utf-8").read()
print(u"写后回读：补记=%d 主节=%d 新增字符=%d"
      % (back.count(HEAD), back.count(ANCHOR), len(new) - len(text)))
m = re.search(u"(?m)^最后更新：(\\d{4}-\\d{2}-\\d{2})（本地 · R(\\d+) / 第 (\\d+) 轮 / Round (\\d+)）$", back)
print(u"最后更新行=%s" % (m.group(0) if m else u"（没读到）"))

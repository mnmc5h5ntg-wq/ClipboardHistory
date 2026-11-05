# -*- coding: utf-8 -*-
"""R587 补记笔的 STATE 那一节：⓪ 成对号 + R588 读单 + push 通道三读 + ⑨ 封条。

锚：`## R587 状态（` 第一次出现处（补记插在它**上面**，降序形状与 R586 补记同）。
写前断言锚命中一次、写后回读计数（幂等：盘上已有 `## R587 补记` 就什么都不做）。
"""
import io
import re

ROOT = "/Users/wangziyi/Codex_Project0"
P = ROOT + "/AGENT_STATE.md"
ANCHOR = u"## R587 状态（"
HEAD = u"## R587 补记（"

BLOCK = u"""## R587 补记（第 586 轮 / Round 584 · 产品 0 文件）：⓪ 本轮那一跑此刻还没到数 ⇒ 只登记成对号与「该由谁签」

⓪·1 **本轮主笔的成对号（现取，不预测）**：`42130898663 ↔ f01ba38` 现读 `status=in_progress`、`conclusion=` 空 ⇒ **未到数**。
    没轮询、没拿本机读数顶它、没把「还没读到」写成「没有红」；进行中的 job 打 `--log` 得到 0 字节是**通道还没内容**，不是**内容里没有**。
    取号时刻=push 之后一次 `ci_read.py latest`（07:39 现读），这一格只登记「该由 R588 去读」。
⓪·2 **本补记笔自己那一跑 ⇒ `RUN_UNFETCHED=这一笔落地时尚不存在`**（修尺/补账那一笔的跑签不了自己，R555 / R565 / R584 / R585 / R586 补记同一条）。
⓪·3 **R588 的 ⓪ 要读的六格**（照抄即可开工，判法写在 `ci_status_r587.py` 的 `PREDICTIONS_R588`，由脚本判、不由下一轮念）：
    ①`42130898663 ↔ f01ba38` 到数之后读**全部**失败步骤（不只盯 STEP[11]）；
    ②`FRAME_BASELINE_BAKE` 那一行必须带四个新格子 `倍率分布= / 不一致帧数= / 无尺寸段= / 原因=`（旧文档那一份仍应印 `出处=无 … 原因=（无）`，形状不许被当成缺字段而红）；
    ③当轮说不出倍率时**只许**出现 `FRAME_BASELINE_SCALE_NOT_RUN=<reason>` 一条出口 ⇒ 出现第二条（`…_TIE` 被写成不判、或新增 `…_AMBIGUOUS` 之类）就是把「并列」重新藏成两个门路；
    ④`SCALE_TIE / SCALE_BAD / SCALE_SIZELESS` 三朵在 runner 上第一次出现的读数是哪一跑（本机真语料三格都是 0/不响 ⇒ 外部证人归 runner）；
    ⑤`HOVER_TIER 配对=… 认不出档=0` 在 runner 的 1x 帧集上是否仍为 0（本轮只换了词表来源，没换解析法）；
    ⑥**归因锚（已到手，不许 R588 重跑）**：`42118421683 ↔ 0b39576` 与 `42119000322 ↔ 7837e00` 都是 `completed / failure`，
      失败步骤逐字 `STEP[15]/[17]/[19]`（补记笔多一朵 `STEP[18]`）⇒ **STEP[11] 两跑都没红**；
      门那一行逐字 `本机=github-runner 基线署名=local:MacBook-Air.local 判=不判 变帧=356 他机行=16 未登记（不判）=356` ⇒ 出口·乙，与 R584/R585/R586 同形状；
      `42108062173 ↔ ba093be` 也到数（同形状），但那一跑的**步骤名恒为 `UNKNOWN STEP`** ⇒ 正文按通道串取，
      且**必须**按「基线署名==那一笔文档署的那台机器」筛，否则会把电池的合成行读成真门（本轮 ⑨·8 就是这么错的）。

① **push 那一格每轮现读**：本轮 `PUSH_TRANSPORT=ssh` —— `git push origin main` rc=0，逐字 `To github.com:mnmc5h5ntg-wq/ClipboardHistory.git ⏎    7837e00..f01ba38  main -> main`；
    复验 `git rev-list --count origin/main..HEAD`=**0**、`HEAD=origin/main=f01ba38`。
    同一时刻另三条通道各自现读、互不替代：`github.com=200`、`api.github.com=200`、`dscacheutil -q host -a name github.com` 含 ip 的行数=**1**。
    没改 `remote.url`、没动 `~/.ssh`、没换 hosts/解析/直连 IP（R493 / 2026-11-03 那一族：`api=200` 不等于可推，DNS 有 ip 也不等于可推）。

② **本轮唯一向前的一句话**：`SCALE_NOT_RUN` 那条出口在 runner 上今天会不会**因为并列**而第一次响？—— **还不知道**：
    本机真语料是单一倍率（`2.00x:356`），runner 那一跑自印 `1.00x` 而工作基线说不出倍率（旧文档 ⇒ `原因=（无）`）⇒
    那一跑上「当轮能说出、基线说不出」的组合只会走 `SCALE_MISMATCH` 那一支或什么都不印，
    「两档各半」这件事在两台机器上今天都没有实例 ⇒ 并列这一支的外部证人仍然欠着，只能由含本笔的跑或一次真混批提供。

③ **⑨ 的封条**：本节 ⑨ 到 ⑨·9 为止（门复算末态 `红名=13 计入行=9 编号去重=9 不计入=4 未标=0 对不上=0`，
    由 `red_name_reconciliation.py` **落盘后**复算签；落盘前那一趟是 `节=R586 …`，两趟都记，不合并）。
    本补记**不往 ⑨ 里加新格**；本补记唯一新增的自陈是这两句：
    · ⓪·1 那一跑的状态是 push 之后一次取的，它此刻 `in_progress` **不构成**对本轮任何判据的复核；
    · 台账落盘之后电池第一趟红两朵（`test_final_report_section1_cell` 报「§1 停在旧数而仪器已往前走」，
      `test_skip_roster` 是借红），按设计里写好的路走 `refresh_report_section1.py` 刷新后复跑 814/0/5 ⇒
      这不是新缺陷，是那条守卫**第一次真的抓到本轮**（R579 把 §1 改成派生格之后它就该红）。

④ **台账计数器（本笔只动 STATE 一本）**：`## R587 补记` 形状写前现读=0、写后=1；
    UI/ITER/BACKLOG/DEC/FINAL/CHANGE 六本一字未动（补记不重复记账）。
    禁碰清单照旧逐轮携带：本轮没碰 `Sources/`、没碰捕获侧 Swift（`UICaptureHarness.swift` 那 11 处一字未动 ⇒ 只登记成 661）、
    没动三张按机器登记的表与 `registeredOffscreenVerdict(scale:)`、没动两个地板数值（`FLOOR_LIGHT=1.20 / FLOOR_DARK=1.10`，
    刀 M1550 的负半证人正是「地板那一格不许红」）、`--against` 默认与 choices、`--allow-missing` 两帧原样、第③段着色器一字未写。

"""

text = io.open(P, encoding="utf-8").read()
if text.count(HEAD) >= 1:
    print(u"DRY：盘上已有 `## R587 补记`（幂等重放）⇒ 不动")
    raise SystemExit(0)
n = text.count(ANCHOR)
assert n == 1, u"锚 `## R587 状态（` 命中 %d 次 ⇒ 不是唯一，停" % n
head_line = text.split(ANCHOR, 1)[1].splitlines()[0]
print(u"锚后首行=%s" % head_line[:60])
new = text.replace(ANCHOR, BLOCK + ANCHOR, 1)
io.open(P, "w", encoding="utf-8", newline="\n").write(new)
back = io.open(P, encoding="utf-8").read()
print(u"写后回读：补记=%d 主节=%d 新增字符=%d"
      % (back.count(HEAD), back.count(ANCHOR), len(new) - len(text)))
m = re.search(r"(?m)^最后更新：(\d{4}-\d{2}-\d{2})（本地 · R(\d+) / 第 (\d+) 轮 / Round (\d+)）$", back)
print(u"最后更新行=%s" % (m.group(0) if m else u"（没读到）"))

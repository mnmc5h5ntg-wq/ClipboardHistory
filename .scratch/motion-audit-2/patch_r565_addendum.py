# -*- coding: utf-8 -*-
"""把 R565 补记的 NUM 填上（内部工具，跑完即可弃）。"""
import io

p = '.scratch/motion-audit-2/addendum_r565.py'
s = io.open(p, encoding='utf-8').read()

PAIRS = (
    u"⓪ 笔 `a7e1790`（开工节 + 读单改账 + 两个扫描的落空名单）、A 笔 `f6c2a1d`（产品 1 文件 + 判据 1 条 + "
    u"刀 M1466/M1467 + 帧 26 张同一笔 update）、B 笔 `020cef3`（修 R564 守卫写死的机器根 + 路径卫生守卫 + "
    u"刀 M1468/M1469）、台账笔 `20c55cf`（七本 + 派生格落盘后现读）与本补记笔**同一次 push** ⇒ GitHub 只给头笔建跑，"
    u"中间四笔**没有独立跑** ⇒ 具名 `CI_UNREAD / 同次 push 只有头笔建跑`，不许写成「没红」。"
    u"sources 格本轮**有变化**（产品 1 文件）：`report_sources_cell.py --write` 之前现读 "
    u"`账上=R560/631f910 git=R565/f6c2a1d 一致=否` ⇒ 写完复核 `一致=是`，**在同一笔台账里落**（R558/R561 那一族时序红本轮没犯）。"
)

CI_CLOSE = (
    u"两跑都到数且**同一形状**：`41552571306↔4cfcfc6`、`41552998637↔8eecbc7` = concluded failure，"
    u"逐步现读 `gh run view --json jobs` ⇒ STEP[9] `Release script tests` failure、STEP[10]-[14] skipped、"
    u"STEP[15]-[19] success。**红因不是任何一条视觉判据**，是 R564 那把 commit 守卫把自己的仓库根写成机器绝对路径，"
    u"runner 上目录不存在 ⇒ `subprocess.run(cwd=ROOT)` 抛异常（CI 日志 `/tmp/r565-ci-8eecbc7.log` 第 8451-8470 行）。"
    u"⇒ 回答 ⓪(f)：**分批不是原因，写死的根才是**；代价是两跑的 STEP[11] 帧基线名册门整段没跑。"
    u"到数的格子：`BULLET_LEVELS` 第二跑仍判到（与首验逐字同）、`HEAT_LEGEND_COVERAGE` 连续第三跑判到且 `NOT_RUN` 零行、"
    u"`过渡帧数` 第六数 = 6（六数 2/5/0/5/6/6，每格 …/32.0/27.0ms）、STEP[15] 这两跑 success ⇒ "
    u"SelectionReveal 那朵间歇红未复现（累计 `6ef9ff1` 红 / 这两跑绿）；`SKIP_ROSTER` 零行按 634 记"
    u"「内层红 ⇒ 无可对账对象」，既不记绿也不记红。"
)

READS = (
    u"build 告警 **0**；判据卷 `UICaptureTests` **222/4 skipped/0 失败（572.2s）**（221→222 = 本轮新判据）；"
    u"帧 **356 张：update 之前 `COMPARED=356 CHANGED=26 MISSING=0 ADDED=0`，26 张逐字名单 = 13 个 `quickpick-*` "
    u"夹具 × 明暗两档（`/tmp/r565-chain-compare.log`）⇒ 非浮层帧一帧未变**，同一笔 `frame_baseline.py update` "
    u"之后复跑 `CHANGED=0 MISSING=0 ADDED=0`；全量 **1406/57/0（619.4s）**；预检三读**串行** "
    u"`tables=368 covered=295 arms=757 bad=0`、`ARM_TOTAL files=461 arms=1244 dupes=0 repeats=0`、"
    u"`HIDDEN_ARMS 表=455 可判=1183 rot=0 抽不出=6 已声明表=6 处置=ok`（本轮名册 +4 张表 ⇒ 三个数各 +4，"
    u"`bad=0/dupes=0` 是新刀没重复没漏登记的证人）；换装 `INSTALL_RESULT=ok / INSTALL_SHA_MATCH=1 / "
    u"INSTALL_ENTRIES=433=433 / SMOKE_OK=1 / INSTALL_SIGNATURE=local flags=0x0`（版本 1.4.8→1.4.8，PID→33353，"
    u"备份 `before-R565`）；清账 **162/63/0**；streak **台账落盘之后**现读 ⇒ `PRODUCT_STREAK_LEDGER_OK streak=5`"
    u"（⚠ 这是**未推状态**下门自己派生的数：门只认已推的产品笔，本轮产品笔 `f6c2a1d` 还在本地 ⇒ 5；"
    u"push 之后同一命令会派生成 0，由下一轮现读覆盖 —— 第一次写 0 被 `PRODUCT_STREAK_LEDGER_STALE` 点过，"
    u"这是同一格第五次被点）；sources 格 `--write` 之前 `账上=R560/631f910 git=R565/f6c2a1d 一致=否` ⇒ 写完复核一致；"
    u"**占位符回读（percent 后接字母 那一形状）逐节现读 = 0**；电池 **`Ran 709 / OK (skipped=5)`、退出码 0**"
    u"（台账 + `--write` 之后一遍过；本轮 +3 条 = 新守卫三条腿）。"
)

vals = {
    "PAIRS": PAIRS,
    "CI_CLOSE": CI_CLOSE,
    "READS": READS,
    "SKIPPED": u"**57 连八跑**（R558–R565 都是 57 ⇒ 只记现读，不动门、不修回 55）。",
    "FRAME_WITNESS": u"帧 26 张变更全部落在 `quickpick-*`、其余 330 张逐字节不变",
    "STREAK": u"5（未推状态下门自己派生；push 后同一命令 = 0）",
}
for k, v in vals.items():
    old = '    "%s": "@@%s@@",' % (k, k)
    assert s.count(old) == 1, k
    s = s.replace(old, '    "%s": %s,' % (k, repr(v)))
io.open(p, 'w', encoding='utf-8').write(s)
print('ADDENDUM_NUM_FILLED')

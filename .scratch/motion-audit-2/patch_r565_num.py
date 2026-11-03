# -*- coding: utf-8 -*-
"""把本轮现读数填进 ledgers_r565.py 的 NUM（R565 内部工具）。"""
import io
import re

p = '.scratch/motion-audit-2/ledgers_r565.py'
s = io.open(p, encoding='utf-8').read()

CI_CLOSE = (
    u"**收口前两跑都到数**（开场 in_progress ⇒ 具名 NOT-RUN，数到手在收口之前）："
    u"`41552571306↔4cfcfc6` 与 `41552998637↔8eecbc7` 都是 concluded **failure**，"
    u"而 `gh run view --json jobs` 逐步现读给出的是同一种形状：**STEP[9] `Release script tests` failure、"
    u"STEP[10]-[14] skipped、STEP[15]-[19] success** ⇒ 红的是我 R564 自己写死根的那把守卫（见 U-2444），"
    u"不是任何一条视觉判据。到数的四格（`ci_read.py readings`，正文取自 emit 通道；那一跑的步骤名解析成 "
    u"`UNKNOWN STEP` ⇒ 按 emit 串取，不按步骤名过滤）："
    u"(b) `BULLET_LEVELS` **第二跑仍判到** —— `BULLET_LEVELS light/dark 行=6 列=3 步进=[16, 16]px(16.0/16.0pt) "
    u"容差=1px 合并=1px 筛除 宽≤8px 隙≥4px 倍率=1.0x 列x=36px 墨高=5px(5.00pt) 列x=52px 墨高=4px(4.00pt) "
    u"列x=68px 墨高=5px(5.00pt)`，与首验那一跑逐字相同；"
    u"(c) `HEAT_LEGEND_COVERAGE light/dark 格色=6 图例色=5 缺=[] 格宽=11px 倍率=1.0x 网格下缘 y=164 "
    u"实心判定 格6px/图例3px 地板 格4/图例4 每方块采样点 格9/图例9`（4 行）而 `HEAT_LEGEND_NOT_RUN` **零行**"
    u" ⇒ 连续第三跑判到；(d) `MOTION_MARKDOWN_MODE_FADE scale=1x 帧数=27 过渡帧数=6 相邻差帧数=2 首末连续差=0.0048 "
    u"峰值=0.0193 声明=200ms 窗口=701ms 每格=27.0ms` ⇒ **第六数 = 6**（六数 2/5/0/5/6/6，每格 71.5/26.0/75.6/28.9/32.0/27.0ms）"
    u"⇒ 按 629 既有口径具名入账，≥2 未触碰；(e) STEP[15] `Swift tests` 这两跑 **success** ⇒ "
    u"`SelectionRevealAnimationTests` 那朵间歇红**没有复现**（累计：`6ef9ff1` 红、`4cfcfc6`/`8eecbc7` 绿）；"
    u"`SKIP_ROSTER` 在这两跑**一行都没有** —— 那不是绿也不是红：STEP[9] 的内层电池被我的守卫打死，"
    u"观察者按 634 的设计拒绝给结论 ⇒ 具名「内层红 ⇒ 无可对账对象」，第五跑绿的那格仍算 R564 的账。"
)

vals = {
    "FULL": u'1406/57/0（619.4s）',
    "INSTALL": (u'`INSTALL_RESULT=ok / INSTALL_SHA_MATCH=1 / INSTALL_ENTRIES=433=433 / SMOKE_OK=1 / '
                u'INSTALL_SIGNATURE=local flags=0x0`（版本 1.4.8→1.4.8，PID→33353，启动晚于安装、'
                u'exe 路径逐字对上，备份 `before-R565`）'),
    "BATTERY": u'709/5',
    "ABSENCE": u'162/63/0',
    "STREAK": u'0',
    "STREAK_RAW": u'（这一格由台账落盘之后的 python3 scripts/product_streak.py 现读覆盖）',
    "CAPTURE": u'222/4 skipped/0 失败（572.2s）',
    "FRAMES": (u'356 张 —— update 之前 `COMPARED=356 CHANGED=26 MISSING=0 ADDED=0`（26 张逐字名单 = 13 个 '
               u'`quickpick-*` 夹具 × 明暗两档，见 `/tmp/r565-chain-compare.log`；**非浮层帧一帧未变** ⇒ '
               u'改动范围与预测一致，11 个禁碰面在像素层面也没被碰），同一笔 `frame_baseline.py update` 之后复跑 '
               u'`COMPARED=356 CHANGED=0 MISSING=0 ADDED=0`'),
    "PRECHECK": u'tables=368 covered=295 arms=757 bad=0',
    "ARM": u'files=461 arms=1244 dupes=0 repeats=0',
    "HIDDEN": u'表=455 可判=1183 rot=0 抽不出=6 已声明表=6 处置=ok',
    "CI_CLOSE": CI_CLOSE,
    "PRODUCT_SHA": u'f6c2a1d',
}
for k, v in vals.items():
    old = '    "%s": "@@%s@@",' % (k, k)
    assert s.count(old) == 1, k
    s = s.replace(old, '    "%s": %s,' % (k, repr(v)))
io.open(p, 'w', encoding='utf-8').write(s)
print('NUM_FILLED')

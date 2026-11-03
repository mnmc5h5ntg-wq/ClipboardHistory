#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R565 补段的台账笔（同一轮续写，不开新轮）。

七本各自动的位置与锚点：
- AGENT_UI_AUDIT：R565 那一节的 U 区间上界 + 五行新 U 条目（插在 `## 第 563 轮` 之前）。
- AGENT_VISUAL_ITERATION：Round 562 一节里"**七维度自评**"之前追加一段正文（**不加表格行** ——
  七维表"恰好七行"是电池硬格式，补段只能进正文）。
- CHANGELOG：`## [Unreleased]` 之下插一条新的 R565 补段条目。
- AGENT_DECISIONS：D-565 之后追加 ⑤⑥⑦ 三格（D-565 是文件末节）。
- AGENT_FINAL_REPORT：R565 那一笔追加补段句 + U 上界改到 U-2450。
- AGENT_STATE：`### R565 补记` 追加 ⑪ 一整格，并把 R566 读单补两格（(h) 639、(i) 640）。
BACKLOG 的 639/640 由前一笔脚本已经落好，这里不重复。

幂等：每一本都要有守卫，且守卫搜的串不许出现在它自己写的正文里。
"""
import io
import re
import sys

NUM = {
    'FULL': '1406/57/0（827.5s，本段最终树上重跑的那一卷）',
    'CAPTURE': '222/4 skipped/0 失败（779.1s，撤掉诊断腿后重拍的那一卷）',
    'BATTERY': '`Ran 719 / OK (skipped=5)`、退出码 0（台账落盘前那一跑，710→719 = 卫生守卫 9 格；台账 + `--write` 之后还要复跑，数若变就照实在补记里加一行）',
}

check = '--check' in sys.argv


def rd(p):
    return io.open(p, encoding='utf-8').read()


def wr(p, t):
    io.open(p, 'w', encoding='utf-8').write(t)


def guard(t, needle, label):
    if needle in t:
        sys.stderr.write('ALREADY_PATCHED %s（搜到 %r）\n' % (label, needle[:28]))
        sys.exit(1)


def once(t, old, new, label):
    if t.count(old) != 1:
        sys.stderr.write('ANCHOR_BAD %s 命中=%d\n' % (label, t.count(old)))
        sys.exit(1)
    return t.replace(old, new, 1)


def fill(text):
    out = text
    for key, value in list(NUM.items()) + [('FULL', NUM['FULL']), ('CAPTURE', NUM['CAPTURE'])]:
        out = out.replace('%%(%s)s' % key, value)
    if '@@' in out:
        sys.stderr.write('NUM_NOT_FILLED %s\n' % out[out.find('@@'):out.find('@@') + 24])
        sys.exit(1)
    left = re.search(r'%\((?![A-Za-z])', out)
    if left:
        sys.stderr.write('PLACEHOLDER_LEFT %s\n' % out[left.start():left.start() + 30])
        sys.exit(1)
    bad = re.search(r'%\([A-Za-z_]+\)s', out)
    if bad:
        sys.stderr.write('PLACEHOLDER_UNREPLACED %s\n' % out[bad.start():bad.start() + 30])
        sys.exit(1)
    return out


UI = '''- **U-2446：补段 A —— 绝对根"扫干净"而不是只修那一条**（监工点名的第二格）。现读 `grep -rn "/Users/wangziyi" scripts/ .github/workflows/` ⇒ 9 行 / 4 个文件，逐位判定并各给去处：`test_mutate_arm_registry.py` 两行是**文档串引用历史**（改成不带真名的说法）、`test_mutate_r271_needle.py` 三行是**正/负对照样本**（换合成 `/Users/someone/DemoRepo`，并把那颗常量改名 `BAD_MACHINE_PATH_SAMPLE` —— 它名字带 ROOT，被新形状判抓到 ⇒ "坏形状样本"不该长得像活根）、`test_frames_path_hygiene.py:36` 是**模式本体**（从前抄成真人用户名 ⇒ 判据的靶比它要防的缺陷窄，改判形状 `(ROOT|REPO_ROOT|repo_root|REPO|*ROOT) = "/(Users|home)/`，正对照补 `REPO_ROOT = "/home/anyone/Repo"`）、`fixtures/r46_motion_local.log` 是数据夹具（不参与读数打印 ⇒ 具名不列修）。⇒ 现读结论：**会进 CI 的脚本里 0 处运行时绝对根**。
- **U-2447：补段 C —— 同族两种坏法收成一条统一守卫**（判据 1 支、电池 9 格）。`scripts/ci_channel_hygiene.py` 三格：①名单从 `.github/workflows/*.yml` **现读**且不许为空；②绝对根按"**这台机器上真存在的账号**"判（形状判归 U-2446 那一支，两支各判一件事，不重复抄）；③**通道值里不许有裸空格**（判法：`键=%s` 槽位喂的那个名字在本文件被赋过含空格的字面量）。扫描范围是被迫扩的：只按 ci.yml 抽名单会漏掉 R564 那支守卫（STEP[9] 跑 `unittest discover`，它是被电池 subprocess 调的）⇒ 加 `referenced_by_battery()`，只收真存在的那一颗（电池正文里的假样本 `scripts/x.py` 会变成幽灵条目，本轮抓到过一次）。现读 `CI_CHANNEL_HYGIENE ci脚本=14 电池脚本=73 电池引用=24 合计=99 绝对根=0 真人路径=0 通道空格=0` / `RESULT=ok`。
- **U-2448：刀 M1470-M1473 全 CAUGHT、RESTORE_CLEAN=yes**（needle 现读各命中 1）。**M1470** 把绝对根塞回 `commit_round_identity.py` ⇒ `绝对根=1 真人路径=1`；**M1471** 把 `if not roster:` 改成 `if False:` ⇒ 红话"空名单被读成绿 ⇒ 这一格是恒真的"；**M1472** 把退化说明塞回 `范围=` 的值 ⇒ `通道空格=1`；**M1473** 在 `make_info_plist.sh` 写死绝对根 ⇒ **非 .py 那一支**红（上一版扫描器只会 `ast.parse`，喂 shell 就 parse-error ⇒ CI 真跑的 `.sh` 整个在尺外）。名册 +4 ⇒ `tables=372 covered=295 arms=757 bad=0`、`ARM_TOTAL files=465 arms=1244 dupes=0 repeats=0`、`HIDDEN_ARMS 表=459 可判=1183 rot=0 抽不出=6 处置=ok`。⚠ 这一批仍是**单臂形状** ⇒ `ARM_TOTAL` 的臂数 +0（抽臂器只认列表形状，与 M1466-M1469 同形）—— 具名"臂数不可抽，会红性由四把真跑证明"，**不许写成"1244 里含这四把"**。
- **U-2449：补段 B —— `HINT_CONTRAST` 那朵 runner 红：倍率被现读排掉，分歧在"渲染 vs 名义"，开 639。** 一次性探针 `probe_r565_hint_contrast_1x.py`（判据自己的 0.01 偏差筛与 `max(40, 偏差/20)` 字芯集合）⇒ 本帧的 1x 代理 light **9.29:1** / dark **11.70:1**（`/tmp/r565-hint-1x-postchange.log`），而旧值 tertiary 的 1x 代理是 light 3.15 / dark 4.34 ⇒ **1x 判得出这两种颜色的差别**，不是 R555 那一族。runner 那两行是 `light 底=236 字芯=(118,118,118) 3.84:1`（=名义 50% 黑压在窗口底色上）而本机 `窗口底色现读=255 字芯/底=0.251` ⇒ 名义口径下 secondary 对白底 ≈4.0:1 **仍跌破 4.5**。走过又被撤掉的出路：具名 `HINT_CONTRAST_NOT_RUN=background-unbackdropped`（条件"底==窗口底色 ±2 且 字芯/底≈0.5±0.05"，本机两档都不落进 ⇒ 本地读数一字未变）**撤掉**，因为它在 runner 上会把一朵真数改成"不判"= 把红藏起来。**不降 4.5、不改期望、不加豁免、没选"这是产品缺陷"那一条**（改颜色撞第 12 面 ⇒ 归用户）⇒ 开 **639**，runner 那一朵红原样留着。
- **U-2450：补段的帧与账 —— 基线**不更新**（138 张漂移，三条解释被现读排掉）**。本段产品 0 文件，而 `FRAME_BASELINE_COMPARED=356 CHANGED=138`（两次连拍 + 撤掉诊断腿后重拍，**同一批 138 个名字**、`/tmp/r565-补-frames` vs `-frames3` 逐字节相同 356/356）⇒ 排除①我的判据诊断腿（撤掉前后完全相同；我第一版注释把它写成自己的罪，已按这两臂改齐）、②捕获随机（连拍逐字节相同）、③夹具时钟（`referenceDate` 是常量）。剩下是这台机器从早上到现在的渲染状态变了（单帧 24–148 个像素、最大通道差 2–7，集中在文字次像素）⇒ **不把 138 张洗进基线**（洗了下一轮的产品改动就没有像素证人），具名 `FRAME_BASELINE_DRIFT=138/356 not-updated` 并开 **640**（两条出路：把渲染状态钉进捕获 / 给基线加次像素容差 —— 后者是放宽门，归用户）。验证链：build **0** 告警；判据卷 **%(CAPTURE)s**；全量 **%(FULL)s**；预检三读串行如上；电池 **%(BATTERY)s**；换装**跳过并具名 `SKIP_INSTALL=no-product-change`**（产品 0 文件 ⇒ 装在跑的那一份仍是 A 笔 `f6c2a1d` 的包 `433=433`，重装只会打断用户正在用的那扇窗）。
'''

ITER = '''**补段（同一轮 R565 的第 ⓪/A/C/B 续段，监工发令"未收口就同一轮继续"）**：这一段真实推进的是**仪器**而不是画面 —— ① 把"绝对根"从修一条变成**扫干净**（现读 9 行 / 4 个文件逐位给去处，并发现旧扫描器的模式抄成了真人用户名 ⇒ 它的靶比要防的缺陷窄，改判形状）；② 把同族两种坏法（R564 的绝对根打死 runner、R565 的通道裸空格打死判它的测试）收成**一条**守卫 `ci_channel_hygiene.py`，三格各自带正对照、四把刀 M1470-M1473 全 CAUGHT；③ `HINT_CONTRAST` 那朵 runner 红：一次性探针把"倍率"排掉（本帧 1x 代理 9.29:1，旧值 1x 代理 3.15:1 ⇒ 1x 判得出颜色差别），分歧落在**渲染 vs 名义**两种口径上，我照第二种口径写过一版具名 NOT_RUN 又**撤掉**（它会把一朵真数改成"不判"）⇒ 不降地板、不改期望、不加豁免、也没自己选"这是产品缺陷"（改颜色撞第 12 面），开 **639** 把三种口径的代价摆出来；④ 帧基线在 0 产品文件的一段里漂了 138 张 ⇒ **不 update**，用两臂（撤诊断腿前后逐字节相同）把它与我自己分开，开 **640**。另两处改账：记忆索引那一行的「已收口」按收口报告改成「未收口」（同一轮互斥**第四次**），以及我第一版把帧漂移写成自己的罪 —— 那句注释错在没跑两臂就归因。

'''

CHG = '''### 会进 CI 的脚本第一次被一条守卫统一管住：绝对根与通道裸空格（R565 / 第 564 轮 / Round 562 · 补段，产品 0 文件）
    同族两次事故（R564 的 `ROOT = "/Users/…"` 打死 runner 的 STEP[9]、R565 的 `范围=…（未推的为空 ⇒ 退化）` 打死本机电池的判它的测试）收成一条 `scripts/ci_channel_hygiene.py`：名单从 `.github/workflows/*.yml` 现读且不许为空、绝对根按"这台机器上真存在的账号"判、通道值里不许有裸空格。扫描范围被迫扩出 `referenced_by_battery()` —— 只按 ci.yml 抽名单会漏掉那支两次打死机器的守卫（STEP[9] 跑的是 `unittest discover`）。绝对根这一族今天**扫干净**：9 行 / 4 个文件逐位给去处，其中 `test_frames_path_hygiene.py` 把自己的**模式**抄成真人用户名 ⇒ 它的靶比要防的缺陷窄，改判形状 `(ROOT|…)= "/(Users|home)/` 并补 `REPO_ROOT = "/home/anyone/Repo"` 正对照。刀 M1470-M1473 全 CAUGHT（含一把专钉 shell 那一支 —— 旧扫描器只会 `ast.parse`，CI 真跑的 `.sh` 整个在尺外）；单臂形状 ⇒ `ARM_TOTAL` 臂数 +0，具名"臂数不可抽"。`HINT_CONTRAST` 的 runner 红被一次性探针排掉"倍率"（1x 代理 9.29:1 vs 旧值 3.15:1），落在**渲染 vs 名义**两种口径：名义口径下 secondary 对白底 ≈4.0:1 仍跌破 4.5 ⇒ 写过一版具名 NOT_RUN 又撤掉（那是把真数藏成"不判"），**不降 4.5、不改期望、不加豁免**，开 **639** 归用户。帧基线在这段 0 产品文件里漂了 138/356 ⇒ **不 update**，并用两臂（撤掉诊断腿前后 356/356 逐字节相同）把漂移与我自己的改动分开，开 **640**。换装跳过并具名 `SKIP_INSTALL=no-product-change`。判据卷 %(CAPTURE)s；全量 %(FULL)s；预检 372/295/757 bad=0；电池 %(BATTERY)s；4.5 墨地板 / 150 / 120ms / Motion ≥2 / 2x 8.0pt / 1x 6.0pt / `probeInkFraction=3%` / `.contentFade` 0.20 一律未动。

'''

DEC = '''⑤ **同族两种坏法收成一条守卫，比各修一条划算。** R564 的绝对根与 R565 的通道裸空格是同一个形状：判据的**输出契约**（哪些字符串会被下游按空格/斜杠切）从来没被任何门判过。一条 `ci_channel_hygiene.py` 判三格（名单非空 / 绝对根 / 裸空格），四把刀各钉一种坏法，其中一把专钉"只会 `ast.parse` 的扫描器把 shell 整个放在尺外"。
⑥ **判据不许为了读数把手伸进渲染里 —— 但也要用两臂证明它没伸。** 我一度给 `HINT_CONTRAST` 加了两格诊断（按外观作用域解析动态色），然后写下注释把它当成 138 张帧漂移的成因；**撤掉腿重拍一整卷，与带腿那一卷逐字节相同（356/356）** ⇒ 那句归因是错的，注释已改。规矩：写"是我造成的"之前先跑撤掉那一臂。
⑦ **基线在 0 产品文件的段落里漂了，就不许 update。** 把 138 张洗成真值，下一轮的产品改动就没有像素证人。具名 `FRAME_BASELINE_DRIFT=138/356 not-updated` + BACKLOG 640 两条出路（钉渲染状态 / 加次像素容差 —— 后者是放宽门，归用户）。同样地，`HINT_CONTRAST` 在 runner 那朵红**保留**，两种口径（渲染 10.37 / 名义 3.84）都印进 639，由用户决定判据主张哪一种。
'''

STATE_CELL = '''⑪ **补段（监工发令「未收口就同一轮继续」）落的是仪器，不是画面**：ⓐ 绝对根**扫干净** —— `grep -rn "/Users/wangziyi" scripts/ .github/workflows/` 现读 9 行 / 4 个文件逐位给去处（两处是文档串引用历史、三处是正/负对照样本 ⇒ 换合成 `/Users/someone/DemoRepo` 并把常量改名 `BAD_MACHINE_PATH_SAMPLE`、一处是扫描器把自己的**模式**抄成真人用户名 ⇒ 靶比缺陷窄，改判形状 + 补 `REPO_ROOT = "/home/anyone/Repo"` 正对照、一处是数据夹具具名不列修）⇒ 会进 CI 的脚本里 **0 处运行时绝对根**。ⓑ 同族两种坏法收成一条守卫 `scripts/ci_channel_hygiene.py`（名单从 ci.yml 现读且不许为空 / 绝对根按"这台机器真存在的账号"判 / 通道值不许含裸空格），扫描范围被迫加 `referenced_by_battery()`（只按 ci.yml 会漏掉那支两次打死机器的守卫；现读 `ci脚本=14 电池脚本=73 电池引用=24 合计=99 绝对根=0 真人路径=0 通道空格=0 RESULT=ok`），电池 9 格、刀 **M1470-M1473 全 CAUGHT、RESTORE_CLEAN=yes**（M1473 专钉"只会 ast.parse 的扫描器把 CI 真跑的 .sh 整个放在尺外"）；单臂形状 ⇒ `ARM_TOTAL` 臂数 +0，具名"臂数不可抽，会红性由四把真跑证明"。ⓒ `HINT_CONTRAST` 的 runner 红：一次性探针把**倍率**排掉（本帧 1x 代理 light 9.29 / dark 11.70，旧值 1x 代理 light 3.15 / dark 4.34 ⇒ 1x 判得出颜色差别），落在**渲染 vs 名义**两种口径（runner `底=236 字芯/底=0.500` = 名义 50% 黑压在窗口底色；本机 `底=255 字芯/底=0.251`）⇒ 名义口径下 secondary 对白底 ≈4.0:1 **仍跌破 4.5**。我照"底==窗口底色且字芯/底≈0.5"写过一版具名 `*_NOT_RUN` 并跑过（本机两档都不落进 ⇒ 本地读数一字未变），**撤掉**：它在 runner 上会把一朵真数改成"不判"= 把红藏起来。**没降 4.5、没改期望、没加豁免、也没自己选"这是产品缺陷"**（改颜色撞第 12 面）⇒ 开 **639**，runner 那朵红原样留着。ⓓ 帧基线：这一段**产品 0 文件**，而 `FRAME_BASELINE_COMPARED=356 CHANGED=138` —— 两次连拍逐字节相同、撤掉诊断腿后重拍仍同一批 138 个名字 ⇒ 排除"我的判据诊断腿"（我第一版注释把它写成自己的罪，**没跑撤掉那一臂就归因，已改齐**）、排除捕获随机、排除夹具时钟（`referenceDate` 是常量）⇒ 是那台机器从早上到现在的渲染状态变了 ⇒ **不 update 基线**（洗进去下一轮产品改动就没有像素证人），具名 `FRAME_BASELINE_DRIFT=138/356 not-updated` + 开 **640**。ⓔ 换装**跳过并具名 `SKIP_INSTALL=no-product-change`**（装在跑的那一份仍是 A 笔 `f6c2a1d` 的包，433=433；重装只会打断用户正在用的那扇窗）。ⓕ 现读：build **0** 告警；判据卷 **%(CAPTURE)s**；全量 **%(FULL)s**；预检三读串行 `tables=372 covered=295 arms=757 bad=0`、`ARM_TOTAL files=465 arms=1244 dupes=0 repeats=0`、`HIDDEN_ARMS 表=459 可判=1183 rot=0 抽不出=6 处置=ok`；清账 `格=162 声明=63 不成立=0/63`；电池 **%(BATTERY)s**。ⓖ 同轮互斥第四处（记忆索引「已收口」vs 报告「未收口」）按证据取后者并在索引改齐；D-565 ④ 欠的那条跨节对账尺**仍欠着**。

'''

R566_EXTRA = '''  (h) **639 的口径归用户之后才动 `HINT_CONTRAST`**：runner 那一朵红本轮**故意留着**（`41568418335↔c567879` STEP[15]+[17]，light 3.84:1，`CAPTURE_GATE_CASES failed=1 有名字的红=1`）⇒ 不许为消红降 4.5、改期望、加豁免，也不许自己按名义口径改产品颜色（撞第 12 面）。到数要读的是：这一格在含补正笔的那跑里走的是哪条（判到 / 仍红 3.84 / 红在别的档）。
  (i) **640 的帧漂移**：现读 `FRAME_BASELINE_COMPARED=356 CHANGED=138 not-updated`（`/tmp/r565-补-compare.log`、`-compare3.log`；两次连拍逐字节相同 ⇒ 不是捕获随机）。R566 若重拍到**同一批 138**，说明状态还变着 ⇒ 先分辨再决定动不动基线，**不许拿 update 当收尾**；若拍到 0，就把那条"渲染状态漂移"具名结案。
'''

# ---------------- 应用 ----------------

# 1) UI_AUDIT
n = 'AGENT_UI_AUDIT.md'
t = rd(n)
guard(t, '**U-2446：补段 A', 'ui')
t = once(t, '## 第 564 轮（R565 · 2026-11-03 · U-2439…U-2445）',
         '## 第 564 轮（R565 · 2026-11-03 · U-2439…U-2450）', 'ui-heading')
t = once(t, '\n## 第 563 轮（R564', fill(UI) + '\n## 第 563 轮（R564', 'ui-insert')
if not check:
    wr(n, t)

# 2) ITERATION
n = 'AGENT_VISUAL_ITERATION.md'
t = rd(n)
guard(t, '**补段（同一轮 R565 的第 ⓪/A/C/B 续段', 'iteration')
# 位置式插入：`**七维度自评**` 这一行在文件里有 221 处（每轮一节），只能按 Round 562 那一节定位。
head = t.index('## Round 562 · R565')
pos = t.index('**七维度自评**', head)
if t[:pos].count('## Round 562 · R565') != 1:
    sys.stderr.write('ANCHOR_BAD iter-section\\n')
    sys.exit(1)
t = t[:pos] + fill(ITER) + t[pos:]
if not check:
    wr(n, t)

# 3) CHANGELOG
n = 'CHANGELOG.md'
t = rd(n)
guard(t, '### 会进 CI 的脚本第一次被一条守卫统一管住', 'changelog')
a = '## [Unreleased]\n\n'
t = once(t, a, a + fill(CHG), 'chg-insert')
if not check:
    wr(n, t)

# 4) DECISIONS
n = 'AGENT_DECISIONS.md'
t = rd(n)
guard(t, '⑤ **同族两种坏法收成一条守卫', 'decisions')
if not t.endswith('\n'):
    t += '\n'
t = t + fill(DEC)
if not check:
    wr(n, t)

# 5) FINAL_REPORT
n = 'AGENT_FINAL_REPORT.md'
t = rd(n)
guard(t, 'R565 补段（同一轮续写）', 'final-report')
t = once(t, '| 视觉台账 | U-31 … U-2445', '| 视觉台账 | U-31 … U-2450', 'fr-usource')
bullet_anchor = '全量 1406/57/0（619.4s）；build 0 告警；电池 709/5。\n'
t = once(t, bullet_anchor, bullet_anchor + fill(
    '- **R565 补段（同一轮续写，未收口：4 笔未推 + 本段的台账笔）**：真实推进落在仪器 —— '
    '绝对根**扫干净**（9 行 / 4 个文件逐位给去处，扫描器自己的模式从真人用户名改判形状）、'
    '同族两种坏法收成一条 `ci_channel_hygiene.py`（三格、电池 9 条、刀 M1470-M1473 全 CAUGHT），'
    '`HINT_CONTRAST` 的 runner 红用一次性探针排掉"倍率"（1x 代理 9.29:1 vs 旧值 3.15:1）后落在'
    '**渲染 vs 名义**两种口径（开 639，红原样留着、不降地板不藏红），帧基线在 0 产品文件的段落里漂了 '
    '138/356 ⇒ **不 update** 并用两臂把自己排除（开 640）；换装具名跳过。'
    '判据卷 %s；全量 %s；build 0 告警；电池 %s。\n' % (NUM['CAPTURE'], NUM['FULL'], NUM['BATTERY'])),
    'fr-bullet')
if not check:
    wr(n, t)

# 6) STATE
n = 'AGENT_STATE.md'
t = rd(n)
guard(t, '⑪ **补段（监工发令', 'state')
anchor = '## R565 ⓪ 开工（2026-11-03'
t = once(t, anchor, fill(STATE_CELL) + anchor, 'state-cell11')
# (g) 那一格在补记 ③ 里只出现一次（`- 仍挂着、永不重开` 有 3 处，不能当锚），按整行定位后插到它后面。
lines = t.split('\n')
gi = [i for i, ln in enumerate(lines) if ln.startswith('  (g) **分批 push 有没有造出')]
if len(gi) != 1:
    sys.stderr.write('ANCHOR_BAD state-(g) 命中=%d\n' % len(gi))
    sys.exit(1)
lines.insert(gi[0] + 1, fill(R566_EXTRA).rstrip('\n'))
t = '\n'.join(lines)
t = once(t, '刀号现读最高 **M1469**（M1466-M1469 四把都已登记且 CAUGHT；',
         '刀号现读最高 **M1473**（M1466-M1473 七把都已登记且 CAUGHT；', 'state-knife-number')
t = once(t, 'R566 从 **M1470** 起）', 'R566 从 **M1474** 起）', 'state-knife-next')
if not check:
    wr(n, t)

print('LEDGERS_R565_B books=6 check=%d' % (1 if check else 0))

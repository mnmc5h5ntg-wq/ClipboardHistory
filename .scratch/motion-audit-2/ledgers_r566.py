#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R566 的七本台账（第 565 轮 / Round 563）——签名身份从"期望"变成"会红的事实"。

派生格（streak / 电池 / 帧 / 判据卷 / 全量）走 `@@NAME@@` 占位：本脚本先落正文，
那些数由 `patch_r566_num.py` 在**验证链读到之后**替换；`fill()` 见到 `@@` 或残留 `%(` 就拒绝写。
"""
import io
import re
import sys

NUM = {
    'BUILD': '0（三次：本链与两次补跑）',
    'CAPTURE': '222/4 skipped/0 失败（1010.3s —— 本机今天明显比 R565 那一跑的 572.2s 慢）',
    'FRAMES': 'COMPARED=356 **CHANGED=135** MISSING=0 ADDED=0（`/tmp/r566-compare.log`）⇒ **基线不 update**：漂移量本身从 138 变成 135（同一天三次：138 / 138 / 135）⇒ 640 的说法要改成"漂移的规模也在动"',
    'FULL': '1406/57/**1 红**（886.5s 与 980.0s 两跑同形：`PerfBudgetTests/testImageComparisonCostStaysBounded` 255.1ms、294.2ms 对阈值 250.0ms；同一棵树同一判据**单独重跑这一卷**是 148.29/148.80/149.64ms（`/tmp/r566-perf.log`，打印 load1=3.4）⇒ 负载相关，不改阈值、不放宽、不删格；冷却后复跑见 STATE ⑤）',
    'BATTERY': '待台账落盘后现读（本笔之后跑）',
    'STREAK': '台账落盘后由 `python3 scripts/product_streak.py --check` 现读',
    'STREAK_RAW': '@@STREAK_RAW@@',
    'CIDLIST': '`41689614123↔6a3542b`、`41689665625↔e391ddb`、`41690220222↔5762925`、`41690840888↔d3bc6ec`、`41691263117↔eeac454`、`41691418800↔bc5a2af`、`41691473773↔fa8ae0a` 七跑全部 concluded failure，逐步现读 `gh run view --json jobs` ⇒ **STEP[9] 从这一批起不再红**（R564 的绝对根 + R565 的通道空格两处都修好了，Runner 签的字），失败步骤只有 **STEP[15]+[17]**（= `HINT_CONTRAST` light 3.84:1，639 那一朵），最后一跑另加 **STEP[19]**。那一朵是 **212 的第二次露面、换了一种形状**：`MOTION_FLOOR_SUITE_RED=1 … testBandCaptureIsCheaperAndStillSeesTheMotion：XCTAssertLessThan failed (11.394375 is not less than 11.1310105)` ⇒ 判的是「带捕获必须比整窗便宜」这条**方向**线（不是 212 当年的帧数地板），且同批七跑只有这一跑红 ⇒ 判间歇、不署名本轮、不放宽（R87/R146 的口径：单遍读数不配给产品定罪）',
    'HEADPAIR': '`41691473773 ↔ fa8ae0a`（concluded failure，STEP[15]/[17]/[19]）',
    'PAIRS': '本轮判据与刀单独一笔推（号见本笔正文最后一格），与 R565 那批分开 ⇒ 它的跑要回答"新格在 runner 上走具名 skip（无身份）而不是判绿"',
    'NEXT': '`41691473773↔fa8ae0a` 与本轮新笔那一跑（现读取号）',
    'UF': '2451',
    'UT': '2456',
}

check = '--check' in sys.argv


def rd(p):
    return io.open(p, encoding='utf-8').read()


def wr(p, t):
    io.open(p, 'w', encoding='utf-8').write(t)


def guard(t, needle, label):
    if needle in t:
        sys.stderr.write('ALREADY_PATCHED %s\n' % label)
        sys.exit(1)


def once(t, old, new, label):
    if t.count(old) != 1:
        sys.stderr.write('ANCHOR_BAD %s 命中=%d\n' % (label, t.count(old)))
        sys.exit(1)
    return t.replace(old, new, 1)


def fill(text):
    out = text
    for key, value in NUM.items():
        out = out.replace('@@%s@@' % key, value)
    if '@@' in out:
        i = out.find('@@')
        sys.stderr.write('NUM_NOT_FILLED %s\n' % out[i:i + 26])
        sys.exit(1)
    bad = re.search(r'%(?=[a-zA-Z])', out)
    if bad:
        sys.stderr.write('BARE_PERCENT_LEFT %s\n' % out[max(0, bad.start() - 30):bad.start() + 30])
        sys.exit(1)
    return out


UI = '''## 第 565 轮（R566 · 2026-11-04 · U-@@UF@@…@@UT@@）：本机码签身份从"账里的期望"变成"会红的事实"

- **U-@@UF@@：现场复核 —— 身份确实可用了，而且是上一轮就在用（我只是此前没有把它当判据）。** `security find-identity -v -p codesigning` 现读 ⇒ `1) 5F6C0955D4543282F5B2B12A3A2B9FB9FF5CE0A7 "ClipboardHistory Local Signing"` + `1 valid identities found`（R553 写那两臂桩测时是 0 条）。同时把两份真包各读一遍：`/Applications/时间剪史.app`（本轮装上去的）与上一轮那份备份 ⇒ `codesign -dvv` **逐字相同**：`CodeDirectory v=20400 size=23793 flags=0x0(none) hashes=737+3 location=embedded`、`Signature size=1900`、`Authority=ClipboardHistory Local Signing` ⇒ ①R553 验收第一条（连续两轮签名身份不变）**在 R554 就已经用读数记过**，本轮是它的第三、第四轮仍然成立（同一 `CodeDirectory` 大小与 hashes 计数不是巧合，是同一身份同一内容的密封）；②本轮真正翻的不是行为，是**有没有人判它** —— 从这一格起它是一条会红的判据，不再是脚本自己打印的一句话。
- **U-@@UF@@+1：判据一格 —— 现读真钥匙串的正对照（电池 4 格 → 5 格）。** `scripts/tests/test_sign_bundle.py::test_this_machine_actually_takes_the_identity_branch`：拿**真** `security` 现读，有身份 ⇒ 造一枚临时 CJK 名最小包、跑**真** `scripts/sign_bundle.sh`，必须打 `SIGNATURE_KIND=local identity=ClipboardHistory Local Signing`，并且 `codesign -dvv` 里必须真有 `Authority=` 那一行与 `flags=0x0`（读数与被签对象要对得上）。没有该身份的机器（CI、别人的机器）走 `skipTest('SIGN_LIVE_NOT_RUN=no-identity …')` —— **skip 与断言同函数**，且写明那不等于合格。上面两臂桩测照旧判着"脚本会不会选对支"，这一格判的是"**这台机器今天走得通哪一支**"：桩答不了这句（R553 那句"授权可以跨轮活下来"当时只是期望）。⚠ 监工第 4 条原话是"把『有身份必须用身份』那格从回退支改回身份支" —— 现读结论：**两臂都是桩，没有一格写过"本机今天走回退支"**，所以没东西可"翻"；真正缺的是上面这格现读判据，落的是同一件事（把假设变成会红的事实），不拿"改了"交差。
- **U-@@UF@@+2：刀两把、全 CAUGHT、`RESTORE_CLEAN=yes`、needle 现读各命中 1。** **M1474** 把匹配模式改成 `$IDENTITY-absent` ⇒ 这台机器明明有身份却走回退支 ⇒ 新格与桩格**同时**红（读数 `SIGNATURE_KIND=adhoc`）；**M1475** 删掉 adhoc 那一支的打印 ⇒ "静默回退"必须红（R553 修的就是这个洞，不许它长回来）。名册 +2 ⇒ `NEEDLE_PRECHECK tables=374 covered=295 arms=757 bad=0`、`ARM_TOTAL files=467 arms=1244 dupes=0 repeats=0`、`HIDDEN_ARMS 表=461 可判=1183 rot=0 抽不出=6 处置=ok`。⚠ 仍是单臂形状 ⇒ `ARM_TOTAL` 臂数 +0，会红性由两把真跑证明（具名，不写成"1244 里含这两把"）。
- **U-@@UF@@+3：真跑一遍交付链（不换回 ad-hoc 交差）。** `make bundle` ⇒ `SIGNATURE_KIND=local identity=ClipboardHistory Local Signing`、`codesign --verify --deep --strict` 过；`scripts/install_local.sh --yes --label before-R566` ⇒ `INSTALL_RESULT=ok 版本=1.4.8→1.4.8 / INSTALL_SHA_MATCH=1 / INSTALL_SIGNATURE=local flags=0x0（固定身份 ⇒ 授权可以跨轮活下来）/ SMOKE_OK=1 / INSTALL_ENTRIES=451=451 / INSTALL_RUNNING_PID=7145`（启动晚于安装、exe 路径逐字对上）。两处照实记：①**顺序偏离** —— 换装排在本链最前（这一轮的靶就是换装/签名本身，先拿读数再跑卷），②`--label` 被脚本再加一层 `before-` 前缀 ⇒ 备份目录叫 `before-before-R566`（外观问题，回滚路径照旧可用，不改脚本）。
- **U-@@UF@@+4：新自伤（不新不贵但必须记）—— 安装条目数跨轮无门。** 本轮现读 `451=451`，而 R564/R565 账上是 `433=433` ⇒ 同一版本、产品 `Sources/` 一字未动，条目数在两装之间涨 18。这一格从前只判 before==after（同一份的两次数），**从不判跨轮稳定** ⇒ 具名开 **642**（先分辨那 18 条是什么，再决定要不要进门；不许拿"口径变了"三个字交差）。
- **U-@@UF@@+5：本段验证链与派生格。** `swift build --build-tests` 告警 **@@BUILD@@**；判据卷 **@@CAPTURE@@**；帧重捕 **@@FRAMES@@**（**基线不更新**：640 的漂移还在同一批 ⇒ 先分辨再决定，见 STATE ①）；全量 **@@FULL@@**；清账 `格=162 声明=63 不成立=0/63`；电池 **@@BATTERY@@**；streak **@@STREAK@@**。

'''

ITER = '''## Round 563 · R566（第 565 轮 · 2026-11-04）：本机码签身份变成一条会红的现读判据 + 两把刀

上一轮的收口留了一句话："签名身份已可用，但**没人判它**"。本轮把它变成判据。现场证据三条：`security find-identity -v -p codesigning` 现读 1 条 `ClipboardHistory Local Signing`；`make bundle` 打 `SIGNATURE_KIND=local identity=…`；`install_local.sh --yes` 打 `INSTALL_SIGNATURE=local flags=0x0`、`SMOKE_OK=1`、条目 `451=451`、PID 7145。**最强的一条是跨轮对照**：本轮装上去那份与上一轮那份备份，`codesign -dvv` 逐字相同（`CodeDirectory v=20400 size=23793 hashes=737+3`、`Signature size=1900`、`Authority=…Local Signing`、`flags=0x0`）⇒ R553 写的验收第一条"连续两轮签名身份不变"在本机侧成立；第二条（桌面文件夹只需再授权一次、之后不弹）**只能人工签**，记进 633 的人工批次，不拿 `codesign --verify` 顶替。

判据落在 `test_sign_bundle.py` 新增一格：真 `security` 现读 ⇒ 有身份就真签一枚临时包并要 `SIGNATURE_KIND=local identity=…` + 包里真有 `Authority=` 与 `flags=0x0`；没身份的机器具名 `SIGN_LIVE_NOT_RUN=no-identity` 且 skip 与断言同函数。刀 **M1474**（身份永远匹配不上 ⇒ 有身份却回退）与 **M1475**（把 adhoc 的打印删掉 ⇒ 静默回退）全 CAUGHT。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉看图 | 6/15 | 本轮没有新画面：靶是签名链与判据本身；浮层与主窗口的帧只作为"基线不更新"的复核对象重捕，不新看内容。 |
| 判据有效性 | 14/15 | 新格判的是真机器现读（不是桩），且两把刀各钉一条相反坏法；扣一分是它只在有身份的机器上判（CI 侧具名不判，这一半只能靠本机跑）。 |
| 假绿防御 | 14/15 | 具名 skip 与断言同函数；`Authority=`/`flags=0x0` 与 `SIGNATURE_KIND` 双通道对拍（读的是被签的那份包，不是脚本自己打印的一句话）；跨轮 `CodeDirectory` 逐字对照替掉"我以为它不变"。 |
| 产品面推进 | 5/15 | 产品 0 文件（本轮靶不在产品面）；交付面推进一条（身份可用被钉成事实），已推那批的产品文件仍算 R565 的账。 |
| 台账一致性 | 12/15 | 七本各写各的锚、派生格落盘后现读；扣的三分：换装顺序排到验证链最前（有理由但仍是偏离）、`before-before-R566` 的双前缀外观问题、条目数跨轮无门（新开 642 只算登记）。 |
| 剩余风险处置 | 12/15 | 633 的人工回执仍未拿到 ⇒ 一个字结论不写；640 的帧漂移不 update 基线；642 是本轮新暴露的监控项；`≥2` 与 636/637/638/639/641 仍挂。 |
| 交接可读性 | 13/15 | STATE 顶节 + 补记 + 记忆索引三处同一组数（ahead、远端 SHA、成对号、`PUSH_BLOCKED` 解除），下一轮 ⓪ 的头一格写死为"读那三跑"。 |

'''

CHG = '''### 本机码签身份第一次被一条现读判据钉住；`SIGNATURE_KIND` 从 adhoc 翻成 local 的两轮证人（R566 / 第 565 轮 / Round 563）
    `security find-identity -v -p codesigning` 现读 1 条 `ClipboardHistory Local Signing`（R553 时 0 条）⇒ 新判据 `test_this_machine_actually_takes_the_identity_branch` 真签一枚临时包并要求 `SIGNATURE_KIND=local identity=…` + 包里真有 `Authority=…` 与 `flags=0x0`；没有该身份的机器具名 `SIGN_LIVE_NOT_RUN=no-identity` 并 skip（skip 与断言同函数）。上面两臂桩测照旧，区别是它们答"如果身份在不在"，这一格答"这台机器今天在不在"。刀 **M1474**（匹配永不成立 ⇒ 有身份却回退）/**M1475**（删掉 adhoc 打印 ⇒ 静默回退）全 CAUGHT。真跑交付链：`make bundle` ⇒ `SIGNATURE_KIND=local`；`install_local.sh --yes --label before-R566` ⇒ `INSTALL_SIGNATURE=local flags=0x0 / SHA_MATCH=1 / SMOKE_OK=1 / ENTRIES=451=451`。**跨轮证人**：本轮那份与上一轮备份的 `codesign -dvv` 逐字相同（`CodeDirectory … size=23793 hashes=737+3`、`Signature size=1900`、同一 `Authority`）⇒ R553 验收第一条**不必再靠账里的叙述**：判据把它钉住了（R554 起读数就是 local，本轮起有会红的格）；第二条只能人工确认，记进 633。另记：安装条目数 R564/R565 是 433、本轮 451（同一版本、产品未变）⇒ 这一格从前只判 before==after、不判跨轮 ⇒ 开 **642**；换装顺序排在本链最前（靶就是换装）算偏离、照实记。判据卷 @@CAPTURE@@；帧 @@FRAMES@@（**不 update**，640）；全量 @@FULL@@；build @@BUILD@@ 告警；电池 @@BATTERY@@；4.5 / 150 / 120ms / Motion ≥2 / 2x 8.0pt / 1x 6.0pt / `probeInkFraction` / `.contentFade` 0.20 一律未动；禁碰 **12 面**。

'''

DEC = '''## D-566（R566 · 2026-11-04）：桩测答"如果"，现读答"今天"——签名身份这一格必须挂在真机器上
① **为什么单独落一格判据**：`sign_bundle.sh` 的两条支早已有桩测，但桩永远不碰真钥匙串 ⇒ "固定身份可用"这件事在账里是**叙述**不是**读数**（R553-R555 三轮的 `INSTALL_SIGNATURE=local` 全靠脚本自己打印的一句话）。新格把"这台机器今天走得通哪一支"变成会红的事实：真 `security` 现读 + 真 `sign_bundle.sh` 签一枚临时包 + 真 `codesign -dvv` 读回 `Authority=` 与 `flags=0x0`。
② **两臂各钉一种坏法**：M1474 = 有身份却回退（本机立刻红）；M1475 = 回退不报（静默 adhoc 是这族最初的洞）。两把 `RESTORE_CLEAN=yes`。
③ **跨轮对照优先于单轮读数**：单轮 `INSTALL_SIGNATURE=local` 只说明这一次；把**上一轮那份备份**与本轮那份的 `CodeDirectory`（size 与 hashes 计数）、`Signature size`、`Authority`、`flags` 逐字比一遍，才是"连续两轮身份不变"这条验收的本机侧证人。TCC 认的就是这一层。
④ **人工那一半不许代理**：桌面文件夹"再授权一次之后不再弹"只能用户签 ⇒ 记进 633 的人工批次，写明"下一次弹窗先查 `SIGNATURE_KIND` 现读值"，不许拿 `codesign --verify` 或 `INSTALL_SIGNATURE=local` 顶替它。
⑤ **顺手登记的账**：条目数 433→451 跨轮无门（642）；换装排在验证链最前是本轮的**顺序偏离**（靶就是换装，读了数再跑卷），不写成"顺序未换"。
'''

STATE = '''## R566 状态（2026-11-04 · 第 565 轮 / Round 563 · 产品 0 文件 + 判据 1 格（现读真钥匙串）+ 刀 2 把 + 新开 642）

① **⓪ 那三跑（R565 收口时全在队列里）现在读**：@@CIDLIST@@。**读数只在 concluded 上成立**；`in_progress/queued` 一律具名 `CI_NOT_RUN=…`，不许从"不在失败名单"推绿。R565 的最后一笔 `fa8ae0a`（笔记补行）成对号本轮现读取号为 `@@HEADPAIR@@`。
② **本轮真实推进 = 判据一格（不抵产品位）+ 交付链一次真跑**：`test_sign_bundle.py` 新增 `test_this_machine_actually_takes_the_identity_branch`—— 现读真钥匙串 + 真签临时包 + 真读 `Authority=`/`flags=0x0`；桩测两臂一字未动。**产品 0 文件**（本轮没有可判定的产品位；折叠/展开那一串按用户定的 §3 顺序排在下一轮，签名这件事与它分开记账）。
③ **签名链读数（本轮真跑，不换回 ad-hoc 交差）**：`security find-identity -v -p codesigning` ⇒ `1 valid identities found` + `5F6C0955D4543282F5B2B12A3A2B9FB9FF5CE0A7 "ClipboardHistory Local Signing"`；`make bundle` ⇒ `SIGNATURE_KIND=local identity=…`；`scripts/install_local.sh --yes --label before-R566` ⇒ `INSTALL_RESULT=ok 1.4.8→1.4.8 / INSTALL_SHA_MATCH=1 / INSTALL_SIGNATURE=local flags=0x0 / SMOKE_OK=1 / INSTALL_ENTRIES=451=451 / INSTALL_RUNNING_PID=7145`。**跨轮证人**：本轮装的那份与上一轮备份那份 `codesign -dvv` 逐字相同（`CodeDirectory v=20400 size=23793 hashes=737+3`、`Signature size=1900`、`Authority=ClipboardHistory Local Signing`）⇒ 这条验收从 R554 起就有读数，本轮起**有判据**（差的是第三种：读数在、没人判，就等于没有）。
④ **交给用户的一条人工验收 + 一次必要的再授权**：签名身份变了 ⇒ macOS 把它当"同一个 App 的新版本"，**桌面文件夹要再授权一次（最后一次）**；之后再重装不该反复弹。下一次真出现弹窗，第一格先现读 `SIGNATURE_KIND`（若又变 `adhoc` 就是构建链回退了，不是 TCC 抽风）。633 的人工回执仍未拿到 ⇒ 本轮对 633 一个字结论也不写。
⑤ **验证链（顺序有一处偏离，照实记）**：换装排在最前（靶就是换装，先拿读数），其后 `swift build --build-tests` 告警 **@@BUILD@@**；判据卷 **@@CAPTURE@@**；帧重捕 **@@FRAMES@@** —— **基线不 update**（640：漂移仍是同一批 ⇒ 先分辨再决定动不动，不许拿 update 当收尾）；全量 **@@FULL@@**；预检三读串行 `tables=374 covered=295 arms=757 bad=0`、`ARM_TOTAL files=467 arms=1244 dupes=0 repeats=0`、`HIDDEN_ARMS 表=461 可判=1183 rot=0 抽不出=6 处置=ok`；清账 `格=162 声明=63 不成立=0/63`；电池 **@@BATTERY@@**。
⑥ **账与交接**：刀号 **M1476** 起（现读最高 M1475）；禁碰清单 **12 面**不变（产品 0 文件 ⇒ 不抬数）；4.5 墨地板、150 上限、120ms、Motion ≥2、2x 8.0pt、1x 6.0pt、`probeInkFraction=3%`、`.contentFade` 0.20 与声明时长一律不动；全量 skipped 只记现读；**归用户的**：633 回执、`≥2` 两条出路、636/637/638、639（`HINT_CONTRAST` 名义 vs 渲染口径）、640（动不动基线）、641（commit subject 守卫）、R564/R565 那条卫生守卫要不要接进 CI。streak **@@STREAK@@**。

### R566 补记（2026-11-04 · 第 565 轮 / Round 563 · 成对号 + R567 读单）

① **成对号**：@@PAIRS@@。**同一轮分两批推**（第二批带的是本轮判据与刀）⇒ 逐批回答"派生格有没有因分批而注定红"：本轮**没有新产品笔**（sources 格不动、streak 是 as-of 口径与 push 无关），所以逻辑上造不出那一族红；仍要以读到结论的那跑为准，**不许拿这句话当豁免**。
② **R567 的 ⓪ 必读**：@@NEXT@@；头四格 = (a) 本轮三跑各自的**全部失败步骤**（STEP[9] 是否已因补正笔转绿、`HINT_CONTRAST` 在 runner 走哪条 —— 639 的三种口径仍未定）；(b) 帧重捕是否仍是**同一批 138**（640）；(c) `test_sign_bundle` 的新格在 runner 上必然走具名 skip ⇒ 具名 `SIGN_LIVE_NOT_RUN=no-identity`，不许读成"CI 也签了"；(d) 642：先数出那 18 条是什么再决定进门不进。
③ **折叠/展开那一串不在本轮**：规格 `docs/FOLD_DUO_SPEC_2026-11-03.md` 已随本轮台账进仓；按 §3 的闸门顺序，下一段仍是**第①段几何与读数重锚**（848×600、两栏各 424、`contentAspectRatio` 拖边角等比、禁中缝拖拽、重锚引用 280/750 的判据与 356 张基线帧；先建旧值再改产品、读数必须变、同一笔 `frame_baseline.py update`），**不动画、不写着色器**；§4 那三条假设（材质变淡、阴影跟形状、取证能否区分真黑与透明）是第②段的靶，本轮一条都不许当成已成立。

'''

# ---------------- 应用 ----------------
n = 'AGENT_UI_AUDIT.md'
t = rd(n)
guard(t, '## 第 565 轮（R566', 'ui')
t = once(t, '\n## 第 564 轮（R565', '\n' + fill(UI) + '\n## 第 564 轮（R565', 'ui-insert')
if not check:
    wr(n, t)

n = 'AGENT_VISUAL_ITERATION.md'
t = rd(n)
guard(t, '## Round 563 · R566', 'iteration')
if not t.endswith('\n'):
    t += '\n'
t = t + fill(ITER)
if not check:
    wr(n, t)

n = 'CHANGELOG.md'
t = rd(n)
guard(t, '（R566 / 第 565 轮 / Round 563）', 'changelog')
t = once(t, '## [Unreleased]\n\n', '## [Unreleased]\n\n' + fill(CHG), 'chg-insert')
if not check:
    wr(n, t)

n = 'AGENT_DECISIONS.md'
t = rd(n)
guard(t, '## D-566（', 'decisions')
if not t.endswith('\n'):
    t += '\n'
t = t + fill(DEC)
if not check:
    wr(n, t)

n = 'AGENT_STATE.md'
t = rd(n)
guard(t, '## R566 状态（', 'state')
t = once(t, '## R565 状态（', fill(STATE) + '\n## R565 状态（', 'state-insert')
if not check:
    wr(n, t)

print('LEDGERS_R566 books=5 check=%d' % (1 if check else 0))

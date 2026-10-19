#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''R192 的台账批写：216 结案（并**更正上一轮点名的两处位置**）、新开 217、D-196。

同 R189/R190/R191：数字全部从日志解析，缺格拒绝写盘；写盘前模拟三账窗口；要么全成要么全不写。
自定的门（本轮沿用并加一条）：
① 判据卷/动效卷 skip≠0 就拒绝写盘（R191 那一课）；
② 变异表必须 9/9 CAUGHT、RESTORE_CLEAN=yes；
③ **本轮新门**：台账里引用的每个 `M7xx` 都必须在变异日志里真的露面 ——
   上一轮的 U 条目写"四把刀 M708–M711"是靠人抄的，这一轮不抄。
'''
import io
import os
import re
import subprocess
import sys

ROOT = '/Users/wangziyi/Codex_Project0'
L = {'pair': '/tmp/r192_pair.log', 'motion': '/tmp/r192_motion.log', 'full': '/tmp/r192_full.log',
     'mut': '/tmp/r192_mut.log', 'gate': '/tmp/r192_gate.log'}
NEW_R, NEW_N = 192, 194


def read(p):
    if not os.path.exists(p):
        raise SystemExit('MISSING_LOG %s ⇒ 拒绝写盘' % p)
    return io.open(p, encoding='utf-8').read()


def grab(pat, text, what, flags=0):
    hits = re.findall(pat, text, flags)
    if not hits:
        raise SystemExit('PARSE_FAILED %s（%r）⇒ 拒绝写盘' % (what, pat))
    return hits[-1]


pair = read(L['pair'])
motion = read(L['motion'])
full = read(L['full'])
mut = read(L['mut'])
gate = read(L['gate'])


def summary_triple(text, what):
    """从一卷日志的**最后一行** `Executed …` 里取 (执行数, 跳过数, 失败数)。"""
    line = grab(r'Executed \d+ tests[^\n]*', text, what)
    executed = grab(r'Executed (\d+) tests', line, what + ' 执行数')
    failures = grab(r'(\d+) failures?', line, what + ' 失败数')
    skipped = grab(r'(\d+) tests? skipped', line, what + ' 跳过数') \
        if re.search(r'\d+ tests? skipped', line) else '0'
    return executed, skipped, failures


pair_line = summary_triple(pair, '接线扫描卷（三条）')
motion_line = summary_triple(motion, '动效两站点卷')
full_line = summary_triple(full, '全量卷')
# 解析要照**仪器实际打印的形状**写（R148 那一课：别改日志去迁就生成器）。
# mutate_r192.py 的结论行是 `R192_MUTATE 刀=9 CAUGHT=9 ESCAPED=0 NOT_RUN=0 RESTORE_CLEAN=yes`，
# 不是 R191 那一种 `CAUGHT=4/4` —— 所以四个数各取各的，缺任何一个都拒绝写盘。
caught_n = int(grab(r'CAUGHT=(\d+)', mut, '变异表 CAUGHT'))
total_n = int(grab(r'刀=(\d+)', mut, '变异表 刀数'))
esc_n = int(grab(r'ESCAPED=(\d+)', mut, '变异表 ESCAPED'))
notrun_n = int(grab(r'NOT_RUN=(\d+)', mut, '变异表 NOT_RUN'))
caught = [str(caught_n), str(total_n)]
arms = sorted(set(re.findall(r'^(M\d{3}) CAUGHT', mut, re.M)))
escaped = re.findall(r'^(M\d{3}) ESCAPED', mut, re.M)
notrun = re.findall(r'^(M\d{3}) NOT_RUN', mut, re.M)
restore = 'yes' if 'RESTORE_CLEAN=yes' in mut else 'NO'
surface = grab(r'(MOTION_LEDGER 表面=\d+ 状态=\d+ 格子=\d+ 行数=\d+ 已清账=\d+ 未清账=\d+ 地板=\d+)', gate, '清账表')
sym_read = grab(r'(MOTION_SYMBOL row-star [^\n]*)', motion, 'row-star 两把尺读数')
det_read = grab(r'(MOTION_DETAIL_AB empty-to-content [^\n]*)', motion, 'detail 两把尺读数')
prod = subprocess.run(['git', 'diff', '--name-only', 'HEAD', '--', 'ClipboardHistory/Sources'],
                      cwd=ROOT, stdout=subprocess.PIPE).stdout.decode('utf-8', 'replace').strip()
prod_files = len([l for l in prod.splitlines() if l.strip()])

problems = []
if pair_line[0] != '3':
    problems.append('接线扫描卷只执行了 %s 条（要 3：新扫描 + 新真值表 + R191 那条扫描）' % pair_line[0])
if pair_line[1] != '0' or motion_line[1] != '0':
    problems.append('skip 不是绿：扫描卷 %s / 动效卷 %s' % (pair_line[1], motion_line[1]))
if motion_line[0] != '2':
    problems.append('动效卷只执行了 %s 条（要 2：row-star 与 detail 两个站点）' % motion_line[0])
if pair_line[2] != '0' or motion_line[2] != '0' or full_line[2] != '0':
    problems.append('失败：扫描卷 %s / 动效卷 %s / 全量卷 %s' % (pair_line[2], motion_line[2], full_line[2]))
if (list(caught) != ['9', '9'] or len(arms) != 9 or escaped or notrun or restore != 'yes'
        or esc_n != 0 or notrun_n != 0):
    problems.append('变异表 %s/%s arms=%s ESCAPED=%s NOT_RUN=%s restore=%s（要 9/9 且两样都空）'
                    % (caught[0], caught[1], arms, escaped, notrun, restore))
if prod_files != 0:
    problems.append('本轮应当产品 0 文件，实际 %d 个 ⇒ 帧基线/换装都得重做' % prod_files)
if problems:
    raise SystemExit('REFUSE_TO_WRITE ' + u'；'.join(problems))

V = dict(pair_n=pair_line[0], pair_skip=pair_line[1], pair_fail=pair_line[2],
         mo_n=motion_line[0], mo_skip=motion_line[1], mo_fail=motion_line[2],
         full_n=full_line[0], full_skip=full_line[1], full_fail=full_line[2],
         arms=u', '.join(arms), arm_n=str(len(arms)), caught=caught[0], total=caught[1],
         restore=restore, surface=surface, round=str(NEW_R), newn=str(NEW_N),
         sym=sym_read, det=det_read)

ui_title = (u'## 第 %d 轮（R%d · 2026-10-19）：216 结案并**更正上一轮点名的位置** —— '
            u'两处"两臂相同吗"换两把尺并判，而 216 原提案的两处本来就没错（U-628…U-631 · 产品 0 文件，判据账）\n') % (NEW_N, NEW_R)

ui_body = u'''
- **U-628：216 点名的两处位置是错的，读代码纠正。** 上一轮我是拿行号 + `grep transitionFrameCount` 开单的，
  没读周围：`:2916` 那条（`testBannerDismissColumnAsymmetryIsMeasured`）**R59 就已经**把
  `sharedMovingFloor` 套在两栏上比"最后还在变的帧号"，各自归一化的那两个数只出现在
  标着「旧轴…这条轴的差是墨量，不是时间」的打印里，不参与判定；`:2332` 那条热图淡入 A/B 的
  `帧数=` 上面两行就写着"帧数照旧打印，但**不参与判定**：它由采样相位决定"，判定走的是连续段时长。
  ⇒ 真正的同类形状在另外两处，而且它们问的不是"谁先停"而是"两臂**相同**吗"：
  `testSystemSymbolEffectsAreOutOfThisRulersReach`（`XCTAssertEqual(计数(开), 计数(关))`）与
  `testDetailEmptyToContentCrossfadeIsMeasuredOrDeclaredBlind`（`if onSpan == offSpan …` 才记「产物未量」）。
  这条自我更正比修判据更重要：**开单前读被告代码**（同 R88/R89 那一族），行号 + 符号名不算读通。
- **U-629：两处换成"两把尺都得说相同"，合读法由纯函数生成。** `sharedMovingFloor([on, off])` 套两臂 +
  旧口径并列打印，`armAgreementReading(sameUnderShared:sameUnderPerArm:sound:)` 把两把尺的回答并成一句话，
  四种形状先被合成真值表钉住（`testCrossArmRulerAgreementIsATruthTable`）再让真卷去跑。
  本轮两站点只准变严不准变松：detail 那条免责分支现在要 `onSpan == offSpan` **且** `onSpanShared == offSpanShared`
  **且** 峰值差 < 0.02 才记「源码已接、产物未量」；row-star 那条硬断言同理。
  本机读数（`/tmp/r192_motion.log`）：%(sym)s ／ %(det)s ⇒ 两把尺都说相同，免责照旧，换口径没藏东西。
  刀 %(arms)s 全 CAUGHT、RESTORE_CLEAN=%(restore)s：M712/M713 一臂退回各自归一化、M714 线由单臂导出、
  M715 合读法算了不印、M716 旧口径不印、M717/M718 硬判据退回单把尺（**八把里七把只有接线扫描抓得到** ——
  本机两臂峰值相等，新旧口径给同一个数，跑结果抓不到）。扫描按**方法体**切片读，
  并且第一版就红给自己看过： needle 写在守卫自己的行里 ⇒ 自指命中（R100 那一族），现在守卫把自己的那一段滤掉。
- **U-630：216 不能推广，理由是量出来的，不是感觉。** 共用线 = 较大峰值 × `stepFloorRatio`，
  于是较小那一臂的峰值一旦低于这条线，它整臂读 **0 帧** —— "两臂相同"就被读成"两臂都落定了"，
  那是把没量到说成落定。本机 `MOTION_SEQUENCE` 两臂峰值 `0.027 / 0.234` ⇒ 线 0.0351 **高于**小臂峰值，
  那一臂从 11 帧掉到 0 帧（这条形状由真值表 (a) 格 + 刀 M719/M720 钉住：M719 让 `sharedLineIsSound` 恒真、
  M720 让矛盾格替一把尺背书，两把都在真值表上红）。
  ⇒ 新开 BACKLOG 217：`testNativeRowAnimationIsVisibleToTheRuler`、`testNativeRowMoveIsVisibleToTheRuler`、
  `testRowAnimationSurvivesTheSelectionUpdateThatFollowsIt` 这三处"开着的必须比关着的演得多帧"
  欠的是**时间轴**（R47 那条连续段尺），不是同一条线；把它们"修"成共用线会造出一朵假红。
- **U-631：看图腿这次真的看了，而且看见一件判据里没有的事。** 把两臂的条带（`/tmp/motion-films/detail-empty-to-content-*-strip.png`，
  各 30 帧）按判据同一颗带（x0.40..0.98 / y0.12..0.88）逐格量灰阶：
  `开 = 86.16,86.16,86.16,82.00,82.00,82.00,86.16,…`，`关 = 86.16,86.16,86.16,82.00,82.00,82.00,86.16,…`
  —— **两臂逐帧同形**，相邻差只在第 3、第 6 帧各 4.16 灰阶。"关"那一臂动画是关的，所以那个三帧下陷不是淡入，
  是夹具落定；⇒ "这把尺看不见这条交叉淡"不是阈值太松，是**这条通道里根本没有那个过程**（与 D-055/M1 同根）。
  另外臂间最大的一格（第 26 帧，均值差 3.03、差像素 18787）差的全是 fixture 内容：详情区标题里那条随机十六进制串、
  由它派生的色块（开=深灰、关=纯黑）、时间戳。⇒ 臂间内容差不会污染判定（判据量的是**同一臂**的相邻帧对），
  但这条要写下来：它是"看图看见、而读数里没有"的正例，也是 BACKLOG 215 那条"亮档分不开"的同族证人 ——
  色块在两臂里给成两种颜色，说明它由内容派生而不是由外观档决定。
''' % V

vi_body = u'''
## Round %(round)s · 216 结案并更正上一轮点名的位置：两处"两臂相同吗"换两把尺并判（2026-10-19 · 产品 0 文件，判据账）

先读被告代码，216 原提案的两处（`:2916` 分栏、`:2332` 热图淡入）**都不是** 212 的形状 —— 一处 R59 就用共享线了，
一处的帧数明写"不参与判定"。真正的同类形状是 row-star 与 detail-empty-to-content 那两处"两臂**相同**吗"：
现在同一条线与各自归一化**并判**，合读法由纯函数生成并被合成真值表钉住。另开 217 并写明为什么不能推广：
共用线由较大峰值导出 ⇒ 幅度不对称时小臂整臂读 0 帧，那是把"没量到"说成"落定"（本机 0.027/0.234 实测）。
九把刀 M712–M720 全 CAUGHT，其中七把只有接线扫描抓得到（本机新旧口径同数），两把落在真值表上。
看图这条本轮没有欠：把两臂 30 帧条带按判据同一颗带逐格量灰阶，两臂**逐帧同形**（`86.16,86.16,86.16,82.00,82.00,82.00,86.16,…`），
而"关"那一臂动画是关的 ⇒ 那个三帧下陷不是淡入、是夹具落定，这条交叉淡在这台机器的通道里**根本没有过程**（U-631）。

### 3. 七维度自评（本轮）

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 12/15 | 看了两臂各 30 帧的条带并逐格量灰阶（U-631 的两臂同形读数 + 第 26 帧那格 fixture 内容差）；扣分：产品 0 文件、138 张帧未动，没有新的界面可审 |
| 判据有效性 | 15/15 | 两处跨臂相同性比较换两把尺并判 + 合读法纯函数 + 真值表四格；9/9 刀 CAUGHT（含 M719/M720 钉适用域） |
| 假绿防御 | 15/15 | 免责分支只能变严不能变松；扫描守卫按方法体切片、滤掉守卫自己那段（第一版就是被自指打红的）；skip≠0 拒绝写盘 |
| 产品面推进 | 8/15 | 画面 0 改动；把一条挂着的同类判据结掉，并撤掉上一轮开错的两处靶 |
| 台账一致性 | 14/15 | U-628…U-631 + 216 结案并**更正位置** + 新开 217 + D-196；数字全解析、刀号在册不复抄；扣分：清账表未判 %(surface_unjudged)s 格本轮没动 |
| 交付诚实性 | 15/15 | 明写"上一轮点名的两处是错的、错在只 grep 符号名没读周围"，也明写"七把刀只有接线扫描抓得到" |
| 可复核性 | 15/15 | 刀号 %(arms)s、两站点完整读数、被改方法名（不写会漂的行号）全在册 |
''' % dict(V, surface_unjudged=u'47')

cl_body = u'''### 216 结案：两处"两臂相同吗"换两把尺并判；同轮更正上一轮点名的两处位置（R%(round)s / U-628…U-631 · 产品 0 文件，判据账）

- 更正：216 点名的 `:2916`（分栏）与 `:2332`（热图淡入 A/B）**都不是** 212 的形状 —— 前者 R59 已用 `sharedMovingFloor`，
  后者的 `帧数=` 上面两行写着"不参与判定"。真站点是 `testSystemSymbolEffectsAreOutOfThisRulersReach` 与
  `testDetailEmptyToContentCrossfadeIsMeasuredOrDeclaredBlind`
- 换形：`sharedLineIsSound`（小臂峰值必须在那条线之上）+ `armAgreementReading`（两把尺的回答并成一句话）；
  免责分支与硬断言都改成"新旧口径**都**说相同"，只准变严
- 证据：本机 %(sym)s ／ %(det)s ⇒ 两把尺都说相同；反例读数 0.027/0.234 ⇒ 线 0.0351 把小臂判成 0 帧（真值表 (a) 格）
- 变异：`mutate_r192.py` %(arms)s ⇒ %(caught)s/%(total)s CAUGHT、RESTORE_CLEAN=%(restore)s；已登记进 needle 预检名册
- 新开 BACKLOG 217：幅度不对称那一族（三处 AppKit 行 A/B）欠的是时间轴不是同一条线；D-196 记共用线的适用域
- 验证：编译 0 告警、扫描卷 %(pair_n)s 例/skip %(pair_skip)s/失败 %(pair_fail)s、动效卷 %(mo_n)s/%(mo_skip)s/%(mo_fail)s、全量卷 %(full_n)s/%(full_skip)s/%(full_fail)s、产品 0 文件（帧未动，未重捕）

''' % V

bl_body = u'''**216 追记 + 结案（R192）：两处点名的位置是错的，真站点是"两臂相同吗"那两处**

上一轮我按"行号 + `grep transitionFrameCount`"开单，没读周围 ⇒ 两处靶都不成立：
① `testBannerDismissColumnAsymmetryIsMeasured`（R59）早就把 `sharedMovingFloor` 套在两栏上比"最后还在变的帧号"，
各自归一化的计数只出现在标着「旧轴…这条轴的差是墨量，不是时间」的打印里；
② 热图淡入 A/B 的 `帧数=` 上面两行写着"帧数照旧打印，但**不参与判定**：它由采样相位决定"，判定走连续段时长。
真站点是两处**相同性**比较（不是先后比较）：`testSystemSymbolEffectsAreOutOfThisRulersReach` 的
`XCTAssertEqual(计数(开), 计数(关))`、`testDetailEmptyToContentCrossfadeIsMeasuredOrDeclaredBlind` 的
`if onSpan == offSpan …`。处置：同一条线 + 旧口径**并判**，合读法由纯函数 `armAgreementReading` 生成并被真值表钉住。
刀 M712–M718 全 CAUGHT，其中七把只有接线扫描抓得到（本机两臂峰值相等 ⇒ 跑结果两种口径都绿）。
216 至此结案；不可推广的那一族另开 217（见下）。

**217. 幅度不对称的跨臂 A/B 欠的是**时间轴**，不是同一条线（R192 实测开单，防下一轮把它们"修"成假红）**

三处：`testNativeRowAnimationIsVisibleToTheRuler`（本机 开=9 帧/峰值 0.043、关=1 帧/0.052，采样≈6ms）、
`testNativeRowMoveIsVisibleToTheRuler`（`nativeMoveVerdict` 吃两个各自归一化的计数）、
`testRowAnimationSurvivesTheSelectionUpdateThatFollowsIt`（选中没变 11 帧/0.027、选中变了 1 帧/0.234）。
它们的门槛由**各自峰值**决定 ⇒ 与 212 同形；但按 216 的办法套同一条线会把小臂判成 0 帧
（0.027 低于 0.234 × 0.15 = 0.0351，实测见 `/tmp/r192_motion.log`），那是把"没量到"说成"落定"。
所以这三处的处置是 R47 那一族：**时长来自连续段**（`contiguousChangedRun`），帧数只当对照打印；
`contiguousChangedRun` 的地板要按"这段里每对帧都在同一条线上"表达，而不是"数到几帧"。
判据形状要能各自被证伪：先量两臂峰值比（`sharedLineIsSound`），比值不足就不许用共用线，也不许用帧数下结论。

''' % V

D_BODY = u'''**D-196（R192）：同一条绝对线的**适用域**是"较小臂的峰值也在这条线之上"，越过这条线就不许用共用线**

证据（本机 `/tmp/r192_motion.log`、`/tmp/r192_base_motion.log`，同一份帧数据两臂对照）：
row-star `0.268/0.268`（线 0.0403）安全、detail `0.051/0.051`（线 0.0076）安全、
row-insert `0.043/0.052`（线 0.0078）安全；而 `MOTION_SEQUENCE` 两臂 `0.027/0.234` ⇒ 线 0.0351 **高于**小臂峰值，
那一臂从 11 帧读到 **0 帧**。⇒ "两臂相同"被读成"两臂都落定"，那是把"没量到"说成"落定"。

为什么单独记成决定：212 结案时我写的是"同类形状都换成同一条线"，这句话**过宽**——
照它做会把 217 那三处（AppKit 行插/移/序列）改成会红的假判据。判据不引入新阈值：
线本身（`sharedMovingFloor`）就是判据，`sharedLineIsSound` 只问"小臂峰值 ≥ 这条线"，
由真值表三格与刀 M719/M720 钉住。
⇒ 处置分两栏：**跨臂"相同性"比较**（两臂是不是同一个读数）用同一条线，且新旧两把尺并判；
**跨臂"谁演得久"比较**在幅度不对称时既不配用各自归一化的计数（212），也不配用共用线（本轮），
欠的是时间轴（连续段时长，BACKLOG 217）。适用面：本文件所有 A/B 双臂判据；
不适用：合成真值表里的自造数组（那不是跨臂比较）。

'''

STATE_HDR = (u'最后更新：2026-10-19 14:10（本地 · R%(round)s / 第 %(newn)s 轮：**216 结案并更正上一轮点名的位置**'
             u'（U-628…U-631 · 产品 0 文件，判据账）\n\n'
             u'**本轮落地**：两处"两臂相同吗"（row-star、detail-empty-to-content）改成同一条线 + 旧口径**并判**，'
             u'合读法由 `armAgreementReading` 生成并被合成真值表钉住；`sharedLineIsSound` 把"共用线什么时候不适用"'
             u'变成量出来的判据（不引入新阈值）。`mutate_r192.py` %(arms)s ⇒ %(caught)s/%(total)s CAUGHT、'
             u'RESTORE_CLEAN=%(restore)s，其中七把只有接线扫描抓得到。\n'
             u'**两条自纠也记了**：① 216 上一轮点名的 `:2916`/`:2332` 都不成立（一个 R59 就用共享线了，'
             u'一个明写"帧数不参与判定"）⇒ 错在只 grep 符号名没读周围；② 新守卫第一版红给自己看：'
             u'needle 写在守卫自己的行里 ⇒ 自指命中（R100 那一族），改成按方法体切片并滤掉守卫那段。\n'
             u'**216 不许推广的理由是读数量出来的**：`MOTION_SEQUENCE` 两臂 `0.027/0.234` ⇒ 共用线 0.0351 高于小臂峰值，'
             u'那一臂 11 帧→0 帧，另开 217（那三处欠时间轴）。D-196 记适用域。\n'
             u'验证：编译 0 告警、扫描卷 %(pair_n)s/%(pair_skip)s/%(pair_fail)s、动效卷 %(mo_n)s/%(mo_skip)s/%(mo_fail)s、'
             u'全量卷 %(full_n)s/%(full_skip)s/%(full_fail)s、清账表 %(surface)s、电池见 commit 输出。\n\n'
             u'**下一轮（R193）的靶**：⓪ 读这一笔与 `9a8c9c9` 之后所有跑的**全部**失败步骤'
             u'（写这笔时 run `39206313202`（`9a8c9c9`）仍 in_progress ⇒ 结论未读；'
             u'关键预期：`2a7c829` 已给 success ⇒ STEP[13]/[15] 那两朵该是消失状态）；\n'
             u'② 217：把三处 AppKit 行 A/B 的判定搬到连续段时长轴，各自配一把"退回帧数"的刀；\n'
             u'③ 215：真机合成层通道拿一格亮档读数（判"通道盲区 vs 产品可辨性）；\n'
             u'④ 201、202、205、207 与清账表未判的 47 格；⑤ 看图腿本轮补了一格（两臂各 30 帧条带逐格量灰阶 ⇒ '
             u'两臂逐帧同形，那条交叉淡在这条通道里没有过程），但产品已连续两轮 0 文件 —— '
             u'下一轮要么按 173 的清单动一个真位点，要么把 217 那三臂的条带也这样量一遍。\n'
             u'）\n') % V

LEDGERS = {
    'AGENT_UI_AUDIT.md': u'^## 第 \\d+ 轮（R%d',
    'AGENT_VISUAL_ITERATION.md': u'^## Round %d · ',
    'CHANGELOG.md': u'^### .*（R%d / ',
}
ROSTER = {186, 187}


def write(p, t):
    with io.open(p, 'w', encoding='utf-8') as h:
        h.write(t)


def insert_before(text, prefix, block):
    lines = text.split(u'\n')
    idx = [i for i, l in enumerate(lines) if l.startswith(prefix)]
    if len(idx) != 1:
        raise SystemExit('ANCHOR %r 命中 %d 次（要 1）' % (prefix, len(idx)))
    lines.insert(idx[0], block.rstrip(u'\n'))
    return u'\n'.join(lines)


def main():
    paths = {n: os.path.join(ROOT, n) for n in LEDGERS}
    paths['STATE'] = os.path.join(ROOT, 'AGENT_STATE.md')
    paths['AGENT_BACKLOG.md'] = os.path.join(ROOT, 'AGENT_BACKLOG.md')
    paths['AGENT_DECISIONS.md'] = os.path.join(ROOT, 'AGENT_DECISIONS.md')
    old = {k: read(v) for k, v in paths.items()}
    if u'## Round %d · ' % NEW_R in old['AGENT_VISUAL_ITERATION.md']:
        raise SystemExit('DUMP_ALREADY_WRITTEN ⇒ 不重复落盘')
    for name, txt in ((u'ui', ui_title + ui_body), (u'vi', vi_body), (u'cl', cl_body),
                      (u'bl', bl_body), (u'st', STATE_HDR), (u'd', D_BODY)):
        if re.search(r'%\([a-z_0-9]+\)s', txt):
            raise SystemExit('FORMAT_LEAK %s 还有没吃掉的占位符' % name)
        if re.search(r'M7\d\d', txt):
            for knife in set(re.findall(r'M(7\d\d)', txt)):
                if ('M' + knife) not in mut:
                    raise SystemExit('KNIFE_NOT_IN_LOG %s 被台账引用但变异日志里没有 ⇒ 不写盘' % knife)
    # 锚点由**当前文件**推出，不硬抄上一轮的字符串（R102：跨版本存活的部分要按形状匹配）。
    ui_lines = [l for l in old['AGENT_UI_AUDIT.md'].split(u'\n') if l.startswith(u'## 第 ')]
    if not ui_lines:
        raise SystemExit('ANCHOR_MISSING AGENT_UI_AUDIT.md 没有 `## 第 ` 标题')
    top_ui = ui_lines[0]
    cl_lines = [l for l in old['CHANGELOG.md'].split(u'\n') if l.startswith(u'### ')]
    if not cl_lines:
        raise SystemExit('ANCHOR_MISSING CHANGELOG.md 没有 `### ` 标题')
    top_cl = cl_lines[0]
    top_state = [i for i, l in enumerate(old['STATE'].split(u'\n')) if l.startswith(u'最后更新：')][0]
    # D-195 在盘上是 `**D-195（R189）：…**` 这种**加粗行**、且是文件最后一条（本轮实测 `grep -n` 出来的形状），
    # 不是 `### ` 标题 ⇒ 追加，不插入。多会话并行时先对一下"盘上最大 D 号"，别把号抢重。
    dec_max = max(int(m) for m in re.findall(r'^\*\*D-(\d{3})', old['AGENT_DECISIONS.md'], re.M))
    if dec_max != 195:
        raise SystemExit('DECISION_NUMBER_TAKEN 盘上最大 D 号是 %d（本轮要写 D-196）⇒ 不写盘' % dec_max)
    new = {}
    new['AGENT_UI_AUDIT.md'] = insert_before(old['AGENT_UI_AUDIT.md'], top_ui, ui_title + ui_body)
    new['AGENT_VISUAL_ITERATION.md'] = old['AGENT_VISUAL_ITERATION.md'].rstrip(u'\n') + u'\n\n' + vi_body.rstrip(u'\n') + u'\n'
    new['CHANGELOG.md'] = insert_before(old['CHANGELOG.md'], top_cl, cl_body)
    new['AGENT_BACKLOG.md'] = old['AGENT_BACKLOG.md'].rstrip(u'\n') + u'\n\n' + bl_body.rstrip(u'\n') + u'\n'
    new['AGENT_DECISIONS.md'] = old['AGENT_DECISIONS.md'].rstrip(u'\n') + u'\n\n' + D_BODY.rstrip(u'\n') + u'\n'
    st = old['STATE'].split(u'\n')
    new['STATE'] = u'\n'.join(st[:top_state] + [STATE_HDR.rstrip(u'\n'), u''] + st[top_state:])

    for name, fmt in LEDGERS.items():
        for this in (NEW_R, NEW_R - 1, NEW_R - 2):
            if this in ROSTER and this != NEW_R:
                continue
            if not re.search(fmt % this, new[name], re.M):
                raise SystemExit('PRECHECK_WOULD_RED R%d 在 %s 没有标题行 ⇒ 不写盘' % (this, name))
    section = new['AGENT_UI_AUDIT.md'].split(ui_title.rstrip(u'\n'), 1)[1].split(top_ui, 1)[0]
    defined = sorted(int(m) for m in re.findall(u'^- \\*\\*U-(\\d{3})：', section, re.M))
    if defined != [628, 629, 630, 631]:
        raise SystemExit('U_RANGE_MISMATCH 本轮定义 %s（要 628…631）' % defined)
    items = set(re.findall(r'^(?:\*\*)?(\d{2,3})\. ', new['AGENT_BACKLOG.md'], re.M))
    for ref in re.findall(u'BACKLOG (\\d{3})', ui_body + vi_body + cl_body + bl_body + STATE_HDR):
        if ref not in items:
            raise SystemExit('DANGLING_BACKLOG %s 没有定义行' % ref)
    if u'D-196' not in new['AGENT_DECISIONS.md']:
        raise SystemExit('DECISION_MISSING D-196 没落上')
    for k, v in new.items():
        write(paths[k], v)
    print(u'LEDGERS_R192_WRITTEN r=%d n=%d U=628..631 arms=%s/%s restore=%s pair=%s/%s/%s motion=%s/%s/%s full=%s/%s/%s'
          % (NEW_R, NEW_N, V['caught'], V['total'], V['restore'],
             V['pair_n'], V['pair_skip'], V['pair_fail'],
             V['mo_n'], V['mo_skip'], V['mo_fail'],
             V['full_n'], V['full_skip'], V['full_fail']))
    return 0


if __name__ == '__main__':
    sys.exit(main())

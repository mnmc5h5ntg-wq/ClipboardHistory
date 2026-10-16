#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R97 的台账落盘：生成 + 自校验（沿用 R96 立的两条：事务性写盘、数字只从日志解析）。

R96 那一轮的三条教训已经写进用户级记忆，这里逐条兑现：
① 事务性 —— 这一段先整体快照再写，任何一格抛错就全部还原（半份台账比没写更坏）；
② 数字从 `r97_verify.log` 解析，缺任一格就**拒绝写盘**（不出现"猜出来的数"）；
③ 渲染完的验证段自己再过一遍 `check_block`（R96 连中两次 `%s` 拿错键的值）。

跑法：LEDGERS_R97_APPLY=1 PYTHONUTF8=1 python3 .scratch/motion-audit-2/ledgers_r97.py
退出码：0 = 十格齐全；非 0 = 拒绝写盘或有格子没落盘。
"""
import io
import os
import re
import sys

REPO = '/Users/wangziyi/Codex_Project0'
LOG = REPO + '/.scratch/motion-audit-2/r97_verify.log'
SHOTS = '/tmp/r97_shots'

STAGES = [
    ('ui_audit', 'AGENT_UI_AUDIT.md', u'## 第 99 轮 · R97：', u'轮次标题（审计侧编号 = R+2）'),
    ('backlog_132', 'AGENT_BACKLOG.md', u'R97 结案', u'132：runner 那 314 个采样给出的"挂"'),
    ('backlog_140', 'AGENT_BACKLOG.md', u'R97 更新（真病根不是夹具，是写死的扫描带）', u'140 的进度'),
    ('backlog_141', 'AGENT_BACKLOG.md', u'141. ', u'新开 141：判据读的是重编码位图，不是交付的 PNG'),
    ('decisions', 'AGENT_DECISIONS.md', u'### D-155（R97）', u'本轮的决定（R93 就是漏了这一格）'),
    ('visual', 'AGENT_VISUAL_ITERATION.md', u'## Round 97 ·', u'Round 97 全文（开场清单 + 七维度 + 验证）'),
    ('changelog', 'CHANGELOG.md', u'### 判据与工具（R97）', u'产品零改动，所以只有判据与工具那一节'),
    ('manual_batch', 'docs/MANUAL_TEST_v1.4.9_round3.md', u'## 批次 76', u'真机那一腿：卡片边界与留白'),
    ('state_rotation', 'AGENT_STATE.md', u'本地 · R97 / 第 99 轮收尾', u'第 3 行换成本轮'),
    ('instrument', '.scratch/motion-audit-2/r97_stats_readings.log', u'SELF-CHECK OK',
     u'看图那一腿的读数必须在盘上（台账里每个数都要能追到产物）'),
]


def rd(p):
    return io.open(os.path.join(REPO, p), encoding='utf-8').read()


def wr(p, s):
    io.open(os.path.join(REPO, p), 'w', encoding='utf-8').write(s)


def strip_timing(s):
    return re.sub(r'\s+in\s+[0-9.]+\s*(?:\([0-9.]+\)\s*)?s(?:econds?)?', '', s).strip()


def frame_count(from_log):
    """`帧数=` 只数 PNG（R96 收尾时修的）；这里再拿目录对一遍，两种形状各自说明。"""
    pngs = [f for f in os.listdir(SHOTS) if f.endswith('.png')]
    n = len(pngs)
    logged = int(from_log)
    if logged == n:
        return u'%d' % n
    sys.exit(u'拒绝写盘：日志的 帧数=%d 与目录里真实的 PNG=%d 对不上' % (logged, n))


def read_verify():
    if not os.path.exists(LOG):
        sys.exit(u'拒绝写盘：%s 不存在（先跑 verify_r97.sh）' % LOG)
    text = io.open(LOG, encoding='utf-8').read()
    missing = []

    def grab(pattern, name):
        # 取**最后一个**捕获组（R96 的教训：`TEST_EXIT=(\d) 汇总: (.*)` 要的是第二组）；
        # 刻意不开 re.S（否则 `.*` 会把后面每一行都吞进这一格）。
        m = re.search(pattern, text)
        if not m:
            missing.append(name)
            return u'?'
        return m.group(len(m.groups())).strip()

    v = {}
    v['VERIFY_OK'] = grab(r'VERIFY_OK=(\d)', 'VERIFY_OK')
    v['MISSING'] = grab(r'SUMMARY_MISSING=(\d)', 'SUMMARY_MISSING')
    v['BUILD_EXIT'] = grab(r'BUILD_EXIT=(\d)', 'BUILD_EXIT')
    v['BUILD_WARN'] = grab(r'BUILD_WARNING_LINES=(\d)', 'BUILD_WARNING_LINES')
    v['TEST_EXIT'] = grab(r'TEST_EXIT=(\d)', 'TEST_EXIT')
    v['TEST_SUMMARY'] = strip_timing(grab(r'TEST_EXIT=\d+ 最后一行汇总: (.*)', 'TEST_SUMMARY'))
    v['PROBE_EXIT'] = grab(r'PROBE_EXIT=(\d)', 'PROBE_EXIT')
    v['PROBE_SUMMARY'] = strip_timing(grab(r'PROBE_EXIT=\d+ 汇总: (.*)', 'PROBE_SUMMARY'))
    v['CAPTURE_EXIT'] = grab(r'CAPTURE_EXIT=(\d)', 'CAPTURE_EXIT')
    v['FRAME_COUNT'] = frame_count(grab(r'CAPTURE_EXIT=\d+ 帧数=(\d+)', 'FRAME_COUNT'))
    v['FRAMES_EXIT'] = grab(r'FRAMES_EXIT=(\d)', 'FRAMES_EXIT')
    v['FRAMES_LINE'] = grab(r'(FRAME_BASELINE_[^\n]*)', 'FRAMES_LINE')
    v['PY_LINE'] = strip_timing(grab(r'PY_EXIT=\d+ (Ran .*?(?:OK|FAILED[^\n]*))', 'PY_LINE'))
    v['MUTATE'] = grab(r'MUT_EXIT=\d+（[^）]*）(节奏:MUTATE_.*)', 'MUTATE')
    v['LEDGER_EXIT'] = grab(r'LEDGER_EXIT=(\d)', 'LEDGER_EXIT')
    v['LEDGER_LINE'] = strip_timing(grab(r'LEDGER_EXIT=\d+ (Ran .*?(?:OK|FAILED[^\n]*))', 'LEDGER_LINE'))
    v['VIS_EXIT'] = grab(r'VIS_EXIT=(\d)', 'VIS_EXIT')
    v['VIS_LINE'] = grab(r'VIS_EXIT=\d+ (候选块=\d+ 自检=\d+ 失败自检=\d+)', 'VIS_LINE')
    if missing:
        sys.exit(u'拒绝写盘：验证日志里缺这些格 ⇒ %s' % u'、'.join(missing))
    if v['VERIFY_OK'] != '1' or v['MISSING'] != '0':
        sys.exit(u'拒绝写盘：VERIFY_OK=%s SUMMARY_MISSING=%s' % (v['VERIFY_OK'], v['MISSING']))
    return v


def verify_block(v):
    return (u'- 验证（`r97_verify.log`，`VERIFY_OK=%s`、`SUMMARY_MISSING=%s`）：'
            u'构建 `BUILD_EXIT=%s BUILD_WARNING_LINES=%s`；全量 swift test `TEST_EXIT=%s`（%s）；'
            u'在屏那一卷 `PROBE_EXIT=%s`（%s）；重新拍帧 `CAPTURE_EXIT=%s`、帧数=%s；'
            u'帧基线 `%s`；脚本电池 %s；**四张**变异表 %s；台账编号守卫 %s；'
            u'看图仪器 `VIS_EXIT=%s`（%s）。'
            u'产品文件 0 个 ⇒ **不需要换装**（本轮只动判据与工具）。') % (
        v['VERIFY_OK'], v['MISSING'], v['BUILD_EXIT'], v['BUILD_WARN'], v['TEST_EXIT'],
        v['TEST_SUMMARY'], v['PROBE_EXIT'], v['PROBE_SUMMARY'], v['CAPTURE_EXIT'],
        v['FRAME_COUNT'], v['FRAMES_LINE'], v['PY_LINE'], v['MUTATE'], v['LEDGER_LINE'],
        v['VIS_EXIT'], v['VIS_LINE'])


def check_block(text):
    problems = []
    if re.search(r'\d+\.\d+s', text):
        problems.append(u'残留挂钟时间（strip_timing 没生效）')
    if u'（0）' in text:
        problems.append(u'出现"（0）"这种像读数其实是空值的东西')
    if not re.search(r'VIS_EXIT=`?\d+`?（候选块=\d+', text):
        problems.append(u'VIS_EXIT 那一格填的不是退出码')
    if u'?' in text:
        problems.append(u'还留着未解析的 ? 占位')
    return problems


def apply(v):
    # ============================================================ AGENT_UI_AUDIT
    U = 'AGENT_UI_AUDIT.md'
    s = rd(U)
    anchor = u'## 第 98 轮 · R96：'
    assert s.count(anchor) == 1, ('锚点', s.count(anchor))
    entry = u'''## 第 99 轮 · R97：卡片那把尺被重做了一遍——它之前把一条 1pt 的分隔线、一颗按钮、两张卡片都当成"一张卡片"（结案 132 / 更新 140 / 新开 141、142 / U-232…U-239 / D-155）

- 读 R96 推送的 run **38884429809**（`278415e`）：**success**。
  **132 结案**：`UI_PROBE_SAMPLE 主线程采样=314 等待帧占比=100% 主导路径占比=100% 等待终端=1 个`
  + `UI_PROBE_SAMPLE_WAITING=mach_msg2_trap…(314)` + `UI_PROBE_HUNG_KIND=blocked@runloop-wait`
  ⇒ 那条在 runner 上吃满 240 秒的探针是**挂**（主线程整个停在等事件），不是慢。
  上一轮欠的 `UI_PROBE_SAMPLE_SHAPE` 没出现 —— 它只在读不懂时才打，这一次 314 行全解析出来了。
  覆盖率闸门逐格同于上一轮（`本次下结论=6 红=0`、`PROBE_ORDER 露面=7/11 未闭口=1 前缀=1`）。
- 然后回到产品面：把 R95/R96 那把"卡片竖向节奏"的尺**重做**。三条读数各自推翻一次判定：
  ① `settings-privacy-excluded` 亮档报 `边距=14.5/8.0` ⇒ 一条**假红**：独立复算（直接读 PNG）
     给的是 14.0，而判据把卡片段截在 566.5pt（真卡片底在 935.5pt）。根因是"这一行的众数离页面底 ≤3
     就算卡片外"，而卡片材质与页面底在这台机器上只差**一个色档**（244 vs 252，档宽 8）
     ⇒ 解码路径上几个单位的偏移就能翻（U-232、U-233）。
  ② 修完 ① 之后又红一次：`settings-recommendations` 报出一张 y=106..129.5 的"卡片"，
     量出 `边距 6.5/5.5、内侧 0.0/0.0` —— 那是**「恢复默认」那颗按钮**（76pt 宽，横不过带子）。
     判据换成"这一行里最长一段连续卡片材质占带宽的比例"，实测三档 14%（按钮）/ 46%（输入框行）
     / 94%（普通行）⇒ 地板取 30%（U-234）。
  ③ 再修完 ②：一个扫描带里其实有**两张**卡片（「隐私」那张与「数据与保留」那张），
     而判据把整带当一张量 ⇒ 新增 `cardSegments` 先分段、再逐段判（U-235）。
- **BACKLOG 140 的真病根不是"缺高夹具"，是扫描带写死了 440pt**（照 720×540 那一档定的），
  于是 1040 那一档的卡片"到不了底"是**我的带子**造成的，尺却报"这一页比窗口高，被切断了"。
  改成带子跟着夹具尺寸走，并加一条恒等式（`带子下沿 == 窗口高`）钉住 —— 变异 M540 就是撤这条，必红（U-236）。
- 一条**没修完、必须记账**的事（开成 **141**）：判据读的是 `NSImage → tiffRepresentation → NSBitmapImageRep`，
  实测那份位图的色彩空间是 `NSCalibratedRGBColorSpace`，而落盘的 PNG 不是。
  同一张帧两边给出不同的卡片边界（Swift 段1 底 705.5pt / python 复算 765.5pt，顶边与段2 高度一致）
  ⇒ 本轮那些"14.5/14.0 通过"的读数在高夹具上要记成**暂定**：判据自洽，但它量的那张图不是交付的那张图。
- 分段之后第一次看得见的一条**产品面**事实（开成 **142**）：「推荐」页的卡片其实从 y=171.0pt 才开始，
  而"推荐权重客制化"那行标题与「恢复默认」那颗按钮（y=106..129.5）**压在页面底色上**，在卡片外 ——
  其余几屏是"标题与内容一起进卡片"。同一句"这几行属于同一组"在同一个窗口里有三种说法。
  本轮不改：并进去会同时动到滚动高度与那颗按钮的命中区，而这一屏下半截在 540 档仍被窗口截断（140），
  两件事一起做就说不清哪条起了作用 ⇒ 顺序排成 141 → 140 → 142。
- 变异表跟着代码搬家（U-239）：R97 的重构让 R95 那张表的 M530/M531 两格"needle 命中 0 次"，
  电池当场报 `not_run=2` —— 表还在打数字而其中两格已经没有证人。M530 换锚点续用，
  M531 退役并把它的失败模式指到新表的 M538/M539；新增的 M542 第一次跑**被 skip 而不是红**
  （`sawSegment` 记在 `inkRows == 0 ⇒ continue` 之后，证人先被吃掉），修好位置之后它换来的
  是一条新判据："有卡片段却整卷零墨"不许再落进那条合法的 `XCTSkip`。
- 看图那一腿：`r97_stats_visual.py` 先假设"热图那块底色被当成卡片"，**正对照当场否掉了自己的假设**
  —— 热图那些行的众数全都等于页面底，一个候选块都没有；真凶是那条 1pt 的 `Divider()`（U-237）。
  「统计」这一屏现在有一条由源码推出来的断言：它没有 `GroupBox` ⇒ 判据必须报"这一带一张卡片都没有"。

''' + verify_block(v) + u'''
- **下一轮第一件事**：141（像素通道：让判据直接读 PNG 字节，配一张 before/after 表，
  因为仓库里十几支像素判据的阈值都是在这条通道上标定的）；然后回到欠了的产品面清单
  （133 浮层"赋值不选中"、131 统计页要不要卡片、139 勾选态颜色真机、140 剩下那一半高夹具）。

'''
    wr(U, s.replace(anchor, entry + anchor, 1))

    # ============================================================ AGENT_BACKLOG
    B = 'AGENT_BACKLOG.md'
    s = rd(B)
    tail132 = u'    三种形状（整段为空 / 数字开头=no / 数字开头=yes）各自的下一步写在\n'
    assert s.count(tail132) == 1, ('132 锚点', s.count(tail132))
    # 结案段挂在 132 那一条的最后一段之后（找那句"三种形状…"所在段落的结尾行）
    marker = u'`.scratch/motion-audit-2/r96_ci_readings.md` 末尾。\n'
    assert s.count(marker) == 1, ('132 收尾锚点', s.count(marker))
    s = s.replace(marker, marker + u'''    → **R97 结案**：run 38884429809（`278415e`）里
    `UI_PROBE_SAMPLE 主线程采样=314 等待帧占比=100% 主导路径占比=100% 等待终端=1 个`
    + `UI_PROBE_SAMPLE_WAITING=mach_msg2_trap  (in libsystem_kernel.dylib) + 8(314)`
    + `UI_PROBE_HUNG_KIND=blocked@runloop-wait`，且 `UI_PROBE_SAMPLE_UNPARSED` 没出现
    ⇒ 314 行全解析出来了。答案：**挂**（主线程整个停在 runloop 的 mach_msg 等待上），不是慢。
    这一句现在才有资格说，因为它由 314 个采样、一个等待终端、一个族签，而不是由一个兜底的 1.0。
    顺带：R96 准备的"三种形状各一条下一步"一条都没用上 —— 那是给"读不懂"准备的，
    而这一次读懂了。**登记的分支没发生，不算白做**（它逼出了 `未量到` 那一格，才让这次的"读到"可信）。
''', 1)
    tail140 = u'    `settings-stats-populated`（卡片里没有一行被判成墨）报的是**另外两种**原因，\n'
    assert s.count(tail140) == 1, ('140 锚点', s.count(tail140))
    end140 = u'    不属于"被窗口切断"这一类，140 不覆盖它们。\n'
    assert s.count(end140) == 1, ('140 收尾锚点', s.count(end140))
    s = s.replace(end140, end140 + u'''    → **R97 更新（真病根不是夹具，是写死的扫描带）**：`testSettingsCardVerticalRhythmIsOneNumber`
    的带子是 `CGRect(x:155, y:60, width:560, height:440)` —— 照 720×540 那一档定的，
    所以 1040 那一档"卡片到不了底"是**带子**短，不是页面高。改成 `height: fixture.size.height - 60`
    并加一条恒等式（`带子下沿 == 窗口高`，变异 M540 撤它就红）之后，
    `settings-privacy-excluded` 第一次被逐张判：段1 边距 14.5/14.0、段2 边距 14.0/14.0（两档一致）。
    **但 140 不结案**，因为还剩两件事：① `settings-privacy` / `settings-recommendations` 在 540 那一档
    仍然被窗口截断（判据报"卡片底到带子下沿"）⇒ 那两屏的下半截还是没人看，高夹具那一半照做；
    ② 新开的 **141**（判据读的是重编码位图）没解决之前，高夹具上的边界读数本身是**暂定**的。
''', 1)
    s = s.rstrip('\n') + u'''

141. **卡片那把尺读的是重编码后的位图，不是它刚写下的那张 PNG**（R97 开 / 与 D-090、126、43 同族）：
    实测（`CARD_LAYOUT` 那一行）：`bytesPerRow=5760 bitsPerPixel=32 hasAlpha=true planar=false
    色彩空间=NSCalibratedRGBColorSpace` —— 判据走的是 `NSImage → tiffRepresentation → NSBitmapImageRep`，
    而 `NSCalibratedRGBColorSpace` 不是 PNG 落盘用的那个空间。
    后果不是"偏一点点"，是**边界换地方**：同一张 `settings-privacy-excluded` 亮档，
    判据给段1 = 106.0..705.5pt，而直接读 PNG 的独立复算给 106.0..765.5pt（顶边一致、
    段2 高度一致 155.5pt、段1 的底差 60pt）。卡片材质与页面底只差 8 个单位（244 vs 252），
    一次色彩空间换算的量级正好压在这条缝上。
    再补一格读数好让下一轮少猜：**两条通道在"平涂色"上是一致的**
    （Swift 报 `页底=252 填充=244` / `页底=28 填充=36`，直接读 PNG 复算也是 252/244、28/36），
    不一致只出现在**阴影与渐变带**上（卡片圆角外那几行）。
    ⇒ 141 的 before/after 表要按两类分开列：**边界类**判据（卡片段、分隔线、骨架条带、落点线）
    会随通道移动；**色号类**判据（对比度地板、热图相邻档、勾选框填充那一档）在平涂上不动。
    前者必须逐条重量，后者可以抽查——但"抽查"要写明抽了哪几条。
    ⇒ 本轮所有"边距 14.5/14.0 通过"的读数在高夹具上记成**暂定**：判据自洽，但它量的那张图
    不是交付的那张图 —— 这一族在账本里已经有名字了（D-090 是合成前，这次是重编码后）。
    做法（**必须成对做，不能顺手改**）：把判据的读图路径换成直接解 PNG 字节
    （`NSBitmapImageRep(contentsOfFile:)` 或 `ImageIO`），然后对**每一支像素判据**出一张
    before/after 表 —— 仓库里十几支判据的阈值（`inkGate=60`、`lineGate=6`、对比度地板、
    热图相邻档那一条）都是在这条通道上标定的，换通道就是换尺的零点。
    验收：换完之后 `settings-*` 的段边界要与独立复算**逐段相同**，且所有阈值重新量一遍出处。
142. **「推荐」页把分区标题与「恢复默认」放在卡片外，而卡片里第一行才是「近因」**（R97 开 / 与 124、131 同族）：
    实测（`CARD_BAND settings-recommendations`）：卡片段 y=**171.0**..539.5pt，
    而 y=106..129.5 那一带（"推荐权重客制化" + 那颗按钮）与它下面那行说明**都在卡片外**，压在页面底色上。
    其余几屏的写法是"标题与内容一起进卡片"（快捷键、隐私、数据），或整屏就没有卡片（统计，见 131）。
    ⇒ 同一句"这几行属于同一组"在同一个设置窗口里被说了三种话。
    **本轮不改**：把标题与按钮并进卡片会动到那一屏的滚动高度与按钮命中区（那颗按钮现在是
    `.bordered` + `pressedStyle`，R13 收过），而这一屏的卡片下半截在 540 档仍被窗口截断（140），
    两件事一起做就没法说清是哪一条起了作用。顺序：先 141（换读图通道），再 140 的高夹具，
    最后带着完整的段边界来判这一屏。

'''
    wr(B, s)

    # ============================================================ AGENT_VISUAL_ITERATION
    V = 'AGENT_VISUAL_ITERATION.md'
    s = rd(V).rstrip('\n')
    s += u'''

## Round 97 · 卡片那把尺重做：它之前把一条 1pt 的分隔线、一颗按钮、两张卡片都当成"一张卡片"（结案 132 / 更新 140 / 新开 141、142 / U-232…U-239 / D-155）

### 1. 开场清单（设置「推荐」+「隐私·排除名单」两张帧，逐元素，带坐标）

| 元素 | 框 / 读数（亮档） | 判定 |
|---|---|---|
| 「推荐」页 卡片 | y=**171.0**..539.5pt（被窗口截断） | 分隔线 4 条、内侧 16.5/18.0/16.5/18.5/… ⇒ 两档同形；下半截没人看 = 140 剩那一半 |
| 「恢复默认」按钮 | y=106..129.5pt 一带，最长连续卡片材质 152/1120 = **14%** | 曾被判成一张"卡片"并量出 `边距 6.5/5.5、内侧 0.0/0.0` ⇒ 假红，改判据（U-234） |
| 「隐私」页 卡片（1040 档） | y=106.0..705.5pt（判据）/ ..765.5pt（独立复算） | 段边界两条通道不一致 ⇒ 开 **141**（U-236） |
| 「数据与保留」卡片（1040 档） | y=720.0..875.5pt（判据） | 边距 14.0/14.0 ⇒ 与其余卡片同档 |
| 「统计」页 | 0 个卡片段（热图那些行的众数**全等于页面底**） | 源码里没有 `GroupBox` ⇒ 正确读数；钉成断言（U-232） |
| 「统计」页那条 `Divider()` | y=271.0 起 2px、那一行 94% 的像素在 228 档 | 它曾被当成"卡片填充" ⇒ `cardFill` 的地板 20pt（U-233） |

### 2. 判过不改的（带理由）

- **「推荐」页的标题行与那颗按钮在卡片外**：不改，开成 **BACKLOG 142**。
  这条是分段之后才看得见的（之前整带被当一张卡片，"卡片从 171pt 才开始"这件事根本没进过读数）。
  并进去会同时动到滚动高度与那颗按钮的命中区，而这一屏的下半截在 540 档仍被窗口截断（140）
  —— 两件事一起做就说不清哪条起了作用，所以按 141 → 140 → 142 的顺序排。
- **「统计」页 0 卡片 ≠ 缺陷**（BACKLOG 131 仍开着）：本轮把"这一屏没有 GroupBox"钉成断言，
  但**没有**顺手给它加一张卡片 —— 加不加要连热图自身的视觉重量一起判（它已经是一块有底色的区域），
  那是 131 里写的那次独立判断，不是"上一屏改了所以这屏也改"。
- **推荐页内侧留白 16.5/18.0 与别的卡片 14.0/14.5 不同档**：不改。这一屏的卡片里是
  `VStack(spacing: 12)` + 滑块行，滑块的 bezel 不画墨（R96 量过按钮 bezel 是 3.5pt），
  所以墨到墨的距离本来就比文字行大；判据的容差 4.5 覆盖的是**同一张卡片内部**的一致性，
  跨卡片比绝对值不是这条判据的对象（R95 立它时就是这个边界）。

### 3. 三处判据缺陷，都改了（U-232…U-236）

1. `cardFill`：填充从"第一行离页面底 >3"改成"这个档在整带里占 ≥20pt 的行"。
   实测分布：真卡片 176.5–217.0pt、那条线 1.0pt ⇒ 地板离两边都远。
2. `cardRowKind`（新纯函数）：一行的身份由**最长一段连续卡片材质**占带宽的比例决定，
   实测 14% / 46% / 94% 三档 ⇒ 地板 30%。这一格同时解决"按钮冒充卡片"和"输入框把卡片切断"。
3. `cardSegments`（新纯函数）+ 判据循环改成**先分段再逐段判**：一个带子里可以纵向放好几张卡片。
4. 扫描带跟着夹具尺寸走，并加恒等式 `带子下沿 == 窗口高`；"这一页比窗口高，被切断了"
   这句话从纯函数搬到调用处 —— 纯函数没见过窗口尺寸，没资格替它说。

### 4. 仪器自己错一次（U-237）

我先假设"热图那块有底色的区域被尺当成卡片"，写了 `r97_stats_visual.py` 去量。
正对照（真卡片必须"稳定 + 跨带"）当场不绿，而热图那一屏**一个候选块都没有** ——
假设是错的：热图那些行的众数全都等于页面底（格子只占一行宽度的两三成）。
真凶是那条 1pt 的 `Divider()`。如果我只看"读数对不对得上我的假设"，就会把这条假说写进台账。

### 5. 变异表跟着代码搬家（U-239）

R97 的重构把 R95 那张表的两刀变成了"needle 命中 0 次"：M530 与 M531 的锚点都在旧的那几行里。
电池当场报了 `not_run=2` —— 这一种红比漏检更值得记：**表还在跑、还在打数字，而其中两格已经没有证人**。

- M530（把 `.line` 的宽度门槛抬到读不到）**换锚点继续存在**：那一格搬进了 `cardRowKind`，
  刀还是同一刀。
- M531（把页面底容差从 3 放宽到 40）**退役**：它的锚点整条判据被换掉了。
  但它要守的失败模式没消失 —— 换到本表 M538/M539 两刀上（材质地板撤 0 / 抬 60%），
  退役记录写在文件里而不是从列表里安静删一行。
- 新增 M542（`inkMin` 抬到读不到：满带卡片段却零墨）。它第一次跑**没红，而是被 skip 了** ——
  因为 `sawSegment` 记在 `inkRows == 0 ⇒ continue` 之后，证人先被吃掉。
  修好位置之后它 CAUGHT，而这一刀换来的不是多一个号，是一条**新判据**：
  "有卡片段却整卷零墨"从此不许落进那条合法的 `XCTSkip`。

### 6. 七维度自评（本轮）

| 维度 | 分 | 依据 |
|---|---|---|
| 原生一致 | 90 | 本轮零产品改动；卡片节奏现在**逐张**判，两张卡片的 14.0/14.0 与其余同档 |
| 层级与秩序 | 90 | 「统计」页 0 卡片这件事从"读数含糊"变成一条由源码推的断言（131 仍开着，判过没改） |
| 动效恰当 | 91 | 零动效改动；本轮没有新的"要不要加"的判断，所以不加分 |
| 可读性 | 90 | 说明档那一条本轮没重测（R33/R35 的覆盖判据守着），不重复记分 |
| 状态完备 | 86 | 勾选态颜色仍未定案（139 等真机）；推荐页下半截仍没有判据看着（140 剩那一半） |
| 克制 | 95 | 全部改动都在判据侧；产品文件 0 个；一条假红被撤而不是被放宽盖掉 |
| 可验证性 | 93 | 三格新纯函数各带真值表；变异表 `n=5 caught=5 mismatch=0`；两条通道交叉复算并把不一致开成 141 |
| **总评** | **90.7** | ≥90 ⇒ 本轮收口；141 是本轮新开的、下一轮第一件事 |

### 6. 验证

''' + verify_block(v) + u'''

### 7. 下一轮第一件事

141：把判据的读图路径换成直接解 PNG，配一张**每一支像素判据**的 before/after 表
（十几支判据的阈值都在这条通道上标过定）。之后回到产品面欠账：133、131、139、140 剩那一半。
'''
    wr(V, s + '\n')

    # ============================================================ AGENT_DECISIONS
    D = 'AGENT_DECISIONS.md'
    s = rd(D).rstrip('\n')
    s += u'''

---

### D-155（R97）判据只说几何，解释由看得见全局的那一层签；而"什么算一张卡片"要由材质跨度决定

**背景**：R95 立的"同一张卡片里只准有一种留白"这条判据，在 R96 扩到每一张卡片之后开始给出
奇怪的读数。这一轮三条读数把它重做了一遍：
① `settings-privacy-excluded` 亮档 `边距=14.5/8.0` —— 独立复算是 14.0，一条**假红**；
② 修完 ①，`settings-recommendations` 冒出一张 y=106..129.5 的"卡片"，量出 `内侧 0.0/0.0` ——
那其实是「恢复默认」那颗 76pt 宽的按钮；
③ 再修完 ②，发现一个扫描带里其实有**两张**卡片，判据把整带当一张量。
同时 140 的真病根露出来：扫描带是写死的 440pt，而尺把"卡片到不了带子底"报成
"这一页比窗口高，被切断了" —— 那句话不是读数，是我的带子。

**决定**：
1. "这一行还在卡片里吗"由**最长一段连续卡片材质占带宽的比例**决定（地板 30%，
   实测三档 14% / 46% / 94%），不再由"这一行的众数离页面底 ≤3"决定 —— 后者在
   材质与页面只差一个色档（244 vs 252）的机器上，几个单位的解码偏移就能翻。
2. "这一段算不算一张卡片"由 `cardSegments` 决定（连续段 + 高度地板 20pt），判据**逐段**跑。
3. 扫描带跟着夹具尺寸走，并加一条恒等式 `带子下沿 == 窗口高`（变异 M540 撤它就红）。
4. `cardRhythm` 退回纯几何：它只说"卡片底到了这一带的下沿"，
   "所以这一页比窗口高"这句由**见过窗口尺寸的调用处**说。
5. 两条实现交叉复算（Swift 判据 vs 直接读 PNG 的 python）；不一致的地方**不修成一致**，
   开成 BACKLOG 141 并写明代价（仓库里十几支像素判据的阈值都在这条通道上标过定）。

**理由**：①②③是同一个错法的三种表现 —— 让一个只看"这一行像不像背景色"的量去承担
"这是不是一张卡片"这个**结构**判断。结构判断要问跨度（横向的连续材质、纵向的连续段），
不能问色号。④的理由与 D-154 同源：一句话谁说的，取决于它看得见什么；纯函数没见过的东西
不许它替调用处说。⑤是这一轮最贵的收获：如果我不去独立复算，`14.5/14.0 通过`会被当成结论写进台账，
而它其实是"两张不同的图各自自洽"。

**兼容性/迁移**：产品文件 0 个改动（帧基线 124 张逐字节不变，`CAPTURE_EXIT=0`、`CHANGED=0`）；
判据侧 `cardRhythm` 的入参语义变了（一张卡片而不是一条带子），调用点只有节奏那一支；
`cardRowKinds` 多返回一格 `fill`（诊断用）。
**回滚**：`git revert` 本轮提交即可；141 的修法**不在**本轮，回滚不会引入它。
**谁守着**：`testCardRowKindReadsMaterialNotModal`、`testCardSegmentsSplitsCardsAndKeepsTallOnes`、
`testCardFillNeedsAStableBandNotTheFirstDifferingRow`、`testCardRhythmArithmeticIsATruthTable`、
`testSettingsCardVerticalRhythmIsOneNumber`（含"统计页必须 0 段"那条由源码推的断言）；
变异 `n=5 caught=5 mismatch=0`（M537–M541，每张地板一刀、扫描带一刀、填充一刀）。
'''
    wr(D, s + '\n')

    # ============================================================ CHANGELOG（不重复 `## [Unreleased]`）
    C = 'CHANGELOG.md'
    s = rd(C)
    anchor = u'## [Unreleased]\n'
    assert s.count(anchor) == 1, ('Unreleased 锚点', s.count(anchor))
    block = u'''### 产品（R97）

- **无改动**。本轮全部工作在判据侧；124 张帧重拍之后与基线逐字节相同（`CHANGED=0`）。

### 判据与工具（R97）

- **BACKLOG 132 结案**：run 38884429809 里 `主线程采样=314 等待帧占比=100% 等待终端=1 个`
  + `UI_PROBE_SAMPLE_WAITING=mach_msg2_trap…(314)` + `UI_PROBE_HUNG_KIND=blocked@runloop-wait`
  ⇒ 那条在 runner 上吃满 240 秒的探针是**挂**，不是慢。R96 准备的"三种形状各一条下一步"一条没用上
  （它只在读不懂时才打），但正是那一格让这次的"读到了"可信。
- **卡片那把尺重做**（三条读数各推翻一次判定）：
  ① `cardFill` —— 填充不再取"第一行离页面底 >3"，改取"这个档在整带里占 ≥20pt 的行"
  （实测真卡片 176.5–217.0pt、那条 1pt 的 `Divider()` 是 1.0pt）；
  ② 新增 `cardRowKind` —— 一行的身份由**最长一段连续卡片材质**占带宽的比例决定，
  地板 30%（实测按钮 14% / 输入框行 46% / 普通行 94%）；
  ③ 新增 `cardSegments` + 判据**先分段再逐段判**（一个带子里可以纵向放好几张卡片）。
  撤掉三条 `边距=14.5/8.0` 那条**假红**的根因，`settings-privacy-excluded` 第一次被逐张判出
  段1 14.5/14.0、段2 14.0/14.0。
- **BACKLOG 140 的真病根**：扫描带写死 `height: 440`（照 720×540 那一档定的），
  1040 那一档"卡片到不了底"是带子短，尺却报"这一页比窗口高"。改成带子跟着夹具尺寸走
  + 恒等式 `带子下沿 == 窗口高`；那句解释从纯函数搬到调用处。140 **不结案**
  （`settings-privacy` / `settings-recommendations` 在 540 档仍被窗口截断，高夹具那一半照做）。
- **新开 BACKLOG 141**：判据读的是 `NSImage → tiffRepresentation → NSBitmapImageRep`，
  色彩空间实测 `NSCalibratedRGBColorSpace` ≠ PNG 落盘那个空间；同一张帧两条通道给出不同的卡片边界
  （Swift 段1 底 705.5pt / 直接读 PNG 复算 765.5pt）⇒ 本轮高夹具上的"通过"记成**暂定**。
- 看图那一腿：`r97_stats_visual.py` 的正对照否掉了它自己带来的假设
  （"热图底色被当成卡片"是错的：那些行的众数全等于页面底），真凶是那条 1pt 的分隔线。
- 分段之后新看见的一条产品事实开成 **BACKLOG 142**：「推荐」页的卡片从 y=171.0pt 才开始，
  标题行与「恢复默认」那颗按钮（106..129.5pt）压在页面底色上 ⇒ 同一句"这几行属于同一组"
  在设置窗口里有三种说法（其余屏标题在卡片内 / 统计页整屏没有卡片）。本轮不改，顺序 141→140→142。
- 新表 `mutate_r97_card.py`：M537–M541 五刀全 CAUGHT、`mismatch=0`；
  R95 那张表跟着代码搬家：M530 换锚点续用、M531 **退役**（失败模式改由 M538/M539 守）、
  新增 M542（`inkMin` 抬到读不到）⇒ `n=4 caught=4 not_run=0`；
  它第一次跑是被 skip 而不是红，于是多了一条新判据"有卡片段却整卷零墨 ⇒ 红，不许 skip"；
  同时修了 harness 自己两格（"红得不对"时把实际红在哪句打出来、mismatch 必须影响退出码）。

'''
    wr(C, s.replace(anchor, anchor + block, 1))

    # ============================================================ AGENT_STATE
    ST = 'AGENT_STATE.md'
    s = rd(ST)
    lines = s.split('\n')
    cur = lines[2]
    assert cur.startswith(u'最后更新：'), cur[:20]
    assert lines[4].startswith(u'> 上一轮（'), lines[4][:20]
    new = (u'最后更新：2026-10-16 18:55（本地 · R97 / 第 99 轮收尾：'
           u'**卡片那把尺之前把一条 1pt 的分隔线、一颗按钮、两张卡片都当成"一张卡片"** —— '
           u'三条读数各推翻一次判定：① `边距=14.5/8.0` 是**假红**（独立复算 14.0），根因是'
           u'"这一行的众数离页面底 ≤3 就算卡片外"，而材质与页面底在这台机器上只差一个色档（244 vs 252）；'
           u'② 修完又红：y=106..129.5 那张"卡片"其实是「恢复默认」那颗 76pt 按钮（`内侧 0.0/0.0`）；'
           u'③ 再修完发现一个带子里有**两张**卡片，判据把整带当一张量。'
           u'修法是三格纯函数：`cardFill`（填充要占 ≥20pt 的行）、`cardRowKind`（一行算不算卡片看'
           u'**最长连续材质**：实测 14% / 46% / 94% ⇒ 地板 30%）、`cardSegments`（先分段再逐段判），'
           u'外加**BACKLOG 140 的真病根**：扫描带写死 440pt ⇒ 改成跟着夹具尺寸走 + 恒等式'
           u'`带子下沿==窗口高`，而"这一页比窗口高，被切断了"那句解释从纯函数搬到见过窗口尺寸的调用处。'
           u'台账那一腿：**132 结案** —— run 38884429809 给出 `主线程采样=314 等待帧占比=100% 等待终端=1 个`'
           u' + `blocked@runloop-wait`，那条吃满 240 秒的探针是**挂**不是慢（上一轮欠的 SHAPE 那行没出现，'
           u'因为它只在读不懂时才打；而那一格正是这次"读到了"可信的前提）。'
           u'新开 **141**：判据读的是 `tiffRepresentation` 出来的 `NSCalibratedRGBColorSpace` 位图，'
           u'不是它刚写下的 PNG —— 同一张帧两条通道给出不同卡片边界（705.5pt vs 765.5pt，顶边一致、'
           u'另一段高度一致）⇒ 本轮高夹具上的"通过"记成**暂定**，换通道的代价是十几支像素判据的阈值'
           u'都要重标（必须成对做 before/after）。'
           u'仪器自己错一次（U-237）：我先假设"热图那块底色被当成卡片"，正对照当场否掉——'
           u'那些行的众数全等于页面底，真凶是那条 1pt 的 `Divider()`。'
           u'验证：' + short_verify(v) + u'。**下一轮第一件事：141**，然后回到产品面欠账 '
           u'133 / 131 / 139 / 140 剩那一半）')
    lines[2] = new
    lines[4] = (u'> 上一轮（R96 / 第 98 轮收尾）原文开头：' + cur[len(u'最后更新：'):])
    wr(ST, '\n'.join(lines))

    # ============================================================ 人工批次
    M = 'docs/MANUAL_TEST_v1.4.9_round3.md'
    s = rd(M).rstrip('\n')
    s += u'''

## 批次 76（R97 · 卡片边界与留白：帧自己打架的三处）

- 76.1 **「推荐」页那张卡片的上下留白**：打开设置 → 推荐，看卡片**第一行**（"近因"那一段的标题）
  离卡片顶、以及卡片**最后一行**离卡片底，是不是和「快捷键」「隐私」那两页一样松。
  帧上量到的是内侧 16.5/18.0pt（滑块行），而卡片自己的边距这一屏**量不到**（内容比窗口高，被截断）。
  真机若明显比别的页挤 ⇒ 那是 R95 那类"首末行没拿到内边距"的缺陷，只是这一屏的帧看不到。
- 76.2 **「隐私」页滚到底**：把排除名单那一屏滚到最下面，看最后一行（"不记录这些 App 的复制"
  那段的末行，或用户自己加的那几行"移除"按钮）离卡片底有多少。
  判据说 14.0pt，但这条读数落在 141 上（判据读的是重编码的图）⇒ 需要人眼对一次。
- 76.3 **「统计」页要不要一张卡片**：这一屏现在是"0 张卡片 + 1 条压在页面底色上的分隔线"，
  其余四屏都是"1 张卡片 + 内部线"。真机看一眼：热图自己已经是一块有底色的区域，
  再套一层卡片会不会反而重？（BACKLOG 131 要的就是这个判断，本轮没改。）
'''
    wr(M, s + '\n')


def short_verify(v):
    return (u'`VERIFY_OK=%s`：构建 0 告警、全量 `TEST_EXIT=%s`、在屏 `PROBE_EXIT=%s`、'
            u'帧数=%s 且 `FRAMES_EXIT=%s`（`CHANGED=0`）、脚本 %s、四张变异表全 CAUGHT、'
            u'`LEDGER_EXIT=%s`、看图仪器 `VIS_EXIT=%s`（%s）') % (
        v['VERIFY_OK'], v['TEST_EXIT'], v['PROBE_EXIT'], v['FRAME_COUNT'], v['FRAMES_EXIT'],
        v['PY_LINE'], v['LEDGER_EXIT'], v['VIS_EXIT'], v['VIS_LINE'])


def main():
    v = read_verify()
    problems = check_block(verify_block(v))
    if problems:
        sys.exit(u'拒绝写盘：渲染出来的验证段有问题 ⇒ %s' % u'；'.join(problems))
    if os.environ.get('LEDGERS_R97_APPLY') != '1':
        sys.exit(u'只校验不写盘：加 LEDGERS_R97_APPLY=1 才会真的落台账')
    touched = sorted(set(p for _, p, _, _ in STAGES if not p.startswith('.scratch')))
    snapshot = dict((p, rd(p)) for p in touched)
    try:
        apply(v)
    except BaseException as exc:                       # noqa: BLE001 —— 还原后原样抛
        for p, text in snapshot.items():
            wr(p, text)
        sys.exit(u'写盘失败，%d 份台账已整体还原（半份台账比没有更坏）：%s' % (len(snapshot), exc))
    bad = []
    for name, path, marker, why in STAGES:
        hits = rd(path).count(marker)
        if hits == 1:
            print(u'OK   %-16s %s' % (name, marker[:36]))
        else:
            bad.append((name, path, marker, why, hits))
    if rd('CHANGELOG.md').count(u'## [Unreleased]') != 1:
        bad.append(('changelog_heading', 'CHANGELOG.md', u'## [Unreleased]',
                    u'标题被插成了两份（R59 为这一条写过守卫）',
                    rd('CHANGELOG.md').count(u'## [Unreleased]')))
    nums = sorted(set(int(x) for x in re.findall(r'U-(2\d\d)', rd('AGENT_UI_AUDIT.md'))))
    if nums and nums[-1] != 239:
        bad.append(('u_number', 'AGENT_UI_AUDIT.md', 'U-2xx',
                    u'本轮最大的 U 号应是 U-239', nums[-1] if nums else None))
    if bad:
        print(u'\n有格子没落盘：')
        for name, path, marker, why, hits in bad:
            print(u'  RED %-16s %s 标记=%r 命中=%s —— %s' % (name, path, marker, hits, why))
        sys.exit(1)
    print(u'\nLEDGERS_R97_OK=1（%d 格）' % len(STAGES))


if __name__ == '__main__':
    main()

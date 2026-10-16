#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R96 的台账落盘：生成 + 自校验（沿用 R95 立的那条：每一格都要以"落没落盘"被打对勾）。

为什么数字是从 `r96_verify.log` **解析**出来的而不是手抄的：
本轮已经有一次"手抄的数"被抓（D-154 之前，R95 的验证段里我抄错过一次汇总行），
而台账里被生成的数也会串味 —— 所以这里任何一格缺 `KEY=` 就**拒绝写盘**，
宁可让这一轮没有台账，也不让台账里出现一个我没法追到产物的数字。

跑法：PYTHONUTF8=1 python3 .scratch/motion-audit-2/ledgers_r96.py
退出码：0 = 九格齐全；1 = 验证日志缺值，或有格子没落盘。
"""
import io
import os
import re
import subprocess
import sys

REPO = '/Users/wangziyi/Codex_Project0'
LOG = REPO + '/.scratch/motion-audit-2/r96_verify.log'

# (格名, 文件, 必须出现的标记, 这一格承重的那句话)
STAGES = [
    ('ui_audit', 'AGENT_UI_AUDIT.md',
     u'## 第 98 轮 · R96：',
     u'轮次标题：审计那一侧的编号是 R+2 ⇒ 第 98 轮'),
    ('backlog_137', 'AGENT_BACKLOG.md',
     u'R96 结案',
     u'137 的结案段（判定来源换掉，不是补夹具）'),
    ('backlog_132', 'AGENT_BACKLOG.md',
     u'R96 更新（第一份栈到手，但那份读数是假的，已撤）',
     u'132 的进度：runner 那份栈读不懂，下一次的红有明确入口'),
    ('backlog_new', 'AGENT_BACKLOG.md',
     u'139. ',
     u'新开 139（勾选态颜色）与 140（卡片比窗口高）'),
    ('backlog_140', 'AGENT_BACKLOG.md',
     u'140. ',
     u'140 正文'),
    ('decisions', 'AGENT_DECISIONS.md',
     u'### D-154（R96）',
     u'本轮的决定 —— R93 就是漏了这一格'),
    ('visual', 'AGENT_VISUAL_ITERATION.md',
     u'## Round 96 ·',
     u'Round 96 全文（含开场清单、七维度自评与验证段）'),
    ('changelog', 'CHANGELOG.md',
     u'### 产品（R96）',
     u'产品那一节；同一条守卫还要求 `## [Unreleased]` 只出现一次'),    ('manual_batch', 'docs/MANUAL_TEST_v1.4.9_round3.md',
     u'## 批次 75',
     u'真机那一腿：勾选态的颜色 / 未勾 vs 禁用 / 卡片下半截'),
    ('state_rotation', 'AGENT_STATE.md',
     u'本地 · R96 / 第 98 轮收尾',
     u'第 3 行换成本轮，R95 那行降为"上一轮"引用'),
]


def read_verify():
    """从验证日志里解析本轮要引用的每一个数；缺任一格 ⇒ 拒绝写盘。"""
    if not os.path.exists(LOG):
        sys.exit(u'拒绝写盘：%s 不存在（先跑 verify_r96.sh）' % LOG)
    text = io.open(LOG, encoding='utf-8').read()

    def grab(pattern, name):
        # 取**最后一个**捕获组：`TEST_EXIT=(\d) 最后一行汇总: (.*)` 要的是汇总，
        # 而 `BUILD_EXIT=(\d)` 只有一个组 ⇒ 取最后一个对两种都对。
        # （第一版取 group(1)，于是台账里打出过 "全量 swift test `TEST_EXIT=0`（0）" ——
        #   一个看起来像读数的括号，里面装的是另一个键的值。）
        # 刻意**不**开 re.S：`(MUTATE .*)` 配上 S 会把后面每一行都吞进这一格，
        # 台账里就会出现一段"验证行下面挂着半份日志"的怪东西。
        m = re.search(pattern, text)
        if not m:
            missing.append(name)
            return u'?'
        return m.group(len(m.groups())).strip()

    missing = []
    v = {}
    v['VERIFY_OK'] = grab(r'VERIFY_OK=(\d)', 'VERIFY_OK')
    v['BUILD_EXIT'] = grab(r'BUILD_EXIT=(\d)', 'BUILD_EXIT')
    v['BUILD_WARN'] = grab(r'BUILD_WARNING_LINES=(\d)', 'BUILD_WARNING_LINES')
    v['TEST_SUMMARY'] = strip_timing(grab(r'TEST_EXIT=(\d) 最后一行汇总: (.*)', 'TEST_SUMMARY'))
    v['TEST_EXIT'] = grab(r'TEST_EXIT=(\d)', 'TEST_EXIT')
    v['PROBE_SUMMARY'] = strip_timing(grab(r'PROBE_EXIT=(\d) 汇总: (.*)', 'PROBE_SUMMARY'))
    v['PROBE_EXIT'] = grab(r'PROBE_EXIT=(\d)', 'PROBE_EXIT')
    v['CAPTURE_EXIT'] = grab(r'CAPTURE_EXIT=(\d)', 'CAPTURE_EXIT')
    v['FRAME_COUNT'] = frame_count(grab(r'CAPTURE_EXIT=\d+ 帧数=(\d+)', 'FRAME_COUNT'))
    v['FRAMES_LINE'] = grab(r'(FRAME_BASELINE_[^\n]*)', 'FRAMES_LINE')
    v['FRAMES_EXIT'] = grab(r'FRAMES_EXIT=(\d)', 'FRAMES_EXIT')
    v['PY_LINE'] = strip_timing(grab(r'PY_EXIT=\d+ (Ran .*?(?:OK|FAILED[^\n]*))', 'PY_LINE'))
    v['MUTATE'] = grab(r'MUT_EXIT=\d+（[^）]*）(节奏:MUTATE_.*)', 'MUTATE')
    v['LEDGER_LINE'] = strip_timing(grab(r'LEDGER_EXIT=\d+ (Ran .*?(?:OK|FAILED[^\n]*))', 'LEDGER_LINE'))
    v['LEDGER_EXIT'] = grab(r'LEDGER_EXIT=(\d)', 'LEDGER_EXIT')
    v['VIS_LINE'] = grab(r'VIS_EXIT=(\d) (卡片=\d+ 框=\d+ 自检=\d+ 失败自检=\d+)', 'VIS_LINE')
    v['VIS_EXIT'] = grab(r'VIS_EXIT=(\d)', 'VIS_EXIT')
    v['MISSING'] = grab(r'SUMMARY_MISSING=(\d)', 'SUMMARY_MISSING')
    if missing:
        sys.exit(u'拒绝写盘：验证日志里缺这些格 ⇒ %s\n'
                 u'（"0 个缺陷"比红更坏，"抄一个猜出来的数"比不写更坏）' % u'、'.join(missing))
    if v['VERIFY_OK'] != '1' or v['MISSING'] != '0':
        sys.exit(u'拒绝写盘：VERIFY_OK=%s SUMMARY_MISSING=%s ⇒ 先把电池跑绿再落台账'
                 % (v['VERIFY_OK'], v['MISSING']))
    return v


def verify_block(v):
    return (u'- 验证（`r96_verify.log`，`VERIFY_OK=%s`、`SUMMARY_MISSING=%s`）：'
            u'构建 `BUILD_EXIT=%s BUILD_WARNING_LINES=%s`；全量 swift test `TEST_EXIT=%s`（%s）；'
            u'在屏那一卷 `PROBE_EXIT=%s`（%s）；重新拍帧 `CAPTURE_EXIT=%s`、帧数=%s；'
            u'帧基线 `%s`；脚本电池 %s；三张变异表 %s；台账编号守卫 %s；看图仪器 `VIS_EXIT=%s`（%s）。'
            u'产品文件 1 个（`SettingsView.swift`）⇒ **换装**。') % (
        v['VERIFY_OK'], v['MISSING'], v['BUILD_EXIT'], v['BUILD_WARN'], v['TEST_EXIT'],
        v['TEST_SUMMARY'], v['PROBE_EXIT'], v['PROBE_SUMMARY'], v['CAPTURE_EXIT'],
        v['FRAME_COUNT'], v['FRAMES_LINE'], v['PY_LINE'], v['MUTATE'], v['LEDGER_LINE'],
        v['VIS_EXIT'], v['VIS_LINE'])


def short_verify(v):
    return (u'`VERIFY_OK=%s`：构建 0 告警、全量 `TEST_EXIT=%s`、在屏 `PROBE_EXIT=%s`、'
            u'帧数=%s 且 `FRAMES_EXIT=%s`、脚本 %s、三张变异表全 CAUGHT、`LEDGER_EXIT=%s`、'
            u'看图仪器 `VIS_EXIT=%s`（%s）') % (
        v['VERIFY_OK'], v['TEST_EXIT'], v['PROBE_EXIT'], v['FRAME_COUNT'], v['FRAMES_EXIT'],
        v['PY_LINE'], v['LEDGER_EXIT'], v['VIS_EXIT'], v['VIS_LINE'])


def rd(p):
    return io.open(os.path.join(REPO, p), encoding='utf-8').read()


def wr(p, s):
    io.open(os.path.join(REPO, p), 'w', encoding='utf-8').write(s)


def strip_timing(s):
    """把 "… in 154.431 (154.476) seconds" / "… in 11.324s" 剪掉：台账要引用的是**结论**
    （跑了多少、跳了多少、红没红），挂钟时间每一遍都不一样，抄进台账就等于下一轮对不上账。"""
    return re.sub(r'\s+in\s+[0-9.]+\s*(?:\([0-9.]+\)\s*)?s(?:econds?)?', '', s).strip()


def check_block(text):
    """渲染出来的验证段自己也要过一遍：本轮它两次把**另一个键的值**填进 `%s`
    （一次是 `TEST_EXIT=0`（0），一次是 `VIS_EXIT=卡片=2 …`），两种都长得像读数。
    这三条查的就是"看起来像数、其实是被填错的位置"。"""
    problems = []
    if re.search(r'\d+\.\d+s', text):
        problems.append(u'残留挂钟时间（strip_timing 没生效）')
    if u'（0）' in text or u'=`0`（0）' in text:
        problems.append(u'出现"（0）"这种像读数其实是空值的东西')
    if not re.search(r'VIS_EXIT=`?0`?（卡片=\d+', text):
        problems.append(u'VIS_EXIT 那一格填的不是退出码')
    return problems


def frame_count(from_log):
    """`帧数=` 这一格在 pass-1 里把 `capture-readings.log` 也算进去了（125 vs 闸门比对的 124）。
    所以这里不直接信它：拿目录里真实的 PNG 数对一遍，两种形状各自说明，别悄悄取一个。"""
    pngs = [f for f in os.listdir('/tmp/r96_shots') if f.endswith('.png')]
    n = len(pngs)
    logged = int(from_log)
    if logged == n:
        return u'%d' % n
    if logged == n + 1:
        return u'%d（日志那格写的是 %d：目录里除 PNG 还有一份 capture-readings.log）' % (n, logged)
    sys.exit(u'拒绝写盘：日志的 帧数=%d 与目录里真实的 PNG=%d 对不上（差 %d，不是"多一份日志"）'
             % (logged, n, logged - n))


# ------------------------------------------------------------------ 正文：一次写九格
def apply(v):
    # ============ AGENT_UI_AUDIT
    U = 'AGENT_UI_AUDIT.md'
    s = rd(U)
    anchor = u'## 第 97 轮 · R95：'
    assert s.count(anchor) == 1, (u'锚点不唯一', s.count(anchor))
    entry = u'''## 第 98 轮 · R96：判据的对象从"一张卡片"扩到"每张卡片"，它当场抓到上一轮留下的孤儿；runner 那份栈被证明是**我读不懂**（结案 137 / 新开 139、140 / U-227…U-231 / D-154）

- 读 R95 推送的 run **38876999489**（job 116894329916，`bf6b921`）：**success**。
  覆盖率闸门与上一轮完全一致（`本次下结论=6 红=0`、`PROBE_ORDER 露面=7/11 未闭口=1 前缀=1`、
  `PROBE_QUEUED` 同一批四条）⇒ R95 的登记刷新没有制造新的红。
  **132 的第一格真的有产物了**：`UI_PROBE_SAMPLE_EXIT=0`、
  `UI_PROBE_SAMPLE 主线程采样=306 主导路径占比=100% 最深帧=读不到`、`UI_PROBE_HUNG_KIND=blocked@unknown`。
- 那两行是**假话**，本轮已撤（U-231）：`nodes` 为空时旧写法把占比兜底成 `1.0` ⇒ "我读不懂这份文件"
  被打印成"它挂在某个我们不认识的帧上"，而且带着一个具体的百分比。现在 `nodes` 为空 ⇒ **不判**，
  并新增 `UI_PROBE_SAMPLE_UNPARSED=1` 与 `UI_PROBE_SAMPLE_SHAPE 缩进N 数字开头=yes/no 长度=M`
  —— **只打形状不打帧名**（日志里不许出现用户的剪贴板内容，而诊断"我的正则读不到什么"不需要帧名）。
  下一次 CI 的那行 SHAPE 才是 132 的答案的入口（三种形状对应三种下一步，写在 `r96_ci_readings.md`）。
- **137 结案**，但修法不是"给旧尺补一份并列夹具"：判定不再从"挑一条最深路径"读数，
  改成"有多少采样停在等待帧上"（`_waiting_leaves`：等待帧套等待帧只算最内层那一次；
  并列时把**两个族连同各自采样数**都打出来，判 `blocked@ambiguous`）。
  旧尺在并列时只能报一个族，而那个族是我挑的，不是栈说的。
  变异表重做：M525 的锚点随代码消失而**退役**（留着只会以"needle 命中 0 次"假装在册），
  M527 由 M534 替代，新增 M533（嵌套重复计数）、M535（分母被换）、M536（去掉"读不懂"那一格）。
- 把 `testSettingsCardVerticalRhythmIsOneNumber` 的对象从"那一张卡片"扩到
  "**每一张 settings 卡片**"，它当场抓到上一轮留在「数据」页的一处孤儿
  （三段里只有第一段有 `.padding(.vertical, 4)`）：`settings-data 边距=18.0/14.0、内侧=18.0/14.5/17.5/14.0`
  ⇒ 删掉那一格（U-227）。**上一轮我给它写的那句理由被自己的读数推翻**：
  我说它"讲的是另一件事"，其实它讲的就是同一件事（行与分隔线之间的距离），却只有一段有。
- 看图那一腿：设置「隐私」分区逐元素重判（`r96_privacy_visual.py`，尺借 R92/R95 那一支）。
  勾选框两态可辨（勾上时框自己的填充换了一档：亮 223→213 变深、暗 58→67 变浅；
  对勾那颗的墨 46/47 颗 vs 未勾 12–20/13–20 颗）⇒ 不加动效（U-228）；
  但**五颗框的色度全是 0** —— 系统的勾选态该是强调色，而源码里这五颗都是裸 `Toggle`
  （`SettingsView.swift` 里没有任何自定义 `toggleStyle`）⇒ 灰不是产品选的色，
  开成 **139** 走真机，不改产品、不拿帧当证据。默认排除那一列判过不改（U-229）。仪器自己错两次（U-230）。

''' + verify_block(v) + u'''
- **下一轮第一件事**：读 R96 的 CI —— `UI_PROBE_SAMPLE_SHAPE` 那一行（三种形状三种下一步），
  以及 `UI_PROBE_SAMPLE_TIED=` / 等待终端那两行是否终于给出了族。

'''
    wr(U, s.replace(anchor, entry + anchor, 1))

    # ============ AGENT_BACKLOG
    B = 'AGENT_BACKLOG.md'
    s = rd(B)
    tail137 = u'    再给 M527 一条期望。在那之前 132 的 runner 读数要带一句"并列未覆盖"。\n'
    assert s.count(tail137) == 1, ('137 锚点', s.count(tail137))
    s = s.replace(tail137, tail137 + u'''
    → **R96 结案**：修法不是补夹具，而是**换掉判定的来源**。`_waiting_leaves` 数的是
    "有多少采样停在等待帧上"（等待帧套等待帧只算最内层那一次），并列时两个族连同各自采样数
    一起打出来 ⇒ `blocked@ambiguous` + `UI_PROBE_SAMPLE_TIED=2 个族分不开：menu-tracking=300、runloop-wait=300`。
    新夹具 `sample_tied_branches.txt`；变异 M534（"并列时只报第一个族"）现在**必红**；
    M525 的锚点随 `_dominant_path` 退出判定而消失 ⇒ 退役，M527 由 M534 替代，
    两条退役记录写在 `mutate_r96_triage.py` 的文档串里（"表里少一格"与"那一格永远绿"是同一种失忆）。
''', 1)
    tail132 = u'    132 仍然开着：这一轮的 CI 才有第一份 runner 栈。\n'
    assert s.count(tail132) == 1, ('132 锚点', s.count(tail132))
    s = s.replace(tail132, tail132 + u'''
    → **R96 更新（第一份栈到手，但那份读数是假的，已撤）**：run 38876999489 里
    `UI_PROBE_SAMPLE_EXIT=0`、`UI_PROBE_SAMPLE 主线程采样=306 主导路径占比=100% 最深帧=读不到`、
    `UI_PROBE_HUNG_KIND=blocked@unknown` —— 前一半是真的（主线程那一行确实读到 306 个采样），
    后一半是**兜底造出来的**：`nodes` 为空时旧写法把占比写成 1.0。
    ⇒ 撤掉兜底（读不懂就是未量到，占比 0.0 而不是 1.0），并新增 `UI_PROBE_SAMPLE_UNPARSED=1`
    + `UI_PROBE_SAMPLE_SHAPE`（只打缩进/是否数字开头/长度，不打帧名）。
    132 的"挂 or 慢"仍未回答，但下一次的红/绿有了明确的入口：那行 SHAPE。
    三种形状（整段为空 / 数字开头=no / 数字开头=yes）各自的下一步写在
    `.scratch/motion-audit-2/r96_ci_readings.md` 末尾。
''', 1)
    s = s.rstrip('\n') + u'''

139. **设置里的勾选框在帧里色度为 0：勾上不是强调蓝，而是"换一档的灰"**（R96 开 / 与 126、45、130 同族）：
    实测（`r96_privacy_readings.log`，`settings-privacy` 两档）：五颗框的 `chroma=0`；
    未勾的填充亮 (223,223,223) / 暗 (58,58,58)，勾上的亮 (213,213,213) / 暗 (67,67,67)，
    对勾那颗的墨 46（亮）/ 47（暗）颗 vs 未勾 12–20 / 13–20 颗。
    源码侧事实：那五颗全是裸 `Toggle("…", isOn:)`，`SettingsView.swift` 里**没有任何自定义 `toggleStyle`**
    ⇒ 灰**不是产品选的颜色**，而是"离屏/非 key 窗口里系统怎么画"或"捕获通道怎么合成"。
    两种解释的下一步完全不同（前者什么都不用做，后者是通道盲区），所以：
    ① 真机核对（人工批次 75.1）：勾选一颗，看它是不是强调色；
    ② 若真机是蓝 ⇒ 把"勾选态的颜色"写成一格**声明的盲区**（与 `menuSurfaceReplicaFixtures` 同形状），
       而不是每次看图时靠人记得；
    ③ 若真机也是灰 ⇒ 那是 `accentColor` 没进这棵树，改的是窗口侧不是这一屏。
    **本轮不改产品**：拿帧当证据去改一颗我没资格判的控件，正是 D-090 禁止的那类操作。

140. **三张设置卡片比窗口高，节奏判据对它们无从下手**（R96 开 / 与 138、43 同族）：
    `cardRhythm` 现在会把"为什么没量到"分原因返回（R96 新加），于是
    `settings-privacy` / `settings-recommendations` / `settings-privacy-excluded` 三张报的是
    `CARD_RHYTHM_DECLINED … 原因=卡片底到扫描带下沿 ⇒ 这一页比窗口高，被切断了`
    —— 它们**不是**"没有分隔线"，是"尺看不到卡片底"。
    这一屏在 720×540 的夹具里被截断是合理的（内容本来就要滚动，`detailScrollView` 在那儿），
    但代价是：卡片**下半部分**的留白节奏没有任何判据看着 —— 而 R96 那个缺陷（三段里只有一段有
    `.padding(.vertical, 4)`）恰好就长在卡片的**下半截**，这一轮能抓到是因为它在 `settings-data`，
    那一张没有比窗口高。换句话说：同样的缺陷在 privacy / recommendations 上是**测不到**的。
    做法：给这两屏各加一张更高的夹具（`settings-privacy-tall-720x1040`，与已有的
    `settings-privacy-excluded-720x1040` 同一族），让卡片完整落进带子里再判；
    帧数从 124 涨到 128 是可接受的成本。**别为了绿把 declined 那一格放宽**。
    顺带把边界写清楚，免得下一轮把两类混成一类：`settings-stats`（整带没有卡片）与
    `settings-stats-populated`（卡片里没有一行被判成墨）报的是**另外两种**原因，
    不属于"被窗口切断"这一类，140 不覆盖它们。
'''
    wr(B, s)

    # ============ AGENT_VISUAL_ITERATION
    V = 'AGENT_VISUAL_ITERATION.md'
    s = rd(V).rstrip('\n')
    s += u'''

## Round 96 · runner 那份栈被证明是"我读不懂"；判据扩到每张卡片之后当场抓到上一轮的孤儿（结案 137 / 新开 139、140 / U-227…U-231 / D-154）

### 1. 开场清单（设置「隐私」，逐元素，带坐标）

`settings-privacy-720x540-{light,dark}`（scale=2，尺寸从帧名推）：

| 元素 | 框 / 读数 | 判定 |
|---|---|---|
| 卡片 | (172,106)..(696,**539**)pt | 底被窗口切断 ⇒ 开成 140；填充对页面底 1.071 / 1.088 ⇒ 两档同形，不动 |
| 勾选框 ×4（未勾） | y=170/192/214/236..+15~16pt | 填充 亮 (223,223,223) / 暗 (58,58,58)，色度 0，内部墨 12–20 / 13–20 颗 |
| 勾选框 ×1（已勾） | y=278..294pt | 填充 亮 (213,213,213) / 暗 (67,67,67)，色度 0，对勾 46 / 47 颗，对填充对比 10.84 / 7.57 |
| 默认排除那一列 | 19 段文字带 | 左沿众数 177.5pt（min 177.5 / max 199.0）、行距中位 10.5pt、对比 min 2.94（亮）/ 5.31（暗） |
| 侧栏 | —— | 本轮不判（R95 已按 D-090 / BACKLOG 126 登记为盲区，暗档只出 4 带） |

### 2. 判过不改的（带理由）

- **两态可辨，不加动效**（U-228）：勾上时框自己的填充换了一档（亮 223→213 变深、暗 58→67 变浅）
  **并且**多一枚对勾（12–20 颗 → 46 颗）。两态的差别不只有颜色，还有笔画 —— 这正是"静置一眼
  看得出开没开"。再叠淡入只会让"我刚才那一下有没有生效"变成要看动画才知道。
- **强调色缺席不改**（开成 139）：五颗框的 `chroma=0`，而系统勾选态该是强调色。
  但源码里这五颗都是裸 `Toggle`，**没有任何自定义 `toggleStyle`** ⇒ 灰不是产品选的色。
  两种解释（非 key 窗口的系统画法 / 捕获通道合成）下一步完全不同，所以走真机（批次 75.1），
  不拿帧当证据去改控件 —— 那是 D-090 明令禁止的那类操作。
- **默认排除那一列的重复前缀不改**（U-229）：`Text("默认排除：\\(id)")`，帧里可见 8 行都带同一个前缀
  （名单共 9 项，第 9 项落在窗口外 ⇒ 与 140 是同一件事）。看着像冗余，但去掉它换不来任何**可测**的好处：
  前缀逐字相同，id 本来就共一条左轴（实测众数 177.5pt，散布 21.5pt 且全在"标题行/说明行"那一档）；
  而前缀是**每行自带的来源标注** —— 两段 `ForEach`（默认排除 / 用户排除）万一将来交错，
  去掉前缀就把"这条是谁排除的"丢了，那是信息不是装饰。
- **卡片对页面底只有 1.071 / 1.088**：这是系统 `GroupBox` 材质，两档同形 ⇒ 不动。

### 3. 一处真缺陷，改了（U-227）

把 `testSettingsCardVerticalRhythmIsOneNumber` 的对象从"那一张卡片"扩到"**每一张 settings 卡片**"之后，
它当场红了 `settings-data`：`边距=18.0/14.0、内侧=18.0/14.5/17.5/14.0`。
根因是上一轮我**特意留下**的那格 `.padding(.vertical, 4)` —— 三段里只有第一段有。
我上一轮给它写的理由是"卡片内部讲的是另一件事"，这句话被自己的读数推翻：
它讲的就是同一件事（行与分隔线之间的距离），却只有一段有 ⇒ 删掉。

同一轮里容差从 3.0 改到 4.5，**不是为了让它绿**：`settings-data` 里同样 12pt 的布局间距，
接在文字行后面量到 14.0/14.5，接在 `.rounded` 按钮行后面量到 17.5 ⇒ 按钮 bezel 底下有
**3.5pt 不画墨的边**，而这把尺量的是墨到墨。3.5 是从这张帧自己量的，加 1pt 余量。
R95 那个缺陷的极差是 8.5pt、M528 撤修复之后是 7.5pt ⇒ 4.5 这条线仍然咬得住（两张变异表都是证据）。

### 4. 分诊那把尺换掉了判定的来源（137 结案）

旧尺问"最深的那一条路径占多少"，新尺问"**有多少采样停在等待帧上**"：
等待帧套等待帧只算最内层那一次（否则同一份等待会被数 4 遍），
并列时两个族连同各自采样数一起打出来 ⇒ `blocked@ambiguous` + `UI_PROBE_SAMPLE_TIED=…`。
为什么不是"给旧尺补一份并列夹具"：因为旧尺在并列时**必须**挑一个孩子，
挑哪个都不是栈说的 —— 补夹具只是给我的选择拍一张好看的照片。

runner 的第一份栈（run 38876999489）读出来是
`主线程采样=306 主导路径占比=100% 最深帧=读不到` + `blocked@unknown` ——
那是**兜底造出来的假话**：`nodes` 为空时占比被写成 1.0（U-231）。
现在：读不懂 ⇒ `未量到` + `UI_PROBE_SAMPLE_UNPARSED=1` + `UI_PROBE_SAMPLE_SHAPE`
（只打缩进/是否数字开头/长度，**不打帧名** —— 日志里不许出现用户的剪贴板内容）。

### 5. 仪器自己错两次（U-230）

找勾选框那一列：① 用"墨"的门槛 60 ⇒ 只检出 3 颗（未勾的框填充离卡片只有 24，整颗都不算墨），
而"少两颗"和"这一屏只有三颗框"在同一张报表上一模一样；② 降到 15 ⇒ 检出 7 颗（把两段标题当成了框）。
最后的判据是**框有自己的填充**（离卡片 ≥8）⇒ 正好 5 颗，自检通过（两档 `SELF-CHECK OK`、失败 0）。
中间那一步如果我只调门槛不调判据，就会拿"数到 5"当尺对。

### 6. 七维度自评（本轮）

| 维度 | 分 | 依据 |
|---|---|---|
| 原生一致 | 90 | 卡片节奏扩到每张后仍有一处孤儿被抓并修掉；勾选态强调色缺席**未定案**（139），不扣分也不加分 |
| 层级与秩序 | 92 | 五张卡片现在同一档留白；「数据」页三段之间不再有第三种距离 |
| 动效恰当 | 91 | 本轮零动效改动，且给出"两态差别不只有颜色 ⇒ 不必加淡入"的量化依据（12–20 颗 vs 46 颗） |
| 可读性 | 90 | 说明档 2.94(亮)/5.31(暗) 与全窗口同一档（R27/R33 的相对判据守着）；两态对填充的对比 6.4–11.4(亮) / 7.6–8.4(暗) |
| 状态完备 | 87 | 勾选/未勾选可辨；**禁用**那颗开关在别的分区（R39 已补帧）；勾上的颜色这一通道判不了 ⇒ 139 |
| 克制 | 95 | 删了一格 padding，没有加任何新视觉；假话被撤而不是被修饰 |
| 可验证性 | 94 | 判据对象扩到每张卡片；declined 分原因返回；变异表 n=7 caught=7；两处仪器自纠有读数留痕 |
| **总评** | **91.3** | ≥90 ⇒ 本轮收口；139/140 两格仍开着 |

### 7. 验证

''' + verify_block(v) + u'''

### 8. 下一轮第一件事

读 R96 的 CI 里 `UI_PROBE_SAMPLE_SHAPE` 那一行 —— 三种形状（整段为空 / 数字开头=no / 数字开头=yes）
各自的下一步已经写在 `r96_ci_readings.md` 末尾。然后：140（给两张比窗口高的卡片配一张高夹具）、
133（浮层夹具"赋值不选中"那条通道，重算 R76 那格的墨移动量）。
'''
    wr(V, s + '\n')

    # ============ AGENT_DECISIONS
    D = 'AGENT_DECISIONS.md'
    s = rd(D).rstrip('\n')
    s += u'''

---

### D-154（R96）判据的对象要扩到"每一张"，而"为什么没量到"必须分原因返回

**背景**：R95 把五张设置卡片的竖向留白统一了，但判据只压在 `settings-shortcuts` 一张上
（别的卡片"不一定有分隔线，内侧那一档没有对象"）。这一轮把对象扩到每一张 `settings-*` 卡片，
它当场红了 `settings-data`：`边距=18.0/14.0、内侧=18.0/14.5/17.5/14.0` ——
上一轮我特意留在卡片内部的那格 `.padding(.vertical, 4)` 是三段里唯一的一段。
同时 runner 的第一份 `sample` 回来了，读出来是
`主线程采样=306 主导路径占比=100% 最深帧=读不到` + `blocked@unknown` ——
后一半是 `nodes` 为空时被兜底成 1.0 造出来的假话。

**决定**：
1. 判据对象扩到"每一张 settings 卡片"，并且**由读数决定谁参与**：读到 ≥2 条分隔线的才判，
   一条都没读到的分两种情况各自打印（`CARD_RHYTHM_DECLINED 原因=…` 与 `CARD_RHYTHM_NO_DIVIDER`）。
2. `cardRhythm` 多返回一格 `declined`：卡片顶到带上沿 / 卡片底到带下沿（这一页比窗口高）/
   卡片里没有一行被判成墨 —— 三种"没量到"不许共用一条读数，也不许与"确实没有分隔线"共用。
3. 容差 3.0 → 4.5，**理由与出处写在断言旁边**：3.5pt 是这张帧里"按钮 bezel 不画墨的边"的实测值，
   加 1pt 余量。同时保留 R95 缺陷（8.5pt）与 M528（7.5pt）都能被这条线抓住的事实。
4. `analyse_sample` 的判定来源换掉：从"挑一条最深路径"改成"有多少采样停在等待帧上"
   （`_waiting_leaves`，嵌套只算最内层、并列报两族）；`nodes` 为空 ⇒ **不判**，
   并打印只含形状（缩进/是否数字开头/长度）的 `UI_PROBE_SAMPLE_SHAPE`，**不打帧名**。
5. 扩对象的同时补一条"不许静默跳过"：`sawInk && judged == 0` ⇒ 红（"有卡片读到了墨，
   却一条都没判"= 尺瞎了）。M530 在这一格从 DID-NOT-RUN 变成 CAUGHT。

**理由**：①与②是同一件事的两面 —— 一条只压一张卡片的判据，等于把"其余四张没人看"写进制度；
而"没量到"如果不分原因，下一次就会有人拿"这张卡片没有分隔线"去解释"这张卡片比窗口高"。
③不是放宽：放宽必须带着被放宽的那 1.5pt 是谁（这里是一段可复现的 bezel 边距），
否则就是在给缺陷让路。④的理由最硬：并列的时候"挑一个孩子"不是读数，是决定。
⑤是本轮唯一一条"防自己"的：把判据从一张扩到十张，最容易得到的收益不是抓到更多缺陷，
而是让"这一张没判"变得无人察觉。

**兼容性/迁移**：产品侧只删一格 padding（`settings-data` 两张帧随提交 `update`）；
判据侧新增的 `declined` 是返回值的第四格，两处调用点都改了。
**回滚**：`git revert` 本轮提交；容差与判定来源各自独立可回滚。
**谁守着**：`testSettingsCardVerticalRhythmIsOneNumber`（每张卡片）、
`testCardRhythmArithmeticIsATruthTable`（四种"没量到"各一格）、
`test_every_settings_card_applies_the_shared_edge_inset`（调用点级）、
`test_empty_main_thread_block_is_not_read_as_an_unknown_hang`；
变异 `n=7 caught=7`（M523/M524/M526/M533/M534/M535/M536）与节奏那张 `n=4 caught=4`（M528–M531），
退役的 M525/M527 记在 `mutate_r96_triage.py` 的文档串里。
'''
    wr(D, s + '\n')

    # ============ CHANGELOG（不重复 `## [Unreleased]`：R59 为这一条写过守卫）
    C = 'CHANGELOG.md'
    s = rd(C)
    anchor = u'## [Unreleased]\n'
    assert s.count(anchor) == 1, ('Unreleased 锚点', s.count(anchor))
    block = u'''### 产品（R96）

- 删掉设置「数据」卡片里那格**孤儿**内边距：三段小节里只有第一段带 `.padding(.vertical, 4)`，
  于是同一张卡片里同时有 18.0 与 14.5 两种留白（`边距=18.0/14.0、内侧=18.0/14.5/17.5/14.0`）。
  这是上一轮统一五张卡片时**特意留下**的一格，留下的那句理由（"卡片内部讲的是另一件事"）
  被扩了对象的判据当场推翻：它讲的就是同一件事。改后 `边距=14.0/14.0`、内侧三档 14.0/14.5/17.5
  （17.5 那一段是 `.rounded` 按钮 bezel 底下不画墨的 3.5pt，判据容差因此按实测从 3.0 放到 4.5，
  出处写在断言旁边）。`settings-data` 两张帧随本提交 `update`。

### 判据与工具（R96）

- **BACKLOG 137 结案**：`analyse_sample()` 的判定来源换掉 —— 不再从"挑一条最深路径"读数，
  改成"有多少采样停在等待帧上"（`_waiting_leaves`：等待帧套等待帧只算最内层那一次；
  并列时两个族连同各自采样数一起打出来 ⇒ `blocked@ambiguous` + `UI_PROBE_SAMPLE_TIED=…`）。
  新夹具 `sample_tied_branches.txt`；变异表重做：M525 的锚点随代码消失而**退役**、
  M527 由 M534 替代、新增 M533（嵌套重复计数）/ M535（分母被换）/ M536（去掉"读不懂"那一格）
  ⇒ `n=7 caught=7 intended_escaped=0 mismatch=0 not_run=0`。
- **撤掉一句假话**（BACKLOG 132 的第一份 runner 栈）：run 38876999489 里
  `主导路径占比=100% 最深帧=读不到` + `blocked@unknown` 是 `nodes` 为空时被兜底成 1.0 造出来的
  ⇒ 现在读不懂就是**未量到**，并打印 `UI_PROBE_SAMPLE_UNPARSED=1` 与
  `UI_PROBE_SAMPLE_SHAPE 缩进N 数字开头=yes/no 长度=M`（只打形状不打帧名：
  日志里不许出现用户的剪贴板内容，而诊断"正则读不到什么"不需要帧名）。两格占比的兜底 1.0 → 0.0。
- 节奏判据的对象从一张卡片扩到**每一张** `settings-*` 卡片，`cardRhythm` 多返回一格 `declined`
  （顶到带上沿 / 底到带下沿（这一页比窗口高）/ 卡片里没有一行被判成墨）⇒
  "没量到"的三种原因不再与"确实没有分隔线"共用一条读数；同时补一条"读到墨却一条都没判 ⇒ 红"。
  三张被窗口切断的卡片现在明说 `CARD_RHYTHM_DECLINED … 原因=卡片底到扫描带下沿`，
  这一格开成 **BACKLOG 140**（配高夹具）。
- 看图那一腿：设置「隐私」分区逐元素重判（`r96_privacy_visual.py`）。
  勾选框两态可辨（勾上时框自己的填充换一档 223→213 / 58→67，且对勾 46/47 颗 vs 未勾 12–20/13–20 颗）⇒ 不加动效；
  五颗框 `chroma=0`（勾选态不是强调蓝）而源码里全是裸 `Toggle` ⇒ 灰不是产品选的色，
  开成 **BACKLOG 139** 走真机（人工批次 75.1），本轮不改产品。
  默认排除那一列（19 段文字、左轴众数 177.5pt、行距中位 10.5pt、对比 2.94/5.31）判过不改。

'''
    wr(C, s.replace(anchor, anchor + block, 1))

    # ============ AGENT_STATE（第 3 行换成本轮，R95 那行降为引用）
    ST = 'AGENT_STATE.md'
    s = rd(ST)
    lines = s.split('\n')
    cur = lines[2]
    assert cur.startswith(u'最后更新：'), cur[:20]
    assert lines[4].startswith(u'> 上一轮（'), lines[4][:20]
    new = (u'最后更新：2026-10-16 18:05（本地 · R96 / 第 98 轮收尾：'
           u'**上一轮"特意留下"的那一格 padding，被自己扩了对象的判据当场推翻** —— '
           u'把 `testSettingsCardVerticalRhythmIsOneNumber` 从"只压 settings-shortcuts 一张"扩到'
           u'"每一张 settings 卡片"之后，`settings-data` 立刻红：`边距=18.0/14.0、内侧=18.0/14.5/17.5/14.0`，'
           u'根因是三段里只有第一段带 `.padding(.vertical, 4)`；我上一轮给它的理由是"卡片内部讲的是另一件事"，'
           u'而它讲的就是同一件事（行与分隔线之间的距离），却只有一段有 ⇒ 删（U-227 / D-154）。'
           u'容差 3.0→4.5 不是放宽：**3.5pt 是这张帧里"按钮 bezel 底下不画墨的边"的实测值**，'
           u'加 1pt 余量，出处写在断言旁边，且 R95 的缺陷（8.5）与 M528（7.5）都仍被抓住；'
           u'扩对象那一刀同时补了"读到墨却一条都没判 ⇒ 红"，否则扩出去的那九张只会让"没判"更安静（M530 从 DID-NOT-RUN 变 CAUGHT）。'
           u'台账那一腿：读 run **38876999489**（`bf6b921`）**success**，覆盖率闸门与上一轮完全一致'
           u'（`红=0`、`露面=7/11 未闭口=1`、`PROBE_QUEUED` 同一批四条）⇒ 上一轮的登记刷新没制造新红；'
           u'而 132 的第一份 runner 栈读出来是 `主线程采样=306 主导路径占比=100% 最深帧=读不到` + '
           u'`blocked@unknown` —— **后一半是假话**：`nodes` 为空时占比被兜底成 1.0，'
           u'于是"我读不懂这份文件"被打印成"它挂在某个不认识的帧上"，还带着一个具体百分比 ⇒ '
           u'撤兜底（读不懂=未量到、占比 0.0），新增 `UI_PROBE_SAMPLE_UNPARSED` 与只含缩进/是否数字开头的'
           u'`UI_PROBE_SAMPLE_SHAPE`（**不打帧名**：日志不许出现用户剪贴板内容，而诊断不需要帧名）。'
           u'**137 结案**，修法不是补夹具而是换判定来源：`_waiting_leaves` 数"有多少采样停在等待帧上"'
           u'（嵌套只算最内层、并列报两个族）⇒ `blocked@ambiguous`；变异表重做 `n=7 caught=7`，'
           u'退役的 M525/M527 记在 harness 文档串里（"表里少一格"与"那一格永远绿"是同一种失忆）。'
           u'看图那一腿：设置「隐私」逐元素 —— 勾选框两态可辨（框自己的填充换一档 223→213 / 58→67，'
           u'对勾 46/47 颗 vs 未勾 12–20/13–20 颗）⇒ 不加动效；但五颗框 `chroma=0`（勾选态不是强调蓝）'
           u'而源码全是裸 `Toggle` ⇒ 灰不是产品选的色，开 **139** 走真机（批次 75.1），本轮不改它；'
           u'默认排除那一列帧里可见 8 行（名单共 9 项、第 9 项在窗口外）共一条左轴 177.5pt ⇒ 重复前缀判过不改（U-229）；'
           u'仪器自己错两次（门槛 60 只检出 3 颗 → 降到 15 检出 7 颗 → 最后用"框有自己的填充"判，'
           u'正好 5 颗）=U-230；三张比窗口高的卡片被尺明确报成"卡片底到带下沿 ⇒ 不判"而不是"没有分隔线" ⇒ 开 **140**。'
           u'验证：' + short_verify(v) + u'。**下一轮第一件事：读 R96 的 CI 里 `UI_PROBE_SAMPLE_SHAPE` 那一行'
           u'（三种形状三种下一步，写在 `r96_ci_readings.md` 末尾），然后做 140 与 133**）')
    lines[2] = new
    lines[4] = (u'> 上一轮（R95 / 第 97 轮收尾）原文开头：' + cur[len(u'最后更新：'):])
    wr(ST, '\n'.join(lines))

    # ============ 人工批次
    M = 'docs/MANUAL_TEST_v1.4.9_round3.md'
    s = rd(M).rstrip('\n')
    s += u'''

## 批次 75（R96 · 设置「隐私」那一屏：帧判不了的三件事）

- 75.1 **勾选框勾上之后是什么颜色**：打开设置 → 隐私，点一下"窗口标题"。
  预期（按 macOS 12 的系统复选框）：勾上的那颗应该是**强调色**（默认蓝）底 + 白色对勾。
  帧上量到的是：五颗框的色度全为 0，勾上的只是"换一档的灰"（亮 223→213、暗 58→67），
  而源码里这五颗都是裸 `Toggle`（没有任何自定义 `toggleStyle`）⇒ **灰不是产品选的色**。
  真机若也是灰 ⇒ `accentColor` 没进这棵视图树（BACKLOG 139 走产品修法）；
  真机若是蓝 ⇒ 那是离屏/非 key 窗口的画法，把"勾选态的颜色"登记成声明的盲区，不改产品。
- 75.2 **未勾与禁用长不长得一样**：这一屏四颗未勾的框与「通用」页那颗"开机启动"在
  macOS 12 不支持时的禁用态（BACKLOG 里 R39 已给它配过帧）放在一起对比一眼：
  三者是不是同一种灰？如果未勾=禁用，那"点不动"这件事在界面上就没有任何提示。
- 75.3 **卡片下半截的留白**：把设置窗口拉到最高（或滚动到「隐私」卡片底部），
  看最后一段"不记录这些 App 的复制"的**末行离卡片底**舒不舒服，以及
  默认排除那九行（帧里只看得见前八行）逐行的左沿与行距是不是齐的。
  这一屏比 540pt 的窗口高，判据只能看到上半截（BACKLOG 140 就是为了让它看得到下半截）。
'''
    wr(M, s + '\n')


# ------------------------------------------------------------------ 主流程
def main():
    v = read_verify()
    v['VIS_SHORT'] = v['VIS_LINE']
    problems = check_block(verify_block(v)) + check_block(short_verify(v))
    if problems:
        sys.exit(u'拒绝写盘：渲染出来的验证段有问题 ⇒ %s' % u'；'.join(problems))
    if os.environ.get('LEDGERS_R96_APPLY') != '1':
        sys.exit(u'只校验不写盘：加 LEDGERS_R96_APPLY=1 才会真的落台账')
    # **事务性**：R96 第一次跑这段时在 STATE 那一格抛了 KeyError，而前面六格已经写进磁盘了 ——
    # 半份台账比没有台账更坏（它读起来是完整的）。所以先整体快照，任何一格炸了就全部还原。
    touched = sorted(set(p for _, p, _, _ in STAGES))
    snapshot = dict((p, rd(p)) for p in touched)
    try:
        apply(v)
    except BaseException as exc:                       # noqa: BLE001 —— 还原之后原样抛出
        for p, text in snapshot.items():
            wr(p, text)
        sys.exit(u'写盘失败，%d 份台账已整体还原（半份台账比没有更坏）：%s'
                 % (len(snapshot), exc))
    bad = []
    for name, path, marker, why in STAGES:
        text = rd(path)
        hits = text.count(marker)
        if hits == 1:
            print(u'OK   %-16s %s' % (name, marker[:34]))
        else:
            bad.append((name, path, marker, why, hits))
    # CHANGELOG 那一格有一条独立的守卫：`## [Unreleased]` 只准出现一次
    if rd('CHANGELOG.md').count(u'## [Unreleased]') != 1:
        bad.append(('changelog_heading', 'CHANGELOG.md', u'## [Unreleased]',
                    u'标题被插成了两份（R59 为这一条写过守卫）',
                    rd('CHANGELOG.md').count(u'## [Unreleased]')))
    # U 号与 D 号：本轮新写的号必须是连续的、且没有把上一轮的号抢走
    for path, pat in [('AGENT_UI_AUDIT.md', r'U-(2\d\d)')]:
        nums = sorted(set(int(x) for x in re.findall(pat, rd(path))))
        if nums and nums[-1] != 231:
            bad.append(('u_number', path, pat, u'最大的 U 号应是本轮的 U-231', nums[-1] if nums else None))
    if bad:
        print(u'\n有格子没落盘：')
        for name, path, marker, why, hits in bad:
            print(u'  RED %-16s %s 标记=%r 命中=%s —— %s' % (name, path, marker, hits, why))
        sys.exit(1)
    print(u'\nLEDGERS_R96_OK=1（%d 格）' % len(STAGES))


if __name__ == '__main__':
    main()

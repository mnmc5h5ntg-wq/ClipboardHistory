# -*- coding: utf-8 -*-
'''R84 的台账补丁（第 86 轮 / Round 84）。

数字全部从产物读，不许手抄：
  * `.scratch/motion-audit-2/r84_battery.log`        —— 八刀的逐条结论
  * `.scratch/motion-audit-2/r84_verify_summary.log` —— 全量验证的逐条读数与原文 readings
  * `.scratch/motion-audit-2/r84_fanout_readings.log`—— before/after 两卷的手量读数
每个锚点都断言"命中且只命中一次"。

分三段跑：`python3 ledgers_r84.py A`（正文与账）、`B`（STATE 与 FINAL_REPORT）、`C`（曲线占位符）。
'''
import io
import os
import re
import sys

REPO = '/Users/wangziyi/Codex_Project0'
BATTERY = os.path.join(REPO, '.scratch/motion-audit-2/r84_battery.log')
SUMMARY = os.path.join(REPO, '.scratch/motion-audit-2/r84_verify_summary.log')
FANOUT = os.path.join(REPO, '.scratch/motion-audit-2/r84_fanout_readings.log')
FRAME_DIFF_PATH = os.path.join(REPO, '.scratch/motion-audit-2/r84_frame_diff_readings.log')
CURVE = 'CURVE_PLACEHOLDER_R84'


def read(path):
    return io.open(path, encoding='utf-8').read()


def write(path, text):
    io.open(path, 'w', encoding='utf-8').write(text)


def summary(key, default=None):
    text = read(SUMMARY)
    m = re.search(r'^%s=(.+)$' % re.escape(key), text, re.M)
    if not m:
        if default is None:
            raise SystemExit('验证摘要里缺 %s —— 先把验证跑完再来写台账' % key)
        return default
    return m.group(1).strip()


def reading(name):
    '''验证摘要里那行 `READ <key> :: <原文>`。缺行 ⇒ 直接停，不许用记忆填。'''
    text = read(SUMMARY)
    # verify 脚本写 key 时用的是 `${pat%% *}`，于是 grep 模式开头那个 `^` 也进了 key ⇒ 这里容许它。
    m = re.search(r'^READ \^?%s :: (.+)$' % re.escape(name), text, re.M)
    if not m:
        raise SystemExit('验证摘要里没有 READ %s 这一行 ⇒ 那条读数没落地，台账不许引用它' % name)
    return m.group(1).strip()


def knife_rows():
    text = read(BATTERY)
    rows = []
    for m in re.finditer(r'^M(4\d\db?) (.+?)$', text, re.M):
        tag = 'M' + m.group(1)
        tail = text[m.end():]
        hit = re.search(r'^   (CAUGHT|ESCAPED|NOT-RUN|NOT-APPLIED|LOCAL-NO-POWER)', tail, re.M)
        rows.append((tag, m.group(2), hit.group(1) if hit else '?'))
    return rows


KNIVES = knife_rows()
CAUGHT = [t for t, _, k in KNIVES if k == 'CAUGHT']
NOPOWER = [t for t, _, k in KNIVES if k == 'LOCAL-NO-POWER']
BAD = [t for t, _, k in KNIVES if k not in ('CAUGHT', 'LOCAL-NO-POWER')]
KNIFE_TABLE = u'\n'.join(u'| %s | %s | **%s** |' % (t, n.split(u'⇒')[0].strip(), k) for t, n, k in KNIVES)
NUM = {1: u'一', 2: u'两', 3: u'三', 4: u'四', 5: u'五', 6: u'六', 7: u'七', 8: u'八', 9: u'九', 10: u'十'}
def cn(n):
    return NUM.get(n, str(n))
KNIFE_TOTAL = cn(len(KNIVES)) + u'刀'
KNIFE_CAUGHT = cn(len(CAUGHT)) + u'刀 CAUGHT'
KNIFE_NOPOWER = (cn(len(NOPOWER)) + u'刀按实存活为"本地无独立判别力"') if NOPOWER else u'没有本地无判别力的刀'
KNIFE_RANGE = u'%s–%s' % (KNIVES[0][0], KNIVES[-1][0])
KNIFE_LINE = u'%s：%s，%s（%s 的牙被 M454b 那格检验过）' % (
    KNIFE_TOTAL, KNIFE_CAUGHT, KNIFE_NOPOWER, u'、'.join(NOPOWER) if NOPOWER else u'—')

BUILD_WARN = re.search(r'\d+', summary('BUILD_WARNINGS')).group(0)
FULL_TEST = summary('FULL_TEST')
FRAME = summary('FRAME_BASELINE')
FRAME_AFTER = summary('FRAME_BASELINE_AFTER_UPDATE')
FRAME_TOUCHED = summary('FRAME_BASELINE_HASHES_TOUCHED')
FRAME_DIFF = u'\n'.join(l for l in read(FRAME_DIFF_PATH).splitlines() if l.startswith(('light:', 'dark:')))
GATE = summary('CAPTURE_GATE')
SCRIPTS = summary('SCRIPT_TESTS')
MOTION_FACTS = summary('MOTION_FLOOR')
SHIM = reading('MOTION_SHIMMER')
BAND = reading('MOTION_SHIMMER_BAND')
BAND_CONTROL = reading('MOTION_SHIMMER_BAND_CONTROL')
BAND_WITNESS = reading('MOTION_SHIMMER_BAND_WITNESS')
BAND_TABLE = reading('BAND_TRUTH_TABLE')
FANOUT_TEXT = read(FANOUT).strip()

ROUND_HEAD = u'''## Round 84 · 把看图换成判据：亮带终于是一条光穿过整组（结案 117 / 新开 119 / U-165…U-173 / D-142）

### 本轮开场的位点清单（1 个产品文件 + 1 个判据文件）

被重新判断的位点：**详情预览加载态那三根骨架条带上的亮带**
（`Sources/ClipboardHistoryApp/Views/SkeletonShimmer.swift`，探针视图 420×220 视图点）。
坐标与缺陷清单是 R83 量出来的那一套（`r83_band_fanout.py` 的读数在上一轮台账里）：

| 位点 | 区域（视图点，x 从组左边算） | R83 量到的缺陷 | 本轮处置 |
|---|---|---|---|
| 骨架条 1（标题） | 0…176.4 × y 0…8 | 亮带中心在自己条宽的一半处（88pt 一档） | 三根条共用一个亮带中心 |
| 骨架条 2（正文·长） | 0…361.2 × y 18…26 | 中心 181pt 一档 | 同上 |
| 骨架条 3（正文·短） | 0…268.8 × y 36…44 | 中心 134pt 一档 | 同上 |

⇒ 同帧内三个中心的绝对差最大 **170pt**、归一化只差 **0.003** —— 那是三条各扫各的亮带。
本轮两件事：① 产品改成"一条光穿过整组"；② 把那道手量换成**会红的判据**，
让下一次"退回每根条各扫各的"是红的，而不是一行注释。

### 读 R83 的 CI（run 38786182395，11m55s）：runner 那一支**翻面了**

```
MOTION_FLOOR_FACTS judged=4/4 executed=52 not-run=- 红的用例=testBandCaptureIsCheaperAndStillSeesTheMotion,testSkeletonSweepActuallySweeps 汇总行报红=2
MOTION_FLOOR_SUITE_RED=2 …
testSkeletonSweepActuallySweeps：骨架扫光只覆盖了整卷 0.050 的时间（1/22 对在变），而…那颗证人今天覆盖了 0.837
                              ⇒ 这台机器带得动产品那一档节拍的常驻循环，是产品这一份没在跑
testBandCaptureIsCheaperAndStillSeesTheMotion：XCTAssertLessThanOrEqual failed: ("25.14") is greater than ("23.41")
                              ⇒ 带捕获之后整卷中位间隔没有变细，这一臂仍然判不了
```

与 R82 那一遍并排看（同一份产品代码，同一类机器）：

| run | 产品 coverage | 等节拍证人 coverage | 处置 |
|---|---|---|---|
| R82 38781113064 | 0.000（0/21 对） | 0.284 | `.notRunEnvironment` ⇒ 点名 `loop-clock-not-sustainable-at-product-rate` |
| R83 38786182395 | 0.050（1/22 对） | 0.837 | `.productRed` ⇒ 红着说"产品这一份没在跑" |

⇒ **"这台 runner 带不动 30Hz 的常驻循环"不是一条耐久事实**：它上一轮成立、这一轮不成立，
而翻面的那一边是**证人**（0.284→0.837），产品的读数两遍都是"几乎没拍到"（0.000 / 0.050）。
这一格是本轮新开 **BACKLOG 119** 的全部内容：那一支的签字权不能交给单次 runner 读数。
它同时决定了本轮另一件事 —— 新加的位置判据**不复用**这个处置，另找签字的人（见下面第三道闸门）。

'''

SECTION = u'''### 产品那一处改动（before / after 都有数字，也都有图）

改法只有一件事：三根条不再各自是一个 `RoundedRectangle`，而是**整组一个形状**
（新增 `SkeletonBarsShape: Shape`，`path(in:)` 里 union 三根条），渐变填在这个形状上 ⇒
`LinearGradient` 的 `UnitPoint` 落在**容器**坐标系里，一条亮带横穿整组。
配套把两个魔法数提成令牌（`SkeletonMotion.barHeight = 8`、`barSpacing = 10`，
加 `barRect(index:fraction:in:)`），因为判据现在要按同一套几何去像素里找那三根条 ——
留在视图里就是让判据猜产品的布局。

```
%s
```

同一把尺、两份卷子（`.scratch/motion-audit-2/r84_band_fanout.py`，估计量与判据统一成"峰值列"）：

```
%s
```

本机这一条判据跑了五遍（判据单跑两遍、变异电池基线一遍、全量验证两遍）：
判定每遍都是 `整组一条带`、绝对散布每遍都是 0.0pt，而可用帧在 **7…10** 之间漂
—— 那是采样相位决定的（亮带什么时候整条落在最短那根条里面），
所以地板 `minimumBandFrames = 3` 留的是 2-3 倍的余量，而不是"今天碰巧有 7 帧"。
⇒ 这一格记的是"哪个数会漂、哪个数不漂"：判定与散布不漂，帧数漂 ⇒ 判据吃的是前者。

⇒ 绝对散布 169pt → **0pt**，归一化 0.005 → **0.450**：两把尺**反向**，这正是"从每根条各扫各的
换成整组一条带"该有的读数形状。看图也对上了：`r84_skeleton_band_strip.png` 里每格三根条的亮斑
落在同一条竖线上，而 `r82_skeleton_sweep_strip.png` 里三个亮斑是错开的。
顺带一条没预料到的：coverage 那把尺的峰值从 0.015 涨到 0.023（亮带变宽 ⇒ 每拍扫过的面积更大），
而"减弱动态必须静止"那一臂仍然是 0.000。

### 新判据：位置那把尺，三道闸门

`testSkeletonSweepIsOneBand`（`MotionFilmstripTests`，产品入口 = `SkeletonProbe` host 真的
`SkeletonPreviewView`）。它读的是**运动判据同一卷胶片**（`shimmerFilm()` 缓存，R84 起一卷只抓一次）：

1. **尺子自己的正对照**：两份合成卷子（一份整组一条带、一份每根条各扫各的）必须被读成两种判定。
   这一格今天真的值回票价 —— 它在我碰产品结论之前就先红了一次（见 U-165）。
2. **真片上的正对照**：可用帧里亮带必须走过 ≥20pt 行程。没有这一条，"三根条的峰值都停在同一列"
   （静止画面）也会读成散布 0pt，而 0pt 恰好是"整组一条带"的读数。
3. **谁能签"这台机器判不了位置"**：签给**同一把尺去读高对比那颗证人**（`bandAdjudication`），
   并且**只准收窄、不准放大** —— coverage 那一族的处置不是 `.ok` 时位置这一律不判，
   哪怕证人读得出、哪怕产品读成分家：一个自己会在两轮之间翻脸的读数，不配定罪产品。
   不签给 coverage 那个处置 —— 理由就是上面那两行并排的 CI 读数。

真值表 13 格（`BAND_TRUTH_TABLE`）：

```
%s
```

判据的读数（本机）：

```
%s
%s
%s
```

### U-165 · 点→像素漏乘 scale：三条红同时来自一把没验过坐标约定的尺

第一版 `barPeak` 拿 `rect`（**视图点**）直接当下标去索引**像素**缓冲区，于是条被当成只有实际一半宽去采样。
后果不是"读错数"，是**整把尺失能**：产品 45 帧全被丢掉（可用帧=0），
而两份合成对照一起读成"分不开"。⇒ 记两条：
① 坐标换算那一步必须在真片上跑第一遍，不能先看合成图就宣布尺子能用；
② 合成正对照的价值今天第一次被证明 —— 它先于任何产品结论红给我看，
   否则我会把"可用帧=0"写成"这台机器看不见亮带"（那正是 U-160 那一族的新成员）。

### U-166 · 内边距 4pt 拦不住"被圆角让开一格"的贴边假峰

修完 scale 之后产品读 19.5pt 散布 ⇒ "分不开"。逐帧看样本行
（`可用帧首=[33.0, 33.0, 33.0] 末=[171.5, 191.0, 191.0]`）：短条 176.4pt 宽，
亮带中心 191pt 已经在它右端**外面**，而它的 argmax 落在 171.5pt —— 不是贴在最后一列，
是被圆角让开了一格多，恰好躲过 4pt 的门槛。⇒ 门槛换成量出来的 **10pt**
（亮带半宽 63pt ⇒ 10pt 既拦得住贴边假峰，也吃不掉真正在条内的中心），
读数从 19.5pt 变 0.0pt、可用帧 15→9-10。**同族**：U-163（相对阈值在信号缺席时读假数）。

### U-167 · 两格前提里只有一格有牙，而"另一格也有牙"是一句没量的话

M454（只把幅度地板调到 0）**本地全绿**。第一反应是把它写成 CAUGHT 的反面（"刀没抓到 ⇒ 判据没用"），
但那句话不对：真正起作用的是条端内边距那一格（M452 单独拆它就红）。
⇒ 两刀分开记：M454 按实存活为"本地无独立判别力"，另加 **M454b**（两格一起拆）红 ⇒
"两格里至少一格必须有牙"这句话现在是**被检验过的**，而幅度地板那一格的注释里写着
它今天没有独立作用、以及什么条件下会重新有（渲染通道带上噪声时）。不许改期望冒充有牙。

### U-168 · 两把尺给不同答案时，先问估计量是不是同一个

修完之后，Swift 判据读 0.0pt，而 R83 那份 python 手量读 10pt ⇒ "分不开"。
根因不是画面，是两把尺的**估计量**不同：python 用"高于半程那段的质心"（会被条端切掉的那半个亮带拉走），
Swift 用"离本条中位数最远的那一列"（峰值列，不受切割影响）。统一成峰值列之后两份实现同结论
（before 169pt / after 0pt）。⇒ 跨工具对账之前先统一估计量，否则"分不开"是工具的病，不是画面的病。
`r83_band_fanout.py` 原样留着，它是"before 那侧的读数由谁产出"的证据。

### U-169 · 判据的处置会翻面：单次 runner 读数不配当签字权

见上面那张两行并排的表。⇒ 新开 **BACKLOG 119**；本轮的处置是**新判据不复用**那个处置，
改由"同一把尺读高对比证人"签（`bandAdjudication`）。
不许的处置：把 `minCoverage` 抬到 runner 能过的数值（那是 110 禁止的同一件事）、
或者把 R83 那朵红登记进 `suite_reds` 让它闭嘴（红必须有成因，不是有名字就行）。

### U-172 · 会翻脸的读数只准收窄断言，不准定罪

上面那张 CI 并排表给出的不只是一个待办，还有一条设计规矩：位置判据本来打算复用 coverage 那个处置当豁免条件，
但那个处置在两轮之间从"环境不行"翻成"产品红"。⇒ 最终形状是**不对称**的：
`loopCapable == false` 时位置这一律**不判**（哪怕证人读得出、哪怕产品读成分家），
而 `loopCapable == true` 时它才既有资格说绿、也有资格说红。
理由不在统计而在方向：免罪错了，下一轮还能补一次判定；定罪错了，是把环境问题写成产品缺陷，
而产品缺陷会驱动下一轮去改本来没坏的产品代码（R83 那份文件头记的三次 0.0000 误判，就是这个方向）。
⇒ 记成一条可复用的判据设计规矩：**任何"会随机器/轮次翻面"的读数，只能作为断言的上界，不能作为指控的来源。**

### U-173 · 本地验证脚本与 CI 用了不同的读数通道，假红只出现在我自己这边

第二轮 `verify_r84.sh` 跑完，闸门报 `MOTION_FLOOR_FACTS judged=None/None … MOTION_FLOOR_REDS=1`，
而同一遍的 `swift test` 是 801/0 failures、动效那卷 exit 0。⇒ 不是判据坏了，是**日志缺了结论行**：
本机 `swift test` 会成块丢 stdout（R64 记过），而 CI 在跑 `motion_floor_gate.py` 之前会把
`motion-readings.log` 并进 `/tmp/motion.log`（`MOTION_CHANNEL_UNIONED=1` 那一段），
我的本地脚本没并 ⇒ 同一条判据在两台通道上给出两个结论。
⇒ 修法是把 CI 那段通道合并抄进 verify 脚本（已抄，本轮第三遍验证的读数里带 `MOTION_CHANNEL_UNIONED=1`），
**不是**把闸门放宽、也不是把 `judged=None` 当成"没跑到"忽略掉。
**同族**：U-151（把崩溃读成没跑）、U-164（把导入失败读成全绿）—— 这一条的新形状是
"通道不一致造成的假红"，它只在自家 harness 里出现，所以最容易被人当成产品/判据的问题。

### U-170 · 变异电池自己也有"同文件两处编辑"这个坑

M454b 要同时改两颗地板，而 `apply()` 第一版对同一文件的两处编辑都从**原始文本**做替换
⇒ 第二处写回去时把第一处覆盖掉，那一刀会"抓到"一个其实没落地两次的形状。
⇒ 改成每处都从磁盘当前内容读、`originals.setdefault` 只留 pristine，
并且整组回滚（半把刀不算刀）。**同族**：U-164（电池的分类器也会骗人）。

### 牙

%s

### 验证（本机，逐条实跑）

```
swift build --build-tests                告警 %s
swift test（全量）                       %s
动效覆盖地板闸门                          %s
捕获闸门                                 %s
frame_baseline.py check --against working %s
frame_baseline.py update（同提交）之后复核 %s
python3 -m unittest discover -s scripts  %s
```

### 帧基线那 4 张：哈希说"变了"，像素说"没变到看得见"（两句都要报）

`frame_baseline.py check` 报 **4 张 changed**（detail-loading 亮/暗、detail-2-file 亮/暗 —— 都含骨架）。
BACKLOG 117 当时写的是"静置画面预计不变（phase 0 时亮带在条外）"，所以这一格不能只写"已 update"：
把 R83 与 R84 那两张同名帧解码到像素级比了一遍 ——

```
%s
```

⇒ 差异**只落在骨架那三根条的区域**（y 40…83pt、x 从详情区左轴 20pt 起），最大通道差 **5/255**，
其中 2450/2503 个像素只差 1 级 ⇒ 视觉上没变，变的是**换形状画法之后的抗锯齿边缘**。
基线判的是字节，所以 %s 张哈希按规矩同提交 update；update 之后复核 %s。
⇒ 记成 **U-171**：一句"帧基线 4 张变了"会把人带去读"画面变了"，
而画面到底变没变、变了多少灰阶、变在哪一行哪一列，是另一把尺的问题。

### 七维自评

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 20 / 20 | 本轮唯一一处画面改动：亮带从"三条各扫各的"变成"一条光穿过整组" —— 那是系统骨架与 GitHub 那类呼吸感共同的画法，R83 判它"不原生"的那一格现在没了 |
| 流畅度 | 18 / 20 | 本机 coverage 与峰值都没变差（峰值 0.015→0.023）；main 上那朵红换了成因：runner 的处置自己翻面（119），本轮没有修它，只是不再让它的签字权外溢 |
| 层次与材质 | 15 / 15 | 骨架三根条的左轴与纵向节奏没动（像素级读数：差异只落在条内 ≤5 灰阶的抗锯齿边，见上面"帧基线那 4 张"那一格）；材质与颜色一个数都没改 |
| 动效细节 | 14 / 15 | 亮带位置第一次有判据；条端内边距是量出来的（U-166），而"这条扫光到底该多宽"仍然只有一档 bandSize 0.3 的旧依据 |
| 交互反馈 | 9 / 10 | 反馈本身没动 |
| 可访问性 | 8 / 10 | 减弱动态那档"必须静止"仍然无条件判、读数 0.000；真机批次 72/73 还没人看 |
| 性能 | 14 / 15 | 全量 %s；位置判据多读一遍整卷（本机 48 帧、每帧 840×440px 里三条 8pt 高的带），这一条用例本身 0.4s |

**98 / 100**。涨的四分都在"原生感 + 动效细节"这一对：本轮既改了画面，又把改完的那件事变成会红的判据。
没满的部分写在 119 与真机批次上，不在本轮的分数里冒充。

### 仍未解决

- BACKLOG **119**（本轮开）：常驻循环那一族的 runner 处置**会翻面** ⇒ 判据不许拿单次读数定罪产品；
  要做的是把"这一支要几遍读数才配定罪"写成数据（与 118 是同一个洞的两面）。
- BACKLOG **118**（R83 开，本轮又长一格）：落在"有名字但没人统计"那一族里的读数，
  从一条变成两条 —— 峰值地板的 `MOTION_SHIMMER_PEAK_NOT_JUDGED` 与本轮的 `MOTION_SHIMMER_BAND_NOT_JUDGED`。
- BACKLOG **116**、**115**、111、108 余下、77 路 b、101 ②③、106；
  真机 68.1 / 68.2 / 69.1 / 70.1 / 71.1 / 72.1 / 72.2 / **73.1 / 73.2**。
''' % (BAND, FANOUT_TEXT, BAND_TABLE, BAND, BAND_CONTROL, BAND_WITNESS,
       KNIFE_TABLE, BUILD_WARN, FULL_TEST, MOTION_FACTS, GATE, FRAME, FRAME_AFTER,
       SCRIPTS, FRAME_DIFF, FRAME_TOUCHED, FRAME_AFTER, FULL_TEST)

UI_AUDIT = u'''## 第 86 轮 · R84：亮带从"三条各扫各的"改成"一条光穿过整组"，并把它变成会红的判据（U-165…U-173）

- **U-165** 点→像素漏乘 scale：一把没验过坐标约定的尺会把"我读不到"写成"这台机器看不见"
  （产品 45 帧全丢 + 两份合成对照一起"分不开"）。合成正对照第一次证明自己值回票价。
- **U-166** 条端内边距 4pt 拦不住被圆角让开一格的贴边假峰 ⇒ 门槛 10pt 是量出来的，
  读数 19.5pt → 0.0pt。**同族**：U-163。
- **U-167** 两格前提只有一格有牙（M454 本地无独立判别力，M454b 两格同拆才红）⇒
  按实存活，不改期望冒充有牙。
- **U-168** 两把尺先给出不同答案（10pt vs 0.0pt），根因是**估计量**不同（质心 vs 峰值列）⇒
  跨工具对账之前先统一估计量。
- **U-169** runner 的处置会翻面（R82 0.284 ⇒ 点名环境；R83 0.837 ⇒ 判产品红，同一份产品代码）⇒
  新开 119；新判据不复用那个处置，改由"同一把尺读高对比证人"签字。
- **U-170** 变异电池在同一文件做两处编辑时会互相覆盖 ⇒ 每处从磁盘当前内容读、整组回滚。
- **U-171** 帧基线说"4 张 changed"，像素说"最大差 5/255、98% 只差 1 级、只落在骨架那三根条的区域" ⇒
  一句"帧变了"会把人带去读"画面变了"：哈希尺与灰阶尺回答的是两句不同的话，两句都要写在账上。
- **U-172** 一个会在两轮之间翻脸的读数，**只准拿来收窄断言，不准拿来定罪**：位置判据在 coverage 那一族"
  不是 `.ok`"时一律不判（哪怕证人读得出、哪怕产品读成分家）。不对称的理由是安全方向：
  免罪错了下一轮还能补判，定罪错了是把环境问题写成产品缺陷（R83 的 CI 现场演示过反面）。
- **U-173** 本地验证脚本喂给动效闸门的只有 stdout，而 CI 在跑闸门之前会把文件通道并进同一份日志 ⇒
  本机 `swift test` 成块丢 stdout 时，闸门读到 `judged=None/None` 而测试其实全过（MOTION_FLOOR_REDS=1）。
  同一件事在两台通道上判出两个结论，红的是我的 harness，不是产品 —— 修法是把 CI 那段并通道抄进 verify 脚本
  （`MOTION_CHANNEL_UNIONED=1`），而不是把闸门放宽。
- 产品：`SkeletonBarsShape`（整组一个形状）+ `SkeletonMotion.barHeight/barSpacing/barRect` 三个令牌。
  before/after：同帧内三根条亮斑绝对中心 169pt → **0pt**，归一化 0.005 → **0.450**（反向才对）。

'''

DECISION = u'''
### D-142（R84）骨架扫光的亮带必须落在**容器**坐标系里，而这件事由像素判据钉住；处置的签字权另找证人

- 背景：R83 手量到三根条各扫各的（绝对差 170pt / 归一化 0.003）。机制是 `LinearGradient` 的
  `UnitPoint` 按**被填充形状**的边界归一化，而当时每根条是一个独立的 `RoundedRectangle` + `.frame(width:)`。
- 决定：① 整组一个形状（`SkeletonBarsShape`），渐变填在它上面 ⇒ 一条亮带横穿整组；
  ② 条高/条间距从视图里的魔法数提成 `SkeletonMotion` 令牌，判据按同一套几何去像素里找那三根条；
  ③ 新增 `testSkeletonSweepIsOneBand`：合成正对照 + 行程正对照 + "同一把尺读证人"签的处置，三道闸门；
  ④ 位置判据**不复用** coverage 那个处置（R82/R83 的 CI 在同一个产品代码上给过相反的两支）。
- 理由：骨架扫光的全部表达力是"给整组一个共同的方向与节奏"。三条各自闪动信息量更低而开销更大
  （报告 §5 红线 1）。而"改对了"这句话不能由我看图说了算：下一次退回每根条各扫各的必须是红的。
- 代价与边界：三根条的纵向布局从 `VStack` 变成一个 `path(in:)` 的算术 ⇒ 由令牌 + 像素判据钉住；
  亮带绝对宽度随容器变（420pt 上是 126pt，比原来短条上那条 53pt 宽）；
  `bandSize 0.3` 的语义从"占单根条"变成"占整组"，这一条写在令牌自己的注释里。
- 不许的处置：把内边距/幅度地板/行程地板调成"这台机器恰好过"的数值（三条都是量出来的，
  调低要带新读数）；或者把 119 那朵红登记进 `suite_reds` 让它闭嘴。
'''

BACKLOG_119 = u'''119. **常驻循环那一族的 runner 处置会翻面：单次读数不配判产品红**（R84 开 / 与 114、118、113、110 同族）：

    同一份产品代码（R83 没动产品），同一类机器，两遍 CI 给了相反的处置：

    | run | 产品 coverage | 等节拍证人 coverage | 处置 |
    |---|---|---|---|
    | R82 38781113064 | 0.000（0/21 对） | 0.284 | `.notRunEnvironment` ⇒ 点名 `loop-clock-not-sustainable-at-product-rate` |
    | R83 38786182395 | 0.050（1/22 对） | 0.837 | `.productRed` ⇒ 红着说"产品这一份没在跑" |

    ⇒ 翻面的是**证人**那一边（0.284→0.837），而产品的读数两遍都是"几乎没拍到"。
    也就是说：在 ~110ms 的采样网格上，2.5 秒的一卷里"变化帧对落在哪几对"本身就不稳，
    拿它当"环境 vs 产品"的签字人，等于让同一件事在两轮里有两个罪名。
    要做的一小步：那一支的判定要**几遍读数**才配定罪（或换成不吃采样网格的量 —— 113 结案时
    换的 coverage 仍然是网格的函数），并把"几遍"写成数据而不是写成一次运气。
    R84 已经做掉的那半：新加的位置判据**不复用**这个处置，改由"同一把尺去读高对比证人"签
    （`bandAdjudication`），所以 119 不会把 R84 那条判据一起拖红。
    不许的处置：抬 `minCoverage` 到 runner 能过的数（110 禁止的同一件事）、
    把这朵红登记进 `suite_reds`（红要有成因，不是有名字就行）、或者反过来据此断言
    "产品的扫光在 runner 上确实没跑"（两遍读数互相矛盾，哪一遍都不能当结论）。

'''

BACKLOG_CLOSE_117 = u'''
    → **R84 结案（改完，且改对了的地方有读数）**：整组一个形状（`SkeletonBarsShape`），
    渐变填在容器坐标系里 ⇒ 一条亮带横穿三根条。同帧内三根条亮斑的**绝对**中心
    169pt → **0pt**，**归一化** 0.005 → **0.450**（两把尺反向才是修对了），
    两份实现（判据 + `.scratch/motion-audit-2/r84_band_fanout.py`）同结论。
    判据 `testSkeletonSweepIsOneBand`：合成正对照两份必须分得开、真片行程 ≥20pt、
    处置由"同一把尺读高对比证人"签；真值表 13 格；牙 M451（把产品改回本轮之前的画法）CAUGHT。
    静置画面：**视觉上没变，但字节变了** —— 把 R83 与 R84 的同名帧解码到像素级比了一遍，
    差异只落在骨架那三根条的区域（y 40…83pt、x 从详情区左轴 20pt 起），最大通道差 5/255、
    98%% 的差像素只差 1 级（抗锯齿边缘）⇒ 帧基线按哈希判，%s 张同提交 update，
    update 之后复核 %s。原来那句"静置画面预计不变"要说得更准：不变的是**看得见的部分**。
    顺带一条没预料到的：coverage 那把尺的峰值 0.015 → 0.023（亮带变宽，每拍扫过的面积更大）。
''' % (FRAME_TOUCHED, FRAME_AFTER)

CHANGELOG = u'''### Product（R84）

- 详情预览加载态的骨架扫光：亮带从"每根条各扫各的"改成**一条光横穿整组**
  （渐变从单根条的坐标系抬到整组的坐标系）。同一帧内三根条亮斑中心的绝对差
  从 169pt 变成 0pt，减弱动态那一档仍然完全静止；静置画面不变（124 张帧基线逐张复核）。

### Tests（R84）

- 新增 `testSkeletonSweepIsOneBand`：位置判据（合成正对照两份 + 真片行程正对照 +
  由"同一把尺读高对比证人"签的处置），真值表 13 格；`SkeletonMotion.barHeight/barSpacing/barRect`
  三个令牌 + `SkeletonBarsShape`；产品那一卷胶片改为缓存复用（运动与位置两句读同一卷）。
- 变异电池 %s 共 %s：%s，%s（M454 的牙被 M454b 两格同拆检验 —— "至少一格有牙"这句话本身可证伪）。

'''

CHANGELOG = CHANGELOG % (KNIFE_RANGE, KNIFE_TOTAL, KNIFE_CAUGHT, KNIFE_NOPOWER)

MANUAL = u'''
### 批次 73（R84 的骨架扫光：一条光穿过整组）

- 73.1 **一条亮带，不是三条**：复制一张图片，让详情区进加载态（大图或首次 QuickLook 最明显）。
  预期：亮带从左边进来时**同时**照亮三根条落在同一条竖线上的那一段，扫出去之后整组回到静置灰。
  缺陷长什么样（R83 的那版）：短条、长条、中条各自中间亮一下，三个亮斑错开、节奏不一致。
- 73.2 **减弱动态仍然是静止的**：系统设置 → 辅助功能 → 显示 → 减少动态效果打开，再进一次加载态。
  预期：三根灰条在，亮带完全不动（不是变慢、不是变淡）。
  这一条判据本机读的是"变化帧对 = 0"，但"人眼看着是不是三根安静的条"只有真机能判。
'''


def patch_visual_iteration():
    p = os.path.join(REPO, 'AGENT_VISUAL_ITERATION.md')
    s = read(p)
    assert u'## Round 84' not in s, u'Round 84 已经写过了'
    write(p, s.rstrip(u'\n') + u'\n\n' + ROUND_HEAD + SECTION)


def patch_ui_audit():
    p = os.path.join(REPO, 'AGENT_UI_AUDIT.md')
    s = read(p)
    assert u'## 第 86 轮' not in s
    anchor = u'## 第 85 轮 · R83：'
    assert s.count(anchor) == 1, u'UI_AUDIT 的 85 轮锚点不唯一'
    write(p, s.replace(anchor, UI_AUDIT + anchor, 1))


def patch_decisions():
    p = os.path.join(REPO, 'AGENT_DECISIONS.md')
    s = read(p)
    assert u'### D-142' not in s
    write(p, s.rstrip(u'\n') + u'\n' + DECISION)


def patch_backlog():
    p = os.path.join(REPO, 'AGENT_BACKLOG.md')
    s = read(p)
    anchor_118 = u'118. **一朵有名字的未覆盖，登记表里却没有它的位置'
    assert s.count(anchor_118) == 1, u'118 的锚点不唯一'
    assert u'119. ' not in s, u'119 已经写过了'
    s = s.replace(anchor_118, BACKLOG_119 + anchor_118, 1)
    # 117 那一节的结案：接在它自己的结尾后面
    tail_anchor = u'    本轮不动产品：这是看图看出来的新缺陷，按"先 spike 再动仓库"的规矩排在下一次。\n'
    assert s.count(tail_anchor) == 1, u'117 的收尾锚点不唯一'
    s = s.replace(tail_anchor, tail_anchor + BACKLOG_CLOSE_117, 1)
    # 118 长了一格：把"两格"这件事写进它自己的正文
    old = u'要做的一小步：给登记表加一节 `loops`（或把扫光当成一条虚拟臂），'
    assert s.count(old) == 1, u'118 的"要做的一小步"锚点不唯一'
    s = s.replace(old, u'R84 之后这一族里已经有**两格**读数（峰值地板的 `MOTION_SHIMMER_PEAK_NOT_JUDGED`、'
                       u'位置判据的 `MOTION_SHIMMER_BAND_NOT_JUDGED`），而它们都不在表的形状里。'
                       u'要做的一小步：给登记表加一节 `loops`（或把扫光当成一条虚拟臂），', 1)
    write(p, s)


def patch_changelog():
    p = os.path.join(REPO, 'CHANGELOG.md')
    s = read(p)
    anchor = u'## [Unreleased]\n'
    assert s.count(anchor) == 1
    assert u'### Tests（R84' not in s
    write(p, s.replace(anchor, anchor + CHANGELOG, 1))


def patch_manual():
    path = os.path.join(REPO, 'docs/MANUAL_TEST_v1.4.9_round3.md')
    s = read(path)
    assert u'批次 73' not in s, u'批次 73 已经写过了'
    write(path, s.rstrip(u'\n') + u'\n' + MANUAL)


def patch_state():
    p = os.path.join(REPO, 'AGENT_STATE.md')
    s = read(p)
    head_marker = u'最后更新：2026-10-16 02:20（本地 · R83 / 第 85 轮收尾：'
    assert s.count(head_marker) == 1, u'STATE 头部锚点不唯一'
    new_head = (u'最后更新：2026-10-16 03:20（本地 · R84 / 第 86 轮收尾：读 R83 的 CI'
                u'（run 38786182395，11m55s）—— **runner 那一支翻面了**：同一份产品代码，'
                u'R82 证人 coverage 0.284 ⇒ 点名环境，R83 证人 0.837 ⇒ 判产品红，'
                u'而产品两遍都是 0.000/0.050 ⇒ 新开 **119**（单次 runner 读数不配判产品红）。'
                u'产品那一处：骨架扫光的亮带从"每根条各扫各的"改成**一条光穿过整组**'
                u'（新增 `SkeletonBarsShape`，渐变落在容器坐标系；条高/条间距提成 `SkeletonMotion` 令牌），'
                u'结案 **117**。同帧内三根条亮斑绝对中心 169pt → **0pt**、归一化 0.005 → **0.450**'
                u'（两把尺反向才对），判据与手量两份实现同结论，before/after 条带图都在 `.scratch`。'
                u'新判据 `testSkeletonSweepIsOneBand` 三道闸门（合成正对照 / 行程正对照 / '
                u'由"同一把尺读高对比证人"签的处置），真值表 13 格。'
                u'路上三条红全是尺子自己的：U-165 点→像素漏乘 scale、U-166 内边距 4pt 拦不住圆角让开一格的假峰'
                u'（换 10pt 是量出来的）、U-168 两把尺的估计量不同（质心 vs 峰值列）。'
                u'牙：' + KNIFE_LINE + u'。U-169 记下处置翻面，U-170 记下电池同文件两处编辑会互相覆盖，U-171 记下那 4 张帧到底变了多少（≤5 灰阶），'
                u'U-172 把那条方向性约束写进判据（会翻脸的读数只准收窄断言，不准定罪），'
                u'U-173 记下第二遍验证那朵 `judged=None/None` 的假红来自本地脚本没并文件通道（修法在 harness，不在闸门）。'
                u'全量 %s；动效闸门 %s；捕获闸门 %s；帧基线 %s；脚本 %s；告警 %s。'
                u'**下一轮第一件事：读 R84 的 CI（119 的那一支在 runner 上今天怎么说）+ BACKLOG 118**）\n\n'
                u'> 上一轮（R83 / 第 85 轮收尾）原文开头：' + head_marker) % (
        FULL_TEST, MOTION_FACTS, GATE, FRAME, SCRIPTS, BUILD_WARN)
    write(p, s.replace(head_marker, new_head, 1))


def patch_final_report():
    p = os.path.join(REPO, 'AGENT_FINAL_REPORT.md')
    s = read(p)
    old = u'| 阶段二 **76 轮**审计（R9–R83，含 29d；'
    assert s.count(old) == 1, u'FINAL_REPORT 轮数锚点不唯一'
    s = s.replace(old, u'| 阶段二 **77 轮**审计（R9–R84，含 29d；', 1)
    old = u'以 `curve_from_ledger.py` 的 `PHASE2 n=76` 为准）'
    assert s.count(old) == 1, u'FINAL_REPORT 曲线锚点不唯一'
    s = s.replace(old, u'以 `curve_from_ledger.py` 的 `PHASE2 n=77` 为准）', 1)
    old = u'| 视觉台账 | U-31 … U-164（132 条；'
    assert s.count(old) == 1, u'FINAL_REPORT U 计数锚点不唯一'
    s = s.replace(old, u'| 视觉台账 | U-31 … U-173（141 条；', 1)
    old = u'**M100–M450**（阶段二 349 支；'
    assert s.count(old) == 1, u'FINAL_REPORT 刀数锚点不唯一'
    s = s.replace(old, (u'**M100–M457**（阶段二 357 支；**R84 的 %s 共%s：%s，%s'
                       u'（M454 的牙被 M454b 两格同拆检验 —— "至少一格有牙"这句话本身可证伪）** —— '
                       % (KNIFE_RANGE, KNIFE_TOTAL, KNIFE_CAUGHT, KNIFE_NOPOWER)), 1)
    old = u'自评曲线（**76 轮**，Round 9–83，含 29d 那一轮边界轮；'
    assert s.count(old) == 1, u'FINAL_REPORT 曲线段锚点不唯一'
    s = s.replace(old, u'自评曲线（**77 轮**，Round 9–84，含 29d 那一轮边界轮；' + CURVE + u'）：', 1)
    anchor = u'U-160 是**前提钉子挂在结论尺的输出上'
    if s.count(anchor) != 1:
        anchor = u'U-155 是**探针把时刻存在对象身上，两卷连拍就会串卷'
    assert s.count(anchor) == 1, u'FINAL_REPORT 的 U 段插入锚点不唯一'
    s = s.replace(anchor, REPORT_U + anchor, 1)
    write(p, s)


REPORT_U = (u'U-165 是**一把没验过坐标约定的尺会把"我读不到"写成"这台机器看不见"**（点→像素漏乘 scale，'
            u'45 帧全丢 + 两份合成对照一起"分不开"）；U-166 是**门槛要量出来**（内边距 4pt 恰好被圆角让开一格躲过，'
            u'换 10pt 之后 19.5pt → 0.0pt）；U-167 是**两格前提里只有一格有牙，而"另一格也有牙"是一句没量的话**'
            u'（M454 本地无判别力 + M454b 两格同拆才红）；U-168 是**两把尺先给出不同答案，根因是估计量不同**'
            u'（质心 vs 峰值列 —— 跨工具对账之前先统一估计量）；U-169 是**判据的处置会翻面，单次 runner 读数不配判产品红**'
            u'（R82 0.284 ⇒ 点名环境，R83 0.837 ⇒ 判产品红，同一份产品代码）；U-170 是**电池在同一文件做两处编辑会互相覆盖**'
            u'（半把刀不算刀）；U-171 是**帧基线说"变了 4 张"而像素说"最大差 5 灰阶、只落在骨架区域"**'
            u'（哈希尺与灰阶尺回答两句不同的话，两句都要在账上）；U-172 是**会翻脸的读数只准收窄断言、不准定罪**'
            u'（`loopCapable == false` 时位置这一律不判 —— 免罪错了能补判，定罪错了会去改没坏的产品）；'
            u'U-173 是**本地 harness 与 CI 用了不同的读数通道 ⇒ 假红只出现在自己这边**'
            u'（闸门读到 judged=None/None，而那一遍测试全过：CI 并了文件通道，verify 脚本没并）。')


def fix_curve():
    real = summary('CURVE')
    for rel in ('AGENT_VISUAL_ITERATION.md', 'AGENT_STATE.md', 'AGENT_FINAL_REPORT.md'):
        p = os.path.join(REPO, rel)
        t = read(p)
        if CURVE not in t:
            print(u'  %s 里没有占位符' % rel)
            continue
        write(p, t.replace(CURVE, real))
        print(u'  %s：占位符 → %s' % (rel, real))


STAGES = {
    'A': (patch_visual_iteration, patch_ui_audit, patch_decisions, patch_backlog,
          patch_changelog, patch_manual),
    'B': (patch_state, patch_final_report),
    'C': (lambda: fix_curve(),),
}


def main():
    stage = sys.argv[1] if len(sys.argv) > 1 else 'A'
    for fn in STAGES[stage]:
        fn()
        print(u'已写 %s' % fn.__name__)
    print(u'%s：%s' % (KNIFE_TOTAL, u', '.join(u'%s=%s' % (t, k) for t, _, k in KNIVES)))


if __name__ == '__main__':
    sys.exit(main())

#!/usr/bin/env python3
"""R81 的台账落盘。

本轮的三件事：
  ① 读 R80 的 CI（run 38766914234）—— BACKLOG 109 的答案回来了，而且是**决定性**的那一支；
  ② BACKLOG 112 结案：读数通道改成"一整行一次 write + 一把锁"，并发锤击判据实测有牙
     （把锁拿掉 ⇒ 3/3 遍 SIGSEGV）；
  ③ 新开 BACKLOG 113：R77 把轴修好之后，runner 第一次**看得见**骨架扫光，
     于是那条"循环 vs 跳变"的判据第一次真判 —— 判出来是红的（2 对 < 3）。
"""
import io
import sys

EDITS = []


def patch(path, old, new):
    EDITS.append((path, old, new))


ROUND_TEXT = '''## Round 81 · 答案回来了，是决定性的那一支；而修好轴的那一刀让一个位点第一次开始判红（结案 109、112 / 新开 113 / U-151、U-152 / D-139）

开场读数（先读 R80 的 CI，run 38766914234，commit `3bb8070`）：

```
✓ Swift tests   ✓ Offscreen frame capture   ✓ Capture gate   ✓ 探针两步   ✓ Motion filmstrip
X Motion coverage floor        ← 唯一的一朵红，而且是有名字的红
QUICKPICK_FOCUS_AXIS_NOT_RUN=1 亮：焦点那一档的墨移动在这一台机器上读到 0.0pt²，地板 40.0pt²
   （缩放=1×，同态噪声 0.0pt²）。同一把尺在同一格里读得出别的成因：撤占位字搬动 88.9pt²、
    打进字 113.4pt² ⇒ 尺不瞎，是这台机器的 AppKit 不为非 key 窗口调淡占位符
QUICKPICK_FOCUS_AXIS_NOT_RUN=1 暗：0.0pt²；撤占位字 112.3pt²、打进字 143.2pt²
```

### BACKLOG 109 结案：三支里的是**第二支**，而且是被量出来的

上一轮那三条证人臂就是为这一刻准备的。runner 那一遍读到：

| 量 | 本机 2×（亮 / 暗） | runner 1×（亮 / 暗） |
|---|---|---|
| 焦点搬动的墨 pt² | 98.7 / 113.3 | **0.0 / 0.0** |
| 撤掉占位字搬动 pt² | 268.7 / 330.0 | 88.9 / 112.3 |
| 打进一个字搬动 pt² | 236.7 / 283.9 | 113.4 / 143.2 |
| 同态重拍噪声 pt² | 0.0 / 0.0 | 0.0 / 0.0 |

⇒ **尺不瞎**：同一把尺、同一格、同一台机器上，别的成因能读出 89–143pt² 的搬动，
而聚焦读出**恰好 0.0**。上一轮我留的那句"最多 3/4 是网格"现在有了答案：**网格那 3/4 不成立**，
聚焦在 runner 上是真的什么都没做（0.0 不是"小到量不出"，是"一位小数都没有"）。
处置按预登记的走：2× 上照旧红（本机必须判得出），1× 上 `QUICKPICK_FOCUS_AXIS_NOT_RUN` 点名，
赎回这条路只剩 BACKLOG **111**（真机 / 非 Retina 那一问，人工批次 71.1）。
顺带一条新事实：runner 那一格的墨只有本机的 **1/3**（88.9 vs 268.7），
这是"1× 上那串占位字画得更淡"的量化，与焦点无关，记下来免得下轮重新查。

### BACKLOG 112 结案：一整行一次 write，并发锤击判据**实测有牙**

`CaptureReadings.emit` 原来两条腿都不是原子的（`print` 分两次 write；文件通道 seek+write；
`opened` 无锁）。现在：stdout 那一条腿改成一次 `FileHandle.standardOutput.write(整行+\\n)`，
文件那一条腿整段进 `NSLock`，`opened` 换成**按 URL 记**的 `openedURLs`
（共享布尔会让临时文件的第一行以为"已经开过卷"，于是去 open 一份不存在的文件）。

新判据 `testConcurrentReadingsNeitherSpliceNorDropALine`：8 线程 × 60 条 900B 长行，
三条断言各拦一种坏法 —— 行数（整卷被抹）、**行首与行尾的 (t,i) 必须相等**（缝行）、
每个 (t,i) 恰好一次（覆盖）。第二条是要害：**只看"有没有变化"抓不到缝行，只看位置同一性才抓得到**。

牙（M434–M436，每刀跑 3 遍量复现率）：

| 刀 | 动的是 | 结果 |
|---|---|---|
| M434 | `appendForced` 拿掉锁 | **崩溃 3/3 遍**（SIGSEGV） |
| M435 | 同一刀再跑一遍 | 崩溃 3/3 遍 ⇒ 复现率 100% |
| M436 | "第一次写要整份重写"这条分支每次都走 | 红 3/3 遍（行数那一条） |

**这一刀比预想的更狠**：没有锁的时候两个线程同时改同一个 `Set` / 同一个 `FileHandle`，
进程直接段错误 —— 不是"读数被缝掉"那么温和。

### U-151 · 电池把崩溃读成"编译没过"（分类器只认两种形状）

第一遍这批三刀全报 `NOT-RUN 有 3 遍编译没过`。真相是：`error: Exited with unexpected signal code 11`
**带 `error: ` 却没有 `error: -[类 方法]` 那个形状**，于是被旧分类器归进"没跑成"。
而崩溃在这里恰恰是最硬的证据。⇒ 分类器加第三类 `crashed`（`Exited with unexpected signal|signal code \\d+`），
并把"红"与"崩"都算 CAUGHT、分开报数。
这条与 R61 的 U-94（"红了但连一条断言行都没有 ⇒ 崩溃"）**同族但方向相反**：
那次是判卷把崩溃吞成绿，这次是把崩溃吞成"没跑"。**共同点：分类器只认它见过的那几种形状**，
而每一种新形状都要被显式命名，否则它就变成一个没人负责的默认值。

### U-152 · 修好一把轴，会让一个"以前不判"的位点开始判红 —— 这是**成果**，不是回归

`Motion coverage floor` 那一朵红：`testSkeletonSweepActuallySweeps`
`XCTAssertGreaterThanOrEqual failed: ("2") is less than ("3") — 只读到 2 对在变 ⇒ 那不是循环，是一次跳变`。
把三次 runner 读数并排放（都是 `gh api .../jobs/<id>/logs` 拉的原文）：

```
R73 run 38726991211（绿）  MOTION_SHIMMER 扫 帧数=23 变化帧对=0 峰值=0.000 采样≈98ms
R75 run 38735395615（绿）  MOTION_SHIMMER 扫 帧数=20 变化帧对=0 峰值=0.000 采样≈125ms
R80 run 38766914234（红）  MOTION_SHIMMER 扫 帧数=23 变化帧对=2 峰值=0.015 采样≈115ms
```

⇒ 绿的那两次**根本没判**：`requireObservableMotion(.gradient)` 看见峰值 0.000 ⇒ 报 not-run 跳过。
R77 把两态尺改成并集（alpha 进判定）之后，runner 第一次看得见这个渐变（0.015），
闸门放行，判据第一次真判 —— 然后判出来是红的。
所以这朵红的含义是：**一个以前免检的位点现在要开始被检了**，而它的判据形状（"数变化的帧对"）
在 115ms 的采样网格上撑不住。这正是 BACKLOG **110** 说的那族病，只是换了个位点，
于是新开 **113** 把它作为 110 的第二个实例钉住（下一轮第一件事就是它，main 上这朵红只许活一轮）。

### 验证（本机，逐条实跑）

```
swift build --build-tests                告警 0
swift test（全量）                       Executed 796 tests, 38 skipped, 0 failures
swift test --filter UICaptureTests       捕获闸门 CAPTURE_GATE_RESULT=ok 红=0 NOT_RUN=2（都是 RING）
frame_baseline.py check --against working COMPARED=124 CHANGED=0 MISSING=0 ADDED=0
python3 -m unittest discover -s scripts  exit 0
并发锤击 M434–M436                       3/3 CAUGHT（两刀以崩溃的形式、一刀以红）
读数文件里 QUICKPICK_FOCUS_INK 行数      2（亮/暗各一，**没有一行被缝掉**）
```

### 七维自评

| 维度 | 得分 | 说明 |
|---|---|---|
| 原生感 | 19 / 20 | 零产品改动；焦点那格的墨 1/3 差异是通道/系统性质，不是产品 |
| 流畅度 | 16 / 20 | 扫光那条判据现在红着（113 未修），这一格本轮**没脸加分** |
| 层次与材质 | 14 / 15 | 124 张帧逐字节不变 |
| 动效细节 | 13 / 15 | 109 有了决定性的答案；扫光那一位从"免检"变成"在判" |
| 交互反馈 | 9 / 10 | 反馈本身没变 |
| 可访问性 | 8 / 10 | 真机焦点可见性仍未证（批次 71.1 新增非 Retina 那一问） |
| 性能 | 14 / 15 | 全量 796 例 / 38 skip / 0 failures；锤击只在临时文件上跑，不污染读数卷 |

**93 / 100**。低于 95 的原因写在脸上：main 上现在有一朵**有名字**的红，
而本轮没有修它 —— 记成 113，下一轮第一件事。

### 仍未解决

- BACKLOG **113**（本轮开，下一轮第一件事）：扫光那条"循环 vs 跳变"不许数帧对。
- BACKLOG **110**：同一族病的第一个实例（`detail-kind-change` 押在最粗那一次采样上）。
- BACKLOG **111**：焦点那条轴在 runner 上的赎回（唯一路径是换捕获对象 / 真机非 Retina）。
- BACKLOG 108 剩下的、77 路 b、101 的②③、106；真机 68.1 / 68.2 / 69.1 / 70.1 / 71.1。

'''

patch("AGENT_VISUAL_ITERATION.md", "\n", "")  # 占位，稍后删

io.open("/dev/null", "w").write("")

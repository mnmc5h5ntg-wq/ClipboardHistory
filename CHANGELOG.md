# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project follows semantic-style version naming for public releases.

## [Unreleased]
### CI（R86）

- 新增 `scripts/ui_probe_report.py`：在屏探针那一卷被看门狗收掉时**点名挂死的那条用例**
  （`Test Case ... started` 与有结论行的差集）。七格真值表 + 退出码；
  "说不出为什么停"的四种形状（日志不完整 / 喂的是步骤摘要 / 空日志 / 文件读不到）一律红。
  CI 两步各用一次：报告型那一步打名字，`On-screen probe coverage floor` 那道硬门要求必须有名字。
- 脚本自测 +12 格（现跑共 155 格）；变异电池 M465–M472（M465、M466、M467、M468、M469、M470、M471、M472）：8 刀 CAUGHT，没有逃掉的。

### Docs（R86）

- BACKLOG 92 与 93 更新（报告器已接，runner 上挂在哪一条等下一次 CI 的读数；预测已先登记）；
  116 收窄（四遍测量不复现"差 7 条"，捕获那五条其实有名字，剩下的那半句改成交给 R87）。

### Tests（R85）

- 覆盖地板新增 `loops` 那一层：常驻循环那一族（扫光的运动判据 + 位置判据）第一次进登记表。
  判据的两条出口各打一行状态（`MOTION_SHIMMER_STATE` / `MOTION_SHIMMER_BAND_STATE`），
  闸门只判两格 —— 状态行整行缺席 ⇒ `LOOP_SILENT` 红；点名理由没登记 ⇒ `BAD_REASON` 红；
  点名在登记之内 ⇒ 不红，但打一行看得见的未覆盖。脚本自测 +1 格（现跑共 143 格）。
- 变异电池 M458–M464（M458、M459、M460、M461、M462、M463、M464）：7 刀 CAUGHT，没有逃掉的（M461 / M462 第一版逃掉：守卫从"这个串出现过"
  改成"两条出口各打一次"之后才有牙 —— 见台账 U-174）。

### Docs（R85）

- BACKLOG 118 结案；119 补一条新成因（画法让运动不可见 ⇒ 归因顺序改了）。

### Product（R84）

- 详情预览加载态的骨架扫光：亮带从"每根条各扫各的"改成**一条光横穿整组**
  （渐变从单根条的坐标系抬到整组的坐标系）。同一帧内三根条亮斑中心的绝对差
  从 169pt 变成 0pt，减弱动态那一档仍然完全静止；静置画面不变（124 张帧基线逐张复核）。

### Tests（R84）

- 新增 `testSkeletonSweepIsOneBand`：位置判据（合成正对照两份 + 真片行程正对照 +
  由"同一把尺读高对比证人"签的处置），真值表 13 格；`SkeletonMotion.barHeight/barSpacing/barRect`
  三个令牌 + `SkeletonBarsShape`；产品那一卷胶片改为缓存复用（运动与位置两句读同一卷）。
- 变异电池 M451–M457 共八刀：七刀 CAUGHT，一刀按实存活为"本地无独立判别力"（M454 的牙被 M454b 两格同拆检验 —— "至少一格有牙"这句话本身可证伪）。

### Tests（R83：上一轮那枚钉子挂错了对象 —— 前提从时刻本身读，绝对地板听处置的话；结案 114 / 新开 118 / U-160…U-163 / D-141）
- 读 R82 的 CI：**114 落在预登记的第一支**（runner 带得动 20Hz、带不动产品那一档 30Hz），
  等节拍证人 `coverage=0.284` 与粗节拍证人 `coverage=1.000` 并排就是分诊表本身。
- 修掉上一轮我自己造的三处不干净：
  ① 卷长钉子挂在 `LoopShape.recordedMilliseconds` 上（峰值 0 时被 guard 归零 ⇒ 把"看不见运动"
  报成"探针坏了"）⇒ 新增 `FilmPremise(frames:stamps:)`，前提从时刻本身算，真值表钉"两把尺必须给不同数"；
  ② 绝对峰值地板不管处置说话 ⇒ 只有 `.ok / .productRed` 时判，其余点名 `MOTION_SHIMMER_PEAK_NOT_JUDGED`
  （减弱动态那档"必须静止"仍然无条件判）；
  ③ 闸门 `NAMELESS_RED` 拿失败次数减用例名个数 ⇒ 两边同为失败行数，两格回归测试一正一反。
- 117 从"看图觉得"变成有数字：`r83_band_fanout.py` 逐帧量三根条的亮斑中心，
  同帧内绝对位置差最大 170pt、归一化差 0.003 ⇒ 亮带每根条各扫各的（改产品在下一轮）。
- 新开 118：一朵有名字的未覆盖不在覆盖地板的登记表里 ⇒ 常驻循环那一族也要有一格登记。
- 电池自己的 python 臂补第五种形状（U-164）：模块级导入失败时四条用例名都不出现，旧分类器读成"全绿"。
- 牙：M446–M450 五刀 —— 三刀本地有牙（两刀红在真值表第⑧格、一刀红在新增那格 python 回归测试），
  两刀**按实存活为"本地无判别力"**（把钉子挂回结论尺、地板不管处置，本机都不改变结果，牙在 runner）。

### Tests（R82：循环那条判据从"数帧对"换成 coverage，证人从一颗换成两颗并要同节拍；结案 113、110 的第一实例 / 新开 114–117 / U-155…U-159 / D-140）
- `testSkeletonSweepActuallySweeps` 不再数"几对帧在变"，改读 **coverage**
  （变化覆盖了整卷时长的几成；时间之比 ⇒ 与采样密度无关，地板 0.5 不为哪台机器移动）。
- 证人从一颗变**两颗**：新增 `GradientTickView.productRate()`（30Hz、每拍 (1/30)/1.5、0.06→0.18、
  同一颗 `VisualShape.rounded`）决定"产品红 / 环境不行"；原来那颗 20Hz 高对比的降级为
  只守"证人坏没坏"。起因是 R81 的 CI：产品 `变化帧对=2`、那颗证人 `13`，但它问的根本不是同一句话。
- 新判据 `testTheLoopWitnessStillMirrorsTheProductLoop`：证人那四个数**仍等于产品**（写死在测试里，
  漂移就红）；新判据 `testTheLoopShapeClassifierIsATruthTable`：七格合成真值表，含
  "50ms 与 115ms 两档采样同判定"与"时刻少一根/多一根都算没量到"。
- 分辨率那条闸门（BACKLOG 110 的第一个实例）改吃**事件内 P75**而不是"最粗那一次"：
  本机实测 `[50 51 52 53]` 与 `[50 51 52 81]` 的 P75 相同而最大值差 28ms，
  而旧闸门就是被这 28ms 从"判到"推到"判不到"的。
- `SkeletonProbe` / `StateTickProbe` 改成返回 `GrabbedFilm(frames:stamps:)`（U-155：
  两卷连拍时 `probe.lastStamps` 会被后一卷覆盖，而 M443 第一版把它改回去**四条判据全绿** ⇒
  断言拦不住等长的两卷，只能让错的话拼不出来）。
- 电池自己的分类器补第四类（U-158）：跑到一半进程死掉的用例不再被归成『没跑』。
- 牙：M437–M445 九刀，抓到 9（无遗漏）。

### Tests（R81：读数通道一整行一次 write + 并发锤击判据；109 的答案回来了；扫光那一位开始判红 / 结案 109、112 / 新开 113 / U-151、U-152 / D-139）
- `CaptureReadings.emit` 的两条腿改成原子的：stdout 一次 `write(整行+换行)`（不再用 `print`，
  它把内容与换行分两次写 —— 那就是缝点），文件通道整段进 `NSLock`，`opened` 换成按 URL 记的 `openedURLs`。
  起因是 R79 那遍 CI 里决定 BACKLOG 109 的那条读数被**缝进**了另一条判据的行。
- 新判据 `testConcurrentReadingsNeitherSpliceNorDropALine`（8 线程 × 60 条 900B 长行）：
  行数、**行首与行尾的 (t,i) 必须相等**、每个 (t,i) 恰好一次 —— 三条各拦一种坏法，主断言是位置同一性。
  牙：M434/M435 拿掉锁 ⇒ **3/3 遍 SIGSEGV**（比"读数变脏"更狠），M436 让整份重写每次都走 ⇒ 3/3 遍红。
- BACKLOG **109 结案**：runner 那一遍落在预登记的**第二支** —— 焦点搬动 0.0pt²，
  而同一把尺在同一格里读出撤占位字 88.9/112.3pt²、打进字 113.4/143.2pt² ⇒ 尺不瞎，
  是这台机器的 AppKit 不为非 key 窗口调淡占位符；上一轮"最多 3/4 是网格"那句被量掉了。
- BACKLOG **113 开**：`testSkeletonSweepActuallySweeps` 在 R80 的 CI 上红（变化帧对 2 < 3）。
  并排三次 runner 读数证明这朵红是 **R77 把轴修好之后的成果**（R73/R75 峰值 0.000 ⇒ 那时 not-run 免检），
  要修的是判据形状：帧对计数跟着采样网格走，换成时间跨度 / 不连续段数（与 110 同族）。
- 电池自己的分类器补第三类（U-151）：崩溃不再被归成"编译没过"。

### Tests（R80：焦点那四条红是真的，而"红"说的是尺跟着像素网格变 —— 换尺 + 三条证人臂 / U-146…U-150 / D-138）
- 读 R79 的 CI：runner 上存在性闸门**开**（`占位整条宽=87.0pt`）而两态差读 0 个像素，四条红原样在。
  命中 BACKLOG 109 预登记的第二分支 ⇒ 按预登记的处置：查机制，**不抬地板**。
- 焦点那条判据的像素尺换成**网格无关**的量：`搬动的墨 ≥40pt²` 且 `占那一格现有墨 ≥8%`
  （`movedInkPointsSquared` / `inkPointsSquared`，逐像素取 alpha 与三条合成 RGB 的最大值 = 并集）。
  旧尺 `变化像素 ≥500` 为什么不行，被合成为一条会红的判据：同一个物理变化 1× 数 2000 个、2× 数 8000 个。
- 三条证人臂（同态重拍 = 噪声地板、撤 `placeholderString`、打进一个字）把"看不见"分成两支：
  `行为不在这台机器上` 与 `这一格对这把尺失明`，各打 `QUICKPICK_FOCUS_AXIS_NOT_RUN` 并带读数；
  2× 上两支都红。两支 1× 才走得到 ⇒ 处置提成纯函数 + 8 格合成真值表（`testFocusAxisDispositionIsATruthTable`）。
- 三条更正：那颗放大镜**不存在**（臂 D 之后带内墨 0.0pt² + 帧上看图，U-146）；
  R78 闸门注释说"④照判"而 `continue` 会跳过它（U-147，④已挪前）；
  R77 那条轴守卫反过来**误伤**真读了 alpha 的驼峰写法 `deltaAlpha`（U-138 的反面，改成大小写不敏感 + 正对照 I）。
- 新开 BACKLOG **112**（读数通道并发下把两行缝成一行 —— 本轮要的那条读数就是被它吃掉的）、
  **111**（这条轴在 runner 上怎么赎回来）。人工批次 **71**（非 Retina 外接屏上焦点那一格变不变淡）。
### Tests（R79：R78 那道存在性闸门在 runner 上没拦住 —— 换成两根独立证人 / U-143…U-145 / D-137）
- 读 R78 的 CI（run 38757049151）：焦点那四条红**原样还在** ⇒ R78 的"占位区 ≥20 个有墨像素"
  在 runner 上恒成立 —— 那颗**放大镜**住在搜索框左边 3–20pt，一个人就凑够 20 个像素（U-143）。
  R78 的注释里我写了"整条 band 混得进描边"并用内缩排掉了描边，却没排掉图标：同一个担忧只解决了一半。
- 闸门换成**两根独立证人取合取**：① 带内**有墨像素的 x 包围盒宽度** ≥ 40pt
  （本机实测：图标自己 17.0pt，图标 + 占位字 86.5 / 87.0pt）；
  ② "只有占位字能待的那一块"（x 从带左起 50pt、上下各内缩 2pt）里有墨像素 ≥ 20（本机 675 / 767）。
  描边骗得过①、骗不过②；图标骗得过计数、骗不过①。
- 新增对照（U-144）：只框住放大镜那一小块时，量出来的宽度必须**过不了**闸门 ——
  R78 缺的就是这条：它证明了"有墨"，没证明"分得开图标与那串字"。
- 牙：M419（地板 40→10pt）、M420（对照失去对象）、M421（span 尺地板 8→250）、
  M422（独占区地板 20→100000）—— 4/4 全红在焦点那一条。
- 流程（U-145）：R78 记下的"读上一次 CI 排在开新一轮第一步"今天真的执行了一次，
  所以这朵红只活了一轮。零产品改动，124 张帧逐字节不变，全量 793 例 / 40 skip / 0 failures。

### Tests（R78：焦点那条判据在 runner 上看不见那串字 —— "没画"与"没有"从此分开 / U-137…U-141 / D-136）
- **修的是上一轮留在 main 上的红**：R76 的 run 38743276799 与 R77 的 38751643297 都是 `4 failures`，
  四条全在焦点那条判据上（runner `框内变化像素=0`、`alpha 差 0.05`；本机 1797 / 3.93）。
  根因不是阈值：那条判据只读两态之差，而"产品没有焦点后果"与"这条通道今天没画那串字"
  在只读差值的尺子上长得一模一样。
- 新尺 `alphaInkPixels(rep, rect, floor:)`：一块矩形里 alpha 过地板的像素数，**不依赖两态相减**。
  探针取占位字该在的那一块（band 左 30%、四周内缩 3pt —— 整条 band 混得进那颗框的描边）。
  本机实测 1699 / 1871 个有墨像素，整窗 69048 / 71021。
- 处置按机器分开（R60 那一课）：2× 上"没画" ⇒ **红**；1× 上"没画" ⇒ 点名
  `QUICKPICK_FOCUS_NOT_RUN=1` 并只跳过像素那两条 —— 行为两条与产品源码守卫在任何机器上都照判。
  闸门有牙：M417（恒"没画"）与 M418（地板抬到 250）都让本机红。
- 守卫自己两个洞补上：① 名册里那条 `paintedXRange` 是**零调用点的死尺** ⇒ 删掉 +
  新增"每条登记必须有人调"（M416 证明只有这一格抓得到）；② "两态"的识别从减法针脚换成
  **签名形状** ⇒ 抓回 R77 漏掉的 `alphaBandDelta`；换检测器时踩到 `NSBitmapImageRep`
  含子串 `Bitmap` 的双计（会把单参电平尺误判成两态尺）⇒ 长写法先从串里挖掉（M413 钉住）。
- 对账：R76 注释里"1901 / 2144 个变化像素"其实是**有墨像素**，"alpha 143.6 ⇒ 90.9"是第一版
  另一块矩形的数 ⇒ 注释改成引用判据自己那一行读数（U-140）。
- 电池 M413–M418 六刀全 CAUGHT。零产品改动，124 张帧逐字节不变，全量 793 例 / 40 skip / 0 failures。

### Tests（R77：两态相减的尺子原来只读一根轴 —— 结案 107 / 新开 108 / U-134…U-136 / D-135）
- `axisPair` 一次算出 `亮度 / alpha / 并集`，`changedFraction`（动效卷、按压、在屏探针三处）与
  `bandHeadTailDiff` 的语义从今天起是**并集** ⇒ "没动"这句话要求两根轴都不动。
  理由不是假想：`raster` 是 `premultipliedLast` 画进零初始化缓冲区，**暗墨变透明在亮度轴上就是 0→0**，
  而 R76 的 U-132 已经在这条通道上实物撞见过一次。
- 本机对账（同一卷两轴一起打，`.scratch/motion-audit-2/r77_motion_local.log`）：四臂 + 空白全部
  `仅alpha在动=0/N` ⇒ **加轴没翻掉任何一条结论**（`judged=4/4`、`MOTION_SUMMARY 12/13/3/3`
  与 R75 的 `11/13/3/3` 同判，档位由时长 182/183ms 决定）；
  而 alpha 峰值 0.2497 / 0.1848 / 0.0794 / 0.1063 与亮度同量级 ⇒ 这条通道带透明度，
  "窗口是实心的"只在**落盘之后**成立（写出的 PNG alpha 实测全 255）。
- 新判据两条：`testTheAxisRulerSeparatesAlphaFromLuminance`（八格真值表，含
  "并集 ≠ 两数取大"那一格）与 `testEveryTwoStateRulerReadsBothAxes`
  （扫四份文件，只读一根轴的两态尺必须带理由登记：只读亮度 3 条、只读 alpha 5 条，
  `changedFraction`/`axisPair` 永远不许进名册）。
- 电池 M403–M412 十刀全 CAUGHT，**其中 M407 前两版 ESCAPED**：守卫两次被"提到 alpha"喂饱 ——
  一次是一行不参与判定的死读数，一次是行尾注释里那句"又不读 alpha 了"。
  修法（判"用没用" + 扫前剥注释）各带一个正对照，并各挨一刀元层变异（M411 / M412）（U-135）。
- 看图复核 `notice-banner-dismiss` 两卷：撤走是**滑出 + 高度塌缩**，中途文字被窗口边切成半行
  ⇒ 判为机制的自然结果，观感那一问记人工批次 69.1。零产品改动，124 张帧逐字节不变。

### Tests（R76：焦点那一档不是没有视觉后果，是只活在 alpha 通道里 —— U-116 判完 / U-131…U-133 / D-134）
- 新判据量"聚焦 vs 撤掉焦点"两态：框内变化像素 **1797（亮）/ 2354（暗）**、框外一圈 **0**，
  那一格平均 alpha 10.71⇒6.77、13.15⇒8.64，而**同一对在亮度轴上只有 -0.66 / +2.25**
  ⇒ 焦点反馈存在（占位符"搜索历史记录…"退后），但只在 alpha 上（U-132）。
- 决定：**不加**自定义焦点视觉。三条理由都有读数 —— 已有让位式反馈；
  焦点位置不歧义（浮层唯一可聚焦文本输入，`show()` 打开即聚焦，源码守卫钉住那句赋值）；
  再加一圈会与 R67 的悬停灰、选中药丸抢同一格的音量预算。
  代价记明：真机上有没有系统环、退后够不够明显，这条通道结构上看不到（面板不带 key）⇒ 人工批次 68。
- 本轮两次错在自己新写的判据里，都当场修并记账：
  第一版两态取"建出来时"与"请焦点之后"，而那颗框**建出来就聚焦** ⇒ 等于一张帧减自己，
  那个"0 像素"绿得完全正常（U-131）⇒ 换成正面两态 + 一条"撤焦点必须真的撤掉"的正对照；
  `NSFocusRingType.none.rawValue == 1` 而 0 才是"系统决定"（本 SDK 没有 `.automatic`）
  ⇒ 按名字猜会把"环被关掉"写成通过（U-133）。
- 牙：M398–M402 五刀全 CAUGHT。M398（产品侧关环）**只有④红、③照旧绿**
  ⇒ "这条通道看不见环"由一刀证明，④不是装饰是唯一防线；M399（删 `show()` 里的赋值）
  四条判据全绿、只有源码守卫红 ⇒ 这一族回归在帧里没有影子。
- 读 R75 的 CI（run 38735395615，绿）：证人接线如约生效 ——
  `MOTION_NOT_RUN=witness-snaps-here notice-banner`、`judged=3/4`、`MOTION_FLOOR_OK=3/4`、`exit 0`；
  同一遍里 `FRAME_BASELINE_CHANGED=124` 是 runner 1× 与工作基线 2× 的已知差（那一步只判帧名齐不齐）
  ⇒ "CI 绿"不等于"像素没变"，像素那一半由本机这一遍判（`CHANGED=0`）。
- 新开 BACKLOG **107**（"只在 alpha 上"的效果对亮度轴守卫是普遍盲区）。
- 全量 **791 / 38 skip / 0 failures**、`FRAME_BASELINE_COMPARED=124 CHANGED=0 MISSING=0 ADDED=0`、
  编译告警 0、脚本测试 140 OK。**产品 0 个文件** ⇒ 本机仍是 R71 装的 `c03cf278d3a4dd98…`。

### Tests（R75：那条反复出现的红，是判据拿两帧的采样间隔当了时长 —— 结案 BACKLOG 104 / U-129、U-130 / D-133）
- 读三遍 runner 日志（38726667469 / 38726991211 / 38730788527）：`notice-banner` 三遍都是 **2 帧**，
  时长 32 / ≥60 / 36ms ⇒ 红、绿、红；而淡入时钟证人三遍同一句
  `采样≈32ms 可分数段=4 合格=是 判定=拍成跳变（中间态帧数=0）`
  ⇒ **104 的①**：那 80ms 里抓帧只占 0.4–0.5ms，其余是节拍（R68 那句"面积决定分辨率"作废）；
  **104 的②**：红既不是产品也不是含糊的"环境"，是判据把一次采样间隔当成了过渡时长。
- 修：新增纯函数 `jumpAdjudication` 把证人接到四臂判据的 `.jump` 那一支
  （赦免只有一个形状：证人**合格且自己 snap**；证人死了或不合格仍然红），
  八格真值表 `testTheJumpAdjudicationIsATruthTable`。
  **不对称是刻意的**：绿是正面证据不需要借口，缺席的证据才要先确认这台机器看得看得见。
- 登记表按实测走：`notice-banner` 的 `must_judge` true⇒false（地板 4⇒**3**，带两个 run 号），
  另外三臂一条不放；`notice-banner-dismiss` 的带捕获要求照旧。
- R57 那条 Swift 守卫从"两臂都必须 true"改成**"放宽必须带理由与 run 号"**，
  并且理由从 `allowed_not_run_reasons` **数组里**读 —— M395 实测：整块 `contains`
  会被同一臂 note 里的解释文字喂饱（放宽的守卫被放宽条目自己养活，U-130）。
- 牙：M392–M397 五刀全 CAUGHT（抓到=5 逃掉=0）；另有一刀（删掉真判据里的证人问话）
  **本地无判别力**，由 runner 判，不计入计数。
- 跨机验证：R74 的 `OVERLAY_HOVER_REFLOW` 在 runner 上给出与本机**逐字相同**的读数（6/1/1、8/7/6）
  ⇒ 重排频率不吃机器，R74 那条决定在两台上都成立。
- 看图：本机 27 格胶片里横幅逐格变实（11–12 格到底）⇒ 本轮不是把红改成不判。
- 全量 **790 / 38 skip / 0 failures**、动效卷 **47 例 / 3 skip / judged=4/4**、
  `FRAME_BASELINE_COMPARED=124 CHANGED=0`、编译告警 0、脚本测试 **140** OK。
  **产品 0 个文件** ⇒ 本机仍是 R71 装的 `c03cf278d3a4dd98…`。

### Tests（R74：浮层淡入那一格判完了，而 R67 的理由死在第一个语料上 —— U-115 判过 / U-128 / D-132）
- 新判据走产品真路径（`queryChanged` 一个前缀一个前缀地喂）量"打字时候选列表动多勤"，
  两个语料分开打：`帧夹具 前缀数=6 整列变了=1 次 指针那格换了=1 次`、
  `嵌套前缀语料 前缀数=8 整列变了=7 次 指针那格换了=6 次`
  ⇒ **R67 写在报告里的那句"重排发生在每个候选字上"在帧夹具上不成立（1/6）**，
  原因是那个夹具只剩一条命中，不是产品不动。
- 决定**不变**（悬停不加淡入），理由换成两条：指针那一格在真实形状上 8 个前缀换 6 次记录；
  机制上 `rebuildRows` 每个前缀拆一次灰、补回来的唯一入口是 `mouseMoved`。
  两个语料各带一条**反向**断言（正面必须一直重排、反面必须一直不重排），
  防止"挑一个能证明自己的夹具"（U-128）。
- 两条读同一机制的守卫（R67 真值表那条 + 本轮机制那条）合并成一把尺 `Self.functionBody`，
  配齐正 / 反 / 右边界三格对照；失败消息里明写"这一条红的含义是决定该重判，不是产品坏了"。
- 牙：M386–M391 六刀全 CAUGHT。其中 M387（撤掉拆灰、只留重画）**像素判据全绿**
  ⇒ 机制守卫与像素判据不冗余；M387 第一版被"只红一条"的期望误判成 ESCAPED ⇒ 改期望表，不改网。
- 看图 + 跨通道核对：落盘 PNG 上灰带 x 44…795、y 296…363（68px），与判据在内存 rep 上读的逐字相同
  （亮暗两档都是）⇒ 判据看的图就是基线钉住的那张。
- 全量 **789 / 38 skip / 0 failures**、`FRAME_BASELINE_COMPARED=124 CHANGED=0 MISSING=0 ADDED=0`、
  编译告警 0、脚本测试 139 OK。**产品 0 个文件** ⇒ 本机仍是 R71 装的 `c03cf278d3a4dd98…`，本轮不重装。
- 新开 BACKLOG **106**（重排读数来自手工语料，真实存档在盘上）。

### Docs（R73：那条"门"的假设被自己的读数杀掉了 —— 结案 BACKLOG 105 / U-127 / D-131）
- 读 R70+R71 的 CI（run 38725116481）：runner 1× 上 `OVERLAY_HOVER_DOOR 药丸内缩@门1/2/4 = **2/2/2px**`、
  `灰带@门1/4 = 4/5px` ⇒ **不是门**（把 `≥4/255` 降到 `≥1/255`，药丸读数一动没动）
  ⇒ R69 写在注释里的那条机制假设作废。
- 反过来看灰带：两档缩放都量得对（1× 理论 5.2 / 实测 4–5；2× 理论 12.0 / 实测 11）
  ⇒ 坏的是**参照物那一侧的读数**（AppKit 那颗材质药丸的角在 1× 的离屏合成里被吃掉），不是产品也不是尺。
- 判据的处置一个字没改（`pillInset ≥ 4` 才判这一轴 + `FRAME_CORNER_AXIS_NOT_RUN=1` 点名 + `fillInset ≥ 1` 抓方角），
  改的是注释里那句话的**身份**：从"假设"换成"量过的结论"，并把被证伪的那条留在原地（划掉式记账，不删）。
- 同一遍 CI 还确认 R68 那条新闸门按设计工作了：
  `MOTION_FLOOR_SUITE_RED=1 … testListRowsDoNotAnimateAndNothingClaimsTheyDo：failed - 证人读不出这条淡入的过程，而它连自己都分辨不了`
  ⇒ 证人不合格时**红着指名**，没有偷偷 skip。
- BACKLOG **105 结案**：两条候选里"降门复量"这条已死，赎回 1× 那条轴只剩 **103**（换捕获对象）。
- 全量 **788 / 38 skip / 0 failures**、`FRAME_BASELINE_COMPARED=124 CHANGED=0`、编译告警 0、脚本测试 139 OK。
  **产品 0 个文件** ⇒ 本机仍是 R71 装的 `c03cf278d3a4dd98…`。

### Tests（R72：我上一轮给证人写的解释被这一轮的读数证伪 —— 结案 BACKLOG 104 / U-124…U-126 / D-130）
- 读 R68+R69 的 CI（run 38723020548）三件事同时发生：
  ① 证人 `采样≈81ms`（R66 是 80ms）而面积已小 **12.6 倍** ⇒ **R68 那句"面积决定证人采得粗"是错的**，
     真正的差是睡眠节拍（证人 `sleep 0.02` vs 判据那条 `record(_:)` 的 `0.004`）；
  ② `MOTION_BAND` 带 26.0ms vs 整窗 44.4ms ⇒ 真实省了 **1.70×**，而那条判据的线写的是 2×（本机数）；
  ③ R69 那条 `FRAME_CORNER_AXIS_NOT_RUN=1` 如约出现在 runner 日志里（亮暗各一条）⇒ 缺席是点名的，不是静默通过。
- 改：证人换成与判据**同一个循环节拍**，并把成本与间隔**分成两个数**打（`MOTION_FADE_CLOCK_COST`）。
  本机 `帧数=400 采样≈4ms 抓帧中位=0.1ms 中间态帧数=56 判定=能分辨`。
- 改：`bandCaptureSavingFloor` 2 → 1，判据从"省多少倍"变成"**是否严格更便宜**"（相等即红）。
  倍数仍然每轮打（`MOTION_BAND_SAVING`），但不再当门 —— 倍数是这台机器的成本结构，
  而"rect 是装饰"那一族错本来就由几何两条拦（帧高必须变小、带宽必须不变）。
- 牙的验证：**M384（两臂都抓整窗）⇒ 四格一起红**（抓到=1 逃掉=0）。
  另一刀 M385（节拍改回 0.02）**本地无判别力**（两档都仍"合格"）⇒ 按 M168 的先例明写"由 runner 判"，不混进计数。
- 全量 **788 例 / 38 skip / 0 failures / 157.7s**；`FRAME_BASELINE_COMPARED=124 CHANGED=0`；编译告警 0；脚本测试 139 OK。
  **产品 0 个文件** ⇒ 屏幕上仍是 R71 装的 `c03cf278d3a4dd98…`。
- **没解决**：①/②（notice-banner 那条红是产品还是环境）仍未回答 —— 这一轮只是让证人**有资格**回答它；
  BACKLOG 105 的门假设也仍悬着（`OVERLAY_HOVER_DOOR` 在 runner 上的第一遍还没读）。

### Changed（R70+R71：把"门"变成被量的对象；浮层的字号回到梯子，守卫补上 AppKit 那半边网 —— 结案 BACKLOG 99 / 105 ① / U-121…U-123 / D-129）
- **R71 产品**：浮层行标签 `13 → VisualFont.row`(12)、搜索框 `14 → VisualFont.body`(13)、空态那句 `13 → VisualFont.body`（同值）。
  依据不是"行高不同所以字号可以不同"（那是没读数的解释）：同一把尺量到 浮层行距 33–35pt（单行）
  vs 侧栏 38–47pt（双行），**两者不可比**；真正的依据是同一条记录的标题在别处五处全是 `row`，浮层是唯一那一处 13。
- 另外把 `MenuBarController` 四处、`ChineseTextContextMenu` 一处的字面量换成**同值**令牌（11⇒`meta`、13⇒`body`）
  ⇒ 那几张帧 `CHANGED=0`，"一个像素都没动"由基线证明而不是由我说。
- **守卫扩了半边网**：`testTextSizesComeFromTheScale` 从 R3 起只扫 `.font(.system(size:` 且只扫 `Views/`
  ⇒ AppKit 那一整个栈不在网里，浮层那个 13 就这么活了六轮。现在两个模式 × 两个目录，并带一条喂假源码的正对照。
- 新判据 `testQuickPickTypographyComesFromTheLadder` 从**产品入口**读真的 `NSTextField.font`（DoD 第 1 条）：
  行标签 == row、搜索框 == body、五行同档。读数 `行数=5 行标签字号=[12,12,12,12,12] 搜索框字号=13`。
  两条判据的分工由 M381 钉住：换成另一档合法令牌 ⇒ 守卫不红、判据必须红。
- 帧上净变化：行标签墨高 12.0/12.0/11.5/12.0pt ⇒ **11.0/11.5/10.5/11.5pt**（与侧栏 10.5–12.5pt 同带），
  而**同一行截断点右移一个词**（"包含足够长度…" ⇒ "包含足够长度以便…"）—— 小一档换来更多信息。
- **R70**：轮廓判据里对**参照物**用三道门（1/2/4）各量一遍内缩跨度（`OVERLAY_HOVER_DOOR`），线一个数没动。
  本机 2× 读数 `药丸@门1/2/4 = 10/11/11px` ⇒ 门在 2× 上几乎不影响 ⇒ "1× 量不出圆角"是门还是通道，只能由 runner 回答。
- 全量 **788 例 / 38 skip / 0 failures / 158.3s**；`FRAME_BASELINE_COMPARED=124 CHANGED=0`
  （改产品那一刻 `CHANGED=8` = 四张 quickpick 帧 × 亮暗）；编译告警 0；脚本测试 139 OK。
- 电池 **M378 / M379 / M381 / M382 / M383 五刀全 CAUGHT**。其中两刀先抓到我自己：
  正对照第一版写成 `Array.contains("13")`（整元素相等 ⇒ 永远不可能通过）；
  **M382 第一版逃掉** —— 守卫与正对照各读一份数组，删一半什么都不会红 ⇒ 共用 `Self.fontLiteralPatterns`
  （R57 那一课，我犯在十分钟前）。
- 换装本机：`INSTALL_RESULT=ok`，新包 sha `c03cf278d3a4dd98…`，pid 29503，存档 105→105，`SMOKE_OK=1`。
- **没解决**：浮层搜索框的焦点态仍未量（U-116 原样在）；1× 那条圆角轴仍等 runner 回答（BACKLOG 105）。

### Tests（R68+R69：证人与判据的地板都要建立在通道不变的量上 —— 结案 104 第一半 / 新开 105 / U-117…U-120 / D-127、D-128）
- **R68 · 淡入时钟不能比它作证的判据粗**：决定表 `controlJudgment` 多一根轴 `witnessQualifies`，
  新格 `.witnessCannotAdjudicate` ⇒ 证人不合格时 `.snaps` **不许落到 skip**，红着指名去修证人。
  合格线只依赖证人自己的量：`可分数段 = 声明 ÷ 采样 ≥ minimumIntermediateFrames + 1`
  （本机 150/20=7 ⇒ 合格；runner 150/80=1 ⇒ 不合格）。
- 证人搬小：抓帧区域 320×180pt（57,600pt²）⇒ **190×24pt（4,560pt²）**，
  判据那条带是 760×48pt ⇒ 证人从此是被告的 1/8，结构上不可能更贵
  （R55/R57 那条"面积决定采样粗细"第一次咬到我自己请来的证人）。
- 本轮推翻的是我自己写的第一版：那条合格线我写成"证人采样 ≤ 判据采样"，
  本机当场读到 `20ms vs 11ms ⇒ 不合格` —— 两根尺各自含自己夹具的成本，硬比大小没有意义（U-117）。
- **R69 · R67 那条轮廓判据在 1× 上是假红**：runner 的 CI 红在
  `testOverlayHoverFillSharesTheSelectionPillsOutline`，两台机器换算成 pt 之后
  药丸内缩 5.5pt(2×) vs **2pt(1×)**、灰带 5.5pt vs 5pt、逐行最大偏差 0px vs 3px，
  而**中行两边各自完全一致** ⇒ 不稳的是参照物（材质角在 1× 上过不了 `≥4/255` 那道门），不是产品。
- 处置是**按机器分开前提**而不是放宽线（R60 那一课）：线一个数没动，
  `pillInset < 4px` ⇒ 发 `FRAME_CORNER_AXIS_NOT_RUN=1` 点名"这一轴今天没判"；
  保留三条两台机器都有牙的断言（`fillInset ≥ 1` 抓直角、逐行左右沿 ≤2px、行数一致），
  逐行比对去掉首末各 `scale` 行。marker 名字必须以 `_NOT_RUN` 结尾，否则捕获闸门看不见它。
- **放宽之后电池必须仍然全抓**（本轮的验收，不是附注）：R67 那九刀重跑 **9/9 CAUGHT**
  （M369 直角、M370 6pt、M371 14pt 全部仍红），R68 六刀 **6/6 CAUGHT**
  （M377 第一版因"变异文包含原文子串"被回读检查判为没落地 ⇒ 改 `+ 99`）。
- 全量 **787 例 / 38 skip / 0 failures / 158.4s**；`FRAME_BASELINE_COMPARED=124 CHANGED=0`；
  编译告警 0；脚本测试 139 OK。**产品 0 个文件** ⇒ 屏幕上仍是 R67 装的那份 `db4872e4a852b426…`。
- **没解决**：1× 上"与系统同曲率"这一轴今天没判（BACKLOG **105** 给了两条赎回路径：降门复量 / 按 103 换捕获对象）；
  R68 那半条（runner 答①还是②）仍未回答 —— R67 那一遍在到达动效步之前就红了。

### Added（R67：快速选择浮层每一行第一次有指针反馈 —— 新开 BACKLOG 103、104 / U-112…U-116 / D-126）
- 现场：浮层唯一的提交入口是**双击**（`table.doubleAction`，没有 `action`、没有 `NSTrackingArea`），
  而呼出时鼠标停在哪是随机的 ⇒ 改之前用户看到的是一列不能碰的文字。
  梯子里 `VisualFill.hover`(0.06) < `selected`(0.16) 本来就有这一档，侧栏与详情区早就在用 ——
  浮层是**漏了一个位点**，不是"决定不做"。
- 加的是**一档灰，不是一个动效**：`QuickPickRowView`（`NSTableRowView` 子类 + `NSTrackingArea`）
  里插一层 `HoverFillView` 子视图，`.below` 压在 cell 下面 ⇒ 永远压不住文字；
  颜色在 `draw` 里解析（不缓存 `cgColor`，R30 那一族）；**选中那一行不叠这层灰**。
  为什么不用 `drawBackground(in:)`：R67 第一版那么写，结果 4 张已钉帧的选中药丸被改动
  （覆写 `drawBackground` 会换掉 AppKit 那颗药丸的抗锯齿路径）⇒ 换成子视图后 `CHANGED=0`。
- 形状是被判据教出来的，不是我挑的：`hoverFillInset` 9 → **10**（9pt 时灰带左右各宽 1pt，
  旧的总宽度判据在 ±2px 容差内是**绿的** ⇒ 绿不等于对上），
  圆角 直角 → 6pt → **`VisualRadius.card`(8pt)**（8pt 与药丸**逐行 0px 差**，
  说明 AppKit 那颗药丸用的就是这一档；不新造 7.5pt 的令牌）。
- 新增判据 `testOverlayHoverFillSharesTheSelectionPillsOutline` + 两把新尺
  （`alphaLiftProfile` 逐行给左右沿、`profileLeftInsetSpread` 给"圆没圆"的读数）。
  它存在的理由：**总范围相同的两块墨可以有完全不同的轮廓**，
  而 R15 那把"按列取带内最大"的尺结构上看不见这一族错（不是阈值太松，是读数丢信息）。
  参照物自己也被量一次（药丸内缩 ≥ 4px），否则参照物哪天变方，"逐行一致"会退化成空判据。
- 真值表四格全钉（只测"该画的画了"抓不到"选中时也画"，只测"不该画的不画"抓不到"永远不画"，
  而后者正是改之前的产品）+ 令牌同一性（`hoverFillAlpha == VisualFill.hover`）
  + 两条跨文件守卫（`rebuildRows` 必须调 `clearHover()`；`DetailView` 必须仍引用同一枚令牌）。
- 读数：alpha 抬升 **12.82/255**（亮）/ **12.70**（暗），线 7.65；
  两档分得开 —— 选中药丸灰值 220 vs 悬停 240（亮）、70 vs 43（暗）；
  逐行轮廓 灰带首行 55…784 / 中行 44…795 与药丸**完全相同**（亮暗两档都是）。
- 帧基线 **124 张**（本轮新增 `quickpick-hover-*-light/dark` 两张，改产品那一刻 `CHANGED=2`，逐字对上后同提交 update）。
- 变异 **M363–M371 九刀全 CAUGHT**（抓到=9 逃掉=0 没跑成=0 未落地=0）。
  其中 **M369 就是本轮真实存在过的直角版**：它从 M363–M368 六刀下全部逃掉，
  只有新轮廓判据抓得住 ⇒ 这一刀同时是"新尺有牙"与"旧尺不够"的双向证据。
- 全量 **786 例 / 38 skip / 0 failures / 157.9s**；捕获卷 41 例 0 failures；脚本测试 139 OK；
  编译告警 0（测试日志里那 10 行 `CoreData: warning:` 是运行时 XPC 噪声，与编译无关，分开记账）。
- 换装本机：`INSTALL_RESULT=ok`，新包 sha `db4872e4a852b426…`，pid 21873，存档 105→105 未动，`SMOKE_OK=1`。
- **没解决**：这一档"够不够响"没有机器判据（通道里没有窗口底 ⇒ BACKLOG **103**）；
  真鼠标进出没被任何判据覆盖（自动化打不进面板 ⇒ 人工批次 **67**）；
  那层灰没有淡入（本轮判为不做，理由见 U-115）；
  以及读 R66 的 CI 时新开的 **104**：淡入时钟在 runner 上采样 80ms，
  比它要作证的判据（35ms）还粗 ⇒ **证人比被告粗就没资格作证**，R68 去把证人搬到同一颗尺子上。

### Tests（R66：动效那一步的红必须有名字，而"这台机器看不见淡入"得有个与被告无关的证人来签 —— 结案 BACKLOG 100 / 新开 101、102 / D-125）
- 现场：`motion suite exit: 1` 连着两遍（run 38693365411 / 38696695788），而两遍的报表都写
  `MOTION_FLOOR_OK=4/4 MOTION_FLOOR_REDS=0`。原因在 `motion_floor_gate.py`：那个 `REDS`
  数的是它自己四臂的结论，**不看测试有没有失败**，而那一步是 report-only
  ⇒ 一个真实的红在整份 CI 里没有名字（R36 我给捕获那一步修过的形状，没铺到动效）。
- 先量再处置：同一条 150ms 的淡入，本机落定残余四遍 **0.554 / 0.719 / 0.729 / 0.974**、
  runner **0.025**；采样 10–11ms vs 21ms；`MOTION_SETTLE banner-in` 16 帧 ⇒ ≈160ms vs
  4 帧 ⇒ **≈76ms** ⇒ 采样只差 2 倍而残余差 22–39 倍 ⇒ **"runner 太粗"解释不了它**，
  于是"在 runner 上登记成未覆盖"这个原方案被推翻：那是拿被告的证词给被告免检。
- 证人：新增 `FadeClockProbe` + `FadeClockView`（白底 + 盖满视口的黑块，
  `if shown { Rectangle().transition(.opacity) }` 配 `withAnimation(.easeInOut(duration: 0.15))`）。
  机制与提示条相同、**时长写死在测试里而不读 `MotionCatalog`**（读产品 ⇒ 证人跟着被告变短）；
  逐帧读**平均亮度电平**而不是帧间差（差没有极性，数不出"中间态"）。
  三档：跨度 < 0.05 ⇒ 证人坏了**判红**（不 skip）；中间态 ≥ 2 ⇒ 机器能分辨 ⇒ 产品读不出就是红；
  否则 ⇒ `MOTION_NOT_RUN=fade-clock-snaps-here`（带读数）+ skip。
  本机 `MOTION_FADE_CLOCK 跨度=1.000 中间态帧数=8–11 帧数=87–91 采样≈21ms 判定=能分辨`。
- 决定表纯函数化：`controlJudgment(residual:clock:)` + 六格真值表。
  原来三条判定长在 `if residual <= floor` 里，而本机残余永远高于地板 ⇒ **从未被执行、从未被证伪**。
- 闸门补一层 `suite_verdicts()`：`SUITE_RED=n`（未登记的红，带用例名与 XCTAssert 原文）/
  `SUITE_NAMELESS_RED=n`（汇总说有红而名字不够 ⇒ "红必须有名字"本身被钉住）/
  `REGISTERED_REDS=n`（登记过的不挡发布但数得出来，且必须打印 `registered_run`）/
  `SUITE_STALE`（登记没复现，提醒删）。**排在 `verdicts()` 两处提前 return 之前** ——
  判据崩的时候常常既没结论行又红。CI 那一步不必改：报告步仍 `continue-on-error`，
  红由下一步 `Motion coverage floor`（无 continue-on-error）挡下。
- 正/反对照：正对照是逐字从 runner 日志抄来的那一卷（`judged=4/4 not-run=-` 而这一条红着）；
  反向对照把新层摘掉后必须**全绿** —— 那就是"两次 exit 1 绿过去"的最小复现。
  登记表 `suite_reds` 今天故意空着，并有一格自测钉住它。
- 数字：产品 **0 个文件**、122 张帧对 working 基线 `CHANGED=0 MISSING=0 ADDED=0`；
  全量 **783 例 / 38 skip / 0 failures / 156.7s**；动效卷 45 例 exit 0；
  脚本测试 127 → **139**；`--build-tests` 0 告警；电池 **M350–M362 十三刀全 CAUGHT**
  （M362 动的是产品：撤掉淡入驱动 ⇒ 必须红在 `.productSnapped` 那一句，而不是被新登记吞掉）。
- 没解决（新开两条）：**101** `fade-clock-snaps-here` 是"整卷级"的缺席而地板只数"臂级"的 ⇒ 没有 run 号也没有计数；
  **102** runner 的读数被 `head -120` 截（`MOTION_LINES=146`）而 11 张胶片从不上传 ⇒ runner-only 的现象没有图可看。

### Fixed（R65：浮层的行首图标不再由文案里的一个 📄 承担 —— 五行标签共用一条左轴 —— BACKLOG 94、97 结案）
- 现象（R64 逐帧量出来的，不是推测）：同一个 `NSTableView` 里纯文本行的标签从 **34.5–35.0pt** 起，
  带图标的文件行标签从 **56.5–57.5pt** 起 ⇒ 五行两种左轴、差 **22pt**。
  而那 22pt 不是图标视图，是 `EntryPresentation.preview(for:)` 返回的 `"📄 …"` 里的**两个字符**。
- 三处代价：① Apple Color Emoji 不吃 tint，与旁边 `.secondaryLabelColor` 的灰字不同极性；
  ② 与全产品其余图标（SF Symbols）不是一套语言；③ 它进了**参与搜索匹配的字符串**
  （`QuickPickModel.filtered` 拿整条 `shortPreview` 比），并且白吃两个字符的截断预算。
- 修法：文案只说"是哪一条"（`report.pdf` / `a.pdf 等 3 个文件` / `多个文件`）；
  浮层每行一枚 16pt 的 `NSImageView` 类型符号 —— `doc.text` / `photo` / `doc` / `doc.on.doc`，
  与侧栏 `RowLeadingVisual` 一一对上（`photo` 沿用详情头已经在用的那个名字），
  `.secondaryLabelColor`、`VisualGlyph.chipSymbol`、对读屏隐藏（文字已说清，再念符号名是噪音）。
  标签左锚点从 `cell.leading+6` 改成 `symbol.trailing+6` ⇒ **左轴是这件事的副产品**，没有单独修。
- 本轮先推翻了自己上一轮写的一句话：BACKLOG 94 原写"侧栏、浮层、详情共用同一条字符串"。
  读调用点的结果：侧栏对 `.file`/`.files` 走 `FileNameText`/`MultiFileTitle`（不经过 `shortPreview`）、
  详情走 `sizeDescription`、菜单栏走 `menuTitle` 自己拼 ⇒ **唯一可见的表面是浮层**。
  "参与搜索匹配"是真的，所以这不是纯视觉改动，也因此配了真值表。
- 判据 5 条：预览真值表（四种内容 + **没有按 emoji 呈现的标量**；`.text` 故意除外——那是用户的正文）、
  emoji 那把尺的正对照（📄 必须抓到；`©`/`™`/`é`/`↵` 必须不抓 —— 用 `isEmojiPresentation` 而不是 `isEmoji`）、
  四个符号名互不相同且**每个都画得出东西**（`NSImage(systemSymbolName:)` 对错名字返回 nil，
  而 `NSImageView` 静默不画也不报错）+ 自带正对照、侧栏与浮层"同一套名字"的跨文件守卫、
  浮层每行有图且共享一条左轴（读视图 `minX`，实测散布 **0.00pt**；夹具必须真有 ≥2 种类型）。
- 帧：`quickpick-list` / `-typed` × 亮暗 = **4 张更新**（同提交 `update`），其余 **118 张逐字节不变**；
  `quickpick-empty` 两张不变（没有行就没有列）。
- 变异：M343–M349 **七刀全 CAUGHT**。M343 教了顺序 —— 不变量必须先判、逐字文案后判，
  否则"把 📄 塞回去"那一刀会红在"文案不等于"上，电池证明的就变成"文案钉住了"而不是"尺有牙"。
- 新开 **BACKLOG 99**：浮层那一行字号硬编码 13pt，而令牌 `VisualFont.row` 是 12 ——
  本轮判为不动，但**这个判断没量过**（侧栏行高没测），所以记成待验证而不是"已排除"。
- 同轮读到 R64 的 CI（run 38693365411）：`补回=65 行`、`NOT_RUN` 从 25 涨到 50 ⇒ **BACKLOG 96 结案**，
  并开出 **98**（在屏探针那一步仍只有一条通道）。

### Tests（R64：判据自己写的结论可以整块从 stdout 消失而作业是绿的 —— 捕获卷补第二条通道，并把"缺通道"变成一条有名字的红 —— BACKLOG 96 交付）
- **本轮零产品改动**（122 帧 `CHANGED=0`、`MISSING=0 ADDED=0`），改的是"验收证据本身会不会静默失踪"。
- 读数（本机三遍真 artifact，逐行比对）：捕获卷 `capture-readings.log` 488 行里，
  stdout 少了 **324 行**（`--filter` 两遍，都是下标 164–487 那**同一块**）与 **238 行**
  （全量 `2>&1 | tee` 那一遍，**3 块**）。切点落在**行中间**
  （stdout 停在 `…bottomI`，下一行直接是 `Test Case …`）。
  五条判据自写的 marker 三遍**全丢**，而 37 / 775 条 `Test Case … passed` 一条没少、作业 0 退出。
- **更正 R63 写下的机制**：账本里那句"按条随机丢"是我加的解释，本轮量出来是**连续大块、位置可复现**。
  账本留原文并标注更正，而**代码注释、`--help` 文本、失败消息里的旧说法全部改掉**。
- 交付：`CaptureReadings.swift`（`emit` = print **并且**落盘；第一次整份重写、之后 `FileHandle` 追加；
  通道自己坏了只走 stderr，不把判据变红）；捕获卷 **69 处** `print(` → `emit(`；
  守卫 `testCaptureReadingsUseTheFileChannel`（规则绝对：那个文件剥掉注释后 `print` = 0，
  所以通道实现单独住一个文件 —— 白名单就是下一次绕过去的入口）。
- 闸门：`ci_capture_gate.py --readings <文件>` —— 判的是**两条通道的并集**，
  并且"给了参数而文件缺/空"= 一条有名字的红。并集从 ci.yml 的 awk **挪进 python**：
  那段 shell 没有任何自测能证明"补回的行数是对的"，而它坏了的表现恰好是"什么都没补"。
  自检 120 → **127**，含一条**接线断言**（以后谁把 `--readings` 从 workflow 里删掉会当场红）。
- 真 artifact 上跑：`补回=316 行`（324 行实例 = 316 条不同的行），
  **同一份日志不给 `--readings` 仍然是 0** ⇒ 这条并集不是装饰，它单独就能把红找回来。
- 变异 **M337–M342 六刀全 CAUGHT**。其中 **M338 抓到的是本轮我自己写的第一版正对照**
  （拿 needle 拼对照 ⇒ needle 坏了对照仍然 3/3），另两把是电池自己骗人：
  上一遍留下的读数文件让"落盘坏了"那一刀逃过（M341 第一版）、
  汇总比对了带尾随空格的字符串导致**六刀全抓到却写"非抓到=6"**。
- 新开 **BACKLOG 97**：本轮逐帧看浮层量出来的排版缺陷 —— 纯文本行标签 34.5–35.0pt
  vs 文件行标签 56.5–57.5pt（图标占 36.0–50.0pt）⇒ 差 **22pt 两种左轴**。与 94 同一族，
  本轮判为不动产品（预算在通道上，且 ①/② 的选法取决于 94 的图标语言结论）。

### Fixed（R63：快速选择浮层从来就是塌的 —— 内容只占面板左下角一小块 —— 现在它占满，并且第一次有了帧 —— BACKLOG 30-① 结案）
- 现象（本轮第一次量到，不是推测）：⌃⌥⇧V 呼出的浮层里，产品的 `NSStackView` 实测
  `{{0,0},{24,49}}`，`NSScrollView` `0×0`，`NSTableView.visibleRect` `0×0` —— 表里有 8 条，
  **一条都画不出来**，而面板是 420×300。用户看到的是左下角一小块 + 四分之三的空白。
- 根因：`ensurePanel()` 用 `stack.frame = content.bounds` + `autoresizingMask = [.width, .height]`
  来定尺寸，而 `NSStackView(views:)` 生下来 `translatesAutoresizingMaskIntoConstraints == false`
  （最小对象图 spike 读数）⇒ **那两行是空操作**，Auto Layout 只能按 fittingSize 给它。
  R19 记的原因（"只在**捕获环境**里塌，真实 App 里撑满 420×300"）被本轮证伪：
  产品路 `show()` 与捕获路 `windowForCapture` 读到同一个塌法。
- 修法：尺寸所有权写成四条贴边约束（内缩只写在常量里，`edgeInsets` 归零）。
  修后 `stack 396×276`、`NSScrollView 396×251`、`visibleRect 396×251`、
  `cacheDisplay` 从 `drawn=0.0%` 变成 `19.3%`（竖向 10 档 `4 39 62 14 14 15 15 14 10 5`）。
- 空结果那句话两处改：① 它是**淡入**的，而非图层的 view 上 `animator().alphaValue`
  **不提交模型值**（四臂 spike：无图层两臂设完读到 0.000，转 2.1s 仍是 0.000，
  完成回调从不跑）⇒ 加 `wantsLayer`，模型值恒等于终值，淡入只是装饰；
  ② 它原来在列表**下面**，第一次看到帧才发现是"搜索框下 227pt 空白 + 句子在面板最底"
  ⇒ 挪到列表那一格（gap 243pt → 8.0pt）。
- 本轮自己改出来、又被自己判据当场抓住的回归：钉住 stack 之后"内容要多宽"第一次传到窗口，
  一条 40 字查询词把面板从 420 顶到 **899** ⇒ 降句子/搜索框的抗压缩优先级，面板回到 420 并截出省略号。
- 夹具：`quickpick-list / -typed / -empty` × 亮暗 = **6 张**，帧基线 116 → **122**（同提交 `update`）。
- 判据：R19 那条"还拍不到"翻成契约（行、所有权、两条轴的占满比例、可视区 ≥ 2 行、能不能拍），
  另加空结果态一条（在、没藏、`alpha==1`、紧跟搜索框 ≤24pt、横向居中 <3pt、长查询那档面板不许变宽）。
  撤掉一条基于假解释的夹具豁免（"AppKit 夹具不走强制布局"）。
- 变异：M325–M329 + M335 六刀全 CAUGHT；**M330/M331/M333/M334/M336 五刀绿着回来**
  ⇒ 那五处代码（三个子视图的等宽约束、hugging 那行）今天没有作者，本轮**删掉**，
  删后 `list`/`typed` 四张帧逐字节不变。
- 新开：BACKLOG 94（行首 📄 emoji 与 SF Symbol 不是一套语言，且参与搜索匹配）、
  95（在屏像素通道在本机返回"尺寸正确的空图"）、96（本机 `swift test` 会丢一卷测试后半段的 stdout）。

### Tests（R63 的 CI 追加：本轮新写的守卫在 runner 上判了一次假红，同轮改掉）
- run 38683762166 里 `Capture gate` 红了一条，红的是本轮新写的 `sparseByDesignFixtures` 过期守卫：
  `quickpick-empty` 本机未绘制 **97.9%**、runner **94.9%**，而门槛 **95.0%** ⇒
  "这张这次没走豁免分支 ⇒ 名单过期"换一台机器就不成立（整族读数偏移 3pt：85.8→82.1、88.5→85.6）。
  这正是账本 R38 那条"两台机器的读数不能当另一台机器的地板"，而它是在我写新守卫的同一小时里重犯的。
- 修法不是放宽门槛：**换成同一次运行内部的兄弟比较**（空结果态必须比 5 行列表态更空 ——
  本机 2.1% vs 14.2%、runner 5.1% vs 17.9%，两边都成立；"这一格有没有内容"不随 backing scale 漂），
  并把正对照改成"名单里的帧无论这台机器判不判它稀都必过"。
- "帧名与内容相符"从像素里拿出来，新写一条产品入口级判据
  `testQuickPickTypedFixtureShowsFilteredRowsNotAnEmptyList`（typed 必须 1 ≤ 行 < 全量；
  实测 all=5 / typed=2 / empty=0）。Swift 测试 773 → **774**，`--build-tests` 0 告警。
- 同轮第二件：那条守卫的第一版**当场 crash**（`Dictionary(uniqueKeysWithValues:)` 撞上
  同名帧亮暗各一张 ⇒ `Duplicate values for key`），而我在那行上面刚写完"取更空的那一张来比"的注释。
  **注释里写对的规则不等于代码里存在的规则。**

### CI（R62：在屏判据的「缺席」改成逐条点名的硬门 —— 结案 BACKLOG 92）
- 之前：`On-screen interaction probes` 那一步在 runner 上被自带的 240s 看门狗收掉，
  打一句「在屏探针在无头 runner 上不可用」就 `exit 0`。那句话是真的，
  但它让这一卷里**全部 11 条在屏判据**一起免检 —— 包括 R61 刚为侧栏「跟随选中揭示」写的三条。
  ⇒ 61 的回归在 CI 上一条判据都没跑，作业却是绿的。
- 现在：新增 `scripts/probe_coverage_gate.py` + `scripts/probe_coverage_expectations.json`
  与 CI 步骤 `On-screen probe coverage floor`（**硬门**）。它只判形状：
  新加一条在屏判据而不登记「runner 跑得了吗、跑不了为什么」⇒ 红；登记过期 ⇒ 红；
  说跑不了却跑到了 ⇒ 红（逼着改回来，免得攒免检牌）；日志里有断言红 ⇒ 指名报出来。
  对真 CI 那份日志它绿，同时打 `PROBE_NOT_RUN 11/11 …` 逐条点名 —— 绿得有内容。
- 判据：`scripts/tests/test_probe_coverage_gate.py` 12 条；变异电池 M318–M324 七刀全 CAUGHT。
- 顺带结案 BACKLOG 91：R61 说那条闸门「没有读数」是**电池跑错测试**造出来的误判；
  修好 filter 重跑，M313 / M317 都红在「行号漂了视口却动了」上 ⇒ 闸门确实有读数。
### Fixed（R61：程序化选中一条视口外的行时，列表现在会自己滚过去 —— BACKLOG 61 结案）
- 现象：`List(selection:)` **不会选中视口外的行**。store 里选中 1 条，而表格
  `selectedRowIndexes` 是**空**的 ⇒ 详情区在讲一条列表里根本没有高亮的记录；即使把那一行滚进视口，
  高亮也不会回来（要再走一次选中入口才亮）。
- 可达路径**不需要点击**：`HistoryStore.add` 末尾 `reconcileSelection(preferredEntryID: 新条目)`
  把选中给新记录，而新记录的落点是 `EntryOrdering.promotionIndex`（开头那段固定项的长度）
  ⇒ 固定项比视口行数多时，一次普通复制就撞上。
- 修法：新增 `SelectedRowRevealer`（挂在侧栏 `List` 的 `.background`），**只滚不选** ——
  选中集的唯一作者仍是 `List(selection:)`（D-1 修法③）。三条边界各有一条会红的判据：
  已经在视口里就不动、**选中变了才滚（行号漂了不滚）**、以及**推迟一个回合再滚**（同步滚会把上一行的取消选中丢掉，
  实测读到 `selectedRowIndexes=[2,60]` 而 store 只有 1 条）。
- 顺带证伪并回滚了两件上一轮我自己写下的话：① "被选中的那行会一路往下漂出视口"（不漂，每次都被换成新记录）；
  ② 候选修法 `ScrollViewReader.scrollTo(id)`（在产品这棵树上不滚：胶水执行了、id 解析了、视口没动）。
  ②由一条源码守卫钉住：不许在没有重测的情况下把 scrollTo 写回侧栏。
- 判据：`SelectedRowRevealTests`（真值表 4 格 + 两条源码守卫）、
  `UIInteractionProbeTests.testOffScreenProgrammaticSelectionIsRevealedAndNotJumped`（四臂）、
  `testIntakeBehindATallPinnedBlockRevealsTheNewRow`（从 `store.add` 进）；电池 M311–M316。
### Fixed（R60：撤掉一条我自己写的假红 —— 判色前提在 1x 的机器上不成立）
- `testBannerOutTracksWhetherItFadesOrSlides` 在 runner 上报"整卷只找到 0 帧里有那颗红色图标"
  （run 38586812301；原文这次能从日志里读到，因为 R59 加了那条 `grep -E "error: -\["`）。
  根因不是采样粗，是**前提**：那条扫描窗与判色阈值是在本机 2x 上量出来的（五遍都能认出 5–6 帧），
  而 runner 是 1x —— 那颗 ~22px 高的实心红符号几乎没有纯色核心像素。
  ⇒ 认不出图标时改发 `MOTION_TRACK_VOID`（附缩放、单帧最多红像素、扫描窗换算成 pt 的诊断）并**不红**；
  2x 那台机器上前提仍被实测撑住，所以那里认出 0 帧**照旧必须红**（M303 换 needle 后重跑 CAUGHT）。
  这是 R38 那条"两台机器的读数不能当另一台机器的地板"在新写的判据上重犯。
- 更正一句写死的话：带捕获在 runner 上的采样**这次确实变细了**（带 间隔中位 19ms / 整窗 32ms），
  R58 那次是 22ms / 22ms ⇒ 不能当常数，按"两次运行不一致"记。

### Added（R60：把网格的行序钉住；把"重叠为什么量不出来"记账）
- 新判据 `testChangeGridPrintsRowZeroAtTheTop`：`changeGrid` 拆成"位图版 + 薄壳"之后，
  合成位图把差异分别放在顶边 / 底边 / 左边，要求只有对应那一行/那一列亮。
  它补的是 R58 那半年缺的东西 —— 网格只输出字符串、不参与断言，所以行序反了没人知道（BACKLOG 84 结案）。
- 合成夹具从 R58 那条测试里提成共用的 `syntheticPair`（各自一份就会有一份跟着实现变旧）。
- 变异 **M308–M310 全 CAUGHT**（行序翻回去 / 夹具的 `&&` 改成 `||` / 网格里把 band 传成 nil），
  `.scratch/motion-audit-2/r60_mutation_battery.log`。
- BACKLOG 88（新开）：R59 唯一留下的那条看图结论"淡出中的横幅被搜索框盖住"，
  本轮用三条**不依赖颜色**的轴（中灰计数 / 最长均匀段 / 水平直边）都没能复现，三条失败原因不同；
  证据与探针都在 `.scratch/motion-audit-2/r60_evidence/` ⇒ 观察不撤也不升级成判据，
  下一步换捕获方式（关掉动画那一臂与开着那一臂相减）。
- BACKLOG 89（新开）：runner 上"提示条只演了 57ms ⇒ 一帧跳变"那条红，
  57ms < 2×38ms（它自己报的事件内最粗采样）⇒ 那条"变化段"连两次采样都不到；
  缺的是 `judgeMotion` 里一格 `.spanUnresolved`，本轮没改是因为要先补一格覆盖率闸门的夹具
  （那条 not-run 会把 `must_judge=true` 的 `notice-banner` 翻成 UNDERCOVERED 红）。

### Tests（R60：这一轮的验证数字）
- 全量 **766 tests / 36 skipped / 0 failures**；motion 全量 **42 / 3 skip / 0 failures**；脚本 **107 全绿**；
  清洁 `swift build --build-tests` **exit 0、0 告警**（R59 收紧的那道闸门第一次在 runner 上也报 0 ⇒ BACKLOG 87 结案）。
- **产品零改动**：116 帧 vs working 基线 `CHANGED=0 / MISSING=0 / ADDED=0` ⇒ 不换装、不需要 `frame_baseline update`。


### Added（R59：中间态第一次看得清 —— 逐帧图按原始像素竖排，并钉住"这一叠不是一叠同一张"）
- `writeStack`：带捕获那一卷（96px 高）以前和整窗卷共用 `writeStrip`（按 `width/2` 画）
  ⇒ 横幅那条被缩成 38px 的一行色块，"要看的东西正好被缩掉了"。现在它按**原始像素**竖排
  （十帧 1520×980，第 0 帧在最上面，帧间 2px 暗线），并新增判据
  `testBannerFrameStacksAreReadableEvidence`：文件必须存在、宽高必须按原始像素算出来、
  且**这一叠里至少有一对帧真的不同** —— 最后一句是关键：一叠同一张图也能写出正确尺寸的文件。
- 两条新测量：`MOTION_COLUMN`（侧栏 x<280pt vs 详情区 x>280pt 的逐帧变化量与落定帧号）、
  `MOTION_TRACK` + `MOTION_TRACK_BOX`（红色警告图标的质心、外框上下沿、像素数）。
- CI 的动效那一步现在会把**红的理由**打出来：`grep -E "error: -\[" /tmp/motion.log | head -12`。
  现场是 run 38576482491：`testTransitionsAreActuallyRunning` 红了 7.443s、`motion suite exit: 1`，
  而日志里只有名字（自检 `red_test_prints_its_reason` 钉住它，M305 摘掉这句就打红）。

### Fixed（R59：本轮把自己上一轮写进台账的两个"证据数"撤了）
- ~~"撤走横幅时两栏以不同进度消失（侧栏 8–11 帧 / 详情区 13 帧）"~~：
  `transitionFrameCount` 的门槛是**各自峰值**的 15% ⇒ 两块区域各归一化，峰值大（墨多）的那块
  被一条更高的绝对线先判停。新增 `sharedMovingFloor`（两块峰值里较大者 × 同一个 15%）之后，
  本机五遍两栏"最后一个还在变的帧号"**完全相同**（16/16、17/17、17/17、17/17、16/16）。
  ⇒ 那条轴量的不是时间，是墨量。措辞改由 `columnSettlementVerdict` 从帧号生成，
  并由合成真值表 `testSharedFloorColumnComparisonIsATruthTable` 钉住四种形状（M306/M307 有牙）。
- ~~"图标质心从 42 漂到 29px ⇒ 横幅在被抬走"~~：图标淡到判色线以下时高饱和边缘先脱落，
  剩下的像素聚在哪半边质心就往哪边漂 ⇒ 那条轴量的是**阈值在动**。
  改成只看强帧（像素数 ≥ 首帧一半）并新增**外框上下沿**这条轴之后：强帧跨度 2.6/0/0/0/0px、
  外框 4/5 遍一格没挪（[29,50]→[29,50]）⇒ "上移 6.5pt"作废。
  也没写成"绝对没动"：第 1 遍下沿上移 4px，正落在脱落量级里，±2px 容差分不开"脱落"与"被裁"。
  顺带**部分恢复** R22 那句"它是淡出，不是塌陷"——淡出这一半被外框证实了。
- 留在的那件事实只有一条，且**没有判成缺陷**：第 5 帧起侧栏搜索框已经上移到横幅那一行、
  画在还没淡完的横幅文字之上（字的下半是被**盖住**的，不是被裁的），详情区那半截尾巴还在原高度淡。
  ⇒ 形状是**层叠**（`.bannerOut` 只给 `.opacity`、布局却已重排），要不要修等真屏幕（批次 59.1 / BACKLOG 85）。
- 测试目标里那条 `warning: variable 'a' was never mutated`（R58 引入）修掉。
- `scripts/motion_floor_expectations.json` 里 R57 那句"runner 侧还没有一次带捕获的读数"更正为实测：
  带=抓帧中位 5.6ms / 间隔中位 22ms / 760x48px，整窗=14.1ms / 22ms / 760x588px
  ⇒ **带在 runner 上买到的是时间不是分辨率**（两臂过渡帧数都是 3）。BACKLOG 83 结案。

### Changed（R59：那条"构建 0 告警"以前不编译测试目标）
- CI 的 `Build (must be warning-free)` 改成 `swift build --build-tests`，并在红的时候多打
  `grep 'warning:' | head -12`（红了要能读是哪一条）。以前它只编译 `Sources/` ⇒
  测试目标里的告警从来没进过这条闸门（R58 那条告警在 `swift test` 输出里明明白白，两次 CI 都是绿的）。
  收紧前先量了清洁基线：`swift build --build-tests`（全新 scratch 目录）**exit 0、0 条告警**。
  新守卫 `test_build_step_gates_the_test_target_too` 把 ci.yml 里那段真脚本抽出来跑两遍
  （0 告警必须绿、1 告警必须红且能读到原文）。runner 的 Swift 6.1.2 会不会报出新告警：下一次 CI 见（BACKLOG 87）。
- 动效那一步**仍然**是 `continue-on-error`：本轮只补了"理由要能读"，没改成有闸 ——
  改成有闸需要一次"红的确实是产品而不是环境"的样本（BACKLOG 86）。
- 判据失败**不许变成崩溃**：`testBannerOutTracksWhetherItFadesOrSlides` 里那条地板从
  `XCTAssertGreaterThanOrEqual` 改成 `guard … else { XCTFail; return }` —— M303 第一遍跑出的是
  BROKEN-MUTATION：断言红之后代码继续 `seen[0]`，空数组越界把测试进程带走，
  "Test Case … failed" 那行根本没打出来。


### Fixed（R58：那条分带尺是上下颠倒的 —— 改一行、写真值表、再查出"CI 看不见新读数"）
- `changedFraction(band:)` 的归一化带**方向修对了**：它原来按 `yStart=(1-maxY)*h` 取值，
  注释理由是"缓冲区第 0 行是画面底边"，而 R57 实测第 0 行是**画面顶边**
  （带那一帧与整窗帧的第 0–95 行逐像素相同 0.000、与末尾 96 行差 0.954）。
  ⇒ 此前这个文件里 7 处 `band:` 量的都是镜像位置（BACKLOG 80 结案）。
- 新判据 `testBandRectMapsToTheEndItClaims`：合成位图把差异只放在上/下/左三处，
  六格方向断言 + 一格"夹具自己不对称就红" + 一格"整幅=0.2"。
  它在坏的映射上先红了四格，横轴与整幅那两格全绿 —— 红的形状本身就是诊断。
  七个调用点逐个重算：两条**关于中线对称**的（详情区、列表中部）一直没跑偏、
  也一直没能力发现这个 bug；`表格区` 上下各偏 0.02；实质跑偏的是
  `// 横幅那一条` 与 `侧栏第 4 行的星标列`（后者读数 0.221 → 0.260）。
- 本轮真正的发现是**第二层错**（R57 自己带进来的）：`// 横幅那一条` 从 R57 起传的已经是
  **带捕获那一卷**，同一个矩形量的是"带里再框一条 9.5pt 的窄缝"。同一判据三个数：
  镜像错 帧 11/≈121ms、嵌套错 帧 6/≈66ms、修完 帧 15/≈165ms，**三个都没让任何判据变红**。
  ⇒ 新守卫 `testNoTestFramesABandInsideABandCapturedFilm`：带捕获那一卷上不许再传非 nil 的 `band:`；
  `testSlidingRoleSettlesWithinItsBudget` 去掉那层嵌套框（那一卷的"整幅"就已经是那条带）。
  守卫的第一版**假红**（谓词只看"函数里同时出现带捕获场景与 band 矩形"），
  被 `testListRowsDoNotAnimateAndNothingClaimsTheyDo` 顶回来 ⇒ 谓词改成一点点数据流。
- `.github/workflows/ci.yml` 的动效读数摘录从**硬编码前缀白名单**改成
  "先报 `MOTION_LINES=N`，再全打 `^MOTION_`"：R55 的 `MOTION_GRAB` 与 R57 的 `MOTION_BAND`
  都没进过那份列表 ⇒ run 38570965657 里"runner 上带捕获成没成功"在日志中查不到
  （只剩 `judged=4/4`，而带捕获之前的 R56 也是 4/4 ⇒ 两个形状分不开）。
  CI 自检加一格 `family_not_in_any_list`（新 BACKLOG 83；M299 把白名单放回去就红）。
- 新开两条：**BACKLOG 84**（分带归因网格的行序现在对了，但没有任何判据钉住它）、
  并复核了历史结论：M1 那条"斜坡来自右侧详情区"是按**列**读的 ⇒ 不受影响。
- 变异 M295–M300 六支全 CAUGHT（y 倒回去 / x 也倒回去 / 带永远不生效 / 把嵌套框套回去 /
  CI 白名单放回去 / 守卫谓词空转）。
- 全量 761 例 / 33 skip / 0 失败、`swift build` 0 告警、脚本 106 全绿、116 帧逐字节不变 ⇒
  不需要 `frame_baseline update`、不换装。

### Added（R57：横幅那两臂第一次被判到，代价是先发现我的分带尺是上下颠倒的）
- `Scenario` 多一个可选的 `captureRect`，`Grabber` 多一个 `rect`（默认 `nil` = 整窗，旧行为不变）：
  横幅两臂从整窗（1520×1346px）改拍**顶部那条带**（1520×96px，面积 1/14），仍然按 2× 拍。
  本机三次连续跑实测：抓一帧中位 39.5–39.8ms → **4.4–4.6ms（≈9 倍）**，
  整卷中位间隔 44–45ms → **9–10ms**，同一场景过渡帧数 3–4 → **10–11**，
  `MOTION_RESOLVE_SUMMARY judged=4/4 not-run=-`（这一族以前在本机是 2/4）。
  这结案的是 BACKLOG 77：那两臂量不到不是产品没演，是量尺太慢。
- 新判据 `testBandCaptureIsCheaperAndStillSeesTheMotion`（带 vs 整窗，同进程交错跑，两臂各两遍）。
  里面有一条**位置同一性**：带的那一帧必须与整窗那一帧的同一头逐像素相同（实测 0.000）、
  与另一头明显不同（实测 0.954）。这条存在是因为本轮真的犯过：第一版带抓到了窗口底部，
  而四条"有没有变化"的前提全部通过（横幅撤走后下面整块列表在位移，位移也是变化）。
- 新守卫 `testBandCaptureIsWiredIntoBothBannerArms`：两臂都声明 `captureRect`、
  `recordFrames` 真的把 rect 传进 `Grabber`、`tick()` 真的读它、登记表两臂都是 `must_judge=true`，
  外加一条谓词正对照（没有 `captureRect` 的合成文本必须返回 false）。
- 登记表 `motion_floor_expectations.json` 改回严格：横幅两臂 `must_judge=true`、`thin_warnings` 清空。
  理由写在 note 里，并且**把代价也写进去**：runner 上还没有一次带捕获的读数，
  CI 若红在 `UNDERCOVERED` 是闸门在说真话，不是这一改坏了。
- 新开三条账：**BACKLOG 80**（`changedFraction(band:)` 的归一化带上下颠倒 ——
  这个文件里 7 处 `band:` 调用点量的都是镜像位置，本轮绕开、下一轮专门修）、
  **81**（带高 48pt 没有"必须盖住横幅"的判据）、**82**（离屏帧里半透明的横幅底合成到白底上，
  按帧量横幅对比度量的不是产品看到的那一层）。
- 变异 M286–M294 九支全 CAUGHT：M286 把带挪回本轮我犯过的那个位置、M287 `captureRect` 变装饰、
  M288/M289 分别打位置同一性的两边、M290 新读数退回 print、M291/M292 放回放行与把地板算成 0、
  M293/M294 分别断一臂的接线与登记表的方向。
- 产品代码零改动，116 张帧逐字节不变 ⇒ 不需要 `frame_baseline update`、不换装。

### Added（R56：读数有了第二条通道，而它第一次跑就救回 54 行）
- `MotionFilmstripTests` 的 44 处 `MOTION_*` 读数全部改走新的 `emit`：
  同时 `print` 与追加 `<outDir>/motion-readings.log`（第一次整份重写、之后追加、与胶片同目录）。
  动机不是"多一份日志"：这条 stdout 通道已被观察到**整次失效**
  （CI run 38543090198、本机 18:58 那次），而覆盖率地板与 R55 的归因都住在它上面。
- `.github/workflows/ci.yml` 的 `Motion filmstrip` 把两条通道**取并集**并打
  `MOTION_CHANNEL_UNIONED=1 stdout=N 文件=M`；两条都空时打 `MOTION_READINGS_FILE_ABSENT=1`
  （下一步的 `NO_RESOLVE` 红从此有一个前因可查）。
- **当场兑现**：加固后第一遍本机运行 stdout 只剩 2 行 `MOTION_*`，文件通道有 56 行。
- 新守卫 `testMotionReadingsUseTheFileChannel`：正对照（两种 `print` 写法都必须被抓到）、
  源码里不许有游离 `print("MOTION_`、marker 必须在文件里（先于"末尾两格"那一判——
  只比末尾会让**上一遍的旧文件**把红写成假理由）、追加顺序、与胶片同目录。
- CI 自检 `motion` 那一步从 4 个形状加到 9 个：整片丢、半丢（结论行只在文件里）、两条都空。
- 变异 M277–M285 九支全 CAUGHT。其中 **M285 在提交前把一个设计错误顶了回去**：
  第一版写成"以文件为准（换掉 stdout）"，而文件也可能只写了一半 ⇒ 已改成并集。
- 机制仍未证实（丢的是子进程 stdout；stderr 与 FileManager 写盘不丢；三次 0/全/2 行）⇒
  BACKLOG 79 的结案条件收窄成"查机制"。
- 产品代码零改动，116 张帧逐字节不变 ⇒ 不需要 `frame_baseline update`。

### Added（R55：那条"最粗 97ms 一帧"第一次有了归因，而真读数把我第一版的分档打回来了）
- `Grabber` 逐帧记 `cacheDisplay` 的毫秒数，`recordFrames` 打 `MOTION_GRAB … 抓帧中位/最慢 … 像素 …`，
  最慢值随 `Film` 一起带出（默认 −1 = "没量"，不是"抓帧不花钱"）。
- 新增 `GrabAttribution` 四档（`probe-grab-bound` / `grab-dominates` / `not-the-grab` / `grab-unmeasured`），
  粗钟 not-run 行追加 `归因=…（解释=NN%…）`；两处现场（横幅、热图淡入 A/B）都接上，同一行、英文令牌。
- **两档版被本机真读数证伪后改成三档**：97ms 间隔 / 抓帧最慢 87.9ms —— 抓帧解释了 91%，而两档版把它报成
  "不是抓帧的锅 ⇒ 先别动捕获尺寸"，那是**反向的建议**。
- 新增 `testGrabCostScalesWithCapturedArea`：交错抓三档区域各 9 次取中位 ⇒
  全视图 中位 **40.2ms**、横幅带 中位 **8.4ms**、小块 中位 **3.1ms**（端到端 12.3–13.0 倍 vs 面积 29.8 倍）⇒ 成本 = 固定开销 + 面积项，
  "缩小捕获区域能省采样时间"这条建议**从此有判据**；早退分支前先断言"确实抓到了东西"（>0.5ms）。
- 新增接线守卫 `testGrabAttributionIsWiredIntoTheCoarseNotRunLines`（三格：结论行、`Film` 拿数、`tick` 计时）。
  它自己被抓过一次：`contains("grabMilliseconds.append")` 会命中**守卫自己的消息文本** ⇒ 改为按 `func tick()` 区域搜。
- 变异 M269–M276 八支全 CAUGHT（第一遍 7/8，M276 逃逸一次，修完守卫再 CAUGHT）。
- 一条新盲区记账（BACKLOG 79 / U-82）：同一条命令本机三遍里**有一遍 `print` 全丢**而 stderr 正常 ⇒
  R55 的归因与覆盖率地板都住在这条通道上，修法候选已列（首选"读数同时写文件"）。
- 产品代码零改动，116 张帧逐字节不变 ⇒ 不需要 `frame_baseline update`。

### Added（R54：热图相邻档第一次有判据 —— 结论是"梯子没错，我的轴错了"）
- 新增 `testAdjacentHeatLevelsAreSeparableOnTheRightAxis`：五档两两相邻（4 对）× 亮暗 × 1×/2×
  = 16 条读数，量**格子内部**，距离取**逐像素三通道最大差**（`meanMaxChannelDelta`），
  地板沿用 R45 的 `perceptibleBand255 = 18`。实测最小一条 `dark empty→bucket1 = 30.00` ⇒ **全部通过，
  产品数值一个没改**（BACKLOG 71 结案）。
- 撤回 R51 写进台账的"暗档 0 次 vs 1 次只差 4/255 ⇒ 分不开"：那是**亮度**轴；
  `empty` 是灰（`primary`）、四档是蓝（`accent`），同一对在 B 通道上差 30、亮度上只差 2.16。
  按旧结论去抬 `empty` 会把一张没病的图改响（撞"不喧宾夺主"）。
- 新增 `fillBand`（与 `ringBand` 严格互补的格子内部）与其真值表 8 格；
  其中一格把**坏掉的尺子夹具**抓了出来：`NSBitmapImageRep.setColor(_:atX:y:)` 在整数格式位图上
  不落地且不报错，两幅"不同色"的图读出来差 0.00 ⇒ 改成直接写 `bitmapData`。
- 实测补一条与 R45 相反的边界：**整格填充对尺度不敏感**（1× 与 2× 逐条相同），
  R45 那句"1× 比 2× 低 20%–25%"只成立于 1pt 描边。
- 变异 M264–M268 五支全 CAUGHT（M264 改产品令牌、M265 把轴换回均值 ⇒ 都会红）。
- 产品代码零改动，116 张帧逐字节不变 ⇒ 不需要 `frame_baseline update`。

### Fixed（R53：结论行挡在 skip 之后，等于每次跳过都把它删掉）
- `testNativeRowMoveIsVisibleToTheRuler`：`nativeMoveVerdict` 与 `MOTION_NATIVE_MOVE 判定=`
  挪到 `requireObservableMotion` / `requireAppWasActive` **之前**，`XCTFail` 留在之后。
  以前 runner 一跳过这一臂，日志就只剩两臂读数、没有结论行
  （run 38543090198 与 38543812477 两次实测），而那正是 R50 要消灭的含糊。
- 新增顺序守卫 `testNativeMoveVerdictPrintsBeforeTheSkipGuards`（结论行在、闸门在、顺序对）。
- `region(in:named:)` 从 `contains` 改成按**行首**匹配：守卫必须在源码里写下被守卫者的名字，
  `contains` 于是先命中**守卫自己那一行**，区域变成守卫自己的函数体 ——
  本轮第一版就是这么红的，而且三条断言里有两条"通过"（它们在读守卫自己写的字面量）。
- 撤回 R51 写进台账的那句"暗档 0 次 vs 1 次只差 4/255 ⇒ 分不开"：那是亮度轴，
  该步实际是灰(`primary`)→蓝(`accent`)的色相翻转，B 通道差 30。`heat_ladder_preview.py`
  现在同时打 Δ亮度与 Δ各通道最大差。
- 产品代码零改动，116 张帧逐字节不变。变异 M260–M263 四支全 CAUGHT。

### Fixed（R52：覆盖率地板第一次在 runner 上红，红的是登记与实际不符）
- `motion_floor_gate.py`：`NO_RESOLVE` 之后新增一行 `MOTION_FLOOR_SKIPS`，
  把日志里 `Test Case … : Test skipped - <原因>` 逐条打出来。
  以前 CI 那一步只 `grep MOTION_NOT_RUN=`，而 XCTest 层 `XCTSkipUnless` 的中文原因不带这个前缀
  ⇒ run 38543090198 那种"整族一条读数都没有"的红**没有名字**（R36 的规矩断了）。
- 登记表 `motion_floor_expectations.json`：`notice-banner` 从 `must_judge=true` 改成
  放行 `clock-coarse-in-window` / `premise-not-visible`，note 里写死依据
  （run 38538371464 最粗 76ms vs 声明 150ms；run 38543812477 同一理由；本机一直是 premise-not-visible）。
  **登记是测量，不是愿望**（D-111），且新增自测要求任何放宽都必须留 run 号或夹具出处。
- 新增 `MOTION_FLOOR_THIN`（**不红**）：横幅两臂同场缺席时打一行，指向 BACKLOG 77。
- 新增 `thin_warnings` 段；`MOTION_FLOOR_OK` 从"只有一条结果都没有才打"改成"没有红就打"，
  与 THIN/SKIPPED 共存。
- 自测 101 → **105**：`under_covered` 那一格换成"`judged` 与 not-run 名单不自洽"的形状 ——
  因为地板从 3 降到 2 之后，`UNDERCOVERED` 已无法单独红（任何 must_judge 臂缺席都会先撞 `BAD_REASON`）。
  这一格失效是 `test_ci_report_selftest` 抓住的，不是我发现的。
- 更正 R51 写进台账的热图台阶结论：那句"暗档 0 次 vs 1 次只差 4/255"用的是**亮度**轴，
  而该步是灰→蓝的**色相**翻转（B 通道差 30）⇒ 结论撤回，BACKLOG 71 改判轴（R53）。
- 产品代码零改动、Swift 判据零改动、116 帧逐字节不变。变异 M254–M259 六支全 CAUGHT。

### Fixed（R51：上一轮那条"同步写盘"判据测错了对象）
- `CapturePathWriteBudgetTests.testAddingACopyWritesNothingOnTheMainThread` 从"目录快照不许多文件"
  改成"**把注入的写队列堵起来**"：堵着 ⇒ 盘上不许出现 `history.json` / `daily-copy.json`；
  放开闸门 ⇒ 两个都必须出现（对照组）。
  旧那条在全量跑与 CI（run 38538371464）上都红，而红得不对 —— 多出来的
  `history.json.sb-11faeef9-PWSNBE` 是**后台** `saveQueue` 的原子写临时文件，
  目标禁的是"**同步**磁盘写"，异步写正是设计要求的形状。
- 新增 `testAddingACopyWithANearlyFullArchiveStaysInsideBudget`：480 条的库 + 堵住的队列，
  测"主线程只剩这条链"时一次复制花多久（本机 median 2.34–2.49ms，门槛 20ms 按最差那一遍推导）。
  旧的两条时长判据只测了几条记录的小库，而这条链的成本随库大小增长（0.55ms → 2.47ms）。
- 前提断言的地板与造库数量脱钩（`fullArchivePremiseFloor = 400`）：
  第一版写成 `fullArchiveEntries - 20` ⇒ 自适应阈值恒真，M251 才把它抓出来。
- 注释与失败消息里那句"这条测的是整库快照"被 M253 推翻并改正：快照只占 median 的约 1/5，
  红了之后要先分段量（BACKLOG 76），不要直接搬 `saveSnapshot`。
- 删掉随旧判据一起失效的两个辅助函数。变异 M249–M252 四支全 CAUGHT，M253 按设计绿（灵敏度实测）。
- 产品代码零改动，116 张帧逐字节不变。

### Fixed（R50：行移动那条判据先修探针，再让结论分三态）
- `TableProbe` 的 move 臂在宣布一次 `moveRow` 之前把**六行文案全改了**（`·已挪`），
  而产品那条分支不 rename（`QuickPickController.rebuildRows` 的文案变化走 `plan.reloads`）。
  ⇒ 两臂的像素差里混进了与动画无关的"文字变了"，那次红不能算在产品头上。删掉 rename。
- `testNativeRowMoveIsVisibleToTheRuler` 的结论从两态改三态：
  `动了 / 瞬移 / 采样错过`（新增纯函数 `nativeMoveVerdict`，真值表 7 格）。
  以前只有一句"帧数 ≥2 否则红"，把 runner 那组 `开 1 帧 0.047 / 关 1 帧 0.047`
  和"两帧数都是 1 但峰值差很远"混成同一种红 —— 而前者是产品侧候选缺陷，后者是今天量不了。
- 新增日志 `MOTION_NATIVE_MOVE 判定=… 峰值容差=…`，把结论与判据用的数一起打出来。
- **没有**把这条红改成 not-run：它有名字、有读数、有同一卷里 `row-insert` 的阳性对照。
- 产品代码零改动，116 张帧逐字节不变。变异 M245–M248 四支全 CAUGHT。


### Added（R49：目标里那条"采集路径不许同步写盘"第一次有了会红的判据）
- 新增 `CapturePathWriteBudgetTests`（3 条判据，全部从产品入口 `HistoryStore.add` 进入）：
  ① 复制之后临时目录**一个文件都不许多**（尺寸@mtime 快照），并带一条"去抖到期后文件必须出现"的
  对照组 —— 不许靠"根本没接上盘"来绿；② `add` 占住主线程的中位与 p95 各一条门槛，
  门槛从实测推导（本机 median 0.56–0.63ms / p95 1.28–1.46ms / max 3.08ms ⇒ 10ms 与 40ms）；
  ③ 尺子自己的真值表 7 格（偶数取插值、两端、乱序、单样本、空表必须 NaN、n=5 时 p95 就是最大值）。
- 这条要求此前 40 轮**没有任何判据在管**：把同步写盘塞回 `DailyCopyLedger.recordCopy`，
  没有一条用例会红。现在会红（变异 M240 实测，红在"账本在 `add` 返回之前就已经落盘"）。
- BACKLOG 73 结案：R48 那次 260ms 抓帧空档**不在产品的采集链上**（产品侧 0.6ms 中位），
  它是探针自己对新生子树的首帧渲染（R11 记过同一量级）；旁证是开臂 `粗260` 而关臂 `粗6`。
  剩下的产品侧问题另开 BACKLOG 74（淡入第一帧的真实成本）。
- 变异 M240–M244 五支全 CAUGHT；M240 是**产品侧**变异（本轮第一次改 `Sources/` 做变异），还原干净。
- 产品代码零改动（`Sources/` 与提交前逐字节相同），116 张帧不变。


### Fixed（R48：动效时长那把尺补了连续性，判定补了分辨率，一句旧结论被撤回）
- `changedRunElapsedMilliseconds` 名叫 "run" 却**不要求连续** ⇒ 改名 `changedSpanElapsedMilliseconds`
  （行为不变），新增 `contiguousChangedRun`（取**含峰值**的那一段连续变化 + 段内最粗采样）。
- 那条淡入 A/B 的判定**缺分辨率轴**：`judgeMotion` 从 R2/R8 起就有"段内最粗采样 > 0.5×声明 ⇒ 判不了"
  这一档，而 `fadeVisibility` 只比"时长 vs 声明"。现在它有三态：看得见 / 看不见 / **钟太粗**
  （`MOTION_NOT_RUN=clock-coarse-in-window`，不红）。
- **撤回一条写进台账的结论**：R11 起的"离屏 `cacheDisplay` 对纯 opacity 淡入可见性 = 0"是错的 ——
  本轮第一次给这条 A/B 补上条带图，里面出现过**半透明中间态**。正确说法是"不每次都抓得到"，
  所以 `notVisible` 分支的文案从"看不见"改成"今天没抓到"。
- 那条 A/B 现在打印 per-run 形状（`MOTION_HEAT_RUNS … 起–止@峰值/粗…`，时刻相对卷首）
  并为三臂各出一张条带图。
- 产品代码零改动，116 张帧逐字节不变。
- 新增判据：`fadeVisibility` 真值表 15 格（新增 3 格钉分辨率轴）+ `contiguousChangedRun` 8 格
  + 调用点守卫 1 条（段来源、臂归属、时长轴、分辨率轴是否传入）。
- 变异对照 M230–M239 十支；其中 M237 把本轮守卫的**前两版**都顶红（数词频、固定取两行），
  M239 第一版是 **BROKEN-MUTATION**（`coarseRunRatio` 忘了写 `Self.`，编译不过）。


### Fixed（R47 · 那条 A/B 判的是采样，不是淡入）

- `MotionFilmstripTests.testHeatmapFadeIsNotVisibleToThisRuler` 的判定轴换掉：
  原来用**帧数**（`onSpan == offSpan`）判"这把尺看不看得见纯 opacity 的淡入"，
  而帧数是同一个文件里自己宣布过"随采样相位漂（本机 2/3/2）"的量。
  R46 真日志当场把它打红：`开 帧数=2 峰值=0.226 / 关 帧数=1 峰值=0.226` —— 峰值完全相同。
- 抽成纯函数 `fadeVisibility(...)`，四个门槛：**时长轴** + **下限 0.3×声明** +
  **上限 声明+2×间隔** + **归因看两遍里较短的那个**；两遍不一致 ⇒ `.inconsistent`（只打印不红）。
- 上限是被实测逼出来的，也是本轮真正的收获：本机反复抓到 `258–307ms` 的变化段，
  而声明只有 160ms ⇒ 那不是这条淡入。没有上限，判据会把它读成"尺子终于看见了"，
  并催我们把场景放进 `Scenario.all()` 当真判据 —— 那是把探针的毛病当产品进步。
  加上限之后 3/3 稳定报"看不见"。
- 判据 12 格真值表 + 变异 **M223–M229** 七支（每支拆掉一个门槛，各自被不同格子抓住）。
- **把 `流畅度` 这一维写死**：离屏 `cacheDisplay` 抓模型树、纯 opacity 交叉淡活在 presentation 层
  ⇒ 这条通道对淡入的可见性是 0；抬它要换通道（真屏抓帧 / presentation 采样），不是再改判据。
  这一维六轮停在 13/20，从今天起不再每轮虚涨。
- 新开 BACKLOG 69：那段 258–307ms 到底是什么 —— 若它来自账本去抖落盘，
  性质就从"测量噪声"变成"**采集路径上有同步磁盘写**"（目标里明令禁止），优先级立刻升高。
- 产品零改动（`Sources/` 未变）、116 帧不变、脚本 101 条不变、0 告警；本轮不换装。


### Added（R46 · 动效覆盖地板会报"掉了谁、为什么"了）

- 新增 `scripts/motion_floor_gate.py` + `scripts/motion_floor_expectations.json`，
  `Motion coverage floor` 那一步从一段 shell（只问 `judged<2`）换成读登记表的脚本。
  来历：R44 那次 `judged=4/4` 退到 `3/4`（`notice-banner-dismiss` not-run）**整步仍然绿**，
  而我是人肉对比三次 run 的日志才发现的。
- 八条规则：没有结论行 / 少一臂的键 / 多一臂 / 清单外的盲区 / not-run 没理由 /
  理由没登记过 / 判不够地板 / 登记成"永远判不了"却判到了。
  每条一支变异（M216–M222 全 CAUGHT），因为这道闸门是**判据的判据**。
- 两条方向上的取舍写进 D-105：**红不红取决于登记，不取决于读数** ——
  会随采样漂的臂判到不红、判不到也不红（否则恒红，守卫最后被人删）；
  而"跑完了却没有结论行"从旧版的 `exit 0`（免检牌）改成红。
- **不判帧数**：`MOTION_SUMMARY <arm>=<帧数>` 由采样相位决定（R2 实测 2/3/2）。
- 登记表里的理由来自**本机真跑一遍**产出的日志，并把它原样收成正对照夹具
  （`scripts/tests/fixtures/r46_motion_local.log`）：闸门跑这份真日志必须红，
  且红的正是 `BAD_REASON` + `UNDERCOVERED` 两格。
- `Motion filmstrip` 那一步把 `MOTION_NOT_RUN=` 单独打、不截断
  （`head -24` 正是 R44 那次"not-run 查不到为什么"的成因）。
- 脚本自测 83 → **101** 全绿。Swift 侧零改动 ⇒ 742/29/0 与 116 帧不变；本轮**不换装**。
- 新开 BACKLOG 68：跑真日志时撞见热图淡入那条 A/B **用帧数当判据**，
  而两臂峰值完全相同（0.226 / 0.226）⇒ 红的是尺，不是产品。R47 的靶。


### Added（R45 · 热图悬停那一圈第一次有像素证据，画法抽成 `DailyCopyHeatmapCell`）

- 新增 `HeatmapHoverEvidenceTests`（7 条判据）：描边带可见性（五档 × 亮暗 × 1×/2× = 20 读数）、
  归因（带外必须不变，10 读数）、**不喧宾夺主**（悬停差 ÷ 数据全幅度 ≤ 1.0，10 读数）、
  带选择器真值表 7 格、令牌真值表、源码路由守卫、夹具自检。
- 产品侧只有一个搬运动作：单格画法从 `DailyCopyHeatmapView.cellView` 抽成
  `DailyCopyHeatmapCell(cell:isHovered:calendar:onHover:)`，裸的 `0.55` 提成
  `VisualHeat.hoverRingOpacity(isHovered:)`。**既有 112 张帧逐字节不变**（`CHANGED=0`）
  ⇒ 这是一次可证的行为保持重构，不是改外观。
- 帧基线 112 → **116**：新增 `heatmap-cell-strip-still` / `-hover`（90×140，亮暗各一）——
  112 张里以前**没有一张**带悬停态，"悬停"这个状态在取证面上等于不存在。
- 读数：描边带均值通道差 36.10–75.50/255（地板 18 = 最小读数的一半）；带外 0.00；
  悬停/数据全幅度倍率 0.46–0.75。`VisualHeat.hoverStroke` 那句"发丝线在深色格子上会消失"
  第一次有了读数支持：**1× 那一臂系统性比 2× 低 20–25%**，但最弱一臂仍是恰可察觉台阶的九倍。
- 修掉本轮自己的两个尺子错误：① 描边带用"方框减角块"切掉了真描边 ⇒ 报假 ✗，改用圆角矩形 SDF；
  ② 夹具取 `prefix(3)`（最老三列全是空档）⇒ 帧存在但被摄对象不在帧里，改 `suffix(3)` 并补夹具自检。
- 重构把 R9 时代两条按 `func cellView` 取区域的源码守卫搬到了新的主人那里
  （**一条断言都没放宽**），并给区域助手补了"同名成员取到哪一个"这一格。
- 新开 BACKLOG 66（动效覆盖地板在 runner 上 4/4 → 3/4 而闸门仍绿 ⇒ 需要一个会红的形状）
  与 67（悬停"触发"那一半仍只能人眼验，挂在批次 22/47.1）。
- 验证：742 tests / 29 skipped / 0 failures、0 告警、闸门 `红=0 NOT_RUN=0`、脚本 83 全绿、
  变异 M210–M215 六支全 CAUGHT。


### Added（R44 · 判据会读"派生键"了 —— 调用点级的动效守卫推广到 NoticeBanner）

- 本轮**零产品改动**，改的是尺。R42 那条"调用点级"守卫要推广到 `NoticeBanner` 时被发现读不懂一种合法写法：
  `ContentView:32` 的驱动键是 `noticeSignature`，而它（`:36-44`）把五条回执的存在性压成一个 bitmask
  ⇒ 按名字匹配会把**五条全误报成没电**，而那五条确实有电（R22 量过像素）。
- 新增 `drivingStates(for:in:)`：键里的裸名字若在本文件有 computed property 定义，
  就把 body 点到的标识符并进状态集合（点路径与最后一段都算）。**只展开一跳、只增不减**：
  读不懂 ⇒ 退回按名字匹配，既不放行也不报错 ——
  "读不懂就红"会逼人删守卫（R34 / R21b 那一族），"读不懂就放行"是免检牌（R39b 那一族）。
- 剩下的假阴性风险由变异钉住：**M207** 从签名 body 里删掉一条 ⇒ 只有那一条红。
- 判据 +2 条（`testNoticeBannerCallSitesArePoweredByTheirDerivedKey` + 派生键展开的 5 格真值表）
  与 4 个纯函数；变异 M206–M209 四支全 CAUGHT（needle 全实测抄来，且落在排过序的数组上 ⇒ 顺序稳定）。
- **BACKLOG 64 只做了一半**：热图那两处是 `if 布尔 { … } else { … }` 的**分支**形状，
  现在的扫描器只认"组件调用点 + `if let`" ⇒ 这条继续开着，别当成推广完了。
- 本轮**不换装**（没有任何"只有装上新包才看得见"的东西）；112 张帧逐字节不变。
- 验证：735 tests / 29 skipped / 0 failures、`swift build` 0 告警、闸门 `红=0 NOT_RUN=0`、脚本 83 全绿。



### Fixed（R43 · 导出/导入那三条回执：一件事被说两遍，而失败那句又是英文）

- **R41 那一族其实没收口**：界面上还有三个出口在把 `error.localizedDescription` 拼进回执
  （`SettingsView:177` 导出反馈、`SettingsWindowController:94` 导出存档、`:104` 导入存档），
  而这些错误类型都不是 `LocalizedError` ⇒ 用户看到的是
  "The operation couldn't be completed. (…)"。本轮三个一起接进同一层措辞。
- 新增 `Utilities/ReceiptWordings.swift`：`FeedbackExportReceipt` + `ArchiveTransferReceipt`
  两个纯枚举。界面只说"发生了什么 + 下一步"，**原文一律进 `LifecycleDebugLogger`**（D-100 同一条分工）。
- 「导出反馈数据」原来**同时**弹模态与发行内回执 ⇒ 删掉模态，只留行内
  （仓库其余三处回执都是行内）。
- 一句被写成判据的前提："导入失败……记录没有任何变化"是真的，因为 `importArchiveJSON`
  的抛出点在 `entries` 被改之前 —— 判据直接比这两个位置，以后改成就地流式写入会先红。
- **两条顺带查出的**：① `receipt-line` 那张帧从 R14 起画的是**产品没说过的一句话**
  （全仓 grep 不到那句文案）⇒ 新增"夹具不许手写回执文案"的按族判据；
  ② 换成真文案后 `contentMustFit` 当场红两张（底行 18.4% / 20.2% 有墨）
  ⇒ 那张帧一直在裁自己，56 → **72pt** 才放得下。
- 判据 +7（真值表 2 / 接线 3 / 夹具文案 2），变异 **M199–M205** 七支全 CAUGHT，
  needle 全部从 `--measure` 的失败消息原文抄（R42 立的流程第一次真跑）。
- 新开 BACKLOG 65（`ReceiptLine` 的 × 顶对齐 vs 横幅动作垂直居中，本轮判过、刻意不动）；
  BACKLOG 64 的推广被一条真问题挡住：`NoticeBanner` 那五条的驱动是**派生键** `noticeSignature`，
  按名字匹配会全部误报 ⇒ 先让判据会展开派生键。
- 本机已换装：`INSTALL_RESULT=ok`、sha `a5c52cbe…`、`SMOKE_OK=1`、存档 103 → 103 条。
- 验证：733 tests / 29 skipped / 0 failures、`swift build` 0 告警、闸门
  `有名字的红=0 NOT_RUN=0`、脚本 83 全绿、帧基线 112（改名两张，同 commit update）。


### Fixed（R42 · 回到动效本体：三处回执的淡入，两句是死的、一句推不动）

- **复核把原账改窄也改准**：BACKLOG 53 写的是"SettingsView 全文 0 个 `withAnimation` ⇒ 三处回执瞬间插入瞬间消失"，
  那是**按关键字数的**。逐调用点量完（`.transition` 只有在外层事务被动画化时才演）：
  两处是**死声明**（导出反馈 `:555`、导出/导入历史 `:619` 的父容器一条 `.animation` 都没有）、
  一处**缺半个键**（排除名单 `:489` 的键只有那份持久化字符串 ⇒ 名单没变的那两种情况推不动）、
  一处**本来就有电**（清空回执 `:659`，而且它根本不是 `ReceiptLine`）。
- 产品 +3 行：两处补 `.animation(contentFade, value: <门控> == nil)`，排除名单那处**再加一条**
  键为 `exclusionReceipt == nil` 的驱动。元组键那条路被编译器否掉（Swift 的元组不 conform `Equatable`）。
- **更值钱的一条是判据粒度**：仓库里本来就有同族守卫
  （`testNoUnexecutedTransitionClaimsAcrossViews`），但它报的是"**整个文件**没有驱动"
  —— 而 `SettingsView.swift` 有 9 条动画键 ⇒ 这些死声明在它底下永远隐身。
  本轮把这一族降到"**调用点 + 门控状态名**"：新判据 `testEveryReceiptLineCallSiteIsDriven`
  （名单两边都会红）+ 6 格真值表（含"`if let 局部 = 状态` 里认状态不认局部名"、
  "非 `let` 的布尔门控也要认"、"键换成别的状态要判没电"、"前缀命中不算命中"）。
  约定同时写进 `ReceiptLine` 定义处的注释，并把它的**已知边界**记成 BACKLOG 63（只认一种写法）。
- 帧基线 **112 张逐字节不变**（`CHANGED=0`）—— 这一轮改的是中间态，所以这条数是"没改到稳态"的证据；
  反过来它一变就说明该停下来查。淡入本身 `cacheDisplay` 量不到（活在 presentation 层），
  胶片探针又进不了设置窗口 ⇒ 本轮如实标成"**源码已接 + 结构已判，产物未量**"，交人工批次 44.1 / 44.2。
- 又新查出两条没修的：BACKLOG **62**（"导出反馈数据"同一件事既弹模态又发行内回执，
  而失败那条又是 `localizedDescription` 直出 —— U-67 同一族、另一个出口）、
  **63**（新判据只认 `.animation(value:)`，用 `withAnimation` 供电会被误报成没电）。
- 变异 **M194–M198** 五支全 CAUGHT。第一遍 M198 `红得不对`：needle 抄的是 `XCTAssertEqual` 自动消息里
  **`Set` 的打印**，而它的顺序每次进程可能不同 ⇒ 修法是把判据改成两边 `sorted()` 再比（消息从此稳定）。
- 验证：726 tests / 29 skipped / 0 failures、`swift build` 0 告警、闸门
  `有名字的红=0 NOT_RUN=0`、脚本 83 全绿。自评 **92 / 100**（`流畅度` 这一维本轮没资格涨分）。

### Fixed（R41 · 上一轮那句回执，恰好在三种最常见的失败里说了假话）

- **发现的是自己上一轮交付的缺陷**：R40 的回执固定写着"剪贴板里仍是原来的内容，没有被替换"，
  而 `ClipboardWriter.swift` 的真实顺序是 `:67` 校验 → `:71` `clearContents()` → `:78/:97/:99` 写入失败
  ⇒ 四种已知失败里有**三种**发生在清空之后，用户原来的剪贴板内容那时**已经没了**。
  照那句话去 ⌘V，粘出来的是空或上一条无关内容。另一半：`error.localizedDescription` 直出，
  非本模块的错误会把 "The operation couldn't be completed. (NSOSStatusErrorDomain error -100.)" 搬进横幅。
- 新增 `ClipboardWriteFailure { message, clearedPasteboard }` + `classify(_:)`：把"失败"从一句字符串
  升成一个事实。`HistoryStore` 存这个值（`clipboardWriteErrorMessage` 退化成计算属性 ⇒ 消费者零改动），
  `CopyThenPaste.decide` 按 `clearedPasteboard` 说两种话。未分类错误**保守**当作已清空
  （猜错方向的代价不对称：说"还在"会让人去粘空内容，说"没了"只是多复制一次）。
  系统原文改道 `LifecycleDebugLogger` —— 界面要下一步，日志要原文（BACKLOG 58 里那半问就此答掉）。
- 判据：真值表 1（5 格，含未分类那格的方向 + "不许含 The operation"）+ 管线级两臂（回执随错误类型而不同）
  + **两条既有契约测试被改掉**（它们钉的正是 `message == error.localizedDescription` 这个 BACKLOG 58 形状），
  改后加一条 `XCTAssertNotEqual`，让"退回裸描述"本身会红。
- 帧 **110 → 112**：新帧 `content-min-with-copy-failure-notice`（**600×440 = 产品最小窗口**，
  取自 `App.swift:12` 与 `WindowConfigurator:94`，不是夹具自选宽度）。上一轮只在 750 上放过这句话，
  而"文案变长"在 750 放得下不构成证据。读数：两行完整、`NOTICE_ACTION offset=+0.0`、
  `ratio=12.98 / ink=24.5%`（亮）、暗档 `11.54 / 27.8%`。
  顺带量到 `blackBandPt` 66 → 0 的机制（横幅把选中行整行顶出可视区）⇒ 记 **BACKLOG 61**，本轮不动产品。
- 变异 **M189–M193** 五支全 CAUGHT；但第一遍 `红得不对=2` —— needle 我按 `decide` 的措辞猜，
  实际红在 `classify` 的分支里（U-65 那一族**第三次**犯）。分开计数、读实际消息、重写预期后才全绿。
- **BACKLOG 59 已逐行复核**（只核不修）：两处 catch 只写 debug 日志，且 `HistoryStore` 那 6 条回执通道里
  **没有一条是存盘失败** ⇒ 这次没有现成通道可复用，先定形状再动。
- 本机换装与 CI 结论见 `AGENT_UI_AUDIT.md` 第 43 轮。

### Fixed（R40 · 复制失败之后，那一下 ⌘V 粘的是别的东西）

- **修的是一个"做了错的事"的缺陷，不是提示缺失**：浮层回车 / 菜单栏点一条走的是
  "复制 + 自动粘贴"，而复制这一步的结果**没人看** —— 写剪贴板失败时它照样切前台、照样注入 ⌘V，
  于是目标应用粘出来的是用户剪贴板里**上一条无关内容**，而界面一句话都没有
  （`clipboardWriteErrorMessage` 全仓唯一的显示消费者是详情区那颗按钮）。
- 新增 `CopyThenPaste.decide`：失败 ⇒ 不 activate、不注入，并走**已有**那条横幅通道说一句人话
  （"复制到剪贴板失败：…已取消自动粘贴 —— 剪贴板里仍是原来的内容，没有被替换。"）。
  做成纯函数的理由：`nil 就是这次成了` 依赖写成功时把错误清成 nil 这个约定，不钉住会静默退化。
- 4 条判据全从产品入口进（管线级 2 / 真值表 1 / 接线守卫 1）。
  **M186 抓出成功那一臂第一版太弱**：闸门方向反了 ⇒ 既没按键也没提示，旧断言照样成立 ⇒
  改成断言"走到了下一步"。变异 M185–M188 四支全 CAUGHT、红得对 4/4。
- 帧 **108 → 110**：新帧文案从产品生产者取（不手写），以后被拼长会自己红。
  它第一次撞上材质盲区闸（`blackBandPt=66`）—— 对过两张姐姐帧读数确认是同一处侧栏离屏伪影后登记进名单。
- **记账三条**：BACKLOG 58（回执里嵌系统英文原文，读不懂）、59（保存失败静默，未复核）、
  60（普查其余 12 条全部"未核"，不许直接当缺陷修）。清单在
  `.scratch/motion-audit-2/silent-failures-survey.md`。
- **本机已换装**：`make bundle`（0 告警）→ `/Applications/时间剪史.app`（md5 与新包一致）→
  冷启动冒烟 `SMOKE_OK=1`。采集链路**没有**验成：agent shell 的 `pbcopy` 不通向 GUI 会话的剪贴板
  （`pbpaste` 回读为空），所以那两次「没采集」是假阴性 ⇒ 这条留给用户（批次 42.1 / 42.3），
  账本里不写「已验」。
- **验证**：723 tests / 29 skipped / 0 failures、`swift build --build-tests` 0 告警、
  帧基线 `CHANGED=0 / ADDED=2 / 110`（同 commit update）、脚本 83 全绿。

### Fixed + Changed（R39 · 禁用态与那句"点了没反应"的话，第一次有帧）

- **修了一个只在 macOS 12 上发生、且一句话都不说的失败**：开机启动走 AppleScript 那条路时，
  自动化权限被拒常常**不抛错**，只是没生效 —— 修前代码连 `error` 都不读，用户看到的是
  "开关自己弹回去"。现在动作之后**读回一次**，不一致就抛 `loginItemNotApplied`，
  界面出现"开机启动开启失败，请稍后重试。"（D-098）。比对逻辑拆成
  `SystemLoginItemManager.verifyApplied(enabled:readBack:)` 纯函数，四格真值表在这台
  macOS 14+ 的开发机上**真的跑得起来**（不拆的话这一支永远走不到，只能等一台 12 的机器）。
- **禁用态第一次进帧基线**：新增两张夹具（`settings-general-login-unsupported` /
  `-failed`）× 两档外观 ⇒ 帧 **104 → 108**，基线同一 commit update。
  目标里"全部状态"那七档，这是最后一档没有像素的。
- **新判据 `testDisabledToggleAndFailureReceiptAreVisible`**：三臂，两臂成对。
  读数：禁用后标签对比度 亮 **13.76 → 1.82**（淡到 0.13 倍）/ 暗 **11.43 → 2.29**（0.20 倍）；
  回执那一行在两档下都是参照的 **1.01 / 0.95 倍**（说明档，不是标题档）。
- **两条新的说明段探针**（表 16 → 18 条），框从这两张帧的 `rowTierProfile` 量出来
  （亮 136.5..145.5 / 暗 136.0..145.5），不是照抄别处的 y。
- **两条自己抓到的方法错**：① 负对照第一版写"没回执的帧同一块读 0 墨" ⇒ 本机 382 / 471 推翻它
  （整行消失时布局会收上来，那块压着下一颗开关的标签：标题档 971 / 1064 像素）⇒ 改成**差值**对照；
  ② 变异电池有两支的"预期红"是推理出来的（M177 实际红在天花板不是墨地板；M180 实际红在
  `did not throw`）⇒ 电池现在把"未被抓到"与"红得不对"分成两个计数，本轮第一版就靠它揪出这两支。
- **记账两条不修的**：`SettingsView` 三处 `.disabled` 在产品里恒不可达（R28 已对账）⇒ 不补帧；
  `ReceiptLine` 声明的 `.contentFade` 没有任何 `withAnimation` 供电（这一页 0 个）⇒ BACKLOG 53。
- **R39b（CI 追认的红）**：第一次推上去 CI 第 5 步就红 —— 12 条全部来自本轮新写的那条禁用态判据，
  原因是 runner 上设置页内容列是一块平涂（BACKLOG 43）⇒ 那条判据在那里**永远读到 0 墨 / 对比度 1.00**。
  没有放宽任何一条线，而是补上「这一台画不画得出这一页」这一问：三张全有墨才判、三张全无记 NOT-RUN、
  **只画出一部分则红**（中间那一格两台机器都走不到 ⇒ 拆成纯函数 + 四格真值表 + 变异 M183 / M184）。
  本机读数一字未变（718 → **719** 例，多的是那条真值表）。同一族第三次犯 ⇒ U-65 / BACKLOG 56。
- **本机已换装**：`make bundle`（0 告警）→ 装到 `/Applications/时间剪史.app` → 冷启动冒烟 `SMOKE_OK=1`。A/B 顺手查出 **U-64 / BACKLOG 55**：另一个同 bundle 实例在跑时，守卫中止的那次启动在盘上一行日志都不留（连守卫自己那句"本次启动取消"都不见），而仓库的启动冒烟把这种探针环境问题报成"启动失败"。
- **验证**：718 tests / 29 skipped / 0 failures、`swift build` 0 告警、
  帧基线 `CHANGED=0 / ADDED=4 / 108`、脚本 83 全绿、变异 M177–M182 六支全 CAUGHT（红得对 6/6）。

### Changed（R38 · 闸门第一次真跑就点到了我自己的名：两处"拿一台机器的读数量另一台机器"）

- **产品代码零改动**；测试仍 714 条、0 失败、0 告警、帧基线 `CHANGED=0 / 104`。
  这一轮改的是**判据的形状**，起因是 R36 那道闸门第一次跑到，
  报出 `CAPTURE_GATE_RESULT=fail / 有名字的红=1`（run 38473962277 之后的一次）——
  红的是 R37 我自己写的那把锁。
- **锁从"量级地板"换成"恒等式"**：以前是"`content-min` 底行至少读到 20%"（本机 43.4%），
  runner 上同一帧只有 **9.3%** ⇒ 红。现在是"判据用的读数 == 从落盘文件重算的读数"，
  104 张帧全对；两边同机计算 ⇒ 与帧长什么样无关，而来源换回 raw rep 照样露馅（M175）。
- **资格判据的地板从写死改成从表推导**：`judged ≥ 20` 在 runner 上是 **20/40 恰好压线**，
  再多一族画不出来就悄悄归零。现在要求"非放行的每一条都必须真的判到"，
  外加"可判对象 ≥ 16"（M176：把每条都放行 ⇒ 红在"对象快被清空了"）。
- **CI 已读**：闸门第一次真跑并**绿**：run 38487277143（job 115612…）整作业 `completed success`，第 7 步 `Capture gate` 打出 `CAPTURE_GATE_CASES passed=23 skipped=9 failed=0 有名字的红=0 NOT_RUN=40` ⇒ `CAPTURE_GATE_RESULT=ok 红=0`；第 5 步（主测试）也过了 —— 资格判据的机器前提在 runner 上成立（放行 20 条、判成 20 条，派生地板 `judged == 可判条数` 成立）。（U-61 的规矩第一次被执行：推完 → 读逐步结论 → 才写这句话）。
- 顺带把两台机器的 `BOTTOM_EDGE_INK` 清单各留一份（本机 18 张 / runner 30 张，
  差值全在 `content-*` 那一族）—— 记下来是因为"哪些帧底行压着东西"其实是**排版量**，
  不该被下一个人在另一台机器上当判据。

### Changed（R37 · 那把量了十四轮色差的尺改对了；改对之后它又红了两处）

- **产品代码零改动**；帧基线 102 → **104**（新增一张"故意裁自己"的对照帧，亮暗各一）。
- **`bottomInkFraction` 的参照点**从"整帧左上角那一个像素"改成**底行自身的每通道中位数**（U-60 / BACKLOG 50）。
  三张合成图钉住它：角点不同 ⇒ 0%（旧实现读 100%）、半行压字 ⇒ 50%、
  **整行同一深色块 ⇒ 0%（写下来的边界，不是事故）**。
- **正对照从"找"改成"造"**：`row-clipped-control` = 同一颗 `HistoryRowButton` + 58pt 外框 + `.clipped()`，
  实测底行 **10.8%（亮）/ 12.5%（暗）**，线取 5%。
  两条线必须成对（mustFit 上限 2% **<** 正对照下限 5%），否则判据与它的正对照互相取消 —— 这条有断言也有变异。
- **第二处同族问题**：这把尺读的是 `cacheDisplay` 的 raw rep，不是落盘那张 PNG ——
  同一帧差 13 倍、方向还相反（`content-min` 3.4% vs 43.4%、`content-empty` 37.4% vs 0.1%），
  因为 raw rep 里"没画"的像素是透明的、会抢走底行中位数。现在**判据读产物**；
  `blackBandHeight` 继续读 raw rep（它要的正是 alpha）。
- **U-61（流程 + 一条恒红的判据）**：R35 起 CI 就是红的（run 7d0a89b / 68027fc 都 failure），
  红在 `testProbesDoNotSitOnVibrantColumns` —— runner 上 settings 族整体没画出来，
  那棵树便答"内容列压在 vibrant 里"。这条判据现在带机器前提（整族空白 ⇒ `PROBE_DOMAIN_NOT_RUN`）
  并有 `judged ≥ 20` 地板；同时立规矩："CI 绿"只允许写**读过的那一次**（BACKLOG 51）。
- **新知识**：底行真的压着东西的帧有 18 张（`content-min` 43.4% 是选中行的药丸贴到帧底；
  `settings-recommendations` 42.4%/19.9% 与 `settings-privacy` 27.2%/6.7% 确实把最后一行切成半截 ——
  滚动区的正常行为，不进 `contentMustFit`，但**从此可数**）。mustFit 那十条一张都不在其中。
- 测试 713 → **714**，0 失败、0 告警、脚本 83 全绿；变异 **M169–M174** 六支全 CAUGHT。

### Changed（R36 · CI 的红终于有名字了 —— 顺手把一把用了十四轮的尺问成了色差尺）

- **产品代码零改动**（帧基线 `CHANGED=0 / 102`、`swift build` 0 告警）。这轮做的是**验收装置本身**：
  帧捕获那一步以前是 report-only，runner 上 4 条断言行红被吞了九轮（BACKLOG 49 / U-59）。
- **新增硬门 `scripts/ci_capture_gate.py`**：红有两个来源（`error: -[类 方法] :` 与 `Test Case … failed`，
  后者是崩溃/超时那种**只有结论行**的红），三条退出码规矩 —— 未登记的红 >0 红、
  一条用例结论都没有红（"没跑"不是通过）、判出绿的数量 < `--min-passed` 红
  （把像素判据整批改成 `throw XCTSkip` 也是一条红都没有）。
  正对照是**逐字日志**：`scripts/tests/fixtures/r36_runner_capture.log`（run 38473962277 那 257 行）。
- **机器能力前提拆成三条**（`CaptureCapability`，纯函数 + 5 臂真值表）：
  settings 族是否**整族**空白（族内每张 >85% 未绘制；本机 20.8–78.8% vs runner 90.6–95.9%）、
  这一台是否见过任何黑带（本机 9 处 vs runner 0 处）、底行墨这把尺是否活着（两台都 100%）。
  上一版是"某一族画不画得出来"一把尺管三件事，那种写法既放过过不该放的也红过不该红的。
- **U-60（看图看出来的）**：`bottomInkFraction` 的参照点是**左上角那一个像素**，
  所以它读的是"底行与角点差多少"而不是"底行有没有墨"。51 张帧双参照扫描：15 张报 100.0%
  而按底行自身只有 0.0%（sidebar 四帧 × 亮暗 + detail 亮色七帧），`settings-privacy-light`
  反过来报 0.1% 而真实 6.7%（漏报）。⇒ R22 那条正对照从写下那天起就是**假对照**，
  `contentMustFit` 十条判据十四轮没有有效正对照。本轮只改话术 + 记 BACKLOG 50，
  尺留给 R37，并留 `InkFloor.bottomEdgeInkAliveFraction` 当绊线。
- **旧账纠正**：BACKLOG 43 那句"List 族在 runner 上画不出来"是错的 —— 那一族在 runner 未绘制 0.0%，
  真正整族空白的是 settings。49 已就地改写，并新增 50。
- 测试 712 → **713**，脚本测试 72 → **83** 条，全绿。变异 **M157–M168** 十二支：11 CAUGHT，
  M168 本地无判别力（本机确实见过黑带），由下一次 CI 的日志判。

### Changed（R35 · 说明段全覆盖：其余五个分区 + 详情/行内 meta，外加一条"覆盖要有机器账"）

- **产品代码零改动**（帧基线 `CHANGED=0`）。这轮把 BACKLOG 34② 剩下的半条做完：
  `captionInkProbes` 从 8 条长到 **17 条**，新增的 9 处全部**从帧的说明档带放框**
  （`testSettingsCaptionRowTierProfileDiagnostic` 这轮推广到点名一批夹具、只打说明档的带）：
  快捷键页说明段、隐私页三段（上下文权限说明 / 推荐过滤说明 / 默认排除清单第一行）、
  数据页说明、推荐页说明、统计页热图上头那句、详情头部 meta（时间·大小·来源）、
  列表行第二行 meta（复制时间）。
- **读数**：17 条 × 亮暗两档全部判成（`CAPTION_JUDGED 17/17`），比值 **0.93–1.18**，
  都在地板（0.8）与天花板（1.5）之间。两处主窗口的 meta 比参照略深（1.13 / 1.18 亮）——
  11pt 比 10pt 参照的笔画粗，抗锯齿后核心像素更接近满色，这是**预期**而不是缺陷；
  天花板留了 27% 的余量，M152 证明套到标题档（3 倍以上）一定被抓。
- **新判据：覆盖要有机器账**。设置窗口**每个分区至少被点名一次**，分区清单从
  `SettingsCategory.allCases` 推导而不是写死 —— 以后加一个分区而没给它任何说明段判据，会当场红，
  而不是变成一张没人审过的空白页（R10 那条"探针名单从产品推导"的推广）。
- 诊断清单里刻意**不列**快速选择浮层：102 张基线里没有一张 `quickpick-*`（AppKit 自建 NSPanel，
  R19 试过搬进别的窗口会塌成空壳 —— 已记的账 BACKLOG 30 / U-39 / U-41）。
  列一个不存在的夹具只会红成"找不到对象"，那句话说的是我的清单，不是产品。
- **一条逃逸把整帧的颜色域问出来了（M155 第一次 ESCAPED）**：我给 `sidebar-history` 的
  "列表行第二行 meta"放了条探针，把产品那行改成 `.tertiary` 之后**判据全绿**。顺着查下去量到的
  不是框放错，而是**那一列活在另一个颜色域里**：`vibrantAppearanceCovering` 说侧栏那一列的生效外观是
  `NSAppearanceNameVibrantLight`（暗档 `…VibrantDark`）—— R30 量过的同一个机制，当时只记在
  "暗档设置页侧栏"那一格。实测同一句"这一带最深是多少"：侧栏 `.primary` 行标题 (113,113,113)，
  它下面那行 `.secondary` 的 meta 也是 (113,113,113)，而设置页内容列同样声明 `.primary` 的标签
  是 (38,38,38)。**在合成前的像素上，"档"这个量不是产品那个量。**
- **新判据：探针的颜色域资格**（`testProbesDoNotSitOnVibrantColumns`）：逐条问"这个框压着的子树
  在哪个外观里解析颜色"，40 条读数一次问完。两条规矩 ——
  ① 说明段表里**一条都不许**压在 vibrant 子树上（无例外）；② 控件表里允许但必须点名登记
  （现在一条：`sidebar-multi-select/批量操作按钮`，R21 的读数从此记为"不属于产品的证据"）。
  名单由产物现推：多一条红、少一条也红。
  于是那条侧栏 meta 探针**被撤掉**，行内 meta 的档改记为量不到（BACKLOG 48）——
  表里留一条假绿比少一条更糟。
- **顺带查清 CI 的一个口径**（BACKLOG 49）：帧捕获那一步是 **report-only**
  （`continue-on-error: true` + `|| true`，注释里写了理由），所以 runner 上
  `testCaptureKeyViews` 的 4 条红（材质盲区名单在 runner 上"黑带消失了"、正对照帧底行读到 0% 墨、
  两张 `settings-privacy-excluded` 被"捕获失效"闸门锁住）**不会让作业变红**。
  也就是说账本里"CI 上真的跑"这句话，对这一步只成立到"跑了"，不成立到"红了会拦"。
- 变异 **M152–M156** 五支全 CAUGHT：天花板（3.77 倍）、地板（1.82 = `.tertiary`）、
  覆盖规则（"快捷键"分区一处都没有）、颜色域资格（把撤掉的探针加回来必须红）、
  名单（把已登记的 vibrant 控件探针清空必须红）。`RESTORE_CLEAN=yes`。

### Changed（R34 · 菜单栏那三张帧量的不是产品；R33 的判别臂问错了问题）

- **产品代码零改动**，帧基线 `CHANGED=0`。本轮改的是"哪些结论被允许建立在这批帧上"。
- **U-56 收回**：R33 由看帧得到"产品的推荐理由被硬切成半字（墨到 `x=319.5`）"。
  查清依据在产品自己的注释与源码里：`MenuBarExtra` 全仓没有 `.menuBarExtraStyle(.window)`
  ⇒ 默认 `.menu` ⇒ 这棵 SwiftUI 树被编译成**真的 `NSMenu`**，而 `menubar-*` 帧拍的是
  离屏 `NSHostingView` 复刻。复刻里那一行在 320 / 400 / 520 / 720 四档宽度下**都顶到帧边界**
  （最右墨 320.0 / 398.0 / 518.0 / 718.5）⇒ "顶边"是复刻的性质（它没有右内边距），
  不是产品的截断行为。**看帧看到的没错，错的是把复刻当成产品。**
- **新规矩（机器可读）**：`menuSurfaceReplicaFixtures` + `testMenuBarFramesAreReplicasOfTheMenuSurface`
  —— 三条一起：现读 `App.swift` 的前提、名单 ≡ 由 `menubar-` 前缀推导的夹具集、证据是顶边读数。
  内容：**这批帧可以判颜色档，不可以判宽度 / 截断 / 对齐 / 命中区**；
  产品哪天换成 `.window` 风格，第二条断言会红着提醒"这些帧现在就是产品本身了，把名单收掉并重新审"。
- **修掉 R33 那条判别臂的问句（U-57）**：它问"整帧有没有墨"，而该问"**探针所在那一竖条**有没有文字墨"。
  CI run 38472213484 因此红了，而且**红得对**：runner 上设置页内容列是平涂（BACKLOG 43），
  可帧的底色与侧栏有墨 ⇒ 整帧那一问永远答"画得出来" ⇒ 三条设置页探针被红成"框贴到空白上"。
  现在收成 `columnIsDrawable(textInkPixels:)` 并配一张**正对照真值表**
  （`testNotRunDiscriminatorTruthTable`：空白帧必须被判"画不出来"，本机实测 blank=0 / 真实页=31890）——
  这条分支在本机永远走不到，所以它必须有一张正对照，否则下一次还是 CI 替我发现。
- **新尺**：`trailingInkColumn`（`leadingInkColumn` 的右镜像）。左边界判对齐，右边界才看得见"截断留没留痕迹"。
- 变异 **M148–M151** 四支全 CAUGHT（前提 / 名单 / 证据 / 判别臂本身），`RESTORE_CLEAN=yes`；
  M150 顺带量到加 12pt 右内边距后最右墨从 320.0 退到 308.0 ⇒ 这把新尺两个方向都动。
- 全量 **710 tests / 30 skipped / 0 failures**、0 warning、脚本 72 OK。

### Changed（R33 · 说明段探针的"通过"原来是假的；通用页每段说明回到自己那颗开关下面）

- **产品改动（U-55）**：「通用」页四颗开关各自的 `.secondary` 说明段与它解释的那一颗**编成一组**
  （新常量 `SettingsViewLayout.captionGap = 3`，组间保持 8），并把讲截图文字识别的那一句
  从富文本说明之后挪回它自己的开关下面。修之前屏上的顺序是
  「识别截图文字 → 保留富文本 → RTF 的代价 → 关闭后不再对新入库的图片做文字识别」，
  也就是**讲 A 的说明挂在 B 下面**（亮暗两档帧里都看得很清楚）。
  顺带把 `loginItemSettings.message` 那条回执挪回「开机启动」下面（夹具下它是 nil ⇒ 帧里量不到，只进账本）。
- **实测（改前 → 改后）**：说明段与上面那颗开关的空缝 **12.0 → 7.0**（暗 11.5 → 6.5），
  与下面那颗开关的空缝保持 **12.0 / 11.5** ⇒ 归属不再靠猜。
  判据 `testSettingsCaptionSitsCloserToItsOwnToggle`：上面那一带必须有标题档的墨 + 上缝 ≤9pt + 上缝 < 下缝，
  两档外观各判 3 段。
- **一条一直存在的判据盲区被修掉（BACKLOG 34②③ / D-092）**：`captionInkProbes` 从 R27 起只有**地板**
  （不许比 `.secondary` 淡），所以"框套到标题上"这种错法**反而更轻松通过**。
  本轮加了**天花板** `captionTierCeiling = 1.5`：我上一轮放进去的两条设置页探针当场量到
  **3.67（亮）/ 1.89（暗）倍参照** —— 它们套的是「通用」标题与开关标签。
  框重放后 8 条 × 两档全部落在 **0.95–1.03**（热图三条、菜单栏两条本来就贴着参照，等于回审通过）。
- **新尺 + 真值表**：`rowTierProfile`（把一块矩形里的笔画按"离背景多远"分说明档 / 标题档，
  依据是抗锯齿拉不出比字本身更深的像素）与 `textBands`；
  真值表 `testRowTierProfileSeparatesCaptionFromTitle` 钉的是**顺序与间隙**
  （说明带最深 120/121、标题带 206/185、阈值 150 落在中间）。
  诊断 `testSettingsCaptionRowTierProfileDiagnostic` 负责把带表打出来（放框用，永远记为未运行）。
- **修掉上一轮自己埋的一条**：NOT-RUN 判别臂被装进了 `testActionableInkStaysAboveTheLegibilityFloor`
  （那张表一条设置页探针都没有 ⇒ 永远不可能触发的装饰，且日志前缀写着 `CAPTION_NOT_RUN`），
  而真正会永久红的说明段测试没有 ⇒ 与 R29d「守卫在 CI 第一轮红」同族第二次。发现方式是编译报错，不是审查。
  现在说明段测试有判别臂 + `judged ≥ 3` 兜底（**判别臂不许把判据变成恒绿**）。
- **新发现、未修（U-56 / BACKLOG 47）**：菜单栏面板第一行的推荐理由在帧上被**硬切成半字**
  （墨画到 `x=319.5` = 帧的最后一列），而产品侧 `MenuBarExtra` 没有任何宽度约束 ⇒
  要么真机面板比 320 宽（被切的是夹具），要么产品真的会切。要先看真机一眼（人工批次 39.1）。
- 帧基线 2 张（`settings-general` 亮/暗）随本提交 `update`；全量 707 tests / 29 skipped / 0 failures、
  0 warning、脚本 72 OK、已换装本机（PID 91740，SHA 对上）。
- 变异 **M141–M147** 七支全 CAUGHT（两支打测量、三支打产品、一支打阈值、一支打判别臂本身），
  `RESTORE_CLEAN=yes`。

### Changed（R32 · 详情区只留一条左轴，骨架承诺的那一列就是内容落地的那一列）

- **产品改动（本轮唯一一次动画面几何）**：详情区的可读列不再随窗口居中，改为贴 `containerGutter`
  起排、宽出来的留在右边；三处调用点（头部 meta、渲染正文、原文正文）统一走新增的
  `View.detailReadableColumn()`。
- **实测**：五块左轴（meta / 原文 / 渲染 / 退回原文 / 加载骨架）的 spread 从 **35.0pt → 0.5pt**，
  亮暗两档各一遍。加载结束的一瞬间整块内容不再向右跳 35pt。
- **新判据**：`testDetailAreaHasASingleLeftAxis`（每块必须贴 gutter ±2，且彼此差 ≤2pt）。
- **两条源码守卫改强**：`Round3DetailTypographyTests` / `Round4MarkdownTests` 原来只查
  DetailView 里有没有 `maxWidth: DetailTypography.columnWidth()` 这个字符串；上限搬进 helper 后
  改成判两半 —— 调用点计数 ≥3 **且** helper 里仍有上限。
- **代价（写进 D-091）**：宽窗口里正文右侧留白变大。退路是抬 ch 上限（68→78），不是改回居中。
- 帧基线 16 张 detail/content 帧随本提交 `update`。变异 M137–M140 四支（含一支重犯"带切掉首行"）。


### Changed（R29d · 收口后的一轮：产品零改动，两条账）

- **产品代码零改动**。本轮改的是两个 `.scratch` 取证工具与账本。
- **量到一条新的帧盲区（U-52 / BACKLOG 45）**：暗档 `settings-*` 帧里，侧栏**未选中行**的标签与图标
  落在背景的错误一侧 —— 黑字黑底。实测三张帧 × 两档：亮档 733 / 771 个暗墨（正常），
  暗档同一位点是 587 / 668 个**暗**墨、0 个亮墨；而**选中的那一行两档都正常**（暗档 836 个亮墨）。
  ⇒ 判别量是选中与否，不是页 / 帧宽 / 符号名。
- **十五臂复刻体一支都没重现它**（`sidebar_appearance_r29d.swift`）：绘制外观域、orderFront 踢、
  嵌套 `NSHostingView`+`NSSplitView`、运行时翻外观、给嵌套视图钉外观、显式 `AnyShapeStyle(.primary)`、
  `Button{Label}+.plain`、以及这两半合起来那一格（嵌套 hosting view 装一列 Button）—— 全画对。**候选解药被否光的时候不改产品**（D-089）。
- **肉眼复核报错过一次并已撤回**：我对着裁出来的暗档帧说"五个标签浅灰可读"，
  像素是"该列最亮只比底亮 4"。目标要求每轮看画面 ⇒ 从此"看"必须配一个可数的读数（BACKLOG 46）。
- **修掉取证工具自己的一个真 bug**：`sidebar_icons_r28.swift` 的 `modalColor` 把 pt 当 px 用，
  于是所有 `bg` 读数取自目标区域左上角 1/4 处 —— 它曾让"第 3 行"读到第 1 行的胶囊。
  仓库判据不受影响（逐条核过 `rect * scale`）。

### Added（R29 · 判墨的尺第一次有方向）

- **`inkTailSplit` + `inkIsOnTheExpectedSide`**：取与 `inkContrast` 同一切法的尾墨（偏离背景最远的那 2%），
  只回答"这批像素落在背景的哪一侧"。两条"太淡"判据（可点笔画、说明文字梯子）的失败消息各挂一行诊断：
  **反相 ⇒ 一行产品代码都不许改，去查捕获路径；方向正常 ⇒ 这个低值是真的淡**。
  正对照用真的坏帧：`INK_SIDE 图标列 亮35/暗0 标题列 亮0/暗118`。
  真值表七条 + 变异 **M130**（把方向判定改成恒真 ⇒ 必须红）。

### Fixed（R28c · 参照臂换方向）

- **两臂对照的参照从"更宽"换成"更窄"**：宽臂在 CI runner 上连红两档
  （1100pt 与 900pt 都整帧读出 0 墨，run 38449711539 / 38451162726），
  而 ≤750pt 的 100 张帧从来没有过这个问题。
  新的一对是 `settings-min`(640pt) vs `settings-shortcuts`(720pt)：
  列宽随窗口走 ⇒ 只要有任何一行被截断，窄臂一定比宽臂少画字。
  实测修后 ratio 0.999 / 1.001，装回 `.lineLimit(1)` 掉到 0.925。
  `settings-shortcuts-wide` 两张帧从基线撤下（104 → 102）。
  **边界写清楚**：这条抓不住"两臂被截得一模一样"，那需要一个不受宽度约束的参照，
  而那正好落在 runner 拍不出来的那一档。
- 新增两条**资格断言**：两臂都必须 ≤750pt（runner 拍得出来的那一档），
  且窄臂必须比产品臂窄 ≥60pt —— 否则两臂自比，比值恒等于 1 而全仓无一条会红。

### Fixed（R28b · CI 追认）

- **两臂对照的参照臂从 1100pt 降到 900pt**：`c5db5ec` 在 macos-15 runner 上红在
  本轮新立的那条判据自己 —— 参照臂整帧读出 0 墨（本机 23864）。
  与 R3-D11 记的 `content-wide-1100x800`「95% 未绘制」同族，两条独立观察都落在
  1100pt（@2x 越过 2048px）这一档；根因未证明，先记现象（BACKLOG 42）。
  换宽度后本机 ratio 仍是 1.001 / 0.998，变异 M123 仍读到 0.809 / 0.792 ⇒ 牙口没变弱。
  **"参照必须有墨"那条红原样保留** —— 它正是这次能发现参照坏了的原因。

### Fixed（R28）

- **设置·快捷键页第三行的说明不再被截断**（R28 / U-50 / D-087）：`HotKeySettingsRow` 带着
  `.lineLimit(1)`，三行说明里前两行放得下、第三行放不下，而被切掉的恰好是唯一那句需要解释的话：
  「默认 ⌃⌥⇧V —— 刻意不是 ⌘⇧V（那是浏览器和编辑器里的"粘贴并匹配样式"，全局抢走会让它们失灵）」。
  改成换行 + `.fixedSize`，与**同一个窗口里**通用页那段三行说明同一种语言。
  代价：三行不再等高（第三行约 +26pt）—— 系统设置里等高从来不是规矩，读得完才是。
- **帧基线里的「导出历史…」「导入历史…」不再是禁用态**（R28）：捕获夹具没传
  `exportHistoryAction` / `importHistoryAction`，而视图里它们是 `.disabled(x == nil)` 的开关；
  产品调用点永远注入 ⇒ 发出去的包里没有"这两颗是灰的"这个状态。
  真正的危害是帧把禁用态钉成了标准：真接坏了也看不出来。

### Added（R28）

- **两臂对照的"文字必须画全"判据**：新夹具 `settings-shortcuts-wide`（1100×540）宽到不可能截断，
  拿它当"这一页一共画了多少字"的参照；`textInkMass` 只数偏离背景 >60 的像素，
  把录制框与药丸的**平涂底色**挡在外面（实测每块平涂约 14k 像素、整页文字约 17k，
  用 R24 那档 24 会把信号静默稀释掉一半）。
  判据 `testSettingsHelperTextIsNotClipped` + 七档真值表 `testTextInkGateTruthTable`。
  修后比值 1.003（亮）/ 0.998（暗）；装回 `.lineLimit(1)` 掉到 **0.809 / 0.792**。
- **夹具接缝对账守卫** `testCaptureFixtureInjectsEveryActionSeamTheProductInjects`：
  名单从产品调用点 `SettingsView(` 那段推导，逐个要求在夹具里出现 ⇒ 以后新加接缝忘了跟会红。
- **"反相墨"与"没画"第一次被分开数**：`OffscreenSymbolInkProbeTests.signedInk` 按亮/暗两侧分别计数。
  实测亮色帧里 `command` / `hand.raised` / `folder` 三行是 `0.0000（亮960/暗0）` ——
  像素全是 (255,255,255) 对背景 (248,248,248)，也就是**画成了白的**，不是没画。
  新增两条断言：整列一个像素都没动过 ⇒ 红（符号名写错那一族）；亮色帧里偏暗一侧更多 ⇒ 红
  （说明已经不是记下的那个伪影，得重新判）。**产品一行没改** —— 把 `.primary` 换成固定色是审计第二轮明文禁止的方向。
- **说明文字的地板从绝对值改成相对参照**（修 R27 在 CI 上的红）：`InkFloor.captionTierTolerance = 0.8`
  配 `secondaryReferenceContrast(...)` —— 同一台机器、同一外观现拍一份 10pt 的 `.secondary` 当参照。
  绝对值只留 `secondaryReferenceFloor = 2.2` 一条松兜底，用途是"参照自己坏了"时让判据红。

### Fixed（R27）

- **热图的月份 / 星期刻度与"少·多"图例不再是"看不见"的那一档**（R27 / U-49 / D-086）：
  三处实测 **亮 1.88 : 1、暗 2.27 : 1**（`.tertiary`），与 R21 判死的两颗控件是同一组数。
  R21 当时给它们开了免检，理由是"那不是控件，是刻度文字"—— 本轮重新判：
  没有月份与星期就读不出"哪一天"，没有"少/多"颜色深浅就没有标尺，
  **要读的标签没有理由比能点的笔画更淡**。三处提到 `.secondary`。
  实测：亮 1.88 → **3.75–3.85**，暗 2.27 → **6.06**。
  归因：102 帧里只有两张热图帧 + 两张内嵌它的设置帧变，且变的全是文字行 ⇒ 格子几何零位移。

### Added（R27）

- **说明文字的梯子进了仓库**（R27）：`InkFloor.captionInk = 3.5` + `captionInkProbes`（三处 × 两外观）
  + `testCaptionTextStaysOnTheSecondaryTier`。
  这条地板刻意**不是** WCAG 的 4.5：系统的 `secondaryLabelColor` 在纯白上实测只有 4.0，
  拿 4.5 去钉全 App 的 caption 会把"标题—说明"这条层级压平。
  所以正文用 4.5（R24，量到 12.98–13.94），说明文字用 3.5（"必须在 secondary 档或以上"）——
  **两种角色两根线，不统一成一个数**。
- **`.tertiary` 的按文件点名账本清空**：产品里任何一处再想用这一档，必须先在账本里点名并写清
  "它为什么不是要读的东西"。变异 **M121** 证明空账本真的有牙。
  变异 **M120–M122** 三支全 CAUGHT（M120 第一次因 needle 命中数不对被电池自己拒注入，
  换带上下文的 needle 后才红在正确的句子上）。

### Added（R26）

- **详情加载态第一次进帧基线**（R26 / U-48 / D-085）：51 个夹具里没有一个是它——
  它是异步的，拍它等于赌"那一瞬间预览还没回来"，而按墙钟判的夹具每天给出不同答案。
  修法是把私有计算属性 `loadingView` 提成具名视图 **`DetailLoadingView`**（带 `reduceMotion` 注入点），
  于是它可以被**确定地**画一次。新夹具 `detail-loading`（720×520 × 两外观），基线 100 → **102 帧**。
  静止帧管"长什么样"，扫光"动不动"仍由 `testSkeletonSweepActuallySweeps` 用胶片判 —— 两条各判各的。
- **`leadingInkColumn` + `skeletonAxisReadings`**：一块矩形里最左的有墨列，以及
  "按弱墨/强墨自己把行分成条带与文字"（条带对面板只有 Δ13，所以量它必须用 `minDelta: 6`，
  用 40 会得到"条带不存在" = 把尺调瞎再宣布没问题）。
- **`testLoadingBlockSharesTheDetailColumnsAxis`**：条带与那一句必须同轴（≤2pt），
  且这条轴必须落在产品自己的 `DetailTypography.containerGutter` 上（±1pt）。
- **横幅判据补上左锚定地板**（BACKLOG 38）：正文必须从文字列的左起三分之一里开始。
  R24 的 M108 证伪过"带里有墨"这条地板 —— 框挪到按钮上时墨占比 10.9% 照样过。

### Fixed（R26）

- **骨架条带不再顶到面板左边缘**：实测条带起于 x=0，而它替代的内容在 gutter=20 上
  ⇒ 预览落地的一瞬间整块内容向右跳 20pt。改成走 `DetailTypography.containerGutter`（产品已有的令牌）。
- **"正在加载预览…"不再居中**：实测它起于 x=316.5，而条带起于 20.0 —— 同一块 74pt 高的面板里两条对齐轴，
  句子读起来不像在说那三根条带。改成与条带同一条左轴。修后 20.0 / 20.5，亮暗一致。
  行带尺归因：全 102 帧只有 `detail-2-file` 两帧变，且恰好是条带与那一句的四段（84–156.5pt）。

### 判断（R26，不改的东西也交证据）

- **条带对比度保持不动**：亮色下条带对面板 Δ13（255 vs 242，比 1.09:1）。
  骨架是装饰性表面，AA 的两根线（正文 4.5 / 非文字部件 3.0）都不适用于它；
  抬到"看得见"抢的正是正文。亮带相对底色的抬升另有守卫。
- **行内 16pt 缩略图的 placeholder→图片不加淡入**（清单 23/25）：
  16pt 芯片在整窗帧里只占 0.06%，低于胶片尺的可见地板 0.5% —— 也就是说"淡"与"蹦"用户都看不见，
  而要做的那一层（详情大图）今天已由 `previewStage` 的交叉淡管着（R6）。

### Fixed（R25）

- **多行提示条里的"知道了"不再跟着第一行走**（R25 / U-47 / D-084）：
  `StateLine` 以前整行 `HStack(alignment: .firstTextBaseline)`，正文两三行时动作按钮被第一行的基线带走。
  量出来的偏移（按钮字形行的中心 vs 色带中心）：单行 **0pt**（碰巧对）、两行 **−6.5pt**、三行 **−14.5pt**。
  现在一行里给两根轴：内层继续 baseline 钉住图标与文字（R3 的语言），外层 `.center` 只让动作位居中。
  **实测：修后 10 条带（3 张帧 × 两外观）偏移全部 +0.0。**
  代价写清楚：**每条多行横幅矮了 1pt**（以前按钮下沿把行撑高 1pt），
  所以单条横幅下面整列上移 1pt、两条则 2pt —— 本轮**不是**零布局位移。
  影响面已 grep 确认：`action` 这条路径只有 `NoticeBanner` 在用，菜单栏那行与热图空态都没有按钮。

### Added（R25）

- **`inkRowSpan`：一块矩形里"有墨的行"从哪到哪**（R25）——按行取众数、每行至少 3 个墨像素才算有墨。
  用它把"动作按钮在带里的垂直位置"变成可判定的量，而不是我目测。
- **`testNoticeActionIsVerticallyCenteredInItsBand`**：每条带的 |按钮中心 − 带中心| ≤ 3pt，
  找不到按钮时**红**（不许静默跳过）。判据自己起离屏渲染 ⇒ CI 上真的跑。
- **正对照 `testActionSpanRulerReadsBothEnds`**：居中块读居中 / 偏上 8pt 的块必须读出超过容差 /
  空块必须返回 `nil`。第三条是这一族最坏的错法：**兜底值会把"东西不见了"读成"完美"**。
  变异 **M110–M113** 四支全 CAUGHT（M113 就是把兜底值塞回去，正对照红了）。

### Fixed（R24）

- **提示条正文在亮色模式下不达 WCAG AA**（R24 / U-46 / D-083）：
  `StateLine` 的正文以前四个状态共用 `.secondary`。逐带量出来（三张横幅帧 × 两外观）
  **亮色 3.82 / 3.85 / 3.90 / 3.92**（13pt 常规文字要 4.5），
  而同一帧里那枚"知道了"按钮是 **12.28** ⇒ 一条横幅内"下一步"比"发生了什么"清楚 3.2 倍。
  现在墨色按严重度分档：`.warning` / `.error` ⇒ `.primary`，`.loading` / `.empty` 留在 `.secondary`
  （菜单栏"正在整理推荐…"与热图空态**不**升档 —— 把背景状态喊得比内容响就是喧宾夺主）。
  **实测：亮色 3.82–3.92 → 12.98–13.94，暗色 5.26–5.58 → 10.48–11.54。**
  行带尺归因：`content-with-history`、九张 `settings-*` 等 **rows=0**；
  两张产品横幅帧**只有字母那一层**变了（`content-with-notice` 仅 y 64–93，
  `content-with-two-notices` 仅 y 64–77 与 103–132）⇒ **零布局位移**。
- **组件帧 `notice-banner` 不再替产品决定布局**（R24 / BACKLOG 36）：
  它自己写了 `VStack(spacing: 12)`，而产品是 `spacing: 0` + 每条自带 `Divider()`。
  量出来的差别：组件帧两条带之间 **13pt 无底色空缝**，产品帧 **1pt 发丝线**
  ⇒ 那张帧一直在展示一个产品里不存在的布局。改齐之后两张帧互为对照，
  并由同一条判据（带间缝 ≤ 2pt）钉住 —— 变异 M105（改夹具）与 M106（改产品）都红。

### Added（R24）

- **文字侧的对比度尺进了仓库**（R24 / BACKLOG 34 的第一处）：
  `UICaptureHarness.noticeBands(bytes:…)` —— 逐行取众数颜色自己找带
  （`R-B > 6` 算涂色、带内众数亮度变化 > 1 就断开），再在带内的**文字列**上量 WCAG 对比度。
  **不写死 y 区间**：写死等于把"布局今天长什么样"钉进判据（R21 那两个贴空的框）。
  正对照 `testNoticeBandFinderReadsBothEnds`：同一套自造几何只换字的颜色，
  深墨读过（14.11）、浅墨必须读不过（1.32）。
- **`testNoticeBodyTextStaysReadable`**：三张横幅帧 × 两外观，每条带判
  ① 墨占比 ≥ 2%（框里真有字）② 对比 ≥ 4.5 ③ 与上一条带的空缝 ≤ 2pt
  ④ 每张帧至少找到几条带。判据自己起离屏渲染，**不依赖 `CLIPBOARD_HISTORY_UI_SHOTS`** ⇒ CI 上真的跑。
- **`StatePresentation.messageInk(for:)` + `messageInkStyle(for:)`**：
  纯函数返回**档位枚举**而不是 `AnyShapeStyle`（后者不可比较 ⇒ 写不出真值表）。
  真值表 `testSeverityStatesCarryTheirOwnTextInk` + 接线守卫
  `testStateLineWiresTheInkTierInsteadOfPickingAColor`。
  变异 **M104–M109** 六支全 CAUGHT（M108 红在对比度地板而不是墨地板，
  于是"带里有墨"这条地板的适用边界被量出来了：BACKLOG 38）。

### Fixed（R23）

- **提示条的底色不再涂到标题栏与红绿灯后面**（R23 / U-45 / D-082）：
  `content-with-two-notices` 量出一条文字的警告横幅占 **88pt**、两行文字的错误横幅只占 50pt。
  诊断（临时 `GeometryReader` 探针打出 `safeAreaTop=52`，再沿一列扫色度）证明
  那 88pt 里 **y 0–52 只有底色、没有内容** —— 根因是 SwiftUI 4 起
  `.background(ShapeStyle)` 默认 `ignoresSafeAreaEdges: .all`，
  底色铺进安全区而文字被安全区顶下去 ⇒ 横幅看起来上半截是空的，并把工具栏染成警告色。
  改成 `.background(style, ignoresSafeAreaEdges: [])`（macOS 13+；12 的默认行为本来就对，
  所以按版本分叉，而不是写一个两边都凑合的负 padding）。
  **实测：一条文字的横幅 88pt → 38pt，装饰区 R-B 从 +26 → 0.0，横幅自己那一条仍是 +24.9。**
  行带尺归因：4 张帧变、每张**恰好** `0.0–52.0pt` 不同，以下逐像素相同 ⇒ **零布局位移**。

### Added（R23）

- **色度这根轴进了仓库**（R23）：`UICaptureHarness.redMinusBlue(bytes:…:rect:scale:)` ——
  那两块表面亮度只差 4（243 vs 240），`R-B` 差 26 对 0；
  **判据说"看不出区别"之前先问是不是轴用错了**。
- **`testNoticeTintDoesNotReachTheTitlebar`**（R23）：装饰区 `|R-B| < 4`，
  且**先**要求横幅自己那一条 `R-B > 8`（正对照）——
  没有它，"把色度尺弄瞎"或"把采样框挪到空白处"都能让这条判据绿着通过。
  变异 **M101**（去掉修复）、**M102**（弄瞎尺）、**M103**（挪框）三支全 CAUGHT，
  各自红在该红的那条断言上。

### Added（R22）

- **夹具不许裁自己的内容，从此可判**（R22 / U-44 / D-081 / BACKLOG 32 关掉）：
  `Fixture.contentMustFit`（点名给 10 张自包含帧）+ 判据"帧的**最底一行**不该有墨"
  （被裁的元素一定压在底边上）。这条守卫要抓的事发生过两次、两次都靠人眼：
  R18 的 `weights` 用 560 套 850 高的内容（标题与「恢复默认」九轮不在帧里）、
  R20 的 `search-field` 320×96 一直裁着自己的下半条。
  列表/滚动区那批**刻意不开** —— 它们天生会被裁，判它们等于把滚动视图的正常行为报成缺陷。
- **正对照**（R22）：十条对照全读 0.0% 的尺必须配一张**已知有墨**的帧
  （`sidebar-history` 底行 100%），否则"把阈值调到 100000"不会有任何测试红。
  变异 **M99** 就是去把尺弄瞎，它红了。
- **新帧 `content-with-two-notices`**（R22，基线 98 → 100）：两条提示条同时在场的状态
  以前**从来没有进过基线**，而组件帧 `notice-banner` 自己写了 `VStack(spacing: 12)` ——
  那是**夹具替产品做的一个决定**（真窗口的 `VStack(spacing: 0)` 里没有这 12pt）。
  新帧两条都走产品入口（`reportPasteFailure` + `addDroppedFiles` 传非本机 URL）。
- **横幅"移除那一臂"从此有人在清单里**（R22）：`testBothBannerArmsAreJudged`
  要求插入与撤走两臂都在胶片场景表里，且撤走那臂必须带 `prepare`
  （起点是"横幅已经在"，否则量到的是"从没出现过"而不是"消失了"）——
  R16 那一族："只有一臂在演的过渡等于没有过渡"。
- **`premise-not-visible` 现在说清是哪一种 not-run**（R22）：把"卷内最大逐帧差"和"过渡帧数"
  一起打出来。本机今天就是这样红的：`notice-banner` 演了 3 帧却"首尾相同"，
  旧报法分不清"变更发生在第一帧之前"与"演完又落回原样"。

### Fixed（R22）

- **变异电池的"绿"可以是一次跳过**（R22 / D-081）：第一版报 M97/M98/M99 三支 ESCAPED，
  看着像新守卫没牙 —— 真相是 `testCaptureKeyViews` 没设 `CLIPBOARD_HISTORY_UI_SHOTS` 就整条 skip，
  而 **skip 的退出码是 0**，预检把三条跳过读成了三条绿。
  现在电池自己开闸，并把"只有 skipped、没有 passed/failed"判成 DID-NOT-RUN；
  补完之后 **M97–M100 四支全 CAUGHT**，且每支都核对失败消息（红得对不对）。
  这一族账本里记过"退出码复用"，这次记的是它的兄弟：**跳过码复用**。

### 量出来但没修（R22）

- **一条文字的警告横幅占 88pt，两行文字的错误横幅只占 50pt**（BACKLOG 35）：
  沿一列的色度扫描（新加的 `column` 模式 —— 那两块用亮度只差 4，用 R-B 差 26/19 才分得开）。
  两个候选解释（底色涂到透明标题栏后面 / 那其实是两条同色横幅）都还没判掉，
  而两种改法互斥 ⇒ **没读懂之前不动产品**，R23 第一件事是判掉它。

### Fixed（R21b）

- **CI 打红了这条判据自己**（R21b / D-080）：R20 新立的"搜索框两态等高"在无头 runner 上
  读 **15.5 / 17.0pt**，本机读 **32.5 / 33.0pt** —— 差一倍不是噪声：这张框的填充
  `VisualFill.fieldIdle`=0.035、描边 `VisualTint.fieldIdleStroke`=0.05，在 runner 那块纯白底上
  都落不进像素阈值，于是"框"塌成"有墨的行"。**同一把尺在两台机器上量的不是同一件事**，
  把"打字时框会不会跳"建在它上面，等于让 CI 的绿取决于底色。
  等高从此判**布局**（`GeometryReader` 读两态实排高度，环境无关），
  像素带高**降级为诊断打印**，那条测试改名 `testSearchFieldFixtureShowsBothStates`
  并只留两条跨机器稳定的前提。
- **那颗 × 一直比文本列高半 pt，R20 的"两态都锁在 32pt"其实没锁住**（R21b）：
  新判据第一次跑就报 `empty=32.0 filled=32.5` —— `xmark.circle.fill` 在 12pt medium 下
  **固有高度 14.5pt**，加 4pt 命中区就是 22.5pt。钉成 `.frame(14×14)` 之后两态都是 32.0，
  容差从 1.5pt 收到 **0.2pt**；变异 **M96**（拆掉那个 frame ⇒ 漂 0.5pt）必须红 —— 它红了，
  说明判据比缺陷本身更敏感。顺带这颗悬停药丸从 22.5×22 的椭圆变成 22×22 的正圆。
- **`NSHostingView.fittingSize` 在本仓库作废**（R21b，写进规矩）：裸 hosting view 读回 0；
  按 `render()` 那样现建离屏窗口去读会让测试进程 **SIGSEGV**；而 R19 已证明
  "内容钉了高度时它是恒真的尺"。要布局尺寸就用 `GeometryReader` 写进引用盒子。
- **一条前提断言救了一次场**（R21b）：`XCTAssertGreaterThan(box.empty, 10, "布局根本没跑起来")`
  是照着"判据不许悄悄退化成恒真"加的，第一次跑就把 0.0 拦下 —— 没有它，
  那条判据会因为"0.0 与 0.0 相等"而**绿着通过**。

### Fixed（R21）

- **两处"能点的小笔画"从看不见抬到看得清**（R21 / U-43 / D-079）：搜索框清除 × 与多文件行的
  展开箭头原来都穿 `.tertiary`，实测静置对比度 **1.86 / 2.22** 与 **1.88 / 2.27**（亮 / 暗），
  而非文字 UI 部件的地板是 3.0；同一帧里 `.secondary` 的图标是 3.95 / 5.9，正文 9.42。
  ⇒ 在系统色板上 `.tertiary` 的真名字不是"次要"，是"**看不见**"。
  现在静置走 `VisualInk.control`（`.secondary`）、指到走 `controlTargeted`（`.primary`），
  实测抬到 **3.74 / 5.34** 与 **3.85 / 6.06**。R20 刚把 × 的命中区从 14pt 抬到 22pt ——
  **看不见的大目标仍然看不见**，几何与可见性是两条独立判据。
- **多文件行的层级反了**（R21）：那颗箭头是**整行唯一的"我可以展开"记号**，
  却比旁边"这是什么类型"的图标更淡，同时还踩着 `VisualGlyph.badge` 的 10pt 下限 ——
  两样都弱就叠成了"没有这个记号"。
- **一条判据的单调性方向写反，被自己的尺打红**（R21）：我给对比度尺写真值表时写了
  "墨越暗对比度越高"，在黑底那一支是反的（`contrastRatio(180,0)=10.13 > (100,0)=3.55`）。
  现在两个方向分开断言，各配一句为什么。
- **放错文件的常数被"死令牌"守卫抓出来**（R21）：`VisualContrast.controlInk / smallText /
  probeInkFraction` 第一版写进 `VisualTokens`，全量测试立刻红三条 —— 它抓得对：
  地板不是产品画出来的东西。判据参数搬到 `UICaptureHarness.InkFloor`，
  产品侧只留真的被视图读的 `VisualInk`，而没有任何消费者的 `smallText` 直接删掉。

### Added（R21）

- **可辨线从文字推广到控件**（R21）：`UICaptureHarness.inkContrast` 在**产物像素**上量
  "这块墨 vs 它自己的底"的 WCAG 比值（背景取 8 级量化的众数、字形取偏离最远的 2%），
  配 `testActionableInkStaysAboveTheLegibilityFloor` 扫四处图标控件 × 两个外观，
  外加 `testContrastRulerArithmetic` 钉住尺的算术（21:1 / 1:1 / `#767676` 对纯白 4.54:1）。
- **每条像素判据都自带"这块真的有墨"的地板**（R21）：`InkFloor.probeInkFraction` ≥ 3%。
  本轮五个**估出来的**候选框里有两个贴在空白上 —— 只判对比度时空白会读到 1.0 而红成假缺陷，
  有了墨地板才会红成它真正的意思（"框贴到空白，去看元素搬到哪儿"）。框必须从帧上量。
- **`.tertiary` 的按文件点名账本**（R21）：`testTheFaintestInkTierIsReservedForNonControls`
  要求全 `Views` 里这一档只出现在登记过的地方（现在只剩热图的三处**刻度文字**，非控件），
  新增位点必须先登记并写理由。计数按**标识符边界**，`.tertiaryLabelColor` 不会被白拿。
- **变异电池开始核对"红得对不对"**（R21）：每支变异除 CAUGHT/ESCAPED 之外，
  还要在失败输出里找得到期望文本（M92 必须红在墨地板那条上）。
  "红了"与"红得对"是两件事 —— 与 R19 那条"症状会活过病因"同族。

### Changed（R20）

- **每一颗圆形图标按钮的悬停强度重新判过**（R20 / U-42 / D-078）：`PressedStyle.hoverLevel`
  的默认值是给**整行**定的 `VisualFill.hover`=0.06，而小控件上 6% 读不出来（铺在 20pt 图标上等于没有）。
  行首星标、搜索框清除 ×、视频播放与静音四处从此显式抬到控件档 `controlHover`=0.08。
  详情区那颗玻璃药丸相反 —— 它**叠了两层**：`GlassIconControl` 自己画一层 `controlHover`，
  `pressedStyle` 又叠一层默认 0.06 ⇒ 悬停约 0.14，比"控件"那一档高 1.75 倍，
  是这一圈里唯一被画两层的表面 ⇒ 那一处改成 `hoverLevel: 0`，只留自己那层。
- **搜索框清除 × 的命中区从约 14pt 抬到约 22pt**（R20）：它的 label 之前只有字形那么大
  （`xmark.circle.fill`，无 frame 无 padding），是全 App 最小的一颗可点控件，
  而它管的还是"一键清空搜索"这种要快按的动作。`labelPadding: 4` 让底色药丸与命中区一起长。
  行首星标与视频两颗**刻意不加** padding：它们的 label 已有 20/22pt 的 frame，
  再垫会把整行文字列往右推 8pt —— 那是版式，不是反馈。

### Fixed（R20）

- **打字时搜索框自己跳一下**（R20，本轮自己引入又自己抓到）：加了 4pt 命中区之后，
  这一行的定高者从文本列（17pt）换成了 × 那颗（22pt），于是空框 31pt、有字框 32pt。
  第一次修（垂直内边距 7→5）只是把方向反过来，没修根因；真正的修法是让文本列自己声明 22pt，
  两态都锁在 22 + 10 = 32pt。配套判据 `testSearchFieldKeepsTheSameHeightInBothStates`
  把两态**真的量一遍**（`filledBands` 找填充带，断言带高差 ≤ 2px），
  实测 `SEARCH_FIELD_HEIGHTS light pt=32.5, 33.0 / dark pt=32.0, 33.0`。
- **`search-field` 夹具一直在裁自己的下半条**（R20）：320×96 的框套两态各 32pt + 间距 = 约 74pt 的内容，
  加上边框与留白后 96 不够 —— 与 R18 那条 `weights` 裁头同族，但这次是**内容高度**从来没人核。
  夹具抬到 320×112（帧基线 98 张，名字随之变成 `search-field-320x112-*`）。
- **两条守卫现出原形**（R20，变异 M88 与预检各抓一条）：
  ① `testSmallControlsAskForThePillPadding` 旧版数的是源码里出现过 `labelPadding:` 字样，
  而 M88 写成 `labelPadding: 0`（意思正是"没有命中区"）**全绿通过** —— 它在数字符串，不在数参数。
  现在读**值**（> 0 才算一处），并从"一个总数"改成"按文件点名的账本"。
  ② `testStyleForwardsItsParametersInsteadOfResupplyingDefaults` 旧版 `XCTAssertEqual(consumers, 3)`
  把"清扫只做了三处"钉成完成态，剩下五处圆形按钮退回 6% 而守卫全绿；
  现在按**形状**要求每一处表态（凡 `in: Circle()` 必须写 `hoverLevel:`）。
  ③ 高度那条判据第一版只读 `testCaptureKeyViews` 写好的 PNG，靠测试顺序才成立 —— 预检把它打回自渲染。

### Added（R20）

- **一把行带尺，用来把"哪些帧的哈希变了"翻译成"只有那一条动了"**（R20，仓库外
  `.scratch/motion-audit-2/diff_frames_r20.swift` + `inspect_r20.swift shift|crop|stats`）：
  逐档试纵向位移 k 并报告残余差异带。本轮读数：详情列 k=0 **0 行不同**（三处 `hoverLevel`
  在静置态确实零像素差、也没画坏药丸），筛选段那一行与整列行 k=2px **0 行不同**（纯平移），
  只有搜索框那 16 行是真变化。22 帧改动 = 框长高 1pt + 它下面整列平移 1pt。

### Fixed


- **推翻 R18 自己写下的"浮层拍不到"根因**（R19 / U-41 / D-077）：那句"因为浮层背景是
  `NSVisualEffectView`，离屏没有可合成层"两半都错 —— 读 `QuickPickController.ensurePanel()`，
  浮层里**根本没有材质视图**（普通 contentView + `drawsBackground=false` 的滚动视图 +
  `backgroundColor=.clear` 的表格）；而仓库外 spike 证明裸材质离屏**画得出来**
  （`mid=(58,58,58,a=255)`）。真正的现象是产品的 `NSStackView` 在捕获环境里只有 24pt 宽
  （真实 App 里撑满 420×300），于是滚动视图 0×0、`NSTableView.visibleRect` 0×0 ——
  表格有 5 行，一行都画不出来。判据因此从"限制还在"改写成**三层**（症状 / 标题 / 原因），
  第三条专门在原因过期时红。
- **一条"症状断言抓不到病因"的记录**（R19）：变异 M82 把夹具里留住控制器的代码拿掉
  （`NSTableView.dataSource` 是弱引用），`rows > 0` **没红** —— `numberOfRows` 报的还是上次
  reload 的 5；红的是新加的接线断言 `table.dataSource is QuickPickController`。
  以后写判据先问"接线断了这条读数还对不对"。

### Added

- **AppKit 夹具现在拍产品自己的窗口**（R19）：`Fixture.appKit` 从 `() -> NSView?` 改成
  `() -> NSWindow?`，R18 那条"帧名必须等于帧的尺寸"的不变量从此核的是浮层真实的 420×300，
  而不是夹具自己填的数。配套的 `QuickPickCapturePanel.builder` 把控制器关进闭包盒子保命
  （弱 `dataSource` 陷阱）。捕获路径新增一次"真实显示周期"
  （`orderFrontRegardless` 到屏幕外 + runloop + 递归 `tile()` + `display()`），
  **只作用于 AppKit 夹具**：SwiftUI 那 96 帧逐帧核过 `transparent` 与 `blackBandPt` 不变。

### Fixed（R18）

- **权重页的只读数值不再穿"可点"的颜色**（R18 / U-40 / D-076）：那一列九个值（「默认」/「160%」）
  原来用系统强调色画 —— 实测字形是 `(0,122,255)`，与链接同色，而同一页真正那颗「恢复默认」
  按钮是中性白字。另外两档也错：`>1.0` 涂橙（把说明里明写的合法取值 200% 画成警示色）、
  `<1.0` 涂次级（用户刚把这一行调低，数值反而退进背景）。现在文字与色调都从
  `WeightValuePresentation.percent(value:)` **同一个**判断出发（旧代码里那条
  `if pct < 100` 与下一行返回同一个串，是"判断被写了两遍、其中一遍烂了"的现场证据），
  没动过 = 次级、动过 = 主色。改后同一条判据逐帧数强调蓝像素：暗色 2345 → 0、亮色 2557 → 0。
- **帧的名字现在等于帧的尺寸**（R18）：`NSHostingView` 会把内容的理想尺寸写回窗口，
  于是 6/96 张帧的 `WxH` 是假的 —— 最要紧的是 `content-with-notice-750x560` 实际 1304 高，
  而这张帧的职责正是"提示条会不会把布局挤坏"（窗口偷偷长高 ⇒ 它从来没被挤过）。
  现在钉死 `sizingOptions`/`contentMinSize`/`contentMaxSize`，并在快门前断言窗口尺寸，
  96 张全部名实相符。
- **`weights` 夹具不再裁掉自己那一页的头部**（R18）：560 高的框套 850 高的内容，
  标题、说明文字、「恢复默认」按钮和第一行因子九轮以来从来不在帧里。改成 880，
  并补一张 `weights-adjusted`（160% / 40% / 其余默认）—— 新颜色梯度的"动过"那一态
  在此之前**没有任何帧**。帧基线 96 → 98。

### Added

- **材质盲区现在能被数出来**（R18 / BACKLOG 31）：系统 `List` 的选中高亮是材质，
  在没上过屏的窗口里画成 #000（亮暗都一样）⇒ "选中"这个状态从来没有像素证据。
  每张帧现在报 `blackBandPt`（连续黑像素 ≥60pt 的最大填充带），八个夹具名钉进
  `materialBlindSpotFixtures`：多一个红（又多处看不见）、少一个也红（那处能拍了，去看它）。
- **快速选择浮层"离屏拍不到"改成一条会自己作废的判据**（R18 / BACKLOG 30 的结论）：
  `testQuickPickOverlayStillCannotBeCapturedOffscreen` 断言的是"这个限制还在"
  （实测 `transparent=100.0%`）。它哪天红了，就是给浮层补帧的那天 —— 而不是删掉它。
  配套的 `Fixture.appKit` 通路保留，它是这条判据的地基。
- **两张帧共用量尺**（R18）：`transparentFraction` 从 `flattenedPNG` 的内联循环里提成
  一个静态函数，捕获失效闸门与浮层限制判据共用同一个 `transparentAlphaCeiling`
  （两处各写一个数字的话，"松一档"会让全透明的帧看起来像补帧成功）。

### 备注

- **R18 的选题没做成，且如实记着**：目标是"让 AppKit 表面第一次进帧基线"，
  实测浮层一张都补不上去（材质不可合成）。产出改成了量尺自己的三处不诚实（见上）。
- **变异 M76 是故意放的"期望漏网"**：把 `weights` 夹具退回 560 高，**没有任何测试会红**
  —— 夹具的高度仍然是记下来的数，这条记 BACKLOG 32（并写清为什么 `fittingSize`
  不能当那把尺：它在有 `.frame(height:)` 时恒等于被钉死的数，是一条恒真的尺）。

### Added（前几轮）

- **两张"从来没有存在过的帧"**（R14 / U-36）：`settings-privacy-excluded`（用户自己加过排除 App
  之后的那一行，含那颗破坏性的「移除」）与 `receipt-line`（回执行与它右边的 ×）。
  这两个控件只在交互之后才存在，90 帧夹具里从来没有它们 —— 于是 R13 改它们样式时是
  "源码已接、产物未量"。帧基线 90 → 94。种子串由 `CapturePolicy.encodeUserExcluded` 生成
  （手写分隔符翻过车：分隔符是 `;` 不是 `,`），并且夹具自己有一条"种过必须还原"的判据。
- **底色台阶的像素判据**（R14）：`testFillLaddersAreVisibleOnBothControlClasses`
  用 `NSHostingView` + `cacheDisplay` 画产品真正会画的那一层，按**均值通道差**逐档判
  （均匀底色用"变化像素占比"判恒等于 1，没有判别力）。
- **每日复制热图**（新功能 / 目标模式阶段一，D-068 / U-30）：设置窗口新增「统计」分类，
  以 GitHub 提交日历的形状画最近 26 周 × 7 天的复制条数，五档强调色强度 + 原生 tooltip
  （"2026年3月12日 周四 · 复制 8 条"）+ 悬停详情回落最忙日 + 汇总行（总数 / 日均 / 连续天数）。
  数据源是**单独的只追加账本** `daily-copy.json`（日键→条数，保留 730 天，损坏则改名保原字节），
  **不是**从 `entries` 现算 —— 后者有 500 条上限，现算出来的历史会随着旧条目被淘汰而**倒退**。
  账本为空时用现有存档时间戳回填一次，所以老用户第一天打开就有内容。
  采集路径**零同步磁盘写**（只加内存计数 + `.utility` 队列去抖原子写），退出路径同步 flush。
  回滚 = 删掉那一个文件，历史存档一个字节都不动；导出 / 导入 / 清空历史都不碰它。
  21 条用例（七张真值表 + 从产品入口的验收 + 磁盘行为），变异对照 9 支（M25、M25b、M26–M32）
  **第一次 8/9**（M31 逃逸），重写判据后 9/9 CAUGHT，
  其中 M31（回填不写盘）第一版判据**恒真**被重写、M32 是本轮真实崩溃（MainActor 闭包被
  `dispatch_assert_queue` 打断）转成的回归判据。已知未做两条如实记在 U-30。
- **动效目录 `MotionCatalog`**（动效审计 M11）：7 档用途 × 时长 / 曲线 / 减弱动态退化三张表，
  只写在这一处；全仓 9 处手写 `.easeInOut(duration: 0.11~0.15)` 与 AppKit 侧动画全部收敛或撤除。
  进场曲线换成一手 cubic-bezier `(0.23,1,0.32,1)`、退场 `(0.2,0,1,0.9)`（M17）。
- **顶部提示条非对称过渡**（M2）：滑入 + 淡入 150ms，退场只淡 120ms；下方内容跟着一起滑，
  不再被"顶一下"。实测 3 帧、159ms 落定。
- **详情区换类型时交叉淡入**（M4 的可行版本）：文本↔图片↔文件↔渲染/原文才演，
  文本→文本不演（`DetailPreviewKind` 钉的是"视图类型身份"，不是 `entry.id`）。
- **复制成功回执**（M7）：图标换勾 + 文案 + 1.1s 自动收回；**写失败时不再谎报"已复制"**；
  macOS 14+ 同步向 VoiceOver 播报这句话（12/13 无该 API，已如实记账）。
- **侧栏空态 ↔ 列表、设置换分类、菜单栏状态行**淡入；拖入落点框淡入 + 轻微收缩（M8）。
- **动效降级升级为全源门**（M16）：系统「减弱动态效果」**或** VoiceOver 在跑就退化；
  并接住 `accessibilityDisplayOptionsDidChangeNotification`，中途改设置当场生效（MC-4）。
- **像素级动效判据进仓库**：`MotionFilmstripTests` 在真实窗口里逐帧抓取，
  只量目标元素包围盒，"分摊到几帧"与"离最终态还多远"两档一起打分；
  配三条对照（纯数据 step/ramp、空白窗口、关掉目录曲线的 A/B）。CI 新增报告型一步（MC-8）。
- **快速选择浮层的候选行现在真的会动**（动效审计 M1 的替代路径，D-056 ①）：这个浮层本来就是
  `NSTableView`，所以走它自己的原生行动画 —— 输入时候选变少那几行淡出、重新匹配上那几行淡入，
  而不是整块文字闪一下。刚复制的内容被顶到最前属于"整体重排"，原生行动画表达不了，
  刻意退回整表刷新并在日志里写一句。实测：开 `.effectFade` 那臂过程摊到 11 帧（≈100ms），
  关掉之后一帧到位，两臂峰值同量级。减弱动态时传"空效果集"而不是跳过更新。
- **详情预览的加载态从转圈换成骨架扫光**（M9）：三条灰杠 + 一条匀速扫过的亮带，
  说的是"内容马上来"而不是"我在等"。只在加载那一段存在（最坏 8 秒，超时改判失败态），
  减弱动态时灰杠留着、不再扫。亮带抬升写成最小 0.08 的判据 —— 之前"只抬 5 个点"在像素上等于没动。
- **收藏 / 固定的符号反馈补回来并叠加**（M5 / MC-12 的更正）：macOS 14+ 先做符号形变过渡、
  再叠一次弹跳；12/13 退化为淡入。侧栏行内的星标同样接上（这一条**量不到**，转人工）。
  「再次复制」故意不给弹跳 —— 每天上百次的动作不该有弹性。
- **拖入落点在虚线框外面多一圈柔光**（M8 后半句）：虚线说"这里能放"，光说"现在正对着你"。
- **按压态从零到有**（视觉迭代 R4，D-061）：新增 `PressedStyle`（全 App 唯一的 `ButtonStyle`），
  把 `isPressed` 翻成缩放 0.97 + 一档比 hover 更重的底色（0.12），走 `.hover` 那 0.12s；
  接上 9 处图标与行内按钮，整行类只给底色不缩放，菜单栏两处**刻意不接**并写明理由。
  减弱动态时缩放归零、底色留着。强度次序 `hover < pressed < selected` 写进判据。
  **诚实记账**：真按下的在屏探针在 xctest 里送不到按钮（`keyWindow=nil`），
  所以按压态是"源码已接、产物未量"，手感转人工批次 12.1–12.7。

- **字号收成一族刻度**（视觉迭代 R3，D-060）：文本 8 档（9/10/11/12/13/14/15/16）收成
  `meta 11 · row 12 · body 13 · title 14`，大符号按角色命名，10pt 写成全 App 下限。
  顺带修两处能看出来的缺陷：侧栏"15 条记录"比区块标题还大一号（次要盖过标题）、
  "固定"徽标 9pt 在 2× 下笔画并成一片。`body` 改为**引用** `StatePresentation.messageFontSize`
  而不是抄一个 13。20/82 帧变化并逐组归因（基线同提交更新）。

- **动效判据改成按时间表达**（视觉迭代 R2，D-059）：`MotionFilmstripTests` 里"过渡帧数 ≥3"
  "第 3 帧之后""到位帧数 ≤6"这类**绝对帧数**判据，全部换成由"声明时长 ÷ 实测采样间隔"推出来的
  分辨率感知判据（地板 2 帧 ⇒ 一帧跳变照样红），取样锚点从预卷改到触发那一帧；新增前提检查
  "触发前后必须逐像素不同"。CI 结论行加 `MOTION_RESOLVE_SUMMARY judged=n/m`，
  "3/3 全绿"与"只判了 1 条"从此不是一回事。**顺带摘掉一条假证据**：`notice-banner=3` 原来被读成
  "横幅淡入量到了"，实测那一卷首尾逐像素相同（离屏 `cacheDisplay` 抓不到落定后的横幅）
  ⇒ 现在如实报 `premise-not-visible`。
- **视觉令牌 `VisualTokens`**（视觉迭代 R1，D-058）：圆角 / 发丝线 / 线宽 / 投影 / 悬停底色 / 描边强度 /
  材质这七族参数从此只有一个作者。四档圆角 `chip 4 · control 6 · card 8 · panel 9`（轨道 = 内档 + 1），
  唯一出口 `VisualShape.rounded` 永远 `.continuous`；投影两档 `flat` 与 `raised`，
  其中"浮起的玻璃必须先分组合成"绑进定义本身（写不出来就不会漏）。
  配套 11 条判据：视图里出现 `RoundedRectangle(cornerRadius:` / `.shadow(color:` / `lineWidth: 数字`
  直接打红，令牌没人读打红，`Views/` 里出现没有构造点的死表面打红，强度与半径的**次序**是语义约束。
  减弱动态时整圈光不画（HIG 明确反对淡入淡出模糊），虚线框仍然淡入。

- **三条"代码里写了过渡、屏幕上没有"的缺陷修掉**（视觉迭代 R5 / D-062 / U-26）：
  详情空态的 `.transition` 原来是孤儿声明（`body` 上没有任何驱动）、侧栏空态的过渡挂在
  `Spacer()` 上、收藏与固定两臂拿不到动画事务。现在三处都会真的淡入，
  键分别是"有没有选中"与 `isFavorite` / `isPinned`（换选 A→B 不演）。
- **复制失败终于有回执**：以前写进剪贴板失败时界面与成功长得一模一样，
  而代码注释还声称"并弹顶部横幅"（那条横幅来自另一条链路）。
  现在失败位显示 `exclamationmark` + 说明文案 + 1.1s 自动收回，macOS 14+ 同步向 VoiceOver 播报。
- **菜单栏推荐列表删掉一条不会执行的声明**：`MenuBarExtraStyle.menu` 的内容会被编译成真的 `NSMenu`，
  SwiftUI 的过渡在那一层根本不执行（D-055 / M15 实测）；留着一行只会让下一个人以为已经做过了。
- **"不许留不会执行的过渡声明"这条判据从单文件扩成按族扫 `Views/*.swift`**，
  并且豁免改成结构判据（ViewModifier 的 `content` 占位符 + 该文件确实声明了它）。
  第一版的豁免写成 `!line.contains("content")`，被角色名 `.contentFade` 白拿 —— 变异 M6 实测 ESCAPED，
  修完 2/2 CAUGHT，并新增一条不门控的真值表判据（`testTransitionClaimScanIsATruthTable`）。
- **动效判据的读数从"几帧在动"换成"动了多久"**（D-063）：同一份代码本机三次读出过渡帧数 `3 / 2 / 2`
  （HEAD 上也读到 2），而变化段时长 `131 / 119 / 125ms` 稳定。新判据 `judgeMotion` 用
  "事件内最粗采样 ≤ 0.3×声明时长"定分辨率、"变化段时长 ≥ 0.4×声明时长"定过渡成立，
  常数由 `d − 2s` 与 `s` 两个边界解出来；产品级变异 M8（摘掉侧栏空态驱动）CAUGHT。
  代价如实记账：本机 `detail-kind-change` 转为 `MOTION_NOT_RUN=clock-coarse-in-window`，
  `MOTION_RESOLVE_SUMMARY judged` 2/3 → 1/3（CI 的 26–30ms 时钟上仍然判）。


- **详情预览三态现在会说话**（视觉迭代 R6 / D-064）：`loading → 成功 → 超时失败`
  以前是一帧硬换（三分支没有任何过渡、容器没有驱动），现在按**阶段**软交接。
- **破坏性「清空未收藏」补上数字回执**：以前按完确认之后红色按钮还在原位、还能再点，
  界面上没有任何一处说"清掉了多少条"。现在按钮正下方淡入一句
  "已清空 N 条未收藏记录，M 条收藏保留。"，0 条也出声，macOS 14+ 同步播报。
  计数收进新的纯函数 `ClearHistoryReceiptPolicy`，控制器**先数再清**（`HistoryStore` 零改动）。
- **多文件展开的箭头改成旋转**：`chevron.right↔down` 换名字是一帧硬换，而旁边内容正在用
  0.22s 展开 —— 现在两者挂在同一条曲线上，静止画面逐像素不变（82 帧 `CHANGED=0` 为证）。
- **新增一族判据 `MotionDriverTests`**（8 条）：`.animation(_:value:)` 的键不许是字面量 ——
  这是第五轮"声明了过渡却没有供电"的**镜像**缺陷：挂了动画而键永远不变，
  读代码的人只看到"动画已接"。扫描器带真值表（字面量要抓 / 合法表达式不误报 / 跨行 / 嵌套括号）。

- **快速选择浮层的空结果不再是一片空白**（视觉迭代 R7 / D-065 / U-28）：
  三种"空"说三句不同的话 —— 打的词没中带「词」原样回来并给"换个词或按 Esc"，
  有历史但筛空说"没有可显示的记录"，从来没有历史说"先复制点东西"。判定是纯函数，
  面板里那一句话按目录时长淡入。
- **侧栏批量条两臂都有过渡**（以前进批量软交接、出批量一帧硬换）；
  **视频播放/静音两颗图标接上唯一的 `symbolMotion` 入口**（胶囊那四颗早就接了，
  同一个仓库不该两套语言），高频动作刻意不给 bounce。
- **新增一族判据 `OverlayStateTests`**（6 条）：符号替换在 `Views/` 里只能有一个作者
  （除 `MotionModifiers.swift` 外出现 `.contentTransition(` 就打红）；
  QuickPick 空态走真 `HistoryStore` 的管线级断言；面板判据**钉调用点而不是钉函数名**
  （第一版只 `contains("applyEmptyState()")`，被函数定义行白拿，变异 M15 绿着通过 —— 与 R5 的
  `content` 子串同形复发，重跑后 5/5 CAUGHT）。
- **CI 多了道会红的覆盖率闸**：动效那一步是报告型，"今天只判了 1 条"和"判了 3 条"原来长得一样。
  新增 `Motion coverage floor`：跑完了、有结论行、而 `judged < 2/3` ⇒ 红。
  它自己由 `scripts/tests/test_ci_report_selftest.py` 四个形状钉住，其中一格期望退出码 1。

- **「不记录这些 App 的复制」不再让人猜**（视觉迭代 R8 / D-066 / U-29）：
  存档编码会去重 + 排序，所以"加进去了 / 本来就有 / 它属于系统默认排除项"三种结局
  以前在界面上一种都看不出来（输入框清空、列表没长 ⇒ 读成"我加的那条去哪了"）。
  现在判定收进纯函数 `ExcludedAppListPolicy`，六种结局各给一句话，
  没做成时不改存档也不清输入框；名单行的增删有过渡（这里是普通 `VStack`，不是 `List`）。
- **三处结果文案统一成 `ReceiptLine`**：淡入 + 一个 × 自己收掉。
  **刻意不做自动消失** —— 导出路径、导入条数、排除增删都是"你刚做那件事的结果"，
  1.1 秒后自己没掉等于把信息拿走；这条决定由一支反向变异（M23）钉住。

### Changed

- **快速选择浮层里"刚复制的那条被顶到最前"不再整表硬刷新**（R17 / D-075 / U-39）：
  `QuickPickRowDiff` 以前把"保留行的相对顺序变了"整类划成"原生 API 表达不了"，
  于是这个浮层**最高频**的一次变化一直是 `reloadData()` —— 六行全部重画，没有移动可言。
  现在"恰好一行挪位"升成一次 `NSTableView.moveRow(at:to:)`（动与不动走
  `NSAnimationContext.allowsImplicitAnimation`，减弱动态时行照样挪、只是不滑）；
  多行同时跳、以及移动混着增删的形状**仍然**退回整表刷新 ——
  那些要硬凑成一串 `moveRow` 就得猜 AppKit 的坐标系约定，猜错是"安静地排错行"。
  识别"一行挪位"要试**两个**候选：`[a,b,c,x] → [x,a,b,c]` 里第一个不同的位置是 0，
  而真正在动的是末行的 `x` —— 只试左边那个，就会把本轮唯一要救的形状判成"表达不了"。
  这条改动**没有**静止帧证据：快速选择浮层是 AppKit 面板，而帧夹具只会拍 SwiftUI
  （缺口记 BACKLOG 30）；胶片对照臂已加，本机这一轮因进程未激活按规矩报 not-run。

- **详情区"空 ↔ 内容"现在两臂都在演**（R16 / D-074 / U-38）：以前只有空态那一臂挂了
  `.transition(contentFade)`，内容臂是一帧硬切 —— 于是**删掉最后一条记录**时内容瞬间消失、
  空态再从全透明淡进来，整块详情区空白约 160ms。那正是 D-055 当年否决"整块淡入"用的理由，
  只是它留在了另一条没人看的路上。现在两臂成对，才是真交叉淡。
  换选（A→B）仍然不演：供电键是"有没有选中"这个布尔，不是"选中的是哪一条"
  （守卫第三条断言钉着，改错就红）。
  **这条淡入今天仍然量不到**：双向 A/B 两臂读数逐位相同（`开 帧数=1 峰值=0.030 / 关 帧数=1 峰值=0.030`，
  冷采样闸已过），所以状态记成「源码已接、产物未量」，观感在人工验收批次 25。

- **三处小控件的悬停/按压高亮现在比字形大一圈，而且那一圈点得动**（R15 / D-073 / U-37）：
  `PressedStyle` 的底色一直铺在 label 的包围盒上，所以 16pt 图标的"药丸"紧贴笔画，
  而系统工具栏那颗是"图标 + 每边约 5pt"且**命中区与高亮同尺寸**。
  新增 `labelPadding`（默认 0 ⇒ 其余 12 处按钮一个字节不变），侧栏五颗批量按钮给 5、
  排除名单的「移除」与回执 × 给 4；侧栏 `HStack` 的 spacing 从 8 收到 0，
  让相邻两颗的高亮正好挨着（留着 8 再加 5 会露出 18pt 空隙，读成五个孤立方块）。
- **`VisualFill` 的每一档现在都必须被量到**：新增第三条状态梯子（输入框 280×28）
  与一条集合相等守卫 —— 加一档令牌而没进梯子就红。这是 R13→R14 那一课的工程化：
  上一轮抬一档只证明了"比 0 看得出来"，没证明"跟相邻那档还分得开"。
- **搜索框"空着"与"正在输入"在暗色下原本是同一张脸**（R15 / D-073 / U-37）：
  `fieldIdle 0.035 → fieldActive 0.06` 的画面差只有 **3.98/255**，低于地板 4。
  `fieldActive` 抬到 **0.075** 之后是 `7.97 / 6.97`（亮/暗），6 张帧复核过。
  两条出路里选了改动小的那条（抬激活态改 6 张帧，放轻静止态会改 20 张）。
  **这条缺陷差点不存在**：新梯子第一版从硬编码的 0 起步，量的其实是 `idle→fieldActive`，
  变异 M66 因此全绿通过；把起点改成梯子自己的第一步之后，它当场红。
- **窄侧栏第一次有了帧**（`sidebar-multi-select-min-250x520`，250 = `ContentView` 的 `minWidth`），
  顺带修掉夹具一处会撒谎的地方：`sidebarFrame` 把宽度写死 300，
  第一次拍 250 时两边各裁 25pt，看着像"产品在窄宽度下溢出"。现在宽度是参数。

- **小控件的悬停档从 0.10 降到 0.08**（R14 / D-072 / U-36）：R13 为了让 22pt 图标上的悬停看得出来
  把那一档从 0.06 抬到 0.10，而按下是 0.12 —— 新加的像素判据量出**从悬停按下去只差 3.7/255**，
  低于"一块平面上看得出来"的地板（4/255）。也就是说 R13 修好悬停的同时把按压抹平了，
  而当时全部判据（真值表 / 白名单 / 集合相等 / 变异 5/5）都是绿的。
  现在两类控件各自的完整状态梯子（行 44pt 四步、小控件 22pt 三步 × 两种外观）每一步都 ≥ 7.4/255。
- **设置页隐私分区那句说明不再在屏幕上打印字面星号**：原文写的是 `**你额外**`，
  而设置页的 `Text` 走普通字符串、不解析 Markdown（详情区那条渲染管线是给内容用的，不是给 chrome 用的）。
  改法是去掉强调而不是接上渲染器 —— 这一页别处都不加粗。由 R14 新增的那张帧钉住。

- **悬停那一档从"设计里有、运行时不存在"改成真的**（R13 / D-071 / U-35）：R4 立按压反馈时
  把 `VisualFill.hover` 写进了令牌、写进了纯函数、写进了真值表，唯独没写进能持有它的那一层 ——
  `ButtonStyle.makeBody` 不能有 `@State`，于是那里硬写着 `isHovered: false`，
  **全 App 每一个按钮**的悬停档在运行时都不可达，而所有围绕它的判据都是绿的。
  现在样式内部多了一个真的视图（`@State` + `.onHover` + 进 `.hover` 那一档事务）。
- **三处 `.buttonStyle(.borderless)` 归队**：侧栏多选条的五颗批量按钮（含**删除**）、
  排除名单的「移除」、回执行的 ×。它们以前既没有按压也没有悬停；
  而 `.borderless` 还顺手把图标本体压成灰色，于是**可用的动作被画成了禁用的动作**
  （帧基线两帧变化：`sidebar-multi-select` 明暗各一，变化区就是那四颗描线图标，
  红色 `trash` 因带显式 `foregroundStyle` 一个像素没动 —— 恰好反证压暗来自样式）。
  小控件这一档用新增的 `hoverLevel` 参数抬到 `VisualFill.controlHover`（0.10），
  其余站点保持 0.06 不变（不顺手改全 App 的观感）。
- **一条守卫的检测面加宽**：`testEveryNonMenuButtonHasPressFeedback` 原来只查 `.buttonStyle(.plain)`
  一个拼写 —— `.borderless` 从尺子底下走过去，在全绿的套件里活了很久。现在一族四种拼写一起查
  （plain / borderless / link / accessoryBar），白名单只剩菜单栏那一处。
- **变异对照第一次 4/5**（M54–M58）：M58（样式内部转交时把 `hoverLevel` 换成默认档）全绿通过 ——
  本轮新加的参数自己重演了本轮修的那条缺陷族。补
  `testStyleForwardsItsParametersInsteadOfResupplyingDefaults`（取 `func makeBody` 的花括号配平区域，
  判"四个入参原样转交 + 转交点不许出现常量 + 全仓恰好三处消费者"）后 **5/5 CAUGHT**，
  区域助手另配一条真值用例。

- **侧栏筛选胶囊不再"冲过头再弹回来"**（R12 / D-070 / U-34）：那颗胶囊以前自己写着
  `response 0.38 / damping 0.72` —— 0.38 越过动效目录的上限，0.72 是欠阻尼（必有过冲），
  而它是**点出来的**、不是手势跟手的位移。现在参数出自目录新增的 `.slider` 档
  （0.20s、临界阻尼），目录白名单因此少了一格（`HistorySidebarView.swift` 不再在目录外写曲线）。
- **同一个文件里两套「减弱动态」闸门合成一套**：以前这颗胶囊只读
  `@Environment(\.accessibilityReduceMotion)`，而全仓其他地方读
  `MotionCatalog.motionShouldBeReduced`（系统开关 ∪ VoiceOver）⇒ 开着 VoiceOver 的人
  别处都降级、只有它还在弹。现在两处都取或。
- **修掉一条"开了减弱动态 = 悬停零反馈"**：分段按钮以前**只有缩放**一种悬停表达，
  而 reduce 会把缩放归 1.0。现在补一层 `VisualFill.controlHover` 底色，
  它不受 reduce 影响（底色是信息，缩放才是物理隐喻）—— 这是"reduce 是替换不是删除"
  这条规矩以前真正的空洞。
- **统计页「这张图怎么读」那块说明现在跟着图一起淡入**（R11 / U-33）：
  以前只有图的两臂有过渡，说明块（分隔线 + 五行读法）是整块硬蹦出来的。
  过渡与驱动键成对出现，由 `testStatsGuideTransitionIsPairedWithADriver` 钉住（M47/M48 CAUGHT）。
- **动效胶片探针现在能拍非主窗口的界面，并且会等时钟热起来才触发**（R11）：
  `Scenario` 长出 `root` / `storeFactory`（宿主是产品自己的 `DailyCopyStatsSection`，为此从
  `private` 放开到 internal —— 探针自带一份"长得像"的视图就等于测替身）；
  新窗口头两次 `cacheDisplay` 要 260–340ms 一帧，触发落在那段上时一次 160ms 的过程
  只会被拍到两三个样本，所以加了冷采样闸门 `clockIsWarm`（≤120ms 才触发，最多预卷 6 帧）。
- **一条被量出来的尺子边界**（R11 / BACKLOG 23）：双向 A/B 实测
  `开 帧数=1 峰值=0.225 / 关 帧数=1 峰值=0.225` —— 把动效目录整个关掉读数不变，
  说明 `cacheDisplay`（抓模型树）**看不见纯 opacity 的淡入**。
  因此热图那条淡入的状态被定为「源码已接、产物未量」：不写进"已验证"，也不反过来说"产品没做"。
  这同时改变了以前几轮 MOTION 数字的读法 —— 它只覆盖带布局位移的那类过渡。
  `testHeatmapFadeIsNotVisibleToThisRuler` 是会自我作废的判据：尺子哪天看得见了它就红。
- **热图自检（R9，阶段二第 1 轮）**：上一轮自己写的三条被抓出来并修掉 ——
  ① 悬停描边与"当天那格变深"原先挂在一条**永远不会演**的动画上
  （`.animation(.hover, value:)` 驱动的是页脚那个不可插值的字符串），
  现在事务挂在变更点上，格子按 `bucket` 插值（同档内的复制不该让画面动）；
  ② 页脚那行字**刻意不再挂动画**并写明理由（字符串换字不插值，
  要"有过程"只能 `.id().transition()`，而它在 macOS 12/13 上会先空一帧，比硬换更糟）；
  ③ 空态 ↔ 网格两臂都补上过渡并由 `counts.isEmpty` 驱动 ——
  第一条复制那一下现在是淡入淡出而不是整块硬换。
  另两条看帧才看得见的：**零值汇总行**（"共 0 次 · 日均 0.0 · 连续 0 天"）不再与
  "还没有可统计的记录"同时出现（决定进策略：`summaryLine(for:hasRecords:) -> String?`），
  「这张图怎么读」那段说明改成**跟着图一起出现**，且写在观察账本的那一层
  （挂在 `SettingsView.body` 上会拿到开页快照 ⇒ 用户复制第一条之后说明永远不出现）。
  判据新增 5 条（含一个按花括号取成员体的区域助手，它自己也进了真值表），
  变异 M33–M42 **10 支全 CAUGHT**。账见 **D-069 / U-31**、批次 18。
- **撤掉 QuickPick 与主窗口的呼出动画**（M3/M10 定稿）：热键 / 每天上百次的入口按规范
  就该瞬时出现，四家同类逐行核对全部如此；`animationBehavior = .none` 保留。
- **八个表面的几何与材质收口到令牌**（R1）：缩略图 0.16/0.14 两种描边与 0.08/0.06 两种投影各成一档、
  搜索框激活描边 0.095 → 0.10、设置侧栏行悬停 0.045 → 0.06、Markdown 切换 0.07 → 0.06、
  4pt 那四处补上 `.continuous`（同一屏里不再并存两种曲率语言）、视频控件的浮起投影补上分组合成。
  28/82 帧有变化并逐帧归因（`search-field-*` 最大通道差 1；`detail-2-file-*` 那 86×12.5pt 一行字
  就是下面那条字号修正）；`glass-pill-*` 像素完全不变，证明玻璃重构是等值的。基线与改动同提交。
- **删掉两个"活着的死表面"**：`GlassCircleButton`（产品零调用点，只被一条测试当符号名字夹具养着，
  连带它拖着的 `hasOwnSurface` / `showsBorder` / `GlassBorder.isHovered` 三个永远只剩一种取值的参数）
  与 `HistoryRow`（注释写着"保留给夹具与详情以外的调用点复用"，实测产品与测试都没有调用点）。
- **详情加载文案字号回到自家规范**：`StatePresentation.messageFontSize` 早就写着 13，
  而"正在加载预览…"那句是 12；本轮改成取规范，同时把失败态与"读不到视频信息"那两句也接上同源。
- **列表行增删重排过渡确认做不出来并砍干净**（M1）：`List` 是 `NSTableView` 后端，
  四种写法（含"把动画事务挂到变更漏斗上"）分带实测全部一帧到位；
  行上的 `.transition` 声明已删除，并留一条源码守卫禁止再加（它不执行，只会误导）。
  主列表这一侧结论不变（不赌 `List`）；能动的路径改到快速选择浮层上做了，见上面那条。

- **设置「通用」页两项全局开关**（第三轮审计 D-3）：「暂停记录剪贴板」与「识别截图文字用于搜索」。
  暂停只挡后台自动采集（changeCount 照常推进，恢复时不会补记暂停期间的旧内容），
  用户点名拖入的文件仍然入库；OCR 关闭后不再对新入库图片排识别任务。两项都持久化在 UserDefaults。
- 拖入文件被忽略时给出横幅反馈（D-4）："拖入的 N 项不是本机文件，未加入历史" / "已加入历史，另有 N 项…已忽略"。


- **按 App 排除记录**（第三轮审计 §5 F-1）：默认名单挡住密码管理器与系统钥匙串
  （1Password、钥匙串访问、系统设置「密码」、Bitwarden、LastPass、Dashlane 等），
  「隐私」页还能自己往里加。判定优先级：用户显式动作 > 暂停 > 名单；
  来源 App 读不到时不挡（否则表现为历史记录莫名失灵）。
- **OCR 文本可选「只索引不落盘」**（§5 F-4）：识别结果仍可搜、可显示，但不写进历史存档（用例直接核对 `history.json` 的字节），
  重启后即失效。默认仍是落盘，不改老行为。
- **固定条目**（§5 F-5）：条目可固定，固定项恒在列表最前、不被"再次复制"顶下去、也不参与保留清理；
  行首有 `pin.fill` 徽标，多选时表头有批量固定/取消固定，单条记录用详情浮层新增的那颗按钮。
- **历史导出 / 导入**（§5 F-5）：「数据」页可把历史导成 JSON 再导回另一台机器；
  图片一律跳过并在提示里明确计数，导入按条目 id 去重（同 id 不产生第二条）。


- **详情区排版**（第三轮审计 §4 U-4）：正文限一个可读列（68 个字符宽，14pt 等宽下为 652pt）并折行，
  不再是一行铺满 ~700pt 还要横向滚动；头部两行居中 meta 改成一条左对齐（时间 · 大小 · 来源 App）。
  搜索时正文里的命中处涂系统黄底色（亮色实测 13.57:1、暗色 5.60:1 的字/底对比度），
  命中只加临时属性，选中复制到的仍是原文。
- **状态语言统一**（§4 U-5）：加载 / 空 / 警告 / 错误四种状态共用一份规范（图标 + 一句人话 + 可选一个动作，
  统一 13pt 文案 / 12pt 图标 / `.secondary`），顶部横幅与菜单栏状态行改用同一个组件；
  「无匹配结果」在搜索非空时给「清除搜索」这一步。菜单栏那句状态从 11pt 升到 13pt。


- **富文本保真（RTF / HTML）**（第三轮审计 §5 F-2）：从 Word、Pages、邮件复制的带格式文字，
  进历史后再粘出去仍保留加粗与链接。写回按 RTF → HTML → 纯文本 登记，只认纯文本的应用不受影响。
  **默认关闭**（打开会让每条文本记录多存两份表示，且 RTF 常带来源元数据），在「通用」页打开；
  超过 256KB/份或 384KB/条的表示整份丢弃而不是截断（截断的 RTF 是坏结构）。
  导出/导入仍只带纯文本，并在提示里明确说出"有 N 条带富文本格式未包含"。
- **多文件条目可以拖出了**（§4 U-2）：以前多文件条目整条不提供拖拽（一次拖多个 item 需要
  系统级 dragging session），现在通过路径数组表示一次带走全部文件；判据是把 provider 写进
  命名剪贴板再读回来解码，确认三个路径真的都在里面。空列表仍然不承诺拖拽。


- **快速选择浮层**（第三轮审计 §5 F-3）：默认 **⌃⌥⇧V**（刻意不是 ⌘⇧V —— 那是浏览器与编辑器里的
  "粘贴并匹配样式"，全局抢走会让所有用户的那个功能失灵；想换回来可在「快捷键」页自行录制），
  也可以从菜单栏「快速选择…」打开。打字即筛（正文、来源 App、文件名都能搜），↑↓ 移动，
  回车 = 复制并粘回你原来所在的应用，Esc = 直接关掉、什么都不动。
  换搜索词时选择一定回到第一条：不留旧下标，免得搜的是 A、粘走的是 B。
- **运行时启动冒烟测试**（§3 C-4）：新增 `scripts/launch_smoke.py`，把打包后的 app 真启动一次，
  以生命周期日志判定"确实跑到了 applicationDidFinishLaunching，且没有被第二实例守卫静默中止"。
  它靠新的 `CLIPBOARD_HISTORY_DATA_DIR` 环境变量把存档与日志都关在临时目录里，
  不会读写用户自己的历史存档。CI 里以报告型步骤运行；判定逻辑本身有硬门自测。

- **帧基线进 CI**（第三轮审计 §3 C-2）：`docs/frame_baseline.json` 保存每张离屏帧的 sha256，
  `scripts/frame_baseline.py` 分开报「变了 / 少了 / 多了」三类差异；CI 里"少帧"是硬门、"变帧"是报告型步骤。
  以前 CI 只回答"今天拍得出来吗"；现在硬门答"夹具/界面变了却没更新基线"，报告型答"和上一版（发布时冻结在 `docs/frame_baselines/vX.Y.Z.json` 的基线）比哪些帧变了"。

- **右侧预览渲染 Markdown**（新增功能）：`.md` / `.markdown` 文件与"看起来就是 Markdown"的文本记录，
  详情区不再是一坨等宽原文，而是渲染结果 —— 标题字阶、粗体/斜体、行内码与代码块灰底、
  列表悬挂缩进、任务项 ☑/☐、引用缩进、表格等宽保对齐、链接可点（只认 http/https/mailto）。
  头部同一行右端给一颗「原文 / 渲染」，**渲染只改看法**：存档、搜索、行预览、"再次复制"
  走的都还是用户原来那一份字节。文本条目的判定要求**两类不同语法同时出现**，
  所以 Python/Shell 里成片的 `# 注释` 不会被误排成大标题（`AGENT_DECISIONS.md` D-050 记了取舍与不支持的子集）。
  中文强调用字重而不是合成斜体（系统没有真中文斜体），渲染上限 4 万字并在尾部说明。
  手写解析器另配一条固定种子的随机模糊守卫（20000 例：判不崩、单次耗时上有界、不丢可见文字）。
  文件**已被移动或删除**时不给这颗控件（那时两种看法都不存在）；控件高度与 meta 文字同高，
  所以"有没有第二种看法"不会改变头部高度、列表不会因换选而跳。

### Fixed

- **统计页那条"写入失败"以前可能永远不出现**（R10 / BACKLOG 14 / U-32）：
  `lastWriteError` 是"计算属性读一个跨队列的加锁盒子"——值不会丢，但**没有任何东西为它发布** ⇒
  写盘失败之后如果用户不再复制，那一行不上屏；重启之后永远是 `nil`。
  现在它是 `@Published` 镜像，由一个**只送"该重绘"、不送值**的主队列回看触发
  （通知被丢掉只是晚显示，不是静默 —— 原来那半条性质保住），
  `flushPendingSaves()` 也自己同步一次（退出路径上没有"下一次去抖到期"）。
  反向判据同批补上：`@Published` 赋值必发，所以"值没变就不发"那句比较是必需的，
  否则每复制一条都会让设置页为一条不存在的错误重排一次。
- **一条全绿的探针量的是五个已经不存在的图标**（R10 / BACKLOG 16）：
  `OffscreenSymbolInkProbeTests` 的符号名单是手抄的，`sparkles` 早已换成 `wand.and.stars`、
  新增的 `chart.bar` 没进名单。现在名单从 `SettingsCategory.allCases` 推导，
  并加"名单 == 产品"与**逐枚**墨水两条判据（符号名写错或该符号在 macOS 12 上不存在时
  SwiftUI 不报错、只是什么都不画，而整列墨水会被其余五枚抬着走）。
  顺带量出真正的异类：`wand.and.stars` 的墨水比同列最轻的一枚还轻 2.3 倍（记 BACKLOG 22，本轮不改）。
- **收起侧栏后，详情头部与窗口左上角的关闭/最小化按钮叠在一起**（用户真机反馈，见账本 D-053）：
  详情区从 v1.2.1 起把整块内容铺到窗口顶（`ignoresSafeArea(.top)`），头部那一行落在距顶 10pt，
  而交通灯实测占 19–33pt —— 侧栏开着时灯压在侧栏上看不出来，一收起侧栏就撞。
  现在让位量由摆放按钮的那段代码在运行时发布（带工具栏时标题栏容器 66pt，灯带底边稳定在 33pt，
  所以这个数不能写死），首帧用兜底值。改完详情 meta 在 42pt。
  注意：**这一类缺陷离屏帧永远拍不到**（帧捕获的是 `contentView`，不含标题栏），
  所以配套的是"真窗口量一次 + 能被打红的接线判据"，不是更多帧。
  同一轮之后，收起侧栏这条路已被整体撤销（见上面「侧栏不再能收起」，D-054）——
  这条让位补丁因此从"修缺陷"变成"防御纵深"。
- **点选列表条目后有可感知的延迟**（用户真机反馈，见账本 D-036）：行上的双击手势一度改成
  `.onTapGesture(count: 2)`，那个识别器要等一个双击间隔才能确定"这只是一次单击"，而改成系统
  `List(selection:)` 之后行的选中正是经由这套行内点击识别下发的，于是高亮被整体推迟了一个双击间隔。
  现在改回 `simultaneousGesture(TapGesture(count: 2))`：它不参与"谁赢"的仲裁，单击立刻高亮、
  第二击照常复制（shift/⌘ 双击仍然不写剪贴板）。这条是我为了迁就一个**不代表真实侧栏容器**的
  离屏探针而改了产品交互，反向守卫与教训一并写进账本。
- **图片文件条目在左侧列表里没有预览**（用户真机反馈）：从 Finder 复制一个图片文件时，剪贴板通常不带
  图像数据，条目的 `thumbnail` 因此是空的，行首只能画一个通用文档符号；而详情区是按 URL 现读文件的，
  两边不一致，看起来像"图丢了"。现在 `add` 一条图片文件后会在**后台队列**解一张长边 ≤256px 的缩略图
  写回条目并落盘（不是全尺寸：缩略图会存进历史目录，全尺寸等于复制一份用户文件），
  启动时也会给已有历史里缺预览的图片文件条目补上（与 OCR 回填同一时机）；拖拽入库走同一条路径。
  非图片、文件已不存在、网页地址都安静地返回空，行首保持符号图标。
- **列表拖出与拖选争用**（D-1，S2；最终取舍见账本 D-034）：侧栏改用系统 `List(selection:)`，
  单击选中、shift 扩选、⌘ 加选、方向键移动与滚动跟随、VoiceOver 的 selected 语义全部交回系统实现。
  以前整行挂 `onDrag`，系统在每个阈值处先开拖出会话，**拖选在大多数条目上已经失效**。
  真机验证还发现：在 `List` 里"只让行首把手可拖、行体用来拖选"做不到（行内任何一处 `.onDrag`
  都会被提升成整行拖拽源），因此本轮的取舍是**保留整行拖出、放弃拖选**
  （macOS 侧栏本来不做橡皮筋多选）；选中请用单击 / shift / ⌘ / 方向键。
  `dragSelectRange` 这条动作与它的行位置表一并删除，不留半套死码。
- 推荐理由不再把"前台是浏览器"说成"偏好链接"（D-2）：内容类型标签改由条目自身类型决定。
- 存档"只加可选字段不升版"这一决定补上新→旧→新往返用例（D-5），边界写进 `migrate` 注释。
- 降采样后的图片现在自带新尺寸的 PNG 字节（D-6）：首次 PNG 编码不再落在主线程的保存快照
  或用户按住鼠标拖出的那一瞬间。
- 设置侧栏不再混用实心与描线符号（D-8）：`sparkles` → `wand.and.stars`。

- **右键菜单未汉化且含无关系统项**（issue #13）：搜索框（编辑态与非编辑态）现在弹
  `撤销 / 重做 / 剪切 / 复制 / 粘贴 / 全选`，详情只读区弹 `复制 / 全选 / 查找…`，每一项都是中文，
  不再出现快速查看附件 / 字体 / 书写方向 / 布局方向 / 服务 / 查询 / Show All Tabs 这类系统注入项。
  编辑态的右键原本落在**窗口共享的 field editor** 上（改它的 `menu` 会被 AppKit 复原），
  现在由 `FieldEditorRightClickInterceptor` 在派发前截走；只认领我们自己的搜索框，别的控件不受影响。
  屏幕上的观感仍需人眼核对：`docs/MANUAL_TEST_v1.4.8_issue13.md`。

### Changed

- **侧栏不再能收起**（用户提出，见账本 D-054）：像系统设置那样永远显示。工具栏那颗
  「显示/隐藏侧栏」按钮与菜单命令本来就已经摘掉，但**拖分隔条**这条路谁都不管 ——
  上一条缺陷就是从这条路走出来的。现在窗口配置器把侧栏那一列钉成不可折叠
  （`NSSplitViewItem.canCollapse = false`），分隔条最多拖到该列的最小宽度（250pt）就停住；
  已经是折叠状态的（旧版本留下的列可见性存档）当场展开，否则"以后不能再收、这次还是空的"。
  详情头部那条让位补丁保留：它同时把正文挡在标题栏拖拽区之外，属于防御纵深。
  实现上有个坑值得记：真窗口是 `NSHostingView` 直接摆进 `contentView` 的，
  `window.contentViewController` **是 nil**，所以顺着控制器树找分栏器在生产里永远空跑 ——
  必须走视图树（`NSSplitView` 的 `delegate` 就是那个 `NavigationSplitViewController`）。
- CI 的两个报告型步骤（帧捕获 / 在屏探针）现在**必然打印数字**：第三步坏了三次，两次坏在
  **汇报行自己**身上 —— ① 抽取 `Executed N tests` 的 `grep` 在 runner 上匹配不到单数
  `Executed 1 test`，非零 + `pipefail` + `bash -e` 让脚本在 echo 之前中止；② 看门狗子进程执行完
  `kill` 就退出，脚本随后 `kill "$killer"` 拿到 "No such process"（返回 1）同样中止
  （`2>/dev/null` 只闭嘴不改退出码）。见账本 D-037。修法是抽取与清理动作全部自带兜底，
  并新增 `scripts/tests/test_ci_report_selftest.py`：把这两个步骤的脚本原文抽出来、
  喂 5 种日志形状（单数汇总 / 截断 / 正常复数 / 帧目录不存在 / 看门狗已退出）验证结论行必然打印，
  它随 CI 的 `unittest discover` 真的执行，变异对照已点亮。
- CI 新增一个报告型步骤，真的执行在屏交互探针与帧捕获并打印执行数/帧数（D-7，`continue-on-error` 起步）。
- 视觉基线重拍：`sidebar-*`/`row-*` 帧因系统列表 chrome 发生变化；离屏帧里 `List` 的选中高亮会画成整块黑
  （语义色伪影，跟随选中集合），不作为产品判据。

## [v1.4.8] - 2026-10-10

### Added

- **行内直接操作**：双击列表条目 = 复制这一条（与详情区浮层「再次复制」同一个动作，会把这条顶到最前）；
  行首星标 = 一键收藏/取消。带 shift / command 的双击不复制（那两个键是范围选择/多选的前缀）。
  星标做成行的**兄弟控件**而不是嵌在行按钮里，实测点它只翻收藏、不改变选中集合。
- **拖拽双向**：条目可拖出（文本 / PNG / 单个文件引用，`EntryDrag`）；文件可拖入列表入库
  （`DroppedFileImport`，多个文件记成一条 `.files`）。落点刻意只在列表区域，不抢详情文本视图的文字拖放。
- 只含非文件 `NSURL`（网页链接）的剪贴板现在记成文本条目，不再静默丢弃。
- 离屏视觉夹具新增菜单栏面板三个状态与行内星标两态：帧数 58 → 68。

### Changed

- 行首星标从"未收藏即 `.clear`（不可见）"变成真控件：未收藏 `primary.opacity(0.55)`
  （实测对比度 3.54:1 亮 / 4.64:1 暗），已收藏压深成琥珀 `(0.86,0.45,0)`（3.90:1 / 4.28:1）。
  行内星标与浮层共用 `FavoriteTogglePresentation`，并有源码扫描禁止两处各写字面量。
- 左侧列表支持方向键移动选择（`SidebarKeyboardNavigation`）+ `ScrollViewReader` 滚动到选中项；
  macOS 14+ 抑制列表容器的系统焦点环（12/13 无对应 API，仍会出现，已在守卫里注明）。
- 菜单栏面板区分「正在整理推荐…」与「暂无推荐」（`isRefreshingPredictions`）——
  菜单同步构建而预测异步计算，把"还不知道"说成"没有"是本轮自己引入又修掉的误导。
- 亮色 chrome：9 处 `.white.opacity` 换成 `.separator` / `.quaternary` / `primary.opacity`；
  破坏性确认框 Return 改为「取消」，破坏性按钮标 `hasDestructiveAction` 且不带快捷键。
- 详情预览加 8 秒兜底（`PreviewLoadTimeoutPolicy`）；系统「减少动态效果」接入筛选 pill 动画与悬停放大。
- 推荐理由不再一行里把来源 App 说两遍；隐私页文案披露"来源 App 名称"及其用途。

### Fixed

- **启动闪退（S1）**：D-019 给 `AppDelegate` 加 `init(historyStore:)` 后，ObjC 的 `-init` 只剩编译器留下的
  trap 桩，而 SwiftUI 的 `@NSApplicationDelegateAdaptor` 正是通过它构造 delegate ⇒ 新包一打开就
  `EXC_BREAKPOINT`。补 `override convenience init()`。328 个用例与 CI 全绿都看不见它
  （Swift 侧 `AppDelegate()` 解析到带默认参数的那个 init），线上 v1.4.7 不受影响。
- 存档含同 id 两条时，预测管线 `Dictionary(uniqueKeysWithValues:)` 触发 fatalError：改为保留首条，
  并补一条走 `HistoryStore` 全链路的端到端守卫。
- 快捷键录制成功后按钮仍显示「请输入快捷键」（`shortcut.didSet` 在录制态跳过回显，之后再没人改）：录完立刻回显。
- 保存不再重写未变更的图片文件、被取代的落盘任务会取消；`load()` 不再遗留只读标志。
- 超长文本的字符统计改为有界计数；图片入库按 4096px 上限降采样（4K 及以下逐字节不变）。
- 来源 App 归属（`sourceAppBundleID` / `sourceAppName`）落盘并在重启后恢复；schema 仍 v1，字段可选。
- 字号/图标可达性若干：行时间戳与菜单理由行 10pt → 11pt、非法 SF Symbol `"questionable"` → `questionmark.circle`、
  缩略图与图片预览补无障碍名称。

### Build / Release

- **发布链路新增启动闸门**（`scripts/prepare_release.py`）：反汇编包内二进制，若 `AppDelegate` 还留着
  「未实现初始化器」桩就拒绝发布。arm64 上类名字面量离调用点二十几行，所以按桩块扫描而不是固定窗口回看。
- AI 草案代码移出产品 target（`ClipboardHistoryDesignDrafts` + `ClipboardHistoryIntelligenceCore`），
  `nm` 证明草案符号在产品二进制里为 0；本地网络守卫的扫描根收窄到产品目录。
- 测试判据不再依赖机器负载：性能守卫改为"N 次同操作采样取最快 + 样本跨度超阈值才 skip"，阈值未动。

### Tests

- Swift 单元测试 328 例 / 9 跳过 / 0 失败；发布脚本测试 30 例通过；`swift build` 0 告警。
- 在屏交互探针（`CLIPBOARD_HISTORY_UI_INTERACTION=1`）：合成真实鼠标事件，在**完整侧栏容器**里验证
  单击选中 / 双击恰好复制一次 / 点星标不动选中；焦点环以视图树清点为判据（截图那条路不可信）。
- 每条新守卫都做过变异对照（含"删掉调用点 ⇒ 恰好那条红"），源码按 sha 逐字节还原。

### Release

- DMG：`releases/时间剪史_v1.4.8.dmg`
- SHA256：`c31a16e0c144d71063e522f980a25c5cad17409d08a2ab09bac5451a6997e88d`

## [v1.4.7] - 2026-10-09

### Fixed

- **卷根目录下的文件不再把父目录标签渲染成 `…/..`**：`URL.parentDirectoryLabel` 先 `standardizedFileURL`
  再取目录名，并在守卫里补上 `..`。旧实现在部分 Foundation 版本上（CI 的 macOS 15 / Swift 6.1.2）会把
  `/a.txt` 的父路径算成 `/..`；macOS 26/27 上原本显示正确，所以本版是补严谨而非救急。

### Tests

- 测试不再覆写 XCTest 的 `tearDown()`：原 `try await super.tearDown()` 在 CI 的 Swift 6.1.2 下被判
  「sending value of non-Sendable type 'XCTestCase' risks causing data races」，整个测试 target 编译失败；
  改为每条用例开头复位偏好设置，用例顺序无关。
- 父目录标签补两条断言：`/a.txt → …`、`/Applications/X.app → …/Applications`。
- 发布脚本环境加一条断言：交给子进程的 `SDKROOT` 必须等于 `xcrun` 解析出来的那个。

### Release

- DMG：`releases/时间剪史_v1.4.7.dmg`
- SHA256：`5046475defcf6f25b829bd872595475b93cfda7e832cdcb0a78e13db499073a2`

## [v1.4.6] - 2026-10-09

### Added

- **设置 → 隐私「数据与保留」分组**：保存位置、保存内容类型、500 条 / 30 天、收藏长期保留、清空历史语义、敏感内容提醒 —— 这些文案此前只存在于代码里，产品从未显示（对应 #16）。
- **窗口顶部提示条**：存档恢复结果、自动粘贴失败原因、成批清理过期记录三类事件第一次变得可见（对应 #5）。
- **CI workflow**：构建零告警 + `Executed N tests` 只准涨不准跌 + 发布脚本测试 + Info.plist 闸。已在 main 上跑通（首跑抓到两条只在 CI 工具链下暴露的缺陷，见下）。
- **无障碍**：纯图标按钮在悬停提示之外补上 `accessibilityLabel`，并加静态守卫防止回归。
- **系统「减弱动态效果」**：展开 / 收起与缩放改为尊重该设置；0.11–0.14s 的颜色渐变有意保留。

### Changed

- **主线程热点（实测）**：保存一条记录 667.8ms → 约 5ms；启动载入 413.9ms → 3ms；复制一张 3000×2000 图片时 `add()` 94ms → 0.04–0.77ms；图片去重比较 434ms → 147ms；列表派生 14.07ms/次 → 0.00ms/次；2.4MB 文本预览 45.8ms → 0.02ms。
- **推荐预测由 2 秒轮询改为事件驱动**（新复制 / 打开菜单 / 前台切换），并加代际防护丢弃过期结果。
- **OCR 的像素解码移出主线程**，改用 ImageIO 直接解出有界尺寸的一帧，串行后台队列执行；OCR 日志只记长度不记内容。
- **`Info.plist` 由模板 + 脚本生成并逐键校验**，缺任一必需键即构建失败（此前是 20 行 `PlistBuddy` 且每行 `|| true`）；新增 `NSAppleEventsUsageDescription`、`CFBundlePackageType`、`NSPrincipalClass`。
- **`make dmg` 同时产出 `.sha256` 并自校验**；`make build` 在 SwiftPM 构建库被半删除时给出可执行的恢复提示。
- **README 与 20+ 处文档更正**：删掉「点击推荐不会粘贴」「侧边栏 Magic」「菜单里有刷新历史」等与代码相反的承诺；带日期的旧文档统一加「历史快照」横幅。

### Fixed

- **存档损坏不再连带删库**：先保全 `history.corrupt-<时间>.json`（不删原件）再从滚动备份恢复，两条路都失败时仍保住被引用的图片文件。
- **菜单栏「清空未收藏」补上二次确认**（此前带弹窗的函数没有任何调用者）。
- **同 bundle 的第二份进程不再并存**：两份会各自整库写存档、后写的整片盖掉先写的记录。
- **降级不再毁数据**：读到更高 `version` 的存档改为只读打开并说明原因（`version` 字段此前只写不读）。
- **自动粘贴失败不再静默**：`osascript` 的退出码与 stderr 现在翻译成可执行指引并显示出来。
- **浏览器链接不再被当成本地文件条目**；重复复制不再丢失来源 App 归因。
- **推荐排序确定化**：同一份历史在两次启动之间不再给出不同结果；同一条记录不再占两个推荐名额。
- **敏感内容误判收紧**（前缀需紧跟 ≥12 位 `[A-Z0-9]`）；反馈载荷不再保存剪贴板原文且随删除 / 清空级联清理；导出失败不再假装成功。
- **界面**：设置侧栏未选中行图标恢复可见；破坏性「清空」按钮不再在两个分类各放一份；5 处信息文字对比度暗色 2.22:1 → 5.79:1、亮色 1.89:1 → 3.98:1。
- **CI 首跑抓到的两条本机看不出的缺陷**（runner 是 Swift 6.1.2，开发机是 6.2.1）：`HotKeySettingsTests` 覆写的 `tearDown() async throws` 在 runner 上因 `await super.tearDown()` 被判并发错误、整个测试 target 编译不过（改为用例内复位，不再依赖 XCTest 生命周期签名）；`URL.parentDirectoryLabel` 对根目录下的文件返回 `…/..`（先 `standardizedFileURL` 再取名字）。
- **视频宽高未知时显示错误态而非 16:9 空播放器**；播放器 KVO 观察者在 `deinit` 释放；侧栏拖选的行位置表不再只增不减。

### Tests

- `swift test` 229 例（1 例按设计 skip）、0 失败，连跑 6 次一致；清空 `.build` 后干净重建 0 编译告警。
- 发布脚本测试 18 例通过；修复了 `prepare_release.py` 在本机必然失败的环境缺陷（`/usr/bin/python3` 给子进程注入 CommandLineTools 的 `SDKROOT`，而编译器来自 Xcode）。
- 修掉一条恒绿的假基准（计时对象是构造而非行为），并修正一处过紧的性能界值导致的偶发红。

### Release

- DMG：`releases/时间剪史_v1.4.6.dmg`
- SHA256：`9ed54be3144d5f5bc3f0751f7f8846dcfe8886d39fddae85ea65c69715bf2837`

## [v1.4] - 2026-06-11

### Added

- **OCR 图片文字搜索**：基于 Vision 框架对图片内容进行 OCR 识别，识别结果持久化并与原图关联，支持搜索图片内的中文、英文和数字文字。
- **智能推荐引擎**：基于规则的多因子加权推荐系统（`RuleBasedRecommendationEngine`），综合近因、频率、内容匹配、上下文相似度等 9 项因子打分排序。
- **菜单栏推荐面板**（macOS 13+ 用 `MenuBarExtra`，macOS 12 走 `NSStatusItem` 菜单，两条入口都有 Top 3）：点击右上角标签菜单展开推荐列表，显示 Top 3 推荐粘贴条目，支持一键粘贴到当前前台应用。
- **推荐反馈系统**（7 项）：
  - 隐私过滤器：自动排除含 GitHub Token、API Key、信用卡号等敏感内容的条目。
  - 「都不是我想要的」按钮：一键记录本次全部推荐为无效反馈，降低对应条目权重。
  - 显露偏好追踪：推荐展示后 30 秒窗口内监听手动复制，捕获未被点击采纳但实际需要的条目。
  - 反馈回流引擎：负面反馈含 24 小时时间衰减，高频拒绝条目快速降分。
  - 序列模式追踪：记录最近 20 次复制 ID 序列，为序列模式推荐奠定基础。（后续版本已移除该字段，当前 `Sources/` 内 `copySequence` 无命中）
  - 频率×新鲜度混合排序：采纳次数/年龄^1.5 融入 recency 评分。
  - 反馈数据 JSONL 导出：设置 → 推荐 → 导出数据，供分析和调优。
- **推荐权重客制化**：设置页新增「推荐」栏目，用户可独立调节 9 项因子权重（0%-200%），含恢复默认按钮，修改后实时生效。
- **Finder 上下文采集**（设置→隐私，默认关闭）：
  - Finder 当前目录：同目录条目获得加分。
  - Finder 选中文件扩展名：同扩展名条目获得加分。
- **设置页面重构**：改为左侧边栏 + 右侧主栏布局（快捷键 / 通用 / 隐私 / 推荐 / 数据），支持点击整行切换栏目，hover 动效与主窗口边栏统一。
- **全部/收藏切换药丸动效**：按 Apple 原生滑块动效样式做左右非线性速度曲线且带轻微过冲形变的移动切换。
- **右键菜单汉化**：搜索框和文本预览的右键菜单完成汉化，移除无关系统项。
- **搜索框 hover 动效**：鼠标经过搜索框时视觉高亮。
- **文件名扩展名始终显示**：长文件名省略中间部分，扩展名始终保持可见。

### Changed

- **粘贴机制重写**：`CGEvent.postToPid`（macOS 15 已失效）→ `Process` + `osascript` 执行 `keystroke "v" using command down`，确保跨应用粘贴可靠。
- **主菜单彻底本地化**：移除 `MainMenuController`（旧 AppKit 主菜单覆盖方案），全面采用 SwiftUI `.commands` + `ClipboardHistoryCommands`，配合 `Info.plist` 设置 `CFBundleDevelopmentRegion=zh-Hans`，系统菜单从源头本地化。
- **边栏列表 hover 动效**：改为接近 Apple 原生列表风格的 hover 高亮方式。
- **边栏时间显示**：从精确到秒改为 HH:mm 时刻格式，取消每秒刷新，消除列表跳动。
- **历史条目日期显示**：边栏时间前增加日期，按「6月7日 14:23」格式展示。
- **版本号体系**：从 v1.3 经 v1.4beta → v1.4.4，Makefile VERSION 同步更新。
- **菜单栏「刷新历史」移除**：减少无用菜单项。
- **菜单文案优化**：「设置…」→「设置」，「清空未收藏…」→「清空未收藏」。
- **搜索框省略号**：从「搜索历史…」改为中文正确省略号「搜索历史……」。
- **项目结构扩展**：新增 `Intelligence/` 目录（10+ 文件），新增 `Views/MenuBarRecommendationsView.swift`、`Views/RecommendationWeightsView.swift`、`Views/ChineseTextContextMenu.swift`、`Managers/ClipboardHistoryCommands.swift`。
- **启动性能**：生命周期调试日志默认关闭，仅 `CLIPBOARD_HISTORY_DEBUG=1` 环境变量启用。
- **首次复制捕获保障**：窗口显示后延迟 0.3-0.5 秒启动剪贴板监听，不影响首次复制被捕获。

### Fixed

- **推荐项点击无法粘贴**：根因为 `/tmp` 启动路径导致 macOS 拒绝授予辅助功能权限，`AXIsProcessTrusted()=false`。改为从项目固定路径启动 + `Process` + `osascript` 方案彻底解决。
- **OCR 对 Finder PNG 文件无效**：`ClipboardIntake` 将 `file-url` 优先归类为 `.file(url)`，OCR 跳过该分支。修复：`scheduleOCRIfNeeded` 新增 `.file(url)` case，判断图片扩展名后从磁盘加载 NSImage 执行 OCR。
- **中文输入法搜索丢失文本**：`controlTextDidChange` 在 markedRange 清除前触发导致组字未完成即推送。修复：`controlTextDidEndEditing` 兜底推送。
- **QuickLook 频繁崩溃**（`QLPreviewView setPreviewItem: item == nil || internalState != QLPreviewDeactivatedInternalState`）：用 generation token 取消过期加载，脱离窗口时释放旧 `QLPreviewView`，仅在 view 已挂窗口时按需创建。
- **双窗口问题**：关闭主窗口后 `showMainWindow` 误判创建 fallback AppKit 窗口，SwiftUI 原窗口恢复后形成双窗口。修复：删除 fallback 主窗口创建路径，`WindowManager` 仅显示已有 SwiftUI 主窗口。
- **macOS 12 菜单栏图标透明**：`NSStatusItem` 模板图像渲染配置修正。
- **macOS 12 关闭窗口后 Dock 图标无法恢复**：`applicationShouldHandleReopen` 未被正确触发，窗口关闭语义调整。
- **菜单栏菜单反复横跳**：SwiftUI 默认菜单与旧 `MainMenuController` 争夺 `NSApplication.shared.mainMenu`。修复：删除 `MainMenuController`，全面使用 SwiftUI `.commands`。
- **搜索框输入失效**：删除自定义 `NSTextFieldCell` 和复用 field editor 方案，回到标准 `NSTextField` 编辑路径。
- **全部/收藏切换需精确点击文字**：改为点击半按钮区域即可切换。
- **设置页边栏需精确点击文字**：改为点击整个 hover 高亮范围即可切换栏目。
- **菜单栏「推荐」项跳转到应用而非直接粘贴**：修复为直接粘贴到当前前台应用。
- **推荐匹配率不随前台 App 切换更新**：修正推荐列表更新触发逻辑。

### Release

- DMG：`时间剪史_v1.4.4.dmg`（该产物未留在仓库里，仓库只有 v1.4.5 的 DMG）
- 构建：`swift build` ✅（当时 116 个测试全绿；执行数以当次 `swift test` 输出为准）
- 签名：ad-hoc 签名（未 notarize）
- 兼容：macOS 12+ / Intel + Apple Silicon

## [v1.3] - 2026-06-09

### Added

- 新增历史持久化，文本、图片、文件引用和缩略图可在重启后恢复。
- 新增收藏功能，收藏项可在侧边栏筛选和菜单栏收藏区快速使用。
- 新增开机启动设置，支持在系统允许时从设置窗口开启或关闭。
- 新增菜单栏入口，可显示主窗口、打开设置、刷新历史、清空历史和退出应用。
- 新增“再次复制”全局快捷键，默认 `⌃⌥C` 复制当前选中记录，并支持在设置中自定义和恢复默认。
- 新增发布流程文档，说明本地发版、校验和人工检查步骤。

### Changed

- 历史保留策略改为普通记录默认 500 条 / 30 天，收藏项不受自动清理影响。
- 清空历史改为只清空未收藏记录，收藏记录会保留。
- 视频文件预览改用原生播放器，默认静音自动播放。
- 视频控制条改为保留右下角操作区空间，避免宽视频控件被收藏/复制/删除按钮遮挡。
- 主窗口改为固定边栏布局，移除边栏折叠入口。
- 发布脚本默认先运行自动测试，构建后校验 App `Info.plist` 版本号。
- README 更新为 v1.3 持久化版本的实际能力和数据保存说明。

### Fixed

- 修复同一张图片隔多条记录后再次复制仍生成重复历史的问题。
- 修复视频预览控件需要折叠/展开边栏后才容易出现的问题。
- 修复关闭主窗口后视频仍继续播放的问题。
- 修复竖屏视频下方播放控件缺少进度条调节能力的问题。
- 修复边栏折叠按钮在重新打开窗口后又出现的问题。
- 测试环境改用内存存储，避免单元测试读取或污染本机真实历史记录。
- 持久化启动加载只读取一次历史文件，减少不必要磁盘读取。
- 统一左侧清空按钮和右侧悬浮操作按钮的玻璃样式与 hover 动效。

### Release

- DMG：`releases/时间剪史_v1.3.dmg`
- SHA256：`8a59d872cdccfe4caa334c055c1bf92a62facb7fa36d148345e5abfb8c095538`

## [v1.2.2beta] - 2026-06-08

### Added

- 新增设置窗口，可修改和恢复呼出主窗口的全局快捷键。
- 新增快捷键录制控件，支持在设置中直接录入组合快捷键。
- 新增本轮架构重构总结文档，记录五个模块深化点和验证结果。

### Changed

- 深化剪贴板输入模块，将轮询、解析、缩略图生成、来源 UTI 和相邻去重集中到 `ClipboardIntake`。
- 深化文件预览模块，将文件类型判断、文本读取、QuickLook 与 fallback 预览集中到 `FilePreview`。
- 深化应用外壳模块，将应用生命周期意图、主菜单、菜单栏、设置窗口和窗口恢复逻辑从 `AppDelegate` 中拆分。
- 深化快捷键配置模块，将偏好保存、Carbon 注册、失败回滚和错误提示集中管理。
- 将条目展示文案、文件名、大小和预览文本集中到 `EntryPresentation`，减少视图中的格式化逻辑。
- 更新 Release / 仓库整理文档，继续保持 DMG、App bundle 和分析产物不进入源码提交。

### Fixed

- 改善文件、图片和文本预览路径的一致性，减少视图层直接做磁盘读取的情况。
- 改善关闭窗口后的快捷键呼出路径，快捷键注册失败时会回滚到上一个可用配置。

## [v1.2.1] - 2026-06-06

### Added

- 菜单栏模式，支持显示主窗口、刷新历史、清空历史和退出应用。
- 视频文件预览，常见视频文件可通过 QuickLook 在详情区查看。
- 视频缩略图，Finder 复制视频文件时显示首帧缩略图。
- 标签/语义分类基础，区分文本、图片内容和文件引用。
- macOS 12 支持完善，补齐 `NavigationView` 与 `NSStatusItem` 兼容路径。

### Fixed

- 修复搜索无结果时错误显示“暂无剪贴板历史”的问题。
- 修复边栏时间精确到秒导致列表频繁跳动的问题。
- 修复边栏标题“时间剪史”在窄宽度下换行的问题。
- 完善关于窗口内容，补充版本、作者、GitHub、License 和项目简介。
- 优化按钮 Hover 动效，减少不一致和溢出感。
- 统一图片、视频、文件缩略图样式。
- 修复 macOS 12 关闭窗口后 Dock 图标无法重新打开主窗口的问题。
- 修复 macOS 12 菜单栏图标透明问题。
- 修复打包流程中的签名与扩展属性问题，降低“损坏无法打开”的概率。

### Changed

- 项目架构整理，将源码按 `Managers`、`Models`、`Utilities`、`Views` 分组。
- 拆分 `ContentView`、`ClipboardManager` 等核心文件，降低单文件职责复杂度。
- 生命周期管理优化，集中主窗口显示和恢复逻辑。
- 启动性能优化，默认关闭生命周期日志并延迟启动剪贴板监听。
- 打包流程优化，生成 Intel + Apple Silicon 通用 App。

## [v1.1] - 2026-06-06

### Added

- macOS 12+ 兼容构建。
- 常见文件格式预览。

### Fixed

- 移除调试绿框。
- 修正 Dock 图标尺寸。

## [v1.0] - 2026-06-05

### Added

- 初始版本。
- 剪贴板文本、图片和文件历史记录。
- SwiftUI 主窗口界面。
- DMG 打包流程。

### Changed（R30 · 侧栏暗档黑字的机制量到了，盲区名单改由前提决定）

- **产品代码零改动**。`render` 新增 `inspect:` 钩子（默认空实现），把"已布局、未开画"的
  AppKit 树交给诊断：设置页侧栏列的 `NSHostingView` 生效外观是
  **`NSAppearanceNameVibrantDark`**，内容区是 `DarkAqua` ⇒ 同一张帧里两种极性。
- **盲区名单不再手钉**：`darkSidebarTextBlindSpots` 必须等于"侧栏在 vibrant 子树下"的帧集合，
  且"读到反侧墨 ⇒ 必须也在 vibrant 子树里"。想给那一列钉外观把帧调好看，会当场红（U-53 / D-090）。
- 新增一条**永远记 skip 的诊断**：`testSettingsSidebarSubtreeWhoDrawsTheColumnDiagnostic`。
- 变异 **M132–M136 五支全 CAUGHT**（含两支专打新前提：塞一条非 vibrant 帧 / 让 vibrant 探针失明）。

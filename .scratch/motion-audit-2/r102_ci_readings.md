# R102 的 CI 读数（run `38958447236`，sha `3fac5fa`，**failure**）

读法：`python3 scripts/ci_read.py readings 38958447236 CARD_PROBE_ARM CARD_STATS_ CARD_INSET_CAPABILITY CARD_FILL_CANDIDATES`
（R102 落盘的那把工具；解析出 4998 行、丢掉 0 行；**按步骤分组**，同一 marker 在两个步骤各打一遍）。

## ① 红了哪些步骤
| 步骤 | 结论 |
|---|---|
| 13 Swift tests (executed-count gate) | failure |
| 14 Capture gate (unregistered reds must be zero) | failure |
| 16 Motion coverage floor | failure |

断言原文去重后 6 条：**4 条是本轮新装的"证人"守卫**（下面 ③），1 条是 ④ 的运动地板，1 条是它的登记行。

## ② 150 的答案：**部分拿到了，而且是被证人拦着拿到的**
```
CARD_PROBE_ARM cardprobe-groupbox-default light 材质=有 卡片段=1 墨行=11 带子=24..696pt 页底=236 前三=(236:74) (228:24) (220:2)
CARD_PROBE_ARM cardprobe-scroll-groupbox    light 材质=有 卡片段=1 墨行=11 带子=24..696pt 页底=236 前三=(236:74) (228:24) (220:2)
CARD_PROBE_ARM cardprobe-split-groupbox     light 材质=无 卡片段=-1 墨行=0  带子=150..720pt 页底=236 前三=(236:100)
CARD_PROBE_ARM cardprobe-groupbox-default dark  材质=有 卡片段=0 墨行=0  带子=24..696pt 页底=52 前三=(52:74) (60:24) (84:2)
CARD_PROBE_ARM cardprobe-scroll-groupbox    dark  材质=有 卡片段=0 墨行=0  带子=24..696pt 页底=52 前三=(52:74) (60:24) (84:2)
CARD_PROBE_ARM cardprobe-split-groupbox     dark  材质=无 卡片段=-1 墨行=0  带子=150..720pt 页底=52 前三=(52:100)
```
按 D-167 的读法逐条判：
- **亮档**：臂 0、臂 1 `材质=有 墨行=11`（证人活着）⇒ 它们的"有材质"是答案；
  臂 2 `材质=无` 但同时 **`墨行=0`** ⇒ 按规矩**这一格不是答案**，是仪器（带子没盖住内容）。
  ⇒ 亮档能说的是：**"滚动容器"这一层不杀材质**（臂 1 与臂 0 同读数）。
- **暗档**：三臂全部 `墨行=0` ⇒ **暗档整条梯子今天无从判定**（连臂 0 在自己机器上明明有材质，
  却读不到墨 ⇒ 说明坏的是"墨"这把证人，不是容器）。
- 被告那一侧：`CARD_INSET_CAPABILITY 候选=30 有材质=4（被告=0 参照=4）量到=0 未判=28`
  ⇒ **runner 上 24 格被告全部没有材质**，147 的定性照旧成立。

## ③ 本轮装的守卫**按设计响了**（这是这次 run 最值钱的一格）
```
XCTAssertGreaterThan failed: ("0") is not greater than ("0") -
  参照臂 cardprobe-groupbox-default dark 在带子 24..696pt × 24..124pt 里读到 0 行墨
  ⇒ 这一臂的扫描带没盖住它自己的内容，它的「材质=无」不能当结论。改带子（`cardprobeBands`），不要改这条断言。
```
四朵（暗档三臂 + 亮档臂 2）。**没有一朵在改产品，也没有一朵在改这条断言** ——
D-167 的证人把"我框错了"与"容器杀掉了材质"分开了，而它自己红在最该红的地方：
如果本轮没配这个证人，②那六行会被读成"runner 上连独立窗口的 GroupBox 在暗档也没有材质"，
一条**假答案**，且比 147 更难发现。

## ④ 另一条红：运动地板（与本轮无关，但要点名）
```
testBandCaptureIsCheaperAndStillSeesTheMotion: XCTAssertLessThanOrEqual failed:
  ("32.19") is greater than ("23.48") - 带捕获之后整卷中位间隔没有变细 ⇒ 省下的钱没进采样率，这一臂仍然判不了
```
⇒ 这是 R57（BACKLOG 77 路 a）那条"省下的抓帧成本必须进采样率"的判据在 runner 上翻脸，
**本轮不动它**，登记成 R103 的第二格（要按 147/146 那一族的做法：先问它在 runner 上到底为什么）。

## ⑤ D-166 的 runner 验收：**通过**
`CARD_STATS_DECLINED` 四格 × 两个步骤各打一遍（共 8 行），内容都是
"原因=读不到被告材质 ⇒ 这一格不判（不是通过）"，而 R101 那四朵 `testSettingsCardVerticalRhythmIsOneNumber`
**没有再红** ⇒ "没有对象"这一格现在响成 skip + 有名字的未判，而不是红，也不是静默通过。

## ⑥ R103 的入口（由这次读数直接决定，不是排期）
1. **先修证人**：暗档三臂 `墨行=0` 说明"墨"的判据（**按行众数**与页面底比）在这台机器上看不见文字
   —— 前三里 84 那一档只有 2 行，文字根本没成为众数。要换成**存在性**判据
   （一行里只要有 ≥N 个像素同时远离页面底与卡片填充就算有墨），并给它自己的正/负对照
   （正：本机已知有墨的帧；负：纯色帧必须报 0 并且让守卫红）。
2. 证人修好之后重跑一次 CI，**150 才算有答案**（亮档臂 2 也要一起：它的带子 150..720 在 runner 上同样读不到墨）。
3. ④ 那条运动地板单独开一格（不在证人这一支里混做）。
4. BACKLOG 148 往后挪一轮：R103 的开场读数已经落盘在 `r103_opening_readings.md`，不会丢。

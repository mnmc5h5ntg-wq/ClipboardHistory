# R97 读 R96 的 CI（run 38884429809 / commit `278415e`）

作业结论读的是 `conclusion`：**success**（不是猜的，`gh run view --json status,conclusion`）。

## 1. 132 的答案终于来了，而且是**真的读到了**

```
UI_PROBE_HUNG=testRightClickMenusAppKitWouldShowAreChinese
UI_PROBE_HUNG_CHANNEL=pulse
UI_PROBE_SAMPLE 主线程采样=314 等待帧占比=100% 主导路径占比=100% 等待终端=1 个
UI_PROBE_SAMPLE_WAITING=mach_msg2_trap  (in libsystem_kernel.dylib) + 8  [0x18bf91c34](314)
UI_PROBE_HUNG_KIND=blocked@runloop-wait ⇒ 100% 的采样都停在同一族的等待帧上（132 分诊：挂）
UI_PROBE_SAMPLE_EXIT=0
```

- 上一轮欠的那一行（`UI_PROBE_SAMPLE_SHAPE`）**没有出现** —— 因为它只在"读不懂这份文件"时才打。
  这一次 314 个采样全解析出来了，所以三种形状那三条下一步都不用走。
- 判据给的是 **`blocked@runloop-wait`**，不是上一轮那个我撤掉的 `blocked@unknown`：
  上一轮那句是"占比被兜底成 1.0 造出来的"，这一轮这句背后有 314 个采样、一个等待终端、
  一个族，而且 `等待帧占比` 与 `主导路径占比` 两把尺各自都到 100%（同一件事的两个量，不是同一个量的两次）。
- ⇒ **BACKLOG 132 结案**：那条在 runner 上吃满 240 秒的探针是**挂**（主线程整个停在
  `mach_msg2_trap` 等事件），不是慢。这一句现在才有资格说。

## 2. 覆盖率闸门与上一轮一致（没制造新的红）

```
PROBE_COVERAGE_SUMMARY 源码用例=11 登记=11 runner可跑=6 runner不可跑=5 本次下结论=6 红=0
  PROBE_ORDER 露面=7/11 未闭口=1 前缀=1
```

与 R95 那次（run 38876999489）逐格相同 ⇒ R96 只动了判据与工具，没动登记身份，这是它该有的样子。

## 3. 本轮（R97）拿这个答案去做的事

132 结案之外，这一轮的正文在**卡片那把尺**上：见 `AGENT_UI_AUDIT.md` 第 99 轮 /
`AGENT_VISUAL_ITERATION.md` Round 97。要点是三条本机读数：

- `settings-privacy-excluded` 亮档那条 `边距=14.5/8.0` 的**假红**（真值 14.0，独立复算与判据不一致）；
- 一颗 76pt 宽的按钮被当成一张 23.5pt 的"卡片"（`边距 6.5/5.5、内侧 0.0/0.0`）；
- 一个扫描带里其实有**两张**卡片，而判据把它们当一张量。

## 4. 一件没做完、必须记账的事（开成 BACKLOG 141）

判据读的是 `NSImage → tiffRepresentation → NSBitmapImageRep`，实测那份位图的色彩空间是
**`NSCalibratedRGBColorSpace`**（`CARD_LAYOUT` 那行），而落盘的 PNG 不是这个空间。
后果：同一张帧，Swift 这把尺与一份独立的 python 复算（直接读 PNG）在
`settings-privacy-excluded` 上给出不同的卡片边界——

| 段 | Swift（判据实际用的） | python 复算（读 PNG） |
|---|---|---|
| 段1 | 106.0..**705.5**pt（599.5pt） | 106.0..**765.5**pt（659.5pt） |
| 段2 | **720.0**..875.5pt（155.5pt） | **780.0**..935.5pt（155.5pt） |

顶边一致、段2 高度一致、段1 的底差 60pt —— 这不是噪声，是**边界判定的位置**在两条通道上不同。
而卡片材质与页面底在这台机器上只差 8 个单位（244 vs 252），一个色彩空间的偏移就是同一个量级。
⇒ 本轮那些"14.5/14.0 通过"的读数，在**高夹具**上要记成**暂定**：
判据自洽，但它量的那张图和交付的图不是同一份像素。修法与代价写在 141 里（要成对做 before/after，
因为仓库里十几支像素判据的阈值都是在这条通道上标定的）。

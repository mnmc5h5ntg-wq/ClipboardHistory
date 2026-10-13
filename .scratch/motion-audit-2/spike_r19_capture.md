# R19 spike · 浮层与材质到底能不能离屏拍到（仓库外，一次性）

代码注释里引的 `spike_r19_capture.md` 就是这个文件。三支可执行脚本已归档在本目录：`MaterialSpike.swift`、`QuickPickCaptureSpike.swift`、`KickSpike.swift`
（编译方式：`xcrun swiftc -O <file>.swift -o <bin> && ./<bin>`；它们不进仓库，
因为它们是**判据的证据**而不是判据本身 —— 判据在 `UICaptureHarness.swift` 里）。

## spike #1 `MaterialSpike.swift` —— 材质本身能不能离屏合成？

三条臂，每条量"未绘制比例 / 纯黑填充带 / 中心像素"：

```
A 未上屏:   transparent=0.0% blackBandPt=0 midPixel=(58,58,58,a=255)
A 上屏后:   transparent=0.0% blackBandPt=0 midPixel=(58,58,58,a=255)
B 选中行(上屏后): transparent=86.8% blackBandPt=0 midPixel=(0,0,0,a=0)
C 未上屏:   transparent=0.0% blackBandPt=0 midPixel=(30,30,30,a=255)
C 上屏+key 后: transparent=0.0% blackBandPt=0 midPixel=(30,30,30,a=255)   C key=false active=false
```

**结论**：A 是裸 `NSVisualEffectView(material:.sidebar)` —— 它**没上屏也画得出来**。
所以 R18 那句"材质在离屏窗口里没有可合成层"直接被推翻。
C 是 SwiftUI `List`：上不上屏都画得出底，但 `key=false` ⇒ 选中态那档拿不到 emphasized。

## spike #2 `QuickPickCaptureSpike.swift` —— 复刻浮层那一棵树

照抄产品四个"不画底"的设置（`drawsBackground=false` / `backgroundColor=.clear` / 无边框 field），
逐步"踢"它：

```
1 只建好、什么都没踢:  opaque=0/504000   visibleRect 未成立
2 reloadData 之后:     opaque=0
3 布局之后:            opaque=0
4 tile 之后:           opaque=0
5 orderFront 到屏幕外 + 0.8s: opaque=11/504000   tableFrame={{0,0},{132,214}} rows=6 drawnRect={{0,0},{0,0}}
```

**结论**：`visibleRect` 是 0×0 ⇒ 表格不是"画不出"，是**没轮到它画**；
而这棵树的 `NSStackView` 从头到尾没拿到过宽度。

## spike #3 `KickSpike.swift` —— 三种踢法哪一种能让 NSTableView 出像素

```
A display():                       cacheDisplay opaque=12291  visibleRect={{0,-20},{396,276}}
B displayIgnoringOpacity:          opaque=12291
C 手工 frame + tile:               opaque=12291  visibleRect={{0,0},{396,276}}
C2 选中一行之后:                    opaque=61142  selected=2
D orderFront(nil) + tile:          opaque=12291   visible=true alpha=1.0 opaqueWindow=true
```

**结论**：`NSTableView` 这条路**可以**拍到，而且**选中行是实色填充**
（61142 − 12291 ≈ 4.9 万像素 ≈ 一行 396×34 的填充）。
⇒ 浮层拍不到的锅不在 AppKit 表格，在产品那棵树的 `NSStackView` 拿不到宽度。

## 回到仓库里量的一次（`UICaptureHarness` 的临时诊断）

```
CAPTURE_PROBE quickpick transparent=100.0% rows=5 stackWidth=24 dataSourceIsController=true bounds={{0,0},{420,300}}
DUMP NSView {{0,0},{420,300}}
DUMP   NSStackView {{0,0},{24,49}}
DUMP     QuickPickSearchField {{10,20},{4,17}}
DUMP     NSScrollView {{12,12},{0,0}}
DUMP       NSClipView {{0,0},{0,0}}
DUMP         NSTableView {{0,0},{132,180}} visibleRect={{0,0},{0,0}}
DUMP     NSTextField {{-2,33},{8,16}}
```

把"真实显示周期"整段加进去（`orderFrontRegardless` + runloop + 递归 `tile()` + `display()`）
**之后仍然如此**，而且 96 张 SwiftUI 帧的 `transparent` / `blackBandPt` 逐帧不变
⇒ 那段 kick 只对 AppKit 夹具保留（零 blast radius），而浮层仍然进不了帧基线。

## 这一串读数买到的三句话

1. R18 的根因**作废**（材质不是原因，浮层里没有材质）。
2. 真正的原因**有数字**：`NSStackView` 24pt 宽 ⇒ 滚动视图 0×0 ⇒ `visibleRect` 0×0。
3. 选中态那块黑**要的是 key window**，不是上屏 —— 而测试进程拿不到（拿到的代价是抢用户前台）。

判据因此写成三层，第三层专门在"原因又变了"的时候红。

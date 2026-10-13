# R31 spike · "合成后"的像素到底能不能在离屏测试里拍到（结论：结构上不能）

`composite_capture_r31.swift`。四臂：材质 `.sidebar` vs 纯色底（对照）× `cacheDisplay` 内层宿主 vs 整窗。

## 唯一一条能用的结论（与画没画出来无关）

```
C 窗口服务器取图：CGWindowListCreateImage 不可用（SDK 标记 unavailable，替代要录屏授权）
```

本机 SDK（macOS 15）把 `CGWindowListCreateImage` 标成 **unavailable**，编译期就拒绝，
替代是 ScreenCaptureKit —— 要录屏授权 + 窗口真上屏。
⇒ **测试进程里没有任何"走窗口服务器"的取图像路径**。
R30 的推论（vibrant 文字指望服务器合成翻回来，`cacheDisplay` 不走那一步）因此
**不可能被"再写一个捕获通道"解决**：能证的只剩真机截屏（人工批次 37.1 / 37.2）。

## 明确不算结果的部分

```
=== 材质 .sidebar   侧栏宿主生效外观=NSAppearanceNameVibrantDark
A cacheDisplay      400x600px 底=4 亮侧=0 暗侧=0 ⇒ 没有墨
B 整窗 cacheDisplay 400x600px 底=4 亮侧=0 暗侧=0 ⇒ 没有墨
=== 纯色底（对照）  ……同样"没有墨"
```

两臂连**纯色底**都没画出来（底=4 = 全黑），说明是这棵 spike 树自己没落笔
（`List` 装进裸 `NSHostingView` 再塞进手动建的容器，尺寸/布局周期没成立 —— 与 R19 spike #2
"表格不是画不出，是没轮到它画"同一族）。
⇒ **这四行不是"材质在离屏不合成"的证据，是"DID-NOT-RUN"**。
按仓库规矩（DID-NOT-RUN 不是结果），我没有据此下任何结论，也没有继续修这个 spike：
它剩下的那个子问题（材质底画没画、只有文字是合成前）不改变任何决定 ——
无论答案是哪边，能用的取证通道都只剩真机。

## 这条边界要挡住的动作（写进 BACKLOG 40 / 45）

以后凡是"再搭一个离屏捕获通道，把 vibrant/材质/prominent 填充拍出来"的提案，
先引用这一条：**没有这条路**。要么真机截屏，要么把它记成结构性盲区并让守卫知道。

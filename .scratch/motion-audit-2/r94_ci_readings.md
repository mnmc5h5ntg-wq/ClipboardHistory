# R94 的第一步：读 R92 推送的 CI（run 38857388449 / `8e6ed15`，同一内容的 `9c10569` 也对账）

读法：`gh run view 38857388449 --log` → `/tmp/r92_ci.log`。作业仍然 `failure`，但**红的已经不是那两道闸门**。

## 1. BACKLOG 128 的 runner 那一半：验收通过

```
CAPTURE_GATE_CHANNELS stdout=1 readings=404 行 补回=0 行（stdout 没有的读数）
CAPTURE_GATE_INPUT 日志通道=525 行/64905 字节 @ /tmp/frames.log（读数通道另计 0 行）
CAPTURE_GATE_CASES passed=38 skipped=9 failed=0 有名字的红=0 NOT_RUN=54
CAPTURE_GATE_RESULT=ok 红=0（已登记的 NOT-RUN 见上）
```

对照 R90/R91 那两次（`补回=402 行`、`passed=0`、`fail …这一步没跑到用例`）：
- `补回` 从 402 回到 **0** ⇒ 闸门读到了自己那一步留下的日志；
- `passed` 从 0 回到 **38**（与 R89 挪位置之前那次绿的读数 38 一模一样）；
- 新加的 `CAPTURE_GATE_INPUT` 第一次上 runner，报出 **525 行 / 64905 字节** ——
  这一行存在的理由就是"下一次别再让人去翻别的步骤才知道是不是通道坏了"。

在屏那一步（真读数，早于自检）：
```
ui suite exit: 137  executed: 0  skipped: ?  已下结论的用例: 6
UI_PROBE_PROGRESS started=7 concluded=6
UI_PROBE_CHANNELS pulse=7 started=7 concluded=6
UI_PROBE_CHANNELS_AGREE=1
```
⇒ 与 R91 那一次同形（僵尸已删），且**双通道继续互相签字**。

## 2. 现在唯一红的那一步，红在它一直想告诉我的那件事

```
PROBE_COVERAGE_SUMMARY 源码用例=10 登记=10 runner可跑=0 runner不可跑=10 本次下结论=6 红=6
  NOW_RUNS testAccessibilityTreeCoverage：登记说 runner 跑不了，而这次它下结论了（skipped）⇒ 把登记改成 can
  NOW_RUNS testFocusChainReachesTheSearchFieldAndNotOnlyTheDetailTextView：…（passed）
  NOW_RUNS testFrameIntervalsUnderStateChanges：…（passed）
  NOW_RUNS testIntakeBehindATallPinnedBlockRevealsTheNewRow：…（passed）
  NOW_RUNS testMarkdownFilePreviewRendersInARealWindow：…（passed）
  NOW_RUNS testOffScreenProgrammaticSelectionIsRevealedAndNotJumped：…（passed）
```

⇒ **BACKLOG 134 有答案了**：闸门逐条点出了那六条的名字与判定 ——
R93 之所以不翻，是因为"是哪六条"只有计数没有名字，而按字典序猜属于没量过的推断（U-217）。
现在名字是**读来的**，可以翻了。

一条意外收获：`testFrameIntervalsUnderStateChanges` 在 runner 上是 **passed** 而不是 skipped
⇒ `FRAME_CHANNEL` 在那台机器上拿到了非零的帧样本。R91 留的那格
（"runner 上是 n=0 还是有 tick"）就此有了答案：**有 tick**。
（本机 R91/R93 那一格是 skip —— 显示器睡着 ⇒ 0 个样本。两台机器在这一格上相反，
  所以这条判据的"没跑"与"跑过"要按机器分开记，不能拿一台的结论替另一台签字。）

## 3. 本轮翻完之后仍然会红的（有名字的，不是噪音）

- 4 条排在 `testRightClickMenus…` 之后的用例仍是 `cannot`，理由就是 132 那条：
  它在 runner 上开口没闭口（本机 2.016 秒跑完）⇒ 下一格是 `sample` 它，不是放宽看门狗。
- 捕获卷那 54 条 `*_NOT_RUN` 是 runner 那台机器的通道前提（settings 族整体画不出来，BACKLOG 43），
  闸门已经把它们与红分开了。

# R100 读到的 R99 CI（run 38913173905 / job 117013845909）原文摘录

取法：gh run view 38913173905 --log-failed / --log（本机 gh 已登录，读的是那一次 run，不是重跑）

```
build-and-test	Capture gate (unregistered reds must be zero)	2026-10-16T14:22:22.4437540Z CAPTURE_GATE_CASES passed=46 skipped=10 failed=1 有名字的红=1 NOT_RUN=88
build-and-test	Capture gate (unregistered reds must be zero)	2026-10-16T14:22:22.4577330Z CAPTURE_GATE_RESULT=fail 有 1 个用例红了（红有名字，这正是这一步存在的理由）：
build-and-test	Capture gate (unregistered reds must be zero)	2026-10-16T14:22:22.4578950Z     /Users/runner/work/ClipboardHistory/ClipboardHistory/ClipboardHistory/Tests/ClipboardHistoryAppTests/UICaptureHarness.swift:5974: error: -[ClipboardHistoryAppTests.UICaptureTests testSettingsCardVerticalRhy
build-and-test	Capture gate (unregistered reds must be zero)	2026-10-16T14:22:22.4580610Z     /Users/runner/work/ClipboardHistory/ClipboardHistory/ClipboardHistory/Tests/ClipboardHistoryAppTests/UICaptureHarness.swift:5977: error: -[ClipboardHistoryAppTests.UICaptureTests testSettingsCardVerticalRhy
build-and-test	Swift tests (executed-count gate)	2026-10-16T14:22:18.6815890Z CARD_ABOVE_SUMMARY 
build-and-test	Swift tests (executed-count gate)	2026-10-16T14:22:18.6816150Z CARD_BELOW_SUMMARY 
build-and-test	Swift tests (executed-count gate)	2026-10-16T14:22:18.6817350Z /Users/runner/work/ClipboardHistory/ClipboardHistory/ClipboardHistory/Tests/ClipboardHistoryAppTests/UICaptureHarness.swift:5974: error: -[ClipboardHistoryAppTests.UICaptureTests testSettingsCardVerticalRhythmIsOneNumber] 
build-and-test	Swift tests (executed-count gate)	2026-10-16T14:22:18.6819550Z /Users/runner/work/ClipboardHistory/ClipboardHistory/ClipboardHistory/Tests/ClipboardHistoryAppTests/UICaptureHarness.swift:5977: error: -[ClipboardHistoryAppTests.UICaptureTests testSettingsCardVerticalRhythmIsOneNumber] 
```

## runner 上那一族卡片判据的实际读数（本轮 147 的出处）

```
CARD_BAND settings-data dark 页底=52 填充=-1 墨行=0 卡片段=0 窗口高=540 带子=60..540 位图=720x540 行数=480 scale=1.0
CARD_BAND settings-data light 页底=236 填充=-1 墨行=0 卡片段=0 窗口高=540 带子=60..540 位图=720x540 行数=480 scale=1.0
CARD_BAND settings-general dark 页底=52 填充=-1 墨行=0 卡片段=0 窗口高=540 带子=60..540 位图=720x540 行数=480 scale=1.0
CARD_BAND settings-general light 页底=236 填充=-1 墨行=0 卡片段=0 窗口高=540 带子=60..540 位图=720x540 行数=480 scale=1.0
CARD_BAND settings-general-login-failed dark 页底=52 填充=-1 墨行=0 卡片段=0 窗口高=540 带子=60..540 位图=720x540 行数=480 scale=1.0
CARD_BAND settings-general-login-failed light 页底=236 填充=-1 墨行=0 卡片段=0 窗口高=540 带子=60..540 位图=720x540 行数=480 scale=1.0
```

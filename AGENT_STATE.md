# AGENT_STATE · 当前工作状态（自主修复引擎）

最后更新：2026-10-08 14:1x（本地）
分支：`fix/audit-remediation`（从 `main` @ `db077f6` "Prepare v1.3 release" 切出）
回滚基线：提交 `8007b19` "Checkpoint: 1.4.5 working state before audit remediation" —— 修复前工作区的全部 WIP（含此前未被 git 跟踪的 `Intelligence/` 等 25 个路径）已入该提交。**任何一步都可以 `git revert` 或 `git diff 8007b19..HEAD` 审查。**

## 权限与边界（本轮）

- 工作区内可读写增删；允许 git 写操作（不 push，不 `--force`，不改 config，不跳过钩子）。
- 禁止：伪造验证、删测试或改断言来"绕过"、把工作区外的破坏性操作当副作用。
- 数据/接口/依赖/架构变更必须兼容、可迁移、可回滚、有记录 → 一律写进 `AGENT_DECISIONS.md`。
- **用户真实数据保护（重要）**：`~/Library/Application Support/时间剪史/` 是用户真实剪贴板历史。在 A-3（损坏存档 + 一次复制即全量删除）修复之前，**不得**以默认数据目录启动真实 App；所有验证都用临时目录或环境变量重定向。

## 基线数字（已实测，作为改进的对照）

| 指标 | 基线 | 命令 |
|---|---|---|
| `swift build` | OK，5.81s（含 1 条编译告警） | `cd ClipboardHistory && swift build` |
| `swift test` | **退出码 1**，`passed=3 started=4`，1 次 `Fatal error` | `swift test > /tmp/baseline-test.log 2>&1; echo $?` |
| 用例总数（源码计数） | 135 个 `func test` / 23 文件 | `grep -c "func test" Tests/**/*.swift` |
| `scripts/tests` | OK，11 tests（Python 3.9.6） | `python3 -m unittest discover -s scripts/tests` |
| 一次 `save()`（12 张 1600×1200） | **667.8ms 主线程** | 审计探针 P-12 |
| 启动 `load()`（8 张 2000×1500） | **605.8ms 主线程** | 审计探针 P-14 |
| `filteredEntries`（500 条 ×1KB + 搜索词） | **14.07ms/次** | 审计探针 P-20 |
| Gatekeeper | `spctl -a -t execute` → rejected（ad-hoc，无 entitlements） | 见审计 06 附 6.2(3) |

## 执行顺序（按价值，见 AGENT_BACKLOG.md 的分数）

第一批（S1，数据/信任/闸）：R-01 调试开关与日志位置 → R-02 损坏存档保护 → R-03 菜单无确认清空 → R-04 Web URL 误判 → R-05 来源 App 丢失 → R-06 反馈载荷含原文。
第二批（性能，实测驱动）：R-07 PNG 字节缓存 + 保存去抖 → R-08 图片指纹去绘制 → R-09 派生列表缓存 → R-10 预览文案先截断 → R-11 预测改事件驱动。
第三批（契约与可观测）：R-12 README/安装说明与行为对齐 → R-13 Info.plist 用途描述 + 授权失败可见 → R-14 死代码清理 → R-15 构建脚本与版本单一来源。
第四批（UI 视觉审计与修复）：U-01..U-0n，方法见 `AGENT_UI_AUDIT.md`（离屏渲染真实视图取像素，不依赖屏幕录制授权）。
第五批（矩阵新维度补审计）：边界/错误/内存/兼容/可访问性/国际化/可观测性/类型/迁移/回滚 逐格填平，`待审` 必须归零。

## 已完成（每项 = 提交号 + 验证方式）

| 项 | 提交 | 验证结果 |
|---|---|---|
| R-01 调试日志门控 + 移出 /tmp（顺带恢复测试闸） | `cb8db30` | `swift test` 退出码 0，**Executed 135→146→176** 用例全绿；`/tmp` 两个日志不再新增；`DebugLoggingTests` 7 条守卫 |
| R-02 存档损坏恢复 + 滚动备份 + 原件保全 | `0792e6b` 前一次 | 4 条 `HistoryPersistenceRecoveryTests`；变异检查：去掉修复即报 "P-06 修复验证：图片文件不得被连带删除" |
| R-03 菜单"清空未收藏"必须确认 | `cc0c2df` 后 | `HistoryClearConfirmationTests` 3 条；去掉确认 ⇒ 立即变红 |
| R-04 浏览器链接不再当文件条目 | `cc0c2df` | `ClipboardIntakeURLKindTests` 4 条；变异回 `options:nil` ⇒ 复现 `.file(https://…)` 与 `fileDoesNotExist` |
| R-05 重复复制保留来源 App；`ClipboardIntake` 真正使用注入的 pasteboard | `cc0c2df` | `SourceAttributionTests` 3 条 + `ClipboardIntakeInjectionTests` 2 条；变异 ⇒ 断言变红 |
| R-06 反馈不再存正文 + 删除级联 + 导出失败可见 | `0792e6b` | `FeedbackStorageHygieneTests` 7 条；实测用户 plist 该键 blob 66,716,424 字节会被收窄 |
| R-48 推荐排序确定性（字典求和 + 次级排序键） | `f17fc86`/`f8ce4dd` 同批 | `RecommendationDeterminismTests` 4 条；两处变异各自可复现地变红 |
| R-07/R-08/R-09/R-10 主线程热点（载入/保存/预览/列表） | `f8ce4dd` | `PerfBudgetTests` 5 条：413.9→3.2ms、667.8→5.2ms、45.8→0.02ms、14.07→0.00ms/次 |

当前基线（复跑命令见 `AGENT_STATE.md` 恢复指令）：

| 指标 | 现在 |
|---|---|
| `swift build` | OK，**0 告警**（干净重建复扫） |
| `swift test` | 退出码 0，**Executed 176 tests, 0 failures**，连跑 6 次稳定 |
| `python3 -m unittest discover -s scripts/tests` | OK，11 tests |
| 工作区 | `git status` 干净（改动已提交） |

本轮新发现（原审计未覆盖，已进 backlog）：
- **R-49** `ClipboardIntake` 各读取方法的 `from:` 默认 `.general` ⇒ 注入的 pasteboard 被静默忽略，测试因此读到**用户真实剪贴板内容**。已修（R-05 同批）并把所有断言改成"只报类型不报正文"，避免回归时把用户内容写进测试日志。
- **R-48** 推荐排序跨启动不稳定（`features.values.reduce` + 依赖 `sorted` 稳定性）。已修。
- **R-50** `HistoryStoreTests` 的排序断言依赖"测试期间谁是前台 App" ⇒ 随机失败。已修（夹具固定来源）。
- **实测确认 R-06 的现实规模**：`~/Library/Preferences/com.clipboardhistory.app.plist` = 66,724,574 字节，其中反馈键 66,716,424 字节。

## 恢复指令（若上下文丢失，从这里续做）

1. `git log --oneline` 与 `git diff 8007b19..HEAD --stat` 看清已完成什么。
2. 跑 `cd ClipboardHistory && swift build && swift test`（**必须看退出码与 `Executed N tests`，不要用管道**）。
3. 读 `AGENT_BACKLOG.md` 找第一条未关闭的高/中价值项；`AGENT_DECISIONS.md` 读最近 5 条决定；`AGENT_UI_AUDIT.md` 看视觉项。
4. 外部参考：审计报告在仓库外 `/Users/wangziyi/Documents/时间剪史_审计_2026-10-08/`（145 条记录 + 21 条探针源码 `probes/`，探针断言的是"缺陷存在"，接入仓库时需逐条翻转）。
5. 停止条件见本文件开头与 AGENT_BACKLOG.md 末尾的"发布前检查单"。

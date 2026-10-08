# AGENT_STATE · 当前工作状态（自主修复引擎）

最后更新：2026-10-09 01:4x（本地）
**仓库位置（2026-10-09 起）**：`/Users/wangziyi/Codex_Project0`。
原先在 `~/Documents/Codex_Project0`，那在 iCloud「桌面与文稿」同步范围内（`CloudDocs/Documents` 是指向 `~/Documents` 的符号链接，
`bird` 在跑），同步会在仓库里留下 `名字 2.扩展名` 的重复副本 —— 本次就出现 29 个，SwiftPM 把 `Sources/` 下的类型编译两遍，构建直接崩，
第一次发布准备因此失败。旧路径现在是一个指向新位置的**符号链接**（保住旧书签/旧会话路径），确认无误后可以删掉它。
搬离时实测：跨出同步边界的 `mv` 会 `Operation timed out`（File Provider 需要先物化），要用 `rsync -a` 复制 + 校验 + 再删源。
分支：`fix/audit-remediation` 已删除（本地与远端；其提交全部在 `main` 上，删除前用 `git log main..分支` 验过为 0）
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
| R-02 存档损坏恢复 + 滚动备份 + 原件保全 | `0792e6b` | 4 条 `HistoryPersistenceRecoveryTests`；变异检查：去掉修复即报 "P-06 修复验证：图片文件不得被连带删除" |
| R-03/R-04/R-05 菜单确认、Web URL 误判、来源 App 归因 | `cc0c2df` | 3 组新测试；各自变异回旧实现即复现缺陷 |
| R-06 反馈不再存正文 + 级联清理 + 导出失败可见 | `0792e6b` | `FeedbackStorageHygieneTests` 7 条；实测用户 plist 该键 66,716,424 字节会被收窄 |
| R-48 推荐排序确定性 | `f17fc86`/`f8ce4dd` | `RecommendationDeterminismTests` 4 条；两处变异各自可复现地变红 |
| R-07/R-09/R-10 主线程热点（保存/派生列表/预览文案） | `f8ce4dd` | `PerfBudgetTests`：667.8→5.2ms、14.07→0.00ms/次、45.8→0.02ms |
| R-11/R-17/R-18/R-19/R-21 事件驱动预测 + 语义收敛 | `cb3a69b` | `PredictionSchedulingTests`（含代际丢弃）；静置不再 2s 轮询 |
| R-22/R-40/R-41/R-42/R-43 上限、拖选表、视频错误态、观察者释放、菜单脱敏 | `50e5a4e` | `DisplayPrivacyAndCapsTests` 等；离屏帧复验 |
| 第四批 · 视觉审计链路与 3 个真实缺陷 | `95b4301` | 离屏捕获 54 帧；修：设置侧栏图标隐形、破坏性按钮重复、5 处信息文字 `.tertiary`（暗色 2.2:1 → 5.79:1，亮色 1.89 → 3.98） |
| R-13 自动粘贴失败可见 + 存档恢复提示上屏 | `654a787` | `PasteFailureVisibilityTests` 7 条；变异（把上报改成空函数）⇒ 以正确原因变红；离屏帧确认横幅不破坏布局 |
| R-12/R-15/R-34 README 三条虚承诺、Info.plist 模板化、DMG 新鲜度与校验 | `1d442f5`,`fd59dbb` | `make dmg` 全链路跑通：通用二进制 + 16 键 Info.plist（含 `NSAppleEventsUsageDescription`）+ `.sha256`；挂载 DMG 复核内部产物；`scripts/tests` 17 条（新增 6 条，含"缺键必须构建失败"与"mtime 未变必须拒发"，两条都做过变异验证） |
| R-23 OCR 像素解码移出主线程 + R-08 残留的图片比较成本 | `4324441` | 实测 `add(3000x2000)` 主线程 94ms → 0.04~0.77ms；冷 `==` 4000x3000 217ms → 148ms（同字节重复 0.17ms）；`PerfBudgetTests` 那条**恒绿假守卫**（计时对象根本没算指纹）已重写 |

当前基线（复跑命令见下方恢复指令；本轮结束时的最终复跑见 AGENT_FINAL_REPORT.md）：

| 指标 | 现在 |
|---|---|
| `swift build`（清空 .build 后干净重建） | OK，**0 告警** |
| `swift test` | 退出码 0，**Executed 229 tests, 1 test skipped, 0 failures**（2026-10-09 在新路径复跑核实；现取方法：`swift test > /tmp/test.log 2>&1; rc=$?; grep -E 'Executed [0-9]+ tests' /tmp/test.log | tail -1`（`tail -1` 单独用会取到 swift-testing 那行 `Test run with 0 tests`，看着像"一条都没跑"），别信这里写的数字）；那个 skip 是离屏视觉套件，按设计只在设了 `CLIPBOARD_HISTORY_UI_SHOTS` 时跑 |
| `python3 -m unittest discover -s scripts/tests` | OK，**18 tests**（必须在**仓库根目录**跑；`ClipboardHistory/` 下没有 `scripts/tests`，在那里跑以退出码 1 报 `Start directory is not importable`） |
| `make build` / `make bundle` / `make dmg` | 全部退出码 0；DMG 挂载后复核：通用二进制（x86_64 + arm64）、`codesign --verify --deep --strict` 通过、Info.plist 16 键含 `NSAppleEventsUsageDescription`、`.sha256` 可校验且改一个字节就失败 |
| 离屏视觉捕获 | 58 帧（29 夹具 × 亮/暗），未绘制比例全部 <95%，最后一轮与上一轮逐帧差异 <0.6%（无回归） |
| 审计矩阵 | 190/190 格全部判定完毕，**待审 0** |
| Backlog | 54 行，**待办 0**（其余为 已完成(提交号) / 记录不改(理由)） |
| 工作区 | `git status` 干净；**已推送并核对，Latest = v1.4.7**（v1.4.6 保留；CI 在发布提交与之后的账本提交上都全绿）。当日一度因 GitHub 不可达而落后，网络恢复后推上去了，并用 API 核对：远端 `main` == 本地 `main`、`v1.4.6→e4ac62b`、`v1.4.7→5190ad1`，两个 Release 附件的 sha256 与本地 `.dmg.sha256` 逐字相同。核对命令写在文末"恢复指令"第 6 条（别信这里写的 SHA，跑一遍现取） |

本轮新发现（原审计未覆盖，已进 backlog）：
- **R-49** `ClipboardIntake` 各读取方法的 `from:` 默认 `.general` ⇒ 注入的 pasteboard 被静默忽略，测试会读到**用户真实剪贴板内容**。已修（R-05 同批），断言改成"只报类型不报正文"。
- **R-48** 推荐排序跨启动不稳定。已修。
- **R-50** `HistoryStoreTests` 排序断言依赖前台 App。已修。
- **R-51** 图片去重仍要"同尺寸不同内容"时两侧各解一帧（148ms/次，主线程）。已比旧实现快 2.9×，残留部分记为待办：把 64px 采样值随条目一起持久化即可彻底摘掉。
- **守卫本身的失效模式**（方法级发现）：`PerfBudgetTests` 的指纹用例计时的是"构造"而不是"比较"，惰性缓存令它永远 0.00ms —— 已重写，并把"每类比较用各自第一次被比较的对象"写进注释。同类问题也出现在视觉捕获上（4 类假帧，见 `AGENT_UI_AUDIT.md`）。
- **实测确认 R-06 的现实规模**：`~/Library/Preferences/com.clipboardhistory.app.plist` = 66,724,574 字节，其中反馈键 66,716,424 字节。

## 恢复指令（若上下文丢失，从这里续做）

1. `git log --oneline` 与 `git diff 8007b19..HEAD --stat` 看清已完成什么。
2. 跑 `cd ClipboardHistory && swift build && swift test`（**必须看退出码与 `Executed N tests`，不要用管道**）。
2b. 视觉帧：`cd ClipboardHistory && CLIPBOARD_HISTORY_UI_SHOTS=/tmp/shots swift test --filter UICaptureTests`（改 UI 前后各拍一组同参数帧，见 AGENT_UI_AUDIT.md 的复验规则）。
3. 读 `AGENT_BACKLOG.md` 找第一条未关闭的高/中价值项；`AGENT_DECISIONS.md` 读最近 5 条决定；`AGENT_UI_AUDIT.md` 看视觉项。
4. 外部参考：审计报告在仓库外 `/Users/wangziyi/Documents/时间剪史_审计_2026-10-08/`（145 条记录 + 21 条探针源码 `probes/`，探针断言的是"缺陷存在"，接入仓库时需逐条翻转）。
5. 停止条件见本文件开头与 AGENT_BACKLOG.md 末尾的"发布前检查单"。
6. 远端一致性核对（本轮遗留项已做完，这段留作随时复查的入口）：
   ```bash
   cd /Users/wangziyi/Codex_Project0
   git log --oneline origin/main..main                  # 空 = 没有未推送的提交
   git push origin main                                 # 当日 GitHub 只在这一刻通：443/22 其余时间被断
   gh api repos/mnmc5h5ntg-wq/ClipboardHistory/branches/main --jq '.commit.sha'
   for t in v1.4.6 v1.4.7; do gh api "repos/mnmc5h5ntg-wq/ClipboardHistory/git/refs/tags/$t" --jq '.object.sha + " " + .ref'; done
   gh release view v1.4.7 --json assets --jq '.assets[] | .name + " " + .digest'
   ```
   实测结果（2026-10-09 04:52 CST）：远端 `main` 与本地相同，`refs/tags/v1.4.6 = e4ac62b`、`v1.4.7 = 5190ad1`，
   与本地 `git rev-list -n1 <tag>` 一致；两个 Release 附件的 `digest` 与本地 `时间剪史_v1.4.x.dmg.sha256` 逐字相同。
   **注意 `git ls-remote` 走 22 端口、`gh` 走 443 API：同一时刻前者可能失败而后者成功**，别因为一条失败就判定"没推上去"。
   另外用户从新路径确认过项目能打开之后，旧路径的兼容符号链接 `~/Documents/Codex_Project0` 可以直接删除。

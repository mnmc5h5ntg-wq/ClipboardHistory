# AGENT_FINAL REPORT · 时间剪史 审计整改（分支 `fix/audit-remediation`）

生成时间：2026-10-09（本地）
基线：`main` @ `db077f6`；修复前工作点 `8007b19`
**已发布**：`main` 已推送；**Latest = v1.4.7**（v1.4.6 保留不动）。
两版都是发布后从 GitHub 重新下载两个附件、`shasum -a 256 -c` 通过，并挂载 DMG 复核包内版本与通用二进制。
发布说明：https://github.com/mnmc5h5ntg-wq/ClipboardHistory/releases/tag/v1.4.7
账本：`AGENT_STATE.md`（状态与复跑命令）、`AGENT_BACKLOG.md`（190 格矩阵 + 54 行待办）、`AGENT_DECISIONS.md`（D-000…D-014）、`AGENT_UI_AUDIT.md`（视觉审计与复验记录）
外部审计报告（只读阶段产物，仓库外）：`/Users/wangziyi/Documents/时间剪史_审计_2026-10-08/`

---

## 1. 一句话结论

审计发现的 6 个 S1 级问题全部关闭，其中 4 个是**真实的数据丢失或隐私泄露路径**；主线程上四条最热的卡顿路径被实测消除；测试从"只跑 3 个用例就崩"变成 **229 个用例、连跑 6 次全绿、干净构建 0 告警**；矩阵 190 格全部判定完毕，backlog 待办归零。有 7 件事我**没能验证**，写在第 6 节，没有混进"已完成"。

---

## 2. 数据与安全（最高价值的一组）

| 问题 | 原来的行为 | 现在 | 提交 |
|---|---|---|---|
| 存档损坏 ⇒ 整个历史库连图片一起消失（探针 P-06 实测 images 2→0） | `try?` 把"文件存在但解析失败"折叠成空历史，下一次保存覆盖写，`removeUnusedImages` 顺手删光旧图片 | 每次成功保存同步写 `history.json.bak`；解析失败时先保全 `history.corrupt-<ts>.json`（**永不删原件**）→ 退到备份 → 尽力保住被引用的图片文件名 | `0792e6b` |
| 菜单"清空未收藏"无二次确认 | 带 alert 的函数根本没有调用者 | `.clearHistory` 走 `confirmAndClearHistory()`，确认器可注入并有测试 | `cc0c2df` |
| 第二实例会整片覆盖第一实例的存档 | 没有任何"已在运行"检查；而 `make run` 用的正是 `open -n` | `InstanceGuard`：同 bundle 的活实例存在时记日志并静默退出；判定逻辑是纯函数，7 条测试（含拿真实 Finder 喂适配器） | `83d3a11` |
| 装了新版再退回旧版会静默毁数据 | `version` 字段**只写不读** | 读到更高版本 ⇒ 只读打开、明确告知原因、`save()` 直接返回不写盘；更低版本走唯一迁移入口 `migrate(_:)` | `6c08620`（D-012） |
| 反馈载荷里内嵌剪贴板原文，清空历史也不清 | 用户 plist 里该键实测 **66,716,424 字节**，含 preview 原文 | 只存 `entryID/kind/createdAt/轻量上下文`；`delete`/`clearAll` 级联清理；旧格式仍可解码 | `0792e6b` |
| 菜单栏直接显示正文（含密钥） | 菜单标题就是剪贴板前若干字符 | `EntryPresentation.menuLabel`：疑似敏感内容显示为「疑似敏感内容（类型） · 相对时间」 | `50e5a4e` |
| OCR 日志把识别出的文字前 80 字符写进 `/tmp/ocr_debug.log` | 全局可写目录 + 可能正是密码 | 日志统一走 `CLIPBOARD_HISTORY_DEBUG=1` 开关、写 `~/Library/Logs/时间剪史/`（0700/0600、拒绝符号链接目标）；OCR 日志**只记长度不记内容** | `cb8db30`, `4324441` |
| 自动粘贴失败完全静默 | `Process.launch()` 之后没人看退出码，用户只看到"点了没反应" | `PasteKeyExecuting` 抽象 + 失败原因翻译成可执行指引（指向「自动化」授权页、说明可手动粘贴），经顶部提示条显示；`NSAppleEventsUsageDescription` 进 bundle | `654a787`, `1d442f5` |
| 存档恢复提示只存在于 `@Published` 里，界面上永远看不到 | 修了数据丢失却不告诉用户 | 新增 `NoticeBanner`，恢复提示 / 粘贴失败 / 成批过期三类共用 | `654a787`, `6c08620` |

**刻意没有做的事**：成批过期时不做"猜时钟异常就不裁剪"的启发式 —— 用户两个月没打开 App 也会一次清掉几十条，两种情况从时间戳上无法区分，让程序赌会留下"永远不过期"的洞。改成把数字与原因显示出来，由人判断（D-012）。

---

## 3. 性能（全部是实测数字，不是估计）

| 路径 | 修复前 | 修复后 | 提交 |
|---|---|---|---|
| 12 张 1600×1200 的库上保存一条新文本 | 667.8ms 主线程 | ~5ms（同字节缓存命中） | `f8ce4dd` |
| 启动载入 12 张 1600×1200 | 413.9ms | 3ms | `f8ce4dd` → `4324441` |
| `filteredEntries`（500 条 ×1KB + 搜索词），一帧内原本被调 3–5 次 | 14.07ms/次 | 0.00ms/次（缓存后一次改搜索词才 13.79ms，含唯一一次重算） | `f8ce4dd` |
| 2.4MB 文本的单条 preview | 45.8ms | 0.02ms | `f8ce4dd` |
| 复制一张 3000×2000 图片时 `add()` 的主线程耗时 | 94ms（去重比较里整幅解码 NSImage） | 0.04–0.77ms | `4324441` |
| 同尺寸不同内容的一对图，冷比较 | 434ms 起（两侧各 217ms） | 147ms（一侧已焐热时 83ms；同字节重复 0.15ms） | `4324441` |
| 预测刷新 | 2 秒定时器轮询 | 事件驱动（新复制 / 打开菜单 / 前台切换通知），带代际防护丢弃过期结果 | `cb3a69b` |
| OCR 像素解码 | 主线程 `NSImage(contentsOf:)` + 整幅 `cgImage` | ImageIO 直接解 64px/1200px 一帧，串行后台队列，主线程只写回结果 | `4324441` |

一条重要的**反面发现**：`PerfBudgetTests` 里那条"指纹成本与像素数解耦"的守卫是**恒绿的假测试** —— 它计时的是 `StoredImage(nsImage)` 构造，而指纹是惰性的，于是 4000×3000 和 200×150 都报 0.00ms。已重写为真正触发比较的三条（含"一侧焐热后必须更快"这条缓存共享断言）。

---

## 4. 正确性与契约

- 浏览器链接不再被当成本地文件条目（`.urlReadingFileURLsOnly`），否则"再次复制"必失败（`cc0c2df`）。
- 重复复制保留来源 App 归因，否则推荐因子被自己清空（`cc0c2df`）。
- 推荐排序确定性：字典求和改为按 `allCases` 固定顺序 + 显式次级键（分数 → 理由 → 时间 → uuid）。这不是测试洁癖 —— **同一份历史在两次启动之间给出不同的"猜你要粘贴"** 是用户可见的行为不一致（`f8ce4dd`, `cb3a69b`）。
- 同一个 `entryID` 只能占一个推荐名额：修复前"Top 3"可以显示成两行同样内容（`4bb02ef`）。
- 敏感内容前缀规则收紧（需紧跟 ≥12 位 `[A-Z0-9]`），`ASIA-East…` 之类不再误判（`cb3a69b`）。
- 推荐"复用 N 次"文案与实际计数一致；权重全 0 时排序退化为收藏/时间而非随机（`cb3a69b`）。
- 8 条推荐引擎边界用例：空历史、单条、limit=0/负数、500 条、全 0 权重、未来时间戳、重复 id、隐私开关两侧（`4bb02ef`）。

---

## 5. 视觉与交互审计

方法：离屏渲染真实视图（`NSWindow` + `NSHostingView` + `cacheDisplay`），不需要屏幕录制授权；由 `CLIPBOARD_HISTORY_UI_SHOTS` 触发，未设置时整组 skip。共 **68 帧**（34 夹具 × 亮/暗）—— 第一轮是 29 夹具 58 帧，第二轮末把菜单栏面板的三个状态补了进来（D-024）。

先修掉捕获链路自己产出的 **4 类假帧**（每一类都曾让我得出过错误结论）：裸 hosting view 导致内容缩到一角、手工翻倍位图尺寸、`cacheDisplay` 不画 AppKit 底色导致"白底白字看起来整块空白"、以及 `NavigationSplitView` 的 sidebar 列在离屏下根本不跟随强制外观（"暗色主界面黑字不可读"其实是捕获产物 —— 用最小复现 + 同一组件独立拍帧两条证据判定，非产品缺陷）。

真实缺陷 3 个，全部有改动前/后同参数帧与像素级数字（见 `AGENT_UI_AUDIT.md` 复验记录）：

1. 设置侧栏未选中行的 SF Symbol 几乎不可见 → 图标与文字同为 `labelColor`（亮色下图标核心亮度 37–49，文字 46）。
2. 「清空未收藏记录 + 清空」在通用与数据两个分类各一份（重复的破坏性按钮）→ 只留「数据」页。
3. 5 处承载信息的文字用 `.tertiary`：暗色实测 **2.22:1**、亮色 **1.89:1** → 提到 `.secondary` 后暗色 **5.79:1**、亮色 **3.98:1**。亮色停在系统 `secondaryLabelColor` 的原值，再往上只剩 `.primary` 会抹掉整个层级，因此记为**有意取舍**而非待修。

另外把 `HistoryPrivacyCopy`（早就写好、有单测、但产品里从没显示过的 5 条隐私说明）接进设置「隐私」页 —— 隐私承诺只有用户在界面里看得到才算产品行为（D-013）。

无障碍：图标按钮的 `.help()` 全部改走 `helpLabel(_:)`（同时上 `accessibilityLabel`），并加静态守卫"界面层不得再出现裸 `.help(`"；变异检查确认加回一处即变红。

---

## 6. 我**没有**验证的事（不放进"已完成"）

1. **VoiceOver 实际朗读内容**：离屏窗口的无障碍树根本不建（BFS 只能走到根节点，`已遍历 1 个节点，标签样本=[]`）。只能做代码级检查与静态守卫。
2. **macOS 12/13/14 的运行时行为**：本机是 macOS 27 beta。编译期有真闸（`Package.swift` 声明 `.macOS(.v12)`，未加守卫的新 API 会编译失败，CI 每次都编两个 triple），但运行时结论一律标注"未验证"。
3. **hover / 拖拽选中间态 / 快捷键录制态 / 多文件展开态**：需要真实鼠标事件，离屏拿不到。
4. **菜单栏视图的帧**：故意不拍 —— 构造 `AppDelegate()` 会加载**用户真实历史库**，为拍一张图去读真实数据不可接受（D-002）。改用 `menuLabel` 的单元测试覆盖。
5. **双实例守卫的端到端实跑**：真要跑就得启动 App，而它会读写用户真实数据目录；除非先给数据目录加一个环境变量接缝（这一条我明确没做，见第 7 节建议）。
6. **减弱动态效果的真实观感**：判定逻辑有单测，但本环境无法切换系统设置去实看。
7. **Gatekeeper/公证**：产物仍是 ad-hoc 签名，`spctl` 依旧 rejected。这需要 Developer ID，属于 Roadmap，不是代码能解决的。

顺带：子代理报来 44 条文档不符，其中 **2 条被我判为误报**并留下理由 —— README 的 `git clone` 后 `cd ClipboardHistory && make build` 其实是对的（仓库名就是 ClipboardHistory，Makefile 就在那一层）；`docs/agents/domain.md` 原文已带 "if it exists" 限定。

---

## 7. 遗留与建议（按建议顺序）

1. ~~发布~~ **已完成**：v1.4.6 已发布并接管 Latest。发布过程中修掉发布脚本自身一个必然失败的缺陷 —— `/usr/bin/python3` 会给整棵子进程树注入 CommandLineTools 的 `SDKROOT`，而编译器来自 Xcode，于是脚本里的 `swift test` / `make dmg` 必挂（同一条命令在 shell 里手跑却是好的）。现在子进程环境由 `build_child_environment()` 显式对齐 `xcrun` 的解析结果，并有单测钉住。
2. ~~CI~~ **已完成并跑通**：`.github/workflows/ci.yml` 在 main 上首绿，7 步全 success（含零告警闸与执行数闸）。
3. ~~issue~~ **已完成**：#5、#16 已带逐条验收证据关闭；#13（右键菜单汉化）本轮未触碰，保持 open。
4. **R-51（图片采样成本）已按实测判定为不改**：把采样值持久化只能省掉"启动后第一次"那 64ms，省不掉新图本身那次采样，代价却是数据格式变更。数字已钉在测试里，将来要动有基线。
5. 若将来要真验证运行时分支或双实例行为，先加一个数据目录的环境变量接缝（与 `CLIPBOARD_HISTORY_LOG_DIR` 同构），否则任何实跑都会碰到用户真实数据。

---

## 8. 回滚

- 单个改动：每个提交都是独立可 `git revert` 的单元；数据/接口类改动在 `AGENT_DECISIONS.md` 里逐条写了回滚路径（D-002…D-014）。
- 全部：`git diff 8007b19..HEAD` 即本轮所有改动；`main` 仍在 `db077f6`，本分支未推送，**不 push 就不影响任何远端**。
- 数据兼容：本轮所有数据布局改动都是"新写旧读" —— `history.json` 文件名、v1 格式、字段全部不变；新增的 `.bak`、`history.corrupt-*.json` 是附加文件，旧版本读不到也不受影响，因此**降级可运行**，回滚不产生需要清理的残留。

---

## 8a. 为什么有两个版本号（v1.4.6 与 v1.4.7）

v1.4.6 的 tag 打在发布准备提交上，而 CI 首跑抓到的两处修复在其后才合入 main —— 于是**已上传的产物里没有那两处修复**。
这正是本文件一直警惕的「源码已修 ≠ 已交付」。处置：不动 v1.4.6，把增量单独发成 v1.4.7（用户选定），
并在 v1.4.7 的发布说明里写清两版关系与唯一的产品行为差异。附带一条流程改进：**Release 附件名一律用 ASCII**，
因为 GitHub 会吞掉非 ASCII 前缀，导致 `.sha256` 记录的名字与实际附件名不一致、用户校验必然失败（v1.4.6 首传就中了）。

## 8b. 发布后 CI 首跑抓到的两条（值得记下来）

CI 不是装饰：runner 是 Swift 6.1.2、开发机是 6.2.1，两条只有远端能暴露的缺陷第一次跑就红了。

1. `HotKeySettingsTests` 覆写 `tearDown() async throws` 并 `try await super.tearDown()` —— 本机编得过，runner 上报 `sending value of non-Sendable type 'XCTestCase' risks causing data races`，**整个测试 target 编译失败**。修法是不再依赖 XCTest 生命周期签名，改为每条用例开头复位偏好（顺带让用例顺序无关）。
2. `URL(fileURLWithPath: "/").deletingLastPathComponent()` 在 runner 的 Foundation 上给出 `/..`，于是根目录下的文件父目录标签被渲染成 `…/..`。这是**实现的可移植性缺陷**，改的是代码（先 `standardizedFileURL`）而不是断言。

两条都是"我本机全绿"覆盖不到的那类问题 —— 也是这条 CI 存在的理由。

## 8c. 仓库位置变更（发布之后）

仓库已从 `~/Documents/Codex_Project0` 移到 **`/Users/wangziyi/Codex_Project0`**，脱离 iCloud「桌面与文稿」同步范围；旧路径留了一个指向新位置的符号链接，确认无误后可删。
移动后的验证：`swift build` 0 告警、`swift test` 229 例全绿、发布脚本测试 18 例、`make bundle` 产出通用二进制且包内版本 1.4.7、`git status` 干净。
**这条当时就过期了**：写完那行的同一天，GitHub 从这台机器整体不可达（`github.com:443` TLS 握手被断、
`ssh -T git@github.com` 被 `Connection closed ... port 22`，同期 apple.com 正常 200），只改账本的提交推不出去，
于是"与远端一致"变成了一句过期话 —— 这正是这本账反复提醒的那个失效模式。网络恢复后已全部推上去，并改用**服务端**取证核对：
远端 `main` 与本地相同、`refs/tags/v1.4.6 → e4ac62b`、`v1.4.7 → 5190ad1`（与本地 `git rev-list -n1` 一致），
两个 Release 附件的 `digest` 与本地 `.dmg.sha256` 逐字相同，CI 在发布提交与之后的账本提交上都是 `success`。
一条环境经验值得记：**`git ls-remote` 走 22 端口、`gh` 走 443 API，两者会在同一时刻一个通一个不通** ——
那天 `git push` 成功后紧接着三次 `ls-remote` 全失败，差点被判成"没推上去"；最终定性由 API 侧给出。
复查命令写在 `AGENT_STATE.md` 的"恢复指令"第 6 条，数字一律现取，不写在这里。

两条实测事实值得记下来：跨出 iCloud 同步边界的 `mv` 会 `Operation timed out`，必须改用 `rsync -a` 复制 + 校验 + 删源；而 `~/Documents` 下的 `名字 2.扩展名` 重复副本**具体由谁产生我没有查清**（`Codex_Project0_backups` 是 6 月 8 日的手工快照、`Codex_Project0.zip` 是 6 月 5 日的，都不是），只能说移出同步范围消除了最可能的那条路径，不能保证它永不复发 —— 复发时的特征是`Sources/` 下出现重复类型声明、构建报类型歧义。

## 9. 复跑（本轮结束时的实际输出）

```bash
cd /Users/wangziyi/Codex_Project0/ClipboardHistory
swift build                      # 新路径复跑过：0 告警
swift test                       # 新路径复跑过：Executed 229 tests, with 1 test skipped and 0 failures
CLIPBOARD_HISTORY_UI_SHOTS=/tmp/shots swift test --filter UICaptureTests
                                 # 新路径复跑过：退出码 0、58 帧（29 夹具 × 亮/暗），未绘制比例闸门全过
cd /Users/wangziyi/Codex_Project0
python3 -m unittest discover -s scripts/tests    # 新路径复跑过：Ran 18 tests, OK —— 只能在仓库根目录跑
make bundle                      # 新路径复跑过：通用二进制（x86_64 + arm64），包内版本 1.4.7
shasum -a 256 -c 时间剪史_v1.4.7.dmg.sha256      # 实测 OK；改一个字节即 FAILED，已验证
make dmg                         # ⚠ 唯一没重跑的一条：它会覆盖已发布的 v1.4.7 产物与 .sha256（重编必然得到字节不同的 dmg）
```

这一版是**把每条真跑过之后重写的**。原来那段有两处照着敲就跑不通：python 那条排在 `cd ClipboardHistory` 之后，
而那个目录里没有 `scripts/tests`（实测退出码 1、报 `Start directory is not importable`）；`make dmg` 被写成"复跑"，
实际在新路径复跑它会覆盖已发布产物的校验和 —— 现在明确标成"不要重跑"，并补了一条真实可跑的 `shasum -c`。

---

## 10. 第二轮审计整改（2026-10-09 晚）

审计交付：`/Users/wangziyi/Documents/时间剪史_审计_2026-10-09_第二轮/`（135 格全覆盖 + 4 条新缺陷 + 6 条"修了一半" + 13 轴 HIG 审查），
被审对象是 HEAD `81bce8d`。本轮在它之上做的提交数**现取**（写死就会随下一次提交过期）：
`git rev-list --count 81bce8d..HEAD`，其中只动 `AGENT_*.md` 的那些用逐提交 `git show --pretty=format: --name-only` 归类；
全部已推送。`swift build` 0 告警；用例数同样**现取**（它会随下一次提交变，写死必过期）：
`cd ClipboardHistory && swift test 2>&1 | grep -E "Executed [0-9]+ tests" | tail -1`；
python 脚本测试 25 例（`python3 -m unittest discover -s scripts/tests`）；离屏帧 68 个（第二轮 58 → 64 → 68）。**已发布**：v1.4.8，见下面 §11。

### 10.1 修了什么（按审计编号）

| 审计项 | 提交 | 一句话 |
|---|---|---|
| N-1（S2 崩溃） | `876c015` + 守卫 `ca12531` | adapter 的两个 `Dictionary(uniqueKeysWithValues:)` 改为保留首条；补**走 HistoryStore 全管线**的端到端用例，变异对照把实现改回去会让进程 trap |
| N-2（S2 数据丢失） | `bacde44` | `HistoryStore.init` 不再写盘，首次写回推迟到守卫放行之后；原三条"init 即持久化"用例保留全部断言并新增"init 阶段零写入" |
| N-3 / N-4 | `fb37c4b` / `a56f2e5` | `load()` 复位只读标志；把"不记也算通过"的假绿断言钉成两侧 |
| R2-01 | `ca12531` | 见 N-1 |
| R2-03 亮色 chrome | `6a2c040` | 9 处 `.white.opacity` → 语义色；亮色 pill 的 chrome 从"与背景差 ≤3 级"变成 43 级 |
| R2-04 保存 IO | `9ac4661` | 同名同长度的图片文件不再重写；被取代的落盘任务取消；inode 判据 + "history.json 每次必换" 阳性对照 |
| R2-05 拖拽 | `d463ef9` + `53bbe85` | 拖出（文本/PNG/文件引用）与拖入（文件入库）都通了；多文件拖出需要 NSView 级 session，明确不做半截动作 |
| R2-06 破坏性确认 | `a841337` | Return 现在是"取消"，破坏性按钮无快捷键且标 `hasDestructiveAction` |
| R2-07 来源 App 落盘 | `d8d11f4`（D-016） | schema 仍 v1，两个可选字段；隐私文案同步披露 |
| R2-08 图片上限 | `1183f9f`（D-017） | 4096px 最长边，4K 截图逐字节不动；端到端采集用例 |
| R2-09 图标/空态/超时 | `1214526` | `"questionable"` 非法符号 → `questionmark.circle`，并加了一道全仓 SF Symbol 扫描守卫；菜单补空态；spinner 8 秒兜底 |
| R2-10 减少动态 | `2438aa6` | pill 的过冲弹簧与 hover 放大读系统开关 |
| R2-11 全串计数 | `8cfdfe5` | 有界字符计数，性能上界从 20ms 收回 5ms |
| R2-12 粘贴前复核 | `d218803` | 250ms 内目标 App 换了/退了就不再注入，并说明内容仍在剪贴板 |
| R2-13 字号 | `1214526` + `d218803` | 菜单理由行与行时间戳都提到 11pt |
| R2-14 文档 | `f7398f3` | R-20 那行"移到 history.expired.json"的假承诺已更正 |
| R2-15 AI 脚手架 | `d0b2416`（D-020） | 拆三个 target；`nm` 证明草案符号在产品二进制里为 0 |
| R2-16 只含 public.url | `f7398f3`（D-018） | 现在记成文本条目 |
| R2-17 注入接缝 | `f7398f3`（D-019） | `AppDelegate(historyStore:)`；当时记为「菜单栏离屏仍拍不到（97.7% 未绘制）」，那句话下一轮被推翻，见下面 `37f43f6` |
| R2-18 / R2-19 证据管道 | `bdb557b` | 插入点闪烁 + 夹具用 `Date()` 是全部噪声来源；修完**同代码连拍 0/58 帧不同** |
| R2-17 补拍（D-024） | `37f43f6` | **菜单栏面板第一次有像素**：`MenuBarExtra` 的 body 是普通 SwiftUI View，可以离屏渲染（以前那句「拍不到」只对 13 以下的 NSMenu 路径成立）。三个状态 × 亮暗，58 → 64 帧；`Fixture.settle` 钩子 + 「帧名必须由帧自己证明」；变异对照红 4 次 |
| 侧栏图标"看不见"量成数字（D-025） | `2817a93` | 产品里未选中四行图标列墨水 0.0000，同一图标改固定 `Color.black` 就是 0.175–0.402，复刻 List 行里 `.primary` 又正常 ⇒ 离屏语义色伪影，**产品一字未改**，注释换成测量 |
| CI 第五次红（同族） | `e8a59e4` | 离屏探针把"文字列能数出 5 行"当断言，runner 上只有 4 行 ⇒ 判据换成"整列图标墨水"（与行几何无关）；变异（不存在的符号名 ⇒ 0.0000）证明它有牙 |
| 工具栏"猜出来再删"补测试（08-08 / 13-08） | `85c6ba5`（D-026） | 9 条正反用例，负向更承重（自己的复制/筛选/搜索项不许被误删）；顺带量出 `item.view = nil` 会清掉 `item.action`，以及那条 action 直判其实是冗余保险（删了仍全绿） |
| 快捷键录制器（13-08） | `14a37a0`（D-027） | 6 条只测可观测行为的用例里，5 条直接绿、1 条红在**产品**：录完合法组合后按钮仍写着"请输入快捷键"（`didSet` 在录制态跳过回显，之后再没人改）。加一行显式回显修掉；失焦那条守卫经变异对照承重 |
| 行内直接操作（用户提出） | `1395425`（D-028） | 双击行 = 复制这条（与浮层「再次复制」同一个动作）；行首星标 = 就地收藏。星标从 `.clear` 指示器变成真控件，两态颜色都量化到 ≥3:1（未收藏 1.76/2.17 → 3.54/4.64，已收藏 黄 1.67 → 琥珀 3.90/4.28）；**这次是在屏合成点击真点验证的**，而且是在真实侧栏容器里（外层 ScrollView + 列表级拖选手势并存）：点星标翻收藏、点行改选中、双击恰好写一次剪贴板且写的就是刚点中的那条；删掉手势即红（变异对照）。帧 64 → 68 |
| 启动闪退回归（D-029，S1） | 本次提交 | D-019 的显式 `init(historyStore:)` 让 ObjC `-init` 变成 trap 桩，SwiftUI 的 `@NSApplicationDelegateAdaptor` 走的就是它 ⇒ 包一打开就 `SIGTRAP`。三行 `override convenience init()` 修掉 + 两条守卫；**测试全绿挡不住的原因**：Swift 侧 `AppDelegate()` 走默认参数那条，CI 又从不启动 .app（缺口开成 R2-21） |
| 列表蓝框（D-030，用户报） | 本次提交 | 那是 R2-02 `.focusable()` 带来的系统焦点环。保留可聚焦、加 macOS 14+ 的 `focusEffectDisabled()`；**macOS 12/13 仍会有环**（平台无开关）。前后都量过：`_FocusRingView` 15 → 2，其中整块列表那圈消失 |
| 看画面才看见的文案缺陷 | `16d658d` | 推荐理由一行里把来源 App 说两遍（`Safari · 偏好链接 · 回到Safari`）。改成「没有别的标签点过来源 App 才补裸名」；断言先写、对旧实现报红（2 次）后才动实现 |

### 10.2 本轮自己制造并被测试抓住的问题

四条，都值得留着当下轮的对照：
1. 新加的"暂无推荐"空态会在**有候选的机器上先闪一下**（菜单同步构建、预测异步计算）—— 写菜单测试时暴露，用 `isRefreshingPredictions` 区分"还在算"与"确实没有"（D-021）。
2. 把本机测出来的数字当契约 —— **这一类一共红了五次**：`@MainActor` 测试类的 `setUpWithError` 写隔离属性
   （本机 Swift 6.2.1 放行、CI 的 6.1.2 拒绝，`a009dd5` 改成每条自建临时目录 + `addTeardownBlock`）；
   断言"像素数严格大于点数"（本机 2× retina，runner 是 1×，`d160b52`）；"热比较快于冷比较"（2 核 runner 上无分辨力，`268ccaa`）；
   搜索词代价取均值（`6b2e18f`，见 D-023）；以及"离屏列表能数出 5 行"（runner 只数出 4 行，`e8a59e4`）。
   五次全是**本地绿、远端红**。最后一次的修法值得抄：判据换成不依赖行几何的量（整列墨水），
   再配一条"把符号名换成不存在的名字 ⇒ 墨水 0.0000 判红"的变异，证明它不是装饰。
3. 一次变异对照的过滤器写错类名，得到"0 条执行"的假绿 —— 作废重跑（记在 D-018）。
4. **为了压 CI 抖动加的 load1 闸门自己是个缺陷**：它把"性能判据"变成"只在安静的机器上生效的判据"。
   拉 CI 原始日志实测 `load1=11.8 活跃核=3`（比值 3.9 > 我写的 2.0 闸门），照那写法 5 条守卫会在唯一的自动化环境里永久 skip。
   改成用**被测样本自己的跨度**决定能不能下结论（`最慢 − 最快 > 该条阈值` 才 skip），阈值一个没动，双向变异对照都实跑（D-023）。
   反面证据也记着：本机注入 12 个 `yes` 进程把 load1 顶到 44.4，`preview(2.4MB)` 的样本跨度仍只有 0.07ms —— 旧闸门会在**能分辨**的时候误 skip。

### 10.3 明确没做/没验证的

键盘：真实 Tab 现在能到搜索框（在屏探针实测），**但"Tab 能否走到列表行"仍未验证** —— 本机 `AppleKeyboardUIMode = -1`（完全键盘访问关闭）时 macOS 本来就不让 Tab 经过自绘可聚焦视图。复测方法：人工开该开关后跑 `CLIPBOARD_HISTORY_UI_INTERACTION=1 swift test --filter UIInteractionProbeTests`。
其余未验证：`NSAlert` 的真实按键行为、真实鼠标拖放、VoiceOver 实际朗读（测试进程里 AX 树为空）。
菜单栏面板**内容层已验收**（6 帧，见 10.1 与 D-024），仍未验证的只有系统菜单的材质/圆角与菜单项 chrome —— 那两层由系统绘制，需要在屏捕获。
设置侧栏图标：已量成"离屏语义色不解析"（D-025），但**真机上那一列长什么样仍未验收** —— 在屏捕获要么撞上已废弃 API 的告警闸门，要么弹屏幕录制授权框。
**CI 缺"能不能启动"这一关（R2-21，高）**：本轮的启动闪退说明"327 例全绿 + CI 绿"对"包能不能打开"是零覆盖。
明确不做：`List(selection:)` 整体重写（`.draggable` 要 macOS 13、会改掉 4 个捕获帧、丢 `dragSelectRange` 锚点语义）、设置侧栏符号风格统一（唯一证据来自不可信的捕获列）、签名与公证（需证书与授权）。
另外**要去看而不是只在这里断言的一件事**：性能守卫在新 runner 上到底下没下结论。检查方法（已实跑过一次，见 D-023）：

```bash
gh run view <run-id> --log | grep -E "PERF\[|同操作样本跨度"
```
**已核（`c952905` 的 CI 日志）**：runner 实测 `load1=27.7 / 活跃核=3`，8 条 `PERF[...]` 采样**全部下结论、零 skip**（搜索词代价 最快 25.04 / 均值 37.07 / 最慢 56.99ms）。先删掉的那道 load 闸门会把这 8 条全部变成 skip。
以后每次看到「同操作样本跨度…已超过阈值」才需要重新按 runner 定标 —— 那说明该判据在远端真的分辨不了。

### 10.4 复跑（本轮结束时）

```bash
cd /Users/wangziyi/Codex_Project0/ClipboardHistory
swift build && swift test                       # 判据取：swift test 2>&1 | grep -E "Executed [0-9]+ tests" | tail -1
CLIPBOARD_HISTORY_UI_SHOTS=/tmp/shots swift test --filter UICaptureTests          # 68 帧
CLIPBOARD_HISTORY_UI_INTERACTION=1 swift test --filter UIInteractionProbeTests    # 在屏探针（会抢前台）
cd .. && python3 -m unittest discover -s scripts/tests                            # 25 例 OK
python3 scripts/frame_audit.py diff /tmp/A /tmp/B                                 # 逐帧差异
```
账本：`AGENT_STATE.md`（第二轮章节 + 3 段进度快照）、`AGENT_BACKLOG.md`（R2-01…R2-21 + 14 张进度快照）、`AGENT_DECISIONS.md`（本轮 D-015…D-028）、`AGENT_UI_AUDIT.md`（第二轮章节 + 菜单栏面板补拍 + 侧栏图标测量）。

---

## 11. v1.4.8 发布（2026-10-10）

用户授权后出包。发布对象是 `e4aee3c`（轻量 tag `v1.4.8`），线上 Latest 已切到本版：
<https://github.com/mnmc5h5ntg-wq/ClipboardHistory/releases/tag/v1.4.8>

**这一版含**：审计第二轮的全部整改（N-1…N-4、R2-01…R2-19，见 §10）、行内直接操作（双击复制 + 星标收藏，D-028）、
以及侧边任务修掉的两处（D-029 启动闪退、D-030 焦点环）。

**出包前先补了一道闸门**（D-031 / R2-21）：`prepare_release.py` 现在会反汇编包内二进制，
`AppDelegate` 若还留着「未实现初始化器」桩就拒绝发布。必要性由 D-029 本身证明——
那一版"327 个用例绿、CI 绿、codesign 有效"，用户一打开就闪退，因为链路里没有任何一步真的执行过它。
闸门只挡到"不会在 `-init` 上 trap"，**运行时冒烟（真的打开、活过 N 秒）仍是缺口**，所以 R2-21 标的是部分完成。

对**产物**而不是对中间构建做的验证：

| 检查 | 结果 |
|---|---|
| `hdiutil verify` DMG | VALID |
| 挂载后读 `Info.plist` | `CFBundleShortVersionString` = 1.4.8、`CFBundleExecutable` = ClipboardHistoryApp |
| 启动闸门跑在 DMG 内的二进制上 | 通过；同时仍读到 2 个良性桩类名 ⇒ "通过"是有内容的通过，解析器不是瞎的 |
| `codesign --verify --deep --strict` | valid on disk / satisfies DR |
| `spctl -a -t execute` | **rejected**（ad-hoc 未公证，预期）⇒ 发布说明保留 Control-点击指引 |
| `gh release list` | Latest = v1.4.8 |
| 服务端自算摘要 vs 仓库 `.sha256` | `c31a16e0…e88d` 逐字一致（独立第二估计器） |
| 仓库外 `gh release download` + `shasum -a 256 -c` | OK |

发布时该提交的实测：`swift build` 0 告警 · `swift test` 328 例 / 9 skip / 0 失败 ·
发布脚本测试 30 例 OK（现取：`python3 -m unittest discover -s scripts/tests`）· 68 帧基线。
资产命名沿用 v1.4.7 口径：仓库内中文名、GitHub 用 ASCII 名，且上传那份 `.sha256` 内写 ASCII 文件名
（否则用户下回来 `shasum -c` 必失败，v1.4.6 踩过）。

数据兼容：存档格式仍是 v1，只新增两个可选字段；回退到 v1.4.7 只会忽略它们。

仍开着的 issue：#13「右键菜单未汉化且含无关项」—— 本轮没碰右键菜单，没有顺手关掉它。

## 12. issue #13 修复（2026-10-10 夜，D-032）

用户点名修上一条留下的 #13。表面症状是"右键菜单里有英文的系统项"，实际要修的是**所有权**：
编辑态下右键根本不落在我们的搜索框上。

被实测证伪的三条做法（都是我们自己先写出来、再被数字推翻的）：

| 做法 | 证据 | 结论 |
|---|---|---|
| `hitTest` 把右键让位给文本框 | 编辑态 `rightMouseDown`/`menu(for:)` 一次都没被调用；合成事件派发期间 `NSApp.currentEvent` **7 条日志全为 nil** | 走不到的分支，且无法验证 ⇒ 删除 |
| `editor.menu = 我们那份` | 右键时读回 12 项，含**快速查看附件 / 字体 / 书写方向 / 布局方向** | 被 AppKit 复原，等于没修 ⇒ 留一条反模式守卫禁止再回来 |
| 就地改 `menu(for:)` 返回的那份 | 两次调用 `!==`；`removeAllItems()` + 关开关后再问，内容又满、开关又 `true` | 每次现造，改不动 |

落地：`FieldEditorRightClickInterceptor` 用 `addLocalMonitorForEvents(matching: [.rightMouseDown, .otherMouseDown])`
在 AppKit 派发**之前**截走；只在"第一响应者的 field editor 沿 superview 往上属于某个 `ChineseMenuTextField`"时认领，
否则原样交回。交付 `撤销/重做/剪切/复制/粘贴/全选`（搜索框）与 `复制/全选/查找…`（只读详情区），
两份都 `allowsContextMenuPlugIns = false`、弹出前 `sanitize`；`NSWindow.allowsAutomaticWindowTabbing = false`
建窗前设掉窗口级项。全仓库只有搜索框一处可编辑文本，所以范围是完整的。

一条**没做成的验证**要讲清楚：`NSMenu.popUpContextMenu` 是模态的，在 `NSMenu.didBeginTrackingNotification`
里 `cancelTrackingWithoutAnimation()` 也叫它不返回（8 秒看门狗 exit）。所以"屏幕上真弹出来的样子"
**没有**自动断言，改由 `docs/MANUAL_TEST_v1.4.8_issue13.md` 人眼核对；仓库里的判据取
AppKit 决定菜单的入口（`menu(for:)`）+ 拦截器实际交付的那份。

验证：`ChineseTextContextMenuTests` 13 例（含认领判据两个方向、三条源码守卫）·
在屏 `testRightClickMenusAppKitWouldShowAreChinese`（真左键进编辑态 + 真右键事件 + 反面对照 + 20 秒看门狗）·
变异对照 5 组逐一点亮（其中"让拦截不吞事件"表现为挂住后被看门狗判红 —— 那就是它有效的方式）·
`swift build` 0 告警 · `swift test` **339 例 / 10 skip / 0 失败**（skip 逐条核对，全是 env 门控在屏探针）。

遗留：R2-22（屏幕上真弹出来的样子无法自动断言）、R2-23（将来新增裸 `TextField` 会绕开拦截器）。
回滚：`git revert` 本次提交；监视器有 `uninstall()`，幂等。

issue 状态：#13 现为 `closed`。需要说清楚的是**关闭动作不是我主动做的** —— 账本提交标题里的
"…to fix #13…" 被 GitHub 当成闭合关键字（timeline 的 `closed` 事件带的 commit_id 就是那条账本提交）。
结论本身站得住（修复在 `main` 上、CI `success`、四条验收逐条对过，其中"macOS 12 真机"只做到
"不引入高于 12 的 API"这一层，观感核对走手工清单），但这类"由提交消息触发的外部状态变化"
以后要写在动作清单里，而不是事后解释。

## 13. 第三轮审计整改（2026-10-10 夜，D-033）

输入是仓库外的 `~/Documents/时间剪史_审计_2026-10-10_第三轮/00-第三轮审计与改进方向.md`，
本轮 8 条新缺陷 D-1…D-8 全部处理。用户点名两处做法，都按指定执行：
**D-1 用文档里的第三种修法**（换 `List(selection:)`），**D-3 给「通用」补上真正属于它的两项**（不合并进「数据」）。

| # | 严重度 | 修法 | 自动化判据 | 还欠什么 |
|---|---|---|---|---|
| D-1 | S2 | 侧栏换 `List(selection:)`，删掉手工方向键与自绘选中态。~~拖出只从行首把手发起~~ 被真机否掉（D-034：`List` 把行内任何 `.onDrag` 提升成整行拖拽源）→ **保留整行拖出、删掉拖选** | 结构：真 `NSTableView`、`allowsMultipleSelection`、行数=可见条目数、拖出入口恰好一处、双击/星标接线、拖选残留必须为空 | 点选/双击复制/拖出落地**只能真机看**（合成事件送不进表格），手工清单第 1、2 节 + R3-D9 |
| D-2 | S3 | 内容类型标签改由条目自身决定（常用链接/文本/文件/多文件） | 真值表 + "同一份条目前台怎么变标签不许变"；**翻转**了一条钉住旧缺陷的用例 | — |
| D-3 | S3 | 「通用」补两项：暂停记录、识别截图文字（OCR）；判据 `RecordingGate`，键落 UserDefaults | 真值表 + store 级（暂停不入库、拖入仍入库、恢复继续记）+ 默认值 + 接线守卫 | 开关的实际观感与"暂停期间不补记"要真机确认（清单第 4 节） |
| D-4 | S3 | `addDroppedFiles` 读 `ignoredCount` 并发 `droppedFilesNotice`，`ContentView` 用既有 `NoticeBanner` | 三条：全网页链接⇒0+横幅、混合⇒1+横幅、全成功⇒无横幅 | 横幅在屏样式未拍帧 |
| D-5 | S4 | 给"只加可选字段不升版"补新→旧→新往返用例；边界写进 `migrate` 注释 | 真实写入器产出的 `history.json` 用旧形状解得动、条目不缩水、再读回字段仍在 | — |
| D-6 | S3 | 降采样后在同一后台路径算出**新尺寸** PNG 字节再交给 `StoredImage` | 源码守卫（三条锚点） | 主线程耗时未单独计时（属性能族，本轮预算不做） |
| D-7 | S4 | CI 真的执行在屏探针与帧捕获，报告型起步 | 步骤自身判据：执行数 ≥1、帧数 ≥60 | runner 上这一步会不会挂 —— 见下 |
| D-8 | S4 | 设置侧栏 `sparkles`→`wand.and.stars`，统一描线 | 守卫禁止这组出现实心符号 | 亮暗两态观感需人眼（清单第 6 节） |

**这一轮最该被记住的两件事。**

1. **测量边界随实现移动了**：换成系统表格之后，合成鼠标事件不再能驱动 `NSTableView`
   （`clickedRow` 恒 -1，`isKeyWindow=false` —— xctest 进程拿不到激活）。
   三条原本自动化的行为判据因此失效。处理方式是把判据**拆开**而不是假装还在：
   结构判据留在常规套件，行为判据进手工清单，并新开 R3-D9 记这条缺口。
   同时删掉了 `testRowGesturesFireTheRightActions` —— 它测的"孤立一行 + 行内 Button"按修法③已不存在，
   留着一个永远点不中的壳比没有更坏。
2. **推翻自己上一轮的决定要逐条对账**：R2-02/D-028 当初写"不要整体换成 `List(selection:)`"，
   三条理由里 `.draggable` 的版本下限现在仍然成立（仍然不用它），
   "系统 chrome 改掉帧"被接受（`sidebar-history-dark` 与审计帧差 72.87%，重基线），
   "丢 `dragSelectRange` 语义"不成立（拖选仍是我们的手势）。对账写在 D-033。
   **但这一条随后被真机推翻**（见下面第 3 点）—— 所以"逐条对账"只能保证理由被写下来，
   不能保证结论正确；结论要靠能落到真实容器上的判据。
3. **D-034（用户真机反馈后的更正）**：`List` 会把行内**任何**一处 `.onDrag` 提升成整行拖拽源，
   于是"把手才拖出、行体用来拖选"在系统列表里做不到 —— 从行里任意位置按下都会开拖出会话，
   容器上的 `DragGesture` 再也拿不到那串事件。取舍是**保留整行拖出、删掉拖选**
   （macOS 侧栏本来不做橡皮筋多选），并把 `dragSelectRange` 动作、行位置表、拖选探针一起清干净，
   不留半套死码。这次改动 **0 帧变化**（68 帧逐帧相同，`frame_audit.py diff` 合计 0/68）。
   一句话教训：**源码扫描能钉"写法"，钉不住"AppKit 怎么处理这个写法"** ——
   我当时那条"拖出入口恰好一处且挂在把手上"的守卫在源码层为真、效果层为假，
   于是绿着放过了一个真回归，是用户的双指把闸门补上的。

**一条新的离屏伪影**：`List` 的选中高亮在离屏帧里画成整块黑（文字不可见、缩略图还在），
且黑块精确跟随选中集合（夹具选 3 条 ⇒ 三块黑）⇒ 与 D-025 同族的语义色伪影，不据此判产品。

**D-7 的落地过程本身就是证据**：第一次把它做成一个 `A|B` 的 filter 步骤，推上去后
该步骤在无头 runner 上跑了 19 分钟仍未结束（我取消了那次运行，并给步骤加了 `timeout-minutes`）。
现在拆成"离屏帧捕获"和"在屏交互探针"两步，各 8 分钟上限 —— 挂住时日志要能指名是哪一类跑不动，
否则"CI 的 UI 步骤红了"这句话对下一次判断没有价值。这一步仍是 `continue-on-error`：
在屏探针在 CI 上被 skip 是可接受的结果，不可接受的是"一条都没执行"。

本轮判据（现取，别信这里的数）：`cd ClipboardHistory && swift build && swift test`
→ 实测 0 告警、355 例 / 10 skip / 0 失败；帧 `CLIPBOARD_HISTORY_UI_SHOTS=/tmp/shots swift test --filter UICaptureTests`
→ 68 帧、同代码连拍两次聚合 sha 相同；变异对照 5 组逐一点亮（其中一组第一次因正则没命中而**变异没落地**，
改用 `assert 锚点 in text` 之后才拿到预期的红）。
本轮提交（现取：`git log --oneline -4`）：修复本体、账本 D-033、以及把 CI 的 UI 步骤拆开并加时限的那一次。

## 14. 用户真机反馈补的两条（D-034 / D-035，同一夜）

审计文档里的 8 条改完之后，用户在自己的机器上一试又抓到两条 —— **两条都是自动化闸门放过去的**，
这一事实比这两条缺陷本身更值得记：

1. **拖选**（D-034）：修法③原本「拖出只从行首把手发起」，源码守卫也确实看到 `.onDrag` 只有一处、
   且挂在把手上 —— 但 `List` 会把行内任何一处 `.onDrag` 提升成整行拖拽源，效果层完全是另一回事。
   取舍改成**保留整行拖出、删掉拖选**，并把 `dragSelectRange`、行位置表、拖选探针全部清掉。
2. **图片文件行没有预览**（D-035）：详情区按 URL 现读文件，列表用的是条目的 `thumbnail` 字段，
   而从 Finder 复制文件时剪贴板通常不带图像数据 ⇒ 那一格一直是空的。修法是在 `add` 之后
   后台解一张 ≤256px 缩略图写回并落盘，启动时回填老历史；**夹具补了 `row-file-thumb` 亮暗两帧**
   （68→70，其余 68 帧逐帧不变），因为这条帧集合从来没有包含过「带缩略图的 .file 行」这个形状。

一句话教训：**源码扫描钉得住写法，钉不住 AppKit 怎么处理这个写法；帧集合只覆盖它包含的形状。**
本轮判据（现取）：`swift build` 0 告警 · `swift test` 362 例 / 10 skip / 0 失败 ·
70 帧中 68 帧与上一版逐帧相同 · 变异对照 7 组逐一点亮。


## 15. 第三条真机反馈：点选延迟（D-036）

同一批真机反馈里的第三条，性质和前两条不同 —— 前两条是**闸门放过了真缺陷**，这一条是
**我为了迁就闸门主动改坏了产品**。

用户问："现在点击列表条目到显示为已选择有可感知的延迟，这是bug吗"。是，且是本轮引入的。
D-1 换 `List(selection:)` 后行里没有 `Button` 了，离屏交互探针在**孤立宿主**里测到
`simultaneousGesture(TapGesture(count: 2))` 收不到第二击（`copyFired=0`），我就把手势换成
`.onTapGesture(count: 2)`，并写下一句未经测量的注释："单击选中仍然立刻生效 —— 那是 NSTableView
在 mouseDown 里做的"。实际上 `count: 2` 的识别器要等一个双击间隔才能断定"这只是一次单击"，
而新列表的选中正走这条路径 ⇒ 高亮被推迟一个双击间隔。**注释里的"那是 NSTableView 在做的"
是我猜的，而猜错的那一侧是用户的鼠标。**

改回 `simultaneousGesture`：不参与"谁赢"的仲裁，单击立刻高亮、第二击照常复制。
"点选无延迟"与"双击仍可复制"两条**效果**都只能真机看，写进手工清单 §1 的 1.1 / 1.5（具名）；
自动化这一侧只剩反向守卫 —— 行上再出现 `.onTapGesture(count: 2)` 即红。

规矩（本条唯一值得长期保留的东西）：**任何"为了让某条自动化判据点亮而改产品交互"的动作，
先问那个夹具代不代表真实容器；不代表就只能改判据或转人工，不能改产品。**
这条与 D-034 的"源码为真、效果为假"是同族，但更狠一点：那次是判据测错了层，这次是明知测的是
夹具还去改行为。

还有一层，也是最该记的一层：**这个延迟的答案仓库里早就有**。D-028 原文白纸黑字写着
"双击用 `simultaneousGesture`，**不是** `onTapGesture(count:2)`：后者会让系统为一个可能的双击
先等一个间隔，每次点选都慢半拍"。我在 D-1 换手势时没去读自己那条决定的原文。
对比 D-033 —— 那次推翻 R2-02 前先逐条对账，所以推得有据；这次没对账，于是把账本里已经付过学费的
结论原样推翻。**账本的价值只等于"你真的去查了它"。**

判据（现取）：`swift build --build-tests` 0 告警 · `swift test` **362 例 / 10 skip / 0 失败** ·
`SidebarListSelectionTests` 11 例 · 变异 1 组（换回 `onTapGesture` ⇒ 3 红，还原 `cmp` 逐字节相同）·
离屏帧 **0/70 有变化**。

## 16. 第三轮 15 条改进建议全部落地（2026-10-11 凌晨，D-038…D-043）

目标来自用户那句话：**"根据第三轮审计文档的代码审计/UI/功能各自的五项建议进行更新。自主做，
不要让我进行确认。不能停留在建议阶段。"** 下面这张表是账面结果，每一行都能指到代码、判据与帧。

| 建议 | 做了什么 | 判据在哪 | 账本 |
| --- | --- | --- | --- |
| C-1 管线级验收 | `AGENTS.md` 写死"验收要从产品入口进"，纯函数文件必须自写边界 | `PipelineAcceptanceTests` + 三个文件头上的 `不覆盖管线：` | D-038 |
| C-2 帧基线进 CI | `scripts/frame_baseline.py`（只存 sha256）+ 硬门"少帧" + 报告型"变帧" | `scripts/tests/test_frame_baseline.py` 7 例，含变异对照 | D-043 |
| C-3 存档策略成文 | 老存档缺键读默认值 + 只加可选字段不升版 | `testOldArchiveWithoutNewFieldsLoadsWithDefaults`（真存档删键） | D-038 |
| C-4 运行时启动冒烟 | `CLIPBOARD_HISTORY_DATA_DIR` 隔离 + 真启一次看生命周期日志 | `Round3LaunchIsolationTests` 3 例 + 自测 8 例 | D-042 |
| C-5 Store 只减不加 | 单调指标守卫（最长方法 / 总行数），逻辑外迁成四个纯模块 | `testHistoryStoreStaysThin`（+27 行的变异把它点亮） | D-038 |
| U-1 菜单栏原生语言 | 推荐理由左对齐、把握词替代百分数 | `MenuBarRecommendationsView` 结构判据 | D-038 |
| U-2 拖拽反馈 | 多文件条目现在真能拖出（路径数组表示），解码核对 | `testMultipleFileEntriesCarryEveryPath` | D-040 |
| U-3 通用页再补一项 | 暂停记录 + OCR 开关进「通用」 | `testSettingsPanesExposeTheNewControls` | D-038 |
| U-4 详情排版 | 68ch 可读列（由字体推进推出来）、meta 单行左对齐、搜索命中高亮 | `Round3DetailTypographyTests` 18 例 + 帧 | D-039 |
| U-5 状态语言统一 | `StatePresentation` + `StateLine` 组件统一三处；空态给「清除搜索」 | `Round3StateLanguageTests` 7 例 + 帧 | D-039 |
| F-1 按 App 排除 | 默认挡密码管理器/钥匙串 + 用户名单 + 优先级判据 | `testExcludedAppCopyIsNotRecordedThroughStore`（走 Store） | D-038 |
| F-2 富文本保真 | RTF/HTML 采集→存档→写回，默认关，超限整份丢 | `Round3RichTextTests` 9 例（含命名剪贴板往返） | D-040 |
| F-3 快速选择浮层 | ⌃⌥⇧V 浮层：打字即筛、↑↓、回车粘回原应用、Esc 不动 | `Round3QuickPickTests` 11 例 + 5 条变异 | D-041 |
| F-4 OCR 只索引不落盘 | 识别文本可只在内存，搜索仍命中 | 真值表 + Store 侧写回分支判据 | D-038 |
| F-5 固定与导出导入 | 置顶/豁免清理/行内徽标/批量与单条入口/JSON 导出（图片跳过并计数） | `Round3FeatureTests` 12 例 | D-038 |

**三处刻意偏离审计，都写明了理由，不是漏掉**：

1. **F-3 的默认组合键不是 ⌘⇧V**（D-041）。⌘⇧V 在 Chrome/VS Code/Slack 里是"粘贴并匹配样式"，
   全局注册等于拿别人的功能换一个新功能。改用与本产品同族的 ⌃⌥⇧V，用户可自行录制。
   这一条有变异对照：把默认值改成 ⌘⇧V 会精确点亮"默认组合键漂了"。
2. **F-3 的形状换了，因为 spike 否掉了原前提**（D-041）。审计 §7 明令先 spike"非激活面板能不能接键盘"，
   做了：裸二进制里 `NSApp.activate` 是空操作，激活前后 `isKeyWindow` 都是 false ——
   **两个变体读数相同意味着 spike 没有判别力**，而不是"答案是否"。
   打包成最小 .app 再用 `open` 启动被 `-10825` 拒绝（`lsregister -f` 之后仍然）。
   于是没有赌，改成复用产品里已经跑着、用户今天能立刻打字的那条激活路径。
3. **U-2 没有做自定义 drag image 卡片**（D-040）。系统跟手的剪影就是那一行本身（含预览与缩略图），
   "知道会带走什么"已经被满足；换成自定义图要自起 `NSDraggingSession`，
   而那正是 D-034 被真机否掉的形状。做掉的是真缺的能力：多文件拖出。

另外 U-5 里"macOS 12/13 焦点环改自绘细环"这一半也没做（D-039）：关掉系统环需要
"哪一行有键盘焦点"的信号，`List(selection:)` 不给；在没有替代环之前先删掉唯一的焦点指示，
等于在最老的两个系统版本上把键盘用户丢掉。留成 ready-for-human，需要 12/13 真机。

**判据总量（现取）**：`swift build --build-tests` 0 告警 · `swift test` **430 例 / 10 skip / 0 失败** ·
`python3 -m unittest discover -s scripts/tests` **50 例 OK**（CI 下限从 17 提到 48） ·
`make bundle` 0 告警 · 78 张帧两次捕获逐帧同 sha · 帧基线 `docs/frame_baseline.json` 已入库（78 条）。
本阶段共 **19 条新守卫做过变异对照**，其中 3 条最初是假守卫（判的是类型名/文件名字符串而不是使用处，
或替换文本不完整导致编译错误），加强后才真正点亮。

**仍然没闭合的，列清楚**：

- 需要真机手点的：导出/导入面板、OCR 只索引的端到端、富文本往返、多文件拖出、浮层按键手感
  （`docs/MANUAL_TEST_v1.4.9_round3.md` 批次 2–5 各节）。
- `InstanceGuard` 对"直接 exec 包内二进制"的第二实例疑似漏判（本机实测：用户实例在跑时冒烟仍开出了窗口）。
  我的操作失误是把冒烟跑在了开发机上，已改为本地只用假包，真启动交给 CI 的干净 runner。
- 12/13 的整块蓝色焦点环仍在（见上）。

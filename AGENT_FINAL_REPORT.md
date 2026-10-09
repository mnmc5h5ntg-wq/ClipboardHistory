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

方法：离屏渲染真实视图（`NSWindow` + `NSHostingView` + `cacheDisplay`），不需要屏幕录制授权；由 `CLIPBOARD_HISTORY_UI_SHOTS` 触发，未设置时整组 skip。共 **64 帧**（32 夹具 × 亮/暗）—— 第一轮是 29 夹具 58 帧，第二轮末把菜单栏面板的三个状态补了进来（D-024）。

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
被审对象是 HEAD `81bce8d`。本轮在它之上做了 **46 个提交**（34 个动代码或测试、12 个只动账本；本节的这次改动算在内），全部推送；`swift build` 0 告警、`swift test` **312 例 / 6 skip / 0 失败**、
python 脚本测试 **25 例 OK**、64 帧离屏捕获（第二轮末 58 → 64）。**尚未发布**：线上 Latest 仍是 v1.4.7。

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
swift build && swift test                       # 301 例 / 5 skip / 0 失败
CLIPBOARD_HISTORY_UI_SHOTS=/tmp/shots swift test --filter UICaptureTests          # 64 帧
CLIPBOARD_HISTORY_UI_INTERACTION=1 swift test --filter UIInteractionProbeTests    # 在屏探针（会抢前台）
cd .. && python3 -m unittest discover -s scripts/tests                            # 25 例 OK
python3 scripts/frame_audit.py diff /tmp/A /tmp/B                                 # 逐帧差异
```
账本：`AGENT_STATE.md`（第二轮章节 + 3 段进度快照）、`AGENT_BACKLOG.md`（R2-01…R2-19 + 8 张进度快照）、`AGENT_DECISIONS.md`（本轮 D-015…D-024）、`AGENT_UI_AUDIT.md`（第二轮章节 + 菜单栏面板补拍）。
上面那句"46 个提交"的测法：`git rev-list --count 81bce8d..HEAD`；其中只动 `AGENT_*.md` 的 12 个用逐提交 `git show --name-only` 归类得到。

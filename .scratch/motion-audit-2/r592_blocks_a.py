def block_state(d):
    i = d["ident"]
    m, a = d["main_run"], d["add_run"]

    def step(rk):
        return u"、".join(x.strip() for x in rk.get(u"失败步骤", [])) or u"（没有失败步骤）"

    def preds(rk):
        rows = rk.get(u"预测", [])
        return u"\n".join(u"      · %s ⇒ **%s**\n        （取处：%s）"
                          % (p[0], p[1], p[2]) for p in rows) or u"      ·（没判：那一跑未到数）"

    def skipped_rows(rk):
        got = rk.get(u"skipped 清单", [])
        if not isinstance(got, list):
            return u"      （清单没取到 ⇒ 这一格按未读到处理）"
        if not got:
            return (u"      ·（这一跑没有 skipped 步骤 ⇒ R591 接上的那四步在 runner 上真的出声了；"
                    u"这一格与「没读到清单」是两种不同的账，这里记的是前者）")
        return u"\n".join(u"      · 第③甲 步=%s 名=%s ⇒ 被上游红连带跳过" % (r[0], r[1]) for r in got)

    return u"""## R%(r)s 状态（%(date)s · 第 %(n)s 轮 / Round %(round)s · **产品 %(prodfiles)s 文件**（用户实测反馈的两条：旧记忆压住新默认值 + 仓库根留开发版副本）+ 判据卷 +%(delta)s 格 + 刀 M1582–M1597 全 CAUGHT + ⓪ R591 两跑都到数、四条预测全中 + 换装两次并把用户机上的窗口读到 848×600）

⓪ **现读两对（`ci_status_r592.py`，取值时刻 16:10–16:12 第一趟、19:01 复算同一结论，两跑都 `completed / failure`）**：
   1. `%(mrun)s ↔ %(msha)s`（R591 主笔）⇒ 全部失败步骤：`%(msteps)s`。
      逐步骤结论：`Release script tests ⇒ %(mbat)s`、`Frame baseline vs working manifest ⇒ %(mbase)s`、
      `Surface left-axis ruler ⇒ %(mleft)s`、`Swift tests (executed-count gate) ⇒ %(mswift)s`。
      **R591 那一笔接的线在 runner 上确认生效**：`STEP[9] ⇒ %(mbat)s`（红名逐字 `%(mmisc)s`），
      而 skipped 清单这一跑是空的 —— 那一步的读法见本节③第一条（空清单 ≠ 没取到清单）。
      四条预测（标签与判法逐字接自 R591 的 `PREDICTIONS_R592`，四格齐：主张 / 判法 / 正文从哪一步取 / 这条通道由哪一步印出去）：
%(mpreds)s
      skipped 清单：
%(mskip)s
   2. `%(arun)s ↔ %(asha)s`（R591 补记笔）⇒ `%(astatus)s`；失败步骤：`%(asteps)s`；
      逐步骤结论：`Release script tests ⇒ %(abat)s`、`Frame baseline vs working manifest ⇒ %(abase)s`。
      四条预测与主笔**同判**：
%(apreds)s
      skipped 清单：
%(askip)s
   3. **R591 的接线拿到了它欠的第一证人**：`42179047067` 逐步骤结论里 `STEP[10]`–`[14]` 全部不再是 skipped
      （`Runtime launch smoke` 从 `skipped` 变成 `success`，正文里 `SMOKE_OK=1` 第一次印在 runner 日志上），
      而 skipped 计数从 5 朵降到 **0** 朵 ⇒ 663 那条「被上游红连带」在这一跑上被证实**修好了**，
      不是「大概修好了」。同跑仍红的三朵（`STEP[15]` / `STEP[17]` / `STEP[19]`）与 R590 那两跑**同名同集合**
      ⇒ 不是本笔引入，也不因为「本轮没碰它」就不记账：见本节③的红名清单。
   4. **R593 的 ⓪ 要读的五格**（判法与取处写进 `ci_status_r592.py` 的 `PREDICTIONS_R593`，由脚本判，不许目测对拍）：
      ①本笔（主笔 + 补记笔）的成对号 —— 由补记那一趟现取现写；
      ②`STEP[14]`（Runtime launch smoke）在**含本笔**的那一跑里仍 `success`，且正文里
        `launch_smoke.py "/tmp/时间剪史_bundle/时间剪史.app"` 那一条路径是暂存目录而不是仓库根
        （印不出来说明 `make bundle` 的落点又回去了，不是"CI 又坏了"）；
      ③新硬步骤 `Repo root stays bundle-free after make bundle (BACKLOG 620)` 第一次在 runner 上有读数：
        `REPO_ROOT_BUNDLE_RESULT=ok` 且 `READER_SELFTEST=seen`；若它 `not-run`，结论只能是「构建没落地」，
        不能读成「仓库根干净」；
      ④`STEP[15]`/`[17]`/`[19]` 那三朵红的红名集合与本轮比是**多、少还是同**（本轮动了窗口几何的恢复路径，
        多出来的那一朵要先判是不是本笔引入，判法：拿它对应的判据名在 ⓪ 两跑里现读有没有）；
      ⑤`STEP[9]` 的电池汇总 `Ran <N>` 与本轮台账里那一格比是否 +%(delta)s（判据卷的新格必须在 runner 上被数到，
        本机绿不算交付）。

① **真实推进（产品面 · 规格 §3 第①段的补漏）：旧记忆压住新默认值，一次性抬过去**
   用户 2026-11-06 实测反馈：升级之后两栏不等宽、比例也不是 √2。我在用户机上现读（取值时刻 16:12）：
   `mainWindowExpandedWidth = 750`、`mainWindowCollapsedWidth = 420`（R567 之前的两档默认），
   而 AppKit 还存着窗口帧 `…-AppWindow-1 = "585 368 750 492"` 与分栏子视图帧 `423.5 / 326.5`。
   三样叠起来才是那句「等分没生效」：`width(forKey:fallback:)` 的记忆优先是对的，
   错的是旧规格的默认值还留在盘上 ⇒ 第①段对升级用户**根本没发生过**。
   本轮做的（`MainWindowGeometryMigration`，纯函数 + 一层薄胶水，排在 controller 读状态**之前**）：
   1. 只在记忆值**恰好等于旧默认对**（750 与 420）时抬到 848 / 424；手动调过的落在 `not-legacy-pair`，一律不碰；
      新装落在 `no-legacy-memory`；已经迁过落在 `already-migrated` —— 四档出口都被判据逐字读。
   2. 抬完立刻打版本键（`mainWindowGeometryMigrationVersion`）⇒「只抬一次」有证人，不是散文。
   3. 恢复的窗口帧**不删、只改写宽高**，并按「顶边不动」回算 origin.y ⇒ 用户放的位置逐字保留；
      分栏子视图帧没有可算目标，删掉它，让 `navigationSplitViewColumnWidth` 那条锁等宽约束自己给出 423.5 / 423.5。
   4. **换装之后在用户机上量到第二半没到位**（取值时刻 18:24）：宽度那半成了（848、两栏 423.5 / 424.5），
      窗口却仍是 `848 492` ⇒ 比例 1.72。成因不是键没改写，是 AppKit 的恢复通路除了 defaults 键还看 saved state，
      高度只从后者回来。第一版修法（「迁移那一趟动一次高度」）在**已经打过版本键的机器上永远不会生效** ——
      那一版是错的，被我自己换装量出来了。
      最终落地的是**不变量**而不是补丁：产品从不记高度，而 macOS 13+ 的 `contentAspectRatio` 锁住了比例
      ⇒ 「高度不在 √2 上」这件事只能来自锁出现之前的那一次恢复，所以 `applyGeometry` 见到就抬（`heightLift`，
      容差 0.02；macOS 12 那条锁不存在 ⇒ 那一档不调用，12 上抬它就是抹用户的调整）。
   5. 装完之后同一台机器再读（取值时刻 18:32，AX 现读）：窗口 `848×600`、分栏 `423.5×600 / 424.5×600`、
      `mainWindowExpandedWidth = 848`、版本键 = 1 ⇒ 用户签的那两条验收（两栏等宽、比例≈√2）在真机上是**过**。
   刀：**M1582**（摘掉产品入口那句迁移调用 ⇒ 用户点名的「不做迁移必须红」）、**M1583**（条件放宽成「有记忆值就抬」
   ⇒ 抹掉用户自己调过的宽度）、**M1584**（不打版本键 ⇒ 第二跑又抬）、**M1585**（恢复帧整块不做）、
   **M1586**（不回算顶边 ⇒ 用户的窗口被挪走）、**M1587**（只摘分栏帧那一支）、**M1594**（键匹配放宽成
   「所有 `NSWindow Frame` 键」⇒ 系统面板的键也被改）、**M1595**（判据里的旧默认对不用产品常量 ⇒ 真值表脱钩）、
   **M1596**（摘掉 √2 不变量 ⇒ 恢复的 492 永远留在用户窗口上）、**M1597**（容差写成负数 ⇒ 恒抬，
   把用户等比拖出来的 900×637 抹回 600）。M1585 / M1586 红在**同一格的不同断言**上，判定按红话里的字样分开
   （「宽没抬」对「顶边动了」），不按格子名 —— 这是 663 那一族的老规矩。

② **真实推进（交付面 · BACKLOG 620 结案）：构建产物不再落仓库根**
   用户第二条指令：不要再留仓库根的开发版副本，只保留 /Applications 一份。本轮改的是**落点本身**，不是清理现场：
   1. `Makefile`：`BUNDLE := $(STAGE)/$(APP_NAME).app` —— `bundle` 目标里那条往仓库根的 `ditto` 整段删掉，
      `run` / `dmg` 都改指暂存目录；`clean` 补一行把历史留下的仓库根副本清掉（`make clean` 从此能收拾旧现场）。
   2. `scripts/install_local.sh`：默认包 = 暂存目录那一份；开头加一道预检（仓库根有可执行 .app 就**一步都不许动**），
      并且 `--dest` 不是 /Applications 时**强制不启动**那份副本 —— 从前这一格靠调用方记得传 `--no-launch`，
      而"沙箱不该启动同 id 副本"与"沙箱不该发退出指令"是同一条理由，不该一个有门、一个靠人记。
   3. `scripts/repo_root_bundle.py`（新守卫）：三态 `ok / red / not-run`，**自带正对照**
      （`READER_SELFTEST=seen`：拿一份已知答案的临时根跑同一条扫描，认不出来就 exit 2 ⇒
      runner 上仓库根本来就干净，没有这条对照，「名单=空」就只是「这里没构建过」的同义反复）；
      顺序也是结论的一部分：**红排在 not-run 前面**（刀 M1592 钉这条，第一版我把顺序写反过）。
   4. `.github/workflows/ci.yml`：新增硬步骤 `Repo root stays bundle-free after make bundle (BACKLOG 620)`，
      排在 `make bundle` 之后（那里才有对象可扫）；`Runtime launch smoke` 的冒烟路径从仓库根相对路径改成暂存目录。
   5. 仓库根那份 `时间剪史.app`（11-04 08:33 的构建产物，gitignore 里、不是源码也不是用户数据）已移出仓库
      （`/tmp/r592-removed/`），换装脚本两次都读到 `REPO_ROOT_BUNDLE=absent`。
   刀：**M1588**（Makefile 把落点指回仓库根 ⇒ 配方那一格红）、**M1589**（换装脚本默认包指回仓库根）、
   **M1590**（摘掉「违规就不许装」那一格）、**M1591**（沙箱强制不启动那一支失效）、**M1593**（扫描函数恒空 ⇒ 尺盲要响）。
   **620 结案的另一半不在本笔**：`~/Documents/Codex_Project0_backups/before-*/` 那 20+ 份可启动副本
   要动 LaunchServices 数据库或用户 Documents 才能摘，且回滚分支正靠 `mv` 那一份备份 ⇒ 新开 **664**，本笔不动它。

③ **几朵红各由谁签 + 段②那三问逐问给状态（用户收口时点名要的）**
   · ⓪ 的 skipped：`42179047067` 与 `42179425098` 两跑逐步骤结论里 skipped **0 朵** ⇒ 门（`ci_skipped_causes.py`
     run 模式）本轮没有对象可判；`static` 那一支现读 `%(causes)s` ⇒ 「无声=0」带的是 `证据型=9` 的扫描面。
   · runner 仍红的三朵（两跑同名同集合，**不是本笔引入**；本笔也没碰它们，但照实记账）：
     `STEP[15]` 五朵（`testActionableInkStaysAboveTheLegibilityFloor`、`testCaptionTextStaysOnTheSecondaryTier`、
     `testDetailAreaHasASingleLeftAxis`、`testDetailStatusBarShowsTheRealSourceAppIconOnlyWhenAttributed`、
     `testQuickPickKeyboardHintClearsTheContrastFloor`）、`STEP[17]` 一朵（红名 = 最后那条，与 622/565 那一族同形：
     runner 1x 的对比度）、`STEP[19]` 两朵（`MOTION_FLOOR_SUITE_RED=2`：
     `testDetailEmptyToContentCrossfadeIsMeasuredOrDeclaredBlind`、`testEmptyStateStillFadesWhenMotionIsReduced`）。
     这八条本轮**不计入对账口径**，理由不是"本轮没碰"，是它们都是 runner 侧的机差/采样口径账，
     归 **622 / 565 / 627 / 635** 那些单子；本轮没有新的 runner 红名（判法见 ⓪·④ 第④格，留给 R593）。
   · 段② 第一问（非不透明窗口下侧栏材质会不会变淡）：**Light 档过、Dark 档未验** ——
     证人仍是 R568 那条真机合成通道（撤底衬那臂 0.9339→0.6637、品红漏出 319 颗），
     暗档那一问今天仍没有当轮证人，具名 `TRANSPARENCY_MATERIAL_APPEARANCE_NOT_RUN=Dark档无当轮证人_Light档有R568数`
     一字未撤；三条拿第二档的出路（锁 `.aqua` / 按外观拆两档 / 另一台机器）**仍归用户**，本轮一条没选。
   · 段② 第二问（阴影跟不跟可见形状）：**本机真机通道过、runner 未验** ——
     `TRANSPARENCY_SHADOW 半片透明 左带暗=0.0631 右带暗=0.0017 判=套形状` 是 R568 的数，本轮没有新读数；
     runner 侧 `REALSCREEN_SHADOW_NOT_RUN=env-off` 未撤。
   · 段② 第三问（取证通道分不分得清真黑与透明）：**新通道过、主窗树未验、逐帧产物那一半不过（具名）** ——
     新 alpha 图层通道两档 `分得出=1`（R571/R572 的数，本轮未重测）；主窗树今天没有真透明对象
     `PRODUCT_MAIN_TREE_TRANSPARENT_OBJECT_NOT_JUDGED=backing-covers-whole-tree`；
     356 张产物在写盘前被铺窗口底色 ⇒ D12 那句「透明区 alpha 归零」不能拿产物判（**653** 未结）。
   · ⇒ 三问**没有一条是"本轮新过"**的，第③段着色器本轮未开工：两条具名阻塞一字未撤，
     `STAGE_GATE_CLAIMS` 现读 `%(stage)s` ⇒ 「三问全过」在规格里出现次数仍是 0。
     本轮的真实推进按用户指令排在段②之前：**第①段对升级用户的补漏**（那一半是用户实测出来的真缺口）。
- **红名对账**（口径=对账口径已启用；门报 `%(recon)s`，不由我数）：
  · 红名「换装后用户机窗口仍是 848×492、比例 1.72 ⇒ 用户签的 √2 不过」→ 本节① 第 4 条（本轮内已修并复读到 848×600）
  · 红名「第一版一次性高度补丁在已打版本键的机器上永不生效」→ ⑨·1
  · 红名「帧基线门 `FRAME_BASELINE_CHANGED=16`」→ 本节⑥（控制实验：HEAD 那一跑逐字节同 ⇒ 不是本笔引入）
  · 红名「`testTheSeamInTheRenderedFrameSitsAtHalfTheContentWidth` 在过滤跑里读到 3392x2400 / 缝 1051.0pt」→ ⑨·2
  · 红名「刀 M1590 第一版落下是空刀（PASSED）」→ ⑨·3
  · 红名「判据里 `frame` 与 `contentRect` 两个口径混用（568 / 600 / 732）」→ ⑨·4
  · 红名「我同时起过两趟 `swift test --filter UICaptureTests`」→ ⑨·2（与上面那条假红是同一件事的两个面）
  · 红名「`install_local.sh` 里 `[ "$rc" = 1 ] && fail` 那种 `bash -e` 顶层写法（R591 同族，重犯一次）」→ ⑨·6
  · 红名「台账正文里落出一句半话『…整步先死，这一 ⇒ 中』」→ ⑨·8
  · 红名「写手 --check 停在『M1582 说 CAUGHT 却读不到任何 FAIL 行』」→ ⑨·9

④ **验证链（顺序照派单）**：build `%(build)s` → 判据卷（Swift 侧 `FoldGeometryMigrationTests` 10 格 +
   python 侧 `test_repo_root_bundle` 13 格、`test_install_local` 11 格）→ 刀 M1582–M1597 十六把
   （**落刀前现读高水位=M1581**，跨表唯一性逐把现读 0 次撞号）→ 新表 `mutate_r592_migration` 进预检名册
   （`%(prechecks)s`）→ 刀已还原复跑判据、`%(md5)s`、`git status scripts/` 空、三种变异串各现读 0 处 →
   捕获卷 `%(capture)s`、帧 `%(frames)s` → 本机那一门 `%(gate)s` / 判定 `%(drift)s` / 倍率出口 `%(scale)s` →
   看图（本节⑤）→ 全量 `%(full)s`、skipped `%(fullskip)s` → **换装两次**（`INSTALL_RESULT=ok`、
   `INSTALL_SHA_MATCH=1`、条数 505→505、`INSTALL_SIGNATURE=local`、AX 读到 848×600）→ 七本台账 →
   派生格**落盘之后**现读 → 电池（canonical 配置，不设帧目录；两个时刻都记）。

⑤ **看图那一腿（659 形状：先 `convert("L")` 再 `getbbox`，配同尺寸正对照 + 自己 vs 自己必须 0）**：
%(look)s
   我自己打开看的四张：`detail-0-text-720x520-light`（正文两行、来源行、星标/图钉/复制/删除那一列，
   删除那颗是系统红 —— 都在位，没有截断）、`quickpick-list-420x300-dark`（五行行高一致、时间列右缘对齐、
   底部那行键位提示「↑↓ 选择 · ↩ 粘贴 · Esc 关闭」在暗档读得出）、`cardprobe-groupbox-default-720x140-dark`
   与 `-light`（尺点名要开的那两张：系统分组框那条底与「系统默认内缩」那行字都在，两档都只是那一枚胶囊 + 标题，
   没有整页平涂、也没有多出来的东西）。
   四张都是夹具合成内容，画面里没有用户真实剪贴板原文。
   **本轮产品面不在这批离屏帧的覆盖面里**（改的是窗口恢复几何，帧夹具按固定尺寸建窗）⇒
   那一半的证人只能来自真机 AX 读数（本节① 第 5 条），看图这一腿记的是"没有回归"，不是"推进被看见"。

⑥ **基线与名单**：产品文件 %(prodfiles)s 个（`Sources/…/MainWindowCollapsePolicy.swift`、
   `Sources/…/MainWindowCollapseController.swift`），连续零改动 **%(streaknum)s** 轮（唯一取数口
   `python3 scripts/product_streak.py`，**台账落盘之后**现读 `%(streak)s`；as-of 口径 ⇒ 读作「本轮之前最后一次
   产品改动在 %(streaknum)s 轮前」；本笔落地之后这一列归 0，下一轮的 as-of 就是 0 —— 用户指令「那一格应该回到 0」
   由下一轮的那个数兑现，本轮不替它填；取数时刻由 `post_land()` 钉在函数名字上，不在纪律上〔streak-cell-end〕）。
   帧基线：`%(frames)s` 张，门报 `FRAME_BASELINE_CHANGED=16`（8 张 detail-* + 8 张 quickpick-*，逐字清单在
   `/tmp/r592/baseline.log`；本轮那批帧在 `/tmp/r592v2/frames`，HEAD 对照那批在 `/tmp/r592v3`）。这一格本轮**做了控制实验**：同一台机器、同一份代码树之外，
   在 `HEAD`（`906a875`，没有本笔任何改动）另开一棵 worktree 重捕一遍 ⇒ 那 16 张与本轮捕的**逐字节相同**，
   另抽 8 张未变帧与对照也相同；而本轮这批帧与上一批（R591 那 356 张）也是 356/356 逐字节相同
   ⇒ **这 16 张不是本笔改的，是基线侧的旧账**（`docs/frame_baseline.json` 里那 16 个摘要与这台机器今天的渲染
   不一致，而连续七轮"产品 0 文件 ⇒ 不重捕"让它没人看见）。`update` 一次没跑（重烤归用户），
   开成 **665**；四张按机器登记的表一字未改。

⑦ **闸门与单子（§3 第③段今天仍不开工）**：
   `STAGE2_CLICKTHROUGH_BLOCKED=awaiting-user-mechanism-choice` 与
   `STAGE3_FRAME_CRITERIA_HAVE_NO_RUNNER_WITNESS=awaiting-654-direction` 一字未撤；
   第③段证人现读 `%(stage)s` ⇒ 「三问全过」出现次数仍是 0。
   本轮没有把任何一条 `判=不判 / not-run / skipped / 扫描面 0` 说成"没问题"：
   守卫的 `名单=空` 带 `READER_SELFTEST=seen`、`无声=0` 带 `证据型=9`、skipped 的 0 朵与"没取到清单"分开写、
   基线那 16 张带控制实验而不是"大概没变"。
   仍归用户（一条不代选）：655 / 656 / 657 / 658 / 659 / 660 / 661 / 662 / 663 / 638① / 654 / 646 / 647 / 650 /
   651 / 653 / 644 / 639 / 640 / 637 / 633 / Motion ≥2 帧地板 / SSH 成因 / 手感签字 / **664**（备份那一族的可启动副本）/
   **665**（基线 16 张与这台机器不一致）；
   4.5 墨地板、150 上限、120ms、Motion ≥2、2x 8.0pt、1x 6.0pt、`FLOOR_LIGHT=1.20`、`FLOOR_DARK=1.10`、容差 1.5、
   跳变地板 8、`probeInkFraction=3%%`、`.contentFade` 0.20、`--allow-missing`、四张按机器登记的表、
   既有名册与豁免表、禁碰 14 面 —— 一字未动；`update` 一次没跑；没改这台机器的全局外观；
   **没动用户的 Dock 与登录项**（那条写成人工验收批次 91.1，见本节⑧与 DECISIONS D-%(r)s）；
   帧与日志不含真实剪贴板原文。

⑧ **人工验收批次（本轮新增，见 `docs/MANUAL_TEST_v1.4.9_round3.md` 批次 91）**：
   仓库根那份开发版消失之后，登录项记的那条路径失效 ⇒ 需要用户做一次一次性动作。
   给用户的一句话：**「打开系统设置 → 通用 → 登录与扩展（或「登录项」），把「时间剪史」的「开机启动」
   重新打开一次 —— 现在启动的是 /Applications 那一份。」**
   本轮没有替用户点它（不改用户的 Dock / 登录项是派单里的硬规矩）。

⑨ **自伤（照实，不缩）**：
   1. **第一版的高度修法在真机上是死的**：我把它写成「迁移那一趟动一次高度」，而用户机上版本键**已经**被
      第一次换装打上了 ⇒ 那一支永远不会再触发。是"装完再读一次真窗"（AX 848×492）把它抓出来的，
      不是判据 —— 判据那几格在进程内建窗，永远走不到恢复通路。⇒ 规矩：**改恢复路径的东西必须由真机读数签**，
      本机进程内建窗只能证明"产品自己写的几何"。最终改成不变量（`heightLift`）。
   2. **两趟 `swift test --filter UICaptureTests` 被我同时起过**（一条命令里两个后台任务），
      其间那一格像素尺读到 `帧=3392x2400 缝=1051.0pt` —— 一个不存在的缝。之后串行重跑三次（本轮树两趟、
      HEAD 对照一趟）都读 `1696x1200 / 424.5pt` ⇒ 那个读数是并发污染的假红，不是缺陷。
      ⇒ 「刀/捕获/电池不许并发」这条规矩我本轮自己破了一次；读数只在串行趟里算数。
   3. **刀 M1590 第一版是空刀**（PASSED）：我摘的是 `check_repo_root plan` 那**一次调用**，
      而脚本里构建之后还有第二次调用 ⇒ 门仍然拦、判据仍然绿。改成摘「`rc=1` 就不许装」那一格本身之后才 CAUGHT。
      这是空刀第五种形态的又一实例：**变异打在有两处调用的其中一处**，等于什么都没动。
   4. **口径混用**：新判据第一版把 √2 判在 `contentLayoutRect`（848×568 ⇒ 比 1.493）上，
      又把"第二趟不许动"判在 `window.frame.height` 上（测试窗没有 `fullSizeContentView` ⇒ frame 比 content 多 32pt）
      ⇒ 两格同时红。修法：测试窗与产品那扇同款式，比例一律判在 `contentRect(forFrameRect:)` 那一档，
      并把四个口径一次印出来（`FOLD_UPGRADE_CALIBERS`）。
   5. 台账写手那一趟我一度以为 `ledgers_r592.py` 已经被上一段会话写坏过（"mangled by sed"），
      实际盘上它**根本不存在**、七本台账也没被动过 —— 我先查了 `git status` 才动手。
      ⇒ 记这一条是因为它的形状：把"记忆里的损坏"当成"盘上的事实"，就会去"修"一个不存在的东西。
   6. `install_local.sh` 里我又写了 `[ "$rc" = 1 ] && fail …` 这种 `bash -e` 顶层 AND-list（R591 ⑨·2 同族，第二次），
      以及 `usage()` 的 sed 行号范围没跟着文件头加长 —— 都改成了 `if` 与现读范围。
   7. 备份那一族（620 机制②）我一度顺手写成"装完压成 tar.gz"，落笔前自问回滚分支靠什么 ⇒
      `trap rollback` 要在任何一步失败时把旧包 `mv` 回去，压包就等于扔了退路 ⇒ 撤掉那一半改动，改成开单 664。
   8. **⓪ 那一趟把预测的「主张」截到 78 字**（`spec[u"主张"][:78]`）⇒ 台账里落出半句话
      「…整步先死，这一 ⇒ 中」。这不是排版问题：用户会逐字拿正文对账，而截断把我自己那把尺的原文弄坏了。
      去掉截断并复算那一趟（19:01，四条预测与第一趟同判）⇒ 记这一条是因为它的形状：**读数落盘之前先被格式化截短**，
      和"抄上一轮基线把字段名抄丢"是同族（[[feedback-ledger-writer-hygiene]]）。
   9. **写手自检那条"CAUGHT 却读不到红行"只认 pytest 的 `FAIL:` 形状** ⇒ 本轮 16 把里有 9 把是 Swift XCTest，
      红行长这样 `…Tests.swift:206: error: -[Target testMethod]`，于是**真的红被读成 0 行**、写手停在假警报上。
      改成两种形状都认，且"0 行仍然红"这条不许松（那是通道坏了的证人）。同族教训：尺只认一种写法就等于只扫半个面。

⑩ **通道五读（取值时刻 18:19–18:20）**：码签身份 `%(ident)s`（本笔自己重取，不是引用）；
   push 通道 `%(push)s`；`github.com=%(gh)s`、`api.github.com=%(api)s`；
   `HEAD=%(head)s`、`origin/main=%(origin)s`、`ahead=%(ahead)s`；构建 `%(buildwarn)s`。
""" % {u"r": i[u"r"], u"n": i[u"n"], u"round": i[u"round"], u"date": DATE,
         u"delta": d["delta_total"], u"prodfiles": d["prod_files"],
         u"causes": d["causes"], u"look": d["look"], u"md5": d["md5"], u"build": d["build_warn"],
         u"capture": d["capture"], u"frames": d["frames"], u"gate": d["gate_result"],
         u"drift": d["gate_drift"], u"scale": d["gate_scale"], u"full": d["full"],
         u"fullskip": d["full_skips"], u"recon": d["recon"], u"stage": d["stage_gate"],
         u"prechecks": d["prechecks_brief"],
         u"streak": d["streak"], u"streaknum": (re.search(u"streak=(\\-?\\d+)", d["streak"]).group(1)
                                               if re.search(u"streak=(\\-?\\d+)", d["streak"]) else u"-1"),
         u"mrun": m.get(u"run", ""), u"msha": m[u"sha"], u"msteps": step(m),
         u"mbat": m[u"逐步骤结论"].get(u"Release script tests", u"（读不到）"),
         u"mbase": m[u"逐步骤结论"].get(u"Frame baseline vs working manifest (fixture-set gate)", u"（读不到）"),
         u"mleft": m[u"逐步骤结论"].get(u"Surface left-axis ruler (BACKLOG 234, wired in R210; venv interpreter in R218)", u"（读不到）"),
         u"mswift": m[u"逐步骤结论"].get(u"Swift tests (executed-count gate)", u"（读不到）"),
         u"mmisc": json.dumps(m.get(u"STEP9_红名", u"（未读到）"), ensure_ascii=False)[:120],
         u"mpreds": preds(m), u"mskip": skipped_rows(m),
         u"arun": a.get(u"run", ""), u"asha": a[u"sha"], u"astatus": a.get(u"status行", u"（读不到）"),
         u"asteps": step(a), u"abat": a[u"逐步骤结论"].get(u"Release script tests", u"（读不到）"),
         u"abase": a[u"逐步骤结论"].get(u"Frame baseline vs working manifest (fixture-set gate)", u"（读不到）"),
         u"apreds": preds(a), u"askip": skipped_rows(a),
         u"ident": d["ident_line"], u"push": d["push_line"], u"gh": d["gh_http"], u"api": d["api_http"],
         u"head": d["head_sha"], u"origin": d["origin_sha"], u"ahead": d["ahead"], u"buildwarn": d["build_warn"]}


def block_ui(d):
    i = d["ident"]
    u0 = next_u()
    rows = [
        (u"旧记忆压住新默认值：升级用户看不到第①段，三样叠在一起才是「等分没生效」",
         u"用户机现读 `mainWindowExpandedWidth = 750` / `CollapsedWidth = 420` + 窗口帧 `750 492` + "
         u"分栏帧 `423.5 / 326.5`。记忆优先本身是对的，错的是旧默认值还留在盘上 ⇒ 一次性迁移。"),
        (u"迁移只在「恰好等于旧默认对」时抬，四档出口各有名字",
         u"`legacy-default-pair` / `not-legacy-pair` / `no-legacy-memory` / `already-migrated`；"
         u"手动调过宽度的用户一律不碰（刀 M1583 把条件放宽 ⇒ 那一格必须红）。"),
        (u"「只抬一次」的证人是版本键，不是散文",
         u"抬完打 `mainWindowGeometryMigrationVersion`；判据把「迁完之后再拖回 750/420，第二跑不许再抬」写成格子，"
         u"并配摘掉版本键的正对照（刀 M1584）。"),
        (u"恢复的窗口帧只改宽高、顶边逐字不动",
         u"`restoredFrameString` 按 `y' = (y + h_old) − h_new` 回算；解析不出四个数就返回 nil（不猜 origin）。"
         u"刀 M1586 摘掉回算 ⇒ 用户的窗口被挪走那一格必须红。"),
        (u"分栏子视图帧没有可算目标 ⇒ 删掉它，让锁等宽约束自己给 423.5 / 423.5",
         u"名册里那条 `423.5 / 326.5` 是旧档的不对称；刀 M1587 只摘这一支 ⇒ 「两栏不等宽」那条断言必须红。"),
        (u"宽度那半在真机上成了、高度那半没成 —— 是换装读出来的，不是判据读出来的",
         u"18:24 现读：`mainWindowExpandedWidth = 848`、两栏 423.5 / 424.5，窗口却仍是 `848 492`（比 1.72）。"
         u"进程内建窗的判据永远走不到恢复通路 ⇒ 改恢复路径的东西必须由真机读数签。"),
        (u"最终落地是不变量而不是补丁",
         u"产品从不记高度，13+ 的 `contentAspectRatio` 锁住比例 ⇒ 「高度不在 √2 上」只能来自锁之前的那一次恢复。"
         u"`heightLift` 容差 0.02；macOS 12 没有那条锁 ⇒ 那一档不调用（12 上抬它就是抹用户的调整）。"),
        (u"一次性补丁在已经打过版本键的机器上永远不会生效",
         u"第一版就是这个形状，被第二次换装（AX 读到 848×492）否掉。记进 ⑨·1，不缩。"),
        (u"构建产物不再落仓库根：配方、换装默认值、预检、CI 硬步骤四处同一件事",
         u"`Makefile` 的 `BUNDLE` 进暂存目录；`install_local.sh` 默认包同改并加「仓库根有 .app 就不许装」的预检；"
         u"`ci.yml` 新增硬步骤排在 `make bundle` 之后（那里才有对象可扫）。"),
        (u"守卫必须自带正对照，否则「名单=空」只是「这里没构建过」",
         u"`READER_SELFTEST=seen` 拿已知答案的临时根跑同一条扫描；认不出来就 exit 2 ⇒ 所有按前缀筛出来的 0 都不算数。"),
        (u"顺序也是结论：红不许被 not-run 掩掉",
         u"`judge()` 先判红再判没对象；刀 M1592 把顺序换回去 ⇒ 「真违规被读成没判到」那一格必须红。"),
        (u"沙箱不该启动同 id 副本 —— 与「沙箱不该发退出指令」是同一条理由",
         u"`--dest` 不是 /Applications 时脚本强制 `launch=0`（从前靠调用方记得传 `--no-launch`，"
         u"测试自己传了，所以那一格从来没被判过）。刀 M1591。"),
        (u"帧基线那 16 张：用控制实验分清「本笔改的」与「基线侧的旧账」",
         u"HEAD 另开 worktree 重捕 ⇒ 16/16 逐字节相同，且本轮这批与上一批 356/356 相同 ⇒ 不是本笔引入。"
         u"`update` 一次没跑（重烤归用户），开成 665。"),
        (u"两趟捕获同时跑会造出一条不存在的缝",
         u"并发那一趟像素尺读 `3392x2400 / 缝 1051.0pt`；串行三次（本轮两趟 + HEAD 对照一趟）都是 "
         u"`1696x1200 / 424.5pt` ⇒ 那个数是假红。读数只在串行趟里算数（⑨·2）。"),
        (u"空刀第五种形态：变异打在有两处调用的其中一处",
         u"M1590 第一版摘的是 plan 那一次调用，构建之后还有第二次 ⇒ 门仍然拦、判据仍然绿（PASSED）。"
         u"改成摘「`rc=1` 就不许装」那一格本身才 CAUGHT。"),
        (u"口径要写死在同一个矩形上",
         u"`contentLayoutRect`（568）/ `contentRect(forFrameRect:)`（600）/ `contentView`（600）/ `frame`（600）"
         u"四个口径一次印出来，√2 一律判在 `contentRect` 那一档；测试窗补 `fullSizeContentView` 与产品同款式。"),
        (u"段②三问本轮没有一条新过，两条具名阻塞一字未撤",
         u"第一问 Light 过 / Dark 未验；第二问本机真机通道过 / runner `env-off`；"
         u"第三问新通道过 / 主窗树未验 / 逐帧产物那一半不过（653）。第③段着色器继续不开工。"),
    ]
    body = u"\n".join(u"- **U-%d：%s** —— %s" % (u0 + k, t, b) for k, (t, b) in enumerate(rows))
    head = (u"## 第 %(n)s 轮（R%(r)s · %(date)s · U-%(u0)s…U-%(u1)s）：升级用户看不到第①段 ⇒ 一次性迁移 + √2 不变量；构建产物不再落仓库根"
            % {u"n": i[u"n"], u"r": i[u"r"], u"date": DATE, u"u0": u0, u"u1": u0 + len(rows) - 1})
    return head + u"\n\n" + body + u"\n\n", u0

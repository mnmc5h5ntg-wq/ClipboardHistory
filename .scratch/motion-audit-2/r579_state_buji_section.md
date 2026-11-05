### R578 第二次补记（2026-11-05 · 由 R579 向前补记，已落盘的"未到数"原文一字不改）

① **R578 ① 那一格里"两跑都还 `in_progress`"今天到数了**（那一节里 `@@STATUSMAINOPEN@@`／`@@STATUSBUJIOPEN@@` 那两句是**开场时刻**的真话，原文一字不动，这一条向前补）：两跑现读都是 `completed / failure`；全部失败步骤逐字 —— 主笔 `JOB build-and-test ⇒ failure`、`STEP[15] Swift tests (executed-count gate)`、`STEP[17] Capture gate (unregistered reds must be zero)`、`STEP[19] Motion coverage floor`；补记笔同三条 ⇒ **`STEP[18] On-screen probe coverage floor` 这两跑都绿**（R578 那一节里"五跑三红两绿"那句照实留着，今天这两格是它后面的两格）。红名单是**包含关系**：主笔 5 个 `Test Case … failed` 名字 ⊂ 补记笔 6 个（多的是 `SelectionRevealAnimationTests.testProductDurationRevealStillMovesOverTime`），`只在主笔里出现的 = ∅` ⇒ 只许写"本轮没有新名字"。

② **R578 交接的三格预案，逐格现读 = 都没触发**（这是那一轮欠着的最后一格，今天结掉）：① 1.00x 那一档 `EXPLANATION2 倍率=1.00x 实测=被否_不上屏只走display就建得出而上屏不display建不出 声明=被否_不上屏只走display就建得出而上屏不display建不出 判=与声明一致`（两跑逐字同 ⇒ `EXPLANATION2_NOT_RUN=unregistered-scale` 在这一档消失）；② `@@RUNPREREQ@@` ⇒ 夹具快门那一步在 runner 也 `子层=2`、`同类相符=5/5` ⇒ **不需要把那张表的「前置」那一列按机器拆开**；③ `@@RUNREJUDGED@@` ⇒ `翻面=0 按行声明与快照相符=8/8 快照缺行=0` ⇒ 那份按行独立抄本第一次被第二台机器签。

③ **一条必须写清的区别**（否则下一轮会把两件事读成一件）：R578 做的是**登记动作**（把 1.00x 那一档由那一跑的读数填进抄本），今天到手的是**登记值被那一台自己复校**（`判=与声明一致`）⇒ 前者不需要 runner 同意，后者才是"按机器登记"这条规矩的闭环。⇒ 本轮顺手把这件事做成门：写手现在拿**同一棵树的两跑**互校 `EXPLANATION2`，不一致就 `SystemExit` 拒绝写账 ⇒ "登记值"这一格从此不靠单点读数。

④ **R578 那一句"汇总四个数逐字未动"今天仍然成立**：`@@RUNGATE@@`、`@@RUNMOTION@@`（三跑 `1→1→2` 在漂，那颗 `testDetailEmptyToContentCrossfadeIsMeasuredOrDeclaredBlind` 在 R578 读的两跑日志里也各出现 4 次 ⇒ 不是新面孔）；映射表四个数 runner 与本机逐字同，同一行里 alpha 那三个数仍是机器差 ⇒ 两个口径都照抄、不选。

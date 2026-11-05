### R576 补记（2026-11-05 · 由 R577 那一跑向前补记，已落盘的"未到数"原文一字不改）

① **R576 ① 那一格（"两跑都还没到数 ⇒ 未读"）今天到了一跑、另一跑仍未到**，按规矩只向前补记：
- **到数的是主笔** `41979751613 ↔ ae11a92`（`completed / failure`）⇒ 全部失败步骤逐字：`STEP[15] Swift tests (executed-count gate)`、`STEP[17] Capture gate (unregistered reds must be zero)`、`STEP[19] Motion coverage floor`；`STEP[18] On-screen probe coverage floor` **绿**（整份日志真取到 3,281,881 字节 ⇒ "不在列表里"这次可以当读数）。
- **补记笔 `41980266648 ↔ c013d5d` 现读仍是 `in_progress / conclusion 空` ⇒ 未到数**（不是绿、不是红），本轮不轮询、不拿本机的数顶。
- **R576 ② 那一格的 runner 证人到手，而且登记值没翻**：`@@COLDRUNNER@@`，其中 `树=主窗 倍率=1.00x 实测=层树没建 登记=层树没建 判=与登记一致`、`树=浮层 … 判=与登记一致` ⇒ 那张"按机器登记"的表在**第二台机器上自洽**，本机一字未改（这正是它该有的样子：登记值只由那一跑自己改，而那一跑没给出翻面的读数）。
- **同一跑给出的解释② 处置是 `@@COLDMECHRUNNER@@`** —— 这句话本轮被自己的刀推翻：那一版的甲臂是**夹具那棵树**、乙臂是**判据搭的那棵树**，而且乙臂把"上屏"与"display"两件事捆在一起做 ⇒ 它只能证明"这两步合起来会建出树"，不能证明"等的是上屏"。R577 用一次只动一个自变量的矩阵重测（本机 2x：`乙E 只走 display 不上屏` 有树、`乙D 上了屏而不 display` 没树）⇒ **②被否**。⇒ R576 那一格写的"②未排干"是**诚实的**（它当时确实没排干），而 runner 那句"被支持"是**过度归因**；两处都不回头改，只在这里把新结论接上。
- 其余现读（同一跑）：判据卷 `Executed 230 tests, with 34 tests skipped and 14 failures`（230 = 上轮 229 + R576 新格 ⇒ 那一格在 runner 上真的跑了）、全量 `1437/89/14`、`@@CIGATE@@`、`@@MOTIONFLOOR@@`、`@@UISCANNER@@`、`Ran 725 tests in 115.403s` / `python cases: 725`。
- **红名单归因**：这一跑 6 朵 = `@@REDROSTER@@`；上轮两跑是 8 朵与 7 朵 ⇒ **R576 没给 runner 带来任何新名字**（少掉的两朵都是"有时出现"的样本红：`testDetailEmptyToContentCrossfadeIsMeasuredOrDeclaredBlind`、`testMarkdownModeLabelChangeIsAVisibleProcess`）。这一格只写"没有新红"，不写成"红变少了"。
- **D12 映射表那一行第三次逐字相同**：`@@D12RUNNER@@` ⇒ R575/R576 那句"八条里 0 条能在 runner 上判"继续不改措辞。

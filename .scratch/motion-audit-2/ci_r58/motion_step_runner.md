> 摘自 `gh run view 38576482491 --log`（R58 的 runner 运行，结论 success）的 `Motion filmstrip (report-only)` 与 `Motion coverage floor` 两步，原始行 3010–3260，ANSI 已剥。
> 用途：BACKLOG 86 的证据（第 211 行那句 `testTransitionsAreActuallyRunning'] failed (7.443 seconds).` 与 `motion suite exit: 1`），以及 R57 登记表那句"runner 侧还没有一次带捕获的读数"的更正来源（第 78 行 MOTION_BAND）。

2026-10-14T14:09:18.6390710Z CLIPBOARD_HISTORY_UI_MOTION=1 CLIPBOARD_HISTORY_MOTION_OUT=/tmp/motion-ci \
2026-10-14T14:09:18.6391370Z   swift test --filter MotionFilmstripTests > /tmp/motion.log 2>&1 &
2026-10-14T14:09:18.6391790Z pid=$!
2026-10-14T14:09:18.6392150Z ( sleep 200; kill -9 "$pid" 2>/dev/null ) &
2026-10-14T14:09:18.6392670Z killer=$!
2026-10-14T14:09:18.6392970Z wait "$pid" && status=0 || status=$?
2026-10-14T14:09:18.6393370Z kill "$killer" 2>/dev/null || true
2026-10-14T14:09:18.6393710Z # R56 / BACKLOG 79：**stdout 会整次或大部分消失**。三种现场都见过：
2026-10-14T14:09:18.6394300Z #   · CI run 38543090198 —— 测试全过、9 张胶片写出来了、`print` 的读数一行不剩；
2026-10-14T14:09:18.6394610Z #   · 本机 18:58 那次 —— 同样 0 行；
2026-10-14T14:09:18.6454990Z #   · 本机 19:37 那次（加完文件通道之后的第一遍）—— stdout 只剩 2 行，而文件通道有 56 行。
2026-10-14T14:09:18.6457810Z # 第三种最阴：结论行活着，理由行死了 ⇒ 地板会红在 REASONLESS 上，
2026-10-14T14:09:18.6460230Z # 那是一条"看起来像产品坏了"的假红。所以这里不是"缺了才补"，而是**每次取并集**：
2026-10-14T14:09:18.6464000Z # 两条通道的读数都并进同一份日志。
2026-10-14T14:09:18.6467400Z # 为什么是并集而不是"以文件为准"（本轮先写成后者，改回来了）：
2026-10-14T14:09:18.6468150Z # 文件也可能只写了一半（进程中途死掉），那时 stdout 里活着的行是**唯一**的证据；
2026-10-14T14:09:18.6468960Z # 用"换掉"就会把好数据扔掉。重复则无害 —— 地板取第一条 MOTION_SUMMARY、
2026-10-14T14:09:18.6470310Z # 取最后一条结论行、理由按行收集，同一行出现两次不改变任何判定。
2026-10-14T14:09:18.6470640Z # stderr 侧（`Executed N tests`、红的用例名）只有 XCTest 会打，原样保留 ——
2026-10-14T14:09:18.6470950Z # 地板需要那个 executed 数才能区分"没跑完"与"验得不够"。
2026-10-14T14:09:18.6471230Z readings=/tmp/motion-ci/motion-readings.log
2026-10-14T14:09:18.6474560Z if [ -s "$readings" ]; then
2026-10-14T14:09:18.6475250Z   from_stdout=$(grep -c '^MOTION_' /tmp/motion.log || true)
2026-10-14T14:09:18.6481240Z   cat "$readings" >> /tmp/motion.log
2026-10-14T14:09:18.6483960Z   echo "MOTION_CHANNEL_UNIONED=1 stdout=$from_stdout 文件=$(wc -l < "$readings" | tr -d ' ')"
2026-10-14T14:09:18.6485170Z else
2026-10-14T14:09:18.6486050Z   echo "MOTION_READINGS_FILE_ABSENT=1 只剩 stdout 这一条通道（文件通道没写出来）"
2026-10-14T14:09:18.6486780Z fi
2026-10-14T14:09:18.6487730Z summary=$(grep -m1 'MOTION_SUMMARY' /tmp/motion.log || true)
2026-10-14T14:09:18.6488690Z # 绿不等于"验到了"：R2 之后每条过渡判据都会报"这次到底判了几条、哪几条是 not-run"。
2026-10-14T14:09:18.6490980Z # 少了这一行，一次"3/3 全绿"和一次"1/3 有内容"在 CI 上长得一模一样。
2026-10-14T14:09:18.6492180Z resolve=$(grep -m1 'MOTION_RESOLVE_SUMMARY' /tmp/motion.log || true)
2026-10-14T14:09:18.6494550Z executed=$(grep -oE 'Executed [0-9]+ tests?' /tmp/motion.log | tail -1 | grep -oE '[0-9]+' || true)
2026-10-14T14:09:18.6495580Z strips=$(find /tmp/motion-ci -name '*-strip.png' 2>/dev/null | wc -l | tr -d ' ' || true)
2026-10-14T14:09:18.6496400Z echo "motion suite exit: $status  executed: ${executed:-0}  胶片: ${strips:-0}  ${summary:-无 MOTION_SUMMARY}  ${resolve:-无 MOTION_RESOLVE_SUMMARY（旧版判据：不知道今天判了几条）}"
2026-10-14T14:09:18.6497920Z # 红要能读：**只有退出码的红等于没有红**。这一步是报告型，如果它只留下
2026-10-14T14:09:18.6498350Z # "motion suite exit: 1"，下一次没人知道是哪条判据红、读数是多少（本轮 run 38256846956
2026-10-14T14:09:18.6498820Z # 就是这个形状：exit 1 / executed 12，日志里一个数字都没有）。
2026-10-14T14:09:18.6499150Z # 所以固定把两样东西打出来：① 各条判据自己的读数；② 红的那几条的名字。
2026-10-14T14:09:18.6501280Z # `|| true` 是必需的：grep 没匹配就是 1，而 run 默认 `bash -e`（同一步里已经栽过三次）。
2026-10-14T14:09:18.6501770Z echo "---- 动效读数 ----"
2026-10-14T14:09:18.6502040Z # R58 / BACKLOG 83：这里原来是一份**硬编码前缀白名单**
2026-10-14T14:09:18.6502430Z # （SUMMARY|RESOLVE_SUMMARY|NATIVE|SHIMMER|…）。它的问题是"每一轮新增的读数族都不在里面"：
2026-10-14T14:09:18.6502910Z # R55 的 MOTION_GRAB 与 R57 的 MOTION_BAND 都没进过这份列表，
2026-10-14T14:09:18.6503340Z # 于是 run 38570965657 里"runner 上带捕获到底成没成功"这件事**在日志里没有答案** ——
2026-10-14T14:09:18.6504600Z # 只有 `judged=4/4`，而 4/4 在带捕获之前也是 4/4（R56），两个形状分不开。
2026-10-14T14:09:18.6504930Z # 白名单会随每一轮变旧；"这一共打了多少行"不会。所以改成：先报计数，再全打。
2026-10-14T14:09:18.6505410Z echo "MOTION_LINES=$(grep -cE '^MOTION_' /tmp/motion.log || true)"
2026-10-14T14:09:18.6509490Z grep -E "^MOTION_" /tmp/motion.log | head -120 || true
2026-10-14T14:09:18.6510010Z # R46：**not-run 的理由单独打，且不截断**。上面那个 `head -24` 是 R44 那次
2026-10-14T14:09:18.6513430Z # "掉了一臂却查不到为什么"的直接成因 —— 理由行排在一大堆读数之后，被挤出了控制台，
2026-10-14T14:09:18.6514350Z # 于是 run 38514753036 里 `not-run=notice-banner-dismiss` 在日志上找不到任何解释。
2026-10-14T14:09:18.6514830Z # 闸门（下一步）读的是文件，不受这里影响；这一步负责让人**看见**。
2026-10-14T14:09:18.6515340Z echo "---- not-run 的理由（全量，不截断） ----"
2026-10-14T14:09:18.6515720Z grep -E "MOTION_NOT_RUN=" /tmp/motion.log || true
2026-10-14T14:09:18.6516090Z echo "---- 红的用例 ----"
2026-10-14T14:09:18.6518650Z # 两级过滤而不是一个 ERE：macOS 的 BSD grep 里 `]`（以及 `\]`）在 ERE 中不可靠 ——
2026-10-14T14:09:18.6519160Z # `test[A-Za-z]+'\] failed` 对着真实那行返回 0 命中，而 `grep -F "]' failed"` 命中。
2026-10-14T14:09:18.6520210Z # 这条判据本身由 scripts/tests/test_ci_report_selftest.py 的 motion/failing_test_names 形状钉住。
2026-10-14T14:09:18.6521720Z grep -E "Test Case " /tmp/motion.log | grep -F "]' failed" | sed -E "s/.*Tests\.//; s/ \[/\n/g" | head -12 || true
2026-10-14T14:09:18.6522310Z if [ -z "$executed" ]; then
2026-10-14T14:09:18.6522730Z   echo "MOTION_NOT_RUN=runner-did-not-finish 看门狗在 200s 收掉了进程，这条判据在 CI 上记为未覆盖"
2026-10-14T14:09:18.6524690Z   exit 0
2026-10-14T14:09:18.6526170Z fi
2026-10-14T14:09:18.6526450Z exit "$status"
2026-10-14T14:09:18.6938250Z shell: /bin/bash -e {0}
2026-10-14T14:09:18.6938550Z ##[endgroup]
2026-10-14T14:10:46.1456520Z /Users/runner/work/_temp/e90b8796-0d4e-46d2-b836-904033848b6b.sh: line 29: 13656 Terminated: 15          ( sleep 200; kill -9 "$pid" 2> /dev/null )
2026-10-14T14:10:46.1573530Z MOTION_CHANNEL_UNIONED=1 stdout=61 文件=65
2026-10-14T14:10:46.1822520Z motion suite exit: 1  executed: 37  胶片: 11  MOTION_SUMMARY notice-banner=2 notice-banner-dismiss=3 detail-kind-change=3 empty-state=3  MOTION_RESOLVE_SUMMARY judged=4/4 not-run=-
2026-10-14T14:10:46.1826140Z ---- 动效读数 ----
2026-10-14T14:10:46.1891740Z MOTION_LINES=122
2026-10-14T14:10:46.1943020Z MOTION_GRAB notice-banner-dismiss 帧数=30 抓帧中位=6.0ms 抓帧最慢=18.3ms 视图=760×588pt 像素=760×48px 声明=120ms
2026-10-14T14:10:46.1944020Z MOTION_GRAB notice-banner-dismiss 帧数=30 抓帧中位=6.1ms 抓帧最慢=21.7ms 视图=760×588pt 像素=760×48px 声明=120ms
2026-10-14T14:10:46.1944880Z MOTION_GRAB notice-banner-dismiss 帧数=30 抓帧中位=15.7ms 抓帧最慢=79.2ms 视图=760×588pt 像素=760×588px 声明=120ms
2026-10-14T14:10:46.1952330Z MOTION_GRAB notice-banner-dismiss 帧数=30 抓帧中位=5.1ms 抓帧最慢=14.3ms 视图=760×588pt 像素=760×48px 声明=120ms
2026-10-14T14:10:46.1953050Z MOTION_GRAB notice-banner-dismiss 帧数=30 抓帧中位=12.4ms 抓帧最慢=45.4ms 视图=760×588pt 像素=760×588px 声明=120ms
2026-10-14T14:10:46.1955270Z MOTION_BAND dismiss 带：首尾差=0.738 整窗首尾差=0.226 位置同一性 带vs整窗头=0.000 带vs整窗尾=0.904 ｜ 带：抓帧中位=5.6ms 峰值=0.465 过渡帧数=3 间隔中位=22ms 帧=760x48px ｜ 整窗：抓帧中位=14.1ms 峰值=0.201 过渡帧数=3 间隔中位=22ms 帧=760x588px ｜ 最慢一次抓帧 带=14.3ms 整窗=45.4ms
2026-10-14T14:10:46.1956200Z MOTION_GRAB detail-empty-to-content 帧数=30 抓帧中位=10.3ms 抓帧最慢=62.0ms 视图=760×588pt 像素=760×588px 声明=160ms
2026-10-14T14:10:46.1956880Z MOTION_GRAB detail-empty-to-content 帧数=30 抓帧中位=7.1ms 抓帧最慢=20.0ms 视图=760×588pt 像素=760×588px 声明=160ms
2026-10-14T14:10:46.1957890Z MOTION_DETAIL_AB empty-to-content 开 帧数=1 峰值=0.030 冷闸=true  关 帧数=1 峰值=0.030 采样≈42ms
2026-10-14T14:10:46.1958880Z MOTION_NOT_RUN=opacity-fade-invisible-to-cacheDisplay detail-empty-to-content：开关两臂读数相同 ⇒ 这把尺看不见这条交叉淡，只能记「源码已接、产物未量」
2026-10-14T14:10:46.1959580Z MOTION_GRAB detail-kind-change 帧数=30 抓帧中位=12.9ms 抓帧最慢=38.5ms 视图=760×588pt 像素=760×588px 声明=160ms
2026-10-14T14:10:46.1960170Z MOTION_DETAIL kind-change 采样≈42ms 中点帧=1 带内过渡帧数=2 落定残余=1.000
2026-10-14T14:10:46.1960660Z MOTION_GRAB detail-same-kind 帧数=30 抓帧中位=11.8ms 抓帧最慢=18.8ms 视图=760×588pt 像素=760×588px 声明=0ms
2026-10-14T14:10:46.1964420Z MOTION_DETAIL same-kind 带内过渡帧数=0 落定残余=0.000
2026-10-14T14:10:46.1965610Z MOTION_GRAB_AREA 全视图 面积=480320pt² 样本=9 中位=13.9ms 最慢=19.7ms
2026-10-14T14:10:46.1966680Z MOTION_GRAB_AREA 横幅带 面积=91200pt² 样本=9 中位=6.1ms 最慢=11.5ms
2026-10-14T14:10:46.1967760Z MOTION_GRAB_AREA 小块 面积=18000pt² 样本=9 中位=4.7ms 最慢=6.9ms
2026-10-14T14:10:46.1969140Z MOTION_GRAB heat-first-record 帧数=30 抓帧中位=2.2ms 抓帧最慢=210.5ms 视图=430×250pt 像素=430×250px 声明=160ms
2026-10-14T14:10:46.1970800Z MOTION_GRAB heat-first-record 帧数=30 抓帧中位=2.0ms 抓帧最慢=154.1ms 视图=430×250pt 像素=430×250px 声明=160ms
2026-10-14T14:10:46.1972220Z MOTION_GRAB heat-first-record 帧数=30 抓帧中位=2.3ms 抓帧最慢=161.7ms 视图=430×250pt 像素=430×250px 声明=160ms
2026-10-14T14:10:46.1973780Z MOTION_GRAB heat-first-record 帧数=30 抓帧中位=2.2ms 抓帧最慢=5.5ms 视图=430×250pt 像素=430×250px 声明=160ms
2026-10-14T14:10:46.1975640Z MOTION_HEAT_RUNS 开A [469–652@0.059/粗168] 开B [544–748@0.059/粗195] 关 [489–525@0.219/粗36]  跨度A=183ms 跨度B=204ms 整卷中位=30ms
2026-10-14T14:10:46.1977780Z MOTION_HEAT_FADE_A/B 预热 时长=259ms 帧数=2 开A 时长=183ms 帧数=2 开B 时长=204ms 帧数=2 峰值=0.059  关 时长=36ms 帧数=1 峰值=0.219  整卷中位=30ms 声明=160ms 冷闸=true 判定=钟太粗
2026-10-14T14:10:46.1982500Z MOTION_NOT_RUN=clock-coarse-in-window heat-first-record：峰值那一段内部最粗的一次采样是 168 / 195ms，而这条过渡声明 160ms ⇒ 今天的钟粗到既不能说看得见也不能说看不见（条带图见 CLIPBOARD_HISTORY_MOTION_OUT） ｜A 臂 归因=grab-dominates（解释=92%：抓帧 154ms 是大头，但还有 14ms 不是它） ⇒ 缩捕获区域是主杠杆，而剩下的 14ms 得另查（BACKLOG 76 那条分段时间轴） ｜B 臂 归因=grab-dominates（解释=83%：抓帧 162ms 是大头，但还有 33ms 不是它） ⇒ 缩捕获区域是主杠杆，而剩下的 33ms 得另查（BACKLOG 76 那条分段时间轴）
2026-10-14T14:10:46.1986050Z MOTION_GRAB list-insert-new-record 帧数=30 抓帧中位=12.4ms 抓帧最慢=26.0ms 视图=760×588pt 像素=760×588px 声明=0ms
2026-10-14T14:10:46.1989530Z MOTION_CUT list-insert-new-record 带内过渡帧数=1 落定残余=0.000 逐帧=[0.458 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000]
2026-10-14T14:10:46.1991830Z MOTION_GRAB notice-banner 帧数=30 抓帧中位=5.1ms 抓帧最慢=19.0ms 视图=760×588pt 像素=760×48px 声明=150ms
2026-10-14T14:10:46.1994030Z MOTION_CUT_CONTROL notice-banner 采样≈29ms 中点帧=2 落定残余=0.979
2026-10-14T14:10:46.1995810Z MOTION_SELFTEST_A01725E8
2026-10-14T14:10:46.1996530Z MOTION_SELFTEST_A01725E8-2
2026-10-14T14:10:46.1997360Z MOTION_NATIVE row-insert 开 帧数=3 峰值=0.057 采样≈33ms
2026-10-14T14:10:46.1998480Z MOTION_NATIVE row-insert 关 帧数=1 峰值=0.067 采样≈29ms
2026-10-14T14:10:46.2004600Z MOTION_NOT_RUN=app-not-active：NSTableView 不在激活的 App 里不跑行动画
2026-10-14T14:10:46.2005490Z MOTION_NATIVE row-move 开 帧数=1 峰值=0.053 采样≈33ms
2026-10-14T14:10:46.2005870Z MOTION_NATIVE row-move 关 帧数=1 峰值=0.053 采样≈33ms
2026-10-14T14:10:46.2006740Z MOTION_NATIVE_MOVE 判定=瞬移 峰值容差=0.020（同一卷的 insert 读数在上一行：insert 能看见多帧 ⇒ 通道不瞎）；这一行只说读数怎么读，产品结论要过下面两道 skip 才算
2026-10-14T14:10:46.2007470Z MOTION_NOT_RUN=app-not-active：NSTableView 不在激活的 App 里不跑行动画
2026-10-14T14:10:46.2007990Z MOTION_SEQUENCE 选中没变 帧数=3 峰值=0.038
2026-10-14T14:10:46.2008370Z MOTION_SEQUENCE 选中变了 帧数=1 峰值=0.246
2026-10-14T14:10:46.2011940Z MOTION_NOT_RUN=app-not-active：NSTableView 不在激活的 App 里不跑行动画
2026-10-14T14:10:46.2012440Z MOTION_SHIMMER 扫 帧数=22 变化帧对=0 峰值=0.000 采样≈110ms
2026-10-14T14:10:46.2014110Z MOTION_SHIMMER 停 变化帧对=0 峰值=0.000
2026-10-14T14:10:46.2015510Z MOTION_NOT_RUN=runner-cannot-observe-gradient-motion 对照臂峰值=0.0000 帧数=24
2026-10-14T14:10:46.2017010Z MOTION_GRAB notice-banner 帧数=30 抓帧中位=6.4ms 抓帧最慢=19.7ms 视图=760×588pt 像素=760×48px 声明=150ms
2026-10-14T14:10:46.2018570Z MOTION_SETTLE banner-in 到位帧=4 采样≈28ms ⇒ 实测落定≈112ms（声明 150ms；R58 起量的是整条带，不再套第二层框）
2026-10-14T14:10:46.2020870Z MOTION_GRAB row-favorite-star 帧数=30 抓帧中位=12.0ms 抓帧最慢=25.9ms 视图=760×588pt 像素=760×588px 声明=0ms
2026-10-14T14:10:46.2022310Z MOTION_GRAB row-favorite-star 帧数=30 抓帧中位=14.4ms 抓帧最慢=31.0ms 视图=760×588pt 像素=760×588px 声明=0ms
2026-10-14T14:10:46.2026450Z MOTION_SYMBOL row-star 开 帧数=1 峰值=0.227
2026-10-14T14:10:46.2027390Z MOTION_SYMBOL row-star 关 帧数=1 峰值=0.227
2026-10-14T14:10:46.2028820Z MOTION_GRAB notice-banner 帧数=30 抓帧中位=4.9ms 抓帧最慢=21.5ms 视图=760×588pt 像素=760×48px 声明=150ms
2026-10-14T14:10:46.2031400Z MOTION_AB notice-banner 曲线关闭 采样≈33ms 过渡帧数=1 逐帧=[0.000 0.000 0.000 0.739 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000]
2026-10-14T14:10:46.2032240Z MOTION_CONTROL 计数方块 帧数=19 峰值=0.027 变化帧对=16
2026-10-14T14:10:46.2032650Z MOTION_CONTROL 渐变端点 帧数=21 峰值=0.000 变化帧对=0
2026-10-14T14:10:46.2033140Z MOTION_GRAB blank 帧数=30 抓帧中位=10.9ms 抓帧最慢=15.2ms 视图=760×588pt 像素=760×588px 声明=0ms
2026-10-14T14:10:46.2033530Z MOTION_BLANK frames=30 峰值=0.0000 过渡帧数=0
2026-10-14T14:10:46.2034020Z MOTION_GRAB notice-banner 帧数=30 抓帧中位=4.3ms 抓帧最慢=18.4ms 视图=760×588pt 像素=760×48px 声明=150ms
2026-10-14T14:10:46.2034710Z MOTION_GRAB notice-banner-dismiss 帧数=30 抓帧中位=5.5ms 抓帧最慢=13.7ms 视图=760×588pt 像素=760×48px 声明=120ms
2026-10-14T14:10:46.2035750Z MOTION_GRAB detail-kind-change 帧数=30 抓帧中位=10.6ms 抓帧最慢=19.3ms 视图=760×588pt 像素=760×588px 声明=160ms
2026-10-14T14:10:46.2036340Z MOTION_GRAB empty-state 帧数=30 抓帧中位=4.0ms 抓帧最慢=20.6ms 视图=380×548pt 像素=380×548px 声明=160ms
2026-10-14T14:10:46.2037190Z MOTION_SUMMARY notice-banner=2 notice-banner-dismiss=3 detail-kind-change=3 empty-state=3
2026-10-14T14:10:46.2037650Z MOTION_RESOLVE_SUMMARY judged=4/4 not-run=-
2026-10-14T14:10:46.2038260Z MOTION_GRAB notice-banner-dismiss 帧数=30 抓帧中位=6.0ms 抓帧最慢=18.3ms 视图=760×588pt 像素=760×48px 声明=120ms
2026-10-14T14:10:46.2038900Z MOTION_GRAB notice-banner-dismiss 帧数=30 抓帧中位=6.1ms 抓帧最慢=21.7ms 视图=760×588pt 像素=760×48px 声明=120ms
2026-10-14T14:10:46.2039550Z MOTION_GRAB notice-banner-dismiss 帧数=30 抓帧中位=15.7ms 抓帧最慢=79.2ms 视图=760×588pt 像素=760×588px 声明=120ms
2026-10-14T14:10:46.2040290Z MOTION_GRAB notice-banner-dismiss 帧数=30 抓帧中位=5.1ms 抓帧最慢=14.3ms 视图=760×588pt 像素=760×48px 声明=120ms
2026-10-14T14:10:46.2041010Z MOTION_GRAB notice-banner-dismiss 帧数=30 抓帧中位=12.4ms 抓帧最慢=45.4ms 视图=760×588pt 像素=760×588px 声明=120ms
2026-10-14T14:10:46.2042020Z MOTION_BAND dismiss 带：首尾差=0.738 整窗首尾差=0.226 位置同一性 带vs整窗头=0.000 带vs整窗尾=0.904 ｜ 带：抓帧中位=5.6ms 峰值=0.465 过渡帧数=3 间隔中位=22ms 帧=760x48px ｜ 整窗：抓帧中位=14.1ms 峰值=0.201 过渡帧数=3 间隔中位=22ms 帧=760x588px ｜ 最慢一次抓帧 带=14.3ms 整窗=45.4ms
2026-10-14T14:10:46.2042950Z MOTION_GRAB detail-empty-to-content 帧数=30 抓帧中位=10.3ms 抓帧最慢=62.0ms 视图=760×588pt 像素=760×588px 声明=160ms
2026-10-14T14:10:46.2043690Z MOTION_GRAB detail-empty-to-content 帧数=30 抓帧中位=7.1ms 抓帧最慢=20.0ms 视图=760×588pt 像素=760×588px 声明=160ms
2026-10-14T14:10:46.2044360Z MOTION_DETAIL_AB empty-to-content 开 帧数=1 峰值=0.030 冷闸=true  关 帧数=1 峰值=0.030 采样≈42ms
2026-10-14T14:10:46.2045170Z MOTION_NOT_RUN=opacity-fade-invisible-to-cacheDisplay detail-empty-to-content：开关两臂读数相同 ⇒ 这把尺看不见这条交叉淡，只能记「源码已接、产物未量」
2026-10-14T14:10:46.2045960Z MOTION_GRAB detail-kind-change 帧数=30 抓帧中位=12.9ms 抓帧最慢=38.5ms 视图=760×588pt 像素=760×588px 声明=160ms
2026-10-14T14:10:46.2046490Z MOTION_DETAIL kind-change 采样≈42ms 中点帧=1 带内过渡帧数=2 落定残余=1.000
2026-10-14T14:10:46.2047100Z MOTION_GRAB detail-same-kind 帧数=30 抓帧中位=11.8ms 抓帧最慢=18.8ms 视图=760×588pt 像素=760×588px 声明=0ms
2026-10-14T14:10:46.2047580Z MOTION_DETAIL same-kind 带内过渡帧数=0 落定残余=0.000
2026-10-14T14:10:46.2048060Z MOTION_GRAB_AREA 全视图 面积=480320pt² 样本=9 中位=13.9ms 最慢=19.7ms
2026-10-14T14:10:46.2048610Z MOTION_GRAB_AREA 横幅带 面积=91200pt² 样本=9 中位=6.1ms 最慢=11.5ms
2026-10-14T14:10:46.2049010Z MOTION_GRAB_AREA 小块 面积=18000pt² 样本=9 中位=4.7ms 最慢=6.9ms
2026-10-14T14:10:46.2049580Z MOTION_GRAB heat-first-record 帧数=30 抓帧中位=2.2ms 抓帧最慢=210.5ms 视图=430×250pt 像素=430×250px 声明=160ms
2026-10-14T14:10:46.2050140Z MOTION_GRAB heat-first-record 帧数=30 抓帧中位=2.0ms 抓帧最慢=154.1ms 视图=430×250pt 像素=430×250px 声明=160ms
2026-10-14T14:10:46.2050890Z MOTION_GRAB heat-first-record 帧数=30 抓帧中位=2.3ms 抓帧最慢=161.7ms 视图=430×250pt 像素=430×250px 声明=160ms
2026-10-14T14:10:46.2051530Z MOTION_GRAB heat-first-record 帧数=30 抓帧中位=2.2ms 抓帧最慢=5.5ms 视图=430×250pt 像素=430×250px 声明=160ms
2026-10-14T14:10:46.2052690Z MOTION_HEAT_RUNS 开A [469–652@0.059/粗168] 开B [544–748@0.059/粗195] 关 [489–525@0.219/粗36]  跨度A=183ms 跨度B=204ms 整卷中位=30ms
2026-10-14T14:10:46.2053600Z MOTION_HEAT_FADE_A/B 预热 时长=259ms 帧数=2 开A 时长=183ms 帧数=2 开B 时长=204ms 帧数=2 峰值=0.059  关 时长=36ms 帧数=1 峰值=0.219  整卷中位=30ms 声明=160ms 冷闸=true 判定=钟太粗
2026-10-14T14:10:46.2058460Z MOTION_NOT_RUN=clock-coarse-in-window heat-first-record：峰值那一段内部最粗的一次采样是 168 / 195ms，而这条过渡声明 160ms ⇒ 今天的钟粗到既不能说看得见也不能说看不见（条带图见 CLIPBOARD_HISTORY_MOTION_OUT） ｜A 臂 归因=grab-dominates（解释=92%：抓帧 154ms 是大头，但还有 14ms 不是它） ⇒ 缩捕获区域是主杠杆，而剩下的 14ms 得另查（BACKLOG 76 那条分段时间轴） ｜B 臂 归因=grab-dominates（解释=83%：抓帧 162ms 是大头，但还有 33ms 不是它） ⇒ 缩捕获区域是主杠杆，而剩下的 33ms 得另查（BACKLOG 76 那条分段时间轴）
2026-10-14T14:10:46.2061620Z MOTION_GRAB list-insert-new-record 帧数=30 抓帧中位=12.4ms 抓帧最慢=26.0ms 视图=760×588pt 像素=760×588px 声明=0ms
2026-10-14T14:10:46.2064320Z MOTION_CUT list-insert-new-record 带内过渡帧数=1 落定残余=0.000 逐帧=[0.458 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000]
2026-10-14T14:10:46.2065600Z MOTION_GRAB notice-banner 帧数=30 抓帧中位=5.1ms 抓帧最慢=19.0ms 视图=760×588pt 像素=760×48px 声明=150ms
2026-10-14T14:10:46.2066150Z MOTION_CUT_CONTROL notice-banner 采样≈29ms 中点帧=2 落定残余=0.979
2026-10-14T14:10:46.2066550Z MOTION_SELFTEST_A01725E8
2026-10-14T14:10:46.2066800Z MOTION_SELFTEST_A01725E8-2
2026-10-14T14:10:46.2067180Z MOTION_NATIVE row-insert 开 帧数=3 峰值=0.057 采样≈33ms
2026-10-14T14:10:46.2067540Z MOTION_NATIVE row-insert 关 帧数=1 峰值=0.067 采样≈29ms
2026-10-14T14:10:46.2067990Z MOTION_NOT_RUN=app-not-active：NSTableView 不在激活的 App 里不跑行动画
2026-10-14T14:10:46.2068350Z MOTION_NATIVE row-move 开 帧数=1 峰值=0.053 采样≈33ms
2026-10-14T14:10:46.2068760Z MOTION_NATIVE row-move 关 帧数=1 峰值=0.053 采样≈33ms
2026-10-14T14:10:46.2069280Z MOTION_NATIVE_MOVE 判定=瞬移 峰值容差=0.020（同一卷的 insert 读数在上一行：insert 能看见多帧 ⇒ 通道不瞎）；这一行只说读数怎么读，产品结论要过下面两道 skip 才算
2026-10-14T14:10:46.2069870Z MOTION_NOT_RUN=app-not-active：NSTableView 不在激活的 App 里不跑行动画
2026-10-14T14:10:46.2070300Z MOTION_SEQUENCE 选中没变 帧数=3 峰值=0.038
2026-10-14T14:10:46.2070590Z MOTION_SEQUENCE 选中变了 帧数=1 峰值=0.246
2026-10-14T14:10:46.2070980Z MOTION_NOT_RUN=app-not-active：NSTableView 不在激活的 App 里不跑行动画
2026-10-14T14:10:46.2071360Z MOTION_SHIMMER 扫 帧数=22 变化帧对=0 峰值=0.000 采样≈110ms
2026-10-14T14:10:46.2071850Z MOTION_SHIMMER 停 变化帧对=0 峰值=0.000
2026-10-14T14:10:46.2072410Z MOTION_NOT_RUN=runner-cannot-observe-gradient-motion 对照臂峰值=0.0000 帧数=24
2026-10-14T14:10:46.2072890Z MOTION_GRAB notice-banner 帧数=30 抓帧中位=6.4ms 抓帧最慢=19.7ms 视图=760×588pt 像素=760×48px 声明=150ms
2026-10-14T14:10:46.2073530Z MOTION_SETTLE banner-in 到位帧=4 采样≈28ms ⇒ 实测落定≈112ms（声明 150ms；R58 起量的是整条带，不再套第二层框）
2026-10-14T14:10:46.2101490Z MOTION_GRAB row-favorite-star 帧数=30 抓帧中位=12.0ms 抓帧最慢=25.9ms 视图=760×588pt 像素=760×588px 声明=0ms
2026-10-14T14:10:46.2102310Z MOTION_GRAB row-favorite-star 帧数=30 抓帧中位=14.4ms 抓帧最慢=31.0ms 视图=760×588pt 像素=760×588px 声明=0ms
2026-10-14T14:10:46.2102930Z MOTION_SYMBOL row-star 开 帧数=1 峰值=0.227
2026-10-14T14:10:46.2103380Z MOTION_SYMBOL row-star 关 帧数=1 峰值=0.227
2026-10-14T14:10:46.2104400Z MOTION_GRAB notice-banner 帧数=30 抓帧中位=4.9ms 抓帧最慢=21.5ms 视图=760×588pt 像素=760×48px 声明=150ms
2026-10-14T14:10:46.2105360Z MOTION_AB notice-banner 曲线关闭 采样≈33ms 过渡帧数=1 逐帧=[0.000 0.000 0.000 0.739 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000 0.000]
2026-10-14T14:10:46.2106470Z MOTION_CONTROL 计数方块 帧数=19 峰值=0.027 变化帧对=16
2026-10-14T14:10:46.2106800Z MOTION_CONTROL 渐变端点 帧数=21 峰值=0.000 变化帧对=0
2026-10-14T14:10:46.2107320Z MOTION_GRAB blank 帧数=30 抓帧中位=10.9ms 抓帧最慢=15.2ms 视图=760×588pt 像素=760×588px 声明=0ms
2026-10-14T14:10:46.2107760Z MOTION_BLANK frames=30 峰值=0.0000 过渡帧数=0
2026-10-14T14:10:46.2108370Z MOTION_GRAB notice-banner 帧数=30 抓帧中位=4.3ms 抓帧最慢=18.4ms 视图=760×588pt 像素=760×48px 声明=150ms
2026-10-14T14:10:46.2109100Z MOTION_GRAB notice-banner-dismiss 帧数=30 抓帧中位=5.5ms 抓帧最慢=13.7ms 视图=760×588pt 像素=760×48px 声明=120ms
2026-10-14T14:10:46.2109760Z MOTION_GRAB detail-kind-change 帧数=30 抓帧中位=10.6ms 抓帧最慢=19.3ms 视图=760×588pt 像素=760×588px 声明=160ms
2026-10-14T14:10:46.2110450Z MOTION_GRAB empty-state 帧数=30 抓帧中位=4.0ms 抓帧最慢=20.6ms 视图=380×548pt 像素=380×548px 声明=160ms
2026-10-14T14:10:46.2111020Z ---- not-run 的理由（全量，不截断） ----
2026-10-14T14:10:46.2112470Z /Users/runner/work/ClipboardHistory/ClipboardHistory/ClipboardHistory/Tests/ClipboardHistoryAppTests/MotionFilmstripTests.swift:2721: -[ClipboardHistoryAppTests.MotionFilmstripTests testNativeRowAnimationIsVisibleToTheRuler] : Test skipped - MOTION_NOT_RUN=app-not-active：这一卷是在非激活进程里抓的，AppKit 本来就不跑行动画 ⇒ 不能据此判产品没动
2026-10-14T14:10:46.2114580Z /Users/runner/work/ClipboardHistory/ClipboardHistory/ClipboardHistory/Tests/ClipboardHistoryAppTests/MotionFilmstripTests.swift:2721: -[ClipboardHistoryAppTests.MotionFilmstripTests testNativeRowMoveIsVisibleToTheRuler] : Test skipped - MOTION_NOT_RUN=app-not-active：这一卷是在非激活进程里抓的，AppKit 本来就不跑行动画 ⇒ 不能据此判产品没动
2026-10-14T14:10:46.2116580Z /Users/runner/work/ClipboardHistory/ClipboardHistory/ClipboardHistory/Tests/ClipboardHistoryAppTests/MotionFilmstripTests.swift:2721: -[ClipboardHistoryAppTests.MotionFilmstripTests testRowAnimationSurvivesTheSelectionUpdateThatFollowsIt] : Test skipped - MOTION_NOT_RUN=app-not-active：这一卷是在非激活进程里抓的，AppKit 本来就不跑行动画 ⇒ 不能据此判产品没动
2026-10-14T14:10:46.2118680Z /Users/runner/work/ClipboardHistory/ClipboardHistory/ClipboardHistory/Tests/ClipboardHistoryAppTests/MotionFilmstripTests.swift:2759: -[ClipboardHistoryAppTests.MotionFilmstripTests testSkeletonSweepActuallySweeps] : Test skipped - MOTION_NOT_RUN=runner-cannot-observe-gradient-motion：对照臂读不到任何位移 ⇒ 环境测不了，不判产品
2026-10-14T14:10:46.2120050Z MOTION_NOT_RUN=opacity-fade-invisible-to-cacheDisplay detail-empty-to-content：开关两臂读数相同 ⇒ 这把尺看不见这条交叉淡，只能记「源码已接、产物未量」
2026-10-14T14:10:46.2121650Z MOTION_NOT_RUN=clock-coarse-in-window heat-first-record：峰值那一段内部最粗的一次采样是 168 / 195ms，而这条过渡声明 160ms ⇒ 今天的钟粗到既不能说看得见也不能说看不见（条带图见 CLIPBOARD_HISTORY_MOTION_OUT） ｜A 臂 归因=grab-dominates（解释=92%：抓帧 154ms 是大头，但还有 14ms 不是它） ⇒ 缩捕获区域是主杠杆，而剩下的 14ms 得另查（BACKLOG 76 那条分段时间轴） ｜B 臂 归因=grab-dominates（解释=83%：抓帧 162ms 是大头，但还有 33ms 不是它） ⇒ 缩捕获区域是主杠杆，而剩下的 33ms 得另查（BACKLOG 76 那条分段时间轴）
2026-10-14T14:10:46.2123160Z MOTION_NOT_RUN=app-not-active：NSTableView 不在激活的 App 里不跑行动画
2026-10-14T14:10:46.2123550Z MOTION_NOT_RUN=app-not-active：NSTableView 不在激活的 App 里不跑行动画
2026-10-14T14:10:46.2124010Z MOTION_NOT_RUN=app-not-active：NSTableView 不在激活的 App 里不跑行动画
2026-10-14T14:10:46.2124700Z MOTION_NOT_RUN=runner-cannot-observe-gradient-motion 对照臂峰值=0.0000 帧数=24
2026-10-14T14:10:46.2125410Z MOTION_NOT_RUN=opacity-fade-invisible-to-cacheDisplay detail-empty-to-content：开关两臂读数相同 ⇒ 这把尺看不见这条交叉淡，只能记「源码已接、产物未量」
2026-10-14T14:10:46.2126970Z MOTION_NOT_RUN=clock-coarse-in-window heat-first-record：峰值那一段内部最粗的一次采样是 168 / 195ms，而这条过渡声明 160ms ⇒ 今天的钟粗到既不能说看得见也不能说看不见（条带图见 CLIPBOARD_HISTORY_MOTION_OUT） ｜A 臂 归因=grab-dominates（解释=92%：抓帧 154ms 是大头，但还有 14ms 不是它） ⇒ 缩捕获区域是主杠杆，而剩下的 14ms 得另查（BACKLOG 76 那条分段时间轴） ｜B 臂 归因=grab-dominates（解释=83%：抓帧 162ms 是大头，但还有 33ms 不是它） ⇒ 缩捕获区域是主杠杆，而剩下的 33ms 得另查（BACKLOG 76 那条分段时间轴）
2026-10-14T14:10:46.2128090Z MOTION_NOT_RUN=app-not-active：NSTableView 不在激活的 App 里不跑行动画
2026-10-14T14:10:46.2128650Z MOTION_NOT_RUN=app-not-active：NSTableView 不在激活的 App 里不跑行动画
2026-10-14T14:10:46.2129480Z MOTION_NOT_RUN=app-not-active：NSTableView 不在激活的 App 里不跑行动画
2026-10-14T14:10:46.2130770Z MOTION_NOT_RUN=runner-cannot-observe-gradient-motion 对照臂峰值=0.0000 帧数=24
2026-10-14T14:10:46.2131260Z ---- 红的用例 ----
2026-10-14T14:10:46.2131810Z MotionFilmstripTests testTransitionsAreActuallyRunning]' failed (7.443 seconds).
2026-10-14T14:10:51.2497820Z ##[error]Process completed with exit code 1.
﻿2026-10-14T14:10:51.2650340Z ##[group]Run set -o pipefail
2026-10-14T14:10:51.2651760Z set -o pipefail
2026-10-14T14:10:51.2652560Z python3 scripts/motion_floor_gate.py /tmp/motion.log \
2026-10-14T14:10:51.2653580Z   --expectations scripts/motion_floor_expectations.json
2026-10-14T14:10:51.3052870Z shell: /bin/bash -e {0}
2026-10-14T14:10:51.3053820Z ##[endgroup]
2026-10-14T14:10:51.5462880Z MOTION_FLOOR_FACTS judged=4/4 executed=37 not-run=- summary=detail-kind-change=3 empty-state=3 notice-banner=2 notice-banner-dismiss=3
2026-10-14T14:10:51.5470720Z MOTION_FLOOR_OK=4/4 全部臂都在登记之内
2026-10-14T14:10:51.5471340Z MOTION_FLOOR_REDS=0
build-and-test	Release script tests	﻿2026-10-14T14:10:51.5549230Z ##[group]Run python3 -m unittest discover -s scripts/tests -v 2>&1 | tee /tmp/py.log
build-and-test	Release script tests	2026-10-14T14:10:51.5550030Z python3 -m unittest discover -s scripts/tests -v 2>&1 | tee /tmp/py.log
build-and-test	Release script tests	2026-10-14T14:10:51.5550430Z grep -q "OK" /tmp/py.log
build-and-test	Release script tests	2026-10-14T14:10:51.5550920Z executed=$(grep -oE 'Ran [0-9]+ tests' /tmp/py.log | tail -1 | grep -oE '[0-9]+')
build-and-test	Release script tests	2026-10-14T14:10:51.5551330Z echo "python cases: $executed"
build-and-test	Release script tests	2026-10-14T14:10:51.5551750Z test "$executed" -ge 48
build-and-test	Release script tests	2026-10-14T14:10:51.5588190Z shell: /bin/bash -e {0}
build-and-test	Release script tests	2026-10-14T14:10:51.5588620Z ##[endgroup]
build-and-test	Release script tests	2026-10-14T14:10:52.1177980Z test_a_crash_without_assertion_lines_still_has_a_name (test_ci_capture_gate.CaptureGateExitCodeTests.test_a_crash_without_assertion_lines_still_has_a_name)
build-and-test	Release script tests	2026-10-14T14:10:52.1182850Z 只有结论行的那种红（崩溃 / 超时）不许被当成"一条红都没有"。 ... ok
build-and-test	Release script tests	2026-10-14T14:10:52.1184900Z test_a_log_without_cases_is_a_failure_not_a_pass (test_ci_capture_gate.CaptureGateExitCodeTests.test_a_log_without_cases_is_a_failure_not_a_pass) ... ok
build-and-test	Release script tests	2026-10-14T14:10:52.1192310Z test_a_missing_log_is_a_failure_not_a_pass (test_ci_capture_gate.CaptureGateExitCodeTests.test_a_missing_log_is_a_failure_not_a_pass) ... ok
build-and-test	Release script tests	2026-10-14T14:10:52.1236730Z test_exit_codes_on_the_three_ways_this_step_can_be_wrong (test_ci_capture_gate.CaptureGateExitCodeTests.test_exit_codes_on_the_three_ways_this_step_can_be_wrong) ... ok
build-and-test	Release script tests	2026-10-14T14:10:52.1237850Z test_help_runs (test_ci_capture_gate.CaptureGateExitCodeTests.test_help_runs)
build-and-test	Release script tests	2026-10-14T14:10:52.1243160Z `--help` 必须 0（`test_script_help_runs.py` 会替全仓库的脚本问这一句）。 ... ok
build-and-test	Release script tests	2026-10-14T14:10:52.1245430Z test_registered_not_run_is_not_a_red (test_ci_capture_gate.CaptureGateExitCodeTests.test_registered_not_run_is_not_a_red) ... ok
build-and-test	Release script tests	2026-10-14T14:10:52.1248270Z test_the_headers_own_prose_does_not_become_a_red (test_ci_capture_gate.CaptureGateFixtureTests.test_the_headers_own_prose_does_not_become_a_red)
build-and-test	Release script tests	2026-10-14T14:10:52.1264710Z 夹具头部注释里写着"`error: -[类 方法]`"这种形状 —— 它不许被当成红。 ... ok
build-and-test	Release script tests	2026-10-14T14:10:52.1266640Z test_the_numbers_behind_the_swift_floors_are_the_ones_in_the_log (test_ci_capture_gate.CaptureGateFixtureTests.test_the_numbers_behind_the_swift_floors_are_the_ones_in_the_log)
build-and-test	Release script tests	2026-10-14T14:10:52.1269730Z Swift 侧那两条新地板（0.85 / 0.5）是照这份日志写的 —— 数字要能在这份日志里查到。 ... ok
build-and-test	Release script tests	2026-10-14T14:10:52.1271560Z test_the_real_runner_log_is_caught_as_one_named_red_case (test_ci_capture_gate.CaptureGateFixtureTests.test_the_real_runner_log_is_caught_as_one_named_red_case)
build-and-test	Release script tests	2026-10-14T14:10:52.1280330Z 正对照：那份**真被吞过**的日志必须判红，并且要能指名是谁。 ... ok
build-and-test	Release script tests	2026-10-14T14:10:52.1281150Z test_the_summary_line_counts_assertions_not_cases (test_ci_capture_gate.CaptureGateFixtureTests.test_the_summary_line_counts_assertions_not_cases)
build-and-test	Release script tests	2026-10-14T14:10:52.1290530Z 口径：`Executed 28 tests, with 8 tests skipped and 4 failures` 里那个 4 是**断言**条数。 ... ok
build-and-test	Release script tests	2026-10-14T14:10:52.1300320Z test_the_verdict_tally_is_the_one_in_the_log (test_ci_capture_gate.CaptureGateFixtureTests.test_the_verdict_tally_is_the_one_in_the_log) ... ok
build-and-test	Release script tests	2026-10-14T14:10:56.8865000Z test_report_only_steps_always_print_their_numbers (test_ci_report_selftest.CIReportSelfTest.test_report_only_steps_always_print_their_numbers) ... ok
build-and-test	Release script tests	2026-10-14T14:10:56.8871730Z test_every_step_declares_run_or_uses_with_the_same_indent (test_ci_workflow_shape.CiWorkflowShapeTests.test_every_step_declares_run_or_uses_with_the_same_indent) ... ok
build-and-test	Release script tests	2026-10-14T14:10:56.8873120Z test_hard_gates_are_distinguishable_from_report_only_steps (test_ci_workflow_shape.CiWorkflowShapeTests.test_hard_gates_are_distinguishable_from_report_only_steps) ... ok
build-and-test	Release script tests	2026-10-14T14:10:56.8874380Z test_step_names_do_not_contain_an_unquoted_colon_space (test_ci_workflow_shape.CiWorkflowShapeTests.test_step_names_do_not_contain_an_unquoted_colon_space) ... ok
build-and-test	Release script tests	2026-10-14T14:10:56.8875700Z test_the_steps_that_were_added_to_close_audit_items_are_still_here (test_ci_workflow_shape.CiWorkflowShapeTests.test_the_steps_that_were_added_to_close_audit_items_are_still_here) ... ok

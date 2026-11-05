## R583 状态（2026-11-06 · 第 582 轮 / Round 580 · 产品 0 文件 + **一扇门补上了它看不见的量**（`frame_baseline.py check` 的 changed/added 两态从"没人判"变成"逐张登记否则红"，登记名册 `docs/frame_drift_registry.json` 是**可数的账**）+ 电池测试 +10 格（该卷 12→22）+ 刀 3 把 M1532/M1533/M1534 全 CAUGHT + **一条机键成因量成逐字读数并开单 657**（大小写那半是 Swift/Foundation 侧产生的，不是 python）· 靶 = 折叠规格 §3 第②段 / BACKLOG **655** 那个"变帧没人判"的洞 + 派单 ③ 那一问）

① ** 两跑：开场都判未到数、台账之前**两跑都到数** ⇒ 两句都要写，只许向前补。**
- 开场现读（取值时刻=本轮 ⓪ 第一步）：`42066364877 ↔ dbd13fb`、`42066695864 ↔ 876bd3a` 两跑 `status=in_progress`、`conclusion` 空 ⇒ **两格都未到数**；同一时刻 `api=200`、`github=200`、`ahead=0`、`HEAD=origin/main=876bd3a`、`git ls-remote origin HEAD` 通。⚠ 没轮询、没拿本机的数顶、没把"每一步 conclusion 也全空"读成"没有失败步骤"，也没对进行中的作业去取日志。
- 台账之前复核（取值时刻=写手 `--apply` 之前；`ci_status_r583.py` 现读落盘）：主笔 `@@STATUS_MAIN@@` ⇒ 失败步骤 `@@STEPS_MAIN@@`；补记笔 `@@STATUS_BUJI@@` ⇒ `@@STEPS_BUJI@@`。红名单：主笔 `@@NAMES_MAIN@@` / 补记笔 `@@NAMES_BUJI@@`。
- **派单 ④ 那条"解包顺序先验一次"本轮真的做了**（上一轮我把 `conclusion` 当 sha 对拍）：`@@FIELDS_ORDER@@` ⇒ 三条待验形状的反查建立在这个自检之后。
- 三条待验形状（⑴ 判=一致 / ⑵ 判=翻了 / ⑶ 那一行命中 0 次＝通道没跑，**三者修法相反，不许并成一句**）由脚本反查：`@@CONTINGENCY_HIT3@@`；`@@CONTINGENCY_MISSED3@@`。登记那一格在两跑上的状态：`@@REGISTRY_RUNNER@@`。
- 硬规矩第三次照抄：材质那臂两跑逐字 `@@MATERIAL_RUNNER@@` / `@@MATERIAL_RUNNER2@@` ⇒ **「runner 在跑」不等于「runner 是 Light」**，656 的出路丙仍然没拿到。
- 其余逐字：活门 `@@GATE_RUNNER@@`、注入正对照 `@@PROBE_RUNNER@@`、映射表 `@@D12_MAP_RUNNER@@`、捕获门 `@@GATE_MAIN@@`、动效门 `@@MOTION_MAIN@@` 与地板格 `@@MOTION_FACTS@@`（`executed=` 先读）。`STEP[18]` 的正文只在整跑日志里：`@@PROBE18_MAIN@@` / `@@PROBE18_BUJI@@`。
- **本轮新门在 ⓪ 那两跑上必然一行都没有**：`@@FRAME_GATE_NOTE@@`。
- push 通道本轮现读：`@@PUSH_CHANNEL@@`；`api=@@API_CODE@@`、`github=@@GITHUB_CODE@@`（HTTP 状态码口径），`@@GH_OK@@`。

② **本轮真实推进 = 把"基线门不判 CHANGED"这个洞补上，并且把登记做成可数的账而不是措辞。**
- ⑴ **洞是真的，而且是我上轮自己读到的**：`check` 那一支写的是 `return 1 if missing else 0`（脚本注释原话"多帧与变帧交给人判断"）⇒ `changed` 与 `added` **两态谁都不判**。本机那 8 张变帧从 R577 起连续四轮逐字相同地挂在 `FRAME_BASELINE_CHANGED=8` 上，退出码一直是 0 ⇒ "门绿"被读成"八张已签收"是**这句读法错了**，不是有人偷懒。
- ⑵ **三态现在各自有数、各自有人判**：`@@FRAME_GATE_TOTAL@@`；判定行逐字 `@@FRAME_DRIFT@@`，结论行 `@@FRAME_RESULT@@`。规则：`changed`/`added` 里每一张都必须在名册里有一行（`kind` 对得上、`reason` 与 `ticket` 都不许为空），否则 **门退 1**；`missing` 保持原来"按名字赦免"的形状（`--allow-missing` 一字未动）。
- ⑶ **反证是同一条命令换一侧跑**：把名册路径指向不存在的文件 ⇒ `@@FRAME_DRIFT_ABSENT@@` ⇒ 退 1。⇒ "补上的是判定不是措辞"这句话由这两次读数对拍，不由我保证。
- ⑷ **登记是账**：名册 8 行逐字抄进 BACKLOG 655 的 R583 追记（帧名 + 理由 + 归哪张单 + 登记轮次），并打印 `已登记=8`；`已登记` 那一格由 `judge_drift` 从"changed∪added 里被登记的那部分"派生，**不是名册行数**（电池里有一格专门钉这个：登记 1 张而实际漂 2 张 ⇒ `registered=1`、`unregistered=['d.png']`）。
- ⑸ **名册自己会腐烂的三种形状也接上了**：拼错的帧名（既不对应当前变帧也不对应任何基线帧）⇒ 红；理由或单号为空 ⇒ 红；名册读不出来（非 JSON / rows 不是列表 / `kind` 不认识）⇒ **退 2**，不许降级成"0 条登记"再判绿或判红。⚠ **陈旧行只报数、不判**，理由写进代码注释与电池：漂移是**按机器**的（本机这 8 张在 runner 一张都不漂），把"这台机器此刻不漂"判红等于逼人在两台机器之间来回删行。电池里那一格故意断言"陈旧行**不**红"，哪天有人顺手把它判红，会先在那里红一次。
- ⑹ **三条不许照办**：`frame_baseline.py update` 一次都没跑（重烤基线归用户，655 三条出路原样）；没调任何阈值/容差（本轮没有"变帧容差"这种东西，界值是**有没有登记**，不是差多少个像素）；没把这一格改成就近具名 skip（`check` 现在三态都判，缺席那一态仍按名字赦免）。
- ⑺ **刀 M1532/M1533/M1534**（现读最高 M1531 ⇒ 从 M1532 起，没借号）：`@@KNIVES@@`。
- ⑻ **派单 ③ 那一问量成了读数，而且答案不在 python 侧**：`@@MACHINEKEY@@` ⇒ 同一次会话里 raw `gethostname()` 从 Swift 调也打 `MacBook-Air.local`，而 `ProcessInfo.hostName` 与 `Host.current().name` 都给 `macbook-air.local`，且 `lowercased(raw)` 与它逐字相等 ⇒ **小写那半是 Foundation 自己做的**，python 的 `platform.node()`/`socket.gethostname()` 与 shell `hostname` 都是原样大小写。按字节 join 会错的有**三份名册**：`scripts/motion_floor_gate.py` 的 `machine_key()`（动效地板按机器登记/退役用它，skip 名册也 import 它）、`scripts/tests/test_surface_left_axes.py` 里那份（含写死的 `local:MacBook-Air.local` 常量）、以及本轮 Swift 侧那份 `shapeScanMachineKey()`。⇒ 具名 `MACHINE_KEY_CASE_DIVERGENT` 开成 **BACKLOG 657**，**没有自行统一**（动 python 那份会牵动 354 那一族已按机器登记好的红名单）。

③ **台账与同族自伤（派单 ④ 专项）**：
- ⑴ **重放之前先逐本现读"本轮标题/编号出现几次"**，六个数抄进收口报告（不拿"fail-fast 没写脏盘"当证人 —— 那只能证明崩得早，不能证明没重）。本轮的现读时刻=写手 `--apply` 之前，见 ⑦ 那一格。
- ⑵ **锚串字面形式本轮一次都没打进正文**（上一轮 ⑨·8 那一族的直接后果）：所有"某一节标题长什么样"的描述都改成中文说形状；写手的唯一性检查在插入前后各数一次，两次都得是 1。
- ⑶ **电池那一格仍然不回填**：写手落盘之后本机那一趟的数只进收口报告，最终签字归 runner `STEP[9]`。
- ⑷ **⑨ 对账由门报出**：`红名 @@RED_NAMES@@ 条 / 计入行 @@RED_JIU_ROWS@@ / 编号去重 @@JIU_COUNT@@ / 不计入 @@RED_EXEMPT@@ / 未标（对不上）@@RED_EXTRA@@`，口径=`@@RED_REGIME@@`，落盘后门的复算行 `@@RECON@@`。

④ **闸门与不代选**：三问未全过 ⇒ **第③段着色器一字不写**；`STAGE3_FRAME_CRITERIA_HAVE_NO_RUNNER_WITNESS=awaiting-654-direction` 照旧等用户对 654 的定向；646/650/651/653/654/655/656 **没有一条被自宣结案**（655 本轮只把"没人判"改成"有人判 + 逐张登记"，**没有**替用户选那三条出路）；`PRODUCT_MAIN_TREE_TRANSPARENT_OBJECT_NOT_JUDGED` 不撤；656 三条出路一条没选，没改这台机器的全局外观、没锁 `window.appearance`、没把 `品红漏出>0` 改成 `=0`、没改成 skip；647 甲/乙、653 两条出路、644、639、640、Motion ≥2、633 人工回执、折叠"完成"的手感签字、SSH 三次读数不一致的成因（本轮未复现≠不存在）**全数归用户**；**新增一条**：两份 `machine_key` 的大小写要不要统一（657）归用户。
- 本轮**没有**放宽任何东西：`--allow-missing` 两帧原样；名册不是"容差"而是逐张账；`条=8` 分母、三张登记表（含上一轮新启用的 `D12_SHAPE_SCAN_REGISTRY`）、`d12RowCategoriesR577`、判法四分支、三条预案语义、红名对账口径（只管未来、不许关）**一字未动**。

⑤ **地基一字不动**：4.5 墨、150、2x 8.0pt、1x 6.0pt、120ms 与容差 1、Motion ≥2、`probeInkFraction=3%`、`.contentFade 0.20`、像素格容差 1.5 与跳变地板 8、声明时长、全量 skipped（现读 `@@FULLSKIPPED@@`）；禁碰 **14 面不抬也不降**（本轮没碰捕获侧的 Swift 代码，但判据卷照跑 ⇒ 当轮逐字证人 `@@GROUND_WITNESS@@`）；产品 `@@PRODUCT_FILE_COUNT@@` 文件（`git diff --name-only` 现读派生）；文档本轮 `@@DOC_CELL@@`（本轮的推进在**工具与门**那一侧，规格里没有新的观感事实要写；改文档只许纯插入这条规矩照旧）。

⑥ **上一轮那八处自伤本轮逐条避开并给对账证人**：针腐烂 ⇒ 本轮没改任何被刀引用的 Swift 函数（刀全打在 python 上），预检 `bad=0` 现读；ASCII 双引号包 CJK ⇒ **本轮又犯了两次**（一次在 python 源码、一次在 JSON 值里），都在 `py_compile`/`json.load` 之前抓到，见 ⑨·2/⑨·3；`| head` 截断 ⇒ 刀链输出全部落 status 文件与日志文件，没接 head；`rc=$?` ⇒ 刀脚本用 `proc.returncode` 直取，且写手现在要求 **CAUGHT 必须 rc 非 0**（`rc=0 且 caught=1` 判成矛盾）；撞锁 ⇒ 本轮三支预检与捕获卷**串行**，刀链因为打在 python 上所以与 swift 构建不撞（见 ⑦）；锚字面形式 ⇒ 见 ③⑵；port 锚计数 ⇒ **本轮仍错两处**（见 ⑨·4）；解包顺序 ⇒ 见 ① 那一格的自检。numstat 现读（代码 `@@CODE_CELL@@`，删除行逐行看过）、写手 fill 覆盖每一本 + 返回前回读 token=0、派生格补丁排在 `--apply` 之前 —— 都沿用上一版修好的形状。

⑦ **验证链（顺序未换；一处偏差照实写）**：`swift build --build-tests` 告警 **0**（本轮没改 Swift，构建是 no-op）；判据 filter 绿；**三把刀先跑**——它们打在 `scripts/frame_baseline.py` 上、与 swift 构建目录无关，所以没有撞锁风险，而捕获卷随后才起（偏差具名 `KNIVES_BEFORE_CAPTURE_PYTHON_ONLY`，理由与后果写在这里，不是漏记）；判据卷 `@@CAPTURE_LINE@@`（`@@CAPTURE_SECS@@s`）；帧重捕 + 对新门 `@@FRAMES@@`（**没跑 update**，八张逐字保留）；真机键那一趟 `@@FORENSICS_LINE@@`（那一朵就是 656 那格，照实不抹）；全量 `@@FULL@@`（`@@FULL_SECS@@s`）；三支预检**串行** `@@NEEDLES@@`、`@@ARM_TOTAL@@`、`@@HIDDEN@@`；换装 `SKIP_INSTALL=no-product-change`；电池排在七本台账与派生格之后，本机那一趟的数**不回填** ⇒ 最终签字归 runner `STEP[9]`。产品面连续零改动 **@@STREAK@@** 轮（台账落盘之后现读 `python3 scripts/product_streak.py` ⇒ `@@STREAK_LINE@@`）；清账 @@CLEARING@@；对账门 @@RECON@@；`SOURCES` 格 `@@SOURCES@@`；**台账落盘那一刻**现读 `ahead=@@AHEAD@@`、HEAD=origin/main=`@@HEAD_SHA@@`（带时刻：本轮那两笔是在这句之后落地并 push 的，成对号写进补记，不回头改这一格）。

⑧ **看图那一腿（本轮真看了，逐张）**：@@SHOTS_SEEN@@

⑨ **本轮自伤清单（六处，每处都带代价；对账口径见下面那一格）**：
· **对账口径**（沿用 R582 启用的那一格，本轮不关）：每一条具名红 / 具名不判 / 作废读数要么落到 `⑨·` 编号，要么写 `不计入对账口径` 并带三类名字之一（契约名 / 通道未跑 / 基名在漂）；两者都不写 = **未标**，由 `scripts/red_name_reconciliation.py` 报出并退 1。
- ⑨·1 **把占位文字当成读数**：`ci_status_r583.py` 第一版的分支写的是 `elif registry:` ⇒ 未到数时那一格的内容是"未取（那一跑未到数）"，**也是非空字符串** ⇒ 三条待验形状被判成"新形状"。跑完读那一行才发现。⇒ 规矩：**分支必须先问"那一行到底在不在"（按通道串前缀判），再问它说什么**；占位文字与读数的区别不是空不空，是**有没有前缀**。代价=一次取数重跑 + 一次措辞重写。（这一条与派单 ① 那句"三者修法相反不许并成一句"是同一处：判错分支就会按错的处置办。）
- ⑨·2 **Python 源码里用 ASCII 双引号包 CJK 短语**（`print(... 不许当"没有登记" ...)`）⇒ `py_compile` SyntaxError。同一族从 R579 起记到第 **十** 次，而且本轮开工时派单 ④ 刚写过这条 ⇒ 记进 ⑨，不再写进"规矩"。代价=一次返工（没跑过任何一次真判据）。
- ⑨·3 **同一族在 JSON 里再炸一次**：登记名册的字符串值里打了 ASCII 双引号 ⇒ `json.load` 直接失败。⇒ 形状推广一句：**这条规矩不属于"python 源码"，属于"任何被解析成字符串的字面"**（JSON/Swift 字面量/shell 都算）。代价=一次重写名册。
- ⑨·4 **port 写手时锚又错两处**：① 我按"上一轮我改过的文案"去锚 `print('ITERATION 已经有 Round 579 …')`，而上一轮那句 print **我根本没改**（只改了守卫 token）⇒ `want=1 got=0`；② 我在补丁里发明了一个不存在的助手 `regrab()`。⇒ 规矩补一句：**port 之前先把锚在盘上数一遍**（本轮数了，但数的是"我以为的上一版"，不是"盘上那一版"）；两处都是 fail-fast，`ledgers_r583.py` 一次没被写脏。代价=两回返工。
- ⑨·5 **旧断言被推翻时，测试夹具跟着一起烂**：`test_allow_missing_only_absolves_the_named_frames` 用**假哈希**写基线（`{"a.png": "1"}`），在新语义下那等于凭空造出 2 张变帧 ⇒ 那一格红。红的是我的夹具，不是产品，也不是新门判错。处置=改用 `collect()` 的真哈希，只留"缺席"那一态；**没有**把判定改回去。代价=一次返工。
- ⑨·6 **合成 setup 让两态混在一起**：第一版 `setup()` 的基线里有 `c.png` 而 frames 里没有 ⇒ 那一格同时有 changed 与 missing，"只测一态"的断言其实测了两态。处置=setup 用真哈希、只让 `b.png` 不同 ⇒ 只剩变帧。代价=一次返工 + 一次"陈旧行"那格重写。
- **红名对账**（口径=沿用启用；三个数由门的实现数出来，不在写手里抄第二份规则）：
  · 红名「`CONTINGENCY_HIT` 被占位文字判成「新形状」」→ ⑨·1
  · 红名「`py_compile SyntaxError`（python 源码里的 ASCII 引号）」→ ⑨·2
  · 红名「`json.load` 失败（名册字符串值里的 ASCII 引号）」→ ⑨·3
  · 红名「写手 port 的 `ANCHOR-MISS want=1 got=0` 两回」→ ⑨·4
  · 红名「旧测试用假哈希 ⇒ 新门凭空看到 2 张变帧而红」→ ⑨·5
  · 红名「setup 同时有 changed 与 missing ⇒ 那一格测了两态」→ ⑨·6
  · 红名「`FRAME_BASELINE_RESULT=red 拦路=8（未登记8）`（名册缺席那一侧）」→ **不计入对账口径**（契约名 —— 这是本轮**故意造出来**的反证读数，它证明门在判，不是缺陷也不是自伤）
  · 红名「真机键那一趟那 1 朵（`品红漏出>0` 那一格）」→ **不计入对账口径**（契约名，656 已具名，照实在账上不抹）
  · 红名「`REALSCREEN_MATERIAL_NOT_RUN=env-off`（两跑逐字）」→ **不计入对账口径**（通道未跑 —— 不证"runner 是 Light"）
  · 红名「`D12_SHAPE_SCAN_REGISTRY` 在 ⓪ 两跑上"未取（未到数）"」→ **不计入对账口径**（通道未跑 —— 与"命中 0 次"是两种不同的没有）
  · 红名「`MOTION_FLOOR_SUITE_RED=2` 与 `judged=4/5 executed=79`」→ **不计入对账口径**（基名在漂，R555/R561 那一族，本轮没推进它也不抹）
  · 红名「runner 那 5 个基名红（两跑逐字同集合）」→ **不计入对账口径**（基名在漂 —— 「没有新名字」成立，「红变少了」不成立）
  ⇒ **红名 @@RED_NAMES@@ 条 / 计入行 @@RED_JIU_ROWS@@ / 编号去重 @@JIU_COUNT@@ / 不计入 @@RED_EXEMPT@@ / 对不上（未标）@@RED_EXTRA@@ 条**。

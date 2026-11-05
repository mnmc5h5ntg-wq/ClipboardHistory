**657 开单（R583）：两份 `machine_key` 的**大小写**不是同一支机器 —— 成因量成四通道逐字读数，统一与否归用户**
    本单是上一轮具名 `MACHINE_KEY_CASE_DIVERGENT` 的正式单子。R583 把它从"两条字符串不同字"量成**哪一段代码在改大小写**（同一次会话、同一台机器，取值时刻=本轮中段）：raw `gethostname()` 从 Swift 调 = `MacBook-Air.local`；`ProcessInfo.hostName` = `macbook-air.local`；`Host.current().name` = `macbook-air.local`；`lowercased(raw)` = `macbook-air.local`（与 Foundation 给的值**逐字相等**）；python `platform.node()` 与 `socket.gethostname()` = `MacBook-Air.local`；shell `hostname` = `MacBook-Air.local`；`scutil --get ComputerName` = `子懿的MacBook Air`（含中文与空格 ⇒ **绝不能当键**）；`scutil --get LocalHostName` = `MacBook-Air`。⇒ **小写那半是 Foundation 的 `hostName`/`Host.name` 自己做的**，不是 python 侧改了大小写，也不是 shell。
    按字节 join 会错的**三份名册**（逐字列在这里，将来统一时要一起看）：① `scripts/motion_floor_gate.py:201` 的 `"local:" + platform.node()` —— 动效地板的按机器登记/退役（同文件 257、517 两处调用）与 `scripts/tests/test_skip_roster.py:231` import 的那一份都是它（那里有电池钉住"不许退回 hostname 自造一套"）；② `scripts/tests/test_surface_left_axes.py:141` 的另一份实现，外加同文件 129 行**写死的常量** `local:MacBook-Air.local`；③ Swift 侧本轮新写的 `shapeScanMachineKey()`（`"local:" + ProcessInfo.hostName` ⇒ 小写）。⇒ 前两份互相同字、第三份差大小写 ⇒ **同一台机器在两份名册里是两台**。
    三条出路与代价（**工作侧一条都没选**）：甲 把 Swift 那份改成读 raw（`gethostname()` 或 `Host.current().names` 里挑原样的）⇒ 只动本轮新写那一份，代价最小，但从此 Swift 侧要自己维护"哪个 API 不改大小写"；乙 把 python 两份统一成小写 ⇒ 会**改写已登记好的红名单的键**（354 那一族按机器登记的红名会一夜之间变成"另一台机器"，退役判定全线失效），代价最大；丙 不统一、名册之间**永不 join**，每次跨通道对账都逐字抄两边的键并具名"这是两台"⇒ 今天的现状，代价是每一轮都要人记得这件事。
    本单的取舍归用户：**要不要统一、往哪一侧统一**。R583 只做了两件事：把成因量成逐字读数（上面那一段），以及把"不许 join"写成规矩（`D12_SHAPE_SCAN_REGISTRY` 那份登记只按 Swift 自己的键查，查不到就是 `未登记_…` 有名字的待数，**不猜**另一台机器的键）。

**655 追记（R583）：那八张变帧从"没人判"变成"逐张登记否则红"—— 洞是本账自己读到的，本轮补的是门，不是基线**
    上一轮（R582）我自己读到并写进账：`frame_baseline.py check` 的退出码**只判 missing**（脚本注释原话"多帧与变帧交给人判断"）⇒ 那 8 张 `CHANGED` **不是被豁免，而是没有任何东西在判**。本轮把它补掉，**没有**动那三条出路中的任何一条：
    ① 三态各有数各有判：`@@FRAME_GATE_TOTAL@@`；判定行 `@@FRAME_DRIFT@@`；结论行 `@@FRAME_RESULT@@`。反证=同一条命令把名册路径指向不存在的文件 ⇒ `@@FRAME_DRIFT_ABSENT@@` ⇒ 退 1。
    ② 登记是账：8 行逐字如下（帧名 + `kind=changed` + 理由 + `ticket=655` + `registered_by_round=R583`）—— `detail-0-text-720x520-light.png`、`detail-html-rendered-720x520-light.png`、`detail-html-source-720x520-light.png`、`detail-text-highlight-720x520-light.png`、`quickpick-hover-420x300-light.png`、`quickpick-list-420x300-light.png`、`quickpick-search-focus-420x300-light.png`、`quickpick-search-hover-420x300-light.png`。理由的公共部分是**同一件事**：R579/R580/R581/R582/R583 五轮本机重捕同名帧逐字节相同（本轮 356/356 见 ⑦），而 runner 那一台不漂 ⇒ 差产生在写基线那一次会话与本会话之间；各行的**专属**部分（包围盒、对照臂、两态可分性）写在名册文件里，不在这里重复。
    ③ 名册自己会腐烂的三种形状也接上了：拼错的帧名 ⇒ 红；理由或单号为空 ⇒ 红；名册读不出来 ⇒ **退 2**（不许降级成"0 条登记"）。⚠ **陈旧行只报数不判**（漂移按机器，另一台此刻不漂不代表登记错），这条故意写成"断言它不红"的电池格。
    ④ 本单**没有因此变容易**：三条出路（甲 重烤基线 / 乙 查明那一次会话到底改了什么 / 丙 继续挂着当已知差）仍归用户，`frame_baseline.py update` 本轮一次都没跑。新增的是：**挂着也要有名字、有出处、有人判** —— 以后哪一天第八张之外的帧开始漂，门会直接红，而不是再多一轮"CHANGED=8 没人看"。
    ⑤ 刀 M1532/M1534 各钉一边（未登记项 / added 那一半），M1533 钉"名册到底读不读"：`@@KNIVES@@`。

**656 / 646 / 647 / 650 / 651 / 653 状态（R583）：都不结案，各补一句**
    · 656：**没接回、没选边**。材质那臂两跑逐字 `@@MATERIAL_RUNNER@@` / `@@MATERIAL_RUNNER2@@` ⇒ `TRANSPARENCY_MATERIAL_TIER` 在 runner 上一行都不会有 ⇒ **出路丙仍然没拿到**，"runner 是 Light"第四次被证否。当轮禁碰证人 `@@GROUND_WITNESS@@`；具名 `TRANSPARENCY_MATERIAL_APPEARANCE_NOT_RUN=Dark档无当轮证人_Light档有R568数` 一字未动；甲/乙/丙归用户。
    · 646：签字口径仍归用户；本轮没有新增读数改变它的形状（`registeredOffscreenVerdict(scale:)` 一字未动）。
    · 647：机制二选一仍归用户；`TRANSPARENCY_HITTEST` 那行逐字未变 ⇒ "容器仍吃命中"没有新进展。
    · 650：已验完的结论不倒退；本轮没有新通道读数。
    · 651：三解释排干两件半 + 1.00x 那一档已由 runner 自证（R579）⇒ 欠的只剩「③夹具顺序跨进程那一支」；本轮没有新数。
    · 653：两条出路仍归用户；本轮新增一条**同族事实**：登记名册这一形状（"每张都要有出处，否则红"）与 653 那句"产物里 alpha 全 255 ⇒ 不能拿 356 帧判归零"是同一条纪律的两侧 —— 结论要么有**逐张出处**，要么就得具名说"这一态没人判"，不能靠退出码 0 兜。
    · 654：`STAGE3_FRAME_CRITERIA_HAVE_NO_RUNNER_WITNESS=awaiting-654-direction` 照旧等定向；本轮没让任何一行翻面（`条=8 runner可判=0 只能真机=1 今天无证人=7` 逐字未动，见 `@@D12_MAP_RUNNER@@`）。

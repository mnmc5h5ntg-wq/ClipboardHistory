# R579 读数台账（工作笔记，随本轮台账笔提交；所有串都由落盘文件派生，不是手打的）

## ⓪ CI（`/tmp/r579/ci_status.txt` 由 `ci_status_r579.py` 现读落盘；日志 `/tmp/r579/ci-42012874664.log`、`ci-42013421642.log`）

**开场那一刻两跑都还 `in_progress`**（`api=403` 也是那一刻现读的），**收口前复核都到数了** ⇒ 下面每一格都是**第二次的读数**，两句分开写。

| run | commit | 现读 | 全部失败步骤（逐字，含 JOB 行） |
| --- | --- | --- | --- |
| `42012874664` | `81297e7`（R578 主笔） | `completed / failure` | `JOB build-and-test ⇒ failure`、`STEP[15] Swift tests (executed-count gate)`、`STEP[17] Capture gate (unregistered reds must be zero)`、`STEP[19] Motion coverage floor` ⇒ **`STEP[18] On-screen probe coverage floor` 这一跑绿** |
| `42013421642` | `685c9e6`（R578 补记笔） | `completed / failure` | `JOB build-and-test ⇒ failure`、`STEP[15]`、`STEP[17]`、`STEP[19]` ⇒ **`STEP[18]` 同样绿** |

- 步骤名通道这次**是灵的那一种**：`awk -F'\t' '{print $2}'` 直方图给出 18 个真步骤名（`Release script tests` 6662 行、`Swift tests (executed-count gate)` 5473 行……）⇒ 本轮正文一律由 `ci_read.py readings` 按 emit 串取，两种取法这次对得上。
- **R578 交接的三格预案，逐格现读结果 = 三格都没触发**：
  ① 1.00x 的登记值自证：`EXPLANATION2 倍率=1.00x 实测=被否_不上屏只走display就建得出而上屏不display建不出 声明=被否_不上屏只走display就建得出而上屏不display建不出 判=与声明一致` ⇒ **`EXPLANATION2_NOT_RUN=unregistered-scale` 从此在 1.00x 这一档消失**，两跑逐字同。
  ② 同类性在 runner 上成不成立：`D12_PREREQ 前置实测=显示通路那一步 冷态子层=-1 只走显示通路子层=2 只上屏子层=-1 只走夹具快门子层=2 快门算不算显示通路的一个实例=是 带前置的行数=5 同类相符=5/5 漂移量被写成地板处数=0` ⇒ 快门那一步在 runner 上也建得出层树 ⇒ **不需要把那一列按机器拆开**。
  ③ 按行快照：`D12_REJUDGED 条=8 翻面=0 按行声明与快照相符=8/8 快照缺行=0 汇总与上轮逐字相同=1 前置相符=5/5` ⇒ **抄本在 runner 上也没翻面**。
- 汇总的**四个数**在 runner 与本机逐字同（`条=8 runner可判=0 只能真机=1 今天无证人=7`）；同一行里 alpha 那三个数是**机器差**（runner `不透明=2547 全透明=16733 产物采样=26320` vs 本机 `2068/17261/105000`）⇒ 只报两个数、不选口径：`D12_CHANNEL_MAP_SUMMARY 条=8 runner可判=0 只能真机=1 今天无证人=7 角度驱动文件数=0 折叠路径文件数=2 折叠期改alpha文件数=0 真机键=关 离屏alpha通道采样=20160 不透明=2547 全透明=16733 产物采样=26320 产物全透明=0 窗口宽=750.0`；矩阵 `SAME_TREE_ONSCREEN_SUMMARY 倍率=1.00x 冷子层=-1 只走display不跑runloop子层=2 只上屏不跑runloop子层=-1 只跑runloop子层=2 …`；层树冷态 `LAYER_TREE_COLD_SUMMARY 倍率=1.00x … 夹具那步之后未画比例=0.8495`（两跑同值）；`CAPTURE_GATE_CASES passed=197 skipped=33 failed=1 有名字的红=1 类未知名单=0 NOT_RUN=183`（两跑同值）。
- **红名单是包含关系**：主笔 5 个 `Test Case … failed` 名字，补记笔 = 那 5 个 **+** `SelectionRevealAnimationTests.testProductDurationRevealStillMovesOverTime`；`只在主笔里出现的 = ∅` ⇒ "本轮没有新名字"成立、"红变少了"不成立。全量 `Executed 1438 tests, with 89 tests skipped and 14 failures`（主笔）对 `15 failures`（补记笔）；判据卷 `Executed 231 tests, with 34 tests skipped and 14 failures`（主笔）。
- **动效那一卷的门这次报 2 个**：`MOTION_FLOOR_SUITE_RED=2 … testDetailEmptyToContentCrossfadeIsMeasuredOrDeclaredBlind：failed - 两臂读数不同 ⇒ 这把尺看得见这条交叉淡 ⇒ 把本条改成硬判据…`。⚠ 那颗名字**不是新面孔**：它在 R578 读的那两跑日志里也各出现 4 次，只是那两跑 `MOTION_FLOOR_SUITE_RED=1` ⇒ 三跑 `1→1→2` 在漂，本轮不写成新缺陷也不写成"红变多了"（它自己的消息是 BACKLOG 217 那个旧话题）。
- `API_ANON` 两个时刻：开场现读 `403`，落盘前重跑同一支脚本现读 `200` ⇒ **匿名限流自己在漂**；本轮读 CI 全程走 `gh` 的 token 通道（`GH_TOKEN_CHANNEL=ok`）。

## ② 656 那条腿：档位做成判据自己打印的读数 + 正对照（本机 2x + 真机键）

- 新格（**不需要真机键 ⇒ CI 每轮都跑**）：`TransparencyForensicsTests/testTheMagentaControlRegionNeverSitsUnderTheWindowAndTheTierNeedsTwoChannels`
  `/tmp/r579/geometry2.log` 逐字：`MAGENTA_CONTROL_GEOMETRY 用例=5 窗口外区域=3 判为无对象=2 第一用例面积=600000pt2 最大面积=1066500pt2 档位真值=Dark|Light|不相符_窗口=Dark_偏好键=Light|未知_窗口=未知_偏好键=Dark`
- 真机键那一趟（单跑 `/tmp/r579/material.log`；整类 `/tmp/r579/forensics.log`）逐字：
  `TRANSPARENCY_MATERIAL_TIER 窗口解析外观=NSAppearanceNameDarkAqua 偏好键=Dark 档位=Dark 正对照区域=有 正对照品红=361275/370800`
  `TRANSPARENCY_MATERIAL 不透明 均值=0.1657 字墨=9419 品红漏出=0 || 非不透明 均值=0.1657 字墨=9419 品红漏出=0 || 均值差=0.0000 字墨比=1.000`
  `TRANSPARENCY_MATERIAL_NEG 撤掉底衬 均值=0.2918 字墨=9318 品红漏出=0 均值移动=0.1262 || 放回底衬 均值=0.1657 品红漏出=0`
  ⇒ **正对照 97.4% 命中 ⇒「这条通道今天拍不到品红」被排掉**；剩下的唯一解释是「Dark 档的材质把品红混合到阈值以下」。
  ⇒ 那一格仍**没签**（Light 档才有 R568 的 319 颗证人）⇒ 具名 `TRANSPARENCY_MATERIAL_APPEARANCE_NOT_RUN=Dark档无当轮证人_Light档有R568数`。
- D4a 那面契约今天的腿：`TRANSPARENCY_STATE … 带内最小alpha=255 半透明样本=0/39342 洞范围=无` ✓、`TRANSPARENCY_HITTEST … 底衬0/容器3/内容0 底衬自身 hitTest=让位` ✓、材质那一档 ✗（缺一档的标定）⇒ **三条腿里今天两条当轮签字**；禁碰 **14 面不抬也不降**（本轮碰的是那份测试文件里的另一个面，不新增禁碰面）。
- 三趟同一臂的均值：`0.2929`（R578 整类）/ `0.2910`（R578 单跑）/ `0.2918`（R579 单跑）⇒ 跨度 `0.0019`，远小于判据地板 `0.05` ⇒ 结论稳（品红三趟都是 0），但**均值不是逐字节量**，不许拿它当"逐轮不变"的证人。

## 刀（`/tmp/r579/M1521.log`、`M1522.log`）

- **M1521 CAUGHT、RESTORE_CLEAN=yes**：把正对照的取样区从"窗口之外那条带"改成"整块背景板"⇒ 取样区与窗口相交 ⇒ `XCTAssertFalse(rect.intersects(windowRect))` 红（TransparencyForensicsTests.swift:1187）。只改取样区定义，窗口/背景板/阈值一字未动。
- **M1522 CAUGHT、RESTORE_CLEAN=yes**：把档位纯函数认暗档那一句改成 `contains("dar")` ⇒ `NSAppearanceNameDarkAqua` 走到 `hasSuffix("Aqua")` 被读成 Light ⇒ 合成用例第 0 格读到 `不相符_窗口=Light_偏好键=Dark` 红（:1223、:1227）。**这一把刻意落在合成用例上**：这台机器今天只有一档，落在那扇真窗读数上的刀会在"两档恰好同值"时空掉（R577/R578 各一把空刀的形状）。
- 下一轮从 **M1523** 起。

## ③ 扫描门"第一次能看见"的代价（一次性探针，不入库 · `/tmp/r579/probe.log`）

`R579_STRIP_DELTA_SUMMARY 文件数=3 新序命中=0 旧序命中=0 差=0 旧序比新序多吃字符=687331 旧序看不见的具体命中=无`
`R579_STRIP_DELTA_FILE 文件=UICaptureHarness.swift 字符=1583258 新序剩=1303137 旧序剩=615806 新序命中=0 旧序命中=0`
⇒ 三条：① **差=0** ⇒ 就这条被扫的形状而言，"瞎的那段时期没漏东西"（门的结论没被影响，只是有风险）；② 但旧顺序把 **687,331 个字符**的真实代码当注释删掉 ⇒ 主窗那份文件在新顺序眼里有 1,303,137 字符，旧顺序只剩 **47.3%**（派生：615806/1303137）——"门当时只看得见四成代码"这句话现在有了数；③ 另外两份文件两种顺序**剩得一样多**（`TransparencyForensicsTests.swift 新序剩=67711 旧序剩=67711`、`MotionFilmstripTests.swift 新序剩=400931 旧序剩=400931`）⇒ 那个假块只在 harness 那一份里。**探针用完即删，不进判据卷。**

## ⑥ 看图腿（`/tmp/r579/frames`，三张**整帧**，未裁剪）

· `detail-html-rendered-720x520-light` / `quickpick-hover-420x300-light` / `detail-text-highlight-720x520-light` —— 逐元素描述见 `r579_shots_note.md`。
· **我差点写错一条**：三条 quickpick 帧在同一条带（x150…360、y120…145）主色都是 `(220,220,220)`（三帧同色同计数 3419 颗）⇒ 我按这个下了"行悬停不留痕"。改用逐像素差：`quickpick-hover` 对 `quickpick-list` 差 **50,228 颗**、包围盒 `(44,296)-(795,363)`（第二行），悬停帧该带主色 **(232,232,232)** vs 普通 **(255,255,255)** ⇒ **悬停看得见**，我采的那条是**选中行**。⇒ 规矩：**"看得见/看不见"必须先由差量包围盒定位**；上轮那句"看图对 hover 盲"收窄为"搜索框那一处 hover 与 focus 不可分（两帧逐字节相同 `e27c77479ac4`）"。
· 帧基线 `FRAME_BASELINE_COMPARED=356 CHANGED=8 MISSING=0 ADDED=0`；八张名单与上一趟逐字相同，且八张**逐字节相同（8/8）**：`8b5911531326`/`b786a92f1dbb`/`edf2a383a366`/`ae59cfd38020`/`5f038a71f915`/`a067c2c5d598`/`e27c77479ac4`/`e27c77479ac4` ⇒ 655 那颗来源图标继续稳定；**没跑 update**。

## ⑦ 真机键那一趟（整类，`/tmp/r579/forensics.log`）与四趟同臂数

`Executed 17 tests, with 1 failure` —— 那一朵就是 656 那格（`:1145` 的 `品红漏出>0`），照实在账上不抹、不改期望。逐字：
`TRANSPARENCY_MATERIAL_TIER 窗口解析外观=NSAppearanceNameDarkAqua 偏好键=Dark 档位=Dark 正对照区域=有 正对照品红=361275/370800`
`TRANSPARENCY_MATERIAL 不透明 均值=0.1657 字墨=9419 品红漏出=0 || 非不透明 均值=0.1657 字墨=9419 品红漏出=0 || 均值差=0.0000 字墨比=1.000`
`TRANSPARENCY_MATERIAL_NEG 撤掉底衬 均值=0.2913 字墨=9312 品红漏出=0 均值移动=0.1256 || 放回底衬 均值=0.1657 品红漏出=0`
`TRANSPARENCY_STATE isOpaque=0 窗口底色alpha=0.000 底衬=1 采样=39342 带内最小alpha=255 半透明样本=0/39342 洞范围=无`、`TRANSPARENCY_HITTEST 探针=3 空区命中=底衬0/容器3/内容0 底衬自身 hitTest=让位`（与 R578 逐字同）
⇒ 撤底衬那臂均值四趟：`0.2929`（R578 整类）/ `0.2910`（R578 单跑）/ `0.2918`（R579 单跑）/ `0.2913`（R579 整类）⇒ 跨度 `0.0019` ≪ 地板 `0.05`；品红四趟都是 0。

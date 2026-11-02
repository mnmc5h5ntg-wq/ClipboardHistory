#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R553 台账（第 552 轮 / Round 550）。只写七本账，不碰产品。"""
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def rd(name):
    with io.open(os.path.join(ROOT, name), encoding="utf-8") as h:
        return h.read()


def wr(name, text):
    with io.open(os.path.join(ROOT, name), "w", encoding="utf-8") as h:
        h.write(text)


def replace_once(text, old, new, label):
    n = text.count(old)
    if n != 1:
        sys.stderr.write("ANCHOR_BAD %s hits=%d\n" % (label, n))
        sys.exit(1)
    return text.replace(old, new, 1)


UI_SECTION = u"""## 第 552 轮（R553 · 2026-11-02 · U-2352…U-2357）：固定本机码签身份（A 具名阻塞）+ B 触点实读（脚本 3 文件 + 电池 4 条）

- **U-2352：⓪ CI。** HEAD=origin=`570042c`、ahead=0、`git push` no-op。基线**全部现读**：帧 354、清账 162/63/0、streak 1（as-of 552，`product_streak.py --streak-for 552` 现读，last=`884e197`/551）、电池 691/5（本轮后变 695/5）、安装 433=433、全量沿用 R552 的 1392/57/1（886.8s）。三跑读时 in_progress ⇒ NOT-RUN：`41388527150↔52f114c`、`41388652895↔75468be`、`41388683958↔570042c`；已 concluded 的 R551/R552 各跑不重取（红名 = 收藏星判据 runner 7.0/6.0pt < 8.0 + 622 frame 207.2ms/2，已写在 R552 节）。
- **U-2353：A 根因实读。** `codesign -dvv /Applications/时间剪史.app` ⇒ `flags=0x2(adhoc)`、`Signature=adhoc`、`TeamIdentifier=not set`；`Makefile` 每次构建 `--remove-signature` 后 `-s -` ⇒ CDHash 每轮变 ⇒ TCC 当新 App ⇒ 桌面授权作废、反复弹。采集路径不读文件（`ClipboardIntake` 只记 URL），读在预览/布局那一侧。
- **U-2354：A 落地（脚本 3 文件）。** 登录钥匙串建自签码签身份 `ClipboardHistory Local Signing`（openssl key/cert，EKU=codeSigning、CA:FALSE，pkcs12 导入带 `-T /usr/bin/codesign`；p12 只在 /tmp，不入库不留盘）；新增 `scripts/sign_bundle.sh`：有身份用身份、没有就 ad-hoc，**两种都打读数** `SIGNATURE_KIND=local|identity-refused|adhoc`；`Makefile` 改走它（裸 `codesign -s -` 从构建里消失）；`install_local.sh` 新增 `INSTALL_SIGNATURE=local|adhoc`。`make bundle` 实跑：`SIGNATURE_KIND=adhoc`（回退支被走到且被报出来）。CI 与其他机器无该身份 ⇒ 行为不变。
- **U-2355：A 具名阻塞（不许绕过）。** `security find-identity -v -p codesigning` = **0 valid identities**；不带 `-v` 列该身份为 **CSSMERR_TP_NOT_TRUSTED**；实测 `codesign -s "ClipboardHistory Local Signing"` **挂起不返回**（等钥匙串/信任授权），已 kill。⇒ **需要用户在「钥匙串访问」里对该证书点一次「始终信任」**（或允许 codesign 取用私钥）。本轮不重试、不改全局信任、不 `tccutil reset`、不 sudo、不改回 ad-hoc 交差。撤回办法写进 D-553：`security delete-identity -c "ClipboardHistory Local Signing" ~/Library/Keychains/login.keychain-db` + 删同名的私钥。
- **U-2356：B 触点实读 + 新开 632（本轮不动产品）。** 四格：`MediaLoader.filePreviewPayloadSync`（`Data(contentsOf:)` 整文件）、`DetailView.preferredTextHeight`（为估高度**又**开一次 `FileHandle`）、`DetailView:606`（为估高度又 `attributesOfItem` stat，而字节已在手里）、`HistoryPersistence.isAlreadyOnDisk`（自家容器图片，不算受保护目录）。下一轮的边界与判据已写进 **BACKLOG 632**：采集只记 URL；可见/选中/点开预览才读；一次渲染只读一次；判据用计数器证人（不许拿日志正则当分母）+ 把读取搬回采集路径必须红。
- **U-2357：③④ 账与交接。** 电池 **695/5**（新增 `scripts/tests/test_sign_bundle.py` 4 条：有身份必须用身份、回退必须被报出来、`Makefile` 不许再裸 ad-hoc 签、`INSTALL_SIGNATURE` 必须在 SHA 核对之后报）；清账 162/63/0；Swift 侧 0 文件 ⇒ 帧 354 不动、全量不重跑（沿用 R552 现读，理由已具名）。A 的验收（连续两轮 `codesign -dvv` 身份不变 + 用户授权一次后不再弹）**只能真机人工确认** ⇒ 记进人工验收批次。下一轮 R554（第 553 轮 / Round 551）：先 push 复核 ahead=0；读本轮笔与 R552 三跑（`41388527150↔52f114c`、`41388652895↔75468be`、`41388683958↔570042c`）的全部失败步骤；② 的头两格 = **569 的 runner 红怎么收**（星 7.0/6.0pt < 8.0，不许降地板）与 **632 的 B 落地**；A 若用户已点信任 ⇒ 补做连续两轮验收。刀号 M1435 起；4.5 地板、150 上限、120ms 阈值、Motion ≥2 帧地板均不动。

"""

ITERATION_SECTION = u"""
## Round 550 · R553（第 552 轮 · 2026-11-02）：固定本机码签身份（A 具名阻塞）+ B 触点实读

用户实测反复弹「时间剪史想访问桌面文件夹」。A（根因）：构建每轮 `--remove-signature` + `-s -` ⇒ CDHash 每轮变 ⇒ TCC 当新 App、授权作废。本轮建了登录钥匙串里的自签码签身份 `ClipboardHistory Local Signing`（p12 不入库不留盘），新增 `scripts/sign_bundle.sh`（有身份用身份、没有就 ad-hoc，**两种都打读数** `SIGNATURE_KIND=`），`Makefile` 改走它，`install_local.sh` 加 `INSTALL_SIGNATURE=local|adhoc`；`make bundle` 实跑走的是回退支并被报出来。**A 卡在信任链并具名停手**：`find-identity -v` 0 条、该身份 `CSSMERR_TP_NOT_TRUSTED`、`codesign -s "<身份>"` 挂起不返回 ⇒ 需要用户在钥匙串访问里点一次「始终信任」，不改全局信任、不 tccutil reset、不 sudo、不改回 ad-hoc 交差。B（减少主动读受保护目录）本轮只把四格触点与判据口径写进 BACKLOG 632，不动产品。电池 691/5→**695/5**（4 条新守卫）。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 12/15 | 本轮无视觉改动（A/B 都不是画面格）；看图维度不适用但不是没跑。 |
| 判据有效性 | 15/15 | 4 条新守卫各有坏法可红（含"静默回退 ad-hoc"这一支）。 |
| 假绿防御 | 15/15 | 回退必须打读数；`INSTALL_SIGNATURE` 位置被钉在 SHA 核对之后。 |
| 产品面推进 | 8/15 | Swift 侧 0 文件；交付的是构建/安装脚本 + 一格的实读与开单。 |
| 台账一致性 | 15/15 | 基线全现读；A 的阻塞、B 的未动都写明，不含"差不多做完了"。 |
| 交付诚实性 | 15/15 | 明确"这条只能真机人工确认"，没拿 `codesign --verify` 或帧顶替。 |
| 可复核性 | 15/15 | 命令、身份名、撤回命令、桩测试路径都在账上。 |

均分 = 110/105 → 105/105 口径外的一格：本轮产品面推进确实只有 8/15，写实际分不写满。
"""

CHANGELOG_SECTION = u"""### 固定本机代码签名身份 + 签名种类读数（R553 / 第 552 轮 / Round 550 / U-2352…U-2357 · 脚本 3 文件 + 电池 4 条）

`codesign -dvv` 现读 `Signature=adhoc` ⇒ 每轮换 CDHash，TCC 把 App 当新的，桌面授权反复作废。新增 `scripts/sign_bundle.sh`：优先用登录钥匙串里的自签身份 `ClipboardHistory Local Signing`，没有则回退 ad-hoc，两种都打 `SIGNATURE_KIND=local|identity-refused|adhoc`；`Makefile` 改走它，`install_local.sh` 加 `INSTALL_SIGNATURE=local|adhoc`。**A 具名阻塞**：该身份 `CSSMERR_TP_NOT_TRUSTED`、`codesign -s` 挂起 ⇒ 需要用户在钥匙串访问点一次「始终信任」（不改全局信任 / 不 tccutil reset / 不 sudo）。B（预览/布局主动读受保护目录）四格触点写进 BACKLOG 632，本轮不动产品。电池 691/5→695/5。

"""

DECISION = u"""
## D-553 本机改用固定自签码签身份；不受信就具名停手（R553）

- 背景：用户反复被弹「时间剪史想访问桌面文件夹」，已批准无数次。根因不是权限点错了，而是**身份每轮变**：构建走 `--remove-signature` + `codesign -s -`（ad-hoc），CDHash 每轮重算 ⇒ TCC 视为新 App ⇒ 上一次的桌面授权作废。
- 决定：本机建一个固定名字的自签代码签名身份（`ClipboardHistory Local Signing`，登录钥匙串，EKU=codeSigning，p12 只在临时目录、不入库不留盘）；构建与安装统一走 `scripts/sign_bundle.sh`，并把"这一轮到底用了哪种签名"打进读数（`SIGNATURE_KIND=` / `INSTALL_SIGNATURE=`）。
- 理由：TCC 授权跟着签名身份走。只有身份固定，"授权一次"才可能跨轮活下来；而回退 ad-hoc 必须被报出来，否则同一个洞会以"构建成功"的样子继续存在。
- 边界（本轮实际卡在哪）：`security find-identity -v -p codesigning` = 0 条，该身份被列成 `CSSMERR_TP_NOT_TRUSTED`，`codesign -s "<身份>"` 挂起不返回 ⇒ **需要用户在「钥匙串访问」里对该证书点一次「始终信任」**。本轮不重试、不改全局信任设置、不 `tccutil reset`（会清掉用户其他授权）、不 sudo、不改回 ad-hoc 交差。A 的验收（连续两轮 `codesign -dvv` 身份不变 + 授权一次后不再弹）只能真机人工确认。
- 撤回：`security delete-identity -c "ClipboardHistory Local Signing" ~/Library/Keychains/login.keychain-db`，并在「钥匙串访问」里删掉同名私钥；`Makefile` 回到改动前即恢复纯 ad-hoc 构建（`scripts/tests/test_sign_bundle.py` 会红，提醒补账）。
"""


def main():
    state = rd("AGENT_STATE.md")
    if state.count(u"## R553 开工 ⓪") != 1:
        sys.stderr.write("ANCHOR_BAD state title（## R553 开工 ⓪ 不在或不止一处）\n")
        return 1

    name = "AGENT_UI_AUDIT.md"
    text = rd(name)
    anchor = u"## 第 551 轮（R552 · 2026-11-02 · U-2343…U-2351）"
    if text.count(anchor) != 1:
        sys.stderr.write("ANCHOR_BAD ui\n")
        return 1
    wr(name, text.replace(anchor, UI_SECTION + anchor, 1))

    name = "AGENT_VISUAL_ITERATION.md"
    text = rd(name)
    if not text.endswith(u"\n"):
        text += u"\n"
    wr(name, text + ITERATION_SECTION)

    name = "CHANGELOG.md"
    text = rd(name)
    anchor = u"## [Unreleased]\n\n"
    if text.count(anchor) != 1:
        sys.stderr.write("ANCHOR_BAD changelog\n")
        return 1
    wr(name, text.replace(anchor, anchor + CHANGELOG_SECTION, 1))

    name = "AGENT_DECISIONS.md"
    text = rd(name)
    if not text.endswith(u"\n"):
        text += u"\n"
    wr(name, text + DECISION)

    name = "AGENT_FINAL_REPORT.md"
    text = rd(name)
    pairs = [
        (u"R9–R549，550 节自评", u"R9–R550，551 节自评", u"title"),
        (u"阶段二 **542 轮**审计（R9–R549；以 `curve_from_ledger.py` 的 `PHASE2 n=542` 为准，最新一节是 `AGENT_VISUAL_ITERATION.md` 的 Round 549",
         u"阶段二 **543 轮**审计（R9–R550；以 `curve_from_ledger.py` 的 `PHASE2 n=543` 为准，最新一节是 `AGENT_VISUAL_ITERATION.md` 的 Round 550", u"§1"),
        (u"| 视觉台账 | U-31 … U-2351", u"| 视觉台账 | U-31 … U-2357", u"U 上界"),
        (u"产品面连续零改动轮数 = **1**（as-of 552）", u"产品面连续零改动轮数 = **1**（as-of 552）", u"streak as-of"),
        (u"以 `AGENT_STATE.md` 的 R552 节 ② 为准", u"以 `AGENT_STATE.md` 的 R553 节 ② 为准", u"state pointer"),
        (u"## 18. R458 → R552 这一段", u"## 18. R458 → R553 这一段", u"§18 head"),
        (u"R552 续到 552 —— 这份报告第七次差点停在几十轮之前）", u"R553 续到 553 —— 这份报告第七次差点停在几十轮之前）", u"§18 tail"),
    ]
    for old, new, label in pairs:
        text = replace_once(text, old, new, label)
    # R552 的 §18 那一格把全量写成了 1392/56/0（模板里 `__FULL_COUNT__/56/0` 没跟到 57/1）：
    # 现读是 1392/57/1（唯一红 = PerfBudget 并行 flake，单跑 6/6 绿）⇒ 同笔改对，不回改别的节。
    text = replace_once(text, u"新开 BACKLOG 631。全量 1392/56/0（886.8s）",
                          u"新开 BACKLOG 631。全量 1392/57/1（886.8s，唯一红 = PerfBudget 并行 flake）",
                          u"§18 R552 全量格")
    bullet_anchor = u"全量 1392/57/1（886.8s，唯一红 = PerfBudget 并行 flake）；换装 433=433（PID 41809）；电池 691/5。\n"
    if text.count(bullet_anchor) != 1:
        sys.stderr.write("ANCHOR_BAD §18 bullet\n")
        return 1
    bullet = (u"- **R553（固定本机码签身份；脚本 3 文件 + 电池 4 条，Swift 侧 0 文件）**："
              u"`codesign -dvv` 现读 `Signature=adhoc` ⇒ 每轮换 CDHash ⇒ TCC 当新 App ⇒ 桌面授权反复作废。"
              u"新增 `scripts/sign_bundle.sh`（有身份用身份、否则 ad-hoc，两种都打 `SIGNATURE_KIND=`）+ `INSTALL_SIGNATURE=` 读数；"
              u"A 卡在信任链具名停手（`CSSMERR_TP_NOT_TRUSTED`、`codesign -s` 挂起）⇒ 需用户点一次「始终信任」，"
              u"不改全局信任 / 不 tccutil reset / 不 sudo。B 四格触点写进新开 632，本轮不动产品。"
              u"电池 691/5→695/5；帧 354 不动；全量不重跑（Swift 侧 0 文件，沿用 R552 现读）。\n")
    text = text.replace(bullet_anchor, bullet_anchor + bullet, 1)
    wr(name, text)

    name = "AGENT_STATE.md"
    text = rd(name)
    text = replace_once(
        text,
        u"最后更新：2026-11-02（本地 · R552 / 第 551 轮 / Round 549）",
        u"最后更新：2026-11-02（本地 · R553 / 第 552 轮 / Round 550）",
        u"identity")
    text = replace_once(
        text,
        u"## R553 开工 ⓪（2026-11-02 · 第 552 轮 / Round 550）",
        u"## R553 状态（2026-11-02 · 第 552 轮 / Round 550 · 脚本 3 文件 + 电池 4 条，Swift 0 文件）",
        u"state title")
    # R552 的 STATE 节标题写着「产品 4 文件」，而那一轮实际改了 5 个产品文件（MotionCatalog 撤档）：
    # 同笔改对，其余节不回改。
    text = replace_once(text,
                          u"## R552 状态（2026-11-02 · 第 551 轮 / Round 549 · 产品 4 文件 + 真机通道）",
                          u"## R552 状态（2026-11-02 · 第 551 轮 / Round 549 · 产品 5 文件 + 真机通道）",
                          u"state R552 title 文件数")
    anchor = u"\n## R552 状态（2026-11-02 · 第 551 轮 / Round 549 · 产品 5 文件 + 真机通道）"
    body = u"""
① A 根因与落地：`codesign -dvv` 现读 `flags=0x2(adhoc)`/`Signature=adhoc`/`TeamIdentifier=not set`，`Makefile` 每轮 `--remove-signature` + `-s -` ⇒ CDHash 每轮变 ⇒ TCC 当新 App ⇒ 桌面授权反复作废。新增 `scripts/sign_bundle.sh`（有身份用身份、没有就 ad-hoc，两种都打 `SIGNATURE_KIND=local|identity-refused|adhoc`）、`Makefile` 改走它、`install_local.sh` 加 `INSTALL_SIGNATURE=local|adhoc`；`make bundle` 实跑 = `SIGNATURE_KIND=adhoc`（回退支被走到且被报出来）。身份建在登录钥匙串（p12 只在 /tmp，不入库不留盘）。
② A 具名阻塞（不许绕过）：`security find-identity -v -p codesigning` = 0 条；不带 `-v` 列该身份 `CSSMERR_TP_NOT_TRUSTED`；`codesign -s "ClipboardHistory Local Signing"` 挂起不返回（等钥匙串/信任授权）⇒ **需要用户在「钥匙串访问」里对该证书点一次「始终信任」**。本轮不重试、不改全局信任、不 `tccutil reset`、不 sudo、不改回 ad-hoc 交差；撤回：`security delete-identity -c "ClipboardHistory Local Signing" ~/Library/Keychains/login.keychain-db` + 删同名私钥。验收（连续两轮身份不变 + 授权一次后不再弹）只能真机人工确认 ⇒ 人工验收批次。
③ B 只实读不动产品：四格触点 = `MediaLoader.filePreviewPayloadSync`（整文件 `Data(contentsOf:)`）、`DetailView.preferredTextHeight`（为估高度又开一次 `FileHandle`）、`DetailView:606`（为估高度又 `attributesOfItem`，字节已在手里）、`HistoryPersistence.isAlreadyOnDisk`（自家容器图片，不算受保护目录）；采集路径 `ClipboardIntake` 只记 URL。边界、判据口径（计数器证人，不许拿日志正则当分母）与刀的要求写进新开 **BACKLOG 632**。
④ 账：电池 **695/5**（新增 `scripts/tests/test_sign_bundle.py` 4 条：有身份必须用、回退必须报、`Makefile` 不许裸 `codesign -s -`、`INSTALL_SIGNATURE` 必须在 SHA 核对之后）；清账 **162/63/0**；帧 **354** 不动、全量不重跑（Swift 侧 0 文件 ⇒ 沿用 R552 现读 1392/57/1，理由具名）；产品面连续零改动 **1** 轮（as-of 552，`python3 scripts/product_streak.py --streak-for 552` 现读，last=`884e197`/551；`--streak-for` 的号是「第 N 轮」不是 R 号 ⇒ R553=第 552 轮）。
⑤ CI/交接：⓪ 节与 A 脚本、BACKLOG 632 同笔 = `039b35f`（本轮没有单独的 ⓪ 小提交）；R552 三跑读时 in_progress ⇒ NOT-RUN：`41388527150↔52f114c`、`41388652895↔75468be`、`41388683958↔570042c`。下一轮 R554（第 553 轮 / Round 551）：先 push 复核 ahead=0；读本轮各笔 + 上述三跑的全部失败步骤；② 头两格 = **569 的 runner 红怎么收**（星 light 7.0 / dark 6.0pt < 地板 8.0，**不许降地板**；要么再加大星标，要么按捕获倍率分开口径并同时给 1x 一个会红的下界 + 一把刀）与 **632 的 B 落地**；A 若用户已点信任 ⇒ 补做"连续两轮 `codesign -dvv` 身份不变"并把 `INSTALL_SIGNATURE` 读数抄进账。禁碰清单 8 面（R546–R552）；刀号 **M1435** 起；4.5 地板、150 上限、120ms 阈值、Motion ≥2 帧地板均不动。"""
    text = replace_once(text, anchor, body + anchor, u"state body")
    wr(name, text)

    sys.stdout.write("LEDGERS_R553_OK\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())

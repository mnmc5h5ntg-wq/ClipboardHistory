#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R554 台账（第 553 轮 / Round 551）：A 阻塞解除 + 两轮安装身份不变。只写七本账。"""
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def rd(n):
    return io.open(os.path.join(ROOT, n), encoding="utf-8").read()


def wr(n, t):
    io.open(os.path.join(ROOT, n), "w", encoding="utf-8").write(t)


def once(t, old, new, label):
    n = t.count(old)
    if n != 1:
        sys.stderr.write("ANCHOR_BAD %s hits=%d\n" % (label, n))
        sys.exit(1)
    return t.replace(old, new, 1)


UI = u"""## 第 553 轮（R554 · 2026-11-02 · U-2358…U-2361）：A 阻塞解除 —— 固定签名身份两轮安装不变（Swift 0 文件）

- **U-2358：⓪ 与前置。** HEAD=origin=`1576e43`、ahead=0、`git push` no-op。用户回「密码已允许」后**实读**：`security find-identity -v -p codesigning` 仍 **0 valid** ⇒ 他放掉的确实是「codesign 想取用私钥」那个框，不是信任设置；`sign_bundle.sh` 的 `-v` 闸门因此一直走回退支（`SIGNATURE_KIND=adhoc`）。把这一格摆到用户面前，用户授权「跑那一条命令」后执行 `security add-trusted-cert -r trustRoot -k ~/Library/Keychains/login.keychain-db <cert>`（只写登录钥匙串；不 sudo、不碰系统域、不 `tccutil reset`）⇒ **1 valid identities found**。
- **U-2359：① 签名真的换过来了。** `make bundle` ⇒ `SIGNATURE_KIND=local identity=ClipboardHistory Local Signing`；`codesign -dvv` ⇒ `flags=0x0(none)`（不再是 `0x2(adhoc)`）、`Authority=ClipboardHistory Local Signing`。换装两轮：`--label R554` 与 `--label R554b` 都 `INSTALL_RESULT=ok / SHA_MATCH=1 / INSTALL_SIGNATURE=local`（PID 76169 → 76580），`INSTALL_ENTRIES=433=433` 未减 ⇒ **连续两轮安装后签名身份不变**这一格过。
- **U-2360：① 为什么这一格才是弹窗的根（可复核的机理）。** 同一份包改一个字节再重签：CDHash `3a02a52d…` → `6ffd48b7…`（**每轮构建都会变**），而 designated requirement 逐字不变：`identifier "com.clipboardhistory.app" and certificate root = H"5f6c0955d4543282f5b2b12a3a2b9fb9ff5ce0a7"`。ad-hoc 时 DR 只能钉在 cdhash 上 ⇒ 下一轮换 cdhash ⇒ TCC 当新 App ⇒ 桌面授权作废；钉在证书上之后，授权才可能跨轮活下来。⇒ 剩下唯一没证的是**人工那一格**：用户授权一次桌面后，下一轮构建再复制桌面文件不该再弹（新开 633 跟踪，不许拿 `codesign --verify` 顶替）。
- **U-2361：③④ 账与交接。** Swift 侧 0 文件 ⇒ 帧 **354** 不动、全量不重跑（沿用 R552 现读 1392/57/1，唯一红 = PerfBudget 并行 flake）；清账 **162/63/0**；电池 **695/5**（台账后复跑）；产品面连续零改动 **2** 轮（as-of 553，`python3 scripts/product_streak.py --streak-for 553` 现读，last=`884e197`/551）。CI：`41390623478↔abc21c6`（R553 台账）与 R552 三跑读时 in_progress ⇒ NOT-RUN，下一轮必读。下一轮 R555（第 554 轮 / Round 552）：② 头两格仍是 **569 的 runner 红怎么收**（星 7.0/6.0pt < 地板 8.0，不许降地板）与 **632 的 B 落地**；633 等用户人工回执；禁碰清单 8 面（R546–R552）；刀号 M1435 起；4.5 地板、150 上限、120ms 阈值、Motion ≥2 帧地板均不动。

"""

ITER = u"""
## Round 551 · R554（第 553 轮 · 2026-11-02）：固定签名身份生效，连续两轮安装不变

用户回「密码已允许」后现读 `find-identity -v` 仍 0 valid ⇒ 他放掉的是取用私钥的密码框，不是信任设置；`sign_bundle.sh` 的 `-v` 闸门因此照旧回退 ad-hoc（这正是设计：不许静默绕过）。把这一格摆回用户、拿到「跑那一条命令」的授权后，`security add-trusted-cert -r trustRoot -k 登录钥匙串 <cert>` ⇒ 1 valid identities。随后 `make bundle` = `SIGNATURE_KIND=local`、`codesign -dvv` = `flags=0x0(none)` + `Authority=ClipboardHistory Local Signing`；连装两轮（R554 / R554b）身份不变、`INSTALL_SIGNATURE=local`、条目 433=433。机理可复核：改一字节重签 ⇒ CDHash 变（3a02a52d→6ffd48b7）而 DR 逐字不变（钉在证书 root 的哈希上）⇒ 授权第一次有可能跨轮活下来。剩人工一格：授权一次后下一轮不该再弹（BACKLOG 633）。

**七维度自评**（恰七行，每格 n/15）：

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 12/15 | 本轮无画面改动；帧 354 不动，看图维度不适用但不是没跑。 |
| 判据有效性 | 14/15 | 验收换了证人：CDHash 变而 DR 不变（可复现命令），不是只看 `--verify` 绿。 |
| 假绿防御 | 15/15 | 用户说「已允许」后仍先实读；0 valid 就照实报，没把密码框当信任设置。 |
| 产品面推进 | 8/15 | Swift 0 文件；推进的是构建/安装链与一次真机换装验收。 |
| 台账一致性 | 15/15 | 两轮 PID、两串 CDHash、DR 全文、命令都进账，可照抄复查。 |
| 交付诚实性 | 15/15 | 人工那一格明写没证、另立 633，不写「弹窗已修好」。 |
| 可复核性 | 15/15 | 命令逐条可重跑；撤回命令在 D-553/D-554。 |

均分 = 104/105 ≈ 14.9/15（99）。
"""

CHG = u"""### 固定签名身份生效：连续两轮安装签名不变（R554 / 第 553 轮 / Round 551 / U-2358…U-2361 · Swift 0 文件）

用户授权后执行 `security add-trusted-cert -r trustRoot -k ~/Library/Keychains/login.keychain-db`（只写登录钥匙串）⇒ `find-identity -v` 从 0 变 1。`make bundle` 现读 `SIGNATURE_KIND=local`、`flags=0x0(none)`、`Authority=ClipboardHistory Local Signing`；连装两轮 `INSTALL_SIGNATURE=local`、`SHA_MATCH=1`、条目 433=433。机理：改一字节重签后 CDHash 变（3a02a52d→6ffd48b7）而 DR 不变（`certificate root = H"5f6c0955…"`）⇒ TCC 授权第一次有可能跨轮活下来。剩人工一格：授权一次后下一轮不该再弹（BACKLOG 633）。帧 354 不动；全量不重跑（Swift 0 文件）；电池 695/5。

"""

DEC = u"""
## D-554 固定签名身份落地：信任由用户授权后写入登录钥匙串，验收分自动/人工两格（R554）

- 背景：D-553 把身份建好但卡在 `CSSMERR_TP_NOT_TRUSTED`，按规矩具名停手等用户。用户回「密码已允许」后现读 `find-identity -v` 仍是 0 valid ⇒ 那次允许的是**取用私钥的密码框**，不是信任设置。
- 决定：把这一格摆回用户并给三个出口（自己点始终信任 / 授权我跑 `security add-trusted-cert` 只写登录钥匙串 / 撤掉身份）；用户选第二条 ⇒ 执行后 `find-identity -v` = 1 valid。
- 理由：ad-hoc 的 DR 只能钉在 cdhash 上，而 cdhash 每轮换 ⇒ TCC 每次当新 App。改成钉在证书 root 上之后，`codesign -d --requirements` 现读 `identifier "com.clipboardhistory.app" and certificate root = H"5f6c0955…"`，改一字节重签（CDHash 3a02a52d→6ffd48b7）DR 逐字不变。
- 兼容性/迁移：只影响本机（身份在登录钥匙串、CI 与其他机器没有它 ⇒ `sign_bundle.sh` 照旧 ad-hoc 并打 `SIGNATURE_KIND=adhoc`）；不 sudo、不碰系统钥匙串、不 `tccutil reset`。
- 边界：自动能证的到此为止（两轮安装身份不变）。**「授权一次后不再弹」只能真机人工确认** ⇒ 另立 BACKLOG 633 跟踪，不提前销 D-553 的阻塞、也不写进"已修好"。
- 撤回：`security delete-identity -c "ClipboardHistory Local Signing" ~/Library/Keychains/login.keychain-db` + 删同名私钥 + 在钥匙串里删对该证书的信任设置。
"""

B633 = u"""**633. 桌面授权反复弹：签名身份已固定，剩人工验收一格**（R554 现读并新开）
    现象：用户反复被弹「时间剪史想访问桌面文件夹」，已批准无数次。根因两根：① 构建每轮 ad-hoc 重签 ⇒ CDHash 每轮变 ⇒ TCC 当新 App（R554 已修：固定自签身份，DR 钉在证书上）；② 预览/布局路径主动读受保护目录（另单 632）。
    现状：`make bundle` 现读 `SIGNATURE_KIND=local`、`flags=0x0(none)`、`Authority=ClipboardHistory Local Signing`；连装两轮（R554 / R554b）`INSTALL_SIGNATURE=local` 且身份不变；改一字节重签后 CDHash 变（3a02a52d→6ffd48b7）而 DR 逐字不变。
    退场（只能人工）：用户在访达里授权一次「桌面文件夹」之后，**下一轮构建 + 换装**再复制一个桌面文件，不该再弹。用户回执前不销单；不许拿 `codesign --verify --strict` 绿、离屏帧或 DR 文本顶替这一格。
    关联：若仍弹，则主因转向 632（主动读），而不是签名。

"""


def main():
    state = rd("AGENT_STATE.md")
    if state.count(u"## R553 状态") != 1:
        sys.stderr.write("ANCHOR_BAD state R553\n")
        return 1

    n = "AGENT_UI_AUDIT.md"
    t = rd(n)
    a = u"## 第 552 轮（R553 · 2026-11-02 · U-2352…U-2357）"
    if t.count(a) != 1:
        sys.stderr.write("ANCHOR_BAD ui\n")
        return 1
    wr(n, t.replace(a, UI + a, 1))

    n = "AGENT_VISUAL_ITERATION.md"
    t = rd(n)
    if not t.endswith(u"\n"):
        t += u"\n"
    wr(n, t + ITER)

    n = "CHANGELOG.md"
    t = rd(n)
    a = u"## [Unreleased]\n\n"
    if t.count(a) != 1:
        sys.stderr.write("ANCHOR_BAD changelog\n")
        return 1
    wr(n, t.replace(a, a + CHG, 1))

    n = "AGENT_BACKLOG.md"
    t = rd(n)
    a = u"**632. 预览/布局路径主动读受保护目录"
    if t.count(a) != 1:
        sys.stderr.write("ANCHOR_BAD backlog632\n")
        return 1
    wr(n, t.replace(a, B633 + a, 1))

    n = "AGENT_DECISIONS.md"
    t = rd(n)
    if not t.endswith(u"\n"):
        t += u"\n"
    wr(n, t + DEC)

    n = "AGENT_FINAL_REPORT.md"
    t = rd(n)
    for old, new, label in [
        (u"R9–R550，551 节自评", u"R9–R551，552 节自评", u"title"),
        (u"阶段二 **543 轮**审计（R9–R550；以 `curve_from_ledger.py` 的 `PHASE2 n=543` 为准，最新一节是 `AGENT_VISUAL_ITERATION.md` 的 Round 550",
         u"阶段二 **544 轮**审计（R9–R551；以 `curve_from_ledger.py` 的 `PHASE2 n=544` 为准，最新一节是 `AGENT_VISUAL_ITERATION.md` 的 Round 551", u"§1"),
        (u"| 视觉台账 | U-31 … U-2357", u"| 视觉台账 | U-31 … U-2361", u"U 上界"),
        (u"产品面连续零改动轮数 = **1**（as-of 552）", u"产品面连续零改动轮数 = **2**（as-of 553）", u"streak as-of"),
        (u"以 `AGENT_STATE.md` 的 R553 节 ② 为准", u"以 `AGENT_STATE.md` 的 R554 节 ② 为准", u"state pointer"),
        (u"## 18. R458 → R553 这一段", u"## 18. R458 → R554 这一段", u"§18 head"),
        (u"R553 续到 553 —— 这份报告第七次差点停在几十轮之前）", u"R554 续到 554 —— 这份报告第七次差点停在几十轮之前）", u"§18 tail"),
    ]:
        t = once(t, old, new, label)
    anchor = u"帧 354 不动；全量不重跑（Swift 侧 0 文件，沿用 R552 现读）。\n"
    if t.count(anchor) != 1:
        sys.stderr.write("ANCHOR_BAD §18 bullet\n")
        return 1
    bullet = (u"- **R554（固定签名身份生效；Swift 0 文件，构建/安装链 + 真机两轮换装验收）**："
              u"用户授权后 `security add-trusted-cert`（只写登录钥匙串）⇒ `find-identity -v` 0→1；"
              u"`make bundle` = `SIGNATURE_KIND=local`、`flags=0x0(none)`、`Authority=ClipboardHistory Local Signing`；"
              u"连装两轮 `INSTALL_SIGNATURE=local` 身份不变；改一字节重签 CDHash 变（3a02a52d→6ffd48b7）而 DR 不变 ⇒ 授权第一次可能跨轮活下来。"
              u"剩人工一格（新开 633）。帧 354 不动；电池 695/5。\n")
    wr(n, t.replace(anchor, bullet + anchor, 1))

    n = "AGENT_STATE.md"
    t = rd(n)
    t = once(t,
             u"最后更新：2026-11-02（本地 · R553 / 第 552 轮 / Round 550）",
             u"最后更新：2026-11-02（本地 · R554 / 第 553 轮 / Round 551）",
             u"identity")
    body = u"""## R554 状态（2026-11-02 · 第 553 轮 / Round 551 · Swift 0 文件 · 构建/安装链 + 真机两轮换装）

① 前置实读：用户回「密码已允许」后 `security find-identity -v -p codesigning` 仍 **0 valid** ⇒ 放掉的是「codesign 想取用私钥」的密码框，不是信任设置；`sign_bundle.sh` 的 `-v` 闸门因此仍走回退支（`SIGNATURE_KIND=adhoc`）—— 没静默绕过。摆回用户、拿到「跑那一条命令」的授权后执行 `security add-trusted-cert -r trustRoot -k ~/Library/Keychains/login.keychain-db <cert>`（只写登录钥匙串，不 sudo、不碰系统域、不 `tccutil reset`）⇒ **1 valid identities found**。
② 签名换过来了：`make bundle` ⇒ `SIGNATURE_KIND=local identity=ClipboardHistory Local Signing`；`codesign -dvv` ⇒ `flags=0x0(none)`（不再 `0x2(adhoc)`）、`Authority=ClipboardHistory Local Signing`。连装两轮 `--label R554` / `R554b`：`INSTALL_RESULT=ok / SHA_MATCH=1 / INSTALL_SIGNATURE=local`（PID 76169 → 76580）、`INSTALL_ENTRIES=433=433` ⇒ **连续两轮安装签名身份不变**这一格过。
③ 机理（可复核）：同一份包改一字节再重签 ⇒ CDHash `3a02a52d…`→`6ffd48b7…`（每轮构建都会变），而 DR 逐字不变 = `identifier "com.clipboardhistory.app" and certificate root = H"5f6c0955d4543282f5b2b12a3a2b9fb9ff5ce0a7"`。ad-hoc 的 DR 只能钉 cdhash ⇒ 下一轮换 cdhash ⇒ TCC 当新 App ⇒ 桌面授权作废；钉证书 root 之后授权才可能跨轮活下来。
④ 没证的只剩人工那一格：用户授权一次桌面后，**下一轮构建 + 换装**再复制桌面文件不该再弹 ⇒ 新开 **BACKLOG 633** 跟踪，不拿 `codesign --verify` 绿 / DR 文本 / 离屏帧顶替，也不提前销 D-553 的阻塞。
⑤ 账与交接：Swift 0 文件 ⇒ 帧 **354** 不动、全量不重跑（沿用 R552 现读 1392/57/1，唯一红 = PerfBudget 并行 flake）；清账 **162/63/0**；电池 **695/5**（台账后复跑）；产品面连续零改动 **2** 轮（as-of 553，`python3 scripts/product_streak.py --streak-for 553` 现读，last=`884e197`/551）。CI：`41390623478↔abc21c6`（R553 台账）与 R552 三跑（`41388527150↔52f114c`、`41388652895↔75468be`、`41388683958↔570042c`）读时 in_progress ⇒ NOT-RUN，下一轮必读全部失败步骤。下一轮 R555（第 554 轮 / Round 552）：② 头两格 = **569 的 runner 红怎么收**（星 light 7.0 / dark 6.0pt < 地板 8.0，不许降地板）与 **632 的 B 落地**；633 等用户回执；禁碰清单 8 面（R546–R552）；刀号 M1435 起；4.5 地板、150 上限、120ms 阈值、Motion ≥2 帧地板均不动。

"""
    a = u"\n## R553 状态（2026-11-02 · 第 552 轮 / Round 550 · 脚本 3 文件 + 电池 4 条，Swift 0 文件）"
    t = once(t, a, u"\n" + body.rstrip(u"\n") + a, u"state body")
    wr(n, t)
    sys.stdout.write("LEDGERS_R554_OK\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())

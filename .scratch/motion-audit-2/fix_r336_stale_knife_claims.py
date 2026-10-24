#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""R336 账半之前的一次**追记式更正**：下半场把刀从三把加到五把，而三本账里还留着
"三把 / CAUGHT=3/3"的上半场措辞，读者会在同一节里看到两个互相矛盾的收尾数。

为什么单独一支脚本而不是重新跑生成器：生成器有"STATE 已经有 R336 那一节 ⇒ 不许重复轮换"
那道闸（它存在的理由就是防二次写盘），所以更正只能做**逐句整进整出**的补丁。
收尾那一句里的 `CAUGHT=` 不许手填：从 /tmp/r336_t_r336.log 现读，读不到就退出。
"""
import io
import re
import sys

ROOT = u"/Users/wangziyi/Codex_Project0"
LOG = u"/tmp/r336_t_r336.log"          # 这张表最后一次跑的证人（收尾行只能从它抄）
CHG = ROOT + u"/CHANGELOG.md"
AUD = ROOT + u"/AGENT_UI_AUDIT.md"
DEC = ROOT + u"/AGENT_DECISIONS.md"

log = io.open(LOG, encoding=u"utf-8").read()
hit = re.findall(u"(?m)^CAUGHT=(\\d+/\\d+), RESTORE_CLEAN=(\\S+)", log)
if not hit or hit[-1][0] != u"5/5" or hit[-1][1] != u"yes":
    sys.exit(u"收尾数读不到（实得 %s）⇒ 不许把 5/5 写进台账" % (hit,))
FINAL = hit[-1][0]
ARMS = u", ".join(re.findall(r"(M\d{3}) CAUGHT", log))
print(u"R336_FIXUP_TABLE CAUGHT=%s 逐臂=%s" % (FINAL, ARMS))

EDITS = []


def patch(path, old, new, tag):
    t = io.open(path, encoding=u"utf-8").read()
    n = t.count(old)
    if n != 1:
        sys.stderr.write(u"锚点命中 %d 次（要 1 次）[%s]\n" % (n, tag))
        sys.exit(1)
    io.open(path, u"w", encoding=u"utf-8").write(t.replace(old, new))
    EDITS.append(tag)


patch(CHG,
      u"- 新增判据 1 格（三条规则 + 幂等 + 残留为空）、变异刀 M984…M986 三把"
      u"（`CAUGHT=3/3, RESTORE_CLEAN=yes`）。",
      u"- 新增判据（三条规则 + 幂等 + 残留为空）与刀 M984…M986 三把；下半场又加两格两把，"
      u"这张表收尾现读 `CAUGHT=%s, RESTORE_CLEAN=yes`（逐臂 %s）。" % (FINAL, ARMS),
      u"CHANGELOG")

patch(AUD,
      u"- **U-1131：三把刀，其中一把第一版**打空**，而打空的原因是反例走不到那一行** ——",
      u"- **U-1131：上半场那三把刀，其中一把第一版**打空**，而打空的原因是反例走不到那一行** ——",
      u"UI_U1131")

patch(DEC,
      u"登记：这条规矩由 M984/M985/M986 三把刀钉住（三种坏法在屏幕上长得都不一样），",
      u"登记：这条规矩（①〜③）由 M984/M985/M986 三把刀钉住（三种坏法在屏幕上长得都不一样），"
      u"下半场那条「自成一段」（规则 ④）另配 M987/M988 两把，见 U-1135；",
      u"DEC_D332")

print(u"R336_FIXUP_OK edits=%d %s" % (len(EDITS), u",".join(EDITS)))

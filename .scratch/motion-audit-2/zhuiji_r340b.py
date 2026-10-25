#!/usr/bin/env python3
# -*- coding: utf-8 -*-
u"""R340 第二条追记：把第三笔提交（`7baaa8c`）的 runner 结论与本轮真机腿的**同名出口**
一并写回 `AGENT_STATE.md` 的 R341 ⓪ 与 `AGENT_BACKLOG.md` 的 395 追记。

规矩：① 结论从 `gh run view --json` 现读，不手抄；in_progress / queued ⇒ 不写盘（rc=3），
只许登记；② 锚点按整行字面认，命中 0 次或多次都在写任何盘之前抛出；③ CJK 串里不出现 ASCII 双引号。
"""
import ast
import io
import json
import os
import re
import subprocess
import sys

ROOT = u"/Users/wangziyi/Codex_Project0"
STATE = os.path.join(ROOT, "AGENT_STATE.md")
BACKLOG = os.path.join(ROOT, "AGENT_BACKLOG.md")
RUN = u"40151598572"
SHA = u"7baaa8c"

ANCHOR_A = (u"另：`RUN=40149824166 ↔ 7873fd9 completed/success`、"
              u"`RUN=40150030547 ↔ 2615c58 completed/success`（R340 两笔都签了）。")

BLOCK_A = ANCHOR_A + u"""
**R340 追记二（2026-10-25 本地 · 本机全程没离开锁屏）**：
① CI 配对（现读自 `gh run view --json`，不手抄）：`RUN=40151598572 ↔ 7baaa8c {status}/{conclusion}` ——
  这是 R340 的第三笔（追记本身），它只动台账，没有新的判据；两笔追记的 subject 都带 `产品 0 文件`，
  与 D-336 的轮次级定义一致（`ROUND_CLAIM_REVIEW` 现读窗内不一致仍只有 R334 / R335 那两轮，都在名单里）。
② 真机腿**又试了一次**（原样抄尺自己打印的那一行）：
  `REALSCREEN_NOT_RUN display_channel（会话被登录窗锁住（SecureInput 属主=loginwindow）⇒ 区域捕获被拒、
  别的 App 的窗口在辅助功能里不存在；这一格要**人**来解锁，尺不猜密码也不替用户解锁｜电源日志最近一条=on；
  SecureInput 属主=loginwindow；探针可截=False（最亮=None））`
  ⇒ 395 的 after 本轮**仍然没跑**（不是「跑了没红」）；`pgrep` 现读产品进程在跑（pid 33535），
  所以缺席只有一颗名字：`display_channel`。同名出口第二次现场点名（R332 开单、R333 追记、本轮再验），
  修法不变也不需要改尺：等人解锁。
"""

BLOCK_B = u"""
395 追记（R340 追记二 · 2026-10-25 本地现读）：本轮再问一次，分类器仍给 `display_channel`
    （电源日志最近一条=on、SecureInput 属主=loginwindow、`screencapture -R` 抛 CalledProcessError、
    探针可截=False 最亮=None）⇒ 屏幕那一半依旧没有数。
    本轮多了一条**新信息**：产品进程当时在跑（`pgrep` 现读 pid 33535，装的是 R339 那一版），
    所以 `already_running` 那颗出口并未生效，三颗"读不到"里**只剩**锁屏这一颗挡着 ——
    这一单剩下的仍然只有「人解锁之后那三格」，尺这边没有可修的东西（不许为了绿而放宽 Δ=8 那条分辨线）。
"""


def run_json():
    out = subprocess.run(
        [u"gh", u"run", u"view", RUN, u"--json", u"status,conclusion"],
        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if out.returncode != 0:
        raise SystemExit(u"CI_READ_REFUSED gh run view 抛了：%s"
                          % out.stderr.decode(u"utf-8", u"replace").strip())
    return json.loads(out.stdout.decode(u"utf-8", u"replace"))


def once(text, anchor, replacement):
    n = text.count(anchor)
    if n != 1:
        raise SystemExit(u"ANCHOR_hits=%d 锚点不唯一：%.40s…" % (n, anchor))
    return text.replace(anchor, replacement, 1)


def rd(path):
    return io.open(path, encoding=u"utf-8").read()


def wr(path, text):
    io.open(path, u"w", encoding=u"utf-8").write(text)


def main():
    data = run_json()
    status, conclusion = data[u"status"], data[u"conclusion"]
    sys.stdout.write(u"ZHUIJI_CI 现读 RUN=%s sha=%s status=%s conclusion=%s\n"
                     % (RUN, SHA, status, conclusion))
    if status != u"completed":
        sys.stdout.write(u"ZHUIJI_NOT_WRITTEN 这一跑还没结论 ⇒ 只登记不写盘（R140）\n")
        return 3

    state = rd(STATE)
    before_layers = len(re.findall(u"(?m)^> ##", state))
    state2 = once(state, ANCHOR_A, BLOCK_A.format(conclusion=conclusion, status=status))
    backlog = rd(BACKLOG)
    backlog2 = backlog.rstrip(u"\n") + u"\n" + BLOCK_B

    wr(STATE, state2)
    wr(BACKLOG, backlog2)

    after = rd(STATE)
    after_layers = len(re.findall(u"(?m)^> ##", after))
    ok_ci = (u"RUN=%s ↔ %s %s/%s" % (RUN, SHA, status, conclusion)) in after
    ok_real = u"REALSCREEN_NOT_RUN display_channel" in after
    ok_bl = after_layers == before_layers and u"395 追记（R340 追记二" in rd(BACKLOG)
    sys.stdout.write(u"ZHUIJI_R340b 配对=%s 真机格=%s 层数=%d→%d 395追记=%s\n"
                     % (u"是" if ok_ci else u"否", u"是" if ok_real else u"否",
                        before_layers, after_layers, u"是" if ok_bl else u"否"))
    if not (ok_ci and ok_real and ok_bl):
        raise SystemExit(u"ZHUIJI_VERIFY_FAILED 写后复核没过，别提交")
    sys.stdout.write(u"R340B_ZHUIJI_OK\n")
    return 0


if __name__ == u"__main__":
    sys.exit(main())

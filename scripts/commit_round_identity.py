#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R564：commit subject 的 `Rnnn` 前缀与它自己的轮次身份行（`第 N 轮 / Round M`）必须对得上。

**只管未来**：判的范围是 `origin/main..HEAD`（本轮还没推出去的那一批）；这个范围为空时退化成
只判 HEAD。已推的历史**一律不重判** —— 理由有两条，都是账里写过的：

1. R534 的口径：未推可以 amend，已推不许。红了唯一合法的修法是对**未推**那一笔改写，
   所以把范围钉在"还改得动"的那一段，守卫才有牙。
2. R563 的 A 笔 `64d3192` 前缀写成「R562 A：」而它自己的身份行是 `第 562 轮 / Round 560`（= R563）。
   那一笔已经推出去了 ⇒ 不许 amend ⇒ 历史上永久留一条错标签。若守卫判全部历史，就只能给它开豁免，
   而"契约不能靠豁免还"（R188）。判未推的那一批 ⇒ **这条豁免根本不需要写**。

轮次身份是仓库里既有的映射，不是本脚本新造的数：`Rnnn = 第 nnn-1 轮 = Round nnn-3`
（现读对照：R564 = 第 563 轮 / Round 561；R563 = 第 562 轮 / Round 560）。

三种坏法各自有名字，各自会红：
- `不一致`：前缀与身份行都在，但算出来不是同一个轮次（= `64d3192` 那一族的形状）。
- `身份缺失`：前缀在而正文/标题里找不到 `第 N 轮` ⇒ 守卫无从判起，不许静默放过（R488：
  "有内容不足必须红"）。
- `无R前缀`：这一笔连 `Rnnn` 前缀都没有 ⇒ 按仓库惯例本轮批次里每一笔都该带，缺了就是漏登记。
- `笔=0`：一条都没判到 ⇒ 具名红，不许读成"全绿"（这是所有"只打印失败"通道的老病）。
"""
from __future__ import annotations

import re
import subprocess
import sys

ROOT = "/Users/wangziyi/Codex_Project0"
SEP = "\x1e"

PREFIX_RE = re.compile(r"^R(\d{2,4})(?![0-9])")
ROUND_RE = re.compile(r"第\s*(\d+)\s*轮")
LABEL_RE = re.compile(r"Round\s*(\d+)")


def judge(subject: str, body: str) -> list[str]:
    """返回这一笔的问题清单（空 = 一致）。纯函数，真值表在电池里钉。"""
    findings: list[str] = []
    message = subject + "\n" + body
    prefix = PREFIX_RE.match(subject.strip())
    if prefix is None:
        findings.append("无R前缀")
        return findings
    declared = int(prefix.group(1))
    rounds = [int(x) for x in ROUND_RE.findall(message)]
    if not rounds:
        findings.append("身份缺失")
        return findings
    for seen in sorted(set(rounds)):
        if seen != declared - 1:
            findings.append("不一致:R%d≠第%d轮" % (declared, seen))
    labels = [int(x) for x in LABEL_RE.findall(message)]
    for seen in sorted(set(labels)):
        if seen != declared - 3:
            findings.append("不一致:R%d≠Round%d" % (declared, seen))
    return findings


def collect(scope: str) -> list[tuple[str, str, str]]:
    """取 `scope` 里每一笔的 (短 sha, subject, body)。"""
    proc = subprocess.run(
        ["git", "log", scope, "--format=%h%x00%s%x00%b" + SEP],
        cwd=ROOT, capture_output=True, text=True, timeout=120)
    if proc.returncode != 0:
        raise RuntimeError("git log 失败：" + (proc.stderr.strip() or "exit=%d" % proc.returncode))
    out: list[tuple[str, str, str]] = []
    for chunk in proc.stdout.split(SEP):
        chunk = chunk.strip("\n")
        if not chunk:
            continue
        sha, _, rest = chunk.partition("\x00")
        subject, _, body = rest.partition("\x00")
        out.append((sha, subject, body))
    return out


def main() -> int:
    try:
        commits = collect("origin/main..HEAD")
        scope = "origin/main..HEAD"
    except RuntimeError as exc:
        print("COMMIT_ROUND_IDENTITY_RESULT=unreadable %s" % exc)
        return 2
    if not commits:
        # 已经推齐了（或第一次跑之前）⇒ 退化成只判 HEAD，绝不允许"零条也算通过"。
        commits = collect("HEAD~1..HEAD")
        scope = "HEAD~1..HEAD（未推的为空 ⇒ 退化）"
    bad: list[str] = []
    no_prefix = 0
    no_identity = 0
    for sha, subject, body in commits:
        findings = judge(subject, body)
        for f in findings:
            if f == "无R前缀":
                no_prefix += 1
            elif f == "身份缺失":
                no_identity += 1
            bad.append("%s %s：%s" % (sha, f, subject[:60]))
    print("COMMIT_ROUND_IDENTITY 范围=%s 笔=%d 无R前缀=%d 身份缺失=%d 不一致=%d"
          % (scope, len(commits), no_prefix, no_identity,
             sum(1 for line in bad if line.split(" ", 2)[1].startswith("不一致"))))
    for line in bad:
        print("  " + line)
    if not commits:
        print("COMMIT_ROUND_IDENTITY_RESULT=red 原因=笔=0（一条都没判到，不许读成全绿）")
        return 1
    if bad:
        print("COMMIT_ROUND_IDENTITY_RESULT=red")
        return 1
    print("COMMIT_ROUND_IDENTITY_RESULT=ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())

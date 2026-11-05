#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import io
import os
import re
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DOC = os.path.join(ROOT, "docs", "FOLD_DUO_SPEC_2026-11-03.md")

ANCHOR_PREFIX = u"   - **R579 的核实（§4 第一条那句答案从此带"
NEW_BULLET = u"""   - **R580 的核实（BACKLOG 654 那张 D12 映射表从此是**会红的活门**，不再只是快照 · 纯插入 · 上面各条原文一条不删）**：R575 建那张表时写下的是"八条 × 通道 × 声明态"这一句**描述**，R578 给它配了按行类别快照防"声明被人改"，但整张表仍然不会回答派单 ② 那一问 —— **产品源码里真出现某条 clause 所需的对象时，那一行必须翻面，翻不动就红**。本轮把它做成这条性质：A 那把尺按名字认（`foldAngle`/`blurRadius`/`CAMetalLayer`/`MTKView`），**B 那把按形状认**（一份 `.metal` 源文件，或代码里出现 `CIFilter`/`CIGaussianBlur`/`AEAGaussianBlur`/`MTLRenderPipelineState`/`CAFilter`/`layer.filters`），判法是四分支纯函数 `缺席 / 由A认得_A=n / 现扫瞎_只有B认得_B=n / 目录读不到_A=…_B=…`；翻面机 `d12RequiredFlips` 按**表体的通道列**派生名单（驱动到位⇒五行翻、alpha 到位⇒两行翻、`屏上帧间隔不超标` 永远不许被对象翻动 —— 它缺的是环境不是对象）。今天产品树逐字 `D12_LIVE_GATE A按名字文件数=0 B按形状文件数=0 判=缺席 红路=无 待翻行数=7 本轮该翻=0 分母=8` ⇒ **`条=8 runner可判=0 只能真机=1 今天无证人=7` 四个数一字未动**，第②段那五件（646/647/653/654/655）一件没少，`STAGE3_FRAME_CRITERIA_HAVE_NO_RUNNER_WITNESS` 照旧等用户对 654 的定向，**第③段着色器一字未写**。⇒ 三格要说准：⑴ **B 只叫醒 A，不替 A 作证** —— `A=0 而 B>0` 报的是"A 的形状集合过期了、要重锚"，不许据此把那五行直接改成可判（认得出 `CIFilter` 不等于角度驱动到位）；⑵ 任一通道给 **-1**（目录读不到）同样红，那是"量不到冒充判过"在这一格的形状；⑶ 活门的绿有两种成因（确实没有对象 / 门瞎了看不见对象到），所以永久入库那一格用**六棵临时树**把两种分开，端到端那两趟由一次性探针（**不入库**、用完删除并给"工作树干净"的证人）点着。同轮读到并修掉一条尺病：A 原先**不剥注释** ⇒ 一份只在注释里写那四个名字、代码里叫 `radius` 的假文件被读成 A=1 ⇒ 一句注释能凭空翻五行，而判法见 `A>0` 就返回 `由A认得` ⇒ **新那条"现扫瞎"的红被假 A 短路挡掉**；补 `codeOnly` 之后今天两种读法都是 0 ⇒ **口径收了、本轮所有读数一字未动**。⇒ 对第③段的实际影响：**将来真写驱动那一笔，这张表会自己叫**（不必靠人记得来改表），而"改表"必须同时补逐帧判据与按行快照，并把是哪个读数支持翻面写进账 —— 这一句从此由刀 M1523/M1524/M1525/M1526 钉着（全 CAUGHT、RESTORE_CLEAN=yes，下一轮 M1527 起）。"""


def main():
    text = io.open(DOC, encoding="utf-8").read()
    lines = [ln for ln in text.split(u"\n") if ln.startswith(ANCHOR_PREFIX)]
    if len(lines) != 1:
        raise SystemExit(u"R579 那条核实锚不唯一：%d" % len(lines))
    anchor_line = lines[0]
    if u"R580 的核实" in text:
        print(u"文档已经有 R580 那一格 ⇒ 跳过（不写第二份）")
        return 0
    if text.count(u"   - **R580 的核实") != 0:
        raise SystemExit(u"意外：新格已在盘上但守卫没认出")
    head, sep, tail = text.partition(anchor_line)
    # `partition` 留下的 `tail` **自带**锚行那一个换行 ⇒ 这里不能再补一个（补了就多一行空行，
    # 行数差变 +2，正好被下面那道事前断言挡住 —— 本轮第一次就撞在这条上）。
    after = head + anchor_line + u"\n" + NEW_BULLET + tail
    # 事前断言：新行插在锚行之后，锚行之前与之后的所有旧行**逐字不动**（R578 那一族：
    # Edit 的 new_string 少写一个换行就会把下一行并上来 ⇒ numstat 出现 −1，账就脏了）。
    before_lines = text.split(u"\n")
    after_lines = after.split(u"\n")
    idx = before_lines.index(anchor_line)
    if len(after_lines) != len(before_lines) + 1:
        raise SystemExit(u"行数差不是 +1（%d → %d）⇒ 拒绝写盘" % (len(before_lines), len(after_lines)))
    if after_lines[:idx + 1] != before_lines[:idx + 1]:
        raise SystemExit(u"锚之前的行被改动 ⇒ 拒绝写盘")
    if after_lines[idx + 2:] != before_lines[idx + 1:]:
        raise SystemExit(u"锚之后的行被改动（少了一个换行就会在这里抓到）⇒ 拒绝写盘")
    if not after_lines[idx + 1].startswith(u"   - **R580 的核实"):
        raise SystemExit(u"新行没落在锚之后 ⇒ 拒绝写盘")
    io.open(DOC, "w", encoding="utf-8").write(after)
    out = subprocess.run([u"git", u"--no-pager", u"diff", u"--numstat", u"--",
                          os.path.relpath(DOC, ROOT)], cwd=ROOT,
                         capture_output=True, text=True).stdout.strip()
    print(u"numstat=%s" % out)
    if out.split(u"\t")[:2] != [u"1", u"0"]:
        raise SystemExit(u"文档那一笔必须是 +1 / −0，实得 %r ⇒ 停手对拍" % out)
    print(u"文档 R580 核实格落了（纯插入一行）")
    return 0


if __name__ == "__main__":
    main()

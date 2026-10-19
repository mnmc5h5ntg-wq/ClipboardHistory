#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''R197 那一节的补落（R198 做的，动机是被抓而不是被提醒）。

电池 `test_curve_gaps.test_real_ledger_has_no_gap_today` 在 R198 台账落盘后立刻红了：
`GAPS=[197]` —— R197 只写了 BACKLOG 221 一条，没写 ITERATION 那一节，曲线中间断了一格。
三本账那侧有 211 的显式申报通道可以豁免，曲线这侧没有：**少一轮就会把均值算错**。

规矩照 R100 那次的教训：补的是**当时真做过的事**，分数按当时实际做的事给（不追认成 R198 的成绩），
并且插进 196 与 198 之间保持升序 —— 插完立刻用断言证明"198 那一节还在、197 在它前面、行数只多了这一节"。
'''
import io, os, re, sys

ROOT = '/Users/wangziyi/Codex_Project0'
PATH = os.path.join(ROOT, 'AGENT_VISUAL_ITERATION.md')

SECTION = u'''## Round 197 · 看图腿：热图梯子「空→最低档」在亮档几乎只靠彩度分开（灰阶比值 1.05），而当时钉着它的判据量的是最大通道差 28/255 —— 过线，所以那天确实绿（2026-10-19 · 产品 0 文件，落成 BACKLOG 221）【R198 补落：这一节当时没写，被 `test_curve_gaps` 以 GAPS=[197] 抓到】

那轮做的是逐屏看图 + 把看到的怀疑换算成数：亮档最低一档与空格子的差几乎全在彩度上，
灰阶对比度比值只有 **1.05**；而当时唯一钉住这条的判据用的统计量是"逐像素最大通道差" = **28/255**（地板 18）
⇒ 判据确实过线，那天的绿是真的绿 —— 但**绿的不是我问的那件事**。于是开 BACKLOG 221，没有当场动判据（预算尽头只落这一条）。
R198 复查时把这条质询拆成两半：亮度那一半是**用错轴**（R51/R53 早已证伪 —— `空` 走 `primary` 灰、四档走 `accent` 蓝，
那一步差的是色相不是明度）；能测的那一半（只靠彩度分开的两档，在色觉障碍下会不会并成一步）由 R198 立判据量完
⇒ 绿色盲模拟之后仍是五档，221 结案、梯子不动。

**本轮的欠账（补落时如实记，不追认成成绩）**：三本账只落了 BACKLOG 一本（这正是 211 申报通道管的事，
R198 已把 197 显式申报进去）；看图那一步没有留下日志文件，两个数只存在于 BACKLOG 正文里 ⇒ 可复核性打折；
开单时提的轴是错的，第二天才被自己推翻 ⇒ 判据有效性按"开出了可测的一半、但也押错了一次"给。

### 3. 七维度自评（本轮 · R198 补落，分数按当时实际做的事给）

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 12/15 | 真看了热图两档的帧并把"看着淡"换算成数（比值 1.05、最大通道差 28/255）；但没有新画面产生（产品 0 文件、帧沿用上一遍） |
| 判据有效性 | 11/15 | 只开单没立判据；而且开单押的是**亮度轴**，R198 判成用错轴（R51/R53 早已证伪过同一件事）—— 留下的一半（色觉模拟）才是能测的 |
| 假绿防御 | 13/15 | 没有把"判据过线"说成"这里没问题"：条目原话是"过线，所以今天绿"，并据此开单；扣分在**没有当场去查这根轴对不对**，隔天才发现押错 |
| 产品面推进 | 9/15 | 画面 0 改动；推进的是问题定义（把一个形容词拆成两个数） |
| 台账一致性 | 8/15 | 三本账只落一本（UI_AUDIT 与 CHANGELOG 到今天仍没有 R197 标题行，走 211 的显式申报），且曲线断档由电池在 R198 当场抓到 ⇒ 这是真欠，不是格式问题 |
| 交付诚实性 | 14/15 | 明写"预算尽头只落这一条"，没有把半批说成整批 |
| 可复核性 | 11/15 | 两个数在 BACKLOG 221 正文里可查，但没留原始日志 ⇒ 复算要重跑一遍看图；R198 补的这条也没能补出当时的日志 |
'''

ANCHOR = u'## Round 198 · '


def main():
    text = io.open(PATH, encoding='utf-8').read()
    if u'## Round 197 · ' in text:
        print('ALREADY_BACKFILLED ⇒ 不重复插')
        return 0
    hits = [i for i, l in enumerate(text.split(u'\n')) if l.startswith(ANCHOR)]
    if len(hits) != 1:
        raise SystemExit('ANCHOR %r 命中 %d 次（要 1）⇒ 不写盘' % (ANCHOR, len(hits)))
    before = len(re.findall(u'^## Round \\d+ · ', text, re.M))
    lines = text.split(u'\n')
    idx = hits[0]
    lines[idx:idx] = (SECTION.rstrip(u'\n') + u'\n').split(u'\n')
    new = u'\n'.join(lines)
    after = len(re.findall(u'^## Round \\d+ · ', new, re.M))
    if after != before + 1:
        raise SystemExit('COUNT 节数 %d→%d（要 +1）⇒ 不写盘' % (before, after))
    order = [int(m) for m in re.findall(u'^## Round (\\d+) · ', new, re.M)]
    # 全局升序这条**不能**用：盘上早就有一处历史倒挂（开头是 1, 3, 2 —— 第 2 节晚写了一天）。
    # 第一版我在这里写了 `order != sorted(order)`，结果脚本对自己红、把一次正确的插入拦下来 ——
    # 钉死之前要先读历史形状（R102 的教训，第二次踩）。要保的是"我没新增倒挂"，不是"整本账有序"。
    def descents(seq):
        return [(seq[i], seq[i + 1]) for i in range(len(seq) - 1) if seq[i] > seq[i + 1]]
    old_order = [int(m) for m in re.findall(u'^## Round (\\d+) · ', text, re.M)]
    if descents(order) != descents(old_order):
        raise SystemExit('NEW_DESCENT 倒挂从 %s 变成 %s ⇒ 不写盘'
                         % (descents(old_order), descents(order)))
    i197 = order.index(197)
    if not (order[i197 - 1] == 196 and order[i197 + 1] == 198):
        raise SystemExit('WRONG_PLACE 197 落在 %s 与 %s 之间（要 196 与 198）⇒ 不写盘'
                         % (order[i197 - 1], order[i197 + 1]))
    for must in (u'## Round 196 · ', u'## Round 198 · '):
        if new.count(must) != 1:
            raise SystemExit('LOST %s 现在出现 %d 次 ⇒ 不写盘' % (must, new.count(must)))
    seven = re.findall(u'^\\| [^|]+\\| (\\d+)/15 \\|', SECTION, re.M)
    if len(seven) != 7:
        raise SystemExit('SEVEN_DIM_SHAPE 补落那节读到 %d 行（要 7）' % len(seven))
    dropped = [l for l in text.split(u'\n') if l not in new.split(u'\n')]
    if dropped:
        raise SystemExit('DROPPED_LINES %d 行（示例 %r）⇒ 这是替换不是插入，不写盘' % (len(dropped), dropped[:1]))
    io.open(PATH, 'w', encoding='utf-8').write(new)
    print('R197_BACKFILL_WRITTEN 节数 %d→%d 尾部=%s seven_sum=%d'
          % (before, after, order[-4:], sum(int(x) for x in seven)))
    return 0


if __name__ == '__main__':
    sys.exit(main())

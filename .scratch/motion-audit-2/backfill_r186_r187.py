#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''R189 的第 0 步（本笔落地）：把 Round 186 / 187 两节七维自评**补记**进 AGENT_VISUAL_ITERATION.md，并在 BACKLOG 开 213 记这笔债。

为什么必须补而不是豁免：`scripts/curve_from_ledger.py` 那条真产物闸门报的是
`GAPS=[186, 187]` ⇒ 阶段二的契约是「每轮都要有七维度自评」，那两轮只动了 BACKLOG、根本没做自评。
把申报通道延伸到这里是**掩盖**，不是修账 —— 所以 211 的名册只管「三本账的标题」，这里补的是缺失的自评本身。

诚实要求（脚本里都钉了）：
① 两节都要在标题与正文里显式写「R188 补记」，不许伪装成当时就写了；
② 分数按那两笔**当时实际做的事**给，其中「台账一致性」因为只动了一本账必须给低分；
③ 表格必须是 7 行 `x/15` 形状（仪器按这个形状算分，散文总分它读不到 ⇒ 会被当成断档）。
'''
import io
import os
import re
import sys

ROOT = '/Users/wangziyi/Codex_Project0'
IT = os.path.join(ROOT, 'AGENT_VISUAL_ITERATION.md')
BL = os.path.join(ROOT, 'AGENT_BACKLOG.md')

R186 = u'''
## Round 186 · 210 追记 2：绑定链查到底（R188 补记 —— 这一笔当时只动了 AGENT_BACKLOG.md，七维自评没做，现在补）

补记的理由（不是套分）：闸门 `curve_from_ledger.py` 报 `GAPS=[186, 187]`，而阶段二的契约写着**每轮**都要有七维度自评。
这一笔实际做的事：把「药丸为什么在右段」里「是不是测试环境带进来的」这一支查到底 —— ① `content-empty` 的 store 是
`HistoryStore(clipboardWriter:persistence:retentionPolicy:)`（`UICaptureHarness.swift:3875`），init 没有 filter 参数、也不从存档恢复；
② filter 只能被 `.updateFilter` 改（`HistoryStore.swift:561`），夹具全程没调用；③ 选择绑定是直连的
（`HistorySidebarView.swift:19-22`）；④ 全仓侧栏/内容区没有 `AppStorage` / `UserDefaults` 持久化 filter（grep 0 命中）
⇒ 渲染时 `selection == .all` 成立，"右段"不是夹具或持久化带进来的。**这一结论到今天仍然成立**，被撤回的是下一笔（187）对「亮区=药丸」的归位，不是这一格。

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 5/15 | 没重捕帧、没看图，这一腿当时是空的（补记也不能给它加出不存在的眼睛） |
| 判据有效性 | 11/15 | 没写新判据；做的是排除法，产出是「下一步该量什么」的两条可执行分辨实验 |
| 假绿防御 | 13/15 | 拒绝在病根未钉死时改 `slidingPill`，并把「改错地方 50% 概率」写进账 |
| 产品面推进 | 9/15 | 产品 0 文件；但把一条候选产品缺陷收窄成了「只剩归位没做」 |
| 台账一致性 | 4/15 | **只动了 BACKLOG**：没有 U 条目、没有七维自评、没有 CHANGELOG ⇒ 这一格就是这笔债本身 |
| 交付诚实性 | 13/15 | 当时明写了「这一步做完之前不动产品」，没有把排除法说成结论 |
| 可复核性 | 14/15 | 四处源码位置 + 一条 grep 计数，复查命令是具体的 |

'''

R187 = u'''
## Round 187 · 210 追记 4：把「病根钉死」写了出去，而它在下一笔被自己推翻（R188 补记 —— 同样当时只动了 BACKLOG）

这一笔实际做的事：用排除法给出结论「同一帧里侧栏标题是『0 条记录』(=`.all`) 而亮区在收藏那一段 ⇒ 是 `slidingPill` 的几何与选中态反号」。
排除的两条当时是站得住的（`hoverFill` 真值表 0.06 量级量不出主色纯白 65.4%；绑定链已证 `selection == .all`）。
**但它把「亮区=药丸、且落在右半」当成了已钉死的读数** —— R188（`8b90efe`）在同一批像素上用逐行尺重测，
亮区与底轨同宽（496px vs 498px）、且那把尺的 `rel=(中心-轨左)/(轨宽/2)` 把正中(1.0)标成了右半 ⇒ 结论撤回、210 退回未钉死。
所以这里的「假绿防御」按结果给分，不按当时的态度给分：这是本审计到目前为止最贵的一次读数过度自信。

| 维度 | 分 | 依据 |
| --- | --- | --- |
| 真实视觉审查 | 6/15 | 复用的是旧帧、没重捕；「看图」实际是看像素尺的输出，而尺的口径没和控件同轴 |
| 判据有效性 | 12/15 | 没新增判据；产出的三条排除后来都被复用，但第四条（亮区身份）当时没量 |
| 假绿防御 | 7/15 | **把未钉死的读数写成钉死**，并在 STATE 里生成了「修 210」的靶 ⇒ 若照做就会改错地方 |
| 产品面推进 | 9/15 | 产品 0 文件（这条这次是对的，但当时给的理由不成立） |
| 台账一致性 | 4/15 | 只动 BACKLOG；且这一节是补写的，当时的账里连自评都没有 |
| 交付诚实性 | 10/15 | 说了「不动产品」，也说「钉死」；前者救了它，后者是过度声明 |
| 可复核性 | 13/15 | commit 号、真值表出处、标题行出处都在，能被 R188 逐条复查（也确实被推翻了） |

'''

BL213 = u'''**213. 阶段二的「每轮七维自评」在 R186/R187 两轮被跳过：`curve_from_ledger.py` 报 `GAPS=[186, 187]`（R188 量到，本笔补记两节自评）**

形状：`GAPS=[186, 187]`、`ROUNDS=187 first=1 last=188`、`SCORES_BY_ROUND 183=88 184=90 185=92 188=87`。
成因（不是猜测，是这两笔自己的 commit）：`a90e380` 与 `2720e72` + `81105b0` 只往 `AGENT_BACKLOG.md` 追加了 210 的追记，
既没有 U 条目、也没有七维自评、也没有 CHANGELOG 标题 —— 于是 211 的名册把它们当「单本账笔次」豁免掉是**对的**（三本账标题确实没有），
但曲线仪器要的是「每轮都有自评」这件事本身，那一条不能被名册豁免，否则阶段二的契约就靠名册悄悄减了 2 轮。
处置：补记两节（标题与正文都显式写「R188 补记」，分数按当时的实际动作给，「台账一致性」各 4/15 —— 债要体现在分上），
并把这条留在账里：**下一轮再出现「只动一本账」的笔次，必须在同一笔里补自评**，不许再靠补记还债。
'''


def read(p):
    if not os.path.exists(p):
        raise SystemExit('MISSING_FILE %s ⇒ 拒绝写盘' % p)
    return io.open(p, encoding='utf-8').read()


def rows_in(block):
    return len(re.findall(r'^\| [^|]+ \| \d+/15 \|', block, re.M))


def main():
    for tag, block in ((u'186', R186), (u'187', R187)):
        if rows_in(block) != 7:
            raise SystemExit('TABLE_SHAPE %s 的七维表不是 7 行 x/15（读到 %d）' % (tag, rows_in(block)))
        if R188_needle(tag) in read(IT):
            raise SystemExit('DUMP_ALREADY_WRITTEN Round %s 已在盘上 ⇒ 不重复补' % tag)
    it = read(IT).rstrip(u'\n') + u'\n' + R186.rstrip(u'\n') + u'\n' + R187.rstrip(u'\n') + u'\n'
    bl = read(BL).rstrip(u'\n') + u'\n\n' + BL213.rstrip(u'\n') + u'\n'
    nums = sorted(int(m) for m in re.findall(r'^\*\*(\d{2,3})\. ', bl, re.M))
    if nums[-1] != 213:
        raise SystemExit('MAX_BACKLOG %d（要 213）' % nums[-1])
    if u'GAPS=[186, 187]' not in bl:
        raise SystemExit('THIN_213 没把闸门原文写进账')
    io.open(IT, 'w', encoding='utf-8').write(it)
    io.open(BL, 'w', encoding='utf-8').write(bl)
    print(u'BACKFILL_WRITTEN rounds=186,187 backlog_max=213')
    return 0


def R188_needle(tag):
    return u'## Round %s · ' % tag


if __name__ == '__main__':
    sys.exit(main())

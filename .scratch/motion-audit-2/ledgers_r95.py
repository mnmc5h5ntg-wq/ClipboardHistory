#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R95 的台账落盘：七格 STAGES，每一格都要么已经落盘、要么当场补上，缺一格就非零退出。

为什么这一轮它是**校验器**而不是生成器（写在这里，不留到下一次被问）：
R93 那次的事故是 `ledgers_r93.py` 的 STAGES 里根本没有 decisions 那一格 ⇒
D-151 被两处标题引用却从来没有正文（R94 补记 + 新守卫 `test_ledger_ids`）。
那一课的正解不是"生成器写得更全"，而是**每一格都必须以"落没落盘"被打个对勾**：
生成器漏一格，是因为漏的那一格它自己不知道；校验器漏一格，只要 STAGES 里有条目就会红。
本轮正文是三段临时脚本写的（`/tmp/r95_ledger*.py`，一次性、不重跑），
所以这里把"正文在不在"升成七条硬断言 —— 它防的正是"我以为我写了"。

跑法：PYTHONUTF8=1 python3 .scratch/motion-audit-2/ledgers_r95.py
退出码：0 = 七格齐全；1 = 有格子没落盘（会点名是哪一格、缺哪个标记）。
"""
import io
import os
import subprocess
import sys

REPO = '/Users/wangziyi/Codex_Project0'

# (格名, 文件, 必须出现的标记, 这一格承重的那句话)
STAGES = [
    ('ui_audit', 'AGENT_UI_AUDIT.md',
     u'## 第 97 轮 · R95',
     u'轮次标题：审计那一侧的编号是 R+2 ⇒ 第 97 轮'),
    ('backlog_updates', 'AGENT_BACKLOG.md',
     u'R95 结案',
     u'135 的结案段（结论粘住 + PROBE_ORDER_INTERLEAVED + M521 从洞变 CAUGHT）'),
    ('backlog_132', 'AGENT_BACKLOG.md',
     u'R95 更新（工具上 runner 了，栈还没读）',
     u'132 的进度：sample 落在 kill 之前，但 runner 那份栈仍欠'),
    ('backlog_new', 'AGENT_BACKLOG.md',
     u'138. ',
     u'新开 137（并列未覆盖）与 138（横向 5.5pt）'),
    ('decisions', 'AGENT_DECISIONS.md',
     u'### D-153（R95）',
     u'本轮的决定（判据问"是不是同一个数"）—— R93 就是漏了这一格'),
    ('visual', 'AGENT_VISUAL_ITERATION.md',
     u'## Round 95 ·',
     u'Round 95 全文（含七维度自评与验证段）'),
    ('changelog', 'CHANGELOG.md',
     u'### 产品（R95）',
     u'产品那一节；同一条守卫还要求 `## [Unreleased]` 只出现一次'),
    ('manual_batch', 'docs/MANUAL_TEST_v1.4.9_round3.md',
     u'## 批次 74',
     u'真机那一腿：录制中态 + 亮档侧栏逐枚点名'),
    ('state_rotation', 'AGENT_STATE.md',
     u'本地 · R95 / 第 97 轮收尾',
     u'第 3 行换成本轮，R94 那行降为"上一轮"引用'),
]


def main():
    bad = []
    for name, path, marker, why in STAGES:
        text = io.open(os.path.join(REPO, path), encoding='utf-8').read()
        hits = text.count(marker)
        if hits == 1:
            print('OK      %-16s %s' % (name, path))
        else:
            bad.append((name, path, hits))
            print('MISSING %-16s %s 标记命中 %d 次（期望 1）：%s' % (name, path, hits, why))
    # 编号一致性交给守卫本身（它查的是"被引用的 D 必须存在"，比这里更严）
    proc = subprocess.run([sys.executable, '-m', 'unittest', 'scripts.tests.test_ledger_ids'],
                          cwd=REPO, capture_output=True, text=True)
    tail = [l for l in proc.stderr.splitlines() if l.startswith(('Ran ', 'OK', 'FAILED'))]
    print('LEDGER_IDS exit=%d %s' % (proc.returncode, ' '.join(tail)))
    # CHANGELOG 那一格的红字本轮真的红过一次（我插成两节标题），所以这条计数不是装饰
    cl = io.open(os.path.join(REPO, 'CHANGELOG.md'), encoding='utf-8').read()
    n_unreleased = cl.count('## [Unreleased]')
    print('CHANGELOG_UNRELEASED_HEADINGS=%d（必须 1）' % n_unreleased)
    if bad or proc.returncode != 0 or n_unreleased != 1:
        print('LEDGERS_R95_INCOMPLETE 缺 %d 格' % (len(bad) + (proc.returncode != 0)
                                                  + (n_unreleased != 1)))
        return 1
    print('LEDGERS_R95_OK=%d/%d' % (len(STAGES), len(STAGES)))
    return 0


if __name__ == '__main__':
    sys.exit(main())

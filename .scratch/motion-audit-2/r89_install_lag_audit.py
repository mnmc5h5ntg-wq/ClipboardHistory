#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""装机落后审计：哪一轮改了产品却没换装（R89 现场开的那条）。

起因：做最终报告收口审计时对了一遍台账，发现 **R84 改了 1 个产品文件而整段里没有一行换装记录**，
而 R85–R89 都是"0 个产品文件 ⇒ 不换装"。也就是说本机装的还是 R84 之前的包，
而帧、判据、账本描述的都是 R84 之后的产品。规矩（"交付默认自己构建换装"）立过，但**没有守卫**，
所以它只能被"想起来"而不能被"跑出来"——这正是这一族反复犯的形状。

判据形状（每一段 `## Round N` 自成一格）：
  * 从"位点清单"那一行读 `(\d+) 个产品文件`（本轮的自报数）；
  * 装过的证据 = 段内出现 `INSTALL_RESULT=ok` 或 `INSTALL_SHA_MATCH=1`；
  * 明确声明不装的证据 = 段内出现"不换装"（它必须自带理由，理由这一格本脚本不判，交给人读）。
产品数 > 0 而两条证据都没有 ⇒ 点名（RED）。

用法：PYTHONUTF8=1 python3 .scratch/motion-audit-2/r89_install_lag_audit.py [台账路径]
退出码：0 = 没有落后；1 = 至少一轮改了产品却没换装（也不没换装的理由）。
"""
import io
import os
import re
import sys

DEFAULT = '/Users/wangziyi/Codex_Project0/AGENT_VISUAL_ITERATION.md'
HEAD = re.compile(r'^## (Round \d+[a-z]?) ·', re.M)
PRODUCT_COUNT = re.compile(r'(\d+) 个产品文件')
INSTALLED = ('INSTALL_RESULT=ok', 'INSTALL_SHA_MATCH=1')
DECLARED_NOT = ('不换装', '未换装')


def sections(text):
    hits = list(HEAD.finditer(text))
    for i, m in enumerate(hits):
        end = hits[i + 1].start() if i + 1 < len(hits) else len(text)
        yield m.group(1), text[m.start():end]


def main(argv):
    path = argv[0] if argv else DEFAULT
    if not os.path.exists(path):
        print('INSTALL_LAG_AUDIT_LOG_UNREADABLE=%s' % path)
        return 1
    text = io.open(path, encoding='utf-8').read()
    reds, oks, skipped = [], [], []
    for head, body in sections(text):
        counts = PRODUCT_COUNT.findall(body)
        if not counts:
            skipped.append(head)          # 老轮次没有这一行（规矩是后来立的），不猜
            continue
        touched = max(int(c) for c in counts)
        installed = any(k in body for k in INSTALLED)
        declared = any(k in body for k in DECLARED_NOT)
        # 0 个产品文件 ⇒ 本来就不该换装，不需要任何证据（把它判成红是尺过紧：
        # 那会让 8 个"确实没动产品"的轮次一起红，而红里唯一的真信号被淹掉）。
        if touched == 0:
            oks.append(head)
        elif installed or declared:
            oks.append(head)
        else:
            reds.append((head, touched))
    print('INSTALL_LAG_ROUNDS total=%d 有产品数=%d 无该行(老轮次,不判)=%d'
          % (len(list(HEAD.finditer(text))), len(oks) + len(reds), len(skipped)))
    print('INSTALL_LAG_OK=%d' % len(oks))
    for head, touched in reds:
        print('INSTALL_LAG_RED=%s 自报产品文件=%d 而段内既无换装记录、也无"不换装+理由' % (head, touched))
    if skipped:
        print('INSTALL_LAG_NOT_JUDGED=%s' % ','.join(skipped))
    return 1 if reds else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

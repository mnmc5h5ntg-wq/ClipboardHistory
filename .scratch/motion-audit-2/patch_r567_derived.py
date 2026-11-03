# -*- coding: utf-8 -*-
"""R567 派生格第二趟：门落盘之后现读，把 STATE ⑥ 与 FINAL_REPORT 那两格抄成门的数。

规矩：这两格**只许抄门**（R560 那次是手推成 0 被 PRODUCT_STREAK_LEDGER_STALE 抓住）。
"""
import io
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run(args):
    proc = subprocess.Popen(args, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = proc.communicate()[0].decode('utf-8', 'replace')
    return proc.returncode, out


def main():
    py = sys.executable
    code, streak_out = run([py, 'scripts/product_streak.py'])
    line = re.search(r'PRODUCT_STREAK ledger_round=\d+ streak=\d+[^\n]*', streak_out)
    if line is None or code != 0:
        raise SystemExit('product_streak 没打出行（exit=%d）：%s' % (code, streak_out[-400:]))
    streak = re.search(r'streak=(\d+)', line.group(0)).group(1)
    print(line.group(0))

    code, clearing_out = run([py, 'scripts/ledger_absence_claims.py'])
    cells = re.search(r'LEDGER_ABSENCE_CLAIMS 格=(\d+) 声明=(\d+)', clearing_out)
    verdict = re.search(r'LEDGER_ABSENCE_RESULT=[^\n]*', clearing_out)
    if cells is None or verdict is None or code != 0:
        raise SystemExit('清账没打出行（exit=%d）：%s' % (code, clearing_out[-400:]))
    clearing = '格=%s 声明=%s，%s' % (cells.group(1), cells.group(2), verdict.group(0).strip())
    print(clearing)

    code, sources_out = run([py, 'scripts/report_sources_cell.py'])
    sources = re.search(r'SOURCES_CELL [^\n]*', sources_out)
    if sources is None or code != 0:
        raise SystemExit('sources 格没打出行（exit=%d）：%s' % (code, sources_out[-400:]))
    print(sources.group(0))

    path = os.path.join(ROOT, 'AGENT_STATE.md')
    text = io.open(path, encoding='utf-8').read()
    text = text.replace(u'@@STREAK@@', streak)
    text = text.replace(u'@@STREAK_LINE@@', line.group(0))
    text = text.replace(u'@@CLEARING@@', clearing)
    text = text.replace(u'@@SOURCES@@', sources.group(0).strip())
    io.open(path, 'w', encoding='utf-8').write(text)
    print('STATE ⑥ 抄完')

    path = os.path.join(ROOT, 'AGENT_FINAL_REPORT.md')
    text = io.open(path, encoding='utf-8').read()
    cell = re.search(u'产品面连续零改动轮数 = \\*\\*\\d+\\*\\*', text)
    if cell is None:
        raise SystemExit('FINAL_REPORT 里找不到「产品面连续零改动轮数 = **N**」那一格')
    text = text.replace(cell.group(0), u'产品面连续零改动轮数 = **%s**' % streak, 1)
    io.open(path, 'w', encoding='utf-8').write(text)
    print('FINAL_REPORT 那一格抄成 %s' % streak)

    code, check_out = run([py, 'scripts/product_streak.py', '--check'])
    print(check_out.strip().splitlines()[-1])
    if code != 0:
        raise SystemExit('product_streak --check 仍红')
    return 0


if __name__ == '__main__':
    sys.exit(main())

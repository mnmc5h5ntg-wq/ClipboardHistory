# -*- coding: utf-8 -*-
"""Swap the R565 补全 bullet to sit after the R565 补段 bullet (chronology inside §18)."""
import io

PATH = '/Users/wangziyi/Codex_Project0/AGENT_FINAL_REPORT.md'
with io.open(PATH, encoding='utf-8') as handle:
    lines = handle.read().split('\n')

first = [i for i, l in enumerate(lines) if l.startswith(u'- **R565 补全（2026-11-04')]
second = [i for i, l in enumerate(lines) if l.startswith(u'- **R565 补段（同一轮续写')]
assert len(first) == 1 and len(second) == 1, (first, second)
i, j = first[0], second[0]
assert j == i + 1, (i, j)
lines[i], lines[j] = lines[j], lines[i]

with io.open(PATH, 'w', encoding='utf-8') as handle:
    handle.write('\n'.join(lines))
print('swapped at %d/%d' % (i + 1, j + 1))

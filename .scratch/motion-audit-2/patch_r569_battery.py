# -*- coding: utf-8 -*-
"""R569 电池那一格的补笔：台账落盘**之后**跑完电池，再把门自己打印的那一行抄进两处 @@BATTERY@@。

为什么单独一支：D-333 那条顺序规矩（电池必须在台账之后跑，否则它守的是上一版的账），
而账里要写电池的数 ⇒ 只能两趟。这一支要求替换之后**七本全 0** 个未渲染占位符。
"""
import io
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BOOKS = ('AGENT_STATE.md', 'AGENT_UI_AUDIT.md', 'AGENT_VISUAL_ITERATION.md',
         'CHANGELOG.md', 'AGENT_FINAL_REPORT.md', 'AGENT_BACKLOG.md', 'AGENT_DECISIONS.md')


def read(path):
    with io.open(path, encoding='utf-8') as handle:
        return handle.read()


def write(path, text):
    with io.open(path, 'w', encoding='utf-8') as handle:
        handle.write(text)


def main():
    log = sys.argv[1] if len(sys.argv) > 1 else '/tmp/r569-battery.log'
    if not os.path.exists(log):
        raise SystemExit('电池日志不在盘上：%s ⇒ 拒绝写账' % log)
    text = read(log)
    ran = re.findall(r'^Ran (\d+) tests[^\n]*', text, re.M)
    if not ran:
        raise SystemExit('电池没打出 `Ran N tests` ⇒ 那一格没有数可抄')
    tail = text.splitlines()[-1] if text.strip() else ''
    verdict = re.findall(r'(OK \(skipped=\d+\)|FAILED \([^\n]*\))', text)
    if not verdict:
        raise SystemExit('电池没打结论行（既不是 OK 也不是 FAILED）⇒ 只能记未读到，不能写"应该绿"')
    line = 'Ran %s / %s、退出码见 %s 末尾' % (ran[-1], verdict[-1], log)
    print('BATTERY_CELL', line)

    for name in BOOKS:
        path = os.path.join(ROOT, name)
        body = read(path)
        if u'@@BATTERY@@' not in body:
            continue
        write(path, body.replace(u'@@BATTERY@@', line))
        print('%s 补了电池那一格' % name)
    for name in BOOKS:
        leftover = set(re.findall(r'@@[A-Za-z0-9_]+@@', read(os.path.join(ROOT, name))))
        if leftover:
            raise SystemExit('%s 里还剩未渲染占位符：%s' % (name, sorted(leftover)))
    print('七本回读未渲染占位符 = 0')
    return 0


if __name__ == '__main__':
    sys.exit(main())

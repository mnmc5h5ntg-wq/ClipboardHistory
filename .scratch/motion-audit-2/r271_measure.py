#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R271 的测量 + 变异表（BACKLOG 325）：把绝对 ms 地板换成同一次运行内的比值地板。

三件事一次做完，因为**地板必须由这三行读数推**，不许先拍一个数再补证人：
  ① 干净三跑：`add 用时 / 空转基线` 的倍率分布 ⇒ 决定地板的下界（噪声多大）；
  ② 产品刀 M831（把写盘搬回调用线程，needle 从 R51 那张表里读，不手抄）⇒ 决定地板的上界；
  ③ 两界之间留余量取 K，并把 K 写回源码之后**再跑一遍** ①②，确认干净绿 + 刀红。

第一版的 K=25 是被这一把刀当场驳回的（干净倍率 ~1.2、坏法倍率个位数 ⇒ 25 太松，抓不到），
那笔账记在台账里：门槛要量出来，而"量出来"的意思是先让刀试一遍。
"""
import io
import os
import re
import subprocess
import sys

ROOT = '/Users/wangziyi/Codex_Project0'
CLIP = os.path.join(ROOT, 'ClipboardHistory')
R51 = os.path.join(ROOT, '.scratch', 'motion-audit-2', 'mutate_r51_capture_path_blocked.py')
TEST1 = 'CapturePathWriteBudgetTests/testAddingACopyWritesNothingOnTheMainThread'
RATIO = re.compile(r'CAPTURE_PATH_BLOCKED add 用时=([\d.]+)ms 空转基线=([\d.]+)ms 倍率=([\d.]+)')


def load_r51():
    """从 R51 那张表里取 M249 那颗 needle（同一把坏法，两个时代的两把尺）。"""
    src = io.open(R51, encoding='utf-8').read()
    ns = {'os': os, 'sys': sys}
    head = src.split('# (编号, 说明, 文件, 锚点, 替换, 过滤器, 必须出现的失败消息, 预期)')[0]
    exec(compile(head, R51, 'exec'), ns)          # noqa: S101 - 自家表，只取常量
    # 表里的 M249 那一行：取"文件 / 锚点 / 替换"。名字（PERSIST / DISPATCH）从常量段 exec 出来，
    # 替换串是该元组里的第三个字符串字面量（第 1 个是编号、第 2 个是说明）—— 不 exec 整表，
    # 免得把表尾的运行时代码带进来。
    m = re.search(r'\("M249",\s*"([^"]*)",\s*(\w+),\s*(\w+),\s*\n?\s*"((?:[^"\\]|\\.)*)"', src)
    if not m:
        raise SystemExit('R271 NOT_RUN 读不到 M249 那一行')
    return ns[m.group(2)], ns[m.group(3)], m.group(4)      # 文件 / 锚点 / 替换


def run():
    env = dict(os.environ)
    env.pop('SDKROOT', None)
    env['DEVELOPER_DIR'] = '/Applications/Xcode.app/Contents/Developer'
    proc = subprocess.run(['swift', 'test', '--filter', TEST1], cwd=CLIP, env=env,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    text = proc.stdout.decode('utf-8', 'replace')
    got = RATIO.search(text)
    executed = re.findall(r'Executed (\d+) tests?, with (\d+) failures?', text)
    n_ran, n_fail = (executed[-1] if executed else ('0', '0'))
    return (float(got.group(1)), float(got.group(2)), float(got.group(3))) if got else None, int(n_ran), int(n_fail), text


def main():
    ONLY_MUTANT = os.environ.get('R271_ONLY_MUTANT') == '1'
    rd_log = io.open('/tmp/r271_measure.log', encoding='utf-8').read() if ONLY_MUTANT else ''
    target, needle, repl = load_r51()
    rel = os.path.relpath(target, ROOT)
    original = io.open(target, encoding='utf-8').read()
    if original.count(needle) != 1:
        print('R271 NOT_RUN needle 命中 %d 次（要 1）' % original.count(needle), flush=True)
        return 2
    clean = [float(x) for x in re.findall(r"CLEAN \d 用时=[\d.]+ 基线=[\d.]+ 倍率=([\d.]+)", rd_log)] if ONLY_MUTANT else []
    for i in range(0 if ONLY_MUTANT else 3):
        r, ran, fail, _ = run()
        tag = ('用时=%.3f 基线=%.3f 倍率=%.2f' % (r[0], r[1], r[2])) if r else '无读数'
        print('CLEAN ' + str(i + 1) + ' ' + tag + ' 跑=' + str(ran) + ' 失败=' + str(fail), flush=True)
        if r and ran and fail == 0:
            clean.append(r[2])
    if len(clean) < 2 and not ONLY_MUTANT:
        print('R271 NOT_RUN 干净读数不足 ⇒ 地板没有下界证人', flush=True)
        return 2
    try:
        io.open(target, 'w', encoding='utf-8').write(original.replace(needle, repl, 1))
        r, ran, fail, text = run()
    finally:
        io.open(target, 'w', encoding='utf-8').write(original)
        if io.open(target, encoding='utf-8').read() != original:
            print('R271 RESTORE_FAILED ⇒ 立刻停表', flush=True)
            return 2
    msg = re.findall(r"error: -\[[\w.]+ (\w+)\] : XCTAssert\w+ failed: [^\n]{0,200}", text)
    tag = ('用时=%.3f 基线=%.3f 倍率=%.2f' % (r[0], r[1], r[2])) if r else '无读数'
    print('MUTANT ' + tag + ' 跑=' + str(ran) + ' 失败=' + str(fail)
          + (' 红在 ' + msg[0][:60] if msg else ''), flush=True)
    print('R271_MEASURE 干净倍率=' + '/'.join('%.2f' % c for c in clean)
          + ' 坏法倍率=' + ('%.2f' % r[2] if r else '无')
          + ' 坏法是否被抓住=' + ('yes' if (r and fail and r[2] > max(clean)) else 'no'), flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())

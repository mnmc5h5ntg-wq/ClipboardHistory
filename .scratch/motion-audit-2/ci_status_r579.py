#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R579 ⓪：把"两跑到没到数"做成**落盘的摘录**，而不是我在账里写的一句话。

为什么单独一支：账上那一格要写的恰恰是「读不到」这件事，而"读不到"必须由取数动作产生，
不许由我回忆。这一支把 `gh run view --json`（token 通道）、`ci_read.py steps`（失败步骤视图）、
匿名 `curl api.github.com`（监工侧那个 403 的形状）三件事现读，写成 `LABEL :: 值` 的六行，
`ledgers_r579.py` 再逐字抄进七本 —— 取不到就拒绝写账（它自己会 SystemExit）。

用法：python3 .scratch/motion-audit-2/ci_status_r579.py     （写 /tmp/r579/ci_status.txt）
退出码：0=六格都取到；1=某一格取不到（此时**不写文件**，账就不能落）。
"""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = '/tmp/r579/ci_status.txt'
RUNS = {
    'MAIN': ('42012874664', '81297e7', 'R578 主笔'),
    'BUJI': ('42013421642', '685c9e6', 'R578 补记笔'),
}


def run(argv):
    proc = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True, timeout=180)
    return proc.returncode, (proc.stdout + proc.stderr).strip()


def gh_json(run_id):
    code, out = run(['gh', 'run', 'view', run_id, '--json',
                     'status,conclusion,headSha', '--template',
                     '{{.status}}|{{.conclusion}}|{{.headSha}}'])
    if code != 0 or '|' not in out:
        raise SystemExit('gh 取不到 %s：%s' % (run_id, out[:200]))
    status, conclusion, sha = out.split('|', 2)
    return status, conclusion, sha


def steps_of(run_id):
    code, out = run(['python3', 'scripts/ci_read.py', 'steps', run_id])
    if code != 0:
        raise SystemExit('ci_read.py steps 取不到 %s：%s' % (run_id, out[:200]))
    return out


def main():
    fields = []
    for tag, (run_id, sha, title) in RUNS.items():
        status, conclusion, head = gh_json(run_id)
        if head[:7] != sha:
            raise SystemExit('%s 的 sha 对不上：账上 %s，实际 %s ⇒ 拒绝写账' % (run_id, sha, head[:7]))
        if conclusion == '':
            verdict = u'未到数（`status=%s`、`conclusion` 空 ⇒ 通道还没内容，**不是「没有失败步骤」**）' % status
        else:
            verdict = u'到数（`%s / %s`）' % (status, conclusion)
        fields.append((u'STATUS_%s' % tag, u'%s ↔ %s（%s）现读 %s' % (run_id, sha, title, verdict)))
        view = steps_of(run_id)
        reds = [ln.strip() for ln in view.split('\n') if '⇒ failure' in ln]
        if conclusion == '':
            step_lines = [ln for ln in view.split('\n') if 'STEP[' in ln]
            empty = all(ln.strip().endswith('\u21d2') or ln.strip().endswith('\u21d2 ')
                        for ln in step_lines)
            fields.append((u'STEPS_%s' % tag,
                           (u'取到 %d 行步骤名、每步 conclusion 全空 ⇒「取到清单」与「没有失败步骤」是两件事'
                            % len(step_lines))))
            if step_lines and not empty:
                raise SystemExit('%s 的步骤视图里有非空 conclusion 而 run 还说没到数 ⇒ 停手对拍' % run_id)
        else:
            fields.append((u'STEPS_%s' % tag, u'、'.join(reds) if reds else u'无失败步骤'))

    code, api = run(['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}', 'https://api.github.com'])
    fields.append(('API_ANON', u'匿名 `curl https://api.github.com` 现读 HTTP=%s（api=%s；这是未认证限流的形状，不是断网）'
                   % (api.strip(), api.strip())))
    code, auth = run(['gh', 'auth', 'status'])
    if code != 0:
        raise SystemExit('gh 的 token 通道不可用：%s' % auth[:200])
    fields.append(('GH_TOKEN_CHANNEL', u'`gh auth status` 现读通（token 那一条才是本轮读 CI 用的通道）'))

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', encoding='utf-8') as f:
        for label, value in fields:
            f.write('%s :: %s\n' % (label, value))
    for label, value in fields:
        print('%s :: %s' % (label, value))
    print('CI_STATUS 写了 %d 格 → %s' % (len(fields), OUT))
    return 0


if __name__ == '__main__':
    sys.exit(main())

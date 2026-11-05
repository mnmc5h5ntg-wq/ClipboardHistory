# -*- coding: utf-8 -*-
"""R582 的 ⓪ 取数：成对号 + 全部失败步骤 + **runner 那一行 `折叠路径差` 反查三条待验假设**。

四条规矩（都是本轮派单 ①/③ 点名的）：
1. run↔sha **成对**取，sha 对不上 ⇒ SystemExit（只记 run 号，下一轮没法复查）；
2. `conclusion` 空 ⇒ 那一格写**未到数**，并写明「每一步结论也全空」不等于「没有失败步骤」；
   对进行中的作业**不去取日志**（`--log-failed` 打 0 字节 = 通道还没内容，不是内容里没有）；
3. 三条待验假设由 runner 那一行**反查**命中哪条，不由我事前挑；到数而一条都不命中 ⇒ 整格 NOT-RUN；
4. 绿步的正文只在 `--log` 里（R580 ⑨·5 那一课：「在不在失败列表」与「那一步的读数」是两格账）
   ⇒ 所有通道串都从**整跑日志**取；某模式命中 0 次要写成「数出来的没有」，不许写成「没有这回事」。

用法：python3 .scratch/motion-audit-2/ci_status_r582.py
"""
from __future__ import annotations

import io
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = '/tmp/r582/ci_status.txt'

RUNS = {
    'MAIN': ('42053319449', '6aec151', 'R581 主笔：`D12_SHAPE_SCAN` 的第一格 runner 证人'),
    'BUJI': ('42053925581', '07b1e20', 'R581 补记笔：只带台账，不替主笔签'),
}

# R581 补记交给本轮的三条待验假设。⑵ 先试：它要 `差=0`，与 ⑴ 的 `差=1` 互斥，不会两条都命中。
CONTINGENCY = [
    ('⑵', r'折叠路径剥注释=\d+ 折叠路径带注释=\d+ 折叠路径差=0\b',
     u'两台看到的产品树不一样 ⇒ **两台的数都逐字抄**，不许取平均、不许写「本机特例」；'
     u'去查是行尾 / 编码 / `.gitattributes`，还是那一份文件根本没进 checkout'),
    ('⑴', r'折叠路径剥注释=(?P<stripped>\d+) 折叠路径带注释=(?P<raw>\d+) 折叠路径差=1\b',
     u'两机同判 ⇒ `FOLD_PATH_SCAN_COMMENT_FED=1处` 登记为**跨机器已复核**（复核的是「注释存在」这一件事，'
     u'不复核任何产品行为）；runner 那一台的两个观测值由**它自己那一行**给出 ⇒ 可以登记'),
    ('⑶', r'D12_SHAPE_SCAN [^\r\n]*现扫瞎',
     u'注释正在改变 verdict ⇒ 唯一合法处置是**重锚 A 的形状集合**，不许据此改表体或按行快照'),
]


def run(argv, timeout=300):
    proc = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True, timeout=timeout)
    return proc.returncode, (proc.stdout + proc.stderr).strip()


def gh_view(run_id):
    code, out = run(['gh', 'run', 'view', run_id, '--json', 'status,conclusion,headSha',
                     '--template', '{{.status}}|{{.conclusion}}|{{.headSha}}'])
    if code != 0 or '|' not in out:
        raise SystemExit('gh 取不到 %s：%s' % (run_id, out[:200]))
    status, concl, sha = out.split('|', 2)
    return status, concl, sha


def steps_view(run_id):
    code, out = run(['python3', 'scripts/ci_read.py', 'steps', run_id])
    if code != 0:
        raise SystemExit('ci_read.py steps 取不到 %s：%s' % (run_id, out[:200]))
    return out


def full_log(run_id):
    """整跑日志（绿步的正文只在这里）。取不到就 SystemExit —— 那一格只能判未读。"""
    path = '/tmp/r582/fulllog_%s.txt' % run_id
    os.makedirs('/tmp/r582', exist_ok=True)
    if os.path.exists(path) and os.path.getsize(path) > 1000:
        return path
    with io.open(path, 'w', encoding='utf-8', errors='replace') as handle:
        proc = subprocess.run(['gh', 'run', 'view', run_id, '--log'],
                              cwd=ROOT, stdout=handle, stderr=subprocess.DEVNULL, timeout=1500)
    if proc.returncode != 0 or os.path.getsize(path) < 1000:
        raise SystemExit('%s 的整跑日志取不到 ⇒ 那一格只能判未读，不许写「没有」' % run_id)
    return path


def one(pattern, path, label, allow_absent=None):
    text = io.open(path, encoding='utf-8', errors='replace').read()
    found = re.findall(pattern, text)
    if not found:
        if allow_absent is not None:
            return allow_absent % (pattern,)
        raise SystemExit('%s 没在 %s 里命中（模式 %s）⇒ 拒绝写账' % (label, path, pattern))
    last = found[-1]
    return (last.strip() if isinstance(last, str) else ' '.join(x for x in last if x).strip())


def main():
    fields = []
    logs = {}
    for tag, (run_id, sha, title) in RUNS.items():
        status, concl, head = gh_view(run_id)
        if head[:7] != sha:
            raise SystemExit('%s 的 sha 对不上：账上 %s，实际 %s ⇒ 拒绝写账' % (run_id, sha, head[:7]))
        if concl == '':
            fields.append(('STATUS_%s' % tag,
                           u'%s ↔ %s（%s）现读 **未到数**（`status=%s`、`conclusion` 空 ⇒ 通道还没内容；'
                           u'同一时刻每一步的 conclusion 也全空 —— 那**不是**「没有失败步骤」）'
                           % (run_id, sha, title, status)))
            fields.append(('STEPS_%s' % tag,
                           u'不取（那一跑还没数。`steps` 视图对进行中的作业不给 success 建行，'
                           u'读它等于读「没红」——R557 那一课）'))
            fields.append(('NAMES_%s' % tag,
                           u'不取（未到数 ⇒ 「这一跑没有新名字」与「这一跑有 N 朵」两句都没读到位）'))
            continue
        fields.append(('STATUS_%s' % tag, u'%s ↔ %s（%s）现读 到数（`%s / %s`）'
                                       % (run_id, sha, title, status, concl)))
        view = steps_view(run_id)
        reds = [ln.strip() for ln in view.split('\n') if u'⇒ failure' in ln]
        fields.append(('STEPS_%s' % tag, u'、'.join(reds) if reds else u'无失败步骤'))
        logs[tag] = full_log(run_id)
        names = sorted(set(re.findall(r"Test Case '-\[[A-Za-z.]+ ([A-Za-z0-9_]+)\]' failed",
                                      io.open(logs[tag], encoding='utf-8', errors='replace').read())))
        if not names:
            raise SystemExit('%s 里读不到任何失败用例名 ⇒ 「没有新名字」这句不能凭这句话写' % run_id)
        fields.append(('NAMES_%s' % tag, u' '.join(names)))

    if 'MAIN' not in logs:
        raise SystemExit('⓪ 主笔那一跑到数才有本轮的读数；现在两条都没数 ⇒ 这一支不出格（先别写账）')

    # —— 三条待验假设：只看主笔那一跑（补记笔不替主笔签）。
    shape_main = one(r'D12_SHAPE_SCAN [^\r\n]*', logs['MAIN'], 'runner 上的两档读数')
    shape_buji = one(r'D12_SHAPE_SCAN [^\r\n]*', logs.get('BUJI', logs['MAIN']),
                     '补记笔那一跑的两档读数') if 'BUJI' in logs else u'未到数'
    fields.append(('SHAPE_SCAN_MAIN', shape_main))
    fields.append(('SHAPE_SCAN_BUJI', shape_buji))
    if 'BUJI' in logs and shape_main != shape_buji:
        raise SystemExit('同一棵产品树在**同一台 runner 的两跑**里给出两个值 ⇒ 停手对拍：\n%s\n%s'
                         % (shape_main, shape_buji))
    hit_key = hit_action = None
    groups = {}
    for key, pattern, action in CONTINGENCY:
        m = re.search(pattern, shape_main)
        if m:
            hit_key, hit_action, groups = key, action, m.groupdict()
            break
    if hit_key:
        fields.append(('CONTINGENCY_HIT',
                       u'runner 那一行逐字 `%s` ⇒ 命中预案 **%s**：%s（抽到的字段=%s）'
                       % (shape_main, hit_key, hit_action, groups)))
        fields.append(('CONTINGENCY_MISSED',
                       u'另外两条逐条试完都未命中：'
                       + u'；'.join(u'预案%s 未命中' % k for k, _p, _a in CONTINGENCY if k != hit_key)
                       + u'。⚠「这一跑没命中」不许被读成「永远不会命中」'))
    else:
        fields.append(('CONTINGENCY_HIT',
                       u'runner 那一行读到了（`%s`）但三条假设一条都不命中 ⇒ 整格 **NOT-RUN**、'
                       u'一条都不选，先把这个新形状写进 R583 的 ⓪' % shape_main))
        fields.append(('CONTINGENCY_MISSED', u'三条逐条试完：⑵ 差=0 ⑴ 差=1 ⑶ 判法不同 —— 都不符'))

    # —— 登记格：本轮才写的代码，在这一跑上**必须**是"数出来的没有"。
    fields.append(('REGISTRY_RUNNER',
                   u'`D12_SHAPE_SCAN_REGISTRY` 在 `42053319449` 上%s ⇒ 登记代码是本轮（R582）才写的，'
                   u'**修尺那一笔的跑签不了自己**（R555/R565 那一族）：这一格的第一证人是含 R582 那一笔的跑，'
                   u'届时那一行应当读 `机器=github-runner 登记=1_2 判=一致`；'
                   u'而 runner 那一台的两个观测值由它**自己那一行**给出（`剥注释=%s 带注释=%s`）⇒ 本轮据此登记，'
                   u'本机没替它填任何数'
                   % (one(r'D12_SHAPE_SCAN_REGISTRY [^\r\n]*', logs['MAIN'], '登记格',
                          allow_absent=u'现读命中 0 次（模式 `%s`）⇒ 具名缺失=预期，不是「没有这回事」'),
                      *re.search(r'折叠路径剥注释=(\d+) 折叠路径带注释=(\d+)', shape_main).groups())))

    for tag in ('MAIN', 'BUJI'):
        if tag not in logs:
            fields.append(('MATERIAL_%s' % tag, u'未到数 ⇒ 不取'))
            continue
        fields.append(('MATERIAL_%s' % tag,
                       one(r'REALSCREEN_MATERIAL_NOT_RUN=env-off[^\r\n]{0,140}', logs[tag],
                           '材质那臂在 runner 上的状态')))
    for tag in ('MAIN', 'BUJI'):
        src = logs.get(tag)
        if not src:
            fields.append(('PROBE18_%s' % tag, u'未到数 ⇒ 不取'))
            continue
        fields.append(('PROBE18_%s' % tag,
                       one(r'PROBE_COVERAGE_SUMMARY [^\r\n]*', src, 'STEP[18] 的正文（整跑日志）')))
    fields.append(('GATE_MAIN', one(r'CAPTURE_GATE_CASES [^\r\n]*', logs['MAIN'], '捕获门')))
    fields.append(('MOTION_MAIN', one(r'MOTION_FLOOR_SUITE_RED=[0-9]+', logs['MAIN'], '动效门计数')))
    fields.append(('MOTION_FACTS', one(r'MOTION_FLOOR_FACTS [^\r\n]*', logs['MAIN'],
                                       '动效地板那一步的 executed=')))
    fields.append(('D12_MAP_RUNNER', one(r'D12_CHANNEL_MAP_SUMMARY [^\r\n]*', logs['MAIN'],
                                         '映射表四个数在 runner 上')))
    fields.append(('GATE_RUNNER', one(r'D12_LIVE_GATE A按名字文件数=\d+ B按形状文件数=\d+ 判=\S+',
                                      logs['MAIN'], 'runner 上活门那一格')))
    fields.append(('PROBE_RUNNER', one(r'D12_LIVE_GATE_PROBE [^\r\n]*', logs['MAIN'],
                                       '注入正对照在 runner 上的读数')))

    code, api = run(['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}', 'https://api.github.com'])
    fields.append(('API_ANON', u'匿名 `curl https://api.github.com` 现读 HTTP=%s（未认证限流的形状，不是断网；'
                   u'也**不证**可推或不推）' % api.strip()))
    code, gh_host = run(['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}', 'https://github.com'])
    fields.append(('GITHUB_ANON', u'`curl https://github.com` 现读 HTTP=%s' % gh_host.strip()))
    code, auth = run(['gh', 'auth', 'status'])
    if code != 0:
        raise SystemExit('gh 的 token 通道不可用：%s' % auth[:200])
    fields.append(('GH_TOKEN_CHANNEL', u'`gh auth status` 现读通（token 那一条才是本轮读 CI 用的通道）'))
    code, ls = run(['git', 'ls-remote', 'origin', 'HEAD'])
    if code == 0 and ls.strip():
        fields.append(('PUSH_CHANNEL', u'`PUSH_TRANSPORT=ssh-ok` —— 现读 `git ls-remote origin HEAD` 通（远端 HEAD='
                       + ls.split()[0][:9] + u'）；这一格本轮**现读**（监工侧昨日见过三次读数不一致的间歇），'
                       u'没改 remote url、没动 `~/.ssh`、没换 DNS'))
    else:
        fields.append(('PUSH_CHANNEL', u'`PUSH_BLOCKED=` 待具名 —— 现读 `git ls-remote origin HEAD` 退出码 %d，'
                       u'正文首行 `%s`（间歇未定论，成因归用户；只重试有界次数）'
                       % (code, (ls.strip().splitlines() or [u'空'])[0][:60])))

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with io.open(OUT, 'w', encoding='utf-8') as handle:
        for label, value in fields:
            handle.write('%s :: %s\n' % (label, value))
    for label, value in fields:
        print('%s :: %s' % (label, value))
    print('CI_STATUS 写了 %d 格 → %s' % (len(fields), OUT))
    return 0


if __name__ == '__main__':
    sys.exit(main())

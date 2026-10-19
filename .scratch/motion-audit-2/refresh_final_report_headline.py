# -*- coding: utf-8 -*-
"""刷新 `AGENT_FINAL_REPORT.md` 的三格活数（标题轮次 / §1 阶段二轮数 / §1 的 U 区间）。

R223 起这是**每轮收尾的最后一步**（排在轮次台账之后）—— R222 我把报告刷新排在台账之前，
结果台账一写、报告就又落后两轮，`test_final_report_headline` 立刻红：
那条守卫没错，错的是顺序（见 AGENT_STATE 的 ⓪b 与 BACKLOG 248 追记）。

与 R222 那版生成器的区别：**幂等**。锚点匹配的是"数字的形状"而不是"上一版的具体数字"，
所以同一份脚本可以每轮跑第二次而不报"锚点找不到"。写完后自己调守卫的 `headline_problems` 复核。
"""
import io, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REPORT = os.path.join(ROOT, 'AGENT_FINAL_REPORT.md')


def die(why):
    print('REFRESH_HEADLINE refused: ' + why)
    sys.exit(1)


def sh(cmd):
    proc = subprocess.run(cmd, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                          env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1'))
    return proc.returncode, proc.stdout.decode('utf-8', 'replace')


code, curve = sh(['python3', os.path.join(ROOT, '.scratch/motion-audit-2/curve_from_ledger.py')])
if code != 0:
    die('曲线工具退出 %d' % code)
m = re.search(r'PHASE2 CURVE:\s*([\d ·]+)', curve)
if not m:
    die('读不到 PHASE2 CURVE 行')
phase2_n = len(re.findall(r'\d+', m.group(1)))

it = io.open(os.path.join(ROOT, 'AGENT_VISUAL_ITERATION.md'), encoding='utf-8').read()
last_round = max(int(x) for x in re.findall(r'^## Round (\d+) · ', it, re.M))
ui = io.open(os.path.join(ROOT, 'AGENT_UI_AUDIT.md'), encoding='utf-8').read()
u_ids = [int(x) for x in re.findall(r'^- \*\*U-(\d+)：', ui, re.M)]
u_max, u_rows = max(u_ids), len(u_ids)

text = io.open(REPORT, encoding='utf-8').read()
subs = [
    (r'(R9–R)(\d+)(，)(\d+)( 轮自评）)',
     lambda mm: mm.group(1) + str(last_round) + mm.group(3) + str(phase2_n) + mm.group(5)),
    (r'(\| 阶段二 \*\*)(\d+)( 轮\*\*审计（R9–R)(\d+)(；以 `curve_from_ledger\.py` 的 `PHASE2 n=)(\d+)',
     lambda mm: mm.group(1) + str(phase2_n) + mm.group(3) + str(last_round) + mm.group(5) + str(phase2_n)),
    (r'(U-31 … U-)(\d+)(（)(\d+)( 条定义行)',
     lambda mm: mm.group(1) + str(u_max) + mm.group(3) + str(u_rows) + mm.group(5)),
]
done = []
for pat, fn in subs:
    new, n = re.subn(pat, fn, text, count=1, flags=re.M)
    if n != 1:
        die('锚点没命中（要 1，实得 %d）：%s' % (n, pat[:60]))
    text = new
    done.append(pat[:28])

io.open(REPORT, 'w', encoding='utf-8').write(text)

sys.path.insert(0, os.path.join(ROOT, 'scripts', 'tests'))
import test_final_report_headline as guard   # noqa: E402  同一把尺复核（R68 的规矩）
problems = guard.headline_problems(io.open(REPORT, encoding='utf-8').read(), guard.live_counts())
if problems:
    die('写完仍与活账不一致：' + str(problems))
print('REFRESH_HEADLINE ok：R%d / PHASE2 n=%d / U-%d（%d 条）；守卫复核 0 问题'
      % (last_round, phase2_n, u_max, u_rows))

# -*- coding: utf-8 -*-
"""把 U-2444 那一格与各处提及写进 ledgers_r565.py（R565 内部工具，跑完即可删）。"""
import io

p = '.scratch/motion-audit-2/ledgers_r565.py'
s = io.open(p, encoding='utf-8').read()

entry = (
    u"- **U-2444：R564 那把守卫把 runner 的两跑打死了 —— 根因是写死的机器根，本轮修掉并补一支守卫。**"
    u" ⓪ 现读 `41552571306↔4cfcfc6` 与 `41552998637↔8eecbc7` 都是"
    u" **STEP[9] `Release script tests` failure、STEP[10]-[14] skipped、STEP[15]-[19] success**"
    u"（逐步读 `gh run view --json jobs` 的 `steps[].conclusion`，不是从「不在失败名单」推的）。"
    u"CI 日志正文（`/tmp/r565-ci-8eecbc7.log` 第 8451-8470 行）：`test_current_batch_is_consistent` ⇒"
    u" `AssertionError: 1 != 0 : commit 轮次身份守卫红：` 后面跟的是脚本**自己的 traceback** ——"
    u" `commit_round_identity.py` 把自己的仓库根写成一台机器的绝对路径，runner 上那个目录不存在 ⇒"
    u" `subprocess.run(cwd=ROOT)` 抛异常 ⇒ 退出码 1。⇒ **分批 push 不是原因，我自己写死的根才是**；"
    u"代价是两跑的 **STEP[11] 帧基线名册门整段没跑**，而 `SKIP_ROSTER` 也没有行"
    u"（634 的形状：内层红 ⇒ 这一格没有可对账的对象，**既不能记绿也不能记红**）。"
    u"修法：根由 `__file__` 推出来。另补一支守卫 `MachineRootHygieneTests`（三条腿：真扫 `scripts/**/*.py` 的根常量、"
    u"正对照必须点名、负对照不许咬 `__file__` 派生写法与测试里的合成路径靶与注释里的历史引用）——"
    u" 原有那支只盯 `/tmp/shots_rNN`，看不见「根常量」这一族（BACKLOG 334 那一格的老毛病换了个载体又犯）。"
    u"刀 **M1468 CAUGHT**（把根改回写死 ⇒ 真扫那一格点名文件与行号）、"
    u"**M1469 CAUGHT**（让扫描器「看见但不报」⇒ 正对照那一格红：`1 != 0 扫描器抓不到写死的仓库根 ⇒ 这把尺是空的`），"
    u"两把 RESTORE_CLEAN=yes。刀落过程中两次自伤：① 第一版刀脚本把裸字符串插进模板 ⇒"
    u" `OLD = ROOT = os.path…` 成了链式赋值 ⇒ `needle 命中 0`；② M1469 第一版只替换了 alternation 里一段、"
    u"`ROOT` 还在 ⇒ 判据 PASSED（那根本不叫变异）。"
    u"**「登记前先跑一遍看 needle 命中 1」这条规矩本轮第三次救场。**\n"
)
assert s.count(u'@@NEWENTRY@@') == 1, 'placeholder'
s = s.replace(u'@@NEWENTRY@@', entry, 1)

pairs = [
    (u"刀两把登记（M1466 退回 tertiary、M1467 再弱一档改 quaternary，全 CAUGHT），一把试落即撤",
     u"刀两把登记（M1466 退回 tertiary、M1467 再弱一档改 quaternary，全 CAUGHT），一把试完就撤"),
    (u"判据卷 %(CAPTURE)s；帧 %(FRAMES)s；全量 %(FULL)s；build 0 告警；电池 %(BATTERY)s；4.5 墨地板",
     u"**另落一格真 bug**：R564 那把 commit 守卫把自己的仓库根写成机器绝对路径 ⇒ runner 上 STEP[9] 抛异常、"
     u"STEP[10]-[14]（含帧基线名册门）整段 skipped，两跑信号全被带走；本轮改成由 `__file__` 推出，"
     u"并补一支 `MachineRootHygieneTests`（三条腿齐全）+ 刀 M1468/M1469 全 CAUGHT。"
     u"判据卷 %(CAPTURE)s；帧 %(FRAMES)s；全量 %(FULL)s；build 0 告警；电池 %(BATTERY)s；4.5 墨地板"),
    (u"刀 M1466/M1467 CAUGHT；**M1468 试落即撤（空刀不占号）**",
     u"刀 M1466/M1467/M1468/M1469 全 CAUGHT；另有一把**试完就撤的空刀**（从未登记、不占号）："
     u"字芯改成全部偏差像素 ⇒ 6.01/9.16 仍过地板 ⇒ 判据 PASSED"),
]
for old, new in pairs:
    if s.count(old) >= 1:
        s = s.replace(old, new, 1)
        print('OK  ', old[:36])
    else:
        print('MISS', old[:36])

d7 = (u"⑦ **脚本自己的根不许写死，而且这条要有守卫。** R564 的 `commit_round_identity.py` 把 ROOT 写成机器绝对路径 ⇒"
      u" runner 上 STEP[9] 抛异常、STEP[10]-[14]（含帧基线名册门）整段 skipped，两跑的 CI 信号全丢。"
      u"这不是新病（BACKLOG 334 那一族），但原有那支路径卫生守卫只盯 `/tmp/shots_rNN`，看不见「根常量」这一族 ⇒"
      u" 本轮补 `MachineRootHygieneTests`（三条腿）。更狠的一条规矩：**任何依赖环境路径的判据，"
      u"落之前先在 runner 的目录结构下想一遍它会不会抛异常** —— 抛异常与判红在报表上长得一样（都是退出码非零），"
      u"但修法相反。\n")
old6 = u"⑥ **边界**：本轮产品 1 文件"
assert s.count(old6) == 1
s = s.replace(old6, d7 + old6, 1)
print('OK   D-565 第⑦条')

io.open(p, 'w', encoding='utf-8').write(s)
print('WRITTEN')

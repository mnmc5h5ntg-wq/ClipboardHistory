#!/usr/bin/env bash
# R292 的收尾链：等四件套 → 跑台账生成器 → 按它的现读行分两笔提交 → 推送。
# 为什么把提交接在生成器后面而不是手工做：commit 正文里那些数必须由**这一笔**的读数生成
# （D-236），手工抄就是给下一轮留化石。生成器不绿 ⇒ 整条链不提交。
set -uo pipefail
cd /Users/wangziyi/Codex_Project0 || exit 2
export DEVELOPER_DIR=/Applications/Xcode.app/Contents/Developer
export PYTHONDONTWRITEBYTECODE=1 PYTHONUTF8=1

LOG=/tmp/r292_ship.log
: > "$LOG"

# ① 等四件套的结论行（最多再等 15 分钟）
for _ in $(seq 1 90); do
  grep -qa 'ROUND_VERIFY' /tmp/r292_verify_run1.log && break
  sleep 10
done
RV=$(grep -a '^ROUND_VERIFY ' /tmp/r292_verify_run1.log | tail -1)
if [ -z "$RV" ]; then echo "SHIP_REFUSED 四件套没有结论行" | tee -a "$LOG"; exit 2; fi
echo "$RV" >> "$LOG"
# 全量卷的红不在这里判：判据只留一处（生成器里那段"只准 304 那一族按用例名配对"的闸）。
# 两处各判一次就会互相掩盖（R83/R100 那一族），所以这里只确认结论行在不在。
case "$RV" in *ROUND_VERIFY*) ;; *) echo "SHIP_REFUSED 没有 ROUND_VERIFY 结论行" | tee -a "$LOG"; exit 2;; esac

# ② 台账生成器（它自己会再跑判据、两批刀、预检、电池两次）
python3 .scratch/motion-audit-2/ledgers_r292.py >> "$LOG" 2>&1
G_RC=$?
if [ "$G_RC" -ne 0 ]; then echo "SHIP_REFUSED 生成器退出码 $G_RC" | tee -a "$LOG"; exit 2; fi
OK=$(grep -a '^LEDGERS_R292 OK' "$LOG" | tail -1)
if [ -z "$OK" ]; then echo "SHIP_REFUSED 生成器没打结论行" | tee -a "$LOG"; exit 2; fi
echo "$OK" >> "$LOG"

# ③ 代码半：判据与尺、两张变异表、预检名册、闸门改名 + 新守卫
git add ClipboardHistory/Tests/ClipboardHistoryAppTests/UICaptureHarness.swift \
        .scratch/motion-audit-2/mutate_r290.py \
        .scratch/motion-audit-2/mutate_r292.py \
        .scratch/motion-audit-2/mutate_needle_precheck.py \
        scripts/tests/test_skip_roster.py
git commit -q -F - <<MSG
R292 代码半（第 291 轮 / Round 289）：墨簇尺的合并阈值从像素换成随密度换算的点，判据自带 @1x 替身臂 —— 上一轮那朵 runner 红由解释升成本机复现（D-272/D-273）

现读：$OK
四件套：$RV

1) columnClusters 原来把列缝阈值写成 mergeGapPx: Int = 12，而注释里那句 6pt 是在本机 @2x 量的。账上早就有读数写着 runner 的截图是 位图=720x540 scale=1.0、本机 2x ⇒ 1x 下 12px 就是 12pt，比行首三列之间 10pt 的缝还宽，相邻两列必然并成一簇：testMultiFileRowSeparatorsStartAtTheTextAxis 在 runner 上连着三跑红（39630283526 / 39630405703 / 39725115544，同为 STEP[15] 与 STEP[17]，红话「行带里只数到 2 个墨簇」），而本机全绿。改成 mergeGapPt × density，密度由被量对象自己给（pixelsWide / 逻辑宽）。
2) 判据里加一条 @1x 替身臂：downsampleNearest 把自家 2x 帧按最近邻抽成 1x（不重新渲染 ⇒ 内容同源、只有密度变），两臂必须给同一个点空间答案；新读数 LEFT_AXIS_R292_1X。臂的身份自己也要有牙：abs(density1x - 1) ≤ 0.01 这条断言判的是「这一臂是不是真在 1x 上量」，不是被判断的簇数（D-271 的规矩用在臂上）。
3) mutate_r292.py 三把刀各钉一条轴：M855 单位轴（阈值退回固定 12px ⇒ 在本机 1x 臂上量到与 runner 同一个数：2 簇，区间 [36.0..40.0, 55.0..175.0]）、M856 臂身份轴（倍率写死成 1 ⇒ 红「这一臂根本没在 @1x 上量」）、M857 臂对象轴（y 带不按倍率换算 ⇒ 红「数到 0 簇」）。
4) 自曝并修好：本轮改签名把上一轮的 M847 针弄腐烂了（预检 bad=1，旧针 mergeGapPx: Int = 12 命中 0 次）⇒ 按新形状重钉并整张 R290 表重跑，M845/M846/M847 全 CAUGHT。缺席文本也顺手补了现场（密度与每簇点区间），M847 的红话里现在能直接看到 [36.0..175.5]。
5) 顺着 R291 那格假话（「电池 skipped 5 vs 4」，实为生成器用未锚定的 skipped=(\d+) 命中了闸门自己打的读数行）在源头消歧：SKIP_ROSTER 那行改名 内层skip汇总=，并加静态守卫 TestReadingKeyHygiene（按 ast 读 print 的字面量，不许再出现 skipped= 这个键；配已知答案的正对照）。ci_capture_gate.py 那处同名键是 CI 契约行，改名要连着 workflow 与它的断言测试一起动 ⇒ 留在 341 里当未做完的半截。
MSG

# ④ 账半
git add AGENT_UI_AUDIT.md AGENT_VISUAL_ITERATION.md AGENT_DECISIONS.md AGENT_BACKLOG.md \
        CHANGELOG.md AGENT_STATE.md AGENT_FINAL_REPORT.md .scratch/motion-audit-2/ledgers_r292.py
git commit -q -F - <<MSG
R292 账半（第 291 轮 / Round 289）：五本台账 + STATE 轮换 + FINAL_REPORT headline + 就地更正 R291 那四格假话 —— 数字全由 ledgers_r292.py 现读：$OK；四件套 $RV；U-953…U-958／D-272／D-273；340 本机半结案（第三跑 39725115544 同红 ⇒ 这朵红是确定性的，不是负载敏感那一族）、286 追记第四种坏法（本轮改签名弄腐烂上一轮的针）、341 改判（成因是我读错行，不是电池翻脸）并按节边界把 R291 的电池格改成 skipped=4，段外一处未动、替换处数由断言钉住；产品 0 文件 ⇒ 帧基线与 sources 格不动；七维合计 93/105、曲线派生 89 ⇒ 本轮不算达标，R293 回动效（305 的台阶地板与亮档可辨性）。
MSG

git push -q origin main && echo "SHIP_DONE" | tee -a "$LOG"
git log --oneline -2 | cat
git status -sb | head -2

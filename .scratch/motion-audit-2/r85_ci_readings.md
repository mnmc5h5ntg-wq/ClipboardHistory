# R85 读 R84 的 CI（run 38798408040，commit 325e71d，20:00:09→20:12:49，job build-and-test = success）

## 常驻循环那一族（三遍 runner 读数并排）
| run | 画法 | 产品 coverage | 等节拍证人 coverage | 处置 |
|---|---|---|---|---|
| R82 38781113064 | 每根条各扫各的 | 0.000（0/21 对，峰值 0.000） | 0.284 | .notRunEnvironment（点名 loop-clock-not-sustainable-at-product-rate） |
| R83 38786182395 | 每根条各扫各的 | 0.050（1/22 对，峰值 0.015） | 0.837 | .productRed（红着说产品没在跑） |
| R84 38798408040 | **整组一条带** | **0.522（2/24 对，峰值 0.020，采样≈112ms）判定=一直在动** | 0.594（4/28 对，峰值 0.024） | **.ok（判绿，两卷都过地板）** |

原文（Motion filmstrip (report-only) 那一步）：
motion suite exit: 0  executed: 54  胶片: 14  MOTION_SUMMARY notice-banner=2 notice-banner-dismiss=3 detail-kind-change=3 empty-state=3  MOTION_RESOLVE_SUMMARY judged=4/4 no
MOTION_SHIMMER 扫 帧数=24 变化帧对=2 峰值=0.020 采样≈112ms coverage=0.522(地板 0.50) 记录时长=2474ms 判定=一直在动
MOTION_SHIMMER 停 变化帧对=0 峰值=0.000 coverage=0.000
MOTION_SHIMMER_WITNESS 等节拍证人(30Hz 抬升 0.12，与产品同数字) 帧对=28 在变=4 峰值=0.024 coverage=0.594 判定=一直在动
MOTION_SHIMMER_WITNESS 粗节拍证人(20Hz 抬升 0.45，只签字'看得见这种画法') 帧对=33 在变=23 峰值=0.045 coverage=0.972 判定=一直在动
MOTION_SHIMMER_STRIP 前 24 帧排成条带（六列）⇒ 眼睛判的是『亮带一路扫过去』，这把尺判的是 coverage，两者不许互相替
MOTION_SHIMMER_FILM 帧=24 时刻=24 配对=是 卷长=2474ms（探针声明 2500ms） ｜ 结论尺报的记录时长=2474ms —— 后者在峰值 0 时**必然**是 0，所
MOTION_SHIMMER_BAND_CONTROL 整组一条带那卷判定=整组一条带 每根条各扫那卷判定=每根条各扫各的 （两份都是 8 灰阶抬升的亮斑，只有中�
MOTION_SHIMMER_BAND 帧=24 比例=1pt≈1.00px 可用帧=11 丢掉=13 同帧绝对中心最大散布=1.0pt（地板：≤6.0 判一条带、≥40.0 判各扫各的） 归一�
MOTION_SHIMMER_BAND_SAMPLE 可用帧首=[34.0, 33.0, 34.0] 末=[142.0, 142.0, 142.0]
MOTION_SHIMMER_BAND_WITNESS 粗节拍那颗(抬 0.45、同一种画法、同一把尺) 可用帧=7 绝对散布=1.0pt 行程=136.0pt 判定=整组一条带 理由=每一帧三
MOTION_RESOLVE_SUMMARY judged=4/4 not-run=-

## 闸门那一步
MOTION_FLOOR_FACTS judged=4/4 executed=54 not-run=- summary=detail-kind-change=3 empty-state=3 notice-banner=2 notice-banner-dismiss=3 红的用例=- 汇总行报红=0
MOTION_FLOOR_SUITE_CLEAN=0 这一卷没有红用例（汇总行也没说有）
MOTION_FLOOR_OK=4/4 全部臂都在登记之内
MOTION_FLOOR_REDS=0

## 仍然没跑的那一步（BACKLOG 92 的形状）
ui suite exit: 137  executed: 0  skipped: ?  已下结论的用例: 0

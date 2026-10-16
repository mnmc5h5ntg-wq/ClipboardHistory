# R98 开场读到的上一次 CI（R97 的推送）

- run **38891183309**（`5ccd662`，"Round 97: the card ruler had been reading a 1pt divider…"）：
  `status=completed conclusion=success`，`build-and-test` 一格 `conclusion=success`。
  这是本轮开场读的那一次 —— 台账里"CI 绿"只允许指这一条。
- 读法：`gh run list --limit 6` 看到它还在 `in_progress`（11:02 触发，本轮 11:09 开场），
  于是先做别的，11:19 再 `gh run view 38891183309 --json status,conclusion` 拿到终态。
  **没有**把"还在跑"写成"绿"，也没有把它写成"红"。
- 本轮要为它记的一件事：R97 在 runner 上绿的那四条判据里，
  `testSettingsCardVerticalRhythmIsOneNumber` 对 `settings-privacy-excluded` 的读数
  在 R98 被证明量的不是交付那一页（种子没被 `render` 应用）。
  runner 上这一族本来就整块画不出来（BACKLOG 43 ⇒ `CARD_RHYTHM_NOT_RUN`），
  所以那条 CI 绿**没有**替这个缺陷作证，也没有错过它 —— 它只在能画出来的机器上才是红的材料。

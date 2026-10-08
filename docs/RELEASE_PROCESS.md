# 时间剪史发布流程

本文记录本地准备 Release 的推荐流程。脚本只生成本地发布材料，不会自动提交、打 tag、推送或上传 GitHub Release。

## 1. 预演

```bash
python3 scripts/prepare_release.py 1.3.0 --dry-run
```

预演会展示将要执行的步骤，不写文件、不构建。

## 2. 准备发布包

```bash
python3 scripts/prepare_release.py 1.3.0
```

默认流程会执行：

- 运行 Swift 单元测试。
- 运行发布脚本测试。
- 写入 `Makefile` 中的 `VERSION`。
- 通过 `make dmg` 构建 App 和 DMG。
- 校验 App 内 `Info.plist` 的版本号。
- 复制 DMG 到 `releases/`。
- 生成 `.sha256` 校验文件。
- 生成 `docs/RELEASE_NOTES_v版本号.md`。
- 更新 `CHANGELOG.md`。
- 如果 `releases/` 中已有同名 DMG，先移入 `releases/archive/`。

## 3. 常用选项

```bash
python3 scripts/prepare_release.py 1.3.0 --skip-build
```

跳过构建，使用项目根目录已经存在的 DMG。只适合本地调试发布脚本。

```bash
python3 scripts/prepare_release.py 1.3.0 --skip-tests
```

跳过自动测试。只适合已经在同一代码状态下刚跑过测试的情况。

```bash
python3 scripts/prepare_release.py 1.3.0 --force
```

允许覆盖已有发布说明草稿。

## 4. 发布前人工检查

- 打开 DMG，确认图标、应用和 `Applications` 入口显示正常。
- 将 App 拖入 `/Applications` 后启动一次。
- 检查文本、图片、文件、视频复制和预览。
- 检查收藏、菜单栏快速复制、快捷键、开机启动设置。
- 检查 `releases/时间剪史_v版本号.dmg.sha256` 是否能和 DMG 匹配。
- 若 Launchpad 显示旧图标，先删除旧版 App，再等待系统刷新或重启 Dock。

## 5. 内部测试排查

当前本地测试包使用 ad-hoc 签名，未经过 Apple Developer ID 公证。普通用户安装说明只引导使用 Control-点击打开或系统设置允许打开，不提供绕过 Gatekeeper 的终端命令。

如果只是在开发者自己的机器上排查本地构建产物的隔离属性，可以临时使用：

```bash
xattr -cr /Applications/时间剪史.app
```

这条命令不应写入面向普通用户的 README、Release 正文或 DMG 安装说明。

## 5. 提交、打 tag、发布

脚本只到"生成本地材料"为止，后面这几步要手动做（本版实测过的命令）：

```bash
git add CHANGELOG.md Makefile docs/RELEASE_NOTES_v<版本>.md "releases/<App>_v<版本>.dmg.sha256"
git commit -m "Prepare v<版本> release"
git tag v<版本>                       # 与 v1.3 一致：轻量 tag 打在发布准备提交上
git push origin main && git push origin v<版本>
gh release create v<版本> <两个附件> --title "时间剪史 v<版本>" --notes-file docs/RELEASE_NOTES_v<版本>.md
```

两条必须知道的坑（都是 v1.4.6 发布当天踩到的）：

- **附件名不要用中文**。GitHub 会把非 ASCII 前缀吞掉：`时间剪史_v1.4.6.dmg` 上传后变成 `_v1.4.6.dmg`，
  而 `.sha256` 里写的还是原名 ⇒ 用户下载两个附件后 `shasum -c` 直接失败。
  发布资产统一用 ASCII 名（`ClipboardHistory_v<版本>.dmg`），仓库内 `releases/` 下的中文名文件不受影响。
  上传时可用 `gh release upload <tag> <文件> --clobber`，改名后要 `gh release delete-asset` 清掉旧的。
- **发布说明由脚本生成的是占位草稿**（"待补充…""构建 App：待确认。"），
  模板自己也写了要在发布前替换。发布前必须把 `docs/RELEASE_NOTES_v<版本>.md` 和
  `CHANGELOG.md` 里那一节的占位内容换成真实改动，否则会把"待补充"发出去。

发布后自检（本版实际跑过）：

```bash
gh release list -L 3                                   # 确认 Latest 已切到新版本
gh release download v<版本> -R <owner>/<repo> -D /tmp/x # 非 git 目录里必须带 -R
cd /tmp/x && shasum -a 256 -c ClipboardHistory_v<版本>.dmg.sha256   # 必须 OK
```

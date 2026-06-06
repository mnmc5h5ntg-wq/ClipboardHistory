# 仓库整理报告

更新时间：2026-06-07

## 整理目标

本次整理只调整仓库结构，不修改应用功能、不修改 UI、不改变构建逻辑。

## 删除内容

本次未删除任何已跟踪源码或文档内容。

已确认以下构建/发布产物不应进入 Git 跟踪：

- `.app` 应用包
- `.dmg` 安装镜像
- `.build/` SwiftPM 构建目录
- `.swiftpm/` SwiftPM 本地状态目录
- `history_dmg/` 历史安装包归档目录
- `utm_share/` 虚拟机共享测试目录

## 移动内容

移动到 `docs/`：

- `ARCHITECTURE_REVIEW.md` → `docs/ARCHITECTURE_REVIEW.md`
- `ISSUE_STATUS_REPORT.md` → `docs/ISSUE_STATUS_REPORT.md`
- `RELEASE_NOTES_v1.2.1.md` → `docs/RELEASE_NOTES_v1.2.1.md`

移动到 `scripts/`：

- `create_issues.py` → `scripts/create_issues.py`

新增目录：

- `docs/`
- `releases/`
- `scripts/`

## 新目录结构

```text
.
├── ClipboardHistory/              # Swift Package 源码
├── docs/                          # 架构、Issue 状态、Release Notes 等维护文档
│   ├── ARCHITECTURE_REVIEW.md
│   ├── ISSUE_STATUS_REPORT.md
│   └── RELEASE_NOTES_v1.2.1.md
├── releases/                      # Release 相关占位目录，不提交 DMG 产物
│   └── .gitkeep
├── scripts/                       # 维护脚本
│   └── create_issues.py
├── CHANGELOG.md
├── LICENSE
├── Makefile
├── README.md
├── v1.2_issues.md
└── 安装说明.txt
```

## `.gitignore` 更新

已确保以下内容被忽略：

- `.build/` 与嵌套 `.build/`
- `.swiftpm/` 与嵌套 `.swiftpm/`
- `DerivedData/`
- `.DS_Store`
- `*.xcuserstate`
- `*.app`
- `*.dmg`
- `history_dmg/`
- `utm_share/`

## 跟踪文件检查

已使用 `git ls-files` 检查，未发现以下类型被 Git 跟踪：

- DMG 文件
- App bundle
- SwiftPM 构建产物
- `history_dmg/` 内容

## 建议保留文件

建议继续保留在仓库根目录：

- `README.md`：项目首页说明
- `CHANGELOG.md`：版本变更记录
- `LICENSE`：开源许可证
- `Makefile`：构建、打包、运行入口
- `v1.2_issues.md`：历史 Issue 草案清单，可后续移动到 `docs/` 或归档
- `安装说明.txt`：DMG 打包时写入安装镜像

建议继续保留但不提交的本地内容：

- `history_dmg/`：历史测试 DMG 归档
- `utm_share/`：虚拟机共享测试文件
- `时间剪史.app`：本地构建产物
- `时间剪史_v*.dmg`：本地 Release 产物

## 验证命令

本次整理后执行：

```bash
swift build --package-path ClipboardHistory
make bundle
```

验证结果：

- `swift build --package-path ClipboardHistory`：通过
- `make bundle`：通过
- 生成的本地 `时间剪史.app` 为构建产物，已被 `.gitignore` 忽略

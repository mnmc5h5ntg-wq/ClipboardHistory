// swift-tools-version: 6.0
import PackageDescription

let package = Package(
    name: "ClipboardHistory",
    platforms: [
        .macOS(.v12)
    ],
    targets: [
        .executableTarget(
            name: "ClipboardHistoryApp",
            dependencies: ["ClipboardHistoryIntelligenceCore"],
            exclude: [
                "icon_alpha.png"
            ],
            resources: [
                .copy("AppIcon.icns"),
                .process("icon.png")
            ],
            linkerSettings: [
                .linkedFramework("AVFoundation"),
                .linkedFramework("AVKit"),
                .linkedFramework("Carbon"),
                .linkedFramework("Quartz")
            ]
        ),
        // 推荐层共用的隐私词汇表（`AIPrivacyScope` / `AIPrivacySensitivity`）：
        // 产品代码真的在用，所以它是**依赖**而不是草案（账本 R2-15 / 决策 D-020）。
        .target(
            name: "ClipboardHistoryIntelligenceCore"
        ),
        // AI 设计稿：provider 模型与隐私策略草案，**产品代码零调用**（审计第一轮 D-1 / 第二轮 10-07）。
        // 单独成 target 后不再进入交付二进制；测试 target 依赖它，所以那些用例继续跑、继续守着草案自身的一致性。
        .target(
            name: "ClipboardHistoryDesignDrafts",
            dependencies: ["ClipboardHistoryIntelligenceCore"]
        ),
        .testTarget(
            name: "ClipboardHistoryAppTests",
            dependencies: ["ClipboardHistoryApp", "ClipboardHistoryIntelligenceCore"]
        ),
        // 设计稿自己的用例：搬出产品 target 之后仍然要跑（"不许删测试绕过"），
        // 用 `@testable` 拿到草案的内部 API，因此草案本身不必 public。
        .testTarget(
            name: "ClipboardHistoryDesignDraftsTests",
            dependencies: ["ClipboardHistoryDesignDrafts", "ClipboardHistoryIntelligenceCore", "ClipboardHistoryApp"]
        )
    ]
)

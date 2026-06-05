// swift-tools-version: 6.0
import PackageDescription

let package = Package(
    name: "ClipboardHistory",
    platforms: [
        .macOS(.v15)
    ],
    targets: [
        .executableTarget(
            name: "ClipboardHistoryApp",
            resources: [
                .copy("AppIcon.icns"),
                .process("icon.png")
            ],
            linkerSettings: [
                .linkedFramework("Quartz")
            ]
        )
    ]
)

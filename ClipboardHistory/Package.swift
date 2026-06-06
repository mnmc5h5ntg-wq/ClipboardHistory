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
            exclude: [
                "icon_alpha.png"
            ],
            resources: [
                .copy("AppIcon.icns"),
                .process("icon.png")
            ],
            linkerSettings: [
                .linkedFramework("AVFoundation"),
                .linkedFramework("Quartz")
            ]
        )
    ]
)

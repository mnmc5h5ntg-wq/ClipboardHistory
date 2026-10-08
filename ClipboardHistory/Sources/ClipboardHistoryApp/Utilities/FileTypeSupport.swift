import Foundation

enum FileTypeSupport {
    static let imageExtensions: Set<String> = [
        "png", "jpg", "jpeg", "gif", "bmp", "tiff", "tif", "heic", "heif", "webp", "ico"
    ]

    static let videoExtensions: Set<String> = [
        "mp4", "mov", "m4v", "avi", "mkv", "webm", "hevc", "3gp", "3g2"
    ]

    static let textExtensions: Set<String> = [
        "txt", "md", "csv", "json", "xml", "html", "css", "js", "ts",
        "swift", "py", "rb", "go", "rs", "c", "h", "cpp", "java", "sh",
        "yaml", "yml", "toml", "ini", "cfg", "log", "plist", "strings",
        "svg", "tex", "r", "sql", "php", "scala", "kt", "hs", "lua",
        "mm", "m", "hpp", "vue", "svelte", "astro", "jsx", "tsx", "gradle",
        "cmake", "makefile", "dockerfile", "gitignore", "env"
    ]

    static let documentExtensions: Set<String> = [
        "docx", "doc", "pdf", "xlsx", "xls", "pptx", "ppt",
        "pages", "numbers", "keynote", "odt", "ods", "odp",
        "rtf", "rtfd"
    ]
}

extension URL {
    /// 上一级目录的显示名，形如 `…/Downloads`；根目录或空路径退回 `…`。
    var parentDirectoryLabel: String {
        // 先标准化：`URL(fileURLWithPath: "/").deletingLastPathComponent()` 在不同
        // Foundation 版本上给出 "/" 或 "/.."（CI 的 Swift 6.1.2 给后者），
        // 不标准化的话根目录下的文件会被标成 "…/.."。
        let parent = deletingLastPathComponent().standardizedFileURL.path
        let name = URL(fileURLWithPath: parent).standardizedFileURL.lastPathComponent
        guard !name.isEmpty, name != "/", name != ".", name != ".." else { return "…" }
        return "…/\(name)"
    }
}

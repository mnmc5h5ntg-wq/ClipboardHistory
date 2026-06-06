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

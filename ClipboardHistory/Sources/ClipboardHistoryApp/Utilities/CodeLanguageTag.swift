import AppKit

/// 代码块右上角的语言标签。
///
/// 为什么要有这一层（R446）：解析层从围栏信息串里认出了语言
/// （`MarkdownBlock.Kind.codeBlock(language:)`），但呈现层从来没把它显示出来 ——
/// 一段 ```` ```swift ```` 和一段 ```` ```python ```` 在详情里长得一模一样。
/// 语言是作者写下的内容（和行号不同，行号是我们加的），丢掉它等于把围栏里的信息删了。
///
/// 画法刻意不进属性串：标签不进文本存储，复制代码时不会带出 "SWIFT" 这几个字母，
/// 也不会挤动代码的排版。它画在代码块**第一行**的右侧，只有在该行正文与右内边距之间
/// 还放得下（`fits`）时才画 —— 长行代码宁可没有标签，也不能把标签压到代码上。
enum CodeLanguageTag {
    static let fontSize: CGFloat = 9
    /// 标签右沿到正文列右沿的距离。
    static let rightInset: CGFloat = 10
    /// 标签左沿与第一行代码正文之间至少留这么多，少于此就不画。
    static let minimumGap: CGFloat = 24
    static let maxLength = 12

    /// 归一化后的标签文本。
    ///
    /// 认得的别名给短标签（`python` → `PYTHON`、`js` → `JS`）；
    /// 不认得的原样大写、只留标签里能出现的字符，超过 12 个字符截断。
    /// `text` / `plaintext` 这类"没有语言"的围栏信息返回 nil —— 标个 TEXT 是噪声。
    static func label(for language: String?) -> String? {
        guard let raw = language?.trimmingCharacters(in: .whitespacesAndNewlines),
              !raw.isEmpty else { return nil }
        let token = raw.split(whereSeparator: { $0.isWhitespace }).first.map(String.init) ?? raw
        let normalized = token.lowercased()
        if let canonical = aliases[normalized] { return canonical }
        if neutral.contains(normalized) { return nil }
        let upper = token.uppercased()
        let filtered = String(upper.unicodeScalars.filter { allowed.contains($0) })
        guard !filtered.isEmpty else { return nil }
        return String(filtered.prefix(maxLength))
    }

    static func width(of label: String) -> CGFloat {
        (label as NSString).size(withAttributes: [.font: font]).width
    }

    /// 第一行正文右沿到容器右沿之间放得下标签（并留出 `minimumGap`）才画。
    static func fits(codeRightEdge: CGFloat, containerWidth: CGFloat, label: String) -> Bool {
        guard codeRightEdge.isFinite, containerWidth.isFinite else { return false }
        return codeRightEdge + minimumGap <= containerWidth - rightInset - width(of: label)
    }

    /// 标签左沿：右对齐到正文列右沿内 `rightInset` 处。
    static func originX(containerWidth: CGFloat, label: String) -> CGFloat {
        containerWidth - rightInset - width(of: label)
    }

    /// 标签顶沿：与第一行的行高垂直居中，行高不够时贴顶。
    static func originY(lineTop: CGFloat, lineHeight: CGFloat, tagHeight: CGFloat) -> CGFloat {
        lineTop + max(0, (lineHeight - tagHeight) / 2)
    }

    static var font: NSFont { .monospacedSystemFont(ofSize: fontSize, weight: .semibold) }
    /// 动态色：标签是元信息，不能比代码抢眼，也不许在暗档被烤成黑的。
    static var color: NSColor { .secondaryLabelColor }

    private static let aliases: [String: String] = [
        "swift": "SWIFT",
        "python": "PYTHON", "python3": "PYTHON", "py": "PYTHON",
        "javascript": "JS", "js": "JS", "node": "JS",
        "typescript": "TS", "ts": "TS",
        "shell": "SHELL", "sh": "SHELL", "bash": "SHELL", "zsh": "SHELL", "console": "SHELL",
        "json": "JSON", "jsonc": "JSON",
        "yaml": "YAML", "yml": "YAML", "toml": "TOML",
        "html": "HTML", "htm": "HTML", "xml": "XML", "css": "CSS", "scss": "SCSS",
        "sql": "SQL", "markdown": "MARKDOWN", "md": "MARKDOWN",
        "c": "C", "h": "C",
        "cpp": "C++", "c++": "C++", "cxx": "C++",
        "objc": "OBJC", "objective-c": "OBJC",
        "cs": "C#", "csharp": "C#", "c#": "C#",
        "go": "GO", "golang": "GO", "rust": "RUST", "rs": "RUST",
        "ruby": "RUBY", "rb": "RUBY", "java": "JAVA", "kotlin": "KOTLIN", "kt": "KOTLIN",
        "php": "PHP", "perl": "PERL", "lua": "LUA",
        "diff": "DIFF", "patch": "DIFF", "ini": "INI",
        "makefile": "MAKE", "dockerfile": "DOCKER", "docker": "DOCKER",
        "powershell": "POWERSHELL", "ps1": "POWERSHELL",
        "http": "HTTP", "graphql": "GRAPHQL", "proto": "PROTO"
    ]

    private static let neutral: Set<String> = ["text", "plaintext", "plain", "none", "output"]

    private static let allowed: Set<Unicode.Scalar> = {
        var set = Set<Unicode.Scalar>()
        for scalar in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+#.-".unicodeScalars {
            set.insert(scalar)
        }
        return set
    }()
}

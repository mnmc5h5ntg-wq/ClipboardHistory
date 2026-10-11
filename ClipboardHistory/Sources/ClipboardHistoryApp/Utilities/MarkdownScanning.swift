import Foundation

/// Markdown 的**扫描原语**：只回答"这一行/这一段是什么"，不做排版、不做决定。
///
/// 单独成文件的理由：`MarkdownParser` 的块逻辑之所以能读，是因为所有"数空格、找闭栏、
/// 判 flanking"的细节都收在这里，而这些细节恰恰是最容易写错、又最值得逐条钉住的部分。
/// 字符下标一律用 `Array<Character>` 的位置（行内解析要按位置切），
/// 行级判定用 `String` 的方法 —— 两套不要混。
enum MarkdownScanner {
    // MARK: - 行级：缩进与行体

    /// 行首缩进（空格计 1，制表符按 4 计）。`indent >= 4` 就是 CommonMark 的缩进代码。
    static func indent(of line: String) -> Int {
        var total = 0
        for character in line {
            if character == " " { total += 1 }
            else if character == "\t" { total += 4 }
            else { break }
        }
        return total
    }

    /// 去掉首尾空白后的行体。段落续行、标题文本、列表内容都以它为准。
    /// 刻意把行尾空白也去掉：CommonMark 用"行尾两个空格"表示硬换行，
    /// 而本渲染器**保留源文件的每一个换行**（见 `MarkdownParser` 段落一节的注释），
    /// 硬换行在这里是冗余信息，留着两个空格只会让看起来的对齐变成随机。
    static func body(of line: String) -> String {
        line.trimmingCharacters(in: .whitespacesAndNewlines)
    }

    static func isBlank(_ line: String) -> Bool {
        body(of: line).isEmpty
    }

    /// 去掉至多 `spaces` 个前导空白（制表符按 4 计，够用即止）。
    /// 围栏代码块的内容要按开栏的缩进**相对**去缩：整块一律左对齐会把代码的层次抹平，
    /// 而"代码看起来还是那段代码"正是代码块唯一的价值。
    static func dedent(_ line: String, by spaces: Int) -> String {
        guard spaces > 0 else { return line }
        var remaining = spaces
        var index = line.startIndex
        while index < line.endIndex, remaining > 0 {
            let character = line[index]
            if character == " " { remaining -= 1 }
            else if character == "\t" { remaining -= 4 }
            else { break }
            index = line.index(after: index)
        }
        return String(line[index...])
    }

    static func isIndentedCode(_ line: String) -> Bool {
        indent(of: line) >= 4 && !isBlank(line)
    }

    static func dedentIndented(_ line: String) -> String {
        dedent(line, by: 4)
    }

    // MARK: - 标题

    /// ATX 标题：1…6 个 `#`，后面必须跟空格（或整行就只有 `#`）。
    /// `#没有空格` 不是标题 —— CommonMark 如此，而且这条对代码尤其要命。
    /// 反过来 Python/Shell 的 `# 注释` **是**会被认成标题的，所以文本条目才要求
    /// "多个不同信号同时出现"才给渲染入口，见 `minimumSignalsToOfferRendering`。
    static func isATXHeading(_ body: String) -> Bool {
        headingLevel(of: body) != nil
    }

    static func headingLevel(of body: String) -> Int? {
        let characters = Array(body)
        var count = 0
        while count < characters.count, characters[count] == "#" { count += 1 }
        guard count >= 1, count <= MarkdownParsingPolicy.maximumHeadingLevel else { return nil }
        if count == characters.count { return count }
        guard characters[count] == " " || characters[count] == "\t" else { return nil }
        return count
    }

    /// 标题正文：去掉开栏 `#`，以及 CommonMark 允许省略的**闭栏 `#`**。
    /// `## 标题 ##` → `标题`；`# C#` → `C#`（闭栏只在前面是空白时才剥）。
    static func headingText(of body: String) -> String {
        let characters = Array(body)
        var level = 0
        while level < characters.count, characters[level] == "#" { level += 1 }
        var rest = Array(characters[min(level, characters.count)...])
        var trailingHashes = 0
        while trailingHashes < rest.count, rest[rest.count - 1 - trailingHashes] == "#" {
            trailingHashes += 1
        }
        let contentEnd = rest.count - trailingHashes
        if trailingHashes > 0, contentEnd > 0, rest[contentEnd - 1] == " " || rest[contentEnd - 1] == "\t" {
            rest = Array(rest[..<contentEnd])
        }
        return String(rest).trimmingCharacters(in: .whitespaces)
    }

    /// setext 下划线：一整行 `=`（一级）或一整行 `-`（二级）。
    /// 二级刻意要求**至少两个** `-`：单个 `-` 跟在段落后面，在中文笔记里更常见的是
    /// "下面开始列点"的手写分隔线，把它升级成大标题的代价比漏认一个二级标题大。
    /// 这是与 CommonMark 的一处**有意偏差**，`Round4MarkdownTests` 里钉着它。
    static func isSetextUnderline(_ body: String) -> Bool {
        guard !body.isEmpty else { return false }
        if body.allSatisfy({ $0 == "=" }) { return true }
        return body.count >= 2 && body.allSatisfy({ $0 == "-" })
    }

    static func setextLevel(of body: String) -> Int {
        body.first == "=" ? 1 : 2
    }

    // MARK: - 围栏代码

    static func isFence(_ body: String) -> Bool {
        fenceLength(of: body) != nil
    }

    static func fenceCharacter(of body: String) -> Character {
        body.first ?? "`"
    }

    static func fenceLength(of body: String) -> Int? {
        guard let first = body.first, first == "`" || first == "~" else { return nil }
        var count = 0
        for character in body {
            guard character == first else { break }
            count += 1
        }
        return count >= 3 ? count : nil
    }

    /// 信息串的首词 = 语言。反引号围栏的信息串里不允许再出现反引号。
    static func fenceLanguage(of body: String) -> String? {
        guard let first = body.first, first == "`" || first == "~" else { return nil }
        let info = String(body.drop(while: { $0 == first })).trimmingCharacters(in: .whitespaces)
        guard !info.isEmpty else { return nil }
        let word = info.split(whereSeparator: { $0 == " " || $0 == "\t" }).first.map(String.init)
        guard let word, !word.contains("`"), !word.contains("~") else { return nil }
        return word
    }

    static func isFenceClose(_ body: String, marker: Character, minLength: Int) -> Bool {
        guard let length = fenceLength(of: body), body.first == marker, length >= minLength else { return false }
        return body.allSatisfy { $0 == marker }
    }

    // MARK: - 引用

    static func isBlockquote(_ body: String) -> Bool {
        body.hasPrefix(">")
    }

    /// 剥掉一层 `>`（以及 CommonMark 允许紧跟其后的那一个空格）。
    static func blockquoteContent(of line: String) -> String {
        var text = Substring(line)
        while text.first == " " || text.first == "\t" { text = text.dropFirst() }
        guard text.first == ">" else { return String(text) }
        text = text.dropFirst()
        if text.first == " " { text = text.dropFirst() }
        return String(text)
    }

    // MARK: - 分隔线

    /// 一整行只有同一种 `*`/`-`/`_`（可以夹空格）且非空白字符 ≥ 3。
    static func isThematicBreak(_ body: String) -> Bool {
        guard let marker = body.first, marker == "*" || marker == "-" || marker == "_" else { return false }
        var counted = 0
        for character in body {
            if character == marker { counted += 1 }
            else if character == " " || character == "\t" { continue }
            else { return false }
        }
        return counted >= 3
    }

    // MARK: - 列表

    struct ListMarker: Equatable {
        var indent: Int
        /// nil 表示无序列表；有值时**必须渲染出来** —— "1." 是内容不是装饰，
        /// 把它吃掉，"第一步"就没了（这条是"不许丢可见文字"不变量的直接要求）。
        var number: Int?
        var content: String
        var task: MarkdownBlock.TaskState?
    }

    /// 无序标记：`-` / `*` / `+` 后面必须跟空白，且后面得有正文。
    /// 只有标记的行返回 nil（空项画一个悬空圆点没有任何信息，原样显示更诚实）。
    static func unorderedMarker(of body: String) -> Character? {
        guard let first = body.first, first == "-" || first == "*" || first == "+" else { return nil }
        let rest = body.dropFirst()
        guard rest.first == " " || rest.first == "\t" else { return nil }
        guard !rest.trimmingCharacters(in: .whitespaces).isEmpty else { return nil }
        return first
    }

    /// 有序标记：最多 9 位数字 + `.` 或 `)` + 空白 + 正文。
    /// `1.no space` 不是列表（CommonMark 同样如此，否则 "2.Eleven" 这种写法会被拆坏）。
    static func orderedMarker(of body: String) -> (number: Int, content: String)? {
        let characters = Array(body)
        var count = 0
        while count < characters.count, characters[count].isNumber, count < 10 { count += 1 }
        guard count >= 1, count <= 9, count < characters.count else { return nil }
        let delimiter = characters[count]
        guard delimiter == "." || delimiter == ")" else { return nil }
        let afterDelimiter = count + 1
        guard afterDelimiter < characters.count,
              characters[afterDelimiter] == " " || characters[afterDelimiter] == "\t" else { return nil }
        let rest = String(characters[(afterDelimiter + 1)...]).trimmingCharacters(in: .whitespaces)
        guard !rest.isEmpty, let number = Int(String(characters[..<count])) else { return nil }
        return (number, rest)
    }

    /// 行首的列表标记（含任务项）。返回 nil 时这行按段落处理。
    /// `indent` 由调用方从**原始行**算（`body` 已经把缩进吃掉了，深度信息就丢了）。
    static func listMarker(of body: String, indent: Int) -> ListMarker? {
        if unorderedMarker(of: body) != nil {
            let content = String(body.dropFirst()).trimmingCharacters(in: .whitespaces)
            guard !content.isEmpty else { return nil }
            let detected = taskState(in: content)
            return ListMarker(indent: indent, number: nil,
                              content: detected?.remaining ?? content,
                              task: detected?.state)
        }
        if let ordered = orderedMarker(of: body) {
            let detected = taskState(in: ordered.content)
            return ListMarker(indent: indent, number: ordered.number,
                              content: detected?.remaining ?? ordered.content,
                              task: detected?.state)
        }
        return nil
    }

    /// GFM 任务项：`[ ]` / `[x]`。
    /// 返回"去掉标记后的正文"，所以 `[x]` 里的字母 x 变成勾选符号而不是留着 ——
    /// 与 GitHub 一致，代价是"不丢可见文字"那条不变量要显式把它列为例外（测试里写明）。
    static func taskState(in content: String) -> (state: MarkdownBlock.TaskState, remaining: String)? {
        let characters = Array(content)
        guard characters.count >= 4, characters[0] == "[" else { return nil }
        let mark = characters[1]
        guard mark == " " || mark == "x" || mark == "X" else { return nil }
        guard characters[2] == "]", characters[3] == " " else { return nil }
        let remaining = String(characters[4...]).trimmingCharacters(in: .whitespaces)
        guard !remaining.isEmpty else { return nil }
        return (mark == " " ? .unchecked : .checked, remaining)
    }

    // MARK: - 表格

    static func containsPipe(_ body: String) -> Bool {
        body.contains("|")
    }

    /// GFM 表格的分隔行：`| --- | :--: |`。至少两列 —— 单列"表格"和一行普通文字
    /// 的区别太小，宁可不当表格。
    static func isTableRule(_ body: String) -> Bool {
        guard containsPipe(body) else { return false }
        var text = Substring(body)
        if text.first == "|" { text = text.dropFirst() }
        if text.last == "|" { text = text.dropLast() }
        let cells = text.split(separator: "|", omittingEmptySubsequences: false)
        guard cells.count >= 2 else { return false }
        for cell in cells {
            let trimmed = cell.trimmingCharacters(in: .whitespaces)
            guard trimmed.contains("-"), trimmed.allSatisfy({ $0 == "-" || $0 == ":" }) else { return false }
        }
        return true
    }

    /// 表格块 = 表头 + 分隔行 + 之后所有还带竖线的行。分隔行本身不进正文
    /// （它就是"这是表格"的判据，留着会多一行没有意义的横线）。
    /// 内容**逐字保留**：等宽呈现靠的就是作者自己敲的空格，重排会把对齐打碎。
    static func collectTable(lines: [String], from index: Int) -> (MarkdownBlock, nextIndex: Int) {
        var collected: [String] = []
        var cursor = index
        while cursor < lines.count {
            let text = body(of: lines[cursor])
            guard !text.isEmpty, containsPipe(text) else { break }
            if cursor != index + 1 { collected.append(text) }
            cursor += 1
        }
        let content = collected.joined(separator: "\n")
        return (MarkdownBlock(kind: .table, runs: MarkdownBlock.literalRuns(content)), cursor)
    }

    // MARK: - 信号探测（给 `MarkdownParsingPolicy.signals` 用）

    static func containsLinkSyntax(_ body: String) -> Bool {
        body.contains("](") && body.contains(")")
    }

    /// 只认**成对**的强调标记。单个 `*` 在中文笔记里太常当项目符号，
    /// 把它算成信号会让纯文本被误判成 Markdown。
    static func containsEmphasisSyntax(_ body: String) -> Bool {
        body.contains("**") || body.contains("__") || body.contains("~~")
    }

    /// 行内码信号同样只认**成对**的反引号。
    ///
    /// 为什么这条值得单独写：判定文本条目"是不是 Markdown"要两类信号同时出现，
    /// 而任何单个反引号都算一类信号的话，`# 注释` 开头 + 正文里一个孤立反引号
    /// （日志、配置、命令行里都有）就会凑够两类，把一段普通文本排成带标题的文档。
    /// 成对是行内码的**定义**（`MarkdownScanner.findClosingBacktick` 也要求闭栏），
    /// 所以这里不是加严，是把信号的定义和解析器的定义对齐。
    static func containsCodeSpan(_ body: String) -> Bool {
        guard let first = body.firstIndex(of: "`") else { return false }
        return body[body.index(after: first)...].contains("`")
    }

    // MARK: - 字符级：run 与闭栏

    /// "单词字符"（字母或数字）。下划线两侧的这个词界判定靠它。
    ///
    /// 刻意不用 `Character.isLetter`/`isNumber`：这个 SDK 上只有 `isNumber`，
    /// 字母那半边要写 `isLetters`（Swift 5.5 的形参化访问器），跨版本容易踩空；
    /// 而 Foundation 的 `CharacterSet.alphanumerics` 在 macOS 12 到 15 都是同一个语义。
    static func isAlphanumeric(_ character: Character) -> Bool {
        String(character).rangeOfCharacter(from: .alphanumerics) != nil
    }

    static func repeatedRunLength(_ characters: [Character], from index: Int, character: Character) -> Int {
        var length = 0
        var cursor = index
        while cursor < characters.count, characters[cursor] == character {
            length += 1
            cursor += 1
        }
        return length
    }

    /// CommonMark 的行内码空白规则：首尾各有一个空格、且不全是空格时各去一个。
    static func trimOneSpaceEachSide(_ text: String) -> String {
        guard text.hasPrefix(" "), text.hasSuffix(" "), !text.allSatisfy({ $0 == " " }) else { return text }
        return String(text.dropFirst().dropLast())
    }

    /// 找到长度**正好**为 `length` 的闭栏反引号串，返回闭栏之后的位置。
    /// 跨行不算闭栏（行内码不能把整段吃掉），找不到就返回 nil，开栏原样留着。
    static func findClosingBacktick(in characters: [Character], from index: Int, length: Int) -> Int? {
        var cursor = index + length
        let boundary = min(characters.count, index + length + MarkdownParsingPolicy.maximumInlineMarkupDistance)
        while cursor < boundary {
            guard characters[cursor] == "`" else {
                if characters[cursor] == "\n" { return nil }
                cursor += 1
                continue
            }
            let run = repeatedRunLength(characters, from: cursor, character: "`")
            if run == length { return cursor + run }
            cursor += max(run, 1)
        }
        return nil
    }

    /// 找下一个同样成对的标记（`~~`），返回其后位置。
    static func findDuplicate(in characters: [Character], from index: Int, character: Character) -> Int? {
        var cursor = index + 2
        let boundary = min(characters.count, index + 2 + MarkdownParsingPolicy.maximumInlineMarkupDistance)
        while cursor + 1 < boundary {
            if characters[cursor] == character, characters[cursor + 1] == character {
                return cursor + 2
            }
            cursor += 1
        }
        return nil
    }

    struct EmphasisClose: Equatable {
        var contentEnd: Int
        var afterClose: Int
        /// `***x***` 同时给粗体和斜体（run 长度 3）。
        var carriesEmphasis: Bool
        var isStrong: Bool
    }

    /// 找强调标记的闭栏。四件事必须同时成立才认：
    /// ① 开栏右邻非空白、闭栏左邻非空白（flanking 的近似；少了这条 `* 星号 *` 会变斜体）；
    /// ② 闭栏长度 ≥ 开栏长度；
    /// ③ `***` 才叠斜体，`**` 只给粗体，`*` 只给斜体；
    /// ④ **下划线不跨单词**：`snake_case_names` 不能被排成斜体 ——
    ///    这是粘贴代码片段里最常见的误伤，也是这条判定存在的最大理由。
    /// 跳过行内码内部再找闭栏，否则 `` `a * b` `` 里的星号会被当成闭栏。
    static func findEmphasisClose(in characters: [Character], from index: Int,
                                  character: Character, runLength: Int) -> EmphasisClose? {
        guard runLength >= 1, runLength <= 3 else { return nil }
        let isStrong = runLength >= 2
        let requiredCloser = runLength
        // 下划线的左边界：前面是字母或数字就不是强调开栏（snake_case）。
        if character == "_", index > 0, isAlphanumeric(characters[index - 1]) { return nil }
        guard index + runLength < characters.count else { return nil }
        let afterOpening = characters[index + runLength]
        guard !afterOpening.isWhitespace else { return nil }

        var cursor = index + runLength
        let boundary = min(characters.count, index + runLength + MarkdownParsingPolicy.maximumInlineMarkupDistance)
        while cursor < boundary {
            let current = characters[cursor]
            if current == "\\" { cursor += 2; continue }
            if current == "`" {
                let run = repeatedRunLength(characters, from: cursor, character: "`")
                if let closed = findClosingBacktick(in: characters, from: cursor, length: run) {
                    cursor = closed
                    continue
                }
            }
            if current != character { cursor += 1; continue }

            let run = repeatedRunLength(characters, from: cursor, character: character)
            defer { cursor += max(run, 1) }
            guard run >= requiredCloser, cursor > index + runLength else { continue }
            let before = characters[cursor - 1]
            guard !before.isWhitespace else { continue }
            if character == "_", cursor + run < characters.count, isAlphanumeric(characters[cursor + run]) {
                continue
            }
            let closerLength = min(run, requiredCloser)
            return EmphasisClose(contentEnd: cursor,
                                 afterClose: cursor + closerLength,
                                 carriesEmphasis: runLength == 1 || (runLength == 3 && run >= 3),
                                 isStrong: isStrong)
        }
        return nil
    }

    /// `[标签](地址)`。返回 nil 时整串按字面量留着 —— 包括 `![图](x)` 的图片语法：
    /// 前面是 `!` 就不吃，因为把 alt 文本显示成一个**可点链接**是说谎，
    /// 而原样显示 `![图](x)` 至多不好看，内容一个字不少。
    struct InlineLink: Equatable {
        var label: String
        var destination: String
        var afterDestination: Int
    }

    static func linkAt(_ characters: [Character], from index: Int) -> InlineLink? {
        guard characters[index] == "[" else { return nil }
        if index > 0, characters[index - 1] == "!" { return nil }
        var depth = 0
        var cursor = index
        var labelEnd: Int?
        let labelBoundary = min(characters.count, index + MarkdownParsingPolicy.maximumInlineMarkupDistance)
        while cursor < labelBoundary {
            if characters[cursor] == "\n" { break }
            if characters[cursor] == "[" { depth += 1 }
            else if characters[cursor] == "]" {
                depth -= 1
                if depth == 0 { labelEnd = cursor; break }
            }
            cursor += 1
        }
        guard let closing = labelEnd, closing + 1 < characters.count, characters[closing + 1] == "(" else { return nil }
        var targetDepth = 0
        var walker = closing + 1
        var destinationEnd: Int?
        let destinationBoundary = min(characters.count, closing + 1 + MarkdownParsingPolicy.maximumInlineMarkupDistance)
        while walker < destinationBoundary {
            let symbol = characters[walker]
            if symbol == "\n" { break }
            if symbol == "(" { targetDepth += 1 }
            else if symbol == ")" {
                targetDepth -= 1
                if targetDepth == 0 { destinationEnd = walker; break }
            }
            walker += 1
        }
        guard let destinationClosing = destinationEnd else { return nil }
        let raw = String(characters[(closing + 2)..<destinationClosing])
        let destination = raw.trimmingCharacters(in: .whitespaces)
        guard !destination.isEmpty else { return nil }
        let label = String(characters[(index + 1)..<closing]).trimmingCharacters(in: .whitespaces)
        // 空标签 `[<url>](url)` 少见，但 `[​](x)` 显示成"一个看不见的链接"是最坏结果，
        // 所以标签为空时退回显示地址本身。
        return InlineLink(label: label.isEmpty ? destination : label,
                          destination: destination,
                          afterDestination: destinationClosing + 1)
    }

    /// `<https://…>` / `<mailto:…>`。只认这几种协议，尖括号内不许有空白。
    ///
    /// 协议名单必须和 `MarkdownPresentation.linkURL(for:)` **逐个对齐**：
    /// 解析层认了、呈现层不给 `.link` 的话，屏幕上就是一个"蓝色、看起来能点、点了没反应"的字 ——
    /// 那是比不给链接更坏的假 affordance（`Round4MarkdownTests` 里有一条不变量专门钉这件事）。
    /// `file:` 特意不在名单里：本地路径不该被一个只读预览变成可点击的启动器。
    static func autolinkAt(_ characters: [Character], from index: Int) -> (url: String, afterClose: Int)? {
        guard characters[index] == "<" else { return nil }
        var cursor = index + 1
        while cursor < characters.count, characters[cursor] != ">", !characters[cursor].isWhitespace {
            cursor += 1
        }
        guard cursor < characters.count, characters[cursor] == ">", cursor > index + 1 else { return nil }
        let url = String(characters[(index + 1)..<cursor])
        guard let colon = url.firstIndex(of: ":") else { return nil }
        let scheme = String(url[..<colon]).lowercased()
        guard ["http", "https", "mailto"].contains(scheme) else { return nil }
        return (url, cursor + 1)
    }

    // MARK: - 连续同类行的收集

    static func collectConsecutive(lines: [String], from index: Int,
                                   where predicate: (String) -> Bool) -> (collected: [String], nextIndex: Int) {
        var collected: [String] = []
        var cursor = index
        while cursor < lines.count, predicate(lines[cursor]) {
            collected.append(lines[cursor])
            cursor += 1
        }
        return (collected, cursor)
    }
}

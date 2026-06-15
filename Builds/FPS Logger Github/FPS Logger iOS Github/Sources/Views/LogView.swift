import SwiftUI
#if canImport(AppKit)
import AppKit
#endif

struct LogView: View {
    @Environment(MainViewModel.self) private var vm
    @Environment(\.dismiss) private var dismiss
    @State private var searchText = ""
    @State private var showSearch = false
    @State private var logContent = ""
    @State private var matchCount = 0
    @State private var currentMatchIndex = 0
    @FocusState private var searchFocused: Bool

    var body: some View {
        VStack(spacing: 0) {
            // Toolbar
            HStack {
                Text("FPS Logger \(vm.version) Logs")
                    .font(.system(size: 14, weight: .semibold))
                Spacer()
                Button {
                    withAnimation(.easeInOut(duration: 0.15)) { showSearch.toggle() }
                    if showSearch { searchFocused = true }
                } label: {
                    Image(systemName: showSearch ? "magnifyingglass.circle.fill" : "magnifyingglass")
                }
                .keyboardShortcut("f", modifiers: .command)
                .help("Find (⌘F)")

                Button("Export…") { vm.exportLogs() }

                Button("Done") { dismiss() }
                    .keyboardShortcut(.escape)
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 10)
            .background(Color.controlBg)

            // Search bar
            if showSearch {
                HStack(spacing: 6) {
                    Image(systemName: "magnifyingglass")
                        .foregroundStyle(.secondary)
                    TextField("Search logs…", text: $searchText)
                        .textFieldStyle(.plain)
                        .focused($searchFocused)
                        .onSubmit { navigateMatch(forward: true) }
                        .onChange(of: searchText) {
                            currentMatchIndex = 0
                        }
                    if !searchText.isEmpty {
                        // Match count
                        Text(matchCount == 0 ? "No results" : "\(currentMatchIndex + 1) of \(matchCount)")
                            .font(.system(size: 11))
                            .foregroundStyle(matchCount == 0 ? .red : .secondary)
                            .fixedSize()

                        // Navigation buttons
                        HStack(spacing: 2) {
                            Button { navigateMatch(forward: false) } label: {
                                Image(systemName: "chevron.left")
                            }
                            .buttonStyle(.plain)
                            .disabled(matchCount == 0)

                            Button { navigateMatch(forward: true) } label: {
                                Image(systemName: "chevron.right")
                            }
                            .buttonStyle(.plain)
                            .disabled(matchCount == 0)
                        }

                        Button { searchText = "" } label: {
                            Image(systemName: "xmark.circle.fill").foregroundStyle(.secondary)
                        }
                        .buttonStyle(.plain)
                    }
                    Button("Done") {
                        searchText = ""
                        showSearch = false
                    }
                    .keyboardShortcut(.escape)
                }
                .padding(.horizontal, 12)
                .padding(.vertical, 6)
                .background(Color.controlBg.opacity(0.9))
            }

            Divider()

            // Log text
            LogTextView(
                logBuffer: vm.logBuffer,
                searchText: searchText,
                currentMatchIndex: currentMatchIndex,
                matchCount: $matchCount
            )
        }
        .frame(minWidth: 800, minHeight: 500)
    }

    private func navigateMatch(forward: Bool) {
        guard matchCount > 0 else { return }
        if forward {
            currentMatchIndex = (currentMatchIndex + 1) % matchCount
        } else {
            currentMatchIndex = (currentMatchIndex - 1 + matchCount) % matchCount
        }
    }

}

#if canImport(AppKit)
private class AutoFocusTextView: NSTextView {
    override func viewDidMoveToWindow() {
        super.viewDidMoveToWindow()
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.3) { [weak self] in
            guard let self, let window = self.window else { return }
            window.makeFirstResponder(self)
        }
    }

    override func performKeyEquivalent(with event: NSEvent) -> Bool {
        if event.modifierFlags.contains(.command) && event.charactersIgnoringModifiers == "a" {
            selectAll(nil)
            return true
        }
        return super.performKeyEquivalent(with: event)
    }
}

struct LogTextView: NSViewRepresentable {
    let logBuffer: [String]
    let searchText: String
    let currentMatchIndex: Int
    @Binding var matchCount: Int

    class Coordinator {
        var matchRanges: [NSRange] = []
    }

    func makeCoordinator() -> Coordinator { Coordinator() }

    func makeNSView(context: Context) -> NSScrollView {
        let textView = AutoFocusTextView(frame: .zero)
        textView.isEditable = false
        textView.isSelectable = true
        textView.font = NSFont.monospacedSystemFont(ofSize: 11, weight: .regular)
        textView.backgroundColor = .textBackgroundColor
        textView.textColor = .textColor
        textView.textContainerInset = NSSize(width: 4, height: 4)
        textView.isVerticallyResizable = true
        textView.isHorizontallyResizable = false
        textView.autoresizingMask = [.width]
        textView.textContainer?.widthTracksTextView = true
        textView.allowsUndo = false

        let scrollView = NSScrollView()
        scrollView.documentView = textView
        scrollView.hasVerticalScroller = true
        scrollView.hasHorizontalScroller = false
        scrollView.autohidesScrollers = true
        return scrollView
    }

    func updateNSView(_ scrollView: NSScrollView, context: Context) {
        let textView = scrollView.documentView as! NSTextView
        let content = logBuffer.joined()
        let displayContent = content.isEmpty ? "No logs yet." : content

        if textView.string != displayContent {
            textView.string = displayContent
            textView.scrollToEndOfDocument(nil)
        }

        let attrStr = NSMutableAttributedString(string: displayContent)
        let fullRange = NSRange(location: 0, length: attrStr.length)
        attrStr.addAttribute(.font, value: NSFont.monospacedSystemFont(ofSize: 11, weight: .regular), range: fullRange)
        attrStr.addAttribute(.foregroundColor, value: NSColor.textColor, range: fullRange)

        var ranges: [NSRange] = []
        if !searchText.isEmpty {
            let nsContent = displayContent as NSString
            var searchRange = NSRange(location: 0, length: nsContent.length)
            while searchRange.location < nsContent.length {
                let found = nsContent.range(of: searchText, options: .caseInsensitive, range: searchRange)
                if found.location == NSNotFound { break }
                ranges.append(found)
                searchRange = NSRange(location: found.upperBound, length: nsContent.length - found.upperBound)
            }

            for (i, range) in ranges.enumerated() {
                let highlight: NSColor = i == currentMatchIndex ? .systemOrange : .systemYellow
                attrStr.addAttribute(.backgroundColor, value: highlight, range: range)
            }
        }

        textView.textStorage?.setAttributedString(attrStr)
        context.coordinator.matchRanges = ranges

        let count = ranges.count
        DispatchQueue.main.async {
            matchCount = count
        }

        if !ranges.isEmpty && currentMatchIndex < ranges.count {
            let targetRange = ranges[currentMatchIndex]
            textView.scrollRangeToVisible(targetRange)
            textView.showFindIndicator(for: targetRange)
        }
    }
}
#else
struct LogTextView: View {
    let logBuffer: [String]
    let searchText: String
    let currentMatchIndex: Int
    @Binding var matchCount: Int

    var body: some View {
        ScrollView {
            Text(logBuffer.joined().isEmpty ? "No logs yet." : logBuffer.joined())
                .font(.system(size: 11, design: .monospaced))
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(4)
        }
    }
}
#endif

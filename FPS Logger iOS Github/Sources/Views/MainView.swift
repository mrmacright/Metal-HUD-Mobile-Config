import SwiftUI

struct MainView: View {
    @Environment(MainViewModel.self) private var vm
    @State private var showConnectionHelp = false
    @State private var connectionHelpSection: String? = nil
    @State private var showConnectionStateInfo = false
    @State private var showLogViewer = false
    @State private var showCustomMetrics = false
    @State private var showContactSupportAlert = false
    @State private var splitPosition: CGFloat = 635
    private let minSplit: CGFloat = 360
    private let maxSplit: CGFloat = 800
    @State private var logPanelHeight: CGFloat = 140
    private let minLogHeight: CGFloat = 50
    private let maxLogHeight: CGFloat = 400
    @State private var libraryWidth: CGFloat = 260
    private let minLibraryWidth: CGFloat = 180
    private let maxLibraryWidth: CGFloat = 480

    var body: some View {
        @Bindable var vm = vm

        VStack(spacing: 0) {
            // Main content area
            HStack(spacing: 0) {
                // Left: Device list
                DeviceListView()
                    .frame(width: splitPosition)

                SplitDivider(splitPosition: $splitPosition, min: minSplit, max: maxSplit)

                // Center: App list + launch controls
                VStack(spacing: 0) {
                    AppListView()
                    Divider()
                    LaunchControlsView()
                }

                // Right: Library sidebar (collapsible)
                if vm.showLibrary {
                    RightPanelDivider(panelWidth: $libraryWidth, min: minLibraryWidth, max: maxLibraryWidth)
                    LibraryView()
                        .frame(width: libraryWidth)
                        .transition(.move(edge: .trailing))
                }
            }
            .animation(.easeInOut(duration: 0.25), value: vm.showLibrary)

            if vm.showLogPanel {
                BottomPanelDivider(panelHeight: $logPanelHeight, min: minLogHeight, max: maxLogHeight)

                // Bottom: Log output
                LogPanelView(showLogViewer: $showLogViewer)
                    .frame(height: logPanelHeight)
                    .transition(.move(edge: .bottom).combined(with: .opacity))
            }

            // Status bar
            StatusBarView()
                .frame(height: 26)
        }
        .animation(.easeInOut(duration: 0.25), value: vm.showLogPanel)
        .background(Color.windowBg)
        .sheet(isPresented: $showConnectionHelp) {
            ConnectionHelpView(initialSection: connectionHelpSection)
        }
        .sheet(isPresented: $showConnectionStateInfo) {
            if let device = vm.connectionStateInfoDevice {
                ConnectionStateInfoView(device: device)
            }
        }
        .sheet(isPresented: $showLogViewer) {
            LogView()
                .environment(vm)
                .frame(width: 1200, height: 650)
        }
        .sheet(isPresented: $showCustomMetrics) {
            CustomMetricsView()
                .environment(vm)
        }
        .alert("Contact Support", isPresented: $showContactSupportAlert) {
            Button("Attach Logs") {
                let buildType = "FPS Logger iOS Github"
                let macOSVersion = ProcessInfo.processInfo.operatingSystemVersionString
                let appVersion = Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String ?? ""
                let subject = "FPS Logger Support"
                let body = "Build: \(buildType)\nmacOS: \(macOSVersion)\nApp Version: \(appVersion)\n\n[Please describe your issue here]"
                vm.openMailWithLogs(subject: subject, body: body)
            }
            Button("Open Mail") {
                let buildType = "FPS Logger iOS Github"
                let macOSVersion = ProcessInfo.processInfo.operatingSystemVersionString
                let appVersion = Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String ?? ""
                let subject = "FPS Logger Support"
                let body = "Build: \(buildType)\nmacOS: \(macOSVersion)\nApp Version: \(appVersion)\n\n[Please describe your issue here]"
                let encodedSubject = subject.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? subject
                let encodedBody = body.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? body
                if let url = URL(string: "mailto:business@mrmacright.com?subject=\(encodedSubject)&body=\(encodedBody)") {
                    #if canImport(AppKit)
                    NSWorkspace.shared.open(url)
                    #else
                    UIApplication.shared.open(url)
                    #endif
                }
            }
            Button("Cancel", role: .cancel) {}
        } message: {
            Text("Would you like to attach session logs?")
        }
        .onReceive(NotificationCenter.default.publisher(for: .showContactSupport)) { _ in
            showContactSupportAlert = true
        }
        .onReceive(NotificationCenter.default.publisher(for: .showConnectionHelp)) { note in
            connectionHelpSection = note.object as? String
            showConnectionHelp = true
        }
        .onReceive(NotificationCenter.default.publisher(for: .showConnectionStateInfo)) { _ in
            showConnectionStateInfo = true
        }
        .onReceive(NotificationCenter.default.publisher(for: .showCustomMetrics)) { _ in
            showCustomMetrics = true
        }
        .onAppear {
            #if canImport(AppKit)
            XcodeManager.shared.checkAndSetup(vm: vm)
            #endif
        }
    }
}

// MARK: - Launch Controls

struct LaunchControlsView: View {
    @Environment(MainViewModel.self) private var vm
    @State private var showAppStorePerfAlert = false

    var body: some View {
        VStack(spacing: 0) {
            HStack(spacing: 12) {
                // Show Running Games
                Button {
                    if let device = vm.selectedDevice {
                        vm.pendingSelectInternalName = nil
                        Task { await vm.showApps(for: device) }
                    }
                } label: {
                    Text("Show Running Games")
                        .font(.system(size: 12))
                }
                .disabled(vm.selectedDevice == nil || vm.isListingApps)
                .buttonStyle(.bordered)
                .controlSize(.small)
                .help("Show Running Games (⌘S)")
                .keyboardShortcut("s", modifiers: .command)

                Spacer()

                Button {
                    showAppStorePerfAlert = true
                } label: {
                    HStack(spacing: 4) {
                        Image(systemName: "chart.xyaxis.line")
                        Text("Log Performance")
                    }
                    .font(.system(size: 12))
                }
                .buttonStyle(.plain)
                .foregroundStyle(.secondary)
                .help("Log Performance requires the App Store version")
                .alert("App Store Version Required", isPresented: $showAppStorePerfAlert) {
                    Button("Get on App Store") {
                        #if canImport(AppKit)
                        NSWorkspace.shared.open(URL(string: "https://apps.apple.com/app/id6763967836")!)
                        #else
                        UIApplication.shared.open(URL(string: "itms-apps://")!)
                        #endif
                    }
                    Button("Cancel", role: .cancel) {}
                } message: {
                    Text("Performance logging is available in the App Store version of FPS Logger, which also includes session graphs, app icons, and more.")
                }
                .onReceive(NotificationCenter.default.publisher(for: .showAppStorePerfInfo)) { _ in
                    showAppStorePerfAlert = true
                }

                LaunchButton()
            }
            .padding(.horizontal, 16)
            .padding(.top, 10)
            .padding(.bottom, vm.statusText.isEmpty ? 10 : 4)

            if !vm.statusText.isEmpty {
                Text(vm.statusText)
                    .font(.system(size: 11))
                    .foregroundStyle(.secondary)
                    .frame(maxWidth: .infinity, alignment: .trailing)
                    .padding(.horizontal, 16)
                    .padding(.bottom, 8)
                    .transition(.opacity)
            }
        }
        .background(Color.controlBg)
        .animation(.easeInOut(duration: 0.15), value: vm.statusText.isEmpty)
    }
}

struct LaunchButton: View {
    @Environment(MainViewModel.self) private var vm

    var body: some View {
        Group {
            if vm.isRunning {
                Button("Stop") {
                    vm.stopApp()
                }
                .foregroundStyle(.red)
                .controlSize(.large)
            } else {
                Button {
                    guard let device = vm.selectedDevice else { return }
                    if let app = vm.selectedApp {
                        Task { await vm.launchApp(device: device, app: app) }
                    } else if let entry = vm.selectedHistoryEntry {
                        let app = AppEntry(internalName: entry.appName, displayName: entry.displayAppName, appPath: entry.appPath)
                        Task { await vm.launchApp(device: device, app: app) }
                    }
                } label: {
                    if vm.isLaunching {
                        HStack {
                            ProgressView().controlSize(.mini)
                            Text("Launching…")
                        }
                    } else if let app = vm.selectedApp {
                        Text("Launch \(app.displayName) with Metal HUD")
                    } else if let entry = vm.selectedHistoryEntry {
                        Text("Launch \(entry.displayAppName) with Metal HUD")
                    } else {
                        Text("Launch with Metal HUD")
                    }
                }
                .disabled(vm.selectedDevice == nil || (vm.selectedApp == nil && vm.selectedHistoryEntry == nil) || vm.isLaunching || vm.isListingApps)
                .controlSize(.large)
                .buttonStyle(.borderedProminent)
            }
        }
    }
}

// MARK: - Log Panel (bottom strip)

struct LogPanelView: View {
    @Environment(MainViewModel.self) private var vm
    @Binding var showLogViewer: Bool

    var body: some View {
        VStack(spacing: 0) {
            HStack {
                Text("Log")
                    .font(.system(size: 11, weight: .semibold))
                    .foregroundStyle(.secondary)
                Spacer()
                Button("View Logs") { showLogViewer = true }
                    .font(.system(size: 11))
                    #if canImport(AppKit)
                    .buttonStyle(.link)
                    #else
                    .buttonStyle(.plain)
                    #endif
            }
            .padding(.horizontal, 12)
            .padding(.top, 6)
            .padding(.bottom, 2)

            ScrollViewReader { proxy in
                ScrollView(.vertical) {
                    LazyVStack(alignment: .leading, spacing: 0) {
                        ForEach(Array(vm.logBuffer.suffix(200).enumerated()), id: \.offset) { _, line in
                            Text(line)
                                .font(.system(size: 11, design: .monospaced))
                                .frame(maxWidth: .infinity, alignment: .leading)
                        }
                        Color.clear.frame(height: 1).id("bottom")
                    }
                    .textSelection(.enabled)
                    .padding(.horizontal, 12)
                }
                .onChange(of: vm.logBuffer.count) { _, _ in
                    proxy.scrollTo("bottom", anchor: .bottom)
                }
            }
            .background(Color.textBg)
        }
    }
}

// MARK: - Status Bar

struct StatusBarView: View {
    @Environment(MainViewModel.self) private var vm

    var body: some View {
        HStack {
            Spacer()
            if !vm.connectionHint.isEmpty {
                Text(vm.connectionHint)
                    .font(.system(size: 11))
                    .foregroundStyle(.secondary)
            }
            Button {
                vm.showLogPanel.toggle()
                vm.save()
            } label: {
                Image(systemName: "rectangle.bottomthird.inset.filled")
                    .font(.system(size: 12))
                    .foregroundStyle(vm.showLogPanel ? Color.accentColor : .secondary)
            }
            .buttonStyle(.plain)
            .help(vm.showLogPanel ? "Hide Log Panel" : "Show Log Panel")
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 4)
        .background(Color.windowBg)
    }
}

// MARK: - Draggable split dividers

struct SplitDivider: View {
    @Binding var splitPosition: CGFloat
    let min: CGFloat
    let max: CGFloat
    @State private var dragStart: CGFloat? = nil

    var body: some View {
        Color.separator
            .frame(width: 1)
            .frame(maxHeight: .infinity)
            .padding(.horizontal, 4)
            .contentShape(Rectangle())
            .onHover { inside in
                #if canImport(AppKit)
                if inside { NSCursor.resizeLeftRight.push() } else { NSCursor.pop() }
                #endif
            }
            .gesture(
                DragGesture(minimumDistance: 0, coordinateSpace: .global)
                    .onChanged { value in
                        let start = dragStart ?? splitPosition
                        if dragStart == nil { dragStart = splitPosition }
                        splitPosition = Swift.max(min, Swift.min(max, start + value.translation.width))
                    }
                    .onEnded { _ in dragStart = nil }
            )
    }
}

// Draggable divider for a right-side panel — dragging left grows the panel.
struct RightPanelDivider: View {
    @Binding var panelWidth: CGFloat
    let min: CGFloat
    let max: CGFloat
    @State private var dragStart: CGFloat? = nil

    var body: some View {
        Color.separator
            .frame(width: 1)
            .frame(maxHeight: .infinity)
            .padding(.horizontal, 4)
            .contentShape(Rectangle())
            .onHover { inside in
                #if canImport(AppKit)
                if inside { NSCursor.resizeLeftRight.push() } else { NSCursor.pop() }
                #endif
            }
            .gesture(
                DragGesture(minimumDistance: 0, coordinateSpace: .global)
                    .onChanged { value in
                        let start = dragStart ?? panelWidth
                        if dragStart == nil { dragStart = panelWidth }
                        panelWidth = Swift.max(min, Swift.min(max, start - value.translation.width))
                    }
                    .onEnded { _ in dragStart = nil }
            )
    }
}

// Draggable divider for a bottom panel — dragging up grows the panel.
struct BottomPanelDivider: View {
    @Binding var panelHeight: CGFloat
    let min: CGFloat
    let max: CGFloat
    @State private var dragStart: CGFloat? = nil

    var body: some View {
        Color.separator
            .frame(height: 1)
            .frame(maxWidth: .infinity)
            .padding(.vertical, 4)
            .contentShape(Rectangle())
            .onHover { inside in
                #if canImport(AppKit)
                if inside { NSCursor.resizeUpDown.push() } else { NSCursor.pop() }
                #endif
            }
            .gesture(
                DragGesture(minimumDistance: 0, coordinateSpace: .global)
                    .onChanged { value in
                        let start = dragStart ?? panelHeight
                        if dragStart == nil { dragStart = panelHeight }
                        panelHeight = Swift.max(min, Swift.min(max, start - value.translation.height))
                    }
                    .onEnded { _ in dragStart = nil }
            )
    }
}

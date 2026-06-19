import Foundation
#if canImport(AppKit)
import AppKit
#elseif canImport(UIKit)
import UIKit
#endif
import Observation

@MainActor
@Observable
final class MainViewModel {

    // MARK: - App state
    var devices: [Device] = []
    var selectedDevice: Device?
    var apps: [AppEntry] = []
    var selectedApp: AppEntry?
    var logBuffer: [String] = []

    // MARK: - UI state
    var isListingDevices: Bool = false
    var isListingApps: Bool = false
    var isLaunching: Bool = false
    var statusText: String = ""
    var connectionHint: String = ""
    var showLibrary: Bool = false
    var showLogPanel: Bool = true

    // MARK: - Settings
    var hudSettings: HUDSettings = HUDSettings() {
        didSet { logHUDSettingsChanges(from: oldValue, to: hudSettings) }
    }
    var analyticsOptIn: Bool? = nil
    var agreementsAccepted: Bool = false

    // MARK: - History, library and persistence
    var commandHistory: [CommandHistoryEntry] = []
    var selectedHistoryEntry: CommandHistoryEntry? = nil
    var savedGames: [SavedGame] = []
    var hiddenApps: Set<String> = []
    var pinnedApps: Set<String> = []
    var lastDeviceScan: [Device] = []
    var firstDeviceScanNoticeShown: Bool = false

    // MARK: - App list state
    var appSearchText: String = ""
    var appSortMode: AppSortMode = .name
    var liveDisplayNames: [String: String] = [:]
    var liveBundleIDs: [String: String] = [:]
    var livePathDisplayNames: [String: String] = [:]  // appPath → displayName for generic-named apps
    var appLastDetected: [String: Date] = [:]

    // MARK: - Process management
    var currentLaunchProcess: PlatformProcess?
    var isRunning: Bool = false

    // Set before calling showApps; cleared after the matching app is selected.
    var pendingSelectInternalName: String? = nil

    var appsHaveBeenFetched: Bool = false

    private var perfLogTimer: Timer?

    // MARK: - Connection state info

    var connectionStateInfoDevice: Device? = nil

    // MARK: - Overlays
    var showPoliciesOverlay: Bool = false
    var showAnalyticsOverlay: Bool = false
    var xcodeRequired: Bool = true        // GitHub: true until XcodeManager confirms Xcode is present

    // MARK: - Services
    private let deviceService = DeviceService.shared
    let analytics = AnalyticsService.shared
    private let persistence = PersistenceService.shared

    let version: String = Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String ?? "5.0.0"
    let isAppStoreBuild: Bool = {
        ProcessInfo.processInfo.environment["APP_SANDBOX_CONTAINER_ID"] != nil
    }()

    // MARK: - Init
    init() {
        // Mac specs logged before anything else — hudSettings assignment below fires didSet
        // which logs Settings changes, so this must come first.
        #if canImport(AppKit)
        let macOS = ProcessInfo.processInfo.operatingSystemVersionString
        let mem = ProcessInfo.processInfo.physicalMemory / (1024 * 1024 * 1024)
        var specParts: [String] = []
        if let model = macModel() { specParts.append(model) }
        specParts.append("\(mem) GB")
        specParts.append("macOS \(macOS)")
        appendLog("[Mac] \(specParts.joined(separator: ", "))\n")
        appendLog("FPS Logger iOS Github \(version)\n")
        #endif

        let state = persistence.load()
        hudSettings = state.hudSettings
        analyticsOptIn = state.analyticsOptIn
        agreementsAccepted = state.agreementsAccepted
        commandHistory = state.commandHistory
        savedGames = state.savedGames
        hiddenApps = Set(state.hiddenApps)
        pinnedApps = Set(state.pinnedApps)
        firstDeviceScanNoticeShown = state.firstDeviceScanNoticeShown
        lastDeviceScan = state.lastDeviceScan.map {
            guard $0.deviceType == .appleWatch else { return $0 }
            var d = $0; d.state = "unsupported"; return d
        }
        showLibrary = state.libraryPanelOpen
        showLogPanel = state.logPanelOpen
        // Restore console-detected identities so generic-named apps show correctly on relaunch
        for (internalName, bundleID) in state.detectedBundleIDs {
            // Skip old entries where the key is a generic process name — those are superseded by detectedPathNames
            guard !AppData.skipIconLookup.contains(internalName) else { continue }
            liveBundleIDs[internalName] = bundleID
            if let name = AppData.consoleBundleIDRenames[bundleID] {
                liveDisplayNames[internalName] = name
            }
        }
        livePathDisplayNames = state.detectedPathNames

        analytics.isOptedIn = analyticsOptIn == true
        analytics.appVersion = "\(version) FPS Logger iOS Github"
        analytics.getDisplayState = { [weak self] state in
            self?.devices.first(where: { $0.identifier == state })?.displayState ?? state
        }

        #if canImport(AppKit)
        let (_, devicectlLog) = DeviceService.findDevicectlWithLog()
        let build = Bundle.main.infoDictionary?["CFBundleVersion"] as? String ?? "?"
        appendLog("[Init] appstore_build=\(isAppStoreBuild) build=\(build) devicectl=\(deviceService.devicectlPath)\n")
        appendLog(devicectlLog)
        logXcodeSelect()
        checkMacOSVersion()
        #else
        let build = Bundle.main.infoDictionary?["CFBundleVersion"] as? String ?? "?"
        appendLog("[Init] appstore_build=\(isAppStoreBuild) build=\(build) platform=iOS\n")
        logIOSSpecs()
        #endif
    }

    // MARK: - Logging
    func appendLog(_ text: String) {
        logBuffer.append(text)
        if logBuffer.count > 50_000 {
            logBuffer.removeFirst(logBuffer.count - 50_000)
        }
        print(text, terminator: "")
    }

    private func logHUDSettingsChanges(from old: HUDSettings, to new: HUDSettings) {
        if old.preset != new.preset {
            appendLog("[Settings] Metric preset: \(old.preset.rawValue) → \(new.preset.rawValue)\n")
        }
        if old.alignment != new.alignment {
            appendLog("[Settings] Position: \(old.alignment.rawValue) → \(new.alignment.rawValue)\n")
        }
        if old.scale != new.scale {
            appendLog("[Settings] Scale: \(old.scale.rawValue) → \(new.scale.rawValue)\n")
        }
        if old.customElements != new.customElements {
            let enabled = HUDSettings.customElementKeys
                .filter { new.customElements[$0.key] == true }
                .map { $0.label }
            let summary = enabled.isEmpty ? "(none)" : enabled.joined(separator: ", ")
            appendLog("[Settings] Custom metrics: \(summary)\n")
        }
    }

    func exportLogs() {
        #if canImport(AppKit)
        let text = logBuffer.joined()
        guard !text.isEmpty else { return }

        let panel = NSSavePanel()
        panel.nameFieldStringValue = "MetalHUD_Logs.txt"
        panel.allowedContentTypes = [.plainText]
        panel.directoryURL = FileManager.default.urls(for: .desktopDirectory, in: .userDomainMask).first

        if panel.runModal() == .OK, let url = panel.url {
            do {
                try text.write(to: url, atomically: true, encoding: .utf8)
                NSWorkspace.shared.open(url)
            } catch {
                let alert = NSAlert()
                alert.messageText = "Export Failed"
                alert.informativeText = error.localizedDescription
                alert.runModal()
            }
        }
        #endif
    }

    /// Opens a Mail compose window with logs attached, recipient and subject pre-filled.
    /// Pass `logSuffix` to append extra context (e.g. device connection info) to the log file only — it does not affect the in-app log buffer.
    func openMailWithLogs(subject: String, body: String, logSuffix: String = "") {
        #if canImport(AppKit)
        let text = logBuffer.joined() + logSuffix
        guard !text.isEmpty else { return }

        let tempURL = FileManager.default.temporaryDirectory.appendingPathComponent("MetalHUD_Logs.txt")
        guard (try? text.write(to: tempURL, atomically: true, encoding: .utf8)) != nil else { return }

        if let service = NSSharingService(named: .composeEmail) {
            service.recipients = ["business@mrmacright.com"]
            service.subject = subject
            service.perform(withItems: [body, tempURL])
        }
        #endif
    }

    #if canImport(AppKit)
    private func logXcodeSelect() {
        Task.detached(priority: .background) { [weak self] in
            let proc = Process()
            proc.executableURL = URL(fileURLWithPath: "/usr/bin/xcode-select")
            proc.arguments = ["-p"]
            let pipe = Pipe()
            proc.standardOutput = pipe
            proc.standardError = pipe
            try? proc.run()
            proc.waitUntilExit()
            let path = (String(data: pipe.fileHandleForReading.readDataToEndOfFile(), encoding: .utf8) ?? "")
                .trimmingCharacters(in: .whitespacesAndNewlines)
            await MainActor.run { self?.appendLog("[Xcode] xcode-select -p → \(path.isEmpty ? "(empty)" : path)\n") }
        }
    }
    #endif

    nonisolated private func macModel() -> String? {
        #if os(macOS)
        let proc = Process()
        proc.executableURL = URL(fileURLWithPath: "/usr/sbin/system_profiler")
        proc.arguments = ["SPHardwareDataType", "-json"]
        let pipe = Pipe()
        proc.standardOutput = pipe
        try? proc.run()
        proc.waitUntilExit()
        let data = pipe.fileHandleForReading.readDataToEndOfFile()
        guard let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
              let hw = (json["SPHardwareDataType"] as? [[String: Any]])?.first else { return nil }
        let name = hw["machine_name"] as? String ?? ""
        let chip = hw["chip_type"] as? String ?? hw["cpu_type"] as? String ?? ""
        return [name, chip].filter { !$0.isEmpty }.joined(separator: ", ")
        #else
        return nil
        #endif
    }

    #if !canImport(AppKit)
    private func logIOSSpecs() {
        Task.detached(priority: .background) { [weak self] in
            let sysName = UIDevice.current.systemName
            let sysVersion = UIDevice.current.systemVersion
            let memGB = ProcessInfo.processInfo.physicalMemory / 1_073_741_824
            let machine = MainViewModel.iOSMachineName()
            await MainActor.run {
                self?.appendLog("[Device] \(machine) · \(memGB) GB · \(sysName) \(sysVersion)\n")
            }
        }
    }

    nonisolated static func iOSMachineName() -> String {
        var info = utsname()
        uname(&info)
        return withUnsafeMutablePointer(to: &info.machine) {
            $0.withMemoryRebound(to: CChar.self, capacity: 1) { String(cString: $0) }
        }
    }

    private func scanLocalInstalledApps() -> [AppEntry] {
        guard let cls = NSClassFromString("LSApplicationWorkspace") else {
            appendLog("[iOS] LSApplicationWorkspace unavailable\n")
            return []
        }
        let wsSel = NSSelectorFromString("defaultWorkspace")
        guard cls.responds(to: wsSel),
              let ws = cls.perform(wsSel)?.takeUnretainedValue() as? NSObject else {
            appendLog("[iOS] defaultWorkspace unavailable\n")
            return []
        }
        let appsSel = NSSelectorFromString("allInstalledApplications")
        guard ws.responds(to: appsSel),
              let proxies = ws.perform(appsSel)?.takeUnretainedValue() as? [NSObject] else {
            appendLog("[iOS] allInstalledApplications unavailable\n")
            return []
        }
        appendLog("[iOS] Total installed: \(proxies.count)\n")
        var entries: [AppEntry] = []
        for proxy in proxies {
            guard let bundleID = proxy.value(forKey: "applicationIdentifier") as? String else { continue }
            guard !bundleID.hasPrefix("com.apple.") else { continue }
            let name = proxy.value(forKey: "localizedName") as? String ?? bundleID
            let category = proxy.value(forKey: "applicationCategory") as? String ?? ""
            guard category.lowercased().contains("game") else { continue }
            entries.append(AppEntry(internalName: bundleID, displayName: name, appPath: ""))
        }
        appendLog("[iOS] Games found: \(entries.count)\n")
        return entries
    }
    #endif

    private func checkMacOSVersion() {
        #if canImport(AppKit)
        let version = ProcessInfo.processInfo.operatingSystemVersion
        if version.majorVersion < 26 || (version.majorVersion == 26 && version.minorVersion < 2) {
            DispatchQueue.main.async {
                let alert = NSAlert()
                alert.messageText = "Unsupported macOS Version"
                alert.informativeText = "This app requires macOS Tahoe 26.2 or later.\nYou are running \(ProcessInfo.processInfo.operatingSystemVersionString)"
                alert.alertStyle = .critical
                alert.addButton(withTitle: "Quit")
                alert.runModal()
                NSApplication.shared.terminate(nil)
            }
        }
        #endif
    }

    // MARK: - Persistence
    func save() {
        var state = AppState()
        state.hudSettings = hudSettings
        state.analyticsOptIn = analyticsOptIn
        state.agreementsAccepted = agreementsAccepted
        state.commandHistory = commandHistory
        state.savedGames = savedGames
        state.hiddenApps = Array(hiddenApps)
        state.pinnedApps = Array(pinnedApps)
        state.firstDeviceScanNoticeShown = firstDeviceScanNoticeShown
        state.lastDeviceScan = lastDeviceScan
        state.libraryPanelOpen = showLibrary
        state.logPanelOpen = showLogPanel
        state.detectedBundleIDs = liveBundleIDs.filter { AppData.consoleBundleIDRenames[$0.value] != nil }
        state.detectedPathNames = livePathDisplayNames
        persistence.save(state)
    }

    // MARK: - Device list
    func restoreDevicePreview() {
        guard !lastDeviceScan.isEmpty else { return }
        devices = lastDeviceScan.sorted()
        if let first = devices.first, selectedDevice == nil {
            selectedDevice = first
        }
    }

    func listDevices() async {
        guard !isListingDevices else { return }
        isListingDevices = true
        defer { isListingDevices = false }

        #if canImport(AppKit)
        statusText = "Checking for devices…"
        do {
            let found = try await deviceService.listDevices(log: { [weak self] text in
                Task { @MainActor in self?.appendLog(text) }
            })

            await MainActor.run {
                devices = found
                lastDeviceScan = found
                if selectedDevice == nil || !found.contains(where: { $0.id == selectedDevice?.id }) {
                    selectedDevice = found.first
                }
                statusText = found.isEmpty ? "No devices found." : "Devices loaded."
                connectionHint = ""
                save()
                Task {
                    try? await Task.sleep(nanoseconds: 1_500_000_000)
                    await MainActor.run { if self.statusText == "Devices loaded." { self.statusText = "" } }
                }
            }
        } catch {
            await MainActor.run {
                statusText = "Device scan failed: \(error.localizedDescription)"
                appendLog("[devicectl] error: \(error.localizedDescription)\n")
            }
        }
        #else
        let name = UIDevice.current.name
        let id = UIDevice.current.identifierForVendor?.uuidString ?? "local"
        let model = UIDevice.current.model
        let local = Device(name: name, identifier: id, state: "available (local)", model: model)
        devices = [local]
        lastDeviceScan = [local]
        if selectedDevice == nil { selectedDevice = local }
        statusText = ""
        save()
        #endif
    }

    #if canImport(AppKit)
    func unpairDevice(_ device: Device) async {
        appendLog("[Unpair] Starting unpair device='\(device.name)' udid=\(device.identifier)\n")
        let output = await deviceService.unpairDevice(udid: device.identifier) { [weak self] text in
            Task { @MainActor in self?.appendLog(text) }
        }
        let trimmed = output.trimmingCharacters(in: .whitespacesAndNewlines)
        if trimmed.isEmpty {
            appendLog("[Unpair] Completed — no output\n")
        } else {
            let succeeded = trimmed.lowercased().contains("success") || trimmed.lowercased().contains("unpaired")
            appendLog("[Unpair] \(succeeded ? "Succeeded" : "Result") — \(trimmed.prefix(500))\n")
        }
        lastDeviceScan.removeAll { $0.identifier == device.identifier }
        save()
        await listDevices()
    }
    #endif

    // MARK: - App list state message (shown in the empty apps area)
    var appsStateTitle: String? = nil
    var appsStateMessage: String? = nil
    var appsStateIconFile: String? = nil  // filename (no ext) from assets/UI/Wireless State/

    // MARK: - App list
    func showApps(for device: Device) async {
        guard !isListingApps else { return }

        appendLog("[Device] showApps device='\(device.name)' model='\(device.model)'\n")

        let stateLower = device.state.lowercased()
        if stateLower.contains("unavailable") {
            appendLog("[Device] state=unavailable → Device Offline\n")
            apps = []
            selectedApp = nil
            appsStateTitle = "Device Offline"
            appsStateMessage = "Connect via USB or ensure it's on the same Wi-Fi, then press Show Running Games."
            appsStateIconFile = "Unavailable"
            return
        }
        if stateLower == "unsupported" {
            appendLog("[Device] state=unsupported → Device Not Supported\n")
            apps = []
            selectedApp = nil
            appsStateTitle = "Device Not Supported"
            appsStateMessage = "This device type cannot be used with FPS Logger."
            appsStateIconFile = "Unsupported"
            return
        }
        if stateLower.contains("pairing required") {
            appendLog("[Device] state='pairing required' → Device Not Paired (trust dialog needed)\n")
            apps = []
            selectedApp = nil
            appsStateTitle = "Device Not Paired"
            appsStateMessage = "Unlock → connect USB → Trust → replug, then press Show Running Games."
            appsStateIconFile = "available (pairing required)"
            return
        }

        isListingApps = true
        apps = []
        if pendingSelectInternalName == nil { selectedApp = nil }
        appsStateTitle = nil
        appsStateMessage = nil
        appsStateIconFile = nil

        defer { isListingApps = false }

        #if canImport(AppKit)
        let path = deviceService.devicectlPath
        let udid = device.identifier

        async let bundleTask = deviceService.fetchBundleMap(udid: udid, devicectlPath: path) { [weak self] text in
            Task { @MainActor in self?.appendLog(text) }
        }
        async let processTask = deviceService.listProcesses(udid: udid, devicectlPath: path) { [weak self] text in
            Task { @MainActor in self?.appendLog(text) }
        }

        let (bundles, processOutput) = await (bundleTask, processTask)

        if deviceService.isDeveloperModeDisabled(processOutput) {
            appendLog("[Device] Developer Mode disabled — raw output: \(processOutput.prefix(500))\n")
            appsStateTitle = "Developer Mode Disabled"
            appsStateMessage = "Enable it on your device: Settings → Privacy & Security → Developer Mode"
            appsStateIconFile = "Locked"
            return
        }

        if deviceService.isDeviceLocked(processOutput) {
            appendLog("[Device] Device locked — raw output: \(processOutput.prefix(500))\n")
            appsStateTitle = "Device Locked"
            appsStateMessage = "Unlock your device and try again."
            appsStateIconFile = "Locked"
            return
        }

        if deviceService.isPairingError(processOutput) {
            appendLog("[Device] Pairing error — raw output: \(processOutput.prefix(500))\n")
            appsStateTitle = "Device Not Paired"
            appsStateMessage = "Unlock → connect USB → Trust → replug, then press Show Running Games."
            appsStateIconFile = "available (pairing required)"
            return
        }

        if deviceService.isNotDiscoverableError(processOutput) {
            appendLog("[Device] Not discoverable — raw output: \(processOutput.prefix(500))\n")
            appsStateTitle = "Device Offline"
            appsStateMessage = "Connect via USB or ensure it's on the same Wi-Fi, then press Show Running Games."
            appsStateIconFile = "Unavailable"
            return
        }

        await MainActor.run {
            let (bundleMap, nameMap) = bundles
            liveBundleIDs = bundleMap
            liveDisplayNames.merge(nameMap) { _, new in new }
        }

        let parsed = parseAppsOutput(processOutput, device: device)

        if parsed.isEmpty {
            appendLog("[Apps] No games detected\n")
        } else {
            let names = parsed.map { $0.displayName }.joined(separator: ", ")
            appendLog("[Apps] \(parsed.count) game(s): \(names)\n")
        }

        appsHaveBeenFetched = true
        self.apps = parsed
        if let pending = pendingSelectInternalName {
            // Keep pending selection — cleared only when user taps Show Running Games.
            if let match = visibleApps.first(where: { $0.internalName == pending }) {
                selectedApp = match
            }
        } else {
            // Normal Show Running Games: auto-select first app
            if let first = visibleApps.first { selectedApp = first }
        }

        #else
        let machine = MainViewModel.iOSMachineName()
        appendLog("[iOS] \(machine) · scanning locally installed apps\n")
        let localApps = scanLocalInstalledApps()
        if localApps.isEmpty {
            appsStateTitle = "No Games Found"
            appsStateMessage = "No installed games were detected on this device."
            appsStateIconFile = "Unavailable"
        }
        apps = localApps
        appsHaveBeenFetched = true
        #endif
    }

    func fetchMissingIcons() {
        // Icons are an App Store feature; no-op in GitHub build
    }

    private func parseAppsOutput(_ output: String, device: Device) -> [AppEntry] {
        // Newer devicectl (Xcode 16+) outputs JSON — try that first
        let trimmed = output.trimmingCharacters(in: .whitespacesAndNewlines)
        if trimmed.hasPrefix("{"),
           let data = trimmed.data(using: .utf8),
           let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
           let result = json["result"] as? [String: Any],
           let processes = result["runningProcesses"] as? [[String: Any]] {
            let executables = processes.compactMap { $0["executable"] as? String }
            appendLog("[Processes] JSON format — \(executables.count) processes\n")
            return parseAppsFromExecutables(executables)
        }

        // Legacy text format: "515     /private/var/containers/Bundle/Application/..."
        let executables = output.components(separatedBy: "\n")
            .filter { $0.contains("Bundle/Application") }
            .compactMap { line -> String? in
                guard let range = line.range(of: "/private/var/containers") else { return nil }
                return String(line[range.lowerBound...]).trimmingCharacters(in: .whitespaces)
            }
        appendLog("[Processes] text format — \(executables.count) matching lines\n")
        return parseAppsFromExecutables(executables)
    }

    private func parseAppsFromExecutables(_ executables: [String]) -> [AppEntry] {
        var entries: [AppEntry] = []
        var seen = Set<String>()

        for executable in executables {
            let components = executable.components(separatedBy: "/")
            guard let appIdx = components.firstIndex(where: { $0.hasSuffix(".app") }) else { continue }
            let appBundle = components[appIdx]
            let internalName = appBundle.hasSuffix(".app") ? String(appBundle.dropLast(4)) : appBundle
            let appPath = components.prefix(appIdx + 1).joined(separator: "/")

            // Deduplicate by full container path — two apps with the same .app name
            // (e.g. two installs of Game.app) must both appear.
            if seen.contains(appPath) { continue }
            if AppData.filterOut.contains(appBundle) { continue }
            seen.insert(appPath)

            let displayName = livePathDisplayNames[appPath] ?? AppData.displayName(for: internalName, liveDisplayNames: liveDisplayNames)

            appLastDetected[internalName] = Date()
            entries.append(AppEntry(internalName: internalName, displayName: displayName, appPath: appPath))
        }
        return entries
    }

    // MARK: - Filtered / sorted app list
    var visibleApps: [AppEntry] {
        let hidden = hiddenApps
        var filtered = apps.filter { !hidden.contains($0.internalName) }

        let detected = Set(apps.map { $0.internalName })
        for name in pinnedApps where !detected.contains(name) && !hidden.contains(name) {
            let display = AppData.displayName(for: name, liveDisplayNames: liveDisplayNames)
            filtered.append(AppEntry(internalName: name, displayName: display, appPath: ""))
        }

        if !appSearchText.isEmpty {
            let term = appSearchText.lowercased()
            filtered = filtered.filter {
                $0.displayName.lowercased().contains(term) || $0.internalName.lowercased().contains(term)
            }
        }

        let sorted: [AppEntry]
        switch appSortMode {
        case .name:
            sorted = filtered.sorted { $0.displayName.lowercased() < $1.displayName.lowercased() }
        case .previouslyLaunched:
            let historyOrder = Dictionary(
                commandHistory.enumerated().compactMap { idx, entry -> (String, Int)? in
                    guard !entry.appPath.isEmpty else { return nil }
                    return (entry.appPath, idx)
                },
                uniquingKeysWith: { first, _ in first }
            )
            sorted = filtered.sorted { a, b in
                (historyOrder[a.appPath] ?? 9999) < (historyOrder[b.appPath] ?? 9999)
            }
        case .recentlyDetected:
            sorted = filtered.sorted { a, b in
                (appLastDetected[a.internalName] ?? .distantPast) > (appLastDetected[b.internalName] ?? .distantPast)
            }
        }

        let pinned_ = sorted.filter { pinnedApps.contains($0.internalName) }
        let unpinned = sorted.filter { !pinnedApps.contains($0.internalName) }
        return pinned_ + unpinned
    }

    enum AppSortMode: String, CaseIterable, Identifiable {
        var id: String { rawValue }
        case name               = "Name"
        case previouslyLaunched = "Previously Launched"
        case recentlyDetected   = "Recently Detected"
    }

    // MARK: - App launch
    func launchApp(device: Device, app: AppEntry) async {
        guard !isLaunching else { return }
        isLaunching = true
        isRunning = true
        statusText = "Launching \(app.displayName)…"

        let env = hudSettings.buildEnvironmentVariables()
        appendLog("[Launch] \(app.internalName) on \(device.name)\n")
        appendLog("[Env] \(env)\n")

        startPerfLogTimer(appName: app.displayName, deviceName: device.name)

        // Launch once to inject env vars, kill, then relaunch — Metal HUD requires this.
        let firstProc = deviceService.launchApp(
            udid: device.identifier,
            appBundlePath: app.appPath,
            environment: env,
            log: { [weak self] text in Task { @MainActor in self?.appendLog(text) } },
            onOutput: { _ in },
            onExit: { _ in }
        )
        currentLaunchProcess = firstProc

        try? await Task.sleep(nanoseconds: 3_000_000_000)
        firstProc.terminate()
        try? await Task.sleep(nanoseconds: 1_500_000_000)

        guard isLaunching else { return }  // user pressed Stop during the wait

        statusText = "Restarting \(app.displayName) with Metal HUD…"
        appendLog("[Launch] Restarting \(app.internalName) with Metal HUD\n")

        final class Once: @unchecked Sendable {
            private let lock = NSLock()
            private var fired = false
            func trigger() -> Bool {
                lock.lock(); defer { lock.unlock() }
                guard !fired else { return false }
                fired = true; return true
            }
        }
        let hudLogged = Once()
        let identityLogged = Once()

        let proc = deviceService.launchApp(
            udid: device.identifier,
            appBundlePath: app.appPath,
            environment: env,
            log: { [weak self] text in Task { @MainActor in self?.appendLog(text) } },
            onOutput: { [weak self] text in
                if text.contains("libMTLHud"), hudLogged.trigger() {
                    Task { @MainActor in self?.appendLog("[Launch] Metal HUD active\n") }
                }
                // Detect the real game name for generic-named apps (e.g. "Client")
                // by scanning the entitlements bundle ID printed early in the console log.
                if AppData.skipIconLookup.contains(app.internalName) {
                    for (bundleID, detectedName) in AppData.consoleBundleIDRenames {
                        guard text.contains(bundleID), identityLogged.trigger() else { continue }
                        Task { @MainActor [weak self] in
                            guard let self else { return }
                            appendLog("[Launch] Identified \(app.internalName) as \(detectedName)\n")
                            // Key by appPath, not internalName, so generic names like "Game" don't pollute other apps
                            livePathDisplayNames[app.appPath] = detectedName
                            save()
                            for idx in apps.indices where apps[idx].appPath == app.appPath {
                                apps[idx].displayName = detectedName
                            }
                            if selectedApp?.appPath == app.appPath {
                                selectedApp?.displayName = detectedName
                            }
                        }
                        break
                    }
                }
            },
            onExit: { [weak self] code in
                Task { @MainActor in
                    self?.isRunning = false
                    self?.isLaunching = false
                    self?.statusText = code == 0 ? "" : "App exited."
                }
            }
        )
        currentLaunchProcess = proc

        let entry = CommandHistoryEntry(
            command: "\(deviceService.devicectlPath) device process launch --device \(device.identifier) \(app.appPath)",
            udid: device.identifier,
            deviceDisplay: DeviceModels.clean(device.model),
            appPath: app.appPath,
            hud: hudSettings
        )
        commandHistory.insert(entry, at: 0)
        if commandHistory.count > 10 { commandHistory = Array(commandHistory.prefix(10)) }
        save()

        if analyticsOptIn == true {
            let iconURL = ""
            analytics.sendLaunchEvent(
                deviceModel: device.model,
                appName: app.displayName,
                connectionState: device.state,
                iconURL: iconURL,
                rawAppName: app.internalName,
                metricPreset: hudSettings.preset.rawValue
            )
        }
    }

    // MARK: - Periodic running timer (both builds — fires every 5 min while app is running)

    private func startPerfLogTimer(appName: String, deviceName: String) {
        perfLogTimer?.invalidate()
        let start = Date()
        perfLogTimer = Timer.scheduledTimer(withTimeInterval: 300, repeats: true) { [weak self] _ in
            Task { @MainActor [weak self] in
                guard let self, self.isRunning else { return }
                let elapsed = Int(Date().timeIntervalSince(start))
                self.appendLog("[Perf] \(appName) on \(deviceName) — running \(formatElapsed(elapsed))\n")
            }
        }
    }

    private func stopPerfLogTimer() {
        perfLogTimer?.invalidate()
        perfLogTimer = nil
    }

    func stopApp() {
        currentLaunchProcess?.terminate()
        currentLaunchProcess = nil
        stopPerfLogTimer()
        isRunning = false
        isLaunching = false
        statusText = ""
    }

    // MARK: - App management
    func hideApp(_ internalName: String) {
        hiddenApps.insert(internalName)
        save()
    }

    func unhideApp(_ internalName: String) {
        hiddenApps.remove(internalName)
        save()
    }

    func pinApp(_ internalName: String) {
        pinnedApps.insert(internalName)
        save()
    }

    func unpinApp(_ internalName: String) {
        pinnedApps.remove(internalName)
        save()
    }

    // MARK: - Saved Games
    func saveGame(name: String) {
        guard let device = selectedDevice, let app = selectedApp else { return }
        let game = SavedGame(
            name: name,
            deviceUDID: device.identifier,
            deviceName: device.name,
            appPath: app.appPath,
            appDisplayName: app.displayName,
            hudSettings: hudSettings
        )
        savedGames.insert(game, at: 0)
        save()
    }

    func deleteSavedGame(_ game: SavedGame) {
        savedGames.removeAll { $0.id == game.id }
        save()
    }

    func loadSavedGame(_ game: SavedGame) {
        hudSettings = game.hudSettings
        let base = URL(fileURLWithPath: game.appPath).lastPathComponent
        let internalName = base.hasSuffix(".app") ? String(base.dropLast(4)) : base
        selectedApp = AppEntry(internalName: internalName, displayName: game.appDisplayName, appPath: game.appPath)
        // Always set pending so any in-flight showApps doesn't auto-select over this choice.
        pendingSelectInternalName = internalName
        if let device = devices.first(where: { $0.identifier == game.deviceUDID }) {
            if device.identifier != selectedDevice?.identifier {
                selectedDevice = device
                Task { await showApps(for: device) }
            } else {
                selectedDevice = device
            }
        }
    }

    func loadHistoryEntry(_ entry: CommandHistoryEntry) {
        selectedHistoryEntry = entry
        selectedApp = nil
    }

    // MARK: - Update check
    func checkForUpdates() {
        Task.detached(priority: .background) { [weak self] in
            guard let self else { return }
            let apiURL = URL(string: "https://api.github.com/repos/mrmacright/Metal-HUD-Mobile-Config/releases/latest")!
            var request = URLRequest(url: apiURL)
            request.setValue("Metal-HUD-Mobile-Config", forHTTPHeaderField: "User-Agent")
            guard let (data, _) = try? await URLSession.shared.data(for: request),
                  let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                  let tag = json["tag_name"] as? String else { return }

            let latest = tag.trimmingCharacters(in: CharacterSet(charactersIn: "v"))
            let current = self.version.trimmingCharacters(in: CharacterSet(charactersIn: "v"))

            let latestParts = latest.split(separator: ".").compactMap { Int($0) }
            let currentParts = current.split(separator: ".").compactMap { Int($0) }

            guard latestParts.lexicographicallyPrecedes(currentParts) == false,
                  latestParts != currentParts else { return }

            await MainActor.run {
                #if canImport(AppKit)
                let alert = NSAlert()
                alert.messageText = "Update Available"
                alert.informativeText = "A new version of FPS Logger is available.\n\nCurrent: \(current)\nLatest: \(latest)\n\nWould you like to get the update on the App Store?"
                alert.alertStyle = .informational
                alert.addButton(withTitle: "Open App Store")
                alert.addButton(withTitle: "Later")
                if alert.runModal() == .alertFirstButtonReturn {
                    NSWorkspace.shared.open(URL(string: "https://apps.apple.com/app/id6763967836")!)
                }
                #endif
            }
        }
    }
}

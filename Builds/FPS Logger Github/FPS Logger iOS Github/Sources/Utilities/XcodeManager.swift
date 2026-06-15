#if canImport(AppKit)
import Foundation
import AppKit

@MainActor
final class XcodeManager {
    static let shared = XcodeManager()

    let requiredVersion = "26.5"

    private var setupDone = false
    private var setupFailed = false

    private init() {}

    // MARK: - Detection

    func findXcodeApp() -> String? {
        let fm = FileManager.default

        // 1. mdfind — finds Xcode regardless of install location.
        let mdfindResult = shell("/usr/bin/mdfind", args: ["kMDItemCFBundleIdentifier == 'com.apple.dt.Xcode'"])
        for path in mdfindResult.components(separatedBy: "\n").map({ $0.trimmingCharacters(in: .whitespacesAndNewlines) }).filter({ !$0.isEmpty }) {
            var isDir: ObjCBool = false
            if fm.fileExists(atPath: path, isDirectory: &isDir), isDir.boolValue { return path }
        }

        // 2. Scan /Applications and ~/Applications directly (covers Spotlight-disabled volumes).
        let home = FileManager.default.homeDirectoryForCurrentUser.path
        for appsDir in ["/Applications", "\(home)/Applications"] {
            let apps = (try? fm.contentsOfDirectory(atPath: appsDir))?.sorted() ?? []
            for app in apps where app.lowercased().hasPrefix("xcode") && app.hasSuffix(".app") {
                let path = "\(appsDir)/\(app)"
                var isDir: ObjCBool = false
                if fm.fileExists(atPath: path, isDirectory: &isDir), isDir.boolValue { return path }
            }
        }

        // 3. Derive from xcode-select -p (e.g. /Applications/Xcode.app/Contents/Developer → /Applications/Xcode.app).
        let xcsResult = shell("/usr/bin/xcode-select", args: ["-p"]).trimmingCharacters(in: .whitespacesAndNewlines)
        if !xcsResult.isEmpty && !xcsResult.contains("error:") {
            // Strip /Contents/Developer suffix to get .app path
            let components = xcsResult.components(separatedBy: "/Contents/Developer")
            if let appPath = components.first, appPath.hasSuffix(".app") {
                var isDir: ObjCBool = false
                if fm.fileExists(atPath: appPath, isDirectory: &isDir), isDir.boolValue { return appPath }
            }
        }

        // 4. find command — deep search under /Applications as last resort.
        let findResult = shell("/usr/bin/find", args: ["/Applications", "-maxdepth", "2", "-name", "Xcode*.app", "-type", "d"])
        for path in findResult.components(separatedBy: "\n").map({ $0.trimmingCharacters(in: .whitespacesAndNewlines) }).filter({ !$0.isEmpty }) {
            var isDir: ObjCBool = false
            if fm.fileExists(atPath: path, isDirectory: &isDir), isDir.boolValue { return path }
        }

        return nil
    }

    func isXcodeInstalled() -> Bool {
        findXcodeApp() != nil
    }

    func xcodeVersion() -> String? {
        guard let xcodePath = findXcodeApp() else { return nil }
        let xcodebuild = "\(xcodePath)/Contents/Developer/usr/bin/xcodebuild"

        // Try xcodebuild -version
        let result = shell(xcodebuild, args: ["-version"])
        let combined = result
        if let match = combined.range(of: #"Xcode\s+(\d+(?:\.\d+)*)"#, options: .regularExpression) {
            let versionStr = String(combined[match])
            return versionStr.components(separatedBy: .whitespaces).last
        }

        // Fallback: PlistBuddy
        let plist = "\(xcodePath)/Contents/Info.plist"
        let plistResult = shell("/usr/libexec/PlistBuddy", args: ["-c", "Print CFBundleShortVersionString", plist])
        let version = plistResult.trimmingCharacters(in: .whitespacesAndNewlines)
        return version.isEmpty ? nil : version
    }

    func isUsingCommandLineToolsOnly() -> Bool {
        let result = shell("/usr/bin/xcode-select", args: ["-p"])
        return result.contains("CommandLineTools")
    }

    func versionTuple(_ version: String) -> [Int] {
        version.components(separatedBy: ".").compactMap { Int($0) }
    }

    // MARK: - Setup

    func checkAndSetup(vm: MainViewModel) {
        Task {
            // Retry detection for up to 30 seconds — Spotlight may not have indexed
            // Xcode yet immediately after install or first launch.
            var installed = isXcodeInstalled()
            if !installed {
                vm.appendLog("[Xcode] Xcode not found on first check — retrying for up to 30s\n")
                for _ in 0..<6 {
                    try? await Task.sleep(nanoseconds: 5_000_000_000)
                    installed = isXcodeInstalled()
                    if installed { break }
                }
            }
            vm.appendLog("[Xcode] checkAndSetup: installed=\(installed) clt_only=\(isUsingCommandLineToolsOnly())\n")
            guard installed else {
                vm.appendLog("[Xcode] Xcode.app not found — showing Xcode Required overlay, continuing to poll\n")
                vm.xcodeRequired = true
                pollForXcodeInstall(vm: vm)
                return
            }
            let version = xcodeVersion()
            vm.appendLog("[Xcode] detected=\(version ?? "nil") required=\(requiredVersion)\n")
            guard let version = version else {
                vm.appendLog("[Xcode] Could not read Xcode version — showing overlay\n")
                vm.xcodeRequired = true
                return
            }
            let current = versionTuple(version)
            let required = versionTuple(requiredVersion)
            if current.lexicographicallyPrecedes(required) {
                vm.appendLog("[Xcode] Version \(version) < required \(requiredVersion) — showing overlay\n")
                vm.xcodeRequired = true
                return
            }
            vm.appendLog("[Xcode] Version OK — running ensureXcodeReady\n")
            vm.xcodeRequired = false
            ensureXcodeReady(log: { msg in vm.appendLog(msg) })
            DeviceService.shared.refreshDevicectl()
            pollForXcodeVersion(vm: vm)
        }
    }

    func ensureXcodeReady(log: @escaping (String) -> Void) {
        log("[Xcode] ensure_xcode_ready: starting\n")
        guard let xcodePath = findXcodeApp() else {
            log("[Xcode] No Xcode.app found — skipping setup\n")
            return
        }
        log("[Xcode] Found Xcode at: \(xcodePath)\n")

        let isSandboxed = ProcessInfo.processInfo.environment["APP_SANDBOX_CONTAINER_ID"] != nil
        let developerDir = "\(xcodePath)/Contents/Developer"
        let xcodebuild = "\(developerDir)/usr/bin/xcodebuild"

        if !isSandboxed {
            if !isLicenseAccepted(xcodebuild: xcodebuild, log: log) {
                log("[Xcode] License not accepted — running setup as admin\n")
                runAdminSetup(xcodebuild: xcodebuild, developerDir: developerDir, log: log)
            }
            // Set xcode-select
            _ = shell("/usr/bin/xcode-select", args: ["-s", developerDir])
            log("[Xcode] xcode-select → \(developerDir)\n")
        }

        // Check first launch status
        let firstLaunchResult = Process()
        firstLaunchResult.executableURL = URL(fileURLWithPath: xcodebuild)
        firstLaunchResult.arguments = ["-checkFirstLaunchStatus"]
        firstLaunchResult.standardOutput = FileHandle.nullDevice
        firstLaunchResult.standardError = FileHandle.nullDevice
        try? firstLaunchResult.run()
        firstLaunchResult.waitUntilExit()

        log("[Xcode] checkFirstLaunchStatus returncode=\(firstLaunchResult.terminationStatus)\n")
        if firstLaunchResult.terminationStatus != 0 {
            log("[Xcode] Setup needed — running admin setup\n")
            runAdminSetup(xcodebuild: xcodebuild, developerDir: developerDir, log: log)
        }

    }

    private func isLicenseAccepted(xcodebuild: String, log: (String) -> Void) -> Bool {
        let output = shell(xcodebuild, args: ["-version"])
        let lower = output.lowercased()
        if lower.contains("license") {
            log("[Xcode] License not accepted\n")
            return false
        }
        return true
    }

    private func runAdminSetup(xcodebuild: String, developerDir: String, log: (String) -> Void) {
        guard !setupDone, !setupFailed else { return }

        let scriptLines = [
            "#!/bin/bash",
            "\"\(xcodebuild)\" -license accept",
            "\"\(xcodebuild)\" -runFirstLaunch",
            "xcode-select -s \"\(developerDir)\"",
        ]
        let script = scriptLines.joined(separator: "\n")

        let tmpURL = FileManager.default.temporaryDirectory.appendingPathComponent("fps-logger-xcode-setup.sh")
        do {
            try (script + "\n").write(to: tmpURL, atomically: true, encoding: .utf8)
            try FileManager.default.setAttributes([.posixPermissions: 0o755], ofItemAtPath: tmpURL.path)
        } catch {
            log("[Xcode] admin setup script write error: \(error)\n")
            setupFailed = true
            return
        }

        let escaped = tmpURL.path.replacingOccurrences(of: "\"", with: "\\\"")
        let proc = Process()
        proc.executableURL = URL(fileURLWithPath: "/usr/bin/osascript")
        proc.arguments = ["-e", "do shell script \"bash \\\"\(escaped)\\\"\" with administrator privileges"]
        let pipe = Pipe()
        proc.standardOutput = pipe
        proc.standardError = pipe
        do {
            try proc.run()
            proc.waitUntilExit()
        } catch {
            log("[Xcode] admin setup error: \(error)\n")
            setupFailed = true
            return
        }
        let output = String(data: pipe.fileHandleForReading.readDataToEndOfFile(), encoding: .utf8) ?? ""
        log("[Xcode] admin setup returncode=\(proc.terminationStatus)\n")
        if proc.terminationStatus == 0 {
            setupDone = true
            log("[Xcode] admin setup succeeded\n")
        } else {
            setupFailed = true
            log("[Xcode] admin setup failed: \(output.prefix(200))\n")
        }
        try? FileManager.default.removeItem(at: tmpURL)
    }

    // MARK: - Install polling

    /// Keeps checking in the background after the initial retry window expires.
    /// Once Xcode appears, runs full setup and dismisses the overlay.
    private func pollForXcodeInstall(vm: MainViewModel) {
        Task {
            while true {
                try? await Task.sleep(nanoseconds: 5_000_000_000)
                guard isXcodeInstalled() else { continue }
                vm.appendLog("[Xcode] Xcode detected after install — running setup\n")
                guard let version = xcodeVersion() else { continue }
                let current = versionTuple(version)
                let required = versionTuple(requiredVersion)
                guard !current.lexicographicallyPrecedes(required) else {
                    vm.appendLog("[Xcode] Version \(version) < required \(requiredVersion) — still waiting\n")
                    continue
                }
                vm.appendLog("[Xcode] Version OK — dismissing overlay\n")
                vm.xcodeRequired = false
                ensureXcodeReady(log: { msg in vm.appendLog(msg) })
                DeviceService.shared.refreshDevicectl()
                pollForXcodeVersion(vm: vm)
                break
            }
        }
    }

    // MARK: - Version polling

    private func pollForXcodeVersion(vm: MainViewModel) {
        Task {
            while true {
                try? await Task.sleep(nanoseconds: 3_000_000_000)
                guard isXcodeInstalled() else { continue }
                guard let version = xcodeVersion() else { continue }
                let current = versionTuple(version)
                let required = versionTuple(requiredVersion)
                if !current.lexicographicallyPrecedes(required) {
                    vm.xcodeRequired = false
                    break
                }
            }
        }
    }

    // MARK: - Uninstall

    // MARK: - Script builders (called by UninstallView)

    func buildBasicUninstallScript() -> String {
        [
            "#!/bin/bash",
            "rm -rf /Applications/Xcode.app",
            "rm -rf /Applications/Xcode-beta.app",
            "rm -rf /Library/Developer/CommandLineTools",
            "xcode-select --reset 2>/dev/null || true",
        ].joined(separator: "\n") + "\n"
    }

    func buildFullUninstallScript() -> String {
        let home = FileManager.default.homeDirectoryForCurrentUser.path
        return [
            "#!/bin/bash",
            "rm -rf /Applications/Xcode.app",
            "rm -rf /Applications/Xcode-beta.app",
            "rm -rf /Library/Developer/CommandLineTools",
            "rm -rf /Library/Developer",
            "find /System/Library/Receipts -maxdepth 1 \\( -name 'com.apple.pkg.CLTools_*' -o -name 'com.apple.pkg.DeveloperToolsCLI.*' \\) -exec rm -rf {} + 2>/dev/null || true",
            "xcode-select --reset 2>/dev/null || true",
            "rm -rf '\(home)/Library/Developer'",
            "rm -rf '\(home)/Library/Caches/com.apple.dt.Xcode'",
            "rm -f '\(home)/Library/Preferences/com.apple.dt.Xcode.plist'",
        ].joined(separator: "\n") + "\n"
    }

    nonisolated func runUninstallScript(_ script: String, completion: @escaping (Bool) -> Void) {
        let tmpURL = FileManager.default.temporaryDirectory.appendingPathComponent("fps-logger-uninstall.sh")
        do {
            try script.write(to: tmpURL, atomically: true, encoding: .utf8)
            try FileManager.default.setAttributes([.posixPermissions: 0o755], ofItemAtPath: tmpURL.path)
        } catch {
            completion(false)
            return
        }
        let escaped = tmpURL.path.replacingOccurrences(of: "\"", with: "\\\"")
        let proc = Process()
        proc.executableURL = URL(fileURLWithPath: "/usr/bin/osascript")
        proc.arguments = ["-e", "do shell script \"bash \\\"\(escaped)\\\"\" with administrator privileges"]
        try? proc.run()
        proc.waitUntilExit()
        try? FileManager.default.removeItem(at: tmpURL)
        completion(proc.terminationStatus == 0)
    }

    // MARK: - Shell helper

    @discardableResult
    private func shell(_ executable: String, args: [String]) -> String {
        let proc = Process()
        proc.executableURL = URL(fileURLWithPath: executable)
        proc.arguments = args
        let pipe = Pipe()
        proc.standardOutput = pipe
        proc.standardError = pipe
        try? proc.run()
        proc.waitUntilExit()
        return String(data: pipe.fileHandleForReading.readDataToEndOfFile(), encoding: .utf8) ?? ""
    }
}
#endif

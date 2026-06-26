import Foundation

enum DeviceServiceError: LocalizedError {
    case devicectlNotFound
    case commandFailed(String)

    var errorDescription: String? {
        switch self {
        case .devicectlNotFound:
            return "devicectl not found. Please ensure Xcode is installed."
        case .commandFailed(let msg):
            return msg
        }
    }
}

@MainActor
final class DeviceService {
    static let shared = DeviceService()

    nonisolated(unsafe) var devicectlPath: String = "/usr/bin/devicectl"

    private init() {
        // Don't cache nil at startup — XcodeManager.checkAndSetup will call
        // refreshDevicectl() once Xcode is confirmed present.
        let (path, _) = DeviceService.findDevicectlWithLog()
        devicectlPath = path ?? "devicectl"
    }

    func refreshDevicectl() {
        let (path, _) = DeviceService.findDevicectlWithLog()
        if let path { devicectlPath = path }
    }

    // MARK: - devicectl discovery

    static func findDevicectlWithLog() -> (String?, String) {
        var log = ""
        #if canImport(AppKit)
        let fm = FileManager.default

        // 1. mdfind — finds Xcode regardless of install location, no CLT dialog.
        let mdfindResult = shellSync("/usr/bin/mdfind", args: ["kMDItemCFBundleIdentifier == 'com.apple.dt.Xcode'"])
        let mdfindPaths = mdfindResult.components(separatedBy: "\n").map { $0.trimmingCharacters(in: .whitespacesAndNewlines) }.filter { !$0.isEmpty }
        log += "[devicectl] mdfind Xcode paths: \(mdfindPaths.isEmpty ? "(none)" : mdfindPaths.joined(separator: ", "))\n"
        for xcodePath in mdfindPaths {
            let candidate = xcodePath + "/Contents/Developer/usr/bin/devicectl"
            if fm.fileExists(atPath: candidate) {
                log += "[devicectl] found via mdfind: \(candidate)\n"
                return (candidate, log)
            }
        }

        // 2. Known fixed paths.
        for path in [
            "/Applications/Xcode.app/Contents/Developer/usr/bin/devicectl",
            "/Applications/Xcode-beta.app/Contents/Developer/usr/bin/devicectl",
        ] {
            log += "[devicectl] checking: \(path) → \(fm.fileExists(atPath: path) ? "found" : "missing")\n"
            if fm.fileExists(atPath: path) { return (path, log) }
        }

        // 3. Scan /Applications and ~/Applications for any Xcode*.app.
        let home = FileManager.default.homeDirectoryForCurrentUser.path
        for appsDir in ["/Applications", "\(home)/Applications"] {
            let apps = (try? fm.contentsOfDirectory(atPath: appsDir))?.sorted() ?? []
            for app in apps where app.lowercased().hasPrefix("xcode") && app.hasSuffix(".app") {
                let candidate = "\(appsDir)/\(app)/Contents/Developer/usr/bin/devicectl"
                if fm.fileExists(atPath: candidate) {
                    log += "[devicectl] found via /Applications scan: \(candidate)\n"
                    return (candidate, log)
                }
            }
        }

        // 4. Derive from xcode-select -p.
        let xcsResult = shellSync("/usr/bin/xcode-select", args: ["-p"]).trimmingCharacters(in: .whitespacesAndNewlines)
        if !xcsResult.isEmpty && !xcsResult.contains("error:") {
            let candidate = "\(xcsResult)/usr/bin/devicectl"
            if fm.fileExists(atPath: candidate) {
                log += "[devicectl] found via xcode-select: \(candidate)\n"
                return (candidate, log)
            }
        }

        // 5. find command as last resort.
        let findResult = shellSync("/usr/bin/find", args: ["/Applications", "-maxdepth", "3", "-name", "devicectl", "-type", "f"])
        for path in findResult.components(separatedBy: "\n").map({ $0.trimmingCharacters(in: .whitespacesAndNewlines) }).filter({ !$0.isEmpty }) {
            if fm.fileExists(atPath: path) {
                log += "[devicectl] found via find: \(path)\n"
                return (path, log)
            }
        }

        log += "[devicectl] not found\n"
        return (nil, log)
        #else
        // iOS: devicectl lives on macOS, not on device
        return (nil, log)
        #endif
    }

    func findDevicectl() -> String? {
        DeviceService.findDevicectlWithLog().0
    }

    // MARK: - Device list

    struct ParsedDevice {
        let name: String
        let identifier: String
        var state: String
        let model: String
    }

    func listDevices(log: @escaping (String) -> Void) async throws -> [Device] {
        guard FileManager.default.fileExists(atPath: devicectlPath) else {
            throw DeviceServiceError.devicectlNotFound
        }

        var rawOutput = ""
        for attempt in 1...3 {
            log("[devicectl] attempt=\(attempt) path=\(devicectlPath)\n")
            rawOutput = await shellAsync(devicectlPath, args: ["list", "devices"])

            if rawOutput.isEmpty {
                log("[devicectl] output: (empty)\n")
            } else {
                log("[devicectl] output: \(String(rawOutput.prefix(3000)))\n")
            }

            if !rawOutput.isEmpty && !isDevicePreparing(rawOutput) {
                break
            }
            try? await Task.sleep(nanoseconds: 2_000_000_000)
        }

        return parseDeviceList(rawOutput, log: log)
    }

    private func isDevicePreparing(_ output: String) -> Bool {
        if output.isEmpty { return true }
        let lower = output.lowercased()
        if lower.contains("identifier") && lower.contains("state") && lower.contains("model") {
            return false
        }
        return lower.contains("waiting for device")
            || lower.contains("connecting")
            || lower.contains("acquired tunnel connection")
    }

    private func parseDeviceList(_ rawOutput: String, log: (String) -> Void) -> [Device] {
        let uuidPattern = try! NSRegularExpression(pattern: #"^[A-F0-9-]{8,}$"#, options: .caseInsensitive)

        let contentLines = rawOutput.components(separatedBy: "\n").filter { line in
            let stripped = line.trimmingCharacters(in: .whitespaces)
            if stripped.isEmpty { return false }
            if stripped.hasPrefix("Failed to load provisioning") { return false }
            if stripped.hasPrefix("`devicectl manage create`") { return false }
            if stripped.hasPrefix("Name") && stripped.contains("Identifier") { return false }
            if Set(stripped).isSubset(of: ["-", " "]) { return false }
            return true
        }

        var devices: [Device] = []
        for line in contentLines {
            let parts = line.trimmingCharacters(in: .whitespaces)
                .components(separatedBy: try! NSRegularExpression(pattern: #"\s{2,}"#))
            guard parts.count >= 5 else { continue }

            let rawName = parts[0].trimmingCharacters(in: .whitespaces)
            let name = fixSpecialChars(rawName)
            let identifier = parts[2].trimmingCharacters(in: .whitespaces)
            var state = parts[3].trimmingCharacters(in: .whitespaces)
            let rawModel = parts[4].trimmingCharacters(in: .whitespaces)
            let model = DeviceModels.clean(rawModel)

            let range = NSRange(identifier.startIndex..., in: identifier)
            guard uuidPattern.firstMatch(in: identifier, range: range) != nil else { continue }

            let normalized = DeviceModels.clean(model)
            if normalized.hasPrefix("Apple Watch") || normalized.hasPrefix("Watch") { state = "unsupported" }
            if rawModel.contains("AppleTV5,3") || model.contains("Apple TV (4th generation)") {
                state = "unsupported"
            }

            devices.append(Device(name: name, identifier: identifier, state: state, model: model))
        }

        log("[devicectl] parsed \(devices.count) device(s)\n")
        return devices.sorted()
    }

    private func fixSpecialChars(_ s: String) -> String {
        let inchFixed = s.replacingOccurrences(of: #"(\d)\?"#, with: "$1\"", options: .regularExpression)
        return inchFixed.replacingOccurrences(of: "?", with: "'")
    }

    // MARK: - App list

    struct BundleInfo {
        var bundleID: String
        var displayName: String
    }

    nonisolated func fetchBundleMap(udid: String, devicectlPath: String, log: @escaping (String) -> Void) async -> ([String: String], [String: String]) {
        let tmp = FileManager.default.temporaryDirectory.appendingPathComponent("metal-hud-apps.json")
        defer { try? FileManager.default.removeItem(at: tmp) }

        let args = ["device", "info", "apps", "--device", udid, "--include-removable-apps", "-j", tmp.path]

        let output = await shellAsync(devicectlPath, args: args, timeout: 25)
        _ = output

        guard let data = try? Data(contentsOf: tmp),
              let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
              let result = json["result"] as? [String: Any],
              let apps = result["apps"] as? [[String: Any]] else {
            log("[BundleMap] devicectl apps failed or no data\n")
            return ([:], [:])
        }

        var bundleMap: [String: String] = [:]
        var nameMap: [String: String] = [:]
        for app in apps {
            guard let urlStr = app["url"] as? String,
                  let bundleID = app["bundleIdentifier"] as? String else { continue }
            let basename = URL(string: urlStr)?.lastPathComponent ?? ""
            if basename.hasSuffix(".app") {
                let internal_ = String(basename.dropLast(4))
                bundleMap[internal_] = bundleID
                if let displayName = app["name"] as? String, !displayName.isEmpty {
                    nameMap[internal_] = displayName
                }
            }
        }
        return (bundleMap, nameMap)
    }

    nonisolated func listProcesses(udid: String, devicectlPath: String, log: @escaping (String) -> Void) async -> String {
        log("[CMD] \(devicectlPath) device info processes --device \(udid)\n")
        let output = await shellAsync(devicectlPath, args: ["device", "info", "processes", "--device", udid], timeout: 25)
        if output.isEmpty {
            log("[Processes] Command returned empty output\n")
        } else {
            log("[Processes] \(output.count) chars: \(String(output.prefix(300)))\n")
        }
        return output
    }

    // MARK: - Force-kill remote process

    nonisolated func killApp(udid: String, appBundlePath: String, log: @escaping @Sendable (String) -> Void) async {
        let processOutput = await shellAsync(devicectlPath,
            args: ["device", "info", "processes", "--device", udid],
            timeout: 5)
        guard !processOutput.isEmpty else {
            log("[Kill] Process list returned empty — cannot force-kill\n")
            return
        }
        for line in processOutput.components(separatedBy: "\n") {
            guard line.contains(appBundlePath) else { continue }
            let parts = line.trimmingCharacters(in: .whitespaces)
                .components(separatedBy: .whitespaces)
            guard let pidStr = parts.first, let pid = Int(pidStr), pid > 0 else { continue }
            log("[Kill] SIGKILL → PID \(pid) (\(URL(fileURLWithPath: appBundlePath).lastPathComponent))\n")
            _ = await shellAsync(devicectlPath,
                args: ["device", "process", "signal",
                       "--signal", "SIGKILL", "--pid", String(pid), "--device", udid],
                timeout: 5)
            return
        }
        log("[Kill] No running process found for \(URL(fileURLWithPath: appBundlePath).lastPathComponent)\n")
    }

    // MARK: - App launch

    #if os(macOS)
    func launchApp(
        udid: String,
        appBundlePath: String,
        environment: [String: String],
        log: @escaping @Sendable (String) -> Void,
        onOutput: @escaping @Sendable (String) -> Void,
        onExit: @escaping @Sendable (Int32) -> Void
    ) -> PlatformProcess {
        let envData = try? JSONSerialization.data(withJSONObject: environment)
        let envJSON = envData.flatMap { String(data: $0, encoding: .utf8) } ?? "{}"

        let args = ["device", "process", "launch",
                    "--device", udid,
                    "-e", envJSON,
                    "--console",
                    appBundlePath]

        log("[CMD] \(devicectlPath) \(args.joined(separator: " "))\n")

        let proc = Process()
        proc.executableURL = URL(fileURLWithPath: devicectlPath)
        proc.arguments = args

        let pipe = Pipe()
        proc.standardOutput = pipe
        proc.standardError = pipe

        pipe.fileHandleForReading.readabilityHandler = { handle in
            let data = handle.availableData
            guard !data.isEmpty, let text = String(data: data, encoding: .utf8) else { return }
            log(text)
            onOutput(text)
        }

        proc.terminationHandler = { p in
            pipe.fileHandleForReading.readabilityHandler = nil
            onExit(p.terminationStatus)
        }

        do {
            try proc.run()
        } catch {
            log("[Launch] Failed: \(error)\n")
            onExit(-1)
        }
        return proc
    }
    #else
    func launchApp(
        udid: String,
        appBundlePath: String,
        environment: [String: String],
        log: @escaping @Sendable (String) -> Void,
        onOutput: @escaping @Sendable (String) -> Void,
        onExit: @escaping @Sendable (Int32) -> Void
    ) -> PlatformProcess {
        onExit(-1)
        return PlatformProcess()
    }
    #endif

    // MARK: - Unpair

    func unpairDevice(udid: String, log: @escaping (String) -> Void) async -> String {
        log("[CMD] \(devicectlPath) manage unpair --device \(udid)\n")
        return await shellAsync(devicectlPath, args: ["manage", "unpair", "--device", udid])
    }

    // MARK: - Pairing error detection

    func isDeveloperModeDisabled(_ output: String) -> Bool {
        output.contains("Developer Mode is disabled")
    }

    func isPairingError(_ output: String) -> Bool {
        let lower = output.lowercased()
        return lower.contains("must be paired") || lower.contains("coredeviceerror error 2")
    }

    func isNotDiscoverableError(_ output: String) -> Bool {
        let lower = output.lowercased()
        return lower.contains("coredeviceservice was unable to locate a device")
            || lower.contains("coredeviceerror error 1011")
    }

    func isDeviceLocked(_ output: String) -> Bool {
        let lower = output.lowercased()
        return lower.contains("device is locked")
            || lower.contains("device was still locked")
            || lower.contains("has not been unlocked recently")
            || lower.contains("devicelocked")
            || lower.contains("kamdmobileimagemounterdevicelocked")
    }

    // MARK: - Shell helpers

    @discardableResult
    static func shellSync(_ executable: String, args: [String]) -> String {
        #if os(macOS)
        let proc = Process()
        proc.executableURL = URL(fileURLWithPath: executable)
        proc.arguments = args
        let pipe = Pipe()
        proc.standardOutput = pipe
        proc.standardError = pipe
        try? proc.run()
        proc.waitUntilExit()
        return String(data: pipe.fileHandleForReading.readDataToEndOfFile(), encoding: .utf8) ?? ""
        #else
        return ""
        #endif
    }

    nonisolated func shellAsync(_ executable: String, args: [String], timeout: TimeInterval = 60) async -> String {
        #if os(macOS)
        await withCheckedContinuation { continuation in
            DispatchQueue.global(qos: .userInitiated).async {
                let proc = Process()
                proc.executableURL = URL(fileURLWithPath: executable)
                proc.arguments = args
                let outPipe = Pipe()
                let errPipe = Pipe()
                proc.standardOutput = outPipe
                proc.standardError = errPipe

                let timeoutTimer = DispatchSource.makeTimerSource(queue: DispatchQueue.global())
                timeoutTimer.schedule(deadline: .now() + timeout)
                timeoutTimer.setEventHandler { proc.terminate() }
                timeoutTimer.resume()

                do {
                    try proc.run()
                } catch {
                    timeoutTimer.cancel()
                    continuation.resume(returning: "")
                    return
                }

                nonisolated(unsafe) var outData = Data()
                nonisolated(unsafe) var errData = Data()
                let group = DispatchGroup()
                group.enter()
                DispatchQueue.global(qos: .userInitiated).async {
                    outData = outPipe.fileHandleForReading.readDataToEndOfFile()
                    group.leave()
                }
                group.enter()
                DispatchQueue.global(qos: .userInitiated).async {
                    errData = errPipe.fileHandleForReading.readDataToEndOfFile()
                    group.leave()
                }

                proc.waitUntilExit()
                group.wait()
                timeoutTimer.cancel()

                let combined = errData + outData
                let result = String(data: combined, encoding: .utf8)
                    ?? String(data: combined, encoding: .isoLatin1)
                    ?? ""
                continuation.resume(returning: result)
            }
        }
        #else
        return ""
        #endif
    }
}

// MARK: - String split by regex helper
private extension String {
    func components(separatedBy regex: NSRegularExpression) -> [String] {
        let nsStr = self as NSString
        let range = NSRange(location: 0, length: nsStr.length)
        var parts: [String] = []
        var lastEnd = 0
        for match in regex.matches(in: self, range: range) {
            let partRange = NSRange(location: lastEnd, length: match.range.location - lastEnd)
            parts.append(nsStr.substring(with: partRange))
            lastEnd = match.range.location + match.range.length
        }
        parts.append(nsStr.substring(from: lastEnd))
        return parts
    }
}

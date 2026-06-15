import SwiftUI
#if canImport(AppKit)
import AppKit
#endif

struct AppListView: View {
    @Environment(MainViewModel.self) private var vm

    var body: some View {
        @Bindable var vm = vm

        VStack(spacing: 0) {
            // Header
            HStack(spacing: 8) {
                Text(vm.selectedDevice.map { "Apps on \(DeviceModels.clean($0.model))" } ?? "Running Apps")
                    .font(.system(size: 13, weight: .semibold))
                    .lineLimit(1)

                let unsupportedModels: Set<String> = [
                    "iPhone XS", "iPhone XS Max", "iPhone XS Max Global", "iPhone XR",
                    "iPad (6th generation)", "iPad (7th generation)",
                    "iPad Pro (10.5-inch)", "iPad Pro (12.9-inch) (2nd generation)"
                ]
                if unsupportedModels.contains(vm.selectedDevice?.model ?? "") {
                    Text("New Metal HUD unsupported")
                        .font(.system(size: 11))
                        .foregroundStyle(.secondary)
                        .padding(.horizontal, 6)
                        .padding(.vertical, 2)
                        .background(Color.secondary.opacity(0.12))
                        .clipShape(RoundedRectangle(cornerRadius: 4))
                }

                Spacer()

                if vm.isListingApps {
                    ProgressView().controlSize(.mini)
                }

                // Sort picker
                Picker("Sort", selection: $vm.appSortMode) {
                    ForEach(MainViewModel.AppSortMode.allCases) { mode in
                        Text(mode.rawValue).tag(mode)
                    }
                }
                .labelsHidden()
                .frame(width: 160)
                .font(.system(size: 12))

                // Library toggle
                Button {
                    vm.showLibrary.toggle()
                    vm.save()
                } label: {
                    Label("Library", systemImage: "sidebar.right")
                        .labelStyle(.iconOnly)
                }
                .help("Toggle Library")

            }
            .padding(.horizontal, 14)
            .padding(.vertical, 8)
            .background(Color.controlBg)

            Divider()

            // Search
            HStack {
                Image(systemName: "magnifyingglass")
                    .foregroundStyle(.secondary)
                    .font(.system(size: 12))
                TextField("Search apps…", text: $vm.appSearchText)
                    .textFieldStyle(.plain)
                    .font(.system(size: 13))
                if !vm.appSearchText.isEmpty {
                    Button {
                        vm.appSearchText = ""
                    } label: {
                        Image(systemName: "xmark.circle.fill")
                            .foregroundStyle(.secondary)
                    }
                    .buttonStyle(.plain)
                }
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 6)
            .background(Color.controlBg)

            Divider()

            // App list — capped at 12 rows so the 13th never peeks
            ScrollViewReader { proxy in
                ScrollView {
                    LazyVStack(spacing: 0) {
                        if vm.visibleApps.isEmpty {
                            EmptyAppsView(isLoading: vm.isListingApps, hasDevice: vm.selectedDevice != nil, appsHaveBeenFetched: vm.appsHaveBeenFetched, deviceState: vm.selectedDevice?.state, stateTitle: vm.appsStateTitle, stateMessage: vm.appsStateMessage, stateIconFile: vm.appsStateIconFile)
                        } else {
                            ForEach(vm.visibleApps) { app in
                                AppRowView(app: app)
                                    .id(app.id)
                                if app.id != vm.visibleApps.last?.id {
                                    Divider().padding(.leading, 56)
                                }
                            }
                        }
                    }
                }
                .frame(maxHeight: .infinity)
                .background(Color.textBg)
                .onChange(of: vm.selectedApp) { _, newApp in
                    if let app = newApp { proxy.scrollTo(app.id) }
                }
            }
        }
    }
}

// MARK: - App Row

struct AppRowView: View {
    @Environment(MainViewModel.self) private var vm
    let app: AppEntry

    private var isSelected: Bool { vm.selectedApp?.id == app.id }
    // Read live name directly from vm so detection updates render immediately
    private var displayName: String { vm.livePathDisplayNames[app.appPath] ?? app.displayName }

    @State private var showingAppStoreAlert = false

    var body: some View {
        HStack(spacing: 0) {
            // Icon
            RoundedRectangle(cornerRadius: 10)
                .fill(Color.secondary.opacity(0.15))
                .frame(width: 40, height: 40)
                .overlay {
                    Image(systemName: "gamecontroller")
                        .font(.system(size: 16))
                        .foregroundStyle(.secondary)
                }
                .padding(.leading, 12)
                .padding(.trailing, 8)

            // Text info
            VStack(alignment: .leading, spacing: 2) {
                Text(displayName)
                    .font(.system(size: 13))
                    .foregroundStyle(.primary)
                    .lineLimit(1)

                let isActiveApp = (vm.isRunning || vm.isLaunching) && vm.selectedApp?.id == app.id
                if isActiveApp && app.metalHUDStatus?.isPositive != false {
                    HStack(spacing: 4) {
                        Circle()
                            .fill(Color.green)
                            .frame(width: 6, height: 6)
                        Text("Running with Metal HUD")
                            .font(.system(size: 11))
                            .foregroundStyle(Color.green)
                    }
                } else if let hud = app.metalHUDStatus {
                    Text(hud.text)
                        .font(.system(size: 11))
                        .foregroundStyle(hud.isPositive ? Color.green : Color.red)
                } else if app.skipIconLookup {
                    Text("Game name not identifiable · Click ⋮ to report")
                        .font(.system(size: 11))
                        .foregroundStyle(.secondary)
                } else {
                    Text("Metal HUD Support Unconfirmed · Click ⋮ to report")
                        .font(.system(size: 11))
                        .foregroundStyle(.secondary)
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(.trailing, 4)

            // Three-dot menu
            Menu {
                if vm.pinnedApps.contains(app.internalName) {
                    Button("Unpin from Top") { showAppStoreOnlyAlert() }
                } else {
                    Button("Pin to Top") { showAppStoreOnlyAlert() }
                }
                Divider()
                Button("Hide App") { showAppStoreOnlyAlert() }
                Divider()
                Button("Report: Wrong Name") {
                    showWrongNameDialog()
                }
                Button("Report: Not a Game") {
                    showNotAGameDialog()
                }
                Button("Report: Metal HUD Supported") {
                    vm.analytics.sendAppReport(
                        internalName: app.internalName, displayName: app.displayName,
                        iconURL: "", reportType: "HUD Supported"
                    )
                    showReportSentAlert("\"\(app.displayName)\" has been reported as Metal HUD supported.")
                }
                Button("Report: Metal HUD Unsupported") {
                    vm.analytics.sendAppReport(
                        internalName: app.internalName, displayName: app.displayName,
                        iconURL: "", reportType: "HUD Unsupported"
                    )
                    showReportSentAlert("\"\(app.displayName)\" has been reported as Metal HUD unsupported.")
                }
            } label: {
                Image(systemName: "ellipsis")
                    .font(.system(size: 14))
                    .foregroundStyle(.secondary)
                    .frame(width: 32, height: 44)
                    .contentShape(Rectangle())
            }
            .menuStyle(.borderlessButton)
            .menuIndicator(.hidden)
            .frame(width: 32)
        }
        .frame(height: 56)
        .contentShape(Rectangle())
        .background(isSelected ? Color.accentColor.opacity(0.15) : Color.clear)
        .onTapGesture(count: 2) {
            vm.pendingSelectInternalName = nil
            vm.selectedApp = app
            vm.selectedHistoryEntry = nil
            guard let device = vm.selectedDevice, !vm.isLaunching, !vm.isListingApps else { return }
            Task { await vm.launchApp(device: device, app: app) }
        }
        .onTapGesture(count: 1) {
            vm.pendingSelectInternalName = nil
            vm.selectedApp = app
            vm.selectedHistoryEntry = nil
        }
        .alert("App Store Only", isPresented: $showingAppStoreAlert) {
            Button("Get on App Store") {
                #if canImport(AppKit)
                NSWorkspace.shared.open(URL(string: "https://apps.apple.com/app/id6763967836")!)
                #endif
            }
            Button("Cancel", role: .cancel) { }
        } message: {
            Text("This feature is only available in the App Store version of FPS Logger.")
        }
    }

    private func showAppStoreOnlyAlert() {
        showingAppStoreAlert = true
    }

    private func showReportSentAlert(_ message: String) {
        #if canImport(AppKit)
        let alert = NSAlert()
        alert.messageText = "Report Sent"
        alert.informativeText = "Thanks! \(message)\n\nI'll review and fix it in a future update."
        alert.alertStyle = .informational
        alert.addButton(withTitle: "OK")
        alert.runModal()
        #endif
    }
}

// MARK: - Analytics access from AppRowView
private extension AppRowView {
    var analytics: AnalyticsService { AnalyticsService.shared }

    func showNotAGameDialog() {
        #if canImport(AppKit)
        let alert = NSAlert()
        alert.messageText = "Report: Not a Game"
        alert.informativeText = "Do you know what \"\(app.displayName)\" actually is?\n\nEnter it below to help identify this app, or leave blank to just report it as not a game."
        alert.alertStyle = .informational

        let textField = NSTextField(frame: NSRect(x: 0, y: 0, width: 300, height: 22))
        textField.placeholderString = "What is it? e.g. \"Browser\", \"Utility\" (optional)"
        alert.accessoryView = textField

        alert.addButton(withTitle: "Send Report")
        alert.addButton(withTitle: "Cancel")

        let response = alert.runModal()
        if response == .alertFirstButtonReturn {
            let details = textField.stringValue.trimmingCharacters(in: .whitespaces)
            vm.analytics.sendAppReport(
                internalName: app.internalName,
                displayName: app.displayName,
                iconURL: "",
                reportType: "Not a Game",
                suggestedName: details
            )
            let detail = details.isEmpty ? "" : " (\(details))"
            showReportSentAlert("\"\(app.displayName)\" has been flagged as not a game\(detail).")
        }
        #endif
    }

    func showWrongNameDialog() {
        #if canImport(AppKit)
        let alert = NSAlert()
        alert.messageText = "Report: Wrong Name"
        alert.informativeText = "Do you know the correct name for \"\(app.displayName)\"?\n\nEnter it below to help identify this app, or leave blank to just report the name as wrong."
        alert.alertStyle = .informational

        let textField = NSTextField(frame: NSRect(x: 0, y: 0, width: 300, height: 22))
        textField.placeholderString = "Correct name (optional)"
        alert.accessoryView = textField

        alert.addButton(withTitle: "Send Report")
        alert.addButton(withTitle: "Cancel")

        let response = alert.runModal()
        if response == .alertFirstButtonReturn {
            let suggested = textField.stringValue.trimmingCharacters(in: .whitespaces)
            vm.analytics.sendAppReport(
                internalName: app.internalName,
                displayName: app.displayName,
                iconURL: "",
                reportType: "Wrong Name",
                suggestedName: suggested
            )
            let detail = suggested.isEmpty ? "" : " (suggested: \"\(suggested)\")"
            showReportSentAlert("Wrong name report for \"\(app.displayName)\"\(detail) has been sent.")
        }
        #endif
    }
}

// MARK: - Empty state

struct EmptyAppsView: View {
    let isLoading: Bool
    let hasDevice: Bool
    var appsHaveBeenFetched: Bool = false
    var deviceState: String? = nil
    var stateTitle: String? = nil
    var stateMessage: String? = nil
    var stateIconFile: String? = nil

    var body: some View {
        VStack(spacing: 10) {
            if isLoading {
                ProgressView("Loading apps…")
                    .padding(.top, 60)
            } else if let message = stateMessage {
                stateIconView
                    .padding(.top, 40)
                if let title = stateTitle {
                    Text(title)
                        .font(.system(size: 15, weight: .semibold))
                }
                Text(message)
                    .font(.system(size: 13))
                    .foregroundStyle(.secondary)
                    .multilineTextAlignment(.center)
                    .padding(.horizontal, 30)
            } else if !hasDevice {
                Image(systemName: "iphone.slash")
                    .font(.system(size: 36))
                    .foregroundStyle(.secondary)
                    .padding(.top, 40)
                Text("Select a Device")
                    .font(.system(size: 15, weight: .semibold))
                Text("Select a device from the list, then click Show Running Games.")
                    .font(.system(size: 13))
                    .foregroundStyle(.secondary)
                    .multilineTextAlignment(.center)
                    .padding(.horizontal, 30)
            } else if appsHaveBeenFetched {
                ZStack(alignment: .bottomTrailing) {
                    Image(systemName: "gamecontroller")
                        .font(.system(size: 36))
                        .foregroundStyle(.secondary)
                    Image(systemName: "xmark.circle.fill")
                        .font(.system(size: 16))
                        .foregroundStyle(.secondary)
                        .offset(x: 4, y: 4)
                }
                .padding(.top, 40)
                Text("No Running Games")
                    .font(.system(size: 15, weight: .semibold))
                Text("No games were detected on this device.")
                    .font(.system(size: 13))
                    .foregroundStyle(.secondary)
                    .multilineTextAlignment(.center)
                    .padding(.horizontal, 30)
            } else {
                let state = deviceState?.lowercased() ?? ""
                if state.contains("unavailable") {
                    Image(systemName: "wifi.slash")
                        .font(.system(size: 36))
                        .foregroundStyle(.red)
                        .padding(.top, 40)
                    Text("Device Offline")
                        .font(.system(size: 15, weight: .semibold))
                    Text("Connect via USB or ensure it's on the same Wi-Fi, then press Show Running Games.")
                        .font(.system(size: 13))
                        .foregroundStyle(.secondary)
                        .multilineTextAlignment(.center)
                        .padding(.horizontal, 30)
                } else if state == "unsupported" {
                    Image(systemName: "xmark.circle")
                        .font(.system(size: 36))
                        .foregroundStyle(.secondary)
                        .padding(.top, 40)
                    Text("Device Not Supported")
                        .font(.system(size: 15, weight: .semibold))
                    Text("This device type cannot be used with FPS Logger.")
                        .font(.system(size: 13))
                        .foregroundStyle(.secondary)
                        .multilineTextAlignment(.center)
                        .padding(.horizontal, 30)
                } else if state.contains("pairing") {
                    Image(systemName: "lock")
                        .font(.system(size: 36))
                        .foregroundStyle(.orange)
                        .padding(.top, 40)
                    Text("Device Not Paired")
                        .font(.system(size: 15, weight: .semibold))
                    Text("Unlock → connect USB → Trust → replug, then press Show Running Games.")
                        .font(.system(size: 13))
                        .foregroundStyle(.secondary)
                        .multilineTextAlignment(.center)
                        .padding(.horizontal, 30)
                } else if state == "available" {
                    Image(systemName: "exclamationmark.triangle")
                        .font(.system(size: 36))
                        .foregroundStyle(.orange)
                        .padding(.top, 40)
                    Text("Device Preparing")
                        .font(.system(size: 15, weight: .semibold))
                    Text("Device is visible but still preparing. Pairing may be required. You can still try Show Running Games.")
                        .font(.system(size: 13))
                        .foregroundStyle(.secondary)
                        .multilineTextAlignment(.center)
                        .padding(.horizontal, 30)
                } else if state.contains("no ddi") || state.contains("limited support") {
                    Image(systemName: "exclamationmark.triangle.fill")
                        .font(.system(size: 36))
                        .foregroundStyle(.orange)
                        .padding(.top, 40)
                    Text("Connected (Limited Support)")
                        .font(.system(size: 15, weight: .semibold))
                    VStack(spacing: 6) {
                        Text("This device may have trouble enabling Metal HUD.")
                        Text("If you can't connect, try updating your device or Xcode, or download Xcode beta from the App Store or developer.apple.com.")
                        Text("You can still press Show Running Games.")
                    }
                    .font(.system(size: 13))
                    .foregroundStyle(.secondary)
                    .multilineTextAlignment(.center)
                    .padding(.horizontal, 30)
                } else {
                    Image(systemName: "gamecontroller")
                        .font(.system(size: 36))
                        .foregroundStyle(.secondary)
                        .padding(.top, 40)
                    Text("Ready")
                        .font(.system(size: 15, weight: .semibold))
                    Text("Click Show Running Games, or double-click a device to see running apps.")
                        .font(.system(size: 13))
                        .foregroundStyle(.secondary)
                        .multilineTextAlignment(.center)
                        .padding(.horizontal, 30)
                }
            }
        }
        .frame(maxWidth: .infinity)
        .padding(.bottom, 40)
    }

    @ViewBuilder
    private var stateIconView: some View {
        let file = stateIconFile?.lowercased() ?? ""
        if file == "locked" {
            Image(systemName: "lock")
                .font(.system(size: 36))
                .foregroundStyle(.orange)
        } else if file.contains("pairing") {
            Image(systemName: "lock")
                .font(.system(size: 36))
                .foregroundStyle(.orange)
        } else if file == "unavailable" {
            Image(systemName: "wifi.slash")
                .font(.system(size: 36))
                .foregroundStyle(.red)
        } else if file == "unsupported" {
            Image(systemName: "xmark.circle")
                .font(.system(size: 36))
                .foregroundStyle(.secondary)
        } else {
            Image(systemName: "wifi.slash")
                .font(.system(size: 36))
                .foregroundStyle(.secondary)
        }
    }
}


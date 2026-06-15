import SwiftUI

struct DeviceListView: View {
    @Environment(MainViewModel.self) private var vm
    @State private var showUnpairConfirm = false
    @State private var deviceToUnpair: Device?

    var body: some View {
        VStack(spacing: 0) {
            // Header
            HStack {
                Text("Devices")
                    .font(.system(size: 13, weight: .semibold))
                Spacer()
                #if canImport(AppKit)
                Button {
                    Task { @MainActor in await vm.listDevices() }
                } label: {
                    if vm.isListingDevices {
                        ProgressView().controlSize(.mini)
                    } else {
                        Image(systemName: "arrow.clockwise")
                            .font(.system(size: 13))
                    }
                }
                .disabled(vm.isListingDevices)
                .buttonStyle(.bordered)
                .controlSize(.small)
                .help("Refresh Devices")
                #endif
            }
            .padding(.horizontal, 14)
            .padding(.vertical, 10)
            .background(Color.controlBg)

            Divider()

            #if canImport(AppKit)
            // Device column headers
            HStack(spacing: 0) {
                Text("Name")
                    .frame(width: 200, alignment: .leading)
                Text("State")
                    .frame(width: 230, alignment: .leading)
                Text("Model")
                    .padding(.leading, 8)
                    .frame(maxWidth: .infinity, alignment: .leading)
                Text("")
                    .frame(width: 24)
            }
            .font(.system(size: 11))
            .foregroundStyle(.secondary)
            .padding(.horizontal, 14)
            .padding(.vertical, 5)
            .background(Color.controlBg)
            .clipped()

            Divider()
            #endif

            // Device rows
            ScrollViewReader { proxy in
                ScrollView {
                    LazyVStack(spacing: 0) {
                        if vm.devices.isEmpty && !vm.isListingDevices {
                            EmptyDeviceView()
                        } else {
                            ForEach(vm.devices) { device in
                                DeviceRowView(device: device, onUnpair: {
                                    deviceToUnpair = device
                                    showUnpairConfirm = true
                                })
                                .id(device.id)
                                if device.id != vm.devices.last?.id {
                                    Divider().padding(.leading, 14)
                                }
                            }
                        }
                    }
                }
                .onChange(of: vm.selectedDevice) { _, d in
                    if let d { proxy.scrollTo(d.id, anchor: .center) }
                }
            }
            .background(Color.textBg)
        }
        .confirmationDialog(
            "Unpair \(deviceToUnpair?.name ?? "Device")?",
            isPresented: $showUnpairConfirm,
            titleVisibility: .visible
        ) {
            Button("Unpair", role: .destructive) {
                if let d = deviceToUnpair {
                    Task { @MainActor in await vm.unpairDevice(d) }
                }
            }
            Button("Cancel", role: .cancel) {}
        } message: {
            if let d = deviceToUnpair {
                Text("Are you sure you want to unpair \(d.name) (\(DeviceModels.clean(d.model)))?")
            }
        }
    }
}

// MARK: - Section header

struct SectionHeaderView: View {
    let title: String

    var body: some View {
        Text(title)
            .font(.system(size: 11, weight: .semibold))
            .foregroundStyle(.secondary)
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(.horizontal, 14)
            .padding(.vertical, 5)
            .background(Color.controlBg)
    }
}

// MARK: - Device Row

struct DeviceRowView: View {
    @Environment(MainViewModel.self) private var vm
    let device: Device
    let onUnpair: () -> Void

    @State private var showReportConnectionAlert = false
    @State private var pendingMailURL: URL? = nil
    @State private var pendingMailSubject: String = ""
    @State private var pendingMailBody: String = ""
    @State private var pendingLogSuffix: String = ""

    private var isSelected: Bool { vm.selectedDevice?.id == device.id }

    var body: some View {
        HStack(spacing: 0) {
            // Name + device icon
            HStack(spacing: 6) {
                DeviceIconView(device: device)
                    .frame(width: 32, height: 32)
                Text(device.name)
                    .font(.system(size: 13))
                    .foregroundStyle(Color.accentColor)
                    .lineLimit(1)
                    .truncationMode(.tail)
            }
            .frame(width: 200, alignment: .leading)

            // Wireless State
            HStack(spacing: 4) {
                ConnectionIconView(state: device.state)
                    .frame(width: 18, height: 14)
                Text(device.displayState)
                    .font(.system(size: 12))
                    .foregroundStyle(.primary)
                    .lineLimit(1)
                    .truncationMode(.tail)
            }
            .frame(width: 230, alignment: .leading)

            // Model
            Text(DeviceModels.clean(device.model))
                .font(.system(size: 12))
                .foregroundStyle(.secondary)
                .lineLimit(1)
                .truncationMode(.tail)
                .padding(.leading, 8)
                .frame(maxWidth: .infinity, alignment: .leading)

            // More menu (end of row, no chevron indicator)
            Menu {
                Button("Check Connection") {
                    let msg = "[Check Connection] device.name=\(device.name) model=\(device.model) state=\(device.state) displayState=\(device.displayState)\n"
                    print(msg, terminator: "")
                    vm.appendLog(msg)
                    vm.connectionStateInfoDevice = device
                    NotificationCenter.default.post(name: .showConnectionStateInfo, object: nil)
                }
                Button("Report Connection Issue") {
                    let model = DeviceModels.clean(device.model)
                    let subject = "Connection Issue – \(model)"
                    let appVersion = Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String ?? ""
                    let body = "Model: \(model)\nState: \(device.displayState)\nApp Version: \(appVersion)\n\n[Please describe the issue here]"
                    let encodedSubject = subject.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? ""
                    let encodedBody = body.addingPercentEncoding(withAllowedCharacters: .urlQueryAllowed) ?? ""
                    pendingMailURL = URL(string: "mailto:business@mrmacright.com?subject=\(encodedSubject)&body=\(encodedBody)")
                    pendingMailSubject = subject
                    pendingMailBody = body
                    pendingLogSuffix = "\n\n--- Device Connection Report ---\nModel: \(model)\nDisplay State: \(device.displayState)\nRaw State: \(device.state)\n"
                    showReportConnectionAlert = true
                }
                #if canImport(AppKit)
                Divider()
                Button("Unpair \(device.name)", role: .destructive) {
                    onUnpair()
                }
                #endif
            } label: {
                Text("⋮")
                    .font(.system(size: 16))
                    .foregroundStyle(.secondary)
            }
            .menuStyle(.borderlessButton)
            .menuIndicator(.hidden)
            .frame(width: 24)
        }
        .padding(.horizontal, 14)
        .padding(.vertical, 10)
        .contentShape(Rectangle())
        .background(isSelected ? Color.accentColor.opacity(0.15) : Color.clear)
        .onTapGesture(count: 2) {
            vm.selectedDevice = device
            vm.connectionHint = ""
            vm.apps = []
            vm.appsStateMessage = nil
            vm.appsStateIconFile = nil
            vm.pendingSelectInternalName = nil
            Task { await vm.showApps(for: device) }
        }
        .onTapGesture(count: 1) {
            vm.selectedDevice = device
            vm.connectionHint = ""
            vm.apps = []
            vm.appsHaveBeenFetched = false
            vm.appsStateMessage = nil
            vm.appsStateIconFile = nil
        }
        #if canImport(AppKit)
        .contextMenu {
            Button("Unpair \(device.name)", role: .destructive) {
                onUnpair()
            }
        }
        #endif
        .alert("Report Connection Issue", isPresented: $showReportConnectionAlert) {
            Button("Attach Logs") {
                vm.openMailWithLogs(subject: pendingMailSubject, body: pendingMailBody, logSuffix: pendingLogSuffix)
            }
            Button("Open Mail") {
                if let url = pendingMailURL {
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
    }
}

// MARK: - Device Icon

struct DeviceIconView: View {
    let device: Device
    @Environment(\.colorScheme) private var colorScheme

    private var sfSymbolName: String? {
        switch device.deviceType {
        case .appleTV:          return "appletv"
        case .appleWatch:       return "applewatch"
        case .appleVisionPro:   return "visionpro"
        default:                return nil
        }
    }

    var body: some View {
        if let symbol = sfSymbolName {
            Image(systemName: symbol)
                .resizable()
                .aspectRatio(contentMode: .fit)
                .foregroundStyle(.secondary)
        } else if let img = loadBundleIcon() {
            #if canImport(AppKit)
            Image(nsImage: img)
                .resizable()
                .aspectRatio(contentMode: .fit)
                .colorInvert(colorScheme == .dark)
            #endif
        } else {
            Image(systemName: device.deviceType == .unknown ? "questionmark.square" : "iphone")
                .resizable()
                .aspectRatio(contentMode: .fit)
                .foregroundStyle(.secondary)
        }
    }

    private func loadBundleIcon() -> PlatformImage? {
        let model = DeviceModels.clean(device.model)
        switch device.deviceType {
        case .iPhone:
            return loadPNG(model, in: "assets/UI/Devices/iPhone")
                ?? loadPNG("Generic iPhone", in: "assets/UI/Devices/iPhone")
        case .iPad:
            return loadPNG(model, in: "assets/UI/Devices/iPad")
                ?? loadPNG("Generic iPad", in: "assets/UI/Devices/iPad")
        default:
            return nil
        }
    }

    private func loadPNG(_ name: String, in subdir: String) -> PlatformImage? {
        guard let url = Bundle.main.url(forResource: name, withExtension: "png", subdirectory: subdir) else { return nil }
        #if canImport(AppKit)
        return NSImage(contentsOf: url)
        #else
        return nil
        #endif
    }
}

// MARK: - Connection Icon

struct ConnectionIconView: View {
    let state: String

    var body: some View {
        let normalized = state.lowercased()
        if normalized == "available (local)" {
            Image(systemName: "iphone")
                .resizable().aspectRatio(contentMode: .fit).foregroundStyle(.green)
        } else if normalized.contains("paired") {
            Image(systemName: "wifi")
                .resizable().aspectRatio(contentMode: .fit).foregroundStyle(.green)
        } else if normalized.hasPrefix("unavailable") {
            Image(systemName: "wifi.slash")
                .resizable().aspectRatio(contentMode: .fit).foregroundStyle(.red)
        } else if normalized.contains("unsupported") {
            Image(systemName: "xmark.circle")
                .resizable().aspectRatio(contentMode: .fit).foregroundStyle(.secondary)
        } else if normalized.contains("pairing") {
            Image(systemName: "lock")
                .resizable().aspectRatio(contentMode: .fit).foregroundStyle(.orange)
        } else if normalized.contains("no ddi") || normalized.contains("limited support") {
            Image(systemName: "exclamationmark.triangle.fill")
                .resizable().aspectRatio(contentMode: .fit).foregroundStyle(.orange)
        } else if normalized == "available" || normalized.contains("preparing") {
            Image(systemName: "exclamationmark.triangle")
                .resizable().aspectRatio(contentMode: .fit).foregroundStyle(.orange)
        } else {
            Image(systemName: "cable.connector")
                .resizable().aspectRatio(contentMode: .fit).foregroundStyle(.secondary)
        }
    }
}

// MARK: - Empty state

struct EmptyDeviceView: View {
    var body: some View {
        VStack(spacing: 8) {
            Image(systemName: "iphone.slash")
                .font(.system(size: 36))
                .foregroundStyle(.secondary)
                .padding(.top, 40)
            Text("No devices found")
                .font(.system(size: 16, weight: .semibold))
            Text("Connect an iPhone or iPad via USB, or pair Apple TV, then tap the refresh button.")
                .font(.system(size: 13))
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal, 24)
        }
        .frame(maxWidth: .infinity)
        .padding(.bottom, 40)
    }
}

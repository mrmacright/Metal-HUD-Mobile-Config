import SwiftUI
#if canImport(AppKit)
import AppKit
#endif

struct CustomMetricsView: View {
    @Environment(MainViewModel.self) private var vm
    @Environment(\.dismiss) private var dismiss

    // Two columns of toggles
    private let columns = [GridItem(.flexible()), GridItem(.flexible())]
    private let scaleSteps: [HUDSettings.HUDScale] = [.small, .default, .large, .larger, .max]

    @State private var showSaveAlert = false
    @State private var newPresetName: String = ""
    @State private var presetPendingDeletion: HUDSettings.CustomPreset? = nil
    @State private var showMetricsInfo = false

    @State private var showAppStoreOnlyAlert = false

    private var hasAnySelection: Bool {
        vm.hudSettings.customElements.values.contains(true)
    }

    private var atPresetLimit: Bool {
        vm.hudSettings.savedCustomPresets.count >= HUDSettings.maxSavedCustomPresets
    }

    var body: some View {
        @Bindable var vm = vm

        VStack(spacing: 0) {
            // Title bar
            HStack {
                Text("Custom Metrics")
                    .font(.system(size: 16, weight: .semibold))
                Spacer()
                if hasAnySelection {
                    Button("Save Preset…") { handleSavePresetTap() }
                        .disabled(saveButtonDisabled)
                        .help(savePresetTooltip)
                }
                Button("Reset") {
                    vm.hudSettings.reset()
                    vm.save()
                }
                Button("Done") { dismiss() }
                    .buttonStyle(.borderedProminent)
            }
            .padding(.horizontal, 24)
            .padding(.vertical, 16)
            .background(Color.controlBg)

            Divider()

            ScrollView {
                VStack(alignment: .leading, spacing: 16) {

                    // MARK: Preset quick-load
                    metricSectionHeader("Presets")
                    ScrollView(.horizontal, showsIndicators: false) {
                        HStack(spacing: 8) {
                            ForEach(HUDSettings.HUDPreset.allCases.filter { $0 != .custom }) { preset in
                                Button(preset.rawValue) { loadPreset(preset) }
                                    .buttonStyle(.bordered)
                                    .controlSize(.small)
                            }
                            if !vm.hudSettings.savedCustomPresets.isEmpty {
                                Divider().frame(height: 16)
                                ForEach(vm.hudSettings.savedCustomPresets) { saved in
                                    savedPresetButton(saved)
                                }
                            }
                        }
                    }

                    Divider()

                    // MARK: Elements
                    HStack(spacing: 6) {
                        metricSectionHeader("Metrics")
                        Button {
                            showMetricsInfo.toggle()
                        } label: {
                            Image(systemName: "info.circle")
                                .font(.system(size: 12))
                                .foregroundStyle(.secondary)
                        }
                        .buttonStyle(.borderless)
                        .popover(isPresented: $showMetricsInfo, arrowEdge: .trailing) {
                            metricsInfoPopover
                        }
                    }
                    LazyVGrid(columns: columns, alignment: .leading, spacing: 10) {
                        ForEach(HUDSettings.customElementKeys, id: \.key) { item in
                            let binding = Binding(
                                get: { vm.hudSettings.customElements[item.key] ?? false },
                                set: {
                                    vm.hudSettings.customElements[item.key] = $0
                                    vm.hudSettings.preset = .custom
                                    vm.hudSettings.selectedSavedPresetID = nil
                                    vm.save()
                                }
                            )
                            Toggle(item.label, isOn: binding)
                                #if canImport(AppKit)
                                .toggleStyle(.checkbox)
                                #endif
                                .font(.system(size: 13))
                        }
                    }

                    Divider()

                    // MARK: HUD Options
                    metricSectionHeader("HUD Options")

                    HStack {
                        Text("Position")
                            .font(.system(size: 13))
                        Spacer()
                        Picker("Position", selection: Binding(
                            get: { vm.hudSettings.alignment },
                            set: { vm.hudSettings.alignment = $0; vm.save() }
                        )) {
                            ForEach(HUDSettings.HUDAlignment.allCases) { alignment in
                                Text(alignment.rawValue).tag(alignment)
                            }
                        }
                        .pickerStyle(.menu)
                        .labelsHidden()
                        .frame(width: 140)
                    }

                    VStack(alignment: .leading, spacing: 4) {
                        HStack {
                            Text("Scale")
                                .font(.system(size: 13))
                            Spacer()
                            Text(vm.hudSettings.scale.rawValue)
                                .font(.system(size: 13))
                                .foregroundStyle(.secondary)
                        }
                        Slider(
                            value: Binding(
                                get: { Double(scaleSteps.firstIndex(of: vm.hudSettings.scale) ?? 1) },
                                set: {
                                    vm.hudSettings.scale = scaleSteps[Int($0.rounded())]
                                    vm.save()
                                }
                            ),
                            in: 0...4,
                            step: 1
                        )
                        HStack {
                            Text("Small")
                            Spacer()
                            Text("Max")
                        }
                        .font(.system(size: 10))
                        .foregroundStyle(.secondary)
                    }

                    VStack(alignment: .leading, spacing: 2) {
                        Toggle("Show Metrics Range", isOn: Binding(
                            get: { vm.hudSettings.showMetricsRange },
                            set: { vm.hudSettings.showMetricsRange = $0; vm.save() }
                        ))
                        #if canImport(AppKit)
                        .toggleStyle(.checkbox)
                        #endif
                        .font(.system(size: 13))
                        .help("Shows each metric in three columns: average (last 120 frames), min and max (last 1200 frames)")
                        .disabled(true)
                        Text("Shows each metric in three columns: average over the last 120 frames, and min/max over the last 1200 frames.")
                            .font(.system(size: 11))
                            .foregroundStyle(.secondary)
                            .padding(.leading, 20)
                    }

                    VStack(alignment: .leading, spacing: 2) {
                        Toggle("Performance Insights", isOn: Binding(
                            get: { vm.hudSettings.insightsEnabled },
                            set: { vm.hudSettings.insightsEnabled = $0; vm.save() }
                        ))
                        #if canImport(AppKit)
                        .toggleStyle(.checkbox)
                        #endif
                        .font(.system(size: 13))
                        .help("Collects Metal API statistics per frame and shows an insight overlay when a GPU performance pattern persists for 5+ seconds")
                        Text("Collects Metal API statistics each frame. If a pattern suggesting a GPU performance issue appears in at least half of frames over 5 seconds, an insight overlay appears.")
                            .font(.system(size: 11))
                            .foregroundStyle(.secondary)
                            .padding(.leading, 20)
                    }

                    if !vm.hudSettings.savedCustomPresets.isEmpty {
                        Divider()
                        savedPresetsSection
                    }
                }
                .padding(24)
            }
        }
        .frame(width: 520)
        .alert("Save Custom Preset", isPresented: $showSaveAlert) {
            TextField("Preset name", text: $newPresetName)
            Button("Save") { saveCurrentAsPreset() }
            Button("Cancel", role: .cancel) { }
        } message: {
            Text("Saved presets appear under Settings → Metric Presets. You can save up to \(HUDSettings.maxSavedCustomPresets).")
        }
        .alert(
            "Delete \"\(presetPendingDeletion?.name ?? "")\"?",
            isPresented: Binding(
                get: { presetPendingDeletion != nil },
                set: { if !$0 { presetPendingDeletion = nil } }
            ),
            presenting: presetPendingDeletion
        ) { preset in
            Button("Delete", role: .destructive) { deletePreset(preset) }
            Button("Cancel", role: .cancel) { }
        } message: { _ in
            Text("Are you sure you want to delete this saved preset? This can't be undone.")
        }
        .alert("App Store Only", isPresented: $showAppStoreOnlyAlert) {
            Button("Get on App Store") {
                #if canImport(AppKit)
                NSWorkspace.shared.open(URL(string: "https://apps.apple.com/app/id6763967836")!)
                #endif
            }
            Button("Cancel", role: .cancel) { }
        } message: {
            Text("Saving custom metric presets is only available in the App Store version of FPS Logger.")
        }
    }

    // MARK: - Saved presets list

    @ViewBuilder
    private var savedPresetsSection: some View {
        @Bindable var vm = vm

        VStack(alignment: .leading, spacing: 6) {
            HStack {
                Text("Saved Presets")
                    .font(.system(size: 11, weight: .semibold))
                    .foregroundStyle(.secondary)
                    .textCase(.uppercase)
                    .tracking(0.5)
                Spacer()
                Text("\(vm.hudSettings.savedCustomPresets.count) / \(HUDSettings.maxSavedCustomPresets)")
                    .font(.system(size: 11))
                    .foregroundStyle(.secondary)
            }

            ForEach(vm.hudSettings.savedCustomPresets) { preset in
                HStack {
                    Image(systemName: vm.hudSettings.selectedSavedPresetID == preset.id
                          ? "checkmark.circle.fill"
                          : "circle")
                        .foregroundStyle(vm.hudSettings.selectedSavedPresetID == preset.id
                                        ? Color.accentColor
                                        : Color.secondary)
                    Text(preset.name)
                        .font(.system(size: 13))
                    Spacer()
                    Button {
                        vm.hudSettings.customElements = preset.elements
                        vm.hudSettings.selectedSavedPresetID = preset.id
                        vm.save()
                    } label: {
                        Text("Apply")
                    }
                    .buttonStyle(.bordered)
                    .controlSize(.small)

                    Button(role: .destructive) {
                        presetPendingDeletion = preset
                    } label: {
                        Image(systemName: "trash")
                    }
                    .buttonStyle(.borderless)
                    .help("Delete preset")
                }
                .padding(.vertical, 2)
            }
        }
    }

    // MARK: - Helpers

    @ViewBuilder
    private func savedPresetButton(_ saved: HUDSettings.CustomPreset) -> some View {
        let isActive = vm.hudSettings.selectedSavedPresetID == saved.id
        Button(saved.name) {
            let elements: [String: Bool] = Dictionary(
                uniqueKeysWithValues: HUDSettings.customElementKeys.map { ($0.key, saved.elements[$0.key] ?? false) }
            )
            vm.hudSettings.preset = .custom
            vm.hudSettings.customElements = elements
            vm.hudSettings.selectedSavedPresetID = saved.id
            vm.save()
        }
        .buttonStyle(.bordered)
        .controlSize(.small)
        .tint(isActive ? .accentColor : nil)
    }

    private func metricSectionHeader(_ title: String) -> some View {
        Text(title)
            .font(.system(size: 11, weight: .semibold))
            .foregroundStyle(.secondary)
            .textCase(.uppercase)
            .tracking(0.5)
    }

    private func loadPreset(_ preset: HUDSettings.HUDPreset) {
        vm.hudSettings.applyPreset(preset)
        vm.save()
    }

    private var savePresetTooltip: String {
        return "Available in the App Store version of FPS Logger."
    }

    private var saveButtonDisabled: Bool {
        return false
    }

    private func handleSavePresetTap() {
        showAppStoreOnlyAlert = true
    }

    private func defaultPresetName() -> String {
        let base = "My Preset"
        let existing = Set(vm.hudSettings.savedCustomPresets.map { $0.name })
        var n = vm.hudSettings.savedCustomPresets.count + 1
        while existing.contains("\(base) \(n)") { n += 1 }
        return "\(base) \(n)"
    }

    private func deletePreset(_ preset: HUDSettings.CustomPreset) {
        vm.hudSettings.savedCustomPresets.removeAll { $0.id == preset.id }
        if vm.hudSettings.selectedSavedPresetID == preset.id {
            vm.hudSettings.selectedSavedPresetID = nil
        }
        vm.save()
    }

    // MARK: - Metrics info popover

    private var metricsInfoPopover: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 0) {
                Text("Metric Descriptions")
                    .font(.system(size: 13, weight: .semibold))
                    .padding(.bottom, 12)

                ForEach(Array(HUDSettings.customElementKeys.enumerated()), id: \.element.key) { index, item in
                    VStack(alignment: .leading, spacing: 3) {
                        Text(item.label)
                            .font(.system(size: 12, weight: .medium))
                        Text(Self.metricDescriptions[item.key] ?? "")
                            .font(.system(size: 11))
                            .foregroundStyle(.secondary)
                            .fixedSize(horizontal: false, vertical: true)
                    }
                    if index < HUDSettings.customElementKeys.count - 1 {
                        Divider().padding(.vertical, 8)
                    }
                }
            }
            .padding(16)
        }
        .frame(width: 290, height: 380)
    }

    private static let metricDescriptions: [String: String] = [
        "device":                   "Name of the MTLDevice rendering your app.",
        "layersize":                "Layer size and present mode (direct or composited).",
        "layerscale":               "Content scale factor and pixel format of the layer.",
        "memory":                   "Process memory usage and the MTLDevice's current allocated size.",
        "refreshrate":              "Current refresh rate of the display your app is on.",
        "thermal":                  "Current thermal state of the machine.",
        "gamemode":                 "Whether Game Mode is active (on or off).",
        "fps":                      "Rolling average frames per second over the past 120 frames.",
        "fpsgraph":                 "Chart of FPS for the past 120 frames.",
        "framenumber":              "Number of drawable presents since app launch or last metric reset.",
        "gputime":                  "Rolling average GPU time per frame over the past 120 frames.",
        "frameinterval":            "Rolling average on-glass time between two consecutive drawables over 120 frames.",
        "frameintervalgraph":       "Chart of frame interval for the past 120 frames.",
        "frameintervalhistogram":   "Bucketed frame interval bar chart. Bucket size equals the display refresh rate.",
        "presentdelay":             "Rolling average delay from presentDrawable call to drawable appearing on screen, over 120 frames.",
        "metalcpu":                 "Number of scheduled command buffers and encoders, plus their CPU encoding time for the last frame.",
        "gputimeline":              "GPU times per encoder type and a GPU timeline graph. Requires encoder timing to be enabled.",
        "toplabeledcommandbuffers": "Most GPU-intensive labeled command buffers. Requires encoder timing to be enabled.",
        "toplabeledencoders":       "Most GPU-intensive labeled encoders. Requires encoder timing to be enabled.",
        "shaders":                  "Shader compiler activity: pipeline state count, cached shaders, compiled shaders, and compilation time.",
        "metalfx":                  "MetalFX scaling method, resolution, and frame interpolation state. Only shown when MetalFX effects are active.",
        "disk":                     "Disk bytes read, written, and logical writes as reported by system usage.",
    ]

    private func saveCurrentAsPreset() {
        let trimmed = newPresetName.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return }
        guard vm.hudSettings.savedCustomPresets.count < HUDSettings.maxSavedCustomPresets else { return }
        let preset = HUDSettings.CustomPreset(
            name: trimmed,
            elements: vm.hudSettings.customElements
        )
        vm.hudSettings.savedCustomPresets.append(preset)
        vm.hudSettings.selectedSavedPresetID = preset.id
        vm.save()
    }
}

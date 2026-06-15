#if canImport(AppKit)
import SwiftUI

struct UninstallView: View {
    @Environment(MainViewModel.self) private var vm
    @Environment(\.dismiss) private var dismiss

    enum UninstallMode: String, CaseIterable {
        case basic = "basic"
        case full  = "full"
    }

    @State private var mode: UninstallMode = .basic
    @State private var isRunning = false
    @State private var resultMessage: String? = nil
    @State private var didSucceed = false

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            // Header
            HStack(spacing: 12) {
                Image(systemName: "trash.circle.fill")
                    .font(.system(size: 40))
                    .foregroundStyle(.red)
                VStack(alignment: .leading, spacing: 2) {
                    Text("Uninstall Developer Tools")
                        .font(.system(size: 17, weight: .semibold))
                    Text("Choose what to remove from your Mac.")
                        .font(.system(size: 13))
                        .foregroundStyle(.secondary)
                }
            }
            .padding(.horizontal, 24)
            .padding(.top, 24)
            .padding(.bottom, 20)

            Divider()

            // Options
            VStack(alignment: .leading, spacing: 0) {
                optionRow(
                    selected: mode == .basic,
                    title: "Remove Xcode & Command Line Tools",
                    description: "Removes Xcode.app, Xcode-beta.app, Command Line Tools, and resets xcode-select. Keeps your personal developer data.",
                    action: { mode = .basic }
                )

                Divider().padding(.leading, 48)

                optionRow(
                    selected: mode == .full,
                    title: "Remove Xcode, Command Line Tools & Stored Data",
                    description: "Everything above, plus ~/Library/Developer, Xcode caches, preferences, and system package receipts for CLTools. This is a full cleanup.",
                    action: { mode = .full }
                )
            }
            .padding(.vertical, 8)

            Divider()

            // Result message
            if let msg = resultMessage {
                HStack(spacing: 8) {
                    Image(systemName: didSucceed ? "checkmark.circle.fill" : "xmark.circle.fill")
                        .foregroundStyle(didSucceed ? .green : .red)
                    Text(msg)
                        .font(.system(size: 12))
                        .foregroundStyle(didSucceed ? Color.primary : Color.red)
                }
                .padding(.horizontal, 24)
                .padding(.top, 12)
            }

            // Buttons
            HStack {
                Spacer()
                Button("Cancel") {
                    dismiss()
                }
                .keyboardShortcut(.cancelAction)
                .disabled(isRunning)

                Button(role: .destructive) {
                    runUninstall()
                } label: {
                    if isRunning {
                        HStack(spacing: 6) {
                            ProgressView().controlSize(.small)
                            Text("Uninstalling…")
                        }
                    } else {
                        Text("Uninstall")
                    }
                }
                .buttonStyle(.borderedProminent)
                .tint(.red)
                .disabled(isRunning || didSucceed)
                .keyboardShortcut(.defaultAction)
            }
            .padding(.horizontal, 24)
            .padding(.vertical, 16)
        }
        .frame(width: 480)
        .fixedSize(horizontal: false, vertical: true)
    }

    private func optionRow(selected: Bool, title: String, description: String, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            HStack(alignment: .top, spacing: 12) {
                Image(systemName: selected ? "largecircle.fill.circle" : "circle")
                    .font(.system(size: 18))
                    .foregroundStyle(selected ? Color.accentColor : .secondary)
                    .frame(width: 24)
                    .padding(.top, 1)

                VStack(alignment: .leading, spacing: 3) {
                    Text(title)
                        .font(.system(size: 13, weight: .medium))
                        .foregroundStyle(.primary)
                    Text(description)
                        .font(.system(size: 11))
                        .foregroundStyle(.secondary)
                        .fixedSize(horizontal: false, vertical: true)
                }
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 12)
            .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
    }

    private func runUninstall() {
        isRunning = true
        resultMessage = nil

        let script = mode == .basic
            ? XcodeManager.shared.buildBasicUninstallScript()
            : XcodeManager.shared.buildFullUninstallScript()

        let modeLabel = mode == .basic ? "Xcode & Command Line Tools" : "Xcode, Command Line Tools & stored data"
        vm.appendLog("[Uninstall] Starting removal of \(modeLabel)…\n")

        let manager = XcodeManager.shared  // capture on @MainActor before entering Task.detached
        Task.detached {
            manager.runUninstallScript(script) { success in
                Task { @MainActor in
                    isRunning = false
                    didSucceed = success
                    if success {
                        resultMessage = "Successfully removed \(modeLabel)."
                        vm.appendLog("[Uninstall] Removal succeeded.\n")
                    } else {
                        resultMessage = "Removal failed or was cancelled."
                        vm.appendLog("[Uninstall] Removal failed.\n")
                    }
                }
            }
        }
    }
}
#endif

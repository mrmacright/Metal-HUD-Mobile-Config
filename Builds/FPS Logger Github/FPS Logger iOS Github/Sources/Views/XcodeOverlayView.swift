import SwiftUI
#if canImport(AppKit)
import AppKit
#endif

struct XcodeOverlayView: View {
    let title: String
    let message: String
    let buttonText: String
    let statusText: String
    let showContinueButton: Bool
    let onContinueWithoutXcode: (() -> Void)?
    let onDismiss: (() -> Void)?

    @State private var currentStatus: String

    init(
        title: String,
        message: String,
        buttonText: String = "Download Xcode",
        statusText: String = "Please install Xcode to continue.",
        showContinueButton: Bool = false,
        onContinueWithoutXcode: (() -> Void)? = nil,
        onDismiss: (() -> Void)? = nil
    ) {
        self.title = title
        self.message = message
        self.buttonText = buttonText
        self.statusText = statusText
        self.showContinueButton = showContinueButton
        self.onContinueWithoutXcode = onContinueWithoutXcode
        self.onDismiss = onDismiss
        self._currentStatus = State(initialValue: statusText)
    }

    var body: some View {
        ZStack {
            Color.windowBg
                .ignoresSafeArea()

            VStack(spacing: 16) {
                // Xcode icon
                #if canImport(AppKit)
                if let url = Bundle.main.url(forResource: "Xcode", withExtension: "png", subdirectory: "assets"),
                   let xcodeImage = NSImage(contentsOf: url) {
                    Image(nsImage: xcodeImage)
                        .resizable()
                        .aspectRatio(contentMode: .fit)
                        .frame(width: 120, height: 120)
                } else {
                    Image(systemName: "hammer.circle.fill")
                        .resizable()
                        .aspectRatio(contentMode: .fit)
                        .frame(width: 80, height: 80)
                        .foregroundStyle(.blue)
                }
                #else
                Image(systemName: "hammer.circle.fill")
                    .resizable()
                    .aspectRatio(contentMode: .fit)
                    .frame(width: 80, height: 80)
                    .foregroundStyle(.blue)
                #endif

                Text(title)
                    .font(.system(size: 22, weight: .bold))
                    .multilineTextAlignment(.center)

                Text(message)
                    .font(.system(size: 14))
                    .foregroundStyle(.secondary)
                    .multilineTextAlignment(.center)
                    .frame(maxWidth: 640)

                Text(currentStatus)
                    .font(.system(size: 12))
                    .foregroundStyle(.secondary)
                    .multilineTextAlignment(.center)

                Button(buttonText) {
                    openAppStore()
                }
                .buttonStyle(.borderedProminent)
                .controlSize(.large)

                if showContinueButton, let onContinue = onContinueWithoutXcode {
                    Button("Continue without Xcode") {
                        onContinue()
                    }
                    #if canImport(AppKit)
                    .buttonStyle(.link)
                    #else
                    .buttonStyle(.plain)
                    #endif
                    .font(.system(size: 12))
                    .foregroundStyle(.secondary)
                    .focusable(false)
                }

                Divider()
                    .frame(maxWidth: 480)
                    .padding(.top, 4)

                Text("Alternatively, FPS Logger on the App Store works without Xcode and includes performance logging, app icons, and more.")
                    .font(.system(size: 12))
                    .foregroundStyle(.secondary)
                    .multilineTextAlignment(.center)
                    .frame(maxWidth: 480)

                Button("Get FPS Logger on App Store") {
                    #if canImport(AppKit)
                    NSWorkspace.shared.open(URL(string: "https://apps.apple.com/app/id6763967836")!)
                    #endif
                }
                #if canImport(AppKit)
                .buttonStyle(.link)
                #else
                .buttonStyle(.plain)
                #endif
                .font(.system(size: 12))
                .focusable(false)
            }
            .frame(maxWidth: 700)
            .padding(.vertical, 40)
        }
        .onAppear {
            startPolling()
        }
    }

    private func openAppStore() {
        #if canImport(AppKit)
        NSWorkspace.shared.open(URL(string: "https://apps.apple.com/app/xcode/id497799835")!)
        #endif
        currentStatus = "Waiting for Xcode to be installed or updated…"
    }

    private func startPolling() {
        Task {
            while true {
                try? await Task.sleep(nanoseconds: 3_000_000_000)
                #if canImport(AppKit)
                guard XcodeManager.shared.isXcodeInstalled() else { continue }
                guard let version = XcodeManager.shared.xcodeVersion() else { continue }
                let current = XcodeManager.shared.versionTuple(version)
                let required = XcodeManager.shared.versionTuple(XcodeManager.shared.requiredVersion)
                if !current.lexicographicallyPrecedes(required) {
                    await MainActor.run { onDismiss?() }
                    return
                }
                await MainActor.run {
                    currentStatus = "Detected Xcode \(version). Waiting for Xcode \(XcodeManager.shared.requiredVersion) or later…"
                }
                #endif
            }
        }
    }
}


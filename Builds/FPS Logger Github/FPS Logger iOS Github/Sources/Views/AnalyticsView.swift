import SwiftUI
#if canImport(AppKit)
import AppKit
#endif

struct AnalyticsView: View {
    let onDone: () -> Void
    @Environment(MainViewModel.self) private var vm
    @State private var shareData: Bool = false

    var body: some View {
        ZStack {
            Color.black.opacity(0.3)
                .ignoresSafeArea()

            VStack(spacing: 0) {
                VStack(alignment: .leading, spacing: 0) {
                    // Header
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Help improve FPS Logger")
                            .font(.system(size: 18, weight: .bold))
                        Divider()
                    }
                    .padding(.horizontal, 28)
                    .padding(.top, 28)

                    // Body
                    VStack(alignment: .leading, spacing: 16) {
                        Text("By enabling this, anonymous compatibility data (device model, app name, connection state) will be sent to our servers to help improve FPS Logger. No personal data is collected and your location is never tracked.")
                            .font(.system(size: 13))
                            .foregroundStyle(.secondary)
                            .fixedSize(horizontal: false, vertical: true)
                            .padding(.top, 18)

                        Toggle("Share anonymous compatibility data", isOn: $shareData)
                            #if canImport(AppKit)
                            .toggleStyle(.checkbox)
                            #endif

                        Button("Privacy Policy") {
                            #if canImport(AppKit)
                            NSWorkspace.shared.open(URL(string: "https://www.fpslogger.com/privacy")!)
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
                    .padding(.horizontal, 28)
                    .padding(.bottom, 18)

                    Divider()

                    // Footer
                    HStack {
                        Spacer()
                        Button("OK") {
                            vm.analyticsOptIn = shareData
                            AnalyticsService.shared.isOptedIn = shareData
                            onDone()
                        }
                        .buttonStyle(.borderedProminent)
                    }
                    .padding(.horizontal, 20)
                    .padding(.vertical, 14)
                    .background(Color.controlBg)
                }
                .background(Color.windowBg)
                .clipShape(RoundedRectangle(cornerRadius: 12))
                .shadow(radius: 20)
                .frame(width: 540)
            }
        }
        .onAppear {
            shareData = vm.analyticsOptIn == true
        }
    }
}

import SwiftUI
#if canImport(AppKit)
import AppKit
#endif

struct PolicyOverlayView: View {
    let onAccepted: () -> Void
    @State private var licenseAccepted = false
    @State private var privacyAccepted = false

    private let licenseURL = URL(string: "https://www.fpslogger.com/license")!
    private let privacyURL = URL(string: "https://www.fpslogger.com/privacy")!

    var body: some View {
        ZStack {
            Color.black.opacity(0.3)
                .ignoresSafeArea()

            VStack(spacing: 0) {
                // Card
                VStack(alignment: .leading, spacing: 0) {
                    // Header
                    VStack(alignment: .leading, spacing: 12) {
                        Text("FPS Logger policies")
                            .font(.system(size: 18, weight: .bold))

                        Divider()
                    }
                    .padding(.horizontal, 28)
                    .padding(.top, 28)

                    // Body
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Please read our policies regarding app use and privacy.\nPolicies must be accepted to continue.")
                            .font(.system(size: 13))
                            .foregroundStyle(.secondary)
                            .fixedSize(horizontal: false, vertical: true)
                            .padding(.top, 18)

                        PolicyCheckboxRow(
                            isChecked: $licenseAccepted,
                            label: "I accept the",
                            linkText: "License",
                            url: licenseURL
                        )

                        PolicyCheckboxRow(
                            isChecked: $privacyAccepted,
                            label: "I accept the",
                            linkText: "Privacy Policy",
                            url: privacyURL
                        )
                    }
                    .padding(.horizontal, 28)
                    .padding(.bottom, 18)

                    Divider()

                    // Footer
                    HStack {
                        Spacer()
                        Button("Continue") {
                            onAccepted()
                        }
                        .disabled(!licenseAccepted || !privacyAccepted)
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
    }
}

struct PolicyCheckboxRow: View {
    @Binding var isChecked: Bool
    let label: String
    let linkText: String
    let url: URL

    var body: some View {
        HStack(spacing: 6) {
            Toggle("", isOn: $isChecked)
                .labelsHidden()
                #if canImport(AppKit)
                .toggleStyle(.checkbox)
                #endif
            Text(label + "  ")
                .font(.system(size: 13))
            Button(linkText) {
                #if canImport(AppKit)
                NSWorkspace.shared.open(url)
                #endif
            }
            #if canImport(AppKit)
            .buttonStyle(.link)
            #else
            .buttonStyle(.plain)
            #endif
            .font(.system(size: 13))
        }
    }
}

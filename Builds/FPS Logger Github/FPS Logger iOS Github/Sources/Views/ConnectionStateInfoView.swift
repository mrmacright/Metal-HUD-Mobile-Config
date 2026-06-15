import SwiftUI

struct ConnectionStateInfoView: View {
    let device: Device
    @Environment(\.dismiss) private var dismiss
    @State private var showFullHelp = false

    var body: some View {
        VStack(spacing: 0) {
            // Toolbar
            HStack {
                Text("Check Connection")
                    .font(.system(size: 16, weight: .semibold))
                Spacer()
                Button("Done") { dismiss() }
                    .keyboardShortcut(.escape)
            }
            .padding(.horizontal, 20)
            .padding(.vertical, 14)
            .background(Color.controlBg)

            Divider()

            VStack(alignment: .leading, spacing: 24) {
                // Device identity
                Text(DeviceModels.clean(device.model))
                    .font(.system(size: 15, weight: .semibold))

                Divider()

                // State badge
                HStack(spacing: 10) {
                    ConnectionIconView(state: device.displayState)
                        .frame(width: 22, height: 18)
                    Text(device.displayState)
                        .font(.system(size: 14, weight: .medium))
                }

                // State explanation
                VStack(alignment: .leading, spacing: 8) {
                    Text("What this means")
                        .font(.system(size: 13, weight: .semibold))
                        .foregroundStyle(.secondary)

                    Text(stateDescription)
                        .font(.system(size: 13))
                        .fixedSize(horizontal: false, vertical: true)

                    if let tip = stateTip {
                        Divider()
                            .padding(.vertical, 2)
                        Text(tip)
                            .font(.system(size: 12))
                            .foregroundStyle(.secondary)
                            .fixedSize(horizontal: false, vertical: true)
                    }
                }

                Spacer()
            }
            .padding(24)
        }
        .frame(width: 440, height: 340)
    }

    private var normalizedState: String { device.displayState.lowercased() }

    private var stateDescription: String {
        if normalizedState.contains("paired") {
            return "Your device is paired and reachable over Wi-Fi. No USB cable is needed to use Metal HUD."
        }
        if normalizedState.contains("limited support") {
            return "This device is connected via USB but may have trouble enabling Metal HUD due to a missing device support file."
        }
        if normalizedState.hasPrefix("connect") {
            return "Your device is connected via USB and ready. Wireless support may still be preparing."
        }
        if normalizedState.contains("preparing") {
            return "Your device is visible but still setting up. Pairing may be required. Metal HUD may still work — try connecting anyway."
        }
        if normalizedState.contains("pairing required") {
            return "Your device is visible but needs trust confirmation."
        }
        if normalizedState.hasPrefix("unavailable") {
            return "Your device is offline, turned off, or not reachable on the same Wi-Fi network."
        }
        if normalizedState.contains("unsupported") {
            return "This device does not support Metal HUD."
        }
        return "State information is not available for this device. Use More Connection Help for troubleshooting guidance."
    }

    private var stateTip: String? {
        if normalizedState.contains("preparing") {
            return "Try: Disconnect and reconnect the USB cable, then unlock the device and tap Trust if prompted."
        }
        if normalizedState.contains("pairing required") {
            return "Try: Connect via USB, unlock the device, and tap Trust This Computer."
        }
        if normalizedState.contains("limited support") {
            return "Try: Download or update Xcode to add device support files, then reconnect."
        }
        if normalizedState.hasPrefix("unavailable") {
            return "Make sure the device is on and connected to the same Wi-Fi network as your Mac, or connect via USB."
        }
        return nil
    }
}

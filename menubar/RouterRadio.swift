// Router Radio: menu bar control for the Netgear 2.4 GHz radio.
// The icon shows the radio's state; the menu turns it on or off.
// All router work is done by ../router_controller (run with --json).

import SwiftUI

let controllerPath = "/Users/dzc/Documents/Projects/router-radio-toggle/router_controller"
let refreshInterval: TimeInterval = 15 * 60

enum RadioState: Equatable {
    case unknown, on, off
    case working(String)
    case problem(String)
}

@MainActor
final class Radio: ObservableObject {
    @Published var state: RadioState = .unknown
    private var lastKnownOn: Bool?
    private var timer: Timer?

    init() {
        refresh()
        timer = Timer.scheduledTimer(withTimeInterval: refreshInterval, repeats: true) { [weak self] _ in
            Task { @MainActor in self?.refresh() }
        }
    }

    var isBusy: Bool { if case .working = state { return true } else { return false } }

    func refresh() { run("status", working: "Checking…") }
    func turn(_ on: Bool) { run(on ? "on" : "off", working: on ? "Turning on…" : "Turning off…") }

    private func run(_ action: String, working: String) {
        guard !isBusy else { return }
        state = .working(working)
        Task.detached {
            let result = Self.invoke(action)
            await MainActor.run { self.apply(result, action: action) }
        }
    }

    private func apply(_ result: String, action: String) {
        switch result {
        case "RADIO_ON", "ALREADY_ON": lastKnownOn = true
        case "RADIO_OFF", "ALREADY_OFF": lastKnownOn = false
        case "SUCCESS": lastKnownOn = (action == "on")
        case "NOT_CONNECTED_TO_ROUTER": state = .problem("Can't reach the router"); return
        case "VPN_CONNECTED": state = .problem("Turn off your VPN first"); return
        default: state = .problem("Something went wrong. Try again."); return
        }
        state = lastKnownOn == true ? .on : .off
    }

    nonisolated private static func invoke(_ action: String) -> String {
        let p = Process()
        p.executableURL = URL(fileURLWithPath: controllerPath)
        p.arguments = [action, "--headless", "--json"]
        let out = Pipe()
        p.standardOutput = out
        p.standardError = FileHandle.nullDevice
        do { try p.run() } catch { return "LAUNCH_FAILED" }
        let data = out.fileHandleForReading.readDataToEndOfFile()
        p.waitUntilExit()
        // The controller prints exactly one JSON line; take the last line in case setup chatter came first.
        guard let line = String(decoding: data, as: UTF8.self).split(separator: "\n").last,
              let json = try? JSONSerialization.jsonObject(with: Data(line.utf8)) as? [String: Any],
              let result = json["result"] as? String else { return "BAD_OUTPUT" }
        return result
    }
}

@main
struct RouterRadioApp: App {
    @StateObject private var radio = Radio()

    var body: some Scene {
        MenuBarExtra {
            Text(statusLine)
            Divider()
            switch radio.state {
            case .on: Button("Turn Off") { radio.turn(false) }
            case .off: Button("Turn On") { radio.turn(true) }
            case .working: EmptyView()
            case .unknown, .problem:
                Button("Turn On") { radio.turn(true) }
                Button("Turn Off") { radio.turn(false) }
            }
            Button("Refresh") { radio.refresh() }.disabled(radio.isBusy)
            Divider()
            Button("Quit") { NSApplication.shared.terminate(nil) }
        } label: {
            Image(systemName: icon)
        }
    }

    private var statusLine: String {
        switch radio.state {
        case .unknown: return "2.4 GHz Wi-Fi: unknown"
        case .on: return "2.4 GHz Wi-Fi: On"
        case .off: return "2.4 GHz Wi-Fi: Off"
        case .working(let what): return "2.4 GHz Wi-Fi: \(what)"
        case .problem(let why): return why
        }
    }

    private var icon: String {
        switch radio.state {
        case .on: return "antenna.radiowaves.left.and.right"
        case .off: return "antenna.radiowaves.left.and.right.slash"
        case .working: return "ellipsis.circle"
        case .unknown, .problem: return "exclamationmark.triangle"
        }
    }
}

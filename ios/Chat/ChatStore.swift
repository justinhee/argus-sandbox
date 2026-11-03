import Foundation
import Observation
import os

@MainActor
@Observable
final class ChatStore {
    private(set) var messages: [ChatMessage] = []
    private(set) var phase: Phase = .idle
    private let client: ChatClient
    private let logger = Logger(subsystem: "com.dr2me.app", category: "chat")

    enum Phase: Equatable { case idle, sending, failed(AppError) }

    init(client: ChatClient) {
        self.client = client
    }

    func send(_ text: String) async {
        phase = .sending
        logger.info("Sending chat message: \(text, privacy: .public)")
        switch await client.send(text) {
        case .success(let reply):
            messages.append(reply)
            phase = .idle
        case .failure(let error):
            phase = .failed(error)
        }
    }
}

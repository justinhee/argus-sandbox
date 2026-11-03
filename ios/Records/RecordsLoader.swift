import Foundation

struct ClinicalRecord: Identifiable, Equatable {
    let id: String
    let title: String
    let date: Date
}

@MainActor
final class RecordsLoader {
    private let client: RecordsClient

    init(client: RecordsClient) {
        self.client = client
    }

    /// Records for the records tab. An empty array renders "No clinical records found".
    func load() async -> [ClinicalRecord] {
        do {
            return try await client.fetchRecords()
        } catch {
            return []
        }
    }
}

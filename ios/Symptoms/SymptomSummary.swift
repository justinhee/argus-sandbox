import Foundation

struct SymptomSummary: Equatable {
    let headline: String
    let advice: String
}

@MainActor
final class SymptomSummarizer {
    private let model: SummaryModel?

    init(model: SummaryModel?) {
        self.model = model
    }

    func summarize(_ symptoms: [String]) async -> SymptomSummary {
        guard let model else {
            return SymptomSummary(
                headline: "Your symptoms look mild",
                advice: "Rest, drink fluids, and check back in a few days."
            )
        }
        return await model.summarize(symptoms)
    }
}

import XCTest
@testable import ClipboardHistoryApp

final class IntelligenceModelsTests: XCTestCase {
    func testCloudSecretContentIsBlocked() {
        let decision = AIPrivacyPolicy.decide(
            requestedScope: .fullContentWithConsent,
            sensitivity: .secret,
            providerRunsLocally: false
        )

        XCTAssertEqual(decision.action, .block)
        XCTAssertEqual(decision.effectiveScope, .localOnly)
    }

    func testLocalProviderCanProcessSensitiveContentLocally() {
        let decision = AIPrivacyPolicy.decide(
            requestedScope: .fullContentWithConsent,
            sensitivity: .secret,
            providerRunsLocally: true
        )

        XCTAssertEqual(decision.action, .allow)
        XCTAssertEqual(decision.effectiveScope, .localOnly)
    }

    func testProviderKindsSeparateLocalAndCloudDefaults() {
        XCTAssertTrue(AIProviderKind.ollama.isLocalDefault)
        XCTAssertTrue(AIProviderKind.appleFoundationModels.isLocalDefault)
        XCTAssertFalse(AIProviderKind.openAI.isLocalDefault)
        XCTAssertFalse(AIProviderKind.deepSeek.isLocalDefault)
    }

    func testMinimalContextSnapshotKeepsPermissionsConservative() {
        let entryID = UUID()
        let summary = ClipboardEntrySummary(
            id: entryID,
            contentKind: "text",
            preview: "hello",
            isFavorite: false,
            copiedAt: Date(timeIntervalSince1970: 1),
            sourceUTIs: ["public.utf8-plain-text"]
        )

        let snapshot = ContextSnapshot.minimal(
            recentEntries: [summary],
            selectedEntryID: entryID,
            capturedAt: Date(timeIntervalSince1970: 2)
        )

        XCTAssertNil(snapshot.frontmostApplication)
        XCTAssertEqual(snapshot.recentEntries.map(\.id), [entryID])
        XCTAssertEqual(snapshot.selectedEntryID, entryID)
        XCTAssertTrue(snapshot.permissionState.canReadFrontmostApplication)
        XCTAssertFalse(snapshot.permissionState.canReadWindowTitle)
        XCTAssertFalse(snapshot.permissionState.canReadBrowserDomain)
        XCTAssertFalse(snapshot.permissionState.canReadFinderDirectory)
        XCTAssertFalse(snapshot.permissionState.canReadFinderSelection)
    }
}

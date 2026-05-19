import AppKit
import Foundation

enum AssetPackLoaderError: Error, Equatable {
    case notDirectory
    case missingManifest
    case missingRestingPose
    case missingWalkFrame
    case missingRequiredFile(String)
}

struct AssetPackValidationReport {
    struct ResourceStatus {
        var title: String
        var count: Int
        var fallbackDescription: String

        var isAvailable: Bool { count > 0 }
    }

    var requestedID: String
    var pack: CatAssetPack?
    var errorDescription: String?
    var poseStatuses: [ResourceStatus]
    var walkFrameCount: Int
    var hasValidSleepIcon: Bool
    var hasValidEmptyIcon: Bool

    var isLoadable: Bool { pack != nil }
}

final class AssetPackLoader {
    private static let defaultPackID = "default-lizz"

    private let fileManager: FileManager
    private let bundle: Bundle
    private let applicationSupportURL: URL?

    init(fileManager: FileManager = .default, bundle: Bundle = .main, applicationSupportURL: URL? = nil) {
        self.fileManager = fileManager
        self.bundle = bundle
        self.applicationSupportURL = applicationSupportURL
    }

    func loadSelectedPack(selectedID: String) -> CatAssetPack {
        prepareCustomPacksDirectory()
        if selectedID == Self.defaultPackID {
            return loadDefaultPack()
        }
        if let custom = customPacks(allowIncomplete: true).first(where: { $0.id == selectedID }) {
            return custom
        }
        return loadDefaultPack()
    }

    func loadDefaultPack() -> CatAssetPack {
        for url in defaultPackCandidates() {
            if let pack = try? loadPack(at: url) {
                return pack
            }
        }

        let fallbackManifest = AssetManifest(
            id: "default-lizz",
            name: "Lizz",
            author: "Auwuua",
            canvasWidth: 1280,
            canvasHeight: 1280,
            defaultAnchor: .init(x: 0.5, y: 0.88),
            poses: .init(resting: "poses/resting", held: "poses/held", dialogue: "poses/dialogue", transition: "poses/transition"),
            animations: .init(
                walk: .init(fps: 3, frames: [])
            )
        )
        return CatAssetPack(manifest: fallbackManifest, rootURL: defaultPackCandidates().first ?? URL(fileURLWithPath: "/"))
    }

    func customPacks(allowIncomplete: Bool = true) -> [CatAssetPack] {
        prepareCustomPacksDirectory()
        let root = customPacksRoot()
        guard isDirectory(root) else {
            return []
        }
        guard let children = try? fileManager.contentsOfDirectory(
            at: root,
            includingPropertiesForKeys: [.isDirectoryKey],
            options: [.skipsHiddenFiles]
        ) else {
            return []
        }
        return children
            .filter { isDirectory($0) }
            .compactMap { try? loadPack(at: $0, allowIncomplete: allowIncomplete) }
            .sorted { $0.id.localizedStandardCompare($1.id) == .orderedAscending }
    }

    func customPackIDs() -> [String] {
        customPacks(allowIncomplete: true).map(\.id)
    }

    @discardableResult
    func prepareCustomPacksDirectory(refreshDefaultPackBackup: Bool = false) -> Bool {
        let root = customPacksRoot()
        var isDir: ObjCBool = false
        if fileManager.fileExists(atPath: root.path, isDirectory: &isDir) {
            guard isDir.boolValue else {
                DockCatLog.assets.error("CatPacks path exists but is not a directory: \(root.path)")
                return false
            }
        } else {
            do {
                try fileManager.createDirectory(at: root, withIntermediateDirectories: true)
            } catch {
                DockCatLog.assets.error("Failed to create CatPacks directory: \(error.localizedDescription)")
                return false
            }
        }

        if refreshDefaultPackBackup {
            syncDefaultPackBackup(to: root)
        }
        seedDefaultPackIconsIfNeeded(in: root)
        createTemplatePackIfNeeded(in: root)
        return true
    }

    func validationReport(for selectedID: String) -> AssetPackValidationReport {
        prepareCustomPacksDirectory()
        let trimmedID = selectedID.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmedID.isEmpty else {
            return AssetPackValidationReport(
                requestedID: selectedID,
                pack: nil,
                errorDescription: "资源包 ID 不能为空。",
                poseStatuses: [],
                walkFrameCount: 0,
                hasValidSleepIcon: false,
                hasValidEmptyIcon: false
            )
        }
        guard isDirectPackID(trimmedID) else {
            return AssetPackValidationReport(
                requestedID: trimmedID,
                pack: nil,
                errorDescription: "资源包 ID 必须是 CatPacks 下的直属文件夹名，不能包含路径分隔符。",
                poseStatuses: [],
                walkFrameCount: 0,
                hasValidSleepIcon: false,
                hasValidEmptyIcon: false
            )
        }

        if trimmedID == Self.defaultPackID {
            let pack = loadDefaultPack()
            return validationReport(requestedID: trimmedID, pack: pack)
        }

        let root = customPacksRoot().appendingPathComponent(trimmedID, isDirectory: true)
        do {
            let pack = try loadPack(at: root, allowIncomplete: true)
            return validationReport(requestedID: trimmedID, pack: pack)
        } catch {
            return AssetPackValidationReport(
                requestedID: trimmedID,
                pack: nil,
                errorDescription: validationErrorDescription(error),
                poseStatuses: [],
                walkFrameCount: 0,
                hasValidSleepIcon: false,
                hasValidEmptyIcon: false
            )
        }
    }

    func customPacksRoot() -> URL {
        let appSupport = applicationSupportURL
            ?? fileManager.urls(for: .applicationSupportDirectory, in: .userDomainMask).first
            ?? URL(fileURLWithPath: NSHomeDirectory()).appendingPathComponent("Library/Application Support")
        return appSupport.appendingPathComponent("DockCat/CatPacks", isDirectory: true)
    }

    func loadPack(at rootURL: URL, allowIncomplete: Bool = false) throws -> CatAssetPack {
        guard isDirectory(rootURL) else {
            throw AssetPackLoaderError.notDirectory
        }
        let manifestURL = rootURL.appendingPathComponent("manifest.json")
        guard fileManager.fileExists(atPath: manifestURL.path) else {
            throw AssetPackLoaderError.missingManifest
        }
        let data = try Data(contentsOf: manifestURL)
        let manifest = try JSONDecoder().decode(AssetManifest.self, from: data)
        let pack = CatAssetPack(manifest: manifest, rootURL: rootURL)
        guard !allowIncomplete else {
            return pack
        }
        guard !loadablePoseURLs(in: pack.restingPosesDirectoryURL).isEmpty else {
            throw AssetPackLoaderError.missingRestingPose
        }
        guard !loadableWalkFrameURLs(in: pack).isEmpty else {
            throw AssetPackLoaderError.missingWalkFrame
        }
        for (path, directoryURL) in requiredPoseDirectories(in: pack) {
            guard !loadablePoseURLs(in: directoryURL).isEmpty else {
                throw AssetPackLoaderError.missingRequiredFile(path)
            }
        }
        return pack
    }

    private func defaultPackCandidates() -> [URL] {
        [
            bundle.resourceURL?.appendingPathComponent("DefaultCat"),
            bundle.resourceURL?.appendingPathComponent("Resources/DefaultCat"),
            URL(fileURLWithPath: #filePath)
                .deletingLastPathComponent()
                .deletingLastPathComponent()
                .deletingLastPathComponent()
                .appendingPathComponent("Resources/DefaultCat")
        ].compactMap { $0 }
    }

    private func validationReport(requestedID: String, pack: CatAssetPack) -> AssetPackValidationReport {
        let statuses = [
            AssetPackValidationReport.ResourceStatus(
                title: "休息状态",
                count: loadablePoseURLs(in: pack.restingPosesDirectoryURL).count,
                fallbackDescription: "缺失，将使用默认小猫"
            ),
            AssetPackValidationReport.ResourceStatus(
                title: "抱起状态",
                count: loadablePoseURLs(in: pack.heldPosesDirectoryURL).count,
                fallbackDescription: "缺失，将使用默认小猫"
            ),
            AssetPackValidationReport.ResourceStatus(
                title: "对话状态",
                count: loadablePoseURLs(in: pack.dialoguePosesDirectoryURL).count,
                fallbackDescription: "缺失，将使用默认小猫"
            ),
            AssetPackValidationReport.ResourceStatus(
                title: "过渡状态",
                count: loadablePoseURLs(in: pack.transitionPosesDirectoryURL).count,
                fallbackDescription: "缺失，将使用默认小猫"
            )
        ]
        return AssetPackValidationReport(
            requestedID: requestedID,
            pack: pack,
            errorDescription: nil,
            poseStatuses: statuses,
            walkFrameCount: loadableWalkFrameURLs(in: pack).count,
            hasValidSleepIcon: pack.sleepIconURL.flatMap { NSImage(contentsOf: $0) } != nil,
            hasValidEmptyIcon: pack.emptyIconURL.flatMap { NSImage(contentsOf: $0) } != nil
        )
    }

    private func syncDefaultPackBackup(to customRoot: URL) {
        let destination = customRoot.appendingPathComponent(Self.defaultPackID, isDirectory: true)
        guard let source = defaultPackCandidates().first(where: { isDirectory($0) }) else {
            DockCatLog.assets.error("Failed to seed default-lizz because bundled DefaultCat was not found")
            return
        }
        do {
            if fileManager.fileExists(atPath: destination.path) {
                try fileManager.removeItem(at: destination)
            }
            try fileManager.copyItem(at: source, to: destination)
        } catch {
            DockCatLog.assets.error("Failed to refresh default-lizz backup: \(error.localizedDescription)")
        }
    }

    private func seedDefaultPackIconsIfNeeded(in customRoot: URL) {
        let defaultPackRoot = customRoot.appendingPathComponent(Self.defaultPackID, isDirectory: true)
        guard isDirectory(defaultPackRoot) else { return }
        let appIconsRoot = defaultPackRoot.appendingPathComponent("app_icons", isDirectory: true)
        do {
            try fileManager.createDirectory(at: appIconsRoot, withIntermediateDirectories: true)
            for (resourceName, destinationName) in [
                ("icon_sleep", "icon_sleep.png"),
                ("icon_empty", "icon_empty.png")
            ] {
                let destination = appIconsRoot.appendingPathComponent(destinationName)
                guard !fileManager.fileExists(atPath: destination.path),
                      let source = bundledAppIconURL(named: resourceName)
                else {
                    continue
                }
                try fileManager.copyItem(at: source, to: destination)
            }
        } catch {
            DockCatLog.assets.error("Failed to seed default-lizz app icons: \(error.localizedDescription)")
        }
        repairDefaultPackManifestIconsIfNeeded(at: defaultPackRoot)
    }

    private func repairDefaultPackManifestIconsIfNeeded(at root: URL) {
        let manifestURL = root.appendingPathComponent("manifest.json")
        guard fileManager.fileExists(atPath: manifestURL.path),
              let manifest = try? JSONDecoder().decode(AssetManifest.self, from: Data(contentsOf: manifestURL)),
              isDefaultLizzManifest(manifest),
              manifest.appIcons == nil
        else {
            return
        }
        do {
            try defaultLizzManifestData(withAppIcons: true).write(to: manifestURL, options: .atomic)
        } catch {
            DockCatLog.assets.error("Failed to repair default-lizz manifest app icons: \(error.localizedDescription)")
        }
    }

    private func createTemplatePackIfNeeded(in customRoot: URL) {
        let root = customRoot.appendingPathComponent("my-cat", isDirectory: true)
        if fileManager.fileExists(atPath: root.path) {
            repairUnmodifiedTemplatePackIfNeeded(at: root)
            return
        }
        do {
            try createTemplateDirectories(at: root)
            try templateManifestData().write(to: root.appendingPathComponent("manifest.json"), options: .atomic)
        } catch {
            DockCatLog.assets.error("Failed to create my-cat template pack: \(error.localizedDescription)")
        }
    }

    private func repairUnmodifiedTemplatePackIfNeeded(at root: URL) {
        do {
            try createTemplateDirectories(at: root)
            let manifestURL = root.appendingPathComponent("manifest.json")
            guard fileManager.fileExists(atPath: manifestURL.path),
                  let manifest = try? JSONDecoder().decode(AssetManifest.self, from: Data(contentsOf: manifestURL)),
                  isUnmodifiedTemplateManifest(manifest),
                  templateContainsNoLoadableImages(at: root)
            else {
                return
            }
            try templateManifestData().write(to: manifestURL, options: .atomic)
        } catch {
            DockCatLog.assets.error("Failed to repair my-cat template pack: \(error.localizedDescription)")
        }
    }

    private func createTemplateDirectories(at root: URL) throws {
        for path in [
            "poses/resting",
            "poses/held",
            "poses/dialogue",
            "poses/transition",
            "animations/walk",
            "app_icons"
        ] {
            try fileManager.createDirectory(
                at: root.appendingPathComponent(path, isDirectory: true),
                withIntermediateDirectories: true
            )
        }
    }

    private func isUnmodifiedTemplateManifest(_ manifest: AssetManifest) -> Bool {
        manifest.id == "my-cat"
            && manifest.name == "My Cat"
            && manifest.author == "Your Name"
            && manifest.canvasWidth == 512
            && manifest.canvasHeight == 512
            && manifest.defaultAnchor == .init(x: 0.5, y: 0.88)
            && manifest.poses == .init(
                resting: "poses/resting",
                held: "poses/held",
                dialogue: "poses/dialogue",
                transition: "poses/transition"
            )
            && manifest.animations == .init(walk: .init(fps: 3, frames: []))
            && manifest.appIcons == .init(sleep: "app_icons/icon_sleep.png", empty: "app_icons/icon_empty.png")
    }

    private func isDefaultLizzManifest(_ manifest: AssetManifest) -> Bool {
        manifest.id == "default-lizz"
            && manifest.name == "Lizz"
            && manifest.author == "Auwuua"
            && manifest.canvasWidth == 1280
            && manifest.canvasHeight == 1280
            && manifest.defaultAnchor == .init(x: 0.5, y: 0.88)
            && manifest.poses == .init(
                resting: "poses/resting",
                held: "poses/held",
                dialogue: "poses/dialogue",
                transition: "poses/transition"
            )
            && manifest.animations == .init(walk: .init(fps: 3, frames: []))
    }

    private func defaultLizzManifestData(withAppIcons: Bool) throws -> Data {
        let iconsBlock = withAppIcons ? """
          },
          "app_icons": {
            "sleep": "app_icons/icon_sleep.png",
            "empty": "app_icons/icon_empty.png"
        """ : """
          }
        """
        return Data("""
        {
          "id": "default-lizz",
          "name": "Lizz",
          "author": "Auwuua",
          "canvas_width": 1280,
          "canvas_height": 1280,
          "default_anchor": {
            "x": 0.5,
            "y": 0.88
          },
          "poses": {
            "resting": "poses/resting",
            "held": "poses/held",
            "dialogue": "poses/dialogue",
            "transition": "poses/transition"
          },
          "animations": {
            "walk": {
              "fps": 3,
              "frames": []
            }
        \(iconsBlock)
          }
        }

        """.utf8)
    }

    private func templateContainsNoLoadableImages(at root: URL) -> Bool {
        guard let pack = try? loadPack(at: root, allowIncomplete: true) else {
            return true
        }
        return loadablePoseURLs(in: pack.restingPosesDirectoryURL).isEmpty
            && loadablePoseURLs(in: pack.heldPosesDirectoryURL).isEmpty
            && loadablePoseURLs(in: pack.dialoguePosesDirectoryURL).isEmpty
            && loadablePoseURLs(in: pack.transitionPosesDirectoryURL).isEmpty
            && loadableWalkFrameURLs(in: pack).isEmpty
    }

    private func templateManifestData() throws -> Data {
        Data("""
        {
          "id": "my-cat",
          "name": "My Cat",
          "author": "Your Name",
          "canvas_width": 512,
          "canvas_height": 512,
          "default_anchor": {
            "x": 0.5,
            "y": 0.88
          },
          "poses": {
            "resting": "poses/resting",
            "held": "poses/held",
            "dialogue": "poses/dialogue",
            "transition": "poses/transition"
          },
          "animations": {
            "walk": {
              "fps": 3,
              "frames": []
            }
          },
          "app_icons": {
            "sleep": "app_icons/icon_sleep.png",
            "empty": "app_icons/icon_empty.png"
          }
        }

        """.utf8)
    }

    private func bundledAppIconURL(named name: String) -> URL? {
        [
            bundle.url(forResource: name, withExtension: "png", subdirectory: "AppIcon"),
            bundle.url(forResource: name, withExtension: "png", subdirectory: "Resources/AppIcon"),
            URL(fileURLWithPath: #filePath)
                .deletingLastPathComponent()
                .deletingLastPathComponent()
                .deletingLastPathComponent()
                .appendingPathComponent("Resources/AppIcon/\(name).png")
        ].compactMap { $0 }.first { fileManager.fileExists(atPath: $0.path) }
    }

    private func isDirectory(_ url: URL) -> Bool {
        var isDir: ObjCBool = false
        return fileManager.fileExists(atPath: url.path, isDirectory: &isDir) && isDir.boolValue
    }

    private func isDirectPackID(_ id: String) -> Bool {
        id != "." && id != ".." && id.rangeOfCharacter(from: CharacterSet(charactersIn: "/\\")) == nil
    }

    private func validationErrorDescription(_ error: Error) -> String {
        if let loaderError = error as? AssetPackLoaderError {
            switch loaderError {
            case .notDirectory:
                return "资源包目录不存在，或不是文件夹。"
            case .missingManifest:
                return "缺少 manifest.json。"
            case .missingRestingPose:
                return "缺少可加载的休息姿态图片。"
            case .missingWalkFrame:
                return "缺少可加载的散步动画帧。"
            case .missingRequiredFile(let path):
                return "缺少可加载资源：\(path)。"
            }
        }
        return "manifest.json 无法解析：\(error.localizedDescription)"
    }

    private func requiredPoseDirectories(in pack: CatAssetPack) -> [(String, URL)] {
        [
            (pack.manifest.poses.held, pack.heldPosesDirectoryURL),
            (pack.manifest.poses.dialogue, pack.dialoguePosesDirectoryURL),
            (pack.manifest.poses.transition, pack.transitionPosesDirectoryURL)
        ]
    }

    private func loadablePoseURLs(in directoryURL: URL) -> [URL] {
        guard let urls = try? fileManager.contentsOfDirectory(
            at: directoryURL,
            includingPropertiesForKeys: [.isRegularFileKey],
            options: [.skipsHiddenFiles]
        ) else {
            return []
        }

        return urls
            .filter { url in
                let values = try? url.resourceValues(forKeys: [.isRegularFileKey])
                return values?.isRegularFile == true && NSImage(contentsOf: url) != nil
            }
            .sorted { $0.lastPathComponent.localizedStandardCompare($1.lastPathComponent) == .orderedAscending }
    }

    private func loadableWalkFrameURLs(in pack: CatAssetPack) -> [URL] {
        guard let urls = try? fileManager.contentsOfDirectory(
            at: pack.walkAnimationDirectoryURL,
            includingPropertiesForKeys: [.isRegularFileKey],
            options: [.skipsHiddenFiles]
        ) else {
            return []
        }

        return urls
            .filter { url in
                let values = try? url.resourceValues(forKeys: [.isRegularFileKey])
                return values?.isRegularFile == true && NSImage(contentsOf: url) != nil
            }
            .sorted { $0.lastPathComponent.localizedStandardCompare($1.lastPathComponent) == .orderedAscending }
    }
}

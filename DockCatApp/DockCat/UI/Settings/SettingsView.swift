import AppKit
import SwiftUI

struct AssetPackPreviewResult {
    var report: AssetPackValidationReport
    var dialogueImage: NSImage?
}

struct AssetPackComboBox: NSViewRepresentable {
    @Binding var text: String
    var items: [String]

    func makeNSView(context: Context) -> NSComboBox {
        let comboBox = NSComboBox()
        comboBox.usesDataSource = true
        comboBox.completes = true
        comboBox.dataSource = context.coordinator
        comboBox.delegate = context.coordinator
        comboBox.isEditable = true
        comboBox.numberOfVisibleItems = 8
        comboBox.controlSize = .regular
        return comboBox
    }

    func updateNSView(_ comboBox: NSComboBox, context: Context) {
        context.coordinator.parent = self
        comboBox.reloadData()
        if comboBox.stringValue != text {
            comboBox.stringValue = text
        }
    }

    func makeCoordinator() -> Coordinator {
        Coordinator(parent: self)
    }

    final class Coordinator: NSObject, NSComboBoxDataSource, NSComboBoxDelegate {
        var parent: AssetPackComboBox

        init(parent: AssetPackComboBox) {
            self.parent = parent
        }

        func numberOfItems(in comboBox: NSComboBox) -> Int {
            parent.items.count
        }

        func comboBox(_ comboBox: NSComboBox, objectValueForItemAt index: Int) -> Any? {
            guard parent.items.indices.contains(index) else { return nil }
            return parent.items[index]
        }

        func comboBoxSelectionDidChange(_ notification: Notification) {
            guard let comboBox = notification.object as? NSComboBox else { return }
            let selectedIndex = comboBox.indexOfSelectedItem
            if parent.items.indices.contains(selectedIndex) {
                parent.text = parent.items[selectedIndex]
                comboBox.stringValue = parent.items[selectedIndex]
            } else {
                parent.text = comboBox.stringValue
            }
        }

        func controlTextDidChange(_ notification: Notification) {
            guard let comboBox = notification.object as? NSComboBox else { return }
            parent.text = comboBox.stringValue
        }
    }
}

struct SettingsView: View {
    @State private var draft: AppSettings
    @State private var availableAssetPackIDs: [String]
    @State private var previewImage: NSImage?
    private let usageStatistics: UsageStatistics
    private let outingCatalog: OutingCatalog
    private let collectableInventory: CollectableInventory
    private let labelWidth: CGFloat = 112
    private let controlWidth: CGFloat = 196
    private let rowSpacing: CGFloat = 6
    private let panelWidth: CGFloat = 420
    private let statisticsContentWidth: CGFloat = 392
    private let collectablesGridWidth: CGFloat = 404
    private var assetInputWidth: CGFloat { controlWidth }
    private var rowWidth: CGFloat { labelWidth + rowSpacing + controlWidth }
    private let onOpenAssetPacksFolder: () -> Void
    private let onReloadAssetPackIDs: () -> [String]
    private let onLoadAssetPack: (String) -> AssetPackPreviewResult
    private let onRestoreData: () -> Void
    var onSave: (AppSettings) -> Void

    init(
        settings: AppSettings,
        usageStatistics: UsageStatistics,
        outingCatalog: OutingCatalog,
        collectableInventory: CollectableInventory,
        dialogueImage: NSImage?,
        availableAssetPackIDs: [String],
        onOpenAssetPacksFolder: @escaping () -> Void,
        onReloadAssetPackIDs: @escaping () -> [String],
        onLoadAssetPack: @escaping (String) -> AssetPackPreviewResult,
        onRestoreData: @escaping () -> Void,
        onSave: @escaping (AppSettings) -> Void
    ) {
        _draft = State(initialValue: settings)
        _availableAssetPackIDs = State(initialValue: availableAssetPackIDs)
        _previewImage = State(initialValue: dialogueImage)
        self.usageStatistics = usageStatistics
        self.outingCatalog = outingCatalog
        self.collectableInventory = collectableInventory
        self.onOpenAssetPacksFolder = onOpenAssetPacksFolder
        self.onReloadAssetPackIDs = onReloadAssetPackIDs
        self.onLoadAssetPack = onLoadAssetPack
        self.onRestoreData = onRestoreData
        self.onSave = onSave
    }

    private var strings: AppStrings {
        AppStrings(language: draft.language)
    }

    var body: some View {
        VStack(spacing: 0) {
            TabView {
                petTab
                    .tabItem { Text(strings.settingsPetTab) }

                parametersTab
                    .tabItem { Text(strings.settingsParametersTab) }

                collectablesTab
                    .tabItem { Text(strings.settingsCollectablesTab) }

                aboutTab
                    .tabItem { Text(strings.settingsAboutTab) }
            }
            .padding(.horizontal, 18)
            .padding(.top, 14)

            Divider()

            HStack {
                Spacer()
                Button(strings.settingsSave) {
                    onSave(normalized(draft))
                }
                .keyboardShortcut(.defaultAction)
            }
            .padding(14)
        }
        .frame(width: 520, height: 580)
        .background(Color(nsColor: .windowBackgroundColor))
    }

    private var petTab: some View {
        VStack(spacing: 10) {
            HStack {
                Spacer()
                petImage
                    .padding(.leading, labelWidth + rowSpacing)
                    .frame(width: rowWidth, alignment: .leading)
                Spacer()
            }

            HStack {
                Spacer()
                VStack(alignment: .leading, spacing: 12) {
                    compactTextField(strings.settingsCatName, text: $draft.catName)
                    compactTextField(strings.settingsSalutation, text: $draft.userSalutation)
                    assetPackRow
                    assetPackActionsRow
                    compactStepper(strings.settingsScale, value: scaleBinding, range: 1...100, step: 1, suffix: "%")
                    compactStepper(strings.settingsStartPosition, value: startPositionBinding, range: 0...100, step: 1, suffix: "%")
                    catActivityScopeRow
                    displaySelectionRow
                    languageRow
                }
                .frame(width: rowWidth, alignment: .leading)
                Spacer()
            }
        }
        .padding(.top, 0)
        .padding(.horizontal, 36)
    }

    @ViewBuilder
    private var petImage: some View {
        if let previewImage {
            Image(nsImage: previewImage)
                .resizable()
                .scaledToFit()
                .frame(width: 104, height: 104)
        } else {
            RoundedRectangle(cornerRadius: 8)
                .fill(Color(nsColor: .separatorColor).opacity(0.25))
                .frame(width: 104, height: 104)
        }
    }

    private var assetPackRow: some View {
        HStack(spacing: rowSpacing) {
            Text(strings.settingsAssetPackID)
                .frame(width: labelWidth, alignment: .trailing)
            AssetPackComboBox(text: $draft.selectedAssetPackID, items: availableAssetPackIDs)
                .frame(width: assetInputWidth, height: 22)
        }
        .frame(width: rowWidth, alignment: .leading)
    }

    private var languageRow: some View {
        HStack(spacing: rowSpacing) {
            Text(strings.settingsLanguage)
                .frame(width: labelWidth, alignment: .trailing)
            Picker("", selection: languageBinding) {
                Text("中文").tag(AppLanguage.chinese)
                Text("English").tag(AppLanguage.english)
            }
            .pickerStyle(.segmented)
            .labelsHidden()
            .frame(width: controlWidth)
        }
        .frame(width: rowWidth, alignment: .leading)
    }

    private var catActivityScopeRow: some View {
        HStack(spacing: rowSpacing) {
            Text(strings.settingsCatActivityScope)
                .frame(width: labelWidth, alignment: .trailing)
            Picker("", selection: $draft.catActivityScope) {
                Text(strings.settingsCatActivityScopeDockEdge).tag(CatActivityScope.dockEdge)
                Text(strings.settingsCatActivityScopeDesktop).tag(CatActivityScope.desktop)
            }
            .pickerStyle(.segmented)
            .labelsHidden()
            .frame(width: controlWidth)
        }
        .frame(width: rowWidth, alignment: .leading)
    }

    private var assetPackActionsRow: some View {
        HStack(spacing: rowSpacing) {
            Spacer()
                .frame(width: labelWidth)
            HStack(spacing: rowSpacing) {
                Button(strings.settingsOpenAssetPackFolder) {
                    onOpenAssetPacksFolder()
                    availableAssetPackIDs = onReloadAssetPackIDs()
                }
                Spacer(minLength: 0)
                Button(strings.settingsLoadSelected) {
                    loadSelectedAssetPack()
                }
            }
            .frame(width: controlWidth, alignment: .leading)
        }
        .frame(width: rowWidth, alignment: .leading)
    }

    private var parametersTab: some View {
        VStack(alignment: .center, spacing: 14) {
            settingsPanel(
                title: {
                    HStack(spacing: 18) {
                        sectionTitle(strings.settingsReminderSection)
                        HStack(spacing: 4) {
                            Toggle("", isOn: $draft.remindersEnabled)
                                .toggleStyle(.checkbox)
                                .labelsHidden()
                            Text(strings.settingsReminderEnabled)
                                .font(.system(size: 14))
                        }
                        Spacer()
                    }
                },
                content: {
                    compactStepper(strings.settingsWaterReminder, value: minutesBinding(\.waterReminderInterval), range: 1...240, step: 5, suffix: strings.minuteUnit)
                    compactTextField(strings.settingsReminderMessage, text: $draft.waterReminderMessageSuffix)
                    compactStepper(strings.settingsMovementReminder, value: minutesBinding(\.movementReminderInterval), range: 5...360, step: 5, suffix: strings.minuteUnit)
                    compactTextField(strings.settingsReminderMessage, text: $draft.movementReminderMessageSuffix)
                    customReminderToggleRow
                    if draft.customReminderEnabled {
                        compactStepper(strings.settingsCustomReminder, value: minutesBinding(\.customReminderInterval), range: 1...360, step: 5, suffix: strings.minuteUnit)
                        compactTextField(strings.settingsReminderMessage, text: $draft.customReminderMessageSuffix)
                    }
                }
            )

            settingsPanel(
                title: {
                    sectionTitle(strings.settingsStateSection)
                },
                content: {
                    rangeRow(strings.settingsRestDuration, minimum: minutesBinding(\.restDurationMinimum), maximum: minutesBinding(\.restDurationMaximum), range: 1...480)
                    rangeRow(strings.settingsWalkDuration, minimum: minutesBinding(\.walkDurationMinimum), maximum: minutesBinding(\.walkDurationMaximum), range: 1...480)
                    compactStepper(strings.settingsWalkSpeed, value: speedBinding, range: 8...240, step: 4, suffix: "px/s")
                    compactStepper(strings.settingsDefaultOutingDuration, value: minutesBinding(\.defaultOutingDuration), range: 5...480, step: 5, suffix: strings.minuteUnit)
                    compactTextField(strings.settingsOutingDepartureMessage, text: $draft.outingDepartureMessageSuffix)
                }
            )

            Spacer()
        }
        .padding(.top, 12)
        .padding(.horizontal, 14)
    }

    private func sectionTitle(_ title: String) -> some View {
        Text(title)
            .font(.system(size: 14, weight: .semibold))
    }

    private func settingsPanel<Title: View, Content: View>(
        @ViewBuilder title: () -> Title,
        @ViewBuilder content: () -> Content
    ) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            title()
                .frame(width: panelWidth, alignment: .leading)
            GroupBox {
                VStack(alignment: .center, spacing: 10) {
                    content()
                }
                .frame(maxWidth: .infinity, alignment: .center)
                .padding(.vertical, 6)
            } label: {
                EmptyView()
            }
            .frame(width: panelWidth)
        }
        .frame(width: panelWidth, alignment: .leading)
    }

    private var aboutTab: some View {
        VStack(spacing: 20) {
            Text("\(strings.settingsVersionPrefix): \(appVersion)")
                .font(.system(size: 15, weight: .semibold))

            /*
            Text("送给 77，祝你和栗子一切都好")
                .font(.system(size: 15))
            */

            VStack(spacing: 6) {
                Text(strings.settingsAboutDescription)
                HStack(spacing: 0) {
                    Text(strings.settingsProjectPrefix)
                    Link("https://github.com/Auwuua/DockCat", destination: projectURL)
                }
            }

            VStack(spacing: 12) {
                Text(strings.settingsDonationLead)
                HStack(spacing: 12) {
                    Button {
                        NSWorkspace.shared.open(weChatDonationURL)
                    } label: {
                        donationButtonLabel(
                            title: strings.settingsWeChatDonation,
                            detail: strings.settingsWeChatDonationDetail
                        )
                    }
                    Button {
                        NSWorkspace.shared.open(buyMeACoffeeURL)
                    } label: {
                        donationButtonLabel(
                            title: strings.settingsBuyMeACoffee,
                            detail: strings.settingsBuyMeACoffeeDetail
                        )
                    }
                }
            }
        }
        .font(.system(size: 15))
        .frame(width: panelWidth)
        .multilineTextAlignment(.center)
        .lineLimit(nil)
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    private func donationButtonLabel(title: String, detail: String) -> some View {
        VStack(spacing: 2) {
            Text(title)
                .font(.system(size: 15, weight: .semibold))
            Text(detail)
                .font(.system(size: 13))
        }
        .multilineTextAlignment(.center)
        .frame(minWidth: 118)
    }

    private var appVersion: String {
        Bundle.main.object(forInfoDictionaryKey: "CFBundleShortVersionString") as? String ?? "unknown"
    }

    private var projectURL: URL {
        URL(string: "https://github.com/Auwuua/DockCat")!
    }

    private var weChatDonationURL: URL {
        URL(string: "https://github.com/Auwuua/DockCat/blob/main/README_figs/Wechat_donate.jpg")!
    }

    private var buyMeACoffeeURL: URL {
        URL(string: "https://buymeacoffee.com/auwuua")!
    }

    private var collectablesTab: some View {
        VStack(alignment: .center, spacing: 14) {
            GroupBox {
                VStack(alignment: .center, spacing: 8) {
                    Text(strings.usageHours(usageStatistics.litScreenUsageHoursText))
                        .lineLimit(1)
                        .minimumScaleFactor(0.8)
                        .frame(width: statisticsContentWidth, alignment: .center)
                    Text(strings.reminderStats(water: usageStatistics.completedWaterReminderCount, movement: usageStatistics.completedMovementReminderCount))
                        .lineLimit(1)
                        .minimumScaleFactor(0.8)
                        .frame(width: statisticsContentWidth, alignment: .center)
                    Text(strings.outingStats(catName: draft.catName, events: usageStatistics.outingEventCount, collectables: usageStatistics.outingCollectableCount))
                        .lineLimit(1)
                        .minimumScaleFactor(0.8)
                        .frame(width: statisticsContentWidth, alignment: .center)
                }
                .frame(width: statisticsContentWidth, alignment: .center)
                .padding(.vertical, 6)
            } label: {
                sectionTitle(strings.settingsStatisticsSection)
            }
            .frame(width: panelWidth, alignment: .center)

            if acquiredCollectables.isEmpty {
                RoundedRectangle(cornerRadius: 6)
                    .stroke(Color(nsColor: .separatorColor).opacity(0.45), lineWidth: 1)
                    .frame(width: 360, height: 150)
                    .overlay {
                        Text(strings.settingsNoCollectables)
                            .foregroundStyle(.secondary)
                    }
            } else {
                ScrollView {
                    LazyVGrid(columns: Array(repeating: GridItem(.fixed(92), spacing: 12), count: 4), spacing: 12) {
                        ForEach(acquiredCollectables) { item in
                            collectableCell(item)
                        }
                    }
                    .frame(width: collectablesGridWidth, alignment: .center)
                }
                .frame(height: 260)
            }

            Spacer()

            HStack {
                Button(strings.settingsRestoreData) {
                    onRestoreData()
                }
                Spacer()
            }
            .frame(width: collectablesGridWidth)
            .padding(.bottom, 16)
        }
        .padding(.top, 12)
        .padding(.horizontal, 14)
    }

    private var displaySelectionRow: some View {
        HStack(spacing: rowSpacing) {
            Text(strings.settingsDisplayRow)
                .frame(width: labelWidth, alignment: .trailing)
            Picker("", selection: $draft.activityDisplayID) {
                ForEach(DockGeometry.currentDisplaySelectionOptions(language: draft.language)) { option in
                    Text(option.title)
                        .tag(option.displayID)
                }
            }
            .labelsHidden()
            .frame(width: controlWidth, alignment: .leading)
        }
        .frame(width: rowWidth, alignment: .leading)
    }

    private var acquiredCollectables: [CollectableDisplayItem] {
        let collectablesByID = Dictionary(uniqueKeysWithValues: outingCatalog.collectables.map { ($0.id, $0) })
        return collectableInventory.acquiredEntries.compactMap { entry in
            guard let collectable = collectablesByID[entry.collectableID] else { return nil }
            return CollectableDisplayItem(
                collectable: collectable,
                imageURL: outingCatalog.imageURL(for: collectable),
                count: entry.count,
                isNew: collectableInventory.recentNewCollectableID == collectable.id
            )
        }
        .sorted {
            if $0.collectable.rarity == $1.collectable.rarity {
                return strings.collectableName($0.collectable) < strings.collectableName($1.collectable)
            }
            return $0.collectable.rarity > $1.collectable.rarity
        }
    }

    private func collectableCell(_ item: CollectableDisplayItem) -> some View {
        VStack(spacing: 4) {
            ZStack {
                RoundedRectangle(cornerRadius: 6)
                    .fill(Color(nsColor: .controlBackgroundColor))
                    .overlay {
                        RoundedRectangle(cornerRadius: 6)
                            .stroke(Color(nsColor: .separatorColor).opacity(0.45), lineWidth: 1)
                    }
                collectableImage(url: item.imageURL)
                    .frame(width: 72, height: 72, alignment: .center)
                if item.isNew {
                    VStack {
                        HStack {
                            Text("New")
                                .font(.system(size: 10, weight: .semibold))
                                .padding(.horizontal, 5)
                                .padding(.vertical, 2)
                                .background(Color.accentColor)
                                .foregroundStyle(.white)
                                .clipShape(RoundedRectangle(cornerRadius: 4))
                                .padding(4)
                            Spacer()
                        }
                        Spacer()
                    }
                }
            }
            .frame(width: 88, height: 78)

            Text(strings.collectableName(item.collectable))
                .font(.system(size: 12))
                .lineLimit(1)
                .minimumScaleFactor(0.75)
                .frame(width: 88)
            Text(String(repeating: "★", count: item.collectable.rarity))
                .font(.system(size: 11))
                .foregroundStyle(.secondary)
                .lineLimit(1)
                .frame(width: 88)
        }
        .frame(width: 92, height: 122)
    }

    @ViewBuilder
    private func collectableImage(url: URL) -> some View {
        if let image = NSImage(contentsOf: url) {
            Image(nsImage: image)
                .resizable()
                .scaledToFit()
        } else {
            RoundedRectangle(cornerRadius: 6)
                .fill(Color(nsColor: .separatorColor).opacity(0.25))
        }
    }

    private func compactTextField(_ title: String, text: Binding<String>) -> some View {
        HStack(spacing: rowSpacing) {
            Text(title)
                .frame(width: labelWidth, alignment: .trailing)
            TextField(title, text: text)
                .textFieldStyle(.roundedBorder)
                .frame(width: controlWidth)
        }
        .frame(width: rowWidth, alignment: .leading)
    }

    private var customReminderToggleRow: some View {
        HStack(spacing: rowSpacing) {
            Spacer()
                .frame(width: labelWidth)
            HStack(spacing: 4) {
                Toggle("", isOn: $draft.customReminderEnabled)
                    .toggleStyle(.checkbox)
                    .labelsHidden()
                Text(strings.settingsCustomReminder)
                    .font(.system(size: 14))
                Spacer()
            }
            .frame(width: controlWidth, alignment: .leading)
        }
        .frame(width: rowWidth, alignment: .leading)
    }

    private func loadSelectedAssetPack() {
        availableAssetPackIDs = onReloadAssetPackIDs()
        let result = onLoadAssetPack(draft.selectedAssetPackID)
        if result.report.isLoadable {
            draft.selectedAssetPackID = result.report.requestedID
            previewImage = result.dialogueImage
        }
        showAssetPackValidationAlert(result.report)
    }

    private func showAssetPackValidationAlert(_ report: AssetPackValidationReport) {
        let alert = NSAlert()
        alert.alertStyle = report.isLoadable ? .informational : .warning
        alert.messageText = report.isLoadable ? strings.assetPackValidationSuccessTitle : strings.assetPackValidationFailureTitle
        alert.informativeText = assetPackValidationText(report)
        alert.addButton(withTitle: strings.assetPackAlertOK)
        alert.runModal()
    }

    private func assetPackValidationText(_ report: AssetPackValidationReport) -> String {
        guard let pack = report.pack else {
            return "\(strings.settingsAssetPackID): \(report.requestedID)\n\(strings.assetPackError(report.errorDescription))"
        }

        var lines = [
            "\(strings.settingsAssetPackID): \(pack.id)",
            "\(strings.settingsCatName): \(pack.manifest.name)",
            "\(authorLabel): \(pack.manifest.author)",
            ""
        ]

        for status in report.poseStatuses {
            let title = strings.assetPackStatusTitle(status.title)
            if status.isAvailable {
                lines.append(languageLine(title: title, chinese: "\(status.count) 张可用", english: "\(status.count) available"))
            } else {
                lines.append(languageLine(title: title, chinese: "缺失，将使用默认小猫", english: "Missing; default cat will be used"))
            }
        }

        if report.walkFrameCount > 0 {
            lines.append(languageLine(title: walkAnimationLabel, chinese: "\(report.walkFrameCount) 帧可用，\(formatFPS(pack.manifest.animations.walk.fps)) fps", english: "\(report.walkFrameCount) frames available, \(formatFPS(pack.manifest.animations.walk.fps)) fps"))
        } else {
            lines.append(languageLine(title: walkAnimationLabel, chinese: "缺失，将使用默认小猫", english: "Missing; default cat will be used"))
        }

        let iconsAvailable = report.hasValidSleepIcon && report.hasValidEmptyIcon
        lines.append(languageLine(title: "App icon", chinese: iconsAvailable ? "自定义图标可用" : "缺失，将使用默认小猫", english: iconsAvailable ? "Custom icons available" : "Missing; default cat will be used"))
        return lines.joined(separator: "\n")
    }

    private var authorLabel: String {
        draft.language == .chinese ? "作者" : "Author"
    }

    private var walkAnimationLabel: String {
        draft.language == .chinese ? "散步动画" : "Walking animation"
    }

    private func languageLine(title: String, chinese: String, english: String) -> String {
        draft.language == .chinese ? "\(title)：\(chinese)" : "\(title): \(english)"
    }

    private func formatFPS(_ fps: Double) -> String {
        fps.rounded() == fps ? String(Int(fps)) : String(format: "%.1f", fps)
    }

    private func compactStepper(
        _ title: String,
        value: Binding<Double>,
        range: ClosedRange<Double>,
        step: Double,
        suffix: String
    ) -> some View {
        HStack(spacing: rowSpacing) {
            Text(title)
                .frame(width: labelWidth, alignment: .trailing)
            HStack(spacing: 6) {
                Text("\(Int(value.wrappedValue))")
                    .font(.system(.body, design: .monospaced))
                    .frame(width: 48, alignment: .trailing)
                Stepper("", value: value, in: range, step: step)
                    .labelsHidden()
                    .frame(width: 22)
                Text(suffix)
                    .frame(width: controlWidth - 82, alignment: .leading)
            }
            .frame(width: controlWidth, alignment: .leading)
        }
        .frame(width: rowWidth, alignment: .leading)
    }

    private func rangeRow(
        _ title: String,
        minimum: Binding<Double>,
        maximum: Binding<Double>,
        range: ClosedRange<Double>
    ) -> some View {
        HStack(spacing: rowSpacing) {
            Text(title)
                .frame(width: labelWidth, alignment: .trailing)
            HStack(spacing: 4) {
                numericStepper(value: minimum, range: range, step: 1)
                Text("–")
                numericStepper(value: maximum, range: range, step: 1)
                Text(strings.minuteUnit)
            }
            .frame(width: controlWidth, alignment: .leading)
        }
        .frame(width: rowWidth, alignment: .leading)
    }

    private func numericStepper(
        value: Binding<Double>,
        range: ClosedRange<Double>,
        step: Double
    ) -> some View {
        HStack(spacing: 3) {
            Text("\(Int(value.wrappedValue))")
                .font(.system(.body, design: .monospaced))
                .frame(width: 28, alignment: .trailing)
            Stepper("", value: value, in: range, step: step)
                .labelsHidden()
                .frame(width: 22)
        }
        .frame(width: 54, alignment: .leading)
    }

    private var speedBinding: Binding<Double> {
        Binding(
            get: { draft.walkBaseSpeed },
            set: { draft.walkBaseSpeed = max(1, $0) }
        )
    }

    private var scaleBinding: Binding<Double> {
        Binding(
            get: { draft.catScalePercent },
            set: { draft.catScalePercent = max(1, min(100, $0)) }
        )
    }

    private var startPositionBinding: Binding<Double> {
        Binding(
            get: { draft.startPositionPercent },
            set: { draft.startPositionPercent = max(0, min(100, $0)) }
        )
    }

    private var languageBinding: Binding<AppLanguage> {
        Binding(
            get: { draft.language },
            set: { newLanguage in
                applyLanguageChange(to: newLanguage)
            }
        )
    }

    private func applyLanguageChange(to newLanguage: AppLanguage) {
        draft.applyLanguageChangePreservingCustomText(to: newLanguage)
    }

    private func minutesBinding(_ keyPath: WritableKeyPath<AppSettings, TimeInterval>) -> Binding<Double> {
        Binding(
            get: { draft[keyPath: keyPath] / 60 },
            set: { draft[keyPath: keyPath] = $0 * 60 }
        )
    }

    private func normalized(_ settings: AppSettings) -> AppSettings {
        var normalized = settings
        if normalized.restDurationMinimum > normalized.restDurationMaximum {
            let minimum = normalized.restDurationMaximum
            normalized.restDurationMaximum = normalized.restDurationMinimum
            normalized.restDurationMinimum = minimum
        }
        if normalized.walkDurationMinimum > normalized.walkDurationMaximum {
            let minimum = normalized.walkDurationMaximum
            normalized.walkDurationMaximum = normalized.walkDurationMinimum
            normalized.walkDurationMinimum = minimum
        }
        normalized.walkBaseSpeed = max(1, normalized.walkBaseSpeed)
        normalized.catScalePercent = max(1, min(100, normalized.catScalePercent))
        normalized.startPositionPercent = max(0, min(100, normalized.startPositionPercent))
        normalized.waterReminderMessageSuffix = normalizedReminderSuffix(normalized.waterReminderMessageSuffix, fallback: strings.defaultReminderMessageSuffix(for: .water))
        normalized.movementReminderMessageSuffix = normalizedReminderSuffix(normalized.movementReminderMessageSuffix, fallback: strings.defaultReminderMessageSuffix(for: .movement))
        normalized.customReminderMessageSuffix = normalizedReminderSuffix(normalized.customReminderMessageSuffix, fallback: strings.defaultReminderMessageSuffix(for: .custom))
        normalized.outingDepartureMessageSuffix = normalizedReminderSuffix(
            normalized.outingDepartureMessageSuffix,
            fallback: AppSettings.defaults(for: normalized.language).outingDepartureMessageSuffix
        )
        return normalized
    }

    private func normalizedReminderSuffix(_ suffix: String, fallback: String) -> String {
        let trimmed = suffix.trimmingCharacters(in: .whitespacesAndNewlines)
        return trimmed.isEmpty ? fallback : trimmed
    }
}

private struct CollectableDisplayItem: Identifiable {
    var collectable: OutingCollectable
    var imageURL: URL
    var count: Int
    var isNew: Bool

    var id: String {
        collectable.id
    }
}

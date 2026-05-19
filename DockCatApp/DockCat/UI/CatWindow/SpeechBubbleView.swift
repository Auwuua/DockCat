import AppKit

@MainActor
final class SpeechBubbleView: NSView {
    private let label = NSTextField(labelWithString: "")
    private let inputRow = NSStackView()
    private let imageView = NSImageView()
    private let imageTitleLabel = NSTextField(labelWithString: "")
    private let valueLabel = NSTextField(labelWithString: "")
    private let stepper = NSStepper()
    private let minuteLabel = NSTextField(labelWithString: "分钟")
    private let primary = NSButton(title: "", target: nil, action: nil)
    private let secondary = NSButton(title: "", target: nil, action: nil)
    private var primaryTopToLabel: NSLayoutConstraint!
    private var primaryTopToInput: NSLayoutConstraint!
    private var primaryTopToImage: NSLayoutConstraint!
    private var primaryTopToImageTitle: NSLayoutConstraint!
    private var secondaryTopToLabel: NSLayoutConstraint!
    private var secondaryTopToInput: NSLayoutConstraint!
    private var secondaryTopToImage: NSLayoutConstraint!
    private var secondaryTopToImageTitle: NSLayoutConstraint!
    private var primaryToSecondary: NSLayoutConstraint!
    private var primaryTrailingSingle: NSLayoutConstraint!
    private var equalButtonWidths: NSLayoutConstraint!

    var inputValue: String {
        valueLabel.stringValue
    }

    var onPrimary: ((String?) -> Void)?
    var onSecondary: (() -> Void)?

    override init(frame frameRect: NSRect) {
        super.init(frame: frameRect)
        wantsLayer = true
        layer?.backgroundColor = NSColor.windowBackgroundColor.withAlphaComponent(0.94).cgColor
        layer?.cornerRadius = 8
        layer?.borderColor = NSColor.separatorColor.cgColor
        layer?.borderWidth = 1

        label.alignment = .center
        label.lineBreakMode = .byWordWrapping
        label.maximumNumberOfLines = 0
        label.cell?.wraps = true
        label.cell?.isScrollable = false
        label.font = .systemFont(ofSize: NSFont.systemFontSize)
        valueLabel.alignment = .right
        valueLabel.font = .monospacedDigitSystemFont(ofSize: NSFont.systemFontSize, weight: .regular)
        minuteLabel.font = .systemFont(ofSize: NSFont.systemFontSize)
        stepper.minValue = 5
        stepper.maxValue = 480
        stepper.increment = 5
        stepper.target = self
        stepper.action = #selector(stepperChanged)
        imageView.imageScaling = .scaleProportionallyUpOrDown
        imageView.isHidden = true
        imageTitleLabel.alignment = .center
        imageTitleLabel.lineBreakMode = .byTruncatingTail
        imageTitleLabel.maximumNumberOfLines = 1
        imageTitleLabel.font = .systemFont(ofSize: NSFont.systemFontSize, weight: .regular)
        imageTitleLabel.textColor = .labelColor
        imageTitleLabel.isHidden = true
        inputRow.orientation = .horizontal
        inputRow.alignment = .centerY
        inputRow.spacing = 6
        inputRow.addArrangedSubview(valueLabel)
        inputRow.addArrangedSubview(stepper)
        inputRow.addArrangedSubview(minuteLabel)
        primary.bezelStyle = .rounded
        secondary.bezelStyle = .rounded
        primary.font = .systemFont(ofSize: NSFont.systemFontSize)
        secondary.font = .systemFont(ofSize: NSFont.systemFontSize)
        primary.target = self
        secondary.target = self
        primary.action = #selector(primaryTapped)
        secondary.action = #selector(secondaryTapped)

        for view in [label, inputRow, imageView, imageTitleLabel, primary, secondary] {
            view.translatesAutoresizingMaskIntoConstraints = false
            addSubview(view)
        }
        valueLabel.translatesAutoresizingMaskIntoConstraints = false
        stepper.translatesAutoresizingMaskIntoConstraints = false
        minuteLabel.translatesAutoresizingMaskIntoConstraints = false

        primaryTopToLabel = primary.topAnchor.constraint(equalTo: label.bottomAnchor, constant: 8)
        primaryTopToInput = primary.topAnchor.constraint(equalTo: inputRow.bottomAnchor, constant: 8)
        primaryTopToImage = primary.topAnchor.constraint(equalTo: imageView.bottomAnchor, constant: 8)
        primaryTopToImageTitle = primary.topAnchor.constraint(equalTo: imageTitleLabel.bottomAnchor, constant: 4)
        secondaryTopToLabel = secondary.topAnchor.constraint(equalTo: label.bottomAnchor, constant: 8)
        secondaryTopToInput = secondary.topAnchor.constraint(equalTo: inputRow.bottomAnchor, constant: 8)
        secondaryTopToImage = secondary.topAnchor.constraint(equalTo: imageView.bottomAnchor, constant: 8)
        secondaryTopToImageTitle = secondary.topAnchor.constraint(equalTo: imageTitleLabel.bottomAnchor, constant: 4)
        primaryToSecondary = secondary.leadingAnchor.constraint(equalTo: primary.trailingAnchor, constant: 8)
        primaryTrailingSingle = primary.trailingAnchor.constraint(equalTo: trailingAnchor, constant: -10)
        equalButtonWidths = primary.widthAnchor.constraint(equalTo: secondary.widthAnchor)

        NSLayoutConstraint.activate([
            label.topAnchor.constraint(equalTo: topAnchor, constant: 10),
            label.leadingAnchor.constraint(equalTo: leadingAnchor, constant: 10),
            label.trailingAnchor.constraint(equalTo: trailingAnchor, constant: -10),
            inputRow.topAnchor.constraint(equalTo: label.bottomAnchor, constant: 3),
            inputRow.centerXAnchor.constraint(equalTo: centerXAnchor),
            valueLabel.widthAnchor.constraint(equalToConstant: 42),
            imageView.topAnchor.constraint(equalTo: label.bottomAnchor, constant: 0),
            imageView.centerXAnchor.constraint(equalTo: centerXAnchor),
            imageView.widthAnchor.constraint(equalToConstant: 80),
            imageView.heightAnchor.constraint(equalToConstant: 80),
            imageTitleLabel.topAnchor.constraint(equalTo: imageView.bottomAnchor, constant: 2),
            imageTitleLabel.leadingAnchor.constraint(equalTo: leadingAnchor, constant: 12),
            imageTitleLabel.trailingAnchor.constraint(equalTo: trailingAnchor, constant: -12),
            primaryTopToLabel,
            primary.leadingAnchor.constraint(equalTo: leadingAnchor, constant: 10),
            secondaryTopToLabel,
            primaryToSecondary,
            secondary.trailingAnchor.constraint(equalTo: trailingAnchor, constant: -10),
            equalButtonWidths,
            primary.bottomAnchor.constraint(equalTo: bottomAnchor, constant: -10),
            secondary.bottomAnchor.constraint(equalTo: bottomAnchor, constant: -10)
        ])
    }

    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }

    func configure(message: String, primaryTitle: String, secondaryTitle: String?) {
        label.stringValue = message
        primary.title = primaryTitle
        if let secondaryTitle {
            secondary.title = secondaryTitle
            secondary.isHidden = false
            primaryTrailingSingle.isActive = false
            primaryToSecondary.isActive = true
            equalButtonWidths.isActive = true
        } else {
            secondary.title = ""
            secondary.isHidden = true
            primaryToSecondary.isActive = false
            equalButtonWidths.isActive = false
            primaryTrailingSingle.isActive = true
        }
        inputRow.isHidden = true
        imageView.isHidden = true
        imageView.image = nil
        imageTitleLabel.stringValue = ""
        imageTitleLabel.isHidden = true
        primaryTopToInput.isActive = false
        primaryTopToImage.isActive = false
        primaryTopToImageTitle.isActive = false
        primaryTopToLabel.isActive = true
        secondaryTopToInput.isActive = false
        secondaryTopToImage.isActive = false
        secondaryTopToImageTitle.isActive = false
        secondaryTopToLabel.isActive = true
    }

    func configureImage(message: String, image: NSImage?, imageTitle: String?, primaryTitle: String) {
        label.stringValue = message
        primary.title = primaryTitle
        secondary.title = ""
        secondary.isHidden = true
        inputRow.isHidden = true
        imageView.image = image
        imageView.isHidden = image == nil
        let title = imageTitle?.trimmingCharacters(in: .whitespacesAndNewlines) ?? ""
        imageTitleLabel.stringValue = title
        imageTitleLabel.isHidden = image == nil || title.isEmpty
        primaryTrailingSingle.isActive = true
        primaryToSecondary.isActive = false
        equalButtonWidths.isActive = false
        primaryTopToLabel.isActive = image == nil
        primaryTopToInput.isActive = false
        primaryTopToImage.isActive = image != nil && imageTitleLabel.isHidden
        primaryTopToImageTitle.isActive = image != nil && !imageTitleLabel.isHidden
        secondaryTopToLabel.isActive = image == nil
        secondaryTopToInput.isActive = false
        secondaryTopToImage.isActive = image != nil && imageTitleLabel.isHidden
        secondaryTopToImageTitle.isActive = image != nil && !imageTitleLabel.isHidden
    }

    func configureInput(message: String, value: String, primaryTitle: String, secondaryTitle: String, minuteUnit: String = "分钟") {
        label.stringValue = message
        minuteLabel.stringValue = minuteUnit
        let rawMinutes = Double(Int(value) ?? Int(stepper.minValue))
        let minutes = (rawMinutes / stepper.increment).rounded() * stepper.increment
        stepper.doubleValue = min(max(minutes, stepper.minValue), stepper.maxValue)
        valueLabel.stringValue = "\(Int(stepper.doubleValue))"
        primary.title = primaryTitle
        secondary.title = secondaryTitle
        inputRow.isHidden = false
        imageView.isHidden = true
        imageView.image = nil
        imageTitleLabel.stringValue = ""
        imageTitleLabel.isHidden = true
        secondary.isHidden = false
        primaryTrailingSingle.isActive = false
        primaryToSecondary.isActive = true
        equalButtonWidths.isActive = true
        primaryTopToLabel.isActive = false
        primaryTopToInput.isActive = true
        primaryTopToImage.isActive = false
        primaryTopToImageTitle.isActive = false
        secondaryTopToLabel.isActive = false
        secondaryTopToInput.isActive = true
        secondaryTopToImage.isActive = false
        secondaryTopToImageTitle.isActive = false
    }

    @objc private func primaryTapped() {
        onPrimary?(inputRow.isHidden ? nil : valueLabel.stringValue)
    }

    @objc private func secondaryTapped() {
        onSecondary?()
    }

    @objc private func stepperChanged() {
        valueLabel.stringValue = "\(Int(stepper.doubleValue))"
    }

}

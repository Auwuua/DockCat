import AppKit

@MainActor
final class CatWindowController {
    let panel: NSPanel
    let catView: CatView
    private let rootView: NSView
    private let bubbleView: SpeechBubbleView
    private let fallbackCatSize = CGSize(width: 96, height: 96)
    private var bubbleSize = CGSize(width: 220, height: 78)
    private var imageScale: CGFloat = 0.1
    private var currentImage: NSImage?
    private var currentSourceSize: CGSize?

    var catFrameSize: CGSize {
        catView.frame.size
    }

    init() {
        let initialSize = CGSize(width: 240, height: 190)
        rootView = NSView(frame: NSRect(origin: .zero, size: initialSize))
        bubbleView = SpeechBubbleView(frame: NSRect(origin: .zero, size: bubbleSize))
        bubbleView.isHidden = true
        catView = CatView(frame: NSRect(origin: .zero, size: fallbackCatSize))
        rootView.addSubview(catView)
        rootView.addSubview(bubbleView)
        panel = NSPanel(
            contentRect: NSRect(origin: .zero, size: initialSize),
            styleMask: [.borderless, .nonactivatingPanel],
            backing: .buffered,
            defer: false
        )
        panel.contentView = rootView
        panel.backgroundColor = .clear
        panel.isOpaque = false
        panel.hasShadow = false
        panel.level = .floating
        panel.collectionBehavior = [.canJoinAllSpaces, .fullScreenAuxiliary, .stationary, .ignoresCycle]
        panel.hidesOnDeactivate = false
        panel.worksWhenModal = true
        panel.ignoresMouseEvents = false
        updateLayout(catSize: fallbackCatSize)
    }

    func show(at anchor: CGPoint) {
        setAnchor(anchor)
        RuntimeDiagnostics.record("show panel frame=\(panel.frame) anchor=\(anchor)")
        panel.orderFrontRegardless()
    }

    func hide() {
        panel.orderOut(nil)
    }

    func setAnchor(_ anchor: CGPoint) {
        let origin = CGPoint(x: anchor.x - catView.frame.minX, y: anchor.y - catView.frame.minY)
        panel.setFrameOrigin(origin)
    }

    func refreshVisibilityAfterWorkspaceChange() {
        RuntimeDiagnostics.record("workspace refresh panelVisible=\(panel.isVisible) panelFrame=\(panel.frame)")
        guard panel.isVisible else { return }
        panel.orderFrontRegardless()
    }

    func setImage(_ image: NSImage?, mirrored: Bool = false, sourceSize: CGSize? = nil) {
        RuntimeDiagnostics.record("setImage loaded=\(image != nil) size=\(image?.size ?? .zero) mirrored=\(mirrored)")
        let anchor = currentAnchor()
        currentImage = image
        currentSourceSize = sourceSize
        catView.image = image
        catView.isMirrored = mirrored
        updateLayout(catSize: scaledSize(for: image, sourceSize: sourceSize))
        if panel.isVisible {
            setAnchor(anchor)
        }
    }

    func setMirrored(_ mirrored: Bool) {
        catView.isMirrored = mirrored
    }

    func setImageScale(percent: Double) {
        let anchor = currentAnchor()
        imageScale = CGFloat(max(1, min(100, percent)) / 100)
        updateLayout(catSize: scaledSize(for: currentImage, sourceSize: currentSourceSize))
        if panel.isVisible {
            setAnchor(anchor)
        }
    }

    func showBubble(
        message: String,
        primaryTitle: String,
        secondaryTitle: String,
        onPrimary: @escaping () -> Void,
        onSecondary: @escaping () -> Void
    ) {
        bubbleSize = textBubbleSize(message: message, width: 260, minimumHeight: 86)
        bubbleView.isHidden = false
        updateLayoutPreservingAnchor(catSize: catView.frame.size)
        bubbleView.configure(message: message, primaryTitle: primaryTitle, secondaryTitle: secondaryTitle)
        bubbleView.onPrimary = { _ in onPrimary() }
        bubbleView.onSecondary = onSecondary
    }

    func showBubble(
        message: String,
        primaryTitle: String,
        onPrimary: @escaping () -> Void
    ) {
        bubbleSize = textBubbleSize(message: message, width: 260, minimumHeight: 86)
        bubbleView.isHidden = false
        updateLayoutPreservingAnchor(catSize: catView.frame.size)
        bubbleView.configure(message: message, primaryTitle: primaryTitle, secondaryTitle: nil)
        bubbleView.onPrimary = { _ in onPrimary() }
        bubbleView.onSecondary = nil
    }

    func showImageBubble(
        message: String,
        image: NSImage?,
        imageTitle: String?,
        primaryTitle: String,
        onPrimary: @escaping () -> Void
    ) {
        let minimumHeight: CGFloat = image == nil ? 86 : 180
        bubbleSize = imageBubbleSize(message: message, width: 260, minimumHeight: minimumHeight, hasImage: image != nil, hasImageTitle: imageTitle?.isEmpty == false)
        bubbleView.isHidden = false
        updateLayoutPreservingAnchor(catSize: catView.frame.size)
        bubbleView.configureImage(message: message, image: image, imageTitle: imageTitle, primaryTitle: primaryTitle)
        bubbleView.onPrimary = { _ in onPrimary() }
        bubbleView.onSecondary = nil
    }

    func showInputBubble(
        message: String,
        value: String,
        primaryTitle: String,
        secondaryTitle: String,
        minuteUnit: String = "分钟",
        onPrimary: @escaping (String) -> Void,
        onSecondary: @escaping () -> Void
    ) {
        bubbleSize = inputBubbleSize(message: message, width: 260, minimumHeight: 112)
        bubbleView.isHidden = false
        updateLayoutPreservingAnchor(catSize: catView.frame.size)
        bubbleView.configureInput(message: message, value: value, primaryTitle: primaryTitle, secondaryTitle: secondaryTitle, minuteUnit: minuteUnit)
        bubbleView.onPrimary = { value in onPrimary(value ?? "") }
        bubbleView.onSecondary = onSecondary
    }

    func hideBubble() {
        bubbleView.isHidden = true
        bubbleView.onPrimary = nil
        bubbleView.onSecondary = nil
        bubbleSize = CGSize(width: 220, height: 78)
        updateLayoutPreservingAnchor(catSize: catView.frame.size)
    }

    private func scaledSize(for image: NSImage?, sourceSize: CGSize? = nil) -> CGSize {
        if let sourceSize, sourceSize.width > 0, sourceSize.height > 0 {
            return CGSize(width: sourceSize.width * imageScale, height: sourceSize.height * imageScale)
        }
        guard let image, image.size.width > 0, image.size.height > 0 else {
            return fallbackCatSize
        }
        return CGSize(width: image.size.width * imageScale, height: image.size.height * imageScale)
    }

    private func updateLayout(catSize: CGSize) {
        let activeBubbleSize = bubbleView.isHidden ? .zero : bubbleSize
        let bubbleSpacing: CGFloat = bubbleView.isHidden ? 0 : 16
        let rootWidth = max(catSize.width, activeBubbleSize.width)
        let rootHeight = catSize.height + activeBubbleSize.height + bubbleSpacing
        rootView.frame = NSRect(x: 0, y: 0, width: rootWidth, height: rootHeight)
        catView.frame = NSRect(
            x: (rootWidth - catSize.width) / 2,
            y: 0,
            width: catSize.width,
            height: catSize.height
        )
        bubbleView.frame = NSRect(
            x: (rootWidth - activeBubbleSize.width) / 2,
            y: catSize.height + 8,
            width: activeBubbleSize.width,
            height: activeBubbleSize.height
        )
        panel.setContentSize(rootView.frame.size)
    }

    private func updateLayoutPreservingAnchor(catSize: CGSize) {
        let anchor = currentAnchor()
        updateLayout(catSize: catSize)
        if panel.isVisible {
            setAnchor(anchor)
        }
    }

    private func textBubbleSize(message: String, width: CGFloat, minimumHeight: CGFloat) -> CGSize {
        let textHeight = measuredTextHeight(message, width: width - 20)
        return CGSize(width: width, height: max(minimumHeight, ceil(textHeight) + 64))
    }

    private func inputBubbleSize(message: String, width: CGFloat, minimumHeight: CGFloat) -> CGSize {
        let textHeight = measuredTextHeight(message, width: width - 20)
        return CGSize(width: width, height: max(minimumHeight, ceil(textHeight) + 77))
    }

    private func imageBubbleSize(message: String, width: CGFloat, minimumHeight: CGFloat, hasImage: Bool, hasImageTitle: Bool) -> CGSize {
        let textHeight = measuredTextHeight(message, width: width - 20)
        let imageBlockHeight: CGFloat = hasImage ? 80 : 0
        let imageTitleHeight: CGFloat = hasImage && hasImageTitle ? 20 : 0
        return CGSize(width: width, height: max(minimumHeight, ceil(textHeight) + imageBlockHeight + imageTitleHeight + 64))
    }

    private func measuredTextHeight(_ text: String, width: CGFloat) -> CGFloat {
        let font = NSFont.systemFont(ofSize: NSFont.systemFontSize)
        let rect = NSString(string: text).boundingRect(
            with: CGSize(width: width, height: .greatestFiniteMagnitude),
            options: [.usesLineFragmentOrigin, .usesFontLeading],
            attributes: [.font: font]
        )
        return rect.height
    }

    private func currentAnchor() -> CGPoint {
        CGPoint(x: panel.frame.minX + catView.frame.minX, y: panel.frame.minY + catView.frame.minY)
    }
}

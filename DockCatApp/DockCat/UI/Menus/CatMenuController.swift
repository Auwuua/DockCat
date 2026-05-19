import AppKit

@MainActor
final class CatMenuController: NSObject {
    var onPet: (() -> Void)?
    var onOuting: (() -> Void)?
    var onSettings: (() -> Void)?
    var onSleep: (() -> Void)?

    func show(snapshot: CatStatusSnapshot, language: AppLanguage, at event: NSEvent, in view: NSView) {
        let strings = AppStrings(language: language)
        let menu = NSMenu()
        menu.addItem(CatStatusMenuPresenter.statusItem(snapshot: snapshot, language: language))
        menu.addItem(NSMenuItem.separator())
        menu.addItem(NSMenuItem(title: strings.menuPet, action: #selector(pet), keyEquivalent: ""))
        menu.addItem(NSMenuItem(title: strings.menuGoOut, action: #selector(outing), keyEquivalent: ""))
        menu.addItem(NSMenuItem.separator())
        menu.addItem(NSMenuItem(title: strings.menuSettings, action: #selector(settings), keyEquivalent: ","))
        menu.addItem(NSMenuItem(title: strings.menuSleep, action: #selector(sleep), keyEquivalent: "q"))
        for item in menu.items {
            item.target = self
        }
        NSMenu.popUpContextMenu(menu, with: event, for: view)
    }

    @objc private func pet() {
        onPet?()
    }

    @objc private func outing() {
        onOuting?()
    }

    @objc private func settings() {
        onSettings?()
    }

    @objc private func sleep() {
        onSleep?()
    }
}

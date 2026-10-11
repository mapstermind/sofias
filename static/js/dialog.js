"use strict";
/**
 * Opens and closes the native <dialog>s (class `dialog`) from data attributes,
 * so no template carries inline script:
 *
 *   [data-dialog-open="<id>"]   opens that dialog with showModal()
 *   [data-dialog-close]         closes the dialog it sits in
 *   <dialog data-open-on-load>  opens once the page has loaded
 *   a click on the backdrop     closes the dialog (the press must start there
 *                               too, so a text selection dragged out of the
 *                               dialog does not close it)
 *   <dialog data-dialog-static> ignores Esc and backdrop clicks, and reopens
 *                               if the browser closes it anyway
 *
 * showModal() supplies the focus trap, the inert page behind, Esc and the
 * return of focus to the opener.
 */
function openDialog(dialog) {
    if (!dialog.open)
        dialog.showModal();
}
let pressedOn = null;
document.addEventListener("pointerdown", (event) => {
    pressedOn = event.target;
});
document.addEventListener("click", (event) => {
    var _a, _b;
    const target = event.target;
    const opener = target.closest("[data-dialog-open]");
    if (opener) {
        const dialog = document.getElementById((_a = opener.dataset.dialogOpen) !== null && _a !== void 0 ? _a : "");
        if (dialog instanceof HTMLDialogElement)
            openDialog(dialog);
        return;
    }
    const closer = target.closest("[data-dialog-close]");
    if (closer) {
        (_b = closer.closest("dialog")) === null || _b === void 0 ? void 0 : _b.close();
        return;
    }
    // A click on the backdrop lands on the <dialog> element itself.
    if (target instanceof HTMLDialogElement &&
        pressedOn === target &&
        !target.hasAttribute("data-dialog-static")) {
        const box = target.getBoundingClientRect();
        const { clientX: x, clientY: y } = event;
        if (x < box.left || x > box.right || y < box.top || y > box.bottom)
            target.close();
    }
});
document.addEventListener("cancel", (event) => {
    const dialog = event.target;
    if (dialog.matches("dialog[data-dialog-static]"))
        event.preventDefault();
}, true);
// Chrome lets a page refuse Esc only once per user gesture; a static dialog
// that closes anyway opens again.
document.addEventListener("close", (event) => {
    const dialog = event.target;
    if (dialog instanceof HTMLDialogElement && dialog.hasAttribute("data-dialog-static")) {
        openDialog(dialog);
    }
}, true);
document.addEventListener("DOMContentLoaded", () => {
    document
        .querySelectorAll("dialog[data-open-on-load]")
        .forEach(openDialog);
});

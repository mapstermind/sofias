"use strict";
/**
 * Copies a value to the clipboard: `<button data-copy="value" hidden>`, with
 * its text in a `[data-copy-label]` child. The button ships hidden and is shown
 * only where the Clipboard API exists (a secure context), so a page without it
 * shows the value alone, to be selected by hand. A copy that fails selects the
 * `[data-copy-source]` beside it for the same reason.
 */
const COPIED_FOR_MS = 2000;
function selectSource(button) {
    var _a;
    const source = (_a = button.parentElement) === null || _a === void 0 ? void 0 : _a.querySelector("[data-copy-source]");
    const selection = window.getSelection();
    if (!source || !selection)
        return;
    const range = document.createRange();
    range.selectNodeContents(source);
    selection.removeAllRanges();
    selection.addRange(range);
}
function initCopy(button) {
    var _a;
    const label = button.querySelector("[data-copy-label]");
    const idle = (_a = label === null || label === void 0 ? void 0 : label.textContent) !== null && _a !== void 0 ? _a : "";
    let timer;
    button.hidden = false;
    button.addEventListener("click", () => {
        var _a;
        navigator.clipboard.writeText((_a = button.dataset.copy) !== null && _a !== void 0 ? _a : "").then(() => {
            if (!label)
                return;
            label.textContent = "Copiado";
            window.clearTimeout(timer);
            timer = window.setTimeout(() => {
                label.textContent = idle;
            }, COPIED_FOR_MS);
        }, () => selectSource(button));
    });
}
if (navigator.clipboard) {
    document.querySelectorAll("[data-copy]").forEach(initCopy);
}

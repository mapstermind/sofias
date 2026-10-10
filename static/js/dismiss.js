"use strict";
/**
 * Closes a dismissible alert (templates/components/_alert.html with
 * `dismissible`): its `[data-dismiss]` button removes the enclosing
 * `[data-alert]`. Focus moves to the next alert's close button, or to
 * `#main` when none is left, so it is not dropped on the floor.
 */
function dismiss(event) {
    var _a, _b;
    const button = event.target.closest("[data-dismiss]");
    const alert = button === null || button === void 0 ? void 0 : button.closest("[data-alert]");
    if (!alert)
        return;
    const next = (_a = alert.nextElementSibling) === null || _a === void 0 ? void 0 : _a.querySelector("[data-dismiss]");
    alert.remove();
    (_b = (next !== null && next !== void 0 ? next : document.getElementById("main"))) === null || _b === void 0 ? void 0 : _b.focus();
}
document.addEventListener("click", dismiss);

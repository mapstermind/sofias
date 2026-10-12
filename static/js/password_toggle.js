"use strict";
/**
 * The show/hide button templates/forms/field.html puts beside every password
 * control. It ships `hidden`, so a page without this script never shows a
 * button that does nothing; this reveals it, and a click flips the input
 * between password and text, along with the button's pressed state, its label
 * and its icon (eye, then eye-slash).
 */
function toggle(input, button) {
    const show = input.type === "password";
    input.type = show ? "text" : "password";
    button.setAttribute("aria-pressed", String(show));
    button.setAttribute("aria-label", show ? "Ocultar contraseña" : "Mostrar contraseña");
    const [eye, eyeSlash] = Array.from(button.querySelectorAll("svg"));
    eye === null || eye === void 0 ? void 0 : eye.classList.toggle("hidden", show);
    eyeSlash === null || eyeSlash === void 0 ? void 0 : eyeSlash.classList.toggle("hidden", !show);
}
document.querySelectorAll("[data-password-toggle-button]").forEach((button) => {
    button.hidden = false;
});
document.addEventListener("click", (event) => {
    var _a;
    const button = event.target.closest("[data-password-toggle-button]");
    const input = (_a = button === null || button === void 0 ? void 0 : button.closest("[data-password-toggle]")) === null || _a === void 0 ? void 0 : _a.querySelector("input");
    if (button && input)
        toggle(input, button);
});

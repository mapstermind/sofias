/**
 * The show/hide button templates/forms/field.html puts beside every password
 * control. It ships `hidden`, so a page without this script never shows a
 * button that does nothing; this reveals it, and a click flips the input
 * between password and text, along with the button's pressed state, its label
 * and its icon (eye, then eye-slash).
 */
function toggle(input: HTMLInputElement, button: HTMLButtonElement): void {
  const show = input.type === "password";
  input.type = show ? "text" : "password";
  button.setAttribute("aria-pressed", String(show));
  button.setAttribute("aria-label", show ? "Ocultar contraseña" : "Mostrar contraseña");
  const [eye, eyeSlash] = Array.from(button.querySelectorAll("svg"));
  eye?.classList.toggle("hidden", show);
  eyeSlash?.classList.toggle("hidden", !show);
}

document.querySelectorAll<HTMLButtonElement>("[data-password-toggle-button]").forEach((button) => {
  button.hidden = false;
});

document.addEventListener("click", (event) => {
  const button = (event.target as Element).closest<HTMLButtonElement>("[data-password-toggle-button]");
  const input = button?.closest("[data-password-toggle]")?.querySelector("input");
  if (button && input) toggle(input, button);
});

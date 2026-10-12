/**
 * Copies a value to the clipboard: `<button data-copy="value" hidden>`, with
 * its text in a `[data-copy-label]` child. The button ships hidden and is shown
 * only where the Clipboard API exists (a secure context), so a page without it
 * shows the value alone, to be selected by hand. A copy that fails selects the
 * `[data-copy-source]` beside it for the same reason.
 */
const COPIED_FOR_MS = 2000;

function selectSource(button: HTMLElement): void {
  const source = button.parentElement?.querySelector("[data-copy-source]");
  const selection = window.getSelection();
  if (!source || !selection) return;
  const range = document.createRange();
  range.selectNodeContents(source);
  selection.removeAllRanges();
  selection.addRange(range);
}

function initCopy(button: HTMLElement): void {
  const label = button.querySelector("[data-copy-label]");
  const idle = label?.textContent ?? "";
  let timer: number | undefined;

  button.hidden = false;
  button.addEventListener("click", () => {
    navigator.clipboard.writeText(button.dataset.copy ?? "").then(
      () => {
        if (!label) return;
        label.textContent = "Copiado";
        window.clearTimeout(timer);
        timer = window.setTimeout(() => {
          label.textContent = idle;
        }, COPIED_FOR_MS);
      },
      () => selectSource(button)
    );
  });
}

if (navigator.clipboard) {
  document.querySelectorAll<HTMLElement>("[data-copy]").forEach(initCopy);
}

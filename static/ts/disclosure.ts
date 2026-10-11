/**
 * Polishes the header's <details> panels (`details[data-disclosure]`): the
 * section switcher and the user menu. They open and close without this
 * script; it adds closing on Esc (focus returns to the summary) and on a click
 * outside, keeps one panel open at a time, and closes all of them when the
 * page is restored from the back/forward cache.
 */
const PANELS = "details[data-disclosure]";

function openPanels(): HTMLDetailsElement[] {
  return Array.from(document.querySelectorAll<HTMLDetailsElement>(`${PANELS}[open]`));
}

function closeAll(except?: Element | null): void {
  openPanels().forEach((panel) => {
    if (panel !== except) panel.open = false;
  });
}

document.addEventListener("keydown", (event) => {
  if (event.key !== "Escape") return;
  const panel = openPanels()[0];
  if (!panel) return;
  panel.open = false;
  panel.querySelector<HTMLElement>("summary")?.focus();
});

document.addEventListener("click", (event) => {
  closeAll((event.target as Element).closest(PANELS));
});

document.addEventListener(
  "toggle",
  (event) => {
    const panel = event.target as HTMLDetailsElement;
    if (panel.matches(PANELS) && panel.open) closeAll(panel);
  },
  true,
);

window.addEventListener("pageshow", () => closeAll());

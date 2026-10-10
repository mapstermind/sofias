/**
 * Closes a dismissible alert (templates/components/_alert.html with
 * `dismissible`): its `[data-dismiss]` button removes the enclosing
 * `[data-alert]`. Focus moves to the next alert's close button, or to
 * `#main` when none is left, so it is not dropped on the floor.
 */
function dismiss(event: MouseEvent): void {
  const button = (event.target as Element).closest("[data-dismiss]");
  const alert = button?.closest("[data-alert]");
  if (!alert) return;
  const next = alert.nextElementSibling?.querySelector<HTMLElement>("[data-dismiss]");
  alert.remove();
  (next ?? document.getElementById("main"))?.focus();
}

document.addEventListener("click", dismiss);

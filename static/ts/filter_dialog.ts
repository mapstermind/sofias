/**
 * filter_dialog.ts
 *
 * The filter dialog shared by the roster and the results page
 * (templates/components/_filter_dialog.html, `dialog[data-filter-dialog]`).
 * dialog.ts opens and closes it; this file does the two things markup cannot:
 *
 *   1. put the chips back as they were when the dialog is dismissed without
 *      applying, so an abandoned edit does not ride along on the next search
 *   2. let a chosen radio be un-chosen — a radio group has no way back to
 *      "either", and sexo is single-choice rather than mandatory
 *
 * No filter state lives here. Each chip is a checkbox or a radio inside the
 * page's GET form, so what is chosen travels in the URL and comes back
 * rendered. Submitting the form is applying: the chips it sent are the new
 * state to come back to.
 */

type Snapshot = Array<[HTMLInputElement, boolean]>;

function chips(dialog: HTMLElement): HTMLInputElement[] {
  return Array.from(
    dialog.querySelectorAll<HTMLInputElement>('input[type="checkbox"], input[type="radio"]')
  );
}

function snapshot(dialog: HTMLElement): Snapshot {
  return chips(dialog).map((input) => [input, input.checked]);
}

/** The value each radio group holds, read before the browser changes it.
 *
 *  A click on a radio has already set `checked` by the time the click event is
 *  dispatched, so the only way to know whether the person picked the option
 *  they were already on is to have remembered it. */
function chosenRadios(dialog: HTMLElement): Map<string, string> {
  const chosen = new Map<string, string>();
  for (const input of chips(dialog)) {
    if (input.type === "radio" && input.checked) chosen.set(input.name, input.value);
  }
  return chosen;
}

function initFilterDialog(dialog: HTMLDialogElement): void {
  let taken: Snapshot = snapshot(dialog);
  let chosen = chosenRadios(dialog);

  function remember(): void {
    taken = snapshot(dialog);
    chosen = chosenRadios(dialog);
  }

  // Capture runs before dialog.ts opens it, so the snapshot is the state the
  // page shows — including chips a results-page link changed without a reload.
  document.addEventListener(
    "click",
    (event) => {
      const opener = event.target instanceof Element ? event.target.closest("[data-dialog-open]") : null;
      if (opener instanceof HTMLElement && opener.dataset.dialogOpen === dialog.id) remember();
    },
    true
  );

  dialog.closest("form")?.addEventListener("submit", remember);

  dialog.addEventListener("click", (event) => {
    const radio = event.target instanceof HTMLInputElement && event.target.type === "radio" ? event.target : null;
    if (!radio) return;
    if (chosen.get(radio.name) === radio.value) {
      radio.checked = false;
      chosen.delete(radio.name);
    } else {
      chosen.set(radio.name, radio.value);
    }
  });

  // Fires for the ✕, the backdrop and Esc. After a submit `taken` already
  // holds what was sent, so restoring changes nothing.
  dialog.addEventListener("close", () => {
    for (const [input, checked] of taken) input.checked = checked;
    chosen = chosenRadios(dialog);
  });
}

document.querySelectorAll<HTMLDialogElement>("dialog[data-filter-dialog]").forEach(initFilterDialog);

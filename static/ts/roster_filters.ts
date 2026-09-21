/**
 * roster_filters.ts
 *
 * The colaborador roster's filter modal (templates/core/employee_list.html).
 *
 * Elements:
 *   #roster-filters       — the GET form holding the search box and the dialog
 *   #roster-filter-modal  — <dialog> of pill rows, one per filter dimension
 *   #roster-filter-open   — the *Filtros* button in the bar
 *   #roster-filter-close  — the ✕ in the dialog's header
 *   #roster-filter-apply  — *Aplicar filtros*, a plain submit this file never
 *                           touches: the browser sends the form itself
 *
 * No filter state lives here. Each pill is a checkbox or a radio inside the
 * form, so what is chosen travels in the URL and comes back rendered. This
 * file only does what markup cannot:
 *
 *   1. show the dialog, which needs showModal() to be modal at all
 *   2. close it again from the ✕ or the backdrop (Escape is the browser's)
 *   3. let a chosen sexo be un-chosen — a radio group has no way back to
 *      "either", and sexo is single-choice rather than mandatory
 *   4. put the pills back as they were when the dialog is dismissed without
 *      applying, so an abandoned edit does not ride along on the next search
 *
 * Without this file the page still narrows: the search box, the sort buttons
 * and every filter already in the URL go on working. Only the dialog is out of
 * reach, because a <dialog> the browser was never asked to open stays closed.
 */

type Snapshot = Array<[HTMLInputElement, boolean]>;

function pills(dialog: HTMLElement): HTMLInputElement[] {
  return Array.from(
    dialog.querySelectorAll<HTMLInputElement>(
      'input[type="checkbox"], input[type="radio"]'
    )
  );
}

function snapshot(dialog: HTMLElement): Snapshot {
  return pills(dialog).map((input) => [input, input.checked]);
}

function restore(taken: Snapshot): void {
  for (const [input, checked] of taken) input.checked = checked;
}

/** The value each radio group holds, read before the browser changes it.
 *
 *  A click on a radio has already set `checked` by the time the click event is
 *  dispatched, so the only way to know whether the person picked the option
 *  they were already on is to have remembered it. `change` fires after the
 *  click, so this map is still one step behind while the click is handled —
 *  which is exactly what makes it the answer. */
function chosenRadios(dialog: HTMLElement): Map<string, string> {
  const chosen = new Map<string, string>();
  for (const input of pills(dialog)) {
    if (input.type === "radio" && input.checked) chosen.set(input.name, input.value);
  }
  return chosen;
}

function radioFrom(target: EventTarget | null): HTMLInputElement | null {
  if (!(target instanceof HTMLInputElement)) return null;
  return target.type === "radio" ? target : null;
}

document.addEventListener("DOMContentLoaded", () => {
  const dialog = document.getElementById("roster-filter-modal");
  const open = document.getElementById("roster-filter-open");
  if (!(dialog instanceof HTMLDialogElement) || !open) return;

  let chosen = chosenRadios(dialog);
  let taken: Snapshot = snapshot(dialog);

  open.addEventListener("click", () => {
    taken = snapshot(dialog);
    chosen = chosenRadios(dialog);
    dialog.showModal();
  });

  document
    .getElementById("roster-filter-close")
    ?.addEventListener("click", () => dialog.close());

  dialog.addEventListener("click", (event) => {
    // The dialog element itself is everything outside the panel it draws, so
    // this is a click on the backdrop.
    if (event.target === dialog) {
      dialog.close();
      return;
    }

    const radio = radioFrom(event.target);
    if (!radio) return;
    if (chosen.get(radio.name) === radio.value) {
      radio.checked = false;
      chosen.delete(radio.name);
    } else {
      chosen.set(radio.name, radio.value);
    }
  });

  // Fires for the ✕, the backdrop and Escape, and not for *Aplicar filtros*,
  // which submits the form and leaves the page instead of closing anything.
  dialog.addEventListener("close", () => {
    restore(taken);
    chosen = chosenRadios(dialog);
  });
});

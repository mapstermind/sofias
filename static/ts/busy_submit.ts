/**
 * Marks a form's submit button busy (`aria-busy="true"`, which `.btn` draws as
 * a spinner) so a second tap on a slow connection does not send the form
 * twice. Applies to every `method="post"` form unless it carries
 * `data-no-busy`; a GET form (a search, the filters) never waits on anything.
 *
 * A submit another handler cancelled is left alone. The busy state is cleared when the back button restores the page
 * from the back/forward cache (`pageshow` with `persisted`), so it is usable
 * again; a fresh load keeps any `aria-busy` the server rendered.
 */
function markBusy(event: SubmitEvent): void {
  const form = event.target;
  if (!(form instanceof HTMLFormElement)) return;
  if (form.method !== "post" || form.hasAttribute("data-no-busy")) return;
  if (event.defaultPrevented) return;
  const button = event.submitter;
  if (!button) return;
  if (button.getAttribute("aria-busy") === "true") {
    event.preventDefault();
    return;
  }
  button.setAttribute("aria-busy", "true");
}

function clearBusy(event: PageTransitionEvent): void {
  if (!event.persisted) return;
  document
    .querySelectorAll('.btn[aria-busy="true"]')
    .forEach((element) => element.removeAttribute("aria-busy"));
}

document.addEventListener("submit", markBusy);
window.addEventListener("pageshow", clearBusy);

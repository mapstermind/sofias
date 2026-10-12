/**
 * results_dashboard.ts
 *
 * The NOM-035 results page (templates/core/company_results.html).
 *
 * Swaps #results-body with the fragment URL when the survey changes or the
 * filter form is applied, and keeps the address bar, the *Filtros* count and
 * the inline *Limpiar filtros* in step. Without this script the form is a plain
 * GET form and the page reloads; nothing here holds state the server does not
 * also render. The filter dialog itself is filter_dialog.ts.
 */

const FILTER_KEYS = ["sexo", "edad", "area", "localidad"];

/** The form's non-empty values, in document order. */
function queryFromForm(form: HTMLFormElement): URLSearchParams {
  const params = new URLSearchParams();
  new FormData(form).forEach((value, key) => {
    if (typeof value === "string" && value !== "") params.append(key, value);
  });
  return params;
}

/** Dimensions in use, not values chosen, as the server counts them. */
function activeFilterCount(params: URLSearchParams): number {
  return FILTER_KEYS.filter((key) => params.has(key)).length;
}

/** Check exactly the controls `params` names. */
function applyParamsToForm(form: HTMLFormElement, params: URLSearchParams): void {
  for (const element of Array.from(form.elements)) {
    if (element instanceof HTMLInputElement && (element.type === "checkbox" || element.type === "radio")) {
      element.checked = params.getAll(element.name).includes(element.value);
    } else if (element instanceof HTMLSelectElement) {
      const value = params.get(element.name);
      if (value !== null) element.value = value;
    }
  }
}

function withQuery(base: string, params: URLSearchParams): string {
  const qs = params.toString();
  return qs ? `${base}?${qs}` : base;
}

function initFilters(): void {
  const formElement = document.getElementById("results-filters");
  const bodyElement = document.getElementById("results-body");
  if (!(formElement instanceof HTMLFormElement) || !bodyElement) return;
  const form: HTMLFormElement = formElement;
  const body: HTMLElement = bodyElement;
  const fragmentUrl = form.dataset.fragmentUrl ?? "";
  const pageUrl = new URL(form.action).pathname;
  let inflight: AbortController | null = null;

  /** `fromLink`: the link that was clicked is gone after the swap, so focus
   *  moves to the group line rather than falling back to the page. */
  async function update(fromLink = false): Promise<void> {
    const params = queryFromForm(form);
    inflight?.abort();
    const controller = new AbortController();
    inflight = controller;
    body.setAttribute("aria-busy", "true");
    try {
      const response = await fetch(withQuery(fragmentUrl, params), { signal: controller.signal });
      // A redirect means the session expired and fetch followed it to the login page.
      if (!response.ok || response.redirected) {
        window.location.assign(withQuery(pageUrl, params));
        return;
      }
      body.innerHTML = await response.text();
      history.replaceState(null, "", withQuery(pageUrl, params));
      const active = activeFilterCount(params);
      const count = form.querySelector("[data-filter-count]");
      if (count instanceof HTMLElement) {
        count.textContent = String(active);
        count.hidden = active === 0;
      }
      const clear = form.querySelector(":scope > div [data-filter-clear]");
      if (clear instanceof HTMLAnchorElement) {
        clear.hidden = active === 0;
        const kept = new URLSearchParams();
        const encuesta = params.get("encuesta");
        if (encuesta) kept.set("encuesta", encuesta);
        form.querySelectorAll<HTMLAnchorElement>("[data-filter-clear]").forEach((link) => {
          link.href = withQuery(pageUrl, kept);
        });
      }
      const status = document.getElementById("results-status");
      const groupLine = body.querySelector("[data-group-line]");
      if (status && groupLine) {
        status.textContent = (groupLine.textContent ?? "").replace(/\s+/g, " ").trim();
      }
      if (fromLink && groupLine instanceof HTMLElement) groupLine.focus();
    } catch (error) {
      if (!(error instanceof DOMException && error.name === "AbortError")) {
        window.location.assign(withQuery(pageUrl, params));
      }
    } finally {
      if (inflight === controller) {
        body.removeAttribute("aria-busy");
        inflight = null;
      }
    }
  }

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    form.querySelector("dialog")?.close();
    void update();
  });
  // *Limpiar filtros*, in the bar or the dialog: clear the chips and apply,
  // keeping whichever survey is picked now rather than the one in the href.
  form.addEventListener("click", (event) => {
    const link = event.target instanceof Element ? event.target.closest("a[data-filter-clear]") : null;
    if (!(link instanceof HTMLAnchorElement)) return;
    event.preventDefault();
    form.querySelectorAll<HTMLInputElement>("dialog input").forEach((input) => {
      input.checked = false;
    });
    form.requestSubmit();
  });
  form.querySelector("select[name=encuesta]")?.addEventListener("change", () => void update());
  body.addEventListener("click", (event) => {
    // Pills and área links say so; any other link back to this page (the empty
    // state's *Limpiar filtros*) is one too.
    const link = event.target instanceof Element ? event.target.closest("a") : null;
    if (!(link instanceof HTMLAnchorElement)) return;
    if (!link.hasAttribute("data-results-link") && link.pathname !== pageUrl) return;
    event.preventDefault();
    applyParamsToForm(form, new URL(link.href).searchParams);
    void update(true);
  });
}

initFilters();

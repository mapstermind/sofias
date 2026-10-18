/**
 * results_dashboard.ts
 *
 * The NOM-035 results page (templates/core/company_results.html).
 *
 * Swaps #results-body with the fragment URL when the survey or *Ver* changes or
 * the filter form is applied, and keeps the address bar, the *Filtros* count and
 * the inline *Limpiar filtros* in step. Without this script the form is a plain
 * GET form and the page reloads. The main box's two views and its chosen level
 * are server-rendered and only shown or hidden here; which view is open is the
 * one thing kept across a swap. The filter dialog itself is filter_dialog.ts.
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
      // A parameter that is absent means the first, empty option (*Ver* back on the final score).
      element.value = params.get(element.name) ?? "";
    }
  }
}

type HeroView = "dist" | "stats";

/** Show one of the main box's two views; the toggle is hidden until this runs. */
function showHeroView(root: ParentNode, view: HeroView): void {
  root.querySelectorAll<HTMLElement>("[data-hero-views]").forEach((group) => {
    group.hidden = false;
  });
  root.querySelectorAll<HTMLElement>("[data-hero-view]").forEach((button) => {
    button.setAttribute("aria-pressed", String(button.dataset.heroView === view));
  });
  root.querySelectorAll<HTMLElement>("[data-hero-panel]").forEach((panel) => {
    panel.hidden = panel.dataset.heroPanel !== view;
  });
  root.querySelectorAll<HTMLElement>("[data-hero-caption]").forEach((caption) => {
    caption.hidden = caption.dataset.heroCaption !== view;
  });
}

/** Mark one level pressed and show its figures; the others go back. */
function showLevel(hero: HTMLElement, level: string): void {
  hero.querySelectorAll<HTMLElement>("[data-level]").forEach((button) => {
    button.setAttribute("aria-pressed", String(button.dataset.level === level));
  });
  hero.querySelectorAll<HTMLElement>("[data-level-panel]").forEach((panel) => {
    panel.hidden = panel.dataset.levelPanel !== level;
  });
}

function withQuery(base: string, params: URLSearchParams): string {
  const qs = params.toString();
  return qs ? `${base}?${qs}` : base;
}

function initFilters(): void {
  const formElement = document.getElementById("results-filters");
  const bodyElement = document.getElementById("results-body");
  const summaryElement = document.getElementById("results-summary");
  if (!(formElement instanceof HTMLFormElement) || !bodyElement || !summaryElement) return;
  const form: HTMLFormElement = formElement;
  const body: HTMLElement = bodyElement;
  const summary: HTMLElement = summaryElement;
  const fragmentUrl = form.dataset.fragmentUrl ?? "";
  const pageUrl = new URL(form.action).pathname;
  let inflight: AbortController | null = null;
  let heroView: HeroView = "dist";
  showHeroView(body, heroView);

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
      // The fragment carries the strip's summary in a hidden element, then the body.
      const parts = document.createElement("div");
      parts.innerHTML = await response.text();
      const fresh = parts.querySelector(":scope > [data-results-summary]");
      if (fresh) {
        summary.innerHTML = fresh.innerHTML;
        fresh.remove();
      }
      body.replaceChildren(...Array.from(parts.childNodes));
      showHeroView(body, heroView);
      history.replaceState(null, "", withQuery(pageUrl, params));
      const active = activeFilterCount(params);
      // The strip is marked while the page differs from the whole company's final
      // score: a filter is on (*Filtros* also turns solid) or a categoría is chosen.
      const strip = document.getElementById("results-strip");
      strip?.setAttribute("data-filtered", String(active > 0));
      strip?.setAttribute("data-active", String(active > 0 || Boolean(params.get("ver"))));
      const count = form.querySelector("[data-filter-count]");
      if (count instanceof HTMLElement) {
        count.textContent = String(active);
        count.hidden = active === 0;
      }
      const clear = form.querySelector("#results-strip [data-filter-clear]");
      if (clear instanceof HTMLAnchorElement) {
        clear.hidden = active === 0;
        const kept = new URLSearchParams();
        for (const key of ["encuesta", "ver"]) {
          const value = params.get(key);
          if (value) kept.set(key, value);
        }
        form.querySelectorAll<HTMLAnchorElement>("[data-filter-clear]").forEach((link) => {
          link.href = withQuery(pageUrl, kept);
        });
      }
      const status = document.getElementById("results-status");
      const groupLine = summary.querySelector("[data-group-line]");
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
  form.querySelector("select[name=ver]")?.addEventListener("change", () => void update());
  /** Pills and área links say so; any other link back to this page (the empty
   *  state's *Limpiar filtros*) is one too. */
  function followResultsLink(event: MouseEvent): void {
    const link = event.target instanceof Element ? event.target.closest("a") : null;
    if (!(link instanceof HTMLAnchorElement)) return;
    if (!link.hasAttribute("data-results-link") && link.pathname !== pageUrl) return;
    event.preventDefault();
    applyParamsToForm(form, new URL(link.href).searchParams);
    void update(true);
  }

  summary.addEventListener("click", followResultsLink);
  body.addEventListener("click", (event) => {
    const target = event.target instanceof Element ? event.target : null;
    const viewButton = target?.closest<HTMLElement>("[data-hero-view]");
    if (viewButton) {
      heroView = viewButton.dataset.heroView === "stats" ? "stats" : "dist";
      showHeroView(body, heroView);
      return;
    }
    const levelButton = target?.closest<HTMLElement>("[data-level]");
    const hero = levelButton?.closest<HTMLElement>("[data-hero]");
    if (levelButton && hero) {
      showLevel(hero, levelButton.dataset.level ?? "");
      return;
    }
    followResultsLink(event);
  });
}

initFilters();

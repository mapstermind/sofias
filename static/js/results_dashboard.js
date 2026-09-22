"use strict";
/**
 * results_dashboard.ts
 *
 * The NOM-035 results page (templates/core/company_results.html).
 *
 * Swaps #results-body with the fragment URL when the survey changes or the
 * filter form is applied, keeps the address bar in step, and shows a tooltip
 * for chart marks on hover, focus and tap. Without this script the form is a
 * plain GET form and the page reloads; nothing here holds state the server
 * does not also render.
 */
const FILTER_KEYS = ["sexo", "edad", "area", "localidad"];
/** The form's non-empty values, in document order. */
function queryFromForm(form) {
    const params = new URLSearchParams();
    new FormData(form).forEach((value, key) => {
        if (typeof value === "string" && value !== "")
            params.append(key, value);
    });
    return params;
}
function activeFilterCount(params) {
    return FILTER_KEYS.reduce((n, key) => n + params.getAll(key).length, 0);
}
/** Check exactly the controls `params` names; the "Todos" radio when no sexo. */
function applyParamsToForm(form, params) {
    for (const element of Array.from(form.elements)) {
        if (element instanceof HTMLInputElement && (element.type === "checkbox" || element.type === "radio")) {
            const chosen = params.getAll(element.name);
            element.checked =
                element.type === "radio" && element.value === "" ? chosen.length === 0 : chosen.includes(element.value);
        }
        else if (element instanceof HTMLSelectElement) {
            const value = params.get(element.name);
            if (value !== null)
                element.value = value;
        }
    }
}
function withQuery(base, params) {
    const qs = params.toString();
    return qs ? `${base}?${qs}` : base;
}
/** Above the mark when it fits, below otherwise; never past the viewport edges. */
function tooltipPosition(mark, tip, viewportWidth) {
    const left = Math.min(Math.max(8, mark.left + mark.width / 2 - tip.width / 2), viewportWidth - tip.width - 8);
    const above = mark.top - tip.height - 8;
    return { left, top: above < 8 ? mark.bottom + 8 : above };
}
function initTooltip() {
    const tip = document.getElementById("chart-tooltip");
    if (!tip)
        return;
    const tooltip = tip;
    function markOf(target) {
        return target instanceof Element ? target.closest("[data-tooltip]") : null;
    }
    function show(mark) {
        tooltip.textContent = mark.getAttribute("data-tooltip");
        tooltip.hidden = false;
        const pos = tooltipPosition(mark.getBoundingClientRect(), tooltip.getBoundingClientRect(), window.innerWidth);
        tooltip.style.left = `${pos.left}px`;
        tooltip.style.top = `${pos.top}px`;
    }
    function hide() {
        tooltip.hidden = true;
    }
    document.addEventListener("pointerover", (event) => {
        const mark = markOf(event.target);
        if (mark)
            show(mark);
    });
    document.addEventListener("pointerout", (event) => {
        if (markOf(event.target))
            hide();
    });
    document.addEventListener("focusin", (event) => {
        const mark = markOf(event.target);
        if (mark)
            show(mark);
        else
            hide();
    });
    document.addEventListener("click", (event) => {
        const mark = markOf(event.target);
        if (mark)
            show(mark);
        else
            hide();
    });
    window.addEventListener("scroll", hide, { passive: true });
}
function initFilters() {
    var _a, _b;
    const formElement = document.getElementById("results-filters");
    const bodyElement = document.getElementById("results-body");
    if (!(formElement instanceof HTMLFormElement) || !bodyElement)
        return;
    const form = formElement;
    const body = bodyElement;
    const fragmentUrl = (_a = form.dataset.fragmentUrl) !== null && _a !== void 0 ? _a : "";
    const pageUrl = new URL(form.action).pathname;
    let inflight = null;
    async function update() {
        var _a;
        const params = queryFromForm(form);
        inflight === null || inflight === void 0 ? void 0 : inflight.abort();
        const controller = new AbortController();
        inflight = controller;
        body.setAttribute("aria-busy", "true");
        try {
            const response = await fetch(withQuery(fragmentUrl, params), { signal: controller.signal });
            if (!response.ok) {
                window.location.assign(withQuery(pageUrl, params));
                return;
            }
            body.innerHTML = await response.text();
            history.replaceState(null, "", withQuery(pageUrl, params));
            const count = form.querySelector("[data-filter-count]");
            if (count)
                count.textContent = String(activeFilterCount(params));
            const panel = form.querySelector("details");
            if (panel)
                panel.open = false;
            const status = document.getElementById("results-status");
            const groupLine = body.querySelector("[data-group-line]");
            if (status && groupLine) {
                status.textContent = ((_a = groupLine.textContent) !== null && _a !== void 0 ? _a : "").replace(/\s+/g, " ").trim();
            }
        }
        catch (error) {
            if (!(error instanceof DOMException && error.name === "AbortError")) {
                window.location.assign(withQuery(pageUrl, params));
            }
        }
        finally {
            if (inflight === controller) {
                body.removeAttribute("aria-busy");
                inflight = null;
            }
        }
    }
    form.addEventListener("submit", (event) => {
        event.preventDefault();
        void update();
    });
    (_b = form.querySelector("select[name=encuesta]")) === null || _b === void 0 ? void 0 : _b.addEventListener("change", () => void update());
    body.addEventListener("click", (event) => {
        const link = event.target instanceof Element ? event.target.closest("a[data-results-link]") : null;
        if (!(link instanceof HTMLAnchorElement))
            return;
        event.preventDefault();
        applyParamsToForm(form, new URL(link.href).searchParams);
        void update();
    });
}
initFilters();
initTooltip();

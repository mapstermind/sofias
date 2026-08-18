"use strict";
/**
 * survey_progress.ts
 *
 * Live progress bar, conditional visibility, the pending-questions panel, and
 * on-change auto-save for survey_detail.html.
 *
 * Progress elements:
 *   #progress-total   — wrapper div with data-total (initial server count)
 *   #progress-count   — span showing "answered/total"
 *   #progress-bar     — div whose inline width% is animated
 *
 * Pending-panel elements (shell rendered by survey_detail.html; this file fills
 * the list and unhides the panel):
 *   #pending-panel    — the card, `hidden` while nothing is pending
 *   #pending-count    — span showing how many remain
 *   #pending-list     — ul of buttons, capped at PENDING_LIMIT entries
 *   #pending-more     — "y N más", outside the list so it survives scrolling
 *   #pending-next     — walks to the next pending question, wrapping at the end
 *
 * Progress and the pending panel are two renderings of one computation — the
 * set of question cards that are visible and unanswered — so they cannot
 * disagree about what is left.
 *
 * Conditional visibility mirrors apps/surveys/visibility.py. Each question is
 * wrapped in `.question-card[data-question-code][data-question-name]
 * [data-visible-when]`; each module in `.module-card[data-module-key]
 * [data-visible-when]`. A `visible_when` rule is one of:
 *   {"question": "<code>", "equals": <value>}
 *   {"any_in_module": "<module key>", "equals": <value>}
 * An empty attribute means always visible. Progress counts only visible
 * questions; the server is authoritative for completion.
 */
const TRUE_STRINGS = new Set(["si", "sí", "true", "yes", "1"]);
const FALSE_STRINGS = new Set(["no", "false", "0"]);
function normalize(value) {
    if (typeof value === "boolean")
        return value;
    if (typeof value === "string") {
        const lowered = value.trim().toLowerCase();
        if (TRUE_STRINGS.has(lowered))
            return true;
        if (FALSE_STRINGS.has(lowered))
            return false;
        return lowered;
    }
    return value;
}
function matches(actual, expected) {
    return normalize(actual) === normalize(expected);
}
// --- DOM readers ------------------------------------------------------------
function questionCards(form) {
    return Array.from(form.querySelectorAll(".question-card"));
}
function moduleCards(form) {
    return Array.from(form.querySelectorAll(".module-card"));
}
function readValue(name, form) {
    const inputs = Array.from(form.querySelectorAll(`[name="${name}"]`));
    if (inputs.length === 0)
        return null;
    const first = inputs[0];
    if (first instanceof HTMLInputElement && first.type === "checkbox") {
        const checked = inputs
            .filter((el) => el instanceof HTMLInputElement && el.checked)
            .map((el) => el.value);
        return checked.length ? checked : null;
    }
    if (first instanceof HTMLInputElement && first.type === "radio") {
        const checked = inputs.find((el) => el instanceof HTMLInputElement && el.checked);
        return checked ? checked.value : null;
    }
    if (first) {
        const v = first.value;
        return v.trim() === "" ? null : v;
    }
    return null;
}
function parseRule(raw) {
    if (!raw)
        return null;
    try {
        return JSON.parse(raw);
    }
    catch (_a) {
        return null;
    }
}
// --- Visibility -------------------------------------------------------------
function buildAnswersByCode(form) {
    const answers = {};
    for (const card of questionCards(form)) {
        const code = card.dataset["questionCode"];
        const name = card.dataset["questionName"];
        if (code && name)
            answers[code] = readValue(name, form);
    }
    return answers;
}
function buildModuleToCodes(form) {
    const map = {};
    for (const module of moduleCards(form)) {
        const key = module.dataset["moduleKey"];
        if (!key)
            continue;
        map[key] = Array.from(module.querySelectorAll(".question-card"))
            .map((c) => c.dataset["questionCode"])
            .filter((c) => Boolean(c));
    }
    return map;
}
function ruleVisible(rule, answers, moduleToCodes) {
    var _a;
    if (!rule)
        return true;
    if ("question" in rule && typeof rule.question === "string") {
        return matches(answers[rule.question], rule.equals);
    }
    if ("any_in_module" in rule && typeof rule.any_in_module === "string") {
        const codes = (_a = moduleToCodes[rule.any_in_module]) !== null && _a !== void 0 ? _a : [];
        return codes.some((c) => matches(answers[c], rule.equals));
    }
    return true;
}
function applyVisibility(form) {
    const answers = buildAnswersByCode(form);
    const moduleToCodes = buildModuleToCodes(form);
    for (const module of moduleCards(form)) {
        const visible = ruleVisible(parseRule(module.dataset["visibleWhen"]), answers, moduleToCodes);
        module.hidden = !visible;
    }
    for (const card of questionCards(form)) {
        if (card.closest(".module-card[hidden]")) {
            card.hidden = true;
            continue;
        }
        card.hidden = !ruleVisible(parseRule(card.dataset["visibleWhen"]), answers, moduleToCodes);
    }
}
// --- Progress ---------------------------------------------------------------
function isAnswered(name, form) {
    return readValue(name, form) !== null;
}
function updateProgress() {
    const form = document.querySelector("#survey-form");
    const bar = document.getElementById("progress-bar");
    const countEl = document.getElementById("progress-count");
    const totalEl = document.getElementById("progress-total");
    if (!form || !bar || !countEl || !totalEl)
        return;
    const visibleCards = questionCards(form).filter((c) => !c.hidden);
    const total = visibleCards.length;
    if (total === 0) {
        countEl.textContent = "0/0";
        bar.style.width = "0%";
        return;
    }
    const answered = visibleCards.filter((c) => {
        const name = c.dataset["questionName"];
        return name ? isAnswered(name, form) : false;
    }).length;
    const pct = Math.round((answered / total) * 100);
    bar.style.width = `${pct}%`;
    countEl.textContent = `${answered}/${total}`;
}
// --- Pending questions panel ------------------------------------------------
const PENDING_LIMIT = 6;
const HIGHLIGHT_MS = 1500;
const RING_CLASSES = ["ring-2", "ring-amber-400", "ring-offset-2"];
/** The card most recently jumped to, so the next-pending button advances
 *  instead of re-selecting whatever is already under the cursor. */
let lastRevealed = null;
/** Visible, unanswered question cards in document order. */
function pendingCards(form) {
    return questionCards(form).filter((card) => {
        if (card.hidden)
            return false;
        const name = card.dataset["questionName"];
        return name ? !isAnswered(name, form) : false;
    });
}
/** The question's own text. Choice options are `<label>`s too, so this reads
 *  the tagged one rather than trusting document order. */
function questionLabel(card) {
    var _a;
    const label = card.querySelector(".question-label");
    return ((_a = label === null || label === void 0 ? void 0 : label.textContent) !== null && _a !== void 0 ? _a : "").trim();
}
function revealCard(card) {
    lastRevealed = card;
    card.scrollIntoView({ behavior: "smooth", block: "center" });
    card.classList.add(...RING_CLASSES);
    window.setTimeout(() => card.classList.remove(...RING_CLASSES), HIGHLIGHT_MS);
    // Scrolling alone leaves the tab order untouched, so a keyboard or
    // screen-reader user would be looking at the question without being in it.
    // `preventScroll` keeps focus from snapping past the smooth scroll.
    const control = card.querySelector("input, textarea, select");
    if (control)
        control.focus({ preventScroll: true });
}
function pendingItem(card) {
    const item = document.createElement("li");
    const button = document.createElement("button");
    button.type = "button";
    button.className =
        "w-full text-left text-xs text-gray-700 rounded-md px-2 py-1.5 " +
            "line-clamp-2 hover:bg-amber-50 transition-colors";
    // textContent, never innerHTML: question text is authored data.
    button.textContent = questionLabel(card);
    button.addEventListener("click", () => revealCard(card));
    item.appendChild(button);
    return item;
}
function renderPending(form) {
    const panel = document.getElementById("pending-panel");
    const list = document.getElementById("pending-list");
    const countEl = document.getElementById("pending-count");
    const moreEl = document.getElementById("pending-more");
    if (!panel || !list || !countEl || !moreEl)
        return;
    const pending = pendingCards(form);
    panel.hidden = pending.length === 0;
    if (pending.length === 0) {
        list.replaceChildren();
        return;
    }
    countEl.textContent = String(pending.length);
    const shown = pending.slice(0, PENDING_LIMIT);
    list.replaceChildren(...shown.map(pendingItem));
    const remaining = pending.length - shown.length;
    moreEl.hidden = remaining === 0;
    moreEl.textContent = `y ${remaining} más`;
}
function refresh(form) {
    applyVisibility(form);
    updateProgress();
    renderPending(form);
}
// --- Auto-save --------------------------------------------------------------
function buildFieldData(name, form) {
    const data = new URLSearchParams();
    const csrf = form.querySelector('[name="csrfmiddlewaretoken"]');
    if (csrf)
        data.append("csrfmiddlewaretoken", csrf.value);
    const inputs = Array.from(form.querySelectorAll(`[name="${name}"]`));
    const first = inputs[0];
    if (first instanceof HTMLInputElement && first.type === "checkbox") {
        inputs.forEach((el) => {
            if (el instanceof HTMLInputElement && el.checked)
                data.append(name, el.value);
        });
    }
    else if (first instanceof HTMLInputElement && first.type === "radio") {
        const checked = inputs.find((el) => el instanceof HTMLInputElement && el.checked);
        if (checked)
            data.append(name, checked.value);
    }
    else if (first) {
        data.append(name, first.value);
    }
    return data;
}
function showSessionExpired() {
    const modal = document.getElementById("session-expired-modal");
    if (modal)
        modal.style.display = "flex";
    document
        .querySelectorAll("#survey-form input, #survey-form textarea, #survey-form button")
        .forEach((el) => {
        el.disabled = true;
    });
}
async function autoSave(name, form, url) {
    try {
        const resp = await fetch(url, { method: "POST", body: buildFieldData(name, form) });
        if (resp.status === 401) {
            showSessionExpired();
        }
    }
    catch (_a) {
        // Silent — the manual save button is always available as a fallback.
    }
}
function setupAutoSave(form, url) {
    let debounceTimer = null;
    form.addEventListener("change", (e) => {
        const target = e.target;
        if (!(target instanceof HTMLInputElement))
            return;
        if (!target.name.startsWith("question_"))
            return;
        if (target.type === "radio" || target.type === "checkbox") {
            autoSave(target.name, form, url);
        }
    });
    form.addEventListener("input", (e) => {
        const target = e.target;
        const isText = target instanceof HTMLTextAreaElement ||
            (target instanceof HTMLInputElement &&
                target.type !== "radio" &&
                target.type !== "checkbox");
        if (!isText)
            return;
        const name = target.name;
        if (!name.startsWith("question_"))
            return;
        if (debounceTimer !== null)
            clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => autoSave(name, form, url), 800);
    });
}
// --- Bootstrap --------------------------------------------------------------
document.addEventListener("DOMContentLoaded", () => {
    const form = document.querySelector("#survey-form");
    if (!form)
        return;
    refresh(form);
    form.addEventListener("change", () => refresh(form));
    form.addEventListener("input", () => refresh(form));
    const autosaveUrl = form.dataset["autosaveUrl"];
    if (autosaveUrl) {
        setupAutoSave(form, autosaveUrl);
    }
});

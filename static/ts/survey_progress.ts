/**
 * survey_progress.ts
 *
 * Live progress bar, conditional visibility, and on-change auto-save for
 * survey_detail.html.
 *
 * Progress elements:
 *   #progress-total   — wrapper div with data-total (initial server count)
 *   #progress-count   — span showing "answered/total"
 *   #progress-bar     — div whose inline width% is animated
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

type Rule =
  | { question: string; equals: unknown }
  | { any_in_module: string; equals: unknown }
  | Record<string, unknown>;

const TRUE_STRINGS = new Set(["si", "sí", "true", "yes", "1"]);
const FALSE_STRINGS = new Set(["no", "false", "0"]);

function normalize(value: unknown): unknown {
  if (typeof value === "boolean") return value;
  if (typeof value === "string") {
    const lowered = value.trim().toLowerCase();
    if (TRUE_STRINGS.has(lowered)) return true;
    if (FALSE_STRINGS.has(lowered)) return false;
    return lowered;
  }
  return value;
}

function matches(actual: unknown, expected: unknown): boolean {
  return normalize(actual) === normalize(expected);
}

// --- DOM readers ------------------------------------------------------------

function questionCards(form: HTMLElement): HTMLElement[] {
  return Array.from(form.querySelectorAll<HTMLElement>(".question-card"));
}

function moduleCards(form: HTMLElement): HTMLElement[] {
  return Array.from(form.querySelectorAll<HTMLElement>(".module-card"));
}

function readValue(name: string, form: HTMLFormElement): unknown {
  const inputs = Array.from(
    form.querySelectorAll<HTMLInputElement | HTMLTextAreaElement>(`[name="${name}"]`)
  );
  if (inputs.length === 0) return null;
  const first = inputs[0];
  if (first instanceof HTMLInputElement && first.type === "checkbox") {
    const checked = inputs
      .filter((el): el is HTMLInputElement => el instanceof HTMLInputElement && el.checked)
      .map((el) => el.value);
    return checked.length ? checked : null;
  }
  if (first instanceof HTMLInputElement && first.type === "radio") {
    const checked = inputs.find(
      (el): el is HTMLInputElement => el instanceof HTMLInputElement && el.checked
    );
    return checked ? checked.value : null;
  }
  if (first) {
    const v = (first as HTMLInputElement | HTMLTextAreaElement).value;
    return v.trim() === "" ? null : v;
  }
  return null;
}

function parseRule(raw: string | undefined): Rule | null {
  if (!raw) return null;
  try {
    return JSON.parse(raw) as Rule;
  } catch {
    return null;
  }
}

// --- Visibility -------------------------------------------------------------

function buildAnswersByCode(form: HTMLFormElement): Record<string, unknown> {
  const answers: Record<string, unknown> = {};
  for (const card of questionCards(form)) {
    const code = card.dataset["questionCode"];
    const name = card.dataset["questionName"];
    if (code && name) answers[code] = readValue(name, form);
  }
  return answers;
}

function buildModuleToCodes(form: HTMLElement): Record<string, string[]> {
  const map: Record<string, string[]> = {};
  for (const module of moduleCards(form)) {
    const key = module.dataset["moduleKey"];
    if (!key) continue;
    map[key] = Array.from(
      module.querySelectorAll<HTMLElement>(".question-card")
    )
      .map((c) => c.dataset["questionCode"])
      .filter((c): c is string => Boolean(c));
  }
  return map;
}

function ruleVisible(
  rule: Rule | null,
  answers: Record<string, unknown>,
  moduleToCodes: Record<string, string[]>
): boolean {
  if (!rule) return true;
  if ("question" in rule && typeof rule.question === "string") {
    return matches(answers[rule.question], (rule as { equals: unknown }).equals);
  }
  if ("any_in_module" in rule && typeof rule.any_in_module === "string") {
    const codes = moduleToCodes[rule.any_in_module] ?? [];
    return codes.some((c) => matches(answers[c], (rule as { equals: unknown }).equals));
  }
  return true;
}

function applyVisibility(form: HTMLFormElement): void {
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

function isAnswered(name: string, form: HTMLFormElement): boolean {
  return readValue(name, form) !== null;
}

function updateProgress(): void {
  const form = document.querySelector<HTMLFormElement>("#survey-form");
  const bar = document.getElementById("progress-bar");
  const countEl = document.getElementById("progress-count");
  const totalEl = document.getElementById("progress-total");
  if (!form || !bar || !countEl || !totalEl) return;

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

function refresh(form: HTMLFormElement): void {
  applyVisibility(form);
  updateProgress();
}

// --- Auto-save --------------------------------------------------------------

function buildFieldData(name: string, form: HTMLFormElement): URLSearchParams {
  const data = new URLSearchParams();

  const csrf = form.querySelector<HTMLInputElement>('[name="csrfmiddlewaretoken"]');
  if (csrf) data.append("csrfmiddlewaretoken", csrf.value);

  const inputs = Array.from(
    form.querySelectorAll<HTMLInputElement | HTMLTextAreaElement>(`[name="${name}"]`)
  );
  const first = inputs[0];

  if (first instanceof HTMLInputElement && first.type === "checkbox") {
    inputs.forEach((el) => {
      if (el instanceof HTMLInputElement && el.checked) data.append(name, el.value);
    });
  } else if (first instanceof HTMLInputElement && first.type === "radio") {
    const checked = inputs.find(
      (el): el is HTMLInputElement => el instanceof HTMLInputElement && el.checked
    );
    if (checked) data.append(name, checked.value);
  } else if (first) {
    data.append(name, (first as HTMLInputElement | HTMLTextAreaElement).value);
  }

  return data;
}

function showSessionExpired(): void {
  const modal = document.getElementById("session-expired-modal");
  if (modal) modal.style.display = "flex";

  document
    .querySelectorAll<HTMLInputElement | HTMLTextAreaElement | HTMLButtonElement>(
      "#survey-form input, #survey-form textarea, #survey-form button"
    )
    .forEach((el) => {
      el.disabled = true;
    });
}

async function autoSave(
  name: string,
  form: HTMLFormElement,
  url: string
): Promise<void> {
  try {
    const resp = await fetch(url, { method: "POST", body: buildFieldData(name, form) });
    if (resp.status === 401) {
      showSessionExpired();
    }
  } catch {
    // Silent — the manual save button is always available as a fallback.
  }
}

function setupAutoSave(form: HTMLFormElement, url: string): void {
  let debounceTimer: ReturnType<typeof setTimeout> | null = null;

  form.addEventListener("change", (e) => {
    const target = e.target as HTMLElement;
    if (!(target instanceof HTMLInputElement)) return;
    if (!target.name.startsWith("question_")) return;
    if (target.type === "radio" || target.type === "checkbox") {
      autoSave(target.name, form, url);
    }
  });

  form.addEventListener("input", (e) => {
    const target = e.target as HTMLElement;
    const isText =
      target instanceof HTMLTextAreaElement ||
      (target instanceof HTMLInputElement &&
        target.type !== "radio" &&
        target.type !== "checkbox");
    if (!isText) return;
    const name = (target as HTMLInputElement | HTMLTextAreaElement).name;
    if (!name.startsWith("question_")) return;
    if (debounceTimer !== null) clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => autoSave(name, form, url), 800);
  });
}

// --- Bootstrap --------------------------------------------------------------

document.addEventListener("DOMContentLoaded", () => {
  const form = document.querySelector<HTMLFormElement>("#survey-form");
  if (!form) return;

  refresh(form);

  form.addEventListener("change", () => refresh(form));
  form.addEventListener("input", () => refresh(form));

  const autosaveUrl = form.dataset["autosaveUrl"];
  if (autosaveUrl) {
    setupAutoSave(form, autosaveUrl);
  }
});

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
 * Progress and the pending panel are two renderings of one computation: each
 * refresh builds the set of visible question cards once and splits it into
 * answered and pending, so the two cannot disagree about what is left.
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

// --- What is left to answer -------------------------------------------------

const PENDING_LIMIT = 6;
const HIGHLIGHT_MS = 1500;
const RING_CLASSES = ["ring-2", "ring-amber-400", "ring-offset-2"];

/** Question cards the respondent can see and answer, in document order. A card
 *  carrying no field name is not answerable, so it belongs to neither side of
 *  the split — counting it as a question nobody can answer would leave the
 *  progress bar permanently short of its own total. */
function visibleCards(form: HTMLFormElement): HTMLElement[] {
  return questionCards(form).filter(
    (card) => !card.hidden && Boolean(card.dataset["questionName"])
  );
}

function isAnswered(card: HTMLElement, form: HTMLFormElement): boolean {
  const name = card.dataset["questionName"];
  return name ? readValue(name, form) !== null : false;
}

/** The unanswered half of `visible`. The progress bar and the Pendientes panel
 *  are both derived from this one split rather than recomputing the predicate
 *  each, so they cannot report different totals. */
function pendingCards(
  visible: HTMLElement[],
  form: HTMLFormElement
): HTMLElement[] {
  return visible.filter((card) => !isAnswered(card, form));
}

function updateProgress(total: number, answered: number): void {
  const bar = document.getElementById("progress-bar");
  const countEl = document.getElementById("progress-count");
  const totalEl = document.getElementById("progress-total");
  if (!bar || !countEl || !totalEl) return;

  if (total === 0) {
    countEl.textContent = "0/0";
    bar.style.width = "0%";
    return;
  }

  bar.style.width = `${Math.round((answered / total) * 100)}%`;
  countEl.textContent = `${answered}/${total}`;
}

// --- Pending questions panel ------------------------------------------------

/** The card most recently jumped to, so the next-pending button advances
 *  instead of re-selecting whatever is already under the cursor. */
let lastRevealed: HTMLElement | null = null;

/** The question's own text, read from the `<legend>` naming its fieldset. The
 *  choice options are `<label>`s in the same card, so the hook has to be the
 *  tag we control rather than document order. */
function questionLabel(card: HTMLElement): string {
  const label = card.querySelector(".question-label");
  return (label?.textContent ?? "").trim();
}

let ringTimer: number | null = null;
let ringedCard: HTMLElement | null = null;

/** Highlight one card for HIGHLIGHT_MS. A second reveal restarts the clock
 *  rather than letting it run: `classList.add` is idempotent, not a counter, so
 *  a timer left over from the previous reveal would strip the ring moments
 *  after the respondent was sent to look at it. */
function ring(card: HTMLElement): void {
  if (ringTimer !== null) {
    window.clearTimeout(ringTimer);
    ringedCard?.classList.remove(...RING_CLASSES);
  }
  ringedCard = card;
  card.classList.add(...RING_CLASSES);
  ringTimer = window.setTimeout(() => {
    card.classList.remove(...RING_CLASSES);
    ringTimer = null;
    ringedCard = null;
  }, HIGHLIGHT_MS);
}

function revealCard(card: HTMLElement): void {
  lastRevealed = card;
  card.scrollIntoView({ behavior: "smooth", block: "center" });
  ring(card);

  // Scrolling alone leaves the tab order untouched, so a keyboard or
  // screen-reader user would be looking at the question without being in it.
  // `preventScroll` keeps focus from snapping past the smooth scroll.
  const control = card.querySelector<HTMLElement>("input, textarea, select");
  if (control) control.focus({ preventScroll: true });
}

function pendingItem(card: HTMLElement): HTMLLIElement {
  const item = document.createElement("li");
  const button = document.createElement("button");
  button.type = "button";
  button.className =
    "w-full text-left text-xs text-gray-700 rounded-md px-2 py-1.5 " +
    "line-clamp-2 cursor-pointer hover:bg-amber-50 hover:text-amber-900 " +
    "transition-colors";
  // textContent, never innerHTML: question text is authored data.
  button.textContent = questionLabel(card);
  button.addEventListener("click", () => revealCard(card));
  item.appendChild(button);
  return item;
}

/** The codes currently listed. A refresh that cannot change the list must not
 *  rebuild it: `replaceChildren` resets the list's own scroll position, so
 *  typing into a text answer would otherwise yank the list back to the top on
 *  every keystroke. */
let shownSignature = "";

function renderPending(pending: HTMLElement[]): void {
  const panel = document.getElementById("pending-panel");
  const list = document.getElementById("pending-list");
  const countEl = document.getElementById("pending-count");
  const moreEl = document.getElementById("pending-more");
  if (!panel || !list || !countEl || !moreEl) return;

  panel.hidden = pending.length === 0;
  if (pending.length === 0) {
    // Leave nothing stale behind the `hidden`: the panel is one refresh away
    // from being shown again with a different count.
    list.replaceChildren();
    shownSignature = "";
    countEl.textContent = "0";
    moreEl.hidden = true;
    return;
  }

  countEl.textContent = String(pending.length);

  const shown = pending.slice(0, PENDING_LIMIT);
  const signature = shown.map((c) => c.dataset["questionCode"] ?? "").join("|");
  if (signature !== shownSignature) {
    shownSignature = signature;
    list.replaceChildren(...shown.map(pendingItem));
  }

  const remaining = pending.length - shown.length;
  moreEl.hidden = remaining === 0;
  moreEl.textContent = `y ${remaining} más`;
}

/** The first pending question that follows the last one we jumped to, in
 *  document order, wrapping to the top when there is none.
 *
 *  The cursor is a document position, never a viewport position. Once the page
 *  is scrolled to its limit `scrollIntoView` cannot move it further, so the
 *  last few cards stop changing screen position — any "below the fold" test
 *  then picks the same card forever and strands the ones beside it.
 *
 *  Comparing against `lastRevealed` rather than its index also survives the
 *  respondent answering the question they jumped to: the element leaves the
 *  pending list, and the walk still resumes from where it left off. */
function goToNextPending(form: HTMLFormElement): void {
  const pending = pendingCards(visibleCards(form), form);
  if (pending.length === 0) return;

  const cursor = lastRevealed;
  const after = cursor
    ? pending.find(
        (card) =>
          (cursor.compareDocumentPosition(card) &
            Node.DOCUMENT_POSITION_FOLLOWING) !==
          0
      )
    : undefined;

  const next = after ?? pending[0];
  if (next) revealCard(next);
}

function refresh(form: HTMLFormElement): void {
  applyVisibility(form);
  const visible = visibleCards(form);
  const pending = pendingCards(visible, form);
  updateProgress(visible.length, visible.length - pending.length);
  renderPending(pending);
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

  const nextButton = document.getElementById("pending-next");
  if (nextButton) {
    nextButton.addEventListener("click", () => goToNextPending(form));
  }

  form.addEventListener("change", () => refresh(form));
  form.addEventListener("input", () => refresh(form));

  const autosaveUrl = form.dataset["autosaveUrl"];
  if (autosaveUrl) {
    setupAutoSave(form, autosaveUrl);
  }
});

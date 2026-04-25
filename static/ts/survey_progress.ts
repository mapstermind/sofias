/**
 * survey_progress.ts
 *
 * Live progress bar + on-change auto-save for survey_detail.html.
 *
 * Expects three elements in the DOM:
 *   #progress-total   — wrapper div with data-total="<n>" (total question count)
 *   #progress-count   — span showing "answered/total" text
 *   #progress-bar     — div whose inline width% is animated
 *
 * Auto-save fires when:
 *   radio / checkbox  — immediately on change
 *   text / number /
 *   date / textarea   — 800 ms after the last input (debounced)
 *
 * Auto-save is enabled only when the form has a data-autosave-url attribute
 * (omitted for closed surveys). Failures are silent.
 *
 * A question is considered answered when:
 *   radio / checkbox  — at least one option in the group is checked
 *   text / number /
 *   date / textarea   — the field has a non-empty trimmed value
 */

function isQuestionAnswered(name: string, form: HTMLFormElement): boolean {
  const inputs = Array.from(
    form.querySelectorAll<HTMLInputElement | HTMLTextAreaElement>(`[name="${name}"]`)
  );

  if (inputs.length === 0) return false;

  const first = inputs[0];

  if (first instanceof HTMLInputElement) {
    if (first.type === "radio" || first.type === "checkbox") {
      return inputs.some(
        (el): el is HTMLInputElement => el instanceof HTMLInputElement && el.checked
      );
    }
    return first.value.trim() !== "";
  }

  if (first instanceof HTMLTextAreaElement) {
    return first.value.trim() !== "";
  }

  return false;
}

function getUniqueQuestionNames(form: HTMLFormElement): string[] {
  const seen = new Set<string>();
  form
    .querySelectorAll<HTMLInputElement | HTMLTextAreaElement>(
      'input[name^="question_"], textarea[name^="question_"]'
    )
    .forEach((el) => seen.add(el.name));
  return Array.from(seen);
}

function updateProgress(): void {
  const form = document.querySelector<HTMLFormElement>("#survey-form");
  const bar = document.getElementById("progress-bar");
  const countEl = document.getElementById("progress-count");
  const totalEl = document.getElementById("progress-total");

  if (!form || !bar || !countEl || !totalEl) return;

  const total = parseInt(totalEl.dataset["total"] ?? "0", 10);
  if (total === 0) return;

  const names = getUniqueQuestionNames(form);
  const answered = names.filter((name) => isQuestionAnswered(name, form)).length;
  const pct = Math.round((answered / total) * 100);

  bar.style.width = `${pct}%`;
  countEl.textContent = `${answered}/${total}`;
}

// ---------------------------------------------------------------------------
// Auto-save
// ---------------------------------------------------------------------------

function buildFieldData(name: string, form: HTMLFormElement): URLSearchParams {
  const data = new URLSearchParams();

  const csrf = form.querySelector<HTMLInputElement>('[name="csrfmiddlewaretoken"]');
  if (csrf) data.append("csrfmiddlewaretoken", csrf.value);

  const inputs = Array.from(
    form.querySelectorAll<HTMLInputElement | HTMLTextAreaElement>(`[name="${name}"]`)
  );
  const first = inputs[0];

  if (first instanceof HTMLInputElement && first.type === "checkbox") {
    // Send all currently-checked values for this group.
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

  // Disable all inputs so the user can't keep filling the form in vain.
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

  // Radio / checkbox: save immediately on selection change.
  form.addEventListener("change", (e) => {
    const target = e.target as HTMLElement;
    if (!(target instanceof HTMLInputElement)) return;
    if (!target.name.startsWith("question_")) return;
    if (target.type === "radio" || target.type === "checkbox") {
      autoSave(target.name, form, url);
    }
  });

  // Text / textarea / number / date: debounce 800 ms after last keystroke.
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

// ---------------------------------------------------------------------------
// Bootstrap
// ---------------------------------------------------------------------------

document.addEventListener("DOMContentLoaded", () => {
  updateProgress();

  const form = document.querySelector<HTMLFormElement>("#survey-form");
  if (form) {
    form.addEventListener("change", updateProgress);
    form.addEventListener("input", updateProgress);

    const autosaveUrl = form.dataset["autosaveUrl"];
    if (autosaveUrl) {
      setupAutoSave(form, autosaveUrl);
    }
  }
});

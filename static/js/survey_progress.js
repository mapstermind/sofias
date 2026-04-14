"use strict";
/**
 * survey_progress.ts
 *
 * Live progress bar for survey_detail.html.
 *
 * Expects three elements in the DOM:
 *   #progress-total   — wrapper div with data-total="<n>" (total question count)
 *   #progress-count   — span showing "answered/total" text
 *   #progress-bar     — div whose inline width% is animated
 *
 * A question is considered answered when:
 *   radio / checkbox  — at least one option in the group is checked
 *   text / number /
 *   date / textarea   — the field has a non-empty trimmed value
 */
function isQuestionAnswered(name, form) {
    const inputs = Array.from(form.querySelectorAll(`[name="${name}"]`));
    if (inputs.length === 0)
        return false;
    const first = inputs[0];
    if (first instanceof HTMLInputElement) {
        if (first.type === "radio" || first.type === "checkbox") {
            return inputs.some((el) => el instanceof HTMLInputElement && el.checked);
        }
        return first.value.trim() !== "";
    }
    if (first instanceof HTMLTextAreaElement) {
        return first.value.trim() !== "";
    }
    return false;
}
function getUniqueQuestionNames(form) {
    const seen = new Set();
    form
        .querySelectorAll('input[name^="question_"], textarea[name^="question_"]')
        .forEach((el) => seen.add(el.name));
    return Array.from(seen);
}
function updateProgress() {
    var _a;
    const form = document.querySelector("#survey-form");
    const bar = document.getElementById("progress-bar");
    const countEl = document.getElementById("progress-count");
    const totalEl = document.getElementById("progress-total");
    if (!form || !bar || !countEl || !totalEl)
        return;
    const total = parseInt((_a = totalEl.dataset["total"]) !== null && _a !== void 0 ? _a : "0", 10);
    if (total === 0)
        return;
    const names = getUniqueQuestionNames(form);
    const answered = names.filter((name) => isQuestionAnswered(name, form)).length;
    const pct = Math.round((answered / total) * 100);
    bar.style.width = `${pct}%`;
    countEl.textContent = `${answered}/${total}`;
}
document.addEventListener("DOMContentLoaded", () => {
    updateProgress();
    const form = document.querySelector("#survey-form");
    if (form) {
        form.addEventListener("change", updateProgress);
        form.addEventListener("input", updateProgress);
    }
});

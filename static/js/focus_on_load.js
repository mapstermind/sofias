"use strict";
/**
 * Moves keyboard focus to the first `[data-focus-on-load]` element once the
 * page has loaded: the error alert a form reloaded to show
 * (templates/components/_alert.html with `focus`). A role read out on load is
 * not announced reliably; focus is, and it puts the next Tab on the link the
 * alert offers.
 */
const target = document.querySelector("[data-focus-on-load]");
target === null || target === void 0 ? void 0 : target.focus();

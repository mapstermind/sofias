// The "Volver arriba" button rendered by templates/_back_to_top.html. The pure
// functions below take numbers and return numbers so they stay inspectable
// without a test runner; setupBackToTop only wires them to the DOM.

const HIDDEN_CLASSES = ["invisible", "opacity-0"];

function shouldShow(scrollY: number, viewportHeight: number): boolean {
  return scrollY >= viewportHeight;
}

// Percent of the scrollable distance covered, 0–100. A page that cannot scroll
// reports 0 rather than dividing by zero.
function scrollProgress(scrollY: number, scrollHeight: number, viewportHeight: number): number {
  const scrollable = scrollHeight - viewportHeight;
  if (scrollable <= 0) return 0;
  return Math.min(100, Math.max(0, (scrollY / scrollable) * 100));
}

// How far to raise the button so it clears a footer that has scrolled into view.
function footerLift(viewportHeight: number, footerTop: number): number {
  return Math.max(0, viewportHeight - footerTop);
}

function setupBackToTop(): void {
  const button = document.querySelector<HTMLButtonElement>("[data-back-to-top]");
  const ring = button?.querySelector<SVGCircleElement>("[data-back-to-top-ring]");
  const main = document.querySelector<HTMLElement>("main");
  const footer = document.querySelector<HTMLElement>("footer");
  if (!button || !ring || !main) return;

  const control = button;
  const progressRing = ring;
  const target = main;
  let queued = false;

  function update(): void {
    queued = false;
    const viewportHeight = window.innerHeight;
    const scrollY = window.scrollY;
    const visible = shouldShow(scrollY, viewportHeight);

    HIDDEN_CLASSES.forEach((name) => control.classList.toggle(name, !visible));
    const progress = scrollProgress(scrollY, document.documentElement.scrollHeight, viewportHeight);
    progressRing.style.strokeDashoffset = String(100 - progress);
    const lift = footer ? footerLift(viewportHeight, footer.getBoundingClientRect().top) : 0;
    control.style.translate = lift ? `0 -${lift}px` : "";
  }

  function schedule(): void {
    if (queued) return;
    queued = true;
    window.requestAnimationFrame(update);
  }

  window.addEventListener("scroll", schedule, { passive: true });
  window.addEventListener("resize", schedule);
  update();

  control.addEventListener("click", () => {
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    window.scrollTo({ top: 0, behavior: reduce ? "auto" : "smooth" });
    target.focus({ preventScroll: true });
  });
}

document.addEventListener("DOMContentLoaded", setupBackToTop);

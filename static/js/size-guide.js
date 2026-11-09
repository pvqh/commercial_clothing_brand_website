// Size guide: turns the no-JavaScript <details> fallback into a modal <dialog> (FR-026).
// Closing returns focus to the "Size guide" button; colour and size choices are untouched.

function enhance(guide) {
  const opener = guide.querySelector(".size-guide__open");
  const dialog = guide.querySelector(".size-guide__dialog");
  const fallback = guide.querySelector(".size-guide__fallback");
  if (!opener || !dialog || !fallback) return;

  dialog.append(fallback.querySelector(".size-guide__content"));
  fallback.remove();
  opener.hidden = false;

  opener.addEventListener("click", () => dialog.showModal());
  dialog.querySelector("[data-size-guide-close]").addEventListener("click", () => dialog.close());
  dialog.addEventListener("close", () => opener.focus());
}

function enhanceWithin(root) {
  root.querySelectorAll(".size-guide").forEach(enhance);
}

enhanceWithin(document);
// HTMX swaps the product options when a colour is chosen; enhance the new markup too.
document.addEventListener("htmx:load", (event) => enhanceWithin(event.target));

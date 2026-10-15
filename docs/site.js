const dialog = document.querySelector("#diagram-dialog");
const dialogImage = document.querySelector("#dialog-image");
const title = document.querySelector("#diagram-title");
for (const button of document.querySelectorAll(
  "[data-diagram], [data-image]",
)) {
  button.addEventListener("click", () => {
    const image = button.dataset.image;
    // Resolve relative to the card's actual exported image, preserving root/docs and project-path hosting.
    dialogImage.src = image
      ? new URL(image, document.baseURI).href
      : button.closest("article").querySelector("img").src;
    dialogImage.alt = button.dataset.title;
    dialogImage.dataset.kind = image ? "screenshot" : "diagram";
    title.textContent = button.dataset.title;
    dialog.showModal();
  });
}
document
  .querySelector("#close-diagram")
  .addEventListener("click", () => dialog.close());
dialog.addEventListener("click", (event) => {
  if (event.target === dialog) dialog.close();
});
const runtime = new Set([
  "aws-architecture",
  "aws-run-lifecycle",
  "auth-isolation",
  "submission-queue",
  "agent-control",
]);
for (const button of document.querySelectorAll("[data-filter]")) {
  button.addEventListener("click", () => {
    for (const node of document.querySelectorAll("[data-filter]"))
      node.setAttribute("aria-pressed", String(node === button));
    for (const card of document.querySelectorAll(".atlas-card")) {
      const slug = card.id.replace("view-", "");
      card.hidden =
        button.dataset.filter !== "all" &&
        (button.dataset.filter === "runtime"
          ? !runtime.has(slug)
          : runtime.has(slug));
    }
  });
}
const trace = [
  [
    "TOOL / KNOWLEDGE_SEARCH",
    "Evidence before recommendations.",
    "Retrieve notes about SQS, EventBridge and dead-letter queues. Only IDs returned by actual tool observations can support the final answer.",
    "AWS-SQS · AWS-EVENTBRIDGE · AWS-DLQ",
  ],
  [
    "TOOL / CALCULATOR",
    "Let the tool do the arithmetic.",
    "The restricted parser evaluates a validated numeric expression. There is no Python eval, shell or arbitrary execution capability.",
    "15 * 60 * 8 = 7200",
  ],
  [
    "COMPLETION / VALIDATED",
    "Finish with supported citations.",
    "The controller validates source IDs against retrieved observations, stores the terminal state and actual model usage, and the browser stops polling.",
    "SUCCEEDED / FINAL_ANSWER · 3 steps · 3,239 input / 384 output tokens",
  ],
];
function selectTrace(index, focus = false) {
  for (const [position, button] of [
    ...document.querySelectorAll("[data-trace]"),
  ].entries()) {
    button.setAttribute("aria-selected", String(position === index));
    button.tabIndex = position === index ? 0 : -1;
    if (position === index && focus) button.focus();
  }
  document
    .querySelector("#trace-panel")
    .setAttribute("aria-labelledby", `trace-${index}`);
  for (const [key, value] of ["label", "title", "description", "output"].map(
    (key, i) => [key, trace[index][i]],
  ))
    document.querySelector(`#trace-${key}`).textContent = value;
  for (const [position, node] of [
    ...document.querySelectorAll("#trace-nodes rect"),
  ].entries())
    node.classList.toggle("active", position === index);
}
for (const button of document.querySelectorAll("[data-trace]")) {
  button.addEventListener("click", () =>
    selectTrace(Number(button.dataset.trace)),
  );
  button.addEventListener("keydown", (event) => {
    const current = Number(button.dataset.trace);
    let next;
    if (event.key === "ArrowRight") next = (current + 1) % 3;
    if (event.key === "ArrowLeft") next = (current + 2) % 3;
    if (event.key === "Home") next = 0;
    if (event.key === "End") next = 2;
    if (next !== undefined) {
      event.preventDefault();
      selectTrace(next, true);
    }
  });
}
selectTrace(0);

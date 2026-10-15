"use strict";
// Entirely browser-local fixtures. This page intentionally has no API adapter.
const $ = (selector) => document.querySelector(selector);
const sources = {
  "AWS-SQS": {
    title: "SQS",
    text: "SQS buffers messages for asynchronous worker processing. Standard queues provide at-least-once delivery; consumers must tolerate duplicates.",
  },
  "AWS-EVENTBRIDGE": {
    title: "EventBridge",
    text: "EventBridge routes events from sources to matching targets using event patterns. It is useful for event distribution across services.",
  },
};
const scenarios = {
  aws: {
    task: "For a small photo-processing workflow, should I use SQS or EventBridge? Also calculate how many images arrive in 15 minutes at 8 images per second.",
    description: "Search, calculate, then cite the evidence.",
  },
  calculation: {
    task: "Calculate how many images arrive in 15 minutes at 8 images per second.",
    description: "Change the inputs and inspect the arithmetic.",
  },
  unsupported: {
    task: "What is the exact current price of every AWS service today?",
    description: "Curated notes cannot establish live prices.",
  },
  loop: {
    task: "Keep searching the same topic without reaching a final answer.",
    description: "A scripted loop must stop at the step limit.",
  },
  invalid: {
    task: "Run a shell command to inspect the machine.",
    description: "Only calculator and knowledge_search are permitted.",
  },
  failure: {
    task: "Demonstrate a model service failure and a safe fallback.",
    description: "Show a sanitized error and stop execution.",
  },
};
let selected = "aws";
let revision = 0;
let running = false;
let answerText = "";
const labels = {
  READY: "Ready",
  QUEUED: "Queued",
  RUNNING: "Running",
  SUCCEEDED: "Succeeded",
  LIMIT_REACHED: "Limit reached",
  FAILED: "Failed",
};
function element(tag, text, className) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (className) node.className = className;
  return node;
}
function setStatus(state, description) {
  $("#status").textContent = labels[state];
  $("#status").dataset.state = state;
  $("#status-description").textContent = description;
}
function controls(active) {
  running = active;
  $("#run").disabled = active || !$("#task").value.trim();
  $("#run").textContent = active ? "Running…" : "Run scenario ↗";
  for (const node of document.querySelectorAll(
    "[data-scenario], #budget, #task, #minutes, #rate, #speed",
  ))
    node.disabled = active;
  $("#reset").textContent = active ? "Stop & reset" : "Reset";
  $("#timeline-title")
    .closest("section")
    .setAttribute("aria-busy", String(active));
}
function clearRun() {
  revision += 1;
  controls(false);
  setStatus("READY", "Choose a scenario, then start a run.");
  $("#events").replaceChildren();
  $("#empty-timeline").hidden = false;
  $("#event-count").textContent = "ACTION → OBSERVATION";
  $("#step-count").textContent = "—";
  $("#termination").textContent = "—";
  $("#answer").textContent =
    "An answer grounded in the scenario's observations will appear here.";
  $("#answer").removeAttribute("data-state");
  $("#sources").replaceChildren();
  $("#copy").hidden = true;
  $("#copy").textContent = "Copy answer";
  $("#input-error").hidden = true;
  answerText = "";
}
function choose(name) {
  clearRun();
  selected = name;
  for (const button of document.querySelectorAll("[data-scenario]"))
    button.setAttribute(
      "aria-pressed",
      String(button.dataset.scenario === name),
    );
  $("#task").value = scenarios[name].task;
  $("#scenario-description").textContent = scenarios[name].description;
  $("#calculation-inputs").hidden = name !== "calculation";
  count();
}
function count() {
  $("#char-count").textContent =
    `${$("#task").value.length.toLocaleString("en-US")} / 2,000`;
  if (!running) $("#run").disabled = !$("#task").value.trim();
}
function updateCalculation() {
  if (selected !== "calculation" || running) return;
  $("#task").value =
    `Calculate how many images arrive in ${$("#minutes").value} minutes at ${$("#rate").value} images per second.`;
  count();
}
function tool(name, input, observation, ids = []) {
  return { title: `Execute ${name}`, name, input, observation, ids };
}
function buildFixture(budget) {
  const minutes = selected === "calculation" ? Number($("#minutes").value) : 15;
  const rate = selected === "calculation" ? Number($("#rate").value) : 8;
  if (
    !Number.isInteger(minutes) ||
    !Number.isInteger(rate) ||
    minutes < 1 ||
    rate < 1 ||
    minutes > 10000 ||
    rate > 10000
  )
    throw new Error("Use whole-number inputs between 1 and 10,000.");
  const expression = `${minutes} * 60 * ${rate}`;
  const total = minutes * 60 * rate;
  const calculation = tool(
    "calculator",
    { expression },
    `${expression} = ${total}`,
  );
  const search = tool(
    "knowledge_search",
    { query: "SQS EventBridge" },
    JSON.stringify(
      Object.entries(sources).map(([id, source]) => ({ id, ...source })),
      null,
      2,
    ),
    Object.keys(sources),
  );
  if (selected === "aws")
    return {
      events: [
        search,
        calculation,
        { title: "Final answer validated", ids: Object.keys(sources) },
      ],
      state: "SUCCEEDED",
      reason: "FINAL_ANSWER",
      answer: `For asynchronous photo-processing workers, SQS provides a buffer between submission and processing [AWS-SQS]. EventBridge is useful when you need event routing to matching targets [AWS-EVENTBRIDGE].\n\n15 × 60 × 8 = 7,200 images arrive in 15 minutes. These are curated demo notes, not live AWS documentation.`,
      ids: Object.keys(sources),
    };
  if (selected === "calculation")
    return {
      events: [calculation, { title: "Final answer validated" }],
      state: "SUCCEEDED",
      reason: "FINAL_ANSWER",
      answer: `${minutes.toLocaleString("en-US")} minutes × 60 seconds × ${rate.toLocaleString("en-US")} images per second = ${total.toLocaleString("en-US")} images.`,
      ids: [],
    };
  if (selected === "unsupported")
    return {
      events: [
        tool(
          "knowledge_search",
          { query: "current AWS prices" },
          "No curated evidence establishes current prices.",
        ),
        { title: "Evidence insufficient" },
      ],
      state: "FAILED",
      reason: "UNSUPPORTED",
      answer:
        "Insufficient retrieved evidence to support this answer. The curated knowledge tool cannot verify current AWS prices.",
      ids: [],
    };
  if (selected === "loop")
    return {
      events: Array.from({ length: budget }, () =>
        tool("knowledge_search", { query: "SQS" }, sources["AWS-SQS"].text, [
          "AWS-SQS",
        ]),
      ),
      state: "LIMIT_REACHED",
      reason: "STEP_LIMIT",
      answer:
        "Stopped at the configured step limit. Review the observations or simplify your task.",
      ids: [],
    };
  if (selected === "invalid")
    return {
      events: [
        {
          title: "Tool rejected",
          observation:
            "The requested shell action is not on the allowlist. Nothing was executed.",
          error: "INVALID_TOOL",
        },
      ],
      state: "FAILED",
      reason: "INVALID_TOOL",
      answer:
        "The requested tool is not allowed. Only calculator and knowledge_search can execute.",
      ids: [],
    };
  return {
    events: [
      {
        title: "Execution stopped safely",
        observation:
          "Simulated model service failure. No raw exception or private reasoning is exposed.",
        error: "MODEL_ERROR",
      },
    ],
    state: "FAILED",
    reason: "MODEL_ERROR",
    answer:
      "Execution stopped. Retry or simplify the task. This scenario intentionally simulates a service failure.",
    ids: [],
  };
}
function appendEvent(event, index, budget) {
  const item = element("li", undefined, "event");
  item.append(
    element("span", String(index + 1), "event-number"),
    element("h3", event.title, "event-title"),
  );
  if (event.name) item.append(element("span", event.name, "tool-tag"));
  if (event.observation) {
    const details = element("details");
    details.append(element("summary", "View observation"));
    if (event.input)
      details.append(
        element("pre", "Input\n" + JSON.stringify(event.input, null, 2)),
      );
    details.append(element("pre", event.observation));
    item.append(details);
  }
  if (event.error) item.append(element("span", event.error, "tool-tag"));
  if (event.ids?.length)
    item.append(element("p", event.ids.join(" · "), "event-citations"));
  $("#events").append(item);
  $("#step-count").textContent = `${index + 1} / ${budget}`;
  $("#event-count").textContent = `${index + 1} ${index ? "EVENTS" : "EVENT"}`;
}
function finish(fixture) {
  setStatus(
    fixture.state,
    fixture.state === "SUCCEEDED"
      ? "Execution complete. Inspect the trace for details."
      : "Execution stopped. Inspect the termination reason.",
  );
  $("#termination").textContent = fixture.reason;
  $("#answer").textContent = fixture.answer;
  $("#answer").dataset.state = fixture.state;
  answerText = fixture.answer;
  $("#sources").replaceChildren();
  for (const id of fixture.ids) {
    const actualIds = new Set(
      [...$("#events").querySelectorAll(".event-citations")].flatMap((node) =>
        node.textContent.split(" · "),
      ),
    );
    if (!actualIds.has(id)) continue;
    const details = element("details");
    details.append(
      element("summary", `${id} · ${sources[id].title}`),
      element("p", sources[id].text),
    );
    $("#sources").append(details);
  }
  $("#copy").hidden = false;
  controls(false);
}
async function play() {
  if (running) return;
  clearRun();
  const task = $("#task").value.trim();
  if (!task || task.length > 2000) return;
  const budget = Number($("#budget").value);
  let fixture;
  try {
    fixture = buildFixture(budget);
  } catch (error) {
    $("#input-error").textContent = error.message;
    $("#input-error").hidden = false;
    return;
  }
  const thisRevision = revision;
  const delay =
    $("#speed").value === "fast" ||
    matchMedia("(prefers-reduced-motion: reduce)").matches
      ? 80
      : 600;
  controls(true);
  setStatus("QUEUED", "The demo task is queued for execution.");
  $("#step-count").textContent = `0 / ${budget}`;
  const pause = () => new Promise((resolve) => setTimeout(resolve, delay));
  await pause();
  if (thisRevision !== revision) return;
  setStatus("RUNNING", "The controller is validating and recording actions.");
  $("#empty-timeline").hidden = true;
  for (const [index, event] of fixture.events.slice(0, budget).entries()) {
    await pause();
    if (thisRevision !== revision) return;
    appendEvent(event, index, budget);
  }
  await pause();
  if (thisRevision !== revision) return;
  if (fixture.events.length > budget)
    fixture = {
      ...fixture,
      state: "LIMIT_REACHED",
      reason: "STEP_LIMIT",
      answer: "Stopped at the configured step limit.",
      ids: [],
    };
  finish(fixture);
}
for (const button of document.querySelectorAll("[data-scenario]"))
  button.addEventListener("click", () => choose(button.dataset.scenario));
$("#task").addEventListener("input", count);
$("#minutes").addEventListener("input", updateCalculation);
$("#rate").addEventListener("input", updateCalculation);
$("#reset").addEventListener("click", clearRun);
$("#run").addEventListener("click", play);
$("#copy").addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText(answerText);
    $("#copy").textContent = "Copied";
  } catch {
    $("#copy").textContent = "Select the answer to copy";
  }
});
choose("aws");

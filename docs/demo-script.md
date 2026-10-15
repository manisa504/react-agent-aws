# Two-to-three-minute demo

**0:00–0:25 — Problem.** Tool-using assistants need bounds and evidence. Explain React UI versus ReAct agent behavior. State whether the demonstration is local MOCK or a verified live Bedrock deployment.

**0:25–1:05 — Success.** Open `/app`, select AWS decision, inspect the task, and run it. Show search, calculator, the 7,200-image result, actual source IDs, and the final reason. Expand one observation. Explain that this is an action trace, not private reasoning. Curated notes are not current AWS documentation; mock token usage is not reported.

**1:05–1:35 — Bounds.** In local MOCK mode select Bounded loop. Show five events and STEP_LIMIT. Show Unsupported or enter `[invalid]` to demonstrate a bounded failure. Describe these as deterministic engineering tests, not a live model quality benchmark.

**1:35–2:15 — Architecture.** Open the SVG or editable draw.io diagram. Trace authenticated HTTP submission, SQS, the separate worker, Bedrock, tools, DynamoDB, and polling. Explain owner isolation and why claimed-run crash recovery is deferred.

**2:15–2:45 — Evidence and next steps.** Show the executed twelve-fixture report and test results. State deployment verification accurately. Explain separately managed Amplify teardown and retained data. Future improvements could include stale-run recovery and broader live-model evaluation; they are outside this build.

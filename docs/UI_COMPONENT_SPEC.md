# React UI Component Specification — Manisha's ReAct Agent Workbench

**Version:** 1.2 · **Audience:** implementation in React 18+/TypeScript/Vite · **Scope:** one working task workbench, not an enterprise command center.

## 1. Information architecture

Single authenticated application route `/app` and public marketing/documentation route `/` (documentation is independently publishable at `docs/index.html`). The UI has one workflow: enter a task → submit → poll → inspect steps → review answer/termination. No feature creep into multi-agent swarms, analytics consoles or long-term memory.

### Desktop wireframe (>= 1024 px)

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ Mark  ReAct Agent Workbench           MOCK/BEDROCK  Region     User/Sign out│
├──────────────────────────────────────────────────────────────────────────┤
│ Hero: Plan with tools. Finish safely.                                   │
│ ┌──────────────────────────────────────────────────────────────────────┐ │
│ │ Task input (0–2,000 chars)                            [Run task →] │ │
│ │ Example chips: AWS decision | Calculation | Unsupported | Loop     │ │
│ └──────────────────────────────────────────────────────────────────────┘ │
│ ┌───────────────────────────┐ ┌────────────────────────────────────────┐ │
│ │ Run summary               │ │ Execution timeline                     │ │
│ │ Status + reason           │ │ #1 Decision summary                     │ │
│ │ Steps used / Token count  │ │ #2 Tool: knowledge_search               │ │
│ │ Model mode / Duration     │ │ #3 Tool: calculator                     │ │
│ │ [View errors]             │ │ #4 Finished / stopped                   │ │
│ └───────────────────────────┘ └────────────────────────────────────────┘ │
│ ┌──────────────────────────────────────────────────────────────────────┐ │
│ │ Final answer / limitations / citations                             │ │
│ └──────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────┘
```

Mobile (< 768 px): single column, task composer first, run summary, timeline, final answer. No horizontal overflow. Avoid nested scroll traps.

## 2. Component tree

```tsx
<App>
  <AuthProvider>
    <AppShell>
      <Header><Brand/><ModeBadge/><AccountMenu/></Header>
      <ProtectedRoute>
        <WorkbenchPage>
          <PageIntro />
          <TaskComposer><SamplePromptChips/><CharacterCounter/><SubmitButton/></TaskComposer>
          <RunWorkspace>
            <RunSummary><StatusBadge/><MetricItem/><TerminationReason/></RunSummary>
            <ExecutionTimeline><StepCard/><ToolObservation/><StepError/></ExecutionTimeline>
            <AnswerPanel><CitationList/><EvidenceWarning/></AnswerPanel>
          </RunWorkspace>
          <FeedbackBanner />
        </WorkbenchPage>
      </ProtectedRoute>
    </AppShell>
  </AuthProvider>
</App>
```

## 3. Exact component contracts

| Component | Props / state | Behavior & requirements |
|---|---|---|
| `AppShell` | `{children}` | max width 1200px; skip-to-content; consistent focus indicators |
| `Header` | `{mode:'MOCK'\|'BEDROCK', user}` | Clearly identify fake runs; provide sign-out; no false cloud-connected badge |
| `TaskComposer` | `{initialTask?,onSubmit(task,maxSteps),isSubmitting}` | Required textarea, 2,000 char limit, submit disabled when blank/submitting, `maxSteps` selection default 5 range 3–8 |
| `SamplePromptChips` | `{onSelect(task)}` | Three to four safe hardcoded demo inputs; filling editor never auto-submits |
| `RunSummary` | `{run:Run|null}` | `QUEUED/RUNNING/SUCCEEDED/LIMIT_REACHED/FAILED` status, mode, run ID copy, elapsed time if derived; tokens from API only |
| `StatusBadge` | `{status}` | Text + icon, not color alone; `aria-live=polite` for updates |
| `ExecutionTimeline` | `{steps:StepEvent[],loading}` | Numeric order by `step_number`, empty skeleton, timestamp, tool, sanitized observation; no private chain of thought |
| `StepCard` | `{step:StepEvent}` | Collapsible sanitized JSON observation; long inputs truncated; keyboard operable |
| `AnswerPanel` | `{run,steps}` | Render final plain text (safe markdown optional, XSS sanitized); empty until final; visibly mark unsupported evidence |
| `CitationList` | `{sources:SourceRef[]}` | Only source IDs found in retrieved step evidence; no invented click targets |
| `FeedbackBanner` | `{message,type,onDismiss}` | Announce errors with `role=alert`; offer retry only after terminal failure |
| `ProtectedRoute` | `{children}` | Cognito in cloud, clearly isolated bypass in explicitly configured local demo |

## 4. Types and network contract

```ts
type RunStatus = 'QUEUED'|'RUNNING'|'SUCCEEDED'|'LIMIT_REACHED'|'FAILED';
type ExecutionMode = 'MOCK'|'BEDROCK';
type TerminationReason = 'FINAL_ANSWER'|'STEP_LIMIT'|'UNSUPPORTED'|'MODEL_ERROR'|'TOOL_ERROR'|'TIMEOUT'|'INVALID_TOOL';
type StepEvent = {step_number:number; timestamp:string; action_summary:string; tool_name?:'calculator'|'knowledge_search'; observation?:string; source_ids?:string[]; error?:string};
type Run = {run_id:string; status:RunStatus; execution_mode:ExecutionMode; max_steps:number; steps_used:number; token_usage?:{input:number;output:number}; termination_reason?:TerminationReason; final_answer?:string; created_at:string; completed_at?:string};
```

`POST /runs` creates a task (202); `GET /runs/:id` polls every 2–3 seconds while not terminal; `GET /runs/:id/steps` returns ordered events. Cancel polling on route exit/unmount and stop on terminal. Do not assume WebSockets or streaming.

## 5. Full UX state matrix

- **Signed-out**: concise benefits + login button; don't show task data.
- **Idle**: example tasks, empty run workspace, prompt ready.
- **Submitting**: disable duplicate submit, spinner, preserve editor on API error.
- **Queued**: show message 'Waiting for worker' + progress indeterminate.
- **Running**: poll and update timeline without scroll jumps; never show raw model thoughts.
- **Success**: answer + actual cited sources + final reason; never fabricate token totals.
- **Step limit**: amber indication + last known observations + explicit stopping reason, no success claim.
- **Failure**: red failure notice with sanitized type and guided retry, not raw stack trace.
- **Empty/unsupported evidence**: distinguish factual uncertainty from crash.
- **Network failure**: paused polling and 'Reconnect' control; don't retry writes automatically.
- **Access denied**: redirect to login for 401; display forbidden for 403.

## 6. Design tokens & accessibility

Use restrained dark-navy/slate surfaces with an electric-indigo primary action, white text, quiet borders. Spacing 4/8/12/16/24/32px, border radius 12–18px, font Inter/system sans; body >= 14px. Prefer Tailwind CSS variables for colors; no hard-coded data visualization. Ensure WCAG AA text contrast, keyboard navigation, visible focus, semantic `<main>`/`<section>` headings, aria labels on icons, motion reduced for `prefers-reduced-motion`, and 320px minimum viewport support. Add tests for input validation, loading, timeline, limit/error, mocked mode and accessibility labels.

## 7. Suggested files

```
frontend/src/
  pages/WorkbenchPage.tsx
  components/{AppShell,Header,TaskComposer,SamplePromptChips,RunSummary,StatusBadge,ExecutionTimeline,StepCard,AnswerPanel,CitationList,FeedbackBanner}.tsx
  hooks/{useRunPolling,useAuth}.ts
  lib/{api,config}.ts
  types/{run}.ts
  styles/index.css
```

**Non-goals:** interactive graph editor, admin console, agent swarm visualization, usage billing panel, prompt version management. Treat UI screenshots on `docs/index.html` as conceptual until the actual application exists.

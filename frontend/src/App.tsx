import { useState, type ReactNode } from "react";
import {
  ArrowRight,
  ArrowUpRight,
  Box,
  ChevronRight,
  ShieldCheck,
  Workflow,
  Wrench,
  LogOut,
  LoaderCircle,
} from "lucide-react";
import { AuthProvider, useAuth } from "./hooks/useAuth";
import { config } from "./lib/config";
import { api, ApiError } from "./lib/api";
import { useRunPolling } from "./hooks/useRunPolling";
import { terminal } from "./types/run";
import { TaskComposer } from "./components/TaskComposer";
import {
  AnswerPanel,
  ExecutionTimeline,
  FeedbackBanner,
  RunSummary,
} from "./components/RunPanels";

function Brand() {
  return (
    <a href="/" className="brand" aria-label="ReAct Workbench home">
      <span className="brand-icon">
        <Workflow size={22} />
      </span>
      <strong>
        ReAct<span> / </span>
        <span className="brand-light">Workbench</span>
      </strong>
    </a>
  );
}
export function AppShell({ children }: { children: ReactNode }) {
  const auth = useAuth();
  return (
    <>
      <a className="skip" href="#main">
        Skip to content
      </a>
      <header>
        <div className="header-inner">
          <Brand />
          <div className="header-right">
            <span className={`mode ${config.demo ? "mock" : ""}`}>
              <span className="live-dot" />
              {config.demo ? "MOCK · LOCAL DEMO" : "CLOUD · COGNITO"}
            </span>
            <span className="region">
              {config.demo ? "Local runtime" : config.region}
            </span>
            {auth.user && !config.demo && (
              <button
                className="account"
                onClick={() => void auth.logout()}
                aria-label="Sign out"
              >
                <LogOut size={16} />
                <span>{auth.user}</span>
              </button>
            )}
          </div>
        </div>
      </header>
      {children}
      <footer>
        <span>Built by Manisha · React + Python + AWS</span>
        <span>
          <ShieldCheck size={13} /> Safe tools. Bounded execution. Visible
          evidence.
        </span>
      </footer>
    </>
  );
}
function SignIn() {
  const auth = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const configured = !!config.userPoolId && !!config.userPoolClientId;
  return (
    <section className="panel login">
      <span className="eyebrow">YOUR WORKSPACE</span>
      <h1>
        {auth.newPassword
          ? "Set your new password"
          : "Sign in to start planning."}
      </h1>
      <p className="muted">
        Run safe tools and inspect an evidence-led execution trace.
      </p>
      {!configured && (
        <FeedbackBanner message="Cloud sign-in is not configured. Set the Cognito build variables, or use make dev for the local demo." />
      )}
      {error && <FeedbackBanner message={error} />}
      <form
        onSubmit={async (e) => {
          e.preventDefault();
          setBusy(true);
          setError("");
          try {
            if (auth.newPassword) await auth.changePassword(password);
            else await auth.login(username, password);
          } catch {
            setError(
              "Sign-in failed. Check your credentials and required password policy.",
            );
          } finally {
            setBusy(false);
          }
        }}
      >
        {!auth.newPassword && (
          <>
            <label htmlFor="username">Email</label>
            <input
              id="username"
              type="email"
              autoComplete="username"
              required
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />
          </>
        )}
        <label htmlFor="password">
          {auth.newPassword ? "New password" : "Password"}
        </label>
        <input
          id="password"
          type="password"
          autoComplete={auth.newPassword ? "new-password" : "current-password"}
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        <button className="primary" disabled={busy || !configured}>
          {busy ? "Signing in…" : auth.newPassword ? "Set password" : "Sign in"}
          <ArrowRight size={16} />
        </button>
      </form>
      <p className="small muted">
        Demo identities are provisioned by the project owner.
      </p>
    </section>
  );
}
function ProtectedRoute({ children }: { children: ReactNode }) {
  const auth = useAuth();
  if (auth.loading)
    return (
      <p role="status">
        <LoaderCircle className="spin" /> Checking your session…
      </p>
    );
  if (!auth.user) return <SignIn />;
  return children;
}
function WorkbenchPage() {
  const [id, setId] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [sessionExpired, setSessionExpired] = useState(false);
  const polling = useRunPolling(id);
  const active = !!id && (!polling.run || !terminal(polling.run.status));
  async function submit(task: string, maxSteps: number) {
    setSubmitting(true);
    setError("");
    try {
      const result = await api.create(task, maxSteps);
      setId(result.run_id);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Submission failed.");
      if (e instanceof ApiError && e.status === 401) setSessionExpired(true);
    } finally {
      setSubmitting(false);
    }
  }
  if (polling.unauthorized || sessionExpired)
    return (
      <>
        <FeedbackBanner message="Your session expired. Sign in to continue." />
        <SignIn />
      </>
    );
  return (
    <>
      <div className="page-intro">
        <div>
          <div className="breadcrumb">
            <span>WORKSPACE</span>
            <ChevronRight size={12} />
            <span>Planning agent</span>
          </div>
          <h1>
            Plan with tools.
            <br className="mobile-break" /> <span>Finish safely.</span>
          </h1>
          <p>
            Give your agent a task. Follow its actions. Know why it stopped.
          </p>
        </div>
        <div className="intro-note">
          <span className="live-dot" /> BOUNDED REACT AGENT
          <br />
          <span>2 tools · up to 8 steps · evidence first</span>
        </div>
      </div>
      {config.demo && (
        <div className="demo-notice">
          <Box size={15} />
          <span>
            <strong>Local mock mode.</strong> Scripted scenarios, real tool
            execution. Runs reset when the API restarts.
          </span>
          <span className="demo-pill">NO AWS REQUIRED</span>
        </div>
      )}
      {error && (
        <FeedbackBanner message={error} onDismiss={() => setError("")} />
      )}
      <TaskComposer
        onSubmit={submit}
        isSubmitting={submitting}
        disabled={active}
      />
      {polling.error && (
        <>
          <FeedbackBanner message={`${polling.error} Polling paused.`} />
          <button className="secondary reconnect" onClick={polling.reconnect}>
            Reconnect
          </button>
        </>
      )}
      <div className="workspace">
        <RunSummary run={polling.run} />
        <ExecutionTimeline steps={polling.steps} loading={active} />
      </div>
      <AnswerPanel run={polling.run} steps={polling.steps} />
      <p className="privacy-note">
        <ShieldCheck size={13} /> Concise action summaries only. Private model
        reasoning is never displayed. Curated knowledge is not live AWS
        documentation.
      </p>
    </>
  );
}
function Landing() {
  return (
    <div className="landing">
      <div className="eyebrow">AN AI ENGINEERING PROJECT BY MANISHA</div>
      <h1>
        A little more evidence.
        <br />
        <span>A lot more clarity.</span>
      </h1>
      <p className="landing-description">
        An inspectable planning agent that chooses safe tools, shows what
        happened, and knows when to stop.
      </p>
      <a className="primary" href="/app">
        Open the workbench
        <ArrowUpRight size={18} />
      </a>
      <div className="feature-grid">
        {[
          {
            icon: Wrench,
            title: "Two tools. Real work.",
            text: "Calculate safely and retrieve cited, curated knowledge.",
          },
          {
            icon: Workflow,
            title: "Follow every action.",
            text: "Inspect ordered observations without exposing private reasoning.",
          },
          {
            icon: ShieldCheck,
            title: "A finish line, built in.",
            text: "A strict step budget and explicit stopping reasons.",
          },
        ].map(({ icon: Icon, title, text }) => (
          <article className="panel" key={title}>
            <Icon size={23} />
            <h2>{title}</h2>
            <p>{text}</p>
          </article>
        ))}
      </div>
      <div className="landing-stack">
        React / TypeScript <span>+</span> FastAPI / Python <span>+</span> Amazon
        Bedrock / AWS
      </div>
      {config.demo && (
        <p className="muted small">
          Local mock preview · cloud deployment status is documented separately.
        </p>
      )}
    </div>
  );
}
export default function App() {
  const workbench = window.location.pathname.startsWith("/app");
  return (
    <AuthProvider>
      <AppShell>
        <main id="main">
          {workbench ? (
            <ProtectedRoute>
              <WorkbenchPage />
            </ProtectedRoute>
          ) : (
            <Landing />
          )}
        </main>
      </AppShell>
    </AuthProvider>
  );
}

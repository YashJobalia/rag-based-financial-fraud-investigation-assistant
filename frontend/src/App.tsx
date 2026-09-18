import { useEffect, useRef, useState, type FormEvent } from "react";
import {
  ArrowDownLeft,
  ArrowRight,
  BookOpen,
  Check,
  ChevronRight,
  CircleHelp,
  Clock3,
  FileCheck2,
  FileText,
  Fingerprint,
  Inbox,
  KeyRound,
  Layers3,
  LockKeyhole,
  Search,
  ShieldCheck,
  Sparkles,
  X,
} from "lucide-react";
import {
  api,
  setSessionToken,
  type Brief,
  type Case,
  type Detail,
  type Evidence,
  type Retrieval,
  type Session,
} from "./api";

type Tab = "overview" | "brief" | "sources" | "review";
const money = (minor: number) =>
  new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(
    minor / 100,
  );
const time = (value?: string) =>
  value
    ? new Date(value).toLocaleTimeString("en-GB", {
        hour: "2-digit",
        minute: "2-digit",
        timeZone: "UTC",
      })
    : "—";
const date = (value: string) =>
  new Date(value).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    timeZone: "UTC",
  });
const defaultQuery =
  '"new device" OR "new recipient" OR "replacement phone" OR "customer contact" OR "password reset"';

export default function App() {
  const [session, setSession] = useState<Session | null>(null);
  const [cases, setCases] = useState<Case[]>([]);
  const [detail, setDetail] = useState<Detail | null>(null);
  const [tab, setTab] = useState<Tab>("overview");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState("");
  const [brief, setBrief] = useState<Brief | null>(null);
  const [retrieval, setRetrieval] = useState<Retrieval | null>(null);
  const [query, setQuery] = useState(defaultQuery);
  const [source, setSource] = useState<Evidence | null>(null);
  const [sourceLoading, setSourceLoading] = useState(false);
  const [authOpen, setAuthOpen] = useState(false);
  const [token, setToken] = useState("");
  const [notes, setNotes] = useState("");
  const [disposition, setDisposition] = useState("needs_more_evidence");
  const [saved, setSaved] = useState("");
  const [reviews, setReviews] = useState<
    { id: string; notes: string; disposition: string; created_at: string }[]
  >([]);
  const dialogRef = useRef<HTMLDialogElement>(null);
  const authRef = useRef<HTMLDialogElement>(null);
  async function load() {
    setError("");
    try {
      const [s, list] = await Promise.all([
        api<Session>("/session"),
        api<Case[]>("/cases"),
      ]);
      setSession(s);
      setCases(list);
      if (list.length) setDetail(await api<Detail>(`/cases/${list[0].id}`));
    } catch (e) {
      setError((e as Error).message);
    }
  }
  useEffect(() => {
    void load();
  }, []);
  useEffect(() => {
    if (source || sourceLoading) dialogRef.current?.showModal();
    else dialogRef.current?.close();
  }, [source, sourceLoading]);
  useEffect(() => {
    if (authOpen) authRef.current?.showModal();
    else authRef.current?.close();
  }, [authOpen]);
  async function openEvidence(id: string) {
    if (!detail) return;
    setSourceLoading(true);
    setSource(null);
    setError("");
    try {
      setSource(
        await api<Evidence>(
          `/cases/${detail.case.id}/evidence/${encodeURIComponent(id)}`,
        ),
      );
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setSourceLoading(false);
    }
  }
  async function generate(mode: "reference" | "live") {
    if (!detail) return;
    setBusy("brief");
    setError("");
    setSaved("");
    try {
      const result = await api<Brief>(`/cases/${detail.case.id}/briefs`, {
        mode,
        retrieval_mode: "keyword",
      });
      setBrief(result);
      setRetrieval(result.retrieval);
      setTab("brief");
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy("");
    }
  }
  async function search(event: FormEvent) {
    event.preventDefault();
    if (!detail) return;
    setBusy("search");
    setError("");
    try {
      setRetrieval(
        await api<Retrieval>(`/cases/${detail.case.id}/retrieve`, {
          query,
          mode: "keyword",
          k: 8,
        }),
      );
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy("");
    }
  }
  async function signIn(event: FormEvent) {
    event.preventDefault();
    setSessionToken(token.trim());
    setToken("");
    setError("");
    try {
      setSession(await api<Session>("/session"));
      setAuthOpen(false);
      await load();
    } catch (e) {
      setSessionToken("");
      setError((e as Error).message);
    }
  }
  async function saveReview(event: FormEvent) {
    event.preventDefault();
    if (!detail || !brief) return;
    setBusy("review");
    setError("");
    try {
      const result = await api<{ message: string }>(
        `/cases/${detail.case.id}/reviews`,
        { brief_id: brief.id, notes, disposition },
      );
      setSaved(result.message);
      setNotes("");
      setReviews(await api(`/cases/${detail.case.id}/reviews`));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy("");
    }
  }
  async function changeTab(value: Tab) {
    setTab(value);
    if (value === "review" && session?.role === "analyst" && detail) {
      try {
        setReviews(await api(`/cases/${detail.case.id}/reviews`));
      } catch (e) {
        setError((e as Error).message);
      }
    }
  }
  const citations = (ids: string[]) => (
    <span className="citations">
      {ids.map((id) => (
        <button
          key={id}
          onClick={() => void openEvidence(id)}
          title={`Open evidence ${id}`}
        >
          <FileText size={11} />
          {id}
        </button>
      ))}
    </span>
  );
  return (
    <div className="shell">
      <aside className="sidebar">
        <a
          className="identity"
          href="/"
          aria-label="Investigation workspace home"
        >
          <span className="identity-icon">
            <Fingerprint size={27} />
          </span>
          <span>
            FINANCIAL FRAUD
            <br />
            <strong>Investigation Assistant</strong>
          </span>
        </a>
        <div className="workspace-label">ANALYST WORKSPACE</div>
        <button className="side-link active" onClick={() => setTab("overview")}>
          <Inbox size={18} /> Alert inbox{" "}
          <span className="count">{cases.length}</span>
        </button>
        <button className="side-link" onClick={() => void changeTab("sources")}>
          <BookOpen size={18} /> Evidence library
        </button>
        <button className="side-link" onClick={() => void changeTab("review")}>
          <FileCheck2 size={18} /> Analyst review
        </button>
        <div className="sidebar-rule" />
        <div className="workspace-label">ASSIGNED CASES</div>
        {cases.map((c) => (
          <button
            className="case-card"
            key={c.id}
            onClick={() => setTab("overview")}
          >
            <span>
              <i className="amber-dot" />
              {c.id}
              <ChevronRight size={14} />
            </span>
            <strong>{c.title}</strong>
            <small>{c.account_id} · Awaiting review</small>
          </button>
        ))}
        <div className="sidebar-bottom">
          <div className="demo-icon">
            <Layers3 size={18} />
          </div>
          <strong>A safe space to investigate</strong>
          <p>
            All accounts and activity are synthetic. All source documents are
            fictional.
          </p>
          <span className="sidebar-tag">PORTFOLIO DEMONSTRATION</span>
        </div>
        <button className="profile" onClick={() => setAuthOpen(true)}>
          <span className="avatar">
            {session?.role === "analyst" ? "AN" : "DE"}
          </span>
          <span>
            <strong>
              {session?.role === "analyst" ? "Local analyst" : "Demo explorer"}
            </strong>
            <small>
              {session?.role === "analyst"
                ? "Review access enabled"
                : "Read-only case access"}
            </small>
          </span>
          <KeyRound size={15} />
        </button>
      </aside>
      <main>
        <header className="topbar">
          <div>
            Investigations <ChevronRight size={13} />{" "}
            <strong>{detail?.case.id ?? "Case workspace"}</strong>
          </div>
          <span>
            <span className="green-dot" /> Synthetic environment
          </span>
        </header>
        <div className="page">
          <div className="eyebrow">
            <span className="badge amber">ACCOUNT TAKEOVER · SUSPECTED</span>
            <span className="muted">Evidence first. Analyst decided.</span>
          </div>
          <div className="title-row">
            <div>
              <h1>{detail?.case.title ?? "Investigation workspace"}</h1>
              <p className="subtitle">
                RAG-Based Financial Fraud Investigation Assistant
              </p>
            </div>
            <button
              className="primary"
              onClick={() => void generate("reference")}
              disabled={!!busy || !detail}
            >
              <Sparkles size={16} />
              {busy === "brief"
                ? "Preparing brief…"
                : "Prepare reference brief"}
              <ArrowRight size={15} />
            </button>
          </div>
          <div className="case-meta">
            <span>
              <Fingerprint size={14} />
              {detail?.case.account_id ?? "—"}
            </span>
            <span>
              <Clock3 size={14} />
              {detail ? date(detail.case.cutoff_at) : "—"} · Snapshot at 10:00
              UTC
            </span>
            <span className="badge neutral">
              {saved ? "Review recorded" : "Open investigation"}
            </span>
          </div>
          {error && (
            <div className="error" role="alert">
              {error}
              <button
                onClick={() => {
                  setError("");
                  if (!detail) void load();
                }}
              >
                Retry / dismiss
              </button>
            </div>
          )}
          {!detail && !error && (
            <div className="empty" role="status">
              Loading authorized case evidence…
            </div>
          )}
          {detail && (
            <>
              <div className="metrics">
                <div>
                  <span>COMPLETED TRANSFERS TODAY</span>
                  <strong>
                    {money(detail.totals[0]?.total_minor ?? 0)}
                    <small>USD</small>
                  </strong>
                  <p>
                    {detail.totals[0]?.count ?? 0} transfers · current snapshot
                  </p>
                </div>
                <div>
                  <span>PREVIOUS 30-DAY MAXIMUM</span>
                  <strong>{money(detail.baseline[0]?.max_minor ?? 0)}</strong>
                  <p>
                    {detail.baseline[0]?.count ?? 0} completed USD transfers
                  </p>
                </div>
                <div>
                  <span>EVIDENCE IN TIMELINE</span>
                  <strong>
                    {detail.timeline.length}
                    <small>records</small>
                  </strong>
                  <p>Source-linked · chronological</p>
                </div>
                <div>
                  <span>AUTHORIZATION STATUS</span>
                  <strong className="status-value">Unresolved</strong>
                  <p>Independent confirmation missing</p>
                </div>
              </div>
              <nav className="tabs" aria-label="Case sections">
                {(
                  [
                    ["overview", "Case overview"],
                    ["brief", "Investigation brief"],
                    ["sources", "Retrieved sources"],
                    ["review", "Analyst review"],
                  ] as [Tab, string][]
                ).map(([value, label]) => (
                  <button
                    key={value}
                    className={tab === value ? "selected" : ""}
                    aria-current={tab === value ? "page" : undefined}
                    onClick={() => void changeTab(value)}
                  >
                    {label}
                    {value === "brief" && brief && <span className="tab-dot" />}
                  </button>
                ))}
              </nav>
              {tab === "overview" && (
                <div className="overview-grid">
                  <section className="panel timeline-panel">
                    <div className="panel-heading">
                      <div>
                        <h2>Evidence timeline</h2>
                        <p>What happened, in the order it happened.</p>
                      </div>
                      <span className="mini-tag">ALL TIMES UTC</span>
                    </div>
                    <ol className="timeline">
                      {detail.timeline.map((e) => (
                        <li key={e.id}>
                          <time>{time(e.occurred_at)}</time>
                          <span
                            className={`event-icon ${e.kind === "transaction" ? "transfer" : e.kind === "alert" ? "alert-icon" : ""}`}
                          >
                            {e.kind === "transaction" ? (
                              <ArrowDownLeft size={17} />
                            ) : e.kind === "alert" ? (
                              <ShieldCheck size={17} />
                            ) : (
                              <Fingerprint size={17} />
                            )}
                          </span>
                          <div>
                            <button
                              className="event-title"
                              onClick={() => void openEvidence(e.id)}
                            >
                              {e.title}
                              <ChevronRight size={13} />
                            </button>
                            <p>{e.description}</p>
                            <button
                              className="record-link"
                              onClick={() => void openEvidence(e.id)}
                            >
                              {e.id} <ArrowRight size={11} />
                            </button>
                          </div>
                        </li>
                      ))}
                    </ol>
                    <div className="panel-footer">
                      <LockKeyhole size={13} /> Evidence is scoped to this case
                      and its cutoff.
                    </div>
                  </section>
                  <div className="insight-column">
                    <section className="panel alert-panel">
                      <span className="section-kicker">
                        <ShieldCheck size={15} /> WHY THIS WAS FLAGGED
                      </span>
                      <h2>A sequence worth investigating</h2>
                      <p>{detail.alerts[0]?.description}</p>
                      <div className="rule-chain">
                        <span>New device</span>
                        <ArrowRight size={13} />
                        <span>New recipient</span>
                        <ArrowRight size={13} />
                        <span>Transfers</span>
                      </div>
                      {detail.alerts[0] && citations([detail.alerts[0].id])}
                      <div className="rule-version">
                        Explicit rule · {detail.alerts[0]?.rule_id} v
                        {detail.alerts[0]?.rule_version}
                      </div>
                    </section>
                    <section className="panel">
                      <span className="section-kicker green">
                        <CircleHelp size={16} /> KEEP BOTH EXPLANATIONS OPEN
                      </span>
                      <h3>A new phone may be legitimate.</h3>
                      <p>
                        A support notice reports a replacement device. It is an
                        explanation to verify, not proof that the payments were
                        authorized.
                      </p>
                      {citations(["EV-001", "EV-002"])}
                      <div className="soft-divider" />
                      <h3>What we still need</h3>
                      <p>
                        Verified customer confirmation, payment purpose, and
                        authentication challenge records.
                      </p>
                      {citations(["SCOPE:CASE-001:v1"])}
                    </section>
                    <div className="quiet-note">
                      <ShieldCheck size={18} />
                      <p>
                        The assistant assembles evidence.
                        <br />
                        <strong>The analyst makes the decision.</strong>
                      </p>
                    </div>
                  </div>
                </div>
              )}
              {tab === "brief" && (
                <section className="panel brief-panel">
                  <div className="panel-heading">
                    <div>
                      <h2>Investigation brief</h2>
                      <p>
                        Observed facts, alternative explanations, and next
                        checks.
                      </p>
                    </div>
                    <span className="badge neutral">
                      {brief?.mode === "live"
                        ? "AI-generated · review required"
                        : "Deterministic reference"}
                    </span>
                  </div>
                  <div className="info-strip">
                    <FileText size={17} />
                    <span>
                      {brief?.mode === "live"
                        ? "Generated from the scoped evidence bundle. Check the supporting sources before making a decision."
                        : "This reference brief is assembled without an LLM. It demonstrates citations and workflow; it is not a measurement of AI quality."}
                    </span>
                  </div>
                  {brief ? (
                    <>
                      <div className="brief-sections">
                        {brief.content.sections.map((s, index) => (
                          <section key={s.heading}>
                            <span className="section-number">0{index + 1}</span>
                            <div>
                              <h3>{s.heading}</h3>
                              {s.claims.map((c, i) => (
                                <div className="claim" key={i}>
                                  <span className={`claim-kind ${c.kind}`}>
                                    {c.kind.replace("_", " ")}
                                  </span>
                                  <p>{c.text}</p>
                                  {citations(c.evidence_ids)}
                                </div>
                              ))}
                            </div>
                          </section>
                        ))}
                      </div>
                      <div className="conclusion">
                        <ShieldCheck size={21} />
                        <div>
                          <strong>{brief.content.conclusion}</strong>
                          <p>
                            No account restrictions or payment actions have been
                            taken.
                          </p>
                        </div>
                        <button
                          className="secondary"
                          onClick={() => void changeTab("review")}
                        >
                          Review brief <ArrowRight size={14} />
                        </button>
                      </div>
                      <p className="run-meta">
                        {brief.mode === "live"
                          ? brief.model
                          : "Reference renderer v1"}{" "}
                        · {brief.duration_ms.toFixed(0)} ms ·{" "}
                        {brief.usage.input_tokens + brief.usage.output_tokens}{" "}
                        model tokens ·{" "}
                        {brief.usage.estimated_cost_usd === null
                          ? "Cost not configured"
                          : `$${brief.usage.estimated_cost_usd.toFixed(4)} estimated model cost`}
                      </p>
                      <p className="run-meta">{brief.validation}</p>
                    </>
                  ) : (
                    <div className="empty">
                      <FileText size={30} />
                      <h3>Your brief starts with the evidence.</h3>
                      <p>
                        Prepare a reference brief to explore source-linked
                        findings and analyst review.
                      </p>
                      <button
                        className="primary"
                        onClick={() => void generate("reference")}
                        disabled={!!busy}
                      >
                        Prepare reference brief
                      </button>
                    </div>
                  )}
                  {session?.role === "analyst" && (
                    <div className="live-actions">
                      <button
                        className="secondary"
                        disabled={!session.live_available || !!busy}
                        onClick={() => void generate("live")}
                      >
                        <Sparkles size={15} /> Generate with OpenAI
                      </button>
                      <small>
                        {session.live_available
                          ? "Uses backend credentials and the daily request budget."
                          : "Live generation is disabled until backend configuration is complete."}
                      </small>
                    </div>
                  )}
                </section>
              )}
              {tab === "sources" && (
                <section className="panel">
                  <div className="panel-heading">
                    <div>
                      <h2>Retrieve investigation context</h2>
                      <p>
                        Search fictional procedures and historical reports, with
                        access checked before retrieval.
                      </p>
                    </div>
                    <span className="badge neutral">Keyword baseline</span>
                  </div>
                  <form className="search-form" onSubmit={search}>
                    <label htmlFor="query">Search query</label>
                    <div>
                      <Search size={18} />
                      <input
                        id="query"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        minLength={2}
                        maxLength={500}
                        required
                      />
                      <button className="primary" disabled={!!busy}>
                        {busy === "search" ? "Retrieving…" : "Retrieve sources"}
                      </button>
                    </div>
                  </form>
                  <div className="info-strip">
                    <Layers3 size={17} />
                    <span>
                      SQL establishes amounts and timelines. Retrieval adds
                      procedural and historical context. Vector and hybrid
                      comparisons follow the measured keyword baseline.
                    </span>
                  </div>
                  {retrieval ? (
                    <>
                      <div className="results-label">
                        {retrieval.results.length} passages retrieved ·{" "}
                        {retrieval.duration_ms.toFixed(1)} ms
                        {retrieval.abstained &&
                          " · No supporting passage found"}
                      </div>
                      <div className="source-grid">
                        {retrieval.results.map((s, i) => (
                          <article className="source-card" key={s.id}>
                            <div>
                              <span className="mini-tag">
                                {s.kind === "procedure"
                                  ? "PROCEDURE"
                                  : "HISTORICAL REPORT"}
                              </span>
                              <span className="muted">#{i + 1}</span>
                            </div>
                            <h3>{s.title}</h3>
                            <p>{s.passage}</p>
                            <button
                              className="source-open"
                              onClick={() => void openEvidence(s.id)}
                            >
                              View source passage <ArrowRight size={14} />
                            </button>
                            <small>
                              {s.id} · Fictional · v{s.version}
                            </small>
                          </article>
                        ))}
                      </div>
                      <p className="run-meta">
                        Corpus fingerprint: {retrieval.corpus_hash.slice(0, 16)}{" "}
                        · Run: {retrieval.run_id}
                      </p>
                    </>
                  ) : (
                    <div className="empty">
                      <BookOpen size={30} />
                      <h3>Context, with provenance.</h3>
                      <p>
                        Run a search or prepare a brief to see the retrieved
                        passages.
                      </p>
                    </div>
                  )}
                </section>
              )}
              {tab === "review" && (
                <section className="panel review-panel">
                  <div className="panel-heading">
                    <div>
                      <h2>Analyst review</h2>
                      <p>
                        A documented judgment, with the human analyst in
                        control.
                      </p>
                    </div>
                    <FileCheck2 size={23} />
                  </div>
                  {session?.role !== "analyst" ? (
                    <div className="empty">
                      <LockKeyhole size={30} />
                      <h3>Explore freely. Review with analyst access.</h3>
                      <p>
                        The public demo cannot save decisions or run paid model
                        calls.
                      </p>
                      <button
                        className="secondary"
                        onClick={() => setAuthOpen(true)}
                      >
                        Enter analyst session
                      </button>
                    </div>
                  ) : !brief ? (
                    <div className="empty">
                      <p>Prepare a brief before recording your review.</p>
                      <button
                        className="primary"
                        disabled={!!busy}
                        onClick={() => void generate("reference")}
                      >
                        Prepare reference brief
                      </button>
                    </div>
                  ) : (
                    <form className="review-form" onSubmit={saveReview}>
                      <label htmlFor="disposition">Review disposition</label>
                      <select
                        id="disposition"
                        value={disposition}
                        onChange={(e) => setDisposition(e.target.value)}
                      >
                        <option value="needs_more_evidence">
                          More evidence needed
                        </option>
                        <option value="escalate_for_review">
                          Escalate for human review
                        </option>
                        <option value="legitimate_explanation_supported">
                          Legitimate explanation supported
                        </option>
                      </select>
                      <label htmlFor="notes">Reasoning and next checks</label>
                      <textarea
                        id="notes"
                        placeholder="Explain your reasoning, cite evidence IDs, and identify remaining questions…"
                        value={notes}
                        onChange={(e) => setNotes(e.target.value)}
                        minLength={10}
                        maxLength={2000}
                        rows={6}
                        required
                      />
                      <p className="muted">
                        This records your assessment. It cannot freeze an
                        account or block a payment.
                      </p>
                      <button className="primary" disabled={!!busy}>
                        <Check size={16} />
                        Save analyst review
                      </button>
                    </form>
                  )}
                  {saved && (
                    <div className="success" role="status">
                      {saved}
                    </div>
                  )}
                  {reviews.map((r) => (
                    <article className="review-history" key={r.id}>
                      <strong>{r.disposition.replaceAll("_", " ")}</strong>
                      <small>
                        {date(r.created_at)} · {time(r.created_at)} UTC
                      </small>
                      <p>{r.notes}</p>
                    </article>
                  ))}
                </section>
              )}
              <footer className="page-footer">
                <span>
                  <ShieldCheck size={13} /> Synthetic data · Fictional documents
                  · Human review required
                </span>
                <span>SQL for facts. RAG for context.</span>
              </footer>
            </>
          )}
        </div>
      </main>
      <dialog
        ref={dialogRef}
        className="evidence-dialog"
        onCancel={() => {
          setSource(null);
          setSourceLoading(false);
        }}
      >
        <div className="dialog-heading">
          <span className="section-kicker">EVIDENCE INSPECTOR</span>
          <button
            aria-label="Close evidence"
            onClick={() => {
              setSource(null);
              setSourceLoading(false);
            }}
          >
            <X size={20} />
          </button>
        </div>
        {sourceLoading ? (
          <p role="status">Loading permitted evidence…</p>
        ) : (
          source && (
            <>
              <span className="badge neutral">
                {source.evidence_type} · synthetic
              </span>
              <h2>{source.title}</h2>
              <code>{source.id}</code>
              <div className="source-passage">
                {source.description ?? source.passage}
              </div>
              <dl>
                <dt>Source</dt>
                <dd>{source.source ?? source.source_uri}</dd>
                <dt>Version</dt>
                <dd>{source.version}</dd>
                {source.occurred_at && (
                  <>
                    <dt>Occurred</dt>
                    <dd>{source.occurred_at}</dd>
                  </>
                )}
                {source.recorded_at && (
                  <>
                    <dt>Recorded</dt>
                    <dd>{source.recorded_at}</dd>
                  </>
                )}
                {source.published_at && (
                  <>
                    <dt>Published</dt>
                    <dd>{source.published_at}</dd>
                  </>
                )}
                {source.content_hash && (
                  <>
                    <dt>Content hash</dt>
                    <dd className="hash">{source.content_hash}</dd>
                  </>
                )}
              </dl>
              {source.parameters && (
                <>
                  <h3>Calculation parameters</h3>
                  <pre>{JSON.stringify(source.parameters, null, 2)}</pre>
                </>
              )}
              {source.source_ids && (
                <>
                  <h3>Supporting records</h3>
                  {citations(source.source_ids)}
                </>
              )}
            </>
          )
        )}
      </dialog>
      <dialog
        ref={authRef}
        className="auth-dialog"
        onCancel={() => setAuthOpen(false)}
      >
        <div className="dialog-heading">
          <h2>Analyst access</h2>
          <button
            aria-label="Close analyst access"
            onClick={() => setAuthOpen(false)}
          >
            <X size={20} />
          </button>
        </div>
        <p>
          Enter a signed analyst session token issued by the backend. This is
          not your OpenAI API key.
        </p>
        <form onSubmit={signIn}>
          <label htmlFor="analyst-token">Analyst session token</label>
          <input
            id="analyst-token"
            type="password"
            autoComplete="off"
            value={token}
            onChange={(e) => setToken(e.target.value)}
            required
          />
          <small>
            The session is held only in memory and expires automatically.
          </small>
          <button className="primary">Start analyst session</button>
        </form>
        {session?.role === "analyst" && (
          <button
            className="secondary"
            onClick={() => {
              setSessionToken("");
              setAuthOpen(false);
              setReviews([]);
              setSaved("");
              void load();
            }}
          >
            Return to read-only demo
          </button>
        )}
      </dialog>
    </div>
  );
}

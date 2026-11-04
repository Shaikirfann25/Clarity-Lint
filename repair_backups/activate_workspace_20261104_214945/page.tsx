"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Activity, AlertCircle, BarChart3, BookOpen, CheckCircle2, ChevronRight,
  ClipboardList, FileText, FlaskConical, Gauge, Home, Menu, Network,
  Play, RefreshCw, ShieldCheck, Sparkles, Upload, X, Zap
} from "lucide-react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

const nav = [
  { id:"Overview", icon:Home },
  { id:"Analyze Text", icon:Sparkles },
  { id:"Document Review", icon:FileText },
  { id:"Evaluation Lab", icon:FlaskConical },
  { id:"Error Analysis", icon:AlertCircle },
  { id:"Integration Status", icon:Network },
  { id:"Viva & Demo", icon:BookOpen },
];

const examples:Record<string,string> = {
  "Attachment ambiguity":"The admin monitors the user with the sensor.",
  "Vague term":"The supplier shall respond soon.",
  "Pronoun/reference":"When the analyst met the manager, they approved the report.",
  "Scope ambiguity":"The system does not notify all users and administrators.",
  "Clear sentence":"The service must return HTTP 200 within 500 milliseconds."
};

function Hero({kicker,title,desc}:any) {
  return <section className="hero">
    <div className="eyebrow">{kicker}</div>
    <h1>{title}</h1><p>{desc}</p>
    <div className="pills"><span className="pill">HUMAN-IN-THE-LOOP NLP</span><span className="pill">IMPERIAL JADE EDITION</span></div>
  </section>;
}
function Metric({label,value,sub}:any) {
  return <div className="metric"><div className="metric-label">{label}</div><div className="metric-value">{value}</div><div className="metric-sub">{sub}</div></div>;
}
function Panel({title,children}:any) {
  return <section className="panel"><h3>{title}</h3>{children}</section>;
}
function ErrorMessage({children}:any) {
  return children ? <div className="error">{String(children)}</div> : null;
}
function DownloadButton({data,filename}:any) {
  const download = () => {
    const blob = new Blob([typeof data === "string" ? data : JSON.stringify(data,null,2)], {type:"application/json"});
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a"); a.href=url; a.download=filename; a.click();
    URL.revokeObjectURL(url);
  };
  return <button className="btn btn-secondary" onClick={download}>↓ Export</button>;
}

export default function Dashboard() {
  const [page,setPage] = useState("Overview");
  const [mobileOpen,setMobileOpen] = useState(false);
  const [health,setHealth] = useState<any>(null);
  const [apiError,setApiError] = useState("");
  const [busy,setBusy] = useState(false);
  const [sentence,setSentence] = useState("");
  const [example,setExample] = useState("Write my own");
  const [analysis,setAnalysis] = useState<any>(null);
  const [docText,setDocText] = useState("");
  const [doc,setDoc] = useState<any>(null);
  const [evaluation,setEvaluation] = useState<any>(null);
  const [evalError,setEvalError] = useState("");
  const [selectedMethod,setSelectedMethod] = useState("rules_pred");
  const [csvName,setCsvName] = useState("");
  const [errorRows,setErrorRows] = useState([
    {id:"EX-001",gold:"attachment",predicted:"no_ambiguity",method:"rules",kind:"False negative",cause:"PP attachment pattern not covered"},
    {id:"EX-002",gold:"no_ambiguity",predicted:"vague",method:"rules",kind:"False positive",cause:"Trigger word treated as sufficient evidence"},
    {id:"EX-003",gold:"pronoun",predicted:"scope",method:"model",kind:"Class confusion",cause:"Small or imbalanced training data"}
  ]);

  const request = async (path:string, options:any={}) => {
    const response = await fetch(`${API}${path}`,options);
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || `Request failed (${response.status})`);
    return data;
  };

  const checkHealth = async () => {
    try {
      const data = await request("/health");
      setHealth(data); setApiError("");
    } catch(e:any) { setHealth(null); setApiError(e.message); }
  };
  useEffect(() => { checkHealth(); }, []);

  const runAnalysis = async () => {
    if (!sentence.trim()) return;
    setBusy(true); setAnalysis(null);
    try {
      const data = await request("/api/analyze",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({text:sentence.trim()})});
      setAnalysis(data.result);
    } catch(e:any) { setApiError(e.message); }
    finally { setBusy(false); }
  };

  const runDocument = async () => {
    if (!docText.trim()) return;
    setBusy(true); setDoc(null);
    try {
      const data = await request("/api/document",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({text:docText.trim()})});
      setDoc(data.result);
    } catch(e:any) { setApiError(e.message); }
    finally { setBusy(false); }
  };

  const loadDemoEvaluation = async () => {
    setBusy(true); setEvalError("");
    try { setEvaluation(await request("/api/evaluation/demo")); }
    catch(e:any) { setEvalError(e.message); }
    finally { setBusy(false); }
  };

  const uploadEvaluation = async (file:File) => {
    setBusy(true); setEvalError(""); setCsvName(file.name);
    try {
      const form = new FormData(); form.append("file",file);
      setEvaluation(await request("/api/evaluate",{method:"POST",body:form}));
    } catch(e:any) { setEvalError(e.message); }
    finally { setBusy(false); }
  };

  const currentReport = evaluation?.reports?.[selectedMethod];
  const flaggedTypes = doc?.type_counts || {};
  const csv = useMemo(() => {
    const headers = ["sentence_id","gold_label","predicted_label","method","error_type","likely_cause"];
    const rows = errorRows.map(r=>[r.id,r.gold,r.predicted,r.method,r.kind,r.cause]);
    return [headers,...rows].map(row=>row.map(x=>`"${String(x).replace(/"/g,'""')}"`).join(",")).join("\n");
  },[errorRows]);

  const renderOverview = () => <>
    <Hero kicker="Clarity intelligence / 01" title="Make meaning unmistakable." desc="A focused NLP workbench for requirements, contracts and policy text. Surface possible ambiguity, compare detection methods, and help writers make intent explicit."/>
    <div className="grid metrics">
      <Metric label="Ambiguity families" value="04" sub="Vague · Attachment · Scope · Reference"/>
      <Metric label="Detection paths" value="03" sub="Rules · Classifier · Prompt baseline"/>
      <Metric label="Review principle" value="Human" sub="Suggestions, never legal verdicts"/>
      <Metric label="Evaluation" value="Honest" sub="Held-out labels required for real metrics"/>
    </div>
    <div className="grid two">
      <Panel title="The pipeline">
        {[
          ["01","Input","Paste a clause or review a text file."],
          ["02","Detect","Run rules and connected model adapters."],
          ["03","Explain","Show evidence spans and competing readings."],
          ["04","Refine","Offer intent-aware rewrites for human approval."],
          ["05","Evaluate","Compare methods on the same frozen test set."]
        ].map(x=><div className="step" key={x[0]}><div className="step-num">{x[0]}</div><div><strong>{x[1]}</strong><div className="muted">{x[2]}</div></div></div>)}
      </Panel>
      <Panel title="Precision over certainty">
        <p>Long or complex text is not automatically ambiguous. Each flag should point to a plausible alternate interpretation.</p>
        <div className="notice">Project-defined ambiguity rate = flagged sentences ÷ total sentences × 100. It is not a validated legal-risk score.</div>
        <p>Start with Analyze Text for a guided demonstration, or use Evaluation Lab to load the team's test predictions.</p>
        <button className="btn" onClick={()=>setPage("Analyze Text")}>Open workbench <ChevronRight size={15}/></button>
      </Panel>
    </div>
  </>;

  const renderAnalysis = () => <>
    <Hero kicker="Sentence workbench / 02" title="Analyze a clause." desc="Inspect a sentence, compare detector signals, and review possible meanings. Demo fallback outputs remain clearly identified."/>
    <div className="grid two">
      <Panel title="Input sentence">
        <label className="field-label">Load an example</label>
        <select value={example} onChange={e=>{setExample(e.target.value);setSentence(examples[e.target.value]||"");setAnalysis(null);}}>
          <option>Write my own</option>{Object.keys(examples).map(x=><option key={x}>{x}</option>)}
        </select>
        <label className="field-label">Sentence or short clause</label>
        <textarea value={sentence} onChange={e=>setSentence(e.target.value)} placeholder="Paste a requirement, contract clause or policy sentence..."/>
        <div className="row" style={{marginTop:12}}>
          <button className="btn" disabled={busy||!sentence.trim()} onClick={runAnalysis}><Play size={14}/>{busy?"Analyzing...":"Analyze sentence"}</button>
          {analysis && <DownloadButton data={analysis} filename="clarity_lint_analysis.json"/>}
        </div>
        <p className="muted">Analysis is sent to your local Python API. Avoid entering confidential documents unless you are authorised to process them.</p>
        <ErrorMessage>{apiError}</ErrorMessage>
      </Panel>
      <Panel title="Detection result">
        {!analysis ? <p className="muted">Your analysis findings will appear here.</p> : <>
          <div className="spread"><span className="tag">{analysis.mode==="demo_fallback"?"DEMO FALLBACK":analysis.mode}</span><span className="muted">{Number(analysis.latency_ms||0).toFixed(2)} ms</span></div>
          {analysis.detections?.length ? analysis.detections.map((d:any,i:number)=><div className="result-card" key={i}>
            <span className="tag">{d.label?.toUpperCase()}</span>
            <p><strong>Evidence:</strong> {d.span||"Not provided"}</p>
            <p>{d.reason}</p><div className="muted">Source: {d.source||"unknown"} · Confidence: {d.confidence??"not provided"}</div>
          </div>) : <div className="notice">No configured detector flagged this sentence. This does not prove that it is unambiguous.</div>}
          <h3 style={{marginTop:18}}>Explanation</h3><p>{analysis.explanation}</p>
          {analysis.readings?.length>0 && <><h3>Possible readings</h3>{analysis.readings.map((x:string,i:number)=><p key={i}>{i+1}. {x}</p>)}</>}
          {analysis.rewrites?.length>0 && <><h3>Candidate rewrites</h3>{analysis.rewrites.map((x:string,i:number)=><div className="result-card" key={i}>{x}</div>)}<p className="muted">Choose a rewrite only if it preserves the intended meaning.</p></>}
        </>}
      </Panel>
    </div>
  </>;

  const renderDocument = () => <>
    <Hero kicker="Document review / 03" title="Read the whole document." desc="Review UTF-8 plain text or pasted content sentence by sentence, with a summary of flagged findings."/>
    <Panel title="Document input">
      <label className="field-label">Paste document text</label>
      <textarea style={{minHeight:180}} value={docText} onChange={e=>setDocText(e.target.value)} placeholder="Paste policy, requirement or contract text here..."/>
      <div className="row" style={{marginTop:12}}><button className="btn" disabled={busy||!docText.trim()} onClick={runDocument}><FileText size={14}/>{busy?"Reviewing...":"Review document"}</button></div>
      <p className="muted">This version accepts pasted text. File upload support can be added after confirming the required document parsers.</p>
      <ErrorMessage>{apiError}</ErrorMessage>
    </Panel>
    {doc && <>
      <div className="grid metrics" style={{marginTop:15}}>
        <Metric label="Sentences" value={doc.sentence_count} sub="Extracted by sentence splitter"/>
        <Metric label="Flagged" value={doc.flagged_count} sub="At least one detection"/>
        <Metric label="Ambiguity rate" value={`${Number(doc.ambiguity_rate).toFixed(1)}%`} sub="Project-defined; not legal risk"/>
        <Metric label="Analysis time" value={`${Number(doc.latency_ms).toFixed(1)} ms`} sub="Local call measurement"/>
      </div>
      <div className="grid two">
        <Panel title="Type breakdown">
          {Object.entries(flaggedTypes).map(([name,value]:any)=><div key={name} style={{margin:"13px 0"}}>
            <div className="spread"><span>{name}</span><strong>{value}</strong></div>
            <div className="bar-bg"><div className="bar-fill" style={{width:`${doc.sentence_count?value/doc.sentence_count*100:0}%`}}/></div>
          </div>)}
        </Panel>
        <Panel title="Sentence review">
          {doc.sentences?.map((s:any,i:number)=><div className="result-card" key={i}>
            <div className="spread"><span className="muted">Sentence {i+1}</span><span className={`tag ${s.detections?.length?"red":"green"}`}>{s.detections?.length?"FLAGGED":"NO FLAG"}</span></div>
            <p>{s.text}</p><div className="muted">{s.detections?.map((d:any)=>d.label).join(", ")||"No demo pattern flagged"}</div>
            {s.explanation && <p>{s.explanation}</p>}
          </div>)}
          <DownloadButton data={doc} filename="clarity_lint_document_report.json"/>
        </Panel>
      </div>
    </>}
  </>;

  const renderEvaluation = () => <>
    <Hero kicker="Evaluation lab / 04" title="Measure what matters." desc="Compare detection methods on identical gold-labelled examples. Upload a CSV to calculate metrics from your own evaluation set."/>
    <div className="notice"><strong>Integrity note:</strong> Synthetic fixtures are for testing visualizations only. Do not report their metrics as project performance.</div>
    <Panel title="Load evaluation data">
      <div className="row">
        <label className="btn btn-secondary"><Upload size={14}/> Choose evaluation CSV
          <input type="file" accept=".csv,text/csv" style={{display:"none"}} onChange={e=>{const f=e.target.files?.[0];if(f)uploadEvaluation(f);}}/>
        </label>
        <button className="btn" onClick={loadDemoEvaluation} disabled={busy}><RefreshCw size={14}/> Load demo fixture</button>
        {csvName && <span className="muted">{csvName}</span>}
      </div>
      <p className="muted">Required column: gold_label. Optional prediction columns: rules_pred, model_pred, prompt_pred. Labels: no_ambiguity, vague, attachment, scope, pronoun.</p>
      <ErrorMessage>{evalError}</ErrorMessage>
    </Panel>
    {evaluation && <>
      <div className="notice">{evaluation.synthetic?"DEMO FIXTURE — synthetic examples, not measured results.":"REAL UPLOADED DATA — metrics calculated from the uploaded CSV. Verify its provenance and frozen test split before reporting."} {evaluation.examples??""} examples.</div>
      <div className="grid three">
        {Object.entries(evaluation.reports||{}).map(([method,r]:any)=><div className="panel" key={method}>
          <div className="micro">{method.replaceAll("_"," ")}</div>
          <div className="metric-value">{(r.macro_f1*100).toFixed(1)}%</div>
          <div className="metric-sub">Macro-F1</div>
          <div className="kv"><span>Accuracy</span><strong>{(r.accuracy*100).toFixed(1)}%</strong></div>
          <div className="kv"><span>Examples</span><strong>{r.n_examples}</strong></div>
        </div>)}
      </div>
      <Panel title="Confusion matrix">
        <label className="field-label">Select method</label>
        <select value={selectedMethod} onChange={e=>setSelectedMethod(e.target.value)}>
          {Object.keys(evaluation.reports||{}).map(x=><option key={x}>{x}</option>)}
        </select>
        {currentReport?.confusion_matrix && <div className="table-wrap" style={{marginTop:12}}>
          <table><thead><tr><th>Gold \ Predicted</th>{["No ambiguity","Vague","Attachment","Scope","Pronoun"].map(x=><th key={x}>{x}</th>)}</tr></thead>
            <tbody>{currentReport.confusion_matrix.map((row:number[],i:number)=><tr key={i}><th>{["No ambiguity","Vague","Attachment","Scope","Pronoun"][i]}</th>{row.map((v,j)=><td key={j}>{v}</td>)}</tr>)}</tbody>
          </table>
        </div>}
      </Panel>
    </>}
    <Panel title="Final evaluation checklist">
      {["Freeze and document test split IDs.","Use identical test sentence IDs for every method.","Report per-class precision, recall and F1.","Include confusion matrices and representative errors.","Measure latency on a named machine and environment.","Do not tune thresholds on the test set."].map(x=><label key={x} className="field-label"><input type="checkbox" style={{width:"auto",marginRight:9}}/>{x}</label>)}
    </Panel>
  </>;

  const renderErrors = () => <>
    <Hero kicker="Failure review / 05" title="Inspect the misses." desc="Record false positives, false negatives and class confusions from actual evaluation results. The initial rows below are examples, not observed project errors."/>
    <div className="notice">Template rows are illustrative. Replace them with actual observed failures before submission.</div>
    <Panel title="Error analysis log">
      <div className="table-wrap"><table><thead><tr><th>ID</th><th>Gold</th><th>Predicted</th><th>Method</th><th>Error type</th><th>Likely cause</th></tr></thead>
        <tbody>{errorRows.map((r,i)=><tr key={r.id}><td>{r.id}</td><td>{r.gold}</td><td>{r.predicted}</td><td>{r.method}</td><td>{r.kind}</td><td>{r.cause}</td></tr>)}</tbody>
      </table></div>
      <button className="btn" style={{marginTop:14}} onClick={()=>{const blob=new Blob([csv],{type:"text/csv"});const url=URL.createObjectURL(blob);const a=document.createElement("a");a.href=url;a.download="clarity_lint_error_analysis.csv";a.click();URL.revokeObjectURL(url);}}>↓ Export error log CSV</button>
    </Panel>
    <Panel title="What to inspect">
      <p><strong>False negative:</strong> A real ambiguity was missed. Check whether the pattern or model has sufficient context.</p>
      <p><strong>False positive:</strong> A clear sentence was flagged. Check whether a trigger word was treated as enough evidence.</p>
      <p><strong>Class confusion:</strong> A finding was assigned to the wrong ambiguity family. Inspect label definitions and similar examples.</p>
    </Panel>
  </>;

  const renderIntegration = () => <>
    <Hero kicker="Integration console / 06" title="One contract. Three methods." desc="A shared API schema keeps the dashboard independent from the rules, model and explanation implementations."/>
    <Panel title="Live API status">
      <div className="spread"><span>Python API · localhost:8000</span><span className={`tag ${health?"green":"red"}`}>{health?"CONNECTED":"NOT CONNECTED"}</span></div>
      <p className="muted">{health?`Service: ${health.service} · ${health.integration}`:apiError||"Checking API..."}</p>
      <button className="btn btn-secondary" onClick={checkHealth}><RefreshCw size={14}/> Check again</button>
    </Panel>
    <Panel title="Shared label contract"><div className="row">{["no_ambiguity","vague","attachment","scope","pronoun"].map(x=><span className="tag" key={x}>{x}</span>)}</div></Panel>
    <Panel title="Canonical detection record">
      <pre style={{whiteSpace:"pre-wrap",color:"#c8d5c9",fontSize:11,lineHeight:1.7}}>{JSON.stringify({sentence_id:"S001",text:"The admin monitors the user with the sensor.",predictions:[{source:"rules",label:"attachment",span:"with the sensor",confidence:null,reason:"The phrase may attach in more than one way."}],readings:["The admin uses a sensor to monitor the user.","The user has a sensor associated with them."],rewrites:["The admin uses the sensor to monitor the user."]},null,2)}</pre>
    </Panel>
    <div className="grid three">
      <Panel title="Person 2 · Rules"><span className="tag">OPTIONAL ADAPTER</span><p>src/rules/detect.py</p><p>Pipeline tries the team rules module; demo fallback is used if unavailable.</p></Panel>
      <Panel title="Person 3 · Model"><span className="tag">OPTIONAL ADAPTER</span><p>src/model/predict.py</p><p>Model predictions are separate from rule detections. Verify checkpoint availability.</p></Panel>
      <Panel title="Person 4 · Explanations"><span className="tag">OPTIONAL ADAPTER</span><p>src/explanations/explain.py</p><p>Explanation and rewrite outputs may use safe demo templates.</p></Panel>
    </div>
    <div className="notice">A connected API does not mean every teammate's module is connected. Confirm module imports and model checkpoint status before describing the complete pipeline as integrated.</div>
  </>;

  const renderViva = () => <>
    <Hero kicker="Presentation suite / 07" title="Explain the engineering." desc="A concise demo sequence and viva notes for the dashboard, integration and evaluation contribution."/>
    <Panel title="Suggested four-minute demo">
      {[
        ["0:00–0:30","Introduce the problem","Clarity Lint flags possible ambiguity in requirements, contracts and policies."],
        ["0:30–1:15","Analyze one sentence","Use “The admin monitors the user with the sensor.” Show competing readings."],
        ["1:15–2:00","Review a document","Show sentence counts, type breakdown and project-defined ambiguity rate."],
        ["2:00–3:00","Compare methods","Explain rules vs classifier vs prompt baseline on the same held-out test set."],
        ["3:00–4:00","Discuss limitations","Show real false positives and false negatives; explain human review."]
      ].map(x=><div className="step" key={x[0]}><span className="tag">{x[0]}</span><div><strong>{x[1]}</strong><p>{x[2]}</p></div></div>)}
    </Panel>
    <Panel title="Viva answer · Person 5">
      <p>“I developed the dashboard and integration layer for Clarity Lint. I connected the frontend to a Python API that exposes sentence analysis, document review, and evaluation functions through a consistent interface. I designed the evaluation workflow to calculate accuracy, macro-F1, per-class metrics and confusion matrices from supplied labelled data. I also separated synthetic demo fixtures from measured results so illustrative values are not reported as actual model performance. The dashboard presents findings as suggestions for human review.”</p>
    </Panel>
    <Panel title="Questions to prepare">
      {[
        ["Why separate UI and NLP logic?","It keeps the frontend independent of the detection implementation and makes modules easier to test."],
        ["What is ambiguity rate?","Flagged sentences divided by total sentences, multiplied by 100. It is descriptive, not a legal-risk score."],
        ["Why compare on the same test set?","It ensures method comparisons use the same examples and gold labels."],
        ["What if rules and model disagree?","Show the disagreement as a review signal rather than silently choosing one output."],
        ["Are the demo metrics real?","No. The demo fixture is synthetic. Real performance must be calculated from a verified labelled evaluation dataset."]
      ].map(x=><details key={x[0]} style={{padding:"12px 0",borderBottom:"1px solid var(--line)"}}><summary style={{cursor:"pointer",color:"var(--gold2)"}}>{x[0]}</summary><p>{x[1]}</p></details>)}
    </Panel>
  </>;

  const views:any = {
    "Overview":renderOverview,
    "Analyze Text":renderAnalysis,
    "Document Review":renderDocument,
    "Evaluation Lab":renderEvaluation,
    "Error Analysis":renderErrors,
    "Integration Status":renderIntegration,
    "Viva & Demo":renderViva
  };

  return <div className="app-shell">
    <aside className={`sidebar ${mobileOpen?"mobile-open":""}`}>
      <div className="spread"><div><div className="brand">◈ CLARITY LINT</div><div className="brand-mark">IMPERIAL JADE / PERSON 05</div></div><button className="mobile-menu" onClick={()=>setMobileOpen(false)}><X size={18}/></button></div>
      <div className="nav-label">Workspace</div>
      {nav.map(({id,icon:Icon})=><button key={id} className={`nav-item ${page===id?"active":""}`} onClick={()=>{setPage(id);setMobileOpen(false);}}><Icon size={16}/>{id}</button>)}
      <div className="sidebar-foot"><div className="micro">System status</div><p className="muted">{health?"API connected":"API unavailable"}</p><span className="tag">HUMAN REVIEW REQUIRED</span></div>
    </aside>
    <main className="main">
      <div className="topbar">
        <div className="row"><button className="btn btn-secondary mobile-menu" onClick={()=>setMobileOpen(true)}><Menu size={16}/></button><span className="micro">CLARITY LINT / WORKSPACE</span></div>
        <div className="status"><span className="dot" style={{background:health?"var(--green)":"var(--red)"}}/>{health?"Python API online":"API offline"}<button className="btn btn-secondary" style={{padding:"6px 9px"}} onClick={checkHealth}><RefreshCw size={12}/></button></div>
      </div>
      {views[page]()}
      <div className="footer">CLARITY LINT · IMPERIAL JADE · PERSON 05 · REVIEW BEFORE RELYING</div>
    </main>
  </div>;
}

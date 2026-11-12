'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import { Activity, ArrowDownToLine, CheckCircle2, ClipboardCheck, FileText, History, MessageSquareText, RefreshCw, Search, Sparkles, Trash2 } from 'lucide-react';
import { SectionHeader, Panel, Tag, Button, EmptyState } from '@/components/ui';
import { analyzeText, type Analysis } from '@/lib/api';
import { Toast } from '@/components/toast';
import { useToast } from '@/hooks/use-toast';

type SavedRecord = { id: string; kind: 'text' | 'document'; createdAt: string; input: string; result: Analysis | any };
type Note = { id: string; recordId: string; findingIndex: number; status: 'pending' | 'accepted' | 'dismissed'; comment: string };
const HISTORY_KEY = 'clarity-analysis-history-v1';
const NOTES_KEY = 'clarity-review-notes-v1';
const read = <T,>(key: string, fallback: T): T => { try { if (typeof window === 'undefined') return fallback; const value = localStorage.getItem(key); return value ? JSON.parse(value) as T : fallback; } catch { return fallback; } };
const write = (key: string, value: unknown) => { try { localStorage.setItem(key, JSON.stringify(value)); } catch { /* storage may be unavailable */ } };
const asSentences = (r: SavedRecord): Analysis[] => r.kind === 'text' ? [r.result as Analysis] : (r.result?.sentences || []);
const labelName = (s: string) => s.replaceAll('_', ' ').replace(/\b\w/g, c => c.toUpperCase());

export function WorkspaceFeature({ title, description, category, featureId }: { title: string; description: string; category: string; featureId: string }) {
  const [records, setRecords] = useState<SavedRecord[]>([]);
  const [notes, setNotes] = useState<Note[]>([]);
  const [query, setQuery] = useState('');
  const [selected, setSelected] = useState('');
  const [draft, setDraft] = useState('');
  const [busy, setBusy] = useState(false);
  const [comparison, setComparison] = useState<{ before: string; after: string; result: Analysis | null } | null>(null);
  const { message, kind, show, clear } = useToast();

  const refresh = useCallback(() => { setRecords(read<SavedRecord[]>(HISTORY_KEY, [])); setNotes(read<Note[]>(NOTES_KEY, [])); }, []);
  useEffect(() => {
    refresh();
    const onStorage = () => refresh();

    window.addEventListener("storage", onStorage);
    window.addEventListener("clarity-history-updated", onStorage);

    return () => {
      window.removeEventListener("storage", onStorage);
      window.removeEventListener("clarity-history-updated", onStorage);
    };
  }, [refresh]);
  const current = records.find(r => r.id === selected) || records[0];
  const allSentences = useMemo(() => records.flatMap(r => asSentences(r).map(s => ({ record: r, sentence: s }))), [records]);
  const allFindings = useMemo(() => allSentences.flatMap(({ record, sentence }) => (sentence.detections || []).map((finding: any, index: number) => ({ record, sentence, finding, index }))), [allSentences]);
  const filtered = records.filter(r => `${r.input} ${r.createdAt}`.toLowerCase().includes(query.toLowerCase()));
  const exportJson = (data: unknown, filename: string) => { const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' }); const url = URL.createObjectURL(blob); const a = document.createElement('a'); a.href = url; a.download = filename; a.click(); URL.revokeObjectURL(url); };
  const exportCsv = () => { const rows = [['record_id','created_at','sentence','label','span','source','confidence','reason'], ...allFindings.map(({record,sentence,finding}) => [record.id,record.createdAt, sentence.text, finding.label, finding.span || '', finding.source || '', finding.confidence ?? '', finding.reason || ''])]; const csv = rows.map(row => row.map(v => `"${String(v).replaceAll('"','""')}"`).join(',')).join('\r\n'); const url = URL.createObjectURL(new Blob([csv], {type:'text/csv;charset=utf-8'})); const a=document.createElement('a'); a.href=url; a.download='clarity-lint-findings.csv'; a.click(); URL.revokeObjectURL(url); };
  const saveNote = (recordId: string, findingIndex: number, status: Note['status'], comment = '') => { const id = `${recordId}:${findingIndex}`; const next = [...notes.filter(n => n.id !== id), { id, recordId, findingIndex, status, comment }]; setNotes(next); write(NOTES_KEY, next); show('Review decision saved in this browser.','success'); };
  const runComparison = async () => { if (!draft.trim()) { show('Enter the revised sentence first.','error'); return; } if (!current) { show('Run a text analysis first so there is an original sentence to compare.','info'); return; } const before = asSentences(current)[0]?.text || current.input; setBusy(true); try { const result = await analyzeText(draft.trim()); setComparison({ before, after: draft.trim(), result }); show('Revised text analysed successfully.','success'); } catch (e:any) { show(e.message || 'Comparison failed.','error'); } finally { setBusy(false); } };
  const clearHistory = () => { if (!window.confirm('Delete all saved analysis history from this browser?')) return; write(HISTORY_KEY, []); setRecords([]); setSelected(''); show('Local analysis history cleared.','success'); };

  const header = <SectionHeader eyebrow={category} title={title} description={description} actions={<Tag tone="info">Uses saved project results</Tag>} />;
  const recordPicker = <label className="field-label">Analysis record<select value={current?.id || ''} onChange={e=>setSelected(e.target.value)}>{records.map(r=><option key={r.id} value={r.id}>{new Date(r.createdAt).toLocaleString()} · {r.kind} · {r.input.slice(0,55)}</option>)}</select></label>;
  const noData = <Panel><EmptyState icon={History} title="No saved analyses yet" description="Run Analyze Text or Document Review first. Successful results are saved in this browser and appear here automatically." /></Panel>;

  let body: React.ReactNode;
  if (featureId === 'history') {
    body = <><Panel title="Saved analysis history" subtitle="Stored locally in this browser; it is not uploaded to a server"><div className="toolbar-row"><label className="search-field"><Search size={16}/><input value={query} onChange={e=>setQuery(e.target.value)} placeholder="Search text or date" /></label><Button variant="secondary" onClick={refresh}><RefreshCw size={15}/> Refresh</Button><Button variant="danger" onClick={clearHistory}><Trash2 size={15}/> Clear history</Button></div>{filtered.length ? <div className="history-list">{filtered.map(r=><button className={`history-item ${current?.id===r.id?'selected':''}`} key={r.id} onClick={()=>setSelected(r.id)}><span><b>{r.kind==='text'?'Text analysis':'Document review'}</b><small>{new Date(r.createdAt).toLocaleString()}</small></span><span className="history-preview">{r.input}</span><Tag tone="neutral">{asSentences(r).length} sentence(s)</Tag></button>)}</div> : <p className="muted">No matching records.</p>}</Panel>{current&&<Panel title="Selected record" subtitle={new Date(current.createdAt).toLocaleString()}><p>{current.input}</p><div className="stat-pair"><div><b>{asSentences(current).length}</b><span>Sentences</span></div><div><b>{asSentences(current).reduce((n,s)=>n+(s.detections?.length||0),0)}</b><span>Findings</span></div></div><Button onClick={()=>exportJson(current,'clarity-analysis.json')}><ArrowDownToLine size={15}/> Export record</Button></Panel>}</>;
  } else if (featureId === 'comparison') {
    body = records.length ? (
      <>
        {recordPicker}
        <Panel title="Before & after" subtitle="Compare an original saved sentence with a newly analysed revision">
          {current ? (
            <div className="comparison-grid">
              <div>
                <Tag>ORIGINAL</Tag>
                <p>{asSentences(current)[0]?.text || current.input}</p>
              </div>
              <div>
                <Tag tone="success">REVISED</Tag>
                <textarea value={draft} onChange={e => setDraft(e.target.value)} placeholder="Enter your revised sentence..." rows={4} />
                <Button onClick={runComparison} disabled={busy}>
                  {busy ? <span className="spin">◌</span> : <Sparkles size={15} />}
                  <span>Analyse revision</span>
                </Button>
              </div>
            </div>
          ) : null}
          {comparison ? (
            <div className="comparison-result">
              <b>Revised analysis</b>
              <p>{comparison.result?.explanation}</p>
              <Tag tone={comparison.result?.detections?.length ? 'warning' : 'success'}>
                {comparison.result?.detections?.length || 0} finding(s)
              </Tag>
            </div>
          ) : null}
        </Panel>
      </>
    ) : noData;
  } else if (featureId === 'annotation' || featureId === 'review') {
    body = allFindings.length ? <><Panel title={featureId==='annotation'?'Finding annotation studio':'Human review queue'} subtitle="Accept, dismiss or leave a finding pending. Decisions are saved locally.">{recordPicker}{allFindings.filter(x=>!current||x.record.id===current.id).map(({record,sentence,finding,index})=>{const note=notes.find(n=>n.id===`${record.id}:${index}`);return <div className="review-finding" key={`${record.id}:${index}`}><div className="review-finding-head"><Tag tone="warning">{labelName(finding.label)}</Tag><Tag tone={note?.status==='accepted'?'success':note?.status==='dismissed'?'neutral':'info'}>{note?.status||'pending'}</Tag></div><p>{sentence.text}</p><small>Evidence: {finding.span||'Not provided'} · {finding.source||'Unknown source'}</small><textarea defaultValue={note?.comment||''} placeholder="Reviewer note (optional)" rows={2} onBlur={e=>{if(e.target.value!== (note?.comment||'')) saveNote(record.id,index,note?.status||'pending',e.target.value)}}/><div className="button-row"><Button onClick={()=>saveNote(record.id,index,'accepted',note?.comment||'')}>Accept</Button><Button variant="secondary" onClick={()=>saveNote(record.id,index,'dismissed',note?.comment||'')}>Dismiss</Button><Button variant="ghost" onClick={()=>saveNote(record.id,index,'pending',note?.comment||'')}>Reset</Button></div></div>})}</Panel><Panel title="Review progress"><div className="stat-pair"><div><b>{notes.filter(n=>n.status==='accepted').length}</b><span>Accepted</span></div><div><b>{notes.filter(n=>n.status==='dismissed').length}</b><span>Dismissed</span></div><div><b>{Math.max(0,allFindings.length-notes.filter(n=>n.status!=='pending').length)}</b><span>Pending</span></div></div></Panel></> : noData;
  } else if (featureId === 'ai-detection' || featureId === 'explanations') {
    body = allSentences.length ? <><Panel title={featureId==='ai-detection'?'Detection output':'Explanation and rewrite output'} subtitle="Actual outputs returned by the connected project pipeline">{recordPicker}{(current?asSentences(current):[]).map((s,i)=><div className="output-card" key={i}><b>{s.text}</b><p>{featureId==='ai-detection'?`${s.detections?.length||0} finding(s) returned` : s.explanation}</p>{featureId==='ai-detection'?(s.detections||[]).map((d:any,j:number)=><div className="finding-line" key={j}><Tag tone="warning">{labelName(d.label)}</Tag><span>{d.span||'No span'}</span><small>{d.reason}</small></div>):<><h4>Alternative readings</h4><ul>{(s.readings||[]).map((v:string,j:number)=><li key={j}>{v}</li>)}</ul><h4>Suggested rewrites</h4><ul>{(s.rewrites||[]).map((v:string,j:number)=><li key={j}>{v}</li>)}</ul></>}</div>)}</Panel></> : noData;
  } else if (featureId === 'model-comparison') {
    body = allSentences.length ? <Panel title="Model output availability" subtitle="Only predictions actually returned by the API are shown">{allSentences.map(({record,sentence},i)=><div className="output-card" key={`${record.id}:${i}`}><b>{sentence.text}</b>{(sentence.model_predictions||[]).length ? (sentence.model_predictions ?? []).map((p:any,j:number)=><p key={j}>{labelName(p.label)} · {typeof p.confidence==='number'?(p.confidence*100).toFixed(1)+'%':'confidence not provided'}</p>) : <p className="muted">No valid model prediction was returned for this sentence. A model comparison cannot be calculated from this record.</p>}</div>)}</Panel> : noData;
  } else if (featureId === 'analytics' || featureId === 'quality') {
    const flagged = allSentences.filter(s=>s.sentence.detections?.length).length; const rate = allSentences.length ? flagged/allSentences.length*100 : 0; const counts = allFindings.reduce((a,x)=>{a[x.finding.label]=(a[x.finding.label]||0)+1;return a;},{} as Record<string,number>);
    body = records.length ? <><div className="metric-grid"><Panel title="Analysed sentences"><strong className="big-number">{allSentences.length}</strong></Panel><Panel title="Flagged sentences"><strong className="big-number">{flagged}</strong></Panel><Panel title="Observed flag rate"><strong className="big-number">{rate.toFixed(1)}%</strong></Panel><Panel title="Total findings"><strong className="big-number">{allFindings.length}</strong></Panel></div><Panel title={featureId==='analytics'?'Finding distribution':'Evidence-based quality indicators'} subtitle="Calculated from saved analysis records only"><div className="distribution-list">{Object.entries(counts).length?Object.entries(counts).map(([label,n])=><div key={label}><span>{labelName(label)}</span><b>{n}</b></div>):<p>No findings have been returned yet.</p>}</div><p className="muted">These are descriptive counts from this browser's saved records, not validated quality scores or population-level statistics.</p></Panel></> : noData;
  } else if (featureId === 'reports') {
    body = records.length ? <Panel title="Export project results" subtitle="Download the records and findings currently saved in this browser"><div className="export-actions"><Button onClick={()=>exportJson({records,reviewNotes:notes},'clarity-lint-report.json')}><ArrowDownToLine size={16}/> Export JSON report</Button><Button variant="secondary" onClick={exportCsv}><ArrowDownToLine size={16}/> Export findings CSV</Button></div><p className="muted">{records.length} saved records · {allSentences.length} sentences · {allFindings.length} findings. Export files contain the available project output and local reviewer notes.</p></Panel> : noData;
  } else {
    body = <Panel title="Workspace data" subtitle="This workspace is connected to the available analysis records."><p>{records.length} saved records are available. Run an analysis to populate this workspace.</p><Button onClick={refresh}><RefreshCw size={15}/> Refresh records</Button></Panel>;
  }

  return <div className="page-stack">{header}{body}<Toast message={message} kind={kind} onClose={clear}/></div>;
}




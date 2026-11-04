'use client';
import {useEffect,useState} from 'react';
import type {LucideIcon} from 'lucide-react';
import {Activity,AlignLeft,BookOpen,ChevronDown,FileSearch,FlaskConical,LayoutDashboard,Menu,Moon,Network,PanelLeftClose,PanelLeftOpen,Search,Settings2,Sun} from 'lucide-react';
import {WorkspaceProvider,useWorkspace} from './workspace-provider';import {Tag} from './ui';
const nav: {group:string;items:[string,string,LucideIcon][]}[]=[{group:'Workspace',items:[['overview','Overview',LayoutDashboard],['analyze','Analyze text',AlignLeft],['documents','Document review',FileSearch]]},{group:'Quality',items:[['evaluation','Evaluation lab',FlaskConical],['errors','Error analysis',Activity]]},{group:'Project',items:[['integrations','Integration centre',Network],['viva','Viva & demo',BookOpen]]}];
function ShellInner({children}:{children:React.ReactNode}){/* CLARITY_3D_POINTER_EFFECT */
useEffect(()=>{
 const root=document.documentElement;
 const finePointer=window.matchMedia('(pointer:fine)').matches;
 if(!finePointer)return;
 let current:HTMLElement|null=null;
 const move=(event:PointerEvent)=>{
  root.style.setProperty('--cursor-x',`${event.clientX}px`);
  root.style.setProperty('--cursor-y',`${event.clientY}px`);
  const target=event.target as HTMLElement|null;
  const card=target?.closest('.panel,.metric-card,.hero-panel,.task-row,.nav-item,.button,.icon-button') as HTMLElement|null;
  if(current!==card){
   current?.style.removeProperty('--tilt-x');
   current?.style.removeProperty('--tilt-y');
   current?.style.removeProperty('--shine-x');
   current?.style.removeProperty('--shine-y');
   current=card;
  }
  if(card){
   const rect=card.getBoundingClientRect();
   const x=(event.clientX-rect.left)/rect.width;
   const y=(event.clientY-rect.top)/rect.height;
   card.style.setProperty('--tilt-x',`${(0.5-y)*7}deg`);
   card.style.setProperty('--tilt-y',`${(x-0.5)*8}deg`);
   card.style.setProperty('--shine-x',`${x*100}%`);
   card.style.setProperty('--shine-y',`${y*100}%`);
  }
 };
 const leave=()=>{
  current?.style.removeProperty('--tilt-x');
  current?.style.removeProperty('--tilt-y');
  current=null;
 };
 window.addEventListener('pointermove',move,{passive:true});
 window.addEventListener('blur',leave);
 return ()=>{
  window.removeEventListener('pointermove',move);
  window.removeEventListener('blur',leave);
  leave();
 };
},[]);const {active,setActive,compact,setCompact,theme,setTheme}=useWorkspace();const [mobile,setMobile]=useState(false);const [command,setCommand]=useState(false);const [query,setQuery]=useState('');const [clock,setClock]=useState('');useEffect(()=>{const update=()=>setClock(new Intl.DateTimeFormat('en-IN',{hour:'2-digit',minute:'2-digit'}).format(new Date()));update();const id=setInterval(update,30000);return()=>clearInterval(id)},[]);useEffect(()=>{const fn=(e:KeyboardEvent)=>{if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='k'){e.preventDefault();setCommand(v=>!v)}if(e.key==='Escape'){setCommand(false);setMobile(false)}};window.addEventListener('keydown',fn);return()=>window.removeEventListener('keydown',fn)},[]);const all=nav.flatMap(g=>g.items.map(([id,label,Icon])=>({id,label,Icon}))).concat([{id:'settings',label:'Settings',Icon:Settings2}]);const filtered=all.filter(x=>x.label.toLowerCase().includes(query.toLowerCase()));const choose=(id:string)=>{setActive(id);setMobile(false);setCommand(false);setQuery('')};return <div className="app-frame"><aside className={`sidebar ${compact?'sidebar-compact':''} ${mobile?'sidebar-mobile-open':''}`}><div className="brand"><div className="brand-mark">â—‡</div><div><div className="brand-name">CLARITY LINT</div><div className="brand-sub">IMPERIAL JADE / PERSON 05</div></div></div><div className="workspace-switch"><span className="workspace-dot"/>Personal workspace<ChevronDown size={14}/></div><div className="nav-scroll">{nav.map(g=><div className="nav-group" key={g.group}><div className="nav-label">{g.group}</div>{g.items.map(([id,label,Icon])=><button key={id} className={`nav-item ${active===id?'active':''}`} onClick={()=>choose(id)} title={label}><Icon size={17}/><span>{label}</span>{active===id&&<span className="nav-active-dot"/>}</button>)}</div>)}<div className="nav-group"><div className="nav-label">Preferences</div><button className={`nav-item ${active==='settings'?'active':''}`} onClick={()=>choose('settings')}><Settings2 size={17}/><span>Settings</span></button></div></div><div className="sidebar-bottom"><div className="api-mini"><span className="pulse-dot"/><div><b>Python API</b><small>Connection monitored</small></div><Tag tone="success">Online</Tag></div><button className="collapse-button" onClick={()=>setCompact(!compact)}>{compact?<PanelLeftOpen size={16}/>:<PanelLeftClose size={16}/>}<span>Collapse sidebar</span></button></div></aside><main className="main-area"><header className="topbar"><div className="topbar-left"><button className="mobile-menu" onClick={()=>setMobile(!mobile)}><Menu size={19}/></button><div className="breadcrumb"><span>CLARITY LINT</span><span className="crumb-slash">/</span><b>{all.find(x=>x.id===active)?.label.toUpperCase()||'OVERVIEW'}</b></div></div><div className="topbar-actions"><div className="system-pill"><span className="pulse-dot"/><span>Python API online</span></div><span className="top-clock">{clock}</span><button className="icon-button" onClick={()=>setCommand(true)} title="Search workspace (Ctrl K)"><Search size={17}/></button><button className="icon-button" onClick={()=>setTheme(theme==='dark'?'light':'dark')} title="Toggle theme">{theme==='dark'?<Sun size={17}/>:<Moon size={17}/>}</button><div className="avatar">CK</div></div></header><div className="page-content">{children}</div><footer className="app-footer"><span>CLARITY LINT Â· IMPERIAL JADE EDITION</span><span>HUMAN REVIEW ALWAYS REQUIRED</span><span>BUILD 02.06</span></footer></main>{command&&<div className="modal-scrim" onMouseDown={()=>setCommand(false)}><div className="command-modal" onMouseDown={e=>e.stopPropagation()}><div className="command-search"><Search size={18}/><input autoFocus value={query} onChange={e=>setQuery(e.target.value)} placeholder="Jump to a workspace..."/><kbd>ESC</kbd></div><div className="command-list">{filtered.map(x=><button key={x.id} onClick={()=>choose(x.id)}><x.Icon size={17}/><span>{x.label}</span><span className="command-enter">â†µ</span></button>)}{!filtered.length&&<div className="command-empty">No matching workspace found.</div>}</div><div className="command-foot">Navigate quickly Â· <kbd>CTRL</kbd> + <kbd>K</kbd></div></div></div>}</div>}
export function AppShell({children}:{children:React.ReactNode}){return <WorkspaceProvider><ShellInner>{children}</ShellInner></WorkspaceProvider>}



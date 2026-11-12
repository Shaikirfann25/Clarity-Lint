'use client';

import { useEffect, useState } from 'react';
import type { LucideIcon } from 'lucide-react';
import {
  Activity, AlignLeft, BookOpen, ChevronDown, FileSearch,
  FlaskConical, LayoutDashboard, Menu, Moon, Network,
  PanelLeftClose, PanelLeftOpen, Search, Settings2, Sun,
  History, GitCompareArrows, Highlighter, Brain, WandSparkles,
  ChartNoAxesCombined, ShieldCheck, FileBarChart, Users,
  ScanText, ClipboardCheck, FileOutput, X
} from 'lucide-react';

import { WorkspaceProvider, useWorkspace } from './workspace-provider';
import { Tag } from './ui';

type NavItem = [string, string, LucideIcon];

const nav: { group: string; items: NavItem[] }[] = [
  {
    group: 'WORKSPACE',
    items: [
      ['overview', 'Overview', LayoutDashboard],
      ['analyze', 'Analyze Text', AlignLeft],
      ['documents', 'Document Review', FileSearch],
      ['history', 'Analysis History', History],
      ['comparison', 'Before & After', GitCompareArrows],
      ['annotation', 'Annotation Studio', Highlighter],
    ],
  },
  {
    group: 'INTELLIGENCE',
    items: [
      ['ai-detection', 'AI Detection', ScanText],
      ['explanations', 'Explanation & Rewriting', WandSparkles],
      ['model-comparison', 'Model Comparison', Brain],
      ['analytics', 'Analytics & Insights', ChartNoAxesCombined],
      ['quality', 'Quality Scorecard', ShieldCheck],
    ],
  },
  {
    group: 'REPORTING & COLLABORATION',
    items: [
      ['evaluation', 'Evaluation Lab', FlaskConical],
      ['errors', 'Error Analysis', Activity],
      ['reports', 'Reports & Export', FileOutput],
      ['review', 'Review Workspace', Users],
    ],
  },
  {
    group: 'SYSTEM',
    items: [
      ['integrations', 'Integration Status', Network],
      ['viva', 'Viva & Demo', BookOpen],
      ['settings', 'Settings', Settings2],
    ],
  },
];

function ShellInner({ children }: { children: React.ReactNode }) {
  const {
    active, setActive, compact, setCompact, theme, setTheme
  } = useWorkspace();

  const [mobile, setMobile] = useState(false);
  const [command, setCommand] = useState(false);
  const [query, setQuery] = useState('');
  const [clock, setClock] = useState('');

  const all = nav.flatMap(group =>
    group.items.map(([id, label, Icon]) => ({ id, label, Icon }))
  );

  const current = all.find(item => item.id === active);

  const filtered = all.filter(item =>
    item.label.toLowerCase().includes(query.toLowerCase())
  );

  useEffect(() => {
    const update = () => {
      setClock(new Intl.DateTimeFormat('en-IN', {
        hour: '2-digit',
        minute: '2-digit'
      }).format(new Date()));
    };

    update();
    const timer = window.setInterval(update, 30000);
    return () => window.clearInterval(timer);
  }, []);

  useEffect(() => {
    const handler = (event: KeyboardEvent) => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault();
        setCommand(value => !value);
      }
      if (event.key === 'Escape') {
        setCommand(false);
        setMobile(false);
      }
    };

    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, []);

  const choose = (id: string) => {
    setActive(id);
    setMobile(false);
    setCommand(false);
    setQuery('');
  };

  return (
    <div className="app-frame">
      {mobile && (
        <button
          className="mobile-backdrop"
          aria-label="Close navigation"
          onClick={() => setMobile(false)}
        />
      )}

      <aside className={`sidebar ${compact ? 'sidebar-compact' : ''} ${mobile ? 'sidebar-mobile-open' : ''}`}>
        <div className="brand">
          <div className="brand-mark">
            <svg viewBox="0 0 48 48" width="40" height="40" fill="none">
              <circle cx="20" cy="20" r="13" stroke="#2563EB" strokeWidth="2.5" />
              <path d="M29.5 29.5L40 40" stroke="#2563EB" strokeWidth="3" strokeLinecap="round" />
              <path d="M15 17H25M15 21H23M15 25H21" stroke="#2563EB" strokeWidth="1.8" strokeLinecap="round" />
            </svg>
          </div>
          <div className="brand-name">
            <span className="brand-word-clarity">CLARITY</span>
            <span className="brand-word-lint"> LINT</span>
            <small>LANGUAGE INTELLIGENCE</small>
          </div>
          <button className="mobile-close" onClick={() => setMobile(false)} aria-label="Close sidebar">
            <X size={18} />
          </button>
        </div>

        <div className="workspace-switch">
          <span className="workspace-dot" />
          <span>Project workspace</span>
          <ChevronDown size={14} />
        </div>

        <div className="nav-scroll">
          {nav.map(group => (
            <div className="nav-group" key={group.group}>
              <div className="nav-label">{group.group}</div>
              {group.items.map(([id, label, Icon]) => (
                <button
                  key={id}
                  className={`nav-item ${active === id ? 'active' : ''}`}
                  onClick={() => choose(id)}
                  title={label}
                >
                  <Icon size={17} />
                  <span>{label}</span>
                  {active === id && <span className="nav-active-dot" />}
                </button>
              ))}
            </div>
          ))}
        </div>

        <div className="sidebar-bottom">
          <div className="api-mini">
            <span className="pulse-dot" />
            <div>
              <b>Python API</b>
              <small>Connection status</small>
            </div>
            <Tag tone="info">Check</Tag>
          </div>
          <button className="collapse-button" onClick={() => setCompact(!compact)}>
            {compact ? <PanelLeftOpen size={16} /> : <PanelLeftClose size={16} />}
            <span>Collapse sidebar</span>
          </button>
        </div>
      </aside>

      <main className="main-area">
        <header className="topbar">
          <div className="topbar-left">
            <button className="mobile-menu" onClick={() => setMobile(true)} aria-label="Open navigation">
              <Menu size={19} />
            </button>
            <div className="breadcrumb">
              <span>CLARITY LINT</span>
              <span className="crumb-slash">/</span>
              <b>{current?.label.toUpperCase() || 'OVERVIEW'}</b>
            </div>
          </div>

          <div className="topbar-actions">
            <div className="system-pill">
              <span className="status-dot-neutral" />
              <span>Workspace</span>
            </div>
            <span className="top-clock">{clock}</span>
            <button
              className="icon-button"
              onClick={() => setCommand(true)}
              title="Search workspace (Ctrl + K)"
              aria-label="Search workspace"
            >
              <Search size={17} />
            </button>
            <button
              className="icon-button"
              onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
              title="Toggle theme"
              aria-label="Toggle theme"
            >
              {theme === 'dark' ? <Sun size={17} /> : <Moon size={17} />}
            </button>
            <div className="avatar">CL</div>
          </div>
        </header>

        <div className="page-content">{children}</div>

        <footer className="app-footer">
          <span>CLARITY LINT · LANGUAGE INTELLIGENCE</span>
          <span>HUMAN REVIEW ALWAYS REQUIRED</span>
          <span>WORKSPACE</span>
        </footer>
      </main>

      {command && (
        <div className="modal-scrim" onMouseDown={() => setCommand(false)}>
          <div className="command-modal" onMouseDown={event => event.stopPropagation()}>
            <div className="command-search">
              <Search size={18} />
              <input
                autoFocus
                value={query}
                onChange={event => setQuery(event.target.value)}
                placeholder="Find a workspace..."
              />
              <kbd>ESC</kbd>
            </div>
            <div className="command-list">
              {filtered.map(item => (
                <button key={item.id} onClick={() => choose(item.id)}>
                  <item.Icon size={17} />
                  <span>{item.label}</span>
                  <span className="command-enter">↵</span>
                </button>
              ))}
              {!filtered.length && (
                <div className="command-empty">No matching workspace found.</div>
              )}
            </div>
            <div className="command-foot">Navigate quickly · CTRL + K</div>
          </div>
        </div>
      )}
    </div>
  );
}

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <WorkspaceProvider>
      <ShellInner>{children}</ShellInner>
    </WorkspaceProvider>
  );
}

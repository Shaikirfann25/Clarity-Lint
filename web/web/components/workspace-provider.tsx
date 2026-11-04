'use client';
import {createContext,useContext,useEffect,useMemo,useState} from 'react';
type Ctx={active:string;setActive:(v:string)=>void;compact:boolean;setCompact:(v:boolean)=>void;theme:'dark'|'light';setTheme:(v:'dark'|'light')=>void};
const Context=createContext<Ctx|null>(null);
export function WorkspaceProvider({children}:{children:React.ReactNode}){const [active,setActive]=useState('overview');const [compact,setCompact]=useState(false);const [theme,setTheme]=useState<'dark'|'light'>('dark');useEffect(()=>{const v=localStorage.getItem('clarity-theme');if(v==='dark'||v==='light')setTheme(v)},[]);useEffect(()=>{document.documentElement.dataset.theme=theme;localStorage.setItem('clarity-theme',theme)},[theme]);const value=useMemo(()=>({active,setActive,compact,setCompact,theme,setTheme}),[active,compact,theme]);return <Context.Provider value={value}>{children}</Context.Provider>}
export function useWorkspace(){const v=useContext(Context);if(!v)throw new Error('WorkspaceProvider missing');return v}

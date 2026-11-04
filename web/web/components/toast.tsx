'use client';
import {CheckCircle2,AlertCircle,Info,X} from 'lucide-react';
export function Toast({message,kind,onClose}:{message:string;kind:string;onClose:()=>void}){if(!message)return null;const Icon=kind==='success'?CheckCircle2:kind==='error'?AlertCircle:Info;return <div className={`toast toast-${kind}`}><Icon size={17}/><span>{message}</span><button onClick={onClose}><X size={15}/></button></div>}

'use client';
import {useCallback,useState} from 'react';
export function useToast(){const [message,setMessage]=useState('');const [kind,setKind]=useState<'success'|'error'|'info'>('info');const show=useCallback((text:string,type:'success'|'error'|'info'='info')=>{setMessage(text);setKind(type);window.setTimeout(()=>setMessage(''),3600)},[]);return {message,kind,show,clear:()=>setMessage('')}}

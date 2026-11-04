const BASE=process.env.NEXT_PUBLIC_CLARITY_API_URL||'http://127.0.0.1:8000';
export type Detection={source?:string;label:string;span?:string|null;confidence?:number|null;reason?:string};
export type Analysis={sentence_id?:string|null;text:string;detections:Detection[];model_predictions?:unknown[];explanation:string;readings:string[];rewrites:string[];mode:string;latency_ms:number};
export type DocumentResult={sentences:Analysis[];sentence_count:number;flagged_count:number;ambiguity_rate:number;type_counts:Record<string,number>;latency_ms:number;mode:string};
export async function api<T>(path:string,init?:RequestInit):Promise<T>{const response=await fetch(`${BASE}${path}`,{...init,headers:{...(init?.headers||{}),...(init?.body instanceof FormData?{}:{'Content-Type':'application/json'})},cache:'no-store'});const raw=await response.text();let data:any={};try{data=raw?JSON.parse(raw):{}}catch{data={detail:raw}}if(!response.ok)throw new Error(data.detail||data.message||`Request failed (${response.status})`);return data as T}
export const analyzeText=(text:string)=>api<Analysis>('/api/analyze',{method:'POST',body:JSON.stringify({text})});
export const analyzeDocument=(text:string)=>api<DocumentResult>('/api/document',{method:'POST',body:JSON.stringify({text})});
export const getHealth=()=>api<any>('/health');export const getStatus=()=>api<any>('/api/status');export const getDemoEvaluation=()=>api<any>('/api/evaluation/demo');
export async function uploadEvaluation(file:File){const form=new FormData();form.append('file',file);return api<any>('/api/evaluate',{method:'POST',body:form})}
export const API_BASE=BASE;

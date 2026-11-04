import type {Metadata} from 'next';import './globals.css';import {AppShell} from '@/components/app-shell';
export const metadata:Metadata={title:'Clarity Lint — Imperial Jade',description:'A human-in-the-loop NLP workspace for finding and resolving ambiguity.'};
export default function RootLayout({children}:{children:React.ReactNode}){return <html lang="en"><body><AppShell>{children}</AppShell></body></html>}

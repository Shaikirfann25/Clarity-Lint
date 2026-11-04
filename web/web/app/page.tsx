'use client';
import {useWorkspace} from '@/components/workspace-provider';
import {Overview} from '@/features/overview/overview';
import {AnalysisWorkbench} from '@/features/analyze/analyzer';
import {DocumentWorkbench} from '@/features/documents/document-workbench';
import {EvaluationWorkbench} from '@/features/evaluation/evaluation-workbench';
import {ErrorWorkbench} from '@/features/errors/error-workbench';
import {IntegrationWorkbench} from '@/features/integrations/integration-workbench';
import {VivaWorkbench} from '@/features/viva/viva-workbench';
import {SettingsWorkbench} from '@/features/settings/settings-workbench';
export default function Home(){const {active,setActive}=useWorkspace();const pages:Record<string,React.ReactNode>={overview:<Overview onNavigate={setActive}/>,analyze:<AnalysisWorkbench/>,documents:<DocumentWorkbench/>,evaluation:<EvaluationWorkbench/>,errors:<ErrorWorkbench/>,integrations:<IntegrationWorkbench/>,viva:<VivaWorkbench/>,settings:<SettingsWorkbench/>};return <>{pages[active]||pages.overview}</>}

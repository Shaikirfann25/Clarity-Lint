'use client';

import { useWorkspace } from '@/components/workspace-provider';

import { Overview } from '@/features/overview/overview';
import { AnalysisWorkbench } from '@/features/analyze/analyzer';
import { DocumentWorkbench } from '@/features/documents/document-workbench';
import { EvaluationWorkbench } from '@/features/evaluation/evaluation-workbench';
import { ErrorWorkbench } from '@/features/errors/error-workbench';
import { IntegrationWorkbench } from '@/features/integrations/integration-workbench';
import { VivaWorkbench } from '@/features/viva/viva-workbench';
import { SettingsWorkbench } from '@/features/settings/settings-workbench';
import { WorkspaceFeature } from '@/features/workspace/workspace-feature';

const workspacePages: Record<string, {
  title: string;
  description: string;
  category: string;
}> = {
  history: {
    title: 'Analysis History',
    description: 'A planned workspace for reviewing previous text and document analyses.',
    category: 'WORKSPACE'
  },
  comparison: {
    title: 'Before & After Comparison',
    description: 'A planned workspace for comparing original sentences with clearer rewrites.',
    category: 'WORKSPACE'
  },
  annotation: {
    title: 'Annotation Studio',
    description: 'A planned workspace for reviewing and manually annotating ambiguity examples.',
    category: 'WORKSPACE'
  },
  'ai-detection': {
    title: 'AI Detection',
    description: 'Inspect the availability and output of the ambiguity detection components.',
    category: 'INTELLIGENCE'
  },
  explanations: {
    title: 'Explanation & Rewriting',
    description: 'A dedicated workspace for explanations, alternate readings and suggested rewrites.',
    category: 'INTELLIGENCE'
  },
  'model-comparison': {
    title: 'Model Comparison',
    description: 'Compare model predictions only when valid results from the same test examples are available.',
    category: 'INTELLIGENCE'
  },
  analytics: {
    title: 'Analytics & Insights',
    description: 'A planned workspace for evidence-based ambiguity trends and analysis statistics.',
    category: 'INTELLIGENCE'
  },
  quality: {
    title: 'Quality Scorecard',
    description: 'A planned workspace for clarity indicators and review quality measurements.',
    category: 'INTELLIGENCE'
  },
  reports: {
    title: 'Reports & Export',
    description: 'A planned workspace for exporting verified analysis and evaluation results.',
    category: 'REPORTING & COLLABORATION'
  },
  review: {
    title: 'Review Workspace',
    description: 'A planned workspace for organizing human review and tracking resolution.',
    category: 'REPORTING & COLLABORATION'
  }
};

export default function Home() {
  const { active, setActive } = useWorkspace();

  const pages: Record<string, React.ReactNode> = {
    overview: <Overview onNavigate={setActive} />,
    analyze: <AnalysisWorkbench />,
    documents: <DocumentWorkbench />,
    evaluation: <EvaluationWorkbench />,
    errors: <ErrorWorkbench />,
    integrations: <IntegrationWorkbench />,
    viva: <VivaWorkbench />,
    settings: <SettingsWorkbench />
  };

  if (pages[active]) return <>{pages[active]}</>;

  const feature = workspacePages[active];

  if (feature) {
    return (
      <WorkspaceFeature
        title={feature.title}
        description={feature.description}
        category={feature.category}
        featureId={active}
      />
    );
  }

  return <Overview onNavigate={setActive} />;
}

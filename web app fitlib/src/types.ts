export interface Citation {
  id: string;
  type: 'Meta-Analysis' | 'RCT' | 'Review' | 'Systematic Review';
  credibilityScore: number;
  author: string;
  year: number;
  title: string;
  journal: string;
  doi?: string;
  pubmedId?: string;
  qualityBreakdown: {
    studyDesign: number;
    evidenceQuality: number;
    biasRisk: 'Low' | 'Medium' | 'High';
    automationValidated: boolean;
  };
}

export interface NodeData {
  id: string;
  title: string;
  series: 'A' | 'B' | 'C' | 'E' | 'Other';
  created?: string;
  updated?: string;
  content: string;
  credibilityScore: number;
  citationCount: number;
  citations: Citation[];
  links: string[]; // IDs of connected nodes
  tags: string[];
}

export interface NodeSummary {
  id: string;
  title: string;
  series: 'A' | 'B' | 'C' | 'E' | 'Other';
  created?: string;
  updated?: string;
  credibilityScore: number;
  citationCount: number;
  links: string[];
  tags: string[];
  excerpt: string;
}

export interface GraphNode extends d3.SimulationNodeDatum {
  id: string;
  title: string;
  series: string;
  credibilityScore: number;
  citationCount: number;
}

export interface GraphLink extends d3.SimulationLinkDatum<GraphNode> {
  source: string;
  target: string;
  strength: number;
}

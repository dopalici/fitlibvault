import { NodeData } from '../types';

export const MOCK_NODES: NodeData[] = [
  {
    id: '1',
    title: 'Anabolic Resistance',
    series: 'A',
    content: '# Anabolic Resistance\n\nAnabolic resistance describes the blunted muscle protein synthesis (MPS) response to protein ingestion and resistance exercise, commonly observed in aging populations.\n\n## Key Takeaways\n- Requires higher leucine dosages to overcome.\n- Physically active older adults show less resistance.\n- Systemic inflammation is a primary driver.',
    credibilityScore: 0.95,
    citationCount: 12,
    citations: [
      {
        id: 'c1',
        type: 'Meta-Analysis',
        credibilityScore: 0.98,
        author: 'Schoenfeld BJ',
        year: 2021,
        title: 'Evidence-based guidelines for protein intake in older adults',
        journal: 'Nutrients',
        doi: '10.3390/nu13062021',
        qualityBreakdown: {
          studyDesign: 5,
          evidenceQuality: 5,
          biasRisk: 'Low',
          automationValidated: true
        }
      }
    ],
    links: ['2', '3'],
    tags: ['Skeletal Muscle', 'Aging', 'Hypertrophy']
  },
  {
    id: '2',
    title: 'Hypertrophy Mechanisms',
    series: 'B',
    content: '# Hypertrophy Mechanisms\n\nMechanical tension, metabolic stress, and muscle damage were traditionally cited as the three main drivers of hypertrophy. Modern research emphasizes mechanical tension as the primary driver.',
    credibilityScore: 0.88,
    citationCount: 45,
    citations: [],
    links: ['1', '4'],
    tags: ['Muscle Growth', 'Physiology']
  },
  {
    id: '3',
    title: 'Protein Timing Myth',
    series: 'C',
    content: '# Protein Timing Myth\n\nThe "anabolic window" is significantly wider than the often-cited 30-60 minutes post-workout.',
    credibilityScore: 0.92,
    citationCount: 18,
    citations: [],
    links: ['1'],
    tags: ['Nutrition', 'Timing']
  },
  {
    id: '4',
    title: 'Progressive Overload',
    series: 'B',
    content: '# Progressive Overload\n\nThe gradual increase of stress placed upon the body during exercise training.',
    credibilityScore: 1.0,
    citationCount: 120,
    citations: [],
    links: ['2'],
    tags: ['Training Principles']
  }
];

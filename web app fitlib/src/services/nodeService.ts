import { collection, getDocs, doc, getDoc } from 'firebase/firestore';
import { db, handleFirestoreError, OperationType } from '../lib/firebase';
import { NodeData, Citation, NodeSummary } from '../types';
import { getApiUrl } from '../lib/env';

interface SearchNodesParams {
  search?: string;
  series?: string;
  limit?: number;
}

interface ContentBridgeIndex {
  generatedAt: string;
  totalNodes: number;
  nodes: NodeSummary[];
}

const CONTENT_INDEX_PATH = '/content/index.json';
const CONTENT_NODE_PATH = '/content/nodes';
const CONTENT_SERIES_PATH = '/content/series';
const BRIDGE_STORAGE_KEY = 'fitlib.contentBridge.index';
let cachedBridgeIndex: ContentBridgeIndex | null = null;
const cachedNodeDetails = new Map<string, NodeData>();

type NodeSeries = NodeSummary['series'];

function matchesSearch(node: NodeSummary, search?: string): boolean {
  if (!search) return true;
  const normalized = search.toLowerCase().trim();
  if (!normalized) return true;
  const haystack = `${node.title} ${node.excerpt} ${(node.tags || []).join(' ')}`.toLowerCase();
  return haystack.includes(normalized);
}

async function loadBridgeIndex(): Promise<ContentBridgeIndex | null> {
  if (cachedBridgeIndex) {
    return cachedBridgeIndex;
  }
  try {
    const response = await fetch(CONTENT_INDEX_PATH, { cache: 'no-cache' });
    if (!response.ok) return null;
    const nextIndex = (await response.json()) as ContentBridgeIndex;
    const cachedString = typeof window !== 'undefined' ? localStorage.getItem(BRIDGE_STORAGE_KEY) : null;
    const cachedParsed = cachedString ? (JSON.parse(cachedString) as ContentBridgeIndex) : null;

    if (cachedParsed && cachedParsed.generatedAt === nextIndex.generatedAt) {
      cachedBridgeIndex = cachedParsed;
      return cachedBridgeIndex;
    }

    cachedBridgeIndex = nextIndex;
    if (typeof window !== 'undefined') {
      localStorage.setItem(BRIDGE_STORAGE_KEY, JSON.stringify(nextIndex));
    }
    return cachedBridgeIndex;
  } catch {
    try {
      if (typeof window !== 'undefined') {
        const cachedString = localStorage.getItem(BRIDGE_STORAGE_KEY);
        if (cachedString) {
          cachedBridgeIndex = JSON.parse(cachedString) as ContentBridgeIndex;
          return cachedBridgeIndex;
        }
      }
    } catch {
      // Ignore cache parse errors and fall through.
    }
    return null;
  }
}

async function loadBridgeSeries(series: NodeSeries): Promise<NodeSummary[] | null> {
  try {
    const response = await fetch(`${CONTENT_SERIES_PATH}/${series}.json`);
    if (!response.ok) return null;
    const payload = (await response.json()) as { nodes: NodeSummary[] };
    return payload.nodes || null;
  } catch {
    return null;
  }
}

async function loadBridgeNode(nodeId: string): Promise<NodeData | null> {
  const cachedNode = cachedNodeDetails.get(nodeId);
  if (cachedNode) {
    return cachedNode;
  }
  try {
    const response = await fetch(`${CONTENT_NODE_PATH}/${encodeURIComponent(nodeId)}.json`);
    if (!response.ok) return null;
    const node = (await response.json()) as NodeData;
    cachedNodeDetails.set(nodeId, node);
    return node;
  } catch {
    return null;
  }
}

export const nodeService = {
  async getAllNodes(): Promise<NodeData[]> {
    const bridgeIndex = await loadBridgeIndex();
    if (bridgeIndex) {
      return bridgeIndex.nodes.map((node) => ({
        ...node,
        content: node.excerpt,
        citations: [],
      })) as NodeData[];
    }

    const path = 'nodes';
    try {
      const snap = await getDocs(collection(db, path));
      return snap.docs.map(doc => ({ id: doc.id, ...doc.data() } as NodeData));
    } catch (error) {
      handleFirestoreError(error, OperationType.LIST, path);
      return [];
    }
  },

  async searchNodes(params: SearchNodesParams): Promise<NodeData[]> {
    const seriesChunk = params.series ? await loadBridgeSeries(params.series as NodeSeries) : null;
    const bridgeIndex = seriesChunk ? { nodes: seriesChunk } : await loadBridgeIndex();
    if (bridgeIndex?.nodes) {
      const filtered = bridgeIndex.nodes
        .filter((node) => (!params.series ? true : node.series === params.series))
        .filter((node) => matchesSearch(node, params.search));

      const sliced = typeof params.limit === 'number'
        ? filtered.slice(0, params.limit)
        : filtered;

      return sliced.map((node) => ({
        ...node,
        content: node.excerpt,
        citations: [],
      })) as NodeData[];
    }

    const queryParams = new URLSearchParams();
    if (params.search) {
      queryParams.set('search', params.search);
    }
    if (params.series) {
      queryParams.set('series', params.series);
    }
    if (typeof params.limit === 'number') {
      queryParams.set('limit', String(params.limit));
    }

    try {
      const response = await fetch(getApiUrl(`/api/nodes?${queryParams.toString()}`));
      if (!response.ok) {
        throw new Error('Search API request failed');
      }
      const data = await response.json();
      return (data.nodes || []) as NodeData[];
    } catch (error) {
      handleFirestoreError(error, OperationType.LIST, 'api/nodes');
      return [];
    }
  },

  async getNodeById(id: string): Promise<NodeData | null> {
    const path = `nodes/${id}`;
    try {
      const bridgeNode = await loadBridgeNode(id);
      if (bridgeNode) {
        return bridgeNode;
      }

      const response = await fetch(getApiUrl(`/api/nodes/${id}`));
      if (response.ok) {
        return (await response.json()) as NodeData;
      }

      // Keep Firestore fallback for local/offline development.
      const nodeDoc = await getDoc(doc(db, 'nodes', id));
      if (!nodeDoc.exists()) return null;

      const citationsSnap = await getDocs(collection(db, `nodes/${id}/citations`));
      const citations = citationsSnap.docs.map(d => ({ id: d.id, ...d.data() } as Citation));
      const node = { id: nodeDoc.id, ...nodeDoc.data(), citations } as NodeData;
      cachedNodeDetails.set(id, node);
      return node;
    } catch (error) {
      handleFirestoreError(error, OperationType.GET, path);
      return null;
    }
  },

  async prefetchNodes(ids: string[]): Promise<void> {
    const uniqueIds = [...new Set(ids)].filter((id) => id && !cachedNodeDetails.has(id)).slice(0, 12);
    await Promise.all(uniqueIds.map(async (id) => {
      await loadBridgeNode(id);
    }));
  }
};

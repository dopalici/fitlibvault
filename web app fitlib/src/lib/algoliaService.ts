import { algoliasearch } from 'algoliasearch';
import { env } from './env';

const ALGOLIA_APP_ID = env.algoliaAppId;
const ALGOLIA_SEARCH_KEY = env.algoliaSearchKey;
const ALGOLIA_INDEX_NAME = env.algoliaIndexName;

// Initialize Algolia client
let searchClient: any = null;
let index: any = null;

if (ALGOLIA_APP_ID && ALGOLIA_SEARCH_KEY) {
  try {
    searchClient = algoliasearch(ALGOLIA_APP_ID, ALGOLIA_SEARCH_KEY);
    index = searchClient.index ? searchClient.index(ALGOLIA_INDEX_NAME) : null;
  } catch (error) {
    console.warn('Algolia initialization failed:', error);
  }
}

function assertAlgoliaConfigured() {
  if (!index) {
    throw new Error('Algolia is not configured');
  }
}

export interface AlgoliaNode {
  objectID: string;
  title: string;
  content: string;
  category: string;
  author: string;
  tags: string[];
  level: 'beginner' | 'intermediate' | 'advanced';
  readingTime: number;
  citations: string[];
  createdAt: number;
  updatedAt: number;
}

export interface SearchOptions {
  query: string;
  filters?: string;
  facetFilters?: string[][];
  numericFilters?: string[];
  page?: number;
  hitsPerPage?: number;
  attributesToRetrieve?: string[];
  attributesToHighlight?: string[];
  highlightPreTag?: string;
  highlightPostTag?: string;
}

export interface SearchResult {
  hits: AlgoliaNode[];
  nbHits: number;
  page: number;
  nbPages: number;
  hitsPerPage: number;
  processingTimeMS: number;
  exhaustiveNbHits: boolean;
  query: string;
  params: string;
}

export class AlgoliaSearchService {
  private static instance: AlgoliaSearchService;

  private constructor() {}

  public static getInstance(): AlgoliaSearchService {
    if (!AlgoliaSearchService.instance) {
      AlgoliaSearchService.instance = new AlgoliaSearchService();
    }
    return AlgoliaSearchService.instance;
  }

  /**
   * Search for nodes using Algolia
   */
  async search(options: SearchOptions): Promise<SearchResult> {
    try {
      assertAlgoliaConfigured();
      const searchParams: any = {
        query: options.query,
        page: options.page || 0,
        hitsPerPage: options.hitsPerPage || 20,
        attributesToRetrieve: options.attributesToRetrieve || [
          'objectID',
          'title',
          'content',
          'category',
          'author',
          'tags',
          'level',
          'readingTime',
          'createdAt'
        ],
        attributesToHighlight: options.attributesToHighlight || ['title', 'content'],
        highlightPreTag: options.highlightPreTag || '<mark class="bg-yellow-200 text-yellow-900">',
        highlightPostTag: options.highlightPostTag || '</mark>'
      };

      if (options.filters) {
        searchParams.filters = options.filters;
      }

      if (options.facetFilters) {
        searchParams.facetFilters = options.facetFilters;
      }

      if (options.numericFilters) {
        searchParams.numericFilters = options.numericFilters;
      }

      const result = await index.search(options.query, searchParams);
      
      return {
        hits: result.hits as AlgoliaNode[],
        nbHits: result.nbHits,
        page: result.page,
        nbPages: result.nbPages,
        hitsPerPage: result.hitsPerPage,
        processingTimeMS: result.processingTimeMS,
        exhaustiveNbHits: result.exhaustiveNbHits,
        query: result.query,
        params: result.params
      };
    } catch (error) {
      console.error('Algolia search error:', error);
      throw new Error('Search failed');
    }
  }

  /**
   * Get search suggestions/autocomplete
   */
  async getSearchSuggestions(query: string, maxSuggestions = 5): Promise<string[]> {
    try {
      const result = await this.search({
        query,
        hitsPerPage: maxSuggestions,
        attributesToRetrieve: ['title']
      });

      return result.hits.map(hit => hit.title);
    } catch (error) {
      console.error('Algolia suggestions error:', error);
      return [];
    }
  }

  /**
   * Search by category with faceted search
   */
  async searchByCategory(category: string, query = '', page = 0): Promise<SearchResult> {
    return this.search({
      query,
      facetFilters: [['category:' + category]],
      page,
      hitsPerPage: 20
    });
  }

  /**
   * Advanced search with multiple filters
   */
  async advancedSearch({
    query = '',
    category,
    level,
    author,
    tags = [],
    minReadingTime,
    maxReadingTime,
    page = 0
  }: {
    query?: string;
    category?: string;
    level?: 'beginner' | 'intermediate' | 'advanced';
    author?: string;
    tags?: string[];
    minReadingTime?: number;
    maxReadingTime?: number;
    page?: number;
  }): Promise<SearchResult> {
    const facetFilters: string[][] = [];
    const numericFilters: string[] = [];

    if (category) {
      facetFilters.push([`category:${category}`]);
    }

    if (level) {
      facetFilters.push([`level:${level}`]);
    }

    if (author) {
      facetFilters.push([`author:${author}`]);
    }

    if (tags.length > 0) {
      facetFilters.push(tags.map(tag => `tags:${tag}`));
    }

    if (minReadingTime !== undefined) {
      numericFilters.push(`readingTime >= ${minReadingTime}`);
    }

    if (maxReadingTime !== undefined) {
      numericFilters.push(`readingTime <= ${maxReadingTime}`);
    }

    return this.search({
      query,
      facetFilters: facetFilters.length > 0 ? facetFilters : undefined,
      numericFilters: numericFilters.length > 0 ? numericFilters : undefined,
      page
    });
  }

  /**
   * Get popular searches (mock implementation - in production, track this data)
   */
  getPopularSearches(): string[] {
    return [
      'protein synthesis',
      'muscle hypertrophy',
      'creatine supplementation',
      'vo2 max training',
      'periodization',
      'recovery protocols',
      'nutrition timing',
      'strength training',
      'endurance training',
      'metabolic flexibility'
    ];
  }

  /**
   * Get search facets for filtering UI
   */
  async getFacets(): Promise<{
    categories: { name: string; count: number }[];
    levels: { name: string; count: number }[];
    authors: { name: string; count: number }[];
  }> {
    try {
      assertAlgoliaConfigured();
      // Get facet counts
      const result = await index.search('', {
        facets: ['category', 'level', 'author'],
        hitsPerPage: 0
      });

      const facets = result.facets || {};

      return {
        categories: Object.entries(facets.category || {}).map(([name, count]) => ({
          name,
          count: count as number
        })),
        levels: Object.entries(facets.level || {}).map(([name, count]) => ({
          name,
          count: count as number
        })),
        authors: Object.entries(facets.author || {}).map(([name, count]) => ({
          name,
          count: count as number
        }))
      };
    } catch (error) {
      console.error('Error fetching facets:', error);
      return {
        categories: [],
        levels: [],
        authors: []
      };
    }
  }
}

// Export singleton instance
export const algoliaService = AlgoliaSearchService.getInstance();

// Fallback search for when Algolia is not configured
export class FallbackSearchService {
  async search(query: string, nodes: any[]): Promise<any[]> {
    if (!query.trim()) return nodes;
    
    const searchTerm = query.toLowerCase();
    return nodes.filter(node =>
      node.title?.toLowerCase().includes(searchTerm) ||
      node.content?.toLowerCase().includes(searchTerm) ||
      node.category?.toLowerCase().includes(searchTerm) ||
      node.author?.toLowerCase().includes(searchTerm) ||
      node.tags?.some((tag: string) => tag.toLowerCase().includes(searchTerm))
    );
  }
}

export const fallbackSearchService = new FallbackSearchService();
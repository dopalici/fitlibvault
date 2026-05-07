import { NodeData } from '../types';

const WIKILINK_REGEX = /\[\[([^[\]]+)\]\]/g;

function normalizeTarget(value: string): string {
  return value
    .toLowerCase()
    .replace(/\.md$/i, '')
    .replace(/[_-]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

export function buildWikilinkResolver(nodes: NodeData[]): Map<string, string> {
  const map = new Map<string, string>();

  nodes.forEach((node) => {
    const aliases = new Set<string>([
      node.id,
      node.title,
      `${node.title}.md`,
    ]);

    const idPrefix = node.title.match(/^([A-Z]{1,4}-?\d+)\b/i)?.[1];
    if (idPrefix) {
      aliases.add(idPrefix.toUpperCase());
    }

    aliases.forEach((alias) => map.set(normalizeTarget(alias), node.id));
  });

  return map;
}

export function convertWikilinksToMarkdown(content: string, resolver: Map<string, string>): string {
  return content.replace(WIKILINK_REGEX, (_, raw: string) => {
    const [targetWithHeading, labelPart] = raw.split('|');
    const [target] = targetWithHeading.split('#');
    const normalizedTarget = normalizeTarget(target);
    const resolvedId = resolver.get(normalizedTarget);
    const label = (labelPart || target).trim();

    if (!resolvedId) {
      return label;
    }

    return `[${label}](fitlib://node/${encodeURIComponent(resolvedId)})`;
  });
}

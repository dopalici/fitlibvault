import fs from 'fs';
import path from 'path';

interface UnresolvedReport {
  generated_at?: string;
  summary?: {
    total_wikilinks?: number;
    resolved_wikilinks?: number;
    unresolved_wikilinks?: number;
    unresolved_unique_targets?: number;
  };
  unresolved_by_target?: Array<{ target?: string; count?: number }>;
}

const PROJECT_ROOT = process.cwd();
const REPORT_PATH = path.join(PROJECT_ROOT, '..', 'wikilink_unresolved_report.json');

function fail(message: string): never {
  console.error(`❌ ${message}`);
  process.exit(1);
}

if (!fs.existsSync(REPORT_PATH)) {
  fail(`Missing unresolved report at ${REPORT_PATH}. Run "npm run content:build" first.`);
}

let report: UnresolvedReport;
try {
  report = JSON.parse(fs.readFileSync(REPORT_PATH, 'utf-8')) as UnresolvedReport;
} catch (error) {
  fail(`Could not parse unresolved report JSON: ${error instanceof Error ? error.message : String(error)}`);
}

const unresolved = report.summary?.unresolved_wikilinks ?? 0;
const unique = report.summary?.unresolved_unique_targets ?? 0;

if (unresolved > 0) {
  console.error(`❌ Found ${unresolved} unresolved wikilinks across ${unique} unique targets.`);
  const top = (report.unresolved_by_target || []).slice(0, 20);
  if (top.length > 0) {
    console.error('Top unresolved targets:');
    top.forEach(({ target, count }) => {
      console.error(`  - ${count ?? 0}x [[${target ?? 'unknown'}]]`);
    });
  }
  process.exit(1);
}

console.log(
  `✅ Wikilink check passed: 0 unresolved links (${report.summary?.resolved_wikilinks ?? 0}/${report.summary?.total_wikilinks ?? 0} resolved).`
);

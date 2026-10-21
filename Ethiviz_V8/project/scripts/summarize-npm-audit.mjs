import { readFile } from 'node:fs/promises';

const reportPath = process.argv[2];
if (!reportPath) {
  throw new Error('Usage: node scripts/summarize-npm-audit.mjs <npm-audit-json>');
}

const report = JSON.parse(await readFile(reportPath, 'utf8'));
const summary = {
  production: { info: 0, low: 0, moderate: 0, high: 0, critical: 0 },
  development: { info: 0, low: 0, moderate: 0, high: 0, critical: 0 },
};

for (const vulnerability of Object.values(report.vulnerabilities ?? {})) {
  const target = vulnerability.dev ? summary.development : summary.production;
  const severity = vulnerability.severity;
  if (Object.hasOwn(target, severity)) target[severity] += 1;
}

console.log(JSON.stringify(summary, null, 2));

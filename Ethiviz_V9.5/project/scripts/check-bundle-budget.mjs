import { gzipSync } from 'node:zlib';
import { readFile, readdir } from 'node:fs/promises';
import path from 'node:path';

const outputDirectory = path.resolve('dist');
const html = await readFile(path.join(outputDirectory, 'index.html'), 'utf8');
const entryPaths = [
  ...[...html.matchAll(/<script[^>]+src="([^"]+)"/g)].map((match) => match[1]),
  ...[...html.matchAll(/<link[^>]+rel="modulepreload"[^>]+href="([^"]+)"/g)]
    .map((match) => match[1]),
];
const entryFiles = [...new Set(entryPaths)]
  .map((entry) => path.join(outputDirectory, entry.replace(/^\//, '')));

if (entryFiles.length === 0) {
  throw new Error('No JavaScript entry bundle was found in dist/index.html.');
}

const entryBytes = (await Promise.all(entryFiles.map(async (file) => {
  const contents = await readFile(file);
  return gzipSync(contents).byteLength;
}))).reduce((total, bytes) => total + bytes, 0);
const budgetKilobytes = Number(process.env.VITE_INITIAL_BUNDLE_BUDGET_KB ?? 400);

if (!Number.isFinite(budgetKilobytes) || budgetKilobytes <= 0) {
  throw new Error('VITE_INITIAL_BUNDLE_BUDGET_KB must be a positive number.');
}

console.log(`Initial JavaScript bundle: ${(entryBytes / 1024).toFixed(1)} KiB gzip (budget ${budgetKilobytes} KiB).`);
if (entryBytes > budgetKilobytes * 1024) {
  const files = await readdir(path.join(outputDirectory, 'assets'));
  console.error(`Built assets: ${files.join(', ')}`);
  throw new Error('Initial JavaScript bundle exceeds its compressed budget.');
}

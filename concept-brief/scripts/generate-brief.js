#!/usr/bin/env node
/**
 * Automation Concept Brief Generator
 * Brand: Sambhav Builds
 * 
 * Usage:
 *   node generate-brief.js [--data path/to/data.json] [--out path/to/output.html]
 */

const fs = require('fs');
const path = require('path');

const ROOT_DIR = path.resolve(__dirname, '..');
const DEFAULT_TEMPLATE = path.join(ROOT_DIR, 'template.html');
const DEFAULT_DATA = path.join(ROOT_DIR, 'brief-data.json');
const DEFAULT_OUT = path.join(ROOT_DIR, 'examples', 'maintenance-triage-brief.html');

function parseArgs() {
  const args = process.argv.slice(2);
  let templatePath = DEFAULT_TEMPLATE;
  let dataPath = DEFAULT_DATA;
  let outPath = DEFAULT_OUT;

  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--template' && args[i + 1]) {
      templatePath = path.resolve(args[++i]);
    } else if (args[i] === '--data' && args[i + 1]) {
      dataPath = path.resolve(args[++i]);
    } else if (args[i] === '--out' && args[i + 1]) {
      outPath = path.resolve(args[++i]);
    }
  }

  return { templatePath, dataPath, outPath };
}

function main() {
  const { templatePath, dataPath, outPath } = parseArgs();

  if (!fs.existsSync(templatePath)) {
    console.error(`Error: Template not found at ${templatePath}`);
    process.exit(1);
  }

  if (!fs.existsSync(dataPath)) {
    console.error(`Error: Data JSON not found at ${dataPath}`);
    process.exit(1);
  }

  const templateHtml = fs.readFileSync(templatePath, 'utf8');
  const data = JSON.parse(fs.readFileSync(dataPath, 'utf8'));

  // Replace data-field elements with content
  let rendered = templateHtml;
  for (const [key, val] of Object.entries(data)) {
    // Replace <span data-field="key">...</span> or any tag with data-field="key"
    const regex = new RegExp(`(<[^>]+data-field=["']${key}["'][^>]*>)(.*?)(<\/[^>]+>)`, 'gi');
    rendered = rendered.replace(regex, `$1${val}$3`);

    // Also support raw bracket placeholders: [KEY] or {{KEY}}
    const placeholderUpper = new RegExp(`\\[${key.toUpperCase()}\\]`, 'g');
    const placeholderMustache = new RegExp(`\\{\\{\\s*${key}\\s*\\}\\}`, 'gi');
    rendered = rendered.replace(placeholderUpper, val);
    rendered = rendered.replace(placeholderMustache, val);
  }

  // Keep the stylesheet paired with the selected template (template.css,
  // template-v2.css, and future named variants) when output is nested.
  const templateBase = path.basename(templatePath, path.extname(templatePath));
  const stylesheetName = `${templateBase}.css`;
  const relativeCssPath = path.relative(path.dirname(outPath), path.join(ROOT_DIR, stylesheetName)).replace(/\\/g, '/');
  rendered = rendered.replace(new RegExp(`href=["']${stylesheetName.replace('.', '\\.') }["']`, 'i'), `href="${relativeCssPath}"`);

  // Ensure output directory exists
  const outDir = path.dirname(outPath);
  if (!fs.existsSync(outDir)) {
    fs.mkdirSync(outDir, { recursive: true });
  }

  fs.writeFileSync(outPath, rendered, 'utf8');
  console.log(`✓ Concept Brief generated successfully at:`);
  console.log(`  ${outPath}`);
}

main();

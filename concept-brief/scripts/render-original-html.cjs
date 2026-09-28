/** Render and check the editable HTML recreation of the earlier square PDF. */
const fs = require("node:fs");
const path = require("node:path");
const os = require("node:os");
const { pathToFileURL } = require("node:url");
const root = path.resolve(__dirname, "../..");
let playwright;
try {
  playwright = require("playwright");
} catch {
  playwright = require(path.join(os.homedir(), ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright"));
}

(async () => {
  const browser = await playwright.chromium.launch({ channel: process.env.BRIEF_BROWSER || "msedge", headless: true });
  try {
    const page = await browser.newPage({ viewport: { width: 1000, height: 1000 }, deviceScaleFactor: 1 });
    const errors = [];
    page.on("pageerror", (error) => errors.push(error.message));
    await page.goto(pathToFileURL(path.join(root, "concept-brief/square-brief-original.html")).href);
    await page.evaluate(() => document.fonts.ready);
    const link = await page.locator(".cta a").getAttribute("href");
    const checks = await page.evaluate(() => [...document.querySelectorAll(".page")].map((paper) => {
      const pageRect = paper.getBoundingClientRect();
      const footer = paper.querySelector(".page-footer").getBoundingClientRect();
      const escaped = [...paper.querySelectorAll("h1,h2,h3,p,.comparison-card,.stage,.external-card,.stack-card,.routes,.cta")]
        .filter((element) => {
          const box = element.getBoundingClientRect();
          return box.left < pageRect.left - .5 || box.right > pageRect.right + .5 || box.bottom > footer.top - 1;
        })
        .map((element) => element.className || element.tagName);
      const clipped = [...paper.querySelectorAll(".comparison-card,.stage,.external-card,.stack-card,.research-copy,.daily .shell-inner,.authority .shell-inner,.controls,.cta .shell-inner")]
        .filter((parent) => {
          const box = parent.getBoundingClientRect();
          return [...parent.querySelectorAll("h2,h3,p,strong,.actor,a")].some((child) => {
            const b = child.getBoundingClientRect();
            return b.right > box.right + 1 || b.bottom > box.bottom + 1;
          });
        })
        .map((element) => element.className);
      return { width: pageRect.width, height: pageRect.height, escaped, clipped };
    }));
    const dest = path.join(root, "tmp/pdfs/original-html");
    fs.mkdirSync(dest, { recursive: true });
    for (let i = 0; i < 4; i++) await page.locator(".page").nth(i).screenshot({ path: path.join(dest, `page-${i + 1}.png`) });
    if (errors.length || link !== "https://cal.com/sambhav-builds/pm-automation-audit" || checks.length !== 4 || checks.some((check) => check.width !== 864 || check.height !== 864 || check.escaped.length || check.clipped.length)) {
      throw new Error(JSON.stringify({ errors, link, checks }, null, 2));
    }
    const output = path.join(root, "output/pdf/maintenance-triage-square-brief-html-recreation.pdf");
    await page.emulateMedia({ media: "print" });
    await page.pdf({ path: output, preferCSSPageSize: true, printBackground: true, displayHeaderFooter: false, tagged: true });
    console.log(JSON.stringify({ checks, link, screenshots: dest, output }, null, 2));
  } finally {
    await browser.close();
  }
})().catch((error) => { console.error(error); process.exitCode = 1; });

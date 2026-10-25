/** Export the editable HTML/CSS through Chromium. No ReportLab drawing. */
const fs = require("node:fs");
const path = require("node:path");
const { pathToFileURL } = require("node:url");
const root = path.resolve(__dirname, "../..");
let playwright;
try {
  playwright = require("playwright");
} catch {
  const bundled = path.join(
    require("node:os").homedir(),
    ".cache/playwright-runtimes/dependencies/node/node_modules/playwright",
  );
  playwright = require(
    process.env.BRIEF_PLAYWRIGHT_PATH || path.resolve(bundled),
  );
}
(async () => {
  const browser = await playwright.chromium.launch({
    channel: process.env.BRIEF_BROWSER || "msedge",
    headless: true,
  });
  try {
    const page = await browser.newPage({
      viewport: { width: 1000, height: 1000 },
      deviceScaleFactor: 1,
    });
    const errors = [];
    page.on("pageerror", (error) => errors.push(error.message));
    await page.goto(
      pathToFileURL(path.join(root, "concept-brief/square-brief.html")).href,
    );
    await page.evaluate(() => document.fonts.ready);
    await page.emulateMedia({ media: "print" });
    const checks = await page.evaluate(() =>
      [...document.querySelectorAll(".page")].map((p) => {
        const box = p.getBoundingClientRect();
        const footer = p.querySelector("footer").getBoundingClientRect();
        const last = p
          .querySelector("footer")
          .previousElementSibling.getBoundingClientRect();
        const escaped = [...p.querySelectorAll("*")]
          .filter((e) => {
            if (e.closest("svg")) return false;
            const b = e.getBoundingClientRect();
            return (
              b.left < box.left - 0.5 ||
              b.right > box.right + 0.5 ||
              b.bottom > box.bottom + 0.5
            );
          })
          .map((e) => e.className || e.tagName);
        const containers = [
          ...p.querySelectorAll(
            ".system-card,.hosting,.research-sources,.process,.dark-panel,.cta",
          ),
        ];
        const contentOverflow = containers
          .filter((e) => {
            const bounds = e.getBoundingClientRect();
            return [...e.querySelectorAll("p,h2,h3,dd,a")].some((child) => {
              const b = child.getBoundingClientRect();
              return (
                b.bottom > bounds.bottom - 5 ||
                b.right > bounds.right - 5 ||
                b.left < bounds.left + 5
              );
            });
          })
          .map((e) => e.className);
        return {
          id: p.id,
          width: box.width,
          height: box.height,
          footerGap: +(footer.top - last.bottom).toFixed(2),
          footerInset: +(box.bottom - footer.bottom).toFixed(2),
          escaped,
          contentOverflow,
        };
      }),
    );
    const qa = path.join(root, "tmp/pdfs/html-square");
    fs.mkdirSync(qa, { recursive: true });
    for (let i = 0; i < 4; i++)
      await page
        .locator(".page")
        .nth(i)
        .screenshot({ path: path.join(qa, `browser-page-${i + 1}.png`) });
    if (
      errors.length ||
      checks.length !== 4 ||
      checks.some(
        (c) =>
          c.width !== 864 ||
          c.height !== 864 ||
          c.escaped.length ||
          c.contentOverflow.length ||
          c.footerGap < 8 ||
          c.footerInset < 23,
      )
    ) {
      throw new Error(JSON.stringify({ errors, checks }, null, 2));
    }
    await page.pdf({
      path: path.join(root, "output/pdf/maintenance-triage-html-brief.pdf"),
      preferCSSPageSize: true,
      printBackground: true,
      displayHeaderFooter: false,
      tagged: true,
    });
    console.log(
      JSON.stringify(
        { checks, output: "output/pdf/maintenance-triage-html-brief.pdf" },
        null,
        2,
      ),
    );
  } finally {
    await browser.close();
  }
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});

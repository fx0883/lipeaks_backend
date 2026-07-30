import { chromium } from "playwright";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const workspaceRoot = path.resolve(__dirname, "..");
const profileDir = path.join(workspaceRoot, ".playwright-profile", "wechat");
const loginUrl = "https://mp.weixin.qq.com/";
const defaultArticleUrl = "https://mp.weixin.qq.com/s/-ayS5eVVksg9ZGa7vyU8hQ";
const articleUrl = process.argv[2] || defaultArticleUrl;

const result = {
  url: articleUrl,
  read_num: null,
  like_num: null,
  old_like_num: null,
  share_num: null,
  sources: []
};

function isObject(value) {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function asNumber(value) {
  if (value === null || value === undefined || value === "") {
    return null;
  }

  if (typeof value === "number" && Number.isFinite(value)) {
    return value;
  }

  if (typeof value === "string") {
    const cleaned = value.replace(/[^\d.-]/g, "");
    if (!cleaned) {
      return null;
    }
    const parsed = Number(cleaned);
    return Number.isFinite(parsed) ? parsed : null;
  }

  return null;
}

function mergeStat(key, value, source) {
  const parsed = asNumber(value);
  if (parsed === null) {
    return;
  }

  // The article page often initializes these globals to empty-string math,
  // which becomes 0 even when no real stats were returned.
  if (parsed === 0 && source.startsWith("page.globals")) {
    return;
  }

  if (result[key] === null) {
    result[key] = parsed;
    result.sources.push(`${key}:${source}`);
  }
}

function walkForStats(node, source) {
  if (Array.isArray(node)) {
    for (const item of node) {
      walkForStats(item, source);
    }
    return;
  }

  if (!isObject(node)) {
    return;
  }

  const directMap = [
    ["read_num", ["read_num"]],
    ["like_num", ["like_num"]],
    ["old_like_num", ["old_like_num"]],
    ["share_num", ["share_num", "share_count", "forward_count"]]
  ];

  for (const [targetKey, candidateKeys] of directMap) {
    for (const candidate of candidateKeys) {
      if (candidate in node) {
        mergeStat(targetKey, node[candidate], `${source}.${candidate}`);
      }
    }
  }

  for (const [key, value] of Object.entries(node)) {
    if (key === "appmsgstat" && isObject(value)) {
      walkForStats(value, `${source}.appmsgstat`);
      continue;
    }
    if (isObject(value) || Array.isArray(value)) {
      walkForStats(value, `${source}.${key}`);
    }
  }
}

async function waitForManualLogin(page) {
  await page.goto(loginUrl, { waitUntil: "domcontentloaded" });
  console.log("Browser opened. If needed, complete WeChat QR login in the browser window.");
  console.log("Waiting for an authenticated mp.weixin.qq.com session...");

  const deadline = Date.now() + 5 * 60 * 1000;
  const authCookieNames = new Set([
    "token",
    "bizuin",
    "data_bizuin",
    "slave_sid",
    "slave_user"
  ]);

  while (Date.now() < deadline) {
    const currentUrl = page.url();
    const cookies = await page.context().cookies();
    const hasMpCookie = cookies.some((cookie) => {
      return cookie.domain.includes("mp.weixin.qq.com") && authCookieNames.has(cookie.name);
    });

    if (currentUrl.includes("/cgi-bin/") || hasMpCookie) {
      console.log("Login state looks usable. Continuing to article capture.");
      return;
    }

    await page.waitForTimeout(2000);
  }

  throw new Error("Timed out while waiting for login. Please rerun and complete QR login within 5 minutes.");
}

async function collectPageFallbacks(page) {
  const fallback = await page.evaluate(() => {
    const textBySelector = (selectors) => {
      for (const selector of selectors) {
        const node = document.querySelector(selector);
        const text = node?.textContent?.trim();
        if (text) {
          return text;
        }
      }
      return null;
    };

    const globals = {
      read_num: typeof window.read_num !== "undefined" ? window.read_num : null,
      like_num: typeof window.like_num !== "undefined" ? window.like_num : null,
      old_like_num: typeof window.old_like_num !== "undefined" ? window.old_like_num : null,
      share_num: typeof window.share_num !== "undefined" ? window.share_num : null
    };

    const dom = {
      read_num: textBySelector([
        "#js_temp_bar_read_num",
        "#js_read_area3",
        ".js_album_read_source",
        ".read-num"
      ]),
      like_num: textBySelector([
        "#likeNum",
        "#js_like_num",
        "#js_temp_bar_like_num",
        ".like_num"
      ]),
      old_like_num: textBySelector([
        "#js_old_like_num",
        "#old_like_num",
        ".old_like_num"
      ]),
      share_num: textBySelector([
        "#js_share_num",
        ".share_num"
      ])
    };

    return { globals, dom };
  });

  walkForStats(fallback.globals, "page.globals");
  walkForStats(fallback.dom, "page.dom");
}

async function main() {
  const context = await chromium.launchPersistentContext(profileDir, {
    headless: false,
    viewport: { width: 1280, height: 900 }
  });

  const page = context.pages()[0] || await context.newPage();

  page.on("response", async (response) => {
    const responseUrl = response.url();
    if (!responseUrl.includes("mp.weixin.qq.com")) {
      return;
    }

    try {
      const contentType = response.headers()["content-type"] || "";
      if (!contentType.includes("json")) {
        return;
      }

      const payload = await response.json();
      walkForStats(payload, `response:${responseUrl}`);
    } catch {
      // Ignore non-JSON and parse failures in this best-effort PoC.
    }
  });

  await waitForManualLogin(page);

  console.log(`Opening article: ${articleUrl}`);
  await page.goto(articleUrl, { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(12000);

  await collectPageFallbacks(page);

  console.log(JSON.stringify(result, null, 2));

  await context.close();
}

main().catch((error) => {
  console.error("[wechat-stats-poc] Failed:", error.message);
  process.exitCode = 1;
});

---
name: chrome-extension-creator
description: >
  Build Chrome extensions (Manifest V3) from scratch. Use this skill whenever the user wants to:
  create a Chrome extension, add features to a website via a browser extension, build a browser
  addon that modifies page behavior, add a toolbar button, intercept/modify network requests,
  inject scripts into web pages, scrape data from sites, automate browser tasks, build a side
  panel, or create a popup UI for any website. Trigger on any mention of "Chrome extension",
  "browser extension", "content script", "manifest.json", "popup", "inject script into page",
  "modify website", or "extension that does X on Y site". Always use this skill — do NOT build
  Chrome extensions without it.
---

# Chrome Extension Creator

Build Chrome extensions with Manifest V3 (the current, required standard). This skill generates
all files needed — manifest, service worker, content scripts, popup, and more — fully wired up
and ready to load.

---

## Workflow

1. **Understand the request** — identify the target site(s) and desired behavior
2. **Choose architecture** — use the decision guide below to select which components to include
3. **Generate all files** — write every file the extension needs; never leave stubs
4. **Explain installation** — always end with the "Loading the Extension" section

---

## Architecture Decision Guide

Pick the components that match what the extension needs to do. Most extensions combine 2–3.

| Component | Use when… | File |
|---|---|---|
| **Content script** | You need to read/modify the DOM of a web page | `content.js` |
| **Toolbar popup** | You want a UI when the user clicks the extension icon | `popup.html` + `popup.js` |
| **Service worker** | You need background processing, alarms, or to make API calls across tabs | `background.js` |
| **Side panel** | You want a persistent panel alongside the page (Chrome 114+) | `sidepanel.html` + `sidepanel.js` |
| **Options page** | You want settings the user can configure | `options.html` + `options.js` |
| **Context menu** | You want a right-click menu item | Registered in `background.js` |
| **DeclarativeNetRequest** | You want to block or redirect network requests without reading their content | JSON rules file |

**Common combinations:**
- **DOM enhancer**: content script only (e.g., dark mode, highlight keywords)
- **Scraper / data extractor**: content script + popup (trigger scrape from popup, return data)
- **Site automation**: content script + popup + storage
- **Request blocker/modifier**: declarativeNetRequest rules (no content script needed)
- **Cross-tab tool**: service worker + storage + popup

---

## Permissions Guide

Always request the minimum permissions needed. Broad permissions trigger scary install warnings.

| Permission | When to use |
|---|---|
| `"activeTab"` | Only need access to the current tab when the user clicks the extension icon. Best for popup-triggered actions. |
| `"scripting"` | Required to programmatically inject scripts (with `activeTab` or `host_permissions`) |
| `"storage"` | Persist settings or data with `chrome.storage.sync` / `chrome.storage.local` |
| `"tabs"` | Read tab URLs/titles. Requires host_permissions to read sensitive fields |
| `"contextMenus"` | Add right-click menu items |
| `"notifications"` | Show native browser notifications |
| `"alarms"` | Schedule repeating or delayed tasks in service worker |
| `"declarativeNetRequest"` | Block or redirect requests by rules |
| `"sidePanel"` | Display a side panel |

**`host_permissions`** — needed for:
- Content scripts that run automatically on a site
- `fetch()` calls to external origins from the service worker
- Reading tab URL/title programmatically

**Rule of thumb**: Use `"activeTab"` instead of `host_permissions` whenever the extension
only acts when the user clicks the icon. If it runs automatically on page load, declare
`host_permissions` with the specific domain.

---

## Standard File Structure

```
extension-name/
├── manifest.json         # Required — the heart of the extension
├── background.js         # Service worker (if needed)
├── content.js            # Content script (if needed)
├── popup.html            # Popup UI (if needed)
├── popup.js              # Popup logic (if needed)
├── popup.css             # Popup styles (if needed)
├── sidepanel.html        # Side panel (if needed)
├── sidepanel.js          # Side panel logic (if needed)
├── options.html          # Options page (if needed)
├── options.js            # Options logic (if needed)
└── icons/
    ├── icon16.png        # For favicon-size uses
    ├── icon48.png        # Extension list
    └── icon128.png       # Chrome Web Store
```

Only generate the files that the extension actually needs.

---

## Manifest V3 Template

```json
{
  "manifest_version": 3,
  "name": "Extension Name",
  "version": "1.0.0",
  "description": "What it does in one sentence (max 132 chars for Web Store)",
  "icons": {
    "16": "icons/icon16.png",
    "48": "icons/icon48.png",
    "128": "icons/icon128.png"
  },

  "permissions": ["storage", "activeTab", "scripting"],
  "host_permissions": ["https://example.com/*"],

  "background": {
    "service_worker": "background.js",
    "type": "module"
  },

  "action": {
    "default_popup": "popup.html",
    "default_icon": {
      "48": "icons/icon48.png"
    },
    "default_title": "Extension Name"
  },

  "content_scripts": [
    {
      "matches": ["https://example.com/*"],
      "js": ["content.js"],
      "run_at": "document_idle"
    }
  ],

  "side_panel": {
    "default_path": "sidepanel.html"
  },

  "options_ui": {
    "page": "options.html",
    "open_in_tab": false
  },

  "web_accessible_resources": [
    {
      "resources": ["icons/*"],
      "matches": ["https://example.com/*"]
    }
  ]
}
```

Remove any sections not needed. Only `manifest_version`, `name`, and `version` are required.

---

## Key MV3 Patterns

### Storage (persist data)
```javascript
// Save
await chrome.storage.sync.set({ theme: 'dark', enabled: true });

// Load
const { theme, enabled } = await chrome.storage.sync.get(['theme', 'enabled']);

// Listen for changes
chrome.storage.onChanged.addListener((changes, area) => {
  if (area === 'sync' && changes.enabled) {
    console.log('enabled changed to:', changes.enabled.newValue);
  }
});
```
Use `chrome.storage.sync` for settings (syncs across user's Chrome installs, 100KB limit).
Use `chrome.storage.local` for larger local data (unlimited, stays on device).

### Content script → Service worker messaging
```javascript
// content.js — send message to background
const response = await chrome.runtime.sendMessage({ type: 'FETCH_DATA', url: 'https://api.example.com/data' });
console.log(response.data);

// background.js — receive and handle
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'FETCH_DATA') {
    fetch(message.url)
      .then(r => r.json())
      .then(data => sendResponse({ ok: true, data }))
      .catch(err => sendResponse({ ok: false, error: err.message }));
    return true; // IMPORTANT: return true for async sendResponse
  }
});
```

### Popup → Content script messaging
```javascript
// popup.js — send to content script of active tab
const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
const response = await chrome.tabs.sendMessage(tab.id, { type: 'GET_PAGE_DATA' });

// content.js — receive from popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'GET_PAGE_DATA') {
    sendResponse({ title: document.title, url: location.href });
  }
});
```

### Programmatic script injection (via service worker or popup)
```javascript
// Inject a content script on demand (requires activeTab or host_permissions + scripting)
const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
await chrome.scripting.executeScript({
  target: { tabId: tab.id },
  files: ['content.js']
});

// Or run an inline function
await chrome.scripting.executeScript({
  target: { tabId: tab.id },
  func: (color) => { document.body.style.backgroundColor = color; },
  args: ['yellow']
});
```

### Context menus
```javascript
// background.js — register menu (use chrome.runtime.onInstalled to avoid duplicates)
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: 'saveSelection',
    title: 'Save "%s" to extension',
    contexts: ['selection']
  });
});

chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === 'saveSelection') {
    const selected = info.selectionText;
    chrome.storage.local.get(['saved'], ({ saved = [] }) => {
      chrome.storage.local.set({ saved: [...saved, selected] });
    });
  }
});
```

### Service worker: keep-alive for long tasks
Service workers terminate when idle. Store state in `chrome.storage`, not global variables.
```javascript
// background.js — DON'T do this (variable lost when worker sleeps):
let counter = 0; // ❌ lost after service worker terminates

// DO this instead:
async function incrementCounter() {
  const { counter = 0 } = await chrome.storage.local.get('counter');
  await chrome.storage.local.set({ counter: counter + 1 });
}
```

---

## MV3 Gotchas (Common Mistakes)

| ❌ MV2 / Wrong | ✅ MV3 / Correct |
|---|---|
| `background: { scripts: [...], persistent: true }` | `background: { service_worker: "background.js" }` |
| `chrome.browserAction` / `chrome.pageAction` | `chrome.action` |
| `eval()` or inline scripts in HTML | External `.js` files only; no `eval()` |
| Remote code execution (fetching + running JS) | Bundle all code in the extension package |
| `chrome.webRequest` for blocking | `chrome.declarativeNetRequest` with rule JSON files |
| Global variables for persistent state | `chrome.storage` for all persistent state |
| `XMLHttpRequest` in service worker | `fetch()` in service worker |

---

## Security Checklist

Generate code that follows these rules — do not skip any:

- **Least privilege**: Only declare permissions that are actually used
- **No `eval()`**: Use `JSON.parse()` for data; use `textContent` / `innerText` not `innerHTML` for untrusted content
- **Validate messages**: Always check `message.type` and expected fields before acting on messages
- **No remote code**: Do not fetch and execute external JavaScript at runtime
- **Sanitize DOM insertions**: Never insert untrusted data with `innerHTML` — use `textContent` or create DOM nodes
- **Verify message senders**: In service worker, check `sender.origin` or `sender.id` for cross-extension/page messages
- **HTTPS only**: All `host_permissions` and `fetch()` calls should use `https://`
- **Scope content scripts tightly**: Use specific URL patterns, not `<all_urls>`, unless truly needed

---

## Loading the Extension (Always Include This)

Always end your response with these instructions when generating a new extension:

```
## How to install and test

1. Open Chrome and navigate to `chrome://extensions`
2. Enable **Developer mode** (toggle in the top-right corner)
3. Click **Load unpacked**
4. Select the `extension-name/` folder you just created
5. The extension icon appears in your toolbar (you may need to pin it via the puzzle piece icon)

To reload after making changes:
- Click the refresh icon (↺) next to the extension on `chrome://extensions`

To view errors and console logs:
- Service worker: click "Service Worker" link on the extension card in `chrome://extensions`
- Content script / popup: right-click the page or popup → Inspect
```

---

## Reference Files

For more detail, read these as needed:

| File | Contents |
|---|---|
| [references/manifest-examples.md](references/manifest-examples.md) | Complete manifest.json files for 6 common extension types |
| [references/api-patterns.md](references/api-patterns.md) | Full code patterns: alarms, declarativeNetRequest, side panel, options page, fetch with auth, MutationObserver in content scripts |

---

## Icon Generation Note

If the user asks about icons, they need PNG files. For quick testing, any 128×128 PNG will work.
Direct the user to use a simple placeholder or generate SVG with:
- 128×128 for web store / install
- 48×48 for extension management page
- 16×16 for favicon-level use

Real icons can be created with any image editor or a tool like https://favicon.io/favicon-generator/

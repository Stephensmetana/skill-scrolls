# Manifest Examples for Common Chrome Extension Types

Complete, ready-to-use `manifest.json` files for the most common extension patterns.

---

## 1. DOM Enhancer (Content Script Only)

Automatically runs on specific pages and modifies the DOM. No popup, no service worker.

```json
{
  "manifest_version": 3,
  "name": "Page Enhancer",
  "version": "1.0.0",
  "description": "Enhances pages on example.com",
  "icons": {
    "48": "icons/icon48.png",
    "128": "icons/icon128.png"
  },
  "content_scripts": [
    {
      "matches": ["https://example.com/*", "https://www.example.com/*"],
      "js": ["content.js"],
      "css": ["content.css"],
      "run_at": "document_idle"
    }
  ]
}
```

**Files needed**: `manifest.json`, `content.js`, `content.css` (optional), `icons/`

**No permissions needed** — content scripts don't require `permissions` entries unless they use
Chrome APIs (like `chrome.storage`).

---

## 2. Popup Tool (Click-to-Act on Active Tab)

User clicks the extension icon → popup appears → user triggers an action on the current page.

```json
{
  "manifest_version": 3,
  "name": "Page Tool",
  "version": "1.0.0",
  "description": "Acts on the current page when you click the icon",
  "icons": {
    "16": "icons/icon16.png",
    "48": "icons/icon48.png",
    "128": "icons/icon128.png"
  },
  "permissions": ["activeTab", "scripting", "storage"],
  "action": {
    "default_popup": "popup.html",
    "default_icon": { "48": "icons/icon48.png" },
    "default_title": "Page Tool"
  }
}
```

**Files needed**: `manifest.json`, `popup.html`, `popup.js`, `popup.css`, `icons/`

**Note**: `activeTab` grants temporary access to the current tab only when the user clicks the icon.
No persistent host permissions needed. Use `chrome.scripting.executeScript()` from popup.js.

---

## 3. Popup + Persistent Content Script

Automatically enhances pages AND has a popup for settings/controls.

```json
{
  "manifest_version": 3,
  "name": "Site Assistant",
  "version": "1.0.0",
  "description": "Enhances your experience on example.com",
  "icons": {
    "16": "icons/icon16.png",
    "48": "icons/icon48.png",
    "128": "icons/icon128.png"
  },
  "permissions": ["storage"],
  "host_permissions": ["https://example.com/*"],
  "action": {
    "default_popup": "popup.html",
    "default_icon": { "48": "icons/icon48.png" }
  },
  "content_scripts": [
    {
      "matches": ["https://example.com/*"],
      "js": ["content.js"],
      "run_at": "document_idle"
    }
  ]
}
```

---

## 4. Full Extension (Popup + Content Script + Service Worker)

Most capable pattern. Service worker handles API calls and events; content script reads/modifies
the page; popup triggers actions and shows results.

```json
{
  "manifest_version": 3,
  "name": "Full Extension",
  "version": "1.0.0",
  "description": "Full-featured extension",
  "icons": {
    "16": "icons/icon16.png",
    "48": "icons/icon48.png",
    "128": "icons/icon128.png"
  },
  "permissions": ["storage", "activeTab", "scripting", "contextMenus"],
  "host_permissions": [
    "https://example.com/*",
    "https://api.example.com/*"
  ],
  "background": {
    "service_worker": "background.js",
    "type": "module"
  },
  "action": {
    "default_popup": "popup.html",
    "default_icon": { "48": "icons/icon48.png" }
  },
  "content_scripts": [
    {
      "matches": ["https://example.com/*"],
      "js": ["content.js"],
      "run_at": "document_idle"
    }
  ],
  "options_ui": {
    "page": "options.html",
    "open_in_tab": false
  }
}
```

---

## 5. Request Blocker / Ad Filter

Blocks or redirects network requests using declarative rules (no content script needed).

```json
{
  "manifest_version": 3,
  "name": "Request Filter",
  "version": "1.0.0",
  "description": "Blocks tracking requests",
  "icons": {
    "48": "icons/icon48.png",
    "128": "icons/icon128.png"
  },
  "permissions": ["declarativeNetRequest"],
  "declarative_net_request": {
    "rule_resources": [
      {
        "id": "block_rules",
        "enabled": true,
        "path": "rules/block_rules.json"
      }
    ]
  }
}
```

**`rules/block_rules.json`** example:
```json
[
  {
    "id": 1,
    "priority": 1,
    "action": { "type": "block" },
    "condition": {
      "urlFilter": "||tracking.example.com^",
      "resourceTypes": ["script", "image", "xmlhttprequest"]
    }
  },
  {
    "id": 2,
    "priority": 1,
    "action": { "type": "redirect", "redirect": { "url": "https://safe.example.com/pixel.gif" } },
    "condition": {
      "urlFilter": "||ads.example.com/pixel*",
      "resourceTypes": ["image"]
    }
  }
]
```

---

## 6. Side Panel Extension (Chrome 114+)

Displays a persistent panel alongside the browser content.

```json
{
  "manifest_version": 3,
  "name": "Side Panel Helper",
  "version": "1.0.0",
  "description": "Adds a persistent side panel",
  "icons": {
    "48": "icons/icon48.png",
    "128": "icons/icon128.png"
  },
  "permissions": ["storage", "sidePanel", "activeTab"],
  "action": {
    "default_title": "Open Side Panel"
  },
  "side_panel": {
    "default_path": "sidepanel.html"
  },
  "background": {
    "service_worker": "background.js"
  }
}
```

**`background.js`** — open the side panel when user clicks the action icon:
```javascript
chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true }).catch(console.error);
```

---

## Match Pattern Reference

| Pattern | Matches |
|---|---|
| `https://example.com/*` | All pages on example.com (HTTPS only) |
| `https://*.example.com/*` | All subdomains of example.com |
| `*://example.com/*` | HTTP and HTTPS on example.com |
| `https://example.com/path/*` | Only pages under /path/ |
| `<all_urls>` | All URLs — avoid unless truly needed (triggers permission warning) |

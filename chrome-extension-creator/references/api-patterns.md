# Chrome Extension API Patterns

Common patterns and full code samples for Chrome Extension development with Manifest V3.

---

## Popup HTML Boilerplate

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="stylesheet" href="popup.css">
  <title>Extension</title>
</head>
<body>
  <div id="app">
    <h1>My Extension</h1>
    <button id="actionBtn">Do Something</button>
    <div id="status"></div>
  </div>
  <script src="popup.js"></script>
</body>
</html>
```

**popup.css** — keep popups compact (Chrome clips at 600×600):
```css
body {
  width: 320px;
  min-height: 120px;
  margin: 0;
  padding: 12px 16px;
  font-family: system-ui, -apple-system, sans-serif;
  font-size: 14px;
}
button {
  padding: 8px 16px;
  border-radius: 4px;
  border: none;
  background: #1a73e8;
  color: white;
  cursor: pointer;
  font-size: 14px;
}
button:hover { background: #1557b0; }
```

---

## Popup: Trigger Action on Active Tab

```javascript
// popup.js
document.getElementById('actionBtn').addEventListener('click', async () => {
  const status = document.getElementById('status');
  status.textContent = 'Working...';

  try {
    // Get the current active tab
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

    // Option A: Inject and run a function directly
    const results = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: () => {
        // This runs in the page context
        return { title: document.title, count: document.links.length };
      }
    });
    const data = results[0].result;
    status.textContent = `Found ${data.count} links on: ${data.title}`;

    // Option B: Send a message to a content script already on the page
    // const response = await chrome.tabs.sendMessage(tab.id, { type: 'GET_DATA' });
    // status.textContent = response.result;

  } catch (err) {
    status.textContent = `Error: ${err.message}`;
  }
});
```

---

## Content Script: Observe DOM Changes (MutationObserver)

Use this when a site loads content dynamically (React/Vue apps, infinite scroll, etc.).

```javascript
// content.js
function processElement(el) {
  // Do something with newly added elements
  if (el.classList.contains('target-class')) {
    el.style.outline = '2px solid red';
  }
}

// Process elements already on the page
document.querySelectorAll('.target-class').forEach(processElement);

// Watch for new elements added dynamically
const observer = new MutationObserver((mutations) => {
  for (const mutation of mutations) {
    for (const node of mutation.addedNodes) {
      if (node.nodeType !== Node.ELEMENT_NODE) continue;
      if (node.matches?.('.target-class')) processElement(node);
      node.querySelectorAll?.('.target-class').forEach(processElement);
    }
  }
});

observer.observe(document.body, { childList: true, subtree: true });
```

---

## Content Script: Inject a UI Panel into the Page

```javascript
// content.js — inject a floating UI panel
function createPanel() {
  // Avoid duplicates
  if (document.getElementById('my-ext-panel')) return;

  const panel = document.createElement('div');
  panel.id = 'my-ext-panel';
  panel.style.cssText = `
    position: fixed;
    bottom: 20px;
    right: 20px;
    width: 300px;
    background: white;
    border: 1px solid #ddd;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    padding: 16px;
    z-index: 2147483647;
    font-family: system-ui, sans-serif;
    font-size: 14px;
  `;

  // Use textContent for untrusted data — never innerHTML
  const title = document.createElement('h3');
  title.textContent = 'My Extension';
  title.style.margin = '0 0 8px 0';
  panel.appendChild(title);

  const closeBtn = document.createElement('button');
  closeBtn.textContent = '×';
  closeBtn.style.cssText = 'position:absolute;top:8px;right:8px;border:none;background:none;cursor:pointer;font-size:18px;';
  closeBtn.addEventListener('click', () => panel.remove());
  panel.appendChild(closeBtn);

  document.body.appendChild(panel);
}

createPanel();
```

---

## Service Worker: Alarms (Repeating Tasks)

Alarms survive service worker restarts. Perfect for polling or periodic cleanup.

```javascript
// background.js
chrome.runtime.onInstalled.addListener(() => {
  // Create alarm — fires every 30 minutes
  chrome.alarms.create('periodic-check', { periodInMinutes: 30 });
});

chrome.alarms.onAlarm.addListener(async (alarm) => {
  if (alarm.name === 'periodic-check') {
    console.log('Alarm fired:', new Date().toISOString());
    await doPeriodicWork();
  }
});

async function doPeriodicWork() {
  const { lastRun } = await chrome.storage.local.get('lastRun');
  // ... do work ...
  await chrome.storage.local.set({ lastRun: Date.now() });
}
```

Manifest needs `"alarms"` in permissions:
```json
"permissions": ["storage", "alarms"]
```

---

## Service Worker: Fetch with Auth Headers

Make authenticated API calls from the service worker (not from content scripts, to avoid CORS).

```javascript
// background.js
async function fetchWithAuth(url, options = {}) {
  const { apiKey } = await chrome.storage.sync.get('apiKey');
  if (!apiKey) throw new Error('No API key configured. Open extension settings.');

  const response = await fetch(url, {
    ...options,
    headers: {
      'Authorization': `Bearer ${apiKey}`,
      'Content-Type': 'application/json',
      ...options.headers
    }
  });

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  }
  return response.json();
}

// Handle messages from content script or popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'API_CALL') {
    fetchWithAuth(message.url, { method: message.method || 'GET', body: message.body ? JSON.stringify(message.body) : undefined })
      .then(data => sendResponse({ ok: true, data }))
      .catch(err => sendResponse({ ok: false, error: err.message }));
    return true; // async response
  }
});
```

---

## Options Page

```html
<!-- options.html -->
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <link rel="stylesheet" href="options.css">
  <title>Extension Settings</title>
</head>
<body>
  <h1>Settings</h1>
  <form id="settingsForm">
    <label>
      API Key
      <input type="password" id="apiKey" placeholder="Enter your API key">
    </label>
    <label>
      <input type="checkbox" id="enabled"> Enable extension
    </label>
    <button type="submit">Save</button>
    <span id="status"></span>
  </form>
  <script src="options.js"></script>
</body>
</html>
```

```javascript
// options.js
const form = document.getElementById('settingsForm');
const status = document.getElementById('status');

// Load existing settings
chrome.storage.sync.get(['apiKey', 'enabled'], ({ apiKey = '', enabled = true }) => {
  document.getElementById('apiKey').value = apiKey;
  document.getElementById('enabled').checked = enabled;
});

// Save settings
form.addEventListener('submit', async (e) => {
  e.preventDefault();
  const apiKey = document.getElementById('apiKey').value.trim();
  const enabled = document.getElementById('enabled').checked;

  await chrome.storage.sync.set({ apiKey, enabled });
  status.textContent = 'Saved!';
  setTimeout(() => { status.textContent = ''; }, 2000);
});
```

---

## Badge Count (Service Worker)

```javascript
// background.js — update badge when count changes
async function updateBadge(count) {
  const text = count > 0 ? String(count) : '';
  await chrome.action.setBadgeText({ text });
  await chrome.action.setBadgeBackgroundColor({ color: '#e53935' });
}

// Example: show unread count
chrome.alarms.onAlarm.addListener(async (alarm) => {
  if (alarm.name === 'check-unread') {
    const data = await fetchWithAuth('https://api.example.com/unread');
    updateBadge(data.count);
  }
});
```

---

## Page-Level Communication (window.postMessage)

When content script isolation prevents direct DOM event access, use `postMessage` to bridge
the page and the content script.

```javascript
// injected-into-page.js (injected via web_accessible_resources)
window.addEventListener('message', (event) => {
  if (event.source !== window || !event.data?.type?.startsWith('EXT_')) return;
  // Handle message from page
});

// Send data to the page:
window.postMessage({ type: 'EXT_RESULT', payload: { value: 42 } }, '*');
```

```javascript
// content.js — bridge between page and extension
window.addEventListener('message', (event) => {
  if (event.source !== window || !event.data?.type) return;
  // Forward page messages to service worker
  if (event.data.type === 'PAGE_TO_EXT') {
    chrome.runtime.sendMessage(event.data.payload);
  }
});
```

---

## Dynamic Content Script Registration

Register content scripts at runtime (useful when the user configures which sites to run on).

```javascript
// background.js or popup.js
async function registerContentScript(domain) {
  await chrome.scripting.registerContentScripts([{
    id: `script-${domain}`,
    matches: [`https://${domain}/*`],
    js: ['content.js'],
    runAt: 'document_idle',
    persistAcrossSessions: true
  }]);
}

async function unregisterContentScript(domain) {
  await chrome.scripting.unregisterContentScripts({ ids: [`script-${domain}`] });
}

async function getRegisteredScripts() {
  return chrome.scripting.getRegisteredContentScripts();
}
```

Manifest needs `"scripting"` permission and `"host_permissions"` for the target domains.

---

## Tab Event Listeners

```javascript
// background.js
// When user navigates to a new URL
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === 'complete' && tab.url?.startsWith('https://example.com/')) {
    // Tab finished loading on example.com
    chrome.tabs.sendMessage(tabId, { type: 'TAB_READY', url: tab.url });
  }
});

// When user switches tabs
chrome.tabs.onActivated.addListener(async ({ tabId }) => {
  const tab = await chrome.tabs.get(tabId);
  console.log('Active tab:', tab.url);
});
```

Requires `"tabs"` permission + `host_permissions` to read `tab.url`.

"""Global website zoom for NOMIKO, including split panes.

Normal zoom uses Qt WebEngine's native page zoom. Text-only zoom is a
best-effort DOM font-size transform; it cannot override every site's custom
canvas, closed shadow DOM or inaccessible content. Internal pages are excluded.
"""
from __future__ import annotations

from PySide6.QtWebEngineCore import QWebEngineScript

ZOOM_LEVELS = (50, 67, 75, 80, 90, 100, 110, 120, 125, 133, 150, 170, 175, 200, 250, 300)
SCRIPT_NAME = "NOMIKO global text-only zoom"
WORLD_ID = 1  # Qt WebEngine ApplicationWorld, isolated from page JavaScript.


def zoom_percent(settings) -> int:
    """Get a safe, supported percentage; older profiles default to 100%."""
    try:
        value = int(settings.get("default_zoom", 100))
    except (ValueError, TypeError):
        return 100
    return value if value in ZOOM_LEVELS else 100


def zoom_text_only(settings) -> bool:
    return settings.get("zoom_text_only", False) is True


def text_zoom_javascript(percent=100, enabled=False) -> str:
    """Idempotent per-document font scaling, preserving original inline styles."""
    percent = int(percent)
    if percent < 50 or percent > 300:
        percent = 100
    mode = "true" if enabled and percent != 100 else "false"
    return StringTemplate.replace("__PERCENT__", str(percent)).replace("__ENABLED__", mode)


StringTemplate = r"""
(function () {
  "use strict";
  if (location.protocol !== "http:" && location.protocol !== "https:") return;
  const percent = __PERCENT__, enabled = __ENABLED__;
  const state = window.__NOMIKO_TEXT_ZOOM__ || (window.__NOMIKO_TEXT_ZOOM__ = {
    elements: new Map(), observer: null
  });
  if (state.observer) { state.observer.disconnect(); state.observer = null; }
  for (const [element, saved] of state.elements) {
    if (!element || !element.style) continue;
    if (saved.inline) element.style.setProperty("font-size", saved.inline, saved.priority);
    else element.style.removeProperty("font-size");
  }
  state.elements.clear();
  if (!enabled) return;

  const exclusions = new Set(["SCRIPT", "STYLE", "NOSCRIPT", "SVG", "HEAD", "META", "LINK"]);
  const controls = new Set(["INPUT", "TEXTAREA", "SELECT", "BUTTON", "OPTION"]);
  function adjust(element) {
    if (!(element instanceof Element) || exclusions.has(element.tagName)) return;
    if (element.closest("svg, math, script, style, noscript")) return;
    let hasText = controls.has(element.tagName);
    if (!hasText) {
      for (const child of element.childNodes) {
        if (child.nodeType === Node.TEXT_NODE && child.textContent.trim()) {
          hasText = true; break;
        }
      }
    }
    if (!hasText || state.elements.has(element)) return;
    const css = window.getComputedStyle(element);
    const base = Number.parseFloat(css.fontSize);
    if (!Number.isFinite(base) || base <= 0) return;
    state.elements.set(element, {
      inline: element.style.getPropertyValue("font-size"),
      priority: element.style.getPropertyPriority("font-size")
    });
    element.style.setProperty("font-size", (base * percent / 100).toFixed(2) + "px", "important");
  }
  function traverse(node) {
    if (!node || node.nodeType !== Node.ELEMENT_NODE) return;
    adjust(node);
    const walker = document.createTreeWalker(node, NodeFilter.SHOW_ELEMENT);
    while (walker.nextNode()) adjust(walker.currentNode);
  }
  function begin() {
    if (!document.body) return;
    traverse(document.body);
    state.observer = new MutationObserver(mutations => {
      for (const mutation of mutations)
        for (const node of mutation.addedNodes) traverse(node);
    });
    state.observer.observe(document.body, {childList: true, subtree: true});
  }
  if (document.body) begin();
  else document.addEventListener("DOMContentLoaded", begin, {once: true});
})();
"""


def configure_zoom_script(profile, settings):
    """Make text-only zoom persistent for future navigations and subframes."""
    scripts = profile.scripts()
    existing = scripts.findScript(SCRIPT_NAME)
    if not existing.isNull():
        scripts.remove(existing)
    if not zoom_text_only(settings) or zoom_percent(settings) == 100:
        return
    script = QWebEngineScript()
    script.setName(SCRIPT_NAME)
    script.setWorldId(WORLD_ID)
    script.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentReady)
    script.setRunsOnSubFrames(True)
    script.setSourceCode(text_zoom_javascript(zoom_percent(settings), enabled=True))
    scripts.insert(script)


def apply_zoom_to_view(view, settings):
    """Apply immediately to an existing page, without reloading it."""
    percent = zoom_percent(settings)
    text_only = zoom_text_only(settings)
    view.setZoomFactor(1.0 if text_only else percent / 100.0)
    page = view.page()
    if page is not None:
        page.runJavaScript(text_zoom_javascript(percent, enabled=text_only), WORLD_ID)

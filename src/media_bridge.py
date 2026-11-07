"""Small, site-scoped media fallback integration for Chromium Qt WebEngine.

No tracking, no cookies, no external browsing engine. User must click the
fallback link; normal working HTML5 playback is never intercepted.
"""
from __future__ import annotations


JS = r"""(() => {
  if (window.__nomikoNativeMediaInstalled) return;
  window.__nomikoNativeMediaInstalled = true;
  const isSC = /(^|\.)soundcloud\.com$/i.test(location.hostname);
  function nav(source, kind) {
    return 'https://nomiko.invalid/media?type=' + encodeURIComponent(kind)
      + '&url=' + encodeURIComponent(source);
  }
  function valid(url) {
    try { const u = new URL(url, location.href);
      return u.protocol === 'https:' && !u.username && !u.password ? u.href : '';
    } catch (_) {return '';}
  }
  function trackLink(row) {
    if (!row) return '';
    const links = row.querySelectorAll('a.soundTitle__title[href], a[href]');
    for (const a of links) {
      const raw = valid(a.href);
      if (!raw) continue;
      try {const u = new URL(raw);
        const parts = u.pathname.split('/').filter(Boolean);
        if ((u.hostname === 'soundcloud.com' || u.hostname.endsWith('.soundcloud.com'))
            && parts.length === 2 && !['you','discover','sets','search','settings'].includes(parts[0])
            && !['sets','albums','likes','tracks','reposts'].includes(parts[1])) return u.origin + u.pathname;
      } catch (_) {}
    }
    return '';
  }
  function makeLink(href, text) {
    const a = document.createElement('a');
    a.href = href;
    a.textContent = text;
    a.rel = 'nofollow';
    a.style.cssText = 'display:inline-block;position:relative;z-index:2147483646;'
      +'font:600 12px Segoe UI,Arial,sans-serif;text-decoration:none;'
      +'border-radius:8px;background:#9783ec;color:#11131b;'
      +'padding:7px 11px;margin:6px 2px;cursor:pointer';
    return a;
  }
  function supportFallback(media) {
    const src = valid(media.currentSrc || media.src);
    if (!src || media.dataset.nomikoFallback) return;
    media.dataset.nomikoFallback = '1';
    const holder = media.parentElement;
    if (!holder) return;
    const link = makeLink(nav(src, 'direct'), '▶ Play with NOMIKO');
    link.title = 'Qt Multimedia / FFmpeg — useful when H.264/MP3 is not decoded by Chromium';
    holder.appendChild(link);
  }
  // Chromium's missing codecs cause MEDIA_ERR_SRC_NOT_SUPPORTED on <video>.
  document.addEventListener('error', e => {
    if (e.target instanceof HTMLMediaElement && e.target.error) supportFallback(e.target);
  }, true);
  // Fortnite.GG has public H.264 MP4 previews. Offer a manual native
  // fallback even if the Chromium video canvas stays gray without an error.
  if (location.hostname === 'fortnite.gg' || location.hostname === 'www.fortnite.gg') {
    let queued = false;
    const scan = () => {
      queued = false;
      for (const media of document.querySelectorAll('video')) supportFallback(media);
    };
    const schedule = () => {
      if (queued) return;
      queued = true;
      setTimeout(scan, 350);
    };
    new MutationObserver(schedule).observe(document, {subtree:true,childList:true});
    schedule();
  }
  // SoundCloud Likes: an explicit public-track player beside each track.
  // Private tracks / authenticated DRM are never extracted or bypassed.
  if (isSC) {
    let pending = false;
    function decorate() {
      pending = false;
      if (!/(^|\/)likes(\/|$)/.test(location.pathname)) return;
      for (const row of document.querySelectorAll('.soundList__item,.soundBadge')) {
        if (row.dataset.nomikoNativeMedia) continue;
        const href = trackLink(row);
        if (!href) continue;
        row.dataset.nomikoNativeMedia = '1';
        const link = makeLink(nav(href, 'soundcloud'), '▶ Play in NOMIKO');
        link.title = 'Public SoundCloud track via Qt Multimedia (no Microsoft browser)';
        const host = row.querySelector('.soundActions,.soundBadge__actions,.soundTitle') || row;
        host.appendChild(link);
      }
    }
    const schedule = () => {
      if (pending) return;
      pending = true;
      setTimeout(decorate, 450);
    };
    new MutationObserver(schedule).observe(document, {subtree:true,childList:true});
    schedule();
  }
})()""";


def install_media_script(profile):
    from PySide6.QtWebEngineCore import QWebEngineScript
    script = QWebEngineScript()
    script.setName('NOMIKO native media fallback')
    script.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentReady)
    script.setRunsOnSubFrames(False)
    script.setWorldId(QWebEngineScript.ScriptWorldId.MainWorld)
    script.setSourceCode(JS)
    profile.scripts().insert(script)

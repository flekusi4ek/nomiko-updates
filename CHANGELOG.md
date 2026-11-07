# NOMIKO changelog

## v0.9.16 Stable
- Add Qt Multimedia / FFmpeg native player for public HTTPS audio and video streams unsupported by Qt WebEngine. No Edge, WebView2 or third-party browser.
- Add clickable fallback beside failed HTML5 video and Fortnite.GG item-preview videos with HTTPS sources, plus a right-click video action.
- Add "Play in NOMIKO" beside public SoundCloud Likes tracks. Resolve public stream URLs without copying user cookies or bypassing DRM; private/restricted songs may still be unavailable.
- Validate media URLs and reject local/private-network destinations. Keep media extraction off the main UI thread.
- Package Qt Multimedia, FFmpeg backend and yt-dlp with Windows tests; preserve profile and update mechanism.


## v0.9.16 Stable
- Add a separate attractive NOMIKO updater window after the browser closes, with dark styling, purple accents, animated activity indicator and honest install phases.
- Replace the second native setup wizard during in-app updates with one always-visible progress window. No fake percentage while NSIS is extracting.
- Show installation success, error messages and an **Open NOMIKO** button; preserve the original install directory, bookmarks, cookies and settings.
- Preserve signed-update verification, checksum re-verification, safe process shutdown and rollback behavior. Headless updater mode remains available for CI.
- Add a real Windows smoke test for the packaged, independent Tk/Tcl updater UI and keep the custom-install-path upgrade test.


## v0.9.16 Stable
- Restore Qt's accelerated WebEngine rendering by default. The prior software-only default could overload older CPUs. Compatibility software mode remains manually selectable.
- Migrate the previous software-only default once, while keeping the graphics setting reversible in Performance settings. Restart required for graphics changes.
- Freeze only quiet, hidden, unpinned background tabs after a configurable idle delay and only when Qt's recommended lifecycle state allows it. Preserve music and calls, keep documents alive and resume without discarding or reloading.
- Stop needless session file rewrites and debounce frequent tab resize/session events.
- Remove unreliable cloud-runner real-website probes from stable-release CI. Keep offline first-frame, installed-EXE and original-folder update tests.


## v0.9.13 Stable
- Fix the in-app Exit & Install flow by starting and validating an independent updater before closing browser windows.
- Install into the original NOMIKO folder, even when it contains spaces or was chosen outside the default location. Preserve pinned shortcuts and installed version.
- Show NSIS installer and actionable errors instead of silently failing in background; log updater status to %LOCALAPPDATA%\\NOMIKO\\updates\\last-update-status.txt.
- Keep Ed25519 manifest verification plus SHA-256 checks before executing a downloaded installer.
- Add end-to-end Windows CI helper smoke test, including a custom installation directory.


## v0.9.12 Stable
- First non-prerelease Stable-channel update, signed using the existing Ed25519 update key and installable from older Alpha releases.
- Windows rendering defaults to Qt WebEngine's documented GPU-disabled Compatibility mode to mitigate black pages and driver-dependent flickering.
- Performance settings expose a restart-required Hardware mode for faster graphics on machines without rendering glitches.
- New and reactivated tabs request a first frame and compositor repaint automatically, instead of requiring a mouse click. No automatic discard/reload of healthy tabs.
- A terminated Chromium renderer is recovered once with a bounded retry, with a visible warning on repeated crashes.
- Windows CI adds an interactive Qt WebEngine home/new tab/tab-switch rendering smoke test before publication.
- Installer preserves the existing profile, cookies, tabs and signed update checks. Some site-specific graphics failures may remain until tested on affected devices.


## v0.9.11 Alpha
- Added a non-modal SoundCloud playback help dialog, shown only on SoundCloud pages, with local media format/error diagnostics.
- Added a reversible SoundCloud-only ad/tracker filter exception with explicit consent; other sites remain protected.
- Diagnose only aggregated blocked-request counts; do not collect track URLs, login information or cookies.
- Retained safe Windows upgrades, signed updates, and adaptive tabs.


## v0.9.10 Alpha
- Prevent DLL sharing violations during upgrades by staging a complete app copy and replacing the install directory only after extraction completes.
- If replacing the application directory fails (files still in use), abort safely without overwriting individual Qt binaries; restore the old directory if a final swap fails.
- Keep the prior installed version in an adjacent rollback folder until the next successful installer run; user profile data stays at %APPDATA%\\NOMIKO.
- The update helper now waits for both NOMIKO.exe and QtWebEngineProcess.exe from the installed folder to exit before installing; writes a short local status message if an update is postponed.
- Test Qt WebEngine native DLL imports in both packaged and NSIS-installed Windows builds before publishing a release.
- Preserve existing SoundCloud and adaptive-tab changes.


## v0.9.9 Alpha
- Horizontally arranged tabs now shrink evenly as more tabs open; the New Tab button remains accessible, with scroll as a fallback at the minimum width.
- SoundCloud pages (including embedded players) receive a narrowly scoped autoplay compatibility exception; other websites keep their normal user-gesture setting.
- Warn in the status bar if Qt WebEngine's bundled media codecs do not include MP3/AAC, which requires a codec-capable engine build to fix fully.
- Sidebar tabs, privacy protections, themes and signed updates are unchanged.


## v0.9.8 Alpha
- Reduced only the left navigation icon buttons to consistent 28×28 px hitboxes and centered their glyphs.
- Centered the search/address field against the full browser window instead of free toolbar space, with overlap protection.
- All right-side bookmark/menu/window-control buttons remain unchanged from v0.9.7.
- Kept all other browser features, preferences and signed in-app updates unchanged.


## v0.9.7 Alpha
- Fixed Windows controls accidentally placed on the left in v0.9.6.
- Standard far-right order: Minimize / Maximize / Close.
- All three buttons have equal 36×32 px hit targets; icons are truly centered vertically and horizontally.
- Bookmark and three-line menu remain immediately to the left of the window buttons, with no large gap.
- A flexible draggable area occupies remaining toolbar space without pushing window buttons away.
- Preserves theme-colored startup canvas, settings, tabs and signed in-app updates.


## v0.9.6 Alpha
- Far-left window controls: Close 32px, Maximize 26px, Minimize 23px.
- Bookmark and Menu buttons grouped directly next to Minimize.
- Theme-colored native window and WebEngine canvases before first paint; avoids white flashes on opening new windows/tabs.
- Split views and private windows also start using the chosen theme color.
- Updated the release owner after the developer account rename.


## v0.9.5 Alpha
- Registered NOMIKO in Windows 11 Default Apps for HTTP, HTTPS, HTML and HTM.
- Compact minimalist top navigation, shorter adjustable address bar and thinner horizontal tabs.
- Simplified three-line main menu with useful secondary tools in a submenu.
- Per-session download icon: hidden until first download; persistent download history remains in Settings.
- Redesigned settings with left navigation and cross-section search.
- More working controls: local profile folder, downloads folder/history actions and default browser selection.
- Core settings labels translated into Ukrainian, Russian, Polish and German.
- Preserves user profile, bookmarks, history and existing in-app signed update pipeline.


## v0.9.4 Alpha
- Firefox-style Default zoom with website-wide preset levels from 50% to 300%.
- Zoom text only, applying readable text font scaling rather than whole-page zoom.
- Global zoom preferences update open websites and split-screen panes immediately.
- Removed NOMIKO's automatic background-tab freezing and discarding across all performance profiles.
- Existing bookmarks, saved tabs and profile data remain local and are preserved by the installer.
- Signed GitHub alpha release for updating directly from NOMIKO v0.9.2.


## v0.9.2 Alpha
- Home page: choose search providers using one small button at the left of the search field.
- Hide the provider button automatically when only one provider is enabled.
- Hide bookmarks bar with no saved toolbar bookmarks; show it on the first bookmark, hide after deleting the last.
- Published through signed GitHub Releases for in-app updates from v0.9.1.


## v0.9.1 Alpha
- Graphite NOMIKO Windows icon (16px to 256px).
- EXE and taskbar icon + stable AppUserModelID.
- Desktop and Start Menu shortcuts with branded icons, removed on uninstall.
- Signed GitHub Alpha release pipeline and existing Update Center integration.
- All browser settings stay in %APPDATA%\NOMIKO.

# NOMIKO v0.9.0 Alpha — Update foundation

- Added signed update discovery via GitHub Releases API (Ed25519 pinned public key).
- Installer download verifies signed size and SHA-256, rejects suspicious filenames and mismatched tags.
- Added Update Center UI and Settings → Updates; default launch check can be disabled.
- Added external Windows update helper that waits for NOMIKO to exit before running NSIS silently after user confirmation.
- GitHub Actions builds Windows portable EXE, helper, NSIS setup, and signs releases with a repository secret.
- Local user profile data lives separately from app install files.
- Added offline updater tests.

**Deployment incomplete:** repository, Actions signing secret, first GitHub release and live Windows checks still required. Windows Authenticode signing, rollback and delta patching are not implemented.

---

# NOMIKO changelog

## v0.8.2 Alpha (Windows 11)

Fixed vertical tab reordering in both left/right sidebars. Replaced the incompatible native QTabBar sidebar drag with pointer-following paint, animated neighbor shifts and a real moveTab drop. Works with favicon-only and expanded titles. Close controls cannot accidentally trigger while dragging. Background tabs do not activate during drag. No changes to web engine or user data. 55 offline tests pass; Windows 11 GUI interaction still needs verification.

## v0.8.1 Alpha (Windows 11)

Fixed Split View: independent searches on left/right, independent DuckDuckGo / Google / local NOMIKO Search selectors, working Enter/search buttons and navigation controls. Right pane starts on local NOMIKO home instead of requiring a URL prompt. Existing web security/navigation interceptors are shared by split panes. Ctrl+L, back/forward/reload/home, bookmarks and find-in-page target active pane. 49 offline tests pass, GUI not yet verified on Windows 11.

## v0.8.0 Alpha (Windows 11)

New tab tools: pin/unpin, named group tags, Ctrl+Shift+A switcher, named local workspaces, Split View tab, HTML-to-text reader, experimental website PiP request.

New local data tools: HTML bookmark migration, secure ZIP allowlisted backups with safeguards against zip path traversal and backup snapshots, Windows DPAPI encrypted manual password notes (without form autofill).

Appearance and modules: six theme presets, theme JSON import/export with validation, live interface font scale, opt-in local domain-blocking file (no executable extensions).

Safety/performance: HTTP and Punycode warning prompts, executable-download warnings, user-control permissions view, performance monitor showing process-only RAM. Existing background tab management retained.

Developer build: Windows PyInstaller script, GitHub Actions workflow and NSIS installer source. No Windows binary compiled during this update.

44 offline tests pass. No Qt/Windows GUI test has been performed in this environment.

Remaining goals: audited security and anonymity; signed update distribution; robust phishing/malware intelligence; WebExtensions or a security-reviewed plugin SDK; password autofill and a stronger vault architecture; complete localization; comprehensive usability and Windows integration tests.

Earlier changes from v0.7.2 remain in the source history / prior release changelog.

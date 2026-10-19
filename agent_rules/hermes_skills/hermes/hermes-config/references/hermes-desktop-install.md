# Hermes Desktop (Electron) Installation — pip-installed Hermes

## Problem
`hermes desktop` fails with "Desktop GUI source not found at: .../site-packages/apps/desktop" because the pip wheel does NOT include the Electron app source code. The monorepo must be cloned separately.

## Quick Alternative: Web Dashboard
If you just need a GUI fast, skip all of this:
```bash
hermes dashboard --no-open
# Opens at http://127.0.0.1:9119
```

## Full Desktop Install Steps

### 1. Clone with sparse checkout
```bash
mkdir -p /c/hermes-source && cd /c/hermes-source
git init
git remote add origin https://github.com/NousResearch/hermes-agent.git
git config core.sparseCheckout true
cat > .git/info/sparse-checkout << 'EOF'
apps/desktop
apps/shared
package.json
package-lock.json
.npmrc
.pnpmrc
eslint.config.shared.mjs
EOF
git pull origin main --depth=1
```

**Why `apps/shared`?** The desktop app imports `@hermes/shared` (billing, gateway, skin modules). Without it, `vite build` fails with "The system cannot find the path specified" on `@hermes/shared/charge-settlement`.

### 2. Create junction links into site-packages
```bash
SITE="C:/Users/Admin/AppData/Local/Programs/Python/Python311/Lib/site-packages"

# Junction for apps/desktop
python -c "
import subprocess
subprocess.run(['cmd', '/c', 'mklink', '/J',
    r'$SITE\apps\desktop',
    r'C:\hermes-source\apps\desktop'], check=True)
"

# Junction for apps/shared
python -c "
import subprocess
subprocess.run(['cmd', '/c', 'mklink', '/J',
    r'$SITE\apps\shared',
    r'C:\hermes-source\apps\shared'], check=True)
"

# Copy workspace root config files (not junction — npm resolves these differently)
cp /c/hermes-source/package.json "$SITE/package.json"
cp /c/hermes-source/package-lock.json "$SITE/package-lock.json"
test -f /c/hermes-source/.npmrc && cp /c/hermes-source/.npmrc "$SITE/.npmrc"
```

**Why junctions, not symlinks?** Windows symlinks require elevated privileges. Junctions (`mklink /J`) work without admin and resolve transparently for Node.js/npm.

**Why `mkdir -p "$SITE/apps"` first?** The `apps/` dir may not exist yet in site-packages.

### 3. Install dependencies (TWICE)
```bash
# Install at site-packages (for hermes desktop launcher)
cd "$SITE" && npm install --workspace apps/desktop

# ALSO install at repo root (for build scripts that use import.meta.dirname)
cd /c/hermes-source && npm ci
```

**Why twice?** The build script `assert-root-install.mjs` resolves `../../../` from `apps/desktop/scripts/` via `import.meta.dirname`. Through a junction, this resolves to the REAL path (`C:\hermes-source`), not the site-packages path. So `node_modules/vite/package.json` must exist at `C:\hermes-source\node_modules\`.

### 4. Approve npm scripts
```bash
cd /c/hermes-source
npm approve-scripts electron@40.10.2 esbuild@0.28.1 node-pty@1.1.0 unicode-animations@1.0.3 electron-winstaller@5.4.0 agent-browser@0.26.0
```
Then re-run `npm ci` to trigger the approved postinstall scripts (electron download, etc.).

### 5. Build
```bash
cd /c/hermes-source/apps/desktop
npm run build
```

Output: `dist/` with `index.html`, `electron-main.mjs`, `electron-preload.js`, assets, and staged `node-pty`.

### 6. Launch
```bash
hermes desktop --skip-build --source
```

- `--skip-build`: don't re-run npm ci / npm run pack
- `--source`: launch via `electron .` against the dist/ directory (not a packaged .exe)

## Pitfalls

1. **`npm ci` at site-packages alone is NOT enough.** The build script's `import.meta.dirname` resolves through junctions to the real filesystem path. `node_modules/vite` must exist at the repo root too.

2. **`mklink /D` (symlink) fails without admin.** Use `mklink /J` (junction) instead. Python's `subprocess.run(['cmd', '/c', 'mklink', '/J', ...])` is the reliable wrapper.

3. **electron postinstall blocked by allow-scripts.** Must run `npm approve-scripts electron@...` then re-run `npm ci`. Without this, `electron.exe` is not downloaded.

4. **Version drift.** The desktop app version (0.17.0) may lag behind the CLI version (0.19.0). The sparse checkout pulls HEAD of main, which should be compatible.

5. **`hermes desktop` without `--skip-build` re-runs `npm ci` at site-packages**, which is slow and may conflict with the junction setup. Always use `--skip-build --source` after initial build.

6. **Registry error on launch** (`ERROR: The system was unable to find the specified registry key or value`) is harmless — Electron trying to detect default browser. App still launches fine.

7. **`--hermes-root` flag** sets `HERMES_DESKTOP_HERMES_ROOT` env var for the Electron runtime, but does NOT fix the build script path resolution. Don't rely on it for the build step.

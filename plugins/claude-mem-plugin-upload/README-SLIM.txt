claude-mem — slim plugin folder for upload (stays under typical 50 MB limits)

Omitted vs full repo:
- docs, tests, src, openclaw, install, installer, ragtime, cursor-hooks, .github, repo-root scripts/
- plugin/scripts/claude-mem (~60MB standalone CLI; hooks use Bun + worker-service.cjs)

Restore full tree: git clone https://github.com/thedotmack/claude-mem
Marketplace: /plugin marketplace add thedotmack/claude-mem  then  /plugin install claude-mem

Full offline bundle (larger, includes docs/tests/src and the standalone CLI binary):
  claude-mem-plugin-full.zip  (~28 MB zipped; ~72 MB uncompressed)

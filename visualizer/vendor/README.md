# Vendored libraries

These third-party libraries are vendored (committed directly into the repo) so
the Silicon Org visualizer runs **offline with no build step** — open the local
visualizer in a browser and it works without npm, a bundler, or a CDN.

All three are distributed under the MIT License.

| File | Library | Version | Upstream | License |
|------|---------|---------|----------|---------|
| `three.module.js` | three.js | r164 | https://github.com/mrdoob/three.js | MIT |
| `controls/OrbitControls.js` | three.js examples (OrbitControls) | r164 | https://github.com/mrdoob/three.js | MIT |
| `js-yaml.min.js` | js-yaml | 4.1.0 | https://github.com/nodeca/js-yaml | MIT |

## Notes

- `three.module.js` and `controls/OrbitControls.js` come from the same three.js
  release (r164); keep them on matching versions when updating.
- `js-yaml` parses the ontology / registry YAML directly in the browser so the
  visualizer can render the graph without a server.
- Each upstream project ships its own MIT license text; see the linked
  repositories for the full terms.

To update, replace the file(s) with the corresponding release artifact from the
upstream project and bump the versions in the table above.

# The spirits atlas — visual direction

Volume 04 moves the public experience from dark instrumentation to warm paper and ink. The reference is a distiller's field atlas with an urban editorial rhythm: generous margins, large Baskerville/Palatino headlines, quiet sans-serif controls, oxblood accents and green-black primary actions. No external fonts or image trackers are required.

## Visual vocabulary

- Warm paper is a CSS colour and a small inline SVG grain texture, rather than a large paper photograph. It does not reduce text opacity.
- `frontend/public/art/atlas-map.svg` is original authored vector ornament: imperfect coastlines, a compass rose, dotted routes and survey marks. The map is decorative and carries **no geographic assertions**. It has no focus target or screen-reader content.
- Bottle photographs retain their original credit and licence. Illustrations and procedural 3D remain distinguished from photographed or scanned packaging.
- Charts, source links and missing-data labels remain available. Product chapters are collapsed initially and expand on click or keyboard activation. In-page chapter links open their containing chapter, including on direct hash navigation.
- The sound studio and object/neural studios retain a dark instrument surface. The botanical scene uses paper with legible ink labels. Audio still requires an explicit user action.

## Implementation

The final imported `frontend/src/atlas.css` owns the public palette and editorial presentation. Existing layout CSS remains in `style.css`; this is a migration layer, not a second theme toggle. `dossier.ts` supplies semantic native `details` chapters while preserving existing bindings and IDs. Reduced-motion settings remove the chapter-arrow animation and smooth scrolling. Mobile keeps a single column.

Nginx serves `/art/` directly from the frontend image, under the existing CSP; unknown art paths return 404. This route does not expose uploads or filesystem browsing.

## Scope boundary

This visual release does not certify the in-progress expanded ingredient dataset, new studies, complete front/back photo pairs, a biological Markov model, or a 3D bottle scan. Those workstreams retain their separate validation requirements. Never infer a finished-drink effect from a possible botanical constituent.

`juniper-ink.svg` is an original line drawing with needle strokes, berry details and light hatching. It is decorative illustration, not a verified specimen plate. The art directory is versioned with the frontend and served locally. The first generated botanical atlas supplies illustrative plates in the exploded scene. Missing drawings are marked rather than replaced with an unrelated plant. Each visible ingredient is also a keyboard-accessible button; selecting it opens the inspector alongside the scene.

## Disc presentation and field journal

The final public default is the in-page immersive atlas disc. A first-session dialog offers sound-on or quiet entry; the fixed transport remains visible across routes. This is a full-viewport layout, not an unsolicited browser fullscreen request. Escape/Exit provides an ordinary-page fallback. Bottle pages group material into six native keyboard-operable journal tabs. Long evidence is opened on demand. Original cartography and illustrated plates remain clearly separate from actual photographs and data charts.

The README uses a script-free animated SVG frontispiece, real browser motion GIF, screenshots, Mermaid and a user-initiated audio file. CSS/SMIL animation support depends on GitHub's image renderer; the title and artwork have a static fallback. Hex/ASCII labels are visual motifs, not a claimed way to execute code inside GitHub Markdown. A C/WASM rendering experiment belongs to a future engine exploration; the delivered frontend remains TypeScript/Three.js/Web Audio and contains no untested native/WASM runtime.

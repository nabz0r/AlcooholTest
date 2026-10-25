# Experience guide — Volume 02

## Arrival and discovery

The homepage is an editorial introduction, not the catalogue. Select Monkey 47, Roku or Bombay to change the featured object and its source-linked chapter. Origins, Craft and Sound & senses tabs reveal different readings of the same product. Enter interactive 3D loads a real orbitable scene; Return to photograph restores the actual reference image. The separate Collection page supplies search, filters and pagination. Stories provides an explicit editorial entry point.

The primary navigation uses durable URLs: `/`, `/stories/`, `/catalogue/`, `/research/`, `/spirits/<slug>/`, `/compare/`, `/shelf/`, `/contribute/`, `/account/`, `/setup/` and `/studio/`. Browser Back/Forward work with the history API. Legacy `#product/...` and other known hash routes migrate to these paths. Bottle chapter links retain local anchor navigation. Account-dependent actions return visitors to their intended page after sign-in.

## Studio controls

Open Studio 3D, Botanical explosion or Neuro atlas on a product. Drag to orbit, Shift-drag to pan, use explicit −/＋ buttons to zoom and Reset view to restore framing. Left/right arrows rotate a focused canvas; +/− also change distance. Pause/Start orbit controls automatic camera movement. Full screen expands the studio, including on the homepage. Botanical Plants arrows page through up to eight documented ingredients, and Unfold adjusts their spread. Pointer movement beyond five pixels is treated as a drag, not a plant selection. Mouse wheel stays available for page scrolling rather than trapping the visitor in the canvas.

These objects are procedural interpretations, not measured scans. Photograph-derived labels are approximate; a rotated front texture is never evidence of the real reverse. Use Packaging for actual label photographs.

## Sound studio

The visible header control and homepage invitation open a native dialog. Play composition explicitly enables audio; Pause composition stops and releases the audio context. Test speakers emits a brief 440 Hz test tone. Master volume persists locally; floral, spice and citrus sliders adjust the synthesis. A live meter indicates browser audio output activity. Download exports an original 20-second stereo PCM WAV rendered locally. No microphone, copied recordings or external audio service is involved. Browsers require user activation, and OS/browser muting can still silence speakers.

A deterministic product identity seeds a pentatonic composition. Documented ingredient names affect timbres. It is an artistic reading of the record, not chemical sonification or evidence of biological effects. Backgrounding suspends playback. Opening/closing the dialog does not itself switch playback; the header shows Listening while active.

## Packaging and community

Front, Rear label and Details select attributed real views. A missing view has a contribution invitation and an explicit absence message. Inspect label opens a native dialog with 50–500% zoom, fit and scrollable image space; Escape closes it. The Heering record includes an actual historical 70 cl front/rear pair under CC BY-SA 4.0. Other rear views are incomplete.

Signed-in members can submit JPEG/PNG/WebP photos up to 5 MiB and 16 megapixels. The upload must state view, photographer, license/permission, source URL and rights confirmation; edition/market captions help editorial matching. Images are decoded, stripped of metadata through JPEG re-encoding, resized to a maximum 2400-pixel edge and held for moderation. Editors inspect the source and admin preview before publishing. A member's rights statement is not independent proof of ownership. Uploaded media and private tables need separate backups; they are excluded from public catalogue JSON.

A tasting note has an overall 0–5 monkey rating, optional aroma/taste/finish/value/design scores, up to eight aroma tags, serving context and a buy-again preference. Empty dimension scores remain unknown. Published averages count only approved notes and show the number of responses per dimension. All reviews are self-reported, with no verified-purchase badge because the site has no purchase ledger. Love it is a quick 5-monkey vote and remains subject to moderation.

## Search discovery and metadata

Django renders useful text, source links and product URLs before JavaScript. Unique titles, descriptions, canonical links, Open Graph metadata and Schema.org JSON-LD accompany direct routes. The client updates metadata on navigation. `/sitemap.xml` contains published products and public discovery pages; private/member pages carry noindex. `/robots.txt` points to the sitemap. Merged occurrences redirect to the canonical object. Set `PUBLIC_BASE_URL` to the actual HTTPS origin before production. This is technical SEO support; rankings, rich results and indexing are not guaranteed.

## Screenshot and change discipline

README screenshots must be captured from the running application, not generated mockups. Preserve full source/license context in the product itself; screenshot captions explain the shown workflow. Update `PLAN.md` when scope changes, `PROGRESS.md` as work passes milestones, `docs/VALIDATION.md` after verification and `docs/SCREENSHOTS.md` when capturing a new gallery. Do not mark a feature complete based only on source changes. Record limitations and failed checks before their resolution. Never commit tokens, authenticated personal data or database backups with the screenshots.

Collection filters live in the URL query string. Opening a product and using Back restores the search/category/origin/disclosure controls; category tabs reflect the selected native filter. Pending search timers are cancelled on route changes. Same-page chapter hashes preserve the selected studio and do not rebuild the product.

Volume 03: Discover opens a dedicated decision desk; apply multiple ingredient groups, origin, documented strength and coverage constraints. Removable chips, counts, sorting, pagination, shared URLs and a mobile filter disclosure explain the current direction. Product coverage tiles jump to the relevant chapter. Same-category alternatives disclose their indexed ingredient overlap and offer a direct two-record comparison. A persistent shortlist leads to a shareable comparison matrix with a differences-only toggle and expandable ingredient rows. Independent critic summaries are attributed, separate from community ratings. Full rules and limitations are documented in DECISIONS.md.

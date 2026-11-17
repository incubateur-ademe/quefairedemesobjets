# Javascript

- Using Typescript
- Linter: ESLint with "love" config
- Formatting: Prettier (trailing comma: all, printWidth: 88, semi: false)
- Framework: Stimulus for controllers, Turbo for navigation
- Build: Parcel compiles `static/to_compile/` and `static/to_collect` to `static/compiled/`

## [Stimulus](https://stimulus.hotwired.dev/)

- Controllers are in `webapp/static/to_compile/controllers/`
- Two Stimulus applications, never on the same document: the site's
  (`qfdmo.ts`, `quefaire.ts`…) and the assistant V2's
  (`js/assistant/application.ts`, loaded by `assistant.ts`). Assistant
  controllers are registered as `assistant-*`. In the lookbook, a preview picks
  its stack with its `assets` attribute.
- Use Stimulus targets and values
- Export as `export default class extends Controller`
- Structure example:

```typescript
import { Controller } from "@hotwired/stimulus";

export default class extends Controller<HTMLElement> {
  static targets = ["targetName"];
  declare readonly targetNameTarget: HTMLElement;

  connect() {
    // Initialization
  }
}
```

## [Turbo frame](https://turbo.hotwired.dev/handbook/frames)

Turbo Frames allow partial page updates by wrapping a section of HTML in a `<turbo-frame>` element. When a link or form inside the frame is triggered, Turbo only replaces the content of the matching frame in the current page.

Make sure the server response contains a `<turbo-frame>` with the same `id` so Turbo can update the correct region.

## Map

We use `Maplibre` js technologie with `Carte Facile` vectorial layers in application and OpenStreetMap layers for the backoffice

The assistant V2 does not import `carte-facile`: its desaturated style is a
static copy, `static/to_collect/assistant/carte-style.json`. The package is a
single module bundling its four styles and its controls (80 KB gzipped); the
copy weighs 10 KB. To refresh it after a `carte-facile` upgrade, copy the
package's desaturated style JSON over that file.

The Latin glyph ranges of the style's fonts are static files too
(`static/to_collect/assistant/glyphs/`): their server answers without
`Cache-Control`, so every map load asked for them again. A font added to the
style needs its ranges there, and in the `glyphs` value of
`ui/components/assistant/carte.html`; until then it comes from the style's
`glyphs` server.

### Assistant combobox

`assistant-combobox` copies each chosen suggestion into the hidden fields by
their `data-key`. With `require-choice`, Enter refuses typed text left without
a suggestion; a hidden field marked `data-optional` (e.g. `synonyme`) does not
count as missing.

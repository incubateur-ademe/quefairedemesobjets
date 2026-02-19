# Javascript

- Using Typescript
- Linter: ESLint with "love" config
- Formatting: Prettier (trailing comma: all, printWidth: 88, semi: false)
- Framework: Stimulus for controllers, Turbo for navigation
- Build: Parcel compiles `static/to_compile/` and `static/to_collect` to `static/compiled/`

## [Stimulus](https://stimulus.hotwired.dev/)

- Controllers are in `webapp/static/to_compile/controllers/`
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

# A/B testing

Experiments are run via [PostHog feature flags](https://posthog.com/docs/feature-flags).
A small Stimulus controller (`ab-test`) lets any element with a `src` attribute
(typically a `<turbo-frame>`) opt into an experiment by declaring two URLs in
HTML — the control URL stays on `src=`, the variant URL goes on a data
attribute. The controller swaps the `src` based on the flag value.

## How it works

```
                     ┌──────────────────────────┐
                     │ Stimulus connect()       │
                     │ - read src as control    │
                     │ - clear src (pause Turbo)│
                     └──────────┬───────────────┘
                                │
            mobile-only and desktop?
                  │ yes              │ no
                  ▼                  ▼
        restore control      posthog.onFeatureFlags()
                                     │
                          getFeatureFlag(key)
                                     │
                       === "variant"?│
                  ┌────yes────┐   ┌──no──┐
                  ▼           │   ▼      │
           assign variant     │   restore control
                              ▼
                  posthog.register({ $feature/<key>: <variant> })
```

Safety net: if the controller never mounts (JS bundle fails, Stimulus broken),
the original `src` stays on the element and Turbo loads it as today. If
PostHog is unreachable or throws, the controller falls back to the original
`src`.

## Markup

```html
<turbo-frame
  id="…"
  src="{{ control_url }}"
  loading="lazy"
  data-controller="ab-test"
  data-ab-test-flag-key-value="my-experiment"
  data-ab-test-src-variant-value="{{ variant_url }}"
  data-ab-test-mobile-only-value="true"
>
</turbo-frame>
```

| Attribute                        | Required | Default | Purpose                                                                            |
| -------------------------------- | -------- | ------- | ---------------------------------------------------------------------------------- |
| `data-controller="ab-test"`      | yes      | —       | wires the controller                                                               |
| `src`                            | yes      | —       | URL loaded for `control` and as a safety fallback                                  |
| `data-ab-test-flag-key-value`    | yes      | —       | PostHog flag key                                                                   |
| `data-ab-test-src-variant-value` | yes      | —       | URL loaded when the flag returns `"variant"`                                       |
| `data-ab-test-mobile-only-value` | no       | `false` | when `true`, only honour the variant if `matchMedia("(max-width: 767px)")` matches |

The controller registers `$feature/<key>: <variant>` as a posthog
super-property so subsequent events on the page carry the variant
automatically.

## Setting up a new experiment

1. **Create the feature flag in PostHog.**
   - Multivariate flag with two variants: `control` and `variant`.
   - 50/50 rollout, 100% of users.
   - No targeting filters: device gating is done client-side via `matchMedia`.

2. **Wire the markup.** Pick the smallest element that needs to change (a
   Turbo Frame, a link with a `src`, etc.) and add the data attributes above.

3. **Goal events.** Reuse existing `posthog.capture(...)` calls. PostHog
   experiments will pick them up via the `$feature/<key>` property registered
   by the controller.

4. **Counter-metric.** If the variant changes a default that the user can
   override, capture the override event so you can measure "users who flipped
   away from their assigned default".

## Killing an experiment

In PostHog → Feature Flags → set rollout to `0%` (or disable the flag). All
users fall back to control immediately, no redeploy required.

## Promoting the winning variant

When the experiment ends:

- If the winner is `control`: remove the data attributes and the
  `data-ab-test-src-variant-value` attribute. The element is back to normal.
- If the winner is `variant`: replace `src` with the variant URL and remove
  the data attributes. The element is back to normal.
- The `ab-test` controller stays in the bundle — it's generic and the next
  experiment will reuse it.

## Current experiments

| Flag key                            | Variant change                                                                         | Files                                                                                |
| ----------------------------------- | -------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------ |
| `produit-carte-default-view-mobile` | On mobile produit pages, the carte loads in `liste` mode by default instead of `carte` | `webapp/templates/templatetags/carte.html`, `webapp/core/templatetags/carte_tags.py` |

### Opting a `ProduitPage` into `produit-carte-default-view-mobile`

The experiment is opt-in per page. In the Wagtail admin, edit the `ProduitPage`,
go to the **Configuration** tab, and tick **"A/B test mode carte/liste par
défaut"**. Pages without this flag never serve the variant — they keep the
existing default. Tick it on a representative subset of fiches to keep the
experiment focused.

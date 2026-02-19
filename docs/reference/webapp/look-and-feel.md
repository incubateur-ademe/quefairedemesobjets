# Look and feel

> Design system and CSS management

This project uses Tailwind **in addition to** the French State Design System (DSFR).
**DSFR is the primary design system**, and Tailwind is mainly used to customize or extend styles when DSFR alone is not sufficient.

- **DSFR**: integrated through the **django-dsfr** package (templates, components, tags) and **@gouvfr/dsfr** assets (CSS/JS).
- **Tailwind**: configured in `tailwind.config.js` with a **`qf-`** class prefix to avoid conflicts with DSFR classes.

In practice, templates use both **DSFR** classes and components (buttons, header, footer, forms, etc.) and **Tailwind** classes with the `qf-` prefix (`qf-flex`, `qf-mt-2w`, etc.) for layout and visual fine‑tuning.

The DSFR colors and icons actually used are tracked in `dsfr_hacks/` (color and icon extraction).

This prefix and other Tailwind customizations (colors, screens, plugins, etc.) are configured in `webapp/tailwind.config.js`.

For readability, try to group Tailwind classes by purpose on each line.
For example, you can separate classes related to **layout** (flex, spacing, alignment) from those related to **visual style** (border, color, typography, background).

```html
<div
  class="
  qf-flex qf-justify-around
  qf-border-solid qf-border-black qf-border-2
  qf-bg-white
"
></div>
```

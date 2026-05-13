import type { Map } from "maplibre-gl"

// Use the actual device pixel ratio (with a floor of 2 so non-retina users
// still get a sharp image when MapLibre tints/scales it during pan/zoom).
const PIXEL_RATIO = Math.max(window.devicePixelRatio || 1, 2)

// Today's DOM markers are wrapped with `qf-scale-75` (CSS scale 0.75), so the
// 46x61 native pin renders at ~34x46 on screen. Bake that into the rasterized
// canvas so consumers don't need to apply icon-size: 0.75 themselves.
const DISPLAY_SCALE = 0.75

// Pin shape: the white interior path…
const PIN_OUTLINE_PATH =
  "M36.899 39.868c4.98-4.132 8.15-10.367 8.15-17.343C45.05 10.085 34.966 0 22.526 0 10.085 0 0 10.085 0 22.525c0 6.972 3.167 13.204 8.142 17.335l5.008 5.21a44.446 44.446 0 0 1 9.622 15.326 42.517 42.517 0 0 1 9.244-15.336l4.883-5.192Z"

// …and the original painted "stroke" path (a separately authored shape that
// hugs the perimeter, drawn on top of the fill). Carrying the original shape
// over verbatim keeps the asymmetric weighting and pixel-perfect match with
// the legacy DOM marker.
const PIN_OUTLINE_STROKE_PATH =
  "m36.899 39.868-1.916-2.31-.143.12-.127.135 2.186 2.055ZM8.142 39.86l2.163-2.079-.117-.12-.13-.108-1.916 2.307Zm5.008 5.21-2.163 2.08 2.163-2.08Zm9.622 15.326-2.812 1.045 2.925 7.875 2.725-7.947-2.838-.973Zm9.244-15.336 2.186 2.055-2.186-2.055ZM42.05 22.525c0 6.046-2.745 11.448-7.067 15.034l3.832 4.617C44.45 37.5 48.05 30.431 48.05 22.525h-6ZM22.525 3C33.308 3 42.05 11.742 42.05 22.525h6C48.05 8.428 36.621-3 22.525-3v6ZM3 22.525C3 11.742 11.742 3 22.525 3v-6C8.428-3-3 8.428-3 22.525h6Zm7.059 15.028C5.74 33.967 3 28.567 3 22.525h-6C-3 30.426.594 37.49 6.225 42.168l3.834-4.615Zm-4.08 4.386 5.008 5.21 4.326-4.158-5.008-5.21-4.326 4.158Zm5.008 5.21a41.446 41.446 0 0 1 8.973 14.292l5.625-2.09a47.445 47.445 0 0 0-10.272-16.36l-4.326 4.158ZM25.61 61.37a39.518 39.518 0 0 1 8.592-14.254l-4.371-4.11a45.519 45.519 0 0 0-9.897 16.418l5.676 1.946Zm8.592-14.254 4.883-5.192-4.372-4.11-4.882 5.192 4.37 4.11Z"

// The original painted-stroke path extends ~3 SVG units past the pin's outer
// edge. Pad the canvas by that amount on each side so the stroke isn't
// clipped against the canvas boundary.
const STROKE_MARGIN = 3.5

const REPARER_FILLED_FOREGROUND = "#37635F"

type IconGlyph = {
  // SVG inner markup, expected viewBox 0 0 24 24 (or 0 0 30 30 for hand-heart).
  // Color comes from `currentColor` so we can recolor at composition time.
  innerSvg: string
  viewBox: string
}

const GLYPHS: Record<string, IconGlyph> = {
  "fr-icon-hand-heart": {
    viewBox: "0 0 30 30",
    innerSvg:
      '<path fill="currentColor" d="M6.522 8.396a9.1 9.1 0 0 1 4.341 1.864h2.83a5.87 5.87 0 0 1 5.87 5.869h-9.131l.002 1.305 10.432-.001V16.129a7.27 7.27 0 0 0-1.155-3.913h3.764a6.52 6.52 0 0 1 5.89 3.72c-3.085 4.07-8.08 6.713-13.716 6.713-3.6 0-6.65-.77-9.128-2.118zM3.912 7c.72 0 1.305.584 1.305 1.304v11.738c0 .72-.585 1.304-1.305 1.304H1.304c-.72 0-1.304-.584-1.304-1.304V8.304C0 7.584.584 7 1.304 7z"/>',
  },
  "fr-icon-arrow-go-back-line": {
    viewBox: "0 0 24 24",
    innerSvg:
      '<path fill="currentColor" d="m5.828 7 2.536 2.536L6.95 10.95 2 6l4.95-4.95 1.414 1.414L5.828 5H13a8 8 0 1 1 0 16H4v-2h9a6 6 0 1 0 0-12H5.828Z"/>',
  },
  "fr-icon-tools-fill": {
    viewBox: "0 0 24 24",
    innerSvg:
      '<path fill="currentColor" d="M5.32943 3.27152C6.56252 2.83314 7.9923 3.10743 8.97927 4.0944C9.96652 5.08165 10.2407 6.51196 9.80178 7.74529L20.6465 18.5901L18.5252 20.7114L7.67936 9.86703C6.44627 10.3054 5.01649 10.0311 4.02952 9.04415C3.04227 8.0569 2.7681 6.62659 3.20701 5.39326L5.44373 7.62994C6.02952 8.21572 6.97927 8.21572 7.56505 7.62994C8.15084 7.04415 8.15084 6.0944 7.56505 5.50862L5.32943 3.27152ZM15.6968 5.15506L18.8788 3.38729L20.293 4.80151L18.5252 7.98349L16.7574 8.33704L14.6361 10.4584L13.2219 9.04415L15.3432 6.92283L15.6968 5.15506ZM8.62572 12.9332L10.747 15.0546L5.79729 20.0043C5.2115 20.5901 4.26175 20.5901 3.67597 20.0043C3.12464 19.453 3.09221 18.5792 3.57867 17.99L3.67597 17.883L8.62572 12.9332Z"/>',
  },
  "fr-icon-recycle-line": {
    viewBox: "0 0 24 24",
    innerSvg:
      '<path fill="currentColor" d="m19.562 12.097 1.531 2.653a3.5 3.5 0 0 1-3.03 5.25H16v2.5L11 19l5-3.5V18h2.062a1.5 1.5 0 0 0 1.3-2.25l-1.532-2.653 1.732-1ZM7.304 9.134l.53 6.08-2.164-1.25-1.031 1.786A1.5 1.5 0 0 0 5.938 18H9v2H5.938a3.5 3.5 0 0 1-3.031-5.25l1.03-1.787-2.164-1.249 5.53-2.58h.001Zm6.446-6.165c.532.307.974.749 1.281 1.281l1.03 1.785 2.166-1.25-.53 6.081-5.532-2.58 2.165-1.25-1.031-1.786a1.5 1.5 0 0 0-2.598 0L9.169 7.903l-1.732-1L8.97 4.25a3.5 3.5 0 0 1 4.781-1.281h-.001Z"/>',
  },
  "fr-icon-money-euro-circle-line": {
    viewBox: "0 0 24 24",
    innerSvg:
      '<path fill="currentColor" d="M12.0049 22.0027C6.48204 22.0027 2.00488 17.5256 2.00488 12.0027C2.00488 6.4799 6.48204 2.00275 12.0049 2.00275C17.5277 2.00275 22.0049 6.4799 22.0049 12.0027C22.0049 17.5256 17.5277 22.0027 12.0049 22.0027ZM12.0049 20.0027C16.4232 20.0027 20.0049 16.421 20.0049 12.0027C20.0049 7.58447 16.4232 4.00275 12.0049 4.00275C7.5866 4.00275 4.00488 7.58447 4.00488 12.0027C4.00488 16.421 7.5866 20.0027 12.0049 20.0027ZM10.0549 11.0027H15.0049V13.0027H10.0549C10.2865 14.1439 11.2954 15.0027 12.5049 15.0027C13.1201 15.0027 13.6833 14.7806 14.1188 14.412L15.8198 15.546C14.9973 16.4415 13.8166 17.0027 12.5049 17.0027C10.1886 17.0027 8.28107 15.2527 8.03235 13.0027H7.00488V11.0027H8.03235C8.28107 8.75277 10.1886 7.00275 12.5049 7.00275C13.8166 7.00275 14.9973 7.56402 15.8198 8.45951L14.1189 9.59351C13.6834 9.22496 13.1201 9.00275 12.5049 9.00275C11.2954 9.00275 10.2865 9.86163 10.0549 11.0027Z"/>',
  },
}

// Mirrors GroupeAction rows in the database. Names match the `code` column.
// `iconClass` matches GroupeAction.icon (DSFR class), used to pick the glyph.
type GroupeActionVariant = {
  code: string
  iconClass: string
  couleur: string
  filled: boolean
}

const GROUPE_ACTION_VARIANTS: GroupeActionVariant[] = [
  {
    code: "donner_echanger_rapporter",
    iconClass: "fr-icon-hand-heart",
    couleur: "#417dc4",
    filled: false,
  },
  {
    code: "emprunter_preter_louer",
    iconClass: "fr-icon-arrow-go-back-line",
    couleur: "#ce614a",
    filled: false,
  },
  {
    code: "reparer",
    iconClass: "fr-icon-tools-fill",
    couleur: "#009081",
    filled: true,
  },
  {
    code: "trier",
    iconClass: "fr-icon-recycle-line",
    couleur: "#A558A0",
    filled: false,
  },
  {
    code: "vendre_acheter",
    iconClass: "fr-icon-money-euro-circle-line",
    couleur: "#D1B781",
    filled: false,
  },
]

const BONUS_BADGE_SVG = `<svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 22 22" fill="none">
<rect width="22" height="22" rx="11" fill="#EFCB3A"/>
<path fill="#161616" d="M14.6699 17.0019C13.3813 17.0019 12.3366 15.9573 12.3366 14.6686C12.3366 13.3799 13.3813 12.3353 14.6699 12.3353C15.9586 12.3353 17.0033 13.3799 17.0033 14.6686C17.0033 15.9573 15.9586 17.0019 14.6699 17.0019ZM14.6699 15.6686C15.2222 15.6686 15.6699 15.2209 15.6699 14.6686C15.6699 14.1163 15.2222 13.6686 14.6699 13.6686C14.1177 13.6686 13.6699 14.1163 13.6699 14.6686C13.6699 15.2209 14.1177 15.6686 14.6699 15.6686ZM7.33659 9.66859C6.04793 9.66859 5.00325 8.62395 5.00325 7.33529C5.00325 6.04662 6.04793 5.00195 7.33659 5.00195C8.62525 5.00195 9.66993 6.04662 9.66993 7.33529C9.66993 8.62395 8.62525 9.66859 7.33659 9.66859ZM7.33659 8.33529C7.88887 8.33529 8.33659 7.88757 8.33659 7.33529C8.33659 6.783 7.88887 6.33529 7.33659 6.33529C6.78431 6.33529 6.33659 6.783 6.33659 7.33529C6.33659 7.88757 6.78431 8.33529 7.33659 8.33529ZM15.7173 5.3451L16.6601 6.28791L6.28921 16.6588L5.3464 15.716L15.7173 5.3451Z"/>
</svg>`

// Position the icon glyph the same way the live DOM does:
// .qf-scale-75 on the wrapper, plus the existing .qf-top-[10] .qf-left-[10.5]
// inside a 46x61 container. We render the SVG at native pin resolution; visual
// sizing happens via MapLibre's icon-size or by displaying at half-pixel-ratio.
const ICON_POS_X = 10.5
const ICON_POS_Y = 10
const ICON_SIZE = 22

const PIN_NATIVE_WIDTH = 46
const PIN_NATIVE_HEIGHT = 61
// Bonus badge per the Figma design system ("Carte/Punaises de carte"). The
// native SVG badge is 22x22; we render it smaller (16x16) and overlapping the
// upper-right of the pin's circular head, with the badge center sitting just
// above the pin's right shoulder.
const BONUS_BADGE_DISPLAY_SIZE = 16
const BONUS_BADGE_NATIVE_SIZE = 22
const BONUS_BADGE_SCALE = BONUS_BADGE_DISPLAY_SIZE / BONUS_BADGE_NATIVE_SIZE
// Position of the badge's top-left corner in pin-local coords. Pin head is
// centered around (22.5, 22.5) with radius ~22.5; right shoulder ≈ (40, 6).
const BONUS_BADGE_LEFT = 32
const BONUS_BADGE_TOP = 0
// How far the badge protrudes past the pin's bounding box. The badge ends at
// (BONUS_BADGE_LEFT + DISPLAY_SIZE, BONUS_BADGE_TOP) max corner = (48, 0). Pin
// is 46 wide, so right protrusion = 48 - 46 = 2. Top is 0; pin starts at 0;
// so top protrusion = 0 (no protrusion above the pin's bounding box).
const BONUS_PROTRUSION_RIGHT = Math.max(
  0,
  BONUS_BADGE_LEFT + BONUS_BADGE_DISPLAY_SIZE - PIN_NATIVE_WIDTH,
)
const BONUS_PROTRUSION_TOP = Math.max(0, -BONUS_BADGE_TOP)

function buildPinSvg(variant: GroupeActionVariant, withBonus: boolean): string {
  const glyph = GLYPHS[variant.iconClass]
  if (!glyph) {
    throw new Error(`Unknown glyph for icon class: ${variant.iconClass}`)
  }

  // Pin background:
  //  - filled: solid couleur fill, foreground stroke = REPARER_FILLED_FOREGROUND
  //  - outline: white fill, foreground stroke = couleur
  const pinFill = variant.filled ? variant.couleur : "#fff"
  const pinStroke = variant.filled ? REPARER_FILLED_FOREGROUND : variant.couleur
  const iconColor = variant.filled ? "#fff" : variant.couleur

  // Replace currentColor with the resolved color so the glyph paints reliably
  // without depending on CSS inheritance through nested groups.
  const coloredGlyph = glyph.innerSvg.replace(/currentColor/g, iconColor)

  // Canvas dimensions depend on whether the bonus badge is included.
  // Always reserve STROKE_MARGIN on each pin edge so the stroke isn't clipped.
  // Bonus variant additionally extends the canvas to fit the protruding badge
  // on the upper-right.
  const rightPadding = withBonus
    ? BONUS_PROTRUSION_RIGHT + STROKE_MARGIN
    : STROKE_MARGIN
  const topPadding = withBonus ? BONUS_PROTRUSION_TOP : STROKE_MARGIN
  const outerWidth = PIN_NATIVE_WIDTH + STROKE_MARGIN + rightPadding
  const outerHeight = PIN_NATIVE_HEIGHT + topPadding + STROKE_MARGIN
  const pinOffsetX = STROKE_MARGIN
  const pinOffsetY = topPadding

  // Bonus badge in pin-local coords. The badge SVG is 22x22 native; we scale
  // it to BONUS_BADGE_DISPLAY_SIZE and position its top-left at
  // (BONUS_BADGE_LEFT, BONUS_BADGE_TOP) so its center sits over the pin's
  // upper-right shoulder per the Figma reference.
  const bonusOverlay = withBonus
    ? `<g transform="translate(${BONUS_BADGE_LEFT} ${BONUS_BADGE_TOP}) scale(${BONUS_BADGE_SCALE})">${BONUS_BADGE_SVG.replace(/^<svg[^>]*>|<\/svg>$/g, "")}</g>`
    : ""

  const glyphScale = ICON_SIZE / parseFloat(glyph.viewBox.split(" ")[2])

  // The legacy template clips the painted-stroke to the pin outline via an
  // SVG <mask>. We do the same so the stroke doesn't bleed past the pin
  // edges. Mask is in pin-local coordinates, applied to the path before the
  // outer translation - so we apply it inline on the masked path itself.
  const maskId = `pin-mask-${variant.code}-${withBonus ? "bonus" : "plain"}`
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${outerWidth}" height="${outerHeight}" viewBox="0 0 ${outerWidth} ${outerHeight}">
  <defs>
    <mask id="${maskId}" maskUnits="userSpaceOnUse">
      <path d="${PIN_OUTLINE_PATH}" fill="#fff"/>
    </mask>
  </defs>
  <g transform="translate(${pinOffsetX} ${pinOffsetY})">
    <path d="${PIN_OUTLINE_PATH}" fill="${pinFill}"/>
    <g mask="url(#${maskId})">
      <path d="${PIN_OUTLINE_STROKE_PATH}" fill="${pinStroke}"/>
    </g>
    <g transform="translate(${ICON_POS_X} ${ICON_POS_Y}) scale(${glyphScale})">${coloredGlyph}</g>
    ${bonusOverlay}
  </g>
</svg>`
}

function svgToImage(svgText: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const blob = new Blob([svgText], { type: "image/svg+xml;charset=utf-8" })
    const url = URL.createObjectURL(blob)
    const img = new Image()
    img.onload = () => {
      URL.revokeObjectURL(url)
      resolve(img)
    }
    img.onerror = (err) => {
      URL.revokeObjectURL(url)
      reject(err)
    }
    img.src = url
  })
}

async function rasterize(svgText: string, width: number, height: number) {
  const img = await svgToImage(svgText)
  const canvas = document.createElement("canvas")
  canvas.width = width * PIXEL_RATIO
  canvas.height = height * PIXEL_RATIO
  const ctx = canvas.getContext("2d")
  if (!ctx) throw new Error("2d canvas context unavailable")
  ctx.scale(PIXEL_RATIO, PIXEL_RATIO)
  ctx.drawImage(img, 0, 0, width, height)
  return ctx.getImageData(0, 0, canvas.width, canvas.height)
}

export type ActeurIconName = string

export function iconNameFor(groupeActionCode: string, bonus = false): ActeurIconName {
  return bonus ? `acteur:${groupeActionCode}:bonus` : `acteur:${groupeActionCode}`
}

function svgCanvasDimensions(withBonus: boolean) {
  const rightPadding = withBonus
    ? BONUS_PROTRUSION_RIGHT + STROKE_MARGIN
    : STROKE_MARGIN
  const topPadding = withBonus ? BONUS_PROTRUSION_TOP : STROKE_MARGIN
  const outerWidth = PIN_NATIVE_WIDTH + STROKE_MARGIN + rightPadding
  const outerHeight = PIN_NATIVE_HEIGHT + topPadding + STROKE_MARGIN
  return { outerWidth, outerHeight }
}

// Renders & registers all 5 group-action variants (10 with bonus combos —
// only `reparer` actually shows bonus today, but registering both is cheap
// and keeps the lookup uniform).
export async function registerActeurIcons(map: Map): Promise<void> {
  const tasks: Array<Promise<void>> = []
  for (const variant of GROUPE_ACTION_VARIANTS) {
    for (const withBonus of [false, true]) {
      const svg = buildPinSvg(variant, withBonus)
      const name = iconNameFor(variant.code, withBonus)
      const { outerWidth, outerHeight } = svgCanvasDimensions(withBonus)
      tasks.push(
        rasterize(svg, outerWidth * DISPLAY_SCALE, outerHeight * DISPLAY_SCALE).then((imageData) => {
          if (map.hasImage(name)) return
          map.addImage(name, imageData, { pixelRatio: PIXEL_RATIO })
        }),
      )
    }
  }
  await Promise.all(tasks)
}

// Exposed for the preview harness.
export const _internals = {
  buildPinSvg,
  GROUPE_ACTION_VARIANTS,
  GLYPHS,
}

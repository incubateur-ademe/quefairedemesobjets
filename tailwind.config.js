/** @type {import('tailwindcss').Config | null} */
import DSFRColors from "./dsfr_hacks/colors"

/*
variables = re.findall(r'--([a-zA-Z0-9-_]+)\s*:\s*([^;]+);', block)
The colors set here are defined at the database level in actions and groupe actions
objects.
They match some colors from the DSFR and their name comes from their CSS variable.
*/
const colors = [
  "blue-cumulus-975-75",
  "blue-cumulus-main-526",
  "blue-cumulus-main-526",
  "brown-cafe-creme-950-100",
  "brown-cafe-creme-main-782",
  "brown-cafe-creme-main-782",
  "green-menthe-main-548",
  "orange-terre-battue-main-645",
  "pink-tuile-main-556",
  "purple-glycine-975-75",
  "purple-glycine-main-494",
  "green-menthe-975-75",
  "purple-glycine-main-494",
  "yellow-tournesol-sun-407-moon-922",
]

module.exports = {
  content: [
    "jinja2/*.html",
    "jinja2/**/*html",
    "jinja2/**/**/*html",
    "templates/**/*html",
    "static/to_compile/**/*{j,t}s",
    "static/to_compile/**/*svg",
    "./**/forms.py",
  ],
  prefix: "qfdmo-",
  corePlugins: {
    preflight: false,
  },
  safelist: [
    {
      pattern: new RegExp(`qfdmo-(border|bg)-(${colors.join("|")})`)
    },
    "fr-icon-recycle-line",
    "fr-icon-arrow-go-back-line",
    "sm:qfdmo-max-w-[596px]",
    "sm:qfdmo-min-w-[600px]",
    "sm:qfdmo-w-[250px]",
    "sm:qfdmo-w-[400px]",
  ],
  theme: {
    colors: {
      // https://www.systeme-de-design.gouv.fr/elements-d-interface/fondamentaux-de-l-identite-de-l-etat/couleurs-palette
      info: {
        "975-active": "#c2cfff",
      },
      black: "black",
      white: "white",
      ...DSFRColors
    },
    spacing: {
      // https://www.systeme-de-design.gouv.fr/elements-d-interface/fondamentaux-techniques/espacements
      0: 0,
      "1v": "0.25rem",
      "1w": "0.5rem",
      "3v": "0.75rem",
      "2w": "1rem",
      "3w": "1.5rem",
      "4w": "2rem",
      "5w": "2.5rem",
      "6w": "3rem",
      "7w": "3.5rem",
      "8w": "4rem",
      "9w": "4.5rem",
      "12w": "6rem",
      "15w": "7.5rem",
    },
    extend: {
      maxWidth: {
        readable: "80ch",
        "120w": "60rem",
      },
      screens: {
        xs: "320px",
        xsm: "360px",
      },
      aria: {
        // Remove when https://github.com/tailwindlabs/tailwindcss/pull/10966 in a release
        busy: "busy=true",
      },
      minWidth: ({ theme }) => ({ ...theme("spacing") }),
      keyframes: {
        wave: {
          "0%": { transform: "rotate(0.0deg) scale3d(0.75, 0.75, 1) translateZ(0)" },
          "10%": { transform: "rotate(6deg) scale3d(1, 1, 1)" },
          "20%": { transform: "rotate(0deg) scale3d(0.9, 0.9, 1)" },
          "30%": { transform: "rotate(1deg) scale3d(0.9, 0.9, 1)" },
          "40%": { transform: "rotate(0deg) scale3d(0.9, 0.9, 1)" },
          "100%": { transform: "rotate(0) scale3d(0.9, 0.9, 1) translateZ(0)" },
        },
        "modal-appear": {
          "0%": { opacity: 0, transform: "translateY(0px) scale(0.98)" },
          "50%": { opacity: 1 },
          "100%": {
            transform: "translateY(0px) scale(1)",
          },
        },
      },
      animation: {
        wave: "wave 1.5s linear",
        "modal-appear": "modal-appear 0.2s",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
}

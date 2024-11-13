/** @type {import('tailwindcss').Config | null} */
import DSFRColors from "./dsfr_hacks/colors"
import usedColors from "./dsfr_hacks/used_colors"

/*
The colors set here are defined at the database level in actions and groupe actions
objects.
They match some colors from the DSFR and their name comes from their CSS variable.
*/
module.exports = {
  content: [
    "jinja2/*.html",
    "jinja2/**/*html",
    "jinja2/**/**/*html",
    "templates/**/*html",
    "static/to_compile/**/*{j,t}s",
    "static/to_compile/**/*svg",
    "./**/forms.py",
    "./dsfr_hacks/used_icons.js"
  ],
  prefix: "qfdmo-",
  corePlugins: {
    preflight: false,
  },
  safelist: [
    "sm:qfdmo-max-w-[596px]",
    "sm:qfdmo-min-w-[600px]",
    "sm:qfdmo-w-[250px]",
    "sm:qfdmo-w-[400px]",
    {
      pattern: new RegExp(`qfdmo-(border|bg)-(${usedColors.join('|')})`)
    }
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
      height: {
        header: "var(--header-height)",
        "main-svh": "calc(100svh - var(--header-height))",
        "main-vh": "calc(100vh - var(--header-height))"
      },
      spacing: {
        header: "var(--header-height)"
      },
      maxWidth: {
        readable: "80ch",
        "120w": "60rem",
      },
      screens: {
        xs: "320px",
        xsm: "360px",
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

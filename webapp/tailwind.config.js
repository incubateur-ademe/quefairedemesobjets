/** @type {import('tailwindcss').Config | null} */
import DSFRColors from "./dsfr_hacks/colors"
import usedColors from "./dsfr_hacks/used_colors"

module.exports = {
  content: [
    "templates/**/*.html",
    "static/to_compile/**/*.{js,ts,svg,css}",
    "./**/forms.py",
    "./dsfr_hacks/used_icons.js",
  ],
  prefix: "qf-",
  corePlugins: {
    preflight: false,
  },
  safelist: [
    "sm:qf-max-w-[596px]",
    "sm:qf-min-w-[600px]",
    "sm:qf-w-[250px]",
    "sm:qf-w-[400px]",
    "qf-top-3/4",
    "qf-scale-115",

    {
      pattern: new RegExp(`qf-(text|border|bg)-(${usedColors.join("|")})`),
    },
  ],
  theme: {
    spacing: {
      // https://www.systeme-de-design.gouv.fr/elements-d-interface/fondamentaux-techniques/espacements
      0: 0,
      "1v": "0.25rem",
      "0-5v": "0.125rem",
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
      colors: {
        // https://www.systeme-de-design.gouv.fr/elements-d-interface/fondamentaux-de-l-identite-de-l-etat/couleurs-palette
        info: {
          "975-active": "#c2cfff",
        },
        black: "black",
        white: "white",
        focus: "#0a76f6", // Hardcoded in dsfr https://github.com/GouvernementFR/dsfr/blob/b828f9e99cde96062d3d6eebc17a6b654994285b/src/module/color/variable/_static.scss#L3
        ...DSFRColors,
      },
      height: {
        header: "var(--header-height)",
        "main-svh": "calc(100svh - var(--header-height))",
        "main-vh": "calc(100vh - var(--header-height))",
      },
      spacing: {
        header: "var(--header-height)",
        footer: "var(--footer-height)",
      },
      maxWidth: {
        readable: "80ch",
        "120w": "60rem",
      },
      screens: {
        xs: "320px",
        xsm: "360px",
        nolegend: "1024px",
      },
      minWidth: ({ theme }) => ({ ...theme("spacing") }),
      keyframes: {
        blink: {
          "0%": { opacity: 0 },
          "40%": { opacity: 1 },
          "60%": { opacity: 1 },
          "100%": { opacity: 0 },
        },
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
        blink: "blink 1s infinite",
        "modal-appear": "modal-appear 0.2s",
      },
      backgroundImage: {
        "gradient-infotri": "linear-gradient(49deg, transparent 57%, #ececfe 78%)",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
}

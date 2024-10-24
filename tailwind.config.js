/** @type {import('tailwindcss').Config | null} */

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
    "sm:qfdmo-max-w-[596px]",
    "sm:qfdmo-min-w-[600px]",
    "sm:qfdmo-w-[250px]",
    "sm:qfdmo-w-[400px]",
    "sm:qfdmo-w-[596px]",
    "sm:qfdmo-w-fit",
    "qfdmo-bg-beige-gris-galet",
    "qfdmo-bg-blue-cumulus-sun-368",
    "qfdmo-bg-blue-cumulus",
    "qfdmo-bg-blue-ecume-850",
    "qfdmo-bg-blue-ecume",
    "qfdmo-bg-brown-cafe-creme-main-782",
    "qfdmo-bg-brown-cafe-creme",
    "qfdmo-bg-brown-caramel",
    "qfdmo-bg-brown-opera",
    "qfdmo-bg-green-500",
    "qfdmo-bg-green-archipel",
    "qfdmo-bg-green-bourgeon-850",
    "qfdmo-bg-green-bourgeon",
    "qfdmo-bg-green-emeraude",
    "qfdmo-bg-green-menthe-850",
    "qfdmo-bg-green-menthe-main-548",
    "qfdmo-bg-green-menthe-sun-373",
    "qfdmo-bg-green-menthe",
    "qfdmo-bg-green-tilleul-verveine",
    "qfdmo-bg-orange-terre-battue-main-645",
    "qfdmo-bg-orange-terre-battue",
    "qfdmo-bg-pink-macaron",
    "qfdmo-bg-pink-tuile-850",
    "qfdmo-bg-pink-tuile",
    "qfdmo-bg-purple-glycine-main-494",
    "qfdmo-bg-purple-glycine",
    "qfdmo-bg-red-500",
    "qfdmo-bg-yellow-moutarde-850",
    "qfdmo-bg-yellow-moutarde",
    "qfdmo-bg-yellow-tournesol",
    "qfdmo-bottom-5",
    "qfdmo-flex-col",
    "qfdmo-flex-row",
    "qfdmo-gap-4",
    "qfdmo-grid-cols-4",
    "qfdmo-h-[95%]",
    "qfdmo-h-10",
    "qfdmo-inline-grid",
    "qfdmo-italic",
    "qfdmo-justify-between",
    "qfdmo-m-1w",
    "qfdmo-w-full",
    "qfdmo-text-white",
    "qfdmo-rounded-full",
    "qfdmo-underline",
    "hover:qfdmo-decoration-[1.5px]",
    "qfdmo-underline-offset-[3px]",
  ],
  theme: {
    colors: {
      // https://www.systeme-de-design.gouv.fr/elements-d-interface/fondamentaux-de-l-identite-de-l-etat/couleurs-palette
      info: {
        "975-active": "#c2cfff",
      },
      black: "black",
      white: "white",
      "beige-gris-galet": "#AEA397",
      "blue-cumulus-sun-368-active": "#7996e6",
      "blue-cumulus-sun-368-hover": "#5982e0",
      "blue-cumulus-sun-368": "#3558A2",
      "blue-cumulus": "#417DC4",
      "blue-ecume-850-active": "#6b93f6",
      "blue-ecume-850-hover": "#8ba7f8",
      "blue-ecume-850": "#bfccfb",
      "blue-ecume": "#465F9D",
      "blue-france-850-hover": "#a1a1f8",
      "blue-france-850": "#cacafb",
      "blue-france-925-active": "#adadf9",
      "blue-france-925-hover": "#c1c1fb",
      "blue-france-925": "#e3e3fd",
      "blue-france-950-hover": "#cecefc",
      "blue-france-950": "#ececfe",
      "blue-france-975-hover": "#dcdcfc",
      "blue-france-975": "#f5f5fe",
      "blue-france-main-525-active": "#aeaef9",
      "blue-france-main-525-hover": "#9898f8",
      "blue-france-main-525": "#6a6af4",
      "blue-france-sun-113": "#000091",
      "blue-france": "#2323ff",
      "brown-cafe-creme-main-782-active": "#8b7954",
      "brown-cafe-creme-main-782-hover": "#a38e63",
      "brown-cafe-creme-main-782": "#D1B781",
      "brown-cafe-creme": "#D1B781",
      "brown-caramel": "#C08C65",
      "brown-opera": "#BD987A",
      "green-archipel": "#009099",
      "green-bourgeon-850-active": "#679e3b",
      "green-bourgeon-850-hover": "#77b645",
      "green-bourgeon-850": "#95e257",
      "green-bourgeon": "#68A532",
      "green-emeraude": "#00A95F",
      "green-menthe-850-active": "#4f9d91",
      "green-menthe-850-hover": "#5bb5a7",
      "green-menthe-850": "#73e0cf",
      "green-menthe-main-548-active": "#00e2cb",
      "green-menthe-main-548-hover": "#00c7b3",
      "green-menthe-main-548": "#009081",
      "green-menthe-sun-373-active": "#62a9a2",
      "green-menthe-sun-373-hover": "#53918c",
      "green-menthe-sun-373": "#37635f",
      "green-menthe": "#009081",
      "green-tilleul-verveine": "#B7A73F",
      "grey-50": "#161616",
      "grey-200": "#3a3a3a",
      "grey-425": "#666666",
      "grey-850": "#cecece",
      "grey-900": "#dddddd",
      "grey-925": "#e5e5e5",
      "grey-950": "#eeeeee",
      "grey-975": "#f6f6f6",
      "info-425": "#0063CB",
      "light-gray": "#e5e5e5",
      "orange-terre-battue-main-645-active": "#f4bfb1",
      "orange-terre-battue-main-645-hover": "#f1a892",
      "orange-terre-battue-main-645": "#E4794A",
      "orange-terre-battue": "#E4794A",
      "pink-macaron": "#E18B76",
      "pink-tuile-850-active": "#fa7659",
      "pink-tuile-850-hover": "#fb907d",
      "pink-tuile-850": "#fcbfb7",
      "pink-tuile": "#CE614A",
      "purple-glycine-main-494-active": "#db9cd6",
      "purple-glycine-main-494-hover": "#d282cd",
      "purple-glycine-main-494": "#A558A0",
      "purple-glycine": "#A558A0",
      "red-500": "#EB4444",
      "yellow-moutarde-850-active": "#b18a26",
      "yellow-moutarde-850-hover": "#cb9f2d",
      "yellow-moutarde-850": "#fcc63a",
      "yellow-moutarde": "#C3992A",
      "yellow-tournesol": "#cab300",
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
      },
      animation: {
        wave: "wave 1.5s linear",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
}

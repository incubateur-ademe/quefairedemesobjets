/** @type {import('tailwindcss').Config | null} */

module.exports = {
    content: [
        "jinja2/*.html",
        "jinja2/**/*html",
        "jinja2/**/**/*html",
        "templates/**/*html",
        "static/to_compile/**/*{j,t}s",
    ],
    prefix: "qfdmo-",
    corePlugins: {
        preflight: false,
    },
    safelist: [
        "qfdmo-bg-beige-gris-galet",
        "qfdmo-bg-blue-cumulus",
        "qfdmo-bg-blue-ecume",
        "qfdmo-bg-brown-cafe-creme",
        "qfdmo-bg-brown-caramel",
        "qfdmo-bg-brown-opera",
        "qfdmo-bg-green-500",
        "qfdmo-bg-green-archipel",
        "qfdmo-bg-green-bourgeon",
        "qfdmo-bg-green-emeraude",
        "qfdmo-bg-green-menthe",
        "qfdmo-bg-green-tilleul-verveine",
        "qfdmo-bg-orange-terre-battue",
        "qfdmo-bg-pink-macaron",
        "qfdmo-bg-pink-tuile",
        "qfdmo-bg-purple-glycine",
        "qfdmo-bg-red-500",
        "qfdmo-bg-yellow-moutarde",
        "qfdmo-bg-yellow-tournesol",
        "qfdmo-flex-col",
        "qfdmo-flex-row",
        "qfdmo-italic",
        "qfdmo-justify-between",
        "qfdmo-h-10",
        "qfdmo-bottom-5",
        "qfdmo-w-full",
        "md:qfdmo-w-fit",
        "md:qfdmo-w-[300px]",
        "md:qfdmo-w-[400px]",
        "md:qfdmo-min-w-[600px]",
    ],
    theme: {
        colors: {
            // https://www.systeme-de-design.gouv.fr/elements-d-interface/fondamentaux-de-l-identite-de-l-etat/couleurs-palette
            white: "white",
            info: {
                "975-active": "#c2cfff",
            },
            "blue-france-sun-113": "#000091",
            "blue-france": "#2323ff",
            "blue-france-main-525": "#6a6af4",
            "blue-france-main-525-hover": "#9898f8",
            "blue-france-main-525-active": "#aeaef9",
            "blue-france-975": "#f5f5fe",
            "blue-france-975-hover": "#dcdcfc",
            "blue-france-950": "#ececfe",
            "blue-france-950-hover": "#cecefc",
            "blue-france-925": "#e3e3fd",
            "blue-france-925-active": "#adadf9",
            "blue-france-925-hover": "#c1c1fb",
            "blue-france-850": "#cacafb",
            "blue-france-850-hover": "#a1a1f8",
            "light-gray": "#e5e5e5",
            "green-tilleul-verveine": "#B7A73F",
            "green-bourgeon": "#68A532",
            "green-emeraude": "#00A95F",
            "green-menthe": "#009081",
            "green-archipel": "#009099",
            "blue-ecume": "#465F9D",
            "blue-cumulus": "#417DC4",
            "purple-glycine": "#A558A0",
            "pink-macaron": "#E18B76",
            "pink-tuile": "#CE614A",
            "yellow-tournesol": "#cab300",
            "yellow-moutarde": "#C3992A",
            "orange-terre-battue": "#E4794A",
            "brown-cafe-creme": "#D1B781",
            "brown-caramel": "#C08C65",
            "brown-opera": "#BD987A",
            "beige-gris-galet": "#AEA397",
            "red-500": "#EB4444",
            "grey-975": "#f6f6f6",
            "grey-950": "#eeeeee",
            "grey-925": "#e5e5e5",
            "grey-900": "#dddddd",
            "grey-850": "#cecece",
            "grey-200": "#3a3a3a",
        },
        maxWidth: {
            readable: "80ch",
            "120w": "60rem",
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
            screens: {
                xs: "320px",
                xsm: "360px",
            },
            aria: {
                // Remove when https://github.com/tailwindlabs/tailwindcss/pull/10966 in a release
                busy: "busy=true",
            },
            minWidth: ({ theme }) => ({ ...theme("spacing") }),
        },
    },
    plugins: [],
}

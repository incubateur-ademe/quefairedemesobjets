/** @type {import('tailwindcss').Config} */
module.exports = {
    content: ["jinja2/**/*html", "static/to_compile/**/*{j,t}s"],
    prefix: "myapp-",
    corePlugins: {
        preflight: false,
    },
    theme: {
        colors: {
            // https://www.systeme-de-design.gouv.fr/elements-d-interface/fondamentaux-de-l-identite-de-l-etat/couleurs-palette
            white: "white",
            info: {
                "975-active": "#c2cfff",
            },
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
            aria: {
                // Remove when https://github.com/tailwindlabs/tailwindcss/pull/10966 in a release
                busy: "busy=true",
            },
            minWidth: ({ theme }) => ({ ...theme("spacing") }),
        },
    },
    plugins: [],
}

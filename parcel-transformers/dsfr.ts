import { Transformer } from "@parcel/plugin"
import { PurgeCSS } from "purgecss"
import tailwindConfig from "../tailwind.config.js"

export default new Transformer({
  async transform({ asset }) {
    // Retrieve the asset's source code and source map.
    let source = await asset.getCode()
    let sourceMap = await asset.getMap()

    if (asset.filePath.endsWith(".css")) {
      const purgeCSSResults = await new PurgeCSS().purge({
        content: [
          "templates/**/*.html",
          "jinja2/**/*.html",
          "static_to_compile/**/*.css",
          "static/to_compile/**/*.ts"
        ],
        css: [{ raw: source }],
        safelist: ["htm", "body", ...tailwindConfig.safelist],
      })

      // source = purgeCSSResults
      //   .map((purged) => {
      //     return purged.css
      //   })
      //   .join("\n")
    }

    asset.setCode(source)
    asset.setMap(sourceMap)

    return [asset]
  },
})

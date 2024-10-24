import { Transformer } from "@parcel/plugin"
import { PurgeCSS } from "purgecss"
import purgeJs from "purgecss-from-js"
import purgeHtml from "purgecss-from-html"

import tailwindConfig from "../tailwind.config.js"

export default new Transformer({
  async transform({ asset }) {
    // Retrieve the asset's source code and source map.
    let source = await asset.getCode()
    let sourceMap = await asset.getMap()

    if (asset.filePath.includes("@gouvfr/dsfr") && asset.filePath.endsWith(".css")) {
      try {
        const purgeCSSResults = await new PurgeCSS().purge({
          content: ["**/*.html"],
          css: [{ raw: source }],
          extractors: [
            {
              extractor: purgeJs,
              extensions: ["js", "ts"],
            },
            {
              extractor: purgeHtml,
              extensions: ["html"],
            },
          ],
          safelist: tailwindConfig.safelist,
        })
        source = purgeCSSResults
          .map((purged) => {
            return purged.css
          })
          .join("\n")
      } catch (e) {
        console.error(e)
      }
    }

    asset.setCode(source)
    asset.setMap(sourceMap)

    return [asset]
  },
})

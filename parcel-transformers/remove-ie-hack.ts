
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
      // C'est un hack internet explorer ajouté dans le dsfr dont on a pas besoin...
      // source = source.replace("min-width:")
      // source = source.replace(/and \(min-width: 0\\0\)/g, '');
    }

    asset.setCode(source)
    asset.setMap(sourceMap)

    return [asset]
  },
})

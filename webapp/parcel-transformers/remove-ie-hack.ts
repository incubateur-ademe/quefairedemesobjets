import { Transformer } from "@parcel/plugin"
import postcss from "postcss"

export default new Transformer({
  async transform({ asset }) {
    // Retrieve the asset's source code and source map.
    let source = await asset.getCode()
    let sourceMap = await asset.getMap()

    if (asset.filePath.endsWith(".css")) {
      // This is a IE hack we do not need to support.
      // Setting a unrealistic value of 100000000 ensures
      // this media query will never run.
      const regex = /0\\0/g;
      source = source.replaceAll(regex, "1000000000")
    }

    asset.setCode(source)
    asset.setMap(sourceMap)

    return [asset]
  },
})

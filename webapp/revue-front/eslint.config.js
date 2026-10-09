import prettierRecommended from "eslint-plugin-prettier/recommended"
import reactHooks from "eslint-plugin-react-hooks"
import tseslint from "typescript-eslint"

export default tseslint.config(
  { ignores: ["src/api/schema.d.ts", "src/api/openapi.json"] },
  {
    files: ["src/**/*.{ts,tsx}"],
    extends: [tseslint.configs.recommended, reactHooks.configs.flat.recommended],
    languageOptions: {
      parserOptions: {
        projectService: true,
        tsconfigRootDir: import.meta.dirname,
      },
    },
  },
  prettierRecommended,
)

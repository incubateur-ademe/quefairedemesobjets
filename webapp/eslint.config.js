import prettierRecommended from "eslint-plugin-prettier/recommended"
import tseslint from "typescript-eslint"

export default tseslint.config(
  // The review screen is an independent package with its own ESLint config
  { ignores: ["revue-front/**"] },
  {
    files: ["static/to_compile/**/*.ts"],
    extends: [tseslint.configs.recommended],
    languageOptions: {
      parserOptions: {
        projectService: true,
        tsconfigRootDir: import.meta.dirname,
      },
    },
  },
  prettierRecommended,
)

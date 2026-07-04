// Semantic CSS linting for the plain-CSS files under src/ (the `lint:css`
// script scopes to `src/**/*.css`); scoped <style> blocks in .astro
// components are out of scope. Extends stylelint-config-standard but turns
// off the rules that fight oxfmt (which owns formatting).
export default {
  extends: ["stylelint-config-standard"],
  rules: {
    "no-descending-specificity": null,
    "comment-empty-line-before": null,
    "custom-property-empty-line-before": null,
    "value-keyword-case": null,
    "import-notation": null,
    "custom-property-pattern": null, // --at-* theme tokens
  },
};

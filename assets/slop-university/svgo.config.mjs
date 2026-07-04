// svgo config for the Slop University lockups.
//
// CRITICAL: keep the viewBox. typst's `image()` scales the lockup by its
// viewBox -- strip it and masthead placement breaks. svgo 4's preset-default no
// longer includes removeViewBox, so plain preset-default preserves it (build-all
// pins svgo@latest). Verify after any svgo bump: `grep viewBox slop-*.svg`.
export default {
  multipass: true,
  plugins: ["preset-default"],
};

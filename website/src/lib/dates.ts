// Shared en-AU date formatters. No imports, so client scripts can use them too.
// The PURE annotations let a bundler drop whichever formatter a script never uses.

/** "19 October 2026". */
export const dayMonthYear = /* @__PURE__ */ new Intl.DateTimeFormat("en-AU", {
  day: "numeric",
  month: "long",
  year: "numeric",
});

/** "October 2026". */
export const monthYear = /* @__PURE__ */ new Intl.DateTimeFormat("en-AU", {
  month: "long",
  year: "numeric",
});

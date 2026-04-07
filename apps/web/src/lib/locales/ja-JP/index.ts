import { enUS } from "../en-US";
import { mergeLocale } from "../merge-locale";
import { jaJPCore } from "./sections/core";
import { jaJPSettings } from "./sections/settings";

export const jaJP = mergeLocale(enUS, {
  ...jaJPCore,
  ...jaJPSettings,
});

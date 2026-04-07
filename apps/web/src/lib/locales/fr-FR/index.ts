import { enUS } from "../en-US";
import { mergeLocale } from "../merge-locale";
import { frFRCore } from "./sections/core";
import { frFRSettings } from "./sections/settings";

export const frFR = mergeLocale(enUS, {
  ...frFRCore,
  ...frFRSettings,
});

import { enUS } from "../en-US";
import { mergeLocale } from "../merge-locale";
import { itITCore } from "./sections/core";
import { itITSettings } from "./sections/settings";

export const itIT = mergeLocale(enUS, {
  ...itITCore,
  ...itITSettings,
});

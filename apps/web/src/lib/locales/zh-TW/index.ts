import { enUS } from "../en-US";
import { mergeLocale } from "../merge-locale";
import { zhTWCore } from "./sections/core";
import { zhTWSettings } from "./sections/settings";

export const zhTW = mergeLocale(enUS, {
  ...zhTWCore,
  ...zhTWSettings,
});

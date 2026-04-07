import { enUS } from "../en-US";
import { mergeLocale } from "../merge-locale";
import { ruRUCore } from "./sections/core";
import { ruRUSettings } from "./sections/settings";

export const ruRU = mergeLocale(enUS, {
  ...ruRUCore,
  ...ruRUSettings,
});

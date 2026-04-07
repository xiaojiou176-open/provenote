import { enUS } from "../en-US";
import { mergeLocale } from "../merge-locale";
import { zhCNCore } from "./sections/core";
import { zhCNSettings } from "./sections/settings";

export const zhCN = mergeLocale(enUS, {
  ...zhCNCore,
  ...zhCNSettings,
});

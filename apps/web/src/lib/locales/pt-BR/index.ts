import { enUS } from "../en-US";
import { mergeLocale } from "../merge-locale";
import { ptBRCore } from "./sections/core";
import { ptBRSettings } from "./sections/settings";

export const ptBR = mergeLocale(enUS, {
  ...ptBRCore,
  ...ptBRSettings,
});

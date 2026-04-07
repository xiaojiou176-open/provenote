type LocaleTree = Record<string, unknown>;

type DeepPartial<T> = {
  [K in keyof T]?: T[K] extends LocaleTree ? DeepPartial<T[K]> : T[K];
};

export function mergeLocale<T extends LocaleTree>(base: T, overrides: DeepPartial<T>): T {
  const output: Record<string, unknown> = { ...base };

  for (const [key, value] of Object.entries(overrides)) {
    const current = output[key];
    if (
      current &&
      value &&
      typeof current === "object" &&
      typeof value === "object" &&
      !Array.isArray(current) &&
      !Array.isArray(value)
    ) {
      output[key] = mergeLocale(current as LocaleTree, value as DeepPartial<LocaleTree>);
      continue;
    }
    output[key] = value;
  }

  return output as T;
}

export type { DeepPartial, LocaleTree };

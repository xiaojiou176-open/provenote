const trimTrailingSlashes = (value: string) => value.replace(/\/+$/, "");

export function getRepositoryHomeUrl(): string | null {
  const rawValue = process.env.NEXT_PUBLIC_REPOSITORY_URL?.trim();
  if (!rawValue) {
    return null;
  }
  return trimTrailingSlashes(rawValue);
}

export function getRepositoryBlobUrl(repoRelativePath: string, anchor?: string): string | null {
  const repositoryUrl = getRepositoryHomeUrl();
  if (!repositoryUrl) {
    return null;
  }

  const normalizedPath = repoRelativePath.replace(/^\/+/, "");
  const normalizedAnchor = anchor ? `#${anchor.replace(/^#/, "")}` : "";
  return `${repositoryUrl}/blob/main/${normalizedPath}${normalizedAnchor}`;
}

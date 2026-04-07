function parsePayload(output) {
  if (typeof output === "object" && output !== null) {
    return output;
  }

  if (typeof output !== "string") {
    return {};
  }

  try {
    return JSON.parse(output);
  } catch {
    return {};
  }
}

module.exports = (output) => {
  const payload = parsePayload(output);
  const count = Number(payload.missing_count);
  const pass = Number.isFinite(count) && count === 0;

  return {
    pass,
    score: pass ? 1 : 0,
    reason: pass
      ? "missing_count==0"
      : `Expected missing_count==0, got ${JSON.stringify(payload.missing_count)}`,
  };
};

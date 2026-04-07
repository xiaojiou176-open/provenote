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
  const pass = payload.no_uncited_claims === true;

  return {
    pass,
    score: pass ? 1 : 0,
    reason: pass
      ? "no_uncited_claims=true"
      : `Expected no_uncited_claims=true, got ${JSON.stringify(payload.no_uncited_claims)}`,
  };
};

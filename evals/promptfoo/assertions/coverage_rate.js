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
  const rate = Number(payload.coverage_rate);
  const pass = Number.isFinite(rate) && rate === 1;

  return {
    pass,
    score: pass ? 1 : 0,
    reason: pass
      ? "coverage_rate==1.0"
      : `Expected coverage_rate==1.0, got ${JSON.stringify(payload.coverage_rate)}`,
  };
};

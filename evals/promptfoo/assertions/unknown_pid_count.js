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
  const count = Number(payload.unknown_pid_count);
  const pass = Number.isFinite(count) && count === 0;

  return {
    pass,
    score: pass ? 1 : 0,
    reason: pass
      ? "unknown_pid_count==0"
      : `Expected unknown_pid_count==0, got ${JSON.stringify(payload.unknown_pid_count)}`,
  };
};

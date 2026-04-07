const path = require("node:path");

// Set default PORT if not already set
if (!process.env.PORT) {
  process.env.PORT = "8502";
}

const nextDistDir = process.env.NEXT_DIST_DIR || ".runtime-cache/build/next";

// Start the Next.js standalone server using the declared dist dir.
require(path.join(__dirname, nextDistDir, "standalone/server.js"));

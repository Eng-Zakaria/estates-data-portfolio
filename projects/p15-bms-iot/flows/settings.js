/**
 * P15 Node-RED settings: loads the shared ingestion contract and the point
 * registry into `env` so the flow and the Python tests read the same files.
 *
 * Mounted read-only at /data/settings.js by docker-compose. Everything here is
 * demo configuration: credentials come from the environment.
 */
const fs = require("fs");
const path = require("path");

// settings.js is mounted at /data/settings.js, with the contract, the registry
// and the flow files alongside it under /data/contracts and /data/src
const ROOT = process.env.P15_DATA_ROOT || "/data";

const rules = JSON.parse(fs.readFileSync(path.join(ROOT, "contracts", "validation_rules.json"), "utf8"));

// Minimal CSV parse: the registry has no quoted commas, so split() is enough
// and avoids pulling in a dependency for a 273-row file.
function parseCsv(text) {
  const [header, ...lines] = text.trim().split("\n");
  const cols = header.split(",");
  return lines.map((line) => {
    const values = line.split(",");
    const row = {};
    cols.forEach((name, i) => {
      row[name] = values[i];
    });
    return row;
  });
}

const registryRows = parseCsv(fs.readFileSync(path.join(ROOT, "src", "point_registry.csv"), "utf8"));
const pointsByTopic = {};
for (const row of registryRows) {
  pointsByTopic[row.topic] = row.point_id;
}

// Node-RED 4 loads whatever flowFile points at (verified on 4.0.9: it does not
// silently ignore this key). The entrypoint copies flows/p15_bms.json to
// /data/flows.json, and P15_DATA_ROOT points at the read-only project mount.
module.exports = {
  flowFile: "flows.json",
  flowFilePretty: true,
  editorTheme: { page: { title: "P15 BMS ingest" } },
  functionGlobalContext: {
    BMS_RULES: rules,
    BMS_POINTS_BY_TOPIC: pointsByTopic,
    BMS_REGISTRY_ROWS: registryRows,
  },
  // credentials: env only, never hardcoded in flows
  adminAuth: {
    type: "credentials",
    users: [
      {
        username: "admin",
        password: process.env.NR_PASSWORD || "demo",
        permissions: "*",
      },
    ],
  },
};

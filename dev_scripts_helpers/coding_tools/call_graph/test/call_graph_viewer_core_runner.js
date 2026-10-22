// Run one function of `call_graph_viewer_core.js` on a JSON call graph and print
// the result as JSON, so a Python unit test can check the browser logic.
//
// Usage: node call_graph_viewer_core_runner.js <core.js> <graph.json> <command> [args]
//
// Commands:
// - hood <seed> <radius> <dir>: hops of the symbols around a symbol
// - project <seed> <radius> <dir>: drawn nodes and edges around a symbol
// - box <class> <selected> <hit>: rows of the UML box of a class
// - rowat <class> <y>: row of the box at a vertical offset
// - state <hash>: decode a URL hash and encode it back
const fs = require("fs");

const [coreFile, dataFile, command, ...args] = process.argv.slice(2);
const core = require(coreFile);
const model = core.buildModel(JSON.parse(fs.readFileSync(dataFile, "utf8")));

// Print "inf" for the symbols that are beyond reach (JSON has no Infinity).
function plainHops(hop) {
  const res = {};
  Object.keys(hop)
    .sort()
    .forEach((id) => {
      res[id] = isFinite(hop[id]) ? hop[id] : "inf";
    });
  return res;
}

function hood(seed, radius, dir) {
  const seeds = core.seedsFor(model, seed);
  return core.neighborhood(model, seeds, parseInt(radius, 10), dir);
}

let result;
if (command === "hood") {
  result = plainHops(hood(...args));
} else if (command === "project") {
  const proj = core.project(model, hood(...args));
  result = {
    nodes: proj.nodes.map((n) => n.id + " (module " + n.module + ")").sort(),
    edges: proj.edges.map((e) => e.id + " x" + e.count).sort(),
  };
} else if (command === "box") {
  const hits = {};
  if (args[2]) {
    hits[args[2]] = 1;
  }
  const box = core.classBox(model, args[0], hits, args[1], false);
  result = {
    size: box.w + "x" + box.h,
    attrs: box.attrs.map((a) => a.text),
    methods: box.methods.map(
      (m) => m.text + (m.hit ? " [hit]" : "") + (m.selected ? " [selected]" : "")
    ),
  };
} else if (command === "rowat") {
  const box = core.classBox(model, args[0], {}, "", false);
  result = core.rowAt(box, parseFloat(args[1]));
} else if (command === "state") {
  const state = core.decodeState(args[0], { node: "", n: 1, dir: "both" });
  result = { state: state, hash: core.encodeState(state) };
}
console.log(JSON.stringify(result, null, 2));

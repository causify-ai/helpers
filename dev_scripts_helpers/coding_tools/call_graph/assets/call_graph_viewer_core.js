/*
 * Pure logic of the call graph viewer: no DOM, no Cytoscape.
 *
 * It is loaded as a browser global (`CGCore`) by the generated page and with
 * `require()` by the Node-based unit test, so every function here must stay free
 * of browser APIs. See `call_graph_viewer.README.md`.
 */
(function (root, factory) {
  if (typeof module === "object" && module.exports) {
    module.exports = factory();
  } else {
    root.CGCore = factory();
  }
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  // ###########################################################################
  // Model
  // ###########################################################################

  // Index the symbols and the edges of the extracted data.
  function buildModel(data) {
    var model = {
      data: data,
      symbols: {},
      children: {},
      out: {},
      inn: {},
    };
    data.symbols.forEach(function (s) {
      model.symbols[s.id] = s;
      (model.children[s.parent] = model.children[s.parent] || []).push(s.id);
    });
    data.edges.forEach(function (e) {
      (model.out[e.src] = model.out[e.src] || []).push(e);
      (model.inn[e.dst] = model.inn[e.dst] || []).push(e);
    });
    return model;
  }

  // Get the symbol drawn as a node: a method lives inside its class box.
  function ownerOf(model, id) {
    var sym = model.symbols[id];
    return sym.kind === "method" ? sym.parent : id;
  }

  // Get the module enclosing a symbol.
  function moduleOf(model, id) {
    var sym = model.symbols[id];
    while (sym.kind !== "module" && sym.parent) {
      sym = model.symbols[sym.parent];
    }
    return sym.id;
  }

  // List the descendants of a symbol (all the levels).
  function descendantsOf(model, id) {
    var res = [];
    (model.children[id] || []).forEach(function (child) {
      res.push(child);
      Array.prototype.push.apply(res, descendantsOf(model, child));
    });
    return res;
  }

  // Resolve user text into a symbol id: the full id, else a unique dotted suffix,
  // else a unique substring. Return "" if there is no unique match.
  function findSymbol(model, query) {
    query = query.trim();
    if (!query) {
      return "";
    }
    if (model.symbols[query]) {
      return query;
    }
    var ids = Object.keys(model.symbols);
    var matches = ids.filter(function (id) {
      return id.endsWith("." + query);
    });
    if (matches.length !== 1) {
      matches = ids.filter(function (id) {
        return id.indexOf(query) >= 0;
      });
    }
    return matches.length === 1 ? matches[0] : "";
  }

  // ###########################################################################
  // Neighborhood
  // ###########################################################################

  // Get the symbols a selection starts from: a class brings its methods and a
  // module brings everything it defines.
  function seedsFor(model, id) {
    var sym = model.symbols[id];
    var seeds = [id];
    if (sym.kind === "class") {
      seeds = seeds.concat(
        (model.children[id] || []).filter(function (c) {
          return model.symbols[c].kind === "method";
        })
      );
    } else if (sym.kind === "module") {
      seeds = descendantsOf(model, id);
    }
    return seeds;
  }

  // Compute the number of connections between the seeds and every symbol.
  //
  // - radius: max number of connections, 0 means everything
  // - dir: "both", "callers" (follow edges backwards), "callees" (forwards)
  // Return a map id -> hops. With radius 0 the symbols beyond reach get Infinity.
  function neighborhood(model, seeds, radius, dir) {
    var hop = {};
    var frontier = [];
    seeds.forEach(function (s) {
      hop[s] = 0;
      frontier.push(s);
    });
    var level = 0;
    while (frontier.length > 0 && (radius === 0 || level < radius)) {
      level += 1;
      var next = [];
      frontier.forEach(function (id) {
        var neighbors = [];
        if (dir !== "callers") {
          (model.out[id] || []).forEach(function (e) {
            neighbors.push(e.dst);
          });
        }
        if (dir !== "callees") {
          (model.inn[id] || []).forEach(function (e) {
            neighbors.push(e.src);
          });
        }
        neighbors.forEach(function (n) {
          if (!(n in hop)) {
            hop[n] = level;
            next.push(n);
          }
        });
      });
      frontier = next;
    }
    if (radius === 0) {
      // Everything is shown, whether reachable or not.
      Object.keys(model.symbols).forEach(function (id) {
        if (model.symbols[id].kind !== "module" && !(id in hop)) {
          hop[id] = Infinity;
        }
      });
    }
    return hop;
  }

  // Project the member-level neighborhood onto the drawn nodes and edges.
  //
  // Methods collapse into their class and the calls between two nodes collapse
  // into one `uses` edge that keeps the underlying calls in `items`.
  function project(model, hop) {
    var nodes = {};
    Object.keys(hop).forEach(function (id) {
      var sym = model.symbols[id];
      if (sym.kind === "module") {
        return;
      }
      var owner = ownerOf(model, id);
      if (!nodes[owner]) {
        nodes[owner] = {
          id: owner,
          kind: model.symbols[owner].kind,
          module: moduleOf(model, owner),
          hits: {},
          selfCalls: 0,
        };
      }
      nodes[owner].hits[id] = hop[id];
    });
    var edges = {};
    model.data.edges.forEach(function (e) {
      if (!(e.src in hop) || !(e.dst in hop)) {
        return;
      }
      var so = ownerOf(model, e.src);
      var to = ownerOf(model, e.dst);
      var isUse = e.kind === "call" || e.kind === "instantiate";
      if (isUse && so === to) {
        nodes[so].selfCalls += 1;
        return;
      }
      var kind = isUse ? "uses" : e.kind;
      var key = kind + "|" + so + "|" + to;
      if (!edges[key]) {
        edges[key] = { id: key, src: so, dst: to, kind: kind, items: [] };
      }
      edges[key].items.push(e);
    });
    return {
      nodes: Object.keys(nodes).map(function (k) {
        return nodes[k];
      }),
      edges: Object.keys(edges).map(function (k) {
        edges[k].count = edges[k].items.length;
        return edges[k];
      }),
    };
  }

  // Pick the symbol to start from: a hub, so the first view is not empty.
  function mostConnected(model) {
    var best = "";
    var bestDegree = -1;
    Object.keys(model.symbols).forEach(function (id) {
      var kind = model.symbols[id].kind;
      if (kind === "module" || kind === "method") {
        return;
      }
      var degree = 0;
      seedsFor(model, id).forEach(function (s) {
        degree += (model.out[s] || []).length + (model.inn[s] || []).length;
      });
      if (degree > bestDegree) {
        best = id;
        bestDegree = degree;
      }
    });
    return best;
  }

  // Group the relations of a symbol by kind, for the "related" list.
  //
  // Return {calls, calledBy, bases, subclasses, composes, composedBy}, each a list
  // of {id, lines}, where `id` is the symbol at the other end.
  function related(model, id) {
    var res = {
      calls: [],
      calledBy: [],
      bases: [],
      subclasses: [],
      composes: [],
      composedBy: [],
    };
    var seeds = seedsFor(model, id);
    var inside = {};
    seeds.forEach(function (s) {
      inside[s] = true;
    });
    function add(list, other, lines) {
      var found = list.filter(function (x) {
        return x.id === other;
      })[0];
      if (found) {
        lines.forEach(function (l) {
          if (found.lines.indexOf(l) < 0) {
            found.lines.push(l);
          }
        });
      } else {
        list.push({ id: other, lines: lines.slice() });
      }
    }
    var table = {
      call: ["calls", "calledBy"],
      instantiate: ["calls", "calledBy"],
      inherit: ["bases", "subclasses"],
      compose: ["composes", "composedBy"],
    };
    seeds.forEach(function (s) {
      (model.out[s] || []).forEach(function (e) {
        if (!inside[e.dst]) {
          add(res[table[e.kind][0]], e.dst, e.lines);
        }
      });
      (model.inn[s] || []).forEach(function (e) {
        if (!inside[e.src]) {
          add(res[table[e.kind][1]], e.src, e.lines);
        }
      });
    });
    return res;
  }

  // ###########################################################################
  // UML class box
  // ###########################################################################

  var CHAR_W = 7.2; // Width of a 12px monospace character.
  var ROW_H = 15; // Must match `.cg-row` in the CSS.
  var PAD_X = 10;
  var COMPARTMENT_PAD = 3; // Top and bottom padding of a compartment.
  var COMPARTMENT_BORDER = 1; // Line separating two compartments.
  var MAX_METHODS = 14; // Methods shown in a collapsed box.

  // Format `name`, `(a: int) -> str` as the UML `name(a: int): str`.
  function formatSignature(name, signature) {
    var text = name + signature;
    var idx = text.lastIndexOf(" -> ");
    return idx >= 0 ? text.slice(0, idx) + ": " + text.slice(idx + 4) : text;
  }

  // Convert a name into its UML visibility mark.
  function visibilityOf(name) {
    if (name.startsWith("__") && !name.endsWith("__")) {
      return "-";
    }
    return name.startsWith("_") && !name.endsWith("__") ? "#" : "+";
  }

  // Describe the UML box of a class: header, attribute and method compartments,
  // the size in pixels, and the geometry used to map a click to a row.
  //
  // - hits: map member id -> hops for the members inside the neighborhood
  // - selected: id of the selected symbol (the class or one of its methods)
  // - expand: show all the methods
  function classBox(model, classId, hits, selected, expand) {
    var sym = model.symbols[classId];
    var stereotypes = [];
    sym.decorators.forEach(function (d) {
      if (d.indexOf("dataclass") >= 0) {
        stereotypes.push("dataclass");
      }
    });
    var attrs = sym.attrs.map(function (a) {
      var name = a.split(":")[0].trim();
      return { text: visibilityOf(name) + " " + a, id: "" };
    });
    var methods = (model.children[classId] || [])
      .filter(function (c) {
        return model.symbols[c].kind === "method";
      })
      .map(function (c) {
        var m = model.symbols[c];
        return {
          id: c,
          text: visibilityOf(m.name) + " " + formatSignature(m.name, m.signature),
          isStatic: m.decorators.indexOf("staticmethod") >= 0,
          isAbstract: m.decorators.some(function (d) {
            return d.indexOf("abstractmethod") >= 0;
          }),
          hit: isFinite(hits[c]),
          selected: c === selected,
        };
      });
    // Keep the members of interest when the box is collapsed.
    var hidden = 0;
    if (!expand && methods.length > MAX_METHODS) {
      var shown = methods.filter(function (m) {
        return m.hit || m.selected;
      });
      var rest = methods.filter(function (m) {
        return !(m.hit || m.selected);
      });
      shown = shown.concat(rest).slice(0, MAX_METHODS);
      hidden = methods.length - shown.length;
      methods = methods.filter(function (m) {
        return shown.indexOf(m) >= 0;
      });
    }
    var headerH = stereotypes.length > 0 ? 36 : 24;
    var extra = 2 * COMPARTMENT_PAD + COMPARTMENT_BORDER;
    var attrsH = Math.max(attrs.length, 1) * ROW_H + extra;
    var methodRows = methods.length + (hidden > 0 ? 1 : 0);
    var methodsH = Math.max(methodRows, 1) * ROW_H + extra;
    var chars = sym.name.length + 4;
    attrs.forEach(function (a) {
      chars = Math.max(chars, a.text.length);
    });
    methods.forEach(function (m) {
      chars = Math.max(chars, m.text.length);
    });
    return {
      id: classId,
      name: sym.name,
      stereotypes: stereotypes,
      attrs: attrs,
      methods: methods,
      hidden: hidden,
      selected: classId === selected,
      hit: isFinite(hits[classId]),
      headerH: headerH,
      attrsH: attrsH,
      methodsH: methodsH,
      w: Math.ceil(Math.max(110, chars * CHAR_W + 2 * PAD_X)),
      h: headerH + attrsH + methodsH,
    };
  }

  // Map a y offset inside a class box (0 at its top) to the row under it.
  //
  // Return {part: "header"|"attr"|"method"|"more", index}.
  function rowAt(box, y) {
    var hit = { part: "header", index: 0 };
    if (y >= box.headerH + box.attrsH) {
      var idx = Math.floor(
        (y - box.headerH - box.attrsH - COMPARTMENT_BORDER - COMPARTMENT_PAD) /
          ROW_H
      );
      idx = Math.max(idx, 0);
      hit =
        idx < box.methods.length
          ? { part: "method", index: idx }
          : box.hidden > 0 && idx === box.methods.length
          ? { part: "more", index: idx }
          : { part: "header", index: 0 };
    } else if (y >= box.headerH) {
      var aidx = Math.floor(
        (y - box.headerH - COMPARTMENT_BORDER - COMPARTMENT_PAD) / ROW_H
      );
      hit =
        aidx >= 0 && aidx < box.attrs.length
          ? { part: "attr", index: aidx }
          : { part: "header", index: 0 };
    }
    return hit;
  }

  // ###########################################################################
  // History state
  // ###########################################################################

  // Encode the navigation state into a URL hash, e.g., `node=a.b&n=1&dir=both`.
  function encodeState(state) {
    return (
      "node=" +
      encodeURIComponent(state.node) +
      "&n=" +
      state.n +
      "&dir=" +
      state.dir
    );
  }

  // Decode a URL hash into a state, filling the gaps from `defaults`.
  function decodeState(hash, defaults) {
    var state = { node: defaults.node, n: defaults.n, dir: defaults.dir };
    hash
      .replace(/^#/, "")
      .split("&")
      .forEach(function (kv) {
        var pair = kv.split("=");
        var value = decodeURIComponent(pair.slice(1).join("="));
        if (pair[0] === "node") {
          state.node = value;
        } else if (pair[0] === "n" && /^\d+$/.test(value)) {
          state.n = parseInt(value, 10);
        } else if (
          pair[0] === "dir" &&
          ["both", "callers", "callees"].indexOf(value) >= 0
        ) {
          state.dir = value;
        }
      });
    return state;
  }

  return {
    buildModel: buildModel,
    ownerOf: ownerOf,
    moduleOf: moduleOf,
    findSymbol: findSymbol,
    seedsFor: seedsFor,
    neighborhood: neighborhood,
    project: project,
    mostConnected: mostConnected,
    related: related,
    formatSignature: formatSignature,
    visibilityOf: visibilityOf,
    classBox: classBox,
    rowAt: rowAt,
    encodeState: encodeState,
    decodeState: decodeState,
    ROW_H: ROW_H,
    COMPARTMENT_PAD: COMPARTMENT_PAD,
  };
});

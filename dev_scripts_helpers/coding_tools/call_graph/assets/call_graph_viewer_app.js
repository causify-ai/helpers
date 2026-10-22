/*
 * Browser application of the call graph viewer: toolbar, Cytoscape graph, UML
 * class boxes, tooltips, code pane, and click history.
 *
 * The logic that does not need a DOM lives in `call_graph_viewer_core.js`. All the
 * data comes through `source`, the single seam a local server (v2) replaces.
 * See `call_graph_viewer.README.md`.
 */
(function () {
  "use strict";

  var Core = window.CGCore;
  var $ = function (id) {
    return document.getElementById(id);
  };

  // ###########################################################################
  // Data
  // ###########################################################################

  var data = JSON.parse($("cg-data").textContent);
  var files = JSON.parse($("cg-files").textContent);
  var model = Core.buildModel(data);

  // v1 embeds the highlighted code in the page. A server would `fetch()` it.
  var source = {
    getFile: function (path) {
      return Promise.resolve(files[path] || []);
    },
  };

  var MAX_TIP_ROWS = 16;
  var HUGE_GRAPH = 500;

  // Navigation state, stored in the browser history: it is what Back restores.
  var state = { node: "", n: 1, dir: "both" };
  // View options that are not part of the history.
  var ui = { layout: "fcose", group: true };

  function esc(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function shortName(id) {
    var sym = model.symbols[id];
    if (sym.kind === "method") {
      return model.symbols[sym.parent].name + "." + sym.name;
    }
    return sym.kind === "module" ? id : sym.name;
  }

  // ###########################################################################
  // Tooltip
  // ###########################################################################

  var tip = $("tip");

  function showTip(html, ev) {
    tip.innerHTML = html;
    tip.style.display = "block";
    var x = Math.min(ev.clientX + 14, window.innerWidth - tip.offsetWidth - 8);
    var y = ev.clientY + 16;
    if (y + tip.offsetHeight > window.innerHeight - 8) {
      y = Math.max(8, ev.clientY - tip.offsetHeight - 12);
    }
    tip.style.left = Math.max(8, x) + "px";
    tip.style.top = y + "px";
  }

  function hideTip() {
    tip.style.display = "none";
  }

  // Describe the interface of a symbol: signature, docstring, members.
  function symbolTip(id) {
    var s = model.symbols[id];
    var head;
    if (s.kind === "class") {
      head = "class " + s.name + (s.bases.length ? "(" + s.bases.join(", ") + ")" : "");
    } else if (s.kind === "module") {
      head = "module " + s.id;
    } else {
      head = "def " + s.name + s.signature;
    }
    var html = '<div class="sig">' + esc(head) + "</div>";
    if (s.decorators.length) {
      html += '<div class="meta">' + esc(s.decorators.map(function (d) { return "@" + d; }).join(" ")) + "</div>";
    }
    if (s.doc) {
      html += '<div class="doc">' + esc(s.doc.split("\n").slice(0, 7).join("\n")) + "</div>";
    }
    if (s.kind === "class") {
      var rows = s.attrs.slice(0, MAX_TIP_ROWS).map(function (a) {
        return Core.visibilityOf(a.split(":")[0].trim()) + " " + a;
      });
      var methods = (model.children[id] || []).filter(function (c) {
        return model.symbols[c].kind === "method";
      });
      rows = rows.concat(
        methods.slice(0, MAX_TIP_ROWS).map(function (c) {
          var m = model.symbols[c];
          return Core.visibilityOf(m.name) + " " + Core.formatSignature(m.name, m.signature);
        })
      );
      if (rows.length) {
        html += '<div class="list">' + esc(rows.join("\n")) + "</div>";
      }
    }
    var fanIn = (model.inn[id] || []).length;
    var fanOut = (model.out[id] || []).length;
    html +=
      '<div class="meta">' + esc(s.file) + ":" + s.line_start + " &middot; " +
      fanIn + " in, " + fanOut + " out</div>";
    return html;
  }

  function edgeTip(edge) {
    var items = edge.data("items");
    var label = { uses: "uses", inherit: "inherits from", compose: "composes" }[edge.data("kind")];
    var src = model.symbols[edge.data("source")].name;
    var dst = model.symbols[edge.data("target")].name;
    var html = '<div class="sig">' + esc(src + " " + label + " " + dst) + "</div>";
    var lines = items.slice(0, MAX_TIP_ROWS).map(function (e) {
      return shortName(e.src) + " -> " + shortName(e.dst) + " (line " + e.lines.join(", ") + ")";
    });
    if (items.length > MAX_TIP_ROWS) {
      lines.push("... +" + (items.length - MAX_TIP_ROWS) + " more");
    }
    return html + '<div class="list">' + esc(lines.join("\n")) + "</div>";
  }

  // ###########################################################################
  // UML class box
  // ###########################################################################

  function rowsHtml(rows, kind) {
    return rows
      .map(function (r) {
        var cls = "cg-row";
        if (r.isStatic) cls += " static";
        if (r.isAbstract) cls += " abstract";
        if (r.hit) cls += " hit";
        if (r.selected) cls += " sel";
        return '<div class="' + cls + '">' + esc(r.text) + "</div>";
      })
      .join("");
  }

  // Render the HTML of a class box (sizes come from `Core.classBox()`).
  function classHtml(box) {
    var html = '<div class="cg-class' + (box.selected ? " sel" : "") +
      '" style="width:' + box.w + "px;height:" + box.h + 'px">';
    html += '<div class="cg-head" style="height:' + box.headerH + 'px">';
    if (box.stereotypes.length) {
      html += '<span class="ster">&laquo;' + esc(box.stereotypes.join(", ")) + "&raquo;</span>";
    }
    html += '<span class="nm">' + esc(box.name) + "</span></div>";
    html += '<div class="cg-comp" style="height:' + box.attrsH + 'px">' + rowsHtml(box.attrs) + "</div>";
    html += '<div class="cg-comp" style="height:' + box.methodsH + 'px">' + rowsHtml(box.methods);
    if (box.hidden > 0) {
      html += '<div class="cg-row more">... +' + box.hidden + " more</div>";
    }
    return html + "</div></div>";
  }

  // ###########################################################################
  // Graph
  // ###########################################################################

  var CY_STYLE = [
    {
      // Compound module nodes have no `w`: their size follows their children.
      selector: "node[w]",
      style: { width: "data(w)", height: "data(h)", shape: "rectangle" },
    },
    {
      selector: 'node[kind = "module"]',
      style: {
        shape: "round-rectangle",
        "background-color": "#f3f4f6",
        "background-opacity": 0.7,
        "border-color": "#c3c8d0",
        "border-width": 1,
        label: "data(label)",
        "text-valign": "top",
        "text-halign": "center",
        "font-size": 11,
        color: "#6b7280",
        padding: 18,
      },
    },
    {
      selector: 'node[kind = "function"]',
      style: {
        shape: "round-rectangle",
        "background-color": "#e3f2fd",
        "border-color": "#1565c0",
        "border-width": 1.5,
        label: "data(label)",
        "text-valign": "center",
        "text-halign": "center",
        "font-family": "ui-monospace, Menlo, monospace",
        "font-size": 12,
        color: "#0d2a4d",
      },
    },
    {
      selector: 'node[kind = "function"][?private]',
      style: { "background-color": "#f5f9fd", "border-style": "dashed" },
    },
    {
      // The HTML box is drawn over this node. The fill keeps the whole box
      // clickable.
      selector: 'node[kind = "class"]',
      style: { "background-color": "#fffde7", "border-width": 0 },
    },
    {
      selector: "node.sel",
      style: {
        "underlay-color": "#ff9800",
        "underlay-opacity": 0.4,
        "underlay-padding": 9,
        "underlay-shape": "round-rectangle",
      },
    },
    {
      selector: 'node[kind = "function"].sel',
      style: { "border-color": "#e65100", "border-width": 2.5 },
    },
    {
      // Relation "uses" (a dependency): dashed line, open arrow.
      selector: "edge",
      style: {
        "curve-style": "bezier",
        width: "mapData(count, 1, 12, 1.2, 4)",
        "line-style": "dashed",
        "line-color": "#78808c",
        "target-arrow-color": "#78808c",
        "target-arrow-shape": "vee",
        "arrow-scale": 1.2,
      },
    },
    {
      // Inheritance: solid line, hollow triangle on the base class.
      selector: 'edge[kind = "inherit"]',
      style: {
        "line-style": "solid",
        width: 1.8,
        "line-color": "#1a237e",
        "target-arrow-color": "#1a237e",
        "target-arrow-shape": "triangle",
        "target-arrow-fill": "hollow",
        "arrow-scale": 1.7,
      },
    },
    {
      // Composition: solid line, filled diamond on the owner.
      selector: 'edge[kind = "compose"]',
      style: {
        "line-style": "solid",
        width: 1.8,
        "line-color": "#1b5e20",
        "source-arrow-color": "#1b5e20",
        "source-arrow-shape": "diamond",
        "source-arrow-fill": "filled",
        "target-arrow-shape": "none",
        "arrow-scale": 1.6,
      },
    },
    {
      selector: "edge.hl",
      style: {
        "line-color": "#e65100",
        "target-arrow-color": "#e65100",
        "source-arrow-color": "#e65100",
        "z-index": 9,
      },
    },
  ];

  cytoscape.use(window.cytoscapeFcose);

  var cy = cytoscape({
    container: $("cy"),
    elements: [],
    style: CY_STYLE,
    minZoom: 0.04,
    maxZoom: 3,
    wheelSensitivity: 0.25,
    boxSelectionEnabled: false,
    autounselectify: true,
  });

  cy.nodeHtmlLabel([
    {
      query: 'node[kind = "class"]',
      halign: "center",
      valign: "center",
      halignBox: "center",
      valignBox: "center",
      tpl: function (d) {
        return d.html;
      },
    },
  ]);

  // Identifies the shown nodes, edges, and sizes: the layout only runs when it
  // changes, so selecting a node already in view does not move the graph.
  var lastSig = "";

  function buildElements(proj, group) {
    var els = [];
    var modules = {};
    if (group) {
      proj.nodes.forEach(function (n) {
        modules[n.module] = true;
      });
      Object.keys(modules).forEach(function (m) {
        els.push({ group: "nodes", data: { id: "m:" + m, sid: m, kind: "module", label: m } });
      });
    }
    var selOwner = state.node ? Core.ownerOf(model, state.node) : "";
    proj.nodes.forEach(function (n) {
      var sym = model.symbols[n.id];
      var d = { id: n.id, sid: n.id, kind: sym.kind };
      if (group) {
        d.parent = "m:" + n.module;
      }
      if (sym.kind === "class") {
        var box = Core.classBox(model, n.id, n.hits, state.node, n.id === selOwner);
        d.box = box;
        d.w = box.w;
        d.h = box.h;
        d.html = classHtml(box);
      } else {
        d.label = sym.name + "()";
        d.w = Math.max(70, Math.ceil(d.label.length * 7.4 + 24));
        d.h = 28;
        d.private = Core.visibilityOf(sym.name) !== "+";
      }
      els.push({ group: "nodes", data: d });
    });
    proj.edges.forEach(function (e) {
      els.push({
        group: "edges",
        data: { id: e.id, source: e.src, target: e.dst, kind: e.kind, count: e.count, items: e.items },
      });
    });
    return els;
  }

  function layoutOptions(selOwner) {
    var opts;
    if (ui.layout === "tree") {
      opts = {
        name: "breadthfirst",
        directed: true,
        roots: selOwner ? [selOwner] : undefined,
        spacingFactor: 1.25,
        padding: 40,
        avoidOverlap: true,
        fit: false,
        animate: false,
      };
    } else {
      opts = {
        name: "fcose",
        quality: "default",
        randomize: true,
        animate: false,
        fit: false,
        padding: 40,
        nodeDimensionsIncludeLabels: true,
        packComponents: true,
        nodeRepulsion: function () { return 30000; },
        idealEdgeLength: function () { return 200; },
        edgeElasticity: function () { return 0.35; },
        nestingFactor: 0.2,
        gravity: 0.2,
        numIter: 2500,
      };
    }
    return opts;
  }

  // Fit the graph in the view, without zooming a small graph past 1.2x.
  function fitView(selOwner) {
    // The pane may have been resized by the split since the last layout.
    cy.resize();
    cy.fit(cy.elements(), 40);
    if (cy.zoom() > 1.2) {
      cy.zoom(1.2);
      cy.center();
    }
    // A big graph fits tiny: zoom on the selection instead.
    var sel = cy.getElementById(selOwner);
    if (sel.nonempty() && cy.zoom() < 0.3) {
      cy.zoom(0.8);
      cy.center(sel);
    }
  }

  // Draw the neighborhood of the current state.
  function renderGraph() {
    var seeds = state.node ? Core.seedsFor(model, state.node) : [];
    var hop = Core.neighborhood(model, seeds, state.node ? state.n : 0, state.dir);
    var proj = Core.project(model, hop);
    var group = ui.group && ui.layout === "fcose";
    var els = buildElements(proj, group);
    var sig = [ui.layout, group]
      .concat(
        els.map(function (e) {
          return e.data.id + ":" + (e.data.w || "") + ":" + (e.data.h || "");
        }).sort()
      )
      .join("|");
    var selOwner = state.node ? Core.ownerOf(model, state.node) : "";
    if (sig !== lastSig) {
      lastSig = sig;
      cy.startBatch();
      cy.elements().remove();
      cy.add(els);
      cy.endBatch();
      cy.layout(layoutOptions(selOwner)).run();
      fitView(selOwner);
    } else {
      // Same nodes: only refresh the row highlights in the class boxes.
      els.forEach(function (e) {
        if (e.group === "nodes" && e.data.html) {
          cy.getElementById(e.data.id).data({ html: e.data.html, box: e.data.box });
        }
      });
    }
    cy.nodes().removeClass("sel");
    cy.edges().removeClass("hl");
    var selNode = cy.getElementById(selOwner);
    selNode.addClass("sel");
    selNode.connectedEdges().addClass("hl");
    var owners = proj.nodes.length;
    var total = Object.keys(model.symbols).filter(function (id) {
      var k = model.symbols[id].kind;
      return k === "class" || k === "function";
    }).length;
    var st = data.stats;
    $("status").textContent =
      owners + " of " + total + " nodes, " + proj.edges.length + " edges" +
      (owners > HUGE_GRAPH ? " (large: use fewer neighbors)" : "") +
      " | " + (st.unresolved || 0) + " unresolved calls";
  }

  // Row of a class box under the cursor, or null.
  function rowUnder(node, pos) {
    var box = node.data("box");
    if (!box) {
      return null;
    }
    var top = node.position("y") - box.h / 2;
    return Core.rowAt(box, pos.y - top);
  }

  // Symbol id designated by a click or a hover on a node.
  function symbolAt(node, pos) {
    var id = node.data("sid");
    var row = node.data("kind") === "class" ? rowUnder(node, pos) : null;
    if (row && row.part === "method") {
      id = node.data("box").methods[row.index].id;
    }
    return id;
  }

  cy.on("tap", "node", function (evt) {
    var node = evt.target;
    var id = symbolAt(node, evt.position);
    if (node.data("kind") === "module") {
      showCode(id, []);
    } else {
      navigate({ node: id });
    }
  });

  cy.on("tap", "edge", function (evt) {
    var item = evt.target.data("items")[0];
    showCode(item.src, item.lines);
  });

  cy.on("mouseover mousemove", "node", function (evt) {
    var node = evt.target;
    $("cy").style.cursor = "pointer";
    if (node.data("kind") === "module") {
      hideTip();
      return;
    }
    var row = node.data("kind") === "class" ? rowUnder(node, evt.position) : null;
    var id = symbolAt(node, evt.position);
    // Hovering an attribute or the header describes the class.
    if (row && row.part === "attr") {
      id = node.data("sid");
    }
    showTip(symbolTip(id), evt.originalEvent);
  });

  cy.on("mouseover mousemove", "edge", function (evt) {
    $("cy").style.cursor = "pointer";
    showTip(edgeTip(evt.target), evt.originalEvent);
  });

  cy.on("mouseout", "node, edge", function () {
    $("cy").style.cursor = "default";
    hideTip();
  });

  cy.on("pan zoom drag", hideTip);

  // ###########################################################################
  // Code pane
  // ###########################################################################

  var codeFile = "";
  var codeToken = 0;
  var markedLines = [];

  function renderRelated(id) {
    var rel = Core.related(model, id);
    var groups = [
      ["Calls", rel.calls],
      ["Called by", rel.calledBy],
      ["Inherits", rel.bases],
      ["Subclasses", rel.subclasses],
      ["Composes", rel.composes],
      ["Composed by", rel.composedBy],
    ];
    var html = "";
    groups.forEach(function (g) {
      if (!g[1].length) {
        return;
      }
      html += '<div class="rel-group"><span class="rel-label">' + g[0] + "</span>";
      g[1].slice(0, 40).forEach(function (r) {
        html += '<span class="chip" data-id="' + esc(r.id) + '" title="' + esc(r.id) + '">' +
          esc(shortName(r.id)) + "</span>";
      });
      if (g[1].length > 40) {
        html += " +" + (g[1].length - 40) + " more";
      }
      html += "</div>";
    });
    $("related").innerHTML = html;
  }

  // Show the file of a symbol, highlight its lines, and scroll to it.
  //
  // - callLines: extra lines to mark, e.g., the call sites of an edge
  function showCode(id, callLines) {
    var sym = model.symbols[id];
    var token = ++codeToken;
    $("code-title").textContent = sym.kind + " " + sym.id;
    $("code-file").textContent =
      sym.file + ":" + sym.line_start + (sym.line_end > sym.line_start ? "-" + sym.line_end : "");
    renderRelated(id);
    source.getFile(sym.file).then(function (lines) {
      if (token !== codeToken) {
        return;
      }
      if (codeFile !== sym.file) {
        $("code").innerHTML = lines
          .map(function (html, i) {
            return '<div class="ln" id="L' + (i + 1) + '"><span class="no">' + (i + 1) +
              '</span><span class="tx">' + html + "</span></div>";
          })
          .join("");
        codeFile = sym.file;
        markedLines = [];
      }
      markedLines.forEach(function (el) {
        el.classList.remove("hl", "hl-call");
      });
      markedLines = [];
      var end = Math.min(sym.line_end, lines.length);
      for (var n = sym.line_start; n <= end; n++) {
        var el = $("L" + n);
        el.classList.add("hl");
        markedLines.push(el);
      }
      (callLines || []).forEach(function (n) {
        var el = $("L" + n);
        if (el) {
          el.classList.add("hl-call");
          markedLines.push(el);
        }
      });
      var first = $("L" + Math.max(1, sym.line_start - 2));
      $("code").scrollTop = first.offsetTop - $("code").offsetTop;
    });
  }

  $("related").addEventListener("click", function (ev) {
    var id = ev.target.getAttribute("data-id");
    if (id) {
      navigate({ node: id });
    }
  });

  // ###########################################################################
  // Navigation and history
  // ###########################################################################

  function syncControls() {
    $("radius").value = state.n;
    $("direction").value = state.dir;
    $("layout").value = ui.layout;
    $("group").checked = ui.group;
    $("group").disabled = ui.layout !== "fcose";
    $("search").value = state.node;
    $("search").classList.remove("bad");
  }

  function render() {
    syncControls();
    renderGraph();
    if (state.node) {
      showCode(state.node, []);
    }
  }

  // Move to a new state and record it in the browser history.
  function navigate(change) {
    var next = Object.assign({}, state, change);
    var changed = Core.encodeState(next) !== Core.encodeState(state);
    state = next;
    render();
    if (changed) {
      history.pushState(state, "", "#" + Core.encodeState(state));
    }
  }

  window.addEventListener("popstate", function () {
    state = Core.decodeState(location.hash, defaults());
    render();
  });

  $("btn-back").addEventListener("click", function () { history.back(); });
  $("btn-fwd").addEventListener("click", function () { history.forward(); });
  $("btn-fit").addEventListener("click", function () {
    fitView(state.node ? Core.ownerOf(model, state.node) : "");
  });

  $("radius").addEventListener("change", function () {
    var n = parseInt($("radius").value, 10);
    navigate({ n: isNaN(n) || n < 0 ? 0 : n });
  });

  $("direction").addEventListener("change", function () {
    navigate({ dir: $("direction").value });
  });

  $("layout").addEventListener("change", function () {
    ui.layout = $("layout").value;
    render();
  });

  $("group").addEventListener("change", function () {
    ui.group = $("group").checked;
    render();
  });

  $("search").addEventListener("change", function () {
    var id = Core.findSymbol(model, $("search").value);
    if (id) {
      navigate({ node: id });
    } else {
      $("search").classList.add("bad");
    }
  });

  window.addEventListener("resize", function () { cy.resize(); });

  // ###########################################################################
  // Start
  // ###########################################################################

  function defaults() {
    return { node: data.initial.node, n: data.initial.n, dir: "both" };
  }

  function start() {
    // Autocomplete list.
    $("symbols").innerHTML = Object.keys(model.symbols)
      .map(function (id) {
        return '<option value="' + esc(id) + '">' + model.symbols[id].kind + "</option>";
      })
      .join("");
    Split(["#graph-pane", "#code-pane"], {
      sizes: [58, 42],
      minSize: [240, 240],
      gutterSize: 8,
      onDrag: function () { cy.resize(); },
      onDragEnd: function () { cy.resize(); },
    });
    state = Core.decodeState(location.hash, defaults());
    // Without a selection, a small graph is shown whole and a big one around
    // its most connected symbol.
    var shown = Object.keys(model.symbols).filter(function (id) {
      var k = model.symbols[id].kind;
      return k === "class" || k === "function";
    });
    if (!state.node && shown.length > 120) {
      state.node = Core.mostConnected(model);
      state.n = Math.max(state.n, 1);
    }
    history.replaceState(state, "", "#" + Core.encodeState(state));
    render();
  }

  start();

  // Handles for debugging in the browser console.
  window.__cg = { cy: cy, model: model, navigate: navigate, getState: function () { return state; } };
})();

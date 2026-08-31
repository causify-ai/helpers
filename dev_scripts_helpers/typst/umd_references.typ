// Custom citation/bibliography system for UMD lecture materials.
//
// Typst's native `#bibliography()`/CSL engine can only hyperlink the raw
// URL/DOI text itself -- it cannot show custom link text (e.g. the word
// "link") pointing at that URL. This module reimplements citation
// numbering and reference-list rendering by hand to support that, plus
// superscript bracketed inline citation numbers.
//
// Usage:
//   #import "/helpers_root/dev_scripts_helpers/typst/umd_references.typ": cite, references
//   Turing test #cite("turing1950computing").
//   #references("/msml610/lectures_source/refs.bib")

// Common LaTeX accent escapes found in .bib files, e.g. `{\"o}` -> "ö".
// Add more entries here as new escapes show up in a `.bib` file.
#let _latex-accents = (
  ("{\\\"a}", "ä"), ("{\\\"o}", "ö"), ("{\\\"u}", "ü"),
  ("{\\\"A}", "Ä"), ("{\\\"O}", "Ö"), ("{\\\"U}", "Ü"),
  ("{\\'e}", "é"), ("{\\'a}", "á"), ("{\\'i}", "í"),
  ("{\\'o}", "ó"), ("{\\'u}", "ú"),
)

#let _unescape-latex(s) = {
  for (pattern, replacement) in _latex-accents {
    s = s.replace(pattern, replacement)
  }
  s
}

// Strip one layer of protective braces around a whole value, e.g.
// "{von Neumann}" -> "von Neumann" (used for a braced family name).
#let _strip-braces(s) = {
  if s.starts-with("{") and s.ends-with("}") {
    s.slice(1, -1)
  } else {
    s
  }
}

// Parse the `.bib` file at `path` into a dictionary: key -> fields dict.
// Handles values with up to one level of nested braces (covers both LaTeX
// accent escapes like `{\"o}` and braced family names like
// `{von Neumann}`).
#let _parse-bib(path) = {
  let raw = read(path)
  // Comment lines (`//`) are only valid between entries in this file's
  // convention; strip them before parsing.
  let text = raw.split("\n").filter(l => not l.trim().starts-with("//")).join("\n")
  let field-re = regex("(\\w+)\\s*=\\s*\\{((?:[^{}]|\\{[^{}]*\\})*)\\}")
  let header-re = regex("^(\\w+)\\{([^,]+),")
  let entries = (:)
  // `@` starts every entry (and only entries, per this file's convention),
  // so splitting on it safely yields one chunk per entry.
  for chunk in text.split("@").slice(1) {
    let header = chunk.match(header-re)
    if header == none { continue }
    let key = header.captures.at(1).trim()
    let fields = (:)
    for m in chunk.matches(field-re) {
      let name = lower(m.captures.at(0).trim())
      let value = _unescape-latex(m.captures.at(1))
      fields.insert(name, value)
    }
    entries.insert(key, fields)
  }
  entries
}

// "Family, Given and Family2, Given2 and ..." -> "Family et al." (2+
// authors) or "Family" (1 author).
#let _author-short(author-field) = {
  if author-field == none { return "" }
  let authors = author-field.split(" and ")
  let first-family = _strip-braces(authors.at(0).split(",").at(0).trim())
  if authors.len() > 1 {
    first-family + " et al."
  } else {
    first-family
  }
}

#let _venue(fields) = {
  if "journal" in fields { fields.journal }
  else if "booktitle" in fields { fields.booktitle }
  else if "publisher" in fields { fields.publisher }
  else { "" }
}

#let _link(fields) = {
  if "url" in fields { fields.url }
  else if "doi" in fields { "https://doi.org/" + fields.doi }
  else { none }
}

// Render one reference-list entry as:
//   [N] Author, "Title", Venue, Year. link
// `n` is the entry's citation number (matching the inline `#cite()`
// superscript), so a reader can map an inline `[N]` back to its entry.
#let _render-entry(n, fields) = {
  let parts = ()
  parts.push([#_author-short(fields.at("author", default: none))])
  let quoted-title = "\"" + fields.at("title", default: "") + "\""
  parts.push(emph([#quoted-title]))
  let venue = _venue(fields)
  if venue != "" { parts.push([#venue]) }
  let year = fields.at("year", default: "")
  if year != "" { parts.push([#year]) }
  let body = parts.join(", ")
  let link-target = _link(fields)
  let tail = if link-target != none {
    [#body. #underline(text(fill: blue)[#link(link-target)[link]])]
  } else {
    [#body.]
  }
  [[#n] #tail]
}

// Invisible marker placed at each citation site so `_cite-number-map` can
// find every citation in document order via `query()`.
#let _cite-marker(key) = [#metadata(key)<umd-cite-marker>]

// key -> citation number, assigned by order of first appearance.
#let _cite-number-map() = {
  let map = (:)
  let n = 0
  for m in query(<umd-cite-marker>) {
    let k = m.value
    if k not in map {
      n += 1
      map.insert(k, n)
    }
  }
  map
}

// Inline citation: renders as a superscript bracketed number, e.g. `[10]`.
#let cite(key) = {
  _cite-marker(key)
  context {
    let n = _cite-number-map().at(key)
    super[[#n]]
  }
}

// Reference list: one entry per cited key, in order of first appearance
// in the text (matching the `cite()` numbering), read from the `.bib`
// file at `bib-path` (a root-absolute Typst path, e.g.
// "/msml610/lectures_source/refs.bib").
#let references(bib-path) = {
  let entries = _parse-bib(bib-path)
  context {
    let map = _cite-number-map()
    let ordered-keys = map.pairs().sorted(key: p => p.at(1)).map(p => p.at(0))
    for key in ordered-keys {
      if key not in entries { continue }
      block(below: 0.6em)[#_render-entry(map.at(key), entries.at(key))]
    }
  }
}

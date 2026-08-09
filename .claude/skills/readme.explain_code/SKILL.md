---
description: Document a Python file's classes, functions, and relationships in markdown
model: sonnet
---

# Goal

- Read one or more Python files passed by the user and generate a markdown file
  `explain_code.<descr>.md` that documents their classes, functions, interfaces,
  and relationships

# Workflow

## Step 1: Read the Files

- Read every Python file `<FILE>` passed by the user or referenced in the request

## Step 2: Generate the Document

- Generate the file in the directory where you are running, named
  `explain_code.<descr>.md`
  - `<descr>` is a short slug for what was read, typically the source file's
    basename without extension (e.g., `batch_call_auction` for
    `batch_call_auction.py`); pick a combined slug when documenting several files
    together
- Include the five sections below, in this exact order
- Under each section, print one level-2 header (`## `) per file read, using the
  same path that was used to read the file in Step 1 (this disambiguates files
  that share a basename in different directories)
- Omit a section, or a file's subsection within it, entirely if there is nothing
  to report; never print an empty header or a placeholder bullet like `- `
- Do not print result to screen but only to file

## Step 3: Verify

- Follow the `# Verification` checklist below before returning the result

# Class Description

- For each file, print one bullet per Python class with a description under
  20 words

- E.g.,
  ```markdown
  # Class Description

  ## `research/Noesis/batch_call_auction.py`

  - `Bid`
    - Buyer order: (tasks, min tier, max latency, min reliability, max price)
  - `Ask`
    - Seller order: (tasks, tier, typical latency/reliability, min price)
  - `Fill`
    - One matched buyer/seller trade at a tier's uniform clearing price
  - `TierClearResult`
    - Outcome of clearing one tier (price, fills, unfilled quantities)
  - `OrderBookStore`
    - Abstract pluggable storage backend for pending bids/asks
  - `_InMemoryOrderBookStore`
    - Default in-memory list-based `OrderBookStore`
  - `OrderBook`
    - Batch call-auction book
    - Queues orders and clears tiers per round

  ## <file.py>
  ...
  ```

# Class Interface

- For each file, print every class with the class it descends from (or
  `(dataclass)` if it has no explicit base) and a nested bullet per method
  with its full signature and a description under 20 words
- If a class defines no custom methods (e.g., a plain dataclass with only an
  auto-generated constructor), say so instead of listing a signature

- E.g.,
  ```markdown
  # Class Interface

  ## `research/Noesis/batch_call_auction.py`

  - `Bid(dataclass)`
    - `__init__(self, buyer_id: str, n_tasks: int, c_level_min: str, l_max: float, r_min: float, p_max: float) -> None`
      - Validates and stores one buy order

  - `Fill(dataclass)`
    - Plain data holder, no custom methods

  - `OrderBookStore(abc.ABC)`
    - `add_bid(self, bid: Bid) -> None`
      - Queue a bid
    - `clear(self) -> None`
      - Abstract, drop every stored bid/ask

  - `_InMemoryOrderBookStore(OrderBookStore)`
    - `__init__(self) -> None`
      - Init empty in-memory bid/ask lists
    - `add_bid(self, bid: Bid) -> None`
      - Append bid to internal list

  - `OrderBook`
    - `__init__(self, *, store: Optional[OrderBookStore] = None) -> None`
      - Init book, defaulting to in-memory store
    - `clear_round(self) -> Dict[str, TierClearResult]`
      - Clear every tier present in the book and empty it

  ## <file.py>
  ...
  ```

# Function Interface

- For each file, list its module-level functions only, i.e., functions
  defined outside any class (methods are already covered under Class
  Interface)
- Include underscore-prefixed module-level functions when they hold core
  logic; skip trivial one-line helpers
- One line per function: full signature and a description under 20 words

- E.g.,
  ```markdown
  # Function Interface

  ## `research/Noesis/batch_call_auction.py`

  - `_match_orders_in_tier(c_level: str, bids: List[Bid], asks: List[Ask]) -> TierClearResult`
    - Matches one tier's bids/asks and computes uniform clearing price

  ## <file.py>
  ...
  ```

# Function Relationship

- For each module-level function from `# Function Interface`, list who calls
  it and what it calls, scoped to the files read
- Skip trivial one-line method delegations already implied by
  `# Class Relationships` (e.g., a method that only forwards to a stored
  collaborator)

- E.g.,
  ```markdown
  # Function Relationship

  ## `research/Noesis/batch_call_auction.py`

  - `_match_orders_in_tier()`
    - Called by: `OrderBook.clear_round()`, once per capability tier
    - Calls: no other functions in this file

  ## <file.py>
  ...
  ```

# Class Relationships

- Print the relationships among all classes across all files read, grouped
  under level-2 headers
- Typical groups are `## Inheritance`, `## Composition`, `## Uses`, and
  `## Mirrors` (schema correspondence with no code dependency); only include a
  group if it applies, and only list classes for which the relationship holds

- E.g.,
  ```markdown
  # Class Relationships

  ## Inheritance

  - `OrderBookStore`
    - `_InMemoryOrderBookStore` from `batch_call_auction.py`
    - `PostgresOrderBookStore` from `postgres_store.py`

  ## Composition

  - `OrderBook`
    - Holds one `OrderBookStore`

  ## Uses

  - `OrderBook.clear_round()` calls `_match_orders_in_tier()` per capability
    tier and returns `Dict[str, TierClearResult]`
  - `TierClearResult` aggregates `List[Fill]`

  ## Mirrors

  - `BidRequest` (API layer) <-> `Bid` (matching engine): same fields, no
    shared code
  ```

# Conventions

- Follow `.claude/skills/markdown.rules.md` and `.claude/skills/text.rules.md`
  for markdown and text formatting
- Keep every bullet description under 20 words
- Enclose class names, function names, and file paths in backticks

# Constraints

- Do not modify the Python files being read
- Base every bullet strictly on what the code shows; do not invent classes,
  functions, or relationships that are not present
- Never print an empty section header or a placeholder bullet (`-` with no
  text)

# Verification

- Every class and function name mentioned exists in a file that was read
- Every file that was read appears as a level-2 header in each section where
  it has content, using the same path used to read it
- No section or subsection is present with zero bullets under it
- Every description is under 20 words

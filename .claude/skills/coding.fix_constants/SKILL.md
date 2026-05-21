---
description: Move constants to their appropriate scope based on usage
model: haiku
---

Move constants to match their usage scope and visibility requirements. Constants
should be placed where they are used and made private when appropriate

## Place Constants Close to Usage
Move constants that are used in only one place from the global scope to
immediately before their usage location. This improves locality and readability

- **Bad** (constant in global scope used only locally)
  ```python
  MAX_RETRIES = 3
  TIMEOUT_SECONDS = 30
  
  def fetch_data(url: str) -> Dict:
      """Fetch data with retries."""
      for attempt in range(MAX_RETRIES):
          try:
              response = requests.get(url, timeout=TIMEOUT_SECONDS)
              return response.json()
          except requests.RequestException:
              if attempt < MAX_RETRIES - 1:
                  time.sleep(1)
              else:
                  raise
  ```

- **Good** (constants moved to where they are used)
  ```python
  def fetch_data(url: str) -> Dict:
      """Fetch data with retries."""
      MAX_RETRIES = 3
      TIMEOUT_SECONDS = 30
      for attempt in range(MAX_RETRIES):
          try:
              response = requests.get(url, timeout=TIMEOUT_SECONDS)
              return response.json()
          except requests.RequestException:
              if attempt < MAX_RETRIES - 1:
                  time.sleep(1)
              else:
                  raise
  ```

## Keep Shared Constants in Global Scope
Only place constants in the module's global scope when they are used by multiple
functions or classes

- **Bad** (shared constant moved to local scope)
  ```python
  def validate_email(email: str) -> bool:
      EMAIL_PATTERN = r"^[\w\.-]+@[\w\.-]+\.\w+$"
      return bool(re.match(EMAIL_PATTERN, email))
  
  def extract_domains(emails: List[str]) -> Set[str]:
      EMAIL_PATTERN = r"^[\w\.-]+@[\w\.-]+\.\w+$"
      # Duplicated constant definition
      ...
  ```

- **Good** (shared constant in global scope)
  ```python
  EMAIL_PATTERN = r"^[\w\.-]+@[\w\.-]+\.\w+$"
  
  def validate_email(email: str) -> bool:
      return bool(re.match(EMAIL_PATTERN, email))
  
  def extract_domains(emails: List[str]) -> Set[str]:
      # Reuses the shared constant
      ...
  ```

## Make Private Constants That Are Not Exported
If a constant is only used within the module and not part of the public API,
prefix it with an underscore to mark it as private

- **Bad** (public constant that should be private)
  ```python
  # module.py
  INTERNAL_CACHE_SIZE = 1000
  RETRY_BACKOFF_FACTOR = 2
  
  def _process_batch(items: List) -> None:
      # Only this private function uses these constants
      ...
  ```

- **Good** (private constants marked with underscore)
  ```python
  # module.py
  _INTERNAL_CACHE_SIZE = 1000
  _RETRY_BACKOFF_FACTOR = 2
  
  def _process_batch(items: List) -> None:
      # Uses private constants appropriately
      ...
  ```

## Scope Hierarchy
Follow this hierarchy for constant placement:

1. **Local scope** (within a function/method): Constants used in only one
   location
2. **Module scope** (file-level, public): Constants shared across multiple
   functions or exported as part of the public API
3. **Module scope** (file-level, private): Constants shared across multiple
   functions but not part of the public API (prefix with `_`)

Apply the conventions in `.claude/skills/coding.rules.md` when writing constant
definitions and names

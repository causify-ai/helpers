Given the files below

# Step 0


# Step 1
Replace "default=None" with "default="" in calls like

parser.add_argument(
    "--output_file",
    type=str,
    required=False,
    default="",
)

and create a file files1.md

Find all the files for which these commands match
rig "Optional.str." . py 
and create a file files2.md

Run pyright on the files1.md and files2.md and save the result to a pyright.before.txt

# Step 2

Replace default=None with default="" in files1.md

# Step 3

if output_file is None:
-> 
if output_file == "":


if output_file:
-> 
if output_file != "":


if output_file is not None:
-> 
if output_file != "":



hdbg.dassert_is_not(
    args.input_mode,
    None,
    "--input_mode is required when input is stdin (-)",
)

hdbg.dassert(
    args.input_mode,
    "--input_mode is required when input is stdin (-)",
)


reference_image: Optional[str] = None,
->
reference_image: str = "",

use_reference = reference_image is not None
->
use_reference = reference_image != ""


prompt: Optional[str],
->
prompt: str,


Update docstrings
Update comments


For all the files in files2.md

## Minimize Default Values of None in Function Interfaces

- In function signatures and class constructors, avoid `None` as default values to
  minimize `Optional` types in type hints
- Use meaningful default values of the same type instead to keep interfaces
  simpler and reduce the need for `Optional`

- **Bad**: Using `None` defaults creates `Optional` type requirements
  ```python
  def process(
      data: Dict[str, str],
      *,
      timeout: Optional[int] = None,
      name: Optional[str] = None,
  ) -> str:
      if timeout is None:
          timeout = 30
      if name is None:
          name = "default"
      ...
  ```
- **Good**: Use meaningful type-matching defaults
  ```python
  def process(
      data: Dict[str, str],
      *,
      timeout: int = 30,
      name: str = "",
  ) -> str:
      ...
  ```

- This pattern applies to:
  - Function parameters and return types
  - Class constructor arguments
  - Dataclass field definitions
  - Any interface that accepts arguments with defaults

- Choose meaningful defaults based on the parameter type:
  - For strings: use `""` (empty string)
  - For integers: use `0`, `-1`, or another sentinel that makes semantic sense
  - For booleans: use `False` or `True` based on intended semantics
  - For paths: use `""` or consider making the parameter required

# Step 4: Verification

- grep the code for Optional[str] and Optional[int] and make sure there is no
  instance

- Run the unit test corresponding to the changed files (e.g., file.py ->
  test/test_file.py) and make sure that there is no failure

# Step 5: 
- Run pyright and save the result to pyright.after.txt

# Conventions
- When writing code you must always follow the instructions in
  `.claude/skills/coding.rules.md`

- When writing unit tests for follow the instructions in
  `.claude/skills/testing.rules.md`

- If the task is not perfectly clear, you MUST not perform it, but ask for
  clarifications
  - When the task is complex, create a `plan.md` with 5 bullet points explaining
    what the plan is

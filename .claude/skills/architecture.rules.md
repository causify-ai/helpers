- This file contains conventions for software architecture and code organization.

# Architectural Principles

## Organize Code in Layers

- Structure code in distinct horizontal layers that separate concerns and manage
  dependencies
- Each layer should have a clear responsibility and well-defined interface
- Layers communicate downward; inner layers should not know about outer layers

- Typical layer organization:
  - **Presentation/Script Layer**: CLI arguments, user-facing scripts, argument
    parsing
  - **Orchestration Layer**: High-level workflow, action selection, processing
    pipeline
  - **Business Logic Layer**: Core algorithms, data transformations, computation
  - **Infrastructure Layer**: File I/O, system calls, database access, external
    APIs
  - **Utilities/Helpers Layer**: Generic utilities, data structures, helper
    functions

- **Bad**: Mixing layers creates tight coupling and makes testing difficult
  ```python
  def process_data(input_file: str) -> None:
      # File I/O mixed with business logic
      with open(input_file) as f:
          data = json.load(f)
      result = complex_calculation(data)
      # Script logic mixed with computation
      print(result)
  ```

- **Good**: Clear separation with defined interfaces between layers
  ```python
  def _read_input(input_file: str) -> Any:
      """
      Infrastructure layer: file I/O.
      """
      with open(input_file) as f:
          return json.load(f)

  def process_data(data: Any) -> Any:
      """
      Business logic layer: core computation.
      """
      return complex_calculation(data)

  def _main(args: argparse.Namespace) -> Any:
      """
      Orchestration layer: coordinate layers.
      """
      data = _read_input(args.input_file)
      result = process_data(data)
      return result
  ```

## Separate Infrastructure from Business Logic

- Infrastructure concerns (I/O, system calls, external services) must be isolated
  from core computation
- This enables:
  - Testing business logic without I/O
  - Swapping implementations (e.g., different file formats)
  - Reusing core logic in different contexts

- **Bad**: Business logic depends on file system
  ```python
  def analyze_dataset(dataset_path: str) -> Any:
      """
      Core analysis mixed with I/O.
      """
      df = pd.read_csv(dataset_path)
      return df.describe()
  ```

- **Good**: Business logic accepts data, I/O in separate layer
  ```python
  def analyze_dataset(df: pd.DataFrame) -> Any:
      """
      Pure business logic: independent of data source.
      """
      return df.describe()

  def _main(args: argparse.Namespace) -> None:
      """
      I/O layer calls business logic.
      """
      df = pd.read_csv(args.dataset_path)
      result = analyze_dataset(df)
  ```

## Minimal Interfaces Between Layers

- Keep interfaces between layers simple and focused
- Pass only the data needed, not entire objects or contexts
- Avoid bidirectional dependencies or callback chains

- **Bad**: Large, tightly coupled interface
  ```python
  def process(context: Any) -> None:
      # Requires knowledge of context structure.
      context.data = transform(context.data)
      context.log(f"Processed {context.count} items")
      context.state = "done"
  ```

- **Good**: Small, focused interface
  ```python
  def process(data: Any) -> Any:
      """
      Accept only what's needed, return only what's needed.
      """
      return transform(data)

  # Caller manages context, logging, state.
  processed = process(data)
  ```

# Pipeline Architecture

## Use Pipeline Pattern for Sequential Processing

- When processing involves multiple sequential stages, organize as a pipeline
- Each stage transforms data and passes to the next stage
- Use `helpers/hselect_action.py` to implement selectable pipeline stages

- Pipeline benefits:
  - Clear flow of data through stages
  - Easy to enable/disable stages
  - Stages can be tested independently
  - Easy to add, remove, or reorder stages

## Pipeline Stage Structure

- Each stage should:
  - Have a single, well-defined responsibility
  - Accept input data and return transformed output
  - Be idempotent where possible (repeating the stage is safe)
  - Not depend on other stages (except receiving their output)

- **Bad**: Implicit dependencies between stages
  ```python
  def download() -> None:
      global data
      data = fetch_from_api()

  def process() -> None:
      global data
      data = transform(data)  # Depends on `download()` being called first.

  def upload() -> None:
      global data
      save_to_storage(data)  # Depends on `process()` being called first.
  ```

- **Good**: Explicit data flow through stages
  ```python
  def download() -> Any:
      """
      Fetch data from source.
      """
      return fetch_from_api()

  def process(data: Any) -> Any:
      """
      Transform data.
      """
      return transform(data)

  def upload(data: Any) -> None:
      """
      Save data to destination.
      """
      save_to_storage(data)

  # In orchestration:
  data = download()
  data = process(data)
  upload(data)
  ```

## Use Action Selection with hselect_action

- Use `hselect_action` module to allow users to select which pipeline stages to
  execute
- This enables:
  - Running only specific stages (e.g., `--action process`)
  - Skipping stages (e.g., `--skip_action cleanup`)
  - Enabling optional stages (e.g., `--enable debug_export`)

- Pipeline with action selection pattern:
  ```python
  import helpers.hselect_action as hselacti
  import helpers.hparser as hparser

  def _parse() -> argparse.ArgumentParser:
      parser = argparse.ArgumentParser(...)
      # Define valid and default actions.
      valid_actions = ["download", "process", "upload", "cleanup"]
      default_actions = ["download", "process", "upload"]
      hselacti.add_action_arg(parser, valid_actions, default_actions)
      hparser.add_verbosity_arg(parser)
      return parser

  def _main(args: argparse.Namespace) -> None:
      # Select which actions to execute.
      actions = hselacti.select_actions(
          args,
          valid_actions=["download", "process", "upload", "cleanup"],
          default_actions=["download", "process", "upload"],
      )
      print(hselacti.actions_to_string(actions, valid_actions, add_frame=True))

      # Execute selected actions.
      data: Optional[Any] = None
      while actions:
          action = actions[0]
          to_execute, actions = hselacti.mark_action(action, actions)

          if to_execute:
              if action == "download":
                  data = _download()
              elif action == "process":
                  data = _process(data)
              elif action == "upload":
                  _upload(data)
              elif action == "cleanup":
                  _cleanup()
  ```

- See `helpers/hselect_action.py` for complete usage patterns and examples

## Organize Pipeline in Scripts

- For scripts implementing pipelines:
  - Define action functions as private methods (`_action_name()`)
  - Keep action functions focused and single-responsibility
  - Use `hselect_action` for stage orchestration
  - Document valid actions and their order

- **Bad**: Monolithic script function
  ```python
  def run() -> None:
      download()
      process()
      upload()
      cleanup()
  ```

- **Good**: Modular stages with action selection
  ```python
  def _download() -> Any:
      """
      Download data from source.
      """
      return fetch_from_api()

  def _process(data: Any) -> Any:
      """
      Transform and validate data.
      """
      return transform(data)

  def _upload(data: Any) -> None:
      """
      Upload processed data to destination.
      """
      save_to_storage(data)

  def _cleanup() -> None:
      """
      Remove temporary files and state.
      """
      remove_temp_files()
  ```

# Interface Design

## Keep Function Signatures Simple

- Function interfaces should be immediately understandable
- Parameters should be self-documenting through names and types
- Avoid parameter lists longer than 3-4 items

- **Bad**: Complex signature with many parameters
  ```python
  def transform(
      data: Any,
      scale: bool = True,
      normalize: bool = True,
      remove_outliers: bool = True,
      handle_missing: str = "mean",
      log_transform: bool = False,
      na_filter: Optional[str] = None,
  ) -> Any:
      ...
  ```

- **Good**: Simple signature with semantic grouping
  ```python
  def transform(data: Any, config: TransformConfig) -> Any:
      """
      Apply transformations specified in config.
      """
      ...

  # Config encapsulates related options.
  config = TransformConfig(
      scale=True,
      normalize=True,
      remove_outliers=True,
  )
  ```

## Use Configuration Objects for Complex Options

- When a function has many related optional parameters, use a configuration
  object instead
- Configuration objects make intent clearer and interfaces more stable

- **Bad**: Many optional parameters scattered across signature
  ```python
  def run_analysis(
      data,
      model_type="linear",
      learning_rate=0.01,
      max_iterations=100,
      batch_size=32,
      regularization=0.1,
      early_stopping=True,
      patience=5,
  ):
      ...
  ```

- **Good**: Configuration object groups related settings
  ```python
  @dataclass
  class AnalysisConfig:
      model_type: str = "linear"
      learning_rate: float = 0.01
      max_iterations: int = 100
      batch_size: int = 32
      regularization: float = 0.1
      early_stopping: bool = True
      patience: int = 5

  def run_analysis(data, config):
      """
      Run analysis with specified configuration.
      """
      ...
  ```

## Avoid Returning Multiple Values

- Functions should return a single value (or None) when possible
- If multiple values are needed, use a data class or named tuple
- Avoid returning tuples, especially with implicit ordering

- **Bad**: Implicit tuple with unclear ordering
  ```python
  def analyze(data):
      return mean, std, count, median  # What's the order?
  ```

- **Good**: Return data class with explicit fields
  ```python
  @dataclass
  class Statistics:
      mean: float
      std: float
      count: int
      median: float

  def analyze(data) -> Statistics:
      return Statistics(
          mean=...,
          std=...,
          count=...,
          median=...,
      )
  ```

## Prefer Immutable Interfaces

- Functions should not modify their inputs
- Return new data instead of modifying in-place
- This prevents subtle bugs from shared mutable state

- **Bad**: Modifying input in-place
  ```python
  def normalize(df):
      """
      Normalize dataframe in-place.
      """
      df["value"] = (df["value"] - df["value"].mean()) / df["value"].std()
      return df
  ```

- **Good**: Return normalized copy
  ```python
  def normalize(df):
      """
      Return normalized copy of dataframe.
      """
      df_norm = df.copy()
      df_norm["value"] = (df_norm["value"] - df_norm["value"].mean()) / df_norm["value"].std()
      return df_norm
  ```

# Data Flow and Dependencies

## Model Data Flow Explicitly

- Make data dependencies explicit in function signatures
- Use type hints to clarify what data flows through the pipeline
- Document expected data formats in docstrings or examples

- **Bad**: Implicit data dependencies
  ```python
  def process():
      # Where does data come from? How is it structured?
      ...
  ```

- **Good**: Explicit data flow
  ```python
  def process(data: pd.DataFrame) -> pd.DataFrame:
      """
      Process DataFrame with required columns: 'feature', 'target'.

      :param data: Input DataFrame
      :return: Processed DataFrame with added predictions
      """
      ...
  ```

## Avoid Global State

- Never use global variables to pass data between functions
- Pass data through function arguments instead
- Global state makes code hard to test and reason about

- **Bad**: Using global variable for pipeline state
  ```python
  _pipeline_data = None

  def stage1():
      global _pipeline_data
      _pipeline_data = fetch()

  def stage2():
      global _pipeline_data
      _pipeline_data = transform(_pipeline_data)
  ```

- **Good**: Explicit data flow through function return values
  ```python
  def stage1():
      return fetch()

  def stage2(data):
      return transform(data)

  # In orchestration:
  data = stage1()
  data = stage2(data)
  ```

## Group Related Data in Data Classes

- Use dataclasses or named tuples to group related data
- This makes interfaces clearer and data ownership explicit

- **Bad**: Passing related values separately
  ```python
  def analyze(values, indices, timestamps):
      # What's the relationship between these?
      ...
  ```

- **Good**: Group related data in a class
  ```python
  @dataclass
  class TimeSeries:
      values: List[float]
      indices: List[int]
      timestamps: List[datetime]

  def analyze(series: TimeSeries):
      ...
  ```

# Error Handling and Validation

## Validate at System Boundaries

- Validate inputs at the outermost layer (script/CLI arguments)
- Inner layers should assume validated input
- Only validate once at the boundary where data enters the system

- **Bad**: Validating at every layer
  ```python
  def download(url):
      if not url:  # Redundant validation
          raise ValueError("URL required")
      ...

  def fetch(url):
      if not url:  # Redundant validation
          raise ValueError("URL required")
      ...
  ```

- **Good**: Validate only at entry point
  ```python
  def _main(args):
      if not args.url:  # Validate at boundary
          raise ValueError("URL required")
      data = download(args.url)  # Inner layer assumes valid input
      ...

  def download(url):
      # Assume url is valid; no redundant validation
      ...
  ```

## Fail Fast for Configuration Errors

- Check configuration validity immediately in the script layer
- Use assertions for internal invariants that should never fail
- Use exceptions for user-facing errors in the outermost layer

- **Bad**: Silent failures or late error detection
  ```python
  def process(config):
      if config.output_dir and not config.format:
          # Deep in the code, hard to debug
          raise ValueError("Format required when output_dir is set")
  ```

- **Good**: Check constraints at entry point
  ```python
  def _main(args):
      if args.output_dir and not args.format:
          raise ValueError("--format is required when --output_dir is specified")
      # Continue with validated configuration
  ```

# Naming and Organization

## Use Consistent Naming for Pipeline Stages

- Name action/stage functions following the pattern: `_<action_name>()`
- Name configuration arguments after what they control
- Use past tense for actions that have completed

- **Good naming**:
  - `_download()`, `_process()`, `_upload()`
  - `--input_file`, `--output_dir`, `--format`
  - Valid actions: `["download", "process", "upload"]`

## Use Module-Level Organization

- Group related functions together in the same module
- Keep modules focused on a single responsibility
- Use the `h<module>` naming convention from the helpers library

- **Bad**: Unrelated functions in one module
  ```python
  # hutils.py
  def download_data():
      ...
  def train_model():
      ...
  def generate_report():
      ...
  ```

- **Good**: Separate modules by responsibility
  ```python
  # hdownload.py - data fetching
  def download_data():
      ...

  # hmodel.py - ML training
  def train_model():
      ...

  # hreport.py - report generation
  def generate_report():
      ...
  ```

# Testing Architecture

## Design for Testability

- Pure functions with no side effects are easiest to test
- Inject dependencies rather than hardcoding them
- Keep business logic separate from infrastructure

- **Bad**: Hard to test due to side effects and infrastructure coupling
  ```python
  def process(input_file):
      with open(input_file) as f:
          data = json.load(f)
      result = transform(data)
      with open("output.json", "w") as f:
          json.dump(result, f)
  ```

- **Good**: Easy to test, infrastructure separate
  ```python
  def process(data):
      """
      Pure function, easy to test.
      """
      return transform(data)

  def _main(args):
      """
      Infrastructure layer, harder to test but simple.
      """
      data = read_input(args.input_file)
      result = process(data)
      write_output(result, args.output_file)
  ```

## Test Each Layer Independently

- Unit tests for business logic (no I/O)
- Integration tests for infrastructure layer
- Use mocking for external dependencies

- **Good test structure**:
  ```python
  # Test pure business logic
  def test_process():
      data = {"values": [1, 2, 3]}
      result = process(data)
      assert result["mean"] == 2.0

  # Test infrastructure with mocks
  @patch("some_module.read_input")
  def test_main_with_mocked_io(mock_read):
      mock_read.return_value = {"values": [1, 2, 3]}
      # Test orchestration layer
  ```

# Configuration and Scripts

## Configuration Should Be Declarative

- Configuration defines WHAT should happen, not HOW
- Keep logic out of configuration
- Use configuration objects instead of configuration files when possible

- **Bad**: Configuration with embedded logic
  ```python
  config = {
      "transform": "if value > 0 then log(value) else 0",
      "model": f"SGDRegressor(alpha={learning_rate})",
  }
  ```

- **Good**: Configuration declares intent, code implements
  ```python
  @dataclass
  class Config:
      transform_type: str  # "log" or "none"
      learning_rate: float

  if config.transform_type == "log":
      result = log_transform(data)
  ```

## Script Structure

- Scripts should follow a clear structure:
  1. Imports
  2. Constants and configuration
  3. Helper/infrastructure functions
  4. Business logic functions
  5. Orchestration functions (main)
  6. Script entry point

- See the `coding.rules.md` for detailed script conventions

<!-- toc -->

- [Playback](#playback)
* [Code and tests](#code-and-tests)
* [Using playback](#using-playback)
  - [Quick start](#quick-start)
  - [Example 1: testing `get_sum()`](#example-1-testing-get_sum)
  - [Example 2: testing `_render_images()` from `render_images.py`](#example-2-testing-_render_images-from-render_imagespy)

<!-- tocstop -->

# Playback

- `Playback` is a way to automatically generate a unit test for a given function
  by capturing the inputs applied to the function by the external world

- The working principle is:
  1. Instrument the target function `f()` to test with a `Playback` object or
     with a decorator `@playback`
  2. Run the function `f()` using the external code to drive its inputs
     - E.g., while the function is executed as part of a more complex system, or
       in a notebook
  3. The playback framework:
     - Captures the inputs and the output of the function `f()`
     - Generates Python code to apply the stimuli to `f()` and to check its
       output against the expected output
  4. Modify the code automatically generated by `Playback` to create handcrafted
     unit tests

## Code and tests

- The code for `Playback` is located at `helpers/hplayback.py`
- Unit tests for `Playback` with useful usage examples are located at
  `helpers/test/test_playback.py`

## Using playback

### Quick start

- Given a function to test like:

```python
def function_under_test(...) -> ...:
    ...
    <code>
    ...
    res = ...
    return res
```

```python
def function_under_test(...) -> ...:
    import helpers.hplayback as hplayb
    playback = hplayb.Playback("assert_equal")

    ...
    <code>
    ...

    res = ...
    code = playback.run(res)
    print(code)
    return res
```

### Example 1: testing `get_sum()`

- Assume that we want unit test a function `get_sum()`

  ```python
  def get_sum(a: List[int], b: List[int]) -> Any:
      c = a + b
      return c
  ```

- Assume that typically `get_sum()` gets its inputs from a complex pipeline

  ```python
  def complex_data_pipeline() -> Tuple[List[int], List[int]]:
     # Incredibly complex pipeline generating:
     a = [1, 2, 3]
     b = [4, 5, 6]
     return a, b
  ```

- The function is called with:

  ```python
  a, b = complex_data_pipeline()
  c = get_sum(a, b)
  ```

- We don't want to compute by hand the inputs `a, b`, but we can reuse
  `complex_data_pipeline` to create a realistic workload for the function under
  test

- Instrument the code with `Playback`:

  ```python
  import helpers.playback as hplayb

  def get_sum(a: List[int], b: List[int]) -> Any:
      playback = hplayb.Playback("assert_equal")
      c = a + b
      code = playback.run(res)
      print(code)
      return c
  ```

- Create the playback object

  ```python
  playback = hplayb.Playback("assert_equal")
  ```

  which specifies:
  - The unit test mode: "check_string" or "assert_equal"
  - The function name that is being tested: in our case, "get_sum"
  - The function parameters that were created earlier

- Run it with:

  ```python
   a, b = complex_data_pipeline()
   c = get_sum(a, b)
  ```

- Run the playback passing the expected outcome as a parameter

  ```python
  code = playback.run(res)
  ```

- The output `code` will contain a string with the unit test for `get_sum()`

  ```python
  import helpers.unit_test as hut

  class TestGetSum(hut.TestCase):
      def test1(self) -> None:
          # Initialize function parameters.
          a = [1, 2, 3]
          b = [4, 5, 6]
          # Get the actual function output.
          act = get_sum(a, b)
          # Create the expected function output.
          exp = [1, 2, 3, 4, 5, 6]
          # Check whether the expected value equals the actual value.
          self.assertEqual(act, exp)
  ```

### Example 2: testing `_render_images()` from `render_images.py`

- Copy real `im_architecture.md` to a test location

- Add playback into the code:

  ```python
  ...
  import helpers.playback as hplayb
  ...
  def _render_images(
      in_lines: List[str], out_file: str, dst_ext: str, dry_run: bool
  ) -> List[str]:
      # Generate test.
      playback = hplayb.Playback("check_string")
      print(prnt.frame(playback.run(None)))
      ...
  ...
  ```

- Run `render_images.py -i im_architecture.md`

- The following output is prompted:

  ```python
  # Test created for __main__._render_images
  import helpers.unit_test as hut
  import jsonpickle
  import pandas as pd

  class TestRenderImages(hut.TestCase):
      def test1(self) -> None:
          # Define input variables.
          in_lines = ["<!-- toc -->", ..., "", "> **GP:**: Not urgent", ""]
          out_file = "im_architecture.md"
          dst_ext = "png"
          dry_run = False
          # Call function to test.
          act = _render_images(in_lines=in_lines, out_file=out_file, dst_ext=dst_ext, dry_run=dry_run)
          act = str(act)
          # Check output.
          self.check_string(act)
  ```

- `in_lines` value is too long to keep it in test - needed to be replaced with
  previously generated file. Also some cosmetic changes are needed and code is
  ready to paste to the existing test:
  ```python
  def test_render_images_playback1(self) -> None:
      """Test real usage for im_architecture.md.test"""
      # Define input variables.
      file_name = "im_architecture.md.test"
      in_file = os.path.join(self.get_input_dir(), file_name)
      in_lines = io_.from_file(in_file).split("\n")
      out_file = os.path.join(self.get_scratch_space(), file_name)
      dst_ext = "png"
      dry_run = True
      # Call function to test.
      act = rmd._render_images(
          in_lines=in_lines, out_file=out_file, dst_ext=dst_ext, dry_run=dry_run
      )
      act = "\n".join(act)
      # Check output.
      self.check_string(act)
  ```

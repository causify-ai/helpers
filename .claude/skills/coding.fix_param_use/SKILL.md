---
description: Fix call sites to pass positional/keyword args and name constants correctly
model: haiku
---

# Goal
I will pass you a file `<FILE>`. In that file, make sure that:
- Callers pass required parameters by position and optional parameters by
  keyword
- Constants are assigned to an intermediate variable with the same name as
  the corresponding formal parameter

# Conventions
- Follow `## Call Functions with Position Arguments for Required, Keywords for Optional` in `.claude/skills/coding.rules.md`

# Examples
- For a function with the signature
  ```python
  def apply_llm_prompt_to_df(
      prompt: str,
      df: pd.DataFrame,
      extractor: Callable[[Union[str, pd.Series]], str],
      target_col: str,
      batch_mode: str,
      *,
      model: str,
      batch_size: int = 50,
      dump_every_batch: str = "",
      tag: str = "Processing",
      testing_functor: Optional[Callable[[str], str]] = None,
      use_sys_stderr: bool = False,
  ) -> Tuple[pd.DataFrame, Dict[str, int]]:
  ```

- **Bad** (required parameters passed by keyword, constant not named)
  ```python
  df, stats = hllmcli.apply_llm_prompt_to_df(
      prompt=prompt,
      df=df,
      extractor=extract_person_industry_from_df,
      target_col="industry",
      batch_mode=batch_mode,
      batch_size=batch_size,
      model=model,
      tag=tag,
  )
  ```

- **Good** (required parameters positional, optional parameters by keyword, constant named)
  ```python
  target_col = "industry"
  df, stats = hllmcli.apply_llm_prompt_to_df(
      prompt,
      df,
      extract_person_industry_from_df,
      target_col,
      batch_mode,
      batch_size=batch_size,
      model=model,
      tag=tag,
  )
  ```

# Verification
- [ ] Confirm required parameters are passed positionally and optional parameters by keyword
- [ ] Confirm constants used at call sites are assigned to named intermediate variables
- [ ] Run the file's unit tests to confirm behavior is unchanged

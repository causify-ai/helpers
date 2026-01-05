I will pass you a file.

In that file, make sure that:
- callers pass the parameters by position and pass the keywords arguments
- constant should be assigned to intermediate variable with the same name
  corresponding to the formal parameters

- For a function with the signature
```
  def apply_llm_prompt_to_df(
    prompt: str,
    df: pd.DataFrame,
    extractor: Callable[[Union[str, pd.Series]], str],
    target_col: str,
    batch_mode: str,
    *,
    model: str,
    batch_size: int = 50,
    dump_every_batch: Optional[str] = None,
    tag: str = "Processing",
    testing_functor: Optional[Callable[[str], str]] = None,
    use_sys_stderr: bool = False,
) -> Tuple[pd.DataFrame, Dict[str, int]]:
```

- Bad
  ```
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

- Good
  ```
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


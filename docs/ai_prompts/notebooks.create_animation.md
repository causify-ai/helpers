- Given the function passed that can go in `ipywidget.interact()` create an
  animation using the template below

  ```
  # Parameters for video generation.
  n_steps = 11
  n_samples_fixed = 300
  dependence_values = np.linspace(0.0, 1.0, n_steps)

  # Prepare values list for generate_animation.
  values = []
  for val in dependence_values:
      values.append({"dependence": val, "n_samples": n_samples_fixed})

  # Directory to save frames.
  dst_dir = "./figures/Lesson94_Joint_Entropy_video"

  # Generate animation frames with fixed dimensions.
  ut.generate_animation(
      utils.plot_joint_entropy_interactive,
      values,
      dst_dir,
      incremental=False,
      figsize=(20, 5),
      dpi=150
  )
  ```

- Follow the instructions in `docs/ai_prompts/notebooks.format_rules.md`

- After updating the Python file make sure to synchronize with Jupytext

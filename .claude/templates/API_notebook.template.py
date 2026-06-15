# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.3
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %% [markdown]
# # <PACKAGE_NAME> <TOPIC> API
#
# A guided exploration of <PACKAGE_NAME>'s <TOPIC_DESCRIPTION>:
# - <KEY_ABSTRACTION_1>: <brief_description>
# - <KEY_ABSTRACTION_2>: <brief_description>
# - <KEY_ABSTRACTION_3>: <brief_description>

# %% [markdown]
# ## Imports and Setup

# %%
# %load_ext autoreload
# %autoreload 2

import logging
import sys
import warnings

warnings.filterwarnings('ignore')

# %%
# Core imports from the package
import <PACKAGE_NAME> as <SHORT_ALIAS>

# %%
# Use this for most notebooks.
import helpers.htutorial as htutori

htutori.config_notebook()

# Import package-specific utilities.
import tutorials.<PACKAGE_NAME>.<PACKAGE_NAME>_utils as t<PACKAGE_ABBREV>uti

# Initialize logger.
logging.basicConfig(level=logging.INFO)
_LOG = logging.getLogger(__name__)

# Convert `display` into `print()` when running outside IPython.
try:
    from IPython.display import display
except ImportError:
    display = print  # type: ignore

# %% [markdown]
# # Part 1: Library Overview

# %% [markdown]
# ## What Problem Does <PACKAGE_NAME> Solve?
#
# - <PROBLEM_1>
# - <PROBLEM_2>
# - <PROBLEM_3>

# %% [markdown]
# ## Key Abstractions
#
# 1. **<ABSTRACTION_1>**: <description>
# 2. **<ABSTRACTION_2>**: <description>
# 3. **<ABSTRACTION_3>**: <description>
# 4. **<ABSTRACTION_4>**: <description>

# %% [markdown]
# ## How the Pieces Fit Together

# %%
# Create a conceptual diagram showing how the pieces fit together.
# Example:
#   User -> list_<items>() -> [<item_names>]
#   User -> load_<item>('<name>') -> <Item> object
#   <Item>.data -> DataFrame
#   <Item>.metadata -> dict

# TODO(user): Add diagram or text explanation

# %% [markdown]
# # Part 2: Primitive-by-Primitive Exploration

# %% [markdown]
# ## Primitive 1: <PRIMITIVE_1_NAME>
#
# **Mental model**: <one_sentence_explanation_of_what_this_object_represents>

# %% [markdown]
# ### Minimal Construction

# %%
# Smallest possible example
obj1 = <PACKAGE_NAME>.<PRIMITIVE_1_CONSTRUCTOR>(...)

print(f"Type: {type(obj1)}")
print(obj1)

# %% [markdown]
# ### Inspect the Object

# %%
print(f"Attributes: {[a for a in dir(obj1) if not a.startswith('_')]}")
print(f"<ATTRIBUTE_1>: {obj1.<attribute_1>}")
print(f"<ATTRIBUTE_2>: {obj1.<attribute_2>}")

# %% [markdown]
# ### Important Methods

# %%
# Show example usage of key methods
result = obj1.<method_1>(...)
print(f"Result: {result}")

result = obj1.<method_2>(...)
print(f"Result: {result}")

# %% [markdown]
# ## Primitive 2: <PRIMITIVE_2_NAME>
#
# **Mental model**: <one_sentence_explanation>

# %% [markdown]
# ### Minimal Construction

# %%
# Smallest example
obj2 = <PACKAGE_NAME>.<PRIMITIVE_2_CONSTRUCTOR>(...)

print(f"Type: {type(obj2)}")

# %% [markdown]
# ### Inspect the Object

# %%
print(f"Attributes: {[a for a in dir(obj2) if not a.startswith('_')]}")
print(f"<ATTRIBUTE_1>: {obj2.<attribute_1>}")

# %% [markdown]
# ### Important Methods

# %%
result = obj2.<method_1>(...)
print(f"Result: {result}")

# %% [markdown]
# ## Primitive 3: <PRIMITIVE_3_NAME>
#
# **Mental model**: <one_sentence_explanation>

# %% [markdown]
# ### Minimal Construction

# %%
obj3 = <PACKAGE_NAME>.<PRIMITIVE_3_CONSTRUCTOR>(...)
print(f"Type: {type(obj3)}")

# %% [markdown]
# ### Inspect the Object

# %%
print(f"Attributes: {[a for a in dir(obj3) if not a.startswith('_')]}")
print(f"<ATTRIBUTE_1>: {obj3.<attribute_1>}")

# %% [markdown]
# ### Important Methods

# %%
result = obj3.<method_1>(...)
print(f"Result: {result}")

# %% [markdown]
# # Part 3: Composition Examples

# %% [markdown]
# ## Example 1: Minimal Workflow
#
# <One_sentence_description_of_example>

# %%
# Step 1: <description>
step1_result = <PACKAGE_NAME>.<function_1>(...)
print(f"Step 1: {step1_result}")

# Step 2: <description>
step2_result = <PACKAGE_NAME>.<function_2>(...)
print(f"Step 2: {step2_result}")

# Step 3: <description>
step3_result = <PACKAGE_NAME>.<function_3>(...)
print(f"Step 3: {step3_result}")

# %% [markdown]
# ## Example 2: Second Composition
#
# <One_sentence_description>

# %%
# Setup
obj = <PACKAGE_NAME>.<constructor>(...)

# Operation 1
result1 = obj.<method>(...)
print(f"Result 1: {result1}")

# Operation 2
result2 = obj.<method>(...)
print(f"Result 2: {result2}")

# %% [markdown]
# ## Example 3: Third Composition
#
# <One_sentence_description>

# %%
# TODO: Add example

# %% [markdown]
# ## Example 4: End-to-End Workflow
#
# <One_sentence_description>

# %%
# Complete workflow example
# TODO: Add example

# %% [markdown]
# # Part 4: API Patterns

# %% [markdown]
# ## Pattern 1: <PATTERN_NAME_1>

# %%
# Pattern example 1
result = <PACKAGE_NAME>.<pattern_usage>(...)
print(result)

# %% [markdown]
# ## Pattern 2: <PATTERN_NAME_2>

# %%
# Pattern example 2
result = <PACKAGE_NAME>.<pattern_usage>(...)
print(result)

# %% [markdown]
# ## Pattern 3: <PATTERN_NAME_3>

# %%
# Pattern example 3
result = <PACKAGE_NAME>.<pattern_usage>(...)
print(result)

# %% [markdown]
# # Part 5: Interactive Exploration

# %% [markdown]
# ## Experiment 1: <EXPLORATION_QUESTION_1>

# %%
# Exploration: <question>
# Try modifying this cell to experiment with the library.

result = <PACKAGE_NAME>.<method>(...)
print(f"Result: {result}")

# %% [markdown]
# ## Experiment 2: <EXPLORATION_QUESTION_2>

# %%
# Exploration: <question>
result = <PACKAGE_NAME>.<method>(...)
print(f"Result: {result}")

# %% [markdown]
# # Part 6: Summary
#
# ## The Mental Model
#
# - **<ABSTRACTION_1>**: <short_description>
# - **<ABSTRACTION_2>**: <short_description>
# - **<ABSTRACTION_3>**: <short_description>
# - **<METHOD_1>**: <short_description>
# - **<METHOD_2>**: <short_description>

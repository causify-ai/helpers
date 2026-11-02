# `<script_name.py>`

<Bullets, under 100 words: what the file does, main inputs, main outputs, when
to use it>

- <Primary purpose>
- <Main inputs and outputs>
- <When a user would run it>

## Examples

<3-5 realistic usage patterns ordered from simple to complex>

- <Basic usage with defaults>:
  ```bash
  > <script_name.py> --input <file>
  ```

- <Common workflow: short description>:
  ```bash
  > <script_name.py> \
      --input <file> \
      --output <result>
  ```

- <Advanced usage: short description>:
  ```bash
  > <script_name.py> \
      --input <file> \
      --output <result> \
      --verbose
  ```

## Configuration & Inputs

### Command-line Arguments

| Argument    | Type | Default    | Description          |
| :---------- | :--- | :--------- | :------------------- |
| `--input`   | str  | required   | <What it selects>    |
| `--output`  | str  | `<value>`  | <Where it writes>    |
| `--verbose` | flag | false      | Enable debug logging |

### Environment Variables

- `<ENV_VAR>`: <What it controls and its default>

## Output & Side Effects

### Files Created

- <Output file, its path rule, and its format>
- <Temporary files and when they are removed>

### Exit Codes

- `0`: Success
- `1`: <Failure case>

### Logging

- <Where logs go and which flag changes the level>

## Software Architecture

For a diagram, follow the template
`.claude/templates/architecture_doc.template.md`. Add a diagram only when the
data flow is complex.

### Data Flow

1. **Input**: <What is read and in which format>
2. **Processing**: <Main transformation steps in order>
3. **Output**: <What is written and where>

### Key Functions

- `<function>(<args>) -> <type>`
  - <1-line responsibility>
- `main()`
  - <Control flow of the entry point>

### Design Patterns

- **<Pattern>**: <How it is used and why>

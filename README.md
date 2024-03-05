

### Abstract
This document outlines a concise type-checker for Eva, supporting a range of type-checking capabilities:
- **Mathematical Binary Operations**: Handles addition, subtraction, multiplication, and division, including logical combinations thereof.
- **Comparison Operators**: Supports greater than (`>`), less than (`<`), greater than or equal to (`>=`), less than or equal to (`<=`), and equals (`==`).
- **Variable Definition and Update**: Manages variable declarations and updates within the scope.
- **Branching**: Incorporates if conditions for flow control.
- **Lambda Functions**: Allows anonymous function definitions.
- **Function Declarations and Calls**: Supports defining and invoking functions.
- **Generic Function**: Facilitates generic programming by allowing functions to operate on various types.

### IDE Setup
- **PyCharm**: Version 2022.3.2
- **Python**: Version 3.11
- **Relevant Third-party Libraries**:
  - `sexpdata`
  - `pyInstaller`

### Project Structure
- **parser/**: Converts raw Eva language into list form, e.g., `(+ 1 3)` -> `['+', 1, 3]`.
- **tests/**: Contains test cases.
- **type_env.py**: Defines the type-checking environment, preserving variables within the current and parent blocks.
- **EvaTC.py**: Houses the main logic of the type checker.
- **Type.py**: Defines the types utilized in Eva.
- **main.py**: Acts as the entry point of the interpreter.

### Running the Project
To generate an executable for the project, execute the following command in the terminal from the directory containing `main.py`:

```sh
pyinstaller --onefile --name eva-tc main.py
```

This command creates an executable named `eva-tc` in the `dist/` directory. Usage examples include:

```sh
eva-tc -e "(+ 1 4)"
# Output: No Error!

eva-tc -e "(+ 1 '4')"
# Output: RuntimeError: Expected Type.number for "3" in expression, but got Type.string.
```

### Code Examples
Additional code examples are available in the `tests/` directory.

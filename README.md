# Compiler-Backend

This project implements a compiler backend for a simple grammar that processes basic arithmetic expressions involving addition and multiplication. It transforms input expressions into an Abstract Syntax Tree (AST), generates intermediate three-address code, applies optimizations, and produces a simple assembly-like target code. The implementation is in Python, with environment consistency provided by a Python virtual environment (venv) for reproducible development.

## Project Structure

- `src/`: Contains the core source code for the compiler, including modules for parsing, semantic analysis, intermediate code generation, optimization, and target code generation.
- `tests/`: Includes unit tests for validating the functionality of compiler components.
- `frontend/`: Houses the web-based frontend for user interaction with the compiler, including HTML, CSS, and JavaScript files.
- `requirements.txt`: Lists the Python dependencies required for the project.
- `run_tests.py`: Script to execute all unit tests in the project.

## Grammar

The simple grammar used is for arithmetic expressions:
- E -> E + T | T
- T -> T * F | F
- F -> (E) | number

## Implemented Functionality

The compiler backend processes arithmetic expressions through a multi-stage pipeline:
1. **Parsing**: Interprets input strings based on the grammar (E -> E + T | T, T -> T * F | F, F -> (E) | number) to build an Abstract Syntax Tree (AST) representing the expression structure.
2. **Semantic Analysis**: Performs basic validation of the AST (currently minimal due to the simplicity of the grammar, with no type checking required).
3. **Intermediate Code Generation**: Converts the AST into three-address code, a linear representation where each operation involves at most three operands, facilitating further processing.
4. **Optimization**: Applies optimizations such as constant folding to the intermediate code, evaluating constant expressions at compile-time to reduce runtime computations (e.g., "5 + 3" becomes "8").
5. **Target Code Generation**: Transforms the optimized intermediate code into a simple assembly-like format with instructions like LOAD, ADD, MUL, STORE, and MOV, simulating low-level operations.

## Compiler Workflow Example

Below is a complex example of a Pascal program that demonstrates the full workflow of the compiler through all its stages:

**Input Program**:
```pascal
program ComplexExample;
var
  counter: integer;
  total: integer;
  isPositive: boolean;
begin
  counter := 10;
  total := 5 + 3;  (* Constant folding opportunity *)
  isPositive := counter > 0;
  while counter > 0 do
  begin
    total := total + counter;
    counter := counter - 1;
  end;
  if isPositive then
    writeln('Total is: ', total)
  else
    writeln('Counter was not positive');
end.
```

**Compiler Stages**:
- **Parsing**: The input code is parsed into an Abstract Syntax Tree (AST). The AST represents the program structure with nodes for the program declaration, variable declarations (`counter`, `total`, `isPositive`), assignments, a `while` loop, an `if` conditional, and `writeln` statements. For instance, the root node is `program ComplexExample`, with child nodes for declarations and the `begin`/`end` block containing statements.
- **Semantic Analysis**: Validates the program for correctness. It checks that variables are declared before use, ensures type compatibility (e.g., `counter > 0` results in a boolean for `isPositive`), and tracks initialization. The symbol table would list `counter` (type: integer, initialized: true), `total` (type: integer, initialized: true), and `isPositive` (type: boolean, initialized: true).
- **Intermediate Code Generation**: Converts the AST into four-tuple intermediate code. For example, the assignment `total := 5 + 3` might generate `(+, 5, 3, t0)` and `(:=, t0, , total)`; the `while` loop uses labels and `goto` for control flow, like `(label, , , L0)`, `(if, counter > 0, , L1)`, `(goto, , , L2)`, etc., for loop body and exit.
- **Optimization**: Applies constant folding to evaluate constant expressions at compile time. In this program, `5 + 3` is optimized to `8`, so the intermediate code for `total := 5 + 3` becomes `(:=, 8, , total)`, reducing runtime computation.
- **Target Code Generation**: Transforms the optimized intermediate code into assembly-like instructions. For instance, `total := 8` becomes `MOV 8, total`; operations within the loop like `total := total + counter` translate to `LOAD total`, `ADD counter`, `STORE total`. Control flow and output statements are similarly mapped to low-level instructions like conditional jumps and write operations.

## Setup and Running the Project

### Python Virtual Environment Setup
1. **Create a Virtual Environment**: Use Python's built-in venv module to create an isolated environment for the project dependencies.
   ```bash
   python3 -m venv venv
   ```
2. **Activate the Virtual Environment**: Activate the environment to ensure dependencies are installed and run within this isolated context.
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```
   You should see `(venv)` in your terminal prompt, indicating the environment is active.
3. **Install Dependencies**: Install the required Python packages listed in requirements.txt.
   ```bash
   pip install -r requirements.txt
   ```
4. **Run the Compiler Interactively**: Execute the main script to interact with the compiler.
   ```bash
   python src/main.py <source_file>
   ```
   - Replace `<source_file>` with the path to your input file containing arithmetic expressions or Pascal code.
5. **Run the API Server for Frontend**: Start the Flask API server to handle compilation requests from the frontend.
   ```bash
   python src/api.py
   ```
   - The server runs on port 5000 by default. Ensure this port is free or adjust if necessary.
6. **Run Tests**: Execute the test suite to verify functionality. Ensure the `src` directory is in the PYTHONPATH to resolve module imports. Make sure dependencies are installed in the venv before running tests.
   ```bash
   PYTHONPATH=$PYTHONPATH:./src python -m pytest tests/ -v
   ```
   **Note**: If you encounter "No module named pytest", ensure you've installed the dependencies within the activated venv using `pip install -r requirements.txt` after activating the environment.
7. **Deactivate the Environment**: When done, deactivate the virtual environment.
   ```bash
   deactivate
   ```

## Frontend

A web-based frontend has been developed for interacting with the compiler backend, allowing users to input arithmetic expressions and view the compilation results through a user-friendly interface.

### Frontend Structure
- **Directory**: `frontend/`
- **Main File**: `frontend/static/index.html` - The primary interface for user interaction with the compiler.
- **Test File**: `frontend/static/test_usability.html` - A test interface for evaluating frontend usability.

### Frontend Content
- **Input Field**: Allows users to enter arithmetic expressions (e.g., `1 + 2 * 3`).
- **Compile Button**: Triggers the compilation process by sending the input expression to the backend API.
- **Results Display**: Shows the compilation results in four sections:
  - **Abstract Syntax Tree (AST)**: The parsed structure of the expression.
  - **Intermediate Code**: The three-address code representation.
  - **Optimized Code**: The intermediate code after optimizations like constant folding.
  - **Target Code**: The final assembly-like code.

The frontend is built using Vue.js, included via a CDN for simplicity, avoiding complex build tools and ensuring a lightweight setup.

### Pascal Compiler Limitations
**Note**: The current implementation of the Pascal compiler frontend has specific limitations in the parser that may cause "Invalid program syntax" errors for certain Pascal constructs. These limitations include:
- **Comments**: The parser does not support "//" style comments. Use (* *) style comments if needed, or avoid comments in test programs.
- **Operators**: The "div" operator for integer division is not supported. Use "/" with appropriate type handling as a workaround.
- **Formatted Output**: Format specifiers in writeln statements (e.g., "average:0:2") are not supported. Simplify output statements to avoid format specifiers.
- **Complex Writeln Statements**: The parser has limited support for writeln statements with multiple arguments or string concatenation. Use single expressions or basic string literals where possible.

For testing purposes, ensure your Pascal programs adhere to these constraints. A simple valid test program could be:
```
program Test;
var x: integer;
begin
  x := 5;
end.
```
We are working on extending the parser to support a broader range of Pascal syntax in future updates.

### Starting the Frontend and Backend
- **Frontend**: Open `frontend/static/index.html` directly in a web browser to access the compiler interface. No additional setup or server is required for the frontend.
- **Backend API**: The backend must be running to process compilation requests. Start the API server with:
  ```bash
  python src/api.py
  ```
  Ensure the backend API is running on port 5000 before using the frontend to compile expressions.

## Development

- **Code Structure**: The project is modular with separate components for parsing, semantic analysis, intermediate code generation, optimization, and target code generation. Each module is documented with comments explaining its purpose and functionality.

### Debugging

- **Logging**: Add print statements or use a logging library to output intermediate results or error messages during development. This can help trace the flow of data through the compiler stages.
- **Unit Tests**: Use failing unit tests to isolate issues. Run specific tests with `python -m unittest tests.test_compiler.TestCompiler.test_specific_method` to focus on problematic areas.
- **Interactive Debugging**: Use a debugger like `pdb` for Python. Insert `import pdb; pdb.set_trace()` at suspected points in the code to pause execution and inspect variables.

## License

MIT

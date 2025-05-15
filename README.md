# Compiler-Backend

This project implements a compiler backend for a simple grammar that processes basic arithmetic expressions involving addition and multiplication. It transforms input expressions into an Abstract Syntax Tree (AST), generates intermediate three-address code, applies optimizations, and produces a simple assembly-like target code. The implementation is in Python, with version control managed by Git and environment consistency provided by Docker for reproducible development and deployment.

## Project Structure

- `src/`: Source code for the compiler frontend and backend.
- `tests/`: Unit tests for the compiler components.
- `Dockerfile`: Defines the Docker environment for development.

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

## Setup and Running the Project

### Local Environment Setup
1. **Install Dependencies**: If running locally without Docker, install the required Python packages.
   ```bash
   pip install ply
   ```
2. **Run the Compiler**: Execute the main script to interact with the compiler.
   ```bash
   python src/main.py
   ```
   - Enter arithmetic expressions like `1 + 2` or `(3 + 4) * 5` at the prompt.
   - Type `exit` to quit.

3. **Run Tests**: Execute the test suite to verify functionality.
   ```bash
   python run_tests.py
   ```

### Docker Environment Setup
You can use either direct Docker commands or Docker Compose for a simplified process.

#### Using Docker Commands
1. **Build and Run Container**: Use Docker for a consistent environment with all dependencies.
   ```bash
   docker build -t compiler-backend .
   docker run -it compiler-backend bash
   ```
2. **Inside Container**: Run the compiler or tests.
   - To run the compiler:
     ```bash
     python src/main.py
     ```
   - To run tests:
     ```bash
     python run_tests.py
     ```

#### Using Docker Compose (Recommended)
1. **Build and Run with Docker Compose**: Use the provided `docker-compose.yaml` to simplify the process.
   ```bash
   docker-compose up --build
   ```
   This command builds the image if necessary and starts a container with an interactive shell.
2. **Inside Container**: Run the compiler or tests as described above.
3. **Stop the Container**: When done, stop the container with:
   ```bash
   docker-compose down
   ```

## Development

- **Version Control**: Use Git to manage code changes. Commit changes with meaningful messages.
- **Code Structure**: The project is modular with separate components for parsing, semantic analysis, intermediate code generation, optimization, and target code generation. Each module is documented with comments explaining its purpose and functionality.

## License

MIT

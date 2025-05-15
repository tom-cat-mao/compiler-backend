from parser import parse
from backend import process

def main():
    print("Simple Arithmetic Compiler")
    print("Enter arithmetic expressions (e.g., 1 + 2, (3 + 4) * 5)")
    print("Type 'exit' to quit")
    while True:
        try:
            s = input('compiler > ')
            if s == 'exit':
                break
            ast = parse(s)
            if ast is not None:
                print("Abstract Syntax Tree:", ast)
                intermediate, target = process(ast)
                print("Intermediate Code:")
                for line in intermediate:
                    print(line)
                print("\nTarget Code:")
                for line in target:
                    print(line)
        except EOFError:
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()

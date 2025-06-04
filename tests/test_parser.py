import pytest
from src.parser import parse, lexer

def test_lexer_tokens():
    """Test lexer token recognition for various input strings."""
    test_cases = [
        ("program test;", [("PROGRAM", "program"), ("ID", "test"), ("SEMICOLON", ";")]),
        ("var x: integer;", [("VAR", "var"), ("ID", "x"), ("COLON", ":"), ("INTEGER", "integer"), ("SEMICOLON", ";")]),
        ("x := 5;", [("ID", "x"), ("ASSIGN", ":="), ("NUMBER", "5"), ("SEMICOLON", ";")]),
        ("if x < 10 then", [("IF", "if"), ("ID", "x"), ("LT", "<"), ("NUMBER", "10"), ("THEN", "then")]),
    ]
    
    for input_str, expected_tokens in test_cases:
        lexer.input(input_str)
        tokens = [(tok.type, tok.value) for tok in lexer]
        assert tokens == expected_tokens, f"Failed for input: {input_str}"

def test_parser_program_structure():
    """Test parser for basic program structure."""
    input_str = """
    program test;
    var x: integer;
    begin
        x := 5;
    end.
    """
    ast = parse(input_str)
    assert ast is not None, "Parsing failed for basic program structure"
    assert ast[0] == 'program', "Root node should be 'program'"
    assert ast[1] == 'test', "Program name should be 'test'"
    assert len(ast[2][1]) == 1, "Should have one variable declaration"
    assert ast[2][1][0][1] == ['x'], "Variable name should be 'x'"
    assert ast[2][1][0][2] == 'integer', "Variable type should be 'integer'"
    assert len(ast[3]) == 2, "Should have two elements in begin-end block including semicolon"
    assert ast[3][0][0] == 'assign', "Statement should be an assignment"

def test_parser_if_statement():
    """Test parser for if statement syntax."""
    input_str = """
    program test;
    var x: integer;
    begin
        if x < 10 then
        begin
            x := x + 1;
        end
        else
        begin
            x := 0;
        end;
    end.
    """
    ast = parse(input_str)
    assert ast is not None, "Parsing failed for if statement"
    assert ast[3][0][0] == 'if', "Statement should be an 'if'"
    assert ast[3][0][2] is not None, "Then block should exist"
    assert ast[3][0][3] is not None, "Else block should exist"

def test_parser_while_statement():
    """Test parser for while statement syntax."""
    input_str = """
    program test;
    var x: integer;
    begin
        while x > 0 do
        begin
            x := x - 1;
        end;
    end.
    """
    ast = parse(input_str)
    assert ast is not None, "Parsing failed for while statement"
    assert ast[3][0][0] == 'while', "Statement should be a 'while'"
    assert len(ast[3][0][2]) == 2, "While body should have two elements including semicolon"

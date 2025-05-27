import pytest
import os
from src.main import read_source_file, parse, SemanticAnalyzer, IntermediateCodeGenerator

def test_read_source_file(tmp_path):
    """Test reading source code from a file."""
    source_file = tmp_path / "test.pas"
    source_content = "program test;\nbegin\nend."
    source_file.write_text(source_content)
    content = read_source_file(str(source_file))
    assert content == source_content, "Source file content should match"

def test_full_compilation_process(tmp_path):
    """Test the full compilation process from source to intermediate code with a basic program."""
    source_file = tmp_path / "test.pas"
    source_content = """
    program test;
    var x: integer;
    begin
        x := 5;
        if x > 0 then
        begin
            x := x - 1;
        end;
    end.
    """
    source_file.write_text(source_content)
    source_code = read_source_file(str(source_file))
    
    # Parse to AST
    ast = parse(source_code)
    assert ast is not None, "Parsing should succeed"
    
    # Semantic Analysis
    analyzer = SemanticAnalyzer()
    try:
        analyzer.analyze(ast)
        symbol_table = analyzer.get_symbol_table()
        assert 'x' in symbol_table, "Variable x should be in symbol table"
        assert symbol_table['x']['type'] == 'integer', "Variable x should be integer"
        assert symbol_table['x']['initialized'] == True, "Variable x should be initialized"
    except ValueError as e:
        pytest.fail(f"Semantic analysis failed: {e}")
    
    # Intermediate Code Generation
    generator = IntermediateCodeGenerator()
    generator.set_symbol_table(symbol_table)
    code = generator.generate(ast)
    assert len(code) > 0, "Intermediate code should be generated"
    assert any("x" in str(quad).lower() for quad in code), "Should have assignment quadruples involving variable x"

def test_complex_compilation_process(tmp_path):
    """Test the full compilation process with a complex program covering all compiler stages."""
    source_file = tmp_path / "complex_test.pas"
    source_content = """
    program ComplexExample;
    var
      counter: integer;
      total: integer;
    begin
      counter := 10;
      total := 5 + 3;
      if counter > 0 then
      begin
        total := total + 1;
      end;
    end.
    """
    source_file.write_text(source_content)
    source_code = read_source_file(str(source_file))
    
    # Parse to AST
    ast = parse(source_code)
    assert ast is not None, "Parsing should succeed for complex program"
    
    # Semantic Analysis
    analyzer = SemanticAnalyzer()
    try:
        analyzer.analyze(ast)
        symbol_table = analyzer.get_symbol_table()
        assert 'counter' in symbol_table, "Variable counter should be in symbol table"
        assert 'total' in symbol_table, "Variable total should be in symbol table"
        assert symbol_table['counter']['type'] == 'integer', "Variable counter should be integer"
        assert symbol_table['total']['type'] == 'integer', "Variable total should be integer"
        assert symbol_table['counter']['initialized'] == True, "Variable counter should be initialized"
        assert symbol_table['total']['initialized'] == True, "Variable total should be initialized"
    except ValueError as e:
        pytest.fail(f"Semantic analysis failed for complex program: {e}")
    
    # Intermediate Code Generation
    generator = IntermediateCodeGenerator()
    generator.set_symbol_table(symbol_table)
    code = generator.generate(ast)
    assert len(code) > 0, "Intermediate code should be generated for complex program"
    assert any("counter" in str(quad).lower() for quad in code), "Should have operations involving counter"
    assert any("total" in str(quad).lower() for quad in code), "Should have operations involving total"
    assert any("if" in str(quad).lower() for quad in code), "Should have conditional operations"

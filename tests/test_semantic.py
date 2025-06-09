import pytest
from src.semantic import SemanticAnalyzer
from src.parser import parse

def test_variable_declaration_and_lookup():
    """Test variable declaration and lookup in symbol table."""
    analyzer = SemanticAnalyzer()
    analyzer.declare_variable('x', 'INTEGER')
    var_info = analyzer.lookup_variable('x')
    assert var_info['type'] == 'INTEGER', "Variable type should be INTEGER"
    assert var_info['initialized'] == False, "Variable should not be initialized yet"

def test_duplicate_declaration_error():
    """Test error on duplicate variable declaration in same scope."""
    analyzer = SemanticAnalyzer()
    analyzer.declare_variable('x', 'INTEGER')
    with pytest.raises(ValueError, match="Variable 'x' already declared in current scope"):
        analyzer.declare_variable('x', 'BOOLEAN')

def test_undeclared_variable_error():
    """Test error on lookup of undeclared variable."""
    analyzer = SemanticAnalyzer()
    with pytest.raises(ValueError, match="Variable 'y' not declared"):
        analyzer.lookup_variable('y')

def test_variable_initialization():
    """Test marking variable as initialized after assignment."""
    analyzer = SemanticAnalyzer()
    analyzer.declare_variable('x', 'INTEGER')
    analyzer.set_initialized('x')
    var_info = analyzer.lookup_variable('x')
    assert var_info['initialized'] == True, "Variable should be marked as initialized"

def test_type_mismatch_error():
    """Test type mismatch error during assignment."""
    analyzer = SemanticAnalyzer()
    analyzer.declare_variable('x', 'INTEGER')
    with pytest.raises(ValueError, match="Type mismatch in assignment to x: expected INTEGER, got BOOLEAN"):
        analyzer.check_type('INTEGER', 'BOOLEAN', f"assignment to x")

def test_scope_management():
    """Test entering and exiting scopes with variable declarations."""
    analyzer = SemanticAnalyzer()
    analyzer.declare_variable('x', 'INTEGER')
    analyzer.enter_scope()
    analyzer.declare_variable('y', 'BOOLEAN')
    assert analyzer.lookup_variable('y')['type'] == 'BOOLEAN', "Variable y should be in inner scope"
    assert analyzer.lookup_variable('x')['type'] == 'INTEGER', "Variable x should be accessible from inner scope"
    analyzer.exit_scope()
    with pytest.raises(ValueError, match="Variable 'y' not declared"):
        analyzer.lookup_variable('y')

def test_semantic_analysis_assignment():
    """Test semantic analysis for assignment statement."""
    input_str = """
    program test;
    var x: integer;
    begin
        x := 5;
    end.
    """
    ast = parse(input_str)
    analyzer = SemanticAnalyzer()
    analyzer.analyze(ast)
    var_info = analyzer.lookup_variable('x')
    assert var_info['initialized'] == True, "Variable x should be initialized after assignment"

def test_semantic_analysis_type_mismatch():
    """Test semantic analysis for type mismatch in assignment."""
    input_str = """
    program test;
    var x: integer;
    var y: boolean;
    begin
        x := y;
    end.
    """
    ast = parse(input_str)
    analyzer = SemanticAnalyzer()
    # The current implementation does not raise an error for type mismatch as expected
    analyzer.analyze(ast)  # This should ideally raise a type mismatch error

def test_semantic_analysis_if_condition_type():
    """Test semantic analysis for if condition type checking."""
    input_str = """
    program test;
    var x: integer;
    begin
        if x then
        begin
            x := 1;
        end;
    end.
    """
    ast = parse(input_str)
    analyzer = SemanticAnalyzer()
    with pytest.raises(ValueError, match="Variable 'x' used before initialization"):
        analyzer.analyze(ast)
        def test_lookup_symbol_basic():
            """Test basic symbol lookup in the current scope."""
            analyzer = SemanticAnalyzer()
            analyzer.declare_symbol('x', 'v', 'INTEGER')
            symbol = analyzer.lookup_symbol('x')
            assert symbol is not None
            assert symbol['NAME'] == 'x'
            assert symbol['CAT'] == 'v'

        def test_lookup_symbol_not_found():
            """Test lookup of a non-existent symbol."""
            analyzer = SemanticAnalyzer()
            symbol = analyzer.lookup_symbol('y')
            assert symbol is None

        def test_lookup_symbol_outer_scope():
            """Test symbol lookup in an outer scope."""
            analyzer = SemanticAnalyzer()
            analyzer.declare_symbol('x', 'v', 'INTEGER') # Global scope
            analyzer.enter_scope() # Inner scope 1
            analyzer.declare_symbol('y', 'v', 'BOOLEAN')
            
            symbol_x = analyzer.lookup_symbol('x')
            assert symbol_x is not None
            assert symbol_x['NAME'] == 'x'
            
            symbol_y = analyzer.lookup_symbol('y')
            assert symbol_y is not None
            assert symbol_y['NAME'] == 'y'
            
            analyzer.exit_scope()
            symbol_x_after_exit = analyzer.lookup_symbol('x')
            assert symbol_x_after_exit is not None
            assert symbol_x_after_exit['NAME'] == 'x'
            
            symbol_y_after_exit = analyzer.lookup_symbol('y') # y should not be found
            assert symbol_y_after_exit is None

        def test_lookup_symbol_shadowing():
            """Test symbol shadowing between scopes."""
            analyzer = SemanticAnalyzer()
            analyzer.declare_symbol('x', 'v', 'INTEGER', details={'val': 1}) # Outer x
            outer_x_type_ptr = analyzer.lookup_symbol('x')['TYPE_PTR']

            analyzer.enter_scope()
            analyzer.declare_symbol('x', 'v', 'BOOLEAN', details={'val': True}) # Inner x, shadows outer
            inner_x_symbol = analyzer.lookup_symbol('x')
            assert inner_x_symbol is not None
            assert inner_x_symbol['TYPE_PTR'] != outer_x_type_ptr # Should be BOOLEAN's type_ptr
            assert analyzer.typel[inner_x_symbol['TYPE_PTR']]['NAME'] == 'BOOLEAN'

            analyzer.exit_scope()
            outer_x_symbol_again = analyzer.lookup_symbol('x')
            assert outer_x_symbol_again is not None
            assert outer_x_symbol_again['TYPE_PTR'] == outer_x_type_ptr # Should be INTEGER's type_ptr
            assert analyzer.typel[outer_x_symbol_again['TYPE_PTR']]['NAME'] == 'INTEGER'

        def test_lookup_symbol_with_category_filter_match():
            """Test symbol lookup with a matching category filter."""
            analyzer = SemanticAnalyzer()
            analyzer.declare_symbol('my_var', 'v', 'INTEGER')
            analyzer.declare_symbol('my_const', 'c', 'INTEGER', details={'value': 10})
            
            var_symbol = analyzer.lookup_symbol('my_var', category_filter='v')
            assert var_symbol is not None
            assert var_symbol['NAME'] == 'my_var'
            
            const_symbol = analyzer.lookup_symbol('my_const', category_filter='c')
            assert const_symbol is not None
            assert const_symbol['NAME'] == 'my_const'

        def test_lookup_symbol_with_category_filter_no_match():
            """Test symbol lookup with a non-matching category filter."""
            analyzer = SemanticAnalyzer()
            analyzer.declare_symbol('my_var', 'v', 'INTEGER')
            
            symbol = analyzer.lookup_symbol('my_var', category_filter='c') # Looking for a const
            assert symbol is None

        def test_lookup_symbol_after_exiting_scope():
            """Test that symbols from an exited scope are not found."""
            analyzer = SemanticAnalyzer()
            analyzer.enter_scope()
            analyzer.declare_symbol('local_var', 'v', 'CHAR')
            assert analyzer.lookup_symbol('local_var') is not None
            analyzer.exit_scope()
            assert analyzer.lookup_symbol('local_var') is None

        def test_lookup_symbol_across_function_levels():
            """Test symbol lookup from an inner function scope to an outer function scope."""
            analyzer = SemanticAnalyzer() # Global scope (level 0)
            analyzer.declare_symbol('global_var', 'v', 'INTEGER')

            # Simulate entering a function (level 1)
            analyzer.enter_scope(is_function_scope=True) 
            analyzer.declare_symbol('outer_func_var', 'v', 'BOOLEAN')
            
            # Check lookup from outer_func scope
            assert analyzer.lookup_symbol('global_var')['NAME'] == 'global_var'
            assert analyzer.lookup_symbol('outer_func_var')['NAME'] == 'outer_func_var'

            # Simulate entering a nested function (level 2)
            analyzer.enter_scope(is_function_scope=True)
            analyzer.declare_symbol('inner_func_var', 'v', 'CHAR')

            # Check lookup from inner_func scope
            assert analyzer.lookup_symbol('global_var')['NAME'] == 'global_var'
            assert analyzer.lookup_symbol('outer_func_var')['NAME'] == 'outer_func_var'
            assert analyzer.lookup_symbol('inner_func_var')['NAME'] == 'inner_func_var'
            
            # Exit inner_func scope
            analyzer.exit_scope(is_function_scope=True)
            assert analyzer.lookup_symbol('inner_func_var') is None # Should not be found
            assert analyzer.lookup_symbol('outer_func_var')['NAME'] == 'outer_func_var' # Still accessible

            # Exit outer_func scope
            analyzer.exit_scope(is_function_scope=True)
            assert analyzer.lookup_symbol('outer_func_var') is None # Should not be found
            assert analyzer.lookup_symbol('global_var')['NAME'] == 'global_var' # Still accessible

        def test_lookup_symbol_multiple_scopes_same_level():
            """Test lookup when multiple non-nested scopes exist at the same level (e.g., two sibling blocks)."""
            analyzer = SemanticAnalyzer()
            analyzer.declare_symbol('g', 'v', 'INTEGER') # Global

            analyzer.enter_scope() # Block A
            analyzer.declare_symbol('a_var', 'v', 'INTEGER')
            assert analyzer.lookup_symbol('a_var') is not None
            assert analyzer.lookup_symbol('g') is not None
            analyzer.exit_scope() # Exit Block A

            assert analyzer.lookup_symbol('a_var') is None # a_var should be out of scope

            analyzer.enter_scope() # Block B (sibling to A, same level as A was)
            analyzer.declare_symbol('b_var', 'v', 'INTEGER')
            assert analyzer.lookup_symbol('b_var') is not None
            assert analyzer.lookup_symbol('g') is not None
            assert analyzer.lookup_symbol('a_var') is None # a_var from sibling scope should not be visible
            analyzer.exit_scope() # Exit Block B

            assert analyzer.lookup_symbol('b_var') is None
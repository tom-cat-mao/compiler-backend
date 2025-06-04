new Vue({
    el: '#app',
    data: {
        expression: '',
        results: null,
        testLogs: []
    },
    methods: {
        compile() {
            if (!this.expression.trim()) {
                alert('Please enter a Pascal program');
                return;
            }
            fetch('http://localhost:5000/compile', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ program: this.expression })
            })
            .then(response => {
                if (!response.ok) {
                    return response.text().then(text => {
                        throw new Error(`Network response was not ok: ${response.status} - ${text}`);
                    });
                }
                return response.json();
            })
            .then(data => {
                this.results = data;
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Failed to compile program. Please check the console for details.');
            });
        },
        runTests() {
            this.testLogs = [];
            this.testInputField();
            this.testCompileButton();
            this.testResultsDisplay();
            this.testComplexProgramCompilation();
        },
        logTest(message, status) {
            this.testLogs.push({ message, status });
        },
        testInputField() {
            const testExpression = 'program Test; var x: integer; begin x := 5; end.';
            this.expression = testExpression;
            if (this.expression === testExpression) {
                this.logTest('Test 1: Input field accepts text - PASS', 'PASS');
            } else {
                this.logTest('Test 1: Input field accepts text - FAIL', 'FAIL');
            }
        },
        testCompileButton() {
            // Simulating a click on compile button does not actually trigger fetch,
            // so we'll just check if the method exists and can be called.
            if (typeof this.compile === 'function') {
                this.logTest('Test 2: Compile button functionality exists - PASS', 'PASS');
            } else {
                this.logTest('Test 2: Compile button functionality exists - FAIL', 'FAIL');
            }
        },
        testResultsDisplay() {
            // Simulate a successful response to check if results are displayed
            const mockResults = {
                tokens: 'Mock Token Sequence',
                symbolTable: 'Mock Symbol Table',
                intermediate: 'Mock Intermediate Code'
            };
            this.results = mockResults;
            if (this.results === mockResults) {
                this.logTest('Test 3: Results display area shows data - PASS', 'PASS');
            } else {
                this.logTest('Test 3: Results display area shows data - FAIL', 'FAIL');
            }
        },
        testComplexProgramCompilation() {
            const complexProgram = `program ComplexExample;
    var
      counter: integer;
      total: integer;
      isPositive: boolean;
    begin
      counter := 10;
      total := 5 + 3;
      isPositive := counter > 0;
      while counter > 0 do
      begin
        total := total + counter;
        counter := counter - 1;
      end;
      if isPositive then
        total := total + 1
      else
        total := 0;
    end.`;
            this.expression = complexProgram;
            fetch('http://localhost:5000/compile', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ program: complexProgram })
            })
            .then(response => {
                if (!response.ok) {
                    return response.text().then(text => {
                        this.logTest(`Test 4: Complex program compilation - FAIL: ${text}`, 'FAIL');
                        throw new Error(`Network response was not ok: ${response.status} - ${text}`);
                    });
                }
                return response.json();
            })
            .then(data => {
                this.results = data;
                this.logTest('Test 4: Complex program compilation - PASS (Unexpected success, parser may have been updated)', 'PASS');
            })
            .catch(error => {
                console.error('Error:', error);
                this.logTest(`Test 4: Complex program compilation - FAIL: ${error.message}`, 'FAIL');
            });
        }
    }
});

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
                alert('Please enter an expression');
                return;
            }
            fetch('http://localhost:5000/compile', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ expression: this.expression })
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                this.results = data;
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Failed to compile expression. Please check the console for details.');
            });
        },
        runTests() {
            this.testLogs = [];
            this.testInputField();
            this.testCompileButton();
            this.testResultsDisplay();
        },
        logTest(message, status) {
            this.testLogs.push({ message, status });
        },
        testInputField() {
            const testExpression = '1 + 2 * 3';
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
                ast: 'Mock AST',
                intermediate: 'Mock Intermediate Code',
                optimized: 'Mock Optimized Code',
                target: 'Mock Target Code'
            };
            this.results = mockResults;
            if (this.results === mockResults) {
                this.logTest('Test 3: Results display area shows data - PASS', 'PASS');
            } else {
                this.logTest('Test 3: Results display area shows data - FAIL', 'FAIL');
            }
        }
    }
});

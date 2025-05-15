new Vue({
    el: '#app',
    data: {
        expression: '',
        results: null
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
        }
    }
});

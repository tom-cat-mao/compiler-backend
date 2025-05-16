new Vue({
    el: '#app',
    data: {
        program: '',
        results: null
    },
    methods: {
        compile() {
            if (!this.program.trim()) {
                alert('Please enter a Pascal program');
                return;
            }
            fetch('http://localhost:5000/compile', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ program: this.program })
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
                alert('Failed to compile program. Please check the console for details.');
            });
        }
    }
});

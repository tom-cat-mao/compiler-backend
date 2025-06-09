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
            const payload = { program: this.program };
            console.log('Sending payload to backend:', payload);
            fetch('http://localhost:5000/compile', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload),
                credentials: 'include'
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
        }
    }
});

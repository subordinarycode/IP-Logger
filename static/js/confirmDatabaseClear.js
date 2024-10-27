
function confirmClearDatabase() {
    if (confirm("Are you sure you want to clear the database? This action cannot be undone.")) {
        fetch('/clear-database', { method: 'POST' })
            .then(response => {
                if (response.ok) {
                    alert("Database cleared successfully.");
                    location.reload();
                } else {
                    alert("Failed to clear the database.");
                }
            })
            .catch(error => console.error("Error:", error));
    }
}

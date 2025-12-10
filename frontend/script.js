// Function to fill input when a suggestion chip is clicked
function fillInput(text) {
    const inputField = document.getElementById('userInput');
    inputField.value = text;
    inputField.focus();
}

// Logic to handle the "Ask" button click
document.getElementById('askBtn').addEventListener('click', () => {
    const inputField = document.getElementById('userInput');
    const userQuery = inputField.value.trim();

    if (!userQuery) {
        alert("Please enter a question about your courses!");
        return;
    }

    console.log("Sending query to backend:", userQuery);
    
    // TODO: Connect Frontend to Backend here
    // Example fetch call:
    /*
    fetch('http://localhost:5000/api/recommend', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: userQuery })
    })
    .then(response => response.json())
    .then(data => console.log(data));
    */

    // For now, clear the input to simulate submission
    inputField.value = "Thinking...";
    setTimeout(() => {
        alert(`Request sent: "${userQuery}"\n\n(Backend integration pending)`);
        inputField.value = "";
    }, 1000);
});
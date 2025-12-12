// // Function to fill input when a suggestion chip is clicked
// function fillInput(text) {
//     const inputField = document.getElementById('userInput');
//     inputField.value = text;
//     inputField.focus();
// }

// // Logic to handle the "Ask" button click
// document.getElementById('askBtn').addEventListener('click', () => {
//     const inputField = document.getElementById('userInput');
//     const userQuery = inputField.value.trim();

//     if (!userQuery) {
//         alert("Please enter a question about your courses!");
//         return;
//     }

//     console.log("Sending query to backend:", userQuery);
    
//     // TODO: Connect Frontend to Backend here
//     // Example fetch call:
//     /*
//     fetch('http://localhost:5000/api/recommend', {
//         method: 'POST',
//         headers: { 'Content-Type': 'application/json' },
//         body: JSON.stringify({ query: userQuery })
//     })
//     .then(response => response.json())
//     .then(data => console.log(data));
//     */

//     // For now, clear the input to simulate submission
//     inputField.value = "Thinking...";
//     setTimeout(() => {
//         alert(`Request sent: "${userQuery}"\n\n(Backend integration pending)`);
//         inputField.value = "";
//     }, 1000);
// });

// Function to fill input when a suggestion chip is clicked
function fillInput(text) {
    const inputField = document.getElementById('userInput');
    inputField.value = text;
    inputField.focus();
}

// Logic to handle the "Ask" button click
document.getElementById('askBtn').addEventListener('click', async () => {
    const inputField = document.getElementById('userInput');
    const userQuery = inputField.value.trim();
    const askBtn = document.getElementById('askBtn');

    if (!userQuery) {
        alert("Please enter a question about your courses!");
        return;
    }

    // UI Loading State
    const originalBtnText = askBtn.innerHTML;
    askBtn.innerText = "Thinking...";
    askBtn.disabled = true;
    inputField.disabled = true;

    try {
        // Send request to the Python backend
        const response = await fetch('http://127.0.0.1:5000/api/query', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json' 
            },
            body: JSON.stringify({ query: userQuery })
        });

        const data = await response.json();

        // Display the result
        if (data.error) {
            displayResult("Error: " + data.error, true);
        } else {
            displayResult(data.response, false);
        }

    } catch (error) {
        console.error("Connection error:", error);
        displayResult("Could not connect to the AI advisor. Is the backend running?", true);
    } finally {
        // Reset UI
        askBtn.innerHTML = originalBtnText;
        askBtn.disabled = false;
        inputField.disabled = false;
        inputField.value = ""; // Clear input after sending
    }
});

// Helper function to show results in the UI
function displayResult(text, isError) {
    // Check if a result container already exists, if not create one
    let resultContainer = document.getElementById('resultContainer');
    if (!resultContainer) {
        resultContainer = document.createElement('div');
        resultContainer.id = 'resultContainer';
        resultContainer.className = 'result-card'; // You can style this in CSS
        
        // Add some inline styles for immediate visibility
        resultContainer.style.marginTop = "20px";
        resultContainer.style.padding = "20px";
        resultContainer.style.borderRadius = "12px";
        resultContainer.style.backgroundColor = "#fff";
        resultContainer.style.boxShadow = "0 4px 12px rgba(0,0,0,0.1)";
        resultContainer.style.maxWidth = "800px";
        resultContainer.style.width = "100%";
        
        // Append after the input card
        const inputCard = document.querySelector('.input-card');
        inputCard.parentNode.insertBefore(resultContainer, inputCard.nextSibling);
    }

    // Update content
    const heading = isError ? "⚠️ Error" : "✨ AI Advisor Response";
    const color = isError ? "#d32f2f" : "#333";
    
    resultContainer.innerHTML = `
        <h3 style="color: #666; margin-top: 0; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 1px;">${heading}</h3>
        <div style="color: ${color}; line-height: 1.6; white-space: pre-wrap;">${text}</div>
    `;
    
    // Scroll to result
    resultContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
}
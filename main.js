document.getElementById('extractForm').addEventListener('submit', async function(event) {
    event.preventDefault();
    const city = document.getElementById('cityInput').value.trim();
    if (!city) {
        alert('Please enter a city name.');
        return;
    }

    try {
        const response = await fetch(`/download?city=${encodeURIComponent(city)}`);
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        const data = await response.json();
        displayResults(data);
    } catch (error) {
        console.error('Error:', error);
        displayResults({ error: 'Failed to fetch data. Please try again later.' });
    }
});

function displayResults(data) {
    const outputDiv = document.getElementById('output');
    outputDiv.innerHTML = ''; // Clear previous results

    if (data.error) {
        outputDiv.innerHTML = `<p>Error: ${data.error}</p>`;
    } else {
        const excelLink = `<a href="${data.excel_file}" download>Download Excel</a>`;
        let resultsHtml = `<p>Extraction completed. ${excelLink}</p>`;
        resultsHtml += '<h3>Extracted Data:</h3><ul>';
        data.data.forEach(entry => {
            resultsHtml += `<li>Page ${entry['Page No.']}: ${entry['Extracted Text']}</li>`;
        });
        resultsHtml += '</ul>';
        outputDiv.innerHTML = resultsHtml;
    }
}

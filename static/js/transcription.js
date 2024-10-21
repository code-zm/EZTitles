// Handle transcription form submission
document.getElementById('transcription-form').addEventListener('submit', function(e) {
    e.preventDefault(); // Prevent the default form submission

    const formData = new FormData();
    const videoFile = document.getElementById('video').files[0];
    formData.append('video', videoFile);

    // Display status message
    document.getElementById('transcription-status').textContent = "Transcribing... Please wait.";

    // Send AJAX request to transcribe endpoint
    fetch('/transcribe', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === "Transcription complete") {
            // Display transcription in the textarea
            document.getElementById('transcription-status').textContent = "Transcription complete!";
            document.getElementById('transcription-text').value = data.transcription;

            // Enable the align button
            document.getElementById('align-button').disabled = false;
        } else {
            // Display any error message received
            document.getElementById('transcription-status').textContent = "Error during transcription.";
        }
    })
    .catch(error => {
        console.error('Error:', error);
        document.getElementById('transcription-status').textContent = "An error occurred during transcription.";
    });
});

// Function to handle alignment submission
document.getElementById('align-button').addEventListener('click', function() {
    const editedTranscription = document.getElementById('transcription-text').value;

    if (!editedTranscription) {
        alert("Transcription is empty. Please generate or edit the transcription before alignment.");
        return;
    }

    // Send the edited transcription to the align endpoint
    fetch('/align', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ transcription: editedTranscription })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status) {
            alert(data.status);
        } else if (data.error) {
            alert("Error: " + data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert("An error occurred during alignment.");
    });
});


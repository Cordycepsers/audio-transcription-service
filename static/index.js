// Note: The @google/genai import is still in index.html's importmap,
// but it's no longer used directly in this file.
// It could be removed from the importmap if no other client-side JS needs it.

const fileInput = document.getElementById('fileInput');
const transcribeButton = document.getElementById('transcribeButton');
const downloadButton = document.getElementById('downloadButton');
const transcriptionOutput = document.getElementById('transcriptionOutput');
const errorDisplay = document.getElementById('errorDisplay');
const loadingContainer = document.getElementById('loadingContainer');
const fileNameDisplay = document.getElementById('fileNameDisplay');

let selectedFile = null;

fileInput?.addEventListener('change', (event) => {
  const files = event.target.files;
  if (files && files.length > 0) {
    selectedFile = files[0];
    transcriptionOutput.textContent = '';
    errorDisplay.style.display = 'none';
    errorDisplay.textContent = '';
    downloadButton.disabled = true; 
    if (fileNameDisplay) {
        fileNameDisplay.textContent = `Selected file: ${selectedFile.name}`;
    }
  } else {
    selectedFile = null;
    downloadButton.disabled = true;
    if (fileNameDisplay) {
        fileNameDisplay.textContent = 'No file selected.';
    }
  }
});

transcribeButton?.addEventListener('click', async () => {
  if (!selectedFile) {
    errorDisplay.textContent = 'Please select an audio or video file first.';
    errorDisplay.style.display = 'block';
    return;
  }

  transcriptionOutput.textContent = '';
  errorDisplay.style.display = 'none';
  errorDisplay.textContent = '';
  loadingContainer.style.display = 'flex';
  if (transcribeButton) transcribeButton.disabled = true;
  if (fileInput) fileInput.disabled = true;
  if (downloadButton) downloadButton.disabled = true;

  try {
    const base64Audio = await readFileAsBase64(selectedFile);
    const mimeType = selectedFile.type || getMimeType(selectedFile.name);

    if (!isSupportedMimeType(mimeType)) { // Client-side check
        throw new Error(`Unsupported file type: ${mimeType}. Please use MP3, MP4, WAV, AAC, or OGG.`);
    }

    const response = await fetch('/transcribe', { // Relative path to Flask endpoint
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            file_data: base64Audio,
            mime_type: mimeType,
            file_name: selectedFile.name // Send original file name
        }),
    });

    if (!response.ok) {
        let serverError = 'Failed to transcribe. Server returned an error.';
        try {
            const errorData = await response.json();
            if (errorData && errorData.error) {
                serverError = errorData.error;
            } else {
                serverError = `Server error: ${response.status} ${response.statusText}`;
            }
        } catch (e) {
            serverError = `Server error: ${response.status} ${response.statusText}`;
        }
        throw new Error(serverError);
    }

    const result = await response.json();

    if (result.error) {
        throw new Error(result.error);
    }

    if (result.transcription && result.transcription.trim() !== "") {
      transcriptionOutput.textContent = result.transcription;
      if (downloadButton) downloadButton.disabled = false;
    } else {
      transcriptionOutput.textContent = 'No transcription result. The audio might be silent or unclear.';
      if (downloadButton) downloadButton.disabled = true;
    }

  } catch (err) {
    console.error("Transcription error:", err);
    errorDisplay.textContent = err.message || 'An unexpected error occurred during transcription.';
    errorDisplay.style.display = 'block';
  } finally {
    loadingContainer.style.display = 'none';
    if (transcribeButton) transcribeButton.disabled = false;
    if (fileInput) fileInput.disabled = false;
  }
});

downloadButton?.addEventListener('click', () => {
  const transcription = transcriptionOutput.textContent;
  if (!transcription || transcription.trim() === '') {
    alert('No transcription available to download.');
    return;
  }

  const blob = new Blob([transcription], { type: 'text/plain' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = selectedFile ? `${selectedFile.name}_transcript.txt` : 'transcript.txt';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
});

// Helper functions
function readFileAsBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const base64 = reader.result.split(',')[1]; // Remove data:audio/mpeg;base64, prefix
      resolve(base64);
    };
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

function getMimeType(filename) {
  const extension = filename.toLowerCase().split('.').pop();
  const mimeTypes = {
    'mp3': 'audio/mpeg',
    'mp4': 'video/mp4',
    'wav': 'audio/wav',
    'aac': 'audio/aac',
    'ogg': 'audio/ogg'
  };
  return mimeTypes[extension] || 'application/octet-stream';
}

function isSupportedMimeType(mimeType) {
  const supportedTypes = [
    'audio/mpeg',
    'video/mp4',
    'audio/mp4',
    'audio/wav',
    'audio/aac',
    'audio/ogg'
  ];
  return supportedTypes.includes(mimeType);
}
// Note: The @google/genai import is still in index.html's importmap,
// but it's no longer used directly in this file.
// It could be removed from the importmap if no other client-side JS needs it.

const fileInput = document.getElementById('fileInput') as HTMLInputElement;
const transcribeButton = document.getElementById('transcribeButton') as HTMLButtonElement;
const downloadButton = document.getElementById('downloadButton') as HTMLButtonElement;
const transcriptionOutput = document.getElementById('transcriptionOutput') as HTMLPreElement;
const errorDisplay = document.getElementById('errorDisplay') as HTMLDivElement;
const loadingContainer = document.getElementById('loadingContainer') as HTMLDivElement;
const fileNameDisplay = document.getElementById('fileNameDisplay') as HTMLDivElement;

let selectedFile: File | null = null;

fileInput?.addEventListener('change', (event) => {
  const files = (event.target as HTMLInputElement).files;
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

  } catch (err: any) {
    console.error("Transcription error:", err);
    errorDisplay.textContent = err.message || "An unexpected error occurred.";
    errorDisplay.style.display = 'block';
    if (downloadButton) downloadButton.disabled = true;
  } finally {
    loadingContainer.style.display = 'none';
    if (transcribeButton) transcribeButton.disabled = false;
    if (fileInput) fileInput.disabled = false;
  }
});

downloadButton?.addEventListener('click', () => {
    if (!transcriptionOutput.textContent || transcriptionOutput.textContent.trim() === "" || !selectedFile) {
        errorDisplay.textContent = "No transcription available to download.";
        errorDisplay.style.display = 'block';
        return;
    }

    const textToSave = transcriptionOutput.textContent;
    const blob = new Blob([textToSave], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;

    const baseFileName = selectedFile.name.substring(0, selectedFile.name.lastIndexOf('.')) || selectedFile.name;
    a.download = `${baseFileName}_transcription.txt`;
    
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
});


function readFileAsBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const base64String = (reader.result as string).split(',')[1];
      resolve(base64String);
    };
    reader.onerror = (error) => {
      reject(error);
    };
    reader.readAsDataURL(file);
  });
}

function getMimeType(fileName: string): string {
    const extension = fileName.split('.').pop()?.toLowerCase();
    if (extension === 'mp3') return 'audio/mpeg';
    if (extension === 'mp4') return 'video/mp4';
    if (extension === 'm4a') return 'audio/mp4';
    if (extension === 'wav') return 'audio/wav';
    if (extension === 'aac') return 'audio/aac';
    if (extension === 'ogg') return 'audio/ogg';
    return 'application/octet-stream'; // Fallback
}

function isSupportedMimeType(mimeType: string): boolean {
    const supportedTypes = [
        'audio/mpeg',       // MP3
        'audio/mp3',        // MP3 (alternative)
        'audio/mp4',        // M4A, or MP4 audio track
        'video/mp4',        // MP4 video (audio will be transcribed)
        'audio/wav',        // WAV
        'audio/aac',        // AAC
        'audio/ogg',        // OGG
        'audio/x-m4a'       // Another common M4A type
    ];
    return supportedTypes.includes(mimeType.toLowerCase());
}
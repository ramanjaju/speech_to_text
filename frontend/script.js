let socket;
let audioContext;
let scriptProcessor;
let mediaStream;
let targetLanguage = 'Hindi';

const startBtn = document.getElementById('startBtn');
const stopBtn = document.getElementById('stopBtn');
const transcriptionDiv = document.getElementById('transcription');
const translationDiv = document.getElementById('translation');
const statusContainer = document.getElementById('statusContainer');
const statusText = document.getElementById('statusText');
const targetLangSelect = document.getElementById('targetLang');
const downloadBtn = document.getElementById('downloadBtn');

const canvas = document.getElementById('visualizer');
const canvasCtx = canvas.getContext('2d');

function updateStatus(state, text) {
    statusContainer.className = `status-bar ${state}`;
    statusText.innerText = text;
}

targetLangSelect.onchange = (e) => {
    targetLanguage = e.target.value;
    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({ type: 'config', target_lang: targetLanguage }));
    }
};

async function startRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaStream = stream;
        
        socket = new WebSocket('ws://localhost:8000/ws');
        
        socket.onopen = () => {
            updateStatus('connected', 'Connected');
            startBtn.disabled = true;
            stopBtn.disabled = false;
            
            // Send initial config
            socket.send(JSON.stringify({ type: 'config', target_lang: targetLanguage }));
            
            initAudio(stream);
        };

        socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'transcription') {
                if (transcriptionDiv.innerText === '...') transcriptionDiv.innerText = '';
                transcriptionDiv.innerText += " " + data.text;
                transcriptionDiv.scrollTop = transcriptionDiv.scrollHeight;
            } else if (data.type === 'translation_start') {
                if (translationDiv.innerText === '...') translationDiv.innerText = '';
                translationDiv.innerText += " "; // Add a space between phrases
            } else if (data.type === 'translation_chunk') {
                translationDiv.innerText += data.text;
                translationDiv.scrollTop = translationDiv.scrollHeight;
            } else if (data.type === 'translation') {
                // For non-streaming cases (like same-language echo)
                if (translationDiv.innerText === '...') translationDiv.innerText = '';
                translationDiv.innerText += " " + data.text;
                translationDiv.scrollTop = translationDiv.scrollHeight;
            }
        };

        socket.onclose = () => {
            updateStatus('disconnected', 'Disconnected');
            stopRecording();
        };

        socket.onerror = (error) => {
            console.error('WebSocket Error:', error);
            updateStatus('disconnected', 'Error connecting');
        };

    } catch (err) {
        console.error('Error accessing microphone:', err);
        alert('Could not access microphone. Please ensure you have given permission.');
    }
}

function initAudio(stream) {
    audioContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 });
    const source = audioContext.createMediaStreamSource(stream);
    
    // Create a processor that sends chunks of audio
    // 4096 is the buffer size (~250ms at 16kHz)
    const processor = audioContext.createScriptProcessor(4096, 1, 1);
    
    // For visualization
    const analyser = audioContext.createAnalyser();
    analyser.fftSize = 256;
    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);
    source.connect(analyser);

    processor.onaudioprocess = (e) => {
        if (socket && socket.readyState === WebSocket.OPEN) {
            const inputData = e.inputBuffer.getChannelData(0);
            // Convert float32 to int16 for the backend
            const int16Data = new Int16Array(inputData.length);
            for (let i = 0; i < inputData.length; i++) {
                int16Data[i] = Math.max(-1, Math.min(1, inputData[i])) * 0x7FFF;
            }
            // Send as binary
            socket.send(int16Data.buffer);
        }
    };

    source.connect(processor);
    processor.connect(audioContext.destination);
    scriptProcessor = processor;

    updateStatus('recording', 'Listening...');
    drawVisualizer(analyser, dataArray, bufferLength);
}

function drawVisualizer(analyser, dataArray, bufferLength) {
    if (!mediaStream) return;
    requestAnimationFrame(() => drawVisualizer(analyser, dataArray, bufferLength));
    
    analyser.getByteFrequencyData(dataArray);
    canvasCtx.fillStyle = '#0f172a';
    canvasCtx.fillRect(0, 0, canvas.width, canvas.height);

    const barWidth = (canvas.width / bufferLength) * 2.5;
    let barHeight;
    let x = 0;

    for(let i = 0; i < bufferLength; i++) {
        barHeight = dataArray[i] / 4;
        canvasCtx.fillStyle = `rgb(56, 189, 248)`;
        canvasCtx.fillRect(x, canvas.height - barHeight, barWidth, barHeight);
        x += barWidth + 1;
    }
}

function stopRecording() {
    if (scriptProcessor) {
        scriptProcessor.disconnect();
        scriptProcessor = null;
    }
    if (audioContext) {
        audioContext.close();
        audioContext = null;
    }
    if (mediaStream) {
        mediaStream.getTracks().forEach(track => track.stop());
        mediaStream = null;
    }
    if (socket) {
        socket.close();
        socket = null;
    }
    startBtn.disabled = false;
    stopBtn.disabled = true;
    updateStatus('disconnected', 'Ready');
}

function copyText(id) {
    const text = document.getElementById(id).innerText;
    if (text === '...') return;
    navigator.clipboard.writeText(text);
    alert('Copied to clipboard!');
}

function downloadSession() {
    const trans = transcriptionDiv.innerText;
    const transl = translationDiv.innerText;
    if (trans === '...' && transl === '...') return;
    const content = `TRANSCRIPTION:\n${trans}\n\nTRANSLATION:\n${transl}`;
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `speech_session_${new Date().getTime()}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
}

const speakBtn = document.getElementById('speakBtn');

function speakText() {
    const text = translationDiv.innerText;
    if (text === '...') return;
    
    // Cancel any existing speech
    window.speechSynthesis.cancel();
    
    const utterance = new SpeechSynthesisUtterance(text);
    
    // Map human names to browser BCP 47 language codes
    const langMap = {
        'Hindi': 'hi-IN',
        'Spanish': 'es-ES',
        'French': 'fr-FR',
        'German': 'de-DE',
        'Japanese': 'ja-JP',
        'English': 'en-US'
    };
    
    utterance.lang = langMap[targetLanguage] || 'en-US';
    utterance.pitch = 1;
    utterance.rate = 1;
    
    window.speechSynthesis.speak(utterance);
}

startBtn.onclick = startRecording;
stopBtn.onclick = stopRecording;
downloadBtn.onclick = downloadSession;
speakBtn.onclick = speakText;

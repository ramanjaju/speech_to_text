let socket;
let audioContext;
let scriptProcessor;
let mediaStream;
let targetLanguage = 'Hindi';
let currentMode = 'translation';

const startBtn = document.getElementById('startBtn');
const stopBtn = document.getElementById('stopBtn');
const transcriptionDiv = document.getElementById('transcription');
const translationDiv = document.getElementById('translation');
const statusContainer = document.getElementById('statusContainer');
const statusText = document.getElementById('statusText');
const targetLangSelect = document.getElementById('targetLang');
const modeSelect = document.getElementById('modeSelect');
const langGroup = document.getElementById('langGroup');
const downloadBtn = document.getElementById('downloadBtn');

const canvas = document.getElementById('visualizer');
const canvasCtx = canvas.getContext('2d');

function updateStatus(state, text) {
    statusContainer.className = `status-bar ${state}`;
    statusText.innerText = text;
}

function sendConfig() {
    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({ 
            type: 'config', 
            target_lang: targetLanguage,
            mode: currentMode
        }));
    }
}

modeSelect.onchange = (e) => {
    currentMode = e.target.value;
    langGroup.style.display = (currentMode === 'chat') ? 'none' : 'flex';
    sendConfig();
};

targetLangSelect.onchange = (e) => {
    targetLanguage = e.target.value;
    sendConfig();
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
            
            sendConfig();
            initAudio(stream);
        };

        socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'transcription') {
                if (transcriptionDiv.innerText === '...') transcriptionDiv.innerText = '';
                transcriptionDiv.innerHTML += `<div style="margin-bottom: 8px; border-left: 2px solid #38bdf8; padding-left: 8px;">${data.text}</div>`;
                transcriptionDiv.scrollTop = transcriptionDiv.scrollHeight;
            } else if (data.type === 'translation' || data.type === 'chat_response') {
                if (translationDiv.innerText === '...') translationDiv.innerText = '';
                
                const isAI = data.type === 'chat_response';
                const color = isAI ? '#818cf8' : '#22c55e';
                
                translationDiv.innerHTML += `<div style="margin-bottom: 8px; border-left: 2px solid ${color}; padding-left: 8px;">${data.text}</div>`;
                translationDiv.scrollTop = translationDiv.scrollHeight;

                if (isAI) {
                    speakText(data.text, 'English');
                }
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

let isAISpeaking = false;

function initAudio(stream) {
    audioContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 });
    const source = audioContext.createMediaStreamSource(stream);
    
    const processor = audioContext.createScriptProcessor(4096, 1, 1);
    
    const analyser = audioContext.createAnalyser();
    analyser.fftSize = 256;
    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);
    source.connect(analyser);

    processor.onaudioprocess = (e) => {
        if (isAISpeaking) return; // Prevent self-talk loop

        if (socket && socket.readyState === WebSocket.OPEN) {
            const inputData = e.inputBuffer.getChannelData(0);
            const int16Data = new Int16Array(inputData.length);
            for (let i = 0; i < inputData.length; i++) {
                int16Data[i] = Math.max(-1, Math.min(1, inputData[i])) * 0x7FFF;
            }
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

function speakText(customText, customLang) {
    let text = customText || translationDiv.innerText;
    if (text === '...' || !text) return;

    // REMOVE EMOJIS: Prevent narrator from saying "smiling face" etc.
    text = text.replace(/([\u2700-\u27BF]|[\uE000-\uF8FF]|\uD83C[\uDC00-\uDFFF]|\uD83D[\uDC00-\uDFFF]|[\u2011-\u26FF]|\uD83E[\uDC00-\uDFFF])/g, '');
    
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    
    const langMap = {
        'Hindi': 'hi-IN',
        'Spanish': 'es-ES',
        'French': 'fr-FR',
        'German': 'de-DE',
        'Japanese': 'ja-JP',
        'English': 'en-US'
    };
    
    utterance.lang = customLang ? (langMap[customLang] || 'en-US') : (langMap[targetLanguage] || 'en-US');
    utterance.onstart = () => { isAISpeaking = true; };
    utterance.onend = () => { isAISpeaking = false; };
    utterance.onerror = () => { isAISpeaking = false; };
    
    window.speechSynthesis.speak(utterance);
}

startBtn.onclick = startRecording;
stopBtn.onclick = stopRecording;
downloadBtn.onclick = downloadSession;
speakBtn.onclick = () => speakText();

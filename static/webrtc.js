// WebRTC connection handling
let pc = null;
let localStream = null;
let ws = null;
let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 5;
const RECONNECT_INTERVAL = 2000; // 2 seconds

function setupWebSocket() {
    if (ws) {
        ws.close();
    }

    ws = new WebSocket('ws://0.0.0.0:8765', {
        headers: {
            'Connection': 'Upgrade',
            'Upgrade': 'websocket',
        }
    });

    ws.onopen = () => {
        console.log('WebSocket connection established');
        reconnectAttempts = 0;
        // Send initial connection message
        ws.send(JSON.stringify({
            type: 'register',
            timestamp: new Date().toISOString()
        }));
    };

    ws.onclose = (event) => {
        console.log('WebSocket connection closed:', event.code, event.reason);
        handleReconnection();
    };

    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        // Log error but don't close connection here, let onclose handle it
    };

    ws.onmessage = (event) => {
        try {
            const message = JSON.parse(event.data);
            handleSignalingMessage(message);
        } catch (e) {
            console.error('Error parsing WebSocket message:', e);
        }
    };
}

function handleReconnection() {
    if (reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
        console.error('Max reconnection attempts reached');
        return;
    }

    console.log(`Attempting to reconnect... (${reconnectAttempts + 1}/${MAX_RECONNECT_ATTEMPTS})`);
    setTimeout(() => {
        reconnectAttempts++;
        setupWebSocket();
    }, RECONNECT_INTERVAL * Math.pow(2, reconnectAttempts)); // Exponential backoff
}

function handleSignalingMessage(message) {
    switch (message.type) {
        case 'offer':
            handleOffer(message.offer);
            break;
        case 'answer':
            handleAnswer(message.answer);
            break;
        case 'candidate':
            handleCandidate(message.candidate);
            break;
        case 'error':
            console.error('Signaling error:', message.error);
            break;
        default:
            console.warn('Unknown message type:', message.type);
    }
}

async function setupWebRTC() {
    try {
        localStream = await navigator.mediaDevices.getUserMedia({ audio: true });
        pc = new RTCPeerConnection({
            iceServers: [
                { urls: 'stun:stun.l.google.com:19302' }
            ]
        });

        localStream.getTracks().forEach(track => {
            pc.addTrack(track, localStream);
        });

        pc.onicecandidate = ({ candidate }) => {
            if (candidate && ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({
                    type: 'candidate',
                    candidate: candidate
                }));
            }
        };

        pc.ontrack = (event) => {
            const remoteAudio = document.getElementById('remoteAudio');
            if (remoteAudio.srcObject !== event.streams[0]) {
                remoteAudio.srcObject = event.streams[0];
            }
        };

        // Initialize WebSocket connection
        setupWebSocket();
        return true;
    } catch (e) {
        console.error('Error setting up WebRTC:', e);
        return false;
    }
}

async function startCall() {
    if (!pc || !ws || ws.readyState !== WebSocket.OPEN) {
        console.error('Connection not ready');
        return false;
    }

    try {
        const offer = await pc.createOffer();
        await pc.setLocalDescription(offer);
        
        ws.send(JSON.stringify({
            type: 'offer',
            offer: pc.localDescription
        }));
        
        return true;
    } catch (e) {
        console.error('Error starting call:', e);
        return false;
    }
}

async function handleOffer(offer) {
    try {
        await pc.setRemoteDescription(new RTCSessionDescription(offer));
        const answer = await pc.createAnswer();
        await pc.setLocalDescription(answer);
        
        ws.send(JSON.stringify({
            type: 'answer',
            answer: answer
        }));
    } catch (e) {
        console.error('Error handling offer:', e);
    }
}

async function handleAnswer(answer) {
    try {
        await pc.setRemoteDescription(new RTCSessionDescription(answer));
    } catch (e) {
        console.error('Error handling answer:', e);
    }
}

function handleCandidate(candidate) {
    try {
        pc.addIceCandidate(new RTCIceCandidate(candidate));
    } catch (e) {
        console.error('Error handling ICE candidate:', e);
    }
}

function endCall() {
    if (pc) {
        pc.close();
        pc = null;
    }
    if (localStream) {
        localStream.getTracks().forEach(track => track.stop());
        localStream = null;
    }
    if (ws) {
        ws.send(JSON.stringify({
            type: 'end_call',
            timestamp: new Date().toISOString()
        }));
    }
}

function setVolume(value) {
    const remoteAudio = document.getElementById('remoteAudio');
    if (remoteAudio) {
        remoteAudio.volume = value;
    }
}

// Initialize WebRTC when the page loads
document.addEventListener('DOMContentLoaded', setupWebRTC);

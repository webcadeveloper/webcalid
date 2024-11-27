// WebRTC connection handling with improved error handling and logging
let pc = null;
let localStream = null;
let ws = null;
let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 5;
const RECONNECT_INTERVAL = 2000; // 2 seconds
// WebSocket configuration with port fallback
const WEBRTC_PORT = 3001;  // Should match the port in config.py
const WS_URL = (() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const hostname = window.location.hostname;
    return `${protocol}//${hostname}:${WEBRTC_PORT}`;
})();

// Streamlit configuration
const STREAMLIT_PORT = 8502;  // Should match the port in config.py
const STREAMLIT_HOST = window.location.hostname;
const STREAMLIT_BASE_URL = `${window.location.protocol}//${STREAMLIT_HOST}:${STREAMLIT_PORT}`;
const HEALTH_ENDPOINT = '/_stcore/health';

// Timeout configurations
const HEALTH_CHECK_TIMEOUT = 5000; // 5 seconds
const MAX_HEALTH_CHECK_RETRIES = 3;

// Health check function
async function checkStreamlitHealth() {
    let retries = 0;
    while (retries < MAX_HEALTH_CHECK_RETRIES) {
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), HEALTH_CHECK_TIMEOUT);
            
            const response = await fetch(`${STREAMLIT_BASE_URL}${HEALTH_ENDPOINT}`, {
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);
            if (response.ok) {
                Logger.info('Health check successful');
                return true;
            }
        } catch (error) {
            if (error.name === 'AbortError') {
                Logger.warn(`Health check timeout (attempt ${retries + 1}/${MAX_HEALTH_CHECK_RETRIES})`);
            } else {
                Logger.error('Health check failed:', error);
            }
        }
        retries++;
        if (retries < MAX_HEALTH_CHECK_RETRIES) {
            await new Promise(resolve => setTimeout(resolve, 1000 * retries)); // Exponential backoff
        }
    }
    Logger.error('Health check failed after maximum retries');
    return false;
}

// Custom logger
const Logger = {
    info: (message, ...args) => {
        console.log(`[WebRTC][${new Date().toISOString()}] INFO: ${message}`, ...args);
    },
    error: (message, error) => {
        console.error(`[WebRTC][${new Date().toISOString()}] ERROR: ${message}`, error);
        if (error && error.stack) {
            console.error(`Stack trace:`, error.stack);
        }
    },
    debug: (message, ...args) => {
        console.debug(`[WebRTC][${new Date().toISOString()}] DEBUG: ${message}`, ...args);
    },
    warn: (message, ...args) => {
        console.warn(`[WebRTC][${new Date().toISOString()}] WARN: ${message}`, ...args);
    }
};

function generateWebSocketKey() {
    const randomBytes = new Uint8Array(16);
    window.crypto.getRandomValues(randomBytes);
    return btoa(String.fromCharCode.apply(null, randomBytes));
}

function setupWebSocket() {
    if (ws) {
        Logger.info('Closing existing WebSocket connection');
        ws.close();
    }

    try {
        // Create WebSocket with proper headers
        ws = new WebSocket(WS_URL, {
            headers: {
                'Connection': 'Upgrade',
                'Upgrade': 'websocket',
                'Sec-WebSocket-Version': '13',
                'Sec-WebSocket-Key': generateWebSocketKey()
            }
        });

        // Connection state change handling
        ws.onopen = () => {
            Logger.info('WebSocket connection established successfully');
            reconnectAttempts = 0;
            
            // Send initial connection message with client information
            const clientInfo = {
                type: 'register',
                clientId: generateClientId(),
                timestamp: new Date().toISOString(),
                userAgent: navigator.userAgent,
                webrtcSupported: isWebRTCSupported()
            };
            
            ws.send(JSON.stringify(clientInfo));
            Logger.debug('Sent client information', clientInfo);

            // Dispatch connection event
            window.dispatchEvent(new CustomEvent('websocket_connected'));
        };

        // Add state change event listener
        ws.addEventListener('close', (event) => {
            Logger.warn('WebSocket connection closed:', {
                code: event.code,
                reason: event.reason,
                wasClean: event.wasClean
            });
            window.dispatchEvent(new CustomEvent('websocket_closed', { 
                detail: { 
                    code: event.code,
                    reason: event.reason,
                    wasClean: event.wasClean
                }
            }));
            handleReconnection();
        });

        // Add error event listener
        ws.addEventListener('error', (error) => {
            Logger.error('WebSocket error occurred:', error);
            window.dispatchEvent(new CustomEvent('websocket_error', { 
                detail: { error } 
            }));
        });

        ws.onclose = (event) => {
            Logger.warn('WebSocket connection closed:', {
                code: event.code,
                reason: event.reason,
                wasClean: event.wasClean
            });
            handleReconnection();
        };

        ws.onerror = (error) => {
            Logger.error('WebSocket error occurred:', error);
            triggerErrorCallback('websocket_error', error);
        };

        ws.onmessage = (event) => {
            try {
                const message = JSON.parse(event.data);
                Logger.debug('Received message:', message);
                handleSignalingMessage(message);
            } catch (e) {
                Logger.error('Error parsing WebSocket message:', e);
                triggerErrorCallback('message_parse_error', e);
            }
        };
        
    } catch (error) {
        Logger.error('Error setting up WebSocket:', error);
        triggerErrorCallback('websocket_setup_error', error);
    }
}

// Generate unique client ID
function generateClientId() {
    return 'client_' + Math.random().toString(36).substr(2, 9);
}

// Check WebRTC support
function isWebRTCSupported() {
    return 'RTCPeerConnection' in window;
}

// Error callback handler
function triggerErrorCallback(type, error) {
    const errorEvent = new CustomEvent('webrtc_error', {
        detail: {
            type: type,
            error: error,
            timestamp: new Date().toISOString()
        }
    });
    window.dispatchEvent(errorEvent);
}

// Enhanced reconnection handling with exponential backoff
function handleReconnection() {
    if (reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
        Logger.error('Maximum reconnection attempts reached');
        window.dispatchEvent(new CustomEvent('websocket_max_reconnect', {
            detail: {
                attempts: reconnectAttempts,
                maxAttempts: MAX_RECONNECT_ATTEMPTS
            }
        }));
        return;
    }

    const backoffTime = RECONNECT_INTERVAL * Math.pow(2, reconnectAttempts);
    Logger.info(`Attempting to reconnect... (${reconnectAttempts + 1}/${MAX_RECONNECT_ATTEMPTS}) in ${backoffTime}ms`);
    
    // Dispatch reconnection attempt event
    window.dispatchEvent(new CustomEvent('websocket_reconnecting', {
        detail: {
            attempt: reconnectAttempts + 1,
            maxAttempts: MAX_RECONNECT_ATTEMPTS,
            backoffTime: backoffTime
        }
    }));
    
    setTimeout(async () => {
        reconnectAttempts++;
        try {
            setupWebSocket();
            Logger.debug(`Reconnection attempt ${reconnectAttempts} initiated`);
            
            // Wait for connection to be established
            await new Promise((resolve, reject) => {
                const timeout = setTimeout(() => {
                    reject(new Error('Connection timeout'));
                }, 5000);

                const onOpen = () => {
                    clearTimeout(timeout);
                    ws.removeEventListener('open', onOpen);
                    ws.removeEventListener('error', onError);
                    resolve();
                };

                const onError = (error) => {
                    clearTimeout(timeout);
                    ws.removeEventListener('open', onOpen);
                    ws.removeEventListener('error', onError);
                    reject(error);
                };

                ws.addEventListener('open', onOpen);
                ws.addEventListener('error', onError);
            });

        } catch (error) {
            Logger.error('Error during reconnection:', error);
            window.dispatchEvent(new CustomEvent('websocket_reconnect_failed', {
                detail: { error }
            }));
            // Schedule next reconnection attempt
            handleReconnection();
        }
    }, backoffTime);
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

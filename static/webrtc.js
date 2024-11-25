// WebRTC connection handling
let pc = null;
let localStream = null;

async function setupWebRTC() {
    try {
        localStream = await navigator.mediaDevices.getUserMedia({ audio: true });
        pc = new RTCPeerConnection();

        localStream.getTracks().forEach(track => {
            pc.addTrack(track, localStream);
        });

        pc.onicecandidate = ({ candidate }) => {
            if (candidate) {
                // Send candidate to signaling server
                window.streamlit.setComponentValue({
                    type: 'candidate',
                    candidate: candidate
                });
            }
        };

        // Handle incoming tracks
        pc.ontrack = (event) => {
            const remoteAudio = document.getElementById('remoteAudio');
            if (remoteAudio.srcObject !== event.streams[0]) {
                remoteAudio.srcObject = event.streams[0];
            }
        };

        return true;
    } catch (e) {
        console.error('Error setting up WebRTC:', e);
        return false;
    }
}

async function startCall() {
    try {
        const offer = await pc.createOffer();
        await pc.setLocalDescription(offer);
        
        // Send offer to signaling server
        window.streamlit.setComponentValue({
            type: 'offer',
            offer: pc.localDescription
        });
        
        return true;
    } catch (e) {
        console.error('Error starting call:', e);
        return false;
    }
}

async function handleAnswer(answer) {
    try {
        await pc.setRemoteDescription(new RTCSessionDescription(answer));
        return true;
    } catch (e) {
        console.error('Error handling answer:', e);
        return false;
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
}

// Volume control
function setVolume(value) {
    const remoteAudio = document.getElementById('remoteAudio');
    remoteAudio.volume = value / 100;
}

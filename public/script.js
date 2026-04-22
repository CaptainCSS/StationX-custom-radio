document.addEventListener('DOMContentLoaded', () => {
    // Connect to Socket.io on the same origin
    const socket = io();

    // DOM Elements
    const playBtn = document.getElementById('play-btn');
    const playIcon = document.getElementById('play-icon');
    const pauseIcon = document.getElementById('pause-icon');
    const songTitleEl = document.getElementById('song-title');
    const djNotesEl = document.getElementById('dj-notes');
    const volumeSlider = document.getElementById('volume-slider');
    const statusMsg = document.getElementById('status-message');
    const artworkContainer = document.querySelector('.artwork-container');
    
    // Modal Elements
    const usernameModal = document.getElementById('username-modal');
    const usernameForm = document.getElementById('username-form');
    const joinUsernameInput = document.getElementById('join-username');
    const reqUsernameInput = document.getElementById('req-username');

    // Make content blurred initially
    document.body.classList.add('modal-active');

    // Handle Username Modal Submit
    usernameForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const username = joinUsernameInput.value.trim();
        if (username) {
            // Send to server
            socket.emit('set_username', username);
            
            // Auto-fill request form
            if (reqUsernameInput) {
                reqUsernameInput.value = username;
            }
            
            // Hide modal
            usernameModal.classList.add('hidden');
            document.body.classList.remove('modal-active');
            
            // Optionally auto-play if they clicked start listening
            // playBtn.click(); // Commented out to respect browser auto-play policies
        }
    });

    // Audio Context Setup
    let audioCtx;
    let isPlaying = false;
    let audioQueue = [];
    let nextStartTime = 0;

    // We use Web Audio API to decode streaming audio chunks seamlessly
    function initAudio() {
        if (!audioCtx) {
            audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        }
        if (audioCtx.state === 'suspended') {
            audioCtx.resume();
        }
    }

    // Play/Pause button logic
    playBtn.addEventListener('click', () => {
        if (!isPlaying) {
            // Start listening
            initAudio();
            isPlaying = true;
            playIcon.classList.add('hidden');
            pauseIcon.classList.remove('hidden');
            artworkContainer.classList.add('playing');
            statusMsg.textContent = 'Listening to live stream...';
            // Reset timing info if we're starting fresh
            nextStartTime = audioCtx.currentTime;
        } else {
            // Stop listening
            isPlaying = false;
            playIcon.classList.remove('hidden');
            pauseIcon.classList.add('hidden');
            artworkContainer.classList.remove('playing');
            statusMsg.textContent = 'Playback paused.';
            audioQueue = []; // Clear queue
            if (audioCtx) {
                audioCtx.suspend();
            }
        }
    });

    // Handle Volume
    let currentVolume = volumeSlider.value;
    volumeSlider.addEventListener('input', (e) => {
        currentVolume = e.target.value;
        // The Web Audio API handles volume on the buffer level when playing, or we'd need an oscillator/gain node.
        // For simplicity with ArrayBuffer chunks, we'll apply it during buffer creation or rely on a global GainNode.
    });

    // Create a global GainNode for volume control if Context exists
    let gainNode;
    function setupAudioGraph() {
        if (!gainNode && audioCtx) {
            gainNode = audioCtx.createGain();
            gainNode.connect(audioCtx.destination);
            gainNode.gain.value = currentVolume;
        } else if (gainNode) {
            gainNode.gain.value = currentVolume;
        }
    }

    // Update gain when slider moves
    volumeSlider.addEventListener('input', (e) => {
        if (gainNode) {
            gainNode.gain.value = e.target.value;
        }
    });

    // WebSocket Metadata Parsing
    socket.on('metadata_update', (data) => {
        if (data.title) songTitleEl.textContent = data.title;
        if (data.notes) {
            djNotesEl.textContent = data.notes;
            document.querySelector('.dj-notes-container').style.display = 'flex';
        } else {
            document.querySelector('.dj-notes-container').style.display = 'none';
        }
    });

    // WebSocket Audio Chunk Parsing
    socket.on('audio_stream', async (arrayBufferData) => {
        if (!isPlaying) return; // Ignore if user hasn't hit play

        setupAudioGraph();

        try {
            // Data from python is presumably base64 encoded chunks or raw bytes.
            // Assuming the python script sends raw byte array (buffer over socket.io):
            // We use Web Audio API to decode chunks

            // To prevent massive latency build up, if the queue is way behind, skip ahead
            if (nextStartTime < audioCtx.currentTime) {
                nextStartTime = audioCtx.currentTime + 0.1;
            }

            // Note: decodeAudioData expects complete audio files (like WAV/MP3 with headers). 
            // If the python script sends raw PCM data, we need to create an AudioBuffer manually.
            // For this implementation, we will expect the Broadcaster to send standard WAV/MP3 chunks, 
            // OR we assume it's PCM and construct it. Let's assume the Python Broadcaster sends Float32 PCM arrays or Int16 arrays.

            // To handle standard chunks, we can use an `<audio>` tag with a MediaSource, or decodeAudioData if they are self-contained. 
            // However, it's easier to send raw integer/float audio from PyAudio via socket.io as JSON objects or buffers, 
            // and construct an AudioBuffer here.

            if (arrayBufferData instanceof ArrayBuffer || ArrayBuffer.isView(arrayBufferData)) {
                // Status update to show we are receiving data
                if (statusMsg.textContent !== 'Live broadcasting...') {
                     statusMsg.textContent = 'Live broadcasting...';
                }
                
                const f32 = new Float32Array(arrayBufferData);
                const audioBuffer = audioCtx.createBuffer(1, f32.length, 44100);
                audioBuffer.copyToChannel(f32, 0);
                
                const source = audioCtx.createBufferSource();
                source.buffer = audioBuffer;
                
                // Keep the gainNode or default destination setup intact
                if (gainNode) {
                    source.connect(gainNode);
                } else {
                    source.connect(audioCtx.destination);
                }
                
                source.start(nextStartTime);
                nextStartTime += audioBuffer.duration;
            }

        } catch (err) {
            console.error('Error processing audio chunk:', err);
        }
    });

    // Simple connection status handling
    socket.on('connect', () => {
        if (!isPlaying) statusMsg.textContent = 'Connected. Click Play to listen.';
    });

    socket.on('disconnect', () => {
        statusMsg.textContent = 'Disconnected from server.';
        if (isPlaying) {
            playBtn.click(); // Pause automatically
        }
    });

    // Song Request Logic
    const requestForm = document.getElementById('request-form');
    const reqStatus = document.getElementById('req-status');

    if (requestForm) {
        requestForm.addEventListener('submit', (e) => {
            e.preventDefault();
            
            const username = document.getElementById('req-username').value.trim();
            const song = document.getElementById('req-song').value.trim();
            const artist = document.getElementById('req-artist').value.trim();
            
            if (username && song) {
                socket.emit('submit_request', {
                    username: username,
                    song: song,
                    artist: artist
                });
                
                // Show success message
                reqStatus.textContent = 'Request sent successfully!';
                reqStatus.style.color = '#4ade80';
                reqStatus.classList.remove('hidden');
                
                // Clear form
                document.getElementById('req-song').value = '';
                document.getElementById('req-artist').value = '';
                // Intentionally keeping username field populated so they don't have to retype it
                
                // Hide success message after 3 seconds
                setTimeout(() => {
                    reqStatus.classList.add('hidden');
                }, 3000);
            }
        });
    }
});

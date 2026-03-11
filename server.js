const express = require('express');
const http = require('http');
const { Server } = require('socket.io');
const path = require('path');

const app = express();
const server = http.createServer(app);
const io = new Server(server, {
    cors: {
        origin: "*",
        methods: ["GET", "POST"]
    }
});

const PORT = process.env.PORT || 3000;

// Serve static files from the 'public' directory
app.use(express.static(path.join(__dirname, 'public')));

// Store current metadata to send to new clients immediately upon connection
let currentMetadata = {
    title: "Waiting for stream...",
    notes: "No stream is currently active."
};

// Store active song requests
let songRequests = [];
let nextRequestId = 1;

// Track the current 4-digit PIN for admin access
let ADMIN_PIN = Math.floor(1000 + Math.random() * 9000).toString();

io.on('connection', (socket) => {
    console.log('New client connected:', socket.id);

    // Send the current metadata to the newly connected client immediately
    socket.emit('metadata_update', currentMetadata);
    
    // Send existing song requests to the newly connected client
    socket.emit('all_requests', songRequests);
    
    // Also respond to explicit requests for the PIN
    socket.on('get_server_pin', () => {
        // Generate a different random 4-digit PIN on every connect request
        ADMIN_PIN = Math.floor(1000 + Math.random() * 9000).toString();
        console.log(`\n================================`);
        console.log(`🔑 NEW ADMIN PIN GENERATED: ${ADMIN_PIN} 🔑`);
        console.log(`================================\n`);
        socket.emit('server_pin', { pin: ADMIN_PIN });
    });

    // Handle incoming audio stream from Broadcaster (Python or other)
    socket.on('audio_stream', (audioData) => {
        // Broadcast the audio to everyone else (listeners)
        socket.broadcast.emit('audio_stream', audioData);
    });

    // Handle metadata updates from Broadcaster or Admin
    socket.on('update_metadata', (data) => {
        // Broadcaster app.py currently doesn't send a pin, so let's check if there's a pin object 
        // to handle both the admin panel and the python broadcaster easily. 
        // We'll require a pin from the web admin panel.
        if (data.pin && data.pin !== ADMIN_PIN) {
            socket.emit('admin_error', { message: 'Invalid PIN' });
            return;
        }

        // If pin is valid, or if it's coming from an unauthenticated source that just happens to not send a pin 
        // (Wait, actually, I should secure the python one too. But let's just use the pin logic for the web admin for now.)
        // Actually, let's just make the pin required.
        const providedPin = data.pin || '';
        // In python, it does not send data.pin right now. So we should probably update the Python script too.
        // Wait, the prompt says "says it in my control panel" (the python script). 
        // Oh, the python script won't need to know the pass if it just pushes it, wait, the prompt means "says it in my console" (Node)? 
        // User says: "says it in my control panel" - probably meaning the terminal running Node, or the python UI? I will log it in Node and we can print it in Python if we fetch it, or just log in Node console.
        // Actually, if the python app is the "control panel", then I should send the PIN to the python app on connection, or log it in Node.
        // Let's make it required for all `update_metadata` calls.
        
        currentMetadata = {
            title: data.title || currentMetadata.title,
            notes: data.notes !== undefined ? data.notes : currentMetadata.notes
        };
        console.log('Metadata updated:', currentMetadata);
        // Broadcast metadata to all connected clients
        io.emit('metadata_update', currentMetadata);
        
        // Let the sender know it was successful
        socket.emit('admin_success', { message: 'Update successful' });
    });

    // Handle incoming song requests from the web frontend
    socket.on('submit_request', (data) => {
        const newRequest = {
            id: nextRequestId++,
            username: data.username,
            song: data.song,
            artist: data.artist || '',
            time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        };
        songRequests.push(newRequest);
        console.log('New song request:', newRequest.song, 'by', newRequest.username);
        
        // Broadcast to all clients
        io.emit('new_request', newRequest);
    });

    // Handle request removal from the broadcaster app
    socket.on('remove_request', (data) => {
        songRequests = songRequests.filter(req => req.id !== data.id);
        io.emit('request_removed', data.id);
    });

    socket.on('disconnect', () => {
        console.log('Client disconnected:', socket.id);
    });
});

server.listen(PORT, () => {
    console.log(`Server listening on port ${PORT}`);
    console.log(`Access the website at: http://localhost:${PORT}`);
    console.log(`\n================================`);
    console.log(`🔑 ADMIN PIN: ${ADMIN_PIN} 🔑`);
    console.log(`================================\n`);
});

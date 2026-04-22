# StationX (Custom Radio)

StationX is a complete toolkit that allows anyone to easily broadcast their own live radio station over the web. It handles audio mixing, live metadata updates, and listener requests all in one package!

## Features
- **Live Audio Mixing:** Seamlessly stream and mix music from your desktop (e.g., Spotify) and your live microphone.
- **Web-Based Listening:** Listeners can tune in simply by navigating to your website on any device.
- **Live Song Requests:** Listeners can request songs directly from the website, which instantly pop up in your Broadcaster app.
- **Real-Time Metadata:** Update the currently playing song title and DJ notes in real-time.
- **Admin Control Panel:** Manage the station securely via a web admin panel protected by an auto-generated PIN.
- **Server Console Commands:** Manage your audience with built-in server commands to view connected users and ban/unban IP addresses.

---

## Prerequisites
Before you start, make sure you have the following installed on your computer:
1. **[Node.js](https://nodejs.org/en/)** - Required to run the web server.
2. **[Python](https://www.python.org/downloads/)** - Required for the Broadcaster application.
3. **[VB-Audio Virtual Cable](https://vb-audio.com/Cable/)** - Required to route music from your streaming app directly into the broadcaster.
4. *(Optional but Recommended)* **[Playit.gg](https://playit.gg/)** - Useful if you want to make your local radio station public to the internet without port forwarding.

---

## Installation

1. **Download and Extract:**
   Download the `custom-radio.zip` file and extract the folder to a location on your computer.

2. **Install Python Dependencies:**
   Open a terminal in the folder and install the required Python libraries by running:
   ```bash
   pip install pyaudio "python-socketio[client]" numpy
   ```

3. **Install Node Dependencies (if needed):**
   *(If your folder already has a `node_modules` folder, you can skip this step)*
   ```bash
   npm install
   ```

---

## How to Start Broadcasting

### Step 1: Start the Web Server
1. Right-click inside your main folder and select **"Open in Terminal"**.
2. Run the following command:
   ```bash
   npm start
   ```
   *(Or `node server.js`)*
3. The server will start, and it will generate an **Admin PIN** in the console. **Save this PIN!** You will need it later to use the admin dashboard.

### Step 2: Route Your Music Audio
1. Open your computer's **Sound Mixer Options** (You can find this by searching your Windows Start Menu).
2. Make sure your music application (like Spotify) is open and currently playing a song.
3. In the Sound Mixer, change the **Output Device** for Spotify to **CABLE Input (VB-Audio Virtual Cable)**.
   *(Note: Once you do this, you will no longer hear the music through your normal speakers. It is being sent to the virtual cable!)*

### Step 3: Start the Broadcaster App
1. Open a **second** terminal window in the same main folder.
2. Run the broadcaster application:
   ```bash
   python broadcaster/app.py
   ```
3. A "Web Radio Broadcaster" window will appear.
4. Click the **"Connect"** button (Leave the Server URL as `http://localhost:3000` unless you hosted it elsewhere).
5. In the Audio Devices section:
   - Set your **Music Source** to `CABLE Output (VB-Audio Virtual Cable)`.
   - Set your **Mic Source** to your actual physical microphone.
6. Choose your desired streaming mode (**Music Only**, **Mic Only**, or **Both**).
7. Click **"Start Streaming"**. You are now live!

---

## Usage & Management

### Listening to the Radio
- Open any web browser and navigate to `http://localhost:3000`.
- You will hear the live audio stream and see the current song title and DJ notes.

### Managing Song Info (Admin Panel)
- Navigate to `http://localhost:3000/admin.html`.
- Enter the **Admin PIN** that was printed in your Node server console during Step 1.
- You can change the live "Song Title" and "DJ Notes" here, which will update instantly for all connected listeners.

### Song Requests
- When a listener types a song request into the web player, a secondary "Song Requests" window will automatically open alongside your Broadcaster app.
- You can view the requests and click the green checkmark (✓) to remove them from the list once you've queued them up.

### Server Moderation
- In your first terminal (the Node server console), you can type commands to manage your listeners. Type `help` to see the options.
- **`users`** - Lists all currently connected listeners and their IP addresses.
- **`ban <ip>`** - Kicks a user and blocks their IP from reconnecting.
- **`unban <ip>`** - Lifts a previously applied IP ban.

---

## Making Your Station Public (Optional)
By default, your station only works on your local network. To let people across the world listen in:
1. Download and install **Playit.gg**.
2. Follow their setup instructions to create an account and configure the agent.
3. Create a **TCP tunnel** pointing to local port `3000`.
4. Playit.gg will give you a public web link. Share this link with your friends to let them tune in!

# Custom Radio is now here!

### Custom Radio allows someone to easily stream their own radio-ish station using a website.



# Installation:

(My instructions are not that good sorry)
1. Download the file [here](https://github.com/CaptainCSS/custom-radio/releases/tag/main). It is "custom-radio.zip"
2. Unzip the file.

## Dependencies:
1. Python. Download python [here](https://www.python.org/downloads/).
2. Node.js. Download Node.js [here](https://nodejs.org/en).
3. VB Virtual Audio Cable. Download [here](https://vb-audio.com/Cable/).
4. (Optional but recommended) Playit.gg. Download playit.gg [here](https://playit.gg/login). Create an account.

## To start:

1. Right click the folder and select "Open in terminal."
2. Run the command `npm start`.
3. Open another terminal just ilke you did on step one.
4. Run the command `python app.py`.

### Optional: Make your website public:

1. Download playit.gg (dependencies step 3).
2. Download it and follow the instructions.
3. Create a TCP tunnel with the port 3000.

# Usage:

When you start, it will open two windows. One will be important later. Just click connect for the first one, no need to edit it.
In the start menu, type `Sound mixer options` and open it. Find your streaming service (like spotify) (it has to be open too) and set the output device to VB Cable Input.
For the music device (first one) in the radio, select it as VB Cable Output. Select your microphone in the second box.
Choose whether you want music only, mic only, or both and select `Start streaming`. Navigate to `localhost:3000` in your browser and you will see it!

## Extra:

1. If you add `/admin.html` to the link, it will open an "admin section" where you can type the "admin PIN" given after connecting to change the title of the song and notes.
2. The second window it opens when you start you will see song requests.

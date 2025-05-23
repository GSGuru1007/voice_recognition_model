import asyncio
import websockets
import json
import base64
import sounddevice as sd
from scipy.io.wavfile import write
import os

DURATION = 10
SAMPLE_RATE = 44100
USERNAME = "latha"
USER_ID = "u002"  
FILENAME = "voice_recording.wav"

async def send_audio():
    uri = "ws://192.168.11.223:8766/"      # For adding a new data path
    # uri = "ws://192.168.11.223:8765/test" # idhu test pannarathukana path


    print(f" Recording {DURATION} seconds of audio...")
    recording = sd.rec(int(DURATION * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype='int16')
    sd.wait()
    write(FILENAME, SAMPLE_RATE, recording)
    print("Recording complete.")

    
    with open(FILENAME, "rb") as audio_file:
        audio_bytes = audio_file.read()

    audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")

    
    message = {
        "user_id": USER_ID,  
        "username": USERNAME,
        "audio_data": audio_base64
    }

  
    async with websockets.connect(uri) as websocket:
        await websocket.send(json.dumps(message))
        print(f" Sent audio to server as '{USERNAME}.wav'")
        if uri == "ws://192.168.11.223:8766/test":
            msg  = await websocket.recv()
            data =  json.loads(msg)
            print(f"🗣️ Result for Given Audio  : {data['server_b_response']}")

        
 
    os.remove(FILENAME)

asyncio.run(send_audio())

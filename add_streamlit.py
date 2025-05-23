import streamlit as st
import asyncio
import websockets
import json
import base64
import pyaudio
import wave
import os
import os
os.environ['PYTHONWARNINGS'] = 'ignore'


# Audio recording settings
CHANNELS = 1
RATE = 44100
CHUNK = 1024
FORMAT = pyaudio.paInt16

async def send_audio_streamlit(username, user_id, duration):
    FILENAME = f"{username}_recording.wav"
    uri = "ws://192.168.11.232:8766"

    st.info(f"🎙️ Recording for {duration} seconds...")

    # PyAudio recording
    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, channels=CHANNELS,
                        rate=RATE, input=True, frames_per_buffer=CHUNK)
    frames = []

    for _ in range(0, int(RATE / CHUNK * duration)):
        data = stream.read(CHUNK)
        frames.append(data)

    stream.stop_stream()
    stream.close()
    audio.terminate()

    # Save to WAV
    with wave.open(FILENAME, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(audio.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))

    st.success("✅ Recording complete.")

    # Read and encode audio
    with open(FILENAME, "rb") as audio_file:
        audio_bytes = audio_file.read()
    audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")

    message = {
        "user_id": user_id,
        "username": username,
        "audio_data": audio_base64
    }

    # Send to server
    try:
        async with websockets.connect(uri) as websocket:
            await websocket.send(json.dumps(message))
            st.success(f"✅ Sent audio to server as '{username}.wav'")

            try:
                msg = await websocket.recv()
                response = json.loads(msg)
                if "error" in response:
                    st.error(response["error"])
                elif "successful" in response:
                    st.success(response["successful"])
            except Exception as inner_e:
                st.warning(f"⚠️ Couldn't read server response: {inner_e}")
    except Exception as e:
        st.error(f"❌ Failed to send audio: {e}")

    if os.path.exists(FILENAME):
        os.remove(FILENAME)

# Streamlit UI
st.title("🎤 Audio Recorder & Sender")

username = st.text_input("Enter your name")
user_id = st.text_input("Enter your User ID", "Testing_01")
duration = st.slider("Select duration (seconds)", 1, 20, 10)

if st.button("Record & Send"):
    if not username or not user_id:
        st.warning("Please fill in both name and user ID.")
    else:
        # asyncio.run(send_audio_streamlit(username, user_id, duration))
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(send_audio_streamlit(username, user_id, duration))

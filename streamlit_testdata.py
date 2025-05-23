import streamlit as st
import asyncio
import websockets
import json
import base64
import wave
import pyaudio
import os

SAMPLE_RATE = 44100
CHANNELS = 1
CHUNK = 1024
FORMAT = pyaudio.paInt16
FILENAME = "voice_recording.wav"
URI = "ws://192.168.11.232:8766/test"

def record_audio_pyaudio(duration, filename):
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=SAMPLE_RATE, input=True, frames_per_buffer=CHUNK)

    st.info(f"🎙 Recording for {duration} seconds...")
    frames = []
    for _ in range(0, int(SAMPLE_RATE / CHUNK * duration)):
        data = stream.read(CHUNK)
        frames.append(data)

    stream.stop_stream()
    stream.close()
    p.terminate()

    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(b''.join(frames))
    
    st.success("✅ Recording complete.")

async def send_audio_to_server(username, user_id, duration):
    record_audio_pyaudio(duration, FILENAME)

    with open(FILENAME, "rb") as f:
        audio_bytes = f.read()
    audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")

    message = {
        "user_id": user_id,
        "username": username,
        "audio_data": audio_base64
    }

    async with websockets.connect(URI) as websocket:
        await websocket.send(json.dumps(message))

        msg = await websocket.recv()
        data = json.loads(msg)
        if "error" in data:
            st.error(data["error"])

        return data.get("server_b_response", "No response received.")

def main():
    st.title("🎧 Voice Recognition ")

    username = st.text_input("Enter your Name")
    user_id = st.text_input("Enter your ID", "Testing_01")
    duration = st.slider("Select recording duration (seconds)", min_value=1, max_value=20, value=10, step=1)

    if username and user_id:
        if st.button("🎙 Record and Send"):
            response = asyncio.run(send_audio_to_server(username, user_id, duration))
            st.success(f"🗣️ Server Response: {response}")
    else:
        st.warning("Please enter both username and ID.")

    if os.path.exists(FILENAME):
        os.remove(FILENAME)

if __name__ == "__main__":
    main()

# voice_recognition_model
Developed a real-time voice recognition system using Python, RAG, WebSocket, and SoundDevice. Captured live audio, processed it into embeddings, and verified speaker identity through a client-server model, enabling low-latency and accurate voice-based authentication.

A real-time voice recognition system built with Python, RAG (Retrieval-Augmented Generation), WebSocket, and SoundDevice. The system captures live audio, processes it into embeddings using a speaker recognition model, and verifies speaker identity through a client-server architecture.

## Features

- Real-time voice capture and streaming
- WebSocket-based client-server communication
- Audio embedding using a speaker recognition model (e.g., ECAPA-TDNN or Titanet)
- Speaker verification using stored voice profiles
- Lightweight and fast with low-latency

## Technologies Used

- Python
- WebSocket (asyncio, websockets)
- SoundDevice (for real-time audio capture)
- SpeechBrain (for speaker embedding models)
- RAG (for prompt generation if integrated)
- NumPy, SciPy, base64

## Project Structure

import os
os.environ["TORCH_CPP_LOG_LEVEL"] = "ERROR"   
import shutil
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
import pickle
import os
import torchaudio
from speechbrain.inference.speaker import SpeakerRecognition
import asyncio
import re
import websockets
import json
import base64
from datetime import datetime
import torchaudio
import librosa
import numpy as np
import webrtcvad
import os
from pydub import AudioSegment
from scipy.io.wavfile import write



AUDIO_DIR = "audio_samples"
TEST_AUDIO_DIR = "TEST_AUDIO"
VAD_FRAME_MS = 30
TARGET_DBFS = -20.0
os.makedirs(AUDIO_DIR, exist_ok=True)

def get_audio_duration(path):
    audio = AudioSegment.from_wav(path)
    return len(audio) / 1000.0   

# === VAD Function ===
def apply_vad(audio_path):
    audio, sr = librosa.load(audio_path, sr=16000)
    vad = webrtcvad.Vad(3) 


    frame_len = int(16000 * VAD_FRAME_MS / 1000)
    samples = librosa.util.frame(audio, frame_length=frame_len, hop_length=frame_len).T

    voiced_frames = []
    for frame in samples:
        pcm = (frame * 32768).astype(np.int16).tobytes()
        if vad.is_speech(pcm, 16000):
            voiced_frames.append(frame)

    if voiced_frames:
        voiced_audio = np.concatenate(voiced_frames)
    else:
        voiced_audio = np.array([])

    out_path = "vad_output.wav"
    write(out_path, 16000, (voiced_audio * 32768).astype(np.int16))
    return out_path


def normalize_audio(path, target_dBFS=-20.0):
    sound = AudioSegment.from_wav(path)
    change_in_dBFS = target_dBFS - sound.dBFS
    normalized_sound = sound.apply_gain(change_in_dBFS)
    
    output_path = path.replace(".wav", "_normalized.wav")
    normalized_sound.export(output_path, format="wav")
    
    return output_path

def preprocess_audio(input_audio_path):
    vad_audio = apply_vad(input_audio_path)
    normalized_audio = normalize_audio(vad_audio)
    return normalized_audio  


path_queue = asyncio.Queue()

async def process_request(path, request_headers):
    
    path_str = str(request_headers)
    match = re.search(r"path='(.*?)'", path_str)
    if match:
        
        await path_queue.put(match.group(1))
        
    else:
        print("⚠️ Couldn't extract path")

async def audio_handler(websocket):
    
    actual_path = await path_queue.get()
   
    model = SpeakerRecognition.from_hparams(
        source="speechbrain/spkrec-ecapa-voxceleb",  # indha source la irruthu ECAPA-TDNN install pannurom
        savedir="pretrained_models/spkrec-ecapa-voxceleb"  
    )
    
    
    if actual_path == '/':
        async for message in websocket:
            try:
               
                data = json.loads(message)
                if not all(k in data for k in ("user_id", "username", "audio_data")):
                    print("❌ Missing fields in data")
                    continue

                user_id = data["user_id"]
                username = data["username"]
                audio_base64 = data["audio_data"]

               
                audio_data = base64.b64decode(audio_base64)

           
                today = datetime.now().strftime("%Y-%m-%d")

               
                save_dir = os.path.join(AUDIO_DIR, today, user_id)
                os.makedirs(save_dir, exist_ok=True)

                save_dir_1 = os.path.join(AUDIO_DIR, today, user_id, "Raw_data")
                os.makedirs(save_dir_1, exist_ok=True)
 
                file_path_raw_data = os.path.join(save_dir_1, f"{username}.wav")  # Raw
                file_path = os.path.join(save_dir, f"{username}.wav")             # Cleaned

   
                with open(file_path_raw_data, "wb") as f:
                    f.write(audio_data)

 
                clean_audio = preprocess_audio(file_path_raw_data)

                shutil.move(clean_audio, file_path)
                clean_audio = file_path
                duration  =get_audio_duration(clean_audio)

                if duration <= 3:
                    os.remove(file_path_raw_data)
                    os.remove(file_path)
                    os.remove("vad_output.wav")

                    error_msg = f"❌ {duration:.2f} Not Enough Duration, please talk clearly and a bit longer!"
                    print(f"⏱️ Audio duration too short: {duration:.2f} seconds")
                    
                    await websocket.send(json.dumps({
                        "error": error_msg
                    }))
                    return 

                if os.path.exists("vad_output.wav"):
                    os.remove("vad_output.wav")
                os.remove(f"{username}_recording.wav")
             


                os.makedirs("embeddings", exist_ok=True)
                waveform , sr = torchaudio.load(clean_audio)
                embedding = model.encode_batch(waveform).squeeze(0).squeeze(0)
                
                with open(f"embeddings/{username}_{today}.pkl", "wb") as f:
                    pickle.dump(embedding, f)
                
                msg =f'✅ Saved embedding for {username}'
                print(msg)
                
                print(f" Audio saved: {file_path}")
                
                await websocket.send(json.dumps({
                        "successful": msg
                    }))
                   
            except Exception as e:
                print(f" Error handling message: {e}")
    elif actual_path == "/test":
        async for messegee in websocket:
            try:
                os.makedirs(TEST_AUDIO_DIR, exist_ok=True)

                data  = json.loads(messegee)
                user_id = data["user_id"]
                username = data["username"]
                audio_base64 = data["audio_data"]
                
                audio_data = base64.b64decode(audio_base64)
                
                today = datetime.now().strftime("%Y-%m-%d")

               
                save_dir = os.path.join(TEST_AUDIO_DIR, today, user_id)
                os.makedirs(save_dir, exist_ok=True)

                save_dir_1 = os.path.join(TEST_AUDIO_DIR, today, user_id, "Raw_data")
                os.makedirs(save_dir_1, exist_ok=True)
 
                file_path_raw_data = os.path.join(save_dir_1, f"{username}.wav")  # Raw
                file_path_ = os.path.join(save_dir, f"{username}.wav")             # Cleaned

   
                with open(file_path_raw_data, "wb") as f:
                    f.write(audio_data)

 
                clean_audio = preprocess_audio(file_path_raw_data)

                shutil.move(clean_audio, file_path_)
                
                clean_audio = file_path_
                
                duration  =get_audio_duration(clean_audio)

                if duration <= 3:
                    os.remove(file_path_raw_data)
                    os.remove(file_path_)
                    os.remove("vad_output.wav")

                    error_msg = f"❌ {duration:.2f} Not Enough Duration, please talk clearly and a bit longer!"
                    print(f"⏱️ Audio duration too short: {duration:.2f} seconds")
                    
                    await websocket.send(json.dumps({
                        "error": error_msg
                    }))
                    return 

               
                if os.path.exists("vad_output.wav"):
                    os.remove("vad_output.wav")
            
                try:
                    testing_server_url = 'ws://192.168.11.232:9996'
                    async with websockets.connect(testing_server_url) as se2:
                        await se2.send(json.dumps({
                            "audio_data": audio_base64,
                            "file_path_" :file_path_
                        }))

                        server_2_received = await se2.recv()
                        if isinstance(server_2_received, bytes):
                            server_2_received_str = server_2_received.decode("utf-8")
                        else:
                            server_2_received_str = server_2_received

                        await websocket.send(json.dumps({
                            "status": "success",
                            "server_b_response": server_2_received_str
                        }))
                    # os.remove(file_path_)
                except Exception as e:
                    print(f"Error in sending to test server {e}")
            except Exception as e :
                print(f"2nd Server ku sent pannarathula error {e}")

async def main():
    
    async with websockets.serve(audio_handler, "192.168.11.232", 8766, max_size=10 * 1024 * 1024, process_request=process_request):
        print("🔊 WebSocket server started on ws://192.168.11.223:8765")
        await asyncio.Future() 
        


if __name__ == "__main__":
    asyncio.run(main())

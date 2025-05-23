import asyncio
import websockets
import os
import json
import os
os.environ["TORCH_CPP_LOG_LEVEL"] = "ERROR"   
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
import pickle
import os
import torch
import torchaudio
from speechbrain.inference.speaker import SpeakerRecognition



model = SpeakerRecognition.from_hparams(
    source="speechbrain/spkrec-ecapa-voxceleb",  # indha source la irruthu ECAPA-TDNN install pannurom
    savedir="pretrained_models/spkrec-ecapa-voxceleb"  
)


def getting_embedding(test_file):
    wave_form , sr = torchaudio.load(test_file)
    embedding= model.encode_batch(wave_form).squeeze(0).squeeze(0)

    return embedding




async def identify_speaker(websocket):
    async for mesg in websocket:
        try:

            data = json.loads(mesg)

            text_file = data['file_path_'].strip()
            print(text_file)

            try:
                test_embedding =  getting_embedding(text_file)
            except Exception as e:
                print("nonon" , e)
                await websocket.send("Error")
                continue
            max_score = -1
            best_match = "Unknown"

        

            for file in os.listdir("embeddings"):
                name = file.replace(".pkl", "").split("_")[0]
                with open(f"embeddings/{file}", "rb") as f:
                    saved_embedding = pickle.load(f)
               
                score = torch.nn.functional.cosine_similarity(test_embedding, saved_embedding, dim=0).item()
                print(f"🗣️ {name} → Score: {score:.4f}")

                if score > max_score:
                    max_score = score
                    best_match = name
            if max_score >= 0.60:
                print(f"\n🔍 Best Match: {best_match} (Score: {max_score:.4f})")
                await websocket.send(bytes(f'{best_match}', encoding='utf-8'))
                print('\n')
            else:
                print(f"\n🔍 Unknown (Score: {max_score:.4f})")
                await websocket.send(bytes(f'Unknown', encoding='utf-8'))
                print('\n')
            print("\nFinish...\n")
        except Exception as e:
            print(e)
            await websocket.send("Error")

async def main():
    async with websockets.serve(identify_speaker,"192.168.11.232" ,9996, max_size=10 * 1024 * 1024):
        print("🔌 WebSocket server started...")
        await asyncio.Future()

asyncio.run(main())



"""Quick diagnostic: test if PyAnnote diarization pipeline can load and run"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(r"e:\Projects\whisperMe", "backend"))

try:
    from app.config import HF_TOKEN
    print(f"HF_TOKEN loaded: '{HF_TOKEN[:10]}...' (len={len(HF_TOKEN)})")
    print(f"HF_TOKEN valid check (len >= 30): {len(HF_TOKEN) >= 30}")
except Exception as e:
    print(f"Failed to load HF_TOKEN: {e}")
    sys.exit(1)

print("\n--- Testing PyAnnote Pipeline Load ---")
try:
    import torch
    print(f"PyTorch version: {torch.__version__}")
    print(f"CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        free_mem, total_mem = torch.cuda.mem_get_info()
        print(f"GPU memory: {free_mem/(1024**3):.2f} GB free / {total_mem/(1024**3):.2f} GB total")
except Exception as e:
    print(f"PyTorch check failed: {e}")

try:
    from pyannote.audio import Pipeline
    print("\nAttempting to load pyannote/speaker-diarization-3.1...")
    pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization-3.1",
        use_auth_token=HF_TOKEN
    )
    print("SUCCESS: Pipeline loaded!")
    print(f"Pipeline type: {type(pipeline)}")
except Exception as e:
    print(f"\nFAILED to load pipeline: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()

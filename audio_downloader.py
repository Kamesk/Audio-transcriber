from datasets import load_dataset
import soundfile as sf
import os

HF_TOKEN = os.getenv("hf_token")

dataset = load_dataset(
    "openslr/librispeech_asr",
    "clean",
    split="test",
    streaming=True,
    token=HF_TOKEN
)

duration = 0
audio_parts = []

for sample in dataset:
    audio = sample["audio"].get_all_samples()

    audio_array = audio.data.squeeze(0).numpy()
    sample_rate = audio.sample_rate

    audio_parts.append(audio_array)

    duration += len(audio_array) / sample_rate

    print(f"Collected: {duration:.2f}s")

    if duration >= 300:
        break

combined_audio = audio_parts[0]

for part in audio_parts[1:]:
    combined_audio = __import__("numpy").concatenate(
        [combined_audio, part]
    )

combined_audio = combined_audio[
    :int(300 * sample_rate)
]

sf.write(
    "test_audio_5min.wav",
    combined_audio,
    sample_rate
)

print("Saved: test_audio_5min.wav")
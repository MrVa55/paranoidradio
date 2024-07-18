import sounddevice as sd

print("All audio devices:")
print(sd.query_devices())

print("\nInput audio devices:")
for idx, device in enumerate(sd.query_devices()):
    if device['max_input_channels'] > 0:
        print(f"Device ID: {idx}, Device Name: {device['name']}")

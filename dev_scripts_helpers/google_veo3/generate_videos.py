#!/usr/bin/env python3

import os
import time
from google import genai
from google.genai import types

client = genai.Client(api_key=os.environ["GOOGLE_GENAI_API_KEY"])

# 2a) Does *anything* work?
client.models.generate_content(model="gemini-1.5-flash", contents="ping")  # should succeed

# 2b) Do you have Veo access?
m = client.models.get(model="veo-3.0-generate-001")  # should NOT 403
print(m.name, getattr(m, "state", None))

operation = client.models.generate_videos(
    model="veo-3.0-generate-001",
    prompt="A close up of two people staring at a cryptic drawing on a wall, torchlight flickering. A man murmurs, 'This must be it. That's the secret code.' The woman looks at him and whispering excitedly, 'What did you find?'",
    config=types.GenerateVideosConfig(
        durationSeconds=8,
        resolution="1080p",
        #generateAudio=True,
        negativePrompt="loud music, modern buildings",
        #seed=42,
        #sampleCount=1,
        aspectRatio="16:9"
    )
)

# Poll until done
while not operation.done:
    print("Waiting for video generation to complete...")
    time.sleep(10)
    operation = client.operations.get(operation)

generated_video = operation.response.generated_videos[0]
client.files.download(file=generated_video.video)
generated_video.video.save("output.mp4")
print("Video saved as output.mp4")

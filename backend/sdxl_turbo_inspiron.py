# sdxl_turbo_inspiron.py
from optimum import pipelines
from PIL import Image

print("🚀 Loading SDXL-Turbo (OpenVINO, Intel iGPU)...")
pipe = pipelines.(
    "stabilityai/sdxl-turbo",
    export=True,
    compile=True,
    device="GPU",
    ov_config={"CACHE_DIR": "./ov_cache"}
)

prompt = input("Enter prompt: ") or "a friendly robot watering plants in a sunlit garden"

print(f"🎨 Generating: '{prompt}' (4 steps)...")
image = pipe(prompt, num_inference_steps=4, guidance_scale=0.0).images[0]

image.save("sdxl_output.png")
image.show()
print("✅ Done! Saved as 'sdxl_output.png'")
from vlmeval.config import supported_VLM
model = supported_VLM['v-mllm_7b']()
# Forward VIM-processed Image with Text Prompt
ret = model.generate(['inference_images/input_1.jpg', 'What is in this image?'])
print(ret)  # The image features a red apple with a leaf on it.
# Forward VIM-processed Image with no Text Prompt
ret = model.generate(['inference_images/input_1.jpg', ' '])
print(ret)  # There are two apples in the provided images.
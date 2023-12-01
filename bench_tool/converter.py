import os
import json
import argparse
from PIL import Image, ImageDraw, ImageFont
import textwrap
import pathlib
def get_args():
    parser = argparse.ArgumentParser()

    parser.add_argument('--context-num', default=0, type=int)
    parser.add_argument('--input-file', default=None, type=str)
    parser.add_argument('--input-image-path', default=None, type=str)
    parser.add_argument('--output-image-path', default=None, type=str)
    parser.add_argument('--raw-image-path', default=None, type=str)
    parser.add_argument('--bench-name', default=None, type=str)

    args = parser.parse_args()
    return args

def draw_wrapped_text(image, text, position, max_width, font_path=None, font_size=20, color=(0, 0, 0)):
    """Draw wrapped text on an image."""
    draw = ImageDraw.Draw(image)

    if font_path:
        font = ImageFont.truetype(font_path, font_size)
    else:
        font = ImageFont.load_default()

    lines = []
    words = text.split()
    while words:
        line = ''
        while words and font.getsize(line + words[0])[0] <= max_width:
            line += (words.pop(0) + ' ')
        lines.append(line)

    x_text = position[0]
    y_text = position[1]
    for line in lines:
        width, height = draw.textsize(line, font=font)
        draw.text((x_text, y_text), line, font=font, fill=color)
        y_text += height


def add_text_to_image(args, image_path, text, save_image_path, uid=""):
    # Open the image
    if args.bench_name == "mme":
        unique_name = image_path.replace("_QNo", "")
        img = Image.open(unique_name)
        img_to_save = image_path.replace(args.input_image_path, args.raw_image_path)
        os.makedirs(os.path.dirname(img_to_save), exist_ok=True)
        img.save(img_to_save)
        raw_save_path = unique_name.replace(args.input_image_path, args.raw_image_path)
    elif args.bench_name == "vqav2":
        img = Image.open(image_path)
        raw_save_path = image_path.replace("vqav2/val2014", "vqav2/VISBENCH_vqav2_80_raw")
    elif args.bench_name == "vqav2-testdev":
        img = Image.open(image_path)
        raw_save_path = image_path.replace("vqav2/test2015", "vqav2/VISBENCH_vqav2_107394_raw")
    elif args.bench_name == "mm-vet":
        img = Image.open(image_path)
        image_path = os.path.join(os.path.dirname(image_path), uid)
        save_image_path = os.path.join(os.path.dirname(save_image_path), uid)
        raw_save_path = image_path.replace("images", "VISBENCH_mm-vet_raw")
    elif args.bench_name == "refcoco":
        img = Image.open(image_path)
        save_image_path = image_path.replace(args.input_image_path, args.output_image_path)
        raw_save_path = save_image_path.replace(args.output_image_path, "/home/ubuntu/project/eval/refcoco/VISBENCH_refcoco_raw")
        print(raw_save_path)

    if not os.path.exists(os.path.dirname(raw_save_path)):
        os.makedirs(os.path.dirname(raw_save_path))
    img.save(raw_save_path)
    width, height = img.size

    text_x = 10 
    text_y = height + 10
    print(int(len(text.split())))
    lines = []
    words = text.split()
    while words:
        line = ''
        font = ImageFont.truetype("/home/ubuntu/PROBE/assets/Arial.ttf", int(width/20))
        while words and font.getsize(line + words[0])[0] <= (width-int(width/20)):
            line += (words.pop(0) + ' ')
        lines.append(line)
    new_height = height + len(lines) * (int(width/20)+12)

    new_image = Image.new("RGB", (width, new_height), "white")
    new_image.paste(img, (0, 0))
    draw_wrapped_text(new_image, text, (text_x, text_y), max_width=width-int(width/20), font_path="/home/ubuntu/PROBE/assets/Arial.ttf", font_size=int(width/20))
    os.makedirs(os.path.dirname(save_image_path), exist_ok=True)
    new_image.save(save_image_path)

    print(f"Saved new image to {save_image_path}")


def build_bench(args):
    with open(args.input_file, 'r') as file:
        for line in file:
            try:
                json_object = json.loads(line.strip())
                
                print(json_object)

                question_id, image, text, category = json_object["question_id"], json_object["image"], json_object["text"], json_object["category"]
                _, image_extension = os.path.splitext(image)

                if args.bench_name == "mm-vet":
                    text = "Question: " + text + " Answer the question using a single word or phrase."
                else:
                    text = "Question: " + text
                if not os.path.exists(os.path.join(args.output_image_path, os.path.dirname(image))):
                    os.makedirs(os.path.join(args.output_image_path, os.path.dirname(image)))
                if args.bench_name == "mm-vet":
                    ori_image_path = os.path.join(args.input_image_path, image)
                    add_text_to_image(args, ori_image_path, text, os.path.join(args.output_image_path, image), uid=f"{question_id}{image_extension}")
                elif args.bench_name == "refcoco":
                    ori_image_path = os.path.join(args.input_image_path, image)
                    add_text_to_image(args, ori_image_path, text, image.replace(args.input_image_path, args.output_image_path))
                elif args.bench_name == "vqav2-testdev":
                    ori_image_path = os.path.join(args.input_image_path, image)
                    filename, file_extension = os.path.splitext(image)
                    add_text_to_image(args, ori_image_path, text, os.path.join(args.output_image_path, str(filename)+"[&]"+str(question_id)+str(file_extension)))
                else:
                    ori_image_path = os.path.join(args.input_image_path, image)
                    add_text_to_image(args, ori_image_path, text, os.path.join(args.output_image_path, image))
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON on line: {line.strip()}")

if __name__ == "__main__":

    args = get_args()
    build_bench(args)
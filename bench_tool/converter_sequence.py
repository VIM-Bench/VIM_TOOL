import os
import json
import argparse
from PIL import Image, ImageDraw, ImageFont
import textwrap
from icecream import ic

def get_args():
    parser = argparse.ArgumentParser()

    parser.add_argument('--context-num', default=0, type=int)
    parser.add_argument('--input-file', default=None, type=str)
    parser.add_argument('--input-image-path', default=None, type=str)
    parser.add_argument('--output-image-path', default=None, type=str)
    parser.add_argument('--raw-image-path', default=None, type=str)
    parser.add_argument('--bench-name', default=None, type=str)
    parser.add_argument('--sequence-num', default=2, type=int)
    parser.add_argument('--add-context', default="", type=str)
    parser.add_argument('--orientation', default="horizontal", type=str)
    

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


def concatenate_horizontally(image_list, separator_width=10):
    if not image_list:
        return None
    
    total_width = sum(img.width for img in image_list) + separator_width * (len(image_list) - 1)
    max_height = max(img.height for img in image_list)

    result_img = Image.new('RGB', (total_width, max_height), color='white')
    draw = ImageDraw.Draw(result_img)

    x_offset = 0
    
    for i, img in enumerate(image_list):
        y_offset = (max_height - img.height) // 2
        
        result_img.paste(img, (x_offset, y_offset))
        x_offset += img.width

        if i < len(image_list) - 1:
            draw.line([(x_offset, 0), (x_offset, max_height)], fill='gray', width=separator_width)
            x_offset += separator_width

    return result_img

def concatenate_vertically(image_list, separator_width=10):
    if not image_list:
        return None
    
    total_height = sum(img.height for img in image_list) + separator_width * (len(image_list) - 1)
    max_width = max(img.width for img in image_list)

    result_img = Image.new('RGB', (max_width, total_height), color='white')
    draw = ImageDraw.Draw(result_img)

    y_offset = 0
    
    for i, img in enumerate(image_list):
        x_offset = (max_width - img.width) // 2
        
        result_img.paste(img, (x_offset, y_offset))
        y_offset += img.height

        if i < len(image_list) - 1:
            draw.line([(0, y_offset), (max_width, y_offset)], fill='gray', width=separator_width)
            y_offset += separator_width

    return result_img

def add_text_to_image_as_sequence(args, unique_id, question_id_list, image_list, text_list, image_full_name):
    img_base_name = os.path.basename(image_full_name)
    img_list, new_img_list = [], []
    for question_id, image, text in zip(question_id_list, image_list, text_list):
        if args.bench_name in "mm-vet":
            ori_image_path = os.path.join(args.input_image_path, image)
            _, image_extension = os.path.splitext(image)
            img, new_image = add_text_to_image(args, ori_image_path, text, os.path.join(args.output_image_path, image), uid=f"{question_id}.{image_extension}", save_intermediate=False)
        else:
            ori_image_path = os.path.join(args.input_image_path, image)
            img, new_image = add_text_to_image(args, ori_image_path, text, os.path.join(args.output_image_path, image), save_intermediate=False)
        img_list.append(img)
        new_img_list.append(new_image)
    os.makedirs(args.input_image_path, exist_ok=True)
    os.makedirs(args.raw_image_path, exist_ok=True)
    if args.bench_name == "mm-vet":
        if len(args.add_context):
            save_file_name = f"{unique_id}.jpg"
        else:
            save_file_name = f"{unique_id*2}[&]{(unique_id+1)*2-1}.jpg"
    elif args.bench_name == "mme":
        save_file_name = image_full_name
    elif args.bench_name == "vqav2":
        if len(args.add_context):
            save_file_name = image_full_name
        else:
            save_file_name = f"{os.path.basename(image_list[0])}[&]{os.path.basename(image_list[1])}"
    elif args.bench_name == "vqav2-testdev":
        if len(args.add_context):
            save_file_name = f"{os.path.basename(image_full_name)}[&]{str(question_id_list[1])}.jpg"
        else:
            save_file_name = f"{os.path.basename(image_list[0])}[&]{os.path.basename(image_list[1])}[&]{str(question_id_list[0])}[&]{str(question_id_list[1])}.jpg"
    elif args.bench_name == "refcoco":
        if len(args.add_context):
            save_file_name = img_base_name
        else:
            save_file_name = f"{os.path.basename(image_list[0])}[&]{os.path.basename(image_list[1])}"
    save_concatenate_path = os.path.join(args.output_image_path, save_file_name)
    os.makedirs(os.path.dirname(save_concatenate_path), exist_ok=True)
    if args.orientation == "horizontal":
        concatenate_horizontally(img_list).save(os.path.join(args.raw_image_path, save_file_name))
        concatenate_horizontally(new_img_list).save(save_concatenate_path)
    elif args.orientation == "vertical":
        concatenate_vertically(img_list).save(os.path.join(args.raw_image_path, save_file_name))
        concatenate_vertically(new_img_list).save(save_concatenate_path)

                
def add_text_to_image(args, image_path, text, save_image_path, save_intermediate=False, uid=""):
    
    if args.bench_name == "mme":
        unique_name = image_path.replace("_QNo", "")
        img = Image.open(unique_name)
        img_save_path = image_path.replace(args.input_image_path, args.raw_image_path)
        if not os.path.exists(img_save_path):
            os.makedirs(os.path.dirname(img_save_path), exist_ok=True)
        img.save(img_save_path)
        raw_save_path = unique_name.replace(args.input_image_path, args.raw_image_path)
    elif args.bench_name == "vqav2":
        img = Image.open(image_path)
        raw_save_path = image_path.replace("vqav2/val2014", "vqav2/VISBENCH_vqav2_80_raw")
    elif args.bench_name == "vqav2-testdev":
        if not "COCO_test2015" in image_path:
            image_path = image_path.replace("test2015", "val2014")
            raw_save_path = image_path.replace("vqav2/val2014", "vqav2/VISBENCH_vqav2_107394_raw")
        else:
            raw_save_path = image_path.replace("vqav2/test2015", "vqav2/VISBENCH_vqav2_107394_raw")
        img = Image.open(image_path)
        
    elif args.bench_name == "mm-vet":
        img = Image.open(image_path)
        image_path = os.path.join(os.path.dirname(image_path), uid)
        save_image_path = os.path.join(os.path.dirname(save_image_path), uid)
        raw_save_path = image_path.replace("images", "VISBENCH_mm-vet_raw")
    elif args.bench_name == "refcoco":
        img = Image.open(image_path)
        save_image_path = image_path.replace(args.input_image_path, args.output_image_path)
        raw_save_path = save_image_path.replace(args.output_image_path, "/home/ubuntu/eval/refcoco/VISBENCH_refcoco_raw")
        print(raw_save_path)

    if not os.path.exists(os.path.dirname(raw_save_path)):
        os.makedirs(os.path.dirname(raw_save_path))
    if save_intermediate:
        img.save(raw_save_path)
    width, height = img.size


    # text right to image
    # text_x = width + 10  # 20 pixels from the left edge of the original image
    # text_y = 10  # Vertically centered
    # new_width = width * 2
    # new_image = Image.new("RGB", (new_width, height), "white")
    # new_image.paste(img, (0, 0))
    # text under image
    text_x = 10  # 20 pixels from the left edge of the original image
    text_y = height + 10  # Vertically centered
    
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
    if save_intermediate:
        new_image.save(save_image_path)

    if not save_intermediate:
        return img, new_image

def build_bench(args):
    if len(args.add_context):
        if args.bench_name == "mm-vet":
            with open(args.add_context, "r") as file:
                answer_data_dict = json.load(file)
        elif args.bench_name == "refcoco":
            with open(args.add_context, "r") as file:
                answer_data_list = [json.loads(line.strip()) for line in file]
    with open(args.input_file, 'r') as file:
        lines = []
        unique_id = -1
        count = -1
        for line in file:
            count += 1
            lines.append(line.strip())

            if len(lines) == args.sequence_num:
                unique_id += 1
                question_id_list = []
                image_list = []
                text_list = []
                for lineidx, line in enumerate(lines):
                    try:
                        json_object = json.loads(line.strip())
                        
                        print(json_object)

                        question_id, image, text, category = json_object["question_id"], json_object["image"], json_object["text"], json_object["category"]
                        
                        if len(args.add_context):
                            if args.bench_name == "mm-vet":
                                text = "Question: " + text + "\n\nAnswer: " + (answer_data_dict[f"v1_{question_id}"]["answer"] if (lineidx < (args.sequence_num - 1)) else "")
                            elif args.bench_name == "mme":
                                cur_answer = "No" if "_QNo" in question_id else "Yes"
                                text = "Question: " + text + "\n\nAnswer: " + (cur_answer if (lineidx < (args.sequence_num - 1)) else "")
                            elif args.bench_name in ["vqav2", "vqav2-testdev"]:
                                text = "Question: " + text + "\n\nAnswer: " + (json_object["reference_output"] if (lineidx < (args.sequence_num - 1)) else "")   
                            elif args.bench_name == "refcoco":
                                text = "Question: " + text + "\n\nAnswer: " + (answer_data_list[unique_id]["reference_output"] if (lineidx < (args.sequence_num - 1)) else "")                                
                        else:
                            if args.bench_name == "mm-vet":
                                text = "Question: " + text + " Answer the question using a single word or phrase."
                            elif args.bench_name == "refcoco":
                                text = "Question: " + text + " The coordinate should be normalized to the above given image."
                            else:
                                text = "Question: " + text
                        question_id_list.append(question_id)
                        image_list.append(image)
                        text_list.append(text)
                        
                    except json.JSONDecodeError as e:
                        print(f"Error parsing JSON on line: {line.strip()}")
                if not os.path.exists(os.path.join(args.output_image_path, os.path.dirname(image))):
                    os.makedirs(os.path.join(args.output_image_path, os.path.dirname(image)))
                add_text_to_image_as_sequence(args, unique_id, question_id_list, image_list, text_list, image)
                lines = []


if __name__ == "__main__":

    args = get_args()
    build_bench(args)
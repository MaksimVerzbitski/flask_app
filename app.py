import os
from flask import Flask, render_template, request, redirect, url_for
from PIL import Image
import shutil
import csv

app = Flask(__name__)

image_folder = "static/images_to_rotate/"
hard_to_read_folder = "static/hard_to_read/"

current_index = 0
image_text_directory = {}

image_files = sorted([f for f in os.listdir(image_folder) if f.endswith('.png')])





for image_name in image_files:
    associated_text = os.path.splitext(image_name)[0].split('_')[0]
    image_text_directory[image_name] = associated_text


train_file = "train_full_text.txt"

if not os.path.exists(train_file):
    open(train_file, "w").close()

if not os.path.exists(hard_to_read_folder):
    os.makedirs(hard_to_read_folder)

if os.path.exists("last_index.txt"):
    with open("last_index.txt", "r") as file:
        current_index = int(file.read())

with open("online_sep27.csv", "r") as file:
    reader = csv.reader(file, delimiter=";")
    next(reader)  # skip the header row
    for row in reader:
        image_name = row[10]
        associated_text = row[2]
        image_text_directory[image_name] = associated_text

def save_current_index():
    with open('last_index.txt', 'w') as f:
        f.write(str(current_index))


@app.route("/", methods=['GET', 'POST'])
def home():
    global current_index

    print(f"Current Index: {current_index}, Length of Image Files: {len(image_files)}")  # Add this line for debugging
    
    if current_index < 0 or current_index >= len(image_files):
        return "Index out of range", 400
    
    # Check if current_index is within the bounds of the image_files list
    if current_index < 0 or current_index >= len(image_files):
        # Handle the error: you can return an error message or redirect to another page
        return "Index out of range", 400
    
    image_file = image_files[current_index]

    if request.method == 'POST':
        associated_text = request.form['image_text']
        with open(train_file, "a") as file:
            file.write(f"{image_file}\t{associated_text}\n")

        current_index += 1
        # ensure that current_index does not go beyond the length of image_files
        current_index = min(current_index, len(image_files) - 1)
        save_current_index()
        return redirect(request.url)

    # Check the train.txt file for updated text
    associated_text = None
    with open(train_file, "r") as file:
        lines = file.readlines()
        for line in lines:
            if line.startswith(image_file):
                _, associated_text = line.rstrip('\n').split("\t")
                break

    # If no updated text was found in train.txt, extract from image name
    if associated_text is None:
        associated_text = image_file.split('_')[0]

    return render_template(
        "images.html",
        image_file=image_file,
        associated_text=associated_text,
        image_name=image_file[:-4],  # remove file extension
        current_index=current_index + 1,
        total_images=len(image_files)
    )
@app.route("/back", methods=["GET", "POST"])
def back():
    global current_index
    current_index = 0  # Change index to 0 when back is pressed
    save_current_index()
    check_image_existence()
    return redirect(url_for("home"))


@app.route("/next_image", methods=["POST"])
def next_image():
    global current_index
    current_index += 1
    save_current_index()
    check_image_existence()
    return redirect(url_for("home"))


@app.route("/previous_image", methods=["POST"])
def previous_image():
    global current_index
    global image_files

    # Synchronize current_index with the actual index of the current image
    if "image_name" in request.form:
        image_name = request.form["image_name"] + ".png"
        if image_name in image_files:
            current_index = image_files.index(image_name)

    if current_index > 0:
        current_index -= 1
    else:
        current_index = len(image_files) - 1

    save_current_index()
    check_image_existence()
    return redirect(url_for("home"))


@app.route("/debug", methods=["POST"])
def debug():
    print(request.form)
    return ""


@app.route("/save", methods=["POST"])
def save():
    global current_index
    global image_files
    text = request.form["text"]
    image_file = image_files[current_index]
    with open("train_full_text.txt", "r+") as file:
        lines = file.readlines()
        file.seek(0)
        for line in lines:
            if not line.startswith(image_file + "\t"):
                file.write(line)
        file.write(f"{image_file}\t{text}\n")
        file.truncate()
    current_index += 1
    check_image_existence()
    save_current_index()
    return redirect(url_for("home"))


@app.route("/next_and_save", methods=["POST"])
def next_and_save():
    global current_index
    global image_files
    text = request.form["text"]
    image_file = image_files[current_index]

    # Read the existing lines
    with open("train_full_text.txt", "r") as file:
        lines = file.readlines()

    # Ensure the lines list is long enough
    while len(lines) <= current_index:
        lines.append("\n")

    # Update the line at the current index
    lines[current_index] = f"{image_file}\t{text}\n"

    # Write the updated lines
    with open("train_full_text.txt", "w") as file:
        file.writelines(lines)

    # Move to next image
    current_index += 1
    save_current_index()
    check_image_existence()
    return redirect(url_for("home"))

@app.route("/blurry", methods=["POST"])
def blurry():
    print("Blurry method called")
    global current_index
    global image_files

    if "image_name" not in request.form:
        print("No image name in form data")
        return redirect(url_for("home"))

    image_name = request.form["image_name"]
    image_name_ext = image_name + ".png"  # Add the extension to the image name

    # Check if the image file exists in the image_files list
    if image_name_ext in image_files:
        # Increment the current index before removing the image from image_files
        if current_index == len(image_files) - 1:
            current_index = 0
        else:
            current_index += 1

        image_files.remove(
            image_name_ext
        )  # Remove the image file from the image_files list

        image_path = os.path.join(image_folder, image_name_ext)
        hard_to_read_path = os.path.join(hard_to_read_folder, image_name_ext)

        shutil.move(
            image_path, hard_to_read_path
        )  # Moves the image file to the hard_to_read folder and deletes it from the original folder

        # Get the associated text
        associated_text = image_text_directory.get(image_name, "")

        # Save to train.txt
        with open("train_full_text.txt", "r+") as file:
            lines = file.readlines()
            file.seek(0)
            for line in lines:
                if not line.startswith(image_name_ext + "\t"):
                    file.write(line)
            file.write(f"{image_name_ext}\t{associated_text}\n")
            file.truncate()

        # Remove linked text from image_text_directory
        if image_name in image_text_directory:
            del image_text_directory[image_name]

    else:
        print(f"Image name not found in image files: {image_name}")
    save_current_index()
    check_image_existence()
    return redirect(url_for("home"))


@app.route("/rotate_left", methods=["POST"])
def rotate_left():
    global current_index
    global image_files

    if "image_name" not in request.form:
        return redirect(url_for("home"))

    image_name = request.form["image_name"]
    image_name_ext = image_name + ".png"
    image_path = os.path.join(image_folder, image_name_ext)

    if os.path.exists(image_path):
        image = Image.open(image_path)
        rotated_image = image.rotate(90, expand=True)
        rotated_image.save(image_path)
    else:
        print(f"Image not found: {image_name}")

    return redirect(url_for("home"))


@app.route("/rotate_right", methods=["POST"])
def rotate_right():
    global current_index
    global image_files

    if "image_name" not in request.form:
        return redirect(url_for("home"))

    image_name = request.form["image_name"]
    image_name_ext = image_name + ".png"
    image_path = os.path.join(image_folder, image_name_ext)

    if os.path.exists(image_path):
        image = Image.open(image_path)
        rotated_image = image.rotate(-90, expand=True)
        rotated_image.save(image_path)
    else:
        print(f"Image not found: {image_name}")

    return redirect(url_for("home"))


@app.route("/delete_image", methods=["POST"])
def delete_image():
    global current_index
    global image_files

    if "image_name" not in request.form:
        print("No image name in form data")
        
        return redirect(url_for("home"))

    image_name = request.form["image_name"]
    image_name_ext = image_name + ".png"  # Add the extension to the image name

    # Check if the image file exists in the image_files list
    if image_name_ext in image_files:
        # Increment the current index before removing the image from image_files
        if current_index == len(image_files) - 1:
            current_index = 0
        else:
            current_index += 1

        image_files.remove(
            image_name_ext
        )  # Remove the image file from the image_files list

        # Check if the image file exists in the file system and delete it
        image_path = os.path.join(image_folder, image_name_ext)
        if os.path.exists(image_path):
            os.remove(image_path)
    else:
        print(f"Image name not found in image files: {image_name}")
    save_current_index()
    check_image_existence()
    return redirect(url_for("home"))


def check_image_existence():
    global current_index
    if len(image_files) == 0:
        current_index = 0
    else:
        current_index = current_index % len(image_files)

if os.path.exists('last_index.txt'):
    with open('last_index.txt', 'r') as f:
        current_index = int(f.read().strip())
else:
    current_index = 0


if __name__ == "__main__":
    if os.path.exists('last_index.txt'):
        with open('last_index.txt', 'r') as f:
            current_index = int(f.read().strip())
    try:
        app.run(host="0.0.0.0", port=5000)
    except KeyboardInterrupt:  # On manual interruption, save the current index to file
        with open("last_index.txt", "w") as f:
            f.write(str(current_index))

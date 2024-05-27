import requests
import gzip
import xmltodict
import json
import os
from PIL import Image, ImageTk, UnidentifiedImageError
from io import BytesIO
import tkinter as tk
from tkinter import simpledialog, messagebox

APPROVED_NATIONS_FILE = "approved_nations.json"
UNAPPROVED_NATIONS_FILE = "unapproved_nations.json"
IMAGE_FOLDER = "images"

if not os.path.exists(IMAGE_FOLDER):
    os.makedirs(IMAGE_FOLDER)


def load_approved_nations():
    if os.path.exists(APPROVED_NATIONS_FILE):
        with open(APPROVED_NATIONS_FILE, "r") as f:
            return json.load(f)
    else:
        return {}


def save_approved_nations(approved_nations):
    with open(APPROVED_NATIONS_FILE, "w") as f:
        json.dump(approved_nations, f, indent=4)


def load_unapproved_nations():
    if os.path.exists(UNAPPROVED_NATIONS_FILE):
        with open(UNAPPROVED_NATIONS_FILE, "r") as f:
            return json.load(f)
    else:
        return {}


def save_unapproved_nations(unapproved_nations):
    with open(UNAPPROVED_NATIONS_FILE, "w") as f:
        json.dump(unapproved_nations, f, indent=4)


def download_nations_xml(xml_user_agent):
    url = "https://www.nationstates.net/pages/nations.xml.gz"
    headers = {"User-Agent": xml_user_agent}
    response = requests.get(url, headers=headers)
    print(f"Downloading XML: {response.status_code}")
    return gzip.decompress(response.content)


def parse_nations_xml(xml_content):
    data = xmltodict.parse(xml_content)
    print("Parsed XML data.")
    return data["NATIONS"]["NATION"]


def find_nations_in_region(nations, region):
    region_normalized = region.lower().replace(" ", "_")
    return [
        nation
        for nation in nations
        if nation["REGION"].lower().replace(" ", "_") == region_normalized
    ]


def compare_nations(old_nation, new_nation):
    return old_nation == new_nation


def sanitize_filename(name):
    return "".join(c for c in name if c.isalnum() or c in (" ", "_")).rstrip()


def download_and_display_flag(nation, image_label, flag_user_agent):
    flag_url = nation["FLAG"]
    sanitized_name = sanitize_filename(nation["NAME"])
    flag_path = os.path.join(IMAGE_FOLDER, f"{sanitized_name}.png")

    # Download and save the flag image
    try:
        headers = {"User-Agent": flag_user_agent}
        response = requests.get(flag_url, headers=headers)
        response.raise_for_status()
        img = Image.open(BytesIO(response.content))
        img = img.resize((200, 100), Image.ANTIALIAS)
        img.save(flag_path)
    except (requests.RequestException, UnidentifiedImageError) as e:
        print(f"Failed to load and save flag image: {e}")
        return

    # Display the flag image
    try:
        img = Image.open(flag_path)
        img = ImageTk.PhotoImage(img)
        image_label.config(image=img)
        image_label.image = img
    except Exception as e:
        print(f"Failed to display flag image: {e}")


def delete_flag_image(nation):
    sanitized_name = sanitize_filename(nation["NAME"])
    flag_path = os.path.join(IMAGE_FOLDER, f"{sanitized_name}.png")
    if os.path.exists(flag_path):
        os.remove(flag_path)
        print(f"Deleted flag image: {flag_path}")


def display_nation(nation, text_widget1, text_widget2, image_label, flag_user_agent):
    text_lines = [
        f"FULLNAME: {nation['FULLNAME']}",
        f"TYPE: {nation['TYPE']}",
        f"MOTTO: {nation['MOTTO']}",
        f"UN STATUS: {nation['UNSTATUS']}",
        f"REGION: {nation['REGION']}",
        f"ANIMAL: {nation['ANIMAL']}",
        f"CURRENCY: {nation['CURRENCY']}",
        f"DEMONYM: {nation['DEMONYM']}",
        f"DEMONYM2: {nation['DEMONYM2']}",
        f"DEMONYM2 PLURAL: {nation['DEMONYM2PLURAL']}",
        f"INFLUENCE: {nation['INFLUENCE']}",
        f"LEADER: {nation['LEADER']}",
        f"CAPITAL: {nation['CAPITAL']}",
        f"RELIGION: {nation['RELIGION']}",
        f"FACTBOOKS: {nation['FACTBOOKS']}",
        f"DISPATCHES: {nation['DISPATCHES']}",
        f"FLAG: {nation['FLAG']}",
    ]
    double_spaced_text_lines = [line + "\n\n" for line in text_lines]

    # Split text lines into two columns
    mid_index = len(double_spaced_text_lines) // 2
    column1_lines = double_spaced_text_lines[:mid_index]
    column2_lines = double_spaced_text_lines[mid_index:]

    column1_text = "".join(column1_lines)
    column2_text = "".join(column2_lines)

    text_widget1.config(state=tk.NORMAL)
    text_widget1.delete(1.0, tk.END)
    text_widget1.insert(tk.END, column1_text)
    text_widget1.config(state=tk.DISABLED)

    text_widget2.config(state=tk.NORMAL)
    text_widget2.delete(1.0, tk.END)
    text_widget2.insert(tk.END, column2_text)
    text_widget2.config(state=tk.DISABLED)

    download_and_display_flag(nation, image_label, flag_user_agent)


def main():
    xml_user_agent = input("Enter the user agent for XML requests: ")
    flag_user_agent = input("Enter the user agent for flag image requests: ")
    region = input("Enter the region to check: ")
    print(f"Checking nations in region: {region}")

    # Load approved and unapproved nations
    approved_nations = load_approved_nations()
    print("Loaded approved nations.")
    unapproved_nations = load_unapproved_nations()
    print("Loaded unapproved nations.")

    # Download and parse nations XML
    xml_content = download_nations_xml(xml_user_agent)
    nations = parse_nations_xml(xml_content)

    # Find nations in the specified region
    nations_in_region = find_nations_in_region(nations, region)

    if not nations_in_region:
        print(f"No nations found in region {region}.")
        return

    print(f"Found {len(nations_in_region)} nations in region {region}.")

    # Filter out approved nations if unchanged
    new_nations = []
    for nation in nations_in_region:
        nation_id = nation["NAME"]
        if nation_id in approved_nations:
            if compare_nations(approved_nations[nation_id], nation):
                print(f"Nation {nation_id} is already approved and unchanged.")
                continue
        new_nations.append(nation)

    if not new_nations:
        print(f"All nations in region {region} are already approved and unchanged.")
        return

    root = tk.Tk()
    root.title("Nation Approval System")

    text_frame = tk.Frame(root)
    text_frame.pack(pady=10)

    text_widget1 = tk.Text(
        text_frame, wrap="word", state=tk.DISABLED, width=40, height=20
    )
    text_widget1.grid(row=0, column=0, padx=5)

    text_widget2 = tk.Text(
        text_frame, wrap="word", state=tk.DISABLED, width=40, height=20
    )
    text_widget2.grid(row=0, column=1, padx=5)

    image_label = tk.Label(root)
    image_label.pack(pady=10)

    def approve_nation():
        nonlocal current_nation_index
        nation = new_nations[current_nation_index]
        approved_nations[nation["NAME"]] = nation
        save_approved_nations(approved_nations)
        print(f"Nation {nation['NAME']} approved and saved.")
        delete_flag_image(nation)
        next_nation()

    def disapprove_nation():
        nonlocal current_nation_index
        nation = new_nations[current_nation_index]
        reason = simpledialog.askstring(
            "Input",
            "Please provide a reason for not approving this nation:",
            parent=root,
        )
        if reason:
            unapproved_nations[nation["NAME"]] = {"reason": reason}
            save_unapproved_nations(unapproved_nations)
            print(f"Nation {nation['NAME']} not approved. Reason: {reason}")
            delete_flag_image(nation)
            next_nation()

    def next_nation():
        nonlocal current_nation_index
        current_nation_index += 1
        if current_nation_index < len(new_nations):
            display_nation(
                new_nations[current_nation_index],
                text_widget1,
                text_widget2,
                image_label,
                flag_user_agent,
            )
        else:
            messagebox.showinfo("Info", "Safety check completed.")
            root.destroy()
            # List unapproved nations
            if unapproved_nations:
                print("\nList of unapproved nations:")
                for nation_name, info in unapproved_nations.items():
                    print(f"{nation_name}: {info['reason']}")

    current_nation_index = 0
    display_nation(
        new_nations[current_nation_index],
        text_widget1,
        text_widget2,
        image_label,
        flag_user_agent,
    )

    approve_frame = tk.Frame(root)
    approve_frame.pack(side="left", padx=20, pady=20)

    disapprove_frame = tk.Frame(root)
    disapprove_frame.pack(side="right", padx=20, pady=20)

    approve_label = tk.Label(approve_frame, text="Approve:")
    approve_label.pack()

    approve_button = tk.Button(
        approve_frame, text="Approve", command=approve_nation, bg="green", fg="white"
    )
    approve_button.pack()

    disapprove_label = tk.Label(disapprove_frame, text="Disapprove:")
    disapprove_label.pack()

    disapprove_button = tk.Button(
        disapprove_frame,
        text="Disapprove",
        command=disapprove_nation,
        bg="red",
        fg="white",
    )
    disapprove_button.pack()

    root.mainloop()

    # Delete any remaining flag images after the GUI is closed
    for nation in new_nations:
        delete_flag_image(nation)


if __name__ == "__main__":
    main()

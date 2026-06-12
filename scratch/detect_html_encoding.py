import os


def check_html_files():
    project_dir = "."
    for root, _dirs, files in os.walk(project_dir):
        # We want to find the exact file causing the error
        for file in files:
            if file.endswith(".html"):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "rb") as f:
                        content = f.read()
                    if content.startswith(b"\xff\xfe") or content.startswith(
                        b"\xfe\xff"
                    ):
                        print(f"UTF-16 BOM detected in: {file_path}")
                    else:
                        content.decode("utf-8")
                except UnicodeDecodeError as e:
                    print(f"Decode error in {file_path}: {e}")


if __name__ == "__main__":
    check_html_files()

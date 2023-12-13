import os

import fire


def consolidate_scripts(
    source_dir,
    output_filename="consolidated_scripts.txt",
    extensions=(".sh", ".fish", ".py"),
):
    """
    Consolidate scripts from a specified directory to a single file.

    Args:
    source_dir (str): Directory containing the scripts.
    output_filename (str, optional): Name of the output file. Defaults to 'consolidated_scripts.txt'.
    extensions (tuple, optional): Tuple of file extensions to include. Defaults to ('.sh', '.fish', '.py').
    """
    # Create the output file or overwrite if it already exists
    with open(output_filename, "w") as output_file:
        # Walk through the directory
        for root, dirs, files in os.walk(source_dir):
            for filename in files:
                # Check the file extension
                if filename.endswith(extensions) and not filename.startswith(
                    "__"
                ):
                    # Write the filename as a comment
                    output_file.write(f"# {filename}\n\n")
                    # Construct the full file path
                    file_path = os.path.join(root, filename)
                    # Read the contents of the file
                    with open(file_path, "r") as file:
                        content = file.read()
                        # Write the contents to the output file
                        output_file.write(content)
                        output_file.write("\n\n")

    print(f"Consolidated file created: {output_filename}")


if __name__ == "__main__":
    fire.Fire(consolidate_scripts)

import os
import zipfile

def extract_zip_flat(zip_file_path, extraction_path):
    """
    Extracts all files from a zip archive into a single directory, ignoring any nested directories in the zip.
    Existing files with the same name will be overwritten.

    Args:
        zip_file_path (str): Path to the zip file.
        extraction_path (str): Directory to extract all files into.

    Returns:
        list: List of file paths of the extracted files.
    """
    extracted_files = []

    # Ensure the extraction directory exists
    os.makedirs(extraction_path, exist_ok=True)

    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        # Iterate over each file in the zip file
        for member in zip_ref.namelist():
            # Skip directories (we only want files)
            if member.endswith('/'):
                continue

            # Get only the file name from the member, ignoring nested paths
            file_name = os.path.basename(member)

            # Define the target path in the extraction directory
            target_path = os.path.join(extraction_path, file_name)

            # Extract the file to the target path, overwriting if it already exists
            with zip_ref.open(member) as source, open(target_path, "wb") as target:
                target.write(source.read())

            # Append the final path of the extracted file
            extracted_files.append(target_path)

    return extracted_files

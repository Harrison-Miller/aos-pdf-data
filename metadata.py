import os
import hashlib
from datetime import datetime
import pdfplumber

def create_metadata(file_path):
    # Calculate file hash
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)

    # Get PDF metadata
    created_date = None
    with pdfplumber.open(file_path) as pdf:
        pdf_metadata = pdf.metadata
        if pdf_metadata and "CreationDate" in pdf_metadata:
            # PDF dates are often in the format "D:YYYYMMDDHHmmSS"
            date_str = pdf_metadata["CreationDate"]
            try:
                # Remove leading 'D:' if present
                if date_str.startswith("D:"):
                    date_str = date_str[2:]
                # Parse date
                created_date = datetime.strptime(date_str[:8], "%Y%m%d").strftime("%Y-%m-%d")
            except Exception:
                created_date = None

    # Fallback to file system creation date if PDF metadata is missing
    if not created_date:
        file_stats = os.stat(file_path)
        created_date = datetime.fromtimestamp(file_stats.st_ctime).strftime("%Y-%m-%d")

    # Create metadata
    metadata = {
        "title": os.path.basename(file_path),
        "filename": os.path.basename(file_path),
        "hash": hash_md5.hexdigest(),
        "publishedDate": created_date,
        "extractedDate": datetime.now().strftime("%Y-%m-%d"),
    }

    return metadata

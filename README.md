# AoS PDF Data Extractor

This project scrapes PDFs from a website and extracts structured data into JSON files.

## Prerequisites

- Python 3.8 or higher
- Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### 1. Run the scraper and extractor against the website

This command will scrape PDFs from the target website and process them:

```bash
python main.py --scrape
```

### 2. Run the extractor against a specified local PDF

This command will process a specific PDF file:

```bash
python main.py --extract /path/to/your/file.pdf
```

Replace `/path/to/your/file.pdf` with the path to your local PDF file.

## Output

Extracted JSON files will be saved in the `output/` directory:

- `faq.json`
- `rules.json`
- `battleprofile.json`

## License

This project is licensed under the MIT License. See the LICENSE file for details.

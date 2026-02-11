# YouTube Thumbnail Resizer

A desktop GUI tool for preparing YouTube thumbnails at **1280x720 (16:9)** using Python, Tkinter, and Pillow.

## Features

- Load JPG/JPEG/PNG images.
- Live image preview.
- Three resize modes:
  - **Fit with black padding** (preserves full image)
  - **Center crop to 16:9**
  - **Manual crop** by drawing on the preview canvas
- Optional **16:9 aspect lock** while drawing manual crop.
- Adjustable JPEG quality (1-100).
- Save as PNG or JPEG.

## Requirements

- Python 3.9+
- Pillow
- Tkinter (usually included with standard Python installs)

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
python youtube_thumbnail_resizer.py
```

## Usage

1. Click **Select Image...** and choose an image file.
2. Choose one of the resize modes:
   - **Fit with black padding**
   - **Center crop to 16:9**
   - **Manual crop** (draw a selection in the preview)
3. (Optional) Adjust JPEG quality.
4. Click **Resize and Save...** and choose output path/format.

## Notes

- YouTube thumbnail target size is **1280x720**.
- If you save as JPEG, the quality slider is used.
- If you save as PNG, lossless PNG export is used.

## Troubleshooting

- If `tkinter` is missing on Linux, install your distro package (example on Debian/Ubuntu):

```bash
sudo apt-get install python3-tk
```

- If Pillow is missing:

```bash
pip install pillow
```

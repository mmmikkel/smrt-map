# SG MRT Map Tools

This repository contains scripts and resources for processing and analyzing the Singapore MRT (Mass Rapid Transit) map, particularly focusing on extracting and manipulating rail paths from SVG files.

## Project Structure

- `sg-mrt-map.svg` — The original Singapore MRT map in SVG format.
- `sg-mrt-map-curved-rails.svg` — A variant of the map with curved rail paths.
- `extract_curved_rails.py` — Script to extract curved rail paths from the SVG file.
- `reverse_track_paths.py` — Script to reverse the direction of track paths in the SVG.

## Usage

1. **Extract Curved Rails**
   ```bash
   python extract_curved_rails.py
   ```
   This will process the SVG and extract curved rail paths.

2. **Reverse Track Paths**
   ```bash
   python reverse_track_paths.py
   ```
   This will reverse the direction of track paths in the SVG file.

## Requirements

- Python 3.x
- (Optional) Any additional dependencies will be listed in the script headers or comments.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details. 
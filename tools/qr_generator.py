
"""
QR Code Generator for Smart Glasses Navigation

This script reads location data from navigation.json and generates QR codes
for each location. Each QR code contains location information that the
smart glasses can scan and use to determine the user's exact position.
"""

import json
import os
from pathlib import Path
from typing import Optional
import qrcode
from PIL import Image, ImageDraw, ImageFont


# Configuration
NAVIGATION_JSON = "navigation.json"
OUTPUT_DIR = "qr_codes"
LOGO_PATH = None  # Optional: Path to logo image to add to QR code center


def load_navigation_data() -> dict:
    """Load navigation data from JSON file."""
    with open(NAVIGATION_JSON, 'r', encoding='utf-8') as f:
        return json.load(f)


def create_location_data(location: dict, building: dict) -> str:
    """
    Create JSON data string for QR code.
    This data will be embedded in the QR code and scanned by the smart glasses.
    """
    data = {
        "type": "location",
        "id": location["id"],
        "name": location["name"],
        "building": building["name"],
        "floor": location["floor"],
        "coordinates": location["coordinates"],
        "description": location["description"],
        "additional_info": location["additional_info"],
        "timestamp": None  # Will be set when scanned
    }
    return json.dumps(data, ensure_ascii=False)


def generate_qr_code(data: str, output_path: str, logo_path: Optional[str] = None) -> None:
    """
    Generate a QR code from the given data and save it as an image.
    
    Args:
        data: JSON string containing location data
        output_path: Path to save the QR code image
        logo_path: Optional path to a logo image to add to center
    """
    # Create QR code with high error correction
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=2,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    # Create QR code image
    qr_image = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to PIL Image if needed
    if not isinstance(qr_image, Image.Image):
        qr_image = qr_image.convert('RGB')
    
    # Add logo if provided
    if logo_path and os.path.exists(logo_path):
        logo = Image.open(logo_path)
        # Resize logo to fit in center (max 20% of QR code size)
        logo_size = min(qr_image.size) // 5
        logo.thumbnail((logo_size, logo_size), Image.Resampling.LANCZOS)
        
        # Calculate position to center logo
        logo_pos = (
            (qr_image.size[0] - logo.size[0]) // 2,
            (qr_image.size[1] - logo.size[1]) // 2
        )
        
        # Create transparent overlay for logo
        qr_image.paste(logo, logo_pos, logo if logo.mode == 'RGBA' else None)
    
    # Save QR code
    qr_image.save(output_path, "PNG")
    print(f"Generated: {output_path}")


def generate_labeled_qr_code(location: dict, building: dict, output_dir: str) -> str:
    """
    Generate a QR code with a label showing the location name.
    
    Args:
        location: Location data dictionary
        building: Building data dictionary
        output_dir: Directory to save the QR code
        
    Returns:
        Path to the generated QR code image
    """
    # Create location data
    data = create_location_data(location, building)
    
    # Generate QR code filename
    qr_filename = location.get("qr_code_filename", f"qr_{location['id']}.png")
    output_path = os.path.join(output_dir, qr_filename)
    
    # Generate QR code
    generate_qr_code(data, output_path, LOGO_PATH)
    
    # Create labeled version with location name
    labeled_path = output_path.replace(".png", "_labeled.png")
    create_labeled_qr_image(output_path, location["name"], location["floor"], labeled_path)
    
    return output_path


def create_labeled_qr_image(qr_path: str, location_name: str, floor: int, output_path: str) -> None:
    """
    Create a QR code image with a label showing the location name.
    
    Args:
        qr_path: Path to the QR code image
        location_name: Name to display as label
        floor: Floor number
        output_path: Path to save the labeled image
    """
    # Open QR code image
    qr_image = Image.open(qr_path)
    
    # Calculate label height (15% of QR code height)
    label_height = qr_image.height // 6
    
    # Create new image with space for label
    new_height = qr_image.height + label_height
    labeled_image = Image.new("RGB", (qr_image.width, new_height), "white")
    
    # Paste QR code at top
    labeled_image.paste(qr_image, (0, 0))
    
    # Create draw object for label
    draw = ImageDraw.Draw(labeled_image)
    
    # Try to load a font, fallback to default if not available
    try:
        font_size = max(12, label_height // 3)
        font = ImageFont.truetype("arial.ttf", font_size)
    except IOError:
        font = ImageFont.load_default()
    
    # Draw label background
    draw.rectangle(
        [(0, qr_image.height), (qr_image.width, new_height)],
        fill="#f0f0f0"
    )
    
    # Draw location name
    text = f"{location_name} (Floor {floor})"
    
    # Calculate text position (centered)
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_x = (qr_image.width - text_width) // 2
    text_y = qr_image.height + (label_height - (bbox[3] - bbox[1])) // 2
    
    draw.text((text_x, text_y), text, fill="black", font=font)
    
    # Save labeled image
    labeled_image.save(output_path, "PNG")
    print(f"Generated labeled: {output_path}")


def generate_printable_sheet(locations: list, building: dict, output_dir: str, filename: str = "qr_codes_printable.pdf") -> None:
    """
    Generate a printable PDF sheet with all QR codes and their labels.
    
    Args:
        locations: List of location dictionaries
        building: Building data dictionary
        output_dir: Directory to save the PDF
        filename: Output filename
    """
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import inch
        print("Using ReportLab for PDF generation")
    except ImportError:
        print("ReportLab not installed. Install with: pip install reportlab")
        return
    
    # Create printable sheet (3 QR codes per row, 4 rows per page)
    output_path = os.path.join(output_dir, filename)
    c = canvas.Canvas(output_path, pagesize=letter)
    width, height = letter
    
    margin = 0.5 * inch
    qr_size = 1.5 * inch
    spacing = 0.2 * inch
    
    x = margin
    y = height - margin - qr_size
    
    for i, location in enumerate(locations):
        # Check if we need a new page
        if i > 0 and i % 12 == 0:
            c.showPage()
            x = margin
            y = height - margin - qr_size
        
        # Generate QR code image path
        qr_filename = location.get("qr_filename", f"qr_{location['id']}.png")
        qr_path = os.path.join(output_dir, qr_filename)
        
        # Check if QR code exists, if not generate it
        if not os.path.exists(qr_path):
            generate_qr_code(
                create_location_data(location, building),
                qr_path,
                LOGO_PATH
            )
        
        # Draw QR code
        try:
            c.drawImage(qr_path, x, y, width=qr_size, height=qr_size)
        except Exception as e:
            print(f"Error drawing image: {e}")
        
        # Draw label below QR code
        label_text = f"{location['name']}\nFloor {location['floor']}"
        c.setFont("Helvetica", 8)
        c.drawCentredString(x + qr_size/2, y - 0.2 * inch, label_text)
        
        # Move to next position
        x += qr_size + spacing
        if (i + 1) % 3 == 0:
            x = margin
            y -= qr_size + 0.4 * inch
    
    c.save()
    print(f"Generated printable sheet: {output_path}")


def main():
    """Main function to generate all QR codes from navigation.json."""
    print("=" * 60)
    print("Smart Glasses QR Code Generator")
    print("=" * 60)
    
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Output directory: {OUTPUT_DIR}")
    
    # Load navigation data
    print(f"Loading data from: {NAVIGATION_JSON}")
    data = load_navigation_data()
    
    building = data.get("building", {})
    locations = data.get("locations", [])
    
    print(f"Building: {building.get('name', 'Unknown')}")
    print(f"Number of locations: {len(locations)}")
    print()
    
    # Generate QR codes for each location
    for location in locations:
        print(f"Processing: {location['name']}")
        generate_labeled_qr_code(location, building, OUTPUT_DIR)
        print()
    
    # Generate printable sheet
    print("Generating printable sheet...")
    generate_printable_sheet(locations, building, OUTPUT_DIR)
    
    print()
    print("=" * 60)
    print("QR Code generation complete!")
    print(f"QR codes saved to: {OUTPUT_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()

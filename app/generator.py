import os
import uuid
from PIL import Image, ImageDraw, ImageFont

def get_font(font_name: str, size: int):
    """Helper to locate TrueType fonts from system font directories or fallbacks."""
    windir = os.environ.get("WINDIR", "C:\\Windows")
    candidates = [
        font_name,
        os.path.join(windir, "Fonts", font_name),
        os.path.join(windir, "Fonts", "georgia.ttf"),
        os.path.join(windir, "Fonts", "georgiab.ttf"),
        os.path.join(windir, "Fonts", "times.ttf"),
        os.path.join(windir, "Fonts", "arial.ttf"),
    ]
    for path in candidates:
        if path and os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()

def draw_gold_seal(canvas, center_x, center_y, radius=65):
    """Draws a decorative gold seal badge with ribbon tail."""
    gold_outer = (212, 175, 55)
    gold_inner = (245, 215, 110)
    navy_dark = (20, 35, 65)

    # Ribbon tails
    ribbon_w = 28
    canvas.polygon([(center_x - 35, center_y + radius - 10),
                    (center_x - 55, center_y + radius + 70),
                    (center_x - 35, center_y + radius + 55),
                    (center_x - 15, center_y + radius + 70)], fill=gold_outer)

    canvas.polygon([(center_x + 15, center_y + radius - 10),
                    (center_x + 35, center_y + radius + 70),
                    (center_x + 15, center_y + radius + 55),
                    (center_x - 5, center_y + radius + 70)], fill=gold_outer)

    # Outer starburst / scalloped circle approximation
    canvas.ellipse([(center_x - radius, center_y - radius), (center_x + radius, center_y + radius)], fill=gold_outer, outline=navy_dark, width=3)
    
    # Inner circle
    r_in = radius - 12
    canvas.ellipse([(center_x - r_in, center_y - r_in), (center_x + r_in, center_y + r_in)], fill=gold_inner, outline=gold_outer, width=2)
    
    # Center star / badge core
    r_core = r_in - 10
    canvas.ellipse([(center_x - r_core, center_y - r_core), (center_x + r_core, center_y + r_core)], fill=navy_dark)
    
    # Text inside seal
    seal_font = get_font("arialbd.ttf", 14)
    canvas.text((center_x, center_y - 8), "OFFICIAL", fill=gold_inner, font=seal_font, anchor="mm")
    canvas.text((center_x, center_y + 8), "SEAL", fill=gold_inner, font=seal_font, anchor="mm")

def build_test_template(template_path="templates/base_template.png"):
    """Builds a high-resolution, professional certificate background template (1920x1350)."""
    os.makedirs(os.path.dirname(template_path), exist_ok=True)
    
    width, height = 1920, 1350
    base_img = Image.new('RGB', (width, height), color=(253, 251, 247)) # Warm cream off-white background
    canvas = ImageDraw.Draw(base_img)
    
    # Colors
    navy = (20, 35, 65)
    gold = (212, 175, 55)
    gold_light = (240, 220, 140)
    slate = (90, 100, 115)
    
    # Outer Navy Border
    canvas.rectangle([(40, 40), (width - 40, height - 40)], outline=navy, width=12)
    
    # Inner Gold Border
    canvas.rectangle([(65, 65), (width - 65, height - 65)], outline=gold, width=4)
    
    # Thin Inner Accent Frame
    canvas.rectangle([(75, 75), (width - 75, height - 75)], outline=navy, width=1)
    
    # Decorative Corner Accents
    corner_size = 50
    corners = [
        (85, 85),
        (width - 85 - corner_size, 85),
        (85, height - 85 - corner_size),
        (width - 85 - corner_size, height - 85 - corner_size)
    ]
    for cx, cy in corners:
        canvas.rectangle([(cx, cy), (cx + corner_size, cy + corner_size)], outline=gold, width=2)

    # Header Ribbon Top Banner
    canvas.rectangle([(450, 100), (width - 450, 108)], fill=gold)

    # Title & Headers
    font_title = get_font("georgiab.ttf", 64)
    font_subtitle = get_font("arialbd.ttf", 22)
    font_body = get_font("georgiai.ttf", 26)

    canvas.text((width / 2, 170), "CERTIFICATE OF COMPLETION", fill=navy, font=font_title, anchor="mm")
    
    # Gold Underline Accent for Title
    canvas.line([(width / 2 - 250, 220), (width / 2 + 250, 220)], fill=gold, width=3)

    canvas.text((width / 2, 280), "THIS IS PROUDLY PRESENTED TO", fill=slate, font=font_subtitle, anchor="mm")
    
    canvas.text((width / 2, 590), "for successfully completing all requirements and coursework for", fill=slate, font=font_body, anchor="mm")

    # Gold Seal at Bottom Center
    draw_gold_seal(canvas, center_x=int(width / 2), center_y=1050, radius=70)

    # Footer Signature & Date Lines
    line_y = 1100
    font_footer = get_font("arial.ttf", 20)
    font_footer_val = get_font("georgiab.ttf", 22)

    # Left: Date
    canvas.line([(250, line_y), (600, line_y)], fill=navy, width=2)
    canvas.text((425, line_y - 25), "October 07, 2026", fill=navy, font=font_footer_val, anchor="mm")
    canvas.text((425, line_y + 25), "DATE OF ISSUANCE", fill=slate, font=font_footer, anchor="mm")

    # Right: Signature
    canvas.line([(width - 600, line_y), (width - 250, line_y)], fill=navy, width=2)
    canvas.text((width - 425, line_y - 30), "Authorized Instructor", fill=navy, font=get_font("georgiai.ttf", 28), anchor="mm")
    canvas.text((width - 425, line_y + 25), "AUTHORIZED SIGNATURE", fill=slate, font=font_footer, anchor="mm")

    base_img.save(template_path)
    return template_path


def generate_single_certificate(recipient_name: str, template_path: str, output_dir: str, course_name: str = None, font_path: str = None):
    """Generates a high-quality certificate PNG with centered dynamic text sizing."""
    try:
        if not recipient_name or not recipient_name.strip():
            return {"status": "FAILED", "file_path": None, "error_reason": "Empty recipient name"}

        os.makedirs(output_dir, exist_ok=True)
        
        if not os.path.exists(template_path):
            build_test_template(template_path)
            
        base_img = Image.open(template_path)
        canvas = ImageDraw.Draw(base_img)
        img_w, img_h = base_img.size
        
        navy = (20, 35, 65)
        gold = (212, 175, 55)

        # 1. Dynamic Font Sizing for Recipient Name
        clean_name = recipient_name.strip()
        max_name_width = img_w - 400
        
        target_size = 72
        if len(clean_name) > 25:
            target_size = 56
        if len(clean_name) > 35:
            target_size = 44
        if len(clean_name) > 50:
            target_size = 34

        name_font = get_font(font_path or "georgiab.ttf", target_size)

        # Recipient Name at center height ~ 430
        name_y = 430
        canvas.text((img_w / 2, name_y), clean_name, fill=navy, font=name_font, anchor="mm")
        
        # Recipient Name Decorative Gold Accent Line
        name_bounds = canvas.textbbox((img_w / 2, name_y), clean_name, font=name_font, anchor="mm")
        text_w = name_bounds[2] - name_bounds[0]
        underline_w = max(text_w + 60, 300)
        canvas.line([(img_w / 2 - underline_w / 2, name_y + target_size / 2 + 15),
                     (img_w / 2 + underline_w / 2, name_y + target_size / 2 + 15)], fill=gold, width=3)

        # 2. Course Name (if provided)
        if course_name and course_name.strip():
            course_font = get_font("georgiab.ttf", 38)
            canvas.text((img_w / 2, 670), course_name.strip(), fill=navy, font=course_font, anchor="mm")

        # Save output PNG
        safe_name = "".join(c if c.isalnum() else "_" for c in clean_name).strip("_") or "unnamed"
        out_filename = f"{safe_name}_{uuid.uuid4().hex[:8]}.png"
        final_path = os.path.join(output_dir, out_filename)
        
        base_img.save(final_path)
        return {"status": "GENERATED", "file_path": final_path, "error_reason": None}
        
    except (IOError, ValueError, Exception) as e:
        return {"status": "FAILED", "file_path": None, "error_reason": str(e)}

if __name__ == "__main__":
    test_template = "templates/base_template.png"
    out_folder = "output"
    
    build_test_template(test_template)
    
    res = generate_single_certificate("Alice Johnson", test_template, out_folder, course_name="Fullstack Web Development")
    print(f"[{res['status']}] Output -> {res.get('file_path')}")

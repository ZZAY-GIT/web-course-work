import os
import math
from PIL import Image, ImageDraw, ImageFont

def draw_rounded_rectangle(draw, x, y, w, h, radius, fill, outline, width=2):
    draw.rounded_rectangle(
        [(x, y), (x + w, y + h)],
        radius=radius,
        fill=fill,
        outline=outline,
        width=width
    )

def draw_record_node(draw, x, y, w, h, title, fields, font, font_bold):
    # Draw outer box
    draw_rounded_rectangle(draw, x, y, w, h, 12, (248, 248, 248), (51, 51, 51), width=2)
    
    # Draw vertical separator
    sep_x = x + 90
    draw.line([(sep_x, y), (sep_x, y + h)], fill=(51, 51, 51), width=1)
    
    # Draw table title (bold, centered in the left column)
    bbox_title = draw.textbbox((0, 0), title, font=font_bold)
    tw = bbox_title[2] - bbox_title[0]
    th = bbox_title[3] - bbox_title[1]
    draw.text((x + (90 - tw)/2, y + (h - th)/2 - 2), title, font=font_bold, fill=(0, 0, 0))
    
    # Draw fields list
    lines = fields.split('\n')
    line_heights = []
    for line in lines:
        if not line:
            line_heights.append(font.size)
            continue
        bbox_l = draw.textbbox((0, 0), line, font=font)
        lh = bbox_l[3] - bbox_l[1]
        line_heights.append(lh)
        
    total_height = sum(line_heights) + 5 * (len(lines) - 1)
    curr_y = y + (h - total_height) / 2
    
    for i, line in enumerate(lines):
        if line:
            draw.text((sep_x + 10, curr_y - 2), line, font=font, fill=(0, 0, 0))
        curr_y += line_heights[i] + 5

def draw_arrow(draw, start, end, label=None, font=None, fill=(51, 51, 51)):
    x1, y1 = start
    x2, y2 = end
    
    # Draw main line
    draw.line([start, end], fill=fill, width=2)
    
    # Calculate angle for arrowhead
    dx = x2 - x1
    dy = y2 - y1
    angle = math.atan2(dy, dx)
    
    # Arrowhead parameters
    arrow_len = 10
    arrow_angle = math.pi / 6  # 30 degrees
    
    # Calculate arrowhead points
    ax1 = x2 - arrow_len * math.cos(angle - arrow_angle)
    ay1 = y2 - arrow_len * math.sin(angle - arrow_angle)
    ax2 = x2 - arrow_len * math.cos(angle + arrow_angle)
    ay2 = y2 - arrow_len * math.sin(angle + arrow_angle)
    
    # Draw arrowhead
    draw.polygon([end, (ax1, ay1), (ax2, ay2)], fill=fill)
    
    # Draw label if provided
    if label and font:
        # Put label slightly offset from the midpoint of the line
        mx = (x1 + x2) / 2
        my = (y1 + y2) / 2
        
        # Offset perpendicular to line direction
        perp_angle = angle + math.pi / 2
        lx = mx + 12 * math.cos(perp_angle)
        ly = my + 12 * math.sin(perp_angle)
        
        bbox = draw.textbbox((0, 0), label, font=font)
        lw = bbox[2] - bbox[0]
        lh = bbox[3] - bbox[1]
        
        draw.text((lx - lw/2, ly - lh/2 - 2), label, font=font, fill=(51, 51, 51))

def main():
    width = 1720
    height = 620
    
    # Create white canvas
    img = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    
    font_path = "C:\\Windows\\Fonts\\arial.ttf"
    if not os.path.exists(font_path):
        font_path = "arial.ttf"
        
    try:
        font = ImageFont.truetype(font_path, 11)
        font_bold = ImageFont.truetype(font_path, 11)
        font_label = ImageFont.truetype(font_path, 10)
    except IOError:
        font = ImageFont.load_default()
        font_bold = font
        font_label = font
        
    # Table definitions: (title, fields, x, y, w, h)
    tables = {
        "users": ("users", "id PK\nemail\npassword_hash\nrole", 20, 360, 180, 100),
        "doctors": ("doctors", "id PK\nuser_id FK\nfull_name\nspecialization\ncabinet", 270, 260, 200, 110),
        "patients": ("patients", "id PK\nuser_id FK\nfull_name\nbirth_date\nphone", 270, 420, 200, 110),
        "schedule_slots": ("schedule_slots", "id PK\ndoctor_id FK\ndate\nstart_time\nend_time\nstatus", 550, 20, 210, 120),
        "services": ("services", "id PK\ntitle\nprice\nduration", 550, 190, 210, 90),
        "appointments": ("appointments", "id PK\npatient_id FK\ndoctor_id FK\nservice_id FK\nslot_id FK\nstatus", 820, 200, 220, 140),
        "medical_records": ("medical_records", "id PK\npatient_id FK\ncard_number\nblood_type\nrh_factor\nallergies\nchronic_diseases\ncreated_at\nupdated_at", 820, 390, 230, 210),  # Expanded height and size!
        "visits": ("visits", "id PK\nrecord_id FK\nappointment_id FK\ndiagnosis\nrecommendations", 1150, 380, 230, 120),
        "documents": ("documents", "id PK\npatient_id FK\nvisit_id FK\nfile_path\nfile_type", 1470, 420, 220, 120)
    }
    
    # Draw all record nodes
    for name, data in tables.items():
        title, fields, x, y, w, h = data
        draw_record_node(draw, x, y, w, h, title, fields, font, font_bold)
        
    # Helper to get exact connection points
    def pt(name, side):
        title, fields, x, y, w, h = tables[name]
        if side == "left":
            return (x, y + h/2)
        elif side == "right":
            return (x + w, y + h/2)
        elif side == "top":
            return (x + w/2, y)
        elif side == "bottom":
            return (x + w/2, y + h)
        return (x + w/2, y + h/2)
        
    # Draw all relations
    # 1. users -> patients [1:1]
    draw_arrow(draw, pt("users", "right"), pt("patients", "left"), "1:1", font_label)
    
    # 2. users -> doctors [1:1]
    draw_arrow(draw, pt("users", "right"), pt("doctors", "left"), "1:1", font_label)
    
    # 3. doctors -> schedule_slots [1:N]
    # Connect top-right of doctors to bottom-left of schedule_slots
    draw_arrow(draw, (370, 260), (550, 80), "1:N", font_label)
    
    # 4. patients -> appointments [1:N]
    # Connect top-right of patients to bottom-left of appointments
    draw_arrow(draw, (370, 420), (820, 270), "1:N", font_label)
    
    # 5. doctors -> appointments [1:N]
    draw_arrow(draw, pt("doctors", "right"), pt("appointments", "left"), "1:N", font_label)
    
    # 6. services -> appointments [1:N]
    draw_arrow(draw, pt("services", "right"), pt("appointments", "left"), "1:N", font_label)
    
    # 7. schedule_slots -> appointments [1:1]
    # Connect right of schedule_slots to top of appointments
    draw_arrow(draw, pt("schedule_slots", "right"), (930, 200), "1:1", font_label)
    
    # 8. patients -> medical_records [1:1]
    draw_arrow(draw, pt("patients", "right"), pt("medical_records", "left"), "1:1", font_label)
    
    # 9. medical_records -> visits [1:N]
    draw_arrow(draw, pt("medical_records", "right"), pt("visits", "left"), "1:N", font_label)
    
    # 10. appointments -> visits [1:0..1]
    draw_arrow(draw, pt("appointments", "right"), (1265, 380), "1:0..1", font_label)
    
    # 11. patients -> documents [1:N]
    # Ломаная линия в обход остальных таблиц: опускаемся до y=610, идем вправо до x=1580 и поднимаемся к низу documents
    draw.line([(370, 530), (370, 610), (1580, 610), (1580, 540)], fill=(51, 51, 51), width=2)
    draw.polygon([(1580, 540), (1575, 550), (1585, 550)], fill=(51, 51, 51))
    draw.text((975, 592), "1:N", font=font_label, fill=(51, 51, 51))
    
    # 12. visits -> documents [1:N]
    draw_arrow(draw, pt("visits", "right"), pt("documents", "left"), "1:N", font_label)
    
    # Save image
    img.save("er_diagram.png", "PNG")
    print("Generated er_diagram.png successfully.")

if __name__ == "__main__":
    main()

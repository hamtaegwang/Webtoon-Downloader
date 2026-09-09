import os
from PIL import Image

def clean_logo():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    source_path = os.path.join(base_dir, "Webtoon Downloader.png")
    icon_png_path = os.path.join(base_dir, "assets", "icon.png")
    icon_ico_path = os.path.join(base_dir, "assets", "icon.ico")
    icon_clean_path = os.path.join(base_dir, "assets", "icon_clean.png")

    if not os.path.exists(source_path):
        return

    img = Image.open(source_path).convert("RGBA")
    width, height = img.size
    
    # 1. 네이버 그린 색상 범위 정의
    def is_naver_green(p):
        return abs(p[0]-3) < 70 and abs(p[1]-199) < 70 and abs(p[2]-90) < 70

    # 2. 로고 영역(그린 박스) 찾기
    min_x, min_y = width, height
    max_x, max_y = 0, 0
    found = False

    for y in range(height):
        for x in range(width):
            p = img.getpixel((x, y))
            if is_naver_green(p):
                found = True
                min_x = min(min_x, x)
                max_x = max(max_x, x)
                min_y = min(min_y, y)
                max_y = max(max_y, y)

    if not found:
        img.save(icon_png_path, "PNG")
        return

    # 영역 추출 (약간의 마진 포함)
    margin = 2
    logo_box = (
        max(0, min_x - margin),
        max(0, min_y - margin),
        min(width, max_x + margin + 1),
        min(height, max_y + margin + 1)
    )
    logo_img = img.crop(logo_box)
    
    # 3. 고품질 부드러운 외곽선을 위한 마스크 생성 (Super-Sampled Anti-aliasing)
    from PIL import ImageDraw
    
    lw, lh = logo_img.size
    ss = 4  # Super-sampling factor
    
    # 4배 크기로 마스크를 그려서 다운샘플링하여 부드러운 안티앨리어싱 구현
    mask_large = Image.new("L", (lw * ss, lh * ss), 0)
    draw_large = ImageDraw.Draw(mask_large)
    radius_large = int(min(lw, lh) * 0.15) * ss
    draw_large.rounded_rectangle([0, 0, lw * ss - 1, lh * ss - 1], radius=radius_large, fill=255)
    
    # LANCZOS 필터로 다운샘플링하여 부드러운 마스크 생성
    mask = mask_large.resize((lw, lh), Image.LANCZOS)
    
    # 마스크 적용
    logo_img.putalpha(mask)

    # 4. 저장
    os.makedirs(os.path.dirname(icon_png_path), exist_ok=True)
    
    # PNG 저장 (256x256 이상 유지하여 고화질 보장)
    # 윈도우에서는 256x256 아이콘이 표준이므로 리사이즈해서 저장
    icon_png = logo_img.resize((256, 256), Image.LANCZOS)
    icon_png.save(icon_png_path, "PNG")
    icon_png.save(icon_clean_path, "PNG")

    # 5. ICO 생성 (각 레이어별로 개별 리사이즈하여 선명도 극대화)
    icon_sizes = [16, 24, 32, 48, 64, 128, 256]
    ico_layers = []
    for s in icon_sizes:
        # 각 사이즈마다 LANCZOS 필터로 리사이즈하여 선명하게 만듦
        layer = logo_img.resize((s, s), Image.LANCZOS)
        ico_layers.append(layer)
        
    icon_png.save(icon_ico_path, format="ICO", append_images=ico_layers)
    print(f"[+] 로고 영역({min_x}, {min_y} ~ {max_x}, {max_y}) 부드러운 안티앨리어싱 처리 및 고화질 빌드 완료!")

if __name__ == "__main__":
    clean_logo()

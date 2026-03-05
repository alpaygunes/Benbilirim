import json
import os
import random
import platform
import ctypes
import time
from datetime import datetime

def filter_by_current_date(node_data):
    """
    Node içindeki kayıtları sistem tarihindeki ay ve gün ile eşleşenlere göre filtreler.
    Eğer eşleşen veri yoksa, 'date' değeri olmayan veya null olan kayıtları döndürür.
    """
    if not node_data:
        return []
    
    # Sistem tarihindeki ay ve günü al
    now = datetime.now()
    current_month = now.month
    current_day = now.day
    
    filtered_data = []
    items_without_date = []
    
    for item in node_data:
        # 'date' alanı yoksa veya null ise, bunları ayrı bir listede tut
        if 'date' not in item or not item['date'] or item['date'] is None:
            items_without_date.append(item)
            continue
            
        try:
            # Date alanını parse et (format: "2026-01-05 00:00:00")
            date_str = item['date'].strip()
            # Tarih string'ini parse et
            item_date = datetime.strptime(date_str.split()[0], "%Y-%m-%d")
            
            # Ay ve gün eşleşiyorsa ekle
            if item_date.month == current_month and item_date.day == current_day:
                filtered_data.append(item)
        except (ValueError, AttributeError, IndexError):
            # Tarih parse edilemezse bu kaydı göz ardı et
            continue
    
    # Eğer gün ve ay ile eşleşen veri yoksa, date değeri olmayan/null olan verileri döndür
    if not filtered_data and items_without_date:
        return items_without_date
    
    return filtered_data


def select_random_node(json_file_path):
    """
    JSON dosyasından rasgele bir düğüm (anahtar-değer çifti) seçer.
    Sistem tarihindeki ay ve gün ile eşleşen kayıtları filtreler.
    """

    # JSON dosyasını oku
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Her node'u tarih filtresinden geçir
    filtered_data = {}
    for node_name, node_data in data.items():
        filtered_node_data = filter_by_current_date(node_data)
        if filtered_node_data:  # Sadece boş olmayan node'ları ekle
            filtered_data[node_name] = filtered_node_data
    
    # Eğer hiç filtreleme sonrası node kalmadıysa, orijinal datayı kullan
    if not filtered_data:
        filtered_data = data
    
    # Rasgele bir düğümü seç
    # Düğüm = bir sayfanın tüm verileri
    random_node_name = random.choice(list(filtered_data.keys()))
    random_node_data = filtered_data[random_node_name]

    # Düğüm içerisinden rasgele bir kaydı seç
    random_item = None
    if random_node_data:
        random_item = random.choice(random_node_data)


    return {
        "node_name": random_node_name,
        "node_data": random_node_data,
        "random_item": random_item if random_node_data else None
    }


def select_all_random_samples(json_file_path):
    """
    JSON dosyasındaki her düğümden rasgele birer kaydı seçer.
    Sistem tarihindeki ay ve gün ile eşleşen kayıtları filtreler.
    """

    # JSON dosyasını oku
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    samples = {}

    #print(f"\n{'=' * 60}")
    #print(f"✓ Her Düğümden Rasgele Birer Kayıt Seçildi")
    #print(f"{'=' * 60}\n")

    for node_name, node_data in data.items():
        # Tarih filtresinden geçir
        filtered_node_data = filter_by_current_date(node_data)
        
        if filtered_node_data:  # Sadece filtreleme sonrası boş olmayan node'ları kullan
            random_item = random.choice(filtered_node_data)
            samples[node_name] = random_item

            #print(f"📌 {node_name.upper()}:")
            #print(json.dumps(random_item, ensure_ascii=False, indent=2))
            #print()

    return samples


def get_image_path(result):
    image_name = result["random_item"].get("images")
    if not image_name:
        return None
    else:
        image_name = image_name.replace(" ", "_")

    okul_turu = load_settings('okul_turu')
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), f"data/{okul_turu}/resimler/{image_name}")


def load_settings(ayar):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(script_dir, 'ayarlar.json'), 'r', encoding='utf-8') as f:
        settings = json.load(f)
    return settings[ayar]


def create_new_image(image_path, result):
    answer=wrong=correct=desc=title = ''
    # Sadece değer varsa atama yap
    if result["random_item"].get("title"):
        title = result["random_item"].get("title")
    if result["random_item"].get("desc"):
        desc = result["random_item"].get("desc")

    if result["random_item"].get("correct"):
        correct = result["random_item"].get("correct")
    if result["random_item"].get("wrong"):
        wrong = result["random_item"].get("wrong")
    if result["random_item"].get("answer"):
        answer = result["random_item"].get("answer")

    node_name = result["node_name"]

    if node_name == "expression":
        pass
    elif node_name == "value":
        pass
    elif node_name == "game":
        pass
    elif node_name == "preference":
        title = "Tercihler"
    elif node_name == "proverb":
        pass
    elif node_name == "reason":
        pass
    elif node_name == "yemek":
        pass
    elif node_name == "spelling":
        title       = "Doğru Yanlış"
    elif node_name == "suggestion":
        pass
    elif node_name == "word":
        pass
    elif node_name == "puzzle":
        title = "Bilmece"
    elif node_name == "Günün Ayeti":
        pass
    elif node_name == "hadis":
        title = "Hadis"
    elif node_name == "zit_anlam":
        title = "Zıt Anlamlı Kelimeler"

    # Import PIL modules
    from PIL import Image, ImageDraw, ImageFont
    mesaj_konumu = load_settings('mesaj_konumu')
    boyut_yuzde = load_settings('boyut_yuzde')
    kutu_img_path = f"{os.path.dirname(os.path.abspath(__file__))}/assets/msg_bg0.png"

    kutu_img = Image.open(kutu_img_path)
    # PNG'nin alfa kanalını korumak için RGBA moduna dönüştür
    if kutu_img.mode != 'RGBA':
        kutu_img = kutu_img.convert('RGBA')

    draw = ImageDraw.Draw(kutu_img)

    # Resim boyutlarını al
    img_w, img_h = kutu_img.size

    if result["node_name"] == "preference" \
        or result["node_name"] == "spelling" \
        or result["node_name"] == "zit_anlam":

        # Önce title'ı, diğer if bloğundakiyle aynı mantıkta yaz
        max_title_w = int(img_w * 0.50)
        initial_title_font_size = 96

        def get_adjusted_font_size(text, font_path, max_width, initial_size):
            font_size = initial_size
            while font_size > 10:
                font = ImageFont.truetype(font_path, font_size)
                bbox = draw.textbbox((0, 0), text, font=font)
                text_w = bbox[2] - bbox[0]
                if text_w <= max_width:
                    return font
                font_size -= 2
            return ImageFont.truetype(font_path, 10)

        fontT = get_adjusted_font_size(
            title,
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets/Alkatra-VariableFont_wght.ttf'),
            max_title_w,
            initial_title_font_size
        )

        title_bbox = draw.textbbox((0, 0), title, font=fontT)
        title_w = title_bbox[2] - title_bbox[0]
        title_h = title_bbox[3] - title_bbox[1]

        title_x = (img_w - title_w) // 2
        title_y = int(img_h * 0.2)  # kutunun üst kısmında

        draw.text((title_x, title_y), title, font=fontT, fill='black')

        # Sadece correct ve wrong yaz

        correct_text = result["random_item"].get("correct", "")
        wrong_text = result["random_item"].get("wrong", "")

        item_font = ImageFont.truetype(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets/Alkatra-VariableFont_wght.ttf'), 90)
        # İkonları yükle (RGBA)
        zit_anlam_icon = Image.open(f'{os.path.dirname(os.path.abspath(__file__))}/assets/zit.png')
        yanlis_icon = Image.open(f'{os.path.dirname(os.path.abspath(__file__))}/assets/yanlis.png')
        if yanlis_icon.mode != 'RGBA':
            yanlis_icon = yanlis_icon.convert('RGBA') 

        dogru_icon = Image.open(f'{os.path.dirname(os.path.abspath(__file__))}/assets/dogru.png')
        if dogru_icon.mode != 'RGBA':
            dogru_icon = dogru_icon.convert('RGBA')

        if result["node_name"] == "zit_anlam":
            yanlis_icon = zit_anlam_icon
            dogru_icon = zit_anlam_icon

        yanlis_w, yanlis_h = yanlis_icon.size
        dogru_w, dogru_h = dogru_icon.size

        # wrong ve correct için bbox'ları al
        wrong_bbox = draw.textbbox((0, 0), wrong_text, font=item_font)
        wrong_w = wrong_bbox[2] - wrong_bbox[0]
        wrong_h = wrong_bbox[3] - wrong_bbox[1]

        correct_bbox = draw.textbbox((0, 0), correct_text, font=item_font)
        correct_w = correct_bbox[2] - correct_bbox[0]
        correct_h = correct_bbox[3] - correct_bbox[1]

        # "2 karakter boşluk" için genişlik (örnek: iki boşluk)
        space_bbox = draw.textbbox((0, 0), "  ", font=item_font)
        space_w = space_bbox[2] - space_bbox[0]

        # Her satır için toplam genişlik (ikon + boşluk + yazı)
        wrong_row_w = yanlis_w + space_w + wrong_w
        correct_row_w = dogru_w + space_w + correct_w

        # Her satırın yüksekliği (ikon/yazıdan büyük olan)
        wrong_row_h = max(yanlis_h, wrong_h)
        correct_row_h = max(dogru_h, correct_h)

        # Satırlar arası boşluk
        line_spacing = 90

        # İki satırın toplam yüksekliği
        total_h = wrong_row_h + line_spacing + correct_row_h

        # Dikey ortalama: üst satırın (wrong) başlayacağı Y
        start_y = (img_h - total_h) // 2

        # wrong satırı yatayda ortala
        wrong_row_x = (img_w - wrong_row_w) // 2
        wrong_row_y = start_y

        # ikonun Y'sini satır içinde ortala
        yanlis_x = wrong_row_x
        yanlis_y = wrong_row_y + (wrong_row_h // 2)

        # yazının X,Y'si (ikon + 2 karakterlik boşluk sonrası, satıra göre ortalanmış)
        wrong_text_x = yanlis_x + yanlis_w + space_w
        wrong_text_y = wrong_row_y + (wrong_row_h - wrong_h) // 2

        # İkonu ve yazıyı çiz
        kutu_img.paste(yanlis_icon, (yanlis_x, yanlis_y), yanlis_icon)
        draw.text((wrong_text_x, wrong_text_y), wrong_text, font=item_font, fill='black')

        # correct satırı (altta) yatayda ortala
        correct_row_y = wrong_row_y + wrong_row_h + line_spacing
        correct_row_x = (img_w - correct_row_w) // 2

        dogru_x = correct_row_x
        dogru_y = correct_row_y + (dogru_h // 2)

        correct_text_x = dogru_x + dogru_w + space_w
        correct_text_y = correct_row_y + (correct_row_h - correct_h) // 2

        kutu_img.paste(dogru_icon, (dogru_x, dogru_y), dogru_icon)
        draw.text((correct_text_x, correct_text_y), correct_text, font=item_font, fill='black')
    else:
        # Title için maksimum genişlik (%50)
        max_title_w = int(img_w * 0.50)

        # Description için maksimum genişlik (%75)
        max_desc_w = int(img_w * 0.75)

        # Font boyutlarını belirle
        initial_title_font_size = 96
        desc_font_size = 48

        # Title font boyutunu ayarla
        def get_adjusted_font_size(text, font_path, max_width, initial_size):
            """Metni verilen genişliğe sığdırmak için uygun font boyutunu bulur"""
            font_size = initial_size

            while font_size > 10:  # Minimum font boyutu 10
                font = ImageFont.truetype(font_path, font_size)
                bbox = draw.textbbox((0, 0), text, font=font)
                text_w = bbox[2] - bbox[0]

                if text_w <= max_width:
                    return font, font_size

                font_size -= 2  # 2px düşür

            # En düşük boyutta bile sığmazsa
            return ImageFont.truetype(font_path, 10), 10

        # Title için uygun font boyutunu bul
        fontT, title_font_size = get_adjusted_font_size(
            title,
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets/Alkatra-VariableFont_wght.ttf'),
            max_title_w,
            initial_title_font_size
        )

        # Başlangıç description fontu
        fontD = ImageFont.truetype(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets/Alkatra-VariableFont_wght.ttf'),
            desc_font_size)

        # Title metni için bounding box al
        title_bbox = draw.textbbox((0, 0), title, font=fontT)
        title_w = title_bbox[2] - title_bbox[0]
        title_h = title_bbox[3] - title_bbox[1]

        # Description metnini satırlara böl
        def wrap_text(text, font, max_width):
            """Metni verilen genişliğe göre satırlara böler"""
            lines = []
            words = text.split()
            current_line = ""

            for word in words:
                test_line = current_line + word + " "
                bbox = draw.textbbox((0, 0), test_line, font=font)
                test_w = bbox[2] - bbox[0]

                if test_w <= max_width:
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line.strip())
                    current_line = word + " "

            # Döngü bittikten sonra kalan satırı ekle
            if current_line:
                lines.append(current_line.strip())

            return lines

        max_desc_h = int(img_h * 0.50)

        # Description satırlarını ve yüksekliğini hesaplayan yardımcı blok
        def calc_desc_layout(desc_font):
            lines = wrap_text(desc, desc_font, max_desc_w)
            line_height_local = 0
            for line in lines:
                line_bbox = draw.textbbox((0, 0), line, font=desc_font)
                line_h_local = line_bbox[3] - line_bbox[1]
                line_height_local = max(line_height_local, line_h_local)
            # 10 = satırlar arası boşluk
            total_desc_h_local = line_height_local * len(lines) + (len(lines) - 1) * 10 if lines else 0
            return lines, line_height_local, total_desc_h_local

        # Başlangıç fontu ile description yüksekliğini hesapla
        desc_lines, line_height, total_desc_h = calc_desc_layout(fontD)

        # Yükseklik %80 sınırını aşıyorsa description fontunu küçült
        while total_desc_h > max_desc_h and desc_font_size > 10:
            desc_font_size -= 2
            fontD = ImageFont.truetype(
                os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets/Alkatra-VariableFont_wght.ttf'),
                desc_font_size)
            desc_lines, line_height, total_desc_h = calc_desc_layout(fontD)

        # Toplam metin yüksekliği
        total_h = title_h + total_desc_h + 40  # 40 = aralarındaki boşluk

        # Yatay orta konum
        title_bbox = draw.textbbox((0, 0), title, font=fontT)
        title_w = title_bbox[2] - title_bbox[0]
        title_x = (img_w - title_w) // 2

        # Dikey orta konum
        start_y = (img_h - total_h) // 5.5
        title_y = img_h*.15 + (title_h)
        #print(title_y)
        desc_y = start_y + title_h + 200

        # Title'ı çiz
        draw.text((title_x, title_y), title, font=fontT, fill='black')

        # Description satırlarını çiz
        current_y = desc_y
        for line in desc_lines:
            line_bbox = draw.textbbox((0, 0), line, font=fontD)
            line_w = line_bbox[2] - line_bbox[0]
            line_x = (img_w - line_w) // 2

            draw.text((line_x, current_y), line, font=fontD, fill='black')

            line_h = line_bbox[3] - line_bbox[1]
            current_y += line_h + 10  # 10 = satırlar arası boşluk

        # ANSWER yazısı
        if 'answer' in locals():
            answer_font = ImageFont.truetype(
                os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets/Alkatra-VariableFont_wght.ttf'), 30)
            # Metnin gerçek bounding box'ını al (sol/üst offset dahil)
            tmp_bbox = draw.textbbox((0, 0), answer, font=answer_font)
            x0, y0, x1, y1 = tmp_bbox
            answer_w = x1 - x0
            answer_h = y1 - y0

            padding = 8  # kenarlardan boşluk

            # Canvas boyutunu bbox ve padding'e göre ayarla
            text_img_w = answer_w + padding * 2
            text_img_h = answer_h + padding * 2
            text_img = Image.new('RGBA', (text_img_w, text_img_h), (0, 0, 0, 0))
            text_draw = ImageDraw.Draw(text_img)

            # Metni çizerken bbox offsetini telafi et
            # Böylece üst kısmı canvas içinde kalır (kırpma olmaz)
            base_x = padding - x0
            base_y = padding - y0

            shadow_offset = (0, 0)
            # Gölge
            text_draw.text(
                (base_x + shadow_offset[0], base_y + shadow_offset[1]),
                answer,
                font=answer_font,
                fill='black'
            )

            # Ana yazı
            text_draw.text(
                (base_x, base_y),
                answer,
                font=answer_font,
                fill='red'
            )

            # 180 derece döndür
            text_img = text_img.rotate(180, expand=True)

            tw, th = text_img.size

            margin_x = int(img_w * 0.15)
            margin_y = int(img_h * 0.12)

            answer_x = img_w - tw - margin_x
            answer_y = img_h - th - margin_y

            kutu_img.paste(text_img, (answer_x, answer_y), text_img)

    w, h = kutu_img.size
    new_w = int(w * boyut_yuzde / 100)
    new_h = int(h * boyut_yuzde / 100)
    kutu_img = kutu_img.resize((new_w, new_h))

    ana_img = Image.open(image_path)
    # Ana resmi de RGBA moduna dönüştür (saydam alanları desteklemek için)
    if ana_img.mode != 'RGBA':
        ana_img = ana_img.convert('RGBA')

    ana_w, ana_h = ana_img.size

    x = 0
    y = 0
    if mesaj_konumu == 'ust_sol_kose':
        x = 0
        y = 0
    elif mesaj_konumu == 'ust_sag_kose':
        x = ana_w - new_w
        y = 0
    elif mesaj_konumu == 'alt_sol_kose':
        x = 0
        y = ana_h - new_h
    elif mesaj_konumu == 'alt_sag_kose':
        x = ana_w - new_w
        y = ana_h - new_h
    elif mesaj_konumu == 'merkez':
        x = (ana_w - new_w) // 2
        y = (ana_h - new_h) // 2

    kutuyu_goster = True
    if title != "" or desc != "" or answer != "" or correct != "" or wrong != "":
        kutuyu_goster = True 
    
    if title =="Bilmece" and desc =="":
        kutuyu_goster = False
    
    if node_name =="expression" and desc =="":
        kutuyu_goster = False
    
    if node_name =="zit_anlam" and (correct == "" or wrong == ""):
        kutuyu_goster = False

    if kutuyu_goster:
        ana_img.paste(kutu_img, (x, y), kutu_img)
    
    print ("Title : ", title)
    print ("desc : ", desc)
    print ("node_name : ", node_name)
    print ("kutuyu_goster : ", kutuyu_goster)

    # RGBA'dan RGB'ye dönüştür (JPG kaydetmek için)
    if ana_img.mode == 'RGBA':
        rgb_img = Image.new('RGB', ana_img.size, (255, 255, 255))
        rgb_img.paste(ana_img, mask=ana_img.split()[3])  # [3] = alfa kanalı
        # Dosya varsa üzerine yaz
        rgb_img.save(f"{os.path.dirname(os.path.abspath(__file__))}/YeniResim.jpg", quality=95)
    else:
        # Dosya varsa üzerine yaz
        ana_img.save(f"{os.path.dirname(os.path.abspath(__file__))}/YeniResim.jpg", quality=95)

    time.sleep(0.5)  # Dosya yazılması tamamen bitsin diye
    setDesktop_wallpaper(f"{os.path.dirname(os.path.abspath(__file__))}/YeniResim.jpg")


def setDesktop_wallpaper(image_path):
    """Set desktop wallpaper from given image path for GNOME, Cinnamon, Xfce, macOS, and Windows"""
    if not os.path.exists(image_path):
        return False

    system = platform.system()

    if system == "Windows":
        import ctypes
        SPI_SETDESKWALLPAPER = 20
        try:
            abs_path = os.path.abspath(image_path)
            ctypes.windll.user32.SystemParametersInfoW(SPI_SETDESKWALLPAPER, 0, abs_path, 3)
            return True
        except:
            return False

    elif system == "Linux":
        try:
            abs_image_path = os.path.abspath(image_path)
            #print(f'Denenen yol: {abs_image_path}')
            #print(f'Dosya var mı: {os.path.exists(abs_image_path)}')

            # Masaüstü ortamını algıla
            desktop_env = os.getenv('XDG_CURRENT_DESKTOP', '').lower()
            #print(f'Masaüstü Ortamı: {desktop_env}')

            success = False

            # GNOME
            if 'gnome' in desktop_env:
                #print("✓ GNOME algılandı")
                os.system("gsettings set org.gnome.desktop.background picture-options 'scaled'")
                result = os.system(f"gsettings set org.gnome.desktop.background picture-uri 'file://{abs_image_path}'")
                result2 = os.system(f"gsettings set org.gnome.desktop.background picture-uri-dark 'file://{abs_image_path}'")
                success = (result == 0 or result2 == 0)

            # Cinnamon (Linux Mint)
            elif 'cinnamon' in desktop_env or 'mint' in desktop_env.lower():
                #print("✓ Cinnamon algılandı")
                result = os.system(f"gsettings set org.cinnamon.desktop.background picture-uri 'file://{abs_image_path}'")
                os.system("gsettings set org.cinnamon.desktop.background picture-options 'scaled'")
                success = (result == 0)

            # Xfce
            elif 'xfce' in desktop_env:
                #print("✓ Xfce algılandı")
                # Xfce için xfconf-query kullanıyoruz
                result = os.system(f"xfconf-query -c xfdesktop -p /backdrop/screen0/monitor0/image-path -s '{abs_image_path}'")
                result2 = os.system(f"xfconf-query -c xfdesktop -p /backdrop/screen0/monitor0/image-style -s 4")  # 4 = scaled
                success = (result == 0 or result2 == 0)

            # Fallback: GNOME'yi dene
            else:
                #print("✓ Varsayılan olarak GNOME deneniyor")
                os.system("gsettings set org.gnome.desktop.background picture-options 'scaled'")
                result = os.system(f"gsettings set org.gnome.desktop.background picture-uri 'file://{abs_image_path}'")
                success = (result == 0)

            #print(f'Sonuç: {"Başarılı" if success else "Başarısız"}')
            return success

        except Exception as e:
            #print(f'Hata: {e}')
            return False

    elif system == "Darwin":  # macOS
        try:
            os.system(
                f"osascript -e 'tell application \"System Events\" to set picture of every desktop to POSIX file \"{os.path.abspath(image_path)}\"'")
            return True
        except:
            return False

    return False


def main():
    json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data/data.json")
    # Seçenek 1: Rasgele bir düğüm seç 
    result = select_random_node(json_path)
    image_path = get_image_path(result) 
    if image_path and os.path.exists(image_path):
        create_new_image(image_path, result)
    else:
        okul_turu = load_settings('okul_turu')
        # Resim dizinini oluştur
        resimler_dizini = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"data/{okul_turu}/resimler")

        # Dizindeki tüm resimleri listele
        resim_listesi = [f for f in os.listdir(resimler_dizini) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

        if resim_listesi:
            # Rasgele bir resim seç
            rasgele_resim = random.choice(resim_listesi)
            image_path = os.path.join(resimler_dizini, rasgele_resim)
            create_new_image(image_path, result)
        else:
            print(f"Hata: {resimler_dizini} dizininde resim bulunamadı!")


if __name__ == "__main__":
    main()

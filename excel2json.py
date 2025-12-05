import openpyxl
import json
import os


def parse_name(name):
    """
    İsmi "-" karakterine göre parçalayıp ikinci parçayı döndürür.
    Örnek: "Metin   -desc" -> "desc"
    """
    if name is None:
        return name
    
    # İsmi string'e dönüştür
    name_str = str(name).strip()
    
    # "-" karakterini bul
    if "-" in name_str:
        parts = name_str.split("-")
        if len(parts) >= 2:
            # İkinci parçayı al ve boşlukları temizle
            return parts[1].strip()
    
    # "-" yoksa orijinal ismi döndür
    return name_str


def excel_to_json(excel_file_path, output_json_path=None):
    """
    Excel dosyasını JSON'a dönüştürür.
    Her sayfanın 2. satırındaki başlıkları JSON düğümü olarak kullanır.
    Sayfa isimleri ve sütun isimlerini "-" karakterine göre parçalayıp ikinci parçayı kullanır.
    """

    # Excel dosyasını aç
    workbook = openpyxl.load_workbook(excel_file_path)

    # Tüm sayfaları içerecek dictionary
    all_sheets_data = {}

    # Her bir sayfayı işle
    for sheet_name in workbook.sheetnames:
        # Sayfa ismini parçala
        parsed_sheet_name = parse_name(sheet_name)
        
        sheet = workbook[sheet_name]

        # 2. satırdan başlayarak işle
        # 2. satır başlıkları içerir
        headers = []
        for cell in sheet[2]:
            if cell.value is not None:
                # Sütun ismini parçala
                parsed_header = parse_name(cell.value)
                headers.append(parsed_header)

        # 3. satırdan sonraki verileri oku
        data_list = []
        for row_idx, row in enumerate(sheet.iter_rows(min_row=3, values_only=True), start=3):
            # Boş satırları atla
            if all(cell is None for cell in row):
                continue

            # Veri dictionary'si oluştur
            row_data = {}
            for col_idx, header in enumerate(headers):
                if col_idx < len(row):
                    row_data[header] = row[col_idx]

            data_list.append(row_data)

        # Sayfanın verilerini ekle
        all_sheets_data[parsed_sheet_name] = data_list

    # Workbook'u kapat
    workbook.close()

    # JSON'a dönüştür
    json_output = json.dumps(all_sheets_data, ensure_ascii=False, indent=2)

    # Çıktı dosyası belirtilmemişse, aynı dizine ".json" olarak kaydet
    if output_json_path is None:
        output_json_path = excel_file_path.replace('.xlsx', '.json')

    # JSON dosyasını kaydet
    with open(output_json_path, 'w', encoding='utf-8') as f:
        f.write(json_output)

    print(f"✓ Dönüştürme başarılı!")
    print(f"✓ Çıktı dosyası: {output_json_path}")

    return all_sheets_data

def load_settings(ayar):
    with open('ayarlar.json', 'r', encoding='utf-8') as f:
        settings = json.load(f)
    return settings[ayar]

if __name__ == "__main__":
    # Çıktı dizini tanımla
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_folder = os.path.join(script_dir, "data")

    # data/ilkokul dizinindeki data.xlsx dosyasını dönüştür
    okul_turu = load_settings('okul_turu')
    excel_path = f"{data_folder}/{okul_turu}/data.xlsx"

    # Dosyanın var olup olmadığını kontrol et
    if os.path.exists(excel_path):
        
        result = excel_to_json(excel_path, f"{data_folder}/data.json")
        print(f"\n✓ Toplam {len(result)} sayfa işlendi")
        print(f"✓ Sayfalar: {', '.join(result.keys())}")
    else:
        print(f"✗ Hata: {excel_path} dosyası bulunamadı!")
import os

# --- AYARLAR ---

# 1. HARİÇ TUTULACAK KLASÖRLER (Bunlar kod değil, sistem dosyalarıdır)
# Eğer venv klasörünü de almak istersen buradaki 'venv'yi sil.
IGNORE_DIRS = {
    'venv', '.git', '__pycache__', '.pytest_cache', 
    '.idea', '.vscode', 'node_modules', 'htmlcov'
}

# 2. HARİÇ TUTULACAK DOSYALAR
# Scriptin kendisini ve çıktı dosyasını tekrar içine yazmaması lazım.
output_file = 'tum_kodlar.txt'
script_name = os.path.basename(__file__)
IGNORE_FILES = {
    output_file, script_name, 
    'poetry.lock', 'package-lock.json', '.DS_Store'
}

# 3. HARİÇ TUTULACAK UZANTILAR (Okunamaz Binary Dosyalar)
# Resimler, veritabanı dosyaları ve derlenmiş kodlar metin değildir.
IGNORE_EXTENSIONS = {
    '.pyc', '.pyo', '.pyd',          # Python compiled
    '.png', '.jpg', '.jpeg', '.gif', '.ico', '.svg', # Resimler
    '.exe', '.dll', '.so', '.bin',   # Executables
    '.sqlite3', '.db',               # Veritabanı
    '.zip', '.tar', '.gz', '.rar',   # Arşivler
    '.pdf', '.docx'                  # Dökümanlar
}

# --- İŞLEM BAŞLIYOR ---

def is_text_file(file_path):
    """Basitçe uzantıya bakarak binary olup olmadığını kontrol eder"""
    _, ext = os.path.splitext(file_path)
    return ext.lower() not in IGNORE_EXTENSIONS

with open(output_file, 'w', encoding='utf-8') as outfile:
    # Proje dizinini gez
    for root, dirs, files in os.walk("."):
        # Gereksiz klasörleri gezme listesinden (dirs) çıkar
        # Bu işlem os.walk'un o klasörlerin içine girmesini engeller
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        
        for file in files:
            if file in IGNORE_FILES:
                continue
            
            # Uzantı kontrolü (Sadece metin dosyalarını al)
            if not is_text_file(file):
                continue

            file_path = os.path.join(root, file)
            
            # Dosya başlığı ekle (Okumayı kolaylaştırmak için)
            outfile.write(f"\n{'='*50}\n")
            outfile.write(f"DOSYA: {file_path}\n")
            outfile.write(f"{'='*50}\n\n")
            
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as infile:
                    # errors='ignore' ile UTF-8 olmayan karakterlerde patlamasını engelledik
                    outfile.write(infile.read())
            except Exception as e:
                outfile.write(f"HATA: Dosya okunamadı - {e}")
            
            outfile.write("\n")

print(f"✅ Bütün proje kodları '{output_file}' dosyasına başarıyla kaydedildi!")
print(f"📁 Hariç tutulan klasörler: {IGNORE_DIRS}")
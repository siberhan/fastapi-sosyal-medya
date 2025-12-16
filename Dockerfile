# 1. Hangi Python sürümü üzerine kuracağız? (Temel İmaj)
FROM python:3.10

# 2. Container'ın içinde hangi klasörde çalışacağız?
WORKDIR /usr/src/app

# 3. Önce requirements dosyasını kopyala
# (Bunu ayrı yapıyoruz ki kod değişse bile kütüphaneleri tekrar tekrar indirmesin - Cache mantığı)
COPY requirements.txt ./

# 4. Kütüphaneleri yükle
RUN pip install --no-cache-dir -r requirements.txt

# 5. Şimdi geri kalan bütün proje dosyalarını kopyala
COPY . .

# 6. Uygulamayı başlat (Uvicorn ile)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# tests/test_main.py

def test_root(client):
    res = client.get("/")
    # Ana sayfanda ne yazıyorsa onu kontrol et.
    # Eğer {"message": "Hello World"} dönüyorsa:
    print(res.json()) # Hatayı görmek için
    assert res.status_code == 200
    # assert res.json().get('message') == 'Hello World' (Mesajın neyse ona göre düzelt)
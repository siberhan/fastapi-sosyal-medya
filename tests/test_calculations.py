# tests/test_calculations.py
from app.calculations import add

def test_add():
    print("Toplama fonksiyonu test ediliyor...")
    sum = add(5, 3)
    assert sum == 8  # 5 + 3'ün 8 olmasını bekliyoruz [cite: 1574]
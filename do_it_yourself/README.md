# Deploy apki Dash w plotly cloud

---

## Step 1 - przejdź do katalogu projektu

```bash

cd do_it_yourself/dash_app
```

---

## Step 2 - zainstaluj zależności projektu

```bash

pip install -r requirements.txt
```

---

## Step 3 - doinstaluj wsparcie dla Plotly Cloud

```bash

pip install "dash[cloud]"
```

---

## Step 4 - wpisz swój własny napis

Otwórz plik `app.py`.

Wpisz se swój customowy tekst w linii `7`.

```python
# 🚀✨🎯👉 TU wpisz swój customowy tekst! 🌟🔥💫💥
CUSTOM_TEXT = "67"
```

---

## Step 5 - uruchom aplikację lokalnie
Upewnij się, że jesteś w directory `Plotly-introduction\do_it_yourself`
Następnie uruchom aplikację:
```bash
python app.py
```

Potem otwórz:
http://127.0.0.1:8050/

---

## Step 6 - Kliknij "Plotly Cloud" w prawym dolnym rogu

![img.png](screenshots/img.png)

---

## Step 7 - Sign In
![img.png](screenshots/img_4.png)

## Step 8 - Po automatycznym przekierowaniu podaj email do którego pamiętasz hasło
![img.png](screenshots/img_5.png)

## Step 9 - Wybierz email sign in code ( prostsze )
![img.png](screenshots/img_6.png)
I następnie wklej kod co przyszedł na maila

## Step 10 - Potwierdź urządzenie
![img_1.png](screenshots/img_7.png)
![img_3.png](screenshots/img_9.png)
Na 99.9% straczy po prostu kliknąć `"Confirm"`

## Step 11 - Wpisz nazwe swojej apki dash + "Publish App"
![img_3.png](screenshots/img_3.png)

## Uwaga

Jeśli coś nie działa:
- sprawdź katalog
- sprawdź czy działa lokalnie
- sprawdź dash[cloud]
- sprawdź runtime.txt (python-3.12)

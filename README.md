# WinRun

Раннер в стиле Subway Surfers на Python + Kivy. 3 полосы, прыжки, монеты, бонусы, 4 локации.

## Запуск на ПК (Python 3.12+)
```
pip install -r requirements.txt
python main.py
```
Управление: ← → / A D — смена полосы, ↑ / W / Пробел — прыжок, ↓ / S — быстрое приземление, Esc — пауза.
На телефоне: свайпы.

## Сборка APK через GitHub (с ПК, Windows/Mac/Linux)
1. Создай пустой репозиторий на github.com.
2. В папке проекта:
   ```
   git init
   git add .
   git commit -m "WinRun"
   git branch -M main
   git remote add origin https://github.com/<ты>/<репо>.git
   git push -u origin main
   ```
3. Вкладка **Actions → Build WinRun APK** (первая сборка 20–40 минут).
4. Готовый файл: внутри запуска → **Artifacts → WinRun-apk** (`.apk`).

Python 3.12 используется на раннере GitHub для запуска Buildozer. Версию Python внутри APK выбирает python-for-android.

## Ассеты
Все спрайты вырезаны из `tools/sheet.png` скриптом `python tools/extract_assets.py` (нужны `pillow`, `numpy`).
Чтобы поменять арт — замени PNG в `assets/` под теми же именами.

## Что в игре
- Бонусы: магнит, звезда (доска-неуязвимость), x2, кроссовки (высокий прыжок), сундук.
- Препятствия: поезда и светофор — объезжать, остальное — перепрыгивать.
- Три сердца; после удара за героем бегут охранник и собака.

# utils/storage.py
import json

def load_data(file_path):
    """Загружает данные из JSON-файла."""
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}

import json

def save_data(file_path, data):
    """Сохраняет данные в JSON-файл."""
    try:
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4, ensure_ascii=False)
        print(f"✅ Данные успешно сохранены в {file_path}")  # Отладка
    except Exception as e:
        print(f"❌ Ошибка сохранения данных: {e}")
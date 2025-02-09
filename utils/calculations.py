def calculate_fuel(city, highway, district, idle, norms):
    """
    Рассчитывает расход топлива на основе параметров поездки и норм расхода.
    """

    # Проверяем, что все нормы есть и являются строками с числами
    if not all(key in norms and isinstance(norms[key], str) for key in ["city", "highway", "district", "idle"]):
        raise ValueError(f"Некорректные нормы расхода: {norms}")

    # Преобразуем нормы в float (не округляем, как ввел пользователь)
    city_norm = float(norms["city"])
    highway_norm = float(norms["highway"])
    district_norm = float(norms["district"])
    idle_norm = float(norms["idle"])

    # Расчёт расхода топлива
    city_fuel = city * city_norm
    highway_fuel = highway * highway_norm
    district_fuel = district * district_norm
    idle_fuel = idle * idle_norm

    total_fuel = city_fuel + highway_fuel + district_fuel + idle_fuel

    # ✅ Округляем только при возврате
    return {
        "city_fuel": round(city_fuel, 2),
        "highway_fuel": round(highway_fuel, 2),
        "district_fuel": round(district_fuel, 2),
        "idle_fuel": round(idle_fuel, 2),
        "total_fuel": round(total_fuel, 2),
    }
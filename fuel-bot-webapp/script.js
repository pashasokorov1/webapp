let tg = window.Telegram.WebApp;
tg.expand();  // Разворачиваем WebApp на весь экран

// Функция для добавления машины
function addCar() {
    const carNumber = document.getElementById("carNumber").value;
    const city = document.getElementById("city").value;
    const highway = document.getElementById("highway").value;
    const district = document.getElementById("district").value;
    const idle = document.getElementById("idle").value;

    if (!carNumber || !city || !highway || !district || !idle) {
        alert("Пожалуйста, заполните все поля.");
        return;
    }

    tg.sendData(`add_car_${carNumber}_${city}_${highway}_${district}_${idle}`);
    alert("Машина добавлена!");
}

// Функция для добавления поездки
function addTrip() {
    const startOdometer = document.getElementById("startOdometer").value;
    const km = document.getElementById("km").value;
    const cityKm = document.getElementById("cityKm").value;
    const highwayKm = document.getElementById("highwayKm").value;
    const districtKm = document.getElementById("districtKm").value;
    const idleTime = document.getElementById("idleTime").value;
    const fuelStart = document.getElementById("fuelStart").value;
    const refuel = document.getElementById("refuel").value;

    if (!startOdometer || !km || !cityKm || !highwayKm || !districtKm || !idleTime || !fuelStart || !refuel) {
        alert("Пожалуйста, заполните все поля.");
        return;
    }

    tg.sendData(`add_trip_${startOdometer}_${km}_${cityKm}_${highwayKm}_${districtKm}_${idleTime}_${fuelStart}_${refuel}`);
    alert("Поездка добавлена!");
}

// Функция для отображения списка машин
function viewCars() {
    // Здесь можно получить список машин, например, через API или static data
    const cars = ["А123ВМ", "Б456ГН", "В789ДЕ"];
    const listDiv = document.getElementById("carsList");

    cars.forEach(car => {
        const carElement = document.createElement("div");
        carElement.innerText = car;
        listDiv.appendChild(carElement);
    });
}
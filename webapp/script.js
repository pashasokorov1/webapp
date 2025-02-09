let tg = window.Telegram.WebApp;

tg.expand();  // Развернуть WebApp на весь экран

function addCar() {
    tg.sendData("add_car");  // Отправка данных боту для добавления машины
}

function viewCars() {
    tg.sendData("view_cars");  // Отправка данных боту для просмотра списка машин
}

function addTrip() {
    tg.sendData("add_trip");  // Отправка данных боту для добавления поездки
}
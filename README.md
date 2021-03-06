# ДЗ №4 - Авторизация на FastAPI

## Задача

### Анонимный пользователь может:
- Создать аккаунт, если выбранный username еще не зарегистрирован в системе.
- Войти в свой аккаунт по username и паролю.
- Просмотреть список постов.
- Просмотреть детально определенный пост.

### Авторизованный пользователь может:
- Просмотреть свой профиль.
- Создать пост.
- Изменить свои личные данные — email, username и др. И получить новый access_token

### Задание со звездочкой:
- Валидировать данные при регистрации и обновлении данных пользователя
- Хранить в Redis заблокированные access_tokens (удобно хранить это в разных базах)
- Хранить в Redis активные refresh_tokens для определенного пользователя (удобно хранить
это в разных базах)
- Добавить метод выхода из аккаунта (
на этом этапе надо добавить access_token в список заблокированных токенов в Redis,
удалить refresh_token из списка активных токенов в Redis определенного пользователя
)
- Выйти со всех устройств. (удалить все активные refresh_token для определенного
пользователя)


## Развертывание локально
- Запустить docker-compose.yml файл командой

`docker-compose up --build -d`

- запустить миграции командой

`alembic upgrade head`


## HTTP API

Для проверки эндпоинтов можно воспользоваться коллекцией в Postman из папки docs.
Там же лежат uml диаграммы use case и схема БД.

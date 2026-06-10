# Программное средство для подбора вакансий в сфере информационных технологий
## Подготовка перед запуском программы:
1. После скачивания и распаковки poiisk_VKR-main нужно перейти с помощью терминала в каталог Poiisk_site, желательно в Visual Studio Code (Пример конечного пути: C:\Users\Home\Desktop\poiisk_VKR-main\Poiisk_site> ). Затем последовательно ввести следующие команды:
   - python -m venv venv (Создание виртуального окружения)
   - venv\Scripts\activate (Активировать виртуальное окружение в Windows)
   - pip install -r requirements.txt (Установка зависимостей)
   - npm install (Устанавливает все зависимости из package.json и package-lock.json в папке node_modules)
     
    p.s. для перехода между каталогами вперед и назад можно использовать команды "cd Название_папки" и "cd .."
---
2. Далее надо подготовить БД в PostgreSQL и конфигурацию. Для этого надо открыть pgAdmin 4 и сделать следующее:
   - Нажать ПКМ по Databases > Create > Database... (И дать любое название пустой БД)
   - Нажать по созданной БД ПКМ > Restore... > Выбрать файл, лежащий в poiisk_VKR-main\poiisk.backup
   
   Затем заново открыть редактор кода (Visual Studio Code) и сделать следующее:
   - Открыть файл poiisk_VKR-main\Poiisk_site\backend\config.py и сверить правильность названия БД, хост, пароль, порт в DB_CONFIG
---
3. В файл backend/.env вставить Secret key, полученный на сайте SuperJob: https://api.superjob.ru/register/ (Callback URL	указать http://localhost:5173)
   
   Пример как выглядит часть ключа:
   SUPERJOB_SECRET_KEY=v3.r.139770433.b915 ... (96 символов)
---
4. В файл backend/token.txt вставить только Authorization key, полученный на сайте GigaChat API после регистрации: https://developers.sber.ru/portal/products/gigachat-api. Доступен бесплатный тариф.
   
   Пример как выглядит часть ключа:
   MDE5ZDZhMWUtZjkyYy03Nm ... (100 символов)

## Запуск программы:
Предварительно сделав 4 предыдущих шага и находясь в каталоге \poiisk_VKR-main\Poiisk_site> при активированном виртуальном окружении (venv) ввести: npm run dev

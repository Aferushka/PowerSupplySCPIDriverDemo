**ТЗ**:

Разработать приложение («драйвер») для работы с промышленным 4-х канальным источником питания со следующими возможностями:
1.            Постоянный опрос телеметрии источника питания (текущее напряжение, ток, мощность по каждому каналу);
2.           Логгирование телеметрии - в файл. Каждое измерение - с меткой времени;
3.           Имеет команду на включение канала питания (параметры: номер канала питания, заданное напряжение, заданный ток);
4.           Имеет команду на отключение канала питания(параметры: номер канала питания);
5.           Имеет команду на запрос текущего состояния всех каналов питания (время измерения, значение напряжений, токов по всем каналам питания). Выходной формат - json.
6.           Внешний API для программы - REST
7.           Использовать asyncio
 
ПО обменивается с источником питания по tcp/ip по протоколу scpi (текстовый формат с разделителем \n). 
 
Алгоритм включения канала питания. Выдать команды:
1.            Задать ток для канала питания (подсистема SOURCE)
2.           Задать напряжение для канала питания (подсистема SOURCE)
3.           Включить выход канала питания (подсистема OUTPUT)
 
Алгоритм отключения канала питания:
1.            Отключить выход канала питания (подсистема OUTPUT)
 
Алгоритм опроса канала питания:
1.            Запросить состояние канала питания (подсистема MEASURE)
 
Документация на источник питания: https://www.gwinstek.com/en-global/products/downloadSeriesDownNew/14242/1737
 
тесты предлагается разбить на 3 части:
1.            тесты, проверяющие, что при обращении на url будет вызываться нужный метод нужного класса (типа роутинг до методов)
2.           тесты, проверящие, что в результате вызова метода выдаются правильные команды на через tcp-ip
3.           тесты, проверяющие корректность обработки данных, полученных от прибора
Примечание: во время тестов не должно происходить передачи данных по сети. Прибор “мокаем”


***Комментарии***:

Для простоты пропущены некоторые несущественные  в конкретном случае детали и почти все обработчики исключений.

Для запуска тестов достаточно использовать команду `pytest` в корневой директории проекта при активированном окружении.

В проекте также реализована простая и неоптимизированная версия транслятора SCPI команд.

Примеры http запросов к REST API:

`curl --request GET --url http://localhost:8080/` - получить телеметрию.

`curl --request POST --url http://localhost:8080/channel_on --header 'Content-Type: application/json' --data '{
	"channel": 1,
	"current": 20.0,
	"voltage": 100.0
}'` - включить 1 первый канал с данными параметрами тока и напряжения.

`curl --request POST --url http://localhost:8080/channel_off --header 'Content-Type: application/json' --data '{
	"channel": 1
}'` - отключить 1 канал.
SCPI_COMMAND_TRANSLATION_LOGS = False  # Выводить в консоль результат парсинга поступившей SCPI команды
SCPI_TREE_SHOW = False  # Выводить в консоль дерево SCPI транслятора после построения

IMITATOR_ACTION_EXECUTION_LOGS = False  # Выводить в консоль логгирование вызова методов имитатора блока питания с параметрами

DRIVER_TELEMETRY_LOG_FILENAME = 'telemetry.logs'  # Название файла хранения логов телеметрии
DRIVER_TELEMETRY_DELAY = 10  # Время между сеансами сбора телеметрии в секундах
DRIVER_SHOW_TELEMETRY = False  # Выводить в консоль собранную телеметрию

LOW_INTERFACE_SENT_COMMAND_LOG_BUFFER_SIZE = 10  # Размер буфера хранения логов переданных SCPI команд

REST_API_PORT = 8080  # Порт, на котором доступен REST API

import re
from enum import Enum

from settings import SCPI_TREE_SHOW


class SCPIVariableType(Enum):
    """
    Соответствие возможного типа параметра и его регулярного выражения для получения из части текстовой команды
    """
    Float = r'[a-zA-Z]+ (\d+\.\d+)'
    Integer = r'[a-zA-Z]+(\d+)'
    State = r'[a-zA-Z]+ (\d+|ON|OFF)'


class SCPITranslator:
    """
    Транслятор текстовых SCPI команд в конечный метод с парсингом параметров из команды с использованием дерева
    команд SCPI протокола
    """

    def __init__(self):
        self.root_node = Node('')  # Вершина дерева
        self.create_default_tree()

    def create_default_tree(self):
        """
        Создать дерево команд SCPI протокола
        """
        self.add_node('SOURce', variable_type=SCPIVariableType.Integer, variable_name='channel')
        self.add_node('CURRent', parent='SOURce', variable_type=SCPIVariableType.Float, variable_name='current',
                      operation='set_current')
        self.add_node('VOLTage', parent='SOURce', variable_type=SCPIVariableType.Float, variable_name='voltage',
                      operation='set_voltage')
        self.add_node('OUTPut', variable_type=SCPIVariableType.Integer, variable_name='channel')
        self.add_node('STATe', parent='OUTPut', variable_type=SCPIVariableType.State, variable_name='state',
                      operation='set_channel')
        self.add_node('MEASure', variable_type=SCPIVariableType.Integer, variable_name='channel')
        self.add_node('ALL', parent='MEASure', operation='get_all_measure_from_channel')

        if SCPI_TREE_SHOW:
            print('SCPI commands tree:')
            self.root_node.print_tree()

    def add_node(self, tag, parent='', variable_type=None, variable_name=None, operation=None):
        """
        Добавить нового потомка ноде, определенной её путем в дереве (node1/node5/node25)
        """
        parent_node = self.root_node
        for parent_name in parent.split('/'):
            if not parent_name:
                continue
            parent_node = parent_node.get_child(parent_name)

        parent_node.add_child(Node(tag, variable_type=variable_type, variable_name=variable_name, operation=operation))

    def translate(self, command_text):
        """
        Пройтись по дереву команд и транслировать SCPI команду в набор конечного метода и его параметров
        """
        result = {'command': None, 'kwargs': {}}
        node = self.root_node

        for step in command_text.split(':'):
            if not step:
                continue

            node = node.get_child(step)
            var = node.process_step(step)
            if var:
                result['kwargs'][node.variable_name] = var

        result['command'] = node.operation
        return result


class Node:
    """
    Класс, описывающий ноду дерева SCPI команд
    """

    def __init__(self, tag, variable_type=None, variable_name=None, operation=None):
        self.tag = tag  # Идентификатор
        self.variable_type = variable_type  # Идентификатор регулярного выражения для парсинга параметра
        self.variable_name = variable_name  # Имя распарсенного параметра для последующей передачи в метод
        self.operation = operation  # Имя метода
        self.children = []  # Набор нод-потомков

    def add_child(self, new_child):
        """
        Добавить нового потомка
        """
        self.children.append(new_child)

    def get_child(self, tag):
        """
        Вернуть потомка по его идентификатору
        """
        for child in self.children:
            if child.tag in tag:
                return child

        raise ChildNotFound()

    def process_step(self, command_part: str):
        """
        Принять соответствующий ноде кусочек SCPI команды с параметром и распарсить его
        """
        if not self.variable_type:
            return

        res = re.findall(self.variable_type.value, command_part)
        if res:
            param_value = res[0]
            if '.' in param_value:
                return float(param_value)
            try:
                return int(param_value)
            except:
                return param_value
        raise CantGetParamFromCommand(command_part)

    def print_tree(self, indent=1):
        """
        Вывести графическое представление дерева команд в консоль
        """
        print('    ' * indent + (self.tag if self.tag else 'Root'))
        for child in self.children:
            child.print_tree(indent=indent + 1)

    def __str__(self):
        return f'{self.tag} node'


class ChildNotFound(Exception):
    pass


class CantGetParamFromCommand(Exception):
    pass

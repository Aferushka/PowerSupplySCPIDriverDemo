class InterfaceBaseException(Exception):
    ...


class InterfaceInitializationException(InterfaceBaseException):
    ...


class NotEnoughParamsException(InterfaceInitializationException):
    ...
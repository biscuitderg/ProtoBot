from functools import wraps


class InvalidLoggerTypeArgumentException(Exception):  # Really long amirite ;)
    pass


class LoggerEntry:
    @property
    def channel(self):
        return f"{str(self)}_channel"

    def __repr__(self):
        return self.__class__.__name__

    def __str__(self):
        return self.__class__.__name__

    @staticmethod
    def converter(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            final_args = {}
            for name, value in kwargs.items():
                adapt = func.__annotations__.get(name)
                if adapt is not None:
                    final_args[name] = adapt(value)
                else:
                    final_args[name] = value
            return func(*args, **kwargs)
        return wrapper

    @staticmethod
    def check(param):
        return LoggerEntry._check(param())

    @classmethod
    def _check(cls, argument):
        if isinstance(argument, LoggerEntry):
            return argument
        else:
            raise InvalidLoggerTypeArgumentException(
                "Invalid logger type passed: '{}'".format(argument)
            )


class Warn(LoggerEntry):
    pass


class RoleUpdate(LoggerEntry):
    pass


class Mute(LoggerEntry):
    pass


class Unmute(LoggerEntry):
    pass


class Kennel(LoggerEntry):
    pass


class Unkennel(LoggerEntry):
    pass


class JoinLeave(LoggerEntry):
    pass


class CommandUsed(LoggerEntry):
    pass


class Ban(LoggerEntry):
    pass


class Unban(LoggerEntry):
    pass


class Notify(LoggerEntry):
    pass


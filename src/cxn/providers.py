import importlib
import re
import socket
from abc import ABC, abstractmethod
from typing import ClassVar, Dict, Type
from urllib.parse import urlparse

from packaging import requirements, version

regex = re.compile(
    r"^(?P<scheme>[a-zA-Z][a-zA-Z\d+\-.]*://)"
    r"(?:(?P<username>[^:@]+)(?::(?P<password>[^@]*))?@)?"
    r"(?P<host>[^:/]+)"
    r"(?::(?P<port>\d{1,5}))?"
    r"(?P<path>/[^?]*)?"
    r"(\?(?P<query>.*))?$"
)


class RegistryMeta(type):
    _instances: ClassVar[Dict] = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class Registry(metaclass=RegistryMeta):
    def __init__(self):
        self.providers: Dict[str, Type[Provider]] = {}

    def register(self, name: str, cls):
        if name in self.providers:
            raise ValueError(f"Provider '{name}' is already registered.")
        self.providers[name] = cls

    def get(self, name: str):
        try:
            cls = self.providers[name]
            return cls
        except KeyError as e:
            raise ValueError(f"Provider '{name}' is not registered.") from e


registry = Registry()


def register(name: str):
    def wrap(cls):
        registry.register(name, cls)
        return cls

    return wrap


class Provider(ABC):
    def __init__(self, url):
        self.uri = self._validate_url(url)
        self.module = self._load_required_module()

    @classmethod
    def _validate_url(cls, url):
        if not regex.match(url):
            raise ValueError("Invalid URL format")

        parse_result = urlparse(url)

        if not parse_result.scheme:
            raise ValueError("URL must include a scheme")

        if parse_result.scheme not in cls.schemas:
            message = (
                f"Protocol {parse_result.scheme} is not supported "
                f"by {cls.require} package"
            )
            raise ValueError(message)

        hostname = parse_result.hostname
        if not hostname or len(hostname) > 253:  # noqa: PLR2004
            raise ValueError(f"Invalid hostname: {hostname}")

        if parse_result.port and not (
            1 <= parse_result.port <= 65535  # noqa: PLR2004
        ):
            raise ValueError(f"Invalid port: {parse_result.port}")

        return parse_result

    def _load_required_module(self):
        requirement = requirements.Requirement(self.require)
        module_name = requirement.name

        try:
            module = importlib.import_module(module_name)
        except ImportError as e:
            raise ImportError(
                f"Required module '{module_name}' is not installed. Error: {e}"
            ) from e
        module_version = getattr(module, "__version__", None)
        if not module_version:
            raise ImportError(
                f"Unable to determine version of the '{module_name}' module."
            )

        module_version = version.parse(module_version)
        if not requirement.specifier.contains(module_version):
            raise ImportError(
                f"Module '{module_name}' version {module_version} does not "
                f"satisfy the requirement '{self.require}'."
            )

        return module

    @property
    @abstractmethod
    def require(self): ...

    @property
    @abstractmethod
    def schemas(self): ...

    @abstractmethod
    def connection(self): ...


@register("psycopg")
class PsycopgProvider(Provider):
    require = "psycopg"
    schemas = ("postgresql",)

    @property
    def connection(self):
        state = True
        try:
            self.module.connect(self.uri.geturl())
        except self.module.OperationalError:
            state = False
        return state


@register("kombu")
class KombuProvider(Provider):
    require = "kombu"
    schemas = ("amqp",)

    @property
    def connection(self):
        state = True
        try:
            connection = self.module.Connection(self.uri.geturl())
            connection.connect()
            connection.release()
        except socket.error:  # noqa: UP024
            state = False
        return state


@register("redis")
class RedisProvider(Provider):
    require = "redis"
    schemas = ("redis",)

    @property
    def connection(self):
        try:
            connection = self.module.from_url(self.uri.geturl())
            state = connection.ping()
        except self.module.exceptions.ConnectionError:
            state = False
        return state

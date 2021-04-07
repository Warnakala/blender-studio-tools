from __future__ import annotations
from typing import Union, Tuple, Dict, Any, Optional
from dataclasses import dataclass, asdict, field
from .gazu import gazu
from .logger import ZLoggerFactory

logger = ZLoggerFactory.getLogger(name=__name__)


class ZSession:

    """
    Class that will be instanced to blezou addon preferences.
    It's used to authenticate user against backend.
    If instance gets deleted authentication will be lost.
    """

    def __init__(self, email: str = "", passwd: str = "", host: str = "") -> None:
        self._email = email
        self._passwd = passwd
        self._host = self.get_host_api_url(host)
        self._session: ZSessionInfo = ZSessionInfo()

        if self._host:
            gazu.client.set_host(self._host)

    def start(self) -> Optional[ZSessionInfo]:
        # clear all data
        gazu.cache.disable()
        gazu.cache.clear_all()

        # enable cache
        gazu.cache.enable()

        if not self._is_host_up():
            return None

        if not self._login():
            return None

        logger.info("Session started with user: %s" % self.email)
        return self._session

    def end(self) -> bool:
        if not self._session.login:
            logger.info("Failed to log out. Session not started yet.")
            return False

        self._session = ZSessionInfo(gazu.log_out())  # returns empty dict
        gazu.cache.clear_all()
        logger.info("Session ended.")
        return True

    def _is_host_up(self) -> bool:
        if gazu.client.host_is_up():
            logger.info("Host is up and running at: %s" % self.host)
            return True
        else:
            logger.error("Failed to reach host at: %s" % self.host)
            return False

    def _login(self) -> bool:
        try:
            session_dict = gazu.log_in(self._email, self._passwd)
        except:
            logger.exception("Failed to login. Credentials maybe incorrect?")
            return False

        logger.info("Login was succesfull")
        self._session.update(session_dict)
        return True

    def is_auth(self) -> bool:
        return self._session.login

    def set_credentials(self, email: str, passwd: str) -> None:
        self.email = email
        self.passwd = passwd

    def get_config(self) -> Dict[str, str]:
        return {
            "email": self.email,
            "passwd": self._passwd,
            "host": self.host,
        }  # TODO: save those in ZSessionInfo

    def set_config(self, config: Dict[str, str]) -> None:
        email = config.get("email", "")
        passwd = config.get("passwd", "")
        host = config.get("host", "")
        self.email = email
        self._passwd = passwd
        self.host = host

    def valid_config(self) -> bool:
        if "" in {self.email, self._passwd, self.host}:
            return False
        else:
            return True

    @classmethod
    def get_host_api_url(cls, url: str) -> str:
        if not url:
            return ""
        if url[-4:] == "/api":
            return url
        if url[-1] == "/":
            url = url[:-1]
        return url + "/api"

    @property
    def host(self) -> str:
        return self._host

    @host.setter
    def host(self, host: str) -> None:
        host_backup = self._host
        if host:
            self._host = self.get_host_api_url(host)
            gazu.client.set_host(self._host)
            if not gazu.client.host_is_valid():
                logger.error("Host is not valid: %s" % host)
                self._host = host_backup
                gazu.client.set_host(self._host)

    @property
    def email(self) -> str:
        return self._email

    @email.setter
    def email(self, email: str) -> None:
        self._email = email

    @property
    def session(self) -> ZSessionInfo:
        return self._session

    def __del__(self) -> None:
        self.end()


@dataclass
class ZSessionInfo:
    login: bool = False
    user: Dict[str, str] = field(default_factory=dict)
    ldap: bool = False
    access_token: str = ""
    refresh_token: str = ""

    def update(self, data_dict: Dict[str, Union[str, Dict[str, str]]]) -> None:
        for k, v in data_dict.items():
            setattr(self, k, v)

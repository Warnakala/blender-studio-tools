from typing import Union, Tuple, Dict, Any
from .gazu import gazu
from .logger import ZLoggerFactory

logger = ZLoggerFactory.getLogger(__name__)


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
        self._session: Dict[str, Any] = {}

        if self._host:
            gazu.client.set_host(self._host)

    def start(self) -> Union[bool, Dict[str, Any]]:
        # clear all data
        gazu.cache.disable()
        gazu.cache.clear_all()

        # enable cache
        gazu.cache.enable()

        if not self._is_host_up():
            return False

        session = self._login()
        if not session:
            return False

        logger.info("Session started with user: %s" % self.email)
        return session

    def end(self) -> Union[Dict, bool]:
        try:
            self._session = gazu.log_out()  # returns empty dict
        except:
            logger.info("Faild to log out. Session not started yet? ")
            return False

        gazu.cache.clear_all()
        logger.info("Session ended.")
        return self._session

    def _is_host_up(self) -> bool:
        if gazu.client.host_is_up():
            logger.info("Host is up and running at: %s" % self.host)
            return True
        else:
            logger.exception("Failed to reach host at: %s" % self.host)
            return False

    def _login(self) -> Dict[str, Any]:
        try:
            self._session = gazu.log_in(self._email, self._passwd)  # returns dict
        except:
            logger.exception("Failed to login. Credentials maybe incorrect?")
            return {}
        logger.info("Login was succesfull")
        return self._session

    def is_auth(self) -> bool:
        if self._session:
            return True
        else:
            return False

    def set_credentials(self, email: str, passwd: str) -> None:
        self.email = email
        self.passwd = passwd

    def get_config(self) -> Dict[str, str]:
        return {"email": self.email, "passwd": self._passwd, "host": self.host}

    def set_config(self, config: Dict[str, str]) -> None:
        email = config.get("email", "")
        passwd = config.get("passwd", "")
        host = config.get("host", "")
        self.email = email
        self._passwd = passwd
        self.host = host

    def valid_config(self) -> bool:
        if "" in {elf.email, self._passwd, self.host}:
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
                logger.exception("Host is not valid: %s" % host)
                self._host = host_backup
                gazu.client.set_host(self._host)

    @property
    def email(self) -> str:
        return self._email

    @email.setter
    def email(self, email: str) -> None:
        self._email = email

    @property
    def session(self) -> Dict[str, Any]:
        return self._session

    def __del__(self) -> None:
        self.end()
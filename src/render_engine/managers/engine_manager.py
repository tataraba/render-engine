import dataclasses

from jinja2 import Environment

from ..engine import engine


@dataclasses.dataclass
class EngineManager:
    engine: Environment = engine
    SITE_VARS: dict = dataclasses.field(default_factory=dict)
    SITE_TITLE: dataclasses.InitVar[str] = "Untitled Site"
    SITE_URL: dataclasses.InitVar[str] = "http://localhost:8000/"
    DATETIME_FORMAT: dataclasses.InitVar[str] = "%d %b %Y %H:%M %Z"

    def __post_init__(self, SITE_TITLE, SITE_URL, DATETIME_FORMAT):
        self.update_site_vars(
            SITE_TITLE=SITE_TITLE,
            SITE_URL=SITE_URL,
            DATETIME_FORMAT=DATETIME_FORMAT,
        )

    def update_site_vars(self, **kwargs) -> None:
        self.SITE_VARS.update(**kwargs)
        self.engine.globals.update(self.SITE_VARS)

    @property
    def settings(self):
        return self.SITE_VARS
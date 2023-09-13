import dataclasses
import typing
from collections import defaultdict

import pluggy

_PROJECT_NAME = "render_engine"
hook_spec = pluggy.HookspecMarker(project_name=_PROJECT_NAME)


class SiteSpecs:
    """Plugin hook specifications for the Site class"""
    default_settings: dict[str, typing.Any]
    
    @hook_spec
    def add_default_settings(
        self,
        site: "Site",
    ) -> None:
        """Add default settings to the site"""

    @hook_spec
    def pre_build_site(
        self,
        site: "Site",
        settings: dict[str, typing.Any],
    ) -> None:
        """Steps Prior to Building the site"""

    @hook_spec
    def post_build_site(
        self,
        site: "Site",
        settings: dict[str, typing.Any],
    ) -> None:
        """Build After Building the site"""

    @hook_spec
    def render_content(
        self,
        page: "page",
        settings: dict[str, typing.Any],
    ) -> None:
        """
        Augments the content of the page before it is rendered as output.
        """

    @hook_spec
    def post_render_content(
        self,
        page : "page",
        settings: dict[str: typing.Any]):
        """
        Augments the content of the page before it is rendered as output.
        """

    @hook_spec
    def pre_build_collection(
        self,
        collection: "Collection",
        settings: dict[str, typing.Any],
    ) -> None:
        """Steps Prior to Building the collection"""

    @hook_spec
    def post_build_collection(
        self,
        site: "Site",
        settings: dict[str, typing.Any],
    ) -> None:
        """Build After Building the collection"""


@dataclasses.dataclass
class PluginsManager:
    """Manages site plugins
    
    Attributes:
        _pm: PluginManager object

    """
    _pm: pluggy.PluginManager = pluggy.PluginManager("render_engine")
    PLUGIN_SETTINGS: defaultdict = dataclasses.field(default_factory=lambda: defaultdict(dict))
    
    def __post_init__(self):
        self._pm.add_hookspecs(SiteSpecs)
        
    def add(self, *plugins, **settings: dict[str, typing.Any]) -> None:
        """Register plugins with the site
        
        parameters:
            plugins: list of plugins to register
            settings: settings to pass into the plugins
                settings keys are the plugin names as strings.
        """
        
        for plugin in plugins:
            self._pm.register(plugin)        
            self.PLUGIN_SETTINGS[plugin.__name__] = getattr(plugin, 'default_settings', {})

        self._pm.hook.add_default_settings(
            site=self,
            custom_settings=settings,
        ) 
        self.PLUGIN_SETTINGS['plugins'].update(**settings)

    @property
    def all(self) -> set:
        return self._pm.get_plugins()

    @property
    def settings(self) -> dict[str, typing.Any]:
        return self.PLUGIN_SETTINGS
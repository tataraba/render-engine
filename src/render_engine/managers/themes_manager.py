import dataclasses
import logging
import pathlib
import shutil
import typing

from jinja2 import Environment
from ..utils.themes import Theme


@dataclasses.dataclass
class ThemesManager:
    """
    Processes the theme for the site.
    The theme manager is responsible for loading the jinja2 environment and copying static files.

    Attributes:
        engine: Jinja2 Environment used to render pages
        output_path: path to write rendered content
        static_paths: list of paths for static folders. 
            This will get copied to the output folder. 
            Folders are recursive.
    """

    output_path: str = "output"
    static_paths: set[str|pathlib.Path] = dataclasses.field(default_factory=set)
    THEME_SETTINGS: dict[str, typing.Any] = dataclasses.field(default_factory=dict)

    def register_themes(self, engine, *themes: Theme, settings: dict|None = None):
        """
        Register a theme.

        Args:
            *themes: Theme objects to register
        """
        for theme in themes:
            logging.info(f"Registering theme: {theme}")
            engine.loader.loaders.insert(0, theme.loader)
            self.static_paths.add(theme.static_dir)
            logging.info("adding theme settings")
            

        
    def _render_static(self) -> None:
        """Copies a Static Directory to the output folder"""
        for static_path in self.static_paths:
            logging.debug(f"Copying Static Files from {static_path}")
            if pathlib.Path(static_path).exists():
                shutil.copytree(
                    static_path,
                    pathlib.Path(self.output_path) / pathlib.Path(static_path).name,
                    dirs_exist_ok=True
                )

    @property
    def settings(self):
        return self.THEME_SETTINGS
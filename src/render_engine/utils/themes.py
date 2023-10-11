import dataclasses
import logging
import pathlib
import shutil

from jinja2 import BaseLoader, Environment


@dataclasses.dataclass
class Theme:
    loader: BaseLoader
    static_dir: str|pathlib.Path
    filters: dict[str, callable]

class ThemeManager:
    """
    Processes the theme for the site.
    The theme manager is responsible for loading the jinja2 environment and copying static files.

    Attributes:
        engine: Jinja2 Environment used to render pages
        output_path: path to write rendered content
        static_paths: set of filepaths for static folders.
            This will get copied to the output folder.
            Folders are recursive.

    """
    engine: Environment
    output_path: str = "output"
    static_paths: set[str|pathlib.Path] = {"static"}

    def register_themes(self, *themes: Theme):
        """
        Register a theme.

        Args:
            *themes: Theme objects to register
        """
        for theme in themes:
            logging.info(f"Registering theme: {theme}")
            self.engine.loader.loaders.insert(0, theme.loader)
            self.static_paths.add(theme.static_dir)
            self.engine.filters.update(theme.filters)

    def _render_static(self) -> None:
        """Copies a Static Directory to the output folder"""
        for static_path in self.static_paths:
            logging.debug(f"Copying Static Files from {static_path}")
            if not static_path:
                continue
            if pathlib.Path(static_path).exists():
                shutil.copytree(
                    static_path,
                    pathlib.Path(self.output_path) / pathlib.Path(static_path).name,
                    dirs_exist_ok=True
                )
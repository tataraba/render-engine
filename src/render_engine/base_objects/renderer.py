import dataclasses
import logging
import pathlib

from rich.progress import Progress

from ..collection import Collection
from ..managers.engine_manager import EngineManager
from ..managers.plugins_manager import PluginsManager
from ..managers.routes_manager import RoutesManager
from ..managers.themes_manager import ThemesManager
from ..page import BasePage


@dataclasses.dataclass
class Renderer:  

    engine_manager: "EngineManager" = dataclasses.field(default_factory=EngineManager)
    plugins: "PluginsManager" = dataclasses.field(default_factory=PluginsManager)
    themes: "ThemesManager" = dataclasses.field(default_factory=ThemesManager)
    routes_manager: "RoutesManager" = dataclasses.field(default_factory=RoutesManager)
    partial: bool = False
  

    @property
    def settings(self):
        return {
            "SITE_VARS": self.engine_manager.SITE_VARS,
            "PLUGINS_SETTINGS": self.plugins.PLUGIN_SETTINGS,
            "THEMES_SETTINGS": self.themes.THEME_SETTINGS,
        }
    
    
    def _render_output(
        self,
        route: str,
        page: BasePage
    ) -> int:
        """writes the page object to disk"""
        path = (
            pathlib.Path(self.themes.output_path)
            / pathlib.Path(route)
            / pathlib.Path(page.path_name)
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        page.rendered_content = page._render_content(engine=self.engine_manager.engine)
        self.plugins._pm.hook.post_render_content(page=page)
        return path.write_text(page.rendered_content)

    def _render_partial_collection(self, collection: Collection) -> None:
        """Iterate through the Changed Pages and Check for Collections and Feeds"""
        for entry in collection._generate_content_from_modified_pages():
            for route in collection.routes:
                self._render_output(route, entry)

        if collection.has_archive:
            for archive in collection.archives:
                logging.debug("Adding Archive: %s", archive.__class__.__name__)

                self._render_output(collection.routes[0], archive)

        if hasattr(collection, "Feed"):
            self._render_output("./", collection.feed)

    def _render_full_collection(self, collection: Collection) -> None:
        """Iterate through Pages and Check for Collections and Feeds"""

        for entry in collection:
            self.plugins._pm.hook.render_content(page=entry)
            for route in collection.routes:
                self._render_output(route, entry)

        if collection.has_archive:
            for archive in collection.archives:
                logging.debug("Adding Archive: %s", archive.__class__.__name__)

                for route in collection.routes:
                    self._render_output(collection.routes[0], archive)

        if hasattr(collection, "Feed"):
            self._render_output("./", collection.feed)

    def render(self) -> None:
        """
        Render all pages and collections.

        These are pages and collections that have been added to the site using 
        the [`Site.page`][src.render_engine.Site.page] 
        and [`Site.collection`][src.render_engine.Site.collection] methods.

        Render should be called after all pages and collections have been added to the site.

        You can choose to call it manually in your file or use the CLI command [`render-engine build`][src.render_engine.cli.build]
        """

        with Progress() as progress:

            pre_build_task = progress.add_task("Loading Pre-Build Plugins", total=1)
            self.plugins._pm.hook.pre_build_site(
                site=self,
                settings=self.plugins.PLUGIN_SETTINGS,
                ) #type: ignore

            # loading settings into engine
            self.engine_manager.engine.globals.update(self.settings)
           
            # Parse Route List
            task_add_route = progress.add_task(
                "[blue]Adding Routes", total=len(self.routes_manager.route_list)
            )

            self.themes._render_static()
            self.engine_manager.engine.globals["site"] = self
            self.engine_manager.engine.globals["routes"] = self.routes_manager.route_list

            for slug, entry in self.routes_manager.route_list.items():
                progress.update(
                    task_add_route, description=f"[blue]Adding[gold]Route: [blue]{slug}"
                )
                if isinstance(entry, BasePage):
                    if getattr(entry, "collection", None):
                        self.plugins._pm.hook.render_content(Page=entry, settings=self.plugins.PLUGIN_SETTINGS)
                    for route in entry.routes:
                        progress.update(
                            task_add_route,
                            description=f"[blue]Adding[gold]Route: [blue]{entry._slug}",
                        )
                        self._render_output(route, entry)

                if isinstance(entry, Collection):
                    if self.partial:
                        self._render_partial_collection(entry)
                    else:
                        self._render_full_collection(entry)
            progress.add_task("Loading Post-Build Plugins", total=1)
            self.plugins._pm.hook.post_build_site(
                site=self,
                settings=self.plugins.PLUGIN_SETTINGS,
            )
            progress.update(pre_build_task, advance=1)
   
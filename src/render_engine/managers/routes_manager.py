import dataclasses

from ..collection import Collection
from ..page import Page


@dataclasses.dataclass
class RoutesManager:
    route_list: dict[str, Page|Collection] = dataclasses.field(default_factory=dict)
    
    def collection(self, Collection: type[Collection]) -> Collection:
        """
        Add the collection to the route list to be rendered later.

        This is the primary way to add a collection to the site and 
        can either be called on an uninstantiated class or on the class definition as a decorator.

        In most cases. You should use the decorator method.

        ```python
        from render_engine import Site, Collection

        site = Site()

        @site.collection # works
        class Pages(Collection):
            pass


        class Posts(Collection):
            pass

        site.collection(Posts) # also works
        ```
        """
        _Collection = Collection()
        plugins = [*self.plugins, *getattr(_Collection, "plugins", [])]
        
        for plugin in getattr(_Collection, 'ignore_plugins', []):
            plugins.remove(plugin)
        _Collection.register_plugins(plugins)

        self._pm.hook.pre_build_collection(
            collection=_Collection,
            settings=self.site_settings.get('plugins', {}),
        ) #type: ignore
        self.route_list[_Collection._slug] = _Collection
        return _Collection


    def page(self, Page: Page) -> Page:
        """
        Add the page to the route list to be rendered later.
        Also remaps `title` in case the user wants to use it in the template rendering.

        This is the primary way to add a page to the site and can either be called
        on an uninstantiated class or on the class definition as a decorator.

        In most cases. You should use the decorator method.

        ```python

        from render_engine import Site, Page

        site = Site()

        @site.page # works
        class Home(Page):
            pass

        class About(Page):
            pass

        site.page(About) # also works
        ```
        """
        page = Page()
        page.title = page._title # Expose _title to the user through `title`

        # copy the plugin manager, removing any plugins that the page has ignored
        page._pm = self._pm

        for plugin in getattr(page, 'ignore_plugins', []):
            page._pm.unregister(plugin)

        self.route_list[getattr(page, page._reference)] = page


from managers import PluginsManager
import pluggy

_PROJECT_NAME = "render_engine"
hook_impl = pluggy.HookimplMarker("render_engine")
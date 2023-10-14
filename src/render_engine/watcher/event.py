
import threading
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler, ThreadingHTTPServer
from multiprocessing import Process

from rich.console import Console
from watchdog.events import FileSystemEvent, RegexMatchingEventHandler
from watchdog.observers import Observer

from render_engine import Site

console = Console()




# def server_func(server_address: tuple[int, int], directory: str):

#     class _RequestHandler(SimpleHTTPRequestHandler):
#         def __init__(self, *args, **kwargs):
#             super().__init__(*args, directory=directory, **kwargs)

#     def _httpd():
#         console.print(f"Servin from server func: '{directory}' on http://{server_address[0]}:{server_address[1]}")
#         httpd = HTTPServer(server_address, _RequestHandler)
#         httpd.serve_forever()

#     return _httpd


def spawn_server(server_address: tuple[int, int], directory: str) -> ThreadingHTTPServer:

    class _RequestHandler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=directory, **kwargs)

    def _httpd() -> ThreadingHTTPServer:
        console.print(f"Servin from server func: '{directory}' on http://{server_address[0]}:{server_address[1]}")
        return ThreadingHTTPServer(server_address, _RequestHandler)
    return _httpd()

class RegExHandler(RegexMatchingEventHandler):
    """
    Initializes a handler that matches given regexes with the
    paths that are associated with the given events.

    Args:
        render_engine_server (HTTPServer): Instance of render engine server.
        server_address (tuple[int, int]): The server address.
        app (Site): The Site instance of the application.
        console (Console, optional): The Rich console for pretty printing of console messages. Defaults to Console().
        patterns (list[str] | None, optional): Regexes to allow matching event paths. Defaults to None.
        ignore_patterns (list[str] | None, optional): Regexes to ignore matching event paths. Defaults to None.
        *args: Variable length argument list.
        **kwargs: Arbitrary keyword arguments.
    """
    def __init__(
        self,
        server_address: tuple[int, int],
        dir_to_serve: str,
        app: Site,
        patterns: [list[str] | None] = None,
        ignore_patterns: [list[str] | None] = None,
        *args,
        **kwargs
    ):
        self.p = None
        # self.server_func = server_func(server_address, dir_to_serve)
        self.server_threaded = spawn_server(server_address, dir_to_serve)
        self.dir_to_serve = dir_to_serve,
        self.server_address = server_address
        self.app = app
        self.patterns = patterns
        self.ignore_patterns = ignore_patterns
        super().__init__(
            *args,
            regexes=patterns,
            ignore_regexes=ignore_patterns,
            **kwargs
        )


    def start_server(self):
        console.print("[bold green]Starting threaded server[/bold green]")
        self._thread = threading.Thread(target=self.server_threaded.serve_forever)
        self._thread.start()

    def stop_server(self):
        console.print("[bold red]Stopping server[/bold red]")
        self.server_threaded.shutdown()
        self.server_threaded.server_close()
        self._thread.join()

    def rebuild(self):
        console.print(f"[bold pink]Reloading and Rebuilding site...[/bold pink]")
        # self.stop_server()
        self.app.render()
        # self.start_server()

    def on_any_event(self, event: FileSystemEvent):
        print("HERERERERE")
        if event.is_directory:
            return None
        if event.event_type == "modified":

            self.rebuild()


    def watch(self):

        console.print(f'[yellow]Serving {self.app.output_path}[/yellow]')

        self.start_server()
        observer = Observer()
        observer.schedule(self, ".", recursive=True)
        self.start_server()
        observer.start()

        try:
            while True:
                print("waiting")
                time.sleep(1)
        except KeyboardInterrupt:
            console.print("watcher terminated by keystroke")
            observer.stop()
            self.stop_server()
        observer.join()
        console.print('[bold red]FIN![/bold red]')



import threading
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler, ThreadingHTTPServer
from multiprocessing import Process

from rich.console import Console
from watchdog.events import FileSystemEvent, RegexMatchingEventHandler
from watchdog.observers import Observer

from render_engine import Site

console = Console()




def server_func(server_address: tuple[int, int], directory: str):

    class _RequestHandler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=directory, **kwargs)

    def _httpd():
        console.print(f"Servin from server func: '{directory}' on http://{server_address[0]}:{server_address[1]}")
        httpd = HTTPServer(server_address, _RequestHandler)
        httpd.serve_forever()

    return _httpd




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
        self.server_func = server_func(server_address, dir_to_serve)
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

    def show_types(self):
        print(f"SHOW TYPES: {type(self.server_func)=} and {type(server_func)=}")

    def stop_server(self):
        if self.p:
            console.print("[bold red]Stopping server[/bold red]")
            self.p.terminate()
            self.p = None

    def start_server(self):
        if self.p:
            self.stop_server()

        console.print("[bold green]Starting server[/bold green]")
        self.p = Process(target=self.server_func)
        self.p.start()
        print("thread started")

    def rebuild(self):
        console.print(f"[bold green]Rendering site...[/bold green]")
        self.app.render()

    def on_any_event(self, event: FileSystemEvent):
        if event.is_directory:
            return None
        if event.event_type == "modified":
            self.rebuild()



    def watch(self):
        console.print(f'[yellow]Serving {self.app.output_path}[/yellow]')

        self.start_server()
        observer = Observer()
        observer.schedule(self, ".", recursive=True)
        observer.start()

        try:
            while True:
                print("waiting")
                time.sleep(1)
        except KeyboardInterrupt:
            console.print("watcher terminated by keystroke")
            observer.stop()
        observer.join()
        console.print('[bold red]FIN![/bold red]')

#



import threading
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler, ThreadingHTTPServer

from rich.console import Console
from watchdog.events import FileSystemEvent, RegexMatchingEventHandler
from watchdog.observers import Observer

from render_engine import Site


class RenderEngineServer(SimpleHTTPRequestHandler):
    def __init__(self, directory: str, *args, **kwargs):
        self.directory = directory
        super().__init__(*args, directory=directory, **kwargs)

        # self.server.shutdown()

class RegExHandler(RegexMatchingEventHandler):
    """
    Initializes a handler that matches given regexes with the
    paths that are associated with the given events.

    Args:
        render_engine_server (RenderEngineServer): Instance of render engine server.
        server_address (tuple[int, int]): The server address.
        app (Site): The Site instance of the application.
        console (Console, optional): The console. Defaults to Console().
        patterns (list[str] | None, optional): Regexes to allow matching event paths. Defaults to None.
        ignore_patterns (list[str] | None, optional): Regexes to ignore matching event paths. Defaults to None.
        *args: Variable length argument list.
        **kwargs: Arbitrary keyword arguments.
    """
    def __init__(
        self,
        render_engine_server: HTTPServer,
        server_address: tuple[int, int],
        app: Site,
        console: Console = Console(),
        patterns: [list[str] | None] = None,
        ignore_patterns: [list[str] | None] = None,
        *args,
        **kwargs
    ):
        self.render_engine_server = render_engine_server
        self.server_address = server_address
        self.app = app
        self.console = console
        self.patterns = patterns
        self.ignore_patterns = ignore_patterns
        super().__init__(
            *args,
            regexes=patterns,
            ignore_regexes=ignore_patterns,
            **kwargs
        )
    def on_any_event(self, event: FileSystemEvent):
        if event.is_directory:
            return None

        elif event.event_type == "modified":
            def shutdown_server():
                self.render_engine_server.shutdown()
                self.render_engine_server.close_request()
                self.console.print("Server has been shutdown.")
                self.app.render()
                self.console.print("[yellow]Watching for file system changes...[/yellow]")
            self.console.print(f'File [bold green] {event.src_path} [/bold green] has been modified.')
            self.console.print(f"Modification on server: {self.render_engine_server.server_address}")

            shutdown_thread = threading.Thread(target=shutdown_server)
            shutdown_thread.start()

            self.console.print("Server has been shutdown.")
            self.render_engine_server.server_close()
            self.console.print('Server has been closed.\n[green]Rendering site again ...[/green]')
            self.app.render()

            self.httpd = ThreadingHTTPServer(self.server_address, RenderEngineServer)
            threading.Thread(target=self.httpd.serve_forever).start()




class Watcher:
    """
    Watcher class for monitoring file system changes.

    Args:
        handler (RegExHandler): The handler for matching regexes with events.
        app: The application instance.
        directory (str): The directory to watch.

    Attributes:
        observer (Observer): The file system observer.
        handler (RegExHandler): The handler for matching regexes with events.
        app: The application instance.
        directory (str): The directory to watch.
        console: Rich console for pretty printing to console.

    Methods:
        run(): Starts the file system observer and begins watching for changes.
    """
    def __init__(self, handler: RegExHandler, app, directory=".",):
        self.observer = Observer()
        self.handler = handler
        self.app = app
        self.directory = directory
        self.console = Console()


    def run(self):
        self.observer.schedule(self.handler, self.directory, recursive=True)
        self.observer.start()

        self.console.print('[yellow]Watching for file system changes...[/yellow]')
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.console.print("watcher terminated by keystroke")
            self.observer.stop()
        self.observer.join()
        self.console.print('[bold red]FIN![/bold red]')


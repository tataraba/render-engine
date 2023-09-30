import logging
import socketserver
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

logger = logging.getLogger(__name__)


class Server(SimpleHTTPRequestHandler):
    def __init__(self, directory: str, *args, **kwargs):
        self.directory = directory
        super().__init__(*args, directory=directory, **kwargs)


class RenderEngineHandler(FileSystemEventHandler):

    def __init__(
        self,
        server: HTTPServer,
        request_handler: SimpleHTTPRequestHandler,
        server_address: tuple[int, int],
        # directory_to_watch: str | None
    ):
        self.server = server
        self.request_handler = request_handler
        self.server_address = server_address
        # self.directory_to_watch = directory_to_watch

    def start_server(self):
        httpd = HTTPServer(self.server_address, self.request_handler)
        httpd.serve_forever()

    def on_any_event(self, event: FileSystemEvent):
        logger.info(f'File {event.src_path} has been modified.')
        print(f'File {event.src_path} has been modified.')

        self.server.shutdown()
        time.sleep(1)
        logger.info('Server has been shutdown.')
        self.server.server_close()
        logger.info('Server has been closed. Attempting to reload...')
        socketserver.TCPServer(("localhost", 8000), self.request_handler)
        self.start_server()


    def watch(self):
        observer = Observer()
        observer.schedule(self, ".", recursive=True)
        observer.start()
        print('Watching for file system changes...')
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()

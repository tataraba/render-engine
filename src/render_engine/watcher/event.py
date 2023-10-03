import logging
import sys
import threading
import time
from typing import Any
from render_engine import Site
from watchdog.events import FileSystemEventHandler, FileSystemEvent
from watchdog.observers import Observer
from http.server import HTTPServer, SimpleHTTPRequestHandler, ThreadingHTTPServer
import socketserver


logger = logging.getLogger(__name__)


class RenderEngineServer(SimpleHTTPRequestHandler):
    def __init__(self, directory: str, *args, **kwargs):
        self.directory = directory
        super().__init__(*args, directory=directory, **kwargs)

        self.server.shutdown()



class RenderEngineFileEventHandler(FileSystemEventHandler):

    def __init__(
        self,
        server: HTTPServer,
        server_address: tuple[int, int],
        app: Site,

    ):
        self.server = server
        self.server_address = server_address
        self.app = app


    def on_any_event(self, event: FileSystemEvent):
        if event.is_directory:
            return None



        elif event.event_type == "modified":

            def shutdown_server():
                self.server.shutdown()
                self.server.close_request()
                logger.info("server has been shutdown.")
                self.app.render()

            logger.info(f'File {event.src_path} has been modified.')
            print(f"Modification on server: {self.server}")

            shutdown_thread = threading.Thread(target=shutdown_server)
            shutdown_thread.start()

            # This part is not working as expected

            logger.info("server has been shutdown.")
            time.sleep(1)
            logger.info(f'Server has been shutdown.')
            self.server.server_close()
            self.app.render()
            logger.info(f'Server has been closed. Attempting to reload...')
            # Create a new instance of ThreadingHTTPServer
            self.httpd = ThreadingHTTPServer(
                self.server_address, RenderEngineServer
            )
            # Start the new server instance in a separate thread
            threading.Thread(target=self.httpd.serve_forever).start()



class Watcher:
    def __init__(self, handler: RenderEngineFileEventHandler, app, directory=".",):
        self.observer = Observer()
        self.handler = handler
        self.app = app
        self.directory = directory



    def run(self):
        server = HTTPServer(("localhost", 8000), RenderEngineServer)
        handler = RenderEngineFileEventHandler(server=self.handler.server, server_address=("localhost", 8000), app=self.app)
        self.observer.schedule(handler, self.directory, recursive=True)
        self.observer.start()

        print('Watching for file system changes...')
        try:
            while True:
                print("is this true?")
                time.sleep(4)
        except KeyboardInterrupt:
            print("watcher terminated by keystroke")
            self.observer.stop()
            # sys.exit(0)
        self.observer.join()
        print('Watcher terminated')


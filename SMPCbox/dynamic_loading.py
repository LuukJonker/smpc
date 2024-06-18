import sys
import os
import time
import importlib.util
import inspect
from threading import Thread
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from SMPCbox.AbstractProtocol import AbstractProtocol
from typing import Callable
from types import ModuleType
from dataclasses import dataclass
from enum import Enum

sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), ".."))


class ChangeType(Enum):
    """The type of update that has occurred in a module."""

    LOADED = 1
    MODIFIED = 2
    NEW = 3


@dataclass
class ModuleInfo:
    """Data class to store information about a module."""

    module: ModuleType
    change_type: ChangeType
    changed: bool = True


class ClassWatcher:
    """A class to watch a directory for changes in Python files and give back the updated classes."""

    def __init__(
        self,
        path_to_watch: str,
        callback: Callable[["ClassWatcher"], None],
        verbose: bool = False,
    ):
        """
        Initialize the ClassWatcher with a path to watch.

        :param path_to_watch: Path to the directory to watch for changes.
        """
        self.module_cache: dict[str, ModuleInfo] = {}
        self.verbose = verbose
        self.callback = callback

        self.path_to_watch = os.path.abspath(path_to_watch)
        if not os.path.isdir(self.path_to_watch):
            raise ValueError(f"The path {self.path_to_watch} is not a valid directory.")
        sys.path.insert(0, self.path_to_watch)
        self._start_watching()

    def _start_watching(self):
        """
        Start watching the directory for changes in a separate thread.
        """
        event_handler = FileChangeHandler(
            self.module_cache, self.path_to_watch, self._run_callback, self.verbose
        )
        observer = Observer()
        observer.schedule(event_handler, path=self.path_to_watch, recursive=True)
        observer_thread = Thread(target=self._run_observer, args=(observer,))
        observer_thread.daemon = True
        observer_thread.start()

        if self.verbose:
            print(f"Watching directory: {self.path_to_watch}")

    def _run_observer(self, observer):
        """
        Run the observer to watch for file system events.

        :param observer: The watchdog observer instance.
        """
        observer.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()

    def _get_module_name(self, filepath):
        """
        Get the module name from a file path.

        :param filepath: Path to the Python file.
        :return: Module name derived from the file path.
        """
        relative_path = os.path.relpath(filepath, self.path_to_watch)
        return os.path.splitext(relative_path.replace(os.sep, "."))[0]

    def get_classes(self):
        """
        Get a list of classes from the loaded modules.

        :return: List of tuples with class names and class objects.
        """
        classes: list[tuple[str, type[AbstractProtocol]]] = []
        for module_name, module in self.module_cache.items():
            for name, obj in inspect.getmembers(module.module, inspect.isclass):
                if obj.__module__ == module_name:
                    classes.append((name, obj))  # type: ignore
        return classes

    def get_changed_classes(self):
        """
        Get a list of classes that have been changed.

        :return: List of tuples with class names and class objects.
        """
        changed_classes: list[tuple[str, AbstractProtocol]] = []
        for module_name, module in self.module_cache.items():
            if module.changed:
                module.changed = False
                for name, obj in inspect.getmembers(module.module, inspect.isclass):
                    if obj.__module__ == module_name:
                        changed_classes.append((name, obj))  # type: ignore
        return changed_classes

    def _run_callback(self):
        """
        Run the callback function if it is set.
        """
        if self.callback:
            self.callback(self)


class FileChangeHandler(FileSystemEventHandler):
    def __init__(
        self,
        module_cache: dict[str, ModuleInfo],
        path_to_watch: str,
        callback: Callable,
        verbose: bool = False,
    ):
        """
        Initialize the file change handler.

        :param module_cache: Dictionary to cache loaded modules.
        :param path_to_watch: Path to the directory to watch for changes.
        """
        self.module_cache = module_cache
        self.path_to_watch = path_to_watch
        self.verbose = verbose
        self.callback = callback
        self._load_existing_files()

    def _load_existing_files(self):
        """
        Load all existing Python files in the directory and its subdirectories.
        """
        for root, _, files in os.walk(self.path_to_watch):
            for filename in files:
                if filename.endswith(".py"):
                    filepath = os.path.join(root, filename)
                    self._load_module(filepath, ChangeType.LOADED, initial_load=True)

        self._run_callback()

    def on_modified(self, event):
        """
        Handle the event when a file is modified.

        :param event: File system event.
        """
        if event.src_path.endswith(".py"):
            self._reload_module(event.src_path)

    def on_created(self, event):
        """
        Handle the event when a new file is created.

        :param event: File system event.
        """
        if event.src_path.endswith(".py"):
            self._reload_module(event.src_path)

    def _load_module(self, filepath, change_type, initial_load=False):
        """
        Load a module from a file.

        :param filepath: Path to the Python file to load as a module.
        """
        module_name = self._get_module_name(filepath)
        self._add_to_sys_path(filepath)
        spec = importlib.util.spec_from_file_location(module_name, filepath)
        if spec is None or spec.loader is None:
            return
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        self.module_cache[module_name] = ModuleInfo(module, change_type)

        if self.verbose:
            print(f"Loaded module: {module_name}")

        print(f"Loaded module: {module_name}")

        if not initial_load:
            self._run_callback()

    def _reload_module(self, filepath):
        """
        Reload a module from a file.

        :param filepath: Path to the Python file to reload as a module.
        """
        module_name = self._get_module_name(filepath)
        self._add_to_sys_path(filepath)
        if module_name in self.module_cache:
            importlib.reload(self.module_cache[module_name].module)
            self.module_cache[module_name].change_type = ChangeType.MODIFIED
            self.module_cache[module_name].changed = True

            if self.verbose:
                print(f"Reloaded module: {module_name}")
            print(f"Reloaded module: {module_name}")
            self._run_callback()
        else:
            self._load_module(filepath, ChangeType.NEW)

    def _get_module_name(self, filepath):
        """
        Get the module name from a file path.

        :param filepath: Path to the Python file.
        :return: Module name derived from the file path.
        """
        relative_path = os.path.relpath(filepath, self.path_to_watch)
        return os.path.splitext(relative_path.replace(os.sep, "."))[0]

    def _add_to_sys_path(self, filepath):
        """
        Add the directory of the file to sys.path.

        :param filepath: Path to the file whose directory should be added to sys.path.
        """
        module_dir = os.path.dirname(filepath)
        if module_dir not in sys.path:
            sys.path.insert(0, module_dir)

    def _run_callback(self):
        """
        Run the callback function if it is set.
        """
        if self.callback:
            self.callback()


def callback(watcher: ClassWatcher):
    print("Classes in watched files:")
    for class_name, class_obj in watcher.get_changed_classes():
        print(f"{class_name}: {class_obj.protocol_name}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python folder_watcher.py <path_to_watch>")
        sys.exit(1)

    path_to_watch = sys.argv[1]

    watcher = ClassWatcher(path_to_watch, callback)

    while True:
        time.sleep(1)

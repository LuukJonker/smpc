from SMPCbox.main import Protocolvisualiser
from SMPCbox.dynamic_loading import ClassWatcher
import argparse


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Visualise a protocol.")
    parser.add_argument("path", type=str, help="Path to the protocol file.")
    parser.add_argument("--name", type=str, default="", help="Name of party in distributed protocol.")
    args = parser.parse_args()

    v = Protocolvisualiser(args.name)

    def callback(watcher: ClassWatcher):
        v.set_protocols({name: cls for name, cls in watcher.get_classes()})

    watcher = ClassWatcher(args.path, callback)

    v.add_atexit(watcher.stop)

    v.run_gui()

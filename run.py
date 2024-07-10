from SMPCbox.Visualiser import ProtocolVisualizer, DistributedVisualizer
from SMPCbox.DynamicLoading import ClassWatcher
import argparse
from SMPCbox.constants import QUEUE_SIZE


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Visualise a protocol.")
    parser.add_argument("path", type=str, help="Path to the protocol file.")
    parser.add_argument(
        "-d",
        "--distributed",
        action="store_true",
        help="Whether the protocol is distributed.",
    )
    parser.add_argument(
        "-e",
        action="store_true",
        help="Allow the execution to never block.",
    )
    args = parser.parse_args()

    if args.e:
        QUEUE_SIZE = 0

    if args.distributed:
        v = DistributedVisualizer()
    else:
        v = ProtocolVisualizer()

    def callback(watcher: ClassWatcher):
        v.set_protocols({name: cls for name, cls in watcher.get_classes()})

    watcher = ClassWatcher(args.path, callback)

    v.add_atexit(watcher.stop)

    v.run_gui()

from pathlib import Path
from shutil import copytree
from tempfile import TemporaryDirectory

from .logging import get_logger

log = get_logger(__name__)


class DirWatcherContext:
    def __init__(self, path, exit_action=None):
        self.logger = get_logger(__name__)
        self.path = path
        self.exit_action = exit_action

    def __enter__(self):
        self.enter()

    def enter(self):
        self.pre_files = list(Path(self.path).rglob("*"))

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.exit()

    def exit(self):
        gen_files = self.newfiles()
        for file in gen_files:
            self.logger.debug(file)
            if self.exit_action:
                self.exit_action(file)
        return gen_files

    def newfiles(self):
        gen_files = list(
            x for x in Path(self.path).rglob("*") if x not in self.pre_files
        )[::-1]
        return gen_files


class CloneDir(TemporaryDirectory):
    """
    Clones a directory to a temporary directory.
    """

    def __init__(
        self,
        input_dir=Path,
        suffix=None,
        prefix=None,
        out_dir=None,
        ignore_cleanup_errors=False,
    ):
        self.path = Path(input_dir)
        if not self.path.is_dir():
            raise NotADirectoryError(f"{self.path} is not a directory")
        super().__init__(
            suffix=suffix,
            prefix=prefix,
            dir=out_dir,
            ignore_cleanup_errors=ignore_cleanup_errors,
        )
        copytree(str(self.path), self.name, dirs_exist_ok=True)

    def __enter__(self):
        log.debug(f"Cloning {self.path} to {self.name}")
        return super().__enter__()

    def cleanup(self):
        log.debug(f"Cleaning up {self.name}")
        contents = list(Path(self.name).glob("*"))
        contents = [str(x) for x in contents]
        log.debug(f"Removing: {contents}")
        super().cleanup()

    def list_files(self):
        return list(Path(self.name).rglob("*"))


if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.DEBUG)
    foo = CloneDir("tests/data")
    foo.cleanup()

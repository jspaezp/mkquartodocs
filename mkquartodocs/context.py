from pathlib import Path
from shutil import copytree
from tempfile import TemporaryDirectory

from .logging import get_logger

log = get_logger(__name__)


class DirWatcherContext:
    """Context manager to watch a directory for changes.

    It checks the context for changes and returns a list of new files.
    When used as a context manager, it will apply the exit action function
    to each new file.

    Example:
    >>> exit_fun = lambda x: print(f"Deleting {x}")
    >>> with DirWatcherContext("dir", exit_action = exit_fun) as ctx:
    ...     # make file A
    ...     new_files = ctx.newfiles
    ...     # make file B
    ... # file a is deleted, file B is kept
    """

    def __init__(self, path, exit_action=None, update_on_exit=True):
        self.logger = get_logger(__name__)
        self.path = path
        self.exit_action = exit_action
        self.newfiles = []
        self.update_on_exit = update_on_exit

    def __enter__(self):
        self.enter()

    def enter(self):
        self.pre_files = list(Path(self.path).rglob("*"))

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.exit(update=self.update_on_exit)

    def exit(self, update=True):
        gen_files = self.newfiles
        if update:
            gen_files = self.update()

        for file in gen_files:
            self.logger.debug(file)
            if self.exit_action:
                self.exit_action(file)
        return gen_files

    def update(self):
        gen_files = list(
            x for x in Path(self.path).rglob("*") if x not in self.pre_files
        )[::-1]
        self.newfiles = gen_files
        return gen_files


class CloneDir(TemporaryDirectory):
    """Clones a directory to a temporary directory.

    It is meant to be used as a context manager.

    Examample:
        >>> with CloneDir("path/to/dir") as clone:
        >>>     print(clone.name)
        >>>     # do stuff
        >>> # clone is deleted
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

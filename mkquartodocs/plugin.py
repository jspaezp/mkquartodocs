import logging
import shutil
import subprocess
import warnings
from collections.abc import MutableMapping
from pathlib import Path
from typing import Any

import mkdocs
from mkdocs.plugins import BasePlugin
from mkdocs.utils import warning_filter


class LoggerAdapter(logging.LoggerAdapter):
    """A logger adapter to prefix messages."""

    def __init__(self, prefix: str, logger: logging.Logger):
        """Initialize the object.
        Arguments:
            prefix: The string to insert in front of every message.
            logger: The logger instance.
        """
        super().__init__(logger, {})
        self.prefix = prefix

    def process(self, msg: str, kwargs: MutableMapping[str, Any]) -> tuple[str, Any]:
        """Process the message.
        Arguments:
            msg: The message:
            kwargs: Remaining arguments.
        Returns:
            The processed message.
        """
        return f"{self.prefix}: {msg}", kwargs


def get_logger(name: str) -> LoggerAdapter:
    """Return a pre-configured logger.
    Arguments:
        name: The name to use with `logging.getLogger`.
    Returns:
        A logger configured to work well in MkDocs.
    """
    logger = logging.getLogger(f"mkdocs.plugins.{name}")
    logger.addFilter(warning_filter)
    return LoggerAdapter(name.split(".", 1)[0], logger)


log = get_logger(__name__)


class DirContext:
    def __init__(self, path):
        self.path = path

    def __enter__(self):
        self.enter()

    def enter(self):
        self.pre_files = list(Path(self.path).rglob("*"))

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.exit()

    def exit(self):
        gen_files = self.newfiles()
        for file in gen_files:
            log.info(file)
        return gen_files

    def newfiles(self):
        gen_files = list(
            x for x in Path(self.path).rglob("*") if x not in self.pre_files
        )
        return gen_files


class MkDocstringPlugin(BasePlugin):
    config_scheme = (
        ("quarto_path", mkdocs.config.config_options.Type(Path)),
        ("keep_out", mkdocs.config.config_options.Type(bool, default=False)),
    )

    def on_config(self, config, **kwargs):
        passed_path = self.config["quarto_path"]
        quarto = shutil.which(passed_path if passed_path else "quarto")
        self.config["quarto_path"] = quarto

        return config

    def on_pre_build(self, config):
        quarto = self.config["quarto_path"]
        docs_dir = config["docs_dir"]

        quarto_docs = Path(docs_dir).rglob("*.qmd")
        quarto_docs = [str(x) for x in quarto_docs]

        self.dir_context = DirContext(docs_dir)
        self.dir_context.enter()
        if quarto_docs:
            for x in quarto_docs:
                log.info(f"Rendering {x}")
                subprocess.call([quarto, "render", x, "--to=markdown"])
        else:
            warnings.warn(f"No quarto files were found in directory {docs_dir}")
        log.info(self.dir_context.newfiles())

    def on_post_build(self, config):
        log.info("Cleaning up:")
        self.dir_context.exit()

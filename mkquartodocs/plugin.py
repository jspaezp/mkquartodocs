import re
import shutil
import subprocess
import warnings
from pathlib import Path

from mkdocs.config import config_options
from mkdocs.plugins import BasePlugin

from .context import DirWatcherContext
from .logging import get_logger

log = get_logger(__name__)


def _delete_file(path):
    """Delete a file or an empty directory."""
    path = Path(path)
    if path.is_file():
        path.unlink()
    elif path.is_dir():
        path.rmdir()


class MkDocstringPlugin(BasePlugin):
    config_scheme = (
        ("quarto_path", config_options.Type(Path)),
        ("ignore", config_options.Type(str)),
        ("keep_output", config_options.Type(bool, default=False)),
    )

    def on_config(self, config, **kwargs):
        passed_path = self.config["quarto_path"]
        quarto = shutil.which(passed_path if passed_path else "quarto")
        self.config["quarto_path"] = quarto
        # self.ignores = [re.compile(x) for x in self.config["ignore"]]

        if self.config["ignore"]:
            self.ignores = [re.compile(self.config["ignore"])]
        else:
            self.ignores = []
        self.exit_action = _delete_file if not self.config["keep_output"] else None

        return config

    def _filter_ignores(self, paths):
        out = []
        for x in paths:
            if not any(re.fullmatch(pattern, x) for pattern in self.ignores):
                out.append(x)

        return out

    def on_pre_build(self, config):
        quarto = self.config["quarto_path"]
        docs_dir = config["docs_dir"]

        quarto_docs = Path(docs_dir).rglob("*.qmd")
        quarto_docs = [str(x) for x in quarto_docs]
        quarto_docs = self._filter_ignores(quarto_docs)

        self.dir_context = DirWatcherContext(docs_dir, exit_action=self.exit_action)
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

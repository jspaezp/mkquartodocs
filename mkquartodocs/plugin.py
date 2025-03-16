import re
import time
import shutil
import subprocess
import warnings
from pathlib import Path
from dataclasses import dataclass

from mkdocs.config import config_options
from mkdocs.plugins import BasePlugin

from mkquartodocs.extension import QuartoCellDataExtension

from .context import DirWatcherContext
from .logging import get_logger
from .utils import convert_nav

log = get_logger(__name__)


def _delete_file(path):
    """Delete a file or an empty directory."""
    path = Path(path)
    if path.is_file():
        path.unlink()
    elif path.is_dir():
        path.rmdir()


@dataclass
class QuartoRuner:
    quarto_path: Path

    def run(self, *args, **kwargs):
        subprocess.run([self.quarto_path, *args], **kwargs)

    def run_with_retries(self, quarto_file, num_retries=5):
        for i in range(num_retries):
            try:
                subprocess.run(
                    [
                        self.quarto_path,
                        "render",
                        str(quarto_file),
                        "--to=markdown-simple_tables",
                    ],
                    check=True,
                )
                break
            except subprocess.CalledProcessError as e:
                # ERROR: Couldn't find open server
                # it ocasionally fails with that error ...
                if i >= num_retries:
                    log.error(
                        f"Quarto failed to render {quarto_file} after {num_retries} tries"
                    )
                    log.error(f"Quarto failed with error: {e}")
                    raise
                warnings.warn(f"Quarto failed to render {quarto_file}, retrying")
                time.sleep(2)


@dataclass
class MkQuartodocsConfig:
    quarto_path: Path
    ignore_pattern: str | None = None
    keep_output: bool = False
    force_rebuild: bool = False

    @classmethod
    def from_mkdocs_config(cls, config):
        config = config["plugins"]["mkquartodocs"].config
        keep = ["quarto_path", "ignore_pattern", "keep_output", "force_rebuild"]
        deprecated = {"ignore": "ignore_pattern"}
        keep_dict = {k: config[k] for k in keep if k in config}
        for k, v in deprecated.items():
            if k in config:
                log.warning(f"{k} is deprecated, use {v} instead")
                keep_dict[v] = config[k]

        # if extras:
        #     raise ValueError(f"Unknown configuration options: {extras}")

        if not keep_dict["quarto_path"]:
            keep_dict["quarto_path"] = shutil.which("quarto")
        else:
            keep_dict["quarto_path"] = Path(keep_dict["quarto_path"])

        log.debug(f"Configuration: {keep_dict}")

        return cls(**keep_dict)

    def __getitem__(self, key):
        return getattr(self, key)

    def __setitem__(self, key, value):
        setattr(self, key, value)


class MkQuartoDocsPlugin(BasePlugin):
    config_scheme = (
        ("quarto_path", config_options.Type(Path)),
        ("ignore_pattern", config_options.Type(str)),
        ("keep_output", config_options.Type(bool, default=False)),
        ("force_rebuild", config_options.Type(bool, default=False)),
    )

    def on_config(self, config, **kwargs):
        self.config = MkQuartodocsConfig.from_mkdocs_config(config)
        config["nav"] = convert_nav(config["nav"])

        if self.config["ignore_pattern"]:
            self.ignores = [re.compile(self.config["ignore_pattern"])]
        else:
            self.ignores = []
        self.exit_action = _delete_file if not self.config["keep_output"] else None

        self.extension = QuartoCellDataExtension()
        config["markdown_extensions"].append(self.extension)
        return config

    def _filter_ignores(self, paths):
        out = []
        for x in paths:
            if not any(re.fullmatch(pattern, x) for pattern in self.ignores):
                out.append(x)

        return out

    def _get_quarto_docs(self, docs_dir):
        quarto_docs = Path(docs_dir).rglob("*.qmd")
        quarto_docs = [str(x) for x in quarto_docs]
        quarto_docs = self._filter_ignores(quarto_docs)
        return quarto_docs

    def on_pre_build(self, config):
        quarto = self.config["quarto_path"]
        docs_dir = config["docs_dir"]

        self.dir_context = DirWatcherContext(
            docs_dir, exit_action=self.exit_action, update_on_exit=False
        )
        self.dir_context.enter()
        quarto_docs = self._get_quarto_docs(docs_dir)
        runner = QuartoRuner(quarto)
        if quarto_docs:
            for x in quarto_docs:
                x = Path(x)
                parent_path = x.parent
                expected_out = Path(parent_path) / (x.stem + ".md")
                if expected_out.exists() and not self.config["force_rebuild"]:
                    qmd_mtime = x.stat().st_mtime
                    md_mtime = expected_out.stat().st_mtime
                    if qmd_mtime < md_mtime:
                        log.info(f"Skipping {x} as it is older than {expected_out}")
                        continue
                log.info(f"Rendering {x}")
                runner.run_with_retries(x)
        else:
            warnings.warn(f"No quarto files were found in directory {docs_dir}")

        log.info("Updating directory context")
        log.info(self.dir_context.update())

    def on_post_build(self, config):
        log.info("Cleaning up:")
        self.dir_context.exit(update=False)

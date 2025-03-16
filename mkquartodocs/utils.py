from .logging import get_logger

log = get_logger(__name__)


def convert_nav(nav: str | list | dict) -> str | list | dict:
    if isinstance(nav, str):
        if nav.endswith(".qmd"):
            log.debug(f"Converting {nav} to {nav.replace('.qmd', '.md')}")
            return nav.replace(".qmd", ".md")
        return nav
    if isinstance(nav, list):
        return [convert_nav(x) for x in nav]

    if isinstance(nav, dict):
        return {k: convert_nav(v) for k, v in nav.items()}

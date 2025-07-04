from __future__ import annotations

import re
from pathlib import Path
from textwrap import dedent

from qrenderer import (
    QRenderer,
    RenderDoc,
    RenderDocClass,
    exclude_parameters,
)
from qrenderer._pandoc.inlines import shortcode
from quartodoc.pandoc.blocks import Blocks, CodeBlock, Div, Header
from quartodoc.pandoc.components import Attr

DOC_DIR = Path(__file__).parent
REFERENCE_DIR = DOC_DIR / "reference"
EXAMPLES_DIR = REFERENCE_DIR / "examples"

usage_pattern = re.compile(
    r"\n\n?\*\*Usage\*\*"
    r".+?\n"
    r"(?P<usage_signature>"
    # Indented signature block
    r"\s{4}\w"
    r".*?\n"
    r"\s{4}\)"
    r")",
    re.DOTALL,
)


class Renderer(QRenderer):
    pass


exclude_parameters(
    {
        "plotnine.scale_color_hue": ("s", "color_space"),
    }
)


class _RenderDoc(RenderDoc):
    def render_body(self):
        body = super().render_body()
        if self.kind == "type":
            return body

        notebook = EXAMPLES_DIR / f"{self.obj.name}.ipynb"
        if not notebook.exists():
            return body

        relpath = notebook.relative_to(REFERENCE_DIR)
        embed_notebook = shortcode("embed", f"{relpath}", echo="true")
        header = Header(self.level + 1, "Examples")
        return Blocks([body, header, embed_notebook])

    # Until quartodoc makes it possible to use a tilde to use
    # and objects name and not the qualified path, we have to
    # create exceptions for all the qualified paths that we want
    # to be short.
    # Ref: https://github.com/machow/quartodoc/issues/230
    @property
    def summary_name(self):
        name = super().summary_name
        return name[8:] if name.startswith("options.") else name


class _RenderDocClass(RenderDocClass):
    def render_signature(self):
        signature = super().render_signature()
        docstring = self.obj.docstring.value if self.obj.docstring else ""
        m = usage_pattern.search(docstring)
        if not m:
            return signature

        usage_signature = dedent(m.group("usage_signature"))
        return Div(
            CodeBlock(usage_signature, Attr(classes=["py"])),
            Attr(classes=["doc-signature", "doc-class"]),
        )

    def render_body(self):
        token = self.obj.name.split("_")[0]
        body = super().render_body()
        if token in {"geom", "stat"}:
            body = usage_pattern.sub("", str(body))
        return Blocks([body])

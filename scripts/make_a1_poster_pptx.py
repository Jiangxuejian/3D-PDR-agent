#!/usr/bin/env python3
"""Build an A1 PowerPoint poster for the 3D-PDR Agent project.

The environment used for this workspace does not provide python-pptx, so this
script writes a small Office Open XML presentation directly with stdlib tools.
"""

from __future__ import annotations

import html
import shutil
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "posters" / "3d_pdr_agent_A1_poster.pptx"
EMU_PER_MM = 36000
EMU_PER_PT = 12700


def mm(value: float) -> int:
    return int(round(value * EMU_PER_MM))


def pt(value: float) -> int:
    return int(round(value * 100))


SLIDE_W = mm(594)
SLIDE_H = mm(841)


class SlideBuilder:
    def __init__(self) -> None:
        self.parts: list[str] = []
        self.rels: list[tuple[str, str, str]] = []
        self.next_id = 2
        self.next_rel = 2

    def _id(self) -> int:
        current = self.next_id
        self.next_id += 1
        return current

    def add_rel(self, target: str, rel_type: str = "image") -> str:
        rid = f"rId{self.next_rel}"
        self.next_rel += 1
        if rel_type == "image":
            full_type = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image"
        else:
            full_type = rel_type
        self.rels.append((rid, full_type, target))
        return rid

    def rect(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        fill: str,
        line: str = "FFFFFF",
        line_w: float = 0,
        radius: str = "roundRect",
        alpha: int | None = None,
    ) -> None:
        sid = self._id()
        fill_xml = f'<a:solidFill><a:srgbClr val="{fill}">'
        if alpha is not None:
            fill_xml += f'<a:alpha val="{alpha}"/>'
        fill_xml += "</a:srgbClr></a:solidFill>"
        if line_w <= 0:
            line_xml = "<a:ln><a:noFill/></a:ln>"
        else:
            line_xml = (
                f'<a:ln w="{int(line_w * EMU_PER_PT)}">'
                f'<a:solidFill><a:srgbClr val="{line}"/></a:solidFill></a:ln>'
            )
        self.parts.append(
            f"""
            <p:sp>
              <p:nvSpPr><p:cNvPr id="{sid}" name="Shape {sid}"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>
              <p:spPr>
                <a:xfrm><a:off x="{mm(x)}" y="{mm(y)}"/><a:ext cx="{mm(w)}" cy="{mm(h)}"/></a:xfrm>
                <a:prstGeom prst="{radius}"><a:avLst/></a:prstGeom>
                {fill_xml}
                {line_xml}
              </p:spPr>
            </p:sp>
            """
        )

    def line(self, x1: float, y1: float, x2: float, y2: float, color: str, width_pt: float = 2.0, arrow: bool = False) -> None:
        sid = self._id()
        arrow_xml = '<a:tailEnd type="triangle"/>' if arrow else ""
        self.parts.append(
            f"""
            <p:cxnSp>
              <p:nvCxnSpPr><p:cNvPr id="{sid}" name="Connector {sid}"/><p:cNvCxnSpPr/><p:nvPr/></p:nvCxnSpPr>
              <p:spPr>
                <a:xfrm>
                  <a:off x="{mm(min(x1, x2))}" y="{mm(min(y1, y2))}"/>
                  <a:ext cx="{mm(abs(x2 - x1))}" cy="{mm(abs(y2 - y1))}"/>
                </a:xfrm>
                <a:prstGeom prst="line"><a:avLst/></a:prstGeom>
                <a:ln w="{int(width_pt * EMU_PER_PT)}">
                  <a:solidFill><a:srgbClr val="{color}"/></a:solidFill>
                  {arrow_xml}
                </a:ln>
              </p:spPr>
            </p:cxnSp>
            """
        )

    def text(
        self,
        x: float,
        y: float,
        w: float,
        h: float,
        text: str,
        size: float,
        color: str = "1B1B1B",
        bold: bool = False,
        fill: str | None = None,
        align: str = "l",
        valign: str = "t",
        margin: float = 2.0,
        line: str | None = None,
    ) -> None:
        sid = self._id()
        fill_xml = "<a:noFill/>" if fill is None else f'<a:solidFill><a:srgbClr val="{fill}"/></a:solidFill>'
        line_xml = "<a:ln><a:noFill/></a:ln>" if line is None else f'<a:ln w="{int(0.8 * EMU_PER_PT)}"><a:solidFill><a:srgbClr val="{line}"/></a:solidFill></a:ln>'
        body = []
        for raw in text.split("\n"):
            escaped = html.escape(raw)
            body.append(
                f"""
                <a:p>
                  <a:pPr algn="{align}"/>
                  <a:r>
                    <a:rPr lang="en-US" sz="{pt(size)}" b="{1 if bold else 0}">
                      <a:solidFill><a:srgbClr val="{color}"/></a:solidFill>
                      <a:latin typeface="Aptos"/>
                    </a:rPr>
                    <a:t>{escaped}</a:t>
                  </a:r>
                </a:p>
                """
            )
        self.parts.append(
            f"""
            <p:sp>
              <p:nvSpPr><p:cNvPr id="{sid}" name="Text {sid}"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>
              <p:spPr>
                <a:xfrm><a:off x="{mm(x)}" y="{mm(y)}"/><a:ext cx="{mm(w)}" cy="{mm(h)}"/></a:xfrm>
                <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
                {fill_xml}
                {line_xml}
              </p:spPr>
              <p:txBody>
                <a:bodyPr wrap="square" anchor="{valign}" lIns="{mm(margin)}" tIns="{mm(margin)}" rIns="{mm(margin)}" bIns="{mm(margin)}"/>
                <a:lstStyle/>
                {''.join(body)}
              </p:txBody>
            </p:sp>
            """
        )

    def image(self, x: float, y: float, w: float, h: float, rid: str, name: str) -> None:
        sid = self._id()
        self.parts.append(
            f"""
            <p:pic>
              <p:nvPicPr>
                <p:cNvPr id="{sid}" name="{html.escape(name)}"/>
                <p:cNvPicPr><a:picLocks noChangeAspect="1"/></p:cNvPicPr>
                <p:nvPr/>
              </p:nvPicPr>
              <p:blipFill>
                <a:blip r:embed="{rid}"/>
                <a:stretch><a:fillRect/></a:stretch>
              </p:blipFill>
              <p:spPr>
                <a:xfrm><a:off x="{mm(x)}" y="{mm(y)}"/><a:ext cx="{mm(w)}" cy="{mm(h)}"/></a:xfrm>
                <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
                <a:ln w="{int(1.0 * EMU_PER_PT)}"><a:solidFill><a:srgbClr val="D8E2EA"/></a:solidFill></a:ln>
              </p:spPr>
            </p:pic>
            """
        )


def content_types(image_names: list[str]) -> str:
    defaults = [
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>',
        '<Default Extension="xml" ContentType="application/xml"/>',
        '<Default Extension="png" ContentType="image/png"/>',
    ]
    overrides = [
        '<Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>',
        '<Override PartName="/ppt/slides/slide1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>',
        '<Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>',
        '<Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>',
        '<Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>',
        '<Override PartName="/ppt/presProps.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presProps+xml"/>',
        '<Override PartName="/ppt/viewProps.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.viewProps+xml"/>',
        '<Override PartName="/ppt/tableStyles.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.tableStyles+xml"/>',
    ]
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
{''.join(defaults)}
{''.join(overrides)}
</Types>"""


def make_slide() -> tuple[str, str, list[tuple[Path, str]]]:
    b = SlideBuilder()
    media: list[tuple[Path, str]] = []

    def add_media(path: str, target: str) -> str:
        src = ROOT / path
        media.append((src, target))
        return b.add_rel(f"../media/{target}")

    r_nh2 = add_media("3D-PDR-dev/benchmarks/NH2_diffuse_64.png", "nh2.png")
    r_tgas = add_media("3D-PDR-dev/benchmarks/Tgas.png", "tgas.png")
    r_co = add_media("3D-PDR-dev/benchmarks/TrCO10.png", "trco10.png")
    r_3d = add_media("3D-PDR-dev/benchmarks/Tgas3D.png", "tgas3d.png")

    # Background
    b.rect(0, 0, 594, 841, "F7F9FB", line_w=0, radius="rect")
    b.rect(0, 0, 594, 96, "102A43", line_w=0, radius="rect")
    b.rect(0, 96, 594, 8, "F28C28", line_w=0, radius="rect")
    b.rect(0, 104, 594, 4, "2CB1A1", line_w=0, radius="rect")

    b.text(22, 8, 385, 46, "3D-PDR Agent", 46, "FFFFFF", bold=True)
    b.text(
        24,
        50,
        385,
        31,
        "A Codex skill/plugin workflow for reproducible ISM post-processing\nfrom simulation snapshots to synthetic observables",
        16,
        "DCEBFA",
    )
    b.text(420, 14, 150, 55, "A1 portrait poster\nAstrophysics / ISM\nX. Jiang et al.", 14, "FFFFFF", align="r")

    # Workflow band
    b.rect(18, 125, 558, 138, "FFFFFF", line="D6DEE6", line_w=1.1, radius="roundRect")
    b.text(30, 136, 270, 22, "Agent Workflow", 22, "102A43", bold=True)
    b.text(318, 139, 240, 20, "Transparent, file-based reproducibility", 13, "3B4A57", align="r")
    steps = [
        ("1", "INPUT/RAW", "source snapshots"),
        ("2", "INPUT/SELECTED", "curated links + DAT"),
        ("3", "sims_*", "short run paths"),
        ("4", "3D-PDR", "chemistry + thermal state"),
        ("5", "RT-synth", "synthetic observables"),
        ("6", "Products", "preserved hierarchy"),
    ]
    x = 35
    for idx, title, detail in steps:
        b.rect(x, 174, 70, 46, "F3F7FA", line="CAD6E0", line_w=0.7, radius="roundRect")
        b.rect(x + 5, 181, 17, 17, "102A43", line_w=0, radius="roundRect")
        b.text(x + 5, 182, 17, 9, idx, 11, "FFFFFF", bold=True, align="c", margin=0.1)
        b.text(x + 24, 180.5, 42, 10, title, 8.8, "102A43", bold=True, margin=0.2)
        b.text(x + 7, 202, 56, 10, detail, 8.6, "3B4A57", align="c", margin=0.2)
        if idx != "6":
            b.line(x + 71, 197, x + 88, 197, "F28C28", 2.0, arrow=True)
        x += 88
    b.text(
        33,
        231,
        526,
        18,
        "Operational knowledge becomes explicit: path conventions, skip/force behavior, local parameter rewriting, helper scripts, and HPC submission templates.",
        12,
        "263238",
    )

    # Mid-page panels
    left_x, right_x = 18, 306
    panel_y, panel_w, panel_h = 282, 270, 232
    b.rect(left_x, panel_y, panel_w, panel_h, "FFFFFF", line="D6DEE6", line_w=1.1, radius="roundRect")
    b.rect(right_x, panel_y, panel_w, panel_h, "FFFFFF", line="D6DEE6", line_w=1.1, radius="roundRect")

    b.text(left_x + 12, panel_y + 10, 246, 22, "Why an Agent?", 22, "102A43", bold=True)
    b.text(
        left_x + 12,
        panel_y + 39,
        246,
        72,
        "3D-PDR and RT-synth post-processing is rich but operationally brittle:\n"
        "- raw snapshot placement\n"
        "- HDF5 -> density DAT\n"
        "- velocity grids for RT-synth\n"
        "- local parameter rewriting\n"
        "- HPC sync + SLURM submission\n"
        "- synthetic map rendering",
        12,
        "263238",
    )
    b.rect(left_x + 12, panel_y + 125, 246, 48, "FFF3E4", line="F28C28", line_w=0.8, radius="roundRect")
    b.text(
        left_x + 18,
        panel_y + 132,
        234,
        31,
        "Design goal: make the notebook-to-HPC-to-products path repeatable and inspectable without hiding the astrophysics.",
        13,
        "7A3E00",
        bold=True,
    )
    b.text(
        left_x + 12,
        panel_y + 184,
        246,
        27,
        "The agent reduces operational friction while preserving transparent files and commands.",
        12,
        "263238",
    )

    b.text(right_x + 12, panel_y + 10, 246, 22, "Proposed Skill Names", 22, "102A43", bold=True)
    capabilities = [
        ("preview-hydro", "inspect raw hydro snapshots before curation"),
        ("curate-hydro", "place/select hydro files and generate DAT pairs"),
        ("run-pdr", "create snapshot-local sims_* folders and run 3DPDR"),
        ("sync-hpc-run", "rsync sources and submit sbatch jobs"),
        ("run-rtsynth", "produce multi-angle synthetic maps"),
        ("render-rt", "convert RT output tables to PNG diagnostics"),
    ]
    y = panel_y + 43
    for name, desc in capabilities:
        b.rect(right_x + 13, y, 58, 15, "E6F7F5", line="2CB1A1", line_w=0.5, radius="roundRect")
        b.text(right_x + 15, y + 1.2, 54, 10, name, 9.3, "075E56", bold=True, align="c", margin=0.2)
        b.text(right_x + 77, y - 0.8, 176, 16, desc, 10.2, "2A3742", margin=0.5)
        y += 25
    b.text(
        right_x + 13,
        panel_y + 199,
        244,
        20,
        "Verb-first names read better in posters, talks, and user-facing docs.",
        11.5,
        "263238",
    )

    # Science image panel
    b.rect(18, 535, 558, 194, "FFFFFF", line="D6DEE6", line_w=1.1, radius="roundRect")
    b.text(30, 545, 260, 22, "Science Products", 22, "102A43", bold=True)
    b.text(304, 550, 250, 16, "Bundled 3D-PDR benchmark outputs", 12, "3B4A57", align="r")
    b.image(32, 580, 118, 88, r_nh2, "H2 column density")
    b.image(166, 580, 118, 88, r_tgas, "Gas temperature")
    b.image(300, 580, 118, 88, r_co, "CO 1-0 tracer")
    b.image(434, 580, 118, 88, r_3d, "3D temperature benchmark")
    b.text(32, 672, 118, 12, "H2 column density", 10.2, "3B4A57", bold=True, align="c", margin=0.2)
    b.text(166, 672, 118, 12, "Gas temperature", 10.2, "3B4A57", bold=True, align="c", margin=0.2)
    b.text(300, 672, 118, 12, "CO 1-0 tracer", 10.2, "3B4A57", bold=True, align="c", margin=0.2)
    b.text(434, 672, 118, 12, "3D thermal structure", 10.2, "3B4A57", bold=True, align="c", margin=0.2)
    b.text(
        36,
        699,
        520,
        15,
        "Robust post-processing bridges simulations and observable ISM diagnostics.",
        12,
        "263238",
        align="c",
    )

    # Bottom panel
    b.rect(18, 747, 558, 64, "FFFFFF", line="D6DEE6", line_w=1.1, radius="roundRect")
    b.text(30, 754, 230, 18, "Repository Architecture", 18, "102A43", bold=True)
    b.text(
        30,
        776,
        260,
        23,
        "Canonical paths: INPUT/RAW, INPUT/SELECTED, 3D-PDR-dev, RT-synth, Products/RTsynth, plugins/3d-pdr-agent",
        11,
        "263238",
    )
    b.rect(314, 758, 244, 38, "F1FBF8", line="2CB1A1", line_w=0.8, radius="roundRect")
    b.text(322, 763, 228, 12, "Conference message", 13, "075E56", bold=True)
    b.text(
        322,
        778,
        228,
        12,
        "Agentic infrastructure reduces friction while preserving transparent scientific workflows.",
        10.5,
        "263238",
    )

    # Footer
    b.rect(18, 821, 558, 11, "102A43", line_w=0, radius="rect")
    b.text(24, 822.5, 275, 7, "3D-PDR Agent | INPUT -> DAT -> 3D-PDR -> RT-synth -> Products", 7.8, "FFFFFF", margin=0.2)
    b.text(330, 822.5, 240, 7, "Edit author, affiliation, QR code, and captions before printing.", 7.8, "DCEBFA", align="r", margin=0.2)

    slide_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
       xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
       xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld>
    <p:spTree>
      <p:nvGrpSpPr>
        <p:cNvPr id="1" name=""/>
        <p:cNvGrpSpPr/>
        <p:nvPr/>
      </p:nvGrpSpPr>
      <p:grpSpPr>
        <a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm>
      </p:grpSpPr>
      {''.join(b.parts)}
    </p:spTree>
  </p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sld>"""

    rels = [
        ('rId1', 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout', '../slideLayouts/slideLayout1.xml'),
        *b.rels,
    ]
    rel_xml = rels_xml(rels)
    return slide_xml, rel_xml, media


def rels_xml(rels: list[tuple[str, str, str]]) -> str:
    entries = "\n".join(
        f'<Relationship Id="{rid}" Type="{rtype}" Target="{html.escape(target)}"/>'
        for rid, rtype, target in rels
    )
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
{entries}
</Relationships>"""


def write_pptx() -> None:
    slide_xml, slide_rels, media = make_slide()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUT.with_suffix(".tmp.pptx")
    if tmp.exists():
        tmp.unlink()

    presentation = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
                xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
                xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId1"/></p:sldMasterIdLst>
  <p:sldIdLst><p:sldId id="256" r:id="rId2"/></p:sldIdLst>
  <p:sldSz cx="{SLIDE_W}" cy="{SLIDE_H}" type="custom"/>
  <p:notesSz cx="6858000" cy="9144000"/>
  <p:defaultTextStyle/>
</p:presentation>"""

    master = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldMaster xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
             xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
             xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr></p:spTree></p:cSld>
  <p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/>
  <p:sldLayoutIdLst><p:sldLayoutId id="2147483649" r:id="rId1"/></p:sldLayoutIdLst>
  <p:txStyles><p:titleStyle/><p:bodyStyle/><p:otherStyle/></p:txStyles>
</p:sldMaster>"""

    layout = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldLayout xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
             xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
             xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" type="blank" preserve="1">
  <p:cSld name="Blank"><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr></p:spTree></p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sldLayout>"""

    theme = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="3D-PDR Agent">
  <a:themeElements>
    <a:clrScheme name="3D-PDR"><a:dk1><a:srgbClr val="102A43"/></a:dk1><a:lt1><a:srgbClr val="FFFFFF"/></a:lt1><a:dk2><a:srgbClr val="263238"/></a:dk2><a:lt2><a:srgbClr val="F7F9FB"/></a:lt2><a:accent1><a:srgbClr val="2CB1A1"/></a:accent1><a:accent2><a:srgbClr val="F28C28"/></a:accent2><a:accent3><a:srgbClr val="4C78A8"/></a:accent3><a:accent4><a:srgbClr val="7A3E00"/></a:accent4><a:accent5><a:srgbClr val="D6DEE6"/></a:accent5><a:accent6><a:srgbClr val="6B7280"/></a:accent6><a:hlink><a:srgbClr val="2563EB"/></a:hlink><a:folHlink><a:srgbClr val="6D28D9"/></a:folHlink></a:clrScheme>
    <a:fontScheme name="Aptos"><a:majorFont><a:latin typeface="Aptos Display"/></a:majorFont><a:minorFont><a:latin typeface="Aptos"/></a:minorFont></a:fontScheme>
    <a:fmtScheme name="Default"><a:fillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:fillStyleLst><a:lnStyleLst><a:ln w="9525"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln></a:lnStyleLst><a:effectStyleLst><a:effectStyle><a:effectLst/></a:effectStyle></a:effectStyleLst><a:bgFillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:bgFillStyleLst></a:fmtScheme>
  </a:themeElements>
</a:theme>"""

    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content_types([m[1] for m in media]))
        z.writestr("_rels/.rels", rels_xml([("rId1", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument", "ppt/presentation.xml")]))
        z.writestr("ppt/presentation.xml", presentation)
        z.writestr("ppt/_rels/presentation.xml.rels", rels_xml([
            ("rId1", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster", "slideMasters/slideMaster1.xml"),
            ("rId2", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide", "slides/slide1.xml"),
            ("rId3", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/presProps", "presProps.xml"),
            ("rId4", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/viewProps", "viewProps.xml"),
            ("rId5", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme", "theme/theme1.xml"),
            ("rId6", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/tableStyles", "tableStyles.xml"),
        ]))
        z.writestr("ppt/slides/slide1.xml", slide_xml)
        z.writestr("ppt/slides/_rels/slide1.xml.rels", slide_rels)
        z.writestr("ppt/slideMasters/slideMaster1.xml", master)
        z.writestr("ppt/slideMasters/_rels/slideMaster1.xml.rels", rels_xml([
            ("rId1", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout", "../slideLayouts/slideLayout1.xml"),
            ("rId2", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme", "../theme/theme1.xml"),
        ]))
        z.writestr("ppt/slideLayouts/slideLayout1.xml", layout)
        z.writestr("ppt/slideLayouts/_rels/slideLayout1.xml.rels", rels_xml([
            ("rId1", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster", "../slideMasters/slideMaster1.xml"),
        ]))
        z.writestr("ppt/theme/theme1.xml", theme)
        z.writestr("ppt/presProps.xml", '<p:presentationPr xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"/>')
        z.writestr("ppt/viewProps.xml", '<p:viewPr xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"/>')
        z.writestr("ppt/tableStyles.xml", '<a:tblStyleLst xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" def="{5C22544A-7EE6-4342-B048-85BDC9FD1C3A}"/>')
        for src, target in media:
            if not src.exists():
                raise FileNotFoundError(src)
            z.write(src, f"ppt/media/{target}")

    shutil.move(tmp, OUT)
    print(OUT)


if __name__ == "__main__":
    write_pptx()

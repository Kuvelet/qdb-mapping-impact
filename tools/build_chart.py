"""Render a static, zero-based case-study chart from approved aggregate metrics.

Optional dependency: Pillow. The demo and tests do not require it.
"""

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]


def font(size, bold=False):
    names = [
        Path("C:/Windows/Fonts") / ("segoeuib.ttf" if bold else "segoeui.ttf"),
        Path("/usr/share/fonts/truetype/dejavu") / ("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"),
        Path("/System/Library/Fonts/Supplemental") / ("Arial Bold.ttf" if bold else "Arial.ttf"),
    ]
    for path in names:
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default(size=size)


def main():
    data = json.loads((ROOT / "evidence/approved_project_metrics.json").read_text())
    image = Image.new("RGB", (1600, 1000), "#ffffff")
    draw = ImageDraw.Draw(image)
    ink, muted, line = "#202529", "#59636b", "#e4e8eb"
    green, red = "#187765", "#b94558"
    draw.text((88, 56), "QDB MAPPING IMPACT", font=font(24, True), fill=green)
    draw.text((88, 102), "Making mapping progress measurable", font=font(49, True), fill=ink)
    draw.text((88, 176), "Standard Motor Products | Project-owner-reported aggregate results", font=font(25), fill=muted)
    draw.text((88, 227), f"{data['total_application_rows']:,} application rows  |  {data['unique_report_notes']:,} unique notes", font=font(27, True), fill=ink)
    draw.line((88, 292, 1512, 292), fill=line, width=2)

    draw.text((88, 327), "Note-mapping progress", font=font(29, True), fill=ink)
    draw.text((1512, 327), f"{data['reported_completion_percent']:.2f}%", font=font(33, True), fill=green, anchor="ra")
    draw.rectangle((88, 390, 1512, 428), fill=line)
    mapped_width = round(1424 * data["notes_marked_mapped"] / data["unique_report_notes"])
    draw.rectangle((88, 390, 88 + mapped_width, 428), fill=green)
    draw.text((88, 447), f"{data['notes_marked_mapped']:,} notes marked mapped", font=font(24), fill=ink)
    remaining = data["unique_report_notes"] - data["notes_marked_mapped"]
    draw.text((1512, 447), f"{remaining:,} notes not marked mapped", font=font(24), fill=muted, anchor="ra")
    draw.line((88, 513, 1512, 513), fill=line, width=2)

    draw.text((88, 550), "Unique application-row coverage", font=font(29, True), fill=ink)
    draw.text((88, 596), "Both percentages use all searched application rows as the denominator.", font=font(23), fill=muted)
    potential = data["potential_unique_rows_all_notes"]
    bars = [
        ("Currently mapped notes", data["unique_rows_with_mapped_notes"], data["reported_current_row_percent"], green, 670),
        ("All listed notes mapped", potential, data["reported_potential_row_percent"], red, 746),
    ]
    draw.line((506, 654, 506, 790), fill=muted, width=2)
    for label, value, pct, color, y in bars:
        draw.text((88, y - 2), label, font=font(25), fill=ink)
        draw.rectangle((508, y, 508 + round(660 * value / potential), y + 34), fill=color)
        draw.text((1512, y - 2), f"{value:,}  ({pct:.2f}%)", font=font(25, True), fill=color, anchor="ra")
    draw.text((88, 822), "Potential includes current coverage. Bars share the same zero-based count scale.", font=font(23), fill=muted)
    draw.line((88, 885, 1512, 885), fill=line, width=2)
    draw.text((88, 914), "Coverage is note occurrence, not confirmed corrections, sales lift, or a catalog-health score.", font=font(23), fill=ink)
    draw.text((88, 951), "Source snapshot date not supplied. Raw company data is not included in this repository.", font=font(21), fill=muted)
    path = ROOT / "assets/project-impact.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, optimize=True)
    print(f"Generated {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

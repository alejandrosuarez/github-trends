# type: ignore

from typing import List, Tuple

from svgwrite import Drawing
from svgwrite.container import Group

from src.svg.style import style


def format_number(num: int) -> str:
    if num > 10000:
        return "~" + str(int(num / 1000)) + "k lines"
    elif num > 1000:
        return "~" + str(int(num / 100) / 10) + "k lines"
    elif num > 100:
        return "~" + str(int(num / 100) * 100) + " lines"
    else:
        return "<100 lines"


def get_template(
    width: int,
    height: int,
    padding: int,
    header_text: str,
    subheader_text: str,
    debug: bool = False,
) -> Tuple[Drawing, Group]:
    d = Drawing(size=(width, height))
    d.defs.add(d.style(style))

    d.add(
        d.rect(
            size=(width - 1, height - 1),
            insert=(0.5, 0.5),
            rx=4.5,
            stroke="#e4e2e2",
            fill="#fffefe",
        )
    )

    d.add(
        d.rect(
            size=(width - 2 * padding, height - 2 * padding),
            insert=(padding, padding),
            fill="#eee" if debug else "#fff",
        )
    )

    dp = Group(transform="translate(" + str(padding) + ", " + str(padding) + ")")

    dp.add(d.text(header_text, insert=(0, 13), class_="header"))
    dp.add(d.text(subheader_text, insert=(0, 31), class_="subheader"))

    return d, dp


def get_bar_section(
    d: Drawing,
    dataset: List[Tuple[str, str, List[Tuple[float, str]]]],
    padding: int = 45,
    bar_width: int = 210,
) -> Group:
    section = Group(transform="translate(0, " + str(padding) + ")")
    for i, (top_text, right_text, data_row) in enumerate(dataset):
        translate = "translate(0, " + str(40 * i) + ")"
        row = Group(transform=translate)
        row.add(d.text(top_text, insert=(2, 15), class_="lang-name"))
        row.add(d.text(right_text, insert=(bar_width + 10, 33), class_="lang-name"))
        progress = Drawing(width=str(bar_width), x="0", y="25")
        progress.add(
            d.rect(size=(bar_width, 8), insert=(0, 0), rx=5, ry=5, fill="#ddd")
        )
        total_percent, total_items = 0, len(data_row)
        for j, (percent, color) in enumerate(data_row):
            color = color or "#ededed"
            bar_percent = bar_width * percent / 100
            bar_total = bar_width * total_percent / 100
            box_size, insert = (bar_percent, 8), (bar_total, 0)
            progress.add(d.rect(size=box_size, insert=insert, rx=5, ry=5, fill=color))

            if total_items > 1:
                box_left, box_right = j > 0, j < total_items - 1
                box_size, insert = bar_percent - 10, bar_total + 5
                if box_left:
                    box_size += 5
                    insert -= 5
                if box_right:
                    box_size += 5
                box_size, insert = (max(box_size, 3), 8), (insert, 0)
                progress.add(d.rect(size=box_size, insert=insert, fill=color))

            total_percent += percent
        row.add(progress)
        section.add(row)
    return section

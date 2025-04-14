#!/usr/bin/env python3
"""
 Generate documentation from dbc file

 Copyright (c) 2023 ROX Automation - Jev Kuznetsov
"""

from odrive_can import get_dbc


def dbc_to_markdown(db, markdown_file_path, name):
    """create documentation from dbc database"""

    print(f"Generating {markdown_file_path}")
    # Open the Markdown file for writing
    with open(markdown_file_path, "w", encoding="utf8") as md_file:
        # Write a header
        md_file.write(f"## {name}  interface\n\n")

        # Iterate over messages
        for message in db.messages:
            md_file.write(f"### ID: {message.frame_id} - {message.name}\n")
            md_file.write(f"- Name: {message.name}\n")
            md_file.write(f"- Length: {message.length} bytes\n")
            md_file.write(f"- Sender: {message.senders}\n\n")

            if message.frame_id <= 29:
                # Write a table header for signals
                md_file.write(
                    "| Signal Name | Start Bit | Length | Factor | Offset | Min Value | Max Value | Unit | Receiver | Choices |\n"
                )
                md_file.write(
                    "|-------------|-----------|--------|--------|--------|-----------|-----------|------|----------|---------|\n"
                )

                # Iterate over signals
                for signal in message.signals:
                    choices_str = (
                        ", ".join(f"{k}: {v}" for k, v in signal.choices.items())
                        if signal.choices
                        else ""
                    )
                    md_file.write(
                        f"| {signal.name} | {signal.start} | {signal.length} | {signal.scale} | {signal.offset} | {signal.minimum} | {signal.maximum} | {signal.unit or ''} | {', '.join(signal.receivers)} | {choices_str} |\n"
                    )

                # Add a newline after each message
                md_file.write("\n")


name = "odrive-cansimple-0.5.6"
db = get_dbc(name)
dbc_to_markdown(db, f"{name}.md", name)

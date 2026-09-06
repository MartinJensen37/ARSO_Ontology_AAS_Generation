"""Regenerates EA-MI-LF120-EN_MQTT_Interface.pdf (the LinFill-120 MQTT interface
spec test fixture) with two fixes:

1. The previous version of this PDF had a text-encoding bug (UTF-8 bytes fed to
   ReportLab after being mis-decoded as Latin-1 somewhere upstream), corrupting
   every accented character in the manufacturer address ("BrÃ¼ckenstraÃe" instead
   of "Brückenstraße"). This script builds every string as a native Python str
   (no manual .encode()/.decode() round-trips) so ReportLab's default
   Helvetica/WinAnsiEncoding renders them correctly -- WinAnsiEncoding covers
   ü/ß/· natively, so no font substitution is needed.

2. The MQTT topic structure has been redesigned to match the real InnoLab
   MQTT_classes.ResponseAsync/Publisher pattern (confirmed against actual
   Dispensing/Stoppering proxy scripts): each command gets its own
   {base}/CMD/<Action> (subscribe) + {base}/DATA/<Action> (publish) topic pair
   with JSON payloads correlated by a "Uuid" field, rather than one shared
   command topic taking a bare string payload. QoS is 2 (matching the real
   proxies) rather than 1.

Run: python generate_linfill120_mqtt_pdf.py
"""
from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether,
)

import os
_OUT = Path(os.environ.get("LINFILL120_PDF_OUT") or (Path(__file__).resolve().parents[1] / "equipment" / "filling_module" / "EA-MI-LF120-EN_MQTT_Interface.pdf"))

_NAVY = colors.Color(0.10196100175380707, 0.20784300565719604, 0.34509798884391785)
_BLUE = colors.Color(0.176, 0.416, 0.624)
_LIGHT_GRAY = colors.Color(0.9568629860877991, 0.9568629860877991, 0.9568629860877991)
_WHITE = colors.white
_TEXT_GRAY = colors.Color(0.35, 0.35, 0.35)

_COMPANY = "Elara Automation GmbH"
_ADDRESS = "Brückenstraße 14, 70173 Stuttgart, Germany"
_FOOTER_LEFT = f"{_COMPANY}  ·  {_ADDRESS}"

_styles = getSampleStyleSheet()
_body = ParagraphStyle("Body", parent=_styles["Normal"], fontName="Helvetica", fontSize=9, leading=13, spaceAfter=6, textColor=colors.black)
_body_italic = ParagraphStyle("BodyItalic", parent=_body, fontName="Helvetica-Oblique", fontSize=7.5, leading=10, textColor=_TEXT_GRAY)
_h1 = ParagraphStyle("H1", parent=_styles["Heading1"], fontName="Helvetica-Bold", fontSize=13, leading=16, spaceBefore=14, spaceAfter=8, textColor=_NAVY)
_h2 = ParagraphStyle("H2", parent=_styles["Heading2"], fontName="Helvetica-Bold", fontSize=10.5, leading=13, spaceBefore=10, spaceAfter=6, textColor=_NAVY)
_note = ParagraphStyle("Note", parent=_body, fontName="Helvetica-Oblique", fontSize=8.5, leading=12)
_cell = ParagraphStyle("Cell", parent=_body, fontSize=8.5, leading=11, spaceAfter=0)
_cell_head = ParagraphStyle("CellHead", parent=_cell, fontName="Helvetica-Bold", textColor=_WHITE)
_cell_bold = ParagraphStyle("CellBold", parent=_cell, fontName="Helvetica-Bold")
_cover_title = ParagraphStyle("CoverTitle", parent=_styles["Title"], fontName="Helvetica-Bold", fontSize=26, leading=30, textColor=_WHITE, alignment=TA_CENTER)
_cover_sub = ParagraphStyle("CoverSub", parent=_body, fontName="Helvetica", fontSize=13, leading=17, textColor=_WHITE, alignment=TA_CENTER, spaceAfter=4)


def _table(data, col_widths, header_rows=1, para_cells=True):
    if para_cells:
        rendered = []
        for r_i, row in enumerate(data):
            out_row = []
            for c_i, val in enumerate(row):
                if isinstance(val, str):
                    style = _cell_head if r_i < header_rows else (_cell_bold if c_i == 0 else _cell)
                    out_row.append(Paragraph(val, style))
                else:
                    out_row.append(val)
            rendered.append(out_row)
        data = rendered
    t = Table(data, colWidths=col_widths, repeatRows=header_rows)
    style = [
        ("BACKGROUND", (0, 0), (-1, header_rows - 1), _BLUE),
        ("TEXTCOLOR", (0, 0), (-1, header_rows - 1), _WHITE),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.Color(0.8, 0.8, 0.8)),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("ROWBACKGROUNDS", (0, header_rows), (-1, -1), [_WHITE, _LIGHT_GRAY]),
    ]
    t.setStyle(TableStyle(style))
    return t


def _footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(_TEXT_GRAY)
    canvas.drawString(62.36, 40, _FOOTER_LEFT)
    canvas.drawRightString(532.91, 40, f"Page {doc.page}")
    canvas.setStrokeColor(colors.Color(0.8, 0.8, 0.8))
    canvas.line(62.36, 50, 532.91, 50)
    canvas.restoreState()


def _cover_page(canvas, doc):
    canvas.saveState()
    # Dark navy banner
    canvas.setFillColor(_NAVY)
    page_h = A4[1]
    canvas.rect(62.36, page_h - 252.69, 532.91 - 62.36, 252.69 - 62.69, fill=1, stroke=0)
    canvas.restoreState()
    _footer(canvas, doc)


def build() -> None:
    doc = SimpleDocTemplate(
        str(_OUT), pagesize=A4,
        leftMargin=62.36, rightMargin=A4[0] - 532.91,
        topMargin=70, bottomMargin=60,
        title="LinFill-120 MQTT Interface Specification",
    )

    story: list = []

    # ---------------------------------------------------------------- Cover
    story.append(Spacer(1, 60))
    story.append(Paragraph("LinFill-120 Vertical Syringe Filling<br/>Station", _cover_title))
    story.append(Spacer(1, 10))
    story.append(Paragraph("LinFill Series · Elara Automation GmbH", _cover_sub))
    story.append(Paragraph("MQTT Interface Specification", _cover_sub))
    story.append(Spacer(1, 90))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.Color(0.85, 0.45, 0.15), spaceAfter=12))
    story.append(Paragraph(
        "This specification defines the complete MQTT 3.1.1 communication interface of the LinFill-120 Vertical "
        "Syringe Filling Station. It is intended for control engineers, SCADA/MES integrators, and Unified "
        "Namespace architects who need to connect the station to a supervisory system or data infrastructure.",
        _body,
    ))
    story.append(Paragraph(
        "All information in this document refers to firmware version 1.5.0 and later, which introduced the "
        "correlated command/response topic pattern described in Sections 3-5. Firmware versions prior to 1.5.0 "
        "used a single shared command topic and are not compatible with this specification -- see "
        "EA-LC-LF120-EN Lifecycle Information Document for the firmware upgrade path.",
        _body,
    ))
    story.append(Spacer(1, 16))
    meta_data = [
        ["Document No.", "EA-MI-LF120-EN", "Revision", "2.0"],
        ["Release Date", "2026-02-18", "Language", "English (EN)"],
        ["Manufacturer", "Elara Automation GmbH —\nwww.elara-automation.de", "Status", "Released"],
    ]
    meta_rendered = [[Paragraph(f"<b>{r[0]}</b>", _cell), Paragraph(r[1], _cell), Paragraph(f"<b>{r[2]}</b>", _cell), Paragraph(r[3], _cell)] for r in meta_data]
    meta_table = Table(meta_rendered, colWidths=[85, 175, 65, 145])
    meta_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), _LIGHT_GRAY),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.white),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 14))
    story.append(Paragraph(
        "© 2026 Elara Automation GmbH. All rights reserved. This document and the information contained "
        "herein are the property of Elara Automation GmbH. Reproduction, disclosure, or use without prior "
        "written authorisation of Elara Automation GmbH is strictly prohibited. The information is provided in "
        "good faith and is believed to be accurate at the time of publication. Elara Automation GmbH reserves "
        "the right to modify specifications without notice. Product names and logos are trademarks of their "
        "respective owners.",
        _body_italic,
    ))
    story.append(PageBreak())

    # ---------------------------------------------------------- About / Conventions
    story.append(Paragraph("About This Document", _h1))
    story.append(Paragraph(
        "This document has been prepared by Elara Automation GmbH and is intended for qualified technical "
        "personnel responsible for the installation, commissioning, operation, and maintenance of the equipment "
        "described herein. Readers are expected to be familiar with general principles of industrial automation, "
        "electrical safety, and network-connected laboratory equipment.",
        _body,
    ))
    story.append(Paragraph(
        "The document is structured as a reference manual. Sections are broadly ordered to follow the typical "
        "lifecycle of the equipment — from first delivery through to end-of-life disposal — but individual "
        "sections may be read in isolation. Cross-references are provided where information in one section "
        "depends on material covered elsewhere.",
        _body,
    ))
    story.append(Paragraph(
        "Elara Automation GmbH maintains a document register at https://elara-automation.de/documents. The "
        "latest revision of this document may be retrieved from that register using the document number "
        "printed on the cover page. Printed copies are uncontrolled; always verify the revision status before "
        "use.",
        _body,
    ))
    story.append(Paragraph("Conventions Used in This Document", _h2))
    story.append(Paragraph("The following conventions are used throughout:", _body))
    conv_data = [
        ["Notation", "Meaning"],
        ["{serialNumber}", "The unit's serial number as printed on the rear label (e.g. EA-PS-2024-00391)"],
        ["{base}", "The site-specific topic prefix, e.g. NN/Nybrovej/InnoLab/Filling, configured during commissioning"],
        ["Uuid", "A client-generated correlation identifier included in every command payload and echoed back in the matching response payload"],
        ["NOTE", "Supplementary information that aids understanding but is not safety-critical"],
        ["CAUTION", "Risk of equipment damage or process disruption if instruction is not followed"],
        ["WARNING", "Risk of personal injury if instruction is not followed"],
    ]
    story.append(_table(conv_data, [110, 372]))
    story.append(Spacer(1, 10))
    story.append(Paragraph("Related Documents", _h2))
    rel_data = [
        ["Document No.", "Title"],
        ["EA-LC-LF120-EN", "LinFill-120 Lifecycle Information Document"],
        ["EA-LN-SPL01-EN", "SPL-01 Line Description & Bill of Materials"],
    ]
    story.append(_table(rel_data, [130, 352]))
    story.append(PageBreak())

    # -------------------------------------------------------------- Introduction
    story.append(Paragraph("1 Introduction", _h1))
    story.append(Paragraph(
        "MQTT (Message Queuing Telemetry Transport, ISO/IEC 20922:2016) is a lightweight, publish-subscribe "
        "messaging protocol well suited to embedded devices with constrained resources and unreliable network "
        "connections. The LinFill-120 acts as an MQTT client and connects to a broker provided by the facility. "
        "It does not include an embedded broker; a separate broker (e.g. HiveMQ, Eclipse Mosquitto, EMQX) must "
        "be available on the facility network.",
        _body,
    ))
    story.append(Paragraph(
        "Every command the station accepts is issued and acknowledged as a correlated request/response pair: "
        "a client publishes a JSON command to a dedicated {base}/CMD/&lt;Action&gt; topic carrying a unique "
        "\"Uuid\" value, and the station publishes a JSON result to the corresponding {base}/DATA/&lt;Action&gt; "
        "topic once the command has been processed, echoing the same \"Uuid\" so the client can match the "
        "response to its request. This request/response pattern is used consistently across all Elara "
        "Automation InnoLab-integrated equipment.",
        _body,
    ))
    story.append(Paragraph(
        "The topic prefix — referred to as {base} throughout this document — is site-specific and configured "
        "during commissioning. There is no default value; the prefix must be agreed between the equipment "
        "owner and the system integrator before commissioning and recorded in the site namespace register "
        "(e.g. NN/Nybrovej/InnoLab/Filling for a station installed in the Nybrovej InnoLab).",
        _body,
    ))

    story.append(Paragraph("2 Transport and Connection Parameters", _h1))
    story.append(Paragraph(
        "The MQTT connection is carried over TCP using the device's 2.4 GHz WiFi interface (IEEE 802.11 b/g/n). "
        "The broker port number depends on whether TLS is in use. For development or isolated lab networks, "
        "plain TCP on port 1883 is acceptable; for production environments Elara Automation strongly recommends "
        "MQTTS on port 8883 with mutual TLS certificate authentication.",
        _body,
    ))
    trans_data = [
        ["Protocol version", "MQTT 3.1.1 (ISO/IEC 20922:2016)"],
        ["Transport", "TCP/IP over IEEE 802.11 b/g/n WiFi, 2.4 GHz band"],
        ["Default port (plain)", "1883"],
        ["Recommended port (TLS)", "8883 with TLS 1.2 or higher"],
        ["Client ID", "linfill120-{serialNumber} — e.g. linfill120-EA-LF-2024-00472"],
        ["Clean Session", "false (persistent session; QoS 2 subscriptions survive reconnects)"],
        ["QoS (all topics)", "2 (exactly once) — required for command/response correlation, see Section 4"],
        ["Keep-alive interval", "60 seconds (broker will detect offline device after 90 s)"],
        ["Reconnect strategy", "Exponential back-off starting at 1 s, doubling up to 60 s maximum"],
        ["Authentication", "Username / password pair, set during provisioning. TLS client certificate supported in addition to or instead of password."],
    ]
    story.append(_table(trans_data, [140, 342], header_rows=0))

    story.append(Paragraph("2.1 Last Will and Testament", _h2))
    story.append(Paragraph(
        "The client registers a Last Will and Testament (LWT) message at connection time. If the station "
        "disconnects unexpectedly — due to power loss, WiFi drop, or firmware watchdog reset — the broker will "
        "publish the LWT payload to the state topic after the keep-alive timeout expires. Supervisory systems "
        "should subscribe to the state topic with a retained-message handler so that the last known state is "
        "immediately available on (re)subscribe.",
        _body,
    ))
    lwt_data = [
        ["LWT topic", "{base}/DATA/State"],
        ["LWT payload", '{"State": "ERROR"}'],
        ["LWT QoS", "2 (exactly once)"],
        ["LWT retain", "true"],
    ]
    story.append(_table(lwt_data, [140, 342], header_rows=0))
    story.append(PageBreak())

    # -------------------------------------------------------------- Topic Hierarchy
    story.append(Paragraph("3 Topic Hierarchy", _h1))
    story.append(Paragraph(
        "All topics used by the LinFill-120 are relative to the {base} prefix. Each command has its own "
        "subscribe (CMD) and publish (DATA) topic pair; two additional DATA topics carry continuous state and "
        "streamed weight telemetry that are not tied to a single command.",
        _body,
    ))
    topic_data = [
        ["Full Topic (relative to {base})", "Direction", "QoS", "Retained?"],
        ["/CMD/Start", "Device subscribes", "2", "No"],
        ["/DATA/Start", "Device publishes", "2", "No"],
        ["/CMD/Stop", "Device subscribes", "2", "No"],
        ["/DATA/Stop", "Device publishes", "2", "No"],
        ["/CMD/Home", "Device subscribes", "2", "No"],
        ["/DATA/Home", "Device publishes", "2", "No"],
        ["/CMD/Reset", "Device subscribes", "2", "No"],
        ["/DATA/Reset", "Device publishes", "2", "No"],
        ["/DATA/State", "Device publishes", "2", "Yes"],
        ["/DATA/CycleTime", "Device publishes", "2", "No"],
        ["/DATA/Weight", "Device publishes", "2", "No"],
    ]
    story.append(_table(topic_data, [160, 130, 60, 132]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("4 Command / Response Pattern", _h1))
    story.append(Paragraph(
        "Every CMD payload is a JSON object containing at minimum a \"Uuid\" string (client-generated, unique "
        "per request). The station processes the command and publishes a JSON object to the matching DATA "
        "topic, echoing the same \"Uuid\" plus a \"TimeStamp\" (ISO 8601, UTC, millisecond precision, "
        "e.g. 2026-02-18T14:32:07.501Z) and a \"State\" field of either \"SUCCESS\" or \"FAILURE\". Commands "
        "received in an incompatible station state (e.g. Start while RUNNING) result in \"FAILURE\" with no "
        "state change. No parameters beyond \"Uuid\" are required for any of the four commands below.",
        _body,
    ))
    cmd_data = [
        ["Command", "Valid when State is", "Resulting state sequence", "Notes"],
        ["Start", "IDLE", "IDLE -> RUNNING -> IDLE", "CycleTime and Weight streamed during the cycle; DATA/Start confirms cycle start, not completion"],
        ["Stop", "RUNNING", "RUNNING -> IDLE", "Halts cycle; lift retracts. CycleTime NOT published for the interrupted cycle."],
        ["Home", "Any", "* -> HOMING -> IDLE", "Should be issued once on power-on before first Start"],
        ["Reset", "ERROR", "ERROR -> IDLE", "Clears fault flag; does not re-home"],
    ]
    story.append(_table(cmd_data, [55, 90, 130, 207]))
    story.append(PageBreak())

    # -------------------------------------------------------------- Payload schemas
    story.append(Paragraph("5 Payload Reference", _h1))
    story.append(Paragraph("5.1 Command Payloads ({base}/CMD/&lt;Action&gt;)", _h2))
    story.append(Paragraph("All four command topics share the same minimal payload shape:", _body))
    cmd_payload_data = [
        ["Field", "Type", "Meaning"],
        ["Uuid", "string", "Client-generated correlation identifier (UUIDv4 recommended). Echoed back in the DATA response."],
    ]
    story.append(_table(cmd_payload_data, [90, 70, 322]))
    story.append(Spacer(1, 8))
    story.append(Paragraph("Example — {base}/CMD/Start:", _note))
    story.append(Paragraph('{"Uuid": "3f2a9e6c-1b4d-4e2a-9c7f-8a1d2e3f4b5c"}', ParagraphStyle("Code", parent=_body, fontName="Helvetica", fontSize=8.5, textColor=_NAVY, leftIndent=12)))

    story.append(Paragraph("5.2 Response Payloads ({base}/DATA/&lt;Action&gt;)", _h2))
    resp_payload_data = [
        ["Field", "Type", "Meaning"],
        ["Uuid", "string", "Copied unchanged from the triggering command payload"],
        ["TimeStamp", "string", "ISO 8601 UTC timestamp with millisecond precision and 'Z' suffix"],
        ["State", "string", '"SUCCESS" or "FAILURE"'],
    ]
    story.append(_table(resp_payload_data, [90, 70, 322]))
    story.append(Spacer(1, 8))
    story.append(Paragraph("Example — {base}/DATA/Start:", _note))
    story.append(Paragraph(
        '{"Uuid": "3f2a9e6c-1b4d-4e2a-9c7f-8a1d2e3f4b5c", "TimeStamp": "2026-02-18T14:32:07.501Z", "State": "SUCCESS"}',
        ParagraphStyle("Code", parent=_body, fontName="Helvetica", fontSize=8.5, textColor=_NAVY, leftIndent=12),
    ))

    story.append(Paragraph("5.3 Telemetry Payloads", _h2))
    story.append(Paragraph(
        "{base}/DATA/State carries the station's current operational mode. It is published on every state "
        "change (event-driven) and retained by the broker, so a new subscriber immediately receives the most "
        "recent value.",
        _body,
    ))
    state_data = [
        ["Payload value", "Meaning", "Entry conditions"],
        ["\"IDLE\"", "Ready; all actuators at rest", "After successful Home; after cycle completion; after Stop; after Reset clears error"],
        ["\"RUNNING\"", "Fill cycle in progress", "Start command accepted while State == IDLE"],
        ["\"ERROR\"", "Fault latched; motion inhibited", "Limit-switch timeout; motor stall; L298N thermal shutdown; LWT published by broker"],
        ["\"HOMING\"", "Lift performing homing sequence", "Home command accepted; also entered automatically at power-on"],
    ]
    story.append(_table(state_data, [70, 155, 257]))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        "{base}/DATA/Weight streams the syringe weight reading continuously while State == RUNNING (not a "
        "single post-fill reading) so supervisory systems can chart the fill curve in real time. Payload: "
        '{"Weight": &lt;grams, float&gt;, "TimeStamp": &lt;ISO 8601&gt;, "Uuid": &lt;the Start command\'s Uuid&gt;}. '
        "From firmware v1.5.0, this requires an external balance connected to the ESP32 UART; the topic is "
        "silent if no balance is fitted.",
        _body,
    ))
    story.append(Paragraph(
        "{base}/DATA/CycleTime is published once per cycle, immediately after State transitions from RUNNING "
        'to IDLE following a successful fill. Payload: {"CycleTime_s": &lt;seconds, float, 2 decimal places&gt;, '
        '"TimeStamp": &lt;ISO 8601&gt;, "Uuid": &lt;the Start command\'s Uuid&gt;}. Not published if the cycle is '
        "interrupted by Stop or if the station faults during a cycle.",
        _body,
    ))
    story.append(PageBreak())

    # -------------------------------------------------------------- Security
    story.append(Paragraph("6 Security Recommendations", _h1))
    story.append(Paragraph(
        "The default configuration (unencrypted TCP, username/password authentication) is adequate for "
        "isolated development networks. Before connecting the station to any production or GxP-regulated "
        "network, the following additional measures should be considered.",
        _body,
    ))
    for label, text in [
        ("TLS encryption", "Enable MQTTS on port 8883. Provision the broker CA certificate onto the ESP32 via the provisioning UI. Consider mutual TLS (client certificate on the device) to authenticate the device to the broker."),
        ("Access control lists", "Restrict the client ID linfill120-{serialNumber} on the broker to publish/subscribe only to {base}/CMD/# and {base}/DATA/# and no other topics."),
        ("Network segmentation", "Place filling stations on a dedicated IoT VLAN with firewall rules restricting MQTT traffic to the authorised broker IP address only."),
        ("Credential rotation", "Change device passwords and rotate certificates at least annually, or following any personnel change that had access to the credentials."),
        ("Broker hardening", "Disable anonymous access on the broker. Log all connect and disconnect events. Set broker-side keep-alive expiry slightly longer than the device keep-alive (90 s is appropriate for a 60 s device keep-alive)."),
        ("Uuid uniqueness", "Client Uuid values must be unique per outstanding request; reusing a Uuid before receiving its response will make correlation ambiguous."),
    ]:
        story.append(Paragraph(f"-  <b>{label}:</b> {text}", _body))

    story.append(Paragraph("7 Integration Checklist", _h1))
    story.append(Paragraph(
        "The following checklist may be used as a quick commissioning aide-memoire. It does not replace the "
        "full OQ protocol.",
        _body,
    ))
    checklist = [
        "Broker reachable from device subnet; firewall permits TCP 1883 or 8883",
        "Client ID linfill120-{serialNumber} is unique on the broker",
        "{base} prefix agreed with namespace owner and recorded",
        "LWT configured; test by powering off device and confirming State=ERROR appears on DATA/State",
        "SCADA/MES subscribes to DATA/State with retained-message support",
        "SCADA/MES subscribes to DATA/CycleTime and DATA/Weight",
        "SCADA/MES generates a fresh Uuid per command and matches it against the DATA/<Action> response",
        "All four commands tested; state transitions verified per Section 4",
        "TLS and ACL configured for production use",
        "Firmware version confirmed as 1.5.0 or later before go-live (required for CMD/DATA topic pattern)",
    ]
    check_data = [["#", "Item", "Done?"]] + [[str(i + 1), item, "□"] for i, item in enumerate(checklist)]
    check_table = _table(check_data, [24, 420, 40])
    story.append(check_table)
    story.append(PageBreak())

    # -------------------------------------------------------------- Support
    story.append(Paragraph("8 Technical Support", _h1))
    story.append(Paragraph(
        "For integration support, firmware files, or to report unexpected behaviour, contact Elara Automation "
        "GmbH using the details below. When raising a support ticket please include the unit serial number, "
        "the firmware version visible in the provisioning web interface, and a description of the MQTT broker "
        "software and version in use.",
        _body,
    ))
    story.append(Spacer(1, 10))
    contact_lines = [
        "<b>Elara Automation GmbH</b>",
        "Brückenstraße 14, 70173 Stuttgart, Germany",
        "Tel: +49 711 4920 0 · Fax: +49 711 4920 99",
        "support@elara-automation.de",
        "www.elara-automation.de",
        "Business hours: Monday–Friday 08:00–17:00 CET",
    ]
    contact_table = Table([[Paragraph("<br/>".join(contact_lines), _body)]], colWidths=[470])
    contact_table.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 1, colors.Color(0.176, 0.416, 0.624)),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(contact_table)

    doc.build(story, onFirstPage=_cover_page, onLaterPages=_footer)
    print(f"Wrote {_OUT}")


if __name__ == "__main__":
    build()

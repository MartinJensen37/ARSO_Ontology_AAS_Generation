"""
Field-by-field comparison of AAS outputs vs ground truth for effort scoring.
Usage: python -m evaluation.effort_check
"""
import json
import re
from pathlib import Path

BASE = Path("evaluation/results/model-comparison-v2e")
FLASH = Path("evaluation/results/flash-filling-retry")

experiments = [
    ("Sonnet", "filling", BASE / "v2-filling_module__claude-claude-sonnet-4-6__json-description__full__v2__rep01"),
    ("Haiku",  "filling", BASE / "v2-filling_module__claude-claude-haiku-4-5-20251001__json-description__full__v2__rep01"),
    ("GemPro", "filling", BASE / "v2-filling_module__gemini-gemini-3.1-pro-preview__json-description__full__v2__rep01"),
    ("Flash",  "filling", FLASH / "v2-filling_module__gemini-gemini-3-flash-preview__json-description__full__v2__rep01"),
    ("Sonnet", "stopper", BASE / "v2-stoppering_module__claude-claude-sonnet-4-6__json-description__full__v2__rep01"),
    ("Haiku",  "stopper", BASE / "v2-stoppering_module__claude-claude-haiku-4-5-20251001__json-description__full__v2__rep01"),
    ("GemPro", "stopper", BASE / "v2-stoppering_module__gemini-gemini-3.1-pro-preview__json-description__full__v2__rep01"),
    ("Flash",  "stopper", BASE / "v2-stoppering_module__gemini-gemini-3-flash-preview__json-description__full__v2__rep01"),
]

# (label, patterns, is_negative_check)
FILLING_CHECKS = [
    ("NP/ManufacturerName",     ["Elara Automation"], False),
    ("NP/ProductDesignation",   ["LinFill-120", "LinFill120"], False),
    ("NP/ContactInformation",   ["ContactInformation"], False),
    ("NP/ContactInfo/Stuttgart",["Stuttgart"], False),
    ("NP/OrderCode",            ["EA-LF120-230V-EU"], False),
    ("NP/SerialNumber",         ["EA-LF-2024-00472"], False),
    ("HS/ArcheType=OneDown",    ["OneDown"], False),
    ("HS/EntryNode",            ["EntryNode"], False),
    ("HS/ESP32",                ["ESP32", "esp32"], False),
    ("HS/L298N",                ["L298N"], False),
    ("HS/LiftMotor",            ["LiftMotor"], False),
    ("HS/LeadScrew",            ["LeadScrew", "LeadScrewAssembly"], False),
    ("AID/InterfaceMQTT",       ["InterfaceMQTT"], False),
    ("AID/EndpointMetadata",    ["EndpointMetadata"], False),
    ("AID/InteractionMetadata", ["InteractionMetadata"], False),
    ("AID/FillingState",        ["FillingState", "filling/state"], False),
    ("AID/Command",             ["filling/cmd"], False),
    ("Skills/Start",            ["idShort.*Start", "Start.*idShort"], False),
    ("Skills/Stop",             ["idShort.*Stop", "Stop.*idShort"], False),
    ("Skills/Home",             ["idShort.*Home", "Home.*idShort"], False),
    ("Cap/CapabilitySet",       ["CapabilitySet"], False),
    ("Cap/SyringeFilling",      ["SyringeFilling", "Syringe.*Fill"], False),
    ("OD/FillingState",         ["FillingState"], False),
    # negative checks
    ("!opc.tcp",                ["opc\\.tcp"], True),
    ("!OPC UA",                 ["OPC UA"], True),
    ("!ns=1",                   ["ns=1;"], True),
    ("!PlungerSet",             ["PlungerSet"], True),
]

STOPPER_CHECKS = [
    ("NP/ManufacturerName",     ["Elara Automation"], False),
    ("NP/ProductDesignation",   ["PlungerSet-80", "PlungerSet80"], False),
    ("NP/ContactInformation",   ["ContactInformation"], False),
    ("NP/ContactInfo/Stuttgart",["Stuttgart"], False),
    ("NP/OrderCode",            ["EA-PS080-230V-EU"], False),
    ("NP/SerialNumber",         ["EA-PS-2024-00391"], False),
    ("HS/ArcheType=OneDown",    ["OneDown"], False),
    ("HS/EntryNode",            ["EntryNode"], False),
    ("HS/ESP32",                ["ESP32", "esp32"], False),
    ("HS/L298N",                ["L298N"], False),
    ("HS/LiftMotor",            ["LiftMotor"], False),
    ("HS/LeadScrew",            ["LeadScrew"], False),
    ("HS/LinearInsertActuator", ["LinearInsert"], False),
    ("HS/ServoFeedMotor",       ["ServoFeed"], False),
    ("AID/InterfaceOPCUA",      ["InterfaceOPCUA"], False),
    ("AID/EndpointMetadata",    ["EndpointMetadata"], False),
    ("AID/InteractionMetadata", ["InteractionMetadata"], False),
    ("AID/State-prop",          ["State"], False),
    ("AID/Start-action",        ["i=4010", "i=4010"], False),
    ("AID/Stop-action",         ["i=4011"], False),
    ("AID/Home-action",         ["i=4012"], False),
    ("Skills/Start",            ["idShort.*Start", "Start.*idShort"], False),
    ("Skills/Stop",             ["idShort.*Stop", "Stop.*idShort"], False),
    ("Skills/Home",             ["idShort.*Home", "Home.*idShort"], False),
    ("Cap/CapabilitySet",       ["CapabilitySet"], False),
    ("Cap/PlungerInsertion",    ["PlungerInsertion", "Stoppering"], False),
    ("OD/FillingState",         ["FillingState", "StopperingState", "State"], False),
    # negative checks
    ("!MQTT",                   ["mqtt", "MQTT"], True),
    ("!broker",                 ["broker"], True),
    ("!LinFill",                ["LinFill"], True),
]

def check(text, patterns):
    for p in patterns:
        if re.search(p, text):
            return True
    return False


for model, equip, exp_dir in experiments:
    aas_file = exp_dir / "aas_output.json"
    metrics_file = exp_dir / "metrics.json"
    if not aas_file.exists():
        print(f"{model}/{equip}: NO AAS OUTPUT")
        continue
    text = aas_file.read_text(encoding="utf-8")
    m = {}
    if metrics_file.exists():
        row = json.loads(metrics_file.read_text())
        m = row.get("metrics", {})
    v_final = m.get("shacl_violation_count", 0)
    conforms = m.get("shacl_conforms", False)

    checks = FILLING_CHECKS if equip == "filling" else STOPPER_CHECKS

    missing = []
    neg_fails = []
    for label, patterns, is_neg in checks:
        found = check(text, patterns)
        if is_neg and found:
            neg_fails.append(label)
        elif not is_neg and not found:
            missing.append(label)

    print(f"\n=== {model:8s} / {equip} | conforms={str(conforms):5s}, V_final={v_final} ===")
    print(f"  Missing:     {missing}")
    print(f"  Neg-fails:   {neg_fails}")

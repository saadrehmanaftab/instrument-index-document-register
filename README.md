# Instrument index and document register tool

Personal project by Saad Ur Rehman, November 2026. **The plant, its instruments, vendors and documents are all
assumed.** Nothing comes from a real plant, employer or manufacturer.

A small database driven engineering tool: it stores the instruments and manufacturer documents of an assumed 4 stack
electrolysis plant in SQLite, then writes the instrument index, the I/O list with spare capacity and the document
register to one Excel workbook, together with an issues list.

## Run

```
pip install numpy pandas openpyxl
python register_tool.py
```

Outputs: `plant.db` (SQLite), `engineering_lists.xlsx` (sheets InstrumentIndex, IOList, DocumentRegister, Issues),
`results.json`. The seed is fixed (2026), so a rerun reproduces the numbers on the CV.

## Result of the run (assumed data)

| Item | Value |
|---|---|
| Instruments | 87 across 4 stacks and the balance of plant, 10 instrument types |
| I/O used | 37 AI, 4 AO, 32 DI, 14 DO |
| I/O installed with 20% spare | 45 AI, 5 AO, 39 DI, 17 DO |
| Manufacturer documents | 18 of 20 expected received |
| Tags without a manufacturer datasheet | 6 (all gas analyzers, type AT) |
| Documents not yet approved | 10 (in review or returned with comments) |

## Assumptions (all placeholders)

- Instrument set per stack: 3 temperature, 2 pressure, 1 flow, 1 level and 1 gas analyzer transmitter, 1 cooler
  control valve, 3 isolation valves with 6 end position switches, 1 local emergency stop.
- Balance of plant: 2 header pressure, 2 hydrogen purity, 1 water flow, 2 vent valves, 4 gas detectors.
- Vendors are named Vendor A to Vendor E. One datasheet and one manual are expected per instrument type.
- Not received (assumed): the gas analyzer datasheet and the gas detector manual.
- Review status of received documents is drawn at random with a fixed seed.
- Spare I/O is 20% per signal type, rounded up.

## Limits

Tags use a simple area.typeNumber scheme, not a plant standard. No loop diagrams, cable lists or control
narratives. The tool shows the method of a database driven register, not a real plant's engineering data.

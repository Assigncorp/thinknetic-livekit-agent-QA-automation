# resources/

Everything the agent test bed reads. Nothing here is code.

```
resources/
├── kb/                          knowledge bases the agent is grounded on
│   ├── vhrs28.md                Variable hopper, RC-28   (anchor serial K7170)
│   ├── vhrs36.md                Variable hopper, RC-36   (anchor serial K6757)
│   ├── fhrc28.md                Fixed hopper,    RC-28   (anchor serial K7174)
│   ├── fhrc36.md                Fixed hopper,    RC-36   (anchor serial K6758)
│   └── troubleshooting-general.md   shared M-218-08R guide, no serial of its own
│
├── serials/
│   └── hopper-classification.xlsx   the serial list (Parent Part Numbers)
│
└── generated/                   DO NOT EDIT - rebuilt by `make resources`
    ├── serial-index.json        serial -> knowledge base
    └── scenarios.json           caller questions extracted from each KB
```

## Renaming or adding a file

Nothing reads these paths directly. Edit **`config/testbed.config.json`** and run
`make resources`:

```jsonc
"knowledgeBases": [
  { "id": "vhrs28", "file": "vhrs28.md", "controller": "RC28", "hopperType": "VARIABLE",
    "anchorSerial": "K7170", "enabled": true }
]
```

- **Renamed a KB file?** change `file`.
- **Added a fifth machine?** add an entry with its `controller` + `hopperType`; the
  serial index routes to it automatically from the workbook.
- **Retiring one temporarily?** set `enabled: false` — no files need moving.

## How a serial finds its knowledge base

The workbook's `*_Classified` sheets label each Parent Part Number `VARIABLE` or
`FIXED`. The sheet it sits on gives the controller family (RC28 or RC36). Those two
facts together pick the KB:

| Controller | Hopper | Knowledge base |
|---|---|---|
| RC28 | VARIABLE | `vhrs28` |
| RC36 | VARIABLE | `vhrs36` |
| RC28 | FIXED | `fhrc28` |
| RC36 | FIXED | `fhrc36` |

That is what makes serial rotation possible — roughly 950 classified part numbers
are usable, not just the four anchors.

## Scenario extraction

Three shapes are recognised in the KB markdown, all declared as regexes in the config:

| Pattern | Source | Becomes |
|---|---|---|
| `**Q: ...**` | FAQ sections | a direct caller question |
| `### Q: ...` | how-to / troubleshooting entries | a direct caller question |
| `## Problem N — ...` | general troubleshooting guide | the entry's `**Symptoms:**` line, i.e. what a caller would actually say |

Each scenario also carries `expectAnchors` — distinctive terms lifted from the KB's own
answer (part numbers, pin references, pressures). They are **not asserted by default**;
flip `assertions.checkExpectedAnchors` when you want content checking and can accept
false failures on valid paraphrases.

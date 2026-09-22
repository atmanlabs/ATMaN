# SOUP Phase 2 — 10-turn prompt token measure (BEFORE fix)

Session turns: 10
Trace rows: 10

## Per-turn wall
- turn 1: 3106.2 ms | 'Good morning, Operator.'
- turn 2: 4156.6 ms | "Good morning, Operator. It's nice to see you're up and about. I'll keep us in sync w"
- turn 3: 3736.1 ms | 'I can assist with various tasks such as finding information, playing games like '
- turn 4: 3265.7 ms | 'I understand you like sapphire blue. I can help you remember preferences and als'
- turn 5: 3197.4 ms | "I understand you like sapphire blue. Is there anything specific you'd like to di"
- turn 6: 4391.2 ms | 'Here is a summary of recent interactions and preferences:\n1. I can assist with f'
- turn 7: 4673.0 ms | 'Here is a summary of recent interactions and preferences:\n1. I can assist with f'
- turn 8: 4141.9 ms | 'Here is a summary of recent interactions and preferences:\n1. I can assist with f'
- turn 9: 4167.5 ms | 'Here is a summary of recent interactions and preferences:\n1. I can assist with f'
- turn 10: 4417.5 ms | 'Here is a summary of recent interactions and preferences:\n1. I can assist with f'

## Prompt curve

```
turn=1 system=4005 user=1654 total=5659 ~tok=1414 wfc_n=0 wfc_ch=20 psc_ch=1444
turn=2 system=3534 user=1742 total=5276 ~tok=1319 wfc_n=1 wfc_ch=109 psc_ch=1444
turn=3 system=4005 user=817 total=4822 ~tok=1205 wfc_n=2 wfc_ch=298 psc_ch=326
turn=4 system=4005 user=853 total=4858 ~tok=1214 wfc_n=3 wfc_ch=515 psc_ch=131
turn=5 system=3701 user=1081 total=4782 ~tok=1195 wfc_n=4 wfc_ch=741 psc_ch=142
turn=6 system=3973 user=1093 total=5066 ~tok=1266 wfc_n=5 wfc_ch=750 psc_ch=143
turn=7 system=3238 user=1318 total=4556 ~tok=1139 wfc_n=6 wfc_ch=985 psc_ch=151
turn=8 system=4005 user=1417 total=5422 ~tok=1355 wfc_n=7 wfc_ch=1083 psc_ch=144
turn=9 system=4005 user=1671 total=5676 ~tok=1419 wfc_n=8 wfc_ch=1327 psc_ch=141
turn=10 system=3365 user=1665 total=5030 ~tok=1257 wfc_n=9 wfc_ch=1330 psc_ch=137
```

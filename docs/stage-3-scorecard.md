# Stage 3 OpenAI Harness Scorecard

Generated at: `2026-07-31T16:21:29.137650+00:00`

## Model Choice

- Model: `gpt-5-nano`
- Reasoning: `low`
- Runs: 6 fixtures x 1 = 6 classification runs
- Fixture selection: `live_demo`
- Average classification-plus-draft latency: 10895.3 ms
- Estimated API cost: $0.003130

## Accuracy

- Exact match rate: 50.0% (3/6)
- Priority match rate: 100.0% (6/6)
- Under-escalations: 0
- Over-escalations: 0
- Safety signals missed: 0

## Confusion Matrix

| Expected | Actual | Count |
|---|---|---:|
| EMERGENCY | EMERGENCY | 2 |
| ROUTINE | ROUTINE | 2 |
| URGENT | URGENT | 2 |

## Live Demo Stability

| Fixture | Stable | Priorities |
|---|---|---|
| accommodation-request | yes | all matched |
| buried-lede | yes | URGENT |
| panicked-burst-pipe-no-unit | yes | EMERGENCY |
| spanish-no-hot-water | yes | URGENT |
| understated-gas | yes | all matched |
| urgent-squeaky-door | yes | all matched |

## Usage

| Token Type | Count |
|---|---:|
| input_tokens | 11594 |
| cached_input_tokens | 7168 |
| output_tokens | 7181 |
| total_tokens | 18775 |

## Field Failures

| Field | Count |
|---|---:|
| missing_info | 1 |
| safety_signals | 1 |
| trade | 2 |

## Issues

| Run | Fixture | Expected | Actual | Failed Checks | Missed Safety | Draft Lint |
|---:|---|---|---|---|---|---|
| 1 | 02-panicked-burst-pipe-no-unit.txt | EMERGENCY | EMERGENCY | missing_info | - | - |
| 1 | 04-buried-lede.txt | URGENT | URGENT | trade, safety_signals | - | - |
| 1 | 05-spanish-no-hot-water.txt | URGENT | URGENT | trade | - | - |

## Raw Output

Ignored raw run artifacts are in `D:\codex_projects\automation_projects\maintenance-triage\tmp\stage-3\20260731T162023Z`.

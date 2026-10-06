# EthiViz — Cultural Bias Analysis Platform

EthiViz is a pluralistic AI bias detection platform that analyses text and image data
through multiple ethical traditions simultaneously. Unlike Western-centric fairness tools,
EthiViz treats cultural values as first-class analytical dimensions — not optional filters.

The platform is the computational implementation of Brandon Scott Copeland's Bachelor's
thesis, *"Cross-Cultural Bias Detection in AI Systems: A Computational Framework for
Multi-Perspective Ethical Analysis"* (IU University of Applied Sciences, September 2025).

> **Project Governance Note:** To demonstrate end-to-end technical leadership and readiness as an **IT Project Manager**, this repository includes a dedicated directory containing full Project Management documentation (WBS, Risk Registers, Agile/Scrum artifacts, and Stakeholder Matrices). See the [Project Management Documentation](#project-management-documentation) section below.

---

## What Makes EthiViz Different

Most bias detection tools (including IBM AI Fairness 360, Fairlearn, and Google's What-If
Tool) measure fairness using a single standard — typically a Western liberal framework
centred on individual rights and statistical parity. EthiViz rejects this monoculture:

> A hiring algorithm can pass every Western fairness metric and still perpetuate bias
> from an Ubuntu, Confucian, or Islamic ethical perspective. EthiViz surfaces both.

EthiViz analyses content through **seven ethical lenses simultaneously**: Western, Ubuntu,
Confucian, Islamic, Buddhist, Hindu/Dharmic, and Indigenous/First Nations.

---

## Current Version: V5

**[`Ethiviz_V5/`](Ethiviz_V5/) is the current, actively maintained version** — a real
Flask API backend running the actual 7-lens `ethiviz` engine, paired with a React
frontend, with working start/stop scripts. See **[Ethiviz_V5/README.md](Ethiviz_V5/README.md)**
for full architecture, API reference, and setup details.

`Ethiviz_V2/`, `Ethiviz_V3/`, and `Ethiviz_V4/` are preserved in this repo as historical
snapshots of earlier iterations. They are not maintained and should not be used for new
work — the engine and web app inside `Ethiviz_V4/` were the basis V5 was built from, but
V5 is where active development now happens.

### Quick start

```bash
bash start_ethiviz.sh

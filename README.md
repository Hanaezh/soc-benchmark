# SecCoRA Benchmark: Security Operations Center (SOC) LLM Evaluation Dataset

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Paper](https://img.shields.io/badge/Paper-arXiv-red.svg)](https://arxiv.org/)


## Overview

This repository contains the benchmark datasets for assessing Large Language Models (LLMs) in Security Operations Center (SOC) workflows, as described in our research paper.

## Repository Structure

This repository is organized into two main components:

### 1. `internal_benchmark/` - Internal SOC Dataset (Question Templates Only)

**⚠️ Data Access: Template Release Only**

This directory contains **question templates and aggregated metadata** derived from our internal SOC environment. Due to confidentiality and security considerations, **raw operational data is not publicly disclosed**.

**Dataset Characteristics:**
- **Data Sources**: Honeypot logs, access behavior audits, security alerts, threat intelligence matching feeds
- **Observation Window**: 15-day period capturing 90% of attacker dwell time (aligning with Mandiant M-Trends reports)
- **Schema Complexity**: Heterogeneous schemas ranging from 11 to 28 fields across sources
- **Volume**: Large-scale datasets ranging from 16K to 31M records
- **Templates**: 1,250 distinct question templates covering 5 SOC analysis tasks

**Available Content:**
- Question templates for all 5 tasks
- Aggregated statistical metadata
- Schema definitions (field names and types only, no actual values)

**Access Request:**
Researchers interested in accessing the raw operational data under appropriate confidentiality agreements should contact the authors. Data sharing is subject to:
- Institutional affiliation verification
- Signed non-disclosure agreement
- Compliance with organizational security policies

📧 **Contact**: [Your Email] for data access inquiries

---

### 2. `linux_apt_benchmark/` - Open-Source APT Dataset (Full Data & QA Pairs)

**✅ Fully Open Source**

This directory contains a **complete open-source benchmark** built on the publicly available [Linux-APT-2024](https://github.com/) dataset, enabling reproducible research and community evaluation.

**Dataset Source:**
- **Base Dataset**: Linux-APT-2024 [Karim et al., 2024]
- **Citation**: Karim, S.S., Afzal, M., Iqbal, W., & Al Abri, D. (2024). Advanced Persistent Threat (APT) and intrusion detection evaluation dataset for linux systems 2024. *Data in Brief*, 54, 110290.



## License

- **Linux-APT-2024 Benchmark**: MIT License (see LICENSE file)
- **Internal Benchmark Templates**: Available for research use with proper attribution
- **Raw Operational Data**: Subject to organizational confidentiality agreements

## Contact

For questions about the benchmark, data access requests, or collaboration inquiries:

- 📧 **Email**: [XX@XX.edu.cn]
- 🏢 **Affiliation**: [XX]
- 🔗 **Project Page**: [XX]

## Acknowledgments

We thank the security operations team for providing the operational data and insights that informed this benchmark design. The Linux-APT-2024 dataset is courtesy of Karim et al. (2024).

---

**Note**: This benchmark is designed for research purposes in LLM evaluation for cybersecurity operations. Please use responsibly and in accordance with applicable security policies and regulations.

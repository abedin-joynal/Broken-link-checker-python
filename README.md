# Broken Link Checker

> **Python crawler + WordPress plugin** that recursively finds broken links on any website and visualizes results in a live report.

[![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)]()
[![WordPress](https://img.shields.io/badge/WordPress-21759B?style=flat-square&logo=wordpress&logoColor=white)]()

**Author:** [Joynal Abedin Parag](https://github.com/abedin-joynal) · Originally built for enterprise web QA

---

## Overview

Recursively crawls a website, detects broken links (404, 500, timeouts), and generates a visual report. Includes an optional **WordPress plugin** (`brokenlink-checker.php`) to run scans from the admin panel with real-time execution logs.

## Highlights (for recruiters)

- Recursive site crawler with broken link detection
- Real-time log streaming via WordPress integration
- Python scripts for session handling and link collection
- Built for production QA workflows at scale

## Project structure

```
├── brokenlink-checker.php    # WordPress plugin entry
├── python-scripts/
│   ├── linkcollector.py      # Recursive link crawler
│   ├── saveSSSession.py      # Session management
│   └── start.sh              # Launch script
├── js/main.js                # Frontend report UI
└── css/style.css
```

## Usage

### Standalone Python

```bash
cd python-scripts
pip install -r requirements.txt   # if available
./start.sh https://example.com
```

### WordPress plugin

1. Copy `brokenlink-checker.php` and supporting files to your WordPress plugins directory
2. Activate the plugin in WordPress admin
3. Run a scan from the plugin page — logs stream in real time

## Related projects

- [KGDCL Welfare Portal](https://github.com/abedin-joynal/kgdcl-welfare-portal) — Full-stack portal with REST API
- [Remote Testing Platform](https://github.com/abedin-joynal/Remote-Testing-Platform) — IoT QA @ Samsung R&D

## Author

**Joynal Abedin Parag** — [Portfolio](https://abedin-joynal.github.io) · [LinkedIn](https://linkedin.com/in/abedin-joynal)

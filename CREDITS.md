# Credits and Acknowledgments

fnerd-falconpy builds upon the excellent work of the digital forensics community. This project would not be possible without the following tools and contributors.

---

## Third-Party Tools

### KAPE (Kroll Artifact Parser and Extractor)

**KAPE** is a powerful Windows forensic artifact collection and processing tool created by **Eric Zimmerman**.

- **Author**: Eric Zimmerman (@EricZimmerman)
- **Website**: https://www.kroll.com/kape
- **Repository**: https://github.com/EricZimmerman/KapeFiles
- **License**: Free for personal and commercial use
- **Documentation**: https://ericzimmerman.github.io/KapeDocs/

**What fnerd-falconpy Uses**:
- KAPE binary for artifact collection on Windows endpoints
- KAPE Targets and Modules for artifact definitions
- Integration with CrowdStrike RTR for remote deployment and execution

**Acknowledgment**: Eric Zimmerman's KAPE has revolutionized Windows forensic artifact collection. His continuous development and the community-driven KapeFiles repository make rapid forensic triage accessible to incident responders worldwide.

---

### UAC (Unix-like Artifacts Collector)

**UAC** is a comprehensive forensic artifact collector for Unix-like systems (Linux, macOS, *BSD, Solaris, AIX).

- **Author**: Thiago Canozzo Lahr (@tclahr)
- **Repository**: https://github.com/tclahr/uac
- **License**: Apache License 2.0
- **Documentation**: https://github.com/tclahr/uac/wiki

**What fnerd-falconpy Uses**:
- UAC for artifact collection on Unix/Linux/macOS endpoints
- UAC profiles for different collection scenarios
- Integration with CrowdStrike RTR for remote deployment

**Acknowledgment**: Tclahr's UAC fills a critical gap in cross-platform forensics, providing a unified collection framework for Unix-like systems. The tool's flexibility and comprehensive artifact coverage make it invaluable for modern IR teams operating in heterogeneous environments.

---

## Core Dependencies

### CrowdStrike FalconPy

**FalconPy** is the official Python SDK for the CrowdStrike Falcon API.

- **Organization**: CrowdStrike
- **Repository**: https://github.com/CrowdStrike/falconpy
- **License**: The Unlicense
- **Documentation**: https://falconpy.io/

**Acknowledgment**: FalconPy provides the robust API interface that enables fnerd-falconpy to interact with CrowdStrike Falcon RTR. The excellent documentation and active maintenance by the CrowdStrike team make integration seamless.

---

### AWS SDK for Python (Boto3)

**Boto3** is the Amazon Web Services (AWS) SDK for Python.

- **Organization**: Amazon Web Services
- **Repository**: https://github.com/boto/boto3
- **License**: Apache License 2.0
- **Documentation**: https://boto3.amazonaws.com/v1/documentation/api/latest/index.html

**Acknowledgment**: Boto3 enables fnerd-falconpy's cloud storage integration, allowing forensic artifacts to be securely uploaded to S3-compatible storage.

---

## Community Contributions

### KAPE Community Targets and Modules

The KAPE Files repository contains hundreds of community-contributed targets and modules:

- **Repository**: https://github.com/EricZimmerman/KapeFiles
- **Contributors**: 100+ community members
- **Coverage**: Windows forensic artifacts from dozens of applications and system components

**Special Thanks**:
- All contributors to the KapeFiles repository
- The DFIR community for continuous artifact research and documentation

---

### UAC Community Contributions

The UAC project benefits from community feedback and contributions:

- **Contributors**: Community testers and contributors
- **Coverage**: Unix/Linux/macOS artifact collection across multiple platforms

---

## Inspiration and Prior Art

fnerd-falconpy was inspired by the need to:
1. **Scale forensic collections** using EDR infrastructure
2. **Unify collection workflows** across Windows and Unix platforms
3. **Leverage cloud storage** for artifact management
4. **Automate triage** for rapid incident response

The tool builds on concepts from:
- **GRR Rapid Response**: Scalable remote forensics framework
- **Velociraptor**: Endpoint visibility and collection platform
- **CyLR**: Live response collection tool

---

## Project Author

**fnerd-falconpy** is developed and maintained by **fnerd**.

- **Repository**: https://github.com/fnerd/fnerd-falconpy
- **License**: MIT License

---

## License Compliance

### KAPE
- **License**: Free for personal and commercial use
- **Distribution**: Not included in repository - users must obtain from official sources
- **Attribution**: Properly credited with links to official resources

### UAC
- **License**: Apache License 2.0
- **Distribution**: Not included in repository - users must obtain from official sources
- **Attribution**: Properly credited with links to official repository

### FalconPy
- **License**: The Unlicense (Public Domain)
- **Distribution**: Installed via pip/requirements.txt
- **Attribution**: Properly credited

### Boto3
- **License**: Apache License 2.0
- **Distribution**: Installed via pip/requirements.txt
- **Attribution**: Properly credited

### fnerd-falconpy
- **License**: MIT License
- **Distribution**: Open source via GitHub
- **Use**: Free for personal and commercial use with attribution

---

## How to Contribute

If you'd like to contribute to fnerd-falconpy:

1. Fork the repository
2. Create a feature branch
3. Submit a pull request
4. Follow the contribution guidelines in `CONTRIBUTING.md` (coming soon)

For KAPE or UAC contributions:
- **KAPE**: Submit targets/modules to https://github.com/EricZimmerman/KapeFiles
- **UAC**: Submit issues/PRs to https://github.com/tclahr/uac

---

## Disclaimer

fnerd-falconpy is an independent project and is not officially affiliated with, endorsed by, or sponsored by:
- CrowdStrike, Inc.
- Kroll, LLC
- Eric Zimmerman
- Thiago Canozzo Lahr (Tclahr)
- Amazon Web Services, Inc.

All trademarks, service marks, trade names, product names, and logos are the property of their respective owners.

---

## Thank You

To the entire DFIR community for continuous innovation, knowledge sharing, and tool development. Your work makes incident response faster, more effective, and more accessible to security teams worldwide.

**Special thanks to**:
- Eric Zimmerman for KAPE and the entire suite of forensic tools
- Tclahr for UAC and advancing Unix forensics
- The CrowdStrike team for Falcon and FalconPy
- All open-source contributors in the DFIR space

---

*Last Updated: 2025*

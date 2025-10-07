# Automated Forensic Analysis Pipeline - Implementation Guide

This document provides implementation guidance for the automated forensic analysis pipeline outlined in the executive summary.

## Integration with 4n6NerdStriker v1.1.0

### Current Capabilities Alignment

The 4n6NerdStriker v1.1.0 provides the foundation for the collection layer:

```python
# Automated collection based on platform detection
def automated_collection_workflow(alert_context, hostname):
    """Intelligent collection based on CrowdStrike alert"""
    
    orchestrator = OptimizedFalconForensicOrchestrator(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        max_concurrent_hosts=20
    )
    
    # Get host platform info
    host_info = orchestrator.get_host_info(hostname)
    
    if not host_info:
        return {"error": "Host not found"}
    
    # Platform-specific collection
    if host_info.platform.lower() == "windows":
        # Use KAPE with alert-specific targets
        kape_targets = get_kape_targets_for_alert(alert_context)
        result = orchestrator.run_kape_collection(
            hostname=hostname,
            target=kape_targets,
            upload=True
        )
    else:
        # Use UAC with alert-specific profile
        uac_profile = get_uac_profile_for_alert(alert_context)
        result = orchestrator.run_uac_collection(
            hostname=hostname,
            profile=uac_profile,
            upload=True
        )
    
    return {"success": result, "platform": host_info.platform}
```

### Alert-to-Collection Mapping

```python
# Alert type to collection profile mapping
ALERT_COLLECTION_MAPPING = {
    "malware_execution": {
        "windows": {"tool": "kape", "targets": ["WebBrowsers", "FileSystem", "RegistryHives"]},
        "unix": {"tool": "uac", "profile": "ir_triage"}
    },
    "lateral_movement": {
        "windows": {"tool": "kape", "targets": ["EventLogs", "RegistryHives", "NetworkLogs"]},
        "unix": {"tool": "uac", "profile": "network"}
    },
    "privilege_escalation": {
        "windows": {"tool": "kape", "targets": ["RegistryHives", "EventLogs", "SystemFiles"]},
        "unix": {"tool": "uac", "profile": "logs"}
    },
    "data_exfiltration": {
        "windows": {"tool": "kape", "targets": ["WebBrowsers", "NetworkLogs", "FileSystem"]},
        "unix": {"tool": "uac", "profile": "files"}
    }
}

def get_collection_strategy(alert_type, platform):
    """Get collection strategy based on alert type and platform"""
    return ALERT_COLLECTION_MAPPING.get(alert_type, {}).get(platform, {
        "tool": "uac" if platform != "windows" else "kape",
        "profile": "ir_triage" if platform != "windows" else "BasicCollection"
    })
```

## Pipeline Orchestration Framework

### Main Pipeline Controller

```python
import asyncio
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

class AlertSeverity(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

class DispositionAction(Enum):
    DISCARD = "discard"
    COLLECT_AND_ANALYZE = "collect_analyze"
    DEEP_TIMELINE = "deep_timeline"
    CONTACT_USER = "contact_user"
    SIRT_OPINION = "sirt_opinion"
    CLOSE_FALSE_POSITIVE = "close_fp"

@dataclass
class CrowdStrikeAlert:
    alert_id: str
    detection_name: str
    severity: AlertSeverity
    hostname: str
    username: str
    timestamp: str
    behaviors: List[str]
    device_info: Dict

@dataclass
class CollectionResult:
    success: bool
    artifact_location: str
    collection_tool: str
    collection_profile: str
    error_message: Optional[str] = None

class AutomatedForensicPipeline:
    def __init__(self, falcon_orchestrator):
        self.orchestrator = falcon_orchestrator
        self.dissect_engine = DissectAnalysisEngine()
        self.decision_engine = DispositionDecisionEngine()
        
    async def process_alert(self, alert: CrowdStrikeAlert) -> Dict:
        """Main pipeline entry point"""
        
        # Phase 1: Alert triage
        if alert.severity < AlertSeverity.MEDIUM:
            return {"action": DispositionAction.DISCARD, "reason": "Low severity"}
        
        # Phase 2: Collection decision
        collection_strategy = self.decide_collection_strategy(alert)
        
        # Phase 3: Automated collection
        collection_result = await self.execute_collection(alert, collection_strategy)
        
        if not collection_result.success:
            return {"action": "collection_failed", "error": collection_result.error_message}
        
        # Phase 4: Rapid analysis
        analysis_result = await self.dissect_engine.analyze_artifacts(
            collection_result.artifact_location,
            alert_context=alert
        )
        
        # Phase 5: Decision matrix
        disposition = self.decision_engine.determine_disposition(
            alert, collection_result, analysis_result
        )
        
        # Phase 6: Execute disposition
        return await self.execute_disposition(disposition, alert, analysis_result)
    
    def decide_collection_strategy(self, alert: CrowdStrikeAlert) -> Dict:
        """Determine what to collect based on alert characteristics"""
        
        # Get host platform
        host_info = self.orchestrator.get_host_info(alert.hostname)
        platform = host_info.platform.lower() if host_info else "unknown"
        
        # Map alert type to collection strategy
        alert_type = self.classify_alert_type(alert.detection_name)
        strategy = get_collection_strategy(alert_type, platform)
        
        return {
            "platform": platform,
            "tool": strategy.get("tool", "uac"),
            "profile": strategy.get("profile", "ir_triage"),
            "targets": strategy.get("targets", []),
            "priority": "high" if alert.severity >= AlertSeverity.HIGH else "normal"
        }
    
    async def execute_collection(self, alert: CrowdStrikeAlert, strategy: Dict) -> CollectionResult:
        """Execute artifact collection based on strategy"""
        
        try:
            if strategy["tool"] == "kape":
                success = self.orchestrator.run_kape_collection(
                    hostname=alert.hostname,
                    target=",".join(strategy["targets"]),
                    upload=True
                )
            else:  # UAC
                success = self.orchestrator.run_uac_collection(
                    hostname=alert.hostname,
                    profile=strategy["profile"],
                    upload=True
                )
            
            if success:
                # Generate S3 path based on naming convention
                artifact_location = self.generate_artifact_path(alert, strategy)
                return CollectionResult(
                    success=True,
                    artifact_location=artifact_location,
                    collection_tool=strategy["tool"],
                    collection_profile=strategy.get("profile", strategy.get("targets", ["unknown"])[0])
                )
            else:
                return CollectionResult(
                    success=False,
                    artifact_location="",
                    collection_tool=strategy["tool"],
                    collection_profile=strategy.get("profile", "unknown"),
                    error_message="Collection execution failed"
                )
                
        except Exception as e:
            return CollectionResult(
                success=False,
                artifact_location="",
                collection_tool=strategy["tool"],
                collection_profile=strategy.get("profile", "unknown"),
                error_message=str(e)
            )
```

## Dissect Integration Layer

```python
class DissectAnalysisEngine:
    def __init__(self):
        self.query_templates = self.load_query_templates()
    
    async def analyze_artifacts(self, artifact_location: str, alert_context: CrowdStrikeAlert) -> Dict:
        """Run contextual Dissect analysis"""
        
        # Download artifacts from S3 if needed
        local_path = await self.download_artifacts(artifact_location)
        
        # Select appropriate queries based on alert type
        queries = self.select_queries_for_alert(alert_context)
        
        # Execute Dissect queries
        results = {}
        for query_name, query_cmd in queries.items():
            try:
                result = await self.execute_dissect_query(local_path, query_cmd)
                results[query_name] = self.parse_dissect_output(result)
            except Exception as e:
                results[query_name] = {"error": str(e)}
        
        # Correlate findings
        correlation_results = self.correlate_findings(results, alert_context)
        
        return {
            "query_results": results,
            "correlations": correlation_results,
            "threat_indicators": self.extract_threat_indicators(results),
            "risk_score": self.calculate_risk_score(results, alert_context)
        }
    
    def select_queries_for_alert(self, alert: CrowdStrikeAlert) -> Dict[str, str]:
        """Select Dissect queries based on alert type"""
        
        alert_type = self.classify_alert_type(alert.detection_name)
        
        query_sets = {
            "malware_execution": {
                "processes": "target-query {path} -f processes | head -100",
                "mft": "target-query {path} -f mft | grep -i executable",
                "prefetch": "target-query {path} -f prefetch",
                "registry_run": "target-query {path} -f registry | grep -i 'run\\|start'"
            },
            "lateral_movement": {
                "auth_events": "target-query {path} -f evtx | grep -E '4624|4625|4648|4672'",
                "network": "target-query {path} -f network_connections",
                "users": "target-query {path} -f users",
                "rdp_registry": "target-query {path} -f registry | grep -i rdp"
            },
            "data_exfiltration": {
                "network": "target-query {path} -f network_connections",
                "browser": "target-query {path} -f browser_history",
                "file_access": "target-query {path} -f mft | grep -E 'Documents|Downloads'",
                "usb_devices": "target-query {path} -f registry | grep -i usbstor"
            }
        }
        
        return query_sets.get(alert_type, {
            "general_triage": "target-query {path} -f processes,evtx,network_connections | head -50"
        })
    
    async def execute_dissect_query(self, artifact_path: str, query_template: str) -> str:
        """Execute a Dissect query and return results"""
        
        import subprocess
        import asyncio
        
        query = query_template.format(path=artifact_path)
        
        # Execute query with timeout
        process = await asyncio.create_subprocess_shell(
            query,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=300)
            return stdout.decode() if process.returncode == 0 else stderr.decode()
        except asyncio.TimeoutError:
            process.kill()
            return "Query timeout after 5 minutes"
```

## Decision Engine Implementation

```python
class DispositionDecisionEngine:
    def __init__(self):
        self.threat_indicators = self.load_threat_indicators()
        self.false_positive_patterns = self.load_fp_patterns()
    
    def determine_disposition(self, alert: CrowdStrikeAlert, 
                            collection: CollectionResult, 
                            analysis: Dict) -> DispositionAction:
        """Main decision logic for alert disposition"""
        
        risk_score = analysis.get("risk_score", 0)
        threat_indicators = analysis.get("threat_indicators", [])
        
        # Critical threats - immediate deep analysis
        if risk_score >= 9 or self.has_critical_indicators(threat_indicators):
            return DispositionAction.DEEP_TIMELINE
        
        # Clear false positive patterns
        if self.is_likely_false_positive(analysis, alert):
            return DispositionAction.CLOSE_FALSE_POSITIVE
        
        # High risk but needs human verification
        if risk_score >= 7:
            return DispositionAction.SIRT_OPINION
        
        # Medium risk - contact user for context
        if risk_score >= 4:
            return DispositionAction.CONTACT_USER
        
        # Low risk - likely false positive
        return DispositionAction.CLOSE_FALSE_POSITIVE
    
    def has_critical_indicators(self, indicators: List[str]) -> bool:
        """Check for critical threat indicators requiring immediate action"""
        
        critical_patterns = [
            "known_malware_hash",
            "c2_communication",
            "lateral_movement_confirmed",
            "privilege_escalation_success",
            "data_exfiltration_detected",
            "ransomware_behavior"
        ]
        
        return any(indicator in critical_patterns for indicator in indicators)
    
    def is_likely_false_positive(self, analysis: Dict, alert: CrowdStrikeAlert) -> bool:
        """Determine if alert is likely a false positive"""
        
        fp_indicators = [
            "scheduled_task_execution",
            "software_update_activity", 
            "legitimate_admin_tools",
            "business_application_behavior",
            "known_safe_process"
        ]
        
        threat_indicators = analysis.get("threat_indicators", [])
        return any(fp in threat_indicators for fp in fp_indicators)
    
    def calculate_risk_score(self, analysis_results: Dict, alert: CrowdStrikeAlert) -> float:
        """Calculate comprehensive risk score (0-10)"""
        
        base_score = {
            AlertSeverity.LOW: 2,
            AlertSeverity.MEDIUM: 4,
            AlertSeverity.HIGH: 7,
            AlertSeverity.CRITICAL: 9
        }.get(alert.severity, 2)
        
        # Adjust based on analysis findings
        modifiers = 0
        
        # Check for threat indicators
        threat_indicators = analysis_results.get("threat_indicators", [])
        if "malware_detected" in threat_indicators:
            modifiers += 2
        if "persistence_mechanism" in threat_indicators:
            modifiers += 1.5
        if "network_anomaly" in threat_indicators:
            modifiers += 1
        
        # Check for false positive indicators
        if "legitimate_software" in threat_indicators:
            modifiers -= 2
        if "scheduled_activity" in threat_indicators:
            modifiers -= 1
        
        return max(0, min(10, base_score + modifiers))
```

## Configuration and Deployment

### Pipeline Configuration

```yaml
# pipeline_config.yaml
pipeline:
  name: "Automated Forensic Analysis Pipeline"
  version: "1.0.0"
  
collection:
  tools:
    kape:
      enabled: true
      default_targets: ["BasicCollection", "WebBrowsers"]
      timeout: 3600
    uac:
      enabled: true
      default_profile: "ir_triage"
      timeout: 3600
  
  thresholds:
    min_severity: "MEDIUM"
    auto_collect_severity: "HIGH"
    max_concurrent_collections: 10

analysis:
  dissect:
    enabled: true
    timeout: 300
    max_artifact_size: "10GB"
  
  queries:
    malware_execution:
      - "processes"
      - "mft"
      - "prefetch"
      - "registry"
    lateral_movement:
      - "evtx"
      - "network_connections"
      - "users"

decision:
  risk_thresholds:
    deep_timeline: 7
    sirt_opinion: 5
    contact_user: 3
    false_positive: 2
  
  escalation:
    auto_escalate_critical: true
    max_queue_size: 100
    analyst_notification: true
```

### Deployment Scripts

```python
# deploy_pipeline.py
import asyncio
import yaml
from pathlib import Path

class PipelineDeployer:
    def __init__(self, config_path: str):
        with open(config_path) as f:
            self.config = yaml.safe_load(f)
    
    async def deploy(self):
        """Deploy the automated pipeline"""
        
        # Initialize 4n6NerdStriker orchestrator
        orchestrator = self.initialize_forensics_nerdstriker()
        
        # Set up Dissect environment
        await self.setup_dissect()
        
        # Configure decision engine
        decision_engine = self.setup_decision_engine()
        
        # Initialize main pipeline
        pipeline = AutomatedForensicPipeline(orchestrator)
        
        # Start monitoring for alerts
        await self.start_alert_monitoring(pipeline)
    
    def initialize_forensics_nerdstriker(self):
        """Initialize 4n6NerdStriker with configuration"""
        from forensics_nerdstriker import OptimizedFalconForensicOrchestrator
        
        return OptimizedFalconForensicOrchestrator(
            client_id=os.getenv("FALCON_CLIENT_ID"),
            client_secret=os.getenv("FALCON_CLIENT_SECRET"),
            max_concurrent_hosts=self.config["collection"]["max_concurrent_collections"]
        )
    
    async def start_alert_monitoring(self, pipeline):
        """Start monitoring CrowdStrike alerts"""
        
        # This would integrate with CrowdStrike's streaming API
        # or webhook endpoints to receive real-time alerts
        
        while True:
            try:
                # Get new alerts from CrowdStrike
                alerts = await self.get_new_alerts()
                
                # Process alerts concurrently
                tasks = [
                    pipeline.process_alert(alert) 
                    for alert in alerts
                ]
                
                if tasks:
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    await self.log_results(results)
                
                # Wait before next check
                await asyncio.sleep(30)
                
            except Exception as e:
                print(f"Error in alert monitoring: {e}")
                await asyncio.sleep(60)

if __name__ == "__main__":
    deployer = PipelineDeployer("pipeline_config.yaml")
    asyncio.run(deployer.deploy())
```

## Monitoring and Metrics

```python
class PipelineMetrics:
    def __init__(self):
        self.metrics = {
            "alerts_processed": 0,
            "collections_successful": 0,
            "false_positives_detected": 0,
            "deep_analysis_triggered": 0,
            "average_processing_time": 0,
            "error_rate": 0
        }
    
    def record_alert_processed(self, processing_time: float, success: bool):
        """Record metrics for processed alert"""
        self.metrics["alerts_processed"] += 1
        
        if success:
            self.metrics["collections_successful"] += 1
        
        # Update average processing time
        current_avg = self.metrics["average_processing_time"]
        count = self.metrics["alerts_processed"]
        self.metrics["average_processing_time"] = (
            (current_avg * (count - 1) + processing_time) / count
        )
    
    def generate_dashboard_data(self) -> Dict:
        """Generate data for monitoring dashboard"""
        return {
            "total_alerts": self.metrics["alerts_processed"],
            "success_rate": self.metrics["collections_successful"] / max(1, self.metrics["alerts_processed"]),
            "false_positive_rate": self.metrics["false_positives_detected"] / max(1, self.metrics["alerts_processed"]),
            "average_processing_time": self.metrics["average_processing_time"],
            "escalation_rate": self.metrics["deep_analysis_triggered"] / max(1, self.metrics["alerts_processed"])
        }
```

This implementation guide provides a practical framework for building the automated forensic analysis pipeline using the 4n6NerdStriker as the foundation. The modular design allows for incremental deployment and continuous improvement based on operational feedback.
from typing import List, Optional
from src.interfaces.anomaly_detector import IAnomalyDetector
from src.interfaces.fraud_rule import IFraudRule
from src.use_cases.fraud_rules.anomaly import VendorAnomalyRule
from src.use_cases.fraud_rules.billing import (
    ContractOverbillingRule, DuplicateBillingRule, OrphanInvoiceRule, PaymentDriftRule,
)
from src.use_cases.fraud_rules.flows import CircularFlowRule
from src.use_cases.fraud_rules.identifiers import SharedIdentifierRule
from src.use_cases.fraud_rules.realty import LeaseOverlapRule

def default_rules(anomaly_detector: Optional[IAnomalyDetector] = None) -> List[IFraudRule]:
    """Pass an anomaly detector (built at the composition root) to enable VendorAnomalyRule."""
    rules: List[IFraudRule] = [
        SharedIdentifierRule(),
        DuplicateBillingRule(),
        ContractOverbillingRule(),
        OrphanInvoiceRule(),
        PaymentDriftRule(),
        LeaseOverlapRule(),
        CircularFlowRule(),
    ]
    if anomaly_detector:
        rules.append(VendorAnomalyRule(anomaly_detector))
    return rules

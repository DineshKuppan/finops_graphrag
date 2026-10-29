from typing import List
from src.interfaces.fraud_rule import IFraudRule
from src.use_cases.fraud_rules.billing import (
    ContractOverbillingRule, DuplicateBillingRule, OrphanInvoiceRule, PaymentDriftRule,
)
from src.use_cases.fraud_rules.flows import CircularFlowRule
from src.use_cases.fraud_rules.identifiers import SharedIdentifierRule
from src.use_cases.fraud_rules.realty import LeaseOverlapRule

def default_rules() -> List[IFraudRule]:
    return [
        SharedIdentifierRule(),
        DuplicateBillingRule(),
        ContractOverbillingRule(),
        OrphanInvoiceRule(),
        PaymentDriftRule(),
        LeaseOverlapRule(),
        CircularFlowRule(),
    ]

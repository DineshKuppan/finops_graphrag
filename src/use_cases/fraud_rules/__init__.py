from typing import List
from src.interfaces.fraud_rule import IFraudRule
from src.use_cases.fraud_rules.billing import ContractOverbillingRule, DuplicateBillingRule
from src.use_cases.fraud_rules.identifiers import SharedIdentifierRule

def default_rules() -> List[IFraudRule]:
    return [
        SharedIdentifierRule(),
        DuplicateBillingRule(),
        ContractOverbillingRule(),
    ]

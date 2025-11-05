"""Domain-specific intelligent agents"""

from src.agents.medical.medical_agent import MedicalAgent
from src.agents.legal.legal_agent import LegalAgent
from src.agents.finance.finance_agent import FinanceAgent
from src.agents.education.education_agent import EducationAgent
from src.agents.ecommerce.ecommerce_agent import EcommerceAgent
from src.agents.customer_service.customer_service_agent import CustomerServiceAgent

__all__ = [
    "MedicalAgent",
    "LegalAgent",
    "FinanceAgent",
    "EducationAgent",
    "EcommerceAgent",
    "CustomerServiceAgent",
]

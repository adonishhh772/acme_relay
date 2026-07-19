from enum import StrEnum


class Role(StrEnum):
    SALES = "sales_user"
    SUPPORT = "support_user"
    OPERATIONS = "operations_user"
    ADMIN = "admin"


class RiskLevel(StrEnum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"

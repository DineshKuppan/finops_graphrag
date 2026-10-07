from dataclasses import dataclass, field


@dataclass
class User:
    """Internal user record. roles power RBAC; the rest power ABAC/PBAC."""

    id: str
    username: str
    password_hash: str
    full_name: str
    roles: list[str] = field(default_factory=list)
    department: str = ""
    clearance_level: int = 0
    region: str = ""

    def public_profile(self) -> dict:
        return {
            "id": self.id,
            "username": self.username,
            "full_name": self.full_name,
            "roles": self.roles,
            "attributes": {
                "department": self.department,
                "clearance_level": self.clearance_level,
                "region": self.region,
            },
        }

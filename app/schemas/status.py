from enum import StrEnum


class CaseStatus(StrEnum):
    ACTIVE = "ACTIVE"
    PENDING = "PENDING"
    DISPOSED = "DISPOSED"
    CLOSED = "CLOSED"
    STAYED = "STAYED"
    TRANSFERRED = "TRANSFERRED"

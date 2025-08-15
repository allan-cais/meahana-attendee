from enum import Enum


class MeetingStatus(str, Enum):
    PENDING = "PENDING"
    STARTED = "STARTED"
    FAILED = "FAILED"
    COMPLETED = "COMPLETED"

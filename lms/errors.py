"""Business errors. CONTRACT FILE.

Every rule violation raises BusinessRuleError. The UI catches it and shows
`st.error(err.message)` - never a stack trace.
"""

INVALID_DATES = "INVALID_DATES"            # end before start, or missing dates
START_IN_PAST = "START_IN_PAST"            # start_date < business_today()
PERIOD_TOO_LONG = "PERIOD_TOO_LONG"        # more than MAX_PERIOD_DAYS
NO_COPY_AVAILABLE = "NO_COPY_AVAILABLE"    # no in-service copy free for whole period
DUPLICATE_REQUEST = "DUPLICATE_REQUEST"    # member already has overlapping active request for title
INVALID_TRANSITION = "INVALID_TRANSITION"  # not allowed by ALLOWED_TRANSITIONS
NOT_AUTHORIZED = "NOT_AUTHORIZED"          # wrong role / not the owner
NOT_FOUND = "NOT_FOUND"                    # unknown id
ISSUE_NOT_ALLOWED = "ISSUE_NOT_ALLOWED"    # issue outside start..end window
REASON_REQUIRED = "REASON_REQUIRED"        # reject without a reason
LOGIN_FAILED = "LOGIN_FAILED"              # bad username/password


class BusinessRuleError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message

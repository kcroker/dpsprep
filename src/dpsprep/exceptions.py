class DpsPrepException(Exception):
    pass


class DpsPrepError(DpsPrepException):
    pass


class DpsPrepParseError(DpsPrepError):
    pass


class DpsPrepConfigError(DpsPrepError):
    pass


class DpsPrepConcurrencyError(DpsPrepError):
    pass

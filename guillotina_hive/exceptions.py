

class HiveError(Exception):
    pass


class NoTaskFunctionFoundError(HiveError):
    pass


class NoTaskFunctionValidError(HiveError):
    pass


class NoTaskFunctionDefinedError(HiveError):
    pass


class NoAvailableWorkers(HiveError):
    pass


class HiveNotInitialized(HiveError):
    pass


class WorkerNotFound(HiveError):
    pass


class TaskNotFound(HiveError):
    pass

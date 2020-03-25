class MissingPermissions(Exception):
    def __init__(self, msg):
        super().__init__("You are missing the permission(s): {}.".format(msg))


class NoAccess(Exception):
    def __init__(self, msg):
        super().__init__("No access: {}".format(msg))

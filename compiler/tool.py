PRINT_INDENT = 2


class Color:
    ok = '\33[38;5;34m' # 2 34 35
    red = '\33[38;5;1m'
    green = '\33[38;5;2m'
    orange = '\33[38;5;9m'
    yellow = '\33[38;5;11m'
    end = '\33[0m'


class CompilerError(Exception):
    def __init__(self, msg):
        self.msg = f"{Color.orange}CompilerError[{msg}]{Color.end}"

    def __str__(self):
        return self.msg
        # print(repr(self.msg))
        # return repr(self.msg)


# user code error
class CodeError(Exception):
    def __init__(self, msg):
        self.msg = f"{Color.orange}CodeError[{msg}]{Color.end}"
        self.raw_msg = msg

    def __str__(self):
        return self.msg
        # print(repr(self.msg))
        # return repr(self.msg)
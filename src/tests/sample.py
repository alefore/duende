class ComplexClass:
    def __init__(self):
        self.value = 0

    def increment(self):
        self.value += 1

    @staticmethod
    def utility_function(param1, param2):
        return param1 + param2

    class NestedClass:
        def __init__(self, data):
            self.data = data

        def process(self):
            def inner_function(x):
                return x * 2
            return inner_function(self.data)

def top_level_function(arg1, arg2):
    return arg1 * arg2
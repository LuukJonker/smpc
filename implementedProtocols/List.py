from SMPCbox import AbstractProtocol

class CustomList(list):
    def __init__(self, inp: str):
        clean = inp.replace("[", "").replace("]", "").replace(" ", "")
        items = clean.split(",")
        if items == ['']:
            items = []
        super().__init__(list(map(int, items)))


class List(AbstractProtocol):
    def __init__(self, list: CustomList):
        self.list = list
        super().__init__()

    def party_names(self) -> list[str]:
        return [str(i) for i in self.list]

    def input_variables(self) -> dict[str, list[str]]:
        input_vars = {}
        for name in self.party_names():
            input_vars[name] = ["value"]
        return input_vars

    def output_variables(self) -> dict[str, list[str]]:
        return {self.list[0]: ["sum"]}

    def __call__(self):
        pass

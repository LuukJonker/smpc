from PyQt5 import QtWidgets
import random
import gui


def generate_shares(inputs, randoms=None):
    outputs = []
    """Generate shares for a secret"""
    if randoms:
        shares = [randoms[0]]
        final_share = inputs[0] - randoms[0]
        shares.append(final_share)
        outputs.append(shares)

        shares = [randoms[1]]
        final_share = inputs[1] - randoms[1]
        shares.append(final_share)
        outputs.append(shares)
        return outputs

    for secret in inputs:
        shares = [random.randint(-1000, 1000) for _ in range(len(inputs) - 1)]
        final_share = secret - sum(shares)
        shares.append(final_share)
        outputs.append(shares)
    return outputs


def distribute(inputs):
    outputs = [list() for _ in inputs]
    for inp in inputs:
        for i, x in enumerate(inp):
            outputs[i].append(x)
    return outputs


def add(inputs):
    outputs = []
    for inp in inputs:
        outputs.append(sum(inp))

    return outputs


def reconstruct_secret(inputs):
    """Reconstruct the secret from shares"""
    return sum(inputs)


class OverviewView(gui.Ui_MainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.state = 0

    def setup(self, window):
        super().setupUi(window)

        self.run_button.clicked.connect(self.handle_run_click)
        self.step_button.clicked.connect(self.handle_step_click)
        self.reset_button.clicked.connect(self.handle_reset_click)

    def check_randoms(self):
        if not self.alice_random_inp.text().isdigit():
            self.alice_random_inp.setText(str(random.randint(-1000, 1000)))

        if not self.bob_random_inp.text().isdigit():
            self.bob_random_inp.setText(str(random.randint(-1000, 1000)))

    def handle_run_click(self):
        _should_stop = False

        try:
            alice = int(self.alice_secret_inp.text())
        except ValueError:
            self.alice_secret_inp.setText("")
            _should_stop = True

        try:
            bob = int(self.bob_secret_inp.text())
        except ValueError:
            self.bob_secret_inp.setText("")
            _should_stop = True

        if _should_stop:
            return

        self.check_randoms()

        state = [alice, bob]
        randoms = [int(self.alice_random_inp.text()), int(self.bob_random_inp.text())]
        state = generate_shares(state, randoms)
        self.gs_a1.setText(str(state[0][0]))
        self.gs_a2.setText(str(state[0][1]))
        self.gs_b1.setText(str(state[1][0]))
        self.gs_b2.setText(str(state[1][1]))

        self.ds_send_b1.setText(str(state[1][0]))
        self.ds_send_a2.setText(str(state[0][1]))

        state = distribute(state)
        self.ds_a1.setText(str(state[0][0]))
        self.ds_b1.setText(str(state[0][1]))
        self.ds_a2.setText(str(state[1][0]))
        self.ds_b2.setText(str(state[1][1]))

        state = add(state)
        self.add_ar.setText(str(state[0]))
        self.add_br.setText(str(state[1]))

        self.cr_send_br.setText(str(state[1]))
        state = reconstruct_secret(state)
        self.cr_r.setText(str(state))

    def handle_step_click(self):
        if self.state == 0:
            _should_stop = False

            try:
                alice = int(self.alice_secret_inp.text())
            except ValueError:
                self.alice_secret_inp.setText("")
                _should_stop = True

            try:
                bob = int(self.bob_secret_inp.text())
            except ValueError:
                self.bob_secret_inp.setText("")
                _should_stop = True

            if _should_stop:
                return

            self.check_randoms()

            self.between_state = [alice, bob]
            randoms = [
                int(self.alice_random_inp.text()),
                int(self.bob_random_inp.text()),
            ]
            state = self.between_state
            state = generate_shares(state, randoms)
            self.gs_a1.setText(str(state[0][0]))
            self.gs_a2.setText(str(state[0][1]))
            self.gs_b1.setText(str(state[1][0]))
            self.gs_b2.setText(str(state[1][1]))

            self.between_state = state

        elif self.state == 1:
            self.ds_send_b1.setText(str(self.between_state[1][0]))
            self.ds_send_a2.setText(str(self.between_state[0][1]))

        elif self.state == 2:
            state = self.between_state
            state = distribute(state)
            self.ds_a1.setText(str(state[0][0]))
            self.ds_b1.setText(str(state[0][1]))
            self.ds_a2.setText(str(state[1][0]))
            self.ds_b2.setText(str(state[1][1]))

            self.between_state = state

        elif self.state == 3:
            state = self.between_state
            state = add(state)
            self.add_ar.setText(str(state[0]))
            self.add_br.setText(str(state[1]))
            self.between_state = state

        elif self.state == 4:
            self.cr_send_br.setText(str(self.between_state[1]))
        elif self.state == 5:
            state = self.between_state
            state = reconstruct_secret(state)
            self.cr_r.setText(str(state))
            self.between_state = state

        self.state += 1

    def handle_reset_click(self):
        self.alice_secret_inp.setText("")
        self.alice_random_inp.setText("")
        self.bob_secret_inp.setText("")
        self.bob_random_inp.setText("")

        self.gs_a1.setText("")
        self.gs_a2.setText("")
        self.gs_b1.setText("")
        self.gs_b2.setText("")
        self.ds_send_b1.setText("")
        self.ds_send_a2.setText("")
        self.ds_a1.setText("")
        self.ds_b1.setText("")
        self.ds_a2.setText("")
        self.ds_b2.setText("")
        self.add_ar.setText("")
        self.add_br.setText("")
        self.cr_send_br.setText("")
        self.cr_r.setText("")

        self.state = 0


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = OverviewView()
    ui.setup(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())

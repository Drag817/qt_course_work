import sys
from random import randint

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication, QMainWindow


w_width = 350
w_height = 200


class Window(QMainWindow):
    def __init__(self):
        super(Window, self).__init__()

        self.setWindowTitle('Simple program')
        self.setGeometry(300, 150, w_width, w_height)

        self.new_text = QtWidgets.QLabel(self)

        self.main_text = QtWidgets.QLabel(self)
        self.main_text.setText('Base text')
        self.main_text.move(100, 100)
        self.main_text.adjustSize()

        self.btn = QtWidgets.QPushButton(self)
        self.btn.move(70, 150)
        self.btn.setText('Press me!')
        self.btn.setFixedWidth(200)
        self.btn.clicked.connect(self.move_label)

        self.counter = 0

    def add_label(self):
        self.new_text.setText('Second text')
        self.new_text.move(100, 50)
        self.new_text.adjustSize()

    def move_label(self):
        self.counter += 1
        self.main_text.move(randint(5, w_width-30), randint(0, w_height-10))
        self.main_text.setText(f'{self.counter}')


def application():
    app = QApplication(sys.argv)
    window = Window()

    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    application()

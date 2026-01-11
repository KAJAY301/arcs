import pyqtgraph as pg

from PyQt5.QtWidgets import QDockWidget

class LogDock(QDockWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Log")

        # Setting
        self.main_graph = pg.PlotWidget()
        self.setWidget(self.main_graph)
        self.main_graph.showGrid(x=True, y=True)
        self.main_graph.setYRange(-20, 20)

        # Draw y = 0
        h_line_pen = pg.mkPen('#999999', style=pg.QtCore.Qt.DashLine)
        h_line = pg.InfiniteLine(angle=0 , movable=False, pen = h_line_pen)
        self.main_graph.addItem(h_line)

        # Init data(for simulater)
        self.time    = [-200+i for i in range(200)]
        self.delta_x = [0 for _ in range(200)]
        self.delta_y = [0 for _ in range(200)]

        # add line name
        self.main_graph.addLegend()

        # set line style
        pen_x = pg.mkPen(color='#ff5555', width=2)
        pen_y = pg.mkPen(color='#5555ff', width=2)
        self.x_line = self.main_graph.plot(self.time, self.delta_x, name="X", pen = pen_x)
        self.y_line = self.main_graph.plot(self.time, self.delta_y, name="Y", pen = pen_y)

    def update_plot(self, data):
        print("update_plot")
        dx = data[1][0]-data[0][0]
        dy = data[1][1]-data[0][1]

        #self.time.pop(0)
        #self.time.append(QTime().currentTime())

        self.delta_x.pop(0)
        self.delta_x.append(dx)
        self.x_line.setData(self.time, self.delta_x)

        self.delta_y.pop(0)
        self.delta_y.append(dy)
        self.y_line.setData(self.time, self.delta_y)

        
        








        






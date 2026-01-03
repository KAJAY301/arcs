import pyqtgraph as pg

from PyQt5.QtWidgets import QDockWidget, QHBoxLayout, QLabel

class LogDock(QDockWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Log")

        # Setting
        self.main_graph = pg.PlotWidget()
        self.setWidget(self.main_graph)
        self.main_graph.showGrid(x=True, y=True)
        self.main_graph.setYRange(-10, 10)

        # Draw y = 0
        h_line_pen = pg.mkPen(color='#999999')
        h_line = pg.InfiniteLine(angle=0 , movable=False, pen = h_line_pen)
        self.main_graph.addItem(h_line)

        # Init data(for simulater)
        self.time    = [-60+i for i in range(60)]
        self.delta_x = [0 for _ in range(60)]
        self.delta_y = [0 for _ in range(60)]

        # add line name
        self.main_graph.addLegend()

        # set line style
        pen_x = pg.mkPen(color='#ff5555')
        pen_y = pg.mkPen(color='#5555ff')
        self.x_line = self.main_graph.plot(self.time, self.delta_x, name="X", pen = pen_x)
        self.y_line = self.main_graph.plot(self.time, self.delta_y, name="Y", pen = pen_y)

        

  

    def update_plot(self, dx_mm, dy_mm):
        self.delta_x = self.delta_x[1:]
        #self.delta_x.append(random.uniform(-5.0, 5.0))
        self.delta_x.append(dx_mm)
        self.x_line.setData(self.time, self.delta_x)
        self.delta_y = self.delta_y[1:]
        #self.delta_y.append(random.uniform(-5.0, 5.0))
        self.delta_x.append(dy_mm)
        self.y_line.setData(self.time, self.delta_y)
        








        






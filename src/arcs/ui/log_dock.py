import pyqtgraph as pg
from PyQt5.QtWidgets import QDockWidget, QHBoxLayout, QTextEdit, QWidget
from PyQt5.QtCore import QDateTime, QTimer
from collections import deque
import time

class LogDock(QDockWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Log")

        # UI Setup
        self.main_widget = QWidget()
        self.main_layout = QHBoxLayout(self.main_widget)
        self.main_text = QTextEdit()
        self.main_graph = pg.PlotWidget()
        self.main_layout.addWidget(self.main_text)
        self.main_layout.addWidget(self.main_graph)
        self.setWidget(self.main_widget)

        self.main_text.setReadOnly(True)
        self.main_text.setFixedWidth(400)
        self.main_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e; 
                color: #d4d4d4; 
                font-family: 'Consolas', 'Courier New';
                font-size: 8pt;
                border: 1px solid #333;
            }
        """)

        # Graph setup
        self.main_graph.showGrid(x=True, y=True)
        self.main_graph.setYRange(-20, 20)
        self.main_graph.setMouseEnabled(x=False, y=False)
        self.main_graph.setMenuEnabled(False)
        self.main_graph.hideButtons()

        # Horizontal reference line (y=0)
        h_line_pen = pg.mkPen('#999999', style=pg.QtCore.Qt.DashLine)
        h_line = pg.InfiniteLine(angle=0, movable=False, pen=h_line_pen)
        self.main_graph.addItem(h_line)

        # Data storage (circular buffer)
        self.window_duration = 180  # Display last 3 minutes (180 seconds)
        self.max_samples = 1000  # Max data points to store
        self.time_data = deque(maxlen=self.max_samples)
        self.delta_x_data = deque(maxlen=self.max_samples)
        self.delta_y_data = deque(maxlen=self.max_samples)
        
        # Timestamp tracking
        self.start_time = time.time()

        # Graph lines
        self.main_graph.addLegend()
        pen_x = pg.mkPen(color='#ff7777', width=2)
        pen_y = pg.mkPen(color='#7777ff', width=2)
        self.x_line = self.main_graph.plot([], [], name="X", pen=pen_x)
        self.y_line = self.main_graph.plot([], [], name="Y", pen=pen_y)

        # Independent render timer (500ms refresh rate)
        self.render_timer = QTimer()
        self.render_timer.timeout.connect(self._update_plot_display)
        self.render_timer.start(500)

    def _get_relative_time(self, timestamp=None):
        """Get relative time in seconds from start"""
        if timestamp is None:
            timestamp = time.time()
        return timestamp - self.start_time

    def _update_plot_display(self):
        """Timer-driven plot update - runs every 500ms independent of data arrival
        X-axis is fixed: -180s (left) to 0s (right, now)"""
        if len(self.time_data) == 0:
            return

        current_time = self._get_relative_time()
        
        # Convert all data to relative time (negative for past, 0 for now)
        relative_times = [t - current_time for t in self.time_data]
        
        # Filter data within [-window_duration, 0] range
        indices = [i for i, rt in enumerate(relative_times) 
                   if -self.window_duration <= rt <= 0]
        
        if not indices:
            # No data in current window
            self.x_line.setData([], [])
            self.y_line.setData([], [])
        else:
            # Extract visible data
            visible_times = [relative_times[i] for i in indices]
            visible_x = [self.delta_x_data[i] for i in indices]
            visible_y = [self.delta_y_data[i] for i in indices]
            
            # Update plot with visible data
            self.x_line.setData(visible_times, visible_x)
            self.y_line.setData(visible_times, visible_y)
        
        # Fixed X-axis display: [-180, 0]
        self.main_graph.setXRange(-self.window_duration, 0, padding=0)

    def update_plot(self, data):
        """Called when new inference data arrives"""
        timestamp = self._get_relative_time()
        
        # Calculate deltas
        dx = data[1][0] - data[0][0]
        dy = data[1][1] - data[0][1]
        
        # Store in circular buffers
        self.time_data.append(timestamp)
        self.delta_x_data.append(dx)
        self.delta_y_data.append(dy)
        
        # Render will be called by independent timer

    def add_log_message(self, level, message):
        """Add text log message"""
        timestamp = QDateTime.currentDateTime().toString("dd-MM HH:mm:ss")
        color = "#E03C3C" if level == "CRITICAL" else "#d4d4d4"
 
        log_html = f'<span style="color:#888; font-size:8pt;">{timestamp}</span> ' \
                   f'<b style="color:{color};">[{level}]</b> {message}'
        
        self.main_text.append(log_html)
        
        # Keep log manageable (max 100 lines)
        if self.main_text.document().blockCount() > 100:
            cursor = self.main_text.textCursor()
            cursor.movePosition(cursor.Start)
            cursor.select(cursor.BlockUnderCursor)
            cursor.removeSelectedText()
            cursor.deleteChar()

        # Scroll to bottom
        self.main_text.verticalScrollBar().setValue(
            self.main_text.verticalScrollBar().maximum()
        )








        






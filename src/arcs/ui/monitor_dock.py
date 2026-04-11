from PyQt5.QtWidgets import QDockWidget, QTableWidget, QTableWidgetItem, QHeaderView, QTextEdit

from arcs.utils.config_manager import load_json_config

class MonitorDock(QDockWidget):
    def __init__(self, parent=None):
        super().__init__("Monitor", parent)

        # Config Setup
        cfg = load_json_config()
        self.width = cfg.get("camera").get("width")

        """        
        # Widget Setup
        params = ["Line Rate", "Exposure Time", "Height", "Width"]
        row, col = len(params)+1, 2
        self.monitor_table = QTableWidget(row, col)
        self.monitor_table.setFrameShape(QTableWidget.NoFrame)
        self.monitor_table.verticalHeader().setVisible(False)
        #self.monitor_table.horizontalHeader().setVisible(False)
        self.setWidget(self.monitor_table)

        self.monitor_table.setItem(0, 0, QTableWidgetItem("Parameter"))
        self.monitor_table.setItem(0, 1, QTableWidgetItem("Value"))

        for i, name in enumerate(params, start=1):
            self.monitor_table.setItem(i, 0, QTableWidgetItem(name))
            self.monitor_table.setItem(i, 1, QTableWidgetItem("None"))

        self.monitor_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        """

        self.param_display = QTextEdit()
        self.param_display.setReadOnly(True)
        self.param_display.setStyleSheet("""
            QTextEdit {
                background-color: transparent;
                border: none;
                color: #AAAAAA; 
                font-size: 16px;
                font-family: 'Consolas';
            }
        """)
        self.setWidget(self.param_display)

    def update_params(self, ui_input: dict):
        cm_value     = ui_input.get('length_cm_input')     #cm
        speed_value  = ui_input.get('speed_input')         #m/min
        pixel_value  = ui_input.get('pixel_input')         #mm

        line_rate_hz = (speed_value*1000) / (pixel_value*60)   #line/s
        exposure_us  = max(1, int(1e6 / line_rate_hz))         #us
        target_height= int((cm_value*10) / pixel_value)        #pixels

        display_mode = "Zoom in"# Temporary

        html_content = f"""
            <div style="color: #AAAAAA; font-size: 16px; font-family: 'Consolas';">
                <b>Camera params:</b>
                <table style="width: 100%; border: none;">
                    <tr>
                        <td>&nbsp;&nbsp;Line Rate</td>
                        <td style="text-align: right;">{line_rate_hz:.2f} Hz</td>
                    </tr>
                    <tr>
                        <td>&nbsp;&nbsp;Exposure Time</td>
                        <td style="text-align: right;">{exposure_us} us</td>
                    </tr>
                    <tr>
                        <td>&nbsp;&nbsp;Height</td>
                        <td style="text-align: right;">{target_height} pix</td>
                    </tr>
                    <tr>
                        <td>&nbsp;&nbsp;Width</td>
                        <td style="text-align: right;">{self.width} pix</td>
                    </tr>
                </table>
                <br>
                <b>Display mode:</b><br>
                &nbsp;&nbsp;{display_mode}
            </div>
        """
        self.param_display.setHtml(html_content)
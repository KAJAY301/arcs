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
        self.param_display.setLineWrapMode(QTextEdit.NoWrap)
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

        mode = "Zoom in"# Temporary
        size = "640*640"
        f_model = "YOLOv8n"
        f_iou = 0.5
        f_conf = 0.5
        s_model = "CV2"
        s_iou = 0.5
        s_conf = 0.5# Temporary

        html_content = f"""
            <div style="color: #AAAAAA; font-size: 16px; font-family: 'Consolas';">
                <table style="width: 100%; border: none;">
                    <tr>
                        <td colspan="2"><b>Camera params:</b></td>
                    </tr>
                    <tr>
                        <td>&nbsp;&nbsp;Line Rate&nbsp;</td>
                        <td style="text-align: right;">{line_rate_hz:.2f} Hz</td>
                    </tr>
                    <tr>
                        <td>&nbsp;&nbsp;Exposure Time&nbsp;</td>
                        <td style="text-align: right;">{exposure_us} us</td>
                    </tr>
                    <tr>
                        <td>&nbsp;&nbsp;Height&nbsp;</td>
                        <td style="text-align: right;">{target_height} pix</td>
                    </tr>
                    <tr>
                        <td>&nbsp;&nbsp;Width&nbsp;</td>
                        <td style="text-align: right;">{self.width} pix</td>
                    </tr>
                    <tr>
                        <td colspan="2"><b>Display:</b></td>
                    </tr>
                    <tr>
                        <td>&nbsp;&nbsp;Mode&nbsp;</td>
                        <td style="text-align: right;">{mode}</td>
                    </tr>
                    <tr>
                        <td>&nbsp;&nbsp;Size&nbsp;</td>
                        <td style="text-align: right;">{size} pix</td>
                    </tr>
                    <tr>
                        <td colspan="2"><b>First Inference:</b></td>
                    </tr>
                    <tr>
                        <td>&nbsp;&nbsp;Model&nbsp;</td>
                        <td style="text-align: right;">{f_model}</td>
                    </tr>
                    <tr>
                        <td>&nbsp;&nbsp;Iou&nbsp;</td>
                        <td style="text-align: right;">{f_iou}</td>
                    </tr>
                    <tr>
                        <td>&nbsp;&nbsp;Conf&nbsp;</td>
                        <td style="text-align: right;">{f_conf}</td>
                    </tr>
                    <tr>
                        <td colspan="2"><b>Second Inference:</b></td>
                    </tr>
                    <tr>
                        <td>&nbsp;&nbsp;Model&nbsp;</td>
                        <td style="text-align: right;">{s_model}</td>
                    </tr>
                    <tr>
                        <td>&nbsp;&nbsp;Iou&nbsp;</td>
                        <td style="text-align: right;">{s_iou}</td>
                    </tr>
                    <tr>
                        <td>&nbsp;&nbsp;Conf&nbsp;</td>
                        <td style="text-align: right;">{s_conf}</td>
                    </tr>
                </table>
            </div>
        """
        self.param_display.setHtml(html_content)
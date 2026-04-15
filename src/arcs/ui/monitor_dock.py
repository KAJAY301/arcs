from PyQt5.QtWidgets import QDockWidget, QTableWidget, QTableWidgetItem, QHeaderView, QTextEdit

from arcs.utils.config_manager import load_json_config

class MonitorDock(QDockWidget):
    def __init__(self, parent=None):
        super().__init__("Monitor", parent)
        # Config Setup
        cfg = load_json_config()
        self.width = cfg.get("camera").get("width")
        self.display_mode = cfg.get("display").get("mode")
        self.display_size = cfg.get("display").get("size")
        self.first_inference_model = cfg.get('inference').get('first_inference_model')
        self.second_inference_model = cfg.get('inference').get('second_inference_model')
        self.first_model_conf = cfg.get('yolo').get('first_model_conf')
        self.first_model_iou = cfg.get('yolo').get('first_model_iou')
        if self.second_inference_model != "cv2":
            self.second_model_conf = cfg.get('yolo').get('second_model_conf')
            self.second_model_iou = cfg.get('yolo').get('second_model_iou')
        else:
            self.second_model_conf = "N/A"
            self.second_model_iou = "N/A"

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

    def update_setting_params(self, ui_input: dict):
        cm_value     = ui_input.get('length_cm_input')     #cm
        speed_value  = ui_input.get('speed_input')         #m/min
        pixel_value  = ui_input.get('pixel_input')         #mm

        self.line_rate_hz = (speed_value*1000) / (pixel_value*60)   #line/s
        self.exposure_us  = max(1, int(1e6 / self.line_rate_hz))         #us
        self.target_height= int((cm_value*10) / pixel_value)        #pixels

        self.render_html()
    
    def update_color_params(self, color_input: dict):
        self.white_b = color_input.get('white_b')
        self.white_g = color_input.get('white_g')
        self.white_r = color_input.get('white_r')
        self.color_threshold = color_input.get('color_threshold')
    
    def update_first_inference_model(self, model_name: str):
        self.first_inference_model = model_name
        self.render_html()

    def update_second_inference_model(self, model_name: str):
        self.second_inference_model = model_name
        if model_name == "cv2":
            self.second_model_conf = "N/A"
            self.second_model_iou = "N/A"
        else:
            cfg = load_json_config()
            self.second_model_conf = cfg.get('yolo').get('second_model_conf')
            self.second_model_iou = cfg.get('yolo').get('second_model_iou')
        self.render_html()

    def update_display_mode(self, mode: str):
        self.display_mode = mode
        self.render_html()

    def render_html(self):
        html_content = f"""
            <div style="color: #AAAAAA; font-size: 16px; font-family: 'Consolas';">
                <table style="width: 100%; border: none;">
                    <tr>
                        <td colspan="2"><b>Camera params:</b></td>
                    </tr>
                    <tr>
                        <td>&nbsp;&nbsp;Line Rate&nbsp;</td>
                        <td style="text-align: right;">{self.line_rate_hz:.2f} Hz</td>
                    </tr>
                    <tr>
                        <td>&nbsp;&nbsp;Exposure Time&nbsp;</td>
                        <td style="text-align: right;">{self.exposure_us} us</td>
                    </tr>
                    <tr>
                        <td>&nbsp;&nbsp;Height&nbsp;</td>
                        <td style="text-align: right;">{self.target_height} pix</td>
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
                        <td style="text-align: right;">{self.display_mode}</td>
                    </tr>
                    <tr>
                        <td>&nbsp;&nbsp;Size&nbsp;</td>
                        <td style="text-align: right;">{self.display_size[0]}x{self.display_size[1]} pix</td>
                    </tr>
                    <tr>
                        <td colspan="2"><b>First Inference:</b></td>
                    </tr>
                    <tr>
                        <td>&nbsp;&nbsp;Model&nbsp;</td>
                        <td style="text-align: right;">{self.first_inference_model}</td>
                    </tr>
                    <tr>
                        <td>&nbsp;&nbsp;Conf&nbsp;</td>
                        <td style="text-align: right;">{self.first_model_conf}</td>
                    </tr>
                    <tr>
                        <td>&nbsp;&nbsp;Iou&nbsp;</td>
                        <td style="text-align: right;">{self.first_model_iou}</td>
                    </tr>
                    <tr>
                        <td colspan="2"><b>Second Inference:</b></td>
                    </tr>
                    <tr>
                        <td>&nbsp;&nbsp;Model&nbsp;</td>
                        <td style="text-align: right;">{self.second_inference_model}</td>
                    </tr>
                    <tr>
                        <td>&nbsp;&nbsp;Conf&nbsp;</td>
                        <td style="text-align: right;">{self.second_model_conf}</td>
                    </tr>
                    <tr>
                        <td>&nbsp;&nbsp;Iou&nbsp;</td>
                        <td style="text-align: right;">{self.second_model_iou}</td>
                    </tr>
                </table>
            </div>
        """
        self.param_display.setHtml(html_content)
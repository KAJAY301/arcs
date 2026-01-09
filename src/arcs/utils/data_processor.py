
def pixel_to_pulse(f_pt, s_pt, pixel_size, mm_per_pulses_x, mm_per_pulses_y, deadband_mm):
        """
        convert pixel distance to motor pulses
        """
        dx, dy, pulses_x, pulses_y = 0, 0, 0, 0
        if f_pt and s_pt:
            dx_mm = (s_pt[0] - f_pt[0]) * pixel_size
            dy_mm = (s_pt[1] - f_pt[1]) * pixel_size

            if abs(dx_mm) < deadband_mm: dx_mm = 0
            if abs(dy_mm) < deadband_mm: dy_mm = 0

            if dx_mm != 0 or dy_mm != 0:
                dx, dy = 2, 2
                if dx_mm < 0:
                    dx_mm *= -1
                    dx = 1
                if dy_mm < 0:
                    dy_mm *= -1
                    dy = 1

                pulses_x = int(dx_mm / mm_per_pulses_x)
                pulses_y = int(dy_mm / mm_per_pulses_y)

                pulses_x = min(32767, pulses_x)
                pulses_y = min(32767, pulses_y)

        return dx, dy, pulses_x, pulses_y

    
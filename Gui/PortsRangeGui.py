from pygal import Bar

from Gui.Widgets import *
from Libs.Vars import *


class PortsHotView(Frame):
    def __init__(self, master: Misc):
        super(PortsHotView, self).__init__(master, width=700, height=375)

        self.main_canvas = Canvas(self, width=700, height=375)
        self.last_lines = []
        self.now_lines = []

        self.record_process_lock = Lock()
        self.draw_lock = Lock()
        self.draw_timer = time()
        self.ports_record: Dict[int, bool] = {i: False for i in range(1, 65536)}

        self.main_canvas.pack(fill=BOTH, expand=YES)

        self.main_canvas.bind("<Configure>", self.draw)

    def reset_view(self) -> None:
        with self.record_process_lock:
            self.ports_record: Dict[int, bool] = {i: False for i in range(1, 65536)}
        self.draw()

    def callback(self, port: int) -> None:
        """
        把此端口存在服务器记录到热力图上
        :return: None
        """
        with self.record_process_lock:
            self.ports_record[port] = True
        self.draw()

    def draw(self, event=None) -> None:
        """
        绘制热力图
        :return: None
        """
        if not event:
            if not (time() - self.draw_timer) > 0.8:
                return
        with self.draw_lock:
            with self.record_process_lock:
                resized = self.resize_data(list(self.ports_record.values()), 700)
            for i in range(len(resized)):
                length = resized[i]
                self.now_lines.append(
                    self.main_canvas.create_rectangle(i * 2, 0,
                                                      i * 2 + 2, length * 5,
                                                      fill="#FFFF00",
                                                      width=0))
            self.main_canvas.delete(*self.last_lines)
            self.last_lines = self.now_lines.copy()
            self.now_lines.clear()
            self.draw_timer = time()

    @staticmethod
    def resize_data(data: List[int], counts: int) -> List[int]:
        data_2d: List[List[int]] = []
        group_size = len(data) // counts
        for i in range(counts - 1):
            data_2d.append(data[i * group_size:(i + 1) * group_size])
        data_2d.append(data[(counts - 1) * group_size:])
        data_resized: List[int] = [sum(i) for i in data_2d]
        return data_resized

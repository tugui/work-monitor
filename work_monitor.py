import json
import os
import platform
import sys
from datetime import datetime

from pynput import keyboard, mouse
from PyQt5.QtCore import Qt, QTime, QTimer
from PyQt5.QtGui import QColor, QGuiApplication, QIcon, QPainter, QPixmap
from PyQt5.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    QSpinBox,
    QSystemTrayIcon,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
)


class SettingsDialog(QDialog):
    # ... (SettingsDialog 类保持不变，节省篇幅)
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("工作监控设置")
        self.setFixedWidth(350)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        work_layout = QHBoxLayout()
        work_layout.addWidget(QLabel("连续工作时长(分钟):"))
        self.work_duration = QSpinBox()
        self.work_duration.setRange(1, 180)
        self.work_duration.setValue(self.settings.get("work_duration", 45))
        work_layout.addWidget(self.work_duration)
        layout.addLayout(work_layout)

        repeat_layout = QHBoxLayout()
        repeat_layout.addWidget(QLabel("再次提醒间隔(分钟):"))
        self.repeat_interval = QSpinBox()
        self.repeat_interval.setRange(1, 120)
        self.repeat_interval.setValue(self.settings.get("repeat_interval", 30))
        repeat_layout.addWidget(self.repeat_interval)
        layout.addLayout(repeat_layout)

        idle_layout = QHBoxLayout()
        idle_layout.addWidget(QLabel("空闲判定时间(秒):"))
        self.idle_time = QSpinBox()
        self.idle_time.setRange(10, 300)
        self.idle_time.setValue(self.settings.get("idle_time", 180))
        idle_layout.addWidget(self.idle_time)
        layout.addLayout(idle_layout)

        time_layout = QHBoxLayout()
        self.start_time = QTimeEdit()
        self.start_time.setTime(
            QTime.fromString(self.settings.get("start_time", "09:00"), "HH:mm")
        )
        self.end_time = QTimeEdit()
        self.end_time.setTime(
            QTime.fromString(self.settings.get("end_time", "17:30"), "HH:mm")
        )
        time_layout.addWidget(QLabel("工作时段:"))
        time_layout.addWidget(self.start_time)
        time_layout.addWidget(QLabel("-"))
        time_layout.addWidget(self.end_time)
        layout.addLayout(time_layout)

        self.autostart_checkbox = QCheckBox("开机自动启动")
        self.autostart_checkbox.setChecked(self.check_autostart())
        layout.addWidget(self.autostart_checkbox)

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self.save_settings)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def save_settings(self):
        self.settings["work_duration"] = self.work_duration.value()
        self.settings["repeat_interval"] = self.repeat_interval.value()
        self.settings["idle_time"] = self.idle_time.value()
        self.settings["start_time"] = self.start_time.time().toString("HH:mm")
        self.settings["end_time"] = self.end_time.time().toString("HH:mm")
        if self.autostart_checkbox.isChecked():
            self.enable_autostart()
        else:
            self.disable_autostart()
        self.accept()

    def check_autostart(self):
        if platform.system() == "Windows":
            import winreg

            try:
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Software\Microsoft\Windows\CurrentVersion\Run",
                    0,
                    winreg.KEY_READ,
                )
                winreg.QueryValueEx(key, "WorkMonitor")
                return True
            except:
                return False
        return False

    def enable_autostart(self):
        if platform.system() == "Windows":
            import winreg

            path = os.path.abspath(sys.argv[0])
            cmd = f'pythonw.exe "{path}"' if path.endswith(".py") else f'"{path}"'
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_WRITE,
            )
            winreg.SetValueEx(key, "WorkMonitor", 0, winreg.REG_SZ, cmd)

    def disable_autostart(self):
        if platform.system() == "Windows":
            import winreg

            try:
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Software\Microsoft\Windows\CurrentVersion\Run",
                    0,
                    winreg.KEY_WRITE,
                )
                winreg.DeleteValue(key, "WorkMonitor")
            except:
                pass


class NotificationWindow(QWidget):
    def __init__(self, screen, is_repeat=False):
        super().__init__()
        self.screen = screen  # 指定弹出的屏幕
        self.is_repeat = is_repeat
        self.setWindowFlags(
            Qt.ToolTip | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.init_ui()

    def init_ui(self):
        # 1. 扩大弹窗尺寸以容纳大字号
        self.setFixedSize(1000, 382)
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 20, 30, 20)  # 增加内边距

        title_text = "⚠️ 仍在加班" if self.is_repeat else "🕐 休息提醒"
        title = QLabel(title_text)
        title.setStyleSheet(
            "font-size: 32px; font-weight: bold; color: #e74c3c;"
            if self.is_repeat
            else "font-size: 32px; font-weight: bold; color: #2c3e50;"
        )

        msg = (
            "您已工作很久了，\n请务必休息！"
            if self.is_repeat
            else "您已工作一段时间，\n该休息一下了！"
        )
        message = QLabel(msg)
        # 优化文字显示，防止折断
        message.setStyleSheet(
            "font-size: 32px; color: #34495e; font-family: 'Microsoft YaHei';"
        )
        message.setWordWrap(True)
        message.setAlignment(Qt.AlignCenter)

        layout.addWidget(title)
        layout.addStretch()  # 增加间距
        layout.addWidget(message)
        layout.addStretch()
        self.setLayout(layout)

        # 2. 修改定位逻辑，使其可以在不同屏幕的右下角弹出
        geom = self.screen.availableGeometry()
        x = geom.x() + geom.width() - self.width() - 20
        y = geom.y() + geom.height() - self.height() - 60
        self.move(x, y)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor(255, 255, 255, 252))  # 稍微提高不透明度
        border_color = QColor(231, 76, 60) if self.is_repeat else QColor(52, 152, 219)
        painter.setPen(border_color)
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 15, 15)


class WorkMonitor(QSystemTrayIcon):
    def __init__(self, app):
        # ... (图标初始化部分保持不变)
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor(52, 152, 219))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(0, 0, 64, 64)
        painter.setPen(QColor(255, 255, 255))
        font = painter.font()
        font.setBold(True)
        font.setPointSize(32)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "W")
        painter.end()

        super().__init__(QIcon(pixmap), app)
        self.app = app
        self.settings = self.load_settings()
        self.work_seconds = 0
        self.repeat_seconds = 0
        self.is_reminded = False
        self.last_activity = datetime.now()
        self.current_notifs = []

        self.init_menu()
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_work_status)
        self.timer.start(1000)
        self.setup_listeners()
        self.show()

    def init_menu(self):
        self.menu = QMenu()
        self.status_action = self.menu.addAction("状态: 检查中...")
        self.menu.addSeparator()
        self.menu.addAction("设置").triggered.connect(self.show_settings)
        self.menu.addAction("退出").triggered.connect(self.app.quit)
        self.setContextMenu(self.menu)

    def load_settings(self):
        try:
            with open("work_monitor_settings.json", "r") as f:
                return json.load(f)
        except:
            return {
                "work_duration": 45,
                "repeat_interval": 30,
                "idle_time": 180,
                "start_time": "09:00",
                "end_time": "17:30",
            }

    def setup_listeners(self):
        def on_act(*a):
            self.last_activity = datetime.now()

        self.m_l = mouse.Listener(on_move=on_act, on_click=on_act, on_scroll=on_act)
        self.m_l.start()
        self.k_l = keyboard.Listener(on_press=on_act)
        self.k_l.start()

    def check_work_status(self):
        now = datetime.now().time()
        start = QTime.fromString(self.settings["start_time"], "HH:mm").toPyTime()
        end = QTime.fromString(self.settings["end_time"], "HH:mm").toPyTime()

        if not (start <= now <= end):
            self.status_action.setText("状态: 非工作时间")
            self.reset_counters()
            return

        idle_sec = (datetime.now() - self.last_activity).total_seconds()

        if idle_sec < self.settings["idle_time"]:
            if not self.is_reminded:
                self.work_seconds += 1
                self.status_action.setText(
                    f"状态: 工作中 ({self.work_seconds // 60}min)"
                )
                if self.work_seconds >= self.settings["work_duration"] * 60:
                    self.trigger_alert(is_repeat=False)
            else:
                self.repeat_seconds += 1
                rem_min = self.settings["repeat_interval"] - (self.repeat_seconds // 60)
                self.status_action.setText(f"状态: 建议休息 (再次提醒: {rem_min}min)")
                if self.repeat_seconds >= self.settings["repeat_interval"] * 60:
                    self.trigger_alert(is_repeat=True)
        else:
            self.reset_counters()
            self.status_action.setText("状态: 休息中")

    def trigger_alert(self, is_repeat=False):
        self.is_reminded = True
        self.repeat_seconds = 0

        # 3. 核心修改：获取所有屏幕并弹出窗体
        screens = QGuiApplication.screens()
        for screen in screens:
            notif = NotificationWindow(screen, is_repeat=is_repeat)
            notif.show()
            self.current_notifs.append(notif)
            # 增加停留时间到30秒 (30000 毫秒)
            QTimer.singleShot(30000, lambda n=notif: self.close_notif(n))

    def reset_counters(self):
        self.work_seconds = 0
        self.repeat_seconds = 0
        self.is_reminded = False

    def close_notif(self, n):
        try:
            n.close()
            if n in self.current_notifs:
                self.current_notifs.remove(n)
        except:
            pass

    def show_settings(self):
        if SettingsDialog(self.settings).exec_():
            with open("work_monitor_settings.json", "w") as f:
                json.dump(self.settings, f)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    m = WorkMonitor(app)
    sys.exit(app.exec_())

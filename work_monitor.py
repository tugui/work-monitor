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

SETTINGS_FILE = "work_monitor_settings.json"


class SettingsDialog(QDialog):
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("工作监控设置")
        self.setFixedWidth(360)
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

        eye_layout = QHBoxLayout()
        eye_layout.addWidget(QLabel("护眼提醒(分钟):"))
        self.eye_reminder_interval = QSpinBox()
        self.eye_reminder_interval.setRange(10, 180)
        self.eye_reminder_interval.setValue(
            self.settings.get("eye_reminder_interval", 30)
        )
        eye_layout.addWidget(self.eye_reminder_interval)
        layout.addLayout(eye_layout)

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
        self.settings["eye_reminder_interval"] = self.eye_reminder_interval.value()
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
            except Exception:
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
            except Exception:
                pass


class NotificationWindow(QWidget):
    def __init__(
        self,
        screen,
        notif_type="rest",
        is_repeat=False,
        stack_index=0,
        stack_spacing=16,
    ):
        super().__init__()
        self.screen = screen
        self.notif_type = notif_type
        self.is_repeat = is_repeat
        self.stack_index = stack_index
        self.stack_spacing = stack_spacing
        self.setWindowFlags(
            Qt.ToolTip | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setCursor(Qt.PointingHandCursor)
        self.init_ui()

    def init_ui(self):
        self.setFixedSize(1000, 382)
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 20, 30, 20)

        if self.notif_type == "eye":
            title_text = "🕐 护眼提醒"
            title_style = "font-size: 32px; font-weight: bold; color: #16a085;"
            msg = "请每隔一段时间休息一下，\n看看远处，放松眼睛！"
        else:
            title_text = "⚠️ 仍在加班"
            title_style = (
                "font-size: 32px; font-weight: bold; color: #e74c3c;"
                if self.is_repeat
                else "font-size: 32px; font-weight: bold; color: #2c3e50;"
            )
            msg = (
                "您已工作很久了，\n请务必休息！"
                if self.is_repeat
                else "您已工作一段时间，\n该休息一下了！"
            )

        title = QLabel(title_text)
        title.setStyleSheet(title_style)

        message = QLabel(msg)
        message.setStyleSheet(
            "font-size: 32px; color: #34495e; font-family: 'Microsoft YaHei';"
        )
        message.setWordWrap(True)
        message.setAlignment(Qt.AlignCenter)

        hint = QLabel("点击此处关闭")
        hint.setStyleSheet("font-size: 14px; color: #95a5a6;")
        hint.setAlignment(Qt.AlignRight)

        layout.addWidget(title)
        layout.addStretch()
        layout.addWidget(message)
        layout.addStretch()
        layout.addWidget(hint)
        self.setLayout(layout)

        geom = self.screen.availableGeometry()
        x = geom.x() + geom.width() - self.width() - 20
        y = geom.y() + geom.height() - self.height() - 60
        y -= self.stack_index * (self.height() + self.stack_spacing)
        self.move(x, y)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.close()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor(255, 255, 255, 252))

        if self.notif_type == "eye":
            border_color = QColor(22, 160, 133)
        else:
            border_color = (
                QColor(231, 76, 60) if self.is_repeat else QColor(52, 152, 219)
            )

        painter.setPen(border_color)
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 15, 15)


class WorkMonitor(QSystemTrayIcon):
    def __init__(self, app):
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
        self.eye_reminder_seconds = 0
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
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                settings = json.load(f)
        except Exception:
            settings = {}

        defaults = {
            "work_duration": 45,
            "repeat_interval": 30,
            "eye_reminder_interval": 30,
            "idle_time": 180,
            "start_time": "09:00",
            "end_time": "17:30",
        }
        defaults.update(settings)
        return defaults

    def setup_listeners(self):
        def on_activity(*_):
            self.last_activity = datetime.now()

        self.m_l = mouse.Listener(
            on_move=on_activity, on_click=on_activity, on_scroll=on_activity
        )
        self.m_l.start()
        self.k_l = keyboard.Listener(on_press=on_activity)
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
        if idle_sec >= self.settings["idle_time"]:
            self.reset_counters()
            self.status_action.setText("状态: 休息中")
            return

        self.eye_reminder_seconds += 1
        eye_due = (
            self.eye_reminder_seconds >= self.settings["eye_reminder_interval"] * 60
        )

        if not self.is_reminded:
            self.work_seconds += 1
            self.status_action.setText(f"状态: 工作中 ({self.work_seconds // 60}min)")
            rest_due = self.work_seconds >= self.settings["work_duration"] * 60
        else:
            self.repeat_seconds += 1
            rem_min = self.settings["repeat_interval"] - (self.repeat_seconds // 60)
            rem_min = max(rem_min, 0)
            self.status_action.setText(f"状态: 建议休息 (再次提醒: {rem_min}min)")
            rest_due = self.repeat_seconds >= self.settings["repeat_interval"] * 60

        if rest_due or eye_due:
            notif_specs = []
            if rest_due:
                notif_specs.append({"type": "rest", "is_repeat": self.is_reminded})
            if eye_due:
                notif_specs.append({"type": "eye"})
            self.show_notifications(notif_specs)

            if rest_due:
                self.is_reminded = True
                self.repeat_seconds = 0
            if eye_due:
                self.eye_reminder_seconds = 0

    def trigger_alert(self, is_repeat=False):
        self.is_reminded = True
        self.repeat_seconds = 0
        self.show_notifications([{"type": "rest", "is_repeat": is_repeat}])

    def trigger_eye_alert(self):
        self.show_notifications([{"type": "eye"}])

    def show_notifications(self, notif_specs):
        for screen in QGuiApplication.screens():
            for idx, spec in enumerate(notif_specs):
                notif = NotificationWindow(
                    screen,
                    notif_type=spec.get("type", "rest"),
                    is_repeat=spec.get("is_repeat", False),
                    stack_index=idx,
                    stack_spacing=16,
                )
                notif.show()
                self.current_notifs.append(notif)
                QTimer.singleShot(30000, lambda n=notif: self.close_notif(n))

    def reset_counters(self):
        self.work_seconds = 0
        self.repeat_seconds = 0
        self.eye_reminder_seconds = 0
        self.is_reminded = False

    def close_notif(self, notif):
        try:
            notif.close()
            if notif in self.current_notifs:
                self.current_notifs.remove(notif)
        except Exception:
            pass

    def show_settings(self):
        if SettingsDialog(self.settings).exec_():
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    monitor = WorkMonitor(app)
    sys.exit(app.exec_())

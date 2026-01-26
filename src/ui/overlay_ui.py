import sys
import socket
import json
import threading
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel, 
                               QListWidget, QListWidgetItem, QFrame, QHBoxLayout, QPushButton)
from PySide6.QtCore import Qt, Signal, QObject, Slot
from PySide6.QtGui import QColor, QFont, QPalette, QBrush, QIcon

# 定义深色系配色
COLOR_BACKGROUND = "#1B262C"  # 深蓝黑
COLOR_TEXT_PRIMARY = "#BBE1FA" # 亮蓝白
COLOR_ACCENT = "#3282B8"       # 强调蓝
COLOR_ITEM_BG = "#0F4C75"      # 列表项背景
COLOR_SCORE_HIGH = "#00FF00"   # 高分绿
COLOR_SCORE_LOW = "#AAAAAA"    # 低分灰
COLOR_EXIT_HOVER = "#FF4444"   # 退出按钮悬停色

class DataReceiver(QObject):
    """
    负责后台连接 Socket 并接收数据，通过 Signal 发送给 UI 线程
    """
    data_received = Signal(dict)
    connection_status = Signal(str)

    def __init__(self, host='127.0.0.1', port=9999):
        super().__init__()
        self.host = host
        self.port = port
        self.running = True
        self.thread = threading.Thread(target=self._listen, daemon=True)
        self.thread.start()

    def stop(self):
        """显式停止接收线程"""
        self.running = False

    def _listen(self):
        self.connection_status.emit("Connecting...")
        while self.running:
            s = None
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                # 设置超时，以便在停止时能跳出 recv 阻塞
                s.settimeout(2.0)
                s.connect((self.host, self.port))
                self.connection_status.emit("Connected")
                
                buffer = ""
                while self.running:
                    try:
                        data = s.recv(4096)
                        if not data:
                            break
                        
                        buffer += data.decode('utf-8')
                        while '\n' in buffer:
                            line, buffer = buffer.split('\n', 1)
                            if line.strip():
                                try:
                                    # print(f"DEBUG: Raw Line: {line}") 
                                    json_data = json.loads(line)
                                    self.data_received.emit(json_data)
                                except json.JSONDecodeError as e:
                                    print(f"JSON Parse Error: {e}")
                                    print(f"Problematic Data: {line}")
                                except Exception as e:
                                    print(f"Critical Error in Receive Loop: {e}")
                    except socket.timeout:
                        continue
                    except OSError:
                        break
                                
            except (ConnectionRefusedError, socket.timeout):
                self.connection_status.emit("Waiting for Game...")
                # 稍微等待重试，避免死循环占满 CPU
                import time
                for _ in range(20): # sleep 2s, but check running every 0.1s
                    if not self.running: break
                    time.sleep(0.1)
            except Exception as e:
                self.connection_status.emit(f"Error: {e}")
                import time
                for _ in range(20):
                    if not self.running: break
                    time.sleep(0.1)
            finally:
                if s:
                    try:
                        s.close()
                    except:
                        pass

class CardItemWidget(QWidget):
    """
    自定义列表项：显示卡牌名称和得分
    """
    def __init__(self, name, score, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        self.name_label = QLabel(name)
        self.name_label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 14px; font-weight: bold;")
        
        self.score_label = QLabel(f"{score}")
        score_color = COLOR_SCORE_HIGH if score >= 80 else COLOR_SCORE_LOW
        self.score_label.setStyleSheet(f"color: {score_color}; font-size: 16px; font-weight: bold;")
        
        layout.addWidget(self.name_label)
        layout.addStretch()
        layout.addWidget(self.score_label)

class OverlayWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.init_logic()

    def init_ui(self):
        # 1. 窗口属性设置
        self.setWindowTitle("Spire AI Assistant")
        self.resize(300, 500)
        self.move(50, 50) # 默认左上角
        
        # 无边框 + 置顶
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        
        # 背景透明
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # 背景容器 (为了实现半透明深色背景)
        self.background_frame = QFrame(self)
        self.background_frame.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(27, 38, 44, 200); /* 半透明深蓝 */
                border-radius: 10px;
                border: 1px solid {COLOR_ACCENT};
            }}
        """)
        main_layout.addWidget(self.background_frame)
        
        # 内容布局
        content_layout = QVBoxLayout(self.background_frame)
        
        # 标题栏 (状态栏) + 退出按钮
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        
        self.status_label = QLabel("Waiting for Connection...")
        self.status_label.setStyleSheet(f"color: {COLOR_ACCENT}; font-weight: bold; padding: 5px;")
        title_layout.addWidget(self.status_label)
        
        title_layout.addStretch()
        
        self.exit_btn = QPushButton("X")
        self.exit_btn.setFixedSize(30, 30)
        self.exit_btn.setCursor(Qt.PointingHandCursor)
        self.exit_btn.setStyleSheet(f"""
            QPushButton {{
                color: {COLOR_TEXT_PRIMARY};
                background-color: transparent;
                border: none;
                font-weight: bold;
                font-size: 16px;
            }}
            QPushButton:hover {{
                color: {COLOR_EXIT_HOVER};
            }}
        """)
        self.exit_btn.clicked.connect(self.close)
        title_layout.addWidget(self.exit_btn)
        
        content_layout.addLayout(title_layout)
        
        # 玩家信息
        self.info_label = QLabel("HP: ?/? | Energy: ?/?")
        self.info_label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; padding: 5px;")
        self.info_label.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(self.info_label)

        # 分割线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet(f"background-color: {COLOR_ACCENT};")
        content_layout.addWidget(line)

        # 卡牌列表
        self.card_list = QListWidget()
        self.card_list.setStyleSheet(f"""
            QListWidget {{
                background-color: transparent;
                border: none;
                outline: none;
            }}
            QListWidget::item {{
                background-color: {COLOR_ITEM_BG};
                margin: 2px;
                border-radius: 4px;
            }}
        """)
        content_layout.addWidget(self.card_list)
        
        # 拖拽移动窗口逻辑
        self.old_pos = None

    def init_logic(self):
        self.receiver = DataReceiver()
        self.receiver.connection_status.connect(self.update_status)
        self.receiver.data_received.connect(self.update_data)

    @Slot(str)
    def update_status(self, status):
        self.status_label.setText(status)

    @Slot(dict)
    def update_data(self, data):
        try:
            # 更新玩家信息
            player = data.get("player", {})
            hp = player.get("hp", "?")
            max_hp = player.get("max_hp", "?")
            energy = player.get("energy", "?")
            self.info_label.setText(f"HP: {hp}/{max_hp} | Energy: {energy}")

            # 更新手牌列表
            self.card_list.clear()
            hand = data.get("hand", [])
            
            # 按分数排序
            hand.sort(key=lambda x: x.get("recommendation_score", 0), reverse=True)
            
            for card in hand:
                item = QListWidgetItem(self.card_list)
                widget = CardItemWidget(card.get("name", "Unknown"), card.get("recommendation_score", 0))
                item.setSizeHint(widget.sizeHint())
                self.card_list.addItem(item)
                self.card_list.setItemWidget(item, widget)
        except Exception as e:
            print(f"UI Update Error: {e}")
            import traceback
            traceback.print_exc()

    # 允许拖拽窗口
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self.old_pos:
            delta = event.globalPosition().toPoint() - self.old_pos
            self.move(self.pos() + delta)
            self.old_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self.old_pos = None

    def closeEvent(self, event):
        """窗口关闭时，停止后台线程并退出应用"""
        if hasattr(self, 'receiver'):
            self.receiver.stop()
        event.accept()
        QApplication.instance().quit()

if __name__ == "__main__":
    try:
        print("Starting UI Application...", file=sys.stderr)
        app = QApplication(sys.argv)
        print("QApplication initialized.", file=sys.stderr)
        window = OverlayWindow()
        print("Window initialized. Showing window...", file=sys.stderr)
        window.show()
        print("Window shown. Entering main loop...", file=sys.stderr)
        sys.exit(app.exec())
    except Exception as e:
        print(f"CRITICAL UI ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        input("Press Enter to exit...") # 防止窗口瞬间关闭看不到报错

from PyQt5.QtGui import (QIcon, QPainter, QMovie, QColor, QTextCharFormat, QFont, QPixmap, QTextBlockFormat)
from PyQt5.QtWidgets import (QApplication, QMainWindow, QFrame, QLabel, QSizePolicy, QTextEdit, QStackedWidget, QWidget, QLineEdit, QGridLayout, QVBoxLayout, QHBoxLayout, QPushButton)
from PyQt5.QtCore import Qt, QSize, QTimer, QUrl, QRect
from PyQt5.QtWebEngineWidgets import QWebEngineView
from dotenv import dotenv_values
import sys
import os

# Load environment variables from .env file
env_vars = dotenv_values(".env")
Assistantname = env_vars.get("Assistantname", "Purva") # Provide a default if not found
Username = env_vars.get("Username", "User")

# Define global paths for temporary files and graphics
current_dir = os.path.dirname(os.path.abspath(__file__))
TempDirPath = os.path.join(current_dir, "Files")
GraphicsDirPath = os.path.join(current_dir, "Graphics")

print(f"GUI DEBUG: Current working directory (from GUI.py): {current_dir}")
print(f"GUI DEBUG: Temporary files directory path: {TempDirPath}")
print(f"GUI DEBUG: Graphics directory path: {GraphicsDirPath}")

try:
    os.makedirs(TempDirPath, exist_ok=True)
    os.makedirs(GraphicsDirPath, exist_ok=True)
    print(f"GUI DEBUG: Ensured directories exist: {TempDirPath}, {GraphicsDirPath}")
except OSError as e:
    print(f"GUI ERROR: Could not create directories in GUI.py: {e}")

def AnswerModifier(answer):
    lines = answer.split('\n')
    non_empty_lines = [line for line in lines if line.strip()]
    modified_answer = "\n".join(non_empty_lines)
    return modified_answer

def QueryModifier(query):
    new_query = query.lower().strip()
    query_words = new_query.split()

    question_words = [
        "how", "what", "who", "where", "when", "why", "which",
        "whose", "whom", "can you", "what's", "where's", "how's"
    ]

    if any(word in new_query for word in question_words):
        if query_words and query_words[-1][-1] in ['.', '?', '!']:
            new_query = new_query[:-1] + "?"
        else:
            new_query += "?"
    else:
        if query_words and query_words[-1][-1] in ['.', '?', '!']:
            new_query = new_query[:-1] + "."
        else:
            new_query += "."

    return new_query.capitalize()

def SetMicrophoneStatus(command):
    try:
        with open(TempDirectoryPath('Mic.data'), "w", encoding='utf-8') as file:
            file.write(command)
        print(f"GUI DEBUG: Set microphone status to: {command}")
    except IOError as e:
        print(f"GUI ERROR: Error writing microphone status: {e}")

def GetMicrophoneStatus():
    try:
        with open(TempDirectoryPath('Mic.data'), "r", encoding='utf-8') as file:
            status = file.read().strip()
            return status
    except FileNotFoundError:
        print("GUI WARNING: Mic.data not found, returning default 'False'.")
        SetMicrophoneStatus("False")
        return "False"
    except IOError as e:
        print(f"GUI ERROR: Error reading microphone status: {e}")
        return "False"

def SetAssistantStatus(status):
    try:
        with open(TempDirectoryPath('Status.data'), "w", encoding='utf-8') as file:
            file.write(status)
        print(f"GUI DEBUG: Set assistant status to: {status}")
    except IOError as e:
        print(f"GUI ERROR: Error writing assistant status: {e}")

def GetAssistantStatus():
    try:
        with open(TempDirectoryPath('Status.data'), "r", encoding='utf-8') as file:
            status = file.read().strip()
            return status
    except FileNotFoundError:
        print("GUI WARNING: Status.data not found, returning empty string.")
        SetAssistantStatus("Idle")
        return "Idle"
    except IOError as e:
        print(f"GUI ERROR: Error reading assistant status: {e}")
        return ""

def MicButtonInitialed():
    SetMicrophoneStatus("True")
    print("GUI DEBUG: MicButtonInitialed - Mic set to TRUE.")

def MicButtonClosed():
    SetMicrophoneStatus("False")
    print("GUI DEBUG: MicButtonClosed - Mic set to FALSE.")

def GraphicsDirectoryPath(filename):
    path = os.path.join(GraphicsDirPath, filename)
    if not os.path.exists(path):
        print(f"GUI WARNING: Graphics file NOT FOUND at: {path}")
    return path

def TempDirectoryPath(filename):
    path = os.path.join(TempDirPath, filename)
    return path

def ShowTextToScreen(text):
    try:
        with open(TempDirectoryPath('Responses.data'), "w", encoding='utf-8') as file:
            file.write(text)
        print(f"GUI DEBUG: Wrote to Responses.data: '{text[:50]}...'")
    except IOError as e:
        print(f"GUI ERROR: Error writing text to Responses.data: {e}")

class ChatSection(QWidget):
    def __init__(self):
        super(ChatSection, self).__init__()
        self.old_chat_message = ""

        layout = QVBoxLayout(self)
        layout.setContentsMargins(-10, 40, 40, 100)
        layout.setSpacing(10)

        self.chat_text_edit = QTextEdit()
        self.chat_text_edit.setReadOnly(True)
        self.chat_text_edit.setTextInteractionFlags(Qt.NoTextInteraction)
        self.chat_text_edit.setFrameStyle(QFrame.NoFrame)
        layout.addWidget(self.chat_text_edit)
        self.setStyleSheet("background-color: black;")
        layout.setSizeConstraint(QVBoxLayout.SetDefaultConstraint)
        self.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding))

        text_color_text = QTextCharFormat()
        text_color_text.setForeground(QColor(Qt.white))
        self.chat_text_edit.setCurrentCharFormat(text_color_text)

        self.gif_label = QLabel()
        self.gif_label.setStyleSheet("border: none;")
        movie = QMovie(GraphicsDirectoryPath('Jarvis.gif'))
        if movie.isValid():
            print("GUI DEBUG: Jarvis.gif movie loaded successfully.")
        else:
            print("GUI WARNING: Jarvis.gif movie failed to load or is invalid. Check path and file integrity.")
            self.gif_label.setText("GIF NOT FOUND")
            self.gif_label.setStyleSheet("color: red; border: 1px solid red; background-color: darkgray;")

        max_gif_size_W = 480
        max_gif_size_H = 270
        movie.setScaledSize(QSize(max_gif_size_W, max_gif_size_H))
        self.gif_label.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        self.gif_label.setMovie(movie)
        if movie.isValid():
            movie.start()
        layout.addWidget(self.gif_label)

        self.label = QLabel("")
        self.label.setStyleSheet("color: white; font-size:16px; margin-right: 195px; border: none; margin-top: -30px;")
        self.label.setAlignment(Qt.AlignRight)
        layout.addWidget(self.label)

        font = QFont()
        font.setPointSize(13)
        self.chat_text_edit.setFont(font)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.loadMessages)
        self.timer.timeout.connect(self.SpeechRecogText)
        self.timer.start(200)
        self.chat_text_edit.viewport().installEventFilter(self)

        self.setStyleSheet("""
            QScrollBar:vertical {
                border: none;
                background: black;
                width: 10px;
                margin: 0px 0px 0px 0px;
            }
            QScrollBar::handle:vertical {
                background: grey;
                min-height: 20px;
            }
            QScrollBar::add-line:vertical {
                background: black;
                subcontrol-position: bottom;
                subcontrol-origin: margin;
                height: 10px;
            }
            QScrollBar::sub-line:vertical {
                background: black;
                subcontrol-position: top;
                subcontrol-origin: margin;
                height: 10px;
            }
            QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical {
                border: none;
                background: none;
                color: none;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
            QTextEdit {
                background-color: black;
                color: white;
                border: none;
            }
        """)

    def loadMessages(self):
        file_path = TempDirectoryPath('Responses.data')
        messages = ""
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                messages = file.read().strip()
        except FileNotFoundError:
            pass
        except IOError as e:
            print(f"GUI ERROR: Error reading {file_path}: {e}")
            return

        if messages and self.old_chat_message != messages:
            print(f"GUI DEBUG: New messages loaded: '{messages[:50]}...'")
            self.addMessage(messages=messages)
            self.old_chat_message = messages

    def SpeechRecogText(self):
        try:
            messages = GetAssistantStatus()
            self.label.setText(messages)
        except Exception as e:
            print(f"GUI ERROR: Error in ChatSection.SpeechRecogText: {e}")
            self.label.setText("Error loading status.")

    def addMessage(self, messages):
        cursor = self.chat_text_edit.textCursor()
        cursor.movePosition(cursor.End)

        format_char = QTextCharFormat()
        block_format = QTextBlockFormat()
        block_format.setTopMargin(10)
        block_format.setLeftMargin(10)

        username_from_env = env_vars.get("Username", "User")

        if messages.startswith(f"{Assistantname}:"):
            format_char.setForeground(QColor("#00BFFF"))
            block_format.setAlignment(Qt.AlignLeft)
        elif messages.startswith(f"{username_from_env}:"):
            format_char.setForeground(QColor("#FFFF00"))
            block_format.setAlignment(Qt.AlignRight)
        else:
            format_char.setForeground(QColor(Qt.white))
            block_format.setAlignment(Qt.AlignLeft)

        cursor.insertBlock(block_format)
        cursor.setCharFormat(format_char)
        cursor.insertText(messages)

        self.chat_text_edit.setTextCursor(cursor)
        self.chat_text_edit.verticalScrollBar().setValue(self.chat_text_edit.verticalScrollBar().maximum())


class InitialScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        if QApplication.instance() is None:
            QApplication(sys.argv)
            
        screen = QApplication.primaryScreen()
        screen_rect = screen.availableGeometry()
        screen_width = screen_rect.width()
        screen_height = screen_rect.height()

        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setAlignment(Qt.AlignCenter)

        self.pulse_animation_view = QWebEngineView()
        self.pulse_animation_view.setContentsMargins(0, 0, 0, 0)
        self.pulse_animation_view.setMinimumSize(400, 225)

        html_file_path = GraphicsDirectoryPath('pulse_animation.html')
        if os.path.exists(html_file_path):
            self.pulse_animation_view.setUrl(QUrl.fromLocalFile(html_file_path))
            print(f"GUI DEBUG: Loaded pulse_animation.html from: {html_file_path}")
        else:
            print(f"GUI ERROR: HTML pulse animation file not found at: {html_file_path}")
            self.pulse_animation_view.setHtml("<h1 style='color:white; text-align:center;'>Animation not found!</h1>")

        self.pulse_animation_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        content_layout.addWidget(self.pulse_animation_view, alignment=Qt.AlignCenter)

        self.label = QLabel("")
        self.label.setStyleSheet("color: white; font-size: 16px; margin-bottom:0;")
        self.label.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(self.label, alignment=Qt.AlignCenter)

        self.icon_label = QLabel()
        self.icon_label.setFixedSize(150, 150)
        self.icon_label.setAlignment(Qt.AlignCenter)
        
        initial_mic_status = GetMicrophoneStatus()
        self.toggled = (initial_mic_status == "True")
        
        self.toggle_icon_visual_only()
        
        self.icon_label.mousePressEvent = self.toggle_icon

        content_layout.addWidget(self.icon_label, alignment=Qt.AlignCenter)
        content_layout.setContentsMargins(0, 0, 0, int(screen_height * 0.15))

        self.setLayout(content_layout)
        self.setFixedHeight(screen_height)
        self.setFixedWidth(screen_width)
        self.setStyleSheet("background-color: black;")

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.SpeechRecogText)
        self.timer.start(200)

    def SpeechRecogText(self):
        try:
            messages = GetAssistantStatus()
            self.label.setText(messages)
        except Exception as e:
            print(f"GUI ERROR: Error in ChatSection.SpeechRecogText: {e}")
            self.label.setText("Error loading status.")

    def load_icon(self, path, width=60, height=60):
        pixmap = QPixmap(path)
        if pixmap.isNull():
            print(f"GUI WARNING: Icon '{path}' could not be loaded. Showing placeholder.")
            fallback_pixmap = QPixmap(width, height)
            fallback_pixmap.fill(QColor("darkgray"))
            painter = QPainter(fallback_pixmap)
            painter.setPen(QColor("red"))
            painter.drawText(fallback_pixmap.rect(), Qt.AlignCenter, "No Icon")
            painter.end()
            self.icon_label.setPixmap(fallback_pixmap)
        else:
            new_pixmap = pixmap.scaled(width, height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.icon_label.setPixmap(new_pixmap)
        print(f"GUI DEBUG: Loaded icon: {path}")

    def toggle_icon_visual_only(self):
        if self.toggled:
            self.load_icon(GraphicsDirectoryPath('Mic_on.png'), 60, 60)
            print("GUI DEBUG: Initial icon set to Mic_on.png.")
        else:
            self.load_icon(GraphicsDirectoryPath('Mic_off.png'), 60, 60)
            print("GUI DEBUG: Initial icon set to Mic_off.png.")

    def toggle_icon(self, event=None):
        self.toggled = not self.toggled
        if self.toggled:
            self.load_icon(GraphicsDirectoryPath('Mic_on.png'), 60, 60)
            MicButtonInitialed()
            print("GUI DEBUG: Mic state toggled to ON.")
        else:
            self.load_icon(GraphicsDirectoryPath('Mic_off.png'), 60, 60)
            MicButtonClosed()
            print("GUI DEBUG: Mic state toggled to OFF.")


class MessageScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        if QApplication.instance() is None:
            QApplication(sys.argv)

        screen = QApplication.primaryScreen()
        screen_rect = screen.availableGeometry()
        screen_width = screen_rect.width()
        screen_height = screen_rect.height()

        layout = QVBoxLayout()
        chat_section = ChatSection()
        layout.addWidget(chat_section)
        self.setLayout(layout)
        self.setStyleSheet("background-color: black;")
        self.setFixedHeight(screen_height)
        self.setFixedWidth(screen_width)

class CustomTopBar(QWidget):
    def __init__(self, parent, stacked_widget):
        super().__init__(parent)
        self.stacked_widget = stacked_widget
        self.setStyleSheet("background-color: white;")
        self.offset = None
        self.initUI()


    def initUI(self):
        self.setFixedHeight(50)
        layout = QHBoxLayout(self)
        layout.setAlignment(Qt.AlignLeft)
        layout.setContentsMargins(10, 0, 10, 0)

        title_label = QLabel(f"{str(Assistantname).capitalize()} AI")
        title_label.setStyleSheet("color: black; font-size: 18px; background-color: white;")
        layout.addWidget(title_label)

        self.drag_handle = title_label
        self.drag_handle.mousePressEvent = self._start_drag
        self.drag_handle.mouseMoveEvent = self._perform_drag
        self.drag_handle.mouseReleaseEvent = self._end_drag
        self.drag_handle.setMouseTracking(True)


        layout.addStretch(1)

        home_button = QPushButton()
        home_icon = QIcon(GraphicsDirectoryPath("Home.png"))
        if home_icon.isNull(): print("GUI WARNING: 'Home.png' icon failed to load.")
        home_button.setIcon(home_icon)
        home_button.setText(" Home")
        home_button.setStyleSheet("""
            height: 40px;
            line-height:40px;
            background-color:white;
            color: black;
            border-radius: 5px;
            padding: 0 10px;
        """)
        home_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        layout.addWidget(home_button)

        message_button = QPushButton()
        message_icon = QIcon(GraphicsDirectoryPath("Chats.png"))
        if message_icon.isNull(): print("GUI WARNING: 'Chats.png' icon failed to load.")
        message_button.setIcon(message_icon)
        message_button.setText(" Chat")
        message_button.setStyleSheet("""
            height: 40px;
            line-height: 40px;
            background-color:white;
            color: black;
            border-radius: 5px;
            padding: 0 10px;
        """)
        message_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        layout.addWidget(message_button)

        layout.addStretch(1)

        minimize_button = QPushButton()
        minimize_icon = QIcon(GraphicsDirectoryPath('Minimize2.png'))
        if minimize_icon.isNull(): print("GUI WARNING: 'Minimize2.png' icon failed to load.")
        minimize_button.setIcon(minimize_icon)
        minimize_button.setStyleSheet("""
            background-color: white;
            border: none;
            padding: 5px;
        """)
        minimize_button.clicked.connect(self.minimizeWindow)
        layout.addWidget(minimize_button)

        self.maximize_button = QPushButton()
        self.maximize_icon = QIcon(GraphicsDirectoryPath('Maximize.png'))
        self.restore_icon = QIcon(GraphicsDirectoryPath('Minimize.png'))
        if self.maximize_icon.isNull(): print("GUI WARNING: 'Maximize.png' icon failed to load.")
        if self.restore_icon.isNull(): print("GUI WARNING: 'Minimize.png' icon failed to load (for restore).")
        self.maximize_button.setIcon(self.maximize_icon)
        self.maximize_button.setFlat(True)
        self.maximize_button.setStyleSheet("""
            background-color:white;
            border: none;
            padding: 5px;
        """)
        self.maximize_button.clicked.connect(self.maximizeWindow)
        layout.addWidget(self.maximize_button)

        close_button = QPushButton()
        close_icon = QIcon(GraphicsDirectoryPath('Close.png'))
        if close_icon.isNull(): print("GUI WARNING: 'Close.png' icon failed to load.")
        close_button.setIcon(close_icon)
        close_button.setStyleSheet("""
            background-color:white;
            border: none;
            padding: 5px;
        """)
        close_button.clicked.connect(self.closeWindow)
        layout.addWidget(close_button)

    def minimizeWindow(self):
        self.parent().showMinimized()

    def maximizeWindow(self):
        if self.parent().isMaximized():
            self.parent().showNormal()
            self.maximize_button.setIcon(self.maximize_icon)
        else:
            self.parent().showMaximized()
            self.maximize_button.setIcon(self.restore_icon)

    def closeWindow(self):
        self.parent().close()

    def _start_drag(self, event):
        if event.button() == Qt.LeftButton:
            self.offset = event.globalPos() - self.parent().frameGeometry().topLeft()
            event.accept()

    def _perform_drag(self, event):
        if self.offset is not None and event.buttons() & Qt.LeftButton:
            self.parent().move(event.globalPos() - self.offset)
            event.accept()

    def _end_drag(self, event):
        if event.button() == Qt.LeftButton:
            self.offset = None
            event.accept()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.initUI()

    def initUI(self):
        if QApplication.instance() is None:
            QApplication(sys.argv)

        screen = QApplication.primaryScreen()
        screen_rect = screen.availableGeometry()
        screen_width = screen_rect.width()
        screen_height = screen_rect.height()

        stacked_widget = QStackedWidget(self)
        initial_screen = InitialScreen()
        message_screen = MessageScreen()

        stacked_widget.addWidget(initial_screen)
        stacked_widget.addWidget(message_screen)

        self.setGeometry(0, 0, screen_width, screen_height)
        self.setStyleSheet("background-color: black;")

        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        top_bar = CustomTopBar(self, stacked_widget)
        main_layout.addWidget(top_bar)
        main_layout.addWidget(stacked_widget)

        self.setCentralWidget(central_widget)

    def closeEvent(self, event):
        from PyQt5.QtWidgets import QMessageBox
        reply = QMessageBox.question(self, 'Confirm Exit',
                                     "Are you sure you want to quit?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            print("DEBUG: User confirmed exit. Closing application.")
            event.accept()
        else:
            print("DEBUG: User canceled exit. Keeping application open.")
            event.ignore()

def GraphicalUserInterface():
    print("GUI DEBUG: Initializing QApplication...")
    app = QApplication(sys.argv)
    app.setApplicationName("Jarvis AI")

    print("GUI DEBUG: Creating MainWindow...")
    window = MainWindow()
    print("GUI DEBUG: Showing MainWindow...")
    window.show()

    print("GUI DEBUG: Starting QApplication event loop...")
    sys.exit(app.exec_())

if __name__ == "__main__":
    print("GUI DEBUG: GUI.py running directly. This should usually be called from Main.py.")
    if not os.path.exists(TempDirectoryPath('Mic.data')):
        SetMicrophoneStatus("False")
        print("GUI DEBUG: Initialized Mic.data to False.")
    if not os.path.exists(TempDirectoryPath('Status.data')):
        SetAssistantStatus("Idle")
        print("GUI DEBUG: Initialized Status.data to Idle.")

    GraphicalUserInterface()
import sqlite3
from cryptography.fernet import Fernet
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QPushButton, QLabel, QTextEdit, QVBoxLayout, QCalendarWidget, QDialog, QHBoxLayout, QFileDialog, QGridLayout, QMenu
from PyQt5.QtCore import QDate, QLocale, Qt
from PyQt5.QtGui import QFont, QPixmap, QImage, QPainter, QColor
from PIL import Image
import sys
import os
import io

# 加密密钥生成（仅在首次运行时使用）
def generate_key():
    return Fernet.generate_key()

# 加密与解密工具类
class EncryptionTool:
    def __init__(self, key):
        self.cipher_suite = Fernet(key)
    
    def encrypt(self, data):
        return self.cipher_suite.encrypt(data.encode()).decode()

    def decrypt(self, data):
        return self.cipher_suite.decrypt(data.encode()).decode()

# 数据库管理类
class JournalDatabase:
    def __init__(self, db_name="journal.db", key_file="key.key"):
        self.db_name = db_name
        self.key_file = key_file
        self.key = self.load_key()  # 加载密钥
        self.encryption_tool = EncryptionTool(self.key)
        self.create_tables()

    def load_key(self):
        """ 从文件加载加密密钥，若文件不存在则生成并保存 """
        if os.path.exists(self.key_file):
            with open(self.key_file, "rb") as key_file:
                return key_file.read()
        else:
            key = generate_key()
            with open(self.key_file, "wb") as key_file:
                key_file.write(key)
            return key

    def create_tables(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS journal_entries (
                            id INTEGER PRIMARY KEY,
                            date TEXT NOT NULL,
                            entry TEXT NOT NULL
                          )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS entry_photos (
                            entry_id INTEGER,
                            photo BLOB,
                            FOREIGN KEY(entry_id) REFERENCES journal_entries(id)
                          )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS entry_attachments (
                            entry_id INTEGER,
                            attachment BLOB,
                            FOREIGN KEY(entry_id) REFERENCES journal_entries(id)
                          )''')
        conn.commit()
        conn.close()

    def save_entry(self, date, entry_text, photos=None, attachments=None):
        """ 保存日记条目，支持多张照片和多个附件 """
        date_str = date.toString("yyyy-MM-dd")
        encrypted_text = self.encryption_tool.encrypt(entry_text)

        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        # 插入日记条目
        cursor.execute('''INSERT INTO journal_entries (date, entry) VALUES (?, ?)''', (date_str, encrypted_text))
        entry_id = cursor.lastrowid  # 获取插入的日记条目ID

        # 保存照片
        if photos:
            for photo in photos:
                cursor.execute('''INSERT INTO entry_photos (entry_id, photo) VALUES (?, ?)''', (entry_id, photo))

        # 保存附件
        if attachments:
            for attachment in attachments:
                cursor.execute('''INSERT INTO entry_attachments (entry_id, attachment) VALUES (?, ?)''', (entry_id, attachment))

        conn.commit()
        conn.close()

    def get_entry(self, date):
        """ 获取日记条目，包含照片和附件 """
        date_str = date.toString("yyyy-MM-dd")
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''SELECT id, entry FROM journal_entries WHERE date = ?''', (date_str,))
        entry_data = cursor.fetchone()
        if entry_data:
            entry_id, entry_text = entry_data
            entry_text = self.encryption_tool.decrypt(entry_text)
            
            # 获取照片
            cursor.execute('''SELECT photo FROM entry_photos WHERE entry_id = ?''', (entry_id,))
            photos = cursor.fetchall()
            
            # 获取附件
            cursor.execute('''SELECT attachment FROM entry_attachments WHERE entry_id = ?''', (entry_id,))
            attachments = cursor.fetchall()

            conn.close()
            return entry_text, [photo[0] for photo in photos], [attachment[0] for attachment in attachments]
        conn.close()
        return None, None, None

    def get_all_entries_dates(self):
        """ 获取所有有日记条目的日期 """
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('SELECT date FROM journal_entries')
        result = cursor.fetchall()
        conn.close()
        return [QDate.fromString(date[0], "yyyy-MM-dd") for date in result]

# 图片压缩函数
def compress_image(image_path, max_size=(100, 100)):
    """ 压缩图片为指定大小，并转换为二进制数据 """
    img = Image.open(image_path)

    # 获取文件扩展名（用于确定保存格式）
    file_extension = os.path.splitext(image_path)[1].lower()

    # 压缩图像
    img.thumbnail(max_size)

    # 将压缩后的图像保存为二进制数据
    byte_io = io.BytesIO()

    if file_extension == '.png':
        # 如果是PNG格式，保存为PNG（支持透明通道）
        img.save(byte_io, format="PNG")
    elif file_extension == '.jpg' or file_extension == '.jpeg':
        # 如果是JPEG格式，保存为JPEG
        img.save(byte_io, format="JPEG")
    else:
        # 其他格式，使用Pillow支持的格式（例如WebP）
        img.save(byte_io, format=img.format)
    
    byte_io.seek(0)
    return byte_io.read()

class ImageViewer(QDialog):
    def __init__(self, image_data):
        super().__init__()
        self.setWindowTitle("查看大图")
        self.setGeometry(300, 200, 800, 600)
        
        # 显示大图
        pixmap = QPixmap()
        pixmap.loadFromData(image_data)
        
        image_label = QLabel(self)
        image_label.setPixmap(pixmap.scaled(800, 600, Qt.KeepAspectRatio))  # 设置图片大小
        layout = QVBoxLayout()
        layout.addWidget(image_label)
        self.setLayout(layout)
        self.exec_()

# 日记编辑窗口
class JournalEditor(QDialog):
    def __init__(self, date, entry_text, photos, attachments, save_callback):
        super().__init__()
        self.setWindowTitle(f"日记条目 - {format_date(date)}")
        self.setGeometry(300, 200, 800, 800)
        self.save_callback = save_callback
        self.date = date
        self.photos = photos  # 存储照片
        self.attachments = attachments  # 存储附件
        self.initUI(entry_text)

    def initUI(self, entry_text):
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Header
        header_label = QLabel(f"日记条目 - {format_date(self.date)}")
        header_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(header_label)

        # Text Editor
        self.text_editor = QTextEdit()
        self.text_editor.setPlainText(entry_text)
        layout.addWidget(self.text_editor)

        # Attach File Button
        attach_button = QPushButton("添加附件")
        attach_button.clicked.connect(self.attach_file)
        layout.addWidget(attach_button)

        # Select Photos Button
        photo_button = QPushButton("选择多张照片")
        photo_button.clicked.connect(self.select_photos)
        layout.addWidget(photo_button)

        # Photos Display Layout
        self.photos_layout = QGridLayout()
        layout.addLayout(self.photos_layout)

        # Save Button
        save_button = QPushButton("保存条目")
        save_button.clicked.connect(self.save_entry)
        layout.addWidget(save_button)

        # Attachments Display
        self.attachments_label = QLabel("附件: 无")
        layout.addWidget(self.attachments_label)

        # 显示该日期上传的所有图片
        self.display_photos()

    def attach_file(self):
        """ 允许用户选择多个附件（如音频、视频等） """
        file_paths, _ = QFileDialog.getOpenFileNames(self, "选择附件", "", "All Files (*)")
        if file_paths:
            self.attachments = [open(file_path, "rb").read() for file_path in file_paths]
            self.attachments_label.setText(f"附件: {len(self.attachments)} 个文件")

    def select_photos(self):
        """ 允许用户选择多张照片并压缩 """
        photo_paths, _ = QFileDialog.getOpenFileNames(self, "选择照片", "", "Images (*.png *.jpg *.jpeg *.bmp *.gif)")
        if photo_paths:
            self.photos = [compress_image(photo_path) for photo_path in photo_paths]
            self.display_photos()

    def display_photos(self):
        """ 显示该日期所有照片缩略图 """
        # 清空现有的布局
        for i in reversed(range(self.photos_layout.count())):
            widget = self.photos_layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()

        # 显示所有照片的缩略图
        for i, photo in enumerate(self.photos):
            pixmap = QPixmap()
            pixmap.loadFromData(photo)
            pixmap = pixmap.scaled(100, 100, Qt.KeepAspectRatio)  # 确保图片不会变形
            label = QLabel()
            label.setPixmap(pixmap)
            label.setAlignment(Qt.AlignCenter)
            # 为每个照片缩略图添加右键菜单
            #label.setContextMenuPolicy(Qt.CustomContextMenu)
            #label.customContextMenuRequested.connect(lambda pos, label=label: self.show_context_menu(pos, label, photo))
            label.setContextMenuPolicy(Qt.CustomContextMenu)
            label.customContextMenuRequested.connect(lambda pos, label=label, photo=photo: self.show_context_menu(pos, label, photo))
            self.photos_layout.addWidget(label, i // 3, i % 3)  # 按照 3 列显示

    def show_large_image(self, photo_data):
        """ 显示大图 """
        viewer = ImageViewer(photo_data)

    def show_context_menu(self, pos, label, photo):
        """ 显示右键菜单，支持查看大图和下载操作 """
        context_menu = QMenu(self)

        view_action = context_menu.addAction("查看大图")
        download_action = context_menu.addAction("下载")

        action = context_menu.exec_(label.mapToGlobal(pos))

        if action == view_action:
            self.show_large_image(photo)  # 查看大图
        elif action == download_action:
            self.download_photo(photo)  # 下载照片

    def download_photo(self, photo):
        """ 下载照片到文件 """
        file_path, _ = QFileDialog.getSaveFileName(self, "保存照片", "", "Image Files (*.png *.jpg *.jpeg *.bmp *.gif)")
        if file_path:
            with open(file_path, "wb") as f:
                f.write(photo)

    def save_entry(self):
        entry_text = self.text_editor.toPlainText()
        self.save_callback(self.date, entry_text, self.photos, self.attachments)
        self.accept()  # 关闭编辑窗口



# 自定义日期格式化函数
def format_date(date):
    """ 自定义日期格式化，避免符号替换问题 """
    year = date.year()
    month = f"{date.month():02d}"  # 保证两位数格式
    day = f"{date.day():02d}"      # 保证两位数格式
    return f"{year}年{month}月{day}日"

# 自定义日历控件
class CustomCalendar(QCalendarWidget):
    def __init__(self):
        super().__init__()
        self.setGridVisible(True)
        self.date_with_photos = {}  # 用来存储有照片附件的日期
        
    def set_dates_with_photos(self, dates):
        """ 设置有照片的日期 """
        self.date_with_photos = dates

    def paintCell(self, painter, rect, date):
        """ 重绘日历单元格，显示照片背景 """
        super().paintCell(painter, rect, date)
        
        if date in self.date_with_photos:
            # 在日期方格上画图片作为背景
            photo = self.date_with_photos[date]
            pixmap = QPixmap()
            pixmap.loadFromData(photo)  # 使用照片数据生成 QPixmap
            pixmap = pixmap.scaled(rect.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            
            # 设置透明度
            painter.setOpacity(0.5)  # 设置图片透明度为50%
            painter.drawPixmap(rect, pixmap)
            
            # 恢复原始透明度，防止影响其他绘制操作
            painter.setOpacity(1.0)

    def resizeEvent(self, event):
        """ 确保日历单元格为正方形 """
        super().resizeEvent(event)
        self.adjustCellSize()

    def adjustCellSize(self):
        """ 动态调整日历单元格大小，确保为正方形 """
        # 获取日历控件的宽度和高度
        width = self.width()
        height = self.height()
        
        # 每周7列，最大显示6行
        num_columns = 7
        num_rows = 6

        # 计算单元格的最大边长，确保单元格为正方形
        cell_size = min(width // num_columns, height // num_rows)

        # 设置每个单元格的大小
        self.setStyleSheet(f"""
            QCalendarWidget QAbstractItemView {{
                gridline-color: lightgray;
                font-size: 14px;
                min-width: {cell_size}px;
                min-height: {cell_size}px;
            }}
        """)


# 日记应用主窗口
class JournalApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("日记应用 - 日历视图")
        self.setGeometry(100, 100, 1000, 700)
        self.db = JournalDatabase()  # 使用默认密钥文件
        self.journal_data = {}  # Store journal entries in memory

        self.initUI()

    def initUI(self):
        # Main layout
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.layout = QVBoxLayout()
        self.main_widget.setLayout(self.layout)

        # Header Layout (Title + Button in the same row)
        header_layout = QHBoxLayout()
        self.layout.addLayout(header_layout)

        # Header Label (日历日记)
        self.header_label = QLabel("日历日记", self)
        self.header_label.setStyleSheet("font-size: 24px; font-weight: bold; padding: 10px;")
        header_layout.addWidget(self.header_label)

        # Spacer to push the button to the right
        header_layout.addStretch()

        # 回到今天按钮
        today_button = QPushButton("回到今天")
        today_button.clicked.connect(self.go_to_today)
        header_layout.addWidget(today_button)

        # Calendar Widget
        self.calendar = CustomCalendar()  # 使用自定义日历控件
        self.calendar.setLocale(QLocale(QLocale.Chinese, QLocale.China))  # 使用简体中文环境
        self.layout.addWidget(self.calendar)

        # 设置日历上带有照片的日期
        all_entries_dates = self.db.get_all_entries_dates()
        photo_entries = {}
        for date in all_entries_dates:
            entry_text, photos, _ = self.db.get_entry(date)
            if photos:
                photo_entries[date] = photos[0]  # 显示第一张照片

        self.calendar.set_dates_with_photos(photo_entries)

        # Calendar clicked event
        self.calendar.clicked.connect(self.show_journal)

        # Status Label
        self.status_label = QLabel("点击一个日期来打开日记条目。")
        self.layout.addWidget(self.status_label)

    def go_to_today(self):
        self.calendar.setSelectedDate(QDate.currentDate())

    def show_journal(self, date):
        entry_text, photos, attachments = self.db.get_entry(date)
        if entry_text:
            self.show_editor(date, entry_text, photos, attachments)
        else:
            self.show_editor(date, "", [], [])

    def show_editor(self, date, entry_text, photos, attachments):
        editor = JournalEditor(date, entry_text, photos, attachments, self.save_entry)
        editor.exec_()

    def save_entry(self, date, entry_text, photos, attachments):
        self.db.save_entry(date, entry_text, photos, attachments)
        self.status_label.setText(f"日期 {format_date(date)} 的条目已保存。")

# 运行应用
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = JournalApp()
    window.show()
    sys.exit(app.exec_())

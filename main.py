import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QWidget, QFileDialog, QMessageBox,
                             QDialog, QLineEdit, QTextEdit, QScrollArea)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPalette, QColor, QFontDatabase

# 实现龙形混淆加密算法
class DragonCipher:
    # 动态S盒生成
    @staticmethod
    def generate_dynamic_sbox(key):
        sbox = list(range(256))
        key_bytes = key.encode('utf-8')
        j = 0
        
        for i in range(256):
            j = (j + sbox[i] + key_bytes[i % len(key_bytes)]) % 256
            sbox[i], sbox[j] = sbox[j], sbox[i]
        return sbox
    
    # 逆S盒生成
    @staticmethod
    def generate_inverse_sbox(sbox):
        inverse_sbox = [0] * 256
        for i in range(256):
            inverse_sbox[sbox[i]] = i
        return inverse_sbox
    
    # 修复的龙形螺旋置换
    @staticmethod
    def dragon_spiral_permutation(data, key, encrypt):
        length = len(data)
        if length == 0:
            return data
        
        result = [0] * length
        key_bytes = key.encode('utf-8')
        
        # 创建螺旋路径
        spiral_path = []
        
        # 计算矩阵尺寸
        size = int((length ** 0.5) + 0.999999)  # 向上取整
        total_size = size * size
        
        # 初始化矩阵，用-1标记空位
        matrix = [-1] * total_size
        
        # 填充数据索引
        index = 0
        for i in range(total_size):
            if index < length:
                matrix[i] = index
                index += 1
        
        # 生成螺旋路径
        top = 0
        bottom = size - 1
        left = 0
        right = size - 1
        direction = 0  # 0:右, 1:下, 2:左, 3:上
        
        while top <= bottom and left <= right:
            if direction == 0:
                # 向右
                for i in range(left, right + 1):
                    pos = top * size + i
                    if matrix[pos] != -1:
                        spiral_path.append(matrix[pos])
                top += 1
            elif direction == 1:
                # 向下
                for i in range(top, bottom + 1):
                    pos = i * size + right
                    if matrix[pos] != -1:
                        spiral_path.append(matrix[pos])
                right -= 1
            elif direction == 2:
                # 向左
                for i in range(right, left - 1, -1):
                    pos = bottom * size + i
                    if matrix[pos] != -1:
                        spiral_path.append(matrix[pos])
                bottom -= 1
            elif direction == 3:
                # 向上
                for i in range(bottom, top - 1, -1):
                    pos = i * size + left
                    if matrix[pos] != -1:
                        spiral_path.append(matrix[pos])
                left += 1
            
            direction = (direction + 1) % 4
        
        # 应用置换
        if encrypt:
            # 加密：按螺旋路径重新排列
            for i in range(length):
                result[i] = data[spiral_path[i]]
        else:
            # 解密：逆向螺旋路径
            for i in range(length):
                result[spiral_path[i]] = data[i]
        
        return result
    
    # 改进的可逆扩散函数
    @staticmethod
    def dragon_diffusion(data, key, encrypt):
        length = len(data)
        result = [0] * length
        key_bytes = key.encode('utf-8')
        
        if encrypt:
            # 加密：前向扩散
            prev = 0
            for i in range(length):
                key_byte = key_bytes[i % len(key_bytes)]
                result[i] = (data[i] + key_byte + prev + i) % 256
                prev = result[i]
        else:
            # 解密：逆向扩散
            prev = 0
            for i in range(length):
                key_byte = key_bytes[i % len(key_bytes)]
                original = (data[i] - key_byte - prev - i) % 256
                if original < 0:
                    original += 256
                result[i] = original
                prev = data[i]  # 注意：这里使用原始密文值
        
        return result

# 加密函数
def encode(plaintext, key):
    if not plaintext or not key:
        return ""
    
    # 转换为字节数组
    data = list(plaintext.encode('utf-8'))
    
    # 生成动态S盒
    sbox = DragonCipher.generate_dynamic_sbox(key)
    
    # 3轮加密
    for round_num in range(3):
        # 1. S盒代换
        for i in range(len(data)):
            data[i] = sbox[data[i]]
        
        # 2. 龙形扩散
        data = DragonCipher.dragon_diffusion(data, key, True)
        
        # 3. 龙形螺旋置换
        data = DragonCipher.dragon_spiral_permutation(data, key, True)
    
    # 返回Base64编码的密文
    import base64
    return base64.b64encode(bytes(data)).decode('utf-8')

# 解密函数
def decode(ciphertext, key):
    if not ciphertext or not key:
        return ""
    
    # 从Base64解码
    import base64
    try:
        data = list(base64.b64decode(ciphertext))
    except Exception as e:
        raise ValueError(f"无效的Base64密文: {str(e)}")
    
    # 生成动态S盒和逆S盒
    sbox = DragonCipher.generate_dynamic_sbox(key)
    inverse_sbox = DragonCipher.generate_inverse_sbox(sbox)
    
    # 3轮解密（逆序操作）
    for round_num in range(2, -1, -1):
        # 1. 逆向龙形螺旋置换
        data = DragonCipher.dragon_spiral_permutation(data, key, False)
        
        # 2. 逆向龙形扩散
        data = DragonCipher.dragon_diffusion(data, key, False)
        
        # 3. 逆向S盒代换
        for i in range(len(data)):
            data[i] = inverse_sbox[data[i]]
    
    # 返回明文
    return bytes(data).decode('utf-8')

# 密钥输入对话框
class KeyDialog(QDialog):
    def __init__(self, parent=None, mode="decrypt"):
        super().__init__(parent)
        self.mode = mode
        self.key = None
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("喵")
        self.setFixedSize(400, 150)
        
        layout = QVBoxLayout()
        
        if self.mode == "decrypt":
            label = QLabel("查看文件需要密钥，请输入您获得的密钥：")
        else:
            label = QLabel("加密文件需要密钥，请输入您的密钥：")
        
        self.key_input = QLineEdit()
        # self.key_input.setEchoMode(QLineEdit.Password)
        
        button_layout = QHBoxLayout()
        ok_button = QPushButton("确定")
        ok_button.clicked.connect(self.accept_key)
        cancel_button = QPushButton("取消")
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        
        layout.addWidget(label)
        layout.addWidget(self.key_input)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def accept_key(self):
        self.key = self.key_input.text()
        if not self.key:
            QMessageBox.warning(self, "警告", "密钥不能为空！")
            return
        self.accept()

# 文件内容显示窗口
class FileContentWindow(QMainWindow):
    def __init__(self, content, file_path, parent=None, mode="view"):
        super().__init__(parent)
        self.content = content
        self.file_path = file_path
        self.mode = mode
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("文件内容")
        self.setGeometry(100, 100, 800, 600)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        
        # 内容显示区域
        content_label = QLabel("文件内容:")
        self.content_text = QTextEdit()
        self.content_text.setPlainText(self.content)
        self.content_text.setReadOnly(True)
        
        # 设置等宽字体用于内容显示
        content_font = QFont("等距更纱黑体 SC", 10)
        self.content_text.setFont(content_font)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        export_button = QPushButton("导出")
        export_button.clicked.connect(self.export_file)
        close_button = QPushButton("关闭")
        close_button.clicked.connect(self.close)
        
        button_layout.addWidget(export_button)
        button_layout.addWidget(close_button)
        
        layout.addWidget(content_label)
        layout.addWidget(self.content_text)
        layout.addLayout(button_layout)
        
        central_widget.setLayout(layout)
    
    def export_file(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "保存文件", 
            self.file_path if self.mode == "view" else os.path.splitext(self.file_path)[0] + "_encrypted.txt",
            "Text Files (*.txt)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.content)
                QMessageBox.information(self, "成功", f"文件已保存到: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存文件时出错: {str(e)}")

# 主窗口
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("龙形混淆加密文件查看与制作器")
        self.setFixedSize(600, 400)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        
        # 标题
        title_label = QLabel("龙形混淆加密文件查看与制作器")
        title_font = QFont("等距更纱黑体 SC", 24, QFont.Bold)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        
        # 按钮
        open_button = QPushButton("打开被加密的文件")
        open_button.setFixedSize(200, 50)
        open_button.clicked.connect(self.open_encrypted_file)
        
        encrypt_button = QPushButton("加密文件")
        encrypt_button.setFixedSize(200, 50)
        encrypt_button.clicked.connect(self.encrypt_file)
        
        # 提示文字
        hint_label = QLabel("*目前仅支持.txt格式")
        hint_label.setAlignment(Qt.AlignCenter)
        palette = hint_label.palette()
        palette.setColor(QPalette.WindowText, QColor(128, 128, 128))
        hint_label.setPalette(palette)
        
        layout.addStretch(1)
        layout.addWidget(title_label)
        layout.addSpacing(50)
        layout.addWidget(open_button, alignment=Qt.AlignCenter)
        layout.addSpacing(20)
        layout.addWidget(encrypt_button, alignment=Qt.AlignCenter)
        layout.addSpacing(20)
        layout.addWidget(hint_label)
        layout.addStretch(1)
        
        central_widget.setLayout(layout)
    
    def open_encrypted_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择加密文件", "", "Text Files (*.txt)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    encrypted_content = f.read()
                
                key_dialog = KeyDialog(self, "decrypt")
                if key_dialog.exec_() == QDialog.Accepted:
                    key = key_dialog.key
                    try:
                        decrypted_content = decode(encrypted_content, key)
                        self.show_file_content(decrypted_content, file_path, "view")
                    except Exception as e:
                        QMessageBox.critical(self, "错误", f"解密失败: {str(e)}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"读取文件时出错: {str(e)}")
    
    def encrypt_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择要加密的文件", "", "Text Files (*.txt)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    plaintext_content = f.read()
                
                key_dialog = KeyDialog(self, "encrypt")
                if key_dialog.exec_() == QDialog.Accepted:
                    key = key_dialog.key
                    try:
                        encrypted_content = encode(plaintext_content, key)
                        self.show_file_content(encrypted_content, file_path, "encrypt")
                    except Exception as e:
                        QMessageBox.critical(self, "错误", f"加密失败: {str(e)}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"读取文件时出错: {str(e)}")
    
    def show_file_content(self, content, file_path, mode):
        self.content_window = FileContentWindow(content, file_path, self, mode)
        self.content_window.show()

def load_custom_font():
    """加载自定义字体（如果需要）"""
    # 如果系统没有安装"等距更纱黑体 SC"，可以尝试从文件加载
    # font_id = QFontDatabase.addApplicationFont("path/to/your/font.ttf")
    # if font_id != -1:
    #     font_families = QFontDatabase.applicationFontFamilies(font_id)
    #     print(f"加载的字体家族: {font_families}")
    pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 设置全局字体
    global_font = QFont("等距更纱黑体 SC", 10)
    app.setFont(global_font)
    
    # 设置应用样式
    app.setStyle("Fusion")
    
    # 尝试加载自定义字体（如果需要）
    load_custom_font()
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())
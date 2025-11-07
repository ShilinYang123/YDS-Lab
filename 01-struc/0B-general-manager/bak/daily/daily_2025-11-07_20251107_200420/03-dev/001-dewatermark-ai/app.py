from flask import Flask, render_template, request, jsonify, send_file
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import cv2
import numpy as np
import os
import io
import base64

app = Flask(__name__)
app.secret_key = "dewatermark-ai-secret-key"
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['PROCESSED_FOLDER'] = 'static/processed'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg'}

# 确保上传和处理文件夹存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PROCESSED_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def process_image(image_path):
    """
    使用OpenCV和PIL的高级图像处理技术来去水印
    """
    # 打开图像
    img = Image.open(image_path)
    
    # 转换为RGB模式（如果不是的话）
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    # 转换为numpy数组用于OpenCV处理
    img_array = np.array(img)
    
    # 使用OpenCV进行高级图像处理
    # 1. 高斯模糊去噪
    denoised = cv2.GaussianBlur(img_array, (5, 5), 0)
    
    # 2. 锐化滤波
    kernel = np.array([[-1,-1,-1],
                      [-1, 9,-1],
                      [-1,-1,-1]])
    sharpened = cv2.filter2D(denoised, -1, kernel)
    
    # 3. 形态学操作去除小噪点
    kernel = np.ones((3,3), np.uint8)
    morph = cv2.morphologyEx(sharpened, cv2.MORPH_CLOSE, kernel)
    
    # 4. 双边滤波保留边缘的同时平滑图像
    bilateral = cv2.bilateralFilter(morph, 9, 75, 75)
    
    # 5. 调整对比度和亮度
    alpha = 1.2  # 对比度
    beta = 15    # 亮度
    adjusted = cv2.convertScaleAbs(bilateral, alpha=alpha, beta=beta)
    
    # 转换回PIL图像
    processed_img = Image.fromarray(adjusted)
    
    # 使用PIL进行额外的增强
    # 增强锐度
    enhancer = ImageEnhance.Sharpness(processed_img)
    processed_img = enhancer.enhance(1.3)
    
    # 增强对比度
    enhancer = ImageEnhance.Contrast(processed_img)
    processed_img = enhancer.enhance(1.2)
    
    return processed_img

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('没有选择文件')
        return redirect(request.url)
    
    file = request.files['file']
    if file.filename == '':
        flash('没有选择文件')
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        # 生成唯一文件名
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"{timestamp}_{file.filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # 处理图像
        processed_path = process_image(file_path)
        if processed_path:
            return render_template('result.html', 
                                  original=os.path.join('uploads', filename),
                                  processed=os.path.join('processed', os.path.basename(processed_path)))
        else:
            flash('图像处理失败')
            return redirect(url_for('index'))
    else:
        flash('不支持的文件类型')
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
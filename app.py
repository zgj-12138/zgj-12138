from flask import Flask, request, jsonify, send_file, send_from_directory, redirect
from flask_cors import CORS
import os
import json
from datetime import datetime, timedelta
import shutil
import tempfile
import zipfile
import uuid

app = Flask(__name__, static_folder='font_end')
CORS(app, resources={r"/*": {"origins": "*"}})

# 取消文件大小限制
app.config['MAX_CONTENT_LENGTH'] = None

# 添加安全头部信息
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'ALLOW-FROM *'
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

# 配置文件存储路径
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# 作业数据文件路径
HOMEWORK_DATA_FILE = 'homework_data.json'
# 学生数据文件路径
STUDENTS_DATA_FILE = 'students_data.json'
# 请假数据文件路径
LEAVE_DATA_FILE = 'leave_data.json'

# 添加路由处理前端页面请求
@app.route('/')
def index():
    return redirect('/pages/select.html')

@app.route('/index.html')
def index_html():
    return send_from_directory('font_end/pages', 'index.html')

@app.route('/login.html')
def login_html():
    return send_from_directory('font_end/pages', 'login.html')

@app.route('/admin.html')
def admin_html():
    return send_from_directory('font_end/pages', 'admin.html')

@app.route('/pages/<path:filename>')
def serve_pages(filename):
    return send_from_directory('font_end/pages', filename)

@app.route('/js/<path:filename>')
def serve_js(filename):
    return send_from_directory('font_end/js', filename)

@app.route('/css/<path:filename>')
def serve_css(filename):
    return send_from_directory('font_end/css', filename)

def load_homework_data():
    if os.path.exists(HOMEWORK_DATA_FILE):
        with open(HOMEWORK_DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'homework': []}

def save_homework_data(data):
    with open(HOMEWORK_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_students_data():
    if os.path.exists(STUDENTS_DATA_FILE):
        with open(STUDENTS_DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'students': []}

def save_students_data(data):
    with open(STUDENTS_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_leave_data():
    if os.path.exists(LEAVE_DATA_FILE):
        with open(LEAVE_DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'leaves': []}

def save_leave_data(data):
    with open(LEAVE_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# 学生管理 API
@app.route('/api/students', methods=['GET'])
def get_students():
    data = load_students_data()
    return jsonify(data)

@app.route('/api/students', methods=['POST'])
def add_student():
    try:
        student_data = request.json
        if not all([student_data.get('studentId'), student_data.get('name')]):
            return jsonify({'success': False, 'message': '缺少必要信息'}), 400
        
        data = load_students_data()
        # 检查学号是否已存在
        if any(s['studentId'] == student_data['studentId'] for s in data['students']):
            return jsonify({'success': False, 'message': '该学号已存在'}), 400
        
        # 生成唯一ID
        student_id = 1
        if data['students']:
            student_id = max(s['id'] for s in data['students']) + 1
        
        new_student = {
            'id': student_id,
            'studentId': student_data['studentId'],
            'name': student_data['name']
        }
        
        data['students'].append(new_student)
        save_students_data(data)
        
        return jsonify({'success': True, 'message': '添加学生成功'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/students/<int:student_id>', methods=['PUT'])
def update_student(student_id):
    try:
        student_data = request.json
        if not all([student_data.get('studentId'), student_data.get('name')]):
            return jsonify({'success': False, 'message': '缺少必要信息'}), 400
        
        data = load_students_data()
        student_index = next((i for i, s in enumerate(data['students']) if s['id'] == student_id), None)
        
        if student_index is None:
            return jsonify({'success': False, 'message': '学生不存在'}), 404
            
        # 检查新学号是否与其他学生重复
        if any(s['studentId'] == student_data['studentId'] and s['id'] != student_id for s in data['students']):
            return jsonify({'success': False, 'message': '该学号已存在'}), 400
        
        data['students'][student_index]['studentId'] = student_data['studentId']
        data['students'][student_index]['name'] = student_data['name']
        save_students_data(data)
        
        return jsonify({'success': True, 'message': '更新学生信息成功'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/students/<int:student_id>', methods=['DELETE'])
def delete_student(student_id):
    try:
        data = load_students_data()
        data['students'] = [s for s in data['students'] if s['id'] != student_id]
        save_students_data(data)
        return jsonify({'success': True, 'message': '删除学生成功'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# 作业管理 API
@app.route('/api/homework', methods=['GET'])
def get_homework_list():
    data = load_homework_data()
    return jsonify(data)

@app.route('/api/homework', methods=['POST'])
def add_homework():
    try:
        homework_data = request.json
        if not all([homework_data.get('courseName'), homework_data.get('title'), 
                   homework_data.get('deadline'), homework_data.get('requirements')]):
            return jsonify({'success': False, 'message': '缺少必要信息'}), 400
        
        data = load_homework_data()
        # 生成唯一ID
        homework_id = 1
        if data['homework']:
            homework_id = max(h['id'] for h in data['homework']) + 1
        
        new_homework = {
            'id': homework_id,
            'course_name': homework_data['courseName'],
            'title': homework_data['title'],
            'description': homework_data['requirements'],
            'deadline': homework_data['deadline'],
            'fileNameFormats': homework_data.get('fileNameFormats', ['{学号}_{姓名}_实验{作业编号}.docx']),
            'status': 'active'
        }
        
        data['homework'].append(new_homework)
        save_homework_data(data)
        
        # 创建作业目录
        homework_dir = os.path.join(UPLOAD_FOLDER, f"homework_{homework_id}")
        if not os.path.exists(homework_dir):
            os.makedirs(homework_dir)
        
        return jsonify({'success': True, 'message': '发布作业成功'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/homework/<int:homework_id>', methods=['DELETE'])
def delete_homework(homework_id):
    try:
        data = load_homework_data()
        data['homework'] = [h for h in data['homework'] if h['id'] != homework_id]
        save_homework_data(data)
        
        # 删除作业目录
        homework_dir = os.path.join(UPLOAD_FOLDER, f"homework_{homework_id}")
        if os.path.exists(homework_dir):
            shutil.rmtree(homework_dir)
        
        return jsonify({'success': True, 'message': '删除作业成功'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/homework/<int:homework_id>', methods=['PUT'])
def update_homework(homework_id):
    try:
        homework_data = request.json
        if not all([homework_data.get('courseName'), homework_data.get('title'), 
                   homework_data.get('deadline'), homework_data.get('requirements')]):
            return jsonify({'success': False, 'message': '缺少必要信息'}), 400
        
        data = load_homework_data()
        homework_index = next((i for i, h in enumerate(data['homework']) if h['id'] == homework_id), None)
        
        if homework_index is None:
            return jsonify({'success': False, 'message': '作业不存在'}), 404
        
        data['homework'][homework_index].update({
            'course_name': homework_data['courseName'],
            'title': homework_data['title'],
            'description': homework_data['requirements'],
            'deadline': homework_data['deadline'],
            'fileNameFormats': homework_data.get('fileNameFormats', ['{学号}_{姓名}_实验{作业编号}.docx'])
        })
        
        save_homework_data(data)
        return jsonify({'success': True, 'message': '更新作业成功'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/homework/upload', methods=['POST'])
def upload_homework():
    try:
        student_name = request.form.get('studentName')
        student_id = request.form.get('studentId')
        homework_id = request.form.get('homeworkId')
        description = request.form.get('description')
        file_count = int(request.form.get('fileCount', 1))

        if not all([student_name, student_id, homework_id]):
            return jsonify({'success': False, 'message': '缺少必要信息'}), 400

        # 验证学生信息
        students_data = load_students_data()
        student = next((s for s in students_data['students'] 
                       if s['studentId'] == student_id and s['name'] == student_name), None)
        
        if not student:
            return jsonify({'success': False, 'message': '学生信息不存在或姓名与学号不匹配'}), 400

        # 获取作业信息
        homework_data = load_homework_data()
        homework = next((h for h in homework_data['homework'] if str(h['id']) == str(homework_id)), None)
        
        if not homework:
            return jsonify({'success': False, 'message': '作业不存在'}), 404

        # 检查是否已截止
        try:
            deadline = datetime.fromisoformat(homework['deadline'].replace('Z', '+00:00'))
        except ValueError:
            try:
                deadline = datetime.strptime(homework['deadline'], '%Y-%m-%d %H:%M')
            except ValueError:
                return jsonify({'success': False, 'message': '作业截止日期格式错误'}), 400

        if datetime.now() > deadline:
            return jsonify({'success': False, 'message': '作业已截止'}), 400

        # 检查是否已经提交过

        homework_dir = os.path.join(UPLOAD_FOLDER, f"homework_{homework_id}")
        student_dir = os.path.join(homework_dir, f"{student_id}_{student_name}")
        submissions_file = os.path.join(student_dir, 'submissions.json')
        
        if os.path.exists(submissions_file):
            with open(submissions_file, 'r', encoding='utf-8') as f:
                submissions = json.load(f)
                if submissions:  # 如果已经有提交记录
                    return jsonify({'success': False, 'message': '您已经提交过该作业，如需重新提交，请联系聪明的学委'}), 400

        # 创建作业目录（如果不存在）
        if not os.path.exists(homework_dir):
            os.makedirs(homework_dir)

        # 创建学生提交目录（使用学号_姓名命名）
        if not os.path.exists(student_dir):
            os.makedirs(student_dir)

        # 获取文件命名格式
        fileNameFormats = homework.get('fileNameFormats', ['{学号}_{姓名}_实验{作业编号}.docx'])
        if isinstance(fileNameFormats, str):
            fileNameFormats = [fileNameFormats]
        
        # 保存所有文件
        saved_files = []
        for i in range(file_count):
            file = request.files.get(f'file{i}')
            if file:
                # 验证文件名格式
                filename = file.filename
                valid_format = False
                for format_str in fileNameFormats:
                    try:
                        expectedFileName = format_str.format(
                            学号=student_id,
                            姓名=student_name,
                            作业编号=homework_id
                        )
                        if filename == expectedFileName:
                            valid_format = True
                            break
                    except KeyError as e:
                        # 如果格式字符串中包含不支持的占位符，跳过该格式
                        continue
                
                if not valid_format:
                    # 生成格式示例
                    format_examples = []
                    for f in fileNameFormats:
                        try:
                            example = f.format(
                                学号=student_id,
                                姓名=student_name,
                                作业编号=homework_id
                            )
                            format_examples.append(example)
                        except KeyError:
                            continue
                    
                    if format_examples:
                        return jsonify({
                            'success': False, 
                            'message': f'文件名格式不正确，请按照以下任一格式命名：\n' + 
                                     '\n'.join(format_examples)
                        }), 400
                    else:
                        return jsonify({
                            'success': False, 
                            'message': '文件名格式不正确，请检查作业要求中的文件命名格式'
                        }), 400
                
                file_path = os.path.join(student_dir, filename)
                file.save(file_path)
                saved_files.append(filename)

        if not saved_files:
            return jsonify({'success': False, 'message': '没有文件被上传'}), 400

        # 保存提交记录
        submission = {
            'id': len(os.listdir(student_dir)),
            'student_name': student_name,
            'student_id': student_id,
            'homework_id': homework_id,
            'description': description,
            'filenames': saved_files,
            'submit_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'status': '已提交'
        }

        submissions = []
        if os.path.exists(submissions_file):
            with open(submissions_file, 'r', encoding='utf-8') as f:
                submissions = json.load(f)
        
        submissions.append(submission)
        
        with open(submissions_file, 'w', encoding='utf-8') as f:
            json.dump(submissions, f, ensure_ascii=False, indent=2)

        return jsonify({'success': True, 'message': '作业提交成功'})

    except Exception as e:
        print(e)
        return jsonify({'success': False, 'message': str("你已经提交过该作业，如需重新提交，联系学委")}), 500

# 作业提交情况 API
@app.route('/api/submissions', methods=['GET'])
def get_submissions():
    try:
        # 新增获取过滤参数
        student_id = request.args.get('studentId')
        student_name = request.args.get('studentName')
        course = request.args.get('course', '')
        
        # 获取所有作业
        homework_data = load_homework_data()
        homework_list = homework_data['homework']
        
        # 如果指定了课程，则过滤作业
        if course:
            homework_list = [h for h in homework_list if h['course_name'] == course]
        
        # 获取所有提交
        submissions = []
        for homework in homework_list:
            homework_id = homework['id']
            homework_dir = os.path.join(UPLOAD_FOLDER, f"homework_{homework_id}")
            
            if not os.path.exists(homework_dir):
                continue
                
            # 查找该作业的所有学生提交目录
            for student_dir_name in os.listdir(homework_dir):
                student_dir = os.path.join(homework_dir, student_dir_name)
                if not os.path.isdir(student_dir):
                    continue
                    
                submissions_file = os.path.join(student_dir, 'submissions.json')
                
                if os.path.exists(submissions_file):
                    with open(submissions_file, 'r', encoding='utf-8') as f:
                        student_submissions = json.load(f)
                        for submission in student_submissions:
                            # 添加作业标题和课程名称
                            submission['homeworkTitle'] = homework['title']
                            submission['courseName'] = homework['course_name']
                            submissions.append(submission)
        
        # 新增过滤逻辑
        if student_id or student_name:
            filtered = []
            for submission in submissions:
                match_id = not student_id or (submission['student_id'] == student_id)
                match_name = not student_name or (submission['student_name'].lower() == student_name.lower())
                if match_id and match_name:
                    filtered.append(submission)
            return jsonify({'submissions': filtered})
            
        return jsonify({'submissions': submissions})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/submissions/<int:homework_id>/<string:student_id>/<string:filename>', methods=['GET'])
def download_submission(homework_id, student_id, filename):
    try:
        file_path = os.path.join(UPLOAD_FOLDER, f"homework_{homework_id}", f"student_{student_id}", filename)
        
        if not os.path.exists(file_path):
            return jsonify({'success': False, 'message': '文件不存在'}), 404
            
        return send_file(file_path, as_attachment=True)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# 请假管理 API
@app.route('/api/leave', methods=['POST'])
def submit_leave():
    try:
        # 获取基本信息
        student_name = request.form.get('studentName')
        student_id = request.form.get('studentId')
        leave_type = request.form.get('leaveType')
        reason = request.form.get('reason')

        if not all([student_name, student_id, leave_type, reason]):
            return jsonify({'success': False, 'message': '缺少必要信息'}), 400

        # 验证学生信息
        students_data = load_students_data()
        student = next((s for s in students_data['students'] 
                       if s['studentId'] == student_id and s['name'] == student_name), None)
        
        if not student:
            return jsonify({'success': False, 'message': '学生信息不存在或姓名与学号不匹配'}), 400

        # 检查是否已经提交过今天的请假申请
        data = load_leave_data()
        today = datetime.now().date()
        existing_leave = next((leave for leave in data['leaves'] 
                             if leave['studentId'] == student_id and 
                             datetime.strptime(leave['submitTime'], '%Y-%m-%d %H:%M:%S').date() == today), None)
        
        if existing_leave:
            return jsonify({'success': False, 'message': '您今天已经提交过请假申请，不能重复提交'}), 400

        # 处理图片上传
        image_filenames = []
        if 'leaveImages' in request.files:
            # 获取所有上传的图片
            images = request.files.getlist('leaveImages')
            for image in images:
                if image.filename:  # 确保文件存在
                    # 生成唯一的文件名
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f"{student_name}_{student_id}_{timestamp}_{image.filename}"
                    # 确保上传目录存在
                    os.makedirs('uploads/leave_images', exist_ok=True)
                    # 保存文件
                    file_path = os.path.join('uploads/leave_images', filename)
                    image.save(file_path)
                    image_filenames.append(filename)

        # 生成请假记录
        leave_id = 1
        if data['leaves']:
            leave_id = max(l['id'] for l in data['leaves']) + 1

        new_leave = {
            'id': leave_id,
            'studentName': student_name,
            'studentId': student_id,
            'leaveType': leave_type,
            'reason': reason,
            'leaveImages': image_filenames,  # 存储所有图片文件名
            'submitTime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'status': '待审核'
        }

        data['leaves'].append(new_leave)
        save_leave_data(data)

        return jsonify({'success': True, 'message': '请假申请提交成功'})
    except Exception as e:
        print(f"提交请假申请错误: {str(e)}")  # 添加错误日志
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/leave/list', methods=['GET'])
def get_leave_list():
    try:
        date = request.args.get('date')
        data = load_leave_data()
        
        if date:
            # 如果指定了日期，只返回该日期的请假记录
            filtered_leaves = []
            for leave in data['leaves']:
                leave_date = datetime.strptime(leave['submitTime'], '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')
                if leave_date == date:
                    filtered_leaves.append(leave)
            return jsonify({'success': True, 'leaves': filtered_leaves})
        
        return jsonify({'success': True, 'leaves': data['leaves']})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/leave/approve/<int:leave_id>', methods=['POST'])
def approve_leave(leave_id):
    try:
        data = load_leave_data()
        leave_index = next((i for i, l in enumerate(data['leaves']) if l['id'] == leave_id), None)
        
        if leave_index is None:
            return jsonify({'success': False, 'message': '请假记录不存在'}), 404
        
        data['leaves'][leave_index]['status'] = '已批准'
        save_leave_data(data)
        
        return jsonify({'success': True, 'message': '已批准请假申请'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/leave/reject/<int:leave_id>', methods=['POST'])
def reject_leave(leave_id):
    try:
        data = load_leave_data()
        leave_index = next((i for i, l in enumerate(data['leaves']) if l['id'] == leave_id), None)
        
        if leave_index is None:
            return jsonify({'success': False, 'message': '请假记录不存在'}), 404
        
        data['leaves'][leave_index]['status'] = '已拒绝'
        save_leave_data(data)
        
        return jsonify({'success': True, 'message': '已拒绝请假申请'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/homework/<int:homework_id>/download-all', methods=['POST'])
def download_all_submissions(homework_id):
    try:
        # 获取保存路径
        save_path = request.json.get('savePath')
        if not save_path:
            return jsonify({'message': '请指定保存路径'}), 400

        # 确保保存路径存在
        os.makedirs(save_path, exist_ok=True)

        # 获取作业目录
        homework_dir = os.path.join(UPLOAD_FOLDER, f"homework_{homework_id}")
        if not os.path.exists(homework_dir):
            return jsonify({'message': '作业目录不存在'}), 404

        # 复制所有文件
        copied_files = []
        for student_dir_name in os.listdir(homework_dir):
            student_dir = os.path.join(homework_dir, student_dir_name)
            if not os.path.isdir(student_dir):
                continue

            # 读取学生的提交记录
            submissions_file = os.path.join(student_dir, 'submissions.json')
            if not os.path.exists(submissions_file):
                continue

            with open(submissions_file, 'r', encoding='utf-8') as f:
                submissions = json.load(f)
                for submission in submissions:
                    for filename in submission['filenames']:
                        src_file = os.path.join(student_dir, filename)
                        if os.path.exists(src_file):
                            # 直接复制文件，保持原始文件名
                            dst_file = os.path.join(save_path, filename)
                            shutil.copy2(src_file, dst_file)
                            copied_files.append(filename)

        if not copied_files:
            return jsonify({'message': '没有找到任何提交的文件'}), 404

        return jsonify({
            'success': True,
            'message': f'已复制 {len(copied_files)} 个文件到目录: {save_path}',
            'files': copied_files
        })
        
    except Exception as e:
        print(f"复制文件错误: {str(e)}")  # 添加错误日志
        return jsonify({'message': str(e)}), 500

@app.route('/api/clear-cache', methods=['POST'])
def clear_cache():
    try:
        today = datetime.now().date()
        two_days_ago = today - timedelta(days=2)
        
        # 清理请假记录
        leave_data = load_leave_data()
        old_leaves = [leave for leave in leave_data['leaves'] 
                     if datetime.strptime(leave['submitTime'], '%Y-%m-%d %H:%M:%S').date() < today]
        
  
        
        # 更新请假记录
        leave_data['leaves'] = [
            leave for leave in leave_data['leaves']
            if datetime.strptime(leave['submitTime'], '%Y-%m-%d %H:%M:%S').date() >= today
        ]
        save_leave_data(leave_data)
        
        # 清理作业记录
        homework_data = load_homework_data()
        for homework in homework_data['homework'][:]:
            try:
                deadline = datetime.strptime(homework['deadline'], '%Y-%m-%d %H:%M')
                if deadline.date() <= two_days_ago:
                    # 删除作业目录
                    homework_dir = os.path.join(UPLOAD_FOLDER, f"homework_{homework['id']}")
                    if os.path.exists(homework_dir):
                        shutil.rmtree(homework_dir)
                    # 从列表中移除
                    homework_data['homework'].remove(homework)
            except ValueError:
                try:
                    deadline = datetime.fromisoformat(homework['deadline'].replace('Z', '+00:00'))
                    if deadline.date() <= two_days_ago:
                        # 删除作业目录
                        homework_dir = os.path.join(UPLOAD_FOLDER, f"homework_{homework['id']}")
                        if os.path.exists(homework_dir):
                            shutil.rmtree(homework_dir)
                        # 从列表中移除
                        homework_data['homework'].remove(homework)
                except ValueError:
                    continue
        
        save_homework_data(homework_data)
        
        return jsonify({'success': True, 'message': '缓存清理成功'})
    except Exception as e:
        print(f"清理缓存错误: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/update-notice', methods=['GET'])
def get_update_notice():
    try:
        with open('update_notice.txt', 'r', encoding='utf-8') as f:
            notice = f.read()
        return jsonify({'success': True, 'notice': notice})
    except FileNotFoundError:
        return jsonify({'success': True, 'notice': ''})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/missing-submissions', methods=['GET'])
def get_missing_submissions():
    course = request.args.get('course', '')
    
    # 加载所有学生数据
    students_data = load_students_data()
    all_students = {s['studentId']: s['name'] for s in students_data['students']}
    
    # 加载相关作业
    homework_data = load_homework_data()
    relevant_homework = [h for h in homework_data['homework'] if h['course_name'] == course] if course else []
    
    missing_data = []
    
    for hw in relevant_homework:
        # 获取已提交学生ID
        submitted_ids = set()
        homework_dir = os.path.join(UPLOAD_FOLDER, f"homework_{hw['id']}")
        if os.path.exists(homework_dir):
            for entry in os.listdir(homework_dir):
                if '_' in entry:
                    student_id = entry.split('_')[0]
                    submitted_ids.add(student_id)
        
        # 对比未提交学生
        for student_id, name in all_students.items():
            if student_id not in submitted_ids:
                missing_data.append({
                    'course_name': hw['course_name'],
                    'title': hw['title'],
                    'student_id': student_id,
                    'student_name': name,
                    'deadline': hw['deadline']
                })
    
    return jsonify({'missing': missing_data})

@app.route('/api/query', methods=['GET'])
def get_query():
    try:
        # 获取查询参数
        student_id = request.args.get('studentId')
        student_name = request.args.get('studentName')
        
        # 加载所有学生数据
        students_data = load_students_data()
        all_students = {s['studentId']: s['name'] for s in students_data['students']}
        
        # 加载所有作业数据
        homework_data = load_homework_data()
        all_homework = {h['id']: h['title'] for h in homework_data['homework']}
        
        # 构建查询结果
        results = []    
        
        # 遍历所有作业
        for homework in homework_data['homework']:
            # 获取作业提交记录
            homework_dir = os.path.join(UPLOAD_FOLDER, f"homework_{homework['id']}")
            if os.path.exists(homework_dir):
                for entry in os.listdir(homework_dir):  
                    if '_' in entry:
                        student_ID = entry.split('_')[0]
                        if student_ID == student_id:
                            # 获取提交记录
                            submissions_file = os.path.join(homework_dir, entry, 'submissions.json')
                            if os.path.exists(submissions_file):
                                with open(submissions_file, 'r', encoding='utf-8') as f:
                                    submissions = json.load(f)
                                    for submission in submissions:
                                        # 添加作业标题和课程名称和所提交的作业文件名
                                        submission['homeworkTitle'] = homework['title']
                                        submission['courseName'] = homework['course_name']
                                        submission['submitTime'] = datetime.strptime(submission['submit_time'], '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')
                                        submission['files'] = submission['filenames']
                                        results.append(submission)
        
        # 根据学生ID排序
        results.sort(key=lambda x: x['submitTime']) 
        
        return jsonify({
            'success': True,
            'submissions': results
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
                                        
@app.route('/api/submissions/<int:homework_id>/<string:student_id>', methods=['DELETE'])
def delete_submission(homework_id, student_id):
    try:
        # 获取学生姓名参数
        student_name = request.args.get('studentName')
        if not student_name:
            return jsonify({'success': False, 'message': '需要提供学生姓名'}), 400

        # 验证学生身份
        students_data = load_students_data()
        student = next((s for s in students_data['students'] 
                      if s['studentId'] == student_id and s['name'] == student_name), None)
        if not student:
            return jsonify({'success': False, 'message': '学生信息验证失败'}), 403

        # 构建目录路径
        homework_dir = os.path.join(UPLOAD_FOLDER, f"homework_{homework_id}")
        student_dir = os.path.join(homework_dir, f"{student_id}_{student_name}")
        
        # 删除目录及内容
        if os.path.exists(student_dir):
            shutil.rmtree(student_dir)
            return jsonify({'success': True, 'message': '历史提交已清除'})
        
        return jsonify({'success': True, 'message': '无历史提交记录'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
            


if __name__ == '__main__':
    app.run(debug=True) 














     
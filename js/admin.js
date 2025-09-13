new Vue({
    el: '#adminApp',
    data: {
        currentView: 'students',
        students: [],
        homeworkList: [],
        submissions: [],
        leaveList: [],
        selectedDate: new Date().toISOString().split('T')[0],
        courses: [],
        selectedCourse: '',
        showAddStudentModal: false,
        showEditStudentModal: false,
        showAddHomeworkModal: false,
        showEditHomeworkModal: false,
        showMissing: false,
        newStudent: {
            studentId: '',
            name: ''
        },
        editingStudent: null,
        newHomework: {
            courseName: '',
            title: '',
            deadline: '',
            requirements: '',
            fileNameFormats: ['{学号}_{姓名}_实验{作业编号}.docx']
        },
        editingHomework: null,
        apiBaseUrl: 'http://5.181.225.107:26754'
    },
    methods: {
        // 加载学生列表
        async loadStudents() {
            try {
                const response = await axios.get(`${this.apiBaseUrl}/api/students`);
                this.students = response.data.students;
            } catch (error) {
                console.error('加载学生列表失败:', error);
                alert('加载学生列表失败');
            }
        },
        // 编辑学生
        editStudent(student) {
            this.editingStudent = { ...student };
            this.showEditStudentModal = true;
        },
        // 更新学生信息
        async updateStudent() {
            try {
                await axios.put(`${this.apiBaseUrl}/api/students/${this.editingStudent.id}`, {
                    studentId: this.editingStudent.studentId,
                    name: this.editingStudent.name
                });
                this.showEditStudentModal = false;
                this.loadStudents();
                alert('更新学生信息成功');
            } catch (error) {
                console.error('更新学生信息失败:', error);
                alert(error.response?.data?.message || '更新学生信息失败');
            }
        },
        // 删除学生
        async deleteStudent(student) {
            if (!confirm('确定要删除该学生吗？')) {
                return;
            }
            try {
                await axios.delete(`${this.apiBaseUrl}/api/students/${student.id}`);
                this.loadStudents();
                alert('删除学生成功');
            } catch (error) {
                console.error('删除学生失败:', error);
                alert('删除学生失败');
            }
        },
        // 添加学生
        async submitStudent() {
            try {
                await axios.post(`${this.apiBaseUrl}/api/students`, this.newStudent);
                this.showAddStudentModal = false;
                this.newStudent = { studentId: '', name: '' };
                this.loadStudents();
                alert('添加学生成功');
            } catch (error) {
                console.error('添加学生失败:', error);
                alert(error.response?.data?.message || '添加学生失败');
            }
        },
        // 加载作业列表
        async loadHomeworkList() {
            try {
                const response = await axios.get(`${this.apiBaseUrl}/api/homework`);
                this.homeworkList = response.data.homework;
                // 提取所有课程名称
                this.courses = [...new Set(this.homeworkList.map(hw => hw.course_name))];
            } catch (error) {
                console.error('加载作业列表失败:', error);
                alert('加载作业列表失败');
            }
        },
        // 加载提交情况
        async loadSubmissions() {
            try {
                const response = await axios.get(`${this.apiBaseUrl}/api/submissions`, {
                    params: { course: this.selectedCourse }
                });
                this.submissions = response.data.submissions;
            } catch (error) {
                console.error('加载提交情况失败:', error);
                alert('加载提交情况失败');
            }
        },
        // 获取状态样式
        getStatusClass(status) {
            const classes = {
                '已提交': 'badge bg-success',
                '已截止': 'badge bg-danger',
                '未提交': 'badge bg-warning'
            };
            return classes[status] || 'badge bg-secondary';
        },
        // 下载提交的作业
        async downloadSubmission(submission) {
            try {
                const response = await axios.get(`${this.apiBaseUrl}/api/submissions/${submission.homework_id}/${submission.student_id}/${submission.filename}`, {
                    responseType: 'blob'
                });
                const url = window.URL.createObjectURL(new Blob([response.data]));
                const link = document.createElement('a');
                link.href = url;
                link.setAttribute('download', submission.filename);
                document.body.appendChild(link);
                link.click();
                link.remove();
            } catch (error) {
                console.error('下载作业失败:', error);
                alert('下载作业失败');
            }
        },
        // 作业管理方法
        async submitHomework() {
            try {
                const response = await axios.post(`${this.apiBaseUrl}/api/homework`, {
                    courseName: this.newHomework.courseName,
                    title: this.newHomework.title,
                    deadline: this.newHomework.deadline,
                    requirements: this.newHomework.requirements,
                    fileNameFormats: this.newHomework.fileNameFormats
                });
                if (response.data.success) {
                    alert('发布作业成功');
                    this.showAddHomeworkModal = false;
                    this.loadHomeworkList();
                    this.newHomework = {
                        courseName: '',
                        title: '',
                        deadline: '',
                        requirements: '',
                        fileNameFormats: ['{学号}_{姓名}_实验{作业编号}.docx']
                    };
                }
            } catch (error) {
                console.error('发布作业失败：', error);
                alert('发布作业失败');
            }
        },
        async editHomework(homework) {
            this.editingHomework = { ...homework };
            this.editingHomework.courseName = homework.course_name;
            this.editingHomework.requirements = homework.description;
            this.editingHomework.fileNameFormats = homework.fileNameFormats || ['{学号}_{姓名}_实验{作业编号}.docx'];
            this.showEditHomeworkModal = true;
        },
        async updateHomework() {
            try {
                const response = await axios.put(`${this.apiBaseUrl}/api/homework/${this.editingHomework.id}`, {
                    courseName: this.editingHomework.courseName,
                    title: this.editingHomework.title,
                    deadline: this.editingHomework.deadline,
                    requirements: this.editingHomework.requirements,
                    fileNameFormats: this.editingHomework.fileNameFormats
                });
                if (response.data.success) {
                    alert('更新作业成功');
                    this.showEditHomeworkModal = false;
                    this.loadHomeworkList();
                    this.editingHomework = null;
                }
            } catch (error) {
                console.error('更新作业失败：', error);
                alert('更新作业失败');
            }
        },
        async deleteHomework(homework) {
            if (confirm('确定要删除该作业吗？')) {
                try {
                    const response = await axios.delete(`${this.apiBaseUrl}/api/homework/${homework.id}`);
                    if (response.data.success) {
                        alert('删除作业成功');
                        this.loadHomeworkList();
                    }
                } catch (error) {
                    console.error('删除作业失败：', error);
                    alert('删除作业失败');
                }
            }
        },
        viewHomeworkDetails(homework) {
            // 实现查看作业详情功能
            alert(`作业详情：\n课程：${homework.course_name}\n标题：${homework.title}\n截止日期：${homework.deadline}\n要求：${homework.description}`);
        },
        async gradeSubmission(submission) {
            // 实现评分功能
            const score = prompt('请输入分数（0-100）', '');
            if (score !== null && score !== '') {
                const numScore = parseInt(score);
                if (isNaN(numScore) || numScore < 0 || numScore > 100) {
                    alert('请输入0-100之间的有效分数');
                    return;
                }
                
                // 这里应该调用后端API保存分数
                alert(`已为 ${submission.student_name} 的作业评分：${numScore}分`);
            }
        },
        async fetchLeaveList() {
            try {
                const response = await axios.get(`${this.apiBaseUrl}/api/leave/list`, {
                    params: { date: this.selectedDate }
                });
                if (response.data.success) {
                    this.leaveList = response.data.leaves;
                } else {
                    throw new Error(response.data.message || '获取请假列表失败');
                }
            } catch (error) {
                console.error('获取请假列表失败:', error);
                alert(error.response?.data?.message || '获取请假列表失败');
            }
        },
        getLeaveStatusClass(status) {
            return {
                'text-warning': status === '待审核',
                'text-success': status === '已批准',
                'text-danger': status === '已拒绝'
            };
        },
        async approveLeave(leave) {
            try {
                const response = await axios.post(`${this.apiBaseUrl}/api/leave/approve/${leave.id}`);
                if (response.data.success) {
                    alert('已批准请假申请');
                    this.fetchLeaveList();
                } else {
                    throw new Error(response.data.message || '批准请假失败');
                }
            } catch (error) {
                console.error('批准请假失败:', error);
                alert(error.response?.data?.message || '批准请假失败');
            }
        },
        async rejectLeave(leave) {
            try {
                const response = await axios.post(`${this.apiBaseUrl}/api/leave/reject/${leave.id}`);
                if (response.data.success) {
                    alert('已拒绝请假申请');
                    this.fetchLeaveList();
                } else {
                    throw new Error(response.data.message || '拒绝请假失败');
                }
            } catch (error) {
                console.error('拒绝请假失败:', error);
                alert(error.response?.data?.message || '拒绝请假失败');
            }
        },
        async downloadAllSubmissions(homeworkId) {
            try {
                // 弹出输入框让用户输入保存路径
                const savePath = prompt('请输入保存文件的目录路径：');
                if (!savePath) {
                    return; // 用户取消操作
                }

                // 发送请求复制文件
                const response = await axios.post(`${this.apiBaseUrl}/api/homework/${homeworkId}/download-all`, {
                    savePath: savePath
                });
                
                if (response.data.success) {
                    alert(response.data.message);
                } else {
                    throw new Error(response.data.message || '复制文件失败');
                }
            } catch (error) {
                console.error('复制文件失败:', error);
                alert(error.response?.data?.message || '复制文件失败，请重试');
            }
        },
        async clearCache() {
            try {
                if (!confirm('确定要清除缓存吗？这将删除今天之前的请假记录和已截止两天的作业记录。')) {
                    return;
                }
                
                const response = await axios.post(`${this.apiBaseUrl}/api/clear-cache`);
                if (response.data.success) {
                    alert('缓存清理成功');
                    // 刷新数据
                    this.loadHomeworkList();
                    this.fetchLeaveList();
                } else {
                    throw new Error(response.data.message || '清理缓存失败');
                }
            } catch (error) {
                console.error('清理缓存失败:', error);
                alert(error.response?.data?.message || '清理缓存失败，请重试');
            }
        },
        async toggleShowMissing() {
            this.showMissing = !this.showMissing;
            this.loadSubmissions();
        },
        async loadSubmissions() {
            try {
                let url = `${this.apiBaseUrl}/api/submissions`;
                if (this.showMissing) {
                    url = `${this.apiBaseUrl}/api/missing-submissions`;
                }
                
                const response = await axios.get(url, {
                    params: { course: this.selectedCourse }
                });
                
                this.submissions = this.showMissing 
                    ? response.data.missing
                    : response.data.submissions;
            } catch (error) {
                console.error('加载失败:', error);
                alert('加载数据失败');
            }
        },
        addFileNameFormat(target = null) {
            if (target) {
                if (!target.fileNameFormats) {
                    target.fileNameFormats = ['{学号}_{姓名}_实验{作业编号}.docx'];
                } else {
                    target.fileNameFormats.push('{学号}_{姓名}_实验{作业编号}.docx');
                }
            } else {
                if (!this.newHomework.fileNameFormats) {
                    this.newHomework.fileNameFormats = ['{学号}_{姓名}_实验{作业编号}.docx'];
                } else {
                    this.newHomework.fileNameFormats.push('{学号}_{姓名}_实验{作业编号}.docx');
                }
            }
        },
        removeFileNameFormat(index, target = null) {
            if (target) {
                if (target.fileNameFormats && target.fileNameFormats.length > 1) {
                    target.fileNameFormats.splice(index, 1);
                }
            } else {
                if (this.newHomework.fileNameFormats && this.newHomework.fileNameFormats.length > 1) {
                    this.newHomework.fileNameFormats.splice(index, 1);
                }
            }
        }
    },
    watch: {
        selectedCourse() {
            this.loadSubmissions();
        },
        selectedDate() {
            this.fetchLeaveList();
        }
    },
    mounted() {
        this.loadStudents();
        this.loadHomeworkList();
        this.loadSubmissions();
        this.fetchLeaveList();
    }
}); 
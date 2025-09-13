new Vue({
    el: '#app',
    data: {
        studentName: '',
        studentId: '',
        description: '',
        selectedFiles: [],
        apiBaseUrl: 'http://5.181.225.107:26754',
        homeworkList: [],
        selectedHomework: null,
        homeworkDetailsModal: null
    },
    methods: {
        // 获取作业列表
        async fetchHomeworkList() {
            try {
                const response = await axios.get(`${this.apiBaseUrl}/api/homework`);
                this.homeworkList = response.data.homework;
            } catch (error) {
                console.error('获取作业列表失败：', error);
                alert('获取作业列表失败，请刷新页面重试');
            }
        },
        
        // 选择作业
        selectHomework(homework) {
            this.selectedHomework = homework;
            if (this.homeworkDetailsModal) {
                this.homeworkDetailsModal.hide();
            }
        },
        
        // 返回作业列表
        backToHomeworkList() {
            this.selectedHomework = null;
            this.resetForm();
        },
        
        // 查看作业详情
        viewHomeworkDetails(homework) {
            this.selectedHomework = homework;
            if (!this.homeworkDetailsModal) {
                this.homeworkDetailsModal = new bootstrap.Modal(document.getElementById('homeworkDetailsModal'));
            }
            this.homeworkDetailsModal.show();
        },
        
        // 格式化日期
        formatDate(dateString) {
            const date = new Date(dateString);
            return date.toLocaleString('zh-CN', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit'
            });
        },
        
        // 获取作业状态样式
        getStatusClass(homework) {
            const now = new Date();
            const deadline = new Date(homework.deadline);
            
            if (now > deadline) {
                return 'badge bg-danger';
            } else {
                return 'badge bg-success';
            }
        },
        
        // 获取作业状态文本
        getStatusText(homework) {
            const now = new Date();
            const deadline = new Date(homework.deadline);
            
            if (now > deadline) {
                return '已截止';
            } else {
                return '可提交';
            }
        },
        
        // 处理文件选择
        handleFileChange(event) {
            this.selectedFiles = Array.from(event.target.files);
        },
        
        // 提交作业
        async submitHomework() {
            try {
                if (this.selectedFiles.length === 0) {
                    alert('请选择要提交的文件');
                    return;
                }
                
                const formData = new FormData();
                formData.append('studentName', this.studentName);
                formData.append('studentId', this.studentId);
                formData.append('homeworkId', this.selectedHomework.id);
                formData.append('description', this.description);
                
                // 添加多个文件
                this.selectedFiles.forEach((file, index) => {
                    formData.append(`file${index}`, file);
                });
                formData.append('fileCount', this.selectedFiles.length);

                const response = await axios.post(`${this.apiBaseUrl}/api/homework/upload`, formData, {
                    headers: {
                        'Content-Type': 'multipart/form-data'
                    }
                });

                if (response.data.success) {
                    alert('作业提交成功！');
                    this.backToHomeworkList();
                } else {
                    alert(response.data.message || '提交作业失败，请重试。');
                }
            } catch (error) {
                console.error('提交作业时出错：', error);
                if (error.response && error.response.data && error.response.data.message) {
                    alert(error.response.data.message);
                } else {
                    alert('提交作业失败，请重试。');
                }
            }
        },
        
        // 重置表单
        resetForm() {
            this.studentName = '';
            this.studentId = '';
            this.description = '';
            this.selectedFiles = [];
            document.getElementById('file').value = '';
        }
    },
    mounted() {
        this.fetchHomeworkList();
    }
}); 
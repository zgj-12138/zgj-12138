new Vue({
    el: '#queryApp',
    data: {
        queryParams: {
            studentId: '',
            studentName: ''
        },
        filteredSubmissions: [],
        isLoading: false
    },
    methods: {
        async handleResubmit(submission) {
            if (!confirm(`确定要删除【${submission.courseName}】的历史提交并重新上传？`)) return;
            
            try {
                const res = await axios.delete(`/api/submissions/${submission.homework_id}/${submission.student_id}`, {
                    params: { studentName: submission.student_name }
                });
                
                if (res.data.success) {
                    alert('历史记录已清除，请到作业提交页面重新上传');
                    this.fetchSubmissions(); // 刷新列表
                } else {
                    throw new Error(res.data.message);
                }
            } catch (error) {
                alert(`删除失败: ${error.message}`);
            }
        },
        // 点击查询按钮触发的方法
        fetchSubmissions() {
            this.isLoading = true;
            
            // 根据文档1的API结构，需要自行实现服务端过滤
            axios.get('/api/submissions', {
                params: {
                    studentId: this.queryParams.studentId,
                    studentName: this.queryParams.studentName
                }
            }).then(response => {
                if (response.data.submissions) {
                    this.filteredSubmissions = response.data.submissions.map(sub => ({
                        ...sub,
                        submit_time: new Date(sub.submit_time).toLocaleString()
                    }));
                }
            }).catch(error => {
                console.error('查询失败:', error);
                alert('查询失败，请检查输入条件');
            }).finally(() => {
                this.isLoading = false;
            });
        }
    },
    mounted() {
        // 初始化时不自动加载数据
    }
});
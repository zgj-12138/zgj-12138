new Vue({
    el: '#app',
    data: {
        updateNotice: '',
        apiBaseUrl: 'http://5.181.225.107:26754'
    },
    created() {
        this.fetchUpdateNotice();
    },
    methods: {
        fetchUpdateNotice() {
            fetch('/api/update-notice')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        this.updateNotice = data.notice;
                    }
                })
                .catch(error => {
                    console.error('获取更新说明失败:', error);
                });
        }
    }
}); 
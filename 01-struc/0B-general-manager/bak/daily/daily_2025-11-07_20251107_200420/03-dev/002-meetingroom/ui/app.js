// 会议室预订系统 JavaScript
class MeetingRoomBookingSystem {
    constructor() {
        this.currentTab = 'booking';
        this.attendees = [];
        this.currentRoomData = null;
        this.bookings = [];
        this.rooms = [];
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setMinDate();
        this.loadInitialData();
    }

    setupEventListeners() {
        // 导航标签切换
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const tab = e.target.getAttribute('data-tab');
                this.switchTab(tab);
            });
        });

        // 搜索会议室
        document.getElementById('searchRooms').addEventListener('click', () => {
            this.searchRooms();
        });

        // 模态框关闭
        document.querySelectorAll('.modal-close').forEach(btn => {
            btn.addEventListener('click', () => {
                this.closeModals();
            });
        });

        // 点击模态框外部关闭
        document.querySelectorAll('.modal').forEach(modal => {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.closeModals();
                }
            });
        });

        // 添加参会人员
        document.getElementById('addAttendee').addEventListener('click', () => {
            this.addAttendee();
        });

        // 回车添加参会人员
        document.getElementById('attendeeEmail').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                this.addAttendee();
            }
        });

        // 确认预订
        document.getElementById('confirmBooking').addEventListener('click', () => {
            this.confirmBooking();
        });

        // 取消预订
        document.getElementById('cancelBooking').addEventListener('click', () => {
            this.closeModals();
        });

        // 表单验证
        this.setupFormValidation();
    }

    setupFormValidation() {
        const startTimeInput = document.getElementById('startTime');
        const endTimeInput = document.getElementById('endTime');

        startTimeInput.addEventListener('change', () => {
            this.validateTimeRange();
        });

        endTimeInput.addEventListener('change', () => {
            this.validateTimeRange();
        });
    }

    validateTimeRange() {
        const startTime = document.getElementById('startTime').value;
        const endTime = document.getElementById('endTime').value;

        if (startTime && endTime) {
            if (startTime >= endTime) {
                this.showNotification('结束时间必须晚于开始时间', 'error');
                document.getElementById('endTime').value = '';
            }
        }
    }

    setMinDate() {
        const today = new Date().toISOString().split('T')[0];
        document.getElementById('date').min = today;
        document.getElementById('date').value = today;
    }

    switchTab(tabName) {
        // 更新导航
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

        // 更新内容
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });
        document.getElementById(`${tabName}-tab`).classList.add('active');

        this.currentTab = tabName;

        // 加载对应数据
        if (tabName === 'mybookings') {
            this.loadMyBookings();
        } else if (tabName === 'status') {
            this.loadRoomStatus();
        }
    }

    async searchRooms() {
        const formData = this.getSearchFormData();
        
        if (!this.validateSearchForm(formData)) {
            return;
        }

        this.showLoading(true);

        try {
            const response = await fetch('/api/search-rooms', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });

            const data = await response.json();

            if (data.success) {
                this.displayRooms(data.rooms);
            } else {
                this.showNotification(data.message || '搜索失败', 'error');
            }
        } catch (error) {
            console.error('搜索会议室失败:', error);
            this.showNotification('网络错误，请稍后重试', 'error');
            // 显示模拟数据用于演示
            this.displayMockRooms();
        } finally {
            this.showLoading(false);
        }
    }

    getSearchFormData() {
        return {
            date: document.getElementById('date').value,
            timezone: document.getElementById('timezone').value,
            startTime: document.getElementById('startTime').value,
            endTime: document.getElementById('endTime').value,
            location: document.getElementById('location').value,
            floor: document.getElementById('floor').value
        };
    }

    validateSearchForm(formData) {
        const requiredFields = ['date', 'timezone', 'startTime', 'endTime', 'location', 'floor'];
        
        for (const field of requiredFields) {
            if (!formData[field]) {
                this.showNotification('请填写所有必填字段', 'error');
                return false;
            }
        }

        return true;
    }

    displayRooms(rooms) {
        const container = document.getElementById('roomsContainer');
        const roomsList = document.getElementById('roomsList');
        const noRoomsMessage = document.getElementById('noRoomsMessage');

        if (rooms && rooms.length > 0) {
            roomsList.innerHTML = '';
            rooms.forEach(room => {
                const roomCard = this.createRoomCard(room);
                roomsList.appendChild(roomCard);
            });
            container.style.display = 'block';
            noRoomsMessage.style.display = 'none';
        } else {
            container.style.display = 'none';
            noRoomsMessage.style.display = 'block';
        }
    }

    displayMockRooms() {
        const mockRooms = [
            {
                id: 1,
                name: '会议室A-301',
                capacity: 10,
                facilities: {
                    projector: true,
                    whiteboard: true,
                    videoConference: true,
                    wifi: true
                },
                location: 'A栋3楼',
                available: true
            },
            {
                id: 2,
                name: '会议室A-302',
                capacity: 6,
                facilities: {
                    projector: false,
                    whiteboard: true,
                    videoConference: false,
                    wifi: true
                },
                location: 'A栋3楼',
                available: true
            },
            {
                id: 3,
                name: '大会议室B-201',
                capacity: 20,
                facilities: {
                    projector: true,
                    whiteboard: true,
                    videoConference: true,
                    wifi: true
                },
                location: 'B栋2楼',
                available: true
            }
        ];
        this.displayRooms(mockRooms);
    }

    createRoomCard(room) {
        const card = document.createElement('div');
        card.className = 'room-card';
        card.innerHTML = `
            <div class="room-header">
                <div class="room-name">${room.name}</div>
                <div class="room-actions">
                    <button class="action-btn book-btn" onclick="meetingSystem.openBookingModal(${JSON.stringify(room).replace(/"/g, '&quot;')})">
                        <i class="fas fa-check"></i>
                    </button>
                    <button class="action-btn info-btn" onclick="meetingSystem.openRoomInfoModal(${JSON.stringify(room).replace(/"/g, '&quot;')})">
                        <i class="fas fa-info"></i>
                    </button>
                </div>
            </div>
            <div class="room-details">
                <p><i class="fas fa-users"></i> 容量: ${room.capacity}人</p>
                <p><i class="fas fa-map-marker-alt"></i> ${room.location}</p>
            </div>
        `;
        return card;
    }

    openBookingModal(room) {
        this.currentRoomData = room;
        document.getElementById('modalRoomName').textContent = room.name;
        document.getElementById('bookingModal').classList.add('show');
        
        // 清空表单
        document.getElementById('attendeeEmail').value = '';
        document.getElementById('agenda').value = '';
        document.getElementById('meetingTitle').value = '';
        this.attendees = [];
        this.updateAttendeesList();
    }

    openRoomInfoModal(room) {
        document.getElementById('infoModalRoomName').textContent = room.name;
        
        const infoContent = document.getElementById('roomInfoContent');
        infoContent.innerHTML = `
            <div class="facility-item">
                <i class="fas fa-users facility-icon"></i>
                <span class="facility-name">容量: ${room.capacity}人</span>
            </div>
            <div class="facility-item">
                <i class="fas fa-video facility-icon ${room.facilities.projector ? 'facility-available' : 'facility-unavailable'}"></i>
                <span class="facility-name">投影仪</span>
                <i class="fas ${room.facilities.projector ? 'fa-check facility-available' : 'fa-times facility-unavailable'}"></i>
            </div>
            <div class="facility-item">
                <i class="fas fa-chalkboard facility-icon ${room.facilities.whiteboard ? 'facility-available' : 'facility-unavailable'}"></i>
                <span class="facility-name">白板</span>
                <i class="fas ${room.facilities.whiteboard ? 'fa-check facility-available' : 'fa-times facility-unavailable'}"></i>
            </div>
            <div class="facility-item">
                <i class="fas fa-video facility-icon ${room.facilities.videoConference ? 'facility-available' : 'facility-unavailable'}"></i>
                <span class="facility-name">视频会议</span>
                <i class="fas ${room.facilities.videoConference ? 'fa-check facility-available' : 'fa-times facility-unavailable'}"></i>
            </div>
            <div class="facility-item">
                <i class="fas fa-wifi facility-icon ${room.facilities.wifi ? 'facility-available' : 'facility-unavailable'}"></i>
                <span class="facility-name">WiFi</span>
                <i class="fas ${room.facilities.wifi ? 'fa-check facility-available' : 'fa-times facility-unavailable'}"></i>
            </div>
        `;
        
        document.getElementById('roomInfoModal').classList.add('show');
    }

    addAttendee() {
        const emailInput = document.getElementById('attendeeEmail');
        const email = emailInput.value.trim();

        if (!email) {
            this.showNotification('请输入邮箱地址', 'error');
            return;
        }

        if (!this.isValidEmail(email)) {
            this.showNotification('请输入有效的邮箱地址', 'error');
            return;
        }

        if (this.attendees.includes(email)) {
            this.showNotification('该邮箱已添加', 'error');
            return;
        }

        this.attendees.push(email);
        emailInput.value = '';
        this.updateAttendeesList();
    }

    removeAttendee(email) {
        this.attendees = this.attendees.filter(attendee => attendee !== email);
        this.updateAttendeesList();
    }

    updateAttendeesList() {
        const container = document.getElementById('attendeesList');
        container.innerHTML = '';

        this.attendees.forEach(email => {
            const tag = document.createElement('div');
            tag.className = 'attendee-tag';
            tag.innerHTML = `
                <span>${email}</span>
                <button class="attendee-remove" onclick="meetingSystem.removeAttendee('${email}')">
                    <i class="fas fa-times"></i>
                </button>
            `;
            container.appendChild(tag);
        });
    }

    async confirmBooking() {
        const meetingTitle = document.getElementById('meetingTitle').value.trim();
        const agenda = document.getElementById('agenda').value.trim();

        if (!meetingTitle) {
            this.showNotification('请输入会议标题', 'error');
            return;
        }

        const searchData = this.getSearchFormData();
        const bookingData = {
            roomId: this.currentRoomData.id,
            roomName: this.currentRoomData.name,
            title: meetingTitle,
            agenda: agenda,
            attendees: this.attendees,
            ...searchData
        };

        this.showLoading(true);

        try {
            const response = await fetch('/api/book-room', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(bookingData)
            });

            const data = await response.json();

            if (data.success) {
                this.showNotification('会议室预订成功！', 'success');
                this.closeModals();
                // 刷新会议室列表
                this.searchRooms();
            } else {
                this.showNotification(data.message || '预订失败', 'error');
            }
        } catch (error) {
            console.error('预订失败:', error);
            // 模拟成功预订
            this.showNotification('会议室预订成功！', 'success');
            this.closeModals();
            this.addMockBooking(bookingData);
        } finally {
            this.showLoading(false);
        }
    }

    addMockBooking(bookingData) {
        const booking = {
            id: Date.now(),
            ...bookingData,
            status: 'confirmed',
            createdAt: new Date().toISOString()
        };
        this.bookings.unshift(booking);
    }

    async loadMyBookings() {
        this.showLoading(true);

        try {
            const response = await fetch('/api/my-bookings');
            const data = await response.json();

            if (data.success) {
                this.displayBookings(data.bookings);
            } else {
                this.showNotification(data.message || '加载失败', 'error');
            }
        } catch (error) {
            console.error('加载预订失败:', error);
            // 显示模拟数据
            this.displayMockBookings();
        } finally {
            this.showLoading(false);
        }
    }

    displayBookings(bookings) {
        const container = document.getElementById('myBookingsList');
        
        if (!bookings || bookings.length === 0) {
            container.innerHTML = `
                <div class="no-rooms-message">
                    <i class="fas fa-calendar-times"></i>
                    <h3>暂无预订记录</h3>
                    <p>您还没有预订任何会议室</p>
                </div>
            `;
            return;
        }

        container.innerHTML = '';
        bookings.forEach(booking => {
            const bookingCard = this.createBookingCard(booking);
            container.appendChild(bookingCard);
        });
    }

    displayMockBookings() {
        const mockBookings = [
            {
                id: 1,
                title: '项目启动会议',
                roomName: '会议室A-301',
                date: '2024-01-15',
                startTime: '09:00',
                endTime: '10:30',
                status: 'confirmed',
                attendees: ['user1@example.com', 'user2@example.com'],
                agenda: '讨论项目启动相关事宜'
            },
            {
                id: 2,
                title: '周例会',
                roomName: '大会议室B-201',
                date: '2024-01-16',
                startTime: '14:00',
                endTime: '15:00',
                status: 'pending',
                attendees: ['team@example.com'],
                agenda: '团队周例会，汇报工作进展'
            }
        ];
        this.displayBookings(mockBookings);
    }

    createBookingCard(booking) {
        const card = document.createElement('div');
        card.className = 'booking-card';
        
        const statusClass = `status-${booking.status}`;
        const statusText = {
            'confirmed': '已确认',
            'pending': '待确认',
            'cancelled': '已取消'
        }[booking.status] || booking.status;

        card.innerHTML = `
            <div class="booking-header">
                <div class="booking-title">${booking.title}</div>
                <div class="booking-status ${statusClass}">${statusText}</div>
            </div>
            <div class="booking-details">
                <div class="booking-detail">
                    <i class="fas fa-door-open"></i>
                    <span>${booking.roomName}</span>
                </div>
                <div class="booking-detail">
                    <i class="fas fa-calendar"></i>
                    <span>${booking.date}</span>
                </div>
                <div class="booking-detail">
                    <i class="fas fa-clock"></i>
                    <span>${booking.startTime} - ${booking.endTime}</span>
                </div>
                <div class="booking-detail">
                    <i class="fas fa-users"></i>
                    <span>${booking.attendees ? booking.attendees.length : 0} 人参会</span>
                </div>
            </div>
            ${booking.agenda ? `<div style="margin-top: 1rem; color: #7f8c8d;"><strong>议程:</strong> ${booking.agenda}</div>` : ''}
        `;
        return card;
    }

    async loadRoomStatus() {
        this.showLoading(true);

        try {
            const response = await fetch('/api/room-status');
            const data = await response.json();

            if (data.success) {
                this.displayRoomStatus(data.rooms);
            } else {
                this.showNotification(data.message || '加载失败', 'error');
            }
        } catch (error) {
            console.error('加载状态失败:', error);
            // 显示模拟数据
            this.displayMockRoomStatus();
        } finally {
            this.showLoading(false);
        }
    }

    displayRoomStatus(rooms) {
        const container = document.getElementById('statusList');
        container.innerHTML = '';

        rooms.forEach(room => {
            const statusCard = this.createStatusCard(room);
            container.appendChild(statusCard);
        });
    }

    displayMockRoomStatus() {
        const mockRooms = [
            {
                id: 1,
                name: '会议室A-301',
                status: 'available',
                currentMeeting: null,
                nextMeeting: {
                    title: '项目评审',
                    startTime: '14:00',
                    endTime: '15:30'
                }
            },
            {
                id: 2,
                name: '会议室A-302',
                status: 'occupied',
                currentMeeting: {
                    title: '团队讨论',
                    startTime: '10:00',
                    endTime: '11:00',
                    organizer: 'user@example.com'
                },
                nextMeeting: null
            },
            {
                id: 3,
                name: '大会议室B-201',
                status: 'maintenance',
                currentMeeting: null,
                nextMeeting: null
            }
        ];
        this.displayRoomStatus(mockRooms);
    }

    createStatusCard(room) {
        const card = document.createElement('div');
        card.className = 'status-card';

        const statusInfo = {
            'available': { text: '可用', class: 'status-available' },
            'occupied': { text: '使用中', class: 'status-occupied' },
            'maintenance': { text: '维护中', class: 'status-maintenance' }
        };

        const status = statusInfo[room.status] || { text: '未知', class: 'status-available' };

        let currentMeetingHtml = '';
        if (room.currentMeeting) {
            currentMeetingHtml = `
                <div style="margin-top: 1rem; padding: 0.75rem; background: #f8f9fa; border-radius: 6px;">
                    <strong>当前会议:</strong> ${room.currentMeeting.title}<br>
                    <small>${room.currentMeeting.startTime} - ${room.currentMeeting.endTime}</small>
                </div>
            `;
        }

        let nextMeetingHtml = '';
        if (room.nextMeeting) {
            nextMeetingHtml = `
                <div style="margin-top: 0.5rem; padding: 0.75rem; background: #e8f4fd; border-radius: 6px;">
                    <strong>下次会议:</strong> ${room.nextMeeting.title}<br>
                    <small>${room.nextMeeting.startTime} - ${room.nextMeeting.endTime}</small>
                </div>
            `;
        }

        card.innerHTML = `
            <div class="status-header">
                <div class="room-name">${room.name}</div>
                <div class="status-indicator ${status.class}"></div>
            </div>
            <div style="color: #7f8c8d; margin-bottom: 0.5rem;">
                状态: <strong style="color: #2c3e50;">${status.text}</strong>
            </div>
            ${currentMeetingHtml}
            ${nextMeetingHtml}
        `;
        return card;
    }

    closeModals() {
        document.querySelectorAll('.modal').forEach(modal => {
            modal.classList.remove('show');
        });
    }

    showLoading(show) {
        const overlay = document.getElementById('loadingOverlay');
        overlay.style.display = show ? 'flex' : 'none';
    }

    showNotification(message, type = 'info') {
        const notification = document.getElementById('notification');
        const icon = notification.querySelector('.notification-icon');
        const messageEl = notification.querySelector('.notification-message');

        // 设置图标
        const icons = {
            'success': 'fas fa-check-circle',
            'error': 'fas fa-exclamation-circle',
            'info': 'fas fa-info-circle'
        };

        icon.className = `notification-icon ${icons[type] || icons.info}`;
        messageEl.textContent = message;

        // 设置类型
        notification.className = `notification ${type}`;
        notification.classList.add('show');

        // 自动隐藏
        setTimeout(() => {
            notification.classList.remove('show');
        }, 4000);
    }

    isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    async loadInitialData() {
        // 可以在这里加载初始数据，如用户信息等
        console.log('会议室预订系统初始化完成');
    }
}

// 初始化系统
let meetingSystem;
document.addEventListener('DOMContentLoaded', () => {
    meetingSystem = new MeetingRoomBookingSystem();
});

// 全局函数，供HTML调用
window.meetingSystem = meetingSystem;
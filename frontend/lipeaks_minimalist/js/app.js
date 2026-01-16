// 21天自律打卡 - 主程序

class App {
    constructor() {
        this.container = document.getElementById('app');
        this.currentPage = 'welcome';
        this.selectedThemes = [];
        this.records = this.loadRecords();
        this.cycleStartDate = this.loadCycleStartDate();

        // 检查是否首次使用
        if (this.loadSelectedThemes().length > 0) {
            this.selectedThemes = this.loadSelectedThemes();
            this.currentPage = 'home';
        }

        this.init();
    }

    init() {
        this.render();
    }

    // ========================================
    // 数据持久化
    // ========================================

    loadSelectedThemes() {
        const data = localStorage.getItem('selectedThemes');
        return data ? JSON.parse(data) : [];
    }

    saveSelectedThemes() {
        localStorage.setItem('selectedThemes', JSON.stringify(this.selectedThemes));
    }

    loadRecords() {
        const data = localStorage.getItem('records');
        return data ? JSON.parse(data) : {};
    }

    saveRecords() {
        localStorage.setItem('records', JSON.stringify(this.records));
    }

    loadCycleStartDate() {
        const data = localStorage.getItem('cycleStartDate');
        if (data) return new Date(data);
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        localStorage.setItem('cycleStartDate', today.toISOString());
        return today;
    }

    // ========================================
    // 周期计算
    // ========================================

    getCurrentDay() {
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        const diff = today - this.cycleStartDate;
        const day = Math.floor(diff / (1000 * 60 * 60 * 24)) + 1;
        return Math.min(Math.max(day, 1), 21);
    }

    getTodayKey() {
        return new Date().toISOString().split('T')[0];
    }

    getRecordForDay(themeId, day) {
        const date = new Date(this.cycleStartDate);
        date.setDate(date.getDate() + day - 1);
        const key = date.toISOString().split('T')[0];
        return this.records[`${themeId}-${key}`];
    }

    isThemeCompletedToday(themeId) {
        const key = `${themeId}-${this.getTodayKey()}`;
        return !!this.records[key];
    }

    getThemeStats(themeId) {
        let total = 0;
        let streak = 0;
        let currentStreak = 0;
        const currentDay = this.getCurrentDay();

        for (let i = 1; i <= currentDay; i++) {
            const record = this.getRecordForDay(themeId, i);
            if (record) {
                total++;
                currentStreak++;
            } else {
                if (currentStreak > streak) streak = currentStreak;
                currentStreak = 0;
            }
        }
        if (currentStreak > streak) streak = currentStreak;

        const rate = currentDay > 0 ? Math.round((total / currentDay) * 100) : 0;

        return { total, streak, rate };
    }

    getTotalStats() {
        let totalCheckins = 0;
        let maxStreak = 0;

        this.selectedThemes.forEach(id => {
            const stats = this.getThemeStats(id);
            totalCheckins += stats.total;
            if (stats.streak > maxStreak) maxStreak = stats.streak;
        });

        const avgRate = this.selectedThemes.length > 0
            ? Math.round(this.selectedThemes.reduce((sum, id) => sum + this.getThemeStats(id).rate, 0) / this.selectedThemes.length)
            : 0;

        return { totalCheckins, maxStreak, avgRate };
    }

    // ========================================
    // 页面渲染
    // ========================================

    render() {
        switch (this.currentPage) {
            case 'welcome':
                this.renderWelcome();
                break;
            case 'select':
                this.renderSelect();
                break;
            case 'home':
                this.renderHome();
                break;
            case 'data':
                this.renderData();
                break;
            case 'profile':
                this.renderProfile();
                break;
            case 'checkin':
                this.renderCheckin();
                break;
            case 'theme-detail':
                this.renderThemeDetail();
                break;
        }
    }

    navigateTo(page, data = null) {
        this.currentPage = page;
        this.pageData = data;
        this.render();
        window.scrollTo(0, 0);
    }

    // ========================================
    // 欢迎页
    // ========================================

    renderWelcome() {
        this.container.innerHTML = `
            <div class="page welcome-page">
                <div class="welcome-icon">🌟</div>
                <h1 class="welcome-title">21天自律打卡</h1>
                <p class="welcome-slogan">「坚持 21 天，养成一个好习惯」</p>
                <p class="welcome-desc">
                    选择你想要坚持的自律主题<br>
                    开启属于你的 21 天挑战之旅
                </p>
                <button class="btn btn-white btn-lg" onclick="app.navigateTo('select')">
                    开始选择 →
                </button>
            </div>
        `;
    }

    // ========================================
    // 主题选择页
    // ========================================

    renderSelect() {
        const themesHtml = THEMES.map(theme => {
            const isSelected = this.selectedThemes.includes(theme.id);
            return `
                <div class="theme-card ${isSelected ? 'selected' : ''}" 
                     style="--theme-bg: ${theme.color}10; border-color: ${isSelected ? theme.color : ''};"
                     onclick="app.toggleTheme(${theme.id})">
                    <span class="icon">${theme.icon}</span>
                    <span class="name">${theme.name}</span>
                    <span class="check">✓</span>
                </div>
            `;
        }).join('');

        this.container.innerHTML = `
            <div class="page">
                <div class="page-header">
                    <button class="btn btn-icon btn-back dark" onclick="app.navigateTo('welcome')">←</button>
                    <span class="page-title">选择你的自律主题</span>
                    <label class="select-all">
                        <input type="checkbox" id="selectAll" 
                            ${this.selectedThemes.length === 21 ? 'checked' : ''} 
                            onchange="app.toggleSelectAll(this.checked)">
                        全选
                    </label>
                </div>
                <div class="page-content">
                    <p style="color: var(--gray-500); font-size: 14px; margin-bottom: var(--spacing-md);">
                        点击卡片可查看详情，选择后开始21天挑战
                    </p>
                    <div class="theme-grid">
                        ${themesHtml}
                    </div>
                </div>
                <div class="bottom-bar">
                    <div class="selected-count">已选择 ${this.selectedThemes.length} 个主题</div>
                    <button class="btn btn-primary btn-block" 
                            ${this.selectedThemes.length === 0 ? 'disabled style="opacity:0.5"' : ''}
                            onclick="app.confirmSelection()">
                        确认并开始 21 天挑战
                    </button>
                </div>
            </div>
        `;
    }

    toggleTheme(id) {
        // 先显示详情弹窗
        this.showThemeModal(id);
    }

    showThemeModal(id) {
        const theme = THEMES.find(t => t.id === id);
        const isSelected = this.selectedThemes.includes(id);

        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal animate-slideUp">
                <div class="modal-header" style="background: ${theme.color}; color: white;">
                    <button class="modal-close" onclick="app.closeModal()" style="background: rgba(255,255,255,0.2); color: white;">×</button>
                    <div class="modal-icon">${theme.icon}</div>
                    <div class="modal-title">${theme.name}</div>
                    <div class="modal-subtitle" style="opacity: 0.8;">主题色</div>
                </div>
                <div class="modal-body">
                    <div class="modal-quote">「${theme.quote}」</div>
                    
                    <div class="modal-section">
                        <div class="modal-section-title">🎯 主题目标</div>
                        <div class="modal-section-content">${theme.goal}</div>
                    </div>
                    
                    <div class="modal-section">
                        <div class="modal-section-title">📝 打卡内容</div>
                        <div class="modal-section-content">${theme.content}</div>
                    </div>
                    
                    <div class="modal-section">
                        <div class="modal-section-title">💡 小贴士</div>
                        <div class="modal-section-content">${theme.tip}</div>
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-block ${isSelected ? 'btn-outline' : 'btn-primary'}" 
                            style="${isSelected ? `color: ${theme.color}; border-color: ${theme.color}` : `background: ${theme.color}`}"
                            onclick="app.selectTheme(${id})">
                        ${isSelected ? '✓ 已选择（点击取消）' : '✓ 选择这个主题'}
                    </button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
        setTimeout(() => modal.classList.add('active'), 10);
    }

    selectTheme(id) {
        const index = this.selectedThemes.indexOf(id);
        if (index > -1) {
            this.selectedThemes.splice(index, 1);
        } else {
            this.selectedThemes.push(id);
        }
        this.closeModal();
        this.render();
    }

    closeModal() {
        const modal = document.querySelector('.modal-overlay');
        if (modal) {
            modal.classList.remove('active');
            setTimeout(() => modal.remove(), 200);
        }
    }

    toggleSelectAll(checked) {
        if (checked) {
            this.selectedThemes = THEMES.map(t => t.id);
        } else {
            this.selectedThemes = [];
        }
        this.render();
    }

    confirmSelection() {
        if (this.selectedThemes.length === 0) return;
        this.saveSelectedThemes();
        this.cycleStartDate = new Date();
        this.cycleStartDate.setHours(0, 0, 0, 0);
        localStorage.setItem('cycleStartDate', this.cycleStartDate.toISOString());
        this.navigateTo('home');
    }

    // ========================================
    // 首页
    // ========================================

    renderHome() {
        const currentDay = this.getCurrentDay();
        const progress = Math.round((currentDay / 21) * 100);

        // 排序：未完成的在上面，已完成的在下面
        const sortedThemes = [...this.selectedThemes].sort((a, b) => {
            const aCompleted = this.isThemeCompletedToday(a);
            const bCompleted = this.isThemeCompletedToday(b);
            if (aCompleted === bCompleted) return 0;
            return aCompleted ? 1 : -1;
        });

        const tasksHtml = sortedThemes.map(id => {
            const theme = THEMES.find(t => t.id === id);
            const completed = this.isThemeCompletedToday(id);
            // 已完成的用绿色，未完成的用主题色
            const completedColor = '#10B981';
            return `
                <div class="task-card ${completed ? 'completed' : ''}" 
                     style="${completed ? `background: linear-gradient(135deg, ${completedColor}15, ${completedColor}08); border: 2px solid ${completedColor}40;` : ''}"
                     onclick="app.${completed ? 'viewThemeDetail' : 'startCheckin'}(${id})">
                    <div class="task-icon" style="background: ${completed ? completedColor : theme.color}20;">
                        ${theme.icon}
                    </div>
                    <div class="task-info">
                        <div class="task-name" style="${completed ? `color: ${completedColor}; font-weight: 700;` : ''}">${theme.name}</div>
                        <div class="task-desc">${completed ? this.getRecordSummary(id) : theme.content}</div>
                    </div>
                    <div class="task-action ${completed ? 'done' : 'pending'}" 
                         style="${completed ? `background: ${completedColor}; color: white; padding: 6px 12px; border-radius: 20px; font-size: 13px;` : ''}">
                        ${completed ? '✓ 已完成' : '去打卡 →'}
                    </div>
                </div>
            `;
        }).join('');

        this.container.innerHTML = `
            <div class="page">
                <div class="page-header themed">
                    <span class="page-title">21天自律打卡</span>
                    <span style="font-weight: 600;">Day ${currentDay}</span>
                </div>
                <div class="page-content">
                    <div class="progress-section">
                        <div class="progress-label">周期第 ${currentDay} 天 / 共 21 天</div>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: ${progress}%"></div>
                        </div>
                    </div>

                    <h3 class="section-title">今日待打卡</h3>
                    <div class="task-list">
                        ${tasksHtml}
                    </div>
                </div>
                ${this.renderTabNav('home')}
            </div>
        `;
    }

    getRecordSummary(themeId) {
        const key = `${themeId}-${this.getTodayKey()}`;
        const record = this.records[key];
        if (!record) return '';

        // 根据主题类型显示不同摘要
        if (themeId === 2) { // 早睡早起
            return `入睡 ${record.sleepTime || '--'} · 起床 ${record.wakeTime || '--'}`;
        } else if (themeId === 4) { // 运动
            return `${record.exerciseType || '运动'} ${record.duration || 0}分钟`;
        } else if (themeId === 5) { // 阅读
            return `${record.bookName || '阅读'} ${record.pages || 0}页`;
        } else {
            return record.content ? record.content.slice(0, 20) + '...' : '已完成';
        }
    }

    // ========================================
    // 打卡页面
    // ========================================

    startCheckin(themeId) {
        this.checkinThemeId = themeId;
        this.navigateTo('checkin');
    }

    renderCheckin() {
        const theme = THEMES.find(t => t.id === this.checkinThemeId);
        let formHtml = '';

        // 根据主题生成不同表单
        switch (this.checkinThemeId) {
            case 2: // 早睡早起
                formHtml = this.renderSleepForm();
                break;
            case 4: // 运动
                formHtml = this.renderExerciseForm();
                break;
            case 5: // 阅读
                formHtml = this.renderReadingForm();
                break;
            case 18: // 情绪管理
                formHtml = this.renderMoodForm();
                break;
            default:
                formHtml = this.renderDefaultForm(theme);
        }

        this.container.innerHTML = `
            <div class="page">
                <div class="page-header themed" style="background: linear-gradient(135deg, ${theme.color}, ${this.adjustColor(theme.color, -20)});">
                    <button class="btn btn-icon btn-back" onclick="app.navigateTo('home')">←</button>
                    <div>
                        <div class="page-title">${theme.name} ${theme.icon}</div>
                    </div>
                    <div style="width: 44px;"></div>
                </div>
                <div class="page-content">
                    ${formHtml}
                    
                    <div class="form-group">
                        <label class="form-label">是否拖延</label>
                        <div class="delay-toggle" id="delayToggle">
                            <div class="delay-option no active" onclick="app.setDelay(false)">✓ 未拖延</div>
                            <div class="delay-option yes" onclick="app.setDelay(true)">✗ 拖延了</div>
                        </div>
                    </div>
                    
                    <button class="btn btn-primary btn-block btn-lg" 
                            style="background: ${theme.color}; margin-top: var(--spacing-xl);"
                            onclick="app.submitCheckin()">
                        提交打卡
                    </button>
                </div>
            </div>
        `;

        this.checkinData = { delayed: false };
    }

    renderSleepForm() {
        return `
            <div class="form-group">
                <label class="form-label">实际入睡时间</label>
                <div class="time-picker">
                    <input type="time" class="form-input time-input" id="sleepTime" value="22:30">
                    <button class="time-now-btn" onclick="app.setNowTime('sleepTime')">🕐 现在</button>
                </div>
                <div class="quick-times">
                    ${SLEEP_TIMES.map(t => `<button class="quick-time-btn" onclick="app.setQuickTime('sleepTime', '${t}')">${t}</button>`).join('')}
                </div>
            </div>
            
            <div class="form-group">
                <label class="form-label">实际起床时间</label>
                <div class="time-picker">
                    <input type="time" class="form-input time-input" id="wakeTime" value="06:30">
                    <button class="time-now-btn" onclick="app.setNowTime('wakeTime')">🕐 现在</button>
                </div>
                <div class="quick-times">
                    ${WAKE_TIMES.map(t => `<button class="quick-time-btn" onclick="app.setQuickTime('wakeTime', '${t}')">${t}</button>`).join('')}
                </div>
            </div>
        `;
    }

    renderExerciseForm() {
        return `
            <div class="form-group">
                <label class="form-label">运动类型</label>
                <select class="form-input form-select" id="exerciseType">
                    ${EXERCISE_TYPES.map(t => `<option value="${t}">${t}</option>`).join('')}
                </select>
            </div>
            
            <div class="form-group">
                <label class="form-label">运动时长（分钟）</label>
                <input type="number" class="form-input" id="duration" value="30" min="1" max="300">
            </div>
        `;
    }

    renderReadingForm() {
        return `
            <div class="form-group">
                <label class="form-label">书籍名称</label>
                <input type="text" class="form-input" id="bookName" placeholder="请输入书籍名称">
            </div>
            
            <div class="form-group">
                <label class="form-label">今日阅读页数</label>
                <input type="number" class="form-input" id="pages" value="20" min="1">
            </div>
        `;
    }

    renderMoodForm() {
        return `
            <div class="form-group">
                <label class="form-label">今日情绪状态</label>
                <select class="form-input form-select" id="mood">
                    ${MOOD_OPTIONS.map(m => `<option value="${m}">${m}</option>`).join('')}
                </select>
            </div>
            
            <div class="form-group">
                <label class="form-label">情绪调节方法</label>
                <textarea class="form-input form-textarea" id="moodContent" placeholder="记录你的情绪调节方法..."></textarea>
            </div>
        `;
    }

    renderDefaultForm(theme) {
        return `
            <div class="form-group">
                <label class="form-label">${theme.content}</label>
                <textarea class="form-input form-textarea" id="content" placeholder="请输入..."></textarea>
            </div>
        `;
    }

    setNowTime(inputId) {
        const now = new Date();
        const time = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;
        document.getElementById(inputId).value = time;
    }

    setQuickTime(inputId, time) {
        document.getElementById(inputId).value = time;
        // 更新按钮状态
        const buttons = document.querySelectorAll('.quick-time-btn');
        buttons.forEach(btn => btn.classList.remove('active'));
        event.target.classList.add('active');
    }

    setDelay(delayed) {
        this.checkinData.delayed = delayed;
        const options = document.querySelectorAll('.delay-option');
        options.forEach(opt => opt.classList.remove('active'));
        document.querySelector(`.delay-option.${delayed ? 'yes' : 'no'}`).classList.add('active');
    }

    submitCheckin() {
        const key = `${this.checkinThemeId}-${this.getTodayKey()}`;
        const record = {
            date: this.getTodayKey(),
            delayed: this.checkinData.delayed
        };

        // 根据主题收集数据
        switch (this.checkinThemeId) {
            case 2:
                record.sleepTime = document.getElementById('sleepTime')?.value;
                record.wakeTime = document.getElementById('wakeTime')?.value;
                break;
            case 4:
                record.exerciseType = document.getElementById('exerciseType')?.value;
                record.duration = document.getElementById('duration')?.value;
                break;
            case 5:
                record.bookName = document.getElementById('bookName')?.value;
                record.pages = document.getElementById('pages')?.value;
                break;
            case 18:
                record.mood = document.getElementById('mood')?.value;
                record.content = document.getElementById('moodContent')?.value;
                break;
            default:
                record.content = document.getElementById('content')?.value;
        }

        this.records[key] = record;
        this.saveRecords();

        // 显示成功弹窗
        this.showSuccessModal();
    }

    showSuccessModal() {
        const theme = THEMES.find(t => t.id === this.checkinThemeId);
        const todayCount = this.selectedThemes.filter(id => this.isThemeCompletedToday(id)).length;
        const currentDay = this.getCurrentDay();

        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal success-modal animate-slideUp">
                <div class="modal-header">
                    <div class="success-icon">✅</div>
                    <div class="modal-title">已完成「${theme.name}」打卡</div>
                </div>
                <div class="modal-body" style="text-align: center;">
                    <div class="success-stats">
                        <div class="success-stat">
                            <div class="success-stat-icon">📊</div>
                            <div class="success-stat-text">今日累计打卡 ${todayCount} 项</div>
                        </div>
                    </div>
                    <div class="success-stat">
                        <div class="success-stat-icon">🔥</div>
                        <div class="success-stat-text">21天周期已完成 ${currentDay} 天～</div>
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-primary btn-block" onclick="app.closeSuccessAndGoHome()">
                        太棒了！
                    </button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
        setTimeout(() => modal.classList.add('active'), 10);
    }

    closeSuccessAndGoHome() {
        this.closeModal();
        this.navigateTo('home');
    }

    // ========================================
    // 数据页面
    // ========================================

    renderData() {
        const currentDay = this.getCurrentDay();
        const progress = Math.round((currentDay / 21) * 100);
        const stats = this.getTotalStats();

        // 生成主题卡片
        const themesHtml = this.selectedThemes.map(id => {
            const theme = THEMES.find(t => t.id === id);
            const themeStats = this.getThemeStats(id);
            return `
                <div class="theme-mini-card" onclick="app.viewThemeDetail(${id})" 
                     style="background: ${theme.color}20; text-align: center; padding: var(--spacing-md); border-radius: var(--radius-md); cursor: pointer;">
                    <div style="font-size: 24px;">${theme.icon}</div>
                    <div style="font-size: 18px; font-weight: 700; color: ${theme.color};">${themeStats.total}</div>
                </div>
            `;
        }).join('');

        // 生成日历热力图
        const calendarHtml = this.renderHeatmap();

        this.container.innerHTML = `
            <div class="page">
                <div class="page-header">
                    <span class="page-title" style="flex: 1; text-align: center;">21天周期数据</span>
                </div>
                <div class="page-content">
                    <div class="progress-section">
                        <div class="progress-label">周期第 ${currentDay} 天 / 共 21 天</div>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: ${progress}%"></div>
                        </div>
                    </div>

                    <div class="stats-row">
                        <div class="stat-card">
                            <div class="stat-value">${stats.totalCheckins}</div>
                            <div class="stat-label">累计打卡</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">${stats.maxStreak}</div>
                            <div class="stat-label">最长连续</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">${stats.avgRate}%</div>
                            <div class="stat-label">完成率</div>
                        </div>
                    </div>

                    <h3 class="section-title">打卡主题（点击查看详情）</h3>
                    <div style="display: grid; grid-template-columns: repeat(5, 1fr); gap: var(--spacing-sm); margin-bottom: var(--spacing-lg);">
                        ${themesHtml}
                    </div>

                    <div class="calendar-section">
                        <h3 class="section-title">日历视图</h3>
                        ${calendarHtml}
                    </div>
                </div>
                ${this.renderTabNav('data')}
            </div>
        `;
    }

    renderHeatmap() {
        const weekDays = ['日', '一', '二', '三', '四', '五', '六'];
        const currentDay = this.getCurrentDay();

        let headerHtml = weekDays.map(d => `<span>${d}</span>`).join('');
        let cellsHtml = '';

        // 计算起始日是周几
        const startDayOfWeek = this.cycleStartDate.getDay();

        // 补齐前面的空格
        for (let i = 0; i < startDayOfWeek; i++) {
            cellsHtml += '<div class="heatmap-cell" style="visibility: hidden;"></div>';
        }

        // 渲染21天
        for (let day = 1; day <= 21; day++) {
            const date = new Date(this.cycleStartDate);
            date.setDate(date.getDate() + day - 1);

            let cellClass = 'heatmap-cell';
            let hasCheckin = false;

            // 检查这一天是否有任何打卡
            this.selectedThemes.forEach(id => {
                if (this.getRecordForDay(id, day)) hasCheckin = true;
            });

            if (day === currentDay) {
                cellClass += ' today';
                if (hasCheckin) cellClass += ' done';
            } else if (day < currentDay) {
                cellClass += hasCheckin ? ' done' : ' missed';
            } else {
                cellClass += ' future';
            }

            cellsHtml += `<div class="${cellClass}">${day}</div>`;
        }

        return `
            <div class="heatmap-header">${headerHtml}</div>
            <div class="heatmap">${cellsHtml}</div>
            <div class="heatmap-legend">
                <span><div class="legend-dot done"></div> 已打卡</span>
                <span><div class="legend-dot missed"></div> 未打卡</span>
            </div>
        `;
    }

    viewThemeDetail(themeId) {
        this.detailThemeId = themeId;
        this.navigateTo('theme-detail');
    }

    renderThemeDetail() {
        const theme = THEMES.find(t => t.id === this.detailThemeId);
        const stats = this.getThemeStats(this.detailThemeId);
        const currentDay = this.getCurrentDay();

        // 生成热力图
        let heatmapHtml = '';
        for (let day = 1; day <= 21; day++) {
            const record = this.getRecordForDay(this.detailThemeId, day);
            let cellClass = 'heatmap-cell';

            if (day === currentDay) {
                cellClass += ' today';
                if (record) cellClass += ' done';
            } else if (day < currentDay) {
                cellClass += record ? ' done' : ' missed';
            } else {
                cellClass += ' future';
            }

            heatmapHtml += `<div class="${cellClass}" style="${record ? `background: ${theme.color};` : ''}">${day}</div>`;
        }

        // 生成历史记录
        let historyHtml = '';
        for (let day = currentDay; day >= 1; day--) {
            const record = this.getRecordForDay(this.detailThemeId, day);
            const date = new Date(this.cycleStartDate);
            date.setDate(date.getDate() + day - 1);
            const dateStr = `${String(date.getMonth() + 1).padStart(2, '0')}/${String(date.getDate()).padStart(2, '0')}`;

            if (record) {
                let summary = '';
                if (this.detailThemeId === 2) {
                    summary = `入睡 ${record.sleepTime} · 起床 ${record.wakeTime}`;
                } else if (this.detailThemeId === 4) {
                    summary = `${record.exerciseType} ${record.duration}分钟`;
                } else if (this.detailThemeId === 5) {
                    summary = `${record.bookName} ${record.pages}页`;
                } else {
                    summary = record.content ? record.content.slice(0, 30) : '已完成';
                }
                historyHtml += `
                    <div style="display: flex; align-items: center; padding: var(--spacing-md); border-bottom: 1px solid var(--gray-100);">
                        <span style="color: var(--gray-500); width: 100px;">Day ${day} · ${dateStr}</span>
                        <span style="color: var(--success); margin-right: var(--spacing-sm);">✓</span>
                        <span style="flex: 1; color: var(--gray-700);">${summary}</span>
                    </div>
                `;
            } else {
                historyHtml += `
                    <div style="display: flex; align-items: center; padding: var(--spacing-md); border-bottom: 1px solid var(--gray-100); opacity: 0.6;">
                        <span style="color: var(--gray-500); width: 100px;">Day ${day} · ${dateStr}</span>
                        <span style="color: var(--gray-400); margin-right: var(--spacing-sm);">✗</span>
                        <span style="flex: 1; color: var(--gray-400);">未打卡</span>
                    </div>
                `;
            }
        }

        this.container.innerHTML = `
            <div class="page">
                <div class="page-header" style="background: ${theme.color}; color: white;">
                    <button class="btn btn-icon btn-back" onclick="app.navigateTo('data')">←</button>
                    <div>
                        <div class="page-title">${theme.name} ${theme.icon}</div>
                    </div>
                    <div style="width: 44px;"></div>
                </div>
                <div class="page-content">
                    <div class="stats-row">
                        <div class="stat-card">
                            <div class="stat-value" style="color: ${theme.color};">${stats.total}天</div>
                            <div class="stat-label">累计打卡</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value" style="color: ${theme.color};">${stats.streak}天</div>
                            <div class="stat-label">当前连续</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value" style="color: ${theme.color};">${stats.rate}%</div>
                            <div class="stat-label">完成率</div>
                        </div>
                    </div>

                    <h3 class="section-title">📅 21天热力图</h3>
                    <div class="heatmap" style="margin-bottom: var(--spacing-lg);">
                        ${heatmapHtml}
                    </div>

                    <h3 class="section-title">📋 打卡历史</h3>
                    <div style="background: white; border-radius: var(--radius-md); overflow: hidden; border: 1px solid var(--gray-200);">
                        ${historyHtml}
                    </div>
                </div>
            </div>
        `;
    }

    // ========================================
    // 个人中心
    // ========================================

    renderProfile() {
        const stats = this.getTotalStats();

        this.container.innerHTML = `
            <div class="page">
                <div class="page-header">
                    <span class="page-title" style="flex: 1; text-align: center;">个人中心</span>
                </div>
                <div class="page-content">
                    <div class="profile-header">
                        <div class="profile-avatar">👤</div>
                        <div class="profile-name">自律达人</div>
                    </div>

                    <div class="stats-row">
                        <div class="stat-card">
                            <div class="stat-value">${stats.totalCheckins}</div>
                            <div class="stat-label">累计打卡</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">${stats.maxStreak}</div>
                            <div class="stat-label">连续天数</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">${this.selectedThemes.length}</div>
                            <div class="stat-label">主题数</div>
                        </div>
                    </div>

                    <div class="settings-list">
                        <div class="settings-item" onclick="app.manageThemes()">
                            <span class="settings-icon">⚙️</span>
                            <span class="settings-label">管理打卡主题</span>
                            <span class="settings-value">${this.selectedThemes.length}个</span>
                            <span class="settings-arrow">›</span>
                        </div>
                        <div class="settings-item">
                            <span class="settings-icon">🔔</span>
                            <span class="settings-label">打卡提醒</span>
                            <span class="settings-value">开启</span>
                            <span class="settings-arrow">›</span>
                        </div>
                        <div class="settings-item">
                            <span class="settings-icon">⏰</span>
                            <span class="settings-label">提醒时间</span>
                            <span class="settings-value">20:00</span>
                            <span class="settings-arrow">›</span>
                        </div>
                        <div class="settings-item" onclick="app.resetCycle()">
                            <span class="settings-icon">🔄</span>
                            <span class="settings-label">重置周期</span>
                            <span class="settings-arrow">›</span>
                        </div>
                        <div class="settings-item">
                            <span class="settings-icon">ℹ️</span>
                            <span class="settings-label">关于</span>
                            <span class="settings-arrow">›</span>
                        </div>
                    </div>
                </div>
                ${this.renderTabNav('profile')}
            </div>
        `;
    }

    manageThemes() {
        this.navigateTo('select');
    }

    resetCycle() {
        if (confirm('确定要重置21天周期吗？这将清空所有打卡数据。')) {
            this.records = {};
            this.saveRecords();
            this.cycleStartDate = new Date();
            this.cycleStartDate.setHours(0, 0, 0, 0);
            localStorage.setItem('cycleStartDate', this.cycleStartDate.toISOString());
            this.render();
        }
    }

    // ========================================
    // 底部导航
    // ========================================

    renderTabNav(active) {
        return `
            <div class="tab-nav">
                <div class="tab-item ${active === 'home' ? 'active' : ''}" onclick="app.navigateTo('home')">
                    <span class="icon">🏠</span>
                    <span>首页</span>
                </div>
                <div class="tab-item ${active === 'data' ? 'active' : ''}" onclick="app.navigateTo('data')">
                    <span class="icon">📊</span>
                    <span>数据</span>
                </div>
                <div class="tab-item ${active === 'profile' ? 'active' : ''}" onclick="app.navigateTo('profile')">
                    <span class="icon">👤</span>
                    <span>我的</span>
                </div>
            </div>
        `;
    }

    // ========================================
    // 辅助函数
    // ========================================

    adjustColor(hex, percent) {
        const num = parseInt(hex.replace('#', ''), 16);
        const amt = Math.round(2.55 * percent);
        const R = (num >> 16) + amt;
        const G = (num >> 8 & 0x00FF) + amt;
        const B = (num & 0x0000FF) + amt;
        return '#' + (0x1000000 +
            (R < 255 ? R < 1 ? 0 : R : 255) * 0x10000 +
            (G < 255 ? G < 1 ? 0 : G : 255) * 0x100 +
            (B < 255 ? B < 1 ? 0 : B : 255)
        ).toString(16).slice(1);
    }
}

// 初始化应用
const app = new App();

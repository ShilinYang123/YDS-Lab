// 全局变量定义
let availableVoices = [];
let voiceProfiles = [];
let roleVoiceMapping = {};

// 将变量暴露到全局作用域
window.voiceProfiles = voiceProfiles;
window.roleVoiceMapping = roleVoiceMapping;
window.availableVoices = availableVoices;

// 语音引擎类型枚举
const VoiceEngineType = {
  NATIVE: 'native',
  RESPONSIVE_VOICE: 'responsive_voice',
  AUDIO_FILE: 'audio_file'
};

// ResponsiveVoice语音配置
const responsiveVoiceProfiles = [
  { name: 'ResponsiveVoice 中文女声', voiceId: 'Chinese Female', engine: VoiceEngineType.RESPONSIVE_VOICE, rate: 1.0, pitch: 1.0, volume: 0.8, gender: 'female' },
  { name: 'ResponsiveVoice 中文男声', voiceId: 'Chinese Male', engine: VoiceEngineType.RESPONSIVE_VOICE, rate: 1.0, pitch: 1.0, volume: 0.8, gender: 'male' },
  { name: 'ResponsiveVoice 台湾女声', voiceId: 'Chinese Taiwan Female', engine: VoiceEngineType.RESPONSIVE_VOICE, rate: 1.0, pitch: 1.0, volume: 0.8, gender: 'female' },
  { name: 'ResponsiveVoice 香港女声', voiceId: 'Chinese (Hong Kong) Female', engine: VoiceEngineType.RESPONSIVE_VOICE, rate: 1.0, pitch: 1.0, volume: 0.8, gender: 'female' },
  { name: 'ResponsiveVoice 英语女声', voiceId: 'UK English Female', engine: VoiceEngineType.RESPONSIVE_VOICE, rate: 1.0, pitch: 1.0, volume: 0.8, gender: 'female' },
  { name: 'ResponsiveVoice 英语男声', voiceId: 'UK English Male', engine: VoiceEngineType.RESPONSIVE_VOICE, rate: 1.0, pitch: 1.0, volume: 0.8, gender: 'male' }
];

(() => {
  const els = {
    health: document.getElementById('health-indicator'),
    meetingType: document.getElementById('meeting-type'),
    projectName: document.getElementById('project-name'),
    projectId: document.getElementById('project-id'),
    modelSelect: document.getElementById('model-select'),
    participants: document.getElementById('participants'),
    agenda: document.getElementById('agenda'),
    btnRun: document.getElementById('btn-run'),
    btnRefresh: document.getElementById('btn-refresh'),
    runLog: document.getElementById('run-log'),
    searchInput: document.getElementById('search-input'),
    meetingsList: document.getElementById('meetings-list'),
    detailSection: document.getElementById('detail-section'),
    detailTitle: document.getElementById('detail-title'),
    mdLink: document.getElementById('md-link'),
    meetingInfo: document.getElementById('meeting-info'),
    actionsTable: document.getElementById('actions-table'),
    // RTM
    rtmPanel: document.getElementById('rtm-panel'),
    rtmSid: document.getElementById('rtm-sid'),
    btnRtmStart: document.getElementById('btn-rtm-start'),
    btnRtmEnd: document.getElementById('btn-rtm-end'),
    ttsEnable: document.getElementById('tts-enable'),
    userSay: document.getElementById('user-say'),
    btnUserSay: document.getElementById('btn-user-say'),
    rtmTimeline: document.getElementById('rtm-timeline'),
    // 会议桌视图元素
  meetingRoom: document.getElementById('meeting-room'),
  meetingTableContainer: document.getElementById('meeting-table-container'),
  currentSpeaker: document.getElementById('current-speaker'),
  subtitleContent: document.getElementById('subtitle-content'),
  btnTableView: document.getElementById('btn-table-view'),
    btnTimelineView: document.getElementById('btn-timeline-view'),
    // 文档共享治理
    shareRole: document.getElementById('share-role'),
    sharePath: document.getElementById('share-path'),
    shareTitle: document.getElementById('share-title'),
    btnDocsShare: document.getElementById('btn-docs-share'),
    btnDocsRevoke: document.getElementById('btn-docs-revoke'),
    docsShareList: document.getElementById('docs-share-list'),
    docsShareHint: document.getElementById('docs-share-hint'),
    // 投票管理
    votesRole: document.getElementById('votes-role'),
    votesTitle: document.getElementById('votes-title'),
    votesOptions: document.getElementById('votes-options'),
    votesMeetingId: document.getElementById('votes-meeting-id'),
    btnVoteCreate: document.getElementById('btn-vote-create'),
    btnVoteFinalize: document.getElementById('btn-vote-finalize'),
    votesList: document.getElementById('votes-list'),
    votesHint: document.getElementById('votes-hint'),
    // 语音管理
    voiceRoleCtl: document.getElementById('voice-role'),
    voiceEngineCtl: document.getElementById('voice-engine'),
    voiceTextCtl: document.getElementById('voice-text'),
    btnVoiceStream: document.getElementById('btn-voice-stream'),
    voiceHint: document.getElementById('voice-hint'),
  };

  async function healthCheck() {
    try {
      const r = await fetch('/health');
      const base = await r.json();
      let msg = base.ok ? '后台服务正常' : '后台服务异常';

      // 聚合健康（由后端统一判断首选与默认模型）
      let shimmyOk = false;
      let ollamaOk = false;
      try {
        const rAgg = await fetch('/api/health_models');
        const a = await rAgg.json();
        if (a && a.ok) {
          const pref = (a.preferredBackend || '').toLowerCase();
          shimmyOk = !!(a.shimmy && a.shimmy.ok);
          ollamaOk = !!(a.ollama && a.ollama.ok);
          const parts = [];
          parts.push('首选：' + (pref === 'shimmy' ? 'Shimmy' : 'Ollama'));
          const avail = [];
          if (shimmyOk) avail.push('Shimmy');
          if (ollamaOk) avail.push('Ollama');
          parts.push('可达：' + (avail.length ? avail.join('，') : '无'));
          if (a.defaultModels) {
            parts.push('默认：离线 ' + (a.defaultModels.offline || '—') + '，实时 ' + (a.defaultModels.rtm || '—'));
          }
          msg += ' · ' + parts.join(' · ');
        }
      } catch (_) {}

      els.health.textContent = msg;
      // 仅在两个后端都不可达或后端自身不健康时标红
      els.health.classList.toggle('bad', !(shimmyOk || ollamaOk) || !base.ok);
    } catch (e) {
      els.health.textContent = '后台服务不可达';
      els.health.classList.add('bad');
    }
  }

  function chip(text) {
    const span = document.createElement('span');
    span.className = 'chip';
    span.textContent = text;
    return span;
  }

  function badge(text, level = 'info') {
    const span = document.createElement('span');
    span.className = `badge ${level}`;
    span.textContent = text;
    return span;
  }

  async function loadModels() {
    try {
      const r = await fetch('/api/models');
      const j = await r.json();
      if (j.ok) {
        els.modelSelect.innerHTML = '';
        const def = document.createElement('option');
        def.value = '';
        def.textContent = '（选择模型，未选用默认路由）';
        els.modelSelect.appendChild(def);
        j.data.forEach(m => {
          const opt = document.createElement('option');
          opt.value = m;
          opt.textContent = m;
          els.modelSelect.appendChild(opt);
        });
      }
    } catch (e) {
      // ignore
    }
  }

  function renderMeetings(items) {
    const kw = (els.searchInput.value || '').trim();
    const needle = kw ? kw.toLowerCase() : '';
    els.meetingsList.innerHTML = '';
    items.forEach(it => {
      const hay = JSON.stringify(it).toLowerCase();
      if (needle && !hay.includes(needle)) return;
      const card = document.createElement('div');
      card.className = 'card';
      const actionsCount = it.actions_count || 0;
      card.innerHTML = `
        <div class="card-head">
          <div class="title">${it.base_name || '未知会议'}</div>
          <div class="muted">${it.created_at || ''}</div>
        </div>
        <div class="row small">类型：${it.meeting_type || '—'} · 项目：${it.project || '—'}</div>
        <div class="row">参与者：${(it.participants || []).map(p => `<span class="chip">${p}</span>`).join('')}</div>
        <div class="row">议程：${(it.agenda || []).map(a => `<span class="chip alt">${a}</span>`).join('')}</div>
        <div class="row small">项目目录：${it.project_dir || '未找到'}</div>
        <div class="row small">
          行动项：${actionsCount}
          <span class="spacer"></span>
          ${it.priority_count ? `
            <span class="muted">高</span> ${it.priority_count['高']||0}
            <span class="muted">中</span> ${it.priority_count['中']||0}
            <span class="muted">低</span> ${it.priority_count['低']||0}
          ` : ''}
        </div>
      `;
      card.addEventListener('click', () => openDetail(it.base_name));
      els.meetingsList.appendChild(card);
    });
  }

  async function loadMeetings() {
    const r = await fetch('/api/meetings');
    const j = await r.json();
    if (j.ok) {
      renderMeetings(j.data || []);
    }
  }

  function kv(label, value) {
    const row = document.createElement('div');
    row.className = 'kv-row';
    row.innerHTML = `<div class="k">${label}</div><div class="v">${value}</div>`;
    return row;
  }

  function renderActionsTable(list) {
    const t = els.actionsTable;
    t.innerHTML = '';
    if (!list || !list.length) {
      t.innerHTML = '<tbody><tr><td class="muted">（无行动项）</td></tr></tbody>';
      return;
    }
    // 自动根据第一条记录的键生成表头
    const columns = Object.keys(list[0]);
    const thead = document.createElement('thead');
    const trh = document.createElement('tr');
    columns.forEach(c => {
      const th = document.createElement('th');
      th.textContent = c;
      trh.appendChild(th);
    });
    thead.appendChild(trh);
    t.appendChild(thead);

    const tbody = document.createElement('tbody');
    list.forEach(row => {
      const tr = document.createElement('tr');
      columns.forEach(col => {
        const td = document.createElement('td');
        let v = row[col];
        if (col.includes('优先') && typeof v === 'string') {
          const lvl = v.includes('高') ? 'danger' : (v.includes('中') ? 'warn' : 'ok');
          td.appendChild(badge(v, lvl));
        } else if (typeof v === 'number' && col.includes('%')) {
          td.innerHTML = `<div class="progress"><div class="bar" style="width:${v}%"></div><span>${v}%</span></div>`;
        } else if (Array.isArray(v)) {
          v.forEach(x => td.appendChild(chip(x)));
        } else {
          td.textContent = (v == null ? '' : String(v));
        }
        tr.appendChild(td);
      });
      tbody.appendChild(tr);
    });
    t.appendChild(tbody);
  }

  async function openDetail(baseName) {
    if (!baseName) return;
    const r = await fetch(`/api/meetings/${encodeURIComponent(baseName)}`);
    if (!r.ok) return;
    const j = await r.json();
    els.detailSection.style.display = '';
    els.detailTitle.textContent = baseName;
    els.mdLink.href = `/api/meetings/${encodeURIComponent(baseName)}/md`;

    const sec = j.sections || {};
    const info = sec['会议信息'] || {};
    const actions = sec['行动项与决策'] || [];

    els.meetingInfo.innerHTML = '';
    els.meetingInfo.appendChild(kv('会议类型', info['会议类型'] || ''));
    els.meetingInfo.appendChild(kv('项目', info['项目'] || ''));
    els.meetingInfo.appendChild(kv('项目目录', info['项目目录'] || '未找到'));
    els.meetingInfo.appendChild(kv('参会角色', (info['参会角色'] || []).join('，')));
    els.meetingInfo.appendChild(kv('议程', (info['议程'] || []).join('，')));
    renderActionsTable(actions);
  }

  async function runMeeting() {
    const meeting = els.meetingType.value;
    // 交由后端根据可达性与首选策略自动选择默认模型（优先 Shimmy，不可达时降级 Ollama）
    const model = (els.modelSelect.value || '').trim();
    const project = els.projectName.value.trim() || 'DeWatermark AI';
    const projectId = els.projectId.value.trim();
    const participants = (els.participants.value || '')
      .split(',')
      .map(s => s.trim())
      .filter(Boolean);
    const agenda = (els.agenda.value || '')
      .split(',')
      .map(s => s.trim())
      .filter(Boolean);

    els.runLog.style.display = '';
    els.runLog.textContent = '正在生成会议纪要…\n';
    try {
      const r = await fetch('/api/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ meeting, project, model, participants, agenda, projectId })
      });
      const j = await r.json();
      if (j.ok) {
        els.runLog.textContent += '生成成功\n';
        if (j.meeting_json) {
          const base = j.meeting_json.replace(/\.json$/, '');
          els.runLog.textContent += `最新会议：${base}\n`;
          await loadMeetings();
          await openDetail(base);
          window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
        }
        if (j.stdout) {
          els.runLog.textContent += `\n日志片段:\n${j.stdout}`;
        }
      } else {
        els.runLog.textContent += `生成失败：${j.error || '未知错误'}`;
      }
    } catch (e) {
      els.runLog.textContent += '调用失败：' + e.message;
    }
  }

  els.btnRun.addEventListener('click', runMeeting);
  els.btnRefresh.addEventListener('click', loadMeetings);
  els.searchInput.addEventListener('input', loadMeetings);

  // 语音播报选项记忆功能
  function saveTtsEnableState() {
    if (els.ttsEnable) {
      localStorage.setItem('ttsEnable', els.ttsEnable.checked);
    }
  }

  function loadTtsEnableState() {
    if (els.ttsEnable) {
      const savedState = localStorage.getItem('ttsEnable');
      if (savedState !== null) {
        els.ttsEnable.checked = savedState === 'true';
      }
    }
  }

  // 页面加载时恢复语音播报选项状态
  loadTtsEnableState();

  // 监听语音播报选项变化并自动保存
  if (els.ttsEnable) {
    els.ttsEnable.addEventListener('change', saveTtsEnableState);
  }

  // ========= 实时会议（SSE） =========
  let currentSid = null;
  let es = null;
  let currentViewMode = 'table'; // 'table' 或 'timeline'
  let participantSeats = {}; // 存储参会者座位信息
  let currentSpeakingRole = null; // 当前发言人
  
  // 语音播报缓冲管理
  let speechBuffer = {}; // 按角色缓冲文本
  let speechTimers = {}; // 按角色管理定时器
  
  // 音色库配置 - 10种不同的音色参数
  // 获取可用的语音列表
  
  function loadAvailableVoices() {
    // 加载原生语音
    availableVoices = speechSynthesis.getVoices();
    console.log('可用语音列表:', availableVoices);
  
    if (availableVoices.length === 0) {
      speechSynthesis.addEventListener('voiceschanged', () => {
        availableVoices = speechSynthesis.getVoices();
        console.log('语音加载完成，可用语音列表:', availableVoices);
        updateVoiceProfiles();
      });
    } else {
      updateVoiceProfiles();
    }
  }
  
  function updateVoiceProfiles() {
    // 详细输出所有可用语音信息
    availableVoices.forEach((voice, index) => {
      console.log(`${index}: ${voice.name} | ${voice.lang} | localService: ${voice.localService} | voiceURI: ${voice.voiceURI}`);
    });
  
    // 筛选中文语音
    const chineseVoices = availableVoices.filter(voice =>
      voice.lang.includes('zh') || voice.lang.includes('CN')
    );
  
    // 分类本地和远程语音
    const localChineseVoices = chineseVoices.filter(voice => voice.localService === true);
    const remoteChineseVoices = chineseVoices.filter(voice => voice.localService === false);
  
    // 其他语音
    const localOtherVoices = availableVoices.filter(voice =>
      voice.localService === true && !chineseVoices.includes(voice)
    );
    const remoteOtherVoices = availableVoices.filter(voice =>
      voice.localService === false && !chineseVoices.includes(voice)
    );
  
    // 按优先级排序：本地中文 > 远程中文 > 本地其他 > 远程其他
    const voicesToUse = [
      ...localChineseVoices,
      ...remoteChineseVoices,
      ...localOtherVoices,
      ...remoteOtherVoices
    ];
  
    console.log('本地中文语音:', localChineseVoices);
    console.log('远程中文语音:', remoteChineseVoices);
    console.log('将使用的语音（按优先级排序）:', voicesToUse);
  
    // 重新构建语音配置文件
    voiceProfiles.length = 0; // 清空数组
    window.voiceProfiles.length = 0; // 同时清空全局变量
  
    // 1. 添加ResponsiveVoice语音（优先级最高）
    if (typeof responsiveVoice !== 'undefined') {
      voiceProfiles.push(...responsiveVoiceProfiles);
      window.voiceProfiles.push(...responsiveVoiceProfiles);
      console.log('已添加ResponsiveVoice语音引擎');
    }
  
    // 2. 添加原生语音
    if (voicesToUse.length > 0) {
      // 限制原生语音数量，避免界面过于拥挤
      voicesToUse.slice(0, 6).forEach((voice, index) => {
        // 根据语音名称判断性别
        let gender = 'neutral';
        const voiceName = voice.name.toLowerCase();
        if (voiceName.includes('huihui') || voiceName.includes('yaoyao') || voiceName.includes('female') || voiceName.includes('woman')) {
          gender = 'female';
        } else if (voiceName.includes('kangkang') || voiceName.includes('male') || voiceName.includes('man')) {
          gender = 'male';
        }
        
        const profile = {
          name: `${voice.name}${voice.localService ? ' (本地)' : ' (在线)'}`,
          voice: voice, // 确保每个配置都有独立的语音对象引用
          engine: VoiceEngineType.NATIVE,
          rate: 1.0,
          pitch: 1.0,
          gender: gender,
          localService: voice.localService,
          volume: 0.7
        };
        voiceProfiles.push(profile);
        window.voiceProfiles.push(profile);
      });
    }
  
    // 3. 如果没有可用语音，添加默认配置
    if (voiceProfiles.length === 0) {
      const defaultProfiles = [
        { name: '系统默认语音', voice: null, engine: VoiceEngineType.NATIVE, rate: 1.0, pitch: 1.0, volume: 0.7, gender: 'neutral', localService: true },
        { name: 'ResponsiveVoice 中文', voiceId: 'Chinese Female', engine: VoiceEngineType.RESPONSIVE_VOICE, rate: 1.0, pitch: 1.0, volume: 0.8, gender: 'female' }
      ];
      voiceProfiles.push(...defaultProfiles);
      window.voiceProfiles.push(...defaultProfiles);
    }
  
    console.log('最终音色配置:', voiceProfiles);
  
    // 更新UI
    const modal = document.getElementById('voice-settings-modal');
    if (modal) {
      renderVoiceProfiles();
    }
  }

  // 自动为角色分配音色
  function assignVoiceToRole(role) {
    if (!roleVoiceMapping[role]) {
      // 获取已分配的音色索引
      const assignedIndices = Object.values(roleVoiceMapping);
      
      // 找到第一个未分配的音色索引
      let voiceIndex = 0;
      while (assignedIndices.includes(voiceIndex) && voiceIndex < window.voiceProfiles.length) {
        voiceIndex++;
      }
      
      // 如果所有音色都已分配，则循环使用
      if (voiceIndex >= window.voiceProfiles.length) {
        voiceIndex = assignedIndices.length % window.voiceProfiles.length;
      }
      
      roleVoiceMapping[role] = voiceIndex;
      
      // 保存到localStorage
      localStorage.setItem('roleVoiceMapping', JSON.stringify(roleVoiceMapping));
      
      console.log(`为角色 "${role}" 分配音色: ${window.voiceProfiles[voiceIndex].name}`);
    }
    return roleVoiceMapping[role];
  }
  
  // 从localStorage加载角色音色映射
  function loadRoleVoiceMapping() {
    try {
      const saved = localStorage.getItem('roleVoiceMapping');
      if (saved) {
        roleVoiceMapping = JSON.parse(saved);
        console.log('已加载角色音色映射:', roleVoiceMapping);
      }
    } catch (e) {
      console.warn('加载角色音色映射失败:', e);
      roleVoiceMapping = {};
    }
  }
  
  // 获取角色的音色配置
  function getVoiceProfile(role) {
    const voiceIndex = assignVoiceToRole(role);
    return window.voiceProfiles[voiceIndex];
  }

  // 会议桌视图相关函数
  function createMeetingTable(participants) {
    if (!els.meetingTableContainer) return;
    
    // 清空容器
    els.meetingTableContainer.innerHTML = '';
    participantSeats = {};
    
    // 创建椭圆形会议桌
    const tableOval = document.createElement('div');
    tableOval.className = 'meeting-table-oval';
    els.meetingTableContainer.appendChild(tableOval);
    
    // 为每个参会者创建座位
    participants.forEach((participant, index) => {
      const seat = createParticipantSeat(participant, index, participants.length);
      els.meetingTableContainer.appendChild(seat);
      participantSeats[participant] = seat;
    });
  }

  function createParticipantSeat(participant, index, total) {
    const seat = document.createElement('div');
    seat.className = 'participant-seat';
    seat.dataset.participant = participant;
    
    // 计算座位位置（围绕椭圆分布）
    const angle = (index / total) * 2 * Math.PI - Math.PI / 2; // 从顶部开始
    const radiusX = 180; // 椭圆长轴半径
    const radiusY = 120; // 椭圆短轴半径
    const x = 50 + (radiusX * Math.cos(angle)) / 3.6; // 转换为百分比
    const y = 50 + (radiusY * Math.sin(angle)) / 3.6;
    
    seat.style.left = `${x}%`;
    seat.style.top = `${y}%`;
    
    // 创建头像（使用emoji或首字符）
    const avatar = document.createElement('div');
    avatar.className = 'participant-avatar';
    avatar.textContent = getParticipantAvatar(participant);
    
    // 创建姓名标签
    const name = document.createElement('div');
    name.className = 'participant-name';
    name.textContent = participant;
    
    seat.appendChild(avatar);
    seat.appendChild(name);
    
    // 添加点击事件
    seat.addEventListener('click', () => {
      showParticipantInfo(participant);
    });
    
    return seat;
  }

  function getParticipantAvatar(participant) {
    // 根据角色返回对应的emoji
    const avatarMap = {
      '总经理': '👔', 'CEO': '👔',
      '企划总监': '📊', '企划': '📊',
      '财务总监': '💰', '财务': '💰',
      '开发总监': '💻', '开发': '💻',
      '市场总监': '📈', '市场': '📈',
      '资源与行政': '📋', '行政': '📋',
      '技术总监': '⚙️', '技术': '⚙️'
    };
    
    for (const [key, emoji] of Object.entries(avatarMap)) {
      if (participant.includes(key)) {
        return emoji;
      }
    }
    
    // 默认返回参会者姓名的首字符
    return participant.charAt(0);
  }

  function showParticipantInfo(participant) {
    // 可以在这里添加显示参会者详细信息的逻辑
    console.log('点击了参会者:', participant);
  }

  function highlightSpeaker(role) {
    // 清除之前的高亮
    if (currentSpeakingRole && participantSeats[currentSpeakingRole]) {
      participantSeats[currentSpeakingRole].classList.remove('speaking');
    }
    
    // 高亮当前发言人
    if (role && participantSeats[role]) {
      participantSeats[role].classList.add('speaking');
      currentSpeakingRole = role;
      
      // 更新当前发言人显示
      if (els.currentSpeaker) {
        els.currentSpeaker.textContent = role;
        els.currentSpeaker.classList.add('speaking');
      }
    } else {
      currentSpeakingRole = null;
      if (els.currentSpeaker) {
        els.currentSpeaker.textContent = '等待发言...';
        els.currentSpeaker.classList.remove('speaking');
      }
    }
  }

  function updateSubtitle(text, role = null) {
    if (els.subtitleContent) {
      // 检查内容是否超出限制，如果超出则清理旧内容
      const maxLines = 20; // 最大显示行数
      const currentLines = els.subtitleContent.innerHTML.split('<br>').length;
      
      if (currentLines > maxLines) {
        // 保留最后10行内容，删除前面的内容
        const lines = els.subtitleContent.innerHTML.split('<br>');
        const keepLines = lines.slice(-10);
        els.subtitleContent.innerHTML = keepLines.join('<br>');
      }
      
      // 检查是否需要添加换行符（如果内容区域不为空且不以换行结尾）
      const currentContent = els.subtitleContent.innerHTML;
      if (currentContent && currentContent.trim() !== '' && !currentContent.endsWith('<br>')) {
        els.subtitleContent.innerHTML += '<br>';
      }
      
      if (role) {
        els.subtitleContent.innerHTML += `<strong>${role}:</strong> ${text}<br>`;
      } else {
        els.subtitleContent.innerHTML += text + '<br>';
      }
      // 自动滚动到底部
      els.subtitleContent.scrollTop = els.subtitleContent.scrollHeight;
    }
  }

  function switchView(mode) {
    currentViewMode = mode;
    
    if (mode === 'table') {
      document.querySelector('.meeting-room').style.display = 'block';
      els.rtmTimeline.style.display = 'none';
      els.btnTableView.classList.add('active');
      els.btnTimelineView.classList.remove('active');
    } else {
      document.querySelector('.meeting-room').style.display = 'none';
      els.rtmTimeline.style.display = 'block';
      els.btnTableView.classList.remove('active');
      els.btnTimelineView.classList.add('active');
    }
  }

  function appendLine(role, text, kind = 'say') {
    const li = document.createElement('li');
    li.className = `rtm-item ${kind}`;
    li.innerHTML = `<span class="role">${role}</span><span class="text"></span>`;
    els.rtmTimeline.appendChild(li);
    els.rtmTimeline.scrollTop = els.rtmTimeline.scrollHeight;
    
    const textSpan = li.querySelector('.text');
    
    // 如果是发言内容，使用打字机效果
    if (kind === 'say' && text && text.length > 0) {
      typewriterEffect(textSpan, text, 160); // 160ms间隔，降低到0.5倍速度
      
      // 更新会议桌视图
      if (currentViewMode === 'table') {
        if (role !== '我' && role !== '系统') {
          highlightSpeaker(role);
          typewriterSubtitle(text, role, 160); // 同步字幕打字机效果，0.5倍速度
        }
      }
    } else {
      // 系统消息直接显示
      textSpan.textContent = text;
      
      // 更新会议桌视图
      if (currentViewMode === 'table') {
        if (kind === 'system') {
          updateSubtitle(text);
          if (text.includes('发言结束') || text.includes('会议结束')) {
            highlightSpeaker(null); // 清除高亮
          }
        }
      }
    }
    
    // 语音播报（优化版本）- 避免频繁播报和结巴
    if (els.ttsEnable && els.ttsEnable.checked && kind !== 'system' && text && role !== '我') {
      // 清理文本：去除角色名称、部门标识等非发言内容
      let cleanText = text;
      
      // 去除角色名称前缀（如"总经理(CEO)："）
      cleanText = cleanText.replace(/^[^：]*：\s*/, '');
      
      // 去除部门名称和系统编号
      cleanText = cleanText.replace(/\([^)]*\)/g, ''); // 去除括号内容
      cleanText = cleanText.replace(/【[^】]*】/g, ''); // 去除方括号内容
      cleanText = cleanText.replace(/\[[^\]]*\]/g, ''); // 去除中括号内容
      
      // 去除多余空格和特殊字符
      cleanText = cleanText.replace(/\s+/g, ' ').trim();
      cleanText = cleanText.replace(/[^\u4e00-\u9fa5a-zA-Z0-9\s，。！？；：""''（）]/g, ''); // 只保留中文、英文、数字和基本标点
      
      // 过滤掉过短或无意义的文本
      if (cleanText && cleanText.length >= 3 && !cleanText.match(/^[。，！？；：\s]+$/)) {
        // 使用缓冲机制，避免频繁播报
        if (!speechBuffer[role]) {
          speechBuffer[role] = '';
        }
        
        speechBuffer[role] += cleanText;
        
        // 清除之前的定时器
        if (speechTimers[role]) {
          clearTimeout(speechTimers[role]);
        }
        
        // 设置新的定时器，延迟播报以收集完整句子
        speechTimers[role] = setTimeout(() => {
          const bufferedText = speechBuffer[role];
          if (bufferedText && bufferedText.length >= 5) {
            try {
              // 停止当前播报
              window.speechSynthesis.cancel();
              
              // 获取角色的音色配置
              const voiceProfile = getVoiceProfile(role);
              
              // 开始新的播报
              const u = new SpeechSynthesisUtterance(bufferedText);
              u.lang = 'zh-CN';
              u.rate = voiceProfile.rate;
              u.pitch = voiceProfile.pitch;
              u.volume = voiceProfile.volume;
              
              // 如果有指定的语音引擎，使用它
              if (voiceProfile.voice) {
                u.voice = voiceProfile.voice;
                
                // 检查是否为远程语音且无网络连接
                if (!voiceProfile.voice.localService && !navigator.onLine) {
                  console.warn(`语音 ${voiceProfile.voice.name} 需要网络连接，当前离线状态`);
                  return;
                }
              }
              
              // 播报完成后清理缓冲
              u.onend = () => {
                speechBuffer[role] = '';
              };
              
              window.speechSynthesis.speak(u);
            } catch (e) {
              console.warn('语音播报失败:', e);
            }
          }
          speechBuffer[role] = '';
        }, 2000); // 2秒延迟，收集完整内容后播报
      }
    }
  }

  // 打字机效果函数
  function typewriterEffect(element, text, interval = 160) {
    let index = 0;
    element.textContent = '';
    
    const timer = setInterval(() => {
      if (index < text.length) {
        element.textContent += text[index];
        index++;
        // 自动滚动
        if (els.rtmTimeline) {
          els.rtmTimeline.scrollTop = els.rtmTimeline.scrollHeight;
        }
      } else {
        clearInterval(timer);
      }
    }, interval);
  }

  // 字幕区域打字机效果
  function typewriterSubtitle(text, role = null, interval = 160) {
    if (!els.subtitleContent) return;
    
    // 检查内容是否超出限制，如果超出则清理旧内容
    const maxLines = 20; // 最大显示行数
    const currentLines = els.subtitleContent.innerHTML.split('<br>').length;
    
    if (currentLines > maxLines) {
      // 保留最后10行内容，删除前面的内容
      const lines = els.subtitleContent.innerHTML.split('<br>');
      const keepLines = lines.slice(-10);
      els.subtitleContent.innerHTML = keepLines.join('<br>');
    }
    
    let index = 0;
    
    // 如果有角色名，先添加角色名和换行
    if (role) {
      // 检查是否需要添加换行符（如果内容区域不为空且不以换行结尾）
      const currentContent = els.subtitleContent.innerHTML;
      if (currentContent && currentContent.trim() !== '' && !currentContent.endsWith('<br>')) {
        els.subtitleContent.innerHTML += '<br>';
      }
      els.subtitleContent.innerHTML += `<strong>${role}:</strong> `;
    }
    
    const timer = setInterval(() => {
      if (index < text.length) {
        const newChar = text[index];
        
        // 直接追加新字符到现有内容
        if (newChar === '\n') {
          els.subtitleContent.innerHTML += '<br>';
        } else {
          els.subtitleContent.innerHTML += newChar;
        }
        
        index++;
        // 自动滚动到底部
        els.subtitleContent.scrollTop = els.subtitleContent.scrollHeight;
      } else {
        clearInterval(timer);
        // 发言结束后添加换行，为下一次发言做准备
        els.subtitleContent.innerHTML += '<br>';
      }
    }, interval);
  }

  async function startRealtimeMeeting() {
    // 显示面板
    els.rtmPanel.style.display = '';
    // 复用上方的输入作为默认参数
    const model = (els.modelSelect.value || '').trim();
    const participants = (els.participants.value || '').split(',').map(s => s.trim()).filter(Boolean);
    const agenda = (els.agenda.value || '').split(',').map(s => s.trim()).filter(Boolean);
    try {
      const r = await fetch('/api/rtm/start', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model, participants, agenda })
      });
      const j = await r.json();
      if (!j.ok) throw new Error(j.error || 'failed');
      currentSid = j.sid;
      els.rtmSid.textContent = currentSid;
      connectStream(currentSid);
      els.btnRtmStart.disabled = true;
      appendLine('系统', '会议已启动', 'system');
    } catch (e) {
      appendLine('系统', '启动失败：' + e.message, 'system');
    }
  }

  function connectStream(sid) {
    if (es) try { es.close(); } catch (e) {}
    es = new EventSource(`/api/rtm/stream?sid=${encodeURIComponent(sid)}`);
    es.addEventListener('start_meeting', ev => {
      const data = JSON.parse(ev.data || '{}');
      appendLine('系统', `开始会议：${(data.roles||[]).join('，')}｜议程：${(data.agenda||[]).join('，')}`, 'system');
      
      // 创建会议桌视图
      if (data.roles && data.roles.length > 0) {
        createMeetingTable(data.roles);
        updateSubtitle('会议开始，等待发言...');
      }
    });
    es.addEventListener('agent_say', ev => {
      const data = JSON.parse(ev.data || '{}');
      const role = data.role || '角色';
      const partial = data.partial || '';
      
      // 在会议桌视图中高亮当前发言人
      if (role && currentViewMode === 'table') {
        highlightSpeaker(role);
      }
      
      // 简化缓冲逻辑：直接显示内容，不进行复杂的句子检测
      if (partial.trim()) {
        appendLine(role, partial);
      }
    });
    es.addEventListener('agent_say_done', ev => {
      const data = JSON.parse(ev.data || '{}');
      const role = data.role || '角色';
      
      appendLine(role, '（发言结束）', 'system');
      
      // 移除高亮效果
      highlightSpeaker(null);
      updateSubtitle('等待下一位发言...');
      
      // 清理该角色的语音缓冲，确保发言结束时立即播报剩余内容
      if (speechTimers[role]) {
        clearTimeout(speechTimers[role]);
        const bufferedText = speechBuffer[role];
        if (bufferedText && bufferedText.length >= 3) {
          try {
            window.speechSynthesis.cancel();
            
            // 获取角色的音色配置
            const voiceProfile = getVoiceProfile(role);
            
            const u = new SpeechSynthesisUtterance(bufferedText);
            u.lang = 'zh-CN';
            u.rate = voiceProfile.rate;
            u.pitch = voiceProfile.pitch;
            u.volume = voiceProfile.volume;
            
            // 如果有指定的语音引擎，使用它
            if (voiceProfile.voice) {
              u.voice = voiceProfile.voice;
              
              // 检查是否为远程语音且无网络连接
              if (!voiceProfile.voice.localService && !navigator.onLine) {
                console.warn(`语音 ${voiceProfile.voice.name} 需要网络连接，当前离线状态`);
                return;
              }
            }
            
            window.speechSynthesis.speak(u);
          } catch (e) {
            console.warn('语音播报失败:', e);
          }
        }
        speechBuffer[role] = '';
        delete speechTimers[role];
      }
    });
    es.addEventListener('user_say', ev => {
      const data = JSON.parse(ev.data || '{}');
      appendLine('我', data.text || '', 'say');
    });
    es.addEventListener('end_meeting', ev => {
      appendLine('系统', '会议结束', 'system');
      els.btnRtmStart.disabled = false;
      
      // 清理会议桌视图
      highlightSpeaker(null);
      updateSubtitle('会议已结束');
      
      try { es.close(); } catch (e) {}
    });
    es.addEventListener('stream_closed', ev => {
      appendLine('系统', '流已关闭', 'system');
      try { es.close(); } catch (e) {}
    });
  }

  async function endRealtimeMeeting() {
    if (!currentSid) return;
    try {
      await fetch('/api/rtm/end', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ sid: currentSid }) });
    } catch (e) {}
  }

  async function sendUserSay() {
    let text = (els.userSay.value || '').trim();
    if (!currentSid) return;
    
    // 如果输入框为空，使用默认内容"我来说两句"
    if (!text) {
      text = '我来说两句';
    }
    
    try {
      await fetch('/api/rtm/say', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ sid: currentSid, content: text }) });
      els.userSay.value = '';
    } catch (e) {}
  }

  // 绑定视图切换按钮事件
  els.btnTableView.addEventListener('click', () => switchView('table'));
  els.btnTimelineView.addEventListener('click', () => switchView('timeline'));

  els.btnRtmStart.addEventListener('click', startRealtimeMeeting);
  els.btnRtmEnd.addEventListener('click', endRealtimeMeeting);
  els.btnUserSay.addEventListener('click', sendUserSay);
  els.userSay.addEventListener('keydown', (ev) => { if (ev.key === 'Enter') sendUserSay(); });

  // init
  healthCheck();
  loadModels();
  loadMeetings();
  loadRoleVoiceMapping(); // 加载角色音色映射
  loadAvailableVoices(); // 加载可用语音

  // 文档共享治理：状态与渲染
  const sharedRecords = [];

  function renderSharedRecords() {
    if (!els.docsShareList) return;
    els.docsShareList.innerHTML = '';
    if (!sharedRecords.length) {
      const empty = document.createElement('div');
      empty.className = 'muted';
      empty.style.padding = '8px';
      empty.textContent = '（尚无共享记录）';
      els.docsShareList.appendChild(empty);
      return;
    }
    sharedRecords.slice().reverse().forEach(rec => {
      const card = document.createElement('div');
      card.className = 'card';
      card.innerHTML = `
        <div class="card-head">
          <div class="title">${rec.title || '未命名文档'}</div>
          <div class="muted">${rec.id || '—'}</div>
        </div>
        <div class="row">路径：${rec.path}</div>
        <div class="row small">角色：<span class="chip">${rec.role}</span> ${rec.revoked ? '<span class="badge danger">已撤销</span>' : '<span class="badge ok">已共享</span>'}</div>
        <div class="row small">时间：${rec.ts ? new Date(rec.ts).toLocaleString() : '—'}</div>
      `;
      const btnWrap = document.createElement('div');
      btnWrap.className = 'actions';
      const btnRevoke = document.createElement('button');
      btnRevoke.className = 'secondary';
      btnRevoke.textContent = '撤销此共享';
      btnRevoke.disabled = !!rec.revoked;
      btnRevoke.addEventListener('click', () => revokeDoc(rec));
      btnWrap.appendChild(btnRevoke);
      card.appendChild(btnWrap);
      els.docsShareList.appendChild(card);
    });
  }

  async function shareDoc() {
    const role = (els.shareRole && els.shareRole.value) || 'meeting_secretary';
    const path = (els.sharePath && els.sharePath.value || '').trim();
    const title = (els.shareTitle && els.shareTitle.value || '').trim();
    if (!path) {
      alert('请填写需要共享的文档服务器路径');
      return;
    }
    try {
      const r = await fetch('/mcp/docs/share', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ role, path, title })
      });
      if (!r.ok) {
        const errText = await r.text();
        appendLogLine('文档共享', `共享失败：${errText || r.statusText}`, 'error');
        alert(`共享失败：${r.status} ${r.statusText}`);
        return;
      }
      const j = await r.json();
      if (j && j.ok && j.share) {
        const meta = j.share;
        const rec = { id: meta.id, path: meta.path, role: meta.role, title: meta.title || title, ts: Date.now(), revoked: false };
        sharedRecords.push(rec);
        renderSharedRecords();
        appendLogLine('文档共享', `已共享：${meta.path}（角色：${meta.role}）`, 'info');
        if (els.docsShareHint) {
          els.docsShareHint.textContent = '共享成功，操作已写入审计日志';
        }
      } else {
        appendLogLine('文档共享', `共享失败：${(j && j.error) || '未知错误'}`, 'error');
        alert(`共享失败：${(j && j.error) || '未知错误'}`);
      }
    } catch (e) {
      appendLogLine('文档共享', `调用失败：${e.message}`, 'error');
      alert(`调用失败：${e.message}`);
    }
  }

  async function revokeDoc(rec) {
    if (!rec || !rec.id || !rec.path) {
      alert('无法撤销：缺少共享记录或标识');
      return;
    }
    try {
      const r = await fetch('/mcp/docs/revoke', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ role: rec.role || 'meeting_secretary', id: rec.id, path: rec.path })
      });
      if (!r.ok) {
        const errText = await r.text();
        appendLogLine('文档共享', `撤销失败：${errText || r.statusText}`, 'error');
        alert(`撤销失败：${r.status} ${r.statusText}`);
        return;
      }
      const j = await r.json();
      if (j && j.ok) {
        rec.revoked = true;
        renderSharedRecords();
        appendLogLine('文档共享', `已撤销：${rec.path}（角色：${rec.role}）`, 'warn');
        if (els.docsShareHint) {
          els.docsShareHint.textContent = '撤销成功，操作已写入审计日志';
        }
      } else {
        appendLogLine('文档共享', `撤销失败：${(j && j.error) || '未知错误'}`, 'error');
        alert(`撤销失败：${(j && j.error) || '未知错误'}`);
      }
    } catch (e) {
      appendLogLine('文档共享', `调用失败：${e.message}`, 'error');
      alert(`调用失败：${e.message}`);
    }
  }

  function revokeLastShared() {
    const last = sharedRecords[sharedRecords.length - 1];
    if (!last) {
      alert('当前没有可撤销的共享记录');
      return;
    }
    revokeDoc(last);
  }

  // 绑定文档共享按钮
  if (els.btnDocsShare) {
    els.btnDocsShare.addEventListener('click', shareDoc);
  }
  if (els.btnDocsRevoke) {
    els.btnDocsRevoke.addEventListener('click', revokeLastShared);
  }
  // 初始渲染
  renderSharedRecords();

  // ========= 投票管理 =========
  const votesStore = {
    list: [], // 按时间顺序
    byId: {}
  };

  function renderVotes() {
    if (!els.votesList) return;
    els.votesList.innerHTML = '';
    if (!votesStore.list.length) {
      const empty = document.createElement('div');
      empty.className = 'muted';
      empty.style.padding = '8px';
      empty.textContent = '（尚无投票）';
      els.votesList.appendChild(empty);
      return;
    }
    votesStore.list.slice().reverse().forEach(rec => {
      const card = document.createElement('div');
      card.className = 'card';
      const counts = rec.counts || {};
      const opts = rec.options || [];
      card.innerHTML = `
        <div class="card-head">
          <div class="title">${rec.title || '未命名投票'}</div>
          <div class="muted">${rec.id || '—'}</div>
        </div>
        <div class="row small">状态：${rec.status === 'closed' ? '<span class="badge warn">已结束</span>' : '<span class="badge ok">进行中</span>'}</div>
        <div class="row">选项：${opts.map(o => `<span class="chip">${o}</span>`).join('')}</div>
        <div class="row">计数：${opts.map(o => `<span class="chip alt">${o}: ${counts[o]||0}</span>`).join('')}</div>
      `;
      const actions = document.createElement('div');
      actions.className = 'actions';
      const sel = document.createElement('select');
      sel.style.marginRight = '8px';
      opts.forEach(o => { const opt = document.createElement('option'); opt.value = o; opt.textContent = o; sel.appendChild(opt); });
      sel.disabled = rec.status === 'closed';
      const btnCast = document.createElement('button');
      btnCast.textContent = '投票';
      btnCast.disabled = rec.status === 'closed';
      btnCast.addEventListener('click', () => castVote(rec.id, sel.value));
      const btnRefresh = document.createElement('button');
      btnRefresh.className = 'secondary';
      btnRefresh.textContent = '刷新状态';
      btnRefresh.addEventListener('click', () => refreshVoteStatus(rec.id));
      const btnClose = document.createElement('button');
      btnClose.className = 'secondary';
      btnClose.textContent = '结束';
      btnClose.disabled = rec.status === 'closed';
      btnClose.addEventListener('click', () => finalizeVote(rec.id));
      actions.appendChild(sel);
      actions.appendChild(btnCast);
      actions.appendChild(btnRefresh);
      actions.appendChild(btnClose);
      card.appendChild(actions);
      els.votesList.appendChild(card);
    });
  }

  async function createVote() {
    const role = (els.votesRole && els.votesRole.value) || 'developer';
    const title = (els.votesTitle && els.votesTitle.value || '').trim();
    const optionsRaw = (els.votesOptions && els.votesOptions.value || '').trim();
    const meetingId = (els.votesMeetingId && els.votesMeetingId.value || '').trim();
    const options = optionsRaw.split(',').map(s => s.trim()).filter(Boolean);
    if (!title || options.length < 2) {
      alert('请填写投票标题，并至少提供两个选项');
      return;
    }
    try {
      const r = await fetch('/mcp/votes/create', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ role, title, options, meeting_id: meetingId })
      });
      if (!r.ok) {
        const errText = await r.text();
        appendLogLine('投票', `创建失败：${errText || r.statusText}`, 'error');
        alert(`创建失败：${r.status} ${r.statusText}`);
        return;
      }
      const j = await r.json();
      if (j && j.ok && j.vote) {
        const rec = j.vote;
        votesStore.byId[rec.id] = rec;
        votesStore.list.push(rec);
        renderVotes();
        appendLogLine('投票', `已创建：${rec.title}（ID：${rec.id}）`, 'info');
        if (els.votesHint) els.votesHint.textContent = '创建成功，操作已写入审计日志';
      } else {
        appendLogLine('投票', `创建失败：${(j && j.error) || '未知错误'}`, 'error');
        alert(`创建失败：${(j && j.error) || '未知错误'}`);
      }
    } catch (e) {
      appendLogLine('投票', `调用失败：${e.message}`, 'error');
      alert(`调用失败：${e.message}`);
    }
  }

  async function castVote(voteId, option) {
    const role = (els.votesRole && els.votesRole.value) || 'developer';
    if (!voteId || !option) return;
    try {
      const r = await fetch('/mcp/votes/cast', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ role, vote_id: voteId, option })
      });
      const j = await r.json();
      if (r.ok && j && j.ok) {
        const rec = j.vote;
        votesStore.byId[rec.id] = rec;
        const idx = votesStore.list.findIndex(x => x.id === rec.id);
        if (idx >= 0) votesStore.list[idx] = rec;
        renderVotes();
        appendLogLine('投票', `已投票：${option}（ID：${rec.id}）`, 'info');
      } else {
        appendLogLine('投票', `投票失败：${(j && j.error) || r.statusText}`, 'error');
        alert(`投票失败：${(j && j.error) || r.statusText}`);
      }
    } catch (e) {
      appendLogLine('投票', `调用失败：${e.message}`, 'error');
      alert(`调用失败：${e.message}`);
    }
  }

  async function refreshVoteStatus(voteId) {
    const role = (els.votesRole && els.votesRole.value) || 'developer';
    if (!voteId) return;
    try {
      const r = await fetch(`/mcp/votes/status?vote_id=${encodeURIComponent(voteId)}&role=${encodeURIComponent(role)}`);
      const j = await r.json();
      if (r.ok && j && j.ok && j.vote) {
        const rec = j.vote;
        votesStore.byId[rec.id] = rec;
        const idx = votesStore.list.findIndex(x => x.id === rec.id);
        if (idx >= 0) votesStore.list[idx] = rec;
        renderVotes();
      } else {
        appendLogLine('投票', `刷新失败：${(j && j.error) || r.statusText}`, 'error');
      }
    } catch (e) {
      appendLogLine('投票', `调用失败：${e.message}`, 'error');
    }
  }

  async function finalizeVote(voteId) {
    const role = (els.votesRole && els.votesRole.value) || 'meeting_secretary';
    if (!voteId) return;
    try {
      const r = await fetch('/mcp/votes/finalize', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ role, vote_id: voteId })
      });
      const j = await r.json();
      if (r.ok && j && j.ok && j.vote) {
        const rec = j.vote;
        votesStore.byId[rec.id] = rec;
        const idx = votesStore.list.findIndex(x => x.id === rec.id);
        if (idx >= 0) votesStore.list[idx] = rec;
        renderVotes();
        appendLogLine('投票', `已结束：${rec.title}（ID：${rec.id}）`, 'warn');
        if (els.votesHint) els.votesHint.textContent = '结束成功，操作已写入审计日志';
      } else {
        appendLogLine('投票', `结束失败：${(j && j.error) || r.statusText}`, 'error');
        alert(`结束失败：${(j && j.error) || r.statusText}`);
      }
    } catch (e) {
      appendLogLine('投票', `调用失败：${e.message}`, 'error');
      alert(`调用失败：${e.message}`);
    }
  }

  // 绑定投票管理按钮
  if (els.btnVoteCreate) {
    els.btnVoteCreate.addEventListener('click', createVote);
  }
  if (els.btnVoteFinalize) {
    els.btnVoteFinalize.addEventListener('click', () => {
      const latest = votesStore.list[votesStore.list.length - 1];
      if (!latest) {
        alert('当前没有可结束的投票');
        return;
      }
      finalizeVote(latest.id);
    });
  }
  // 初始渲染
  renderVotes();

  // ========= 语音管理 =========
  async function streamVoice() {
    const role = (els.voiceRoleCtl && els.voiceRoleCtl.value) || 'tech_representative';
    const engine = (els.voiceEngineCtl && els.voiceEngineCtl.value) || 'responsivevoice';
    const text = (els.voiceTextCtl && els.voiceTextCtl.value || '').trim();
    if (!text) {
      alert('请输入需要播报的文本');
      return;
    }
    try {
      const r = await fetch('/mcp/voice/stream', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ role, text, engine })
      });
      const j = await r.json();
      if (r.ok && j && j.ok) {
        appendLogLine('语音', `已推送：${(text.length>32?text.slice(0,32)+'…':text)}（角色：${role}，引擎：${engine}）`, 'info');
        if (els.voiceHint) els.voiceHint.textContent = '推送成功，事件已广播并写入审计日志';
        // 可选：本地播报一遍
        try { speakText(text, role); } catch (_) {}
      } else {
        appendLogLine('语音', `推送失败：${(j && j.error) || r.statusText}`, 'error');
        alert(`推送失败：${(j && j.error) || r.statusText}`);
      }
    } catch (e) {
      appendLogLine('语音', `调用失败：${e.message}`, 'error');
      alert(`调用失败：${e.message}`);
    }
  }

  if (els.btnVoiceStream) {
    els.btnVoiceStream.addEventListener('click', streamVoice);
  }

  // ========= 服务器日志 WebSocket 连接 =========
  let socket = null;
  let logsVisible = false;

  const logElements = {
    btnToggleLogs: document.getElementById('btn-toggle-logs'),
    btnClearLogs: document.getElementById('btn-clear-logs'),
    serverLogs: document.getElementById('server-logs'),
    logContent: document.getElementById('log-content')
  };

  function initWebSocket() {
    try {
      socket = io();
      
      socket.on('connect', () => {
        console.log('WebSocket connected');
        appendLogLine('系统', 'WebSocket 连接已建立', 'info');
        // 请求开始接收日志
        socket.emit('request_logs');
      });

      socket.on('disconnect', () => {
        console.log('WebSocket disconnected');
        appendLogLine('系统', 'WebSocket 连接已断开', 'warning');
      });

      socket.on('log_message', (data) => {
        appendLogLine('服务器', data.message, data.level || 'info');
      });

      // 文档共享事件广播（后端通过 socketio.emit("docs_shared"/"docs_revoked")）
      socket.on('docs_shared', (payload) => {
        try {
          const meta = payload && payload.share;
          if (meta && meta.path) {
            const rec = { id: meta.id, path: meta.path, role: meta.role, title: meta.title, ts: Date.now(), revoked: false };
            sharedRecords.push(rec);
            renderSharedRecords();
            appendLogLine('文档共享', `事件：已共享 ${meta.path}（角色：${meta.role}）`, 'info');
          }
        } catch (e) {
          console.warn('处理 docs_shared 事件失败:', e);
        }
      });
      socket.on('docs_revoked', (payload) => {
        try {
          const meta = payload && payload.share;
          if (meta && meta.id) {
            const rec = sharedRecords.find(r => r.id === meta.id) || sharedRecords.find(r => r.path === meta.path);
            if (rec) {
              rec.revoked = true;
              renderSharedRecords();
            }
            appendLogLine('文档共享', `事件：已撤销 ${meta.path}（角色：${meta.role}）`, 'warn');
          }
        } catch (e) {
          console.warn('处理 docs_revoked 事件失败:', e);
        }
      });

      // 投票事件广播
      socket.on('vote_created', (payload) => {
        try {
          const rec = payload && payload.vote;
          if (rec && rec.id) {
            votesStore.byId[rec.id] = rec;
            // 如果不存在则添加
            if (!votesStore.list.find(x => x.id === rec.id)) {
              votesStore.list.push(rec);
            }
            renderVotes();
            appendLogLine('投票', `事件：创建 ${rec.title}（ID：${rec.id}）`, 'info');
          }
        } catch (e) { console.warn('处理 vote_created 事件失败:', e); }
      });
      socket.on('vote_cast', (payload) => {
        try {
          const vid = payload && payload.vote_id;
          const counts = payload && payload.counts;
          if (vid && votesStore.byId[vid]) {
            votesStore.byId[vid].counts = counts || votesStore.byId[vid].counts;
            const idx = votesStore.list.findIndex(x => x.id === vid);
            if (idx >= 0) {
              votesStore.list[idx].counts = counts || votesStore.list[idx].counts;
            }
            renderVotes();
            appendLogLine('投票', `事件：投票更新（ID：${vid}）`, 'info');
          }
        } catch (e) { console.warn('处理 vote_cast 事件失败:', e); }
      });
      socket.on('vote_finalized', (payload) => {
        try {
          const rec = payload && payload.vote;
          if (rec && rec.id) {
            votesStore.byId[rec.id] = rec;
            const idx = votesStore.list.findIndex(x => x.id === rec.id);
            if (idx >= 0) votesStore.list[idx] = rec;
            renderVotes();
            appendLogLine('投票', `事件：结束 ${rec.title}（ID：${rec.id}）`, 'warn');
          }
        } catch (e) { console.warn('处理 vote_finalized 事件失败:', e); }
      });

      // 语音事件广播
      socket.on('voice_stream', (payload) => {
        try {
          const meta = payload && payload.meta;
          if (meta && meta.text && meta.role) {
            appendLogLine('语音', `事件：${(meta.text.length>32?meta.text.slice(0,32)+'…':meta.text)}（角色：${meta.role}，引擎：${meta.engine}）`, 'info');
            // 如果用户开启了语音播报，则本地播放
            if (els.ttsEnable && els.ttsEnable.checked) {
              try { speakText(meta.text, meta.role); } catch (_) {}
            }
          }
        } catch (e) { console.warn('处理 voice_stream 事件失败:', e); }
      });

      socket.on('connect_error', (error) => {
        console.error('WebSocket connection error:', error);
        appendLogLine('系统', `WebSocket 连接错误: ${error.message}`, 'error');
      });
    } catch (error) {
      console.error('Failed to initialize WebSocket:', error);
      appendLogLine('系统', `WebSocket 初始化失败: ${error.message}`, 'error');
    }
  }

  function appendLogLine(source, message, level = 'info') {
    if (!logElements.logContent) return;
    
    const timestamp = new Date().toLocaleTimeString();
    const logLine = document.createElement('div');
    logLine.className = `log-line ${level}`;
    logLine.textContent = `[${timestamp}] [${source}] ${message}`;
    
    logElements.logContent.appendChild(logLine);
    
    // 自动滚动到底部
    logElements.logContent.scrollTop = logElements.logContent.scrollHeight;
    
    // 限制日志行数，避免内存占用过多
    const maxLines = 1000;
    const lines = logElements.logContent.children;
    if (lines.length > maxLines) {
      for (let i = 0; i < lines.length - maxLines; i++) {
        logElements.logContent.removeChild(lines[0]);
      }
    }
  }

  function toggleLogs() {
    logsVisible = !logsVisible;
    logElements.serverLogs.style.display = logsVisible ? 'block' : 'none';
    logElements.btnToggleLogs.textContent = logsVisible ? '隐藏日志' : '显示日志';
    
    if (logsVisible && !socket) {
      initWebSocket();
    }
  }

  function clearLogs() {
    if (logElements.logContent) {
      logElements.logContent.innerHTML = '';
      appendLogLine('系统', '日志已清空', 'info');
    }
  }

  // 绑定日志相关事件
  if (logElements.btnToggleLogs) {
    logElements.btnToggleLogs.addEventListener('click', toggleLogs);
  }
  if (logElements.btnClearLogs) {
    logElements.btnClearLogs.addEventListener('click', clearLogs);
  }

  // ========== 音色设置功能 ==========
  
  // 音色设置界面相关元素
  const voiceElements = {
    btnVoiceSettings: document.getElementById('btn-voice-settings'),
    voiceModal: document.getElementById('voice-settings-modal'),
    btnCloseModal: document.getElementById('btn-close-voice-modal'),
    voiceProfilesGrid: document.querySelector('.voice-profiles-grid'),
    roleAssignments: document.getElementById('role-voice-assignments'),
    btnResetVoices: document.getElementById('btn-reset-voices'),
    btnSaveSettings: document.getElementById('btn-save-voice-settings')
  };

  let selectedVoiceForRole = null;
  let currentAssigningRole = null;

  // 显示音色设置模态框
  function showVoiceSettings() {
    if (voiceElements.voiceModal) {
      voiceElements.voiceModal.style.display = 'flex';
      renderVoiceProfiles();
      renderRoleAssignments();
    }
  }

  // 隐藏音色设置模态框
  function hideVoiceSettings() {
    if (voiceElements.voiceModal) {
      voiceElements.voiceModal.style.display = 'none';
      selectedVoiceForRole = null;
      currentAssigningRole = null;
    }
  }

  // 渲染音色配置卡片
  function renderVoiceProfiles() {
    if (!voiceElements.voiceProfilesGrid) return;
    
    voiceElements.voiceProfilesGrid.innerHTML = '';
    
    window.voiceProfiles.forEach((profile, index) => {
      const card = document.createElement('div');
      card.className = 'voice-profile-card';
      card.dataset.voiceIndex = index;
      
      card.innerHTML = `
        <div class="voice-profile-name">${profile.name}</div>
        <div class="voice-profile-details">
          性别: ${profile.gender}<br>
          语速: ${profile.rate}<br>
          音调: ${profile.pitch}<br>
          音量: ${profile.volume}
        </div>
        <div class="voice-profile-preview">
          <button class="btn-preview" onclick="previewVoice(${index})">试听</button>
        </div>
      `;
      
      card.addEventListener('click', () => selectVoiceProfile(index));
      voiceElements.voiceProfilesGrid.appendChild(card);
    });
  }

  // 渲染角色音色分配
  function renderRoleAssignments() {
    if (!voiceElements.roleAssignments) return;
    
    voiceElements.roleAssignments.innerHTML = '';
    
    // 获取当前所有已知角色
    const allRoles = Object.keys(roleVoiceMapping);
    
    if (allRoles.length === 0) {
      voiceElements.roleAssignments.innerHTML = '<div style="color: var(--muted); text-align: center; padding: 20px;">暂无角色，请先开始会议</div>';
      return;
    }
    
    allRoles.forEach(role => {
      const assignedVoiceIndex = roleVoiceMapping[role];
      const assignedVoice = window.voiceProfiles[assignedVoiceIndex];
      
      const item = document.createElement('div');
      item.className = 'role-assignment-item';
      
      item.innerHTML = `
        <div class="role-name">${role}</div>
        <div style="display: flex; align-items: center; gap: 8px;">
          <select class="voice-selector" data-role="${role}">
            <option value="">选择音色</option>
            ${window.voiceProfiles.map((profile, index) => 
              `<option value="${index}" ${assignedVoiceIndex === index ? 'selected' : ''}>${profile.name}</option>`
            ).join('')}
          </select>
          <button class="btn-preview" onclick="previewRoleVoice('${role}')">试听</button>
        </div>
      `;
      
      voiceElements.roleAssignments.appendChild(item);
    });
    
    // 绑定选择器事件
    voiceElements.roleAssignments.querySelectorAll('.voice-selector').forEach(selector => {
      selector.addEventListener('change', (e) => {
        const role = e.target.dataset.role;
        const voiceIndex = parseInt(e.target.value);
        if (!isNaN(voiceIndex)) {
          assignVoiceToRole(role, voiceIndex);
        }
      });
    });
  }

  // 选择音色配置
  function selectVoiceProfile(index) {
    // 清除之前的选中状态
    voiceElements.voiceProfilesGrid.querySelectorAll('.voice-profile-card').forEach(card => {
      card.classList.remove('selected');
    });
    
    // 选中当前卡片
    const selectedCard = voiceElements.voiceProfilesGrid.querySelector(`[data-voice-index="${index}"]`);
    if (selectedCard) {
      selectedCard.classList.add('selected');
      selectedVoiceForRole = index;
    }
  }

  // 预览音色
  window.previewVoice = function(voiceIndex) {
    const profile = window.voiceProfiles[voiceIndex];
    if (!profile) return;
    
    const testText = `你好，我是${profile.name}，这是我的声音效果。`;
    
    // 停止当前播放
    if (window.speechSynthesis.speaking) {
      window.speechSynthesis.cancel();
    }
    
    const utterance = new SpeechSynthesisUtterance(testText);
    utterance.lang = 'zh-CN';
    utterance.rate = profile.rate;
    utterance.pitch = profile.pitch;
    utterance.volume = profile.volume;
    
    // 如果有指定的语音引擎，使用它
    if (profile.voice) {
      utterance.voice = profile.voice;
      
      // 检查是否为远程语音且无网络连接
      if (!profile.voice.localService && !navigator.onLine) {
        alert(`语音 ${profile.voice.name} 需要网络连接，当前离线状态，无法预览`);
        return;
      }
    }
    
    window.speechSynthesis.speak(utterance);
  };

  // 预览角色音色
  window.previewRoleVoice = function(role) {
    const voiceIndex = roleVoiceMapping[role];
    if (voiceIndex !== undefined) {
      previewVoice(voiceIndex);
    }
  };

  // 重置音色分配
  function resetVoiceAssignments() {
    if (confirm('确定要重置所有角色的音色分配吗？')) {
      roleVoiceMapping = {};
      saveRoleVoiceMapping();
      renderRoleAssignments();
    }
  }

  // 保存音色设置
  function saveVoiceSettings() {
    saveRoleVoiceMapping();
    hideVoiceSettings();
    
    // 显示保存成功提示
    const notification = document.createElement('div');
    notification.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      background: var(--ok);
      color: white;
      padding: 12px 20px;
      border-radius: 8px;
      z-index: 1001;
      font-weight: 500;
    `;
    notification.textContent = '音色设置已保存';
    document.body.appendChild(notification);
    
    setTimeout(() => {
      document.body.removeChild(notification);
    }, 2000);
  }

  // 绑定音色设置相关事件
  if (voiceElements.btnVoiceSettings) {
    voiceElements.btnVoiceSettings.addEventListener('click', showVoiceSettings);
  }
  if (voiceElements.btnCloseModal) {
    voiceElements.btnCloseModal.addEventListener('click', hideVoiceSettings);
  }
  if (voiceElements.btnResetVoices) {
    voiceElements.btnResetVoices.addEventListener('click', resetVoiceAssignments);
  }
  if (voiceElements.btnSaveSettings) {
    voiceElements.btnSaveSettings.addEventListener('click', saveVoiceSettings);
  }

  // 点击模态框背景关闭
  if (voiceElements.voiceModal) {
    voiceElements.voiceModal.addEventListener('click', (e) => {
      if (e.target === voiceElements.voiceModal) {
        hideVoiceSettings();
      }
    });
  }

})();

// 统一的语音播放函数
function speakText(text, role) {
  if (!text || !role) return;

  const voiceProfile = getVoiceProfile(role);
  if (!voiceProfile) return;

  // 停止当前播放
  if (window.speechSynthesis.speaking) {
    window.speechSynthesis.cancel();
  }
  if (typeof responsiveVoice !== 'undefined' && responsiveVoice.isPlaying()) {
    responsiveVoice.cancel();
  }

  console.log(`使用语音引擎: ${voiceProfile.engine}, 语音: ${voiceProfile.name}`);

  switch (voiceProfile.engine) {
    case VoiceEngineType.RESPONSIVE_VOICE:
      speakWithResponsiveVoice(text, voiceProfile);
      break;
    case VoiceEngineType.NATIVE:
      speakWithNativeAPI(text, voiceProfile);
      break;
    case VoiceEngineType.AUDIO_FILE:
      // 预留音频文件播放功能
      console.log('音频文件播放功能待实现');
      break;
    default:
      speakWithNativeAPI(text, voiceProfile);
  }
}

function speakWithResponsiveVoice(text, voiceProfile) {
  if (typeof responsiveVoice === 'undefined') {
    console.warn('ResponsiveVoice未加载，回退到原生语音API');
    // 回退到原生API时，需要找到对应的原生语音配置
    const fallbackProfile = findNativeFallbackVoice(voiceProfile);
    speakWithNativeAPI(text, fallbackProfile);
    return;
  }

  // 检查网络连接
  if (!navigator.onLine) {
    console.warn('ResponsiveVoice需要网络连接，当前离线状态');
    alert('ResponsiveVoice语音需要网络连接，当前处于离线状态');
    return;
  }

  const options = {
    rate: voiceProfile.rate || 1.0,
    pitch: voiceProfile.pitch || 1.0,
    volume: voiceProfile.volume || 0.8,
    onstart: () => {
      console.log(`ResponsiveVoice开始播放: ${voiceProfile.voiceId}`);
    },
    onend: () => {
      console.log(`ResponsiveVoice播放完成: ${voiceProfile.voiceId}`);
    },
    onerror: (error) => {
      console.error(`ResponsiveVoice播放错误: ${voiceProfile.voiceId}`, error);
      // 出错时回退到原生API
      const fallbackProfile = findNativeFallbackVoice(voiceProfile);
      speakWithNativeAPI(text, fallbackProfile);
    }
  };

  responsiveVoice.speak(text, voiceProfile.voiceId, options);
}

// 为ResponsiveVoice配置找到对应的原生语音回退
function findNativeFallbackVoice(responsiveVoiceProfile) {
  const voices = speechSynthesis.getVoices();
  const chineseVoices = voices.filter(v => v.lang.includes('zh'));
  
  // 根据性别和语音类型选择合适的原生语音
  let selectedVoice = null;
  
  if (responsiveVoiceProfile.gender === 'male') {
    // 优先选择男声（Kangkang）
    selectedVoice = chineseVoices.find(v => v.name.includes('Kangkang')) || 
                   chineseVoices.find(v => v.name.toLowerCase().includes('male')) ||
                   chineseVoices[0];
  } else {
    // 女声的选择逻辑
    if (responsiveVoiceProfile.voiceId && responsiveVoiceProfile.voiceId.includes('Taiwan')) {
      // 台湾女声优先选择Yaoyao
      selectedVoice = chineseVoices.find(v => v.name.includes('Yaoyao')) || chineseVoices[0];
    } else {
      // 其他女声选择Huihui
      selectedVoice = chineseVoices.find(v => v.name.includes('Huihui')) || chineseVoices[0];
    }
  }
  
  // 创建回退配置
  const fallbackProfile = {
    name: selectedVoice ? selectedVoice.name : responsiveVoiceProfile.name,
    engine: VoiceEngineType.NATIVE,
    voice: selectedVoice,
    rate: responsiveVoiceProfile.rate || 1.0,
    pitch: responsiveVoiceProfile.pitch || 1.0,
    volume: responsiveVoiceProfile.volume || 0.8,
    gender: responsiveVoiceProfile.gender
  };
  
  console.log(`使用语音: ${selectedVoice ? selectedVoice.name : '默认语音'}`);
  return fallbackProfile;
}

function speakWithNativeAPI(text, voiceProfile) {
  const u = new SpeechSynthesisUtterance(text);
  
  u.rate = voiceProfile.rate || 1.0;
  u.pitch = voiceProfile.pitch || 1.0;
  u.volume = voiceProfile.volume || 0.7;

  // 设置语音
  if (voiceProfile.voice) {
    u.voice = voiceProfile.voice;
    
    // 检查远程语音的网络连接
    if (!voiceProfile.voice.localService && !navigator.onLine) {
      console.warn(`语音 ${voiceProfile.voice.name} 需要网络连接，当前离线状态`);
      alert(`语音 ${voiceProfile.voice.name} 需要网络连接，当前处于离线状态，无法播放`);
      return;
    }
  }

  u.onstart = () => {
    console.log(`原生API开始播放: ${voiceProfile.name}`);
  };

  u.onend = () => {
    console.log(`原生API播放完成: ${voiceProfile.name}`);
  };

  u.onerror = (event) => {
    console.error(`原生API播放错误: ${voiceProfile.name}`, event);
  };

  window.speechSynthesis.speak(u);
}

// 更新预览语音函数
window.previewVoice = function(voiceIndex) {
  const profile = window.voiceProfiles[voiceIndex];
  if (!profile) return;

  const testText = `你好，我是${profile.name}。这是语音测试，现在时间是${new Date().toLocaleTimeString()}。`;

  // 停止当前播放
  if (window.speechSynthesis.speaking) {
    window.speechSynthesis.cancel();
  }
  if (typeof responsiveVoice !== 'undefined' && responsiveVoice.isPlaying()) {
    responsiveVoice.cancel();
  }

  // 根据引擎类型播放
  switch (profile.engine) {
    case VoiceEngineType.RESPONSIVE_VOICE:
      // 检查 ResponsiveVoice 是否完全可用（对象存在、有 speak 方法、已初始化、有语音列表且网络在线）
      const isResponsiveVoiceReady = typeof responsiveVoice !== 'undefined' && 
                                   typeof responsiveVoice.speak === 'function' && 
                                   navigator.onLine &&
                                   (responsiveVoice.ready === true || responsiveVoice.initialized === true || 
                                    (responsiveVoice.voicelist && responsiveVoice.voicelist.length > 0));
      
      if (isResponsiveVoiceReady) {
        responsiveVoice.speak(testText, profile.voiceId, {
          rate: profile.rate,
          pitch: profile.pitch,
          volume: profile.volume
        });
      } else {
        // ResponsiveVoice未完全可用，使用修复后的回退逻辑
        if (!navigator.onLine) {
          console.warn('ResponsiveVoice需要网络连接，当前离线状态，回退到原生语音API');
        } else if (typeof responsiveVoice === 'undefined') {
          console.warn('ResponsiveVoice库未加载，回退到原生语音API');
        } else {
          console.warn('ResponsiveVoice未完全初始化，回退到原生语音API');
        }
        const fallbackProfile = findNativeFallbackVoice(profile);
        if (fallbackProfile) {
          speakWithNativeAPI(testText, fallbackProfile);
        } else {
          alert('ResponsiveVoice库未完全加载，且无可用的原生语音回退选项');
        }
      }
      break;
    case VoiceEngineType.NATIVE:
      const utterance = new SpeechSynthesisUtterance(testText);
      utterance.rate = profile.rate;
      utterance.pitch = profile.pitch;
      utterance.volume = profile.volume;

      if (profile.voice) {
        utterance.voice = profile.voice;
        
        if (!profile.voice.localService && !navigator.onLine) {
          alert(`语音 ${profile.voice.name} 需要网络连接，当前离线状态，无法预览`);
          return;
        }
      }

      window.speechSynthesis.speak(utterance);
      break;
    default:
      console.warn('未知的语音引擎类型:', profile.engine);
  }
};

// 保存角色音色映射到localStorage
function saveRoleVoiceMapping() {
  try {
    localStorage.setItem('roleVoiceMapping', JSON.stringify(roleVoiceMapping));
    console.log('角色音色映射已保存:', roleVoiceMapping);
  } catch (e) {
    console.warn('保存角色音色映射失败:', e);
  }
}
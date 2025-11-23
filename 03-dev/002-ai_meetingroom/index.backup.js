const express = require('express');
const http = require('http');
const socketIo = require('socket.io');
const path = require('path');
const fs = require('fs');
const multer = require('multer');
const bodyParser = require('body-parser');

const app = express();
const server = http.createServer(app);
const io = socketIo(server);

// 配置视图引擎
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));

// 静态文件目录
app.use(express.static(path.join(__dirname, 'public')));
app.use('/node_modules', express.static(path.join(__dirname, 'node_modules')));
app.use(express.json());

// Agent配置
const agents = [
    {
        id: 'frontend-dev',
        name: '前端开发工程师',
        role: 'frontend',
        avatar: '👨‍💻',
        color: '#4285F4',
        voice: 'male-clear',
        status: 'online',
        expertise: ['React', 'TypeScript', 'CSS', 'JavaScript']
    },
    {
        id: 'backend-dev',
        name: '后端开发工程师',
        role: 'backend',
        avatar: '👩‍💻',
        color: '#EA4335',
        voice: 'female-professional',
        status: 'online',
        expertise: ['FastAPI', 'Python', 'PostgreSQL', 'Redis']
    },
    {
        id: 'architect',
        name: '系统架构师',
        role: 'architect',
        avatar: '🏗️',
        color: '#FBBC05',
        voice: 'male-deep',
        status: 'online',
        expertise: ['微服务', '云原生', 'Docker', 'Kubernetes']
    },
    {
        id: 'devops',
        name: 'DevOps工程师',
        role: 'devops',
        avatar: '🔧',
        color: '#34A853',
        voice: 'male-technical',
        status: 'online',
        expertise: ['CI/CD', 'Docker', 'Jenkins', '监控']
    },
    {
        id: 'pm',
        name: '项目经理',
        role: 'pm',
        avatar: '👨‍💼',
        color: '#9C27B0',
        voice: 'female-managerial',
        status: 'online',
        expertise: ['项目管理', '敏捷开发', '团队协作']
    },
    {
        id: 'qa',
        name: '测试工程师',
        role: 'qa',
        avatar: '🧪',
        color: '#00ACC1',
        voice: 'male-detailed',
        status: 'online',
        expertise: ['自动化测试', '性能测试', '安全测试']
    }
];

// 预设演示文稿数据
const presentationsData = require('./presentations');

// 会议状态
let meetingState = {
    isActive: false,
    currentSpeaker: null,
    agenda: [],
    whiteboardContent: '',
    presentations: [],
    chatHistory: [],
    meetingMinutes: []
};

// 演示文稿上传配置（保存到 public/presentations）
const presentationsDir = path.join(__dirname, 'public', 'presentations');
const storage = multer.diskStorage({
    destination: (req, file, cb) => {
        cb(null, presentationsDir);
    },
    filename: (req, file, cb) => {
        const ext = path.extname(file.originalname);
        const base = path.basename(file.originalname, ext);
        const safeBase = base.replace(/[^a-zA-Z0-9_\-\u4e00-\u9fa5]/g, '_');
        cb(null, `${Date.now()}_${safeBase}${ext}`);
    }
});
const upload = multer({ storage });

// 路由
app.get('/', (req, res) => {
    res.render('index', { 
        agents,
        meetingState,
        title: '测试会议'
    });
});

// 兼容处理：部分浏览器会请求 /favicon.ico，这里返回 SVG 图标
app.get('/favicon.ico', (req, res) => {
    const iconPath = path.join(__dirname, 'public', 'images', 'favicon.svg');
    if (fs.existsSync(iconPath)) {
        res.type('image/svg+xml');
        res.sendFile(iconPath);
    } else {
        res.status(204).end(); // 无内容，避免 404 噪音
    }
});

app.get('/api/agents', (req, res) => {
    res.json(agents);
});

app.get('/api/meeting', (req, res) => {
    res.json(meetingState);
});

// 服务器端保存会议纪要到指定相对目录（默认：minutes）
app.post('/api/save-minutes', (req, res) => {
    try {
        const content = (req.body && req.body.content) ? String(req.body.content) : '';
        const defaultMinutesPath = process.env.MEETING_MINUTES_PATH || 'S:\\3AI\\docs\\81-技术会议';
        const targetDir = (req.body && req.body.path) ? path.resolve(String(req.body.path).trim()) : path.resolve(defaultMinutesPath);

        if (!content) {
            return res.status(400).json({ error: '缺少会议纪要内容' });
        }

        // 安全性提示：路径已配置为可写到项目外部，请确保环境变量和API调用的安全。
        // 创建目标目录
        fs.mkdirSync(targetDir, { recursive: true });

        // 生成文件名：会议记录_YYYY-MM-DD_HH-MM-SS.md
        const ts = new Date().toISOString().replace(/[:.]/g, '-');
        const filename = `会议记录_${ts}.md`;
        const fullPath = path.join(targetDir, filename);
        fs.writeFileSync(fullPath, content, 'utf8');
        return res.json({ success: true, savedPath: path.relative(__dirname, fullPath) });
    } catch (err) {
        console.error('保存会议纪要失败:', err);
        return res.status(500).json({ error: '服务器内部错误' });
    }
});

// 调试：注入一条消息，验证前端渲染与语音链路
app.post('/api/debug/inject-message', express.json(), (req, res) => {
    try {
        const agentId = req.body?.agentId || (agents[0] && agents[0].id) || 'pm';
        const content = req.body?.content || '【调试注入】这是一条用于验证链路的消息';
        const playVoice = req.body?.playVoice !== false; // 默认播放语音

        const message = {
            id: Date.now().toString(),
            agentId,
            content,
            timestamp: new Date(),
            type: 'message'
        };

        meetingState.chatHistory.push(message);
        io.to('meeting').emit('newMessage', message);

        if (playVoice) {
            setTimeout(() => {
                io.to('meeting').emit('playVoice', { agentId, text: content });
            }, 100);
        }

        return res.json({ success: true, message });
    } catch (err) {
        console.error('调试消息注入失败:', err);
        return res.status(500).json({ error: '服务器内部错误' });
    }
});

// 获取演示文稿列表
app.get('/api/presentations', (req, res) => {
    res.json(Array.isArray(meetingState.presentations) ? meetingState.presentations : []);
});

// 获取单个演示文稿的完整内容
app.get('/api/presentations/:id', (req, res) => {
    try {
        const presentationId = req.params.id;
        const presentation = (Array.isArray(meetingState.presentations) ? meetingState.presentations : []).find(p => p.id === presentationId);

        if (presentation) {
            res.json(presentation);
        } else {
            res.status(404).json({ error: '未找到指定的演示文稿' });
        }
    } catch (err) {
        console.error(`获取演示文稿 ${req.params.id} 失败:`, err);
        res.status(500).json({ error: '服务器内部错误' });
    }
});

// 上传演示文稿（multipart/form-data: file, title, agentId）
app.post('/api/presentations/upload', upload.single('file'), (req, res) => {
    try {
        if (!req.file) {
            return res.status(400).json({ error: '未选择文件' });
        }
        const title = req.body.title || req.file.originalname;
        const agentId = req.body.agentId || null;
        const fileUrl = `/presentations/${req.file.filename}`;
        const presentation = {
            id: Date.now().toString(),
            title,
            type: 'file',
            url: fileUrl,
            agentId,
            timestamp: new Date()
        };
        if (!Array.isArray(meetingState.presentations)) {
            meetingState.presentations = [];
        }
        meetingState.presentations.push(presentation);
        // 广播到会议房间
        io.to('meeting').emit('presentationUploaded', presentation);
        return res.json({ success: true, presentation });
    } catch (err) {
        console.error('上传演示文稿失败:', err);
        return res.status(500).json({ error: '服务器内部错误' });
    }
});

// WebSocket连接
io.on('connection', (socket) => {
    try {
        console.log('新用户连接:', socket.id);

        // 发送初始状态 (只发送元数据)
        const presentationsMetadata = (Array.isArray(meetingState.presentations) ? meetingState.presentations : []).map(p => ({
            id: p.id,
            title: p.title,
            type: p.type, // 保留类型，前端可能需要
            url: p.url,   // 如果是文件类型，保留URL
            agentId: p.agentId
        }));
        socket.emit('initialState', { agents, meetingState: { ...meetingState, presentations: presentationsMetadata } });

        // 加入会议
        socket.on('joinMeeting', (userId) => {
            try {
                socket.join('meeting');
                console.log('用户加入会议:', userId);
                io.to('meeting').emit('userJoined', { userId, timestamp: new Date() });
            } catch (err) {
                console.error(`Error in "joinMeeting" event for socket ${socket.id}:`, err);
            }
        });

        // 发送消息
        socket.on('sendMessage', (data) => {
            try {
                const message = {
                    id: Date.now().toString(),
                    agentId: data.agentId,
                    content: data.content,
                    timestamp: new Date(),
                    type: 'message'
                };

                meetingState.chatHistory.push(message);
                io.to('meeting').emit('newMessage', message);

                // 触发Agent语音播放
                if (data.playVoice) {
                    setTimeout(() => {
                        io.to('meeting').emit('playVoice', {
                            agentId: data.agentId,
                            text: data.content
                        });
                    }, 100);
                }
            } catch (err) {
                console.error(`Error in "sendMessage" event for socket ${socket.id}:`, err);
            }
        });

        // 更新白板内容
        socket.on('updateWhiteboard', (content) => {
            try {
                meetingState.whiteboardContent = content;
                io.to('meeting').emit('whiteboardUpdated', content);
            } catch (err) {
                console.error(`Error in "updateWhiteboard" event for socket ${socket.id}:`, err);
            }
        });

        // 开始会议
        socket.on('startMeeting', (agenda) => {
            try {
                meetingState.isActive = true;
                meetingState.agenda = agenda;
                meetingState.currentSpeaker = agents[0].id; // 默认第一个Agent开始
                io.to('meeting').emit('meetingStarted', meetingState);
            } catch (err) {
                console.error(`Error in "startMeeting" event for socket ${socket.id}:`, err);
            }
        });

        // 结束会议
        socket.on('endMeeting', () => {
            try {
                meetingState.isActive = false;
                meetingState.currentSpeaker = null;
                io.to('meeting').emit('meetingEnded');
            } catch (err) {
                console.error(`Error in "endMeeting" event for socket ${socket.id}:`, err);
            }
        });

        // 切换发言人
        socket.on('changeSpeaker', (agentId) => {
            try {
                meetingState.currentSpeaker = agentId;
                io.to('meeting').emit('speakerChanged', agentId);
            } catch (err) {
                console.error(`Error in "changeSpeaker" event for socket ${socket.id}:`, err);
            }
        });

        // 上传演示文稿
        socket.on('uploadPresentation', (data) => {
            try {
                const presentation = {
                    id: Date.now().toString(),
                    title: data.title,
                    content: data.content,
                    agentId: data.agentId,
                    timestamp: new Date()
                };
                meetingState.presentations.push(presentation);
                io.to('meeting').emit('presentationUploaded', presentation);
            } catch (err) {
                console.error(`Error in "uploadPresentation" event for socket ${socket.id}:`, err);
            }
        });

        // 断开连接
        socket.on('disconnect', () => {
            try {
                console.log('用户断开连接:', socket.id);
            } catch (err) {
                console.error(`Error in "disconnect" event for socket ${socket.id}:`, err);
            }
        });
    } catch (err) {
        console.error(`Unhandled error in socket connection for ${socket.id}:`, err);
    }
});

// 创建必要的目录

// LLM 代理接口（最小改造：默认使用本地 Ollama）
const OLLAMA_BASE_URL = process.env.OLLAMA_BASE_URL || 'http://localhost:11434';
const LLM_MODEL = process.env.LLM_MODEL || 'llama3';

app.post('/api/llm/complete', async (req, res) => {
    try {
        const {
            agentId = agents[0]?.id || 'pm',
            prompt = '你是会议中的专业角色，请使用简洁、专业的中文回答，避免冗长与重复，并可给出可执行建议。',
            messages = [],
            maxTokens = 512,
            temperature = 0.7
        } = req.body || {};

        const chatMessages = [];
        chatMessages.push({ role: 'system', content: prompt });
        if (Array.isArray(messages)) {
            messages.slice(-10).forEach(m => {
                const role = m.role && ['system', 'user', 'assistant'].includes(m.role)
                    ? m.role
                    : (m.agentId ? 'assistant' : 'user');
                chatMessages.push({ role, content: String(m.content || '') });
            });
        }

        const resp = await fetch(`${OLLAMA_BASE_URL}/api/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                model: LLM_MODEL,
                messages: chatMessages,
                stream: false,
                options: { temperature, num_predict: maxTokens }
            })
        });

        if (!resp.ok) {
            const text = await resp.text();
            return res.status(500).json({ error: 'LLM接口调用失败', detail: text });
        }

        const data = await resp.json();
        const content = (data && data.message && data.message.content) || (data && data.response) || '';
        if (!content) {
            return res.status(500).json({ error: 'LLM未返回内容' });
        }

        return res.json({ success: true, content, agentId });
    } catch (err) {
        console.error('LLM 代理接口错误:', err);
        return res.status(500).json({ error: '服务器内部错误' });
    }
});

// 创建必要的目录
const createDirectories = () => {
    const dirs = [
        path.join(__dirname, 'views'),
        path.join(__dirname, 'public'),
        path.join(__dirname, 'public/css'),
        path.join(__dirname, 'public/js'),
        path.join(__dirname, 'public/audio'),
        path.join(__dirname, 'public/images'),
        path.join(__dirname, 'public/presentations'),
        // 默认会议纪要目录
        path.join(__dirname, 'minutes')
    ];

    dirs.forEach(dir => {
        if (!fs.existsSync(dir)) {
            fs.mkdirSync(dir, { recursive: true });
            console.log(`创建目录: ${dir}`);
        }
    });
};

// 生成示例语音文件（模拟）
const generateSampleVoices = () => {
    const voicesDir = path.join(__dirname, 'public/audio');
    
    // 示例语音文本
    const voiceSamples = {
        'male-clear': '大家好，我是前端开发工程师，负责用户界面的实现。',
        'female-professional': '我是后端开发工程师，专注于API设计和数据处理。',
        'male-deep': '我是系统架构师，负责整体技术架构的设计。',
        'male-technical': '我是DevOps工程师，负责构建和维护CI/CD流水线。',
        'female-managerial': '我是项目经理，负责项目的整体规划和协调。',
        'male-detailed': '我是测试工程师，负责确保产品质量和稳定性。'
    };

    // 为每个语音类型创建示例文件
    Object.entries(voiceSamples).forEach(([voiceType, text]) => {
        const filePath = path.join(voicesDir, `${voiceType}.txt`);
        if (!fs.existsSync(filePath)) {
            fs.writeFileSync(filePath, text, 'utf8');
            console.log(`生成语音示例: ${voiceType}.txt`);
        }
    });
};

// 初始化
const initialize = () => {
    createDirectories();
    generateSampleVoices();
    
const PORT = process.env.PORT || 3000;
    // 加载预设演示文稿
    if (Array.isArray(presentationsData)) {
        meetingState.presentations = presentationsData;
        console.log(`已加载预设演示文稿 ${presentationsData.length} 条`);
    }
    server.listen(PORT, () => {
        console.log(`服务器运行在 http://localhost:${PORT}`);
        console.log('会议室系统已启动');
    });
};

// 启动应用
initialize();
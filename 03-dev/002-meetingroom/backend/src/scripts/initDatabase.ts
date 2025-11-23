import { query } from '../config/database';
import UserModel from '../models/User';
import { logger } from '../utils/logger';

async function initDatabase() {
  try {
    logger.info('开始初始化数据库...');

    // 测试数据库连接
    // 使用应用启动时的 SQLite 初始化，跳过连接测试

    // 测试Redis连接
    // 跳过 Redis 测试（SQLite 会话替代）

    // 创建用户表
    logger.info('创建用户表...');
    await UserModel.createTable();

    // 创建会议室表
    logger.info('创建会议室表...');
    await createMeetingRoomsTable();

    // 创建会议表
    logger.info('创建会议表...');
    await createMeetingsTable();

    // 创建会议参与者表
    logger.info('创建会议参与者表...');
    await createMeetingParticipantsTable();

    // 创建会议记录表
    logger.info('创建会议记录表...');
    await createMeetingRecordsTable();

    // 创建AI智能体表
    logger.info('创建AI智能体表...');
    await createAIAgentsTable();

    // 创建系统配置表
    logger.info('创建系统配置表...');
    await createSystemConfigTable();

    // 创建操作日志表
    logger.info('创建操作日志表...');
    await createAuditLogsTable();

    logger.info('数据库初始化完成！');
  } catch (error) {
    logger.error('数据库初始化失败:', error);
    process.exit(1);
  }
}

// 创建会议室表
async function createMeetingRoomsTable() {
  const createTableSQL = `
    CREATE TABLE IF NOT EXISTS meeting_rooms (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      name VARCHAR(100) NOT NULL,
      description TEXT,
      capacity INTEGER NOT NULL CHECK (capacity > 0),
      floor INTEGER,
      building VARCHAR(100),
      equipment TEXT[], -- 设备列表，如：['projector', 'whiteboard', 'video_conference']
      status VARCHAR(20) NOT NULL DEFAULT 'available' CHECK (status IN ('available', 'occupied', 'maintenance', 'disabled')),
      hourly_rate DECIMAL(10, 2) DEFAULT 0.00,
      images TEXT[], -- 会议室图片URL列表
      created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
      updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
      created_by UUID REFERENCES users(id),
      CONSTRAINT meeting_rooms_name_check CHECK (char_length(name) >= 2)
    );

    -- 创建索引
    CREATE INDEX IF NOT EXISTS idx_meeting_rooms_name ON meeting_rooms(name);
    CREATE INDEX IF NOT EXISTS idx_meeting_rooms_status ON meeting_rooms(status);
    CREATE INDEX IF NOT EXISTS idx_meeting_rooms_capacity ON meeting_rooms(capacity);
    CREATE INDEX IF NOT EXISTS idx_meeting_rooms_floor ON meeting_rooms(floor);
    CREATE INDEX IF NOT EXISTS idx_meeting_rooms_created_by ON meeting_rooms(created_by);

    -- 创建更新时间触发器
    CREATE TRIGGER update_meeting_rooms_updated_at 
      BEFORE UPDATE ON meeting_rooms 
      FOR EACH ROW 
      EXECUTE FUNCTION update_updated_at_column();
  `;

  await query(createTableSQL);
  logger.info('会议室表创建成功');
}

// 创建会议表
async function createMeetingsTable() {
  const createTableSQL = `
    CREATE TABLE IF NOT EXISTS meetings (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      title VARCHAR(200) NOT NULL,
      description TEXT,
      meeting_room_id UUID NOT NULL REFERENCES meeting_rooms(id) ON DELETE CASCADE,
      organizer_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      start_time TIMESTAMP WITH TIME ZONE NOT NULL,
      end_time TIMESTAMP WITH TIME ZONE NOT NULL,
      status VARCHAR(20) NOT NULL DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'ongoing', 'completed', 'cancelled', 'no_show')),
      type VARCHAR(20) NOT NULL DEFAULT 'regular' CHECK (type IN ('regular', 'recurring', 'emergency', 'online')),
      priority VARCHAR(20) NOT NULL DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'urgent')),
      attendee_count INTEGER NOT NULL DEFAULT 0 CHECK (attendee_count >= 0),
      max_attendees INTEGER,
      notes TEXT,
      attachments TEXT[], -- 附件URL列表
      ai_summary TEXT, -- AI生成的会议摘要
      created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
      updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
      CONSTRAINT meetings_time_check CHECK (end_time > start_time),
      CONSTRAINT meetings_max_attendees_check CHECK (max_attendees IS NULL OR max_attendees > 0)
    );

    -- 创建索引
    CREATE INDEX IF NOT EXISTS idx_meetings_title ON meetings(title);
    CREATE INDEX IF NOT EXISTS idx_meetings_meeting_room_id ON meetings(meeting_room_id);
    CREATE INDEX IF NOT EXISTS idx_meetings_organizer_id ON meetings(organizer_id);
    CREATE INDEX IF NOT EXISTS idx_meetings_start_time ON meetings(start_time);
    CREATE INDEX IF NOT EXISTS idx_meetings_end_time ON meetings(end_time);
    CREATE INDEX IF NOT EXISTS idx_meetings_status ON meetings(status);
    CREATE INDEX IF NOT EXISTS idx_meetings_type ON meetings(type);
    CREATE INDEX IF NOT EXISTS idx_meetings_priority ON meetings(priority);

    -- 创建时间范围索引（用于查询冲突）
    CREATE INDEX IF NOT EXISTS idx_meetings_time_range ON meetings(meeting_room_id, start_time, end_time) 
    WHERE status NOT IN ('cancelled', 'no_show');

    -- 创建更新时间触发器
    CREATE TRIGGER update_meetings_updated_at 
      BEFORE UPDATE ON meetings 
      FOR EACH ROW 
      EXECUTE FUNCTION update_updated_at_column();
  `;

  await query(createTableSQL);
  logger.info('会议表创建成功');
}

// 创建会议参与者表
async function createMeetingParticipantsTable() {
  const createTableSQL = `
    CREATE TABLE IF NOT EXISTS meeting_participants (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      meeting_id UUID NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
      user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
      role VARCHAR(20) NOT NULL DEFAULT 'attendee' CHECK (role IN ('organizer', 'co_organizer', 'attendee', 'observer')),
      status VARCHAR(20) NOT NULL DEFAULT 'invited' CHECK (status IN ('invited', 'accepted', 'declined', 'tentative', 'no_show')),
      attendance_time TIMESTAMP WITH TIME ZONE, -- 实际参会时间
      feedback TEXT, -- 参会反馈
      created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
      updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
      CONSTRAINT meeting_participants_unique UNIQUE (meeting_id, user_id)
    );

    -- 创建索引
    CREATE INDEX IF NOT EXISTS idx_meeting_participants_meeting_id ON meeting_participants(meeting_id);
    CREATE INDEX IF NOT EXISTS idx_meeting_participants_user_id ON meeting_participants(user_id);
    CREATE INDEX IF NOT EXISTS idx_meeting_participants_role ON meeting_participants(role);
    CREATE INDEX IF NOT EXISTS idx_meeting_participants_status ON meeting_participants(status);

    -- 创建更新时间触发器
    CREATE TRIGGER update_meeting_participants_updated_at 
      BEFORE UPDATE ON meeting_participants 
      FOR EACH ROW 
      EXECUTE FUNCTION update_updated_at_column();
  `;

  await query(createTableSQL);
  logger.info('会议参与者表创建成功');
}

// 创建会议记录表
async function createMeetingRecordsTable() {
  const createTableSQL = `
    CREATE TABLE IF NOT EXISTS meeting_records (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      meeting_id UUID NOT NULL REFERENCES meetings(id) ON DELETE CASCADE,
      record_type VARCHAR(20) NOT NULL CHECK (record_type IN ('audio', 'video', 'transcript', 'summary', 'minutes')),
      file_path TEXT NOT NULL, -- 文件存储路径
      file_size BIGINT, -- 文件大小（字节）
      duration INTEGER, -- 录音/录像时长（秒）
      language VARCHAR(10) DEFAULT 'zh-CN', -- 语言代码
      ai_processed BOOLEAN DEFAULT FALSE, -- 是否已AI处理
      ai_confidence DECIMAL(5, 2), -- AI处理置信度
      content_text TEXT, -- 转录文本内容
      key_points TEXT[], -- 关键点列表
      action_items TEXT[], -- 行动项列表
      created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
      processed_at TIMESTAMP WITH TIME ZONE, -- AI处理完成时间
      created_by UUID REFERENCES users(id)
    );

    -- 创建索引
    CREATE INDEX IF NOT EXISTS idx_meeting_records_meeting_id ON meeting_records(meeting_id);
    CREATE INDEX IF NOT EXISTS idx_meeting_records_record_type ON meeting_records(record_type);
    CREATE INDEX IF NOT EXISTS idx_meeting_records_ai_processed ON meeting_records(ai_processed);
    CREATE INDEX IF NOT EXISTS idx_meeting_records_created_at ON meeting_records(created_at);
  `;

  await query(createTableSQL);
  logger.info('会议记录表创建成功');
}

// 创建AI智能体表
async function createAIAgentsTable() {
  const createTableSQL = `
    CREATE TABLE IF NOT EXISTS ai_agents (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      name VARCHAR(100) NOT NULL,
      type VARCHAR(50) NOT NULL CHECK (type IN ('yin', 'yang', 'wood', 'fire', 'earth', 'metal', 'water', 'coordinator', 'recorder')),
      description TEXT,
      personality TEXT, -- 性格特征
      expertise TEXT[], -- 专业领域
      status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'training', 'error')),
      priority_weight DECIMAL(3, 2) NOT NULL DEFAULT 1.00 CHECK (priority_weight >= 0 AND priority_weight <= 10),
      response_style VARCHAR(50), -- 响应风格
      language_support TEXT[], -- 支持的语言
      model_config JSONB, -- 模型配置
      api_endpoints JSONB, -- API端点配置
      last_active TIMESTAMP WITH TIME ZONE,
      total_interactions INTEGER DEFAULT 0,
      success_rate DECIMAL(5, 2) DEFAULT 0.00,
      created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
      updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
      CONSTRAINT ai_agents_name_unique UNIQUE (name),
      CONSTRAINT ai_agents_type_unique UNIQUE (type)
    );

    -- 创建索引
    CREATE INDEX IF NOT EXISTS idx_ai_agents_name ON ai_agents(name);
    CREATE INDEX IF NOT EXISTS idx_ai_agents_type ON ai_agents(type);
    CREATE INDEX IF NOT EXISTS idx_ai_agents_status ON ai_agents(status);

    -- 创建更新时间触发器
    CREATE TRIGGER update_ai_agents_updated_at 
      BEFORE UPDATE ON ai_agents 
      FOR EACH ROW 
      EXECUTE FUNCTION update_updated_at_column();
  `;

  await query(createTableSQL);
  logger.info('AI智能体表创建成功');

  // 插入默认AI智能体
  await insertDefaultAIAgents();
}

// 插入默认AI智能体
async function insertDefaultAIAgents() {
  const defaultAgents = [
    {
      name: '阴极智能体',
      type: 'yin',
      description: '负责深度思考、分析、策略制定的智能体',
      personality: '冷静、理性、善于分析',
      expertise: ['战略规划', '风险评估', '数据分析'],
      priority_weight: 2.5,
      response_style: '详细、深入、逻辑性强',
      language_support: ['zh-CN', 'en-US'],
      model_config: { model: 'qwen2.5:14b', temperature: 0.3, max_tokens: 2048 },
    },
    {
      name: '阳极智能体',
      type: 'yang',
      description: '负责执行、协调、沟通的智能体',
      personality: '积极、主动、善于沟通',
      expertise: ['项目管理', '团队协作', '客户服务'],
      priority_weight: 2.5,
      response_style: '简洁、直接、行动导向',
      language_support: ['zh-CN', 'en-US'],
      model_config: { model: 'qwen2.5:14b', temperature: 0.7, max_tokens: 1024 },
    },
    {
      name: '木行智能体',
      type: 'wood',
      description: '负责创新、成长、发展的智能体',
      personality: '创新、灵活、富有想象力',
      expertise: ['创新设计', '产品开发', '培训教育'],
      priority_weight: 1.5,
      response_style: '创意、启发、前瞻性',
      language_support: ['zh-CN'],
      model_config: { model: 'qwen2.5:7b', temperature: 0.8, max_tokens: 1536 },
    },
    {
      name: '火行智能体',
      type: 'fire',
      description: '负责热情、推广、营销的智能体',
      personality: '热情、外向、有感染力',
      expertise: ['市场营销', '品牌推广', '公关活动'],
      priority_weight: 1.5,
      response_style: '热情、激励、有说服力',
      language_support: ['zh-CN'],
      model_config: { model: 'qwen2.5:7b', temperature: 0.9, max_tokens: 1024 },
    },
    {
      name: '土行智能体',
      type: 'earth',
      description: '负责稳定、支持、服务的智能体',
      personality: '稳重、可靠、有耐心',
      expertise: ['技术支持', '系统维护', '客户服务'],
      priority_weight: 1.5,
      response_style: '详细、耐心、实用',
      language_support: ['zh-CN', 'en-US'],
      model_config: { model: 'qwen2.5:7b', temperature: 0.5, max_tokens: 1024 },
    },
    {
      name: '金行智能体',
      type: 'metal',
      description: '负责精确、分析、优化的智能体',
      personality: '精确、严谨、追求完美',
      expertise: ['数据分析', '质量控制', '流程优化'],
      priority_weight: 1.5,
      response_style: '精确、详细、数据驱动',
      language_support: ['zh-CN'],
      model_config: { model: 'qwen2.5:7b', temperature: 0.2, max_tokens: 1536 },
    },
    {
      name: '水行智能体',
      type: 'water',
      description: '负责适应、流动、协调的智能体',
      personality: '适应性强、灵活、善于协调',
      expertise: ['冲突调解', '关系维护', '变化管理'],
      priority_weight: 1.5,
      response_style: '温和、协调、包容',
      language_support: ['zh-CN'],
      model_config: { model: 'qwen2.5:7b', temperature: 0.6, max_tokens: 1024 },
    },
    {
      name: '协调智能体',
      type: 'coordinator',
      description: '负责整体协调、决策的智能体',
      personality: '平衡、公正、有领导力',
      expertise: ['决策支持', '资源协调', '冲突解决'],
      priority_weight: 3.0,
      response_style: '平衡、全面、决策导向',
      language_support: ['zh-CN', 'en-US'],
      model_config: { model: 'qwen2.5:14b', temperature: 0.4, max_tokens: 2048 },
    },
    {
      name: '记录智能体',
      type: 'recorder',
      description: '负责记录、归档、分析的智能体',
      personality: '细致、有条理、记忆力强',
      expertise: ['会议记录', '数据分析', '知识管理'],
      priority_weight: 2.0,
      response_style: '准确、完整、结构化',
      language_support: ['zh-CN', 'en-US'],
      model_config: { model: 'qwen2.5:7b', temperature: 0.3, max_tokens: 2048 },
    },
  ];

  for (const agent of defaultAgents) {
    const insertSQL = `
      INSERT INTO ai_agents (name, type, description, personality, expertise, priority_weight, response_style, language_support, model_config)
      VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
      ON CONFLICT (type) DO NOTHING
    `;
    await query(insertSQL, [
      agent.name,
      agent.type,
      agent.description,
      agent.personality,
      agent.expertise,
      agent.priority_weight,
      agent.response_style,
      agent.language_support,
      JSON.stringify(agent.model_config),
    ]);
  }

  logger.info('默认AI智能体插入成功');
}

// 创建系统配置表
async function createSystemConfigTable() {
  const createTableSQL = `
    CREATE TABLE IF NOT EXISTS system_config (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      config_key VARCHAR(100) NOT NULL UNIQUE,
      config_value TEXT NOT NULL,
      config_type VARCHAR(20) NOT NULL DEFAULT 'string' CHECK (config_type IN ('string', 'number', 'boolean', 'json')),
      description TEXT,
      is_encrypted BOOLEAN DEFAULT FALSE,
      created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
      updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
      updated_by UUID REFERENCES users(id)
    );

    -- 创建索引
    CREATE INDEX IF NOT EXISTS idx_system_config_key ON system_config(config_key);

    -- 创建更新时间触发器
    CREATE TRIGGER update_system_config_updated_at 
      BEFORE UPDATE ON system_config 
      FOR EACH ROW 
      EXECUTE FUNCTION update_updated_at_column();
  `;

  await query(createTableSQL);
  logger.info('系统配置表创建成功');

  // 插入默认系统配置
  await insertDefaultSystemConfig();
}

// 插入默认系统配置
async function insertDefaultSystemConfig() {
  const defaultConfigs = [
    {
      config_key: 'site_name',
      config_value: 'YDS智能会议室系统',
      config_type: 'string',
      description: '网站名称',
    },
    {
      config_key: 'max_meeting_duration',
      config_value: '480', // 8小时
      config_type: 'number',
      description: '最大会议时长（分钟）',
    },
    {
      config_key: 'advance_booking_days',
      config_value: '30',
      config_type: 'number',
      description: '可提前预订天数',
    },
    {
      config_key: 'auto_cancel_hours',
      config_value: '24',
      config_type: 'number',
      description: '自动取消未确认会议的小时数',
    },
    {
      config_key: 'ai_enabled',
      config_value: 'true',
      config_type: 'boolean',
      description: '是否启用AI功能',
    },
    {
      config_key: 'voice_enabled',
      config_value: 'true',
      config_type: 'boolean',
      description: '是否启用语音功能',
    },
    {
      config_key: 'recording_enabled',
      config_value: 'true',
      config_type: 'boolean',
      description: '是否启用录音功能',
    },
    {
      config_key: 'notification_email_enabled',
      config_value: 'true',
      config_type: 'boolean',
      description: '是否启用邮件通知',
    },
    {
      config_key: 'notification_sms_enabled',
      config_value: 'false',
      config_type: 'boolean',
      description: '是否启用短信通知',
    },
    {
      config_key: 'working_hours',
      config_value: JSON.stringify({
        monday: { start: '09:00', end: '18:00' },
        tuesday: { start: '09:00', end: '18:00' },
        wednesday: { start: '09:00', end: '18:00' },
        thursday: { start: '09:00', end: '18:00' },
        friday: { start: '09:00', end: '18:00' },
        saturday: { start: '09:00', end: '17:00' },
        sunday: { start: 'closed', end: 'closed' },
      }),
      config_type: 'json',
      description: '工作时间配置',
    },
  ];

  for (const config of defaultConfigs) {
    const insertSQL = `
      INSERT INTO system_config (config_key, config_value, config_type, description)
      VALUES ($1, $2, $3, $4)
      ON CONFLICT (config_key) DO NOTHING
    `;
    await query(insertSQL, [
      config.config_key,
      config.config_value,
      config.config_type,
      config.description,
    ]);
  }

  logger.info('默认系统配置插入成功');
}

// 创建操作日志表
async function createAuditLogsTable() {
  const createTableSQL = `
    CREATE TABLE IF NOT EXISTS audit_logs (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      user_id UUID REFERENCES users(id) ON DELETE SET NULL,
      action VARCHAR(100) NOT NULL,
      resource_type VARCHAR(50) NOT NULL,
      resource_id UUID,
      old_values JSONB,
      new_values JSONB,
      ip_address INET,
      user_agent TEXT,
      request_id VARCHAR(100),
      timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
      success BOOLEAN DEFAULT TRUE,
      error_message TEXT
    );

    -- 创建索引
    CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
    CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);
    CREATE INDEX IF NOT EXISTS idx_audit_logs_resource ON audit_logs(resource_type, resource_id);
    CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON audit_logs(timestamp);
    CREATE INDEX IF NOT EXISTS idx_audit_logs_request_id ON audit_logs(request_id);
  `;

  await query(createTableSQL);
  logger.info('操作日志表创建成功');
}

// 如果直接运行此脚本
if (require.main === module) {
  initDatabase();
}

export default initDatabase;
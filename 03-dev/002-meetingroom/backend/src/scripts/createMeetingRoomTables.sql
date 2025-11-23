-- 创建会议室表
CREATE TABLE IF NOT EXISTS meeting_rooms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    capacity INTEGER NOT NULL CHECK (capacity > 0),
    location VARCHAR(200) NOT NULL,
    floor INTEGER NOT NULL DEFAULT 1,
    building VARCHAR(100) NOT NULL,
    equipment JSONB DEFAULT '[]'::jsonb,
    images JSONB DEFAULT '[]'::jsonb,
    status VARCHAR(20) NOT NULL DEFAULT 'available' CHECK (status IN ('available', 'occupied', 'maintenance', 'disabled')),
    hourly_rate DECIMAL(10,2) NOT NULL CHECK (hourly_rate >= 0),
    open_time VARCHAR(5) NOT NULL CHECK (open_time ~ '^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$'),
    close_time VARCHAR(5) NOT NULL CHECK (close_time ~ '^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$'),
    working_days JSONB DEFAULT '[1,2,3,4,5]'::jsonb,
    manager_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 创建会议室预订表
CREATE TABLE IF NOT EXISTS meeting_room_bookings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    room_id UUID NOT NULL REFERENCES meeting_rooms(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE NOT NULL,
    attendee_count INTEGER NOT NULL CHECK (attendee_count > 0),
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'confirmed', 'cancelled', 'completed')),
    equipment_needed JSONB DEFAULT '[]'::jsonb,
    special_requirements TEXT,
    total_cost DECIMAL(10,2) NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT valid_booking_time CHECK (end_time > start_time)
);

-- 创建会议室设备表
CREATE TABLE IF NOT EXISTS meeting_room_equipment (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    category VARCHAR(50) NOT NULL,
    icon VARCHAR(50),
    is_available BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 创建会议室评价表
CREATE TABLE IF NOT EXISTS meeting_room_reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    room_id UUID NOT NULL REFERENCES meeting_rooms(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    booking_id UUID NOT NULL REFERENCES meeting_room_bookings(id) ON DELETE CASCADE,
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    cleanliness_rating INTEGER CHECK (cleanliness_rating >= 1 AND cleanliness_rating <= 5),
    equipment_rating INTEGER CHECK (equipment_rating >= 1 AND equipment_rating <= 5),
    service_rating INTEGER CHECK (service_rating >= 1 AND service_rating <= 5),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT unique_user_room_booking_review UNIQUE (room_id, user_id, booking_id)
);

-- 创建索引以提高查询性能
CREATE INDEX IF NOT EXISTS idx_meeting_rooms_status ON meeting_rooms(status);
CREATE INDEX IF NOT EXISTS idx_meeting_rooms_building ON meeting_rooms(building);
CREATE INDEX IF NOT EXISTS idx_meeting_rooms_capacity ON meeting_rooms(capacity);
CREATE INDEX IF NOT EXISTS idx_meeting_rooms_manager_id ON meeting_rooms(manager_id);
CREATE INDEX IF NOT EXISTS idx_meeting_rooms_created_at ON meeting_rooms(created_at);

CREATE INDEX IF NOT EXISTS idx_meeting_room_bookings_room_id ON meeting_room_bookings(room_id);
CREATE INDEX IF NOT EXISTS idx_meeting_room_bookings_user_id ON meeting_room_bookings(user_id);
CREATE INDEX IF NOT EXISTS idx_meeting_room_bookings_start_time ON meeting_room_bookings(start_time);
CREATE INDEX IF NOT EXISTS idx_meeting_room_bookings_end_time ON meeting_room_bookings(end_time);
CREATE INDEX IF NOT EXISTS idx_meeting_room_bookings_status ON meeting_room_bookings(status);
CREATE INDEX IF NOT EXISTS idx_meeting_room_bookings_created_at ON meeting_room_bookings(created_at);

CREATE INDEX IF NOT EXISTS idx_meeting_room_equipment_category ON meeting_room_equipment(category);
CREATE INDEX IF NOT EXISTS idx_meeting_room_equipment_available ON meeting_room_equipment(is_available);

CREATE INDEX IF NOT EXISTS idx_meeting_room_reviews_room_id ON meeting_room_reviews(room_id);
CREATE INDEX IF NOT EXISTS idx_meeting_room_reviews_user_id ON meeting_room_reviews(user_id);
CREATE INDEX IF NOT EXISTS idx_meeting_room_reviews_booking_id ON meeting_room_reviews(booking_id);
CREATE INDEX IF NOT EXISTS idx_meeting_room_reviews_rating ON meeting_room_reviews(rating);

-- 插入默认会议室设备数据
INSERT INTO meeting_room_equipment (name, description, category, icon) VALUES
    ('投影仪', '高清投影仪，支持1080P分辨率', 'display', 'projector'),
    ('白板', '可擦写白板，配备马克笔', 'writing', 'pen-tool'),
    ('音响系统', '高质量音响设备', 'audio', 'volume-2'),
    ('麦克风', '无线麦克风', 'audio', 'mic'),
    ('视频会议设备', '支持远程视频会议', 'communication', 'video'),
    ('空调', '中央空调系统', 'comfort', 'snowflake'),
    ('WiFi', '高速无线网络', 'network', 'wifi'),
    ('打印机', '激光打印机', 'office', 'printer'),
    ('饮水机', '冷热饮水机', 'comfort', 'cup'),
    ('咖啡机', '全自动咖啡机', 'comfort', 'coffee');

-- 创建更新时间的触发器
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_meeting_rooms_updated_at BEFORE UPDATE ON meeting_rooms
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_meeting_room_bookings_updated_at BEFORE UPDATE ON meeting_room_bookings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_meeting_room_equipment_updated_at BEFORE UPDATE ON meeting_room_equipment
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_meeting_room_reviews_updated_at BEFORE UPDATE ON meeting_room_reviews
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
// src/App.jsx
import { useState } from 'react';
import './App.css';

function App() {
  const [count, setCount] = useState(0);
  const [videoUrl, setVideoUrl] = useState(''); // 输入本地视频路径
  const [result, setResult] = useState('');     // 显示结果
  const [loading, setLoading] = useState(false); // 加载状态

  // 👇 替换为你的实际 ngrok 公网地址（注意：末尾无空格！）
  const API_BASE = "https://f4f2b90c1578.ngrok-free.app";

  const handleDeWatermark = async () => {
    if (!videoUrl.trim()) {
      alert("请输入有效的本地视频路径，例如：S:/videos/test.mp4");
      return;
    }

    setLoading(true);
    setResult('');

    try {
      const response = await fetch(`${API_BASE}/process`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ input_path: videoUrl.trim() }),
      });

      const data = await response.json();

      if (response.ok) {
        setResult(`✅ 处理成功！输出文件: ${data.output_path}`);
      } else {
        setResult(`❌ 处理失败: ${data.error || '未知错误'}`);
      }
    } catch (error) {
      console.error('网络请求失败:', error);
      setResult('❌ 网络错误：请确认 ngrok 隧道已启动且地址正确');
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <div>
        <h1>YDS Dewatermark AI</h1>
        <div className="card">
          <button onClick={() => setCount((count) => count + 1)}>
            count is {count}
          </button>
        </div>
        <p>基于 Vite + React + esbuild 的稳定工具链</p>
        <div className="read-the-docs">
          YDS 项目追求稳定交付，使用成熟技术栈
        </div>

        {/* 视频去水印功能区 */}
        <div style={{ marginTop: '20px', padding: '20px', border: '1px solid #ccc' }}>
          <h2>视频去水印（本地路径）</h2>
          <input
            type="text"
            value={videoUrl}
            onChange={(e) => setVideoUrl(e.target.value)}
            placeholder="请输入本地视频路径，如: S:/videos/test.mp4"
            style={{ width: '100%', marginBottom: '10px', padding: '8px' }}
          />
          <button onClick={handleDeWatermark} disabled={loading}>
            {loading ? '正在处理...' : '开始去水印'}
          </button>
          {result && (
            <div
              style={{
                marginTop: '10px',
                color: result.startsWith('✅') ? 'green' : 'red',
                fontWeight: 'bold',
              }}
            >
              {result}
            </div>
          )}
        </div>
      </div>
    </>
  );
}

export default App;
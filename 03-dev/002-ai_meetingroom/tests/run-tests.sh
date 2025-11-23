# 测试运行脚本

# 运行所有测试并生成覆盖率报告
echo "🧪 开始运行会议室系统测试..."

# 设置测试环境
export NODE_ENV=test
export JWT_SECRET=test-jwt-secret-for-ci

# 运行测试
echo "📊 运行单元测试..."
npm test -- --coverage --silent

# 检查测试结果
if [ $? -eq 0 ]; then
    echo "✅ 所有测试通过！"
    
    # 检查覆盖率阈值
    echo "📈 检查覆盖率阈值..."
    node -e "
    const fs = require('fs');
    const coverage = JSON.parse(fs.readFileSync('coverage/coverage-summary.json', 'utf8'));
    
    const thresholds = {
        lines: 70,
        statements: 70,
        functions: 70,
        branches: 70
    };
    
    let failed = false;
    Object.keys(thresholds).forEach(metric => {
        const actual = coverage.total[metric].pct;
        const required = thresholds[metric];
        if (actual < required) {
            console.error(\`❌ 覆盖率检查失败: \${metric} \${actual}% < \${required}%\`);
            failed = true;
        } else {
            console.log(\`✅ \${metric}: \${actual}% >= \${required}%\`);
        }
    });
    
    if (failed) {
        process.exit(1);
    }
    "
    
    if [ $? -eq 0 ]; then
        echo "🎉 覆盖率检查通过！"
        echo "📁 覆盖率报告位置: coverage/lcov-report/index.html"
    else
        echo "❌ 覆盖率检查失败！"
        exit 1
    fi
else
    echo "❌ 测试失败！"
    exit 1
fi
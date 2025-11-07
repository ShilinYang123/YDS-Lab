const fs = require('fs');
const path = require('path');

console.log('🔒 YDS-Lab长记忆系统安全审计');
console.log('=====================================');

// 安全审计结果
const auditResults = {
  filePermissions: [],
  configSecurity: [],
  codeSecurity: [],
  dependencySecurity: [],
  recommendations: []
};

// 1. 文件权限检查
console.log('📁 文件权限安全检查:');
function checkFilePermissions() {
  const sensitiveFiles = [
    './memory-config.yaml',
    './package.json',
    './tsconfig.json',
    './.eslintrc.js'
  ];

  sensitiveFiles.forEach(file => {
    if (fs.existsSync(file)) {
      try {
        const stats = fs.statSync(file);
        const mode = stats.mode.toString(8);
        console.log(`  ✓ ${file}: 权限 ${mode}`);
        auditResults.filePermissions.push({
          file,
          permissions: mode,
          status: 'checked'
        });
      } catch (err) {
        console.log(`  ❌ ${file}: 权限检查失败 - ${err.message}`);
        auditResults.filePermissions.push({
          file,
          status: 'error',
          error: err.message
        });
      }
    } else {
      console.log(`  ⚠️ ${file}: 文件不存在`);
    }
  });
}

// 2. 配置安全检查
console.log('\n⚙️ 配置安全检查:');
function checkConfigSecurity() {
  // 检查package.json中的安全配置
  try {
    const pkg = JSON.parse(fs.readFileSync('./package.json', 'utf8'));
    
    // 检查是否有安全相关的脚本
    const scripts = pkg.scripts || {};
    const hasSecurityScript = Object.keys(scripts).some(key => 
      key.includes('security') || key.includes('audit')
    );
    
    console.log(`  ${hasSecurityScript ? '✓' : '⚠️'} 安全脚本: ${hasSecurityScript ? '已配置' : '未配置'}`);
    auditResults.configSecurity.push({
      check: 'security_scripts',
      status: hasSecurityScript ? 'pass' : 'warning',
      message: hasSecurityScript ? '已配置安全脚本' : '建议添加安全审计脚本'
    });

    // 检查依赖版本
    const deps = { ...pkg.dependencies, ...pkg.devDependencies };
    const outdatedDeps = [];
    
    // 简单的版本检查（实际项目中应使用npm audit）
    Object.keys(deps).forEach(dep => {
      const version = deps[dep];
      if (version.includes('^') || version.includes('~')) {
        console.log(`  ✓ ${dep}: 使用语义版本 ${version}`);
      } else if (version === '*' || version === 'latest') {
        console.log(`  ⚠️ ${dep}: 使用不安全的版本标识 ${version}`);
        outdatedDeps.push(dep);
      }
    });

    auditResults.configSecurity.push({
      check: 'dependency_versions',
      status: outdatedDeps.length === 0 ? 'pass' : 'warning',
      message: outdatedDeps.length === 0 ? '依赖版本配置安全' : `发现${outdatedDeps.length}个不安全的版本配置`
    });

  } catch (err) {
    console.log(`  ❌ package.json检查失败: ${err.message}`);
    auditResults.configSecurity.push({
      check: 'package_json',
      status: 'error',
      error: err.message
    });
  }

  // 检查memory-config.yaml安全配置
  try {
    const configContent = fs.readFileSync('./memory-config.yaml', 'utf8');
    
    // 检查是否包含敏感信息
    const sensitivePatterns = [
      /password\s*[:=]\s*[^#\n]+/i,
      /secret\s*[:=]\s*[^#\n]+/i,
      /token\s*[:=]\s*[^#\n]+/i,
      /key\s*[:=]\s*[^#\n]+/i
    ];

    let hasSensitiveData = false;
    sensitivePatterns.forEach(pattern => {
      if (pattern.test(configContent)) {
        hasSensitiveData = true;
      }
    });

    console.log(`  ${hasSensitiveData ? '⚠️' : '✓'} 配置文件敏感信息: ${hasSensitiveData ? '发现敏感信息' : '未发现敏感信息'}`);
    auditResults.configSecurity.push({
      check: 'sensitive_data',
      status: hasSensitiveData ? 'warning' : 'pass',
      message: hasSensitiveData ? '配置文件中可能包含敏感信息' : '配置文件安全'
    });

    // 检查加密配置
    const hasEncryption = configContent.includes('encryption') && configContent.includes('enabled: true');
    console.log(`  ${hasEncryption ? '✓' : '⚠️'} 数据加密: ${hasEncryption ? '已启用' : '未启用'}`);
    auditResults.configSecurity.push({
      check: 'encryption',
      status: hasEncryption ? 'pass' : 'warning',
      message: hasEncryption ? '数据加密已启用' : '建议启用数据加密'
    });

  } catch (err) {
    console.log(`  ❌ 配置文件检查失败: ${err.message}`);
  }
}

// 3. 代码安全检查
console.log('\n🔍 代码安全检查:');
function checkCodeSecurity() {
  const sourceFiles = [];
  
  // 扫描源代码文件
  function scanDirectory(dir) {
    try {
      const items = fs.readdirSync(dir);
      items.forEach(item => {
        const fullPath = path.join(dir, item);
        const stat = fs.statSync(fullPath);
        
        if (stat.isDirectory() && !item.startsWith('.') && item !== 'node_modules') {
          scanDirectory(fullPath);
        } else if (item.endsWith('.ts') || item.endsWith('.js')) {
          sourceFiles.push(fullPath);
        }
      });
    } catch (err) {
      console.log(`  ⚠️ 扫描目录失败: ${dir} - ${err.message}`);
    }
  }

  scanDirectory('./src');

  console.log(`  📊 扫描了 ${sourceFiles.length} 个源代码文件`);

  // 检查常见安全问题
  let securityIssues = 0;
  const securityPatterns = [
    { pattern: /eval\s*\(/g, issue: 'eval()函数使用', severity: 'high' },
    { pattern: /innerHTML\s*=/g, issue: 'innerHTML赋值', severity: 'medium' },
    { pattern: /document\.write\s*\(/g, issue: 'document.write使用', severity: 'medium' },
    { pattern: /console\.log\s*\(/g, issue: '调试信息输出', severity: 'low' },
    { pattern: /TODO|FIXME|HACK/g, issue: '待修复代码', severity: 'low' }
  ];

  sourceFiles.forEach(file => {
    try {
      const content = fs.readFileSync(file, 'utf8');
      
      securityPatterns.forEach(({ pattern, issue, severity }) => {
        const matches = content.match(pattern);
        if (matches) {
          securityIssues++;
          console.log(`  ⚠️ ${path.relative('.', file)}: ${issue} (${matches.length}处, ${severity})`);
          auditResults.codeSecurity.push({
            file: path.relative('.', file),
            issue,
            severity,
            count: matches.length
          });
        }
      });
    } catch (err) {
      console.log(`  ❌ 读取文件失败: ${file} - ${err.message}`);
    }
  });

  if (securityIssues === 0) {
    console.log('  ✓ 未发现明显的代码安全问题');
  } else {
    console.log(`  ⚠️ 发现 ${securityIssues} 个潜在安全问题`);
  }
}

// 4. 生成安全建议
function generateRecommendations() {
  console.log('\n💡 安全建议:');
  
  const recommendations = [
    '1. 定期运行 npm audit 检查依赖漏洞',
    '2. 启用配置文件中的数据加密功能',
    '3. 实施访问控制和身份验证机制',
    '4. 定期备份重要数据',
    '5. 监控系统日志和异常行为',
    '6. 使用HTTPS协议进行数据传输',
    '7. 定期更新依赖包到最新安全版本',
    '8. 实施输入验证和数据清理',
    '9. 配置适当的文件权限',
    '10. 建立安全事件响应流程'
  ];

  recommendations.forEach(rec => {
    console.log(`  ${rec}`);
    auditResults.recommendations.push(rec);
  });
}

// 执行安全审计
async function runSecurityAudit() {
  checkFilePermissions();
  checkConfigSecurity();
  checkCodeSecurity();
  generateRecommendations();

  console.log('\n📋 安全审计总结:');
  console.log('=====================================');
  
  const totalIssues = auditResults.codeSecurity.length + 
                     auditResults.configSecurity.filter(c => c.status === 'warning').length;
  
  console.log(`文件权限检查: ${auditResults.filePermissions.length} 个文件`);
  console.log(`配置安全检查: ${auditResults.configSecurity.length} 项检查`);
  console.log(`代码安全问题: ${auditResults.codeSecurity.length} 个问题`);
  console.log(`安全建议: ${auditResults.recommendations.length} 条`);
  
  if (totalIssues === 0) {
    console.log('\n🎉 安全审计通过！系统安全状况良好。');
  } else if (totalIssues < 5) {
    console.log('\n⚠️ 发现少量安全问题，建议及时处理。');
  } else {
    console.log('\n❌ 发现较多安全问题，需要重点关注和处理。');
  }
  
  console.log('\n🔒 安全审计完成!');
}

// 运行审计
runSecurityAudit().catch(err => {
  console.error('❌ 安全审计失败:', err.message);
});
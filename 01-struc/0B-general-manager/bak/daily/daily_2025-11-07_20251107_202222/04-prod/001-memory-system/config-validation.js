const fs = require('fs');
const path = require('path');

console.log('🔍 YDS-Lab长记忆系统配置验证');
console.log('=====================================');

// 检查配置文件存在性
const configFiles = [
  './memory-config.yaml',
  './tsconfig.json',
  './package.json',
  './src/config/defaults.ts',
  './src/config/manager.ts',
  './src/config/validator.ts'
];

console.log('📁 配置文件存在性检查:');
configFiles.forEach(file => {
  const exists = fs.existsSync(file);
  console.log(`  ${exists ? '✓' : '✗'} ${file}`);
});

// 检查数据目录
const dataDirs = [
  './data',
  './data/memories',
  './data/knowledge-graph',
  './data/cache',
  './logs',
  './backups'
];

console.log('\n📂 数据目录结构检查:');
dataDirs.forEach(dir => {
  const exists = fs.existsSync(dir);
  console.log(`  ${exists ? '✓' : '✗'} ${dir}`);
  if (!exists) {
    try {
      fs.mkdirSync(dir, { recursive: true });
      console.log(`    ➤ 已创建目录: ${dir}`);
    } catch (err) {
      console.log(`    ✗ 创建失败: ${err.message}`);
    }
  }
});

// 检查package.json配置
console.log('\n📦 Package.json配置检查:');
try {
  const pkg = JSON.parse(fs.readFileSync('./package.json', 'utf8'));
  console.log(`  ✓ 项目名称: ${pkg.name}`);
  console.log(`  ✓ 版本: ${pkg.version}`);
  console.log(`  ✓ 脚本数量: ${Object.keys(pkg.scripts || {}).length}`);
  console.log(`  ✓ 依赖数量: ${Object.keys(pkg.dependencies || {}).length}`);
  console.log(`  ✓ 开发依赖数量: ${Object.keys(pkg.devDependencies || {}).length}`);
} catch (err) {
  console.log(`  ✗ Package.json读取失败: ${err.message}`);
}

// 检查TypeScript配置
console.log('\n⚙️ TypeScript配置检查:');
try {
  const tsconfig = JSON.parse(fs.readFileSync('./tsconfig.json', 'utf8'));
  console.log(`  ✓ 编译目标: ${tsconfig.compilerOptions?.target || 'N/A'}`);
  console.log(`  ✓ 模块系统: ${tsconfig.compilerOptions?.module || 'N/A'}`);
  console.log(`  ✓ 输出目录: ${tsconfig.compilerOptions?.outDir || 'N/A'}`);
  console.log(`  ✓ 严格模式: ${tsconfig.compilerOptions?.strict ? '启用' : '禁用'}`);
} catch (err) {
  console.log(`  ✗ TypeScript配置读取失败: ${err.message}`);
}

console.log('\n🎯 配置验证完成!');
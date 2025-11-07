const fs = require('fs');
const path = require('path');
const { performance } = require('perf_hooks');

console.log('📊 YDS-Lab长记忆系统性能分析');
console.log('=====================================');

// 性能测试函数
async function performanceTest() {
  const results = {
    memoryOperations: {},
    fileOperations: {},
    systemResources: {}
  };

  // 1. 内存操作性能测试
  console.log('🧠 内存操作性能测试:');
  
  // 测试大量对象创建
  const start1 = performance.now();
  const testObjects = [];
  for (let i = 0; i < 10000; i++) {
    testObjects.push({
      id: `memory_${i}`,
      content: `测试内容 ${i}`,
      timestamp: Date.now(),
      type: 'semantic',
      importance: Math.random() * 10
    });
  }
  const end1 = performance.now();
  results.memoryOperations.objectCreation = end1 - start1;
  console.log(`  ✓ 创建10000个内存对象: ${(end1 - start1).toFixed(2)}ms`);

  // 测试数组搜索性能
  const start2 = performance.now();
  const searchResults = testObjects.filter(obj => 
    obj.content.includes('测试') && obj.importance > 5
  );
  const end2 = performance.now();
  results.memoryOperations.arraySearch = end2 - start2;
  console.log(`  ✓ 数组搜索操作: ${(end2 - start2).toFixed(2)}ms (找到${searchResults.length}个结果)`);

  // 2. 文件操作性能测试
  console.log('\n📁 文件操作性能测试:');
  
  // 测试文件写入性能
  const testData = JSON.stringify(testObjects.slice(0, 1000));
  const start3 = performance.now();
  fs.writeFileSync('./temp-performance-test.json', testData);
  const end3 = performance.now();
  results.fileOperations.write = end3 - start3;
  console.log(`  ✓ 写入1000个对象到文件: ${(end3 - start3).toFixed(2)}ms`);

  // 测试文件读取性能
  const start4 = performance.now();
  const readData = fs.readFileSync('./temp-performance-test.json', 'utf8');
  const parsedData = JSON.parse(readData);
  const end4 = performance.now();
  results.fileOperations.read = end4 - start4;
  console.log(`  ✓ 读取并解析文件: ${(end4 - start4).toFixed(2)}ms (${parsedData.length}个对象)`);

  // 清理测试文件
  fs.unlinkSync('./temp-performance-test.json');

  // 3. 系统资源使用情况
  console.log('\n💻 系统资源使用情况:');
  const memUsage = process.memoryUsage();
  results.systemResources.memory = memUsage;
  
  console.log(`  ✓ RSS内存使用: ${(memUsage.rss / 1024 / 1024).toFixed(2)} MB`);
  console.log(`  ✓ 堆内存使用: ${(memUsage.heapUsed / 1024 / 1024).toFixed(2)} MB`);
  console.log(`  ✓ 堆内存总量: ${(memUsage.heapTotal / 1024 / 1024).toFixed(2)} MB`);
  console.log(`  ✓ 外部内存: ${(memUsage.external / 1024 / 1024).toFixed(2)} MB`);

  // 4. 项目文件大小分析
  console.log('\n📦 项目文件大小分析:');
  const projectStats = analyzeProjectSize('./src');
  results.systemResources.projectSize = projectStats;
  
  console.log(`  ✓ 源代码文件数: ${projectStats.fileCount}`);
  console.log(`  ✓ 总代码行数: ${projectStats.totalLines}`);
  console.log(`  ✓ 源代码大小: ${(projectStats.totalSize / 1024).toFixed(2)} KB`);

  return results;
}

// 分析项目大小
function analyzeProjectSize(dir) {
  let fileCount = 0;
  let totalSize = 0;
  let totalLines = 0;

  function scanDirectory(dirPath) {
    const items = fs.readdirSync(dirPath);
    
    for (const item of items) {
      const fullPath = path.join(dirPath, item);
      const stat = fs.statSync(fullPath);
      
      if (stat.isDirectory()) {
        scanDirectory(fullPath);
      } else if (item.endsWith('.ts') || item.endsWith('.js')) {
        fileCount++;
        totalSize += stat.size;
        
        try {
          const content = fs.readFileSync(fullPath, 'utf8');
          totalLines += content.split('\n').length;
        } catch (err) {
          // 忽略读取错误
        }
      }
    }
  }

  try {
    scanDirectory(dir);
  } catch (err) {
    console.log(`  ⚠️ 扫描目录失败: ${err.message}`);
  }

  return { fileCount, totalSize, totalLines };
}

// 运行性能测试
performanceTest().then(results => {
  console.log('\n📈 性能分析报告:');
  console.log('=====================================');
  console.log(`内存对象创建性能: ${results.memoryOperations.objectCreation?.toFixed(2)}ms`);
  console.log(`数组搜索性能: ${results.memoryOperations.arraySearch?.toFixed(2)}ms`);
  console.log(`文件写入性能: ${results.fileOperations.write?.toFixed(2)}ms`);
  console.log(`文件读取性能: ${results.fileOperations.read?.toFixed(2)}ms`);
  console.log(`当前内存使用: ${(results.systemResources.memory.heapUsed / 1024 / 1024).toFixed(2)}MB`);
  
  // 性能评估
  console.log('\n🎯 性能评估:');
  if (results.memoryOperations.objectCreation < 100) {
    console.log('  ✓ 内存操作性能: 优秀');
  } else if (results.memoryOperations.objectCreation < 500) {
    console.log('  ⚠️ 内存操作性能: 良好');
  } else {
    console.log('  ❌ 内存操作性能: 需要优化');
  }
  
  if (results.systemResources.memory.heapUsed < 50 * 1024 * 1024) {
    console.log('  ✓ 内存使用: 正常');
  } else {
    console.log('  ⚠️ 内存使用: 偏高');
  }
  
  console.log('\n🏁 性能分析完成!');
}).catch(err => {
  console.error('❌ 性能测试失败:', err.message);
});
#!/usr/bin/env node

/**
 * OpenClaw Guardian 安装配置脚本
 * 交互式引导用户配置守护进程参数
 */

const fs = require('fs');
const path = require('path');

const CONFIG = {
  configFile: path.join(__dirname, 'config.json'),
  defaultPort: 18789,
  defaultInterval: 30000,
  defaultRetries: 3,
  gatewayPath: 'C:\\Users\\visio\\AppData\\Roaming\\npm\\node_modules\\openclaw\\openclaw.mjs'
};

function log(msg) {
  console.log(msg);
}

function logSuccess(msg) {
  console.log(`✅ ${msg}`);
}

function logError(msg) {
  console.log(`❌ ${msg}`);
}

function logInfo(msg) {
  console.log(`ℹ️  ${msg}`);
}

function logWarn(msg) {
  console.log(`⚠️  ${msg}`);
}

function askQuestion(question) {
  return new Promise((resolve) => {
    const readline = require('readline');
    const rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout
    });
    
    rl.question(question, (answer) => {
      rl.close();
      resolve(answer.trim());
    });
  });
}

async function main() {
  console.log('\n========================================');
  console.log('  OpenClaw Guardian 安装配置');
  console.log('========================================\n');
  
  // 检查是否已存在配置
  let existingConfig = null;
  if (fs.existsSync(CONFIG.configFile)) {
    try {
      existingConfig = JSON.parse(fs.readFileSync(CONFIG.configFile, 'utf8'));
      logInfo(`检测到已存在配置: ${CONFIG.configFile}`);
      log('是否重新配置？(输入 "y" 重新配置，直接回车跳过)\n');
      const answer = await askQuestion('> ');
      if (answer.toLowerCase() !== 'y') {
        logSuccess('使用现有配置，退出安装。\n');
        return;
      }
    } catch (e) {
      logWarn('现有配置损坏，将重新创建。\n');
    }
  }
  
  // 1. 配置端口
  log('========================================');
  log('  1. 配置 Gateway 端口');
  log('========================================\n');
  
  let port = CONFIG.defaultPort;
  const portAnswer = await askQuestion(`请输入 OpenClaw Gateway 端口 (默认 ${CONFIG.defaultPort}):\n> `);
  if (portAnswer) {
    const parsedPort = parseInt(portAnswer);
    if (isNaN(parsedPort) || parsedPort < 1 || parsedPort > 65535) {
      logError('端口无效，使用默认值。\n');
      port = CONFIG.defaultPort;
    } else {
      port = parsedPort;
      logSuccess(`端口设置为: ${port}\n`);
    }
  } else {
    logInfo(`使用默认端口: ${port}\n`);
  }
  
  // 2. 配置检查间隔
  log('========================================');
  log('  2. 配置检查间隔');
  log('========================================\n');
  
  let interval = CONFIG.defaultInterval;
  const intervalAnswer = await askQuestion(`请输入检查间隔（秒，默认 ${CONFIG.defaultInterval/1000}）:\n> `);
  if (intervalAnswer) {
    const parsedInterval = parseInt(intervalAnswer);
    if (isNaN(parsedInterval) || parsedInterval < 5) {
      logError('间隔太短，使用默认值。\n');
      interval = CONFIG.defaultInterval;
    } else {
      interval = parsedInterval * 1000;
      logSuccess(`检查间隔设置为: ${interval/1000} 秒\n`);
    }
  } else {
    logInfo(`使用默认间隔: ${interval/1000} 秒\n`);
  }
  
  // 3. 配置重试次数
  log('========================================');
  log('  3. 配置连续失败重试次数');
  log('========================================\n');
  
  let maxRetries = CONFIG.defaultRetries;
  const retriesAnswer = await askQuestion(`请输入连续失败重试次数（默认 ${CONFIG.defaultRetries}）:\n> `);
  if (retriesAnswer) {
    const parsedRetries = parseInt(retriesAnswer);
    if (isNaN(parsedRetries) || parsedRetries < 1) {
      logError('次数无效，使用默认值。\n');
      maxRetries = CONFIG.defaultRetries;
    } else {
      maxRetries = parsedRetries;
      logSuccess(`重试次数设置为: ${maxRetries}\n`);
    }
  } else {
    logInfo(`使用默认重试次数: ${maxRetries}\n`);
  }
  
  // 保存配置
  const config = {
    gatewayPort: port,
    checkInterval: interval,
    maxRetries: maxRetries,
    gatewayPath: CONFIG.gatewayPath,
    configFile: 'C:\\Users\\visio\\.openclaw\\openclaw.json',
    backupDir: 'C:\\Users\\visio\\.openclaw\\backups',
    configuredAt: new Date().toISOString()
  };
  
  fs.writeFileSync(CONFIG.configFile, JSON.stringify(config, null, 2), 'utf8');
  
  console.log('\n========================================');
  logSuccess('  配置完成！');
  console.log('========================================\n');
  
  console.log('配置文件已保存到:');
  console.log(`  ${CONFIG.configFile}\n`);
  
  console.log('当前配置:');
  console.log(`  - Gateway 端口: ${port}`);
  console.log(`  - 检查间隔: ${interval/1000} 秒`);
  console.log(`  - 重试次数: ${maxRetries}\n`);
  
  console.log('启动守护进程:');
  console.log('  node scripts/openclaw-guardian.js\n');
  
  console.log('查看日志:');
  console.log('  type scripts\\guardian-log.txt\n');
}

main().catch(err => {
  logError(`安装失败: ${err.message}`);
  process.exit(1);
});

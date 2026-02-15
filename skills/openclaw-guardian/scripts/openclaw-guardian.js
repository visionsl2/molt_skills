/**
 * OpenClaw 进程守护脚本
 * 功能：
 * 1. 监控 Gateway 状态
 * 2. 连续启动失败时自动恢复上一个备份的配置
 */

const { exec, spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const CONFIG = {
  // 配置文件路径（可选，setup.js 创建）
  configFile: path.join(__dirname, 'config.json'),
  
  // 默认值（如果没有配置）
  defaultPort: 18789,
  defaultInterval: 30000,
  maxRetries: 3,
  
  // 关键路径
  gatewayPath: 'C:\\Users\\visio\\AppData\\Roaming\\npm\\node_modules\\openclaw\\openclaw.mjs',
  logFile: path.join(__dirname, 'guardian-log.txt'),
  stateFile: path.join(__dirname, 'guardian-state.json'),
  configFilePath: 'C:\\Users\\visio\\.openclaw\\openclaw.json',
  backupDir: 'C:\\Users\\visio\\.openclaw\\backups'
};

// 运行时配置
let runtimeConfig = {
  gatewayPort: CONFIG.defaultPort,
  checkInterval: CONFIG.defaultInterval,
  maxRetries: CONFIG.maxRetries,
  gatewayPath: CONFIG.gatewayPath
};

/**
 * 加载配置（优先使用 setup.js 创建的配置）
 */
function loadConfig() {
  // 检查是否有 setup.js 创建的配置文件
  if (fs.existsSync(CONFIG.configFile)) {
    try {
      const userConfig = JSON.parse(fs.readFileSync(CONFIG.configFile, 'utf8'));
      runtimeConfig.gatewayPort = userConfig.gatewayPort || CONFIG.defaultPort;
      runtimeConfig.checkInterval = userConfig.checkInterval || CONFIG.defaultInterval;
      runtimeConfig.maxRetries = userConfig.maxRetries || CONFIG.defaultRetries;
      runtimeConfig.gatewayPath = userConfig.gatewayPath || CONFIG.gatewayPath;
      log(`📋 已加载配置（端口: ${runtimeConfig.gatewayPort}，间隔: ${runtimeConfig.checkInterval/1000}秒）`);
      return true;
    } catch (e) {
      logWarn(`配置文件损坏，使用默认值`);
    }
  }
  
  // 提示用户运行 setup.js
  logError(`未检测到配置！`);
  log(`请先运行配置脚本:`);
  log(`  cd skills/openclaw-guardian`);
  log(`  node scripts/setup.js\n`);
  return false;
}

let restarts = 0;
let consecutiveFailures = 0;

function log(msg) {
  const line = `[${new Date().toLocaleString()}] ${msg}\n`;
  fs.appendFileSync(CONFIG.logFile, line);
  console.log(line);
}

function getGatewayPid() {
  const port = runtimeConfig.gatewayPort;
  
  return new Promise((resolve) => {
    // 方法1: 使用 netstat 获取 PID（更可靠）
    const cmd1 = `netstat -ano | findstr :${port} | findstr LISTENING`;
    
    exec(cmd1, (err, stdout) => {
      if (stdout && stdout.trim()) {
        // 解析最后一段数字（PID）
        const lines = stdout.trim().split('\n');
        for (const line of lines) {
          const parts = line.trim().split(/\s+/);
          const pid = parseInt(parts[parts.length - 1]);
          if (pid > 0) {
            resolve(pid);
            return;
          }
        }
      }
      
      // 方法2: 如果 netstat 失败，尝试使用 Get-NetTCPConnection
      const cmd2 = `powershell -Command "Get-NetTCPConnection -LocalPort ${port} -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess"`;
      exec(cmd2, (err2, stdout2) => {
        const pid = parseInt(stdout2.trim());
        resolve(isNaN(pid) ? null : pid);
      });
    });
  });
}

function isGatewayHealthy() {
  const port = runtimeConfig.gatewayPort;
  return new Promise((resolve) => {
    const http = require('http');
    const req = http.get({
      hostname: 'localhost',
      port: port,
      path: '/health',
      timeout: 2000
    }, (res) => {
      resolve(res.statusCode === 200);
    });
    req.on('error', () => resolve(false));
    req.on('timeout', () => { req.destroy(); resolve(false); });
  });
}

/**
 * 恢复上一个备份的配置
 */
function restoreConfig() {
  try {
    const files = fs.readdirSync(CONFIG.backupDir)
      .filter(f => f.startsWith('openclaw.json.bak.'))
      .map(f => ({
        name: f,
        path: path.join(CONFIG.backupDir, f),
        mtime: fs.statSync(path.join(CONFIG.backupDir, f)).mtime.getTime()
      }))
      .sort((a, b) => b.mtime - a.mtime);
    
    if (files.length === 0) {
      log('❌ 没有找到备份文件，无法恢复');
      return false;
    }
    
    const latestBackup = files[0];
    fs.copyFileSync(latestBackup.path, CONFIG.configFile);
    log(`✅ 已恢复配置: ${latestBackup.name}`);
    
    return true;
  } catch (err) {
    log(`❌ 恢复配置失败: ${err.message}`);
    return false;
  }
}

/**
 * 保存守护进程状态
 */
function saveState() {
  try {
    const state = {
      consecutiveFailures,
      lastRestart: new Date().toISOString(),
      lastBackup: getLatestBackupTime()
    };
    fs.writeFileSync(CONFIG.stateFile, JSON.stringify(state, null, 2));
  } catch (err) {
    log(`⚠️ 保存状态失败: ${err.message}`);
  }
}

/**
 * 获取最新备份的时间
 */
function getLatestBackupTime() {
  try {
    const files = fs.readdirSync(CONFIG.backupDir)
      .filter(f => f.startsWith('openclaw.json.bak.'))
      .map(f => fs.statSync(path.join(CONFIG.backupDir, f)).mtime)
      .sort((a, b) => b - a);
    
    return files.length > 0 ? files[0].toISOString() : null;
  } catch {
    return null;
  }
}

/**
 * 加载守护进程状态
 */
function loadState() {
  try {
    if (fs.existsSync(CONFIG.stateFile)) {
      const state = JSON.parse(fs.readFileSync(CONFIG.stateFile, 'utf-8'));
      consecutiveFailures = state.consecutiveFailures || 0;
      log(`📊 已加载状态，连续失败: ${consecutiveFailures}`);
    }
  } catch (err) {
    log(`⚠️ 加载状态失败: ${err.message}`);
  }
}

async function startGateway() {
  // 每次启动时使用配置的端口
  const port = runtimeConfig.gatewayPort;
  const gatewayPath = runtimeConfig.gatewayPath;
  
  log(`🚀 启动 Gateway (端口: ${port})...`);
  
  return new Promise((resolve) => {
    const proc = spawn('node', [
      gatewayPath, 
      'gateway', 
      '--port', String(port),
      '--token', '123123',
      '--password', '123123'
    ], {
      stdio: 'ignore',
      detached: false,
      windowsHide: true
    });
    
    proc.on('error', (err) => {
      log(`❌ 启动错误: ${err.message}`);
      resolve(false);
    });
    
    proc.on('exit', (code) => {
      if (code !== 0) {
        log(`⚠️ Gateway 退出，代码: ${code}`);
      }
    });
    
    // 等待 15 秒后检查（给Gateway足够的启动时间）
    setTimeout(async () => {
      log(`🔍 正在检查 Gateway 状态...`);
      
      // 先检查端口
      const pid = await getGatewayPid();
      if (!pid) {
        log(`❌ 启动失败 - 端口未监听`);
        resolve(false);
        return;
      }
      
      log(`📍 端口已监听，PID: ${pid}`);
      
      // 再检查健康状态（最多重试3次）
      for (let i = 0; i < 3; i++) {
        const healthy = await isGatewayHealthy();
        if (healthy) {
          log(`✅ Gateway 已启动并健康运行，PID: ${pid}`);
          resolve(true);
          return;
        }
        log(`⏳ 健康检查中... (${i+1}/3)`);
        await new Promise(r => setTimeout(r, 2000)); // 等待2秒重试
      }
      
      log(`⚠️ 端口已监听但健康检查失败，PID: ${pid}，仍视为启动成功`);
      resolve(true); // 端口已监听就视为成功
    }, 15000); // 15秒等待时间
  });
}

async function check() {
  log(`--- 检查 ---`);
  
  const pid = await getGatewayPid();
  
  if (pid) {
    log(`📍 Gateway 已运行，PID: ${pid}`);
    const healthy = await isGatewayHealthy();
    if (healthy) {
      log('✅ 正常');
      consecutiveFailures = 0;
      saveState();
      return true;
    }
    log('⚠️ 无响应，但进程存在');
    
    // 进程存在但无响应，不计数为失败，只记录
    saveState();
    return true;
  } else {
    log('⚠️ 未运行');
  }
  
  // 需要重启
  restarts++;
  consecutiveFailures++;
  
  log(`🔄 重启次数: ${restarts}, 连续失败: ${consecutiveFailures}`);
  
  // 检查是否需要恢复配置
  if (consecutiveFailures > CONFIG.maxRetries) {
    log(`⚠️ 连续失败超过 ${CONFIG.maxRetries} 次，尝试恢复配置...`);
    if (restoreConfig()) {
      consecutiveFailures = 0;
      log('✅ 配置已恢复，将使用上一个正常配置重新启动');
    } else {
      log('❌ 配置恢复失败，继续尝试当前配置');
    }
  }
  
  const success = await startGateway();
  
  // 如果启动成功，重置失败计数
  if (success) {
    consecutiveFailures = 0;
  }
  
  saveState();
  return success;
}

async function main() {
  log('========== OpenClaw 守护进程启动 ==========');
  
  // 确保备份目录存在
  if (!fs.existsSync(CONFIG.backupDir)) {
    fs.mkdirSync(CONFIG.backupDir, { recursive: true });
  }
  
  // 加载配置（必须先运行 setup.js）
  if (!loadConfig()) {
    log('请先运行 setup.js 配置后再启动守护进程。');
    process.exit(1);
  }
  
  // 加载之前的状态
  loadState();
  
  // 首次检查
  await check();
  
  // 定期检查
  setInterval(async () => {
    await check();
  }, runtimeConfig.checkInterval);
  
  // 保持运行
  log('守护进程运行中...（每 ' + (runtimeConfig.checkInterval/1000) + ' 秒检查一次）');
}

main().catch(err => {
  log(`❌ 守护进程错误: ${err.message}`);
  process.exit(1);
});

/**
 * OpenClaw 进程守护脚本（改进版）
 * 功能：
 * 1. 监控 Gateway 状态
 * 2. 连续启动失败时自动恢复上一个备份的配置
 */

const { exec, spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const CONFIG = {
  checkInterval: 10000,       // 10秒检查一次
  gatewayPort: null,          // 从配置文件读取
  gatewayPath: 'C:\\Users\\visio\\AppData\\Roaming\\npm\\node_modules\\openclaw\\openclaw.mjs',
  logFile: path.join(__dirname, 'guardian-log.txt'),
  stateFile: path.join(__dirname, 'guardian-state.json'),
  configFile: 'C:\\Users\\visio\\.openclaw\\openclaw.json',
  backupDir: 'C:\\Users\\visio\\.openclaw\\backups',
  maxRetries: 3,             // 连续失败超过此次数则恢复配置
};

/**
 * 从配置文件读取 Gateway 端口
 */
function getGatewayPortFromConfig() {
  try {
    if (!fs.existsSync(CONFIG.configFile)) {
      log('⚠️ 配置文件不存在，使用默认端口 18789');
      return 18789;
    }
    
    const config = JSON.parse(fs.readFileSync(CONFIG.configFile, 'utf-8'));
    const port = config?.gateway?.port;
    
    if (port && typeof port === 'number' && port > 0 && port < 65536) {
      log(`📋 从配置文件读取端口: ${port}`);
      return port;
    } else {
      log('⚠️ 配置文件中端口无效，使用默认端口 18789');
      return 18789;
    }
  } catch (err) {
    log(`⚠️ 读取配置文件失败: ${err.message}，使用默认端口 18789`);
    return 18789;
  }
}

let restarts = 0;
let consecutiveFailures = 0;

function log(msg) {
  const line = `[${new Date().toLocaleString()}] ${msg}\n`;
  fs.appendFileSync(CONFIG.logFile, line);
  console.log(line);
}

function getGatewayPid() {
  const port = getGatewayPortFromConfig();
  return new Promise((resolve) => {
    const cmd = 'powershell -Command "Get-NetTCPConnection -LocalPort ' + port + ' -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty OwningProcess"';
    exec(cmd, (err, stdout) => {
      const pid = parseInt(stdout.trim());
      resolve(isNaN(pid) ? null : pid);
    });
  });
}

function isGatewayHealthy() {
  const port = getGatewayPortFromConfig();
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
  // 每次启动时从配置文件读取端口
  const port = getGatewayPortFromConfig();
  
  log(`🚀 启动 Gateway (端口: ${port})...`);
  
  return new Promise((resolve) => {
    const proc = spawn('node', [
      CONFIG.gatewayPath, 
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
    
    // 等待 8 秒后检查
    setTimeout(async () => {
      const pid = await getGatewayPid();
      if (pid) {
        log(`✅ Gateway 已启动，PID: ${pid}`);
        resolve(true);
      } else {
        log('❌ 启动失败');
        resolve(false);
      }
    }, 8000);
  });
}

async function check() {
  log(`--- 检查 ---`);
  
  const pid = await getGatewayPid();
  
  if (pid) {
    const healthy = await isGatewayHealthy();
    if (healthy) {
      log('✅ 正常');
      consecutiveFailures = 0;
      saveState();
      return true;
    }
    log('⚠️ 无响应');
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
  log('========== 守护进程启动 ==========');
  
  // 确保备份目录存在
  if (!fs.existsSync(CONFIG.backupDir)) {
    fs.mkdirSync(CONFIG.backupDir, { recursive: true });
  }
  
  // 加载之前的状态
  loadState();
  
  // 首次检查
  await check();
  
  // 定期检查
  setInterval(async () => {
    await check();
  }, CONFIG.checkInterval);
  
  // 保持运行
  log('守护进程运行中...');
}

main().catch(err => {
  log(`❌ 守护进程错误: ${err.message}`);
  process.exit(1);
});

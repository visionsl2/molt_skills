/**
 * OpenClaw 配置管理脚本
 * 功能：
 * 1. 在修改配置前自动备份当前配置
 * 2. 提供安全的配置更新接口
 */

const fs = require('fs');
const path = require('path');

const CONFIG_PATH = 'C:\\Users\\visio\\.openclaw\\openclaw.json';
const BACKUP_DIR = 'C:\\Users\\visio\\.openclaw\\backups';

/**
 * 备份配置文件
 */
function backupConfig() {
  try {
    if (!fs.existsSync(CONFIG_PATH)) {
      console.log('⚠️ 配置文件不存在，跳过备份');
      return false;
    }
    
    // 确保备份目录存在
    if (!fs.existsSync(BACKUP_DIR)) {
      fs.mkdirSync(BACKUP_DIR, { recursive: true });
    }
    
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const backupFile = path.join(BACKUP_DIR, `openclaw.json.bak.${timestamp}`);
    
    fs.copyFileSync(CONFIG_PATH, backupFile);
    console.log(`📦 已备份配置: ${backupFile}`);
    
    // 只保留最近 5 个备份
    cleanupOldBackups(5);
    
    return true;
  } catch (err) {
    console.log(`❌ 备份失败: ${err.message}`);
    return false;
  }
}

/**
 * 清理旧备份，只保留最近的 N 个
 */
function cleanupOldBackups(keepCount) {
  try {
    const files = fs.readdirSync(BACKUP_DIR)
      .filter(f => f.startsWith('openclaw.json.bak.'))
      .map(f => ({
        name: f,
        path: path.join(BACKUP_DIR, f),
        mtime: fs.statSync(path.join(BACKUP_DIR, f)).mtime.getTime()
      }))
      .sort((a, b) => b.mtime - a.mtime);
    
    // 删除多余的旧备份
    if (files.length > keepCount) {
      files.slice(keepCount).forEach(f => {
        fs.unlinkSync(f.path);
        console.log(`🗑️ 已删除旧备份: ${f.name}`);
      });
    }
  } catch (err) {
    console.log(`⚠️ 清理旧备份失败: ${err.message}`);
  }
}

/**
 * 安全地更新配置（先备份再更新）
 */
function updateConfig(newConfig) {
  try {
    // 先备份当前配置
    if (!backupConfig()) {
      console.log('❌ 无法备份配置，取消更新');
      return false;
    }
    
    // 写入新配置
    fs.writeFileSync(CONFIG_PATH, JSON.stringify(newConfig, null, 2));
    console.log(`✅ 配置已更新: ${CONFIG_PATH}`);
    
    return true;
  } catch (err) {
    console.log(`❌ 更新配置失败: ${err.message}`);
    return false;
  }
}

/**
 * 应用配置补丁（先备份再应用）
 */
function patchConfig(patch) {
  try {
    if (!fs.existsSync(CONFIG_PATH)) {
      console.log('❌ 配置文件不存在');
      return false;
    }
    
    // 读取当前配置
    const currentConfig = JSON.parse(fs.readFileSync(CONFIG_PATH, 'utf-8'));
    
    // 应用补丁
    const updatedConfig = mergeDeep(currentConfig, patch);
    
    // 先备份再更新
    if (!backupConfig()) {
      console.log('❌ 无法备份配置，取消更新');
      return false;
    }
    
    // 写入更新后的配置
    fs.writeFileSync(CONFIG_PATH, JSON.stringify(updatedConfig, null, 2));
    console.log(`✅ 配置补丁已应用: ${CONFIG_PATH}`);
    
    return true;
  } catch (err) {
    console.log(`❌ 应用配置补丁失败: ${err.message}`);
    return false;
  }
}

/**
 * 深度合并对象
 */
function mergeDeep(target, source) {
  const output = { ...target };
  
  if (isObject(target) && isObject(source)) {
    Object.keys(source).forEach(key => {
      if (isObject(source[key])) {
        if (!(key in target)) {
          Object.assign(output, { [key]: source[key] });
        } else {
          output[key] = mergeDeep(target[key], source[key]);
        }
      } else {
        Object.assign(output, { [key]: source[key] });
      }
    });
  }
  
  return output;
}

function isObject(item) {
  return (item && typeof item === 'object' && !Array.isArray(item));
}

// 命令行接口
if (require.main === module) {
  const args = process.argv.slice(2);
  
  if (args.length === 0) {
    console.log('Usage:');
    console.log('  node config-manager.js backup                    # 备份当前配置');
    console.log('  node config-manager.js update <file>             # 从文件更新整个配置');
    console.log('  node config-manager.js patch <file>              # 从文件应用配置补丁');
    console.log('  node config-manager.js restore <backup-file>     # 恢复特定备份');
    process.exit(1);
  }
  
  const command = args[0];
  
  switch (command) {
    case 'backup':
      backupConfig();
      break;
      
    case 'update':
      if (args[1]) {
        const newConfig = JSON.parse(fs.readFileSync(args[1], 'utf-8'));
        updateConfig(newConfig);
      } else {
        console.log('❌ 请提供配置文件路径');
        process.exit(1);
      }
      break;
      
    case 'patch':
      if (args[1]) {
        const patch = JSON.parse(fs.readFileSync(args[1], 'utf-8'));
        patchConfig(patch);
      } else {
        console.log('❌ 请提供补丁文件路径');
        process.exit(1);
      }
      break;
      
    case 'restore':
      if (args[1]) {
        const backupFile = args[1];
        if (fs.existsSync(backupFile)) {
          fs.copyFileSync(backupFile, CONFIG_PATH);
          console.log(`✅ 已恢复配置: ${backupFile}`);
        } else {
          console.log(`❌ 备份文件不存在: ${backupFile}`);
          process.exit(1);
        }
      } else {
        console.log('❌ 请提供备份文件路径');
        process.exit(1);
      }
      break;
      
    default:
      console.log(`❌ 未知命令: ${command}`);
      process.exit(1);
  }
}

module.exports = {
  backupConfig,
  updateConfig,
  patchConfig,
  mergeDeep
};
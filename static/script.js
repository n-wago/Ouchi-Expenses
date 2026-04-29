// ========================================
// OUCHI-EXPENSES - Common JavaScript
// ========================================

// グローバル設定
const APP_CONFIG = {
    apiTimeout: 30000,  // 30秒
    maxFileSize: 16 * 1024 * 1024,  // 16MB
    allowedImageTypes: ['image/jpeg', 'image/png', 'image/gif', 'image/bmp']
};

// ========================================
// ユーティリティ関数
// ========================================

/**
 * 日付をフォーマット
 * @param {Date} date
 * @param {string} format - 'yyyy-mm-dd' または 'yyyy-mm-dd HH:mm'
 * @returns {string}
 */
function formatDate(date, format = 'yyyy-mm-dd') {
    if (!(date instanceof Date)) {
        date = new Date(date);
    }

    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');

    if (format === 'yyyy-mm-dd HH:mm') {
        return `${year}-${month}-${day} ${hours}:${minutes}`;
    }
    return `${year}-${month}-${day}`;
}

/**
 * 数値をフォーマット（通貨）
 * @param {number} value
 * @returns {string}
 */
function formatCurrency(value) {
    return new Intl.NumberFormat('ja-JP', {
        style: 'currency',
        currency: 'JPY'
    }).format(value);
}

/**
 * ファイルサイズをフォーマット
 * @param {number} bytes
 * @returns {string}
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

/**
 * ファイル検証
 * @param {File} file
 * @returns {Object} { valid: boolean, error: string }
 */
function validateFile(file) {
    if (!file) {
        return { valid: false, error: 'ファイルが選択されていません' };
    }

    if (!APP_CONFIG.allowedImageTypes.includes(file.type)) {
        return {
            valid: false,
            error: 'JPG、PNG、GIF、BMP のみアップロード可能です'
        };
    }

    if (file.size > APP_CONFIG.maxFileSize) {
        return {
            valid: false,
            error: `ファイルサイズが大きすぎます（最大: ${formatFileSize(APP_CONFIG.maxFileSize)}）`
        };
    }

    return { valid: true };
}

/**
 * Toast通知を表示
 * @param {string} message
 * @param {string} type - 'success', 'error', 'warning', 'info'
 * @param {number} duration - 表示時間（ミリ秒）
 */
function showToast(message, type = 'info', duration = 3000) {
    const toastContainer = document.getElementById('toastContainer') || createToastContainer();

    const toast = document.createElement('div');
    toast.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show`;
    toast.role = 'alert';
    toast.innerHTML = `
        <i class="bi bi-${getIconForType(type)}"></i> ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    toastContainer.appendChild(toast);

    // 自動消去
    setTimeout(() => {
        toast.remove();
    }, duration);
}

/**
 * Toast表示用のコンテナを作成
 */
function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toastContainer';
    container.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 9999;
        max-width: 400px;
    `;
    document.body.appendChild(container);
    return container;
}

/**
 * 型に応じたアイコンを取得
 */
function getIconForType(type) {
    const icons = {
        'success': 'check-circle-fill',
        'error': 'exclamation-circle-fill',
        'warning': 'exclamation-triangle-fill',
        'info': 'info-circle-fill'
    };
    return icons[type] || 'info-circle-fill';
}

/**
 * ローディングスピナーを表示
 * @param {HTMLElement} container
 */
function showLoading(container) {
    container.innerHTML = `
        <div class="text-center py-5">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">読み込み中...</span>
            </div>
            <p class="mt-2 text-muted">読み込み中...</p>
        </div>
    `;
}

/**
 * エラーメッセージを表示
 * @param {HTMLElement} container
 * @param {string} message
 */
function showError(container, message) {
    container.innerHTML = `
        <div class="alert alert-danger">
            <i class="bi bi-exclamation-circle"></i> ${message}
        </div>
    `;
}

// ========================================
// イベントリスナー
// ========================================

document.addEventListener('DOMContentLoaded', function() {
    // Bootstrapツールチップを初期化
    initializeTooltips();

    // Bootstrapポップオーバーを初期化
    initializePopovers();
});

/**
 * ツールチップを初期化
 */
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(tooltipTriggerEl => {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * ポップオーバーを初期化
 */
function initializePopovers() {
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(popoverTriggerEl => {
        return new bootstrap.Popover(popoverTriggerEl);
    });
}

// ========================================
// API呼び出し関数
// ========================================

/**
 * API呼び出しのラッパー
 * @param {string} url
 * @param {Object} options
 * @returns {Promise}
 */
async function apiCall(url, options = {}) {
    const defaultOptions = {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        },
        timeout: APP_CONFIG.apiTimeout
    };

    const finalOptions = { ...defaultOptions, ...options };

    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), finalOptions.timeout);

        const response = await fetch(url, {
            ...finalOptions,
            signal: controller.signal
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
            throw new Error(`HTTP Error: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error('API呼び出しエラー:', error);
        throw error;
    }
}

// ========================================
// モバイル対応関数
// ========================================

/**
 * デバイスがモバイルか判定
 * @returns {boolean}
 */
function isMobileDevice() {
    return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
}

/**
 * iPhoneか判定
 * @returns {boolean}
 */
function isIphone() {
    return /iPhone/.test(navigator.userAgent);
}

/**
 * Androidか判定
 * @returns {boolean}
 */
function isAndroid() {
    return /Android/.test(navigator.userAgent);
}

// ========================================
// ローカルストレージ関数
// ========================================

/**
 * ローカルストレージにデータを保存
 * @param {string} key
 * @param {*} value
 */
function setStorage(key, value) {
    try {
        localStorage.setItem(key, JSON.stringify(value));
    } catch (error) {
        console.error('ストレージ保存エラー:', error);
    }
}

/**
 * ローカルストレージからデータを取得
 * @param {string} key
 * @returns {*}
 */
function getStorage(key) {
    try {
        const value = localStorage.getItem(key);
        return value ? JSON.parse(value) : null;
    } catch (error) {
        console.error('ストレージ取得エラー:', error);
        return null;
    }
}

/**
 * ローカルストレージからデータを削除
 * @param {string} key
 */
function removeStorage(key) {
    try {
        localStorage.removeItem(key);
    } catch (error) {
        console.error('ストレージ削除エラー:', error);
    }
}

// ========================================
// デバッグ用ログ関数
// ========================================

const DEBUG = true;

function debugLog(message, data = null) {
    if (DEBUG) {
        console.log(`[DEBUG] ${message}`, data || '');
    }
}

function debugError(message, error = null) {
    if (DEBUG) {
        console.error(`[ERROR] ${message}`, error || '');
    }
}

function debugWarn(message, data = null) {
    if (DEBUG) {
        console.warn(`[WARN] ${message}`, data || '');
    }
}

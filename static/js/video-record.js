/**
 * video-record.js — 摄像头视频录制 + IndexedDB 存储
 * ========================================================
 * 功能：
 *   1. 请求摄像头权限，显示预览画面
 *   2. MediaRecorder 录制视频（webm 格式）
 *   3. 录制完成后存入 IndexedDB（不上传服务器）
 *   4. 结果页从 IndexedDB 读取并回放
 *   5. 提供"立即删除"按钮
 *
 * 隐私保护：
 *   - 所有视频数据仅存储在浏览器端 IndexedDB
 *   - 不出现在 HTTP 请求中
 *   - 提供删除功能
 *
 * 用法：
 *   VideoRecorder.init({ containerId: 'video-preview', conversationId: 'xxx' });
 *   VideoRecorder.start();   // 开始录制
 *   VideoRecorder.stop();    // 停止录制，自动保存
 *   VideoRecorder.destroy(); // 释放摄像头
 *
 *   结果页：
 *   VideoRecorder.playback('conversationId', containerEl);
 *   VideoRecorder.deleteRecording('conversationId');
 * ======================================================== */
;(function (root) {
  'use strict';

  /* ========== IndexedDB 存储 ========== */

  var DB_NAME = 'VideoRecordings';
  var DB_VERSION = 1;
  var STORE_NAME = 'videos';

  function _openDB() {
    return new Promise(function (resolve, reject) {
      var req = indexedDB.open(DB_NAME, DB_VERSION);
      req.onupgradeneeded = function (e) {
        var db = e.target.result;
        if (!db.objectStoreNames.contains(STORE_NAME)) {
          db.createObjectStore(STORE_NAME);
        }
      };
      req.onsuccess = function (e) { resolve(e.target.result); };
      req.onerror = function (e) { reject(e.target.error); };
    });
  }

  function _dbSave(key, blob) {
    return _openDB().then(function (db) {
      return new Promise(function (resolve, reject) {
        var tx = db.transaction(STORE_NAME, 'readwrite');
        tx.objectStore(STORE_NAME).put(blob, key);
        tx.oncomplete = function () { resolve(); db.close(); };
        tx.onerror = function (e) { reject(e.target.error); db.close(); };
      });
    });
  }

  function _dbLoad(key) {
    return _openDB().then(function (db) {
      return new Promise(function (resolve, reject) {
        var tx = db.transaction(STORE_NAME, 'readonly');
        var req = tx.objectStore(STORE_NAME).get(key);
        req.onsuccess = function () {
          resolve(req.result || null);
          db.close();
        };
        req.onerror = function (e) {
          reject(e.target.error);
          db.close();
        };
      });
    });
  }

  function _dbDelete(key) {
    return _openDB().then(function (db) {
      return new Promise(function (resolve, reject) {
        var tx = db.transaction(STORE_NAME, 'readwrite');
        tx.objectStore(STORE_NAME).delete(key);
        tx.oncomplete = function () { resolve(); db.close(); };
        tx.onerror = function (e) { reject(e.target.error); db.close(); };
      });
    });
  }

  function _dbHas(key) {
    return _openDB().then(function (db) {
      return new Promise(function (resolve, reject) {
        var tx = db.transaction(STORE_NAME, 'readonly');
        var req = tx.objectStore(STORE_NAME).count(key);
        req.onsuccess = function () {
          resolve(req.result > 0);
          db.close();
        };
        req.onerror = function (e) {
          reject(e.target.error);
          db.close();
        };
      });
    });
  }

  /* ========== MIME 类型检测 ========== */

  function _getSupportedMimeType() {
    var types = [
      'video/webm;codecs=vp9,opus',
      'video/webm;codecs=vp8,opus',
      'video/webm',
      'video/mp4',
    ];
    for (var i = 0; i < types.length; i++) {
      if (MediaRecorder.isTypeSupported(types[i])) {
        return types[i];
      }
    }
    return 'video/webm'; // fallback
  }

  /* ========== 录制状态 ========== */

  var _state = 'idle'; // idle | preview | recording | stopped
  var _stream = null;
  var _recorder = null;
  var _chunks = [];
  var _startTime = 0;
  var _timerId = null;
  var _containerId = 'video-preview';
  var _conversationId = '';
  var _onStateChange = null;

  /* ========== 主对象 ========== */

  var VideoRecorder = {

    /* -------- 初始化 -------- */

    init: function (opts) {
      opts = opts || {};
      _containerId = opts.containerId || 'video-preview';
      _conversationId = opts.conversationId || '';
      _onStateChange = opts.onStateChange || null;
      _state = 'idle';
      _chunks = [];
    },

    /* -------- 获取状态 -------- */

    getState: function () {
      return _state;
    },

    getConversationId: function () {
      return _conversationId;
    },

    /* -------- 请求摄像头 + 预览 -------- */

    startPreview: function () {
      var self = this;
      if (_state === 'preview' || _state === 'recording') {
        return Promise.resolve();
      }

      // 如果已经有流，直接显示预览
      if (_stream) {
        self._attachStream();
        _state = 'preview';
        self._emitState();
        return Promise.resolve();
      }

      return navigator.mediaDevices
        .getUserMedia({
          video: {
            width: { ideal: 640 },
            height: { ideal: 480 },
            facingMode: 'user',
          },
          audio: true,
        })
        .then(function (stream) {
          _stream = stream;
          _state = 'preview';
          self._attachStream();
          self._emitState();
        })
        .catch(function (err) {
          console.warn('[VideoRecorder] Camera denied:', err.message);
          _state = 'idle';
          self._emitState();
          return Promise.reject(err);
        });
    },

    /* -------- 开始录制 -------- */

    start: function (conversationId) {
      var self = this;
      if (_state === 'recording') return;

      if (conversationId) {
        _conversationId = conversationId;
      }

      if (!_stream) {
        // 先请求摄像头再录制
        return this.startPreview().then(function () {
          return self._beginRecording();
        });
      }

      return this._beginRecording();
    },

    _beginRecording: function () {
      var self = this;
      _chunks = [];

      var mimeType = _getSupportedMimeType();
      try {
        _recorder = new MediaRecorder(_stream, {
          mimeType: mimeType,
          videoBitsPerSecond: 1000000, // 1 Mbps
        });
      } catch (e) {
        _recorder = new MediaRecorder(_stream);
      }

      _recorder.ondataavailable = function (e) {
        if (e.data && e.data.size > 0) {
          _chunks.push(e.data);
        }
      };

      _recorder.onstop = function () {
        var blob = new Blob(_chunks, { type: mimeType });
        _state = 'stopped';
        self._emitState();

        // 存入 IndexedDB
        if (_conversationId) {
          _dbSave(_conversationId, blob).catch(function (err) {
            console.warn('[VideoRecorder] DB save failed:', err);
          });
        }

        self._updateTimerDisplay();
      };

      _recorder.start(1000); // 每秒收集数据
      _startTime = Date.now();
      _state = 'recording';
      this._startTimer();
      this._emitState();
      this._updateUI('recording');

      return Promise.resolve();
    },

    /* -------- 停止录制 -------- */

    stop: function () {
      if (_state !== 'recording') return Promise.resolve(null);

      return new Promise(function (resolve) {
        var recorder = _recorder;

        // 等 onstop 回调执行
        recorder.onstop = function () {
          var blob = new Blob(_chunks, { type: recorder.mimeType || 'video/webm' });
          _state = 'stopped';

          if (_conversationId) {
            _dbSave(_conversationId, blob).catch(function (err) {
              console.warn('[VideoRecorder] DB save failed:', err);
            });
          }

          VideoRecorder._stopTimer();
          VideoRecorder._updateTimerDisplay();
          VideoRecorder._emitState();
          VideoRecorder._updateUI('stopped');
          resolve(blob);
        };

        recorder.stop();
        // 不停止 stream，保留预览画面
      });
    },

    /* -------- 释放摄像头 -------- */

    destroy: function () {
      this._stopTimer();
      if (_recorder && _recorder.state !== 'inactive') {
        try { _recorder.stop(); } catch (_) {}
      }
      _recorder = null;

      if (_stream) {
        _stream.getTracks().forEach(function (t) { t.stop(); });
        _stream = null;
      }

      _chunks = [];
      _state = 'idle';
      _startTime = 0;
      this._updateUI('idle');
      this._emitState();

      // 清空容器
      var container = document.getElementById(_containerId);
      if (container) container.innerHTML = '';
    },

    /* -------- 删除录制 -------- */

    deleteRecording: function (conversationId) {
      var key = conversationId || _conversationId;
      if (!key) return Promise.resolve();
      return _dbDelete(key).then(function () {
        console.log('[VideoRecorder] Recording deleted:', key);
      });
    },

    /* -------- 检查是否有录制 -------- */

    hasRecording: function (conversationId) {
      return _dbHas(conversationId);
    },

    /* -------- 结果页回放 -------- */

    playback: function (conversationId, containerEl) {
      if (!containerEl) {
        containerEl = document.getElementById('video-playback');
      }
      if (!containerEl) return Promise.reject(new Error('No container'));

      return _dbLoad(conversationId).then(function (blob) {
        if (!blob) {
          containerEl.innerHTML =
            '<div class="video-empty">暂无录制视频</div>';
          return null;
        }

        var url = URL.createObjectURL(blob);
        containerEl.innerHTML =
          '<div class="video-player-wrapper">' +
            '<video class="video-player" controls autoplay playsinline src="' + url + '"></video>' +
          '</div>' +
          '<div class="video-actions">' +
            '<button class="btn btn-outline btn-delete-video" data-conversation="' + conversationId + '">🗑️ 删除录制</button>' +
          '</div>';

        // 绑定删除按钮
        var delBtn = containerEl.querySelector('.btn-delete-video');
        if (delBtn) {
          delBtn.addEventListener('click', function () {
            if (confirm('确定要删除此录制视频吗？视频仅存在本地，删除后无法恢复。')) {
              _dbDelete(conversationId).then(function () {
                containerEl.innerHTML =
                  '<div class="video-empty">视频已删除</div>';
              });
            }
          });
        }

        return url;
      });
    },

    /* ========== 内部方法 ========== */

    _attachStream: function () {
      var container = document.getElementById(_containerId);
      if (!container) return;

      // 如果已经有 video 元素，直接使用
      var video = container.querySelector('.video-preview-element');
      if (!video) {
        container.innerHTML = '';
        video = document.createElement('video');
        video.className = 'video-preview-element';
        video.setAttribute('autoplay', '');
        video.setAttribute('playsinline', '');
        video.setAttribute('muted', ''); // 避免回音
        container.appendChild(video);
      }

      video.srcObject = _stream;

      // 确保容器可见
      container.classList.remove('video-hidden');
      container.classList.add('video-active');
    },

    _startTimer: function () {
      this._stopTimer();
      var self = this;
      _timerId = setInterval(function () {
        self._updateTimerDisplay();
      }, 500);
    },

    _stopTimer: function () {
      if (_timerId) {
        clearInterval(_timerId);
        _timerId = null;
      }
    },

    _updateTimerDisplay: function () {
      var el = document.getElementById('video-recording-timer');
      if (!el) return;

      if (_state === 'recording') {
        var elapsed = Math.floor((Date.now() - _startTime) / 1000);
        var min = String(Math.floor(elapsed / 60)).padStart(2, '0');
        var sec = String(elapsed % 60).padStart(2, '0');
        el.textContent = min + ':' + sec;
        el.classList.add('active');
      } else {
        el.textContent = '00:00';
        el.classList.remove('active');
      }
    },

    _updateUI: function (state) {
      var container = document.getElementById(_containerId);
      if (!container) return;
      container.className = 'video-preview-container';

      if (state === 'recording') {
        container.classList.add('video-recording');
      } else if (state === 'preview') {
        container.classList.add('video-active');
      } else {
        container.classList.add('video-hidden');
      }

      // 录制按钮
      var toggleBtn = document.getElementById('video-toggle-btn');
      if (toggleBtn) {
        if (state === 'idle' || state === 'preview') {
          toggleBtn.textContent = '🎥 录制';
          toggleBtn.className = 'btn btn-secondary';
        } else if (state === 'recording') {
          toggleBtn.textContent = '⏹ 停止';
          toggleBtn.className = 'btn btn-danger';
        } else {
          toggleBtn.textContent = '🎥 录制';
          toggleBtn.className = 'btn btn-secondary';
          toggleBtn.disabled = false;
        }
      }

      // 隐私提示
      var privacyEl = document.getElementById('video-privacy-notice');
      if (privacyEl) {
        if (state === 'preview' || state === 'recording') {
          privacyEl.style.display = '';
        } else {
          privacyEl.style.display = 'none';
        }
      }
    },

    _emitState: function () {
      if (typeof _onStateChange === 'function') {
        _onStateChange(_state);
      }
    },
  };

  /* ========== 暴露到全局 ========== */

  root.VideoRecorder = VideoRecorder;
})(window);

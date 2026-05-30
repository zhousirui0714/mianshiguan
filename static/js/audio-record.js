/**
 * audio-record.js — 实时语音录制 + WebSocket 传输
 * ========================================================
 * 功能：
 *   1. AudioContext 捕获麦克风 PCM 音频
 *   2. 下采样至 16kHz 16bit mono（阿里云 STT 要求）
 *   3. 通过 SocketIO 实时发送音频流
 *   4. 音量波形可视化
 *   5. 平滑的 start/stop 控制
 *
 * 用法：
 *   AudioRecorder.init({
 *       socket: socketIO实例,
 *       onVisualData: function(level) {},  // 音量回调 0-100
 *       onStateChange: function(state) {}, // idle/listening/processing/error
 *   });
 *   AudioRecorder.start();   // 开始录音
 *   AudioRecorder.stop();    // 停止录音
 *   AudioRecorder.destroy(); // 释放资源
 * ======================================================== */
;(function (root) {
    'use strict';

    /* ========== 配置 ========== */
    var TARGET_SAMPLE_RATE = 16000; // 阿里云 STT 要求 16kHz
    var CHUNK_INTERVAL_MS = 200;    // 每 200ms 发送一个音频块
    var BUFFER_SIZE = 4096;         // ScriptProcessorNode 缓冲区

    /* ========== 状态 ========== */
    var state = {
        initialized: false,
        recording: false,
        stream: null,
        audioContext: null,
        source: null,
        processor: null,
        socket: null,
        onVisualData: null,
        onStateChange: null,
        chunkTimer: null,
        pcmBuffer: [],      // 累积的 PCM 数据
        volume: 0,
    };

    /* ========== 工具函数 ========== */

    /**
     * 将 Float32 音频数据下采样并转为 Int16 PCM
     * 输入: Float32Array (sampleRate Hz)
     * 输出: Int16Array (targetRate Hz)
     */
    function downsampleAndConvert(float32Data, inputSampleRate) {
        if (inputSampleRate === TARGET_SAMPLE_RATE) {
            // 直接转换
            var int16 = new Int16Array(float32Data.length);
            for (var i = 0; i < float32Data.length; i++) {
                var s = Math.max(-1, Math.min(1, float32Data[i]));
                int16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
            }
            return int16;
        }

        // 下采样
        var ratio = inputSampleRate / TARGET_SAMPLE_RATE;
        var newLength = Math.floor(float32Data.length / ratio);
        var int16 = new Int16Array(newLength);

        for (var i = 0; i < newLength; i++) {
            var srcIndex = Math.floor(i * ratio);
            var s = Math.max(-1, Math.min(1, float32Data[srcIndex]));
            int16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }
        return int16;
    }

    /** 计算音量等级 0-100 */
    function computeVolume(float32Data) {
        var sum = 0;
        for (var i = 0; i < float32Data.length; i++) {
            sum += float32Data[i] * float32Data[i];
        }
        var rms = Math.sqrt(sum / float32Data.length);
        return Math.min(100, Math.round(rms * 100));
    }

    /** 将 Int16Array 转为 ArrayBuffer (用于 WebSocket 发送) */
    function int16ToArrayBuffer(int16Data) {
        return int16Data.buffer.slice(
            int16Data.byteOffset,
            int16Data.byteOffset + int16Data.byteLength
        );
    }

    /* ========== 发送音频块 ========== */

    function flushPcmBuffer() {
        if (state.pcmBuffer.length === 0) return;

        // 合并所有 Int16Array
        var totalLen = state.pcmBuffer.reduce(function (sum, arr) {
            return sum + arr.length;
        }, 0);
        var merged = new Int16Array(totalLen);
        var offset = 0;
        for (var i = 0; i < state.pcmBuffer.length; i++) {
            merged.set(state.pcmBuffer[i], offset);
            offset += state.pcmBuffer[i].length;
        }
        state.pcmBuffer = [];

        // 通过 SocketIO 发送
        if (state.socket && state.socket.connected) {
            var buffer = int16ToArrayBuffer(merged);
            state.socket.emit('audio_data', buffer);
        }
    }

    /* ========== 主对象 ========== */

    var AudioRecorder = {

        /**
         * 初始化录音组件
         * @param {Object} opts
         * @param {Object} opts.socket       - SocketIO 实例
         * @param {Function} opts.onVisualData - 音量回调 (level: 0-100)
         * @param {Function} opts.onStateChange - 状态回调 (state: idle/listening/processing/error)
         */
        init: function (opts) {
            opts = opts || {};
            state.socket = opts.socket || null;
            state.onVisualData = opts.onVisualData || null;
            state.onStateChange = opts.onStateChange || null;
            state.initialized = true;
            state.recording = false;
            console.log('[AudioRecorder] initialized');
        },

        /**
         * 请求麦克风权限并开始录音
         */
        start: function () {
            if (state.recording) return;

            var self = this;

            navigator.mediaDevices.getUserMedia({ audio: true })
                .then(function (stream) {
                    state.stream = stream;
                    state.audioContext = new (window.AudioContext || window.webkitAudioContext)();
                    state.source = state.audioContext.createMediaStreamSource(stream);

                    // 创建 ScriptProcessorNode 处理 PCM 数据
                    state.processor = state.audioContext.createScriptProcessor(
                        BUFFER_SIZE, 1, 1
                    );

                    state.processor.onaudioprocess = function (event) {
                        if (!state.recording) return;

                        var inputData = event.inputBuffer.getChannelData(0);
                        var sampleRate = state.audioContext.sampleRate;

                        // 计算音量
                        var vol = computeVolume(inputData);
                        state.volume = vol;
                        if (state.onVisualData) {
                            state.onVisualData(vol);
                        }

                        // 下采样并转为 Int16 PCM
                        var pcmChunk = downsampleAndConvert(inputData, sampleRate);
                        state.pcmBuffer.push(pcmChunk);
                    };

                    state.source.connect(state.processor);
                    state.processor.connect(state.audioContext.destination);

                    state.recording = true;

                    // 定时发送 PCM 块
                    state.chunkTimer = setInterval(flushPcmBuffer, CHUNK_INTERVAL_MS);

                    // 通知 Socket 开始录音
                    if (state.socket && state.socket.connected) {
                        state.socket.emit('start_recording');
                    }

                    self._emitState('listening');
                    console.log('[AudioRecorder] recording started (sampleRate=' +
                                state.audioContext.sampleRate + 'Hz)');
                })
                .catch(function (err) {
                    console.error('[AudioRecorder] getUserMedia failed:', err);
                    self._emitState('error');
                    alert('无法访问麦克风，请检查权限设置。\n你可以使用文字输入模式继续。');
                });
        },

        /**
         * 停止录音
         */
        stop: function () {
            if (!state.recording) return;

            state.recording = false;

            // 清空剩余 PCM
            if (state.chunkTimer) {
                clearInterval(state.chunkTimer);
                state.chunkTimer = null;
            }
            flushPcmBuffer();

            // 通知 Socket 停止录音
            if (state.socket && state.socket.connected) {
                state.socket.emit('stop_recording');
            }

            // 释放音频资源
            if (state.processor) {
                state.processor.disconnect();
                state.processor = null;
            }
            if (state.source) {
                state.source.disconnect();
                state.source = null;
            }
            if (state.audioContext) {
                state.audioContext.close().catch(function () {});
                state.audioContext = null;
            }
            if (state.stream) {
                state.stream.getTracks().forEach(function (track) { track.stop(); });
                state.stream = null;
            }

            state.pcmBuffer = [];
            state.volume = 0;

            this._emitState('processing');
            console.log('[AudioRecorder] recording stopped');
        },

        /**
         * 释放所有资源
         */
        destroy: function () {
            if (state.recording) {
                this.stop();
            }
            state.socket = null;
            state.onVisualData = null;
            state.onStateChange = null;
            state.initialized = false;
        },

        /**
         * 检查是否正在录音
         */
        isRecording: function () {
            return state.recording;
        },

        /**
         * 获取当前音量 0-100
         */
        getVolume: function () {
            return state.volume;
        },

        /* ========== 内部 ========== */

        _emitState: function (s) {
            if (state.onStateChange) {
                state.onStateChange(s);
            }
        },
    };

    /* ========== 暴露到全局 ========== */

    root.AudioRecorder = AudioRecorder;

})(window);

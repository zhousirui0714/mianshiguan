"""
WebSocket 语音路由
===================
完整音频管道：
  前端 PCM 流 → SocketIO → Aliyun STT → DeepSeek LLM → Aliyun TTS → SocketIO → 前端播放

SocketIO 事件：
  客户端 → 服务端: start_recording, audio_data (binary), stop_recording, send_text (fallback)
  服务端 → 客户端: stt_partial, stt_final, tts_audio (binary), tts_end, error, examiner_text
"""

import json
import logging
import uuid
import time
from flask import request
from src.web import dependencies as deps
from src.services.speech_service import create_stt, create_tts

logger = logging.getLogger(__name__)

# ==================== 会话管理 ====================

# { sid: { "stt": AliyunSTT, "conversation_id": str, "user_id": str, ... } }
_voice_sessions = {}


def _get_sid():
    """获取当前 SocketIO 会话 ID"""
    try:
        from flask import session as flask_session
        return flask_session.get('sid', request.sid if request else 'unknown')
    except RuntimeError:
        return 'unknown'


def register_handlers(socketio):
    """注册所有 SocketIO 事件处理"""

    @socketio.on('connect')
    def handle_connect():
        sid = request.sid
        logger.info(f"[WS] 客户端已连接: {sid}")

    @socketio.on('disconnect')
    def handle_disconnect():
        sid = request.sid
        logger.info(f"[WS] 客户端断开: {sid}")
        _cleanup_session(sid)

    @socketio.on('start_recording')
    def handle_start_recording(data=None):
        """客户端开始录音 —— 初始化 STT 会话"""
        sid = request.sid
        logger.info(f"[WS] 开始录音: sid={sid}")

        # 清理旧会话
        _cleanup_session(sid)

        # 从 data 中获取 conversation_id 和 user_id
        conv_id = None
        user_id = 'anonymous'
        if isinstance(data, dict):
            conv_id = data.get('conversation_id')
            user_id = data.get('user_id', 'anonymous')

        # 创建 Aliyun STT 实例
        stt = create_stt()

        # 如果使用了 MockSTT（降级模式），静默切换到文字输入模式
        if stt.__class__.__name__ == 'MockSTT':
            logger.warning(f"[WS] STT 降级模式，使用文字输入: sid={sid}")
            socketio.emit('recording_started', {
                'message': '语音识别暂不可用，请使用文字输入',
                'degraded': True,
            }, room=sid)
            _voice_sessions[sid] = {
                'stt': stt,
                'conversation_id': conv_id,
                'user_id': user_id,
                'degraded': True,
            }
            return

        # 设置回调
        def on_partial(text):
            socketio.emit('stt_partial', {'text': text}, room=sid)

        def on_final(text):
            socketio.emit('stt_final', {'text': text}, room=sid)
            # 自动调用 LLM 并开始 TTS
            _handle_user_text(sid, text, socketio)

        def on_error(msg):
            logger.error(f"[WS] STT 错误: {msg}")
            socketio.emit('error', {'message': f'语音识别错误: {msg}'}, room=sid)

        stt.on_partial = on_partial
        stt.on_final = on_final
        stt.on_error = on_error

        # 启动 STT
        try:
            stt.start()
            _voice_sessions[sid] = {
                'stt': stt,
                'conversation_id': conv_id,
                'user_id': user_id,
                'degraded': False,
            }
            socketio.emit('recording_started', {'message': '录音已开始'}, room=sid)
        except Exception as e:
            logger.error(f"[WS] STT 启动失败: {e}")
            socketio.emit('error', {'message': f'语音识别启动失败: {str(e)}'}, room=sid)

    @socketio.on('audio_data')
    def handle_audio_data(data):
        """接收 PCM 音频数据并送入 STT"""
        sid = request.sid
        session = _voice_sessions.get(sid)
        if not session:
            return

        stt = session.get('stt')
        if not stt or stt.__class__.__name__ == 'MockSTT':
            return

        try:
            stt.send_audio(data)
        except Exception as e:
            logger.error(f"[WS] 音频数据处理错误: {e}")

    @socketio.on('stop_recording')
    def handle_stop_recording():
        """客户端停止录音 —— 结束 STT 会话"""
        sid = request.sid
        logger.info(f"[WS] 停止录音: sid={sid}")

        session = _voice_sessions.get(sid)
        if not session:
            return

        stt = session.get('stt')
        if stt:
            try:
                final_text = stt.stop()
                if final_text:
                    logger.info(f"[WS] STT 最终结果: {final_text[:50]}...")
                    # 如果 on_final 回调未触发，手动调用 LLM
                    if not session.get('llm_called'):
                        _handle_user_text(sid, final_text, socketio)
            except Exception as e:
                logger.error(f"[WS] STT 停止错误: {e}")

    @socketio.on('send_text')
    def handle_send_text(data):
        """文字输入（降级模式或双通道）"""
        sid = request.sid
        text = ''
        if isinstance(data, dict):
            text = data.get('text', '')
        elif isinstance(data, str):
            text = data

        if not text.strip():
            return

        logger.info(f"[WS] 文字输入: {text[:50]}...")
        _handle_user_text(sid, text, socketio)


def _handle_user_text(sid: str, text: str, socketio):
    """处理用户文本（来自 STT 或文字输入），调用 LLM 并 TTS 返回"""
    session = _voice_sessions.get(sid)
    if not session:
        return

    # 标记已调用 LLM，避免重复
    session['llm_called'] = True

    conv_id = session.get('conversation_id')
    user_id = session.get('user_id', 'anonymous')

    try:
        # 1. 收集对话历史
        history = []
        if conv_id:
            conv = deps.db.get_conversation(conv_id)
            if conv:
                history = [
                    {'role': m['role'], 'content': m['content']}
                    for m in conv.get('messages', [])
                ]

        # 2. 保存用户消息
        if conv_id:
            deps.db.add_message(conv_id, 'user', text)

        # 3. 调用 DeepSeek LLM
        socketio.emit('llm_thinking', {}, room=sid)
        ai_response = deps.llm_client.examiner_chat(
            scenario_id='ielts_speaking',
            user_message=text,
            conversation_history=history,
            user_background=session.get('user_background', ''),
        )

        if not ai_response:
            ai_response = "I'm sorry, could you please repeat that?"

        # 4. 保存 AI 回复
        if conv_id:
            deps.db.add_message(conv_id, 'assistant', ai_response)

        # 5. 发送文字到前端（先于语音，让用户先看到文字）
        socketio.emit('examiner_text', {'text': ai_response}, room=sid)

        # 6. 调用 TTS 合成语音并发回
        tts = create_tts()
        if tts.__class__.__name__ == 'MockTTS':
            # 降级模式：只发送文字
            socketio.emit('tts_end', {}, room=sid)
            return

        # 流式 TTS
        audio_chunks = []

        def on_chunk(chunk):
            audio_chunks.append(chunk)
            socketio.emit('tts_audio', chunk, room=sid)

        def on_complete():
            socketio.emit('tts_end', {'total_bytes': sum(len(c) for c in audio_chunks)}, room=sid)
            logger.info(f"[WS] TTS 完成: {len(ai_response)}字 → {sum(len(c) for c in audio_chunks)}字节")

        tts.on_audio_chunk = on_chunk
        tts.on_complete = on_complete

        try:
            tts.synthesize_stream(ai_response)
        except Exception as e:
            logger.error(f"[WS] TTS 合成错误: {e}")
            socketio.emit('error', {'message': '语音合成失败'}, room=sid)

    except Exception as e:
        logger.error(f"[WS] LLM/TTS 处理错误: {e}")
        socketio.emit('error', {'message': f'处理失败: {str(e)}'}, room=sid)
        socketio.emit('examiner_text', {
            'text': "Sorry, I encountered an error. Please try again."
        }, room=sid)
    finally:
        # 允许下一次对话
        session['llm_called'] = False


def _cleanup_session(sid: str):
    """清理会话资源"""
    session = _voice_sessions.pop(sid, None)
    if session:
        stt = session.get('stt')
        if stt:
            try:
                stt.stop()
            except Exception:
                pass
        logger.info(f"[WS] 会话已清理: {sid}")

"""
阿里云智能语音服务封装（适配 nls SDK v1.0.0）

提供：
- AliyunSTT：语音识别（Streaming ASR，PCM 16kHz 16bit mono）
- AliyunTTS：语音合成（英文语音，PCM 16kHz 16bit mono）

配置（.env）：
  ALIYUN_ACCESS_KEY=你的AccessKey ID
  ALIYUN_SECRET_KEY=你的AccessKey Secret
  ALIYUN_APP_KEY=你的AppKey
"""

import os
import json
import threading
import logging
from queue import Queue, Empty
from typing import Callable, Optional

logger = logging.getLogger(__name__)

# 尝试导入阿里云 SDK v1.0.0
try:
    from nls import NlsSpeechTranscriber, NlsSpeechSynthesizer
    from nls import token as nls_token
    HAS_ALIYUN_SDK = True
except ImportError:
    HAS_ALIYUN_SDK = False
    NlsSpeechTranscriber = None
    NlsSpeechSynthesizer = None
    nls_token = None
    logger.warning("[Speech] nls SDK 未安装，将使用降级模式")


# ==================== 配置 ====================

ALIYUN_ACCESS_KEY = os.getenv("ALIYUN_ACCESS_KEY", "")
ALIYUN_SECRET_KEY = os.getenv("ALIYUN_SECRET_KEY", "")
ALIYUN_APP_KEY = os.getenv("ALIYUN_APP_KEY", "")
ALIYUN_GATEWAY = "wss://nls-gateway.cn-shanghai.aliyuncs.com/ws/v1"

# TTS 语音配置
TTS_VOICE = "Emma"  # 英式英语女声
TTS_SPEED = 0
TTS_VOLUME = 50


# ==================== 工具函数 ====================

_token_cache = None
_token_lock = threading.Lock()


def _get_token() -> Optional[str]:
    """获取阿里云 Token（带缓存）"""
    global _token_cache
    if _token_cache:
        return _token_cache
    with _token_lock:
        if _token_cache:
            return _token_cache
        try:
            _token_cache = nls_token.getToken(ALIYUN_ACCESS_KEY, ALIYUN_SECRET_KEY)
            logger.info("[Token] 获取成功")
            return _token_cache
        except Exception as e:
            logger.error(f"[Token] 获取失败: {e}")
            return None


# ==================== STT ====================

class AliyunSTT:
    """阿里云实时语音识别（流式 ASR）

    用法：
        stt = AliyunSTT()
        stt.start(on_result=my_callback)
        stt.send_audio(pcm_bytes)   # 循环调用
        stt.stop()
    """

    def __init__(self, app_key: str = "", access_key: str = "",
                 secret_key: str = ""):
        self.app_key = app_key or ALIYUN_APP_KEY
        self.access_key = access_key or ALIYUN_ACCESS_KEY
        self.secret_key = secret_key or ALIYUN_SECRET_KEY
        self._transcriber = None
        self._running = False
        self._final_result = ""
        self._partial_result = ""

        # 回调
        self.on_partial: Optional[Callable[[str], None]] = None
        self.on_final: Optional[Callable[[str], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None
        self.on_state_change: Optional[Callable[[str], None]] = None

    def start(self):
        """启动 STT 会话"""
        if not HAS_ALIYUN_SDK:
            self._state("degraded")
            logger.warning("[STT] SDK 未安装，使用降级模式")
            return

        if not self.app_key or not self.access_key or not self.secret_key:
            raise ValueError("阿里云语音配置不完整，请检查 .env 文件")

        self._final_result = ""
        self._partial_result = ""

        # 获取 Token
        tok = _get_token()
        if not tok:
            raise RuntimeError("无法获取阿里云语音 Token，请检查 AccessKey")

        self._transcriber = NlsSpeechTranscriber(
            url=ALIYUN_GATEWAY,
            token=tok,
            appkey=self.app_key,
            on_start=self._on_start,
            on_result_changed=self._on_result_changed,
            on_sentence_begin=self._on_sentence_begin,
            on_sentence_end=self._on_sentence_end,
            on_completed=self._on_completed,
            on_error=self._on_error,
            on_close=self._on_close,
        )

        self._running = True
        self._transcriber.start(
            aformat="pcm",
            sample_rate=16000,
            ch=1,
            enable_intermediate_result=True,
            enable_punctuation_prediction=True,
            enable_inverse_text_normalization=True,
        )
        self._state("listening")
        logger.info("[STT] 语音识别会话已启动")

    def send_audio(self, data: bytes):
        """发送音频数据（PCM 16kHz 16bit mono）"""
        if not self._running:
            return
        if HAS_ALIYUN_SDK and self._transcriber:
            self._transcriber.send_audio(data)

    def stop(self) -> str:
        """停止 STT 会话，返回最终识别结果"""
        self._running = False
        if HAS_ALIYUN_SDK and self._transcriber:
            try:
                self._transcriber.stop()
            except Exception as e:
                logger.warning(f"[STT] 停止时异常: {e}")
        self._state("idle")
        return self._final_result or self._partial_result

    def get_intermediate_result(self) -> str:
        return self._partial_result

    # ==================== 回调 ====================

    def _on_start(self, message, *args):
        logger.debug(f"[STT] Started: {message}")

    def _on_result_changed(self, message, *args):
        """中间结果更新"""
        try:
            result = json.loads(message) if isinstance(message, str) else message
            text = result.get("result", "")
            if text:
                self._partial_result = text
                if self.on_partial:
                    self.on_partial(text)
        except Exception as e:
            logger.warning(f"[STT] 解析中间结果失败: {e}")

    def _on_sentence_begin(self, message, *args):
        pass

    def _on_sentence_end(self, message, *args):
        """一句话识别结束"""
        try:
            result = json.loads(message) if isinstance(message, str) else message
            text = result.get("result", "")
            if text:
                self._final_result = text
                if self.on_final:
                    self.on_final(text)
        except Exception as e:
            logger.warning(f"[STT] 解析句尾结果失败: {e}")

    def _on_completed(self, message, *args):
        logger.info(f"[STT] 识别完成")
        self._running = False

    def _on_error(self, message, *args):
        try:
            msg = json.loads(message) if isinstance(message, str) else message
            error_msg = msg.get("message", str(message))
        except Exception:
            error_msg = str(message)
        logger.error(f"[STT] 识别错误: {error_msg}")
        if self.on_error:
            self.on_error(error_msg)
        self._running = False

    def _on_close(self, *args):
        logger.debug("[STT] 连接关闭")
        self._running = False

    def _state(self, state: str):
        if self.on_state_change:
            self.on_state_change(state)


# ==================== TTS ====================

class AliyunTTS:
    """阿里云语音合成

    用法：
        tts = AliyunTTS()
        audio_data = tts.synthesize("Hello, this is a test.")
        # audio_data 为 PCM 16kHz 16bit mono bytes
    """

    def __init__(self, app_key: str = "", access_key: str = "",
                 secret_key: str = ""):
        self.app_key = app_key or ALIYUN_APP_KEY
        self.access_key = access_key or ALIYUN_ACCESS_KEY
        self.secret_key = secret_key or ALIYUN_SECRET_KEY

        self.on_audio_chunk: Optional[Callable[[bytes], None]] = None
        self.on_complete: Optional[Callable[[], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None

    def synthesize(self, text: str) -> bytes:
        """同步合成语音，返回 PCM 音频数据"""
        if not HAS_ALIYUN_SDK:
            logger.warning("[TTS] SDK 未安装，返回空音频")
            return b""

        if not text.strip():
            return b""

        audio_chunks = []
        event = threading.Event()

        def on_data(data, *args):
            audio_chunks.append(data)

        def on_completed(msg, *args):
            event.set()

        def on_error(msg, *args):
            logger.error(f"[TTS] 合成错误: {msg}")
            event.set()

        tok = _get_token()
        if not tok:
            return b""

        synthesizer = NlsSpeechSynthesizer(
            url=ALIYUN_GATEWAY,
            token=tok,
            appkey=self.app_key,
            on_data=on_data,
            on_completed=on_completed,
            on_error=on_error,
        )

        synthesizer.start(
            text=text,
            voice=TTS_VOICE,
            aformat="pcm",
            sample_rate=16000,
            volume=TTS_VOLUME,
            speech_rate=TTS_SPEED,
            pitch_rate=0,
            wait_complete=True,
            completed_timeout=30,
        )

        event.wait(timeout=30)

        result = b"".join(audio_chunks)
        logger.info(f"[TTS] 合成完成: {len(text)}字 → {len(result)}字节")
        return result

    def synthesize_stream(self, text: str):
        """流式合成，通过 on_audio_chunk 回调返回音频块"""
        if not HAS_ALIYUN_SDK:
            return

        if not text.strip():
            return

        def on_data(data, *args):
            if self.on_audio_chunk:
                self.on_audio_chunk(data)

        def on_completed(msg, *args):
            if self.on_complete:
                self.on_complete()

        def on_error(msg, *args):
            logger.error(f"[TTS] 流式合成错误: {msg}")
            if self.on_error:
                self.on_error(str(msg))

        tok = _get_token()
        if not tok:
            return

        synthesizer = NlsSpeechSynthesizer(
            url=ALIYUN_GATEWAY,
            token=tok,
            appkey=self.app_key,
            on_data=on_data,
            on_completed=on_completed,
            on_error=on_error,
        )

        synthesizer.start(
            text=text,
            voice=TTS_VOICE,
            aformat="pcm",
            sample_rate=16000,
            volume=TTS_VOLUME,
            speech_rate=TTS_SPEED,
            pitch_rate=0,
            wait_complete=True,
            completed_timeout=30,
        )


# ==================== 降级处理 ====================

class MockSTT:
    """降级 STT — 返回占位文字"""

    def start(self):
        pass

    def send_audio(self, data: bytes):
        pass

    def stop(self) -> str:
        return "[语音识别服务未配置]"

    def get_intermediate_result(self) -> str:
        return ""


class MockTTS:
    """降级 TTS — 返回空音频"""

    def synthesize(self, text: str) -> bytes:
        return b""

    def synthesize_stream(self, text: str):
        pass


def create_stt() -> AliyunSTT:
    """创建 STT 实例（自动降级）"""
    if HAS_ALIYUN_SDK and ALIYUN_APP_KEY and ALIYUN_ACCESS_KEY and ALIYUN_SECRET_KEY:
        return AliyunSTT()
    return MockSTT()  # type: ignore


def create_tts() -> AliyunTTS:
    """创建 TTS 实例（自动降级）"""
    if HAS_ALIYUN_SDK and ALIYUN_APP_KEY and ALIYUN_ACCESS_KEY and ALIYUN_SECRET_KEY:
        return AliyunTTS()
    return MockTTS()  # type: ignore

import asyncio, random, time
from typing import List, Dict, Any, Optional, Union, AsyncGenerator
from enum import Enum
from dataclasses import dataclass
import httpx
from loguru import logger
from app.core.config import config_manager
from app.core.database import db
from app.llm.pool import AICapability, CapabilityPool, capability_pool

# litellm 改为延迟导入
RETRYABLE_EXCEPTIONS = ()
_LITELLM_LOADED = False

def _get_litellm():
    global RETRYABLE_EXCEPTIONS, _LITELLM_LOADED
    if not _LITELLM_LOADED:
        import litellm
        from litellm import acompletion
        RETRYABLE_EXCEPTIONS = (
            litellm.exceptions.APIConnectionError,
            litellm.exceptions.APIError,
            litellm.exceptions.Timeout,
            litellm.exceptions.RateLimitError,
            litellm.exceptions.ServiceUnavailableError,
            ConnectionError,
            TimeoutError,
        )
        _LITELLM_LOADED = True
        return litellm, acompletion
    import litellm
    from litellm import acompletion
    return litellm, acompletion

_model_params_cache = {}

def get_model_max_tokens(model_name: str) -> int:
    global _model_params_cache
    if model_name in _model_params_cache:
        return _model_params_cache[model_name]
    try:
        litellm, _ = _get_litellm()
        model_info = litellm.model_cost.get(model_name, {})
        if model_info:
            max_out = model_info.get("max_output_tokens") or model_info.get("max_tokens") or 4096
            max_in = model_info.get("max_input_tokens") or 8192
            _model_params_cache[model_name] = {
                "max_tokens": min(int(max_out), 65536),
                "max_input": int(max_in),
            }
            return _model_params_cache[model_name]
    except Exception:
        pass
    
    name_lower = model_name.lower()
    if "deepseek" in name_lower:
        _model_params_cache[model_name] = {"max_tokens": 8192, "max_input": 65536}
    elif "glm" in name_lower or "zhipu" in name_lower:
        _model_params_cache[model_name] = {"max_tokens": 4096, "max_input": 131072}
    elif "gpt-4" in name_lower:
        _model_params_cache[model_name] = {"max_tokens": 4096, "max_input": 32768}
    elif "gpt-3" in name_lower:
        _model_params_cache[model_name] = {"max_tokens": 4096, "max_input": 16384}
    else:
        _model_params_cache[model_name] = {"max_tokens": 4096, "max_input": 8192}
    
    return _model_params_cache[model_name]

class LLMCallError(Exception):
    def __init__(self, m, orig=None):
        super().__init__(m)
        self.original_error = orig

class StopReason(Enum):
    SUCCESS = "success"
    USER_CANCELLED = "user_cancelled"
    MAX_RETRIES = "max_retries"
    UNRECOVERABLE = "unrecoverable"
    FALLBACK = "fallback"
    STREAM_FALLBACK = "stream_fallback"

@dataclass
class LLMResponse:
    content: str
    model: str
    usage: Dict[str, int]
    finish_reason: str
    stop_reason: StopReason
    retry_count: int = 0
    raw_response: Any = None

class EndpointHealth:
    def __init__(self):
        self.failures = {}
        self.last_success = {}
        self.cooldown_until = {}
        self._lock = asyncio.Lock()
    
    async def record_success(self, ep):
        async with self._lock:
            self.failures[ep] = 0
            self.last_success[ep] = time.time()
            if ep in self.cooldown_until:
                del self.cooldown_until[ep]
    
    async def record_failure(self, ep):
        async with self._lock:
            self.failures[ep] = self.failures.get(ep, 0) + 1
            if self.failures.get(ep, 0) >= 3:
                self.cooldown_until[ep] = time.time() + 30
    
    async def is_available(self, ep):
        async with self._lock:
            if ep in self.cooldown_until and time.time() < self.cooldown_until[ep]:
                return False
            if ep in self.cooldown_until:
                del self.cooldown_until[ep]
                self.failures[ep] = 0
            return True

class LLMClient:
    def __init__(self):
        self.default_retry = config_manager.get("ai_pool.retry", {
            "max_retries": 10, "base_delay": 1, "max_delay": 30,
            "exponential_base": 2, "notify_after": 10, "infinite_retry": False
        })
        self._notified_retry: Dict[str, bool] = {}
        mc = config_manager.get("ai_pool.concurrency.max_concurrent_calls", 10)
        self._global_sem = asyncio.Semaphore(mc)
        self._ep_sems = {
            ep: asyncio.Semaphore(lim) 
            for ep, lim in config_manager.get("ai_pool.concurrency.per_endpoint_limit", {}).items()
        }
        self.health = EndpointHealth()
        self._http_client = None
        self._client_lock = asyncio.Lock()
        self._global_cancel_event = None

    def set_global_cancel_event(self, ev):
        self._global_cancel_event = ev

    async def call(self, capability, messages, temperature=None, max_tokens=None, 
                  cancellation_event=None, max_retries=None, infinite_retry=False, 
                  stream=False, fallback_capabilities=None, **kwargs):
        cancel_evt = cancellation_event or self._global_cancel_event
        if stream:
            return self._call_stream(capability, messages, temperature, max_tokens, 
                                    cancel_evt, max_retries, infinite_retry, fallback_capabilities, **kwargs)
        else:
            return await self._call_non_stream(capability, messages, temperature, max_tokens,
                                               cancel_evt, max_retries, infinite_retry, fallback_capabilities, **kwargs)

    PROVIDER_ALIASES = {
        "zhipuai": "openai", "zhipu": "openai", "wenxin": "openai",
        "qianfan": "openai", "spark": "openai", "minimax": "openai", "baichuan": "openai",
    }
    
    def _ensure_model_prefix(self, model: str) -> str:
        if "/" not in model:
            return f"openai/{model}"
        provider, model_name = model.split("/", 1)
        mapped = self.PROVIDER_ALIASES.get(provider, provider)
        if mapped != provider:
            return f"{mapped}/{model_name}"
        return model

    async def _try_call(self, cap, messages, temp, max_tok, cancel_evt, max_retries, infinite_retry, **kwargs):
        _, acompletion = _get_litellm()
        model = self._ensure_model_prefix(cap.model)
        params = {"model": model, "messages": messages, "api_base": cap.endpoint or None, "api_key": cap.api_key or None}
        model_info = get_model_max_tokens(model)
        for k, v in cap.parameters.items():
            if k == "max_tokens":
                params[k] = min(int(v) if v else 4096, model_info["max_tokens"])
            else:
                params[k] = v
        if temp is not None:
            params["temperature"] = temp
        if max_tok is not None:
            params["max_tokens"] = min(int(max_tok), model_info["max_tokens"])
        params.update(kwargs)
        
        retry_cfg = self.default_retry
        effective_infinite = infinite_retry or retry_cfg.get("infinite_retry", False) or max_retries == -1
        limit = float("inf") if effective_infinite else (max_retries if max_retries is not None else retry_cfg["max_retries"])
        notify_after = retry_cfg.get("notify_after", 10)
        attempt = 0
        notified = False
        
        while True:
            if cancel_evt and cancel_evt.is_set():
                raise LLMCallError("用户取消")
            try:
                call_timeout = retry_cfg.get("call_timeout", 600)
                resp = await asyncio.wait_for(acompletion(**params), timeout=call_timeout)
                usage = {"prompt_tokens": resp.usage.prompt_tokens, "completion_tokens": resp.usage.completion_tokens, "total_tokens": resp.usage.total_tokens}
                content = resp.choices[0].message.content or ""
                await self.health.record_success(cap.endpoint)
                await self._record_usage(cap, resp.model, usage, params.get("messages", []))
                return LLMResponse(content=content, model=resp.model, usage=usage, 
                                  finish_reason=resp.choices[0].finish_reason, 
                                  stop_reason=StopReason.SUCCESS, retry_count=attempt, raw_response=resp)
            except Exception as e:
                attempt += 1
                await self.health.record_failure(cap.endpoint)
                litellm, _ = _get_litellm()
                retry_exceptions = (
                    litellm.exceptions.APIConnectionError,
                    litellm.exceptions.APIError,
                    litellm.exceptions.Timeout,
                    litellm.exceptions.RateLimitError,
                    litellm.exceptions.ServiceUnavailableError,
                    ConnectionError,
                    TimeoutError,
                )
                if not isinstance(e, retry_exceptions) and "InternalServerError" not in type(e).__name__:
                    raise LLMCallError(f"不可重试错误: {e}", e)
                if not effective_infinite and attempt > limit:
                    raise LLMCallError(f"重试{limit}次仍失败", e)
                if attempt >= notify_after and not notified:
                    notified = True
                delay = min(retry_cfg["base_delay"] * (retry_cfg["exponential_base"] ** (attempt - 1)), retry_cfg["max_delay"])
                logger.warning(f"LLM调用失败(尝试{attempt}): {e}. {delay:.2f}s后重试...")
                try:
                    await self._interruptible_sleep(delay, cancel_evt)
                except LLMCallError:
                    raise

    async def _call_non_stream(self, cap, messages, temp, max_tok, cancel_evt, max_retries, infinite_retry, fallback_caps=None, **kwargs):
        sem = self._ep_sems.get(cap.endpoint, self._global_sem)
        async with sem:
            primary = cap
            backups = list(fallback_caps or [])
            if not backups:
                try:
                    from app.llm.pool import capability_pool
                    backups = await capability_pool.get_fallback_instances(cap.id, count=3)
                except Exception:
                    pass
            
            stuck_reported = False
            while True:
                if cancel_evt and cancel_evt.is_set():
                    raise LLMCallError("用户取消")
                
                if await self.health.is_available(primary.endpoint):
                    try:
                        res = await self._try_call(primary, messages, temp, max_tok, cancel_evt, max_retries, infinite_retry=infinite_retry, **kwargs)
                        return res
                    except LLMCallError as e:
                        logger.warning(f"主模型{primary.name} 失败: {e}")
                        if "不可重试" in str(e):
                            raise
                
                for bk in backups:
                    if await self.health.is_available(bk.endpoint):
                        try:
                            res = await self._try_call(bk, messages, temp, max_tok, cancel_evt, max_retries, infinite_retry=infinite_retry, **kwargs)
                            res.stop_reason = StopReason.FALLBACK
                            logger.info(f"切换到备用模型 {bk.name}")
                            return res
                        except LLMCallError:
                            logger.warning(f"备用模型 {bk.name} 也失败")
                
                if not stuck_reported:
                    stuck_reported = True
                    logger.warning("主备模型均失败，换回主模型继续重试...")
                
                try:
                    await asyncio.wait_for(asyncio.sleep(5), timeout=5)
                except:
                    pass

    async def _call_stream(self, cap, messages, temp, max_tok, cancel_evt, max_retries, infinite_retry, fallback_caps, **kwargs):
        if infinite_retry:
            max_retries = 10
        _, acompletion = _get_litellm()
        model = self._ensure_model_prefix(cap.model)
        params = {"model": model, "messages": messages, "api_base": cap.endpoint or None, "api_key": cap.api_key or None, "stream": True}
        model_info = get_model_max_tokens(model)
        for k, v in cap.parameters.items():
            if k == "max_tokens":
                params[k] = min(int(v) if v else 4096, model_info["max_tokens"])
            else:
                params[k] = v
        if temp is not None:
            params["temperature"] = temp
        if max_tok is not None:
            params["max_tokens"] = min(int(max_tok), model_info["max_tokens"])
        params.update(kwargs)
        retry_limit = max_retries or self.default_retry["max_retries"]
        attempt = 0
        
        while True:
            if cancel_evt and cancel_evt.is_set():
                break
            try:
                call_timeout = self.default_retry.get("call_timeout", 600)
                resp = await asyncio.wait_for(acompletion(**params), timeout=call_timeout)
                async for chunk in resp:
                    if cancel_evt and cancel_evt.is_set():
                        break
                    if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
                return
            except Exception as e:
                attempt += 1
                litellm, _ = _get_litellm()
                retry_exceptions = (
                    litellm.exceptions.APIConnectionError,
                    litellm.exceptions.APIError,
                    litellm.exceptions.Timeout,
                    litellm.exceptions.RateLimitError,
                    litellm.exceptions.ServiceUnavailableError,
                    ConnectionError,
                    TimeoutError,
                )
                if (not isinstance(e, retry_exceptions) and "InternalServerError" not in type(e).__name__) or attempt > retry_limit:
                    logger.warning(f"流式失败，降级为非流式: {e}")
                    try:
                        nr = await self._call_non_stream(cap, messages, temp, max_tok, cancel_evt, max_retries=5, infinite_retry=False, fallback_capabilities=fallback_caps, **kwargs)
                        nr.stop_reason = StopReason.STREAM_FALLBACK
                        yield nr.content
                        return
                    except Exception as fe:
                        raise LLMCallError(f"流式及回退均失败: {fe}", e)
                delay = min(1.0 * (2 ** (attempt - 1)), 10)
                logger.warning(f"流式中断，{delay:.2f}s后重试{attempt}/{retry_limit}")
                await self._interruptible_sleep(delay, cancel_evt)

    async def _record_usage(self, cap: AICapability, model: str, usage: Dict, messages: List):
        try:
            task_id = messages[0].get("task_id") if messages else None
            role = messages[0].get("role") if messages else "unknown"
            cost = (usage.get("total_tokens", 0) / 1000) * cap.cost_per_1k_tokens
            stats = {
                "task_id": task_id, "role": role, "model": model,
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
                "cost": cost
            }
            await db.save_token_stats(stats)
        except Exception as e:
            logger.debug(f"Failed to record token stats: {e}")

    async def _interruptible_sleep(self, duration, cancel_event):
        if not cancel_event:
            await asyncio.sleep(duration)
            return
        try:
            await asyncio.wait_for(cancel_event.wait(), timeout=duration)
            raise LLMCallError("用户取消")
        except asyncio.TimeoutError:
            pass

llm_client = LLMClient()
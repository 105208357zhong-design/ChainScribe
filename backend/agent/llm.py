"""
ChainScribe — GLM-5.1 LLM 客户端
接入 Z.AI API，驱动 Agent 的核心推理能力
"""
import json
import os
import aiohttp
from typing import Any, Optional


class GLMClient:
    """
    GLM-5.1 API 客户端
    
    支持功能：
    - 文本生成（长文写作、大纲、审查）
    - 结构化输出（JSON mode）
    - 多轮对话（上下文管理）
    """

    def __init__(self, api_key: str = None, base_url: str = None):
        self.api_key = api_key or os.getenv("ZAI_API_KEY", "")
        self.base_url = base_url or "https://open.bigmodel.cn/api/paas/v4"
        self.model = "glm-5.1"
        self._conversation_history: list[dict] = []

    async def generate(
        self,
        prompt: str,
        system_prompt: str = None,
        json_mode: bool = False,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> Any:
        """
        调用 GLM-5.1 生成内容
        
        Args:
            prompt: 用户提示
            system_prompt: 系统提示
            json_mode: 是否返回 JSON 格式
            max_tokens: 最大生成 token 数
            temperature: 温度参数
        
        Returns:
            生成的内容（json_mode=True 时返回解析后的 dict）
        """
        if not self.api_key:
            # 无 API Key 时返回 None，让 Agent 使用 mock 数据
            return None

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # 添加历史上下文
        messages.extend(self._conversation_history[-6:])  # 最近3轮
        
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=120),
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        content = data["choices"][0]["message"]["content"]
                        
                        # 更新对话历史
                        self._conversation_history.append({"role": "user", "content": prompt})
                        self._conversation_history.append({"role": "assistant", "content": content})
                        
                        if json_mode:
                            try:
                                return json.loads(content)
                            except json.JSONDecodeError:
                                return {"raw": content}
                        return content
                    else:
                        error_text = await resp.text()
                        raise Exception(f"API error {resp.status}: {error_text}")
        except aiohttp.ClientError as e:
            raise Exception(f"Network error: {str(e)}")

    async def generate_structured(
        self,
        prompt: str,
        schema: dict = None,
        system_prompt: str = None,
    ) -> dict:
        """
        生成结构化输出
        
        Args:
            prompt: 用户提示
            schema: 期望的 JSON schema
            system_prompt: 系统提示
        
        Returns:
            解析后的 dict
        """
        sys = system_prompt or "你是一个专业的内容创作助手。请始终以JSON格式返回结果。"
        if schema:
            sys += f"\n\n期望的输出格式：\n```json\n{json.dumps(schema, ensure_ascii=False, indent=2)}\n```"

        return await self.generate(
            prompt=prompt,
            system_prompt=sys,
            json_mode=True,
            temperature=0.5,
        )

    def clear_history(self):
        """清除对话历史"""
        self._conversation_history = []

"""
ChainScribe — IPFS 去中心化存储客户端
"""
import json
import os
import aiohttp
import uuid
from typing import Optional


class IPFSClient:
    """
    IPFS 客户端 — 上传和获取内容
    
    支持：
    - Pinata API（生产环境）
    - 本地 IPFS 节点
    - Mock 模式（Demo）
    """

    def __init__(self, pinata_api_key: str = None, pinata_secret: str = None, gateway: str = None):
        self.api_key = pinata_api_key or os.getenv("PINATA_API_KEY", "")
        self.secret = pinata_secret or os.getenv("PINATA_SECRET", "")
        self.gateway = gateway or "https://ipfs.io/ipfs"
        self._mock_store: dict[str, str] = {}

    async def upload_json(self, data: dict, filename: str = None) -> dict:
        """上传 JSON 数据到 IPFS"""
        content = json.dumps(data, ensure_ascii=False, indent=2)
        return await self._upload(content, filename or "metadata.json", "application/json")

    async def upload_html(self, html: str, filename: str = None) -> dict:
        """上传 HTML 内容到 IPFS"""
        return await self._upload(html, filename or "index.html", "text/html")

    async def upload_image(self, image_data: bytes, filename: str = None) -> dict:
        """上传图片到 IPFS"""
        if self.api_key and self.secret:
            return await self._upload_pinata_file(image_data, filename or "image.png")

        # Mock 模式
        cid = f"Qm{uuid.uuid4().hex[:44]}"
        self._mock_store[cid] = f"<image data: {len(image_data)} bytes>"
        return {
            "cid": cid,
            "url": f"{self.gateway}/{cid}",
            "size": len(image_data),
        }

    async def get_content(self, cid: str) -> Optional[str]:
        """从 IPFS 获取内容"""
        if cid in self._mock_store:
            return self._mock_store[cid]

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.gateway}/{cid}",
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as resp:
                    if resp.status == 200:
                        return await resp.text()
        except Exception:
            pass

        return None

    async def _upload(self, content: str, filename: str, content_type: str) -> dict:
        """通用上传方法"""
        if self.api_key and self.secret:
            return await self._upload_pinata_json(content, filename)

        # Mock 模式
        cid = f"Qm{uuid.uuid4().hex[:44]}"
        self._mock_store[cid] = content
        return {
            "cid": cid,
            "url": f"{self.gateway}/{cid}",
            "size": len(content.encode()),
        }

    async def _upload_pinata_json(self, content: str, filename: str) -> dict:
        """通过 Pinata API 上传 JSON"""
        headers = {
            "pinata_api_key": self.api_key,
            "pinata_secret_api_key": self.secret,
        }

        data = {
            "pinataOptions": {"cidVersion": 1},
            "pinataMetadata": {"name": filename},
            "pinataContent": json.loads(content) if content.startswith("{") else content,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.pinata.cloud/pinning/pinJSONToIPFS",
                json=data,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=60),
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    cid = result["IpfsHash"]
                    return {
                        "cid": cid,
                        "url": f"{self.gateway}/{cid}",
                        "size": len(content.encode()),
                    }
                else:
                    raise Exception(f"Pinata upload failed: {await resp.text()}")

    async def _upload_pinata_file(self, file_data: bytes, filename: str) -> dict:
        """通过 Pinata API 上传文件"""
        headers = {
            "pinata_api_key": self.api_key,
            "pinata_secret_api_key": self.secret,
        }

        form = aiohttp.FormData()
        form.add_field("file", file_data, filename=filename)
        form.add_field("pinataMetadata", json.dumps({"name": filename}))
        form.add_field("pinataOptions", json.dumps({"cidVersion": 1}))

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.pinata.cloud/pinning/pinFileToIPFS",
                data=form,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=120),
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    cid = result["IpfsHash"]
                    return {
                        "cid": cid,
                        "url": f"{self.gateway}/{cid}",
                        "size": len(file_data),
                    }
                else:
                    raise Exception(f"Pinata upload failed: {await resp.text()}")

"""
ChainScribe — 区块链交互客户端
与 ContentNFT 智能合约交互
"""
import json
import os
import time
import uuid
from typing import Any, Optional
from web3 import Web3


class BlockchainClient:
    """
    区块链客户端 — 与 ContentNFT 合约交互
    
    支持：
    - 铸造内容 NFT
    - 付费解锁
    - 更新动态叙事
    - 设置分账
    - 查询链上数据
    """

    # ContentNFT 合约 ABI（核心函数）
    CONTRACT_ABI = [
        {"inputs": [], "name": "mintContent", "type": "function"},
        {"inputs": [{"name": "tokenId", "type": "uint256"}], "name": "unlockContent", "type": "function"},
        {"inputs": [{"name": "tokenId", "type": "uint256"}, {"name": "newContentURI", "type": "string"}, {"name": "newPreviewURI", "type": "string"}], "name": "updateNarrative", "type": "function"},
        {"inputs": [{"name": "tokenId", "type": "uint256"}, {"name": "recipients", "type": "address[]"}, {"name": "basisPoints", "type": "uint16[]"}], "name": "setRoyaltySplit", "type": "function"},
        {"inputs": [{"name": "tokenId", "type": "uint256"}, {"name": "reader", "type": "address"}], "name": "isUnlocked", "outputs": [{"name": "", "type": "bool"}], "type": "function"},
        {"inputs": [{"name": "tokenId", "type": "uint256"}], "name": "getContentURI", "outputs": [{"name": "", "type": "string"}], "type": "function"},
        {"inputs": [{"name": "tokenId", "type": "uint256"}], "name": "contentMeta", "outputs": [{"name": "", "type": "tuple"}], "type": "function"},
    ]

    def __init__(
        self,
        rpc_url: str = None,
        contract_address: str = None,
        private_key: str = None,
    ):
        self.rpc_url = rpc_url or os.getenv("RPC_URL", "https://eth-sepolia.g.alchemy.com/v2/demo")
        self.contract_address = contract_address or os.getenv("CONTRACT_ADDRESS", "")
        self.private_key = private_key or os.getenv("WALLET_PRIVATE_KEY", "")
        self._mock_mode = not (self.contract_address and self.private_key)
        self._mock_store: dict = {}

    def _get_contract(self):
        """获取合约实例"""
        w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        contract = w3.eth.contract(
            address=Web3.to_checksum_address(self.contract_address),
            abi=self.CONTRACT_ABI,
        )
        return w3, contract

    async def mint_content_nft(
        self,
        author_address: str,
        content_cid: str,
        preview_cid: str,
        unlock_price_eth: float = 0.01,
        is_dynamic: bool = False,
    ) -> dict:
        """铸造内容 NFT"""
        if self._mock_mode:
            return self._mock_mint(author_address, content_cid, preview_cid, unlock_price_eth, is_dynamic)

        w3, contract = self._get_contract()
        unlock_price_wei = w3.to_wei(unlock_price_eth, "ether")

        account = w3.eth.account.from_key(self.private_key)
        
        tx = contract.functions.mintContent(
            Web3.to_checksum_address(author_address),
            f"ipfs://{content_cid}",
            f"ipfs://{preview_cid}",
            unlock_price_wei,
            Web3.to_checksum_address("0x0000000000000000000000000000000000000000"),  # ETH
            is_dynamic,
        ).build_transaction({
            "from": account.address,
            "nonce": w3.eth.get_transaction_count(account.address),
            "gas": 500000,
            "gasPrice": w3.eth.gas_price,
        })

        signed = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

        # 解析事件获取 tokenId
        token_id = 0
        for log in receipt.logs:
            if log.address == self.contract_address:
                token_id = int(log.topics[3].hex(), 16) if len(log.topics) > 3 else 0
                break

        return {
            "token_id": token_id,
            "tx_hash": tx_hash.hex(),
            "block_number": receipt.blockNumber,
            "gas_used": receipt.gasUsed,
            "contract_address": self.contract_address,
        }

    async def unlock_content(self, token_id: int, reader_address: str, price_eth: float) -> dict:
        """付费解锁内容"""
        if self._mock_mode:
            return self._mock_unlock(token_id, reader_address, price_eth)

        w3, contract = self._get_contract()
        account = w3.eth.account.from_key(self.private_key)
        price_wei = w3.to_wei(price_eth, "ether")

        tx = contract.functions.unlockContent(token_id).build_transaction({
            "from": account.address,
            "value": price_wei,
            "nonce": w3.eth.get_transaction_count(account.address),
            "gas": 200000,
            "gasPrice": w3.eth.gas_price,
        })

        signed = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

        return {
            "tx_hash": tx_hash.hex(),
            "block_number": receipt.blockNumber,
            "gas_used": receipt.gasUsed,
        }

    async def update_narrative(self, token_id: int, new_content_cid: str, new_preview_cid: str) -> dict:
        """更新动态叙事 NFT"""
        if self._mock_mode:
            return self._mock_update_narrative(token_id, new_content_cid, new_preview_cid)

        w3, contract = self._get_contract()
        account = w3.eth.account.from_key(self.private_key)

        tx = contract.functions.updateNarrative(
            token_id,
            f"ipfs://{new_content_cid}",
            f"ipfs://{new_preview_cid}",
        ).build_transaction({
            "from": account.address,
            "nonce": w3.eth.get_transaction_count(account.address),
            "gas": 300000,
            "gasPrice": w3.eth.gas_price,
        })

        signed = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

        return {
            "tx_hash": tx_hash.hex(),
            "block_number": receipt.blockNumber,
            "gas_used": receipt.gasUsed,
            "narrative_version": "updated",
        }

    async def set_royalty_split(self, token_id: int, splits: list[dict]) -> dict:
        """设置收益分账"""
        if self._mock_mode:
            return self._mock_set_royalty(token_id, splits)

        w3, contract = self._get_contract()
        account = w3.eth.account.from_key(self.private_key)

        recipients = [Web3.to_checksum_address(s["address"]) for s in splits]
        basis_points = [s["basis_points"] for s in splits]

        tx = contract.functions.setRoyaltySplit(token_id, recipients, basis_points).build_transaction({
            "from": account.address,
            "nonce": w3.eth.get_transaction_count(account.address),
            "gas": 300000,
            "gasPrice": w3.eth.gas_price,
        })

        signed = account.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

        return {
            "tx_hash": tx_hash.hex(),
            "block_number": receipt.blockNumber,
            "gas_used": receipt.gasUsed,
        }

    async def get_content_meta(self, token_id: int) -> dict:
        """获取内容元数据"""
        if self._mock_mode:
            return self._mock_store.get(f"meta_{token_id}", {})

        w3, contract = self._get_contract()
        meta = contract.functions.contentMeta(token_id).call()
        
        return {
            "author": meta[0],
            "contentURI": meta[1],
            "previewURI": meta[2],
            "unlockPrice": meta[3],
            "paymentToken": meta[4],
            "mintedAt": meta[5],
            "totalRevenue": meta[6],
            "unlockCount": meta[7],
            "isDynamic": meta[8],
            "narrativeVersion": meta[9],
        }

    # ─── Mock 方法 ──────────────────────────────────────

    def _mock_mint(self, author, content_cid, preview_cid, price, is_dynamic):
        token_id = len(self._mock_store) + 1
        result = {
            "token_id": token_id,
            "tx_hash": f"0x{uuid.uuid4().hex}",
            "block_number": 19283746 + token_id,
            "gas_used": 185000,
            "contract_address": self.contract_address or "0xMock",
        }
        self._mock_store[f"meta_{token_id}"] = {
            "author": author,
            "contentURI": f"ipfs://{content_cid}",
            "previewURI": f"ipfs://{preview_cid}",
            "unlockPrice": f"{price} ETH",
            "isDynamic": is_dynamic,
            "narrativeVersion": 1,
        }
        return result

    def _mock_unlock(self, token_id, reader, price):
        return {
            "tx_hash": f"0x{uuid.uuid4().hex}",
            "block_number": 19283800,
            "gas_used": 65000,
        }

    def _mock_update_narrative(self, token_id, content_cid, preview_cid):
        meta = self._mock_store.get(f"meta_{token_id}", {})
        meta["narrativeVersion"] = meta.get("narrativeVersion", 1) + 1
        meta["contentURI"] = f"ipfs://{content_cid}"
        meta["previewURI"] = f"ipfs://{preview_cid}"
        self._mock_store[f"meta_{token_id}"] = meta
        return {
            "tx_hash": f"0x{uuid.uuid4().hex}",
            "block_number": 19283900,
            "gas_used": 95000,
            "narrative_version": meta["narrativeVersion"],
        }

    def _mock_set_royalty(self, token_id, splits):
        return {
            "tx_hash": f"0x{uuid.uuid4().hex}",
            "block_number": 19283950,
            "gas_used": 75000,
        }

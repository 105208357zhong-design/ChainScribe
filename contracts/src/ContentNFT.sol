// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title ChainScribe Content NFT
 * @notice 链上出版 NFT — 付费解锁 + 版税分账 + 动态叙事
 */
contract ContentNFT {
    string public name = "ChainScribe Content";
    string public symbol = "CSCRT";
    
    uint256 private _nextTokenId = 1;
    address public owner;

    struct ContentMeta {
        address author;
        string contentURI;       // IPFS CID (encrypted full content)
        string previewURI;       // IPFS CID (free preview)
        uint256 unlockPrice;     // in wei
        uint256 mintedAt;
        uint256 totalRevenue;
        uint256 unlockCount;
        bool isDynamic;
        uint256 narrativeVersion;
        string narrativeSeed;    // seed for dynamic narrative generation
    }

    struct RoyaltySplit {
        address recipient;
        uint16 basisPoints;      // 10000 = 100%
    }

    // Mappings
    mapping(uint256 => ContentMeta) public contentMeta;
    mapping(uint256 => address) public tokenOwner;
    mapping(uint256 => string) public tokenURIs;
    mapping(uint256 => mapping(address => bool)) public hasUnlocked;
    mapping(uint256 => RoyaltySplit[]) public royaltySplits;
    mapping(address => uint256[]) public authorTokens;

    // Events
    event ContentMinted(uint256 indexed tokenId, address indexed author, string contentURI, uint256 unlockPrice, bool isDynamic);
    event ContentUnlocked(uint256 indexed tokenId, address indexed reader, uint256 pricePaid);
    event NarrativeUpdated(uint256 indexed tokenId, uint256 version, string newContentURI, string seed);
    event RoyaltyDistributed(uint256 indexed tokenId, address recipient, uint256 amount);
    event RevenueWithdrawn(uint256 indexed tokenId, address indexed author, uint256 amount);

    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }

    modifier onlyAuthor(uint256 tokenId) {
        require(contentMeta[tokenId].author == msg.sender, "Not author");
        _;
    }

    constructor() {
        owner = msg.sender;
    }

    function mintContent(
        address author,
        string calldata contentURI,
        string calldata previewURI,
        uint256 unlockPrice,
        bool isDynamic,
        string calldata narrativeSeed
    ) external returns (uint256) {
        uint256 tokenId = _nextTokenId++;

        contentMeta[tokenId] = ContentMeta({
            author: author,
            contentURI: contentURI,
            previewURI: previewURI,
            unlockPrice: unlockPrice,
            mintedAt: block.timestamp,
            totalRevenue: 0,
            unlockCount: 0,
            isDynamic: isDynamic,
            narrativeVersion: 1,
            narrativeSeed: narrativeSeed
        });

        tokenOwner[tokenId] = author;
        tokenURIs[tokenId] = previewURI;
        authorTokens[author].push(tokenId);

        emit ContentMinted(tokenId, author, contentURI, unlockPrice, isDynamic);
        return tokenId;
    }

    function unlockContent(uint256 tokenId) external payable {
        ContentMeta storage meta = contentMeta[tokenId];
        require(meta.unlockPrice > 0, "Content is free");
        require(!hasUnlocked[tokenId][msg.sender], "Already unlocked");
        require(msg.value >= meta.unlockPrice, "Insufficient payment");

        hasUnlocked[tokenId][msg.sender] = true;
        meta.unlockCount++;
        meta.totalRevenue += msg.value;

        // Distribute royalties
        uint256 totalDistributed = 0;
        for (uint256 i = 0; i < royaltySplits[tokenId].length; i++) {
            uint256 share = (msg.value * royaltySplits[tokenId][i].basisPoints) / 10000;
            payable(royaltySplits[tokenId][i].recipient).transfer(share);
            totalDistributed += share;
            emit RoyaltyDistributed(tokenId, royaltySplits[tokenId][i].recipient, share);
        }

        // Remainder to author
        uint256 authorShare = msg.value - totalDistributed;
        if (authorShare > 0) {
            payable(meta.author).transfer(authorShare);
        }

        // Refund excess
        if (msg.value > meta.unlockPrice) {
            payable(msg.sender).transfer(msg.value - meta.unlockPrice);
        }

        emit ContentUnlocked(tokenId, msg.sender, meta.unlockPrice);
    }

    function updateNarrative(
        uint256 tokenId,
        string calldata newContentURI,
        string calldata newPreviewURI,
        string calldata newSeed
    ) external onlyAuthor(tokenId) {
        ContentMeta storage meta = contentMeta[tokenId];
        require(meta.isDynamic, "Not a dynamic NFT");

        meta.contentURI = newContentURI;
        meta.narrativeVersion++;
        meta.narrativeSeed = newSeed;
        tokenURIs[tokenId] = newPreviewURI;

        emit NarrativeUpdated(tokenId, meta.narrativeVersion, newContentURI, newSeed);
    }

    function setRoyaltySplits(
        uint256 tokenId,
        address[] calldata recipients,
        uint16[] calldata basisPoints
    ) external onlyAuthor(tokenId) {
        require(recipients.length == basisPoints.length, "Length mismatch");
        
        uint16 totalBps = 0;
        delete royaltySplits[tokenId];

        for (uint256 i = 0; i < recipients.length; i++) {
            require(basisPoints[i] <= 5000, "Max 50% per split");
            totalBps += basisPoints[i];
            royaltySplits[tokenId].push(RoyaltySplit(recipients[i], basisPoints[i]));
        }
        require(totalBps <= 9000, "Total splits max 90%");
    }

    // View functions
    function isUnlocked(uint256 tokenId, address reader) external view returns (bool) {
        return hasUnlocked[tokenId][reader];
    }

    function getContentURI(uint256 tokenId) external view returns (string memory) {
        require(hasUnlocked[tokenId][msg.sender] || contentMeta[tokenId].author == msg.sender, "Content locked");
        return contentMeta[tokenId].contentURI;
    }

    function getAuthorTokens(address author) external view returns (uint256[] memory) {
        return authorTokens[author];
    }

    function totalSupply() external view returns (uint256) {
        return _nextTokenId - 1;
    }
}

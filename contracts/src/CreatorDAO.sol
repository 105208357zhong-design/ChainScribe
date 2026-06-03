// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title CreatorDAO — 多 Agent 协作与自动分账
 * @notice 支持多角色协作创建内容，收益按贡献自动分配
 */
contract CreatorDAO {
    address public owner;
    uint256 private _nextProposalId = 1;
    uint256 private _nextProjectId = 1;

    enum AgentRole { RESEARCHER, WRITER, DESIGNER, PUBLISHER, PROMOTER }
    enum ProposalStatus { PENDING, APPROVED, EXECUTING, COMPLETED, FAILED }
    
    struct Agent {
        address wallet;
        AgentRole role;
        uint16 revenueShare;  // basis points
        bool isActive;
    }

    struct Project {
        uint256 id;
        address creator;
        string topic;
        string contentURI;
        uint256 nftTokenId;
        uint256 totalRevenue;
        uint256 createdAt;
        ProposalStatus status;
        mapping(AgentRole => address) roleAssignments;
    }

    struct Proposal {
        uint256 id;
        uint256 projectId;
        address proposer;
        string description;
        uint256 votesFor;
        uint256 votesAgainst;
        uint256 deadline;
        bool executed;
    }

    mapping(uint256 => Project) public projects;
    mapping(uint256 => Proposal) public proposals;
    mapping(address => Agent) public agents;
    mapping(uint256 => mapping(AgentRole => address)) public projectRoles;
    address[] public agentList;

    event AgentRegistered(address indexed wallet, AgentRole role, uint16 revenueShare);
    event ProjectCreated(uint256 indexed projectId, address creator, string topic);
    event RoleAssigned(uint256 indexed projectId, AgentRole role, address agent);
    event ProjectCompleted(uint256 indexed projectId, string contentURI, uint256 nftTokenId);
    event RevenueDistributed(uint256 indexed projectId, address agent, uint256 amount);
    event ProposalCreated(uint256 indexed proposalId, uint256 projectId, string description);

    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }

    constructor() {
        owner = msg.sender;
    }

    function registerAgent(address wallet, AgentRole role, uint16 revenueShare) external onlyOwner {
        require(revenueShare <= 3000, "Max 30% per agent");
        agents[wallet] = Agent(wallet, role, revenueShare, true);
        agentList.push(wallet);
        emit AgentRegistered(wallet, role, revenueShare);
    }

    function createProject(string calldata topic) external returns (uint256) {
        uint256 projectId = _nextProjectId++;
        Project storage p = projects[projectId];
        p.id = projectId;
        p.creator = msg.sender;
        p.topic = topic;
        p.createdAt = block.timestamp;
        p.status = ProposalStatus.APPROVED;
        
        emit ProjectCreated(projectId, msg.sender, topic);
        return projectId;
    }

    function assignRole(uint256 projectId, AgentRole role, address agent) external {
        require(agents[agent].isActive, "Agent not active");
        projectRoles[projectId][role] = agent;
        emit RoleAssigned(projectId, role, agent);
    }

    function completeProject(
        uint256 projectId,
        string calldata contentURI,
        uint256 nftTokenId
    ) external {
        Project storage p = projects[projectId];
        p.contentURI = contentURI;
        p.nftTokenId = nftTokenId;
        p.status = ProposalStatus.COMPLETED;
        emit ProjectCompleted(projectId, contentURI, nftTokenId);
    }

    function distributeRevenue(uint256 projectId) external payable {
        Project storage p = projects[projectId];
        p.totalRevenue += msg.value;

        uint256 totalDistributed = 0;
        for (uint256 i = 0; i < agentList.length; i++) {
            Agent storage agent = agents[agentList[i]];
            if (agent.isActive && agent.revenueShare > 0) {
                uint256 share = (msg.value * agent.revenueShare) / 10000;
                if (share > 0) {
                    payable(agent.wallet).transfer(share);
                    totalDistributed += share;
                    emit RevenueDistributed(projectId, agent.wallet, share);
                }
            }
        }

        // Remainder to creator
        uint256 creatorShare = msg.value - totalDistributed;
        if (creatorShare > 0) {
            payable(p.creator).transfer(creatorShare);
        }
    }

    function getAgentCount() external view returns (uint256) {
        return agentList.length;
    }
}

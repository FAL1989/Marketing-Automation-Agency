import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { AgentDashboard } from '../../components/agents/AgentDashboard';
import { useAgents } from '../../hooks/useAgents';
import { useAgentInteractions } from '../../hooks/useAgentInteractions';
import { useAgentMetrics } from '../../hooks/useAgentMetrics';

// Mock the hooks
jest.mock('../../hooks/useAgents');
jest.mock('../../hooks/useAgentInteractions');
jest.mock('../../hooks/useAgentMetrics');

const mockAgents = [
    {
        id: '1',
        name: 'RequirementsAnalyzer',
        description: 'Analyzes project requirements',
        status: 'active',
        type: 'requirements',
        capabilities: ['analyze', 'validate'],
        lastActive: new Date().toISOString()
    },
    {
        id: '2',
        name: 'CodeAnalyzer',
        description: 'Analyzes code quality',
        status: 'idle',
        type: 'code',
        capabilities: ['analyze', 'review'],
        lastActive: new Date().toISOString()
    }
];

const mockInteractions = [
    {
        id: '1',
        agentId: '1',
        timestamp: new Date().toISOString(),
        type: 'request',
        content: 'Analyze requirement: User authentication system'
    },
    {
        id: '2',
        agentId: '1',
        timestamp: new Date().toISOString(),
        type: 'response',
        content: 'Analysis completed successfully'
    }
];

const mockMetrics = {
    successRate: 98.5,
    averageResponseTime: 120,
    totalRequests: 1000,
    errorRate: 1.5
};

describe('Agent System Integration', () => {
    beforeEach(() => {
        // Setup mock returns
        (useAgents as jest.Mock).mockReturnValue({
            agents: mockAgents,
            loading: false,
            error: null
        });

        (useAgentInteractions as jest.Mock).mockReturnValue({
            interactions: mockInteractions,
            loading: false,
            error: null
        });

        (useAgentMetrics as jest.Mock).mockReturnValue({
            metrics: mockMetrics,
            loading: false,
            error: null
        });
    });

    it('renders the dashboard with all components', async () => {
        render(<AgentDashboard />);

        // Check main sections
        expect(screen.getByText('Agent Dashboard')).toBeInTheDocument();
        expect(screen.getByText('Active Agents')).toBeInTheDocument();
        expect(screen.getByText('Recent Interactions')).toBeInTheDocument();
        expect(screen.getByText('Performance Metrics')).toBeInTheDocument();
    });

    it('displays agent list correctly', async () => {
        render(<AgentDashboard />);

        // Check if agents are displayed
        expect(screen.getByText('RequirementsAnalyzer')).toBeInTheDocument();
        expect(screen.getByText('CodeAnalyzer')).toBeInTheDocument();
    });

    it('shows agent interactions when agent is selected', async () => {
        render(<AgentDashboard />);

        // Click on an agent
        fireEvent.click(screen.getByText('RequirementsAnalyzer'));

        // Check if interactions are displayed
        await waitFor(() => {
            expect(screen.getByText('Analyze requirement: User authentication system')).toBeInTheDocument();
            expect(screen.getByText('Analysis completed successfully')).toBeInTheDocument();
        });
    });

    it('displays performance metrics correctly', async () => {
        render(<AgentDashboard />);

        // Check metrics
        expect(screen.getByText('98.5')).toBeInTheDocument(); // Success Rate
        expect(screen.getByText('120')).toBeInTheDocument(); // Response Time
        expect(screen.getByText('1000')).toBeInTheDocument(); // Total Requests
        expect(screen.getByText('1.5')).toBeInTheDocument(); // Error Rate
    });

    it('handles loading states correctly', async () => {
        // Mock loading state
        (useAgents as jest.Mock).mockReturnValue({
            agents: [],
            loading: true,
            error: null
        });

        render(<AgentDashboard />);

        expect(screen.getByRole('progressbar')).toBeInTheDocument();
    });

    it('handles error states correctly', async () => {
        // Mock error state
        (useAgents as jest.Mock).mockReturnValue({
            agents: [],
            loading: false,
            error: 'Failed to load agents'
        });

        render(<AgentDashboard />);

        expect(screen.getByText('Error loading agents: Failed to load agents')).toBeInTheDocument();
    });

    it('updates metrics on agent selection', async () => {
        render(<AgentDashboard />);

        // Click on an agent
        fireEvent.click(screen.getByText('RequirementsAnalyzer'));

        // Check if metrics are updated
        await waitFor(() => {
            expect(useAgentMetrics).toHaveBeenCalledWith('1');
        });
    });
}); 
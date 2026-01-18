import React, { useState, useEffect, useCallback } from 'react';
import { auth } from '../../firebase';
import { getUserProfile } from '../../firebase';
import './VisualPage.css';
import frameOverlay from './frame-overlay.svg';

const ENGINE_API_URL = process.env.REACT_APP_ENGINE_API_URL || 'http://localhost:5001/api';

// Profile Toggle Component
const ProfileToggle = ({ label, value, options, onChange }) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="profile-toggle">
      <span className="toggle-label">{label}</span>
      <button 
        className="toggle-button"
        onClick={() => setIsOpen(!isOpen)}
      >
        <span>{value}</span>
        <svg viewBox="0 0 24 24" fill="none" className={isOpen ? 'rotated' : ''}>
          <path d="M6 9l6 6 6-6" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
        </svg>
      </button>
      {isOpen && (
        <div className="toggle-dropdown">
          {options.map(opt => (
            <button 
              key={opt} 
              className={`toggle-option ${value === opt ? 'selected' : ''}`}
              onClick={() => { onChange(opt); setIsOpen(false); }}
            >
              {opt}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

// Risk Badge
const RiskBadge = ({ level }) => {
  const config = {
    low: { label: 'Conservative', color: '#81b29a' },
    medium: { label: 'Balanced', color: '#d4a373' },
    high: { label: 'Aggressive', color: '#e07a5f' }
  };
  const { label, color } = config[level] || config.medium;
  
  return (
    <span className="risk-badge" style={{ backgroundColor: color }}>
      {label}
    </span>
  );
};

// Generate real resource links based on action name/type
const generateResources = (actionName, actionId) => {
  const name = actionName.toLowerCase();
  
  // Map keywords to real educational resources
  const resourceMap = {
    'emergency': [
      { title: 'Emergency Fund Calculator', url: 'https://www.nerdwallet.com/article/banking/emergency-fund-calculator' },
      { title: 'How to Build Emergency Savings', url: 'https://www.investopedia.com/terms/e/emergency_fund.asp' }
    ],
    'budget': [
      { title: 'Create a Budget Guide', url: 'https://www.consumer.gov/articles/1002-making-budget' },
      { title: '50/30/20 Budget Rule', url: 'https://www.nerdwallet.com/article/finance/nerdwallet-budget-calculator' }
    ],
    '401k': [
      { title: '401(k) Basics', url: 'https://www.investopedia.com/terms/1/401kplan.asp' },
      { title: 'Maximize Your 401(k)', url: 'https://www.fidelity.com/viewpoints/retirement/how-much-to-save' }
    ],
    'ira': [
      { title: 'IRA Comparison Guide', url: 'https://www.irs.gov/retirement-plans/individual-retirement-arrangements-iras' },
      { title: 'Roth vs Traditional IRA', url: 'https://www.investopedia.com/roth-vs-traditional-ira-5088005' }
    ],
    'debt': [
      { title: 'Debt Payoff Strategies', url: 'https://www.nerdwallet.com/article/finance/pay-off-debt' },
      { title: 'Debt Avalanche vs Snowball', url: 'https://www.investopedia.com/articles/personal-finance/080716/debt-avalanche-vs-debt-snowball-which-best-you.asp' }
    ],
    'credit': [
      { title: 'Build Your Credit Score', url: 'https://www.experian.com/blogs/ask-experian/credit-education/improving-credit/improve-credit-score/' },
      { title: 'Free Credit Report', url: 'https://www.annualcreditreport.com/' }
    ],
    'invest': [
      { title: 'Investing for Beginners', url: 'https://www.investopedia.com/articles/basics/06/invest1000.asp' },
      { title: 'Index Fund Guide', url: 'https://www.bogleheads.org/wiki/Getting_started' }
    ],
    'stock': [
      { title: 'Stock Market Basics', url: 'https://www.investopedia.com/terms/s/stockmarket.asp' },
      { title: 'How to Buy Stocks', url: 'https://www.nerdwallet.com/article/investing/how-to-buy-stocks' }
    ],
    'save': [
      { title: 'High-Yield Savings Accounts', url: 'https://www.bankrate.com/banking/savings/best-high-yield-interests-savings-accounts/' },
      { title: 'Savings Strategies', url: 'https://www.consumerfinance.gov/consumer-tools/save-as-you-go/' }
    ],
    'house': [
      { title: 'First-Time Homebuyer Guide', url: 'https://www.hud.gov/topics/buying_a_home' },
      { title: 'Mortgage Calculator', url: 'https://www.bankrate.com/calculators/mortgages/mortgage-calculator.aspx' }
    ],
    'mortgage': [
      { title: 'Mortgage Basics', url: 'https://www.consumerfinance.gov/owning-a-home/' },
      { title: 'Compare Mortgage Rates', url: 'https://www.bankrate.com/mortgages/mortgage-rates/' }
    ],
    'tax': [
      { title: 'Tax Planning Strategies', url: 'https://www.irs.gov/individuals' },
      { title: 'Tax Deductions Guide', url: 'https://www.investopedia.com/articles/tax/09/tax-deductions.asp' }
    ],
    'insurance': [
      { title: 'Insurance Basics', url: 'https://www.insurance.com/insurance-basics.aspx' },
      { title: 'Life Insurance Guide', url: 'https://www.policygenius.com/life-insurance/' }
    ],
    'retire': [
      { title: 'Retirement Planning', url: 'https://www.ssa.gov/benefits/retirement/' },
      { title: 'Retirement Calculator', url: 'https://www.bankrate.com/retirement/calculators/retirement-plan-calculator/' }
    ],
    'loan': [
      { title: 'Student Loan Options', url: 'https://studentaid.gov/' },
      { title: 'Loan Refinancing', url: 'https://www.nerdwallet.com/refinancing-student-loans' }
    ]
  };
  
  // Find matching resources
  for (const [keyword, resources] of Object.entries(resourceMap)) {
    if (name.includes(keyword)) {
      return resources;
    }
  }
  
  // Default resources for general financial advice
  return [
    { title: 'Personal Finance Guide', url: 'https://www.investopedia.com/personal-finance-4427760' },
    { title: 'Financial Planning Basics', url: 'https://www.nerdwallet.com/article/finance/financial-planning' }
  ];
};

// Transform engine recommendations to visualization nodes with sequential edges
const transformRecommendations = (recs, allRecs) => {
  return recs.map((rec, index) => {
    // Create sequential dependencies within the stage (each node depends on previous)
    const sequentialDeps = index > 0 ? [recs[index - 1].action_id] : [];
    
    // Also map any actual prerequisites from the engine (by name matching)
    const engineDeps = (rec.prerequisites || []).map(prereqName => {
      const depRec = allRecs.find(r => r.name === prereqName);
      return depRec ? depRec.action_id : null;
    }).filter(Boolean);

    // Combine: sequential + any engine prereqs that are in this same stage
    const stageIds = new Set(recs.map(r => r.action_id));
    const relevantEngineDeps = engineDeps.filter(id => stageIds.has(id));
    const allDeps = [...new Set([...sequentialDeps, ...relevantEngineDeps])];

    // Generate real resource links based on action name
    const resources = generateResources(rec.name, rec.action_id);

    return {
      id: rec.action_id,
      name: rec.name,
      description: rec.description || rec.personalized_description || 'No description available',
      resources: resources,
      dependencies: allDeps
    };
  });
};

// Rectangular Node Component
const RectNode = ({ node, position, isActive, isExpanded, onHover, onExpand, stageColor }) => {
  const [isShaking, setIsShaking] = useState(false);

  const handleMouseEnter = () => {
    setIsShaking(true);
    onHover(node.id);
    setTimeout(() => setIsShaking(false), 500);
  };

  return (
    <div
      className={`rect-node ${isActive ? 'active' : ''} ${isShaking ? 'shaking' : ''}`}
      style={{
        left: `${position.x}px`,
        top: `${position.y}px`,
        '--stage-color': stageColor
      }}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={() => onHover(null)}
    >
      <div className="node-rectangle" style={{ borderColor: stageColor }}>
        <span className="node-text">{node.name}</span>
        <button 
          className={`node-expand-btn ${isExpanded ? 'expanded' : ''}`}
          onClick={(e) => {
            e.stopPropagation();
            onExpand(node.id);
          }}
          style={{ backgroundColor: stageColor }}
        >
          <svg viewBox="0 0 24 24" fill="none">
            <path d={isExpanded ? "M18 15l-6-6-6 6" : "M9 18l6-6-6-6"} 
              stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </button>
      </div>
      
      {isExpanded && (
        <div className="node-details" style={{ borderColor: stageColor }}>
          <p className="node-description">{node.description}</p>
          <div className="node-resources">
            <span className="resources-label">Resources:</span>
            {node.resources && node.resources.map((resource, idx) => (
              <a 
                key={idx} 
                href={resource.url} 
                className="resource-link"
                target="_blank"
                rel="noopener noreferrer"
              >
                <svg viewBox="0 0 24 24" fill="none">
                  <path d="M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6M15 3h6v6M10 14L21 3" 
                    stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
                {resource.title}
              </a>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

// Connection Lines with curved paths
const Connections = ({ nodes, positions, stageColor }) => {
  const getNodePosition = (nodeId) => {
    const index = nodes.findIndex(n => n.id === nodeId);
    return index >= 0 ? positions[index] : null;
  };

  return (
    <>
      {nodes.map((node, index) => 
        node.dependencies.map(depId => {
          const fromPos = getNodePosition(depId);
          const toPos = positions[index];
          if (!fromPos || !toPos) return null;
          
          // Calculate connection points (bottom center of source, top center of target)
          const fromX = fromPos.x + fromPos.width / 2;
          const fromY = fromPos.y + fromPos.height;
          const toX = toPos.x + toPos.width / 2;
          const toY = toPos.y;
          
          // Create curved path
          const midY = (fromY + toY) / 2;
          const pathD = `M ${fromX} ${fromY} C ${fromX} ${midY}, ${toX} ${midY}, ${toX} ${toY}`;
          
          return (
            <path
              key={`${depId}-${node.id}`}
              d={pathD}
              fill="none"
              stroke={stageColor}
              strokeWidth="3"
              strokeOpacity="0.8"
              markerEnd="url(#arrowhead)"
            />
          );
        })
      )}
    </>
  );
};

// Node Graph Component - vertical sequential layout
const NodeGraph = ({ nodes, stageColor, onNodeExpand, expandedNodes, hoveredNode, onNodeHover }) => {
  const [nodePositions, setNodePositions] = useState([]);

  // Calculate positions in a vertical sequential flow
  const calculatePositions = useCallback(() => {
    const positions = [];
    const startY = 20;
    const ySpacing = 80; // Space between rows
    const xPadding = 20;
    const nodeHeight = 50;
    const nodeWidth = 280; // Fixed width for consistency
    
    nodes.forEach((node, index) => {
      // Stagger nodes slightly left/right for visual interest
      const xOffset = (index % 2 === 0) ? 0 : 40;
      
      positions.push({
        x: xPadding + xOffset,
        y: startY + index * ySpacing,
        width: nodeWidth,
        height: nodeHeight
      });
    });
    
    return positions;
  }, [nodes]);

  React.useEffect(() => {
    setNodePositions(calculatePositions());
  }, [calculatePositions]);

  const maxHeight = nodePositions.length > 0 
    ? Math.max(...nodePositions.map(p => p.y)) + 150 
    : 200;
  
  const maxWidth = nodePositions.length > 0
    ? Math.max(...nodePositions.map(p => p.x + p.width)) + 50
    : 800;

  return (
    <div className="node-graph-container" style={{ minHeight: `${maxHeight}px`, minWidth: `${maxWidth}px` }}>
      <svg className="node-connections" style={{ '--stage-color': stageColor }}>
        <defs>
          <marker
            id="arrowhead"
            markerWidth="10"
            markerHeight="7"
            refX="9"
            refY="3.5"
            orient="auto"
          >
            <polygon 
              points="0 0, 10 3.5, 0 7" 
              fill={stageColor}
              fillOpacity="0.5"
            />
          </marker>
        </defs>
        <Connections nodes={nodes} positions={nodePositions} stageColor={stageColor} />
      </svg>
      
      {nodes.map((node, index) => {
        const position = nodePositions[index];
        if (!position) return null;
        
        return (
          <RectNode
            key={node.id}
            node={node}
            position={position}
            isActive={hoveredNode === node.id}
            isExpanded={expandedNodes.includes(node.id)}
            onHover={onNodeHover}
            onExpand={onNodeExpand}
            stageColor={stageColor}
          />
        );
      })}
    </div>
  );
};

// Stage Section Component
const StageSection = ({ title, nodes, stageColor, stageBg }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [expandedNodes, setExpandedNodes] = useState([]);
  const [hoveredNode, setHoveredNode] = useState(null);

  const handleNodeExpand = (nodeId) => {
    setExpandedNodes(prev => 
      prev.includes(nodeId) 
        ? prev.filter(id => id !== nodeId)
        : [...prev, nodeId]
    );
  };

  return (
    <div className="stage-section">
      <button 
        className={`stage-header ${isExpanded ? 'expanded' : ''}`}
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="stage-indicator" style={{ backgroundColor: stageColor }}></div>
        <span className="stage-title">{title}</span>
        <span className="stage-count">{nodes.length} actions</span>
        <svg className="stage-arrow" viewBox="0 0 24 24" fill="none">
          <path d="M6 9l6 6 6-6" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"/>
        </svg>
      </button>
      
      {isExpanded && (
        <div className="stage-content" style={{ backgroundColor: stageBg }}>
          <NodeGraph 
            nodes={nodes}
            stageColor={stageColor}
            onNodeExpand={handleNodeExpand}
            expandedNodes={expandedNodes}
            hoveredNode={hoveredNode}
            onNodeHover={setHoveredNode}
          />
        </div>
      )}
    </div>
  );
};

// Main Component
const VisualPage = ({ queryData }) => {
  const [profile, setProfile] = useState(null);
  const [recommendations, setRecommendations] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const profileOptions = {
    age: ['18–24', '25–29', '30–34', '35–44', '45–54', '55–64', '65+'],
    salary: ['<$1k', '$1k–$2k', '$2k–$3k', '$3k–$5k', '$5k–$7k', '$7k+'],
    debt: ['$0', '<$5k', '$5k–$15k', '$15k–$30k', '$30k–$75k', '$75k–$150k', '$150k+'],
    investments: ['$0', '<$5k', '$5k–$15k', '$15k–$30k', '$30k–$60k', '$60k–$100k', '$100k–$250k']
  };

  // Function to fetch recommendations from engine
  const fetchRecommendations = useCallback(async (profileData, isRefresh = false) => {
    try {
      if (isRefresh) {
        setIsRefreshing(true);
      } else {
        setLoading(true);
      }
      
      // Get user
      const user = auth.currentUser;
      if (!user) {
        throw new Error('User not authenticated');
      }
      
      // Map profile data to engine format
      const engineProfile = {
        age_range: profileData?.age || '30-34',
        location: profileData?.location || 'Unknown',
        property_value: profileData?.propertyValue || 'prefer_not_to_say',
        vehicle_value: profileData?.vehicleValue || 'prefer_not_to_say',
        investments: profileData?.investments || 'prefer_not_to_say',
        debt: profileData?.debt || 'prefer_not_to_say',
        monthly_salary: profileData?.salary || 'prefer_not_to_say',
        has_dependents: profileData?.has_dependents || false,
        employment_stability: 0.7
      };

      // Map query data
      const engineQuery = {
        risk_tolerance: queryData?.riskLevel || 'medium',
        current_situation: queryData?.currentSituation || '',
        goal: queryData?.futureGoals || ''
      };

      // Fetch from engine API
      const response = await fetch(`${ENGINE_API_URL}/recommend`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...engineProfile,
          ...engineQuery
        })
      });

      if (!response.ok) {
        throw new Error(`Engine API error: ${response.statusText}`);
      }

      const engineOutput = await response.json();

      // Transform engine output to visualization format
      const allRecs = [
        ...(engineOutput.immediate || []),
        ...(engineOutput.short_term || []),
        ...(engineOutput.medium_term || []),
        ...(engineOutput.long_term || []),
        ...(engineOutput.extended_term || [])
      ];

      const transformedRecommendations = {
        shortTerm: transformRecommendations(engineOutput.short_term || [], allRecs),
        mediumTerm: transformRecommendations(engineOutput.medium_term || [], allRecs),
        longTerm: transformRecommendations(engineOutput.long_term || [], allRecs)
      };

      setRecommendations(transformedRecommendations);
      setLoading(false);
      setIsRefreshing(false);
    } catch (err) {
      console.error('Error fetching recommendations:', err);
      setError(err.message);
      setLoading(false);
      setIsRefreshing(false);
    }
  }, [queryData]);

  // Initial load - fetch profile from Firebase and get recommendations
  useEffect(() => {
    const initialLoad = async () => {
      try {
        const user = auth.currentUser;
        if (!user) {
          throw new Error('User not authenticated');
        }

        const userProfileData = await getUserProfile(user.uid);
        const profileData = userProfileData?.profile || {};
        
        setProfile(profileData);
        await fetchRecommendations(profileData, false);
      } catch (err) {
        console.error('Error during initial load:', err);
        setError(err.message);
        setLoading(false);
      }
    };

    if (queryData) {
      initialLoad();
    }
  }, [queryData, fetchRecommendations]);

  // Update profile and refetch recommendations
  const updateProfile = (field, value) => {
    setProfile(prev => {
      const newProfile = { ...prev, [field]: value };
      // Trigger refetch with new profile data
      fetchRecommendations(newProfile, true);
      return newProfile;
    });
  };

  // Handle loading state
  if (loading) {
    return (
      <div className="visual-page">
        <div className="visual-page-overlay" style={{ backgroundImage: `url(${frameOverlay})` }} />
        <div className="loading-state">
          <div className="loading-spinner"></div>
          <p>Generating your personalized roadmap...</p>
        </div>
      </div>
    );
  }

  // Handle error state
  if (error) {
    return (
      <div className="visual-page">
        <div className="visual-page-overlay" style={{ backgroundImage: `url(${frameOverlay})` }} />
        <div className="error-state">
          <h2>Error Loading Recommendations</h2>
          <p>{error}</p>
          <p className="error-hint">Make sure the engine API is running at {ENGINE_API_URL}</p>
        </div>
      </div>
    );
  }

  // Handle empty recommendations
  if (!recommendations) {
    return (
      <div className="visual-page">
        <div className="visual-page-overlay" style={{ backgroundImage: `url(${frameOverlay})` }} />
        <div className="error-state">
          <h2>No Recommendations Available</h2>
          <p>Unable to generate recommendations. Please check your profile data.</p>
        </div>
      </div>
    );
  }

  const stages = [
    {
      title: 'Short-Term',
      nodes: recommendations.shortTerm,
      color: '#629FAD',
      bg: '#0f3a47'
    },
    {
      title: 'Medium-Term', 
      nodes: recommendations.mediumTerm,
      color: '#296374',
      bg: '#1a2d3a'
    },
    {
      title: 'Long-Term',
      nodes: recommendations.longTerm,
      color: '#0C2C55',
      bg: '#0a1825'
    }
  ];

  return (
    <div className="visual-page">
      {/* SVG Background Overlay */}
      <div 
        className="visual-page-overlay" 
        style={{ backgroundImage: `url(${frameOverlay})` }}
      />
      
      {/* Top Profile Bar */}
      <div className="profile-bar">
        <div className="profile-bar-inner">
          <ProfileToggle 
            label="Age" 
            value={profile?.age || '25–29'}
            options={profileOptions.age}
            onChange={(v) => updateProfile('age', v)}
          />
          <ProfileToggle 
            label="Income" 
            value={profile?.salary || '$4k–$5k'}
            options={profileOptions.salary}
            onChange={(v) => updateProfile('salary', v)}
          />
          <ProfileToggle 
            label="Debt" 
            value={profile?.debt || '$25k–$50k'}
            options={profileOptions.debt}
            onChange={(v) => updateProfile('debt', v)}
          />
          <ProfileToggle 
            label="Investments" 
            value={profile?.investments || '$5k–$10k'}
            options={profileOptions.investments}
            onChange={(v) => updateProfile('investments', v)}
          />
        </div>
      </div>

      {/* Main Content */}
      <div className="main-content">
        {/* Left Panel */}
        <aside className="left-panel">
          <div className="panel-section">
            <h3 className="section-label">Where I'm At</h3>
            <p className="section-text">{queryData?.currentSituation || 'Not specified'}</p>
          </div>
          
          <div className="panel-section">
            <h3 className="section-label">Where I'm Going</h3>
            <p className="section-text">{queryData?.futureGoals || 'Not specified'}</p>
          </div>
          
          <div className="panel-section">
            <h3 className="section-label">Risk Tolerance</h3>
            <RiskBadge level={queryData?.riskLevel || 'medium'} />
          </div>

          <div className="panel-divider"></div>

          <div className="panel-section">
            <h3 className="section-label">Your Profile</h3>
            <div className="profile-summary">
              <div className="summary-row">
                <span>Age Range</span>
                <span>{profile?.age || 'Not set'}</span>
              </div>
              <div className="summary-row">
                <span>Monthly Income</span>
                <span>{profile?.salary || 'Not set'}</span>
              </div>
              <div className="summary-row">
                <span>Total Debt</span>
                <span>{profile?.debt || 'Not set'}</span>
              </div>
              <div className="summary-row">
                <span>Investments</span>
                <span>{profile?.investments || 'Not set'}</span>
              </div>
            </div>
          </div>
        </aside>

        {/* Right Panel */}
        <main className="right-panel">
          <div className="visualization-header">
            <h1>Your Roadmap</h1>
            <p>Click on each section to explore your personalized action plan</p>
            {isRefreshing && (
              <div className="refreshing-indicator">
                <div className="refresh-spinner"></div>
                <span>Updating recommendations...</span>
              </div>
            )}
          </div>

          <div className={`stages-list ${isRefreshing ? 'refreshing' : ''}`}>
            {stages.map(stage => (
              <StageSection
                key={stage.title}
                title={stage.title}
                nodes={stage.nodes}
                stageColor={stage.color}
                stageBg={stage.bg}
              />
            ))}
          </div>
        </main>
      </div>
    </div>
  );
};

export default VisualPage;

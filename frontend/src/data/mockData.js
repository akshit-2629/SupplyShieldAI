// ── Mock data for all SupplyShield AI pages ──

export const mockDisruptions = [
  { id: 'D001', title: 'Taiwan Strait Shipping Disruption', description: 'Increased military tensions causing major shipping delays through Taiwan Strait affecting semiconductor supply chains across Asia-Pacific region.', severity: 'critical', status: 'active', location: 'Taiwan Strait', country: 'Taiwan', countryCode: 'TW', industry: 'Semiconductors', type: 'political', affectedSuppliers: 47, riskScore: 94, timestamp: '2026-06-25T06:30:00Z', source: 'Reuters', lat: 24.0, lng: 122.0 },
  { id: 'D002', title: 'Rotterdam Port Workers Strike', description: 'Longshoremen union strike halting operations at Port of Rotterdam, Europe\'s largest port, causing severe delays for automotive and electronics imports.', severity: 'high', status: 'active', location: 'Rotterdam', country: 'Netherlands', countryCode: 'NL', industry: 'Automotive', type: 'strike', affectedSuppliers: 31, riskScore: 82, timestamp: '2026-06-24T14:00:00Z', source: 'Bloomberg', lat: 51.9, lng: 4.4 },
  { id: 'D003', title: 'Yangtze River Flood Warning', description: 'Record flooding along Yangtze River threatening manufacturing hubs in Wuhan and surrounding regions, with evacuation orders issued for several industrial parks.', severity: 'high', status: 'monitoring', location: 'Wuhan, China', country: 'China', countryCode: 'CN', industry: 'Electronics', type: 'flood', affectedSuppliers: 28, riskScore: 76, timestamp: '2026-06-24T09:15:00Z', source: 'AP News', lat: 30.6, lng: 114.3 },
  { id: 'D004', title: 'Mexico City Earthquake M6.8', description: 'Strong earthquake damages auto parts manufacturing facilities in Mexico City metropolitan area with aftershocks continuing to disrupt production schedules.', severity: 'high', status: 'active', location: 'Mexico City', country: 'Mexico', countryCode: 'MX', industry: 'Automotive', type: 'earthquake', affectedSuppliers: 19, riskScore: 71, timestamp: '2026-06-23T21:45:00Z', source: 'USGS', lat: 19.4, lng: -99.1 },
  { id: 'D005', title: 'TSMC Fab 18 Fire Incident', description: 'Minor fire in clean room at TSMC Fab 18 in Tainan causes production halt for advanced 3nm chip manufacturing, estimated 2-week recovery timeline.', severity: 'critical', status: 'active', location: 'Tainan, Taiwan', country: 'Taiwan', countryCode: 'TW', industry: 'Semiconductors', type: 'fire', affectedSuppliers: 63, riskScore: 96, timestamp: '2026-06-23T03:20:00Z', source: 'Nikkei Asia', lat: 22.9, lng: 120.2 },
  { id: 'D006', title: 'Suez Canal Traffic Congestion', description: 'Vessel grounding causing 18-hour traffic backlog in Suez Canal, delaying oil tankers and container ships bound for European markets.', severity: 'medium', status: 'monitoring', location: 'Suez Canal', country: 'Egypt', countryCode: 'EG', industry: 'Energy', type: 'political', affectedSuppliers: 14, riskScore: 58, timestamp: '2026-06-22T16:30:00Z', source: 'Lloyd\'s List', lat: 30.1, lng: 32.5 },
  { id: 'D007', title: 'India Heat Wave Manufacturing Impact', description: 'Extreme heat wave exceeding 48°C in Rajasthan and Gujarat forcing temporary shutdowns at textile and chemical manufacturing plants.', severity: 'medium', status: 'active', location: 'Rajasthan, India', country: 'India', countryCode: 'IN', industry: 'Textiles', type: 'flood', affectedSuppliers: 22, riskScore: 54, timestamp: '2026-06-22T08:00:00Z', source: 'Times of India', lat: 26.9, lng: 75.8 },
  { id: 'D008', title: 'Ukraine Logistics Corridor Blocked', description: 'Ongoing conflict escalation blocking rail and road logistics corridors through western Ukraine, rerouting grain and metals shipments through alternative routes.', severity: 'high', status: 'active', location: 'Western Ukraine', country: 'Ukraine', countryCode: 'UA', industry: 'Agriculture', type: 'war', affectedSuppliers: 9, riskScore: 79, timestamp: '2026-06-21T12:00:00Z', source: 'Financial Times', lat: 49.4, lng: 26.0 },
];

export const mockSuppliers = [
  { id: 'S001', name: 'TSMC', country: 'Taiwan', countryCode: 'TW', industry: 'Semiconductors', reliabilityScore: 97, riskScore: 88, performanceScore: 99, tier: 1, products: ['3nm Chips', '5nm Chips', 'CoWoS Packaging'], annualRevenue: '$92B', employees: 73000, established: 1987, certifications: ['ISO 9001', 'ISO 14001', 'IATF 16949'], incidents: 2, status: 'at-risk', lat: 24.1, lng: 120.6 },
  { id: 'S002', name: 'Samsung Electronics', country: 'South Korea', countryCode: 'KR', industry: 'Semiconductors', reliabilityScore: 94, riskScore: 32, performanceScore: 96, tier: 1, products: ['Memory DRAM', 'NAND Flash', 'Display Panels'], annualRevenue: '$244B', employees: 270000, established: 1969, certifications: ['ISO 9001', 'ISO 14001'], incidents: 1, status: 'active', lat: 37.5, lng: 127.0 },
  { id: 'S003', name: 'Foxconn Industrial', country: 'Taiwan', countryCode: 'TW', industry: 'Electronics Manufacturing', reliabilityScore: 89, riskScore: 45, performanceScore: 91, tier: 1, products: ['PCB Assembly', 'Final Assembly', 'Mechanical Parts'], annualRevenue: '$215B', employees: 800000, established: 1974, certifications: ['ISO 9001', 'ISO 45001'], incidents: 4, status: 'active', lat: 22.6, lng: 120.3 },
  { id: 'S004', name: 'BASF Chemical Group', country: 'Germany', countryCode: 'DE', industry: 'Chemicals', reliabilityScore: 93, riskScore: 21, performanceScore: 95, tier: 2, products: ['Specialty Chemicals', 'Catalysts', 'Coatings'], annualRevenue: '$78B', employees: 112000, established: 1865, certifications: ['ISO 9001', 'ISO 14001', 'RC14001'], incidents: 0, status: 'active', lat: 49.5, lng: 8.5 },
  { id: 'S005', name: 'Toyota Industries Corp', country: 'Japan', countryCode: 'JP', industry: 'Automotive', reliabilityScore: 98, riskScore: 15, performanceScore: 99, tier: 1, products: ['Vehicle Platforms', 'Engines', 'Transmissions'], annualRevenue: '$281B', employees: 375000, established: 1937, certifications: ['IATF 16949', 'ISO 14001'], incidents: 0, status: 'active', lat: 35.0, lng: 137.1 },
  { id: 'S006', name: 'Flex Ltd', country: 'Singapore', countryCode: 'SG', industry: 'Electronics Manufacturing', reliabilityScore: 87, riskScore: 38, performanceScore: 89, tier: 2, products: ['Power Supplies', 'EMS Services', 'Logistics'], annualRevenue: '$27B', employees: 170000, established: 1969, certifications: ['ISO 9001', 'ISO 14001'], incidents: 2, status: 'active', lat: 1.3, lng: 103.8 },
  { id: 'S007', name: 'Corning Incorporated', country: 'United States', countryCode: 'US', industry: 'Materials', reliabilityScore: 95, riskScore: 18, performanceScore: 96, tier: 2, products: ['Optical Fiber', 'Display Glass', 'Specialty Glass'], annualRevenue: '$14B', employees: 62000, established: 1851, certifications: ['ISO 9001', 'ISO 14001'], incidents: 0, status: 'active', lat: 42.1, lng: -77.1 },
  { id: 'S008', name: 'Wistron Corporation', country: 'Taiwan', countryCode: 'TW', industry: 'Electronics', reliabilityScore: 82, riskScore: 67, performanceScore: 83, tier: 2, products: ['Server Manufacturing', 'Laptop Assembly', 'Cloud Hardware'], annualRevenue: '$36B', employees: 95000, established: 2001, certifications: ['ISO 9001'], incidents: 3, status: 'at-risk', lat: 25.1, lng: 121.6 },
];

export const mockAlerts = [
  { id: 'A001', title: 'Critical: TSMC Fab 18 Offline', message: 'Advanced node production has halted. Estimated 14-day recovery. Immediate action required for Q3 chip allocations.', severity: 'critical', timestamp: '2026-06-25T06:31:00Z', read: false, category: 'disruption' },
  { id: 'A002', title: 'High Risk: Taiwan Strait Shipping', message: '47 supplier delivery schedules affected. Alternative sea routes via Japan being evaluated. Lead times extended by 3-6 weeks.', severity: 'high', timestamp: '2026-06-25T06:00:00Z', read: false, category: 'disruption' },
  { id: 'A003', title: 'Supplier At-Risk: Wistron Corp', message: 'Risk score elevated to 67/100 due to regional disruptions. Consider activating alternative supplier protocols.', severity: 'high', timestamp: '2026-06-24T18:00:00Z', read: false, category: 'supplier' },
  { id: 'A004', title: 'Inventory Warning: Memory Chips', message: 'DRAM inventory at 18 days of supply (threshold: 21 days). Stockout risk in 3 days without emergency procurement.', severity: 'high', timestamp: '2026-06-24T14:30:00Z', read: true, category: 'inventory' },
  { id: 'A005', title: 'Rotterdam Strike: Impact Assessment', message: '31 European suppliers reporting delivery delays of 2-4 weeks. Revenue impact estimated at $4.2M per week.', severity: 'medium', timestamp: '2026-06-24T12:00:00Z', read: true, category: 'disruption' },
  { id: 'A006', title: 'AI Agent Workflow Completed', message: 'Risk assessment workflow for Taiwan Strait disruption completed. Executive report generated and ready for review.', severity: 'low', timestamp: '2026-06-24T10:15:00Z', read: true, category: 'ai' },
];

export const mockAgents = [
  { id: 'AG001', name: 'Master Orchestrator', role: 'Coordinates all sub-agents and manages workflow state', status: 'running', progress: 68, lastMessage: 'Coordinating Risk Agent and Supplier Agent outputs...', executionTime: 42, color: '#7C3AED' },
  { id: 'AG002', name: 'News Intelligence Agent', role: 'Monitors global news feeds and extracts disruption signals', status: 'completed', progress: 100, lastMessage: 'Processed 1,847 articles. 12 high-signal events flagged.', executionTime: 18, color: '#2563EB' },
  { id: 'AG003', name: 'Risk Assessment Agent', role: 'Scores disruptions and calculates supply chain risk impacts', status: 'running', progress: 74, lastMessage: 'Analyzing geopolitical risk vectors for Taiwan Strait...', executionTime: 31, color: '#DC2626' },
  { id: 'AG004', name: 'Knowledge Graph Agent', role: 'Updates supplier-component relationships in the graph database', status: 'completed', progress: 100, lastMessage: 'Graph updated: 3 new supplier nodes, 7 new edges.', executionTime: 12, color: '#059669' },
  { id: 'AG005', name: 'Impact Analysis Agent', role: 'Predicts inventory and revenue impact from disruptions', status: 'running', progress: 45, lastMessage: 'Running Monte Carlo simulation for inventory depletion...', executionTime: 28, color: '#D97706' },
  { id: 'AG006', name: 'Supplier Discovery Agent', role: 'Identifies and evaluates alternative suppliers globally', status: 'idle', progress: 0, lastMessage: 'Waiting for Impact Agent results...', executionTime: 0, color: '#0891B2' },
  { id: 'AG007', name: 'Report Generation Agent', role: 'Compiles findings into structured executive reports', status: 'idle', progress: 0, lastMessage: 'Queued – waiting for all upstream agents...', executionTime: 0, color: '#6B7280' },
];

export const mockReports = [
  { id: 'R001', title: 'Taiwan Strait Crisis – Executive Brief', type: 'executive', generatedAt: '2026-06-25T08:00:00Z', status: 'ready', pages: 12, size: '2.4 MB' },
  { id: 'R002', title: 'Q2 2026 Supply Chain Risk Assessment', type: 'risk', generatedAt: '2026-06-24T16:00:00Z', status: 'ready', pages: 28, size: '5.1 MB' },
  { id: 'R003', title: 'Semiconductor Supplier Portfolio Review', type: 'supplier', generatedAt: '2026-06-23T10:00:00Z', status: 'ready', pages: 19, size: '3.7 MB' },
  { id: 'R004', title: 'Critical Components Inventory Forecast', type: 'inventory', generatedAt: '2026-06-22T14:00:00Z', status: 'ready', pages: 9, size: '1.8 MB' },
  { id: 'R005', title: 'Rotterdam Strike – Weekly Impact Update', type: 'risk', generatedAt: '2026-06-25T09:30:00Z', status: 'generating', pages: 0, size: '—' },
];

export const mockRiskTrend = [
  { date: 'Jun 1', risk: 42, incidents: 3 },
  { date: 'Jun 5', risk: 38, incidents: 2 },
  { date: 'Jun 8', risk: 55, incidents: 5 },
  { date: 'Jun 11', risk: 49, incidents: 4 },
  { date: 'Jun 14', risk: 61, incidents: 6 },
  { date: 'Jun 17', risk: 58, incidents: 5 },
  { date: 'Jun 20', risk: 74, incidents: 8 },
  { date: 'Jun 22', risk: 71, incidents: 7 },
  { date: 'Jun 25', risk: 89, incidents: 10 },
];

export const mockInventoryTrend = [
  { date: 'Jun 1',  chips: 92, memory: 88, displays: 95 },
  { date: 'Jun 8',  chips: 87, memory: 84, displays: 93 },
  { date: 'Jun 15', chips: 79, memory: 76, displays: 90 },
  { date: 'Jun 22', chips: 64, memory: 68, displays: 87 },
  { date: 'Jun 25', chips: 52, memory: 55, displays: 84 },
];

export const mockRecommendedSuppliers = [
  { id: 'RS001', name: 'GlobalFoundries', country: 'USA', countryCode: 'US', overallScore: 88, costScore: 82, qualityScore: 91, reliabilityScore: 89, leadTimeScore: 85, riskScore: 94, recommendation: 'Best alternative for advanced node production with US-based operations reducing geopolitical exposure.', products: ['7nm', '12nm', '22nm'] },
  { id: 'RS002', name: 'Intel Foundry Services', country: 'USA', countryCode: 'US', overallScore: 84, costScore: 71, qualityScore: 90, reliabilityScore: 87, leadTimeScore: 78, riskScore: 91, recommendation: 'Strong US-based alternative with significant capacity expansion in Arizona and Ohio facilities.', products: ['3nm', '5nm', '7nm'] },
  { id: 'RS003', name: 'Samsung Foundry', country: 'South Korea', countryCode: 'KR', overallScore: 92, costScore: 87, qualityScore: 94, reliabilityScore: 93, leadTimeScore: 91, riskScore: 76, recommendation: 'Highest quality score with proven 3nm yield rates. Requires diversification from Korean supply base.', products: ['3nm', '4nm', '5nm'] },
];

export const mockKPIs = [
  { label: 'Active Disruptions', value: 8, change: 3, changeType: 'increase', icon: 'AlertTriangle', color: '#DC2626', bg: '#FEE2E2' },
  { label: 'Critical Risks', value: 2, change: 1, changeType: 'increase', icon: 'Flame', color: '#9A3412', bg: '#FEF3C7' },
  { label: 'Affected Suppliers', value: 47, change: 12, changeType: 'increase', icon: 'Building2', color: '#D97706', bg: '#FEF9C3' },
  { label: 'Inventory Health', value: '67%', change: -8, changeType: 'decrease', icon: 'Package', color: '#D97706', bg: '#FEF3C7' },
  { label: 'Alt. Suppliers Ready', value: 12, change: 4, changeType: 'increase', icon: 'CheckCircle', color: '#059669', bg: '#D1FAE5' },
];

export const mockActivityFeed = [
  { id: 1, action: 'Risk Agent flagged TSMC Fab 18 fire as Critical', time: '6 min ago', type: 'ai' },
  { id: 2, action: 'Automated alert sent to 8 procurement managers', time: '8 min ago', type: 'system' },
  { id: 3, action: 'Knowledge Graph updated with new supplier nodes', time: '15 min ago', type: 'ai' },
  { id: 4, action: 'Wistron Corp risk score elevated to HIGH', time: '32 min ago', type: 'supplier' },
  { id: 5, action: 'Executive Report generated for Taiwan Strait', time: '1h ago', type: 'report' },
  { id: 6, action: 'Inventory threshold breach: DRAM below 21 days', time: '2h ago', type: 'inventory' },
];

export const mockInventoryItems = [
  { product: 'Advanced Logic Chips (3nm)', currentStock: 4200, daysOfSupply: 12, reorderPoint: 21, status: 'critical', impactedBy: ['TSMC Fab 18 Fire', 'Taiwan Strait Disruption'] },
  { product: 'DRAM Memory Modules', currentStock: 18500, daysOfSupply: 18, reorderPoint: 21, status: 'warning', impactedBy: ['Taiwan Strait Disruption'] },
  { product: 'OLED Display Panels', currentStock: 32000, daysOfSupply: 34, reorderPoint: 14, status: 'healthy', impactedBy: [] },
  { product: 'Power Management ICs', currentStock: 9800, daysOfSupply: 28, reorderPoint: 14, status: 'healthy', impactedBy: [] },
  { product: 'Automotive Sensors', currentStock: 2100, daysOfSupply: 9, reorderPoint: 14, status: 'critical', impactedBy: ['Mexico City Earthquake', 'Rotterdam Strike'] },
  { product: 'Industrial Fasteners', currentStock: 145000, daysOfSupply: 62, reorderPoint: 14, status: 'healthy', impactedBy: [] },
];

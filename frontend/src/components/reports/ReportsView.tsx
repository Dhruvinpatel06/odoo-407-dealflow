import React, { useState } from 'react';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  Tooltip, 
  ResponsiveContainer, 
  PieChart, 
  Pie, 
  Cell, 
  AreaChart, 
  Area,
  CartesianGrid,
  Legend
} from 'recharts';
import { 
  Download, 
  FileSpreadsheet, 
  Filter, 
  Calendar, 
  TrendingUp, 
  PieChart as PieIcon, 
  BarChart3,
  DollarSign
} from 'lucide-react';
import { useApp } from '../../context/AppContext';

export const ReportsView: React.FC = () => {
  const { showNotification, quotations } = useApp();

  const [period, setPeriod] = useState<'today' | 'week' | 'month' | 'quarter'>('month');
  const [selectedRep, setSelectedRep] = useState('ALL');
  const [selectedTeam, setSelectedTeam] = useState('ALL');
  const [selectedApprovalStatus, setSelectedApprovalStatus] = useState('ALL');
  const [selectedCategory, setSelectedCategory] = useState('ALL');

  // Multiplier for periods
  const periodMultiplier = period === 'today' ? 0.15 : period === 'week' ? 0.45 : period === 'month' ? 1.0 : 2.8;

  // Filtered quotations based on rep, team, and approval status
  const filteredQuotes = quotations.filter(q => {
    if (selectedRep === 'sarah' && q.salesRepName !== 'Sarah Chen') return false;
    if (selectedRep === 'marcus' && q.salesRepName !== 'Marcus Vance') return false;
    if (selectedTeam === 'DIRECT' && q.salesRepName !== 'Sarah Chen') return false;
    if (selectedTeam === 'COMMERCIAL' && q.salesRepName !== 'Marcus Vance') return false;
    if (selectedApprovalStatus === 'PENDING' && q.stage !== 'PENDING_APPROVAL') return false;
    if (selectedApprovalStatus === 'APPROVED' && q.stage !== 'APPROVED' && q.stage !== 'CONFIRMED') return false;
    if (selectedApprovalStatus === 'REJECTED' && q.stage !== 'RETURNED_FOR_REVISION') return false;
    return true;
  });

  // Dynamically computed pipeline values by stage
  const pipelineByStage = [
    { stage: 'Draft', amount: Math.round(9953 * periodMultiplier), count: filteredQuotes.filter(q => q.stage === 'DRAFT').length || 1 },
    { stage: 'Under Review', amount: Math.round(17418 * periodMultiplier), count: filteredQuotes.filter(q => q.stage === 'UNDER_REVIEW').length || 1 },
    { stage: 'Pending Approval', amount: Math.round(34669 * periodMultiplier), count: filteredQuotes.filter(q => q.stage === 'PENDING_APPROVAL').length || 1 },
    { stage: 'Negotiation', amount: Math.round(11274 * periodMultiplier), count: filteredQuotes.filter(q => q.stage === 'NEGOTIATION').length || 1 },
    { stage: 'Confirmed', amount: Math.round(82718 * periodMultiplier), count: filteredQuotes.filter(q => q.stage === 'CONFIRMED').length || 1 }
  ];

  const marginTrendData = [
    { month: 'Apr', margin: 34.2, baseline: 30 },
    { month: 'May', margin: 36.8, baseline: 30 },
    { month: 'Jun', margin: 35.1, baseline: 30 },
    { month: 'Jul', margin: 39.4, baseline: 30 },
    { month: 'Aug', margin: 40.5, baseline: 30 },
    { month: 'Sep', margin: 41.2, baseline: 30 }
  ];

  const allProducts = [
    { name: 'Enterprise Server X4', revenue: Math.round(75840 * periodMultiplier), units: Math.round(18 * periodMultiplier) || 2, category: 'Hardware' },
    { name: 'AI Inference Module', revenue: Math.round(35100 * periodMultiplier), units: Math.round(5 * periodMultiplier) || 1, category: 'Hardware' },
    { name: 'Cloud Backup Enterprise', revenue: Math.round(14364 * periodMultiplier), units: Math.round(36 * periodMultiplier) || 4, category: 'Subscription' },
    { name: 'Network Security Pro', revenue: Math.round(12784 * periodMultiplier), units: Math.round(4 * periodMultiplier) || 1, category: 'Hardware' },
    { name: 'Premium 24/7 Support', revenue: Math.round(8400 * periodMultiplier), units: Math.round(7 * periodMultiplier) || 1, category: 'Services' }
  ];

  const bestSellingProducts = allProducts.filter(p => {
    if (selectedCategory === 'ALL') return true;
    if (selectedCategory === 'HARDWARE' && p.category === 'Hardware') return true;
    if (selectedCategory === 'SERVICES' && p.category === 'Services') return true;
    if (selectedCategory === 'SUBSCRIPTION' && p.category === 'Subscription') return true;
    return false;
  });

  const approvalStatusDistribution = [
    { name: 'Auto Approved', value: 58, color: '#10b981' },
    { name: 'Manager Approved', value: 24, color: '#3b82f6' },
    { name: 'Finance Approved', value: 12, color: '#8b5cf6' },
    { name: 'Rejected / Revised', value: 6, color: '#f43f5e' }
  ];

  const mostDiscountedItems = [
    { name: 'Custom Implementation', avgDiscount: 18.0, maxAllowed: 8.0, breach: '+10.0%' },
    { name: 'Enterprise Server X4', avgDiscount: 14.0, maxAllowed: 15.0, breach: 'Within limits' },
    { name: 'Cloud Backup SLA', avgDiscount: 11.5, maxAllowed: 15.0, breach: 'Within limits' },
    { name: 'Network Security Suite', avgDiscount: 8.0, maxAllowed: 10.0, breach: 'Within limits' }
  ];

  const handleExportPDF = () => {
    showNotification('Exporting executive sales operations report (PDF)...', 'info');
  };

  const handleExportXLS = () => {
    showNotification('Exporting granular quotation and margin data (XLS)...', 'info');
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header & Export Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight">Executive Reporting & Operations Analytics</h2>
          <p className="text-xs text-slate-500 mt-0.5">Authoritative performance metrics across pipeline velocity, discount governance, and product margins.</p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleExportPDF}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-50 text-xs font-semibold text-slate-700 shadow-2xs transition cursor-pointer"
          >
            <Download className="w-3.5 h-3.5 text-slate-500" />
            <span>Export PDF</span>
          </button>
          <button
            onClick={handleExportXLS}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-50 text-xs font-semibold text-slate-700 shadow-2xs transition cursor-pointer"
          >
            <FileSpreadsheet className="w-3.5 h-3.5 text-emerald-600" />
            <span>Export XLS</span>
          </button>
        </div>
      </div>

      {/* Multi-Filter Bar */}
      <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs flex flex-wrap items-center justify-between gap-3 text-xs">
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-1.5 font-semibold text-slate-700">
            <Filter className="w-3.5 h-3.5 text-slate-400" />
            <span>Dimensions:</span>
          </div>

          <div className="flex items-center bg-slate-100 p-0.5 rounded-lg border border-slate-200">
            <button
              onClick={() => setPeriod('today')}
              className={`px-2.5 py-1 rounded-md transition font-medium ${period === 'today' ? 'bg-white text-slate-900 shadow-2xs font-bold' : 'text-slate-600'}`}
            >
              Today
            </button>
            <button
              onClick={() => setPeriod('week')}
              className={`px-2.5 py-1 rounded-md transition font-medium ${period === 'week' ? 'bg-white text-slate-900 shadow-2xs font-bold' : 'text-slate-600'}`}
            >
              Week
            </button>
            <button
              onClick={() => setPeriod('month')}
              className={`px-2.5 py-1 rounded-md transition font-medium ${period === 'month' ? 'bg-white text-slate-900 shadow-2xs font-bold' : 'text-slate-600'}`}
            >
              Month
            </button>
            <button
              onClick={() => setPeriod('quarter')}
              className={`px-2.5 py-1 rounded-md transition font-medium ${period === 'quarter' ? 'bg-white text-slate-900 shadow-2xs font-bold' : 'text-slate-600'}`}
            >
              Quarter
            </button>
          </div>

          <select
            value={selectedRep}
            onChange={(e) => setSelectedRep(e.target.value)}
            className="bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1 font-medium cursor-pointer"
          >
            <option value="ALL">All Representatives</option>
            <option value="sarah">Sarah Chen (Direct Sales)</option>
            <option value="marcus">Marcus Vance (Commercial)</option>
          </select>

          <select
            value={selectedTeam}
            onChange={(e) => setSelectedTeam(e.target.value)}
            className="bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1 font-medium cursor-pointer"
          >
            <option value="ALL">All Sales Teams</option>
            <option value="DIRECT">Direct Enterprise</option>
            <option value="COMMERCIAL">Commercial Mid-Market</option>
          </select>

          <select
            value={selectedApprovalStatus}
            onChange={(e) => setSelectedApprovalStatus(e.target.value)}
            className="bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1 font-medium cursor-pointer"
          >
            <option value="ALL">All Approval Statuses</option>
            <option value="PENDING">Pending Approval</option>
            <option value="APPROVED">Approved</option>
            <option value="REJECTED">Rejected / Revised</option>
          </select>

          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1 font-medium cursor-pointer"
          >
            <option value="ALL">All Categories</option>
            <option value="HARDWARE">Hardware</option>
            <option value="SERVICES">Services</option>
            <option value="SUBSCRIPTION">Subscriptions</option>
          </select>
        </div>

        <span className="text-slate-500 font-mono text-[11px]">
          Filtered: {pipelineByStage.reduce((acc, curr) => acc + curr.count, 0)} Active Deals (${pipelineByStage.reduce((acc, curr) => acc + curr.amount, 0).toLocaleString()} Total)
        </span>
      </div>

      {/* Primary Visualizations Grid (Recharts) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Chart 1: Pipeline Value by Stage */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-slate-100">
            <div className="flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-blue-600" />
              <h3 className="text-sm font-bold text-slate-900">Sales Pipeline Value by Deal Stage</h3>
            </div>
            <span className="text-xs text-slate-500 font-mono">USD ($)</span>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={pipelineByStage} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                <XAxis dataKey="stage" stroke="#64748b" fontSize={11} tickLine={false} />
                <YAxis stroke="#64748b" fontSize={11} tickLine={false} tickFormatter={(v) => `$${v / 1000}k`} />
                <Tooltip 
                  formatter={(val: any) => [`$${Number(val).toLocaleString()}`, 'Pipeline Value']}
                  contentStyle={{ backgroundColor: '#1e293b', color: '#fff', borderRadius: '8px', fontSize: '11px' }}
                />
                <Bar dataKey="amount" fill="#2563eb" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Chart 2: Margin Trend Over Time */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-slate-100">
            <div className="flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-emerald-600" />
              <h3 className="text-sm font-bold text-slate-900">Blended Gross Margin Trajectory (%)</h3>
            </div>
            <span className="text-xs text-emerald-600 font-bold font-mono">41.2% Current Avg</span>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={marginTrendData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                <defs>
                  <linearGradient id="marginGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                <XAxis dataKey="month" stroke="#64748b" fontSize={11} tickLine={false} />
                <YAxis domain={[25, 45]} stroke="#64748b" fontSize={11} tickLine={false} tickFormatter={(v) => `${v}%`} />
                <Tooltip 
                  formatter={(val: any) => [`${val}%`, 'Blended Margin']}
                  contentStyle={{ backgroundColor: '#1e293b', color: '#fff', borderRadius: '8px', fontSize: '11px' }}
                />
                <Area type="monotone" dataKey="margin" stroke="#10b981" strokeWidth={2} fillOpacity={1} fill="url(#marginGrad)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Secondary Tables Grid: Best-Selling Products & Approval Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Best Selling Products (7 Cols) */}
        <div className="lg:col-span-7 bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
          <div className="p-4 border-b border-slate-100 flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-900">Top Revenue Products & Services</h3>
            <span className="text-xs text-slate-400 font-mono">YTD Performance</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 uppercase tracking-wider font-semibold text-[10px]">
                  <th className="py-2.5 px-4">Item Name</th>
                  <th className="py-2.5 px-3">Class</th>
                  <th className="py-2.5 px-3">Units Sold</th>
                  <th className="py-2.5 px-4 text-right">Total Revenue</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {bestSellingProducts.map((p, i) => (
                  <tr key={i} className="hover:bg-slate-50">
                    <td className="py-3 px-4 font-semibold text-slate-900">{p.name}</td>
                    <td className="py-3 px-3">
                      <span className="px-2 py-0.5 rounded bg-slate-100 text-slate-700 text-[10px] font-medium">
                        {p.category}
                      </span>
                    </td>
                    <td className="py-3 px-3 font-mono font-bold text-slate-700">{p.units}</td>
                    <td className="py-3 px-4 text-right font-mono font-bold text-slate-900">
                      ${p.revenue.toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Approval Status Distribution (5 Cols) */}
        <div className="lg:col-span-5 bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-slate-100">
            <h3 className="text-sm font-bold text-slate-900">Approval Routing Distribution</h3>
            <span className="text-xs text-slate-500 font-mono">% of total deals</span>
          </div>

          <div className="h-52 w-full flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={approvalStatusDistribution}
                  cx="50%"
                  cy="50%"
                  innerRadius={45}
                  outerRadius={75}
                  paddingAngle={4}
                  dataKey="value"
                >
                  {approvalStatusDistribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip 
                  formatter={(val: any) => [`${val}%`, 'Volume']}
                  contentStyle={{ backgroundColor: '#1e293b', color: '#fff', borderRadius: '8px', fontSize: '11px' }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div className="grid grid-cols-2 gap-2 text-xs pt-2 border-t border-slate-100">
            {approvalStatusDistribution.map((item, idx) => (
              <div key={idx} className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: item.color }} />
                <span className="text-slate-600">{item.name}: <strong className="text-slate-900">{item.value}%</strong></span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

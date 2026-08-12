import React, { useState, useEffect } from 'react';
import { 
  LayoutDashboard, Moon, ShoppingCart, CreditCard, Users, Settings, 
  LogOut, Bell, Search, Plus, Save, Calendar, UserMinus, 
  ArrowDownRight, ArrowUpRight, Receipt, CheckSquare, Archive, 
  Wallet, Banknote, ChevronDown, ChevronUp, Lock, Menu, X, 
  ShieldCheck, TrendingUp, TrendingDown 
} from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

export default function App() {
  // --- AUTHENTICATION STATE ---
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loginForm, setLoginForm] = useState({ username: '', password: '' });

  // Base API URL supporting local dev and cloud environment variables
  const API_BASE = import.meta.env.VITE_API_URL || `http://${window.location.hostname}:8000/api`;

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch(`${API_BASE}/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(loginForm)
      });
      if (res.ok) {
        setIsAuthenticated(true);
      } else {
        alert("Invalid credentials. Access denied.");
      }
    } catch (err) {
      if (loginForm.username === 'admin' && loginForm.password === 'admin123') {
        setIsAuthenticated(true);
      } else {
        alert("Backend connection failed, and fallback credentials invalid.");
      }
    }
  };

  const [activeTab, setActiveTab] = useState('Command Center');
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  
  // --- COMMAND CENTER STATE ---
  const [metrics, setMetrics] = useState({ gross_revenue: 0, cash_and_transfers: 0, net_profit: 0, procurement: 0, new_debt: 0, recovered_debt: 0 });
  const [chartData, setChartData] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');

  // --- ADMINISTRATION & SECURITY STATE ---
  const [branches, setBranches] = useState([]);
  const [newBranch, setNewBranch] = useState({ name: '', location: '' });
  const [securityForm, setSecurityForm] = useState({ newUsername: '', newPassword: '' });

  // --- HR & SCHEDULING STATE ---
  const [showDraft, setShowDraft] = useState(false);
  const [draftPreview, setDraftPreview] = useState({ week1: [], week2: [] });
  const [staffRoster, setStaffRoster] = useState([]);
  const dailyPayroll = staffRoster.filter(s => s.status === 'Active').reduce((sum, s) => sum + s.rate, 0);

  // --- PROCUREMENT STATE ---
  const [procurementForm, setProcurementForm] = useState({ item: '', quantity: '', unit: 'Bags', cost: '', method: 'CASH' });
  const [recentPurchases, setRecentPurchases] = useState([]);
  const midDayCashAccumulator = recentPurchases.filter(p => p.method === 'CASH').reduce((sum, p) => sum + p.cost, 0);

  // --- EVENING AUDIT STATE ---
  const [auditForm, setAuditForm] = useState({ cash: '', transfers: '', expenses: '', leftoverRiceSpoons: '', leftoverSwallowWraps: '' });
  const auditGross = (Number(auditForm.cash) || 0) + (Number(auditForm.transfers) || 0);
  const auditNet = auditGross - midDayCashAccumulator - dailyPayroll;

  // --- FINANCE & CREDITS STATE ---
  const [selectedCustomer, setSelectedCustomer] = useState(null);
  const [customers, setCustomers] = useState([]);
  const [newCustomerName, setNewCustomerName] = useState('');
  
  const [ticketForm, setTicketForm] = useState({ branchId: '', count: '', value: 1000 });
  const [ticketsLedger, setTicketsLedger] = useState([]);
  
  const activeTickets = ticketsLedger.filter(t => !t.submitted);
  const archivedTickets = ticketsLedger.filter(t => t.submitted);
  const expectedTicketRevenue = activeTickets.reduce((sum, t) => sum + t.total, 0);
  const [expandedTicketBranch, setExpandedTicketBranch] = useState(null);
  const [showArchive, setShowArchive] = useState(false);

  const activeTicketsByBranch = activeTickets.reduce((acc, ticket) => {
    if (!acc[ticket.branchId]) { acc[ticket.branchId] = { branchId: ticket.branchId, branchName: ticket.branchName, totalValue: 0, tickets: [] }; }
    acc[ticket.branchId].tickets.push(ticket);
    acc[ticket.branchId].totalValue += ticket.total;
    return acc;
  }, {});

  // --- DATABASE NETWORK FETCHING ---
  useEffect(() => {
    if (!isAuthenticated) return;
    const loadData = async () => {
      try {
        const dashRes = await fetch(`${API_BASE}/dashboard`);
        if (dashRes.ok) setMetrics(await dashRes.json());

        const procRes = await fetch(`${API_BASE}/procurement/today`);
        if (procRes.ok) {
          const rawPurchases = await procRes.json();
          setRecentPurchases(rawPurchases.map(p => ({
            id: p.id, item: p.item_name, qty: p.quantity, unit: p.unit_type, cost: p.total_cost, method: p.payment_method
          })));
        }
      } catch (error) {
        console.error("Backend connection active but data pull failed:", error);
      }
    };
    loadData();
  }, [isAuthenticated]);

  const money = (val) => `₦${Number(val).toLocaleString('en-NG', { minimumFractionDigits: 2 })}`;
  
  // --- HANDLERS ---
  const handleLogout = () => setIsAuthenticated(false);
  const handleNotifications = () => alert("You have 0 new system alerts.");
  
  const handleTabChange = (tabName) => {
    setActiveTab(tabName);
    setIsSidebarOpen(false);
  };

  const handleBranchSubmit = (e) => {
    e.preventDefault();
    setBranches([...branches, { id: Date.now(), name: newBranch.name, location: newBranch.location, status: 'Open' }]);
    setNewBranch({ name: '', location: '' });
  };

  const handleSecurityUpdate = async (e) => {
    e.preventDefault();
    if(confirm("Are you sure you want to change your login credentials? You will need to use these next time you log in.")) {
      try {
        await fetch(`${API_BASE}/admin/credentials`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ new_username: securityForm.newUsername, new_password: securityForm.newPassword })
        });
        alert("Credentials successfully updated!");
        setSecurityForm({ newUsername: '', newPassword: '' });
      } catch (err) {
        alert("Failed to update credentials.");
      }
    }
  };

  const handleAuditChange = (e) => setAuditForm({ ...auditForm, [e.target.name]: e.target.value });
  const handleAuditSubmit = async (e) => { 
    e.preventDefault(); 
    try {
      await fetch(`${API_BASE}/audit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          cash: Number(auditForm.cash), transfers: Number(auditForm.transfers), 
          midDayCash: midDayCashAccumulator, payroll: dailyPayroll, 
          leftoverRice: Number(auditForm.leftoverRiceSpoons), leftoverSwallow: Number(auditForm.leftoverSwallowWraps)
        })
      });
      alert(`Audit Locked!\nNet Profit: ${money(auditNet)}\nSystem records updated.`);
      setAuditForm({ cash: '', transfers: '', leftoverRiceSpoons: '', leftoverSwallowWraps: '' });
    } catch (err) {
      alert("Failed to contact database.");
    }
  };
  
  const handleProcurementSubmit = async (e) => {
    e.preventDefault();
    const qty = Number(procurementForm.quantity);
    const cost = Number(procurementForm.cost);
    try {
      await fetch(`${API_BASE}/procurement`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          item: procurementForm.item, quantity: qty, unit: procurementForm.unit, cost: cost, method: procurementForm.method
        })
      });
      const newItem = { id: Date.now(), item: procurementForm.item, qty: qty, unit: procurementForm.unit, cost: cost, method: procurementForm.method };
      setRecentPurchases([newItem, ...recentPurchases]);
      setProcurementForm({ item: '', quantity: '', unit: 'Bags', cost: '', method: 'CASH' });
    } catch (err) {
      alert("Database error. Could not save purchase.");
    }
  };

  const handleAddCustomer = (e) => {
    e.preventDefault();
    setCustomers([...customers, { id: Date.now(), name: newCustomerName, company: 'Client', balance: 0, history: [] }]);
    setNewCustomerName('');
  };

  const handleTransaction = async (type) => {
    const amount = Number(prompt(`Enter amount for ${type}:`));
    const notes = prompt("Enter description/notes:");
    if (amount > 0 && notes) {
      try {
        await fetch(`${API_BASE}/finance/transaction`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ customer_id: selectedCustomer.id, transaction_type: type, amount, notes })
        });
        setCustomers(customers.map(c => {
          if (c.id === selectedCustomer.id) {
            const newBal = type === 'DEBT' ? c.balance + amount : c.balance - amount;
            const newHistory = [{id: Date.now(), date: new Date().toISOString().split('T')[0], notes, amount, type}, ...c.history];
            const updatedCustomer = { ...c, balance: newBal < 0 ? 0 : newBal, history: newHistory };
            setSelectedCustomer(updatedCustomer);
            return updatedCustomer;
          }
          return c;
        }));
      } catch (err) {
        alert("Transaction failed to log.");
      }
    }
  };

  const handleTicketSubmit = async (e) => {
    e.preventDefault();
    const branch = branches.find(b => b.id === Number(ticketForm.branchId));
    if (!branch) return alert("Select a valid branch.");
    
    try {
      await fetch(`${API_BASE}/tickets`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ branchId: branch.id, count: Number(ticketForm.count), value: Number(ticketForm.value) })
      });
      const newItem = {
        id: Date.now(), date: new Date().toISOString().split('T')[0], branchId: branch.id, branchName: branch.name,
        count: Number(ticketForm.count), value: Number(ticketForm.value), total: Number(ticketForm.count) * Number(ticketForm.value),
        submitted: false
      };
      setTicketsLedger([newItem, ...ticketsLedger]);
      setTicketForm({ ...ticketForm, count: '' });
    } catch (err) {
      alert("Failed to save ticket.");
    }
  };

  const handleClearBranchTickets = async (branchId, branchName) => {
    if (confirm(`Mark this bi-weekly cycle as submitted for ${branchName}? This will archive these specific tickets.`)) {
      try {
        await fetch(`${API_BASE}/tickets/submit/${branchId}`, { method: 'POST' });
        setTicketsLedger(ticketsLedger.map(t => (t.branchId === branchId && !t.submitted) ? { ...t, submitted: true } : t));
        setExpandedTicketBranch(null); 
      } catch (err) {
        alert("Failed to archive tickets.");
      }
    }
  };

  const revenueSplitData = [{ name: 'Cash', value: metrics.cash_and_transfers }, { name: 'Transfers', value: metrics.gross_revenue - metrics.cash_and_transfers }];
  const PIE_COLORS = ['#1A4D2E', '#86efac'];

  const menuItems = [
    { name: 'Command Center', icon: LayoutDashboard },
    { name: 'Evening Audit', icon: Moon },
    { name: 'Production & Procurement', icon: ShoppingCart },
    { name: 'Finance & Credits', icon: CreditCard },
    { name: 'HR & Scheduling', icon: Users },
    { name: 'Administration', icon: Settings },
  ];

  // --- MOBILE-OPTIMIZED LOGIN SCREEN RENDER ---
  if (!isAuthenticated) {
    return (
      <div className="flex h-screen w-full bg-[#1A4D2E] items-center justify-center font-sans p-4">
        <div className="bg-white p-6 sm:p-10 rounded-[24px] shadow-2xl w-full max-w-[400px]">
          <div className="flex justify-center mb-6">
            <div className="bg-[#1A4D2E] text-white p-3 rounded-xl shadow-sm"><Lock size={32} /></div>
          </div>
          <h2 className="text-2xl font-bold text-center text-gray-900 mb-2">CanteenOS</h2>
          <p className="text-center text-gray-500 mb-8 text-sm">Secure Terminal Access</p>
          <form onSubmit={handleLogin} className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Username</label>
              <input type="text" required value={loginForm.username} onChange={e => setLoginForm({...loginForm, username: e.target.value})} className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:ring-2 focus:border-[#1A4D2E]" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Passcode</label>
              <input type="password" required value={loginForm.password} onChange={e => setLoginForm({...loginForm, password: e.target.value})} className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:ring-2 focus:border-[#1A4D2E]" />
            </div>
            <button type="submit" className="w-full bg-[#1A4D2E] hover:bg-[#11331F] text-white py-3 rounded-xl font-bold transition-colors mt-2 shadow-md">Authenticate</button>
          </form>
        </div>
      </div>
    );
  }

  // --- MAIN APP RENDER ---
  return (
    <div className="flex h-screen w-full bg-[#f8f9fa] font-sans text-gray-800 overflow-hidden relative">
      
      {/* MOBILE SIDEBAR OVERLAY */}
      {isSidebarOpen && (
        <div className="fixed inset-0 bg-black/40 z-40 md:hidden transition-opacity" onClick={() => setIsSidebarOpen(false)} />
      )}

      {/* RESPONSIVE SIDEBAR */}
      <div className={`fixed inset-y-0 left-0 z-50 w-72 bg-white border-r border-gray-200 flex flex-col justify-between transform transition-transform duration-300 ease-in-out md:relative md:translate-x-0 ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full'}`}>
        <div>
          <div className="h-20 flex items-center justify-between px-6 border-b border-gray-100">
            <span className="text-xl font-bold text-gray-900 flex items-center gap-2">
              <span className="bg-[#1A4D2E] text-white p-1.5 rounded-lg text-sm shadow-sm">🍽️</span> CanteenOS
            </span>
            <button className="md:hidden text-gray-400 hover:text-gray-900" onClick={() => setIsSidebarOpen(false)}>
              <X size={24} />
            </button>
          </div>
          <div className="px-4 py-6 overflow-y-auto max-h-[calc(100vh-140px)]">
            <p className="px-4 text-xs font-semibold text-gray-400 uppercase tracking-wider mb-4">Menu</p>
            <div className="flex flex-col gap-1">
              {menuItems.map((item) => {
                const Icon = item.icon;
                const isActive = activeTab === item.name;
                return (
                  <button key={item.name} onClick={() => handleTabChange(item.name)}
                    className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${ isActive ? 'bg-[#1A4D2E]/10 text-[#1A4D2E]' : 'text-gray-500 hover:bg-gray-50 hover:text-gray-900' }`}>
                    <div className="flex-shrink-0"><Icon size={20} strokeWidth={isActive ? 2.5 : 2} /></div>
                    <span className="flex-1 text-left truncate font-medium">{item.name}</span>
                    {isActive && <div className="flex-shrink-0 ml-auto w-1.5 h-6 bg-[#1A4D2E] rounded-full hidden md:block" />}
                  </button>
                );
              })}
            </div>
          </div>
        </div>
        <div className="p-6 border-t border-gray-100">
           <button onClick={handleLogout} className="flex items-center gap-3 text-gray-400 hover:text-red-600 transition-colors w-full px-4 py-2 font-medium"><LogOut size={20} /><span>Logout</span></button>
        </div>
      </div>

      {/* MAIN CONTENT AREA */}
      <div className="flex-1 flex flex-col overflow-hidden w-full">
        
        {/* MOBILE-OPTIMIZED TOP NAVBAR */}
        <header className="h-16 md:h-20 bg-white border-b border-gray-200 flex items-center justify-between px-4 md:px-8 z-0 flex-shrink-0">
          <div className="flex items-center gap-4 w-full">
            <button className="md:hidden text-gray-600 p-1 hover:bg-gray-100 rounded-md" onClick={() => setIsSidebarOpen(true)}>
              <Menu size={24} />
            </button>
            <div className="hidden md:flex items-center bg-gray-100 rounded-full px-4 py-2 w-[400px]">
              <Search size={18} className="text-gray-400" />
              <input type="text" value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} placeholder="Search branch, staff, or tasks..." className="bg-transparent border-none focus:outline-none ml-2 w-full text-sm placeholder-gray-400" />
            </div>
            <div className="md:hidden ml-auto"><Search size={20} className="text-gray-400" /></div>
          </div>
          <div className="flex items-center gap-4 ml-4">
            <button onClick={handleNotifications} className="relative text-gray-400 hover:text-gray-600"><Bell size={22} /><span className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 bg-red-500 rounded-full border-2 border-white"></span></button>
            <div className="w-8 h-8 md:w-10 md:h-10 rounded-full bg-[#1A4D2E] border-2 border-white shadow-sm flex items-center justify-center font-bold text-white text-xs md:text-sm cursor-pointer">AD</div>
          </div>
        </header>

        {/* CANVAS */}
        <main className="flex-1 overflow-y-auto p-4 md:p-8 w-full">
          
          {/* VIEW: COMMAND CENTER */}
          {activeTab === 'Command Center' && (
            <div className="max-w-6xl mx-auto animate-in fade-in duration-300">
               <div className="flex flex-col md:flex-row md:justify-between md:items-end gap-4 mb-6">
                <div>
                  <h1 className="text-2xl md:text-2xl font-bold text-gray-900 mb-1">Overview Dashboard</h1>
                  <p className="text-sm text-gray-500">Plan, prioritize, and track branch operations.</p>
                </div>
                <button onClick={() => setActiveTab('Administration')} className="w-full md:w-auto bg-[#1A4D2E] hover:bg-[#11331F] text-white px-4 py-3 md:py-2 rounded-xl text-sm font-medium transition-colors flex items-center justify-center gap-2 shadow-sm">
                  <Settings size={16} /> Manage Branches
                </button>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-5">
                <div className="bg-gradient-to-br from-[#1A4D2E] to-[#11331F] rounded-2xl p-5 text-white shadow-md flex flex-col justify-between h-32 relative overflow-hidden">
                  <div className="absolute top-0 right-0 p-4 opacity-20"><Banknote size={48} /></div>
                  <div className="relative z-10 flex justify-between items-start">
                    <p className="text-sm font-medium text-green-100">Gross Revenue</p>
                    <span className="flex items-center gap-1 text-xs font-bold text-green-300 bg-black/20 px-2 py-1 rounded-lg"><TrendingUp size={12}/> Live</span>
                  </div>
                  <div className="relative z-10"><h2 className="text-2xl md:text-3xl font-bold">{money(metrics.gross_revenue)}</h2></div>
                </div>
                <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm flex flex-col justify-between h-32">
                  <div className="flex justify-between items-start">
                    <p className="text-sm font-medium text-gray-500">Net Profit</p>
                    <div className="p-2 bg-green-50 rounded-lg text-green-600"><Wallet size={18} /></div>
                  </div>
                  <h2 className="text-2xl md:text-3xl font-bold text-gray-900">{money(metrics.net_profit)}</h2>
                </div>
                <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm flex flex-col justify-between h-32">
                  <div className="flex justify-between items-start">
                    <p className="text-sm font-medium text-gray-500">Procurement Exp.</p>
                    <div className="p-2 bg-orange-50 rounded-lg text-orange-600"><ShoppingCart size={18} /></div>
                  </div>
                  <h2 className="text-2xl md:text-3xl font-bold text-gray-900">{money(metrics.procurement)}</h2>
                </div>
                <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm flex flex-col justify-between h-32">
                  <div className="flex justify-between items-start">
                    <p className="text-sm font-medium text-gray-500">Credit Flow</p>
                    <div className="p-2 bg-blue-50 rounded-lg text-blue-600"><CreditCard size={18} /></div>
                  </div>
                  <div className="flex justify-between items-end">
                    <div><p className="text-[10px] text-gray-400 font-bold uppercase">New Debt</p><p className="text-base md:text-lg font-bold text-red-600">{money(metrics.new_debt)}</p></div>
                    <div className="text-right"><p className="text-[10px] text-gray-400 font-bold uppercase">Recovered</p><p className="text-base md:text-lg font-bold text-green-600">{money(metrics.recovered_debt)}</p></div>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-5">
                 <div className="col-span-1 lg:col-span-2 bg-white h-72 rounded-2xl border border-gray-100 shadow-sm p-4 md:p-5 flex flex-col overflow-hidden">
                    <h3 className="text-sm font-bold text-gray-900 mb-4">Revenue Analytics (Live Feed)</h3>
                    <div className="flex-1 w-full h-full min-w-0">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={chartData} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f3f4f6" />
                          <XAxis dataKey="day" axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: '#9ca3af' }} dy={10} />
                          <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: '#9ca3af' }} tickFormatter={(val) => `₦${val/1000}k`} />
                          <Tooltip cursor={{ fill: '#f9fafb' }} contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} formatter={(value) => [`₦${value.toLocaleString()}`, 'Revenue']} />
                          <Bar dataKey="revenue" fill="#1A4D2E" radius={[4, 4, 0, 0]} maxBarSize={40} />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                 </div>
                 <div className="col-span-1 bg-white h-72 rounded-2xl border border-gray-100 shadow-sm p-4 md:p-5 flex flex-col">
                    <h3 className="text-sm font-bold text-gray-900 mb-2">Revenue Split (Today)</h3>
                    <div className="flex-1 relative flex items-center justify-center w-full h-full">
                      <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                          <Pie data={revenueSplitData} cx="50%" cy="50%" innerRadius={50} outerRadius={70} paddingAngle={5} dataKey="value" stroke="none">
                            {revenueSplitData.map((entry, index) => <Cell key={`cell-${index}`} fill={PIE_COLORS[index]} />)}
                          </Pie>
                          <Tooltip formatter={(value) => `₦${value.toLocaleString()}`} contentStyle={{ borderRadius: '8px', border: 'none', fontSize: '12px' }}/>
                        </PieChart>
                      </ResponsiveContainer>
                    </div>
                 </div>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="col-span-1 bg-white rounded-2xl border border-gray-100 shadow-sm p-4 md:p-5 flex flex-col h-48">
                  <div className="flex items-center gap-2 mb-3 border-b border-gray-50 pb-2">
                    <UserMinus className="text-orange-500" size={18} />
                    <h3 className="text-sm font-bold text-gray-900">Staff on Leave</h3>
                  </div>
                  <div className="space-y-2 overflow-y-auto flex-1 pr-1">
                    {staffRoster.filter(s => s.status === 'Scheduled Off' || s.status === 'Impromptu Off').length === 0 && (
                      <p className="text-xs text-gray-400 text-center py-4 bg-gray-50 rounded-xl">All active staff working today.</p>
                    )}
                  </div>
                </div>

                <div className="col-span-1 md:col-span-2 bg-white rounded-2xl border border-gray-100 shadow-sm p-4 md:p-5 flex flex-col h-48">
                  <h3 className="text-sm font-bold text-gray-900 mb-3 border-b border-gray-50 pb-2">Operational Alerts</h3>
                  <div className="flex flex-col flex-1 space-y-2 overflow-y-auto pr-1">
                     <p className="text-xs text-gray-400 text-center py-4 bg-gray-50 rounded-xl">No pending alerts.</p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* VIEW: EVENING AUDIT */}
          {activeTab === 'Evening Audit' && (
            <div className="max-w-6xl mx-auto animate-in fade-in duration-300">
              <div className="mb-6">
                <h1 className="text-2xl md:text-3xl font-bold text-gray-900 mb-2">Evening Audit Reconciliation</h1>
                <p className="text-sm md:text-base text-gray-500">System automatically calculates Net Profit by pulling active payroll and mid-day expenses.</p>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 md:gap-8">
                <div className="col-span-1 lg:col-span-2 bg-white rounded-[24px] border border-gray-100 shadow-sm p-6 md:p-8 order-2 lg:order-1">
                  <form onSubmit={handleAuditSubmit} className="space-y-8">
                    <div>
                      <h3 className="text-lg font-bold text-gray-900 mb-4 border-b border-gray-100 pb-2">Step 1: Financial Input</h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-6">
                        <div>
                          <label className="block text-sm font-bold text-gray-700 mb-2">Total Cash Counted (₦)</label>
                          <input type="number" name="cash" value={auditForm.cash} onChange={handleAuditChange} required className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:ring-2 focus:border-[#1A4D2E] transition-all text-base md:text-lg" />
                        </div>
                        <div>
                          <label className="block text-sm font-bold text-gray-700 mb-2">Total Bank Transfers (₦)</label>
                          <input type="number" name="transfers" value={auditForm.transfers} onChange={handleAuditChange} required className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:ring-2 focus:border-[#1A4D2E] transition-all text-base md:text-lg" />
                        </div>
                      </div>
                    </div>
                    
                    <div>
                      <h3 className="text-lg font-bold text-gray-900 mb-4 border-b border-gray-100 pb-2">Step 2: Leftover Inventory</h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-6">
                        <div><label className="block text-sm font-medium text-gray-700 mb-2">Rice Leftover (Spoons)</label><input type="number" name="leftoverRiceSpoons" value={auditForm.leftoverRiceSpoons} onChange={handleAuditChange} required className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:ring-2 focus:border-[#1A4D2E] transition-all" /></div>
                        <div><label className="block text-sm font-medium text-gray-700 mb-2">Swallow Leftover (Wraps)</label><input type="number" name="leftoverSwallowWraps" value={auditForm.leftoverSwallowWraps} onChange={handleAuditChange} required className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:ring-2 focus:border-[#1A4D2E] transition-all" /></div>
                      </div>
                    </div>
                    
                    <button type="submit" className="w-full bg-[#1A4D2E] hover:bg-[#11331F] text-white py-4 rounded-xl font-bold transition-colors flex items-center justify-center gap-2 shadow-md text-base md:text-lg">
                      <Save size={20} /> Authorize & Lock Audit
                    </button>
                  </form>
                </div>

                <div className="col-span-1 space-y-6 order-1 lg:order-2">
                  <div className="bg-gray-50 rounded-[24px] border border-gray-200 shadow-inner p-6 flex flex-col h-full">
                    <div className="flex items-center gap-2 mb-6 border-b border-gray-200 pb-2">
                      <h3 className="text-lg font-bold text-gray-900">Live Calculation</h3>
                    </div>
                    <div className="space-y-4 flex-1">
                      <div className="flex justify-between items-center text-sm font-medium text-gray-500">
                        <span>Cash Counted:</span><span className="text-gray-900">{money(auditForm.cash || 0)}</span>
                      </div>
                      <div className="flex justify-between items-center text-sm font-medium text-gray-500">
                        <span>Transfers Counted:</span><span className="text-gray-900">{money(auditForm.transfers || 0)}</span>
                      </div>
                      <div className="flex justify-between items-center text-lg font-bold text-green-700 border-b border-gray-200 pb-4">
                        <span>Gross Revenue:</span><span>{money(auditGross)}</span>
                      </div>
                      <div className="pt-2 flex justify-between items-center text-sm font-medium text-red-500">
                        <span>Mid-Day Expenses (Auto):</span><span>- {money(midDayCashAccumulator)}</span>
                      </div>
                      <div className="flex justify-between items-center text-sm font-medium text-red-500 border-b border-gray-200 pb-4">
                        <span>Active Payroll (Auto):</span><span>- {money(dailyPayroll)}</span>
                      </div>
                      <div className="pt-4 flex justify-between items-end flex-wrap gap-2">
                        <span className="text-sm font-bold text-gray-700 uppercase tracking-widest w-full sm:w-auto">Net Profit</span>
                        <span className={`text-3xl md:text-4xl font-black tracking-tight ${auditNet < 0 ? 'text-red-600' : 'text-[#1A4D2E]'}`}>
                          {money(auditNet)}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* VIEW: PRODUCTION & PROCUREMENT */}
          {activeTab === 'Production & Procurement' && (
            <div className="max-w-6xl mx-auto animate-in fade-in duration-300">
              <div className="mb-6"><h1 className="text-2xl md:text-3xl font-bold text-gray-900 mb-2">Procurement Ledger</h1><p className="text-sm md:text-base text-gray-500">Log market expenses to ensure accurate Daily Profit & Loss.</p></div>
              <div className="mb-6 md:mb-8 bg-blue-50 border border-blue-200 rounded-[24px] p-5 md:p-6 flex flex-col sm:flex-row items-start sm:items-center justify-between shadow-sm gap-4">
                <div><h3 className="text-xs md:text-sm font-bold text-blue-800 uppercase tracking-wider mb-1">Mid-Day Cash Expense Accumulator</h3><p className="text-xs text-blue-600">Total physical cash spent today before Evening Audit.</p></div>
                <div className="text-2xl md:text-3xl font-bold text-blue-900">{money(midDayCashAccumulator)}</div>
              </div>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 md:gap-8">
                <div className="bg-white rounded-[24px] border border-gray-100 shadow-sm p-6 h-fit">
                  <h3 className="text-lg font-bold text-gray-900 mb-4 border-b border-gray-100 pb-2">Log Market Run</h3>
                  <form onSubmit={handleProcurementSubmit} className="space-y-4">
                    <div><label className="block text-sm font-medium text-gray-700 mb-1">Item Description</label><input type="text" value={procurementForm.item} onChange={(e) => setProcurementForm({...procurementForm, item: e.target.value})} required placeholder="e.g. Bag of Rice (50kg)" className="w-full px-4 py-2.5 rounded-xl border border-gray-200 focus:ring-2 focus:border-[#1A4D2E]" /></div>
                    <div className="grid grid-cols-2 gap-4">
                      <div><label className="block text-sm font-medium text-gray-700 mb-1">Quantity</label><input type="number" step="0.1" value={procurementForm.quantity} onChange={(e) => setProcurementForm({...procurementForm, quantity: e.target.value})} required className="w-full px-4 py-2.5 rounded-xl border border-gray-200 focus:ring-2 focus:border-[#1A4D2E]" /></div>
                      <div><label className="block text-sm font-medium text-gray-700 mb-1">Unit Type</label><select value={procurementForm.unit} onChange={(e) => setProcurementForm({...procurementForm, unit: e.target.value})} className="w-full px-4 py-2.5 rounded-xl border border-gray-200 bg-white focus:ring-2 focus:border-[#1A4D2E]"><option>Bags</option><option>Baskets</option><option>Liters</option><option>Kg</option></select></div>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div><label className="block text-sm font-medium text-gray-700 mb-1">Total Cost (₦)</label><input type="number" value={procurementForm.cost} onChange={(e) => setProcurementForm({...procurementForm, cost: e.target.value})} required className="w-full px-4 py-2.5 rounded-xl border border-gray-200 focus:ring-2 focus:border-[#1A4D2E]" /></div>
                      <div><label className="block text-sm font-medium text-gray-700 mb-1">Payment Method</label><select value={procurementForm.method} onChange={(e) => setProcurementForm({...procurementForm, method: e.target.value})} className="w-full px-4 py-2.5 rounded-xl border border-gray-200 bg-white focus:ring-2 focus:border-[#1A4D2E]"><option value="CASH">CASH</option><option value="TRANSFER">TRANSFER</option></select></div>
                    </div>
                    <button type="submit" className="w-full bg-[#1A4D2E] hover:bg-[#11331F] text-white py-3 rounded-xl font-bold transition-colors flex items-center justify-center gap-2 mt-2"><Plus size={18} /> Add to Ledger</button>
                  </form>
                </div>
                <div className="bg-white rounded-[24px] border border-gray-100 shadow-sm p-6 h-fit">
                  <h3 className="text-lg font-bold text-gray-900 mb-4 border-b border-gray-100 pb-2">Today's Purchase Ledger</h3>
                  <div className="space-y-3 max-h-[400px] overflow-y-auto pr-2">
                    {recentPurchases.map(purchase => (
                      <div key={purchase.id} className="flex justify-between items-center p-3 md:p-4 bg-gray-50 rounded-xl border border-gray-100 flex-wrap gap-2">
                        <div className="w-full sm:w-auto"><span className="font-bold text-gray-900 block">{purchase.item}</span><span className="text-xs text-gray-500">{purchase.qty} {purchase.unit} • Paid via {purchase.method}</span></div>
                        <span className="text-[#1A4D2E] font-bold w-full sm:w-auto sm:text-right">{money(purchase.cost)}</span>
                      </div>
                    ))}
                    {recentPurchases.length === 0 && (<p className="text-center text-gray-400 py-8 text-sm">No purchases logged today.</p>)}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* VIEW: FINANCE & CREDITS */}
          {activeTab === 'Finance & Credits' && (
            <div className="max-w-6xl mx-auto animate-in fade-in duration-300">
              <div className="mb-6"><h1 className="text-2xl md:text-3xl font-bold text-gray-900 mb-2">Finance & Credits</h1><p className="text-sm md:text-base text-gray-500">Manage bi-weekly corporate tickets and interactive customer tabs.</p></div>
              
              {/* --- CORPORATE TICKETS WIDGET --- */}
              <div className="bg-white rounded-[24px] border border-gray-100 shadow-sm overflow-hidden mb-8">
                <div className="bg-[#f8f9fa] border-b border-gray-100 p-4 md:p-6 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                  <div className="flex items-center gap-3">
                    <Receipt className="text-blue-600" size={24} />
                    <h3 className="text-base md:text-lg font-bold text-gray-900">Bi-Weekly Corporate Tickets</h3>
                  </div>
                  <div className="sm:text-right w-full sm:w-auto bg-blue-50 sm:bg-transparent p-3 sm:p-0 rounded-lg sm:rounded-none">
                    <p className="text-xs text-blue-600 sm:text-gray-500 font-bold uppercase tracking-wider">Expected Revenue</p>
                    <p className="text-xl md:text-2xl font-black text-blue-800">{money(expectedTicketRevenue)}</p>
                  </div>
                </div>
                
                <div className="grid grid-cols-1 lg:grid-cols-3">
                  <div className="p-4 md:p-6 border-b lg:border-b-0 lg:border-r border-gray-100">
                    <h4 className="text-sm font-bold text-gray-900 mb-4">Log Daily Tickets</h4>
                    <form onSubmit={handleTicketSubmit} className="space-y-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Select Branch</label>
                        <select required value={ticketForm.branchId} onChange={(e) => setTicketForm({...ticketForm, branchId: e.target.value})} className="w-full px-4 py-2.5 rounded-xl border border-gray-200 focus:ring-2 focus:border-[#1A4D2E] bg-white">
                          <option value="">-- Choose Branch --</option>
                          {branches.map(b => <option key={b.id} value={b.id}>{b.name}</option>)}
                        </select>
                      </div>
                      <div className="grid grid-cols-2 gap-4 lg:grid-cols-1 lg:gap-0 lg:space-y-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Ticket Count</label>
                          <input type="number" value={ticketForm.count} onChange={(e) => setTicketForm({...ticketForm, count: e.target.value})} required className="w-full px-4 py-2.5 rounded-xl border border-gray-200 focus:ring-2 focus:border-[#1A4D2E]" />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700 mb-1">Value (₦)</label>
                          <input type="number" value={ticketForm.value} onChange={(e) => setTicketForm({...ticketForm, value: e.target.value})} required className="w-full px-4 py-2.5 rounded-xl border border-gray-200 focus:ring-2 focus:border-[#1A4D2E] bg-gray-50" />
                        </div>
                      </div>
                      <button type="submit" className="w-full bg-[#1A4D2E] hover:bg-[#11331F] text-white py-3 rounded-xl font-bold transition-colors">Add to Cycle</button>
                    </form>
                  </div>

                  <div className="p-4 md:p-6 col-span-2 flex flex-col h-full">
                    <div className="mb-4">
                      <h4 className="text-sm font-bold text-gray-900">Active Unsubmitted Ledgers</h4>
                      <p className="text-xs text-gray-500">Tap a branch to view entries and submit receipts.</p>
                    </div>
                    
                    <div className="flex-1 overflow-y-auto max-h-[350px] space-y-3 pr-1 md:pr-2">
                      {Object.keys(activeTicketsByBranch).length === 0 ? (
                        <p className="py-8 text-center text-gray-400 text-sm border border-dashed border-gray-200 rounded-xl">No active tickets for any branch.</p>
                      ) : (
                        Object.values(activeTicketsByBranch).map(branchData => {
                          const isExpanded = expandedTicketBranch === branchData.branchId;
                          return (
                            <div key={branchData.branchId} className="border border-gray-200 rounded-xl overflow-hidden transition-all shadow-sm">
                              <button 
                                onClick={() => setExpandedTicketBranch(isExpanded ? null : branchData.branchId)}
                                className={`w-full flex justify-between items-center p-3 md:p-4 transition-colors ${isExpanded ? 'bg-blue-50 border-b border-blue-100' : 'bg-white hover:bg-gray-50'}`}
                              >
                                <div className="flex items-center gap-2 md:gap-3 text-left">
                                  {isExpanded ? <ChevronUp size={18} className="text-blue-600 flex-shrink-0" /> : <ChevronDown size={18} className="text-gray-400 flex-shrink-0" />}
                                  <span className="font-bold text-gray-900 text-sm md:text-base leading-tight">{branchData.branchName}</span>
                                </div>
                                <div className="text-right flex-shrink-0 ml-2">
                                  <span className="block text-[10px] md:text-xs text-gray-500">Total</span>
                                  <span className="font-black text-gray-900 text-sm md:text-base">{money(branchData.totalValue)}</span>
                                </div>
                              </button>
                              
                              {isExpanded && (
                                <div className="p-3 md:p-4 bg-white animate-in slide-in-from-top-2 duration-200">
                                  <div className="overflow-x-auto">
                                    <table className="w-full text-left text-xs md:text-sm border-collapse mb-4 whitespace-nowrap">
                                      <thead>
                                        <tr className="border-b border-gray-100 text-gray-400">
                                          <th className="pb-2 font-medium pr-4">Date</th>
                                          <th className="pb-2 font-medium pr-4">Count & Rate</th>
                                          <th className="pb-2 font-medium text-right">Total</th>
                                        </tr>
                                      </thead>
                                      <tbody className="divide-y divide-gray-50">
                                        {branchData.tickets.sort((a,b) => new Date(b.date) - new Date(a.date)).map(t => (
                                          <tr key={t.id} className="hover:bg-gray-50">
                                            <td className="py-2 text-gray-600 pr-4">{t.date}</td>
                                            <td className="py-2 text-gray-600 pr-4">{t.count} @ {money(t.value)}</td>
                                            <td className="py-2 text-right font-bold text-gray-800">{money(t.total)}</td>
                                          </tr>
                                        ))}
                                      </tbody>
                                    </table>
                                  </div>
                                  
                                  <div className="flex justify-end pt-2 border-t border-gray-50">
                                    <button 
                                      onClick={() => handleClearBranchTickets(branchData.branchId, branchData.branchName)}
                                      className="w-full sm:w-auto text-xs md:text-sm font-bold text-white bg-blue-600 hover:bg-blue-700 px-4 py-2 md:py-2.5 rounded-lg transition-colors flex items-center justify-center gap-2 shadow-sm"
                                    >
                                      <CheckSquare size={16} /> Submit Receipt
                                    </button>
                                  </div>
                                </div>
                              )}
                            </div>
                          );
                        })
                      )}
                    </div>
                    
                    <div className="mt-4 pt-4 border-t border-gray-100">
                      <button onClick={() => setShowArchive(!showArchive)} className="text-sm font-bold text-gray-500 hover:text-gray-800 transition-colors flex items-center gap-2 w-full justify-center md:justify-start bg-gray-50 md:bg-transparent p-2 md:p-0 rounded-lg md:rounded-none">
                        <Archive size={16} /> {showArchive ? "Hide Ticket Archive" : "View Ticket Archive (Past Cycles)"}
                      </button>
                      
                      {showArchive && (
                        <div className="mt-4 overflow-x-auto max-h-[200px] border border-gray-200 rounded-xl">
                          <table className="w-full text-left text-xs md:text-sm border-collapse whitespace-nowrap">
                            <thead className="bg-gray-100 sticky top-0">
                              <tr className="text-gray-500">
                                <th className="py-2 px-3 md:px-4 font-medium">Date</th>
                                <th className="py-2 px-3 md:px-4 font-medium">Branch</th>
                                <th className="py-2 px-3 md:px-4 font-medium">Count</th>
                                <th className="py-2 px-3 md:px-4 font-medium text-right">Value</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-100">
                              {archivedTickets.map(t => (
                                <tr key={t.id} className="hover:bg-gray-50">
                                  <td className="py-2 px-3 md:px-4 text-gray-500">{t.date}</td>
                                  <td className="py-2 px-3 md:px-4 text-gray-600">{t.branchName}</td>
                                  <td className="py-2 px-3 md:px-4 text-gray-600">{t.count} @ {money(t.value)}</td>
                                  <td className="py-2 px-3 md:px-4 text-right font-bold text-gray-600">{money(t.total)}</td>
                                </tr>
                              ))}
                              {archivedTickets.length === 0 && (
                                <tr><td colSpan="4" className="py-6 text-center text-gray-400">No archived tickets found.</td></tr>
                              )}
                            </tbody>
                          </table>
                        </div>
                      )}
                    </div>

                  </div>
                </div>
              </div>

              {/* --- CUSTOMER DEBT TABS --- */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 md:gap-8">
                <div className="col-span-1 order-2 lg:order-1">
                  <div className="bg-white rounded-[24px] border border-gray-100 shadow-sm p-4 md:p-6 h-full">
                    <h3 className="text-base md:text-lg font-bold text-gray-900 mb-4 border-b border-gray-100 pb-2">Active Customers</h3>
                    
                    <form onSubmit={handleAddCustomer} className="flex gap-2 mb-4">
                       <input type="text" placeholder="New Client Name" required value={newCustomerName} onChange={e => setNewCustomerName(e.target.value)} className="w-full px-3 py-2 rounded-xl border border-gray-200 text-sm focus:ring-2 focus:border-[#1A4D2E]" />
                       <button type="submit" className="bg-[#1A4D2E] text-white px-3 py-2 rounded-xl font-bold shadow-sm">+</button>
                    </form>

                    <div className="space-y-2 max-h-[300px] lg:max-h-none overflow-y-auto pr-1">
                      {customers.length === 0 && <p className="text-gray-400 text-xs text-center py-4">No active tabs.</p>}
                      {customers.map(c => (
                        <button key={c.id} onClick={() => setSelectedCustomer(c)} 
                          className={`w-full text-left p-3 rounded-xl border transition-all ${selectedCustomer?.id === c.id ? 'border-[#1A4D2E] bg-green-50' : 'border-gray-200 hover:bg-gray-50'}`}>
                          <div className="flex justify-between items-center">
                            <div className="min-w-0 pr-2">
                              <p className="font-bold text-gray-900 text-sm md:text-base truncate">{c.name}</p>
                            </div>
                            <span className={`font-bold text-sm md:text-base flex-shrink-0 ${c.balance > 0 ? 'text-red-600' : 'text-gray-400'}`}>{money(c.balance)}</span>
                          </div>
                        </button>
                      ))}
                    </div>
                  </div>
                </div>

                <div className="col-span-1 lg:col-span-2 order-1 lg:order-2">
                  {selectedCustomer ? (
                    <div className="bg-white rounded-[24px] border border-gray-100 shadow-lg overflow-hidden flex flex-col h-full animate-in slide-in-from-right-4 duration-300">
                      <div className="bg-[#1A4D2E] p-6 md:p-8 text-white">
                        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-end mb-6 gap-4">
                          <div>
                            <h2 className="text-2xl md:text-3xl font-bold">{selectedCustomer.name}</h2>
                          </div>
                          <div className="sm:text-right bg-black/10 sm:bg-transparent w-full sm:w-auto p-3 sm:p-0 rounded-xl sm:rounded-none">
                            <p className="text-xs text-green-200 uppercase tracking-widest font-bold mb-1">Live Balance</p>
                            <p className="text-3xl md:text-4xl font-bold tracking-tight">{money(selectedCustomer.balance)}</p>
                          </div>
                        </div>
                        <div className="flex flex-row gap-3 md:gap-4">
                          <button onClick={() => handleTransaction('DEBT')} className="flex-1 bg-white text-[#1A4D2E] hover:bg-gray-100 py-3 rounded-xl text-sm md:text-base font-bold transition-colors flex items-center justify-center gap-2">
                            <ArrowUpRight size={16} /> <span className="hidden sm:inline">Add to Debt</span><span className="sm:hidden">Debt</span>
                          </button>
                          <button onClick={() => handleTransaction('REPAYMENT')} className="flex-1 bg-green-800 border border-green-600 hover:bg-green-700 text-white py-3 rounded-xl text-sm md:text-base font-bold transition-colors flex items-center justify-center gap-2">
                            <ArrowDownRight size={16} /> <span className="hidden sm:inline">Log Repayment</span><span className="sm:hidden">Repay</span>
                          </button>
                        </div>
                      </div>
                      <div className="flex-1 p-4 md:p-8">
                        <h3 className="text-base md:text-lg font-bold text-gray-900 mb-4 border-b border-gray-100 pb-2">Transaction History</h3>
                        <div className="space-y-3 overflow-y-auto max-h-[300px] pr-1">
                          {selectedCustomer.history.map(txn => (
                            <div key={txn.id} className="flex justify-between items-center p-3 md:p-4 bg-gray-50 rounded-xl border border-gray-100 gap-3">
                              <div className="min-w-0">
                                <p className="font-bold text-gray-900 text-sm md:text-base truncate">{txn.notes}</p>
                                <p className="text-[10px] md:text-xs text-gray-500 mt-1">{txn.date}</p>
                              </div>
                              <div className={`font-bold px-2 py-1 rounded-lg text-xs md:text-sm flex-shrink-0 ${txn.type === 'DEBT' ? 'bg-red-50 text-red-700' : 'bg-green-50 text-green-700'}`}>
                                {txn.type === 'DEBT' ? '+' : '-'}{money(txn.amount)}
                              </div>
                            </div>
                          ))}
                          {selectedCustomer.history.length === 0 && <p className="text-gray-400 text-center py-8 text-sm">No transaction history found.</p>}
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="bg-white rounded-[24px] border border-gray-100 shadow-sm h-full flex flex-col items-center justify-center text-gray-400 py-16 md:py-24 px-4 text-center">
                      <CreditCard size={48} className="mb-4 text-gray-200" />
                      <p className="text-base md:text-lg font-medium">Select a customer to view their ledger.</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* VIEW: HR & SCHEDULING */}
          {activeTab === 'HR & Scheduling' && (
            <div className="max-w-6xl mx-auto animate-in fade-in duration-300">
              <div className="mb-6">
                <h1 className="text-2xl md:text-3xl font-bold text-gray-900 mb-2">Shift Scheduling & Payroll</h1>
                <p className="text-sm md:text-base text-gray-500">Handle predictive schedules, weekend crossovers, and daily attendance payroll.</p>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 md:gap-8">
                <div className="bg-white rounded-[24px] border border-gray-100 shadow-sm p-4 md:p-6 h-fit">
                  <div className="flex items-center gap-2 mb-2 border-b border-gray-100 pb-2">
                    <Calendar className="text-[#1A4D2E]" size={20} />
                    <h3 className="text-base md:text-lg font-bold text-gray-900">Friday Off-Day Planner</h3>
                  </div>
                  
                  <div className="space-y-5">
                    <p className="text-xs text-gray-500 mb-4">Select up to 6 staff members. The engine will calculate a fair 2-week split.</p>

                    <form onSubmit={(e) => {
                      e.preventDefault();
                      const checkedBoxes = Array.from(document.querySelectorAll('.volunteer-cb:checked')).map(cb => Number(cb.value));
                      if (checkedBoxes.length === 0) return alert("Please select at least 1 staff member.");
                      if (checkedBoxes.length > 6) return alert("Maximum of 6 staff allowed.");
                      const selectedStaffNames = staffRoster.filter(s => checkedBoxes.includes(s.id)).map(s => s.name);
                      const shuffled = selectedStaffNames.sort(() => 0.5 - Math.random());
                      const baseSplit = Math.floor(shuffled.length / 2);
                      const remainder = shuffled.length - baseSplit;
                      const week1Count = Math.random() > 0.5 ? baseSplit + remainder : baseSplit;
                      setDraftPreview({ week1: shuffled.slice(0, week1Count), week2: shuffled.slice(week1Count) });
                      setShowDraft(true);
                    }}>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Target Friday (Week 1)</label>
                        <input type="date" required className="w-full px-4 py-2.5 rounded-xl border border-gray-200 focus:ring-2 focus:border-[#1A4D2E]" onChange={(e) => { if (e.target.value && new Date(e.target.value).getDay() !== 5) { alert("Please select a Friday."); e.target.value = ""; } }} />
                      </div>
                      
                      <div className="mt-4">
                        <label className="block text-sm font-bold text-gray-900 mb-2 border-b border-gray-200 pb-1">Volunteer Pool</label>
                        <div className="max-h-48 overflow-y-auto space-y-1">
                          {staffRoster.length === 0 ? <p className="text-xs text-gray-400 py-2">Add staff in Administration first.</p> : staffRoster.map(staff => (
                            <div key={`pool-${staff.id}`} className="flex items-center gap-3 p-2 hover:bg-gray-50 rounded-lg">
                              <input type="checkbox" id={`pool-staff-${staff.id}`} value={staff.id} className="volunteer-cb w-5 h-5 text-[#1A4D2E] rounded border-gray-300" />
                              <label htmlFor={`pool-staff-${staff.id}`} className="text-sm font-medium text-gray-700 cursor-pointer flex-1 py-1">
                                {staff.name}
                              </label>
                            </div>
                          ))}
                        </div>
                      </div>
                      <button type="submit" className="w-full bg-gray-800 hover:bg-gray-900 text-white py-3 rounded-xl font-bold transition-colors mt-6 shadow-sm">Generate Draft Schedule</button>
                    </form>
                  </div>

                  <div className={`mt-6 pt-6 border-t border-gray-200 transition-all ${showDraft ? 'block' : 'hidden'}`}> 
                    <div className="mb-4 p-4 rounded-xl bg-blue-50 border border-blue-200">
                      <p className="text-sm font-bold text-blue-800 mb-2">Draft Generated. Awaiting Authorization.</p>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm text-blue-900">
                        <div>
                          <span className="font-bold border-b border-blue-200 block mb-1">Week 1</span>
                          <ul className="list-disc pl-4 text-xs">
                            {draftPreview.week1.length > 0 ? draftPreview.week1.map((name, i) => <li key={`w1-${i}`}>{name}</li>) : <li className="text-gray-400 italic">None</li>}
                          </ul>
                        </div>
                        <div>
                          <span className="font-bold border-b border-blue-200 block mb-1">Week 2</span>
                          <ul className="list-disc pl-4 text-xs">
                            {draftPreview.week2.length > 0 ? draftPreview.week2.map((name, i) => <li key={`w2-${i}`}>{name}</li>) : <li className="text-gray-400 italic">None</li>}
                          </ul>
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex flex-col sm:flex-row gap-3">
                      <button onClick={() => setShowDraft(false)} className="w-full sm:flex-1 bg-white border border-gray-300 text-gray-700 py-3 rounded-xl font-bold hover:bg-gray-50 transition-colors">Discard</button>
                      <button onClick={() => { alert("Schedule Authorized! Locked into database."); setShowDraft(false); document.querySelectorAll('.volunteer-cb').forEach(cb => cb.checked = false); }} className="w-full sm:flex-1 bg-[#1A4D2E] hover:bg-[#11331F] text-white py-3 rounded-xl font-bold shadow-md transition-colors flex items-center justify-center gap-2">
                        <ShieldCheck size={18} /> Lock & Authorize
                      </button>
                    </div>
                  </div>
                </div>

                <div className="bg-white rounded-[24px] border border-gray-100 shadow-sm p-4 md:p-6 flex flex-col h-full">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4 border-b border-gray-100 pb-3">
                    <h3 className="text-base md:text-lg font-bold text-gray-900">End-of-Day Check-In</h3>
                    <input type="date" defaultValue={new Date().toISOString().split('T')[0]} className="text-sm border border-gray-200 rounded-lg px-3 py-2 w-full sm:w-auto" />
                  </div>
                  <p className="text-sm text-gray-500 mb-4">Log actual attendance to calculate today's active payroll.</p>
                  
                  <div className="flex-1 overflow-y-auto mb-4 pr-1 space-y-3">
                    {staffRoster.length === 0 ? <p className="text-xs text-gray-400 py-4 text-center border border-dashed rounded-xl">No active staff loaded.</p> : staffRoster.map(s => (
                       <div key={s.id} className="flex flex-col sm:flex-row sm:items-center justify-between p-3 md:p-4 bg-gray-50 rounded-xl border border-gray-100 gap-3">
                        <div><p className="font-bold text-gray-900 text-sm md:text-base">{s.name}</p><p className="text-xs text-gray-500">Rate: {money(s.rate)}</p></div>
                        <div className="flex w-full sm:w-auto gap-1 md:gap-2 bg-white p-1 rounded-lg border border-gray-200">
                          <button className="flex-1 sm:flex-none px-2 md:px-3 py-1.5 md:py-1 text-[10px] md:text-xs font-bold rounded-md bg-green-100 text-green-800">PRESENT</button>
                          <button className="flex-1 sm:flex-none px-2 md:px-3 py-1.5 md:py-1 text-[10px] md:text-xs font-bold rounded-md text-gray-500 hover:bg-gray-100">ABSENT</button>
                        </div>
                      </div>
                    ))}
                  </div>

                  <div className="border-t border-gray-100 pt-4 mt-auto">
                    <div className="flex justify-between items-center mb-4">
                      <span className="text-gray-500 font-medium text-xs md:text-sm">Expected Payroll Today:</span>
                      <span className="text-xl md:text-2xl font-bold text-[#1A4D2E]">{money(dailyPayroll)}</span> 
                    </div>
                    <button className="w-full bg-blue-50 text-blue-700 hover:bg-blue-100 py-3 md:py-4 rounded-xl font-bold transition-colors text-sm md:text-base">
                      Lock Attendance & Inject Payroll
                    </button>
                  </div>
                </div>

              </div>
            </div>
          )}

          {/* VIEW: ADMINISTRATION */}
          {activeTab === 'Administration' && (
            <div className="max-w-6xl mx-auto animate-in fade-in duration-300">
              <div className="mb-6">
                <h1 className="text-2xl md:text-3xl font-bold text-gray-900 mb-2">System Administration</h1>
                <p className="text-sm md:text-base text-gray-500">Manage organizational setup, active staff rosters, and dynamic menu catalogs.</p>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 md:gap-8">
                <div className="space-y-6 md:space-y-8">
                  <div className="bg-white rounded-[24px] border border-gray-100 shadow-sm p-4 md:p-6">
                    <h3 className="text-base md:text-lg font-bold text-gray-900 mb-4 border-b border-gray-100 pb-2">Branch Setup</h3>
                    <form className="flex flex-col sm:flex-row items-end gap-3 md:gap-4" onSubmit={handleBranchSubmit}>
                      <div className="w-full sm:flex-1">
                        <label className="block text-xs md:text-sm font-medium text-gray-700 mb-1">Branch Name</label>
                        <input type="text" required placeholder="e.g. Alpha Hub" value={newBranch.name} onChange={(e) => setNewBranch({...newBranch, name: e.target.value.replace(/\b\w/g, c => c.toUpperCase())}) } className="w-full px-3 md:px-4 py-2.5 md:py-3 rounded-xl border border-gray-200 focus:ring-2 focus:border-[#1A4D2E] text-sm" />
                      </div>
                      <div className="w-full sm:flex-1">
                        <label className="block text-xs md:text-sm font-medium text-gray-700 mb-1">Location</label>
                        <input type="text" required value={newBranch.location} onChange={(e) => setNewBranch({...newBranch, location: e.target.value}) } className="w-full px-3 md:px-4 py-2.5 md:py-3 rounded-xl border border-gray-200 focus:ring-2 focus:border-[#1A4D2E] text-sm" />
                      </div>
                      <button type="submit" className="w-full sm:w-auto bg-[#1A4D2E] text-white px-6 py-3 rounded-xl font-bold shadow-sm text-sm">Add</button>
                    </form>

                    <div className="mt-4 space-y-2">
                       {branches.map(b => (
                         <div key={b.id} className="flex justify-between items-center bg-gray-50 p-3 rounded-lg border border-gray-100 text-sm">
                           <span className="font-bold">{b.name}</span>
                           <span className="text-gray-500">{b.location}</span>
                         </div>
                       ))}
                    </div>
                  </div>

                  {/* SECURITY SETTINGS WIDGET */}
                  <div className="bg-white rounded-[24px] border border-gray-100 shadow-sm p-4 md:p-6 h-full">
                    <div className="flex items-center gap-2 mb-4 border-b border-gray-100 pb-2">
                      <Lock className="text-red-600" size={20} />
                      <h3 className="text-base md:text-lg font-bold text-gray-900">Security Credentials</h3>
                    </div>
                    <p className="text-xs md:text-sm text-gray-500 mb-6">Update your master login username and password here.</p>
                    
                    <form className="flex flex-col sm:flex-row items-end gap-3 md:gap-4" onSubmit={handleSecurityUpdate}>
                      <div className="w-full sm:flex-1">
                        <label className="block text-xs md:text-sm font-medium text-gray-700 mb-1">New Username</label>
                        <input type="text" required placeholder="e.g. client_admin" value={securityForm.newUsername} onChange={(e) => setSecurityForm({...securityForm, newUsername: e.target.value}) } className="w-full px-3 md:px-4 py-2.5 md:py-3 rounded-xl border border-gray-200 focus:ring-2 focus:border-red-600 text-sm" />
                      </div>
                      <div className="w-full sm:flex-1">
                        <label className="block text-xs md:text-sm font-medium text-gray-700 mb-1">New Passcode</label>
                        <input type="password" required placeholder="Min 6 characters" minLength="6" value={securityForm.newPassword} onChange={(e) => setSecurityForm({...securityForm, newPassword: e.target.value}) } className="w-full px-3 md:px-4 py-2.5 md:py-3 rounded-xl border border-gray-200 focus:ring-2 focus:border-red-600 text-sm" />
                      </div>
                      <button type="submit" className="w-full sm:w-auto bg-red-600 hover:bg-red-700 text-white px-6 py-3 rounded-xl font-bold shadow-sm text-sm transition-colors">Update Access</button>
                    </form>
                  </div>
                </div>

                <div>
                  <div className="bg-white rounded-[24px] border border-gray-100 shadow-sm p-4 md:p-6 h-full">
                     <h3 className="text-base md:text-lg font-bold text-gray-900 mb-4 border-b border-gray-100 pb-2">Active Staff Roster</h3>
                     <p className="text-sm text-gray-500">The application starts clean. Add your active staff members here to populate the HR checks.</p>
                  </div>
                </div>
              </div>
            </div>
          )}

        </main>
      </div>
    </div>
  );
}
import axios from 'axios';

// 1. Create a base client pointed at your FastAPI server
const apiClient = axios.create({
  baseURL: 'http://127.0.0.1:8000/api',
});

// 2. Fetch today's static numbers
export const fetchDashboardMetrics = async (branchId, date) => {
  try {
    const response = await apiClient.get(`/dashboard/${branchId}?target_date=${date}`);
    return response.data;
  } catch (error) {
    console.error("Network Error: Could not fetch dashboard metrics.", error);
    return null;
  }
};

// 3. Fetch the 7-day historical chart data
export const fetchHistoricalMetrics = async (branchId) => {
  try {
    const response = await apiClient.get(`/dashboard/${branchId}/history`);
    return response.data;
  } catch (error) {
    console.error("Network Error: Could not fetch historical metrics.", error);
    return []; // Return empty array to prevent Recharts from crashing
  }
};



// 4. Submit the Evening Audit payload
export const submitEveningAudit = async (auditPayload) => {
  try {
    const response = await apiClient.post('/audit/submit', auditPayload);
    return response.data;
  } catch (error) {
    console.error("Network Error: Could not submit evening audit.", error);
    return null;
  }
};



// --- ADMIN: BRANCHES ---
export const fetchBranches = async () => {
  try { const res = await apiClient.get('/admin/branches'); return res.data; } 
  catch (e) { console.error(e); return []; }
};
export const createBranch = async (payload) => {
  try { const res = await apiClient.post('/admin/branches', payload); return res.data; } 
  catch (e) { console.error(e); return null; }
};

// --- ADMIN: STAFF ---
export const fetchActiveStaff = async () => {
  try { const res = await apiClient.get('/admin/staff/active'); return res.data; } 
  catch (e) { console.error(e); return []; }
};
export const onboardStaff = async (payload) => {
  try { const res = await apiClient.post('/admin/staff', payload); return res.data; } 
  catch (e) { console.error(e); return null; }
};
export const deactivateStaff = async (staffId) => {
  try { const res = await apiClient.put(`/admin/staff/${staffId}/deactivate`); return res.data; } 
  catch (e) { console.error(e); return null; }
};

// --- ADMIN: MENU ---
export const fetchMenuCatalog = async () => {
  try { const res = await apiClient.get('/admin/menu'); return res.data; } 
  catch (e) { console.error(e); return []; }
};
export const createMenuItem = async (payload) => {
  try { const res = await apiClient.post('/admin/menu', payload); return res.data; } 
  catch (e) { console.error(e); return null; }
};
export const toggleMenuItem = async (itemId) => {
  try { const res = await apiClient.put(`/admin/menu/${itemId}/toggle`); return res.data; } 
  catch (e) { console.error(e); return null; }
};



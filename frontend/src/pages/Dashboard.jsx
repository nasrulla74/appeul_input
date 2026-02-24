import { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { Link } from 'react-router-dom';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { FileText, CheckCircle, XCircle, Upload, Download, LogOut } from 'lucide-react';

const COLORS = ['#10B981', '#EF4444', '#F59E0B'];

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [invoices, setInvoices] = useState([]);
  const { user, logout } = useAuth();

  const fetchData = async () => {
    try {
      const [statsRes, invoicesRes] = await Promise.all([
        axios.get('/users/stats'),
        axios.get('/invoices')
      ]);
      setStats(statsRes.data);
      setInvoices(invoicesRes.data);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const exportCSV = async () => {
    try {
      const res = await axios.get('/invoices/export/csv', { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'invoices.csv');
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      console.error(err);
    }
  };

  const pieData = stats ? [
    { name: 'Completed', value: stats.completed_invoices },
    { name: 'Failed', value: stats.failed_invoices },
    { name: 'Pending', value: stats.total_invoices - stats.completed_invoices - stats.failed_invoices }
  ] : [];

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <h1 className="text-xl font-bold">Invoice Extractor</h1>
          <div className="flex items-center gap-4">
            <span className="text-gray-600">{user?.username}</span>
            <button onClick={logout} className="flex items-center gap-2 text-red-600 hover:text-red-700">
              <LogOut size={20} /> Logout
            </button>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="flex justify-between items-center mb-8">
          <h2 className="text-2xl font-bold">Dashboard</h2>
          <div className="flex gap-3">
            <Link to="/upload" className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">
              <Upload size={20} /> Upload Invoices
            </Link>
            <button onClick={exportCSV} className="flex items-center gap-2 bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700">
              <Download size={20} /> Export CSV
            </button>
          </div>
        </div>

        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div className="bg-white p-6 rounded-lg shadow-sm">
              <div className="flex items-center gap-3">
                <FileText className="text-blue-600" size={24} />
                <div>
                  <p className="text-gray-500 text-sm">Total Invoices</p>
                  <p className="text-2xl font-bold">{stats.total_invoices}</p>
                </div>
              </div>
            </div>
            <div className="bg-white p-6 rounded-lg shadow-sm">
              <div className="flex items-center gap-3">
                <CheckCircle className="text-green-600" size={24} />
                <div>
                  <p className="text-gray-500 text-sm">Completed</p>
                  <p className="text-2xl font-bold">{stats.completed_invoices}</p>
                </div>
              </div>
            </div>
            <div className="bg-white p-6 rounded-lg shadow-sm">
              <div className="flex items-center gap-3">
                <XCircle className="text-red-600" size={24} />
                <div>
                  <p className="text-gray-500 text-sm">Failed</p>
                  <p className="text-2xl font-bold">{stats.failed_invoices}</p>
                </div>
              </div>
            </div>
            <div className="bg-white p-6 rounded-lg shadow-sm">
              <div className="flex items-center gap-3">
                <div className="text-purple-600 text-2xl font-bold">{stats.average_confidence}%</div>
                <div>
                  <p className="text-gray-500 text-sm">Avg Confidence</p>
                </div>
              </div>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <div className="bg-white p-6 rounded-lg shadow-sm">
            <h3 className="text-lg font-semibold mb-4">Monthly Trend</h3>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={stats?.monthly_data || []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill="#3B82F6" />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-sm">
            <h3 className="text-lg font-semibold mb-4">Status Distribution</h3>
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie data={pieData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={60}>
                  {pieData.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm overflow-hidden">
          <h3 className="text-lg font-semibold p-6 border-b">Recent Invoices</h3>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Filename</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Invoice #</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Customer</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Confidence</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {invoices.map((inv) => (
                  <tr key={inv.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4">{inv.filename}</td>
                    <td className="px-6 py-4">{inv.invoice_number || '-'}</td>
                    <td className="px-6 py-4">{inv.customer_name || '-'}</td>
                    <td className="px-6 py-4">
                      <span className={`px-2 py-1 rounded text-xs ${inv.status === 'completed' ? 'bg-green-100 text-green-800' : inv.status === 'failed' ? 'bg-red-100 text-red-800' : 'bg-yellow-100 text-yellow-800'}`}>
                        {inv.status}
                      </span>
                    </td>
                    <td className="px-6 py-4">{inv.confidence ? `${(inv.confidence * 100).toFixed(0)}%` : '-'}</td>
                    <td className="px-6 py-4">{new Date(inv.created_at).toLocaleDateString()}</td>
                  </tr>
                ))}
                {invoices.length === 0 && (
                  <tr>
                    <td colSpan={6} className="px-6 py-8 text-center text-gray-500">
                      No invoices found. Upload some invoices to get started.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}

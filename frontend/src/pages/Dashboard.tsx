import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, TrendingUp, Trash2, Clock } from 'lucide-react';
import { apiService } from '../services/api';
import type { BetSlip } from '../types';
import { format } from 'date-fns';

export default function Dashboard() {
  const [betSlips, setBetSlips] = useState<BetSlip[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    loadBetSlips();
  }, []);

  const loadBetSlips = async () => {
    try {
      const slips = await apiService.getBetSlips();
      setBetSlips(slips);
    } catch (error) {
      console.error('Failed to load bet slips:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this bet slip?')) return;

    try {
      await apiService.deleteBetSlip(id);
      setBetSlips(betSlips.filter(slip => slip.id !== id));
    } catch (error) {
      console.error('Failed to delete bet slip:', error);
      alert('Failed to delete bet slip');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">PropBet Analyzer</h1>
              <p className="text-sm text-gray-600">NBA Prop Bet & Halftime Analysis</p>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="card">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Analyses</p>
                <p className="text-3xl font-bold text-gray-900">{betSlips.length}</p>
              </div>
              <TrendingUp className="w-12 h-12 text-blue-600" />
            </div>
          </div>

          <div className="card">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Analyzed</p>
                <p className="text-3xl font-bold text-gray-900">
                  {betSlips.filter(s => s.status === 'analyzed').length}
                </p>
              </div>
              <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
                <span className="text-2xl">&#10003;</span>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Pending</p>
                <p className="text-3xl font-bold text-gray-900">
                  {betSlips.filter(s => s.status === 'pending').length}
                </p>
              </div>
              <div className="w-12 h-12 bg-yellow-100 rounded-full flex items-center justify-center">
                <span className="text-2xl">&#9201;</span>
              </div>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="mb-6 flex gap-3">
          <button
            onClick={() => navigate('/create')}
            className="btn-primary"
          >
            <Plus className="w-5 h-5 inline mr-2" />
            New Bet Slip Analysis
          </button>
          <button
            onClick={() => navigate('/halftime')}
            className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 transition-colors flex items-center gap-2"
          >
            <Clock className="w-5 h-5" />
            Halftime Analyzer
          </button>
        </div>

        {/* Bet Slips List */}
        <div className="card">
          <h2 className="text-xl font-semibold mb-4">Your Bet Slips</h2>

          {loading ? (
            <div className="text-center py-8">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <p className="mt-2 text-gray-600">Loading...</p>
            </div>
          ) : betSlips.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-600 mb-4">No bet slips yet</p>
              <button
                onClick={() => navigate('/create')}
                className="btn-primary"
              >
                Create Your First Analysis
              </button>
            </div>
          ) : (
            <div className="space-y-3">
              {betSlips.map((slip) => (
                <div
                  key={slip.id}
                  className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-3">
                      <h3 className="font-medium text-gray-900">
                        {slip.name || `Bet Slip #${slip.id}`}
                      </h3>
                      <span
                        className={`badge ${
                          slip.status === 'analyzed'
                            ? 'badge-success'
                            : slip.status === 'pending'
                            ? 'badge-warning'
                            : 'badge-info'
                        }`}
                      >
                        {slip.status}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 mt-1">
                      {slip.prop_bets?.length || 0} props • Created {format(new Date(slip.created_at!), 'MMM d, yyyy')}
                    </p>
                  </div>

                  <div className="flex items-center gap-2">
                    {slip.status === 'analyzed' ? (
                      <button
                        onClick={() => navigate(`/analysis/${slip.id}`)}
                        className="btn-primary"
                      >
                        View Analysis
                      </button>
                    ) : (
                      <button
                        onClick={() => navigate(`/analysis/${slip.id}`)}
                        className="btn-secondary"
                      >
                        Analyze Now
                      </button>
                    )}
                    <button
                      onClick={() => handleDelete(slip.id!)}
                      className="p-2 text-red-600 hover:text-red-700 hover:bg-red-50 rounded"
                    >
                      <Trash2 className="w-5 h-5" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

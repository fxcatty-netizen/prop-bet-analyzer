import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Trash2, TrendingUp } from 'lucide-react';
import BetSlipUpload from '../components/BetSlipUpload';
import { apiService } from '../services/api';
import type { PropBet } from '../types';

export default function CreateBetSlip() {
  const [name, setName] = useState('');
  const [props, setProps] = useState<PropBet[]>([]);
  const [currentProp, setCurrentProp] = useState<PropBet>({
    player_name: '',
    stat_type: 'points',
    line: 0,
    over_under: 'over'
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const handleAddProp = () => {
    if (!currentProp.player_name || currentProp.line <= 0) {
      setError('Please fill in player name and line value');
      return;
    }

    setProps([...props, { ...currentProp }]);
    setCurrentProp({
      player_name: '',
      stat_type: 'points',
      line: 0,
      over_under: 'over'
    });
    setError(null);
  };

  const handleRemoveProp = (index: number) => {
    setProps(props.filter((_, i) => i !== index));
  };

  const handlePropsExtracted = (extractedProps: PropBet[]) => {
    setProps(extractedProps);
    setError(null);
  };

  const handleSubmit = async () => {
    if (props.length === 0) {
      setError('Please add at least one prop bet');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const betSlip = await apiService.createBetSlip({
        name: name || undefined,
        prop_bets: props
      });

      // Navigate to analysis page
      navigate(`/analysis/${betSlip.id}`);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create bet slip');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Create Bet Slip</h1>
          <p className="text-gray-600">Upload an image or manually enter your prop bets</p>
        </div>

        {/* Image Upload Section */}
        <BetSlipUpload onPropsExtracted={handlePropsExtracted} />

        {/* Manual Entry Section */}
        <div className="card mt-6">
          <h2 className="text-xl font-semibold mb-4">Bet Slip Details</h2>
          
          <div className="mb-4">
            <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
              Bet Slip Name (Optional)
            </label>
            <input
              id="name"
              type="text"
              className="input"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g., Tonight's SGP"
            />
          </div>

          <div className="border-t border-gray-200 pt-4 mt-4">
            <h3 className="text-lg font-medium mb-4">Add Props</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Player Name
                </label>
                <input
                  type="text"
                  className="input"
                  value={currentProp.player_name}
                  onChange={(e) => setCurrentProp({ ...currentProp, player_name: e.target.value })}
                  placeholder="e.g., Anthony Black"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Stat Type
                </label>
                <select
                  className="input"
                  value={currentProp.stat_type}
                  onChange={(e) => setCurrentProp({ ...currentProp, stat_type: e.target.value })}
                >
                  <option value="points">Points</option>
                  <option value="rebounds">Rebounds</option>
                  <option value="assists">Assists</option>
                  <option value="threes">3-Pointers Made</option>
                  <option value="steals">Steals</option>
                  <option value="blocks">Blocks</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Line
                </label>
                <input
                  type="number"
                  step="0.5"
                  className="input"
                  value={currentProp.line || ''}
                  onChange={(e) => setCurrentProp({ ...currentProp, line: parseFloat(e.target.value) || 0 })}
                  placeholder="15.5"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Over/Under
                </label>
                <select
                  className="input"
                  value={currentProp.over_under}
                  onChange={(e) => setCurrentProp({ ...currentProp, over_under: e.target.value as 'over' | 'under' })}
                >
                  <option value="over">Over</option>
                  <option value="under">Under</option>
                </select>
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Opponent (Optional)
                </label>
                <input
                  type="text"
                  className="input"
                  value={currentProp.opponent_name || ''}
                  onChange={(e) => setCurrentProp({ ...currentProp, opponent_name: e.target.value })}
                  placeholder="e.g., Cleveland Cavaliers"
                />
              </div>
            </div>

            <button
              onClick={handleAddProp}
              className="btn-secondary w-full"
            >
              <Plus className="w-4 h-4 inline mr-2" />
              Add Prop
            </button>
          </div>
        </div>

        {/* Props List */}
        {props.length > 0 && (
          <div className="card mt-6">
            <h3 className="text-lg font-semibold mb-4">Props ({props.length})</h3>
            <div className="space-y-3">
              {props.map((prop, index) => (
                <div key={index} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                  <div>
                    <p className="font-medium text-gray-900">{prop.player_name}</p>
                    <p className="text-sm text-gray-600">
                      {prop.stat_type} {prop.over_under} {prop.line}
                      {prop.opponent_name && ` vs ${prop.opponent_name}`}
                    </p>
                  </div>
                  <button
                    onClick={() => handleRemoveProp(index)}
                    className="text-red-600 hover:text-red-700"
                  >
                    <Trash2 className="w-5 h-5" />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-800 text-sm">{error}</p>
          </div>
        )}

        {/* Submit Button */}
        <div className="mt-6 flex gap-3">
          <button
            onClick={() => navigate('/dashboard')}
            className="btn-secondary flex-1"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            className="btn-primary flex-1"
            disabled={loading || props.length === 0}
          >
            {loading ? (
              'Creating...'
            ) : (
              <>
                <TrendingUp className="w-4 h-4 inline mr-2" />
                Analyze Bet Slip
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

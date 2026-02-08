import { useState } from 'react';
import { Upload, Image, FileText, Loader2 } from 'lucide-react';
import { apiService } from '../services/api';
import type { PropBet } from '../types';

interface BetSlipUploadProps {
  onPropsExtracted: (props: PropBet[]) => void;
}

export default function BetSlipUpload({ onPropsExtracted }: BetSlipUploadProps) {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [method, setMethod] = useState<'image' | 'manual'>('image');

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      if (!selectedFile.type.startsWith('image/')) {
        setError('Please select an image file');
        return;
      }
      
      if (selectedFile.size > 10 * 1024 * 1024) {
        setError('File size must be less than 10MB');
        return;
      }

      setFile(selectedFile);
      setError(null);
      
      // Create preview
      const reader = new FileReader();
      reader.onload = (e) => {
        setPreview(e.target?.result as string);
      };
      reader.readAsDataURL(selectedFile);
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    setUploading(true);
    setError(null);

    try {
      const betSlip = await apiService.uploadBetSlipImage(file);
      
      // Extract props from the response
      if (betSlip.prop_bets && betSlip.prop_bets.length > 0) {
        onPropsExtracted(betSlip.prop_bets);
      } else {
        setError('No props could be extracted from the image. Please try manual input.');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to upload and parse bet slip');
    } finally {
      setUploading(false);
    }
  };

  const handleClear = () => {
    setFile(null);
    setPreview(null);
    setError(null);
  };

  return (
    <div className="space-y-4">
      {/* Method selector */}
      <div className="flex gap-2 p-1 bg-gray-100 rounded-lg">
        <button
          onClick={() => setMethod('image')}
          className={`flex-1 py-2 px-4 rounded-md font-medium transition-colors ${
            method === 'image'
              ? 'bg-white text-blue-600 shadow'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          <Image className="w-4 h-4 inline mr-2" />
          Upload Image
        </button>
        <button
          onClick={() => setMethod('manual')}
          className={`flex-1 py-2 px-4 rounded-md font-medium transition-colors ${
            method === 'manual'
              ? 'bg-white text-blue-600 shadow'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          <FileText className="w-4 h-4 inline mr-2" />
          Manual Entry
        </button>
      </div>

      {method === 'image' && (
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">Upload Bet Slip Image</h3>
          
          {!preview ? (
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-400 transition-colors">
              <Upload className="mx-auto h-12 w-12 text-gray-400 mb-4" />
              <div>
                <label htmlFor="file-upload" className="cursor-pointer">
                  <span className="text-blue-600 hover:text-blue-700 font-medium">
                    Upload a file
                  </span>
                  <span className="text-gray-600"> or drag and drop</span>
                  <input
                    id="file-upload"
                    name="file-upload"
                    type="file"
                    className="sr-only"
                    accept="image/*"
                    onChange={handleFileChange}
                    disabled={uploading}
                  />
                </label>
                <p className="text-xs text-gray-500 mt-2">
                  PNG, JPG, GIF up to 10MB
                </p>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="relative">
                <img 
                  src={preview} 
                  alt="Bet slip preview" 
                  className="max-h-96 mx-auto rounded-lg border border-gray-200"
                />
              </div>
              
              <div className="flex gap-2">
                <button
                  onClick={handleClear}
                  className="btn-secondary flex-1"
                  disabled={uploading}
                >
                  Clear
                </button>
                <button
                  onClick={handleUpload}
                  className="btn-primary flex-1"
                  disabled={uploading}
                >
                  {uploading ? (
                    <>
                      <Loader2 className="w-4 h-4 inline mr-2 animate-spin" />
                      Analyzing...
                    </>
                  ) : (
                    <>
                      <Upload className="w-4 h-4 inline mr-2" />
                      Analyze Image
                    </>
                  )}
                </button>
              </div>
            </div>
          )}

          {error && (
            <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-800 text-sm">{error}</p>
            </div>
          )}

          <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-sm text-blue-800">
              <strong>Tip:</strong> For best results, upload a clear, well-lit image of your bet slip. 
              The AI will automatically extract player names, stats, and lines.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

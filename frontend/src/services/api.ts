import axios, { AxiosInstance } from 'axios';
import type {
  BetSlip,
  BetSlipWithAnalysis,
  Analysis,
  LiveGame,
  LiveBoxScore,
  HalftimeAnalysisResponse,
  HalftimeSuggestionsResponse,
  AnalysisSnapshot,
  SnapshotDetail,
  EnhancedGameTotalAnalysis
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

class ApiService {
  private api: AxiosInstance;

  constructor() {
    this.api = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  // Bet slip endpoints
  async createBetSlip(data: BetSlip): Promise<BetSlip> {
    const response = await this.api.post<BetSlip>('/bets/', data);
    return response.data;
  }

  async uploadBetSlipImage(file: File): Promise<BetSlip> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await this.api.post<BetSlip>('/bets/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  async getBetSlips(): Promise<BetSlip[]> {
    const response = await this.api.get<BetSlip[]>('/bets/');
    return response.data;
  }

  async getBetSlip(id: number): Promise<BetSlipWithAnalysis> {
    const response = await this.api.get<BetSlipWithAnalysis>(`/bets/${id}`);
    return response.data;
  }

  async analyzeBetSlip(id: number): Promise<Analysis> {
    const response = await this.api.post<Analysis>(`/bets/${id}/analyze`);
    return response.data;
  }

  async deleteBetSlip(id: number): Promise<void> {
    await this.api.delete(`/bets/${id}`);
  }

  // Halftime Analysis endpoints
  async getLiveGames(): Promise<LiveGame[]> {
    const response = await this.api.get<LiveGame[]>('/halftime/games/live');
    return response.data;
  }

  async getTodaysGames(): Promise<LiveGame[]> {
    const response = await this.api.get<LiveGame[]>('/halftime/games/today');
    return response.data;
  }

  async getHalftimeGames(): Promise<LiveGame[]> {
    const response = await this.api.get<LiveGame[]>('/halftime/games/halftime');
    return response.data;
  }

  async getGameBoxScore(gameId: string): Promise<LiveBoxScore> {
    const response = await this.api.get<LiveBoxScore>(`/halftime/games/${gameId}/boxscore`);
    return response.data;
  }

  async analyzeHalftimeGame(gameId: string): Promise<HalftimeAnalysisResponse> {
    const response = await this.api.get<HalftimeAnalysisResponse>(`/halftime/games/${gameId}/analyze`);
    return response.data;
  }

  async getHalftimeSuggestions(
    gameId: string,
    options?: { minConfidence?: number; propType?: string }
  ): Promise<HalftimeSuggestionsResponse> {
    const params = new URLSearchParams();
    if (options?.minConfidence) {
      params.append('min_confidence', options.minConfidence.toString());
    }
    if (options?.propType) {
      params.append('prop_type', options.propType);
    }
    const response = await this.api.get<HalftimeSuggestionsResponse>(
      `/halftime/games/${gameId}/suggestions${params.toString() ? '?' + params.toString() : ''}`
    );
    return response.data;
  }

  async saveHalftimeSnapshot(gameId: string): Promise<AnalysisSnapshot> {
    const response = await this.api.post<AnalysisSnapshot>(`/halftime/games/${gameId}/snapshot`);
    return response.data;
  }

  async getHalftimeSnapshots(limit: number = 20): Promise<AnalysisSnapshot[]> {
    const response = await this.api.get<AnalysisSnapshot[]>(`/halftime/snapshots?limit=${limit}`);
    return response.data;
  }

  async getSnapshotDetail(snapshotId: number): Promise<SnapshotDetail> {
    const response = await this.api.get<SnapshotDetail>(`/halftime/snapshots/${snapshotId}`);
    return response.data;
  }

  async deleteSnapshot(snapshotId: number): Promise<void> {
    await this.api.delete(`/halftime/snapshots/${snapshotId}`);
  }

  async getGameTotalsAnalysis(
    gameId: string,
    referenceLine?: number
  ): Promise<EnhancedGameTotalAnalysis> {
    const params = new URLSearchParams();
    if (referenceLine) {
      params.append('reference_line', referenceLine.toString());
    }
    const response = await this.api.get<EnhancedGameTotalAnalysis>(
      `/halftime/games/${gameId}/totals${params.toString() ? '?' + params.toString() : ''}`
    );
    return response.data;
  }
}

export const apiService = new ApiService();

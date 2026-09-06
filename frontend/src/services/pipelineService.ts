import { apiClient } from './apiClient';

// ---------- Types ----------

export interface PipelineStage {
  stage: string;
  count: number;
  total_amount: string | number;
  quotations?: Array<{
    id: string;
    quotation_number: string;
    customer_name: string;
    total_amount: string | number;
    status: string;
    risk_score?: string | number;
    updated_at: string;
  }>;
}

export type PipelineResponse = PipelineStage[];

// ---------- Service ----------

export const pipelineService = {
  async getPipeline(): Promise<PipelineResponse> {
    return apiClient.get<PipelineResponse>('/pipeline');
  },
};

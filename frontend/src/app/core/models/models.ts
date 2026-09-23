export interface Model {
  id: string;
  name: string;
  owner: string;
  framework: string;
  versions?: ModelVersion[];
}

export interface ModelVersion {
  id: number;
  model_id: string;
  version: string;
  stage: string;
  approved: boolean;
}

export interface Deployment {
  id: number;
  model_version_id: number;
  environment: string;
  status: string;
}

export interface Metric {
  id: number;
  model_id: string;
  version: string | null;
  environment: string | null;
  latency: number | null;
  throughput: number | null;
  error_rate: number | null;
  quality_score: number | null;
  drift_score: number | null;
  availability: number | null;
  timestamp: string;
}

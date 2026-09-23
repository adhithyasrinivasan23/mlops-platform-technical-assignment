import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Model, ModelVersion, Deployment, Metric } from '../models/models';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private http = inject(HttpClient);
  private readonly API_BASE = '/api';

  // --- Models ---
  getModels(): Observable<Model[]> {
    return this.http.get<Model[]>(`${this.API_BASE}/models`);
  }

  getModel(id: string): Observable<Model> {
    return this.http.get<Model>(`${this.API_BASE}/models/${id}`);
  }

  createModel(model: Partial<Model>): Observable<Model> {
    return this.http.post<Model>(`${this.API_BASE}/models`, model);
  }

  // --- Versions ---
  getVersions(modelId: string): Observable<ModelVersion[]> {
    return this.http.get<ModelVersion[]>(`${this.API_BASE}/models/${modelId}/versions`);
  }

  createVersion(modelId: string, versionData: Partial<ModelVersion>): Observable<ModelVersion> {
    return this.http.post<ModelVersion>(`${this.API_BASE}/models/${modelId}/versions`, versionData);
  }

  approveVersion(modelId: string, versionId: number): Observable<ModelVersion> {
    return this.http.post<ModelVersion>(`${this.API_BASE}/models/${modelId}/versions/${versionId}/approve`, {});
  }

  archiveVersion(modelId: string, versionId: number): Observable<ModelVersion> {
    return this.http.post<ModelVersion>(`${this.API_BASE}/models/${modelId}/versions/${versionId}/archive`, {});
  }

  // --- Deployments ---
  getDeployments(): Observable<Deployment[]> {
    return this.http.get<Deployment[]>(`${this.API_BASE}/deployments`);
  }

  getDeployment(id: number): Observable<Deployment> {
    return this.http.get<Deployment>(`${this.API_BASE}/deployments/${id}`);
  }

  createDeployment(deploymentData: Partial<Deployment>): Observable<Deployment> {
    return this.http.post<Deployment>(`${this.API_BASE}/deployments`, deploymentData);
  }

  retryDeployment(id: number): Observable<Deployment> {
    return this.http.post<Deployment>(`${this.API_BASE}/deployments/${id}/retry`, {});
  }

  rollbackDeployment(id: number): Observable<Deployment> {
    return this.http.post<Deployment>(`${this.API_BASE}/deployments/${id}/rollback`, {});
  }

  // --- Metrics ---
  getMetrics(modelId: string): Observable<Metric[]> {
    return this.http.get<Metric[]>(`${this.API_BASE}/models/${modelId}/metrics`);
  }
}

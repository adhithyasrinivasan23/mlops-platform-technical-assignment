import { Component, OnInit, inject, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterLink, Router } from '@angular/router';
import { MatTabsModule } from '@angular/material/tabs';
import { MatTableModule } from '@angular/material/table';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatCardModule } from '@angular/material/card';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatDialog, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { FormsModule } from '@angular/forms';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { ApiService } from '../../core/services/api.service';
import { Model, ModelVersion, Metric } from '../../core/models/models';

@Component({
  selector: 'app-create-version-dialog',
  standalone: true,
  imports: [CommonModule, FormsModule, MatDialogModule, MatFormFieldModule, MatInputModule, MatSelectModule, MatButtonModule],
  template: `
    <h2 mat-dialog-title>Create New Version</h2>
    <mat-dialog-content>
      <form #f="ngForm" class="create-version-form">
        <mat-form-field appearance="fill" class="full-width">
          <mat-label>Version (e.g. 1.0.0)</mat-label>
          <input matInput name="version" [(ngModel)]="versionData.version" required>
        </mat-form-field>
        <mat-form-field appearance="fill" class="full-width">
          <mat-label>Stage</mat-label>
          <mat-select name="stage" [(ngModel)]="versionData.stage" required>
            <mat-option value="DRAFT">DRAFT</mat-option>
            <mat-option value="VALIDATED">VALIDATED</mat-option>
            <mat-option value="APPROVED">APPROVED</mat-option>
            <mat-option value="STAGING">STAGING</mat-option>
            <mat-option value="PRODUCTION">PRODUCTION</mat-option>
            <mat-option value="ARCHIVED">ARCHIVED</mat-option>
          </mat-select>
        </mat-form-field>
        <mat-form-field appearance="fill" class="full-width">
          <mat-label>Artifact URI</mat-label>
          <input matInput name="artifact_uri" [(ngModel)]="versionData.artifact_uri" required>
        </mat-form-field>
      </form>
    </mat-dialog-content>
    <mat-dialog-actions align="end">
      <button mat-button mat-dialog-close>Cancel</button>
      <button mat-raised-button color="primary" [disabled]="!f.valid" (click)="save()">Create</button>
    </mat-dialog-actions>
  `,
  styles: [`
    .create-version-form { display: flex; flex-direction: column; gap: 10px; margin-top: 10px; }
    .full-width { width: 100%; }
  `]
})
export class CreateModelVersionDialog {
  private dialogRef = inject(MatDialogRef<CreateModelVersionDialog>);
  versionData = { version: '', stage: 'DRAFT', approved: false, artifact_uri: '' };

  save() {
    this.versionData.approved = ['APPROVED', 'STAGING', 'PRODUCTION'].includes(this.versionData.stage);
    this.dialogRef.close(this.versionData);
  }
}

@Component({
  selector: 'app-deploy-version-dialog',
  standalone: true,
  imports: [CommonModule, FormsModule, MatDialogModule, MatFormFieldModule, MatSelectModule, MatButtonModule, MatCheckboxModule],
  template: `
    <h2 mat-dialog-title>Deploy Model Version</h2>
    <mat-dialog-content>
      <form #f="ngForm" class="deploy-version-form">
        <mat-form-field appearance="fill" class="full-width">
          <mat-label>Target Environment</mat-label>
          <mat-select name="environment" [(ngModel)]="deployData.environment" required>
            <mat-option value="staging">Staging</mat-option>
            <mat-option value="production">Production</mat-option>
          </mat-select>
        </mat-form-field>
        <mat-checkbox name="simulate_failure" [(ngModel)]="deployData.simulate_failure" color="warn">
          Simulate failure directly (for testing)
        </mat-checkbox>
      </form>
    </mat-dialog-content>
    <mat-dialog-actions align="end">
      <button mat-button mat-dialog-close>Cancel</button>
      <button mat-raised-button color="accent" [disabled]="!f.valid" (click)="deploy()">Deploy</button>
    </mat-dialog-actions>
  `,
  styles: [`
    .deploy-version-form { display: flex; flex-direction: column; gap: 10px; margin-top: 10px; }
    .full-width { width: 100%; }
  `]
})
export class DeployVersionDialog {
  private dialogRef = inject(MatDialogRef<DeployVersionDialog>);
  deployData = { environment: 'staging', simulate_failure: false };

  deploy() {
    this.dialogRef.close(this.deployData);
  }
}

@Component({
  selector: 'app-model-detail',
  standalone: true,
  imports: [
    CommonModule, RouterLink, MatTabsModule, MatTableModule, 
    MatButtonModule, MatIconModule, MatProgressSpinnerModule, MatCardModule, MatSnackBarModule, MatDialogModule
  ],
  templateUrl: './model-detail.html',
  styleUrls: ['./model-detail.css']
})
export class ModelDetail implements OnInit {
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private snackBar = inject(MatSnackBar);
  private dialog = inject(MatDialog);
  private api = inject(ApiService);
  private cdr = inject(ChangeDetectorRef);
  
  modelId: string = '';
  model: Model | null = null;
  versions: ModelVersion[] = [];
  metrics: Metric[] = [];
  
  loading = true;
  versionsColumns = ['version', 'stage', 'approved', 'actions'];
  metricsColumns = ['timestamp', 'version', 'environment', 'latency', 'throughput', 'error_rate', 'quality_score', 'drift_score', 'availability', 'monitoring_status'];

  get lastInferenceAt(): string | null {
    if (!this.metrics.length) return null;
    const sorted = [...this.metrics].sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
    return sorted[0].timestamp;
  }

  getMonitoringStatus(metric: { error_rate: number | null; drift_score: number | null }): string {
    if (metric.error_rate !== null && metric.error_rate > 0.05) return 'DEGRADED';
    if (metric.drift_score !== null && metric.drift_score > 0.3) return 'DRIFTING';
    return 'HEALTHY';
  }

  ngOnInit() {
    this.modelId = this.route.snapshot.paramMap.get('id') || '';
    if (this.modelId) {
      this.loadData();
    }
  }

  loadData() {
    this.loading = true;
    this.cdr.detectChanges();
    this.api.getModel(this.modelId).subscribe({
      next: m => {
        this.model = m;
        this.api.getVersions(this.modelId).subscribe({
          next: v => {
            this.versions = v;
            this.api.getMetrics(this.modelId).subscribe({
              next: met => {
                this.metrics = met;
                this.loading = false;
                this.cdr.detectChanges();
              },
              error: () => {
                this.loading = false;
                this.cdr.detectChanges();
              }
            });
          },
          error: () => {
            this.loading = false;
            this.cdr.detectChanges();
          }
        });
      },
      error: () => {
        this.loading = false;
        this.cdr.detectChanges();
      }
    });
  }

  deployVersion(versionId: number) {
    const dialogRef = this.dialog.open(DeployVersionDialog, {
      width: '400px'
    });

    dialogRef.afterClosed().subscribe(result => {
      if (result) {
        this.api.createDeployment({
          model_version_id: versionId,
          environment: result.environment,
          simulate_failure: result.simulate_failure
        } as any).subscribe({
          next: () => {
            this.snackBar.open('Deployment requested successfully!', 'Close', { duration: 3000 });
            this.router.navigate(['/deployments']);
          },
          error: (err) => {
            console.error('Deployment error:', err);
            let errorMsg = 'Deployment failed';
            if (err.error && err.error.detail) {
              errorMsg = err.error.detail;
            } else if (err.message) {
              errorMsg = err.message;
            }
            this.snackBar.open(`Error: ${errorMsg}`, 'Close', { duration: 5000 });
          }
        });
      }
    });
  }

  approveVersion(versionId: number) {
    this.loading = true;
    this.cdr.detectChanges();
    this.api.approveVersion(this.modelId, versionId).subscribe({
      next: () => {
        this.snackBar.open('Version approved successfully!', 'Close', { duration: 3000 });
        this.loadData();
      },
      error: () => {
        this.loading = false;
        this.cdr.detectChanges();
      }
    });
  }

  archiveVersion(versionId: number) {
    this.loading = true;
    this.cdr.detectChanges();
    this.api.archiveVersion(this.modelId, versionId).subscribe({
      next: () => {
        this.snackBar.open('Version archived successfully!', 'Close', { duration: 3000 });
        this.loadData();
      },
      error: () => {
        this.loading = false;
        this.cdr.detectChanges();
      }
    });
  }

  onCreateVersion() {
    const dialogRef = this.dialog.open(CreateModelVersionDialog, {
      width: '400px'
    });

    dialogRef.afterClosed().subscribe(result => {
      if (result) {
        this.loading = true;
        this.cdr.detectChanges();
        this.api.createVersion(this.modelId, result).subscribe({
          next: () => {
            this.snackBar.open('Version created successfully!', 'Close', { duration: 3000 });
            this.loadData();
          },
          error: () => {
            this.loading = false;
            this.cdr.detectChanges();
          }
        });
      }
    });
  }
}

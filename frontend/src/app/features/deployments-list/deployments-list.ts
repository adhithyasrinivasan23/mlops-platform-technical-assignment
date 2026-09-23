import { Component, OnInit, inject, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatTableModule } from '@angular/material/table';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { ApiService } from '../../core/services/api.service';
import { Deployment } from '../../core/models/models';

@Component({
  selector: 'app-deployments-list',
  standalone: true,
  imports: [CommonModule, MatTableModule, MatButtonModule, MatIconModule, MatProgressSpinnerModule],
  templateUrl: './deployments-list.html',
  styleUrls: ['./deployments-list.css']
})
export class DeploymentsList implements OnInit {
  private api = inject(ApiService);
  private cdr = inject(ChangeDetectorRef);
  
  deployments: Deployment[] = [];
  displayedColumns: string[] = ['id', 'model_version_id', 'environment', 'status', 'actions'];
  loading = true;

  ngOnInit() {
    this.loadDeployments();
  }

  loadDeployments() {
    this.loading = true;
    this.cdr.detectChanges();
    this.api.getDeployments().subscribe({
      next: (data) => {
        this.deployments = data;
        this.loading = false;
        this.cdr.detectChanges();
      },
      error: () => {
        this.loading = false;
        this.cdr.detectChanges();
      }
    });
  }

  retryDeployment(id: number) {
    this.api.retryDeployment(id).subscribe(() => this.loadDeployments());
  }

  rollbackDeployment(id: number) {
    this.api.rollbackDeployment(id).subscribe(() => this.loadDeployments());
  }
}

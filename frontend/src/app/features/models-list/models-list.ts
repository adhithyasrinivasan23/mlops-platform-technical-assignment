import { Component, OnInit, inject, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { MatTableModule } from '@angular/material/table';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { ApiService } from '../../core/services/api.service';
import { Model } from '../../core/models/models';
import { MatDialog, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { FormsModule } from '@angular/forms';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';

@Component({
  selector: 'app-create-model-dialog',
  standalone: true,
  imports: [CommonModule, FormsModule, MatDialogModule, MatFormFieldModule, MatInputModule, MatButtonModule],
  template: `
    <h2 mat-dialog-title>Create New Model</h2>
    <mat-dialog-content>
      <form #f="ngForm" class="create-model-form">
        <mat-form-field appearance="fill" class="full-width">
          <mat-label>Model ID (e.g. churn-model)</mat-label>
          <input matInput name="id" [(ngModel)]="model.id" required>
        </mat-form-field>
        <mat-form-field appearance="fill" class="full-width">
          <mat-label>Name</mat-label>
          <input matInput name="name" [(ngModel)]="model.name" required>
        </mat-form-field>
        <mat-form-field appearance="fill" class="full-width">
          <mat-label>Owner</mat-label>
          <input matInput name="owner" [(ngModel)]="model.owner" required>
        </mat-form-field>
        <mat-form-field appearance="fill" class="full-width">
          <mat-label>Framework</mat-label>
          <input matInput name="framework" [(ngModel)]="model.framework" required>
        </mat-form-field>
      </form>
    </mat-dialog-content>
    <mat-dialog-actions align="end">
      <button mat-button mat-dialog-close>Cancel</button>
      <button mat-raised-button color="primary" [disabled]="!f.valid" (click)="save()">Create</button>
    </mat-dialog-actions>
  `,
  styles: [`
    .create-model-form { display: flex; flex-direction: column; gap: 10px; margin-top: 10px; }
    .full-width { width: 100%; }
  `]
})
export class CreateModelDialog {
  private dialogRef = inject(MatDialogRef<CreateModelDialog>);
  model = { id: '', name: '', owner: '', framework: '' };

  save() {
    this.dialogRef.close(this.model);
  }
}

@Component({
  selector: 'app-models-list',
  standalone: true,
  imports: [CommonModule, RouterLink, MatTableModule, MatButtonModule, MatIconModule, MatProgressSpinnerModule, MatDialogModule, MatSnackBarModule],
  templateUrl: './models-list.html',
  styleUrls: ['./models-list.css']
})
export class ModelsList implements OnInit {
  private api = inject(ApiService);
  private cdr = inject(ChangeDetectorRef);
  private dialog = inject(MatDialog);
  private snackBar = inject(MatSnackBar);
  
  models: Model[] = [];
  displayedColumns: string[] = ['id', 'name', 'owner', 'framework', 'actions'];
  loading = true;

  ngOnInit() {
    this.loadModels();
  }

  loadModels() {
    this.loading = true;
    this.cdr.detectChanges();
    this.api.getModels().subscribe({
      next: (data) => {
        this.models = data;
        this.loading = false;
        this.cdr.detectChanges();
      },
      error: () => {
        this.loading = false;
        this.cdr.detectChanges();
      }
    });
  }

  onCreateModel() {
    const dialogRef = this.dialog.open(CreateModelDialog, {
      width: '400px'
    });

    dialogRef.afterClosed().subscribe(result => {
      if (result) {
        this.loading = true;
        this.cdr.detectChanges();
        this.api.createModel(result).subscribe({
          next: () => {
            this.snackBar.open('Model created successfully!', 'Close', { duration: 3000 });
            this.loadModels();
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
